import { describe, expect, it } from "vitest";

import {
  normalizeReversibleTrialCategoryInput,
  reversibleTrialCategories,
  reversibleTrialPromptCatalog,
  selectReversibleTrialPrompts,
  validateReversibleTrialPromptBank,
} from "@/lib/coding/reversible-trial-prompts";

const agentLabAllowedFiles = [
  "src/app/agent-lab/**",
  "src/components/agent-lab/**",
  "src/lib/agent-lab/**",
  "src/app/api/agent-lab/**",
  "tests/agent-lab/**",
];

function expectedCoderIds(count: 10 | 25 | 50 | 100) {
  return Array.from({ length: count }, (_, index) => `coder-${String(index + 1).padStart(3, "0")}`);
}

describe("reversible trial prompt catalog", () => {
  it("rejects unknown category inputs before a suite can start", () => {
    expect(normalizeReversibleTrialCategoryInput("Coder")).toBe("Coder");
    expect(normalizeReversibleTrialCategoryInput("bogus")).toBeNull();
  });

  it("keeps the non-Coder banks present while exposing exactly 100 active Coder prompts", () => {
    expect(reversibleTrialPromptCatalog.filter((prompt) => prompt.category === "Coder")).toHaveLength(100);
    expect(reversibleTrialPromptCatalog).toHaveLength(300);
    for (const category of reversibleTrialCategories) {
      expect(selectReversibleTrialPrompts(100, category)).toHaveLength(100);
    }
  });

  it("slices the messy Coder ladder by exact prompt id order", () => {
    for (const count of [10, 25, 50, 100] as const) {
      expect(selectReversibleTrialPrompts(count, "Coder").map((prompt) => prompt.id)).toEqual(
        expectedCoderIds(count),
      );
    }
  });

  it("uses the attached messy human agent-lab prompts as active Coder text", () => {
    const prompts = selectReversibleTrialPrompts(10, "Coder");
    expect(prompts[0]?.prompt).toContain("make a new isolated test area at `/agent-lab`");
    expect(prompts[0]?.prompt).toContain("verify `/agent-lab` loads");
    expect(prompts[1]?.prompt).toContain("make a calculator page at `/agent-lab/calculator`");
    expect(prompts[1]?.prompt).toContain("two number inputs");
    expect(prompts[1]?.prompt).toContain('"use client" as the first line');
    expect(prompts.map((prompt) => prompt.prompt)).not.toContain(
      "badge thingy needs like a warning mode too not just pass fail, dont break old pass/fail stuff tho",
    );
  });

  it("marks all active Coder prompts as productive agent-lab code-change prompts", () => {
    const prompts = selectReversibleTrialPrompts(100, "Coder");
    for (const prompt of prompts) {
      expect(prompt.id).toMatch(/^coder-\d{3}$/);
      expect(prompt.category).toBe("Coder");
      expect(prompt.lane).toBe("coder");
      expect(prompt.benchmark_type).toBe("messy_human_agent_lab");
      expect(prompt.expected_behavior).toBe("productive_code_change");
      expect(prompt.expectedOutcome).toBe("edit_reversible");
      expect(prompt.live_model_call_required).toBe(true);
      expect(prompt.diff_required).toBe(true);
      expect(prompt.disk_change_required).toBe(true);
      expect(prompt.verification_required).toBe(true);
      expect(prompt.rollback_required).toBe(true);
      expect(prompt.reversible).toBe(true);
      expect(prompt.auto_revert).toBe(false);
      expect(prompt.protected_paths_blocked).toBe(true);
    }
  });

  it("limits active Coder allowed files and likely targets to isolated agent-lab paths", () => {
    const prompts = selectReversibleTrialPrompts(100, "Coder");
    for (const prompt of prompts) {
      expect(prompt.allowed_files).toEqual(agentLabAllowedFiles);
      expect(prompt.expected_scope.length).toBeGreaterThan(0);
      expect(prompt.verifyPathHints).toEqual(prompt.expected_scope);
      for (const path of [prompt.targetFile, ...prompt.expected_scope, ...prompt.likelyTargets]) {
        expect(path).toMatch(/^(src\/app\/agent-lab\/|src\/components\/agent-lab\/|src\/lib\/agent-lab\/|src\/app\/api\/agent-lab\/|tests\/agent-lab\/)/);
        expect(path).not.toContain("src/components/coding/");
        expect(path).not.toContain("src/lib/coding/");
        expect(path).not.toContain("tests/ui-agent-trials/fixtures/dummy-coding-targets/");
      }
    }
  });

  it("selects route-specific agent-lab pages before the lab index page", () => {
    const prompts = selectReversibleTrialPrompts(10, "Coder");

    expect(prompts[0]?.targetFile).toBe("src/app/agent-lab/page.tsx");
    expect(prompts[1]?.targetFile).toBe("src/app/agent-lab/calculator/page.tsx");
    expect(prompts[1]?.expected_scope[0]).toBe("src/app/agent-lab/calculator/page.tsx");
  });

  it("keeps old safety, no-op, clarification, and audit-only prompts out of the active Coder benchmark", () => {
    const promptText = selectReversibleTrialPrompts(100, "Coder")
      .map((prompt) => prompt.prompt)
      .join("\n");
    expect(promptText).not.toMatch(/secret\/env key|ask me what screen|mark noop|prompt audit|safety benchmark|preview-only bank/i);
    expect(selectReversibleTrialPrompts(100, "Coder").every((prompt) => prompt.expectedOutcome === "edit_reversible")).toBe(true);
  });

  it("leaves Designer and Combined prompt banks untouched by the Coder replacement", () => {
    expect(selectReversibleTrialPrompts(10, "Designer")[0]?.prompt).toBe(
      "this source page feels cramped af, tell me biggest visual thing making it not daily usable",
    );
    expect(selectReversibleTrialPrompts(10, "Combined")[0]?.prompt).toBe(
      "50 prompts are just repeated 10s, fix bank logic and make UI say real unique bank count",
    );
  });

  it("validates unique banks and confirms the runner can load requested counts without running suites", () => {
    expect(validateReversibleTrialPromptBank(reversibleTrialPromptCatalog)).toEqual([]);
    expect(selectReversibleTrialPrompts(10, "Coder")).toHaveLength(10);
    expect(selectReversibleTrialPrompts(25, "Coder")).toHaveLength(25);
    expect(selectReversibleTrialPrompts(50, "Coder")).toHaveLength(50);
    expect(selectReversibleTrialPrompts(100, "Coder")).toHaveLength(100);
  });
});
