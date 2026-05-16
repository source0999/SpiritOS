/// <reference types="vitest/globals" />

import { createElement } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";

import { ROUTE_RESPONSE_INVALID_PREFIX } from "@/lib/coding/proxy-route-payload";
import {
  ApprovalGatePanel,
  architectPlanDisplayTarget,
  buildQualityGateChecks,
  CodingStabilityCard,
  CodingTaskStateCard,
  deriveApprovalStateChecklist,
  deriveCodingStabilitySummary,
  deriveCodingTaskStateSummary,
  deriveReviewerAgentChecks,
  deriveTaskTranscript,
  deriveTerminalLongTaskStateForApproval,
  deriveWorkflowMemorySnapshot,
  latestLongTaskEvidenceLines,
  knownGoodPromptPatterns,
  LongRunningTaskPanel,
  longTaskVisibleState,
  mergeWorkflowMemorySnapshots,
  promptTextForCoderPacket,
  shouldAppendTaskActivityLog,
  taskSpecForManualPreview,
  taskSpecForPlan,
  testerAgentProposals,
  TaskCompletionStatus,
  VerificationSummary,
  workflowStep,
} from "@/components/coding/CodingAgentInterface";

type WorkflowStepArgs = Parameters<typeof workflowStep>[0];

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

function baseArgs(overrides: Partial<WorkflowStepArgs> = {}): WorkflowStepArgs {
  return {
    approvalGate: {
      action: "",
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
      target: "",
    },
    diffVerification: {
      error: null,
      isChecking: false,
      preview: null,
      unifiedDiff: "",
    },
    finalOutput: null,
    isRunning: false,
    longRunningTask: {
      description: "",
      error: null,
      isChecking: false,
      response: null,
    },
    ...overrides,
  };
}

function stabilitySummary(overrides: Partial<WorkflowStepArgs> = {}) {
  const args = baseArgs(overrides);
  return deriveCodingStabilitySummary({
    approvalGate: args.approvalGate,
    architectPlan: null,
    diffVerification: args.diffVerification,
    finalOutput: args.finalOutput,
    isRunning: args.isRunning,
    logs: [],
    longRunningTask: args.longRunningTask,
  });
}

function approvalPanelProps(
  overrides: Partial<Parameters<typeof ApprovalGatePanel>[0]> = {},
): Parameters<typeof ApprovalGatePanel>[0] {
  return {
    architectPlan: null,
    coderAgentLocalDiff: true,
    diffVerification: baseArgs().diffVerification,
    gate: baseArgs().approvalGate,
    onActionChange: vi.fn(),
    onApprove: vi.fn(),
    onContentChange: vi.fn(),
    onDeny: vi.fn(),
    onPreview: vi.fn(),
    onTargetChange: vi.fn(),
    resolvedTargetPath: "docs/phase-8-manual-check.md",
    task: null,
    ...overrides,
  };
}

function longTaskPanelProps(
  overrides: Partial<Parameters<typeof LongRunningTaskPanel>[0]> = {},
): Parameters<typeof LongRunningTaskPanel>[0] {
  return {
    onCancel: vi.fn(),
    onDescriptionChange: vi.fn(),
    onDiffSelect: vi.fn(),
    onPoll: vi.fn(),
    onRejectPlan: vi.fn(),
    onRetry: vi.fn(),
    onRetryVerification: vi.fn(),
    onStart: vi.fn(),
    state: baseArgs().longRunningTask,
    ...overrides,
  };
}

afterEach(() => {
  cleanup();
});

describe("knownGoodPromptPatterns", () => {
  it("keeps the roadmap seed patterns available for reuse", () => {
    expect(knownGoodPromptPatterns.map((pattern) => pattern.id)).toEqual([
      "safe-docs-append",
      "allowed-file-edit",
      "rejected-protected-path",
      "rejected-traversal-path",
      "rejected-target-mismatch",
    ]);
    expect(
      knownGoodPromptPatterns.every((pattern) => pattern.prompt.includes("Target file:")),
    ).toBe(true);
    expect(
      knownGoodPromptPatterns.find((pattern) => pattern.id === "rejected-protected-path")
        ?.prompt,
    ).toContain(".env.local");
    expect(
      knownGoodPromptPatterns.find((pattern) => pattern.id === "rejected-traversal-path")
        ?.prompt,
    ).toContain("../outside.txt");
  });
});

describe("testerAgentProposals", () => {
  it("suggests Manual Check 10+ without install instructions", () => {
    expect(testerAgentProposals.map((proposal) => proposal.id)).toEqual([
      "manual-check-10",
      "manual-check-11",
      "manual-check-12",
    ]);
    expect(
      testerAgentProposals.every((proposal) =>
        proposal.prompt.includes("Do not install the case. Do not edit any file."),
      ),
    ).toBe(true);
    expect(testerAgentProposals[0]?.expectedOutcome).toContain("applied_anything remains false");
  });
});

describe("deriveWorkflowMemorySnapshot", () => {
  it("persists the workflow story fields needed after refresh", () => {
    const snapshot = deriveWorkflowMemorySnapshot({
      approvalGate: {
        ...baseArgs().approvalGate,
        approvedAt: "2026-05-16T15:00:00.000Z",
        deniedAt: "2026-05-16T15:05:00.000Z",
        preview: {
          decision: "blocked",
          reason_codes: ["task_spec_allowed_file_violation"],
          requires_human_approval: false,
        },
        target: "docs/phase-8-manual-check.md",
      },
      decisionMemory: [
        {
          classification: "implement",
          completedAt: "2026-05-16T15:00:00.000Z",
          id: "decision-1",
          model: "test",
          reasonCodes: [],
          recommendation: "Run with Proxy Agent",
          risk: "Low",
          route: "local_route",
          task: "Target file: docs/phase-8-manual-check.md",
        },
      ],
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          blocked_reasons: [
            {
              path: "source_proxy/api/decision.py",
              reason_code: "task_spec_allowed_file_violation",
            },
          ],
          risk: "blocked",
          status: "blocked",
          verification_plan: ["Review changed files and risk flags."],
        },
        unifiedDiff: SOURCE_PROXY_DECISION_DIFF,
      },
      finalOutput: null,
      knownGoodExamples: knownGoodPromptPatterns,
      logs: [
        {
          id: 1,
          label: "Diff verification",
          detail: "blocked: 1 changed file; risk blocked.",
          level: "warning",
        },
      ],
      longRunningTask: {
        ...baseArgs().longRunningTask,
        response: {
          task: {
            description: "docs task",
            id: "task-memory",
            progress: 50,
            status: "blocked",
          },
        },
      },
      proxySafetySmoke: {
        error: null,
        isRunning: false,
        lastRunAt: "2026-05-16T15:00:00.000Z",
        payload: {
          applied_anything: false,
          cases: [],
          mode: "dry_run",
          suite: "phase-4e-safety-seed",
          summary: { failed: 0, passed: 3, skipped: 0 },
        },
      },
      testerProposals: testerAgentProposals,
    });

    expect(snapshot.taskIds).toContain("task-memory");
    expect(snapshot.lastKnownStatus).toBe("blocked");
    expect(snapshot.blockers).toContain("task_spec_allowed_file_violation");
    expect(snapshot.testReports.join(" ")).toContain("phase-4e-safety-seed");
    expect(snapshot.approvals.join(" ")).toContain("Human approved");
    expect(snapshot.rejections.join(" ")).toContain("Human rejected");
    expect(snapshot.knownGoodExamples).toContain("Safe docs append");
    expect(snapshot.knownGoodExamples).toContain("Manual Check 10");
  });

  it("merges refreshed sparse memory without erasing the task story", () => {
    const merged = mergeWorkflowMemorySnapshots(
      {
        approvals: ["Human approved 11:00:00 AM."],
        blockers: ["old blocker"],
        knownGoodExamples: ["Safe docs append"],
        lastKnownStatus: "running",
        rejections: [],
        taskIds: ["task_previous"],
        testReports: ["phase-4e-safety-seed: 3 passed"],
        updatedAt: "2026-05-16T15:00:00.000Z",
      },
      {
        approvals: [],
        blockers: ["new blocker"],
        knownGoodExamples: ["Manual Check 10"],
        lastKnownStatus: "No active workflow status.",
        rejections: [],
        taskIds: [],
        testReports: [],
        updatedAt: "2026-05-16T15:05:00.000Z",
      },
    );

    expect(merged.taskIds).toContain("task_previous");
    expect(merged.lastKnownStatus).toBe("running");
    expect(merged.blockers).toEqual(["new blocker", "old blocker"]);
    expect(merged.testReports).toContain("phase-4e-safety-seed: 3 passed");
    expect(merged.knownGoodExamples).toEqual(["Manual Check 10", "Safe docs append"]);
  });
});

