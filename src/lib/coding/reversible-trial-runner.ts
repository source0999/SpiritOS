import { isAgentLabTrialPath } from "@/lib/coding/agent-lab-cleanup";
import type { DurableCodingRun, DurableCodingRunRow } from "@/lib/coding/durable-run-types";

export const AGENT_LAB_BASELINE_ROOTS = [
  "src/app/agent-lab",
  "src/components/agent-lab",
  "src/lib/agent-lab",
  "src/app/api/agent-lab",
  "tests/agent-lab",
] as const;

/** Known Coder ×10 page targets probed when workspace list is shallow. */
export const AGENT_LAB_CODER_PROBE_PATHS = [
  "src/app/agent-lab/page.tsx",
  "src/app/agent-lab/calculator/page.tsx",
  "src/app/agent-lab/todo/page.tsx",
  "src/app/agent-lab/cards/page.tsx",
  "src/app/agent-lab/form/page.tsx",
  "src/app/agent-lab/counter/page.tsx",
  "src/app/agent-lab/theme/page.tsx",
  "src/app/agent-lab/notes/page.tsx",
  "src/app/agent-lab/proxy-health/page.tsx",
] as const;

export type TrialApplyStepInstrumentation = {
  checks_completed_at?: string | null;
  checks_started_at?: string | null;
  diff_preview_completed_at?: string | null;
  diff_preview_requested_at?: string | null;
  disk_probe_completed_at?: string | null;
  disk_probe_started_at?: string | null;
  execute_approved_body_read_completed_at?: string | null;
  execute_approved_body_read_failed_at?: string | null;
  execute_approved_body_read_started_at?: string | null;
  execute_approved_completed_at?: string | null;
  execute_approved_content_type?: string | null;
  execute_approved_http_status?: string | null;
  execute_approved_requested_at?: string | null;
  last_progress_reason_code?: string | null;
  prompt_packet_completed_at?: string | null;
  prompt_packet_requested_at?: string | null;
  result_finalized_at?: string | null;
  reverse_receipt_created_at?: string | null;
};

export type AgentLabBaselineSnapshot = {
  baseline_agent_lab_files: string[];
  baseline_checked_at: string;
  baseline_clean_for_fresh_suite: boolean;
  baseline_dirty_agent_lab_files: string[];
  baseline_unreverted_receipts: string[];
};

export type CurrentSuiteAgentLabFileClassification = {
  expectedCurrentSuiteFiles: string[];
  staleLeftoverFiles: string[];
};

export type TrialRunnerRunBlockReason =
  | "suite_running"
  | "suite_stopping"
  | "cleanup_reverse_active"
  | "background_cleanup_active"
  | "pending_revert_targets"
  | "unreverted_receipts_reconciling";

export type EditReversibleOutcomeInput = {
  baselineCleanForFreshSuite?: boolean | null;
  diskChangedFiles?: string[];
  expectedOutcome: string;
  previewChangedFiles?: string[];
  promptPacketReasonCode?: string;
  proposedDiff?: string;
  providerCallMade?: boolean;
  reversalAvailable?: boolean;
};

export type EditReversibleOutcome =
  | { kind: "already_satisfied" }
  | {
      kind: "needs_fix";
      reason_code:
        | "already_satisfied_without_expected_noop"
        | "dirty_baseline_already_satisfied"
        | "edit_required_but_no_diff";
      visible_result_label: "NEEDS FIX";
    };

export type PassReversalProofInput = {
  appliedChangedFiles?: string[];
  diskChangedFiles?: string[];
  expectedOutcome?: string;
  reversalAvailable?: boolean;
  reverseDiff?: string;
  visibleResultLabel: string;
};

export type TrialPromptQuickLink = {
  href: string;
  kind: "page" | "parent";
  label: string;
};

export function normalizeRepoPathForTrial(path: string): string {
  return path.trim().replace(/\\/g, "/");
}

export function inferAgentLabPageHref(path: string): string | null {
  const safePath = normalizeRepoPathForTrial(path);
  if (!safePath.startsWith("src/app/agent-lab/")) return null;
  const appMatch = safePath.match(/^src\/app\/agent-lab\/(.+?)\/(page|layout)\.tsx$/);
  if (safePath === "src/app/agent-lab/page.tsx") return "/agent-lab";
  if (!appMatch) return null;
  const segments = appMatch[1]
    .split("/")
    .filter((segment) => segment && !segment.startsWith("(") && !segment.startsWith("@"));
  return segments.length > 0 ? `/agent-lab/${segments.join("/")}` : "/agent-lab";
}

