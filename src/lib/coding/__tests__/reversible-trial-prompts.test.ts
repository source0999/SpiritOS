import { describe, expect, it } from "vitest";

import {
  reversibleTrialCategories,
  reversibleTrialPromptCatalog,
  selectReversibleTrialPrompts,
} from "@/lib/coding/reversible-trial-prompts";

describe("reversible trial prompt catalog", () => {
  it("supports 10, 25, 50, and 100 realistic prompts per category", () => {
    expect(selectReversibleTrialPrompts(10)).toHaveLength(10);
    expect(selectReversibleTrialPrompts(25)).toHaveLength(25);
    expect(selectReversibleTrialPrompts(50)).toHaveLength(50);
    expect(selectReversibleTrialPrompts(100)).toHaveLength(100);
    expect(reversibleTrialPromptCatalog).toHaveLength(300);
    for (const category of reversibleTrialCategories) {
      expect(selectReversibleTrialPrompts(10, category).every((prompt) => prompt.category === category)).toBe(true);
      expect(selectReversibleTrialPrompts(100, category)).toHaveLength(100);
    }
  });

  it("keeps dummy and preview-only prompts out of the suite and includes quick-find hints", () => {
    const forbidden = /dummy|fixture-only|preview-only|no-op|tiny note|fake backend toy/i;
    for (const prompt of reversibleTrialPromptCatalog) {
      expect(prompt.reversible).toBe(true);
      expect(prompt.auto_revert).toBe(true);
      expect(prompt.protected_paths_blocked).toBe(true);
      expect(prompt.prompt).not.toMatch(forbidden);
      expect(prompt.expected_scope.length).toBeGreaterThan(0);
      expect(prompt.verifyPathHints.length).toBeGreaterThan(0);
      expect(prompt.verifyInstruction).toContain(prompt.verifyPathHints[0]);
      expect(prompt.targetFile).not.toMatch(/^\.env|source_proxy\/data\/|backend\/volumes\/|backend\/searxng_data\/|\.spirit-backups\//);
    }
  });

  it("keeps each category near an 80/20 edit to expected no-edit ratio", () => {
    for (const category of reversibleTrialCategories) {
      const prompts = selectReversibleTrialPrompts(10, category);
      expect(prompts.filter((prompt) => prompt.expectedOutcome === "edit_reversible")).toHaveLength(8);
      expect(prompts.filter((prompt) => prompt.expectedOutcome !== "edit_reversible")).toHaveLength(2);
    }
  });
});
