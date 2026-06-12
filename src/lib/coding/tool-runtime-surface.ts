export type ToolRuntimeActionDisplay = {
  actionType: string;
  adapterSource: string;
  blockedReason: string;
  status: string;
  target: string;
};

export type ToolRuntimeSurface = {
  actions: ToolRuntimeActionDisplay[];
  advisoryTruth: {
    macSubagentsAdvisoryOnly: boolean;
    sourceProxyFinalGate: boolean;
  };
  applyAuthority: false;
  checkOutput: string;
  diagnosticsText: string;
  diffSummary: string;
  filesTouched: string[];
  modelLane: string;
  safeApplyStatus: string;
  taskSpec: {
    allowedFiles: string[];
    clarificationState: string;
    taskKind: string;
    workspaceMode: string;
  };
  toolTruth: {
    exposed: string[];
    writeExecutionScope: string;
  };
};

const DEFAULT_TOOLS = [
  "ReadFile",
  "ListFiles",
  "SearchRepo",
  "WriteFile",
  "EditFile",
  "MultiEdit",
  "RunCheck",
  "AskClarification",
  "ReturnFinal",
];

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function stringValue(value: unknown, fallback = "not reported"): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0) : [];
}

export function buildToolRuntimeSurface(payload: unknown): ToolRuntimeSurface {
  const record = asRecord(payload);
  const taskSpec = asRecord(record.task_spec_intake ?? record.taskSpecIntake ?? record.task_spec ?? record.taskSpec);
  const receipt = asRecord(record.receipt);
  const diagnostics = asRecord(record.diagnostics_packet ?? record.diagnosticsPacket ?? receipt.diagnostics_packet ?? receipt.diagnosticsPacket);
  const executions = Array.isArray(record.executions)
    ? record.executions
    : Array.isArray(receipt.executions)
      ? receipt.executions
      : [];
  const parsedActions = Array.isArray(record.parsed_actions)
    ? record.parsed_actions
    : Array.isArray(record.parsedActions)
      ? record.parsedActions
      : Array.isArray(receipt.parsed_actions)
        ? receipt.parsed_actions
        : [];
  const actions = parsedActions.map((rawAction, index): ToolRuntimeActionDisplay => {
    const action = asRecord(rawAction);
    const execution = asRecord(executions[index]);
    const result = asRecord(execution.result);
    return {
      actionType: stringValue(action.action_type ?? action.actionType, "unknown"),
      adapterSource: stringValue(action.adapter_source ?? action.adapterSource, "generic"),
      blockedReason: stringValue(result.blocked_reason ?? result.blockedReason, "none"),
      status: stringValue(result.status, stringValue(action.execution_state ?? action.executionState, "parsed")),
      target: stringValue(action.target, "not reported"),
    };
  });
  const filesTouched = stringArray(diagnostics.files_touched ?? diagnostics.filesTouched).length > 0
    ? stringArray(diagnostics.files_touched ?? diagnostics.filesTouched)
    : executions.flatMap((rawExecution) => stringArray(asRecord(asRecord(rawExecution).result).files_touched));
  const diffSummary = executions
    .map((rawExecution) => stringValue(asRecord(asRecord(rawExecution).result).diff_summary, ""))
    .filter(Boolean)
    .join("\n")
    .trim();
  const checkOutput = executions
    .map((rawExecution) => {
      const result = asRecord(asRecord(rawExecution).result);
      return [stringValue(result.stdout, ""), stringValue(result.stderr, "")]
        .filter(Boolean)
        .join("\n");
    })
    .filter(Boolean)
    .join("\n")
    .trim();
  const allowedFiles = stringArray(taskSpec.allowed_files ?? taskSpec.allowedFiles);
  const toolNames = stringArray(record.tools_exposed ?? record.toolsExposed);
  const surface: ToolRuntimeSurface = {
    actions,
    advisoryTruth: {
      macSubagentsAdvisoryOnly: true,
      sourceProxyFinalGate: true,
    },
    applyAuthority: false,
    checkOutput: checkOutput || "not run or not reported",
    diagnosticsText: "",
    diffSummary: diffSummary || "No disposable workspace diff reported.",
    filesTouched,
    modelLane: stringValue(taskSpec.model_lane ?? taskSpec.modelLane ?? record.model_lane ?? record.modelLane, "not reported"),
    safeApplyStatus: "blocked unless separately approved",
    taskSpec: {
      allowedFiles,
      clarificationState: stringValue(taskSpec.clarification_state ?? taskSpec.clarificationState, "not reported"),
      taskKind: stringValue(taskSpec.task_kind ?? taskSpec.taskKind ?? taskSpec.task_type ?? taskSpec.taskType, "not reported"),
      workspaceMode: stringValue(taskSpec.workspace_mode ?? taskSpec.workspaceMode, "not reported"),
    },
    toolTruth: {
      exposed: toolNames.length > 0 ? toolNames : DEFAULT_TOOLS,
      writeExecutionScope: "disposable workspace only",
    },
  };
  return {
    ...surface,
    diagnosticsText: toolRuntimeDiagnosticsText(surface),
  };
}

export function toolRuntimeDiagnosticsText(surface: ToolRuntimeSurface): string {
  return [
    "Source Proxy tool runtime diagnostics",
    `task_kind: ${surface.taskSpec.taskKind}`,
    `clarification_state: ${surface.taskSpec.clarificationState}`,
    `workspace_mode: ${surface.taskSpec.workspaceMode}`,
    `model_lane: ${surface.modelLane}`,
    `tools_exposed: ${surface.toolTruth.exposed.join(", ")}`,
    `write_execution_scope: ${surface.toolTruth.writeExecutionScope}`,
    `actions_attempted: ${surface.actions.map((action) => `${action.actionType}:${action.status}:${action.target}`).join("; ") || "none"}`,
    `blocked_reasons: ${surface.actions.map((action) => action.blockedReason).filter((reason) => reason !== "none").join("; ") || "none"}`,
    `files_touched: ${surface.filesTouched.join(", ") || "none"}`,
    `diff_summary: ${surface.diffSummary}`,
    `check_output: ${surface.checkOutput}`,
    `safe_apply_status: ${surface.safeApplyStatus}`,
    `mac_subagents_advisory_only: ${surface.advisoryTruth.macSubagentsAdvisoryOnly}`,
    `source_proxy_final_gate: ${surface.advisoryTruth.sourceProxyFinalGate}`,
  ].join("\n");
}
