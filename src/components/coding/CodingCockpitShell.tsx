"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { FileText, ShieldCheck } from "lucide-react";

import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import "@/styles/dashboard-demo-v4.css";

const statusItems = [
  { label: "Proxy", value: "Ready for safe preview" },
  { label: "Route", value: "Select during preview" },
  { label: "Workspace", value: "SpiritOS" },
];

const statusStripItems = ["Draft", "Preview", "Approval", "Apply", "Verify"];
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
  blocker: string | null;
  changedFiles: string[];
  diff: string;
  error: string | null;
  isApplying: boolean;
  isLoading: boolean;
  requirementSummary: string;
  reviewerSummary: string;
  status: "idle" | "ready" | "approved" | "applied" | "blocked" | "error" | "satisfied";
  targetMatch: boolean;
  taskId: string;
  taskSpecAllowed: boolean;
  verifierSummary: string;
};

type TimelineItem = {
  label: string;
  status: string;
  detail: string;
  active: boolean;
};

function idlePreviewState(): PreviewState {
  return {
    approvalAvailable: false,
    approvedAt: null,
    appliedAt: null,
    applySummary: "",
    blocker: null,
    changedFiles: [],
    diff: "",
    error: null,
    isApplying: false,
    isLoading: false,
    requirementSummary: "Waiting for preview.",
    reviewerSummary: "Waiting for preview.",
    status: "idle",
    targetMatch: false,
    taskId: "",
    taskSpecAllowed: false,
    verifierSummary: "Waiting for preview.",
  };
}

function splitFiles(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => normalizeRepoPath(item))
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
    target.includes("secret") ||
    target.includes("certificate") ||
    target.includes("credentials") ||
    target.startsWith("/") ||
    target.includes("..")
  );
}

function statusStepIndex(previewState: PreviewState): number {
  if (previewState.status === "applied") {
    return 3;
  }
  if (previewState.status === "approved") {
    return 2;
  }
  if (previewState.approvalAvailable) {
    return 2;
  }
  if (previewState.status === "satisfied") {
    return 1;
  }
  if (previewState.status !== "idle" || previewState.isLoading) {
    return 1;
  }
  return 0;
}

function nextSafeActionText({
  draftReady,
  previewState,
}: {
  draftReady: boolean;
  previewState: PreviewState;
}) {
  if (!draftReady) {
    return "Write the task, open Advanced options for target and allowed files, then preview safely. Preview does not write files.";
  }
  if (previewState.status === "applied") {
    return "Applied, verification required. Commit and push are not available here.";
  }
  if (previewState.status === "approved") {
    return "Apply the approved diff through Source Proxy, or reject and restart. Approval alone has not changed files.";
  }
  if (previewState.status === "ready" && previewState.approvalAvailable) {
    return "Review the approval gates, then approve. Approval is required before apply.";
  }
  if (previewState.status === "satisfied") {
    return "No diff is required. Change the task to request a new unique line, or use /proxy-backend for a bounded proposal.";
  }
  return "Resolve any preview blocker, then retry safe preview. No files have been changed.";
}

function readableTaskState(previewState: PreviewState, draftReady: boolean): string {
  if (previewState.status === "applied") return "Applied, verification required";
  if (previewState.status === "approved") return "Approved, not applied";
  if (previewState.status === "ready" && previewState.approvalAvailable) return "Needs approval";
  if (previewState.status === "ready") return "Preview ready";
  if (previewState.status === "blocked" || previewState.status === "error") return "Blocked";
  if (draftReady || previewState.isLoading) return "Preview ready";
  return "Draft";
}

