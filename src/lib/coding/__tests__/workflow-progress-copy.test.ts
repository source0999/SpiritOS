import { describe, expect, it } from "vitest";

import {
  deriveWorkflowProgressCopy,
  formatWorkflowBlockerTitle,
  isApprovalPendingGateReason,
} from "@/lib/coding/workflow-progress-copy";

type WorkflowProgressInput = Parameters<typeof deriveWorkflowProgressCopy>[0];
type WorkflowProgressOverrides = {
  approvalGate?: Partial<WorkflowProgressInput["approvalGate"]>;
  diffVerification?: Partial<WorkflowProgressInput["diffVerification"]>;
  longRunningTask?: Partial<WorkflowProgressInput["longRunningTask"]>;
  stability?: Partial<WorkflowProgressInput["stability"]>;
};

function baseInput(overrides: WorkflowProgressOverrides = {}) {
  return {
    approvalGate: {
      approvedAt: null,
      execution: null,
      isChecking: false,
      preview: null,
      ...overrides.approvalGate,
    },
    diffVerification: {
      preview: null,
      ...overrides.diffVerification,
    },
    longRunningTask: {
      isChecking: false,
      response: null,
      ...overrides.longRunningTask,
    },
    stability: {
      approvalState: "requires human approval",
      diffState: "preview ready",
      lastBlocker: null,
      primaryState: "Needs approval",
      ...overrides.stability,
    },
  };
}

describe("workflow blocker display", () => {
  it("maps implementation_or_terminal_action to approval gate copy when preview is ready", () => {
    const context = {
      primaryState: "Needs approval",
      stepLabel: "Preview ready, waiting for approval",
    };
    expect(
      isApprovalPendingGateReason("implementation_or_terminal_action", context),
    ).toBe(true);
    expect(
      formatWorkflowBlockerTitle("implementation_or_terminal_action", context),
    ).toBe("Awaiting human approval to apply");
  });

  it("keeps real blockers as last blocker titles", () => {
    expect(
      formatWorkflowBlockerTitle("protected_path", {
        primaryState: "Blocked",
        stepLabel: "Blocked: protected_path",
      }),
    ).toBe("protected_path");
  });
});

describe("deriveWorkflowProgressCopy", () => {
  it("preview ready but not approved shows human approval required copy", () => {
    const copy = deriveWorkflowProgressCopy(
      baseInput({
        approvalGate: {
          preview: {
            decision: "requires_human_approval",
            requires_human_approval: true,
          },
        },
        diffVerification: {
          preview: {
            status: "preview_ready",
            git_apply_check_ok: true,
          },
        },
      }),
    );

    expect(copy.stepLabel).toBe("Preview ready, waiting for approval");
    expect(copy.headline).toBe(
      "Preview ready. Human approval required before apply.",
    );
    expect(copy.nextAction).toContain("No files have changed yet");
    expect(copy.applyExecuted).toBe("no");
    expect(copy.applyExecutedHelper).toContain("Preview only");
  });

  it("approval available with applied_anything false says no files changed yet", () => {
    const copy = deriveWorkflowProgressCopy(
      baseInput({
        approvalGate: {
          preview: {
            decision: "requires_human_approval",
            requires_human_approval: true,
          },
        },
        diffVerification: {
          preview: { status: "preview_ready", git_apply_check_ok: true },
        },
      }),
    );

    expect(copy.applyExecuted).toBe("no");
    expect(copy.nextAction).toMatch(/Approve/i);
    expect(copy.nextAction).toMatch(/No files have changed yet/i);
  });

  it("human approved but not applied explains approval alone does not change files", () => {
    const copy = deriveWorkflowProgressCopy(
      baseInput({
        approvalGate: {
          approvedAt: "2026-05-19T00:00:00.000Z",
          execution: { ok: false },
        },
        stability: {
          approvalState: "approved",
          diffState: "preview ready",
          lastBlocker: null,
          primaryState: "Applying",
        },
      }),
    );

    expect(copy.stepLabel).toBe("Human approved, waiting to apply");
    expect(copy.nextAction).toContain("Apply approved diff");
    expect(copy.nextAction).toContain("Approval alone does not change files");
    expect(copy.applyExecuted).toBe("no");
  });

  it("applied needing verification shows verification required", () => {
    const copy = deriveWorkflowProgressCopy(
      baseInput({
        approvalGate: {
          execution: { ok: true },
        },
        longRunningTask: {
          response: {
            task: {
              status: "applied_needs_verification",
              post_apply_verification: {
                required: true,
                status: "verification_ready",
              },
            },
          },
        },
        stability: {
          approvalState: "approved",
          diffState: "preview ready",
          lastBlocker: null,
          primaryState: "Applied, verification required",
        },
      }),
    );

    expect(copy.stepLabel).toBe("Applied, verification required");
    expect(copy.nextAction).toContain("post-apply verification");
    expect(copy.applyExecuted).toBe("yes");
  });
});