export function buildTrialPromptQuickLinks(input: {
  quickFindPaths?: string[];
  selectedTarget?: string;
}): TrialPromptQuickLink[] {
  const paths = [
    ...(input.selectedTarget ? [input.selectedTarget] : []),
    ...(input.quickFindPaths ?? []),
  ].map(normalizeRepoPathForTrial);
  const links: TrialPromptQuickLink[] = [];
  const seen = new Set<string>();
  for (const path of paths) {
    const href = inferAgentLabPageHref(path);
    if (!href || seen.has(href)) continue;
    seen.add(href);
    links.push({
      href,
      kind: href === "/agent-lab" ? "parent" : "page",
      label: href === "/agent-lab" ? "Parent /agent-lab" : `View ${href}`,
    });
  }
  if (!seen.has("/agent-lab") && paths.some((path) => path.startsWith("src/app/agent-lab/"))) {
    links.unshift({ href: "/agent-lab", kind: "parent", label: "Parent /agent-lab" });
  }
  return links;
}

export function trialRunnerRunBlocked(input: {
  backgroundCleanupActive?: boolean;
  isReverting?: boolean;
  orphanUnrevertedReceiptCount?: number;
  suitePendingRevertCount?: number;
  suiteStatus: "idle" | "running" | "stopping" | "done" | "failed";
  unrevertedReceiptReconcileActive?: boolean;
}): { blocked: boolean; reason: TrialRunnerRunBlockReason | null; message: string } {
  if (input.suiteStatus === "running") {
    return {
      blocked: true,
      message: "Trial suite is still running. Wait for the current benchmark to finish.",
      reason: "suite_running",
    };
  }
  if (input.suiteStatus === "stopping") {
    return {
      blocked: true,
      message: "Trial suite is stopping. Wait for the current prompt to finish.",
      reason: "suite_stopping",
    };
  }
  if (input.isReverting) {
    return {
      blocked: true,
      message: "Cleanup/reverse is still running. Wait for it to finish before starting another benchmark.",
      reason: "cleanup_reverse_active",
    };
  }
  if (input.backgroundCleanupActive) {
    return {
      blocked: true,
      message: "Cleanup/reverse is still running in the background. Wait for it to finish before starting another benchmark.",
      reason: "background_cleanup_active",
    };
  }
  if (input.unrevertedReceiptReconcileActive) {
    return {
      blocked: true,
      message: "Trial receipt reconciliation is still running. Wait before starting another benchmark.",
      reason: "unreverted_receipts_reconciling",
    };
  }
  if ((input.suitePendingRevertCount ?? 0) > 0) {
    return {
      blocked: true,
      message: "Unreverted trial edits remain. Reverse trial edits before starting another benchmark.",
      reason: "pending_revert_targets",
    };
  }
  if ((input.orphanUnrevertedReceiptCount ?? 0) > 0) {
    return {
      blocked: true,
      message: "Stored trial receipts still need reverse. Use Reverse trial edits before starting another benchmark.",
      reason: "pending_revert_targets",
    };
  }
  return { blocked: false, message: "", reason: null };
}

export function classifyEditReversibleAlreadySatisfied(
  input: EditReversibleOutcomeInput,
): EditReversibleOutcome {
  const proposedDiff = (input.proposedDiff ?? "").trim();
  const reasonCode = (input.promptPacketReasonCode ?? "").trim();
  const hasDiskProof = (input.diskChangedFiles?.length ?? 0) > 0;
  const hasPreviewProof = (input.previewChangedFiles?.length ?? 0) > 0;
  const hasReversalProof = input.reversalAvailable === true;

  if (input.expectedOutcome !== "edit_reversible") {
    return { kind: "already_satisfied" };
  }

  if (reasonCode !== "coder_no_changes_needed" || !input.providerCallMade) {
    return {
      kind: "needs_fix",
      reason_code: "edit_required_but_no_diff",
      visible_result_label: "NEEDS FIX",
    };
  }

  if (input.baselineCleanForFreshSuite === false) {
    return {
      kind: "needs_fix",
      reason_code: "dirty_baseline_already_satisfied",
      visible_result_label: "NEEDS FIX",
    };
  }

  if (!proposedDiff && !hasDiskProof && !hasPreviewProof && !hasReversalProof) {
    return {
      kind: "needs_fix",
      reason_code: "already_satisfied_without_expected_noop",
      visible_result_label: "NEEDS FIX",
    };
  }

  return { kind: "already_satisfied" };
}

