import { convertToModelMessages, streamText, type ModelMessage } from "ai";

import { getCapabilityRegistry } from "@/lib/server/capabilities/get-capabilities";
import { formatCapabilityAnswer } from "@/lib/server/capabilities/format-capability-answer";
import { createDeterministicAssistantUIMessageResponse } from "@/lib/server/spirit-deterministic-ui-response";
import { lastUserTextFromMessages } from "@/lib/chat-utils";
import { ApiError, errorToResponse } from "@/lib/server/api-errors";
import {
  getOracleMaxOutputTokens,
  getSpiritDiagnostics,
  getSpiritMaxOutputTokens,
} from "@/lib/server/spirit-diagnostics";
import { ollamaOpenAI, probeOllamaOpenAICompat } from "@/lib/server/ollama";
import {
  resolveOllamaModelId,
  type SpiritRuntimeSurface,
} from "@/lib/server/model-routing";
import { runOpenAiWebSearch } from "@/lib/server/openai-web-search";
import { readSpiritRequest } from "@/lib/server/spirit-request";
import {
  buildSpiritSearchHeaders,
  logSpiritSearchEvent,
  sanitizeForHttpByteStringHeader,
  trimSearchQueryForLog,
} from "@/lib/server/spirit-search-telemetry";
import {
  buildWebSearchSourcesHeader,
  formatResearchContextForHermes,
  formatResearchSkippedBanner,
  isWebSearchGloballyEnabled,
} from "@/lib/server/spirit-web-research-guard";
import { buildModelRuntime } from "@/lib/spirit/model-runtime";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { getModelProfile } from "@/lib/spirit/model-profiles";
import { resolveSpiritSystemState } from "@/lib/spirit/system-state";
import { detectCapabilityIntent } from "@/lib/spirit/capability-intent";
import { decideSpiritRoute } from "@/lib/spirit/spirit-route-decision";
import {
  buildResearchSourcePolicy,
  userRequestedFreshExternalSources,
  type SpiritSearchStatus,
} from "@/lib/spirit/research-source-enforcement";
import type { OpenAiWebSearchResult } from "@/lib/server/openai-web-search";
import { resolveVerifiedHttpUrl } from "@/lib/verified-http-url";

function logReasonFromSearchFailure(r: OpenAiWebSearchResult): string {
  if (r.ok) return "no_verified_urls";
  if (r.error === "missing_key") return "missing_openai_key";
  if (r.error === "disabled") return "web_search_env_disabled";
  return r.error;
}

function verifiedHttpSourcesFromSearch(r: OpenAiWebSearchResult): Array<{ url: string }> {
  if (!r.ok || !r.searched) return [];
  const out: Array<{ url: string }> = [];
  for (const s of r.sources) {
    const url = resolveVerifiedHttpUrl(s.url);
    if (url) out.push({ url });
  }
  return out;
}

function appendSourcePolicyBlock(
  base: string,
  opts: {
    searchStatus: SpiritSearchStatus;
    sources: Array<{ url?: string }>;
    requestedFreshSources: boolean;
    modelProfileId?: ModelProfileId;
  },
): string {
  const pol = buildResearchSourcePolicy(opts);
  return `${base.trim()}\n\n${pol}`.trim();
}

// ── Spirit → Ollama - Prompt 10B: system via AI SDK + optional OpenAI web proof ─
// > System is NOT duplicated into messages[] - kills the AI SDK security warning.

