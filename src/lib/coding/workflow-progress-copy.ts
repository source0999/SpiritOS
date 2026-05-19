// ── Workflow progress copy ───────────────────────────────────────────────────
// UI-only labels for /proxy-backend: preview vs approve vs apply vs verify.

export type WorkflowChecklistStatus = "pass" | "waiting" | "blocked";

export type WorkflowApplyChecklistItem = {
  detail?: string;
  id: "diff_preview" | "human_approval" | "apply_executed" | "post_apply_verification";
  label: string;
  status: WorkflowChecklistStatus;
};

export type WorkflowProgressCopy = {
  applyExecuted: "yes" | "no";
  applyExecutedHelper: string;
  checklist: WorkflowApplyChecklistItem[];
  headline: string;
  nextAction: string | null;
  stepLabel: string;
};

/** Backend reason codes that mean “human must approve,” not “preview failed.” */
export const APPROVAL_PENDING_REASON_CODES = new Set([
  "client_command_shape_detected",
  "implementation_or_terminal_action",
  "paid_api_route_possible",
]);

export type WorkflowBlockerDisplayContext = {
  primaryState: string;
  stepLabel: string;
};

export function isApprovalPendingGateReason(
  reasonCode: string | null | undefined,
  context: WorkflowBlockerDisplayContext,
): boolean {
  if (!reasonCode || reasonCode === "none") {
    return false;
  }
  return (
    APPROVAL_PENDING_REASON_CODES.has(reasonCode) &&
    (context.primaryState === "Needs approval" ||
      context.stepLabel.startsWith("Preview ready"))
  );
}

export function formatWorkflowBlockerTitle(
  reasonCode: string,
  context: WorkflowBlockerDisplayContext,
): string {
  if (isApprovalPendingGateReason(reasonCode, context)) {
    return "Awaiting human approval to apply";
  }
  return reasonCode;
}

export type WorkflowProgressInput = {
  approvalGate: {
    approvedAt: string | null;
    isChecking: boolean;
    preview: {
      decision?: string;
      requires_human_approval?: boolean;
    } | null;
    execution: {
      ok?: boolean;
      post_apply_verification?: {
        status?: string;
        required?: boolean;
      } | null;
    } | null;
  };
  diffVerification: {
    preview: {
      status?: string;
      git_apply_check_ok?: boolean;
      blocked_reasons?: Array<{ reason_code?: string }>;
    } | null;
  };
  longRunningTask: {
    isChecking: boolean;
    response: {
      task?: {
        status?: string;
        post_apply_verification?: {
          status?: string;
          required?: boolean;
        } | null;
      };
    } | null;
  };
  stability: {
    approvalState: string;
    diffState: string;
    lastBlocker: string | null;
    primaryState: string;
  };
};

function previewReady(input: WorkflowProgressInput): boolean {
  const preview = input.diffVerification.preview;
  return (
    preview?.status === "preview_ready" ||
    preview?.git_apply_check_ok === true
  );
}

function previewBlocked(input: WorkflowProgressInput): boolean {
  return input.diffVerification.preview?.status === "blocked";
}

function applyExecuted(input: WorkflowProgressInput): boolean {
  const taskStatus = input.longRunningTask.response?.task?.status ?? "";
  return Boolean(
    input.approvalGate.execution?.ok === true ||
      taskStatus === "applied_needs_verification" ||
      taskStatus === "completed" ||
      taskStatus === "verified" ||
      taskStatus === "done",
  );
}

function humanApprovalRecorded(input: WorkflowProgressInput): boolean {
  return Boolean(input.approvalGate.approvedAt);
}

function verificationPassed(input: WorkflowProgressInput): boolean {
  const verification =
    input.longRunningTask.response?.task?.post_apply_verification ??
    input.approvalGate.execution?.post_apply_verification ??
    null;
  return verification?.status === "verified";
}

function verificationPending(input: WorkflowProgressInput): boolean {
  const taskStatus = input.longRunningTask.response?.task?.status ?? "";
  const verification =
    input.longRunningTask.response?.task?.post_apply_verification ??
    input.approvalGate.execution?.post_apply_verification ??
    null;
  return (
    taskStatus === "applied_needs_verification" ||
    verification?.status === "verification_ready" ||
    verification?.status === "manual_verification_required"
  );
}

function applyingNow(input: WorkflowProgressInput): boolean {
  const taskStatus = input.longRunningTask.response?.task?.status ?? "";
  return (
    input.approvalGate.isChecking ||
    input.longRunningTask.isChecking ||
    taskStatus === "executing"
  );
}

function approvalRequired(input: WorkflowProgressInput): boolean {
  return (
    input.approvalGate.preview?.requires_human_approval === true ||
    input.approvalGate.preview?.decision === "requires_human_approval"
  );
}

function blockedLabel(input: WorkflowProgressInput): string {
  const blocker = input.stability.lastBlocker;
  if (blocker) {
    return `Blocked: ${blocker}`;
  }
  if (input.stability.primaryState === "Failed") {
    return "Blocked: verification or execution failed";
  }
  return "Blocked";
}

