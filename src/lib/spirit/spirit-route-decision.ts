// ── spirit-route-decision — hybrid lane picker (Prompt 10C) ─────────────────────
// > Client-safe: no server-only imports. Callers pass env-derived flags from route.ts.
// > `lane` describes the dominant *orchestration* path this turn, not who owns every token.
// > Today Hermes always streams the user-visible reply; OpenAI is optional prefetch only.

import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import {
  isLikelyCasualShortMessage,
  mentionsCodeOrBuild,
  wantsResearchDepth,
  wantsTeacherWebStudyAids,
} from "@/lib/spirit/response-budget";

export type SpiritRouteLane =
  | "local-chat"
  | "openai-web-search"
  | "research-plan"
  | "deepseek-local"
  | "deepseek-api"
  | "disabled";

export type SpiritRouteDecisionReason =
  | "casual_chat"
  | "coding_or_complex_logic"
  | "current_data_needed"
  | "researcher_mode"
  | "deep_think_enabled"
  | "web_search_enabled"
  | "deep_research_requested"
  | "teacher_learning_request"
  | "local_default"
  | "provider_unavailable";

export type SpiritRouteDecision = {
  lane: SpiritRouteLane;
  confidence: "low" | "medium" | "high";
  reasons: SpiritRouteDecisionReason[];
  shouldSearchWeb: boolean;
  /** Teacher lane OpenAI prefetch when aids allowed + prompt looks educational. */
  shouldSearchTeacherWeb: boolean;
  shouldDraftResearchPlan: boolean;
  shouldUseDeepThink: boolean;
  shouldShowVisualizer: boolean;
  modelHint: string;
};

export type SpiritRouteDecisionInput = {
  modelProfileId: ModelProfileId;
  lastUserText: string;
  deepThinkEnabled: boolean;
  /**
   * When true, Researcher skips the OpenAI web prefetch (explicit user opt-out).
   * Default OFF at the protocol level — Researcher web is on unless opted out.
   */
  webSearchOptOut: boolean;
  /** Teacher-only: web study aids. Default ON (omit or undefined); set false to opt out per thread. */
  teacherWebSearchEnabled?: boolean;
  /** Caller reads WEB_SEARCH_ENABLED (or test inject). */
  webSearchGloballyEnabled: boolean;
  /** Ollama model id hint for diagnostics / headers */
  modelHint: string;
};

/** Hermes researcher lane: default web ON unless user opted out or env killed it. */
export function shouldPrefetchOpenAiWebForResearcher(opts: {
  modelProfileId: ModelProfileId;
  lastUserText: string;
  webSearchOptOut?: boolean;
  webSearchGloballyEnabled: boolean;
}): boolean {
  if (opts.modelProfileId !== "researcher") return false;
  if (!opts.webSearchGloballyEnabled) return false;
  if (opts.webSearchOptOut) return false;
  return opts.lastUserText.trim().length > 0;
}

function uniqReasons(r: SpiritRouteDecisionReason[]): SpiritRouteDecisionReason[] {
  return [...new Set(r)];
}

/**
 * Deterministic routing for /api/spirit — extensible when DeepSeek / plan-first land.
 */
export function decideSpiritRoute(input: SpiritRouteDecisionInput): SpiritRouteDecision {
  const last = input.lastUserText.trim();
  const reasons: SpiritRouteDecisionReason[] = [];
  const deep = Boolean(input.deepThinkEnabled);
  const webOptOut = Boolean(input.webSearchOptOut);

  if (input.modelProfileId === "researcher") {
    reasons.push("researcher_mode");
  }
  if (deep) {
    reasons.push("deep_think_enabled");
  }
  if (input.webSearchGloballyEnabled) {
    reasons.push("web_search_enabled");
  }
  if (input.modelProfileId === "teacher" && wantsTeacherWebStudyAids(last)) {
    reasons.push("teacher_learning_request");
  }
  if (mentionsCodeOrBuild(last)) {
    reasons.push("coding_or_complex_logic");
  }
  if (wantsResearchDepth(last)) {
    reasons.push("current_data_needed");
  }
  if (isLikelyCasualShortMessage(last)) {
    reasons.push("casual_chat");
  }

  const shouldSearchWeb = shouldPrefetchOpenAiWebForResearcher({
    modelProfileId: input.modelProfileId,
    lastUserText: input.lastUserText,
    webSearchOptOut: input.webSearchOptOut,
    webSearchGloballyEnabled: input.webSearchGloballyEnabled,
  });

  const teacherWebAidsAllowed = input.teacherWebSearchEnabled !== false;
  const shouldSearchTeacherWeb =
    input.modelProfileId === "teacher" &&
    teacherWebAidsAllowed &&
    input.webSearchGloballyEnabled &&
    wantsTeacherWebStudyAids(last) &&
    last.length > 0;

  const shouldDraftResearchPlan =
    input.modelProfileId === "researcher" &&
    (!isLikelyCasualShortMessage(last) || shouldSearchWeb || !webOptOut || deep);

  let lane: SpiritRouteLane = "local-chat";
  if (shouldSearchWeb || shouldSearchTeacherWeb) {
    lane = "openai-web-search";
  } else if (shouldDraftResearchPlan) {
    lane = "research-plan";
  } else {
    reasons.push("local_default");
  }

  const casual = last.length === 0 ? true : isLikelyCasualShortMessage(last);
  const shouldShowVisualizer =
    deep ||
    (input.modelProfileId === "teacher" && wantsTeacherWebStudyAids(last)) ||
    (input.modelProfileId === "researcher" && !casual) ||
    (shouldSearchWeb && !casual) ||
    shouldSearchTeacherWeb;

  let confidence: "low" | "medium" | "high" = "high";
  if (last.length === 0) {
    confidence = "low";
  } else if (isLikelyCasualShortMessage(last) && input.modelProfileId === "researcher") {
    confidence = "medium";
  }

  return {
    lane,
    confidence,
    reasons: uniqReasons(reasons),
    shouldSearchWeb,
    shouldSearchTeacherWeb,
    shouldDraftResearchPlan,
    shouldUseDeepThink: deep,
    shouldShowVisualizer,
    modelHint: input.modelHint,
  };
}
