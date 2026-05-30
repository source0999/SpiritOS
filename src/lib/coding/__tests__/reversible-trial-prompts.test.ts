import { describe, expect, it } from "vitest";

import {
  reversibleTrialPromptCatalog,
  selectReversibleTrialPrompts,
} from "@/lib/coding/reversible-trial-prompts";

describe("reversible trial prompt catalog", () => {
  it("supports 25, 50, and 100 realistic reversible prompts", () => {
    expect(selectReversibleTrialPrompts(25)).toHaveLength(25);
    expect(selectReversibleTrialPrompts(50)).toHaveLength(50);
    expect(selectReversibleTrialPrompts(100)).toHaveLength(100);
    expect(reversibleTrialPromptCatalog).toHaveLength(100);
  });

  it("keeps dummy and preview-only prompts out of the suite", () => {
    const forbidden = /dummy|fixture-only|preview-only|no-op|tiny note|fake backend toy/i;
    for (const prompt of reversibleTrialPromptCatalog) {
      expect(prompt.reversible).toBe(true);
      expect(prompt.auto_revert).toBe(true);
      expect(prompt.protected_paths_blocked).toBe(true);
      expect(prompt.prompt).not.toMatch(forbidden);
      expect(prompt.expected_scope.length).toBeGreaterThan(0);
      expect(prompt.targetFile).not.toMatch(/^\.env|source_proxy\/data\/|backend\/volumes\/|backend\/searxng_data\/|\.spirit-backups\//);
    }
  });
});
