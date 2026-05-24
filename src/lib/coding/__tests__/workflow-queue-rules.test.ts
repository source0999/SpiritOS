import { describe, expect, it } from "vitest";

import {
  evaluateWorkflowQueueAction,
  isParallelReadOnlyReviewWorkflow,
  isWriteCapableWorkflow,
  type WorkflowQueueItem,
} from "@/lib/coding/workflow-queue-rules";

const activeDocsTask: WorkflowQueueItem = {
  id: "task-docs",
  scopeKey: "docs/source-proxy-daily-use-runbook.md",
  status: "active",
  workflowType: "docs_update",
};

describe("workflow queue rules", () => {
  it("blocks a second write-capable workflow on the same live scope", () => {
    const result = evaluateWorkflowQueueAction({
      action: "start",
      candidate: {
        id: "task-bugfix",
        scopeKey: "docs/source-proxy-daily-use-runbook.md",
        status: "queued",
        workflowType: "bugfix",
      },
      existing: [activeDocsTask],
    });

    expect(result.allowed).toBe(false);
    expect(result.reasonCode).toBe("write_scope_conflict");
    expect(result.authority.apply).toBe(false);
    expect(result.authority.commit).toBe(false);
    expect(result.authority.push).toBe(false);
  });

  it("allows read-only analysis beside a write-capable workflow on the same scope", () => {
    const result = evaluateWorkflowQueueAction({
      action: "start",
      candidate: {
        id: "task-review",
        scopeKey: "docs/source-proxy-daily-use-runbook.md",
        sourceTaskId: "task-docs",
        sourceThreadId: "thread-review-1",
        status: "queued",
        workflowType: "review_only_analysis",
      },
      existing: [activeDocsTask],
    });

    expect(result.allowed).toBe(true);
    expect(result.reasonCode).toBe("parallel_read_only_review_allowed");
    expect(result.authority.approval).toBe(false);
    expect(result.authority.apply).toBe(false);
    expect(result.reviewEvent).toContain("source task task-docs");
    expect(result.reviewEvent).toContain("thread thread-review-1");
  });

  it("blocks parallel read-only review on an occupied scope without source labels", () => {
    const result = evaluateWorkflowQueueAction({
      action: "start",
      candidate: {
        id: "task-review-unlabeled",
        scopeKey: "docs/source-proxy-daily-use-runbook.md",
        status: "queued",
        workflowType: "review_only_analysis",
      },
      existing: [activeDocsTask],
    });

    expect(result.allowed).toBe(false);
    expect(result.reasonCode).toBe("parallel_review_source_label_missing");
    expect(result.authority.approval).toBe(false);
    expect(result.authority.apply).toBe(false);
    expect(result.authority.commit).toBe(false);
    expect(result.authority.push).toBe(false);
  });

  it("allows write-capable workflows on different scopes", () => {
    const result = evaluateWorkflowQueueAction({
      action: "start",
      candidate: {
        id: "task-shell",
        scopeKey: "src/components/coding/CodingCommandCenterShell.tsx",
        status: "queued",
        workflowType: "coding_task",
      },
      existing: [activeDocsTask],
    });

    expect(result.allowed).toBe(true);
    expect(result.reasonCode).toBe("start_allowed");
  });

  it("keeps cancellation reviewable and inert", () => {
    const result = evaluateWorkflowQueueAction({
      action: "cancel",
      candidate: activeDocsTask,
      existing: [activeDocsTask],
    });

    expect(result.allowed).toBe(true);
    expect(result.reasonCode).toBe("cancellation_allowed");
    expect(result.reviewEvent).toContain("task-docs");
    expect(result.authority.apply).toBe(false);
  });

  it("allows retry only after cancelled or failed terminal states", () => {
    const activeRetry = evaluateWorkflowQueueAction({
      action: "retry",
      candidate: activeDocsTask,
      existing: [],
    });
    const failedRetry = evaluateWorkflowQueueAction({
      action: "retry",
      candidate: {
        ...activeDocsTask,
        id: "task-docs-retry",
        status: "failed",
      },
      existing: [],
    });

    expect(activeRetry.allowed).toBe(false);
    expect(activeRetry.reasonCode).toBe("retry_requires_terminal_status");
    expect(failedRetry.allowed).toBe(true);
    expect(failedRetry.reasonCode).toBe("retry_allowed");
    expect(failedRetry.authority.apply).toBe(false);
  });

  it("does not treat review, verification, or blocked workflows as write-capable", () => {
    expect(isWriteCapableWorkflow("coding_task")).toBe(true);
    expect(isWriteCapableWorkflow("review_only_analysis")).toBe(false);
    expect(isWriteCapableWorkflow("verification_only")).toBe(false);
    expect(isWriteCapableWorkflow("blocked_unsafe")).toBe(false);
    expect(isParallelReadOnlyReviewWorkflow("review_only_analysis")).toBe(true);
    expect(isParallelReadOnlyReviewWorkflow("verification_only")).toBe(true);
    expect(isParallelReadOnlyReviewWorkflow("coding_task")).toBe(false);
  });

  it("blocks unsafe workflow switching and missing scope", () => {
    const unsafeSwitch = evaluateWorkflowQueueAction({
      action: "switch",
      candidate: {
        id: "task-unsafe",
        scopeKey: "src/app/coding/page.tsx",
        status: "queued",
        workflowType: "blocked_unsafe",
      },
      existing: [],
    });
    const missingScope = evaluateWorkflowQueueAction({
      action: "start",
      candidate: {
        id: "task-missing",
        scopeKey: "   ",
        status: "queued",
        workflowType: "coding_task",
      },
      existing: [],
    });

    expect(unsafeSwitch.allowed).toBe(false);
    expect(unsafeSwitch.reasonCode).toBe("blocked_workflow_cannot_switch");
    expect(missingScope.allowed).toBe(false);
    expect(missingScope.reasonCode).toBe("scope_missing");
  });
});
