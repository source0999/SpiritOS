"use client";

import { useEffect, useMemo, useRef, useState, type PointerEvent, type TouchEvent } from "react";
import {
  Bot,
  ChevronDown,
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
} from "lucide-react";

import { createThread } from "@/lib/chat-persistence";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import {
  describeCodingProviderIntent,
  getCodingProviderStatuses,
  type CodingProviderId,
} from "@/lib/coding/model-provider-status";
import { derivePlainEnglishScopeDraft } from "@/lib/coding/plain-english-scope";
import { deriveCodingTimelineEvents } from "@/lib/coding/timeline-events";
import { collectPathsFromUnifiedDiff } from "@/lib/coding/unified-diff-paths";
import "@/styles/dashboard-demo-v4.css";

type ShellChat = {
  id: string;
  title: string;
  meta: string;
  emptyState: string;
  providerId: CodingProviderId;
  codingMode: boolean;
  draftText: string;
  appliedAt: string | null;
  approvedAt: string | null;
  applyMessage: string;
  allowedFiles: string[];
  blockedFields: string[];
  changedFiles: string[];
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

const initialShellChats: ShellChat[] = [
  {
    id: "draft",
    title: "New coding chat",
    meta: "Ready",
    emptyState: "No coding task drafted",
    providerId: "local",
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

const defaultWorkspace = {
  id: "spiritos",
  label: "SpiritOS",
  path: "/home/source/SpiritOS",
  status: "Default repo workspace; writes still require preview, approval, and apply gates",
  authority: "Selected workspace; no commit, push, branch, or worktree action is available here",
};

const futureWindowsWorkspace = {
  id: "windows-projects",
  label: "C:\\Projects",
  path: "C:\\Projects",
  status: "Bridge-gated future project source; read-only/proposal-only until explicitly approved",
  authority: "Unavailable from this selector; external workspace actions stay proposal-only",
};

const safetySteps = ["Draft", "Preview", "Approval", "Apply", "Verify"];
const previewStepTimeoutMs = 30_000;
const taskStoryStorageKey = "spiritos:coding-command-center:task-story";
const trialPrompt =
  "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence explaining that verification receipts should include changed files, commands run, and pass/fail results.";
const trialExpectedResult =
  "Expected result: Preview shows one docs-only diff for docs/proxy-test-runner-plan.md. Approve unlocks only after preview evidence. Apply unlocks only after approval. Verify unlocks only after apply.";
const trialInstructions = [
  "1. Click Coding mode if it is not active.",
  "2. Paste the task below into the composer.",
  "3. Click Submit task. Enter only adds a new line.",
  "4. Confirm the active task shows SpiritOS, Local LLM, target file, allowed files, and Draft.",
  "5. Click Preview safely and wait for Preview evidence.",
  "6. Review the diff, then click Approve preview only if the changed file is correct.",
  "7. Click Apply approved diff only for this safe docs-only trial.",
  "8. Click Verify docs-only change after apply.",
];

function canUseIndexedDbPersistence() {
  return typeof window !== "undefined" && "indexedDB" in window;
}

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
  if (!canUseLocalStoryPersistence() || !hasTaskStoryActivity(chats)) {
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
      throw new Error(`${stepLabel} timed out after 30 seconds. No files changed.`);
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

function messageFromPayload(payload: unknown, status: number): string {
  const record = asRecord(payload);
  const detail = asRecord(record.detail);
  const reasonCode = stringValue(record.reason_code) ?? stringValue(detail.reason_code);
  if (reasonCode === "coder_packet_missing_context") {
    return "Preview blocked: Source Proxy needs more codebase context before it can produce a safe diff. No files changed.";
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

export default function CodingCommandCenterShell() {
  const [chats, setChats] = useState<ShellChat[]>(initialShellChats);
  const [activeChatId, setActiveChatId] = useState(initialShellChats[0].id);
  const [persistenceStatus, setPersistenceStatus] = useState("Local session only");
  const [previewDiffCopyStatus, setPreviewDiffCopyStatus] = useState("");
  const [receiptCopyStatus, setReceiptCopyStatus] = useState("");
  const [trialPromptCopyStatus, setTrialPromptCopyStatus] = useState("");
  const directButtonActionAtRef = useRef(0);
  const restoredTaskStoryRef = useRef(false);
  const providerStatuses = useMemo(() => getCodingProviderStatuses(), []);
  const localProvider = providerStatuses.find((provider) => provider.id === "local");
  const cloudProvider = providerStatuses.find((provider) => provider.id === "cloud");
  const contextChips = [
    { label: defaultWorkspace.label, tone: "repo" },
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
  ];

  const activeChat = useMemo(
    () => chats.find((chat) => chat.id === activeChatId) ?? chats[0],
    [activeChatId, chats],
  );
  const activeChatTitle = activeChat?.title ?? "New coding chat";
  const activeChatMeta = activeChat?.meta ?? "Ready";
  const activeChatEmptyState = activeChat?.emptyState ?? "No coding task drafted";
  const activeProviderId = activeChat?.providerId ?? "local";
  const codingModeActive = activeChat?.codingMode === true;
  const activeDraftText = activeChat?.draftText ?? "";
  const taskPacket = useMemo(() => deriveTaskPacket(activeDraftText), [activeDraftText]);
  const activeProposedDiff = activeChat?.proposedDiff ?? "";
  const activePreviewTarget = activeChat?.previewTarget ?? "";
  const activeTaskId = activeChat?.taskId ?? "";
  const activeTaskSubmitted = activeChat?.taskSubmitted === true;
  const activeBlockedFields = taskPacket.blockedFields;
  const activeChangedFiles = activeChat?.changedFiles ?? [];
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
  const providerIntent = describeCodingProviderIntent(activeProviderId, providerStatuses);
  const reviewOnlyPreview = previewStatus === "ready" && Boolean(activeProposedDiff) && !activeTaskId;
  const canRequestPreview =
    codingModeActive &&
    activeDraftText.trim().length > 0 &&
    taskPacket.blockedFields.length === 0;
  const changedFilesAreAllowed =
    activeChangedFiles.length > 0 &&
    activeChangedFiles.every((file) => taskPacket.allowedFiles.includes(file));
  const canApprovePreview =
    previewStatus === "ready" &&
    Boolean(activeProposedDiff) &&
    Boolean(activePreviewTarget) &&
    changedFilesAreAllowed &&
    !approvedAt;
  const canApplyApprovedDiff =
    Boolean(approvedAt) &&
    Boolean(activeProposedDiff) &&
    Boolean(activePreviewTarget) &&
    Boolean(activeTaskId) &&
    changedFilesAreAllowed &&
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
      ? `Preview blocked: missing ${taskPacket.blockedFields.join(", ")}.`
      : previewStatus === "blocked" || previewStatus === "error"
        ? previewMessage
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
        ? changedFilesAreAllowed
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
  const receiptText = [
    "Verification receipt",
    receiptReadinessText,
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
    `Safe next action: ${safeNextAction}`,
  ].join("\n");

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
    stageTrialPrompt();
    if (await writeClipboardText(trialPrompt)) {
      setTrialPromptCopyStatus("Trial task inserted, submitted, and copied. Tap Preview safely.");
    } else {
      setTrialPromptCopyStatus("Copy unavailable on this device, so the task was inserted and submitted. Tap Preview safely.");
    }
  }

  async function copyReceipt() {
    if (await writeClipboardText(receiptText)) {
      setReceiptCopyStatus("Receipt copied.");
    } else {
      setReceiptCopyStatus("Copy failed. Select the receipt text manually.");
    }
  }

  useEffect(() => {
    const storedTaskStory = readStoredTaskStory();
    if (storedTaskStory) {
      restoredTaskStoryRef.current = true;
      setChats(storedTaskStory.chats);
      setActiveChatId(storedTaskStory.activeChatId);
      setPersistenceStatus("Task story restored locally for refresh/reconnect review");
      return;
    }
    if (canUseIndexedDbPersistence()) {
      setPersistenceStatus("Persistence ready");
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

  function updateActiveChatProvider(providerId: CodingProviderId) {
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

  function toggleCodingMode() {
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId ? { ...chat, codingMode: !chat.codingMode } : chat,
      ),
    );
  }

  function submitActiveTask() {
    const packet = deriveTaskPacket(activeDraftText);
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

  function stageTrialPrompt() {
    const packet = deriveTaskPacket(trialPrompt);
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
              draftText: trialPrompt,
              previewMessage:
                packet.blockedFields.length > 0
                  ? `Task submitted locally. Preview blocked: missing ${packet.blockedFields.join(
                      ", ",
                    )}.`
                  : "Task inserted and submitted locally. Preview is ready to request; no files changed.",
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
    if (!canApprovePreview) {
      return;
    }
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChatId
          ? {
              ...chat,
              approvedAt: new Date().toISOString(),
              previewMessage: "Preview approved locally. No files changed yet.",
            }
          : chat,
      ),
    );
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

  async function requestSafePreview() {
    const taskText = activeDraftText.trim();
    if (!taskText) {
      updateActivePreviewState("blocked", "Draft a coding task before preview.");
      return;
    }
    if (taskPacket.blockedFields.length > 0) {
      updateActivePreviewState(
        "blocked",
        `Preview blocked: missing ${taskPacket.blockedFields.join(", ")}.`,
        {
          allowedFiles: taskPacket.allowedFiles,
          blockedFields: taskPacket.blockedFields,
          previewTarget: taskPacket.targetFile,
        },
      );
      return;
    }
    if (!activeTaskSubmitted) {
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
              `Target file: ${taskPacket.targetFile}`,
              `Allowed files: ${taskPacket.allowedFiles.join(", ")}`,
            ],
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
        "Creating preview task",
      );
      const taskPayload = await readJson(taskResponse);
      if (!taskResponse.ok) {
        updateActivePreviewState("error", messageFromPayload(taskPayload, taskResponse.status));
        return;
      }
      const previewTaskId = taskIdFromPayload(taskPayload);
      if (!previewTaskId) {
        updateActivePreviewState("error", "Preview task create did not return a task id.");
        return;
      }

      updateActivePreviewState("loading", "Requesting bounded diff proposal. No files changed.");
      const promptResponse = await fetchWithTimeout(
        "/v1/decisions/prompt-packet",
        {
          body: JSON.stringify({
            active_task_id: previewTaskId,
            allowed_files: taskPacket.allowedFiles,
            current_agent_role: "coder",
            needs_codebase_context: true,
            prefer_free: activeProviderId === "local",
            target_files: [taskPacket.targetFile],
            targeted_files: [taskPacket.targetFile],
            task: taskText,
            wants_implementation: true,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
        "Requesting bounded diff proposal",
      );
      const promptPayload = await readJson(promptResponse);
      if (!promptResponse.ok) {
        updateActivePreviewState("error", messageFromPayload(promptPayload, promptResponse.status));
        return;
      }

      const proposedDiff = diffFromPayload(promptPayload);
      if (!proposedDiff) {
        if (alreadySatisfiedFromPayload(promptPayload)) {
          updateActivePreviewState(
            "blocked",
            messageFromPayload(promptPayload, promptResponse.status),
            {
              allowedFiles: taskPacket.allowedFiles,
              blockedFields: [],
              changedFiles: [],
              previewTarget: taskPacket.targetFile,
              taskId: previewTaskId,
            },
          );
          return;
        }
        updateActivePreviewState(
          "blocked",
          messageFromPayload(promptPayload, promptResponse.status) || "Preview blocked: no diff returned.",
        );
        return;
      }
      const previewTarget = targetFromPayloadOrDiff(promptPayload, proposedDiff) || taskPacket.targetFile;
      const taskId = taskIdFromPayload(promptPayload) || previewTaskId;

      updateActivePreviewState("loading", "Checking diff safety gates. No files changed.");
      const previewResponse = await fetchWithTimeout(
        "/v1/verification/diff-preview",
        {
          body: JSON.stringify({
            route_type: activeProviderId === "local" ? "local-intent" : "cloud-intent",
            active_task_id: taskId,
            task_spec: {
              allowed_files: taskPacket.allowedFiles,
              forbidden_files: [],
              risk_tier: "low",
              schema_version: 1,
              source: "coding_command_center_ui",
              target: taskPacket.targetFile,
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
        updateActivePreviewState("error", messageFromPayload(previewPayload, previewResponse.status));
        return;
      }
      const status = stringValue(asRecord(previewPayload).status);
      if (status === "blocked") {
        updateActivePreviewState("blocked", messageFromPayload(previewPayload, previewResponse.status));
        return;
      }
      updateActivePreviewState("ready", "Preview ready. No files changed yet.", {
        allowedFiles: taskPacket.allowedFiles,
        blockedFields: [],
        changedFiles: collectPathsFromUnifiedDiff(proposedDiff),
        previewTarget,
        proposedDiff,
        taskId,
      });
    } catch (error) {
      updateActivePreviewState(
        "error",
        error instanceof Error ? error.message : "Preview request failed.",
      );
    }
  }

  async function handleStartNewChat() {
    const nextIndex = chats.filter((chat) => chat.title.startsWith("New chat")).length + 1;
    const chat: ShellChat = {
      id: `local-chat-${Date.now()}-${nextIndex}`,
      title: `New chat ${nextIndex}`,
      meta: "Empty",
      emptyState: `Empty chat ${nextIndex}, ready for a prompt`,
      providerId: "local",
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

    if (!canUseIndexedDbPersistence()) {
      setPersistenceStatus("Local session only");
      return;
    }

    const persisted = await createThread({ title: chat.title });
    if (!persisted) {
      setPersistenceStatus("Local session only");
      return;
    }

    setPersistenceStatus("Saved locally");
    setChats((current) =>
      current.map((item) =>
        item.id === chat.id
          ? {
              ...item,
              id: persisted.id,
              persisted: true,
            }
          : item,
      ),
    );
    setActiveChatId(persisted.id);
  }

  return (
    <main className="dashboard-demo-v4-route-shell dashboard-demo-v4-route-shell-coding relative min-h-dvh overflow-hidden bg-[#090a0f] pb-[calc(9.5rem+env(safe-area-inset-bottom))] text-zinc-100 xl:pb-0">
      <DashboardDemoV4FloatingNav desktopVariant="full-height" showMobile={false} />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(34,211,238,0.12),transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.68),rgba(9,10,15,0.96)_46%,#090a0f)]"
      />
      <div className="dashboard-demo-v4-route-main relative mx-auto flex min-h-dvh w-full max-w-[1680px] flex-col gap-3 px-3 py-3 sm:px-4 xl:grid xl:grid-cols-[280px_minmax(0,1fr)_320px] xl:gap-4 xl:p-4">
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
              className="flex h-9 w-9 items-center justify-center rounded-md border border-white/10 bg-white/[0.055] text-zinc-200 transition hover:border-cyan-300/35 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              onClick={handleStartNewChat}
              type="button"
            >
              <MessageSquarePlus aria-hidden="true" size={17} />
            </button>
          </div>

          <div className="space-y-4 p-3">
            <button
              aria-label="Selected workspace: SpiritOS"
              className="flex min-h-11 w-full items-center justify-between gap-3 rounded-md border border-cyan-300/20 bg-cyan-300/[0.065] px-3 text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] transition hover:border-cyan-300/35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              type="button"
            >
              <span className="flex min-w-0 items-center gap-2">
                <FolderGit2 aria-hidden="true" className="shrink-0 text-cyan-100" size={17} />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">{defaultWorkspace.label}</span>
                  <span className="block truncate text-xs text-zinc-500">{defaultWorkspace.path}</span>
                  <span className="block truncate text-xs text-cyan-100/70">
                    {defaultWorkspace.authority}
                  </span>
                </span>
              </span>
              <ChevronDown aria-hidden="true" className="shrink-0 text-zinc-500" size={16} />
            </button>

            <button
              aria-disabled="true"
              aria-label="Future workspace option: C:\\Projects"
              className="mt-2 flex min-h-11 w-full cursor-not-allowed items-center justify-between gap-3 rounded-md border border-dashed border-white/10 bg-white/[0.025] px-3 text-left text-zinc-400"
              disabled
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
                read-only
              </span>
            </button>

            <button
              aria-disabled="true"
              aria-label="Start new project placeholder"
              className="mt-2 flex min-h-11 w-full cursor-not-allowed items-center justify-between gap-3 rounded-md border border-dashed border-amber-200/15 bg-amber-200/[0.035] px-3 text-left text-amber-100/70"
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

        <section className="flex min-h-[58dvh] min-w-0 flex-col rounded-lg border border-white/10 bg-[#0f1118]/92 shadow-2xl shadow-black/25 backdrop-blur-xl xl:min-h-[calc(100dvh-2rem)]">
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
                  {defaultWorkspace.status} · {persistenceStatus}
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
              </div>
            </div>
          </header>

          <div className="flex flex-1 flex-col justify-between gap-6 px-3 py-4 sm:px-4 xl:px-6 xl:py-6">
            <div className="mx-auto grid w-full max-w-4xl gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-white/10 bg-white/[0.04] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <ShieldCheck aria-hidden="true" className="text-emerald-200" size={17} />
                  Safety
                </div>
                <p className="mt-2 text-xs leading-5 text-zinc-500">Draft locked</p>
              </div>
              <div className="rounded-lg border border-white/10 bg-white/[0.04] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
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
                <p className="mt-3 text-xs leading-5 text-zinc-500">{providerIntent}</p>
              </div>
              <div className="rounded-lg border border-white/10 bg-white/[0.04] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <GitBranch aria-hidden="true" className="text-amber-100" size={17} />
                  Workspace
                </div>
                <p className="mt-2 text-xs leading-5 text-zinc-500">
                  {defaultWorkspace.label} is selected by default
                </p>
                <p className="mt-2 text-xs leading-5 text-zinc-500">
                  {futureWindowsWorkspace.label} is read-only/proposal-only; no external workspace
                  action is available from this selector.
                </p>
              </div>
            </div>

            <div className="mx-auto flex w-full max-w-4xl flex-1 items-center justify-center">
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
                        {defaultWorkspace.label}
                      </p>
                      <p>
                        <span className="font-medium text-zinc-100">Provider:</span>{" "}
                        {providerStatuses.find((provider) => provider.id === activeProviderId)?.label ??
                          "Local LLM"}
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
                    <p>{previewMessage}</p>
                    {previewStatus === "blocked" || previewStatus === "error" ? (
                      <p className="mt-2 text-xs leading-5 opacity-90">
                        Immediate action: {safeNextAction}
                      </p>
                    ) : null}
                  </div>
                ) : null}
                {codingModeActive && previewStatus === "ready" && activeProposedDiff ? (
                  <div className="mt-3 rounded-md border border-emerald-300/25 bg-black/25 p-3 text-sm text-zinc-300">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                      <p className="font-medium text-zinc-100">Preview evidence</p>
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
                      {canApprovePreview ? (
                        <button
                          className="inline-flex min-h-10 items-center justify-center rounded-md border border-emerald-300/30 bg-emerald-300/10 px-3 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-300/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40"
                          onClick={approvePreview}
                          type="button"
                        >
                          {activeTaskId ? "Approve preview" : "Mark preview reviewed"}
                        </button>
                      ) : null}
                      {approvedAt && activeTaskId ? (
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

            <div className="mx-auto hidden w-full max-w-4xl rounded-lg border border-cyan-300/15 bg-[#151823]/96 p-2 shadow-xl shadow-black/25 xl:block">
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
              <div className="mb-2 rounded-md border border-white/10 bg-black/20 p-3 text-xs leading-5 text-zinc-400">
                <p className="font-semibold text-zinc-100">Trial prompt and steps</p>
                <p className="mt-2 rounded-md border border-cyan-300/20 bg-cyan-300/10 p-2 text-cyan-50">
                  {currentTrialStep}
                </p>
                <div className="mt-2 space-y-1">
                  {trialInstructions.map((instruction) => (
                    <p key={instruction}>{instruction}</p>
                  ))}
                </div>
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold text-zinc-100">Copy-paste task</p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                      onClick={stageTrialPrompt}
                      onPointerUp={(event) => {
                        event.preventDefault();
                        stageTrialPrompt();
                      }}
                      type="button"
                    >
                      Use task
                    </button>
                    <button
                      className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-zinc-200 transition hover:border-cyan-300/30 hover:text-cyan-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                      onClick={copyTrialPrompt}
                      type="button"
                    >
                      <Copy aria-hidden="true" size={13} />
                      Copy task
                    </button>
                  </div>
                </div>
                <p className="mt-1 rounded-md border border-white/10 bg-black/25 p-2 text-zinc-200">
                  {trialPrompt}
                </p>
                {trialPromptCopyStatus ? (
                  <p className="mt-2 text-zinc-400">{trialPromptCopyStatus}</p>
                ) : null}
                <p className="mt-2 text-zinc-500">{trialExpectedResult}</p>
              </div>
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
              <div className="mt-2 grid gap-2 sm:grid-cols-2">
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
                  onClick={requestSafePreview}
                  onPointerUp={(event) => {
                    if (!canRequestPreview || previewStatus === "loading") return;
                    event.preventDefault();
                    void requestSafePreview();
                  }}
                  type="button"
                >
                  {previewStatus === "loading" ? "Previewing..." : "Preview safely"}
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
          className="mb-2 rounded-lg border border-white/10 bg-[#10131b]/90 p-3 shadow-2xl shadow-black/30 backdrop-blur-xl xl:mb-0 xl:min-h-[calc(100dvh-2rem)]"
          role="complementary"
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                Task state
              </p>
              <h2 className="mt-1 text-base font-semibold">{taskStateLabel}</h2>
            </div>
            <span className="rounded-md border border-emerald-300/35 bg-emerald-300/10 px-2.5 py-1 text-xs font-medium text-emerald-100">
              Safe
            </span>
          </div>

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
            aria-label="Coding task timeline and evidence stream"
            className="mt-5 rounded-lg border border-white/10 bg-black/20 p-3 text-xs leading-5 text-zinc-400"
            role="region"
          >
            <p className="font-semibold uppercase tracking-[0.18em] text-zinc-500">
              Task timeline
            </p>
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

          <div className="mt-5 rounded-lg border border-white/10 bg-black/20 p-3 text-xs leading-5 text-zinc-400">
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
            </div>
            <p className="mt-2 text-zinc-300">{receiptReadinessText}</p>
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
            <p className="mt-2 text-zinc-300">Safe next action: {safeNextAction}</p>
            {receiptCopyStatus ? <p className="mt-2">{receiptCopyStatus}</p> : null}
          </div>
        </aside>
      </div>
      <div
        aria-label="Mobile command composer"
        className="fixed inset-x-0 bottom-0 z-30 border-t border-cyan-300/15 bg-[#10131b]/96 px-3 py-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))] shadow-2xl shadow-black/50 backdrop-blur-xl xl:hidden"
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
              aria-label="Mobile use task"
              className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
              onClick={stageTrialPrompt}
              onPointerUp={(event) => runDirectButtonAction(event, stageTrialPrompt)}
              onTouchEnd={(event) => runDirectButtonAction(event, stageTrialPrompt)}
              type="button"
            >
              Use task
            </button>
            <button
              aria-label="Mobile copy task"
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
              Copy task
            </button>
          </div>
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
              role="region"
            >
              <p className="font-semibold text-zinc-100">Trial prompt and steps</p>
              <p className="mt-2 rounded-md border border-cyan-300/20 bg-cyan-300/10 p-2 text-cyan-50">
                {currentTrialStep}
              </p>
              <div className="mt-1 space-y-1">
                {trialInstructions.map((instruction) => (
                  <p key={instruction}>{instruction}</p>
                ))}
              </div>
              <div className="mt-2 flex flex-wrap items-center justify-between gap-2 sm:hidden">
                <p className="font-semibold text-zinc-100">Copy-paste task</p>
                <div className="flex flex-wrap gap-2">
                  <button
                    className="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-cyan-300/30 bg-cyan-300/10 px-2.5 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/40"
                    onClick={stageTrialPrompt}
                    onPointerUp={(event) => runDirectButtonAction(event, stageTrialPrompt)}
                    onTouchEnd={(event) => runDirectButtonAction(event, stageTrialPrompt)}
                    type="button"
                  >
                    Use task
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
                    Copy task
                  </button>
                </div>
              </div>
              <p className="mt-1 rounded-md border border-white/10 bg-black/25 p-2 text-zinc-200">
                {trialPrompt}
              </p>
              {trialPromptCopyStatus ? (
                <p className="mt-2 text-zinc-400">{trialPromptCopyStatus}</p>
              ) : null}
              <p className="mt-2 text-zinc-500">{trialExpectedResult}</p>
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
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
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
              onClick={requestSafePreview}
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
          </div>
          <p
            aria-live="polite"
            className="mt-2 rounded-md border border-white/10 bg-black/20 px-2 py-1.5 text-xs leading-5 text-zinc-400"
            id="mobile-coding-task-state"
          >
            Mobile task state: {taskStateLabel}. Preview: {gateReasons.preview}
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
