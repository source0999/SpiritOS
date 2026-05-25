"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent,
  type TouchEvent,
} from "react";
import {
  BellRing,
  Bot,
  Clock3,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Code2,
  Copy,
  FolderGit2,
  GitBranch,
  MessageSquarePlus,
  PanelLeft,
  Plus,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";

import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import { buildCodingAlertRows, codingAlertsReceiptLines } from "@/lib/coding/alert-surface";
import { backendTruthReceiptLines, buildBackendTruthRows } from "@/lib/coding/backend-truth-surface";
import {
  codingProviderModelOptionById,
  defaultModelIdForProvider,
  describeCodingProviderIntent,
  getCodingProviderModelOptions,
  getCodingProviderStatuses,
  providerModelReceiptLines,
  type CodingProviderId,
  type CodingProviderModelId,
} from "@/lib/coding/model-provider-status";
import { derivePlainEnglishScopeDraft } from "@/lib/coding/plain-english-scope";
import {
  buildPublicCodingWorkItems,
  formatCodingProgressElapsed,
  publicCodingWorkReceipt,
} from "@/lib/coding/progress-surface";
import {
  DEFAULT_PROXY_TRIAL_ID,
  PROXY_TRIAL_BANK_EXPECTED_RECORD_COUNT,
  PROXY_TRIAL_BANK_VERSION,
  PROXY_TRIAL_PROMPTS,
  PROXY_TRIAL_SHARED_BANK_INTEGRATED,
  proxyTrialWidgetDryRunEvidence,
  type ProxyTrialPrompt,
} from "@/lib/coding/proxy-trial-prompts";
import { buildCodingSettingsRows, settingsReceiptLines } from "@/lib/coding/settings-surface";
import { deriveCodingTimelineEvents } from "@/lib/coding/timeline-events";
import { buildCodingUsageTimeRows, usageTimeReceiptLines } from "@/lib/coding/usage-time-surface";
import { collectPathsFromUnifiedDiff } from "@/lib/coding/unified-diff-paths";
import {
  CODING_WORKSPACE_CONTEXTS,
  DEFAULT_CODING_WORKSPACE_CONTEXT_ID,
  codingWorkspaceContextById,
  workspaceFolderProofRows,
  workspaceReceiptLines,
  type CodingWorkspaceContextId,
} from "@/lib/coding/workspace-context";
import "@/styles/dashboard-demo-v4.css";

type ShellChat = {
  id: string;
  title: string;
  meta: string;
  emptyState: string;
  providerId: CodingProviderId;
  providerModelId?: CodingProviderModelId;
  workspaceContextId?: CodingWorkspaceContextId;
  codingMode: boolean;
  draftText: string;
  appliedAt: string | null;
  approvedAt: string | null;
  applyMessage: string;
  allowedFiles: string[];
  blockedFields: string[];
  changedFiles: string[];
  designProposalIntake?: DesignProposalIntakeDisplay | null;
  isApplying: boolean;
  isVerifying: boolean;
  previewMessage: string;
  previewStatus: "idle" | "loading" | "ready" | "blocked" | "error";
  previewTarget: string;
  proposedDiff: string;
  taskId: string;
  taskSubmitted: boolean;
  receiptCommandsRun: string;
  receiptFocusedTestResult: string;
  receiptLintResult: string;
  receiptPassFail: string;
  receiptTypecheckResult: string;
  rollbackHint: string;
  verificationMessage: string;
  verificationStatus: "not_started" | "required" | "running" | "passed" | "failed" | "unavailable";
  verifiedAt: string | null;
  persisted?: boolean;
};

type DesignProposalIntakeDisplay = {
  applyAuthority: boolean | null;
  approvalAuthority: boolean | null;
  blockedBy: string[];
  formatted: string;
  packetReady: boolean | null;
  reasonCodes: string[];
  status: string;
};

type SessionLogEntry = {
  at: string;
  detail: string;
  id: string;
  status: "info" | "running" | "ready" | "blocked" | "failed" | "inconclusive";
  title: string;
};

type TrialBatchStatus = "idle" | "queued" | "running" | "blocked" | "complete" | "failed";

type ActiveRunState = "idle" | "queued" | "running" | "blocked" | "complete" | "failed";

type StagedPromptPreviewStatus = "pending" | "current" | "completed" | "blocked";

type DrawerShellId = "settings" | "diagnostics" | "evidence";

type TrialBatchProgress = {
  currentStep: number;
  currentTrialId: string;
  currentTrialIndex: number;
  currentTrialTitle: string;
  stageLabel: string;
  stageName: string;
  totalSteps: number;
  totalTrials: number;
};

type TrialReasonCode =
  | "protected_path"
  | "allowed_files_mismatch"
  | "requirement_coverage_failed"
  | "diff_validation_failed"
  | "replacement_content_invalid"
  | "already_satisfied"
  | "already_satisfied_noop_route_gap"
  | "scope_too_broad"
  | "target_unresolved"
  | "frontend_preview_route_gap"
  | "productive_preview_route_gap"
  | "no_diff_route_gap"
  | "missing_target_context"
  | "backend_diff_generation_gap"
  | "blocked_after_retries"
  | "unknown_blocker";

type CodingAdvisoryHelper = {
  blockedActions: string;
  evidence: string;
  manualNextStep: string;
  name: string;
  proposal: string;
  summary: string;
};

const manualHundredFrontendDiagnostic = {
  alreadySatisfiedNoops: 1,
  currentGrade: "B-",
  lastDiagnosticStatus: "Terminal 100 diagnostic accepted; browser checklist still required",
  nextRecommendedFixBatch:
    "Preflight UI organization, then reduce frontend preview gaps, scope-too-broad prompts, and missing target context.",
  productivePreviews: 8,
  safeBlockers: 91,
  terminalHundredStatus: "accepted_terminal_100_prompt_regression",
  terminalTwentyFiveStatus: "promote_to_100_prompt_regression_candidate",
  totalPrompts: 100,
  unexpectedFiles: 0,
  unsafeFailures: 0,
};

const manualHundredStatusLabels = {
  terminalHundredStatus: "Accepted terminal 100 regression",
  terminalTwentyFiveStatus: "Promoted to 100 candidate",
};

const trialBatchLocalStepsPerTrial = 5;
const codingCommandCenterBuildMarker = "target-unresolved-safe-20260525-0248";

const manualHundredAuthorityFlags = [
  "apply_authority: false",
  "commit_authority: false",
  "push_authority: false",
  "execute_approved_authority: false",
  "provider_authority: false",
  "shell_expansion_authority: false",
  "reset_stash_clean_authority: false",
  "phase_7_live_preview_authority: false",
];

const manualHundredTopBlockers = [
  {
    code: "frontend_preview_route_gap",
    count: 12,
    meaning: "The frontend preview path could not fully show or prepare the expected preview.",
    why: "Safety passed, but Britton cannot yet inspect enough useful frontend preview evidence.",
    next: "Inspect the preview route display and fallback copy for these UI-centered prompts before live authority.",
    kind: "implementation-gap",
  },
  {
    code: "scope_too_broad",
    count: 12,
    meaning: "The prompt needs a smaller target, fewer files, or a clearer task boundary.",
    why: "Broad prompts produce safe blockers instead of actionable previews.",
    next: "Rewrite the task around one component, one route, or one file group with explicit allowed files.",
    kind: "usefulness-bad",
  },
  {
    code: "missing_target_context",
    count: 11,
    meaning: "The proxy needs a specific route, component, file, or expected output.",
    why: "The system stayed safe, but it lacked enough target context to form a useful diff.",
    next: "Add the exact route, component name, target file, and expected visible result to the prompt.",
    kind: "usefulness-bad",
  },
  {
    code: "protected_path",
    count: 11,
    meaning: "The request touched a protected file or area and correctly stayed blocked.",
    why: "This is desired safety behavior and should not be relaxed during preflight.",
    next: "Keep these blocked unless Britton separately approves a protected-path lane.",
    kind: "safety-good",
  },
  {
    code: "already_satisfied_noop_route_gap",
    count: 10,
    meaning: "The proxy thought the task was already done but could not show a strong no-op preview route.",
    why: "No-op honesty is good, but the proof route needs clearer evidence.",
    next: "Improve already-satisfied preview receipts so the UI can show why no diff is correct.",
    kind: "implementation-gap",
  },
  {
    code: "backend_diff_generation_gap",
    count: 10,
    meaning: "The backend could not generate a usable preview diff for that task shape yet.",
    why: "The prompt may be valid, but the diff generator does not have the right fallback.",
    next: "Inspect backend diff-generation gaps for metadata or structured task prompts.",
    kind: "implementation-gap",
  },
  {
    code: "no_diff_route_gap",
    count: 10,
    meaning: "The preview route completed without a useful diff.",
    why: "A completed route without evidence is safe but not useful for manual approval.",
    next: "Improve no-diff receipts so Britton can tell whether this was no-op, missing context, or a generator miss.",
    kind: "implementation-gap",
  },
  {
    code: "target_unresolved",
    count: 10,
    meaning: "The request could not be mapped to a specific implementation target.",
    why: "The system cannot preview safely when the target file or component is ambiguous.",
    next: "Name the expected file, route, component, or test before rerunning the diagnostic.",
    kind: "usefulness-bad",
  },
];

const codingAdvisoryHelpers: CodingAdvisoryHelper[] = [
  {
    blockedActions: "No repo scan, file edit, apply, queue, worker, commit, or push.",
    evidence: "Selected trial target, allowed files, top blockers, and 100-prompt diagnostic counts.",
    manualNextStep: "Use the selected trial metadata to keep the next fix batch scoped to one file family.",
    name: "Component Mapper",
    proposal: "Map the selected prompt to likely component, docs, and test zones before asking Proxy for another preview.",
    summary: "Turns approved Proxy context into a bounded component map.",
  },
  {
    blockedActions: "No approval, apply, token consumption, route execution, provider call, or protected-path relaxation.",
    evidence: "Authority flags, protected-path blockers, unsafe failure count, and unexpected file count.",
    manualNextStep: "Confirm the next prompt names allowed files and keeps protected paths out of scope.",
    name: "Safety Reviewer",
    proposal: "Review the next task against allowed files, protected paths, and the no-authority boundary before running Proxy.",
    summary: "Keeps the safety gate legible before Britton asks for more previews.",
  },
  {
    blockedActions: "No test execution, package install, broad build, shell expansion, or command authority.",
    evidence: "Current focused component test, typecheck habit, and diagnostic blocker categories.",
    manualNextStep: "Suggest focused checks only after the next implementation lane names its exact files.",
    name: "Test Scribe",
    proposal: "Draft the smallest useful check list for the next approved lane without running anything itself.",
    summary: "Converts the lane into focused verification suggestions.",
  },
  {
    blockedActions: "No source writes, receipt writes, evidence-store writes, apply, commit, or push.",
    evidence: "Compact diagnostic packet, preview status, changed-file summaries, and blocker counts.",
    manualNextStep: "Summarize what changed only after Proxy produces preview evidence.",
    name: "Change Scribe",
    proposal: "Prepare a human-readable change summary from approved preview evidence and diagnostics.",
    summary: "Turns Proxy evidence into a concise change narrative.",
  },
  {
    blockedActions: "No check pass/fail claims, fabricated evidence, storage writes, or browser automation authority.",
    evidence: "Plan closeouts, manual browser checks, and copyable diagnostic packets.",
    manualNextStep: "Keep browser checks in chat and terminal commands as workflow commands only.",
    name: "Runbook Scribe",
    proposal: "Draft manual browser verification and terminal workflow commands as separate operator aids.",
    summary: "Keeps verification instructions readable for Britton.",
  },
  {
    blockedActions: "No roadmap mutation outside approved docs lanes, no next-plan auto-start, and no approval inference.",
    evidence: "Master roadmap gates, Plan 2 merge design, and current Plan 3 approval boundary.",
    manualNextStep: "Record the next plan title only after the current plan reaches manual verification.",
    name: "Blueprint Scribe",
    proposal: "Draft lane notes that keep Plan 4 gated until Plan 3 browser verification is accepted.",
    summary: "Keeps the fleet roadmap coherent without promoting itself.",
  },
  {
    blockedActions: "No staging, commit, push, branch, tag, merge, release, checkout, reset, stash, or clean.",
    evidence: "Files changed, checks run, and closeout statements supplied by the active lane.",
    manualNextStep: "Wait for Britton to request commit text after verification; keep it as text only.",
    name: "Commit Scribe",
    proposal: "Draft a commit title/body later from verified evidence without touching git state.",
    summary: "Prepares commit language only when asked.",
  },
  {
    blockedActions: "No tag, release, deploy, provider call, autonomy promotion, or final CSS start.",
    evidence: "Plan sequence, diagnostics, authority statements, and remaining UX issues.",
    manualNextStep: "Hold release and final polish until functionality diagnostics pass in later plans.",
    name: "Release Steward",
    proposal: "Summarize readiness risks and keep release/polish blocked until the planned diagnostic gates pass.",
    summary: "Keeps final polish and release thinking gated.",
  },
];

const manualHundredChecklist = [
  "Open /coding in the browser.",
  "Confirm the diagnostic summary is visible.",
  "Confirm total prompts shows 100.",
  "Confirm unsafe failures shows 0.",
  "Confirm unexpected files shows none or 0.",
  "Confirm all authority flags are false.",
  "Confirm productive previews shows 8 or the latest count.",
  "Confirm safe blockers show 91 or the latest count.",
  "Confirm no unknown_blocker category is present.",
  "Confirm top blocker categories are visible.",
  "Expand each top blocker category and confirm plain-English explanation is readable.",
  "Confirm the next recommended fix batch is visible.",
  "Confirm no apply, commit, push, route execution, provider, shell, reset, stash, clean, or live preview controls are enabled.",
  "Confirm older packet/evidence noise is collapsed or visually secondary.",
  "Confirm the UI says the proxy is ready for preflight organization, not live authority.",
];

const initialShellChats: ShellChat[] = [
  {
    id: "draft",
    title: "New coding chat",
    meta: "Ready",
    emptyState: "No coding task drafted",
    providerId: "local",
    providerModelId: "local-default",
    workspaceContextId: "spiritos",
    codingMode: false,
    draftText: "",
    appliedAt: null,
    approvedAt: null,
    applyMessage: "",
    allowedFiles: [],
    blockedFields: [],
    changedFiles: [],
    isApplying: false,
    isVerifying: false,
    previewMessage: "Preview not requested.",
    previewStatus: "idle",
    previewTarget: "",
    proposedDiff: "",
    taskId: "",
    taskSubmitted: false,
    receiptCommandsRun: "not run yet",
    receiptFocusedTestResult: "not reported by UI",
    receiptLintResult: "not reported by UI",
    receiptPassFail: "not run yet",
    receiptTypecheckResult: "not reported by UI",
    rollbackHint: "keep the task bounded; use git diff before any apply.",
    verificationMessage: "Verification has not started.",
    verificationStatus: "not_started",
    verifiedAt: null,
  },
  {
    id: "review",
    title: "Approval queue",
    meta: "Empty",
    emptyState: "Approval queue is empty",
    providerId: "local",
    providerModelId: "local-default",
    workspaceContextId: "spiritos",
    codingMode: false,
    draftText: "",
    appliedAt: null,
    approvedAt: null,
    applyMessage: "",
    allowedFiles: [],
    blockedFields: [],
    changedFiles: [],
    isApplying: false,
    isVerifying: false,
    previewMessage: "Preview not requested.",
    previewStatus: "idle",
    previewTarget: "",
    proposedDiff: "",
    taskId: "",
    taskSubmitted: false,
    receiptCommandsRun: "not run yet",
    receiptFocusedTestResult: "not reported by UI",
    receiptLintResult: "not reported by UI",
    receiptPassFail: "not run yet",
    receiptTypecheckResult: "not reported by UI",
    rollbackHint: "keep the task bounded; use git diff before any apply.",
    verificationMessage: "Verification has not started.",
    verificationStatus: "not_started",
    verifiedAt: null,
  },
];

const defaultWorkspace = codingWorkspaceContextById(DEFAULT_CODING_WORKSPACE_CONTEXT_ID);
const futureWindowsWorkspace = codingWorkspaceContextById("windows-projects");

const safetySteps = ["Draft", "Preview", "Approval", "Apply", "Verify"];
const previewStepTimeoutMs = 45_000;
const previewStepTimeoutSeconds = Math.round(previewStepTimeoutMs / 1000);
const taskStoryStorageKey = "spiritos:coding-command-center:task-story";
const chatPersistenceBoundary =
  "Chat list: current-session only. Task story: local refresh/reconnect review after staged activity. Durable chat history remains gated.";
const queuePreviewHonestyLabels = [
  "preview queue only",
  "no worker running",
  "no provider call",
  "no apply authority",
];
const trialInstructions = [
  "Pick a trial.",
  "Load the prompt.",
  "Run preview.",
  "Review diff or blocked reason.",
  "Stop before apply.",
];

function canUseLocalStoryPersistence() {
  return typeof window !== "undefined" && "localStorage" in window;
}

function hasTaskStoryActivity(chats: ShellChat[]) {
  return chats.some((chat) =>
    Boolean(
      chat.draftText.trim() ||
        chat.taskSubmitted ||
        chat.previewStatus !== "idle" ||
        chat.approvedAt ||
        chat.appliedAt ||
        chat.verifiedAt,
    ),
  );
}

function readStoredTaskStory():
  | {
      activeChatId: string;
      chats: ShellChat[];
    }
  | null {
  if (!canUseLocalStoryPersistence()) {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(taskStoryStorageKey);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as { activeChatId?: unknown; chats?: unknown };
    if (
      typeof parsed.activeChatId !== "string" ||
      !Array.isArray(parsed.chats) ||
      parsed.chats.length === 0
    ) {
      return null;
    }
    return {
      activeChatId: parsed.activeChatId,
      chats: parsed.chats as ShellChat[],
    };
  } catch {
    return null;
  }
}

function writeStoredTaskStory(chats: ShellChat[], activeChatId: string) {
  if (!canUseLocalStoryPersistence()) {
    return false;
  }
  if (!hasTaskStoryActivity(chats)) {
    window.localStorage.removeItem(taskStoryStorageKey);
    return false;
  }
  try {
    window.localStorage.setItem(
      taskStoryStorageKey,
      JSON.stringify({
        activeChatId,
        chats,
        version: 1,
      }),
    );
    return true;
  } catch {
    return false;
  }
}

function removeStoredTaskStory() {
  if (!canUseLocalStoryPersistence()) {
    return;
  }
  try {
    window.localStorage.removeItem(taskStoryStorageKey);
  } catch {
    // Ignore local storage failures; clearing visible UI state is still useful.
  }
}

function chipClass(tone: string) {
  if (tone === "local") {
    return "border-emerald-300/35 bg-emerald-300/10 text-emerald-100";
  }
  if (tone === "cloud") {
    return "border-sky-300/30 bg-sky-300/10 text-sky-100";
  }
  return "border-white/12 bg-white/[0.055] text-zinc-100";
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit,
  stepLabel: string,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), previewStepTimeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(
        `${stepLabel} timed out after ${previewStepTimeoutSeconds} seconds. No files changed.`,
      );
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function firstRecord(...values: unknown[]): Record<string, unknown> {
  for (const value of values) {
    if (value && typeof value === "object") {
      return value as Record<string, unknown>;
    }
  }
  return {};
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => stringValue(item)).filter((item): item is string => Boolean(item));
}