function buildTimelineItems(previewState: PreviewState, draftReady: boolean): TimelineItem[] {
  const hasPreview = previewState.status !== "idle" || previewState.isLoading || draftReady;
  const reviewed = previewState.status !== "idle" && !previewState.isLoading;
  const approvalActive = previewState.approvalAvailable || previewState.status === "approved";
  const applied = previewState.status === "applied";
  return [
    {
      label: "Architect",
      status: draftReady ? "Task scoped" : "Draft",
      detail: draftReady
        ? "Task, target, allowed files, and checks are staged for preview."
        : "Waiting for a scoped task.",
      active: draftReady,
    },
    {
      label: "Coder",
      status: previewState.isLoading ? "Previewing" : hasPreview ? "Preview ready" : "Waiting",
      detail: hasPreview ? "Proposal evidence is captured without applying files." : "No proposal yet.",
      active: hasPreview,
    },
    {
      label: "Reviewer",
      status: reviewed ? "Evidence available" : "Waiting",
      detail: reviewed ? previewState.reviewerSummary : "Reviewer evidence appears after preview.",
      active: reviewed,
    },
    {
      label: "Verifier",
      status: reviewed ? "Evidence available" : "Waiting",
      detail: reviewed ? previewState.verifierSummary : "Verifier evidence appears after preview.",
      active: reviewed,
    },
    {
      label: "Approval Gate",
      status:
        previewState.status === "approved"
          ? "Approved, not applied"
          : previewState.approvalAvailable
            ? "Needs approval"
            : "Locked",
      detail: previewState.approvalAvailable
        ? "Human approval is required before apply."
        : "Approval remains locked until preview gates pass.",
      active: approvalActive,
    },
    {
      label: "Apply Result",
      status: applied ? "Applied, verification required" : "Not applied",
      detail: applied
        ? previewState.applySummary || "Approved diff was applied. Verification is required."
        : "No files have been applied from this cockpit state.",
      active: applied,
    },
  ];
}

