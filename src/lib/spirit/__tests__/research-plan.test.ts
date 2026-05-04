import { describe, expect, it } from "vitest";

import {
  addResearchPlanStep,
  draftResearchPlanFromPrompt,
  editResearchPlanStep,
  removeResearchPlanStep,
  researchPlanToSummary,
} from "@/lib/spirit/research-plan";

describe("research-plan", () => {
  it("draftResearchPlanFromPrompt seeds default steps", () => {
    const p = draftResearchPlanFromPrompt("What about sleep?");
    expect(p.steps.length).toBeGreaterThanOrEqual(4);
    expect(p.originalQuestion).toContain("sleep");
    expect(p.steps[0]?.status).toBe("pending");
  });

  it("editResearchPlanStep updates a step", () => {
    let p = draftResearchPlanFromPrompt("q");
    p = editResearchPlanStep(p, p.steps[0]!.id, { label: "Renamed", detail: "d" });
    expect(p.steps[0]?.label).toBe("Renamed");
    expect(p.steps[0]?.detail).toBe("d");
  });

  it("addResearchPlanStep and removeResearchPlanStep", () => {
    let p = draftResearchPlanFromPrompt("q");
    const n = p.steps.length;
    p = addResearchPlanStep(p, "Extra");
    expect(p.steps).toHaveLength(n + 1);
    const lastId = p.steps[p.steps.length - 1]!.id;
    p = removeResearchPlanStep(p, lastId);
    expect(p.steps).toHaveLength(n);
  });

  it("researchPlanToSummary is non-CoT checklist text", () => {
    const p = draftResearchPlanFromPrompt("test");
    const s = researchPlanToSummary(p);
    expect(s).toContain("User-approved research plan");
    expect(s.toLowerCase()).not.toContain("chain of thought");
  });
});
