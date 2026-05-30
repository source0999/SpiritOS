import type { CodingWorkflowType } from "@/lib/coding/workflow-type";

export type TaskStoryEventType =
  | "scope"
  | "diff"
  | "check"
  | "blocker"
  | "approval"
  | "apply"
  | "verification"
  | "retry"
  | "cancellation";

export type TaskStoryEvent = {
  detail: string;
  timestamp: string;
  type: TaskStoryEventType;
};

export type TaskStoryLedger = {
  events: TaskStoryEvent[];
  taskId: string;
  title: string;
  workflowType: CodingWorkflowType;
};

export function createTaskStoryLedger(input: {
  taskId: string;
  title: string;
  workflowType: CodingWorkflowType;
}): TaskStoryLedger {
  return {
    events: [],
    taskId: input.taskId.trim() || "local-task",
    title: input.title.trim() || "Untitled task",
    workflowType: input.workflowType,
  };
}

export function appendTaskStoryEvent(
  ledger: TaskStoryLedger,
  event: Omit<TaskStoryEvent, "timestamp"> & { timestamp?: string },
): TaskStoryLedger {
  const detail = event.detail.trim();
  if (!detail) {
    return ledger;
  }
  return {
    ...ledger,
    events: [
      ...ledger.events,
      {
        detail,
        timestamp: event.timestamp ?? new Date(0).toISOString(),
        type: event.type,
      },
    ],
  };
}

export function summarizeTaskStoryLedger(ledger: TaskStoryLedger): {
  applyRecorded: boolean;
  approvalRecorded: boolean;
  blockers: string[];
  cancellationRecorded: boolean;
  changedFiles: string[];
  checks: string[];
  eventCount: number;
  verificationRecorded: boolean;
} {
  return {
    applyRecorded: hasEvent(ledger, "apply"),
    approvalRecorded: hasEvent(ledger, "approval"),
    blockers: eventDetails(ledger, "blocker"),
    cancellationRecorded: hasEvent(ledger, "cancellation"),
    changedFiles: eventDetails(ledger, "diff"),
    checks: eventDetails(ledger, "check"),
    eventCount: ledger.events.length,
    verificationRecorded: hasEvent(ledger, "verification"),
  };
}

function hasEvent(ledger: TaskStoryLedger, type: TaskStoryEventType): boolean {
  return ledger.events.some((event) => event.type === type);
}

function eventDetails(ledger: TaskStoryLedger, type: TaskStoryEventType): string[] {
  return ledger.events.filter((event) => event.type === type).map((event) => event.detail);
}