export default function CodingCockpitShell() {
  const [task, setTask] = useState("");
  const [targetFile, setTargetFile] = useState("");
  const [allowedFiles, setAllowedFiles] = useState("");
  const [expectedChecks, setExpectedChecks] = useState("git diff --check");
  const [routeModel, setRouteModel] = useState("source-proxy-default");
  const [draftReady, setDraftReady] = useState(false);
  const [previewState, setPreviewState] = useState<PreviewState>(() => idlePreviewState());

  const allowedFileList = useMemo(() => splitFiles(allowedFiles), [allowedFiles]);
  const validationMessages = useMemo(() => {
    const messages: string[] = [];
    const trimmedTask = task.trim();
    const trimmedTarget = targetFile.trim();
    if (!trimmedTask) {
      messages.push("Task required");
    }
    if (!trimmedTarget) {
      messages.push("Target required");
    }
    if (allowedFileList.length === 0) {
      messages.push("Allowed files required");
    }
    if (trimmedTarget && isProtectedTarget(trimmedTarget)) {
      messages.push("Protected target blocked in UI");
    }
    return messages;
  }, [allowedFileList.length, targetFile, task]);
  const canPreview = validationMessages.length === 0;
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
  const canApplyApprovedDiff = applyControlsVisible && !previewState.isApplying;
  const showWorkspaceEmpty =
    previewState.status === "idle" && !previewState.isLoading && !task.trim();
  const activeStepIndex = statusStepIndex(previewState);
  const currentTaskTitle = task.trim() || "No active task";
  const currentTaskTarget = normalizeRepoPath(targetFile) || "No target selected";
  const currentTaskState = readableTaskState(previewState, draftReady);
  const timelineItems = buildTimelineItems(previewState, draftReady);
  const nextSafeAction = nextSafeActionText({
    draftReady,
    previewState,
  });
  const railTaskItems = [
    {
      label: "Active task",
      value: task.trim() ? currentTaskState : "Ready to draft",
      active: true,
    },
    {
      label: "Waiting approval",
      value: previewState.approvalAvailable ? "1 task" : "None",
      active: previewState.approvalAvailable,
    },
    {
      label: "Blocked",
      value:
        previewState.status === "blocked" || previewState.status === "error" ? "1 task" : "None",
      active: previewState.status === "blocked" || previewState.status === "error",
    },
    {
      label: "Verified/done",
      value: previewState.status === "applied" ? "Verify next" : "None",
      active: previewState.status === "applied",
    },
    {
      label: "Recent tasks",
      value: draftReady ? "Current draft" : "Empty",
      active: draftReady,
    },
  ];
  const railScopeItems = [
    { label: "Target", value: currentTaskTarget },
    {
      label: "Allowed",
      value:
        allowedFileList.length > 0
          ? `${allowedFileList.length} file${allowedFileList.length === 1 ? "" : "s"}`
          : "None selected",
    },
    { label: "Checks", value: expectedChecks.trim() || "None listed" },
  ];
  const workspaceEmptyItems = [
    {
      label: "No active task",
      value: "Draft a task here or pick one from the rail.",
    },
    {
      label: "Select or create a task",
      value: "Use the composer as the active workspace.",
    },
    {
      label: "Preview safely before writes",
      value: "Preview produces review evidence before approval is available.",
    },
    {
      label: "Review changes before approval",
      value: "Diffs and gates stay separate from apply.",
    },
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

  function resetPreviewForEdit() {
    setDraftReady(false);
    setPreviewState(idlePreviewState());
  }

  async function handleDraftPreview() {
    if (!canPreview) {
      setDraftReady(false);
      return;
    }
    setDraftReady(true);
    setPreviewState({
      approvalAvailable: false,
      approvedAt: null,
      appliedAt: null,
      applySummary: "",
      blocker: null,
      changedFiles: [],
      diff: "",
      error: null,
      isApplying: false,
      isLoading: true,
      requirementSummary: "Waiting for preview.",
      reviewerSummary: "Waiting for preview.",
      status: "idle",
      targetMatch: false,
      taskId: "",
      taskSpecAllowed: false,
      verifierSummary: "Waiting for preview.",
    });
    try {
      const trimmedTarget = normalizeRepoPath(targetFile);
      const taskSpec = {
        allowed_files: allowedFileList,
        forbidden_files: [],
        risk_tier: "low",
        schema_version: 1,
        source: "coding_cockpit_ui",
        target: trimmedTarget,
        task_type: "modify_existing_file",
        verification: splitFiles(expectedChecks),
      };
      const promptTask = taskTextForPromptPacket(task, trimmedTarget);
      const proposalResponse = await fetch("/v1/decisions/prompt-packet", {
        body: JSON.stringify({
          needs_codebase_context: true,
          prefer_free: true,
          target_files: allowedFileList,
          targeted_files: allowedFileList,
          task: promptTask,
          wants_implementation: true,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
      });
      const proposalPayload = await readJson(proposalResponse);
      if (!proposalResponse.ok) {
        throw new Error(messageFromPayload(proposalPayload, proposalResponse.status));
      }

      const proposedDiff = diffFromPayload(proposalPayload);
      if (!proposedDiff) {
        if (isCoderAlreadySatisfied(proposalPayload)) {
          const alreadySatisfiedBlocker = "coder_no_changes_needed_unverified";
          setPreviewState({
            approvalAvailable: false,
            approvedAt: null,
            appliedAt: null,
            applySummary: "",
            blocker: alreadySatisfiedBlocker,
            changedFiles: [],
            diff: "",
            error: null,
            isApplying: false,
            isLoading: false,
            requirementSummary:
              "Source Proxy reported already satisfied, but /coding cannot verify the target content without a diff. No approval or apply is available.",
            reviewerSummary: "No reviewer evidence available for an empty diff.",
            status: "blocked",
            targetMatch: false,
            taskId: taskIdFromPayload(proposalPayload),
            taskSpecAllowed: false,
            verifierSummary: "No verifier evidence available for an empty diff.",
          });
          return;
        }
        const noDiffBlocker = noDiffBlockerFromPayload(proposalPayload);
        setPreviewState({
          approvalAvailable: false,
          approvedAt: null,
          appliedAt: null,
          applySummary: "",
          blocker: noDiffBlocker,
          changedFiles: [],
          diff: "",
          error: null,
          isApplying: false,
          isLoading: false,
          requirementSummary: coderSummaryFromPayload(
            proposalPayload,
            "No diff returned for requirement review.",
          ),
          reviewerSummary: "No reviewer evidence available.",
          status: "blocked",
          targetMatch: false,
          taskId: "",
          taskSpecAllowed: false,
          verifierSummary: "No verifier evidence available.",
        });
        return;
      }

      const diffResponse = await fetch("/v1/verification/diff-preview", {
        body: JSON.stringify({
          route_type: routeModel,
          task_spec: taskSpec,
          task_text: task.trim(),
          unified_diff: proposedDiff,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
      });
      const diffPayload = await readJson(diffResponse);
      if (!diffResponse.ok) {
        throw new Error(messageFromPayload(diffPayload, diffResponse.status));
      }
      const changedFiles = changedFilesFromPayload(diffPayload);
      const blocked = statusFromPayload(diffPayload) === "blocked";
      const gate = approvalGateFromPreview(diffPayload, trimmedTarget, allowedFileList);
      setPreviewState({
        approvalAvailable: !blocked && gate.approvalAvailable,
        approvedAt: null,
        appliedAt: null,
        applySummary: "",
        blocker: blocked ? blockerFromPayload(diffPayload) : null,
        changedFiles,
        diff: proposedDiff,
        error: null,
        isApplying: false,
        isLoading: false,
        requirementSummary: gate.requirementSummary,
        reviewerSummary: gate.reviewerSummary,
        status: blocked ? "blocked" : "ready",
        targetMatch: gate.targetMatch,
        taskId: taskIdFromPayload(diffPayload) || taskIdFromPayload(proposalPayload),
        taskSpecAllowed: gate.taskSpecAllowed,
        verifierSummary: gate.verifierSummary,
      });
    } catch (error) {
      setPreviewState({
        approvalAvailable: false,
        approvedAt: null,
        appliedAt: null,
        applySummary: "",
        blocker: null,
        changedFiles: [],
        diff: "",
        error: error instanceof Error ? error.message : "Preview failed.",
        isApplying: false,
        isLoading: false,
        requirementSummary: "Preview failed before requirement review.",
        reviewerSummary: "Preview failed before reviewer evidence.",
        status: "error",
        targetMatch: false,
        taskId: "",
        taskSpecAllowed: false,
        verifierSummary: "Preview failed before verifier evidence.",
      });
    }
  }

  function handleRejectPreview() {
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
    setPreviewState((current) => ({
      ...current,
      error: null,
      isApplying: true,
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
          action: `Modify ${targetFile.trim()}`,
          approved: true,
          approved_diff: previewState.diff,
          target: targetFile.trim(),
          task_id: taskId,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
      });
      const applyPayload = await readJson(applyResponse);
      if (!applyResponse.ok) {
        throw new Error(messageFromPayload(applyPayload, applyResponse.status));
      }
      const appliedFiles = changedFilesFromPayload(applyPayload);
      setPreviewState((current) => ({
        ...current,
        appliedAt: new Date().toISOString(),
        applySummary: messageFromPayload(applyPayload, applyResponse.status),
        changedFiles: appliedFiles.length > 0 ? appliedFiles : current.changedFiles,
        error: null,
        isApplying: false,
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
            className={`${commandPanelClass} space-y-4 p-4 xl:sticky xl:top-6 xl:max-h-[calc(100dvh-3rem)] xl:overflow-auto`}
          >
            <div>
              <p className={commandLabelClass}>
                Workspace
              </p>
              <div className={`${commandInsetClass} mt-2 p-3`}>
                <div className={`text-sm font-semibold ${commandTextClass}`}>SpiritOS</div>
                <div className={`mt-1 text-xs ${commandMutedClass}`}>Source Proxy command center</div>
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
                <div className="rounded-md border border-[var(--ddv4-surface-border-soft)] px-2 py-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ddv4-fg-faint)]">
                  Local state only
                </div>
              </div>
            </div>
            <nav aria-label="Task queues" className="space-y-2">
              <p className={commandLabelClass}>
                Tasks
              </p>
              {railTaskItems.map((item) => (
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
          </aside>

          <div className="flex min-w-0 flex-col gap-5">
        <section aria-labelledby="current-state-heading" className={`${commandPanelClass} order-2 p-4 sm:p-5`}>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 id="current-state-heading" className="text-base font-semibold text-[var(--ddv4-fg)]">
                Task status
              </h2>
              <p className="mt-1 text-sm text-[var(--ddv4-fg-muted)]">
                {currentTaskState}. Keep moving through Draft, Preview, Approval, Apply, then
                Verify. Full diagnostics stay in `/proxy-backend`.
              </p>
            </div>
            <span className="inline-flex min-h-9 items-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-xs font-semibold text-[var(--ddv4-fg)]">
              {currentTaskState}
            </span>
          </div>
          <div aria-label="Coding status" className="mt-4 flex flex-wrap items-center gap-2">
            {statusStripItems.map((item, index) => (
              <div className="flex items-center gap-2" key={item}>
                <span
                  className={`inline-flex min-h-8 items-center rounded-full border px-2.5 text-[11px] font-semibold transition-colors ${
                    index <= activeStepIndex
                      ? "border-[var(--spirit-accent)] bg-[var(--ddv4-nav-active-bg)] text-[var(--ddv4-nav-active-fg)]"
                      : "border-[var(--ddv4-pill-border)] text-[var(--ddv4-fg-faint)]"
                  }`}
                >
                  {item}
                </span>
                {index < statusStripItems.length - 1 ? (
                  <span className="text-[var(--ddv4-fg-faint)]" aria-hidden="true">
                    -
                  </span>
                ) : null}
              </div>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 border-t border-[var(--ddv4-surface-border-soft)] pt-3 text-xs text-[var(--ddv4-fg-muted)]">
            {statusItems.map((item) => (
              <span className="inline-flex gap-2" key={item.label}>
                <span className="uppercase tracking-[0.14em] text-[var(--ddv4-fg-faint)]">{item.label}</span>
                <span className="text-[var(--ddv4-fg)]">{item.value}</span>
              </span>
            ))}
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
                  <p className={`text-sm ${commandMutedClass}`}>Preview safely before anything writes.</p>
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
                    className={`min-h-72 w-full resize-y rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-4 py-4 text-base leading-7 text-[var(--ddv4-fg)] placeholder:text-[var(--ddv4-fg-faint)] sm:text-base ${commandControlClass}`}
                    onChange={(event) => {
                      setTask(event.target.value);
                      resetPreviewForEdit();
                    }}
                    placeholder="Describe the coding task here."
                    value={task}
                  />
                </label>

                <details className={`${commandInsetClass} overflow-hidden`}>
                  <summary className={`min-h-12 cursor-pointer px-3 py-3 text-sm font-semibold ${commandTextClass} ${commandControlClass}`}>
                    Advanced options
                  </summary>
                  <div className="space-y-4 border-t border-[var(--ddv4-surface-border-soft)] p-3">
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

                    <div className="grid gap-4 sm:grid-cols-2">
                      <label className="block">
                        <span className={`mb-2 block text-sm font-medium ${commandTextClass}`}>
                          Expected checks
                        </span>
                        <textarea
                          className={`min-h-24 w-full resize-y rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-3 py-3 text-base text-[var(--ddv4-fg)] placeholder:text-[var(--ddv4-fg-faint)] sm:text-sm ${commandControlClass}`}
                          onChange={(event) => {
                            setExpectedChecks(event.target.value);
                            resetPreviewForEdit();
                          }}
                          placeholder="npm run typecheck"
                          value={expectedChecks}
                        />
                      </label>
                      <label className="block">
                        <span className={`mb-2 block text-sm font-medium ${commandTextClass}`}>
                          Route / model
                        </span>
                        <select
                          className={`min-h-12 w-full rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] px-3 text-base text-[var(--ddv4-fg)] sm:text-sm ${commandControlClass}`}
                          onChange={(event) => {
                            setRouteModel(event.target.value);
                            resetPreviewForEdit();
                          }}
                          value={routeModel}
                        >
                          <option value="source-proxy-default">Source Proxy default</option>
                          <option value="local-planning">Local planning only</option>
                          <option value="codex-proposal">Codex proposal route</option>
                        </select>
                      </label>
                    </div>
                  </div>
                </details>

                <div
                  aria-live="polite"
                  className={`rounded-md border px-3 py-3 text-sm ${
                    canPreview
                      ? "border-emerald-300/30 bg-emerald-300/10 text-emerald-100"
                      : "border-amber-300/30 bg-amber-300/10 text-amber-100"
                  }`}
                  role="status"
                >
                  {canPreview
                    ? "Ready to preview safely. No files will be changed during preview."
                    : validationMessages.join(", ")}
                </div>

                <button
                  className={`inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 shadow-sm transition-colors hover:bg-emerald-200 ${commandFocusClass} ${
                    canPreview ? "" : "opacity-60"
                  }`}
                  disabled={!canPreview || previewState.isLoading}
                  onClick={handleDraftPreview}
                  type="button"
                >
                  <ShieldCheck aria-hidden="true" size={18} />
                  {previewState.isLoading ? "Previewing..." : "Preview safely"}
                </button>
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
                    Draft
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
                    Open diagnostics in /proxy-backend
                  </Link>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>
                      Target
                    </dt>
                    <dd className={`mt-1 break-words ${commandTextClass}`}>{targetFile.trim()}</dd>
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
                      Allowed files
                    </dt>
                    <dd className={`mt-1 break-words ${commandTextClass}`}>
                      {allowedFileList.join(", ")}
                    </dd>
                  </div>
                  <div className={`${commandInsetClass} p-3`}>
                    <dt className={commandLabelClass}>
                      Preview status
                    </dt>
                    <dd className={`mt-1 break-words ${commandTextClass}`}>
                      {previewState.error ??
                        previewState.blocker ??
                        (previewState.isLoading ? "Previewing" : "Preview ready")}
                    </dd>
                  </div>
                </dl>

                {previewState.diff ? (
                  <pre className="mt-4 max-h-72 overflow-auto rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)] p-3 text-xs leading-5 text-[var(--ddv4-fg)]">
                    {previewState.diff}
                  </pre>
                ) : null}
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
                  </div>
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

                {previewState.error ? (
                  <div className="mt-4 rounded-md border border-red-300/40 bg-red-300/10 px-3 py-3 text-sm text-red-100">
                    {previewState.error}
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
                          ? "No apply step. Revise the task or use /proxy-backend for a bounded proposal with a fresh literal."
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
                      label="Verifier"
                      ok={previewState.verifierSummary.toLowerCase().includes("passed")}
                      value={previewState.verifierSummary}
                    />
                    <GateStatus
                      label="Reviewer"
                      ok={!previewState.reviewerSummary.toLowerCase().includes("blocked")}
                      value={previewState.reviewerSummary}
                    />
                    <GateStatus
                      label="Apply"
                      ok={previewState.status === "applied"}
                      value={
                        previewState.status === "applied"
                          ? "Approved diff was applied through Source Proxy."
                          : previewState.status === "approved"
                            ? "Ready to apply approved diff through Source Proxy."
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
            className={`${commandPanelClass} space-y-4 p-4 xl:sticky xl:top-6 xl:max-h-[calc(100dvh-3rem)] xl:overflow-auto`}
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
                  Preview status
                </dt>
                <dd className={`mt-1 break-words ${commandTextClass}`}>{reviewPaneStatus}</dd>
              </div>
              <div className={`${commandInsetClass} p-3`}>
                <dt className={commandLabelClass}>
                  Verifier
                </dt>
                <dd className={`mt-1 break-words ${commandTextClass}`}>{previewState.verifierSummary}</dd>
              </div>
              <div className={`${commandInsetClass} p-3`}>
                <dt className={commandLabelClass}>
                  Reviewer
                </dt>
                <dd className={`mt-1 break-words ${commandTextClass}`}>{previewState.reviewerSummary}</dd>
              </div>
              <div className="rounded-md border border-[var(--spirit-accent)] bg-[var(--ddv4-pill-bg)] p-3">
                <dt className={commandLabelClass}>
                  Next safe move
                </dt>
                <dd className={`mt-1 ${commandTextClass}`}>
                  {previewState.status === "idle" && !draftReady
                    ? "Preview becomes available after task, target, and allowed files are set."
                    : nextSafeAction}
                </dd>
              </div>
            </dl>

            <details className={`${commandInsetClass} overflow-hidden`}>
              <summary className={`min-h-12 cursor-pointer px-3 py-3 text-sm font-semibold ${commandTextClass} ${commandControlClass}`}>
                Evidence trail and logs
              </summary>
              <div className="space-y-3 border-t border-[var(--ddv4-surface-border-soft)] p-3">
                <ol className="space-y-2">
                  {timelineItems.map((item) => (
                    <li
                      className={`rounded-md border p-3 ${
                        item.active
                          ? "border-[var(--spirit-accent)] bg-[var(--ddv4-pill-bg)]"
                          : "border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-surface-fill)]"
                      }`}
                      key={item.label}
                    >
                      <div className={commandLabelClass}>{item.label}</div>
                      <div className={`mt-1 text-sm font-semibold ${commandTextClass}`}>
                        {item.status}
                      </div>
                      <p className={`mt-2 text-sm leading-6 ${commandMutedClass}`}>{item.detail}</p>
                    </li>
                  ))}
                </ol>
                <div className={`${commandInsetClass} p-3 text-sm`}>
                  <div className={`font-semibold ${commandTextClass}`}>Terminal/Test Evidence</div>
                  <p className={`mt-2 leading-6 ${commandMutedClass}`}>
                    {previewState.status === "idle"
                      ? `Expected checks: ${expectedChecks.trim() || "none listed"}. Evidence appears after preview and verification.`
                      : `${previewState.requirementSummary} ${previewState.verifierSummary}`}
                  </p>
                </div>
              </div>
            </details>

            <Link
              className={`inline-flex min-h-11 w-full items-center justify-center rounded-md border border-[var(--ddv4-pill-border)] px-3 text-sm font-medium text-[var(--ddv4-fg)] transition-colors hover:bg-[var(--ddv4-surface-fill)] ${commandFocusClass}`}
              href="/proxy-backend"
            >
              Backend diagnostics
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
            aria-label="Open mobile diagnostics in /proxy-backend"
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
                canPreview ? "" : "opacity-60"
              }`}
              disabled={!canPreview || previewState.isLoading}
              onClick={handleDraftPreview}
              type="button"
            >
              <ShieldCheck aria-hidden="true" size={18} />
              {previewState.isLoading ? "Previewing" : "Preview"}
            </button>
          )}
        </div>
      </div>
      </main>
      <DashboardDemoV4FloatingNav desktopVariant="full-height" />
    </div>
  );
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return {};
  }
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
  return (
    stringValue(record.blocked_reason) ??
    stringValue(record.blockedReason) ??
    stringValue(record.reason_code) ??
    stringValue(record.reasonCode) ??
    stringValue(record.message) ??
    messageFromPayload(payload, 200)
  );
}

function coderSummaryFromPayload(payload: unknown, fallback: string): string {
  const record = asRecord(payload);
  const reasonCode = stringValue(record.reason_code) ?? stringValue(record.reasonCode);
  if (stringValue(record.blocked_reason) ?? stringValue(record.blockedReason)) {
    return stringValue(record.blocked_reason) ?? stringValue(record.blockedReason) ?? fallback;
  }
  if (reasonCode === "coder_model_not_configured" || reasonCode === "local_model_unavailable") {
    return "Coder route unavailable. Check SOURCE_PROXY_CODER_MODEL_ALIAS and Ollama.";
  }
  if (reasonCode === "coder_sync_timeout") {
    return "Coder timed out before returning a diff. Narrow scope or raise the sync deadline.";
  }
  if (reasonCode === "coder_no_changes_needed") {
    return "Target already satisfies this task. No diff to approve or apply.";
  }
  return reasonCode ? `No diff returned (${reasonCode}).` : fallback;
}

function changedFilesFromPayload(payload: unknown): string[] {
  const changed = asRecord(payload).changed_files;
  if (!Array.isArray(changed)) {
    return [];
  }
  return changed
    .map((item) => {
      if (typeof item === "string") {
        return item;
      }
      return stringValue(asRecord(item).path) ?? "";
    })
    .filter(Boolean);
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
      ? "Reviewer blocked this preview."
      : reviewReport.passed === true || llmReviewReport.passed === true
        ? "Reviewer evidence passed."
        : "Reviewer evidence unavailable or advisory.",
    targetMatch,
    taskSpecAllowed,
    verifierSummary: gitApplyPassed
      ? "Verifier passed git apply check."
      : stringValue(record.git_apply_check_error) ?? "Verifier has not passed git apply check.",
  };
}
