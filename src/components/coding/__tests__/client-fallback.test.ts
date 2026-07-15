/// <reference types="vitest/globals" />

import {
  buildQualityGateChecks,
} from "@labs/coding/CodingAgentInterface";

const DOCS_APPEND_STANDARD_UNIFIED_DIFF = [
  "--- a/docs/phase-8-manual-check.md",
  "+++ b/docs/phase-8-manual-check.md",
  "@@ -1,3 +1,4 @@",
  " # Phase 8 Manual Check",
  " ",
  " Approved diffs should require post-apply verification before completion.",
  "+Frontend coding proxy smoke test.",
  "",
].join("\n");

describe("backend-only coder approval gate", () => {
  it("quality gate blocks missing requirements before approval", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          status: "blocked",
          git_apply_check_ok: true,
          changed_files: [{ path: "src/app/coding/design-demo/page.tsx" }],
          typescript_check: { ok: true, summary: "TypeScript parser accepted changed files." },
          requirement_coverage: {
            ok: false,
            missing: ["missing exact text: Design Demo — Vibe Test Canvas"],
          },
        },
        unifiedDiff: [
          "diff --git a/src/app/coding/design-demo/page.tsx b/src/app/coding/design-demo/page.tsx",
          "--- a/src/app/coding/design-demo/page.tsx",
          "+++ b/src/app/coding/design-demo/page.tsx",
          "@@ -1 +1 @@",
          "-export default function Page() { return null; }",
          "+export default function Page() { return <main />; }",
          "",
        ].join("\n"),
      },
      gate: {
        action: "modify file",
        alreadySatisfied: false,
        approvedAt: null,
        content: "",
        deniedAt: null,
        error: null,
        execution: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
        isChecking: false,
        preview: null,
        proposedDiff: "",
        target: "src/app/coding/design-demo/page.tsx",
      },
    });

    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Requirement Coverage",
        required: true,
        status: "fail",
      }),
    );
  });

  it("quality gate reports backend diffs without client fallback state", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          status: "preview_ready",
          git_apply_check_ok: true,
          changed_files: [{ path: "notes/design-demo.md" }],
        },
        unifiedDiff: [
          "diff --git a/notes/design-demo.md b/notes/design-demo.md",
          "new file mode 100644",
          "--- /dev/null",
          "+++ b/notes/design-demo.md",
          "@@ -0,0 +1 @@",
          "+placeholder",
          "",
        ].join("\n"),
      },
      gate: {
        action: "create file",
        alreadySatisfied: false,
        approvedAt: null,
        content: "",
        deniedAt: null,
        error: null,
        execution: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
        isChecking: false,
        preview: null,
        proposedDiff: "",
        target: "notes/design-demo.md",
      },
    });
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Fallback Status",
        required: true,
        status: "pass",
      }),
    );
  });

  it("quality gate treats skipped TypeScript checks as info for markdown-only diffs", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          status: "preview_ready",
          git_apply_check_ok: true,
          changed_files: [{ path: "docs/phase-8-manual-check.md" }],
          requirement_coverage: { ok: true, missing: [] },
          typescript_check: {
            ok: true,
            skipped: true,
            summary: "No TS/TSX files changed.",
          },
        },
        unifiedDiff: [
          "diff --git a/docs/phase-8-manual-check.md b/docs/phase-8-manual-check.md",
          "new file mode 100644",
          "--- /dev/null",
          "+++ b/docs/phase-8-manual-check.md",
          "@@ -0,0 +1 @@",
          "+placeholder",
          "",
        ].join("\n"),
      },
      gate: {
        action: "create file",
        alreadySatisfied: false,
        approvedAt: null,
        content: "",
        deniedAt: null,
        error: null,
        execution: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
        isChecking: false,
        preview: null,
        proposedDiff: "",
        target: "docs/phase-8-manual-check.md",
      },
    });

    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "TypeScript Syntax",
        required: false,
        status: "info",
      }),
    );
  });

  it("quality gate treats already satisfied packets as complete with no diff", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: null,
        unifiedDiff: "",
      },
      gate: {
        action: "already_satisfied",
        alreadySatisfied: true,
        approvedAt: null,
        content: "",
        deniedAt: null,
        error: null,
        execution: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
        isChecking: false,
        preview: {
          decision: "already_satisfied",
          reason_codes: ["coder_no_changes_needed"],
          requires_human_approval: false,
        },
        proposedDiff: "",
        target: "src/app/coding/design-demo/page.tsx",
      },
    });

    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Target Match",
        status: "pass",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Requirement Coverage",
        status: "pass",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Git Apply Check",
        required: false,
        status: "info",
      }),
    );
    expect(checks).not.toContainEqual(
      expect.objectContaining({
        status: "fail",
      }),
    );
  });

  it("standard backend unified diffs keep client fallback disabled", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          status: "preview_ready",
          git_apply_check_ok: true,
          changed_files: [{ path: "docs/phase-8-manual-check.md" }],
          requirement_coverage: { ok: true, missing: [] },
          typescript_check: {
            ok: true,
            skipped: true,
            summary: "No TS/TSX files changed.",
          },
        },
        unifiedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
      },
      gate: {
        action: "modify file",
        alreadySatisfied: false,
        approvedAt: null,
        content: "",
        deniedAt: null,
        error: null,
        execution: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
        isChecking: false,
        preview: null,
        proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      resolvedTargetPath: "docs/phase-8-manual-check.md",
    });

    expect(checks).toContainEqual(
      expect.objectContaining({
        detail: "No client fallback scaffold is being used.",
        label: "Fallback Status",
        required: true,
        status: "pass",
      }),
    );
  });

  it("target match can pass using the resolved Architect target without a diff", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: null,
        unifiedDiff: "",
      },
      gate: {
        action: "needs_coder_diff",
        alreadySatisfied: false,
        approvedAt: null,
        content: "",
        deniedAt: null,
        error: null,
        execution: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
        isChecking: false,
        preview: {
          decision: "blocked",
          reason_codes: ["coder_sync_timeout", "coder_proxy_deadline_blocked"],
          requires_human_approval: false,
        },
        proposedDiff: "",
        target: "docs/phase-8-manual-check.md",
      },
      resolvedTargetPath: "docs/phase-8-manual-check.md",
    });

    expect(checks).toContainEqual(
      expect.objectContaining({
        detail: "Proposal is pinned to docs/phase-8-manual-check.md.",
        label: "Target Match",
        status: "pass",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Git Apply Check",
        status: "waiting",
      }),
    );
  });

  it("coder sync timeout without backend diff does not pass approval gates or create fallback state", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: null,
        unifiedDiff: "",
      },
      gate: {
        action: "needs_coder_diff",
        alreadySatisfied: false,
        approvedAt: null,
        content: "",
        deniedAt: null,
        error: null,
        execution: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
        isChecking: false,
        preview: {
          decision: "blocked",
          reason_codes: ["coder_sync_timeout", "coder_proxy_deadline_blocked"],
          requires_human_approval: false,
        },
        proposedDiff: "",
        target: "docs/phase-8-manual-check.md",
      },
      resolvedTargetPath: "docs/phase-8-manual-check.md",
    });

    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Git Apply Check",
        required: true,
        status: "waiting",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Fallback Status",
        status: "pass",
      }),
    );
    expect(checks.some((check) => check.required && check.status !== "pass")).toBe(true);
  });

  it("quality gate blocks shallow visual improvement diffs before approval", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: null,
        unifiedDiff: "",
      },
      gate: {
        action: "needs_coder_diff",
        alreadySatisfied: false,
        approvedAt: null,
        content: "",
        deniedAt: null,
        error: null,
        execution: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
        isChecking: false,
        preview: {
          decision: "needs_coder_diff",
          reason_codes: [
            "needs_coder_diff",
            "coder_visual_improvement_diff_too_shallow",
          ],
          requires_human_approval: false,
          safety_message:
            "The generated diff was too shallow for this visual improvement task.",
        },
        proposedDiff: "",
        target: "src/components/dashboard/ThemeStrip.tsx",
      },
    });

    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Target Match",
        status: "pass",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Requirement Coverage",
        status: "fail",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Git Apply Check",
        status: "info",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "TypeScript Syntax",
        required: false,
        status: "info",
      }),
    );
  });
});
