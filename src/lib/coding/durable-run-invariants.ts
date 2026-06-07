import type {
  DurableCodingRun,
  DurableCodingRunRow,
  DurableCodingRunStatus,
  DurableCodingRunWriteDebugEntry,
  DurableCodingRunWriteSource,
  DurableCodingRunOwnerKind,
} from "@/lib/coding/durable-run-types";

export const TERMINAL_RUN_STATUSES = new Set<DurableCodingRunStatus>([
  "completed",
  "failed",
  "timed_out",
  "cancelled",
  "cleared",
  "reverted",
]);

export const NON_TERMINAL_ROW_STATUSES = new Set<DurableCodingRunStatus>(["pending", "running"]);

const CONTROL_WRITE_SOURCES = new Set<DurableCodingRunWriteSource>(["clear", "stop"]);

export function promptOrdinal(promptId: string | null | undefined): number | null {
  const match = typeof promptId === "string" ? /(?:^|-)0*(\d+)$/.exec(promptId) : null;
  return match ? Number(match[1]) : null;
}

export function isTerminalRunStatus(status: DurableCodingRunStatus | null | undefined) {
  return Boolean(status && TERMINAL_RUN_STATUSES.has(status));
}

export function isNonTerminalRowStatus(status: DurableCodingRunStatus | null | undefined) {
  return Boolean(status && NON_TERMINAL_ROW_STATUSES.has(status));
}

export function completedRowCount(rows: DurableCodingRunRow[]): number {
  return rows.filter((row) => !isNonTerminalRowStatus(row.status) && row.result_label !== "RUNNING").length;
}

export function durableRunInvariantViolations(run: DurableCodingRun): string[] {
  const violations: string[] = [];
  const runningRows = run.rows.filter((row) => isNonTerminalRowStatus(row.status));
  if (runningRows.length > 1) {
    violations.push(`multiple_running_rows:${runningRows.map((row) => row.prompt_id).join(",")}`);
  }
  if (run.completed_count < completedRowCount(run.rows)) {
    violations.push(`completed_count_below_rows:${run.completed_count}<${completedRowCount(run.rows)}`);
  }
  if (run.completed_count > run.requested_count) {
    violations.push(`completed_count_above_requested:${run.completed_count}>${run.requested_count}`);
  }
  if (isTerminalRunStatus(run.status) && run.status !== "cleared" && run.status !== "cancelled" && runningRows.length > 0) {
    violations.push(`terminal_run_has_running_row:${run.status}:${runningRows.map((row) => row.prompt_id).join(",")}`);
  }
  if (run.status === "completed" && run.completed_count < run.requested_count) {
    violations.push(`completed_status_before_full_count:${run.completed_count}/${run.requested_count}`);
  }
  if (run.status === "cleared" && run.current_prompt_id) {
    violations.push(`cleared_run_keeps_current_prompt:${run.current_prompt_id}`);
  }
  const currentRunning = run.current_prompt_id
    ? runningRows.find((row) => row.prompt_id === run.current_prompt_id)
    : null;
  if (runningRows.length === 1 && !currentRunning) {
    violations.push(`current_prompt_not_running_row:${run.current_prompt_id ?? "none"}!=${runningRows[0].prompt_id}`);
  }
  return violations;
}

export function enforceSingleRunningRow(
  rows: DurableCodingRunRow[],
  keepPromptId: string | null | undefined,
  timestamp: string,
): { rows: DurableCodingRunRow[]; changed: boolean; demoted: string[] } {
  const runningRows = rows.filter((row) => isNonTerminalRowStatus(row.status));
  if (runningRows.length <= 1) return { rows, changed: false, demoted: [] };
  const keep =
    (keepPromptId && runningRows.find((row) => row.prompt_id === keepPromptId)) ||
    [...runningRows].sort((a, b) => {
      const ordinalA = promptOrdinal(a.prompt_id) ?? 0;
      const ordinalB = promptOrdinal(b.prompt_id) ?? 0;
      if (ordinalA !== ordinalB) return ordinalB - ordinalA;
      return b.updated_at.localeCompare(a.updated_at);
    })[0];
  const demoted: string[] = [];
  return {
    changed: true,
    demoted,
    rows: rows.map((row) => {
      if (!isNonTerminalRowStatus(row.status) || row.prompt_id === keep.prompt_id) return row;
      demoted.push(row.prompt_id);
      return {
        ...row,
        status: "failed",
        updated_at: timestamp,
        reason_code: row.reason_code || "rejected_duplicate_running_row",
        result_label: row.result_label === "RUNNING" ? "NEEDS FIX" : row.result_label,
        error_summary: row.error_summary || `Demoted because ${keep.prompt_id} is the active running row.`,
      };
    }),
  };
}

export function classifyPatchWrite(
  patch: {
    status?: DurableCodingRunStatus;
    owner_kind?: DurableCodingRunOwnerKind | null;
    write_source?: DurableCodingRunWriteSource | null;
    reason_code?: string | null;
    rows?: DurableCodingRunRow[];
  },
): { ownerKind: DurableCodingRunOwnerKind; source: DurableCodingRunWriteSource } {
  if (patch.owner_kind || patch.write_source) {
    return {
      ownerKind: patch.owner_kind ?? "unknown",
      source: patch.write_source ?? "unknown",
    };
  }
  if (patch.status === "cleared") return { ownerKind: "clear_action", source: "clear" };
  if (patch.status === "cancelled" || patch.reason_code === "user_clicked_stop_suite") {
    return { ownerKind: "stop_action", source: "stop" };
  }
  if (patch.reason_code?.includes("stale") || patch.reason_code?.includes("apply_ack")) {
    return { ownerKind: "stale_recovery", source: "stale_guard" };
  }
  return { ownerKind: "primary_runner", source: "run_patch" };
}

export function classifyRowWrite(row: {
  owner_kind?: DurableCodingRunOwnerKind | null;
  write_source?: DurableCodingRunWriteSource | null;
  reason_code?: string | null;
}): { ownerKind: DurableCodingRunOwnerKind; source: DurableCodingRunWriteSource } {
  if (row.owner_kind || row.write_source) {
    return {
      ownerKind: row.owner_kind ?? "unknown",
      source: row.write_source ?? "unknown",
    };
  }
  if (row.reason_code?.includes("stale") || row.reason_code?.includes("apply_ack")) {
    return { ownerKind: "stale_recovery", source: "stale_guard" };
  }
  return { ownerKind: "primary_runner", source: "row_upsert" };
}

export function appendWriteDebug(
  run: DurableCodingRun,
  entry: Omit<DurableCodingRunWriteDebugEntry, "invariant_violations">,
): DurableCodingRun {
  const invariantViolations = durableRunInvariantViolations(run);
  const nextEntry: DurableCodingRunWriteDebugEntry = {
    ...entry,
    invariant_violations: invariantViolations,
  };
  return {
    ...run,
    invariant_violations: invariantViolations,
    last_write_decision: entry.decision,
    owner_kind: entry.owner_kind,
    write_debug: [...(run.write_debug ?? []), nextEntry].slice(-80),
    write_source: entry.source,
  };
}

export function terminalWriteAllowed(
  current: DurableCodingRun,
  source: DurableCodingRunWriteSource,
  nextStatus: DurableCodingRunStatus | null | undefined,
) {
  if (!isTerminalRunStatus(current.status)) return true;
  if (!nextStatus) return true;
  if (CONTROL_WRITE_SOURCES.has(source)) return true;
  return !(nextStatus === "running" || nextStatus === "pending");
}
