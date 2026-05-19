"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ArrowRight,
  BrainCircuit,
  Code2,
  FileText,
  LayoutDashboard,
  MessageSquare,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

const statusItems = [
  { label: "Proxy", value: "Ready for safe preview", tone: "text-emerald-200" },
  { label: "Route", value: "Select during preview", tone: "text-sky-200" },
  { label: "Workspace", value: "SpiritOS", tone: "text-slate-100" },
];

const statusStripItems = ["Draft", "Preview", "Approval", "Apply", "Verify"];
const navItems = [
  { href: "/", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/chat", icon: MessageSquare, label: "Chat" },
  { href: "/coding", icon: Code2, label: "Source" },
  { href: "/intelligence", icon: BrainCircuit, label: "Scout" },
  { href: "/oracle", icon: Sparkles, label: "Oracle" },
];

type PreviewState = {
  appliedAt: string | null;
  approvalAvailable: boolean;
  approvedAt: string | null;
  blocker: string | null;
  changedFiles: string[];
  diff: string;
  error: string | null;
  isApplying: boolean;
  isLoading: boolean;
  isVerifying: boolean;
  requirementSummary: string;
  reviewerSummary: string;
  status: "idle" | "ready" | "blocked" | "error" | "applied" | "verified";
  targetMatch: boolean;
  taskSpecAllowed: boolean;
  taskId: string;
  verificationSummary: string;
  verifiedAt: string | null;
  verifierSummary: string;
};

function idlePreviewState(): PreviewState {
  return {
    appliedAt: null,
    approvalAvailable: false,
    approvedAt: null,
    blocker: null,
    changedFiles: [],
    diff: "",
    error: null,
    isApplying: false,
    isLoading: false,
    isVerifying: false,
    requirementSummary: "Waiting for preview.",
    reviewerSummary: "Waiting for preview.",
    status: "idle",
    targetMatch: false,
    taskId: "",
    taskSpecAllowed: false,
    verificationSummary: "Verification waits until after apply.",
    verifiedAt: null,
    verifierSummary: "Waiting for preview.",
  };
}

function splitFiles(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
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
  if (previewState.verifiedAt) {
    return 4;
  }
  if (previewState.appliedAt) {
    return 3;
  }
  if (previewState.approvedAt || previewState.approvalAvailable) {
    return 2;
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
  if (previewState.status === "verified") {
    return "Task is verified. Commit and push are not available here.";
  }
  if (previewState.status === "applied") {
    return "Run verification before considering this task done. Commit and push are not available here.";
  }
  if (previewState.approvedAt) {
    return "Apply the approved diff, or reject and restart. Approval is required before apply, and approval alone does not write files.";
  }
  if (previewState.status === "ready") {
    return "Review the preview, then approve or reject. Approval is required before apply.";
  }
  return "Resolve any preview blocker, then retry safe preview. No files have been changed.";
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
  const activeStepIndex = statusStepIndex(previewState);
  const nextSafeAction = nextSafeActionText({
    draftReady,
    previewState,
  });

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
      appliedAt: null,
      approvalAvailable: false,
      approvedAt: null,
      blocker: null,
      changedFiles: [],
      diff: "",
      error: null,
      isApplying: false,
      isLoading: true,
      isVerifying: false,
      requirementSummary: "Waiting for preview.",
      reviewerSummary: "Waiting for preview.",
      status: "idle",
      targetMatch: false,
      taskSpecAllowed: false,
      taskId: "",
      verificationSummary: "Verification waits until after apply.",
      verifiedAt: null,
      verifierSummary: "Waiting for preview.",
    });
    try {
      const taskSpec = {
        allowed_files: allowedFileList,
        forbidden_files: [],
        risk_tier: "low",
        schema_version: 1,
        source: "coding_cockpit_ui",
        target: targetFile.trim(),
        task_type: "modify_existing_file",
        verification: splitFiles(expectedChecks),
      };
      const proposalResponse = await fetch("/v1/coding/codex", {
        body: JSON.stringify({
          allowed_files: allowedFileList,
          expected_checks: splitFiles(expectedChecks),
          mode: "proposal",
          route_model: routeModel,
          target_file: targetFile.trim(),
          task: task.trim(),
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
        setPreviewState({
          appliedAt: null,
          approvalAvailable: false,
          approvedAt: null,
          blocker: messageFromPayload(proposalPayload, proposalResponse.status),
          changedFiles: [],
          diff: "",
          error: null,
          isApplying: false,
          isLoading: false,
          isVerifying: false,
          requirementSummary: "No diff returned for requirement review.",
          reviewerSummary: "No reviewer evidence available.",
          status: "blocked",
          targetMatch: false,
          taskSpecAllowed: false,
          taskId: taskIdFromPayload(proposalPayload),
          verificationSummary: "Verification waits until after apply.",
          verifiedAt: null,
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
      const gate = approvalGateFromPreview(diffPayload, targetFile.trim(), allowedFileList);
      setPreviewState({
        appliedAt: null,
        approvalAvailable: !blocked && gate.approvalAvailable,
        approvedAt: null,
        blocker: blocked ? blockerFromPayload(diffPayload) : null,
        changedFiles,
        diff: proposedDiff,
        error: null,
        isApplying: false,
        isLoading: false,
        isVerifying: false,
        requirementSummary: gate.requirementSummary,
        reviewerSummary: gate.reviewerSummary,
        status: blocked ? "blocked" : "ready",
        targetMatch: gate.targetMatch,
        taskSpecAllowed: gate.taskSpecAllowed,
        taskId: taskIdFromPayload(diffPayload) || taskIdFromPayload(proposalPayload),
        verificationSummary: "Verification waits until after apply.",
        verifiedAt: null,
        verifierSummary: gate.verifierSummary,
      });
    } catch (error) {
      setPreviewState({
        appliedAt: null,
        approvalAvailable: false,
        approvedAt: null,
        blocker: null,
        changedFiles: [],
        diff: "",
        error: error instanceof Error ? error.message : "Preview failed.",
        isApplying: false,
        isLoading: false,
        isVerifying: false,
        requirementSummary: "Preview failed before requirement review.",
        reviewerSummary: "Preview failed before reviewer evidence.",
        status: "error",
        targetMatch: false,
        taskSpecAllowed: false,
        taskId: "",
        verificationSummary: "Verification waits until after apply.",
        verifiedAt: null,
        verifierSummary: "Preview failed before verifier evidence.",
      });
    }
  }

  function handleRejectPreview() {
    setPreviewState((current) => ({
      ...current,
      approvalAvailable: false,
      approvedAt: null,
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
    }));
  }

  async function handleApplyApprovedDiff() {
    if (!previewState.approvedAt || !previewState.diff || previewState.status !== "ready") {
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
        const createResponse = await fetch("/v1/tasks/long-running", {
          body: JSON.stringify({ description: task.trim() || "Coding cockpit approved diff" }),
          headers: { "content-type": "application/json" },
          method: "POST",
        });
        const createPayload = await readJson(createResponse);
        if (!createResponse.ok) {
          throw new Error(messageFromPayload(createPayload, createResponse.status));
        }
        taskId = taskIdFromPayload(createPayload);
        if (!taskId) {
          throw new Error("Long-running task create did not return a task id.");
        }
      }

      const executeResponse = await fetch("/v1/actions/execute-approved", {
        body: JSON.stringify({
          action: task.trim(),
          approved: true,
          approved_diff: previewState.diff,
          target: targetFile.trim(),
          task_id: taskId,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
      });
      const executePayload = await readJson(executeResponse);
      if (!executeResponse.ok) {
        throw new Error(messageFromPayload(executePayload, executeResponse.status));
      }
      setPreviewState((current) => ({
        ...current,
        appliedAt: new Date().toISOString(),
        blocker: null,
        changedFiles: changedFilesFromPayload(executePayload).length
          ? changedFilesFromPayload(executePayload)
          : current.changedFiles,
        error: null,
        isApplying: false,
        status: "applied",
        taskId,
        verificationSummary: "Manual verification required before this task is done.",
        verifiedAt: null,
        verifierSummary: "Applied. Verification required.",
      }));
    } catch (error) {
      setPreviewState((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Apply failed.",
        isApplying: false,
      }));
    }
  }

  async function handleVerifyAppliedDiff() {
    if (!previewState.appliedAt || !previewState.taskId || previewState.verifiedAt) {
      return;
    }
    setPreviewState((current) => ({
      ...current,
      error: null,
      isVerifying: true,
    }));
    try {
      const verifyResponse = await fetch(
        `/v1/tasks/long-running/${encodeURIComponent(previewState.taskId)}/verify`,
        {
          body: JSON.stringify({
            confirm_backup_audit_present: true,
            confirm_changed_files_reviewed: true,
            confirm_expected_change_present: true,
            confirm_no_unintended_files: true,
            verification_note: "Docs-only change verified from the coding cockpit.",
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        },
      );
      const verifyPayload = await readJson(verifyResponse);
      if (!verifyResponse.ok) {
        throw new Error(messageFromPayload(verifyPayload, verifyResponse.status));
      }
      setPreviewState((current) => ({
        ...current,
        error: null,
        isVerifying: false,
        status: "verified",
        verificationSummary: verificationSummaryFromPayload(verifyPayload),
        verifiedAt: new Date().toISOString(),
      }));
    } catch (error) {
      setPreviewState((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Verification failed.",
        isVerifying: false,
      }));
    }
  }

  return (
    <main className="min-h-dvh overflow-x-hidden bg-slate-950 pb-28 text-slate-100 lg:pb-0">
      <div className="mx-auto flex min-h-dvh w-full max-w-6xl flex-col px-4 py-5 sm:px-6 lg:px-8">
        <nav
          aria-label="Spirit workspace navigation"
          className="mb-5 overflow-x-auto rounded-md border border-white/10 bg-white/[0.03] p-1"
        >
          <div className="flex min-w-max items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = item.href === "/coding";
              return (
                <Link
                  aria-current={active ? "page" : undefined}
                  className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-md px-3 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-emerald-300 ${
                    active
                      ? "bg-emerald-300 text-slate-950"
                      : "text-slate-300 hover:bg-white/10 hover:text-white"
                  }`}
                  href={item.href}
                  key={item.href}
                >
                  <Icon aria-hidden="true" size={17} />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>
        <header className="flex flex-col gap-4 border-b border-white/10 pb-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0 space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200">
              Source Proxy cockpit
            </p>
            <h1 className="text-3xl font-semibold tracking-normal text-white">Coding</h1>
            <p className="max-w-2xl text-sm leading-6 text-slate-300">
              Draft a scoped task, preview the diff safely, then approve and apply only when
              Source Proxy gates allow it.
            </p>
          </div>
          <Link
            className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-md border border-white/15 bg-white/5 px-4 text-sm font-medium text-slate-100 transition hover:border-emerald-300/50 hover:bg-emerald-300/10 focus:outline-none focus:ring-2 focus:ring-emerald-300 sm:w-auto"
            href="/proxy-backend"
          >
            Advanced diagnostics
            <ArrowRight aria-hidden="true" size={16} />
          </Link>
        </header>

        <section aria-label="Coding status" className="border-b border-white/10 py-4">
          <div className="flex flex-wrap items-center gap-2">
            {statusStripItems.map((item, index) => (
              <div className="flex items-center gap-2" key={item}>
                <span
                  className={`inline-flex min-h-9 items-center rounded-full border px-3 text-xs font-semibold ${
                    index <= activeStepIndex
                      ? "border-emerald-300 bg-emerald-300 text-slate-950"
                      : "border-white/15 text-slate-500"
                  }`}
                >
                  {item}
                </span>
                {index < statusStripItems.length - 1 ? (
                  <span className="text-slate-600" aria-hidden="true">
                    -
                  </span>
                ) : null}
              </div>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-400">
            {statusItems.map((item) => (
              <span className="inline-flex gap-2" key={item.label}>
                <span className="uppercase tracking-[0.14em] text-slate-600">{item.label}</span>
                <span className={item.tone}>{item.value}</span>
              </span>
            ))}
          </div>
        </section>

        <div className="grid flex-1 gap-5 py-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <section className="min-w-0 space-y-5" aria-labelledby="task-composer-heading">
            <div className="rounded-md border border-white/10 bg-slate-900/70 p-4 sm:p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-emerald-300/10 text-emerald-200">
                  <FileText aria-hidden="true" size={20} />
                </div>
                <div className="min-w-0">
                  <h2 id="task-composer-heading" className="text-lg font-semibold text-white">
                    Task Composer
                  </h2>
                  <p className="text-sm text-slate-400">Preview safely before anything writes.</p>
                </div>
              </div>

              <div className="space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-200">Task</span>
                  <textarea
                    className="min-h-56 w-full resize-y rounded-md border border-white/10 bg-slate-950/80 px-4 py-4 text-base leading-7 text-slate-200 placeholder:text-slate-600 sm:text-base"
                    onChange={(event) => {
                      setTask(event.target.value);
                      resetPreviewForEdit();
                    }}
                    placeholder="Describe the coding task here."
                    value={task}
                  />
                </label>

                <details className="rounded-md border border-white/10 bg-white/[0.02]">
                  <summary className="min-h-12 cursor-pointer px-3 py-3 text-sm font-semibold text-slate-100">
                    Advanced options
                  </summary>
                  <div className="space-y-4 border-t border-white/10 p-3">
                    <div className="grid gap-4 sm:grid-cols-2">
                      <label className="block">
                        <span className="mb-2 block text-sm font-medium text-slate-200">
                          Target file
                        </span>
                        <input
                          className="min-h-12 w-full rounded-md border border-white/10 bg-slate-950/80 px-3 text-base text-slate-200 placeholder:text-slate-600 sm:text-sm"
                          onChange={(event) => {
                            setTargetFile(event.target.value);
                            resetPreviewForEdit();
                          }}
                          placeholder="docs/example.md"
                          value={targetFile}
                        />
                      </label>
                      <label className="block">
                        <span className="mb-2 block text-sm font-medium text-slate-200">
                          Allowed files
                        </span>
                        <input
                          className="min-h-12 w-full rounded-md border border-white/10 bg-slate-950/80 px-3 text-base text-slate-200 placeholder:text-slate-600 sm:text-sm"
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
                        <span className="mb-2 block text-sm font-medium text-slate-200">
                          Expected checks
                        </span>
                        <textarea
                          className="min-h-24 w-full resize-y rounded-md border border-white/10 bg-slate-950/80 px-3 py-3 text-base text-slate-200 placeholder:text-slate-600 sm:text-sm"
                          onChange={(event) => {
                            setExpectedChecks(event.target.value);
                            resetPreviewForEdit();
                          }}
                          placeholder="npm run typecheck"
                          value={expectedChecks}
                        />
                      </label>
                      <label className="block">
                        <span className="mb-2 block text-sm font-medium text-slate-200">
                          Route / model
                        </span>
                        <select
                          className="min-h-12 w-full rounded-md border border-white/10 bg-slate-950/80 px-3 text-base text-slate-200 sm:text-sm"
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
                  className={`inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 sm:w-auto ${
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

            {previewState.status !== "idle" || previewState.isLoading ? (
              <section className="rounded-md border border-white/10 bg-slate-900/70 p-4 sm:p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-white">Diff Review</h2>
                    <p className="mt-1 text-sm text-slate-400">
                      {previewState.isLoading
                        ? "Requesting a safe preview. No files have been changed."
                        : previewState.status === "verified"
                          ? "Verified. No commit or push controls are available here."
                        : previewState.status === "applied"
                          ? "Applied. Verification is required."
                        : previewState.status === "ready"
                          ? "Preview ready. No files changed yet."
                          : "Preview blocked. No files changed."}
                    </p>
                  </div>
                  <Link
                    className="inline-flex min-h-11 items-center justify-center rounded-md border border-white/15 px-3 text-sm font-medium text-slate-200"
                    href="/proxy-backend"
                  >
                    Full diagnostics
                  </Link>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                  <div className="rounded-md border border-white/10 bg-white/[0.03] p-3">
                    <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                      Target
                    </dt>
                    <dd className="mt-1 break-words text-slate-100">{targetFile.trim()}</dd>
                  </div>
                  <div className="rounded-md border border-white/10 bg-white/[0.03] p-3">
                    <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                      Changed files
                    </dt>
                    <dd className="mt-1 break-words text-slate-100">
                      {previewState.changedFiles.length > 0
                        ? previewState.changedFiles.join(", ")
                        : "None reported"}
                    </dd>
                  </div>
                  <div className="rounded-md border border-white/10 bg-white/[0.03] p-3">
                    <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                      Allowed files
                    </dt>
                    <dd className="mt-1 break-words text-slate-100">
                      {allowedFileList.join(", ")}
                    </dd>
                  </div>
                  <div className="rounded-md border border-white/10 bg-white/[0.03] p-3">
                    <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                      Preview status
                    </dt>
                    <dd className="mt-1 break-words text-slate-100">
                      {previewState.error ??
                        previewState.blocker ??
                        (previewState.isLoading ? "Previewing" : "Preview ready")}
                    </dd>
                  </div>
                </dl>

                {previewState.diff ? (
                  <pre className="mt-4 max-h-72 overflow-auto rounded-md border border-white/10 bg-slate-950 p-3 text-xs leading-5 text-slate-200">
                    {previewState.diff}
                  </pre>
                ) : null}
              </section>
            ) : null}

            {previewState.status !== "idle" || previewState.isLoading ? (
              <section className="rounded-md border border-white/10 bg-slate-900/70 p-4 sm:p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-white">Approval State</h2>
                    <p className="mt-1 text-sm text-slate-400">
                      {previewState.appliedAt
                        ? previewState.verifiedAt
                          ? "Verified. This task is ready for closeout."
                          : "Applied. Verification is required before this task is done."
                        : previewState.approvedAt
                          ? "Approved. Files are still unchanged until you apply the approved diff."
                          : previewState.approvalAvailable
                            ? "Preview ready. Human approval is required before apply."
                            : "Approval unavailable until preview gates pass."}
                    </p>
                  </div>
                  <span
                    className={`inline-flex min-h-9 items-center rounded-md border px-3 text-xs font-semibold ${
                      previewState.approvalAvailable
                        ? "border-emerald-300/40 bg-emerald-300/10 text-emerald-100"
                        : "border-amber-300/40 bg-amber-300/10 text-amber-100"
                    }`}
                  >
                    {previewState.approvalAvailable ? "approval available" : "approval unavailable"}
                  </span>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
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
                </dl>

                {previewState.error ? (
                  <div className="mt-4 rounded-md border border-red-300/40 bg-red-300/10 px-3 py-3 text-sm text-red-100">
                    {previewState.error}
                  </div>
                ) : null}

                <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
                  {previewState.approvalAvailable && !previewState.approvedAt ? (
                    <>
                      <button
                        className="inline-flex min-h-12 items-center justify-center rounded-md border border-white/15 px-4 text-sm font-semibold text-slate-100"
                        onClick={handleRejectPreview}
                        type="button"
                      >
                        Reject
                      </button>
                      <button
                        className="inline-flex min-h-12 items-center justify-center rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950"
                        onClick={handleApprovePreview}
                        type="button"
                      >
                        Approve
                      </button>
                    </>
                  ) : null}
                  {previewState.approvedAt && !previewState.appliedAt ? (
                    <div className="w-full rounded-md border border-emerald-300/30 bg-emerald-300/10 p-3 sm:flex sm:items-center sm:justify-between sm:gap-4">
                      <div className="text-sm text-emerald-100">
                        Approved, not applied. No files have changed yet.
                      </div>
                      <button
                        className="mt-3 inline-flex min-h-12 w-full items-center justify-center rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 disabled:opacity-60 sm:mt-0 sm:w-auto"
                        disabled={previewState.isApplying}
                        onClick={handleApplyApprovedDiff}
                        type="button"
                      >
                        {previewState.isApplying ? "Applying..." : "Apply approved diff"}
                      </button>
                    </div>
                  ) : null}
                  {previewState.appliedAt ? (
                    <div className="w-full rounded-md border border-sky-300/30 bg-sky-300/10 p-3 text-sm text-sky-100">
                      {previewState.verifiedAt ? "Verified." : "Applied. Verification required."}
                    </div>
                  ) : null}
                </div>
              </section>
            ) : null}

            {previewState.appliedAt ? (
              <section className="rounded-md border border-white/10 bg-slate-900/70 p-4 sm:p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-white">Verification</h2>
                    <p className="mt-1 text-sm text-slate-400">
                      {previewState.verifiedAt
                        ? "Verification complete. Commit and push are still not available from this page."
                        : "Review the applied change and confirm the post-apply checks."}
                    </p>
                  </div>
                  <span
                    className={`inline-flex min-h-9 items-center rounded-md border px-3 text-xs font-semibold ${
                      previewState.verifiedAt
                        ? "border-emerald-300/40 bg-emerald-300/10 text-emerald-100"
                        : "border-sky-300/40 bg-sky-300/10 text-sky-100"
                    }`}
                  >
                    {previewState.verifiedAt ? "verified" : "verification required"}
                  </span>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                  <GateStatus
                    label="Changed files reviewed"
                    ok={Boolean(previewState.verifiedAt)}
                    value={
                      previewState.changedFiles.length > 0
                        ? previewState.changedFiles.join(", ")
                        : "No changed files reported."
                    }
                  />
                  <GateStatus
                    label="Expected change present"
                    ok={Boolean(previewState.verifiedAt)}
                    value={previewState.verificationSummary}
                  />
                  <GateStatus
                    label="No unintended files"
                    ok={Boolean(previewState.verifiedAt)}
                    value={
                      previewState.verifiedAt
                        ? "Confirmed during verification."
                        : "Confirm before marking verification complete."
                    }
                  />
                  <GateStatus
                    label="Rollback hint"
                    ok={Boolean(previewState.verifiedAt)}
                    value={`Use Source Proxy evidence or git diff review for ${targetFile.trim()}.`}
                  />
                </dl>

                {previewState.error ? (
                  <div className="mt-4 rounded-md border border-red-300/40 bg-red-300/10 px-3 py-3 text-sm text-red-100">
                    {previewState.error}
                  </div>
                ) : null}

                {!previewState.verifiedAt ? (
                  <button
                    className="mt-4 inline-flex min-h-12 w-full items-center justify-center rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 disabled:opacity-60 sm:w-auto"
                    disabled={previewState.isVerifying}
                    onClick={handleVerifyAppliedDiff}
                    type="button"
                  >
                    {previewState.isVerifying ? "Verifying..." : "Mark verification complete"}
                  </button>
                ) : null}
              </section>
            ) : null}

            {previewState.verifiedAt ? (
              <section className="rounded-md border border-emerald-300/30 bg-emerald-300/10 p-4 sm:p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-white">Task Receipt</h2>
                    <p className="mt-1 text-sm text-emerald-100">
                      Verified. Nothing has been committed or pushed from /coding.
                    </p>
                  </div>
                  <Link
                    className="inline-flex min-h-11 items-center justify-center rounded-md border border-emerald-200/40 px-3 text-sm font-medium text-emerald-50"
                    href="/proxy-backend"
                  >
                    Task evidence
                  </Link>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                  <ReceiptField
                    label="Last action"
                    value="Verification completed through Source Proxy."
                  />
                  <ReceiptField
                    label="Files changed"
                    value={
                      previewState.changedFiles.length > 0
                        ? previewState.changedFiles.join(", ")
                        : "No changed files reported."
                    }
                  />
                  <ReceiptField label="Checks passed" value={previewState.verificationSummary} />
                  <ReceiptField
                    label="Next safe action"
                    value="Review task evidence in /proxy-backend. Commit and push require separate approval outside this first /coding phase."
                  />
                  <ReceiptField
                    label="Rollback hint"
                    value={`Review Source Proxy evidence and git diff for ${targetFile.trim()} before any follow-up.`}
                  />
                  <ReceiptField
                    label="Task evidence"
                    value={previewState.taskId ? `Source Proxy task ${previewState.taskId}` : "/proxy-backend"}
                  />
                </dl>
              </section>
            ) : null}

          </section>

          <aside className="min-w-0" aria-label="Task actions">
            <section className="rounded-md border border-white/10 bg-slate-900/70 p-4">
              <h2 className="text-base font-semibold text-white">Next Safe Action</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">{nextSafeAction}</p>
            </section>
          </aside>
        </div>
      </div>
      <div
        aria-label="Mobile action bar"
        className="fixed inset-x-0 bottom-0 z-20 border-t border-white/10 bg-slate-950/95 px-4 pb-[calc(env(safe-area-inset-bottom)+1rem)] pt-3 shadow-2xl shadow-black/50 backdrop-blur lg:hidden"
        data-testid="mobile-action-bar"
      >
        <div className="mx-auto flex max-w-6xl items-center gap-3">
          <div className="min-w-0 flex-1">
            <div className="truncate text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              {previewState.appliedAt
                ? previewState.verifiedAt
                  ? "Verified"
                  : "Applied"
                : previewState.approvedAt
                  ? "Approved"
                  : previewState.approvalAvailable
                    ? "Needs approval"
                    : "Draft"}
            </div>
            <div className="truncate text-sm font-medium text-slate-200">
              {previewState.verifiedAt
                ? "Ready for closeout"
                : previewState.appliedAt
                  ? "Verification required"
                  : "No files changed"}
            </div>
          </div>
          {previewState.appliedAt && !previewState.verifiedAt ? (
            <button
              className="inline-flex min-h-12 shrink-0 items-center justify-center rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 disabled:opacity-60"
              disabled={previewState.isVerifying}
              onClick={handleVerifyAppliedDiff}
              type="button"
            >
              {previewState.isVerifying ? "Verifying" : "Verify"}
            </button>
          ) : previewState.approvedAt && !previewState.appliedAt ? (
            <button
              className="inline-flex min-h-12 shrink-0 items-center justify-center rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 disabled:opacity-60"
              disabled={previewState.isApplying}
              onClick={handleApplyApprovedDiff}
              type="button"
            >
              {previewState.isApplying ? "Applying" : "Apply"}
            </button>
          ) : previewState.approvalAvailable && !previewState.approvedAt ? (
            <button
              className="inline-flex min-h-12 shrink-0 items-center justify-center rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950"
              onClick={handleApprovePreview}
              type="button"
            >
              Approve
            </button>
          ) : (
            <button
              className={`inline-flex min-h-12 shrink-0 items-center justify-center gap-2 rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 ${
                canPreview ? "" : "opacity-60"
              }`}
              disabled={!canPreview || previewState.isLoading || Boolean(previewState.appliedAt)}
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

function diffFromPayload(payload: unknown): string {
  const record = asRecord(payload);
  return (
    stringValue(record.proposed_diff) ??
    stringValue(record.proposedDiff) ??
    stringValue(record.unified_diff) ??
    stringValue(record.diff) ??
    ""
  );
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

function taskIdFromPayload(payload: unknown): string {
  const record = asRecord(payload);
  const task = asRecord(record.task);
  return (
    stringValue(record.task_id) ??
    stringValue(record.taskId) ??
    stringValue(task.id) ??
    stringValue(asRecord(record.response).task_id) ??
    ""
  );
}

function verificationSummaryFromPayload(payload: unknown): string {
  const record = asRecord(payload);
  const task = asRecord(record.task);
  const verification = asRecord(record.verification);
  const postApplyVerification = asRecord(record.post_apply_verification);
  return (
    stringValue(record.message) ??
    stringValue(record.status) ??
    stringValue(task.status) ??
    stringValue(verification.status) ??
    stringValue(postApplyVerification.status) ??
    "Verification complete."
  );
}

function statusFromPayload(payload: unknown): string {
  return stringValue(asRecord(payload).status) ?? "";
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

function ReceiptField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-emerald-200/20 bg-slate-950/40 p-3 text-emerald-50">
      <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-200/80">
        {label}
      </dt>
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
