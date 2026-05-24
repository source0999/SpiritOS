const QUEUE_RUN_NEXT_ENDPOINT = "/v1/cartographer/queue/run-next";

export type CartographerQueueStatus = {
  available: boolean;
  queueStatus: string;
  runNextStatus: string;
  runNextMethod: string;
  selectionAvailable: boolean;
  executionAvailable: boolean;
  durableStorageAvailable: boolean;
  queueWorkerAvailable: boolean;
  backgroundLoopAvailable: boolean;
  runSelectedTaskAvailable: boolean;
  receiptAvailable: boolean;
  requiredTrustTier: string;
  allowedTaskClassCount: number;
  taskStatusCount: number;
  safeNextAction: string;
  detail: string;
};

const unavailableQueueStatus: CartographerQueueStatus = {
  available: false,
  queueStatus: "unavailable",
  runNextStatus: "unavailable",
  runNextMethod: "none",
  selectionAvailable: false,
  executionAvailable: false,
  durableStorageAvailable: false,
  queueWorkerAvailable: false,
  backgroundLoopAvailable: false,
  runSelectedTaskAvailable: false,
  receiptAvailable: false,
  requiredTrustTier: "unavailable",
  allowedTaskClassCount: 0,
  taskStatusCount: 0,
  safeNextAction:
    "Stop and manually verify queue status before any later queue authority expansion.",
  detail: "Queue status could not be read.",
};

export async function getCartographerQueueStatus(
  origin: string | null,
): Promise<CartographerQueueStatus> {
  if (!origin) {
    return {
      ...unavailableQueueStatus,
      detail: "Request origin was unavailable, so queue status was not fetched.",
    };
  }

  try {
    const response = await fetch(`${origin}${QUEUE_RUN_NEXT_ENDPOINT}`, {
      method: "GET",
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        ...unavailableQueueStatus,
        detail: `Queue status endpoint returned HTTP ${response.status}.`,
      };
    }

    const payload: unknown = await response.json();
    return normalizeQueueStatus(payload);
  } catch (error) {
    return {
      ...unavailableQueueStatus,
      detail:
        error instanceof Error
          ? `Queue status request failed: ${error.message}`
          : "Queue status request failed.",
    };
  }
}

function normalizeQueueStatus(payload: unknown): CartographerQueueStatus {
  if (!isRecord(payload)) {
    return {
      ...unavailableQueueStatus,
      detail: "Queue status endpoint returned an unexpected payload shape.",
    };
  }

  const queue = isRecord(payload.queue) ? payload.queue : {};
  const runNext = isRecord(payload.run_next) ? payload.run_next : {};
  const selectionAvailable = booleanValue(runNext.selection_available) ?? false;
  const executionAvailable = booleanValue(runNext.execution_available) ?? false;

  return {
    available: true,
    queueStatus: stringValue(queue.status) ?? "unknown",
    runNextStatus: stringValue(runNext.status) ?? "unknown",
    runNextMethod: stringValue(runNext.method) ?? "unknown",
    selectionAvailable,
    executionAvailable,
    durableStorageAvailable:
      booleanValue(runNext.durable_storage_available) ??
      booleanValue(queue.durable_storage_available) ??
      false,
    queueWorkerAvailable:
      booleanValue(runNext.queue_worker_available) ??
      booleanValue(queue.queue_worker_available) ??
      false,
    backgroundLoopAvailable: booleanValue(runNext.background_loop_available) ?? false,
    runSelectedTaskAvailable:
      booleanValue(runNext.run_selected_task_available) ?? false,
    receiptAvailable:
      booleanValue(runNext.receipt_available) ??
      booleanValue(queue.receipt_available) ??
      false,
    requiredTrustTier: stringValue(queue.required_trust_tier) ?? "unknown",
    allowedTaskClassCount: arrayLength(queue.allowed_task_classes),
    taskStatusCount: arrayLength(queue.task_statuses),
    safeNextAction:
      stringValue(runNext.safe_next_action) ??
      "Keep queue status display-only and require human review.",
    detail:
      selectionAvailable && !executionAvailable
        ? "Run-next can report one-task selection eligibility, but /map adds no execution control."
        : "Queue status is shown as read-only data and grants no execution authority.",
  };
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function arrayLength(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
