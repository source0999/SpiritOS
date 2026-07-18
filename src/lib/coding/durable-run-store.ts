import { createHash } from "node:crypto";

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import type {
  DurableCodingRun,
  DurableCodingRunCreateInput,
  DurableCodingRunPatchInput,
  DurableCodingRunRow,
  DurableCodingRunStatus,
} from "@/lib/coding/durable-run-types";

/**
 * R1 ownership boundary
 * ---------------------
 *
 * This module keeps its historical import path because the Coding UI and the
 * execute-approved compatibility wrapper still import it.  It is no longer a
 * store: it cannot read or write data/coding-runs.json.  Every returned field
 * is a bounded projection of the Source Proxy long-running-task SQLite state.
 */

const MAX_PROJECTED_RUNS = 50;
const MAX_PROJECTED_LIST_ITEMS = 50;
const MAX_PROJECTED_TEXT = 4_000;
const SOURCE_PROXY_PROJECTION_SCHEMA = "source-proxy-coding-run-projection/v1" as const;
const REQUIRED_ORCHESTRATOR_LANES = [
  "context-broker",
  "planner",
  "coder",
  "reviewer",
  "verifier",
  "anti-cheat",
  "repair",
  "evidence-recorder",
] as const;
const REQUIRED_PARTICIPANT_ROLES = [
  "coding-executor",
  "coding-reviewer",
  "coding-verifier",
  "coding-anti-cheat",
  "evidence-recorder",
] as const;
const TERMINAL_STATUSES = new Set<DurableCodingRunStatus>([
  "completed",
  "failed",
  "timed_out",
  "cancelled",
  "cleared",
  "reverted",
]);

type JsonRecord = Record<string, unknown>;

export class CodingRunProjectionError extends Error {
  readonly reasonCode: string;

  constructor(reasonCode: string, message = reasonCode) {
    super(message);
    this.name = "CodingRunProjectionError";
    this.reasonCode = reasonCode;
  }
}

export class NonAuthoritativeCodingRunMutationError extends Error {
  readonly reasonCode = "next_coding_run_mutation_forbidden";

  constructor(operation: string) {
    super(`Next coding-run ${operation} is forbidden; Source Proxy owns durable task truth.`);
    this.name = "NonAuthoritativeCodingRunMutationError";
  }
}

function asRecord(value: unknown): JsonRecord {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as JsonRecord)
    : {};
}

function asRecords(value: unknown): JsonRecord[] {
  return Array.isArray(value) ? value.map(asRecord).filter((item) => Object.keys(item).length > 0) : [];
}

function boundedText(value: unknown, maxLength = MAX_PROJECTED_TEXT): string {
  return typeof value === "string" ? value.slice(0, maxLength) : "";
}

function boundedStrings(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const strings = value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.slice(0, 500))
    .filter(Boolean);
  return Array.from(new Set(strings)).slice(0, MAX_PROJECTED_LIST_ITEMS);
}

function firstNonEmptyStrings(...values: unknown[]): string[] {
  for (const value of values) {
    const bounded = boundedStrings(value);
    if (bounded.length > 0) return bounded;
  }
  return [];
}

function boundedLimit(limit: number): number {
  if (!Number.isFinite(limit)) return 10;
  return Math.min(Math.max(Math.floor(limit), 1), MAX_PROJECTED_RUNS);
}