export async function POST(req: Request) {
  try {
    console.log("[spirit-api] POST /api/spirit hit");

    const {
      messages: uiMessages,
      modelProfileId,
      runtimeSurface,
      personalizationSummary,
      deepThinkEnabled,
      webSearchOptOut,
      teacherWebSearchEnabled,
      researchPlanSummary,
      oracleMemoryContext,
    } = await readSpiritRequest(req);

    const lastUser = lastUserTextFromMessages(uiMessages);
    const qLog = trimSearchQueryForLog(lastUser);

    const surface: SpiritRuntimeSurface =
      runtimeSurface === "oracle" ? "oracle" : "chat";
    const ollamaModelId = resolveOllamaModelId(surface);
    const webGlob = isWebSearchGloballyEnabled();

    const capabilityKind = detectCapabilityIntent(lastUser);
    if (capabilityKind !== null) {
      let ollamaReachable: boolean | undefined;
      if (capabilityKind === "ai_runtime") {
        const probe = await probeOllamaOpenAICompat();
        ollamaReachable = probe.ok;
      }

      const registry = await getCapabilityRegistry();
      const diagnostics = getSpiritDiagnostics();
      const text = formatCapabilityAnswer({
        registry,
        diagnostics,
        webSearchEnabled: webGlob,
        runtimeSurface: surface,
        activeResolvedModelId: ollamaModelId,
        intentKind: capabilityKind,
        userMessage: lastUser,
        ollamaReachable,
      });

      const responseHeaders = {
        ...buildSpiritSearchHeaders({
          routeLane: "local-chat",
          routeConfidence: "high",
          webSearch: "none",
          searchStatus: "none",
          provider: null,
          sourceCount: 0,
          queryTrimmed: trimSearchQueryForLog(lastUser),
          elapsedMs: null,
          searchKind: "none",
          skipReason: null,
          webSourcesJson: null,
        }),
        "x-spirit-runtime-surface": sanitizeForHttpByteStringHeader(surface),
      };

      return createDeterministicAssistantUIMessageResponse({
        text,
        originalMessages: uiMessages,
        headers: responseHeaders,
      });
    }

    const routeDecision = decideSpiritRoute({
      modelProfileId,
      lastUserText: lastUser,
      deepThinkEnabled,
      webSearchOptOut,
      teacherWebSearchEnabled,
      webSearchGloballyEnabled: webGlob,
      modelHint: ollamaModelId,
    });

    let researchWebContext: string | null = null;
    let webSearchHeader = "none";
    let webSourcesHeader: string | null = null;
    let spiritSourceCount = 0;
    let spiritSearchProvider: string | null = null;
    let searchElapsedMs: number | null = null;
    let searchKind: "researcher" | "teacher" | "none" = "none";
    let skipReason: string | null = null;
    let webVerifiedUrlCount: number | undefined;

    const freshSourceAsk = userRequestedFreshExternalSources(lastUser);

    if (modelProfileId === "researcher") {
      searchKind = "researcher";
      let verified: Array<{ url?: string }> = [];
      let policyStatus: SpiritSearchStatus = "none";

      if (routeDecision.shouldSearchWeb) {
        logSpiritSearchEvent({
          route: "openai-web-search",
          status: "starting",
          mode: "researcher",
          queryTrimmed: qLog,
        });
        const t0 = Date.now();
        const r = await runOpenAiWebSearch({ query: lastUser.slice(0, 2000) });
        searchElapsedMs = Date.now() - t0;
        verified = verifiedHttpSourcesFromSearch(r);
        webVerifiedUrlCount = verified.length;
        spiritSourceCount = verified.length;
        spiritSearchProvider = r.ok ? r.provider : "openai";
        researchWebContext = formatResearchContextForHermes(lastUser, r);
        webSearchHeader = r.ok && r.searched ? "used" : "failed";
        webSourcesHeader = buildWebSearchSourcesHeader(r);
        policyStatus = r.ok && r.searched ? "used" : "failed";
        if (!(r.ok && r.searched)) {
          skipReason = logReasonFromSearchFailure(r);
        }
        if (r.ok && r.searched && verified.length > 0) {
          logSpiritSearchEvent({
            route: "openai-web-search",
            status: "used",
            mode: "researcher",
            queryTrimmed: qLog,
            provider: r.provider,
            sources: verified.length,
            elapsedMs: searchElapsedMs,
          });
        } else if (r.ok && r.searched) {
          logSpiritSearchEvent({
            route: "openai-web-search",
            status: "failed",
            mode: "researcher",
            queryTrimmed: qLog,
            provider: r.provider,
            elapsedMs: searchElapsedMs,
            reason: "no_verified_urls",
          });
        } else {
          logSpiritSearchEvent({
            route: "openai-web-search",
            status: "failed",
            mode: "researcher",
            queryTrimmed: qLog,
            provider: "openai",
            elapsedMs: searchElapsedMs,
            reason: logReasonFromSearchFailure(r),
          });
        }
      } else if (!webGlob) {
        skipReason = "WEB_SEARCH_DISABLED";
        researchWebContext = formatResearchSkippedBanner("WEB_SEARCH_DISABLED");
        webSearchHeader = "disabled";
        policyStatus = "disabled";
        logSpiritSearchEvent({
          route: "local-chat",
          status: "disabled",
          mode: "researcher",
          queryTrimmed: qLog,
          reason: skipReason,
        });
      } else if (webSearchOptOut) {
        skipReason = "user_disabled_web_search";
        researchWebContext = formatResearchSkippedBanner("user_disabled_web_search");
        webSearchHeader = "skipped";
        policyStatus = "skipped";
        logSpiritSearchEvent({
          route: "local-chat",
          status: "skipped",
          mode: "researcher",
          queryTrimmed: qLog,
          provider: "openai",
          reason: skipReason,
        });
      } else {
        skipReason = "not_triggered_for_this_prompt";
        researchWebContext = formatResearchSkippedBanner("not_triggered_for_this_prompt");
        webSearchHeader = "skipped";
        policyStatus = "skipped";
        logSpiritSearchEvent({
          route: "local-chat",
          status: "skipped",
          mode: "researcher",
          queryTrimmed: qLog,
          reason: skipReason,
        });
      }

      researchWebContext = appendSourcePolicyBlock(researchWebContext, {
        searchStatus: policyStatus,
        sources: verified,
        requestedFreshSources: freshSourceAsk,
        modelProfileId: "researcher",
      });
    } else if (modelProfileId === "teacher" && routeDecision.shouldSearchTeacherWeb) {
      searchKind = "teacher";
      logSpiritSearchEvent({
        route: "teacher-web-aids",
        status: "starting",
        mode: "teacher",
        queryTrimmed: qLog,
      });
      const t0 = Date.now();
      const r = await runOpenAiWebSearch({
        query: lastUser.slice(0, 2000),
        maxResults: 4,
      });
      searchElapsedMs = Date.now() - t0;
      const verified = verifiedHttpSourcesFromSearch(r);
      webVerifiedUrlCount = verified.length;
      spiritSourceCount = verified.length;
      spiritSearchProvider = r.ok ? r.provider : "openai";
      researchWebContext = formatResearchContextForHermes(lastUser, r);
      webSearchHeader = r.ok && r.searched ? "used" : "failed";
      webSourcesHeader = buildWebSearchSourcesHeader(r);
      researchWebContext = appendSourcePolicyBlock(researchWebContext, {
        searchStatus: r.ok && r.searched ? "used" : "failed",
        sources: verified,
        requestedFreshSources: freshSourceAsk,
        modelProfileId: "teacher",
      });
      if (!(r.ok && r.searched)) {
        skipReason = logReasonFromSearchFailure(r);
      }
      if (r.ok && r.searched && verified.length > 0) {
        logSpiritSearchEvent({
          route: "teacher-web-aids",
          status: "used",
          mode: "teacher",
          queryTrimmed: qLog,
          provider: r.provider,
          sources: verified.length,
          elapsedMs: searchElapsedMs,
        });
      } else {
        logSpiritSearchEvent({
          route: "teacher-web-aids",
          status: "failed",
          mode: "teacher",
          queryTrimmed: qLog,
          provider: "openai",
          elapsedMs: searchElapsedMs,
          reason: r.ok && r.searched ? "no_verified_urls" : logReasonFromSearchFailure(r),
        });
      }
    }

    const systemState = resolveSpiritSystemState({
      runtimeSurface: surface,
      modelHint: ollamaModelId,
      modelProfileId: modelProfileId ?? null,
      modelProfileLabel: getModelProfile(modelProfileId).label,
    });

    const runtime = buildModelRuntime(modelProfileId, {
      personalizationSummary,
      lastUserMessage: lastUser,
      deepThinkEnabled,
      researchWebContext,
      researchPlanSummary: researchPlanSummary ?? null,
      webVerifiedUrlCount,
      runtimeSurface: surface,
      systemState,
      oracleMemoryContext: oracleMemoryContext ?? null,
    });

    if (process.env.NODE_ENV === "development") {
      console.log(`[spirit-api] surface=${surface} mode=${modelProfileId}`);
    }

    const maxOutputTokens =
      surface === "oracle"
        ? getOracleMaxOutputTokens()
        : (runtime.maxOutputTokens ?? getSpiritMaxOutputTokens());

    let converted: ModelMessage[];
    try {
      converted = await convertToModelMessages(
        uiMessages.map((m) => {
          const { id, ...rest } = m;
          void id;
          return rest;
        }),
      );
    } catch {
      throw new ApiError(400, "Invalid message format");
    }

    const result = await streamText({
      model: ollamaOpenAI.chat(ollamaModelId),
      system: runtime.systemPrompt,
      messages: converted,
      temperature: runtime.temperature,
      maxOutputTokens,
    });

    const responseHeaders = {
      ...buildSpiritSearchHeaders({
        routeLane: routeDecision.lane,
        routeConfidence: routeDecision.confidence,
        webSearch: webSearchHeader,
        searchStatus: webSearchHeader,
        provider: spiritSearchProvider,
        sourceCount: spiritSourceCount,
        queryTrimmed: trimSearchQueryForLog(lastUser),
        elapsedMs: searchElapsedMs,
        searchKind,
        skipReason,
        webSourcesJson: webSourcesHeader,
      }),
      "x-spirit-runtime-surface": sanitizeForHttpByteStringHeader(surface),
    };

    return result.toUIMessageStreamResponse({
      headers: responseHeaders,
    });
  } catch (error) {
    return errorToResponse(error);
  }
}
