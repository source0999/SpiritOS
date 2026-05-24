import type { CodingWorkflowType } from "@/lib/coding/workflow-type";

export type WorkflowQueueStatus = "active" | "queued" | "cancelled" | "completed" | "failed";

export type WorkflowQueueItem = {
  id: string;
  scopeKey: string;
  status: WorkflowQueueStatus;
  sourceTaskId?: string;
  sourceThreadId?: string;
  workflowType: CodingWorkflowType;
};

export type WorkflowQueueAction = "start" | "switch" | "cancel" | "retry";

export type WorkflowQueueDecision = {
  allowed: boolean;
  authority: {
    approval: false;
    apply: false;
    commit: false;
    push: false;
  };
  reasonCode: string;
  reviewEvent: string;
};

const WRITE_CAPABLE_WORKFLOWS = new Set<CodingWorkflowType>([
  "bugfix",
  "coding_task",
  "docs_update",
  "test_generation",
]);

const LIVE_STATUSES = new Set<WorkflowQueueStatus>(["active", "queued"]);
const RETRYABLE_STATUSES = new Set<WorkflowQueueStatus>(["cancelled", "failed"]);
const PARALLEL_REVIEW_WORKFLOWS = new Set<CodingWorkflowType>([
  "review_only_analysis",
  "verification_only",
]);

export function isWriteCapableWorkflow(workflowType: CodingWorkflowType): boolean {
  return WRITE_CAPABLE_WORKFLOWS.has(workflowType);
}

export function isParallelReadOnlyReviewWorkflow(workflowType: CodingWorkflowType): boolean {
  return PARALLEL_REVIEW_WORKFLOWS.has(workflowType);
}

export function evaluateWorkflowQueueAction(input: {
  action: WorkflowQueueAction;
  candidate: WorkflowQueueItem;
  existing: WorkflowQueueItem[];
}): WorkflowQueueDecision {
  const scopeKey = normalizeScopeKey(input.candidate.scopeKey);
  if (!scopeKey) {
    return decision(false, "scope_missing", "Queue action blocked because scope is missing.");
  }

  if (input.action === "cancel") {
    return decision(true, "cancellation_allowed", `Cancellation is reviewable for ${input.candidate.id}.`);
  }

  if (input.action === "retry" && !RETRYABLE_STATUSES.has(input.candidate.status)) {
    return decision(
      false,
      "retry_requires_terminal_status",
      `Retry blocked for ${input.candidate.id} until it is cancelled or failed.`,
    );
  }

  const parallelReviewDecision = evaluateParallelReadOnlyReview(input.candidate, input.existing);
  if (parallelReviewDecision) {
    return parallelReviewDecision;
  }

  if (hasWriteScopeConflict(input.candidate, input.existing)) {
    return decision(
      false,
      "write_scope_conflict",
      `Queue action blocked because another write-capable workflow already owns ${scopeKey}.`,
    );
  }

  if (input.action === "switch" && input.candidate.workflowType === "blocked_unsafe") {
    return decision(
      false,
      "blocked_workflow_cannot_switch",
      `Switch blocked because ${input.candidate.id} is unsafe.`,
    );
  }

  return decision(
    true,
    `${input.action}_allowed`,
    `Queue action ${input.action} is reviewable for ${input.candidate.id}.`,
  );
}

function evaluateParallelReadOnlyReview(
  candidate: WorkflowQueueItem,
  existing: WorkflowQueueItem[],
): WorkflowQueueDecision | null {
  if (!isParallelReadOnlyReviewWorkflow(candidate.workflowType)) {
    return null;
  }

  const candidateScope = normalizeScopeKey(candidate.scopeKey);
  const overlapsLiveScope = existing.some(
    (item) =>
      item.id !== candidate.id &&
      LIVE_STATUSES.has(item.status) &&
      normalizeScopeKey(item.scopeKey) === candidateScope,
  );
  if (!overlapsLiveScope) {
    return null;
  }

  if (!candidate.sourceTaskId?.trim() || !candidate.sourceThreadId?.trim()) {
    return decision(
      false,
      "parallel_review_source_label_missing",
      `Parallel read-only review blocked for ${candidate.id} until source task and thread labels are present.`,
    );
  }

  return decision(
    true,
    "parallel_read_only_review_allowed",
    `Parallel read-only review ${candidate.id} is labeled by source task ${candidate.sourceTaskId} and thread ${candidate.sourceThreadId}.`,
  );
}

function hasWriteScopeConflict(candidate: WorkflowQueueItem, existing: WorkflowQueueItem[]): boolean {
  if (!isWriteCapableWorkflow(candidate.workflowType)) {
    return false;
  }

  const candidateScope = normalizeScopeKey(candidate.scopeKey);
  return existing.some((item) => {
    if (item.id === candidate.id || !LIVE_STATUSES.has(item.status)) {
      return false;
    }
    return (
      isWriteCapableWorkflow(item.workflowType) &&
      normalizeScopeKey(item.scopeKey) === candidateScope
    );
  });
}

function normalizeScopeKey(scopeKey: string): string {
  return scopeKey.trim().toLowerCase();
}

function decision(
  allowed: boolean,
  reasonCode: string,
  reviewEvent: string,
): WorkflowQueueDecision {
  return {
    allowed,
    authority: {
      approval: false,
      apply: false,
      commit: false,
      push: false,
    },
    reasonCode,
    reviewEvent,
  };
}