function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value) ?? "null";
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  const record = value as JsonRecord;
  return `{${Object.keys(record)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalJson(record[key])}`)
    .join(",")}}`;
}

function sha256Json(value: unknown): string {
  return `sha256:${createHash("sha256").update(canonicalJson(value), "utf8").digest("hex")}`;
}

function sourceTaskFromEnvelope(payload: unknown): JsonRecord | null {
  const envelope = asRecord(payload);
  const task = asRecord(envelope.task);
  return typeof task.id === "string" && task.id.trim() ? task : null;
}

function terminalEvidenceReasons(task: JsonRecord): string[] {
  const snapshot = asRecord(task.ast_snapshot);
  const verification = Object.keys(asRecord(task.post_apply_verification)).length
    ? asRecord(task.post_apply_verification)
    : asRecord(snapshot.post_apply_verification);
  const orchestrator = asRecord(snapshot.coding_orchestrator);
  const laneStates = asRecord(orchestrator.lane_states);
  const approval = asRecord(snapshot.campaign_2_approval);
  const executionEvidence = asRecord(snapshot.approved_execution_evidence);
  const productionProof = asRecord(snapshot.coding_production_proof);
  const artifact = asRecord(snapshot.coding_artifact);
  const participantRecords = asRecords(snapshot.coding_participant_records);
  const runtimeOutputs = asRecords(snapshot.coding_runtime_outputs);
  const runtimeConsumptions = asRecords(snapshot.coding_runtime_consumptions);
  const reasons: string[] = [];

  if (task.status !== "completed") reasons.push("source_task_not_completed");
  if (verification.status !== "verified") reasons.push("post_apply_verification_not_verified");
  if (approval.state !== "consumed") reasons.push("approval_not_consumed");
  if (executionEvidence.final_truth_status !== "GO" || executionEvidence.commit_safe !== true) {
    reasons.push("final_go_evidence_missing");
  }
  const proofSha256 = boundedText(productionProof.proof_sha256, 80);
  const proofBody = { ...productionProof };
  delete proofBody.proof_sha256;
  if (
    executionEvidence.terminal_proof_eligible !== true ||
    productionProof.schema_version !== "coding.production-proof/v1" ||
    productionProof.terminal_proof_eligible !== true ||
    productionProof.task_id !== task.id ||
    productionProof.run_id !== orchestrator.run_id ||
    productionProof.artifact_sha256 !== artifact.artifact_sha256 ||
    productionProof.approval_id !== approval.approval_id ||
    !/^sha256:[0-9a-f]{64}$/.test(proofSha256) ||
    executionEvidence.production_proof_sha256 !== proofSha256 ||
    sha256Json(proofBody) !== proofSha256
  ) {
    reasons.push("terminal_production_proof_invalid");
  }
  if (orchestrator.authoritative !== true || orchestrator.schema_version !== "coding-orchestrator/v2") {
    reasons.push("authoritative_orchestrator_state_missing");
  }
  for (const lane of REQUIRED_ORCHESTRATOR_LANES) {
    const expected = lane === "repair" ? new Set(["completed", "skipped"]) : new Set(["completed"]);
    if (!expected.has(String(laneStates[lane] ?? ""))) reasons.push(`lane_not_complete:${lane}`);
  }

  const participantsByRole = new Map(participantRecords.map((record) => [String(record.role ?? ""), record]));
  for (const role of REQUIRED_PARTICIPANT_ROLES) {
    const record = participantsByRole.get(role);
    if (
      !record ||
      record.passed !== true ||
      !boundedText(record.invocation_id) ||
      !boundedText(record.output_id) ||
      !boundedText(record.consumer_acknowledgement_id)
    ) {
      reasons.push(`participant_evidence_missing:${role}`);
    }
  }

  const outputIds = new Set(runtimeOutputs.map((record) => boundedText(record.output_id)).filter(Boolean));
  const consumedOutputIds = new Set(
    runtimeConsumptions.map((record) => boundedText(record.output_id)).filter(Boolean),
  );
  if (outputIds.size === 0 || [...outputIds].some((outputId) => !consumedOutputIds.has(outputId))) {
    reasons.push("runtime_output_consumption_incomplete");
  }

  return reasons;
}

function projectedStatus(sourceStatus: string, terminalSuccess: boolean): DurableCodingRunStatus {
  if (terminalSuccess) return "completed";
  if (sourceStatus === "cancelled") return "cancelled";
  if (sourceStatus === "reverted") return "reverted";
  if (sourceStatus === "timed_out") return "timed_out";
  if (sourceStatus === "cleared") return "cleared";
  if (sourceStatus === "queued") return "pending";
  if (
    sourceStatus === "needs_approval" ||
    sourceStatus === "waiting_for_operator_browser" ||
    sourceStatus === "applied_needs_verification" ||
    sourceStatus === "verification_passed_pending_participants"
  ) {
    return sourceStatus === "needs_approval" ? "needs_approval" : "running";
  }
  if (
    sourceStatus === "completed" ||
    sourceStatus.includes("failed") ||
    sourceStatus.includes("blocked") ||
    sourceStatus === "needs_context" ||
    sourceStatus === "coder_config_blocked"
  ) {
    return "failed";
  }
  return "running";
}

function taskReasonCode(task: JsonRecord, sourceStatus: string, terminalSuccess: boolean): string | null {
  if (terminalSuccess) return null;
  if (sourceStatus === "completed") return "backend_terminal_evidence_incomplete";
  if (sourceStatus === "applied_needs_verification") return "post_apply_verification_required";
  if (sourceStatus === "verification_passed_pending_participants") {
    return "independent_participants_pending";
  }
  const diagnostic = asRecord(asRecord(task.ast_snapshot).latest_approval_binding_diagnostic);
  return boundedText(diagnostic.reason_code, 160) || boundedText(task.reason_code, 160) || sourceStatus || null;
}

/** Convert one persisted Source Proxy task envelope into a bounded UI view. */
export function projectSourceProxyTaskEnvelope(payload: unknown): DurableCodingRun | null {
  const task = sourceTaskFromEnvelope(payload);
  if (!task) return null;

  const taskId = boundedText(task.id, 200);
  const sourceStatus = boundedText(task.status, 160) || "unknown";
  const snapshot = asRecord(task.ast_snapshot);
  const orchestrator = asRecord(snapshot.coding_orchestrator);
  const verification = Object.keys(asRecord(task.post_apply_verification)).length
    ? asRecord(task.post_apply_verification)
    : asRecord(snapshot.post_apply_verification);
  const executionEvidence = asRecord(snapshot.approved_execution_evidence);
  const audit = asRecord(executionEvidence.audit);
  const artifact = asRecord(snapshot.coding_artifact);
  const evidenceReasons = terminalEvidenceReasons(task);
  const terminalSuccess = evidenceReasons.length === 0;
  const status = projectedStatus(sourceStatus, terminalSuccess);
  const changedFiles = firstNonEmptyStrings(
    audit.changed_files,
    verification.changed_files,
    executionEvidence.changed_files,
  );
  const checks = asRecords(verification.checks)
    .map((check) => boundedText(check.id, 200) || boundedText(check.command, 200))
    .filter(Boolean)
    .slice(0, MAX_PROJECTED_LIST_ITEMS);
  const verificationStatus = boundedText(verification.status, 160) || "not_recorded";
  const approvalState = boundedText(asRecord(snapshot.campaign_2_approval).state, 160) || "not_recorded";
  const orchestratorComplete = evidenceReasons.every(
    (reason) => !reason.startsWith("lane_not_complete:") && reason !== "authoritative_orchestrator_state_missing",
  );
  const runId = boundedText(orchestrator.run_id, 200) || taskId;
  const createdAt = boundedText(task.created_at, 80) || new Date(0).toISOString();
  const updatedAt = boundedText(task.updated_at, 80) || createdAt;
  const description = boundedText(task.description, 500) || `Coding task ${taskId}`;
  const reasonCode = taskReasonCode(task, sourceStatus, terminalSuccess);
  const isApplied = changedFiles.length > 0 && !["pending", "needs_approval"].includes(status);
  const rowStatus: DurableCodingRunStatus = terminalSuccess
    ? "completed"
    : status === "failed" || status === "cancelled" || status === "timed_out"
      ? status
      : status === "pending"
        ? "pending"
        : "running";
  const resultLabel = terminalSuccess ? "PASS" : status === "failed" ? "NEEDS FIX" : "PENDING";
  const endpointStatuses = [
    `source-proxy:task-status:${sourceStatus}`,
    `source-proxy:verification:${verificationStatus}`,
    `source-proxy:approval:${approvalState}`,
    `source-proxy:orchestrator:${orchestratorComplete ? "complete" : "incomplete"}`,
  ];
  const row: DurableCodingRunRow = {
    prompt_id: taskId,
    run_id: taskId,
    prompt_text: description,
    prompt_excerpt: description.slice(0, 220),
    status: rowStatus,
    started_at: createdAt,
    updated_at: updatedAt,
    provider_call_made: Boolean(artifact.provider || artifact.model),
    model_called_for_generation: boundedText(artifact.model, 200) || "not_recorded",
    endpoint_statuses: endpointStatuses,
    reason_code: reasonCode ?? "",
    generated_diff_present: changedFiles.length > 0,
    preview_changed_files: changedFiles,
    applied_changed_files: isApplied ? changedFiles : [],
    disk_changed_files: isApplied ? changedFiles : [],
    checks_run: checks,
    checks_result: verificationStatus,
    reversal_available: Boolean(verification.backup_manifest_sha256 || verification.backup_audit_present),
    reversal_status: Boolean(verification.backup_manifest_sha256 || verification.backup_audit_present)
      ? "available"
      : "not_recorded",
    result_label: resultLabel,
    error_summary: status === "failed" ? boundedText(task.next_action, 500) || reasonCode || "" : "",
    owner_kind: "observer",
    write_source: "unknown",
  };

  return {
    run_id: runId,
    suite_id: taskId,
    created_at: createdAt,
    updated_at: updatedAt,
    suite_started_at: createdAt,
    current_prompt_started_at: status === "running" ? createdAt : null,
    current_step_started_at: status === "running" ? updatedAt : null,
    started_by_surface: "coding",
    lane: "coder",
    benchmark_name: description.slice(0, 160),
    requested_count: 1,
    completed_count: terminalSuccess ? 1 : 0,
    status,
    current_prompt_id: TERMINAL_STATUSES.has(status) ? null : taskId,
    rows: [row],
    provider: boundedText(artifact.provider, 200),
    model: boundedText(artifact.model, 200),
    provider_call_made: row.provider_call_made,
    model_called_for_generation: row.model_called_for_generation,
    endpoint_statuses: endpointStatuses,
    generated_diff_present: changedFiles.length > 0,
    preview_changed_files: changedFiles,
    applied_changed_files: isApplied ? changedFiles : [],
    disk_changed_files: isApplied ? changedFiles : [],
    checks_run: checks,
    checks_result: verificationStatus,
    reversal_available: row.reversal_available,
    reversal_status: row.reversal_status,
    final_summary: boundedText(orchestrator.summary, 1_000) || boundedText(task.next_action, 1_000),
    last_error: status === "failed" ? boundedText(task.next_action, 1_000) || reasonCode : null,
    reason_code: reasonCode,
    frontend_url: "/coding",
    proxy_url: "source-proxy",
    owner_kind: "observer",
    write_source: "unknown",
    runner_instance_id: null,
    client_instance_id: null,
    lease_epoch: null,
    last_write_decision: "authoritative_source_proxy_projection",
    write_debug: [],
    invariant_violations: terminalSuccess ? [] : evidenceReasons.slice(0, MAX_PROJECTED_LIST_ITEMS),
    backend_authority: {
      schema_version: SOURCE_PROXY_PROJECTION_SCHEMA,
      owner: "source_proxy",
      store: "long_running_tasks_sqlite",
      projection: "read_only",
      source_task_id: taskId,
      source_status: sourceStatus,
      terminal_success: terminalSuccess,
      terminal_evidence_reasons: evidenceReasons.slice(0, MAX_PROJECTED_LIST_ITEMS),
    },
  };
}

async function responseJson(
  response: Awaited<ReturnType<typeof sourceProxyFetch>>,
  reasonCode: string,
): Promise<unknown> {
  try {
    return await response.json();
  } catch (error) {
    throw new CodingRunProjectionError(
      reasonCode,
      error instanceof Error ? error.message : "Source Proxy returned invalid JSON.",
    );
  }
}

async function fetchTaskById(taskId: string): Promise<DurableCodingRun | null> {
  const response = await sourceProxyFetch(`/v1/tasks/long-running/${encodeURIComponent(taskId)}`, {
    cache: "no-store",
    headers: { accept: "application/json" },
    method: "GET",
  });
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new CodingRunProjectionError(
      "source_proxy_coding_run_read_failed",
      `Source Proxy coding-run read failed with HTTP ${response.status}.`,
    );
  }
  const projected = projectSourceProxyTaskEnvelope(
    await responseJson(response, "source_proxy_coding_run_payload_invalid"),
  );
  if (!projected) {
    throw new CodingRunProjectionError("source_proxy_coding_run_payload_invalid");
  }
  return projected;
}

export async function getCodingRun(runId: string): Promise<DurableCodingRun | null> {
  const normalized = runId.trim();
  if (!normalized) return null;
  const direct = await fetchTaskById(normalized);
  if (direct) return direct;
  const runs = await listRecentCodingRuns(MAX_PROJECTED_RUNS);
  return runs.find((run) => run.run_id === normalized || run.suite_id === normalized) ?? null;
}

export async function listRecentCodingRuns(limit = 10): Promise<DurableCodingRun[]> {
  const bounded = boundedLimit(limit);
  const response = await sourceProxyFetch(
    `/v1/tasks/long-running?include_completed=true&limit=${bounded}`,
    { cache: "no-store", headers: { accept: "application/json" }, method: "GET" },
  );
  if (!response.ok) {
    throw new CodingRunProjectionError(
      "source_proxy_coding_run_list_failed",
      `Source Proxy coding-run list failed with HTTP ${response.status}.`,
    );
  }
  const payload = asRecord(await responseJson(response, "source_proxy_coding_run_list_payload_invalid"));
  if (!Array.isArray(payload.tasks)) {
    throw new CodingRunProjectionError("source_proxy_coding_run_list_payload_invalid");
  }
  const taskIds = Array.from(
    new Set(
      payload.tasks
        .map((item) => boundedText(asRecord(item).task_id, 200))
        .filter(Boolean),
    ),
  ).slice(0, bounded);
  const runs = await Promise.all(taskIds.map(fetchTaskById));
  return runs
    .filter((run): run is DurableCodingRun => run !== null)
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))
    .slice(0, bounded);
}

export async function getActiveCodingRun(): Promise<DurableCodingRun | null> {
  const runs = await listRecentCodingRuns(MAX_PROJECTED_RUNS);
  return runs.find((run) => !TERMINAL_STATUSES.has(run.status)) ?? null;
}

/** No local run may be created; callers must create a Source Proxy task. */
export async function createCodingRun(_input: DurableCodingRunCreateInput = {}): Promise<never> {
  void _input;
  throw new NonAuthoritativeCodingRunMutationError("create");
}

/**
 * Compatibility read for the execute-approved wrapper.  The patch is
 * intentionally ignored and cannot alter, promote, or complete backend truth.
 */
export async function patchCodingRun(
  runId: string,
  _patch: DurableCodingRunPatchInput,
): Promise<DurableCodingRun | null> {
  void _patch;
  return getCodingRun(runId);
}

/**
 * Compatibility read for the execute-approved wrapper.  A client-supplied
 * PASS/completed row is discarded; only the Source Proxy projection returns.
 */
export async function upsertCodingRunRow(
  runId: string,
  _promptId: string,
  _row: Partial<DurableCodingRunRow>,
): Promise<DurableCodingRun | null> {
  void _promptId;
  void _row;
  return getCodingRun(runId);
}
