import {
  convertToModelMessages,
  streamText,
  stepCountIs,
  type ModelMessage,
  type ToolSet,
} from "ai";

import { getCapabilityRegistry } from "@/lib/server/capabilities/get-capabilities";
import { formatCapabilityAnswer, WORKSPACE_READ_TOOLS_PROBE_REJECTED_MESSAGE } from "@/lib/server/capabilities/format-capability-answer";
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
import { resolveSpiritToolsForOllamaModel } from "@/lib/spirit/tools/tool-registry";
import { handleDirectWorkspaceRequest } from "@/lib/spirit/tools/direct-workspace-request";
import { handleDirectDevCommandRequest } from "@/lib/spirit/tools/direct-dev-command-request";
import { detectCapabilityIntent } from "@/lib/spirit/capability-intent";
import { isConcreteWorkspaceReadRequest } from "@/lib/spirit/concrete-workspace-read-request";
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
    const spiritTools = await resolveSpiritToolsForOllamaModel(ollamaModelId);
    const webGlob = isWebSearchGloballyEnabled();

    const capabilityKind = detectCapabilityIntent(lastUser);

    const localToolsEnvEnabled = process.env.SPIRIT_ENABLE_LOCAL_TOOLS === "true";
    const ollamaToolsAllowed = process.env.SPIRIT_OLLAMA_SUPPORTS_TOOLS === "true";
    const concreteWorkspaceRead = isConcreteWorkspaceReadRequest(lastUser);
    const readOnlyToolsAttached = Boolean(spiritTools);
    const fileEditToolsAttached =
      Boolean(
        spiritTools &&
          typeof spiritTools === "object" &&
          "propose_file_edit" in spiritTools,
      );
    const workspaceEditing = {
      fileEditEnvEnabled: process.env.SPIRIT_ENABLE_FILE_EDIT_TOOLS === "true",
      editToolsAttached: fileEditToolsAttached,
    };
    const devCommandToolsAttached =
      Boolean(
        spiritTools &&
          typeof spiritTools === "object" &&
          "run_dev_command" in spiritTools,
      );
    const devCommands = {
      devCommandEnvEnabled: process.env.SPIRIT_ENABLE_DEV_COMMAND_TOOLS === "true",
      devCommandToolsAttached,
    };
    const shouldLetWorkspaceToolsHandle =
      concreteWorkspaceRead && readOnlyToolsAttached;

    if (process.env.NODE_ENV === "development") {
      const reason = readOnlyToolsAttached
        ? "tools_attached"
        : !localToolsEnvEnabled
          ? "local_tools_env_off"
          : !ollamaToolsAllowed
            ? "ollama_tools_transport_off"
            : "model_probe_unsupported";
      console.log(
        `[spirit-api] surface=${surface} profile=${modelProfileId ?? "unset"} workspace-tools modelId=${ollamaModelId} SPIRIT_ENABLE_LOCAL_TOOLS=${localToolsEnvEnabled} SPIRIT_OLLAMA_SUPPORTS_TOOLS=${ollamaToolsAllowed} toolsAttached=${readOnlyToolsAttached} reason=${reason}`,
      );
    }

    // ── 3. Concrete workspace read/list/tail: never let the model invent listings without tools ─
    if (concreteWorkspaceRead && !readOnlyToolsAttached) {
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

      if (!localToolsEnvEnabled) {
        const registry = await getCapabilityRegistry();
        const diagnostics = getSpiritDiagnostics();
        const text = formatCapabilityAnswer({
          registry,
          diagnostics,
          webSearchEnabled: webGlob,
          runtimeSurface: surface,
          activeResolvedModelId: ollamaModelId,
          intentKind: "file_access",
          userMessage: lastUser,
          workspaceEditing,
          devCommands,
        });

        return createDeterministicAssistantUIMessageResponse({
          text,
          originalMessages: uiMessages,
          headers: responseHeaders,
        });
      }

      const directAnswer = await handleDirectWorkspaceRequest(lastUser);
      if (directAnswer) {
        return createDeterministicAssistantUIMessageResponse({
          text: directAnswer.markdown,
          originalMessages: uiMessages,
          headers: responseHeaders,
          toolActivity: directAnswer.toolActivity,
        });
      }

      const text = !ollamaToolsAllowed
        ? [
            "SPIRIT_ENABLE_LOCAL_TOOLS is on, but SPIRIT_OLLAMA_SUPPORTS_TOOLS is not set to \"true\", so this API will not attach OpenAI-style tool calls to Ollama.",
            "Without tool-call support from your model, Hermes cannot run list_workspace_files, read_workspace_file, read_log_tail, or get_system_status on the wire.",
            "Set SPIRIT_OLLAMA_SUPPORTS_TOOLS=true only after you use an Ollama model that accepts tools; leaving it false avoids HTTP 400 errors from models that reject tool payloads.",
          ].join("\n\n")
        : WORKSPACE_READ_TOOLS_PROBE_REJECTED_MESSAGE;

      return createDeterministicAssistantUIMessageResponse({
        text,
        originalMessages: uiMessages,
        headers: responseHeaders,
      });
    }

    // ── 4. Capability Intent Bridge (Pre-LLM) ──
    const bypassDevCommandsCapability =
      capabilityKind === "dev_commands" && devCommandToolsAttached;

    if (capabilityKind !== null && !shouldLetWorkspaceToolsHandle && !bypassDevCommandsCapability) {
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

      if (
        capabilityKind === "dev_commands" &&
        localToolsEnvEnabled &&
        process.env.SPIRIT_ENABLE_DEV_COMMAND_TOOLS === "true" &&
        !devCommandToolsAttached
      ) {
        const directDevAnswer = await handleDirectDevCommandRequest(lastUser);
        if (directDevAnswer) {
          return createDeterministicAssistantUIMessageResponse({
            text: directDevAnswer.markdown,
            originalMessages: uiMessages,
            headers: responseHeaders,
            toolActivity: directDevAnswer.toolActivity,
          });
        }
      }

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
        workspaceEditing,
        devCommands,
      });

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
      localToolsAttached: readOnlyToolsAttached,
      fileEditToolsAttached,
      devCommandToolsAttached,
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
      ...(spiritTools
        ? { tools: spiritTools as ToolSet, stopWhen: stepCountIs(12) }
        : {}),
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
