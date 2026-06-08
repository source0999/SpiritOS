import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";

import type {
  DurableCodingRun,
  DurableCodingRunCreateInput,
  DurableCodingRunPatchInput,
  DurableCodingRunProvenance,
  DurableCodingRunRow,
} from "@/lib/coding/durable-run-types";
import {
  NON_TERMINAL_ROW_STATUSES,
  TERMINAL_RUN_STATUSES,
  appendWriteDebug,
  classifyPatchWrite,
  classifyRowWrite,
  completedRowCount,
  enforceSingleRunningRow,
  terminalWriteAllowed,
} from "@/lib/coding/durable-run-invariants";

type StorePayload = {
  runs: DurableCodingRun[];
};

const SERVER_APPLY_PROOF_STATUS = "/v1/actions/execute-approved:server_apply_proof_recorded";
let mutationQueue: Promise<unknown> = Promise.resolve();

async function withStoreMutation<T>(mutation: () => Promise<T>): Promise<T> {
  const run = mutationQueue.then(mutation, mutation);
  mutationQueue = run.catch(() => undefined);
  return run;
}

function storePath() {
  if (process.env.SPIRIT_CODING_RUNS_STORE) {
    return process.env.SPIRIT_CODING_RUNS_STORE;
  }
  return path.join(process.cwd(), "data", "coding-runs.json");
}

function nowIso() {
  return new Date().toISOString();
}

function emptyRun(input: DurableCodingRunCreateInput): DurableCodingRun {
  const timestamp = nowIso();
  const runId = input.run_id || input.suite_id || `coding-run-${randomUUID()}`;
  return {
    run_id: runId,
    suite_id: input.suite_id || runId,
    created_at: input.created_at || timestamp,
    updated_at: input.updated_at || timestamp,
    suite_started_at: input.suite_started_at ?? timestamp,
    current_prompt_started_at: input.current_prompt_started_at ?? null,
    current_step_started_at: input.current_step_started_at ?? null,
    started_by_surface: "coding",
    lane: "coder",
    benchmark_name: input.benchmark_name || "Coder run",
    requested_count: input.requested_count ?? 1,
    completed_count: input.completed_count ?? 0,
    status: input.status || "pending",
    current_prompt_id: input.current_prompt_id ?? null,
    rows: input.rows || [],
    provider: input.provider || "",
    model: input.model || "",
    provider_call_made: input.provider_call_made ?? false,
    model_called_for_generation: input.model_called_for_generation || "none",
    endpoint_statuses: input.endpoint_statuses || [],
    generated_diff_present: input.generated_diff_present ?? false,
    preview_changed_files: input.preview_changed_files || [],
    applied_changed_files: input.applied_changed_files || [],
    disk_changed_files: input.disk_changed_files || [],
    checks_run: input.checks_run || [],
    checks_result: input.checks_result || "",
    reversal_available: input.reversal_available ?? false,
    reversal_status: input.reversal_status || "none",
    final_summary: input.final_summary || "",
    last_error: input.last_error ?? null,
    reason_code: input.reason_code ?? null,
    frontend_url: input.frontend_url || "https://10.0.0.186:3000/coding",
    proxy_url: input.proxy_url || "https://10.0.0.186:8787",
    owner_kind: input.owner_kind ?? null,
    write_source: input.write_source ?? "create",
    runner_instance_id: input.runner_instance_id ?? null,
    client_instance_id: input.client_instance_id ?? null,
    lease_epoch: input.lease_epoch ?? null,
    last_write_decision: input.last_write_decision ?? "accepted_create",
    write_debug: input.write_debug || [],
    invariant_violations: input.invariant_violations || [],
  };
}

async function readStore(): Promise<StorePayload> {
  try {
    const raw = await readFile(storePath(), "utf8");
    const parsed = JSON.parse(raw) as Partial<StorePayload>;
    return { runs: Array.isArray(parsed.runs) ? parsed.runs : [] };
  } catch {
    return { runs: [] };
  }
}