export function deriveWorkflowApplyChecklist(
  input: WorkflowProgressInput,
): WorkflowApplyChecklistItem[] {
  const executed = applyExecuted(input);
  const approved = humanApprovalRecorded(input);
  const ready = previewReady(input);
  const blocked = previewBlocked(input);
  const verifyPass = verificationPassed(input);
  const verifyPending = verificationPending(input);

  const diffStatus: WorkflowChecklistStatus = blocked
    ? "blocked"
    : ready
      ? "pass"
      : "waiting";

  let approvalStatus: WorkflowChecklistStatus = "waiting";
  if (approved || executed) {
    approvalStatus = "pass";
  } else if (
    input.stability.approvalState === "unavailable" ||
    input.stability.primaryState === "Blocked"
  ) {
    approvalStatus = "blocked";
  }

  const applyStatus: WorkflowChecklistStatus = executed
    ? "pass"
    : applyingNow(input)
      ? "waiting"
      : approved && !executed
        ? "waiting"
        : "waiting";

  let verifyStatus: WorkflowChecklistStatus = "waiting";
  if (verifyPass) {
    verifyStatus = "pass";
  } else if (verifyPending) {
    verifyStatus = "waiting";
  } else if (
    input.longRunningTask.response?.task?.post_apply_verification?.status ===
    "verification_failed"
  ) {
    verifyStatus = "blocked";
  }

  return [
    {
      id: "diff_preview",
      label: "Diff preview ready",
      status: diffStatus,
      detail: blocked
        ? "Preview is blocked until safety issues are resolved."
        : ready
          ? "Read-only preview passed."
          : "Waiting for a valid diff preview.",
    },
    {
      id: "human_approval",
      label: "Human approval recorded",
      status: approvalStatus,
      detail:
        approvalStatus === "pass"
          ? "Approve was recorded."
          : "Approve applies the reviewed diff through the protected path.",
    },
    {
      id: "apply_executed",
      label: "Apply executed",
      status: applyStatus,
      detail: executed
        ? "Files were written through the protected execution layer."
        : "No workspace writes until Approve succeeds.",
    },
    {
      id: "post_apply_verification",
      label: "Post-apply verification passed",
      status: verifyStatus,
      detail: verifyPass
        ? "Verification completed."
        : verifyPending
          ? "Run verification before marking done."
          : "Verification runs after apply.",
    },
  ];
}

export function deriveWorkflowProgressCopy(
  input: WorkflowProgressInput,
): WorkflowProgressCopy {
  const executed = applyExecuted(input);
  const approved = humanApprovalRecorded(input);
  const ready = previewReady(input);
  const required = approvalRequired(input);
  const checklist = deriveWorkflowApplyChecklist(input);

  if (
    input.stability.primaryState === "Blocked" ||
    input.stability.primaryState === "Failed" ||
    previewBlocked(input)
  ) {
    const stepLabel = blockedLabel(input);
    return {
      stepLabel,
      headline: stepLabel,
      nextAction: "Resolve the blocker, then regenerate or revise the diff preview.",
      applyExecuted: executed ? "yes" : "no",
      applyExecutedHelper: executed
        ? "Apply executed. Files were written through the protected path."
        : "Preview only. No file writes happen until you click Approve.",
      checklist,
    };
  }

  if (
    input.stability.primaryState === "Done" ||
    input.stability.primaryState === "Verified" ||
    verificationPassed(input)
  ) {
    return {
      stepLabel: "Verified complete",
      headline: "Verified complete",
      nextAction: null,
      applyExecuted: executed ? "yes" : "no",
      applyExecutedHelper: executed
        ? "Apply executed. Post-apply verification passed."
        : "No apply was required for this task.",
      checklist,
    };
  }

  if (verificationPending(input)) {
    return {
      stepLabel: "Applied, verification required",
      headline: "Applied, verification required",
      nextAction: "Next: run post-apply verification before marking done.",
      applyExecuted: "yes",
      applyExecutedHelper: "Apply executed. Verification is still required.",
      checklist,
    };
  }

  if (applyingNow(input)) {
    return {
      stepLabel: "Applying approved diff",
      headline: "Applying approved diff",
      nextAction: "Wait for the protected apply path to finish.",
      applyExecuted: executed ? "yes" : "no",
      applyExecutedHelper: executed
        ? "Apply executed."
        : "Apply in progress. No additional approval is needed during execution.",
      checklist,
    };
  }

  if (approved && !executed) {
    return {
      stepLabel: "Human approved, waiting to apply",
      headline: "Human approved, waiting to apply",
      nextAction:
        "Next: click Apply approved diff. Approval alone does not change files.",
      applyExecuted: "no",
      applyExecutedHelper:
        "Approval is recorded, but apply has not completed yet.",
      checklist,
    };
  }

  if (ready && required && !approved && !executed) {
    return {
      stepLabel: "Preview ready, waiting for approval",
      headline: "Preview ready. Human approval required before apply.",
      nextAction:
        "Next: inspect the diff, then click Approve. No files have changed yet.",
      applyExecuted: "no",
      applyExecutedHelper:
        "Preview only. No file writes happen until you click Approve.",
      checklist,
    };
  }

  return {
    stepLabel: input.stability.primaryState,
    headline: input.stability.primaryState,
    nextAction: null,
    applyExecuted: executed ? "yes" : "no",
    applyExecutedHelper: executed
      ? "Apply executed. Files were written through the protected path."
      : ready
        ? "Preview only. No file writes happen until you click Approve."
        : "Apply not executed yet.",
    checklist,
  };
}