export function downgradePassWithoutReversalProof(input: PassReversalProofInput): {
  downgraded: boolean;
  failure_reason: string;
  reason_code: string;
  visible_result_label: "NEEDS FIX" | "PASS";
} {
  if (input.visibleResultLabel !== "PASS") {
    return {
      downgraded: false,
      failure_reason: "",
      reason_code: "",
      visible_result_label: input.visibleResultLabel as "NEEDS FIX" | "PASS",
    };
  }
  if (input.expectedOutcome && input.expectedOutcome !== "edit_reversible") {
    return {
      downgraded: false,
      failure_reason: "",
      reason_code: "",
      visible_result_label: "PASS",
    };
  }
  const applied = input.appliedChangedFiles ?? [];
  const disk = input.diskChangedFiles ?? [];
  const reverseDiff = (input.reverseDiff ?? "").trim();
  if (
    applied.length > 0 &&
    disk.length > 0 &&
    reverseDiff.length > 0 &&
    input.reversalAvailable === true
  ) {
    return {
      downgraded: false,
      failure_reason: "",
      reason_code: "",
      visible_result_label: "PASS",
    };
  }
  return {
    downgraded: true,
    failure_reason: "NEEDS FIX: PASS requires applied files, disk proof, and reversal availability.",
    reason_code: "pass_missing_reversal_proof",
    visible_result_label: "NEEDS FIX",
  };
}

export function evaluateAgentLabBaseline(input: {
  agentLabFiles: string[];
  checkedAt?: string;
  unrevertedReceiptTargets: string[];
}): AgentLabBaselineSnapshot {
  const baseline_agent_lab_files = Array.from(
    new Set(input.agentLabFiles.map(normalizeRepoPathForTrial).filter(Boolean)),
  ).sort();
  const dirtyFromReceipts = input.unrevertedReceiptTargets
    .map(normalizeRepoPathForTrial)
    .filter((path) => isAgentLabTrialPath(path));
  const baseline_unreverted_receipts = Array.from(new Set(dirtyFromReceipts)).sort();
  const baseline_dirty_agent_lab_files = Array.from(
    new Set([...baseline_agent_lab_files, ...baseline_unreverted_receipts]),
  ).sort();
  const baseline_clean_for_fresh_suite = baseline_dirty_agent_lab_files.length === 0;
  return {
    baseline_agent_lab_files,
    baseline_checked_at: input.checkedAt ?? new Date().toISOString(),
    baseline_clean_for_fresh_suite,
    baseline_dirty_agent_lab_files,
    baseline_unreverted_receipts,
  };
}

export function classifyCurrentSuiteAgentLabFiles(input: {
  completedPromptChangedFiles: string[];
  dirtyAgentLabFiles: string[];
}): CurrentSuiteAgentLabFileClassification {
  const expected = new Set(
    input.completedPromptChangedFiles
      .map(normalizeRepoPathForTrial)
      .filter((path) => path && isAgentLabTrialPath(path)),
  );
  const dirty = Array.from(
    new Set(
      input.dirtyAgentLabFiles
        .map(normalizeRepoPathForTrial)
        .filter((path) => path && isAgentLabTrialPath(path)),
    ),
  ).sort();
  return {
    expectedCurrentSuiteFiles: dirty.filter((path) => expected.has(path)),
    staleLeftoverFiles: dirty.filter((path) => !expected.has(path)),
  };
}

export function formatAgentLabBaselineDiagnostics(snapshot: AgentLabBaselineSnapshot): string[] {
  return [
    `baseline_checked_at: ${snapshot.baseline_checked_at}`,
    `baseline_agent_lab_files: ${snapshot.baseline_agent_lab_files.join(", ") || "none"}`,
    `baseline_dirty_agent_lab_files: ${snapshot.baseline_dirty_agent_lab_files.join(", ") || "none"}`,
    `baseline_unreverted_receipts: ${snapshot.baseline_unreverted_receipts.join(", ") || "none"}`,
    `baseline_clean_for_fresh_suite: ${snapshot.baseline_clean_for_fresh_suite ? "true" : "false"}`,
  ];
}

export function collectAgentLabFilesFromListEntries(
  roots: readonly string[],
  listedEntries: Array<{ path?: string; kind?: string }>,
): string[] {
  const files: string[] = [];
  for (const entry of listedEntries) {
    const path = normalizeRepoPathForTrial(entry.path ?? "");
    if (!path) continue;
    if (entry.kind === "file" || /\.[A-Za-z0-9]+$/.test(path)) {
      if (roots.some((root) => path === root || path.startsWith(`${root}/`))) {
        files.push(path);
      }
    }
  }
  return files;
}

function endpointStatusesForRow(run: DurableCodingRun, row: DurableCodingRunRow | null | undefined): string[] {
  return [...new Set([...(run.endpoint_statuses || []), ...(row?.endpoint_statuses || [])])];
}

function staleStartedAtMs(run: DurableCodingRun, row: DurableCodingRunRow | null | undefined): number {
  return Date.parse(
    run.current_step_started_at ||
      run.current_prompt_started_at ||
      row?.updated_at ||
      row?.started_at ||
      run.updated_at ||
      run.created_at,
  );
}