async function writeStore(payload: StorePayload) {
  const target = storePath();
  await mkdir(path.dirname(target), { recursive: true });
  const tmp = `${target}.${process.pid}.${Date.now()}.${randomUUID()}.tmp`;
  await writeFile(tmp, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  await rename(tmp, target);
}

function sortRuns(runs: DurableCodingRun[]) {
  return [...runs].sort((a, b) => b.updated_at.localeCompare(a.updated_at));
}

function mergeStringLists(
  current: string[] | null | undefined,
  incoming: string[] | null | undefined,
): string[] {
  return Array.from(new Set([...(current ?? []), ...(incoming ?? [])]));
}

const EMPTY_TRIAL_PROVENANCE: DurableCodingRunProvenance = {
  generation_source: "unknown",
  diff_source: "none",
  model_output_classification: "not_classified",
  raw_response_length: 0,
  raw_response_excerpt_safe: "",
  scaffold_used: false,
  scaffold_kind: "",
  fallback_used: false,
  fallback_kind: "",
  parser_repair_used: false,
  bounded_create_used: false,
  known_scaffold_used: false,
  generic_scaffold_used: false,
  model_raw_diff_used: false,
  generated_diff_by_backend: false,
  trial_result_trust_status: "missing_provenance",
};

function normalizeTrialProvenance(
  incoming: Partial<DurableCodingRunProvenance> | null | undefined,
  existing?: DurableCodingRunProvenance,
): DurableCodingRunProvenance {
  const merged = { ...EMPTY_TRIAL_PROVENANCE, ...(existing ?? {}), ...(incoming ?? {}) };
  return {
    ...merged,
    raw_response_length: Number(merged.raw_response_length) || 0,
    scaffold_used: Boolean(merged.scaffold_used),
    fallback_used: Boolean(merged.fallback_used),
    parser_repair_used: Boolean(merged.parser_repair_used),
    bounded_create_used: Boolean(merged.bounded_create_used),
    known_scaffold_used: Boolean(merged.known_scaffold_used),
    generic_scaffold_used: Boolean(merged.generic_scaffold_used),
    model_raw_diff_used: Boolean(merged.model_raw_diff_used),
    generated_diff_by_backend: Boolean(merged.generated_diff_by_backend),
  };
}

function normalizedRowStatus(row: DurableCodingRunRow): DurableCodingRunRow {
  if (
    row.result_label === "RUNNING" &&
    row.status === "completed" &&
    row.applied_changed_files.length === 0 &&
    row.disk_changed_files.length === 0 &&
    !row.reason_code
  ) {
    return { ...row, status: "running" };
  }
  return row;
}

function durableRowRank(row: DurableCodingRunRow): number {
  const normalized = normalizedRowStatus(row);
  if (normalized.result_label === "PASS" || normalized.result_label === "REVERTED") return 50;
  if (normalized.status === "failed" || normalized.result_label === "NEEDS FIX") return 40;
  if (normalized.status === "completed" || normalized.status === "reverted") return 30;
  if (normalized.applied_changed_files.length > 0 || normalized.disk_changed_files.length > 0) return 20;
  if (normalized.status === "running" || normalized.status === "pending") return 10;
  return 0;
}

function normalizeRows(rows: DurableCodingRunRow[]): DurableCodingRunRow[] {
  const byPrompt = new Map<string, DurableCodingRunRow>();
  for (const row of rows.map(normalizedRowStatus)) {
    const existing = byPrompt.get(row.prompt_id);
    if (!existing || durableRowRank(row) >= durableRowRank(existing)) {
      byPrompt.set(row.prompt_id, row);
    }
  }
  return [...byPrompt.values()];
}

function rowsWithTerminalCurrentPrompt(
  current: DurableCodingRun,
  patch: DurableCodingRunPatchInput,
  timestamp: string,
) {
  if (!patch.status || !TERMINAL_RUN_STATUSES.has(patch.status) || patch.rows || !current.current_prompt_id) {
    return patch.rows ?? current.rows;
  }
  const terminalStatus = patch.status;
  return current.rows.map((row) => {
    if (row.prompt_id !== current.current_prompt_id || !NON_TERMINAL_ROW_STATUSES.has(row.status)) {
      return row;
    }
    return {
      ...row,
      status: terminalStatus,
      updated_at: timestamp,
      reason_code: patch.reason_code || patch.last_error || row.reason_code || "run_marked_terminal",
      result_label:
        terminalStatus === "timed_out"
          ? "NEEDS FIX"
          : terminalStatus === "cleared"
            ? "CLEARED"
          : terminalStatus === "completed"
            ? "COMPLETED"
            : terminalStatus.toUpperCase(),
      error_summary: patch.last_error || patch.final_summary || row.error_summary,
    };
  });
}

export async function createCodingRun(input: DurableCodingRunCreateInput = {}) {
  return withStoreMutation(async () => {
    const store = await readStore();
    const timestamp = nowIso();
    const run = appendWriteDebug(emptyRun(input), {
      accepted: true,
      at: timestamp,
      client_instance_id: input.client_instance_id ?? null,
      completed_count_after: input.completed_count ?? 0,
      completed_count_before: null,
      decision: "accepted_create",
      lease_epoch: input.lease_epoch ?? null,
      owner_kind: input.owner_kind ?? "primary_runner",
      prompt_id: input.current_prompt_id ?? null,
      runner_instance_id: input.runner_instance_id ?? null,
      source: "create",
      status_after: input.status ?? "pending",
      status_before: null,
    });
    const nextRuns = [run, ...store.runs.filter((item) => item.run_id !== run.run_id)].slice(0, 50);
    await writeStore({ runs: nextRuns });
    return run;
  });
}

export async function patchCodingRun(runId: string, patch: DurableCodingRunPatchInput) {
  return withStoreMutation(async () => {
    const store = await readStore();
    const index = store.runs.findIndex((run) => run.run_id === runId || run.suite_id === runId);
    if (index < 0) return null;
    const current = store.runs[index];
    const timestamp = nowIso();
    const classified = classifyPatchWrite(patch);
    if (!terminalWriteAllowed(current, classified.source, patch.status)) {
      const rejected = appendWriteDebug(current, {
        accepted: false,
        at: timestamp,
        client_instance_id: patch.client_instance_id ?? null,
        completed_count_after: current.completed_count,
        completed_count_before: current.completed_count,
        decision: "rejected_terminal_reopen",
        lease_epoch: patch.lease_epoch ?? null,
        owner_kind: classified.ownerKind,
        prompt_id: patch.current_prompt_id ?? current.current_prompt_id,
        runner_instance_id: patch.runner_instance_id ?? null,
        source: classified.source,
        status_after: current.status,
        status_before: current.status,
      });
      store.runs[index] = rejected;
      await writeStore({ runs: sortRuns(store.runs).slice(0, 50) });
      return rejected;
    }
    const rawPatchRows = rowsWithTerminalCurrentPrompt(current, patch, timestamp);
    const patchRows =
      TERMINAL_RUN_STATUSES.has(current.status) && patch.status !== "cleared" && patch.status !== "cancelled"
        ? rawPatchRows.filter((row) => !NON_TERMINAL_ROW_STATUSES.has(row.status))
        : rawPatchRows;
    const mergedRows = patch.rows ? [...current.rows, ...patchRows] : patchRows;
    const singleRunning = enforceSingleRunningRow(
      normalizeRows(mergedRows),
      patch.current_prompt_id ?? current.current_prompt_id,
      timestamp,
    );
    const updated: DurableCodingRun = {
      ...current,
      ...patch,
      run_id: current.run_id,
      suite_id: current.suite_id,
      created_at: current.created_at,
      reversal_status: patch.status === "cleared" ? "none" : (patch.reversal_status ?? current.reversal_status),
      rows: singleRunning.rows,
      updated_at: timestamp,
    };
    const patchedRunningRow = updated.rows.find((row) => NON_TERMINAL_ROW_STATUSES.has(row.status));
    if (patchedRunningRow && updated.current_prompt_id !== patchedRunningRow.prompt_id) {
      updated.current_prompt_id = patchedRunningRow.prompt_id;
      updated.current_prompt_started_at = patchedRunningRow.started_at;
      updated.current_step_started_at = timestamp;
    }
    updated.completed_count = Math.max(
      current.completed_count,
      patch.completed_count ?? 0,
      patch.rows || (patch.status && TERMINAL_RUN_STATUSES.has(patch.status)) ? completedRowCount(updated.rows) : 0,
    );
    const hasInFlightRow = updated.rows.some((row) => NON_TERMINAL_ROW_STATUSES.has(row.status));
    let decision = patch.status === "cleared" ? "accepted_clear_wins" : "accepted_run_patch";
    if (singleRunning.changed) decision = `accepted_duplicate_running_demoted:${singleRunning.demoted.join(",")}`;
    if ((patch.completed_count ?? current.completed_count) < current.completed_count) {
      decision = "accepted_progress_regression_blocked";
    }
    if (
      patch.status &&
      TERMINAL_RUN_STATUSES.has(patch.status) &&
      patch.status !== "cleared" &&
      patch.status !== "cancelled" &&
      hasInFlightRow &&
      updated.completed_count < updated.requested_count &&
      (current.status === "running" || current.status === "pending")
    ) {
      updated.status = current.status;
      updated.final_summary = current.final_summary || updated.final_summary;
      updated.reason_code = current.reason_code ?? updated.reason_code;
      updated.last_error = current.last_error ?? updated.last_error;
      decision = "accepted_terminal_patch_deferred_for_inflight_prompt";
    }
    if (
      TERMINAL_RUN_STATUSES.has(current.status) &&
      current.status !== "cleared" &&
      current.status !== "cancelled" &&
      (patch.status === "running" || patch.status === "pending")
    ) {
      updated.status = current.status;
      updated.completed_count = Math.max(current.completed_count, completedRowCount(updated.rows));
      updated.current_prompt_id = current.current_prompt_id;
      updated.current_prompt_started_at = current.current_prompt_started_at;
      updated.current_step_started_at = current.current_step_started_at;
      updated.final_summary = current.final_summary || updated.final_summary;
      updated.reason_code = current.reason_code ?? updated.reason_code;
      updated.last_error = current.last_error ?? updated.last_error;
      decision = "accepted_terminal_reopen_blocked";
    }
    if (patch.status === "completed" && updated.completed_count < updated.requested_count) {
      updated.status = "failed";
      updated.reason_code = updated.reason_code || "completed_before_requested_count_blocked";
      updated.last_error =
        updated.last_error || `Completed terminal patch blocked at ${updated.completed_count}/${updated.requested_count}.`;
      updated.final_summary = updated.final_summary || "Completed terminal patch blocked before requested count.";
      decision = "accepted_completed_terminal_blocked_before_full_count";
    }
    if (patch.status === "cleared") {
      updated.current_prompt_id = null;
      updated.current_prompt_started_at = null;
      updated.current_step_started_at = null;
      updated.completed_count = Math.max(updated.completed_count, completedRowCount(updated.rows));
    }
    const withDebug = appendWriteDebug(updated, {
      accepted: true,
      at: timestamp,
      client_instance_id: patch.client_instance_id ?? null,
      completed_count_after: updated.completed_count,
      completed_count_before: current.completed_count,
      decision,
      lease_epoch: patch.lease_epoch ?? null,
      owner_kind: classified.ownerKind,
      prompt_id: patch.current_prompt_id ?? current.current_prompt_id,
      runner_instance_id: patch.runner_instance_id ?? null,
      source: classified.source,
      status_after: updated.status,
      status_before: current.status,
    });
    store.runs[index] = withDebug;
    await writeStore({ runs: sortRuns(store.runs).slice(0, 50) });
    return withDebug;
  });
}

export async function upsertCodingRunRow(runId: string, promptId: string, row: Partial<DurableCodingRunRow>) {
  return withStoreMutation(async () => {
    const store = await readStore();
    const run = store.runs.find((item) => item.run_id === runId || item.suite_id === runId);
    if (!run) return null;
    const timestamp = nowIso();
    const existing = run.rows.find((item) => item.prompt_id === promptId);
    const classified = classifyRowWrite(row);
    const existingHasServerApplyProof = Boolean(
      existing?.endpoint_statuses?.some((status) => status.includes(SERVER_APPLY_PROOF_STATUS)),
    );
    const incomingHasServerApplyProof = Boolean(
      row.endpoint_statuses?.some((status) => status.includes(SERVER_APPLY_PROOF_STATUS)),
    );
    const preserveServerApplyProof =
      existingHasServerApplyProof &&
      !incomingHasServerApplyProof &&
      ((row.status === "running" || row.status === "pending") ||
        row.reason_code === "execute_approved_body_read_missing" ||
        row.reason_code === "apply_ack_no_disk_proof" ||
        row.reason_code === "post_apply_verification_missing");
    const nextRow: DurableCodingRunRow = {
      prompt_id: promptId,
      run_id: typeof row.run_id === "string" ? row.run_id : existing?.run_id,
      prompt_text: row.prompt_text || existing?.prompt_text || "",
      prompt_excerpt: row.prompt_excerpt || existing?.prompt_excerpt || "",
      status: preserveServerApplyProof ? existing?.status ?? "completed" : row.status || existing?.status || "running",
      started_at: row.started_at ?? existing?.started_at ?? timestamp,
      updated_at: timestamp,
      provider_call_made: row.provider_call_made ?? existing?.provider_call_made ?? false,
      model_called_for_generation: row.model_called_for_generation || existing?.model_called_for_generation || "none",
      endpoint_statuses: mergeStringLists(existing?.endpoint_statuses, row.endpoint_statuses),
      reason_code: preserveServerApplyProof ? existing?.reason_code ?? "" : row.reason_code || existing?.reason_code || "",
      generated_diff_present: row.generated_diff_present ?? existing?.generated_diff_present ?? false,
      preview_changed_files: mergeStringLists(existing?.preview_changed_files, row.preview_changed_files),
      applied_changed_files: mergeStringLists(existing?.applied_changed_files, row.applied_changed_files),
      disk_changed_files: mergeStringLists(existing?.disk_changed_files, row.disk_changed_files),
      checks_run: mergeStringLists(existing?.checks_run, row.checks_run),
      checks_result: preserveServerApplyProof ? existing?.checks_result ?? "" : row.checks_result || existing?.checks_result || "",
      reversal_available: preserveServerApplyProof ? existing?.reversal_available ?? true : row.reversal_available ?? existing?.reversal_available ?? false,
      reversal_status: preserveServerApplyProof ? existing?.reversal_status ?? "available" : row.reversal_status || existing?.reversal_status || "none",
      reverse_diff: typeof row.reverse_diff === "string" ? row.reverse_diff : existing?.reverse_diff,
      result_label: preserveServerApplyProof ? existing?.result_label ?? "PASS" : row.result_label || existing?.result_label || "",
      error_summary: preserveServerApplyProof ? existing?.error_summary ?? "" : row.error_summary || existing?.error_summary || "",
      provenance: normalizeTrialProvenance(row.provenance, existing?.provenance),
      step_instrumentation: {
        ...(existing?.step_instrumentation ?? {}),
        ...(row.step_instrumentation ?? {}),
        ...(preserveServerApplyProof ? { last_progress_reason_code: "server_apply_proof_recorded" } : {}),
      },
      owner_kind: row.owner_kind ?? existing?.owner_kind ?? classified.ownerKind,
      write_source: row.write_source ?? existing?.write_source ?? classified.source,
      runner_instance_id: row.runner_instance_id ?? existing?.runner_instance_id ?? null,
      client_instance_id: row.client_instance_id ?? existing?.client_instance_id ?? null,
      lease_epoch: row.lease_epoch ?? existing?.lease_epoch ?? null,
    };
    if (
      TERMINAL_RUN_STATUSES.has(run.status) &&
      run.status !== "cleared" &&
      run.status !== "cancelled" &&
      NON_TERMINAL_ROW_STATUSES.has(nextRow.status)
    ) {
      const rejected = appendWriteDebug(run, {
        accepted: false,
        at: timestamp,
        client_instance_id: row.client_instance_id ?? null,
        completed_count_after: run.completed_count,
        completed_count_before: run.completed_count,
        decision: "rejected_terminal_row_reopen",
        lease_epoch: row.lease_epoch ?? null,
        owner_kind: classified.ownerKind,
        prompt_id: promptId,
        runner_instance_id: row.runner_instance_id ?? null,
        source: classified.source,
        status_after: run.status,
        status_before: run.status,
      });
      store.runs = sortRuns(store.runs.map((item) => (item.run_id === run.run_id ? rejected : item)));
      await writeStore(store);
      return rejected;
    }
    const singleRunning = enforceSingleRunningRow(
      normalizeRows([...run.rows.filter((item) => item.prompt_id !== promptId), nextRow]),
      NON_TERMINAL_ROW_STATUSES.has(nextRow.status) ? promptId : run.current_prompt_id,
      timestamp,
    );
    run.rows = singleRunning.rows;
    run.completed_count = completedRowCount(run.rows);
    const currentRow = run.current_prompt_id
      ? run.rows.find((item) => item.prompt_id === run.current_prompt_id)
      : null;
    const nextRowIsInFlight = NON_TERMINAL_ROW_STATUSES.has(nextRow.status);
    const currentRowIsInFlight = Boolean(currentRow && NON_TERMINAL_ROW_STATUSES.has(currentRow.status));
    const activeRunningRow = run.rows.find((item) => NON_TERMINAL_ROW_STATUSES.has(item.status));
    if (nextRowIsInFlight) {
      run.current_prompt_id = promptId;
      run.current_prompt_started_at = nextRow.started_at;
      run.current_step_started_at = timestamp;
    } else if (run.current_prompt_id === promptId && activeRunningRow) {
      run.current_prompt_id = activeRunningRow.prompt_id;
      run.current_prompt_started_at = activeRunningRow.started_at;
      run.current_step_started_at = timestamp;
    } else if (run.current_prompt_id === promptId || !currentRowIsInFlight) {
      run.current_prompt_id = promptId;
      run.current_prompt_started_at = nextRow.started_at;
      run.current_step_started_at = timestamp;
    }
    run.updated_at = timestamp;
    const withDebug = appendWriteDebug(run, {
      accepted: true,
      at: timestamp,
      client_instance_id: row.client_instance_id ?? null,
      completed_count_after: run.completed_count,
      completed_count_before: completedRowCount(run.rows.filter((item) => item.prompt_id !== promptId)),
      decision: singleRunning.changed
        ? `accepted_duplicate_running_demoted:${singleRunning.demoted.join(",")}`
        : "accepted_row_upsert",
      lease_epoch: row.lease_epoch ?? null,
      owner_kind: classified.ownerKind,
      prompt_id: promptId,
      runner_instance_id: row.runner_instance_id ?? null,
      source: classified.source,
      status_after: run.status,
      status_before: run.status,
    });
    store.runs = store.runs.map((item) => (item.run_id === run.run_id ? withDebug : item));
    store.runs = sortRuns(store.runs);
    await writeStore(store);
    return withDebug;
  });
}

export async function getCodingRun(runId: string) {
  const store = await readStore();
  return store.runs.find((run) => run.run_id === runId || run.suite_id === runId) ?? null;
}

export async function listRecentCodingRuns(limit = 10) {
  const store = await readStore();
  return sortRuns(store.runs).slice(0, Math.min(Math.max(limit, 1), 50));
}

export async function getActiveCodingRun() {
  const runs = await listRecentCodingRuns(50);
  return runs.find((run) => !TERMINAL_RUN_STATUSES.has(run.status)) ?? null;
}
