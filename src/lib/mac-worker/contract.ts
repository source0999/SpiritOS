import {
  MAC_WORKER_NODE_ID,
  MAC_WORKER_JOB_ENVELOPE_VERSION,
  MAC_WORKER_RESULT_ENVELOPE_VERSION,
  macWorkerJobTypes,
  type MacWorkerCapabilityDescriptor,
  type MacWorkerJob,
  type MacWorkerJobResult,
  type MacWorkerJobType,
  type MacWorkerRunSummary,
  type MacWorkerTraceFields,
} from "./types";

export function isMacWorkerJobType(value: unknown): value is MacWorkerJobType {
  return typeof value === "string" && (macWorkerJobTypes as readonly string[]).includes(value);
}

export function createMacWorkerJob(
  jobType: MacWorkerJobType,
  input: MacWorkerJob["input"] = {},
  jobId = `${jobType}-${Date.now()}`,
): MacWorkerJob {
  return {
    job_id: jobId,
    job_type: jobType,
    input,
    node_id: MAC_WORKER_NODE_ID,
    created_at: new Date().toISOString(),
    job_envelope_version: MAC_WORKER_JOB_ENVELOPE_VERSION,
  };
}

export function createTracedMacWorkerJob(
  jobType: MacWorkerJobType,
  input: MacWorkerJob["input"],
  trace: MacWorkerTraceFields,
  jobId = `${jobType}-${Date.now()}`,
): MacWorkerJob {
  return {
    ...createMacWorkerJob(jobType, input, jobId),
    trace_id: trace.trace_id,
    invocation_event_id: trace.invocation_event_id,
    consumer_event_id: trace.consumer_event_id,
    consumer_subsystem: trace.consumer_subsystem,
    task_id: trace.task_id,
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function boolValue(value: unknown): boolean {
  return value === true;
}

function numberValue(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

export function normalizeMacWorkerResult(value: unknown, fallbackJob: MacWorkerJob): MacWorkerJobResult {
  const record = asRecord(value);
  const result = asRecord(record.result);
  const jobType = isMacWorkerJobType(record.job_type) ? record.job_type : fallbackJob.job_type;
  const now = new Date().toISOString();

  return {
    job_id: stringValue(record.job_id) ?? fallbackJob.job_id,
    job_type: jobType,
    input: asRecord(record.input) as MacWorkerJob["input"],
    node_id: stringValue(record.node_id) ?? fallbackJob.node_id,
    started_at: stringValue(record.started_at) ?? now,
    completed_at: stringValue(record.completed_at) ?? now,
    success: boolValue(record.success),
    result,
    stdout: stringValue(record.stdout) ?? "",
    stderr: stringValue(record.stderr) ?? "",
    error: stringValue(record.error),
    duration_ms: numberValue(record.duration_ms),
    artifacts: stringArray(record.artifacts),
    candidate_files: stringArray(record.candidate_files),
    recommended_checks: stringArray(record.recommended_checks),
    result_envelope_version: stringValue(record.result_envelope_version) ?? MAC_WORKER_RESULT_ENVELOPE_VERSION,
    trace_id: stringValue(record.trace_id) ?? fallbackJob.trace_id,
    invocation_event_id: stringValue(record.invocation_event_id) ?? fallbackJob.invocation_event_id,
    consumer_event_id: stringValue(record.consumer_event_id) ?? fallbackJob.consumer_event_id,
    consumer_subsystem: stringValue(record.consumer_subsystem) ?? fallbackJob.consumer_subsystem,
    task_id: stringValue(record.task_id) ?? fallbackJob.task_id,
  };
}

export function macWorkerCapabilityDescriptor(
  status: MacWorkerCapabilityDescriptor["status"],
  lastHealthCheck: string | null = null,
  allowedWorkspace = process.env.SPIRIT_MACMINI_REPO_PATH?.trim() || "$HOME/spiritos-worker/SpiritOS",
): MacWorkerCapabilityDescriptor {
  return {
    worker: "mac",
    status,
    capabilities: [...macWorkerJobTypes],
    write_capable: true,
    requires_human_first_write: true,
    allowed_workspace: allowedWorkspace,
    job_envelope_version: MAC_WORKER_JOB_ENVELOPE_VERSION,
    result_envelope_version: MAC_WORKER_RESULT_ENVELOPE_VERSION,
    last_health_check: lastHealthCheck,
  };
}

export function summarizeMacWorkerResult(result: MacWorkerJobResult): string {
  if (!result.success) {
    return result.error || result.stderr || "Mac worker job failed";
  }
  const candidateCount = result.candidate_files.length;
  if (candidateCount > 0) {
    return `${result.job_type} returned ${candidateCount} candidate file${candidateCount === 1 ? "" : "s"}`;
  }
  if (typeof result.result?.summary === "string") {
    return result.result.summary;
  }
  return `${result.job_type} completed on ${result.node_id}`;
}

export function macRunSummaryFromResult(result: MacWorkerJobResult | null): MacWorkerRunSummary {
  if (!result) {
    return {
      mac_used: false,
      mac_node_status: "unavailable",
      mac_job_type: null,
      mac_candidate_files: [],
      mac_result_summary: "Mac worker was not called",
      mac_error: null,
      mac_duration_ms: null,
    };
  }

  return {
    mac_used: true,
    mac_node_status: result.success ? "online" : "offline",
    mac_job_type: result.job_type,
    mac_candidate_files: result.candidate_files,
    mac_result_summary: summarizeMacWorkerResult(result),
    mac_error: result.error,
    mac_duration_ms: result.duration_ms,
  };
}
