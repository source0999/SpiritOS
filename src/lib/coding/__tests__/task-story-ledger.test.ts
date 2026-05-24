import { describe, expect, it } from "vitest";

import {
  appendTaskStoryEvent,
  createTaskStoryLedger,
  summarizeTaskStoryLedger,
} from "@/lib/coding/task-story-ledger";

describe("task story ledger", () => {
  it("records reviewable task story events without inventing authority", () => {
    let ledger = createTaskStoryLedger({
      taskId: "task-123",
      title: "Docs receipt update",
      workflowType: "docs_update",
    });

    ledger = appendTaskStoryEvent(ledger, {
      detail: "target docs/source-proxy-daily-use-runbook.md",
      timestamp: "2026-05-22T00:00:00Z",
      type: "scope",
    });
    ledger = appendTaskStoryEvent(ledger, {
      detail: "docs/source-proxy-daily-use-runbook.md",
      timestamp: "2026-05-22T00:01:00Z",
      type: "diff",
    });
    ledger = appendTaskStoryEvent(ledger, {
      detail: "git diff --check: pass",
      timestamp: "2026-05-22T00:02:00Z",
      type: "check",
    });

    const summary = summarizeTaskStoryLedger(ledger);

    expect(summary.eventCount).toBe(3);
    expect(summary.changedFiles).toEqual(["docs/source-proxy-daily-use-runbook.md"]);
    expect(summary.checks).toEqual(["git diff --check: pass"]);
    expect(summary.approvalRecorded).toBe(false);
    expect(summary.applyRecorded).toBe(false);
    expect(summary.verificationRecorded).toBe(false);
  });

  it("keeps apply and verification as separate ledger events", () => {
    let ledger = createTaskStoryLedger({
      taskId: "task-apply",
      title: "Apply proof",
      workflowType: "coding_task",
    });
    ledger = appendTaskStoryEvent(ledger, { detail: "human approved", type: "approval" });
    ledger = appendTaskStoryEvent(ledger, { detail: "execute-approved returned success", type: "apply" });

    const beforeVerification = summarizeTaskStoryLedger(ledger);
    expect(beforeVerification.approvalRecorded).toBe(true);
    expect(beforeVerification.applyRecorded).toBe(true);
    expect(beforeVerification.verificationRecorded).toBe(false);

    ledger = appendTaskStoryEvent(ledger, { detail: "post-apply verification pass", type: "verification" });
    expect(summarizeTaskStoryLedger(ledger).verificationRecorded).toBe(true);
  });

  it("captures blockers, retry, and cancellation without changing task identity", () => {
    let ledger = createTaskStoryLedger({
      taskId: "",
      title: "",
      workflowType: "blocked_unsafe",
    });
    ledger = appendTaskStoryEvent(ledger, { detail: "target_unresolved", type: "blocker" });
    ledger = appendTaskStoryEvent(ledger, { detail: "operator narrowed scope", type: "retry" });
    ledger = appendTaskStoryEvent(ledger, { detail: "cancelled before preview", type: "cancellation" });
    ledger = appendTaskStoryEvent(ledger, { detail: "   ", type: "check" });

    const summary = summarizeTaskStoryLedger(ledger);

    expect(ledger.taskId).toBe("local-task");
    expect(ledger.title).toBe("Untitled task");
    expect(summary.eventCount).toBe(3);
    expect(summary.blockers).toEqual(["target_unresolved"]);
    expect(summary.cancellationRecorded).toBe(true);
  });
});
