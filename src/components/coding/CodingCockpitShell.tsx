"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Copy, ExternalLink, FileText, Plus, ShieldCheck } from "lucide-react";

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
  allUnrevertedSuiteResultsInReversePromptOrder,
  buildDeleteFileReverseDiff,
  isCoderTrialCleanupPath,
  isAgentLabTrialPath,
  isDummyProductSiteTrialPath,
  pathIsAllowedForTrialReverse,
  uniqueAgentLabTargetsFromResults,
} from "@/lib/coding/agent-lab-cleanup";
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
  codingTargetPlugin,
  type TargetPluginGradingResult,
  type TargetPluginPrompt,
  type TargetPluginStorefrontProbeResult,
} from "@/lib/coding/target-plugins";
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
import type {
  DurableCodingRun,
  DurableCodingRunProvenance,
  DurableCodingRunRow,
  DurableCodingRunStatus,
} from "@/lib/coding/durable-run-types";
import {
  buildTrialPromptQuickLinks,
  classifyNoDiffModelResponse,
  classifyCurrentSuiteAgentLabFiles,
  classifyEditReversibleAlreadySatisfied,
  downgradePassWithoutReversalProof,
  betweenPromptsStaleSummary,
  durableRunHasStaleBetweenPromptsGap,
  durableRunHasStalePostApplyVerification,
  formatAgentLabBaselineDiagnostics,
  mergeStepInstrumentation,
  postApplyStaleNextAction,
  postApplyStaleReasonCode,
  trialRunnerRunBlocked,
  type AgentLabBaselineSnapshot,
  type TrialApplyStepInstrumentation,
} from "@/lib/coding/reversible-trial-runner";
import {
  buildRouteUnavailableDiagnostic,
  extractReasonCodeFromSummary,
  isRouteInfraUnavailableSummary,
  readApiResponse,
  type RouteAvailabilityFailure,
  waitForV1RoutesAfterHmr,
} from "@/lib/coding/route-availability";
import {
  activeCodingApiRouteSequence,
  codingApiRoutesByStatus,
} from "@/lib/coding/shell-registry";

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
const idleDesignStudioComposerState = (): DesignStudioComposerState => ({
  endpointStatus: null,
  error: null,
  isLoading: false,
  outcome: null,
  reason: null,
  requestId: null,
  status: "idle",
  traceId: null,
});
type PreviewState = {
  approvalAvailable: boolean;
  approvedAt: string | null;
  appliedAt: string | null;
  applySummary: string;
  allowedFiles: string[];
  blocker: string | null;
  changedFiles: string[];
  checks: string[];
  causalStatusAfter?: string | null;
  currentPhase: string;
  diff: string;
  error: string | null;
  events: ManualTaskEvent[];
  forbiddenFiles: string[];
  isApplying: boolean;
  isLoading: boolean;
  model: string | null;
  outputHash?: string | null;
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
  plan2SubsystemIntegrations?: Plan2SubsystemIntegration[];
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
  traceId?: string | null;
  invocationEventId?: string | null;
  consumerEventId?: string | null;
  consumerSubsystem?: string | null;
  verifierSummary: string;
  technicalDetail?: string | null;
};

type ComposerMode = "coding" | "design_studio";

type DesignStudioComposerState = {
  endpointStatus: string | null;
  error: string | null;
  isLoading: boolean;
  outcome: string | null;
  reason: string | null;
  requestId: string | null;
  status: "idle" | "running" | "ready" | "blocked" | "error";
  traceId: string | null;
};

type Plan2SubsystemIntegration = {
  subsystem: string;
  status: string;
  outputHash: string | null;
  traceId: string | null;
  invocationEventId: string | null;
  consumerEventId: string | null;
  consumedBy: string | null;
};

type TrialRunState = "idle" | "running" | "complete";
type TrialRunnerMode = "individual" | "benchmark";
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
  provenance: DurableCodingRunProvenance;
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
    | "RUNNING"
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
  baselineCheckedAt: string | null;
  baselineAgentLabFiles: string[];
  baselineDirtyAgentLabFiles: string[];
  baselineUnrevertedReceipts: string[];
  baselineCleanForFreshSuite: boolean | null;
};
type ReversibleSuiteAbort = {
  reason: string;
  source: Extract<ReversibleSuiteState["interruptionSource"], "route_failed" | "provider_timeout">;
  step: string;
};
type DummyCoder10RunState = {
  status: "idle" | "starting" | "request_sent" | "running" | "complete" | "blocked" | "applied" | "cleared" | "error" | "timeout";
  selectedPromptId: string | null;
  taskId: string | null;
  message: string;
  errorText: string | null;
  rawBackendStatus: string | null;
  changedFiles: string[];
  checksRun: string[];
  verificationStatus: string | null;
  generationSource: string | null;
  diffSource: string | null;
  backend_anti_cheat_status: string | null;
  backend_anti_cheat_hard_fail_ids: string[];
  backend_anti_cheat_advisory_ids: string[];
  backend_anti_cheat_report: string | null;
  backend_anti_cheat_reasons: string[];
  modelOutputClassification: string | null;
  noDiffFailureCause: string | null;
  parserExtractorDecision: string | null;
  trialResultTrustStatus: string | null;
  scaffoldUsed: boolean | null;
  fallbackUsed: boolean | null;
  generatedDiffByBackend: boolean | null;
  // Apply provenance surfaced from /v1/actions/execute-approved so recovery
  // (backend-authored fixture rewrite after git apply --check failure) is
  // visible in diagnostics and cannot be hidden behind upstream labels.
  applyMode: string | null;
  stalePatchRecovered: boolean | null;
  rawModelResponseSha256: string | null;
  modelFileBundleSha256: string | null;
  backendConvertedDiffSha256: string | null;
  structuredBundleStatus: string | null;
  structuredBundleParserStage: string | null;
  structuredBundleFileCount: number | null;
  structuredBundleAcceptedPaths: string[];
  structuredBundleRejectedPaths: string[];
  structuredBundleRejectionReason: string | null;
  modelOutputShapeSummary: string | null;
  diffGenerationStatus: string | null;
  diffGenerationReason: string | null;
  diffFileCount: number | null;
  diffAddedPaths: string[];
  diffSkippedPaths: string[];
  diffSkippedReasons: string[];
  diffFilesystemSnapshotSummary: string[];
  patchVerificationStatus: string | null;
  patchVerificationReason: string | null;
  taskCreationStatus: string | null;
  taskCreationElapsedMs: number | null;
  taskCreationTimeoutStage: string | null;
  taskCreationLastCheckpoint: string | null;
  taskCreationBlockingSubsystem: string | null;
  approvedDiffSha256: string | null;
  appliedDiffSha256: string | null;
  backupManifest?: string | null;
  postApplyRediffSha256: string | null;
  provenanceHashNormalization: string | null;
  recommendedNextAction: string | null;
  lastFailureDiagnostics: Record<string, unknown> | null;
  grader: TargetPluginGradingResult | null;
  packet: unknown | null;
  // Wall-clock production timing for the diagnostics report. startedAt is captured when the run
  // begins (status -> starting); finishedAt when it reaches a terminal applied/complete/error state.
  startedAt: number | null;
  finishedAt: number | null;
  // Storefront render probe result (coder-001 only). Null on other prompts or when the fixture
  // contents could not be read. Surfaces whether the page renders real storefront content.
  storefrontProbe: TargetPluginStorefrontProbeResult | null;
  canonicalContextVerdict: string | null;
  canonicalContextReportHash: string | null;
  canonicalContextBlockers: string[];
  canonicalContextAcknowledgements: string[];
};

export type SelectedPromptAuditDiagnosticsState = Pick<
  DummyCoder10RunState,
  | "appliedDiffSha256"
  | "applyMode"
  | "approvedDiffSha256"
  | "backupManifest"
  | "backendConvertedDiffSha256"
  | "structuredBundleStatus"
  | "structuredBundleParserStage"
  | "structuredBundleFileCount"
  | "structuredBundleAcceptedPaths"
  | "structuredBundleRejectedPaths"
  | "structuredBundleRejectionReason"
  | "backend_anti_cheat_status"
  | "backend_anti_cheat_hard_fail_ids"
  | "backend_anti_cheat_advisory_ids"
  | "backend_anti_cheat_report"
  | "backend_anti_cheat_reasons"
  | "diffSource"
  | "fallbackUsed"
  | "generationSource"
  | "modelFileBundleSha256"
  | "modelOutputShapeSummary"
  | "diffGenerationStatus"
  | "diffGenerationReason"
  | "diffFileCount"
  | "diffAddedPaths"
  | "diffSkippedPaths"
  | "diffSkippedReasons"
  | "diffFilesystemSnapshotSummary"
  | "patchVerificationStatus"
  | "patchVerificationReason"
  | "taskCreationStatus"
  | "taskCreationElapsedMs"
  | "taskCreationTimeoutStage"
  | "taskCreationLastCheckpoint"
  | "taskCreationBlockingSubsystem"
  | "postApplyRediffSha256"
  | "provenanceHashNormalization"
  | "rawModelResponseSha256"
  | "stalePatchRecovered"
  | "storefrontProbe"
  | "trialResultTrustStatus"
  | "verificationStatus"
  | "canonicalContextVerdict"
  | "canonicalContextReportHash"
  | "canonicalContextBlockers"
  | "canonicalContextAcknowledgements"
>;

export function selectedPromptAuditDiagnosticsLines(input: {
  grader: TargetPluginGradingResult | null;
  state: SelectedPromptAuditDiagnosticsState;
}) {
  const { grader, state } = input;
  const normalizedBackendAntiCheatStatus = state.backend_anti_cheat_status
    ?.trim()
    .toLowerCase();
  const backendAntiCheatBlocked = ["blocked", "fail", "failed"].includes(
    normalizedBackendAntiCheatStatus ?? "",
  );
  const backendAntiCheatStatus =
    normalizedBackendAntiCheatStatus === "pass"
      ? "passed"
      : backendAntiCheatBlocked
        ? "fail"
        : state.backend_anti_cheat_status;
  const antiCheatStatus =
    backendAntiCheatBlocked
      ? "fail"
      : grader?.provenance?.anti_cheat_status ??
        backendAntiCheatStatus ??
        "missing: no diagnostic envelope received";
  const antiCheatHardFailIds = backendAntiCheatBlocked
    ? [
        ...new Set([
          ...(state.backend_anti_cheat_hard_fail_ids ?? []),
          ...(grader?.provenance?.anti_cheat_hard_fail_ids ?? []),
        ]),
      ]
    : grader?.provenance?.anti_cheat_hard_fail_ids ??
      state.backend_anti_cheat_hard_fail_ids ??
      [];
  const antiCheatAdvisoryIds = backendAntiCheatBlocked
    ? [
        ...new Set([
          ...(state.backend_anti_cheat_advisory_ids ?? []),
          ...(grader?.provenance?.anti_cheat_advisory_ids ?? []),
        ]),
      ]
    : grader?.provenance?.anti_cheat_advisory_ids ??
      state.backend_anti_cheat_advisory_ids ??
      [];
  const antiCheatReasons = backendAntiCheatBlocked
    ? [
        ...new Set([
          ...(state.backend_anti_cheat_reasons ?? []),
          ...(grader?.provenance?.anti_cheat_reasons ?? []),
        ]),
      ]
    : grader?.provenance?.anti_cheat_reasons ?? state.backend_anti_cheat_reasons ?? [];
  const generationStatus =
    state.generationSource === "model" && Boolean(state.rawModelResponseSha256)
      ? "passed"
      : "not_completed";
  const previewVerificationStatus = /pass|verified|ready/i.test(
    state.patchVerificationStatus ?? "",
  )
    ? "passed"
    : state.patchVerificationStatus ?? "not_completed";
  const approvalStatus = state.approvedDiffSha256 ? "valid" : "not_completed";
  const applyStatus =
    state.applyMode && state.appliedDiffSha256 ? "performed" : "not_performed";
  const postApplyVerificationStatus = /post-apply verified|\bverified\b/i.test(
    state.verificationStatus ?? "",
  )
    ? "passed"
    : state.verificationStatus ?? "not_completed";
  const browserVerificationStatus =
    state.storefrontProbe?.storefront_runtime_status === "passed" &&
    (state.storefrontProbe?.product_count ?? 0) >= 6
      ? "passed"
      : "not_completed";
  const authoritativeAntiCheatStatus =
    antiCheatStatus === "passed" && antiCheatHardFailIds.length === 0
      ? "passed"
      : antiCheatStatus;
  const requiredContextConsumers = [
    "planner",
    "coder",
    "reviewer",
    "verifier",
    "final_receipt_builder",
  ];
  const contextStatus =
    state.canonicalContextVerdict === "GO_ELIGIBLE" &&
    state.canonicalContextBlockers.length === 0 &&
    requiredContextConsumers.every((consumer) =>
      state.canonicalContextAcknowledgements.includes(consumer),
    )
      ? "passed"
      : "blocked";
  const commitSafe =
    generationStatus === "passed" &&
    previewVerificationStatus === "passed" &&
    approvalStatus === "valid" &&
    applyStatus === "performed" &&
    postApplyVerificationStatus === "passed" &&
    browserVerificationStatus === "passed" &&
    authoritativeAntiCheatStatus === "passed" &&
    contextStatus === "passed" &&
    grader?.label === "PASS";
  const requiredAction = commitSafe
    ? "none"
    : contextStatus !== "passed"
      ? "resolve canonical context blockers or missing acknowledgements"
      : postApplyVerificationStatus !== "passed"
        ? "complete post-apply verification"
        : browserVerificationStatus !== "passed"
          ? "complete browser verification"
          : authoritativeAntiCheatStatus !== "passed"
            ? "resolve anti-cheat findings"
            : "complete the next failed lifecycle stage";
  return [
    `grader_anti_cheat_status: ${antiCheatStatus}`,
    `anti_cheat_hard_fail_ids: ${formatList(antiCheatHardFailIds, "not_applicable: no anti-cheat hard failures")}`,
    `anti_cheat_advisory_ids: ${formatList(antiCheatAdvisoryIds, "not_applicable: no anti-cheat advisory findings")}`,
    `anti_cheat_reasons: ${formatList(antiCheatReasons, "missing: backend did not provide field")}`,
    `raw_model_response_sha256: ${state.rawModelResponseSha256 ?? "not_recorded: route_error_before_model_call"}`,
    `model_file_bundle_sha256: ${state.modelFileBundleSha256 ?? "not_recorded: route_error_before_model_call"}`,
    `backend_converted_diff_sha256: ${state.backendConvertedDiffSha256 ?? "missing: backend did not provide field"}`,
    `structured_bundle_status: ${state.structuredBundleStatus ?? "missing: backend did not provide field"}`,
    `structured_bundle_parser_stage: ${state.structuredBundleParserStage ?? "missing: backend did not provide field"}`,
    `structured_bundle_file_count: ${state.structuredBundleFileCount ?? "missing: backend did not provide field"}`,
    `structured_bundle_accepted_paths: ${formatList(state.structuredBundleAcceptedPaths, "missing: backend did not provide field")}`,
    `structured_bundle_rejected_paths: ${formatList(state.structuredBundleRejectedPaths, "not_applicable: no rejected paths")}`,
    `structured_bundle_rejection_reason: ${state.structuredBundleRejectionReason ?? "not_applicable: bundle was not rejected"}`,
    `model_output_shape_summary: ${state.modelOutputShapeSummary ?? "missing: backend did not provide field"}`,
    `diff_generation_status: ${state.diffGenerationStatus ?? "missing: backend did not provide field"}`,
    `diff_generation_reason: ${state.diffGenerationReason ?? "missing: backend did not provide field"}`,
    `diff_file_count: ${state.diffFileCount ?? "missing: backend did not provide field"}`,
    `diff_added_paths: ${formatList(state.diffAddedPaths, "not_applicable: no added paths")}`,
    `diff_skipped_paths: ${formatList(state.diffSkippedPaths, "not_applicable: no skipped paths")}`,
    `diff_skipped_reasons: ${formatList(state.diffSkippedReasons, "not_applicable: no skipped paths")}`,
    `diff_filesystem_snapshot_summary: ${formatList(state.diffFilesystemSnapshotSummary, "not_applicable: no filesystem snapshot summary")}`,
    `patch_verification_status: ${state.patchVerificationStatus ?? "missing: backend did not provide field"}`,
    `patch_verification_reason: ${state.patchVerificationReason ?? "missing: backend did not provide field"}`,
    `task_creation_status: ${state.taskCreationStatus ?? "missing: backend did not provide field"}`,
    `task_creation_elapsed_ms: ${state.taskCreationElapsedMs ?? "missing: backend did not provide field"}`,
    `task_creation_timeout_stage: ${state.taskCreationTimeoutStage ?? "missing: backend did not provide field"}`,
    `task_creation_last_checkpoint: ${state.taskCreationLastCheckpoint ?? "missing: backend did not provide field"}`,
    `task_creation_blocking_subsystem: ${state.taskCreationBlockingSubsystem ?? "missing: backend did not provide field"}`,
    `approved_diff_sha256: ${state.approvedDiffSha256 ?? "not_recorded: apply_did_not_happen"}`,
    `applied_diff_sha256: ${state.appliedDiffSha256 ?? "not_recorded: apply_did_not_happen"}`,
    `backup_manifest: ${state.backupManifest ?? "not_recorded: apply_did_not_happen"}`,
    `post_apply_rediff_sha256: ${state.postApplyRediffSha256 ?? "not_recorded: apply_did_not_happen"}`,
    `provenance_hash_normalization: ${state.provenanceHashNormalization ?? "missing: backend did not provide field"}`,
    `apply_mode: ${state.applyMode ?? "not_recorded: apply_did_not_happen"}`,
    `stale_patch_recovered: ${String(state.stalePatchRecovered ?? false)}`,
    `fallback_used: ${String(state.fallbackUsed ?? false)}`,
    `diff_source: ${state.diffSource ?? "missing: backend did not provide field"}`,
    `trial_result_trust_status: ${state.trialResultTrustStatus ?? "missing: backend did not provide field"}`,
    `storefront_runtime_status: ${state.storefrontProbe?.storefront_runtime_status ?? "not probed"}`,
    `preview_behavior_status: ${state.storefrontProbe?.preview_behavior_status ?? "not probed"}`,
    `storefront_runtime_engine: ${state.storefrontProbe?.storefront_runtime_engine ?? "not probed"}`,
    `browser_evidence_source: ${state.storefrontProbe?.browser_evidence_source ?? "not_proven_by_managed_browser"}`,
    `real_browser_used: ${String(state.storefrontProbe?.real_browser_used === true)}`,
    `storefront_runtime_product_count: ${state.storefrontProbe?.storefront_runtime_product_count ?? "not probed"}`,
    `canonical_context_status: ${contextStatus}`,
    `canonical_context_consumption_status: ${contextStatus === "passed" ? "consumed" : "blocked"}`,
    `downstream_context_acknowledgement_status: ${contextStatus === "passed" ? "acknowledged" : "blocked"}`,
    `required_context_status: ${contextStatus === "passed" ? "passed" : "blocked"}`,
    `canonical_context_verdict: ${state.canonicalContextVerdict ?? "missing"}`,
    `canonical_context_report_hash: ${state.canonicalContextReportHash ?? "missing"}`,
    `canonical_context_blockers: ${formatList(state.canonicalContextBlockers, contextStatus === "passed" ? "not_applicable: no canonical context blockers" : "missing: backend did not provide canonical context blockers")}`,
    `canonical_context_acknowledgements: ${formatList(state.canonicalContextAcknowledgements, "missing: backend did not provide canonical context acknowledgements")}`,
    `generation_status: ${generationStatus}`,
    `preview_verification_status: ${previewVerificationStatus}`,
    `approval_status: ${approvalStatus}`,
    `apply_status: ${applyStatus}`,
    `post_apply_verification_status: ${postApplyVerificationStatus}`,
    `browser_verification_status: ${browserVerificationStatus}`,
    `anti_cheat_status: ${authoritativeAntiCheatStatus}`,
    `commit_safe: ${String(commitSafe)}`,
    `final_truth_status: ${commitSafe ? "GO" : "BLOCKED_SAFE"}`,
    `final_receipt_status: ${commitSafe ? "GO" : "BLOCKED_SAFE"}`,
    `required_action: ${requiredAction}`,
  ];
}

export function selectedPromptFailureDiagnosticLines(diagnostics: Record<string, unknown> | null | undefined) {
  if (!diagnostics) return [];
  const sections = [
    "task_identity",
    "prompt_packet",
    "model_provenance",
    "diff_provenance",
    "approval_binding",
    "verification",
    "anti_cheat",
    "acceptance_gate",
    "final_truth_summary",
  ];
  const lines: string[] = [];
  for (const section of sections) {
    const record = asRecord(diagnostics[section]);
    for (const [key, value] of Object.entries(record)) {
      lines.push(`${section}_${key}: ${formatDiagnosticValue(value)}`);
    }
  }
  for (const key of [
    "reason_code",
    "error",
    "expected_approval_id",
    "received_approval_id",
    "task_creation_status",
    "task_creation_elapsed_ms",
    "task_creation_timeout_stage",
    "task_creation_last_checkpoint",
    "task_creation_blocking_subsystem",
  ]) {
    if (diagnostics[key] != null && !lines.some((line) => line.startsWith(`${key}:`))) {
      lines.push(`${key}: ${formatDiagnosticValue(diagnostics[key])}`);
    }
  }
  return lines;
}

export function selectedPromptFallbackDiagnosticLines(state: DummyCoder10RunState) {
  const executeApprovedNotReached = "not_applicable: execute_approved_not_reached";
  const reasonCode =
    state.rawBackendStatus ??
    state.noDiffFailureCause ??
    state.errorText ??
    (state.status === "blocked" ? "selected_prompt_blocked_before_execute_approved" : "missing_diagnostic_envelope");
  const safeBlock = state.status === "blocked" || state.status === "error" || state.status === "timeout";
  const truthStatus =
    state.status === "blocked"
      ? "BLOCKED_SAFE"
      : state.status === "applied" || state.status === "complete"
        ? "MISSING_DIAGNOSTIC_ENVELOPE"
        : "NO-GO";
  const recommendedNextAction =
    state.recommendedNextAction ??
    (safeBlock
      ? "Inspect the selected-prompt pre-apply failure, clear dirty fixture state if needed, then rerun this prompt."
      : "Inspect Source Proxy route health; expected execute-approved diagnostics were not surfaced.");
  return [
    `truth_status: ${truthStatus}`,
    `reason_code: ${reasonCode}`,
    `structured_bundle_status: ${state.structuredBundleStatus ?? "missing: backend did not provide field"}`,
    `structured_bundle_file_count: ${state.structuredBundleFileCount ?? "missing: backend did not provide field"}`,
    `structured_bundle_accepted_paths: ${formatList(state.structuredBundleAcceptedPaths, "missing: backend did not provide field")}`,
    `structured_bundle_rejected_paths: ${formatList(state.structuredBundleRejectedPaths, "not_applicable: no rejected paths")}`,
    `diff_generation_status: ${state.diffGenerationStatus ?? "missing: backend did not provide field"}`,
    `diff_generation_reason: ${state.diffGenerationReason ?? "missing: backend did not provide field"}`,
    `diff_file_count: ${state.diffFileCount ?? "missing: backend did not provide field"}`,
    `diff_added_paths: ${formatList(state.diffAddedPaths, "not_applicable: no added paths")}`,
    `diff_skipped_paths: ${formatList(state.diffSkippedPaths, "not_applicable: no skipped paths")}`,
    `diff_skipped_reasons: ${formatList(state.diffSkippedReasons, "not_applicable: no skipped paths")}`,
    `diff_filesystem_snapshot_summary: ${formatList(state.diffFilesystemSnapshotSummary, "not_applicable: no filesystem snapshot summary")}`,
    `patch_verification_status: ${state.patchVerificationStatus ?? "missing: backend did not provide field"}`,
    `patch_verification_reason: ${state.patchVerificationReason ?? "missing: backend did not provide field"}`,
    `task_creation_status: ${state.taskCreationStatus ?? "missing: backend did not provide field"}`,
    `task_creation_elapsed_ms: ${state.taskCreationElapsedMs ?? "missing: backend did not provide field"}`,
    `task_creation_timeout_stage: ${state.taskCreationTimeoutStage ?? "missing: backend did not provide field"}`,
    `task_creation_last_checkpoint: ${state.taskCreationLastCheckpoint ?? "missing: backend did not provide field"}`,
    `task_creation_blocking_subsystem: ${state.taskCreationBlockingSubsystem ?? "missing: backend did not provide field"}`,
    `approval_binding_status: not_run: execute_approved_not_reached`,
    `approval_binding_failure_reason: ${executeApprovedNotReached}`,
    `expected_approval_id: ${executeApprovedNotReached}`,
    `received_approval_id: ${executeApprovedNotReached}`,
    `task_id_match: ${executeApprovedNotReached}`,
    `target_match: ${executeApprovedNotReached}`,
    `diff_sha256_match: ${executeApprovedNotReached}`,
    `apply_block_layer: selected_prompt_pre_apply`,
    `block_receipt_path: ${executeApprovedNotReached}`,
    `safe_block: ${String(safeBlock)}`,
    `binary_verdict: NO-GO`,
    `causal_crosscheck_status: skipped_with_reason`,
    `fail_closed_lane_status: skipped_with_reason`,
    `phase_verifier_status: skipped_with_reason`,
    `plan5_gate_id: plan5_selected_prompt_pre_apply_block`,
    `plan5_gate_present: false`,
    `post_apply_verification_status: not_run: execute_approved_not_reached`,
    `post_apply_verification_reason: ${executeApprovedNotReached}`,
    `verification_required_action: ${safeBlock ? "Resolve the pre-apply block, then rerun the selected prompt." : executeApprovedNotReached}`,
    `commit_safe: false`,
    `commit_safe_reason: selected_prompt_not_verified`,
    `recommended_next_action: ${recommendedNextAction}`,
  ];
}

export function selectedPromptPreApplyBlockDiagnostic({
  dirtyFiles = [],
  message,
  reasonCode,
  selectedPromptId,
  taskId = null,
}: {
  dirtyFiles?: string[];
  message: string;
  reasonCode: string;
  selectedPromptId: string;
  taskId?: string | null;
}): Record<string, unknown> {
  const taskLabel = taskId ?? "not_applicable: task_not_created";
  const action =
    reasonCode === "dirty_dummy_fixture_reset_failed"
      ? "Run the dummy fixture cleanup/sweep successfully, verify baseline_clean_for_fresh_suite, then rerun Prompt 1."
      : "Verify the dummy fixture baseline, then rerun Prompt 1 from a clean missing-fixture state.";
  return {
    stage_id: "coding_ui.selected_prompt.pre_apply_fixture_baseline",
    subsystem: "coding_cockpit_selected_prompt",
    task_id: taskLabel,
    selected_prompt_task_id: taskLabel,
    run_id: `selected_prompt:${selectedPromptId}:pre_apply_fixture_baseline`,
    trace_id: "not_applicable: execute_approved_not_reached",
    invocation_event_id: "not_applicable: execute_approved_not_reached",
    consumer_event_id: "not_applicable: execute_approved_not_reached",
    status: "blocked",
    truth_status: "BLOCKED_SAFE",
    safe_block: true,
    error_code: reasonCode,
    reason_code: reasonCode,
    human_message: message,
    machine_reason: reasonCode,
    apply_block_layer: "selected_prompt_pre_apply",
    recommended_next_action: action,
    task_identity: {
      backend_task_id: taskLabel,
      selected_prompt_id: selectedPromptId,
      selected_prompt_task_id: taskLabel,
      trace_id: "not_applicable: execute_approved_not_reached",
    },
    diff_provenance: {
      applied_diff_sha256: "not_applicable: apply_did_not_happen",
      approved_diff_sha256: "not_applicable: execute_approved_not_reached",
      backend_converted_diff_sha256: "not_applicable: execute_approved_not_reached",
      changed_files: dirtyFiles,
      diff_source: "not_applicable: execute_approved_not_reached",
      provenance_hash_normalization: "not_applicable: execute_approved_not_reached",
    },
    approval_binding: {
      approval_binding_status: "not_run: execute_approved_not_reached",
      approval_binding_failure_reason: "not_applicable: execute_approved_not_reached",
      apply_block_layer: "selected_prompt_pre_apply",
      block_receipt_path: "not_applicable: apply_did_not_happen",
      expected_approval_id: "not_applicable: execute_approved_not_reached",
      received_approval_id: "not_applicable: execute_approved_not_reached",
      safe_block: true,
    },
    verification: {
      post_apply_verification_status: "not_run: execute_approved_not_reached",
      post_apply_verification_reason: reasonCode,
      preview_verification_status: "not_run: selected_prompt_pre_apply_block",
      verification_required_action: action,
    },
    anti_cheat: {
      anti_cheat_status: "not_run",
      anti_cheat_reasons: [reasonCode],
      grader_result_state: "not_applicable: selected_prompt_pre_apply_block",
      trial_result_trust_status: "blocked_before_apply",
    },
    acceptance_gate: {
      acceptance_failures: [reasonCode],
      binary_verdict: "NO-GO",
      causal_crosscheck_status: "skipped_with_reason",
      fail_closed_lane_status: "skipped_with_reason",
      missing_fields: ["execute_approved_apply_receipt"],
      phase_verifier_status: "skipped_with_reason",
      plan5_gate_id: "plan5_selected_prompt_pre_apply_block",
      plan5_gate_present: false,
      plan5_gate_version: "plan5_acceptance_v1",
      reason: reasonCode,
    },
    final_truth_summary: {
      commit_safe: false,
      commit_safe_reason: reasonCode,
      proof_level: "selected_prompt_pre_apply_block",
      raw_backend_status: reasonCode,
      recommended_next_action: action,
      run_status: "blocked",
      block_receipt_path: "not_applicable: apply_did_not_happen",
      truth_status: "BLOCKED_SAFE",
      why_not_go: message,
    },
    queue_conflict: {},
    unavailable_fields: [
      { field: "expected_approval_id", reason: "execute-approved not reached" },
      { field: "received_approval_id", reason: "execute-approved not reached" },
      { field: "block_receipt_path", reason: "apply did not happen" },
    ],
    persisted_at: "not_applicable: ui_pre_apply_block",
    surfaced_at: new Date().toISOString(),
  };
}

function formatDiagnosticValue(value: unknown): string {
  if (Array.isArray(value)) return formatList(value.map((item) => String(item)), "missing: backend did not provide field");
  if (value == null || value === "") return "missing: backend did not provide field";
  if (typeof value === "boolean") return String(value);
  if (typeof value === "number") return String(value);
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function buildRouteUnavailableSuitePromptResult(
  prompt: ReversibleTrialPrompt,
  failure: RouteAvailabilityFailure,
  promptNumber: number,
  providerLabel: string,
): ReversibleSuitePromptResult {
  const diagnostic = buildRouteUnavailableDiagnostic(failure, promptNumber);
  return {
    allowed_files: prompt.expected_scope,
    applied_changed_files: [],
    checks_result: "not run",
    checks_run: ["git diff --check"],
    disk_changed_files: [],
    endpoint_statuses: [`${failure.route}:${failure.status}`],
    error_summary: diagnostic.error_summary,
    expected_outcome: prompt.expectedOutcome,
    failure_reason: diagnostic.failure_reason,
    model_called_for_generation: "none",
    next_recommended_action: diagnostic.next_recommended_action,
    prompt,
    provider: providerLabel,
    provider_call_made: false,
    provenance: normalizeTrialResultProvenance(undefined),
    preview_changed_files: [],
    reverse_diff: "",
    reverse_status_text: "No applied trial edits to reverse.",
    reverted: false,
    reversal_available: false,
    run_id: `${prompt.id}:route-unavailable`,
    selected_target: prompt.targetFile,
    target_candidates: prompt.expected_scope,
    visible_result_label: diagnostic.visible_result_label,
    elapsed_ms: null,
  };
}

function buildRouteUnavailablePromptResult(
  baseResult: (patch: Partial<ReversibleSuitePromptResult>) => ReversibleSuitePromptResult,
  failure: RouteAvailabilityFailure,
  endpointStatuses: string[],
  promptNumber?: number,
  providerCallMade = false,
  runId = "",
): ReversibleSuitePromptResult {
  const diagnostic = buildRouteUnavailableDiagnostic(failure, promptNumber);
  endpointStatuses.push(`${failure.route}:${failure.status}`);
  return baseResult({
    endpoint_statuses: [...endpointStatuses],
    error_summary: diagnostic.error_summary,
    failure_reason: diagnostic.failure_reason,
    next_recommended_action: diagnostic.next_recommended_action,
    provider_call_made: providerCallMade,
    run_id: runId,
    visible_result_label: diagnostic.visible_result_label,
  });
}

function reversibleSuiteAbortForResult(result: ReversibleSuitePromptResult): ReversibleSuiteAbort | null {
  const endpointText = result.endpoint_statuses.join(", ");
  const failureText = `${result.failure_reason} ${result.error_summary}`.toLowerCase();
  const hasServerError = result.endpoint_statuses.some((status) => /:5\d\d(?:\b|$)/.test(status));
  const fetchFailed = failureText.includes("failed to fetch");

  if (isRouteInfraUnavailableSummary(result.error_summary, result.failure_reason)) {
    return {
      reason: `route_unavailable: ${result.error_summary || result.failure_reason}`,
      source: "route_failed",
      step: "Stopped: SpiritOS /v1 API routes unavailable",
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
type CodingPipelineStepStatus = "pending" | "running" | "complete" | "blocked" | "failed" | "skipped";
type CodingPipelineStep = {
  detail: string;
  label: string;
  status: CodingPipelineStepStatus;
};
type ActiveRunDisplaySource = "composer" | "selected-runner";
type ActiveRunDisplay = {
  detail: string;
  pipelineDetail: string;
  previewState: PreviewState;
  routeLabel: string;
  source: ActiveRunDisplaySource;
  taskLabel: string;
  title: string;
  traceLabel: string;
};

const manualTaskPhaseLabels = {
  received: "Reading request",
  analyzing: "Reading request",
  discovering: "Finding files",
  packet: "Finding files",
  promptPacket: "Running prompt-packet",
  preview: "Calling model",
  checks: "Checking",
  review: "Ready to review",
  done: "Ready to review",
  blocked: "Ready to review",
  failed: "Ready to review",
} as const;

/**
 * Match CodingAgentInterface prompt-packet patience; proxy coder sync deadline defaults to 180s.
 * The buffer used to be 180s (360s total), which left the UI stuck for 6 minutes on a slow/hung
 * model call. The proxy itself gives up at 180s, so keep the frontend deadline just above that to
 * fail faster with an honest timeout instead of a silent black box.
 */
const MANUAL_PROMPT_PACKET_TIMEOUT_MS = 180_000;
const TRIAL_PROMPT_PACKET_TIMEOUT_BUFFER_MS = 180_000;
const TRIAL_PROMPT_PACKET_TIMEOUT_MS = MANUAL_PROMPT_PACKET_TIMEOUT_MS + TRIAL_PROMPT_PACKET_TIMEOUT_BUFFER_MS;
const TRIAL_PROMPT_PACKET_MAX_ATTEMPTS = 2;
const TRIAL_POST_MODEL_STAGE_TIMEOUT_MS = 60_000;
const TRIAL_EXECUTE_APPROVED_STALE_MS = TRIAL_POST_MODEL_STAGE_TIMEOUT_MS + 45_000;
const TRIAL_BETWEEN_PROMPTS_STALE_MS = 45_000;
const TRIAL_DURABLE_ROW_SYNC_TIMEOUT_MS = 20_000;
const TRIAL_LONG_RUNNING_TIMEOUT_MS = 30_000;
const TRIAL_LONG_RUNNING_MAX_ATTEMPTS = 3;
const SELECTED_PROMPT_WAITING_FOR_TASK_ID = "Starting selected prompt. Waiting for backend task id.";
const SELECTED_PROMPT_TASK_ID_STUCK_MESSAGE =
  "No backend task id returned yet. The selected prompt may be stuck before task creation.";
const TRIAL_CLEANUP_DRAIN_MAX_PASSES = 3;
const TRIAL_CLEANUP_ROUTE_HEALTH_ATTEMPTS = 8;
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
  const totalSeconds = Math.round(ms / 1000);
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return seconds === 0 ? `${minutes}m` : `${minutes}m ${seconds}s`;
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
  backupManifest?: string | null;
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
  undoReceiptId?: string | null;
  undoReceiptPath?: string | null;
  postApplyVerificationStatus?: string | null;
  finalTruthStatus?: string | null;
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
const dummyCoderRunStorageKey = "spiritos:coding:dummy-coder-selected-run:v1";
const dummyCoderRunInFlightStaleMs = 120_000;

type BackendRunSyncState = {
  runId: string;
  status: "idle" | "loading" | "synced" | "attached" | "error";
  lastSyncedAt: string | null;
  message: string;
};

export function shouldClearStaleLocalTrialStateAfterCloudClear({
  agentLabBaselineClean,
  agentLabBaselineLoadState,
  appliedRunReceipts,
  backendRunSync,
  localRunnerActive,
  reversibleSuiteState,
}: {
  agentLabBaselineClean: boolean | null | undefined;
  agentLabBaselineLoadState: "idle" | "loading" | "ready" | "error";
  appliedRunReceipts: AppliedRunReceipt[];
  backendRunSync: Pick<BackendRunSyncState, "runId" | "status">;
  localRunnerActive: boolean;
  reversibleSuiteState: ReversibleSuiteState;
}): boolean {
  if (localRunnerActive) return false;
  if (backendRunSync.status !== "synced" || backendRunSync.runId) return false;
  if (agentLabBaselineLoadState !== "ready" || !agentLabBaselineClean) return false;
  if (
    reversibleSuiteState.status === "failed" &&
    (reversibleSuiteState.interruptionSource === "browser_refresh_or_dev_reload" ||
      reversibleSuiteState.interruptionSource === "user_stop") &&
    reversibleSuiteState.completed < reversibleSuiteState.count
  ) {
    return false;
  }
  const hasStaleLocalSuite =
    reversibleSuiteState.status !== "idle" ||
    reversibleSuiteState.results.length > 0 ||
    Boolean(reversibleSuiteState.suiteId);
  const hasStaleTrialSuiteReceipts = appliedRunReceipts.some(
    (receipt) => receipt.id.startsWith("trial-suite:") && !receipt.revertedAt && !receipt.staleResolvedAt,
  );
  return hasStaleLocalSuite || hasStaleTrialSuiteReceipts;
}

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
    baselineCheckedAt: null,
    baselineAgentLabFiles: [],
    baselineDirtyAgentLabFiles: [],
    baselineUnrevertedReceipts: [],
    baselineCleanForFreshSuite: null,
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

function defaultDummyCoderRunState(
  message = "No LumaCart prompt has been run in this panel.",
  status: DummyCoder10RunState["status"] = "idle",
): DummyCoder10RunState {
  return {
    changedFiles: [],
    checksRun: [],
    diffSource: null,
    backend_anti_cheat_status: null,
    backend_anti_cheat_hard_fail_ids: [],
    backend_anti_cheat_advisory_ids: [],
    backend_anti_cheat_report: null,
    backend_anti_cheat_reasons: [],
    errorText: null,
    fallbackUsed: null,
    generatedDiffByBackend: null,
    generationSource: null,
    grader: null,
    message,
    modelOutputClassification: null,
    noDiffFailureCause: null,
    parserExtractorDecision: null,
    packet: null,
    rawBackendStatus: null,
    rawModelResponseSha256: null,
    recommendedNextAction: null,
    lastFailureDiagnostics: null,
    scaffoldUsed: null,
    selectedPromptId: null,
    startedAt: null,
    finishedAt: null,
    applyMode: null,
    appliedDiffSha256: null,
    backupManifest: null,
    approvedDiffSha256: null,
    backendConvertedDiffSha256: null,
    structuredBundleStatus: null,
    structuredBundleParserStage: null,
    structuredBundleFileCount: null,
    structuredBundleAcceptedPaths: [],
    structuredBundleRejectedPaths: [],
    structuredBundleRejectionReason: null,
    modelOutputShapeSummary: null,
    diffGenerationStatus: null,
    diffGenerationReason: null,
    diffFileCount: null,
    diffAddedPaths: [],
    diffSkippedPaths: [],
    diffSkippedReasons: [],
    diffFilesystemSnapshotSummary: [],
    patchVerificationStatus: null,
    patchVerificationReason: null,
    taskCreationStatus: null,
    taskCreationElapsedMs: null,
    taskCreationTimeoutStage: null,
    taskCreationLastCheckpoint: null,
    taskCreationBlockingSubsystem: null,
    modelFileBundleSha256: null,
    postApplyRediffSha256: null,
    provenanceHashNormalization: null,
    stalePatchRecovered: null,
    storefrontProbe: null,
    canonicalContextVerdict: null,
    canonicalContextReportHash: null,
    canonicalContextBlockers: [],
    canonicalContextAcknowledgements: [],
    taskId: null,
    status,
    trialResultTrustStatus: null,
    verificationStatus: null,
  };
}

export function selectedPromptTaskDescription(prompt: TargetPluginPrompt) {
  const selectedTarget = selectedPromptTarget(prompt);
  return [
    prompt.submittedPrompt,
    "",
    `Selected prompt id: ${prompt.id}`,
    `Selected prompt number: ${prompt.number}`,
    `Target file: ${selectedTarget}`,
    `Allowed files: ${prompt.allowedWriteRoot}`,
    `Fixture root: ${prompt.fixtureRoot}`,
    `Forbidden files: ${codingTargetPlugin.formatForbiddenSummary(prompt)}`,
    `Pass expectations: ${prompt.passExpectations.join("; ")}`,
    `Fail conditions: ${prompt.failConditions.join("; ")}`,
    prompt.projectContract,
  ].join("\n");
}

export function selectedPromptTarget(prompt: TargetPluginPrompt) {
  if (prompt.id === "coder-003-render-product-cards") {
    return (
      prompt.primaryExpectedTargets.find((target) => target.endsWith("/src/main.js")) ??
      prompt.primaryExpectedTargets[0] ??
      prompt.fixtureRoot
    );
  }
  return prompt.primaryExpectedTargets[0] ?? prompt.fixtureRoot;
}

export function selectedPromptModelTask(prompt: TargetPluginPrompt) {
  return [
    prompt.submittedPrompt,
    "",
    `Pass expectations: ${prompt.passExpectations.join("; ")}`,
    `Fail conditions: ${prompt.failConditions.join("; ")}`,
    prompt.id === "coder-003-render-product-cards"
      ? "Implementation notes: src/products.js is the source of truth. Option A is mandatory: change index.html to <script type=\"module\" src=\"src/main.js\"></script>, statically import products from './products.js'; in src/main.js, and render cards dynamically from imported products. Do not use dynamic import, do not duplicate product data, and do not hardcode product cards in index.html."
      : "",
    prompt.projectContract,
  ].filter(Boolean).join("\n");
}

function dummyProductDataFieldsPresentFromSource(source: string) {
  if (!source.trim()) return false;
  if (
    !/\bexport\s+default\s+products\b/.test(source) &&
    !/\bexport\s+const\s+products\s*=/.test(source)
  ) {
    return false;
  }
  const productBlocks = [...source.matchAll(/\{[^{}]*\}/g)].map((match) => match[0]);
  const validProducts = productBlocks.filter((block) =>
    ["id", "name", "price", "category", "description"].every((field) =>
      new RegExp(`\\b${field}\\s*:`).test(block),
    ),
  );
  return validProducts.length >= 6;
}

export function selectedPrompt3DiffViolations(
  diff: string,
  context?: { currentIndexHtml?: string; currentMainJs?: string },
) {
  const normalized = diff.replace(/\r\n/g, "\n");
  const currentIndexHtml = context?.currentIndexHtml ?? "";
  const currentMainJs = context?.currentMainJs ?? "";
  const violations: string[] = [];
  if (
    /Product Name|Description: This is a description|grid grid-cols|<main id=["']product-list["'][\s\S]*<div class=["'](?:card|product-card)/i.test(
      normalized,
    )
  ) {
    violations.push("hardcoded_or_generic_cards_in_index_html");
  }
  const hasDynamicProductsImport = /import\s*\(\s*['"]\.\/products\.js['"]\s*\)/i.test(normalized);
  const hasStaticProductsImport = /import\s+[\s\S]*?\s+from\s*['"]\.\/products\.js['"]/i.test(normalized);
  const currentMainHasStaticProductsImport = /import\s+[\s\S]*?\s+from\s*['"]\.\/products\.js['"]/i.test(currentMainJs);
  const diffRemovesProductsImport = /^-\s*import\s+[\s\S]*?\s+from\s*['"]\.\/products\.js['"]/im.test(normalized);
  const hasProductsImport =
    hasDynamicProductsImport ||
    hasStaticProductsImport ||
    (currentMainHasStaticProductsImport && !diffRemovesProductsImport);
  const diffAddsModuleScript = /^\+\s*<script\b[^>]*type=["']module["'][^>]*src=["']src\/main\.js["']/im.test(normalized);
  const currentIndexHasModuleScript = /<script\b[^>]*type=["']module["'][^>]*src=["']src\/main\.js["']/i.test(currentIndexHtml);
  const diffRemovesModuleScript = /^-\s*<script\b[^>]*type=["']module["'][^>]*src=["']src\/main\.js["']/im.test(normalized);
  const hasModuleScriptWiring = diffAddsModuleScript || (currentIndexHasModuleScript && !diffRemovesModuleScript);
  if (
    !/src\/main\.js/i.test(normalized) ||
    !hasProductsImport ||
    !/product\.category|product-card/i.test(normalized)
  ) {
    violations.push("missing_dynamic_products_render_path");
  }
  if ((hasStaticProductsImport || currentMainHasStaticProductsImport) && !hasModuleScriptWiring) {
    violations.push("static_products_import_without_module_script_wiring");
  }
  if (!hasProductsImport) {
    violations.push("missing_products_import");
  }
  if (/^\+.*\b(?:const|let|var)\s+products\s*=\s*\[/im.test(normalized) || (/Product A/.test(normalized) && /Product F/.test(normalized))) {
    violations.push("product_data_duplicated");
  }
  return violations;
}

function storedDummyCoderRunSnapshot(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(dummyCoderRunStorageKey);
}

function isDummyCoderRunStatus(value: unknown): value is DummyCoder10RunState["status"] {
  return (
    value === "idle" ||
    value === "starting" ||
    value === "request_sent" ||
    value === "running" ||
    value === "complete" ||
    value === "blocked" ||
    value === "applied" ||
    value === "cleared" ||
    value === "error" ||
    value === "timeout"
  );
}

function storedStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function storedStringOrNull(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function storedBooleanOrNull(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function loadStoredDummyCoderRunState(): DummyCoder10RunState {
  if (typeof window === "undefined") return defaultDummyCoderRunState();
  try {
    const parsed = JSON.parse(storedDummyCoderRunSnapshot() ?? "null") as Record<string, unknown> | null;
    if (!parsed || typeof parsed !== "object" || !isDummyCoderRunStatus(parsed.status)) {
      return defaultDummyCoderRunState();
    }
    if (parsed.status === "idle" || parsed.status === "cleared") {
      return defaultDummyCoderRunState(storedStringOrNull(parsed.message) ?? undefined, parsed.status);
    }
    const selectedPromptId = storedStringOrNull(parsed.selectedPromptId);
    const selectedPromptKnown = selectedPromptId
      ? codingTargetPlugin.prompts.some((prompt) => prompt.id === selectedPromptId)
      : false;
    if (!selectedPromptKnown) return defaultDummyCoderRunState();
    const storedAt = typeof parsed.storedAt === "number" ? parsed.storedAt : null;
    const inFlight = parsed.status === "starting" || parsed.status === "request_sent" || parsed.status === "running";
    if (inFlight && (!storedAt || Date.now() - storedAt > dummyCoderRunInFlightStaleMs)) {
      return {
        ...defaultDummyCoderRunState(
          "Previous selected prompt timed out before returning a result. Clear it, then run the prompt again.",
          "timeout",
        ),
        errorText: "Selected prompt timed out before the backend returned a prompt-packet result.",
        rawBackendStatus: storedStringOrNull(parsed.rawBackendStatus) ?? "stale_request",
        recommendedNextAction: "Clear the stale selected-prompt state, then rerun Prompt 1.",
        selectedPromptId,
        taskId: storedStringOrNull(parsed.taskId),
      };
    }
    return {
      changedFiles: storedStringArray(parsed.changedFiles),
      checksRun: storedStringArray(parsed.checksRun),
      diffSource: storedStringOrNull(parsed.diffSource),
      backend_anti_cheat_status: storedStringOrNull(parsed.backend_anti_cheat_status),
      backend_anti_cheat_hard_fail_ids: storedStringArray(parsed.backend_anti_cheat_hard_fail_ids),
      backend_anti_cheat_advisory_ids: storedStringArray(parsed.backend_anti_cheat_advisory_ids),
      backend_anti_cheat_report: storedStringOrNull(parsed.backend_anti_cheat_report),
      backend_anti_cheat_reasons: storedStringArray(parsed.backend_anti_cheat_reasons),
      errorText: storedStringOrNull(parsed.errorText),
      fallbackUsed: storedBooleanOrNull(parsed.fallbackUsed),
      generatedDiffByBackend: storedBooleanOrNull(parsed.generatedDiffByBackend),
      generationSource: storedStringOrNull(parsed.generationSource),
      grader:
        parsed.grader && typeof parsed.grader === "object"
          ? (parsed.grader as TargetPluginGradingResult)
          : null,
      message: storedStringOrNull(parsed.message) ?? "Selected prompt state restored after browser refresh.",
      modelOutputClassification: storedStringOrNull(parsed.modelOutputClassification),
      noDiffFailureCause: storedStringOrNull(parsed.noDiffFailureCause),
      parserExtractorDecision: storedStringOrNull(parsed.parserExtractorDecision),
      packet: parsed.packet ?? null,
      rawBackendStatus: storedStringOrNull(parsed.rawBackendStatus),
      rawModelResponseSha256: storedStringOrNull(parsed.rawModelResponseSha256),
      recommendedNextAction: storedStringOrNull(parsed.recommendedNextAction),
      lastFailureDiagnostics:
        parsed.lastFailureDiagnostics && typeof parsed.lastFailureDiagnostics === "object"
          ? (parsed.lastFailureDiagnostics as Record<string, unknown>)
          : null,
      scaffoldUsed: storedBooleanOrNull(parsed.scaffoldUsed),
      selectedPromptId,
      startedAt: typeof parsed.startedAt === "number" ? parsed.startedAt : null,
      finishedAt: typeof parsed.finishedAt === "number" ? parsed.finishedAt : null,
      applyMode: storedStringOrNull(parsed.applyMode),
      appliedDiffSha256: storedStringOrNull(parsed.appliedDiffSha256),
      backupManifest: storedStringOrNull(parsed.backupManifest),
      approvedDiffSha256: storedStringOrNull(parsed.approvedDiffSha256),
        backendConvertedDiffSha256: storedStringOrNull(parsed.backendConvertedDiffSha256),
        structuredBundleStatus: storedStringOrNull(parsed.structuredBundleStatus),
        structuredBundleParserStage: storedStringOrNull(parsed.structuredBundleParserStage),
        structuredBundleFileCount: typeof parsed.structuredBundleFileCount === "number" ? parsed.structuredBundleFileCount : null,
        structuredBundleAcceptedPaths: storedStringArray(parsed.structuredBundleAcceptedPaths),
        structuredBundleRejectedPaths: storedStringArray(parsed.structuredBundleRejectedPaths),
        structuredBundleRejectionReason: storedStringOrNull(parsed.structuredBundleRejectionReason),
        modelOutputShapeSummary: storedStringOrNull(parsed.modelOutputShapeSummary),
        diffGenerationStatus: storedStringOrNull(parsed.diffGenerationStatus),
        diffGenerationReason: storedStringOrNull(parsed.diffGenerationReason),
        diffFileCount: typeof parsed.diffFileCount === "number" ? parsed.diffFileCount : null,
        diffAddedPaths: storedStringArray(parsed.diffAddedPaths),
        diffSkippedPaths: storedStringArray(parsed.diffSkippedPaths),
        diffSkippedReasons: storedStringArray(parsed.diffSkippedReasons),
        diffFilesystemSnapshotSummary: storedStringArray(parsed.diffFilesystemSnapshotSummary),
        patchVerificationStatus: storedStringOrNull(parsed.patchVerificationStatus),
        patchVerificationReason: storedStringOrNull(parsed.patchVerificationReason),
        taskCreationStatus: storedStringOrNull(parsed.taskCreationStatus),
        taskCreationElapsedMs: typeof parsed.taskCreationElapsedMs === "number" ? parsed.taskCreationElapsedMs : null,
        taskCreationTimeoutStage: storedStringOrNull(parsed.taskCreationTimeoutStage),
        taskCreationLastCheckpoint: storedStringOrNull(parsed.taskCreationLastCheckpoint),
        taskCreationBlockingSubsystem: storedStringOrNull(parsed.taskCreationBlockingSubsystem),
        modelFileBundleSha256: storedStringOrNull(parsed.modelFileBundleSha256),
      postApplyRediffSha256: storedStringOrNull(parsed.postApplyRediffSha256),
      provenanceHashNormalization: storedStringOrNull(parsed.provenanceHashNormalization),
      stalePatchRecovered: storedBooleanOrNull(parsed.stalePatchRecovered),
      storefrontProbe:
        parsed.storefrontProbe && typeof parsed.storefrontProbe === "object"
          ? (parsed.storefrontProbe as TargetPluginStorefrontProbeResult)
          : null,
      canonicalContextVerdict: storedStringOrNull(parsed.canonicalContextVerdict),
      canonicalContextReportHash: storedStringOrNull(parsed.canonicalContextReportHash),
      canonicalContextBlockers: storedStringArray(parsed.canonicalContextBlockers),
      canonicalContextAcknowledgements: storedStringArray(parsed.canonicalContextAcknowledgements),
      taskId: storedStringOrNull(parsed.taskId),
      status:
        parsed.status === "starting" || parsed.status === "request_sent" || parsed.status === "running"
          ? parsed.status
          : parsed.status,
      trialResultTrustStatus: storedStringOrNull(parsed.trialResultTrustStatus),
      verificationStatus: storedStringOrNull(parsed.verificationStatus),
    };
  } catch {
    return defaultDummyCoderRunState();
  }
}

function storeDummyCoderRunState(state: DummyCoder10RunState) {
  if (typeof window === "undefined") return;
  if (state.status === "idle" || state.status === "cleared") {
    window.localStorage.removeItem(dummyCoderRunStorageKey);
    return;
  }
  window.localStorage.setItem(dummyCoderRunStorageKey, JSON.stringify({ ...state, storedAt: Date.now() }));
}

function clearStoredDummyCoderRunState() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(dummyCoderRunStorageKey);
}

function durableRunStatusForSuite(state: ReversibleSuiteState): DurableCodingRunStatus {
  if (state.status === "running") return "running";
  if (state.status === "stopping") return "cancelled";
  if (state.status === "done") return "completed";
  if (state.interruptionSource === "provider_timeout") return "timed_out";
  if (state.status === "failed") return "failed";
  return "pending";
}

function durableRunIsVisibleInCodingCloud(run: DurableCodingRun | null | undefined) {
  return Boolean(run && run.status !== "cleared");
}

function shouldAttachDurableRunToUi(run: DurableCodingRun, current: ReversibleSuiteState): boolean {
  if (run.status === "running" || run.status === "pending" || run.status === "completed") {
    return true;
  }
  const runKey = run.run_id || run.suite_id;
  if (current.suiteId && current.suiteId === runKey) {
    return true;
  }
  const stored = loadStoredReversibleSuiteState();
  if (stored.suiteId && stored.suiteId === runKey) {
    return true;
  }
  return false;
}

const REVERSIBLE_SUITE_LEASE_KEY = "spiritos-reversible-suite-runner-lease";
const REVERSIBLE_SUITE_LEASE_TTL_MS = 15_000;

function readReversibleSuiteRunnerLease() {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(window.localStorage.getItem(REVERSIBLE_SUITE_LEASE_KEY) ?? "null") as
      | { runId?: string; at?: number }
      | null;
  } catch {
    return null;
  }
}

function touchReversibleSuiteRunnerLease(runId: string) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(REVERSIBLE_SUITE_LEASE_KEY, JSON.stringify({ runId, at: Date.now() }));
  } catch {
    // Quota/private mode — stale guard falls back to local-runner ref only.
  }
}

function reversibleSuiteRunnerLeaseActive(runId: string, nowMs = Date.now()) {
  const parsed = readReversibleSuiteRunnerLease();
  return Boolean(
    parsed?.runId === runId &&
      typeof parsed.at === "number" &&
      nowMs - parsed.at <= REVERSIBLE_SUITE_LEASE_TTL_MS,
  );
}

function reversibleSuiteRunnerLeaseKnown(runId: string) {
  return readReversibleSuiteRunnerLease()?.runId === runId;
}

function clearReversibleSuiteRunnerLease(runId: string) {
  if (typeof window === "undefined") return;
  try {
    const parsed = JSON.parse(window.localStorage.getItem(REVERSIBLE_SUITE_LEASE_KEY) ?? "null") as
      | { runId?: string }
      | null;
    if (parsed?.runId === runId) {
      window.localStorage.removeItem(REVERSIBLE_SUITE_LEASE_KEY);
    }
  } catch {
    // ignore
  }
}

function durableRunPendingPromptId(run: DurableCodingRun): string | null {
  const inFlight = run.rows.find((row) => row.status === "running" || row.status === "pending");
  if (inFlight) return inFlight.prompt_id;
  const currentRow = run.current_prompt_id
    ? run.rows.find((row) => row.prompt_id === run.current_prompt_id)
    : null;
  if (
    currentRow &&
    currentRow.status !== "completed" &&
    currentRow.status !== "reverted" &&
    currentRow.status !== "failed"
  ) {
    return currentRow.prompt_id;
  }
  if (run.completed_count < run.requested_count && (run.status === "running" || run.status === "pending")) {
    const completedIds = new Set(
      run.rows
        .filter((row) => row.status === "completed" || row.status === "reverted")
        .map((row) => row.prompt_id),
    );
    const count = (reversibleTrialCounts.includes(run.requested_count as ReversibleTrialCount)
      ? run.requested_count
      : 10) as ReversibleTrialCount;
    const prompts = selectReversibleTrialPrompts(count, "Coder");
    return prompts.find((prompt) => !completedIds.has(prompt.id))?.id ?? run.current_prompt_id ?? null;
  }
  return run.current_prompt_id ?? null;
}

function durableRunInFlightActiveRow(run: DurableCodingRun): DurableCodingRunRow | null {
  const byCurrentId = run.current_prompt_id
    ? run.rows.find((row) => row.prompt_id === run.current_prompt_id)
    : null;
  if (byCurrentId && (byCurrentId.status === "running" || byCurrentId.status === "pending")) {
    return byCurrentId;
  }
  const existing = run.rows.find((row) => row.status === "running" || row.status === "pending");
  if (existing) return existing;
  const pendingPromptId = durableRunPendingPromptId(run);
  if (!pendingPromptId || (run.status !== "running" && run.status !== "pending")) return null;
  return {
    prompt_id: pendingPromptId,
    run_id: `${run.run_id}:${run.current_prompt_id}`,
    prompt_text: "",
    prompt_excerpt: "",
    status: "running",
    started_at: run.current_prompt_started_at ?? run.updated_at,
    updated_at: run.current_step_started_at ?? run.updated_at,
    provider_call_made: run.provider_call_made,
    model_called_for_generation: run.model_called_for_generation,
    endpoint_statuses: run.endpoint_statuses || [],
    reason_code: run.reason_code || "",
    generated_diff_present: run.generated_diff_present,
    preview_changed_files: run.preview_changed_files || [],
    applied_changed_files: run.applied_changed_files || [],
    disk_changed_files: run.disk_changed_files || [],
    checks_run: run.checks_run || [],
    checks_result: run.checks_result || "",
    reversal_available: run.reversal_available,
    reversal_status: run.reversal_status,
    result_label: "RUNNING",
    error_summary: run.last_error || "",
  };
}

function durableRunOrphanedInFlightStep(run: DurableCodingRun | null | undefined, nowMs = Date.now()) {
  if (!run || (run.status !== "running" && run.status !== "pending")) return false;
  if (
    durableRunHasStaleEditingFiles(run, nowMs) ||
    durableRunHasStaleExecuteApproved(run, nowMs)
  ) {
    return true;
  }
  if (reversibleSuiteRunnerLeaseActive(run.run_id, nowMs)) return false;
  return durableRunHasStalePromptPacket(run, nowMs);
}

function durableRunSuccessfulRows(run: DurableCodingRun) {
  return run.rows.filter((row) => row.status === "completed" || row.status === "reverted");
}

function durableRunIsResumableUserStop(run: DurableCodingRun) {
  return (
    (run.status === "cancelled" || run.reason_code === "user_stop") &&
    durableRunSuccessfulRows(run).length < run.requested_count
  );
}

function durableRunHasLocalRefreshInterruptedInFlightStep(run: DurableCodingRun) {
  if (run.status !== "running" && run.status !== "pending") return false;
  const lease = readReversibleSuiteRunnerLease();
  if (lease?.runId !== run.run_id || typeof lease.at !== "number") return false;
  if (reversibleSuiteRunnerLeaseActive(run.run_id)) return false;
  const activeRow = durableRunInFlightActiveRow(run);
  return Boolean(
    activeRow &&
      durableRunSuccessfulRows(run).length < run.requested_count &&
      (durableRunHasStalePromptPacket(run) ||
        durableRunHasStaleExecuteApproved(run) ||
        durableRunHasStaleEditingFiles(run) ||
        durableRunHasStalePostApplyVerification(run, Date.now(), TRIAL_EXECUTE_APPROVED_STALE_MS) ||
        durableRunBetweenPromptsStale(run)),
  );
}

function reversibleSuiteStateCanResume(state: ReversibleSuiteState) {
  return (
    state.status === "failed" &&
    (state.interruptionSource === "browser_refresh_or_dev_reload" ||
      state.interruptionSource === "user_stop") &&
    state.completed < state.count
  );
}

function durableRunBetweenPromptsStale(run: DurableCodingRun | null | undefined, nowMs = Date.now()) {
  if (!durableRunHasStaleBetweenPromptsGap(run, nowMs, TRIAL_BETWEEN_PROMPTS_STALE_MS)) return false;
  if (!run) return false;
  if (reversibleSuiteRunnerLeaseActive(run.run_id, nowMs)) {
    return false;
  }
  return true;
}

function durableRunIsStaleStepInterruption(run: DurableCodingRun): boolean {
  if (durableRunBetweenPromptsStale(run)) return true;
  if (durableRunOrphanedInFlightStep(run)) return true;
  if (durableRunHasStalePostApplyVerification(run, Date.now(), TRIAL_EXECUTE_APPROVED_STALE_MS)) return true;
  if (run.reason_code === "prompt_packet_stale_no_completion") {
    const staleRow = run.rows.find((row) => row.reason_code === "prompt_packet_stale_no_completion");
    if (staleRow) return !staleRow.provider_call_made;
    return !run.provider_call_made;
  }
  if (run.reason_code === "execute_approved_stale_no_completion") {
    const staleRow = run.rows.find((row) => row.reason_code === "execute_approved_stale_no_completion");
    if (staleRow) return !staleRow.applied_changed_files?.length;
    return (run.applied_changed_files || []).length === 0;
  }
  if (
    run.reason_code === "apply_ack_no_disk_proof" ||
    run.reason_code === "post_apply_verification_missing" ||
    run.reason_code === "execute_approved_no_completion" ||
    run.reason_code === "between_prompts_runner_lost"
  ) {
    return true;
  }
  return false;
}

function durableRunHasStalePromptPacket(run: DurableCodingRun | null | undefined, nowMs = Date.now()) {
  if (!run || (run.status !== "running" && run.status !== "pending")) return false;
  const activeRow = durableRunInFlightActiveRow(run);
  if (!activeRow || activeRow.status !== "running") return false;
  const statuses = new Set([...(run.endpoint_statuses || []), ...(activeRow.endpoint_statuses || [])]);
  if (!statuses.has("/v1/decisions/prompt-packet:started")) return false;
  if ([...statuses].some((status) => status.startsWith("/v1/decisions/prompt-packet:200"))) return false;
  if ([...statuses].some((status) => status.includes("stale_no_completion") || status.includes(":timeout"))) return false;
  const promptPacketInFlight = true;
  const startedAt = Date.parse(
    (promptPacketInFlight
      ? run.current_prompt_started_at || activeRow.started_at
      : run.current_step_started_at) ||
      run.current_prompt_started_at ||
      activeRow.updated_at ||
      activeRow.started_at ||
      run.updated_at ||
      run.created_at,
  );
  return Number.isFinite(startedAt) && nowMs - startedAt > TRIAL_PROMPT_PACKET_TIMEOUT_MS;
}

function durableRunHasStaleExecuteApproved(run: DurableCodingRun | null | undefined, nowMs = Date.now()) {
  if (!run || (run.status !== "running" && run.status !== "pending")) return false;
  const activeRow = durableRunInFlightActiveRow(run);
  if (!activeRow) return false;
  const statuses = new Set([...(run.endpoint_statuses || []), ...(activeRow.endpoint_statuses || [])]);
  if (![...statuses].some((status) => status.startsWith("/v1/verification/diff-preview:200"))) return false;
  if ([...statuses].some((status) => status.startsWith("/v1/actions/execute-approved:"))) return false;
  if ([...statuses].some((status) => status.includes("stale_no_completion") || status.includes(":timeout"))) {
    return false;
  }
  if (!(run.final_summary || "").toLowerCase().includes("preparing apply")) return false;
  const startedAt = Date.parse(
    run.current_step_started_at ||
      run.current_prompt_started_at ||
      activeRow.updated_at ||
      activeRow.started_at ||
      run.updated_at ||
      run.created_at,
  );
  return Number.isFinite(startedAt) && nowMs - startedAt > TRIAL_EXECUTE_APPROVED_STALE_MS;
}

function durableRunHasStaleEditingFiles(run: DurableCodingRun | null | undefined, nowMs = Date.now()) {
  if (!run || (run.status !== "running" && run.status !== "pending")) return false;
  if (!(run.final_summary || "").toLowerCase().includes("editing files")) return false;
  const activeRow = durableRunInFlightActiveRow(run);
  const statuses = new Set([...(run.endpoint_statuses || []), ...(activeRow?.endpoint_statuses || [])]);
  if (![...statuses].some((status) => status.startsWith("/v1/verification/diff-preview:200"))) return false;
  if ([...statuses].some((status) => status.startsWith("/v1/actions/execute-approved:200"))) return false;
  if (
    [...statuses].some(
      (status) =>
        status.includes("stale_no_completion") ||
        status.includes(":timeout") ||
        status.startsWith("/v1/actions/execute-approved:stale"),
    )
  ) {
    return false;
  }
  const startedAt = Date.parse(
    run.current_step_started_at ||
      run.current_prompt_started_at ||
      activeRow?.updated_at ||
      activeRow?.started_at ||
      run.updated_at ||
      run.created_at,
  );
  return Number.isFinite(startedAt) && nowMs - startedAt > TRIAL_EXECUTE_APPROVED_STALE_MS;
}

async function markDurableCodingRunPromptPacketStale(run: DurableCodingRun): Promise<DurableCodingRun | null> {
  const activeRow = durableRunInFlightActiveRow(run);
  if (!activeRow) return null;
  const endpointStatuses = [
    ...new Set([
      ...(activeRow.endpoint_statuses || []),
      "/v1/decisions/prompt-packet:stale_no_completion",
    ]),
  ];
  const promptNumber = activeRow.prompt_id.match(/\d+/)?.[0]?.replace(/^0+/, "") || "current";
  const hasPromptPacket200 = [...endpointStatuses].some((status) =>
    status.startsWith("/v1/decisions/prompt-packet:200"),
  );
  const errorSummary = hasPromptPacket200
    ? `Prompt ${promptNumber} recorded prompt-packet:200 but never reached a terminal suite stage before the stale deadline.`
    : `Prompt ${promptNumber} stayed on prompt-packet:started without a recorded prompt-packet completion before the stale deadline.`;
  const rowResponse = await fetch(
    `/v1/coding/runs/${encodeURIComponent(run.run_id)}/rows/${encodeURIComponent(activeRow.prompt_id)}`,
    {
      body: JSON.stringify({
        ...activeRow,
        endpoint_statuses: endpointStatuses,
        error_summary: errorSummary,
        reason_code: "prompt_packet_stale_no_completion",
        result_label: "NEEDS FIX",
        status: "failed",
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    },
  );
  if (!rowResponse.ok) return null;
  const runResponse = await fetch(`/v1/coding/runs/${encodeURIComponent(run.run_id)}`, {
    body: JSON.stringify({
      current_prompt_id: activeRow.prompt_id,
      endpoint_statuses: [
        ...new Set([...(run.endpoint_statuses || []), "/v1/decisions/prompt-packet:stale_no_completion"]),
      ],
      final_summary: "Stopped after prompt-packet stale/no completion.",
      last_error: errorSummary,
      reason_code: "prompt_packet_stale_no_completion",
      reversal_available: run.rows.some((row) => row.reversal_available),
      reversal_status: run.rows.some((row) => row.reversal_status === "available") ? "available" : "none",
      status: "failed",
    }),
    headers: { "content-type": "application/json" },
    method: "PATCH",
  });
  if (!runResponse.ok) return null;
  const payload = await runResponse.json();
  return payload.run ?? null;
}

async function markDurableCodingRunExecuteApprovedStale(run: DurableCodingRun): Promise<DurableCodingRun | null> {
  const activeRow = durableRunInFlightActiveRow(run);
  if (!activeRow) return null;
  const endpointStatuses = [
    ...new Set([
      ...(activeRow.endpoint_statuses || []),
      "/v1/actions/execute-approved:stale_no_completion",
    ]),
  ];
  const promptNumber = activeRow.prompt_id.match(/\d+/)?.[0]?.replace(/^0+/, "") || "current";
  const errorSummary = `Prompt ${promptNumber} stayed on preparing apply without a recorded execute-approved completion before the stale deadline.`;
  const rowResponse = await fetch(
    `/v1/coding/runs/${encodeURIComponent(run.run_id)}/rows/${encodeURIComponent(activeRow.prompt_id)}`,
    {
      body: JSON.stringify({
        ...activeRow,
        endpoint_statuses: endpointStatuses,
        error_summary: errorSummary,
        reason_code: "execute_approved_stale_no_completion",
        result_label: "NEEDS FIX",
        status: "failed",
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    },
  );
  if (!rowResponse.ok) return null;
  const runResponse = await fetch(`/v1/coding/runs/${encodeURIComponent(run.run_id)}`, {
    body: JSON.stringify({
      current_prompt_id: activeRow.prompt_id,
      endpoint_statuses: [
        ...new Set([...(run.endpoint_statuses || []), "/v1/actions/execute-approved:stale_no_completion"]),
      ],
      final_summary: "Stopped after execute-approved stale/no completion.",
      last_error: errorSummary,
      reason_code: "execute_approved_stale_no_completion",
      reversal_available: run.rows.some((row) => row.reversal_available),
      reversal_status: run.rows.some((row) => row.reversal_status === "available") ? "available" : "none",
      status: "failed",
    }),
    headers: { "content-type": "application/json" },
    method: "PATCH",
  });
  if (!runResponse.ok) return null;
  const payload = await runResponse.json();
  return payload.run ?? null;
}

async function markDurableCodingRunPostApplyStale(run: DurableCodingRun): Promise<DurableCodingRun | null> {
  const promptId = durableRunPendingPromptId(run);
  if (!promptId) return null;
  const activeRow =
    run.rows.find((row) => row.prompt_id === promptId) ?? durableRunInFlightActiveRow(run);
  if (!activeRow) return null;
  const reasonCode = postApplyStaleReasonCode(run);
  const endpointStatuses = [
    ...new Set([
      ...(activeRow.endpoint_statuses || []),
      ...(run.endpoint_statuses || []),
      "/v1/actions/execute-approved:stale_no_completion",
    ]),
  ];
  const promptNumber = promptId.match(/\d+/)?.[0]?.replace(/^0+/, "") || "current";
  const errorSummary = `Prompt ${promptNumber} reached execute-approved without disk/applied proof before the stale deadline (${reasonCode}).`;
  const rowResponse = await fetch(
    `/v1/coding/runs/${encodeURIComponent(run.run_id)}/rows/${encodeURIComponent(promptId)}`,
    {
      body: JSON.stringify({
        ...activeRow,
        endpoint_statuses: endpointStatuses,
        error_summary: errorSummary,
        reason_code: reasonCode,
        result_label: "NEEDS FIX",
        status: "failed",
        step_instrumentation: mergeStepInstrumentation(activeRow.step_instrumentation, {
          last_progress_reason_code: reasonCode,
          result_finalized_at: new Date().toISOString(),
        }),
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    },
  );
  if (!rowResponse.ok) return null;
  const runResponse = await fetch(`/v1/coding/runs/${encodeURIComponent(run.run_id)}`, {
    body: JSON.stringify({
      current_prompt_id: promptId,
      endpoint_statuses: [
        ...new Set([...(run.endpoint_statuses || []), "/v1/actions/execute-approved:stale_no_completion"]),
      ],
      final_summary: "Stopped after post-apply verification stale/no completion.",
      last_error: errorSummary,
      reason_code: reasonCode,
      reversal_available: run.rows.some((row) => row.reversal_available),
      reversal_status: run.rows.some((row) => row.reversal_status === "available") ? "available" : "none",
      status: "failed",
    }),
    headers: { "content-type": "application/json" },
    method: "PATCH",
  });
  if (!runResponse.ok) return null;
  const payload = await runResponse.json();
  return payload.run ?? null;
}

async function markDurableCodingRunEditingFilesStale(run: DurableCodingRun): Promise<DurableCodingRun | null> {
  const promptId = durableRunPendingPromptId(run);
  if (!promptId) return null;
  const activeRow =
    run.rows.find((row) => row.prompt_id === promptId) ?? durableRunInFlightActiveRow(run);
  if (!activeRow) return null;
  const endpointStatuses = [
    ...new Set([
      ...(activeRow.endpoint_statuses || []),
      ...(run.endpoint_statuses || []),
      "/v1/actions/execute-approved:stale_no_completion",
    ]),
  ];
  const promptNumber = promptId.match(/\d+/)?.[0]?.replace(/^0+/, "") || "current";
  const errorSummary = `Prompt ${promptNumber} stayed on Editing files without a recorded execute-approved completion before the stale deadline.`;
  const rowResponse = await fetch(
    `/v1/coding/runs/${encodeURIComponent(run.run_id)}/rows/${encodeURIComponent(promptId)}`,
    {
      body: JSON.stringify({
        ...activeRow,
        endpoint_statuses: endpointStatuses,
        error_summary: errorSummary,
        reason_code: "execute_approved_stale_no_completion",
        result_label: "NEEDS FIX",
        status: "failed",
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    },
  );
  if (!rowResponse.ok) return null;
  const runResponse = await fetch(`/v1/coding/runs/${encodeURIComponent(run.run_id)}`, {
    body: JSON.stringify({
      current_prompt_id: promptId,
      endpoint_statuses: [
        ...new Set([...(run.endpoint_statuses || []), "/v1/actions/execute-approved:stale_no_completion"]),
      ],
      final_summary: "Stopped after Editing files stale/no completion.",
      last_error: errorSummary,
      reason_code: "execute_approved_stale_no_completion",
      reversal_available: run.rows.some((row) => row.reversal_available),
      reversal_status: run.rows.some((row) => row.reversal_status === "available") ? "available" : "none",
      status: "failed",
    }),
    headers: { "content-type": "application/json" },
    method: "PATCH",
  });
  if (!runResponse.ok) return null;
  const payload = await runResponse.json();
  return payload.run ?? null;
}

async function markDurableCodingRunBetweenPromptsStale(run: DurableCodingRun): Promise<DurableCodingRun | null> {
  const nextPromptId = durableRunPendingPromptId(run);
  const resumeAt = Math.min(run.completed_count + 1, run.requested_count);
  const errorSummary = betweenPromptsStaleSummary(run);
  const runResponse = await fetch(`/v1/coding/runs/${encodeURIComponent(run.run_id)}`, {
    body: JSON.stringify({
      current_prompt_id: nextPromptId ?? run.current_prompt_id,
      final_summary: `Paused, ready to resume from prompt ${resumeAt}`,
      last_error: errorSummary,
      reason_code: "between_prompts_runner_lost",
      status: "failed",
    }),
    headers: { "content-type": "application/json" },
    method: "PATCH",
  });
  if (!runResponse.ok) return null;
  const payload = await runResponse.json();
  return payload.run ?? null;
}

async function failDurableRunIfPromptPacketStale(
  run: DurableCodingRun | null | undefined,
  context: "attach" | "poll" = "poll",
) {
  const stalePromptPacket = durableRunHasStalePromptPacket(run);
  const staleExecuteApproved = durableRunHasStaleExecuteApproved(run);
  const staleEditingFiles = durableRunHasStaleEditingFiles(run);
  const stalePostApplyVerification = durableRunHasStalePostApplyVerification(
    run,
    Date.now(),
    TRIAL_EXECUTE_APPROVED_STALE_MS,
  );
  const staleBetweenPrompts = durableRunBetweenPromptsStale(run);
  if (
    !stalePromptPacket &&
    !staleExecuteApproved &&
    !staleEditingFiles &&
    !stalePostApplyVerification &&
    !staleBetweenPrompts
  ) {
    return run ?? null;
  }
  const staleRun = run;
  if (!staleRun) return null;
  if (!reversibleSuiteRunnerLeaseKnown(staleRun.run_id)) {
    return staleRun;
  }
  if (staleBetweenPrompts) {
    // #region agent log
    fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
      body: JSON.stringify({
        sessionId: "0fdea5",
        hypothesisId: "H9",
        location: "CodingCockpitShell.tsx:failDurableRunIfPromptPacketStale",
        message: "between-prompts stale detected",
        data: {
          runId: staleRun.run_id,
          completedCount: staleRun.completed_count,
          finalSummary: staleRun.final_summary,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    return (await markDurableCodingRunBetweenPromptsStale(staleRun)) ?? staleRun;
  }
  if (stalePostApplyVerification) {
    return (await markDurableCodingRunPostApplyStale(staleRun)) ?? staleRun;
  }
  if (staleEditingFiles) {
    return (await markDurableCodingRunEditingFilesStale(staleRun)) ?? staleRun;
  }
  if (staleExecuteApproved) {
    return (await markDurableCodingRunExecuteApprovedStale(staleRun)) ?? staleRun;
  }
  return (await markDurableCodingRunPromptPacketStale(staleRun)) ?? staleRun;
}

async function cancelDurableCodingRunForUserStop(runId: string): Promise<DurableCodingRun | null> {
  const response = await fetch(`/v1/coding/runs/${encodeURIComponent(runId)}`, {
    body: JSON.stringify({
      final_summary: "Stopped by user",
      last_error: "user_clicked_stop_on_synced_run",
      reason_code: "user_stop",
      status: "cancelled",
    }),
    headers: { "content-type": "application/json" },
    method: "PATCH",
  });
  if (!response.ok) return null;
  const payload = await response.json();
  return payload.run ?? null;
}

async function releaseSyncedReversibleSuiteRun(
  runId: string,
  options: { localRunnerActive: boolean; source: "poll" | "user_stop" },
): Promise<DurableCodingRun | null> {
  const response = await fetch(`/v1/coding/runs/${encodeURIComponent(runId)}`, { cache: "no-store" });
  if (!response.ok) return null;
  const payload = await response.json();
  let run = payload.run as DurableCodingRun | null | undefined;
  if (!run) return null;
  if (!options.localRunnerActive) {
    run = (await failDurableRunIfPromptPacketStale(run, options.source === "user_stop" ? "attach" : "poll")) ?? run;
  }
  if (
    options.source === "user_stop" &&
    (run.status === "running" || run.status === "pending")
  ) {
    run = (await cancelDurableCodingRunForUserStop(runId)) ?? run;
  }
  return run;
}

function suiteStateFromDurableRun(run: DurableCodingRun): ReversibleSuiteState {
  const count = (reversibleTrialCounts.includes(run.requested_count as ReversibleTrialCount)
    ? run.requested_count
    : 10) as ReversibleTrialCount;
  const prompts = selectReversibleTrialPrompts(count, "Coder");
  const promptById = new Map(prompts.map((prompt) => [prompt.id, prompt]));
  const staleInterruption = durableRunIsStaleStepInterruption(run);
  const userStopMidSuite = durableRunIsResumableUserStop(run);
  const localRefreshInterruptedInFlightStep = durableRunHasLocalRefreshInterruptedInFlightStep(run);
  const resumableInterruption = staleInterruption || userStopMidSuite || localRefreshInterruptedInFlightStep;
  const resumeRows = resumableInterruption ? durableRunSuccessfulRows(run) : run.rows;
  const results = resumeRows
    .map((row) => reversibleResultFromDurableRow(row, promptById.get(row.prompt_id)))
    .filter((result): result is ReversibleSuitePromptResult => Boolean(result));
  const status = resumableInterruption
    ? "failed"
    : run.status === "running" || run.status === "pending"
      ? "running"
      : run.status === "completed" || run.status === "reverted"
        ? "done"
        : "failed";
  const nowMs = Date.now();
  const suiteStartedAtMs = Date.parse(run.suite_started_at || run.created_at);
  const activeRow = run.current_prompt_id
    ? run.rows.find((row) => row.prompt_id === run.current_prompt_id)
    : run.rows.find((row) => row.status === "running");
  const promptStartedAtMs = Date.parse(
    run.current_prompt_started_at ||
      activeRow?.started_at ||
      activeRow?.updated_at ||
      run.updated_at ||
      run.created_at,
  );
  const stepStartedAtMs = Date.parse(run.current_step_started_at || activeRow?.updated_at || run.updated_at || run.created_at);
  const completedCount = resumableInterruption ? resumeRows.length : run.completed_count;
  return {
    completed: completedCount,
    count,
    currentPrompt:
      run.current_prompt_id && promptById.get(run.current_prompt_id)
        ? `${Math.min(completedCount + 1, count)}/${count}: ${promptById.get(run.current_prompt_id)?.quickTitle}`
        : activeRow && promptById.get(activeRow.prompt_id)
          ? `${Math.min(completedCount + 1, count)}/${count}: ${promptById.get(activeRow.prompt_id)?.quickTitle}`
          : results.length > 0
            ? "Suite finished."
            : "",
    currentPromptElapsedMs: null,
    currentStep: resumableInterruption
      ? `Paused, ready to resume from prompt ${completedCount + 1}`
      : run.final_summary || (status === "running" ? "Active run attached" : "Synced from backend"),
    currentStepStartedAt:
      Number.isFinite(stepStartedAtMs) && status === "running"
        ? performance.now() - Math.max(0, nowMs - stepStartedAtMs)
        : null,
    alreadySatisfied: results.filter((result) => result.visible_result_label === "ALREADY SATISFIED").length,
    expectedNoEdit: results.filter((result) => result.visible_result_label === "NO EDIT EXPECTED").length,
    fail: resumableInterruption
      ? 0
      : results.filter((result) => result.visible_result_label === "FAIL" || result.visible_result_label === "NEEDS FIX").length,
    interruptionReason: resumableInterruption
      ? run.last_error ||
        (userStopMidSuite
          ? "Suite stopped by user before completion; resume from the interrupted prompt."
          : localRefreshInterruptedInFlightStep
            ? "Browser refreshed while the prompt was in flight; resume from the interrupted prompt."
          : (run.final_summary || "").toLowerCase().includes("preparing apply")
            ? "Apply step lost before execute-approved completion; resume from the interrupted prompt."
            : "Prompt-packet lost before provider proof; resume from the interrupted prompt.")
      : run.last_error,
    interruptionSource: staleInterruption
      ? "browser_refresh_or_dev_reload"
      : localRefreshInterruptedInFlightStep
        ? "browser_refresh_or_dev_reload"
      : run.status === "timed_out"
        ? "provider_timeout"
        : run.status === "cancelled"
          ? "user_stop"
          : "none",
    pass: results.filter((result) => result.visible_result_label === "PASS").length,
    provider: run.provider,
    model: run.model || run.model_called_for_generation,
    results,
    reverted: results.filter((result) => result.reverted).length,
    safetyBlock: results.filter((result) => result.visible_result_label === "BLOCKED").length,
    status,
    stopped: run.status === "cancelled",
    suiteFinishedAt: status === "running" ? null : performance.now(),
    suiteId: run.suite_id || run.run_id,
    suiteStartedAt:
      Number.isFinite(suiteStartedAtMs)
        ? performance.now() - Math.max(0, nowMs - suiteStartedAtMs)
        : performance.now(),
    timeout: run.status === "timed_out" ? 1 : results.filter(reversibleResultIsTimeout).length,
    baselineCheckedAt: null,
    baselineAgentLabFiles: [],
    baselineDirtyAgentLabFiles: [],
    baselineUnrevertedReceipts: [],
    baselineCleanForFreshSuite: null,
  };
}

function reversibleResultFromDurableRow(
  row: DurableCodingRunRow,
  prompt: ReversibleTrialPrompt | undefined,
): ReversibleSuitePromptResult | null {
  if (!prompt) return null;
  return {
    allowed_files: prompt.expected_scope,
    applied_changed_files: row.applied_changed_files,
    checks_result: row.checks_result,
    checks_run: row.checks_run,
    disk_changed_files: row.disk_changed_files,
    endpoint_statuses: row.endpoint_statuses || [],
    error_summary: row.error_summary,
    expected_outcome: prompt.expectedOutcome,
    failure_reason: row.error_summary,
    model_called_for_generation: row.model_called_for_generation,
    next_recommended_action: row.error_summary
      ? "Inspect persisted row diagnostics before rerunning."
      : "Review persisted backend run state.",
    prompt,
    provider: "",
    provider_call_made: row.provider_call_made,
    provenance: normalizeTrialResultProvenance(row.provenance),
    preview_changed_files: row.preview_changed_files,
    reverse_diff: row.reverse_diff || "",
    reverse_status_text:
      row.reversal_available && row.reversal_status === "none"
        ? "Revert availability persisted; refresh-safe reverse diff status depends on stored receipt."
        : row.reversal_status || "No applied trial edits to reverse.",
    reverted: row.reversal_status === "reverted",
    reversal_available: row.reversal_available,
    run_id: row.run_id || row.prompt_id,
    selected_target:
      row.applied_changed_files[0] ||
      row.preview_changed_files[0] ||
      row.disk_changed_files[0] ||
      prompt.targetFile,
    target_candidates: prompt.expected_scope,
    visible_result_label: row.result_label as ReversibleSuitePromptResult["visible_result_label"],
    elapsed_ms: null,
  };
}

function durableRowFromReversibleResult(result: ReversibleSuitePromptResult, status: DurableCodingRunStatus): DurableCodingRunRow {
  const promptText = reversibleTrialPromptForMode(result.prompt, modeForTrialCategory(result.prompt.category));
  return {
    prompt_id: result.prompt.id,
    run_id: result.run_id,
    prompt_text: promptText,
    prompt_excerpt: promptText.slice(0, 240),
    status,
    started_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    provider_call_made: result.provider_call_made,
    provenance: normalizeTrialResultProvenance(result.provenance),
    model_called_for_generation: result.model_called_for_generation || "none",
    endpoint_statuses: result.endpoint_statuses,
    reason_code: extractReasonCodeFromSummary(result.error_summary) || result.failure_reason || "",
    generated_diff_present: result.preview_changed_files.length > 0 || result.applied_changed_files.length > 0,
    preview_changed_files: result.preview_changed_files,
    applied_changed_files: result.applied_changed_files,
    disk_changed_files: result.disk_changed_files,
    checks_run: result.checks_run,
    checks_result: result.checks_result,
    reversal_available: result.reversal_available,
    reversal_status: result.reverted ? "reverted" : result.reversal_available ? "available" : "none",
    reverse_diff: result.reverse_diff,
    result_label: result.visible_result_label,
    error_summary: result.error_summary || result.failure_reason,
  };
}

const EMPTY_TRIAL_RESULT_PROVENANCE: DurableCodingRunProvenance = {
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

function normalizeTrialResultProvenance(input: Partial<DurableCodingRunProvenance> | null | undefined): DurableCodingRunProvenance {
  const merged = { ...EMPTY_TRIAL_RESULT_PROVENANCE, ...(input ?? {}) };
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

function trialProvenanceFromPayload(payload: unknown): DurableCodingRunProvenance {
  const record = payload && typeof payload === "object" && !Array.isArray(payload)
    ? (payload as Record<string, unknown>)
    : {};
  const diagnostics = record.coder_diagnostics && typeof record.coder_diagnostics === "object" && !Array.isArray(record.coder_diagnostics)
    ? (record.coder_diagnostics as Partial<DurableCodingRunProvenance>)
    : {};
  return normalizeTrialResultProvenance(diagnostics);
}

function durableRunStatusForResult(result: ReversibleSuitePromptResult): DurableCodingRunStatus {
  if (result.visible_result_label === "REVERTED") return "reverted";
  if (reversibleResultIsTimeout(result)) return "timed_out";
  if (result.visible_result_label === "FAIL" || result.visible_result_label === "NEEDS FIX") return "failed";
  return "completed";
}

function durableRunPatchFromSuite(state: ReversibleSuiteState): Partial<DurableCodingRun> {
  const rows = state.results.map((result) => durableRowFromReversibleResult(result, durableRunStatusForResult(result)));
  const patch: Partial<DurableCodingRun> = {
    benchmark_name: `Messy Coder ${state.count}`,
    completed_count: state.completed,
    final_summary: state.currentStep,
    last_error: state.interruptionReason,
    reason_code: state.status === "running" ? null : undefined,
    model: state.model,
    model_called_for_generation: state.model,
    provider: state.provider,
    provider_call_made: rows.some((row) => row.provider_call_made),
    requested_count: state.count,
    reversal_available: rows.some((row) => row.reversal_available),
    reversal_status: rows.some((row) => row.reversal_status === "available") ? "available" : "none",
    status: durableRunStatusForSuite(state),
  };
  if (rows.length > 0) {
    patch.current_prompt_id = state.results.at(-1)?.prompt.id ?? null;
    patch.rows = rows;
  }
  return patch;
}

async function createDurableCodingRunForSuite(state: ReversibleSuiteState): Promise<DurableCodingRun | null> {
  const response = await fetch("/v1/coding/runs", {
    body: JSON.stringify({
      ...durableRunPatchFromSuite(state),
      run_id: state.suiteId,
      suite_id: state.suiteId,
      suite_started_at: new Date().toISOString(),
      frontend_url: "https://10.0.0.186:3000/coding",
      proxy_url: "https://10.0.0.186:8787",
      started_by_surface: "coding",
      lane: "coder",
    }),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
  if (!response.ok) return null;
  const payload = await response.json();
  return payload.run ?? null;
}

async function patchDurableCodingRunFromSuite(state: ReversibleSuiteState): Promise<DurableCodingRun | null> {
  if (!state.suiteId) return null;
  const response = await fetch(`/v1/coding/runs/${encodeURIComponent(state.suiteId)}`, {
    body: JSON.stringify(durableRunPatchFromSuite(state)),
    headers: { "content-type": "application/json" },
    method: "PATCH",
  });
  if (!response.ok) return null;
  const payload = await response.json();
  return payload.run ?? null;
}

async function markDurableCodingRunCleared(runId: string): Promise<DurableCodingRun | null> {
  try {
    const response = await fetchWithTimeout(
      `/v1/coding/runs/${encodeURIComponent(runId)}`,
      {
        body: JSON.stringify({
          status: "cleared",
          reason_code: "user_cleared_synced_run",
          last_error: null,
          final_summary: "Run cleared from synced coding cloud.",
          reversal_status: "none",
        }),
        headers: { "content-type": "application/json" },
        method: "PATCH",
      },
      TRIAL_DURABLE_ROW_SYNC_TIMEOUT_MS,
    );
    if (!response.ok) return null;
    const payload = await response.json();
    return payload.run ?? null;
  } catch {
    return null;
  }
}

async function postDurableCodingRunRow(
  suiteId: string,
  result: ReversibleSuitePromptResult,
  status: DurableCodingRunStatus,
): Promise<DurableCodingRun | null> {
  const response = await fetch(
    `/v1/coding/runs/${encodeURIComponent(suiteId)}/rows/${encodeURIComponent(result.prompt.id)}`,
    {
      body: JSON.stringify(durableRowFromReversibleResult(result, status)),
      headers: { "content-type": "application/json" },
      method: "POST",
    },
  );
  if (!response.ok) return null;
  const payload = await response.json();
  return payload.run ?? null;
}

async function postDurableCodingRunRowWithTimeout(
  suiteId: string,
  result: ReversibleSuitePromptResult,
  status: DurableCodingRunStatus,
  timeoutMs = TRIAL_DURABLE_ROW_SYNC_TIMEOUT_MS,
): Promise<DurableCodingRun | null> {
  try {
    const response = await fetchWithTimeout(
      `/v1/coding/runs/${encodeURIComponent(suiteId)}/rows/${encodeURIComponent(result.prompt.id)}`,
      {
        body: JSON.stringify(durableRowFromReversibleResult(result, status)),
        headers: { "content-type": "application/json" },
        method: "POST",
      },
      timeoutMs,
    );
    if (!response.ok) return null;
    const payload = await response.json();
    return payload.run ?? null;
  } catch {
    return null;
  }
}

async function patchDurableCodingRunFromSuiteWithTimeout(
  state: ReversibleSuiteState,
  timeoutMs = TRIAL_DURABLE_ROW_SYNC_TIMEOUT_MS,
): Promise<DurableCodingRun | null> {
  if (!state.suiteId) return null;
  try {
    const response = await fetchWithTimeout(
      `/v1/coding/runs/${encodeURIComponent(state.suiteId)}`,
      {
        body: JSON.stringify(durableRunPatchFromSuite(state)),
        headers: { "content-type": "application/json" },
        method: "PATCH",
      },
      timeoutMs,
    );
    if (!response.ok) return null;
    const payload = await response.json();
    return payload.run ?? null;
  } catch {
    return null;
  }
}

async function postDurableCodingRunPromptStatus(
  suiteId: string,
  prompt: ReversibleTrialPrompt,
  status: DurableCodingRunStatus,
  state: ReversibleSuiteState,
): Promise<DurableCodingRun | null> {
  const promptText = reversibleTrialPromptForMode(prompt, modeForTrialCategory(prompt.category));
  const response = await fetch(
    `/v1/coding/runs/${encodeURIComponent(suiteId)}/rows/${encodeURIComponent(prompt.id)}`,
    {
      body: JSON.stringify({
        prompt_id: prompt.id,
        run_id: `${suiteId}:${prompt.id}`,
        prompt_text: promptText,
        prompt_excerpt: promptText.slice(0, 240),
        status,
        current_prompt_started_at: new Date().toISOString(),
        current_step_started_at: new Date().toISOString(),
        provider_call_made: false,
        model_called_for_generation: state.model || "none",
        endpoint_statuses: [],
        reason_code: "",
        generated_diff_present: false,
        preview_changed_files: [],
        applied_changed_files: [],
        disk_changed_files: [],
        checks_run: [],
        checks_result: "",
        reversal_available: false,
        reversal_status: "none",
        result_label: status === "running" ? "RUNNING" : "",
        error_summary: "",
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    },
  );
  if (!response.ok) return null;
  const payload = await response.json();
  return payload.run ?? null;
}

async function postDurableCodingRunPromptProgress(
  suiteId: string,
  prompt: ReversibleTrialPrompt,
  patch: Partial<DurableCodingRunRow>,
  runPatch: Partial<DurableCodingRun> = {},
): Promise<DurableCodingRun | null> {
  const promptText = reversibleTrialPromptForMode(prompt, modeForTrialCategory(prompt.category));
  const rowResponse = await fetch(
    `/v1/coding/runs/${encodeURIComponent(suiteId)}/rows/${encodeURIComponent(prompt.id)}`,
    {
      body: JSON.stringify({
        prompt_id: prompt.id,
        run_id: `${suiteId}:${prompt.id}`,
        prompt_text: promptText,
        prompt_excerpt: promptText.slice(0, 240),
        status: "running",
        result_label: "RUNNING",
        ...patch,
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    },
  );
  if (!rowResponse.ok) return null;
  const runResponse = await fetch(`/v1/coding/runs/${encodeURIComponent(suiteId)}`, {
    body: JSON.stringify({
      current_prompt_id: prompt.id,
      current_step_started_at: new Date().toISOString(),
      status: "running",
      ...runPatch,
    }),
    headers: { "content-type": "application/json" },
    method: "PATCH",
  });
  if (!runResponse.ok) return null;
  const payload = await runResponse.json();
  return payload.run ?? null;
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
    causalStatusAfter: null,
    currentPhase: "waiting for prompt",
    diff: "",
    error: null,
    events: [],
    forbiddenFiles: PROTECTED_FORBIDDEN_FILES,
    isApplying: false,
    isLoading: false,
    model: providerTruth.modelLabel,
    outputHash: null,
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
    traceId: null,
    invocationEventId: null,
    consumerEventId: null,
    consumerSubsystem: null,
    plan2SubsystemIntegrations: [],
    verifierSummary: "Waiting for preview.",
    technicalDetail: null,
  };
}

function selectedRunnerRouteLabel(state: DummyCoder10RunState): string {
  if (state.rawBackendStatus?.startsWith("/v1/")) {
    return state.rawBackendStatus;
  }
  if (state.status === "starting") return "/v1/tasks/long-running starting";
  if (state.status === "request_sent") return "/v1/decisions/prompt-packet request_sent";
  if (state.status === "running") return state.rawBackendStatus ?? "selected runner running";
  if (state.status === "blocked") return state.rawBackendStatus ?? "selected runner blocked";
  if (state.status === "error" || state.status === "timeout") return state.rawBackendStatus ?? "selected runner failed";
  if (state.status === "applied") return state.rawBackendStatus ?? "selected runner applied";
  if (state.status === "complete") return state.rawBackendStatus ?? "selected runner complete";
  return state.rawBackendStatus ?? "selected runner";
}

function selectedRunnerPreviewState(
  state: DummyCoder10RunState,
  prompt: TargetPluginPrompt,
  providerTruth: CodingProviderModelTruth,
): PreviewState | null {
  if (state.status === "idle" || state.status === "cleared" || !state.selectedPromptId) {
    return null;
  }

  const active = state.status === "starting" || state.status === "request_sent" || state.status === "running";
  const blocked = state.status === "blocked";
  const waitingForTaskId = state.status === "starting" && !state.taskId;
  const failed = state.status === "error" || state.status === "timeout";
  const applied = state.status === "applied";
  const complete = state.status === "complete";
  const routeLabel = selectedRunnerRouteLabel(state);
  const base = idlePreviewState();
  const status: PreviewState["status"] = failed
    ? "error"
    : blocked
      ? "blocked"
      : applied
        ? "applied"
        : complete
          ? state.changedFiles.length > 0
            ? "ready"
            : "satisfied"
          : "idle";
  const currentPhase = waitingForTaskId
    ? SELECTED_PROMPT_WAITING_FOR_TASK_ID
    : state.status === "starting"
    ? "Creating selected trial task."
    : active
      ? "Backend request sent. Waiting for model/diff result."
      : blocked
        ? "Selected trial blocked safely."
        : failed
          ? "Selected trial failed before a usable result."
          : applied
            ? "Selected trial applied; review receipt and changed files."
            : "Selected trial result recorded.";

  return {
    ...base,
    allowedFiles: [prompt.allowedWriteRoot],
    applySummary: applied ? state.message : "",
    blocker: blocked ? state.message || state.rawBackendStatus || "Selected trial blocked safely." : null,
    changedFiles: state.changedFiles,
    checks: state.checksRun.length > 0 ? state.checksRun : ["git diff --check"],
    currentPhase,
    error: failed ? state.errorText ?? state.message ?? "Selected trial failed." : null,
    forbiddenFiles: prompt.forbiddenFiles,
    isApplying: false,
    isLoading: active,
    model: providerTruth.modelLabel,
    previewStatus: state.rawBackendStatus ?? state.status,
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
    reasonCode: blocked
      ? state.grader?.resultState ?? state.rawBackendStatus ?? "selected_runner_blocked"
      : failed
        ? state.rawBackendStatus ?? "selected_runner_failed"
        : null,
    requirementSummary: state.verificationStatus ?? (waitingForTaskId ? "Waiting for backend task id." : active ? "Waiting for backend result." : state.message),
    reviewerSummary: blocked
      ? "Selected runner stopped at a blocked boundary."
      : failed
        ? "Selected runner failed before review."
        : active
          ? waitingForTaskId
            ? "Waiting for backend task id."
            : "Waiting for backend result."
          : "Selected runner result recorded.",
    routeCalled: routeLabel,
    selectedTarget: prompt.primaryExpectedTargets[0] ?? prompt.fixtureRoot,
    status,
    targetCandidates: prompt.primaryExpectedTargets,
    targetMatch: true,
    taskId: state.taskId ?? "",
    taskSpecAllowed: true,
    traceId: null,
    invocationEventId: null,
    consumerEventId: null,
    consumerSubsystem: null,
    verifierSummary: state.verificationStatus ?? (waitingForTaskId ? "Waiting for backend task id." : active ? "Waiting for backend result." : "No verification recorded yet."),
    technicalDetail: active
      ? waitingForTaskId
        ? "selected_runner_waiting_for_task_id"
        : "selected_runner_backend_request_sent"
      : blocked
        ? "selected_runner_blocked"
        : failed
          ? "selected_runner_failed"
          : null,
  };
}

function selectedRunnerDisplayText(
  state: DummyCoder10RunState,
  prompt: TargetPluginPrompt,
): { detail: string; title: string } {
  const title = `Coder ${String(prompt.number).padStart(3, "0")} - ${prompt.title}`;
  if (state.status === "starting") {
    return {
      detail: SELECTED_PROMPT_WAITING_FOR_TASK_ID,
      title: "Runner starting",
    };
  }
  if (state.status === "request_sent") {
    return {
      detail: "Runner prompt sent. Waiting for backend result.",
      title: "Runner request sent",
    };
  }
  if (state.status === "running") {
    return {
      detail: "Selected trial is running. Preview has not returned yet.",
      title: "Selected trial running",
    };
  }
  if (state.status === "blocked") {
    return {
      detail: state.message || "Selected trial stopped at a blocked boundary. No hidden apply is shown.",
      title: "Selected trial blocked",
    };
  }
  if (state.status === "error" || state.status === "timeout") {
    return {
      detail: state.errorText ?? state.message ?? "Selected trial failed before a usable result.",
      title: state.status === "timeout" ? "Selected trial timeout" : "Selected trial failed",
    };
  }
  if (state.status === "applied") {
    return {
      detail: state.message || "Selected trial applied; review changed files and receipt before treating it as done.",
      title: "Selected trial applied",
    };
  }
  return {
    detail: state.message || `Selected trial result recorded for ${title}.`,
    title: state.changedFiles.length > 0 ? "Selected trial preview ready" : "Selected trial result",
  };
}

function buildActiveRunDisplay({
  draftReady,
  previewState,
  selectedPrompt,
  selectedRunnerState,
  selectedProviderTruth,
}: {
  draftReady: boolean;
  previewState: PreviewState;
  selectedPrompt: TargetPluginPrompt;
  selectedRunnerState: DummyCoder10RunState;
  selectedProviderTruth: CodingProviderModelTruth;
}): ActiveRunDisplay {
  const composerHasActiveRun =
    previewState.status !== "idle" ||
    previewState.isLoading ||
    previewState.isApplying ||
    previewState.events.length > 0;

  if (!composerHasActiveRun) {
    const selectedPreviewState = selectedRunnerPreviewState(
      selectedRunnerState,
      selectedPrompt,
      selectedProviderTruth,
    );
    if (selectedPreviewState) {
      const selectedText = selectedRunnerDisplayText(selectedRunnerState, selectedPrompt);
      return {
        detail: selectedText.detail,
        pipelineDetail: selectedText.detail,
        previewState: selectedPreviewState,
        routeLabel: selectedRunnerRouteLabel(selectedRunnerState),
        source: "selected-runner",
        taskLabel: selectedRunnerState.taskId ?? "pending selected-trial task",
        title: selectedText.title,
        traceLabel: "not recorded yet",
      };
    }
  }

  const composerText = activeRunPreviewText(previewState, draftReady);
  return {
    detail: composerText.detail,
    pipelineDetail: composerText.detail,
    previewState,
    routeLabel: previewState.routeCalled ?? "waiting for prompt packet",
    source: "composer",
    taskLabel: previewState.taskId || "not created",
    title: composerText.title,
    traceLabel: previewState.traceId ?? "not recorded",
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

function reversibleTrialCountLabel(category: ReversibleTrialCategory, count: ReversibleTrialCount): string {
  return category === "Coder" ? `Messy Coder ${count}` : String(count);
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

export function reverseUnifiedDiff(diff: string): string {
  const lines = diff.split("\n");
  const reversed: string[] = [];
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index] ?? "";
    const nextLine = lines[index + 1] ?? "";
    if (line.startsWith("--- ") && nextLine.startsWith("+++ ")) {
      reversed.push(`--- ${nextLine.slice(4)}`);
      reversed.push(`+++ ${line.slice(4)}`);
      index += 1;
      continue;
    }
    if (line.startsWith("new file mode ")) {
      reversed.push(line.replace("new file mode ", "deleted file mode "));
      continue;
    }
    if (line.startsWith("deleted file mode ")) {
      reversed.push(line.replace("deleted file mode ", "new file mode "));
      continue;
    }
    const indexMatch = line.match(/^index ([0-9a-f]+)\.\.([0-9a-f]+)(.*)$/);
    if (indexMatch) {
      reversed.push(`index ${indexMatch[2]}..${indexMatch[1]}${indexMatch[3] ?? ""}`);
      continue;
    }
    reversed.push(
      (() => {
      if (line.startsWith("+") && !line.startsWith("+++")) {
        return `-${line.slice(1)}`;
      }
      if (line.startsWith("-") && !line.startsWith("---")) {
        return `+${line.slice(1)}`;
      }
      return line;
      })(),
    );
  }
  return reversed.join("\n");
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

export function executeReadyReverseDiff(diff: string): string {
  const lines = diff.split("\n");
  const normalized: string[] = [];
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index] ?? "";
    const nextLine = lines[index + 1] ?? "";
    const oldMatch = line.match(/^--- b\/(.+)$/);
    const newMatch = nextLine.match(/^\+\+\+ a\/(.+)$/);
    if (oldMatch?.[1] && newMatch?.[1] && oldMatch[1] === newMatch[1]) {
      normalized.push(`--- a/${oldMatch[1]}`);
      normalized.push(`+++ b/${newMatch[1]}`);
      index += 1;
      continue;
    }
    normalized.push(line);
  }
  return normalized.join("\n");
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

function appliedRunReceiptsAreEqual(a: AppliedRunReceipt[], b: AppliedRunReceipt[]) {
  return JSON.stringify(a) === JSON.stringify(b);
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
    candidates.add("src/components/coding/CodingCockpitShell.tsx");
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
  if (label === "RUNNING") return "border-blue-300/70 bg-blue-300/15 text-blue-100";
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

function codingStepStatusClass(status: CodingPipelineStepStatus): string {
  if (status === "complete") return "border-emerald-300/40 bg-emerald-300/10 text-emerald-100";
  if (status === "running") return "border-sky-300/40 bg-sky-300/10 text-sky-100";
  if (status === "blocked") return "border-amber-300/40 bg-amber-300/10 text-amber-100";
  if (status === "failed") return "border-rose-300/40 bg-rose-300/10 text-rose-100";
  if (status === "skipped") return "border-slate-300/30 bg-slate-300/10 text-slate-300";
  return "border-[var(--ddv4-pill-border)] text-[var(--ddv4-fg-muted)]";
}

function activeRunPreviewText(
  previewState: PreviewState,
  draftReady: boolean,
): { detail: string; title: string } {
  if (previewState.isApplying) {
    return {
      detail: "Approved diff is being sent through execute-approved. Apply success is not shown until the route returns it.",
      title: "Apply approved diff",
    };
  }
  if (previewState.isLoading) {
    return {
      detail: previewState.currentPhase || "Existing preview route is running. No files have been changed yet.",
      title: previewState.currentPhase === manualTaskPhaseLabels.promptPacket
        ? "Building prompt packet"
        : previewState.currentPhase === manualTaskPhaseLabels.preview
          ? "Previewing diff"
          : "Working",
    };
  }
  if (previewState.status === "ready" && previewState.approvalAvailable) {
    return {
      detail: "Preview is ready. Human approval is required before the apply route can run.",
      title: "Waiting for approval",
    };
  }
  if (previewState.status === "approved") {
    return {
      detail: "Approval is recorded, but files are still unchanged until apply is explicitly run.",
      title: "Apply gated",
    };
  }
  if (previewState.status === "applied") {
    return {
      detail: previewState.outputHash || previewState.traceId
        ? "Apply completed with receipt or trace fields available for review."
        : "Apply completed. Review changed files and verification before treating this as done.",
      title: "Receipt / trace ready",
    };
  }
  if (previewState.status === "satisfied") {
    return {
      detail: previewState.blocker ?? "Coder reported no diff was required. No files were changed.",
      title: "Already satisfied",
    };
  }
  if (isUsefulClarificationBlock(previewState)) {
    return {
      detail: previewState.blocker ?? "The run stopped at a clarification boundary. No files were changed.",
      title: "Clarification blocked",
    };
  }
  if (isExpectedSafetyBlock(previewState) || previewState.status === "blocked") {
    return {
      detail: previewState.blocker ?? "The approval or safety boundary stopped the run. No hidden apply success is shown.",
      title: "Apply blocked",
    };
  }
  if (previewState.status === "error" || previewState.error) {
    return {
      detail: previewState.error ?? "A route, runtime, verifier, or unexpected error stopped this run.",
      title: "Run failed",
    };
  }
  if (draftReady) {
    return {
      detail: "Draft is ready. Start coding will build a prompt packet and preview a diff before any apply.",
      title: "Ready to start",
    };
  }
  return {
    detail: "Ready. Describe a change to build a prompt packet and preview a diff.",
    title: "Ready",
  };
}

function buildCodingPipelineSteps({
  applyPreflightNeedsFix,
  currentChangedFilesDiagnostics,
  previewState,
}: {
  applyPreflightNeedsFix: boolean;
  currentChangedFilesDiagnostics: ReturnType<typeof buildChangedFilesDiagnostics>;
  previewState: PreviewState;
}): CodingPipelineStep[] {
  const hasStarted =
    previewState.status !== "idle" ||
    previewState.isLoading ||
    previewState.isApplying ||
    previewState.events.length > 0;
  const waitingForSelectedTaskId =
    previewState.technicalDetail === "selected_runner_waiting_for_task_id" && !previewState.taskId;
  const hasPreviewDiff =
    Boolean(previewState.diff.trim()) ||
    currentChangedFilesDiagnostics.previewChangedFiles.length > 0;
  const hasPreviewResult =
    hasPreviewDiff ||
    previewState.status === "ready" ||
    previewState.status === "approved" ||
    previewState.status === "applied" ||
    previewState.status === "satisfied";
  const isFailed = previewState.status === "error" || Boolean(previewState.error);
  const isBlocked =
    previewState.status === "blocked" ||
    isExpectedSafetyBlock(previewState) ||
    isUsefulClarificationBlock(previewState) ||
    previewState.reasonCode === "human_rejected_preview" ||
    previewState.reasonCode === "preview_only_no_apply_requested";
  const receiptOrTraceReady = Boolean(
    previewState.traceId ||
      previewState.outputHash ||
      previewState.invocationEventId ||
      previewState.consumerEventId ||
      previewState.appliedAt ||
      // The selected-prompt runner records a real backend taskId on apply and has no trace/hash,
      // so a non-empty taskId on an applied run is a valid receipt anchor (otherwise the Receipt
      // step stays "pending" forever even after a successful applied PASS_DUMMY_PROJECT_INIT).
      (previewState.status === "applied" && previewState.taskId),
  );
  const verificationRecorded =
    previewState.verifierSummary.toLowerCase().includes("passed") ||
    previewState.checks.length > 0 ||
    currentChangedFilesDiagnostics.diskChangedFiles.length > 0;

  return [
    {
      label: "Build prompt packet",
      status: !hasStarted
        ? "pending"
        : previewState.isLoading && !hasPreviewResult
          ? "running"
          : isFailed && !previewState.routeCalled
            ? "failed"
            : isBlocked && !previewState.routeCalled
              ? "blocked"
              : "complete",
      detail: previewState.routeCalled
        ? `Route observed: ${previewState.routeCalled}`
        : hasStarted
          ? previewState.currentPhase
          : "Waiting for a task.",
    },
    {
      label: "Preview diff",
      status: !hasStarted
        ? "pending"
        : waitingForSelectedTaskId
          ? "pending"
        : previewState.isLoading
          ? "running"
          : isFailed && !hasPreviewResult
            ? "failed"
            : isBlocked && !hasPreviewResult
              ? "blocked"
              : hasPreviewResult
                ? "complete"
                : "pending",
      detail: hasPreviewDiff
        ? formatList(currentChangedFilesDiagnostics.previewChangedFiles, "Preview diff has no changed files.")
        : previewState.status === "satisfied"
          ? "No diff required."
          : waitingForSelectedTaskId
            ? "Waiting for backend task id."
          : previewState.isLoading && previewState.taskId
            ? "Waiting for backend result."
          : previewState.blocker ?? previewState.error ?? "No preview diff yet.",
    },
    {
      label: "Check approval boundary",
      status: previewState.status === "approved" || previewState.status === "applied"
        ? "complete"
        : isFailed
          ? "failed"
          : previewState.status === "ready" && previewState.approvalAvailable
            ? "blocked"
            : isBlocked || applyPreflightNeedsFix
              ? "blocked"
              : hasPreviewResult
                ? "complete"
                : "pending",
      detail: previewState.status === "ready" && previewState.approvalAvailable
        ? "Human approval required before apply."
        : applyPreflightNeedsFix
          ? "Apply preflight needs a safer scope."
          : previewState.reasonCode ?? previewState.reviewerSummary,
    },
    {
      label: "Apply only if approved",
      status: previewState.isApplying
        ? "running"
        : previewState.status === "applied"
          ? "complete"
          : previewState.status === "satisfied" || previewState.reasonCode === "preview_only_no_apply_requested"
            ? "skipped"
            : isFailed
              ? "failed"
              : previewState.status === "approved" || (previewState.status === "ready" && previewState.approvalAvailable) || isBlocked
                ? "blocked"
                : "pending",
      detail: previewState.status === "applied"
        ? previewState.applySummary || "Apply route returned applied."
        : previewState.status === "approved"
          ? "Approved; waiting for explicit apply action."
          : previewState.status === "ready" && previewState.approvalAvailable
            ? "Locked behind human approval."
            : "No apply has run.",
    },
    {
      label: "Verify result",
      status: isFailed
        ? "failed"
        : previewState.status === "applied" && !verificationRecorded
          ? "pending"
          : verificationRecorded && hasPreviewResult
            ? "complete"
            : isBlocked
              ? "blocked"
              : "pending",
      detail: previewState.status === "applied" && !verificationRecorded
        ? "Post-apply verification still required."
        : previewState.verifierSummary,
    },
    {
      label: "Receipt / trace",
      status: receiptOrTraceReady
        ? "complete"
        : isFailed
          ? "failed"
          : previewState.status === "idle"
            ? "pending"
            : previewState.status === "satisfied" || isBlocked
              ? "skipped"
              : "pending",
      detail: receiptOrTraceReady
        ? [
            previewState.taskId ? `task ${previewState.taskId}` : "",
            previewState.traceId ? `trace ${previewState.traceId}` : "",
            previewState.outputHash ? `hash ${previewState.outputHash}` : "",
          ].filter(Boolean).join(" | ")
        : "No receipt or trace field recorded yet.",
    },
  ];
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

export type CodingCockpitShellProps = {
  /** A constrained host surface may present the canonical lifecycle without its global navigation. */
  embedded?: boolean;
};

export function CodingCockpitShell({ embedded = false }: CodingCockpitShellProps = {}) {
  const stopReversibleSuiteAfterCurrentRef = useRef(false);
  const suiteFetchAbortRef = useRef<AbortController | null>(null);
  const selectedPromptAbortRef = useRef<AbortController | null>(null);
  const reversibleSuiteClearVersionRef = useRef(0);
  const localReversibleSuiteRunningRef = useRef(false);
  const autoResumeSuiteIdRef = useRef("");
  const [task, setTask] = useState("");
  const [targetFile, setTargetFile] = useState("");
  const [allowedFiles, setAllowedFiles] = useState("");
  const [expectedChecks, setExpectedChecks] = useState("git diff --check");
  const [composerMode, setComposerMode] = useState<ComposerMode>("coding");
  const [designStudioComposerState, setDesignStudioComposerState] = useState<DesignStudioComposerState>(
    () => idleDesignStudioComposerState(),
  );
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
  const [trialRunnerMode, setTrialRunnerMode] = useState<TrialRunnerMode>("individual");
  const [reversiblePromptsCopyStatus, setReversiblePromptsCopyStatus] = useState("");
  const [reversibleSuiteCopyStatus, setReversibleSuiteCopyStatus] = useState("");
  const [reversibleSuiteState, setReversibleSuiteState] = useState<ReversibleSuiteState>(
    () => defaultReversibleSuiteState(),
  );
  const [reversibleTrialCount, setReversibleTrialCount] = useState<ReversibleTrialCount>(10);
  const [selectedDummyCoderPromptId, setSelectedDummyCoderPromptId] = useState(codingTargetPlugin.prompts[0].id);
  const [dummyCoderRunCopyStatus, setDummyCoderRunCopyStatus] = useState("");
  const [dummyCoderRunState, setDummyCoderRunState] = useState<DummyCoder10RunState>(
    () => defaultDummyCoderRunState(),
  );
  const [operatorCredential, setOperatorCredential] = useState("");
  const [operatorCsrf, setOperatorCsrf] = useState("");
  const [operatorSession, setOperatorSession] = useState<{ expiresAt: string; message: string; status: "unauthenticated" | "authenticating" | "authenticated" | "expiring" | "expired" | "revoked" | "failed" }>({ expiresAt: "", message: "Operator authentication required before approval.", status: "unauthenticated" });
  const [dummyCoderStorageHydrated, setDummyCoderStorageHydrated] = useState(process.env.NODE_ENV === "test");
  const [composerTiming, setComposerTiming] = useState<ComposerTimingState>({
    diffPreviewMs: null,
    promptPacketMs: null,
    runStartedAt: null,
    totalMs: null,
  });
  const [designReportCopyStatus, setDesignReportCopyStatus] = useState("");
  const [combinedCopyStatus, setCombinedCopyStatus] = useState("");
  const [appliedRunReceipts, setAppliedRunReceipts] = useState<AppliedRunReceipt[]>([]);
  const appliedRunReceiptsRef = useRef<AppliedRunReceipt[]>([]);
  const [promptHistory, setPromptHistory] = useState<string[]>([]);
  const [lastPromptSnapshot, setLastPromptSnapshot] = useState("");
  const [reversalStatus, setReversalStatus] = useState("");
  const [isReverting, setIsReverting] = useState(false);
  const [backgroundCleanupActive, setBackgroundCleanupActive] = useState(false);
  const [hasBrowserMounted, setHasBrowserMounted] = useState(process.env.NODE_ENV === "test");
  const [selectedProviderTruth, setSelectedProviderTruth] = useState<CodingProviderModelTruth>(() =>
    selectedProviderModelTruth(),
  );
  const [sourceProxyReachable, setSourceProxyReachable] = useState(process.env.NODE_ENV === "test");
  const [ollamaStoragePath, setOllamaStoragePath] = useState<string | null>(null);
  const [backendRunSync, setBackendRunSync] = useState<BackendRunSyncState>({
    lastSyncedAt: null,
    message: "No active run",
    runId: "",
    status: "idle",
  });
  const [agentLabBaselineSnapshot, setAgentLabBaselineSnapshot] = useState<AgentLabBaselineSnapshot | null>(null);
  const [agentLabBaselineLoadState, setAgentLabBaselineLoadState] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle");
  const [agentLabBaselineLoadError, setAgentLabBaselineLoadError] = useState("");
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
    const storedDummyCoderRun = loadStoredDummyCoderRunState();
    if (
      storedDummyCoderRun.selectedPromptId &&
      codingTargetPlugin.prompts.some((prompt) => prompt.id === storedDummyCoderRun.selectedPromptId)
    ) {
      setSelectedDummyCoderPromptId(storedDummyCoderRun.selectedPromptId);
    }
    setDummyCoderRunState(storedDummyCoderRun);
    setDummyCoderStorageHydrated(true);
    setAppliedRunReceipts(loadStoredAppliedRunReceipts());
    setPromptHistory(loadPromptHistory());
    setHasBrowserMounted(true);
    void refreshAgentLabBaseline();
  }, []);

  async function authenticateOperator() {
    const credential = operatorCredential;
    setOperatorCredential("");
    if (!credential.trim()) {
      setOperatorSession({ expiresAt: "", message: "Enter the operator credential to authenticate.", status: "failed" });
      return;
    }
    setOperatorSession({ expiresAt: "", message: "Authenticating operator session…", status: "authenticating" });
    try {
      const response = await fetchWithTimeout("/v1/operator/session", { body: JSON.stringify({ credential }), headers: { "content-type": "application/json" }, method: "POST" }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
      const payload = asRecord(await readJson(response));
      const csrf = stringValue(payload.csrf);
      const expiresAt = stringValue(payload.expires_at) ?? "";
      if (!response.ok || !csrf || !expiresAt) throw new Error(stringValue(payload.reason_code) ?? "operator_session_failed");
      setOperatorCsrf(csrf);
      setOperatorSession({ expiresAt, message: "Authenticated operator session. Approval remains server-bound.", status: "authenticated" });
    } catch (error) {
      setOperatorCsrf("");
      setOperatorSession({ expiresAt: "", message: error instanceof Error ? error.message : "operator_session_failed", status: "failed" });
    }
  }

  async function revokeOperator() {
    if (!operatorCsrf) return;
    try {
      const response = await fetchWithTimeout("/v1/operator/session", { headers: { "x-spiritos-csrf": operatorCsrf }, method: "DELETE" }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
      const payload = asRecord(await readJson(response));
      if (!response.ok) throw new Error(stringValue(payload.reason_code) ?? "operator_session_revoke_failed");
      setOperatorCsrf("");
      setOperatorSession({ expiresAt: "", message: "Operator session revoked.", status: "revoked" });
    } catch (error) {
      setOperatorSession((current) => ({ ...current, message: error instanceof Error ? error.message : "operator_session_revoke_failed", status: "failed" }));
    }
  }

  function requireOperatorCsrf() {
    if (operatorSession.status !== "authenticated" || !operatorCsrf) throw new Error("operator_session_required");
    return operatorCsrf;
  }

  useEffect(() => {
    appliedRunReceiptsRef.current = appliedRunReceipts;
  }, [appliedRunReceipts]);

  useEffect(() => {
    if (!dummyCoderStorageHydrated) return;
    storeDummyCoderRunState(dummyCoderRunState);
  }, [dummyCoderRunState, dummyCoderStorageHydrated]);

  useEffect(() => {
    let cancelled = false;
    async function attachBackendRun() {
      setBackendRunSync((current) => ({ ...current, message: "Syncing backend run state", status: "loading" }));
      try {
        const activeResponse = await fetch("/v1/coding/runs/active", { cache: "no-store" });
        const activePayload = activeResponse.ok ? await activeResponse.json() : {};
        let run = activePayload.run as DurableCodingRun | null | undefined;
        let cloudCleared = false;
        if (!run) {
          const recentResponse = await fetch("/v1/coding/runs/recent?limit=1", { cache: "no-store" });
          const recentPayload = recentResponse.ok ? await recentResponse.json() : {};
          run = Array.isArray(recentPayload.runs) ? recentPayload.runs[0] : null;
        }
        if (!durableRunIsVisibleInCodingCloud(run)) {
          cloudCleared = run?.status === "cleared";
          run = null;
        }
        if (!localReversibleSuiteRunningRef.current) {
          run = await failDurableRunIfPromptPacketStale(run, "attach");
        }
        if (cancelled) return;
        if (!run) {
          if (cloudCleared) {
            reversibleSuiteClearVersionRef.current += 1;
            clearStoredReversibleSuiteState();
            setReversibleSuiteState(defaultReversibleSuiteState());
          }
          setBackendRunSync({
            lastSyncedAt: new Date().toISOString(),
            message: cloudCleared ? "Run cleared from coding cloud" : "No active run",
            runId: "",
            status: "synced",
          });
          return;
        }
        const syncedState = suiteStateFromDurableRun(run);
        setReversibleTrialCount(syncedState.count);
        setReversibleSuiteState((current) => {
          if (current.status === "running" || current.status === "stopping") return current;
          if (!shouldAttachDurableRunToUi(run, current)) return current;
          return syncedState;
        });
        setBackendRunSync({
          lastSyncedAt: new Date().toISOString(),
          message: run.status === "running" || run.status === "pending" ? "Active run attached" : "Synced from backend",
          runId:
            run.status === "running" || run.status === "pending" || shouldAttachDurableRunToUi(run, reversibleSuiteState)
              ? run.run_id
              : "",
          status: run.status === "running" || run.status === "pending" ? "attached" : "synced",
        });
      } catch (error) {
        if (cancelled) return;
        setBackendRunSync({
          lastSyncedAt: null,
          message: error instanceof Error ? error.message : "Backend run sync failed",
          runId: "",
          status: "error",
        });
      }
    }
    void attachBackendRun();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!backendRunSync.runId) return;
    const interval = window.setInterval(() => {
      void (async () => {
        try {
          const response = await fetch(`/v1/coding/runs/${encodeURIComponent(backendRunSync.runId)}`, {
            cache: "no-store",
          });
          if (!response.ok) return;
          const payload = await response.json();
          let run = payload.run as DurableCodingRun | null | undefined;
          if (!run) return;
          if (!localReversibleSuiteRunningRef.current) {
            run = await failDurableRunIfPromptPacketStale(run);
          }
          if (!run) return;
          if (run.status === "cleared") {
            reversibleSuiteClearVersionRef.current += 1;
            clearStoredReversibleSuiteState();
            setReversibleSuiteState(defaultReversibleSuiteState());
            setBackendRunSync({
              lastSyncedAt: new Date().toISOString(),
              message: "Run cleared from another device",
              runId: "",
              status: "synced",
            });
            return;
          }
          if (!localReversibleSuiteRunningRef.current) {
            setReversibleSuiteState((current) => {
              if (current.suiteId && current.suiteId !== run.suite_id && current.suiteId !== run.run_id) return current;
              if (!shouldAttachDurableRunToUi(run, current)) return current;
              return suiteStateFromDurableRun(run);
            });
          }
          setBackendRunSync((current) => ({
            lastSyncedAt: new Date().toISOString(),
            message: run.status === "running" || run.status === "pending" ? "Active run attached" : "Synced from backend",
            runId:
              run.status === "running" || run.status === "pending"
                ? run.run_id
                : current.runId && current.runId === run.run_id
                  ? run.run_id
                  : "",
            status: run.status === "running" || run.status === "pending" ? "attached" : "synced",
          }));
        } catch {
          setBackendRunSync((current) => ({ ...current, message: "Backend run polling failed", status: "error" }));
        }
      })();
    }, 3500);
    return () => window.clearInterval(interval);
  }, [backendRunSync.runId]);

  useEffect(() => {
    if (backendRunSync.runId) return;
    if (reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping") return;
    let cancelled = false;
    async function pollActiveBackendRun() {
      try {
        const response = await fetch("/v1/coding/runs/active", { cache: "no-store" });
        if (!response.ok) return;
        const payload = await response.json();
        let run = payload.run as DurableCodingRun | null | undefined;
        if (cancelled || !durableRunIsVisibleInCodingCloud(run) || !run) return;
        if (!localReversibleSuiteRunningRef.current) {
          run = await failDurableRunIfPromptPacketStale(run);
        }
        if (cancelled || !durableRunIsVisibleInCodingCloud(run) || !run) return;
        const syncedState = suiteStateFromDurableRun(run);
        if (!shouldAttachDurableRunToUi(run, syncedState)) return;
        setReversibleTrialCount(syncedState.count);
        if (!localReversibleSuiteRunningRef.current) {
          setReversibleSuiteState((current) => {
            if (current.status === "idle" && current.results.length === 0 && !current.suiteId) {
              return current;
            }
            return syncedState;
          });
        }
        setBackendRunSync({
          lastSyncedAt: new Date().toISOString(),
          message: "Active run attached",
          runId: run.run_id,
          status: "attached",
        });
      } catch {
        if (!cancelled) {
          setBackendRunSync((current) => ({ ...current, message: "Waiting for backend run", status: "synced" }));
        }
      }
    }
    const interval = window.setInterval(() => {
      void pollActiveBackendRun();
    }, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [backendRunSync.runId, reversibleSuiteState.status]);

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
    if (
      !shouldClearStaleLocalTrialStateAfterCloudClear({
        agentLabBaselineClean: agentLabBaselineSnapshot?.baseline_clean_for_fresh_suite,
        agentLabBaselineLoadState,
        appliedRunReceipts: appliedRunReceiptsRef.current,
        backendRunSync,
        localRunnerActive: localReversibleSuiteRunningRef.current,
        reversibleSuiteState,
      })
    ) {
      return;
    }
    reversibleSuiteClearVersionRef.current += 1;
    clearStoredReversibleSuiteState();
    updateAppliedRunReceipts((receipts) => receipts.filter((receipt) => !receipt.id.startsWith("trial-suite:")));
    setReversibleSuiteState(defaultReversibleSuiteState());
    setReversibleSuiteCopyStatus(
      "Cleared stale local trial state because the cloud run is clear and Agent Lab baseline is clean.",
    );
  }, [
    agentLabBaselineLoadState,
    agentLabBaselineSnapshot?.baseline_clean_for_fresh_suite,
    backendRunSync.runId,
    backendRunSync.status,
    reversibleSuiteState.results.length,
    reversibleSuiteState.status,
    reversibleSuiteState.suiteId,
  ]);

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
        .map((result) => receiptForSuiteReverseResult(result, appliedRunReceiptsRef.current));
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
  }, [reversibleSuiteState.results.length, reversibleSuiteState.status, reversibleSuiteState.suiteId]);

  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    if (reversibleSuiteState.status === "idle" && reversibleSuiteState.results.length === 0) {
      return;
    }
    storeReversibleSuiteState(reversibleSuiteState);
  }, [reversibleSuiteState]);

  async function clearReversibleSuitePanel(options: { syncBackend?: boolean } = {}) {
    const syncBackend = options.syncBackend ?? true;
    const runId = backendRunSync.runId || reversibleSuiteState.suiteId;
    reversibleSuiteClearVersionRef.current += 1;
    clearStoredReversibleSuiteState();
    updateAppliedRunReceipts((receipts) =>
      receipts.filter((receipt) => !receipt.id.startsWith("trial-suite:") && !receipt.id.startsWith("selected-prompt:")),
    );
    setReversibleSuiteState(defaultReversibleSuiteState());
    setBackendRunSync({
      lastSyncedAt: new Date().toISOString(),
      message: "No active run",
      runId: "",
      status: "synced",
    });
    setReversibleSuiteCopyStatus("Cleared trial suite results. Run again when ready.");
    clearDummyCoder10RunState();
    if (syncBackend && runId) {
      const clearedRun = await markDurableCodingRunCleared(runId);
      if (!clearedRun) {
        setBackendRunSync({
          lastSyncedAt: new Date().toISOString(),
          message: "Backend clear timed out or failed",
          runId: "",
          status: "error",
        });
        setReversibleSuiteCopyStatus(
          "Cleared the local panel, but backend clear timed out or failed. Refresh should not reattach this panel; retry Clear if the backend still shows an active run.",
        );
      }
    }
  }

  async function resetPausedSyncedSuiteNow(copyStatus: string) {
    await clearReversibleSuitePanel({ syncBackend: true });
    const cleanState = defaultReversibleSuiteState();
    setReversibleSuiteState(cleanState);
    storeReversibleSuiteState(cleanState);
    setReversibleSuiteCopyStatus(copyStatus);
  }

  async function drainAgentLabCleanupToClean(
    initialNote = "",
    options: { forceAgentLabSweep?: boolean } = {},
  ): Promise<string> {
    let latestNote = initialNote;
    const shouldSweepAgentLab = options.forceAgentLabSweep || reversibleTrialCategory === "Coder";
    for (let pass = 1; pass <= TRIAL_CLEANUP_DRAIN_MAX_PASSES; pass += 1) {
      const routeReady = await waitForV1RoutesAfterHmr({
        delayMs: 500,
        maxAttempts: TRIAL_CLEANUP_ROUTE_HEALTH_ATTEMPTS,
      });
      if (!routeReady.ok) {
        const message =
          "Reverse completed, waiting for Next route rebuild before confirming Agent Lab cleanup.";
        setReversibleSuiteCopyStatus(message);
        latestNote = message;
      }

      const refreshed = await refreshAgentLabBaseline();
      if (refreshed?.baseline_clean_for_fresh_suite) {
        const cleanState = defaultReversibleSuiteState();
        setReversibleSuiteState(cleanState);
        clearStoredReversibleSuiteState();
        const cleanNote =
          latestNote && latestNote.toLowerCase().includes("clean")
            ? latestNote
            : "Agent-lab cleanup finished. Workspace is clean for a fresh Coder benchmark.";
        setReversibleSuiteCopyStatus(cleanNote);
        return cleanNote;
      }

      if (!shouldSweepAgentLab) {
        break;
      }

      const dirtyCount = refreshed?.baseline_dirty_agent_lab_files.length ?? 0;
      setReversibleSuiteCopyStatus(
        dirtyCount > 0
          ? `Reverse completed; cleanup pass ${pass}/${TRIAL_CLEANUP_DRAIN_MAX_PASSES} removing ${dirtyCount} agent-lab leftover file(s)...`
          : `Reverse completed; cleanup pass ${pass}/${TRIAL_CLEANUP_DRAIN_MAX_PASSES} checking Agent Lab baseline...`,
      );
      latestNote = await sweepAgentLabLeftoverFilesViaServer();
    }

    const finalSnapshot = await refreshAgentLabBaseline();
    if (finalSnapshot?.baseline_clean_for_fresh_suite) {
      const cleanState = defaultReversibleSuiteState();
      setReversibleSuiteState(cleanState);
      clearStoredReversibleSuiteState();
      const cleanNote =
        latestNote && latestNote.toLowerCase().includes("clean")
          ? latestNote
          : "Agent-lab cleanup finished. Workspace is clean for a fresh Coder benchmark.";
      setReversibleSuiteCopyStatus(cleanNote);
      return cleanNote;
    }

    const dirtyCount = finalSnapshot?.baseline_dirty_agent_lab_files.length ?? 0;
    const dirtyNote =
      dirtyCount > 0
        ? `Reverse completed but Agent Lab still has ${dirtyCount} leftover file(s). Retry cleanup or inspect copied diagnostics.`
        : "Reverse completed but Agent Lab baseline could not be confirmed. Retry cleanup after route health stabilizes.";
    setReversibleSuiteCopyStatus(dirtyNote);
    return dirtyNote;
  }

  async function handleCleanUpTrialRunner() {
    if (backgroundCleanupActive && !isReverting) {
      setBackgroundCleanupActive(false);
    }
    if (isReverting || reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping") {
      return;
    }
    const selectedPromptReceipt = selectedPromptReceiptFromState();
    if (selectedPromptReceipt) {
      setBackgroundCleanupActive(true);
      setReversibleSuiteCopyStatus("Undoing the selected-prompt edit and verifying the fixed dummy fixture reset...");
      try {
        await handleRevertReceipt(selectedPromptReceipt);
        const resetNote = await resetDummyProductSiteViaServer();
        await clearReversibleSuitePanel({ syncBackend: true });
        clearDummyCoder10RunState("Selected-prompt Undo and fixed fixture reset verified. Results cleared.");
        setReversibleSuiteCopyStatus(
          `Selected-prompt Undo verified. ${resetNote} Trial Runner results cleared.`,
        );
      } catch (error) {
        setReversibleSuiteCopyStatus(
          error instanceof Error ? error.message : "Selected-prompt Undo or fixed fixture reset failed.",
        );
      } finally {
        setBackgroundCleanupActive(false);
      }
      return;
    }
    if (dummyCoderRunState.status !== "idle" && dummyCoderRunState.status !== "cleared") {
      setBackgroundCleanupActive(true);
      setReversibleSuiteCopyStatus("Verifying the fixed dummy fixture reset before clearing selected-prompt state...");
      try {
        const resetNote = await resetDummyProductSiteViaServer();
        clearDummyCoder10RunState();
        setReversibleSuiteCopyStatus(`${resetNote} Selected-prompt result cleared; no applied receipt was recorded.`);
      } catch (error) {
        setReversibleSuiteCopyStatus(
          error instanceof Error
            ? error.message
            : "Fixed dummy fixture reset failed; selected-prompt state was kept visible.",
        );
      } finally {
        setBackgroundCleanupActive(false);
      }
      return;
    }
    const baseline = await refreshAgentLabBaseline();
    const resultsSnapshot = reversibleSuiteState.results;
    const suiteSnapshot = {
      model: reversibleSuiteState.model,
      provider: reversibleSuiteState.provider,
      suiteId: reversibleSuiteState.suiteId,
    };
    const pendingRevert = suitePendingRevertCount > 0;
    const orphanReceipts = orphanUnrevertedTrialReceipts.length;
    const categorySnapshot = reversibleTrialCategory;
    const receiptsSnapshot = [...appliedRunReceiptsRef.current];
    const hasLeftovers = Boolean(baseline && !baseline.baseline_clean_for_fresh_suite);
    const needsReceiptReverse = pendingRevert || orphanReceipts > 0 || resultsSnapshot.length > 0;
    const pausedSyncedSuite =
      reversibleSuiteStateCanResume(reversibleSuiteState) &&
      Boolean(reversibleSuiteState.suiteId || backendRunSync.runId);

    if (needsReceiptReverse) {
      setBackgroundCleanupActive(true);
      await clearReversibleSuitePanel();
      setReversibleSuiteCopyStatus("UI cleared; reversing trial edits in background...");
      const reverseWork = pendingRevert || resultsSnapshot.length > 0
        ? handleReverseRemainingTrialEdits({
            agentLabFullCleanup: categorySnapshot === "Coder",
            appliedReceiptsOverride: receiptsSnapshot,
            clearSuiteAfter: false,
            resultsOverride: resultsSnapshot,
            suiteSnapshot,
          })
        : handleRevertAllTrialRuns({ clearSuiteAfter: false });
      const reversePromise = Promise.race([
        reverseWork,
        new Promise<string>((_, reject) => {
          window.setTimeout(
            () => reject(new Error("Background trial reverse timed out after 120s.")),
            120_000,
          );
        }),
      ]);
      void reversePromise
        .then(async (note) => {
          if (categorySnapshot === "Coder") {
            await drainAgentLabCleanupToClean(note ?? "", { forceAgentLabSweep: true });
            return;
          }
          if (note) {
            setReversibleSuiteCopyStatus(note);
          }
          await refreshAgentLabBaseline();
        })
        .catch((error) => {
          setReversibleSuiteCopyStatus(
            error instanceof Error ? error.message : "Background trial reverse failed after UI clear.",
          );
        })
        .finally(() => {
          setBackgroundCleanupActive(false);
        });
      return;
    }

    if (hasLeftovers && baseline) {
      setBackgroundCleanupActive(true);
      try {
        if (pausedSyncedSuite) {
          await resetPausedSyncedSuiteNow("Paused suite cleared. Removing agent-lab leftovers...");
        }
        setReversibleSuiteCopyStatus(
          `Removing ${baseline.baseline_dirty_agent_lab_files.length} agent-lab leftover file(s)...`,
        );
        const note = await sweepAgentLabLeftoverFilesViaServer();
        if (!pausedSyncedSuite) {
          await clearReversibleSuitePanel({ syncBackend: true });
        }
        await drainAgentLabCleanupToClean(note, { forceAgentLabSweep: true });
      } catch (error) {
        setReversibleSuiteCopyStatus(
          error instanceof Error ? error.message : "Agent-lab leftover cleanup failed.",
        );
      } finally {
        setIsReverting(false);
        setBackgroundCleanupActive(false);
        await refreshAgentLabBaseline();
      }
      return;
    }

    if (pausedSyncedSuite) {
      await resetPausedSyncedSuiteNow("Paused suite cleared. Run again when ready.");
      await refreshAgentLabBaseline();
      return;
    }

    if (categorySnapshot === "Coder" && !baseline) {
      setBackgroundCleanupActive(true);
      setIsReverting(true);
      setReversibleSuiteCopyStatus("Retrying agent-lab cleanup through server sweep...");
      try {
        const note = await sweepAgentLabLeftoverFilesViaServer();
        const refreshed = await refreshAgentLabBaseline();
        setReversibleSuiteCopyStatus(note);
        if (refreshed?.baseline_clean_for_fresh_suite) {
          const cleanState = defaultReversibleSuiteState();
          setReversibleSuiteState(cleanState);
          storeReversibleSuiteState(cleanState);
        }
      } catch (error) {
        setReversibleSuiteCopyStatus(
          error instanceof Error ? error.message : "Agent-lab leftover cleanup failed.",
        );
      } finally {
        setIsReverting(false);
        setBackgroundCleanupActive(false);
        await refreshAgentLabBaseline();
      }
      return;
    }

    await clearReversibleSuitePanel();
    setReversibleSuiteCopyStatus("Cleared trial suite results. Run again when ready.");
    await refreshAgentLabBaseline();
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
          setAppliedRunReceipts((current) => {
            if (appliedRunReceiptsAreEqual(current, payload.receipts ?? [])) {
              return current;
            }
            storeAppliedRunReceipts(payload.receipts ?? []);
            return payload.receipts ?? [];
          });
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
  const agentLabHasLeftovers =
    agentLabBaselineSnapshot !== null && !agentLabBaselineSnapshot.baseline_clean_for_fresh_suite;
  const currentSuiteAgentLabFileClassification = useMemo(
    () =>
      classifyCurrentSuiteAgentLabFiles({
        completedPromptChangedFiles: reversibleSuiteState.results
          .flatMap((result) => [
            result.selected_target,
            ...result.applied_changed_files,
            ...result.disk_changed_files,
            ...result.preview_changed_files,
            ...result.target_candidates,
          ]),
        dirtyAgentLabFiles: agentLabBaselineSnapshot?.baseline_dirty_agent_lab_files ?? [],
      }),
    [agentLabBaselineSnapshot?.baseline_dirty_agent_lab_files, reversibleSuiteState.results],
  );
  const agentLabHasStaleLeftoversOutsideCurrentSuite =
    currentSuiteAgentLabFileClassification.staleLeftoverFiles.length > 0;
  // Baseline wording must name the fixture that is actually dirty. The probe covers both the
  // /agent-lab area and the LumaCart dummy-product-site fixture, so generic "Agent Lab
  // baseline dirty" wording is wrong when the only leftovers are LumaCart fixture files.
  const dirtyBaselineFileSplit = useMemo(() => {
    const dirty = agentLabBaselineSnapshot?.baseline_dirty_agent_lab_files ?? [];
    const agentLabFiles = dirty.filter((path) => isAgentLabTrialPath(path));
    const dummyProductSiteFiles = dirty.filter((path) => isDummyProductSiteTrialPath(path));
    return { agentLabFiles, dummyProductSiteFiles };
  }, [agentLabBaselineSnapshot?.baseline_dirty_agent_lab_files]);
  const dirtyBaselineScope =
    dirtyBaselineFileSplit.dummyProductSiteFiles.length > 0 && dirtyBaselineFileSplit.agentLabFiles.length === 0
      ? "dummy-product-site"
      : dirtyBaselineFileSplit.agentLabFiles.length > 0 && dirtyBaselineFileSplit.dummyProductSiteFiles.length === 0
        ? "agent-lab"
        : "mixed";
  const agentLabBaselineBlocksRun =
    reversibleTrialCategory === "Coder" &&
    (agentLabBaselineLoadState !== "ready" || agentLabHasLeftovers);
  const reversibleSuiteCanResume = reversibleSuiteStateCanResume(reversibleSuiteState);
  const reversibleSuiteResumeBlocked =
    isReverting ||
    backgroundCleanupActive ||
    reversibleSuiteBusy ||
    agentLabHasStaleLeftoversOutsideCurrentSuite;
  const reversibleSuiteResumeBlockedMessage =
    isReverting || backgroundCleanupActive
      ? "Cleanup/reverse is still running. Wait before resuming the suite."
      : reversibleSuiteBusy
        ? "Trial suite is still running. Wait for the current prompt to finish."
        : agentLabHasStaleLeftoversOutsideCurrentSuite
          ? `Resume blocked by ${currentSuiteAgentLabFileClassification.staleLeftoverFiles.length} stale Agent Lab leftover file(s) outside this suite: ${currentSuiteAgentLabFileClassification.staleLeftoverFiles.join(", ")}`
          : "";
  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    if (localReversibleSuiteRunningRef.current) return;
    if (!reversibleSuiteStateCanResume(reversibleSuiteState)) return;
    if (!reversibleSuiteState.suiteId) return;
    if (!reversibleSuiteRunnerLeaseKnown(reversibleSuiteState.suiteId)) return;
    if (reversibleSuiteState.completed >= reversibleSuiteState.count) return;
    if (agentLabHasStaleLeftoversOutsideCurrentSuite) return;
    const resumeKey = `${reversibleSuiteState.suiteId}:${reversibleSuiteState.completed}`;
    if (autoResumeSuiteIdRef.current === resumeKey) return;
    autoResumeSuiteIdRef.current = resumeKey;
    setReversibleSuiteCopyStatus(
      `Auto-resuming suite ${reversibleSuiteState.suiteId}: ${reversibleSuiteState.completed}/${reversibleSuiteState.count} complete.`,
    );
    void handleRunReversibleSuite(reversibleSuiteState, { forceResume: true });
  }, [
    agentLabHasStaleLeftoversOutsideCurrentSuite,
    reversibleSuiteState.completed,
    reversibleSuiteState.count,
    reversibleSuiteState.status,
    reversibleSuiteState.suiteId,
  ]);
  const hasReversibleSuiteDiagnostics =
    reversibleSuiteState.status !== "idle" &&
    (reversibleSuiteState.results.length > 0 ||
      Boolean(reversibleSuiteState.suiteId) ||
      Boolean(reversibleSuiteState.currentPrompt) ||
      Boolean(reversibleSuiteState.interruptionReason) ||
      Boolean(backendRunSync.runId));
  const trialRunnerBlock = trialRunnerRunBlocked({
    backgroundCleanupActive,
    isReverting,
    orphanUnrevertedReceiptCount: orphanUnrevertedTrialReceipts.length,
    suitePendingRevertCount,
    suiteStatus: reversibleSuiteState.status,
  });
  const reversibleSuiteRunBlocked = trialRunnerBlock.blocked || agentLabBaselineBlocksRun;
  const reversibleSuiteRunBlockedMessage = agentLabBaselineBlocksRun
    ? agentLabBaselineLoadState === "loading"
      ? "Checking Agent Lab baseline before run..."
      : agentLabBaselineLoadState === "error"
        ? `Agent Lab baseline check failed: ${agentLabBaselineLoadError || "unknown error"}. Retry cleanup or refresh.`
        : agentLabHasLeftovers
          ? `Agent Lab still has ${agentLabBaselineSnapshot?.baseline_dirty_agent_lab_files.length ?? 0} leftover file(s). Reverse them before a fresh Coder benchmark.`
          : "Agent Lab baseline is not ready yet. Wait for the baseline check to finish."
    : trialRunnerBlock.message;
  const reversibleSuiteFinished =
    reversibleSuiteState.status === "done" || reversibleSuiteState.status === "failed";
  const hasSelectedPromptResult =
    dummyCoderRunState.status !== "idle" && dummyCoderRunState.status !== "cleared";
  const selectedPromptUndoReceipt = hasSelectedPromptResult
    ? selectedPromptReceiptFromState()
    : null;
  const canCleanUpTrialRunner =
    !isReverting &&
    !reversibleSuiteBusy &&
    !backgroundCleanupActive &&
    (hasSelectedPromptResult ||
      (agentLabBaselineLoadState !== "loading" &&
        (reversibleSuiteState.results.length > 0 ||
          canRevertTrialRuns ||
          suitePendingRevertCount > 0 ||
          agentLabHasLeftovers ||
          (reversibleTrialCategory === "Coder" && agentLabBaselineLoadState === "error") ||
          (reversibleSuiteCanResume && Boolean(reversibleSuiteState.suiteId || backendRunSync.runId)))));
  const selectedPromptTrialLabel: ReversibleSuitePromptResult["visible_result_label"] =
    dummyCoderRunState.status === "starting" ||
    dummyCoderRunState.status === "request_sent" ||
    dummyCoderRunState.status === "running"
      ? "RUNNING"
      : dummyCoderRunState.status === "applied"
        ? "PASS"
        : dummyCoderRunState.status === "blocked"
          ? "BLOCKED"
          : dummyCoderRunState.status === "complete" && dummyCoderRunState.grader?.label === "PASS"
            ? "PASS"
            : dummyCoderRunState.status === "complete" && dummyCoderRunState.grader?.resultState === "PASS_NOOP"
              ? "ALREADY SATISFIED"
              : "NEEDS FIX";
  const showTrialCleanupPanel =
    backgroundCleanupActive ||
    isReverting ||
    agentLabHasLeftovers ||
    reversibleTrialCategory === "Coder" ||
    (reversibleSuiteFinished && reversibleSuiteState.results.length > 0);
  const agentLabBaselineStatusText =
    reversibleTrialCategory === "Coder"
      ? agentLabBaselineLoadState === "loading"
        ? "Checking Agent Lab baseline..."
        : agentLabBaselineLoadState === "error"
          ? `Agent Lab baseline check failed: ${agentLabBaselineLoadError || "unknown error"}`
          : agentLabBaselineSnapshot
            ? agentLabBaselineSnapshot.baseline_clean_for_fresh_suite
              ? "Agent Lab baseline clean — ready for a fresh Coder benchmark."
              : dirtyBaselineScope === "dummy-product-site"
                ? `Dummy product-site baseline dirty (${dirtyBaselineFileSplit.dummyProductSiteFiles.length} leftover file(s)). Reverse before a fresh Coder benchmark.`
                : dirtyBaselineScope === "agent-lab"
                  ? `Agent Lab baseline dirty (${dirtyBaselineFileSplit.agentLabFiles.length} leftover file(s)). Reverse before running.`
                  : `Baseline dirty (${agentLabBaselineSnapshot.baseline_dirty_agent_lab_files.length} leftover file(s)). Reverse before running.`
            : "Agent Lab baseline not loaded yet."
      : null;
  const trialReversalHelpText =
    backgroundCleanupActive || isReverting
      ? "Cleanup/reverse is still running. Wait for it to finish before starting another benchmark."
      : hasSelectedPromptResult
        ? selectedPromptUndoReceipt
          ? "Selected prompt applied reversible edits. This button reverses them and clears the selected-prompt result."
          : "No applied selected-prompt edits to reverse. This button clears the selected-prompt result."
      : agentLabHasLeftovers
        ? dirtyBaselineScope === "dummy-product-site"
          ? `LumaCart fixture still has ${dirtyBaselineFileSplit.dummyProductSiteFiles.length} leftover file(s) on disk. Reverse/clear them before a fresh Coder benchmark.`
          : dirtyBaselineScope === "agent-lab"
            ? `Agent Lab still has ${dirtyBaselineFileSplit.agentLabFiles.length} leftover file(s) on disk. Reverse them before a fresh Coder benchmark.`
            : `Baseline still has ${agentLabBaselineSnapshot?.baseline_dirty_agent_lab_files.length ?? 0} leftover file(s) on disk. Reverse them before a fresh Coder benchmark.`
        : suitePendingRevertCount > 0
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
  const reversibleSuiteCountMismatch =
    reversibleSuiteState.results.length > 0 && reversibleSuiteState.count !== reversibleTrialCount;
  const reversibleSuiteReversalPanel = (
    <>
      <button
        className={`mt-3 inline-flex min-h-10 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
        data-testid={selectedPromptUndoReceipt ? "selected-prompt-undo-last-change" : undefined}
        disabled={!canCleanUpTrialRunner}
        onClick={() => void handleCleanUpTrialRunner()}
        type="button"
      >
        {isReverting || backgroundCleanupActive
          ? "Cleaning up trial run..."
          : selectedPromptUndoReceipt
            ? "Undo last change"
          : agentLabBaselineLoadState === "error"
            ? "Retry agent-lab cleanup"
          : agentLabHasLeftovers && reversibleSuiteState.results.length === 0
            ? "Reverse agent-lab leftovers"
          : reversibleSuiteCanResume && (reversibleSuiteState.suiteId || backendRunSync.runId)
            ? "Clear paused suite and reverse leftovers"
          : canCleanUpTrialRunner
            ? "Reverse trial edits and clear results"
            : agentLabBaselineSnapshot?.baseline_clean_for_fresh_suite
              ? "Trial cleanup complete"
            : "Trial cleanup complete"}
      </button>
      {agentLabBaselineStatusText ? (
        <p
          className={`mt-2 text-xs font-semibold ${
            agentLabBaselineLoadState === "error"
              ? "text-rose-200"
              : agentLabBaselineSnapshot?.baseline_clean_for_fresh_suite
                ? "text-emerald-300"
                : "text-amber-200"
          }`}
        >
          {agentLabBaselineStatusText}
        </p>
      ) : null}
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
  const causalTraceRows = previewState.traceId
    ? [
        ["trace_id", previewState.traceId],
        ["invocation_event_id", previewState.invocationEventId],
        ["consumer_event_id", previewState.consumerEventId],
        ["consumer_subsystem", previewState.consumerSubsystem],
        ["status_after", previewState.causalStatusAfter],
      ]
    : [];
  const plan2SubsystemRows = previewState.plan2SubsystemIntegrations ?? [];
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
    setDesignStudioComposerState(idleDesignStudioComposerState());
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

  function handleComposerModeChange(mode: ComposerMode) {
    setComposerMode(mode);
    resetPreviewForEdit();
  }

  async function handleDesignStudioPreview() {
    const trimmedTask = task.trim();
    const requestId =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? `design-studio-${crypto.randomUUID()}`
        : `design-studio-${Date.now()}`;
    const runStartedAt = performance.now();
    setDraftReady(true);
    rememberPromptSnapshot(task);
    setComposerTiming({
      diffPreviewMs: null,
      promptPacketMs: null,
      runStartedAt,
      totalMs: null,
    });
    setPreviewState(idlePreviewState());
    setDesignStudioComposerState({
      endpointStatus: "started",
      error: null,
      isLoading: true,
      outcome: null,
      reason: null,
      requestId,
      status: "running",
      traceId: null,
    });
    try {
      const response = await fetchWithTimeout(
        "/v1/coding/design-studio/preview",
        {
          body: JSON.stringify({
            model_probe: {
              enabled: true,
              model: "phi4-mini:latest",
              provider: "ollama",
              require_source: false,
              timeout_ms: 60_000,
            },
            prompt: trimmedTask,
            request_id: requestId,
            target_surface: "/coding/design-demo",
          }),
          headers: {
            "content-type": "application/json",
            "x-design-studio-request-id": requestId,
          },
          method: "POST",
        },
        MANUAL_PROMPT_PACKET_TIMEOUT_MS,
      );
      const payload = await readJson(response);
      if (!response.ok) {
        throw new Error(messageFromPayload(payload, response.status));
      }
      const record = asRecord(payload);
      const previewPacket = asRecord(record.preview_packet);
      const messyPromptResult = asRecord(record.messy_prompt_result);
      const outcome = stringValue(messyPromptResult.outcome) ?? stringValue(record.status) ?? "DESIGN_STUDIO_PREVIEW";
      const reason = stringValue(messyPromptResult.reason) ?? stringValue(record.reason_code);
      const traceId = stringValue(previewPacket.trace_id) ?? stringValue(record.trace_id) ?? "not returned";
      setDesignStudioComposerState({
        endpointStatus: `/v1/coding/design-studio/preview:${response.status}`,
        error: null,
        isLoading: false,
        outcome,
        reason: reason ?? null,
        requestId,
        status: outcome === "ASK_CLARIFY_TARGET" ? "blocked" : "ready",
        traceId,
      });
    } catch (error) {
      setDesignStudioComposerState({
        endpointStatus: "/v1/coding/design-studio/preview:failed",
        error: error instanceof Error ? error.message : "Design Studio preview failed.",
        isLoading: false,
        outcome: null,
        reason: null,
        requestId,
        status: "error",
        traceId: null,
      });
    } finally {
      setComposerTiming((current) => ({
        ...current,
        totalMs: elapsedMs(runStartedAt),
      }));
    }
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
      if (appliedRunReceiptsAreEqual(current, next)) {
        return current;
      }
      storeAppliedRunReceipts(next);
      return next;
    });
  }

  const updateDummyCoderRunState = useCallback(
    (nextState: DummyCoder10RunState | ((current: DummyCoder10RunState) => DummyCoder10RunState)) => {
      setDummyCoderRunState((current) => {
        const next = typeof nextState === "function" ? nextState(current) : nextState;
        storeDummyCoderRunState(next);
        return next;
      });
    },
    [],
  );

  useEffect(() => {
    const taskId = dummyCoderRunState.taskId;
    const active =
      dummyCoderRunState.status === "starting" ||
      dummyCoderRunState.status === "request_sent" ||
      dummyCoderRunState.status === "running";
    if (!taskId || !active) return;
    const taskIdForSync = taskId;
    let cancelled = false;
    let timer: number | null = null;

    async function syncSelectedPromptTask() {
      try {
        const response = await fetchWithTimeout(
          `/v1/tasks/long-running/${encodeURIComponent(taskIdForSync)}`,
          { cache: "no-store" },
          TRIAL_LONG_RUNNING_TIMEOUT_MS,
        );
        const payload = await readJson(response);
        const task = asRecord(asRecord(payload).task ?? payload);
        const status = stringValue(task.status);
        if (!response.ok || !status || cancelled) return;
        const steps = arrayOfStrings(task.steps);
        const taskResultsText = stringValue(task.truncated_test_results);
        let taskResults: Record<string, unknown> = {};
        if (taskResultsText?.startsWith("{")) {
          try {
            taskResults = asRecord(JSON.parse(taskResultsText));
          } catch {
            taskResults = {};
          }
        }
        const taskCoderDiagnostics = asRecord(taskResults.coder_diagnostics);
        const taskEnvelope = asRecord(payload);
        const taskCreationDiagnostics = asRecord(taskEnvelope.diagnostic_envelope);
        const taskAntiCheat = asRecord(
          taskEnvelope.anti_cheat ??
          task.anti_cheat ??
          taskCreationDiagnostics.anti_cheat,
        );
        let taskAntiCheatStatus =
          stringValue(taskCoderDiagnostics.anti_cheat_status) ??
          stringValue(task.anti_cheat_status) ??
          stringValue(taskEnvelope.anti_cheat_status) ??
          stringValue(taskAntiCheat.anti_cheat_status);
        const taskAntiCheatReasons = [
          ...arrayOfStrings(taskCoderDiagnostics.anti_cheat_reasons),
          ...arrayOfStrings(task.anti_cheat_reasons),
          ...arrayOfStrings(taskEnvelope.anti_cheat_reasons),
          ...arrayOfStrings(taskAntiCheat.anti_cheat_reasons),
        ];
        const taskAntiCheatHardFailIds = [
          ...arrayOfStrings(taskCoderDiagnostics.anti_cheat_hard_fail_ids),
          ...arrayOfStrings(task.anti_cheat_hard_fail_ids),
          ...arrayOfStrings(taskEnvelope.anti_cheat_hard_fail_ids),
          ...arrayOfStrings(taskAntiCheat.anti_cheat_hard_fail_ids),
        ];
        const taskReasonCode = stringValue(taskResults.reason_code);
        if ((taskAntiCheatStatus === "not_run" || !taskAntiCheatStatus) && taskReasonCode) {
          taskAntiCheatStatus = "failed";
          taskAntiCheatHardFailIds.push(`pre_apply_block:${taskReasonCode}`);
          taskAntiCheatReasons.push(taskReasonCode);
        }
        const taskMessage =
          stringValue(taskResults.summary) ??
          taskResultsText ??
          stringValue(task.message) ??
          stringValue(task.error) ??
          steps.at(-1) ??
          `Selected prompt task ${status}.`;
        // While the packet fetch is still in flight, surface the latest task step as live progress
        // so the run is not a silent black box for minutes. This is purely informational; it must not
        // flip the run to a terminal state unless the task actually reached one.
        const inFlight =
          status === "starting" ||
          status === "running" ||
          status === "queued" ||
          status === "pending" ||
          status === "request_sent";
        if (inFlight) {
          updateDummyCoderRunState((current) => {
            if (current.taskId !== taskIdForSync) return current;
            if (current.status !== "starting" && current.status !== "request_sent" && current.status !== "running") {
              return current;
            }
            return {
              ...current,
              message: taskMessage,
              rawBackendStatus: status,
              status: "running",
              taskCreationStatus:
                stringValue(task.task_creation_status) ??
                stringValue(taskCreationDiagnostics.task_creation_status) ??
                current.taskCreationStatus,
              taskCreationElapsedMs:
                numberValue(task.task_creation_elapsed_ms) ??
                numberValue(taskCreationDiagnostics.task_creation_elapsed_ms) ??
                current.taskCreationElapsedMs,
              taskCreationTimeoutStage:
                stringValue(task.task_creation_timeout_stage) ??
                stringValue(taskCreationDiagnostics.task_creation_timeout_stage) ??
                current.taskCreationTimeoutStage,
              taskCreationLastCheckpoint:
                stringValue(task.task_creation_last_checkpoint) ??
                stringValue(taskCreationDiagnostics.task_creation_last_checkpoint) ??
                current.taskCreationLastCheckpoint,
              taskCreationBlockingSubsystem:
                stringValue(task.task_creation_blocking_subsystem) ??
                stringValue(taskCreationDiagnostics.task_creation_blocking_subsystem) ??
                current.taskCreationBlockingSubsystem,
            };
          });
          return;
        }
        // The task reached a terminal state. blocked/failed/cancelled are hard stops; complete means
        // the backend finished but the packet route may still be slow, so surface it as a recoverable
        // signal rather than leaving the runner stuck on request_sent.
        const terminalStatus =
          status === "blocked" ||
          status === "failed" ||
          status === "cancelled" ||
          status === "complete";
        if (!terminalStatus || cancelled) return;
        const completed = status === "complete";
        updateDummyCoderRunState((current) => {
          if (current.taskId !== taskIdForSync) return current;
          if (current.status !== "starting" && current.status !== "request_sent" && current.status !== "running") {
            return current;
          }
          return {
            ...current,
            backendConvertedDiffSha256:
              stringValue(taskCoderDiagnostics.backend_converted_diff_sha256) ?? current.backendConvertedDiffSha256,
            backend_anti_cheat_status:
              taskAntiCheatStatus ?? current.backend_anti_cheat_status,
            backend_anti_cheat_hard_fail_ids:
              taskAntiCheatHardFailIds.length > 0
                ? [...new Set(taskAntiCheatHardFailIds)]
                : current.backend_anti_cheat_hard_fail_ids,
            backend_anti_cheat_advisory_ids:
              arrayOfStrings(taskCoderDiagnostics.anti_cheat_advisory_ids).length > 0
                ? arrayOfStrings(taskCoderDiagnostics.anti_cheat_advisory_ids)
                : current.backend_anti_cheat_advisory_ids,
            backend_anti_cheat_reasons:
              taskAntiCheatReasons.length > 0
                ? [...new Set(taskAntiCheatReasons)]
                : current.backend_anti_cheat_reasons,
            diffGenerationReason:
              stringValue(taskCoderDiagnostics.diff_generation_reason) ??
              taskReasonCode ??
              current.diffGenerationReason,
            diffGenerationStatus:
              stringValue(taskCoderDiagnostics.diff_generation_status) ??
              (taskReasonCode ? "blocked" : current.diffGenerationStatus),
            diffAddedPaths:
              arrayOfStrings(taskCoderDiagnostics.diff_added_paths).length > 0
                ? arrayOfStrings(taskCoderDiagnostics.diff_added_paths)
                : current.diffAddedPaths,
            diffFileCount:
              numberValue(taskCoderDiagnostics.diff_file_count) ?? current.diffFileCount,
            diffSkippedPaths:
              arrayOfStrings(taskCoderDiagnostics.diff_skipped_paths).length > 0
                ? arrayOfStrings(taskCoderDiagnostics.diff_skipped_paths)
                : current.diffSkippedPaths,
            diffSkippedReasons:
              arrayOfStrings(taskCoderDiagnostics.diff_skipped_reasons).length > 0
                ? arrayOfStrings(taskCoderDiagnostics.diff_skipped_reasons)
                : current.diffSkippedReasons,
            diffFilesystemSnapshotSummary:
              arrayOfStrings(taskCoderDiagnostics.diff_filesystem_snapshot_summary).length > 0
                ? arrayOfStrings(taskCoderDiagnostics.diff_filesystem_snapshot_summary)
                : current.diffFilesystemSnapshotSummary,
            diffSource: stringValue(taskCoderDiagnostics.diff_source) ?? current.diffSource,
            errorText:
              status === "failed" || status === "cancelled"
                ? taskMessage
                : taskReasonCode
                  ? `No diff produced: ${taskReasonCode}.`
                  : null,
            generatedDiffByBackend:
              booleanValue(taskCoderDiagnostics.generated_diff_by_backend) ?? current.generatedDiffByBackend,
            generationSource: stringValue(taskCoderDiagnostics.generation_source) ?? current.generationSource,
            message: completed
              ? `${taskMessage} The prompt-packet route is still finalizing; if this hangs, cancel and rerun Prompt 1.`
              : taskMessage,
            modelFileBundleSha256:
              stringValue(taskCoderDiagnostics.model_file_bundle_sha256) ?? current.modelFileBundleSha256,
            modelOutputClassification:
              stringValue(taskCoderDiagnostics.model_output_classification) ?? current.modelOutputClassification,
            modelOutputShapeSummary:
              stringValue(taskCoderDiagnostics.model_output_shape_summary) ?? current.modelOutputShapeSummary,
            noDiffFailureCause:
              stringValue(taskCoderDiagnostics.no_diff_failure_cause) ??
              stringValue(taskCoderDiagnostics.safe_response_classification) ??
              current.noDiffFailureCause,
            parserExtractorDecision:
              stringValue(taskCoderDiagnostics.parser_extractor_decision) ?? current.parserExtractorDecision,
            patchVerificationReason:
              stringValue(taskCoderDiagnostics.patch_verification_reason) ??
              (taskReasonCode ? "not_applicable: diff_generation_blocked" : current.patchVerificationReason),
            patchVerificationStatus:
              stringValue(taskCoderDiagnostics.patch_verification_status) ??
              (taskReasonCode ? "not_run" : current.patchVerificationStatus),
            rawBackendStatus: taskReasonCode ?? status,
            rawModelResponseSha256:
              stringValue(taskCoderDiagnostics.raw_model_response_sha256) ?? current.rawModelResponseSha256,
            recommendedNextAction: stringValue(task.next_action) ?? current.recommendedNextAction,
            status: completed ? "running" : status === "blocked" ? "blocked" : "error",
            taskCreationStatus:
              stringValue(task.task_creation_status) ??
              stringValue(taskCreationDiagnostics.task_creation_status) ??
              current.taskCreationStatus,
            taskCreationElapsedMs:
              numberValue(task.task_creation_elapsed_ms) ??
              numberValue(taskCreationDiagnostics.task_creation_elapsed_ms) ??
              current.taskCreationElapsedMs,
            taskCreationTimeoutStage:
              stringValue(task.task_creation_timeout_stage) ??
              stringValue(taskCreationDiagnostics.task_creation_timeout_stage) ??
              current.taskCreationTimeoutStage,
            taskCreationLastCheckpoint:
              stringValue(task.task_creation_last_checkpoint) ??
              stringValue(taskCreationDiagnostics.task_creation_last_checkpoint) ??
              current.taskCreationLastCheckpoint,
            taskCreationBlockingSubsystem:
              stringValue(task.task_creation_blocking_subsystem) ??
              stringValue(taskCreationDiagnostics.task_creation_blocking_subsystem) ??
              current.taskCreationBlockingSubsystem,
            structuredBundleAcceptedPaths:
              arrayOfStrings(taskCoderDiagnostics.structured_bundle_accepted_paths).length > 0
                ? arrayOfStrings(taskCoderDiagnostics.structured_bundle_accepted_paths)
                : current.structuredBundleAcceptedPaths,
            structuredBundleFileCount:
              numberValue(taskCoderDiagnostics.structured_bundle_file_count) ?? current.structuredBundleFileCount,
            structuredBundleParserStage:
              stringValue(taskCoderDiagnostics.structured_bundle_parser_stage) ?? current.structuredBundleParserStage,
            structuredBundleRejectedPaths:
              arrayOfStrings(taskCoderDiagnostics.structured_bundle_rejected_paths).length > 0
                ? arrayOfStrings(taskCoderDiagnostics.structured_bundle_rejected_paths)
                : current.structuredBundleRejectedPaths,
            structuredBundleRejectionReason:
              stringValue(taskCoderDiagnostics.structured_bundle_rejection_reason) ??
              current.structuredBundleRejectionReason,
            structuredBundleStatus:
              stringValue(taskCoderDiagnostics.structured_bundle_status) ?? current.structuredBundleStatus,
            trialResultTrustStatus:
              stringValue(taskCoderDiagnostics.trial_result_trust_status) ?? current.trialResultTrustStatus,
            verificationStatus: stringValue(task.post_apply_verification) ?? current.verificationStatus,
          };
        });
        if (timer != null) {
          window.clearInterval(timer);
          timer = null;
        }
      } catch {
        // Keep the prompt-packet request as the primary result path; this sync is only a stuck-state escape hatch.
      }
    }

    void syncSelectedPromptTask();
    timer = window.setInterval(() => void syncSelectedPromptTask(), 3000);
    return () => {
      cancelled = true;
      if (timer != null) window.clearInterval(timer);
    };
  }, [dummyCoderRunState.status, dummyCoderRunState.taskId, updateDummyCoderRunState]);

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
      `run_id: ${backendRunSync.runId || previewState.taskId || "pending_backend_record"}`,
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
      "plan_4_2_operator_ledger:",
      `brain_stage_timeline: ${plan42BrainStageTimelineItems.map((item) => `${item.label}=${item.status} (${item.meta})`).join("; ")}`,
      `task_ledger: ${plan42TaskLedgerItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      `output_contract: ${plan42OutputContractItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      `progress_ledger: ${plan42ProgressLedgerItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      `specialists_and_workers: ${plan42SpecialistWorkerItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      "",
      "plan_4_3_control_ledger:",
      `controls: ${plan43ControlLedgerItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      `authority: ${plan43ControlAuthorityItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      `control_contract: ${plan43ControlContractItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      `last_control_route: ${plan43LastControlRoute}`,
      `last_control_status: ${plan43LastControlStatus}`,
      "",
      "plan_4_4_truth_ledger:",
      `memory_and_research: ${plan44MemoryResearchItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      `assignment_and_verifier: ${plan44AssignmentVerifierItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      `repair_and_productive_truth: ${plan44RepairProductiveTruthItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      "",
      "plan_4_5_api_consolidation_ledger:",
      `canonical_route_sequence: ${plan45CanonicalRouteItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      `supporting_routes: ${plan45SupportingRouteItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
      `dormant_parallel_routes: ${plan45DormantRouteItems.map(([label, value]) => `${label}=${value}`).join("; ")}`,
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
      ...formatAgentLabBaselineDiagnostics({
        baseline_agent_lab_files: state.baselineAgentLabFiles,
        baseline_checked_at: state.baselineCheckedAt ?? "not checked",
        baseline_clean_for_fresh_suite: state.baselineCleanForFreshSuite ?? true,
        baseline_dirty_agent_lab_files: state.baselineDirtyAgentLabFiles,
        baseline_unreverted_receipts: state.baselineUnrevertedReceipts,
      }),
      "",
      "per_prompt:",
    ];
    if (state.results.length === 0 && (state.suiteId || state.interruptionReason || state.currentPrompt)) {
      lines.push(
        "- local_results: none",
        `  backend_run_id: ${backendRunSync.runId || state.suiteId || "none"}`,
        `  backend_sync_status: ${backendRunSync.status}`,
        `  backend_sync_message: ${backendRunSync.message || "none"}`,
        `  paused_prompt: ${state.currentPrompt || "none"}`,
        `  agent_lab_baseline: ${agentLabBaselineSnapshot?.baseline_clean_for_fresh_suite ? "clean" : agentLabBaselineSnapshot ? "dirty" : "unknown"}`,
        `  agent_lab_dirty_files: ${formatList(agentLabBaselineSnapshot?.baseline_dirty_agent_lab_files ?? [], "none")}`,
      );
    }
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

  const selectedDummyCoderPrompt = useMemo<TargetPluginPrompt>(
    () => codingTargetPlugin.prompts.find((prompt) => prompt.id === selectedDummyCoderPromptId) ?? codingTargetPlugin.prompts[0],
    [selectedDummyCoderPromptId],
  );
  const existingDummyProjectSummaryForBaseline = useCallback(
    (baseline: AgentLabBaselineSnapshot | null | undefined) => {
      // Baseline truth must come from the same Source Proxy sweep that the UI shows
      // for "baseline dirty/clean", not from a hardcoded empty file list. A hardcoded
      // empty list produced the contradictory report: "already_satisfied / files present"
      // alongside "LumaCart is not present". Filter the baseline probe to the
      // dummy-product-site fixture root so the summary reflects disk truth.
      const probeFiles = [
        ...(baseline?.baseline_agent_lab_files ?? []),
        ...(baseline?.baseline_dirty_agent_lab_files ?? []),
      ].filter(
        (path) => isDummyProductSiteTrialPath(path),
      );
      // The baseline probe is captured before a run; immediately after a successful apply the
      // probe is stale. Union in the just-applied changed files so the summary cannot say
      // "LumaCart is not present" right after the run created the fixture files.
      const appliedDummyFiles = (dummyCoderRunState.changedFiles ?? []).filter((path) =>
        isDummyProductSiteTrialPath(path),
      );
      return codingTargetPlugin.buildExistingProjectSummary({
        files: [...probeFiles, ...appliedDummyFiles],
      });
    },
    [dummyCoderRunState.changedFiles],
  );
  const existingDummyProjectSummary = useMemo(
    () => existingDummyProjectSummaryForBaseline(agentLabBaselineSnapshot),
    [agentLabBaselineSnapshot, existingDummyProjectSummaryForBaseline],
  );
  const selectedDummyCoderPacket = useMemo(
    () => codingTargetPlugin.buildRunnerPacket(selectedDummyCoderPrompt, existingDummyProjectSummary),
    [existingDummyProjectSummary, selectedDummyCoderPrompt],
  );

  function dummyCoder10DiagnosticsText(
    state = dummyCoderRunState,
    dummyProjectSummary = existingDummyProjectSummary,
  ) {
    const grader = state.grader;
    const productionTime =
      state.startedAt != null && state.finishedAt != null
        ? formatElapsedMs(state.startedAt, state.finishedAt)
        : state.startedAt != null
          ? "in progress"
          : "—";
    if (state.status === "cleared" || !state.selectedPromptId) {
      return [
        "selected_prompt_result: not_applicable: no selected-prompt run active",
        "selected_prompt_task_id: not_applicable: no selected-prompt run active",
        "selected_prompt_status: cleared",
        "message: no active selected-prompt result",
        `existing_dummy_project_summary: ${dummyProjectSummary}`,
      ].join("\n");
    }
    return [
      `selected_prompt_id: ${state.selectedPromptId ?? selectedDummyCoderPrompt.id}`,
      `selected_prompt_task_id: ${state.taskId ?? "missing: backend did not provide field"}`,
      `selected_prompt_number: ${selectedDummyCoderPrompt.number}`,
      `selected_prompt_title: ${selectedDummyCoderPrompt.title}`,
      `submitted_prompt: ${selectedDummyCoderPrompt.submittedPrompt}`,
      `fixture_root: ${selectedDummyCoderPrompt.fixtureRoot}`,
      `allowed_write_root: ${selectedDummyCoderPrompt.allowedWriteRoot}`,
      `primary_expected_targets: ${formatList(selectedDummyCoderPrompt.primaryExpectedTargets, "not_applicable: no primary expected targets")}`,
      `expected_result_state: ${selectedDummyCoderPrompt.expectedResultState}`,
      `run_status: ${state.status}`,
      `error_text: ${state.errorText ?? "missing: no diagnostic envelope received"}`,
      `raw_backend_status: ${state.rawBackendStatus ?? "missing: backend did not provide field"}`,
      ...selectedPromptFailureDiagnosticLines(state.lastFailureDiagnostics),
      ...(state.lastFailureDiagnostics ? [] : selectedPromptFallbackDiagnosticLines(state)),
      `changed_files: ${formatList(state.changedFiles, "not_recorded: apply_did_not_happen")}`,
      `checks_run: ${formatList(state.checksRun, "not_recorded: apply_did_not_happen")}`,
      `verification_status: ${state.verificationStatus ?? "missing: backend did not provide field"}`,
      `generation_source: ${state.generationSource ?? "missing: backend did not provide field"}`,
      `diff_source: ${state.diffSource ?? "missing: backend did not provide field"}`,
      `model_output_classification: ${state.modelOutputClassification ?? "missing: backend did not provide field"}`,
      `trial_result_trust_status: ${state.trialResultTrustStatus ?? "missing: backend did not provide field"}`,
      ...selectedPromptAuditDiagnosticsLines({ grader, state }),
      `scaffold_used: ${String(state.scaffoldUsed ?? false)}`,
      `generated_diff_by_backend: ${String(state.generatedDiffByBackend ?? false)}`,
      `grader_result_state: ${grader?.resultState ?? "not_run: skipped_due_to_apply_block"}`,
      `grader_label: ${grader?.label ?? "not_run: skipped_due_to_apply_block"}`,
      `grader_score: ${grader?.score ?? "not_run: skipped_due_to_apply_block"}`,
      `grader_reason: ${grader?.reason ?? "not_run: skipped_due_to_apply_block"}`,
      `critical_failures: ${formatList(grader?.criticalFailures ?? [], "not_applicable: no grader findings")}`,
      `file_scope_status: ${grader?.fileScope?.file_scope_status ?? "not_run: skipped_due_to_apply_block"}`,
      `provenance_status: ${grader?.provenance?.provenance_status ?? "not_run: skipped_due_to_apply_block"}`,
      `recommended_next_action: ${state.recommendedNextAction ?? grader?.recommendedNextAction ?? "missing: no diagnostic envelope received"}`,
      `production_time: ${productionTime} (started ${state.startedAt ? new Date(state.startedAt).toISOString() : "n/a"}${state.finishedAt ? `, finished ${new Date(state.finishedAt).toISOString()}` : ""})`,
      `preview_behavior_status: ${state.storefrontProbe?.preview_behavior_status ?? "not probed"}`,
      `preview_visible_text_summary: ${state.storefrontProbe?.preview_visible_text_summary ?? "not probed"}`,
      `preview_asset_status: ${state.storefrontProbe?.preview_asset_status ?? "not probed"}`,
      `preview_product_count: ${state.storefrontProbe?.product_count ?? "not probed"}`,
      `storefront_runtime_status: ${state.storefrontProbe?.storefront_runtime_status ?? "not probed"}`,
      `storefront_runtime_engine: ${state.storefrontProbe?.storefront_runtime_engine ?? "not probed"}`,
      `browser_evidence_source: ${state.storefrontProbe?.browser_evidence_source ?? "not_proven_by_managed_browser"}`,
      `real_browser_used: ${String(state.storefrontProbe?.real_browser_used === true)}`,
      `storefront_runtime_product_count: ${state.storefrontProbe?.storefront_runtime_product_count ?? "not probed"}`,
      `existing_dummy_project_summary: ${dummyProjectSummary}`,
    ].join("\n");
  }

  async function copyDummyCoder10Diagnostics() {
    const freshBaseline = agentLabBaselineSnapshot ?? await refreshAgentLabBaseline();
    const copied = await copyTextToClipboard(
      dummyCoder10DiagnosticsText(
        dummyCoderRunState,
        existingDummyProjectSummaryForBaseline(freshBaseline),
      ),
    );
    setDummyCoderRunCopyStatus(copied.ok ? "Selected prompt diagnostics copied." : "Diagnostics ready; clipboard unavailable.");
  }

  function cancelSelectedPromptBackendTask(taskId: string | null | undefined) {
    if (!taskId) return;
    void fetch(`/v1/tasks/long-running/${encodeURIComponent(taskId)}/cancel`, {
      method: "POST",
    }).catch(() => undefined);
  }

  function clearDummyCoder10RunState(message = "No applied selected-prompt edits to reverse. Results cleared.") {
    cancelSelectedPromptBackendTask(dummyCoderRunState.taskId);
    setDummyCoderRunCopyStatus("");
    clearStoredDummyCoderRunState();
    updateDummyCoderRunState(defaultDummyCoderRunState(message, "cleared"));
  }

  function selectedPromptReceiptFromState(state = dummyCoderRunState) {
    if (!state.taskId) return null;
    return appliedRunReceiptsRef.current.find(
      (receipt) => receipt.id.startsWith("selected-prompt:") && receipt.taskId === state.taskId && !receipt.revertedAt,
    ) ?? null;
  }

  function failSelectedPromptStart(error: unknown) {
    const message = error instanceof Error ? error.message : "Dummy Coder 10 prompt failed.";
    const failureDiagnostics = diagnosticPayloadFromError(error);
    const timeoutLayer = timeoutLayerFromError(error);
    const timedOut =
      timeoutLayer !== "network_fetch_error" &&
      timeoutLayer !== "unknown_timeout" &&
      /timeout|abort/i.test(`${message} ${timeoutLayer}`);
    updateDummyCoderRunState((current) => {
      const effectiveDiagnostics =
        failureDiagnostics ??
        missingSelectedPromptDiagnosticEnvelope({
          message,
          rawBackendStatus: current.rawBackendStatus ?? "request_failed",
          selectedPromptId: current.selectedPromptId ?? selectedDummyCoderPrompt.id,
          taskId: current.taskId,
          timeoutLayer,
        });
      const failureTruthSummary = asRecord(effectiveDiagnostics.final_truth_summary);
      const taskCreationFailed = !current.taskId && current.status === "starting";
      if (taskCreationFailed && timedOut) {
        return {
          ...current,
          errorText: SELECTED_PROMPT_TASK_ID_STUCK_MESSAGE,
          finishedAt: Date.now(),
          lastFailureDiagnostics: effectiveDiagnostics,
          message: SELECTED_PROMPT_TASK_ID_STUCK_MESSAGE,
          rawBackendStatus: "/v1/tasks/long-running:timeout",
          recommendedNextAction:
            stringValue(effectiveDiagnostics.recommended_next_action) ??
            stringValue(failureTruthSummary.recommended_next_action) ??
            "Retry Prompt 1 after confirming the long-running task route can create a durable task id. Fallback reason: missing diagnostic envelope.",
          status: "timeout",
          taskCreationStatus:
            stringValue(effectiveDiagnostics.task_creation_status) ??
            stringValue(asRecord(effectiveDiagnostics.diagnostic_envelope).task_creation_status) ??
            "timeout_before_task_id",
          taskCreationElapsedMs:
            numberValue(effectiveDiagnostics.task_creation_elapsed_ms) ??
            numberValue(asRecord(effectiveDiagnostics.diagnostic_envelope).task_creation_elapsed_ms) ??
            current.taskCreationElapsedMs,
          taskCreationTimeoutStage:
            stringValue(effectiveDiagnostics.task_creation_timeout_stage) ??
            stringValue(asRecord(effectiveDiagnostics.diagnostic_envelope).task_creation_timeout_stage) ??
            timeoutLayer,
          taskCreationLastCheckpoint:
            stringValue(effectiveDiagnostics.task_creation_last_checkpoint) ??
            stringValue(asRecord(effectiveDiagnostics.diagnostic_envelope).task_creation_last_checkpoint) ??
            current.taskCreationLastCheckpoint,
          taskCreationBlockingSubsystem:
            stringValue(effectiveDiagnostics.task_creation_blocking_subsystem) ??
            stringValue(asRecord(effectiveDiagnostics.diagnostic_envelope).task_creation_blocking_subsystem) ??
            "source_proxy_long_running_task_route",
        };
      }
      if (taskCreationFailed) {
        return {
          ...current,
          errorText: message,
          finishedAt: Date.now(),
          lastFailureDiagnostics: effectiveDiagnostics,
          message,
          rawBackendStatus: "/v1/tasks/long-running:no_task_id",
          recommendedNextAction:
            stringValue(effectiveDiagnostics.recommended_next_action) ??
            stringValue(failureTruthSummary.recommended_next_action) ??
            "Inspect /v1/tasks/long-running before running this prompt again. Fallback reason: missing diagnostic envelope.",
          status: "error",
          taskCreationStatus:
            stringValue(effectiveDiagnostics.task_creation_status) ??
            stringValue(asRecord(effectiveDiagnostics.diagnostic_envelope).task_creation_status) ??
            "failed_before_task_id",
          taskCreationElapsedMs:
            numberValue(effectiveDiagnostics.task_creation_elapsed_ms) ??
            numberValue(asRecord(effectiveDiagnostics.diagnostic_envelope).task_creation_elapsed_ms) ??
            current.taskCreationElapsedMs,
          taskCreationTimeoutStage:
            stringValue(effectiveDiagnostics.task_creation_timeout_stage) ??
            stringValue(asRecord(effectiveDiagnostics.diagnostic_envelope).task_creation_timeout_stage) ??
            timeoutLayer,
          taskCreationLastCheckpoint:
            stringValue(effectiveDiagnostics.task_creation_last_checkpoint) ??
            stringValue(asRecord(effectiveDiagnostics.diagnostic_envelope).task_creation_last_checkpoint) ??
            current.taskCreationLastCheckpoint,
          taskCreationBlockingSubsystem:
            stringValue(effectiveDiagnostics.task_creation_blocking_subsystem) ??
            stringValue(asRecord(effectiveDiagnostics.diagnostic_envelope).task_creation_blocking_subsystem) ??
            "source_proxy_long_running_task_route",
        };
      }
      return {
        ...current,
        errorText: message,
        finishedAt: Date.now(),
        lastFailureDiagnostics: effectiveDiagnostics,
        message,
        rawBackendStatus: current.rawBackendStatus ?? "request_failed",
        recommendedNextAction:
          stringValue(failureTruthSummary.recommended_next_action) ??
          "Inspect the failed route before running this prompt again. Fallback reason: missing diagnostic envelope.",
        status: timedOut ? "timeout" : "error",
      };
    });
  }

  function handleCancelSelectedPrompt() {
    // Abort any in-flight selected-prompt fetch and reset to a clean idle state. This gives the
    // user an escape from a long/hung "request_sent"/"running" run without waiting for the
    // full packet timeout or treating it as an error.
    selectedPromptAbortRef.current?.abort();
    selectedPromptAbortRef.current = null;
    cancelSelectedPromptBackendTask(dummyCoderRunState.taskId);
    updateDummyCoderRunState((current) => {
      if (
        current.status !== "starting" &&
        current.status !== "request_sent" &&
        current.status !== "running"
      ) {
        return current;
      }
      return defaultDummyCoderRunState("Selected-prompt run cancelled. Baseline left unchanged.", "cleared");
    });
    updateDummyCoderRunState((current) =>
      current.status === "cleared"
        ? { ...current, finishedAt: Date.now(), startedAt: current.startedAt ?? Date.now() }
        : current,
    );
  }

  async function handleRunDummyCoder10Prompt() {
    const prompt = selectedDummyCoderPrompt;
    let packet = codingTargetPlugin.buildRunnerPacket(prompt, existingDummyProjectSummary);
    const selectedTarget = selectedPromptTarget(prompt);
    const taskDescription = selectedPromptTaskDescription(prompt);
    const modelTask = selectedPromptModelTask(prompt);
    setDummyCoderRunCopyStatus("");
    // Allow the user to cancel a long/hung selected-prompt run (live model calls can take a while
    // and previously there was no escape from "request_sent" other than waiting for the 360s timeout).
    selectedPromptAbortRef.current?.abort();
    const abortController = new AbortController();
    selectedPromptAbortRef.current = abortController;
    updateDummyCoderRunState({
      changedFiles: [],
      canonicalContextVerdict: null,
      canonicalContextReportHash: null,
      canonicalContextBlockers: [],
      canonicalContextAcknowledgements: [],
      checksRun: [],
      diffSource: null,
      backend_anti_cheat_status: null,
      backend_anti_cheat_hard_fail_ids: [],
      backend_anti_cheat_advisory_ids: [],
      backend_anti_cheat_report: null,
      backend_anti_cheat_reasons: [],
      errorText: null,
      fallbackUsed: null,
      generatedDiffByBackend: null,
      generationSource: null,
      grader: null,
      message: SELECTED_PROMPT_WAITING_FOR_TASK_ID,
      modelOutputClassification: null,
      noDiffFailureCause: null,
      parserExtractorDecision: null,
      packet,
      rawBackendStatus: "/v1/tasks/long-running:creating_task",
      recommendedNextAction: null,
      scaffoldUsed: null,
      selectedPromptId: prompt.id,
      startedAt: Date.now(),
      finishedAt: null,
      applyMode: null,
      appliedDiffSha256: null,
      approvedDiffSha256: null,
      backendConvertedDiffSha256: null,
      structuredBundleStatus: null,
      structuredBundleParserStage: null,
      structuredBundleFileCount: null,
      structuredBundleAcceptedPaths: [],
      structuredBundleRejectedPaths: [],
      structuredBundleRejectionReason: null,
      modelOutputShapeSummary: null,
      diffGenerationStatus: null,
      diffGenerationReason: null,
      diffFileCount: null,
      diffAddedPaths: [],
      diffSkippedPaths: [],
      diffSkippedReasons: [],
      diffFilesystemSnapshotSummary: [],
      patchVerificationStatus: null,
      patchVerificationReason: null,
      taskCreationStatus: "creating_task",
      taskCreationElapsedMs: null,
      taskCreationTimeoutStage: null,
      taskCreationLastCheckpoint: "ui_request_not_sent",
      taskCreationBlockingSubsystem: null,
      modelFileBundleSha256: null,
      backupManifest: null,
      postApplyRediffSha256: null,
      provenanceHashNormalization: null,
      rawModelResponseSha256: null,
      lastFailureDiagnostics: null,
      stalePatchRecovered: null,
      storefrontProbe: null,
      taskId: null,
      status: "starting",
      trialResultTrustStatus: null,
      verificationStatus: null,
    });

    try {
      const taskResponse = await fetchWithTimeout("/v1/tasks/long-running", {
        body: JSON.stringify({ description: taskDescription }),
        headers: { "content-type": "application/json" },
        method: "POST",
        signal: abortController.signal,
      }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
      const taskPayload = await readJson(taskResponse);
      if (!taskResponse.ok) {
        throw new PayloadBackedError(messageFromPayload(taskPayload, taskResponse.status), taskPayload, taskResponse.status);
      }
      const taskId = taskIdFromPayload(taskPayload);
      if (!taskId) {
        throw new Error("No backend task id returned by /v1/tasks/long-running.");
      }
      const taskPayloadRecord = asRecord(taskPayload);
      const taskPayloadTask = asRecord(taskPayloadRecord.task);
      updateDummyCoderRunState((current) => ({
        ...current,
        message: `Task ${taskId} persisted; checking Prompt 1 baseline`,
        rawBackendStatus: "task_created",
        status: "request_sent",
        taskCreationStatus:
          stringValue(taskPayloadRecord.task_creation_status) ??
          stringValue(taskPayloadTask.task_creation_status) ??
          "persisted_task_id",
        taskCreationElapsedMs:
          numberValue(taskPayloadRecord.task_creation_elapsed_ms) ??
          numberValue(taskPayloadTask.task_creation_elapsed_ms) ??
          current.taskCreationElapsedMs,
        taskCreationTimeoutStage:
          stringValue(taskPayloadRecord.task_creation_timeout_stage) ??
          stringValue(taskPayloadTask.task_creation_timeout_stage) ??
          "not_applicable: task_id_persisted",
        taskCreationLastCheckpoint:
          stringValue(taskPayloadRecord.task_creation_last_checkpoint) ??
          stringValue(taskPayloadTask.task_creation_last_checkpoint) ??
          current.taskCreationLastCheckpoint,
        taskCreationBlockingSubsystem:
          stringValue(taskPayloadRecord.task_creation_blocking_subsystem) ??
          stringValue(taskPayloadTask.task_creation_blocking_subsystem) ??
          "not_applicable: task_id_persisted",
        taskId,
      }));

      if (prompt.id === "coder-001-init-dummy-product-site") {
        updateDummyCoderRunState((current) => ({
          ...current,
          message: `Checking clean dummy fixture baseline before Prompt 1 with task ${taskId}`,
          rawBackendStatus: "checking_dummy_fixture_baseline",
        }));
        const baselineBefore = await refreshAgentLabBaseline();
        if (!baselineBefore) {
          const blockMessage = `Dummy fixture baseline check failed: ${agentLabBaselineLoadError || "baseline route returned no snapshot"}`;
          const diagnostics = selectedPromptPreApplyBlockDiagnostic({
            dirtyFiles: [],
            message: blockMessage,
            reasonCode: "dirty_dummy_fixture_baseline_unknown",
            selectedPromptId: prompt.id,
          });
          updateDummyCoderRunState((current) => ({
            ...current,
            errorText: blockMessage,
            finishedAt: Date.now(),
            lastFailureDiagnostics: diagnostics,
            message: blockMessage,
            rawBackendStatus: "dirty_dummy_fixture_baseline_unknown",
            recommendedNextAction:
              "Restore Source Proxy baseline route health, verify the dummy fixture baseline, then rerun Prompt 1.",
            status: "blocked",
          }));
          return;
        }
        if (!baselineBefore.baseline_clean_for_fresh_suite) {
          updateDummyCoderRunState((current) => ({
            ...current,
            changedFiles: baselineBefore.baseline_dirty_agent_lab_files,
            message: `Resetting dirty dummy fixture baseline (${baselineBefore.baseline_dirty_agent_lab_files.length} file(s)) before Prompt 1`,
            rawBackendStatus: "resetting_dirty_dummy_fixture_baseline",
          }));
          let resetMessage = "";
          try {
            resetMessage = await resetDummyProductSiteViaServer();
          } catch (error) {
            const blockMessage =
              error instanceof Error ? error.message : "Fixed dummy fixture reset failed before Prompt 1.";
            const diagnostics = selectedPromptPreApplyBlockDiagnostic({
              dirtyFiles: baselineBefore.baseline_dirty_agent_lab_files,
              message: blockMessage,
              reasonCode: "dirty_dummy_fixture_reset_failed",
              selectedPromptId: prompt.id,
            });
            updateDummyCoderRunState((current) => ({
              ...current,
              changedFiles: baselineBefore.baseline_dirty_agent_lab_files,
              errorText: blockMessage,
              finishedAt: Date.now(),
              lastFailureDiagnostics: diagnostics,
              message: blockMessage,
              rawBackendStatus: "dirty_dummy_fixture_reset_failed",
              recommendedNextAction:
                "Run the fixed dummy fixture reset successfully, verify baseline_clean_for_fresh_suite, then rerun Prompt 1.",
              status: "blocked",
            }));
            return;
          }
          const baselineAfter = await refreshAgentLabBaseline();
          if (!baselineAfter?.baseline_clean_for_fresh_suite) {
            const dirtyFiles = baselineAfter?.baseline_dirty_agent_lab_files ?? baselineBefore.baseline_dirty_agent_lab_files;
            const blockMessage = `Fixed dummy fixture reset did not reach a clean baseline: ${formatList(dirtyFiles, "unknown dirty files")}. ${resetMessage}`;
            const diagnostics = selectedPromptPreApplyBlockDiagnostic({
              dirtyFiles,
              message: blockMessage,
              reasonCode: "dirty_dummy_fixture_reset_incomplete",
              selectedPromptId: prompt.id,
            });
            updateDummyCoderRunState((current) => ({
              ...current,
              changedFiles: dirtyFiles,
              errorText: blockMessage,
              finishedAt: Date.now(),
              lastFailureDiagnostics: diagnostics,
              message: blockMessage,
              rawBackendStatus: "dirty_dummy_fixture_reset_incomplete",
              recommendedNextAction:
                "Inspect the remaining dummy fixture files, then rerun cleanup before Prompt 1.",
              status: "blocked",
            }));
            return;
          }
          const cleanSummary = existingDummyProjectSummaryForBaseline(baselineAfter);
          packet = codingTargetPlugin.buildRunnerPacket(prompt, cleanSummary);
          updateDummyCoderRunState((current) => ({
            ...current,
            changedFiles: [],
            message: "Clean dummy fixture baseline confirmed for Prompt 1",
            packet,
            rawBackendStatus: "dummy_fixture_baseline_clean",
          }));
        }
      }

      updateDummyCoderRunState((current) => ({
        ...current,
        message: "Request sent",
        rawBackendStatus: "request_sent",
        status: "request_sent",
      }));
      const response = await fetchWithTimeout("/v1/decisions/prompt-packet", {
        body: JSON.stringify({
          active_task_id: taskId,
          allowed_files: [prompt.allowedWriteRoot],
          dummy_coder_10_packet: packet,
          expected_result_state: prompt.expectedResultState,
          forbidden_files: prompt.forbiddenFiles,
          primary_expected_targets: prompt.primaryExpectedTargets,
          project_contract: prompt.projectContract,
          prompt: prompt.submittedPrompt,
          selected_target: selectedTarget,
          selected_prompt_id: prompt.id,
          target_file: selectedTarget,
          task: modelTask,
          trial_mode: "live_apply",
          trial_mode_contract: packet.trial_mode_contract,
          trial_prompt_id: prompt.id,
          wants_implementation: true,
        }),
        headers: { "Content-Type": "application/json" },
        method: "POST",
        signal: abortController.signal,
      }, TRIAL_PROMPT_PACKET_TIMEOUT_MS);
      updateDummyCoderRunState((current) => ({
        ...current,
        message: `Running task ${taskId}`,
        rawBackendStatus: `/v1/decisions/prompt-packet:${response.status}`,
        status: "running",
      }));
      const proposalRead = await readApiResponse(response, "/v1/decisions/prompt-packet");
      const payload = proposalRead.payload;
      const record = asRecord(payload);
      const coderDiagnostics = asRecord(record.coder_diagnostics);
      const contextMetadata = asRecord(record.context_metadata);
      const canonicalContextBroker = asRecord(
        record.canonical_context_broker ?? contextMetadata.canonical_context_broker,
      );
      const canonicalContextAcknowledgementRecord = asRecord(
        canonicalContextBroker.downstream_acknowledgements,
      );
      let canonicalContextAcknowledgements = Object.entries(
        canonicalContextAcknowledgementRecord,
      )
        .filter(([, value]) => asRecord(value).acknowledged === true)
        .map(([consumer]) => consumer);
      let canonicalContextVerdict: string | null =
        stringValue(canonicalContextBroker.verdict) ?? null;
      let canonicalContextReportHash: string | null =
        stringValue(canonicalContextBroker.canonical_report_hash) ?? null;
      let canonicalContextBlockers = arrayOfStrings(
        canonicalContextBroker.required_context_blockers,
      );
      const changedFiles = changedFilesFromPayload(payload);
      const proposedDiff = stringValue(record.proposed_diff) ?? stringValue(record.proposedDiff) ?? "";
      const responseSelectedTarget =
        stringValue(record.target) ??
        prompt.primaryExpectedTargets[0] ??
        prompt.fixtureRoot;
      const checksRun = [
        ...new Set(
          [
            ...arrayOfStrings(record.checks_run),
            ...arrayOfStrings(record.checksRun),
            ...arrayOfStrings(coderDiagnostics.checks_run),
          ].filter(Boolean),
        ),
      ];
      let rawBackendStatus = stringValue(record.status) ?? `http_${response.status}`;
      const reasonCode = stringValue(record.reason_code) ?? stringValue(record.reasonCode);
      const scaffoldUsed = booleanValue(record.scaffold_used) ?? booleanValue(coderDiagnostics.scaffold_used);
      let fallbackUsed = booleanValue(record.fallback_used) ?? booleanValue(coderDiagnostics.fallback_used);
      const generatedDiffByBackend =
        booleanValue(record.generated_diff_by_backend) ?? booleanValue(coderDiagnostics.generated_diff_by_backend);
      const generationSource =
        stringValue(record.generation_source) ?? stringValue(coderDiagnostics.generation_source) ?? null;
      let diffSource = stringValue(record.diff_source) ?? stringValue(coderDiagnostics.diff_source) ?? null;
      const modelOutputClassification =
        stringValue(record.model_output_classification) ?? stringValue(coderDiagnostics.model_output_classification) ?? null;
      let backendAntiCheatStatus =
        stringValue(coderDiagnostics.anti_cheat_status) ?? stringValue(record.anti_cheat_status) ?? null;
      const backendAntiCheatHardFailIds = [
        ...new Set([
          ...arrayOfStrings(coderDiagnostics.anti_cheat_hard_fail_ids),
          ...arrayOfStrings(record.anti_cheat_hard_fail_ids),
        ]),
      ];
      const backendAntiCheatAdvisoryIds = [
        ...new Set([
          ...arrayOfStrings(coderDiagnostics.anti_cheat_advisory_ids),
          ...arrayOfStrings(record.anti_cheat_advisory_ids),
        ]),
      ];
      const backendAntiCheatReasons = [
        ...new Set([
          ...arrayOfStrings(coderDiagnostics.anti_cheat_reasons),
          ...arrayOfStrings(record.anti_cheat_reasons),
        ]),
      ];
      if ((backendAntiCheatStatus === "not_run" || !backendAntiCheatStatus) && reasonCode) {
        backendAntiCheatStatus = "failed";
        backendAntiCheatHardFailIds.push(`pre_apply_block:${reasonCode}`);
        backendAntiCheatReasons.push(reasonCode);
      }
      const backendAntiCheatReportRaw = coderDiagnostics.anti_cheat_report ?? record.anti_cheat_report;
      const backendAntiCheatReport =
        stringValue(backendAntiCheatReportRaw) ??
        (backendAntiCheatReportRaw == null ? null : JSON.stringify(backendAntiCheatReportRaw));
      const noDiffFailureCause =
        stringValue(record.no_diff_failure_cause) ??
        stringValue(record.noDiffFailureCause) ??
        stringValue(record.safe_response_classification) ??
        stringValue(record.safeResponseClassification) ??
        stringValue(coderDiagnostics.no_diff_failure_cause) ??
        stringValue(coderDiagnostics.noDiffFailureCause) ??
        stringValue(coderDiagnostics.safe_response_classification) ??
        stringValue(coderDiagnostics.safeResponseClassification) ??
        null;
      const parserExtractorDecision =
        stringValue(record.parser_extractor_decision) ??
        stringValue(record.parserExtractorDecision) ??
        stringValue(coderDiagnostics.parser_extractor_decision) ??
        stringValue(coderDiagnostics.parserExtractorDecision) ??
        null;
      let trialResultTrustStatus =
        stringValue(record.trial_result_trust_status) ?? stringValue(coderDiagnostics.trial_result_trust_status) ?? null;
      const rawModelResponseSha256 =
        stringValue(record.raw_model_response_sha256) ?? stringValue(coderDiagnostics.raw_model_response_sha256) ?? null;
      const modelFileBundleSha256 =
        stringValue(record.model_file_bundle_sha256) ?? stringValue(coderDiagnostics.model_file_bundle_sha256) ?? null;
      const backendConvertedDiffSha256 =
        stringValue(record.backend_converted_diff_sha256) ?? stringValue(coderDiagnostics.backend_converted_diff_sha256) ?? null;
      const structuredBundleStatus =
        stringValue(record.structured_bundle_status) ?? stringValue(coderDiagnostics.structured_bundle_status) ?? null;
      const structuredBundleParserStage =
        stringValue(record.structured_bundle_parser_stage) ?? stringValue(coderDiagnostics.structured_bundle_parser_stage) ?? null;
      const structuredBundleFileCount =
        numberValue(record.structured_bundle_file_count) ?? numberValue(coderDiagnostics.structured_bundle_file_count);
      const structuredBundleAcceptedPaths = [
        ...new Set([
          ...arrayOfStrings(record.structured_bundle_accepted_paths),
          ...arrayOfStrings(coderDiagnostics.structured_bundle_accepted_paths),
        ]),
      ];
      const structuredBundleRejectedPaths = [
        ...new Set([
          ...arrayOfStrings(record.structured_bundle_rejected_paths),
          ...arrayOfStrings(coderDiagnostics.structured_bundle_rejected_paths),
        ]),
      ];
      const structuredBundleRejectionReason =
        stringValue(record.structured_bundle_rejection_reason) ??
        stringValue(coderDiagnostics.structured_bundle_rejection_reason) ??
        null;
      const modelOutputShapeSummary =
        stringValue(record.model_output_shape_summary) ?? stringValue(coderDiagnostics.model_output_shape_summary) ?? null;
      const diffGenerationStatus =
        stringValue(record.diff_generation_status) ?? stringValue(coderDiagnostics.diff_generation_status) ?? null;
      const diffGenerationReason =
        stringValue(record.diff_generation_reason) ?? stringValue(coderDiagnostics.diff_generation_reason) ?? null;
      const diffFileCount =
        numberValue(record.diff_file_count) ?? numberValue(coderDiagnostics.diff_file_count);
      const diffAddedPaths = [
        ...new Set([
          ...arrayOfStrings(record.diff_added_paths),
          ...arrayOfStrings(coderDiagnostics.diff_added_paths),
        ]),
      ];
      const diffSkippedPaths = [
        ...new Set([
          ...arrayOfStrings(record.diff_skipped_paths),
          ...arrayOfStrings(coderDiagnostics.diff_skipped_paths),
        ]),
      ];
      const diffSkippedReasons = [
        ...new Set([
          ...arrayOfStrings(record.diff_skipped_reasons),
          ...arrayOfStrings(coderDiagnostics.diff_skipped_reasons),
        ]),
      ];
      const diffFilesystemSnapshotSummary = [
        ...new Set([
          ...arrayOfStrings(record.diff_filesystem_snapshot_summary),
          ...arrayOfStrings(coderDiagnostics.diff_filesystem_snapshot_summary),
        ]),
      ];
      const patchVerificationStatus =
        stringValue(record.patch_verification_status) ?? stringValue(coderDiagnostics.patch_verification_status) ?? null;
      const patchVerificationReason =
        stringValue(record.patch_verification_reason) ?? stringValue(coderDiagnostics.patch_verification_reason) ?? null;
      let approvedDiffSha256 =
        stringValue(record.approved_diff_sha256) ?? stringValue(coderDiagnostics.approved_diff_sha256) ?? null;
      let appliedDiffSha256 =
        stringValue(record.applied_diff_sha256) ?? stringValue(coderDiagnostics.applied_diff_sha256) ?? null;
      let postApplyRediffSha256 =
        stringValue(record.post_apply_rediff_sha256) ?? stringValue(coderDiagnostics.post_apply_rediff_sha256) ?? null;
      let provenanceHashNormalization =
        stringValue(record.provenance_hash_normalization) ?? stringValue(coderDiagnostics.provenance_hash_normalization) ?? null;
      let applyModeForGrader =
        stringValue(record.apply_mode) ?? stringValue(coderDiagnostics.apply_mode) ?? null;
      let stalePatchRecoveredForGrader =
        booleanValue(record.stale_patch_recovered) ?? booleanValue(coderDiagnostics.stale_patch_recovered) ?? null;
      const alreadySatisfied = record.already_satisfied === true || record.alreadySatisfied === true;
      const existingStarterFilesPresent =
        coderDiagnostics.existing_starter_files_present === true ||
        coderDiagnostics.existingStarterFilesPresent === true;
      const existingProductDataValidation = asRecord(
        coderDiagnostics.existing_product_data_validation ?? coderDiagnostics.existingProductDataValidation,
      );
      let productDataFieldsPresent =
        coderDiagnostics.existing_product_data_present === true ||
        coderDiagnostics.existingProductDataPresent === true ||
        existingProductDataValidation.ok === true;
      const existingProductCardsValidation = asRecord(
        coderDiagnostics.existing_product_cards_validation ?? coderDiagnostics.existingProductCardsValidation,
      );
      const productCardsRenderPresent =
        coderDiagnostics.existing_product_cards_present === true ||
        coderDiagnostics.existingProductCardsPresent === true ||
        existingProductCardsValidation.ok === true;
      const prompt2AlreadySatisfied =
        prompt.id === "coder-002-add-product-data" &&
        alreadySatisfied &&
        productDataFieldsPresent &&
        /already|satisfied|no[_ -]?changes|coder_no_changes_needed/i.test(`${reasonCode} ${rawBackendStatus}`);
      const prompt3AlreadySatisfied =
        prompt.id === "coder-003-render-product-cards" &&
        alreadySatisfied &&
        productCardsRenderPresent &&
        /already|satisfied|no[_ -]?changes|coder_no_changes_needed/i.test(`${reasonCode} ${rawBackendStatus}`);
      const blockedReason =
        prompt.allowBlockedPass && /protect|secret|env|source_proxy|blocked/i.test(`${reasonCode} ${rawBackendStatus}`)
          ? reasonCode ?? rawBackendStatus
          : null;
      let noOpEvidence =
        (prompt.allowNoopPass ||
          prompt2AlreadySatisfied ||
          prompt3AlreadySatisfied ||
          (prompt.id === "coder-001-init-dummy-product-site" && existingStarterFilesPresent)) &&
        /category|already|no[_ -]?changes|satisfied/i.test(`${reasonCode} ${rawBackendStatus}`)
          ? stringValue(record.simple_reason) ?? stringValue(record.reason) ?? stringValue(record.message) ?? rawBackendStatus
          : null;
      let appliedChangedFiles = changedFiles;
      let verificationStatus = stringValue(record.verification_status) ?? stringValue(record.checks_result) ?? null;
      let applyMessage: string | null = null;
      let applyDiagnosticEnvelope: Record<string, unknown> | null = null;
      let backendBackupManifest: string | null = null;
      let postApplyVerificationStatus: string | null = null;
      let finalTruthStatus: string | null = null;
      let prompt3Context: { currentIndexHtml?: string; currentMainJs?: string } | undefined;
      if (prompt.id === "coder-003-render-product-cards" && proposedDiff.trim()) {
        try {
          const [indexResponse, mainResponse] = await Promise.all([
            fetchWithTimeout(
              "/v1/coding/dummy-product-site-preview/index.html",
              { cache: "no-store" },
              TRIAL_POST_MODEL_STAGE_TIMEOUT_MS,
            ),
            fetchWithTimeout(
              "/v1/coding/dummy-product-site-preview/src/main.js",
              { cache: "no-store" },
              TRIAL_POST_MODEL_STAGE_TIMEOUT_MS,
            ),
          ]);
          prompt3Context = {
            currentIndexHtml: indexResponse.ok ? await indexResponse.text() : "",
            currentMainJs: mainResponse.ok ? await mainResponse.text() : "",
          };
        } catch {
          prompt3Context = undefined;
        }
      }
      const prompt3Violations =
        prompt.id === "coder-003-render-product-cards" && proposedDiff.trim()
          ? selectedPrompt3DiffViolations(proposedDiff, prompt3Context)
          : [];
      if (prompt3Violations.length > 0) {
        updateDummyCoderRunState((current) => ({
          ...current,
          changedFiles,
          errorText: `Prompt 3 model diff rejected before apply: ${prompt3Violations.join(", ")}`,
          finishedAt: Date.now(),
          message: "Prompt 3 model diff rejected before apply.",
          rawBackendStatus: "prompt_3_diff_contract_rejected",
          recommendedNextAction: "Tighten Prompt 3 context and retry without applying hardcoded cards.",
          status: "blocked",
          taskId,
        }));
        return;
      }
      if (response.ok && proposedDiff.trim() && responseSelectedTarget) {
        updateDummyCoderRunState((current) => ({
          ...current,
          message: `Running task ${taskId}: previewing diff`,
          rawBackendStatus,
          status: "running",
        }));
        const taskSpec = asRecord(record.task_spec);
        const diffResponse = await fetchWithTimeout("/v1/verification/diff-preview", {
          body: JSON.stringify({
            route_type: "source-proxy-default",
            task_spec: Object.keys(taskSpec).length > 0
              ? taskSpec
              : {
                  allowed_files: [prompt.allowedWriteRoot],
                  forbidden_files: prompt.forbiddenFiles,
                  risk_tier: "low",
                  source: "dummy-coder-10-selected-prompt",
                  target: responseSelectedTarget,
                  task_type: prompt.id === "coder-001-init-dummy-product-site" ? "create_file_bundle" : "create_or_modify_files",
                  verification: ["git diff --check"],
                },
            task_text: prompt.submittedPrompt,
            unified_diff: proposedDiff,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
        const diffPayload = await readJson(diffResponse);
        if (!diffResponse.ok) {
          throw new PayloadBackedError(messageFromPayload(diffPayload, diffResponse.status), diffPayload, diffResponse.status);
        }
        const diffStatus = statusFromPayload(diffPayload);
        const previewChangedFiles = changedFilesFromPayload(diffPayload);
        if (diffStatus === "blocked") {
          const previewBlocker = blockerFromPayload(diffPayload) || messageFromPayload(diffPayload, diffResponse.status);
          const previewDiagnostics = diagnosticPayloadFromResponse(diffPayload);
          const previewBlockedReasons = Array.isArray(asRecord(diffPayload).blocked_reasons)
            ? (asRecord(diffPayload).blocked_reasons as unknown[])
            : [];
          const previewReasonCode =
            stringValue(asRecord(previewBlockedReasons[0]).reason_code) ??
            stringValue(previewDiagnostics.reason_code) ??
            "diff_preview_blocked";
          const previewBlockDiagnostics: Record<string, unknown> = {
            stage_id: "coding_ui.selected_prompt.diff_preview",
            subsystem: "coding_cockpit_selected_prompt",
            status: "blocked",
            truth_status: "BLOCKED_SAFE",
            safe_block: true,
            reason_code: previewReasonCode,
            human_message: previewBlocker,
            task_identity: {
              backend_task_id: taskId,
              selected_prompt_id: prompt.id,
              selected_prompt_task_id: taskId,
            },
            prompt_packet: {
              raw_backend_status: rawBackendStatus,
              structured_bundle_status: structuredBundleStatus,
              structured_bundle_parser_stage: structuredBundleParserStage,
              structured_bundle_file_count: structuredBundleFileCount,
              structured_bundle_accepted_paths: structuredBundleAcceptedPaths,
              structured_bundle_rejected_paths: structuredBundleRejectedPaths,
              structured_bundle_rejection_reason: structuredBundleRejectionReason,
              model_output_classification: modelOutputClassification,
              model_output_shape_summary: modelOutputShapeSummary,
              diff_generation_status: diffGenerationStatus,
              diff_generation_reason: diffGenerationReason,
              diff_file_count: diffFileCount,
              diff_added_paths: diffAddedPaths,
              diff_skipped_paths: diffSkippedPaths,
              diff_skipped_reasons: diffSkippedReasons,
              diff_filesystem_snapshot_summary: diffFilesystemSnapshotSummary,
              patch_verification_status: patchVerificationStatus,
              patch_verification_reason: patchVerificationReason,
            },
            diff_provenance: {
              backend_converted_diff_sha256: backendConvertedDiffSha256,
              changed_files: previewChangedFiles.length > 0 ? previewChangedFiles : changedFiles,
              diff_source: diffSource,
              generated_diff_by_backend: generatedDiffByBackend,
              model_file_bundle_sha256: modelFileBundleSha256,
              raw_model_response_sha256: rawModelResponseSha256,
              trial_result_trust_status: trialResultTrustStatus,
            },
            approval_binding: {
              approval_binding_status: "not_run: execute_approved_not_reached",
              apply_block_layer: "diff_preview",
              block_receipt_path: "not_applicable: apply_did_not_happen",
              safe_block: true,
            },
            verification: {
              preview_verification_status: "blocked",
              preview_blocked_reasons: previewBlockedReasons,
              post_apply_verification_status: "not_run: execute_approved_not_reached",
              post_apply_verification_reason: "diff_preview_blocked",
              verification_required_action: "Inspect diff preview blocked_reasons, then rerun Prompt 1 from the managed /coding lane.",
            },
            anti_cheat: {
              anti_cheat_status: backendAntiCheatStatus ?? "not_run",
              anti_cheat_hard_fail_ids: backendAntiCheatHardFailIds,
              anti_cheat_advisory_ids: backendAntiCheatAdvisoryIds,
              anti_cheat_reasons: backendAntiCheatReasons,
              trial_result_trust_status: trialResultTrustStatus,
            },
            acceptance_gate: {
              binary_verdict: "NO-GO",
              plan5_gate_id: "plan5_selected_prompt_diff_preview_block",
              plan5_gate_present: false,
              reason: previewReasonCode,
            },
            final_truth_summary: {
              commit_safe: false,
              commit_safe_reason: "diff_preview_blocked",
              proof_level: "selected_prompt_pre_apply_block",
              raw_backend_status: diffStatus,
              recommended_next_action: "Inspect diff preview blocked_reasons, then rerun Prompt 1 from the managed /coding lane.",
              run_status: "blocked",
              block_receipt_path: "not_applicable: apply_did_not_happen",
              truth_status: "BLOCKED_SAFE",
              why_not_go: previewBlocker,
            },
            diff_preview: previewDiagnostics,
          };
          updateDummyCoderRunState((current) => ({
            ...current,
            backendConvertedDiffSha256,
            backend_anti_cheat_status: backendAntiCheatStatus,
            backend_anti_cheat_hard_fail_ids: backendAntiCheatHardFailIds,
            backend_anti_cheat_advisory_ids: backendAntiCheatAdvisoryIds,
            backend_anti_cheat_reasons: backendAntiCheatReasons,
            changedFiles: previewChangedFiles.length > 0 ? previewChangedFiles : changedFiles,
            diffAddedPaths,
            diffFileCount,
            diffFilesystemSnapshotSummary,
            diffGenerationReason,
            diffGenerationStatus,
            diffSkippedPaths,
            diffSkippedReasons,
            diffSource,
            errorText: previewBlocker,
            finishedAt: Date.now(),
            generatedDiffByBackend,
            generationSource,
            lastFailureDiagnostics: previewBlockDiagnostics,
            message: "Selected prompt diff preview blocked before apply.",
            modelFileBundleSha256,
            modelOutputClassification,
            modelOutputShapeSummary,
            patchVerificationReason,
            patchVerificationStatus,
            rawBackendStatus: diffStatus,
            rawModelResponseSha256,
            recommendedNextAction: "Inspect diff preview blocked_reasons, then rerun Prompt 1 from the managed /coding lane.",
            selectedPromptId: prompt.id,
            startedAt: current.startedAt ?? Date.now(),
            status: "blocked",
            structuredBundleAcceptedPaths,
            structuredBundleFileCount,
            structuredBundleParserStage,
            structuredBundleRejectedPaths,
            structuredBundleRejectionReason,
            structuredBundleStatus,
            taskId,
            trialResultTrustStatus,
            verificationStatus: "diff preview blocked",
          }));
          return;
        }
        updateDummyCoderRunState((current) => ({
          ...current,
          changedFiles: previewChangedFiles,
          message: `Running task ${taskId}: applying diff`,
          rawBackendStatus,
          status: "running",
          verificationStatus: "diff preview passed",
        }));
        const approvalAction = `Run selected dummy Coder prompt ${prompt.id}`;
        const contextHashBytes = await window.crypto.subtle.digest(
          "SHA-256",
          new TextEncoder().encode(`${prompt.id}|${prompt.submittedPrompt}|${responseSelectedTarget}`),
        );
        const contextHash = Array.from(new Uint8Array(contextHashBytes))
          .map((value) => value.toString(16).padStart(2, "0"))
          .join("");
        const approvalPreviewResponse = await fetchWithTimeout(
          `/v1/tasks/long-running/${encodeURIComponent(taskId)}/approval-preview`,
          {
            body: JSON.stringify({
              action: approvalAction,
              approved_diff: proposedDiff,
              context_hash: contextHash,
              selected_prompt_id: prompt.id,
              target: responseSelectedTarget,
            }),
            headers: { "content-type": "application/json" },
            method: "POST",
          },
          TRIAL_POST_MODEL_STAGE_TIMEOUT_MS,
        );
        const approvalPreviewPayload = await readJson(approvalPreviewResponse);
        if (!approvalPreviewResponse.ok) {
          throw new PayloadBackedError(
            messageFromPayload(approvalPreviewPayload, approvalPreviewResponse.status),
            approvalPreviewPayload,
            approvalPreviewResponse.status,
          );
        }
        const approvalPreview = asRecord(asRecord(approvalPreviewPayload).preview);
        const previewId = stringValue(approvalPreview.preview_id);
        const previewGeneration = numberValue(approvalPreview.generation);
        if (!previewId || !previewGeneration) throw new Error("approval_preview_missing_server_identity");
        const csrf = requireOperatorCsrf();
        const operatorApprovalResponse = await fetchWithTimeout("/v1/operator/approval", {
          body: JSON.stringify({ action: "approve", generation: previewGeneration, preview_id: previewId, task_id: taskId }),
          headers: { "content-type": "application/json", "x-spiritos-csrf": csrf },
          method: "POST",
        }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
        const operatorApprovalPayload = await readJson(operatorApprovalResponse);
        const approvalId = stringValue(asRecord(asRecord(operatorApprovalPayload).approval).approval_id);
        if (!operatorApprovalResponse.ok || !approvalId) {
          throw new PayloadBackedError(
            messageFromPayload(operatorApprovalPayload, operatorApprovalResponse.status), operatorApprovalPayload, operatorApprovalResponse.status,
          );
        }
        const applyResponse = await fetchWithTimeout("/v1/actions/execute-approved", {
          body: JSON.stringify({
            action: approvalAction,
            approval_id: approvalId,
            approved_diff: proposedDiff,
            allowed_files: [prompt.allowedWriteRoot],
            target: responseSelectedTarget,
            task_id: taskId,
            trial_prompt_id: prompt.id,
            trial_prompt_text: prompt.submittedPrompt,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
        const applyPayload = await readJson(applyResponse);
        if (!applyResponse.ok) {
          const failureDiagnostics = diagnosticPayloadFromResponse(applyPayload);
          const failureTruthSummary = asRecord(failureDiagnostics.final_truth_summary);
          const failureAntiCheat = asRecord(failureDiagnostics.anti_cheat);
          const failureMessage = messageFromPayload(applyPayload, applyResponse.status);
          updateDummyCoderRunState((current) => ({
            ...current,
            backend_anti_cheat_status: stringValue(failureAntiCheat.anti_cheat_status) ?? "not_run",
            backend_anti_cheat_reasons: arrayOfStrings(failureAntiCheat.anti_cheat_reasons),
            changedFiles: previewChangedFiles.length > 0 ? previewChangedFiles : changedFiles,
            errorText: failureMessage,
            finishedAt: Date.now(),
            lastFailureDiagnostics: failureDiagnostics,
            message:
              stringValue(failureTruthSummary.why_not_go) ??
              "Selected prompt apply blocked before workspace changes.",
            rawBackendStatus:
              stringValue(failureDiagnostics.reason_code) ??
              stringValue(failureTruthSummary.raw_backend_status) ??
              `http_${applyResponse.status}`,
            recommendedNextAction:
              stringValue(failureTruthSummary.recommended_next_action) ??
              "Inspect the execute-approved approval binding diagnostic before rerunning this prompt.",
            selectedPromptId: prompt.id,
            startedAt: current.startedAt ?? Date.now(),
            status: stringValue(failureTruthSummary.truth_status) === "BLOCKED_SAFE" ? "blocked" : "error",
            taskId,
            verificationStatus: "skipped_due_to_apply_block",
          }));
          return;
        }
        appliedChangedFiles = changedFilesFromApplyPayloadOrDiff(applyPayload, proposedDiff);
        applyMessage = messageFromPayload(applyPayload, applyResponse.status);
        verificationStatus = applyMessage;
        const applyRecord =
          applyPayload && typeof applyPayload === "object"
            ? (applyPayload as Record<string, unknown>)
            : null;
        const applyDiagnostics = diagnosticPayloadFromResponse(applyPayload);
        const applyExecution = asRecord(applyRecord?.execution);
        const applyAudit = asRecord(applyExecution.audit);
        const applyTask = asRecord(applyRecord?.task);
        const applyTaskEvidence = asRecord(
          asRecord(applyTask.ast_snapshot).approved_execution_evidence,
        );
        const applyTaskAudit = asRecord(applyTaskEvidence.audit);
        backendBackupManifest =
          stringValue(applyAudit.backup_manifest) ??
          stringValue(applyExecution.backup_manifest) ??
          stringValue(applyRecord?.backup_manifest) ??
          stringValue(applyTaskEvidence.backup_manifest) ??
          stringValue(applyTaskAudit.backup_manifest) ??
          null;
        applyDiagnosticEnvelope =
          Object.keys(asRecord(applyDiagnostics.approval_binding)).length > 0 ||
          Object.keys(asRecord(applyDiagnostics.final_truth_summary)).length > 0
            ? applyDiagnostics
            : null;
        const applyDiffProvenance = asRecord(applyDiagnostics.diff_provenance);
        const applyModeFromPayload =
          typeof applyRecord?.apply_mode === "string"
            ? applyRecord.apply_mode
            : stringValue(applyDiffProvenance.apply_mode) ?? null;
        const stalePatchRecoveredFromPayload =
          Boolean(applyRecord?.stale_patch_recovered) || applyDiffProvenance.stale_patch_recovered === true;
        approvedDiffSha256 =
          typeof applyRecord?.approved_diff_sha256 === "string"
            ? applyRecord.approved_diff_sha256
            : stringValue(applyDiffProvenance.approved_diff_sha256) ?? approvedDiffSha256;
        appliedDiffSha256 =
          typeof applyRecord?.applied_diff_sha256 === "string"
            ? applyRecord.applied_diff_sha256
            : stringValue(applyDiffProvenance.applied_diff_sha256) ?? appliedDiffSha256;
        postApplyRediffSha256 =
          typeof applyRecord?.post_apply_rediff_sha256 === "string"
            ? applyRecord.post_apply_rediff_sha256
            : stringValue(applyDiffProvenance.post_apply_rediff_sha256) ?? postApplyRediffSha256;
        provenanceHashNormalization =
          typeof applyRecord?.provenance_hash_normalization === "string"
            ? applyRecord.provenance_hash_normalization
            : stringValue(applyDiffProvenance.provenance_hash_normalization) ?? provenanceHashNormalization;
        applyModeForGrader = applyModeFromPayload ?? applyModeForGrader;
        stalePatchRecoveredForGrader = stalePatchRecoveredFromPayload;
        // Recovery provenance override: if execute-approved reports that git
        // apply --check failed and the backend wrote a deterministic fixture
        // solution itself, the on-disk bytes are NOT model-authored. Override
        // the upstream model-authored labels so the grader and diagnostics
        // cannot launder the recovery as a model-authored PASS.
        const recoveryFallbackUsed = Boolean(applyRecord?.recovery_fallback_used);
        const recoveryDiffSource =
          typeof applyRecord?.recovery_diff_source === "string" ? applyRecord.recovery_diff_source : null;
        const recoveryTrustStatus =
          typeof applyRecord?.recovery_trust_status === "string" ? applyRecord.recovery_trust_status : null;
        if (recoveryFallbackUsed) {
          fallbackUsed = true;
          diffSource = recoveryDiffSource ?? diffSource;
          trialResultTrustStatus = recoveryTrustStatus ?? trialResultTrustStatus;
        }
        updateDummyCoderRunState((current) => ({
          ...current,
          applyMode: applyModeFromPayload,
          appliedDiffSha256,
          approvedDiffSha256,
          backupManifest: backendBackupManifest,
          backendConvertedDiffSha256,
          stalePatchRecovered: stalePatchRecoveredFromPayload,
          postApplyRediffSha256,
          provenanceHashNormalization,
          diffSource: recoveryFallbackUsed && recoveryDiffSource ? recoveryDiffSource : current.diffSource,
          fallbackUsed: recoveryFallbackUsed || current.fallbackUsed,
          lastFailureDiagnostics: applyDiagnosticEnvelope ?? current.lastFailureDiagnostics,
          trialResultTrustStatus:
            recoveryFallbackUsed && recoveryTrustStatus ? recoveryTrustStatus : current.trialResultTrustStatus,
        }));
        const appliedAt = new Date().toISOString();
        const receipt: AppliedRunReceipt = {
          allowedFiles: [prompt.allowedWriteRoot],
          appliedAt,
          backupManifest: backendBackupManifest,
          changedFiles: appliedChangedFiles,
          diff: proposedDiff,
          hermesUsedForThisRun: null,
          id: `selected-prompt:${prompt.id}:${taskId}`,
          model: stringValue(record.model) ?? selectedProviderTruth.modelLabel,
          prompt: prompt.submittedPrompt,
          provider: stringValue(record.provider) ?? selectedProviderTruth.providerLabel,
          providerModelSource: stringValue(record.provider_model_source) ?? "selected-prompt",
          providerModelStatus: stringValue(record.provider_model_status) ?? "recorded",
          revertedAt: null,
          finalTruthStatus: null,
          postApplyVerificationStatus: null,
          reversalModel: null,
          reversalProvider: null,
          reversalProviderModelSource: null,
          reverseDiff: reverseUnifiedDiff(proposedDiff),
          target: responseSelectedTarget,
          taskId,
          undoReceiptId: null,
          undoReceiptPath: null,
        };
        updateAppliedRunReceipts((receipts) => appendAppliedRunReceipt(receipts, receipt));
      }

      // Storefront proof probe: read the just-applied fixture contents and verify the page would
      // render catalog/product content, not only a bare heading. HTTP 200 / files-present must not
      // equal PASS for storefront prompts.
      let storefrontProbe = storefrontProbeFromPayload(
        coderDiagnostics.storefront_probe ?? coderDiagnostics.storefrontProbe,
      );
      if (
        !storefrontProbe &&
        prompt.id === "coder-003-render-product-cards"
      ) {
        try {
          const fixtureEntries = await Promise.all(
            ["index.html", "src/products.js", "src/main.js", "src/styles.css"].map(async (rel) => {
              try {
                const fileResponse = await fetchWithTimeout(
                  `/v1/coding/dummy-product-site-preview/${rel}?t=${Date.now()}`,
                  { cache: "no-store" },
                  TRIAL_POST_MODEL_STAGE_TIMEOUT_MS,
                );
                const text = fileResponse.ok ? await fileResponse.text() : "";
                return [rel, text] as const;
              } catch {
                return [rel, ""] as const;
              }
            }),
          );
          storefrontProbe = codingTargetPlugin.probeStorefront({
            files: Object.fromEntries(fixtureEntries),
          });
        } catch {
          storefrontProbe = null;
        }
      }
      if (prompt.id === "coder-002-add-product-data" && applyMessage) {
        try {
          const fileResponse = await fetchWithTimeout(
            "/v1/coding/dummy-product-site-preview/src/products.js",
            { cache: "no-store" },
            TRIAL_POST_MODEL_STAGE_TIMEOUT_MS,
          );
          const productsSource = fileResponse.ok ? await fileResponse.text() : "";
          productDataFieldsPresent = dummyProductDataFieldsPresentFromSource(productsSource);
        } catch {
          productDataFieldsPresent = false;
        }
      }
      const storefrontProofPresent =
        storefrontProbe?.preview_behavior_status === "PASS_STOREFRONT_RENDERED" &&
        storefrontProbe.preview_asset_status === "present" &&
        storefrontProbe.product_count >= 6 &&
        storefrontProbe.card_render_path_present &&
        storefrontProbe.category_render_path_present &&
        storefrontProbe.description_render_path_present &&
        storefrontProbe.price_render_path_present &&
        storefrontProbe.storefront_runtime_status === "passed";

      if (prompt.id === "coder-001-init-dummy-product-site" && applyMessage) {
        const verificationResponse = await fetchWithTimeout(
          `/v1/tasks/long-running/${encodeURIComponent(taskId)}/verify`,
          {
            body: JSON.stringify({
              confirm_backup_audit_present: true,
              confirm_changed_files_reviewed: true,
              confirm_expected_change_present: true,
              confirm_no_unintended_files: true,
              manual_browser_check_done: false,
              run_snapshot_verification: true,
              verification_profile: "dummy_product_site",
              verification_note:
                "Source Proxy must run managed Chromium against the fixed port-3000 preview before completion.",
            }),
            headers: { "content-type": "application/json" },
            method: "POST",
          },
          TRIAL_POST_MODEL_STAGE_TIMEOUT_MS,
        );
        const verificationPayload = await readJson(verificationResponse);
        const verificationRecord = asRecord(verificationPayload);
        const verificationTask = asRecord(verificationRecord.task);
        const verificationResultsText = stringValue(verificationTask.truncated_test_results);
        let verificationResults: Record<string, unknown> = {};
        if (verificationResultsText?.startsWith("{")) {
          try {
            verificationResults = asRecord(JSON.parse(verificationResultsText));
          } catch {
            verificationResults = {};
          }
        }
        const verificationCoderDiagnostics = asRecord(verificationResults.coder_diagnostics);
        const verificationAntiCheat = asRecord(
          verificationTask.anti_cheat ??
          verificationRecord.anti_cheat ??
          verificationResults.anti_cheat ??
          verificationCoderDiagnostics.anti_cheat,
        );
        backendAntiCheatStatus =
          stringValue(verificationCoderDiagnostics.anti_cheat_status) ??
          stringValue(verificationResults.anti_cheat_status) ??
          stringValue(verificationTask.anti_cheat_status) ??
          stringValue(verificationAntiCheat.anti_cheat_status) ??
          backendAntiCheatStatus;
        backendAntiCheatHardFailIds.push(
          ...arrayOfStrings(verificationCoderDiagnostics.anti_cheat_hard_fail_ids),
          ...arrayOfStrings(verificationResults.anti_cheat_hard_fail_ids),
          ...arrayOfStrings(verificationTask.anti_cheat_hard_fail_ids),
          ...arrayOfStrings(verificationAntiCheat.anti_cheat_hard_fail_ids),
        );
        backendAntiCheatAdvisoryIds.push(
          ...arrayOfStrings(verificationCoderDiagnostics.anti_cheat_advisory_ids),
          ...arrayOfStrings(verificationResults.anti_cheat_advisory_ids),
          ...arrayOfStrings(verificationTask.anti_cheat_advisory_ids),
          ...arrayOfStrings(verificationAntiCheat.anti_cheat_advisory_ids),
        );
        backendAntiCheatReasons.push(
          ...arrayOfStrings(verificationCoderDiagnostics.anti_cheat_reasons),
          ...arrayOfStrings(verificationResults.anti_cheat_reasons),
          ...arrayOfStrings(verificationTask.anti_cheat_reasons),
          ...arrayOfStrings(verificationAntiCheat.anti_cheat_reasons),
        );
        const verificationTaskEvidence = asRecord(
          asRecord(verificationTask.ast_snapshot).approved_execution_evidence,
        );
        backendBackupManifest =
          backendBackupManifest ??
          stringValue(verificationTaskEvidence.backup_manifest) ??
          null;
        const postApplyVerification = asRecord(
          verificationTask.post_apply_verification ?? verificationRecord.post_apply_verification,
        );
        const managedBrowserEvidence = asRecord(postApplyVerification.browser_evidence);
        storefrontProbe = storefrontProbeFromManagedBrowserEvidence(managedBrowserEvidence);
        const snapshotVerification = asRecord(postApplyVerification.snapshot_verification);
        applyModeForGrader =
          stringValue(snapshotVerification.apply_mode) ?? applyModeForGrader;
        postApplyRediffSha256 =
          stringValue(snapshotVerification.post_apply_rediff_sha256) ??
          postApplyRediffSha256;
        const contextBroker = asRecord(verificationTask.canonical_context_broker);
        const finalContextAcks = asRecord(contextBroker.downstream_acknowledgements);
        canonicalContextAcknowledgements = Object.entries(finalContextAcks)
          .filter(([, value]) => asRecord(value).acknowledged === true)
          .map(([consumer]) => consumer);
        canonicalContextVerdict = stringValue(contextBroker.verdict) ?? null;
        canonicalContextReportHash = stringValue(contextBroker.canonical_report_hash) ?? null;
        canonicalContextBlockers = arrayOfStrings(contextBroker.required_context_blockers);
        postApplyVerificationStatus =
          stringValue(postApplyVerification.status) ??
          stringValue(verificationTask.status) ??
          null;
        const postApplyVerified =
          verificationResponse.ok &&
          verificationTask.status === "completed" &&
          postApplyVerification.status === "verified" &&
          contextBroker.go_eligible === true &&
          stringValue(contextBroker.verdict) === "GO_ELIGIBLE";
        rawBackendStatus =
          stringValue(verificationTask.status) ?? rawBackendStatus;
        if (postApplyVerified && applyDiagnosticEnvelope) {
          const priorVerification = asRecord(applyDiagnosticEnvelope.verification);
          const priorFinalTruth = asRecord(applyDiagnosticEnvelope.final_truth_summary);
          applyDiagnosticEnvelope = {
            ...applyDiagnosticEnvelope,
            verification: {
              ...priorVerification,
              commit_blockers: [],
              manual_browser_check_done: true,
              post_apply_verification_reason: "post_apply_verification_passed",
              post_apply_verification_status: "verified",
              verification_required_action: "none",
            },
            final_truth_summary: {
              ...priorFinalTruth,
              commit_safe: true,
              commit_safe_reason: "post_apply_verification_passed",
              proof_level: "post_apply_verified",
              raw_backend_status: "completed",
              recommended_next_action: "none",
              run_status: "completed",
              truth_status: "GO",
              why_not_go: "",
            },
          };
        }
        finalTruthStatus = postApplyVerified ? "GO" : "BLOCKED_SAFE";
        updateAppliedRunReceipts((receipts) =>
          receipts.map((receipt) =>
            receipt.id === `selected-prompt:${prompt.id}:${taskId}`
              ? {
                  ...receipt,
                  backupManifest: receipt.backupManifest ?? backendBackupManifest,
                  finalTruthStatus,
                  postApplyVerificationStatus,
                }
              : receipt,
          ),
        );
        if (!postApplyVerified) {
          const failureMessage = messageFromPayload(
            verificationPayload,
            verificationResponse.status,
          );
          updateDummyCoderRunState((current) => ({
            ...current,
            canonicalContextAcknowledgements,
            canonicalContextBlockers,
            canonicalContextReportHash,
            canonicalContextVerdict,
            backupManifest: backendBackupManifest,
            errorText: failureMessage,
            finishedAt: Date.now(),
            message: "Prompt 1 applied, but canonical post-apply verification did not reach GO.",
            rawBackendStatus: postApplyVerificationStatus ?? "post_apply_verification_failed",
            recommendedNextAction:
              "Inspect the task verification receipt; do not count this apply as complete.",
            status: "blocked",
            storefrontProbe,
            taskId,
            verificationStatus: postApplyVerificationStatus ?? "post-apply verification failed",
          }));
          return;
        }
        verificationStatus = "post-apply verified with browser proof";
        updateDummyCoderRunState((current) => ({
          ...current,
          applyMode: applyModeForGrader,
          backupManifest: backendBackupManifest,
        }));
      }
      if (
        !noOpEvidence &&
        prompt.id === "coder-003-render-product-cards" &&
        alreadySatisfied &&
        storefrontProofPresent &&
        /already|satisfied|no[_ -]?changes|coder_no_changes_needed/i.test(`${reasonCode} ${rawBackendStatus}`)
      ) {
        noOpEvidence =
          stringValue(record.simple_reason) ??
          stringValue(record.reason) ??
          stringValue(record.message) ??
          "Prompt 3 already satisfied: existing LumaCart cards render from product data.";
      }

      const grader = codingTargetPlugin.gradeResult({
        blockedReason,
        categoryEvidencePresent: prompt.id === "coder-009-noop-category-proof" ? Boolean(noOpEvidence) : undefined,
        changedFiles: appliedChangedFiles,
        checksRun,
        claimedVerificationWithoutEvidence:
          /pass|verified|checks passed/i.test(`${record.simple_reason ?? ""} ${record.verification_status ?? ""}`) &&
          checksRun.length === 0,
        commandFailed: /fail|error/i.test(String(record.checks_result ?? record.verification_status ?? "")),
        noOpEvidence,
        productDataFieldsPresent: prompt.id === "coder-002-add-product-data" ? productDataFieldsPresent : undefined,
        prompt,
        requiredInitFilesPresent: prompt.id === "coder-001-init-dummy-product-site"
          ? alreadySatisfied && existingStarterFilesPresent
            ? true
            : prompt.primaryExpectedTargets.every((target) => appliedChangedFiles.includes(target))
          : undefined,
        requiredInitFilesAlreadySatisfied: prompt.id === "coder-001-init-dummy-product-site"
          ? alreadySatisfied && existingStarterFilesPresent
          : undefined,
        provenance: {
          applied_diff_sha256: appliedDiffSha256,
          apply_mode: applyModeForGrader,
          approved_diff_sha256: approvedDiffSha256,
          backend_converted_diff_sha256: backendConvertedDiffSha256,
          diff_source: diffSource,
          fallback_used: fallbackUsed,
          generated_diff_by_backend: generatedDiffByBackend,
          generation_source: generationSource,
          model_file_bundle_sha256: modelFileBundleSha256,
          model_output_classification: modelOutputClassification,
          model_output_usable: booleanValue(record.model_output_usable),
          post_apply_rediff_sha256: postApplyRediffSha256,
          provenance_hash_normalization: provenanceHashNormalization,
          provider_call_made: booleanValue(record.provider_call_made),
          raw_backend_status: rawBackendStatus,
          raw_model_response_sha256: rawModelResponseSha256,
          scaffold_used: scaffoldUsed,
          stale_patch_recovered: stalePatchRecoveredForGrader,
          trial_result_trust_status: trialResultTrustStatus,
        },
        storefrontProbe,
        verificationEvidence: checksRun.length > 0 || record.verification_status ? [String(record.verification_status ?? "recorded")] : [],
      });
      const selectedPromptStatus: DummyCoder10RunState["status"] =
        grader.label === "INVALID"
          ? "error"
          : grader.label === "NEEDS_FIX"
            ? "blocked"
            : applyMessage
              ? "applied"
              : response.ok
              ? "complete"
              : "error";
      updateDummyCoderRunState((current) => ({
        ...current,
        changedFiles: appliedChangedFiles,
        canonicalContextAcknowledgements,
        canonicalContextBlockers,
        canonicalContextReportHash,
        canonicalContextVerdict,
        checksRun,
        backend_anti_cheat_status: backendAntiCheatStatus,
        backend_anti_cheat_hard_fail_ids: backendAntiCheatHardFailIds,
        backend_anti_cheat_advisory_ids: backendAntiCheatAdvisoryIds,
        backend_anti_cheat_report: backendAntiCheatReport,
        backend_anti_cheat_reasons: backendAntiCheatReasons,
        appliedDiffSha256,
        applyMode: applyModeForGrader,
        approvedDiffSha256,
        backendConvertedDiffSha256,
        structuredBundleStatus,
        structuredBundleParserStage,
        structuredBundleFileCount,
        structuredBundleAcceptedPaths,
        structuredBundleRejectedPaths,
        structuredBundleRejectionReason,
        modelOutputShapeSummary,
        diffGenerationStatus,
        diffGenerationReason,
        diffFileCount,
        diffAddedPaths,
        diffSkippedPaths,
        diffSkippedReasons,
        diffFilesystemSnapshotSummary,
        patchVerificationStatus,
        patchVerificationReason,
        diffSource,
        errorText:
          selectedPromptStatus === "blocked" && noDiffFailureCause && !proposedDiff.trim()
            ? `No diff produced: ${noDiffFailureCause}${parserExtractorDecision ? `; ${parserExtractorDecision}` : ""}.`
            : null,
        fallbackUsed,
        finishedAt: Date.now(),
        generatedDiffByBackend,
        generationSource,
        grader,
        message:
          applyMessage ??
          (selectedPromptStatus === "blocked" && noDiffFailureCause && !proposedDiff.trim()
            ? `NEEDS FIX: ${noDiffFailureCause}. ${grader.reason}`
            : grader.reason),
        modelOutputClassification,
        noDiffFailureCause,
        parserExtractorDecision,
        packet,
        lastFailureDiagnostics: applyDiagnosticEnvelope ?? current.lastFailureDiagnostics,
        postApplyRediffSha256,
        provenanceHashNormalization,
        rawBackendStatus,
        rawModelResponseSha256,
        modelFileBundleSha256,
        recommendedNextAction:
          stringValue(record.recommended_next_action) ??
          stringValue(record.next_recommended_action) ??
          grader.recommendedNextAction,
        scaffoldUsed,
        selectedPromptId: prompt.id,
        startedAt: current.startedAt ?? Date.now(),
        status: selectedPromptStatus,
        storefrontProbe,
        taskId,
        trialResultTrustStatus,
        verificationStatus,
      }));
      // After a successful apply, the pre-run baseline probe is stale. Refresh it so the
      // baseline status, dirty wording, and existing-project summary reflect disk truth
      // (otherwise the UI keeps showing "clean" while the fixture files were just created).
      if (selectedPromptStatus === "applied") {
        void refreshAgentLabBaseline();
      }
    } catch (error) {
      // A user-initiated cancel is not a failure: handleCancelSelectedPrompt already reset state.
      const aborted =
        abortController.signal.aborted ||
        (error instanceof DOMException && error.name === "AbortError") ||
        (error instanceof Error && /abort/i.test(error.message));
      if (aborted && selectedPromptAbortRef.current !== abortController) {
        return;
      }
      failSelectedPromptStart(error);
    } finally {
      if (selectedPromptAbortRef.current === abortController) {
        selectedPromptAbortRef.current = null;
      }
    }
  }

  async function fetchAgentLabBaselineSnapshot(): Promise<AgentLabBaselineSnapshot | null> {
    const unrevertedTargets = appliedRunReceiptsRef.current
      .filter((receipt) => receipt.id.startsWith("trial-suite:") && !receipt.revertedAt && !receipt.staleResolvedAt)
      .flatMap((receipt) => [receipt.target, ...receipt.changedFiles])
      .filter((path) => isCoderTrialCleanupPath(path));
    try {
      const query = unrevertedTargets.length > 0 ? `?unreverted_targets=${encodeURIComponent(unrevertedTargets.join(","))}` : "";
      const response = await fetchWithTimeout(
        `/v1/coding/agent-lab-baseline${query}`,
        { cache: "no-store" },
        15_000,
      );
      if (!response.ok) {
        const errorText = await response.text().catch(() => "");
        setAgentLabBaselineLoadState("error");
        setAgentLabBaselineLoadError(errorText || `HTTP ${response.status}`);
        return null;
      }
      const payload = await response.json() as AgentLabBaselineSnapshot;
      setAgentLabBaselineLoadState("ready");
      setAgentLabBaselineLoadError("");
      return payload;
    } catch (error) {
      setAgentLabBaselineLoadState("error");
      setAgentLabBaselineLoadError(error instanceof Error ? error.message : "baseline fetch failed");
      return null;
    }
  }

  async function refreshAgentLabBaseline() {
    if (reversibleTrialCategory === "Coder") {
      setAgentLabBaselineLoadState((current) => (current === "ready" ? "loading" : current === "idle" ? "loading" : current));
    }
    const snapshot = await fetchAgentLabBaselineSnapshot();
    setAgentLabBaselineSnapshot(snapshot);
    setTrialFixturesClean(snapshot ? (snapshot.baseline_clean_for_fresh_suite ? "yes" : "no") : "unknown");
    return snapshot;
  }

  async function sweepAgentLabLeftoverFilesViaServer(): Promise<string> {
    const unrevertedTargets = appliedRunReceiptsRef.current
      .filter((receipt) => receipt.id.startsWith("trial-suite:") && !receipt.revertedAt && !receipt.staleResolvedAt)
      .flatMap((receipt) => [receipt.target, ...receipt.changedFiles])
      .filter((path) => isCoderTrialCleanupPath(path));
    // #region agent log
    fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
      body: JSON.stringify({
        sessionId: "0fdea5",
        hypothesisId: "H5",
        location: "CodingCockpitShell.tsx:sweepAgentLabLeftoverFilesViaServer",
        message: "sweep request start",
        data: { unrevertedTargetCount: unrevertedTargets.length },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    const response = await fetchWithTimeout(
      "/v1/coding/agent-lab-sweep",
      {
        body: JSON.stringify({ unreverted_targets: unrevertedTargets }),
        headers: { "content-type": "application/json" },
        method: "POST",
      },
      120_000,
    );
    const payload = (await response.json().catch(() => ({}))) as {
      clean?: boolean;
      error?: string;
      message?: string;
      snapshot?: AgentLabBaselineSnapshot;
    };
    // #region agent log
    fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
      body: JSON.stringify({
        sessionId: "0fdea5",
        hypothesisId: "H5",
        location: "CodingCockpitShell.tsx:sweepAgentLabLeftoverFilesViaServer",
        message: "sweep request finished",
        data: { ok: response.ok, clean: payload.clean, error: payload.error ?? null },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    if (!response.ok) {
      throw new Error(payload.error || `agent-lab sweep HTTP ${response.status}`);
    }
    if (payload.snapshot) {
      setAgentLabBaselineSnapshot(payload.snapshot);
      setAgentLabBaselineLoadState("ready");
      setAgentLabBaselineLoadError("");
      setTrialFixturesClean(payload.snapshot.baseline_clean_for_fresh_suite ? "yes" : "no");
    } else {
      await refreshAgentLabBaseline();
    }
    return payload.message || (payload.clean ? "Workspace is clean for a fresh Coder benchmark." : "Agent-lab sweep finished.");
  }

  async function resetDummyProductSiteViaServer(): Promise<string> {
    const response = await fetchWithTimeout(
      "/v1/coding/dummy-product-site-preview/reset",
      {
        headers: { "content-type": "application/json" },
        method: "POST",
      },
      120_000,
    );
    const payload = (await response.json().catch(() => ({}))) as {
      status?: string;
      reset_verified?: boolean;
      fixture_root?: string;
      clean_verified?: boolean;
      reset_receipt_id?: string;
      error?: string;
    };
    if (
      !response.ok ||
      payload.status !== "reset_verified" ||
      payload.reset_verified !== true ||
      payload.clean_verified !== true
    ) {
      throw new Error(
        payload.error ||
          `dummy-product-site reset did not verify clean state (HTTP ${response.status})`,
      );
    }
    const baseline = await refreshAgentLabBaseline();
    if (!baseline?.baseline_clean_for_fresh_suite) {
      throw new Error("Reset receipt passed, but the baseline API still reports fixture files.");
    }
    return `Dummy fixture reset verified (${payload.reset_receipt_id ?? "receipt missing"}).`;
  }

  function buildAgentLabCleanupSeedReceipt(target: string): AppliedRunReceipt {
    const providerTruth = selectedProviderTruth;
    const normalizedTarget = normalizeRepoPath(target);
    return {
      allowedFiles: [
        normalizedTarget,
        "src/app/agent-lab/**",
        "src/components/agent-lab/**",
        "src/lib/agent-lab/**",
        "src/app/api/agent-lab/**",
        "tests/agent-lab/**",
      ],
      appliedAt: new Date().toISOString(),
      changedFiles: [target],
      diff: "",
      hermesUsedForThisRun: providerTruth.hermesUsedForThisRun,
      id: `trial-suite:cleanup:${target}`,
      model: providerTruth.modelLabel,
      prompt: `Cleanup delete ${target}`,
      provider: providerTruth.providerLabel,
      providerModelSource: providerTruth.source,
      providerModelStatus: providerTruth.status,
      revertedAt: null,
      reversalModel: null,
      reversalProvider: null,
      reversalProviderModelSource: null,
      reverseDiff: "",
      target: normalizedTarget,
      taskId: `cleanup-${normalizedTarget}`,
    };
  }

  async function sweepAgentLabLeftoverFiles(paths: string[]): Promise<string> {
    const ordered = [...new Set(paths.map((path) => normalizeRepoPath(path)).filter(Boolean))].sort(
      (left, right) => right.length - left.length,
    );
    if (ordered.length === 0) {
      return "No agent-lab leftover files were found on disk.";
    }
    const failures: string[] = [];
    let removed = 0;
    for (const target of ordered) {
      const cleanupReceipt = buildAgentLabCleanupSeedReceipt(target);
      try {
        // #region agent log
        fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
          body: JSON.stringify({
            sessionId: "0fdea5",
            hypothesisId: "H1",
            location: "CodingCockpitShell.tsx:sweepAgentLabLeftoverFiles",
            message: "sweep delete start",
            data: { target, allowedFiles: cleanupReceipt.allowedFiles },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        await sweepDeleteAgentLabFileWithRetry(cleanupReceipt);
        removed += 1;
        // #region agent log
        fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
          body: JSON.stringify({
            sessionId: "0fdea5",
            hypothesisId: "H1",
            location: "CodingCockpitShell.tsx:sweepAgentLabLeftoverFiles",
            message: "sweep delete ok",
            data: { target },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
      } catch (error) {
        const message = error instanceof Error ? error.message : "Agent-lab delete failed.";
        // #region agent log
        fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
          body: JSON.stringify({
            sessionId: "0fdea5",
            hypothesisId: "H1",
            location: "CodingCockpitShell.tsx:sweepAgentLabLeftoverFiles",
            message: "sweep delete failed",
            data: { target, error: message },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        if (reversalLooksAlreadyApplied(message)) {
          removed += 1;
          continue;
        }
        failures.push(`${target}: ${message}`);
      }
    }
    if (failures.length > 0) {
      return `Removed ${removed}/${ordered.length} agent-lab file(s). Still dirty: ${failures.slice(0, 3).join("; ")}`;
    }
    return `Removed ${removed} agent-lab leftover file(s). Workspace is clean for a fresh Coder benchmark.`;
  }

  async function sweepDeleteAgentLabFileWithRetry(
    receipt: AppliedRunReceipt,
    maxAttempts = 3,
  ): Promise<void> {
    let lastError: unknown;
    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      try {
        await applyAgentLabDeleteFallback(receipt);
        return;
      } catch (error) {
        lastError = error;
        const retryable =
          attempt < maxAttempts &&
          (error instanceof BrowserAbortTimeoutError ||
            isTransientNetworkFetchError(error));
        // #region agent log
        fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
          body: JSON.stringify({
            sessionId: "0fdea5",
            hypothesisId: "H2",
            location: "CodingCockpitShell.tsx:sweepDeleteAgentLabFileWithRetry",
            message: retryable ? "sweep delete retry" : "sweep delete give up",
            data: {
              attempt,
              target: receipt.target,
              error: error instanceof Error ? error.message : String(error),
            },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        if (!retryable) break;
        await waitForPromptPacketRetry(attempt);
      }
    }
    throw lastError instanceof Error ? lastError : new Error("Agent-lab delete failed.");
  }

  function finalizeReversibleTrialResult(
    result: ReversibleSuitePromptResult,
  ): ReversibleSuitePromptResult {
    const passProof = downgradePassWithoutReversalProof({
      appliedChangedFiles: result.applied_changed_files,
      diskChangedFiles: result.disk_changed_files,
      expectedOutcome: result.expected_outcome,
      reversalAvailable: result.reversal_available,
      reverseDiff: result.reverse_diff,
      visibleResultLabel: result.visible_result_label,
    });
    if (!passProof.downgraded) return result;
    return {
      ...result,
      error_summary: result.error_summary || `reason_code=${passProof.reason_code}`,
      failure_reason: passProof.failure_reason,
      visible_result_label: passProof.visible_result_label,
    };
  }

  async function runOneReversibleTrialPrompt(
    suiteId: string,
    prompt: ReversibleTrialPrompt,
    onStep?: (step: string) => void,
    options: { baselineCleanForFreshSuite?: boolean | null } = {},
  ): Promise<ReversibleSuitePromptResult> {
    const promptStartedAt = performance.now();
    const endpointStatuses: string[] = [];
    let stepInstrumentation: TrialApplyStepInstrumentation = {
      prompt_packet_requested_at: new Date().toISOString(),
    };
    const pushProgress = (
      patch: Partial<DurableCodingRunRow>,
      runPatch: Partial<DurableCodingRun> = {},
      instrumentationPatch?: TrialApplyStepInstrumentation,
    ) => {
      if (instrumentationPatch) {
        stepInstrumentation = mergeStepInstrumentation(stepInstrumentation, instrumentationPatch);
      }
      void postDurableCodingRunPromptProgress(
        suiteId,
        prompt,
        {
          ...patch,
          step_instrumentation: stepInstrumentation,
        },
        runPatch,
      );
    };
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
      provenance: normalizeTrialResultProvenance(undefined),
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
    let taskResponse: Response;
    const taskCreateInit = {
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
      signal: suiteFetchAbortRef.current?.signal ?? undefined,
    };
    try {
      taskResponse = await fetchLongRunningTaskWithRetry(
        taskCreateInit,
        TRIAL_LONG_RUNNING_TIMEOUT_MS,
        {
          maxAttempts: TRIAL_LONG_RUNNING_MAX_ATTEMPTS,
          onTransientError: (attempt, error) => {
            endpointStatuses.push(`/v1/tasks/long-running(retry ${attempt}):${promptPacketEndpointStatusForError(error)}`);
            onStep?.(`Reading request (retry ${attempt + 1}/${TRIAL_LONG_RUNNING_MAX_ATTEMPTS})`);
            pushProgress(
              {
                endpoint_statuses: [...endpointStatuses],
                error_summary: `transient /v1/tasks/long-running fetch error; retry ${attempt}/${TRIAL_LONG_RUNNING_MAX_ATTEMPTS - 1}`,
              },
              {
                endpoint_statuses: [...endpointStatuses],
                final_summary: "Retrying long-running task create",
              },
            );
          },
        },
      );
    } catch (error) {
      if (suiteFetchAbortRef.current?.signal.aborted) {
        throw new Error("user_stop");
      }
      endpointStatuses.push(`/v1/tasks/long-running:${promptPacketEndpointStatusForError(error)}`);
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: `timeout_source: /v1/tasks/long-running; timeout_layer: ${timeoutLayerFromError(error)}`,
        failure_reason: error instanceof Error ? error.message : "Long-running task create timed out.",
        next_recommended_action: "Restart spiritos-lan if /v1/tasks/long-running is wedged, then rerun from this prompt.",
        visible_result_label: "NEEDS FIX",
      });
    }
    const taskRead = await readApiResponse(taskResponse, "/v1/tasks/long-running");
    const taskPayload = taskRead.payload;
    endpointStatuses.push(`/v1/tasks/long-running:${taskResponse.status}`);
    if (taskRead.routeFailure) {
      return buildRouteUnavailablePromptResult(baseResult, taskRead.routeFailure, endpointStatuses);
    }
    void postDurableCodingRunPromptProgress(
      suiteId,
      prompt,
      {
        endpoint_statuses: [...endpointStatuses],
        model_called_for_generation: selectedProviderTruth.modelId || selectedProviderTruth.modelLabel || "none",
      },
      {
        endpoint_statuses: [...endpointStatuses],
        final_summary: "Reading request",
        model: selectedProviderTruth.modelId || selectedProviderTruth.modelLabel || "none",
        model_called_for_generation: selectedProviderTruth.modelId || selectedProviderTruth.modelLabel || "none",
        provider: selectedProviderTruth.providerLabel,
      },
    );
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

    onStep?.(previewLoadingPhaseLabel(sourceProxyReachable, "promptPacket"));
    const promptPacketStartedStatuses = [...endpointStatuses, "/v1/decisions/prompt-packet:started"];
    await postDurableCodingRunPromptProgress(
      suiteId,
      prompt,
      {
        endpoint_statuses: promptPacketStartedStatuses,
        model_called_for_generation: selectedProviderTruth.modelId || selectedProviderTruth.modelLabel || "none",
      },
      {
        endpoint_statuses: promptPacketStartedStatuses,
        final_summary: previewLoadingPhaseLabel(sourceProxyReachable, "promptPacket"),
        model: selectedProviderTruth.modelId || selectedProviderTruth.modelLabel || "none",
        model_called_for_generation: selectedProviderTruth.modelId || selectedProviderTruth.modelLabel || "none",
        provider: selectedProviderTruth.providerLabel,
      },
    );
    const promptPacketSignal = suiteFetchAbortRef.current?.signal ?? undefined;
    const trialPromptPacketRetry = {
      maxAttempts: TRIAL_PROMPT_PACKET_MAX_ATTEMPTS,
      onRetry: (attempt: number) => {
        if (attempt > 1) {
          onStep?.(`Running prompt-packet (retry ${attempt}/${TRIAL_PROMPT_PACKET_MAX_ATTEMPTS})`);
        }
      },
      totalBudgetMs: TRIAL_PROMPT_PACKET_TIMEOUT_MS,
    };
    let proposalResponse: Response;
    try {
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
          signal: promptPacketSignal,
        },
        MANUAL_PROMPT_PACKET_TIMEOUT_MS,
        trialPromptPacketRetry,
      );
    } catch (error) {
      if (promptPacketSignal?.aborted || suiteFetchAbortRef.current?.signal.aborted) {
        throw new Error("user_stop");
      }
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
    let proposalRead = await readApiResponse(proposalResponse, "/v1/decisions/prompt-packet");
    let proposalPayload = proposalRead.payload;
    endpointStatuses.push(`/v1/decisions/prompt-packet:${proposalResponse.status}`);
    if (proposalRead.routeFailure) {
      return buildRouteUnavailablePromptResult(
        baseResult,
        proposalRead.routeFailure,
        endpointStatuses,
        undefined,
        false,
        taskId,
      );
    }
    if (!proposalResponse.ok) {
      await postDurableCodingRunPromptProgress(
        suiteId,
        prompt,
        { endpoint_statuses: [...endpointStatuses] },
        {
          endpoint_statuses: [...endpointStatuses],
          final_summary: `prompt-packet failed (${proposalResponse.status})`,
        },
      );
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
    await postDurableCodingRunPromptProgress(
      suiteId,
      prompt,
      {
        endpoint_statuses: [...endpointStatuses],
        generated_diff_present: proposedDiff.trim().length > 0,
        model_called_for_generation: modelCalledForGeneration,
        provider_call_made: providerCallMade,
        reason_code: promptPacketReasonCode,
      },
      {
        endpoint_statuses: [...endpointStatuses],
        final_summary: providerCallMade ? "prompt-packet returned; calling model" : "prompt-packet returned; awaiting provider proof",
        generated_diff_present: proposedDiff.trim().length > 0,
        model: modelCalledForGeneration,
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: providerCallMade,
        reason_code: promptPacketReasonCode || null,
      },
    );
    if (
      prompt.expectedOutcome === "edit_reversible" &&
      !proposedDiff.trim() &&
      promptPacketReasonCode === "coder_no_changes_needed" &&
      !providerCallMade &&
      (packet.selectedTarget ?? prompt.targetFile).startsWith("src/")
    ) {
      onStep?.("Recovering prompt-packet route");
      await postDurableCodingRunPromptProgress(
        suiteId,
        prompt,
        { endpoint_statuses: [...endpointStatuses] },
        {
          endpoint_statuses: [...endpointStatuses],
          final_summary: "Recovering prompt-packet route (already-satisfied retry)",
        },
      );
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
          signal: promptPacketSignal,
        },
        MANUAL_PROMPT_PACKET_TIMEOUT_MS,
        trialPromptPacketRetry,
      );
      proposalRead = await readApiResponse(proposalResponse, "/v1/decisions/prompt-packet");
      proposalPayload = proposalRead.payload;
      endpointStatuses.push(`/v1/decisions/prompt-packet(product-retry):${proposalResponse.status}`);
      if (proposalRead.routeFailure) {
        return buildRouteUnavailablePromptResult(
          baseResult,
          proposalRead.routeFailure,
          endpointStatuses,
          undefined,
          false,
          taskId,
        );
      }
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
    await postDurableCodingRunPromptProgress(
      suiteId,
      prompt,
      {
        endpoint_statuses: [...endpointStatuses],
        generated_diff_present: proposedDiff.trim().length > 0,
        model_called_for_generation: modelCalledForGeneration,
        provider_call_made: providerCallMade,
        reason_code: promptPacketReasonCode,
      },
      {
        endpoint_statuses: [...endpointStatuses],
        final_summary: providerCallMade ? "Model returned; previewing diff" : "prompt-packet finished without provider proof",
        generated_diff_present: proposedDiff.trim().length > 0,
        model: modelCalledForGeneration,
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: providerCallMade,
        reason_code: promptPacketReasonCode || null,
      },
    );
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
          signal: promptPacketSignal,
        },
        MANUAL_PROMPT_PACKET_TIMEOUT_MS,
        trialPromptPacketRetry,
      );
      proposalRead = await readApiResponse(proposalResponse, "/v1/decisions/prompt-packet");
      proposalPayload = proposalRead.payload;
      endpointStatuses.push(`/v1/decisions/prompt-packet(retry):${proposalResponse.status}`);
      if (proposalRead.routeFailure) {
        return buildRouteUnavailablePromptResult(
          baseResult,
          proposalRead.routeFailure,
          endpointStatuses,
          undefined,
          false,
          taskId,
        );
      }
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
      const alreadySatisfiedClassification = classifyEditReversibleAlreadySatisfied({
        baselineCleanForFreshSuite: options.baselineCleanForFreshSuite ?? null,
        expectedOutcome: prompt.expectedOutcome,
        promptPacketReasonCode,
        proposedDiff,
        providerCallMade,
      });
      if (alreadySatisfiedClassification.kind === "needs_fix") {
        pushProgress(
          {
            endpoint_statuses: [...endpointStatuses],
            model_called_for_generation: modelCalledForGeneration,
            provider_call_made: true,
            reason_code: alreadySatisfiedClassification.reason_code,
            result_label: "NEEDS FIX",
          },
          {
            final_summary: `Prompt classified as ${alreadySatisfiedClassification.reason_code}`,
            model: modelCalledForGeneration,
            model_called_for_generation: modelCalledForGeneration,
            provider: providerTruth.providerLabel,
            provider_call_made: true,
          },
          {
            last_progress_reason_code: alreadySatisfiedClassification.reason_code,
            prompt_packet_completed_at: new Date().toISOString(),
            result_finalized_at: new Date().toISOString(),
          },
        );
        return finalizeReversibleTrialResult(
          baseResult({
            checks_result: alreadySatisfiedClassification.reason_code,
            error_summary: `reason_code=${alreadySatisfiedClassification.reason_code}`,
            failure_reason: `NEEDS FIX: edit-required prompt reported already satisfied without expected-no-edit proof (${alreadySatisfiedClassification.reason_code}).`,
            model_called_for_generation: modelCalledForGeneration,
            next_recommended_action:
              alreadySatisfiedClassification.reason_code === "dirty_baseline_already_satisfied"
                ? "Reverse trial edits and clear agent-lab leftovers before rerunning."
                : "Inspect prompt-packet/disk proof. Already satisfied cannot count as success for edit_reversible prompts.",
            provider: providerTruth.providerLabel,
            provider_call_made: true,
            run_id: taskId,
            reverse_status_text: "No applied trial edit with reversal proof.",
            visible_result_label: "NEEDS FIX",
          }),
        );
      }
      pushProgress(
        {},
        {},
        {
          last_progress_reason_code: "coder_no_changes_needed",
          prompt_packet_completed_at: new Date().toISOString(),
          result_finalized_at: new Date().toISOString(),
        },
      );
      return finalizeReversibleTrialResult(
        baseResult({
          checks_result: "already satisfied on disk; live model call recorded",
          failure_reason: "",
          model_called_for_generation: modelCalledForGeneration,
          provider: providerTruth.providerLabel,
          provider_call_made: true,
          run_id: taskId,
          reverse_status_text: "Product code already satisfies this prompt; no trial edit was applied.",
          visible_result_label: "ALREADY SATISFIED",
        }),
      );
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
      const noDiffClassification = classifyNoDiffModelResponse({
        allowedFiles: packet.allowedFiles,
        payload: proposalPayload,
        selectedTarget: packet.selectedTarget ?? prompt.targetFile,
      });
      pushProgress(
        {
          endpoint_statuses: [...endpointStatuses],
          model_called_for_generation: modelCalledForGeneration,
          provider_call_made: true,
          reason_code: noDiffClassification.reasonCode,
          result_label: "NEEDS FIX",
        },
        {
          endpoint_statuses: [...endpointStatuses],
          final_summary: `Prompt classified as ${noDiffClassification.reasonCode}`,
          model: modelCalledForGeneration,
          model_called_for_generation: modelCalledForGeneration,
          provider: providerTruth.providerLabel,
          provider_call_made: true,
          reason_code: noDiffClassification.reasonCode,
        },
        {
          last_progress_reason_code: noDiffClassification.reasonCode,
          model_response_classification: noDiffClassification.reasonCode,
          model_response_parse_decision: noDiffClassification.parseDecision,
          model_response_raw_length: noDiffClassification.rawResponseLength,
          model_response_safe_excerpt: noDiffClassification.safeExcerpt,
          no_diff_reason_code: noDiffClassification.reasonCode,
          prompt_packet_completed_at: new Date().toISOString(),
          result_finalized_at: new Date().toISOString(),
        },
      );
      return baseResult({
        error_summary: [
          "proof_missing: diff_preview_missing",
          "provider_call_made=true",
          noDiffClassification.summary,
          `endpoint_statuses=${formatList(endpointStatuses, "none")}`,
        ].join("; "),
        failure_reason: `NEEDS FIX: Live apply proof missing: ${noDiffClassification.reasonCode}.`,
        model_called_for_generation: modelCalledForGeneration,
        next_recommended_action:
          noDiffClassification.reasonCode === "model_empty_response"
            ? "Check Ollama/qwen availability and retry; the model returned an empty body."
            : noDiffClassification.reasonCode === "model_code_block_unparsed" ||
                noDiffClassification.reasonCode === "model_full_file_unconverted"
              ? "Inspect prompt-packet coder_diagnostics and add a bounded extractor only for selected_target/allowed_files if the content is safe."
              : noDiffClassification.reasonCode === "allowed_files_rejected_change"
                ? "Keep the allowed-files gate strict and retry with a target that matches allowed_files."
                : "Inspect prompt-packet coder_diagnostics. A 200 route without diff preview proof must not count as PASS.",
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        checks_result: noDiffClassification.reasonCode,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }

    onStep?.("Finding files");
    let diffResponse: Response;
    try {
      diffResponse = await fetchWithTimeout("/v1/verification/diff-preview", {
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
        signal: suiteFetchAbortRef.current?.signal ?? undefined,
      }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
    } catch (error) {
      endpointStatuses.push(`/v1/verification/diff-preview:${promptPacketEndpointStatusForError(error)}`);
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: `timeout_source: /v1/verification/diff-preview; timeout_layer: ${timeoutLayerFromError(error)}`,
        failure_reason: error instanceof Error ? error.message : "Diff preview timed out.",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    const diffRead = await readApiResponse(diffResponse, "/v1/verification/diff-preview");
    const diffPayload = diffRead.payload;
    endpointStatuses.push(`/v1/verification/diff-preview:${diffResponse.status}`);
    if (diffRead.routeFailure) {
      return buildRouteUnavailablePromptResult(
        baseResult,
        diffRead.routeFailure,
        endpointStatuses,
        undefined,
        true,
        taskId,
      );
    }
    void postDurableCodingRunPromptProgress(
      suiteId,
      prompt,
      {
        endpoint_statuses: [...endpointStatuses],
        generated_diff_present: proposedDiff.trim().length > 0,
        model_called_for_generation: modelCalledForGeneration,
        provider_call_made: true,
      },
      {
        endpoint_statuses: [...endpointStatuses],
        final_summary: "Diff preview returned; preparing apply",
        generated_diff_present: proposedDiff.trim().length > 0,
        model: modelCalledForGeneration,
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
      },
    );
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

    if (previewChangedFiles.some((file) => file.startsWith("src/app/"))) {
      await waitForV1RoutesAfterHmr({
        maxAttempts: 5,
        delayMs: 400,
        signal: suiteFetchAbortRef.current?.signal,
      });
    }

    const approvalAction = `Live trial ${prompt.id}`;
    const contextHashBytes = await window.crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(`${prompt.id}|${prompt.prompt}|${packet.selectedTarget}`),
    );
    const contextHash = Array.from(new Uint8Array(contextHashBytes))
      .map((value) => value.toString(16).padStart(2, "0"))
      .join("");
    const approvalPreviewResponse = await fetchWithTimeout(
      `/v1/tasks/long-running/${encodeURIComponent(taskId)}/approval-preview`,
      {
        body: JSON.stringify({
          action: approvalAction,
          approved_diff: proposedDiff,
          context_hash: contextHash,
          selected_prompt_id: prompt.id,
          target: packet.selectedTarget,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
        signal: suiteFetchAbortRef.current?.signal ?? undefined,
      },
      TRIAL_POST_MODEL_STAGE_TIMEOUT_MS,
    );
    const approvalPreviewPayload = await readJson(approvalPreviewResponse);
    endpointStatuses.push(`/v1/tasks/long-running/${taskId}/approval-preview:${approvalPreviewResponse.status}`);
    if (!approvalPreviewResponse.ok) {
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: safePayloadSummary(approvalPreviewPayload),
        failure_reason: messageFromPayload(approvalPreviewPayload, approvalPreviewResponse.status),
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    const approvalPreview = asRecord(asRecord(approvalPreviewPayload).preview);
    const previewId = stringValue(approvalPreview.preview_id);
    const previewGeneration = numberValue(approvalPreview.generation);
    if (!previewId || !previewGeneration) {
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: "approval_preview_missing_server_identity",
        failure_reason: "The durable approval preview did not return a server-owned ID and generation.",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    const csrf = operatorSession.status === "authenticated" && operatorCsrf ? operatorCsrf : "";
    if (!csrf) {
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: "operator_session_required",
        failure_reason: "The selected prompt remains preview-only until the canonical shell has an authenticated operator session.",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        run_id: taskId,
        visible_result_label: "BLOCKED",
      });
    }
    const operatorApprovalResponse = await fetchWithTimeout("/v1/operator/approval", {
      body: JSON.stringify({ action: "approve", generation: previewGeneration, preview_id: previewId, task_id: taskId }),
      headers: { "content-type": "application/json", "x-spiritos-csrf": csrf },
      method: "POST",
      signal: suiteFetchAbortRef.current?.signal ?? undefined,
    }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
    const operatorApprovalPayload = await readJson(operatorApprovalResponse);
    endpointStatuses.push(`/v1/operator/approval:${operatorApprovalResponse.status}`);
    const approvalId = stringValue(asRecord(asRecord(operatorApprovalPayload).approval).approval_id);
    if (!operatorApprovalResponse.ok || !approvalId) {
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: safePayloadSummary(operatorApprovalPayload),
        failure_reason: messageFromPayload(operatorApprovalPayload, operatorApprovalResponse.status),
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        run_id: taskId,
        visible_result_label: "BLOCKED",
      });
    }

    onStep?.("Editing files");
    pushProgress(
      {
        endpoint_statuses: [...endpointStatuses],
        preview_changed_files: previewChangedFiles,
        provider_call_made: true,
      },
      {
        final_summary: "Editing files",
        preview_changed_files: previewChangedFiles,
      },
      {
        diff_preview_completed_at: new Date().toISOString(),
        execute_approved_requested_at: new Date().toISOString(),
      },
    );
    let applyResponse: Response;
    try {
      applyResponse = await fetchWithTimeout("/v1/actions/execute-approved", {
        body: JSON.stringify({
          action: approvalAction,
          approval_id: approvalId,
          approved_diff: proposedDiff,
          allowed_files: packet.allowedFiles,
          target: packet.selectedTarget,
          task_id: taskId,
          trial_prompt_id: prompt.id,
          trial_prompt_text: prompt.prompt,
          trial_suite_id: suiteId,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
        signal: suiteFetchAbortRef.current?.signal ?? undefined,
      }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
    } catch (error) {
      if (suiteFetchAbortRef.current?.signal.aborted) {
        throw new Error("user_stop");
      }
      endpointStatuses.push(`/v1/actions/execute-approved:${promptPacketEndpointStatusForError(error)}`);
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: `timeout_source: /v1/actions/execute-approved; timeout_layer: ${timeoutLayerFromError(error)}`,
        failure_reason: error instanceof Error ? error.message : "Apply route timed out.",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    endpointStatuses.push(`/v1/actions/execute-approved:${applyResponse.status}`);
    const applyResponseContentType = applyResponse.headers.get("content-type") ?? "unknown";
    pushProgress(
      {
        endpoint_statuses: [...endpointStatuses],
        model_called_for_generation: modelCalledForGeneration,
        preview_changed_files: previewChangedFiles,
        provider_call_made: true,
      },
      {
        endpoint_statuses: [...endpointStatuses],
        final_summary: "Apply route returned; reading execute-approved proof",
        model: modelCalledForGeneration,
        model_called_for_generation: modelCalledForGeneration,
        preview_changed_files: previewChangedFiles,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
      },
      {
        execute_approved_body_read_started_at: new Date().toISOString(),
        execute_approved_completed_at: new Date().toISOString(),
        execute_approved_content_type: applyResponseContentType,
        execute_approved_http_status: String(applyResponse.status),
        last_progress_reason_code: applyResponse.ok
          ? "execute_approved_http_200_body_pending"
          : "execute_approved_http_error_body_pending",
      },
    );
    let applyRead: Awaited<ReturnType<typeof readApiResponse>>;
    try {
      applyRead = await readApiResponse(applyResponse, "/v1/actions/execute-approved", undefined, {
        bodyTimeoutMs: TRIAL_POST_MODEL_STAGE_TIMEOUT_MS,
        signal: suiteFetchAbortRef.current?.signal,
      });
    } catch (error) {
      if (suiteFetchAbortRef.current?.signal.aborted) {
        throw new Error("user_stop");
      }
      endpointStatuses.push(`/v1/actions/execute-approved:body_${promptPacketEndpointStatusForError(error)}`);
      const reasonCode = "execute_approved_body_read_failed";
      pushProgress(
        {
          endpoint_statuses: [...endpointStatuses],
          error_summary: `reason_code=${reasonCode}; timeout_source=/v1/actions/execute-approved body; timeout_layer=${timeoutLayerFromError(error)}`,
          preview_changed_files: previewChangedFiles,
          reason_code: reasonCode,
          result_label: "NEEDS FIX",
        },
        {
          endpoint_statuses: [...endpointStatuses],
          final_summary: "Apply route body read failed after execute-approved returned.",
          last_error: error instanceof Error ? error.message : "Apply route body read timed out.",
          reason_code: reasonCode,
        },
        {
          execute_approved_body_read_failed_at: new Date().toISOString(),
          last_progress_reason_code: reasonCode,
          result_finalized_at: new Date().toISOString(),
        },
      );
      return baseResult({
        endpoint_statuses: [...endpointStatuses],
        error_summary: `timeout_source: /v1/actions/execute-approved body; timeout_layer: ${timeoutLayerFromError(error)}`,
        failure_reason: error instanceof Error ? error.message : "Apply route body read timed out.",
        model_called_for_generation: modelCalledForGeneration,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        preview_changed_files: previewChangedFiles,
        run_id: taskId,
        visible_result_label: "NEEDS FIX",
      });
    }
    const applyPayload = applyRead.payload;
    pushProgress(
      {
        endpoint_statuses: [...endpointStatuses],
        model_called_for_generation: modelCalledForGeneration,
        preview_changed_files: previewChangedFiles,
        provider_call_made: true,
      },
      {
        endpoint_statuses: [...endpointStatuses],
        final_summary: "Apply route returned; checking disk state",
        model: modelCalledForGeneration,
        model_called_for_generation: modelCalledForGeneration,
        preview_changed_files: previewChangedFiles,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
      },
      {
        execute_approved_body_read_completed_at: new Date().toISOString(),
        disk_probe_started_at: new Date().toISOString(),
        last_progress_reason_code: applyResponse.ok ? "execute_approved_body_read" : "execute_approved_failed",
      },
    );
    if (applyRead.routeFailure) {
      return buildRouteUnavailablePromptResult(
        baseResult,
        applyRead.routeFailure,
        endpointStatuses,
        undefined,
        true,
        taskId,
      );
    }
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
    const missingBeforeSnapshots = appliedChangedFiles.filter((file) => !snapshotHasRestorableBaseline(applySnapshots, file));
    const reverseDiff = reverseUnifiedDiff(proposedDiff);
    const reversalAvailable = reverseDiff.trim().length > 0;
    pushProgress(
      {
        applied_changed_files: appliedChangedFiles,
        disk_changed_files: diskChangedFiles,
        endpoint_statuses: [...endpointStatuses],
        preview_changed_files: previewChangedFiles,
        provider_call_made: true,
      },
      {},
      {
        checks_started_at: new Date().toISOString(),
        disk_probe_completed_at: new Date().toISOString(),
      },
    );
    if (appliedChangedFiles.length === 0 || diskChangedFiles.length === 0) {
      const reasonCode = "apply_ack_no_disk_proof";
      pushProgress(
        {
          endpoint_statuses: [...endpointStatuses],
          reason_code: reasonCode,
          result_label: "NEEDS FIX",
        },
        {},
        {
          checks_completed_at: new Date().toISOString(),
          last_progress_reason_code: reasonCode,
          result_finalized_at: new Date().toISOString(),
        },
      );
      return finalizeReversibleTrialResult(
        baseResult({
          applied_changed_files: appliedChangedFiles,
          checks_result: "recorded",
          disk_changed_files: [],
          error_summary: `reason_code=${reasonCode}`,
          failure_reason: "NEEDS FIX: execute-approved returned 200 but no disk/applied proof was recorded.",
          model_called_for_generation: modelCalledForGeneration,
          next_recommended_action: postApplyStaleNextAction(reasonCode),
          provider: providerTruth.providerLabel,
          provider_call_made: true,
          preview_changed_files: previewChangedFiles,
          reverse_diff: reverseDiff,
          reversal_available: reversalAvailable,
          run_id: taskId,
          visible_result_label: "NEEDS FIX",
        }),
      );
    }
    if (previewChangedFiles.length === 0 || missingBeforeSnapshots.length > 0) {
      return baseResult({
        applied_changed_files: appliedChangedFiles,
        checks_result: "recorded",
        disk_changed_files: diskChangedFiles,
        failure_reason:
          previewChangedFiles.length === 0
            ? "Needs fix: generated diff did not produce preview changed files."
            : `Needs fix: restorable baseline snapshot missing for ${formatList(missingBeforeSnapshots, "changed files")}.`,
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

    if (diskChangedFiles.some((file) => file.startsWith("src/app/"))) {
      const postApplyHmrStartedAt = Date.now();
      const postApplyHmr = await waitForV1RoutesAfterHmr({
        maxAttempts: 5,
        delayMs: 400,
        signal: suiteFetchAbortRef.current?.signal,
      });
      if ("cancelled" in postApplyHmr && postApplyHmr.cancelled) {
        throw new Error("user_stop");
      }
      if (!postApplyHmr.ok && "failure" in postApplyHmr) {
        return buildRouteUnavailablePromptResult(
          baseResult,
          postApplyHmr.failure,
          endpointStatuses,
          undefined,
          true,
          taskId,
        );
      }
    }

    if (!prompt.autoRevert) {
      onStep?.("Prompt passed; continuing suite");
      pushProgress(
        {
          applied_changed_files: appliedChangedFiles,
          checks_run: packet.checks,
          disk_changed_files: diskChangedFiles,
          endpoint_statuses: [...endpointStatuses],
          preview_changed_files: previewChangedFiles,
          reversal_available: true,
          reversal_status: "available",
          result_label: "PASS",
        },
        {
          applied_changed_files: appliedChangedFiles,
          disk_changed_files: diskChangedFiles,
          final_summary: "Prompt passed; continuing suite",
        },
        {
          checks_completed_at: new Date().toISOString(),
          last_progress_reason_code: "pass_with_reversal_proof",
          result_finalized_at: new Date().toISOString(),
          reverse_receipt_created_at: new Date().toISOString(),
        },
      );
      return finalizeReversibleTrialResult(
        baseResult({
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
        }),
      );
    }

    onStep?.("Undoing trial edit");
    const revertTaskResponse = await fetch("/v1/tasks/long-running", {
      body: JSON.stringify({ description: `Revert reversible trial ${prompt.id}` }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const revertTaskPayload = await readJson(revertTaskResponse);
    endpointStatuses.push(`/v1/tasks/long-running(revert):${revertTaskResponse.status}`);
    void postDurableCodingRunPromptProgress(
      suiteId,
      prompt,
      {
        applied_changed_files: appliedChangedFiles,
        disk_changed_files: diskChangedFiles,
        endpoint_statuses: [...endpointStatuses],
        model_called_for_generation: modelCalledForGeneration,
        preview_changed_files: previewChangedFiles,
        provider_call_made: true,
        reversal_available: true,
        reversal_status: "available",
      },
      {
        applied_changed_files: appliedChangedFiles,
        disk_changed_files: diskChangedFiles,
        endpoint_statuses: [...endpointStatuses],
        final_summary: "Trial edit applied; creating revert task",
        model: modelCalledForGeneration,
        model_called_for_generation: modelCalledForGeneration,
        preview_changed_files: previewChangedFiles,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        reversal_available: true,
        reversal_status: "available",
      },
    );
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
    let revertResponse: Response;
    try {
      revertResponse = await fetchWithTimeout("/v1/actions/execute-approved", {
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
      }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
    } catch (error) {
      endpointStatuses.push(`/v1/actions/execute-approved(revert):${promptPacketEndpointStatusForError(error)}`);
      return baseResult({
        applied_changed_files: appliedChangedFiles,
        checks_result: "recorded",
        disk_changed_files: diskChangedFiles,
        endpoint_statuses: [...endpointStatuses],
        error_summary: `timeout_source: /v1/actions/execute-approved(revert); timeout_layer: ${timeoutLayerFromError(error)}`,
        failure_reason: error instanceof Error ? error.message : "Reverse route timed out.",
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
    const revertPayload = await readJson(revertResponse);
    endpointStatuses.push(`/v1/actions/execute-approved(revert):${revertResponse.status}`);
    void postDurableCodingRunPromptProgress(
      suiteId,
      prompt,
      {
        applied_changed_files: appliedChangedFiles,
        disk_changed_files: diskChangedFiles,
        endpoint_statuses: [...endpointStatuses],
        model_called_for_generation: modelCalledForGeneration,
        preview_changed_files: previewChangedFiles,
        provider_call_made: true,
        reversal_available: true,
        reversal_status: revertResponse.ok ? "reverted" : "available",
      },
      {
        applied_changed_files: appliedChangedFiles,
        disk_changed_files: diskChangedFiles,
        endpoint_statuses: [...endpointStatuses],
        final_summary: revertResponse.ok ? "Reverse route returned; checking restoration" : "Reverse route failed",
        model: modelCalledForGeneration,
        model_called_for_generation: modelCalledForGeneration,
        preview_changed_files: previewChangedFiles,
        provider: providerTruth.providerLabel,
        provider_call_made: true,
        reversal_available: true,
        reversal_status: revertResponse.ok ? "reverted" : "available",
      },
    );
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

  async function handleRunReversibleSuite(
    resumeState?: ReversibleSuiteState,
    options: { forceResume?: boolean } = {},
  ) {
    // #region agent log
    fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
      body: JSON.stringify({
        sessionId: "0fdea5",
        hypothesisId: "H4",
        location: "CodingCockpitShell.tsx:handleRunReversibleSuite",
        message: "run click entered",
        data: {
          isResume: Boolean(resumeState?.suiteId),
          suiteStatus: reversibleSuiteState.status,
          baselineLoadState: agentLabBaselineLoadState,
          baselineClean: agentLabBaselineSnapshot?.baseline_clean_for_fresh_suite ?? null,
          dirtyCount: agentLabBaselineSnapshot?.baseline_dirty_agent_lab_files.length ?? null,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    const isResume = Boolean(resumeState?.suiteId);
    if (
      !isResume &&
      (reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping")
    ) {
      return;
    }
    if (isResume && reversibleSuiteResumeBlocked && !options.forceResume) {
      setReversibleSuiteCopyStatus(reversibleSuiteResumeBlockedMessage);
      // #region agent log
      fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
        body: JSON.stringify({
          sessionId: "0fdea5",
          hypothesisId: "H10",
          location: "CodingCockpitShell.tsx:handleRunReversibleSuite",
          message: "resume blocked active guard",
          data: {
            isReverting,
            backgroundCleanupActive,
            suiteStatus: reversibleSuiteState.status,
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      return;
    }
    if (!isResume) {
      const latestBaseline =
        reversibleTrialCategory === "Coder" ? await refreshAgentLabBaseline() : agentLabBaselineSnapshot;
      if (reversibleTrialCategory === "Coder" && !latestBaseline) {
        const blockMessage = `Agent Lab baseline check failed: ${agentLabBaselineLoadError || "Source Proxy unreachable or SPIRIT_CODING_USE_PROXY is off."}`;
        setReversibleSuiteCopyStatus(blockMessage);
        // #region agent log
        fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
          body: JSON.stringify({
            sessionId: "0fdea5",
            hypothesisId: "H4",
            location: "CodingCockpitShell.tsx:handleRunReversibleSuite",
            message: "run blocked baseline fetch failed",
            data: { blockMessage },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        return;
      }
      if (reversibleTrialCategory === "Coder" && latestBaseline && !latestBaseline.baseline_clean_for_fresh_suite) {
        const blockMessage = `Agent Lab still has ${latestBaseline.baseline_dirty_agent_lab_files.length} leftover file(s). Reverse them before a fresh Coder benchmark.`;
        setReversibleSuiteCopyStatus(blockMessage);
        setAgentLabBaselineSnapshot(latestBaseline);
        // #region agent log
        fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
          body: JSON.stringify({
            sessionId: "0fdea5",
            hypothesisId: "H4",
            location: "CodingCockpitShell.tsx:handleRunReversibleSuite",
            message: "run blocked baseline dirty",
            data: { blockMessage, dirtyFiles: latestBaseline.baseline_dirty_agent_lab_files },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        return;
      }
      if (trialRunnerBlock.blocked) {
        setReversibleSuiteCopyStatus(trialRunnerBlock.message);
        return;
      }
    }
    if (!normalizeReversibleTrialCategoryInput(reversibleTrialCategory)) {
      setReversibleSuiteCopyStatus(
        `Category invalid: "${reversibleTrialCategory}". Use ${reversibleTrialCategories.join(", ")}.`,
      );
      return;
    }
    const runCount = resumeState?.count ?? reversibleTrialCount;
    const suiteId = resumeState?.suiteId || `suite-${Date.now().toString(36)}`;
    const prompts = selectReversibleTrialPrompts(runCount, reversibleTrialCategory);
    const startIndex = isResume ? Math.min(Math.max(resumeState?.completed ?? 0, 0), prompts.length) : 0;
    let runSourceProxyReachable = sourceProxyReachable;
    let runProviderTruth = selectedProviderTruth;
    if (!isResume) {
      try {
        const response = await fetch("/v1/self/status", { method: "GET" });
        if (response.ok) {
          const payload = await response.json() as unknown;
          runSourceProxyReachable = true;
          runProviderTruth = providerModelTruthFromSelfStatus(payload);
          setSourceProxyReachable(true);
          setOllamaStoragePath(ollamaStoragePathFromSelfStatus(payload));
          setSelectedProviderTruth(runProviderTruth);
        } else {
          runSourceProxyReachable = false;
          setSourceProxyReachable(false);
        }
      } catch {
        runSourceProxyReachable = false;
        setSourceProxyReachable(false);
      }
    }
    const modelLaneUnavailable =
      !runSourceProxyReachable ||
      runProviderTruth.status === "unavailable" ||
      runProviderTruth.providerModelProbeOk === false;
    if (!isResume && modelLaneUnavailable) {
      const reason = !runSourceProxyReachable
        ? "Source Proxy is unreachable at /v1/self/status."
        : runProviderTruth.blockedReason ||
          `${runProviderTruth.modelLabel} is not available from the configured local model lane.`;
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
        provider: runProviderTruth.providerLabel,
        model: runProviderTruth.modelLabel,
        results: [],
        reverted: 0,
        safetyBlock: 0,
        status: "failed",
        stopped: false,
        suiteFinishedAt: performance.now(),
        suiteId,
        suiteStartedAt: performance.now(),
        timeout: 0,
        baselineCheckedAt: null,
        baselineAgentLabFiles: [],
        baselineDirtyAgentLabFiles: [],
        baselineUnrevertedReceipts: [],
        baselineCleanForFreshSuite: null,
      };
      setReversibleSuiteCopyStatus(
        `Trial blocked before run: ${reason} Run curl -k https://127.0.0.1:8787/v1/models and install or select an available Ollama model.`,
      );
      setReversibleSuiteState(blockedState);
      storeReversibleSuiteState(blockedState);
      const blockedRun = await createDurableCodingRunForSuite(blockedState);
      setBackendRunSync({
        lastSyncedAt: new Date().toISOString(),
        message: blockedRun ? "Synced from backend" : "Backend sync failed",
        runId: blockedRun?.run_id ?? suiteId,
        status: blockedRun ? "synced" : "error",
      });
      return;
    }
    let agentLabBaseline: AgentLabBaselineSnapshot | null = null;
    if (!isResume && reversibleTrialCategory === "Coder") {
      agentLabBaseline = await fetchAgentLabBaselineSnapshot();
      if (agentLabBaseline && !agentLabBaseline.baseline_clean_for_fresh_suite) {
        const dirtyState: ReversibleSuiteState = {
          ...defaultReversibleSuiteState(),
          baselineAgentLabFiles: agentLabBaseline.baseline_agent_lab_files,
          baselineCheckedAt: agentLabBaseline.baseline_checked_at,
          baselineCleanForFreshSuite: false,
          baselineDirtyAgentLabFiles: agentLabBaseline.baseline_dirty_agent_lab_files,
          baselineUnrevertedReceipts: agentLabBaseline.baseline_unreverted_receipts,
          count: runCount,
          currentStep: "BASELINE DIRTY",
          interruptionReason:
            "Agent Lab contains leftovers from a prior suite. Reverse trial edits before rerunning.",
          interruptionSource: "route_failed",
          provider: runProviderTruth.providerLabel,
          model: runProviderTruth.modelLabel,
          status: "failed",
          suiteFinishedAt: performance.now(),
          suiteId,
          suiteStartedAt: performance.now(),
        };
        setReversibleSuiteCopyStatus(
          "Agent Lab contains leftovers from a prior suite. Reverse trial edits before rerunning.",
        );
        setReversibleSuiteState(dirtyState);
        storeReversibleSuiteState(dirtyState);
        setAgentLabBaselineSnapshot(agentLabBaseline);
        return;
      }
      if (agentLabBaseline) {
        setAgentLabBaselineSnapshot(agentLabBaseline);
      }
    }
    stopReversibleSuiteAfterCurrentRef.current = false;
    suiteFetchAbortRef.current?.abort();
    suiteFetchAbortRef.current = new AbortController();
    localReversibleSuiteRunningRef.current = true;
    touchReversibleSuiteRunnerLease(suiteId);
    const suiteRunnerLeaseInterval = window.setInterval(() => touchReversibleSuiteRunnerLease(suiteId), 5_000);
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
      baselineCheckedAt:
        agentLabBaseline?.baseline_checked_at ??
        resumeState?.baselineCheckedAt ??
        null,
      baselineAgentLabFiles:
        agentLabBaseline?.baseline_agent_lab_files ?? resumeState?.baselineAgentLabFiles ?? [],
      baselineDirtyAgentLabFiles:
        agentLabBaseline?.baseline_dirty_agent_lab_files ?? resumeState?.baselineDirtyAgentLabFiles ?? [],
      baselineUnrevertedReceipts:
        agentLabBaseline?.baseline_unreverted_receipts ?? resumeState?.baselineUnrevertedReceipts ?? [],
      baselineCleanForFreshSuite:
        agentLabBaseline?.baseline_clean_for_fresh_suite ??
        resumeState?.baselineCleanForFreshSuite ??
        null,
    };
    setReversibleSuiteState(initialSuiteState);
    storeReversibleSuiteState(initialSuiteState);
    const createdRun = isResume
      ? await patchDurableCodingRunFromSuiteWithTimeout(initialSuiteState)
      : await createDurableCodingRunForSuite(initialSuiteState);
    // #region agent log
    fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
      body: JSON.stringify({
        sessionId: "0fdea5",
        hypothesisId: "H10",
        location: "CodingCockpitShell.tsx:handleRunReversibleSuite",
        message: isResume ? "resume backend sync" : "fresh run backend sync",
        data: {
          isResume,
          suiteId,
          startIndex,
          synced: Boolean(createdRun),
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    setBackendRunSync({
      lastSyncedAt: new Date().toISOString(),
      message: createdRun ? "Active run attached" : "Backend sync failed",
      runId: createdRun?.run_id ?? suiteId,
      status: createdRun ? "attached" : "error",
    });
    let nextState: ReversibleSuiteState = initialSuiteState;
    let suiteAbort: ReversibleSuiteAbort | null = null;
    let durableRowSyncFailed = false;
    try {
      for (let index = startIndex; index < prompts.length; index += 1) {
        const prompt = prompts[index];
        if (!prompt) continue;
        // #region agent log
        fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
          body: JSON.stringify({
            sessionId: "0fdea5",
            hypothesisId: "H8",
            location: "CodingCockpitShell.tsx:handleRunReversibleSuite",
            message: "suite loop iteration start",
            data: { suiteId, index, promptId: prompt.id },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
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
        void patchDurableCodingRunFromSuite(nextState).then((run) => {
          if (!run) return;
          setBackendRunSync({
            lastSyncedAt: new Date().toISOString(),
            message: "Active run attached",
            runId: run.run_id,
            status: "attached",
          });
        });
        void postDurableCodingRunPromptStatus(nextState.suiteId, prompt, "running", nextState);
        let result: ReversibleSuitePromptResult;
        const routeReady = await waitForV1RoutesAfterHmr({
          maxAttempts: 3,
          delayMs: 350,
          signal: suiteFetchAbortRef.current?.signal,
        });
        if (!routeReady.ok && "cancelled" in routeReady && routeReady.cancelled) {
          const stoppedState = {
            ...nextState,
            currentStep: "Stopped by user",
            interruptionReason: "user_clicked_stop_suite",
            interruptionSource: "user_stop" as const,
            status: "failed" as const,
            stopped: true,
            suiteFinishedAt: performance.now(),
          };
          setReversibleSuiteState(stoppedState);
          storeReversibleSuiteState(stoppedState);
          await patchDurableCodingRunFromSuite(stoppedState);
          break;
        }
        if (!routeReady.ok && "failure" in routeReady) {
          result = buildRouteUnavailableSuitePromptResult(
            prompt,
            routeReady.failure,
            index + 1,
            selectedProviderTruth.providerLabel,
          );
          const routeAbortState = {
            ...nextState,
            completed: nextState.completed + 1,
            currentStep: "Stopped: SpiritOS /v1 API routes unavailable",
            fail: nextState.fail + 1,
            results: [...nextState.results, result],
            status: "failed" as const,
            interruptionReason: `route_unavailable: ${result.error_summary}`,
            interruptionSource: "route_failed" as const,
          };
          setReversibleSuiteState(routeAbortState);
          storeReversibleSuiteState(routeAbortState);
          await postDurableCodingRunRow(routeAbortState.suiteId, result, durableRunStatusForResult(result));
          await patchDurableCodingRunFromSuite(routeAbortState);
          break;
        }
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
              void patchDurableCodingRunFromSuite(nextState);
            });
          }
          result = await runOneReversibleTrialPrompt(
            nextState.suiteId,
            prompt,
            (step) => {
              nextState = {
                ...nextState,
                currentStep: step,
                currentStepStartedAt: performance.now(),
                currentPromptElapsedMs: elapsedMs(promptStartedAt),
              };
              setReversibleSuiteState(nextState);
              storeReversibleSuiteState(nextState);
              void patchDurableCodingRunFromSuite(nextState);
            },
            { baselineCleanForFreshSuite: nextState.baselineCleanForFreshSuite },
          );
          result = finalizeReversibleTrialResult({ ...result, elapsed_ms: elapsedMs(promptStartedAt) });
          // #region agent log
          fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
            body: JSON.stringify({
              sessionId: "0fdea5",
              hypothesisId: "H6",
              location: "CodingCockpitShell.tsx:handleRunReversibleSuite",
              message: "prompt returned",
              data: {
                promptId: prompt.id,
                index,
                label: result.visible_result_label,
              },
              timestamp: Date.now(),
            }),
          }).catch(() => {});
          // #endregion
        } catch (error) {
          const failureReason = error instanceof Error ? error.message : "Trial prompt failed.";
          if (failureReason === "user_stop") {
            const stoppedState = {
              ...nextState,
              currentStep: "Stopped by user",
              interruptionReason: "user_clicked_stop_suite",
              interruptionSource: "user_stop" as const,
              status: "failed" as const,
              stopped: true,
              suiteFinishedAt: performance.now(),
            };
            setReversibleSuiteState(stoppedState);
            storeReversibleSuiteState(stoppedState);
            await patchDurableCodingRunFromSuite(stoppedState);
            break;
          }
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
            provenance: normalizeTrialResultProvenance(undefined),
            preview_changed_files: [],
            reverse_diff: "",
            reverse_status_text: "No applied trial edits to reverse.",
            reverted: false,
            reversal_available: false,
            run_id: `${suiteId}:${prompt.id}`,
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
          currentStep: bucketedSuccess ? "Continuing to next prompt..." : "Needs fix",
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
        const rowSyncedRun = await postDurableCodingRunRowWithTimeout(
          nextState.suiteId,
          result,
          durableRunStatusForResult(result),
        );
        // #region agent log
        fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
          body: JSON.stringify({
            sessionId: "0fdea5",
            hypothesisId: "H7",
            location: "CodingCockpitShell.tsx:handleRunReversibleSuite",
            message: "row sync finished",
            data: {
              promptId: prompt.id,
              synced: Boolean(rowSyncedRun),
              completed: nextState.completed,
            },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        if (rowSyncedRun) {
          setBackendRunSync({
            lastSyncedAt: new Date().toISOString(),
            message: "Synced from backend",
            runId: rowSyncedRun.run_id,
            status: "synced",
          });
        } else {
          const syncFailedState = {
            ...nextState,
            currentStep: "Stopped: durable row sync failed",
            interruptionReason:
              "durable_row_sync_failed: prompt result could not be persisted before the sync timeout.",
            interruptionSource: "route_failed" as const,
            status: "failed" as const,
            suiteFinishedAt: performance.now(),
          };
          setReversibleSuiteState(syncFailedState);
          storeReversibleSuiteState(syncFailedState);
          setBackendRunSync({
            lastSyncedAt: new Date().toISOString(),
            message: "Backend row sync failed",
            runId: nextState.suiteId,
            status: "error",
          });
          setReversibleSuiteCopyStatus(
            "Stopped after prompt result: durable row sync timed out or failed. Resume/clear controls remain available.",
          );
          await patchDurableCodingRunFromSuiteWithTimeout(syncFailedState);
          nextState = syncFailedState;
          durableRowSyncFailed = true;
          break;
        }
        await patchDurableCodingRunFromSuiteWithTimeout(nextState);
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
          await patchDurableCodingRunFromSuite(nextState);
          break;
        }
        if (stopReversibleSuiteAfterCurrentRef.current) break;
      }
      const suiteFinishedAt = performance.now();
      const stoppedByUser = stopReversibleSuiteAfterCurrentRef.current;
      const doneState = {
        ...nextState,
        currentPrompt: nextState.completed > 0 ? "Suite finished." : "",
        currentStep: durableRowSyncFailed
          ? nextState.currentStep
          : stoppedByUser
            ? "Stopped after current prompt"
            : suiteAbort?.step ?? "Finished",
        currentStepStartedAt: null,
        interruptionReason: durableRowSyncFailed
          ? nextState.interruptionReason
          : stoppedByUser
            ? "user_clicked_stop_after_current_prompt"
            : suiteAbort?.reason ?? null,
        interruptionSource: durableRowSyncFailed
          ? nextState.interruptionSource
          : stoppedByUser
            ? "user_stop" as const
            : suiteAbort?.source ?? "none" as const,
        status: durableRowSyncFailed || nextState.fail > 0 || suiteAbort ? "failed" as const : "done" as const,
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
      const doneRun = await patchDurableCodingRunFromSuite(doneState);
      if (doneRun) {
        setBackendRunSync({
          lastSyncedAt: new Date().toISOString(),
          message: "Synced from backend",
          runId: doneRun.run_id,
          status: "synced",
        });
      }
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
        void patchDurableCodingRunFromSuite(failedState);
        return failedState;
      });
    }
    window.clearInterval(suiteRunnerLeaseInterval);
    clearReversibleSuiteRunnerLease(suiteId);
    localReversibleSuiteRunningRef.current = false;
  }

  async function handleStopReversibleSuiteAfterCurrent() {
    stopReversibleSuiteAfterCurrentRef.current = true;
    suiteFetchAbortRef.current?.abort();
    clearReversibleSuiteRunnerLease(reversibleSuiteState.suiteId);
    const runId = backendRunSync.runId || reversibleSuiteState.suiteId;
    if (!localReversibleSuiteRunningRef.current && runId) {
      const released = await releaseSyncedReversibleSuiteRun(runId, {
        localRunnerActive: false,
        source: "user_stop",
      });
      if (released) {
        const syncedState = suiteStateFromDurableRun(released);
        setReversibleSuiteState(syncedState);
        storeReversibleSuiteState(syncedState);
        setBackendRunSync({
          lastSyncedAt: new Date().toISOString(),
          message: reversibleSuiteStateCanResume(syncedState)
            ? "Paused, ready to resume"
            : "Stopped, synced",
          runId:
            released.status === "running" || released.status === "pending"
              ? released.run_id
              : "",
          status:
            released.status === "running" || released.status === "pending"
              ? "attached"
              : "synced",
        });
        return;
      }
    }
    setReversibleSuiteState((current) => {
      const stoppingState = {
        ...current,
        interruptionReason: "user_clicked_stop_after_current_prompt",
        interruptionSource: "user_stop" as const,
        status: current.status === "running" ? "stopping" as const : current.status,
        stopped: true,
      };
      storeReversibleSuiteState(stoppingState);
      void patchDurableCodingRunFromSuite({
        ...stoppingState,
        status: "failed",
      });
      return stoppingState;
    });
  }

  async function handleReverseRemainingTrialEdits(
    options: {
      agentLabFullCleanup?: boolean;
      appliedReceiptsOverride?: AppliedRunReceipt[];
      clearSuiteAfter?: boolean;
      resultsOverride?: ReversibleSuitePromptResult[];
      suiteSnapshot?: Pick<ReversibleSuiteState, "model" | "provider" | "suiteId">;
    } = {},
  ): Promise<string | undefined> {
    const activeResults = options.resultsOverride ?? reversibleSuiteState.results;
    const activeSuite = options.suiteSnapshot ?? reversibleSuiteState;
    const activeReceipts = options.appliedReceiptsOverride ?? appliedRunReceipts;
    const remainingFromSuite = options.agentLabFullCleanup
      ? allUnrevertedSuiteResultsInReversePromptOrder(activeResults)
      : latestUnrevertedSuiteResultsByTarget(activeResults);
    const remainingSuiteReceiptIds = new Set(remainingFromSuite.map((result) => suiteReceiptIdForResult(result)));
    const remainingFromReceipts = orphanUnrevertedTrialReceipts.filter((receipt) =>
      receipt.id.startsWith("trial-suite:") && !remainingSuiteReceiptIds.has(receipt.id),
    );
    const totalRemaining = remainingFromSuite.length + remainingFromReceipts.length;
    if (totalRemaining === 0 || isReverting) {
      if (totalRemaining === 0 && options.clearSuiteAfter) {
        await clearReversibleSuitePanel();
        setReversibleSuiteCopyStatus("No fixture edits were pending; cleared suite results.");
        return "No fixture edits were pending; cleared suite results.";
      }
      setReversibleSuiteCopyStatus(
        totalRemaining === 0
          ? "No trial edits are waiting for reverse."
          : "Reverse already in progress.",
      );
      return totalRemaining === 0
        ? "No trial edits are waiting for reverse."
        : "Reverse already in progress.";
    }
    setIsReverting(true);
    setReversibleSuiteCopyStatus(`Undoing ${totalRemaining} trial edit(s)...`);
    const revertedSuiteKeys = new Set<string>();
    const revertedReceiptIds = new Set<string>();
    const revertedTargets = new Set<string>();
    const failures: string[] = [];
    const allSuiteResults = activeResults;
    try {
      const suiteReceipts = remainingFromSuite.map((result) =>
        receiptForSuiteReverseResult(result, activeReceipts),
      );
      const receiptsById = new Map(
        [...activeReceipts, ...suiteReceipts].map((receipt) => [receipt.id, receipt]),
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
        if (!options.agentLabFullCleanup && revertedTargets.has(targetKey)) {
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
          await applyReverseReceiptWithAgentLabFallback(receipt, options.agentLabFullCleanup === true);
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
          if (options.agentLabFullCleanup && isAgentLabTrialPath(receipt.target)) {
            try {
              await applyAgentLabDeleteFallback(receipt);
              revertedTargets.add(targetKey);
              registerSuiteTargetReverted(
                targetKey,
                allSuiteResults,
                reconciledReceipts,
                revertedSuiteKeys,
                revertedReceiptIds,
              );
              continue;
            } catch (deleteError) {
              failures.push(
                `${receipt.target}: ${
                  deleteError instanceof Error ? deleteError.message : "Agent-lab delete fallback failed."
                }`,
              );
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
          await applyReverseReceiptWithAgentLabFallback(receipt, options.agentLabFullCleanup === true);
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
      if (options.agentLabFullCleanup) {
        for (const target of uniqueAgentLabTargetsFromResults(allSuiteResults)) {
          if (revertedTargets.has(target)) continue;
          const seedResult = allSuiteResults.find(
            (result) =>
              result.reversal_available &&
              !result.reverted &&
              [result.selected_target, ...result.applied_changed_files, ...result.disk_changed_files].some(
                (file) => normalizeRepoPath(file) === target,
              ),
          );
          const seedReceipt = seedResult
            ? receiptForSuiteReverseResult(seedResult, reconciledReceipts)
            : buildAgentLabCleanupSeedReceipt(target);
          try {
            await applyAgentLabDeleteFallback(seedReceipt);
            revertedTargets.add(target);
            registerSuiteTargetReverted(
              target,
              allSuiteResults,
              reconciledReceipts,
              revertedSuiteKeys,
              revertedReceiptIds,
            );
          } catch (error) {
            failures.push(
              `${target}: ${
                error instanceof Error ? error.message : "Agent-lab delete sweep failed."
              }`,
            );
          }
        }
      }
      const revertedAt = new Date().toISOString();
      const revertedCount = revertedReceiptIds.size;
      if (revertedCount > 0) {
        const reversedResultsForBackend = syncReversibleSuiteResultsFromReceipts(
          activeResults.map((result) =>
            revertedSuiteKeys.has(`${result.prompt.id}:${result.run_id}`)
              ? {
                  ...result,
                  reverted: true,
                  reverse_status_text: "Reversed manually through trial runner controls.",
                }
              : result,
          ),
          reconciledReceipts,
        );
        const reversedSuiteStateForBackend: ReversibleSuiteState = {
          ...reversibleSuiteState,
          reverted: reversedResultsForBackend.filter((result) => result.reversal_available && result.reverted).length,
          results: reversedResultsForBackend,
          suiteId: activeSuite.suiteId || reversibleSuiteState.suiteId,
        };
        if (reversedSuiteStateForBackend.suiteId) {
          for (const result of reversedResultsForBackend) {
            if (revertedSuiteKeys.has(`${result.prompt.id}:${result.run_id}`)) {
              await postDurableCodingRunRow(reversedSuiteStateForBackend.suiteId, result, "reverted");
            }
          }
          const run = await patchDurableCodingRunFromSuite(reversedSuiteStateForBackend);
          if (run) {
            setBackendRunSync({
              lastSyncedAt: new Date().toISOString(),
              message: "Reversal synced from backend",
              runId: run.run_id,
              status: "synced",
            });
          }
        }
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
        setReversibleSuiteState((current) => {
          if (current.status === "idle" && current.results.length === 0 && !current.suiteId) {
            return current;
          }
          const results =
            current.suiteId === reversedSuiteStateForBackend.suiteId
              ? reversedSuiteStateForBackend.results
              : syncReversibleSuiteResultsFromReceipts(
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
          );
          const updatedState = {
            ...current,
            reverted: results.filter(
              (result) =>
                result.reversal_available &&
                (result.reverted || revertedSuiteKeys.has(`${result.prompt.id}:${result.run_id}`)),
            ).length,
            results,
          };
          if (!options.clearSuiteAfter && !options.agentLabFullCleanup) {
            storeReversibleSuiteState(updatedState);
          }
          return updatedState;
        });
      }
      const revertedTargetCount = revertedTargets.size;
      const summary =
        failures.length > 0
          ? `Reversed ${revertedTargetCount} fixture file(s). ${failures.length} item(s) still need attention: ${failures[0]}`
          : revertedTargetCount > 0
            ? revertedCount > revertedTargetCount
              ? `Reversed ${revertedTargetCount} fixture file(s) (${revertedCount} catalog receipt(s) cleared).`
              : `Reversed ${revertedTargetCount} fixture file(s).`
            : "No trial edits were reversed. Check diagnostics for blocker details.";
      if (options.agentLabFullCleanup) {
        updateAppliedRunReceipts((receipts) =>
          receipts.filter((receipt) => !receipt.id.startsWith("trial-suite:")),
        );
      }
      if (options.clearSuiteAfter && failures.length === 0) {
        await clearReversibleSuitePanel();
        const clearedMessage =
          revertedTargetCount > 0
            ? `Reversed ${revertedTargetCount} fixture file(s) and cleared suite results.`
            : "No fixture edits were pending; cleared suite results.";
        setReversibleSuiteCopyStatus(clearedMessage);
        return clearedMessage;
      }
      setReversibleSuiteCopyStatus(summary);
      return summary;
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
            allowed_files: packet.allowedFiles,
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
      const proposalPlan2SubsystemIntegrations = plan2SubsystemIntegrationsFromPayload(proposalPayload);
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
          plan2SubsystemIntegrations: proposalPlan2SubsystemIntegrations,
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
          const applyFailureTrace = causalTraceFromPayload(applyPayload);
          const applyFailureMessage = messageFromPayload(applyPayload, applyResponse.status);
          const applyFailureReasonCode =
            reasonCodeFromPreview(applyPayload) ?? reasonCodeFromErrorMessage(applyFailureMessage);
          setPreviewState({
            approvalAvailable: false,
            approvedAt: null,
            appliedAt: null,
            applySummary: applyFailureMessage,
            allowedFiles: packet.allowedFiles,
            blocker: applyFailureMessage,
            changedFiles,
            checks: packet.checks,
            causalStatusAfter: applyFailureTrace.causalStatusAfter,
            currentPhase: manualTaskPhaseLabels.failed,
            diff: proposedDiff,
            error: applyFailureMessage,
            events: [
              ...previewReadyEvents.slice(0, -1),
              manualEvent("failed", "failed", applyFailureMessage),
            ],
            forbiddenFiles: packet.forbiddenFiles,
            isApplying: false,
            isLoading: false,
            invocationEventId: applyFailureTrace.invocationEventId,
            ...providerTruthPatch(proposalProviderTruth),
            outputHash: outputHashFromPayload(applyPayload),
            plan2SubsystemIntegrations:
              plan2SubsystemIntegrationsFromPayload(applyPayload).length > 0
                ? plan2SubsystemIntegrationsFromPayload(applyPayload)
                : proposalPlan2SubsystemIntegrations,
            previewStatus: "execute-approved failed closed",
            requirementSummary: gate.requirementSummary,
            reasonCode: applyFailureReasonCode,
            reviewerSummary: gate.reviewerSummary,
            routeCalled: "/v1/actions/execute-approved",
            selectedTarget: packet.selectedTarget,
            status: "error",
            targetCandidates: packet.targetCandidates,
            targetMatch: gate.targetMatch,
            taskId,
            taskSpecAllowed: gate.taskSpecAllowed,
            traceId: applyFailureTrace.traceId,
            consumerEventId: applyFailureTrace.consumerEventId,
            consumerSubsystem: applyFailureTrace.consumerSubsystem,
            verifierSummary: gate.verifierSummary,
            technicalDetail: safePayloadSummary(applyPayload),
          });
          return;
        }
        const appliedFiles = changedFilesFromApplyPayloadOrDiff(applyPayload, proposedDiff);
        const causalTrace = causalTraceFromPayload(applyPayload);
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
          causalStatusAfter: causalTrace.causalStatusAfter,
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
          plan2SubsystemIntegrations:
            plan2SubsystemIntegrationsFromPayload(applyPayload).length > 0
              ? plan2SubsystemIntegrationsFromPayload(applyPayload)
              : proposalPlan2SubsystemIntegrations,
          outputHash: outputHashFromPayload(applyPayload),
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
          traceId: causalTrace.traceId,
          invocationEventId: causalTrace.invocationEventId,
          consumerEventId: causalTrace.consumerEventId,
          consumerSubsystem: causalTrace.consumerSubsystem,
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
        plan2SubsystemIntegrations:
          plan2SubsystemIntegrationsFromPayload(diffPayload).length > 0
            ? plan2SubsystemIntegrationsFromPayload(diffPayload)
            : proposalPlan2SubsystemIntegrations,
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
      currentPhase: manualTaskPhaseLabels.blocked,
      events: [
        ...current.events,
        manualEvent("blocked", "blocked", "Human reviewer rejected the preview. No apply route was called."),
      ],
      reasonCode: "human_rejected_preview",
      status: "blocked",
      technicalDetail: "operator_control=reject; route=browser_operator_reject; apply_called=false",
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
      events: [
        ...current.events,
        manualEvent("review", "done", "Human approval recorded. Apply is still a separate action."),
      ],
      status: "approved",
      technicalDetail: "operator_control=approve; route=browser_operator_approval; apply_called=false",
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
        const applyFailureTrace = causalTraceFromPayload(applyPayload);
        const applyFailureMessage = messageFromPayload(applyPayload, applyResponse.status);
        const applyFailureReasonCode =
          reasonCodeFromPreview(applyPayload) ?? reasonCodeFromErrorMessage(applyFailureMessage);
        setPreviewState((current) => ({
          ...current,
          applySummary: applyFailureMessage,
          causalStatusAfter: applyFailureTrace.causalStatusAfter,
          consumerEventId: applyFailureTrace.consumerEventId,
          consumerSubsystem: applyFailureTrace.consumerSubsystem,
          currentPhase: manualTaskPhaseLabels.failed,
          error: applyFailureMessage,
          events: [
            ...current.events,
            manualEvent("failed", "failed", applyFailureMessage),
          ],
          invocationEventId: applyFailureTrace.invocationEventId,
          isApplying: false,
          outputHash: outputHashFromPayload(applyPayload),
          plan2SubsystemIntegrations:
            plan2SubsystemIntegrationsFromPayload(applyPayload).length > 0
              ? plan2SubsystemIntegrationsFromPayload(applyPayload)
              : current.plan2SubsystemIntegrations,
          reasonCode: applyFailureReasonCode,
          routeCalled: "/v1/actions/execute-approved",
          status: "error",
          taskId,
          technicalDetail: safePayloadSummary(applyPayload),
          traceId: applyFailureTrace.traceId,
        }));
        return;
      }
      const appliedFiles = changedFilesFromApplyPayloadOrDiff(applyPayload, previewState.diff);
      const causalTrace = causalTraceFromPayload(applyPayload);
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
        causalStatusAfter: causalTrace.causalStatusAfter,
        changedFiles: changedFiles.length > 0 ? changedFiles : current.changedFiles,
        error: null,
        isApplying: false,
        reasonCode: null,
        status: "applied",
        taskId,
        plan2SubsystemIntegrations:
          plan2SubsystemIntegrationsFromPayload(applyPayload).length > 0
            ? plan2SubsystemIntegrationsFromPayload(applyPayload)
            : current.plan2SubsystemIntegrations,
        outputHash: outputHashFromPayload(applyPayload),
        traceId: causalTrace.traceId,
        invocationEventId: causalTrace.invocationEventId,
        consumerEventId: causalTrace.consumerEventId,
        consumerSubsystem: causalTrace.consumerSubsystem,
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
    if (receipt.backupManifest) {
      const undoResponse = await fetchWithTimeout(
        `/v1/tasks/long-running/${encodeURIComponent(receipt.taskId)}/undo`,
        {
          body: JSON.stringify({
            confirm_undo: true,
            expected_backup_manifest: receipt.backupManifest,
            requested_by: "coding-ui",
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
        TRIAL_POST_MODEL_STAGE_TIMEOUT_MS,
      );
      const undoPayload = await readJson(undoResponse);
      if (!undoResponse.ok) {
        throw new Error(messageFromPayload(undoPayload, undoResponse.status));
      }
      const undo = asRecord(asRecord(undoPayload).undo);
      if (undo.filesystem_verified !== true || undo.untouched_scope_assertion !== true) {
        throw new Error("Undo returned without filesystem and untouched-scope verification.");
      }
      if (stringValue(undo.expected_browser_state) === "fixture_missing") {
        const previewResponse = await fetchWithTimeout(
          `/v1/coding/dummy-product-site-preview/index.html?t=${Date.now()}`,
          { cache: "no-store" },
          TRIAL_POST_MODEL_STAGE_TIMEOUT_MS,
        );
        if (previewResponse.status !== 404) {
          throw new Error(
            `Undo filesystem receipt expected a missing fixture, but browser preview returned HTTP ${previewResponse.status}.`,
          );
        }
        const baseline = await refreshAgentLabBaseline();
        if (!baseline?.baseline_clean_for_fresh_suite) {
          throw new Error("Undo receipt passed, but the baseline API did not confirm a clean fixture.");
        }
      }
      updateAppliedRunReceipts((receipts) =>
        receipts.map((item) =>
          item.id === receipt.id
            ? {
                ...item,
                finalTruthStatus: "UNDO_VERIFIED",
                undoReceiptId: stringValue(undo.undo_receipt_id),
                undoReceiptPath: stringValue(undo.receipt_path),
              }
            : item,
        ),
      );
      const restoredCount = Array.isArray(undo.files_restored) ? undo.files_restored.length : 0;
      return `Manifest-backed Undo verified ${restoredCount || "all"} approved file(s).`;
    }
    const reverseDiff = executeReadyReverseDiff(reverseDiffForReceipt(receipt));
    const changedFiles = changedFilesFromDiffPreview(reverseDiff);
    const allowedFiles = [
      ...new Set([
        ...changedFiles.map((path) => normalizeRepoPath(path)).filter(Boolean),
        normalizeRepoPath(receipt.target),
        ...receipt.allowedFiles.map((path) => normalizeRepoPath(path)).filter(Boolean),
        ...(isAgentLabTrialPath(receipt.target)
          ? [
              "src/app/agent-lab/**",
              "src/components/agent-lab/**",
              "src/lib/agent-lab/**",
              "src/app/api/agent-lab/**",
              "tests/agent-lab/**",
            ]
          : []),
      ]),
    ];
    const outsideAllowed = changedFiles.filter((path) => !pathIsAllowedForTrialReverse(path, allowedFiles));
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
    const taskResponse = await fetchWithTimeout("/v1/tasks/long-running", {
      body: JSON.stringify({
        description: buildReverseTaskDescription(receipt, changedFiles, allowedFiles),
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
    const taskPayload = await readJson(taskResponse);
    if (!taskResponse.ok) {
      throw new Error(messageFromPayload(taskPayload, taskResponse.status));
    }
    const taskId = taskIdFromPayload(taskPayload);
    if (!taskId) {
      throw new Error("Reverse task create did not return a task id.");
    }
    const revertAction = revertActionForReceipt(receipt);
    const reverseResponse = await fetchWithTimeout("/v1/actions/execute-approved", {
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
    }, TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
    const reversePayload = await readJson(reverseResponse);
    if (!reverseResponse.ok) {
      throw new Error(messageFromPayload(reversePayload, reverseResponse.status));
    }
    return messageFromPayload(reversePayload, reverseResponse.status);
  }

  async function readTrialWorkspaceFileStatus(
    path: string,
  ): Promise<{ status: "ok" | "missing" | "error"; content?: string; error?: string }> {
    try {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), TRIAL_POST_MODEL_STAGE_TIMEOUT_MS);
      const response = await fetch("/v1/coding/workspace-read", {
        body: JSON.stringify({ path }),
        headers: { "content-type": "application/json" },
        method: "POST",
        signal: controller.signal,
      });
      window.clearTimeout(timeout);
      if (response.status === 404) {
        return { status: "missing" };
      }
      if (!response.ok) {
        const payload = (await response.json().catch(() => ({}))) as { error?: string };
        const errorText = payload.error ?? `workspace read HTTP ${response.status}`;
        if (response.status === 400 && /not found|no such file|missing|does not exist|unknown path/i.test(errorText)) {
          return { status: "missing" };
        }
        if (/not found|no such file|missing|does not exist/i.test(errorText)) {
          return { status: "missing" };
        }
        return { status: "error", error: errorText };
      }
      const payload = (await response.json()) as { content?: string; excerpt?: string };
      return { content: payload.excerpt ?? payload.content ?? "", status: "ok" };
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return { error: "workspace read timed out", status: "error" };
      }
      return {
        error: error instanceof Error ? error.message : "workspace read failed",
        status: "error",
      };
    }
  }

  async function readTrialWorkspaceFile(path: string): Promise<string | null> {
    const status = await readTrialWorkspaceFileStatus(path);
    if (status.status === "ok") return status.content ?? "";
    if (status.status === "missing") return null;
    throw new Error(status.error ?? "workspace read failed");
  }

  async function applyAgentLabDeleteFallback(receipt: AppliedRunReceipt) {
    const before = await readTrialWorkspaceFileStatus(receipt.target);
    if (before.status === "missing") {
      return "Agent-lab file already absent on disk.";
    }
    if (before.status === "error") {
      throw new Error(before.error ?? "Could not read agent-lab file before delete.");
    }
    const deleteReceipt: AppliedRunReceipt = {
      ...receipt,
      reverseDiff: buildDeleteFileReverseDiff(receipt.target, before.content ?? ""),
    };
    await applyReverseReceipt(deleteReceipt);
    const after = await readTrialWorkspaceFileStatus(receipt.target);
    if (after.status === "ok") {
      // #region agent log
      fetch("http://localhost:7784/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "0fdea5" },
        body: JSON.stringify({
          sessionId: "0fdea5",
          hypothesisId: "H3",
          location: "CodingCockpitShell.tsx:applyAgentLabDeleteFallback",
          message: "delete ack but file still present",
          data: { target: receipt.target },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      throw new Error(`Delete did not remove ${receipt.target} from the workspace.`);
    }
    if (after.status === "error") {
      throw new Error(after.error ?? `Could not verify delete for ${receipt.target}.`);
    }
    return `Deleted ${receipt.target}.`;
  }

  async function applyReverseReceiptWithAgentLabFallback(
    receipt: AppliedRunReceipt,
    agentLabFullCleanup: boolean,
  ) {
    try {
      return await applyReverseReceipt(receipt);
    } catch (error) {
      if (!agentLabFullCleanup || !isAgentLabTrialPath(receipt.target)) {
        throw error;
      }
      const message = error instanceof Error ? error.message : String(error);
      if (reversalLooksAlreadyApplied(message)) {
        return message;
      }
      return applyAgentLabDeleteFallback(receipt);
    }
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
      await handleReverseRemainingTrialEdits({ clearSuiteAfter: options.clearSuiteAfter });
      if (availableTrialResetReceipts.length === 0 && !options.clearSuiteAfter) {
        return;
      }
      if (options.clearSuiteAfter) {
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
        await clearReversibleSuitePanel();
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
      events: [
        ...current.events,
        manualEvent("blocked", "blocked", "Operator cancelled in-flight browser work. No apply success was recorded."),
      ],
      isApplying: false,
      isLoading: false,
      reasonCode: "cancelled",
      status: "blocked",
      technicalDetail: "operator_control=cancel; route=browser_operator_cancel; apply_success=false",
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
  const activeRunDisplay = buildActiveRunDisplay({
    draftReady,
    previewState,
    selectedPrompt: selectedDummyCoderPrompt,
    selectedProviderTruth,
    selectedRunnerState: dummyCoderRunState,
  });
  const activeRunPreview = { detail: activeRunDisplay.detail, title: activeRunDisplay.title };
  const activeRunChangedFilesDiagnostics = buildChangedFilesDiagnostics({
    appliedAt: activeRunDisplay.previewState.appliedAt,
    diff: activeRunDisplay.previewState.diff,
    status: activeRunDisplay.previewState.status,
    verificationChangedFiles: activeRunDisplay.previewState.changedFiles,
  });
  const activeRunProviderTruth = providerTruthForPreviewState(activeRunDisplay.previewState, selectedProviderTruth);
  const selectedPromptDiagnosticsForDom = dummyCoder10DiagnosticsText(
    dummyCoderRunState,
    existingDummyProjectSummary,
  );
  const codingPipelineSteps = buildCodingPipelineSteps({
    applyPreflightNeedsFix: activeRunDisplay.source === "composer" ? applyPreflightNeedsFix : false,
    currentChangedFilesDiagnostics: activeRunChangedFilesDiagnostics,
    previewState: activeRunDisplay.previewState,
  });
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
  const plan42BrainStageTimelineItems = [
    {
      label: "Stage 4",
      meta: "Canonical coding route",
      status: previewState.status === "idle" ? "waiting for task" : currentTaskState,
    },
    {
      label: "Trace",
      meta: previewState.traceId ? `trace ${previewState.traceId}` : "no trace yet",
      status: previewState.consumerEventId ? "consumed event recorded" : "waiting for consumed event",
    },
    {
      label: "Decision",
      meta: previewState.routeCalled ?? "no route yet",
      status: previewState.reasonCode ?? previewState.previewStatus,
    },
  ];
  const plan42TaskLedgerItems = [
    ["task_id", previewState.taskId || "none"],
    ["task_state", currentTaskState],
    ["target", currentTaskTarget],
    ["route", previewState.routeCalled ?? "none"],
    ["consumer", previewState.consumerSubsystem ?? "none"],
  ];
  const plan42OutputContractItems = [
    ["task_id", previewState.taskId || "none"],
    ["trace_id", previewState.traceId ?? "none"],
    ["invocation_event_id", previewState.invocationEventId ?? "none"],
    ["consumer_event_id", previewState.consumerEventId ?? "none"],
    ["consumer_subsystem", previewState.consumerSubsystem ?? "none"],
    ["output_hash", previewState.outputHash ?? "none"],
    ["status", previewState.causalStatusAfter ?? previewState.previewStatus],
  ];
  const plan42ProgressLedgerItems = simpleProgressItems.map((item) => [
    item.label,
    item.status,
  ]);
  const plan42SpecialistWorkerItems = [
    ["provider", activeProviderTruth.providerLabel],
    ["model", activeProviderTruth.modelLabel],
    ["model_source", activeProviderTruth.source],
    ["provider_call_made", String(activeProviderTruth.providerCallMade)],
    [
      "trial_worker",
      reversibleSuiteState.status === "idle"
        ? "idle"
        : `${reversibleSuiteState.status}: ${reversibleSuiteState.currentStep}`,
    ],
  ];
  const plan43CancelOrStopAvailable =
    previewState.isLoading ||
    previewState.isApplying ||
    isReverting ||
    reversibleSuiteState.status === "running" ||
    reversibleSuiteState.status === "stopping";
  const plan43LastControlRoute =
    previewState.reasonCode === "cancelled"
      ? "browser_operator_cancel"
      : previewState.reasonCode === "human_rejected_preview"
        ? "browser_operator_reject"
        : previewState.status === "approved"
          ? "browser_operator_approval"
          : previewState.status === "applied"
            ? "/v1/actions/execute-approved"
            : reversibleSuiteState.status === "stopping"
              ? "/v1/coding/runs/[runId]"
              : "none";
  const plan43LastControlStatus =
    previewState.reasonCode === "cancelled"
      ? "cancelled_no_apply_success"
      : previewState.reasonCode === "human_rejected_preview"
        ? "rejected_no_apply"
        : previewState.status === "approved"
          ? "approved_not_applied"
          : previewState.status === "applied"
            ? "applied_needs_verification"
            : reversibleSuiteState.status === "stopping"
              ? "suite_stop_requested"
              : "waiting_for_operator_action";
  const plan43ControlLedgerItems = [
    [
      "edit",
      task.trim()
        ? "draft_present; editing resets preview before apply"
        : "waiting_for_draft",
    ],
    [
      "approve",
      previewState.status === "approved"
        ? "approved_not_applied"
        : approvalControlsAvailable
          ? "available_after_review_gates"
          : "locked",
    ],
    [
      "reject",
      previewState.reasonCode === "human_rejected_preview"
        ? "rejected_no_apply"
        : approvalControlsAvailable || applyControlsVisible
          ? "available_no_apply"
          : "locked",
    ],
    [
      "apply",
      previewState.isApplying
        ? "execute_approved_in_flight"
        : previewState.status === "applied"
          ? "applied_needs_verification"
          : applyControlsVisible
            ? "available_execute_approved_route"
            : "locked",
    ],
    [
      "cancel",
      previewState.reasonCode === "cancelled"
        ? "cancelled_no_apply_success"
        : plan43CancelOrStopAvailable
          ? "available_for_in_flight_work"
          : "locked",
    ],
    [
      "resume",
      reversibleSuiteCanResume
        ? reversibleSuiteResumeBlocked
          ? "blocked_by_agent_lab_leftovers"
          : `available_from_prompt_${reversibleSuiteState.completed + 1}`
        : "locked",
    ],
    [
      "stop_or_kill",
      reversibleSuiteState.status === "stopping"
        ? "suite_stop_requested"
        : reversibleSuiteState.status === "running"
          ? "available_as_reviewable_stop"
          : "no_process_kill_exposed",
    ],
  ];
  const plan43ControlAuthorityItems = [
    ["apply_without_approval", "false"],
    ["commit", "false"],
    ["push", "false"],
    ["os_process_kill", "false"],
    ["route_backed_apply", previewState.status === "approved" || previewState.isApplying || previewState.status === "applied" ? "/v1/actions/execute-approved" : "locked"],
    ["route_backed_suite_stop", backendRunSync.runId ? "/v1/coding/runs/[runId]" : "browser_or_local_state_only"],
  ];
  const plan43ControlContractItems = [
    ["backend_run_id", backendRunSync.runId || reversibleSuiteState.suiteId || "none"],
    ["task_id", previewState.taskId || "none"],
    ["trace_id", previewState.traceId ?? "none"],
    ["invocation_event_id", previewState.invocationEventId ?? "none"],
    ["output_hash", previewState.outputHash ?? "none"],
    ["control_status", plan43LastControlStatus],
    ["control_route", plan43LastControlRoute],
    [
      "resume_from_prompt",
      reversibleSuiteCanResume
        ? String(reversibleSuiteState.completed + 1)
        : "locked",
    ],
    ["backend_sync_status", backendRunSync.status],
    ["interruption_source", reversibleSuiteState.interruptionSource],
  ];
  const plan44MemoryResearchItems = [
    ["prompt_memory", promptHistory.length > 0 ? `${promptHistory.length} retained` : "empty"],
    ["latest_prompt", promptHistory.at(-1) ?? (task.trim() || "none")],
    ["research_route", previewState.routeCalled ?? "waiting_for_prompt_packet"],
    ["target_candidates", formatList(previewState.targetCandidates, "none")],
    ["provider_research", `${activeProviderTruth.providerLabel}/${activeProviderTruth.modelLabel}`],
  ];
  const plan44AssignmentVerifierItems = [
    ["assignment_target", currentTaskTarget],
    ["allowed_files", formatList(previewState.allowedFiles, "none")],
    ["changed_files", formatList(currentChangedFilesDiagnostics.changedFiles, "none")],
    ["verifier_summary", previewState.verifierSummary],
    ["verifier_evidence", previewState.checks.length > 0 ? `checks_recorded=${formatList(previewState.checks, "none")}` : "none"],
    ["checks", formatList(previewState.checks, "none")],
  ];
  const plan44RepairProductiveTruthItems = [
    ["repair_status", reversalStatus || "no repair/reversal recorded"],
    ["next_safe_action", nextSafeAction],
    ["reason_code", previewState.reasonCode ?? "none"],
    ["technical_detail", previewState.technicalDetail ?? previewState.error ?? "none"],
    ["visible_result", codingVisibleResult.primary_label],
    ["productive_truth", codingVisibleResult.live_model_proof_status],
    ["apply_success_claim", previewState.status === "applied" ? "visible_applied_state" : "not_displayed"],
  ];
  const plan45CanonicalRouteItems = activeCodingApiRouteSequence.map((route, index) => [
    `${index + 1}_${route.id}`,
    `${route.route} -> ${route.sourceProxyRoute ?? "local state"}; ${route.operatorSurface}`,
  ]);
  const plan45SupportingRouteItems = codingApiRoutesByStatus("supporting").map((route) => [
    route.id,
    `${route.route}; ${route.operatorSurface}`,
  ]);
  const plan45DormantRouteItems = codingApiRoutesByStatus("dormant").map((route) => [
    route.id,
    `${route.route}; ${route.dormantReason ?? "dormant"}`,
  ]);
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
  const phoneBackgroundState =
    reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"
      ? "Running, backend synced"
      : reversibleSuiteCanResume
        ? "Paused, ready to resume"
        : reversibleSuiteState.status === "done"
          ? "Finished, synced"
          : reversibleSuiteState.status === "failed"
            ? "Stopped, synced"
            : reversibleSuiteState.results.length > 0
              ? "Last suite synced"
              : "Ready";
  const phoneBackgroundDetail =
    reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"
      ? "Backend run state is the source of truth. Other devices attach automatically while /coding stays open."
      : reversibleSuiteCanResume
        ? `Resume from prompt ${reversibleSuiteState.completed + 1} of ${reversibleSuiteState.count}; completed rows were preserved by backend sync.`
        : reversibleSuiteState.results.length > 0
          ? "Completed suite details rehydrate from backend state across refresh."
          : "Start a reversible suite from the left rail, then use this panel as the quick sync check.";
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
      className={`mt-3 inline-flex min-h-10 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
      disabled={reversibleSuiteResumeBlocked}
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
    <div
      className="dashboard-demo-v4-route-shell dashboard-demo-v4-root"
      data-coding-shell-id="coding-cockpit-shell"
      data-coding-shell-mode={embedded ? "embedded" : "full"}
    >
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
            <section className={`${commandInsetClass} p-3`} aria-label="Trial Runner">
              <p className={commandLabelClass}>Runner tools</p>
              <h3 className={`mt-2 text-base font-semibold ${commandTextClass}`}>Runner Tools</h3>
              <p className={`mt-1 text-xs leading-5 ${commandMutedClass}`}>
                Run one dummy Coder prompt or a later benchmark. Coder 001 creates LumaCart first.
              </p>
              {reversibleSuiteState.results.length > 0 ? (
                <p className={`mt-1 text-xs leading-5 ${commandMutedClass}`}>
                  Last suite syncs from backend after refresh or when another device opens /coding.
                </p>
              ) : null}
              <div className="mt-3 rounded-md border border-[var(--ddv4-surface-border-soft)] p-2 text-xs">
                <p className={`font-semibold ${commandTextClass}`}>{backendRunSync.message}</p>
                <p className={`mt-1 break-all ${commandMutedClass}`}>
                  Run ID: {backendRunSync.runId || "none"}
                </p>
                <p className={`mt-1 ${commandMutedClass}`}>
                  Last synced: {backendRunSync.lastSyncedAt ?? "not yet"}
                </p>
              </div>
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
                    disabled={reversibleSuiteRunBlocked}
                    onChange={(event) => setReversibleTrialCount(Number(event.target.value) as ReversibleTrialCount)}
                    value={reversibleTrialCount}
                  >
                    {reversibleTrialCounts.map((count) => (
                      <option key={count} value={count}>{reversibleTrialCountLabel(reversibleTrialCategory, count)}</option>
                    ))}
                  </select>
                  {reversibleSuiteCountMismatch ? (
                    <span className={`text-xs leading-5 ${commandMutedClass}`}>
                      Results are from a ×{reversibleSuiteState.count} run. Count only changes the next run — use cleanup to reset the panel.
                    </span>
                  ) : null}
                </label>
                <label className="grid gap-1">
                  <span className={commandLabelClass}>Mode</span>
                  <select
                    aria-label="Trial runner mode"
                    className={`min-h-10 rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-3 text-sm font-semibold ${commandTextClass} ${commandControlClass}`}
                    disabled={reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping" || dummyCoderRunState.status === "running" || dummyCoderRunState.status === "starting" || dummyCoderRunState.status === "request_sent"}
                    onChange={(event) => setTrialRunnerMode(event.target.value as TrialRunnerMode)}
                    value={trialRunnerMode}
                  >
                    <option value="individual">Individual prompt</option>
                    <option value="benchmark">Benchmark count</option>
                  </select>
                </label>
              </div>
              {reversiblePromptsCopyStatus || reversibleSuiteCopyStatus ? (
                <p
                  className={`mt-2 text-xs ${
                    reversibleSuiteCopyStatus.toLowerCase().includes("clean") ||
                    reversibleSuiteCopyStatus.toLowerCase().includes("removed")
                      ? "font-semibold text-emerald-300"
                      : reversibleSuiteCopyStatus.toLowerCase().includes("still dirty") ||
                          reversibleSuiteCopyStatus.toLowerCase().includes("failed") ||
                          reversibleSuiteCopyStatus.toLowerCase().includes("blocked")
                        ? "font-semibold text-rose-200"
                        : commandMutedClass
                  }`}
                >
                  {reversiblePromptsCopyStatus || reversibleSuiteCopyStatus}
                </p>
              ) : null}
              <section aria-label="Operator approval session" className="mt-3 rounded-md border border-[var(--ddv4-surface-border-soft)] p-3 text-xs">
                    <div className="flex items-center justify-between gap-2">
                      <p className={`font-semibold ${commandTextClass}`}>Operator approval session</p>
                      <span data-testid="operator-session-status" className="rounded-md border border-[var(--ddv4-pill-border)] px-2 py-0.5 font-semibold uppercase">{operatorSession.status}</span>
                    </div>
                    <p className={`mt-1 ${commandMutedClass}`}>{operatorSession.message}</p>
                    {operatorSession.expiresAt ? <p className={`mt-1 ${commandMutedClass}`}>Expires: {operatorSession.expiresAt}</p> : null}
                    {operatorSession.status === "authenticated" ? (
                      <button className={`mt-2 min-h-9 rounded-md border border-[var(--ddv4-pill-border)] px-3 font-semibold ${commandFocusClass}`} onClick={() => void revokeOperator()} type="button">Log out and revoke</button>
                    ) : (
                      <div className="mt-2 flex flex-wrap gap-2">
                        <input aria-label="Operator credential" autoComplete="off" className={`min-h-9 flex-1 rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-2 ${commandControlClass}`} onChange={(event) => setOperatorCredential(event.target.value)} type="password" value={operatorCredential} />
                        <button className={`min-h-9 rounded-md bg-emerald-300 px-3 font-semibold text-slate-950 ${commandFocusClass}`} disabled={operatorSession.status === "authenticating"} onClick={() => void authenticateOperator()} type="button">Authenticate operator</button>
                      </div>
                    )}
                    <p className={`mt-2 ${commandMutedClass}`}>Approval summary is resolved by the server from the persisted preview; this shell submits only preview ID, generation, action, task ID, and CSRF.</p>
              </section>
              {trialRunnerMode === "individual" ? (
                <div className="mt-3 space-y-3">
                  <label className="grid gap-1">
                    <span className={commandLabelClass}>Selected prompt</span>
                    <select
                      aria-label="Dummy Coder prompt"
                      className={`min-h-10 rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-3 text-sm font-semibold ${commandTextClass} ${commandControlClass}`}
                      data-testid="dummy-coder-prompt-select"
                      disabled={dummyCoderRunState.status === "running" || dummyCoderRunState.status === "starting" || dummyCoderRunState.status === "request_sent"}
                      onChange={(event) => {
                        setSelectedDummyCoderPromptId(event.target.value);
                        setDummyCoderRunCopyStatus("");
                      }}
                      value={selectedDummyCoderPrompt.id}
                    >
                      {codingTargetPlugin.prompts.map((prompt) => (
                        <option key={prompt.id} value={prompt.id}>
                          Coder {String(prompt.number).padStart(3, "0")} - {prompt.title}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="flex flex-wrap gap-2 text-[11px] font-semibold">
                    <span className="rounded-md border border-[var(--ddv4-pill-border)] px-2 py-1 text-[var(--ddv4-fg)]">
                      {selectedDummyCoderPrompt.expectedResultState}
                    </span>
                    <span className="rounded-md border border-[var(--ddv4-pill-border)] px-2 py-1 text-[var(--ddv4-fg)]">
                      dummy-product-site
                    </span>
                  </div>
                  <details className="rounded-md border border-[var(--ddv4-surface-border-soft)] p-2 text-xs">
                    <summary className={`cursor-pointer font-semibold ${commandTextClass}`}>View prompt + boundaries</summary>
                    <div className={`mt-2 space-y-2 ${commandTextClass}`}>
                      <p className="whitespace-pre-wrap leading-5">{selectedDummyCoderPrompt.submittedPrompt}</p>
                      <dl className="grid gap-2">
                        {[
                          ["Fixture root", selectedDummyCoderPrompt.fixtureRoot],
                          ["Allowed write root", selectedDummyCoderPrompt.allowedWriteRoot],
                          ["Forbidden summary", codingTargetPlugin.formatForbiddenSummary(selectedDummyCoderPrompt)],
                          ["Primary expected targets", formatList(selectedDummyCoderPrompt.primaryExpectedTargets, "none")],
                        ].map(([label, value]) => (
                          <div key={label}>
                            <dt className={commandLabelClass}>{label}</dt>
                            <dd className="mt-1 break-words">{value}</dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  </details>
                  <button
                    className={`inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md bg-emerald-300 px-3 text-sm font-semibold text-slate-950 transition-colors hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                    data-testid="run-selected-dummy-coder-prompt"
                    disabled={
                      dummyCoderRunState.status === "running" ||
                      dummyCoderRunState.status === "starting" ||
                      dummyCoderRunState.status === "request_sent" ||
                      reversibleSuiteState.status === "running" ||
                      reversibleSuiteState.status === "stopping"
                    }
                    onClick={() => void handleRunDummyCoder10Prompt()}
                    type="button"
                  >
                    {(dummyCoderRunState.status === "running" || dummyCoderRunState.status === "starting" || dummyCoderRunState.status === "request_sent") ? (
                      <span className="h-2 w-2 animate-pulse rounded-full bg-slate-950" aria-hidden="true" />
                    ) : null}
                    Run selected prompt
                  </button>
                  <pre
                    data-error-text={dummyCoderRunState.errorText ?? "none"}
                    data-raw-backend-status={dummyCoderRunState.rawBackendStatus ?? "none"}
                    data-selected-prompt-id={dummyCoderRunState.selectedPromptId ?? selectedDummyCoderPrompt.id}
                    data-selected-prompt-status={dummyCoderRunState.status}
                    data-testid="selected-prompt-diagnostics"
                    hidden
                  >
                    {selectedPromptDiagnosticsForDom}
                  </pre>
                  {(dummyCoderRunState.status === "running" ||
                    dummyCoderRunState.status === "starting" ||
                    dummyCoderRunState.status === "request_sent") ? (
                    <button
                      className={`inline-flex min-h-10 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                      onClick={handleCancelSelectedPrompt}
                      type="button"
                    >
                      Cancel run
                    </button>
                  ) : null}
                  {reversibleSuiteRunBlocked ? (
                    <p className={`text-xs font-semibold text-amber-200`}>{reversibleSuiteRunBlockedMessage}</p>
                  ) : null}
                  <button
                    className={`inline-flex min-h-10 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                    disabled={
                      reversibleSuiteRunBlocked ||
                      dummyCoderRunState.status === "running" ||
                      dummyCoderRunState.status === "starting" ||
                      dummyCoderRunState.status === "request_sent"
                    }
                    onClick={() => {
                      if (reversibleSuiteRunBlocked) {
                        setReversibleSuiteCopyStatus(reversibleSuiteRunBlockedMessage);
                        return;
                      }
                      void handleRunReversibleSuite();
                    }}
                    type="button"
                  >
                    Run all trials
                  </button>
                  <div className="rounded-md border border-[var(--ddv4-surface-border-soft)] p-2 text-xs">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className={`font-semibold ${commandTextClass}`}>
                          {dummyCoderRunState.message || "Ready"}
                        </p>
                        <p className={`mt-1 break-all ${commandMutedClass}`}>
                          Prompt: {dummyCoderRunState.selectedPromptId ?? selectedDummyCoderPrompt.id}
                          {dummyCoderRunState.taskId ? ` | Task: ${dummyCoderRunState.taskId}` : ""}
                        </p>
                      </div>
                      <span
                        className={`shrink-0 rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] ${
                          dummyCoderRunState.status === "error" || dummyCoderRunState.grader?.label === "INVALID"
                            ? "border-rose-300/40 bg-rose-300/10 text-rose-100"
                            : dummyCoderRunState.status === "timeout"
                              ? "border-rose-300/40 bg-rose-300/10 text-rose-100"
                            : dummyCoderRunState.status === "blocked" || dummyCoderRunState.grader?.label === "NEEDS_FIX"
                              ? "border-amber-300/40 bg-amber-300/10 text-amber-100"
                              : dummyCoderRunState.status === "applied" || dummyCoderRunState.grader
                                ? "border-emerald-300/40 bg-emerald-300/10 text-emerald-100"
                                : "border-[var(--ddv4-pill-border)] text-[var(--ddv4-fg-muted)]"
                        }`}
                      >
                        {dummyCoderRunState.status === "idle"
                          ? "Ready"
                          : dummyCoderRunState.status === "starting"
                            ? "Starting selected prompt..."
                            : dummyCoderRunState.status === "request_sent"
                              ? "Request sent"
                              : dummyCoderRunState.status === "running" && dummyCoderRunState.taskId
                                ? `Running task ${dummyCoderRunState.taskId}`
                                : dummyCoderRunState.status === "blocked"
                                  ? "Needs fix"
                                  : dummyCoderRunState.status === "applied"
                                    ? "Applied / review"
                                    : dummyCoderRunState.status === "timeout"
                                      ? "Timeout"
                                    : dummyCoderRunState.status === "error"
                                      ? "Failed"
                                      : dummyCoderRunState.status === "cleared"
                                        ? "Cleared"
                                        : dummyCoderRunState.grader?.label ?? dummyCoderRunState.status}
                      </span>
                    </div>
                    {dummyCoderRunState.errorText ? (
                      <p className="mt-2 break-words text-xs font-semibold text-rose-100">{dummyCoderRunState.errorText}</p>
                    ) : null}
                  </div>
                  {hasSelectedPromptResult ? (
                    <div className="space-y-2" aria-label="Selected prompt trial preview">
                      <article className="rounded-md border border-[var(--ddv4-surface-border-soft)] p-2 text-xs">
                        <div className="flex items-start justify-between gap-2">
                          <p className={`min-w-0 font-semibold ${commandTextClass}`}>
                            Coder {String(selectedDummyCoderPrompt.number).padStart(3, "0")} - {selectedDummyCoderPrompt.title}
                          </p>
                          <span className={`shrink-0 rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] ${reversibleResultTagClass(selectedPromptTrialLabel)}`}>
                            {selectedPromptTrialLabel}
                          </span>
                        </div>
                        <p className={`mt-1 ${commandMutedClass}`}>
                          {dummyCoderRunState.taskId ? `Task ${dummyCoderRunState.taskId}` : "Task pending"} | Backend {dummyCoderRunState.rawBackendStatus ?? "not started"}
                        </p>
                        {dummyCoderRunState.status === "running" ||
                        dummyCoderRunState.status === "starting" ||
                        dummyCoderRunState.status === "request_sent" ? null : (
                          <p className={`mt-1 ${commandTextClass}`}>
                            {dummyCoderRunState.message || "Ready"}
                          </p>
                        )}
                        {dummyCoderRunState.grader ? (
                          <p className={`mt-1 ${commandMutedClass}`}>
                            Grader: {dummyCoderRunState.grader.resultState} / score {dummyCoderRunState.grader.score}
                          </p>
                        ) : null}
                        {dummyCoderRunState.changedFiles.length > 0 ? (
                          <p className={`mt-1 break-words ${commandMutedClass}`}>
                            Changed: {formatList(dummyCoderRunState.changedFiles, "none")}
                          </p>
                        ) : null}
                        {dummyCoderRunState.verificationStatus ? (
                          <p className={`mt-1 break-words ${commandMutedClass}`}>
                            Verification: {dummyCoderRunState.verificationStatus}
                          </p>
                        ) : null}
                        {dummyCoderRunState.recommendedNextAction ?? dummyCoderRunState.grader?.recommendedNextAction ? (
                          <p className="mt-1 break-words text-rose-100">
                            {dummyCoderRunState.recommendedNextAction ?? dummyCoderRunState.grader?.recommendedNextAction}
                          </p>
                        ) : null}
                        <div className="mt-2 flex flex-wrap gap-2">
                          {dummyCoderRunState.changedFiles.some((path) => isDummyProductSiteTrialPath(path)) ? (
                            <a
                              className={`inline-flex min-h-8 items-center gap-1 rounded-md border border-[var(--ddv4-pill-border)] px-2 text-[11px] font-semibold text-[var(--ddv4-fg)] hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                              href="/v1/coding/dummy-product-site-preview"
                              rel="noreferrer"
                              target="_blank"
                            >
                              <ExternalLink aria-hidden="true" size={12} />
                              Open LumaCart page
                            </a>
                          ) : null}
                          {dummyCoderRunState.changedFiles.length > 0 ? (
                            <button
                              className={`inline-flex min-h-8 items-center rounded-md border border-[var(--ddv4-pill-border)] px-2 text-[11px] font-semibold text-[var(--ddv4-fg)] hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                              onClick={() => void copyTextToClipboard(dummyCoderRunState.changedFiles.join("\n"))}
                              type="button"
                            >
                              Copy changed paths
                            </button>
                          ) : null}
                        </div>
                      </article>
                      {reversibleSuiteReversalPanel}
                    </div>
                  ) : null}
                  <button
                    className={`inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                    onClick={() => void copyDummyCoder10Diagnostics()}
                    type="button"
                  >
                    <Copy aria-hidden="true" size={16} />
                    Copy diagnostics
                  </button>
                  {dummyCoderRunCopyStatus ? (
                    <p className={`text-xs ${commandMutedClass}`}>{dummyCoderRunCopyStatus}</p>
                  ) : null}
                </div>
              ) : null}
              {trialRunnerMode === "benchmark" && reversibleSuiteRunBlocked ? (
                <p className={`mt-2 text-xs font-semibold text-amber-200`}>{reversibleSuiteRunBlockedMessage}</p>
              ) : null}
              {trialRunnerMode === "benchmark" ? (
                <button
                  className={`mt-3 inline-flex min-h-10 w-full items-center justify-center rounded-md bg-emerald-300 px-3 text-sm font-semibold text-slate-950 transition-colors hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                  disabled={reversibleSuiteRunBlocked}
                  onClick={() => {
                    if (reversibleSuiteRunBlocked) {
                      setReversibleSuiteCopyStatus(reversibleSuiteRunBlockedMessage);
                      return;
                    }
                    void handleRunReversibleSuite();
                  }}
                  type="button"
                >
                  {reversibleTrialCategory === "Coder" ? "Run messy Coder benchmark" : "Run reversible trial suite"}
                </button>
              ) : null}
              {reversibleSuiteCanResume ? (
                <button
                  className={`mt-2 inline-flex min-h-10 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] disabled:cursor-not-allowed disabled:opacity-60 ${commandFocusClass}`}
                  disabled={reversibleSuiteResumeBlocked}
                  onClick={() => void handleRunReversibleSuite(reversibleSuiteState)}
                  type="button"
                >
                  Resume interrupted suite ({reversibleSuiteState.completed}/{reversibleSuiteState.count})
                </button>
              ) : null}
              {reversibleSuiteCanResume && agentLabHasLeftovers ? (
                <p className={`mt-2 text-xs ${commandMutedClass}`}>
                  Agent Lab edits from completed prompts stay on disk; resume continues the batch.
                </p>
              ) : null}
              {reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping" ? (
                <button
                  className={`mt-2 inline-flex min-h-10 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-semibold text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                  onClick={() => void handleStopReversibleSuiteAfterCurrent()}
                  type="button"
                >
                  Stop suite now
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
                  {reversibleSuiteState.results.slice(-6).map((result, index) => {
                    const quickLinks = buildTrialPromptQuickLinks({
                      quickFindPaths: result.prompt.verifyPathHints,
                      selectedTarget: result.selected_target,
                    });
                    return (
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
                      <div className="mt-2 flex flex-wrap gap-2">
                        {quickLinks.map((link) => (
                          <Link
                            className={`inline-flex min-h-8 items-center rounded-md border border-[var(--ddv4-pill-border)] px-2 text-[11px] font-semibold text-[var(--ddv4-fg)] hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                            href={link.href}
                            key={link.href}
                            rel="noreferrer"
                            target="_blank"
                          >
                            {link.label}
                          </Link>
                        ))}
                        {result.selected_target ? (
                          <button
                            className={`inline-flex min-h-8 items-center rounded-md border border-[var(--ddv4-pill-border)] px-2 text-[11px] font-semibold text-[var(--ddv4-fg)] hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                            onClick={() => void copyTextToClipboard(result.selected_target)}
                            type="button"
                          >
                            Copy target path
                          </button>
                        ) : null}
                        {result.reversal_available && !result.reverted ? (
                          <button
                            className={`inline-flex min-h-8 items-center rounded-md border border-[var(--ddv4-pill-border)] px-2 text-[11px] font-semibold text-[var(--ddv4-fg)] hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
                            onClick={() => {
                              const receipt = appliedRunReceiptsRef.current.find(
                                (item) => item.id === suiteReceiptIdForResult(result),
                              );
                              if (receipt && !receipt.revertedAt) {
                                void handleRevertReceipt(receipt);
                              }
                            }}
                            type="button"
                          >
                            Reverse this prompt
                          </button>
                        ) : null}
                      </div>
                    </article>
                    );
                  })}
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
                disabled={!hasReversibleSuiteDiagnostics}
                onClick={() => void copyReversibleSuiteDiagnostics()}
                type="button"
              >
                <Copy aria-hidden="true" size={16} />
                Copy trial diagnostics
              </button>
              {showTrialCleanupPanel && !(trialRunnerMode === "individual" && hasSelectedPromptResult)
                ? reversibleSuiteReversalPanel
                : reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"
                  ? (
                      <p className={`mt-3 text-xs ${commandMutedClass}`}>
                        Reverse trial edits unlocks when the suite reaches Done (or after refresh marks an interrupted run as failed).
                      </p>
                    )
                  : null}
              {reversiblePromptsCopyStatus || reversibleSuiteCopyStatus ? (
                <p
                  className={`mt-2 text-xs ${
                    reversibleSuiteCopyStatus.toLowerCase().includes("clean") ||
                    reversibleSuiteCopyStatus.toLowerCase().includes("removed")
                      ? "font-semibold text-emerald-300"
                      : reversibleSuiteCopyStatus.toLowerCase().includes("still dirty") ||
                          reversibleSuiteCopyStatus.toLowerCase().includes("failed")
                        ? "font-semibold text-rose-200"
                        : commandMutedClass
                  }`}
                >
                  {reversiblePromptsCopyStatus || reversibleSuiteCopyStatus}
                </p>
              ) : null}
            </section>
          </aside>

          <section className="flex min-w-0 flex-col gap-5">
            <section className={`${commandPanelClass} p-4 sm:p-5`} aria-labelledby="active-run-preview-heading">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <p className={commandLabelClass}>Active run</p>
                  <h2 id="active-run-preview-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                    Active run preview
                  </h2>
                  <p className={`mt-2 text-sm leading-6 ${commandMutedClass}`}>{activeRunPreview.detail}</p>
                </div>
                <span className="inline-flex min-h-9 shrink-0 items-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-xs font-semibold text-[var(--ddv4-fg)]">
                  {activeRunPreview.title}
                </span>
              </div>
              <dl className="mt-4 grid gap-2 text-xs sm:grid-cols-3">
                {[
                  ["Task", activeRunDisplay.taskLabel],
                  ["Route", activeRunDisplay.routeLabel],
                  ["Trace", activeRunDisplay.traceLabel],
                ].map(([label, value]) => (
                  <div className={`${commandInsetClass} min-w-0 p-3`} key={label}>
                    <dt className={commandLabelClass}>{label}</dt>
                    <dd className={`mt-1 truncate ${commandTextClass}`} title={value}>{value}</dd>
                  </div>
                ))}
              </dl>
              <details className={`${commandInsetClass} mt-3 overflow-hidden`}>
                <summary className={`min-h-10 cursor-pointer px-3 py-2 text-sm font-semibold ${commandTextClass} ${commandControlClass}`}>
                  Runner sync
                </summary>
                <dl className="grid gap-2 border-t border-[var(--ddv4-surface-border-soft)] p-3 text-xs sm:grid-cols-3">
                  {[
                    ["Trial progress", `${reversibleSuiteState.completed}/${reversibleSuiteState.count}`],
                    ["Connection", phoneNetworkState],
                    ["Saved", reversibleSuiteState.results.length > 0 ? "Yes" : "Waiting"],
                  ].map(([label, value]) => (
                    <div className="min-w-0" key={label}>
                      <dt className={commandLabelClass}>{label}</dt>
                      <dd className={`mt-1 truncate ${commandMutedClass}`} title={value}>{value}</dd>
                    </div>
                  ))}
                </dl>
                <div className="px-3 pb-3">
                  <p className={`text-xs leading-5 ${commandMutedClass}`}>{phoneBackgroundDetail}</p>
                  {phoneResumeAction}
                </div>
              </details>
            </section>

            <section className={`${commandPanelClass} p-4 sm:p-5`} aria-labelledby="task-composer-heading">
              <div className="mb-4">
                <p className={commandLabelClass}>Prompt composer</p>
                <h2 id="task-composer-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                  Task Composer
                </h2>
              </div>
              <div
                aria-label="Composer mode"
                className="mb-4 grid gap-2 rounded-md border border-[var(--ddv4-pill-border)] bg-[var(--ddv4-surface-fill)] p-1 sm:grid-cols-2"
                role="group"
              >
                {[
                  ["coding", "Coding"],
                  ["design_studio", "Design Studio"],
                ].map(([mode, label]) => {
                  const selected = composerMode === mode;
                  return (
                    <button
                      aria-pressed={selected}
                      className={`min-h-10 rounded px-3 text-sm font-semibold transition-colors ${
                        selected
                          ? "bg-emerald-300 text-slate-950"
                          : "text-[var(--ddv4-fg-muted)] hover:bg-[var(--ddv4-pill-bg)] hover:text-[var(--ddv4-fg)]"
                      } ${commandFocusClass}`}
                      key={mode}
                      onClick={() => handleComposerModeChange(mode as ComposerMode)}
                      type="button"
                    >
                      {label}
                    </button>
                  );
                })}
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
                  disabled={
                    !canStartTask ||
                    previewState.isLoading ||
                    previewState.isApplying ||
                    designStudioComposerState.isLoading ||
                    isReverting
                  }
                  onClick={composerMode === "design_studio" ? handleDesignStudioPreview : handleDraftPreview}
                  type="button"
                >
                  <ShieldCheck aria-hidden="true" size={18} />
                  {previewState.isLoading || previewState.isApplying || designStudioComposerState.isLoading
                    ? "Working..."
                    : composerMode === "design_studio"
                      ? "Start Design Studio"
                      : "Start coding"}
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
              {composerMode === "design_studio" && designStudioComposerState.status !== "idle" ? (
                <div className={`${commandInsetClass} mt-4 p-3`} aria-live="polite">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className={`text-sm font-semibold ${commandTextClass}`}>Design Studio run</p>
                    <span className="rounded border border-[var(--ddv4-pill-border)] px-2 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg)]">
                      {designStudioComposerState.status}
                    </span>
                  </div>
                  <dl className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                    {[
                      ["request_id", designStudioComposerState.requestId ?? "none"],
                      ["trace_id", designStudioComposerState.traceId ?? "pending"],
                      ["endpoint", designStudioComposerState.endpointStatus ?? "pending"],
                      ["outcome", designStudioComposerState.outcome ?? designStudioComposerState.error ?? "pending"],
                    ].map(([label, value]) => (
                      <div className="min-w-0" key={label}>
                        <dt className={commandLabelClass}>{label}</dt>
                        <dd className={`mt-1 truncate font-mono ${commandTextClass}`} title={value}>
                          {value}
                        </dd>
                      </div>
                    ))}
                  </dl>
                  {designStudioComposerState.reason ? (
                    <p className={`mt-2 text-xs ${commandMutedClass}`}>
                      Reason: {designStudioComposerState.reason}
                    </p>
                  ) : null}
                </div>
              ) : null}
            </section>

            <section className={`${commandPanelClass} p-4 sm:p-5`} aria-labelledby="progress-heading">
              <p className={commandLabelClass}>Activity</p>
              <h2 id="progress-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                Run activity
              </h2>
              <ol className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {codingPipelineSteps.map((item) => (
                  <li className={`${commandInsetClass} min-h-16 p-3`} key={item.label}>
                    <div className={`text-sm font-semibold ${commandTextClass}`}>{item.label}</div>
                    <div className={`mt-2 inline-flex min-h-7 items-center rounded-md border px-2 text-xs font-semibold uppercase tracking-[0.12em] ${codingStepStatusClass(item.status)}`}>
                      {item.status}
                    </div>
                    <p className={`mt-2 line-clamp-2 text-xs leading-5 ${commandMutedClass}`}>{item.detail}</p>
                  </li>
                ))}
              </ol>
            </section>

            <details className={`${commandPanelClass} overflow-hidden`}>
              <summary className={`min-h-12 cursor-pointer px-4 py-3 text-sm font-semibold ${commandTextClass} ${commandControlClass}`}>
                Diagnostics
              </summary>
              <div className="space-y-4 border-t border-[var(--ddv4-surface-border-soft)] p-4 sm:p-5">
            <section className={`${commandInsetClass} p-4`} aria-labelledby="plan-42-ledger-heading">
              <p className={commandLabelClass}>Plan 4.2 ledger</p>
              <h2 id="plan-42-ledger-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                Pipeline ledger
              </h2>
              <ol className="mt-4 grid gap-2 sm:grid-cols-3">
                {plan42BrainStageTimelineItems.map((item) => (
                  <li className={`${commandInsetClass} min-h-20 p-3`} key={item.label}>
                    <div className={`text-sm font-semibold ${commandTextClass}`}>{item.label}</div>
                    <div className={`mt-1 text-xs ${commandMutedClass}`}>{item.meta}</div>
                    <div className={`mt-2 text-xs uppercase tracking-[0.12em] ${commandMutedClass}`}>
                      {item.status}
                    </div>
                  </li>
                ))}
              </ol>
              <div className="mt-4 grid gap-3 lg:grid-cols-2 xl:grid-cols-4">
                {[
                  ["Task ledger", plan42TaskLedgerItems],
                  ["Output contract", plan42OutputContractItems],
                  ["Progress ledger", plan42ProgressLedgerItems],
                  ["Provider and runner", plan42SpecialistWorkerItems],
                ].map(([title, rows]) => (
                  <div className={`${commandInsetClass} p-3`} key={String(title)}>
                    <h3 className={`text-sm font-semibold ${commandTextClass}`}>{String(title)}</h3>
                    <dl className="mt-3 grid gap-2 text-xs">
                      {(rows as string[][]).map(([label, value]) => (
                        <div className="grid grid-cols-[8.75rem_minmax(0,1fr)] gap-2" key={`${title}-${label}`}>
                          <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                            {label}
                          </dt>
                          <dd className={`break-all font-mono ${commandTextClass}`}>{value}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                ))}
              </div>
            </section>

            <section className={`${commandInsetClass} p-4`} aria-labelledby="plan-43-controls-heading">
              <p className={commandLabelClass}>Plan 4.3 controls</p>
              <h2 id="plan-43-controls-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                Reviewable operator controls
              </h2>
              <div className="mt-4 grid gap-3 lg:grid-cols-2">
                <div className={`${commandInsetClass} p-3`}>
                  <h3 className={`text-sm font-semibold ${commandTextClass}`}>Control ledger</h3>
                  <dl className="mt-3 grid gap-2 text-xs">
                    {plan43ControlLedgerItems.map(([label, value]) => (
                      <div className="grid grid-cols-[8.75rem_minmax(0,1fr)] gap-2" key={`plan43-control-${label}`}>
                        <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                          {label}
                        </dt>
                        <dd className={`break-all font-mono ${commandTextClass}`}>{value}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
                <div className={`${commandInsetClass} p-3`}>
                  <h3 className={`text-sm font-semibold ${commandTextClass}`}>Control authority</h3>
                  <dl className="mt-3 grid gap-2 text-xs">
                    {[
                      ...plan43ControlAuthorityItems,
                      ["last_control_route", plan43LastControlRoute],
                      ["last_control_status", plan43LastControlStatus],
                    ].map(([label, value]) => (
                      <div className="grid grid-cols-[8.75rem_minmax(0,1fr)] gap-2" key={`plan43-authority-${label}`}>
                        <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                          {label}
                        </dt>
                        <dd className={`break-all font-mono ${commandTextClass}`}>{value}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
                <div className={`${commandInsetClass} p-3 lg:col-span-2`}>
                  <h3 className={`text-sm font-semibold ${commandTextClass}`}>Control contract</h3>
                  <dl className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                    {plan43ControlContractItems.map(([label, value]) => (
                      <div className="grid grid-cols-[8.75rem_minmax(0,1fr)] gap-2" key={`plan43-contract-${label}`}>
                        <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                          {label}
                        </dt>
                        <dd className={`break-all font-mono ${commandTextClass}`}>{value}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>
            </section>

            <section className={`${commandInsetClass} p-4`} aria-labelledby="plan-44-truth-heading">
              <p className={commandLabelClass}>Plan 4.4 truth</p>
              <h2 id="plan-44-truth-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                Memory, research, verifier, and productive truth
              </h2>
              <div className="mt-4 grid gap-3 lg:grid-cols-3">
                {[
                  ["Memory and research", plan44MemoryResearchItems],
                  ["Assignment and verifier", plan44AssignmentVerifierItems],
                  ["Repair and productive truth", plan44RepairProductiveTruthItems],
                ].map(([title, rows]) => (
                  <div className={`${commandInsetClass} p-3`} key={String(title)}>
                    <h3 className={`text-sm font-semibold ${commandTextClass}`}>{String(title)}</h3>
                    <dl className="mt-3 grid gap-2 text-xs">
                      {(rows as string[][]).map(([label, value]) => (
                        <div className="grid grid-cols-[8.75rem_minmax(0,1fr)] gap-2" key={`plan44-${label}`}>
                          <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                            {label}
                          </dt>
                          <dd className={`break-all font-mono ${commandTextClass}`}>{value}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                ))}
              </div>
            </section>

            <section className={`${commandInsetClass} p-4`} aria-labelledby="plan-45-api-heading">
              <p className={commandLabelClass}>Plan 4.5 APIs</p>
              <h2 id="plan-45-api-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>
                Canonical and dormant route ledger
              </h2>
              <div className="mt-4 grid gap-3 lg:grid-cols-3">
                {[
                  ["Canonical route sequence", plan45CanonicalRouteItems],
                  ["Supporting routes", plan45SupportingRouteItems],
                  ["Dormant parallel routes", plan45DormantRouteItems],
                ].map(([title, rows]) => (
                  <div className={`${commandInsetClass} p-3`} key={String(title)}>
                    <h3 className={`text-sm font-semibold ${commandTextClass}`}>{String(title)}</h3>
                    <dl className="mt-3 grid gap-2 text-xs">
                      {(rows as string[][]).map(([label, value]) => (
                        <div className="grid grid-cols-[8.75rem_minmax(0,1fr)] gap-2" key={`plan45-${label}`}>
                          <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                            {label}
                          </dt>
                          <dd className={`break-all font-mono ${commandTextClass}`}>{value}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                ))}
              </div>
            </section>
              </div>
            </details>
          </section>

          <aside
            aria-label="Review pane"
            className={`${commandPanelClass} space-y-4 p-4 min-[920px]:col-span-2 min-[1200px]:col-span-1 min-[1200px]:sticky min-[1200px]:top-4 min-[1200px]:max-h-[calc(100dvh-2rem)] min-[1200px]:overflow-auto`}
          >
            <section role="status" aria-live="polite" aria-labelledby="pipeline-steps-heading">
              <p className={commandLabelClass}>Plan / steps</p>
              <h2 id="pipeline-steps-heading" className={`mt-2 text-lg font-semibold ${commandTextClass}`}>Single-lane pipeline</h2>
              <p className={`mt-1 text-sm ${commandMutedClass}`}>
                {reversibleSuiteState.status === "running" || reversibleSuiteState.status === "stopping"
                  ? reversibleSuiteState.currentPrompt || "Trial suite is running."
                  : activeRunDisplay.previewState.status === "applied" && activeRunDisplay.previewState.changedFiles.length > 0
                  ? "Files changed on disk. Review or undo this run before starting another."
                  : activeRunDisplay.pipelineDetail}
              </p>
              <ol className="mt-4 space-y-2">
                {codingPipelineSteps.map((step, index) => (
                  <li className={`${commandInsetClass} p-3`} key={step.label}>
                    <div className="flex items-start gap-3">
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] text-xs font-semibold text-[var(--ddv4-fg-muted)]">
                        {index + 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className={`text-sm font-semibold ${commandTextClass}`}>{step.label}</p>
                          <span className={`inline-flex min-h-7 items-center rounded-md border px-2 text-[10px] font-semibold uppercase tracking-[0.12em] ${codingStepStatusClass(step.status)}`}>
                            {step.status}
                          </span>
                        </div>
                        <p className={`mt-2 break-words text-xs leading-5 ${commandMutedClass}`}>{step.detail}</p>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
              <dl className="mt-4 grid gap-2 text-xs">
                {[
                  ["Model", reversibleSuiteState.status !== "idle" ? reversibleSuiteState.model : activeRunProviderTruth.modelLabel],
                  ["Task ID", activeRunDisplay.taskLabel],
                  ["Trace ID", activeRunDisplay.previewState.traceId ?? "none"],
                  ["Output hash", activeRunDisplay.previewState.outputHash ?? "none"],
                ].map(([label, value]) => (
                  <div className="grid grid-cols-[5.75rem_minmax(0,1fr)] gap-2" key={label}>
                    <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">{label}</dt>
                    <dd className={`break-all font-mono ${commandTextClass}`}>{value}</dd>
                  </div>
                ))}
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
                disabled={!hasReversibleSuiteDiagnostics}
                onClick={() => void copyReversibleSuiteDiagnostics()}
                type="button"
              >
                <Copy aria-hidden="true" size={16} />
                Copy trial diagnostics
              </button>
              {(previewState.status === "error" || previewState.error || previewState.reasonCode) ? (
                <div className={`${commandInsetClass} mt-4 p-3`}>
                  <p className={commandLabelClass}>Failure diagnostics</p>
                  <dl className="mt-3 grid gap-2 text-xs">
                    {[
                      ["reason_code", previewState.reasonCode ?? "none"],
                      ["route", previewState.routeCalled ?? "none"],
                      ["task_id", previewState.taskId || "none"],
                      ["technical_detail", previewState.technicalDetail ?? previewState.error ?? "none"],
                    ].map(([label, value]) => (
                      <div className="grid grid-cols-[8.5rem_minmax(0,1fr)] gap-2" key={label}>
                        <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                          {label}
                        </dt>
                        <dd className={`break-all font-mono ${commandTextClass}`}>{value}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              ) : null}
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
              {causalTraceRows.length > 0 ? (
                <div className={`${commandInsetClass} mt-4 p-3`}>
                  <p className={commandLabelClass}>Causal trace</p>
                  <dl className="mt-3 grid gap-2 text-xs">
                    {causalTraceRows.map(([label, value]) => (
                      <div className="grid grid-cols-[9.75rem_minmax(0,1fr)] gap-2" key={label}>
                        <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                          {label}
                        </dt>
                        <dd className={`break-all font-mono ${commandTextClass}`}>{formatNullable(value)}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              ) : null}
              {plan2SubsystemRows.length > 0 ? (
                <div className={`${commandInsetClass} mt-4 p-3`}>
                  <p className={commandLabelClass}>Plan 2 subsystem truth</p>
                  <ul className="mt-3 space-y-3 text-xs">
                    {plan2SubsystemRows.map((row) => (
                      <li className="rounded-md border border-[var(--ddv4-surface-border-soft)] p-3" key={row.subsystem}>
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className={`font-semibold ${commandTextClass}`}>{row.subsystem}</p>
                          <p className="font-mono uppercase text-[var(--ddv4-fg-faint)]">{row.status || "NOT_INTEGRATED"}</p>
                        </div>
                        <dl className="mt-3 grid gap-2">
                          {[
                            ["trace_id", row.traceId],
                            ["invocation_event_id", row.invocationEventId],
                            ["consumer_event_id", row.consumerEventId],
                            ["consumed_by", row.consumedBy],
                            ["output_hash", row.outputHash],
                          ].map(([label, value]) => (
                            <div className="grid grid-cols-[9.75rem_minmax(0,1fr)] gap-2" key={label}>
                              <dt className="font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                                {label}
                              </dt>
                              <dd className={`break-all font-mono ${commandTextClass}`}>{formatNullable(value)}</dd>
                            </div>
                          ))}
                        </dl>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
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
              {showTrialCleanupPanel
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
      {embedded ? null : <DashboardDemoV4FloatingNav desktopVariant="full-height" />}
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

class PayloadBackedError extends Error {
  payload: unknown;
  status: number;

  constructor(message: string, payload: unknown, status: number) {
    super(message);
    this.name = "PayloadBackedError";
    this.payload = payload;
    this.status = status;
  }
}

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit = {},
  timeoutMs = 8000,
) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  const externalSignal = init.signal;
  const onExternalAbort = () => controller.abort();
  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort();
    } else {
      externalSignal.addEventListener("abort", onExternalAbort);
    }
  }
  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal,
    });
  } catch (error) {
    if (externalSignal?.aborted) {
      throw error;
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new BrowserAbortTimeoutError();
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
    externalSignal?.removeEventListener("abort", onExternalAbort);
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

type LongRunningTaskRetryOptions = {
  maxAttempts?: number;
  onTransientError?: (attempt: number, error: unknown) => void;
};

async function fetchLongRunningTaskWithRetry(
  init: RequestInit,
  timeoutMs: number,
  options: LongRunningTaskRetryOptions = {},
) {
  const maxAttempts = options.maxAttempts ?? 3;
  let lastError: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    if (init.signal?.aborted) {
      throw new DOMException("The operation was aborted.", "AbortError");
    }
    try {
      return await fetchWithTimeout("/v1/tasks/long-running", init, timeoutMs);
    } catch (error) {
      lastError = error;
      if (!isTransientNetworkFetchError(error) || attempt === maxAttempts) {
        throw error;
      }
      options.onTransientError?.(attempt, error);
      await waitForPromptPacketRetry(attempt);
    }
  }
  throw lastError;
}

type PromptPacketRetryOptions = {
  maxAttempts?: number;
  onRetry?: (attempt: number) => void;
  totalBudgetMs?: number;
};

async function fetchPromptPacketWithRetry(
  init: RequestInit,
  timeoutMs: number,
  options: PromptPacketRetryOptions = {},
) {
  const maxAttempts = options.maxAttempts ?? 3;
  const totalBudgetMs = options.totalBudgetMs ?? timeoutMs * maxAttempts;
  let lastError: unknown;
  const fetchStartedAt = Date.now();
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    if (Date.now() - fetchStartedAt >= totalBudgetMs) {
      throw new BrowserAbortTimeoutError("prompt_packet_total_budget_exceeded");
    }
    if (init.signal?.aborted) {
      throw new DOMException("The operation was aborted.", "AbortError");
    }
    options.onRetry?.(attempt);
    try {
      const response = await fetchWithTimeout("/v1/decisions/prompt-packet", init, timeoutMs);
      return response;
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
  if (error instanceof DOMException && error.name === "AbortError") return "browser_abort_timeout";
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

function storefrontProbeFromPayload(value: unknown): TargetPluginStorefrontProbeResult | null {
  const record = asRecord(value);
  const previewStatus = stringValue(record.preview_behavior_status);
  const runtimeStatus = stringValue(record.storefront_runtime_status);
  if (!previewStatus || !runtimeStatus) return null;
  return record as unknown as TargetPluginStorefrontProbeResult;
}

function storefrontProbeFromManagedBrowserEvidence(
  value: unknown,
): TargetPluginStorefrontProbeResult | null {
  const record = asRecord(value);
  if (stringValue(record.storefront_runtime_engine) !== "playwright_chromium") {
    return null;
  }
  const runtimeStatus =
    stringValue(record.storefront_runtime_status) === "passed" ? "passed" : "failed";
  const productCount = numberValue(record.product_count) ?? 0;
  const renderedCardCount = numberValue(record.rendered_card_count) ?? 0;
  const visibleFields = asRecord(record.visible_fields);
  const allFieldsVisible = ["name", "price", "category", "description"].every(
    (field) => visibleFields[field] === true,
  );
  const assetResponses = asRecord(record.asset_responses);
  const assetsPassed =
    Object.keys(assetResponses).length >= 4 &&
    Object.values(assetResponses).every((status) => status === 200);
  const passed =
    runtimeStatus === "passed" &&
    productCount >= 6 &&
    renderedCardCount === productCount &&
    allFieldsVisible &&
    assetsPassed;
  return {
    preview_behavior_status: passed ? "PASS_STOREFRONT_RENDERED" : "FAIL_BARE_PAGE",
    preview_visible_text_summary: passed
      ? `Managed Chromium rendered ${renderedCardCount} LumaCart product cards with name, price, category, and description.`
      : "Managed Chromium did not prove the required storefront DOM.",
    preview_asset_status: assetsPassed ? "present" : "empty",
    product_count: productCount,
    card_render_path_present: renderedCardCount === productCount && productCount > 0,
    category_render_path_present: visibleFields.category === true,
    description_render_path_present: visibleFields.description === true,
    price_render_path_present: visibleFields.price === true,
    stylesheet_linked: record.stylesheet_loaded === true,
    visible_product_names: arrayOfStrings(record.rendered_headings),
    storefront_runtime_status: runtimeStatus,
    storefront_runtime_engine: "playwright_chromium",
    real_browser_used: record.real_browser_used === true,
    browser_evidence_source: "source_proxy_managed_playwright",
    storefront_runtime_product_count: renderedCardCount,
    storefront_runtime_visible_fields: {
      name: visibleFields.name === true,
      price: visibleFields.price === true,
      category: visibleFields.category === true,
      description: visibleFields.description === true,
    },
    storefront_runtime_reasons: passed
      ? []
      : [stringValue(record.reason) ?? "managed_browser_dom_contract_failed"],
  };
}

function diagnosticPayloadFromResponse(payload: unknown): Record<string, unknown> {
  const record = asRecord(payload);
  const detail = asRecord(record.detail);
  const detailDiagnosticEnvelope = asRecord(detail.diagnostic_envelope);
  if (Object.keys(detailDiagnosticEnvelope).length > 0) return detailDiagnosticEnvelope;
  const diagnosticEnvelope = asRecord(record.diagnostic_envelope);
  if (Object.keys(diagnosticEnvelope).length > 0) return diagnosticEnvelope;
  return Object.keys(detail).length > 0 ? detail : record;
}

function diagnosticPayloadFromError(error: unknown): Record<string, unknown> | null {
  if (error instanceof PayloadBackedError) {
    const diagnostic = diagnosticPayloadFromResponse(error.payload);
    return Object.keys(diagnostic).length > 0 ? diagnostic : null;
  }
  return null;
}

function missingSelectedPromptDiagnosticEnvelope({
  message,
  rawBackendStatus,
  selectedPromptId,
  taskId,
  timeoutLayer,
}: {
  message: string;
  rawBackendStatus: string;
  selectedPromptId: string;
  taskId: string | null;
  timeoutLayer: string;
}): Record<string, unknown> {
  const effectiveTaskId = taskId ?? "missing: backend did not provide field";
  const reasonCode =
    timeoutLayer === "network_fetch_error"
      ? "network_fetch_error"
      : timeoutLayer === "browser_abort_timeout"
        ? "browser_abort_timeout"
        : "missing_diagnostic_envelope";
  const recommendedNextAction =
    "Inspect Source Proxy and Next route health for the selected prompt task, then rerun only this prompt after the route returns a structured diagnostic envelope.";
  return {
    stage_id: "coding_ui.selected_prompt.failure_catch",
    subsystem: "coding_cockpit_selected_prompt",
    task_id: effectiveTaskId,
    selected_prompt_task_id: effectiveTaskId,
    run_id: `selected_prompt:${selectedPromptId}:${effectiveTaskId}`,
    trace_id: "missing: no diagnostic envelope received",
    invocation_event_id: "missing: no diagnostic envelope received",
    consumer_event_id: "missing: no diagnostic envelope received",
    status: "error",
    truth_status: "MISSING_DIAGNOSTIC_ENVELOPE",
    safe_block: true,
    error_code: reasonCode,
    reason_code: reasonCode,
    human_message: message,
    machine_reason: reasonCode,
    apply_block_layer: "route_error_before_model_call",
    task_creation_status: taskId ? "task_id_known_after_route_error" : "failed_before_task_id",
    task_creation_elapsed_ms: null,
    task_creation_timeout_stage: timeoutLayer,
    task_creation_last_checkpoint: "ui_failure_catch",
    task_creation_blocking_subsystem: "coding_cockpit_selected_prompt",
    recommended_next_action: recommendedNextAction,
    task_identity: {
      backend_task_id: effectiveTaskId,
      selected_prompt_id: selectedPromptId,
      selected_prompt_task_id: effectiveTaskId,
      trace_id: "missing: no diagnostic envelope received",
    },
    approval_binding: {
      approval_binding_status: "not_run: route_error_before_model_call",
      approval_binding_safe_block: true,
      apply_block_layer: "route_error_before_model_call",
      block_receipt_path: "not_applicable: route_error_before_model_call_before_apply_receipt",
      safe_block: true,
    },
    diff_provenance: {
      applied_diff_sha256: "not_recorded: apply_did_not_happen",
      approved_diff_sha256: "not_recorded: apply_did_not_happen",
      backend_converted_diff_sha256: "missing: backend did not provide field",
      changed_files: [],
      diff_source: "not_run: route_error_before_model_call",
    },
    verification: {
      post_apply_verification_status: "not_run: route_error_before_model_call",
      preview_verification_status: "not_run: route_error_before_model_call",
    },
    anti_cheat: {
      anti_cheat_status: "not_run",
      anti_cheat_reasons: ["route_error_before_model_call"],
      grader_result_state: "not_applicable: route_error_before_model_call",
      trial_result_trust_status: "missing_diagnostic_envelope",
    },
    acceptance_gate: {
      acceptance_failures: [reasonCode],
      binary_verdict: "NO-GO",
      causal_crosscheck_status: "skipped_with_reason",
      fail_closed_lane_status: "skipped_with_reason",
      missing_fields: ["diagnostic_envelope"],
      phase_verifier_status: "skipped_with_reason",
      plan5_gate_id: "plan5_ui_missing_diagnostic_envelope",
      plan5_gate_present: false,
      plan5_gate_version: "plan5_acceptance_v1",
      reason: "missing_diagnostic_envelope",
    },
    final_truth_summary: {
      commit_safe: false,
      proof_level: "operator_ui_route_failure",
      raw_backend_status: rawBackendStatus,
      recommended_next_action: recommendedNextAction,
      run_status: "error",
      block_receipt_path: "not_applicable: route_error_before_model_call_before_apply_receipt",
      truth_status: "MISSING_DIAGNOSTIC_ENVELOPE",
      why_not_go: message,
    },
    unavailable_fields: [
      { field: "trace_id", reason: "missing: no diagnostic envelope received" },
      { field: "approval_binding.expected_approval_id", reason: "route_error_before_model_call" },
      { field: "approval_binding.received_approval_id", reason: "route_error_before_model_call" },
      { field: "anti_cheat.detector_results", reason: "route_error_before_model_call" },
      { field: "receipt_path", reason: "apply_did_not_happen" },
    ],
    persisted_at: "missing: no diagnostic envelope received",
    surfaced_at: new Date().toISOString(),
  };
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
  const record = asRecord(payload);
  const diagnostics = asRecord(record.coder_diagnostics ?? record.coderDiagnostics);
  const diagnosticsSummary = asRecord(record.diagnostics_summary ?? record.diagnosticsSummary);
  const compact = {
    status: stringValue(record.status),
    reason_code: stringValue(record.reason_code) ?? stringValue(record.reasonCode),
    no_diff_failure_cause:
      stringValue(record.no_diff_failure_cause) ??
      stringValue(record.noDiffFailureCause) ??
      stringValue(diagnostics.no_diff_failure_cause) ??
      stringValue(diagnosticsSummary.no_diff_failure_cause),
    safe_response_classification:
      stringValue(record.safe_response_classification) ??
      stringValue(record.safeResponseClassification) ??
      stringValue(diagnostics.safe_response_classification) ??
      stringValue(diagnosticsSummary.safe_response_classification),
    parser_extractor_decision:
      stringValue(record.parser_extractor_decision) ??
      stringValue(record.parserExtractorDecision) ??
      stringValue(diagnostics.parser_extractor_decision) ??
      stringValue(diagnosticsSummary.parser_extractor_decision),
    raw_response_length:
      diagnostics.raw_response_length ?? diagnosticsSummary.raw_response_length,
    raw_response_excerpt_safe:
      stringValue(diagnostics.raw_response_excerpt_safe) ?? stringValue(diagnosticsSummary.raw_response_excerpt_safe),
    selected_target: stringValue(record.target) ?? stringValue(record.selected_target),
    allowed_files: arrayOfStrings(record.allowed_files),
    changed_files: changedFilesFromPayload(payload),
  };
  try {
    return JSON.stringify(compact).slice(0, 800);
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

function nestedRecord(record: Record<string, unknown>, keys: string[]): Record<string, unknown> {
  return keys.reduce<Record<string, unknown>>((current, key) => asRecord(current[key]), record);
}

type CausalTraceFields = {
  traceId: string | null;
  invocationEventId: string | null;
  consumerEventId: string | null;
  consumerSubsystem: string | null;
  causalStatusAfter: string | null;
};

export function causalTraceFromPayload(payload: unknown): CausalTraceFields {
  const record = asRecord(payload);
  const task = asRecord(record.task);
  const execution = asRecord(record.execution);
  const taskTrace = asRecord(task.causal_trace);
  const executionTrace = asRecord(execution.causal_trace);
  const trace = Object.keys(executionTrace).length > 0 ? executionTrace : taskTrace;
  return {
    traceId: stringValue(execution.trace_id) ?? stringValue(trace.trace_id) ?? null,
    invocationEventId:
      stringValue(execution.invocation_event_id) ??
      stringValue(trace.invocation_event_id) ??
      null,
    consumerEventId: stringValue(trace.consumer_event_id) ?? null,
    consumerSubsystem: stringValue(trace.consumer_subsystem) ?? null,
    causalStatusAfter: stringValue(trace.status_after) ?? null,
  };
}

export function outputHashFromPayload(payload: unknown): string | null {
  const record = asRecord(payload);
  const task = asRecord(record.task);
  const execution = asRecord(record.execution);
  const taskExecution = asRecord(task.execution);
  const taskAudit = nestedRecord(task, ["ast_snapshot", "approved_execution_evidence", "audit"]);
  return (
    stringValue(record.output_hash) ??
    stringValue(record.outputHash) ??
    stringValue(execution.output_hash) ??
    stringValue(execution.outputHash) ??
    stringValue(taskExecution.output_hash) ??
    stringValue(taskExecution.outputHash) ??
    stringValue(taskAudit.output_hash) ??
    stringValue(taskAudit.outputHash) ??
    null
  );
}

export function plan2SubsystemIntegrationsFromPayload(payload: unknown): Plan2SubsystemIntegration[] {
  const record = asRecord(payload);
  const task = asRecord(record.task);
  const dataTask = asRecord(asRecord(record.data).task);
  const directSnapshot = asRecord(record.ast_snapshot);
  const taskSnapshot = asRecord(task.ast_snapshot);
  const dataTaskSnapshot = asRecord(dataTask.ast_snapshot);
  const snapshot =
    Object.keys(taskSnapshot).length > 0
      ? taskSnapshot
      : Object.keys(dataTaskSnapshot).length > 0
        ? dataTaskSnapshot
        : directSnapshot;
  const integrations = asRecord(snapshot.plan_2_subsystem_integrations);
  return Object.entries(integrations)
    .map(([subsystem, value]) => {
      const item = asRecord(value);
      const trace = asRecord(item.causal_trace);
      return {
        subsystem,
        status: stringValue(item.status) ?? "NOT_INTEGRATED",
        outputHash: stringValue(item.output_hash) ?? stringValue(item.outputHash) ?? null,
        traceId: stringValue(item.trace_id) ?? stringValue(trace.trace_id) ?? null,
        invocationEventId:
          stringValue(item.invocation_event_id) ??
          stringValue(item.invocationEventId) ??
          stringValue(trace.invocation_event_id) ??
          null,
        consumerEventId:
          stringValue(item.consumer_event_id) ??
          stringValue(item.consumerEventId) ??
          stringValue(trace.consumer_event_id) ??
          null,
        consumedBy:
          stringValue(item.consumed_by) ??
          stringValue(item.consumedBy) ??
          stringValue(trace.consumer_subsystem) ??
          null,
      };
    })
    .sort((left, right) => left.subsystem.localeCompare(right.subsystem));
}

export function changedFilesFromPayload(payload: unknown): string[] {
  const record = asRecord(payload);
  const task = asRecord(record.task);
  const execution = asRecord(record.execution);
  const taskExecution = asRecord(task.execution);
  const taskAudit = nestedRecord(task, ["ast_snapshot", "approved_execution_evidence", "audit"]);
  const changed =
    Array.isArray(record.applied_changed_files)
      ? record.applied_changed_files
      : Array.isArray(record.disk_changed_files)
        ? record.disk_changed_files
        : Array.isArray(record.changed_files)
          ? record.changed_files
          : Array.isArray(execution.applied_changed_files)
            ? execution.applied_changed_files
            : Array.isArray(execution.disk_changed_files)
              ? execution.disk_changed_files
              : Array.isArray(execution.changed_files)
                ? execution.changed_files
                : Array.isArray(taskExecution.applied_changed_files)
                  ? taskExecution.applied_changed_files
                  : Array.isArray(taskExecution.disk_changed_files)
                    ? taskExecution.disk_changed_files
                    : Array.isArray(taskExecution.changed_files)
                      ? taskExecution.changed_files
                      : taskAudit.changed_files;
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

export function changedFileSnapshotsFromPayload(payload: unknown): ChangedFileSnapshot[] {
  const record = asRecord(payload);
  const execution = asRecord(record.execution);
  const task = asRecord(record.task);
  const taskExecution = asRecord(task.execution);
  const taskAudit = nestedRecord(task, ["ast_snapshot", "approved_execution_evidence", "audit"]);
  const candidates = [
    record.changed_file_snapshots,
    record.changedFileSnapshots,
    execution.changed_file_snapshots,
    execution.changedFileSnapshots,
    taskExecution.changed_file_snapshots,
    taskExecution.changedFileSnapshots,
    taskAudit.changed_file_snapshots,
    taskAudit.changedFileSnapshots,
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

function snapshotHasRestorableBaseline(snapshots: ChangedFileSnapshot[], path: string): boolean {
  const snapshot = snapshotForPath(snapshots, path);
  return Boolean(snapshot && (snapshot.missingBeforeApply || snapshot.sha256Before));
}

export function snapshotRestored(
  applySnapshots: ChangedFileSnapshot[],
  revertSnapshots: ChangedFileSnapshot[],
  path: string,
): boolean {
  const applySnapshot = snapshotForPath(applySnapshots, path);
  const revertSnapshot = snapshotForPath(revertSnapshots, path);
  if (applySnapshot?.missingBeforeApply) {
    return Boolean(revertSnapshot && revertSnapshot.sha256After === null);
  }
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

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function arrayOfStrings(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => (typeof item === "string" ? item.trim() : "")).filter(Boolean);
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