describe("deriveCodingStabilitySummary", () => {
  it("shows idle before a task starts", () => {
    expect(stabilitySummary().primaryState).toBe("Idle");
    expect(stabilitySummary().target).toBe("No target resolved");
  });

  it("shows routing while the prompt route is loading", () => {
    expect(stabilitySummary({ isRunning: true }).primaryState).toBe("Routing");
  });

  it("shows needs approval for a valid preview with passing gates", () => {
    const summary = stabilitySummary({
      approvalGate: {
        ...baseArgs().approvalGate,
        action: "modify file",
        preview: {
          decision: "requires_human_approval",
          reason_codes: [],
          requires_human_approval: true,
        },
        proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          status: "preview_ready",
          git_apply_check_ok: true,
          changed_files: [{ path: "docs/phase-8-manual-check.md" }],
        },
        unifiedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
      },
    });

    expect(summary.primaryState).toBe("Needs approval");
    expect(summary.diffState).toBe("preview ready");
    expect(summary.approvalState).toBe("requires human approval");
  });

  it("shows needs_coder_diff as blocked", () => {
    const summary = stabilitySummary({
      approvalGate: {
        ...baseArgs().approvalGate,
        action: "needs_coder_diff",
        preview: {
          decision: "needs_coder_diff",
          reason_codes: ["needs_coder_diff"],
          requires_human_approval: false,
        },
        target: "docs/phase-8-manual-check.md",
      },
    });

    expect(summary.primaryState).toBe("Blocked");
    expect(summary.lastBlocker).toBe("needs_coder_diff");
    expect(summary.diffState).toBe("no approvable diff");
  });

  it("shows client-rejected proposed diffs as blocked with the reason", () => {
    const summary = stabilitySummary({
      approvalGate: {
        ...baseArgs().approvalGate,
        action: "needs_coder_diff",
        preview: {
          decision: "blocked",
          reason_codes: ["needs_coder_diff", "client_rejected_proposed_diff"],
          requires_human_approval: false,
        },
        target: "docs/phase-8-manual-check.md",
      },
    });

    expect(summary.primaryState).toBe("Blocked");
    expect(summary.diffState).toBe("client rejected diff");
    expect(summary.lastBlocker).toBe("client_rejected_proposed_diff");
  });

  it("shows reviewer retry exhaustion as blocked with approval unavailable", () => {
    const summary = stabilitySummary({
      approvalGate: {
        ...baseArgs().approvalGate,
        action: "needs_coder_diff",
        coderDiagnostics: {
          coder_attempt_count: 2,
          last_reviewer_blockers: ["missing_must_contain: RequiredLiteral"],
          reviewer_retry_count: 1,
        },
        preview: {
          decision: "blocked",
          reason_codes: ["blocked_after_retries", "reviewer_blocked"],
          requires_human_approval: false,
        },
        target: "src/lib/coding/__tests__/unified-diff-paths.test.ts",
      },
    });

    expect(summary.primaryState).toBe("Blocked");
    expect(summary.approvalState).toBe("unavailable");
    expect(summary.lastBlocker).toBe("blocked_after_retries");
  });

  it("shows target_unresolved as blocked without a fake target", () => {
    const summary = stabilitySummary({
      approvalGate: {
        ...baseArgs().approvalGate,
        preview: {
          decision: "blocked",
          reason_codes: ["target_unresolved"],
        },
      },
      finalOutput: {
        attachedFiles: [],
        completedAt: "t",
        contextTurnCount: 0,
        decision: { reason_codes: ["target_unresolved"] },
        decisionPayload: "{}",
        promptText: "",
        researchSources: [],
        requests: [],
        runId: 1,
        selfCorrection: {
          checks: [],
          confidence: 0,
          reasons: [],
          refinedInstruction: "",
          triggered: false,
        },
        summary: "Route ok",
      },
    });

    expect(summary.primaryState).toBe("Blocked");
    expect(summary.target).toBe("No target resolved");
    expect(summary.lastBlocker).toBe("target_unresolved");
  });

  it("prioritizes protected path blockers over generic no-diff copy", () => {
    const summary = stabilitySummary({
      approvalGate: {
        ...baseArgs().approvalGate,
        action: "needs_coder_diff",
        preview: {
          decision: "blocked",
          reason_codes: ["protected_path"],
          requires_human_approval: false,
        },
        target: ".env.local",
      },
    });

    expect(summary.primaryState).toBe("Blocked");
    expect(summary.approvalState).toBe("unavailable");
    expect(summary.lastBlocker).toBe("protected_path");
    expect(summary.target).toBe(".env.local");
  });

  it("prioritizes path escape blockers over inferred targets", () => {
    const summary = stabilitySummary({
      approvalGate: {
        ...baseArgs().approvalGate,
        action: "needs_coder_diff",
        preview: {
          decision: "blocked",
          reason_codes: ["path_escape"],
          requires_human_approval: false,
        },
        target: "../outside.txt",
      },
      finalOutput: {
        attachedFiles: [],
        completedAt: "t",
        contextTurnCount: 0,
        decision: {
          reason_codes: ["path_escape"],
          resolved_target: { path: "../outside.txt" },
        },
        decisionPayload: "{}",
        promptText: "",
        researchSources: [],
        requests: [],
        runId: 1,
        selfCorrection: {
          checks: [],
          confidence: 0,
          reasons: [],
          refinedInstruction: "",
          triggered: false,
        },
        summary: "Route ok",
      },
    });

    expect(summary.primaryState).toBe("Blocked");
    expect(summary.lastBlocker).toBe("path_escape");
    expect(summary.target).toBe("../outside.txt");
    expect(summary.target).not.toBe("public/next.svg");
  });

  it("shows applied docs-only work as verification required", () => {
    const summary = stabilitySummary({
      longRunningTask: {
        ...baseArgs().longRunningTask,
        response: {
          task: {
            description: "Docs task",
            id: "task-docs",
            post_apply_verification: {
              docs_only: true,
              required: true,
              status: "verification_ready",
            },
            status: "applied_needs_verification",
          },
        },
      },
    });

    expect(summary.primaryState).toBe("Applied, verification required");
    expect(summary.executionState).toBe("applied_needs_verification");
    expect(summary.verificationState).toBe("verification ready");
  });

  it("shows verification_ready when verification is ready before applied status is reflected", () => {
    const summary = stabilitySummary({
      longRunningTask: {
        ...baseArgs().longRunningTask,
        response: {
          task: {
            description: "Docs task",
            id: "task-docs",
            post_apply_verification: {
              required: true,
              status: "verification_ready",
            },
            status: "running",
          },
        },
      },
    });

    expect(summary.primaryState).toBe("Verification ready");
    expect(summary.verificationState).toBe("verification ready");
  });

  it("shows completed verified docs-only tasks as done", () => {
    const summary = stabilitySummary({
      longRunningTask: {
        ...baseArgs().longRunningTask,
        response: {
          task: {
            description: "Docs task",
            id: "task-docs",
            post_apply_verification: {
              docs_only: true,
              required: true,
              status: "verified",
            },
            status: "completed",
          },
        },
      },
    });

    expect(summary.primaryState).toBe("Done");
    expect(summary.executionState).toBe("verified / completed");
    expect(summary.verificationState).toBe("verified");
  });

  it("does not show stale memory as the active target", () => {
    const summary = deriveCodingStabilitySummary({
      approvalGate: baseArgs().approvalGate,
      architectPlan: null,
      diffVerification: baseArgs().diffVerification,
      finalOutput: null,
      isRunning: false,
      logs: [],
      longRunningTask: baseArgs().longRunningTask,
    });

    expect(summary.target).toBe("No target resolved");
  });
});

