"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { Copy, FileText, Plus, ShieldCheck } from "lucide-react";

import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import {
  agentTrialRunSizes,
  agentTrialViewports,
  BACKEND_ROUTE_TRIAL_FIXTURE_PATH,
  backendRouteTrialHasOkParam,
  backendRouteTrialResetDiff,
  buildAgentTrialUiState,
  classifyDiagnosticSidecar,
  COMPONENT_TRIAL_FIXTURE_PATH,
  COMPONENT_TRIAL_TEST_FIXTURE_PATH,
  componentTrialHasWarningTone,
  componentTrialResetDiff,
  componentTrialTestResetDiff,
  dummyTrialBaselineResetDiff,
  DUMMY_TRIAL_EDIT_FIXTURE_TARGETS,
  dummyTrialBaselineResetDiffs,
  ROUTE_SUMMARY_TRIAL_FIXTURE_PATH,
  routeSummaryTrialResetDiff,
  evaluateManualComposerTrialVerdict,
  type AgentTrialApplyStrategy,
  type AgentTrialBank,
  type AgentTrialMode,
  type AgentTrialProofMode,
  type AgentTrialPromptPreview,
  type AgentTrialRunSize,
  type AgentTrialViewport,
} from "@/lib/coding/agent-trials-ui";
import {
  buildChangedFilesDiagnostics,
  changedFilesFromDiffPreview,
  formatChangedFilesDiagnosticsLines,
} from "@/lib/coding/changed-files-diagnostics";
import {
  localHermesProviderModelTruth,
  ollamaStoragePathFromSelfStatus,
  providerModelTruthFromPayload,
  providerModelTruthFromSelfStatus,
  providerTruthFromPreviewState,
  type CodingProviderModelTruth,
} from "@/lib/coding/model-provider-status";
import { providerAndChangedFilesDiagnosticLines } from "@/lib/coding/provider-model-diagnostic-lines";
import {
  buildStressTestReadiness,
  formatStressTestReadinessLines,
  type ProviderCallSmokeResult,
} from "@/lib/coding/stress-test-readiness";
import {
  countActiveUnrevertedTrialReceipts,
  isTrialRunReceipt as isTrialRunReceiptRecord,
} from "@/lib/coding/trial-receipt-reconciliation";
import { copyTextToClipboard } from "@/lib/clipboard";
import { taskRequestsPreviewOnly } from "@/lib/coding/preview-only-request";
import {
  mapVisibleResultBadge,
  type VisibleResultBadge,
  type VisibleResultTone,
} from "@/lib/coding/visible-result-badge";
import {
  normalizeReversibleTrialCategoryInput,
  reversibleTrialCategories,
  reversibleTrialCounts,
  selectReversibleTrialPrompts,
  type ReversibleTrialCategory,
  type ReversibleTrialCount,
  type ReversibleTrialPrompt,
} from "@/lib/coding/reversible-trial-prompts";

const commandPanelClass =
  "rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-pill-bg)] shadow-[var(--ddv4-glass-shadow-drop)] backdrop-blur-xl";
const commandInsetClass =
  "rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)]";
const commandLabelClass =
  "text-xs font-semibold uppercase tracking-[0.14em] text-[var(--ddv4-fg-faint)]";
const commandTextClass = "text-[var(--ddv4-fg)]";
const commandMutedClass = "text-[var(--ddv4-fg-muted)]";
const commandFocusClass =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--spirit-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-transparent";
const commandControlClass = `${commandFocusClass} transition-colors duration-150`;
type PreviewState = {
  approvalAvailable: boolean;
  approvedAt: string | null;
  appliedAt: string | null;
  applySummary: string;
  allowedFiles: string[];
  blocker: string | null;
  changedFiles: string[];
  checks: string[];
  currentPhase: string;
  diff: string;
  error: string | null;
  events: ManualTaskEvent[];
  forbiddenFiles: string[];
  isApplying: boolean;
  isLoading: boolean;
  model: string | null;
  previewStatus: string;
  provider: string | null;
  providerCallAuthorized?: boolean;
  providerCallMade?: boolean;
  providerModelBlockedReason?: string;
  providerModelApiBaseHost?: string | null;
  providerModelProbeOk?: boolean | null;
  providerModelSelectedVia?: string | null;
  providerModelSource?: string;
  providerModelStatus?: string;
  configuredModelIsHermes?: boolean | null;
  hermesLaneAvailable?: boolean;
  hermesUsedForThisRun?: boolean | null;
  requirementSummary: string;
  reasonCode: string | null;
  reviewerSummary: string;
  routeCalled: string | null;
  selectedTarget: string | null;
  status: "idle" | "ready" | "approved" | "applied" | "blocked" | "error" | "satisfied";
  targetCandidates: string[];
  targetMatch: boolean;
  taskId: string;
  taskSpecAllowed: boolean;
  verifierSummary: string;
  technicalDetail?: string | null;
};

type TrialRunState = "idle" | "running" | "complete";
type ReversibleSuiteStatus = "idle" | "running" | "stopping" | "done" | "failed";
type ReversibleSuitePromptResult = {
  allowed_files: string[];
  applied_changed_files: string[];
  checks_result: string;
  checks_run: string[];
  disk_changed_files: string[];
  endpoint_statuses: string[];
  error_summary: string;
  expected_outcome: ReversibleTrialPrompt["expectedOutcome"];
  failure_reason: string;
  model_called_for_generation: string;
  next_recommended_action: string;
  prompt: ReversibleTrialPrompt;
  provider: string;
  provider_call_made: boolean;
  preview_changed_files: string[];
  reverse_diff: string;
  reverse_status_text: string;
  reverted: boolean;
  reversal_available: boolean;
  run_id: string;
  selected_target: string;
  target_candidates: string[];
  visible_result_label:
    | "PASS"
    | "REVERTED"
    | "FAIL"
    | "NEEDS FIX"
    | "BLOCKED"
    | "NO EDIT EXPECTED"
    | "ALREADY SATISFIED";
  elapsed_ms: number | null;
};
type ReversibleSuiteState = {
  completed: number;
  count: ReversibleTrialCount;
  currentPrompt: string;
  currentPromptElapsedMs: number | null;
  currentStep: string;
  currentStepStartedAt: number | null;
  alreadySatisfied: number;
  expectedNoEdit: number;
  fail: number;
  interruptionReason: string | null;
  interruptionSource: "none" | "user_stop" | "browser_refresh_or_dev_reload" | "route_failed" | "provider_timeout";
  pass: number;
  provider: string;
  model: string;
  results: ReversibleSuitePromptResult[];
  reverted: number;
  safetyBlock: number;
  status: ReversibleSuiteStatus;
  stopped: boolean;
  suiteFinishedAt: number | null;
  suiteId: string;
  suiteStartedAt: number | null;
  timeout: number;
};
type ReversibleSuiteAbort = {
  reason: string;
  source: Extract<ReversibleSuiteState["interruptionSource"], "route_failed" | "provider_timeout">;
  step: string;
};

function reversibleSuiteAbortForResult(result: ReversibleSuitePromptResult): ReversibleSuiteAbort | null {
  const endpointText = result.endpoint_statuses.join(", ");
  const failureText = `${result.failure_reason} ${result.error_summary}`.toLowerCase();
  const hasServerError = result.endpoint_statuses.some((status) => /:5\d\d(?:\b|$)/.test(status));
  const hasTimedOut = result.endpoint_statuses.some((status) => /:timeout(?:\b|$)/.test(status));
  const fetchFailed = failureText.includes("failed to fetch");
  const targetMissing = failureText.includes("reason_code=target_missing");
  const providerTimedOut =
    hasTimedOut ||
    failureText.includes("timeout_source: /v1/decisions/prompt-packet") ||
    failureText.includes("model call timed out");

  if (providerTimedOut) {
    return {
      reason: `provider_timeout: ${endpointText || result.failure_reason || "model route timed out"}`,
      source: "provider_timeout",
      step: "Stopped after provider timeout",
    };
  }
  if (hasServerError || fetchFailed) {
    return {
      reason: hasServerError
        ? `route_failed: ${endpointText}`
        : `route_failed: ${result.failure_reason || "Failed to fetch"}`,
      source: "route_failed",
      step: "Stopped after route failure",
    };
  }
  return null;
}

export function reversibleSuiteExceptionLabel(message: string): ReversibleSuitePromptResult["visible_result_label"] {
  const normalized = message.toLowerCase();
  if (
    normalized.includes("preview request returned status") ||
    normalized.includes("failed to fetch") ||
    normalized.includes("source proxy") ||
    normalized.includes("coder_sync_timeout") ||
    normalized.includes("browser_abort_timeout") ||
    normalized.includes("route") ||
    normalized.includes("timeout")
  ) {
    return "NEEDS FIX";
  }
  return "FAIL";
}

function reversibleResultIsTimeout(result: ReversibleSuitePromptResult): boolean {
  const text = [
    result.failure_reason,
    result.error_summary,
    ...result.endpoint_statuses,
  ].join(" ").toLowerCase();
  return text.includes("timeout");
}

function reversibleResultIsAlreadySatisfied(result: ReversibleSuitePromptResult): boolean {
  return (
    result.visible_result_label === "ALREADY SATISFIED" ||
    result.checks_result.toLowerCase().includes("already satisfied") ||
    result.reverse_status_text.toLowerCase().includes("already satisfies")
  );
}

function reversibleResultIsSafetyBlock(result: ReversibleSuitePromptResult): boolean {
  const text = [
    result.checks_result,
    result.failure_reason,
    result.error_summary,
    result.reverse_status_text,
  ].join(" ").toLowerCase();
  return (
    result.visible_result_label === "BLOCKED" ||
    result.expected_outcome === "safety_block_expected" ||
    text.includes("protected path") ||
    text.includes("blocked for safety")
  );
}
type ComposerTimingState = {
  diffPreviewMs: number | null;
  promptPacketMs: number | null;
  runStartedAt: number | null;
  totalMs: number | null;
};
type ManualTaskEventStatus = "done" | "running" | "blocked" | "failed";
type ManualTaskEvent = {
  detail: string;
  label: string;
  status: ManualTaskEventStatus;
};

const manualTaskPhaseLabels = {
  received: "Reading request",
  analyzing: "Reading request",
  discovering: "Finding files",
  packet: "Finding files",
  preview: "Calling model",
  checks: "Checking",
  review: "Ready to review",
  done: "Ready to review",
  blocked: "Ready to review",
  failed: "Ready to review",
} as const;

/** Match CodingAgentInterface prompt-packet patience; proxy coder sync deadline defaults to 180s. */
const MANUAL_PROMPT_PACKET_TIMEOUT_MS = 180_000;
const TRIAL_PROMPT_PACKET_TIMEOUT_BUFFER_MS = 180_000;
const TRIAL_PROMPT_PACKET_TIMEOUT_MS = MANUAL_PROMPT_PACKET_TIMEOUT_MS + TRIAL_PROMPT_PACKET_TIMEOUT_BUFFER_MS;
const PROTECTED_FORBIDDEN_FILES = [
  ".env*",
  "source_proxy/data/**",
  "backend/volumes/**",
  "backend/searxng_data/**",
  ".spirit-backups/**",
  "secrets",
  "credentials",
];

function formatElapsedMs(startedAt: number | null, endedAt: number = performance.now()): string {
  if (startedAt == null) return "—";
  const ms = Math.max(0, endedAt - startedAt);
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function elapsedMs(startedAt: number | null, endedAt: number = performance.now()): number | null {
  if (startedAt == null) return null;
  return Math.max(0, Math.round(endedAt - startedAt));
}

function trialProviderCallMadeFromPayload(
  payload: unknown,
  providerTruth: ReturnType<typeof providerModelTruthFromPayload>,
): boolean {
  if (providerTruth.providerCallMade === true) return true;
  const record =
    payload && typeof payload === "object" ? (payload as Record<string, unknown>) : null;
  if (!record) return false;
  const diagnosticsRaw = record.coder_diagnostics ?? record.coderDiagnostics;
  const diagnostics =
    diagnosticsRaw && typeof diagnosticsRaw === "object"
      ? (diagnosticsRaw as Record<string, unknown>)
      : null;
  if (diagnostics?.provider_call_made === true) return true;
  if (record.provider_call_made === true || record.providerCallMade === true) return true;
  const alreadySatisfied = record.already_satisfied === true || record.alreadySatisfied === true;
  return alreadySatisfied && Boolean(diagnostics?.provider_call_made ?? record.provider_call_made);
}

function trialModelProofFailureSummary(
  payload: unknown,
  reasonCode: string,
  selectedTarget: string,
): string {
  const record = asRecord(payload);
  const diagnostics = asRecord(record.coder_diagnostics ?? record.coderDiagnostics);
  const attemptedAliases = Array.isArray(diagnostics.trial_proof_aliases_attempted)
    ? diagnostics.trial_proof_aliases_attempted.map((item) => String(item)).filter(Boolean)
    : [];
  const fields = [
    "phase=model_proof",
    "server=Source Proxy",
    "route=POST /v1/decisions/prompt-packet",
    "url=/v1/decisions/prompt-packet",
    "failure_type=model_proof",
    `reason_code=${reasonCode || "provider_call_made_false"}`,
    `selected_target=${selectedTarget || "none"}`,
    `attempted_aliases=${attemptedAliases.length > 0 ? attemptedAliases.join("|") : "unknown"}`,
    `provider=${stringValue(diagnostics.provider) ?? stringValue(record.provider) ?? "unknown"}`,
    `model=${stringValue(diagnostics.model) ?? stringValue(diagnostics.litellm_model) ?? stringValue(record.model) ?? "none"}`,
    `exception_type=${stringValue(diagnostics.exception_type) ?? "none"}`,
    `exception_message=${stringValue(diagnostics.exception_message) ?? "none"}`,
  ];
  return fields.join("; ");
}

function isReversibleSuiteTimingFrozen(state: ReversibleSuiteState): boolean {
  return state.status === "done" || state.status === "failed";
}

/** Freeze wall-clock display when the suite is no longer running (avoids live performance.now() drift on re-renders). */
function reversibleSuiteTimingEndAt(state: ReversibleSuiteState): number {
  if (state.suiteFinishedAt != null) return state.suiteFinishedAt;
  if (state.status === "running" || state.status === "stopping") return performance.now();
  return state.suiteStartedAt ?? performance.now();
}

function estimateStoredSuiteFinishedAt(
  suiteStartedAt: number | null,
  results: ReversibleSuitePromptResult[],
): number | null {
  if (suiteStartedAt == null) return null;
  const promptMs = results.reduce(
    (sum, row) => sum + (typeof row.elapsed_ms === "number" ? row.elapsed_ms : 0),
    0,
  );
  return suiteStartedAt + Math.max(promptMs, 0);
}

type ManualTaskPhase = keyof typeof manualTaskPhaseLabels;

/** Spinner label while prompt-packet runs — avoid stuck "Calling model" when Source Proxy is dead. */
function previewLoadingPhaseLabel(sourceProxyReachable: boolean, phase: ManualTaskPhase): string {
  if (phase === "preview" && !sourceProxyReachable) {
    return "Source Proxy unreachable";
  }
  return manualTaskPhaseLabels[phase];
}

function previewLoadingSimpleResult(
  sourceProxyReachable: boolean,
  previewState: PreviewState,
  idleLabel: string,
): string {
  if (!previewState.isLoading) {
    return previewState.error ?? previewState.blocker ?? idleLabel;
  }
  if (!sourceProxyReachable) {
    return "Source Proxy unreachable — backend failure (not stuck on Calling model).";
  }
  if (
    previewState.reasonCode === "coder_sync_timeout" ||
    previewState.reasonCode === "source_proxy_timeout"
  ) {
    return "Backend failed — model sync timed out (transcript preserved).";
  }
  return "Previewing";
}

type ManualTaskPacket = {
  allowedFiles: string[];
  checks: string[];
  forbiddenFiles: string[];
  reasonCode: string | null;
  selectedTarget: string | null;
  targetCandidates: string[];
  taskText: string;
};

type ApplyScopePreflight = {
  allowedFiles: string[];
  allChangedFilesAllowed: boolean;
  changedFiles: string[];
  reason: string | null;
  reasonCode: string | null;
};

type VerificationTarget = {
  fileOpenAvailable: boolean;
  path: string;
  relatedPageHref: string | null;
  routeInferenceNote: string;
  safe: boolean;
};

type AppliedRunReceipt = {
  allowedFiles: string[];
  appliedAt: string;
  changedFiles: string[];
  diff: string;
  id: string;
  prompt: string;
  provider: string | null;
  model: string | null;
  providerModelSource: string;
  providerModelStatus: string;
  hermesUsedForThisRun: boolean | null;
  revertedAt: string | null;
  reversalProvider: string | null;
  reversalModel: string | null;
  reversalProviderModelSource: string | null;
  reverseDiff: string;
  staleResolvedAt?: string | null;
  target: string;
  taskId: string;
};

const appliedRunReceiptStorageKey = "spiritos:coding:applied-run-receipts:v1";
const promptHistoryStorageKey = "spiritos:coding:prompt-history:v1";
const reversibleSuiteStorageKey = "spiritos:coding:reversible-suite-state:v1";

function storedReversibleSuiteSnapshot(): string | null {
  if (typeof window === "undefined") return null;
  return (
    window.sessionStorage.getItem(reversibleSuiteStorageKey) ??
    window.localStorage.getItem(reversibleSuiteStorageKey)
  );
}

function defaultReversibleSuiteState(): ReversibleSuiteState {
  const providerTruth = selectedProviderModelTruth();
  return {
    completed: 0,
    count: 10,
    currentPrompt: "",
    currentPromptElapsedMs: null,
    currentStep: "Idle",
    currentStepStartedAt: null,
    alreadySatisfied: 0,
    expectedNoEdit: 0,
    fail: 0,
    interruptionReason: null,
    interruptionSource: "none",
    pass: 0,
    provider: providerTruth.providerLabel,
    model: providerTruth.modelLabel,
    results: [],
    reverted: 0,
    safetyBlock: 0,
    status: "idle",
    stopped: false,
    suiteFinishedAt: null,
    suiteId: "",
    suiteStartedAt: null,
    timeout: 0,
  };
}

function loadStoredReversibleSuiteState(): ReversibleSuiteState {
  if (typeof window === "undefined") return defaultReversibleSuiteState();
  try {
    const parsed = JSON.parse(storedReversibleSuiteSnapshot() ?? "null") as Partial<ReversibleSuiteState> | null;
    if (!parsed || typeof parsed !== "object") return defaultReversibleSuiteState();
    const base = defaultReversibleSuiteState();
    const storedStatus =
      parsed.status === "running" ||
      parsed.status === "stopping" ||
      parsed.status === "done" ||
      parsed.status === "failed"
        ? parsed.status
        : "idle";
    const interrupted = storedStatus === "running" || storedStatus === "stopping";
    const userStoppedBeforeReload = parsed.stopped === true || parsed.interruptionSource === "user_stop";
    const interruptionReason = interrupted
      ? userStoppedBeforeReload
        ? "user_clicked_stop_after_current_prompt"
        : "browser_refresh_or_dev_reload"
      : typeof parsed.interruptionReason === "string"
        ? parsed.interruptionReason
        : base.interruptionReason;
    const interruptionSource = interrupted
      ? userStoppedBeforeReload
        ? "user_stop"
        : "browser_refresh_or_dev_reload"
      : parsed.interruptionSource ?? base.interruptionSource;
    const results = Array.isArray(parsed.results) ? parsed.results : [];
    const suiteStartedAt =
      typeof parsed.suiteStartedAt === "number" ? parsed.suiteStartedAt : base.suiteStartedAt;
    const suiteFinishedAt =
      typeof parsed.suiteFinishedAt === "number"
        ? parsed.suiteFinishedAt
        : !interrupted && (storedStatus === "done" || storedStatus === "failed")
          ? estimateStoredSuiteFinishedAt(suiteStartedAt, results as ReversibleSuitePromptResult[])
          : base.suiteFinishedAt;
    return {
      ...base,
      ...parsed,
      count: (parsed.count as ReversibleTrialCount | undefined) ?? base.count,
      interruptionReason,
      interruptionSource,
      currentPrompt: interrupted
        ? userStoppedBeforeReload
          ? "Suite paused after user stop. Transcript preserved — reverse pending edits or run again."
          : "Suite paused after browser refresh/dev reload. Transcript preserved — reverse pending edits or run again."
        : typeof parsed.currentPrompt === "string"
          ? parsed.currentPrompt
          : base.currentPrompt,
      currentStep: interrupted
        ? userStoppedBeforeReload
          ? "Stopped after current prompt"
          : "Paused after browser refresh/dev reload"
        : typeof parsed.currentStep === "string"
          ? parsed.currentStep
          : base.currentStep,
      results,
      suiteFinishedAt,
      suiteStartedAt,
      status: interrupted ? "failed" : storedStatus,
      stopped: userStoppedBeforeReload ? true : Boolean(!interrupted && parsed.stopped),
    };
  } catch {
    return defaultReversibleSuiteState();
  }
}

function storeReversibleSuiteState(state: ReversibleSuiteState) {
  if (typeof window === "undefined") return;
  const serialized = JSON.stringify(state);
  window.sessionStorage.setItem(reversibleSuiteStorageKey, serialized);
  window.localStorage.setItem(reversibleSuiteStorageKey, serialized);
}

function clearStoredReversibleSuiteState() {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(reversibleSuiteStorageKey);
  window.localStorage.removeItem(reversibleSuiteStorageKey);
}

function isRecoverableModelLaneBlockedSuite(state: ReversibleSuiteState): boolean {
  return (
    state.status === "failed" &&
    state.results.length === 0 &&
    state.interruptionSource === "route_failed" &&
    (state.currentStep === "Blocked before model proof" ||
      Boolean(state.interruptionReason?.startsWith("model_lane_unavailable:")))
  );
}

function suiteReceiptIdForResult(result: Pick<ReversibleSuitePromptResult, "prompt" | "run_id">): string {
  return `trial-suite:${result.prompt.id}:${result.run_id}`;
}

function suiteTrialPromptIdFromReceiptId(receiptId: string): string | null {
  if (!receiptId.startsWith("trial-suite:")) return null;
  const body = receiptId.slice("trial-suite:".length);
  const separator = body.lastIndexOf(":");
  if (separator <= 0) return null;
  return body.slice(0, separator);
}

function revertActionForReceipt(receipt: AppliedRunReceipt): string {
  const suitePromptId = suiteTrialPromptIdFromReceiptId(receipt.id);
  if (suitePromptId) {
    return `Revert live trial ${suitePromptId}`;
  }
  if (receipt.id.startsWith("trial-reset:")) {
    const slug =
      receipt.target
        .split("/")
        .pop()
        ?.replace(/\.[^.]+$/, "") ?? "fixture-reset";
    return `Revert live trial ${slug}`;
  }
  if (receiptIsTrialRun(receipt)) {
    return `Revert live trial ${receipt.taskId}`;
  }
  return `Revert ${receipt.target}`;
}

function syncSuiteReceiptRevertState(
  receipts: AppliedRunReceipt[],
  result: Pick<
    ReversibleSuitePromptResult,
    "model_called_for_generation" | "prompt" | "provider" | "reverted" | "reversal_available" | "run_id"
  >,
): AppliedRunReceipt[] {
  if (!result.reversal_available || !result.reverted || !result.run_id) {
    return receipts;
  }
  const receiptId = suiteReceiptIdForResult(result);
  const revertedAt = new Date().toISOString();
  return receipts.map((receipt) =>
    receipt.id === receiptId && !receipt.revertedAt
      ? {
          ...receipt,
          revertedAt,
          reversalModel: result.model_called_for_generation,
          reversalProvider: result.provider,
          reversalProviderModelSource: "trial-suite",
        }
      : receipt,
  );
}

function forwardDiffForSuiteResult(result: ReversibleSuitePromptResult): string {
  return reverseUnifiedDiff(result.reverse_diff);
}

function receiptForSuiteReverseResult(
  result: ReversibleSuitePromptResult,
  storedReceipts: AppliedRunReceipt[],
): AppliedRunReceipt {
  const receiptId = suiteReceiptIdForResult(result);
  const stored = storedReceipts.find((item) => item.id === receiptId);
  if (stored && !stored.revertedAt) {
    return stored;
  }
  const forwardDiff = forwardDiffForSuiteResult(result);
  return {
    ...receiptFromSuiteResult(result),
    changedFiles:
      result.applied_changed_files.length > 0
        ? result.applied_changed_files
        : changedFilesFromDiffPreview(forwardDiff),
    diff: forwardDiff,
  };
}

async function reconcileTrialReceiptsViaApi(
  receipts: AppliedRunReceipt[],
): Promise<AppliedRunReceipt[]> {
  if (process.env.NODE_ENV === "test" || receipts.length === 0) {
    return receipts;
  }
  try {
    const response = await fetch("/v1/coding/trial-receipt-reconcile", {
      body: JSON.stringify({ receipts }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    if (!response.ok) {
      return receipts;
    }
    const payload = (await response.json()) as { receipts?: AppliedRunReceipt[] };
    return Array.isArray(payload.receipts) ? payload.receipts : receipts;
  } catch {
    return receipts;
  }
}

function receiptFromSuiteResult(result: ReversibleSuitePromptResult): AppliedRunReceipt {
  return {
    allowedFiles: result.allowed_files,
    appliedAt: new Date().toISOString(),
    changedFiles: result.disk_changed_files,
    diff: forwardDiffForSuiteResult(result),
    hermesUsedForThisRun: null,
    id: suiteReceiptIdForResult(result),
    model: result.model_called_for_generation,
    prompt: result.prompt.prompt,
    provider: result.provider,
    providerModelSource: "trial-suite",
    providerModelStatus: "recorded",
    revertedAt: null,
    reversalModel: null,
    reversalProvider: null,
    reversalProviderModelSource: null,
    reverseDiff: result.reverse_diff,
    target: result.selected_target || result.prompt.targetFile,
    taskId: result.run_id,
  };
}

function reversalLooksAlreadyApplied(message: string): boolean {
  const lower = message.toLowerCase();
  return (
    lower.includes("no changed files") ||
    lower.includes("already reverted") ||
    lower.includes("snapshot restored") ||
    lower.includes("nothing to revert") ||
    lower.includes("target file(s) not found") ||
    lower.includes("git apply") ||
    lower.includes("patch does not apply") ||
    lower.includes("diff_apply_check") ||
    lower.includes("blocked by safety verification")
  );
}

function suiteResultTargetKey(
  result: Pick<ReversibleSuitePromptResult, "prompt" | "selected_target">,
): string {
  return normalizeRepoPath(result.selected_target || result.prompt.targetFile);
}

function latestUnrevertedSuiteResultsByTarget(
  results: ReversibleSuitePromptResult[],
): ReversibleSuitePromptResult[] {
  const latestByTarget = new Map<string, ReversibleSuitePromptResult>();
  for (const result of results) {
    if (!result.reversal_available || result.reverted || !result.reverse_diff.trim()) {
      continue;
    }
    const key = suiteResultTargetKey(result);
    const existing = latestByTarget.get(key);
    if (!existing || result.prompt.id.localeCompare(existing.prompt.id) > 0) {
      latestByTarget.set(key, result);
    }
  }
  return [...latestByTarget.values()];
}

function syncReversibleSuiteResultsFromReceipts(
  results: ReversibleSuitePromptResult[],
  receipts: AppliedRunReceipt[],
): ReversibleSuitePromptResult[] {
  const latestPromptIdByTarget = new Map(
    latestUnrevertedSuiteResultsByTarget(results).map((result) => [
      suiteResultTargetKey(result),
      result.prompt.id,
    ]),
  );
  return results.map((result) => {
    if (!result.reversal_available || result.reverted) {
      return result;
    }
    const latestPromptId = latestPromptIdByTarget.get(suiteResultTargetKey(result));
    if (latestPromptId && latestPromptId !== result.prompt.id) {
      return result;
    }
    const receipt = receipts.find((item) => item.id === suiteReceiptIdForResult(result));
    if (!receipt?.revertedAt && !receipt?.staleResolvedAt) {
      return result;
    }
    return {
      ...result,
      reverted: true,
      reverse_status_text: receipt.staleResolvedAt
        ? "Already at trial baseline on disk."
        : "Reversed manually through trial runner controls.",
    };
  });
}

function alignSuiteResultsToDiskAndReverts(
  results: ReversibleSuitePromptResult[],
  receipts: AppliedRunReceipt[],
): ReversibleSuitePromptResult[] {
  const synced = syncReversibleSuiteResultsFromReceipts(results, receipts);
  const latestStillPending = new Set(
    latestUnrevertedSuiteResultsByTarget(synced).map((result) => suiteResultTargetKey(result)),
  );
  return synced.map((result) => {
    if (!result.reversal_available || result.reverted) {
      return result;
    }
    if (latestStillPending.has(suiteResultTargetKey(result))) {
      return result;
    }
    return {
      ...result,
      reverted: true,
      reverse_status_text: "Already at trial baseline on disk.",
    };
  });
}

function registerSuiteTargetReverted(
  target: string,
  suiteResults: ReversibleSuitePromptResult[],
  reconciledReceipts: AppliedRunReceipt[],
  revertedSuiteKeys: Set<string>,
  revertedReceiptIds: Set<string>,
) {
  const normalized = normalizeRepoPath(target);
  for (const result of suiteResults) {
    if (!result.reversal_available || result.reverted) {
      continue;
    }
    if (suiteResultTargetKey(result) !== normalized) {
      continue;
    }
    revertedSuiteKeys.add(`${result.prompt.id}:${result.run_id}`);
    revertedReceiptIds.add(suiteReceiptIdForResult(result));
  }
  for (const receipt of reconciledReceipts) {
    if (!receipt.id.startsWith("trial-suite:")) {
      continue;
    }
    if (normalizeRepoPath(receipt.target) !== normalized) {
      continue;
    }
    revertedReceiptIds.add(receipt.id);
  }
}

function buildSuiteTrialReceipt(input: {
  allowedFiles: string[];
  appliedAt: string;
  changedFiles: string[];
  diff: string;
  model: string;
  prompt: ReversibleTrialPrompt;
  provider: string;
  reverseDiff: string;
  revertedAt: string | null;
  runId: string;
  target: string;
}): AppliedRunReceipt {
  return {
    allowedFiles: input.allowedFiles,
    appliedAt: input.appliedAt,
    changedFiles: input.changedFiles,
    diff: input.diff,
    hermesUsedForThisRun: null,
    id: `trial-suite:${input.prompt.id}:${input.runId}`,
    model: input.model,
    prompt: input.prompt.prompt,
    provider: input.provider,
    providerModelSource: "trial-suite",
    providerModelStatus: "recorded",
    revertedAt: input.revertedAt,
    reversalModel: input.revertedAt ? input.model : null,
    reversalProvider: input.revertedAt ? input.provider : null,
    reversalProviderModelSource: input.revertedAt ? "trial-suite" : null,
    reverseDiff: input.reverseDiff,
    target: input.target,
    taskId: input.runId,
  };
}

function idlePreviewState(): PreviewState {
  const providerTruth = selectedProviderModelTruth();
  return {
    approvalAvailable: false,
    approvedAt: null,
    appliedAt: null,
    applySummary: "",
    allowedFiles: [],
    blocker: null,
    changedFiles: [],
    checks: ["git diff --check"],
    currentPhase: "waiting for prompt",
    diff: "",
    error: null,
    events: [],
    forbiddenFiles: PROTECTED_FORBIDDEN_FILES,
    isApplying: false,
    isLoading: false,
    model: providerTruth.modelLabel,
    previewStatus: "not started",
    provider: providerTruth.providerLabel,
    providerCallAuthorized: providerTruth.providerCallAuthorized,
    providerCallMade: providerTruth.providerCallMade,
    providerModelBlockedReason: providerTruth.blockedReason,
    providerModelApiBaseHost: providerTruth.providerModelApiBaseHost,
    providerModelProbeOk: providerTruth.providerModelProbeOk,
    providerModelSelectedVia: providerTruth.providerModelSelectedVia,
    providerModelSource: providerTruth.source,
    providerModelStatus: providerTruth.status,
    configuredModelIsHermes: providerTruth.configuredModelIsHermes,
    hermesLaneAvailable: providerTruth.hermesLaneAvailable,
    hermesUsedForThisRun: providerTruth.hermesUsedForThisRun,
    requirementSummary: "Waiting for preview.",
    reasonCode: null,
    reviewerSummary: "Waiting for preview.",
    routeCalled: null,
    selectedTarget: null,
    status: "idle",
    targetCandidates: [],
    targetMatch: false,
    taskId: "",
    taskSpecAllowed: false,
    verifierSummary: "Waiting for preview.",
    technicalDetail: null,
  };
}

function providerTruthForPreviewState(
  previewState: PreviewState,
  configuredTruth?: CodingProviderModelTruth | null,
): CodingProviderModelTruth {
  return providerTruthFromPreviewState(previewState, configuredTruth);
}

function providerTruthPatch(providerTruth: CodingProviderModelTruth) {
  return {
    hermesLaneAvailable: providerTruth.hermesLaneAvailable,
    hermesUsedForThisRun: providerTruth.hermesUsedForThisRun,
    model: providerTruth.modelLabel,
    provider: providerTruth.providerLabel,
    providerCallAuthorized: providerTruth.providerCallAuthorized,
    providerCallMade: providerTruth.providerCallMade,
    providerModelBlockedReason: providerTruth.blockedReason,
    providerModelApiBaseHost: providerTruth.providerModelApiBaseHost,
    providerModelProbeOk: providerTruth.providerModelProbeOk,
    providerModelSelectedVia: providerTruth.providerModelSelectedVia,
    providerModelSource: providerTruth.source,
    providerModelStatus: providerTruth.status,
    configuredModelIsHermes: providerTruth.configuredModelIsHermes,
  };
}

function selectedProviderModelTruth(): CodingProviderModelTruth {
  return localHermesProviderModelTruth();
}

function reversibleTrialPromptForMode(prompt: ReversibleTrialPrompt, mode: AgentTrialMode): string {
  if (prompt.expectedOutcome === "clarify_expected") {
    return prompt.prompt;
  }
  if (prompt.expectedOutcome === "safety_block_expected") {
    return prompt.prompt;
  }
  if (prompt.expectedOutcome === "manual_step_expected") {
    return prompt.prompt;
  }
  if (mode === "design") {
    return prompt.prompt;
  }
  if (mode === "hybrid") {
    return prompt.prompt;
  }
  return prompt.prompt;
}

function visiblePromptExpectationTag(expectedOutcome: ReversibleTrialPrompt["expectedOutcome"]): string {
  if (expectedOutcome === "noop_expected") return "no edit expected";
  if (expectedOutcome === "clarify_expected") return "clarification expected";
  if (expectedOutcome === "safety_block_expected") return "safety block expected";
  if (expectedOutcome === "manual_step_expected") return "manual step expected";
  return "edit expected";
}

function trialCategoryForMode(mode: AgentTrialMode): ReversibleTrialCategory {
  if (mode === "design") return "Designer";
  if (mode === "hybrid") return "Combined";
  return "Coder";
}

function modeForTrialCategory(category: ReversibleTrialCategory): AgentTrialMode {
  if (category === "Designer") return "design";
  if (category === "Combined") return "hybrid";
  return "code";
}

function splitFiles(value: string): string[] {
  return splitLinesOrCommas(value)
    .map((item) => normalizeRepoPath(item))
    .filter(Boolean);
}

function splitLinesOrCommas(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizeRepoPath(path: string): string {
  const trimmed = path.trim().replace(/\\/g, "/");
  if (trimmed.endsWith("/") && /\.[A-Za-z0-9]+$/.test(trimmed.slice(0, -1))) {
    return trimmed.slice(0, -1);
  }
  return trimmed;
}

function isProtectedTarget(value: string): boolean {
  const target = value.trim().toLowerCase();
  return (
    target === ".env" ||
    target.startsWith(".env.") ||
    target.includes("/.env") ||
    target === "source_proxy/data" ||
    target.startsWith("source_proxy/data/") ||
    target === "backend/volumes" ||
    target.startsWith("backend/volumes/") ||
    target === "backend/searxng_data" ||
    target.startsWith("backend/searxng_data/") ||
    target === ".spirit-backups" ||
    target.startsWith(".spirit-backups/") ||
    target.includes("secret") ||
    target.includes("certificate") ||
    target.includes("credentials") ||
    target.startsWith("/") ||
    target.includes("..")
  );
}

function isSafeRepoPath(value: string): boolean {
  const target = normalizeRepoPath(value);
  const lowerTarget = target.toLowerCase();
  return Boolean(
    target &&
      !target.startsWith("/") &&
      !target.split("/").includes("..") &&
      lowerTarget !== ".env" &&
      !lowerTarget.startsWith(".env.") &&
      !lowerTarget.startsWith("source_proxy/data/") &&
      lowerTarget !== "source_proxy/data" &&
      !lowerTarget.startsWith("backend/volumes/") &&
      lowerTarget !== "backend/volumes" &&
      !lowerTarget.startsWith("backend/searxng_data/") &&
      lowerTarget !== "backend/searxng_data" &&
      !lowerTarget.startsWith(".spirit-backups/") &&
      lowerTarget !== ".spirit-backups" &&
      !lowerTarget.includes("secret") &&
      !lowerTarget.includes("credential"),
  );
}

function reverseUnifiedDiff(diff: string): string {
  return diff
    .split("\n")
    .map((line) => {
      if (line.startsWith("+") && !line.startsWith("+++")) {
        return `-${line.slice(1)}`;
      }
      if (line.startsWith("-") && !line.startsWith("---")) {
        return `+${line.slice(1)}`;
      }
      return line;
    })
    .join("\n");
}

function reverseDiffForReceipt(receipt: AppliedRunReceipt): string {
  if (receipt.id.startsWith("trial-reset:") || receipt.id.startsWith("trial-suite:")) {
    if (receipt.reverseDiff.trim()) {
      return receipt.reverseDiff;
    }
  }
  const rebuiltReverseDiff = reverseUnifiedDiff(receipt.diff);
  return rebuiltReverseDiff.trim() ? rebuiltReverseDiff : receipt.reverseDiff;
}

function buildReverseTaskDescription(
  receipt: AppliedRunReceipt,
  changedFiles: string[],
  allowedFiles: string[],
): string {
  const target = normalizeRepoPath(receipt.target) || changedFiles[0] || allowedFiles[0] || "unknown";
  return [
    "Revert previously applied manual coding trial run.",
    `Target file: ${target}`,
    `Changed files: ${changedFiles.join(", ")}`,
    `Allowed files: ${allowedFiles.join(", ")}`,
    "Restore the pre-trial baseline by applying exactly the approved reverse diff.",
    "This is cleanup for an applied trial receipt, not a new feature request.",
  ].join("\n");
}

function appliedRunReceiptFingerprint(receipt: Pick<AppliedRunReceipt, "appliedAt" | "diff" | "target">): string {
  return `${receipt.target}::${receipt.diff}::${receipt.appliedAt}`;
}

function appendAppliedRunReceipt(receipts: AppliedRunReceipt[], receipt: AppliedRunReceipt): AppliedRunReceipt[] {
  const fingerprint = appliedRunReceiptFingerprint(receipt);
  const withoutDupes = receipts.filter((item) => appliedRunReceiptFingerprint(item) !== fingerprint);
  return [...withoutDupes, receipt].slice(-25);
}

function loadStoredAppliedRunReceipts(): AppliedRunReceipt[] {
  if (typeof window === "undefined") return [];
  try {
    const parsed = JSON.parse(window.localStorage.getItem(appliedRunReceiptStorageKey) ?? "[]");
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is AppliedRunReceipt => {
      const receipt = asRecord(item);
      return Boolean(
        stringValue(receipt.id) &&
          stringValue(receipt.diff) &&
          stringValue(receipt.reverseDiff) &&
          stringValue(receipt.appliedAt) &&
          Array.isArray(receipt.allowedFiles) &&
          Array.isArray(receipt.changedFiles),
      );
    });
  } catch {
    return [];
  }
}

function storeAppliedRunReceipts(receipts: AppliedRunReceipt[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(appliedRunReceiptStorageKey, JSON.stringify(receipts));
}

function loadPromptHistory(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const parsed = JSON.parse(window.localStorage.getItem(promptHistoryStorageKey) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function storePromptHistory(history: string[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(promptHistoryStorageKey, JSON.stringify(history.slice(-10)));
}

function receiptIsTrialRun(receipt: AppliedRunReceipt): boolean {
  return isTrialRunReceiptRecord({
    allowedFiles: receipt.allowedFiles,
    changedFiles: receipt.changedFiles,
  });
}

type TrialFixtureBaselines = {
  backendRoute: string | null;
  component: string | null;
};

function buildTrialFixtureResetReceiptFromDiff(
  target: string,
  resetDiff: string,
  receipt: {
    appliedAt: string;
    hermesUsedForThisRun?: boolean | null;
    idSuffix: string;
    model: string;
    prompt: string;
    provider: string;
    providerModelSource: string;
    providerModelStatus: string;
  },
): AppliedRunReceipt {
  return {
    allowedFiles: [target],
    appliedAt: receipt.appliedAt,
    changedFiles: [target],
    diff: reverseUnifiedDiff(resetDiff),
    hermesUsedForThisRun: receipt.hermesUsedForThisRun ?? null,
    id: `trial-reset:${target}:${receipt.idSuffix}`,
    model: receipt.model,
    prompt: receipt.prompt,
    provider: receipt.provider,
    providerModelSource: receipt.providerModelSource,
    providerModelStatus: receipt.providerModelStatus,
    revertedAt: null,
    reversalModel: null,
    reversalProvider: null,
    reversalProviderModelSource: null,
    reverseDiff: resetDiff,
    target,
    taskId: "",
  };
}

function buildTrialFixtureResetReceipt(
  previewState: PreviewState,
  prompt: string,
): AppliedRunReceipt | null {
  if (previewState.status !== "satisfied" || previewState.reasonCode !== "coder_no_changes_needed") {
    return null;
  }
  const target = previewState.selectedTarget ?? "";
  const text = prompt.toLowerCase();
  if (
    target === COMPONENT_TRIAL_FIXTURE_PATH &&
    /warning[- ]?ish|warning tone|warning state|support warning|partial results|warning/.test(text)
  ) {
    return buildTrialFixtureResetReceiptFromDiff(
      target,
      componentTrialResetDiff(target),
      {
        appliedAt: "baseline-already-satisfied",
        hermesUsedForThisRun: previewState.hermesUsedForThisRun ?? null,
        idSuffix: "warning-tone",
        model: previewState.model ?? "not recorded",
        prompt: prompt.trim(),
        provider: previewState.provider ?? "not recorded",
        providerModelSource: previewState.providerModelSource ?? "unknown",
        providerModelStatus: previewState.providerModelStatus ?? "unknown",
      },
    );
  }
  if (
    target === BACKEND_ROUTE_TRIAL_FIXTURE_PATH &&
    /failure path|ok=false|failure case|ok true|non-200|happy response|sad path/.test(text)
  ) {
    return buildTrialFixtureResetReceiptFromDiff(
      target,
      backendRouteTrialResetDiff(target),
      {
        appliedAt: "baseline-already-satisfied",
        hermesUsedForThisRun: previewState.hermesUsedForThisRun ?? null,
        idSuffix: "ok-param",
        model: previewState.model ?? "not recorded",
        prompt: prompt.trim(),
        provider: previewState.provider ?? "not recorded",
        providerModelSource: previewState.providerModelSource ?? "unknown",
        providerModelStatus: previewState.providerModelStatus ?? "unknown",
      },
    );
  }
  return null;
}

function buildDummyTrialBaselineResetReceipt(
  target: string,
  sourceReceipt: Pick<
    AppliedRunReceipt,
    "appliedAt" | "hermesUsedForThisRun" | "model" | "provider" | "providerModelSource" | "providerModelStatus"
  >,
  _baselines: TrialFixtureBaselines,
): AppliedRunReceipt | null {
  const normalized = normalizeRepoPath(target);
  const resetDiff = dummyTrialBaselineResetDiff(normalized);
  if (!resetDiff) {
    return null;
  }
  const idSuffix = normalized.split("/").pop()?.replace(/\.[^.]+$/, "") ?? "baseline-reset";

  return buildTrialFixtureResetReceiptFromDiff(normalized, resetDiff, {
    appliedAt: sourceReceipt.appliedAt,
    hermesUsedForThisRun: sourceReceipt.hermesUsedForThisRun,
    idSuffix,
    model: sourceReceipt.model ?? "not recorded",
    prompt: `Reset dummy trial fixture to baseline for ${target}.`,
    provider: sourceReceipt.provider ?? "not recorded",
    providerModelSource: sourceReceipt.providerModelSource,
    providerModelStatus: sourceReceipt.providerModelStatus,
  });
}

function buildKnownTrialFixtureResetReceipts(baselines: TrialFixtureBaselines): AppliedRunReceipt[] {
  const providerTruth = selectedProviderModelTruth();
  const receipts: AppliedRunReceipt[] = [];
  if (baselines.component && componentTrialHasWarningTone(baselines.component)) {
    receipts.push(
      buildTrialFixtureResetReceiptFromDiff(
        COMPONENT_TRIAL_FIXTURE_PATH,
        componentTrialResetDiff(),
        {
          appliedAt: "known-trial-fixture-reset",
          hermesUsedForThisRun: providerTruth.hermesUsedForThisRun,
          idSuffix: "warning-tone",
          model: providerTruth.modelLabel,
          prompt: "Reset known dummy badge warning fixture for rerunnable trial prompts.",
          provider: providerTruth.providerLabel,
          providerModelSource: providerTruth.source,
          providerModelStatus: providerTruth.status,
        },
      ),
    );
  }
  if (baselines.backendRoute && backendRouteTrialHasOkParam(baselines.backendRoute)) {
    receipts.push(
      buildTrialFixtureResetReceiptFromDiff(
        BACKEND_ROUTE_TRIAL_FIXTURE_PATH,
        backendRouteTrialResetDiff(),
        {
          appliedAt: "known-trial-fixture-reset",
          hermesUsedForThisRun: providerTruth.hermesUsedForThisRun,
          idSuffix: "ok-param",
          model: providerTruth.modelLabel,
          prompt: "Reset known dummy backend route ok-param fixture for rerunnable trial prompts.",
          provider: providerTruth.providerLabel,
          providerModelSource: providerTruth.source,
          providerModelStatus: providerTruth.status,
        },
      ),
    );
  }
  return receipts;
}

function buildAllDummyTrialBaselineResetReceipts(): AppliedRunReceipt[] {
  const providerTruth = selectedProviderModelTruth();
  const receipts: AppliedRunReceipt[] = [];
  for (const target of DUMMY_TRIAL_EDIT_FIXTURE_TARGETS) {
    for (const [index, resetDiff] of dummyTrialBaselineResetDiffs(target).entries()) {
      receipts.push(
        buildTrialFixtureResetReceiptFromDiff(target, resetDiff, {
          appliedAt: "known-trial-fixture-reset",
          hermesUsedForThisRun: providerTruth.hermesUsedForThisRun,
          idSuffix: `baseline-${index + 1}`,
          model: providerTruth.modelLabel,
          prompt: `Reset ${target} to its dummy trial baseline.`,
          provider: providerTruth.providerLabel,
          providerModelSource: providerTruth.source,
          providerModelStatus: providerTruth.status,
        }),
      );
    }
  }
  return receipts;
}

function inferRelatedPage(path: string): { href: string | null; note: string } {
  const safePath = normalizeRepoPath(path);
  if (!isSafeRepoPath(safePath)) {
    return {
      href: null,
      note: "Path is not a safe repo-relative file target. Verify manually before opening.",
    };
  }
  if (safePath.startsWith("src/app/api/")) {
    return { href: null, note: "No related page inferred for API route files. Verify the file directly." };
  }
  if (safePath.startsWith("tests/")) {
    return { href: null, note: "No related page inferred for test or fixture files. Verify the file directly." };
  }
  if (safePath.startsWith("src/components/")) {
    return { href: null, note: "No related page inferred for component files. Verify the file directly." };
  }
  const appMatch = safePath.match(/^src\/app\/(.+?)\/(page|layout)\.tsx$/);
  if (safePath === "src/app/page.tsx") {
    return { href: "/", note: "Related page inferred from src/app/page.tsx." };
  }
  if (!appMatch) {
    return { href: null, note: "No related page inferred. Verify the file directly." };
  }
  const segments = appMatch[1]
    .split("/")
    .filter((segment) => segment && !segment.startsWith("(") && !segment.startsWith("@"));
  const href = segments.length > 0 ? `/${segments.join("/")}` : "/";
  return {
    href,
    note: `Related page inferred from ${appMatch[2]}.tsx route file.`,
  };
}

function buildVerificationTargets(previewState: PreviewState): VerificationTarget[] {
  const sourcePaths =
    previewState.changedFiles.length > 0
      ? previewState.changedFiles
      : changedFilesFromDiffPreview(previewState.diff).length > 0
        ? changedFilesFromDiffPreview(previewState.diff)
        : previewState.selectedTarget
          ? [previewState.selectedTarget]
          : [];

  return Array.from(new Set(sourcePaths.map((path) => normalizeRepoPath(path)).filter(Boolean))).map((path) => {
    const safe = isSafeRepoPath(path);
    const relatedPage = inferRelatedPage(path);
    return {
      fileOpenAvailable: false,
      path,
      relatedPageHref: safe ? relatedPage.href : null,
      routeInferenceNote: relatedPage.note,
      safe,
    };
  });
}

function taskMentionsProtectedPath(value: string): boolean {
  const text = value.toLowerCase();
  return (
    /(^|\s)\.env(\.local)?(\s|$|,|\.|\/)/.test(text) ||
    text.includes("source_proxy/data") ||
    text.includes("backend/volumes") ||
    text.includes("backend/searxng_data") ||
    text.includes(".spirit-backups") ||
    text.includes("secret") ||
    text.includes("credential")
  );
}

function taskMentionsWrongFileScopeConflict(value: string): boolean {
  const text = value.toLowerCase();
  const pointsAtProductionOrPackage =
    text.includes("codingcommandcentershell") ||
    text.includes("package json") ||
    text.includes("package.json") ||
    text.includes("global css");
  return pointsAtProductionOrPackage && (
    text.includes("allowed file should only") ||
    text.includes("block if") ||
    text.includes("wrong file")
  );
}

function buildManualTaskPacket({
  allowedFilesText,
  expectedChecksText,
  prompt,
  targetFile,
}: {
  allowedFilesText: string;
  expectedChecksText: string;
  prompt: string;
  targetFile: string;
}): ManualTaskPacket {
  const normalizedTarget = normalizeRepoPath(targetFile);
  const explicitAllowedFiles = splitFiles(allowedFilesText);
  const checks = splitLinesOrCommas(expectedChecksText);
  const forbiddenFiles = PROTECTED_FORBIDDEN_FILES;
  const targetCandidates = discoverManualTargetCandidates(prompt, normalizedTarget);
  const selectedTarget = normalizedTarget || targetCandidates[0] || null;
  const allowedFiles = explicitAllowedFiles.length > 0
    ? explicitAllowedFiles
    : selectedTarget
      ? [selectedTarget]
      : [];
  const reasonCode = taskMentionsProtectedPath(prompt) || isProtectedTarget(normalizedTarget)
    ? "protected_path_request"
    : taskMentionsWrongFileScopeConflict(prompt)
      ? "wrong_file_scope_conflict"
    : selectedTarget
      ? null
      : "manual_clarification_needed";

  return {
    allowedFiles,
    checks: checks.length > 0 ? checks : ["git diff --check"],
    forbiddenFiles,
    reasonCode,
    selectedTarget,
    targetCandidates,
    taskText: prompt.trim(),
  };
}

function discoverManualTargetCandidates(prompt: string, explicitTarget: string): string[] {
  const candidates = new Set<string>();
  if (explicitTarget) candidates.add(explicitTarget);

  for (const filePath of prompt.match(/[A-Za-z0-9_./-]+\.(?:tsx|ts|js|jsx|py|md|css|json|mjs)/g) ?? []) {
    const normalized = normalizeRepoPath(filePath);
    if (normalized && !isProtectedTarget(normalized)) candidates.add(normalized);
  }

  const text = prompt.toLowerCase();
  if (/\/coding|coding page|coding screen|coding cockpit|composer|start task|blocked task|backend-looking|backend junk|copy diagnostics|advanced details|task copy|progress|transcript|coding result card|result card|live apply run fails|next-step sentence/.test(text)) {
    candidates.add("src/components/coding/CodingCockpitShell.tsx");
    candidates.add("src/components/coding/__tests__/coding-cockpit-shell.test.tsx");
  }
  if (/soccer|scouting|scout|agent card|intelligence agent/.test(text)) {
    candidates.add("src/components/dashboard/ScoutIntelligenceCenter.tsx");
    candidates.add("src/components/dashboard/HomelabScoutIntelligenceWidget.tsx");
  }
  if (/source sidebar|sidebar selected|selected state|voidcore/.test(text)) {
    candidates.add("src/components/chat/ChatThreadListItem.tsx");
    candidates.add("src/components/chat/ChatThreadSidebar.tsx");
  }
  if (/oracle|daily briefing|quick action|briefing preparation/.test(text)) {
    candidates.add("src/components/dashboard/OracleStagePanel.tsx");
    candidates.add("src/components/chat/SpiritChat.tsx");
  }
  if (/trial runner|coder 10|prompt 1|agent trial|manual retest/.test(text)) {
    candidates.add("src/lib/coding/agent-trials-ui.ts");
    candidates.add("src/components/coding/CodingCockpitShell.tsx");
  }
  if (
    /badge component|small badge|warning state|tiny badge|badge helper|dummy trial|trial bits|warning-ish|warning tone/.test(
      text,
    )
  ) {
    candidates.add("tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx");
    candidates.add("tests/ui-agent-trials/fixtures/dummy-coding-targets/readme-trial.md");
  }
  if (text.includes("codingcommandcentershell")) {
    candidates.add("src/components/coding/CodingCommandCenterShell.tsx");
  }
  if (text.includes("package json") || text.includes("package.json")) {
    candidates.add("package.json");
  }
  if (/fake route|route helper|dummy backend|sad path|ok=false|ok true|failure case/.test(text)) {
    candidates.add("tests/ui-agent-trials/fixtures/dummy-coding-targets/backend-route-trial.ts");
  }
  if (/dummy readme|trial edits prod|preview-only/.test(text)) {
    candidates.add("tests/ui-agent-trials/fixtures/dummy-coding-targets/readme-trial.md");
  }
  if (/no-diff|already-satisfied|already satisfied/.test(text)) {
    candidates.add("tests/ui-agent-trials/fixtures/dummy-coding-targets/no-diff-trial.json");
  }
  if (/productive previews|classifies productive previews|trial ui test/.test(text)) {
    candidates.add("src/lib/coding/__tests__/agent-trials-ui.test.ts");
    candidates.add("src/lib/coding/agent-trials-ui.ts");
  }
  if (/\/coding page|coding route/.test(text)) {
    candidates.add("src/app/coding/page.tsx");
    candidates.add("src/app/coding/__tests__/page.test.tsx");
  }
  if (/source proxy|preview route|prompt-packet|diff-preview|long-running/.test(text)) {
    candidates.add("source_proxy/api/action_preview.py");
    candidates.add("source_proxy/api/long_running_tasks.py");
    candidates.add("source_proxy/tasks/long_running.py");
  }
  if (/\bthat label\b|yesterday|like we talked about/.test(text) && candidates.size === 0) {
    return [];
  }

  return Array.from(candidates);
}

function nextSafeActionText({
  draftReady,
  previewState,
}: {
  draftReady: boolean;
  previewState: PreviewState;
}) {
  if (!draftReady) {
    return "Write the task, then start the task. File discovery happens during the run.";
  }
  if (previewState.isLoading) {
    return "Wait for the current preview run to finish. No files have been changed.";
  }
  if (previewState.status === "idle") {
    return "Start the task to discover likely files and build the preview packet.";
  }
  if (previewState.status === "applied") {
    return "Applied, verification required. Commit and push are not available here.";
  }
  if (previewState.status === "approved") {
    return "Apply the approved diff, or reject and restart. Approval alone has not changed files.";
  }
  if (previewState.status === "ready" && previewState.approvalAvailable) {
    return "Review the approval gates, then approve. Approval is required before apply.";
  }
  if (previewState.status === "ready" && previewState.reasonCode === "preview_only_no_apply_requested") {
    return "Preview ready. Apply is disabled because the prompt requested preview-only or no apply.";
  }
  if (previewState.status === "satisfied") {
    return "No diff is required. The target already appears to satisfy the task. No files have been changed.";
  }
  if (previewState.reasonCode === "manual_clarification_needed") {
    return "Add the missing context in the prompt, then start again. No files have been changed.";
  }
  if (previewState.reasonCode === "protected_path_request") {
    return "Choose a non-protected product or source file. Protected paths were not inspected or changed.";
  }
  if (previewState.reasonCode === "wrong_file_scope_conflict") {
    return "Retry with the intended dummy fixture only. The conflicting production/package targets were not inspected or changed.";
  }
  return "Resolve the reported blocker, then retry. No files have been changed.";
}

function isUsefulClarificationBlock(previewState: PreviewState): boolean {
  return (
    previewState.reasonCode === "manual_clarification_needed" ||
    previewState.technicalDetail === "manual_clarification_needed"
  );
}

function isExpectedSafetyBlock(previewState: PreviewState): boolean {
  const code = previewState.reasonCode ?? previewState.technicalDetail ?? "";
  return code === "wrong_file_scope_conflict" || code === "protected_path_request";
}

function diagnosticsHandoffTag(
  previewState: PreviewState,
  applyPreflightNeedsFix: boolean,
): { label: string; tone: "clarify" | "fix" | "record" | "safe" } {
  if (isUsefulClarificationBlock(previewState)) {
    return { label: "Clarify", tone: "clarify" };
  }
  if (isExpectedSafetyBlock(previewState)) {
    return { label: "Safe block", tone: "safe" };
  }
  if (
    previewState.status === "blocked" ||
    previewState.status === "error" ||
    Boolean(previewState.error) ||
    applyPreflightNeedsFix
  ) {
    return { label: "Needs fix", tone: "fix" };
  }
  return { label: "Record", tone: "record" };
}

function reversibleResultTagClass(label: ReversibleSuitePromptResult["visible_result_label"]): string {
  if (label === "PASS") return "border-emerald-300/70 bg-emerald-300/15 text-emerald-100";
  if (label === "REVERTED") return "border-cyan-300/70 bg-cyan-300/15 text-cyan-100";
  if (label === "ALREADY SATISFIED") return "border-lime-300/70 bg-lime-300/15 text-lime-100";
  if (label === "NO EDIT EXPECTED") return "border-sky-300/60 bg-sky-300/15 text-sky-100";
  if (label === "BLOCKED") return "border-amber-300/70 bg-amber-300/15 text-amber-100";
  return "border-rose-300/70 bg-rose-300/15 text-rose-100";
}

function readableTaskState(previewState: PreviewState, draftReady: boolean): string {
  if (previewState.isLoading) return "Working";
  if (previewState.status === "applied") return "Finished";
  if (previewState.status === "approved") return "Approved, not applied";
  if (previewState.status === "ready") return "Preview ready";
  if (previewState.status === "satisfied") return "Already satisfied";
  if (isUsefulClarificationBlock(previewState)) return "Needs clarification";
  if (isExpectedSafetyBlock(previewState)) return "Blocked safely";
  if (previewState.status === "blocked" || previewState.status === "error") return "Failed";
  if (draftReady) return "Needs input";
  return "Ready";
}

function trialVerdictBadgeClass(verdict: "FAIL" | "PASS" | "PENDING" | "UNKNOWN") {
  if (verdict === "PASS") {
    return "border-emerald-300/40 bg-emerald-300/10 text-emerald-100";
  }
  if (verdict === "FAIL") {
    return "border-red-300/40 bg-red-300/10 text-red-100";
  }
  if (verdict === "PENDING") {
    return "border-slate-300/40 bg-slate-300/10 text-slate-200";
  }
  return "border-[var(--ddv4-pill-border)] text-[var(--ddv4-fg-muted)]";
}

function designTaskKind(task: string) {
  const text = task.toLowerCase();
  if (
    /dummy|patch|support warning|route helper|no-diff|already-satisfied|badge|warning state|implementation|fix the|change the/.test(
      text,
    )
  ) {
    return null;
  }
  if (/responsive|mobile|tablet|viewport/.test(text)) return "responsive";
  // "component" alone is too broad for coding prompts (e.g. "badge component").
  if (/\bhandoff\b|component map|component hierarchy|mapping/.test(text)) return "handoff";
  if (/design|visual|critique|layout|screen/.test(text)) return "critique";
  return null;
}

function designResultText({
  kind,
  target,
}: {
  kind: NonNullable<ReturnType<typeof designTaskKind>>;
  target: string;
}) {
  if (kind === "responsive") {
    return [
      "Findings: desktop and mobile context are both represented; the main risk is controls moving below the reading flow on small screens.",
      "Suggested changes: keep the primary task surface first, keep runner controls compact, and recheck mobile tap targets.",
      `Target context: ${target}.`,
      "Confidence: medium; this is a product-surface design check, not a visual polish pass.",
    ].join("\n");
  }
  if (kind === "handoff") {
    return [
      "Findings: the request is a design handoff. The useful output is a compact component map plus likely implementation boundary.",
      "Suggested changes: name the screen, affected component, expected behavior, and one verification check before coding starts.",
      `Target context: ${target}.`,
      "Confidence: medium; this is ready as handoff context, not an implementation command.",
    ].join("\n");
  }
  return [
    "Findings: the screen needs a readable visual critique with the main issue, likely user impact, and a bounded next change.",
    "Suggested changes: prioritize hierarchy, scan order, and primary action clarity before decorative polish.",
    `Target context: ${target}.`,
    "Confidence: medium; this is a product-surface critique, not raw artifact evidence.",
  ].join("\n");
}

function isCombinedTask(task: string) {
  const text = task.toLowerCase();
  return (
    /combined|design[- ]?to[- ]?code|code[- ]?to[- ]?design|designer.*coder|coder.*designer|recheck/.test(text) ||
    (/design|critique|visual|responsive/.test(text) && /code|implement|fix|change|recheck/.test(text))
  );
}

export function CodingCockpitShell() {
  const stopReversibleSuiteAfterCurrentRef = useRef(false);
  const reversibleSuiteClearVersionRef = useRef(0);
  const [task, setTask] = useState("");
  const [targetFile, setTargetFile] = useState("");
  const [allowedFiles, setAllowedFiles] = useState("");
  const [expectedChecks, setExpectedChecks] = useState("git diff --check");
  const [draftReady, setDraftReady] = useState(false);
  const [previewState, setPreviewState] = useState<PreviewState>(() => idlePreviewState());
  const [diagnosticCopyStatus, setDiagnosticCopyStatus] = useState("");
  const [verificationCopyStatus, setVerificationCopyStatus] = useState("");
  const [trialMode, setTrialMode] = useState<AgentTrialMode>("code");
  const [trialProofMode, setTrialProofMode] = useState<AgentTrialProofMode>("live_apply");
  const [trialApplyStrategy, setTrialApplyStrategy] = useState<AgentTrialApplyStrategy>("hold_for_inspection");
  const [trialBank, setTrialBank] = useState<AgentTrialBank>("actual-intelligence");
  const [trialRunSize, setTrialRunSize] = useState<AgentTrialRunSize>(10);
  const [trialViewport, setTrialViewport] = useState<AgentTrialViewport>("desktop");
  const [trialCopyStatus, setTrialCopyStatus] = useState("");
  const [trialRunState, setTrialRunState] = useState<TrialRunState>("idle");
  const [reversibleTrialCategory, setReversibleTrialCategory] = useState<ReversibleTrialCategory>("Coder");
  const [reversiblePromptsCopyStatus, setReversiblePromptsCopyStatus] = useState("");
  const [reversibleSuiteCopyStatus, setReversibleSuiteCopyStatus] = useState("");
  const [reversibleSuiteState, setReversibleSuiteState] = useState<ReversibleSuiteState>(
    () => defaultReversibleSuiteState(),
  );
  const [reversibleTrialCount, setReversibleTrialCount] = useState<ReversibleTrialCount>(10);
  const [composerTiming, setComposerTiming] = useState<ComposerTimingState>({
    diffPreviewMs: null,
    promptPacketMs: null,
    runStartedAt: null,
    totalMs: null,
  });
  const [designReportCopyStatus, setDesignReportCopyStatus] = useState("");
  const [combinedCopyStatus, setCombinedCopyStatus] = useState("");
  const [appliedRunReceipts, setAppliedRunReceipts] = useState<AppliedRunReceipt[]>([]);
  const [promptHistory, setPromptHistory] = useState<string[]>([]);
  const [lastPromptSnapshot, setLastPromptSnapshot] = useState("");
  const [reversalStatus, setReversalStatus] = useState("");
  const [isReverting, setIsReverting] = useState(false);
  const [hasBrowserMounted, setHasBrowserMounted] = useState(process.env.NODE_ENV === "test");
  const [selectedProviderTruth, setSelectedProviderTruth] = useState<CodingProviderModelTruth>(() =>
    selectedProviderModelTruth(),
  );
  const [sourceProxyReachable, setSourceProxyReachable] = useState(process.env.NODE_ENV === "test");
  const [ollamaStoragePath, setOllamaStoragePath] = useState<string | null>(null);
  const [trialFixturesClean, setTrialFixturesClean] = useState<"yes" | "no" | "unknown">("unknown");
  const [lastProviderCallSmoke, setLastProviderCallSmoke] = useState<ProviderCallSmokeResult | null>(null);
  const [stressSmokeStatus, setStressSmokeStatus] = useState("");
  const [isRunningStressSmoke, setIsRunningStressSmoke] = useState(false);
  const [componentTrialContent, setComponentTrialContent] = useState<string | null>(null);
  const [backendRouteTrialContent, setBackendRouteTrialContent] = useState<string | null>(null);
  const trialFixtureBaselines = useMemo<TrialFixtureBaselines>(
    () => ({
      backendRoute: backendRouteTrialContent,
      component: componentTrialContent,
    }),
    [backendRouteTrialContent, componentTrialContent],
  );

  useEffect(() => {
    setAppliedRunReceipts(loadStoredAppliedRunReceipts());
    setPromptHistory(loadPromptHistory());
    setHasBrowserMounted(true);
  }, []);

  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    const stored = loadStoredReversibleSuiteState();
    setReversibleTrialCount(stored.count);
    setReversibleSuiteState((current) => {
      if (current.status !== "idle" || current.results.length > 0 || current.suiteId) {
        return current;
      }
      return stored;
    });
  }, []);

  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    if (reversibleSuiteState.status !== "done" && reversibleSuiteState.status !== "failed") {
      return;
    }
    if (!reversibleSuiteState.suiteId || reversibleSuiteState.results.length === 0) {
      return;
    }
    let cancelled = false;
    void (async () => {
      const clearVersion = reversibleSuiteClearVersionRef.current;
      const suiteReceipts = reversibleSuiteState.results
        .filter((result) => result.reversal_available)
        .map((result) => receiptForSuiteReverseResult(result, appliedRunReceipts));
      if (suiteReceipts.length === 0) {
        return;
      }
      const reconciled = await reconcileTrialReceiptsViaApi(suiteReceipts);
      if (cancelled || clearVersion !== reversibleSuiteClearVersionRef.current) {
        return;
      }
      updateAppliedRunReceipts((current) => {
        const merged = new Map(current.map((receipt) => [receipt.id, receipt]));
        for (const receipt of reconciled) {
          merged.set(receipt.id, receipt);
        }
        return [...merged.values()];
      });
      setReversibleSuiteState((current) => {
        if (current.suiteId !== reversibleSuiteState.suiteId) {
          return current;
        }
        return {
          ...current,
          results: alignSuiteResultsToDiskAndReverts(current.results, reconciled),
        };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [appliedRunReceipts, reversibleSuiteState.results.length, reversibleSuiteState.status, reversibleSuiteState.suiteId]);

  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    if (reversibleSuiteState.status === "idle" && reversibleSuiteState.results.length === 0) {
      return;
    }
    storeReversibleSuiteState(reversibleSuiteState);
  }, [reversibleSuiteState]);

  function clearReversibleSuitePanel() {
    reversibleSuiteClearVersionRef.current += 1;
    clearStoredReversibleSuiteState();
    updateAppliedRunReceipts((receipts) =>
      receipts.filter((receipt) => !receipt.id.startsWith("trial-suite:")),
    );
    setReversibleSuiteState(defaultReversibleSuiteState());
    setReversibleSuiteCopyStatus("Cleared trial suite results. Run again when ready.");
  }

  async function handleCleanUpTrialRunner() {
    if (isReverting || reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping") {
      return;
    }
    if (suitePendingRevertCount > 0) {
      await handleReverseRemainingTrialEdits({ clearSuiteAfter: true });
      return;
    }
    if (orphanUnrevertedTrialReceipts.length > 0) {
      await handleRevertAllTrialRuns({ clearSuiteAfter: true });
      return;
    }
    clearReversibleSuitePanel();
  }

  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    let cancelled = false;
    async function loadProviderTruth() {
      try {
        const response = await fetch("/v1/self/status", { method: "GET" });
        if (!response.ok) {
          if (!cancelled) setSourceProxyReachable(false);
          return;
        }
        const payload = await response.json() as unknown;
        const truth = providerModelTruthFromSelfStatus(payload);
        if (cancelled) return;
        setSourceProxyReachable(true);
        setOllamaStoragePath(ollamaStoragePathFromSelfStatus(payload));
        setSelectedProviderTruth(truth);
        setPreviewState((current) => {
          if (
            current.status !== "idle" ||
            current.isLoading ||
            current.isApplying ||
            (current.model && current.model !== "Unknown local model")
          ) {
            return current;
          }
          return {
            ...current,
            ...providerTruthPatch(truth),
          };
        });
      } catch {
        if (!cancelled) setSourceProxyReachable(false);
      }
    }
    void loadProviderTruth();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    if (!sourceProxyReachable) return;
    if (selectedProviderTruth.status === "unavailable" || selectedProviderTruth.providerModelProbeOk === false) {
      return;
    }
    setReversibleSuiteState((current) => {
      if (!isRecoverableModelLaneBlockedSuite(current)) return current;
      clearStoredReversibleSuiteState();
      return defaultReversibleSuiteState();
    });
  }, [selectedProviderTruth, sourceProxyReachable]);

  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    let cancelled = false;
    async function loadComponentTrialBaseline() {
      try {
        const response = await fetch("/v1/coding/trial-fixture-baseline", { method: "GET" });
        if (!response.ok) return;
        const payload = await response.json() as {
          backend_route_trial?: { excerpt?: string | null };
          component_trial?: { excerpt?: string | null };
          excerpt?: string | null;
        };
        if (cancelled) return;
        const componentExcerpt =
          typeof payload.component_trial?.excerpt === "string"
            ? payload.component_trial.excerpt
            : typeof payload.excerpt === "string"
              ? payload.excerpt
              : null;
        const backendExcerpt =
          typeof payload.backend_route_trial?.excerpt === "string"
            ? payload.backend_route_trial.excerpt
            : null;
        if (componentExcerpt) {
          setComponentTrialContent(componentExcerpt);
        }
        if (backendExcerpt) {
          setBackendRouteTrialContent(backendExcerpt);
        }
      } catch {
        // Baseline hydration is best-effort; static fixtures still render.
      }
    }
    void loadComponentTrialBaseline();
    return () => {
      cancelled = true;
    };
  }, []);

  const [hangTimerTick, setHangTimerTick] = useState(0);
  useEffect(() => {
    const active =
      previewState.isLoading ||
      previewState.isApplying ||
      reversibleSuiteState.status === "running" ||
      reversibleSuiteState.status === "stopping";
    if (!active) return;
    const id = window.setInterval(() => setHangTimerTick((value) => value + 1), 250);
    return () => window.clearInterval(id);
  }, [previewState.isApplying, previewState.isLoading, reversibleSuiteState.status]);
  void hangTimerTick;

  useEffect(() => {
    if (!previewState.isLoading || sourceProxyReachable) return;
    setPreviewState((current) => {
      if (!current.isLoading) return current;
      const stuckOnModelSpinner =
        current.currentPhase === manualTaskPhaseLabels.preview
        || current.currentPhase === "Calling model";
      if (!stuckOnModelSpinner) return current;
      return {
        ...current,
        currentPhase: "Source Proxy unreachable",
        error: current.error ?? "Source Proxy unreachable — backend failure.",
      };
    });
    setReversibleSuiteState((current) => {
      if (current.status !== "running" && current.status !== "stopping") return current;
      if (current.currentStep !== "Calling model") return current;
      return { ...current, currentStep: "Source Proxy unreachable" };
    });
  }, [previewState.isLoading, sourceProxyReachable]);

  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    if (appliedRunReceipts.length === 0) {
      setTrialFixturesClean("yes");
      return;
    }
    let cancelled = false;
    const clearVersion = reversibleSuiteClearVersionRef.current;
    async function reconcileReceipts() {
      try {
        const response = await fetch("/v1/coding/trial-receipt-reconcile", {
          body: JSON.stringify({ receipts: appliedRunReceipts }),
          headers: { "content-type": "application/json" },
          method: "POST",
        });
        if (!response.ok) return;
        const payload = await response.json() as {
          receipts?: AppliedRunReceipt[];
          trial_fixtures_clean?: "yes" | "no" | "unknown";
        };
        if (cancelled || clearVersion !== reversibleSuiteClearVersionRef.current) return;
        if (Array.isArray(payload.receipts)) {
          setAppliedRunReceipts(payload.receipts);
          storeAppliedRunReceipts(payload.receipts);
        }
        if (payload.trial_fixtures_clean) {
          setTrialFixturesClean(payload.trial_fixtures_clean);
        }
      } catch {
        if (!cancelled) setTrialFixturesClean("unknown");
      }
    }
    void reconcileReceipts();
    return () => {
      cancelled = true;
    };
  }, [appliedRunReceipts.length]);

  const allowedFileList = useMemo(() => splitFiles(allowedFiles), [allowedFiles]);
  const validationMessages = useMemo(() => {
    const messages: string[] = [];
    const trimmedTask = task.trim();
    const trimmedTarget = targetFile.trim();
    if (!trimmedTask) {
      messages.push("Task required");
    }
    return messages;
  }, [task]);
  const canPreview = validationMessages.length === 0;
  const hasTaskDraft = Boolean(task.trim());
  const protectedPathRequested = Boolean(
    (targetFile.trim() && isProtectedTarget(targetFile)) || taskMentionsProtectedPath(task),
  );
  const canStartTask = hasTaskDraft;
  const approvalControlsAvailable =
    previewState.status === "ready" &&
    previewState.approvalAvailable &&
    !previewState.blocker &&
    !previewState.error &&
    !previewState.isLoading;
  const applyControlsVisible =
    previewState.status === "approved" &&
    Boolean(previewState.approvedAt) &&
    Boolean(previewState.diff);
  const applyScopePreflight = useMemo(
    () => buildApplyScopePreflight(previewState),
    [previewState],
  );
  const currentAppliedRunReceipt = useMemo(() => {
    if (!previewState.appliedAt || !previewState.diff) return null;
    return (
      appliedRunReceipts.find(
        (receipt) =>
          receipt.appliedAt === previewState.appliedAt &&
          receipt.diff === previewState.diff &&
          receipt.revertedAt === null,
      ) ?? null
    );
  }, [appliedRunReceipts, previewState.appliedAt, previewState.diff]);
  const currentRunReceipt = useMemo(() => {
    if (!previewState.appliedAt || !previewState.diff) return null;
    return (
      appliedRunReceipts.find(
        (receipt) =>
          receipt.appliedAt === previewState.appliedAt &&
          receipt.diff === previewState.diff,
      ) ?? null
    );
  }, [appliedRunReceipts, previewState.appliedAt, previewState.diff]);
  useEffect(() => {
    if (previewState.status !== "applied" || !currentRunReceipt?.revertedAt) return;
    setPreviewState((current) => ({
      ...current,
      appliedAt: null,
      applySummary: "This run has already been reverted through Source Proxy scope checks.",
      currentPhase: manualTaskPhaseLabels.done,
      error: null,
      reasonCode: null,
      status: "ready",
      technicalDetail: null,
    }));
  }, [currentRunReceipt, previewState.status]);
  const currentTrialFixtureResetReceipt = useMemo(
    () => buildTrialFixtureResetReceipt(previewState, task),
    [previewState, task],
  );
  const currentReversalReceipt = currentAppliedRunReceipt ?? currentTrialFixtureResetReceipt;
  const availableTrialResetReceipts = useMemo(
    () => {
      const receipts = [
        ...(currentTrialFixtureResetReceipt ? [currentTrialFixtureResetReceipt] : []),
        ...buildKnownTrialFixtureResetReceipts(trialFixtureBaselines),
        ...buildAllDummyTrialBaselineResetReceipts(),
      ];
      return Array.from(new Map(receipts.map((receipt) => [receipt.id, receipt])).values());
    },
    [currentTrialFixtureResetReceipt, trialFixtureBaselines],
  );
  const unrevertedTrialRunReceipts = useMemo(
    () => appliedRunReceipts.filter((receipt) => receipt.revertedAt === null && !receipt.staleResolvedAt && receiptIsTrialRun(receipt)),
    [appliedRunReceipts],
  );
  const canRevertCurrentRun = Boolean(currentReversalReceipt && !isReverting);
  const currentReversalButtonLabel = currentTrialFixtureResetReceipt && !currentAppliedRunReceipt
    ? "Reset this trial fixture"
    : "Revert this run";
  const unrevertedSuiteResults = useMemo(
    () => latestUnrevertedSuiteResultsByTarget(reversibleSuiteState.results),
    [reversibleSuiteState.results],
  );
  const suiteAutoRevertedTargetCount = useMemo(() => {
    const targets = new Set<string>();
    for (const result of reversibleSuiteState.results) {
      if (!result.reversal_available || !result.reverted) {
        continue;
      }
      targets.add(suiteResultTargetKey(result));
    }
    return targets.size;
  }, [reversibleSuiteState.results]);
  const suiteAutoRevertedRowCount = useMemo(
    () =>
      reversibleSuiteState.results.filter((result) => result.reversal_available && result.reverted)
        .length,
    [reversibleSuiteState.results],
  );
  const activeSuitePromptIds = useMemo(
    () => new Set(reversibleSuiteState.results.map((result) => result.prompt.id)),
    [reversibleSuiteState.results],
  );
  const orphanUnrevertedTrialReceipts = useMemo(
    () =>
      unrevertedTrialRunReceipts.filter((receipt) => {
        if (
          reversibleSuiteState.results.some(
            (result) => receipt.id === suiteReceiptIdForResult(result),
          )
        ) {
          return false;
        }
        const supersededPromptId = suiteTrialPromptIdFromReceiptId(receipt.id);
        if (supersededPromptId && activeSuitePromptIds.has(supersededPromptId)) {
          return false;
        }
        return true;
      }),
    [activeSuitePromptIds, reversibleSuiteState.results, unrevertedTrialRunReceipts],
  );
  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    if (reversibleSuiteState.results.length === 0) return;
    const suiteReceiptIds = new Set(
      reversibleSuiteState.results.map((result) => suiteReceiptIdForResult(result)),
    );
    updateAppliedRunReceipts((receipts) => {
      let changed = false;
      const next = receipts.map((receipt) => {
        if (receipt.revertedAt || receipt.staleResolvedAt || !receipt.id.startsWith("trial-suite:")) {
          return receipt;
        }
        if (suiteReceiptIds.has(receipt.id)) {
          return receipt;
        }
        const promptId = suiteTrialPromptIdFromReceiptId(receipt.id);
        if (!promptId || !activeSuitePromptIds.has(promptId)) {
          return receipt;
        }
        changed = true;
        return {
          ...receipt,
          staleResolvedAt: new Date().toISOString(),
        };
      });
      return changed ? next : receipts;
    });
  }, [activeSuitePromptIds, reversibleSuiteState.results.length]);

  const suitePendingRevertReceiptCount =
    unrevertedSuiteResults.length + orphanUnrevertedTrialReceipts.length;
  const suitePendingRevertTargetCount = useMemo(() => {
    const targets = new Set<string>();
    for (const result of unrevertedSuiteResults) {
      targets.add(suiteResultTargetKey(result));
    }
    for (const receipt of orphanUnrevertedTrialReceipts) {
      targets.add(normalizeRepoPath(receipt.target));
    }
    return targets.size;
  }, [orphanUnrevertedTrialReceipts, unrevertedSuiteResults]);
  const suitePendingRevertCount = suitePendingRevertTargetCount;
  const suitePassReversibleRowCount = useMemo(
    () =>
      reversibleSuiteState.results.filter(
        (result) => result.reversal_available && result.visible_result_label === "PASS",
      ).length,
    [reversibleSuiteState.results],
  );
  const orphanRevertTargetCount = useMemo(() => {
    const targets = new Set<string>();
    for (const receipt of orphanUnrevertedTrialReceipts) {
      targets.add(normalizeRepoPath(receipt.target));
    }
    return targets.size;
  }, [orphanUnrevertedTrialReceipts]);
  const trialReversalCount =
    suitePendingRevertCount > 0
      ? suitePendingRevertCount + orphanRevertTargetCount
      : availableTrialResetReceipts.length;
  const canRevertTrialRuns = trialReversalCount > 0 && !isReverting;
  const reversibleSuiteBusy =
    reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping";
  const canCleanUpTrialRunner =
    !isReverting &&
    !reversibleSuiteBusy &&
    (reversibleSuiteState.results.length > 0 || canRevertTrialRuns || suitePendingRevertCount > 0);
  const trialReversalHelpText =
    suitePendingRevertCount > 0
      ? suitePassReversibleRowCount > suitePendingRevertTargetCount
        ? `Current suite made ${suitePendingRevertTargetCount} dummy fixture edit(s). Product-code PASS rows may be no-op checks; this button reverses fixtures and clears results.`
        : `Current suite made ${suitePendingRevertTargetCount} dummy fixture edit(s). This button reverses fixtures and clears results.`
      : canRevertTrialRuns
        ? orphanUnrevertedTrialReceipts.length > 0
          ? `${orphanUnrevertedTrialReceipts.length} stored trial run(s) can be reversed after refresh, then results will clear.`
          : `${availableTrialResetReceipts.length} dummy fixture baseline(s) can be reset, then results will clear.`
        : suiteAutoRevertedTargetCount > 0
          ? suiteAutoRevertedRowCount > suiteAutoRevertedTargetCount
            ? `Reversed ${suiteAutoRevertedTargetCount} fixture file(s) (${suiteAutoRevertedRowCount} catalog row(s) updated). Nothing left to undo.`
            : `${suiteAutoRevertedTargetCount} fixture file(s) reversed. Nothing left to undo.`
          : reversibleSuiteState.results.length > 0
            ? "No unreverted trial edits remain. Reset fixtures below if disk still looks edited."
            : "No applied trial edits to reverse.";
  const reversibleSuiteFinished =
    reversibleSuiteState.status === "done" || reversibleSuiteState.status === "failed";
  const reversibleSuiteCountMismatch =
    reversibleSuiteState.results.length > 0 && reversibleSuiteState.count !== reversibleTrialCount;
  const reversibleSuiteReversalPanel = (
    <>
      <button
        className={`mt-3 inline-flex min-h-10 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
        disabled={!canCleanUpTrialRunner}
        onClick={() => void handleCleanUpTrialRunner()}
        type="button"
      >
        {isReverting
          ? "Cleaning up trial run..."
          : canCleanUpTrialRunner
            ? "Reverse trial edits and clear results"
            : "Trial cleanup complete"}
      </button>
      <p className={`mt-2 text-xs ${commandMutedClass}`}>{trialReversalHelpText}</p>
    </>
  );
  const canRewindPrompt = promptHistory.length > 0 && !previewState.isLoading && !previewState.isApplying && !isReverting;
  const verificationTargets = useMemo(
    () => buildVerificationTargets(previewState),
    [previewState],
  );
  const canApplyApprovedDiff =
    applyControlsVisible &&
    !previewState.isApplying &&
    applyScopePreflight.reasonCode === null;
  const showWorkspaceEmpty =
    previewState.status === "idle" && !previewState.isLoading && !task.trim();
  const currentTaskTitle = task.trim() || "No active task";
  const currentTaskTarget =
    (previewState.selectedTarget ?? normalizeRepoPath(targetFile)) || "Discovering after start";
  const currentTaskState = readableTaskState(previewState, draftReady);
  const currentDesignTaskKind = designTaskKind(task);
  const showDesignerResult = Boolean(currentDesignTaskKind && draftReady && previewState.status === "idle");
  const showCombinedFlow = Boolean(isCombinedTask(task) && draftReady && previewState.status === "idle");
  const currentDesignResult = currentDesignTaskKind
    ? designResultText({ kind: currentDesignTaskKind, target: currentTaskTarget })
    : "";
  const combinedState = canPreview ? "Ready" : "Needs input";
  const combinedHandoffStatus = canPreview
    ? "Design output is ready for coder context; coder result will need a designer recheck."
    : "Design output is ready, but the request needs clarification before coder handoff.";
  const nextSafeAction = nextSafeActionText({
    draftReady,
    previewState,
  });
  const activeProviderTruth = providerTruthForPreviewState(previewState, selectedProviderTruth);
  const railTaskItems = [
    {
      label: "Active task",
      value: currentTaskState,
      active: true,
    },
    {
      label: "Needs input",
      value: previewState.approvalAvailable ? "1 task" : "None",
      active: previewState.approvalAvailable,
    },
    {
      label: "Failed",
      value:
        previewState.status === "blocked" || previewState.status === "error" ? "1 task" : "None",
      active: previewState.status === "blocked" || previewState.status === "error",
    },
    {
      label: "Finished",
      value: previewState.status === "applied" ? "Verify next" : "None",
      active: previewState.status === "applied",
    },
    {
      label: "Recent tasks",
      value: draftReady ? "Current draft" : "Empty",
      active: draftReady,
    },
  ];
  const visibleRailTaskItems = railTaskItems.filter(
    (item) => item.label === "Active task" || item.active,
  );
  const railScopeItems = [
    { label: "Focus", value: currentTaskTarget },
    {
      label: "Discovery",
      value: previewState.targetCandidates.length > 0
        ? `${previewState.targetCandidates.length} candidate${previewState.targetCandidates.length === 1 ? "" : "s"}`
        : "Runs after start",
    },
    { label: "Checks", value: previewState.checks.join(", ") || "Prepared after start" },
  ];
  const workspaceEmptyItems = [
    {
      label: "Write the task",
      value: "Describe the file change, bug fix, or small implementation you want next.",
    },
    {
      label: "Start discovery",
      value: "SpiritOS infers likely files and safety boundaries from the request.",
    },
    {
      label: "Start the run",
      value: "Use the primary action when the task is clear enough to begin.",
    },
    {
      label: "Track the result",
      value: "The transcript and status areas will update as the task moves forward.",
    },
  ];
  const transcriptItems = [
    {
      speaker: "You",
      body: task.trim() || "Ready for your next coding task.",
    },
    {
      speaker: "SpiritOS",
      body:
        draftReady && !canPreview && previewState.status === "idle"
          ? `I understand the task. I need ${validationMessages
              .filter((message) => message !== "Task required")
              .join(" and ")
              .toLowerCase()} resolved before I can run it.`
          : previewState.status === "idle" && !previewState.isLoading
            ? task.trim()
              ? "I understand the task. Press Start task and I will discover the likely files."
              : "Describe the task, then start it."
          : previewState.isLoading
            ? `${previewState.currentPhase}. No files have been changed.`
            : previewState.error ?? previewState.blocker ?? nextSafeAction,
    },
    ...(task.trim()
      ? [
          {
            speaker: "Understood task",
            body: `Task: ${task.trim()}\nFocus: ${currentTaskTarget}\nCurrent step: ${previewState.currentPhase}`,
          },
        ]
      : []),
    ...previewState.events.map((event) => ({
      speaker: event.label,
      body: event.detail,
    })),
    ...(showDesignerResult && currentDesignTaskKind
      ? [
          {
            speaker: "Designer result",
            body: currentDesignResult,
          },
        ]
      : []),
    ...(showCombinedFlow
      ? [
          {
            speaker: "Combined flow",
            body: [
              "Designer critique: ready as implementation context.",
              `Coder handoff: ${canPreview ? "ready for scoped preview" : "needs target and allowed files"}.`,
              "Designer recheck: pending after coder result.",
            ].join("\n"),
          },
        ]
      : []),
  ];
  const compactContextItems = [
    { label: "Project", value: "SpiritOS" },
    { label: "Task", value: currentTaskState },
    { label: "Target", value: currentTaskTarget },
    { label: "Provider", value: activeProviderTruth.providerLabel },
    { label: "Model", value: activeProviderTruth.modelLabel },
    { label: "Source", value: activeProviderTruth.source },
  ];
  const reviewPaneStatus =
    previewState.error ??
    previewState.blocker ??
    (previewState.isLoading
      ? "Previewing"
      : previewState.status === "idle"
        ? "No preview yet"
        : currentTaskState);
  const showMobileActionBar =
    Boolean(task.trim()) || draftReady || previewState.status !== "idle" || previewState.isLoading;
  const showCopyDiagnostics =
    previewState.status !== "idle" || previewState.isLoading;
  const applyPreflightNeedsFix =
    (previewState.status === "ready" || previewState.status === "approved" || previewState.status === "applied") &&
    Boolean(applyScopePreflight.reasonCode);
  const diagnosticsHandoff = diagnosticsHandoffTag(previewState, applyPreflightNeedsFix);
  const diagnosticsTag = diagnosticsHandoff.label;
  const diagnosticsTagTone = diagnosticsHandoff.tone;
  const currentChangedFilesDiagnostics = buildChangedFilesDiagnostics({
    appliedAt: previewState.appliedAt,
    diff: previewState.diff,
    status: previewState.status,
    verificationChangedFiles: previewState.changedFiles,
  });
  const currentPreviewProviderTruth = providerTruthForPreviewState(previewState, selectedProviderTruth);
  const currentSidecarClassification = classifyDiagnosticSidecar({
    approvalAvailable: previewState.approvalAvailable,
    changedFiles: currentChangedFilesDiagnostics.previewChangedFiles,
    previewDiffProduced: Boolean(previewState.diff.trim()),
    providerCallMade: currentPreviewProviderTruth.providerCallMade,
    providerCallRequired: false,
    providerModelStatus: currentPreviewProviderTruth.status,
    reasonCode: previewState.reasonCode,
    status: previewState.status,
    verificationPassed: previewState.status === "ready" || previewState.status === "approved",
  });
  const designVisibleResult = mapVisibleResultBadge({
    expected_behavior: "design critique",
    hermes_used_for_this_run: selectedProviderTruth.hermesUsedForRunStatus,
    model_called_for_generation: selectedProviderTruth.modelCalledForGeneration ?? "none",
    next_action: canPreview
      ? "Use as implementation context"
      : "Add missing target or allowed files, then rerun.",
    provider_call_made: selectedProviderTruth.providerCallMade,
    status: "design",
    visible_failure: canPreview ? "none visible" : validationMessages.join(", ") || "none visible",
  });
  const combinedVisibleResult = mapVisibleResultBadge({
    expected_behavior: "combined handoff",
    hermes_used_for_this_run: selectedProviderTruth.hermesUsedForRunStatus,
    model_called_for_generation: selectedProviderTruth.modelCalledForGeneration ?? "none",
    next_action: canPreview ? "Run the natural prompt preview, then request designer recheck." : "Clarify the task before coder handoff.",
    provider_call_made: selectedProviderTruth.providerCallMade,
    result_category: canPreview ? "productive_preview" : "blocked_missing_scope",
    status: canPreview ? "ready" : "blocked",
    visible_failure: canPreview ? "none visible" : validationMessages.join(", ") || "none visible",
  });
  const codingVisibleResult = mapVisibleResultBadge({
    actual_behavior:
      previewState.status === "blocked"
        ? "safe_block"
        : previewState.status === "error"
          ? "failed"
          : previewState.status === "satisfied"
            ? "already_satisfied_noop"
            : previewState.status === "ready" || previewState.status === "approved" || previewState.status === "applied"
              ? "productive_preview"
              : previewState.isLoading
                ? "productive_preview"
                : null,
    changed_files: currentChangedFilesDiagnostics.changedFiles,
    allowed_files: previewState.allowedFiles,
    applied_changed_files: previewState.appliedAt ? currentChangedFilesDiagnostics.appliedChangedFiles : [],
    checks_attempted: previewState.appliedAt ? previewState.checks.length > 0 : false,
    checks_run: previewState.appliedAt ? previewState.checks : [],
    disk_changed_files: previewState.appliedAt ? currentChangedFilesDiagnostics.diskChangedFiles : [],
    hermes_used_for_this_run: currentPreviewProviderTruth.hermesUsedForRunStatus,
    model_called_for_generation: currentPreviewProviderTruth.modelCalledForGeneration ?? "none",
    next_action: nextSafeAction,
    preview_changed_files: currentChangedFilesDiagnostics.previewChangedFiles,
    protected_paths_touched: [],
    provider_call_made: currentPreviewProviderTruth.providerCallMade,
    reason_code: previewState.reasonCode,
    reversal_available: Boolean(currentReversalReceipt && !currentReversalReceipt.revertedAt),
    reverted_at: currentAppliedRunReceipt?.revertedAt ?? null,
    result_category: currentSidecarClassification,
    safety_state: previewState.status === "blocked" ? "blocked" : previewState.appliedAt ? "live apply, no commit, no push" : "preview-only diagnostic, no apply, no commit, no push",
    simple_result: previewLoadingSimpleResult(sourceProxyReachable, previewState, currentTaskState),
    status: previewState.status,
    trial_mode: previewState.appliedAt ? "live_apply" : "preview_only",
  });
  const manualTrialVerdict = useMemo(
    () =>
      evaluateManualComposerTrialVerdict({
        backendRouteTrialContent,
        componentTrialContent,
        preview: {
          approvalAvailable: previewState.approvalAvailable,
          appliedAt: previewState.appliedAt,
          changedFiles: previewState.changedFiles,
          diff: previewState.diff,
          error: previewState.error,
          isLoading: previewState.isLoading,
          reasonCode: previewState.reasonCode,
          selectedTarget: previewState.selectedTarget,
          status: previewState.status,
          technicalDetail: previewState.technicalDetail,
        },
        task,
      }),
    [backendRouteTrialContent, componentTrialContent, previewState, task],
  );
  const hasVerificationTargetEvidence =
    previewState.changedFiles.length > 0 ||
    changedFilesFromDiffPreview(previewState.diff).length > 0 ||
    (Boolean(previewState.selectedTarget) &&
      (previewState.status === "ready" ||
        previewState.status === "approved" ||
        previewState.status === "applied" ||
        previewState.status === "satisfied"));
  const showVerificationTargets =
    verificationTargets.length > 0 &&
    hasVerificationTargetEvidence &&
    (previewState.status === "ready" ||
      previewState.status === "approved" ||
      previewState.status === "applied" ||
      previewState.status === "satisfied" ||
      previewState.status === "blocked" ||
      previewState.status === "error");
  const trialState = useMemo(
    () =>
      buildAgentTrialUiState({
        applyStrategy: trialApplyStrategy,
        bank: trialBank,
        componentTrialContent,
        mode: trialMode,
        profile: "britton-realistic",
        providerTruth: selectedProviderTruth,
        runSize: trialRunSize,
        trialMode: trialProofMode,
        viewport: trialViewport,
      }),
    [componentTrialContent, trialApplyStrategy, trialBank, trialMode, trialProofMode, trialRunSize, trialViewport, selectedProviderTruth],
  );
  const trialModeLabels: Record<AgentTrialMode, string> = {
    code: "Coder",
    design: "Designer",
    hybrid: "Combined",
  };
  const trialResultSummary = useMemo(() => summarizeTrialResult(trialState.actualPromptPreviews), [trialState]);
  const trialStatusLabel =
    trialRunState === "complete" ? "Finished" : trialRunState === "running" ? "Working" : "Ready";
  const trialGrade =
    (trialMode === "code"
      ? trialState.latestGrades.coding
      : trialMode === "design"
        ? trialState.latestGrades.design
        : trialState.latestGrades.hybrid) ?? "Not scored";
  const trialCategoryLabel =
    trialMode === "code"
      ? "Coder usefulness"
      : trialMode === "design"
        ? "Designer usefulness"
        : "Combined usefulness";
  function resetTrialResult() {
    setTrialRunState("idle");
    setTrialCopyStatus("");
  }

  function handleRunTrial() {
    setTrialRunState("running");
    setTrialCopyStatus("");
    window.setTimeout(() => setTrialRunState("complete"), 150);
  }

  const stressTestReadiness = useMemo(
    () =>
      buildStressTestReadiness({
        composerProviderTruth: activeProviderTruth,
        lastProviderCallSmoke,
        ollamaStoragePath,
        sourceProxyReachable,
        staleTrialReceiptCount: countActiveUnrevertedTrialReceipts(appliedRunReceipts),
        trialFixturesClean,
        trialRunnerProviderTruth: selectedProviderTruth,
      }),
    [
      activeProviderTruth,
      appliedRunReceipts,
      lastProviderCallSmoke,
      ollamaStoragePath,
      selectedProviderTruth,
      sourceProxyReachable,
      trialFixturesClean,
    ],
  );

  function trialReportText() {
    const modeLabel = trialModeLabels[trialMode];
    return buildFullTrialDiagnosticReport({
      modeLabel,
      bankLabel: trialState.bankLabel,
      bankMode: trialState.bank,
      liveUsefulnessEligible: trialState.liveUsefulnessEligible,
      liveUsefulnessReason: trialState.liveUsefulnessReason,
      previews: trialState.actualPromptPreviews,
      providerTruth: selectedProviderTruth,
      runId: "not recorded",
      runSize: trialRunSize,
      score: `${trialResultSummary.score} (${trialGrade})`,
      status: trialStatusLabel,
      summary: trialResultSummary,
      viewport: trialViewport,
    });
  }

  async function copyTrialReport() {
    try {
      await navigator.clipboard.writeText(trialReportText());
      setTrialCopyStatus("Report copied.");
    } catch {
      setTrialCopyStatus("Report ready in diagnostics.");
    }
  }

  async function copyTrialPromptsOnly() {
    try {
      await navigator.clipboard.writeText(
        buildTrialPromptsOnlyText({
          bankLabel: trialState.bankLabel,
          modeLabel: trialModeLabels[trialMode],
          previews: trialState.actualPromptPreviews,
          runId: "not recorded",
          runSize: trialRunSize,
          viewport: trialViewport,
        }),
      );
      setTrialCopyStatus("Prompts copied.");
    } catch {
      setTrialCopyStatus("Prompts ready in run details.");
    }
  }

  async function copyTrialAttentionOnly() {
    try {
      await navigator.clipboard.writeText(
        buildTrialAttentionOnlyText({
          bankLabel: trialState.bankLabel,
          modeLabel: trialModeLabels[trialMode],
          previews: trialState.actualPromptPreviews,
          runId: "not recorded",
          runSize: trialRunSize,
          viewport: trialViewport,
        }),
      );
      setTrialCopyStatus("Attention report copied.");
    } catch {
      setTrialCopyStatus("Attention report ready in run details.");
    }
  }

  function resetPreviewForEdit() {
    setDraftReady(false);
    setDiagnosticCopyStatus("");
    setVerificationCopyStatus("");
    setDesignReportCopyStatus("");
    setCombinedCopyStatus("");
    setReversalStatus("");
    setPreviewState(idlePreviewState());
  }

  function rememberPromptSnapshot(value: string) {
    const trimmed = value.trim();
    if (!trimmed || trimmed === lastPromptSnapshot) return;
    const nextHistory = [...promptHistory.filter((item) => item !== trimmed), trimmed].slice(-10);
    setPromptHistory(nextHistory);
    storePromptHistory(nextHistory);
    setLastPromptSnapshot(trimmed);
  }

  function handleTaskChange(value: string) {
    if ((draftReady || previewState.status !== "idle") && task.trim()) {
      rememberPromptSnapshot(task);
    }
    setTask(value);
    resetPreviewForEdit();
  }

  function handleRewindPrompt() {
    const previous = promptHistory[promptHistory.length - 1];
    if (!previous) return;
    const nextHistory = promptHistory.slice(0, -1);
    setPromptHistory(nextHistory);
    storePromptHistory(nextHistory);
    setTask(previous);
    setDraftReady(false);
    setDiagnosticCopyStatus("");
    setVerificationCopyStatus("");
    setReversalStatus("Prompt rewound to the last entered task. No files were changed.");
    setPreviewState(idlePreviewState());
  }

  function updateAppliedRunReceipts(updater: (receipts: AppliedRunReceipt[]) => AppliedRunReceipt[]) {
    setAppliedRunReceipts((current) => {
      const next = updater(current);
      storeAppliedRunReceipts(next);
      return next;
    });
  }

  function designReportText() {
    return [
      "SpiritOS design report",
      `scenario: ${currentDesignTaskKind ?? "design"} task from /coding`,
      `visible_result_label: ${designVisibleResult.primary_label}`,
      `visible_result_tone: ${designVisibleResult.primary_tone}`,
      `visible_result_summary: ${designVisibleResult.plain_summary}`,
      `live_model_proof_status: ${designVisibleResult.live_model_proof_status}`,
      `visible_failure: ${canPreview ? "none visible" : validationMessages.join(", ") || "none visible"}`,
      `target: ${currentTaskTarget}`,
      currentDesignResult,
      `next_action: ${
        canPreview
          ? "Use this design result as implementation context."
          : "Add missing target or allowed files, then rerun or hand this report to the next design proof pass."
      }`,
    ].join("\n");
  }

  async function copyDesignReport() {
    try {
      await navigator.clipboard.writeText(designReportText());
      setDesignReportCopyStatus("Design report copied.");
    } catch {
      setDesignReportCopyStatus("Design report ready in diagnostics.");
    }
  }

  function combinedDiagnosticsText() {
    return [
      "SpiritOS combined diagnostics",
      `task: ${task.trim() || "not drafted"}`,
      `combined_state: ${combinedState}`,
      `visible_result_label: ${combinedVisibleResult.primary_label}`,
      `visible_result_tone: ${combinedVisibleResult.primary_tone}`,
      `visible_result_summary: ${combinedVisibleResult.plain_summary}`,
      `live_model_proof_status: ${combinedVisibleResult.live_model_proof_status}`,
      `designer_context: ${currentDesignResult || "not available"}`,
      `coder_context: ${canPreview ? "ready for natural prompt discovery" : validationMessages.join(", ")}`,
      "designer_recheck: pending after coder result",
      `target: ${currentTaskTarget}`,
      `next_action: ${
        canPreview
          ? "Run the natural prompt preview, then request designer recheck."
          : "Clarify the task before coder handoff."
      }`,
    ].join("\n");
  }

  async function copyCombinedDiagnostics() {
    try {
      await navigator.clipboard.writeText(combinedDiagnosticsText());
      setCombinedCopyStatus("Combined diagnostics copied.");
    } catch {
      setCombinedCopyStatus("Combined diagnostics ready.");
    }
  }

  function diagnosticPacketText() {
    const visibleIssue =
      previewState.error ??
      previewState.blocker ??
      (previewState.isLoading ? "Preview is still running." : currentTaskState);
    const preflight = buildApplyScopePreflight(previewState);
    const includeApplyPreflight =
      previewState.status === "approved" || previewState.status === "applied" || previewState.status === "ready";
    const diagnosticReasonCode = previewState.reasonCode ?? (includeApplyPreflight ? preflight.reasonCode : null);
    const diagnosticTechnicalDetail =
      previewState.technicalDetail ?? (includeApplyPreflight ? preflight.reason : null);
    const diagnosticApplyError =
      previewState.reasonCode === "reversal_failed"
        ? null
        : previewState.error ?? (includeApplyPreflight ? preflight.reason : null);
    const changedFilePaths = verificationTargets.map((target) => target.path);
    const relatedPageLinks = verificationTargets
      .map((target) => target.relatedPageHref)
      .filter((href): href is string => Boolean(href));
    const providerTruth = providerTruthForPreviewState(previewState, selectedProviderTruth);
    const changedFilesDiagnostics = buildChangedFilesDiagnostics({
      appliedAt: previewState.appliedAt,
      diff: previewState.diff,
      status: previewState.status,
      verificationChangedFiles: previewState.changedFiles,
    });
    const sidecarClassification = classifyDiagnosticSidecar({
      approvalAvailable: previewState.approvalAvailable,
      changedFiles: changedFilesDiagnostics.previewChangedFiles,
      previewDiffProduced: Boolean(previewState.diff.trim()),
      providerCallMade: providerTruth.providerCallMade,
      providerCallRequired: false,
      providerModelStatus: providerTruth.status,
      reasonCode: diagnosticReasonCode,
      status: previewState.status,
      verificationPassed: previewState.status === "ready" || previewState.status === "approved",
    });
    return [
      "SpiritOS /coding diagnostics",
      "diagnostic_version: manual-natural-runner.v1",
      "run_id: not recorded",
      `timestamp: ${new Date().toISOString()}`,
      `composer_elapsed: ${formatElapsedMs(
        composerTiming.runStartedAt,
        composerTiming.runStartedAt != null && composerTiming.totalMs != null
          ? composerTiming.runStartedAt + composerTiming.totalMs
          : performance.now(),
      )}`,
      `composer_prompt_packet_ms: ${composerTiming.promptPacketMs ?? "none"}`,
      `composer_diff_preview_ms: ${composerTiming.diffPreviewMs ?? "none"}`,
      `composer_total_ms: ${composerTiming.totalMs ?? "none"}`,
      `prompt: ${task.trim() || "not drafted"}`,
      `provider: ${providerTruth.providerLabel}`,
      `model: ${providerTruth.modelLabel}`,
      `provider_call_made: ${providerTruth.providerCallMade}`,
      `model_called_for_generation: ${providerTruth.modelCalledForGeneration ?? "none"}`,
      `target_candidates: ${formatList(previewState.targetCandidates, "none")}`,
      `selected_target: ${(previewState.selectedTarget ?? normalizeRepoPath(targetFile)) || "none"}`,
      `allowed_files: ${formatList(preflight.allowedFiles, "none")}`,
      `generated_diff_present: ${Boolean(previewState.diff.trim())}`,
      `preview_changed_files: ${formatList(changedFilesDiagnostics.previewChangedFiles, "none")}`,
      `applied_changed_files: ${formatList(changedFilesDiagnostics.appliedChangedFiles, "none")}`,
      `disk_changed_files: ${formatList(changedFilesDiagnostics.diskChangedFiles, "none")}`,
      `checks_run: ${formatList(previewState.checks, "none")}`,
      `checks_result: ${previewState.verifierSummary}`,
      `reversal_available: ${canRevertCurrentRun}`,
      `reversal_status: ${reversalStatus || currentAppliedRunReceipt?.revertedAt || "none"}`,
      `visible_result_label: ${codingVisibleResult.primary_label}`,
      `failure_reason: ${previewState.error ?? previewState.blocker ?? previewState.reasonCode ?? "none"}`,
      `endpoint_statuses: ${previewState.routeCalled ?? "none"}`,
      `next_recommended_action: ${nextSafeAction}`,
      `submitted_prompt: ${task.trim() || "not drafted"}`,
      `trial_verdict: ${manualTrialVerdict.verdict}`,
      `trial_fixture_id: ${manualTrialVerdict.fixtureId ?? "none"}`,
      `trial_expected_behavior: ${manualTrialVerdict.expectedBehavior ?? "none"}`,
      `trial_actual_behavior: ${manualTrialVerdict.actualBehavior ?? "none"}`,
      `trial_verdict_detail: ${manualTrialVerdict.detail}`,
      `visible_result_label: ${codingVisibleResult.primary_label}`,
      `visible_result_tone: ${codingVisibleResult.primary_tone}`,
      `visible_result_summary: ${codingVisibleResult.plain_summary}`,
      `live_model_proof_status: ${codingVisibleResult.live_model_proof_status}`,
      `visible_status: ${currentTaskState}`,
      `raw_status: ${previewState.status}`,
      `current_phase: ${previewState.currentPhase}`,
      `current_step: ${previewState.currentPhase}`,
      `reason_code: ${diagnosticReasonCode ?? "none"}`,
      `visible_error: ${visibleIssue}`,
      `technical_detail: ${diagnosticTechnicalDetail ?? "none"}`,
      `target_candidates: ${formatList(previewState.targetCandidates, "none")}`,
      `selected_target: ${(previewState.selectedTarget ?? normalizeRepoPath(targetFile)) || "none"}`,
      `allowed_files: ${formatList(preflight.allowedFiles, "none")}`,
      `internal_allowed_files: ${formatList(previewState.allowedFiles, "none")}`,
      `forbidden_files: ${formatList(previewState.forbiddenFiles, "none")}`,
      ...formatChangedFilesDiagnosticsLines(changedFilesDiagnostics),
      `verification_targets: ${formatList(changedFilePaths, "none")}`,
      `changed_file_paths: ${formatList(changedFilePaths, "none")}`,
      `changed_file_links: ${formatList(changedFilePaths, "none")}`,
      `related_page_links: ${formatList(relatedPageLinks, "none inferred")}`,
      `file_open_available: ${verificationTargets.some((target) => target.fileOpenAvailable)}`,
      `route_inference_notes: ${formatList(verificationTargets.map((target) => `${target.path}: ${target.routeInferenceNote}`), "none")}`,
      `checks: ${formatList(previewState.checks, "none")}`,
      `route_called: ${previewState.routeCalled ?? "none"}`,
      ...providerAndChangedFilesDiagnosticLines(providerTruth, changedFilesDiagnostics),
      `counts_for_live_usefulness: ${codingVisibleResult.should_count_as_live_model_proof}`,
      `s_plus_eligible: ${codingVisibleResult.should_count_as_live_model_proof}`,
      `diagnostic_sidecar_classification: ${sidecarClassification}`,
      `provider_at_preview_time: ${providerTruth.providerLabel}`,
      `model_at_preview_time: ${providerTruth.modelLabel}`,
      `provider_model_source_route_at_preview_time: ${previewState.routeCalled ?? "none"}`,
      `provider_at_apply_time: ${previewState.appliedAt ? providerTruth.providerLabel : "not applied"}`,
      `model_at_apply_time: ${previewState.appliedAt ? providerTruth.modelLabel : "not applied"}`,
      `provider_model_source_route_at_apply_time: ${previewState.appliedAt ? "/v1/actions/execute-approved" : "not applied"}`,
      `provider_at_reversal_time: ${reversalStatus ? selectedProviderTruth.providerLabel : "not reversed"}`,
      `model_at_reversal_time: ${reversalStatus ? selectedProviderTruth.modelLabel : "not reversed"}`,
      `provider_model_source_route_at_reversal_time: ${reversalStatus ? "/v1/actions/execute-approved" : "not reversed"}`,
      `preview_diff_status: ${previewState.previewStatus}`,
      `approval_available: ${previewState.approvalAvailable}`,
      `approved_at: ${previewState.approvedAt ?? "not approved"}`,
      `applied_at: ${previewState.appliedAt ?? "not applied"}`,
      `apply_error: ${diagnosticApplyError ?? "none"}`,
      `apply_summary: ${previewState.applySummary || "none"}`,
      `reversal_available: ${canRevertCurrentRun || canRevertTrialRuns}`,
      `reversal_status: ${reversalStatus || "none"}`,
      `unreverted_trial_runs: ${countActiveUnrevertedTrialReceipts(appliedRunReceipts)}`,
      `stale_resolved_trial_runs: ${appliedRunReceipts.filter((receipt) => receipt.staleResolvedAt).length}`,
      ...formatStressTestReadinessLines(stressTestReadiness, lastProviderCallSmoke),
      `reversal_receipts: ${
        appliedRunReceipts.length > 0
          ? appliedRunReceipts
              .map((receipt) =>
                [
                  receipt.id,
                  `target=${receipt.target}`,
                  `changed=${formatList(receipt.changedFiles, "none")}`,
                  `allowed=${formatList(receipt.allowedFiles, "none")}`,
                  `applied_at=${receipt.appliedAt}`,
                  `provider=${receipt.provider ?? "not recorded"}`,
                  `model=${receipt.model ?? "not recorded"}`,
                  `provider_model_source=${receipt.providerModelSource ?? "unknown"}`,
                  `provider_model_status=${receipt.providerModelStatus ?? "unknown"}`,
                  `hermes_used=${receipt.hermesUsedForThisRun === null ? "unknown" : receipt.hermesUsedForThisRun ? "yes" : "no"}`,
                  `reverted_at=${receipt.revertedAt ?? "not reverted"}`,
                  `reversal_provider=${receipt.reversalProvider ?? "not reversed"}`,
                  `reversal_model=${receipt.reversalModel ?? "not reversed"}`,
                ].join(" | "),
              )
              .join("; ")
          : "none"
      }`,
      `error_message: ${previewState.error ?? previewState.blocker ?? "none"}`,
      "subsystem: coding preview",
      "debug_home: /proxy-backend",
      `next_action: ${nextSafeAction}`,
      "",
      "diff_preview:",
      previewState.diff.trim() ? previewState.diff : "diff omitted because unavailable",
      "",
      "progress_events:",
      previewState.events.length > 0
        ? previewState.events.map((event) => `- ${event.status}: ${event.label} - ${event.detail}`).join("\n")
        : "- none recorded",
      "",
      "copy_paste_block_for_chatgpt_codex:",
      `Manual /coding prompt: ${task.trim() || "not drafted"}`,
      `Trial verdict: ${manualTrialVerdict.verdict}`,
      `Trial fixture: ${manualTrialVerdict.fixtureId ?? "none"}`,
      `Trial detail: ${manualTrialVerdict.detail}`,
      `Observed status: ${currentTaskState}`,
      `Reason code: ${diagnosticReasonCode ?? "none"}`,
      `Provider: ${providerTruth.providerLabel}`,
      `Model: ${providerTruth.modelLabel}`,
      `Provider/model source: ${providerTruth.source}`,
      `Provider/model selected via: ${providerTruth.providerModelSelectedVia ?? "unknown"}`,
      `Configured local model is Hermes: ${
        providerTruth.configuredModelIsHermes === null
          ? "unknown"
          : providerTruth.configuredModelIsHermes
            ? "yes"
            : "no"
      }`,
      `Hermes used: ${providerTruth.hermesUsedForRunStatus}`,
      `Provider call made: ${providerTruth.providerCallMade}`,
      `Visible result: ${codingVisibleResult.primary_label}`,
      `Live model proof status: ${codingVisibleResult.live_model_proof_status}`,
      `Provider call note: ${
        providerTruth.providerCallMade
          ? "live provider route was used for this run"
          : "deterministic preview path; no Hermes generation call was required"
      }`,
      `Selected target: ${previewState.selectedTarget ?? "none"}`,
      `Allowed files: ${formatList(preflight.allowedFiles, "none")}`,
      `Changed files: ${formatList(previewState.changedFiles, "none")}`,
      `Routes: ${previewState.routeCalled ?? "none"}`,
      `Preview status: ${previewState.previewStatus}`,
      `Approval status: ${previewState.approvalAvailable ? "available" : "unavailable"}`,
      `Apply status: ${previewState.appliedAt ? "applied" : previewState.approvedAt ? "approved_not_applied" : "not applied"}`,
      `Reversal availability: ${canRevertCurrentRun || canRevertTrialRuns}`,
      `Reversal status: ${reversalStatus || "none"}`,
      `Need help with: ${nextSafeAction}`,
    ].join("\n");
  }

  async function runHermesStressSmoke() {
    if (isRunningStressSmoke) return;
    setIsRunningStressSmoke(true);
    setStressSmokeStatus("Calling Source Proxy /v1/chat/completions with local Hermes route...");
    try {
      const response = await fetch("/v1/coding/hermes-stress-smoke", { method: "POST" });
      const payload = await response.json() as ProviderCallSmokeResult & {
        detail?: string;
        pass?: boolean;
        response_content?: string;
        response_time_ms?: number;
        routed_model?: string;
        zero_cost_local_route?: boolean;
      };
      const smoke: ProviderCallSmokeResult = {
        pass: payload.pass === true,
        provider: payload.provider ?? "local",
        responseContent: payload.responseContent ?? payload.response_content ?? null,
        responseTimeMs: payload.responseTimeMs ?? payload.response_time_ms ?? null,
        routedModel: payload.routedModel ?? payload.routed_model ?? null,
        zeroCostLocalRoute: payload.zeroCostLocalRoute ?? payload.zero_cost_local_route ?? false,
      };
      setLastProviderCallSmoke(smoke);
      setStressSmokeStatus(
        smoke.pass
          ? `Hermes stress smoke passed via ${smoke.routedModel ?? "local route"} in ${smoke.responseTimeMs ?? "?"}ms.`
          : `Hermes stress smoke failed${payload.detail ? `: ${payload.detail}` : "."}`,
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "Hermes stress smoke failed.";
      setLastProviderCallSmoke({ pass: false });
      setStressSmokeStatus(message);
    } finally {
      setIsRunningStressSmoke(false);
    }
  }

  async function copyDiagnostics() {
    try {
      await navigator.clipboard.writeText(diagnosticPacketText());
      setDiagnosticCopyStatus("Diagnostics copied.");
    } catch {
      setDiagnosticCopyStatus("Diagnostics ready in /proxy-backend.");
    }
  }

  async function copyVerificationPath(path: string) {
    if (!isSafeRepoPath(path)) {
      setVerificationCopyStatus("Unsafe path not copied.");
      return;
    }
    try {
      await navigator.clipboard.writeText(path);
      setVerificationCopyStatus(`Copied ${path}`);
    } catch {
      setVerificationCopyStatus("Path ready to copy manually.");
    }
  }

  function manualEvent(phase: ManualTaskPhase, status: ManualTaskEventStatus, detail: string): ManualTaskEvent {
    return {
      detail,
      label: previewLoadingPhaseLabel(sourceProxyReachable, phase),
      status,
    };
  }

  function setManualProgress(events: ManualTaskEvent[], phase: ManualTaskPhase) {
    setPreviewState((current) => ({
      ...current,
      currentPhase: previewLoadingPhaseLabel(sourceProxyReachable, phase),
      events,
    }));
  }

  function reversibleSuiteDiagnosticsText(state = reversibleSuiteState): string {
    const lines = [
      `suite_id: ${state.suiteId || "none"}`,
      `category: ${reversibleTrialCategory}`,
      `count_requested: ${state.count}`,
      `count_completed: ${state.completed}`,
      `edit_applied_count: ${state.pass}`,
      `already_satisfied_count: ${state.alreadySatisfied}`,
      `expected_no_edit_count: ${state.expectedNoEdit}`,
      `safety_block_count: ${state.safetyBlock}`,
      `needs_fix_count: ${state.fail}`,
      `timeout_count: ${state.timeout}`,
      `undone_count: ${state.reverted}`,
      `stopped: ${state.stopped ? "yes" : "no"}`,
      `suite_interruption_source: ${state.interruptionSource}`,
      `suite_interruption_reason: ${state.interruptionReason ?? "none"}`,
      `suite_recovery_state: ${
        state.interruptionSource === "browser_refresh_or_dev_reload"
          ? "paused_transcript_preserved_reverse_or_rerun"
          : state.interruptionSource === "user_stop"
            ? "user_stop_transcript_preserved"
            : "normal"
      }`,
      `current_step: ${state.currentStep}`,
      `suite_mode: ${reversibleTrialCategory}`,
      `suite_elapsed: ${formatElapsedMs(state.suiteStartedAt)}`,
      `current_prompt_elapsed: ${state.currentPromptElapsedMs != null ? `${(state.currentPromptElapsedMs / 1000).toFixed(1)}s` : "—"}`,
      `branch: browser-run`,
      `provider/model: ${state.provider || "unknown"} / ${state.model || "unknown"}`,
      `health_proxy: ${sourceProxyReachable ? "reachable (/v1/self/status)" : "unreachable"}`,
      `health_model_lane_configured: ${selectedProviderTruth.modelLabel || "unknown"} (${selectedProviderTruth.status})`,
      `health_model_lane_runtime_route: ${selectedProviderTruth.runtimeRouteModel || "unknown"}`,
      `health_model_lane_selected_via: ${selectedProviderTruth.providerModelSelectedVia ?? "unknown"}`,
      `suite_runtime_model_last_seen: ${state.model || "unknown"}`,
      `model_truth_note: health_model_lane_configured is /v1/self/status config; provider/model is the runtime model recorded by suite rows`,
      `health_git: check with git status after suite`,
      `health_search: use Source Proxy research routes when enabled`,
      "final_tree_status: verify with git status after suite; use Reverse trial edits to undo applied prompts manually",
      "next_recommended_action: inspect failures, copy diagnostics, then rerun the bounded suite",
      "",
      "per_prompt:",
    ];
    for (const result of state.results) {
      lines.push(
        `- prompt_id: ${result.prompt.id}`,
        `  title: ${result.prompt.quickTitle}`,
        `  expected_outcome: ${result.expected_outcome}`,
        `  actual_outcome: ${result.visible_result_label}`,
        `  prompt_text: ${reversibleTrialPromptForMode(result.prompt, modeForTrialCategory(result.prompt.category))}`,
        `  run_id: ${result.run_id || "none"}`,
        `  provider_call_made: ${String(result.provider_call_made)}`,
        `  model_called_for_generation: ${result.model_called_for_generation || "none"}`,
        `  target_candidates: ${formatList(result.target_candidates, "none")}`,
        `  selected_target: ${result.selected_target || "none"}`,
        `  allowed_files: ${formatList(result.allowed_files, "none")}`,
        `  preview_changed_files: ${formatList(result.preview_changed_files, "none")}`,
        `  applied_changed_files: ${formatList(result.applied_changed_files, "none")}`,
        `  disk_changed_files: ${formatList(result.disk_changed_files, "none")}`,
        `  checks_run: ${formatList(result.checks_run, "none")}`,
        `  checks_result: ${result.checks_result || "not recorded"}`,
        `  reversal_available: ${String(result.reversal_available)}`,
        `  reverted: ${result.reverted ? "yes" : "no"}`,
        `  reverse_status: ${result.reverse_status_text || "No applied trial edits to reverse."}`,
        `  quick_find_path: ${formatList(result.prompt.verifyPathHints, "none")}`,
        `  verify_instruction: ${result.prompt.verifyInstruction}`,
        `  visible_result_label: ${result.visible_result_label}`,
        `  receipt_model: ${result.model_called_for_generation || "none"}`,
        `  receipt_prompt_id: ${result.prompt.id}`,
        `  receipt_final_status: ${result.visible_result_label}`,
        `  receipt_files_changed: ${formatList(result.applied_changed_files.length > 0 ? result.applied_changed_files : result.preview_changed_files, "none")}`,
        `  receipt_time_spent_ms: ${result.elapsed_ms ?? "none"}`,
        `  failure_reason: ${result.failure_reason || "none"}`,
        `  error_summary: ${result.error_summary || "none"}`,
        `  endpoint_statuses: ${formatList(result.endpoint_statuses, "none")}`,
        `  elapsed_ms: ${result.elapsed_ms ?? "none"}`,
        `  next_recommended_action: ${result.next_recommended_action || "Continue to the next prompt or inspect failures."}`,
      );
    }
    return lines.join("\n");
  }

  async function copyReversibleSuiteDiagnostics() {
    let text = "";
    try {
      text = reversibleSuiteDiagnosticsText();
    } catch (error) {
      const message = error instanceof Error ? error.message : "diagnostics build failed";
      setReversibleSuiteCopyStatus(
        `Could not build trial diagnostics (${message}). Check Advanced details.`,
      );
      return;
    }
    if (!text.trim()) {
      setReversibleSuiteCopyStatus("No trial diagnostics yet — run or finish a suite first.");
      return;
    }
    const copied = await copyTextToClipboard(text);
    if (copied.ok) {
      setReversibleSuiteCopyStatus("Trial diagnostics copied.");
      return;
    }
    setReversibleSuiteCopyStatus(
      copied.reason === "denied"
        ? "Clipboard blocked — allow paste for this site or copy from Advanced details."
        : "Clipboard unavailable — copy from Advanced details manually.",
    );
  }

  function reversibleSuitePromptsText(): string {
    const prompts = selectReversibleTrialPrompts(reversibleTrialCount, reversibleTrialCategory);
    return [
      `category: ${reversibleTrialCategory}`,
      `count_requested: ${reversibleTrialCount}`,
      "",
      ...prompts.flatMap((prompt, index) => [
        `${index + 1}. ${reversibleTrialPromptForMode(prompt, modeForTrialCategory(prompt.category))}`,
        "",
      ]),
    ].join("\n");
  }

  async function copyReversibleSuitePrompts() {
    try {
      await navigator.clipboard.writeText(reversibleSuitePromptsText());
      setReversiblePromptsCopyStatus("Prompts copied.");
    } catch {
      setReversiblePromptsCopyStatus("Prompts are ready but clipboard access failed.");
    }
  }

  async function runOneReversibleTrialPrompt(
    prompt: ReversibleTrialPrompt,
    onStep?: (step: string) => void,
  ): Promise<ReversibleSuitePromptResult> {
    const promptStartedAt = performance.now();
    const endpointStatuses: string[] = [];
    const effectivePrompt = reversibleTrialPromptForMode(prompt, modeForTrialCategory(prompt.category));
    const taskText = effectivePrompt;
    const packet = buildManualTaskPacket({
      allowedFilesText: prompt.expected_scope.join("\n"),
      expectedChecksText: "git diff --check",
      prompt: taskText,
      targetFile: prompt.targetFile,
    });
    const baseResult = (patch: Partial<ReversibleSuitePromptResult>): ReversibleSuitePromptResult => ({
      allowed_files: packet.allowedFiles,
      applied_changed_files: [],
      checks_result: "not run",
      checks_run: packet.checks,
      disk_changed_files: [],
      endpoint_statuses: endpointStatuses,
      error_summary: "",
      expected_outcome: prompt.expectedOutcome,
      failure_reason: "",
      model_called_for_generation: "none",
      next_recommended_action: "",
      prompt,
      provider: selectedProviderTruth.providerLabel,
      provider_call_made: false,
      preview_changed_files: [],
      reverse_diff: "",
      reverse_status_text: "No applied trial edits to reverse.",
      reverted: false,
      reversal_available: false,
      run_id: "",
      selected_target: packet.selectedTarget ?? "",
      target_candidates: packet.targetCandidates,
      visible_result_label: "FAIL",
      elapsed_ms: elapsedMs(promptStartedAt),
      ...patch,
    });
    onStep?.("Reading request");
    const taskResponse = await fetch("/v1/tasks/long-running", {
      body: JSON.stringify({
        description: effectivePrompt,
        steps: [
          "Reading request",
          "Finding files",
          "Calling model",
          "Editing files",
          "Checking",
          "Ready for review",
        ],
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const taskPayload = await readJson(taskResponse);
    endpointStatuses.push(`/v1/tasks/long-running:${taskResponse.status}`);
    if (!taskResponse.ok) {
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        failure_reason: messageFromPayload(taskPayload, taskResponse.status),
      });
    }
    const taskId = taskIdFromPayload(taskPayload);
    if (!taskId) {
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        failure_reason: "Long-running task create did not return a task id.",
      });
    }

    onStep?.(previewLoadingPhaseLabel(sourceProxyReachable, "preview"));
    let proposalResponse: Response;
    try {
      proposalResponse = await fetchPromptPacketWithRetry({
        body: JSON.stringify({
          active_task_id: taskId,
          allowed_files: packet.allowedFiles,
          expected_outcome: prompt.expectedOutcome,
          needs_codebase_context: true,
          prefer_free: true,
          protected_paths_blocked: true,
          quick_find_hints: prompt.verifyPathHints,
          selected_target: packet.selectedTarget,
          task: taskText,
          trial_mode: "live_apply",
          trial_prompt_id: prompt.id,
          verification: packet.checks,
          wants_implementation: true,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
      }, TRIAL_PROMPT_PACKET_TIMEOUT_MS);
    } catch (error) {
      const timeoutLayer = timeoutLayerFromError(error);
      endpointStatuses.push(`/v1/decisions/prompt-packet:${promptPacketEndpointStatusForError(error)}`);
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: `${timeoutLayer === "network_fetch_error" ? "fetch_error_source" : "timeout_source"}: /v1/decisions/prompt-packet; timeout_layer: ${timeoutLayer}; selected_target: ${packet.selectedTarget || "none"}`,
        failure_reason: error instanceof Error ? error.message : "Model call timed out.",
        next_recommended_action:
          timeoutLayer === "browser_abort_timeout"
            ? "Browser aborted before Source Proxy returned. Inspect Source Proxy prompt-packet logs for coder_sync_timeout, provider timeout, or route hang."
            : timeoutLayer === "network_fetch_error"
              ? "Browser fetch failed before a provider response. Confirm the /coding page stayed connected, then rerun the bounded suite."
            : "Inspect the Source Proxy prompt-packet route and provider timeout logs.",
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    let proposalPayload = await readJson(proposalResponse);
    endpointStatuses.push(`/v1/decisions/prompt-packet:${proposalResponse.status}`);
    if (!proposalResponse.ok) {
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: safePayloadSummary(proposalPayload),
        failure_reason: messageFromPayload(proposalPayload, proposalResponse.status),
        next_recommended_action: "Inspect the prompt-packet response body and Source proxy logs for the failed route.",
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    let providerTruth = providerModelTruthFromPayload(proposalPayload, selectedProviderTruth);
    let proposedDiff = diffFromPayload(proposalPayload);
    let providerCallMade = trialProviderCallMadeFromPayload(proposalPayload, providerTruth);
    let modelCalledForGeneration = providerTruth.modelCalledForGeneration
      ?? (providerCallMade ? providerTruth.modelId || providerTruth.modelLabel : "none");
    let promptPacketReasonCode =
      typeof proposalPayload === "object" && proposalPayload !== null
        ? String((proposalPayload as Record<string, unknown>).reason_code ?? "").trim()
        : "";
    if (
      prompt.expectedOutcome === "edit_reversible" &&
      !proposedDiff.trim() &&
      promptPacketReasonCode === "coder_no_changes_needed" &&
      !providerCallMade &&
      (packet.selectedTarget ?? prompt.targetFile).startsWith("src/")
    ) {
      onStep?.(previewLoadingPhaseLabel(sourceProxyReachable, "preview"));
      proposalResponse = await fetchPromptPacketWithRetry(
        {
          body: JSON.stringify({
            active_task_id: taskId,
            allowed_files: packet.allowedFiles,
            expected_outcome: prompt.expectedOutcome,
            needs_codebase_context: true,
            prefer_free: true,
            protected_paths_blocked: true,
            quick_find_hints: prompt.verifyPathHints,
            selected_target: packet.selectedTarget,
            task: taskText,
            trial_mode: "live_apply",
            trial_prompt_id: prompt.id,
            trial_recover_already_satisfied: true,
            verification: packet.checks,
            wants_implementation: true,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
        TRIAL_PROMPT_PACKET_TIMEOUT_MS,
      );
      proposalPayload = await readJson(proposalResponse);
      endpointStatuses.push(`/v1/decisions/prompt-packet(product-retry):${proposalResponse.status}`);
      providerTruth = providerModelTruthFromPayload(proposalPayload, selectedProviderTruth);
      proposedDiff = diffFromPayload(proposalPayload);
      providerCallMade = trialProviderCallMadeFromPayload(proposalPayload, providerTruth);
      modelCalledForGeneration = providerTruth.modelCalledForGeneration
        ?? (providerCallMade ? providerTruth.modelId || providerTruth.modelLabel : "none");
      promptPacketReasonCode =
        typeof proposalPayload === "object" && proposalPayload !== null
          ? String((proposalPayload as Record<string, unknown>).reason_code ?? "").trim()
          : "";
    }
    if (
      prompt.expectedOutcome === "edit_reversible" &&
      !proposedDiff.trim() &&
      promptPacketReasonCode === "coder_no_changes_needed" &&
      (packet.selectedTarget ?? prompt.targetFile).includes("dummy-coding-targets/")
    ) {
      await prepareDummyTrialFixtureForReversibleApply(
        packet.selectedTarget ?? prompt.targetFile,
        onStep,
      );
      onStep?.(previewLoadingPhaseLabel(sourceProxyReachable, "preview"));
      proposalResponse = await fetchPromptPacketWithRetry(
        {
          body: JSON.stringify({
            active_task_id: taskId,
            allowed_files: packet.allowedFiles,
            expected_outcome: prompt.expectedOutcome,
            needs_codebase_context: true,
            prefer_free: true,
            protected_paths_blocked: true,
            quick_find_hints: prompt.verifyPathHints,
            selected_target: packet.selectedTarget,
            task: taskText,
            trial_mode: "live_apply",
            trial_prompt_id: prompt.id,
            verification: packet.checks,
            wants_implementation: true,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
        TRIAL_PROMPT_PACKET_TIMEOUT_MS,
      );
      proposalPayload = await readJson(proposalResponse);
      endpointStatuses.push(`/v1/decisions/prompt-packet(retry):${proposalResponse.status}`);
      providerTruth = providerModelTruthFromPayload(proposalPayload, selectedProviderTruth);
      proposedDiff = diffFromPayload(proposalPayload);
      providerCallMade = trialProviderCallMadeFromPayload(proposalPayload, providerTruth);
      modelCalledForGeneration = providerTruth.modelCalledForGeneration
        ?? (providerCallMade ? providerTruth.modelId || providerTruth.modelLabel : "none");
      promptPacketReasonCode =
        typeof proposalPayload === "object" && proposalPayload !== null
          ? String((proposalPayload as Record<string, unknown>).reason_code ?? "").trim()
          : "";
    }
    const trialDryRunOnly = /dry run/i.test(prompt.prompt);
    if (
      prompt.expectedOutcome === "edit_reversible" &&
      !proposedDiff.trim() &&
      promptPacketReasonCode === "coder_no_changes_needed" &&
      providerCallMade
    ) {
      return baseResult({
        checks_result: "already satisfied on disk; live model call recorded",
        failure_reason: "",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        run_id: taskId,
        reverse_status_text: "Product code already satisfies this prompt; no trial edit was applied.",
        visible_result_label: "ALREADY SATISFIED",
      });
    }
    if (prompt.expectedOutcome !== "edit_reversible") {
      if (proposedDiff.trim()) {
        return baseResult({
          failure_reason: "Needs fix: expected no file edit, but the model returned a diff.",
          model_called_for_generation: modelCalledForGeneration,
          provider: providerTruth.providerLabel,
          provider_call_made: providerCallMade,
          preview_changed_files: changedFilesFromDiffPreview(proposedDiff),
          run_id: taskId,
          visible_result_label: "NEEDS FIX",
        });
      }
      if (!providerCallMade || modelCalledForGeneration === "none") {
        if (prompt.expectedOutcome === "safety_block_expected") {
          const safetyBlockedEarly =
            promptPacketReasonCode === "protected_path_request" ||
            promptPacketReasonCode === "secret_path" ||
            promptPacketReasonCode === "protected_path";
          return baseResult({
            checks_result: "Blocked for safety",
            failure_reason: "",
            model_called_for_generation: modelCalledForGeneration,
            next_recommended_action: "Keep protected paths and secrets untouched.",
            provider: providerTruth.providerLabel,
            provider_call_made: providerCallMade,
            run_id: taskId,
            reverse_status_text: "No applied trial edits to reverse.",
            visible_result_label: safetyBlockedEarly ? "NO EDIT EXPECTED" : "BLOCKED",
          });
        }
        return baseResult({
          checks_result: "not run",
          failure_reason: "Needs fix: expected no-edit outcome was not proven by a real model call.",
          model_called_for_generation: modelCalledForGeneration,
          next_recommended_action: "Restore provider/model generation before counting expected no-edit prompts.",
          provider: providerTruth.providerLabel,
          provider_call_made: providerCallMade,
          run_id: taskId,
          visible_result_label: "NEEDS FIX",
        });
      }
      return baseResult({
        checks_result:
          prompt.expectedOutcome === "clarify_expected"
            ? "Clarification needed"
            : prompt.expectedOutcome === "safety_block_expected"
              ? "Blocked for safety"
              : prompt.expectedOutcome === "noop_expected"
                ? "No edit needed"
                : "Manual step needed",
        failure_reason: "",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: providerCallMade,
        run_id: taskId,
        reverse_status_text: "No applied trial edits to reverse.",
        visible_result_label: "NO EDIT EXPECTED",
      });
    }
    if (!providerCallMade) {
      const syncTimedOut = promptPacketReasonCode === "coder_sync_timeout";
      const modelCallFailed =
        promptPacketReasonCode === "realistic_trial_model_call_failed" ||
        promptPacketReasonCode === "dummy_trial_model_call_failed";
      const selectedTarget = packet.selectedTarget ?? prompt.targetFile;
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: syncTimedOut
          ? `reason_code=${promptPacketReasonCode}; timeout_stage=${String(
              (typeof proposalPayload === "object" && proposalPayload !== null
                ? ((proposalPayload as Record<string, unknown>).coder_diagnostics as Record<string, unknown> | undefined)
                    ?.timeout_stage
                : "") ?? "unknown",
            )}`
          : promptPacketReasonCode
            ? modelCallFailed
              ? trialModelProofFailureSummary(proposalPayload, promptPacketReasonCode, selectedTarget)
              : `reason_code=${promptPacketReasonCode}`
            : "provider_call_made=false",
        failure_reason: syncTimedOut
          ? "NEEDS FIX: Coder exceeded the Source Proxy sync deadline before the model returned. Transcript and suite progress are preserved — retry this prompt."
          : modelCallFailed
            ? "NEEDS FIX: Source Proxy route succeeded, but the trial model-proof call did not complete."
            : "FAIL: No model call",
        model_called_for_generation: modelCalledForGeneration,
        next_recommended_action: syncTimedOut
          ? "Restart Source Proxy with the coder lane (qwen2.5-coder:7b), then rerun. If it still times out, inspect timeout_stage in diagnostics."
          : modelCallFailed
            ? "Run: curl -k https://127.0.0.1:8787/v1/models ; confirm the coder alias is listed and Ollama can answer qwen2.5-coder:7b quickly, then rerun the suite."
          : "Confirm Source Proxy exposes the coder model route and rerun.",
        provider: providerTruth.providerLabel,
        provider_call_made: false,
        run_id: taskId,
        visible_result_label: syncTimedOut || modelCallFailed ? "NEEDS FIX" : "FAIL",
      });
    }
    if (!proposedDiff.trim()) {
      return baseResult({
        error_summary: [
          "proof_missing: diff_preview_missing",
          "provider_call_made=true",
          "transcript_or_model_response_body_empty_or_no_diff",
          `endpoint_statuses=${formatList(endpointStatuses, "none")}`,
        ].join("; "),
        failure_reason: "NEEDS FIX: Live apply proof missing: provider call returned no diff/preview body to apply.",
        model_called_for_generation: modelCalledForGeneration,
        next_recommended_action: "Inspect prompt-packet body/transcript. A 200 route without diff preview proof must not count as PASS.",
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }

    onStep?.("Finding files");
    const diffResponse = await fetch("/v1/verification/diff-preview", {
      body: JSON.stringify({
        route_type: "live_apply",
        task_spec: {
          allowed_files: packet.allowedFiles,
          forbidden_files: PROTECTED_FORBIDDEN_FILES,
          risk_tier: prompt.risk,
          schema_version: 1,
          source: "coding-reversible-trial-runner-suite",
          target: packet.selectedTarget ?? prompt.targetFile,
          task_type: "modify_existing_file",
          verification: packet.checks,
        },
        task_text: taskText,
        unified_diff: proposedDiff,
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const diffPayload = await readJson(diffResponse);
    endpointStatuses.push(`/v1/verification/diff-preview:${diffResponse.status}`);
    if (!diffResponse.ok) {
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: safePayloadSummary(diffPayload),
        failure_reason: messageFromPayload(diffPayload, diffResponse.status),
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    const previewChangedFiles = changedFilesFromPayload(diffPayload);
    const protectedTouched = previewChangedFiles.some((path) => isProtectedTarget(path));
    const outsideAllowed = previewChangedFiles.some((path) => !packet.allowedFiles.includes(path));
    if (trialDryRunOnly) {
      return baseResult({
        applied_changed_files: [],
        checks_result: "dry-run preview only (no disk write)",
        disk_changed_files: [],
        failure_reason: "",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        reverse_status_text: "Dry run: preview recorded without execute-approved.",
        run_id: taskId,
        visible_result_label: "PASS",
      });
    }
    if (statusFromPayload(diffPayload) === "blocked" || protectedTouched || outsideAllowed) {
      return baseResult({
        checks_result: "blocked",
        failure_reason: protectedTouched
          ? "BLOCKED: Protected path"
          : "NEEDS FIX: Live apply proof missing: diff preview touched files outside the allowed scope.",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        run_id: taskId,
        next_recommended_action: protectedTouched
          ? "Keep the protected-path block and verify no files changed."
          : "Inspect the generated diff and allowed-file metadata; the model edited outside the expected scope.",
        visible_result_label: protectedTouched ? "BLOCKED" : "NEEDS FIX",
      });
    }

    onStep?.("Editing files");
    const applyResponse = await fetch("/v1/actions/execute-approved", {
      body: JSON.stringify({
        action: `Live trial ${prompt.id}`,
        approved: true,
        approved_diff: proposedDiff,
        allowed_files: packet.allowedFiles,
        target: packet.selectedTarget,
        task_id: taskId,
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const applyPayload = await readJson(applyResponse);
    endpointStatuses.push(`/v1/actions/execute-approved:${applyResponse.status}`);
    if (!applyResponse.ok) {
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: safePayloadSummary(applyPayload),
        failure_reason: messageFromPayload(applyPayload, applyResponse.status),
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    const appliedChangedFiles = changedFilesFromApplyPayloadOrDiff(applyPayload, proposedDiff);
    const diskChangedFiles = appliedChangedFiles;
    const applySnapshots = changedFileSnapshotsFromPayload(applyPayload);
    const missingBeforeSnapshots = appliedChangedFiles.filter((file) => !snapshotHasBefore(applySnapshots, file));
    const reverseDiff = reverseUnifiedDiff(proposedDiff);
    const reversalAvailable = reverseDiff.trim().length > 0;
    if (appliedChangedFiles.length === 0 || diskChangedFiles.length === 0) {
      return baseResult({
        applied_changed_files: appliedChangedFiles,
        checks_result: "recorded",
        disk_changed_files: [],
        failure_reason: "FAIL: No disk change",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        reverse_diff: reverseDiff,
        reversal_available: reversalAvailable,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    if (previewChangedFiles.length === 0 || missingBeforeSnapshots.length > 0) {
      return baseResult({
        applied_changed_files: appliedChangedFiles,
        checks_result: "recorded",
        disk_changed_files: diskChangedFiles,
        failure_reason:
          previewChangedFiles.length === 0
            ? "Needs fix: generated diff did not produce preview changed files."
            : `Needs fix: before snapshot missing for ${formatList(missingBeforeSnapshots, "changed files")}.`,
        model_called_for_generation: modelCalledForGeneration,
        next_recommended_action: "Require changed-file preview proof and server backup snapshots before counting an edit trial as PASS.",
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        reverse_diff: reverseDiff,
        reversal_available: reversalAvailable,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    if (!reversalAvailable) {
      return baseResult({
        applied_changed_files: appliedChangedFiles,
        checks_result: "recorded",
        disk_changed_files: diskChangedFiles,
        failure_reason: "FAIL: No reversal receipt",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        reverse_diff: reverseDiff,
        reversal_available: false,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }

    const suiteAppliedAt = new Date().toISOString();
    const suiteReceiptId = `trial-suite:${prompt.id}:${taskId}`;
    updateAppliedRunReceipts((receipts) =>
      appendAppliedRunReceipt(
        receipts,
        buildSuiteTrialReceipt({
          allowedFiles: packet.allowedFiles,
          appliedAt: suiteAppliedAt,
          changedFiles: appliedChangedFiles,
          diff: proposedDiff,
          model: modelCalledForGeneration,
          prompt,
          provider: providerTruth.providerLabel,
          reverseDiff,
          revertedAt: null,
          runId: taskId,
          target: packet.selectedTarget ?? prompt.targetFile,
        }),
      ),
    );

    if (!prompt.autoRevert) {
      onStep?.("Ready for review");
      return baseResult({
        applied_changed_files: appliedChangedFiles,
        checks_result: "git diff --check recorded",
        disk_changed_files: diskChangedFiles,
        failure_reason: "",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        reverse_diff: reverseDiff,
        reverse_status_text: "Applied; reverse manually with Reverse trial edits when finished inspecting.",
        reverted: false,
        reversal_available: true,
        run_id: taskId,
        visible_result_label: "PASS",
      });
    }

    onStep?.("Undoing trial edit");
    const revertTaskResponse = await fetch("/v1/tasks/long-running", {
      body: JSON.stringify({ description: `Revert reversible trial ${prompt.id}` }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const revertTaskPayload = await readJson(revertTaskResponse);
    endpointStatuses.push(`/v1/tasks/long-running(revert):${revertTaskResponse.status}`);
    if (!revertTaskResponse.ok) {
      return baseResult({
        applied_changed_files: appliedChangedFiles,
        checks_result: "recorded",
        disk_changed_files: diskChangedFiles,
        endpoint_statuses: [...endpointStatuses],
        error_summary: safePayloadSummary(revertTaskPayload),
        failure_reason: messageFromPayload(revertTaskPayload, revertTaskResponse.status),
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        reverse_diff: reverseDiff,
        reverse_status_text: `Needs manual reverse: ${formatList(diskChangedFiles, "changed files not recorded")}`,
        reversal_available: true,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    const revertTaskId = taskIdFromPayload(revertTaskPayload);
    if (!revertTaskId) {
      return baseResult({
        applied_changed_files: appliedChangedFiles,
        checks_result: "recorded",
        disk_changed_files: diskChangedFiles,
        endpoint_statuses: [...endpointStatuses],
        failure_reason: "Reverse task create did not return a task id.",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        reverse_diff: reverseDiff,
        reverse_status_text: `Needs manual reverse: ${formatList(diskChangedFiles, "changed files not recorded")}`,
        reversal_available: true,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    const revertResponse = await fetch("/v1/actions/execute-approved", {
      body: JSON.stringify({
        action: `Revert live trial ${prompt.id}`,
        approved: true,
        approved_diff: reverseDiff,
        allowed_files: packet.allowedFiles,
        target: packet.selectedTarget,
        task_id: revertTaskId,
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const revertPayload = await readJson(revertResponse);
    endpointStatuses.push(`/v1/actions/execute-approved(revert):${revertResponse.status}`);
    if (!revertResponse.ok) {
      return baseResult({
        applied_changed_files: appliedChangedFiles,
        checks_result: "recorded",
        disk_changed_files: diskChangedFiles,
        endpoint_statuses: [...endpointStatuses],
        error_summary: safePayloadSummary(revertPayload),
        failure_reason: messageFromPayload(revertPayload, revertResponse.status),
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        reverse_diff: reverseDiff,
        reverse_status_text: `Needs manual reverse: ${formatList(diskChangedFiles, "changed files not recorded")}`,
        reversal_available: true,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    const revertSnapshots = changedFileSnapshotsFromPayload(revertPayload);
    const notRestoredFiles = appliedChangedFiles.filter((file) => !snapshotRestored(applySnapshots, revertSnapshots, file));
    if (notRestoredFiles.length > 0) {
      return baseResult({
        applied_changed_files: appliedChangedFiles,
        checks_result: "recorded",
        disk_changed_files: diskChangedFiles,
        endpoint_statuses: [...endpointStatuses],
        error_summary: safePayloadSummary(revertPayload),
        failure_reason: `Needs fix: reverse did not restore the before snapshot for ${formatList(notRestoredFiles, "changed files")}.`,
        model_called_for_generation: modelCalledForGeneration,
        next_recommended_action: "Inspect the reverse diff and restore the listed files before rerunning Coder 10.",
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        reverse_diff: reverseDiff,
        reverse_status_text: `Reverse incomplete: ${formatList(notRestoredFiles, "changed files")}`,
        reversal_available: true,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    onStep?.("Checking work");
    const revertedAt = new Date().toISOString();
    updateAppliedRunReceipts((receipts) =>
      receipts.map((receipt) =>
        receipt.id === suiteReceiptId
          ? {
              ...receipt,
              revertedAt,
              reversalModel: modelCalledForGeneration,
              reversalProvider: providerTruth.providerLabel,
              reversalProviderModelSource: "trial-suite",
            }
          : receipt,
      ),
    );
    return baseResult({
      applied_changed_files: appliedChangedFiles,
      checks_result: "git diff --check recorded",
      disk_changed_files: diskChangedFiles,
      failure_reason: "",
      model_called_for_generation: modelCalledForGeneration,
      provider: providerTruth.providerLabel,
      provider_call_made: true,
      preview_changed_files: previewChangedFiles,
      reverse_diff: reverseDiff,
      reverse_status_text: "Reverted clean after live apply (worked + reverted).",
      reverted: true,
      reversal_available: true,
      run_id: taskId,
      visible_result_label: "REVERTED",
    });
  }

  async function handleRunReversibleSuite(resumeState?: ReversibleSuiteState) {
    if (reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping") return;
    if (!normalizeReversibleTrialCategoryInput(reversibleTrialCategory)) {
      setReversibleSuiteCopyStatus(
        `Category invalid: "${reversibleTrialCategory}". Use ${reversibleTrialCategories.join(", ")}.`,
      );
      return;
    }
    const isResume = Boolean(resumeState?.suiteId);
    const runCount = resumeState?.count ?? reversibleTrialCount;
    const suiteId = resumeState?.suiteId || `suite-${Date.now().toString(36)}`;
    const prompts = selectReversibleTrialPrompts(runCount, reversibleTrialCategory);
    const startIndex = isResume ? Math.min(Math.max(resumeState?.completed ?? 0, 0), prompts.length) : 0;
    const modelLaneUnavailable =
      !sourceProxyReachable ||
      selectedProviderTruth.status === "unavailable" ||
      selectedProviderTruth.providerModelProbeOk === false;
    if (!isResume && modelLaneUnavailable) {
      const reason = !sourceProxyReachable
        ? "Source Proxy is unreachable at /v1/self/status."
        : selectedProviderTruth.blockedReason ||
          `${selectedProviderTruth.modelLabel} is not available from the configured local model lane.`;
      const blockedState: ReversibleSuiteState = {
        completed: 0,
        count: runCount,
        currentPrompt: "",
        currentPromptElapsedMs: null,
        currentStep: "Blocked before model proof",
        currentStepStartedAt: null,
        alreadySatisfied: 0,
        expectedNoEdit: 0,
        fail: 0,
        interruptionReason: `model_lane_unavailable: ${reason}`,
        interruptionSource: "route_failed",
        pass: 0,
        provider: selectedProviderTruth.providerLabel,
        model: selectedProviderTruth.modelLabel,
        results: [],
        reverted: 0,
        safetyBlock: 0,
        status: "failed",
        stopped: false,
        suiteFinishedAt: performance.now(),
        suiteId,
        suiteStartedAt: performance.now(),
        timeout: 0,
      };
      setReversibleSuiteCopyStatus(
        `Trial blocked before run: ${reason} Run curl -k https://127.0.0.1:8787/v1/models and install or select an available Ollama model.`,
      );
      setReversibleSuiteState(blockedState);
      storeReversibleSuiteState(blockedState);
      return;
    }
    stopReversibleSuiteAfterCurrentRef.current = false;
    setReversibleSuiteCopyStatus(
      isResume && startIndex < prompts.length
        ? `Resuming suite ${suiteId}: ${startIndex}/${prompts.length} complete.`
        : "",
    );
    setReversiblePromptsCopyStatus("");
    if (!isResume) {
      updateAppliedRunReceipts((receipts) =>
        receipts.filter((receipt) => !receipt.id.startsWith("trial-suite:")),
      );
      clearStoredReversibleSuiteState();
    }
    const suiteStartedAt = resumeState?.suiteStartedAt ?? performance.now();
    const currentStepStartedAt = performance.now();
    const initialSuiteState: ReversibleSuiteState = {
      completed: resumeState?.completed ?? 0,
      count: runCount,
      currentPrompt:
        startIndex < prompts.length
          ? `${startIndex + 1}/${prompts.length}: ${prompts[startIndex]?.quickTitle ?? "Resuming"}`
          : "Suite finished.",
      currentPromptElapsedMs: null,
      currentStep: isResume ? "Resuming after browser refresh/dev reload" : "Reading request",
      currentStepStartedAt,
      alreadySatisfied: resumeState?.alreadySatisfied ?? 0,
      expectedNoEdit: resumeState?.expectedNoEdit ?? 0,
      fail: resumeState?.fail ?? 0,
      interruptionReason: null,
      interruptionSource: "none",
      pass: resumeState?.pass ?? 0,
      provider: resumeState?.provider || selectedProviderTruth.providerLabel,
      model: resumeState?.model || selectedProviderTruth.modelLabel,
      results: resumeState?.results ?? [],
      reverted: resumeState?.reverted ?? 0,
      safetyBlock: resumeState?.safetyBlock ?? 0,
      status: "running",
      stopped: false,
      suiteFinishedAt: null,
      suiteId,
      suiteStartedAt,
      timeout: resumeState?.timeout ?? 0,
    };
    setReversibleSuiteState(initialSuiteState);
    storeReversibleSuiteState(initialSuiteState);
    let nextState: ReversibleSuiteState = initialSuiteState;
    let suiteAbort: ReversibleSuiteAbort | null = null;
    try {
      for (let index = startIndex; index < prompts.length; index += 1) {
        const prompt = prompts[index];
        if (!prompt) continue;
        nextState = {
          ...nextState,
          currentPrompt: `${index + 1}/${prompts.length}: ${prompt.quickTitle}`,
          currentStep: "Reading request",
          currentPromptElapsedMs: null,
          interruptionReason: null,
          interruptionSource: "none",
          status: stopReversibleSuiteAfterCurrentRef.current ? "stopping" : "running",
        };
        setReversibleSuiteState(nextState);
        storeReversibleSuiteState(nextState);
        let result: ReversibleSuitePromptResult;
        try {
          const promptStartedAt = performance.now();
          if (
            prompt.expectedOutcome === "edit_reversible" &&
            prompt.targetFile.includes("dummy-coding-targets/")
          ) {
            await prepareDummyTrialFixtureForReversibleApply(prompt.targetFile, (step) => {
              nextState = {
                ...nextState,
                currentStep: step,
                currentStepStartedAt: performance.now(),
                currentPromptElapsedMs: elapsedMs(promptStartedAt),
              };
              setReversibleSuiteState(nextState);
              storeReversibleSuiteState(nextState);
            });
          }
          result = await runOneReversibleTrialPrompt(prompt, (step) => {
            nextState = {
              ...nextState,
              currentStep: step,
              currentStepStartedAt: performance.now(),
              currentPromptElapsedMs: elapsedMs(promptStartedAt),
            };
            setReversibleSuiteState(nextState);
            storeReversibleSuiteState(nextState);
          });
          result = { ...result, elapsed_ms: elapsedMs(promptStartedAt) };
        } catch (error) {
          const failureReason = error instanceof Error ? error.message : "Trial prompt failed.";
          result = {
            allowed_files: prompt.expected_scope,
            applied_changed_files: [],
            checks_result: "failed before completion",
            checks_run: ["git diff --check"],
            disk_changed_files: [],
            endpoint_statuses: [],
            error_summary: "",
            expected_outcome: prompt.expectedOutcome,
            failure_reason: failureReason,
            model_called_for_generation: "none",
            next_recommended_action: "Copy diagnostics and inspect the failed prompt runner exception.",
            prompt,
            provider: selectedProviderTruth.providerLabel,
            provider_call_made: false,
            preview_changed_files: [],
            reverse_diff: "",
            reverse_status_text: "No applied trial edits to reverse.",
            reverted: false,
            reversal_available: false,
            run_id: "",
            selected_target: prompt.targetFile,
            target_candidates: prompt.expected_scope,
            visible_result_label: reversibleSuiteExceptionLabel(failureReason),
            elapsed_ms: null,
          };
        }
        const alreadySatisfiedPassed = reversibleResultIsAlreadySatisfied(result);
        const safetyBlockPassed = reversibleResultIsSafetyBlock(result);
        const timeoutFailure = reversibleResultIsTimeout(result);
        const expectedNoEditPassed =
          result.visible_result_label === "NO EDIT EXPECTED" ||
          (safetyBlockPassed && result.expected_outcome !== "edit_reversible");
        const editPassed =
          result.visible_result_label === "PASS" ||
          result.visible_result_label === "REVERTED";
        const revertedPass = result.visible_result_label === "REVERTED";
        const bucketedSuccess =
          editPassed ||
          alreadySatisfiedPassed ||
          expectedNoEditPassed ||
          (safetyBlockPassed && result.expected_outcome === "safety_block_expected");
        nextState = {
          ...nextState,
          completed: nextState.completed + 1,
          currentPrompt: `${index + 1}/${prompts.length}: ${prompt.quickTitle}`,
          currentStep: bucketedSuccess ? "Ready to review" : "Needs fix",
          alreadySatisfied: nextState.alreadySatisfied + (alreadySatisfiedPassed ? 1 : 0),
          expectedNoEdit: nextState.expectedNoEdit + (expectedNoEditPassed ? 1 : 0),
          fail: nextState.fail + (bucketedSuccess ? 0 : 1),
          pass: nextState.pass + (editPassed && !revertedPass ? 1 : 0),
          provider: result.provider || nextState.provider,
          model:
            result.model_called_for_generation && result.model_called_for_generation !== "none"
              ? result.model_called_for_generation
              : nextState.model,
          results: [...nextState.results, result],
          reverted: nextState.reverted + (result.reverted ? 1 : 0),
          safetyBlock: nextState.safetyBlock + (safetyBlockPassed ? 1 : 0),
          status: stopReversibleSuiteAfterCurrentRef.current ? "stopping" : "running",
          timeout: nextState.timeout + (timeoutFailure ? 1 : 0),
        };
        if (result.reverted && result.reversal_available && prompt.autoRevert) {
          updateAppliedRunReceipts((receipts) => syncSuiteReceiptRevertState(receipts, result));
        }
        setReversibleSuiteState(nextState);
        storeReversibleSuiteState(nextState);
        suiteAbort = reversibleSuiteAbortForResult(result);
        if (suiteAbort) {
          nextState = {
            ...nextState,
            currentStep: suiteAbort.step,
            interruptionReason: suiteAbort.reason,
            interruptionSource: suiteAbort.source,
            status: "failed",
          };
          setReversibleSuiteState(nextState);
          storeReversibleSuiteState(nextState);
          break;
        }
        if (stopReversibleSuiteAfterCurrentRef.current) break;
      }
      const suiteFinishedAt = performance.now();
      const stoppedByUser = stopReversibleSuiteAfterCurrentRef.current;
      const doneState = {
        ...nextState,
        currentPrompt: nextState.completed > 0 ? "Suite finished." : "",
        currentStep: stoppedByUser ? "Stopped after current prompt" : suiteAbort?.step ?? "Finished",
        currentStepStartedAt: null,
        interruptionReason: stoppedByUser ? "user_clicked_stop_after_current_prompt" : suiteAbort?.reason ?? null,
        interruptionSource: stoppedByUser ? "user_stop" as const : suiteAbort?.source ?? "none" as const,
        status: nextState.fail > 0 || suiteAbort ? "failed" as const : "done" as const,
        stopped: stoppedByUser,
        suiteFinishedAt,
      };
      updateAppliedRunReceipts((receipts) =>
        doneState.results.reduce(
          (current, result) =>
            result.reverted && result.reversal_available
              ? syncSuiteReceiptRevertState(current, result)
              : current,
          receipts,
        ),
      );
      setReversibleSuiteState(doneState);
      storeReversibleSuiteState(doneState);
      const passCount = doneState.results.filter((result) => result.visible_result_label === "PASS").length;
      if (suiteAbort) {
        setReversibleSuiteCopyStatus(
          `${suiteAbort.step}. Copy diagnostics, check Source Proxy health, then rerun the bounded suite.`,
        );
      } else if (passCount > 0) {
        const uniqueTargets = new Set(
          doneState.results
            .filter((result) => result.reversal_available && !result.reverted)
            .map((result) => suiteResultTargetKey(result)),
        );
        setReversibleSuiteCopyStatus(
          uniqueTargets.size < passCount
            ? `Suite finished: ${passCount} PASS edit(s) across ${uniqueTargets.size} fixture file(s). Reverse once per file when done inspecting.`
            : `Suite finished: ${passCount} edit(s) applied. Use Reverse trial edits when done inspecting.`,
        );
      }
    } catch {
      setReversibleSuiteState((current) => {
        const failedState = {
          ...current,
          status: "failed" as const,
          currentStepStartedAt: null,
          interruptionReason: current.interruptionReason ?? "route_failed",
          interruptionSource:
            current.interruptionSource === "none" ? "route_failed" as const : current.interruptionSource,
          suiteFinishedAt: current.suiteFinishedAt ?? performance.now(),
        };
        storeReversibleSuiteState(failedState);
        return failedState;
      });
    }
  }

  function handleStopReversibleSuiteAfterCurrent() {
    stopReversibleSuiteAfterCurrentRef.current = true;
    setReversibleSuiteState((current) => {
      const stoppingState = {
        ...current,
        interruptionReason: "user_clicked_stop_after_current_prompt",
        interruptionSource: "user_stop" as const,
        status: current.status === "running" ? "stopping" as const : current.status,
        stopped: true,
      };
      storeReversibleSuiteState(stoppingState);
      return stoppingState;
    });
  }

  async function handleReverseRemainingTrialEdits(options: { clearSuiteAfter?: boolean } = {}) {
    const remainingFromSuite = latestUnrevertedSuiteResultsByTarget(reversibleSuiteState.results);
    const remainingFromReceipts = orphanUnrevertedTrialReceipts.filter((receipt) =>
      receipt.id.startsWith("trial-suite:"),
    );
    const totalRemaining = remainingFromSuite.length + remainingFromReceipts.length;
    if (totalRemaining === 0 || isReverting) {
      setReversibleSuiteCopyStatus(
        totalRemaining === 0
          ? "No trial edits are waiting for reverse."
          : "Reverse already in progress.",
      );
      return;
    }
    setIsReverting(true);
    setReversibleSuiteCopyStatus(`Undoing ${totalRemaining} trial edit(s)...`);
    const revertedSuiteKeys = new Set<string>();
    const revertedReceiptIds = new Set<string>();
    const revertedTargets = new Set<string>();
    const failures: string[] = [];
    const allSuiteResults = reversibleSuiteState.results;
    try {
      const suiteReceipts = remainingFromSuite.map((result) =>
        receiptForSuiteReverseResult(result, appliedRunReceipts),
      );
      const receiptsById = new Map(
        [...appliedRunReceipts, ...suiteReceipts].map((receipt) => [receipt.id, receipt]),
      );
      let reconciledReceipts = await reconcileTrialReceiptsViaApi([...receiptsById.values()]);
      updateAppliedRunReceipts((current) => {
        const merged = new Map(current.map((receipt) => [receipt.id, receipt]));
        for (const receipt of reconciledReceipts) {
          merged.set(receipt.id, receipt);
        }
        reconciledReceipts = [...merged.values()];
        return reconciledReceipts;
      });

      for (const result of remainingFromSuite.slice().reverse()) {
        const receipt = receiptForSuiteReverseResult(result, reconciledReceipts);
        const reconciled = reconciledReceipts.find((item) => item.id === receipt.id) ?? receipt;
        const targetKey = suiteResultTargetKey(result);
        if (revertedTargets.has(targetKey)) {
          revertedSuiteKeys.add(`${result.prompt.id}:${result.run_id}`);
          revertedReceiptIds.add(receipt.id);
          continue;
        }
        if (reconciled.revertedAt || reconciled.staleResolvedAt) {
          revertedSuiteKeys.add(`${result.prompt.id}:${result.run_id}`);
          revertedReceiptIds.add(receipt.id);
          if (reconciled.staleResolvedAt) {
            revertedTargets.add(targetKey);
            registerSuiteTargetReverted(
              targetKey,
              allSuiteResults,
              reconciledReceipts,
              revertedSuiteKeys,
              revertedReceiptIds,
            );
          }
          continue;
        }
        try {
          await applyReverseReceipt(receipt);
        } catch (error) {
          const message = error instanceof Error ? error.message : "Reverse apply failed.";
          const [freshReceipt] = await reconcileTrialReceiptsViaApi([receipt]);
          if (freshReceipt?.staleResolvedAt || reversalLooksAlreadyApplied(message)) {
            revertedTargets.add(targetKey);
            registerSuiteTargetReverted(
              targetKey,
              allSuiteResults,
              reconciledReceipts,
              revertedSuiteKeys,
              revertedReceiptIds,
            );
            if (freshReceipt) {
              reconciledReceipts = reconciledReceipts.map((item) =>
                item.id === freshReceipt.id ? freshReceipt : item,
              );
            }
            continue;
          }
          const baselineReset = buildDummyTrialBaselineResetReceipt(
            receipt.target,
            receipt,
            trialFixtureBaselines,
          );
          if (baselineReset) {
            try {
              await applyReverseReceipt(baselineReset);
              revertedTargets.add(targetKey);
              registerSuiteTargetReverted(
                targetKey,
                allSuiteResults,
                reconciledReceipts,
                revertedSuiteKeys,
                revertedReceiptIds,
              );
              continue;
            } catch (resetError) {
              const resetMessage =
                resetError instanceof Error ? resetError.message : "Baseline fixture reset failed.";
              const [freshReceipt] = await reconcileTrialReceiptsViaApi([receipt]);
              if (freshReceipt?.staleResolvedAt || reversalLooksAlreadyApplied(resetMessage)) {
                revertedTargets.add(targetKey);
                registerSuiteTargetReverted(
                  targetKey,
                  allSuiteResults,
                  reconciledReceipts,
                  revertedSuiteKeys,
                  revertedReceiptIds,
                );
                continue;
              }
              failures.push(`${receipt.target}: ${resetMessage}`);
              continue;
            }
          }
          failures.push(`${receipt.target}: ${message}`);
          continue;
        }
        revertedTargets.add(targetKey);
        registerSuiteTargetReverted(
          targetKey,
          allSuiteResults,
          reconciledReceipts,
          revertedSuiteKeys,
          revertedReceiptIds,
        );
      }
      for (const receipt of remainingFromReceipts.slice().reverse()) {
        const reconciled = reconciledReceipts.find((item) => item.id === receipt.id) ?? receipt;
        if (reconciled.revertedAt || reconciled.staleResolvedAt) {
          revertedReceiptIds.add(receipt.id);
          continue;
        }
        try {
          await applyReverseReceipt(receipt);
        } catch (error) {
          const message = error instanceof Error ? error.message : "Reverse apply failed.";
          const [freshReceipt] = await reconcileTrialReceiptsViaApi([receipt]);
          if (freshReceipt?.staleResolvedAt || reversalLooksAlreadyApplied(message)) {
            revertedReceiptIds.add(receipt.id);
            continue;
          }
          const baselineReset = buildDummyTrialBaselineResetReceipt(
            receipt.target,
            receipt,
            trialFixtureBaselines,
          );
          if (baselineReset) {
            try {
              await applyReverseReceipt(baselineReset);
              revertedReceiptIds.add(receipt.id);
              continue;
            } catch (resetError) {
              const resetMessage =
                resetError instanceof Error ? resetError.message : "Baseline fixture reset failed.";
              failures.push(`${receipt.target}: ${resetMessage}`);
              continue;
            }
          }
          failures.push(`${receipt.target}: ${message}`);
          continue;
        }
        revertedReceiptIds.add(receipt.id);
      }
      const revertedAt = new Date().toISOString();
      const revertedCount = revertedReceiptIds.size;
      if (revertedCount > 0) {
        updateAppliedRunReceipts((receipts) =>
          receipts.map((receipt) =>
            revertedReceiptIds.has(receipt.id)
              ? {
                  ...receipt,
                  revertedAt,
                  reversalModel: receipt.model,
                  reversalProvider: receipt.provider,
                  reversalProviderModelSource: "trial-suite",
                }
              : receipt,
          ),
        );
        setReversibleSuiteState((current) => ({
          ...current,
          reverted: current.results.filter(
            (result) =>
              result.reversal_available &&
              (result.reverted || revertedSuiteKeys.has(`${result.prompt.id}:${result.run_id}`)),
          ).length,
          results: syncReversibleSuiteResultsFromReceipts(
            current.results.map((result) =>
              revertedSuiteKeys.has(`${result.prompt.id}:${result.run_id}`)
                ? {
                    ...result,
                    reverted: true,
                    reverse_status_text: "Reversed manually through trial runner controls.",
                  }
                : result,
            ),
            reconciledReceipts,
          ),
        }));
      }
      const revertedTargetCount = revertedTargets.size;
      if (options.clearSuiteAfter && failures.length === 0) {
        clearReversibleSuitePanel();
        setReversibleSuiteCopyStatus(
          revertedTargetCount > 0
            ? `Reversed ${revertedTargetCount} fixture file(s) and cleared suite results.`
            : "No fixture edits were pending; cleared suite results.",
        );
        return;
      }
      setReversibleSuiteCopyStatus(
        failures.length > 0
          ? `Reversed ${revertedTargetCount} fixture file(s). ${failures.length} item(s) still need attention: ${failures[0]}`
          : revertedTargetCount > 0
            ? revertedCount > revertedTargetCount
              ? `Reversed ${revertedTargetCount} fixture file(s) (${revertedCount} catalog receipt(s) cleared).`
              : `Reversed ${revertedTargetCount} fixture file(s).`
            : "No trial edits were reversed. Check diagnostics for blocker details.",
      );
    } finally {
      setIsReverting(false);
    }
  }

  async function handleDraftPreview() {
    const runStartedAt = performance.now();
    setComposerTiming({
      diffPreviewMs: null,
      promptPacketMs: null,
      runStartedAt,
      totalMs: null,
    });
    if (!canPreview) {
      setDraftReady(hasTaskDraft);
      setDiagnosticCopyStatus("");
      setVerificationCopyStatus("");
      setPreviewState(idlePreviewState());
      return;
    }
    setDraftReady(true);
    rememberPromptSnapshot(task);
    setReversalStatus("");
    if (trialMode !== "code" && (currentDesignTaskKind || showCombinedFlow)) {
      setDiagnosticCopyStatus("");
      setVerificationCopyStatus("");
      setPreviewState(idlePreviewState());
      return;
    }
    const startedEvents = [
      manualEvent("received", "done", "Prompt received from the manual composer."),
      manualEvent("analyzing", "running", "Reading the request and checking for protected paths or ambiguity."),
    ];
    const selectedTruth = selectedProviderTruth;
    setPreviewState({
      approvalAvailable: false,
      approvedAt: null,
      appliedAt: null,
      applySummary: "",
      allowedFiles: [],
      blocker: null,
      changedFiles: [],
      checks: ["git diff --check"],
      currentPhase: manualTaskPhaseLabels.analyzing,
      diff: "",
      error: null,
      events: startedEvents,
      forbiddenFiles: PROTECTED_FORBIDDEN_FILES,
      isApplying: false,
      isLoading: true,
      ...providerTruthPatch(selectedTruth),
      previewStatus: "starting",
      requirementSummary: "Waiting for preview.",
      reasonCode: null,
      reviewerSummary: "Waiting for preview.",
      routeCalled: null,
      selectedTarget: null,
      status: "idle",
      targetCandidates: [],
      targetMatch: false,
      taskId: "",
      taskSpecAllowed: false,
      verifierSummary: "Waiting for preview.",
      technicalDetail: null,
    });
    try {
      const packet = buildManualTaskPacket({
        allowedFilesText: allowedFiles,
        expectedChecksText: expectedChecks,
        prompt: task,
        targetFile,
      });
      const discoveredEvents = [
        manualEvent("received", "done", "Prompt received from the manual composer."),
        manualEvent("analyzing", "done", "Request analyzed without requiring frontend scope fields."),
        manualEvent(
          "discovering",
          packet.reasonCode ? "blocked" : "done",
          packet.targetCandidates.length > 0
            ? `Likely files: ${packet.targetCandidates.join(", ")}.`
            : "No confident target file could be inferred from the prompt.",
        ),
      ];
      setPreviewState((current) => ({
        ...current,
        allowedFiles: packet.allowedFiles,
        checks: packet.checks,
        currentPhase: packet.reasonCode ? manualTaskPhaseLabels.blocked : manualTaskPhaseLabels.discovering,
        events: discoveredEvents,
        forbiddenFiles: packet.forbiddenFiles,
        reasonCode: packet.reasonCode,
        selectedTarget: packet.selectedTarget,
        targetCandidates: packet.targetCandidates,
      }));

      if (packet.reasonCode === "protected_path_request") {
        setPreviewState((current) => ({
          ...current,
          blocker: "Protected path request blocked before preview. No files were inspected or changed.",
          currentPhase: manualTaskPhaseLabels.blocked,
          error: null,
          events: [
            ...discoveredEvents,
            manualEvent("blocked", "blocked", "The prompt points at .env, secrets, or source_proxy/data. Preview was not called."),
          ],
          isLoading: false,
          previewStatus: "blocked before preview",
          requirementSummary: "Safety gate blocked protected paths.",
          reviewerSummary: "No reviewer evidence because protected scope was blocked.",
          reasonCode: "protected_path_request",
          status: "blocked",
          technicalDetail: "protected_path_request",
          verifierSummary: "No checks run because preview was blocked before execution.",
        }));
        return;
      }

      if (packet.reasonCode === "wrong_file_scope_conflict") {
        setPreviewState((current) => ({
          ...current,
          blocker: "Wrong-file scope conflict blocked before preview. The prompt points at production or package files while limiting the allowed file to a dummy fixture.",
          currentPhase: manualTaskPhaseLabels.blocked,
          error: null,
          events: [
            ...discoveredEvents,
            manualEvent("blocked", "blocked", "Conflicting target scope was detected, so no preview diff was requested."),
          ],
          isLoading: false,
          previewStatus: "blocked before preview",
          requirementSummary: "Safety gate blocked conflicting wrong-file scope.",
          reviewerSummary: "No reviewer evidence because conflicting scope was blocked.",
          reasonCode: "wrong_file_scope_conflict",
          status: "blocked",
          technicalDetail: "wrong_file_scope_conflict",
          verifierSummary: "Recommended check: confirm allowed files exclude production and package paths.",
        }));
        return;
      }

      if (packet.reasonCode === "manual_clarification_needed" || !packet.selectedTarget) {
        setPreviewState((current) => ({
          ...current,
          blocker: "I need one more detail before I can choose a file safely. Which screen, component, or file should this change touch?",
          currentPhase: manualTaskPhaseLabels.blocked,
          error: null,
          events: [
            ...discoveredEvents,
            manualEvent("blocked", "blocked", "Discovery confidence was too low, so no preview diff was requested."),
          ],
          isLoading: false,
          previewStatus: "clarification needed",
          requirementSummary: "Clarification needed before building a bounded task packet.",
          reviewerSummary: "No reviewer evidence because no diff was requested.",
          reasonCode: "manual_clarification_needed",
          status: "blocked",
          technicalDetail: "manual_clarification_needed",
          verifierSummary: "Recommended after clarification: git diff --check.",
        }));
        return;
      }

      const packetEvents = [
        ...discoveredEvents,
        manualEvent("packet", "done", `Task packet built internally for ${packet.selectedTarget}.`),
        manualEvent("preview", "running", "Calling the existing prompt-packet preview route."),
      ];
      setManualProgress(packetEvents, "preview");
      setPreviewState((current) => ({
        ...current,
        routeCalled: "/v1/decisions/prompt-packet",
      }));

      const trimmedTarget = packet.selectedTarget;
      const taskSpec = {
        allowed_files: packet.allowedFiles,
        forbidden_files: packet.forbiddenFiles,
        risk_tier: "low",
        schema_version: 1,
        source: "coding_cockpit_manual_natural_runner",
        target: trimmedTarget,
        task_type: "modify_existing_file",
        verification: packet.checks,
      };
      const promptTask = taskTextForPromptPacket(packet.taskText, trimmedTarget);
      const promptPacketStartedAt = performance.now();
      const proposalResponse = await fetchWithTimeout(
        "/v1/decisions/prompt-packet",
        {
          body: JSON.stringify({
            expected_outcome: "edit_reversible",
            needs_codebase_context: true,
            prefer_free: true,
            quick_find_hints: packet.targetCandidates,
            selected_target: trimmedTarget,
            target_files: packet.allowedFiles,
            targeted_files: packet.allowedFiles,
            task: promptTask,
            trial_mode: "live_apply",
            wants_implementation: true,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
        MANUAL_PROMPT_PACKET_TIMEOUT_MS,
      );
      const promptPacketMs = elapsedMs(promptPacketStartedAt);
      setComposerTiming((current) => ({
        ...current,
        promptPacketMs,
      }));
      const proposalPayload = await readJson(proposalResponse);
      if (!proposalResponse.ok) {
        throw new Error(messageFromPayload(proposalPayload, proposalResponse.status));
      }
      const proposalProviderTruth = providerModelTruthFromPayload(proposalPayload, selectedTruth);
      const modelCalledForGeneration = proposalProviderTruth.modelCalledForGeneration ?? "none";
      const proposedDiff = diffFromPayload(proposalPayload);
      const alreadySatisfied = isCoderAlreadySatisfied(proposalPayload);
      if (!proposedDiff && alreadySatisfied) {
        const alreadySatisfiedBlocker = "Task appears already done. No diff is required.";
        setPreviewState({
          approvalAvailable: false,
          approvedAt: null,
          appliedAt: null,
          applySummary: "",
          allowedFiles: packet.allowedFiles,
          blocker: alreadySatisfiedBlocker,
          changedFiles: [],
          checks: packet.checks,
          currentPhase: manualTaskPhaseLabels.done,
          diff: "",
          error: null,
          events: [
            ...packetEvents,
            manualEvent("preview", "done", "Coder reported no changes needed because the target already satisfies the request."),
            manualEvent("review", "done", "Coder reported no changes needed because the target already satisfies the request."),
            manualEvent("done", "done", "No preview diff was needed and no files were changed."),
          ],
          forbiddenFiles: packet.forbiddenFiles,
          isApplying: false,
          isLoading: false,
          ...providerTruthPatch(proposalProviderTruth),
          previewStatus: "already satisfied",
          requirementSummary:
            "The task appears already done. No approval or apply is available because there is no diff.",
          reasonCode: "coder_no_changes_needed",
          reviewerSummary: "Already satisfied; no diff invented.",
          routeCalled: "/v1/decisions/prompt-packet",
          selectedTarget: packet.selectedTarget,
          status: "satisfied",
          targetCandidates: packet.targetCandidates,
          targetMatch: true,
          taskId: taskIdFromPayload(proposalPayload),
          taskSpecAllowed: true,
          verifierSummary: "No diff to verify. Recommended check: git diff --check.",
          technicalDetail: "coder_no_changes_needed",
        });
        return;
      }
      if (!proposalProviderTruth.providerCallMade || modelCalledForGeneration === "none") {
        setPreviewState({
          approvalAvailable: false,
          approvedAt: null,
          appliedAt: null,
          applySummary: "",
          allowedFiles: packet.allowedFiles,
          blocker: "FAIL: No model call",
          changedFiles: [],
          checks: packet.checks,
          currentPhase: manualTaskPhaseLabels.failed,
          diff: "",
          error: "FAIL: No model call",
          events: [
            ...packetEvents,
            manualEvent("preview", "failed", "The route did not record provider_call_made=true and a generation model."),
            manualEvent("failed", "failed", "Live apply proof is missing; no files were changed."),
          ],
          forbiddenFiles: packet.forbiddenFiles,
          isApplying: false,
          isLoading: false,
          ...providerTruthPatch(proposalProviderTruth),
          previewStatus: "failed no model call",
          requirementSummary: "NO-GO: Live apply proof missing.",
          reasonCode: "no_model_call",
          reviewerSummary: "No disk edit allowed without live model proof.",
          routeCalled: "/v1/decisions/prompt-packet",
          selectedTarget: packet.selectedTarget,
          status: "error",
          targetCandidates: packet.targetCandidates,
          targetMatch: false,
          taskId: taskIdFromPayload(proposalPayload),
          taskSpecAllowed: false,
          verifierSummary: "No checks run because no model call was proven.",
          technicalDetail: "provider_call_made/model_called_for_generation proof missing",
        });
        return;
      }

      if (!proposedDiff) {
        const reasonCode = noDiffReasonCodeFromPayload(proposalPayload);
        if (alreadySatisfied) {
          const alreadySatisfiedBlocker = "Task appears already done. No diff is required.";
          setPreviewState({
            approvalAvailable: false,
            approvedAt: null,
            appliedAt: null,
            applySummary: "",
            allowedFiles: packet.allowedFiles,
            blocker: alreadySatisfiedBlocker,
            changedFiles: [],
            checks: packet.checks,
            currentPhase: manualTaskPhaseLabels.done,
            diff: "",
            error: null,
            events: [
              ...packetEvents,
              manualEvent("review", "done", "Coder reported no changes needed because the target already satisfies the request."),
              manualEvent("done", "done", "No preview diff was needed and no files were changed."),
            ],
            forbiddenFiles: packet.forbiddenFiles,
            isApplying: false,
            isLoading: false,
            ...providerTruthPatch(proposalProviderTruth),
            previewStatus: "already satisfied",
            requirementSummary:
          "The task appears already done. No approval or apply is available because there is no diff.",
            reasonCode: "coder_no_changes_needed",
            reviewerSummary: "Already satisfied; no diff invented.",
            routeCalled: "/v1/decisions/prompt-packet",
            selectedTarget: packet.selectedTarget,
            status: "satisfied",
            targetCandidates: packet.targetCandidates,
            targetMatch: true,
            taskId: taskIdFromPayload(proposalPayload),
            taskSpecAllowed: true,
            verifierSummary: "No diff to verify. Recommended check: git diff --check.",
            technicalDetail: "coder_no_changes_needed",
          });
          return;
        }
        const noDiffBlocker =
          reasonCode === "realistic_trial_model_call_failed"
            ? coderSummaryFromPayload(
                proposalPayload,
                "Realistic reversible trial could not prove a live model call.",
              )
            : noDiffBlockerFromPayload(proposalPayload);
        setPreviewState({
          approvalAvailable: false,
          approvedAt: null,
          appliedAt: null,
          applySummary: "",
          allowedFiles: packet.allowedFiles,
          blocker: "Task could not start. Copy diagnostics for details.",
          changedFiles: [],
          checks: packet.checks,
          currentPhase: manualTaskPhaseLabels.blocked,
          diff: "",
          error: null,
          events: [
            ...packetEvents,
            manualEvent("blocked", "blocked", `Preview route returned no diff (${reasonCode ?? "no reason code"}).`),
          ],
          forbiddenFiles: packet.forbiddenFiles,
          isApplying: false,
          isLoading: false,
          ...providerTruthPatch(proposalProviderTruth),
          previewStatus: "no diff",
          requirementSummary: coderSummaryFromPayload(
            proposalPayload,
            "No diff returned for requirement review.",
          ),
          reasonCode,
          reviewerSummary: "No reviewer evidence available.",
          routeCalled: "/v1/decisions/prompt-packet",
          selectedTarget: packet.selectedTarget,
          status: "blocked",
          targetCandidates: packet.targetCandidates,
          targetMatch: false,
          taskId: "",
          taskSpecAllowed: false,
          verifierSummary: "No verifier evidence available.",
          technicalDetail: noDiffBlocker,
        });
        return;
      }

      const checksEvents = [
        ...packetEvents,
        manualEvent("preview", "done", "Preview diff returned. Sending it through diff verification."),
        manualEvent("checks", "running", `Preparing checks: ${packet.checks.join(", ")}.`),
      ];
      setManualProgress(checksEvents, "checks");
      const diffPreviewStartedAt = performance.now();
      const diffResponse = await fetchWithTimeout("/v1/verification/diff-preview", {
        body: JSON.stringify({
          route_type: "source-proxy-default",
          task_spec: taskSpec,
          task_text: task.trim(),
          unified_diff: proposedDiff,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
      });
      setComposerTiming((current) => ({
        ...current,
        diffPreviewMs: elapsedMs(diffPreviewStartedAt),
      }));
      const diffPayload = await readJson(diffResponse);
      if (!diffResponse.ok) {
        throw new Error(messageFromPayload(diffPayload, diffResponse.status));
      }
      const changedFiles = changedFilesFromPayload(diffPayload);
      const blocked = statusFromPayload(diffPayload) === "blocked";
      const gate = approvalGateFromPreview(diffPayload, trimmedTarget, packet.allowedFiles);
      const changedOutsideAllowed =
        changedFiles.length > 0 &&
        packet.allowedFiles.length > 0 &&
        !changedFiles.every((file) => packet.allowedFiles.includes(file));
      const effectivelyBlocked = blocked || changedOutsideAllowed;
      const previewOnlyApplyBlocked = taskRequestsPreviewOnly(task);
      if (!effectivelyBlocked && previewOnlyApplyBlocked) {
        setPreviewState({
          approvalAvailable: false,
          approvedAt: null,
          appliedAt: null,
          applySummary: "NO-GO: Preview-only output cannot pass.",
          allowedFiles: packet.allowedFiles,
          blocker: "NO-GO: Live apply proof missing",
          changedFiles,
          checks: packet.checks,
          currentPhase: manualTaskPhaseLabels.blocked,
          diff: proposedDiff,
          error: "NO-GO: Live apply proof missing",
          events: [
            ...checksEvents,
            manualEvent("checks", "done", "Diff verification passed, but the prompt requested preview-only behavior."),
            manualEvent("blocked", "blocked", "Preview-only output cannot show PASS."),
          ],
          forbiddenFiles: packet.forbiddenFiles,
          isApplying: false,
          isLoading: false,
          ...providerTruthPatch(proposalProviderTruth),
          previewStatus: "preview-only blocked",
          requirementSummary: "Preview-only output cannot pass.",
          reasonCode: "preview_only_no_apply_requested",
          reviewerSummary: "No live apply proof because apply was not allowed.",
          routeCalled: "/v1/decisions/prompt-packet -> /v1/verification/diff-preview",
          selectedTarget: packet.selectedTarget,
          status: "blocked",
          targetCandidates: packet.targetCandidates,
          targetMatch: gate.targetMatch,
          taskId: taskIdFromPayload(diffPayload) || taskIdFromPayload(proposalPayload),
          taskSpecAllowed: gate.taskSpecAllowed,
          verifierSummary: gate.verifierSummary,
          technicalDetail: "preview_only_no_apply_requested",
        });
        return;
      }
      if (!effectivelyBlocked) {
        const previewReadyEvents = [
          ...checksEvents,
          manualEvent("checks", "done", "Diff verification passed for the safety gate."),
          manualEvent("review", "done", "Changed files are inside allowed_files."),
          manualEvent("done", "running", "Applying the verified diff through execute-approved."),
        ];
        const previewTaskId = taskIdFromPayload(diffPayload) || taskIdFromPayload(proposalPayload);
        setPreviewState({
          approvalAvailable: false,
          approvedAt: new Date().toISOString(),
          appliedAt: null,
          applySummary: "Applying verified diff through execute-approved.",
          allowedFiles: packet.allowedFiles,
          blocker: null,
          changedFiles,
          checks: packet.checks,
          currentPhase: "Editing files",
          diff: proposedDiff,
          error: null,
          events: previewReadyEvents,
          forbiddenFiles: packet.forbiddenFiles,
          isApplying: true,
          isLoading: false,
          ...providerTruthPatch(proposalProviderTruth),
          previewStatus: "verified; applying",
          requirementSummary: gate.requirementSummary,
          reasonCode: null,
          reviewerSummary: gate.reviewerSummary,
          routeCalled: "/v1/decisions/prompt-packet -> /v1/verification/diff-preview -> /v1/actions/execute-approved",
          selectedTarget: packet.selectedTarget,
          status: "approved",
          targetCandidates: packet.targetCandidates,
          targetMatch: gate.targetMatch,
          taskId: previewTaskId,
          taskSpecAllowed: gate.taskSpecAllowed,
          verifierSummary: gate.verifierSummary,
          technicalDetail: null,
        });
        let taskId = previewTaskId;
        if (!taskId) {
          const taskResponse = await fetch("/v1/tasks/long-running", {
            body: JSON.stringify({ description: task.trim() || "Coding cockpit live apply" }),
            headers: { "content-type": "application/json" },
            method: "POST",
          });
          const taskPayload = await readJson(taskResponse);
          if (!taskResponse.ok) {
            throw new Error(messageFromPayload(taskPayload, taskResponse.status));
          }
          taskId = taskIdFromPayload(taskPayload);
          if (!taskId) {
            throw new Error("Long-running task create did not return a task id.");
          }
        }
        const applyResponse = await fetch("/v1/actions/execute-approved", {
          body: JSON.stringify({
            action: `Modify ${packet.selectedTarget}`,
            approved: true,
            approved_diff: proposedDiff,
            allowed_files: packet.allowedFiles,
            target: packet.selectedTarget,
            task_id: taskId,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        });
        const applyPayload = await readJson(applyResponse);
        if (!applyResponse.ok) {
          throw new Error(messageFromPayload(applyPayload, applyResponse.status));
        }
        const appliedFiles = changedFilesFromApplyPayloadOrDiff(applyPayload, proposedDiff);
        const appliedAt = new Date().toISOString();
        const diskChangedFiles = appliedFiles.length > 0 ? appliedFiles : changedFiles;
        if (diskChangedFiles.length === 0) {
          throw new Error("FAIL: No disk change");
        }
        const receipt: AppliedRunReceipt = {
          allowedFiles: packet.allowedFiles,
          appliedAt,
          changedFiles: diskChangedFiles,
          diff: proposedDiff,
          hermesUsedForThisRun: proposalProviderTruth.hermesUsedForRunStatus === "yes",
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          model: proposalProviderTruth.modelLabel,
          prompt: task.trim(),
          provider: proposalProviderTruth.providerLabel,
          providerModelSource: proposalProviderTruth.source,
          providerModelStatus: proposalProviderTruth.status,
          revertedAt: null,
          reversalModel: null,
          reversalProvider: null,
          reversalProviderModelSource: null,
          reverseDiff: reverseUnifiedDiff(proposedDiff),
          target: packet.selectedTarget,
          taskId,
        };
        updateAppliedRunReceipts((receipts) => appendAppliedRunReceipt(receipts, receipt));
        setPreviewState({
          approvalAvailable: false,
          approvedAt: null,
          appliedAt,
          applySummary: messageFromPayload(applyPayload, applyResponse.status),
          allowedFiles: packet.allowedFiles,
          blocker: null,
          changedFiles: diskChangedFiles,
          checks: packet.checks,
          currentPhase: manualTaskPhaseLabels.done,
          diff: proposedDiff,
          error: null,
          events: [
            ...previewReadyEvents.slice(0, -1),
            manualEvent("done", "done", "Diff applied through execute-approved. Reverse diff receipt is available."),
          ],
          forbiddenFiles: packet.forbiddenFiles,
          isApplying: false,
          isLoading: false,
          ...providerTruthPatch(proposalProviderTruth),
          previewStatus: "live apply complete",
          requirementSummary: gate.requirementSummary,
          reasonCode: null,
          reviewerSummary: gate.reviewerSummary,
          routeCalled: "/v1/decisions/prompt-packet -> /v1/verification/diff-preview -> /v1/actions/execute-approved",
          selectedTarget: packet.selectedTarget,
          status: "applied",
          targetCandidates: packet.targetCandidates,
          targetMatch: gate.targetMatch,
          taskId,
          taskSpecAllowed: gate.taskSpecAllowed,
          verifierSummary: `Checks recorded: ${packet.checks.join(", ")}`,
          technicalDetail: null,
        });
        return;
      }
      setPreviewState({
        approvalAvailable: !effectivelyBlocked && gate.approvalAvailable && !previewOnlyApplyBlocked,
        approvedAt: null,
        appliedAt: null,
        applySummary: "",
        allowedFiles: packet.allowedFiles,
        blocker: changedOutsideAllowed
          ? "Apply blocked because changed_files are not fully contained in allowed_files."
          : blocked ? blockerFromPayload(diffPayload) : null,
        changedFiles,
        checks: packet.checks,
        currentPhase: effectivelyBlocked ? manualTaskPhaseLabels.blocked : manualTaskPhaseLabels.done,
        diff: proposedDiff,
        error: null,
        events: [
          ...checksEvents,
          manualEvent("checks", effectivelyBlocked ? "blocked" : "done", effectivelyBlocked ? "Diff verification blocked the preview." : "Diff verification passed for preview."),
          manualEvent("review", effectivelyBlocked ? "blocked" : "done", effectivelyBlocked ? "Review found a blocker." : "Review result is ready."),
          manualEvent(effectivelyBlocked ? "blocked" : "done", effectivelyBlocked ? "blocked" : "done", effectivelyBlocked ? "Manual task stopped with diagnostics." : "Preview result is ready."),
        ],
        forbiddenFiles: packet.forbiddenFiles,
        isApplying: false,
        isLoading: false,
        ...providerTruthPatch(proposalProviderTruth),
        previewStatus: effectivelyBlocked ? "blocked" : "preview ready",
        requirementSummary: previewOnlyApplyBlocked
          ? `${gate.requirementSummary} Apply is disabled by the preview-only prompt.`
          : gate.requirementSummary,
        reasonCode: changedOutsideAllowed
          ? "changed_files_outside_allowed_files"
          : blocked ? reasonCodeFromPreview(diffPayload)
            : previewOnlyApplyBlocked ? "preview_only_no_apply_requested"
              : null,
        reviewerSummary: gate.reviewerSummary,
        routeCalled: "/v1/decisions/prompt-packet -> /v1/verification/diff-preview",
        selectedTarget: packet.selectedTarget,
        status: effectivelyBlocked ? "blocked" : "ready",
        targetCandidates: packet.targetCandidates,
        targetMatch: gate.targetMatch,
        taskId: taskIdFromPayload(diffPayload) || taskIdFromPayload(proposalPayload),
        taskSpecAllowed: gate.taskSpecAllowed,
        verifierSummary: gate.verifierSummary,
        technicalDetail: changedOutsideAllowed
          ? "changed_files_outside_allowed_files"
          : blocked ? blockerFromPayload(diffPayload) : null,
      });
    } catch (error) {
      const technicalDetail = error instanceof Error ? error.message : "Preview failed.";
      setPreviewState({
        approvalAvailable: false,
        approvedAt: null,
        appliedAt: null,
        applySummary: "",
        allowedFiles: [],
        blocker: null,
        changedFiles: [],
        checks: splitLinesOrCommas(expectedChecks) || ["git diff --check"],
        currentPhase: manualTaskPhaseLabels.failed,
        diff: "",
        error: "Task could not start. Copy diagnostics for details.",
        events: [
          manualEvent("received", "done", "Prompt received from the manual composer."),
          manualEvent("failed", "failed", technicalDetail),
        ],
        forbiddenFiles: PROTECTED_FORBIDDEN_FILES,
        isApplying: false,
        isLoading: false,
        ...providerTruthPatch(selectedProviderTruth),
        previewStatus: "failed",
        requirementSummary: "Preview failed before requirement review.",
        reasonCode: reasonCodeFromErrorMessage(technicalDetail),
        reviewerSummary: "Preview failed before reviewer evidence.",
        routeCalled: "/v1/decisions/prompt-packet",
        selectedTarget: null,
        status: "error",
        targetCandidates: [],
        targetMatch: false,
        taskId: "",
        taskSpecAllowed: false,
        verifierSummary: "Preview failed before verifier evidence.",
        technicalDetail,
      });
    } finally {
      setComposerTiming((current) => ({
        ...current,
        totalMs: elapsedMs(runStartedAt),
      }));
    }
  }

  function handleRejectPreview() {
    setVerificationCopyStatus("");
    setPreviewState((current) => ({
      ...current,
      approvalAvailable: false,
      approvedAt: null,
      appliedAt: null,
      applySummary: "",
      blocker: "Rejected by human reviewer. No files changed.",
      status: "blocked",
    }));
  }

  function handleApprovePreview() {
    if (!previewState.approvalAvailable || previewState.status !== "ready") {
      return;
    }
    if (taskRequestsPreviewOnly(task)) {
      return;
    }
    setVerificationCopyStatus("");
    setPreviewState((current) => ({
      ...current,
      approvedAt: new Date().toISOString(),
      status: "approved",
    }));
  }

  async function handleApplyApprovedDiff() {
    if (!previewState.approvedAt || !previewState.diff || previewState.status !== "approved") {
      return;
    }
    if (taskRequestsPreviewOnly(task)) {
      setPreviewState((current) => ({
        ...current,
        applySummary: "Apply blocked because the prompt requested preview-only.",
        error: "Apply blocked because the prompt requested preview-only.",
        isApplying: false,
        reasonCode: "preview_only_no_apply_requested",
        technicalDetail: "preview_only_no_apply_requested",
      }));
      return;
    }
    if (applyScopePreflight.reasonCode !== null) {
      setPreviewState((current) => ({
        ...current,
        applySummary: applyScopePreflight.reason ?? "Apply blocked before execute-approved.",
        error: applyScopePreflight.reason ?? "Apply blocked before execute-approved.",
        isApplying: false,
        reasonCode: applyScopePreflight.reasonCode,
        technicalDetail: applyScopePreflight.reasonCode,
      }));
      return;
    }
    setPreviewState((current) => ({
      ...current,
      error: null,
      isApplying: true,
      reasonCode: null,
    }));
    try {
      let taskId = previewState.taskId;
      if (!taskId) {
        const taskResponse = await fetch("/v1/tasks/long-running", {
          body: JSON.stringify({ description: task.trim() || "Coding cockpit approved diff" }),
          headers: { "content-type": "application/json" },
          method: "POST",
        });
        const taskPayload = await readJson(taskResponse);
        if (!taskResponse.ok) {
          throw new Error(messageFromPayload(taskPayload, taskResponse.status));
        }
        taskId = taskIdFromPayload(taskPayload);
        if (!taskId) {
          throw new Error("Long-running task create did not return a task id.");
        }
      }
      const applyResponse = await fetch("/v1/actions/execute-approved", {
        body: JSON.stringify({
          action: `Modify ${previewState.selectedTarget ?? targetFile.trim()}`,
          approved: true,
          approved_diff: previewState.diff,
          allowed_files: applyScopePreflight.allowedFiles,
          target: previewState.selectedTarget ?? targetFile.trim(),
          task_id: taskId,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
      });
      const applyPayload = await readJson(applyResponse);
      if (!applyResponse.ok) {
        throw new Error(messageFromPayload(applyPayload, applyResponse.status));
      }
      const appliedFiles = changedFilesFromApplyPayloadOrDiff(applyPayload, previewState.diff);
      const appliedAt = new Date().toISOString();
      const changedFiles = appliedFiles.length > 0 ? appliedFiles : previewState.changedFiles;
      const receipt: AppliedRunReceipt = {
        allowedFiles: applyScopePreflight.allowedFiles,
        appliedAt,
        changedFiles,
        diff: previewState.diff,
        hermesUsedForThisRun: previewState.hermesUsedForThisRun ?? null,
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        model: previewState.model,
        prompt: task.trim(),
        provider: previewState.provider,
        providerModelSource: previewState.providerModelSource ?? "unknown",
        providerModelStatus: previewState.providerModelStatus ?? "unknown",
        revertedAt: null,
        reversalModel: null,
        reversalProvider: null,
        reversalProviderModelSource: null,
        reverseDiff: reverseUnifiedDiff(previewState.diff),
        target: previewState.selectedTarget ?? targetFile.trim(),
        taskId,
      };
      updateAppliedRunReceipts((receipts) => appendAppliedRunReceipt(receipts, receipt));
      setPreviewState((current) => ({
        ...current,
        appliedAt,
        applySummary: messageFromPayload(applyPayload, applyResponse.status),
        allowedFiles: applyScopePreflight.allowedFiles,
        changedFiles: changedFiles.length > 0 ? changedFiles : current.changedFiles,
        error: null,
        isApplying: false,
        reasonCode: null,
        status: "applied",
        taskId,
      }));
    } catch (error) {
      setPreviewState((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Approved apply failed.",
        isApplying: false,
      }));
    }
  }

  async function applyReverseReceipt(receipt: AppliedRunReceipt) {
    const reverseDiff = reverseDiffForReceipt(receipt);
    const changedFiles = changedFilesFromDiffPreview(reverseDiff);
    const allowedFiles = receipt.allowedFiles.map((path) => normalizeRepoPath(path)).filter(Boolean);
    const outsideAllowed = changedFiles.filter((path) => !allowedFiles.includes(path));
    if (allowedFiles.length === 0) {
      throw new Error("Reverse blocked because allowed_files are missing from the applied-run receipt.");
    }
    if (changedFiles.length === 0) {
      throw new Error("Reverse blocked because the stored diff has no changed files.");
    }
    if (outsideAllowed.length > 0) {
      throw new Error(
        `Reverse blocked because changed_files are not fully contained in allowed_files: ${outsideAllowed.join(", ")}`,
      );
    }
    const taskResponse = await fetch("/v1/tasks/long-running", {
      body: JSON.stringify({
        description: buildReverseTaskDescription(receipt, changedFiles, allowedFiles),
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const taskPayload = await readJson(taskResponse);
    if (!taskResponse.ok) {
      throw new Error(messageFromPayload(taskPayload, taskResponse.status));
    }
    const taskId = taskIdFromPayload(taskPayload);
    if (!taskId) {
      throw new Error("Reverse task create did not return a task id.");
    }
    const revertAction = revertActionForReceipt(receipt);
    const reverseResponse = await fetch("/v1/actions/execute-approved", {
      body: JSON.stringify({
        action: revertAction,
        approved: true,
        approved_diff: reverseDiff,
        allowed_files: allowedFiles,
        target: receipt.target,
        task_id: taskId,
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const reversePayload = await readJson(reverseResponse);
    if (!reverseResponse.ok) {
      throw new Error(messageFromPayload(reversePayload, reverseResponse.status));
    }
    return messageFromPayload(reversePayload, reverseResponse.status);
  }

  async function prepareDummyTrialFixtureForReversibleApply(
    target: string,
    onStep?: (step: string) => void,
  ): Promise<void> {
    const normalized = normalizeRepoPath(target);
    const resetDiffs = dummyTrialBaselineResetDiffs(normalized);
    if (resetDiffs.length === 0) {
      return;
    }
    const providerTruth = selectedProviderTruth;
    onStep?.("Resetting trial fixture");
    for (const [index, resetDiff] of resetDiffs.entries()) {
      const receipt = buildTrialFixtureResetReceiptFromDiff(normalized, resetDiff, {
        appliedAt: "suite-fixture-prep",
        hermesUsedForThisRun: providerTruth.hermesUsedForThisRun,
        idSuffix: `suite-cycle-reset-${index}`,
        model: providerTruth.modelLabel ?? "unknown",
        prompt: `Reset ${normalized} to trial baseline before the next reversible apply.`,
        provider: providerTruth.providerLabel,
        providerModelSource: providerTruth.source,
        providerModelStatus: providerTruth.status,
      });
      try {
        await applyReverseReceipt(receipt);
        return;
      } catch {
        // Try the next reset shape (legacy vs satisfied bounded apply).
      }
    }
  }

  async function handleRevertReceipt(receipt: AppliedRunReceipt) {
    if (isReverting) return;
    setIsReverting(true);
    setReversalStatus("Reverting approved diff through Source Proxy scope checks...");
    setDiagnosticCopyStatus("");
    try {
      const summary = await applyReverseReceipt(receipt);
      const revertedAt = new Date().toISOString();
      if (!receipt.id.startsWith("trial-reset:")) {
        updateAppliedRunReceipts((receipts) =>
          receipts.map((item) =>
            item.id === receipt.id
              ? {
                  ...item,
                  revertedAt,
                  reversalModel: selectedProviderTruth.modelLabel,
                  reversalProvider: selectedProviderTruth.providerLabel,
                  reversalProviderModelSource: "ui-selection",
                }
              : item,
          ),
        );
      }
      setPreviewState((current) => ({
        ...current,
        appliedAt: null,
        applySummary: receipt.id.startsWith("trial-reset:")
          ? `Trial fixture reset. ${summary}`
          : `Reverted approved diff. ${summary}`,
        blocker: null,
        currentPhase: receipt.id.startsWith("trial-reset:") ? "waiting for prompt" : current.currentPhase,
        error: null,
        reasonCode: null,
        status: receipt.id.startsWith("trial-reset:") ? "idle" : "ready",
      }));
      setReversalStatus(
        receipt.id.startsWith("trial-reset:")
          ? "Reset this trial fixture. Run the prompt again to generate a fresh preview diff."
          : "Reverted this run. Workspace should be back to the pre-run file content for that diff.",
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "Reverse apply failed.";
      setReversalStatus(message);
      setPreviewState((current) => ({
        ...current,
        error: message,
        reasonCode: "reversal_failed",
        technicalDetail: message,
      }));
    } finally {
      setIsReverting(false);
    }
  }

  async function handleRevertAllTrialRuns(options: { clearSuiteAfter?: boolean } = {}) {
    if (!canRevertTrialRuns && !options.clearSuiteAfter) return;
    if (suitePendingRevertCount > 0) {
      await handleReverseRemainingTrialEdits();
      if (availableTrialResetReceipts.length === 0 && !options.clearSuiteAfter) {
        return;
      }
    }
    setIsReverting(true);
    const trialReceipts = [
      ...orphanUnrevertedTrialReceipts,
      ...availableTrialResetReceipts.filter(
        (resetReceipt) =>
          !orphanUnrevertedTrialReceipts.some((receipt) => receipt.target === resetReceipt.target),
      ),
    ];
    setReversalStatus(`Reverting ${trialReceipts.length} trial item(s) in reverse order...`);
    setDiagnosticCopyStatus("");
    const revertedIds: string[] = [];
    const failures: string[] = [];
    try {
      for (const receipt of [...trialReceipts].reverse()) {
        try {
          await applyReverseReceipt(receipt);
          revertedIds.push(receipt.id);
        } catch (error) {
          const message = error instanceof Error ? error.message : "Reverse apply failed.";
          if (reversalLooksAlreadyApplied(message)) {
            revertedIds.push(receipt.id);
            continue;
          }
          failures.push(`${receipt.target}: ${message}`);
        }
      }
      const revertedAt = new Date().toISOString();
      updateAppliedRunReceipts((receipts) =>
        receipts.map((receipt) =>
          revertedIds.includes(receipt.id)
            ? {
                ...receipt,
                revertedAt,
                reversalModel: selectedProviderTruth.modelLabel,
                reversalProvider: selectedProviderTruth.providerLabel,
                reversalProviderModelSource: "ui-selection",
              }
            : receipt,
          ),
      );
      const currentRunReverted = Boolean(currentRunReceipt && revertedIds.includes(currentRunReceipt.id));
      setPreviewState((current) => ({
        ...current,
        appliedAt: currentRunReverted ? null : current.appliedAt,
        applySummary: currentRunReverted
          ? "Reverted this run through Source Proxy scope checks."
          : current.applySummary,
        blocker: null,
        currentPhase: revertedIds.some((id) => id.startsWith("trial-reset:")) ? "waiting for prompt" : current.currentPhase,
        error: null,
        reasonCode: null,
        status: revertedIds.some((id) => id.startsWith("trial-reset:"))
          ? "idle"
          : currentRunReverted
            ? "ready"
          : current.status,
      }));
      if (options.clearSuiteAfter && failures.length === 0) {
        clearReversibleSuitePanel();
        setReversibleSuiteCopyStatus(`Cleaned up ${revertedIds.length} trial item(s) and cleared suite results.`);
      }
      setReversalStatus(
        failures.length > 0
          ? `Cleaned up ${revertedIds.length} trial item(s). ${failures.length} item(s) still need attention: ${failures[0]}`
          : `Reverted ${revertedIds.length} trial item(s). Ready for a clean prompt retest.`,
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "Reverse apply failed.";
      setReversalStatus(`Stopped after reverting ${revertedIds.length} run(s). ${message}`);
      const currentRunReverted = Boolean(currentRunReceipt && revertedIds.includes(currentRunReceipt.id));
      setPreviewState((current) => ({
        ...current,
        appliedAt: currentRunReverted ? null : current.appliedAt,
        applySummary: currentRunReverted
          ? "Reverted this run through Source Proxy scope checks; another trial reversal failed."
          : current.applySummary,
        error: currentRunReverted || current.status === "applied" ? message : current.error,
        reasonCode: currentRunReverted || current.status === "applied" ? "reversal_failed" : current.reasonCode,
        status: currentRunReverted ? "ready" : current.status,
        technicalDetail: currentRunReverted || current.status === "applied" ? message : current.technicalDetail,
      }));
      if (revertedIds.length > 0) {
        const revertedAt = new Date().toISOString();
        updateAppliedRunReceipts((receipts) =>
          receipts.map((receipt) =>
            revertedIds.includes(receipt.id)
              ? {
                  ...receipt,
                  revertedAt,
                  reversalModel: selectedProviderTruth.modelLabel,
                  reversalProvider: selectedProviderTruth.providerLabel,
                  reversalProviderModelSource: "ui-selection",
                }
              : receipt,
          ),
        );
      }
    } finally {
      setIsReverting(false);
    }
  }

  function handleCancelRun() {
    if (!previewState.isLoading && !previewState.isApplying && !isReverting) return;
    setPreviewState((current) => ({
      ...current,
      applySummary: "Cancelled in the browser before another UI action was taken.",
      blocker: "Cancelled",
      currentPhase: manualTaskPhaseLabels.blocked,
      error: null,
      isApplying: false,
      isLoading: false,
      reasonCode: "cancelled",
      status: "blocked",
      technicalDetail: "cancelled",
    }));
  }

  const liveRunnerState =
    reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"
      ? reversibleSuiteState.currentStep
      : reversibleSuiteState.status === "done"
        ? "Done"
        : reversibleSuiteState.status === "failed"
          ? "Needs fix"
          : previewState.isLoading
            ? previewState.currentPhase || "Reading"
            : previewState.isApplying || isReverting
              ? "Editing"
              : previewState.status === "applied" || previewState.status === "satisfied"
                ? "Done"
                : previewState.status === "blocked" || previewState.status === "error"
                  ? "Failed"
                  : "Idle";
  const generatedDiffPresent = Boolean(previewState.diff.trim());
  const modelCalledForGeneration = currentPreviewProviderTruth.modelCalledForGeneration ?? "none";
  const liveProofComplete =
    previewState.status === "applied" &&
    currentPreviewProviderTruth.providerCallMade &&
    modelCalledForGeneration !== "none" &&
    currentChangedFilesDiagnostics.previewChangedFiles.length > 0 &&
    currentChangedFilesDiagnostics.appliedChangedFiles.length > 0 &&
    currentChangedFilesDiagnostics.diskChangedFiles.length > 0 &&
    previewState.changedFiles.every((file) => previewState.allowedFiles.includes(file)) &&
    previewState.checks.length > 0 &&
    Boolean(currentAppliedRunReceipt && !currentAppliedRunReceipt.revertedAt) &&
    !previewState.changedFiles.some(isProtectedTarget);
  const liveResultLabel =
    reversalStatus.toLowerCase().startsWith("reverted")
      ? "REVERTED"
      : previewState.status === "satisfied" || previewState.reasonCode === "coder_no_changes_needed"
        ? "ALREADY SATISFIED"
        : previewState.reasonCode === "protected_path_request" || previewState.status === "blocked"
          ? "BLOCKED"
          : previewState.status === "error" && previewState.reasonCode === "no_model_call"
            ? "FAIL"
            : liveRunnerState === "Idle" || previewState.isLoading || previewState.isApplying || reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"
              ? liveRunnerState
              : liveProofComplete
                ? "PASS"
                : previewState.status === "error"
                  ? "FAIL"
                  : codingVisibleResult.primary_label;
  const liveResultSentence =
    liveResultLabel === "PASS"
      ? "SpiritOS called the model, applied a bounded disk change, recorded checks, and stored a reverse diff."
      : liveResultLabel === "ALREADY SATISFIED"
        ? "The target file already matches this task. Copy the path below and confirm on disk, or reset the trial fixture to run a live edit again."
        : liveResultLabel === "BLOCKED"
          ? "Protected paths were blocked before any edit."
          : liveResultLabel === "REVERTED"
            ? "This run was reverted through execute-approved using the stored reverse diff."
            : liveRunnerState === "Idle"
              ? "Describe a change and start a live coding run."
              : previewState.status === "satisfied"
                ? (previewState.blocker ?? "No diff was required because the target already satisfies the task.")
                : previewState.error ?? previewState.blocker ?? previewState.applySummary ?? codingVisibleResult.plain_summary;
  const simpleProgressItems = [
    "Reading request",
    "Finding files",
    "Calling model",
    "Editing files",
    "Checking",
    "Undoing trial edit",
    "Ready to review",
  ].map((label) => {
    const suiteStepOrder = [
      "Reading request",
      "Finding files",
      "Calling model",
      "Editing files",
      "Checking",
      "Undoing trial edit",
      "Ready to review",
    ];
    if (reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping") {
      const currentIndex = suiteStepOrder.indexOf(reversibleSuiteState.currentStep);
      const itemIndex = suiteStepOrder.indexOf(label);
      return {
        label,
        status: itemIndex < currentIndex ? "done" : itemIndex === currentIndex ? "running" : "waiting",
      };
    }
    if (reversibleSuiteState.status === "done" || reversibleSuiteState.status === "failed") {
      return { label, status: reversibleSuiteState.status === "done" ? "done" : "finished" };
    }
    const event = previewState.events.find((item) => item.label === label);
    const status =
      event?.status ??
      (previewState.status === "idle" && !previewState.isLoading && !previewState.isApplying
        ? "waiting"
        : previewState.currentPhase === label
          ? "running"
          : previewState.events.some((item) => item.label === label)
            ? "done"
            : "waiting");
    return { label, status };
  });
  const activeSessionItems = [
    {
      label: task.trim() ? "Current request" : "New coding chat",
      meta: currentTaskState,
      active: true,
    },
    {
      label: "Active task",
      meta: currentTaskTitle,
      active: Boolean(task.trim() || previewState.status !== "idle"),
    },
    {
      label: currentAppliedRunReceipt && !currentAppliedRunReceipt.revertedAt
        ? "Revert ready"
        : previewState.status === "applied"
          ? "Live run complete"
          : "Live run status",
      meta: currentAppliedRunReceipt && !currentAppliedRunReceipt.revertedAt
        ? "Reverse diff stored"
        : liveRunnerState,
      active: previewState.status !== "idle" || Boolean(currentAppliedRunReceipt),
    },
  ].filter((item) => item.active);
  const reversibleSuiteCanResume =
    reversibleSuiteState.status === "failed" &&
    reversibleSuiteState.interruptionSource === "browser_refresh_or_dev_reload" &&
    reversibleSuiteState.completed < reversibleSuiteState.count;
  const phoneBackgroundState =
    reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"
      ? "Running in this browser"
      : reversibleSuiteCanResume
        ? "Paused, ready to resume"
        : reversibleSuiteState.status === "done"
          ? "Finished, saved locally"
          : reversibleSuiteState.status === "failed"
            ? "Stopped, saved locally"
            : reversibleSuiteState.results.length > 0
              ? "Last suite saved locally"
              : "Ready";
  const phoneBackgroundDetail =
    reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"
      ? "Keep this tab open while the suite runs. If the browser reloads or the Windows session pauses, completed prompt results stay in this browser and the resume button appears after reload."
      : reversibleSuiteCanResume
        ? `Resume from prompt ${reversibleSuiteState.completed + 1} of ${reversibleSuiteState.count}; completed rows were preserved.`
        : reversibleSuiteState.results.length > 0
          ? "Completed suite details are preserved across refresh until cleanup clears them."
          : "Start a reversible suite from the left rail, then use this panel as the quick phone check.";
  const phoneNetworkState =
    hasBrowserMounted && typeof navigator !== "undefined" && "onLine" in navigator
      ? navigator.onLine
        ? "Browser online"
        : "Browser offline"
      : sourceProxyReachable
        ? "Proxy reachable"
        : "Proxy not confirmed";
  const phoneResumeAction = reversibleSuiteCanResume ? (
    <button
      className={`mt-3 inline-flex min-h-10 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
      onClick={() => void handleRunReversibleSuite(reversibleSuiteState)}
      type="button"
    >
      Resume interrupted suite ({reversibleSuiteState.completed}/{reversibleSuiteState.count})
    </button>
  ) : null;
  function handleNewCodingChat() {
    setTask("");
    setDraftReady(false);
    setDiagnosticCopyStatus("");
    setVerificationCopyStatus("");
    setReversalStatus("");
    if (!currentAppliedRunReceipt || currentAppliedRunReceipt.revertedAt) {
      setPreviewState(idlePreviewState());
    }
  }

  return (
    <div className="dashboard-demo-v4-route-shell dashboard-demo-v4-root">
      <main className="dashboard-demo-v4-route-main min-h-dvh overflow-x-hidden text-[var(--ddv4-fg)]">
        <div className="mx-auto grid min-h-dvh w-full max-w-[min(1500px,100%)] gap-4 px-3 py-4 sm:px-5 lg:px-6 lg:py-6 min-[920px]:grid-cols-[230px_minmax(0,1fr)] min-[1200px]:grid-cols-[248px_minmax(0,1fr)_320px] min-[1440px]:grid-cols-[260px_minmax(0,1fr)_340px]">
          <h1 className="sr-only">Coding</h1>

          <aside
            aria-label="Coding chats"
            className={`${commandPanelClass} space-y-4 p-4 min-[920px]:sticky min-[920px]:top-4 min-[920px]:max-h-[calc(100dvh-2rem)] min-[920px]:overflow-auto`}
          >
            <div>
              <p className={commandLabelClass}>Workspace</p>
              <h2 className={`mt-2 text-lg font-semibold ${commandTextClass}`}>Coding sessions</h2>
              <p className={`mt-1 text-sm ${commandMutedClass}`}>SpiritOS</p>
            </div>
            <button
              className={`inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-md bg-emerald-300 px-3 text-sm font-semibold text-slate-950 shadow-sm transition-colors hover:bg-emerald-200 ${commandFocusClass}`}
              onClick={handleNewCodingChat}
              type="button"
            >
              <Plus aria-hidden="true" size={16} />
              New chat
            </button>
            <nav aria-label="Coding session list" className="space-y-2">
              {activeSessionItems.map((item) => (
                <button
                  aria-current={item.active ? "page" : undefined}
                  className={`${commandInsetClass} min-h-16 w-full p-3 text-left transition-colors hover:bg-[var(--ddv4-surface-fill)]`}
                  key={item.label}
                  type="button"
                >
                  <span className={`block text-sm font-semibold ${commandTextClass}`}>{item.label}</span>
                  <span className={`mt-1 block truncate text-xs ${commandMutedClass}`}>{item.meta}</span>
                </button>
              ))}
            </nav>
            <section className={`${commandInsetClass} p-3`} aria-label="Active task">
              <p className={commandLabelClass}>Active task</p>
              <p className={`mt-2 line-clamp-4 text-sm leading-5 ${commandTextClass}`}>{currentTaskTitle}</p>
              <p className={`mt-2 text-xs ${commandMutedClass}`}>{currentTaskTarget}</p>
            </section>
            <section className={`${commandInsetClass} p-3`} aria-label="Reversible trial runner">
              <p className={commandLabelClass}>Trial Runner</p>
              <h3 className={`mt-2 text-base font-semibold ${commandTextClass}`}>Trial runner</h3>
              <p className={`mt-1 text-xs leading-5 ${commandMutedClass}`}>
                Runs real test prompts, applies reversible edits, and leaves them on disk until you reverse manually.
              </p>
              {reversibleSuiteState.results.length > 0 ? (
                <p className={`mt-1 text-xs leading-5 ${commandMutedClass}`}>
                  Last suite stays in this browser after refresh until you clear it or run again.
                </p>
              ) : null}
              <div className="mt-3 grid gap-2">
                <label className="grid gap-1">
                  <span className={commandLabelClass}>Category</span>
                  <select
                    aria-label="Trial category"
                    className={`min-h-10 rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-3 text-sm font-semibold ${commandTextClass} ${commandControlClass}`}
                    disabled={reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"}
                    onChange={(event) => {
                      const category = event.target.value as ReversibleTrialCategory;
                      setReversibleTrialCategory(category);
                      setTrialMode(modeForTrialCategory(category));
                    }}
                    value={reversibleTrialCategory}
                  >
                    {reversibleTrialCategories.map((category) => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1">
                  <span className={commandLabelClass}>Count</span>
                  <select
                    aria-label="Trial count"
                    className={`min-h-10 rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-3 text-sm font-semibold ${commandTextClass} ${commandControlClass}`}
                    disabled={reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"}
                    onChange={(event) => setReversibleTrialCount(Number(event.target.value) as ReversibleTrialCount)}
                    value={reversibleTrialCount}
                  >
                    {reversibleTrialCounts.map((count) => (
                      <option key={count} value={count}>{count}</option>
                    ))}
                  </select>
                  {reversibleSuiteCountMismatch ? (
                    <span className={`text-xs leading-5 ${commandMutedClass}`}>
                      Results are from a ×{reversibleSuiteState.count} run. Count only changes the next run — use cleanup to reset the panel.
                    </span>
                  ) : null}
                </label>
              </div>
              <button
                className={`mt-3 inline-flex min-h-10 w-full items-center justify-center rounded-md bg-emerald-300 px-3 text-sm font-semibold text-slate-950 transition-colors hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                disabled={reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"}
                onClick={() => void handleRunReversibleSuite()}
                type="button"
              >
                Run reversible trial suite
              </button>
              {reversibleSuiteState.status === "failed" &&
              reversibleSuiteState.interruptionSource === "browser_refresh_or_dev_reload" &&
              reversibleSuiteState.completed < reversibleSuiteState.count ? (
                <button
                  className={`mt-2 inline-flex min-h-10 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                  onClick={() => void handleRunReversibleSuite(reversibleSuiteState)}
                  type="button"
                >
                  Resume interrupted suite ({reversibleSuiteState.completed}/{reversibleSuiteState.count})
                </button>
              ) : null}
              {reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping" ? (
                <button
                  className={`mt-2 inline-flex min-h-10 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                  onClick={handleStopReversibleSuiteAfterCurrent}
                  type="button"
                >
                  Stop after current prompt
                </button>
              ) : null}
              <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
                {[
                  ["Done", `${reversibleSuiteState.completed}/${reversibleSuiteState.count}`],
                  ["Edits applied", String(reversibleSuiteState.pass)],
                  ["Already satisfied", String(reversibleSuiteState.alreadySatisfied)],
                  ["Safety blocks", String(reversibleSuiteState.safetyBlock)],
                  ["Timeouts", String(reversibleSuiteState.timeout)],
                  ["Needs fix", String(reversibleSuiteState.fail)],
                  ["Reverted", String(reversibleSuiteState.reverted)],
                ].map(([label, value]) => (
                  <div className="rounded-md border border-[var(--ddv4-surface-border-soft)] p-2" key={label}>
                    <dt className={commandLabelClass}>{label}</dt>
                    <dd className={`mt-1 break-words ${commandTextClass}`}>{value}</dd>
                  </div>
                ))}
              </dl>
              {reversibleSuiteState.currentPrompt ? (
                <div className="mt-3 rounded-md border border-[var(--ddv4-surface-border-soft)] p-2 text-xs">
                  <p className={`font-semibold ${commandTextClass}`}>{reversibleSuiteState.currentPrompt}</p>
                  <p className={`mt-1 ${commandMutedClass}`}>{reversibleSuiteState.currentStep}</p>
                  <p className={`mt-2 text-xs font-mono ${commandMutedClass}`} aria-live="polite">
                    Timer — suite:{" "}
                    {formatElapsedMs(
                      reversibleSuiteState.suiteStartedAt,
                      reversibleSuiteTimingEndAt(reversibleSuiteState),
                    )}
                    {reversibleSuiteState.currentPromptElapsedMs != null
                      ? ` · prompt: ${(reversibleSuiteState.currentPromptElapsedMs / 1000).toFixed(1)}s`
                      : isReversibleSuiteTimingFrozen(reversibleSuiteState)
                        ? ""
                        : " · prompt: running…"}
                    {!isReversibleSuiteTimingFrozen(reversibleSuiteState) &&
                    reversibleSuiteState.currentStepStartedAt != null
                      ? ` · step (${reversibleSuiteState.currentStep}): ${formatElapsedMs(reversibleSuiteState.currentStepStartedAt)}`
                      : isReversibleSuiteTimingFrozen(reversibleSuiteState)
                        ? ` · step: ${reversibleSuiteState.currentStep}`
                        : ""}
                  </p>
                  <p className={`mt-1 break-words ${commandMutedClass}`}>
                    Open/check this file: {reversibleSuiteState.results.at(-1)?.prompt.verifyPathHints[0] ?? selectReversibleTrialPrompts(reversibleTrialCount, reversibleTrialCategory)[reversibleSuiteState.completed]?.verifyPathHints[0] ?? "shown after run starts"}
                  </p>
                </div>
              ) : null}
              {reversibleSuiteState.results.length > 0 ? (
                <div className="mt-3 space-y-2" aria-label="Trial run results">
                  {reversibleSuiteState.results.slice(-6).map((result, index) => (
                    <article className="rounded-md border border-[var(--ddv4-surface-border-soft)] p-2 text-xs" key={`${result.prompt.id}-${result.run_id || index}`}>
                      <div className="flex items-start justify-between gap-2">
                        <p className={`min-w-0 font-semibold ${commandTextClass}`}>{result.prompt.quickTitle}</p>
                        <span className={`shrink-0 rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] ${reversibleResultTagClass(result.visible_result_label)}`}>
                          {result.visible_result_label}
                        </span>
                      </div>
                      <p className={`mt-1 ${commandMutedClass}`}>{result.reverse_status_text}</p>
                      {result.failure_reason ? (
                        <p className="mt-1 text-rose-100">{result.failure_reason}</p>
                      ) : null}
                    </article>
                  ))}
                </div>
              ) : null}
              <button
                className={`mt-3 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                onClick={() => void copyReversibleSuitePrompts()}
                type="button"
              >
                <Copy aria-hidden="true" size={16} />
                Copy prompts
              </button>
              <button
                className={`mt-3 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                disabled={reversibleSuiteState.results.length === 0}
                onClick={() => void copyReversibleSuiteDiagnostics()}
                type="button"
              >
                <Copy aria-hidden="true" size={16} />
                Copy trial diagnostics
              </button>
              {reversibleSuiteFinished && reversibleSuiteState.results.length > 0
                ? reversibleSuiteReversalPanel
                : reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"
                  ? (
                      <p className={`mt-3 text-xs ${commandMutedClass}`}>
                        Reverse trial edits unlocks when the suite reaches Done (or after refresh marks an interrupted run as failed).
                      </p>
                    )
                  : null}
              {reversiblePromptsCopyStatus || reversibleSuiteCopyStatus ? (
                <p className={`mt-2 text-xs ${commandMutedClass}`}>{reversiblePromptsCopyStatus || reversibleSuiteCopyStatus}</p>
              ) : null}
            </section>
          </aside>

          <section className="flex min-w-0 flex-col gap-5">
            <section className={`${commandPanelClass} p-4 sm:p-5`} aria-labelledby="phone-trial-heading">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <p className={commandLabelClass}>Phone trial</p>
                  <h2 id="phone-trial-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                    Background trial
                  </h2>
                  <p className={`mt-2 text-sm leading-6 ${commandMutedClass}`}>{phoneBackgroundDetail}</p>
                </div>
                <span className="inline-flex min-h-9 shrink-0 items-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-xs font-semibold text-[var(--ddv4-fg)]">
                  {phoneBackgroundState}
                </span>
              </div>
              <dl className="mt-4 grid gap-2 text-xs sm:grid-cols-3">
                {[
                  ["Progress", `${reversibleSuiteState.completed}/${reversibleSuiteState.count}`],
                  ["Connection", phoneNetworkState],
                  ["Saved", reversibleSuiteState.results.length > 0 ? "Yes" : "Waiting"],
                ].map(([label, value]) => (
                  <div className={`${commandInsetClass} min-w-0 p-3`} key={label}>
                    <dt className={commandLabelClass}>{label}</dt>
                    <dd className={`mt-1 truncate ${commandTextClass}`} title={value}>{value}</dd>
                  </div>
                ))}
              </dl>
              {phoneResumeAction}
            </section>

            <section className={`${commandPanelClass} p-4 sm:p-5`} aria-labelledby="task-composer-heading">
              <div className="mb-4">
                <p className={commandLabelClass}>Prompt composer</p>
                <h2 id="task-composer-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                  Task Composer
                </h2>
              </div>
              <label className="block">
                <span className="sr-only">Coding prompt</span>
                <textarea
                  className={`min-h-40 w-full resize-y rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-4 py-4 text-base leading-7 text-[var(--ddv4-fg)] placeholder:text-[var(--ddv4-fg-faint)] ${commandControlClass}`}
                  onChange={(event) => {
                    handleTaskChange(event.target.value);
                  }}
                  placeholder="Describe what you want SpiritOS to change."
                  value={task}
                />
              </label>
              <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                <button
                  className={`inline-flex min-h-12 flex-1 items-center justify-center gap-2 rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 shadow-sm transition-colors hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                  disabled={!canStartTask || previewState.isLoading || previewState.isApplying || isReverting}
                  onClick={handleDraftPreview}
                  type="button"
                >
                  <ShieldCheck aria-hidden="true" size={18} />
                  {previewState.isLoading || previewState.isApplying ? "Working..." : "Start coding"}
                </button>
                {previewState.isLoading || previewState.isApplying || isReverting ? (
                  <button
                    className={`inline-flex min-h-12 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-4 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                    onClick={handleCancelRun}
                    type="button"
                  >
                    Cancel
                  </button>
                ) : null}
                <button
                  className={`inline-flex min-h-12 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-4 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                  disabled={!currentReversalReceipt || Boolean(currentReversalReceipt.revertedAt) || isReverting}
                  onClick={() => {
                    if (currentReversalReceipt && !currentReversalReceipt.revertedAt) {
                      void handleRevertReceipt(currentReversalReceipt);
                    }
                  }}
                  title={
                    currentReversalReceipt && !currentReversalReceipt.revertedAt
                      ? currentTrialFixtureResetReceipt && !currentAppliedRunReceipt
                        ? "Reset the trial fixture so you can run a live edit again."
                        : "Undo the last manual change."
                      : "Available after a manual change is applied or when a trial fixture reset is offered."
                  }
                  type="button"
                >
                  {isReverting
                    ? "Undoing..."
                    : currentTrialFixtureResetReceipt && !currentAppliedRunReceipt
                      ? "Reset trial fixture"
                      : "Undo last change"}
                </button>
              </div>
              {composerTiming.runStartedAt != null &&
              (previewState.isLoading || previewState.isApplying || composerTiming.totalMs != null) ? (
                <p className={`mt-2 text-xs font-mono ${commandMutedClass}`} aria-live="polite">
                  Timer — total: {formatElapsedMs(composerTiming.runStartedAt)}
                  {composerTiming.promptPacketMs != null
                    ? ` · prompt-packet: ${(composerTiming.promptPacketMs / 1000).toFixed(1)}s`
                    : previewState.isLoading
                      ? " · prompt-packet: running…"
                      : ""}
                  {composerTiming.diffPreviewMs != null
                    ? ` · diff-preview: ${(composerTiming.diffPreviewMs / 1000).toFixed(1)}s`
                    : ""}
                  {composerTiming.totalMs != null ? ` · finished: ${(composerTiming.totalMs / 1000).toFixed(1)}s` : ""}
                </p>
              ) : null}
              {!currentAppliedRunReceipt || currentAppliedRunReceipt.revertedAt ? (
                <p className={`mt-2 text-xs ${commandMutedClass}`}>
                  Undo is available after Start coding applies a reversible change.
                </p>
              ) : null}
            </section>

            <section className={`${commandPanelClass} p-4 sm:p-5`} aria-labelledby="progress-heading">
              <p className={commandLabelClass}>Progress</p>
              <h2 id="progress-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                Run progress
              </h2>
              <ol className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {simpleProgressItems.map((item) => (
                  <li className={`${commandInsetClass} min-h-16 p-3`} key={item.label}>
                    <div className={`text-sm font-semibold ${commandTextClass}`}>{item.label}</div>
                    <div className={`mt-1 text-xs uppercase tracking-[0.12em] ${commandMutedClass}`}>
                      {item.status}
                    </div>
                  </li>
                ))}
              </ol>
            </section>
          </section>

          <aside
            aria-label="Review pane"
            className={`${commandPanelClass} space-y-4 p-4 min-[920px]:col-span-2 min-[1200px]:col-span-1 min-[1200px]:sticky min-[1200px]:top-4 min-[1200px]:max-h-[calc(100dvh-2rem)] min-[1200px]:overflow-auto`}
          >
            <section role="status" aria-live="polite">
              <p className={commandLabelClass}>Status</p>
              <h2 className={`mt-2 text-lg font-semibold ${commandTextClass}`}>Coding runner</h2>
              <p className={`mt-1 text-sm ${commandMutedClass}`}>
                {reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"
                  ? reversibleSuiteState.currentPrompt || "Trial suite is running."
                  : previewState.changedFiles.length > 0
                  ? "Files changed on disk. Review or undo this run before starting another."
                  : "No live-run file changes are currently recorded."}
              </p>
              <dl className="mt-4 grid gap-3 text-sm">
                <div className={`${commandInsetClass} p-3`}>
                  <dt className={commandLabelClass}>Current task</dt>
                  <dd className={`mt-1 break-words ${commandTextClass}`}>
                    {reversibleSuiteState.status !== "idle" ? reversibleSuiteState.currentPrompt || "Trial runner" : currentTaskTitle}
                  </dd>
                </div>
                <div className={`${commandInsetClass} p-3`}>
                  <dt className={commandLabelClass}>Model</dt>
                  <dd className={`mt-1 break-words ${commandTextClass}`}>
                    {reversibleSuiteState.status !== "idle" ? reversibleSuiteState.model : currentPreviewProviderTruth.modelLabel}
                  </dd>
                </div>
                <div className={`${commandInsetClass} p-3`}>
                  <dt className={commandLabelClass}>State</dt>
                  <dd className={`mt-1 ${commandTextClass}`}>{liveRunnerState}</dd>
                </div>
              </dl>
            </section>

            <section aria-labelledby="review-pane-heading">
              <p className={commandLabelClass}>Review pane</p>
              <h2 id="review-pane-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                Review pane
              </h2>
              <div className="mt-4">
                <VisibleResultBadgeRow result={codingVisibleResult} />
              </div>
              <p className={`mt-2 text-sm leading-6 ${commandMutedClass}`}>{liveResultSentence}</p>
              <button
                className={`mt-4 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                disabled={!showCopyDiagnostics && !reversalStatus}
                onClick={() => void copyDiagnostics()}
                type="button"
              >
                <Copy aria-hidden="true" size={16} />
                Copy current task diagnostics
              </button>
              <button
                className={`mt-3 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                disabled={reversibleSuiteState.results.length === 0}
                onClick={() => void copyReversibleSuiteDiagnostics()}
                type="button"
              >
                <Copy aria-hidden="true" size={16} />
                Copy trial diagnostics
              </button>
              <dl className="mt-4 grid gap-3 text-sm">
                <div className={`${commandInsetClass} p-3`}>
                  <dt className={commandLabelClass}>Changed files</dt>
                  <dd className={`mt-1 break-words ${commandTextClass}`}>
                    {reversibleSuiteState.results.length > 0
                      ? formatList(reversibleSuiteState.results.at(-1)?.disk_changed_files ?? [], "None")
                      : formatList(currentChangedFilesDiagnostics.diskChangedFiles, "None")}
                  </dd>
                </div>
                <div className={`${commandInsetClass} p-3`}>
                  <dt className={commandLabelClass}>Checks</dt>
                  <dd className={`mt-1 break-words ${commandTextClass}`}>
                    {reversibleSuiteState.results.length > 0
                      ? formatList(reversibleSuiteState.results.at(-1)?.checks_run ?? [], "None recorded")
                      : formatList(previewState.checks, "None recorded")}
                  </dd>
                </div>
              </dl>
              {verificationTargets.length > 0 &&
              (previewState.status === "satisfied" ||
                previewState.status === "ready" ||
                previewState.status === "applied") ? (
                <div className={`${commandInsetClass} mt-4 p-3`}>
                  <p className={commandLabelClass}>Verify on disk</p>
                  <p className={`mt-1 text-xs ${commandMutedClass}`}>
                    Open this file in your editor and confirm the warning tone (or reset the fixture to re-run live).
                  </p>
                  <ul className="mt-3 space-y-2">
                    {verificationTargets.map((target) => (
                      <li className="rounded-md border border-[var(--ddv4-surface-border-soft)] p-3" key={target.path}>
                        <p className={`break-all font-mono text-xs ${commandTextClass}`}>{target.path}</p>
                        <button
                          className={`mt-2 inline-flex min-h-9 items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-xs font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                          disabled={!target.safe}
                          onClick={() => void copyVerificationPath(target.path)}
                          type="button"
                        >
                          <Copy aria-hidden="true" size={14} />
                          Copy path to verify
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {currentAppliedRunReceipt && !currentAppliedRunReceipt.revertedAt ? (
                <button
                  className={`mt-4 inline-flex min-h-11 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                  disabled={isReverting}
                  onClick={() => void handleRevertReceipt(currentAppliedRunReceipt)}
                  type="button"
                >
                  {isReverting ? "Undoing..." : "Undo last change"}
                </button>
              ) : null}
              {reversibleSuiteFinished && (reversibleSuiteState.results.length > 0 || canRevertTrialRuns)
                ? <div className="mt-4">{reversibleSuiteReversalPanel}</div>
                : null}
              {diagnosticCopyStatus ? (
                <p className={`mt-3 text-sm ${commandMutedClass}`}>{diagnosticCopyStatus}</p>
              ) : null}
              {reversalStatus ? (
                <p className={`mt-3 text-sm ${commandMutedClass}`}>{reversalStatus}</p>
              ) : null}
            </section>

          </aside>
        </div>
      </main>
      <DashboardDemoV4FloatingNav desktopVariant="full-height" />
    </div>
  );

  return (
    <div className="dashboard-demo-v4-route-shell dashboard-demo-v4-root">
      <main
        className={`dashboard-demo-v4-route-main min-h-dvh overflow-x-hidden text-[var(--ddv4-fg)] lg:pb-0 ${
          showMobileActionBar ? "pb-44" : "pb-28"
        }`}
      >
      <div className="mx-auto flex min-h-dvh w-full max-w-[min(1500px,100%)] flex-col px-4 py-4 sm:px-6 lg:px-8 lg:py-6">
        <h1 className="sr-only">Coding</h1>

        <div className="grid flex-1 items-start gap-5 xl:grid-cols-[248px_minmax(0,1fr)_328px]">
          <aside
            aria-label="Project task rail"
            className={`${commandPanelClass} order-2 space-y-4 p-4 xl:sticky xl:top-6 xl:order-1 xl:max-h-[calc(100dvh-3rem)] xl:overflow-auto`}
          >
            <div>
              <p className={commandLabelClass}>
                Workspace
              </p>
              <div className={`${commandInsetClass} mt-2 p-3`}>
                <div className={`text-sm font-semibold ${commandTextClass}`}>SpiritOS</div>
                <div className={`mt-1 text-xs ${commandMutedClass}`}>Coding workspace</div>
              </div>
            </div>
            <div>
              <p className={commandLabelClass}>Current task</p>
              <div className={`${commandInsetClass} mt-2 space-y-3 p-3`}>
                <div>
                  <div className={`break-words text-sm font-semibold ${commandTextClass}`}>
                    {currentTaskTitle}
                  </div>
                  <div className={`mt-1 text-xs ${commandMutedClass}`}>{currentTaskState}</div>
                </div>
                <dl className="space-y-2 text-xs">
                  {railScopeItems.map((item) => (
                    <div className="grid grid-cols-[4.75rem_minmax(0,1fr)] gap-2" key={item.label}>
                      <dt className="uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                        {item.label}
                      </dt>
                      <dd className={`truncate ${commandMutedClass}`} title={item.value}>
                        {item.value}
                      </dd>
                    </div>
                  ))}
                </dl>
                <div
                  className="rounded-md border border-[var(--ddv4-surface-border-soft)] px-2 py-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]"
                  title={activeProviderTruth.blockedReason || undefined}
                >
                  {activeProviderTruth.providerLabel} / {activeProviderTruth.modelLabel}
                  <span className="mt-1 block normal-case tracking-normal text-[var(--ddv4-fg-muted)]">
                    Hermes:{" "}
                    {activeProviderTruth.configuredModelIsHermes === null
                      ? "unknown"
                      : activeProviderTruth.configuredModelIsHermes
                        ? "configured"
                        : "not configured"}
                  </span>
                </div>
              </div>
            </div>
            <nav aria-label="Task queues" className="space-y-2">
              <p className={commandLabelClass}>
                Tasks
              </p>
              {visibleRailTaskItems.map((item) => (
                <div
                  className={`flex min-h-11 items-center justify-between gap-3 rounded-md border px-3 text-sm transition-colors ${
                    item.active
                      ? "border-[var(--spirit-accent)] bg-[var(--ddv4-nav-active-bg)] text-[var(--ddv4-nav-active-fg)]"
                      : "border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] text-[var(--ddv4-fg-muted)]"
                  }`}
                  key={item.label}
                >
                  <span>{item.label}</span>
                  <span className="shrink-0 text-xs opacity-75">{item.value}</span>
                </div>
              ))}
            </nav>

            <section aria-label="Agent trials runner" className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <p className={commandLabelClass}>Runner</p>
                <span className="rounded-md border border-[var(--ddv4-pill-border)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                  {trialMode === "code"
                    ? trialState.latestGrades.coding
                    : trialMode === "design"
                      ? trialState.latestGrades.design
                      : trialState.latestGrades.hybrid}
                </span>
              </div>
              <div className={`${commandInsetClass} space-y-2 p-2 text-sm`}>
                <div className="grid grid-cols-3 gap-1">
                  {(["code", "design", "hybrid"] as AgentTrialMode[]).map((mode) => (
                    <button
                      aria-pressed={trialMode === mode}
                      className={`min-h-8 rounded-md border px-2 text-xs font-semibold transition-colors ${commandFocusClass} ${
                        trialMode === mode
                          ? "border-[var(--spirit-accent)] bg-[var(--ddv4-nav-active-bg)] text-[var(--ddv4-nav-active-fg)]"
                          : "border-[var(--ddv4-surface-border-soft)] text-[var(--ddv4-fg-muted)] hover:bg-[var(--ddv4-surface-fill)]"
                      }`}
                      key={mode}
                      onClick={() => {
                        setTrialMode(mode);
                        resetTrialResult();
                      }}
                      type="button"
                    >
                      {trialModeLabels[mode]}
                    </button>
                  ))}
                </div>
                <div>
                  <p className={`mb-1 ${commandLabelClass}`}>Trial mode</p>
                  <div className="grid grid-cols-2 gap-1">
                    {([
                      ["live_apply", "Live Apply Trial"],
                      ["preview_only", "Preview diagnostic"],
                    ] as [AgentTrialProofMode, string][]).map(([mode, label]) => (
                      <button
                        aria-label={mode === "live_apply" ? "Live trial mode" : "Preview diagnostic mode"}
                        aria-pressed={trialProofMode === mode}
                        className={`min-h-8 rounded-md border px-2 text-xs font-semibold transition-colors ${commandFocusClass} ${
                          trialProofMode === mode
                            ? "border-[var(--spirit-accent)] bg-[var(--ddv4-nav-active-bg)] text-[var(--ddv4-nav-active-fg)]"
                            : "border-[var(--ddv4-surface-border-soft)] text-[var(--ddv4-fg-muted)] hover:bg-[var(--ddv4-surface-fill)]"
                        }`}
                        key={mode}
                        onClick={() => {
                          setTrialProofMode(mode);
                          resetTrialResult();
                        }}
                        type="button"
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <p className={`mt-1 text-[11px] leading-4 ${commandMutedClass}`}>
                    Live Apply requires provider generation, execute-approved apply, disk verification, checks, and reversal availability before it counts.
                  </p>
                </div>
                <div>
                  <p className={`mb-1 ${commandLabelClass}`}>After verify</p>
                  <select
                    className={`min-h-9 w-full rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-2 text-sm text-[var(--ddv4-fg)] ${commandFocusClass}`}
                    onChange={(event) => {
                      setTrialApplyStrategy(event.target.value as AgentTrialApplyStrategy);
                      resetTrialResult();
                    }}
                    value={trialApplyStrategy}
                  >
                    <option value="hold_for_inspection">Hold changes for inspection</option>
                    <option value="auto_revert_after_verify">Auto-revert after verify</option>
                  </select>
                </div>
                <div>
                  <p className={`mb-1 ${commandLabelClass}`}>Active bank</p>
                  <div className="grid grid-cols-2 gap-1">
                    {([
                      ["actual-intelligence", trialMode === "design" ? "Designer Live Apply Bank" : trialMode === "hybrid" ? "Combined Live Apply Bank" : "Live Apply Bank"],
                      ["legacy-fixture-smoke", "Preview-only Diagnostic Bank"],
                    ] as [AgentTrialBank, string][]).map(([bank, label]) => (
                      <button
                        aria-label={bank === "actual-intelligence" ? "Live bank" : "Preview diagnostic bank"}
                        aria-pressed={trialBank === bank}
                        className={`min-h-8 rounded-md border px-2 text-xs font-semibold transition-colors ${commandFocusClass} ${
                          trialBank === bank
                            ? "border-[var(--spirit-accent)] bg-[var(--ddv4-nav-active-bg)] text-[var(--ddv4-nav-active-fg)]"
                            : "border-[var(--ddv4-surface-border-soft)] text-[var(--ddv4-fg-muted)] hover:bg-[var(--ddv4-surface-fill)]"
                        }`}
                        key={bank}
                        onClick={() => {
                          setTrialBank(bank);
                          resetTrialResult();
                        }}
                        type="button"
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  {trialBank === "legacy-fixture-smoke" ? (
                    <p className={`mt-1 text-[11px] leading-4 ${commandMutedClass}`}>
                      Legacy fixture smoke only. Does not count for live coding usefulness or S+.
                    </p>
                  ) : null}
                </div>
                <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
                  <label className="block">
                    <span className="mb-1 block text-xs font-semibold text-[var(--ddv4-fg-muted)]">
                      Size
                    </span>
                    <select
                      className={`min-h-9 w-full rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-2 text-sm text-[var(--ddv4-fg)] ${commandFocusClass}`}
                      onChange={(event) => {
                        setTrialRunSize(Number(event.target.value) as AgentTrialRunSize);
                        resetTrialResult();
                      }}
                      value={trialRunSize}
                    >
                      {agentTrialRunSizes.slice(0, 4).map((size) => (
                        <option key={size} value={size}>
                          {size} prompts
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-xs font-semibold text-[var(--ddv4-fg-muted)]">
                      View
                    </span>
                    <select
                      className={`min-h-9 w-full rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-2 text-sm text-[var(--ddv4-fg)] ${commandFocusClass}`}
                      onChange={(event) => {
                        setTrialViewport(event.target.value as AgentTrialViewport);
                        resetTrialResult();
                      }}
                      value={trialViewport}
                    >
                      {agentTrialViewports.map((viewport) => (
                        <option key={viewport} value={viewport}>
                          {viewport}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <button
                  className={`inline-flex min-h-9 w-full items-center justify-center gap-2 rounded-md bg-emerald-300 px-3 text-sm font-semibold text-slate-950 transition-colors hover:bg-emerald-200 ${commandFocusClass}`}
                  onClick={handleRunTrial}
                  type="button"
                >
                  Run trial
                </button>
                <button
                  className={`inline-flex min-h-9 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                  disabled={!canRevertTrialRuns}
                  onClick={() => void handleRevertAllTrialRuns()}
                  type="button"
                >
                  {isReverting ? "Reverting trial runs..." : "Revert all trial runs"}
                </button>
                <p className={`text-[11px] leading-4 ${commandMutedClass}`}>{trialReversalHelpText}</p>
                <dl className="grid gap-1.5 text-xs">
                  <div className="flex items-center justify-between gap-3 rounded-md border border-[var(--ddv4-surface-border-soft)] px-2 py-1.5">
                    <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                      Status
                    </dt>
                    <dd className={commandTextClass}>{trialStatusLabel}</dd>
                  </div>
                  <div className="flex items-center justify-between gap-3 rounded-md border border-[var(--ddv4-surface-border-soft)] px-2 py-1.5">
                    <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                      Score
                    </dt>
                    <dd className={commandTextClass}>{trialResultSummary.score} ({trialGrade})</dd>
                  </div>
                  <div className="rounded-md border border-[var(--ddv4-surface-border-soft)] px-2 py-1.5">
                    <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                      Result
                    </dt>
                    <dd className={`mt-1 ${commandTextClass}`}>
                      {trialRunState === "complete"
                        ? trialResultSummary.headline
                        : "Run a trial to see the latest result."}
                    </dd>
                  </div>
                  <div className="rounded-md border border-[var(--ddv4-surface-border-soft)] px-2 py-1.5">
                    <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                      Bank
                    </dt>
                    <dd className={`mt-1 ${commandTextClass}`}>{trialState.bankLabel}</dd>
                  </div>
                  <div className="rounded-md border border-[var(--ddv4-surface-border-soft)] px-2 py-1.5">
                    <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                      Category
                    </dt>
                    <dd className={`mt-1 ${commandTextClass}`}>
                      {trialRunState === "complete" ? trialCategoryLabel : "Waiting for trial."}
                    </dd>
                  </div>
                  {trialRunState === "complete" ? (
                    <div className="rounded-md border border-[var(--ddv4-surface-border-soft)] px-2 py-1.5">
                      <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                        Outcome mix
                      </dt>
                      <dd className={`mt-1 ${commandTextClass}`}>
                        Useful {trialResultSummary.usefulCount} / Expected safe blocks {trialResultSummary.expectedSafeBlockCount} / Needs review {trialResultSummary.needsReviewCount} / Failed {trialResultSummary.failedOnlyCount} / Not classified {trialResultSummary.notClassifiedCount}
                      </dd>
                      <p className={`mt-1 text-[11px] leading-4 ${commandMutedClass}`}>
                        Safe blocks mean the system avoided an unsafe action; they are not counted as useful coding help. Counts {trialResultSummary.countsSumMatchesSize ? "match" : "do not match"} the selected size.
                      </p>
                      <p className={`mt-1 text-[11px] leading-4 ${commandMutedClass}`}>
                        Live usefulness: {trialState.liveUsefulnessEligible ? "yes" : "no"}; S+ eligible: {trialState.liveUsefulnessEligible ? "yes" : "no"}. {trialState.liveUsefulnessReason}
                      </p>
                    </div>
                  ) : null}
                </dl>
                {trialRunState === "complete" ? (
                  <div className="space-y-2">
                    <details className="rounded-md border border-[var(--ddv4-surface-border-soft)] px-2 py-1.5">
                      <summary className={`cursor-pointer text-xs font-semibold ${commandTextClass}`}>
                        View run details
                      </summary>
                      <div className="mt-2 space-y-2">
                        {trialState.actualPromptPreviews.map((preview, index) => (
                          <article
                            className="rounded-md border border-[var(--ddv4-surface-border-soft)] p-2 text-xs"
                            key={`${preview.fixtureId}-${index}`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <h3 className={`font-semibold ${commandTextClass}`}>
                                {index + 1}. {preview.fixtureId}
                              </h3>
                              {isTrialAttentionItem(preview) ? (
                                <span className="rounded-md border border-amber-300/40 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-amber-100">
                                  attention
                                </span>
                              ) : null}
                            </div>
                            <div className="mt-2">
                              <VisibleResultBadgeRow result={preview.visibleResult} />
                            </div>
                            <p className={`mt-1 line-clamp-3 ${commandMutedClass}`}>
                              {preview.submittedPrompt || "submitted prompt not recorded"}
                            </p>
                            <dl className="mt-2 grid gap-1">
                              <div>
                                <dt className="font-semibold text-[var(--ddv4-fg-faint)]">Expected</dt>
                                <dd className={commandTextClass}>{preview.expectedBehavior}: {preview.triedToDo}</dd>
                              </div>
                              <div>
                                <dt className="font-semibold text-[var(--ddv4-fg-faint)]">Actual</dt>
                                <dd className={commandTextClass}>{preview.actualBehavior}: {preview.simpleReason}</dd>
                              </div>
                              <div>
                                <dt className="font-semibold text-[var(--ddv4-fg-faint)]">Result</dt>
                                <dd className={commandTextClass}>{outcomeCategoryForPreview(preview)} / {preview.reason}</dd>
                              </div>
                              <div>
                                <dt className="font-semibold text-[var(--ddv4-fg-faint)]">Provider/model</dt>
                                <dd className={commandTextClass}>
                                  {formatNullable(preview.provider)} / {formatNullable(preview.model)} / provider_call_made: {preview.providerCallMade ? "true" : "false"}
                                </dd>
                              </div>
                              <div>
                                <dt className="font-semibold text-[var(--ddv4-fg-faint)]">Live usefulness</dt>
                                <dd className={commandTextClass}>
                                  counts: {preview.actualIntelligence.countsForCodingUsefulness && preview.providerCallMade ? "yes" : "no"} / safety only: {preview.actualIntelligence.countsForSafety ? "yes" : "no"} / S+ eligible: {preview.actualIntelligence.sPlusEligible ? "yes" : "no"}
                                </dd>
                              </div>
                              <div>
                                <dt className="font-semibold text-[var(--ddv4-fg-faint)]">Missing fields</dt>
                                <dd className={commandTextClass}>{formatList(preview.missingFields, "none")}</dd>
                              </div>
                              <div>
                                <dt className="font-semibold text-[var(--ddv4-fg-faint)]">Target</dt>
                                <dd className={commandTextClass}>
                                  {preview.selectedFiles[0] ?? formatList(preview.candidateFiles, "not recorded")}
                                </dd>
                              </div>
                              <div>
                                <dt className="font-semibold text-[var(--ddv4-fg-faint)]">Allowed files</dt>
                                <dd className={commandTextClass}>{formatList(preview.allowedFiles, "not recorded")}</dd>
                              </div>
                              <div>
                                <dt className="font-semibold text-[var(--ddv4-fg-faint)]">Checks</dt>
                                <dd className={commandTextClass}>{formatList(preview.recommendedChecks, "not recorded")}</dd>
                              </div>
                            </dl>
                          </article>
                        ))}
                      </div>
                    </details>
                    <button
                      className={`inline-flex min-h-9 w-full items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                      onClick={() => void copyTrialReport()}
                      type="button"
                    >
                      <Copy aria-hidden="true" size={15} />
                      Copy report
                    </button>
                    <button
                      className={`inline-flex min-h-9 w-full items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                      onClick={() => void copyTrialPromptsOnly()}
                      type="button"
                    >
                      <Copy aria-hidden="true" size={15} />
                      Copy prompts only
                    </button>
                    <button
                      className={`inline-flex min-h-9 w-full items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                      onClick={() => void copyTrialAttentionOnly()}
                      type="button"
                    >
                      <Copy aria-hidden="true" size={15} />
                      Copy failures or attention only
                    </button>
                  </div>
                ) : null}
                {trialCopyStatus ? (
                  <p className={`text-xs ${commandMutedClass}`}>{trialCopyStatus}</p>
                ) : null}
              </div>
            </section>
          </aside>

          <div className="order-1 flex min-w-0 flex-col gap-5 xl:order-2">
        <section
          aria-labelledby="current-state-heading"
          aria-live="polite"
          className={`${commandPanelClass} order-2 p-4 sm:p-5`}
          role="status"
        >
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 id="current-state-heading" className="text-base font-semibold text-[var(--ddv4-fg)]">
                Task status
              </h2>
              <p className="mt-1 text-sm text-[var(--ddv4-fg-muted)]">{nextSafeAction}</p>
              {manualTrialVerdict.fixtureId ? (
                <p className="mt-1 text-xs text-[var(--ddv4-fg-faint)]">
                  Trial fixture: {manualTrialVerdict.fixtureId}
                  {manualTrialVerdict.verdict === "PASS" || manualTrialVerdict.verdict === "FAIL"
                    ? ` · ${manualTrialVerdict.detail}`
                    : ""}
                </p>
              ) : null}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {manualTrialVerdict.verdict === "PASS" || manualTrialVerdict.verdict === "FAIL" ? (
                <span
                  aria-label={`Trial verdict ${manualTrialVerdict.verdict}`}
                  className={`inline-flex min-h-9 items-center rounded-md border px-3 text-xs font-semibold uppercase tracking-[0.08em] ${trialVerdictBadgeClass(manualTrialVerdict.verdict)}`}
                >
                  {manualTrialVerdict.verdict}
                </span>
              ) : null}
              <span className="inline-flex min-h-9 items-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-xs font-semibold text-[var(--ddv4-fg)]">
                {currentTaskState}
              </span>
            </div>
          </div>
          <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
            <div className={`${commandInsetClass} p-3`}>
              <div className={commandLabelClass}>
                Task
              </div>
              <div className={`mt-1 break-words ${commandTextClass}`}>{currentTaskTitle}</div>
            </div>
            <div className={`${commandInsetClass} p-3`}>
              <div className={commandLabelClass}>
                Target
              </div>
              <div className={`mt-1 break-words ${commandTextClass}`}>{currentTaskTarget}</div>
            </div>
          </div>
        </section>

        <div className="order-1">
          <section className="min-w-0 space-y-5" aria-labelledby="task-composer-heading">
            <section
              aria-labelledby="task-transcript-heading"
              className={`${commandPanelClass} p-4 sm:p-6`}
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <p className={commandLabelClass}>Active work</p>
                  <h2
                    id="task-transcript-heading"
                    className={`mt-2 text-xl font-semibold ${commandTextClass}`}
                  >
                    Task transcript
                  </h2>
                </div>
                <span className="inline-flex min-h-9 items-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-xs font-semibold text-[var(--ddv4-fg)]">
                  {currentTaskState}
                </span>
              </div>
              <dl className="mt-4 grid gap-2 text-xs sm:grid-cols-3">
                {compactContextItems.map((item) => (
                  <div className="min-w-0 rounded-md border border-[var(--ddv4-surface-border-soft)] px-3 py-2" key={item.label}>
                    <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                      {item.label}
                    </dt>
                    <dd className={`mt-1 truncate ${commandMutedClass}`} title={item.value}>
                      {item.value}
                    </dd>
                  </div>
                ))}
              </dl>
              <div className="mt-5 space-y-3">
                {previewState.events.length > 0 ? (
                  <ol className="grid gap-2 text-sm sm:grid-cols-2">
                    {previewState.events.map((event, index) => (
                      <li
                        className={`${commandInsetClass} min-h-20 p-3`}
                        key={`${event.label}-${index}`}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <span className={`font-semibold ${commandTextClass}`}>{event.label}</span>
                          <span className={`text-xs uppercase tracking-[0.12em] ${commandMutedClass}`}>
                            {event.status}
                          </span>
                        </div>
                        <p className={`mt-2 text-sm leading-5 ${commandMutedClass}`}>{event.detail}</p>
                      </li>
                    ))}
                  </ol>
                ) : null}
                {transcriptItems.map((item, index) => (
                  <article
                    className={`${commandInsetClass} p-4`}
                    key={`${item.speaker}-${index}`}
                  >
                    <div className={commandLabelClass}>{item.speaker}</div>
                    <p className={`mt-2 whitespace-pre-wrap break-words text-base leading-7 ${commandTextClass}`}>
                      {item.body}
                    </p>
                  </article>
                ))}
              </div>
            </section>

            <div className={`${commandPanelClass} p-4 sm:p-6`}>
              <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] bg-[var(--ddv4-pill-bg)] text-[var(--ddv4-fg)]">
                  <FileText aria-hidden="true" size={20} />
                </div>
                <div className="min-w-0">
                  <h2 id="task-composer-heading" className={`text-xl font-semibold ${commandTextClass}`}>
                    Task Composer
                  </h2>
                  <p className={`text-sm ${commandMutedClass}`}>Describe the coding task. SpiritOS discovers the likely files after start.</p>
                </div>
                </div>
                <span className="inline-flex min-h-9 items-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-xs font-semibold text-[var(--ddv4-fg)]">
                  {currentTaskState}
                </span>
              </div>

              <div className="space-y-4">
                <label className="block">
                  <span className={`mb-2 block text-sm font-medium ${commandTextClass}`}>Task</span>
                  <textarea
                    className={`min-h-40 w-full resize-y rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-4 py-4 text-base leading-7 text-[var(--ddv4-fg)] placeholder:text-[var(--ddv4-fg-faint)] sm:text-base ${commandControlClass}`}
                    onChange={(event) => {
                      handleTaskChange(event.target.value);
                    }}
                    placeholder="Describe the coding task here."
                    value={task}
                  />
                </label>

                <div
                  aria-live="polite"
                  className={`rounded-md border px-3 py-3 text-sm ${
                    canPreview || canStartTask
                      ? "border-emerald-300/30 bg-emerald-300/10 text-emerald-100"
                      : "border-amber-300/30 bg-amber-300/10 text-amber-100"
                  }`}
                >
                  {canPreview
                    ? protectedPathRequested
                      ? "Ready to start. Protected paths will be blocked before preview."
                      : "Ready to start. Preview mode will not change files."
                    : canStartTask
                      ? "Ready to start. I may ask one clarification if discovery is too ambiguous."
                    : validationMessages.join(", ")}
                </div>

                <button
                  className={`inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 shadow-sm transition-colors hover:bg-emerald-200 ${commandFocusClass} ${
                    canStartTask ? "" : "opacity-60"
                  }`}
                  disabled={!canStartTask || previewState.isLoading}
                  onClick={handleDraftPreview}
                  type="button"
                >
                  <ShieldCheck aria-hidden="true" size={18} />
                  {previewState.isLoading ? "Working..." : "Start task"}
                </button>

                <button
                  className={`inline-flex min-h-11 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                  disabled={!canRewindPrompt}
                  onClick={handleRewindPrompt}
                  type="button"
                >
                  Rewind entered prompt
                </button>
                <button
                  className={`inline-flex min-h-11 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                  disabled={!canRevertTrialRuns}
                  onClick={() => void handleRevertAllTrialRuns()}
                  type="button"
                >
                  {isReverting ? "Reverting trial runs..." : "Revert all trial runs"}
                </button>
                {reversalStatus ? (
                  <p className={`text-sm ${commandMutedClass}`}>{reversalStatus}</p>
                ) : null}

                <details className={`${commandInsetClass} space-y-4 p-3`}>
                  <summary className={`cursor-pointer text-sm font-semibold ${commandTextClass}`}>
                    Advanced details
                  </summary>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <label className="block">
                      <span className={`mb-2 block text-sm font-medium ${commandTextClass}`}>
                        Target file
                      </span>
                      <input
                        className={`min-h-12 w-full rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-3 text-base text-[var(--ddv4-fg)] placeholder:text-[var(--ddv4-fg-faint)] sm:text-sm ${commandControlClass}`}
                        onChange={(event) => {
                          setTargetFile(event.target.value);
                          resetPreviewForEdit();
                        }}
                        placeholder="docs/example.md"
                        value={targetFile}
                      />
                    </label>
                    <label className="block">
                      <span className={`mb-2 block text-sm font-medium ${commandTextClass}`}>
                        Allowed files
                      </span>
                      <input
                        className={`min-h-12 w-full rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-3 text-base text-[var(--ddv4-fg)] placeholder:text-[var(--ddv4-fg-faint)] sm:text-sm ${commandControlClass}`}
                        onChange={(event) => {
                          setAllowedFiles(event.target.value);
                          resetPreviewForEdit();
                        }}
                        placeholder="Same as target"
                        value={allowedFiles}
                      />
                    </label>
                  </div>

                  <label className="block">
                    <span className={`mb-2 block text-sm font-medium ${commandTextClass}`}>
                      Expected checks
                    </span>
                    <input
                      className={`min-h-12 w-full rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-3 text-base text-[var(--ddv4-fg)] placeholder:text-[var(--ddv4-fg-faint)] sm:text-sm ${commandControlClass}`}
                      onChange={(event) => {
                        setExpectedChecks(event.target.value);
                        resetPreviewForEdit();
                      }}
                      placeholder="npm run typecheck"
                      value={expectedChecks}
                    />
                  </label>
                </details>

              </div>
            </div>

            {showWorkspaceEmpty ? (
              <section
                aria-labelledby="workspace-empty-heading"
                className={`${commandPanelClass} p-4 sm:p-5`}
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <p className={commandLabelClass}>Workspace</p>
                    <h2
                      id="workspace-empty-heading"
                      className={`mt-2 text-base font-semibold ${commandTextClass}`}
                    >
                      No active task
                    </h2>
                  </div>
                  <span className="inline-flex min-h-9 items-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-xs font-semibold text-[var(--ddv4-fg)]">
                    Ready
                  </span>
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {workspaceEmptyItems.map((item) => (
                    <div className={`${commandInsetClass} min-h-28 p-3`} key={item.label}>
                      <div className={`text-sm font-semibold ${commandTextClass}`}>
                        {item.label}
                      </div>
                      <p className={`mt-2 text-sm leading-6 ${commandMutedClass}`}>{item.value}</p>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}

            {showDesignerResult ? (
              <section
                aria-labelledby="designer-result-heading"
                className={`${commandPanelClass} p-4 sm:p-5`}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className={commandLabelClass}>Design</p>
                    <h2 id="designer-result-heading" className={`mt-2 text-base font-semibold ${commandTextClass}`}>
                      Designer result
                    </h2>
                  </div>
                  <button
                    className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                    onClick={() => void copyDesignReport()}
                    type="button"
                  >
                    <Copy aria-hidden="true" size={16} />
                    Copy report
                  </button>
                </div>
                <div className="mt-4 space-y-2">
                  <VisibleResultBadgeRow result={designVisibleResult} />
                  <p className={`text-sm ${commandMutedClass}`}>
                    Target: {currentTaskTarget}. Next: {designVisibleResult.user_next_action}
                  </p>
                </div>
                <p className={`mt-4 whitespace-pre-wrap text-sm leading-6 ${commandTextClass}`}>
                  {currentDesignResult}
                </p>
                {designReportCopyStatus ? (
                  <p className={`mt-3 text-sm ${commandMutedClass}`}>{designReportCopyStatus}</p>
                ) : null}
              </section>
            ) : null}

            {showCombinedFlow ? (
              <section
                aria-labelledby="combined-flow-heading"
                className={`${commandPanelClass} p-4 sm:p-5`}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className={commandLabelClass}>Combined</p>
                    <h2 id="combined-flow-heading" className={`mt-2 text-base font-semibold ${commandTextClass}`}>
                      Combined flow
                    </h2>
                  </div>
                  <span className="inline-flex min-h-9 items-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-xs font-semibold text-[var(--ddv4-fg)]">
                    {combinedState}
                  </span>
                </div>
                <div className="mt-4 space-y-2">
                  <VisibleResultBadgeRow result={combinedVisibleResult} />
                  <p className={`text-sm ${commandMutedClass}`}>
                    Target: {currentTaskTarget}. Next: {combinedVisibleResult.user_next_action}
                  </p>
                </div>
                <dl className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>Designer critique</dt>
                    <dd className={`mt-2 ${commandTextClass}`}>Ready as implementation context.</dd>
                  </div>
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>Coder handoff</dt>
                    <dd className={`mt-2 ${commandTextClass}`}>{combinedHandoffStatus}</dd>
                  </div>
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>Designer recheck</dt>
                    <dd className={`mt-2 ${commandTextClass}`}>Pending after coder result.</dd>
                  </div>
                </dl>
                <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <p className={`text-sm ${commandMutedClass}`}>
                    Designer, coder, and recheck steps are represented here in product language.
                  </p>
                  <button
                    className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                    onClick={() => void copyCombinedDiagnostics()}
                    type="button"
                  >
                    <Copy aria-hidden="true" size={16} />
                    Copy combined diagnostics
                  </button>
                </div>
                {combinedCopyStatus ? (
                  <p className={`mt-3 text-sm ${commandMutedClass}`}>{combinedCopyStatus}</p>
                ) : null}
              </section>
            ) : null}

            {previewState.status !== "idle" || previewState.isLoading ? (
              <section className={`${commandPanelClass} p-4 sm:p-5`}>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className={`text-base font-semibold ${commandTextClass}`}>Diff Review</h2>
                    <p className={`mt-1 text-sm ${commandMutedClass}`}>
                      {previewState.isLoading
                        ? "Requesting a safe preview. No files have been changed."
                        : previewState.status === "satisfied"
                          ? "Already satisfied. No diff was produced."
                          : previewState.status === "ready"
                            ? "Preview ready. No files changed yet."
                            : "Preview blocked. No files changed."}
                    </p>
                  </div>
                  <Link
                    className={`inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-medium text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                    href="/proxy-backend"
                  >
                    Open diagnostics
                  </Link>
                </div>
                <div className="mt-4 space-y-2">
                  <VisibleResultBadgeRow result={codingVisibleResult} />
                  <p className={`text-sm ${commandMutedClass}`}>
                    Target: {currentTaskTarget}. Next: {codingVisibleResult.user_next_action}
                  </p>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>
                      Current step
                    </dt>
                    <dd className={`mt-1 break-words ${commandTextClass}`}>{previewState.currentPhase}</dd>
                  </div>
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>
                      Preview changed files
                    </dt>
                    <dd className={`mt-1 break-words ${commandTextClass}`}>
                      {buildChangedFilesDiagnostics({
                        appliedAt: previewState.appliedAt,
                        diff: previewState.diff,
                        status: previewState.status,
                        verificationChangedFiles: previewState.changedFiles,
                      }).previewChangedFiles.join(", ") || "None"}
                    </dd>
                  </div>
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>
                      Disk changed files
                    </dt>
                    <dd className={`mt-1 break-words ${commandTextClass}`}>
                      {buildChangedFilesDiagnostics({
                        appliedAt: previewState.appliedAt,
                        diff: previewState.diff,
                        status: previewState.status,
                        verificationChangedFiles: previewState.changedFiles,
                      }).diskChangedFiles.join(", ") || "None"}
                    </dd>
                  </div>
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>
                      Changed files
                    </dt>
                    <dd className={`mt-1 break-words ${commandTextClass}`}>
                      {previewState.changedFiles.length > 0
                        ? previewState.changedFiles.join(", ")
                        : "None reported"}
                    </dd>
                  </div>
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>
                      Checks
                    </dt>
                    <dd className={`mt-1 break-words ${commandTextClass}`}>
                      {formatList(previewState.checks, "Recommended after preview")}
                    </dd>
                  </div>
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>
                      Result
                    </dt>
                    <dd className={`mt-1 break-words ${commandTextClass}`}>
                      {previewState.error ??
                        previewState.blocker ??
                        (previewState.isLoading ? "Previewing" : "Preview ready")}
                    </dd>
                  </div>
                </dl>

                {showVerificationTargets ? (
                  <section
                    aria-label="Verification targets"
                    className={`${commandInsetClass} mt-4 p-3`}
                  >
                    <div className="flex flex-col gap-1">
                      <h3 className={`text-sm font-semibold ${commandTextClass}`}>Verification targets</h3>
                      <p className={`text-sm ${commandMutedClass}`}>
                        Use this file/page to verify the applied change.
                      </p>
                    </div>
                    <div className="mt-3 space-y-3">
                      {verificationTargets.map((target) => (
                        <div
                          className="rounded-md border border-[var(--ddv4-surface-border-soft)] p-3"
                          key={target.path}
                        >
                          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                            <div className="min-w-0">
                              <p className={`break-words font-mono text-sm ${commandTextClass}`}>
                                {target.path}
                              </p>
                              <p className={`mt-1 text-xs ${commandMutedClass}`}>
                                {target.safe
                                  ? "No internal file viewer is available yet. Copy the path and open it in your editor."
                                  : "Path is not repo-relative safe, so actions are disabled. Verify manually before opening."}
                              </p>
                              <p className={`mt-1 text-xs ${commandMutedClass}`}>
                                {target.routeInferenceNote}
                              </p>
                            </div>
                            <div className="flex shrink-0 flex-col gap-2 sm:items-end">
                              <button
                                className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                                disabled={!target.safe}
                                onClick={() => void copyVerificationPath(target.path)}
                                type="button"
                              >
                                <Copy aria-hidden="true" size={16} />
                                Copy path
                              </button>
                              {target.relatedPageHref ? (
                                <Link
                                  className={`inline-flex min-h-10 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                                  href={target.relatedPageHref}
                                >
                                  Open related page
                                </Link>
                              ) : (
                                <span className={`text-xs ${commandMutedClass}`}>
                                  No related page inferred.
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    {verificationCopyStatus ? (
                      <p className={`mt-3 text-sm ${commandMutedClass}`}>{verificationCopyStatus}</p>
                    ) : null}
                  </section>
                ) : null}

                {previewState.diff ? (
                  <pre className="mt-4 max-h-72 overflow-auto rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] p-3 text-xs leading-5 text-[var(--ddv4-fg)]">
                    {previewState.diff}
                  </pre>
                ) : null}

                <details className={`${commandInsetClass} mt-4 overflow-hidden`}>
                  <summary className={`min-h-12 cursor-pointer px-3 py-3 text-sm font-semibold ${commandTextClass} ${commandControlClass}`}>
                    Advanced details
                  </summary>
                  <dl className="grid gap-3 border-t border-[var(--ddv4-surface-border-soft)] p-3 text-sm sm:grid-cols-2">
                    <div>
                      <dt className={commandLabelClass}>Target candidates</dt>
                      <dd className={`mt-1 break-words ${commandTextClass}`}>{formatList(previewState.targetCandidates, "none")}</dd>
                    </div>
                    <div>
                      <dt className={commandLabelClass}>Selected target</dt>
                      <dd className={`mt-1 break-words ${commandTextClass}`}>{previewState.selectedTarget ?? "none"}</dd>
                    </div>
                    <div>
                      <dt className={commandLabelClass}>Internal allowed files</dt>
                      <dd className={`mt-1 break-words ${commandTextClass}`}>{formatList(previewState.allowedFiles, "none")}</dd>
                    </div>
                    <div>
                      <dt className={commandLabelClass}>Forbidden files</dt>
                      <dd className={`mt-1 break-words ${commandTextClass}`}>{formatList(previewState.forbiddenFiles, "none")}</dd>
                    </div>
                    <div>
                      <dt className={commandLabelClass}>Reason code</dt>
                      <dd className={`mt-1 break-words ${commandTextClass}`}>{previewState.reasonCode ?? "none"}</dd>
                    </div>
                    <div>
                      <dt className={commandLabelClass}>Route</dt>
                      <dd className={`mt-1 break-words ${commandTextClass}`}>{previewState.routeCalled ?? "none"}</dd>
                    </div>
                    <div className="sm:col-span-2">
                      <dt className={commandLabelClass}>Stress-test readiness</dt>
                      <dd className={`mt-1 space-y-1 break-words ${commandTextClass}`}>
                        <div>Source Proxy reachable: {stressTestReadiness.sourceProxyReachable ? "yes" : "no"}</div>
                        <div>Source Proxy local model: {stressTestReadiness.sourceProxyLocalModel}</div>
                        <div>Ollama storage: {stressTestReadiness.ollamaStoragePath}</div>
                        <div>Manual composer model truth: {stressTestReadiness.manualComposerModelTruth}</div>
                        <div>Trial runner model truth: {stressTestReadiness.trialRunnerModelTruth}</div>
                        <div>Last provider call smoke: {stressTestReadiness.lastProviderCallSmoke}</div>
                        <div>Stale trial receipts: {stressTestReadiness.staleTrialReceipts}</div>
                        <div>Trial fixtures clean: {stressTestReadiness.trialFixturesClean}</div>
                        <div>
                          Ready for 10-prompt stress test:{" "}
                          {stressTestReadiness.readyForTenPromptStressTest ? "yes" : "no"} — {stressTestReadiness.readyReason}
                        </div>
                        <div className="pt-2">
                          <button
                            className={`inline-flex min-h-9 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-xs font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                            disabled={isRunningStressSmoke}
                            onClick={() => void runHermesStressSmoke()}
                            type="button"
                          >
                            {isRunningStressSmoke ? "Running Hermes smoke..." : "Run Hermes 4 stress smoke"}
                          </button>
                          {stressSmokeStatus ? (
                            <p className={`mt-2 text-xs ${commandMutedClass}`}>{stressSmokeStatus}</p>
                          ) : null}
                        </div>
                      </dd>
                    </div>
                  </dl>
                </details>
              </section>
            ) : null}

            {previewState.status !== "idle" || previewState.isLoading ? (
              <section className={`${commandPanelClass} p-4 sm:p-5`}>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className={`text-base font-semibold ${commandTextClass}`}>Safe Next Action</h2>
                    <p className={`mt-1 text-sm ${commandMutedClass}`}>
                      {nextSafeAction}
                    </p>
                    {manualTrialVerdict.fixtureId &&
                    (manualTrialVerdict.verdict === "PASS" || manualTrialVerdict.verdict === "FAIL") ? (
                      <p className={`mt-1 text-xs ${commandMutedClass}`}>{manualTrialVerdict.detail}</p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {manualTrialVerdict.verdict === "PASS" || manualTrialVerdict.verdict === "FAIL" ? (
                      <span
                        aria-label={`Trial verdict ${manualTrialVerdict.verdict}`}
                        className={`inline-flex min-h-9 items-center rounded-md border px-3 text-xs font-semibold uppercase tracking-[0.08em] ${trialVerdictBadgeClass(manualTrialVerdict.verdict)}`}
                      >
                        {manualTrialVerdict.verdict}
                      </span>
                    ) : null}
                    <span
                      className={`inline-flex min-h-9 items-center rounded-md border px-3 text-xs font-semibold ${
                        approvalControlsAvailable
                          ? "border-emerald-300/40 bg-emerald-300/10 text-emerald-100"
                          : previewState.status === "satisfied"
                            ? "border-cyan-300/40 bg-cyan-300/10 text-cyan-100"
                            : "border-amber-300/40 bg-amber-300/10 text-amber-100"
                      }`}
                    >
                      {approvalControlsAvailable
                        ? "approval available"
                        : previewState.status === "satisfied"
                          ? "already satisfied"
                          : "approval unavailable"}
                    </span>
                  </div>
                </div>

                {previewState.error ? (
                  <div className="mt-4 rounded-md border border-red-300/40 bg-red-300/10 px-3 py-3 text-sm text-red-100">
                    {previewState.error}
                  </div>
                ) : null}

                {applyControlsVisible && applyScopePreflight.reason ? (
                  <div className="mt-4 rounded-md border border-red-300/40 bg-red-300/10 px-3 py-3 text-sm text-red-100">
                    {applyScopePreflight.reason}
                  </div>
                ) : null}

                {showCopyDiagnostics ? (
                  <div className="mt-4 flex flex-col gap-2 rounded-md border border-amber-300/30 bg-amber-300/10 p-3 text-sm text-amber-50 sm:flex-row sm:items-center sm:justify-between">
                    <span>Full run diagnostics are ready for handoff.</span>
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                      <span
                        className={`inline-flex min-h-8 items-center justify-center rounded-md border px-2.5 text-xs font-semibold ${
                          diagnosticsTagTone === "fix"
                            ? "border-red-200/40 bg-red-300/15 text-red-50"
                            : diagnosticsTagTone === "clarify"
                              ? "border-amber-200/40 bg-amber-300/15 text-amber-50"
                              : diagnosticsTagTone === "safe"
                                ? "border-emerald-200/30 bg-emerald-300/10 text-emerald-50"
                                : "border-emerald-200/30 bg-emerald-300/10 text-emerald-50"
                        }`}
                      >
                        {diagnosticsTag}
                      </span>
                      <button
                        className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-amber-200/30 bg-black/20 px-3 text-sm font-semibold text-amber-50 transition-colors hover:bg-amber-200/10 ${commandFocusClass}`}
                        onClick={() => void copyDiagnostics()}
                        type="button"
                      >
                        <Copy aria-hidden="true" size={16} />
                        Copy full diagnostics
                      </button>
                    </div>
                  </div>
                ) : null}
                {diagnosticCopyStatus ? (
                  <p className="mt-2 text-sm text-[var(--ddv4-fg-muted)]">{diagnosticCopyStatus}</p>
                ) : null}

                {(canRevertCurrentRun || canRevertTrialRuns || reversalStatus) ? (
                  <div className={`${commandInsetClass} mt-4 p-3`}>
                    <div className={`mb-3 text-sm font-medium ${commandTextClass}`}>
                      Reversal controls
                    </div>
                    <div className="flex flex-col gap-2 sm:flex-row">
                      <button
                        className={`inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                        disabled={!canRevertCurrentRun}
                        onClick={() => currentReversalReceipt ? void handleRevertReceipt(currentReversalReceipt) : undefined}
                        type="button"
                      >
                        {isReverting ? "Reverting..." : currentReversalButtonLabel}
                      </button>
                      <button
                        className={`inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                        disabled={!canRevertTrialRuns}
                        onClick={() => void handleRevertAllTrialRuns()}
                        type="button"
                      >
                        Revert all trial runs
                      </button>
                    </div>
                    <p className={`mt-3 text-sm ${commandMutedClass}`}>
                      {reversalStatus ||
                        (unrevertedTrialRunReceipts.length > 0
                          ? `${unrevertedTrialRunReceipts.length} unreverted trial run${unrevertedTrialRunReceipts.length === 1 ? "" : "s"} tracked. Reverse applies use the original allowed_files.`
                          : appliedRunReceipts.some((receipt) => receipt.staleResolvedAt)
                            ? "Stale trial receipt reconciled; no active unreverted trial changes remain on disk."
                            : "No active unreverted trial runs tracked.")}
                    </p>
                  </div>
                ) : null}

                <div className="mt-4 rounded-md border border-sky-300/30 bg-sky-300/10 p-3 text-sm text-sky-100">
                  {previewState.status === "applied"
                    ? "Applied, verification required. Commit and push are not available here."
                    : previewState.status === "approved"
                      ? "Approved, not applied. Files are still unchanged until you apply the approved diff."
                      : previewState.status === "satisfied"
                        ? "No files changed. Coder reported the target already matches the task. Use a new unique append sentence in the task if you still need a docs smoke diff."
                        : "No files changed yet. Approval is required before apply. Commit and push are not available here."}
                </div>

                <div className={`${commandInsetClass} mt-4 p-3`}>
                  <div className={`mb-3 text-sm font-medium ${commandTextClass}`}>
                    {previewState.status === "applied"
                      ? "Last action: approved diff applied. Verification is required next."
                      : previewState.status === "approved"
                        ? "Last action: human approval recorded. No files changed yet."
                        : previewState.status === "satisfied"
                          ? "No apply step. Revise the task or use diagnostics for a bounded proposal with a fresh literal."
                          : "Next legal action appears after preview gates pass."}
                  </div>
                  <div className="flex flex-col gap-2 sm:flex-row">
                    {approvalControlsAvailable ? (
                      <>
                        <button
                          className={`inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-medium text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                          onClick={handleRejectPreview}
                          type="button"
                        >
                          Reject
                        </button>
                        <button
                          className={`inline-flex min-h-11 items-center justify-center rounded-md bg-emerald-300 px-3 text-sm font-semibold text-slate-950 shadow-sm transition-colors hover:bg-emerald-200 ${commandFocusClass}`}
                          onClick={handleApprovePreview}
                          type="button"
                        >
                          Approve
                        </button>
                      </>
                    ) : null}
                    {applyControlsVisible ? (
                      <>
                        <button
                          className={`inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-medium text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                          onClick={handleRejectPreview}
                          type="button"
                        >
                          Reject
                        </button>
                        <button
                          className={`inline-flex min-h-11 items-center justify-center rounded-md bg-emerald-300 px-3 text-sm font-semibold text-slate-950 shadow-sm transition-colors hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                          disabled={!canApplyApprovedDiff}
                          onClick={handleApplyApprovedDiff}
                          type="button"
                        >
                          {previewState.isApplying ? "Applying..." : "Apply approved diff"}
                        </button>
                      </>
                    ) : null}
                  </div>
                  {previewState.applySummary ? (
                    <p className={`mt-3 text-sm ${commandMutedClass}`}>{previewState.applySummary}</p>
                  ) : null}
                </div>

                <details className={`${commandInsetClass} mt-4 overflow-hidden`}>
                  <summary className={`min-h-12 cursor-pointer px-3 py-3 text-sm font-semibold ${commandTextClass} ${commandControlClass}`}>
                    Review gates
                  </summary>
                  <dl className="grid gap-3 border-t border-[var(--ddv4-surface-border-soft)] p-3 text-sm sm:grid-cols-2">
                    <GateStatus
                      label="Target match"
                      ok={previewState.targetMatch}
                      value={
                        previewState.targetMatch
                          ? "Diff targets the requested file."
                          : "Diff target has not matched yet."
                      }
                    />
                    <GateStatus
                      label="Allowed files"
                      ok={previewState.taskSpecAllowed}
                      value={
                        previewState.taskSpecAllowed
                          ? "Changed files are inside allowed files."
                          : "Allowed-files gate has not passed."
                      }
                    />
                    <GateStatus
                      label="Protected path"
                      ok={!previewState.blocker?.toLowerCase().includes("protected")}
                      value={previewState.blocker ?? "No protected-path blocker reported."}
                    />
                    <GateStatus
                      label="Requirement coverage"
                      ok={previewState.requirementSummary.toLowerCase().includes("passed")}
                      value={previewState.requirementSummary}
                    />
                    <GateStatus
                      label="Checks"
                      ok={previewState.verifierSummary.toLowerCase().includes("passed")}
                      value={previewState.verifierSummary}
                    />
                    <GateStatus
                      label="Review"
                      ok={!previewState.reviewerSummary.toLowerCase().includes("blocked")}
                      value={previewState.reviewerSummary}
                    />
                    <GateStatus
                      label="Apply"
                      ok={previewState.status === "applied"}
                      value={
                        previewState.status === "applied"
                          ? "Approved diff was applied."
                          : previewState.status === "approved"
                            ? "Ready to apply approved diff."
                            : "Locked until human approval is recorded."
                      }
                    />
                    <GateStatus
                      label="Verification"
                      ok={false}
                      value={
                        previewState.status === "applied"
                          ? "Verification required. Run checks before treating this task as done."
                          : "Runs after a separately approved apply flow."
                      }
                    />
                  </dl>
                </details>
              </section>
            ) : null}

          </section>
        </div>
          </div>

          <aside
            aria-label="Review pane"
            className={`${commandPanelClass} order-3 space-y-4 p-4 xl:sticky xl:top-6 xl:max-h-[calc(100dvh-3rem)] xl:overflow-auto`}
          >
            <div>
              <p className={commandLabelClass}>
                Review
              </p>
              <h2 className="mt-2 text-lg font-semibold text-[var(--ddv4-fg)]">Review pane</h2>
              <p className="mt-1 text-sm leading-6 text-[var(--ddv4-fg-muted)]">
                Diff, gates, and artifacts stay here while the task workspace remains focused.
              </p>
            </div>

            <dl className="space-y-3 text-sm">
              <div className={`${commandInsetClass} p-3`}>
                <dt className={commandLabelClass}>
                  Changed files
                </dt>
                <dd className={`mt-1 break-words ${commandTextClass}`}>
                  {previewState.changedFiles.length > 0
                    ? previewState.changedFiles.join(", ")
                    : "None reported"}
                </dd>
              </div>
              <div className={`${commandInsetClass} p-3`}>
                <dt className={commandLabelClass}>
                  Result
                </dt>
                <dd className={`mt-1 break-words ${commandTextClass}`}>{reviewPaneStatus}</dd>
              </div>
              <div className={`${commandInsetClass} p-3`}>
                <dt className={commandLabelClass}>
                  Checks
                </dt>
                <dd className={`mt-1 break-words ${commandTextClass}`}>{previewState.verifierSummary}</dd>
              </div>
              <div className={`${commandInsetClass} p-3`}>
                <dt className={commandLabelClass}>
                  Review
                </dt>
                <dd className={`mt-1 break-words ${commandTextClass}`}>{previewState.reviewerSummary}</dd>
              </div>
              <div className="rounded-md border border-[var(--spirit-accent)] bg-[var(--ddv4-pill-bg)] p-3">
                <dt className={commandLabelClass}>
                  Next safe move
                </dt>
                <dd className={`mt-1 ${commandTextClass}`}>
                  {previewState.status === "idle" && !draftReady
                    ? "Preview becomes available after Britton writes a task and starts discovery."
                    : nextSafeAction}
                </dd>
              </div>
            </dl>

            <Link
              className={`inline-flex min-h-11 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-medium text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
              href="/proxy-backend"
            >
              Diagnostics
            </Link>
          </aside>
        </div>
      </div>
      <div
        aria-label="Mobile action bar"
        className={`fixed inset-x-0 bottom-24 z-20 border-t border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-nav-bg)] px-4 pb-3 pt-3 shadow-2xl shadow-black/30 backdrop-blur lg:hidden ${
          showMobileActionBar ? "" : "hidden"
        }`}
        data-testid="mobile-action-bar"
      >
        <div className="mx-auto flex max-w-6xl items-center gap-3">
          <div className="min-w-0 flex-1">
            <div className="truncate text-xs font-semibold uppercase tracking-[0.14em] text-[var(--ddv4-fg-faint)]">
              {currentTaskState}
            </div>
            <div className="truncate text-sm font-medium text-[var(--ddv4-fg)]">
              {previewState.status === "applied"
                ? "Files applied. Verify next."
                : "No files changed"}
            </div>
          </div>
          <Link
            aria-label="Open mobile diagnostics"
            className={`inline-flex min-h-12 shrink-0 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-medium text-[var(--ddv4-fg)] ${commandFocusClass}`}
            href="/proxy-backend"
          >
            Diag
          </Link>
          {approvalControlsAvailable ? (
            <>
              <button
                className="inline-flex min-h-12 shrink-0 items-center justify-center rounded-md border border-white/15 px-3 text-sm font-medium text-slate-200"
                onClick={handleRejectPreview}
                type="button"
              >
                Reject
              </button>
              <button
                className="inline-flex min-h-12 shrink-0 items-center justify-center rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950"
                onClick={handleApprovePreview}
                type="button"
              >
                Approve
              </button>
            </>
          ) : applyControlsVisible ? (
            <>
              <button
                className="inline-flex min-h-12 shrink-0 items-center justify-center rounded-md border border-white/15 px-3 text-sm font-medium text-slate-200"
                onClick={handleRejectPreview}
                type="button"
              >
                Reject
              </button>
              <button
                className="inline-flex min-h-12 shrink-0 items-center justify-center rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950"
                disabled={!canApplyApprovedDiff}
                onClick={handleApplyApprovedDiff}
                type="button"
              >
                {previewState.isApplying ? "Applying" : "Apply"}
              </button>
            </>
          ) : (
            <button
              className={`inline-flex min-h-12 shrink-0 items-center justify-center gap-2 rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 ${
                canStartTask ? "" : "opacity-60"
              }`}
              disabled={!canStartTask || previewState.isLoading}
              onClick={handleDraftPreview}
              type="button"
            >
              <ShieldCheck aria-hidden="true" size={18} />
              {previewState.isLoading ? "Working" : "Start"}
            </button>
          )}
        </div>
      </div>
      </main>
      <DashboardDemoV4FloatingNav desktopVariant="full-height" />
    </div>
  );
}

export default CodingCockpitShell;

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

class BrowserAbortTimeoutError extends Error {
  timeoutLayer = "browser_abort_timeout" as const;

  constructor(message = "browser_abort_timeout") {
    super(message);
    this.name = "BrowserAbortTimeoutError";
  }
}

async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit = {}, timeoutMs = 8000) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new BrowserAbortTimeoutError();
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

function promptPacketEndpointStatusForError(error: unknown): "timeout" | "fetch_error" {
  return timeoutLayerFromError(error) === "network_fetch_error" ? "fetch_error" : "timeout";
}

function isTransientNetworkFetchError(error: unknown): boolean {
  if (error instanceof BrowserAbortTimeoutError) return false;
  const message = error instanceof Error ? error.message.toLowerCase() : String(error ?? "").toLowerCase();
  return message.includes("failed to fetch") || message.includes("networkerror") || message.includes("load failed");
}

async function waitForPromptPacketRetry(attempt: number) {
  await new Promise((resolve) => window.setTimeout(resolve, 350 * attempt));
}

async function fetchPromptPacketWithRetry(init: RequestInit, timeoutMs: number) {
  const maxAttempts = 3;
  let lastError: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      return await fetchWithTimeout("/v1/decisions/prompt-packet", init, timeoutMs);
    } catch (error) {
      lastError = error;
      if (!isTransientNetworkFetchError(error) || attempt === maxAttempts) {
        throw error;
      }
      await waitForPromptPacketRetry(attempt);
    }
  }
  throw lastError;
}

function timeoutLayerFromError(error: unknown): "browser_abort_timeout" | "source_proxy_timeout" | "long_running_task_timeout" | "ollama_provider_timeout" | "network_fetch_error" | "unknown_timeout" {
  if (error instanceof BrowserAbortTimeoutError) return error.timeoutLayer;
  const message = error instanceof Error ? error.message.toLowerCase() : String(error ?? "").toLowerCase();
  if (message.includes("browser_abort_timeout") || message.includes("aborterror")) return "browser_abort_timeout";
  if (message.includes("coder_sync_timeout") || message.includes("source_proxy_timeout")) return "source_proxy_timeout";
  if (message.includes("long_running")) return "long_running_task_timeout";
  if (message.includes("ollama") || message.includes("provider") || message.includes("litellm")) return "ollama_provider_timeout";
  if (isTransientNetworkFetchError(error)) return "network_fetch_error";
  return "unknown_timeout";
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function messageFromPayload(payload: unknown, status: number): string {
  const record = asRecord(payload);
  const detail = asRecord(record.detail);
  const message =
    stringValue(record.message) ??
    stringValue(record.error) ??
    stringValue(record.reason_code) ??
    stringValue(detail.error) ??
    stringValue(detail.reason_code) ??
    stringValue(record.status);
  return message ?? `Preview request returned status ${status}.`;
}

function safePayloadSummary(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return String(payload ?? "").slice(0, 400);
  }
  try {
    return JSON.stringify(payload).slice(0, 800);
  } catch {
    return "Response body could not be serialized.";
  }
}

function taskTextForPromptPacket(task: string, targetFile: string): string {
  const trimmedTask = task.trim();
  const targetLine = `Target file: ${targetFile}`;
  if (/(^|\n)\s*target\s+file\s*:/i.test(trimmedTask)) {
    return trimmedTask;
  }
  return `${targetLine}\n\n${trimmedTask}`;
}

function diffFromPayload(payload: unknown): string {
  const record = asRecord(payload);
  const nestedPacket = asRecord(record.prompt_packet ?? record.promptPacket);
  return (
    stringValue(record.proposed_diff) ??
    stringValue(record.proposedDiff) ??
    stringValue(nestedPacket.proposed_diff) ??
    stringValue(nestedPacket.proposedDiff) ??
    stringValue(record.unified_diff) ??
    stringValue(record.diff) ??
    ""
  );
}

function isCoderAlreadySatisfied(payload: unknown): boolean {
  const record = asRecord(payload);
  const reasonCode = stringValue(record.reason_code) ?? stringValue(record.reasonCode);
  const status = stringValue(record.status);
  return (
    record.already_satisfied === true ||
    record.alreadySatisfied === true ||
    reasonCode === "coder_no_changes_needed" ||
    status === "already_satisfied"
  );
}

function noDiffBlockerFromPayload(payload: unknown): string {
  const record = asRecord(payload);
  const reasonCode = stringValue(record.reason_code) ?? stringValue(record.reasonCode);
  if (reasonCode === "coder_response_repair_exhausted") {
    return "Coder response repair exhausted after repeated parser/schema failure. The live coder route returned an empty or invalid response, so no diff was produced.";
  }
  return (
    stringValue(record.blocked_reason) ??
    stringValue(record.blockedReason) ??
    stringValue(record.reason_code) ??
    stringValue(record.reasonCode) ??
    stringValue(record.message) ??
    messageFromPayload(payload, 200)
  );
}

function noDiffReasonCodeFromPayload(payload: unknown): string | null {
  const record = asRecord(payload);
  return stringValue(record.reason_code) ?? stringValue(record.reasonCode) ?? null;
}

function reasonCodeFromPreview(payload: unknown): string | null {
  const record = asRecord(payload);
  const taskSpecCheck = asRecord(record.task_spec_check);
  const blockedReasons = record.blocked_reasons;
  if (Array.isArray(blockedReasons)) {
    const first = blockedReasons
      .map((item) => stringValue(asRecord(item).reason_code))
      .find(Boolean);
    if (first) return first;
  }
  const reasonCodes = taskSpecCheck.reason_codes;
  if (Array.isArray(reasonCodes)) {
    const first = reasonCodes.map((item) => (typeof item === "string" ? item : "")).find(Boolean);
    if (first) return first;
  }
  return stringValue(record.reason_code) ?? null;
}

function reasonCodeFromErrorMessage(message: string): string {
  const match = message.match(/\b([a-z][a-z0-9_]*_[a-z0-9_]+)\b/i);
  return match?.[1] ?? "manual_preview_failed";
}

function coderSummaryFromPayload(payload: unknown, fallback: string): string {
  const record = asRecord(payload);
  const reasonCode = stringValue(record.reason_code) ?? stringValue(record.reasonCode);
  if (stringValue(record.blocked_reason) ?? stringValue(record.blockedReason)) {
    return stringValue(record.blocked_reason) ?? stringValue(record.blockedReason) ?? fallback;
  }
  if (reasonCode === "coder_model_not_configured" || reasonCode === "local_model_unavailable") {
    return "Task service unavailable. Open diagnostics for setup details.";
  }
  if (reasonCode === "coder_sync_timeout") {
    return "Coder timed out before returning a diff. Narrow scope or raise the sync deadline.";
  }
  if (reasonCode === "coder_response_repair_exhausted") {
    return "Live coder returned an empty or invalid response after repair attempts. No preview diff was produced.";
  }
  if (reasonCode === "coder_no_changes_needed") {
    return "Target already satisfies this task. No diff to approve or apply.";
  }
  return reasonCode ? `No diff returned (${reasonCode}).` : fallback;
}

function changedFilesFromPayload(payload: unknown): string[] {
  const record = asRecord(payload);
  const changed =
    Array.isArray(record.applied_changed_files)
      ? record.applied_changed_files
      : Array.isArray(record.disk_changed_files)
        ? record.disk_changed_files
        : record.changed_files;
  if (!Array.isArray(changed)) {
    return [];
  }
  return changed
    .map((item) => {
      if (typeof item === "string") {
        return normalizeRepoPath(item);
      }
      return normalizeRepoPath(stringValue(asRecord(item).path) ?? "");
    })
    .filter(Boolean);
}

function changedFilesFromApplyPayloadOrDiff(payload: unknown, approvedDiff: string): string[] {
  const fromPayload = changedFilesFromPayload(payload);
  return fromPayload.length > 0 ? fromPayload : changedFilesFromDiffPreview(approvedDiff);
}

type ChangedFileSnapshot = {
  missingBeforeApply: boolean;
  path: string;
  sha256After: string | null;
  sha256Before: string | null;
};

function changedFileSnapshotsFromPayload(payload: unknown): ChangedFileSnapshot[] {
  const record = asRecord(payload);
  const execution = asRecord(record.execution);
  const candidates = [
    record.changed_file_snapshots,
    record.changedFileSnapshots,
    execution.changed_file_snapshots,
    execution.changedFileSnapshots,
  ];
  const snapshots = candidates.find(Array.isArray);
  if (!Array.isArray(snapshots)) return [];
  return snapshots
    .map((item) => {
      const snapshot = asRecord(item);
      const path = normalizeRepoPath(stringValue(snapshot.path) ?? "");
      if (!path) return null;
      return {
        missingBeforeApply: snapshot.missing_before_apply === true || snapshot.missingBeforeApply === true,
        path,
        sha256After: stringValue(snapshot.sha256_after) ?? stringValue(snapshot.sha256After) ?? null,
        sha256Before: stringValue(snapshot.sha256_before) ?? stringValue(snapshot.sha256Before) ?? null,
      };
    })
    .filter((item): item is ChangedFileSnapshot => item !== null);
}

function snapshotForPath(snapshots: ChangedFileSnapshot[], path: string): ChangedFileSnapshot | undefined {
  const normalized = normalizeRepoPath(path);
  return snapshots.find((snapshot) => snapshot.path === normalized);
}

function snapshotHasBefore(snapshots: ChangedFileSnapshot[], path: string): boolean {
  const snapshot = snapshotForPath(snapshots, path);
  return Boolean(snapshot && !snapshot.missingBeforeApply && snapshot.sha256Before);
}

function snapshotRestored(
  applySnapshots: ChangedFileSnapshot[],
  revertSnapshots: ChangedFileSnapshot[],
  path: string,
): boolean {
  const applySnapshot = snapshotForPath(applySnapshots, path);
  const revertSnapshot = snapshotForPath(revertSnapshots, path);
  return Boolean(
    applySnapshot?.sha256Before &&
      revertSnapshot?.sha256After &&
      applySnapshot.sha256Before === revertSnapshot.sha256After,
  );
}

function uniqueNormalizedFiles(files: string[]): string[] {
  return Array.from(new Set(files.map((file) => normalizeRepoPath(file)).filter(Boolean)));
}

function buildApplyScopePreflight(previewState: PreviewState): ApplyScopePreflight {
  const changedFiles = uniqueNormalizedFiles(previewState.changedFiles);
  const stateAllowedFiles = uniqueNormalizedFiles(previewState.allowedFiles);
  const selectedTarget = normalizeRepoPath(previewState.selectedTarget ?? "");
  const targetOnlyFallbackAllowed =
    stateAllowedFiles.length === 0 &&
    selectedTarget &&
    changedFiles.length === 1 &&
    changedFiles[0] === selectedTarget
      ? [selectedTarget]
      : [];
  const allowedFiles = stateAllowedFiles.length > 0 ? stateAllowedFiles : targetOnlyFallbackAllowed;

  if (changedFiles.length === 0) {
    return {
      allowedFiles,
      allChangedFilesAllowed: false,
      changedFiles,
      reason: "Apply blocked because no changed_files were recorded for the approved preview.",
      reasonCode: "missing_changed_files",
    };
  }
  if (allowedFiles.length === 0) {
    return {
      allowedFiles,
      allChangedFilesAllowed: false,
      changedFiles,
      reason: "Apply blocked because allowed_files could not be resolved for Source Proxy scope matching.",
      reasonCode: "missing_allowed_files",
    };
  }
  const allChangedFilesAllowed = changedFiles.every((file) => allowedFiles.includes(file));
  if (!allChangedFilesAllowed) {
    return {
      allowedFiles,
      allChangedFilesAllowed,
      changedFiles,
      reason: "Apply blocked because changed_files are not fully contained in allowed_files.",
      reasonCode: "changed_files_outside_allowed_files",
    };
  }
  return {
    allowedFiles,
    allChangedFilesAllowed,
    changedFiles,
    reason: null,
    reasonCode: null,
  };
}

function statusFromPayload(payload: unknown): string {
  return stringValue(asRecord(payload).status) ?? "";
}

function taskIdFromPayload(payload: unknown): string {
  const record = asRecord(payload);
  return (
    stringValue(record.task_id) ??
    stringValue(record.taskId) ??
    stringValue(asRecord(record.task).id) ??
    stringValue(asRecord(asRecord(record.data).task).id) ??
    ""
  );
}

function blockerFromPayload(payload: unknown): string {
  const record = asRecord(payload);
  const blockedReasons = record.blocked_reasons;
  if (Array.isArray(blockedReasons) && blockedReasons.length > 0) {
    return blockedReasons
      .map((item) => {
        const reason = asRecord(item);
        return [stringValue(reason.path), stringValue(reason.reason_code)]
          .filter(Boolean)
          .join(": ");
      })
      .filter(Boolean)
      .join(", ");
  }
  return messageFromPayload(payload, 200);
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function GateStatus({
  label,
  ok,
  value,
}: {
  label: string;
  ok: boolean;
  value: string;
}) {
  return (
    <div
      className={`rounded-md border p-3 ${
        ok
          ? "border-emerald-300/30 bg-emerald-300/10 text-emerald-100"
          : "border-amber-300/30 bg-amber-300/10 text-amber-100"
      }`}
    >
      <dt className="text-xs font-semibold uppercase tracking-[0.14em] opacity-80">{label}</dt>
      <dd className="mt-1 break-words">{value}</dd>
    </div>
  );
}

function VisibleResultBadgeRow({ result }: { result: VisibleResultBadge }) {
  return (
    <div className="flex flex-wrap items-center gap-2" aria-label="Visible result">
      <span
        className={`inline-flex min-h-8 items-center rounded-md border px-2.5 text-xs font-semibold uppercase ${visibleResultChipClass(result.primary_tone)}`}
      >
        {result.primary_label}: {result.plain_summary}
      </span>
      {result.secondary_badges.map((badge) => (
        <span
          className={`inline-flex min-h-8 items-center rounded-md border px-2.5 text-xs font-semibold uppercase ${visibleResultChipClass(badge.tone)}`}
          key={`${badge.label}-${badge.tone}`}
        >
          {badge.label}
        </span>
      ))}
    </div>
  );
}

function visibleResultChipClass(tone: VisibleResultTone) {
  if (tone === "success") return "border-emerald-300/40 bg-emerald-300/10 text-emerald-50";
  if (tone === "warning") return "border-amber-300/40 bg-amber-300/10 text-amber-50";
  if (tone === "danger") return "border-red-300/40 bg-red-300/10 text-red-50";
  return "border-slate-300/30 bg-slate-300/10 text-slate-50";
}

type TrialResultSummary = ReturnType<typeof summarizeTrialResult>;

function summarizeTrialResult(previews: AgentTrialPromptPreview[]) {
  const liveApplyProofCount = previews.filter((preview) => preview.visibleResult.score_counts_as_live_usefulness).length;
  const previewOnlyCount = previews.filter((preview) => preview.trialMode === "preview_only").length;
  const productiveUsefulCount = previews.filter((preview) =>
    preview.actualIntelligence.category === "pass_productive" ||
    preview.actualIntelligence.category === "pass_productive_with_warning",
  ).length;
  const expectedSafeBlockCount = previews.filter((preview) => preview.actualIntelligence.countsForSafety).length;
  const clarificationNeededCount = previews.filter((preview) => outcomeCategoryForPreview(preview) === "clarification_needed").length;
  const noOpHonestCount = previews.filter(
    (preview) => preview.actualIntelligence.category === "already_satisfied_noop_useful",
  ).length;
  const falseBlockCount = previews.filter((preview) => preview.simpleResult === "False block").length;
  const failedOnlyCount = previews.filter((preview) => preview.simpleResult === "Failed").length;
  const missingDiagnosticsCount = previews.filter(
    (preview) => ["Blocked safely", "False block", "Failed"].includes(preview.simpleResult) && !preview.copyPasteBlock,
  ).length;
  const notClassifiedCount = previews.filter((preview) => outcomeCategoryForPreview(preview) === "not_classified").length;
  const needsReviewCount = falseBlockCount + failedOnlyCount + missingDiagnosticsCount + notClassifiedCount;
  const classifiedCount =
    productiveUsefulCount +
    expectedSafeBlockCount +
    clarificationNeededCount +
    noOpHonestCount +
    falseBlockCount +
    failedOnlyCount +
    missingDiagnosticsCount +
    notClassifiedCount;
  const usefulCount = productiveUsefulCount + noOpHonestCount;
  return {
    clarificationNeededCount,
    countsSumMatchesSize: classifiedCount === previews.length,
    expectedSafeBlockCount,
    failedOnlyCount,
    falseBlockCount,
    headline: liveApplyProofCount > 0
      ? `Live apply proof: ${liveApplyProofCount}/${previews.length}`
      : previewOnlyCount > 0
        ? "Preview-only diagnostic run. 0 live apply proof."
        : `${usefulCount} diagnostic useful, ${expectedSafeBlockCount} safety-only blocks, ${needsReviewCount} needs review, ${failedOnlyCount} failed`,
    hiddenMutationDetectedCount: 0,
    missingDiagnosticsCount,
    needsReviewCount,
    noOpHonestCount,
    notClassifiedCount,
    productiveUsefulCount,
    score: liveApplyProofCount > 0
      ? `Live apply proof: ${liveApplyProofCount}/${previews.length}`
      : "0/100 live apply proof",
    stuckCount: 0,
    totalPrompts: previews.length,
    usefulCount,
  };
}

function outcomeCategoryForPreview(preview: AgentTrialPromptPreview) {
  if (preview.actualIntelligence.category === "blocked_safety") return "blocked_safety";
  if (preview.actualIntelligence.category === "already_satisfied_noop_useful") return "already_satisfied_noop_useful";
  if (preview.actualIntelligence.category === "pass_productive") return "pass_productive";
  if (preview.actualIntelligence.category === "pass_productive_with_warning") return "pass_productive_with_warning";
  if (preview.simpleResult === "Preview diff produced") return "useful";
  if (preview.simpleResult === "Blocked safely") return "expected_safe_block";
  if (preview.simpleResult === "Asked useful clarification") return "clarification_needed";
  if (preview.simpleResult === "Already satisfied") return "no_op_honest";
  if (preview.simpleResult === "False block") return "false_block";
  if (preview.simpleResult === "Failed") return "failed";
  return "not_classified";
}

function formatList(items: string[], fallback = "not recorded") {
  return items.length > 0 ? items.join(", ") : fallback;
}

function formatNullable(value: string | null | undefined) {
  return value && value.trim() ? value : "not recorded";
}

function isTrialAttentionItem(preview: AgentTrialPromptPreview) {
  const outcome = outcomeCategoryForPreview(preview);
  return (
    outcome === "false_block" ||
    outcome === "failed" ||
    outcome === "not_classified" ||
    !preview.submittedPrompt ||
    preview.promptPreviewMatchesSubmittedPrompt === false ||
    (["Blocked safely", "False block", "Failed"].includes(preview.simpleResult) && !preview.copyPasteBlock)
  );
}

function buildTrialPromptsOnlyText({
  bankLabel,
  modeLabel,
  previews,
  runId,
  runSize,
  viewport,
}: {
  bankLabel: string;
  modeLabel: string;
  previews: AgentTrialPromptPreview[];
  runId: string;
  runSize: number;
  viewport: AgentTrialViewport;
}) {
  return [
    "SpiritOS manual retest prompts",
    `bank: ${bankLabel}`,
    `scenario: ${modeLabel} ${runSize}-prompt ${viewport} trial`,
    `run_id: ${runId}`,
    "",
    previews
      .map((preview, index) => [`Prompt ${index + 1}: ${preview.fixtureId}`, preview.submittedPrompt || "not recorded"].join("\n"))
      .join("\n\n"),
  ].join("\n");
}

function buildFullTrialDiagnosticReport({
  bankLabel,
  bankMode,
  liveUsefulnessEligible,
  liveUsefulnessReason,
  modeLabel,
  previews,
  providerTruth,
  runId,
  runSize,
  score,
  status,
  summary,
  viewport,
}: {
  bankLabel: string;
  bankMode: string;
  liveUsefulnessEligible: boolean;
  liveUsefulnessReason: string;
  modeLabel: string;
  previews: AgentTrialPromptPreview[];
  providerTruth: CodingProviderModelTruth;
  runId: string;
  runSize: number;
  score: string;
  status: string;
  summary: TrialResultSummary;
  viewport: AgentTrialViewport;
}) {
  const attentionItems = previews.filter(isTrialAttentionItem);
  const nextAction =
    attentionItems[0]
      ? `Manually retest ${attentionItems[0].fixtureId} first, then continue through the remaining attention prompts.`
      : "No attention items were found; manually spot-check the prompts-only packet if confidence is needed.";
  const visibleResult = mapVisibleResultBadge({
    actual_intelligence_category:
      summary.failedOnlyCount > 0
        ? "failed_quality"
        : summary.needsReviewCount > 0 || !liveUsefulnessEligible
          ? "pass_productive_with_warning"
          : "pass_productive",
    counts_for_live_usefulness: liveUsefulnessEligible,
    disqualifies_live_claim: !liveUsefulnessEligible,
    hermes_used_for_this_run: providerTruth.hermesUsedForRunStatus,
    model_called_for_generation: providerTruth.modelCalledForGeneration ?? "none",
    next_recommended_action: nextAction,
    provider_call_made: providerTruth.providerCallMade,
    result_category:
      summary.failedOnlyCount > 0
        ? "failed_verification"
        : summary.needsReviewCount > 0
          ? "pass_productive_with_warning"
          : "pass_productive",
    status,
    s_plus_eligible: liveUsefulnessEligible,
  });

  return [
    "SpiritOS trial diagnostic report",
    `bank: ${bankLabel}`,
    `bank_mode: ${bankMode}`,
    bankMode === "legacy-fixture-smoke"
      ? "Legacy fixture smoke only. Does not count for live coding usefulness or S+."
      : "Live Apply Bank selected. Preview diagnostics remain 0 live proof until model call, apply, disk verification, checks, and reversal are recorded.",
    `visible_result_label: ${visibleResult.primary_label}`,
    `visible_result_tone: ${visibleResult.primary_tone}`,
    `visible_result_summary: ${visibleResult.plain_summary}`,
    `live_model_proof_status: ${visibleResult.live_model_proof_status}`,
    `counts_for_live_usefulness: ${liveUsefulnessEligible}`,
    `s_plus_eligible: ${liveUsefulnessEligible}`,
    `s_plus_reason: ${liveUsefulnessReason}`,
    "",
    "model_truth:",
    `configured_model: ${providerTruth.configuredModel}`,
    `runtime_route_model: ${providerTruth.runtimeRouteModel}`,
    `provider: ${providerTruth.providerLabel}`,
    `model: ${providerTruth.modelLabel}`,
    `provider_model_source: ${providerTruth.source}`,
    `provider_model_status: ${providerTruth.status}`,
    `provider_model_probe_ok: ${
      providerTruth.providerModelProbeOk === null || providerTruth.providerModelProbeOk === undefined
        ? "unknown"
        : providerTruth.providerModelProbeOk
    }`,
    `provider_model_selected_via: ${providerTruth.providerModelSelectedVia ?? "unknown"}`,
    `provider_call_made: ${providerTruth.providerCallMade}`,
    `model_called_for_generation: ${providerTruth.modelCalledForGeneration ?? "none"}`,
    `configured_local_model_is_hermes: ${
      providerTruth.configuredModelIsHermes === null
        ? "unknown"
        : providerTruth.configuredModelIsHermes
          ? "yes"
          : "no"
    }`,
    `hermes_used_for_this_run: ${providerTruth.hermesUsedForRunStatus}`,
    "",
    "run:",
    `scenario: ${modeLabel} ${runSize}-prompt ${viewport} trial`,
    `mode: ${modeLabel}`,
    `size: ${runSize}`,
    `viewport: ${viewport}`,
    `status: ${status}`,
    `score: ${score}`,
    "started_at: not recorded",
    "finished_at: not recorded",
    `run_id: ${runId}`,
    "",
    "summary:",
    `total_prompts: ${summary.totalPrompts}`,
    `useful: ${summary.usefulCount}`,
    `blocked_safety_safety_only: ${summary.expectedSafeBlockCount}`,
    `clarification_needed: ${summary.clarificationNeededCount}`,
    `no_op_honest: ${summary.noOpHonestCount}`,
    `false_block: ${summary.falseBlockCount}`,
    `stuck: ${summary.stuckCount}`,
    `failed: ${summary.failedOnlyCount}`,
    `missing_diagnostics: ${summary.missingDiagnosticsCount}`,
    `hidden_mutation_detected: ${summary.hiddenMutationDetectedCount}`,
    `counts_sum_matches_size: ${summary.countsSumMatchesSize}`,
    "",
    "prompt_results:",
    previews.map(formatPromptDiagnostic).join("\n\n"),
    "",
    "attention_items:",
    attentionItems.length > 0 ? attentionItems.map(formatAttentionItem).join("\n") : "none",
    "",
    "manual_retest_prompts:",
    previews
      .map((preview, index) => [`Prompt ${index + 1}: ${preview.fixtureId}`, preview.submittedPrompt || "not recorded"].join("\n"))
      .join("\n\n"),
    "",
    "next_action:",
    nextAction,
  ].join("\n");
}

function buildTrialAttentionOnlyText({
  bankLabel,
  modeLabel,
  previews,
  runId,
  runSize,
  viewport,
}: {
  bankLabel: string;
  modeLabel: string;
  previews: AgentTrialPromptPreview[];
  runId: string;
  runSize: number;
  viewport: AgentTrialViewport;
}) {
  const attentionItems = previews.filter(isTrialAttentionItem);
  if (attentionItems.length === 0) {
    return [
      "SpiritOS trial attention report",
      `bank: ${bankLabel}`,
      `scenario: ${modeLabel} ${runSize}-prompt ${viewport} trial`,
      `run_id: ${runId}`,
      "attention_items: none",
    ].join("\n");
  }

  return [
    "SpiritOS trial attention report",
    `bank: ${bankLabel}`,
    `scenario: ${modeLabel} ${runSize}-prompt ${viewport} trial`,
    `run_id: ${runId}`,
    "",
    attentionItems.map(formatPromptDiagnostic).join("\n\n"),
  ].join("\n");
}

function formatPromptDiagnostic(preview: AgentTrialPromptPreview, index?: number) {
  const prefix = typeof index === "number" ? `${index + 1}.` : `${preview.fixtureId}.`;
  const previewChangedFiles = changedFilesForTrialPreview(preview);
  const changedFilesDiagnostics = buildChangedFilesDiagnostics({
    diff: previewChangedFiles.length > 0 ? `diff --git a/${previewChangedFiles[0]} b/${previewChangedFiles[0]}` : "",
    status: preview.actualBehavior,
    verificationChangedFiles: previewChangedFiles,
  });
  const evidenceFiles = evidenceFilesForTrialPreview(preview);

  return [
    `${prefix} fixture_id: ${preview.fixtureId}`,
    `   submitted_prompt: ${preview.submittedPrompt || "not recorded"}`,
    `   expected_behavior: ${preview.expectedBehavior}`,
    `   actual_behavior: ${preview.actualBehavior}`,
    `   status: ${preview.expectedStatus}`,
    `   result_category: ${outcomeCategoryForPreview(preview)}`,
    `   actual_intelligence_category: ${preview.actualIntelligence.category}`,
    `   visible_result_label: ${preview.visibleResult.primary_label}`,
    `   visible_result_tone: ${preview.visibleResult.primary_tone}`,
    `   visible_result_summary: ${preview.visibleResult.plain_summary}`,
    `   live_model_proof_status: ${preview.visibleResult.live_model_proof_status}`,
    `   live_apply_proof_status: ${preview.visibleResult.live_apply_proof_status}`,
    `   trial_mode: ${preview.trialMode}`,
    `   counts_for_coding_usefulness: ${preview.actualIntelligence.countsForCodingUsefulness}`,
    `   score_counts_as_live_usefulness: ${preview.visibleResult.score_counts_as_live_usefulness}`,
    `   counts_for_safety_only: ${preview.actualIntelligence.countsForSafety}`,
    `   disqualifies_live_claim: ${preview.actualIntelligence.disqualifiesLiveClaim}`,
    `   reason_code: ${preview.reason}`,
    `   missing_fields: ${formatList(preview.missingFields, "none")}`,
    `   target_file: ${preview.selectedFiles[0] ?? "not recorded"}`,
    `   target_candidates: ${formatList(preview.candidateFiles)}`,
    `   allowed_files: ${formatList(preview.allowedFiles)}`,
    `   forbidden_files: ${formatList(preview.forbiddenFiles)}`,
    `   route_or_endpoint: ${preview.routeOrEndpoint}`,
    `   provider: ${formatNullable(preview.provider)}`,
    `   model: ${formatNullable(preview.model)}`,
    `   provider_call_made: ${preview.providerCallMade}`,
    `   model_called_for_generation: ${preview.modelCalledForGeneration ?? "none"}`,
    `   hermes_used_for_this_run: ${preview.hermesUsedForThisRun}`,
    `   qwen_coder_used_for_this_run: ${preview.qwenCoderUsedForThisRun}`,
    `   safety_state: ${preview.safetyState}`,
    `   preview_changed_files: ${formatList(changedFilesDiagnostics.previewChangedFiles, "none")}`,
    `   disk_changed_files: ${formatList(changedFilesDiagnostics.diskChangedFiles, "none")}`,
    `   applied_changed_files: ${formatList(changedFilesDiagnostics.appliedChangedFiles, "none")}`,
    `   changed_files: ${formatList(changedFilesDiagnostics.changedFiles, "none")}`,
    `   evidence_files: ${formatList(evidenceFiles, "none")}`,
    `   checks: ${formatList(preview.recommendedChecks, "not recorded")}`,
    `   checks_run: ${formatList(preview.checksRun, "not recorded")}`,
    `   checks_passed: not_attempted`,
    `   reversal_available: ${preview.reversalAvailable}`,
    `   reverted_at: ${preview.revertedAt ?? "not reverted"}`,
    `   counts_for_live_usefulness: ${preview.visibleResult.score_counts_as_live_usefulness}`,
    `   s_plus_eligible: ${preview.actualIntelligence.sPlusEligible}`,
    `   artifact_paths: ${formatList(preview.artifactPaths)}`,
    `   screenshot_paths: ${formatList(preview.screenshotPaths)}`,
    `   trace_path: ${formatNullable(preview.tracePath)}`,
    `   next_recommended_action: ${isTrialAttentionItem(preview) ? "Manually retest this prompt in /coding." : "No attention flag; retest if needed."}`,
    `   copy_paste_block: ${preview.copyPasteBlock || "not recorded"}`,
  ].join("\n");
}

function changedFilesForTrialPreview(preview: AgentTrialPromptPreview) {
  if (!preview.previewDiffProduced) return [];
  if (outcomeCategoryForPreview(preview) === "already_satisfied_noop_useful") return [];
  return preview.selectedFiles;
}

function evidenceFilesForTrialPreview(preview: AgentTrialPromptPreview) {
  if (outcomeCategoryForPreview(preview) !== "already_satisfied_noop_useful") return [];
  return preview.selectedFiles.length > 0 ? preview.selectedFiles : preview.candidateFiles;
}

function formatAttentionItem(preview: AgentTrialPromptPreview) {
  const reasons = [
    outcomeCategoryForPreview(preview) === "false_block" ? "false_block" : "",
    outcomeCategoryForPreview(preview) === "failed" ? "failed" : "",
    !preview.submittedPrompt ? "missing submitted_prompt" : "",
    preview.promptPreviewMatchesSubmittedPrompt === false ? "prompt preview mismatch" : "",
    ["Blocked safely", "False block", "Failed"].includes(preview.simpleResult) && !preview.copyPasteBlock
      ? "missing diagnostic"
      : "",
  ].filter(Boolean);
  return `- ${preview.fixtureId}: ${reasons.join(", ") || "attention"}`;
}

function approvalGateFromPreview(
  payload: unknown,
  target: string,
  allowedFiles: string[],
): Pick<
  PreviewState,
  | "approvalAvailable"
  | "requirementSummary"
  | "reviewerSummary"
  | "targetMatch"
  | "taskSpecAllowed"
  | "verifierSummary"
> {
  const record = asRecord(payload);
  const changedFiles = changedFilesFromPayload(payload);
  const taskSpecCheck = asRecord(record.task_spec_check);
  const requirementCoverage = asRecord(record.requirement_coverage);
  const reviewReport = asRecord(record.review_report);
  const llmReviewReport = asRecord(record.llm_review_report);
  const targetMatch = changedFiles.length > 0 && changedFiles.every((file) => file === target);
  const taskSpecAllowed =
    taskSpecCheck.ok === true ||
    (changedFiles.length > 0 && changedFiles.every((file) => allowedFiles.includes(file)));
  const gitApplyPassed = record.git_apply_check_ok === true;
  const requirementPassed = requirementCoverage.ok === true;
  const reviewerBlocked =
    reviewReport.passed === false || llmReviewReport.passed === false;
  return {
    approvalAvailable:
      statusFromPayload(payload) !== "blocked" &&
      targetMatch &&
      taskSpecAllowed &&
      gitApplyPassed &&
      requirementPassed &&
      !reviewerBlocked,
    requirementSummary: requirementPassed
      ? "Requirement coverage passed."
      : stringValue(requirementCoverage.summary) ?? "Requirement coverage not confirmed.",
    reviewerSummary: reviewerBlocked
      ? "Review blocked this preview."
      : reviewReport.passed === true || llmReviewReport.passed === true
        ? "Review passed."
        : "Review unavailable or advisory.",
    targetMatch,
    taskSpecAllowed,
    verifierSummary: gitApplyPassed
      ? "Checks passed."
      : stringValue(record.git_apply_check_error) ?? "Checks have not passed yet.",
  };
}