/** Running suite with completed rows but no in-flight row — runner lost between prompts. */
export function durableRunHasStaleBetweenPromptsGap(
  run: DurableCodingRun | null | undefined,
  nowMs = Date.now(),
  staleMs: number,
): boolean {
  if (!run || (run.status !== "running" && run.status !== "pending")) return false;
  if (run.completed_count < 1 || run.completed_count >= run.requested_count) return false;
  const hasActualInFlightRow = run.rows.some(
    (row) => row.status === "running" || row.status === "pending",
  );
  if (hasActualInFlightRow) return false;
  const startedAt = Date.parse(run.current_step_started_at || run.updated_at || "");
  return Number.isFinite(startedAt) && nowMs - startedAt > staleMs;
}

export function betweenPromptsStaleSummary(run: DurableCodingRun): string {
  const resumeAt = Math.min(run.completed_count + 1, run.requested_count);
  return `Suite runner lost after prompt ${run.completed_count}; resume from prompt ${resumeAt} of ${run.requested_count}.`;
}

export function durableRunHasStalePostApplyVerification(
  run: DurableCodingRun | null | undefined,
  nowMs = Date.now(),
  staleMs: number,
): boolean {
  if (!run || (run.status !== "running" && run.status !== "pending")) return false;
  const activeRow =
    (run.current_prompt_id ? run.rows.find((row) => row.prompt_id === run.current_prompt_id) : null) ??
    run.rows.find((row) => row.status === "running" || row.result_label === "RUNNING");
  if (!activeRow) return false;
  const statuses = endpointStatusesForRow(run, activeRow);
  const hasExecuteApproved200 = statuses.some((status) => status.startsWith("/v1/actions/execute-approved:200"));
  if (!hasExecuteApproved200) return false;
  if (statuses.some((status) => status.includes("server_apply_proof_recorded"))) return false;
  if (
    statuses.some(
      (status) =>
        status.includes("stale_no_completion") ||
        status.includes(":timeout") ||
        status.startsWith("/v1/actions/execute-approved:stale"),
    )
  ) {
    return false;
  }
  const hasAppliedProof =
    (activeRow.applied_changed_files?.length ?? 0) > 0 && (activeRow.disk_changed_files?.length ?? 0) > 0;
  const terminalLabel = (activeRow.result_label || "").trim();
  if (hasAppliedProof && terminalLabel && terminalLabel !== "RUNNING") return false;
  if (!hasAppliedProof && terminalLabel && terminalLabel !== "RUNNING" && terminalLabel !== "") return false;
  const instrumentation = activeRow.step_instrumentation;
  const finalizedAt = instrumentation?.result_finalized_at;
  if (finalizedAt) return false;
  const startedAt = staleStartedAtMs(run, activeRow);
  return Number.isFinite(startedAt) && nowMs - startedAt > staleMs;
}

export function postApplyStaleReasonCode(run: DurableCodingRun): string {
  const activeRow =
    (run.current_prompt_id ? run.rows.find((row) => row.prompt_id === run.current_prompt_id) : null) ??
    run.rows.find((row) => row.status === "running" || row.result_label === "RUNNING");
  const statuses = endpointStatusesForRow(run, activeRow ?? undefined);
  if (statuses.some((status) => status.includes("server_apply_proof_recorded"))) {
    return "server_apply_proof_recorded";
  }
  if (statuses.some((status) => status.startsWith("/v1/actions/execute-approved:200"))) {
    const instrumentation = activeRow?.step_instrumentation;
    if (
      instrumentation?.execute_approved_body_read_started_at &&
      !instrumentation.execute_approved_body_read_completed_at
    ) {
      return "execute_approved_body_read_missing";
    }
    if ((activeRow?.applied_changed_files?.length ?? 0) === 0) {
      return "apply_ack_no_disk_proof";
    }
    return "post_apply_verification_missing";
  }
  return "execute_approved_no_completion";
}

export function postApplyStaleNextAction(reasonCode: string): string {
  if (reasonCode === "apply_ack_no_disk_proof" || reasonCode === "post_apply_verification_missing") {
    return "Inspect execute-approved response and disk probe. Do not rerun full suite until cleanup/reverse is stable.";
  }
  return "Inspect execute-approved response and disk probe. Do not rerun full suite until cleanup/reverse is stable.";
}

export function mergeStepInstrumentation(
  current: TrialApplyStepInstrumentation | null | undefined,
  patch: TrialApplyStepInstrumentation,
): TrialApplyStepInstrumentation {
  return { ...(current ?? {}), ...patch };
}