describe("deriveCodingTaskStateSummary", () => {
  it("shows blocked preview state with allowed files and no approval availability", () => {
    const args = baseArgs({
      approvalGate: {
        ...baseArgs().approvalGate,
        target: "docs/phase-8-manual-check.md",
      },
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          blocked_reasons: [
            {
              path: "source_proxy/api/decision.py",
              reason_code: "task_spec_allowed_file_violation",
            },
          ],
          risk: "blocked",
          status: "blocked",
          task_spec_check: {
            allowed_files: ["docs/phase-8-manual-check.md"],
            changed_files: ["source_proxy/api/decision.py"],
            ok: false,
            reason_codes: ["task_spec_allowed_file_violation"],
            target: "docs/phase-8-manual-check.md",
          },
          would_apply_diff: false,
          would_execute: false,
        },
        unifiedDiff: SOURCE_PROXY_DECISION_DIFF,
      },
    });

    const summary = deriveCodingTaskStateSummary({
      approvalGate: args.approvalGate,
      architectPlan: null,
      diffVerification: args.diffVerification,
      finalOutput: null,
      isRunning: false,
      logs: [],
      longRunningTask: args.longRunningTask,
    });

    expect(summary).toMatchObject({
      allowedFiles: "docs/phase-8-manual-check.md",
      appliedAnything: "false",
      approvalAvailable: "false",
      currentWorkflowState: "Blocked",
      lastBlocker: "task_spec_allowed_file_violation",
      safetyLevel: "blocked",
      target: "docs/phase-8-manual-check.md",
      wouldChangeFiles: "no",
    });
  });

  it("shows approval available only after approval preview requires human approval", () => {
    const args = baseArgs({
      approvalGate: {
        ...baseArgs().approvalGate,
        action: "modify file",
        preview: {
          decision: "requires_human_approval",
          reason_codes: [],
          requires_human_approval: true,
        },
        proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          changed_files: [{ path: "docs/phase-8-manual-check.md" }],
          git_apply_check_ok: true,
          risk: "low",
          status: "preview_ready",
          task_spec_check: {
            allowed_files: ["docs/phase-8-manual-check.md"],
            changed_files: ["docs/phase-8-manual-check.md"],
            ok: true,
            reason_codes: [],
          },
          would_apply_diff: false,
        },
        unifiedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
      },
    });

    const summary = deriveCodingTaskStateSummary({
      approvalGate: args.approvalGate,
      architectPlan: null,
      diffVerification: args.diffVerification,
      finalOutput: null,
      isRunning: false,
      logs: [],
      longRunningTask: args.longRunningTask,
    });

    expect(summary.approvalAvailable).toBe("true");
    expect(summary.currentWorkflowState).toBe("Needs approval");
    expect(summary.safetyLevel).toBe("low");
  });

  it("renders the explicit task state fields", () => {
    render(
      createElement(CodingTaskStateCard, {
        summary: {
          allowedFiles: "docs/phase-8-manual-check.md",
          appliedAnything: "false",
          approvalAvailable: "false",
          currentWorkflowState: "Blocked",
          lastBlocker: "protected_path",
          safetyLevel: "blocked",
          target: ".env.local",
          wouldChangeFiles: "no",
        },
      }),
    );

    expect(screen.getByText("Task state")).toBeTruthy();
    expect(screen.getByText("Allowed files")).toBeTruthy();
    expect(screen.getByText("Approval available")).toBeTruthy();
    expect(screen.getByText("Applied anything")).toBeTruthy();
    expect(screen.getByText(".env.local")).toBeTruthy();
  });
});

describe("deriveTaskTranscript", () => {
  it("groups activity logs into role transcript sections", () => {
    const transcript = deriveTaskTranscript({
      approvalGate: {
        ...baseArgs().approvalGate,
        preview: {
          decision: "blocked",
          reason_codes: ["protected_path"],
          requires_human_approval: false,
        },
        target: ".env.local",
      },
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          blocked_reasons: [{ path: ".env.local", reason_code: "protected_path" }],
          risk: "blocked",
          status: "blocked",
        },
        unifiedDiff: "",
      },
      logs: [
        {
          id: 1,
          label: "Route decision received",
          detail: "Classification: implementation; route: Coder Agent.",
          level: "success",
        },
        {
          id: 2,
          label: "Role transition",
          detail: "Architect -> Coder: architect_plan_ready.",
          level: "info",
        },
        {
          id: 3,
          label: "Diff verification",
          detail: "blocked: 1 changed file; risk blocked.",
          level: "warning",
        },
        {
          id: 4,
          label: "Approval preview",
          detail: "blocked: protected path.",
          level: "warning",
        },
      ],
      longRunningTask: {
        ...baseArgs().longRunningTask,
        response: {
          task: {
            current_agent_role: "debugger",
            description: "Target file: .env.local",
            id: "task-roles",
            progress: 60,
            status: "running",
            steps: [
              "Architect captured task scope and context.",
              "Coder prepares a focused diff.",
              "Debugger verifies the diff in the sandbox.",
            ],
            would_execute: false,
            writes_allowed: false,
          },
        },
      },
    });

    expect(transcript.map((section) => section.title)).toEqual([
      "Architect",
      "Coder",
      "Reviewer",
      "Debugger",
      "Verifier",
      "Approval Gate",
    ]);
    expect(transcript.find((section) => section.id === "architect")?.status).toBe("complete");
    expect(transcript.find((section) => section.id === "coder")?.items.join(" ")).toContain(
      "Architect -> Coder",
    );
    expect(transcript.find((section) => section.id === "debugger")?.items.join(" ")).toContain(
      "Debugger verifies the diff in the sandbox.",
    );
    expect(transcript.find((section) => section.id === "verifier")?.status).toBe("blocked");
    expect(transcript.find((section) => section.id === "approval")?.status).toBe("blocked");
    expect(transcript.find((section) => section.id === "approval")?.items.join(" ")).toContain(
      "No approved apply has run.",
    );
  });

  it("shows apply completion inside the approval gate action chain", () => {
    const transcript = deriveTaskTranscript({
      approvalGate: {
        ...baseArgs().approvalGate,
        execution: {
          ok: true,
          relativeFilePath: "docs/phase-8-manual-check.md",
        },
        target: "docs/phase-8-manual-check.md",
      },
      diffVerification: baseArgs().diffVerification,
      logs: [
        {
          id: 1,
          label: "Approval executed",
          detail: "Applied docs/phase-8-manual-check.md.",
          level: "success",
        },
      ],
      longRunningTask: baseArgs().longRunningTask,
    });

    const approval = transcript.find((section) => section.id === "approval");
    expect(approval?.status).toBe("complete");
    expect(approval?.items.join(" ")).toContain("Approval Gate applied");
  });

  it("does not mark approval complete before human approval or apply", () => {
    const transcript = deriveTaskTranscript({
      approvalGate: {
        ...baseArgs().approvalGate,
        action: "modify file",
        proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      diffVerification: baseArgs().diffVerification,
      logs: [],
      longRunningTask: baseArgs().longRunningTask,
    });

    const approval = transcript.find((section) => section.id === "approval");
    expect(approval?.status).toBe("waiting");
    expect(approval?.items).toEqual(["No approved apply has run."]);
  });
});

