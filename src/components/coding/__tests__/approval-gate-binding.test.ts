/// <reference types="vitest/globals" />

import {
  buildCombinedApprovalPreviewAfterDiff,
  deriveApprovalGateProposal,
} from "@/components/coding/approval-gate-binding";

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

const SOURCE_PROXY_DECISION_DIFF = [
  "diff --git a/source_proxy/api/decision.py b/source_proxy/api/decision.py",
  "--- a/source_proxy/api/decision.py",
  "+++ b/source_proxy/api/decision.py",
  "@@ -1 +1 @@",
  "-old",
  "+new",
  "",
].join("\n");

describe("approval gate binding", () => {
  it("derives a concrete create-file approval proposal from an implementation prompt", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        task_classification: "implementation",
      },
      {
        prompt_text: [
          "# Source Manual Prompt Packet",
          "Create the file src/app/design-demo/coding/page.tsx.",
          "Use the existing dashboard shell patterns.",
        ].join("\n"),
      },
    );

    expect(proposal).toEqual({
      action: "create file",
      target: "src/app/design-demo/coding/page.tsx",
    });
  });

  it("prefers explicit proposed_action and target markers when present", () => {
    const proposal = deriveApprovalGateProposal(
      { task_classification: "implementation" },
      {
        prompt_text: [
          "proposed_action: apply generated page code",
          "target: src/app/design-demo/coding/page.tsx",
          "```tsx",
          "export default function Page() {",
          "  return <main>Approved</main>;",
          "}",
          "```",
        ].join("\n"),
      },
    );

    expect(proposal).toEqual({
      action: "apply generated page code",
      content: [
        "export default function Page() {",
        "  return <main>Approved</main>;",
        "}",
        "",
      ].join("\n"),
      target: "src/app/design-demo/coding/page.tsx",
    });
  });

  it("does not arm the approval gate for non-implementation planning", () => {
    const proposal = deriveApprovalGateProposal(
      { task_classification: "codebase_analysis" },
      { prompt_text: "Review src/app/design-demo/coding/page.tsx." },
    );

    expect(proposal).toBeNull();
  });

  it("does not arm the approval gate for encoded path blockers", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["encoded_path_not_allowed"],
        task_classification: "implementation",
      },
      {
        prompt_text: [
          "proposed_action: update encoded target",
          "target: %2e%2e/outside.md",
          "```md",
          "blocked",
          "```",
        ].join("\n"),
        reason_code: "encoded_path_not_allowed",
        target: "%2e%2e/outside.md",
      },
    );

    expect(proposal).toBeNull();
  });

  it("binds proposed_diff from the packet when prompt_text is a coder stub", () => {
    const patch = [
      "--- a/labs/coding/CodingAgentInterface.tsx",
      "+++ b/labs/coding/CodingAgentInterface.tsx",
      "@@ -1,3 +1,4 @@",
      " alpha",
      "-beta",
      "+beta-fixed",
      " gamma",
      "",
    ].join("\n");

    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        task_classification: "implementation",
      },
      {
        prompt_text:
          "Coder Agent produced a unified diff for the approval gate (target: labs/coding/CodingAgentInterface.tsx).",
        proposed_diff: patch,
        target: "labs/coding/CodingAgentInterface.tsx",
      },
    );

    expect(proposal?.target).toBe("labs/coding/CodingAgentInterface.tsx");
    expect(proposal?.proposedDiff).toContain("@@");
    expect(proposal?.proposedDiff).toContain("beta-fixed");
  });

  it("binds deterministic backend Markdown diffs without requiring prompt content", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        resolved_target: {
          exists: true,
          path: "docs/phase-8-manual-check.md",
          source: "explicit_line",
        },
        task_classification: "implementation",
      },
      {
        prompt_text:
          "Coder Agent produced replacement content that the backend converted into a unified diff for the approval gate.",
        proposed_diff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      {
        currentTaskText: "Target file: docs/phase-8-manual-check.md",
        resolvedTargetPath: "docs/phase-8-manual-check.md",
      },
    );

    expect(proposal).toEqual({
      action: "implement proposed file change",
      proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
      target: "docs/phase-8-manual-check.md",
    });
  });

  it("does not bind a backend standard unified diff to the wrong explicit target", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        resolved_target: {
          exists: true,
          path: "labs/coding/CodingAgentInterface.tsx",
          source: "explicit_line",
        },
        task_classification: "implementation",
      },
      {
        prompt_text: "Coder Agent produced a backend standard unified diff.",
        proposed_diff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      {
        currentTaskText: "Target file: labs/coding/CodingAgentInterface.tsx",
        resolvedTargetPath: "labs/coding/CodingAgentInterface.tsx",
      },
    );

    expect(proposal).toBeNull();
  });

  it("rejects backend diffs that touch source_proxy when the task targets docs", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        resolved_target: {
          exists: true,
          path: "docs/phase-8-manual-check.md",
          source: "explicit_line",
        },
        task_classification: "implementation",
      },
      {
        prompt_text: "Coder Agent produced a backend diff.",
        proposed_diff: SOURCE_PROXY_DECISION_DIFF,
        target: "source_proxy/api/decision.py",
      },
      {
        currentTaskText: "Target file: docs/phase-8-manual-check.md",
        resolvedTargetPath: "docs/phase-8-manual-check.md",
      },
    );

    expect(proposal).toBeNull();
  });

  it("does not bind a backend diff that also touches an extra file", () => {
    const multiFileDiff = [
      "diff --git a/docs/phase-8-manual-check.md b/docs/phase-8-manual-check.md",
      "--- a/docs/phase-8-manual-check.md",
      "+++ b/docs/phase-8-manual-check.md",
      "@@ -1 +1,2 @@",
      " # Phase 8 Manual Check",
      "+Safe target change.",
      "diff --git a/docs/other.md b/docs/other.md",
      "--- a/docs/other.md",
      "+++ b/docs/other.md",
      "@@ -1 +1,2 @@",
      " # Other",
      "+Wrong-scope change.",
      "",
    ].join("\n");

    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        resolved_target: {
          exists: true,
          path: "docs/phase-8-manual-check.md",
          source: "explicit_line",
        },
        task_classification: "implementation",
      },
      {
        prompt_text: "Coder Agent produced a backend diff.",
        proposed_diff: multiFileDiff,
        target: "docs/phase-8-manual-check.md",
      },
      {
        currentTaskText: "Target file: docs/phase-8-manual-check.md",
        resolvedTargetPath: "docs/phase-8-manual-check.md",
      },
    );

    expect(proposal).toBeNull();
  });

  it("does not arm approval when current task Target file only has a stale packet diff", () => {
    const patch = [
      "diff --git a/labs/coding/CodingAgentInterface.tsx b/labs/coding/CodingAgentInterface.tsx",
      "--- a/labs/coding/CodingAgentInterface.tsx",
      "+++ b/labs/coding/CodingAgentInterface.tsx",
      "@@ -1,3 +1,4 @@",
      " alpha",
      "-beta",
      "+beta-fixed",
      " gamma",
      "",
    ].join("\n");

    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        task_classification: "implementation",
      },
      {
        prompt_text:
          "Coder Agent produced a unified diff for the approval gate (target: labs/coding/CodingAgentInterface.tsx).",
        proposed_diff: patch,
        target: "labs/coding/CodingAgentInterface.tsx",
      },
      {
        currentTaskText: [
          "Target file: src/app/coding/design-demo/page.tsx",
          "",
          "Scaffold the route.",
        ].join("\n"),
        resolvedTargetPath: "src/app/coding/design-demo/page.tsx",
      },
    );

    expect(proposal).toBeNull();
  });

  it("does not arm approval for already satisfied coder packets", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        task_classification: "implementation",
      },
      {
        already_satisfied: true,
        prompt_text: "The target file already satisfies the requested task. No diff is needed.",
        reason_code: "coder_no_changes_needed",
        target: "src/app/coding/design-demo/page.tsx",
      },
      {
        currentTaskText: "Target file: src/app/coding/design-demo/page.tsx",
        resolvedTargetPath: "src/app/coding/design-demo/page.tsx",
      },
    );

    expect(proposal).toBeNull();
  });

  it("does not arm approval for subjective improvement no-diff packets", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        task_classification: "implementation",
      },
      {
        prompt_text:
          "No diff was produced, and subjective improvement cannot be marked already satisfied. Target: src/components/dashboard/ThemeStrip.tsx.",
        reason_code: "coder_subjective_improvement_requires_diff_or_review",
        target: "src/components/dashboard/ThemeStrip.tsx",
      },
      {
        currentTaskText:
          "make ThemeStrip feel more premium and alive. Target file: src/components/dashboard/ThemeStrip.tsx",
        resolvedTargetPath: "src/components/dashboard/ThemeStrip.tsx",
      },
    );

    expect(proposal).toBeNull();
  });

  it("does not arm approval for shallow visual improvement diffs", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        task_classification: "implementation",
      },
      {
        prompt_text:
          "The generated visual diff was too shallow. Target: src/components/dashboard/ThemeStrip.tsx.",
        proposed_diff: "",
        reason_code: "coder_visual_improvement_diff_too_shallow",
        target: "src/components/dashboard/ThemeStrip.tsx",
      },
      {
        currentTaskText:
          "make ThemeStrip feel more premium and alive. Target file: src/components/dashboard/ThemeStrip.tsx",
        resolvedTargetPath: "src/components/dashboard/ThemeStrip.tsx",
      },
    );

    expect(proposal).toBeNull();
  });

  it("uses backend resolved_target instead of task text parsing", () => {
    const patch = [
      "diff --git a/src/app/page.tsx b/src/app/page.tsx",
      "--- a/src/app/page.tsx",
      "+++ b/src/app/page.tsx",
      "@@ -1 +1 @@",
      "-old",
      "+new",
      "",
    ].join("\n");

    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        resolved_target: {
          path: "src/app/page.tsx",
          source: "explicit_line",
        },
        task_classification: "implementation",
      },
      {
        prompt_text: "Coder Agent produced a unified diff.",
        proposed_diff: patch,
        target: "src/app/page.tsx",
      },
      {
        currentTaskText: "Target file: src/old-parser-would-have-read-this.tsx",
      },
    );

    expect(proposal?.target).toBe("src/app/page.tsx");
    expect(proposal?.proposedDiff).toContain("+new");
  });

  it("returns null when coder model is not configured (no prompt-derived fake proposal)", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        task_classification: "implementation",
      },
      {
        reason_code: "coder_model_not_configured",
        coder_blocked: true,
        proposed_diff: "",
        prompt_text: "```diff\n@@ -1 +1 @@\n-old\n+new\n```",
        target: "docs/phase-8-manual-check.md",
      },
      {
        currentTaskText: "Target file: docs/phase-8-manual-check.md",
        resolvedTargetPath: "docs/phase-8-manual-check.md",
      },
    );

    expect(proposal).toBeNull();
  });

  it("does not arm approval for config-blocked route failure packets", () => {
    const proposal = deriveApprovalGateProposal(
      {
        recommended_route: "codex_cli",
        reason_codes: ["implementation_requested"],
        task_classification: "implementation",
      },
      {
        coder_blocked: true,
        prompt_text: "Codex CLI route is config-blocked and cannot produce an approvable diff.",
        reason_code: "codex_binary_not_found",
        target: "docs/phase-8-manual-check.md",
      },
      {
        currentTaskText: "Target file: docs/phase-8-manual-check.md",
        resolvedTargetPath: "docs/phase-8-manual-check.md",
      },
    );

    expect(proposal).toBeNull();
  });

  it("does not arm approval when Codex route live execution is disabled", () => {
    const proposal = deriveApprovalGateProposal(
      {
        recommended_route: "codex_cli",
        reason_codes: ["implementation_requested"],
        task_classification: "implementation",
      },
      {
        prompt_text: "Codex route live execution is disabled.",
        proposed_diff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        reason_code: "codex_route_live_execution_not_enabled",
        target: "docs/phase-8-manual-check.md",
      },
      {
        currentTaskText: "Target file: docs/phase-8-manual-check.md",
        resolvedTargetPath: "docs/phase-8-manual-check.md",
      },
    );

    expect(proposal).toBeNull();
  });

  it("does not arm approval from a research-only path when the user task names a different file", () => {
    const patch = [
      "diff --git a/source_proxy/api/decision.py b/source_proxy/api/decision.py",
      "--- a/source_proxy/api/decision.py",
      "+++ b/source_proxy/api/decision.py",
      "@@ -1 +1 @@",
      "-a",
      "+b",
      "",
    ].join("\n");

    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested", "repo_first_research"],
        task_classification: "implementation",
      },
      {
        prompt_text: [
          "Source 1: Repo: source_proxy/api/decision.py",
          "Coder Agent produced a unified diff for the approval gate (target: source_proxy/api/decision.py).",
        ].join("\n"),
        proposed_diff: patch,
        target: "source_proxy/api/decision.py",
      },
      {
        currentTaskText: "Update docs/phase-8-manual-check.md with a checklist item.",
      },
    );

    expect(proposal).toBeNull();
  });

  it("returns null when coder is blocked without a backend unified diff", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        task_classification: "implementation",
      },
      {
        reason_code: "coder_agent_blocked",
        coder_blocked: true,
        proposed_diff: "",
        prompt_text: "```diff\n@@ -1 +1 @@\n-a\n+b\n```",
        target: "docs/foo.md",
      },
      {
        currentTaskText: "Target file: docs/foo.md",
        resolvedTargetPath: "docs/foo.md",
      },
    );

    expect(proposal).toBeNull();
  });

  it.each([
    ["missing proposed_diff", undefined],
    ["blank proposed_diff", ""],
    ["junk proposed_diff", "this is not a unified diff"],
  ])("does not arm approval for %s", (_label, proposedDiff) => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        resolved_target: {
          exists: true,
          path: "docs/phase-8-manual-check.md",
          source: "explicit_line",
        },
        task_classification: "implementation",
      },
      {
        prompt_text: "Coder Agent did not provide an approvable backend diff.",
        ...(proposedDiff === undefined ? {} : { proposed_diff: proposedDiff }),
        target: "docs/phase-8-manual-check.md",
      },
      {
        currentTaskText: "Target file: docs/phase-8-manual-check.md",
        resolvedTargetPath: "docs/phase-8-manual-check.md",
      },
    );

    expect(proposal).toBeNull();
  });

  it("does not treat a fenced fake prompt diff as the proposed backend diff", () => {
    const proposal = deriveApprovalGateProposal(
      {
        reason_codes: ["implementation_requested"],
        resolved_target: {
          exists: true,
          path: "docs/phase-8-manual-check.md",
          source: "explicit_line",
        },
        task_classification: "implementation",
      },
      {
        prompt_text: [
          "Coder Agent did not return proposed_diff.",
          "```diff",
          DOCS_APPEND_STANDARD_UNIFIED_DIFF.trimEnd(),
          "```",
        ].join("\n"),
        target: "docs/phase-8-manual-check.md",
      },
      {
        currentTaskText: "Target file: docs/phase-8-manual-check.md",
        resolvedTargetPath: "docs/phase-8-manual-check.md",
      },
    );

    expect(proposal).toBeNull();
  });
});

describe("buildCombinedApprovalPreviewAfterDiff", () => {
  it("upgrades stale blocked existing when diff preview is preview_ready", () => {
    const preview = buildCombinedApprovalPreviewAfterDiff({
      effectiveTarget: "src/app/proxy-backend/page.tsx",
      existing: {
        decision: "blocked",
        reason_codes: ["target_missing"],
        requires_human_approval: false,
      },
      initialDiffPreview: {
        git_apply_check_ok: true,
        status: "preview_ready",
      },
    });
    expect(preview?.requires_human_approval).toBe(true);
    expect(preview?.decision).toBe("requires_human_approval");
  });

  it("seeds requires_human_approval when diff preview is preview_ready", () => {
    const preview = buildCombinedApprovalPreviewAfterDiff({
      effectiveTarget: "src/app/proxy-backend/page.tsx",
      existing: null,
      initialDiffPreview: {
        git_apply_check_ok: true,
        status: "preview_ready",
      },
    });
    expect(preview?.requires_human_approval).toBe(true);
    expect(preview?.decision).toBe("requires_human_approval");
  });
});
