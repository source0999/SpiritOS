import { describe, expect, it } from "vitest";

import { buildToolRuntimeSurface, toolRuntimeDiagnosticsText } from "@/lib/coding/tool-runtime-surface";

describe("tool runtime surface", () => {
  it("shows TaskSpec, action transcript, diff, checks, and advisory truth without apply authority", () => {
    const surface = buildToolRuntimeSurface({
      task_spec_intake: {
        allowed_files: ["docs/phase-8-manual-check.md"],
        clarification_state: "not_needed",
        model_lane: "local_coder",
        task_kind: "edit_existing",
        workspace_mode: "disposable_workspace",
      },
      parsed_actions: [
        {
          action_type: "WriteFile",
          adapter_source: "generic",
          target: "docs/phase-8-manual-check.md",
        },
      ],
      executions: [
        {
          result: {
            diff_summary: "--- a/docs/phase-8-manual-check.md\n+++ b/docs/phase-8-manual-check.md\n+Plan 6 proof",
            files_touched: ["docs/phase-8-manual-check.md"],
            status: "completed",
            stdout: "check ok",
          },
        },
      ],
    });

    expect(surface.applyAuthority).toBe(false);
    expect(surface.taskSpec.taskKind).toBe("edit_existing");
    expect(surface.taskSpec.allowedFiles).toEqual(["docs/phase-8-manual-check.md"]);
    expect(surface.actions[0]).toMatchObject({
      actionType: "WriteFile",
      status: "completed",
      target: "docs/phase-8-manual-check.md",
    });
    expect(surface.diffSummary).toContain("Plan 6 proof");
    expect(surface.checkOutput).toContain("check ok");
    expect(surface.safeApplyStatus).toBe("blocked unless separately approved");
    expect(surface.advisoryTruth.macSubagentsAdvisoryOnly).toBe(true);
  });

  it("keeps blocked reasons and Mac/subagent references in copy diagnostics", () => {
    const surface = buildToolRuntimeSurface({
      taskSpecIntake: {
        allowedFiles: [".env.local"],
        clarificationState: "blocked",
        taskKind: "protected_path",
      },
      parsedActions: [
        {
          actionType: "WriteFile",
          adapterSource: "mac_worker",
          target: ".env.local",
        },
      ],
      executions: [
        {
          result: {
            blockedReason: "Action target is protected or forbidden.",
            errorCode: "protected_path",
            status: "blocked",
          },
        },
      ],
    });
    const text = toolRuntimeDiagnosticsText(surface);

    expect(text).toContain("task_kind: protected_path");
    expect(text).toContain("blocked_reasons: Action target is protected or forbidden.");
    expect(text).toContain("safe_apply_status: blocked unless separately approved");
    expect(text).toContain("mac_subagents_advisory_only: true");
    expect(text).toContain("source_proxy_final_gate: true");
    expect(text).not.toContain("apply_authority: true");
  });
});