describe("workflowStep", () => {
  it("uses honest diff-ready copy when the backend provides an approvable diff", () => {
    expect(
      promptTextForCoderPacket({
        coderBlocked: false,
        coderBlockedReason: "",
        coderDiffReady: true,
        coderNeededContext: "",
        promptText:
          "Coder Agent produced replacement content that the backend converted into a unified diff for the approval gate (target: docs/phase-8-manual-check.md).",
      }),
    ).toBe(
      "Coder Agent produced replacement content; the backend generated the unified diff for the approval gate (see Proposal / Diff Preview).",
    );
  });

  it("does not surface backend success stub after the effective diff is unavailable", () => {
    expect(
      promptTextForCoderPacket({
        coderBlocked: false,
        coderBlockedReason: "",
        coderDiffReady: false,
        coderNeededContext: "",
        promptText:
          "Coder Agent produced replacement content that the backend converted into a unified diff for the approval gate (target: docs/phase-8-manual-check.md).",
      }),
    ).toContain("did not provide an approvable unified diff");
  });

  it("reports backend proposed_diff rejected by client validation as blocked copy", () => {
    expect(
      promptTextForCoderPacket({
        coderBlocked: false,
        coderBlockedReason: "",
        coderDiffReady: false,
        coderNeededContext: "",
        promptText:
          "Coder Agent returned backend-generated proposed_diff for approval-gate validation (target: docs/phase-8-manual-check.md). If the client rejects the diff, treat the proposal as blocked and retry Coder.",
      }),
    ).toBe(
      "Backend returned a proposed diff, but it did not pass client approval validation. No approval action is available.",
    );
  });

  it("keeps manual browser prompt copy available after a blocked Coder response", () => {
    expect(
      promptTextForCoderPacket({
        coderBlocked: true,
        coderBlockedReason: "Coder response was not valid replacement JSON.",
        coderDiffReady: false,
        coderNeededContext: "Retry Local Coder.",
        promptText:
          "# Manual Browser Prompt: SpiritOS Coder Recovery\n\nReturn output to the SpiritOS portal for validation.",
      }),
    ).toContain("Manual Browser Prompt");
  });

  it("uses resolved target when Architect plan target is missing", () => {
    expect(
      architectPlanDisplayTarget(
        {
          coder_packet: {
            target_file: {
              path: "",
            },
          },
        },
        "docs/phase-8-manual-check.md",
      ),
    ).toBe("docs/phase-8-manual-check.md");
  });

  it("derives the visible deterministic TaskSpec contract from an Architect plan", () => {
    expect(
      taskSpecForPlan({
        coder_packet: {
          constraints: {
            must_contain: ["Phase 3B UI clarity smoke test."],
          },
          operation: "edit",
          target_file: {
            exists: true,
            path: "docs/phase-8-manual-check.md",
          },
        },
        verification_plan: {
          required_checks: [{ id: "git_apply_check", command: ["git", "apply", "--check"] }],
        },
      }),
    ).toEqual({
      schema_version: 1,
      task_type: "modify_existing_file",
      target: "docs/phase-8-manual-check.md",
      allowed_files: ["docs/phase-8-manual-check.md"],
      forbidden_files: [],
      literal_requirements: ["Phase 3B UI clarity smoke test."],
      verification: ["git apply check", "literal present", "target-only"],
      risk_tier: "low",
      source: "deterministic",
    });
  });

  it("returns step 2 when route payload was invalid (summary prefix)", () => {
    const step = workflowStep(
      baseArgs({
        isRunning: true,
        finalOutput: {
          attachedFiles: [],
          completedAt: "t",
          contextTurnCount: 0,
          decision: {},
          decisionPayload: "{}",
          promptText: "",
          researchSources: [],
          requests: [],
          runId: 1,
          selfCorrection: {
            checks: [],
            confidence: 0,
            reasons: [],
            refinedInstruction: "",
            triggered: false,
          },
          summary: `${ROUTE_RESPONSE_INVALID_PREFIX}JSON Parse error: unexpected`,
        },
      }),
    );
    expect(step).toBe(2);
  });

  it("returns step 4 when approval preview exists (e.g. target_unresolved blocked)", () => {
    const step = workflowStep(
      baseArgs({
        finalOutput: {
          attachedFiles: [],
          completedAt: "t",
          contextTurnCount: 0,
          decision: { reason_codes: ["target_unresolved"] },
          decisionPayload: "{}",
          promptText: "",
          researchSources: [],
          requests: [],
          runId: 1,
          selfCorrection: {
            checks: [],
            confidence: 0,
            reasons: [],
            refinedInstruction: "",
            triggered: false,
          },
          summary: "Route ok",
        },
        approvalGate: {
          ...baseArgs().approvalGate,
          preview: {
            decision: "blocked",
            reason_codes: ["target_unresolved"],
          },
        },
      }),
    );
    expect(step).toBe(4);
  });

  it("returns step 3 when approval preview decision is needs_coder_diff (e.g. coder_packet_missing_context path)", () => {
    const step = workflowStep(
      baseArgs({
        approvalGate: {
          ...baseArgs().approvalGate,
          preview: {
            decision: "needs_coder_diff",
            reason_codes: ["coder_packet_missing_context"],
          },
        },
      }),
    );
    expect(step).toBe(3);
  });

  it("returns step 3 after Coder blocks before producing a diff", () => {
    const step = workflowStep(
      baseArgs({
        approvalGate: {
          ...baseArgs().approvalGate,
          action: "needs_coder_diff",
          preview: {
            decision: "blocked",
            reason_codes: ["coder_sync_timeout", "coder_proxy_deadline_blocked"],
            requires_human_approval: false,
          },
        },
        finalOutput: {
          attachedFiles: [],
          completedAt: "t",
          contextTurnCount: 0,
          decision: {},
          decisionPayload: "{}",
          promptText: "Coder timed out.",
          researchSources: [],
          requests: [],
          runId: 1,
          selfCorrection: {
            checks: [],
            confidence: 0,
            reasons: [],
            refinedInstruction: "",
            triggered: false,
          },
          summary: "Coder blocked before producing an approvable diff.",
        },
        longRunningTask: {
          ...baseArgs().longRunningTask,
          response: {
            task: {
              id: "task-1",
              description: "Target file: docs/phase-8-manual-check.md",
              status: "blocked",
              created_at: "t",
              updated_at: "t",
              cancelled_at: null,
              steps: ["Coder blocked before producing an approvable diff."],
              poll_count: 4,
              progress: 50,
              ast_snapshot: {},
              open_diffs: [],
              truncated_test_results: "reason_code=coder_sync_timeout",
              current_agent_role: "coder",
              role_transitions: [],
              cycle_count: 0,
              would_execute: false,
              writes_allowed: false,
              next_action: "Coder did not produce an approvable diff.",
            },
          },
        },
      }),
    );

    expect(step).toBe(3);
  });

  it("marks prompt-packet needs_coder_diff as terminal blocked instead of running", () => {
    const state = deriveTerminalLongTaskStateForApproval(
      {
        ...baseArgs().approvalGate,
        action: "needs_coder_diff",
        preview: {
          decision: "needs_coder_diff",
          reason_codes: ["needs_coder_diff"],
          requires_human_approval: false,
        },
        target: "docs/phase-8-manual-check.md",
      },
      {
        ...baseArgs().longRunningTask,
        isChecking: true,
        response: {
          task: {
            id: "task-1",
            description: "Target file: docs/phase-8-manual-check.md",
            status: "running",
            progress: 90,
            current_agent_role: "coder",
            open_diffs: [],
            steps: ["Coder prepares a focused diff."],
            would_execute: false,
            writes_allowed: false,
          },
        },
      },
    );

    expect(state.isChecking).toBe(false);
    expect(state.response?.task.status).toBe("blocked_no_valid_diff");
    expect(state.response?.task.progress).toBeLessThan(90);
    expect(state.response?.task.next_action).toBe(
      "Coder did not produce a valid approvable unified diff. Retry Local Coder with stricter output repair, or copy a manual browser prompt.",
    );
    expect(longTaskVisibleState(state.response?.task).label).toBe(
      "Blocked: blocked_no_valid_diff",
    );
  });

  it("marks client-rejected backend diffs as terminal blocked", () => {
    const state = deriveTerminalLongTaskStateForApproval(
      {
        ...baseArgs().approvalGate,
        action: "needs_coder_diff",
        preview: {
          decision: "blocked",
          reason_codes: ["needs_coder_diff", "client_rejected_proposed_diff"],
          requires_human_approval: false,
          safety_message:
            "Backend returned a proposed diff, but it did not pass client approval validation. No approval action is available.",
        },
        target: "docs/phase-8-manual-check.md",
      },
      {
        ...baseArgs().longRunningTask,
        response: {
          task: {
            id: "task-2",
            description: "Target file: docs/phase-8-manual-check.md",
            status: "running",
            progress: 90,
            current_agent_role: "coder",
            open_diffs: [],
            steps: [],
            would_execute: false,
            writes_allowed: false,
          },
        },
      },
    );

    expect(state.response?.task.status).toBe("coder_diff_rejected");
    expect(state.response?.task.progress).toBeLessThan(90);
    expect(state.response?.task.truncated_test_results).toBe("client_rejected_proposed_diff");
    expect(longTaskVisibleState(state.response?.task).label).toBe(
      "Blocked: coder_diff_rejected",
    );
  });

  it("keeps client-rejected backend diffs out of approval-ready workflow state", () => {
    const step = workflowStep(
      baseArgs({
        approvalGate: {
          ...baseArgs().approvalGate,
          action: "needs_coder_diff",
          preview: {
            decision: "blocked",
            reason_codes: ["needs_coder_diff", "client_rejected_proposed_diff"],
            requires_human_approval: false,
            safety_message:
              "Backend returned a proposed diff, but it did not pass client approval validation. No approval action is available.",
          },
          target: "docs/phase-8-manual-check.md",
        },
        longRunningTask: {
          ...baseArgs().longRunningTask,
          response: {
            task: {
              id: "task-3",
              description: "Target file: docs/phase-8-manual-check.md",
              status: "coder_diff_rejected",
              progress: 50,
              current_agent_role: "coder",
              open_diffs: [],
              steps: [],
              would_execute: false,
              writes_allowed: false,
            },
          },
        },
      }),
    );

    expect(step).toBe(3);
    expect(
      longTaskVisibleState({
        id: "task-3",
        description: "Target file: docs/phase-8-manual-check.md",
        status: "coder_diff_rejected",
      }).label,
    ).toBe("Blocked: coder_diff_rejected");

    expect(
      longTaskVisibleState({
        id: "task-4",
        description: "Target file: src/lib/coding/__tests__/unified-diff-paths.test.ts",
        status: "blocked_after_retries",
      }).label,
    ).toBe("Blocked: blocked_after_retries");
  });

  it("labels applied post-apply tasks without calling them running", () => {
    expect(
      longTaskVisibleState({
        description: "Docs task",
        id: "task-docs",
        post_apply_verification: {
          docs_only: true,
          required: true,
          status: "verification_ready",
        },
        status: "applied_needs_verification",
      }).label,
    ).toBe("Docs-only verification ready");

    expect(
      longTaskVisibleState({
        description: "Code task",
        id: "task-code",
        post_apply_verification: {
          docs_only: false,
          required: true,
          status: "verification_ready",
        },
        status: "applied_needs_verification",
      }).label,
    ).toBe("Applied, verification required");
  });

  it("hides obsolete task controls once docs-only verification is ready", () => {
    render(
      createElement(
        LongRunningTaskPanel,
        longTaskPanelProps({
          state: {
            description: "Docs task",
            error: null,
            isChecking: false,
            response: {
              task: {
                description: "Docs task",
                id: "task-docs",
                open_diffs: [
                  {
                    changed_files: [{ path: "docs/phase-8-manual-check.md" }],
                    diff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
                    risk: "low",
                    status: "applied_needs_verification",
                  },
                ],
                post_apply_verification: {
                  docs_only: true,
                  required: true,
                  status: "verification_ready",
                },
                progress: 92,
                status: "applied_needs_verification",
                would_execute: false,
                writes_allowed: false,
              },
            },
          },
        }),
      ),
    );

    expect(screen.getByText("Docs-only verification ready")).toBeTruthy();
    expect(screen.getByText("Task is already applied; verification is pending.")).toBeTruthy();
    expect(screen.getByText("Waiting for post-apply verification")).toBeTruthy();
    expect(screen.getByText("Internal progress: 92%")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Preview diff" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Retry from start" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Retry verification only" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "View latest evidence" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Start tracked task" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Check status" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Cancel" })).toBeNull();
  });

  it("shows recovery controls and latest evidence for active long tasks", () => {
    const onCancel = vi.fn();
    const onRejectPlan = vi.fn();
    const onRetry = vi.fn();
    render(
      createElement(
        LongRunningTaskPanel,
        longTaskPanelProps({
          onCancel,
          onRejectPlan,
          onRetry,
          state: {
            description: "Target file: docs/phase-8-manual-check.md",
            error: null,
            isChecking: false,
            response: {
              task: {
                current_agent_role: "coder",
                description: "Target file: docs/phase-8-manual-check.md",
                id: "task-controls",
                next_action: "Review the proposed diff before approval.",
                open_diffs: [
                  {
                    changed_files: [{ path: "docs/phase-8-manual-check.md" }],
                    diff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
                    risk: "low",
                    status: "pending_verification",
                  },
                ],
                progress: 64,
                status: "running",
                steps: ["Coder produced a diff preview."],
                truncated_test_results: "pytest: not run yet",
                would_execute: false,
                writes_allowed: false,
              },
            },
          },
        }),
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    fireEvent.click(screen.getByRole("button", { name: "Retry from start" }));
    fireEvent.click(screen.getByRole("button", { name: "Reject plan" }));
    fireEvent.click(screen.getByRole("button", { name: "View latest evidence" }));

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onRetry).toHaveBeenCalledTimes(1);
    expect(onRejectPlan).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("button", { name: "Start tracked task" })).toBeNull();
    expect(screen.getByText("Latest evidence")).toBeTruthy();
    expect(screen.getByText("Latest diff: pending_verification; risk low; 1 changed file.")).toBeTruthy();
    expect(screen.getByText("Test output: pytest: not run yet")).toBeTruthy();
  });

  it("derives compact latest evidence from verification details", () => {
    expect(
      latestLongTaskEvidenceLines({
        description: "Docs task",
        id: "task-evidence",
        post_apply_verification: {
          checks: [
            {
              command_text: "python -m pytest",
              status: "passed",
              summary: "7 passed",
            },
          ],
          docs_only: false,
          required: true,
          status: "verified",
        },
        progress: 100,
        status: "completed",
      }),
    ).toContain("Check python -m pytest: passed, 7 passed.");
  });

  it("hides approval controls after the approved diff has applied", () => {
    render(
      createElement(
        ApprovalGatePanel,
        approvalPanelProps({
          diffVerification: {
            error: null,
            isChecking: false,
            preview: {
              changed_files: [{ path: "docs/phase-8-manual-check.md" }],
              git_apply_check_ok: true,
              limits: { file_writes_allowed: true },
              status: "preview_ready",
            },
            unifiedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
          },
          gate: {
            ...baseArgs().approvalGate,
            action: "modify file",
            approvedAt: "2026-05-14T21:00:00.000Z",
            execution: {
              backup_root: ".spirit-backups/2026-05-14/approved-diff-smoke",
              ok: true,
              post_apply_verification: {
                docs_only: true,
                required: true,
                status: "verification_ready",
              },
              target: "docs/phase-8-manual-check.md",
            },
            preview: {
              decision: "requires_human_approval",
              reason_codes: [],
              requires_human_approval: true,
            },
            proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
            target: "docs/phase-8-manual-check.md",
          },
          task: {
            description: "Docs task",
            id: "task-docs",
            post_apply_verification: {
              docs_only: true,
              required: true,
              status: "verification_ready",
            },
            status: "applied_needs_verification",
          },
        }),
      ),
    );

    expect(
      screen.getByText("This diff has already been approved and applied. Complete verification below."),
    ).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Check action" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Approve" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Reject" })).toBeNull();
  });

  it("renders applied docs-only verification as the primary next action", () => {
    const onDocsOnlyVerify = vi.fn();
    render(
      createElement(VerificationSummary, {
        diffVerification: { error: null, isChecking: false, preview: null, unifiedDiff: "" },
        execution: { ok: true },
        isVerifying: false,
        longRunningTask: {
          description: "",
          error: null,
          isChecking: false,
          response: {
            task: {
              description: "Docs task",
              id: "task-docs",
              post_apply_verification: {
                changed_files: [{ path: "docs/phase-8-manual-check.md" }],
                docs_only: true,
                docs_only_confirmations: {
                  backup_audit_present: false,
                  file_changed_as_expected: false,
                  no_unintended_files: false,
                },
                required: true,
                status: "verification_ready",
              },
              progress: 92,
              status: "applied_needs_verification",
              truncated_test_results: JSON.stringify({
                backup_root: ".spirit-backups/2026-05-14/approved-diff-smoke",
              }),
            },
          },
        },
        onDocsOnlyVerify,
      }),
    );

    expect(screen.getByText("Applied, verification required")).toBeTruthy();
    expect(screen.getByText("Next step: complete docs-only verification")).toBeTruthy();
    expect(screen.getByText("Complete docs-only verification")).toBeTruthy();
    expect(screen.getByText("docs/phase-8-manual-check.md")).toBeTruthy();
    expect(
      screen.getByText(".spirit-backups/2026-05-14/approved-diff-smoke"),
    ).toBeTruthy();
    expect(screen.getByText(/\[ \] Confirm file changed as expected/)).toBeTruthy();
    const advancedDetails = screen
      .getByText("Advanced verification details")
      .closest("details");
    expect(advancedDetails?.hasAttribute("open")).toBe(false);
    expect(advancedDetails?.textContent).toContain('"status": "verification_ready"');
    fireEvent.click(screen.getByText("Mark verification complete"));
    expect(onDocsOnlyVerify).toHaveBeenCalledTimes(1);
  });

  it("shows Step 7 as waiting for verification while Step 6 is unfinished", () => {
    render(
      createElement(TaskCompletionStatus, {
        alreadySatisfied: false,
        execution: { ok: true },
        task: {
          description: "Docs task",
          id: "task-docs",
          post_apply_verification: {
            docs_only: true,
            required: true,
            status: "verification_ready",
          },
          status: "applied_needs_verification",
        },
      }),
    );

    expect(screen.getByText("Waiting for verification")).toBeTruthy();
    expect(screen.getByText("Complete the checklist in Step 6 to finish.")).toBeTruthy();
  });

  it("shows verified state after docs-only completion", () => {
    const summary = stabilitySummary({
      longRunningTask: {
        ...baseArgs().longRunningTask,
        response: {
          task: {
            description: "Docs task",
            id: "task-docs",
            post_apply_verification: {
              docs_only: true,
              required: true,
              status: "verified",
            },
            status: "completed",
          },
        },
      },
    });
    const step = workflowStep(
      baseArgs({
        longRunningTask: {
          ...baseArgs().longRunningTask,
          response: {
            task: {
              description: "Docs task",
              id: "task-docs",
              post_apply_verification: {
                docs_only: true,
                required: true,
                status: "verified",
              },
              status: "completed",
            },
          },
        },
      }),
    );

    expect(step).toBe(7);
    expect(
      longTaskVisibleState({
        description: "Docs task",
        id: "task-docs",
        post_apply_verification: {
          docs_only: true,
          required: true,
          status: "verified",
        },
        status: "completed",
      }).label,
    ).toBe("Verification complete");

    render(createElement(CodingStabilityCard, { summary }));
    expect(screen.getByText("Done")).toBeTruthy();
    cleanup();

    render(
      createElement(
        LongRunningTaskPanel,
        longTaskPanelProps({
          state: {
            description: "Docs task",
            error: null,
            isChecking: false,
            response: {
              task: {
                description: "Docs task",
                id: "task-docs",
                post_apply_verification: {
                  docs_only: true,
                  required: true,
                  status: "verified",
                },
                progress: 100,
                status: "completed",
                would_execute: false,
                writes_allowed: false,
              },
            },
          },
        }),
      ),
    );
    expect(screen.getAllByText("Verification complete").length).toBeGreaterThan(0);
    expect(screen.getByText("Progress: 100%")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Start tracked task" })).toBeNull();
    cleanup();

    render(
      createElement(TaskCompletionStatus, {
        alreadySatisfied: false,
        execution: null,
        task: {
          description: "Docs task",
          id: "task-docs",
          post_apply_verification: {
            docs_only: true,
            required: true,
            status: "verified",
          },
          status: "completed",
        },
      }),
    );
    expect(screen.getByText("Task Complete")).toBeTruthy();
    expect(screen.getByText("Docs verified")).toBeTruthy();
  });

  it("does not show mark complete without post-apply verification state", () => {
    render(
      createElement(VerificationSummary, {
        diffVerification: { error: null, isChecking: false, preview: null, unifiedDiff: "" },
        execution: { ok: true },
        isVerifying: false,
        longRunningTask: {
          description: "",
          error: null,
          isChecking: false,
          response: {
            task: {
              description: "Docs task",
              id: "task-docs",
              status: "applied_needs_verification",
            },
          },
        },
        onDocsOnlyVerify: vi.fn(),
      }),
    );

    expect(screen.queryByText("Mark verification complete")).toBeNull();
  });

  it("keeps pre-approval controls and verification plan visible before apply", () => {
    render(
      createElement(
        ApprovalGatePanel,
        approvalPanelProps({
          diffVerification: {
            error: null,
            isChecking: false,
            preview: {
              changed_files: [{ path: "docs/phase-8-manual-check.md" }],
              git_apply_check_ok: true,
              limits: { file_writes_allowed: true },
              status: "preview_ready",
            },
            unifiedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
          },
          gate: {
            ...baseArgs().approvalGate,
            action: "modify file",
            preview: {
              decision: "requires_human_approval",
              reason_codes: [],
              requires_human_approval: true,
            },
            proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
            target: "docs/phase-8-manual-check.md",
          },
        }),
      ),
    );

    expect(screen.getByRole("button", { name: "Check action" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Approve" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Reject" })).toBeTruthy();
    expect(screen.getByText("3. Reviewer Agent")).toBeTruthy();
    expect(screen.getByText("Target correctness")).toBeTruthy();
    expect(screen.getByText("Diff validity")).toBeTruthy();
    expect(screen.getByText("Requirement coverage")).toBeTruthy();
    expect(screen.getByText("Safety reasons")).toBeTruthy();
    expect(screen.getByText("Test coverage")).toBeTruthy();
    expect(screen.getByText("Likely regression risk")).toBeTruthy();
    expect(screen.getByText("Approval State")).toBeTruthy();
    expect(screen.getByText("Test passed")).toBeTruthy();
    expect(screen.getByText("Verification passed")).toBeTruthy();
    expect(screen.getByText("Approval available")).toBeTruthy();
    expect(screen.getByText("Human approved")).toBeTruthy();
    expect(screen.getByText("Apply completed")).toBeTruthy();
    expect(screen.getByText("Post-apply verification passed")).toBeTruthy();
    cleanup();

    render(
      createElement(VerificationSummary, {
        diffVerification: {
          error: null,
          isChecking: false,
          preview: {
            status: "preview_ready",
            verification_plan: [
              "Review changed files and risk flags.",
              "Apply the diff only after approval.",
            ],
          },
          unifiedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        },
        execution: null,
        isVerifying: false,
        longRunningTask: baseArgs().longRunningTask,
        onDocsOnlyVerify: vi.fn(),
      }),
    );

    expect(screen.getByText("Apply the diff only after approval.")).toBeTruthy();
    expect(screen.queryByText("Complete docs-only verification")).toBeNull();
  });

  it("separates approval state from apply and post-apply verification state", () => {
    const items = deriveApprovalStateChecklist({
      canApprove: true,
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          changed_files: [{ path: "docs/phase-8-manual-check.md" }],
          git_apply_check_ok: true,
          risk: "low",
          status: "preview_ready",
          task_spec_check: {
            allowed_files: ["docs/phase-8-manual-check.md"],
            changed_files: ["docs/phase-8-manual-check.md"],
            ok: true,
            reason_codes: [],
          },
        },
        unifiedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
      },
      gate: {
        ...baseArgs().approvalGate,
        action: "modify file",
        preview: {
          decision: "requires_human_approval",
          reason_codes: [],
          requires_human_approval: true,
        },
        proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      resolvedTargetPath: "docs/phase-8-manual-check.md",
      task: null,
    });

    expect(items.find((item) => item.label === "Test passed")?.status).toBe("pass");
    expect(items.find((item) => item.label === "Verification passed")?.status).toBe("pass");
    expect(items.find((item) => item.label === "Approval available")?.status).toBe("pass");
    expect(items.find((item) => item.label === "Human approved")?.status).toBe("waiting");
    expect(items.find((item) => item.label === "Apply completed")?.status).toBe("waiting");
    expect(items.find((item) => item.label === "Post-apply verification passed")?.status).toBe("waiting");
  });

  it("uses readable rejection reasons and preserves reason codes", () => {
    const onDeny = vi.fn();
    render(
      createElement(
        ApprovalGatePanel,
        approvalPanelProps({
          diffVerification: {
            error: null,
            isChecking: false,
            preview: {
              changed_files: [{ path: "docs/phase-8-manual-check.md" }],
              git_apply_check_ok: true,
              limits: { file_writes_allowed: true },
              status: "preview_ready",
            },
            unifiedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
          },
          gate: {
            ...baseArgs().approvalGate,
            action: "modify file",
            preview: {
              decision: "requires_human_approval",
              reason_codes: [],
              requires_human_approval: true,
            },
            proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
            target: "docs/phase-8-manual-check.md",
          },
          onDeny,
        }),
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "Reject" }));

    expect(screen.getByText("Wrong target")).toBeTruthy();
    expect(
      screen.getByText("The proposed target or changed files do not match the task."),
    ).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", {
        name: /Wrong target The proposed target or changed files do not match the task\./,
      }),
    );

    expect(onDeny).toHaveBeenCalledWith("wrong_target");
  });

  it("keeps blocked no-diff states clear without docs verification checklist", () => {
    render(
      createElement(
        ApprovalGatePanel,
        approvalPanelProps({
          gate: {
            ...baseArgs().approvalGate,
            action: "needs_coder_diff",
            preview: {
              decision: "needs_coder_diff",
              reason_codes: ["needs_coder_diff"],
              requires_human_approval: false,
            },
            target: "docs/phase-8-manual-check.md",
          },
        }),
      ),
    );

    expect(screen.getByText("No approval action is available yet")).toBeTruthy();
    expect(screen.getByText(/Coder did not produce a valid approvable unified diff/)).toBeTruthy();
    expect(screen.queryByText("Complete docs-only verification")).toBeNull();
    cleanup();

    render(
      createElement(VerificationSummary, {
        diffVerification: { error: null, isChecking: false, preview: null, unifiedDiff: "" },
        execution: null,
        isVerifying: false,
        longRunningTask: {
          ...baseArgs().longRunningTask,
          response: {
            task: {
              description: "Docs task",
              id: "task-docs",
              status: "needs_coder_diff",
            },
          },
        },
        onDocsOnlyVerify: vi.fn(),
      }),
    );

    expect(screen.queryByText("Complete docs-only verification")).toBeNull();
    expect(screen.queryByText("Mark verification complete")).toBeNull();
  });

  it("shows protected-path approval blockers honestly", () => {
    render(
      createElement(
        ApprovalGatePanel,
        approvalPanelProps({
          gate: {
            ...baseArgs().approvalGate,
            action: "needs_coder_diff",
            preview: {
              decision: "blocked",
              reason_codes: ["protected_path"],
              requires_human_approval: false,
            },
            target: ".env.local",
          },
        }),
      ),
    );

    expect(screen.getByText("Blocked: protected/secret path")).toBeTruthy();
    expect(
      screen.getByText(
        "Protected and secret-shaped paths cannot be edited through the approval flow.",
      ),
    ).toBeTruthy();
    expect(screen.queryByText(/Coder did not produce a valid approvable unified diff/)).toBeNull();
  });

  it("shows path traversal approval blockers honestly", () => {
    render(
      createElement(
        ApprovalGatePanel,
        approvalPanelProps({
          gate: {
            ...baseArgs().approvalGate,
            action: "needs_coder_diff",
            preview: {
              decision: "blocked",
              reason_codes: ["path_escape"],
              requires_human_approval: false,
            },
            target: "../outside.txt",
          },
        }),
      ),
    );

    expect(screen.getByText("Blocked: path escapes workspace")).toBeTruthy();
    expect(
      screen.getByText(
        "Use a repo-relative path inside the workspace. Traversal, absolute, and drive paths are blocked.",
      ),
    ).toBeTruthy();
  });

  it("shows target-unresolved approval blockers with a concrete next step", () => {
    render(
      createElement(
        ApprovalGatePanel,
        approvalPanelProps({
          gate: {
            ...baseArgs().approvalGate,
            action: "needs_coder_diff",
            preview: {
              decision: "blocked",
              reason_codes: ["target_unresolved"],
              requires_human_approval: false,
            },
          },
        }),
      ),
    );

    expect(screen.getByText("No safe file target was resolved.")).toBeTruthy();
    expect(screen.getByText("Add a Target file: line.")).toBeTruthy();
  });

  it("shows the code verification action for code-edit post-apply verification", () => {
    const onCodeVerify = vi.fn();
    render(
      createElement(VerificationSummary, {
        diffVerification: { error: null, isChecking: false, preview: null, unifiedDiff: "" },
        execution: { ok: true },
        isVerifying: false,
        longRunningTask: {
          description: "",
          error: null,
          isChecking: false,
          response: {
            task: {
              description: "Code task",
              id: "task-code",
              post_apply_verification: {
                docs_only: false,
                changed_files: [{ path: "src/lib/coding/example.test.ts" }],
                checks: [
                  {
                    command: ["npm", "run", "test:coding-frontend-regression"],
                    id: "coding_frontend_regression",
                    required: true,
                    status: "pending",
                  },
                  {
                    command: ["npx", "tsc", "--noEmit", "-p", "tsconfig.json"],
                    id: "typescript_typecheck",
                    required: true,
                    status: "pending",
                  },
                ],
                required: true,
                status: "verification_ready",
              },
              status: "applied_needs_verification",
            },
          },
        },
        onCodeVerify,
        onDocsOnlyVerify: vi.fn(),
      }),
    );

    expect(screen.getByText("Code verification required")).toBeTruthy();
    expect(screen.getByText("src/lib/coding/example.test.ts")).toBeTruthy();
    expect(screen.getByText("npm run test:coding-frontend-regression")).toBeTruthy();
    expect(screen.getByText("npx tsc --noEmit -p tsconfig.json")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Run code verification" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Run code verification" }));
    expect(onCodeVerify).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("Complete docs-only verification")).toBeNull();
    expect(screen.queryByText("Mark verification complete")).toBeNull();
  });

  it("shows running status while code verification is in flight", () => {
    render(
      createElement(VerificationSummary, {
        diffVerification: { error: null, isChecking: false, preview: null, unifiedDiff: "" },
        execution: { ok: true },
        isVerifying: true,
        longRunningTask: {
          description: "",
          error: null,
          isChecking: true,
          response: {
            task: {
              description: "Code task",
              id: "task-code",
              post_apply_verification: {
                docs_only: false,
                checks: [
                  {
                    command: ["npx", "tsc", "--noEmit", "-p", "tsconfig.json"],
                    id: "typescript_typecheck",
                    required: true,
                    status: "pending",
                  },
                ],
                required: true,
                status: "verification_ready",
              },
              status: "applied_needs_verification",
            },
          },
        },
        onCodeVerify: vi.fn(),
        onDocsOnlyVerify: vi.fn(),
      }),
    );

    expect(screen.getByText(/running \| required/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Running verification..." })).toBeTruthy();
  });

  it("shows code verification complete and Task Complete after passing checks", () => {
    const task = {
      description: "Code task",
      id: "task-code",
      post_apply_verification: {
        docs_only: false,
        checks: [
          {
            command_text: "npx tsc --noEmit -p tsconfig.json",
            exit_code: 0,
            id: "typescript_typecheck",
            required: true,
            status: "passed",
          },
        ],
        required: true,
        status: "verified",
      },
      status: "completed",
    };

    render(
      createElement(VerificationSummary, {
        diffVerification: { error: null, isChecking: false, preview: null, unifiedDiff: "" },
        execution: { ok: true },
        isVerifying: false,
        longRunningTask: {
          description: "",
          error: null,
          isChecking: false,
          response: { task },
        },
        onCodeVerify: vi.fn(),
        onDocsOnlyVerify: vi.fn(),
      }),
    );
    expect(screen.getByText("Code verification complete")).toBeTruthy();
    expect(screen.getByText(/passed \| required/)).toBeTruthy();
    cleanup();

    render(createElement(TaskCompletionStatus, {
      alreadySatisfied: false,
      execution: null,
      task,
    }));
    expect(screen.getByText("Task Complete")).toBeTruthy();
    expect(longTaskVisibleState(task).label).toBe("Verification complete");
  });

  it("shows failed code verification command and output tail", () => {
    const task = {
      description: "Code task",
      id: "task-code",
      post_apply_verification: {
        docs_only: false,
        checks: [
          {
            command_text: "npx tsc --noEmit -p tsconfig.json",
            exit_code: 1,
            id: "typescript_typecheck",
            output_tail: "TypeScript failed near the end",
            required: true,
            status: "failed",
            summary: "TypeScript or JavaScript files changed.",
          },
        ],
        required: true,
        status: "verification_failed",
      },
      status: "verification_failed",
    };

    render(
      createElement(VerificationSummary, {
        diffVerification: { error: null, isChecking: false, preview: null, unifiedDiff: "" },
        execution: { ok: true },
        isVerifying: false,
        longRunningTask: {
          description: "",
          error: null,
          isChecking: false,
          response: { task },
        },
        onCodeVerify: vi.fn(),
        onDocsOnlyVerify: vi.fn(),
      }),
    );

    expect(screen.getByText("Verification failed")).toBeTruthy();
    expect(screen.getAllByText("npx tsc --noEmit -p tsconfig.json").length).toBeGreaterThan(0);
    expect(screen.getByText("TypeScript failed near the end")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Run code verification" })).toBeNull();
    expect(longTaskVisibleState(task).label).toBe("Verification failed");
  });

  it("shows unsupported code verification as manual verification required", () => {
    render(
      createElement(VerificationSummary, {
        diffVerification: { error: null, isChecking: false, preview: null, unifiedDiff: "" },
        execution: { ok: true },
        isVerifying: false,
        longRunningTask: {
          description: "",
          error: null,
          isChecking: false,
          response: {
            task: {
              description: "Python task",
              id: "task-python",
              post_apply_verification: {
                changed_files: [{ path: "source_proxy/demo.py" }],
                docs_only: false,
                required: true,
                status: "manual_verification_required",
                unsupported_code_verification: true,
                unsupported_file_types: [".py"],
              },
              status: "applied_needs_verification",
            },
          },
        },
        onCodeVerify: vi.fn(),
        onDocsOnlyVerify: vi.fn(),
      }),
    );

    expect(
      screen.getByText("Manual verification required / unsupported code verification type"),
    ).toBeTruthy();
    expect(screen.getByText("Unsupported types: .py")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Run code verification" })).toBeNull();
    expect(screen.queryByText("Complete docs-only verification")).toBeNull();
  });

  it("dedupes SSE connection and stream fallback activity once per task", () => {
    const logged = new Set<string>();

    expect(shouldAppendTaskActivityLog(logged, "task-1", "sse_connected")).toBe(true);
    expect(shouldAppendTaskActivityLog(logged, "task-1", "sse_connected")).toBe(false);
    expect(shouldAppendTaskActivityLog(logged, "task-1", "stream_fallback")).toBe(true);
    expect(shouldAppendTaskActivityLog(logged, "task-1", "stream_fallback")).toBe(false);
    expect(shouldAppendTaskActivityLog(logged, "task-2", "sse_connected")).toBe(true);
  });
});

describe("coding diff quality gates", () => {
  it("derives reviewer agent checks before approval", () => {
    const checks = deriveReviewerAgentChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          changed_files: [
            {
              added_lines: 12,
              path: "docs/phase-8-manual-check.md",
              removed_lines: 1,
            },
          ],
          git_apply_check_ok: true,
          requirement_coverage: { ok: true, missing: [] },
          risk: "low",
          status: "preview_ready",
          task_spec_check: {
            allowed_files: ["docs/phase-8-manual-check.md"],
            changed_files: ["docs/phase-8-manual-check.md"],
            ok: true,
            reason_codes: [],
          },
          typescript_check: {
            ok: true,
            skipped: true,
            summary: "No TS/TSX files changed.",
          },
          verification_plan: ["Review changed files and risk flags."],
        },
        unifiedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
      },
      gate: {
        ...baseArgs().approvalGate,
        action: "modify file",
        proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      resolvedTargetPath: "docs/phase-8-manual-check.md",
    });

    expect(checks.map((check) => check.label)).toEqual([
      "Target correctness",
      "Diff validity",
      "Requirement coverage",
      "Safety reasons",
      "Test coverage",
      "Likely regression risk",
    ]);
    expect(checks.find((check) => check.label === "Safety reasons")?.status).toBe("pass");
    expect(checks.find((check) => check.label === "Likely regression risk")?.detail).toContain(
      "changed lines 13",
    );
  });

  it("lets reviewer agent block unsafe diffs", () => {
    const checks = deriveReviewerAgentChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          changed_files: [{ path: "source_proxy/api/decision.py" }],
          git_apply_check_ok: true,
          risk: "blocked",
          status: "blocked",
          task_spec_check: {
            allowed_files: ["docs/phase-8-manual-check.md"],
            changed_files: ["source_proxy/api/decision.py"],
            ok: false,
            reason_codes: ["task_spec_allowed_file_violation"],
          },
        },
        unifiedDiff: SOURCE_PROXY_DECISION_DIFF,
      },
      gate: {
        ...baseArgs().approvalGate,
        action: "modify file",
        proposedDiff: SOURCE_PROXY_DECISION_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      resolvedTargetPath: "docs/phase-8-manual-check.md",
    });

    expect(checks.find((check) => check.label === "Target correctness")?.status).toBe("fail");
    expect(checks.find((check) => check.label === "Safety reasons")?.status).toBe("fail");
    expect(checks.find((check) => check.label === "Likely regression risk")?.status).toBe("fail");
  });

  it("passes preview gates for the exact backend-style standard unified diff fixture", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          status: "preview_ready",
          git_apply_check_ok: true,
          changed_files: [{ path: "docs/phase-8-manual-check.md" }],
          task_spec_check: {
            ok: true,
            allowed_files: ["docs/phase-8-manual-check.md"],
            changed_files: ["docs/phase-8-manual-check.md"],
            reason_codes: [],
          },
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
        ...baseArgs().approvalGate,
        action: "modify file",
        proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      resolvedTargetPath: "docs/phase-8-manual-check.md",
    });

    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Target Match",
        status: "pass",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "TaskSpec Allowed Files",
        status: "pass",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "Git Apply Check",
        status: "pass",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        label: "TypeScript Syntax",
        required: false,
        status: "info",
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
        label: "Fallback Status",
        detail: "No client fallback scaffold is being used.",
        status: "pass",
      }),
    );
    expect(checks.filter((check) => check.required).every((check) => check.status === "pass")).toBe(
      true,
    );
  });

  it("can reach approval preview state when the backend diff passes required checks", () => {
    const step = workflowStep(
      baseArgs({
        approvalGate: {
          ...baseArgs().approvalGate,
          action: "modify file",
          preview: {
            decision: "requires_human_approval",
            reason_codes: [],
            requires_human_approval: true,
          },
          proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
          target: "docs/phase-8-manual-check.md",
        },
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
      }),
    );

    expect(step).toBe(4);
  });

  it("fails target matching when a standard unified diff is stale for the current target", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          status: "preview_ready",
          git_apply_check_ok: true,
          changed_files: [{ path: "docs/phase-8-manual-check.md" }],
        },
        unifiedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
      },
      gate: {
        ...baseArgs().approvalGate,
        action: "modify file",
        proposedDiff: DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        target: "src/components/coding/CodingAgentInterface.tsx",
      },
      resolvedTargetPath: "src/components/coding/CodingAgentInterface.tsx",
    });

    expect(checks).toContainEqual(
      expect.objectContaining({
        detail: "Diff does not touch src/components/coding/CodingAgentInterface.tsx.",
        label: "Target Match",
        required: true,
        status: "fail",
      }),
    );
  });

  it("blocks approval readiness when a backend diff touches source_proxy instead of the target", () => {
    const checks = buildQualityGateChecks({
      diffVerification: {
        error: null,
        isChecking: false,
        preview: {
          status: "preview_ready",
          git_apply_check_ok: true,
          changed_files: [{ path: "source_proxy/api/decision.py" }],
          task_spec_check: {
            ok: false,
            allowed_files: ["docs/phase-8-manual-check.md"],
            changed_files: ["source_proxy/api/decision.py"],
            reason_codes: ["task_spec_allowed_file_violation"],
            summary: "task_spec_allowed_file_violation",
          },
        },
        unifiedDiff: SOURCE_PROXY_DECISION_DIFF,
      },
      gate: {
        ...baseArgs().approvalGate,
        action: "modify file",
        proposedDiff: SOURCE_PROXY_DECISION_DIFF,
        target: "docs/phase-8-manual-check.md",
      },
      resolvedTargetPath: "docs/phase-8-manual-check.md",
    });

    expect(checks).toContainEqual(
      expect.objectContaining({
        detail: "TaskSpec blocked this diff because it touches files outside the allowed list.",
        label: "TaskSpec Allowed Files",
        required: true,
        status: "fail",
      }),
    );
    expect(checks).toContainEqual(
      expect.objectContaining({
        detail: "Diff does not touch docs/phase-8-manual-check.md.",
        label: "Target Match",
        required: true,
        status: "fail",
      }),
    );
    expect(checks.some((check) => check.required && check.status !== "pass")).toBe(true);
  });

  it("builds manual preview TaskSpec from the current Target file line without an architect plan", () => {
    const taskSpec = taskSpecForManualPreview(
      null,
      null,
      [
        "Target file: docs/phase-8-manual-check.md",
        "",
        "Use the manual diff preview to validate wrong-file blocking. Do not edit any other file.",
      ].join("\n"),
    );

    expect(taskSpec).toMatchObject({
      target: "docs/phase-8-manual-check.md",
      allowed_files: ["docs/phase-8-manual-check.md"],
      source: "manual_preview_target",
    });
  });
});
