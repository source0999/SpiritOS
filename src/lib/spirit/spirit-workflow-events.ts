// ── spirit-workflow-events - plan / research steps for UI (Prompt 10C) ───────────
// > High-level labels only - no chain-of-thought, no tool dumps.

import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import type { SpiritRouteDecision, SpiritRouteLane } from "@/lib/spirit/spirit-route-decision";

export type SpiritWorkflowStepStatus = "pending" | "active" | "done" | "skipped" | "error";

export type SpiritWorkflowStep = {
  id: string;
  label: string;
  status: SpiritWorkflowStepStatus;
};

/** UI visualizer uses a subset (no "skipped" in props contract - map to pending/done). */
export type SpiritVisualizerStepStatus = "pending" | "active" | "done" | "error";

export type SpiritVisualizerStep = {
  id: string;
  label: string;
  detail?: string;
  status: SpiritVisualizerStepStatus;
};

export function emptySpiritWorkflowSteps(): SpiritWorkflowStep[] {
  return [];
}

function clampStatuses(steps: SpiritVisualizerStep[], busy: boolean, tick: number): SpiritVisualizerStep[] {
  if (steps.length === 0) return steps;
  if (!busy) {
    return steps.map((s, i) => ({
      ...s,
      status: i === steps.length - 1 ? ("done" as const) : ("done" as const),
    }));
  }
  const cap = Math.max(steps.length - 1, 0);
  const idx = Math.min(Math.max(tick, 0), cap);
  return steps.map((s, i) => {
    if (i < idx) return { ...s, status: "done" as const };
    if (i === idx) return { ...s, status: "active" as const };
    return { ...s, status: "pending" as const };
  });
}

/** Baseline chat path (no OpenAI web prefetch in this turn). */
export function buildWorkflowStepsForLocalChat(opts: {
  modelProfileId: ModelProfileId;
  deepThink: boolean;
  busy: boolean;
  tick: number;
}): SpiritVisualizerStep[] {
  const modeLabel =
    opts.modelProfileId === "researcher"
      ? "Researcher"
      : opts.modelProfileId === "teacher"
        ? "Teacher"
        : opts.modelProfileId === "brutal"
          ? "Brutal"
          : opts.modelProfileId === "sassy-chaotic"
            ? "Sassy"
            : "Peer";
  const steps: SpiritVisualizerStep[] = [
    { id: "understand", label: "Understanding request", status: "pending" },
    { id: "route", label: "Choosing route", detail: modeLabel, status: "pending" },
    { id: "searchAvail", label: "Checking search availability", status: "pending" },
  ];
  if (opts.deepThink) {
    steps.push({ id: "deep", label: "Deep think pass", status: "pending" });
  }
  steps.push(
    { id: "draft", label: "Drafting answer", status: "pending" },
    { id: "voice", label: "Preparing voice summary", status: "pending" },
    { id: "complete", label: "Complete", status: "pending" },
  );
  return clampStatuses(steps, opts.busy, opts.tick);
}

export function buildWorkflowStepsForWebSearch(opts: {
  modelProfileId: ModelProfileId;
  deepThink: boolean;
  busy: boolean;
  tick: number;
}): SpiritVisualizerStep[] {
  const steps: SpiritVisualizerStep[] = [
    { id: "understand", label: "Understanding request", status: "pending" },
    { id: "route", label: "Search route selected", detail: "OpenAI web prefetch", status: "pending" },
    { id: "searchAvail", label: "Checking search availability", status: "pending" },
    { id: "search", label: "Searching OpenAI web", status: "pending" },
    { id: "found", label: "Collecting sources", detail: "Verified URLs only", status: "pending" },
    { id: "review", label: "Reviewing source snippets", status: "pending" },
  ];
  if (opts.deepThink) {
    steps.push({ id: "deep", label: "Deep think verification", status: "pending" });
  }
  steps.push(
    { id: "draft", label: "Drafting answer", status: "pending" },
    { id: "voice", label: "Preparing voice summary", status: "pending" },
    { id: "complete", label: "Complete", status: "pending" },
  );
  return clampStatuses(steps, opts.busy, opts.tick);
}

export function buildWorkflowStepsForResearchPlan(opts: {
  deepThink: boolean;
  busy: boolean;
  tick: number;
}): SpiritVisualizerStep[] {
  const steps: SpiritVisualizerStep[] = [
    { id: "understand", label: "Understanding request", status: "pending" },
    { id: "route", label: "Search route selected", detail: "Research plan before web pull", status: "pending" },
    { id: "plan", label: "Structuring research plan", status: "pending" },
    { id: "review", label: "Waiting for you to start research", status: "pending" },
  ];
  if (opts.deepThink) {
    steps.push({ id: "deep", label: "Deep think shaping", status: "pending" });
  }
  steps.push(
    { id: "draft", label: "Drafting answer", status: "pending" },
    { id: "complete", label: "Complete", status: "pending" },
  );
  return clampStatuses(steps, opts.busy, opts.tick);
}

/** Pick step pipeline from server lane + heuristics. */
export function buildWorkflowStepsForRouteDecision(
  lane: SpiritRouteLane | string,
  opts: {
    modelProfileId: ModelProfileId;
    deepThink: boolean;
    busy: boolean;
    tick: number;
  },
): SpiritVisualizerStep[] {
  if (lane === "openai-web-search") {
    return buildWorkflowStepsForWebSearch(opts);
  }
  if (lane === "research-plan") {
    return buildWorkflowStepsForResearchPlan({
      deepThink: opts.deepThink,
      busy: opts.busy,
      tick: opts.tick,
    });
  }
  return buildWorkflowStepsForLocalChat(opts);
}

/** @deprecated prefer buildWorkflowStepsForRouteDecision + labels map */
export function buildSpiritWorkflowStepLabels(opts: {
  modelProfileId: ModelProfileId;
  webSearchOptOut: boolean;
  deepThinkEnabled: boolean;
}): string[] {
  const lane: SpiritRouteLane =
    opts.modelProfileId === "researcher" && !opts.webSearchOptOut
      ? "openai-web-search"
      : "local-chat";
  const steps = buildWorkflowStepsForRouteDecision(lane, {
    modelProfileId: opts.modelProfileId,
    deepThink: opts.deepThinkEnabled,
    busy: true,
    tick: 0,
  });
  return steps.map((s) => s.label);
}

export function workflowStepsFromServerDecision(
  decision: Pick<SpiritRouteDecision, "lane">,
  opts: {
    modelProfileId: ModelProfileId;
    deepThink: boolean;
    busy: boolean;
    tick: number;
  },
): SpiritVisualizerStep[] {
  return buildWorkflowStepsForRouteDecision(decision.lane, opts);
}
