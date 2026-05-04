import { describe, expect, it } from "vitest";

import {
  buildSpiritWorkflowStepLabels,
  buildWorkflowStepsForRouteDecision,
} from "@/lib/spirit/spirit-workflow-events";

describe("buildSpiritWorkflowStepLabels", () => {
  it("uses OpenAI web labels when researcher web is not opted out", () => {
    const steps = buildSpiritWorkflowStepLabels({
      modelProfileId: "researcher",
      webSearchOptOut: false,
      deepThinkEnabled: false,
    });
    expect(steps.some((s) => s.includes("Searching OpenAI web") || s.includes("OpenAI web"))).toBe(
      true,
    );
  });

  it("falls back to local route labels when researcher opted out of web", () => {
    const steps = buildSpiritWorkflowStepLabels({
      modelProfileId: "researcher",
      webSearchOptOut: true,
      deepThinkEnabled: false,
    });
    expect(steps.some((s) => s.includes("Choosing route"))).toBe(true);
  });

  it("adds deep think step when enabled", () => {
    const steps = buildSpiritWorkflowStepLabels({
      modelProfileId: "normal-peer",
      webSearchOptOut: false,
      deepThinkEnabled: true,
    });
    expect(steps).toContain("Deep think pass");
  });
});

describe("buildWorkflowStepsForRouteDecision", () => {
  it("returns web pipeline for openai-web-search lane", () => {
    const steps = buildWorkflowStepsForRouteDecision("openai-web-search", {
      modelProfileId: "researcher",
      deepThink: false,
      busy: true,
      tick: 0,
    });
    expect(steps[0]?.label).toContain("Understanding");
    expect(steps.some((s) => s.label.includes("Searching OpenAI web"))).toBe(true);
  });
});
