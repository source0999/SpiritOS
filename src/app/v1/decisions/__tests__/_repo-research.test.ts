/// <reference types="vitest/globals" />

import { mergeRepoFirstResearchSources } from "@/app/v1/decisions/_repo-research";

describe("repo research response merge", () => {
  it("does not inject Phase 7C into a fresh unrelated coding task", () => {
    const request = JSON.stringify({
      task: [
        "Create a brand new clean design-demo page at /coding/design-demo.",
        "Target file: src/app/coding/design-demo/page.tsx",
      ].join("\n\n"),
      wants_implementation: true,
      needs_codebase_context: true,
    });
    const response = JSON.stringify({
      task_classification: "implementation",
      recommended_route: "local_route",
      next_prompt_action: "run_with_coder_agent",
      reason_codes: ["implementation_requested"],
      relevant_context: "Coder Agent route selected.",
      constraints: [],
    });

    const merged = JSON.parse(mergeRepoFirstResearchSources(request, response));

    expect(JSON.stringify(merged)).not.toContain("Phase 7C");
    expect(JSON.stringify(merged)).not.toContain("Increment 7C.4");
    expect(merged.relevant_context).toContain("Coder Agent route selected");
    expect(merged.constraints).toContain(
      "Do not inherit target files, diffs, routes, phase labels, or approval state from previous runs.",
    );
    expect(merged.self_correction_checks[2].answer).toBe(
      "No active phase was specified in this task; do not inherit one from prior runs.",
    );
  });

  it("keeps Phase 7C context when the current task explicitly asks for it", () => {
    const request = JSON.stringify({
      task: "Patch Phase 7C / Increment 7C.4 self-correction on /coding.",
      wants_implementation: true,
      needs_codebase_context: true,
    });
    const response = JSON.stringify({
      task_classification: "implementation",
      recommended_route: "local_route",
      next_prompt_action: "run_with_coder_agent",
      reason_codes: ["implementation_requested"],
      relevant_context: "Coder Agent route selected.",
      constraints: [],
    });

    const merged = JSON.parse(mergeRepoFirstResearchSources(request, response));

    expect(merged.relevant_context).toContain("Phase 7C / Increment 7C.4");
    expect(merged.phase_label).toBe("Phase 7C");
    expect(merged.increment_label).toBe("Increment 7C.4");
  });
});
