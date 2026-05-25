const WORKFLOW_RUN_CARD_ENDPOINT = "/v1/cartographer/level-8-workflow-run-card";

export type CartographerWorkflowStep = {
  stepId: string;
  title: string;
  status: string;
  source: string;
  blockers: string[];
};

export type CartographerWorkflowStatus = {
  available: boolean;
  workflowId: string;
  workflowTitle: string;
  workflowStatus: string;
  activeRunCount: number;
  recentRunCount: number;
  stepCount: number;
  blockedStepCount: number;
  steps: CartographerWorkflowStep[];
  blockers: string[];
  executionAvailable: boolean;
  backgroundExecutionAllowed: boolean;
  autonomousRetryAllowed: boolean;
  authorityGranted: boolean;
  safeNextAction: string;
  detail: string;
};

const unavailableWorkflowStatus: CartographerWorkflowStatus = {
  available: false,
  workflowId: "unavailable",
  workflowTitle: "Workflow status unavailable",
  workflowStatus: "unavailable",
  activeRunCount: 0,
  recentRunCount: 0,
  stepCount: 0,
  blockedStepCount: 0,
  steps: [],
  blockers: ["workflow_run_card_unavailable"],
  executionAvailable: false,
  backgroundExecutionAllowed: false,
  autonomousRetryAllowed: false,
  authorityGranted: false,
  safeNextAction:
    "Stop and manually verify workflow status before any workflow authority expansion.",
  detail: "Workflow run status could not be read.",
};

export async function getCartographerWorkflowStatus(
  origin: string | null,
): Promise<CartographerWorkflowStatus> {
  if (!origin) {
    return {
      ...unavailableWorkflowStatus,
      detail: "Request origin was unavailable, so workflow status was not fetched.",
    };
  }

  try {
    const response = await fetch(`${origin}${WORKFLOW_RUN_CARD_ENDPOINT}`, {
      method: "GET",
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        ...unavailableWorkflowStatus,
        detail: `Workflow status endpoint returned HTTP ${response.status}.`,
      };
    }

    const payload: unknown = await response.json();
    return normalizeWorkflowStatus(payload);
  } catch (error) {
    return {
      ...unavailableWorkflowStatus,
      detail:
        error instanceof Error
          ? `Workflow status request failed: ${error.message}`
          : "Workflow status request failed.",
    };
  }
}

function normalizeWorkflowStatus(payload: unknown): CartographerWorkflowStatus {
  if (!isRecord(payload)) {
    return {
      ...unavailableWorkflowStatus,
      detail: "Workflow status endpoint returned an unexpected payload shape.",
    };
  }

  const workflow = isRecord(payload.workflow) ? payload.workflow : {};
  const workflowStatus = stringValue(workflow.status) ?? "unknown";
  const steps = stepArray(workflow.steps);
  const activeRunCount = isTerminalWorkflowStatus(workflowStatus) ? 0 : 1;

  return {
    available: true,
    workflowId: stringValue(workflow.workflow_id) ?? "unknown",
    workflowTitle: stringValue(workflow.title) ?? "Workflow run",
    workflowStatus,
    activeRunCount,
    recentRunCount: 1,
    stepCount: numberValue(payload.step_count) ?? steps.length,
    blockedStepCount:
      numberValue(payload.blocked_step_count) ??
      steps.filter((step) => step.blockers.length > 0).length,
    steps,
    blockers: stringArray(payload.blockers).concat(stringArray(workflow.blockers)),
    executionAvailable:
      booleanValue(payload.automatic_execution_allowed) ??
      booleanValue(workflow.cartographer_may_execute_steps) ??
      false,
    backgroundExecutionAllowed:
      booleanValue(payload.background_execution_allowed) ??
      booleanValue(workflow.background_execution_allowed) ??
      false,
    autonomousRetryAllowed:
      booleanValue(payload.autonomous_retry_allowed) ??
      booleanValue(workflow.autonomous_retry_allowed) ??
      false,
    authorityGranted: booleanValue(payload.authority_granted) ?? false,
    safeNextAction:
      stringValue(payload.next_step) ??
      "Keep workflow run status display-only and require human review.",
    detail:
      "Workflow run data is shown for operator review only; /map adds no start, retry, pause, cancel, or approval controls.",
  };
}

function stepArray(value: unknown): CartographerWorkflowStep[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(isRecord).map((step, index) => {
    const blockers = stringArray(step.blockers);
    return {
      stepId: stringValue(step.step_id) ?? `workflow-step-${index + 1}`,
      title: stringValue(step.title) ?? "Untitled workflow step",
      status: blockers.length > 0 ? "blocked" : "ready_for_human_review",
      source: stringValue(step.source) ?? "unknown",
      blockers,
    };
  });
}

function isTerminalWorkflowStatus(status: string): boolean {
  return status === "completed" || status === "failed" || status === "cancelled";
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