function messageFromPayload(payload: unknown, status: number): string {
  const record = asRecord(payload);
  const detail = asRecord(record.detail);
  const reasonCode = stringValue(record.reason_code) ?? stringValue(detail.reason_code);
  const blockedReasons = Array.isArray(record.blocked_reasons)
    ? record.blocked_reasons
        .map((reason) => {
          const reasonRecord = asRecord(reason);
          const code = stringValue(reasonRecord.reason_code);
          const path = stringValue(reasonRecord.path);
          return code ? `${path ?? "*"}:${code}` : "";
        })
        .filter(Boolean)
    : [];
  const saferNextAction = stringValue(asRecord(record.self_correction).safer_next_action);
  if (blockedReasons.length > 0) {
    return [
      `Preview blocked: ${blockedReasons.join(", ")}.`,
      saferNextAction ? `Next: ${saferNextAction}` : "No files changed.",
    ].join(" ");
  }
  if (reasonCode === "coder_packet_missing_context") {
    return "Preview blocked: Source Proxy needs more codebase context before it can produce a safe diff. No files changed.";
  }
  if (reasonCode === "coder_replacement_content_validation_failed") {
    return "Preview blocked: Coder returned replacement content that failed backend diff validation. No files changed.";
  }
  if (reasonCode === "coder_no_changes_needed" || record.already_satisfied === true || record.alreadySatisfied === true) {
    return "Already satisfied: target already contains the requested change. No files changed.";
  }
  return (
    stringValue(record.message) ??
    stringValue(record.error) ??
    stringValue(record.reason_code) ??
    stringValue(detail.error) ??
    stringValue(detail.reason_code) ??
    stringValue(record.status) ??
    `Preview request returned status ${status}.`
  );
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

function alreadySatisfiedFromPayload(payload: unknown): boolean {
  const record = asRecord(payload);
  return (
    record.already_satisfied === true ||
    record.alreadySatisfied === true ||
    stringValue(record.reason_code) === "coder_no_changes_needed"
  );
}

function designProposalIntakeFromPayload(payload: unknown): DesignProposalIntakeDisplay | null {
  const record = asRecord(payload);
  const intake = firstRecord(record.design_proposal_intake, record.designProposalIntake);
  if (Object.keys(intake).length === 0) {
    return null;
  }
  return {
    applyAuthority: booleanValue(intake.apply_authority ?? intake.applyAuthority),
    approvalAuthority: booleanValue(intake.approval_authority ?? intake.approvalAuthority),
    blockedBy: stringArrayValue(intake.blocked_by ?? intake.blockedBy),
    formatted: stringValue(intake.formatted) ?? "",
    packetReady: booleanValue(
      record.design_proposal_packet_ready ??
        record.designProposalPacketReady ??
        intake.packet_ready_for_source_proxy ??
        intake.packetReadyForSourceProxy,
    ),
    reasonCodes: stringArrayValue(intake.reason_codes ?? intake.reasonCodes),
    status: stringValue(intake.status) ?? stringValue(record.status) ?? "not reported",
  };
}

function authorityFlagText(label: string, value: boolean | null): string {
  if (value === null) {
    return `${label}: not reported`;
  }
  return `${label}: ${value ? "true" : "false"}`;
}

function reasonTaxonomyFromRaw(rawReason: string): {
  code: TrialReasonCode;
  explanation: string;
  nextAction: string;
} {
  const normalized = rawReason.trim().toLowerCase();
  let code: TrialReasonCode = "unknown_blocker";
  if (!normalized) {
    code = "unknown_blocker";
  } else if (normalized.includes("protected_path")) {
    code = "protected_path";
  } else if (normalized.includes("replacement_content_invalid")) {
    code = "replacement_content_invalid";
  } else if (normalized.includes("replacement content") && normalized.includes("failed backend diff validation")) {
    code = "replacement_content_invalid";
  } else if (normalized.includes("coder_replacement_content_validation_failed")) {
    code = "replacement_content_invalid";
  } else if (normalized.includes("diff_validation_failed") || normalized.includes("backend diff validation")) {
    code = "diff_validation_failed";
  } else if (normalized.includes("requirement_coverage_failed")) {
    code = "requirement_coverage_failed";
  } else if (normalized.includes("already_satisfied_noop_route_gap")) {
    code = "already_satisfied_noop_route_gap";
  } else if (normalized.includes("allowed") && normalized.includes("mismatch")) {
    code = "allowed_files_mismatch";
  } else if (normalized.includes("already satisfied") || normalized.includes("already_satisfied") || normalized.includes("coder_no_changes_needed")) {
    code = "already_satisfied";
  } else if (normalized.includes("scope_too_broad") || normalized.includes("scope too broad")) {
    code = "scope_too_broad";
  } else if (normalized.includes("target_unresolved") || normalized.includes("target_missing")) {
    code = "target_unresolved";
  } else if (normalized.includes("frontend_preview_route_gap")) {
    code = "frontend_preview_route_gap";
  } else if (normalized.includes("productive_preview_route_gap")) {
    code = "productive_preview_route_gap";
  } else if (normalized.includes("no_diff_route_gap")) {
    code = "no_diff_route_gap";
  } else if (normalized.includes("missing_target_context")) {
    code = "missing_target_context";
  } else if (normalized.includes("backend_diff_generation_gap")) {
    code = "backend_diff_generation_gap";
  } else if (normalized.includes("coder_response_repair_exhausted")) {
    code = "backend_diff_generation_gap";
  } else if (normalized === "blocked_after_retries" || normalized.includes("blocked_after_retries")) {
    code = "blocked_after_retries";
  }

  const copy: Record<TrialReasonCode, { explanation: string; nextAction: string }> = {
    protected_path: {
      explanation: "The requested target is protected and must stay blocked.",
      nextAction:
        "Keep this blocked. Do not edit protected paths. If this was expected, label it as pass_blocked_safely.",
    },
    allowed_files_mismatch: {
      explanation: "The proposed or requested file is outside the declared allowed_files boundary.",
      nextAction: "Keep blocked unless allowed_files includes the target. Improve audit copy if needed.",
    },
    requirement_coverage_failed: {
      explanation: "The proposed patch did not cover the required task details.",
      nextAction:
        "Regenerate or repair the patch so it includes the missing exact requirements, then keep safety gates unchanged.",
    },
    diff_validation_failed: {
      explanation: "The backend rejected the generated diff during validation.",
      nextAction:
        "Fix coder replacement-content to backend diff conversion or improve generated patch format. Preserve safety.",
    },
    replacement_content_invalid: {
      explanation: "Coder replacement content could not be converted into a valid backend diff.",
      nextAction:
        "Fix coder replacement-content to backend diff conversion or improve generated patch format. Preserve safety.",
    },
    already_satisfied: {
      explanation: "The target already contains the requested change, so no diff is needed.",
      nextAction: "No code change needed. Record as no-op proof.",
    },
    already_satisfied_noop_route_gap: {
      explanation:
        "The no-op/shared-bank prompt reached the preview route, but no already-satisfied result or specific blocker came back.",
      nextAction:
        "Improve already-satisfied detection or no-op diagnostics for shared-bank docs prompts, then rerun the 25-preview stage.",
    },
    scope_too_broad: {
      explanation: "The request is too broad to produce one bounded preview diff.",
      nextAction: "Narrow the prompt to one target file and one concrete change before previewing again.",
    },
    target_unresolved: {
      explanation: "The system could not resolve a specific target file.",
      nextAction: "Clarify the target_file and allowed_files, then rerun preview.",
    },
    frontend_preview_route_gap: {
      explanation:
        "The frontend/UI trial reached the preview route, but no diff or recognized blocker came back.",
      nextAction:
        "Improve the prompt-packet or UI-copy preview fallback for frontend targets, then rerun the 10-preview stage.",
    },
    productive_preview_route_gap: {
      explanation:
        "A productive-preview trial reached the preview route, but no diff or specific blocker came back.",
      nextAction:
        "Inspect prompt-packet fallback diagnostics for this docs/test/metadata target, then rerun staged browser evidence.",
    },
    no_diff_route_gap: {
      explanation:
        "A docs productive-preview prompt reached the route, but no diff or no-op proof came back.",
      nextAction:
        "Inspect docs prompt-packet fallback and no-diff diagnostics before rerunning staged browser evidence.",
    },
    missing_target_context: {
      explanation:
        "A test productive-preview prompt likely needs more target context before a bounded diff can be generated.",
      nextAction:
        "Improve test-target context diagnostics or prompt-packet context requests before rerunning staged browser evidence.",
    },
    backend_diff_generation_gap: {
      explanation:
        "A metadata productive-preview prompt reached the route, but backend diff generation did not produce a usable patch or specific blocker.",
      nextAction:
        "Inspect metadata diff generation fallback and copied diagnostics before rerunning staged browser evidence.",
    },
    blocked_after_retries: {
      explanation: "The backend exhausted retries without a more specific blocker.",
      nextAction:
        "Improve diagnostics so this blocker becomes specific, or adjust the prompt/target inference if it should produce a preview diff.",
    },
    unknown_blocker: {
      explanation: "The blocker did not include a recognized reason.",
      nextAction: "Improve backend diagnostics or copy the raw reason into a follow-up debugging prompt.",
    },
  };
  return { code, ...copy[code] };
}

function specificTrialBlockerReason(trial: ProxyTrialPrompt, rawReason: string) {
  const normalized = rawReason.trim().toLowerCase();
  const isGenericUnknown =
    !normalized ||
    ["blocked", "unknown_blocker", "preview_ready"].includes(normalized) ||
    normalized.includes("unknown");
  const isGenericRetryBlocker =
    normalized === "blocked_after_retries" ||
    normalized.includes("blocked_after_retries") ||
    normalized.includes("exhausted retries");
  if (isGenericRetryBlocker) {
    if (trial.category === "safe_blocker" && !trial.allowedFiles.includes(trial.targetFile)) {
      return [
        "Preview blocked: allowed_files_mismatch.",
        `${trial.id} asks for ${trial.targetFile}, but allowed_files only includes ${trial.allowedFiles.join(", ")}.`,
        "Next: keep blocked unless the operator narrows or changes allowed_files.",
        "No files changed.",
      ].join(" ");
    }
    if (trial.category === "safe_blocker") {
      return [
        "Preview blocked: scope_too_broad.",
        `${trial.id} is a broad or multi-file request that must stay bounded to ${trial.allowedFiles.join(", ")}.`,
        "Next: narrow the prompt to one allowed target or keep it blocked.",
        "No files changed.",
      ].join(" ");
    }
    if (trial.category === "generic_blocker_regression" && trial.targetFile.includes("not-real")) {
      return [
        "Preview blocked: target_unresolved.",
        `${trial.id} points at ${trial.targetFile}, which the browser preview route could not resolve safely.`,
        "Next: clarify the target file before previewing again.",
        "No files changed.",
      ].join(" ");
    }
    if (trial.category === "generic_blocker_regression") {
      return [
        "Preview blocked: scope_too_broad.",
        `${trial.id} is underspecified and did not provide enough bounded intent for a safe preview diff.`,
        "Next: ask for one concrete target-file change before previewing again.",
        "No files changed.",
      ].join(" ");
    }
    if (trial.category === "docs_only_productive_preview") {
      return [
        "Preview blocked: no_diff_route_gap.",
        `${trial.id} targets ${trial.targetFile}, but the docs productive-preview route exhausted retries without a diff or no-op proof.`,
        "Next: inspect docs prompt-packet fallback and no-diff diagnostics.",
        "No files changed.",
      ].join(" ");
    }
    if (trial.category === "test_productive_preview") {
      return [
        "Preview blocked: missing_target_context.",
        `${trial.id} targets ${trial.targetFile}, but the test productive-preview route needs more target context before it can produce a bounded diff.`,
        "Next: improve test-target context diagnostics or request bounded test context.",
        "No files changed.",
      ].join(" ");
    }
    if (trial.category === "metadata_productive_preview") {
      return [
        "Preview blocked: backend_diff_generation_gap.",
        `${trial.id} targets ${trial.targetFile}, but metadata diff generation did not return a usable patch or specific blocker.`,
        "Next: inspect metadata diff generation fallback diagnostics.",
        "No files changed.",
      ].join(" ");
    }
  }
  if (trial.category === "already_satisfied_noop" && isGenericUnknown) {
    return [
      "Preview blocked: already_satisfied_noop_route_gap.",
      `${trial.id} is a shared-bank no-op prompt for ${trial.targetFile}, but the browser preview route returned no already-satisfied result and no recognized blocker.`,
      "Next: improve already-satisfied/no-op diagnostics before promoting to 100 previews.",
      "No files changed.",
    ].join(" ");
  }
  if (trial.category === "replacement_content_invalid" && isGenericUnknown) {
    return [
      "Preview blocked: replacement_content_invalid.",
      `${trial.id} is a shared-bank replacement-content validation prompt for ${trial.targetFile}, but the browser preview route returned no recognized validation blocker.`,
      "Next: improve replacement-content validation diagnostics before promoting Phase 7.",
      "No files changed.",
    ].join(" ");
  }
  if (
    trial.category === "generic_blocker_regression" &&
    trial.targetFile.includes("not-real") &&
    isGenericUnknown
  ) {
    return [
      "Preview blocked: target_unresolved.",
      `${trial.id} points at ${trial.targetFile}, but the browser preview route returned no recognized target-unresolved blocker.`,
      "Next: clarify the target file before previewing again.",
      "No files changed.",
    ].join(" ");
  }
  const isFrontendWidgetTrial =
    trial.category === "frontend_productive_preview" &&
    trial.targetFile === "src/components/coding/CodingCommandCenterShell.tsx";
  if (!isFrontendWidgetTrial) {
    return rawReason;
  }
  if (
    normalized &&
    !isGenericUnknown
  ) {
    return rawReason;
  }
  return [
    "Preview blocked: frontend_preview_route_gap.",
    `${trial.id} targets src/components/coding/CodingCommandCenterShell.tsx, but the browser preview route returned no productive diff and no recognized blocker.`,
    "Next: improve frontend UI-copy preview diagnostics or fallback before promoting to 25 previews.",
    "No files changed.",
  ].join(" ");
}

function reviewedStateForEvidence({
  approvedAt,
  diffPresent,
  humanReviewResult,
  status,
}: {
  approvedAt: string | null;
  diffPresent: boolean;
  humanReviewResult?: string;
  status: string;
}) {
  if (humanReviewResult) return humanReviewResult;
  if (status === "already_satisfied") return "not_reviewed_yet";
  if (status === "blocked" || status === "error" || status === "failed") return "not_reviewed_yet";
  if (diffPresent && approvedAt) return "reviewed_preview_diff";
  return "not_reviewed_yet";
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

function targetFromPayloadOrDiff(payload: unknown, diff: string): string {
  const record = asRecord(payload);
  const target = stringValue(record.target) ?? stringValue(asRecord(record.resolved_target).path);
  if (target) {
    return target;
  }
  const plusLine = diff
    .split(/\r?\n/)
    .find((line) => line.startsWith("+++ b/") && line.length > "+++ b/".length);
  return plusLine ? plusLine.slice("+++ b/".length).trim() : "";
}

function deriveTaskPacket(taskText: string) {
  const trimmed = taskText.trim();
  const scopeDraft = derivePlainEnglishScopeDraft(trimmed);
  const targetFile = scopeDraft.targetFiles[0] ?? "";
  const allowedFiles = scopeDraft.allowedFiles;
  const blockedFields: string[] = [];
  if (!trimmed) {
    blockedFields.push("task text");
  }
  if (scopeDraft.reasonCodes.includes("target_unresolved")) {
    blockedFields.push("target file");
  }
  if (
    scopeDraft.reasonCodes.includes("target_unresolved") ||
    scopeDraft.reasonCodes.includes("multiple_targets") ||
    scopeDraft.reasonCodes.includes("target_missing")
  ) {
    blockedFields.push("allowed files");
  }
  if (scopeDraft.reasonCodes.includes("protected_path")) {
    blockedFields.push("safe target");
  }
  return {
    allowedFiles,
    blockedFields,
    expectedChecks: scopeDraft.expectedChecks,
    inspectionSummary: scopeDraft.inspectionSummary,
    reasonCodes: scopeDraft.reasonCodes,
    riskTier: scopeDraft.riskTier,
    rollbackHint: scopeDraft.rollbackHint,
    safeNextAction: scopeDraft.safeNextAction,
    scopeStatus: scopeDraft.status,
    summary: trimmed ? trimmed.split(/\s+/).slice(0, 18).join(" ") : "No coding task drafted",
    targetFile,
    taskType: scopeDraft.taskType,
    title: targetFile ? `Patch ${targetFile}` : "Local coding task",
  };
}

function receiptValue(value: string | null | undefined, fallback = "not run yet") {
  return value && value.trim() ? value : fallback;
}

function formatSessionLogTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function copySelectedText(text: string): boolean {
  if (typeof document === "undefined" || typeof document.execCommand !== "function") {
    return false;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.top = "0";
  textarea.style.left = "0";
  textarea.style.width = "1px";
  textarea.style.height = "1px";
  textarea.style.opacity = "0";
  textarea.style.fontSize = "16px";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  textarea.setSelectionRange(0, textarea.value.length);
  try {
    return document.execCommand("copy");
  } catch {
    return false;
  } finally {
    document.body.removeChild(textarea);
  }
}

async function writeClipboardText(text: string): Promise<boolean> {
  if (copySelectedText(text)) {
    return true;
  }
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

function changedFilesFromPayload(payload: unknown): string[] {
  const record = asRecord(payload);
  const execution = asRecord(record.execution);
  const verification = firstRecord(
    execution.post_apply_verification,
    record.post_apply_verification,
    asRecord(record.task).post_apply_verification,
  );
  const candidates = [execution.changed_files, verification.changed_files];
  for (const candidate of candidates) {
    if (!Array.isArray(candidate)) continue;
    const paths = candidate
      .map((item) => {
        if (typeof item === "string") return item;
        return stringValue(asRecord(item).path) ?? "";
      })
      .filter(Boolean);
    if (paths.length > 0) return paths;
  }
  return [];
}

function rollbackHintFromPayload(payload: unknown): string {
  const record = asRecord(payload);
  const execution = asRecord(record.execution);
  const audit = asRecord(execution.audit);
  return (
    stringValue(execution.rollback_hint) ??
    stringValue(audit.rollback_hint) ??
    "keep the task bounded; use git diff before any apply."
  );
}

function verificationFromPayload(payload: unknown): Record<string, unknown> {
  const record = asRecord(payload);
  const execution = asRecord(record.execution);
  return firstRecord(
    record.post_apply_verification,
    execution.post_apply_verification,
    asRecord(record.task).post_apply_verification,
  );
}

function commandsRunFromPayload(payload: unknown, fallback: string): string {
  const verification = verificationFromPayload(payload);
  const checks = Array.isArray(verification.checks) ? verification.checks : [];
  const commandTexts = checks
    .map((check) => {
      const record = asRecord(check);
      const commandText = stringValue(record.command_text);
      if (commandText) return commandText;
      const command = record.command;
      return Array.isArray(command) ? command.map(String).join(" ") : "";
    })
    .filter(Boolean);
  if (commandTexts.length > 0) {
    return commandTexts.join("; ");
  }
  if (verification.docs_only === true) {
    return "none; docs-only confirmations recorded";
  }
  return fallback;
}

function resultLabelFromCheck(check: Record<string, unknown>): string {
  const status =
    stringValue(check.status) ??
    stringValue(check.result) ??
    stringValue(check.outcome) ??
    stringValue(check.state);
  if (!status) return "";
  if (["pass", "passed", "success", "ok"].includes(status.toLowerCase())) return "pass";
  if (["fail", "failed", "error"].includes(status.toLowerCase())) return "fail";
  return status;
}

function checkResultFromPayload(payload: unknown, matcher: RegExp, fallback: string): string {
  const verification = verificationFromPayload(payload);
  const checks = Array.isArray(verification.checks) ? verification.checks : [];
  for (const check of checks) {
    const record = asRecord(check);
    const commandText =
      stringValue(record.command_text) ??
      (Array.isArray(record.command) ? record.command.map(String).join(" ") : "");
    const label = stringValue(record.name) ?? stringValue(record.label) ?? commandText;
    if (!matcher.test(`${label} ${commandText}`)) continue;
    const result = resultLabelFromCheck(record);
    return result ? result : "reported";
  }
  if (verification.docs_only === true) {
    return "not required for docs-only verification";
  }
  return fallback;
}

function passFailFromPayload(payload: unknown, responseOk: boolean, fallback: string): string {
  const verification = verificationFromPayload(payload);
  const status = stringValue(verification.status);
  if (status === "verified") return "pass";
  if (status === "verification_failed") return "fail";
  if (responseOk && status === "verification_ready") return "pending verification";
  return responseOk ? fallback : "fail";
}

function emptyTaskPacketText(activeDraftText: string) {
  return activeDraftText.trim()
    ? "Draft not submitted yet. Click Submit task to stage the packet."
    : "No task yet. Paste the copy-paste task, then click Submit task.";
}

function taskPacketFromTrial(taskText: string, trial?: ProxyTrialPrompt | null) {
  const inferred = deriveTaskPacket(taskText);
  if (!trial || taskText.trim() !== trial.taskPrompt.trim()) {
    return inferred;
  }
  return {
    ...inferred,
    allowedFiles: trial.allowedFiles,
    blockedFields: taskText.trim() ? [] : ["task text"],
    expectedChecks: trial.targetFile.startsWith("docs/")
      ? ["git diff --check"]
      : inferred.expectedChecks,
    inspectionSummary: `Trial ${trial.id}: explicit target ${trial.targetFile}; allowed files ${trial.allowedFiles.join(", ")}.`,
    reasonCodes: [],
    riskTier: trial.difficulty === "mid" ? "medium" : inferred.riskTier,
    rollbackHint:
      trial.allowedFiles.length > 0
        ? `git restore ${trial.allowedFiles.join(" ")}`
        : inferred.rollbackHint,
    scopeStatus: taskText.trim() ? "ready" : inferred.scopeStatus,
    summary: trial.taskPrompt.split(/\s+/).slice(0, 18).join(" "),
    targetFile: trial.targetFile,
    title: `Trial ${trial.id}: ${trial.title}`,
  };
}

function expectedOutputText(trial: ProxyTrialPrompt) {
  return [
    `Trial: ${trial.id} ${trial.title}`,
    `Expected result: ${trial.expectedResult}`,
    `Expected changed_files: ${
      trial.expectedChangedFiles.length ? trial.expectedChangedFiles.join(", ") : "none"
    }`,
    `Expected UI: ${trial.expectedUiResult}`,
    `Expected backend: ${trial.expectedBackendResult}`,
    `Expected diff: ${trial.expectedDiffBehavior}`,
    `Stop: ${trial.stopCondition}`,
    `Forbidden: ${trial.forbiddenActions.join(", ")}`,
  ].join("\n");
}

export default function CodingCommandCenterShell() {
  const [chats, setChats] = useState<ShellChat[]>(initialShellChats);
  const [activeChatId, setActiveChatId] = useState(initialShellChats[0].id);
  const [persistenceStatus, setPersistenceStatus] = useState("Local session only");
  const [previewDiffCopyStatus, setPreviewDiffCopyStatus] = useState("");
  const [receiptCopyStatus, setReceiptCopyStatus] = useState("");
  const [trialPromptCopyStatus, setTrialPromptCopyStatus] = useState("");
  const [trialWidgetEnabled, setTrialWidgetEnabled] = useState(true);
  const [proxyDiagnosticOpen, setProxyDiagnosticOpen] = useState(false);
  const [trialSearch, setTrialSearch] = useState("");
  const [selectedTrialId, setSelectedTrialId] = useState(DEFAULT_PROXY_TRIAL_ID);
  const [sessionLogs, setSessionLogs] = useState<SessionLogEntry[]>([]);
  const [trialBatchStatus, setTrialBatchStatus] = useState<TrialBatchStatus>("idle");
  const [trialBatchProgress, setTrialBatchProgress] = useState<TrialBatchProgress | null>(null);
  const [trialBatchSummary, setTrialBatchSummary] = useState("");
  const [activeDrawerShell, setActiveDrawerShell] = useState<DrawerShellId | null>(null);
  const [progressStartedAtMs, setProgressStartedAtMs] = useState<number | null>(null);
  const [progressNowMs, setProgressNowMs] = useState(() => Date.now());
  const [usageNowMs, setUsageNowMs] = useState(() => Date.now());
  const chatOpenedAtMsRef = useRef(Date.now());
  const directButtonActionAtRef = useRef(0);
  const drawerShellHeadingRef = useRef<HTMLHeadingElement | null>(null);
  const restoredTaskStoryRef = useRef(false);
  const providerStatuses = useMemo(() => getCodingProviderStatuses(), []);
  const providerModelOptions = useMemo(() => getCodingProviderModelOptions(), []);
  const localProvider = providerStatuses.find((provider) => provider.id === "local");
  const cloudProvider = providerStatuses.find((provider) => provider.id === "cloud");

  const activeChat = useMemo(
    () => chats.find((chat) => chat.id === activeChatId) ?? chats[0],
    [activeChatId, chats],
  );
  const activeWorkspaceContext = codingWorkspaceContextById(activeChat?.workspaceContextId);
  const folderProofRows = workspaceFolderProofRows();
  const workspaceReceiptText = workspaceReceiptLines(activeWorkspaceContext).join("\n");
  const contextChips = [
    { label: activeWorkspaceContext.label, tone: "repo" },
    {
      label: localProvider ? `${localProvider.label} default` : "Local LLM default",
      tone: "local",
    },
    {
      label:
        cloudProvider?.status === "configured"
          ? `${cloudProvider.label} configured`
          : `${cloudProvider?.label ?? "GPT/cloud"} unavailable`,
      tone: "cloud",
    },
    { label: "Safety locked", tone: "local" },
    { label: `Dirty tree: ${activeWorkspaceContext.dirtyState}`, tone: "repo" },
  ];
  const drawerShellCopy: Record<DrawerShellId, { label: string; title: string; body: string }> = {
    diagnostics: {
      label: "Diagnostics",
      title: "Diagnostics Drawer Shell",
      body:
        "Trial prompts, proof controls, blocker summaries, and PR-8.3 diagnostics are available when this drawer is open. Diagnostic controls remain preview/manual proof only and add no provider, queue, worker, apply, commit, or push authority.",
    },
    evidence: {
      label: "Evidence",
      title: "Evidence Drawer Shell",
      body:
        "Task-scoped receipts, timeline detail, dirty-tree proof, rollback notes, and copyable evidence are available when this drawer is open. No receipt store, file write, apply, commit, or push authority is added.",
    },
    settings: {
      label: "Settings",
      title: "Settings Drawer Shell",
      body:
        "Empty shell for provider, model, workspace, backend truth, usage, and display-only configuration detail. GPT/cloud stays unavailable unless real config exists, and no provider call runs here.",
    },
  };
  const activeDrawerShellCopy = activeDrawerShell ? drawerShellCopy[activeDrawerShell] : null;
  const activeChatTitle = activeChat?.title ?? "New coding chat";
  const activeChatMeta = activeChat?.meta ?? "Ready";
  const activeChatEmptyState = activeChat?.emptyState ?? "No coding task drafted";
  const activeProviderId = activeChat?.providerId ?? "local";
  const activeProviderModel = codingProviderModelOptionById(
    activeChat?.providerModelId ?? defaultModelIdForProvider(activeProviderId),
    providerModelOptions,
  );
  const activeProviderStatus =
    providerStatuses.find((provider) => provider.id === activeProviderModel.providerId) ??
    providerStatuses[0];
  const providerModelReceiptText = providerModelReceiptLines({
    model: activeProviderModel,
    provider: activeProviderStatus,
  }).join("\n");
  const backendTruthRows = useMemo(
    () =>
      buildBackendTruthRows({
        model: activeProviderModel,
        provider: activeProviderStatus,
      }),
    [activeProviderModel, activeProviderStatus],
  );
  const backendTruthReceiptText = backendTruthReceiptLines(backendTruthRows).join("\n");
  const settingsRows = useMemo(
    () =>
      buildCodingSettingsRows({
        model: activeProviderModel,
        provider: activeProviderStatus,
        workspace: activeWorkspaceContext,
      }),
    [activeProviderModel, activeProviderStatus, activeWorkspaceContext],
  );
  const settingsReceiptText = settingsReceiptLines(settingsRows).join("\n");
  const providerPreviewBlockedReason = activeProviderModel.previewAvailable
    ? ""
    : `Preview blocked: selected provider/model ${activeProviderModel.modelLabel} is ${activeProviderModel.status}. ${activeProviderModel.blockedReason} No provider call ran.`;
  const codingModeActive = activeChat?.codingMode === true;
  const activeDraftText = activeChat?.draftText ?? "";
  const selectedTrial =
    PROXY_TRIAL_PROMPTS.find((trial) => trial.id === selectedTrialId) ?? PROXY_TRIAL_PROMPTS[0];
  const loadedTrial = PROXY_TRIAL_PROMPTS.find(
    (trial) => trial.taskPrompt.trim() === activeDraftText.trim(),
  );
  const taskPacket = useMemo(
    () => taskPacketFromTrial(activeDraftText, loadedTrial),
    [activeDraftText, loadedTrial],
  );
  const filteredTrials = useMemo(() => {
    const needle = trialSearch.trim().toLowerCase();
    if (!needle) {
      return PROXY_TRIAL_PROMPTS;
    }
    return PROXY_TRIAL_PROMPTS.filter((trial) =>
      `${trial.id} ${trial.title} ${trial.family} ${trial.targetFile} ${trial.taskPrompt}`
        .toLowerCase()
        .includes(needle),
    );
  }, [trialSearch]);
  const activeProposedDiff = activeChat?.proposedDiff ?? "";
  const activePreviewTarget = activeChat?.previewTarget ?? "";
  const activeTaskId = activeChat?.taskId ?? "";
  const activeTaskSubmitted = activeChat?.taskSubmitted === true;
  const activeBlockedFields = taskPacket.blockedFields;
  const activeChangedFiles = activeChat?.changedFiles ?? [];
  const activeDesignProposalIntake = activeChat?.designProposalIntake ?? null;
  const approvedAt = activeChat?.approvedAt ?? null;
  const appliedAt = activeChat?.appliedAt ?? null;
  const applyMessage = activeChat?.applyMessage ?? "";
  const isApplying = activeChat?.isApplying === true;
  const isVerifying = activeChat?.isVerifying === true;
  const previewStatus = activeChat?.previewStatus ?? "idle";
  const previewMessage = activeChat?.previewMessage ?? "Preview not requested.";
  const verificationMessage = activeChat?.verificationMessage ?? "Verification has not started.";
  const verificationStatus = activeChat?.verificationStatus ?? "not_started";
  const verifiedAt = activeChat?.verifiedAt ?? null;
  const previewAlreadySatisfied = previewMessage.startsWith("Already satisfied:");
  const noApplyPreviewTrial =
    /human browser productive preview trial only passes/i.test(activeDraftText) &&
    /do not apply,\s*commit,\s*or push/i.test(activeDraftText);
  const providerIntent = describeCodingProviderIntent(activeProviderStatus.id, providerStatuses);
  const reviewOnlyPreview = previewStatus === "ready" && Boolean(activeProposedDiff) && !activeTaskId;
  const canClearActiveTask = Boolean(
    activeDraftText.trim() ||
      activeTaskSubmitted ||
      activeProposedDiff ||
      activeChangedFiles.length > 0 ||
      previewStatus !== "idle" ||
      activePreviewTarget ||
      approvedAt ||
      appliedAt ||
      verificationStatus !== "not_started",
  );
  const canRequestPreview =
    codingModeActive &&
    activeDraftText.trim().length > 0 &&
    taskPacket.blockedFields.length === 0 &&
    activeProviderModel.previewAvailable;
  const selectedTrialPacket = taskPacketFromTrial(selectedTrial.taskPrompt, selectedTrial);
  const sharedBankTrialCount = PROXY_TRIAL_PROMPTS.length;
  const sharedBankGeneratedCount = PROXY_TRIAL_PROMPTS.filter(
    (trial) => trial.bankSource === "shared_prompt_bank",
  ).length;
  const canRunSelectedTrialPreview =
    Boolean(
      selectedTrial.taskPrompt.trim() &&
        selectedTrialPacket.targetFile &&
        selectedTrialPacket.allowedFiles.length > 0,
    ) && previewStatus !== "loading";
  const canRunAllTrialPreviews = trialBatchStatus !== "running" && previewStatus !== "loading";
  const trialBatchRunning = trialBatchStatus === "running";
  const trialBatchComplete = trialBatchStatus === "complete";
  const activeRunState: ActiveRunState =
    trialBatchStatus !== "idle"
      ? trialBatchStatus
      : previewStatus === "loading"
        ? "running"
        : previewStatus === "blocked"
          ? "blocked"
          : previewStatus === "error"
            ? "failed"
            : previewAlreadySatisfied || previewStatus === "ready" || verificationStatus === "passed"
              ? "complete"
              : activeTaskSubmitted || activeDraftText.trim()
                ? "queued"
                : "idle";
  const activeRunStateLabel = activeRunState;
  const activeRunStateDetail: Record<ActiveRunState, string> = {
    idle: "No local diagnostic or task preview is active.",
    queued: "Local task or diagnostic is staged for preview; no hidden worker or provider is running.",
    running: "UI-local preview lifecycle is running; no backend stream is claimed.",
    blocked: "Preview is blocked safely; no apply authority is granted.",
    complete: "Current preview lifecycle has completed; receipts remain copy-only.",
    failed: "Preview lifecycle stopped on a failure; no retry or mutation authority is granted.",
  };
  const progressTimerActive = activeRunState === "queued" || activeRunState === "running";
  const diagnosticLifecycleLabels = [
    "Idle",
    "Queued",
    "Preparing diagnostic packet",
    "Creating preview task",
    "Requesting bounded diff proposal",
    "Checking diff safety gates",
    "Recording receipt",
    "Complete",
    "Blocked",
    "Failed",
  ];
  const currentDiagnosticLifecycleLabel =
    activeRunState === "failed"
      ? "Failed"
      : activeRunState === "blocked"
        ? "Blocked"
        : activeRunState === "complete"
          ? "Complete"
          : activeRunState === "running"
            ? trialBatchProgress?.stageLabel ?? "Queued"
            : activeRunState === "queued"
              ? "Queued"
              : "Idle";
  const currentDiagnosticLifecycleIndex = Math.max(
    0,
    diagnosticLifecycleLabels.indexOf(currentDiagnosticLifecycleLabel),
  );
  const diagnosticLifecycleTimeline = diagnosticLifecycleLabels.map((label, index) => {
    let status: "waiting" | "active" | "complete" | "blocked" | "failed" = "waiting";
    if (activeRunState === "idle") {
      status = label === "Idle" ? "active" : "waiting";
    } else if (label === "Blocked" && activeRunState === "blocked") {
      status = "blocked";
    } else if (label === "Failed" && activeRunState === "failed") {
      status = "failed";
    } else if (label === "Complete" && activeRunState === "complete") {
      status = "complete";
    } else if (index < currentDiagnosticLifecycleIndex) {
      status = ["Blocked", "Failed"].includes(label) ? "waiting" : "complete";
    } else if (index === currentDiagnosticLifecycleIndex) {
      status = "active";
    }
    return {
      detail:
        label === "Idle"
          ? "No UI-local diagnostic has started."
          : label === "Queued"
            ? "The local diagnostic has been staged in the browser UI."
            : label === "Complete"
              ? "The local diagnostic summary is available when the run completes."
              : label === "Blocked"
                ? "A safe blocker can be shown without granting apply authority."
                : label === "Failed"
                  ? "A failure stops the lifecycle without retry or mutation authority."
                  : "Observable browser-side diagnostic stage; not a streamed backend event.",
      label,
      status,
    };
  });
  const trialBatchProgressNow = trialBatchProgress
    ? Math.max(0, Math.min(trialBatchProgress.currentStep, trialBatchProgress.totalSteps))
    : 0;
  const trialBatchProgressPercent = trialBatchProgress
    ? Math.max(
        0,
        Math.min(
          100,
          Math.round((trialBatchProgressNow / trialBatchProgress.totalSteps) * 100),
        ),
      )
    : 0;
  const trialBatchProgressFillClass = [
    "h-full rounded-full bg-emerald-300 shadow-[0_0_10px_rgba(110,231,183,0.45)]",
    "transition-[width] duration-300",
    trialBatchProgressNow > 0 ? "min-w-2" : "",
  ].join(" ");
  const trialBatchProgressTrialText = trialBatchProgress
    ? [
        `Trial ${trialBatchProgress.currentTrialIndex} of ${trialBatchProgress.totalTrials}:`,
        trialBatchProgress.currentTrialId,
        trialBatchProgress.currentTrialTitle,
      ].join(" ")
    : "Waiting for UI-local diagnostic position";
  const trialBatchProgressValueText = trialBatchProgress
    ? [
        `UI-local diagnostic progress: ${trialBatchProgress.stageLabel} for ${trialBatchProgress.currentTrialId},`,
        `trial ${trialBatchProgress.currentTrialIndex} of ${trialBatchProgress.totalTrials}.`,
        "No streamed backend progress source is available.",
      ].join(" ")
    : "No UI-local diagnostic progress has started. No streamed backend progress source is available.";
  const nextStagedTrial =
    PROXY_TRIAL_PROMPTS.find((trial) => trial.id !== selectedTrial.id) ?? selectedTrial;
  const blockerPreview = manualHundredTopBlockers[0];
  const stagedPromptPreviewItems: Array<{
    detail: string;
    id: string;
    status: StagedPromptPreviewStatus;
    title: string;
  }> = [
    {
      detail: "Selected prompt is the visible current item. It does not start automatically.",
      id: selectedTrial.id,
      status: "current",
      title: selectedTrial.title,
    },
    {
      detail: "Next prompt is staged for operator review only.",
      id: nextStagedTrial.id,
      status: "pending",
      title: nextStagedTrial.title,
    },
    {
      detail: `${manualHundredFrontendDiagnostic.terminalHundredStatus} is historical diagnostic evidence, not a hidden run.`,
      id: "terminal-100-reference",
      status: "completed",
      title: "Terminal 100 diagnostic reference",
    },
    {
      detail: `${blockerPreview.code}: ${blockerPreview.meaning}`,
      id: blockerPreview.code,
      status: "blocked",
      title: "Known safe blocker preview",
    },
  ];
  const currentSessionRunHistoryItems = [
    trialBatchSummary
      ? {
          at: trialBatchProgress ? `trial ${trialBatchProgress.currentTrialIndex}/${trialBatchProgress.totalTrials}` : "latest",
          detail: "Latest browser diagnostic summary is held in current component state only.",
          id: "latest-diagnostic-summary",
          status: activeRunState,
          title: "Latest diagnostic batch",
        }
      : null,
    ...sessionLogs.slice(0, 5).map((entry, index) => ({
      at: `${index + 1}. ${formatSessionLogTime(entry.at)}`,
      detail: "Current-session audit detail captured; open audit logs for the full packet.",
      id: entry.id,
      status: `history ${entry.status}`,
      title: `History: ${entry.title}`,
    })),
  ].filter(Boolean) as Array<{
    at: string;
    detail: string;
    id: string;
    status: string;
    title: string;
  }>;
  const codexLikeFunctionalityRows = [
    {
      detail: "Phase 7 live preview remains disabled; no live apply or route execution is available.",
      label: "Live preview work",
      state: "Gated",
    },
    {
      detail: "The shell can show selected trial context, but it does not start parallel prompts, workers, or background tasks.",
      label: "Multiple running prompts",
      state: "Not started",
    },
    {
      detail: trialBatchRunning
        ? "Showing UI-local stage and trial position only; no Source Proxy streamed backend percentage is claimed."
        : "Real streamed backend progress remains future gated work; exact percent is not faked.",
      label: "Progress/loading",
      state: trialBatchRunning ? "UI-local diagnostic progress" : "Stream gated",
    },
    {
      detail: trialBatchSummary
        ? "A current-session run summary is available in advanced controls; no durable history store was added."
        : "No current-session run summary is recorded; durable run history is still gated.",
      label: "Run history",
      state: trialBatchSummary ? "Session summary available" : "Display-only placeholder",
    },
    {
      detail: "The existing Copy diag action copies a concise packet only; it does not write backend evidence.",
      label: "Copyable diagnostics",
      state: "Available",
    },
    {
      detail: "Task queue previews are inert text only; no queue, worker, or background execution starts here.",
      label: "Task queue previews",
      state: "Gated",
    },
    {
      detail: activeTaskId
        ? "The receipt panel can describe the active task, but it does not approve apply, commit, or push."
        : "No active task receipt is ready; receipt improvements remain copy-only and non-authoritative.",
      label: "Preview receipts",
      state: activeTaskId ? "Receipt context available" : "No active receipt",
    },
  ];
  const changedFilesAreAllowed =
    activeChangedFiles.length > 0 &&
    activeChangedFiles.every((file) => taskPacket.allowedFiles.includes(file));
  const canRecordAuditLog =
    previewAlreadySatisfied ||
    previewStatus === "blocked" ||
    previewStatus === "error" ||
    (previewStatus === "ready" && (Boolean(approvedAt) || changedFilesAreAllowed));
  const canApprovePreview =
    previewStatus === "ready" &&
    Boolean(activeProposedDiff) &&
    Boolean(activePreviewTarget) &&
    changedFilesAreAllowed &&
    !noApplyPreviewTrial &&
    !approvedAt;
  const canMarkPreviewReviewed =
    previewStatus === "ready" &&
    Boolean(activeProposedDiff) &&
    Boolean(activePreviewTarget) &&
    changedFilesAreAllowed &&
    noApplyPreviewTrial &&
    !approvedAt;
  const canApplyApprovedDiff =
    Boolean(approvedAt) &&
    Boolean(activeProposedDiff) &&
    Boolean(activePreviewTarget) &&
    Boolean(activeTaskId) &&
    changedFilesAreAllowed &&
    !noApplyPreviewTrial &&
    !appliedAt &&
    !isApplying;
  const canRunVerification =
    Boolean(appliedAt) &&
    Boolean(activeTaskId) &&
    verificationStatus !== "passed" &&
    !isApplying &&
    !isVerifying;
  const previewBlockedReason =
    taskPacket.blockedFields.length > 0
      ? `Preview blocked: missing ${taskPacket.blockedFields.join(", ")}.${
          taskPacket.reasonCodes.includes("protected_path")
            ? ` Reason codes: ${taskPacket.reasonCodes.join(", ")}.`
            : ""
        }`
      : previewStatus === "blocked" || previewStatus === "error"
        ? previewMessage
        : providerPreviewBlockedReason
          ? providerPreviewBlockedReason
        : "";
  const approvalGateCopy =
    approvedAt
      ? activeTaskId
        ? "Approval gate display: human approval recorded; apply requires the approved route."
        : "Review gate display: preview marked reviewed; write actions are unavailable for this review-only preview."
      : previewAlreadySatisfied
        ? "Approval gate display: no approval needed because the target already contains the requested change."
      : previewStatus === "ready"
      ? activeTaskId
        ? noApplyPreviewTrial
          ? "Approval gate display: preview evidence ready for HB-01 review; approval is intentionally unavailable."
          : changedFilesAreAllowed
          ? "Approval gate display: clean preview evidence available; approval requires human click before apply."
          : "Approval gate display: locked because preview changed files are missing or outside allowed files."
        : "Review gate display: review-only preview evidence available; marking it reviewed cannot apply files."
      : previewStatus === "blocked" || previewStatus === "error"
        ? "Approval gate display: locked because preview is blocked."
        : previewStatus === "loading"
          ? "Approval gate display: waiting for preview evidence."
          : "Approval gate display: locked until preview runs.";
  const previewGateReason =
    previewAlreadySatisfied
      ? previewMessage
      : previewStatus === "blocked" || previewStatus === "error"
      ? previewBlockedReason || previewMessage
      : canRequestPreview
        ? "Ready for preview wiring. No files change during preview."
        : previewBlockedReason || "Locked until a submitted bounded task exists.";
  const gateReasons = {
    approval: reviewOnlyPreview
      ? approvedAt
        ? "Marked reviewed. This does not grant write authority."
        : "Preview evidence exists; you may mark it reviewed."
      : canApprovePreview
        ? "Clean preview evidence exists; explicit human approval is available."
        : canMarkPreviewReviewed
          ? "Preview evidence exists; mark human review without apply authority."
        : noApplyPreviewTrial && previewStatus === "ready"
          ? "Unavailable for HB-01; record preview evidence only."
        : approvedAt
          ? "Approved locally."
          : previewAlreadySatisfied
            ? "Unavailable; no approval needed for a no-op preview."
          : previewStatus === "ready" && Boolean(activeProposedDiff)
            ? "Locked until preview changed files are known and within allowed files."
            : "Locked until preview evidence exists.",
    apply: appliedAt
      ? "Apply evidence exists; repeat apply is locked."
      : canApplyApprovedDiff
        ? "Explicit local approval exists."
        : approvedAt
          ? activeTaskId
            ? changedFilesAreAllowed
              ? "Locked until an approved diff and target are present."
              : "Locked until preview changed files are known and within allowed files."
            : "Locked until a task-backed preview is available."
          : previewAlreadySatisfied
            ? "Unavailable; no file change is needed."
          : "Locked until explicit local approval exists.",
    preview: previewGateReason,
    verify:
      verificationStatus === "passed"
        ? "Verification passed."
        : previewAlreadySatisfied
          ? "Not needed; no file change is required."
        : verificationStatus === "running"
          ? "Verification request is running."
          : appliedAt
            ? "Apply evidence exists; verification is required."
            : "Locked until apply happens.",
  };
  const taskStateLabel = previewAlreadySatisfied
    ? "No-op complete"
    : appliedAt
    ? "Applied"
    : approvedAt
      ? "Approved"
      : previewStatus === "ready"
        ? "Preview ready"
        : activeDraftText.trim()
          ? "Draft"
          : "No active run";
  const trialDiagnosticVisible = trialBatchStatus !== "idle" || Boolean(trialBatchProgress);
  const trialDiagnosticStateLabel =
    trialBatchStatus === "running"
      ? "Trial diagnostic active"
      : trialBatchStatus === "queued"
        ? "Trial diagnostic queued"
        : trialBatchStatus === "complete"
          ? "Trial diagnostic complete"
          : trialBatchStatus === "failed"
            ? "Trial diagnostic failed safely"
            : trialBatchStatus === "blocked"
              ? "Trial diagnostic blocked safely"
              : taskStateLabel;
  const visibleTaskStateLabel = trialDiagnosticVisible
    ? trialDiagnosticStateLabel
    : taskStateLabel;
  const trialDiagnosticActivityText = trialBatchProgress
    ? `${trialBatchProgressTrialText} · ${trialBatchProgress.stageLabel}`
    : trialBatchSummary
      ? "Latest trial diagnostic summary is current-session only."
      : "No UI-local trial diagnostic is active.";
  const trialStatusBadgeLabel =
    previewStatus === "blocked" || previewStatus === "error"
      ? "Blocked safely"
      : previewStatus === "ready" && activeProposedDiff && !approvedAt
        ? "Needs review"
        : previewStatus === "ready" || previewAlreadySatisfied
          ? "Preview ready"
          : "Not run";
  const approvalReviewAction = `Review changed files ${activeChangedFiles.join(
    ", ",
  )} against allowed files ${taskPacket.allowedFiles.join(
    ", ",
  )}, then approve only if the diff text is correct.`;
  const changedFilesSummary =
    activeChangedFiles.length > 0 ? activeChangedFiles.join(", ") : "not known yet";
  const allowedFilesSummary =
    taskPacket.allowedFiles.length > 0 ? taskPacket.allowedFiles.join(", ") : "not declared";
  const approvalPreflightText =
    previewAlreadySatisfied
      ? "Approval preflight: target already satisfied; no changed files to approve."
      : previewStatus === "ready" && Boolean(activeProposedDiff)
      ? changedFilesAreAllowed
        ? `Approval preflight: changed files ${changedFilesSummary} match allowed files ${allowedFilesSummary}.`
        : "Approval preflight: preview changed files are missing or outside allowed files."
      : "Approval preflight: waiting for clean preview evidence.";
  const applyScopeText =
    previewAlreadySatisfied
      ? "Apply scope: unavailable; no file change is needed."
      : noApplyPreviewTrial && previewStatus === "ready"
        ? `Apply scope: unavailable for HB-01; preview scope is ${changedFilesSummary}.`
      : approvedAt && activeTaskId && changedFilesAreAllowed
      ? `Apply scope: approved route may write only ${changedFilesSummary}.`
      : changedFilesAreAllowed
        ? `Apply scope: locked until approval; preview scope is ${changedFilesSummary}.`
        : "Apply scope: locked until preview changed files match allowed files.";
  const safeNextAction =
    verificationStatus === "passed"
      ? "Verification passed. No commit or push is available here."
      : canRunVerification
        ? "Verify is now the next safe step."
        : canApplyApprovedDiff
        ? "Apply approved diff only if the reviewed docs-only change is still correct."
          : noApplyPreviewTrial && previewStatus === "ready"
            ? approvedAt
              ? "HB-01 preview reviewed. Record the receipt; do not apply, commit, or push."
              : "Mark HB-01 preview reviewed, then record the receipt. Do not apply, commit, or push."
          : canApprovePreview
            ? approvalReviewAction
            : previewAlreadySatisfied
              ? "No-op complete. Copy the receipt or start a different bounded task."
            : previewStatus === "blocked" || previewStatus === "error"
              ? previewBlockedReason || previewMessage
              : canRequestPreview
                ? "Run Preview safely to request diff evidence."
                : previewBlockedReason || "Submit a bounded task before preview.";
  const verificationStatusLabel = previewAlreadySatisfied
    ? "not needed"
    : verificationStatus === "required"
      ? "required"
      : verificationStatus.replace("_", " ");
  const verificationDisplayMessage = previewAlreadySatisfied
    ? "No verification needed; target already contains the requested change and no files changed."
    : verificationMessage;
  const currentTrialStep =
    verificationStatus === "passed"
      ? "Trial complete: receipt should show pass; do not commit or push from this lane."
      : canRunVerification
        ? "Current step: click Verify docs-only change. Expect Pass/fail to become pass."
        : canApplyApprovedDiff
        ? "Current step: click Apply approved diff only if the preview still shows one docs-only change."
          : noApplyPreviewTrial && previewStatus === "ready"
            ? approvedAt
              ? "Current step: preview reviewed. Record the diff, changed files, review result, and verification state. Do not apply, commit, or push."
              : "Current step: review the diff, then click Mark preview reviewed. Do not apply, commit, or push."
            : canApprovePreview
              ? "Current step: review the diff, then click Approve preview if it only touches the allowed docs file."
          : previewAlreadySatisfied
            ? "Trial complete: no-op evidence is ready. Copy the receipt or start a different bounded task."
          : previewStatus === "blocked" || previewStatus === "error"
            ? `Current step: stop and debug. ${previewBlockedReason || previewMessage}`
                : canRequestPreview
                  ? activeTaskSubmitted
                    ? "Current step: click Preview safely. Expect preview evidence and no file changes."
                    : "Current step: click Preview safely. A bounded draft will be staged before evidence is requested."
                  : activeTaskSubmitted
                    ? "Current step: fix missing bounded fields before preview."
                    : "Current step: paste the copy-paste task, click Coding mode, then Submit task.";
  const receiptTrialStep = currentTrialStep
    .replace(/^Current step: /, "")
    .replace(/^Trial complete: /, "Complete: ");
  const receiptChangedFilesText =
    activeChangedFiles.length > 0
      ? activeChangedFiles.join(", ")
      : previewAlreadySatisfied
        ? "none; target already satisfied"
        : "not known yet";
  const receiptBlockedReasonText = previewAlreadySatisfied
    ? "none; no-op preview"
    : previewBlockedReason || "none";
  const receiptCommandsRunText =
    verificationStatus === "running"
      ? "none; recording confirmations"
      : previewAlreadySatisfied
        ? "none; no-op preview"
        : activeChat?.receiptCommandsRun ?? "not run yet";
  const unexpectedFiles = activeChangedFiles.filter(
    (file) => !taskPacket.allowedFiles.includes(file),
  );
  const taskBoundaryStateText =
    activeBlockedFields.length > 0
      ? `Blocked: missing ${activeBlockedFields.join(", ")}.`
      : activeTaskSubmitted
        ? "Bounded task is staged."
        : "Draft is not staged yet.";
  const receiptTargetScopeText = taskPacket.targetFile
    ? `Only this file is targeted: ${taskPacket.targetFile}.`
    : "Target file is missing.";
  const receiptAllowedFilesText =
    taskPacket.allowedFiles.length === 1
      ? `Only this file is allowed: ${taskPacket.allowedFiles[0]}.`
      : taskPacket.allowedFiles.length > 1
        ? `Only these files are allowed: ${taskPacket.allowedFiles.join(", ")}.`
        : "Allowed files are missing.";
  const receiptUnexpectedFilesText =
    unexpectedFiles.length > 0
      ? `Unexpected files detected: ${unexpectedFiles.join(", ")}.`
      : activeChangedFiles.length > 0 || previewAlreadySatisfied
        ? "No unexpected files detected."
        : "Unexpected files not known yet.";
  const receiptDiffCheckText = previewAlreadySatisfied
    ? "not applicable; no diff needed"
    : previewStatus === "ready"
      ? unexpectedFiles.length === 0 && activeChangedFiles.length > 0
        ? "pass; changed files match allowed files"
        : "fail; changed files are missing or outside allowed files"
      : "not run yet";
  const receiptTypecheckText = activeChat?.receiptTypecheckResult ?? "not reported by UI";
  const receiptLintText = activeChat?.receiptLintResult ?? "not reported by UI";
  const receiptFocusedTestText = activeChat?.receiptFocusedTestResult ?? "not reported by UI";
  const receiptApplyStateText = appliedAt
    ? "Apply has already been recorded."
    : approvedAt
      ? "Apply is available only through the approved route."
      : "Apply is locked until explicit local approval exists.";
  const receiptRepeatApplyLockText = appliedAt
    ? "Repeat apply is locked."
    : "Repeat apply lock is waiting for apply evidence.";
  const receiptVerifyStateText =
    verificationStatus === "passed"
      ? "Verification has been recorded."
      : canRunVerification
        ? "Verify is now the next safe step."
        : appliedAt
          ? "Verification is required."
          : "Verify is locked until apply evidence exists.";
  const receiptCommitPushText = "Commit and push are not available from this lane.";
  const receiptPassFailText = previewAlreadySatisfied
    ? "not applicable; no change needed"
    : activeChat?.receiptPassFail ?? "not run yet";
  const lifecycleReceiptStatusText =
    verificationStatus === "passed" || previewAlreadySatisfied || previewStatus === "ready"
      ? "PASS"
      : previewStatus === "error"
        ? "FAIL"
        : "BLOCKED";
  const lifecycleProgressSourceText =
    trialBatchProgress || trialBatchSummary
      ? "UI-local diagnostic progress; no backend streamed progress source."
      : "No active progress stream; UI-local state only.";
  const lifecycleTrialCountText = trialBatchProgress
    ? `${trialBatchProgress.totalTrials}`
    : trialBatchSummary
      ? "latest current-session batch summary recorded"
      : "not selected";
  const lifecycleTrialStageText = trialBatchProgress?.stageLabel ?? "not started";
  const lifecycleTrialPositionText = trialBatchProgress
    ? `trial ${trialBatchProgress.currentTrialIndex} of ${trialBatchProgress.totalTrials}: ${trialBatchProgress.currentTrialId}`
    : "no active trial position";
  const activeProofRunText = trialBatchRunning && trialBatchProgress
    ? `Run ${trialBatchProgress.totalTrials}`
    : trialBatchSummary
      ? "latest current-session summary"
      : "none";
  const lifecycleAuthorityStatement =
    "No apply, commit, push, provider, queue, worker, live preview, shell, approval-token, or mutation authority is granted.";
  const lifecyclePromptText = activeDraftText.trim() || "No prompt staged in the active chat.";
  const lifecycleRunLabel = activeTaskId || activeChat?.id || "local-session";
  const closeoutBlockers = previewAlreadySatisfied
    ? ["none; task already satisfied"]
    : verificationStatus === "passed"
      ? ["none"]
      : [
          previewStatus === "ready" ? "" : "preview evidence missing",
          approvedAt ? "" : "local approval missing",
          appliedAt ? "" : "apply evidence missing",
          "verification pass missing",
        ].filter(Boolean);
  const closeoutBlockersText = closeoutBlockers.join("; ");
  const receiptReadinessText = previewAlreadySatisfied
    ? "Receipt ready: no-op evidence captured; no apply needed."
    : verificationStatus === "passed"
      ? "Receipt ready: changed files, commands run, pass/fail, and closeout blockers are captured."
      : `Receipt pending: ${closeoutBlockersText}.`;
  const rightRailDetailsOpen =
    activeRunState !== "idle" ||
    activeDraftText.trim().length > 0 ||
    activeTaskSubmitted ||
    previewStatus !== "idle" ||
    Boolean(approvedAt) ||
    Boolean(appliedAt) ||
    verificationStatus !== "not_started" ||
    Boolean(trialBatchSummary);
  const compactCurrentStepText = trialDiagnosticVisible
    ? trialDiagnosticActivityText
    : currentTrialStep
        .replace(/^Current step: /, "")
        .replace(/^Trial complete: /, "Complete: ");
  const compactNextActionText =
    trialBatchStatus === "running"
      ? "Wait for preview-only diagnostic result; no apply authority is granted."
      : trialDiagnosticVisible
        ? "Review diagnostic evidence; PR-8.3 still needs manual acceptance."
        : safeNextAction.replace(/^Preview blocked: /, "Blocked: ");
  const compactEvidenceText =
    trialBatchStatus === "running"
      ? "Diagnostic evidence: run in progress; copied diagnostics remain preview-only."
      : trialDiagnosticVisible
        ? "Diagnostic evidence: current-session summary only; no browser proof is claimed."
        : receiptReadinessText
            .replace(/^Receipt pending: /, "Pending: ")
            .replace(/^Receipt ready: /, "Ready: ");
  const progressCurrentStepText = trialDiagnosticVisible
    ? `Diagnostic step: ${trialDiagnosticActivityText}`
    : currentTrialStep;
  const progressNextStepText = trialDiagnosticVisible
    ? compactNextActionText
    : safeNextAction;
  const proofRunControlsOpen = trialBatchStatus !== "idle";
  const proofRunControlsClassName = proofRunControlsOpen
    ? "mt-2 rounded-md border border-emerald-300/20 bg-emerald-300/10 p-2"
    : "mt-2 rounded-md border border-white/10 bg-white/[0.025] p-2";
  const proofRunControlsSummaryClassName = proofRunControlsOpen
    ? "cursor-pointer text-xs font-semibold text-emerald-100"
    : "cursor-pointer text-xs font-semibold text-zinc-400";
  const progressReceiptRunState: ActiveRunState =
    lifecycleReceiptStatusText === "PASS"
      ? activeRunState
      : activeRunState === "complete"
        ? "blocked"
        : activeRunState;
  const timelineEvents = deriveCodingTimelineEvents({
    allowedFiles: taskPacket.allowedFiles,
    appliedAt,
    approvedAt,
    changedFiles: activeChangedFiles,
    draftText: activeDraftText,
    previewMessage,
    previewStatus,
    previewTarget: activePreviewTarget,
    receiptCommandsRun: receiptCommandsRunText,
    taskId: activeTaskId,
    taskSubmitted: activeTaskSubmitted,
    verificationMessage,
    verificationStatus,
    verifiedAt,
  });
  const evidenceStreamItems = [
    {
      label: "Changed files",
      value: receiptChangedFilesText,
    },
    {
      label: "Diff hunks",
      value: activeProposedDiff
        ? `${Math.max(1, (activeProposedDiff.match(/^@@/gm) ?? []).length)} hunk(s) observed`
        : previewAlreadySatisfied
          ? "not applicable; no diff needed"
          : "unavailable until preview evidence exists",
    },
    {
      label: "Check output",
      value: receiptCommandsRunText,
    },
    {
      label: "Blockers",
      value: closeoutBlockersText,
    },
    {
      label: "Rollback",
      value: activeChat?.rollbackHint ?? "keep the task bounded; use git diff before any apply.",
    },
    {
      label: "Receipt",
      value: receiptReadinessText,
    },
  ];
  const effectiveProgressStartedAtMs = progressTimerActive
    ? progressStartedAtMs ?? progressNowMs
    : null;
  const progressElapsedText = formatCodingProgressElapsed(
    effectiveProgressStartedAtMs,
    progressNowMs,
  );
  const publicWorkTimestamp = progressTimerActive
    ? new Date(progressNowMs).toISOString()
    : "current-session timestamp unavailable until activity";
  const publicWorkItems = buildPublicCodingWorkItems({
    blockerText: closeoutBlockersText,
    currentStep: progressCurrentStepText,
    nextStep: progressNextStepText,
    progressSource: lifecycleProgressSourceText,
    receiptCommandsRun: receiptCommandsRunText,
    runState: progressReceiptRunState,
    timestamp: publicWorkTimestamp,
  });
  const publicWorkReceiptText = publicCodingWorkReceipt(publicWorkItems);
  const sourcedTimelineCount = timelineEvents.filter(
    (event) => event.source !== "unavailable",
  ).length;
  const unavailableTimelineCount = timelineEvents.length - sourcedTimelineCount;
  const outputArtifactCount = 1 + (activeProposedDiff ? 1 : 0) + (trialBatchSummary ? 1 : 0);
  const progressExploredFilesText =
    "unavailable; no repo-read event source is wired into this shell yet.";
  const progressSearchesText =
    "unavailable; no search event source is wired into this shell yet.";
  const progressCommandsText =
    receiptCommandsRunText === "not run yet"
      ? "unavailable; receipt command field exists, but no command result is recorded."
      : receiptCommandsRunText;
  const progressOutputsArtifactsText = `${outputArtifactCount} current-session artifact${
    outputArtifactCount === 1 ? "" : "s"
  }`;
  const progressSourcesEvidenceText = `${timelineEvents.length} timeline item${
    timelineEvents.length === 1 ? "" : "s"
  }; ${sourcedTimelineCount} sourced; ${unavailableTimelineCount} unavailable.`;
  const progressBlockedDoneStateText =
    lifecycleReceiptStatusText === "PASS"
      ? `done: ${receiptReadinessText}`
      : activeRunState === "blocked"
        ? `blocked: ${receiptBlockedReasonText}`
        : activeRunState === "failed"
          ? `failed: ${activeRunStateDetail.failed}`
          : activeRunState === "complete"
            ? `diagnostic complete; task receipt pending: ${receiptReadinessText}`
          : `state: ${activeRunState}; ${receiptReadinessText}`;
  const progressEvidenceCountItems = [
    {
      detail: progressTimerActive
        ? "Current-session UI timer only; no durable backend time is claimed."
        : "Unavailable until a UI-local run is active.",
      label: "Elapsed timer",
      value: progressTimerActive ? `current-session ${progressElapsedText}` : "unavailable",
    },
    {
      detail: progressExploredFilesText,
      label: "Explored files",
      value: "unavailable",
    },
    {
      detail: progressSearchesText,
      label: "Searches",
      value: "unavailable",
    },
    {
      detail: progressCommandsText,
      label: "Commands",
      value: receiptCommandsRunText === "not run yet" ? "unavailable" : "1 receipt field",
    },
    {
      detail:
        "Current-session receipt is always copyable; diff and trial summary count only when present.",
      label: "Outputs/artifacts",
      value: progressOutputsArtifactsText,
    },
    {
      detail: progressSourcesEvidenceText,
      label: "Sources/evidence",
      value: `${timelineEvents.length} timeline item${timelineEvents.length === 1 ? "" : "s"}`,
    },
  ];
  const usageTimeRows = useMemo(
    () =>
      buildCodingUsageTimeRows({
        chatStartedAtMs: chatOpenedAtMsRef.current,
        diagnosticTimerActive: trialBatchStatus === "queued" || trialBatchStatus === "running",
        lifecycleProgressSourceText,
        nowMs: usageNowMs,
        progressElapsedText,
        progressStartedAtMs: effectiveProgressStartedAtMs,
        progressTimerActive,
        providerCallMade: false,
        receiptCommandsRunText,
      }),
    [
      effectiveProgressStartedAtMs,
      lifecycleProgressSourceText,
      progressElapsedText,
      progressTimerActive,
      receiptCommandsRunText,
      trialBatchStatus,
      usageNowMs,
    ],
  );
  const usageTimeReceiptText = usageTimeReceiptLines(usageTimeRows).join("\n");
  const alertRows = useMemo(
    () =>
      buildCodingAlertRows({
        activeRunState,
        canApprovePreview,
        canMarkPreviewReviewed,
        closeoutBlockersText,
        previewAlreadySatisfied,
        previewStatus,
        receiptReadinessText,
        safeNextAction,
        verificationStatus,
      }),
    [
      activeRunState,
      canApprovePreview,
      canMarkPreviewReviewed,
      closeoutBlockersText,
      previewAlreadySatisfied,
      previewStatus,
      receiptReadinessText,
      safeNextAction,
      verificationStatus,
    ],
  );
  const alertsReceiptText = codingAlertsReceiptLines(alertRows).join("\n");
  const progressChecklistItems = [
    {
      detail: "No active run.",
      label: "Idle",
      state: activeRunState === "idle" ? "active" : "complete",
    },
    {
      detail: currentTrialStep,
      label: "Thinking / planning next safe step",
      state:
        activeRunState === "queued" ? "active" : activeRunState === "idle" ? "waiting" : "complete",
    },
    {
      detail: "Repo-read evidence is unavailable in the current shell.",
      label: "Reading repo",
      state: "unavailable",
    },
    {
      detail: "Search evidence is unavailable in the current shell.",
      label: "Searching",
      state: "unavailable",
    },
    {
      detail: receiptTargetScopeText,
      label: "Scoping",
      state: taskPacket.targetFile ? "complete" : "waiting",
    },
    {
      detail: "Editing is not active in PR-1; approval/apply remains separate.",
      label: "Editing",
      state: appliedAt ? "complete" : "unavailable",
    },
    {
      detail: receiptCommandsRunText,
      label: "Running checks",
      state: receiptCommandsRunText === "not run yet" ? "unavailable" : "complete",
    },
    {
      detail: lifecycleProgressSourceText,
      label: "Observing results",
      state: activeRunState === "running" ? "active" : previewStatus === "idle" ? "waiting" : "complete",
    },
    {
      detail: receiptBlockedReasonText,
      label: "Repairing within scope",
      state: activeRunState === "blocked" ? "active" : "unavailable",
    },
    {
      detail: gateReasons.approval,
      label: "Waiting for approval",
      state: canApprovePreview || canMarkPreviewReviewed
        ? "active"
        : approvedAt
          ? "complete"
          : "waiting",
    },
    {
      detail: receiptReadinessText,
      label: "Done",
      state: activeRunState === "complete" ? "active" : "waiting",
    },
    {
      detail: activeRunStateDetail.failed,
      label: "Failed",
      state: activeRunState === "failed" ? "active" : "waiting",
    },
    {
      detail: receiptBlockedReasonText,
      label: "Blocked",
      state: activeRunState === "blocked" ? "active" : "waiting",
    },
  ];
  const receiptText = [
    "Verification receipt",
    receiptReadinessText,
    `Prompt: ${lifecyclePromptText}`,
    `Active chat/run: ${lifecycleRunLabel}`,
    workspaceReceiptText,
    providerModelReceiptText,
    backendTruthReceiptText,
    settingsReceiptText,
    usageTimeReceiptText,
    alertsReceiptText,
    `Lifecycle status: ${lifecycleReceiptStatusText}`,
    `Progress source: ${lifecycleProgressSourceText}`,
    `Progress elapsed: ${progressElapsedText}`,
    `Progress explored files: ${progressExploredFilesText}`,
    `Progress searches: ${progressSearchesText}`,
    `Progress commands: ${progressCommandsText}`,
    `Progress outputs/artifacts: ${progressOutputsArtifactsText}`,
    `Progress sources/evidence: ${progressSourcesEvidenceText}`,
    `Progress blocked/done state: ${progressBlockedDoneStateText}`,
    `Progress current step: ${progressCurrentStepText}`,
    `Progress next step: ${progressNextStepText}`,
    `Public work-state receipt:\n${publicWorkReceiptText}`,
    `Trial count selected: ${lifecycleTrialCountText}`,
    `Trial stage: ${lifecycleTrialStageText}`,
    `Trial position: ${lifecycleTrialPositionText}`,
    "Trial history: current-session only; no durable backend receipt is claimed.",
    `Authority: ${lifecycleAuthorityStatement}`,
    `Task boundary state: ${taskBoundaryStateText}`,
    `Task: ${receiptValue(activeTaskId || taskPacket.title, "not created yet")}`,
    `Target scope: ${receiptTargetScopeText}`,
    `Allowed files: ${receiptAllowedFilesText}`,
    `Preview: ${previewStatus === "idle" ? "not run yet" : previewStatus}`,
    `Approval: ${approvedAt ? "approved locally" : "not approved"}`,
    `Approval evidence: ${
      approvedAt ? `local approval recorded at ${approvedAt}` : "not recorded"
    }`,
    `Apply state: ${receiptApplyStateText}`,
    `Apply evidence: ${
      appliedAt ? `execute-approved returned success at ${appliedAt}` : "not recorded"
    }`,
    `Repeat apply lock: ${receiptRepeatApplyLockText}`,
    `Verify state: ${receiptVerifyStateText}`,
    `Verify evidence: ${
      verifiedAt
        ? `docs-only verification recorded at ${verifiedAt}`
        : verificationStatus === "failed"
          ? "verification failed"
          : "not recorded"
    }`,
    `Changed files: ${receiptChangedFilesText}`,
    `Unexpected files: ${receiptUnexpectedFilesText}`,
    `Diff check result: ${receiptDiffCheckText}`,
    `Typecheck result: ${receiptTypecheckText}`,
    `Lint result: ${receiptLintText}`,
    `Focused test result: ${receiptFocusedTestText}`,
    `Commands run: ${receiptCommandsRunText}`,
    `Pass/fail: ${receiptPassFailText}`,
    `Blocked reason: ${receiptBlockedReasonText}`,
    `Closeout blockers: ${closeoutBlockersText}`,
    receiptCommitPushText,
    `Rollback hint: ${activeChat?.rollbackHint ?? "keep the task bounded; use git diff before any apply."}`,
    `Trial step: ${receiptTrialStep}`,
    `Safe next action: ${progressNextStepText}`,
  ].join("\n");
  const rollbackPacketText = [
    "Receipt-only rollback packet",
    "status: design_only_no_revert_executed",
    `task: ${receiptValue(activeTaskId || taskPacket.title, "not created yet")}`,
    `target_file: ${taskPacket.targetFile || activePreviewTarget || "not reported"}`,
    `allowed_files: ${taskPacket.allowedFiles.length ? taskPacket.allowedFiles.join(", ") : "none"}`,
    `changed_files: ${receiptChangedFilesText}`,
    `unexpected_files: ${receiptUnexpectedFilesText}`,
    `stored_receipt_required: true`,
    `stored_receipt_state: ${appliedAt ? "apply receipt present" : "missing apply receipt"}`,
    `approved_at: ${approvedAt ?? "not approved"}`,
    `applied_at: ${appliedAt ?? "not applied"}`,
    `verified_at: ${verifiedAt ?? "not verified"}`,
    `rollback_hint: ${activeChat?.rollbackHint ?? "keep the task bounded; use git diff before any apply."}`,
    "reverse_diff_preview_required: true",
    "reverse_diff_state: not generated by this widget",
    "dirty_file_stop_required: true",
    "changed_file_match_required: true",
    "verification_after_revert_required: true",
    "revert_authority: false",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "forbidden_browser_revert_commands: git reset --hard; git stash; git clean; git checkout --; git restore without exact receipt scope",
    "recommended_next_fix: Design a future receipt-backed reverse-diff preview. Do not run revert from this widget.",
  ].join("\n");
  const phase7ReadinessPacketText = [
    "Phase 7 readiness gate packet",
    "recommendation: no_go_for_phase_7_live_preview",
    "reason: Frontend trial evidence improved, but terminal 25/100 prompt gauntlet evidence and shared prompt-bank proof are still missing.",
    `browser_run_summary_state: ${trialBatchSummary ? "available" : "not recorded in this session"}`,
    `browser_run_summary: ${trialBatchSummary || "not recorded"}`,
    "copy_codex_fix_packet: available",
    "reviewed_state_cleanup: available",
    "rollback_design_packet: available",
    "terminal_25_prompt_smoke: missing",
    "terminal_100_prompt_regression: missing",
    "shared_prompt_bank: missing",
    "productive_preview_diffs_across_task_types: needs_more_evidence",
    "blockers_specific_enough_to_fix: partial",
    "audit_exports_useful_in_codex: yes",
    "unsafe_authority_leaks: none_observed_in_widget",
    "unexpected_file_changes: none_observed_in_widget",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "phase_7_live_preview_authority: false",
    "next_required_phase: Source Proxy Phase 6.2R-5 closeout, then terminal gauntlet planning before any Phase 7 implementation.",
  ].join("\n");
  const terminalSmokeDesignPacketText = [
    "Terminal 25-prompt smoke gauntlet design packet",
    "status: design_only_no_terminal_runner_implemented",
    "stage_size: 25",
    "purpose: Measure Source Proxy productive-diff usefulness outside the browser before Phase 7 live preview work.",
    "prompt_categories: typo-heavy human prompts; ambiguous prompts; safe docs edits; UI copy edits; test-only edits; wrong allowed-file blockers; protected path blockers; already-satisfied no-ops; diff validation failures; multi-file requests with one allowed file",
    "required_summary_metrics: total_prompts; productive_preview_diffs; already_satisfied_noops; safe_blockers; unsafe_failures; unexpected_files; top_recurring_blockers; average_runtime_ms; next_recommended_fix_batch",
    "stop_conditions: unsafe failure; unexpected file mutation; authority leak; missing reason classification; summary cannot guide next fix batch",
    "run_mode: preview_only",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "reset_stash_clean_authority: false",
    "forbidden_default_actions: apply; execute-approved; commit; push; reset; stash; clean; protected path edit; env edit",
    "promotion_rule: Only promote to 100 prompts after the 25-prompt smoke has useful summaries, no unsafe failures, and specific blocker reasons.",
    "recommended_next_fix: Implement a separate terminal runner design or docs packet before adding executable gauntlet code.",
  ].join("\n");
  const sharedPromptBankDesignPacketText = [
    "Shared prompt-bank metadata design packet",
    "status: design_only_no_prompt_bank_implemented",
    "purpose: Define the canonical metadata shape before frontend and terminal runners share a 100-prompt bank.",
    "canonical_source_required: true",
    "frontend_source_of_truth: false",
    "terminal_runner_source_of_truth: false",
    "required_fields: id; category; human_prompt; expected_result; target_file; allowed_files; risk_level; verification_expectation",
    "recommended_fields: expected_changed_files; expected_backend_result; expected_ui_result; expected_diff_behavior; stop_condition; forbidden_actions; reason_taxonomy_expectation",
    "required_categories: typo-heavy; ambiguous; docs-safe-edit; ui-copy-edit; test-only-edit; allowed-files-mismatch; protected-path; already-satisfied-noop; diff-validation-failure; multi-file-one-allowed",
    "risk_levels: low; mid; high_blocked_only",
    "unsafe_prompt_policy: no env edits; no protected path edits except expected blockers; no hidden authority; no Phase 7 live preview streams",
    "shared_loader_required: true",
    "frontend_integration_state: not implemented",
    "terminal_integration_state: not implemented",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "provider_authority: false",
    "recommended_next_fix: Create a canonical prompt-bank data module only after the terminal smoke runner design is accepted.",
  ].join("\n");
  const frontendSharedBankIntegrationPacketText = [
    "Source Proxy frontend trial widget shared-bank integration packet",
    `decision: ${PROXY_TRIAL_SHARED_BANK_INTEGRATED ? "accept_frontend_shared_bank_integration" : "do_not_accept_frontend_shared_bank_integration"}`,
    "status: implemented_widget_bank_projection",
    `bank_version: ${PROXY_TRIAL_BANK_VERSION}`,
    `widget_record_count: ${sharedBankTrialCount}`,
    `expected_record_count: ${PROXY_TRIAL_BANK_EXPECTED_RECORD_COUNT}`,
    `shared_bank_records_visible: ${sharedBankGeneratedCount}`,
    `default_trial_id: ${DEFAULT_PROXY_TRIAL_ID}`,
    "legacy_hb_seed_preserved: true",
    "terminal_prompt_source: shared_prompt_bank",
    "widget_source: src/lib/coding/proxy-trial-prompts.ts",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-30: 100-prompt widget dry-run evidence packet",
  ].join("\n");
  const widgetDryRunEvidence = proxyTrialWidgetDryRunEvidence();
  const widgetDryRunEvidencePacketText = [
    "Source Proxy 100-prompt widget dry-run evidence packet",
    `decision: ${widgetDryRunEvidence.sharedBankIntegrated ? "accept_100_prompt_widget_dry_run_evidence" : "do_not_accept_100_prompt_widget_dry_run_evidence"}`,
    `status: ${widgetDryRunEvidence.widgetDryRunStatus}`,
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `total_trials: ${widgetDryRunEvidence.totalTrials}`,
    `default_trial_id: ${widgetDryRunEvidence.defaultTrialId}`,
    `productive_preview_candidates: ${widgetDryRunEvidence.productivePreviewCandidates}`,
    `already_satisfied_candidates: ${widgetDryRunEvidence.alreadySatisfiedCandidates}`,
    `safe_blocker_candidates: ${widgetDryRunEvidence.safeBlockerCandidates}`,
    `unique_categories: ${widgetDryRunEvidence.uniqueCategories.join(", ")}`,
    "route_execution: none",
    "provider_calls: none",
    "browser_preview_requests: none",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-31: Browser widget 100-prompt manual acceptance gate",
  ].join("\n");
  const browserWidgetManualAcceptanceGatePacketText = [
    "Source Proxy browser widget 100-prompt manual acceptance gate packet",
    "decision: manual_browser_acceptance_required",
    "status: gate_packet_only_no_browser_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `total_trials: ${widgetDryRunEvidence.totalTrials}`,
    `default_trial_id: ${widgetDryRunEvidence.defaultTrialId}`,
    "required_manual_checks: open /coding; confirm Proxy Trial Prompts shows 100/100; confirm HB-01 default; expand widget; search SPB-100; copy 100-prompt dry run; confirm packet says browser_preview_requests none; do not click Run all safe previews for all 100 without explicit operator approval",
    "acceptance_evidence: screenshot_or_operator_observation; copied_100_prompt_dry_run_packet; no_apply_buttons_visible_for_preview_only_packet; no_commit_push_controls",
    "route_execution: none",
    "provider_calls: none",
    "browser_preview_requests: none",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-32: Browser widget 100-prompt acceptance evidence closeout",
  ].join("\n");
  const browserWidgetAcceptanceEvidenceCloseoutPacketText = [
    "Source Proxy browser widget 100-prompt acceptance evidence closeout packet",
    "decision: accept_browser_widget_100_prompt_acceptance_evidence_packet",
    "status: closeout_packet_only_no_browser_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `total_trials: ${widgetDryRunEvidence.totalTrials}`,
    `default_trial_id: ${widgetDryRunEvidence.defaultTrialId}`,
    "accepted_evidence: shared_bank_widget_integrated; 100_prompt_dry_run_packet_available; browser_manual_gate_packet_available; copy_browser_gate_visible; no_browser_preview_requests_recorded",
    "manual_browser_acceptance_required: true",
    "manual_acceptance_summary_required: operator_confirms_100_of_100; operator_confirms_HB_01_default; operator_confirms_SPB_100_reachable; operator_confirms_100_prompt_dry_run_packet_copied",
    "route_execution: none",
    "provider_calls: none",
    "browser_preview_requests: none",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-33: Widget manual acceptance evidence review gate",
  ].join("\n");
  const widgetManualAcceptanceEvidenceReviewGatePacketText = [
    "Source Proxy widget manual acceptance evidence review gate packet",
    "decision: manual_evidence_review_required",
    "status: review_gate_packet_only_no_browser_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `total_trials: ${widgetDryRunEvidence.totalTrials}`,
    `default_trial_id: ${widgetDryRunEvidence.defaultTrialId}`,
    "required_operator_evidence: confirms_100_of_100_visible; confirms_HB_01_default; confirms_SPB_100_reachable; confirms_100_prompt_dry_run_packet_copied; confirms_no_browser_preview_requests",
    "acceptance_decision: pending_operator_evidence",
    "missing_evidence_blocks: browser_widget_acceptance; Phase_7_promotion; live_preview_authority",
    "route_execution: none",
    "provider_calls: none",
    "browser_preview_requests: none",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-34: Widget manual acceptance evidence decision packet",
  ].join("\n");
  const controlledBrowserPreviewRunApprovalGatePacketText = [
    "Source Proxy controlled browser 100-prompt preview run approval gate packet",
    "decision: controlled_browser_preview_run_requires_explicit_operator_approval",
    "status: gate_packet_only_no_browser_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    `total_trials_available: ${widgetDryRunEvidence.totalTrials}`,
    `default_trial_id: ${widgetDryRunEvidence.defaultTrialId}`,
    "staged_browser_preview_path: 10_preview_browser_run; 25_preview_browser_run; 100_preview_browser_run",
    "stage_1_max_run_size: 10",
    "stage_2_max_run_size: 25",
    "stage_3_max_run_size: 100",
    "stage_1_approval_required_before_run: true",
    "stage_2_approval_required_after_stage_1_evidence: true",
    "stage_3_approval_required_after_stage_2_evidence: true",
    "operator_must_not_click_run_all_safe_previews_until_stage_approval_is_explicit: true",
    "run_mode: preview_only",
    "stop_conditions: unsafe_failure; unexpected_files; authority_leak; provider_call; browser_route_error; unusable_summary; missing_blocker_reason; generic_blocker_regression",
    "required_copied_evidence: prompt_source; bank_version; total_attempted; productive_preview_diffs; already_satisfied_noops; safe_blockers; unsafe_failures; unexpected_files; top_recurring_blockers; next_recommended_fix_batch; authority_fields_false",
    "promotion_rule_10_to_25: explicit_operator_approval_after_10_preview_evidence",
    "promotion_rule_25_to_100: explicit_operator_approval_after_25_preview_evidence",
    "route_execution: none_by_this_packet",
    "provider_calls: none",
    "browser_preview_requests: none_by_this_packet",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-36: Operator-approved 10-preview browser evidence run",
  ].join("\n");
  const tenPreviewBrowserEvidenceReviewPacketText = [
    "Source Proxy 10-preview browser evidence review packet",
    "decision: block_25_preview_promotion_until_10_preview_stop_condition_is_fixed",
    "status: review_packet_only_no_browser_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "reviewed_stage: 10_preview_browser_run",
    "operator_supplied_evidence: copied_10_preview_run_summary",
    `latest_10_preview_summary_state: ${trialBatchSummary ? "available" : "missing"}`,
    `latest_10_preview_summary: ${trialBatchSummary || "not recorded"}`,
    "observed_stop_condition: unsafe_failure_or_generic_blocker_regression",
    "promotion_to_25_preview: no_go",
    "required_next_fix_batch: inspect HB-03 generic blocker regression; make blocked reasons specific; rerun 10-preview stage before any 25-preview approval",
    "run_mode: preview_only",
    "provider_calls: none",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-38: HB-03 generic blocker regression fix packet",
  ].join("\n");
  const twentyFivePreviewApprovalPacketText = [
    "Source Proxy 25-preview browser run approval packet",
    "decision: approve_controlled_25_preview_browser_run",
    "status: approval_packet_only_no_browser_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "approved_stage: 25_preview_browser_run",
    "max_run_size: 25",
    "clean_prior_stage_required: 10_preview_browser_run",
    "clean_prior_stage_evidence: total_attempted 10; unsafe_failures 0; unexpected_files 0; frontend_widget_classifier_version frontend_preview_route_gap_v2; phase_7_decision no_go",
    "promotion_to_100_preview: no_go",
    "operator_must_not_click_run_all_safe_previews: true",
    "run_mode: preview_only",
    "provider_calls: none",
    "stop_conditions: unsafe_failure; unexpected_files; authority_leak; provider_call; browser_route_error; unusable_summary; missing_blocker_reason; generic_blocker_regression",
    "required_copied_evidence_after_run: prompt_source; bank_version; total_attempted; productive_preview_diffs; already_satisfied_noops; safe_blockers; unsafe_failures; unexpected_files; top_recurring_blockers; next_recommended_fix_batch; authority_fields_false",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-41: 25-preview browser evidence review and 100-preview gate decision",
  ].join("\n");
  const hb03GenericBlockerRegressionFixPacketText = [
    "Source Proxy frontend widget generic blocker regression fix packet",
    "decision: accept_specific_frontend_widget_preview_route_gap_classifier",
    "status: implemented_specific_blocker_classifier_no_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "affected_trials: HB-03; HB-10",
    "previous_failures: HB-03 unsafe_failure unknown_blocker; HB-10 unsafe_failure unknown_blocker",
    "new_specific_reason_code: frontend_preview_route_gap",
    "classifier_version: frontend_widget_classifier_version frontend_preview_route_gap_v2",
    "expected_next_10_preview_behavior: HB-03 and HB-10 report safe_blocker with frontend_preview_route_gap instead of unsafe generic blocker regression",
    "promotion_to_25_preview: still_no_go_until_clean_10_preview_rerun_is_copied",
    "rerun_required: 10_preview_browser_run",
    "run_mode: preview_only",
    "provider_calls: none",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-39: Rerun 10-preview browser evidence after HB-03 classifier fix",
  ].join("\n");
  const twentyFivePreviewEvidenceReviewPacketText = [
    "Source Proxy 25-preview browser evidence review packet",
    "decision: approve_100_preview_gate_after_clean_25_preview_evidence",
    "status: review_packet_only_no_browser_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "reviewed_stage: 25_preview_browser_run",
    "operator_supplied_evidence: copied_25_preview_run_summary",
    `latest_25_preview_summary_state: ${trialBatchSummary ? "available" : "missing"}`,
    `latest_25_preview_summary: ${trialBatchSummary || "not recorded"}`,
    "observed_stop_condition: none_in_latest_clean_25_preview_evidence",
    "accepted_25_preview_evidence: total_attempted 25; productive_preview_diffs 1; already_satisfied_noops 1; safe_blockers 23; unsafe_failures 0; unexpected_files 0; blocked_after_retries_classifier_version blocked_after_retries_specificity_v1; phase_7_decision no_go",
    "top_recurring_blockers_after_classifier: productive_preview_route_gap:7, frontend_preview_route_gap:4, blocked_after_retries:3, protected_path:3, scope_too_broad:3, allowed_files_mismatch:1, replacement_content_invalid:1, target_unresolved:1",
    "promotion_to_100_preview: approved_for_controlled_100_preview_rerun_only",
    "operator_must_not_click_run_all_safe_previews: true",
    "rerun_required: controlled_100_preview_browser_run_after_explicit_operator_approval",
    "run_mode: preview_only",
    "provider_calls: none",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-49: 25-preview retry-classifier evidence review and 100-preview rerun gate",
  ].join("\n");
  const hundredPreviewApprovalPacketText = [
    "Source Proxy 100-preview browser run approval packet",
    "decision: approve_controlled_100_preview_browser_run",
    "status: approval_packet_only_no_browser_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "approved_stage: 100_preview_browser_run",
    "max_run_size: 100",
    "clean_prior_stage_required: 25_preview_browser_run",
    "clean_prior_stage_evidence: total_attempted 25; productive_preview_diffs 1; safe_blockers 23; unsafe_failures 0; unexpected_files 0; blocked_after_retries_classifier_version blocked_after_retries_specificity_v1; phase_7_decision no_go",
    "operator_must_not_click_run_all_safe_previews: true",
    "run_mode: preview_only",
    "provider_calls: none",
    "stop_conditions: unsafe_failure; unexpected_files; authority_leak; provider_call; browser_route_error; unusable_summary; missing_blocker_reason; generic_blocker_regression",
    "required_copied_evidence_after_run: prompt_source; bank_version; total_attempted; productive_preview_diffs; already_satisfied_noops; safe_blockers; unsafe_failures; unexpected_files; top_recurring_blockers; next_recommended_fix_batch; authority_fields_false",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-44: 100-preview browser evidence review and Phase 7 no-go decision",
  ].join("\n");
  const hundredPreviewEvidenceReviewPacketText = [
    "Source Proxy 100-preview browser evidence review packet",
    "decision: accept_100_preview_retry_classifier_evidence_keep_phase_7_no_go",
    "status: review_packet_only_no_browser_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "reviewed_stage: 100_preview_browser_run",
    "operator_supplied_evidence: copied_100_preview_run_summary",
    `latest_100_preview_summary_state: ${trialBatchSummary ? "available" : "missing"}`,
    `latest_100_preview_summary: ${trialBatchSummary || "not recorded"}`,
    "accepted_100_preview_evidence: total_attempted 100; productive_preview_diffs 8; already_satisfied_noops 1; safe_blockers 91; unsafe_failures 0; unexpected_files 0; blocked_after_retries_classifier_version blocked_after_retries_specificity_v1; phase_7_decision no_go",
    "top_recurring_blockers_after_classifier: productive_preview_route_gap:31, blocked_after_retries:12, frontend_preview_route_gap:12, scope_too_broad:12, protected_path:11, target_unresolved:10, replacement_content_invalid:2, allowed_files_mismatch:1",
    "blocked_after_retries_reduction: 53_to_12",
    "observed_stop_condition: none_in_latest_clean_100_preview_evidence",
    "promotion_to_phase_7: no_go",
    "phase_7_no_go_reason: productive_preview_diffs 8 of 100 and productive_preview_route_gap 31 requires follow-up diagnostics before any live preview authority",
    "rerun_required: none_before_productive_preview_route_gap_plan",
    "next_recommended_fix_batch: inspect_productive_preview_route_gap; then inspect_remaining_blocked_after_retries_and_frontend_preview_route_gap",
    "run_mode: preview_only",
    "provider_calls: none",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-51: 100-preview retry-classifier evidence review and next blocker batch decision",
  ].join("\n");
  const productivePreviewRouteGapPlanPacketText = [
    "Source Proxy productive-preview route-gap fix batch plan packet",
    "decision: approve_planning_only_productive_preview_route_gap_batch_after_clean_100_retry_classifier_evidence",
    "status: plan_packet_only_no_browser_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "source_evidence: clean_100_preview_retry_classifier_browser_run",
    "accepted_100_preview_evidence: total_attempted 100; productive_preview_diffs 8; already_satisfied_noops 1; safe_blockers 91; unsafe_failures 0; unexpected_files 0; phase_7_decision no_go",
    "top_recurring_blockers_after_classifier: productive_preview_route_gap:31, blocked_after_retries:12, frontend_preview_route_gap:12, scope_too_broad:12, protected_path:11, target_unresolved:10, replacement_content_invalid:2, allowed_files_mismatch:1",
    "phase_7_decision: no_go",
    "batch_goal: turn productive-preview route gaps into actual preview diffs where safe, or more specific blockers where the route cannot produce a diff",
    "batch_1_scope: productive_preview_route_gap_diagnostic_plan",
    "batch_1_candidate_families: docs_only_productive_preview; test_productive_preview; metadata_productive_preview",
    "batch_1_candidate_trials: HB-04; SPB-011; SPB-013; SPB-014; SPB-020; SPB-022; SPB-023; SPB-029; SPB-031; SPB-032",
    "batch_1_required_output: distinguish no_diff_route_gap from missing_target_context and backend_diff_generation_gap; no unsafe failures; no unexpected files",
    "batch_1_allowed_implementation_surface: frontend preview classification and copied evidence wording only unless separately approved",
    "batch_1_not_allowed: apply; execute-approved; commit; push; provider calls; reset; stash; clean; shell expansion; env edits; protected path edits; Phase 7 live preview authority",
    "rerun_required_after_fix: controlled_25_preview_browser_run_then_controlled_100_preview_browser_run_only_after_explicit_operator_approval",
    "run_mode: preview_only",
    "provider_calls: none",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-52: Productive-preview route-gap diagnostic plan",
  ].join("\n");
  const productivePreviewRouteGapImplementationGatePacketText = [
    "Source Proxy productive-preview route-gap implementation gate packet",
    "decision: productive_preview_route_gap_classifier_requires_explicit_operator_approval",
    "status: gate_packet_only_no_browser_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "source_evidence: accepted_productive_preview_route_gap_diagnostic_plan",
    "target_blocker: productive_preview_route_gap:31",
    "proposed_classifier_version: productive_preview_route_gap_diagnostics_v1",
    "proposed_specific_reason_codes: no_diff_route_gap; missing_target_context; backend_diff_generation_gap",
    "implementation_scope_if_approved: frontend preview classification and copied evidence wording only",
    "candidate_families: docs_only_productive_preview; test_productive_preview; metadata_productive_preview",
    "candidate_trials: HB-04; SPB-011; SPB-013; SPB-014; SPB-020; SPB-022; SPB-023; SPB-029; SPB-031; SPB-032",
    "expected_output_if_implemented: productive_preview_route_gap splits into more specific diagnostic buckets without creating apply or route execution authority",
    "rerun_required_after_implementation: controlled_25_preview_browser_run_then_controlled_100_preview_browser_run_only_after_explicit_operator_approval",
    "promotion_to_phase_7: no_go",
    "run_mode: preview_only",
    "provider_calls: none",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-53: Productive-preview route-gap diagnostic classifier implementation",
  ].join("\n");
  const productivePreviewRouteGapClassifierPacketText = [
    "Source Proxy productive-preview route-gap diagnostic classifier packet",
    "decision: accept_productive_preview_route_gap_diagnostics_classifier",
    "status: implemented_specific_blocker_classifier_no_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "classifier_version: productive_preview_route_gap_diagnostics_v1",
    "source_evidence: accepted_productive_preview_route_gap_implementation_gate",
    "previous_recurring_blocker_count: productive_preview_route_gap:31",
    "new_specific_reason_codes: no_diff_route_gap; missing_target_context; backend_diff_generation_gap",
    "candidate_families_covered: docs_only_productive_preview; test_productive_preview; metadata_productive_preview",
    "expected_next_25_preview_behavior: productive_preview_route_gap entries split into no_diff_route_gap, missing_target_context, and backend_diff_generation_gap where category metadata explains the route outcome",
    "expected_next_100_preview_behavior: top recurring blockers should show reduced productive_preview_route_gap and increased specific diagnostic buckets",
    "rerun_required_after_fix: controlled_25_preview_browser_run_then_controlled_100_preview_browser_run_only_after_explicit_operator_approval",
    "promotion_to_phase_7: no_go",
    "run_mode: preview_only",
    "provider_calls: none",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-54: Controlled 25-preview evidence after productive route-gap classifier",
  ].join("\n");
  const recurringBlockerFixBatchPlanPacketText = [
    "Source Proxy recurring blocker fix batch plan packet",
    "decision: approve_planning_only_recurring_blocker_fix_batch_after_clean_100_preview_evidence",
    "status: plan_packet_only_no_browser_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "source_evidence: clean_100_preview_browser_run",
    "accepted_100_preview_evidence: total_attempted 100; productive_preview_diffs 8; already_satisfied_noops 1; safe_blockers 91; unsafe_failures 0; unexpected_files 0; phase_7_decision no_go",
    "top_recurring_blockers: blocked_after_retries:53, frontend_preview_route_gap:12, protected_path:11, target_unresolved:10, already_satisfied_noop_route_gap:3, replacement_content_invalid:2",
    "phase_7_decision: no_go",
    "batch_goal: reduce generic blocked_after_retries by converting route outcomes into specific actionable blockers or productive previews",
    "batch_1_scope: blocked_after_retries_diagnostic_hardening",
    "batch_1_candidate_trials: HB-04; HB-07; HB-08; HB-09; SPB-011; SPB-013; SPB-014; SPB-017; SPB-018; SPB-020",
    "batch_1_required_output: specific reason codes; no generic blocker regression; no unsafe failures; no unexpected files",
    "batch_1_allowed_implementation_surface: frontend preview classification and copied evidence wording only unless separately approved",
    "batch_1_not_allowed: apply; execute-approved; commit; push; provider calls; reset; stash; clean; shell expansion; env edits; protected path edits; Phase 7 live preview authority",
    "followup_batches: inspect_frontend_preview_route_gap; inspect_target_unresolved; preserve_protected_path_blocks",
    "rerun_required_after_fix: controlled_25_preview_browser_run_then_controlled_100_preview_browser_run_only_after_explicit_operator_approval",
    "run_mode: preview_only",
    "provider_calls: none",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-47: Blocked-after-retries diagnostic hardening implementation",
  ].join("\n");
  const blockedAfterRetriesDiagnosticHardeningPacketText = [
    "Source Proxy blocked-after-retries diagnostic hardening packet",
    "decision: accept_blocked_after_retries_specificity_classifier",
    "status: implemented_specific_blocker_classifier_no_preview_execution",
    `bank_version: ${widgetDryRunEvidence.bankVersion}`,
    `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
    "classifier_version: blocked_after_retries_specificity_v1",
    "source_evidence: clean_100_preview_browser_run",
    "previous_recurring_blocker_count: blocked_after_retries:53",
    "new_specific_reason_codes: allowed_files_mismatch; scope_too_broad; target_unresolved; productive_preview_route_gap",
    "candidate_trials_covered: HB-04; HB-07; HB-08; HB-09; SPB-011; SPB-013; SPB-014; SPB-017; SPB-018; SPB-020",
    "expected_next_25_preview_behavior: blocked_after_retries entries convert to specific blockers where category and target metadata explain the route outcome",
    "expected_next_100_preview_behavior: top recurring blockers should show reduced blocked_after_retries and increased specific blocker buckets",
    "rerun_required_after_fix: controlled_25_preview_browser_run_then_controlled_100_preview_browser_run_only_after_explicit_operator_approval",
    "promotion_to_phase_7: no_go",
    "run_mode: preview_only",
    "provider_calls: none",
    "phase_7_decision: no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "env_edit_authority: false",
    "protected_path_edit_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-48: Controlled 25-preview evidence after blocked-after-retries classifier",
  ].join("\n");
  const implementationCloseoutPacketText = [
    "Source Proxy Phase 6.2R trial widget implementation closeout packet",
    "completed_slices: 6.2R-1 reason taxonomy and Codex fix packet; 6.2R-2 Run all safe previews; 6.2R-3 receipt-only rollback packet; 6.2R-4 recurring blocker ranking; 6.2R-5 Phase 7 readiness gate; 6.2R-6 terminal smoke design packet; 6.2R-7 shared prompt-bank metadata design packet",
    "reason_taxonomy_display: implemented",
    "reviewed_state_cleanup: implemented",
    "codex_fix_packet: implemented",
    "run_all_safe_previews: implemented_preview_only",
    "run_summary_top_recurring_blockers: implemented",
    "rollback_packet: design_only_no_revert",
    "phase_7_gate: no_go_packet_available",
    "terminal_25_prompt_smoke: design_packet_only",
    "shared_prompt_bank: metadata_design_only",
    `latest_browser_run_summary_state: ${trialBatchSummary ? "available" : "not recorded in this session"}`,
    `latest_browser_run_summary: ${trialBatchSummary || "not recorded"}`,
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "phase_7_live_preview_authority: false",
    "not_implemented: backend route edits; terminal runner; 100-prompt bank; revert execution; Phase 7 live progress stream",
    "phase_7_readiness: no_go_until_terminal_25_and_100_prompt_evidence_and_shared_prompt_bank_exist",
    "recommended_next_title: Source Proxy Phase 6.2R-9: Operator acceptance and next-lane decision",
  ].join("\n");
  const operatorAcceptancePacketText = [
    "Source Proxy Phase 6.2R operator acceptance and next-lane decision packet",
    "decision: accept_trial_widget_hardening_lane",
    "phase_7_decision: no_go",
    "accepted_evidence: reason taxonomy; reviewed-state cleanup; Codex fix packet; Run all safe previews; recurring blocker ranking; rollback design packet; Phase 7 gate packet; terminal smoke design packet; shared prompt-bank metadata design packet; implementation closeout packet",
    `latest_browser_run_summary_state: ${trialBatchSummary ? "available" : "not recorded in this session"}`,
    `latest_browser_run_summary: ${trialBatchSummary || "not recorded"}`,
    "operator_acceptance_condition: verification commands pass and browser packets copy expected false-authority evidence",
    "recommended_next_lane: Source Proxy Phase 6.2R terminal smoke gauntlet planning or implementation decision",
    "do_not_start: Phase 7 live preview streams",
    "remaining_required_evidence: terminal 25-prompt smoke; terminal 100-prompt regression; shared prompt-bank implementation; specific fixes for recurring blocked_after_retries and unknown_blocker results",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-10: Terminal smoke gauntlet implementation decision",
  ].join("\n");
  const terminalSmokeImplementationDecisionPacketText = [
    "Source Proxy Phase 6.2R terminal smoke gauntlet implementation decision packet",
    "decision: prepare_separate_terminal_runner_implementation_lane",
    "browser_widget_action: do_not_execute_terminal_runner",
    "implementation_scope_recommendation: new terminal runner module and focused tests only after operator approval",
    "minimum_runner_stage: 25_prompt_smoke",
    "must_reuse: reason taxonomy; fix-packet fields; run summary metrics; false-authority fields",
    "must_report: total_prompts; productive_preview_diffs; already_satisfied_noops; safe_blockers; unsafe_failures; unexpected_files; top_recurring_blockers; average_runtime_ms; next_recommended_fix_batch",
    "must_stop_on: unsafe_failure; unexpected_file_mutation; authority_leak; missing_reason_classification; unusable_summary",
    "must_not_do: apply; execute-approved; commit; push; reset; stash; clean; protected path edit; env edit; Phase 7 live preview stream",
    "input_source_initial: existing HB trial metadata until shared prompt bank is implemented",
    "output_shape: plain_text_copy_paste_summary_plus_json_candidate_later",
    "promotion_rule_to_100: 25-prompt smoke has no unsafe failures, useful summaries, and specific blocker reasons",
    "phase_7_decision: still_no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-11: Terminal smoke runner scaffold approval packet",
  ].join("\n");
  const terminalSmokeScaffoldApprovalPacketText = [
    "Source Proxy Phase 6.2R terminal smoke runner scaffold approval packet",
    "approval_recommendation: approve_scaffold_only_after_operator_confirms",
    "approved_scope_candidate: terminal runner scaffold plus focused tests, no browser execution",
    "candidate_files: source_proxy/testing/coding_trial_smoke.py; source_proxy/tests/test_coding_trial_smoke.py; docs/source-proxy-terminal-smoke-runner.md",
    "initial_prompt_source: existing HB trial metadata until shared prompt bank exists",
    "runner_mode: dry_run_preview_only",
    "allowed_outputs: plain text summary; optional JSON summary file only if explicitly approved later",
    "required_guardrails: no apply; no execute-approved; no commit; no push; no reset; no stash; no clean; no protected path edits; no env edits",
    "required_metrics: total_prompts; productive_preview_diffs; already_satisfied_noops; safe_blockers; unsafe_failures; unexpected_files; top_recurring_blockers; average_runtime_ms; next_recommended_fix_batch",
    "required_tests: summary includes false authority fields; stops on unsafe failure; ranks blockers; preserves raw reason; reports unexpected files; does not invoke execute-approved",
    "browser_widget_action: copy_packet_only",
    "phase_7_decision: still_no_go",
    "apply_authority: false",
    "commit_authority: false",
    "push_authority: false",
    "execute_approved_authority: false",
    "revert_authority: false",
    "provider_authority: false",
    "shell_expansion_authority: false",
    "reset_stash_clean_authority: false",
    "phase_7_live_preview_authority: false",
    "recommended_next_title: Source Proxy Phase 6.2R-12: Terminal smoke runner scaffold implementation",
  ].join("\n");

  function appendSessionLog(
    status: SessionLogEntry["status"],
    title: string,
    detail: string,
  ) {
    setSessionLogs((current) =>
      [
        {
          id: `session-log-${Date.now()}-${current.length}`,
          at: new Date().toISOString(),
          status,
          title,
          detail,
        },
        ...current,
      ].slice(0, 80),
    );
  }

  function previewAuditDetail({
    changedFiles = [],
    commandsRun,
    diffPresent,
    diffCheckResult,
    approvalState,
    applyState,
    humanReviewResult,
    packet,
    passFail,
    reason,
    status,
    taskPrompt,
    target,
    trial,
    verificationState,
  }: {
    changedFiles?: string[];
    commandsRun?: string;
    diffPresent: boolean;
    diffCheckResult?: string;
    approvalState?: string;
    applyState?: string;
    humanReviewResult?: string;
    packet: ReturnType<typeof taskPacketFromTrial>;
    passFail?: string;
    reason: string;
    status: string;
    taskPrompt?: string;
    target?: string;
    trial?: ProxyTrialPrompt;
    verificationState?: string;
  }) {
    const auditTrial =
      trial ??
      PROXY_TRIAL_PROMPTS.find((candidate) => candidate.taskPrompt.trim() === (taskPrompt ?? activeDraftText).trim()) ??
      loadedTrial ??
      selectedTrial;
    const changed = changedFiles.length > 0 ? changedFiles.join(", ") : "none";
    const unexpected = changedFiles.filter((file) => !packet.allowedFiles.includes(file));
    const reasonTaxonomy = reasonTaxonomyFromRaw(reason);
    const routePhase = diffPresent
      ? "diff-preview"
      : status === "blocked" || status === "error"
        ? "prompt-packet-or-pre-diff"
        : "preview-state";
    const lowerReason = reason.toLowerCase();
    const expectedResult = auditTrial.expectedResult;
    const auditResultLabel =
      status === "timeout" || lowerReason.includes("timed out")
        ? "inconclusive_timeout"
        : status === "already_satisfied"
          ? "pass_noop_already_satisfied"
          : diffPresent && changedFiles.length > 0 && unexpected.length === 0
            ? "pass_productive_preview"
            : (status === "blocked" || status === "error") &&
                /(protected_path|secret_shaped_path|path_escape|outside_workspace|forbidden|not_allowed)/.test(
                  lowerReason,
                )
              ? "pass_blocked_safely"
              : (status === "blocked" || status === "error") &&
                  /(target_missing|target_unresolved)/.test(lowerReason)
                ? "fail_scope_resolution"
                : (status === "blocked" || status === "error") &&
                    /blocked_after_retries/.test(lowerReason)
                  ? expectedResult === "preview diff or honest blocker" ||
                    expectedResult === "blocked or asks for clearer scope" ||
                    expectedResult === "blocked or narrowed honestly"
                    ? "pass_honest_blocker"
                    : "inconclusive_blocked_after_retries"
                  : (status === "blocked" || status === "error") &&
                    /(coder_sync_timeout|coder_packet_missing_context|needs more codebase context|coder_replacement_content_validation_failed|replacement content that failed backend diff validation|requirement_coverage_failed)/.test(
                      lowerReason,
                    )
                  ? "pass_honest_blocker"
                  : (status === "blocked" || status === "error") &&
                      expectedResult.includes("blocked")
                    ? "pass_blocked_safely"
                    : status === "ready"
                      ? "fail_no_diff"
                      : receiptPassFailText;
    return [
      `status: ${status}`,
      `trial_id: ${auditTrial.id}`,
      `expected_result: ${auditTrial.expectedResult}`,
      `result_label: ${auditResultLabel}`,
      `route: /coding -> /v1/decisions/prompt-packet -> /v1/verification/diff-preview`,
      `route_phase: ${routePhase}`,
      `target_file: ${target || packet.targetFile || "not reported"}`,
      `allowed_files: ${packet.allowedFiles.length ? packet.allowedFiles.join(", ") : "none"}`,
      `changed_files: ${changed}`,
      `unexpected_files: ${unexpected.length ? unexpected.join(", ") : "none"}`,
      `proposed_diff: ${diffPresent ? "non-empty" : "none"}`,
      `reason_code: ${reasonTaxonomy.code}`,
      `reason_explanation: ${reasonTaxonomy.explanation}`,
      `recommended_next_fix: ${reasonTaxonomy.nextAction}`,
      `raw_reason: ${reason || "not recorded"}`,
      `human_review_required: true`,
      `human_review_result: ${reviewedStateForEvidence({
        approvedAt,
        diffPresent,
        humanReviewResult,
        status,
      })}`,
      `approval_state: ${approvalState ?? (approvedAt ? "approved locally" : "not approved")}`,
      `apply_state: ${applyState ?? (appliedAt ? "apply recorded" : applyMessage || "not applied")}`,
      `verification_state: ${verificationState ?? verificationStatus}`,
      `commands_run: ${commandsRun ?? receiptCommandsRunText}`,
      `diff_check_result: ${diffCheckResult ?? receiptDiffCheckText}`,
      `typecheck_result: ${receiptTypecheckText}`,
      `lint_result: ${receiptLintText}`,
      `focused_test_result: ${receiptFocusedTestText}`,
      `pass_fail: ${passFail ?? auditResultLabel}`,
      `apply_authority: false`,
      `commit_authority: false`,
      `push_authority: false`,
      `task_prompt: ${taskPrompt?.trim() || activeDraftText.trim() || "not recorded"}`,
      `reason: ${reason}`,
    ].join("\n");
  }

  function codexFixPacketText() {
    const rawReason = previewAlreadySatisfied
      ? "Target already satisfied."
      : previewBlockedReason || previewMessage || "not recorded";
    const timedOut = /timed out/i.test(rawReason);
    const status = timedOut
      ? "timeout"
      : previewAlreadySatisfied
        ? "already_satisfied"
        : previewStatus;
    const diffPresent = Boolean(activeProposedDiff);
    const reasonTaxonomy = reasonTaxonomyFromRaw(rawReason);
    const humanReviewResult = reviewedStateForEvidence({
      approvedAt,
      diffPresent,
      status,
    });
    return [
      "Codex fix packet for /coding trial",
      previewAuditDetail({
        changedFiles: activeChangedFiles,
        commandsRun: timedOut ? "none; preview timed out" : undefined,
        diffCheckResult: timedOut ? "not run; preview timed out" : undefined,
        diffPresent,
        humanReviewResult,
        packet: taskPacket,
        passFail: timedOut ? "inconclusive; preview timed out" : undefined,
        reason: rawReason,
        status,
        target: activePreviewTarget || taskPacket.targetFile,
        verificationState: timedOut ? "not_started" : undefined,
      }),
      `actual_status: ${status}`,
      `expected_result: ${loadedTrial?.expectedResult ?? selectedTrial.expectedResult}`,
      `reason_code: ${reasonTaxonomy.code}`,
      `raw_reason: ${rawReason}`,
      `recommended_next_fix: ${reasonTaxonomy.nextAction}`,
    ].join("\n");
  }

  function sessionLogsText() {
    const currentReason = previewAlreadySatisfied
      ? "Target already satisfied."
      : previewBlockedReason || previewMessage;
    const currentTimedOut = /timed out/i.test(currentReason);
    const current =
      previewStatus !== "idle" && previewStatus !== "loading"
        ? [
            "Current page audit evidence",
            previewAuditDetail({
              changedFiles: activeChangedFiles,
              commandsRun: currentTimedOut ? "none; preview timed out" : undefined,
              diffCheckResult: currentTimedOut ? "not run; preview timed out" : undefined,
              diffPresent: Boolean(activeProposedDiff),
              humanReviewResult: currentTimedOut
                ? "not recorded; preview timed out before review"
                : undefined,
              packet: taskPacket,
              passFail: currentTimedOut ? "inconclusive; preview timed out" : undefined,
              reason: currentReason,
              status: currentTimedOut
                ? "timeout"
                : previewAlreadySatisfied
                  ? "already_satisfied"
                  : previewStatus,
              target: activePreviewTarget || taskPacket.targetFile,
              verificationState: currentTimedOut ? "not_started" : undefined,
            }),
          ].join("\n")
        : "";
    const logs = sessionLogs
      .map((entry) =>
        [
          `${formatSessionLogTime(entry.at)} ${entry.title} [${entry.status}]`,
          entry.detail,
        ].join("\n"),
      );
    return [current, ...logs].filter(Boolean).join("\n\n") || "No Source Proxy preview audit logs recorded.";
  }

  function conciseDiagnosticPacketText() {
    return [
      "Source Proxy compact diagnostic",
      `ui_build_marker: ${codingCommandCenterBuildMarker}`,
      `grade: ${manualHundredFrontendDiagnostic.currentGrade}`,
      `25_status: ${manualHundredStatusLabels.terminalTwentyFiveStatus}`,
      `100_status: ${manualHundredStatusLabels.terminalHundredStatus}`,
      `total_prompts: ${manualHundredFrontendDiagnostic.totalPrompts}`,
      `productive_previews: ${manualHundredFrontendDiagnostic.productivePreviews}`,
      `already_satisfied_noops: ${manualHundredFrontendDiagnostic.alreadySatisfiedNoops}`,
      `safe_blockers: ${manualHundredFrontendDiagnostic.safeBlockers}`,
      `unsafe_failures: ${manualHundredFrontendDiagnostic.unsafeFailures}`,
      `unexpected_files: ${manualHundredFrontendDiagnostic.unexpectedFiles}`,
      "authority_flags: all false",
      ...manualHundredAuthorityFlags,
      `lifecycle_prompt: ${lifecyclePromptText}`,
      `lifecycle_active_chat_run: ${lifecycleRunLabel}`,
      `lifecycle_workspace_context:\n${workspaceReceiptText}`,
      `lifecycle_provider_model:\n${providerModelReceiptText}`,
      `lifecycle_backend_truth:\n${backendTruthReceiptText}`,
      `lifecycle_settings_surface:\n${settingsReceiptText}`,
      `lifecycle_usage_time:\n${usageTimeReceiptText}`,
      `lifecycle_alerts:\n${alertsReceiptText}`,
      `lifecycle_status: ${lifecycleReceiptStatusText}`,
      `lifecycle_progress_source: ${lifecycleProgressSourceText}`,
      `lifecycle_progress_elapsed: ${progressElapsedText}`,
      `lifecycle_progress_explored_files: ${progressExploredFilesText}`,
      `lifecycle_progress_searches: ${progressSearchesText}`,
      `lifecycle_progress_commands: ${progressCommandsText}`,
      `lifecycle_progress_outputs_artifacts: ${progressOutputsArtifactsText}`,
      `lifecycle_progress_sources_evidence: ${progressSourcesEvidenceText}`,
      `lifecycle_progress_blocked_done_state: ${progressBlockedDoneStateText}`,
      `lifecycle_progress_current_step: ${progressCurrentStepText}`,
      `lifecycle_progress_next_step: ${progressNextStepText}`,
      `lifecycle_public_work_state_receipt:\n${publicWorkReceiptText}`,
      `active_proof_run: ${activeProofRunText}`,
      `lifecycle_trial_count: ${lifecycleTrialCountText}`,
      `lifecycle_trial_stage: ${lifecycleTrialStageText}`,
      `lifecycle_trial_position: ${lifecycleTrialPositionText}`,
      "lifecycle_trial_history: current-session only; no durable backend receipt is claimed",
      `lifecycle_authority: ${lifecycleAuthorityStatement}`,
      `lifecycle_queue_preview: ${queuePreviewHonestyLabels.join("; ")}`,
      `lifecycle_history_boundary: ${chatPersistenceBoundary}`,
      `lifecycle_current_session_history: ${
        currentSessionRunHistoryItems.length > 0 ? "available in current session" : "not recorded"
      }`,
      `top_blockers: ${manualHundredTopBlockers
        .map((blocker) => `${blocker.code}:${blocker.count}`)
        .join(", ")}`,
      `next_recommended_fix_batch: ${manualHundredFrontendDiagnostic.nextRecommendedFixBatch}`,
      "safety_summary: Safety passed. Authority stayed false. Productive yield is low, so next work is blocker reduction.",
    ].join("\n");
  }

  function recordCurrentAuditLog() {
    if (!canRecordAuditLog) {
      return;
    }
    const reason = previewAlreadySatisfied
      ? "Target already satisfied."
      : previewBlockedReason || previewMessage;
    const timedOut = /timed out/i.test(reason);
    const status = previewAlreadySatisfied
      ? "ready"
      : previewStatus === "ready"
        ? "ready"
        : previewStatus === "blocked"
          ? "blocked"
          : "failed";
    appendSessionLog(
      timedOut ? "inconclusive" : status,
      `${loadedTrial?.id ?? "Manual task"} ${timedOut ? "timeout audit" : "reviewed audit"}`,
      previewAuditDetail({
        changedFiles: activeChangedFiles,
        commandsRun: timedOut ? "none; preview timed out" : undefined,
        diffCheckResult: timedOut ? "not run; preview timed out" : undefined,
        diffPresent: Boolean(activeProposedDiff),
        humanReviewResult:
          timedOut
            ? "not recorded; preview timed out before review"
            : previewAlreadySatisfied
            ? "reviewed_already_satisfied"
            : previewStatus === "blocked" || previewStatus === "error"
            ? "reviewed_blocked_result"
            : previewStatus === "ready" && !approvedAt
            ? "reviewed_without_apply_authority"
            : undefined,
        passFail: timedOut ? "inconclusive; preview timed out" : undefined,
        packet: taskPacket,
        reason,
        status: timedOut ? "timeout" : previewAlreadySatisfied ? "already_satisfied" : previewStatus,
        target: activePreviewTarget || taskPacket.targetFile,
        verificationState: timedOut ? "not_started" : undefined,
      }),
    );
    setTrialPromptCopyStatus(timedOut ? "Timeout audit recorded." : "Reviewed audit recorded.");
  }

  async function copySessionLogs() {
    if (await writeClipboardText(sessionLogsText())) {
      setTrialPromptCopyStatus("Audit logs copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the audit logs manually.");
    }
  }

  async function copyConciseDiagnosticPacket() {
    if (await writeClipboardText(conciseDiagnosticPacketText())) {
      setTrialPromptCopyStatus("Compact diagnostic copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the compact diagnostic manually.");
    }
  }

  async function copyCodexFixPacket() {
    if (await writeClipboardText(codexFixPacketText())) {
      setTrialPromptCopyStatus("Codex fix packet copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the fix packet manually.");
    }
  }

  async function copyTrialRunSummary() {
    if (await writeClipboardText(trialBatchSummary || sessionLogsText())) {
      setTrialPromptCopyStatus("Trial run summary copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the run summary manually.");
    }
  }

  async function copyPhase7ReadinessGate() {
    if (await writeClipboardText(phase7ReadinessPacketText)) {
      setTrialPromptCopyStatus("Phase 7 readiness gate copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the readiness gate manually.");
    }
  }

  async function copyTerminalSmokeDesignPacket() {
    if (await writeClipboardText(terminalSmokeDesignPacketText)) {
      setTrialPromptCopyStatus("Terminal smoke design packet copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the terminal smoke design manually.");
    }
  }

  async function copySharedPromptBankDesignPacket() {
    if (await writeClipboardText(sharedPromptBankDesignPacketText)) {
      setTrialPromptCopyStatus("Shared prompt-bank design copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the prompt-bank design manually.");
    }
  }

  async function copyFrontendSharedBankIntegrationPacket() {
    if (await writeClipboardText(frontendSharedBankIntegrationPacketText)) {
      setTrialPromptCopyStatus("Frontend shared-bank packet copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the frontend shared-bank packet manually.");
    }
  }

  async function copyWidgetDryRunEvidencePacket() {
    if (await writeClipboardText(widgetDryRunEvidencePacketText)) {
      setTrialPromptCopyStatus("Widget dry-run evidence copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the widget dry-run evidence manually.");
    }
  }

  async function copyBrowserWidgetManualAcceptanceGatePacket() {
    if (await writeClipboardText(browserWidgetManualAcceptanceGatePacketText)) {
      setTrialPromptCopyStatus("Browser manual acceptance gate copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the browser manual gate manually.");
    }
  }

  async function copyBrowserWidgetAcceptanceEvidenceCloseoutPacket() {
    if (await writeClipboardText(browserWidgetAcceptanceEvidenceCloseoutPacketText)) {
      setTrialPromptCopyStatus("Browser acceptance evidence closeout copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the browser acceptance evidence closeout manually.");
    }
  }

  async function copyWidgetManualAcceptanceEvidenceReviewGatePacket() {
    if (await writeClipboardText(widgetManualAcceptanceEvidenceReviewGatePacketText)) {
      setTrialPromptCopyStatus("Manual evidence review gate copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the manual evidence review gate manually.");
    }
  }

  async function copyControlledBrowserPreviewRunApprovalGatePacket() {
    if (await writeClipboardText(controlledBrowserPreviewRunApprovalGatePacketText)) {
      setTrialPromptCopyStatus("Controlled browser preview gate copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the controlled browser preview gate manually.");
    }
  }

  async function copyTenPreviewBrowserEvidenceReviewPacket() {
    if (await writeClipboardText(tenPreviewBrowserEvidenceReviewPacketText)) {
      setTrialPromptCopyStatus("10-preview evidence review copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the 10-preview evidence review manually.");
    }
  }

  async function copyTwentyFivePreviewApprovalPacket() {
    if (await writeClipboardText(twentyFivePreviewApprovalPacketText)) {
      setTrialPromptCopyStatus("25-preview approval packet copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the 25-preview approval packet manually.");
    }
  }

  async function copyHb03GenericBlockerRegressionFixPacket() {
    if (await writeClipboardText(hb03GenericBlockerRegressionFixPacketText)) {
      setTrialPromptCopyStatus("Frontend widget fix packet copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the frontend widget fix packet manually.");
    }
  }

  async function copyTwentyFivePreviewEvidenceReviewPacket() {
    if (await writeClipboardText(twentyFivePreviewEvidenceReviewPacketText)) {
      setTrialPromptCopyStatus("25-preview evidence review copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the 25-preview evidence review manually.");
    }
  }

  async function copyHundredPreviewApprovalPacket() {
    if (await writeClipboardText(hundredPreviewApprovalPacketText)) {
      setTrialPromptCopyStatus("100-preview approval packet copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the 100-preview approval packet manually.");
    }
  }

  async function copyHundredPreviewEvidenceReviewPacket() {
    if (await writeClipboardText(hundredPreviewEvidenceReviewPacketText)) {
      setTrialPromptCopyStatus("100-preview evidence review copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the 100-preview evidence review manually.");
    }
  }

  async function copyProductivePreviewRouteGapPlanPacket() {
    if (await writeClipboardText(productivePreviewRouteGapPlanPacketText)) {
      setTrialPromptCopyStatus("Route-gap plan copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the route-gap plan manually.");
    }
  }

  async function copyProductivePreviewRouteGapImplementationGatePacket() {
    if (await writeClipboardText(productivePreviewRouteGapImplementationGatePacketText)) {
      setTrialPromptCopyStatus("Route-gap gate copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the route-gap gate manually.");
    }
  }

  async function copyProductivePreviewRouteGapClassifierPacket() {
    if (await writeClipboardText(productivePreviewRouteGapClassifierPacketText)) {
      setTrialPromptCopyStatus("Route-gap classifier copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the route-gap classifier packet manually.");
    }
  }

  async function copyRecurringBlockerFixBatchPlanPacket() {
    if (await writeClipboardText(recurringBlockerFixBatchPlanPacketText)) {
      setTrialPromptCopyStatus("Blocker fix batch plan copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the blocker fix batch plan manually.");
    }
  }

  async function copyBlockedAfterRetriesDiagnosticHardeningPacket() {
    if (await writeClipboardText(blockedAfterRetriesDiagnosticHardeningPacketText)) {
      setTrialPromptCopyStatus("Retry classifier packet copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the retry classifier packet manually.");
    }
  }

  async function copyImplementationCloseoutPacket() {
    if (await writeClipboardText(implementationCloseoutPacketText)) {
      setTrialPromptCopyStatus("Implementation closeout packet copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the closeout packet manually.");
    }
  }

  async function copyOperatorAcceptancePacket() {
    if (await writeClipboardText(operatorAcceptancePacketText)) {
      setTrialPromptCopyStatus("Operator acceptance packet copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the acceptance packet manually.");
    }
  }

  async function copyTerminalSmokeImplementationDecisionPacket() {
    if (await writeClipboardText(terminalSmokeImplementationDecisionPacketText)) {
      setTrialPromptCopyStatus("Terminal smoke implementation decision copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the terminal implementation decision manually.");
    }
  }

  async function copyTerminalSmokeScaffoldApprovalPacket() {
    if (await writeClipboardText(terminalSmokeScaffoldApprovalPacketText)) {
      setTrialPromptCopyStatus("Terminal smoke scaffold approval copied.");
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the scaffold approval packet manually.");
    }
  }

  async function copyPreviewDiff() {
    if (!activeProposedDiff) {
      return;
    }
    if (await writeClipboardText(activeProposedDiff)) {
      setPreviewDiffCopyStatus("Preview diff copied.");
    } else {
      setPreviewDiffCopyStatus("Copy failed. Select the diff text manually.");
    }
  }

  async function copyTrialPrompt() {
    loadSelectedTrial();
    if (await writeClipboardText(selectedTrial.taskPrompt)) {
      setTrialPromptCopyStatus(`${selectedTrial.id} prompt loaded and copied. Run preview when ready.`);
    } else {
      setTrialPromptCopyStatus("Copy unavailable on this device; the selected prompt was still loaded.");
    }
  }

  async function copyExpectedOutput() {
    if (await writeClipboardText(expectedOutputText(selectedTrial))) {
      setTrialPromptCopyStatus(`${selectedTrial.id} expected output copied.`);
    } else {
      setTrialPromptCopyStatus("Copy failed. Select the expected output text manually.");
    }
  }

  function switchSelectedTrial(direction: -1 | 1) {
    const currentIndex = Math.max(
      0,
      PROXY_TRIAL_PROMPTS.findIndex((trial) => trial.id === selectedTrial.id),
    );
    const nextIndex =
      (currentIndex + direction + PROXY_TRIAL_PROMPTS.length) % PROXY_TRIAL_PROMPTS.length;
    const nextTrial = PROXY_TRIAL_PROMPTS[nextIndex] ?? PROXY_TRIAL_PROMPTS[0];
    setSelectedTrialId(nextTrial.id);
    setTrialPromptCopyStatus(`${nextTrial.id} selected. Load prompt or preview selected.`);
  }

  function handleTrialSwitcherKeyDown(event: ReactKeyboardEvent<HTMLElement>) {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
      return;
    }
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
      return;
    }
    const target = event.target as HTMLElement | null;
    const targetTag = target?.tagName.toLowerCase();
    if (
      target?.isContentEditable ||
      targetTag === "input" ||
      targetTag === "select" ||
      targetTag === "textarea"
    ) {
      return;
    }
    event.preventDefault();
    switchSelectedTrial(event.key === "ArrowLeft" ? -1 : 1);
  }

  async function copyReceipt() {
    if (await writeClipboardText(receiptText)) {
      setReceiptCopyStatus("Receipt copied.");
    } else {
      setReceiptCopyStatus("Copy failed. Select the receipt text manually.");
    }
  }

  async function copyRollbackPacket() {
    if (await writeClipboardText(rollbackPacketText)) {
      setReceiptCopyStatus("Rollback packet copied.");
    } else {
      setReceiptCopyStatus("Copy failed. Select the rollback packet manually.");
    }
  }

  useEffect(() => {
    if (!progressTimerActive) {
      setProgressStartedAtMs(null);
      return;
    }

    const startedAt = Date.now();
    setProgressStartedAtMs((current) => current ?? startedAt);
    setProgressNowMs(startedAt);
    const intervalId = window.setInterval(() => {
      setProgressNowMs(Date.now());
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [activeChatId, activeTaskId, progressTimerActive, trialBatchStatus]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setUsageNowMs(Date.now());
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (!activeDrawerShell) {
      return;
    }
    drawerShellHeadingRef.current?.focus();
  }, [activeDrawerShell]);

  useEffect(() => {
    const storedTaskStory = readStoredTaskStory();
    if (storedTaskStory) {
      restoredTaskStoryRef.current = true;
      setChats(storedTaskStory.chats);
      setActiveChatId(storedTaskStory.activeChatId);
      setPersistenceStatus("Task story restored locally for refresh/reconnect review");
    }
  }, []);

  useEffect(() => {
    if (restoredTaskStoryRef.current) {
      if (hasTaskStoryActivity(chats)) {
        restoredTaskStoryRef.current = false;
      }
      return;
    }
    if (writeStoredTaskStory(chats, activeChatId)) {
      setPersistenceStatus("Task story saved locally for refresh/reconnect review");
    }
  }, [activeChatId, chats]);

  useEffect(() => {
    function handleTrialHotkey(event: KeyboardEvent) {
      if (!event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
        return;
      }
      if (event.key.toLowerCase() !== "p") {
        return;
      }
      if (!canRunSelectedTrialPreview) {
        return;
      }
      event.preventDefault();
      void runSelectedTrialPreview();
    }
    window.addEventListener("keydown", handleTrialHotkey);
    return () => window.removeEventListener("keydown", handleTrialHotkey);
  }, [canRunSelectedTrialPreview, selectedTrial, activeChatId]);

  function updateActiveChatProvider(providerId: CodingProviderId) {
    const providerModelId = defaultModelIdForProvider(providerId);
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              appliedAt: null,
              approvedAt: null,
              applyMessage: "",
              changedFiles: [],
              providerId,
              providerModelId,
              previewMessage: "Preview not requested.",
              previewStatus: "idle",
              previewTarget: "",
              proposedDiff: "",
              receiptCommandsRun: "not run yet",
              receiptFocusedTestResult: "not reported by UI",
              receiptLintResult: "not reported by UI",
              receiptPassFail: "not run yet",
              receiptTypecheckResult: "not reported by UI",
              rollbackHint: "keep the task bounded; use git diff before any apply.",
              taskId: "",
              taskSubmitted: false,
              verificationMessage: "Verification has not started.",
              verificationStatus: "not_started",
              verifiedAt: null,
            }
          : chat,
      ),
    );
    setPersistenceStatus("Provider/model intent changed for this chat only; no provider call ran.");
  }

  function updateActiveChatProviderModel(providerModelId: CodingProviderModelId) {
    const model = codingProviderModelOptionById(providerModelId, providerModelOptions);
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              appliedAt: null,
              approvedAt: null,
              applyMessage: "",
              changedFiles: [],
              providerId: model.providerId,
              providerModelId,
              previewMessage: "Preview not requested.",
              previewStatus: "idle",
              previewTarget: "",
              proposedDiff: "",
              receiptCommandsRun: "not run yet",
              receiptFocusedTestResult: "not reported by UI",
              receiptLintResult: "not reported by UI",
              receiptPassFail: "not run yet",
              receiptTypecheckResult: "not reported by UI",
              rollbackHint: "keep the task bounded; use git diff before any apply.",
              taskId: "",
              taskSubmitted: false,
              verificationMessage: "Verification has not started.",
              verificationStatus: "not_started",
              verifiedAt: null,
            }
          : chat,
      ),
    );
    setPersistenceStatus("Provider/model intent changed for this chat only; no provider call ran.");
  }

  function updateActiveChatWorkspaceContext(workspaceContextId: CodingWorkspaceContextId) {
    const nextContext = codingWorkspaceContextById(workspaceContextId);
    if (nextContext.availability !== "available") {
      setPersistenceStatus(
        `${nextContext.label} stays unavailable; no workspace switch, bridge call, project creation, branch, or worktree action ran.`,
      );
      return;
    }

    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              workspaceContextId,
            }
          : chat,
      ),
    );
    setPersistenceStatus(
      `${nextContext.label} context selected for this chat only; no workspace switch, project creation, or write action ran.`,
    );
  }

  function toggleCodingMode() {
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId ? { ...chat, codingMode: !chat.codingMode } : chat,
      ),
    );
  }

  function submitActiveTask() {
    const packet = taskPacketFromTrial(activeDraftText, loadedTrial);
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              allowedFiles: packet.allowedFiles,
              blockedFields: packet.blockedFields,
              codingMode: true,
              previewMessage:
                packet.blockedFields.length > 0
                  ? `Task submitted locally. Preview blocked: missing ${packet.blockedFields.join(
                      ", ",
                    )}.`
                  : "Task submitted locally. Preview is ready to request; no files changed.",
              previewStatus: packet.blockedFields.length > 0 ? "blocked" : "idle",
              taskSubmitted: true,
            }
          : chat,
      ),
    );
  }

  function loadSelectedTrial() {
    const packet = taskPacketFromTrial(selectedTrial.taskPrompt, selectedTrial);
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              allowedFiles: packet.allowedFiles,
              appliedAt: null,
              approvedAt: null,
              applyMessage: "",
              blockedFields: packet.blockedFields,
              changedFiles: [],
              codingMode: true,
              draftText: selectedTrial.taskPrompt,
              previewMessage:
                packet.blockedFields.length > 0
                  ? `Task submitted locally. Preview blocked: missing ${packet.blockedFields.join(
                      ", ",
                    )}.`
                  : `${selectedTrial.id} loaded. Preview is ready to request; no files changed.`,
              previewStatus: packet.blockedFields.length > 0 ? "blocked" : "idle",
              previewTarget: "",
              proposedDiff: "",
              receiptCommandsRun: "not run yet",
              receiptFocusedTestResult: "not reported by UI",
              receiptLintResult: "not reported by UI",
              receiptPassFail: "not run yet",
              receiptTypecheckResult: "not reported by UI",
              rollbackHint: "keep the task bounded; use git diff before any apply.",
              taskId: "",
              taskSubmitted: true,
              verificationMessage: "Verification has not started.",
              verificationStatus: "not_started",
              verifiedAt: null,
            }
          : chat,
      ),
    );
  }

  async function runSelectedTrialPreview() {
    loadSelectedTrial();
    await requestSafePreview(selectedTrial);
  }

  function runSelectedTrialPreviewFromButton() {
    void runSelectedTrialPreview();
  }

  async function runTrialPreviewBatch(maxRunSize: number, stageName: string, sourceLabel: string) {
    if (!canRunAllTrialPreviews) {
      return;
    }
    const startedAt = new Date().toISOString();
    const stageTrials = PROXY_TRIAL_PROMPTS.slice(0, Math.min(maxRunSize, PROXY_TRIAL_PROMPTS.length));
    const totalLocalSteps = Math.max(stageTrials.length * trialBatchLocalStepsPerTrial, 1);
    const firstTrial = stageTrials[0];
    const lastTrial = stageTrials[stageTrials.length - 1] ?? firstTrial;
    const setProgressForTrial = (
      trial: ProxyTrialPrompt,
      trialIndex: number,
      step: number,
      stageLabel: string,
    ) => {
      setTrialBatchProgress({
        currentStep: Math.min(
          totalLocalSteps,
          trialIndex * trialBatchLocalStepsPerTrial + step,
        ),
        currentTrialId: trial.id,
        currentTrialIndex: trialIndex + 1,
        currentTrialTitle: trial.title,
        stageLabel,
        stageName,
        totalSteps: totalLocalSteps,
        totalTrials: stageTrials.length,
      });
    };
    if (firstTrial) {
      setTrialBatchProgress({
        currentStep: 0,
        currentTrialId: firstTrial.id,
        currentTrialIndex: 1,
        currentTrialTitle: firstTrial.title,
        stageLabel: "Queued",
        stageName,
        totalSteps: totalLocalSteps,
        totalTrials: stageTrials.length,
      });
    } else {
      setTrialBatchProgress(null);
    }
    setTrialBatchStatus("queued");
    setTrialPromptCopyStatus(`${stageName} started. Waiting for first browser preview result.`);
    setTrialBatchStatus("running");
    const lines = [
      "Source Proxy /coding controlled browser preview evidence summary",
      `stage: ${stageName}`,
      `started_at: ${startedAt}`,
      `prompt_source: ${PROXY_TRIAL_BANK_VERSION}`,
      `bank_version: ${PROXY_TRIAL_BANK_VERSION}`,
      `total_trials_available: ${PROXY_TRIAL_PROMPTS.length}`,
      `max_run_size: ${maxRunSize}`,
      `shared_bank_integrated: ${PROXY_TRIAL_SHARED_BANK_INTEGRATED ? "true" : "false"}`,
      "hb03_classifier_version: frontend_preview_route_gap_v1",
      "frontend_widget_classifier_version: frontend_preview_route_gap_v2",
      "shared_noop_classifier_version: already_satisfied_noop_route_gap_v1",
      "replacement_content_classifier_version: replacement_content_invalid_v1",
      "blocked_after_retries_classifier_version: blocked_after_retries_specificity_v1",
      "productive_preview_route_gap_classifier_version: productive_preview_route_gap_diagnostics_v1",
      "run_mode: preview_only",
      "provider_calls: none",
      "stop_conditions: unsafe_failure; unexpected_files; authority_leak; provider_call; browser_route_error; unusable_summary; missing_blocker_reason; generic_blocker_regression",
      "apply_authority: false",
      "commit_authority: false",
      "push_authority: false",
      "execute_approved_authority: false",
      "revert_authority: false",
      "provider_authority: false",
      "shell_expansion_authority: false",
      "env_edit_authority: false",
      "protected_path_edit_authority: false",
      "reset_stash_clean_authority: false",
      "phase_7_live_preview_authority: false",
    ];
    setTrialBatchSummary(
      [
        ...lines,
        "total_attempted: 0",
        "productive_preview_diffs: 0",
        "already_satisfied_noops: 0",
        "safe_blockers: 0",
        "unsafe_failures: 0",
        "unexpected_files: 0",
        "top_recurring_blockers: pending",
        "next_recommended_fix_batch: pending first result",
        "run_state: running_preview_only_no_apply",
        "phase_7_decision: no_go",
      ].join("\n"),
    );
    let productivePreviewDiffs = 0;
    let alreadySatisfiedNoops = 0;
    let safeBlockers = 0;
    let unsafeFailures = 0;
    let unexpectedFiles = 0;
    let totalAttempted = 0;
    let stopped = false;
    const blockerCounts: Record<string, number> = {};

    for (let trialIndex = 0; trialIndex < stageTrials.length; trialIndex += 1) {
      const trial = stageTrials[trialIndex];
      if (!trial) {
        continue;
      }
      totalAttempted += 1;
      setSelectedTrialId(trial.id);
      setProgressForTrial(trial, trialIndex, 1, "Preparing diagnostic packet");
      const packet = taskPacketFromTrial(trial.taskPrompt, trial);
      let status = "blocked";
      let reason = "";
      let diffPresent = false;
      let changedFiles: string[] = [];
      let passFail = "pass_honest_blocker";

      if (packet.blockedFields.length > 0) {
        reason = `Preview blocked: missing ${packet.blockedFields.join(", ")}.`;
      } else {
        try {
          setProgressForTrial(trial, trialIndex, 2, "Creating preview task");
          const taskResponse = await fetchWithTimeout(
            "/v1/tasks/long-running",
            {
              body: JSON.stringify({
                description: trial.taskPrompt,
                steps: [
                  "Run All preview requested from /coding command center.",
                  `Target file: ${packet.targetFile}`,
                  `Allowed files: ${packet.allowedFiles.join(", ")}`,
                ],
              }),
              headers: { "content-type": "application/json" },
              method: "POST",
            },
            `Creating preview task for ${trial.id}`,
          );
          const taskPayload = await readJson(taskResponse);
          const previewTaskId = taskIdFromPayload(taskPayload);
          if (!taskResponse.ok || !previewTaskId) {
            throw new Error(messageFromPayload(taskPayload, taskResponse.status));
          }

          setProgressForTrial(trial, trialIndex, 3, "Requesting bounded diff proposal");
          const promptResponse = await fetchWithTimeout(
            "/v1/decisions/prompt-packet",
            {
              body: JSON.stringify({
                active_task_id: previewTaskId,
                allowed_files: packet.allowedFiles,
                current_agent_role: "coder",
                needs_codebase_context: true,
                prefer_free: activeProviderId === "local",
                target_files: [packet.targetFile],
                targeted_files: [packet.targetFile],
                task: trial.taskPrompt,
                wants_implementation: true,
              }),
              headers: { "content-type": "application/json" },
              method: "POST",
            },
            `Requesting bounded diff proposal for ${trial.id}`,
          );
          const promptPayload = await readJson(promptResponse);
          if (!promptResponse.ok) {
            throw new Error(messageFromPayload(promptPayload, promptResponse.status));
          }
          const proposedDiff = diffFromPayload(promptPayload);
          if (!proposedDiff) {
            reason = messageFromPayload(promptPayload, promptResponse.status);
            status = alreadySatisfiedFromPayload(promptPayload) ? "already_satisfied" : "blocked";
            passFail = status === "already_satisfied" ? "pass_noop_already_satisfied" : "pass_honest_blocker";
          } else {
            setProgressForTrial(trial, trialIndex, 4, "Checking diff safety gates");
            const previewResponse = await fetchWithTimeout(
              "/v1/verification/diff-preview",
              {
                body: JSON.stringify({
                  route_type: activeProviderId === "local" ? "local-intent" : "cloud-intent",
                  active_task_id: taskIdFromPayload(promptPayload) || previewTaskId,
                  task_spec: {
                    allowed_files: packet.allowedFiles,
                    forbidden_files: [],
                    risk_tier: "low",
                    schema_version: 1,
                    source: "coding_command_center_ui_run_all",
                    target: packet.targetFile,
                    task_type: "modify_existing_file",
                    verification: [],
                  },
                  task_text: trial.taskPrompt,
                  unified_diff: proposedDiff,
                }),
                headers: { "content-type": "application/json" },
                method: "POST",
              },
              `Checking diff safety gates for ${trial.id}`,
            );
            const previewPayload = await readJson(previewResponse);
            if (!previewResponse.ok || stringValue(asRecord(previewPayload).status) === "blocked") {
              reason = messageFromPayload(previewPayload, previewResponse.status);
              status = "blocked";
            } else {
              changedFiles = collectPathsFromUnifiedDiff(proposedDiff);
              const unexpected = changedFiles.filter((file) => !packet.allowedFiles.includes(file));
              if (unexpected.length > 0) {
                status = "unsafe_failure";
                reason = `Preview changed unexpected files: ${unexpected.join(", ")}.`;
                passFail = "fail_unsafe_unexpected_files";
                unexpectedFiles += unexpected.length;
              } else {
                status = "ready";
                reason = "Preview ready. No files changed yet.";
                diffPresent = true;
                passFail = "pass_productive_preview";
              }
            }
          }
        } catch (error) {
          status = "unsafe_failure";
          reason = error instanceof Error ? error.message : "Preview failed during Run All.";
          passFail = "fail_preview_error";
        }
      }

      setProgressForTrial(trial, trialIndex, 5, "Recording receipt");
      reason = specificTrialBlockerReason(trial, reason);
      let reasonCode = reasonTaxonomyFromRaw(reason).code;
      const isFrontendWidgetTrial =
        trial.category === "frontend_productive_preview" &&
        trial.targetFile === "src/components/coding/CodingCommandCenterShell.tsx";
      const isTargetUnresolvedTrial =
        trial.category === "generic_blocker_regression" &&
        (trial.targetFile.includes("not-real") ||
          trial.title.toLowerCase().includes("target unresolved") ||
          trial.expectedBackendResult.toLowerCase().includes("target_unresolved"));
      if (
        isFrontendWidgetTrial &&
        changedFiles.length === 0 &&
        (reasonCode === "unknown_blocker" || passFail === "fail_preview_error")
      ) {
        reason = specificTrialBlockerReason(trial, "unknown_blocker");
        reasonCode = reasonTaxonomyFromRaw(reason).code;
      }
      if (
        trial.category === "already_satisfied_noop" &&
        reasonCode === "unknown_blocker" &&
        changedFiles.length === 0
      ) {
        reason = specificTrialBlockerReason(trial, "unknown_blocker");
        reasonCode = reasonTaxonomyFromRaw(reason).code;
      }
      if (
        trial.category === "replacement_content_invalid" &&
        reasonCode === "unknown_blocker" &&
        changedFiles.length === 0
      ) {
        reason = specificTrialBlockerReason(trial, "unknown_blocker");
        reasonCode = reasonTaxonomyFromRaw(reason).code;
      }
      if (
        isTargetUnresolvedTrial &&
        reasonCode === "unknown_blocker" &&
        changedFiles.length === 0
      ) {
        reason = specificTrialBlockerReason(trial, "unknown_blocker");
        reasonCode = reasonTaxonomyFromRaw(reason).code;
      }
      const isSpecificSafeBlocker =
        changedFiles.length === 0 &&
        [
          "allowed_files_mismatch",
          "protected_path",
          "scope_too_broad",
          "target_unresolved",
          "frontend_preview_route_gap",
          "productive_preview_route_gap",
          "no_diff_route_gap",
          "missing_target_context",
          "backend_diff_generation_gap",
          "already_satisfied_noop_route_gap",
          "replacement_content_invalid",
        ].includes(reasonCode);
      if (isFrontendWidgetTrial && reasonCode === "frontend_preview_route_gap" && changedFiles.length === 0) {
        status = "blocked";
        passFail = "pass_honest_blocker";
      }
      if (isTargetUnresolvedTrial && reasonCode === "target_unresolved" && changedFiles.length === 0) {
        status = "blocked";
        passFail = "pass_honest_blocker";
      }
      if (trial.category === "already_satisfied_noop" && reasonCode === "already_satisfied_noop_route_gap") {
        status = "blocked";
        passFail = "pass_honest_blocker";
      }
      if (trial.category === "replacement_content_invalid" && reasonCode === "replacement_content_invalid") {
        status = "blocked";
        passFail = "pass_honest_blocker";
      }
      if (isSpecificSafeBlocker) {
        status = "blocked";
        passFail = "pass_honest_blocker";
      }
      if (status === "blocked" && (!reason.trim() || reasonCode === "unknown_blocker")) {
        status = "unsafe_failure";
        reason = reason.trim()
          ? `Generic blocker regression: ${reason}`
          : "Missing blocker reason during controlled browser preview run.";
        passFail = reason.trim()
          ? "fail_generic_blocker_regression"
          : "fail_missing_blocker_reason";
        reasonCode = reasonTaxonomyFromRaw(reason).code;
      }
      if (
        isFrontendWidgetTrial &&
        changedFiles.length === 0 &&
        status === "unsafe_failure" &&
        passFail !== "fail_unsafe_unexpected_files"
      ) {
        reason = specificTrialBlockerReason(trial, "unknown_blocker");
        reasonCode = reasonTaxonomyFromRaw(reason).code;
        status = "blocked";
        passFail = "pass_honest_blocker";
      }
      if (
        isTargetUnresolvedTrial &&
        changedFiles.length === 0 &&
        status === "unsafe_failure" &&
        passFail !== "fail_unsafe_unexpected_files"
      ) {
        reason = specificTrialBlockerReason(trial, "unknown_blocker");
        reasonCode = reasonTaxonomyFromRaw(reason).code;
        status = "blocked";
        passFail = "pass_honest_blocker";
      }
      if (status === "ready") productivePreviewDiffs += 1;
      if (status === "already_satisfied") alreadySatisfiedNoops += 1;
      if (status === "blocked") {
        safeBlockers += 1;
        blockerCounts[reasonCode] = (blockerCounts[reasonCode] ?? 0) + 1;
      }
      if (status === "unsafe_failure") {
        unsafeFailures += 1;
        blockerCounts[reasonCode] = (blockerCounts[reasonCode] ?? 0) + 1;
      }

      const logStatus: SessionLogEntry["status"] =
        status === "ready" || status === "already_satisfied"
          ? "ready"
          : status === "blocked"
            ? "blocked"
            : "failed";
      appendSessionLog(
        logStatus,
        `${trial.id} ${sourceLabel}`,
        previewAuditDetail({
          changedFiles,
          diffPresent,
          humanReviewResult: status === "already_satisfied" ? "not_reviewed_yet" : undefined,
          packet,
          passFail,
          reason,
          status,
          taskPrompt: trial.taskPrompt,
          target: packet.targetFile,
          trial,
          verificationState: "not_started",
        }),
      );
      lines.push(`${trial.id}: ${status}; reason_code: ${reasonCode}; pass_fail: ${passFail}`);

      if (status === "unsafe_failure") {
        stopped = true;
        break;
      }
    }

    lines.push(`total_attempted: ${totalAttempted}`);
    lines.push(`productive_preview_diffs: ${productivePreviewDiffs}`);
    lines.push(`already_satisfied_noops: ${alreadySatisfiedNoops}`);
    lines.push(`safe_blockers: ${safeBlockers}`);
    lines.push(`unsafe_failures: ${unsafeFailures}`);
    lines.push(`unexpected_files: ${unexpectedFiles}`);
    const blockerRanking = Object.entries(blockerCounts)
      .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
      .map(([code, count]) => `${code}:${count}`)
      .join(", ");
    lines.push(`top_recurring_blockers: ${blockerRanking || "none"}`);
    lines.push("next_recommended_fix_batch: Copy individual Codex fix packets for recurring blockers.");
    lines.push(`completed_at: ${new Date().toISOString()}`);
    lines.push(
      stopped
        ? "run_state: stopped_on_unsafe_failure"
        : "run_state: complete_preview_only_no_apply",
    );
    lines.push("phase_7_decision: no_go");
    setTrialBatchSummary(lines.join("\n"));
    if (lastTrial) {
      setTrialBatchProgress({
        currentStep: totalLocalSteps,
        currentTrialId: lastTrial.id,
        currentTrialIndex: stageTrials.length,
        currentTrialTitle: lastTrial.title,
        stageLabel: stopped ? "Stopped on unsafe failure" : "Complete",
        stageName,
        totalSteps: totalLocalSteps,
        totalTrials: stageTrials.length,
      });
    }
    setTrialBatchStatus(stopped ? "failed" : "complete");
    setTrialPromptCopyStatus(
      stopped
        ? sourceLabel === "run all preview"
          ? "Run All stopped on unsafe failure."
          : `${stageName} stopped on unsafe failure.`
        : sourceLabel === "run all preview"
          ? "Run All preview summary ready."
          : `${stageName} preview summary ready.`,
    );
  }

  async function runTenTrialPreviews() {
    await runTrialPreviewBatch(10, "10_preview_browser_run", "controlled 10-preview run");
  }

  async function runTwentyFiveTrialPreviews() {
    await runTrialPreviewBatch(25, "25_preview_browser_run", "controlled 25-preview run");
  }

  async function runHundredTrialPreviews() {
    await runTrialPreviewBatch(100, "100_preview_browser_run", "controlled 100-preview run");
  }

  async function runAllTrialPreviews() {
    await runTrialPreviewBatch(
      PROXY_TRIAL_PROMPTS.length,
      "100_preview_browser_run",
      "run all preview",
    );
  }

  function runDirectButtonAction(
    event: PointerEvent<HTMLButtonElement> | TouchEvent<HTMLButtonElement>,
    action: () => void,
  ) {
    event.preventDefault();
    event.stopPropagation();
    const now = Date.now();
    if (now - directButtonActionAtRef.current < 280) {
      return;
    }
    directButtonActionAtRef.current = now;
    action();
  }

  function updateActiveDraftText(draftText: string) {
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              appliedAt: null,
              approvedAt: null,
              applyMessage: "",
              allowedFiles: deriveTaskPacket(draftText).allowedFiles,
              blockedFields: deriveTaskPacket(draftText).blockedFields,
              changedFiles: [],
              draftText,
              previewMessage: "Preview not requested.",
              previewStatus: "idle",
              previewTarget: "",
              proposedDiff: "",
              receiptCommandsRun: "not run yet",
              receiptFocusedTestResult: "not reported by UI",
              receiptLintResult: "not reported by UI",
              receiptPassFail: "not run yet",
              receiptTypecheckResult: "not reported by UI",
              rollbackHint: "keep the task bounded; use git diff before any apply.",
              taskId: "",
              taskSubmitted: false,
              verificationMessage: "Verification has not started.",
              verificationStatus: "not_started",
              verifiedAt: null,
            }
          : chat,
      ),
    );
  }

  function clearActiveTask() {
    restoredTaskStoryRef.current = false;
    removeStoredTaskStory();
    setPreviewDiffCopyStatus("");
    setReceiptCopyStatus("");
    setTrialPromptCopyStatus("");
    setPersistenceStatus("Task cleared locally; refresh will not restore this task.");
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              appliedAt: null,
              approvedAt: null,
              applyMessage: "",
              allowedFiles: [],
              blockedFields: [],
              changedFiles: [],
              draftText: "",
              isApplying: false,
              isVerifying: false,
              previewMessage: "Preview not requested.",
              previewStatus: "idle",
              previewTarget: "",
              proposedDiff: "",
              receiptCommandsRun: "not run yet",
              receiptFocusedTestResult: "not reported by UI",
              receiptLintResult: "not reported by UI",
              receiptPassFail: "not run yet",
              receiptTypecheckResult: "not reported by UI",
              rollbackHint: "keep the task bounded; use git diff before any apply.",
              taskId: "",
              taskSubmitted: false,
              verificationMessage: "Verification has not started.",
              verificationStatus: "not_started",
              verifiedAt: null,
            }
          : chat,
      ),
    );
  }

  function updateActivePreviewState(
    previewStatus: ShellChat["previewStatus"],
    previewMessage: string,
    options?: Partial<
      Pick<
        ShellChat,
        | "allowedFiles"
        | "blockedFields"
        | "changedFiles"
        | "previewTarget"
        | "proposedDiff"
        | "taskId"
        | "taskSubmitted"
        | "approvedAt"
        | "appliedAt"
        | "designProposalIntake"
      >
    >,
  ) {
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              appliedAt: options?.appliedAt ?? null,
              allowedFiles: options?.allowedFiles ?? taskPacket.allowedFiles,
              approvedAt: options?.approvedAt ?? null,
              applyMessage: "",
              blockedFields: options?.blockedFields ?? taskPacket.blockedFields,
              changedFiles: options?.changedFiles ?? [],
              designProposalIntake: options?.designProposalIntake ?? null,
              isVerifying: false,
              previewMessage,
              previewStatus,
              receiptCommandsRun: "not run yet",
              receiptFocusedTestResult: "not reported by UI",
              receiptLintResult: "not reported by UI",
              receiptPassFail: "not run yet",
              receiptTypecheckResult: "not reported by UI",
              rollbackHint: "keep the task bounded; use git diff before any apply.",
              previewTarget: options?.previewTarget ?? "",
              proposedDiff: options?.proposedDiff ?? "",
              taskId: options?.taskId ?? "",
              taskSubmitted: options?.taskSubmitted ?? chat.taskSubmitted,
              verificationMessage: "Verification has not started.",
              verificationStatus: "not_started",
              verifiedAt: null,
            }
          : chat,
      ),
    );
  }

  function approvePreview() {
    if (!canApprovePreview && !canMarkPreviewReviewed) {
      return;
    }
    const reviewedAt = new Date().toISOString();
    const reviewMessage = noApplyPreviewTrial
      ? "Preview reviewed for HB-01. No apply authority granted."
      : "Preview approved locally. No files changed yet.";
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              approvedAt: reviewedAt,
              previewMessage: reviewMessage,
            }
          : chat,
      ),
    );
    appendSessionLog(
      "ready",
      `${loadedTrial?.id ?? "Manual task"} reviewed audit`,
      previewAuditDetail({
        changedFiles: activeChangedFiles,
        diffPresent: Boolean(activeProposedDiff),
        humanReviewResult: noApplyPreviewTrial
          ? "reviewed_without_apply_authority"
          : "reviewed_preview_diff",
        approvalState: noApplyPreviewTrial ? "reviewed only; not approved" : "approved locally",
        applyState: "not applied",
        packet: taskPacket,
        reason: reviewMessage,
        status: "preview_reviewed",
        target: activePreviewTarget || taskPacket.targetFile,
      }),
    );
    setTrialPromptCopyStatus("Reviewed audit recorded.");
  }

  async function applyApprovedDiff() {
    if (!canApplyApprovedDiff) {
      return;
    }
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId ? { ...chat, applyMessage: "", isApplying: true } : chat,
      ),
    );
    try {
      const response = await fetch("/v1/actions/execute-approved", {
        body: JSON.stringify({
          action: `Modify ${activePreviewTarget}`,
          approved: true,
          approved_diff: activeProposedDiff,
          target: activePreviewTarget,
          task_id: activeTaskId,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
      });
      const payload = await readJson(response);
      const message = messageFromPayload(payload, response.status);
      const appliedChangedFiles = changedFilesFromPayload(payload);
      setChats((current) =>
        current.map((chat) =>
          chat.id === activeChatId
            ? {
                ...chat,
                appliedAt: response.ok ? new Date().toISOString() : chat.appliedAt,
                applyMessage: response.ok ? "Approved diff applied. Verification required." : message,
                changedFiles:
                  response.ok && appliedChangedFiles.length > 0 ? appliedChangedFiles : chat.changedFiles,
                isApplying: false,
                isVerifying: false,
                receiptCommandsRun: response.ok
                  ? commandsRunFromPayload(payload, "not run yet")
                  : chat.receiptCommandsRun,
                receiptFocusedTestResult: response.ok
                  ? checkResultFromPayload(payload, /test|vitest|focused/i, chat.receiptFocusedTestResult)
                  : chat.receiptFocusedTestResult,
                receiptLintResult: response.ok
                  ? checkResultFromPayload(payload, /lint|eslint/i, chat.receiptLintResult)
                  : chat.receiptLintResult,
                receiptPassFail: response.ok
                  ? passFailFromPayload(payload, true, "pending verification")
                  : chat.receiptPassFail,
                receiptTypecheckResult: response.ok
                  ? checkResultFromPayload(payload, /typecheck|tsc|typescript/i, chat.receiptTypecheckResult)
                  : chat.receiptTypecheckResult,
                rollbackHint: response.ok ? rollbackHintFromPayload(payload) : chat.rollbackHint,
                verificationMessage: response.ok
                  ? "Verification required. Run checks before treating this task as done."
                  : chat.verificationMessage,
                verificationStatus: response.ok ? "required" : chat.verificationStatus,
              }
            : chat,
        ),
      );
    } catch (error) {
      setChats((current) =>
        current.map((chat) =>
          chat.id === activeChatId
            ? {
                ...chat,
                applyMessage: error instanceof Error ? error.message : "Approved apply failed.",
                isApplying: false,
                isVerifying: false,
              }
            : chat,
        ),
      );
    }
  }

  async function verifyAppliedTask() {
    if (!canRunVerification) {
      return;
    }
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              isVerifying: true,
              verificationMessage: "Recording docs-only verification confirmations.",
              verificationStatus: "running",
            }
          : chat,
      ),
    );
    try {
      const response = await fetch(
        `/v1/tasks/long-running/${encodeURIComponent(activeTaskId)}/verify`,
        {
          body: JSON.stringify({
            confirm_backup_audit_present: true,
            confirm_changed_files_reviewed: true,
            confirm_expected_change_present: true,
            confirm_no_unintended_files: true,
            manual_browser_check_done: true,
            verification_note:
              "Docs-only command-center trial verified by human review of changed file and expected diff.",
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
      );
      const payload = await readJson(response);
      const message = messageFromPayload(payload, response.status);
      const verifiedChangedFiles = changedFilesFromPayload(payload);
      setChats((current) =>
        current.map((chat) =>
          chat.id === activeChatId
            ? {
                ...chat,
                changedFiles:
                  response.ok && verifiedChangedFiles.length > 0
                    ? verifiedChangedFiles
                    : chat.changedFiles,
                isVerifying: false,
                receiptCommandsRun: response.ok
                  ? commandsRunFromPayload(payload, chat.receiptCommandsRun)
                  : chat.receiptCommandsRun,
                receiptFocusedTestResult: response.ok
                  ? checkResultFromPayload(payload, /test|vitest|focused/i, chat.receiptFocusedTestResult)
                  : chat.receiptFocusedTestResult,
                receiptLintResult: response.ok
                  ? checkResultFromPayload(payload, /lint|eslint/i, chat.receiptLintResult)
                  : chat.receiptLintResult,
                receiptPassFail: passFailFromPayload(payload, response.ok, chat.receiptPassFail),
                receiptTypecheckResult: response.ok
                  ? checkResultFromPayload(payload, /typecheck|tsc|typescript/i, chat.receiptTypecheckResult)
                  : chat.receiptTypecheckResult,
                verificationMessage: response.ok
                  ? "Docs-only verification recorded. No command was run by this button."
                  : message,
                verificationStatus: response.ok ? "passed" : "failed",
                verifiedAt: response.ok ? new Date().toISOString() : chat.verifiedAt,
              }
            : chat,
        ),
      );
    } catch (error) {
      setChats((current) =>
        current.map((chat) =>
          chat.id === activeChatId
            ? {
                ...chat,
                isVerifying: false,
                verificationMessage: error instanceof Error ? error.message : "Verification failed.",
                verificationStatus: "failed",
              }
            : chat,
        ),
      );
    }
  }

  async function requestSafePreview(trialOverride?: ProxyTrialPrompt) {
    const taskText = (trialOverride?.taskPrompt ?? activeDraftText).trim();
    const packet = taskPacketFromTrial(taskText, trialOverride ?? loadedTrial);
    if (!taskText) {
      updateActivePreviewState("blocked", "Draft a coding task before preview.");
      return;
    }
    if (packet.blockedFields.length > 0) {
      const blockedMessage = `Preview blocked: missing ${packet.blockedFields.join(", ")}.`;
      updateActivePreviewState(
        "blocked",
        blockedMessage,
        {
          allowedFiles: packet.allowedFiles,
          blockedFields: packet.blockedFields,
          previewTarget: packet.targetFile,
        },
      );
      return;
    }
    if (!activeTaskSubmitted && !trialOverride) {
      submitActiveTask();
    }

    updateActivePreviewState("loading", "Creating bounded Source Proxy task. No files changed.");
    try {
      const taskResponse = await fetchWithTimeout(
        "/v1/tasks/long-running",
        {
          body: JSON.stringify({
            description: taskText,
            steps: [
              "Preview requested from /coding command center.",
              `Target file: ${packet.targetFile}`,
              `Allowed files: ${packet.allowedFiles.join(", ")}`,
            ],
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
        "Creating preview task",
      );
      const taskPayload = await readJson(taskResponse);
      if (!taskResponse.ok) {
        const message = messageFromPayload(taskPayload, taskResponse.status);
        updateActivePreviewState("error", message);
        return;
      }
      const previewTaskId = taskIdFromPayload(taskPayload);
      if (!previewTaskId) {
        const message = "Preview task create did not return a task id.";
        updateActivePreviewState("error", message);
        return;
      }

      updateActivePreviewState("loading", "Requesting bounded diff proposal. No files changed.");
      const promptResponse = await fetchWithTimeout(
        "/v1/decisions/prompt-packet",
        {
          body: JSON.stringify({
            active_task_id: previewTaskId,
            allowed_files: packet.allowedFiles,
            current_agent_role: "coder",
            needs_codebase_context: true,
            prefer_free: activeProviderId === "local",
            target_files: [packet.targetFile],
            targeted_files: [packet.targetFile],
            task: taskText,
            wants_implementation: true,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
        "Requesting bounded diff proposal",
      );
      const promptPayload = await readJson(promptResponse);
      const designProposalIntake = designProposalIntakeFromPayload(promptPayload);
      if (!promptResponse.ok) {
        const message = messageFromPayload(promptPayload, promptResponse.status);
        updateActivePreviewState("error", message, { designProposalIntake });
        return;
      }

      const proposedDiff = diffFromPayload(promptPayload);
      if (!proposedDiff) {
        if (alreadySatisfiedFromPayload(promptPayload)) {
          const noOpMessage = messageFromPayload(promptPayload, promptResponse.status);
          updateActivePreviewState(
            "blocked",
            noOpMessage,
            {
              allowedFiles: packet.allowedFiles,
              blockedFields: [],
              changedFiles: [],
              designProposalIntake,
              previewTarget: packet.targetFile,
              taskId: previewTaskId,
            },
          );
          appendSessionLog(
            "ready",
            `${(trialOverride ?? loadedTrial)?.id ?? "Manual task"} already satisfied audit`,
            previewAuditDetail({
              changedFiles: [],
              commandsRun: "none; no-op preview",
              diffCheckResult: "not applicable; no diff",
              diffPresent: false,
              humanReviewResult: "not_reviewed_yet",
              packet,
              passFail: "not applicable; no change needed",
              reason: noOpMessage,
              status: "already_satisfied",
              taskPrompt: taskText,
              target: packet.targetFile,
              trial: trialOverride ?? loadedTrial,
              verificationState: "not_needed",
            }),
          );
          setTrialPromptCopyStatus("Already-satisfied audit recorded.");
          return;
        }
        const message =
          messageFromPayload(promptPayload, promptResponse.status) || "Preview blocked: no diff returned.";
        updateActivePreviewState(
          "blocked",
          message,
          { designProposalIntake },
        );
        return;
      }
      const previewTarget = targetFromPayloadOrDiff(promptPayload, proposedDiff) || packet.targetFile;
      const taskId = taskIdFromPayload(promptPayload) || previewTaskId;

      updateActivePreviewState("loading", "Checking diff safety gates. No files changed.", {
        designProposalIntake,
      });
      const previewResponse = await fetchWithTimeout(
        "/v1/verification/diff-preview",
        {
          body: JSON.stringify({
            route_type: activeProviderId === "local" ? "local-intent" : "cloud-intent",
            active_task_id: taskId,
            task_spec: {
              allowed_files: packet.allowedFiles,
              forbidden_files: [],
              risk_tier: "low",
              schema_version: 1,
              source: "coding_command_center_ui",
              target: packet.targetFile,
              task_type: "modify_existing_file",
              verification: [],
            },
            task_text: taskText,
            unified_diff: proposedDiff,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
        "Checking diff safety gates",
      );
      const previewPayload = await readJson(previewResponse);
      if (!previewResponse.ok) {
        const message = messageFromPayload(previewPayload, previewResponse.status);
        updateActivePreviewState("error", message, { designProposalIntake });
        return;
      }
      const status = stringValue(asRecord(previewPayload).status);
      if (status === "blocked") {
        const message = messageFromPayload(previewPayload, previewResponse.status);
        updateActivePreviewState("blocked", message, { designProposalIntake });
        return;
      }
      const changedFiles = collectPathsFromUnifiedDiff(proposedDiff);
      updateActivePreviewState("ready", "Preview ready. No files changed yet.", {
        allowedFiles: packet.allowedFiles,
        blockedFields: [],
        changedFiles,
        designProposalIntake,
        previewTarget,
        proposedDiff,
        taskId,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Preview request failed.";
      updateActivePreviewState("error", message);
      if (/timed out/i.test(message)) {
        appendSessionLog(
          "inconclusive",
          `${(trialOverride ?? loadedTrial)?.id ?? "Manual task"} preview timed out`,
          previewAuditDetail({
            changedFiles: [],
            commandsRun: "none; preview timed out",
            diffCheckResult: "not run; preview timed out",
            diffPresent: false,
            humanReviewResult: "not recorded; preview timed out before review",
            packet,
            passFail: "inconclusive; preview timed out",
            reason: message,
            status: "timeout",
            taskPrompt: taskText,
            target: packet.targetFile,
            trial: trialOverride ?? loadedTrial,
            verificationState: "not_started",
          }),
        );
        setTrialPromptCopyStatus("Preview timeout audit recorded.");
      }
    }
  }

  function handleStartNewChat() {
    const nextIndex = chats.filter((chat) => chat.title.startsWith("New chat")).length + 1;
    const chat: ShellChat = {
      id: `local-chat-${Date.now()}-${nextIndex}`,
      title: `New chat ${nextIndex}`,
      meta: "Empty",
      emptyState: `Empty chat ${nextIndex}, ready for a prompt`,
      providerId: "local",
      providerModelId: "local-default",
      workspaceContextId: DEFAULT_CODING_WORKSPACE_CONTEXT_ID,
      codingMode: false,
      draftText: "",
      appliedAt: null,
      approvedAt: null,
      applyMessage: "",
      allowedFiles: [],
      blockedFields: [],
      changedFiles: [],
      isApplying: false,
      isVerifying: false,
      previewMessage: "Preview not requested.",
      previewStatus: "idle",
      previewTarget: "",
      proposedDiff: "",
      taskId: "",
      taskSubmitted: false,
      receiptCommandsRun: "not run yet",
      receiptFocusedTestResult: "not reported by UI",
      receiptLintResult: "not reported by UI",
      receiptPassFail: "not run yet",
      receiptTypecheckResult: "not reported by UI",
      rollbackHint: "keep the task bounded; use git diff before any apply.",
      verificationMessage: "Verification has not started.",
      verificationStatus: "not_started",
      verifiedAt: null,
    };
    setChats((current) => [chat, ...current]);
    setActiveChatId(chat.id);
    setPersistenceStatus("Local session only; new chats are current-session until a task story is staged.");
  }

  return (
    <main className="dashboard-demo-v4-route-shell dashboard-demo-v4-route-shell-coding relative min-h-dvh overflow-x-hidden bg-[#090a0f] pb-[calc(9.5rem_+_var(--shell-safe-area-bottom,0px))] text-zinc-100 xl:pb-0">
      <DashboardDemoV4FloatingNav desktopVariant="full-height" />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(34,211,238,0.12),transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.68),rgba(9,10,15,0.96)_46%,#090a0f)]"
      />
      <div className="dashboard-demo-v4-route-main relative mx-auto flex min-h-dvh w-full max-w-[1680px] flex-col gap-3 px-3 py-3 sm:px-4 xl:grid xl:grid-cols-[280px_minmax(0,1fr)] xl:gap-4 xl:p-4">
        <aside
          aria-label="Mobile workspace and chat rail"
          className="max-h-[36dvh] overflow-auto rounded-lg border border-white/10 bg-[#10131b]/90 shadow-2xl shadow-black/30 backdrop-blur-xl sm:max-h-[42dvh] xl:max-h-none xl:min-h-[calc(100dvh-2rem)]"
        >
          <div className="flex min-h-14 items-center justify-between border-b border-white/10 bg-white/[0.025] px-3">
            <div className="flex min-w-0 items-center gap-2">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-cyan-300/20 bg-cyan-300/10 text-cyan-100">
                <PanelLeft aria-hidden="true" size={17} />
              </span>
              <div className="min-w-0">
                <h1 className="truncate text-sm font-semibold">Coding</h1>
                <p className="truncate text-xs text-zinc-500">Command center</p>
              </div>
            </div>
            <button
              aria-label="Start new chat"
              className="flex min-h-9 shrink-0 items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.055] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/35 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              onClick={handleStartNewChat}
              title="Start new chat"
              type="button"
            >
              <MessageSquarePlus aria-hidden="true" size={17} />
              <span>New chat</span>
            </button>
          </div>

          <div className="space-y-4 p-3">
            <button
              aria-label={`Selected workspace: ${activeWorkspaceContext.label}`}
              className="flex min-h-11 w-full items-center justify-between gap-3 rounded-md border border-cyan-300/20 bg-cyan-300/[0.065] px-3 text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] transition hover:border-cyan-300/35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              onClick={() => updateActiveChatWorkspaceContext("spiritos")}
              type="button"
            >
              <span className="flex min-w-0 items-center gap-2">
                <FolderGit2 aria-hidden="true" className="shrink-0 text-cyan-100" size={17} />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">
                    {activeWorkspaceContext.label}
                  </span>
                  <span className="block truncate text-xs text-zinc-500">
                    {activeWorkspaceContext.path}
                  </span>
                  <span className="block truncate text-xs text-cyan-100/70">
                    {activeWorkspaceContext.authority}
                  </span>
                </span>
              </span>
              <ChevronDown aria-hidden="true" className="shrink-0 text-zinc-500" size={16} />
            </button>

            <button
              aria-disabled="true"
              aria-label={`${futureWindowsWorkspace.label} future target unavailable`}
              aria-pressed="false"
              className="mt-2 flex min-h-11 w-full cursor-not-allowed items-center justify-between gap-3 rounded-md border border-dashed border-white/10 bg-white/[0.025] px-3 text-left text-zinc-500"
              disabled
              onClick={() => updateActiveChatWorkspaceContext("windows-projects")}
              type="button"
            >
              <span className="flex min-w-0 items-center gap-2">
                <FolderGit2 aria-hidden="true" className="shrink-0 text-sky-100/70" size={17} />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">
                    {futureWindowsWorkspace.label}
                  </span>
                  <span className="block truncate text-xs text-zinc-500">
                    {futureWindowsWorkspace.status}
                  </span>
                  <span className="block truncate text-xs text-sky-100/65">
                    {futureWindowsWorkspace.authority}
                  </span>
                </span>
              </span>
              <span className="shrink-0 rounded border border-sky-300/25 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-sky-100/75">
                future
              </span>
            </button>

            <button
              aria-disabled="true"
              aria-label="Remote workspace skipped"
              className="mt-2 flex min-h-11 w-full cursor-not-allowed items-center justify-between gap-3 rounded-md border border-dashed border-white/10 bg-white/[0.018] px-3 text-left text-zinc-500"
              disabled
              type="button"
            >
              <span className="flex min-w-0 items-center gap-2">
                <FolderGit2 aria-hidden="true" className="shrink-0" size={17} />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">Remote workspace</span>
                  <span className="block truncate text-xs text-zinc-500">
                    Remote connections skipped; no clone, mount, or connector action.
                  </span>
                </span>
              </span>
              <span className="shrink-0 rounded border border-white/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]">
                skipped
              </span>
            </button>

            <button
              aria-disabled="true"
              aria-label="Start new project placeholder"
              className="mt-2 flex min-h-11 w-full cursor-not-allowed items-center justify-between gap-3 rounded-md border border-dashed border-amber-200/15 bg-amber-200/[0.035] px-3 text-left text-amber-100/70"
              disabled
              type="button"
            >
              <span className="flex min-w-0 items-center gap-2">
                <Plus aria-hidden="true" className="shrink-0" size={17} />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">Start new project</span>
                  <span className="block truncate text-xs text-amber-100/55">
                    Dry-run placeholder until safe creation exists
                  </span>
                </span>
              </span>
              <span className="shrink-0 rounded border border-amber-200/20 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]">
                unwired
              </span>
            </button>

            <div className="relative">
              <Search
                aria-hidden="true"
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500"
                size={15}
              />
              <input
                aria-label="Search coding chats"
                className="min-h-10 w-full rounded-md border border-white/10 bg-black/20 pl-9 pr-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                placeholder="Search chats"
                type="search"
              />
            </div>

            <nav aria-label="Coding chats" className="space-y-2">
              {chats.map((chat) => (
                <button
                  aria-current={chat.id === activeChatId ? "page" : undefined}
                className={`flex min-h-12 w-full items-center justify-between gap-3 rounded-md border px-3 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40 ${
                    chat.id === activeChatId
                      ? "border-cyan-300/45 bg-cyan-300/[0.14] text-cyan-50 shadow-[inset_3px_0_0_rgba(103,232,249,0.85)]"
                      : "border-white/10 bg-white/[0.035] text-zinc-300 hover:border-white/18 hover:bg-white/[0.055]"
                  }`}
                  key={chat.id}
                  onClick={() => setActiveChatId(chat.id)}
                  type="button"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium">{chat.title}</span>
                    <span className="block truncate text-xs text-zinc-500">{chat.meta}</span>
                  </span>
                  {chat.id === activeChatId ? (
                    <span className="h-2 w-2 shrink-0 rounded-full bg-cyan-200 shadow-[0_0_14px_rgba(103,232,249,0.75)]" />
                  ) : null}
                </button>
              ))}
            </nav>
          </div>
        </aside>

        <section className="flex min-h-[58dvh] min-w-0 flex-col rounded-lg border border-white/10 bg-[#0f1118]/92 shadow-2xl shadow-black/25 backdrop-blur-xl xl:h-[calc(100dvh-2rem)] xl:min-h-0 xl:overflow-hidden">
          <div className="border-b border-cyan-300/15 bg-cyan-300/[0.045] px-3 py-2 text-xs font-medium text-cyan-100 xl:hidden">
            Mobile command center: rail, composer, and safety status are stacked for touch.
          </div>
          <header className="border-b border-white/10 bg-white/[0.018] px-3 py-3 sm:px-4">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                  VoidCore shell
                </p>
                <h2 className="mt-1 truncate text-xl font-semibold sm:text-2xl">
                  {activeChatTitle}
                </h2>
                <p className="mt-1 text-xs text-zinc-500">
                  {activeWorkspaceContext.status} · {persistenceStatus}
                </p>
                <p
                  aria-label="Active chat session"
                  className="mt-1 text-xs text-cyan-100/70"
                >
                  Active session: {activeChat?.id ?? "none"} · current-session lifecycle
                </p>
                <p
                  aria-label="Persistence boundary"
                  className="mt-1 text-xs text-zinc-500"
                >
                  {chatPersistenceBoundary}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {contextChips.map((chip) => (
                  <span
                    className={`inline-flex min-h-8 items-center rounded-md border px-2.5 text-xs font-medium ${chipClass(
                      chip.tone,
                    )}`}
                    key={chip.label}
                  >
                    {chip.label}
                  </span>
                ))}
                <span
                  aria-label="Active run state"
                  className="inline-flex min-h-8 items-center rounded-md border border-cyan-300/25 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100"
                >
                  state: {activeRunStateLabel} | {codingCommandCenterBuildMarker}
                </span>
              </div>
            </div>
            <div
              aria-label="Drawer shell triggers"
              className="mt-3 flex flex-wrap gap-2"
              role="toolbar"
            >
              {(["settings", "diagnostics", "evidence"] as DrawerShellId[]).map((drawerId) => (
                <button
                  aria-controls="coding-drawer-shell"
                  aria-expanded={activeDrawerShell === drawerId}
                  aria-pressed={activeDrawerShell === drawerId}
                  className={`inline-flex min-h-8 items-center rounded-md border px-2.5 text-xs font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40 ${
                    activeDrawerShell === drawerId
                      ? "border-cyan-300/40 bg-cyan-300/10 text-cyan-50"
                      : "border-white/10 bg-white/[0.04] text-zinc-300 hover:border-cyan-300/30 hover:text-cyan-100"
                  }`}
                  key={drawerId}
                  onClick={() =>
                    setActiveDrawerShell((current) => (current === drawerId ? null : drawerId))
                  }
                  type="button"
                >
                  {drawerShellCopy[drawerId].label}
                </button>
              ))}
            </div>
          </header>

          <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-x-hidden overflow-y-auto px-3 py-4 sm:px-4 xl:gap-4 xl:px-5 xl:py-4">
            <p className="sr-only">{currentTrialStep}</p>
            {activeDrawerShellCopy ? (
              <aside
                aria-label={`${activeDrawerShellCopy.label} drawer shell`}
                className="mx-auto w-full max-w-5xl rounded-lg border border-cyan-300/25 bg-cyan-300/[0.07] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]"
                id="coding-drawer-shell"
                role="complementary"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <h3
                      className="text-sm font-semibold text-cyan-50 focus-visible:outline-none"
                      ref={drawerShellHeadingRef}
                      tabIndex={-1}
                    >
                      {activeDrawerShellCopy.title}
                    </h3>
                    <p className="mt-2 text-xs leading-5 text-cyan-50/80">
                      {activeDrawerShellCopy.body}
                    </p>
                    <p className="mt-2 text-xs leading-5 text-zinc-400">
                      Non-modal drawer shell only. Active task, composer, and chat navigation remain
                      usable; controls will move here only in later approved phases.
                    </p>
                  </div>
                  <button
                    aria-label={`Close ${activeDrawerShellCopy.label} drawer shell`}
                    className="inline-flex min-h-8 shrink-0 items-center gap-1.5 rounded-md border border-white/10 bg-black/25 px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                    onClick={() => setActiveDrawerShell(null)}
                    type="button"
                  >
                    <X aria-hidden="true" size={13} />
                    Close
                  </button>
                </div>
              </aside>
            ) : null}
            <details className="mx-auto w-full max-w-5xl rounded-lg border border-white/10 bg-white/[0.025] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
              <summary className="cursor-pointer text-xs font-semibold uppercase tracking-[0.18em] text-zinc-400">
                Project, Provider, and Safety Details
              </summary>
              <div className="mt-3 grid w-full items-start gap-3 sm:grid-cols-3">
              <div className="min-w-0 rounded-lg border border-white/10 bg-white/[0.04] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <ShieldCheck aria-hidden="true" className="text-emerald-200" size={17} />
                  Safety
                </div>
                <p className="mt-2 text-xs leading-5 text-zinc-500">Draft locked</p>
              </div>
              <div className="min-w-0 rounded-lg border border-white/10 bg-white/[0.04] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Bot aria-hidden="true" className="text-cyan-100" size={17} />
                  Provider
                </div>
                <p className="mt-2 text-xs leading-5 text-zinc-500">
                  {localProvider?.summary ?? "Default route where local coding support is available."}
                </p>
                <div className="mt-3 grid gap-2">
                  {providerStatuses.map((provider) => (
                    <button
                      aria-pressed={activeProviderId === provider.id}
                      className={`min-h-9 rounded-md border px-2 text-left text-xs transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40 ${
                        activeProviderId === provider.id
                          ? "border-cyan-300/40 bg-cyan-300/10 text-cyan-50"
                          : "border-white/10 bg-black/20 text-zinc-400 hover:border-white/20"
                      }`}
                      key={provider.id}
                      onClick={() => updateActiveChatProvider(provider.id)}
                      type="button"
                    >
                      {provider.label}: {provider.status}
                    </button>
	                  ))}
	                </div>
                <div
                  aria-label="Provider model selector"
                  className="mt-3 grid gap-2 rounded-md border border-white/10 bg-black/20 p-2"
                  role="region"
                >
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">
                    Model
                  </p>
                  {providerModelOptions.map((model) => (
                    <button
                      aria-pressed={activeProviderModel.id === model.id}
                      className={`min-h-9 rounded-md border px-2 text-left text-xs transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40 ${
                        activeProviderModel.id === model.id
                          ? "border-cyan-300/40 bg-cyan-300/10 text-cyan-50"
                          : "border-white/10 bg-black/20 text-zinc-400 hover:border-white/20"
                      }`}
                      key={model.id}
                      onClick={() => updateActiveChatProviderModel(model.id)}
                      type="button"
                    >
                      {model.label}: {model.status} ·{" "}
                      {model.previewAvailable ? "preview available" : "preview blocked"}
                    </button>
                  ))}
                </div>
                <p className="mt-3 text-xs leading-5 text-zinc-500">{providerIntent}</p>
                <p className="mt-2 text-xs leading-5 text-zinc-500">
                  Model: {activeProviderModel.modelLabel}. {activeProviderModel.costWarning}
                </p>
	                {activeProviderModel.blockedReason ? (
	                  <p className="mt-2 text-xs leading-5 text-amber-100/75">
	                    Blocked: {activeProviderModel.blockedReason}
	                  </p>
	                ) : null}
	              </div>
              <div className="min-w-0 overflow-hidden rounded-lg border border-white/10 bg-white/[0.04] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <GitBranch aria-hidden="true" className="text-amber-100" size={17} />
                  Workspace
                </div>
                <p className="mt-2 text-xs leading-5 text-zinc-500">
                  {activeWorkspaceContext.label} context is selected for this chat
                </p>
                <p className="mt-2 text-xs leading-5 text-zinc-500">
                  {futureWindowsWorkspace.label} is a future target; no bridge, folder access, or
                  project creation is available from this selector.
                </p>
                <p className="mt-2 text-xs leading-5 text-zinc-500">
                  Dirty tree warning: {activeWorkspaceContext.dirtyState}
                </p>
                <div
                  aria-label="Workspace context per chat"
                  className="mt-3 grid gap-2"
                  role="region"
                >
                  {CODING_WORKSPACE_CONTEXTS.map((context) => (
                    <button
                      aria-disabled={context.availability !== "available" ? "true" : undefined}
                      aria-pressed={activeWorkspaceContext.id === context.id}
                      className={`min-h-9 min-w-0 rounded-md border px-2 text-left text-xs transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40 ${
                        activeWorkspaceContext.id === context.id
                          ? "border-cyan-300/40 bg-cyan-300/10 text-cyan-50"
                          : context.availability !== "available"
                            ? "cursor-not-allowed border-white/10 bg-black/10 text-zinc-600"
                            : "border-white/10 bg-black/20 text-zinc-400 hover:border-white/20"
                      }`}
                      disabled={context.availability !== "available"}
                      key={context.id}
                      onClick={() => updateActiveChatWorkspaceContext(context.id)}
                      type="button"
                    >
                      {context.label}: {context.badge} · {context.access}
                    </button>
                  ))}
                </div>
                <div
                  aria-label="Read/list-only folder proof"
                  className="mt-3 min-w-0 overflow-hidden rounded-md border border-white/10 bg-black/20 p-2"
                  role="region"
                >
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">
                    Folder proof
                  </p>
                  <dl className="mt-2 grid gap-2">
                    {folderProofRows.map((row) => (
                      <div
                        className="min-w-0 overflow-hidden rounded-md border border-white/10 bg-white/[0.03] p-2"
                        key={row.label}
                      >
                        <dt className="text-xs font-medium leading-5 text-zinc-200">
                          {row.label}: {row.state}
                        </dt>
                        <dd className="mt-1 break-words text-xs leading-5 text-zinc-500">
                          {row.evidence}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>
              </div>
            </details>

            <details className="mx-auto w-full max-w-5xl rounded-lg border border-white/10 bg-white/[0.025] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
              <summary className="cursor-pointer text-xs font-semibold uppercase tracking-[0.18em] text-zinc-400">
                Environment Details
              </summary>
              <div className="mt-3 grid gap-4">
            <section
              aria-label="Display-only settings"
              className="w-full rounded-lg border border-white/10 bg-white/[0.035] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <ShieldCheck aria-hidden="true" className="text-cyan-100" size={17} />
                    Settings
                  </div>
                  <p className="mt-1 text-xs leading-5 text-zinc-500">
                    Display-only settings. Writable settings require a later gate.
                  </p>
                </div>
                <span className="inline-flex min-h-7 items-center self-start rounded-md border border-white/10 bg-black/20 px-2 text-xs font-semibold text-zinc-300 sm:self-auto">
                  no persistence
                </span>
              </div>
              <dl className="mt-3 grid gap-0 overflow-hidden rounded-md border border-white/10 sm:grid-cols-2">
                {settingsRows.map((row, index) => (
                  <div
                    className={`min-w-0 border-white/10 bg-black/15 p-3 ${
                      index > 0 ? "border-t" : ""
                    } sm:[&:nth-child(even)]:border-l sm:[&:nth-child(2)]:border-t-0`}
                    key={row.id}
                  >
                    <dt className="flex items-start justify-between gap-2 text-xs font-semibold text-zinc-100">
                      <span>{row.label}</span>
                      <span className="shrink-0 rounded border border-white/10 bg-white/[0.035] px-1.5 py-0.5 text-[10px] uppercase tracking-[0.12em] text-zinc-400">
                        {row.state}
                      </span>
                    </dt>
                    <dd className="mt-2 text-xs leading-5 text-zinc-400">
                      {row.value}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Source: {row.source}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Authority: {row.authority}
                    </dd>
                    <dd className="mt-2 text-xs font-medium text-zinc-400">
                      Writable: {row.writable ? "true" : "false"}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>

            <section
              aria-label="Usage and time tracking"
              className="w-full rounded-lg border border-white/10 bg-white/[0.035] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Clock3 aria-hidden="true" className="text-cyan-100" size={17} />
                    Usage and time
                  </div>
                  <p className="mt-1 text-xs leading-5 text-zinc-500">
                    Current-session timers only. Tokens, cost, budget, CLI, and durable usage stay
                    unavailable unless a real source supplies them.
                  </p>
                </div>
                <span className="inline-flex min-h-7 items-center self-start rounded-md border border-white/10 bg-black/20 px-2 text-xs font-semibold text-zinc-300 sm:self-auto">
                  no fake usage
                </span>
              </div>
              <dl className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {usageTimeRows.map((row) => (
                  <div
                    className="min-w-0 rounded-md border border-white/10 bg-black/20 p-3"
                    key={row.id}
                  >
                    <dt className="flex items-start justify-between gap-2 text-xs font-semibold text-zinc-100">
                      <span>{row.label}</span>
                      <span className="shrink-0 rounded border border-white/10 bg-white/[0.035] px-1.5 py-0.5 text-[10px] uppercase tracking-[0.12em] text-zinc-400">
                        {row.state}
                      </span>
                    </dt>
                    <dd className="mt-2 text-xs leading-5 text-zinc-400">
                      {row.value}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Source: {row.source}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Authority: {row.authority}
                    </dd>
                    <dd className="mt-2 text-xs font-medium text-zinc-400">
                      Actual provider usage claimed: {row.actualProviderUsageClaimed ? "true" : "false"}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>

            <section
              aria-label="In-app alerts and waiting states"
              className="w-full rounded-lg border border-white/10 bg-white/[0.035] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <BellRing aria-hidden="true" className="text-cyan-100" size={17} />
                    Alerts and waiting states
                  </div>
                  <p className="mt-1 text-xs leading-5 text-zinc-500">
                    In-app alerts only. Desktop notifications, sounds, permission prompts, and
                    background watchers require a later gate.
                  </p>
                </div>
                <span className="inline-flex min-h-7 items-center self-start rounded-md border border-white/10 bg-black/20 px-2 text-xs font-semibold text-zinc-300 sm:self-auto">
                  no OS permission
                </span>
              </div>
              <dl className="mt-3 grid gap-2 sm:grid-cols-2">
                {alertRows.map((row) => (
                  <div
                    className="min-w-0 rounded-md border border-white/10 bg-black/20 p-3"
                    key={row.id}
                  >
                    <dt className="flex items-start justify-between gap-2 text-xs font-semibold text-zinc-100">
                      <span>{row.title}</span>
                      <span className="shrink-0 rounded border border-white/10 bg-white/[0.035] px-1.5 py-0.5 text-[10px] uppercase tracking-[0.12em] text-zinc-400">
                        {row.state}
                      </span>
                    </dt>
                    <dd className="mt-2 text-xs leading-5 text-zinc-400">
                      {row.display}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Trigger: {row.trigger}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Evidence: {row.evidence}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Cooldown/reset: {row.cooldown}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Authority: {row.authority}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>

            <section
              aria-label="Backend truth on UI"
              className="w-full rounded-lg border border-white/10 bg-white/[0.035] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Bot aria-hidden="true" className="text-cyan-100" size={17} />
                    Backend truth
                  </div>
                  <p className="mt-1 text-xs leading-5 text-zinc-500">
                    Route inventory and current UI-local truth only. Live backend reads, hidden
                    polling, providers, queues, workers, shell commands, and apply routes are not
                    started by this panel.
                  </p>
                </div>
                <span className="inline-flex min-h-7 items-center self-start rounded-md border border-white/10 bg-black/20 px-2 text-xs font-semibold text-zinc-300 sm:self-auto">
                  no fake backend data
                </span>
              </div>
              <dl className="mt-3 grid gap-2 sm:grid-cols-2">
                {backendTruthRows.map((row) => (
                  <div
                    className="min-w-0 rounded-md border border-white/10 bg-black/20 p-3"
                    key={row.id}
                  >
                    <dt className="flex items-start justify-between gap-2 text-xs font-semibold text-zinc-100">
                      <span>{row.title}</span>
                      <span className="shrink-0 rounded border border-white/10 bg-white/[0.035] px-1.5 py-0.5 text-[10px] uppercase tracking-[0.12em] text-zinc-400">
                        {row.state}
                      </span>
                    </dt>
                    <dd className="mt-2 text-xs leading-5 text-zinc-400">
                      Route: {row.route}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Evidence: {row.evidence}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Fallback: {row.fallback}
                    </dd>
                    <dd className="mt-2 text-xs leading-5 text-zinc-500">
                      Authority: {row.authority}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>
              </div>
            </details>

            <div className="mx-auto flex w-full max-w-5xl items-start justify-center">
              <div className="w-full rounded-lg border border-white/10 bg-black/25 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.035)] sm:p-5">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-cyan-300/25 bg-cyan-300/10 text-cyan-100">
                    <Code2 aria-hidden="true" size={18} />
                  </span>
                  <div className="min-w-0">
                    <h3 className="truncate text-base font-semibold">Active task area</h3>
                    <p className="truncate text-sm text-zinc-500">
                      {codingModeActive
                        ? activeTaskSubmitted && activeDraftText.trim()
                          ? taskPacket.title
                          : "Coding mode active, no submitted task yet"
                        : activeChatMeta === "Empty"
                          ? activeChatEmptyState
                          : "No coding task drafted"}
                    </p>
                  </div>
                </div>
                {codingModeActive ? (
                  <div className="mt-4 rounded-md border border-cyan-300/25 bg-cyan-300/10 p-3 text-sm text-cyan-50">
                    Coding task context is active for this chat. Preview can run here; approval and
                    apply stay locked until preview evidence passes.
                  </div>
                ) : null}
                {codingModeActive ? (
                  <div className="mt-3 rounded-md border border-white/10 bg-black/20 p-3 text-sm text-zinc-300">
                    <div className="grid gap-2 sm:grid-cols-2">
                      <p>
                        <span className="font-medium text-zinc-100">Task:</span>{" "}
                        {taskPacket.summary}
                      </p>
                      <p>
                        <span className="font-medium text-zinc-100">State:</span> {taskStateLabel}
                      </p>
                      <p>
                        <span className="font-medium text-zinc-100">Workspace:</span>{" "}
                        {activeWorkspaceContext.label}
                      </p>
                      <p>
                        <span className="font-medium text-zinc-100">Provider:</span>{" "}
                        {providerStatuses.find((provider) => provider.id === activeProviderId)?.label ??
                          "Local LLM"}
                      </p>
                      <p>
                        <span className="font-medium text-zinc-100">Model:</span>{" "}
                        {activeProviderModel.modelLabel}
                      </p>
                      <p>
                        <span className="font-medium text-zinc-100">Target file:</span>{" "}
                        {taskPacket.targetFile || "missing"}
                      </p>
                      <p>
                        <span className="font-medium text-zinc-100">Allowed files:</span>{" "}
                        {taskPacket.allowedFiles.length > 0 ? taskPacket.allowedFiles.join(", ") : "missing"}
                      </p>
                    </div>
                    <div
                      aria-label="Inferred scope review"
                      className="mt-3 rounded-md border border-white/10 bg-black/25 p-3 text-xs leading-5 text-zinc-300"
                      role="region"
                    >
                      <p className="font-medium text-zinc-100">Scope review</p>
                      <p>Status: {taskPacket.scopeStatus}</p>
                      <p>Task type: {taskPacket.taskType}</p>
                      <p>Risk: {taskPacket.riskTier}</p>
                      <p>
                        Expected checks:{" "}
                        {taskPacket.expectedChecks.length > 0
                          ? taskPacket.expectedChecks.join("; ")
                          : "none inferred"}
                      </p>
                      <p>Rollback: {taskPacket.rollbackHint}</p>
                      <p>Safe next action: {taskPacket.safeNextAction}</p>
                      <p>{taskPacket.inspectionSummary}</p>
                      {taskPacket.reasonCodes.length > 0 ? (
                        <p>Reason codes: {taskPacket.reasonCodes.join(", ")}</p>
                      ) : null}
                    </div>
                    {activeBlockedFields.length > 0 ? (
                      <p className="mt-2 text-xs text-amber-100">
                        {activeTaskSubmitted
                          ? `Missing bounded fields: ${activeBlockedFields.join(", ")}.`
                          : emptyTaskPacketText(activeDraftText)}
                      </p>
                    ) : !activeTaskSubmitted ? (
                      <p className="mt-2 text-xs text-emerald-100">
                        Bounded task data present. Preview will stage this draft before requesting
                        evidence.
                      </p>
                    ) : (
                      <p className="mt-2 text-xs text-emerald-100">
                        Bounded task data present. {gateReasons.preview}
                      </p>
                    )}
                  </div>
                ) : null}
                {codingModeActive ? (
                  <div
                    aria-live="polite"
                    className={`mt-3 rounded-md border p-3 text-sm ${
                      previewStatus === "ready" || previewAlreadySatisfied
                        ? "border-emerald-300/35 bg-emerald-300/10 text-emerald-100"
                        : previewStatus === "error" || previewStatus === "blocked"
                          ? "border-amber-300/35 bg-amber-300/10 text-amber-100"
                          : "border-white/10 bg-white/[0.035] text-zinc-300"
                    }`}
                    role="status"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p>{previewMessage}</p>
                      <span
                        aria-label="Trial status badge"
                        className="inline-flex min-h-7 items-center rounded-md border border-white/10 bg-black/25 px-2 text-xs font-semibold text-zinc-100"
                      >
                        {trialStatusBadgeLabel}
                      </span>
                    </div>
                    {previewStatus === "blocked" || previewStatus === "error" ? (
                      <p className="mt-2 text-xs leading-5 opacity-90">
                        Immediate action: {safeNextAction}
                      </p>
                    ) : null}
                  </div>
                ) : null}
                {codingModeActive && activeDesignProposalIntake ? (
                  <div
                    aria-label="Design proposal intake evidence"
                    className="mt-3 rounded-md border border-cyan-300/25 bg-cyan-300/10 p-3 text-sm text-cyan-50"
                    role="region"
                  >
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                      <p className="font-medium text-zinc-100">Design proposal intake</p>
                      <span className="inline-flex min-h-6 items-center rounded-md border border-cyan-300/25 bg-black/25 px-2 text-[11px] font-semibold text-cyan-50">
                        {activeDesignProposalIntake.status}
                      </span>
                    </div>
                    <div className="mt-2 grid gap-1 text-xs leading-5 text-cyan-50/90 sm:grid-cols-2">
                      <p>Status: {activeDesignProposalIntake.status}</p>
                      <p>
                        Packet ready:{" "}
                        {activeDesignProposalIntake.packetReady === null
                          ? "not reported"
                          : activeDesignProposalIntake.packetReady
                            ? "yes"
                            : "no"}
                      </p>
                      <p>
                        Reason codes:{" "}
                        {activeDesignProposalIntake.reasonCodes.length > 0
                          ? activeDesignProposalIntake.reasonCodes.join(", ")
                          : "none"}
                      </p>
                      <p>
                        Blocked by:{" "}
                        {activeDesignProposalIntake.blockedBy.length > 0
                          ? activeDesignProposalIntake.blockedBy.join(", ")
                          : "none"}
                      </p>
                      <p>{authorityFlagText("approval_authority", activeDesignProposalIntake.approvalAuthority)}</p>
                      <p>{authorityFlagText("apply_authority", activeDesignProposalIntake.applyAuthority)}</p>
                    </div>
                    {activeDesignProposalIntake.formatted ? (
                      <pre className="mt-3 max-h-40 overflow-auto rounded-md border border-white/10 bg-black/30 p-2 text-[11px] leading-5 text-cyan-50/85">
                        <code>{activeDesignProposalIntake.formatted}</code>
                      </pre>
                    ) : null}
                  </div>
                ) : null}
                {codingModeActive && previewStatus === "ready" && activeProposedDiff ? (
                  <div className="mt-3 rounded-md border border-emerald-300/25 bg-black/25 p-3 text-sm text-zinc-300">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-medium text-zinc-100">Preview evidence</p>
                        <span
                          aria-label="Preview trial status badge"
                          className="inline-flex min-h-6 items-center rounded-md border border-emerald-300/25 bg-emerald-300/10 px-2 text-[11px] font-semibold text-emerald-100"
                        >
                          {trialStatusBadgeLabel}
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-xs text-zinc-500">No files changed yet</p>
                        <button
                          className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-emerald-300/30 hover:text-emerald-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40"
                          onClick={copyPreviewDiff}
                          type="button"
                        >
                          <Copy aria-hidden="true" size={13} />
                          Copy diff
                        </button>
                      </div>
                    </div>
                    <dl className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                      <div className="rounded-md border border-white/10 bg-white/[0.035] p-2">
                        <dt className="font-medium text-zinc-200">Changed files</dt>
                        <dd className="mt-1 text-zinc-400">
                          {activeChangedFiles.length > 0
                            ? activeChangedFiles.join(", ")
                            : activePreviewTarget || "not reported"}
                        </dd>
                      </div>
                      <div className="rounded-md border border-white/10 bg-white/[0.035] p-2">
                        <dt className="font-medium text-zinc-200">Allowed files</dt>
                        <dd className="mt-1 text-zinc-400">{allowedFilesSummary}</dd>
                      </div>
                      <div className="rounded-md border border-white/10 bg-white/[0.035] p-2">
                        <dt className="font-medium text-zinc-200">Unexpected files</dt>
                        <dd className="mt-1 text-zinc-400">{receiptUnexpectedFilesText}</dd>
                      </div>
                      <div className="rounded-md border border-white/10 bg-white/[0.035] p-2">
                        <dt className="font-medium text-zinc-200">Diff check</dt>
                        <dd className="mt-1 text-zinc-400">{receiptDiffCheckText}</dd>
                      </div>
                    </dl>
                    <p className="mt-2 text-xs text-zinc-400">
                      Changed files:{" "}
                      {activeChangedFiles.length > 0
                        ? activeChangedFiles.join(", ")
                        : activePreviewTarget || "not reported"}
                    </p>
                    {!activeTaskId ? (
                      <p className="mt-2 text-xs text-amber-100">
                        Review-only preview: write actions are unavailable. This preview is for
                        inspection only.
                      </p>
                    ) : null}
                    <pre className="mt-3 max-h-72 overflow-auto rounded-md border border-white/10 bg-black/35 p-3 text-xs leading-5 text-zinc-200">
                      <code>{activeProposedDiff}</code>
                    </pre>
                    {previewDiffCopyStatus ? (
                      <p className="mt-2 text-xs text-zinc-400">{previewDiffCopyStatus}</p>
                    ) : null}
                  </div>
                ) : codingModeActive && previewAlreadySatisfied ? (
                  <div className="mt-3 rounded-md border border-emerald-300/25 bg-black/25 p-3 text-sm text-zinc-300">
                    <p className="font-medium text-zinc-100">No diff preview</p>
                    <p className="mt-2 text-xs leading-5 text-emerald-100">
                      Target already contains the requested change. No files changed, so there is
                      no diff to inspect, approve, apply, or verify.
                    </p>
                    <p className="mt-2 text-xs text-zinc-400">
                      Target file: {taskPacket.targetFile || activePreviewTarget || "not reported"}
                    </p>
                    <dl className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                      <div className="rounded-md border border-white/10 bg-white/[0.035] p-2">
                        <dt className="font-medium text-zinc-200">Changed files</dt>
                        <dd className="mt-1 text-zinc-400">none</dd>
                      </div>
                      <div className="rounded-md border border-white/10 bg-white/[0.035] p-2">
                        <dt className="font-medium text-zinc-200">Approval state</dt>
                        <dd className="mt-1 text-zinc-400">not needed for no-op preview</dd>
                      </div>
                    </dl>
                    <p className="text-xs text-zinc-400">Changed files: none</p>
                  </div>
                ) : null}
                {codingModeActive ? (
                  <div className="mt-3 rounded-md border border-white/10 bg-black/20 p-3 text-sm text-zinc-300">
                    {approvalGateCopy}
                    <div className="mt-2 space-y-1 text-xs text-zinc-500">
                      <p>Preview: {gateReasons.preview}</p>
                      <p>
                        {reviewOnlyPreview ? "Review" : "Approval"}: {gateReasons.approval}
                      </p>
                      {!reviewOnlyPreview ? <p>{approvalPreflightText}</p> : null}
                      <p>{reviewOnlyPreview ? "Write actions" : "Apply"}: {gateReasons.apply}</p>
                      {!reviewOnlyPreview ? <p>{applyScopeText}</p> : null}
                      <p>Verify: {gateReasons.verify}</p>
                    </div>
                    {previewStatus === "ready" && !activeTaskId ? (
                      <p className="mt-2 text-xs text-amber-100">
                        Review-only preview: you can mark this diff reviewed, but write actions
                        stay unavailable until a task-backed preview exists.
                      </p>
                    ) : null}
                    <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                      {canApprovePreview || canMarkPreviewReviewed ? (
                        <button
                          className="inline-flex min-h-10 items-center justify-center rounded-md border border-emerald-300/30 bg-emerald-300/10 px-3 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-300/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40"
                          onClick={approvePreview}
                          type="button"
                        >
                          {canMarkPreviewReviewed
                            ? "Mark preview reviewed"
                            : activeTaskId
                              ? "Approve preview"
                              : "Mark preview reviewed"}
                        </button>
                      ) : null}
                      {approvedAt && activeTaskId && !noApplyPreviewTrial ? (
                        <button
                          className="inline-flex min-h-10 items-center justify-center rounded-md bg-emerald-300 px-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40"
                          disabled={!canApplyApprovedDiff}
                          onClick={applyApprovedDiff}
                          type="button"
                        >
                          {isApplying ? "Applying..." : appliedAt ? "Apply recorded" : "Apply approved diff"}
                        </button>
                      ) : null}
                      {approvedAt && !activeTaskId ? (
                        <button
                          aria-disabled="true"
                          className="inline-flex min-h-10 cursor-not-allowed items-center justify-center rounded-md border border-amber-300/25 bg-amber-300/10 px-3 text-sm font-semibold text-amber-100/80"
                          disabled
                          type="button"
                        >
                          Apply unavailable
                        </button>
                      ) : null}
                    </div>
                    {applyMessage ? <p className="mt-2 text-xs text-zinc-300">{applyMessage}</p> : null}
                  </div>
                ) : null}
                {codingModeActive ? (
                  <div className="mt-3 rounded-md border border-white/10 bg-black/20 p-3 text-sm text-zinc-300">
                    <span className="font-medium text-zinc-100">Verification status:</span>{" "}
                    {verificationStatusLabel}
                    <p className="mt-2 text-xs text-zinc-500">{verificationDisplayMessage}</p>
                    {appliedAt ? (
                      <button
                        className="mt-3 inline-flex min-h-10 items-center justify-center rounded-md border border-emerald-300/30 bg-emerald-300/10 px-3 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40"
                        disabled={!canRunVerification}
                        onClick={verifyAppliedTask}
                        type="button"
                      >
                        {isVerifying
                          ? "Verifying..."
                          : verificationStatus === "passed"
                            ? "Verification recorded"
                            : "Verify docs-only change"}
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </div>

            <div className="mx-auto hidden w-full max-w-5xl rounded-lg border border-cyan-300/15 bg-[#151823]/96 p-2 shadow-xl shadow-black/25 xl:block">
              <div className="flex flex-wrap gap-2 px-1 pb-2">
                <button
                  className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs text-zinc-300 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                  type="button"
                >
                  <Plus aria-hidden="true" size={14} />
                  Context
                </button>
                <button
                  aria-label="Desktop coding mode"
                  aria-pressed={codingModeActive}
                  className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs text-zinc-300 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                  onClick={toggleCodingMode}
                  type="button"
                >
                  <Sparkles aria-hidden="true" size={14} />
                  Coding mode
                </button>
              </div>
              {activeDrawerShell === "diagnostics" ? (
              <section
                aria-label="Proxy trial prompt widget"
                className="mb-2 rounded-md border border-white/10 bg-black/20 p-3 text-xs leading-5 text-zinc-400"
                onKeyDown={handleTrialSwitcherKeyDown}
                tabIndex={0}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-zinc-100">Proxy Trial Prompts</p>
                    <p className="mt-1 text-zinc-500">
                      Preview only. Human review required. No apply, commit, or push from this widget.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      aria-label={trialWidgetEnabled ? "Turn trial prompts off" : "Turn trial prompts on"}
                      aria-pressed={trialWidgetEnabled}
                      className="inline-flex min-h-8 items-center rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15"
                      onClick={() => {
                        const next = !trialWidgetEnabled;
                        setTrialWidgetEnabled(next);
                      }}
                      type="button"
                    >
                      {trialWidgetEnabled ? "Trial prompts on" : "Trial prompts off"}
                    </button>
                  </div>
                </div>
                {trialWidgetEnabled ? (
                  <>
                <section
                  aria-label="Compact proxy diagnostic widget"
                  className="mt-2 rounded-md border border-emerald-300/20 bg-black/25 p-2 text-zinc-200"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="mr-auto font-semibold text-zinc-100">Proxy Test</p>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-amber-300/30 bg-amber-300/10 px-2 text-xs font-semibold text-amber-100">
                      Grade {manualHundredFrontendDiagnostic.currentGrade}
                    </span>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2 text-xs font-semibold text-emerald-100">
                      Safe
                    </span>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-white/10 bg-white/[0.04] px-2 text-xs text-zinc-200">
                      Useful: {manualHundredFrontendDiagnostic.productivePreviews}/{manualHundredFrontendDiagnostic.totalPrompts}
                    </span>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-white/10 bg-white/[0.04] px-2 text-xs text-zinc-200">
                      Safely blocked: {manualHundredFrontendDiagnostic.safeBlockers}
                    </span>
                    <span
                      aria-label="Active run state"
                      className="inline-flex min-h-7 items-center rounded-md border border-cyan-300/25 bg-cyan-300/10 px-2 text-xs font-semibold text-cyan-100"
                    >
                      state: {activeRunStateLabel} | {codingCommandCenterBuildMarker}
                    </span>
                    <button
                      className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100"
                      onClick={() => void copyConciseDiagnosticPacket()}
                      type="button"
                    >
                      <Copy aria-hidden="true" size={13} />
                      Copy diag
                    </button>
                    <button
                      aria-expanded={proxyDiagnosticOpen}
                      className="inline-flex min-h-8 items-center rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15"
                      onClick={() => setProxyDiagnosticOpen((open) => !open)}
                      type="button"
                    >
                      {proxyDiagnosticOpen ? "Close details" : "Details"}
                    </button>
                  </div>
                  <p className="mt-2 text-xs text-zinc-400">
                    Preview-only diagnostics. No worker, provider, queue, apply, commit, or push authority is added.
                  </p>
                  <details
                    className={proofRunControlsClassName}
                    open={proofRunControlsOpen}
                  >
                    <summary className={proofRunControlsSummaryClassName}>
                      Proof run controls
                    </summary>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <button
                        className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-55"
                        disabled={!canRunAllTrialPreviews}
                        onClick={() => void runTenTrialPreviews()}
                        type="button"
                      >
                        {trialBatchRunning ? "Running..." : "Run 10"}
                      </button>
                      <button
                        className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-55"
                        disabled={!canRunAllTrialPreviews}
                        onClick={() => void runTwentyFiveTrialPreviews()}
                        type="button"
                      >
                        {trialBatchRunning ? "Running..." : "Run 25"}
                      </button>
                      <button
                        className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-55"
                        disabled={!canRunAllTrialPreviews}
                        onClick={() => void runHundredTrialPreviews()}
                        type="button"
                      >
                        {trialBatchRunning ? "Running..." : "Run 100"}
                      </button>
                    </div>
                    <p className="mt-2 text-xs text-emerald-100/70">
                      Manual proof only. Opening these controls does not start a run.
                    </p>
                  </details>
                  {trialBatchRunning ? (
                    <div className="mt-2 rounded-md border border-emerald-300/20 bg-emerald-300/10 p-2 text-xs text-emerald-50">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-semibold">Running diagnostic...</span>
                        <span className="text-emerald-100/70">Preview-only; no apply authority.</span>
                      </div>
                      <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-emerald-100/80">
                        <span>{trialBatchProgressTrialText}</span>
                        <span>
                          {trialBatchProgress?.stageLabel ?? "Queued"}
                        </span>
                      </div>
                      <div
                        aria-label="UI-local diagnostic progress"
                        aria-valuemax={trialBatchProgress?.totalSteps ?? 1}
                        aria-valuemin={0}
                        aria-valuenow={trialBatchProgress ? trialBatchProgressNow : undefined}
                        aria-valuetext={trialBatchProgressValueText}
                        className="mt-2 h-2 w-full overflow-hidden rounded-full border border-emerald-200/15 bg-black/45"
                        role="progressbar"
                      >
                        <div
                          className={trialBatchProgressFillClass}
                          style={{ width: `${trialBatchProgressPercent}%` }}
                        />
                      </div>
                      <p className="mt-1 text-emerald-100/65">
                        UI-local diagnostic progress only. No streamed backend progress source is available.
                      </p>
                    </div>
                  ) : null}
                  {trialBatchComplete ? (
                    <div
                      aria-live="polite"
                      className="mt-2 flex flex-wrap items-center justify-between gap-2 rounded-md border border-emerald-300/25 bg-emerald-300/10 p-2 text-xs text-emerald-50"
                      role="status"
                    >
                      <div>
                        <p className="font-semibold">Diagnostic complete</p>
                        <p className="mt-0.5 text-emerald-100/80">
                          Grade {manualHundredFrontendDiagnostic.currentGrade} | Useful: {manualHundredFrontendDiagnostic.productivePreviews}/{manualHundredFrontendDiagnostic.totalPrompts} | Safely blocked: {manualHundredFrontendDiagnostic.safeBlockers}
                        </p>
                      </div>
                      <button
                        aria-label="Copy completed diagnostic"
                        className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15"
                        onClick={() => void copyConciseDiagnosticPacket()}
                        type="button"
                      >
                        <Copy aria-hidden="true" size={13} />
                        Copy diag
                      </button>
                    </div>
                  ) : null}
                  {activeRunState === "blocked" || activeRunState === "failed" ? (
                    <div
                      aria-live="polite"
                      className="mt-2 rounded-md border border-amber-300/25 bg-amber-300/10 p-2 text-xs text-amber-50"
                      role="status"
                    >
                      <p className="font-semibold">
                        {activeRunState === "failed" ? "Diagnostic failed safely" : "Diagnostic blocked safely"}
                      </p>
                      <p className="mt-0.5 text-amber-100/80">
                        {activeRunStateDetail[activeRunState]}
                      </p>
                    </div>
                  ) : null}
                  <p className="sr-only">{currentTrialStep}</p>
                </section>
                {proxyDiagnosticOpen ? (
                  <>
                <div className="mt-2 grid gap-2 rounded-md border border-cyan-300/15 bg-cyan-300/10 p-2 text-cyan-50 sm:grid-cols-5">
                  <p><span className="text-cyan-100/70">Selected</span><br />{selectedTrial.id}</p>
                  <p><span className="text-cyan-100/70">Difficulty</span><br />{selectedTrial.difficulty}</p>
                  <p><span className="text-cyan-100/70">Family</span><br />{selectedTrial.family}</p>
                  <p className="sm:col-span-2"><span className="text-cyan-100/70">Target</span><br />{selectedTrial.targetFile}</p>
                  <p><span className="text-cyan-100/70">Bank</span><br />{sharedBankTrialCount}/{PROXY_TRIAL_BANK_EXPECTED_RECORD_COUNT}</p>
                  <p><span className="text-cyan-100/70">Source</span><br />{selectedTrial.bankSource}</p>
                  <p className="sm:col-span-3"><span className="text-cyan-100/70">Category</span><br />{selectedTrial.category}</p>
                  <p className="sm:col-span-5"><span className="text-cyan-100/70">Expected</span> {selectedTrial.expectedResult}</p>
                </div>
                <section
                  aria-label="Active run state summary"
                  className="mt-2 rounded-md border border-cyan-300/15 bg-black/25 p-2 text-xs text-zinc-300"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold text-cyan-50">Active run state</p>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-cyan-300/25 bg-cyan-300/10 px-2 font-semibold text-cyan-100">
                      {activeRunStateLabel}
                    </span>
                  </div>
                  <p className="mt-1">{activeRunStateDetail[activeRunState]}</p>
                  <p className="mt-1 text-zinc-500">
                    UI-local state only. It does not start a provider, worker, queue, route execution, apply, commit, or push.
                  </p>
                </section>
                <section
                  aria-label="Current diagnostic lifecycle timeline"
                  className="mt-2 rounded-md border border-white/10 bg-black/25 p-2 text-xs text-zinc-300"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold text-zinc-100">Diagnostic lifecycle</p>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-white/10 bg-white/[0.04] px-2 font-semibold text-zinc-200">
                      source: UI-local
                    </span>
                  </div>
                  <ol className="mt-2 grid gap-1 sm:grid-cols-2">
                    {diagnosticLifecycleTimeline.map((item) => (
                      <li
                        className="rounded-md border border-white/10 bg-white/[0.035] p-2"
                        key={item.label}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-medium text-zinc-100">{item.label}</span>
                          <span className="text-[0.68rem] uppercase tracking-[0.12em] text-zinc-500">
                            {item.status}
                          </span>
                        </div>
                        <p className="mt-1 text-zinc-400">{item.detail}</p>
                      </li>
                    ))}
                  </ol>
                  <p className="mt-2 text-zinc-500">
                    No backend streamed task events are claimed by this timeline.
                  </p>
                </section>
                <section
                  aria-label="Prompt staging preview"
                  className="mt-2 rounded-md border border-white/10 bg-black/25 p-2 text-xs text-zinc-300"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold text-zinc-100">Prompt staging preview</p>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-white/10 bg-white/[0.04] px-2 font-semibold text-zinc-200">
                      display-only
                    </span>
                  </div>
                  <ol className="mt-2 grid gap-2 lg:grid-cols-2">
                    {stagedPromptPreviewItems.map((item) => (
                      <li
                        className="rounded-md border border-white/10 bg-white/[0.035] p-2"
                        key={`${item.status}-${item.id}`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-medium text-zinc-100">
                            {item.id}: {item.title}
                          </span>
                          <span className="text-[0.68rem] uppercase tracking-[0.12em] text-zinc-500">
                            {item.status}
                          </span>
                        </div>
                        <p className="mt-1 text-zinc-400">{item.detail}</p>
                      </li>
                    ))}
                  </ol>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {queuePreviewHonestyLabels.map((label) => (
                      <span
                        className="inline-flex min-h-7 items-center rounded-md border border-emerald-300/25 bg-emerald-300/10 px-2 text-[11px] font-semibold text-emerald-100"
                        key={label}
                      >
                        {label}
                      </span>
                    ))}
                  </div>
                  <p className="mt-2 text-zinc-500">
                    Staged prompts are visible for review only; this list does not execute a queue.
                  </p>
                </section>
                <section
                  aria-label="Current-session run history"
                  className="mt-2 rounded-md border border-white/10 bg-black/25 p-2 text-xs text-zinc-300"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold text-zinc-100">Current-session run history</p>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-white/10 bg-white/[0.04] px-2 font-semibold text-zinc-200">
                      current-session only
                    </span>
                  </div>
                  {currentSessionRunHistoryItems.length > 0 ? (
                    <ol className="mt-2 grid gap-2">
                      {currentSessionRunHistoryItems.map((item) => (
                        <li
                          className="rounded-md border border-white/10 bg-white/[0.035] p-2"
                          key={item.id}
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-medium text-zinc-100">{item.title}</span>
                            <span className="text-[0.68rem] uppercase tracking-[0.12em] text-zinc-500">
                              {item.status}
                            </span>
                          </div>
                          <p className="mt-1 text-zinc-500">{item.at}</p>
                          <p className="mt-1 text-zinc-400">{item.detail}</p>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="mt-2 rounded-md border border-white/10 bg-white/[0.025] p-2 text-zinc-500">
                      No current-session run history yet.
                    </p>
                  )}
                  <p className="mt-2 text-zinc-500">
                    This panel does not claim durable history and does not write receipts, files, or backend storage.
                  </p>
                </section>
                <div className="mt-2 grid gap-2 sm:grid-cols-[auto_minmax(0,1fr)_auto_auto]">
                  <button
                    aria-label="Previous proxy trial"
                    className="inline-flex min-h-9 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] px-2 text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                    onClick={() => switchSelectedTrial(-1)}
                    type="button"
                  >
                    <ChevronLeft aria-hidden="true" size={15} />
                  </button>
                  <label className="sr-only" htmlFor="proxy-trial-quick-select">Switch proxy trial</label>
                  <select
                    aria-label="Switch proxy trial"
                    className="min-h-9 rounded-md border border-white/10 bg-black/30 px-2 text-sm text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                    id="proxy-trial-quick-select"
                    onChange={(event) => setSelectedTrialId(event.target.value)}
                    value={selectedTrial.id}
                  >
                    {PROXY_TRIAL_PROMPTS.map((trial) => (
                      <option key={trial.id} value={trial.id}>
                        {trial.id} - {trial.title}
                      </option>
                    ))}
                  </select>
                  <span className="inline-flex min-h-9 items-center rounded-md border border-white/10 px-2.5 text-xs text-zinc-500">
                    Switch tasks: arrows or dropdown
                  </span>
                  <button
                    aria-label="Next proxy trial"
                    className="inline-flex min-h-9 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] px-2 text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                    onClick={() => switchSelectedTrial(1)}
                    type="button"
                  >
                    <ChevronRight aria-hidden="true" size={15} />
                  </button>
                </div>
                <p className="mt-2 rounded-md border border-cyan-300/20 bg-cyan-300/10 p-2 text-cyan-50">
                  {currentTrialStep}
                </p>
                <section
                  aria-label="Proxy preflight overview"
                  className="mt-3 rounded-md border border-cyan-300/20 bg-black/25 p-3 text-zinc-200"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-cyan-50">Preflight Overview</p>
                      <p className="mt-1 text-zinc-400">
                        Read this first, then open raw diagnostics only when the next action needs evidence.
                      </p>
                    </div>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2 text-xs font-semibold text-cyan-100">
                      Manual check gate
                    </span>
                  </div>
                  <dl className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Current gate</dt>
                      <dd className="mt-1 font-semibold text-zinc-100">Browser verification required</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Cartographer dependency</dt>
                      <dd className="mt-1 font-semibold text-rose-100">NO-GO if unavailable</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Preflight authority</dt>
                      <dd className="mt-1 font-semibold text-zinc-100">Status only, no apply-capable work</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Verification requirements</dt>
                      <dd className="mt-1 font-semibold text-amber-100">Exact checks before closeout</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Safety lock</dt>
                      <dd className="mt-1 font-semibold text-emerald-100">No authority changed</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Main bottleneck</dt>
                      <dd className="mt-1 font-semibold text-amber-100">Low productive preview yield</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Next useful action</dt>
                      <dd className="mt-1 font-semibold text-zinc-100">Reduce blockers before live work</dd>
                    </div>
                  </dl>
                </section>
                <section
                  aria-label="Coding advisory helper fleet"
                  className="mt-3 rounded-md border border-white/10 bg-black/25 p-3 text-zinc-200"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-zinc-100">Advisory Helper Fleet</p>
                      <p className="mt-1 text-zinc-500">
                        Proposal-only helpers. No helper is running, applying, calling providers, starting workers, or changing files.
                      </p>
                    </div>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2 text-xs font-semibold text-cyan-100">
                      mode: advisory_only
                    </span>
                  </div>
                  <div className="mt-3 grid gap-2 lg:grid-cols-2">
                    {codingAdvisoryHelpers.map((helper) => (
                      <article
                        className="rounded-md border border-white/10 bg-white/[0.04] p-3"
                        key={helper.name}
                      >
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <p className="font-semibold text-zinc-100">{helper.name}</p>
                            <p className="mt-1 text-xs text-zinc-400">{helper.summary}</p>
                          </div>
                          <span className="inline-flex min-h-6 items-center rounded-md border border-emerald-300/25 bg-emerald-300/10 px-2 text-[11px] font-semibold text-emerald-100">
                            advisory_only
                          </span>
                        </div>
                        <dl className="mt-3 grid gap-2 text-xs">
                          <div>
                            <dt className="text-zinc-500">Proposal</dt>
                            <dd className="text-zinc-200">{helper.proposal}</dd>
                          </div>
                          <div>
                            <dt className="text-zinc-500">Evidence used</dt>
                            <dd className="text-zinc-300">{helper.evidence}</dd>
                          </div>
                          <div>
                            <dt className="text-zinc-500">Manual next step</dt>
                            <dd className="text-zinc-200">{helper.manualNextStep}</dd>
                          </div>
                          <div>
                            <dt className="text-zinc-500">Blocked actions</dt>
                            <dd className="text-zinc-300">{helper.blockedActions}</dd>
                          </div>
                        </dl>
                      </article>
                    ))}
                  </div>
                </section>
                <section
                  aria-label="Codex-like functionality layer"
                  className="mt-3 rounded-md border border-cyan-300/20 bg-black/25 p-3 text-zinc-200"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-cyan-50">Codex-like Functionality Layer</p>
                      <p className="mt-1 text-zinc-500">
                        Read-only capability status. Future behavior is visible here before any authority is granted.
                      </p>
                    </div>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-amber-300/30 bg-amber-300/10 px-2 text-xs font-semibold text-amber-100">
                      gated functionality
                    </span>
                  </div>
                  <dl className="mt-3 grid gap-2 lg:grid-cols-2">
                    {codexLikeFunctionalityRows.map((item) => (
                      <div
                        className="rounded-md border border-white/10 bg-white/[0.04] p-3"
                        key={item.label}
                      >
                        <dt className="flex flex-wrap items-start justify-between gap-2 text-sm font-semibold text-zinc-100">
                          <span>{item.label}</span>
                          <span className="inline-flex min-h-6 items-center rounded-md border border-white/10 bg-black/25 px-2 text-[11px] font-semibold text-zinc-200">
                            {item.state}
                          </span>
                        </dt>
                        <dd className="mt-2 text-xs leading-5 text-zinc-300">{item.detail}</dd>
                      </div>
                    ))}
                  </dl>
                  <p className="mt-3 rounded-md border border-white/10 bg-black/25 p-2 text-xs text-zinc-400">
                    No live preview, queue, worker, provider, route execution, apply, commit, push, or shell execution control is enabled by this layer.
                  </p>
                </section>
                <section
                  aria-label="100 prompt diagnostic summary"
                  className="mt-3 rounded-md border border-emerald-300/20 bg-emerald-300/10 p-3 text-zinc-200"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-emerald-100">100 Prompt Diagnostic Summary</p>
                      <p className="mt-1 text-zinc-300">{manualHundredFrontendDiagnostic.lastDiagnosticStatus}</p>
                    </div>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-amber-300/30 bg-amber-300/10 px-2 text-xs font-semibold text-amber-100">
                      Grade {manualHundredFrontendDiagnostic.currentGrade}
                    </span>
                  </div>
                  <dl className="mt-3 grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
                    <div className="min-w-0 rounded-md border border-white/10 bg-black/25 p-2 sm:col-span-3 lg:col-span-3">
                      <dt className="text-zinc-500">25-run status</dt>
                      <dd className="mt-1 font-semibold text-zinc-100">
                        {manualHundredStatusLabels.terminalTwentyFiveStatus}
                      </dd>
                    </div>
                    <div className="min-w-0 rounded-md border border-white/10 bg-black/25 p-2 sm:col-span-3 lg:col-span-3">
                      <dt className="text-zinc-500">100-run status</dt>
                      <dd className="mt-1 font-semibold text-zinc-100">
                        {manualHundredStatusLabels.terminalHundredStatus}
                      </dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Total prompts</dt>
                      <dd className="mt-1 font-semibold text-zinc-100">{manualHundredFrontendDiagnostic.totalPrompts}</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Productive previews</dt>
                      <dd className="mt-1 font-semibold text-amber-100">{manualHundredFrontendDiagnostic.productivePreviews}</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Already-satisfied no-ops</dt>
                      <dd className="mt-1 font-semibold text-zinc-100">{manualHundredFrontendDiagnostic.alreadySatisfiedNoops}</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Safe blockers</dt>
                      <dd className="mt-1 font-semibold text-zinc-100">{manualHundredFrontendDiagnostic.safeBlockers}</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Unsafe failures</dt>
                      <dd className="mt-1 font-semibold text-emerald-100">{manualHundredFrontendDiagnostic.unsafeFailures}</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2">
                      <dt className="text-zinc-500">Unexpected file attempts</dt>
                      <dd className="mt-1 font-semibold text-emerald-100">{manualHundredFrontendDiagnostic.unexpectedFiles}</dd>
                    </div>
                    <div className="rounded-md border border-white/10 bg-black/25 p-2 sm:col-span-3 lg:col-span-4">
                      <dt className="text-zinc-500">Authority flags</dt>
                      <dd className="mt-1 text-zinc-100">
                        All false: apply, commit, push, execute-approved, provider, shell expansion, reset/stash/clean, and Phase 7 live preview.
                      </dd>
                      <dd className="mt-2 grid gap-1 text-[11px] leading-4 text-zinc-300 sm:grid-cols-2">
                        {manualHundredAuthorityFlags.map((flag) => (
                          <code
                            className="min-w-0 rounded border border-white/10 bg-black/30 px-1.5 py-1 font-mono break-all"
                            key={flag}
                          >
                            {flag}
                          </code>
                        ))}
                      </dd>
                    </div>
                  </dl>
                  <details
                    aria-label="Raw diagnostic status values"
                    className="mt-3 rounded-md border border-white/10 bg-black/25 p-2"
                  >
                    <summary className="cursor-pointer text-xs font-semibold text-zinc-300">
                      Raw diagnostic status values
                    </summary>
                    <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                      <div className="min-w-0 rounded-md border border-white/10 bg-black/30 p-2">
                        <dt className="text-zinc-500">Raw 25-run status</dt>
                        <dd className="mt-1 font-mono text-[11px] leading-4 text-zinc-300 break-all">
                          raw: {manualHundredFrontendDiagnostic.terminalTwentyFiveStatus}
                        </dd>
                      </div>
                      <div className="min-w-0 rounded-md border border-white/10 bg-black/30 p-2">
                        <dt className="text-zinc-500">Raw 100-run status</dt>
                        <dd className="mt-1 font-mono text-[11px] leading-4 text-zinc-300 break-all">
                          raw: {manualHundredFrontendDiagnostic.terminalHundredStatus}
                        </dd>
                      </div>
                    </dl>
                  </details>
                  <p className="mt-3 rounded-md border border-amber-300/20 bg-amber-300/10 p-2 text-amber-100">
                    Safety passed and authority stayed false. Productive yield is low, so next work is blocker reduction and preflight organization, not CSS or live authority.
                  </p>
                  <p className="mt-2 rounded-md border border-white/10 bg-black/25 p-2 text-zinc-200">
                    Next recommended fix batch: {manualHundredFrontendDiagnostic.nextRecommendedFixBatch}
                  </p>
                </section>
                <section
                  aria-label="Top blocker explanations"
                  className="mt-3 rounded-md border border-white/10 bg-black/25 p-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-zinc-100">Top Blocker Categories</p>
                      <p className="mt-1 text-zinc-500">
                        Specific buckets are actionable now. No unknown_blocker category is expected in the clean S3 diagnostic.
                      </p>
                    </div>
                    <span className="inline-flex min-h-7 items-center rounded-md border border-emerald-300/25 bg-emerald-300/10 px-2 text-xs font-semibold text-emerald-100">
                      unknown_blocker: 0
                    </span>
                  </div>
                  <div className="mt-3 grid gap-2 lg:grid-cols-2">
                    {manualHundredTopBlockers.map((blocker) => (
                      <details key={blocker.code} className="rounded-md border border-white/10 bg-black/25 p-2">
                        <summary className="cursor-pointer text-sm font-semibold text-zinc-100">
                          {blocker.code}: {blocker.count} <span className="text-xs font-normal text-zinc-500">[{blocker.kind}]</span>
                        </summary>
                        <dl className="mt-2 grid gap-2 text-xs">
                          <div>
                            <dt className="text-zinc-500">Meaning</dt>
                            <dd className="text-zinc-200">{blocker.meaning}</dd>
                          </div>
                          <div>
                            <dt className="text-zinc-500">Why it matters</dt>
                            <dd className="text-zinc-200">{blocker.why}</dd>
                          </div>
                          <div>
                            <dt className="text-zinc-500">What Britton should do next</dt>
                            <dd className="text-zinc-200">{blocker.next}</dd>
                          </div>
                        </dl>
                      </details>
                    ))}
                  </div>
                </section>
                <details
                  aria-label="Manual 100 Frontend Diagnostic Check"
                  className="mt-3 rounded-md border border-cyan-300/20 bg-cyan-300/10 p-3"
                >
                  <summary className="cursor-pointer font-semibold text-cyan-50">Manual 100 Frontend Diagnostic Check</summary>
                  <p className="mt-1 text-zinc-300">
                    Browser verification is still required. This checklist is display-only and does not store results or grant authority.
                  </p>
                  <ol className="mt-3 grid gap-1 text-zinc-200 sm:grid-cols-2">
                    {manualHundredChecklist.map((item, index) => (
                      <li key={item} className="rounded-md border border-white/10 bg-black/25 p-2">
                        {index + 1}. {item}
                      </li>
                    ))}
                  </ol>
                </details>
                  </>
                ) : null}
                {proxyDiagnosticOpen ? (
                  <details
                    aria-label="Advanced proxy trial controls"
                    className="mt-3 rounded-md border border-white/10 bg-black/25 p-3"
                  >
                    <summary className="cursor-pointer text-xs font-semibold text-zinc-300">
                      Advanced trial controls
                    </summary>
                    {trialBatchRunning ? (
                      <p className="mt-2 rounded-md border border-white/10 bg-black/20 p-2 text-xs text-zinc-400">
                        Showing UI-local diagnostic stage and trial position only. No streamed backend progress source is available.
                      </p>
                    ) : null}
                    <div className="mt-3 grid gap-3 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                      <div>
                        <label className="sr-only" htmlFor="proxy-trial-search">Search trials</label>
                        <div className="flex items-center gap-2 rounded-md border border-white/10 bg-black/25 px-2">
                          <Search aria-hidden="true" size={14} />
                          <input
                            className="min-h-9 w-full bg-transparent text-sm text-zinc-100 placeholder:text-zinc-600 focus-visible:outline-none"
                            id="proxy-trial-search"
                            onChange={(event) => setTrialSearch(event.target.value)}
                            placeholder="Search trials"
                            value={trialSearch}
                          />
                        </div>
                        <label className="sr-only" htmlFor="proxy-trial-select">Select trial</label>
                        <select
                          className="mt-2 min-h-40 w-full rounded-md border border-white/10 bg-black/30 p-2 text-sm text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                          id="proxy-trial-select"
                          onChange={(event) => setSelectedTrialId(event.target.value)}
                          size={Math.min(10, Math.max(4, filteredTrials.length))}
                          value={selectedTrial.id}
                        >
                          {filteredTrials.map((trial) => (
                            <option key={trial.id} value={trial.id}>
                              {trial.id} - {trial.title}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="rounded-md border border-white/10 bg-black/25 p-3">
                        <p className="font-semibold text-zinc-100">{selectedTrial.id}: {selectedTrial.title}</p>
                        <p className="mt-2 text-zinc-300">{selectedTrial.taskPrompt}</p>
                        <dl className="mt-3 grid gap-2 sm:grid-cols-2">
                          <div><dt className="text-zinc-500">Target file</dt><dd className="text-zinc-100">{selectedTrial.targetFile}</dd></div>
                          <div><dt className="text-zinc-500">Allowed files</dt><dd className="text-zinc-100">{selectedTrial.allowedFiles.join(", ")}</dd></div>
                          <div><dt className="text-zinc-500">Expected changed_files</dt><dd className="text-zinc-100">{selectedTrial.expectedChangedFiles.length ? selectedTrial.expectedChangedFiles.join(", ") : "none"}</dd></div>
                          <div><dt className="text-zinc-500">Shared record</dt><dd className="text-zinc-100">{selectedTrial.sharedBankRecordId}</dd></div>
                          <div><dt className="text-zinc-500">Category</dt><dd className="text-zinc-100">{selectedTrial.category}</dd></div>
                          <div><dt className="text-zinc-500">Risk</dt><dd className="text-zinc-100">{selectedTrial.riskLevel}</dd></div>
                          <div><dt className="text-zinc-500">Backend result</dt><dd className="text-zinc-100">{selectedTrial.expectedBackendResult}</dd></div>
                          <div><dt className="text-zinc-500">UI result</dt><dd className="text-zinc-100">{selectedTrial.expectedUiResult}</dd></div>
                          <div><dt className="text-zinc-500">Stop condition</dt><dd className="text-zinc-100">{selectedTrial.stopCondition}</dd></div>
                        </dl>
                        <button
                          className="mt-3 inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100"
                          onClick={copyExpectedOutput}
                          type="button"
                        >
                          Copy expected output
                        </button>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15" onClick={loadSelectedTrial} type="button">Load prompt</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md bg-cyan-200 px-2.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-100 disabled:cursor-not-allowed disabled:opacity-55" disabled={!canRunSelectedTrialPreview} onClick={() => void runSelectedTrialPreview()} type="button">Preview selected</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-55" disabled={!canRunAllTrialPreviews} onClick={() => void runTenTrialPreviews()} type="button">{trialBatchRunning ? "Running diagnostic..." : "Run 10 previews"}</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-55" disabled={!canRunAllTrialPreviews} onClick={() => void runTwentyFiveTrialPreviews()} type="button">{trialBatchRunning ? "Running diagnostic..." : "Run 25 previews"}</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-55" disabled={!canRunAllTrialPreviews} onClick={() => void runHundredTrialPreviews()} type="button">{trialBatchRunning ? "Running diagnostic..." : "Run 100 previews"}</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-55" disabled={!canRunAllTrialPreviews} onClick={() => void runAllTrialPreviews()} type="button">{trialBatchRunning ? "Running diagnostic..." : "Run all safe previews"}</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={copyTrialPrompt} type="button"><Copy aria-hidden="true" size={13} />Copy prompt</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyWidgetDryRunEvidencePacket()} type="button"><Copy aria-hidden="true" size={13} />Copy 100-prompt dry run</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyBrowserWidgetManualAcceptanceGatePacket()} type="button"><Copy aria-hidden="true" size={13} />Copy manual check</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyControlledBrowserPreviewRunApprovalGatePacket()} type="button"><Copy aria-hidden="true" size={13} />Copy preview gate</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15" onClick={() => void copyTwentyFivePreviewApprovalPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy 25 approval</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-amber-300/30 bg-amber-300/10 px-2.5 text-xs font-semibold text-amber-100 transition hover:bg-amber-300/15" onClick={() => void copyTwentyFivePreviewEvidenceReviewPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy 25-review</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15" onClick={() => void copyHundredPreviewApprovalPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy 100 approval</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-amber-300/30 bg-amber-300/10 px-2.5 text-xs font-semibold text-amber-100 transition hover:bg-amber-300/15" onClick={() => void copyHundredPreviewEvidenceReviewPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy 100-review</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-amber-300/30 bg-amber-300/10 px-2.5 text-xs font-semibold text-amber-100 transition hover:bg-amber-300/15" onClick={() => void copyProductivePreviewRouteGapPlanPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy route-gap plan</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-amber-300/30 bg-amber-300/10 px-2.5 text-xs font-semibold text-amber-100 transition hover:bg-amber-300/15" onClick={() => void copyProductivePreviewRouteGapImplementationGatePacket()} type="button"><Copy aria-hidden="true" size={13} />Copy route-gap gate</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-amber-300/30 bg-amber-300/10 px-2.5 text-xs font-semibold text-amber-100 transition hover:bg-amber-300/15" onClick={() => void copyProductivePreviewRouteGapClassifierPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy route-gap fix</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-amber-300/30 bg-amber-300/10 px-2.5 text-xs font-semibold text-amber-100 transition hover:bg-amber-300/15" onClick={() => void copyRecurringBlockerFixBatchPlanPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy blocker plan</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-amber-300/30 bg-amber-300/10 px-2.5 text-xs font-semibold text-amber-100 transition hover:bg-amber-300/15" onClick={() => void copyBlockedAfterRetriesDiagnosticHardeningPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy retry fix</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-amber-300/30 bg-amber-300/10 px-2.5 text-xs font-semibold text-amber-100 transition hover:bg-amber-300/15" onClick={() => void copyHb03GenericBlockerRegressionFixPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy frontend fix</button>
                      <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" disabled={!canClearActiveTask} onClick={clearActiveTask} type="button">Clear trial</button>
                      <span className="inline-flex min-h-8 items-center rounded-md border border-white/10 px-2.5 text-xs text-zinc-500">Hotkey: Alt+P</span>
                    </div>
                    {trialBatchSummary ? (
                      <div className="mt-3 rounded-md border border-white/10 bg-black/25 p-2">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="font-semibold text-zinc-100">Run summary</p>
                          <div className="flex flex-wrap gap-2">
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyTrialRunSummary()} type="button"><Copy aria-hidden="true" size={13} />Copy run summary</button>
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-amber-300/30 bg-amber-300/10 px-2.5 text-xs font-semibold text-amber-100 transition hover:bg-amber-300/15" onClick={() => void copyTenPreviewBrowserEvidenceReviewPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy 10-review</button>
                          </div>
                        </div>
                        <details className="mt-2 rounded-md border border-white/10 bg-black/20 p-2">
                          <summary className="cursor-pointer text-xs font-semibold text-zinc-300">Older packets</summary>
                          <div className="mt-2 flex flex-wrap gap-2">
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyPhase7ReadinessGate()} type="button"><Copy aria-hidden="true" size={13} />Copy Phase 7 gate</button>
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyTerminalSmokeDesignPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy 25-prompt design</button>
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copySharedPromptBankDesignPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy prompt-bank design</button>
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyFrontendSharedBankIntegrationPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy frontend bank packet</button>
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyWidgetDryRunEvidencePacket()} type="button"><Copy aria-hidden="true" size={13} />Copy 100-prompt dry run</button>
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyControlledBrowserPreviewRunApprovalGatePacket()} type="button"><Copy aria-hidden="true" size={13} />Copy preview gate</button>
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyImplementationCloseoutPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy closeout packet</button>
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyOperatorAcceptancePacket()} type="button"><Copy aria-hidden="true" size={13} />Copy acceptance packet</button>
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyTerminalSmokeImplementationDecisionPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy terminal decision</button>
                            <button className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100" onClick={() => void copyTerminalSmokeScaffoldApprovalPacket()} type="button"><Copy aria-hidden="true" size={13} />Copy scaffold approval</button>
                          </div>
                        </details>
                        <pre className="mt-2 max-h-36 overflow-auto whitespace-pre-wrap font-mono text-[11px] leading-5 text-zinc-400">{trialBatchSummary}</pre>
                      </div>
                    ) : null}
                  </details>
                ) : null}
                {trialPromptCopyStatus ? <p className="mt-2 text-zinc-400">{trialPromptCopyStatus}</p> : null}
                <p className="mt-2 text-zinc-500">Blocked safely still matters, but does not prove productive coding.</p>
                  </>
                ) : (
                  <p className="mt-2 rounded-md border border-white/10 bg-black/25 p-2 text-zinc-400">
                    Trial prompts are hidden. Turn them on to pick, load, or preview HB tasks.
                  </p>
                )}
                {trialWidgetEnabled && proxyDiagnosticOpen ? (
                <details className="mt-3 rounded-md border border-white/10 bg-black/25 p-3">
                  <summary className="cursor-pointer text-xs font-semibold text-zinc-300">
                    Preview audit logs
                  </summary>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold text-zinc-100">Audit log controls</p>
                    <div className="flex flex-wrap gap-2">
                      <button
                        className="inline-flex min-h-8 items-center rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-55"
                        disabled={!canRecordAuditLog}
                        onClick={recordCurrentAuditLog}
                        type="button"
                      >
                        Record reviewed audit
                      </button>
                      <button
                        className="inline-flex min-h-8 items-center rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100"
                        onClick={() => void copyCodexFixPacket()}
                        type="button"
                      >
                        <Copy aria-hidden="true" size={13} />
                        Copy Codex fix packet
                      </button>
                      <button
                        className="inline-flex min-h-8 items-center rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100"
                        onClick={() => void copySessionLogs()}
                        type="button"
                      >
                        <Copy aria-hidden="true" size={13} />
                        Copy audit logs
                      </button>
                      <button
                        className="inline-flex min-h-8 items-center rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 disabled:cursor-not-allowed disabled:opacity-55"
                        disabled={sessionLogs.length === 0}
                        onClick={() => setSessionLogs([])}
                        type="button"
                      >
                        Reset logs
                      </button>
                    </div>
                  </div>
                  {sessionLogs.length > 0 ? (
                    <ol className="mt-2 max-h-36 space-y-1 overflow-auto text-xs text-zinc-400">
                      {sessionLogs.map((entry) => (
                        <li key={entry.id} className="rounded-md border border-white/10 bg-black/20 p-2">
                          <span className="font-mono text-zinc-500">{formatSessionLogTime(entry.at)}</span>{" "}
                          <span className="font-semibold text-zinc-200">{entry.title}</span>{" "}
                          <span className="text-zinc-500">[{entry.status}]</span>
                          <pre className="mt-1 whitespace-pre-wrap font-mono text-[11px] leading-5 text-zinc-400">
                            {entry.detail}
                          </pre>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="mt-2 text-zinc-500">
                      {previewStatus !== "idle" && previewStatus !== "loading"
                        ? "No reviewed audit entries yet. Copy audit logs still includes the current page evidence."
                        : "No trial runs logged yet."}
                    </p>
                  )}
                </details>
                ) : null}
              </section>
              ) : null}
              <label className="sr-only" htmlFor="coding-command-composer">
                Coding command composer
              </label>
              <textarea
                className="min-h-28 w-full resize-none rounded-md border border-white/10 bg-black/25 px-3 py-3 text-base leading-6 text-zinc-100 placeholder:text-zinc-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                id="coding-command-composer"
                onChange={(event) => updateActiveDraftText(event.target.value)}
                placeholder="Ask for a plan, start a coding task, or gather repo context."
                value={activeDraftText}
              />
              <div className="mt-2 grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                <button
                  aria-label="Desktop submit task"
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                  disabled={!activeDraftText.trim()}
                  onClick={submitActiveTask}
                  onPointerUp={(event) => {
                    if (!activeDraftText.trim()) return;
                    event.preventDefault();
                    submitActiveTask();
                  }}
                  type="button"
                >
                  <Send aria-hidden="true" size={15} />
                  Submit task
                </button>
                <button
                  aria-label="Desktop preview safely"
                  className="inline-flex min-h-10 items-center justify-center rounded-md bg-cyan-200 px-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-100 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                  disabled={!canRequestPreview || previewStatus === "loading"}
                  onClick={() => void requestSafePreview()}
                  onPointerUp={(event) => {
                    if (!canRequestPreview || previewStatus === "loading") return;
                    event.preventDefault();
                    void requestSafePreview();
                  }}
                  type="button"
                >
                  {previewStatus === "loading" ? "Previewing..." : "Preview safely"}
                </button>
                <button
                  aria-label="Desktop clear task"
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.04] px-3 text-sm font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 disabled:cursor-not-allowed disabled:opacity-45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                  disabled={!canClearActiveTask}
                  onClick={clearActiveTask}
                  type="button"
                >
                  <X aria-hidden="true" size={15} />
                  Clear
                </button>
              </div>
              {codingModeActive ? (
                <p className="mt-2 text-xs text-zinc-500">
                  Enter adds a line break. Use Submit task to stage the packet, then Preview safely
                  to request evidence.
                </p>
              ) : null}
            </div>
          </div>
        </section>

        <aside
          aria-label="Mobile safety and task status"
          className="mb-2 rounded-lg border border-white/10 bg-[#10131b]/90 p-3 shadow-2xl shadow-black/30 backdrop-blur-xl xl:hidden"
          role="complementary"
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                Task state
              </p>
              <h2 className="mt-1 text-base font-semibold">{visibleTaskStateLabel}</h2>
            </div>
            <span className="rounded-md border border-emerald-300/35 bg-emerald-300/10 px-2.5 py-1 text-xs font-medium text-emerald-100">
              Safe
            </span>
          </div>

          {trialDiagnosticVisible ? (
            <div
              aria-label="Visible trial diagnostic activity"
              className="mt-4 rounded-lg border border-emerald-300/25 bg-emerald-300/10 p-3 text-xs leading-5 text-emerald-50"
              role="status"
            >
              <p className="font-semibold">{trialDiagnosticStateLabel}</p>
              <p className="mt-1">{trialDiagnosticActivityText}</p>
              <p className="mt-1 text-emerald-100/70">
                UI-local diagnostic lifecycle only; no backend stream, provider, worker, queue,
                apply, commit, or push authority is claimed.
              </p>
            </div>
          ) : null}

          <div className="mt-5 space-y-2">
            {safetySteps.map((step) => (
              <div
                className={`flex min-h-10 items-center justify-between rounded-md border px-3 text-sm ${
                  (step === "Draft" && taskStateLabel === "Draft") ||
                  (step === "Preview" && previewStatus === "ready") ||
                  (step === "Approval" && Boolean(approvedAt)) ||
                  (step === "Apply" && Boolean(appliedAt)) ||
                  (step === "Verify" && verificationStatus === "passed")
                    ? "border-cyan-300/35 bg-cyan-300/10 text-cyan-50"
                    : "border-white/10 bg-white/[0.035] text-zinc-500"
                }`}
                key={step}
              >
                <span>{step}</span>
                <span className="text-xs">
                  {step === "Draft" && activeDraftText.trim()
                    ? "Current"
                    : step === "Preview" && canRequestPreview
                      ? previewStatus === "ready"
                        ? "Evidence"
                        : "Ready"
                      : step === "Approval" && canApprovePreview
                        ? "Ready"
                        : step === "Approval" && approvedAt
                          ? "Approved"
                          : step === "Apply" && canApplyApprovedDiff
                            ? "Ready"
                            : step === "Verify" && verificationStatus === "passed"
                              ? "Passed"
                              : step === "Verify" && verificationStatus === "running"
                                ? "Running"
                                : step === "Verify" && appliedAt
                                  ? "Required"
                              : "Locked"}
                </span>
              </div>
            ))}
          </div>

          <div className="mt-5 rounded-lg border border-white/10 bg-black/20 p-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
              Source Proxy
            </p>
            <p className="mt-2 text-sm text-zinc-300">Safe preview/apply wiring is gated.</p>
            <p className="mt-2 text-xs leading-5 text-zinc-500">
              Preview requires bounded task data. Approval requires preview evidence. Apply requires
              explicit local approval. Commit and push controls are not available here.
            </p>
          </div>

          <div
            aria-label="Compact task progress"
            className="mt-5 rounded-lg border border-cyan-300/20 bg-cyan-300/10 p-3 text-xs leading-5 text-zinc-300"
            role="region"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-semibold uppercase tracking-[0.18em] text-cyan-100">
                  Task progress
                </p>
                <p className="mt-1 text-zinc-100">
                  {progressTimerActive ? progressElapsedText : "Working time unavailable"}
                </p>
              </div>
              <span className="rounded-md border border-cyan-300/30 bg-black/25 px-2.5 py-1 font-semibold text-cyan-100">
                {activeRunState}
              </span>
            </div>
            <dl className="mt-3 grid gap-2">
              <div className="rounded-md border border-white/10 bg-black/25 p-2">
                <dt className="font-semibold text-zinc-100">Current step</dt>
                <dd className="mt-1">{compactCurrentStepText}</dd>
              </div>
              <div className="rounded-md border border-white/10 bg-black/25 p-2">
                <dt className="font-semibold text-zinc-100">Next safe action</dt>
                <dd className="mt-1">{compactNextActionText}</dd>
              </div>
              <div className="rounded-md border border-white/10 bg-black/25 p-2">
                <dt className="font-semibold text-zinc-100">Evidence</dt>
                <dd className="mt-1">{compactEvidenceText}</dd>
              </div>
            </dl>
          </div>

          {activeDrawerShell === "evidence" ? (
          <details
            className="mt-5 rounded-lg border border-white/10 bg-black/20 p-3"
            open={rightRailDetailsOpen || activeDrawerShell === "evidence"}
          >
            <summary className="cursor-pointer text-xs font-semibold uppercase tracking-[0.18em] text-zinc-400">
              Evidence Details and Receipts
            </summary>
            <div className="mt-4 space-y-5">
          <div
            aria-label="Codex-style progress surface"
            className="rounded-lg border border-cyan-300/20 bg-cyan-300/10 p-3 text-xs leading-5 text-zinc-300"
            role="region"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-semibold uppercase tracking-[0.18em] text-cyan-100">
                  Detailed Progress
                </p>
                <p className="mt-1 text-zinc-100">
                  {progressTimerActive ? progressElapsedText : "Working time unavailable"}
                </p>
              </div>
              <span className="rounded-md border border-cyan-300/30 bg-black/25 px-2.5 py-1 font-semibold text-cyan-100">
                {activeRunState}
              </span>
            </div>

            <dl className="mt-3 grid gap-2">
              <div className="rounded-md border border-white/10 bg-black/25 p-2">
                <dt className="font-semibold text-zinc-100">Current step</dt>
                <dd className="mt-1">Progress current step: {progressCurrentStepText}</dd>
              </div>
              <div className="rounded-md border border-white/10 bg-black/25 p-2">
                <dt className="font-semibold text-zinc-100">Next step</dt>
                <dd className="mt-1">Progress next step: {progressNextStepText}</dd>
              </div>
            </dl>

            <div aria-label="Public Thinking and Working summaries" className="mt-3 grid gap-2">
              {publicWorkItems.map((item) => (
                <div
                  className="rounded-md border border-white/10 bg-black/25 p-2"
                  key={item.label}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold text-zinc-100">{item.summary}</p>
                    <span className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[0.7rem] uppercase tracking-[0.14em] text-zinc-400">
                      source: {item.source}
                    </span>
                  </div>
                  <p className="mt-1">Evidence: {item.evidence}</p>
                  <p className="mt-1 text-zinc-500">
                    Timestamp: {item.timestamp} | evidence_unavailable:{" "}
                    {item.evidence_unavailable ? "true" : "false"}
                  </p>
                </div>
              ))}
            </div>

            <dl aria-label="Progress evidence counts" className="mt-3 grid gap-2 sm:grid-cols-2">
              {progressEvidenceCountItems.map((item) => (
                <div
                  className="rounded-md border border-white/10 bg-black/25 p-2"
                  key={item.label}
                >
                  <dt className="font-semibold text-zinc-100">{item.label}</dt>
                  <dd className="mt-1">{item.value}</dd>
                  <dd className="mt-1 text-zinc-500">{item.detail}</dd>
                </div>
              ))}
            </dl>

            <ol aria-label="Progress checklist" className="mt-3 grid gap-2">
              {progressChecklistItems.map((item) => (
                <li
                  className="rounded-md border border-white/10 bg-black/25 p-2"
                  key={item.label}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold text-zinc-100">{item.label}</p>
                  <span className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[0.7rem] uppercase tracking-[0.14em] text-zinc-400">
                      {item.state}
                    </span>
                  </div>
                  <p className="mt-1">Detail: {item.detail}</p>
                </li>
              ))}
            </ol>

            <p className="mt-3 rounded-md border border-emerald-300/20 bg-emerald-300/10 p-2 text-emerald-100">
              No hidden chain-of-thought is displayed. Public work summaries use visible UI
              evidence only.
            </p>
          </div>

          <div
            aria-label="Coding task timeline and evidence stream"
            className="rounded-lg border border-white/10 bg-black/20 p-3 text-xs leading-5 text-zinc-400"
            role="region"
          >
            <p className="font-semibold uppercase tracking-[0.18em] text-zinc-500">
              Task timeline
            </p>
            {trialDiagnosticVisible ? (
              <p className="mt-2 rounded-md border border-emerald-300/20 bg-emerald-300/10 p-2 text-emerald-100">
                Real coding task timeline is waiting; UI-local trial diagnostic is visible
                separately: {trialDiagnosticActivityText}
              </p>
            ) : null}
            <ol className="mt-3 space-y-2">
              {timelineEvents.map((event) => (
                <li
                  className="rounded-md border border-white/10 bg-white/[0.035] p-2"
                  key={event.step}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium text-zinc-100">{event.title}</p>
                    <p className="text-[0.7rem] uppercase tracking-[0.14em] text-zinc-500">
                      {event.status}
                    </p>
                  </div>
                  <p className="mt-1">
                    Source: {event.source} · Authority: {event.authority} · Time:{" "}
                    {event.timestamp}
                  </p>
                  <p className="mt-1 text-zinc-300">Evidence: {event.evidence}</p>
                </li>
              ))}
            </ol>
            <p className="mt-4 font-semibold uppercase tracking-[0.18em] text-zinc-500">
              Evidence stream
            </p>
            <dl className="mt-2 grid gap-2">
              {evidenceStreamItems.map((item) => (
                <div
                  className="rounded-md border border-white/10 bg-white/[0.025] p-2"
                  key={item.label}
                >
                  <dt className="font-medium text-zinc-200">{item.label}</dt>
                  <dd className="mt-1">{item.value}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="rounded-lg border border-white/10 bg-black/20 p-3 text-xs leading-5 text-zinc-400">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-semibold uppercase tracking-[0.18em] text-zinc-500">
                Verification receipt
              </p>
              <button
                className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                onClick={copyReceipt}
                type="button"
              >
                <Copy aria-hidden="true" size={13} />
                Copy receipt
              </button>
              <button
                className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                onClick={() => void copyRollbackPacket()}
                type="button"
              >
                <Copy aria-hidden="true" size={13} />
                Copy rollback packet
              </button>
            </div>
            <p className="mt-2 text-zinc-300">{receiptReadinessText}</p>
            <p>Prompt: {lifecyclePromptText}</p>
            <p>Active chat/run: {lifecycleRunLabel}</p>
            <p>Workspace context: {activeWorkspaceContext.label}</p>
            <p>Workspace path: {activeWorkspaceContext.path}</p>
            <p>Workspace availability: {activeWorkspaceContext.availability}</p>
            <p>Workspace access: {activeWorkspaceContext.access}</p>
            <p>Workspace dirty state: {activeWorkspaceContext.dirtyState}</p>
            <p>Workspace authority: {activeWorkspaceContext.authority}</p>
            <p>Provider selected: {activeProviderStatus.label}</p>
            <p>Provider status: {activeProviderStatus.status}</p>
            <p>Model selected: {activeProviderModel.modelLabel}</p>
            <p>Model status: {activeProviderModel.status}</p>
            <p>Provider call made: false</p>
            <p>Provider cost warning: {activeProviderModel.costWarning}</p>
            <p>Provider blocked reason: {activeProviderModel.blockedReason || "none"}</p>
            <p>Lifecycle status: {lifecycleReceiptStatusText}</p>
            <p>Progress source: {lifecycleProgressSourceText}</p>
            <p>Progress elapsed: {progressElapsedText}</p>
            <p>Progress explored files: {progressExploredFilesText}</p>
            <p>Progress searches: {progressSearchesText}</p>
            <p>Progress commands: {progressCommandsText}</p>
            <p>Progress outputs/artifacts: {progressOutputsArtifactsText}</p>
            <p>Progress sources/evidence: {progressSourcesEvidenceText}</p>
            <p>Progress blocked/done state: {progressBlockedDoneStateText}</p>
            <p>Progress current step: {progressCurrentStepText}</p>
            <p>Progress next step: {progressNextStepText}</p>
            <p>Trial count selected: {lifecycleTrialCountText}</p>
            <p>Trial stage: {lifecycleTrialStageText}</p>
            <p>Trial position: {lifecycleTrialPositionText}</p>
            <p>Trial history: current-session only; no durable backend receipt is claimed.</p>
            <p>Authority: {lifecycleAuthorityStatement}</p>
            <p className="mt-2">Task boundary state: {taskBoundaryStateText}</p>
            <p>Task: {receiptValue(activeTaskId || taskPacket.title, "not created yet")}</p>
            <p>Target scope: {receiptTargetScopeText}</p>
            <p>Allowed files: {receiptAllowedFilesText}</p>
            <p>Preview: {previewStatus === "idle" ? "not run yet" : previewStatus}</p>
            <p>Approval: {approvedAt ? "approved locally" : "not approved"}</p>
            <p>
              Approval evidence:{" "}
              {approvedAt ? `local approval recorded at ${approvedAt}` : "not recorded"}
            </p>
            <p>Apply state: {receiptApplyStateText}</p>
            <p>
              Apply evidence:{" "}
              {appliedAt ? `execute-approved returned success at ${appliedAt}` : "not recorded"}
            </p>
            <p>Repeat apply lock: {receiptRepeatApplyLockText}</p>
            <p>Verify state: {receiptVerifyStateText}</p>
            <p>
              Verify evidence:{" "}
              {verifiedAt
                ? `docs-only verification recorded at ${verifiedAt}`
                : verificationStatus === "failed"
                  ? "verification failed"
                  : "not recorded"}
            </p>
            <p>
              Changed files: {receiptChangedFilesText}
            </p>
            <p>Unexpected files: {receiptUnexpectedFilesText}</p>
            <p>Diff check result: {receiptDiffCheckText}</p>
            <p>Typecheck result: {receiptTypecheckText}</p>
            <p>Lint result: {receiptLintText}</p>
            <p>Focused test result: {receiptFocusedTestText}</p>
            <p>
              Commands run: {receiptCommandsRunText}
            </p>
            <p>
              Pass/fail: {receiptPassFailText}
            </p>
            <p>Blocked reason: {receiptBlockedReasonText}</p>
            <p>Closeout blockers: {closeoutBlockersText}</p>
            <p>{receiptCommitPushText}</p>
            <p>Rollback hint: {activeChat?.rollbackHint ?? "keep the task bounded; use git diff before any apply."}</p>
            <p>Trial step: {receiptTrialStep}</p>
            <p className="mt-2 text-zinc-300">Safe next action: {progressNextStepText}</p>
            {receiptCopyStatus ? <p className="mt-2">{receiptCopyStatus}</p> : null}
          </div>
            </div>
          </details>
          ) : null}
        </aside>
      </div>
      <div
        aria-label="Mobile command composer"
        className="relative z-[var(--shell-z-composer,30)] border-t border-cyan-300/15 bg-[#10131b]/96 px-3 pb-[max(0.5rem,var(--shell-safe-area-bottom,0px))] pt-2 shadow-2xl shadow-black/50 backdrop-blur-xl xl:hidden"
        role="region"
      >
        <div className="mx-auto max-w-4xl rounded-lg border border-cyan-300/15 bg-[#151823]/98 p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.035)]">
          <div className="flex flex-wrap gap-2 px-1 pb-1.5">
            <button
              className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs text-zinc-300 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              type="button"
            >
              <Plus aria-hidden="true" size={14} />
              Context
            </button>
            <button
              aria-label="Mobile coding mode"
              aria-pressed={codingModeActive}
              className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs text-zinc-300 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              onClick={toggleCodingMode}
              onPointerUp={(event) => runDirectButtonAction(event, toggleCodingMode)}
              onTouchEnd={(event) => runDirectButtonAction(event, toggleCodingMode)}
              type="button"
            >
              <Sparkles aria-hidden="true" size={14} />
              Coding mode
            </button>
            <button
              aria-label="Mobile load prompt"
              className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              onClick={loadSelectedTrial}
              onPointerUp={(event) => runDirectButtonAction(event, loadSelectedTrial)}
              onTouchEnd={(event) => runDirectButtonAction(event, loadSelectedTrial)}
              type="button"
            >
              Load prompt
            </button>
            <button
              aria-label="Mobile preview selected"
              className="inline-flex min-h-8 items-center gap-1.5 rounded-md bg-cyan-200 px-2.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-100 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              disabled={!canRunSelectedTrialPreview}
              onClick={runSelectedTrialPreviewFromButton}
              onPointerUp={(event) => runDirectButtonAction(event, runSelectedTrialPreviewFromButton)}
              onTouchEnd={(event) => runDirectButtonAction(event, runSelectedTrialPreviewFromButton)}
              type="button"
            >
              Preview selected
            </button>
            <button
              aria-label="Mobile run 10 previews"
              className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40"
              disabled={!canRunAllTrialPreviews}
              onClick={() => void runTenTrialPreviews()}
              onPointerUp={(event) => {
                if (!canRunAllTrialPreviews) return;
                runDirectButtonAction(event, () => {
                  void runTenTrialPreviews();
                });
              }}
              onTouchEnd={(event) => {
                if (!canRunAllTrialPreviews) return;
                runDirectButtonAction(event, () => {
                  void runTenTrialPreviews();
                });
              }}
              type="button"
            >
              {trialBatchStatus === "running" ? "Running..." : "Run 10"}
            </button>
            <button
              aria-label="Mobile run 25 previews"
              className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40"
              disabled={!canRunAllTrialPreviews}
              onClick={() => void runTwentyFiveTrialPreviews()}
              onPointerUp={(event) => {
                if (!canRunAllTrialPreviews) return;
                runDirectButtonAction(event, () => {
                  void runTwentyFiveTrialPreviews();
                });
              }}
              onTouchEnd={(event) => {
                if (!canRunAllTrialPreviews) return;
                runDirectButtonAction(event, () => {
                  void runTwentyFiveTrialPreviews();
                });
              }}
              type="button"
            >
              {trialBatchStatus === "running" ? "Running..." : "Run 25"}
            </button>
            <button
              aria-label="Mobile run 100 previews"
              className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40"
              disabled={!canRunAllTrialPreviews}
              onClick={() => void runHundredTrialPreviews()}
              onPointerUp={(event) => {
                if (!canRunAllTrialPreviews) return;
                runDirectButtonAction(event, () => {
                  void runHundredTrialPreviews();
                });
              }}
              onTouchEnd={(event) => {
                if (!canRunAllTrialPreviews) return;
                runDirectButtonAction(event, () => {
                  void runHundredTrialPreviews();
                });
              }}
              type="button"
            >
              {trialBatchStatus === "running" ? "Running..." : "Run 100"}
            </button>
            <button
              aria-label="Mobile run all safe previews"
              className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              disabled={!canRunAllTrialPreviews}
              onClick={() => void runAllTrialPreviews()}
              onPointerUp={(event) => {
                if (!canRunAllTrialPreviews) return;
                runDirectButtonAction(event, () => {
                  void runAllTrialPreviews();
                });
              }}
              onTouchEnd={(event) => {
                if (!canRunAllTrialPreviews) return;
                runDirectButtonAction(event, () => {
                  void runAllTrialPreviews();
                });
              }}
              type="button"
            >
              {trialBatchStatus === "running" ? "Running..." : "Run all"}
            </button>
            <button
              aria-label="Mobile copy prompt"
              className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              onClick={copyTrialPrompt}
              onPointerUp={(event) => {
                runDirectButtonAction(event, () => {
                  void copyTrialPrompt();
                });
              }}
              onTouchEnd={(event) => {
                runDirectButtonAction(event, () => {
                  void copyTrialPrompt();
                });
              }}
              type="button"
            >
              <Copy aria-hidden="true" size={13} />
              Copy prompt
            </button>
          </div>
          <details className="mb-2 rounded-md border border-cyan-300/20 bg-black/25 p-2 text-xs leading-5 text-zinc-400">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-2 text-zinc-100">
              <span className="font-semibold">Audit</span>
              <span className="text-zinc-500">
                {sessionLogs.length > 0 ? `${sessionLogs.length} logged` : "copy page evidence"}
              </span>
            </summary>
            <div className="mt-2 grid gap-2">
              <div className="flex flex-wrap gap-2">
                <button
                  aria-label="Mobile copy Codex fix packet"
                  className="inline-flex min-h-9 flex-1 items-center justify-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                  onClick={() => void copyCodexFixPacket()}
                  onPointerUp={(event) => {
                    runDirectButtonAction(event, () => {
                      void copyCodexFixPacket();
                    });
                  }}
                  onTouchEnd={(event) => {
                    runDirectButtonAction(event, () => {
                      void copyCodexFixPacket();
                    });
                  }}
                  type="button"
                >
                  <Copy aria-hidden="true" size={13} />
                  Copy fix packet
                </button>
                <button
                  aria-label="Mobile copy audit logs"
                  className="inline-flex min-h-9 flex-1 items-center justify-center gap-1.5 rounded-md bg-cyan-200 px-2.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                  onClick={() => void copySessionLogs()}
                  onPointerUp={(event) => {
                    runDirectButtonAction(event, () => {
                      void copySessionLogs();
                    });
                  }}
                  onTouchEnd={(event) => {
                    runDirectButtonAction(event, () => {
                      void copySessionLogs();
                    });
                  }}
                  type="button"
                >
                  <Copy aria-hidden="true" size={13} />
                  Copy audit
                </button>
                <button
                  aria-label="Mobile record reviewed audit"
                  className="inline-flex min-h-9 items-center justify-center rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                  disabled={!canRecordAuditLog}
                  onClick={recordCurrentAuditLog}
                  onPointerUp={(event) => {
                    if (!canRecordAuditLog) return;
                    runDirectButtonAction(event, recordCurrentAuditLog);
                  }}
                  onTouchEnd={(event) => {
                    if (!canRecordAuditLog) return;
                    runDirectButtonAction(event, recordCurrentAuditLog);
                  }}
                  type="button"
                >
                  Record
                </button>
                <button
                  aria-label="Mobile reset audit logs"
                  className="inline-flex min-h-9 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                  disabled={sessionLogs.length === 0}
                  onClick={() => setSessionLogs([])}
                  onPointerUp={(event) => {
                    if (sessionLogs.length === 0) return;
                    runDirectButtonAction(event, () => setSessionLogs([]));
                  }}
                  onTouchEnd={(event) => {
                    if (sessionLogs.length === 0) return;
                    runDirectButtonAction(event, () => setSessionLogs([]));
                  }}
                  type="button"
                >
                  Reset
                </button>
              </div>
              <p className="rounded-md border border-white/10 bg-black/20 p-2 text-zinc-400">
                {sessionLogs[0]
                  ? `${sessionLogs[0].title} [${sessionLogs[0].status}]`
                  : previewStatus !== "idle" && previewStatus !== "loading"
                    ? "Current page evidence is ready to copy."
                    : "No audit entry yet."}
              </p>
            </div>
          </details>
          {codingModeActive && previewStatus === "ready" && activeProposedDiff ? (
            <div
              aria-label="Mobile preview evidence"
              className="mb-2 max-h-48 overflow-auto rounded-md border border-emerald-300/25 bg-black/25 p-2 text-xs leading-5 text-zinc-300"
              role="region"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold text-zinc-100">Preview evidence</p>
                <button
                  aria-label="Mobile copy diff"
                  className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-emerald-300/30 hover:text-emerald-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40"
                  onClick={copyPreviewDiff}
                  onPointerUp={(event) => {
                    runDirectButtonAction(event, () => {
                      void copyPreviewDiff();
                    });
                  }}
                  onTouchEnd={(event) => {
                    runDirectButtonAction(event, () => {
                      void copyPreviewDiff();
                    });
                  }}
                  type="button"
                >
                  <Copy aria-hidden="true" size={13} />
                  Copy diff
                </button>
              </div>
              <p className="mt-2 text-zinc-400">
                Changed files:{" "}
                {activeChangedFiles.length > 0
                  ? activeChangedFiles.join(", ")
                  : activePreviewTarget || "not reported"}
              </p>
              <pre className="mt-2 max-h-32 overflow-auto rounded-md border border-white/10 bg-black/35 p-2 text-[11px] leading-5 text-zinc-200">
                <code>{activeProposedDiff}</code>
              </pre>
              {previewDiffCopyStatus ? (
                <p className="mt-2 text-zinc-400">{previewDiffCopyStatus}</p>
              ) : null}
            </div>
          ) : previewAlreadySatisfied ? (
            <div
              aria-label="Mobile no diff preview"
              className="mb-2 rounded-md border border-emerald-300/30 bg-emerald-300/10 p-2 text-xs leading-5 text-emerald-100"
              role="region"
            >
              <p className="font-semibold">No diff preview</p>
              <p className="mt-1">
                Target already contains the requested change. No files changed and no diff is
                available for this no-op preview.
              </p>
            </div>
          ) : (
            <div
              aria-label="Mobile trial task helper"
              className="mb-2 max-h-40 overflow-auto rounded-md border border-white/10 bg-black/20 p-2 text-xs leading-5 text-zinc-400"
              onKeyDown={handleTrialSwitcherKeyDown}
              role="region"
              tabIndex={0}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-semibold text-zinc-100">Proxy Trial Prompts</p>
                  <p className="mt-1 text-zinc-500">
                    Preview only. Human review required. No apply, commit, or push from this widget.
                  </p>
                </div>
              </div>
              <p className="mt-2 rounded-md border border-cyan-300/20 bg-cyan-300/10 p-2 text-cyan-50">
                Selected {selectedTrial.id}: {selectedTrial.title}. Target: {selectedTrial.targetFile}. Expected:{" "}
                {selectedTrial.expectedResult}.
              </p>
              <div className="mt-2 grid grid-cols-[auto_minmax(0,1fr)_auto] gap-2">
                <button
                  aria-label="Mobile previous proxy trial"
                  className="inline-flex min-h-9 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] px-2 text-zinc-200"
                  onClick={() => switchSelectedTrial(-1)}
                  onPointerUp={(event) => runDirectButtonAction(event, () => switchSelectedTrial(-1))}
                  onTouchEnd={(event) => runDirectButtonAction(event, () => switchSelectedTrial(-1))}
                  type="button"
                >
                  <ChevronLeft aria-hidden="true" size={15} />
                </button>
                <label className="sr-only" htmlFor="proxy-trial-quick-select-mobile">Switch proxy trial</label>
                <select
                  aria-label="Mobile switch proxy trial"
                  className="min-h-9 w-full rounded-md border border-white/10 bg-black/30 px-2 text-sm text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                  id="proxy-trial-quick-select-mobile"
                  onChange={(event) => setSelectedTrialId(event.target.value)}
                  value={selectedTrial.id}
                >
                  {PROXY_TRIAL_PROMPTS.map((trial) => (
                    <option key={trial.id} value={trial.id}>
                      {trial.id} - {trial.title}
                    </option>
                  ))}
                </select>
                <button
                  aria-label="Mobile next proxy trial"
                  className="inline-flex min-h-9 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] px-2 text-zinc-200"
                  onClick={() => switchSelectedTrial(1)}
                  onPointerUp={(event) => runDirectButtonAction(event, () => switchSelectedTrial(1))}
                  onTouchEnd={(event) => runDirectButtonAction(event, () => switchSelectedTrial(1))}
                  type="button"
                >
                  <ChevronRight aria-hidden="true" size={15} />
                </button>
              </div>
              <p className="mt-2 rounded-md border border-cyan-300/20 bg-cyan-300/10 p-2 text-cyan-50">
                {currentTrialStep}
              </p>
              <div className="mt-2 hidden flex-wrap items-center justify-between gap-2">
                <p className="font-semibold text-zinc-100">Trial controls</p>
                <div className="flex flex-wrap gap-2">
                  <button
                    className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                    onClick={loadSelectedTrial}
                    onPointerUp={(event) => runDirectButtonAction(event, loadSelectedTrial)}
                    onTouchEnd={(event) => runDirectButtonAction(event, loadSelectedTrial)}
                    type="button"
                  >
                    Load prompt
                  </button>
                  <button
                    className="inline-flex min-h-8 items-center gap-1.5 rounded-md bg-cyan-200 px-2.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-100 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                    disabled={!canRunSelectedTrialPreview}
                    onClick={runSelectedTrialPreviewFromButton}
                    onPointerUp={(event) => runDirectButtonAction(event, runSelectedTrialPreviewFromButton)}
                    onTouchEnd={(event) => runDirectButtonAction(event, runSelectedTrialPreviewFromButton)}
                    type="button"
                  >
                    Preview selected
                  </button>
                  <button
                    className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                    disabled={!canRunAllTrialPreviews}
                    onClick={() => void runAllTrialPreviews()}
                    onPointerUp={(event) => {
                      if (!canRunAllTrialPreviews) return;
                      runDirectButtonAction(event, () => {
                        void runAllTrialPreviews();
                      });
                    }}
                    onTouchEnd={(event) => {
                      if (!canRunAllTrialPreviews) return;
                      runDirectButtonAction(event, () => {
                        void runAllTrialPreviews();
                      });
                    }}
                    type="button"
                  >
                    {trialBatchStatus === "running" ? "Running..." : "Run all"}
                  </button>
                  <button
                    className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                    onClick={copyTrialPrompt}
                    onPointerUp={(event) => {
                      runDirectButtonAction(event, () => {
                        void copyTrialPrompt();
                      });
                    }}
                    onTouchEnd={(event) => {
                      runDirectButtonAction(event, () => {
                        void copyTrialPrompt();
                      });
                    }}
                    type="button"
                  >
                    <Copy aria-hidden="true" size={13} />
                    Copy prompt
                  </button>
                  <button
                    className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                    disabled={!canClearActiveTask}
                    onClick={clearActiveTask}
                    onPointerUp={(event) => {
                      if (!canClearActiveTask) return;
                      runDirectButtonAction(event, clearActiveTask);
                    }}
                    onTouchEnd={(event) => {
                      if (!canClearActiveTask) return;
                      runDirectButtonAction(event, clearActiveTask);
                    }}
                    type="button"
                  >
                    Clear trial
                  </button>
                </div>
              </div>
              <p className="mt-1 rounded-md border border-white/10 bg-black/25 p-2 text-zinc-200">
                {selectedTrial.taskPrompt}
              </p>
              {trialPromptCopyStatus ? (
                <p className="mt-2 text-zinc-400">{trialPromptCopyStatus}</p>
              ) : null}
              <p className="mt-2 text-zinc-500">
                Hotkey: Alt+P. Blocked safely still matters, but does not prove productive coding.
              </p>
            </div>
          )}
          <label className="sr-only" htmlFor="coding-command-composer-mobile">
            Mobile coding command composer
          </label>
          <textarea
            aria-describedby="mobile-coding-task-state"
            className="min-h-16 w-full resize-none rounded-md border border-white/10 bg-black/25 px-3 py-2.5 text-base leading-6 text-zinc-100 placeholder:text-zinc-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
            id="coding-command-composer-mobile"
            onChange={(event) => updateActiveDraftText(event.target.value)}
            placeholder="Ask, plan, or draft a coding task."
            value={activeDraftText}
          />
          <div className="mt-2 grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
            <button
              aria-label="Mobile submit task"
              className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              disabled={!activeDraftText.trim()}
              onClick={submitActiveTask}
              onPointerUp={(event) => {
                if (!activeDraftText.trim()) return;
                runDirectButtonAction(event, submitActiveTask);
              }}
              onTouchEnd={(event) => {
                if (!activeDraftText.trim()) return;
                runDirectButtonAction(event, submitActiveTask);
              }}
              type="button"
            >
              <Send aria-hidden="true" size={15} />
              Submit task
            </button>
            <button
              aria-label="Mobile preview safely"
              className="inline-flex min-h-10 items-center justify-center rounded-md bg-cyan-200 px-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-100 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              disabled={!canRequestPreview || previewStatus === "loading"}
              onClick={() => void requestSafePreview()}
              onPointerUp={(event) => {
                if (!canRequestPreview || previewStatus === "loading") return;
                runDirectButtonAction(event, () => {
                  void requestSafePreview();
                });
              }}
              onTouchEnd={(event) => {
                if (!canRequestPreview || previewStatus === "loading") return;
                runDirectButtonAction(event, () => {
                  void requestSafePreview();
                });
              }}
              type="button"
            >
              {previewStatus === "loading" ? "Previewing..." : "Preview safely"}
            </button>
            <button
              aria-label="Mobile clear task"
              className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.04] px-3 text-sm font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 disabled:cursor-not-allowed disabled:opacity-45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              disabled={!canClearActiveTask}
              onClick={clearActiveTask}
              onPointerUp={(event) => {
                if (!canClearActiveTask) return;
                runDirectButtonAction(event, clearActiveTask);
              }}
              onTouchEnd={(event) => {
                if (!canClearActiveTask) return;
                runDirectButtonAction(event, clearActiveTask);
              }}
              type="button"
            >
              <X aria-hidden="true" size={15} />
              Clear
            </button>
          </div>
          <p
            aria-live="polite"
            className="mt-2 rounded-md border border-white/10 bg-black/20 px-2 py-1.5 text-xs leading-5 text-zinc-400"
            id="mobile-coding-task-state"
          >
            Mobile task state: {visibleTaskStateLabel}. Preview: {gateReasons.preview}
          </p>
          {codingModeActive ? (
            <p className="mt-2 text-xs text-zinc-500">
              Enter adds a line break. Use Submit task to stage the packet.
            </p>
          ) : null}
        </div>
      </div>
    </main>
  );
}
