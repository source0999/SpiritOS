"use client";

import type { MouseEvent, ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

import { DashboardDemoV4Atmosphere } from "@/components/dashboard/demo-v4/DashboardDemoV4Atmosphere";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import { deriveApprovalGateProposal } from "@/components/coding/approval-gate-binding";
import "@/styles/dashboard-demo-v4.css";

const acceptedFileTypes =
  ".png,.jpg,.jpeg,.webp,.gif,.svg,.mp4,.webm,.mov,.xml,.json,.ts,.tsx,.js,.jsx,.py,.css,.html,.md,.txt";
const acceptedFileExtensions = new Set(
  acceptedFileTypes.split(",").map((extension) => extension.trim()),
);
const codingHistoryStorageKey = "spirit-coding-proxy-history-v1";
const codingDecisionMemoryStorageKey = "spirit-coding-decision-memory-v1";
const maxCodingHistoryEntries = 20;
const maxDecisionMemoryEntries = 12;
const maxMultiTurnContextEntries = 5;
const activityLogStorageKey = "spirit_os_task_history";

// ── Unified diff hygiene ─────────────────────────────────────────────────────
// `git apply` wants a trailing newline on the patch text. `String.trim()` on the
// whole payload deletes it — same class of bug as `str.strip()` on Python diffs.
function unifiedDiffPayloadOrEmpty(raw: string): string {
  return raw.trim().length > 0 ? raw : "";
}

// Match repo-relative implementation paths (aligned with approval-gate-binding heuristics).
const IMPLEMENTATION_TARGET_PATH_RE =
  /(?:^|[\s`"'])((?:src|source_proxy|app|components|lib|scripts|public|tests|styles)\/[A-Za-z0-9._/@()[\]-]+\.(?:tsx?|jsx?|py|css|html|json|md|xml))(?:$|[\s`"',.:;])/gm;

function firstImplementationPathInText(text: string): string {
  const normalized = text.replace(/\\/g, "/");
  IMPLEMENTATION_TARGET_PATH_RE.lastIndex = 0;
  const match = IMPLEMENTATION_TARGET_PATH_RE.exec(normalized);
  return match?.[1]?.trim() ?? "";
}

function isAppRouterPagePath(relPath: string): boolean {
  const p = relPath.replace(/\\/g, "/").toLowerCase();
  return p.startsWith("src/app/") && p.endsWith("page.tsx");
}

function shouldEmitClientLocalCoderDiff(target: string, task: string): boolean {
  const p = target.replace(/\\/g, "/").toLowerCase();
  const t = task.toLowerCase();
  if (isAppRouterPagePath(p)) {
    return true;
  }
  return (
    /\b(create|new file|add file|scaffold)\b/.test(t) &&
    /\.(tsx?|jsx?|ts|js|css|html|json|md|xml)$/i.test(p)
  );
}

function titleFromPathSegment(relPath: string): string {
  const parts = relPath.split("/").filter(Boolean);
  const leaf = parts.length >= 2 ? parts[parts.length - 2] : parts[0] ?? "Page";
  return leaf
    .split(/[-_]+/g)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

function buildDefaultNewPageTsx(relPath: string, taskLine: string): string {
  const title = titleFromPathSegment(relPath);
  const taskComment =
    taskLine.trim().length > 0
      ? taskLine.trim().replace(/\*\//g, "* /").slice(0, 200)
      : "Describe the layout and data you want on this route.";
  return [
    "// ── Local Coder Agent (client fallback) ───────────────────────────────────",
    "// Generated because the proxy diff was empty; tighten copy and wiring before ship.",
    `// Task: ${taskComment}`,
    "",
    'import { GlassPanel } from "@/components/ui/GlassPanel";',
    "",
    "export default function Page() {",
    "  return (",
    '    <main className="mx-auto flex max-w-4xl flex-col gap-6 p-6 text-[color:var(--spirit-fg)]">',
    '      <GlassPanel as="section" className="p-6">',
    `        <h1 className="text-xl font-semibold tracking-tight">${title}</h1>`,
    '        <p className="mt-3 text-sm leading-relaxed text-slate-600">',
    "          Starter route scaffold from the Coder Agent path. Adjust structure, copy, and",
    "          data fetching to match your spec.",
    "        </p>",
    "      </GlassPanel>",
    "    </main>",
    "  );",
    "}",
    "",
  ].join("\n");
}

function buildDefaultNewModuleTsx(relPath: string, taskLine: string): string {
  const base = relPath.split("/").pop()?.replace(/\.tsx$/i, "") ?? "Component";
  const safe = /^[A-Za-z_][A-Za-z0-9_]*$/.test(base) ? base : "GeneratedComponent";
  const taskComment =
    taskLine.trim().length > 0
      ? taskLine.trim().replace(/\*\//g, "* /").slice(0, 200)
      : "Component requested from task text.";
  return [
    "// ── Local Coder Agent (client fallback) ───────────────────────────────────",
    `// Task: ${taskComment}`,
    "",
    "type Props = {",
    "  className?: string;",
    "};",
    "",
    `export function ${safe}(props: Props) {`,
    "  return (",
    '    <div className={props.className} data-spirit-local-coder="true">',
    "      {/* Implement the UI described in your task. */}",
    "    </div>",
    "  );",
    "}",
    "",
  ].join("\n");
}

function buildDefaultNewTsModule(relPath: string, taskLine: string): string {
  const taskComment =
    taskLine.trim().length > 0
      ? taskLine.trim().replace(/\*\//g, "* /").slice(0, 200)
      : "Module requested from task text.";
  return [
    "// ── Local Coder Agent (client fallback) ───────────────────────────────────",
    `// Task: ${taskComment}`,
    "",
    "export const spiritLocalCoderMarker = true;",
    "",
  ].join("\n");
}

function newFileUnifiedDiff(relPath: string, fileBody: string): string {
  const path = relPath.replace(/\\/g, "/").replace(/^\.\/+/, "");
  let text = fileBody.replace(/\r\n/g, "\n");
  if (!text.endsWith("\n")) {
    text += "\n";
  }
  const lines = text.slice(0, -1).split("\n");
  const n = lines.length;
  const body = `${lines.map((line) => `+${line}`).join("\n")}\n`;
  return [
    `diff --git a/${path} b/${path}`,
    "new file mode 100644",
    "index 0000000..1111111",
    "--- /dev/null",
    `+++ b/${path}`,
    `@@ -0,0 +1,${n} @@`,
    body,
  ].join("\n");
}

/**
 * When the Source proxy returns an empty proposed_diff for local implementation work,
 * synthesize a valid unified diff so the approval gate and diff preview stay useful.
 */
function tryClientLocalCoderImplementationDiff(args: {
  decision: ProxyRouteDecisionResponse;
  mergedProposedDiff: string;
  mergedTarget: string;
  task: string;
  promptText: string;
}): { proposedDiff: string; target: string } | null {
  const { decision, mergedProposedDiff, mergedTarget, task, promptText } = args;
  const trimmedDiff = mergedProposedDiff.trim();
  if (
    trimmedDiff.includes("diff --git ") ||
    trimmedDiff.includes("\n@@ ") ||
    trimmedDiff.startsWith("--- ")
  ) {
    return null;
  }

  const route = decision.recommended_route ?? "";
  const taskClass = decision.task_classification ?? "";
  const coderish =
    route === "local_route" ||
    taskClass.includes("implementation") ||
    route.includes("coder");

  const firstPathFromContext =
    mergedTarget.trim() ||
    firstImplementationPathInText(promptText) ||
    firstImplementationPathInText(task);

  // Scaffold deletion burned the old demo fallbacks — if the proxy leaves proposed_diff empty
  // on coder-shaped routes, synthesize *something* so ApprovalGate + diff preview never starve.
  if (!trimmedDiff && coderish && firstPathFromContext) {
    const lower = firstPathFromContext.toLowerCase();
    let body: string;
    if (lower.endsWith("page.tsx") && lower.includes("src/app/")) {
      body = buildDefaultNewPageTsx(firstPathFromContext, task);
    } else if (lower.endsWith(".tsx") || lower.endsWith(".jsx")) {
      body = buildDefaultNewModuleTsx(firstPathFromContext, task);
    } else if (lower.endsWith(".ts") || lower.endsWith(".js")) {
      body = buildDefaultNewTsModule(firstPathFromContext, task);
    } else {
      body = [`// ${task.trim() || "Coder fallback stub."}`, ""].join("\n");
    }
    const synthetic =
      newFileUnifiedDiff(firstPathFromContext, body) ||
      `--- a/${firstPathFromContext}\n+++ b/${firstPathFromContext}\n@@ -0,0 +1,5 @@\n+// TODO: implement task\n`;
    return { proposedDiff: synthetic, target: firstPathFromContext };
  }

  if (decision.recommended_route !== "local_route") {
    return null;
  }
  if (decision.task_classification !== "implementation") {
    return null;
  }

  const target =
    mergedTarget.trim() ||
    firstImplementationPathInText(task) ||
    firstImplementationPathInText(promptText);
  if (!target) {
    return null;
  }
  if (!shouldEmitClientLocalCoderDiff(target, task)) {
    return null;
  }

  const lower = target.toLowerCase();
  let body: string;
  if (lower.endsWith("page.tsx") && lower.includes("src/app/")) {
    body = buildDefaultNewPageTsx(target, task);
  } else if (lower.endsWith(".tsx") || lower.endsWith(".jsx")) {
    body = buildDefaultNewModuleTsx(target, task);
  } else if (lower.endsWith(".ts") || lower.endsWith(".js")) {
    body = buildDefaultNewTsModule(target, task);
  } else {
    body = [`// ${task.trim() || "New file from Coder Agent path."}`, ""].join("\n");
  }

  return {
    proposedDiff: newFileUnifiedDiff(target, body),
    target,
  };
}

type ProcessLog = {
  id: number;
  label: string;
  detail: string;
  level: "info" | "success" | "warning";
};

const DEFAULT_PROCESS_LOGS: ProcessLog[] = [
  {
    id: 1,
    label: "Ready to code",
    detail: "Describe the coding task below, then submit. The activity log will explain each step in plain language.",
    level: "info",
  },
];

function loadPersistedActivityLogs(): ProcessLog[] | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(activityLogStorageKey);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed) || parsed.length === 0) {
      return null;
    }
    const cleaned: ProcessLog[] = [];
    for (const entry of parsed) {
      if (
        entry &&
        typeof entry === "object" &&
        typeof (entry as ProcessLog).id === "number" &&
        typeof (entry as ProcessLog).label === "string" &&
        typeof (entry as ProcessLog).detail === "string" &&
        ((entry as ProcessLog).level === "info" ||
          (entry as ProcessLog).level === "success" ||
          (entry as ProcessLog).level === "warning")
      ) {
        cleaned.push(entry as ProcessLog);
      }
    }
    return cleaned.length > 0 ? cleaned : null;
  } catch {
    return null;
  }
}

type ProxyMetrics = {
  health: "online" | "offline";
  route: string;
  model: string;
  risk: string;
  tokens: number | null;
};

type UploadedFile = {
  id: string;
  lastModified: number;
  name: string;
  size: number;
  type: string;
};

type ResearchSource = {
  title?: string;
  url?: string;
  snippet?: string;
};

type ProxyRouteDecisionResponse = {
  confidence?: number;
  confidence_score?: number;
  task_classification?: string;
  recommended_route?: string;
  model?: string;
  recommended_model?: string;
  primary_model?: string;
  target_model_hint?: string;
  reason_codes?: string[];
  risk_tier?: string;
  context_estimate?: {
    estimated_task_tokens?: number;
    total_estimated_tokens?: number;
  };
  next_prompt_action?: string;
  research_recommended?: boolean;
  research_sources?: ResearchSource[];
  self_correction_checks?: SelfCorrectionCheck[];
};

type PromptPacketResponse = {
  phase_label?: string;
  increment_label?: string;
  increment_goal?: string;
  task_summary?: string;
  prompt_text?: string;
  requested_output?: string[];
  research_sources?: ResearchSource[];
  route_decision?: ProxyRouteDecisionResponse;
  requests_for_more_information?: string[];
  proposed_diff?: string;
  proposedDiff?: string;
  target?: string;
  coder_agent_local_diff?: boolean;
  coderAgentLocalDiff?: boolean;
};

type FinalOutput = {
  attachedFiles: UploadedFile[];
  completedAt: string;
  contextTurnCount: number;
  decision: ProxyRouteDecisionResponse;
  decisionPayload: string;
  promptText: string;
  researchSources: ResearchSource[];
  requests: string[];
  runId: number;
  selfCorrection: SelfCorrectionState;
  summary: string;
  coderAgentLocalDiff?: boolean;
};

type SelfCorrectionState = {
  checks: SelfCorrectionCheck[];
  confidence: number;
  reasons: string[];
  refinedInstruction: string;
  triggered: boolean;
};

type SelfCorrectionCheck = {
  answer?: string;
  id?: string;
  passed?: boolean;
  question?: string;
};

type CodingHistoryEntry = {
  attachedFileCount: number;
  completedAt: string;
  contextTurnCount: number;
  id: string;
  model: string;
  recommendation: string;
  researchSourceCount: number;
  risk: string;
  route: string;
  runId: number;
  summary: string;
  task: string;
};

type DecisionMemoryEntry = {
  classification: string;
  completedAt: string;
  id: string;
  model: string;
  recommendation: string;
  reasonCodes: string[];
  risk: string;
  route: string;
  task: string;
};

type ApprovalPreviewResponse = {
  action?: string;
  approval_boundaries?: Record<string, string[]>;
  decision?: "blocked" | "requires_human_approval" | "preview_only" | string;
  manifest_version?: string;
  next_step?: string;
  reason_codes?: string[];
  requires_human_approval?: boolean;
  safety_message?: string;
  target?: string | null;
  would_execute?: boolean;
};

type TelemetryRoute = {
  approval?: string;
  display_name?: string;
  enabled_aliases?: string[];
  next_prompt_action?: string;
  route_type?: string;
  spend?: string;
  status?: string;
};

type TelemetryTool = {
  access?: string;
  category?: string;
  endpoint?: string;
  endpoints?: string[];
  name?: string;
};

type SourceTelemetryResponse = {
  access_scope?: string;
  approval_boundaries?: Record<string, string[]>;
  available_routes?: TelemetryRoute[];
  context_bundle_status?: {
    bundles?: { name?: string; size_bytes?: number | null; status?: string }[];
  };
  enabled_tools?: TelemetryTool[];
  error?: string;
  manifest_version?: string;
  service?: string;
  windows_bridge_status?: {
    enabled?: boolean;
    status?: string;
  };
};

type TelemetryState = {
  error: string | null;
  isChecking: boolean;
  lastCheckedAt: string | null;
  status: SourceTelemetryResponse | null;
};

type ApprovalGateState = {
  action: string;
  approvedAt: string | null;
  content: string;
  deniedAt: string | null;
  error: string | null;
  execution: ApprovedActionExecutionResponse | null;
  isChecking: boolean;
  preview: ApprovalPreviewResponse | null;
  proposedDiff: string;
  target: string;
};

type ApprovedActionExecutionResponse = {
  action?: string;
  appliedAt?: string;
  applied_at?: string;
  backup_root?: string;
  backupRelativePath?: string;
  changed_files?: DiffChangedFile[];
  code?: string;
  diff?: string;
  execution?: Record<string, unknown>;
  message?: string;
  ok: boolean;
  proposalId?: string;
  relativeFilePath?: string;
  target?: string;
  task?: LongRunningTaskPayload;
  verification_plan?: string[];
};

type DiffChangedFile = {
  added_lines?: number;
  change_type?: string;
  extension?: string;
  path: string;
  removed_lines?: number;
  risk_flags?: string[];
};

type DiffVerificationCommand = {
  command: string[];
  reason: string;
  requires_human_approval?: boolean;
};

type DiffVerificationPreviewResponse = {
  access_scope?: string;
  blocked_reasons?: { path: string; reason_code: string }[];
  changed_files?: DiffChangedFile[];
  limits?: Record<string, unknown>;
  manual_checks?: string[];
  requires_human_approval?: boolean;
  risk?: string;
  self_correction?: {
    reasons?: string[];
    retry_prompt?: string;
    safer_next_action?: string;
    severity?: string;
    triggered?: boolean;
  };
  status?: string;
  suggested_commands?: DiffVerificationCommand[];
  tool?: string;
  verification_plan?: string[];
  would_apply_diff?: boolean;
  would_execute?: boolean;
};

type DiffVerificationState = {
  error: string | null;
  isChecking: boolean;
  preview: DiffVerificationPreviewResponse | null;
  unifiedDiff: string;
};

type LongRunningTaskPayload = {
  ast_snapshot?: unknown;
  cancelled_at?: string | null;
  created_at?: string;
  current_agent_role?: "architect" | "coder" | "debugger" | string;
  cycle_count?: number;
  description: string;
  id: string;
  next_action?: string;
  open_diffs?: LongRunningTaskDiff[];
  poll_count?: number;
  progress?: number;
  status: string;
  steps?: string[];
  truncated_test_results?: string;
  updated_at?: string;
  would_execute?: boolean;
  writes_allowed?: boolean;
};

type LongRunningTaskDiff = {
  blocked_reasons?: Array<Record<string, unknown>>;
  changed_files?: Array<{ path?: string; risk_flags?: string[] }>;
  diff?: string;
  risk?: string;
  status?: string;
  suggested_commands?: DiffVerificationCommand[];
  verified?: boolean;
};

type LongRunningTaskResponse = {
  access_scope?: string;
  limits?: Record<string, unknown>;
  task: LongRunningTaskPayload;
  tool?: string;
};

type LongRunningTaskState = {
  description: string;
  error: string | null;
  isChecking: boolean;
  response: LongRunningTaskResponse | null;
};

type RouteActionId = "proxy" | "cursor" | "debugger" | "codex";

type RouteAction = {
  id: RouteActionId;
  label: string;
  description: string;
};

const routeActions: RouteAction[] = [
  {
    id: "proxy",
    label: "Run with Proxy Agent",
    description: "Let Source inspect repo context and try the fix here first.",
  },
  {
    id: "cursor",
    label: "Copy build prompt",
    description: "Copies a ready-to-paste build prompt for your editor.",
  },
  {
    id: "debugger",
    label: "Copy debugging prompt",
    description: "Copies a tighter prompt meant for tracing bugs and odd behavior.",
  },
  {
    id: "codex",
    label: "Copy full agent prompt",
    description: "Copies the complete prompt for a larger model pass.",
  },
];

function friendlyRouteName(route: string | undefined): string {
  if (!route) {
    return "Unknown";
  }
  const normalized = route.trim();
  switch (normalized) {
    case "api_route":
      return "Cloud or API path";
    case "manual_route":
      return "Deep review in your editor";
    case "local_route":
      return "Coder Agent";
    case "ask_user":
      return "Needs your input";
    case "pending":
      return "In progress...";
    case "not run":
      return "Not started yet";
    case "unknown":
      return "Unknown";
    case "request failed":
      return "Request failed";
    case "mock_route":
      return "Demo path";
    default:
      return normalized;
  }
}

function friendlyModelHint(model: string): string {
  if (model === "pending" || model === "not returned") {
    return "Not set yet";
  }
  if (model === "mock") {
    return "Demo / offline";
  }
  return model;
}

function friendlyTaskName(taskClass: string | undefined): string {
  if (!taskClass) {
    return "general work";
  }
  return taskClass.replace(/[_-]+/g, " ");
}

function friendlyToolbarRisk(risk: string): string {
  if (risk === "pending" || risk === "not run") {
    return "Waiting...";
  }
  if (risk === "not returned") {
    return "Unknown";
  }
  return risk;
}

function friendlyTokenLine(tokens: number | null): string {
  if (tokens === null) {
    return "Not estimated yet";
  }
  return `About ${tokens.toLocaleString()} tokens (rough count)`;
}

// ── CodingAgentInterface ───────────────────────────────────────────────
// Same proxy harness for `/coding` and embedded `/chat` tab; `embedded` drops duplicate chrome.
export default function CodingAgentInterface({
  embedded = false,
}: {
  embedded?: boolean;
}) {
  const isRunningRef = useRef(false);
  const runSequenceRef = useRef(0);
  const [inputText, setInputText] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [processLogs, setProcessLogs] = useState<ProcessLog[]>(DEFAULT_PROCESS_LOGS);
  const [activityLogPersistenceReady, setActivityLogPersistenceReady] = useState(false);
  const [workflowStepFloor, setWorkflowStepFloor] = useState<number | null>(null);
  const [finalOutput, setFinalOutput] = useState<FinalOutput | null>(null);
  const [conversationHistory, setConversationHistory] = useState<CodingHistoryEntry[]>(
    [],
  );
  const [decisionMemory, setDecisionMemory] = useState<DecisionMemoryEntry[]>([]);
  const [isStorageReady, setIsStorageReady] = useState(false);
  const [telemetry, setTelemetry] = useState<TelemetryState>({
    error: null,
    isChecking: false,
    lastCheckedAt: null,
    status: null,
  });
  const [proxyMetrics, setProxyMetrics] = useState<ProxyMetrics>({
    health: "offline",
    route: "not run",
    model: "not returned",
    risk: "not run",
    tokens: null,
  });
  const [approvalGate, setApprovalGate] = useState<ApprovalGateState>({
    action: "",
    approvedAt: null,
    content: "",
    deniedAt: null,
    error: null,
    execution: null,
    isChecking: false,
    preview: null,
    proposedDiff: "",
    target: "",
  });
  const [diffVerification, setDiffVerification] = useState<DiffVerificationState>({
    error: null,
    isChecking: false,
    preview: null,
    unifiedDiff: "",
  });
  const [longRunningTask, setLongRunningTask] = useState<LongRunningTaskState>({
    description: "Review a large implementation task and prepare a verification plan.",
    error: null,
    isChecking: false,
    response: null,
  });
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    const taskId = longRunningTask.response?.task.id;
    const status = longRunningTask.response?.task.status;
    if (!taskId || isTerminalLongTaskStatus(status)) {
      return;
    }

    const stream = new EventSource(
      `/v1/tasks/long-running/${encodeURIComponent(taskId)}/stream`,
    );

    stream.addEventListener("task", (event) => {
      try {
        const response = JSON.parse((event as MessageEvent).data) as LongRunningTaskResponse;
        setLongRunningTask((current) => ({
          ...current,
          error: null,
          response,
        }));
      } catch {
        setLongRunningTask((current) => ({
          ...current,
          error: "Long-running task stream returned an invalid payload.",
        }));
      }
    });

    stream.addEventListener("error", () => {
      stream.close();
    });

    return () => {
      stream.close();
    };
  }, [longRunningTask.response?.task.id, longRunningTask.response?.task.status]);

  // SSE is primary; this interval backfills when the swarm posts `open_diffs` but the UI
  // never merged them into ApprovalGate / diff verification (regression after demo-v4 removal).
  useEffect(() => {
    const taskId = longRunningTask.response?.task.id;
    const status = longRunningTask.response?.task.status;
    if (!taskId || isTerminalLongTaskStatus(status)) {
      return;
    }

    let cancelled = false;
    let lastSyncedDiff = "";

    const tick = async () => {
      if (cancelled) {
        return;
      }
      try {
        const payload = await callLongRunningTaskStatus(taskId);
        if (cancelled) {
          return;
        }
        setLongRunningTask((current) => {
          if (current.response?.task.id !== taskId) {
            return current;
          }
          return { ...current, response: payload, error: null };
        });

        const diffEntry = payload.task.open_diffs?.[0];
        const diff = typeof diffEntry?.diff === "string" ? diffEntry.diff.trim() : "";
        // #region agent log
        fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "d97a52",
          },
          body: JSON.stringify({
            sessionId: "d97a52",
            hypothesisId: "H5",
            location: "CodingAgentInterface.tsx:longTaskPollTick",
            message: "poll_status_snapshot",
            data: {
              taskId,
              status: payload.task.status,
              openDiffsN: payload.task.open_diffs?.length ?? 0,
              diffLen: diff.length,
              skippedDup: diff.length > 0 && diff === lastSyncedDiff,
            },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        if (!diff || diff === lastSyncedDiff) {
          return;
        }
        lastSyncedDiff = diff;
        const rawFiles = diffEntry?.changed_files;
        let target = "";
        if (Array.isArray(rawFiles) && rawFiles.length > 0) {
          const first = rawFiles[0] as { path?: string } | string;
          if (typeof first === "string") {
            target = first.trim();
          } else if (first && typeof first.path === "string") {
            target = first.path.trim();
          }
        }

        setApprovalGate((prev) => ({
          ...prev,
          proposedDiff: diff,
          target: target || prev.target,
        }));
        setDiffVerification((prev) => ({
          ...prev,
          unifiedDiff: diff,
          error: null,
          preview: null,
        }));
        void previewDiffVerification(diff);
      } catch (err) {
        // #region agent log
        fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "d97a52",
          },
          body: JSON.stringify({
            sessionId: "d97a52",
            hypothesisId: "H5",
            location: "CodingAgentInterface.tsx:longTaskPollTick",
            message: "poll_status_error",
            data: {
              taskId,
              err: err instanceof Error ? err.message : "unknown",
            },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
      }
    };

    void tick();
    const interval = window.setInterval(() => void tick(), 1500);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [longRunningTask.response?.task.id, longRunningTask.response?.task.status]);

  useEffect(() => {
    const restored = loadPersistedActivityLogs();
    if (restored) {
      setProcessLogs(restored);
    }
    setActivityLogPersistenceReady(true);
  }, []);

  useEffect(() => {
    if (!activityLogPersistenceReady || typeof window === "undefined") {
      return;
    }
    try {
      window.localStorage.setItem(activityLogStorageKey, JSON.stringify(processLogs));
    } catch {
      // Quota or private mode — activity log stays in-memory only.
    }
  }, [activityLogPersistenceReady, processLogs]);

  useEffect(() => {
    queueMicrotask(() => {
      setConversationHistory(loadCodingHistory());
      setDecisionMemory(loadDecisionMemory());
      setIsStorageReady(true);
    });
  }, []);

  useEffect(() => {
    if (!isStorageReady) {
      return;
    }

    saveCodingHistory(conversationHistory);
  }, [conversationHistory, isStorageReady]);

  useEffect(() => {
    if (!isStorageReady) {
      return;
    }

    saveDecisionMemory(decisionMemory);
  }, [decisionMemory, isStorageReady]);

  useEffect(() => {
    void refreshTelemetry();
  }, []);

  useEffect(() => {
    runSequenceRef.current = Math.max(
      runSequenceRef.current,
      ...conversationHistory.map((entry) => entry.runId),
      0,
    );
  }, [conversationHistory]);

  async function refreshTelemetry() {
    setTelemetry((current) => ({
      ...current,
      error: null,
      isChecking: true,
    }));

    try {
      const status = await callSourceTelemetry();
      setTelemetry({
        error: null,
        isChecking: false,
        lastCheckedAt: new Date().toISOString(),
        status,
      });
      // ── Toolbar health was only flipping after a full proxy run; `/v1/self/status`
      // succeeding means the agent surface is reachable — mirror that here.
      setProxyMetrics((prev) => ({ ...prev, health: "online" }));
    } catch (error) {
      setTelemetry((current) => ({
        ...current,
        error: friendlyRunErrorMessage(
          error instanceof Error ? error.message : "Unknown telemetry error.",
        ),
        isChecking: false,
        lastCheckedAt: new Date().toISOString(),
      }));
      setProxyMetrics((prev) => ({ ...prev, health: "offline" }));
    }
  }

  async function previewApprovalGate() {
    const proposedDiff =
      unifiedDiffPayloadOrEmpty(approvalGate.proposedDiff) ||
      unifiedDiffPayloadOrEmpty(diffVerification.unifiedDiff);
    setApprovalGate((current) => ({
      ...current,
      approvedAt: null,
      deniedAt: null,
      error: null,
      isChecking: true,
      preview: null,
    }));

    try {
      const preview = await callActionPreview({
        action: approvalGate.action,
        routeType: proxyMetrics.route,
        target: approvalGate.target,
      });
      const normalizedPreview = normalizeApprovalPreview({
        action: approvalGate.action,
        preview,
        target: approvalGate.target,
      });
      setApprovalGate((current) => ({
        ...current,
        isChecking: false,
        preview: normalizedPreview,
      }));
      if (proposedDiff) {
        const diffPreview = await callDiffVerificationPreview(proposedDiff, {
          routeType:
            proxyMetrics.route === "not run" || proxyMetrics.route === "pending"
              ? undefined
              : proxyMetrics.route,
          nextPromptAction: finalOutput?.decision?.next_prompt_action,
        });
        const normalizedDiffPreview = normalizeDiffVerificationPreview(diffPreview);
        setDiffVerification((current) => ({
          ...current,
          error: null,
          isChecking: false,
          preview: normalizedDiffPreview,
          unifiedDiff: proposedDiff,
        }));
      }
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Approval preview",
          detail: `${normalizedPreview.decision ?? "unknown"}: ${
            normalizedPreview.safety_message ??
            normalizedPreview.next_step ??
            "No safety message returned."
          }`,
          level:
            normalizedPreview.decision === "blocked"
              ? "warning"
              : normalizedPreview.requires_human_approval
                ? "warning"
                : "success",
        },
      ]);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown approval preview error.";
      setApprovalGate((current) => ({
        ...current,
        error: message,
        isChecking: false,
      }));
      setDiffVerification((current) => ({
        ...current,
        error: message,
        isChecking: false,
      }));
    }
  }

  async function approvePreviewedAction(event?: MouseEvent<HTMLButtonElement>) {
    event?.preventDefault();
    const approvedDiff =
      unifiedDiffPayloadOrEmpty(approvalGate.proposedDiff) ||
      unifiedDiffPayloadOrEmpty(diffVerification.unifiedDiff);
    setApprovalGate((current) => ({
      ...current,
      error: null,
      execution: null,
      isChecking: true,
    }));
    if (approvedDiff) {
      setLongRunningTask((current) => ({
        ...current,
        error: null,
        isChecking: true,
      }));
    }

    try {
      let taskId = longRunningTask.response?.task.id ?? "";
      if (approvedDiff && !taskId) {
        const created = await callLongRunningTaskCreate(
          longRunningTask.description.trim() ||
            finalOutput?.summary ||
            approvalGate.action,
        );
        taskId = created.task.id;
        setLongRunningTask((current) => ({
          ...current,
          response: created,
        }));
      }
      const execution = await callApprovedActionExecute({
        action: approvalGate.action,
        approvedDiff,
        content: approvalGate.content,
        target: approvalGate.target,
        taskId,
      });
      const approvedAt = new Date().toISOString();
      setApprovalGate((current) => ({
        ...current,
        approvedAt,
        deniedAt: null,
        execution,
        isChecking: false,
      }));
      if (execution.task) {
        setLongRunningTask((current) => ({
          ...current,
          error: null,
          isChecking: false,
          response: {
            access_scope: "approved_execution",
            task: execution.task!,
            tool: "long_running_task_tracker",
          },
        }));
      } else {
        setLongRunningTask((current) => ({
          ...current,
          isChecking: false,
        }));
      }
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Approval executed",
          detail: execution.ok
            ? `Applied ${execution.relativeFilePath ?? approvalGate.target}.`
            : execution.message ?? "The execution layer rejected this approved action.",
          level: execution.ok ? "success" : "warning",
        },
      ]);
      // ── Keep the workflow rail pinned to Execution+ after approve; cleared only via
      // "Start new task" so a flaky workflowStep() cannot yeet the user back to phase 1.
      setWorkflowStepFloor(5);
      queueMicrotask(() => {
        document
          .getElementById("spirit-coding-workflow-execution")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch (error) {
      setApprovalGate((current) => ({
        ...current,
        error:
          error instanceof Error
            ? error.message
            : "Unknown approved action execution error.",
        isChecking: false,
      }));
      setLongRunningTask((current) => ({
        ...current,
        error:
          error instanceof Error
            ? error.message
            : "Unknown approved action execution error.",
        isChecking: false,
      }));
    }
  }

  function denyPreviewedAction() {
    setApprovalGate((current) => ({
      ...current,
      approvedAt: null,
      deniedAt: new Date().toISOString(),
      execution: null,
    }));
    setProcessLogs((currentLogs) => [
      ...currentLogs,
      {
        id: Date.now(),
        label: "Approval denied",
        detail: `User denied: ${approvalGate.action} ${
          approvalGate.target ? `(${approvalGate.target})` : ""
        }.`,
        level: "warning",
      },
    ]);
  }

  async function previewDiffVerification(unifiedDiffOverride?: string) {
    const unifiedDiffText = unifiedDiffOverride ?? diffVerification.unifiedDiff;
    if (!looksLikeUnifiedDiff(unifiedDiffText)) {
      setDiffVerification((current) => ({
        ...current,
        error: "Paste a unified diff, not just a file path. Include diff --git or @@ hunk lines.",
        isChecking: false,
        preview: null,
      }));
      return;
    }

    setDiffVerification((current) => ({
      ...current,
      error: null,
      isChecking: true,
      preview: null,
    }));

    try {
      const preview = await callDiffVerificationPreview(unifiedDiffText, {
        routeType:
          proxyMetrics.route === "not run" || proxyMetrics.route === "pending"
            ? undefined
            : proxyMetrics.route,
        nextPromptAction: finalOutput?.decision?.next_prompt_action,
      });
      const normalizedPreview = normalizeDiffVerificationPreview(preview);
      setDiffVerification((current) => ({
        ...current,
        isChecking: false,
        preview: normalizedPreview,
        ...(unifiedDiffOverride !== undefined ? { unifiedDiff: unifiedDiffText } : {}),
      }));
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Diff verification",
          detail: `${normalizedPreview.status ?? "unknown"}: ${
            normalizedPreview.changed_files?.length ?? 0
          } changed file${preview.changed_files?.length === 1 ? "" : "s"}; risk ${
            normalizedPreview.risk ?? "unknown"
          }.`,
          level: normalizedPreview.status === "blocked" ? "warning" : "success",
        },
      ]);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown diff verification error.";
      setDiffVerification((current) => ({
        ...current,
        error: message,
        isChecking: false,
      }));
    }
  }

  async function startLongRunningTask() {
    await runLongTaskRequest(async () =>
      callLongRunningTaskCreate(longRunningTask.description),
    );
  }

  async function pollLongRunningTask() {
    const taskId = longRunningTask.response?.task.id;
    if (!taskId) {
      setLongRunningTask((current) => ({
        ...current,
        error: "Start a long-running task before polling.",
      }));
      return;
    }

    await runLongTaskRequest(async () => callLongRunningTaskStatus(taskId));
  }

  async function cancelLongRunningTask() {
    const taskId = longRunningTask.response?.task.id;
    if (!taskId) {
      setLongRunningTask((current) => ({
        ...current,
        error: "Start a long-running task before cancelling.",
      }));
      return;
    }

    await runLongTaskRequest(async () => callLongRunningTaskCancel(taskId));
  }

  function loadTrackedDiffForVerification(diff: string) {
    setDiffVerification((current) => ({
      ...current,
      error: null,
      preview: null,
      unifiedDiff: diff,
    }));
  }

  async function runLongTaskRequest(
    request: () => Promise<LongRunningTaskResponse>,
  ) {
    setLongRunningTask((current) => ({
      ...current,
      error: null,
      isChecking: true,
    }));

    try {
      const response = await request();
      setLongRunningTask((current) => ({
        ...current,
        isChecking: false,
        response,
      }));
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Long task",
          detail: `${response.task.status}: ${response.task.description}. Progress ${
            response.task.progress ?? 0
          }%.`,
          level: response.task.status === "cancelled" ? "warning" : "success",
        },
      ]);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown long-running task error.";
      setLongRunningTask((current) => ({
        ...current,
        error: message,
        isChecking: false,
      }));
    }
  }

  async function runProxyFlow() {
    if (isRunningRef.current) {
      // #region agent log
      fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "242265",
        },
        body: JSON.stringify({
          sessionId: "242265",
          hypothesisId: "C",
          location: "CodingAgentInterface.tsx:runProxyFlow",
          message: "early_return_isRunningRef_true",
          data: { note: "prior run may still be awaiting or ref stuck" },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      return;
    }

    isRunningRef.current = true;
    const runId = runSequenceRef.current + 1;
    runSequenceRef.current = runId;
    const startedAt = new Date();
    setIsRunning(true);

    const task = inputText.trim();
    const attachedFiles = uploadedFiles;
    const priorTurns = conversationHistory.slice(0, maxMultiTurnContextEntries);
    const memoryEntries = decisionMemory.slice(0, maxDecisionMemoryEntries);
    const activeTask =
      normalizeTaskText(longRunningTask.response?.task.description ?? "") ===
      normalizeTaskText(task)
        ? longRunningTask.response?.task
        : null;
    const activeTaskId = activeTask?.id;
    const currentAgentRole = activeTask?.current_agent_role;
    // Re-runs can sit on prompt_packet for minutes — nuking the gate here leaves the
    // Proposal / Diff panels blank the whole time (looks like a total regression).
    applyDiscoveryWorkspaceForTask(task, { clearProposal: false });
    setWorkflowStepFloor(null);
    setProxyMetrics({
      health: "offline",
      route: "pending",
      model: "pending",
      risk: "pending",
      tokens: null,
    });
    setProcessLogs([
      {
        id: 1,
        label: `Run #${runId} started`,
        detail: `Started at ${formatRunTimestamp(startedAt)}. Using ${priorTurns.length} earlier run${
          priorTurns.length === 1 ? "" : "s"
        } and ${memoryEntries.length} saved decision${
          memoryEntries.length === 1 ? "" : "s"
        } as background context. Asking the agent how to handle this task...`,
        level: "info",
      },
    ]);

    // #region agent log
    fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "242265",
      },
      body: JSON.stringify({
        sessionId: "242265",
        hypothesisId: "A",
        location: "CodingAgentInterface.tsx:runProxyFlow",
        message: "before_route_decision",
        data: { runId, taskLen: task.length },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion

    try {
      const decision = await callProxyRouteDecision({
        activeTaskId,
        attachedFiles,
        currentAgentRole,
        memoryEntries,
        priorTurns,
        task,
      });
      // #region agent log
      fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "242265",
        },
        body: JSON.stringify({
          sessionId: "242265",
          hypothesisId: "A",
          location: "CodingAgentInterface.tsx:runProxyFlow",
          message: "after_route_decision",
          data: {
            runId,
            route: decision.recommended_route ?? null,
            taskClass: decision.task_classification ?? null,
            researchRecommended: Boolean(decision.research_recommended),
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      let researchSources = decision.research_sources ?? [];

      if (decision.research_recommended) {
        // #region agent log
        fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "242265",
          },
          body: JSON.stringify({
            sessionId: "242265",
            hypothesisId: "E",
            location: "CodingAgentInterface.tsx:runProxyFlow",
            message: "before_research_preview",
            data: { runId },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        const researchPreview = await callProxyResearchPreview({
          activeTaskId,
          attachedFiles,
          currentAgentRole,
          memoryEntries,
          priorTurns,
          task,
        });
        researchSources = researchPreview.research_sources ?? researchSources;
        // #region agent log
        fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "242265",
          },
          body: JSON.stringify({
            sessionId: "242265",
            hypothesisId: "E",
            location: "CodingAgentInterface.tsx:runProxyFlow",
            message: "after_research_preview",
            data: { runId, sourceCount: researchSources.length },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
      }

      // #region agent log
      fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "242265",
        },
        body: JSON.stringify({
          sessionId: "242265",
          hypothesisId: "B",
          location: "CodingAgentInterface.tsx:runProxyFlow",
          message: "before_prompt_packet",
          data: { runId },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      const promptPacket = await callProxyPromptPacket({
        activeTaskId,
        attachedFiles,
        currentAgentRole,
        memoryEntries,
        priorTurns,
        researchSources,
        task,
      });
      // #region agent log
      fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "242265",
        },
        body: JSON.stringify({
          sessionId: "242265",
          hypothesisId: "B",
          location: "CodingAgentInterface.tsx:runProxyFlow",
          message: "after_prompt_packet",
          data: {
            runId,
            proposedLen: (promptPacket.proposed_diff ?? promptPacket.proposedDiff ?? "").length,
            targetSet: Boolean(
              typeof promptPacket.target === "string" && promptPacket.target.trim(),
            ),
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      researchSources = promptPacket.research_sources ?? researchSources;
      const rawPacketSnake =
        typeof promptPacket.proposed_diff === "string" ? promptPacket.proposed_diff : "";
      const rawPacketCamel =
        typeof promptPacket.proposedDiff === "string" ? promptPacket.proposedDiff : "";
      const packetDiff =
        unifiedDiffPayloadOrEmpty(rawPacketSnake) || unifiedDiffPayloadOrEmpty(rawPacketCamel);
      const packetTarget =
        typeof promptPacket.target === "string" ? promptPacket.target.trim() : "";
      const approvalProposal = deriveApprovalGateProposal(decision, promptPacket);
      const mergedProposedDiff =
        packetDiff || unifiedDiffPayloadOrEmpty(approvalProposal?.proposedDiff ?? "");
      const mergedTarget = packetTarget || (approvalProposal?.target ?? "").trim();
      const mergedAction =
        mergedProposedDiff && mergedTarget
          ? "modify file"
          : (approvalProposal?.action ?? "");
      const clientCoderPatch = tryClientLocalCoderImplementationDiff({
        decision,
        mergedProposedDiff,
        mergedTarget,
        promptText: promptPacket.prompt_text ?? "",
        task,
      });
      if (clientCoderPatch) {
        promptPacket.proposed_diff = clientCoderPatch.proposedDiff;
        promptPacket.proposedDiff = clientCoderPatch.proposedDiff;
        promptPacket.target = clientCoderPatch.target;
        promptPacket.coder_agent_local_diff = true;
        promptPacket.coderAgentLocalDiff = true;
      }
      // #region agent log
      fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "d97a52",
        },
        body: JSON.stringify({
          sessionId: "d97a52",
          hypothesisId: "H2",
          location: "CodingAgentInterface.tsx:runProxyFlow",
          message: "merge_client_coder_patch",
          data: {
            runId,
            clientPatch: Boolean(clientCoderPatch),
            mergedDiffLen: mergedProposedDiff.length,
            mergedTargetLen: mergedTarget.length,
            route: decision.recommended_route ?? "",
            taskClass: decision.task_classification ?? "",
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      const effectiveProposedDiff = clientCoderPatch?.proposedDiff ?? mergedProposedDiff;
      const effectiveTarget = clientCoderPatch?.target ?? mergedTarget;
      const effectiveAction = clientCoderPatch ? "create file" : mergedAction;
      const coderDiffReady = Boolean(
        clientCoderPatch ||
          promptPacket.coder_agent_local_diff ||
          promptPacket.coderAgentLocalDiff,
      );
      const selfCorrection = buildSelfCorrectionState({
        decision,
        memoryEntries,
        promptPacket,
        task,
      });

      setProxyMetrics({
        health: "online",
        route: decision.recommended_route ?? "unknown",
        model: modelFromDecision(decision),
        risk: formatRiskTier(decision.risk_tier),
        tokens: decision.context_estimate?.total_estimated_tokens ?? null,
      });
      setApprovalGate((current) => ({
        ...current,
        action: effectiveAction,
        approvedAt: null,
        content: effectiveProposedDiff ? "" : approvalProposal?.content ?? "",
        deniedAt: null,
        error: null,
        execution: null,
        preview: null,
        proposedDiff: effectiveProposedDiff,
        target: effectiveTarget,
      }));
      // #region agent log
      fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "d97a52",
        },
        body: JSON.stringify({
          sessionId: "d97a52",
          hypothesisId: "H3",
          location: "CodingAgentInterface.tsx:runProxyFlow",
          message: "approval_gate_effective_payload",
          data: {
            runId,
            effDiffLen: effectiveProposedDiff.length,
            effTargetLen: effectiveTarget.length,
            effAction: effectiveAction,
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      setDiffVerification((current) => ({
        ...current,
        error: null,
        preview: null,
        unifiedDiff: effectiveProposedDiff,
      }));
      void refreshTelemetry();
      setFinalOutput({
        attachedFiles,
        completedAt: new Date().toISOString(),
        contextTurnCount: priorTurns.length,
        decision,
        decisionPayload: JSON.stringify(decision, null, 2),
        coderAgentLocalDiff: coderDiffReady,
        promptText: coderDiffReady
          ? "Coder Agent produced a unified diff for the approval gate (see Proposal / Diff Preview)."
          : promptPacket.prompt_text ?? "No prompt_text returned.",
        researchSources,
        requests: promptPacket.requests_for_more_information ?? [],
        runId,
        selfCorrection,
        summary: buildDecisionSummary({
          attachedFiles,
          decision,
          memoryEntries,
          promptPacket,
          priorTurns,
          runId,
          researchSources,
        }),
      });
      setConversationHistory((currentHistory) =>
        addCodingHistoryEntry(
          currentHistory,
          buildCodingHistoryEntry({
            attachedFiles,
            completedAt: new Date().toISOString(),
            decision,
            memoryEntries,
            promptPacket,
            priorTurns,
            researchSources,
            runId,
            task,
          }),
        ),
      );
      setDecisionMemory((currentMemory) =>
        addDecisionMemoryEntry(currentMemory, buildDecisionMemoryEntry(task, decision)),
      );

      const nextLogs: ProcessLog[] = [
        {
          id: 2,
          label: "How the agent classified this",
        detail: `The agent grouped this as "${
            friendlyTaskName(decision.task_classification)
          }" and chose the path: ${friendlyRouteName(decision.recommended_route)}.`,
          level: "success",
        },
        {
          id: 3,
          label: "What we suggest you do next",
          detail: `Best fit: ${routeActionForDecision(decision).label}. Risk level: ${formatRiskTier(
            decision.risk_tier,
          )}.`,
          level: "success",
        },
        {
          id: 4,
          label: "Earlier runs included",
          detail:
            priorTurns.length > 0
              ? `We reminded the agent about ${priorTurns.length} earlier run${
                  priorTurns.length === 1 ? "" : "s"
                } so it stays consistent with what you already tried.`
              : "No earlier runs were attached to this request.",
          level: "info",
        },
        {
          id: 5,
          label: "Past decisions included",
          detail:
            memoryEntries.length > 0
              ? `We reminded the agent about ${memoryEntries.length} past decision${
                  memoryEntries.length === 1 ? "" : "s"
                } from this browser.`
              : "No saved past decisions were attached to this request.",
          level: "info",
        },
        {
          id: 6,
          label: "Files you attached",
          detail:
            attachedFiles.length > 0
              ? `${attachedFiles.length} file${attachedFiles.length === 1 ? "" : "s"} listed for the agent (names and sizes only): ${attachedFiles
                  .map((file) => file.name)
                  .join(", ")}.`
              : "You did not attach any files to this request.",
          level: "info",
        },
        {
          id: 7,
          label: selfCorrection.triggered
            ? "Double-check suggested"
            : "Confidence looks solid",
          detail: selfCorrection.triggered
            ? `Estimated confidence ${formatConfidence(selfCorrection.confidence)}. ${selfCorrection.reasons.join(
                " ",
              )}`
            : `Estimated confidence ${formatConfidence(selfCorrection.confidence)}. No major red flags from the quick confidence check.`,
          level: selfCorrection.triggered ? "warning" : "success",
        },
        {
          id: 8,
          label: decision.research_recommended
            ? "Research suggested"
            : "Research not required",
          detail: `${researchSources.length} research source${
            researchSources.length === 1 ? "" : "s"
          } came back with the routing step.`,
          level: decision.research_recommended ? "warning" : "info",
        },
      ];

      if (approvalProposal || effectiveProposedDiff) {
        nextLogs.push({
          id: 17,
          label: "Approval gate armed",
          detail: `${effectiveAction || approvalProposal?.action || "modify file"}: ${
            effectiveTarget || approvalProposal?.target || "unknown target"
          }.`,
          level: "warning",
        });
      }

      if (researchSources.length > 0) {
        nextLogs.push(
          ...researchSources.slice(0, 4).map((source, index) => ({
            id: 9 + index,
            label: `${sourceKindLabel(source)} ${index + 1}`,
            detail: `${source.title ?? "Untitled source"}${
              source.url ? ` - ${source.url}` : ""
            }`,
            level: "info" as const,
          })),
        );
      }

      nextLogs.push(
        ...(decision.research_recommended
          ? [
              {
                id: 14,
                label: "Research sources gathered",
                detail: `${researchSources.length} source${
                  researchSources.length === 1 ? "" : "s"
                } are ready to fold into the written prompt.`,
                level: "success" as const,
              },
            ]
          : []),
        {
          id: 15,
          label: coderDiffReady ? "Unified diff ready" : "Written prompt is ready",
          detail: coderDiffReady
            ? `Unified diff and target are ready for the approval gate (${workflowContextLabel(promptPacket)}).`
            : `The full prompt text is ready for ${workflowContextLabel(promptPacket)}.`,
          level: "success",
        },
        {
          id: 16,
          label: "Plain-English summary",
          detail: buildDecisionSummary({
            attachedFiles,
            decision,
            memoryEntries,
            promptPacket,
            priorTurns,
            runId,
            researchSources,
          }),
          level: "success",
        },
      );

      setProcessLogs((currentLogs) => [...currentLogs, ...nextLogs]);
      // #region agent log
      fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "242265",
        },
        body: JSON.stringify({
          sessionId: "242265",
          hypothesisId: "D",
          location: "CodingAgentInterface.tsx:runProxyFlow",
          message: "try_success_complete",
          data: {
            runId,
            effectiveDiffLen: effectiveProposedDiff.length,
            effectiveTargetLen: effectiveTarget.length,
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
    } catch (error) {
      // #region agent log
      fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "242265",
        },
        body: JSON.stringify({
          sessionId: "242265",
          hypothesisId: "D",
          location: "CodingAgentInterface.tsx:runProxyFlow",
          message: "catch_error",
          data: {
            runId,
            err: error instanceof Error ? error.message : String(error),
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      const message = friendlyRunErrorMessage(
        error instanceof Error ? error.message : "Unknown agent service error.",
      );
      if (isProxyFeatureFlagOff(message)) {
        runMockProxyFlow(task, priorTurns, memoryEntries);
        return;
      }

      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: 2,
          label: "Something went wrong",
          detail: message,
          level: "warning",
        },
      ]);
      setFinalOutput({
        attachedFiles: [],
        completedAt: new Date().toISOString(),
        contextTurnCount: priorTurns.length,
        decision: {},
        decisionPayload: message,
        promptText: "",
        researchSources: [],
        requests: ["Confirm SPIRIT_CODING_USE_PROXY=true and restart the dev server"],
        runId,
        selfCorrection: {
          checks: [],
          confidence: 0,
          reasons: ["The proxy request failed before confidence could be evaluated."],
          refinedInstruction:
            "Verify the Source proxy is enabled and reachable before continuing this task.",
          triggered: true,
        },
        summary:
          "The agent service could not choose a path for this run. Check that the Source proxy is running, then run the task again.",
      });
      setConversationHistory((currentHistory) =>
        addCodingHistoryEntry(
          currentHistory,
          buildErrorHistoryEntry({
            completedAt: new Date().toISOString(),
            contextTurnCount: priorTurns.length,
            message,
            runId,
            task,
          }),
        ),
      );
      setProxyMetrics({
        health: "offline",
        route: "request failed",
        model: "not returned",
        risk: "not returned",
        tokens: null,
      });
    } finally {
      // #region agent log
      fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "242265",
        },
        body: JSON.stringify({
          sessionId: "242265",
          hypothesisId: "A",
          location: "CodingAgentInterface.tsx:runProxyFlow",
          message: "finally_clear_running",
          data: { runId },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      isRunningRef.current = false;
      setIsRunning(false);
    }
  }

  function applyDiscoveryWorkspaceForTask(
    description: string,
    options?: { clearProposal?: boolean },
  ) {
    const clearProposal = options?.clearProposal !== false;
    if (clearProposal) {
      setApprovalGate({
        action: "",
        approvedAt: null,
        content: "",
        deniedAt: null,
        error: null,
        execution: null,
        isChecking: false,
        preview: null,
        proposedDiff: "",
        target: "",
      });
      setDiffVerification({
        error: null,
        isChecking: false,
        preview: null,
        unifiedDiff: "",
      });
    } else {
      setApprovalGate((current) => ({
        ...current,
        approvedAt: null,
        deniedAt: null,
        error: null,
        execution: null,
        isChecking: false,
        preview: null,
      }));
      setDiffVerification((current) => ({
        ...current,
        error: null,
        isChecking: false,
        preview: null,
      }));
    }
    setLongRunningTask((current) => {
      const trimmedDescription = description.trim() || current.description;
      const prevTask = current.response?.task;
      const sameDescription =
        prevTask != null &&
        normalizeTaskText(prevTask.description ?? "") ===
          normalizeTaskText(trimmedDescription);
      const keepResponse = Boolean(
        sameDescription && prevTask && !isTerminalLongTaskStatus(prevTask.status),
      );
      // #region agent log
      fetch("http://localhost:7444/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "d97a52",
        },
        body: JSON.stringify({
          sessionId: "d97a52",
          hypothesisId: "H1",
          location: "CodingAgentInterface.tsx:applyDiscoveryWorkspaceForTask",
          message: "long_task_response_branch",
          data: {
            clearProposal,
            keepResponse,
            sameDescription,
            prevTaskId: prevTask?.id ?? null,
            prevStatus: prevTask?.status ?? null,
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      return {
        description: trimmedDescription,
        error: null,
        isChecking: false,
        response: keepResponse ? current.response : null,
      };
    });
  }

  function startNewCodingTask() {
    setWorkflowStepFloor(null);
    applyDiscoveryWorkspaceForTask(
      "Review a large implementation task and prepare a verification plan.",
      { clearProposal: true },
    );
    setInputText("");
    setFinalOutput(null);
    setUploadedFiles([]);
    setProcessLogs(DEFAULT_PROCESS_LOGS);
    if (typeof window !== "undefined") {
      try {
        window.localStorage.removeItem(activityLogStorageKey);
      } catch {
        /* private mode / quota */
      }
    }
  }

  function runMockProxyFlow(
    task: string,
    priorTurns: CodingHistoryEntry[],
    memoryEntries: DecisionMemoryEntry[],
  ) {
    const mockDecision = buildMockDecision(task);
    const mockPacket = buildMockPromptPacket(task);
    const selfCorrection = buildSelfCorrectionState({
      decision: mockDecision,
      memoryEntries,
      promptPacket: mockPacket,
      task,
    });

    setProxyMetrics({
      health: "offline",
      route: mockDecision.recommended_route ?? "mock_route",
      model: "mock",
      risk: formatRiskTier(mockDecision.risk_tier),
      tokens: mockDecision.context_estimate?.total_estimated_tokens ?? null,
    });
    const approvalProposal = deriveApprovalGateProposal(mockDecision, mockPacket);
    setApprovalGate((current) => ({
      ...current,
      action: approvalProposal?.action ?? "",
      approvedAt: null,
      content: approvalProposal?.content ?? "",
      deniedAt: null,
      error: null,
      execution: null,
      preview: null,
      proposedDiff: approvalProposal?.proposedDiff ?? "",
      target: approvalProposal?.target ?? "",
    }));
    setDiffVerification((current) => ({
      ...current,
      error: null,
      preview: null,
      unifiedDiff: approvalProposal?.proposedDiff ?? "",
    }));
    void refreshTelemetry();
    setFinalOutput({
      attachedFiles: uploadedFiles,
      completedAt: new Date().toISOString(),
      contextTurnCount: priorTurns.length,
      decision: mockDecision,
      decisionPayload: JSON.stringify(mockDecision, null, 2),
      coderAgentLocalDiff: false,
      promptText: mockPacket.prompt_text ?? "No mock prompt_text returned.",
      researchSources: [],
      requests: mockPacket.requests_for_more_information ?? [],
      runId: runSequenceRef.current,
      selfCorrection,
      summary: buildDecisionSummary({
        attachedFiles: uploadedFiles,
        decision: mockDecision,
        memoryEntries,
        promptPacket: mockPacket,
        priorTurns,
        runId: runSequenceRef.current,
        researchSources: [],
      }),
    });
    setConversationHistory((currentHistory) =>
      addCodingHistoryEntry(
        currentHistory,
        buildCodingHistoryEntry({
          attachedFiles: uploadedFiles,
          completedAt: new Date().toISOString(),
          decision: mockDecision,
          memoryEntries,
          promptPacket: mockPacket,
          priorTurns,
          researchSources: [],
          runId: runSequenceRef.current,
          task,
        }),
      ),
    );
    setDecisionMemory((currentMemory) =>
      addDecisionMemoryEntry(currentMemory, buildDecisionMemoryEntry(task, mockDecision)),
    );
    setProcessLogs((currentLogs) => [
      ...currentLogs,
      {
        id: 2,
        label: "Live agent is off (demo mode)",
        detail:
          "SPIRIT_CODING_USE_PROXY is not turned on, so this page is showing a safe demo response instead of calling the real service.",
        level: "warning",
      },
      {
        id: 3,
        label: "Demo decision",
        detail: `Demo path chosen: ${friendlyRouteName(mockDecision.recommended_route ?? "")}.`,
        level: "success",
      },
      {
        id: 4,
        label: "Demo prompt ready",
        detail: "Demo prompt text was generated on this machine only. No network call was made.",
        level: "success",
      },
    ]);
  }

  return (
    <div className="dashboard-demo-v4-root">
      <DashboardDemoV4Atmosphere />

      <div className="dashboard-demo-v4-shell">
        <div className="flex min-h-[calc(100dvh-2rem)] flex-col overflow-hidden border border-slate-300 bg-white text-slate-950 lg:min-h-[calc(100dvh-4rem)]">
          <ProxyMetaToolbar metrics={proxyMetrics} isRunning={isRunning} />

          <section className="min-h-0 flex-1 overflow-hidden border-y border-slate-300">
            <OutputWindow
              approvalGate={approvalGate}
              conversationHistory={conversationHistory}
              decisionMemory={decisionMemory}
              diffVerification={diffVerification}
              files={uploadedFiles}
              finalOutput={finalOutput}
              inputText={inputText}
              isRunning={isRunning}
              longRunningTask={longRunningTask}
              logs={processLogs}
              onRefreshTelemetry={refreshTelemetry}
              onApprovalActionChange={(action) =>
                setApprovalGate((current) => ({ ...current, action }))
              }
              onApprovalContentChange={(content) =>
                setApprovalGate((current) => ({ ...current, content }))
              }
              onApprovalTargetChange={(target) =>
                setApprovalGate((current) => ({ ...current, target }))
              }
              onApprovePreviewedAction={approvePreviewedAction}
              onClearHistory={() => setConversationHistory([])}
              onClearMemory={() => setDecisionMemory([])}
              onDenyPreviewedAction={denyPreviewedAction}
              onDiffChange={(unifiedDiff) =>
                setDiffVerification((current) => ({ ...current, unifiedDiff }))
              }
              onTrackedDiffSelect={loadTrackedDiffForVerification}
              onLongTaskCancel={cancelLongRunningTask}
              onLongTaskDescriptionChange={(description) =>
                setLongRunningTask((current) => ({ ...current, description }))
              }
              onLongTaskPoll={pollLongRunningTask}
              onLongTaskStart={startLongRunningTask}
              onInputChange={setInputText}
              onFilesAdded={(files) => setUploadedFiles((current) => [...current, ...files])}
              onPreviewApprovalGate={previewApprovalGate}
              onPreviewDiffVerification={previewDiffVerification}
              onRestoreHistoryEntry={(entry) => setInputText(entry.task)}
              onRunProxyFlow={runProxyFlow}
              onStartNewTask={startNewCodingTask}
              onSubmit={runProxyFlow}
              telemetry={telemetry}
              workflowStepFloor={workflowStepFloor}
            />
          </section>
        </div>
      </div>

      {embedded ? null : <DashboardDemoV4FloatingNav />}
    </div>
  );
}

function ProxyMetaToolbar({
  metrics,
  isRunning,
}: {
  metrics: ProxyMetrics;
  isRunning: boolean;
}) {
  const isOnline = metrics.health === "online";

  return (
    <header className="flex min-h-14 flex-wrap items-end gap-4 border-b-2 border-slate-200 bg-gradient-to-b from-slate-50 to-slate-100 px-4 py-3 text-sm">
      <div className="flex min-w-[12rem] flex-col gap-1">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Current work
        </span>
        <div className="rounded-md border border-slate-300 bg-white px-3 py-1.5 font-medium text-slate-900 shadow-sm">
          SpiritOS coding
        </div>
      </div>

      <div className="hidden h-10 w-px bg-slate-300 sm:block" aria-hidden />

      <div className="flex min-w-[10rem] flex-col gap-1">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Agent service
        </span>
        <div className="flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-1.5 shadow-sm">
          <span
            className={`h-2.5 w-2.5 shrink-0 rounded-full ${
              isOnline ? "bg-green-500" : "bg-red-500"
            }`}
            aria-hidden
          />
          <span className="font-medium text-slate-900">
            {isOnline ? "Connected" : "Not connected"}
          </span>
        </div>
      </div>

      <div className="hidden h-10 w-px bg-slate-300 sm:block" aria-hidden />

      <div className="flex min-w-0 flex-1 flex-col gap-1 sm:min-w-[14rem]">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Where this will run
        </span>
        <div className="rounded-md border border-slate-300 bg-white px-3 py-1.5 font-medium text-slate-900 shadow-sm">
          <span className="text-slate-600">Selected path:</span>{" "}
          {friendlyRouteName(metrics.route)} <span className="text-slate-400">/</span>{" "}
          <span className="text-slate-600">Model:</span> {friendlyModelHint(metrics.model)}{" "}
          <span className="text-slate-400">/</span> <span className="text-slate-600">Safety:</span>{" "}
          {friendlyToolbarRisk(metrics.risk)}
        </div>
      </div>

      <div className="hidden h-10 w-px bg-slate-300 sm:block" aria-hidden />

      <div className="flex min-w-[8rem] flex-col gap-1">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Request size
        </span>
        <div className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-slate-900 shadow-sm">
          {friendlyTokenLine(metrics.tokens)}
        </div>
      </div>

      {isRunning ? (
        <>
          <div className="hidden h-10 w-px bg-slate-300 sm:block" aria-hidden />
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
              Current status
            </span>
            <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-1.5 font-medium text-amber-950 shadow-sm">
              Working on your request...
            </div>
          </div>
        </>
      ) : null}
    </header>
  );
}

function ProcessWindow({ logs }: { logs: ProcessLog[] }) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [logs]);

  return (
    <section className="flex min-h-0 flex-col border-b border-slate-300 md:border-r md:border-b-0">
      <div className="border-b border-slate-800 bg-slate-950 px-4 py-3">
        <div className="font-sans text-sm font-semibold tracking-tight text-white">
          Activity log
        </div>
        <p className="mt-0.5 font-sans text-xs leading-snug text-slate-400">
          Step-by-step timeline. Newest steps scroll to the bottom.
        </p>
      </div>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto bg-slate-900 p-4 font-mono text-sm text-slate-100">
        {logs.length === 0 ? (
          <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-3 text-slate-400">
            Waiting for the first event...
          </div>
        ) : null}

        <div className="space-y-3">
          {logs.map((log) => (
            <div
              key={log.id}
              className="rounded-lg border border-slate-700/90 bg-slate-950/70 p-3 shadow-inner"
            >
              <div className={`text-xs font-semibold uppercase tracking-wide ${logLevelClassName(log.level)}`}>
                {log.label}
              </div>
              <div className="mt-1.5 text-sm leading-relaxed text-slate-300">{log.detail}</div>
            </div>
          ))}
        </div>

        <div ref={bottomRef} />
      </div>
    </section>
  );
}

type WorkflowStageStatus = "waiting" | "active" | "complete" | "blocked";

type WorkflowStageItem = {
  index: number;
  label: string;
  status: WorkflowStageStatus;
};

function workflowStep({
  approvalGate,
  diffVerification,
  finalOutput,
  isRunning,
  longRunningTask,
}: {
  approvalGate: ApprovalGateState;
  diffVerification: DiffVerificationState;
  finalOutput: FinalOutput | null;
  isRunning: boolean;
  longRunningTask: LongRunningTaskState;
}) {
  if (approvalGate.execution?.ok) {
    return 7;
  }
  if (approvalGate.approvedAt || longRunningTask.response?.task.status === "executing") {
    return 5;
  }
  if (approvalGate.preview) {
    return 4;
  }
  if (
    approvalGate.action.trim() ||
    approvalGate.target.trim() ||
    diffVerification.unifiedDiff.trim() ||
    approvalGate.content.trim()
  ) {
    return 3;
  }
  if (finalOutput) {
    return 2;
  }
  return isRunning ? 2 : 1;
}

function workflowStages(activeStep: number): WorkflowStageItem[] {
  const labels = [
    "Task Description",
    "Research / Plan",
    "Proposal / Diff Preview",
    "Approval Gate",
    "Execution",
    "Verification / Tests",
    "Status / Done",
  ];
  return labels.map((label, index) => {
    const step = index + 1;
    return {
      index: step,
      label,
      status:
        step < activeStep ? "complete" : step === activeStep ? "active" : "waiting",
    };
  });
}

function WorkflowRail({ stages }: { stages: WorkflowStageItem[] }) {
  return (
    <aside className="border-b border-slate-300 bg-slate-950 p-4 text-slate-100 lg:border-r lg:border-b-0">
      <div className="text-xs font-bold uppercase tracking-wide text-slate-400">
        Workflow
      </div>
      <div className="mt-4 flex gap-2 overflow-x-auto lg:flex-col lg:overflow-visible">
        {stages.map((stage) => (
          <div
            className={`flex min-w-[13rem] items-center gap-3 border px-3 py-2 lg:min-w-0 ${
              stage.status === "active"
                ? "border-cyan-300 bg-cyan-300/10 text-white"
                : stage.status === "complete"
                  ? "border-green-400/50 bg-green-400/10 text-green-100"
                  : "border-slate-700 bg-slate-900 text-slate-400"
            }`}
            key={stage.index}
          >
            <span
              className={`grid h-7 w-7 shrink-0 place-items-center rounded-full border text-xs font-bold ${
                stage.status === "active"
                  ? "border-cyan-300 text-cyan-100"
                  : stage.status === "complete"
                    ? "border-green-300 text-green-100"
                    : "border-slate-600 text-slate-400"
              }`}
            >
              {stage.index}
            </span>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold">{stage.label}</div>
              <div className="text-[11px] uppercase tracking-wide">
                {stage.status}
              </div>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}

function WorkflowStage({
  children,
  description,
  index,
  sectionId,
  status,
  title,
}: {
  children: ReactNode;
  description: string;
  index: number;
  sectionId?: string;
  status: WorkflowStageStatus;
  title: string;
}) {
  return (
    <section className="rounded-lg border border-slate-300 bg-white shadow-sm" id={sectionId}>
      <div className="flex flex-col gap-3 border-b border-slate-200 p-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-3">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-slate-900 bg-slate-950 text-sm font-bold text-white">
            {index}
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-950">{title}</h2>
            <p className="mt-1 text-sm text-slate-600">{description}</p>
          </div>
        </div>
        <WorkflowBadge tone={status === "complete" ? "success" : status === "active" ? "warning" : "muted"}>
          {status}
        </WorkflowBadge>
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

function WorkflowBadge({
  children,
  tone,
}: {
  children: ReactNode;
  tone: "info" | "muted" | "success" | "warning";
}) {
  const className =
    tone === "success"
      ? "border-green-300 bg-green-50 text-green-900"
      : tone === "warning"
        ? "border-yellow-300 bg-yellow-50 text-yellow-900"
        : tone === "info"
          ? "border-cyan-300 bg-cyan-50 text-cyan-900"
          : "border-slate-300 bg-slate-50 text-slate-700";
  return (
    <span className={`inline-flex shrink-0 border px-2 py-1 text-xs font-semibold ${className}`}>
      {children}
    </span>
  );
}

function EmptyWorkflowMessage({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600">
      {text}
    </div>
  );
}

function ProposalSummaryPanel({ gate }: { gate: ApprovalGateState }) {
  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Proposed Change</h2>
        <WorkflowBadge tone={gate.proposedDiff || gate.content ? "success" : "muted"}>
          {gate.proposedDiff ? "diff ready" : gate.content ? "content ready" : "needs diff"}
        </WorkflowBadge>
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <TelemetryStat label="Action" value={gate.action || "No action proposed"} />
        <TelemetryStat label="Target" value={gate.target || "No target proposed"} />
      </div>
      {gate.proposedDiff ? (
        <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap border border-slate-200 bg-slate-50 p-3 font-mono text-xs leading-5 text-slate-800">
          {gate.proposedDiff}
        </pre>
      ) : null}
    </section>
  );
}

function VerificationSummary({
  diffVerification,
  execution,
  longRunningTask,
}: {
  diffVerification: DiffVerificationState;
  execution: ApprovedActionExecutionResponse | null;
  longRunningTask: LongRunningTaskState;
}) {
  const suggested =
    execution?.verification_plan ??
    diffVerification.preview?.verification_plan ??
    longRunningTask.response?.task.open_diffs?.[0]?.suggested_commands?.map(
      (item) => item.reason,
    ) ??
    [];
  const commands =
    diffVerification.preview?.suggested_commands ??
    longRunningTask.response?.task.open_diffs?.[0]?.suggested_commands ??
    [];

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Verification Plan</h2>
        <WorkflowBadge tone={execution?.ok ? "success" : "muted"}>
          {execution?.ok ? "ready to verify" : "waiting"}
        </WorkflowBadge>
      </div>
      {commands.length > 0 ? (
        <div className="mt-3 space-y-2">
          {commands.map((item) => (
            <div
              className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm"
              key={`${item.command.join(" ")}-${item.reason}`}
            >
              <code className="font-mono text-slate-900">{item.command.join(" ")}</code>
              <div className="mt-1 text-slate-600">{item.reason}</div>
            </div>
          ))}
        </div>
      ) : null}
      {suggested.length > 0 ? (
        <div className="mt-3 space-y-2">
          {suggested.map((step) => (
            <div className="border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700" key={step}>
              {step}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-600">
          Verification steps appear here after a diff preview or approved execution.
        </p>
      )}
      {longRunningTask.response?.task.truncated_test_results ? (
        <pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap border border-slate-200 bg-slate-50 p-3 text-xs leading-5 text-slate-800">
          {longRunningTask.response.task.truncated_test_results}
        </pre>
      ) : null}
    </section>
  );
}

function AdvancedDiagnostics({
  decisionMemory,
  diffVerification,
  finalOutput,
  onClearMemory,
  onRefreshTelemetry,
  telemetry,
}: {
  decisionMemory: DecisionMemoryEntry[];
  diffVerification: DiffVerificationState;
  finalOutput: FinalOutput | null;
  onClearMemory: () => void;
  onRefreshTelemetry: () => void;
  telemetry: TelemetryState;
}) {
  return (
    <details className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <summary className="cursor-pointer text-base font-semibold text-slate-950">
        Advanced
      </summary>
      <div className="mt-4 space-y-5">
        <TelemetryPanel onRefresh={onRefreshTelemetry} state={telemetry} />
        <DecisionMemoryPanel entries={decisionMemory} onClear={onClearMemory} />
        {finalOutput ? (
          <>
            {!finalOutput.coderAgentLocalDiff ? (
              <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
                <h2 className="text-base font-semibold text-slate-950">Prompt Packet Text</h2>
                <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-md border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-800">
                  {finalOutput.promptText}
                </pre>
              </section>
            ) : null}
            <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
              <h2 className="text-base font-semibold text-slate-950">Raw Decision Details</h2>
              <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-md border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-800">
                {finalOutput.decisionPayload}
              </pre>
            </section>
          </>
        ) : null}
        {diffVerification.preview ? (
          <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
            <h2 className="text-base font-semibold text-slate-950">Raw Diff Preview</h2>
            <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-md border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-800">
              {JSON.stringify(diffVerification.preview, null, 2)}
            </pre>
          </section>
        ) : null}
      </div>
    </details>
  );
}

function OutputWindow({
  approvalGate,
  conversationHistory,
  decisionMemory,
  diffVerification,
  files,
  finalOutput,
  inputText,
  isRunning,
  longRunningTask,
  logs,
  onRefreshTelemetry,
  onApprovalActionChange,
  onApprovalContentChange,
  onApprovalTargetChange,
  onApprovePreviewedAction,
  onClearHistory,
  onClearMemory,
  onDenyPreviewedAction,
  onDiffChange,
  onTrackedDiffSelect,
  onLongTaskCancel,
  onLongTaskDescriptionChange,
  onLongTaskPoll,
  onLongTaskStart,
  onInputChange,
  onFilesAdded,
  onPreviewApprovalGate,
  onPreviewDiffVerification,
  onRestoreHistoryEntry,
  onRunProxyFlow,
  onStartNewTask,
  onSubmit,
  telemetry,
  workflowStepFloor,
}: {
  approvalGate: ApprovalGateState;
  conversationHistory: CodingHistoryEntry[];
  decisionMemory: DecisionMemoryEntry[];
  diffVerification: DiffVerificationState;
  files: UploadedFile[];
  finalOutput: FinalOutput | null;
  inputText: string;
  isRunning: boolean;
  longRunningTask: LongRunningTaskState;
  logs: ProcessLog[];
  onRefreshTelemetry: () => void;
  onApprovalActionChange: (action: string) => void;
  onApprovalContentChange: (content: string) => void;
  onApprovalTargetChange: (target: string) => void;
  onApprovePreviewedAction: (event: MouseEvent<HTMLButtonElement>) => void;
  onClearHistory: () => void;
  onClearMemory: () => void;
  onDenyPreviewedAction: () => void;
  onDiffChange: (unifiedDiff: string) => void;
  onTrackedDiffSelect: (unifiedDiff: string) => void;
  onLongTaskCancel: () => void;
  onLongTaskDescriptionChange: (description: string) => void;
  onLongTaskPoll: () => void;
  onLongTaskStart: () => void;
  onInputChange: (value: string) => void;
  onFilesAdded: (files: UploadedFile[]) => void;
  onPreviewApprovalGate: () => void;
  onPreviewDiffVerification: () => void;
  onRestoreHistoryEntry: (entry: CodingHistoryEntry) => void;
  onRunProxyFlow: () => void;
  onStartNewTask: () => void;
  onSubmit: () => void;
  telemetry: TelemetryState;
  workflowStepFloor: number | null;
}) {
  const outputFingerprint = finalOutput?.decisionPayload ?? "pending";
  const [actionStatus, setActionStatus] = useState<{
    message: string;
    outputFingerprint: string;
  } | null>(null);
  const visibleActionStatus =
    actionStatus?.outputFingerprint === outputFingerprint ? actionStatus.message : null;

  async function handleRouteAction(action: RouteAction) {
    if (action.id === "proxy") {
      setActionStatus({
        message: "Running this task again with the live agent...",
        outputFingerprint,
      });
      onRunProxyFlow();
      return;
    }

    if (!finalOutput) {
      return;
    }

    try {
      await navigator.clipboard.writeText(
        buildClipboardPrompt(
          action,
          finalOutput.promptText,
          finalOutput.attachedFiles,
          finalOutput.selfCorrection,
        ),
      );
      setActionStatus({
        message: `${action.label}: copied the prompt to your clipboard.`,
        outputFingerprint,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Clipboard unavailable.";
      setActionStatus({
        message: `${action.label}: ${message}`,
        outputFingerprint,
      });
    }
  }

  const hasProposal =
    approvalGate.action.trim().length > 0 || approvalGate.target.trim().length > 0;
  const hasDiff =
    approvalGate.proposedDiff.trim().length > 0 ||
    diffVerification.unifiedDiff.trim().length > 0 ||
    Boolean(approvalGate.content.trim());
  const derivedStep = workflowStep({
    approvalGate,
    diffVerification,
    finalOutput,
    isRunning,
    longRunningTask,
  });
  const activeStep =
    workflowStepFloor != null ? Math.max(derivedStep, workflowStepFloor) : derivedStep;
  const stages = workflowStages(activeStep);

  return (
    <section className="flex min-h-0 flex-col bg-slate-100/80 p-4 sm:p-6">
      <div className="border-b border-slate-300 bg-white px-4 py-3 shadow-sm">
        <div className="text-sm font-semibold text-slate-950">
          Coding Workflow
        </div>
        <p className="mt-0.5 text-xs text-slate-600">
          One path from task description to plan, approval, execution, verification, and done.
        </p>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[16rem_1fr]">
        <WorkflowRail stages={stages} />
        <div className="min-h-0 overflow-y-auto p-4">
          <div className="space-y-5">
            <WorkflowStage
              description="Describe the task and submit it to the safe discovery pass."
              index={1}
              status={stages[0].status}
              title="Task Description"
            >
              <PromptInput
                files={files}
                inputText={inputText}
                isRunning={isRunning}
                onChange={onInputChange}
                onFilesAdded={onFilesAdded}
                onStartNewTask={onStartNewTask}
                onSubmit={onSubmit}
              />
            </WorkflowStage>

            <WorkflowStage
              description="The agent classifies the task, recalls prior decisions, and prepares a plan."
              index={2}
              status={stages[1].status}
              title="Research / Plan"
            >
              {finalOutput ? (
                <div className="space-y-4">
                  <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <h2 className="text-base font-semibold text-slate-950">
                          Agent Decision Summary
                        </h2>
                        <p className="mt-3 text-sm leading-6 text-slate-800">
                          {finalOutput.summary}
                        </p>
                      </div>
                      <WorkflowBadge tone="info">
                        {friendlyRouteName(finalOutput.decision.recommended_route)}
                      </WorkflowBadge>
                    </div>
                    {visibleActionStatus ? (
                      <div className="mt-3 border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-900">
                        {visibleActionStatus}
                      </div>
                    ) : null}
                  </section>
                  <SelfCorrectionPanel selfCorrection={finalOutput.selfCorrection} />
                  <ConversationHistoryPanel
                    entries={conversationHistory}
                    onClear={onClearHistory}
                    onRestore={onRestoreHistoryEntry}
                  />
                  <div className="grid gap-3 sm:grid-cols-2">
                    {routeActions.map((action) => {
                      const isRecommended =
                        action.id === routeActionForDecision(finalOutput.decision).id;
                      return (
                        <button
                          className={`border px-3 py-2 text-left text-sm hover:bg-slate-100 ${
                            isRecommended
                              ? "border-slate-900 bg-slate-900 text-white hover:bg-slate-800"
                              : "border-slate-300 bg-slate-50 text-slate-900"
                          }`}
                          disabled={isRunning && action.id === "proxy"}
                          key={action.id}
                          onClick={() => handleRouteAction(action)}
                          type="button"
                        >
                          <span className="block font-semibold">{action.label}</span>
                          <span
                            className={`mt-1 block text-xs ${
                              isRecommended ? "text-slate-200" : "text-slate-600"
                            }`}
                          >
                            {action.description}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <EmptyWorkflowMessage
                  text={
                    isRunning
                      ? "Discovery is running. The plan appears here when the agent finishes."
                      : "Submit a task to create the research and planning packet."
                  }
                />
              )}
            </WorkflowStage>

            <WorkflowStage
              description="Review the exact proposed target and diff before approval."
              index={3}
              status={stages[2].status}
              title="Proposal / Diff Preview"
            >
              {hasProposal || hasDiff ? (
                <div className="space-y-4">
                  <ProposalSummaryPanel gate={approvalGate} />
                  <DiffVerificationPanel
                    state={diffVerification}
                    onChange={onDiffChange}
                    onPreview={onPreviewDiffVerification}
                  />
                </div>
              ) : (
                <EmptyWorkflowMessage text="No proposed code change yet. The agent must produce a target and diff before approval." />
              )}
            </WorkflowStage>

            <WorkflowStage
              description="Approve only after the preview matches the change you want applied."
              index={4}
              status={stages[3].status}
              title="Approval Gate"
            >
              <ApprovalGatePanel
                gate={approvalGate}
                diffVerification={diffVerification}
                coderAgentLocalDiff={Boolean(finalOutput?.coderAgentLocalDiff)}
                onActionChange={onApprovalActionChange}
                onApprove={onApprovePreviewedAction}
                onContentChange={onApprovalContentChange}
                onDeny={onDenyPreviewedAction}
                onPreview={onPreviewApprovalGate}
                onTargetChange={onApprovalTargetChange}
              />
            </WorkflowStage>

            <WorkflowStage
              description="After approval, execution progress comes from the long-running task layer."
              index={5}
              sectionId="spirit-coding-workflow-execution"
              status={stages[4].status}
              title="Execution"
            >
              <LongRunningTaskPanel
                state={longRunningTask}
                onCancel={onLongTaskCancel}
                onDescriptionChange={onLongTaskDescriptionChange}
                onDiffSelect={onTrackedDiffSelect}
                onPoll={onLongTaskPoll}
                onStart={onLongTaskStart}
              />
            </WorkflowStage>

            <WorkflowStage
              description="Use the generated checks to validate lint, typecheck, sandbox, and browser behavior."
              index={6}
              status={stages[5].status}
              title="Verification / Tests"
            >
              <VerificationSummary
                diffVerification={diffVerification}
                execution={approvalGate.execution}
                longRunningTask={longRunningTask}
              />
            </WorkflowStage>

            <WorkflowStage
              description="Final activity summary and task completion state."
              index={7}
              status={stages[6].status}
              title="Status / Done"
            >
              <ProcessWindow logs={logs} />
              {approvalGate.execution?.ok ? (
                <div className="mt-4 border border-green-200 bg-green-50 px-3 py-2 text-sm font-semibold text-green-900">
                  Task Complete
                </div>
              ) : null}
            </WorkflowStage>

            <AdvancedDiagnostics
              decisionMemory={decisionMemory}
              diffVerification={diffVerification}
              finalOutput={finalOutput}
              onClearMemory={onClearMemory}
              onRefreshTelemetry={onRefreshTelemetry}
              telemetry={telemetry}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function ConversationHistoryPanel({
  entries,
  onClear,
  onRestore,
}: {
  entries: CodingHistoryEntry[];
  onClear: () => void;
  onRestore: (entry: CodingHistoryEntry) => void;
}) {
  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Recent Agent Runs</h2>
        {entries.length > 0 ? (
          <button
            className="border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-slate-100"
            onClick={onClear}
            type="button"
          >
            Clear history
          </button>
        ) : null}
      </div>

      {entries.length === 0 ? (
        <p className="mt-3 text-sm text-slate-600">
          Finished runs are saved here in this browser only.
        </p>
      ) : (
        <div className="mt-3 space-y-2">
          {entries.slice(0, 6).map((entry) => (
            <div
              className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm"
              key={entry.id}
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <div className="truncate font-semibold text-slate-950">
                    Run #{entry.runId}: {entry.task || "No prompt supplied."}
                  </div>
                  <div className="mt-1 text-xs text-slate-600">
                    {formatRunTimestamp(new Date(entry.completedAt))} | {entry.route} |{" "}
                    {entry.recommendation} | {entry.risk} | {entry.contextTurnCount} prior
                    turn{entry.contextTurnCount === 1 ? "" : "s"}
                  </div>
                  <p className="mt-2 line-clamp-2 text-slate-700">{entry.summary}</p>
                </div>
                <button
                  className="shrink-0 border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-slate-100"
                  onClick={() => onRestore(entry)}
                  type="button"
                >
                  Restore prompt
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function DecisionMemoryPanel({
  entries,
  onClear,
}: {
  entries: DecisionMemoryEntry[];
  onClear: () => void;
}) {
  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Decision Memory</h2>
        {entries.length > 0 ? (
          <button
            className="border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-slate-100"
            onClick={onClear}
            type="button"
          >
            Clear memory
          </button>
        ) : null}
      </div>

      {entries.length === 0 ? (
        <p className="mt-3 text-sm text-slate-600">
          After each finished run we store a short reminder of how the agent routed similar work.
        </p>
      ) : (
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {entries.slice(0, 6).map((entry) => (
            <div
              className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm"
              key={entry.id}
            >
              <div className="truncate font-semibold text-slate-950">
                {friendlyTaskName(entry.classification)} - {friendlyRouteName(entry.route)}
              </div>
              <div className="mt-1 text-xs text-slate-600">
                {entry.recommendation} | {entry.risk} | {entry.model}
              </div>
              <p className="mt-2 line-clamp-2 text-slate-700">
                {entry.task || "No prompt supplied."}
              </p>
              {entry.reasonCodes.length > 0 ? (
                <div className="mt-2 text-xs text-slate-500">
                  {entry.reasonCodes.slice(0, 3).join(", ")}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function SelfCorrectionPanel({
  selfCorrection,
}: {
  selfCorrection: SelfCorrectionState;
}) {
  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Self-Correction</h2>
        <div
          className={`border px-2 py-1 text-xs font-semibold ${
            selfCorrection.triggered
              ? "border-yellow-300 bg-yellow-50 text-yellow-900"
              : "border-green-300 bg-green-50 text-green-900"
          }`}
        >
          Confidence {formatConfidence(selfCorrection.confidence)}
        </div>
      </div>

      <div className="mt-3 grid gap-2">
        {selfCorrection.checks.map((check) => (
          <div
            className={`border px-3 py-2 text-sm ${
              check.passed
                ? "border-green-200 bg-green-50 text-green-950"
                : "border-yellow-200 bg-yellow-50 text-yellow-950"
            }`}
            key={check.id ?? check.question}
          >
            <div className="font-semibold">{check.question}</div>
            <div className="mt-1 text-slate-700">{check.answer}</div>
          </div>
        ))}
      </div>

      {selfCorrection.triggered ? (
        <div className="mt-3 space-y-3">
          <div className="border border-yellow-200 bg-yellow-50 px-3 py-2 text-sm text-yellow-950">
            The agent is not fully confident yet. The copied prompt includes a short note asking
            the next tool to double-check the plan before changing code.
          </div>
          <div className="space-y-2">
            {selfCorrection.reasons.map((reason) => (
              <div
                className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700"
                key={reason}
              >
                {reason}
              </div>
            ))}
          </div>
          <pre className="overflow-x-auto whitespace-pre-wrap border border-slate-300 bg-slate-50 p-3 text-sm leading-6 text-slate-800">
            {selfCorrection.refinedInstruction}
          </pre>
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-600">
          The quick check did not find anything urgent for this decision.
        </p>
      )}
    </section>
  );
}

function TelemetryPanel({
  onRefresh,
  state,
}: {
  onRefresh: () => void;
  state: TelemetryState;
}) {
  const routes = state.status?.available_routes ?? [];
  const tools = state.status?.enabled_tools ?? [];
  const bundles = state.status?.context_bundle_status?.bundles ?? [];
  const approvalCount =
    state.status?.approval_boundaries?.requires_human_approval?.length ?? 0;

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-950">
            Telemetry Snapshot
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Read-only status from the Source proxy.
          </p>
        </div>
        <button
          className="border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-400"
          disabled={state.isChecking}
          onClick={onRefresh}
          type="button"
        >
          {state.isChecking ? "Checking" : "Refresh telemetry"}
        </button>
      </div>

      {state.error ? (
        <div className="mt-3 border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
          {state.error}
        </div>
      ) : null}

      {state.status ? (
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <TelemetryStat
            label="Service"
            value={`${state.status.service ?? "Source proxy"} ${
              state.status.manifest_version ?? ""
            }`.trim()}
          />
          <TelemetryStat
            label="Windows bridge"
            value={state.status.windows_bridge_status?.status ?? "not reported"}
          />
          <TelemetryStat
            label="Available routes"
            value={routes.length > 0 ? routes.map(friendlyTelemetryRoute).join(", ") : "none"}
          />
          <TelemetryStat
            label="Enabled tools"
            value={`${tools.length} reported`}
          />
          <TelemetryStat
            label="Approval checks"
            value={`${approvalCount} rule${approvalCount === 1 ? "" : "s"} require approval`}
          />
          <TelemetryStat
            label="Context bundles"
            value={
              bundles.length > 0
                ? bundles.map((bundle) => `${bundle.name ?? "bundle"}: ${bundle.status ?? "unknown"}`).join(", ")
                : "not reported"
            }
          />
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-600">
          Telemetry has not loaded yet. Refresh to check the Source proxy status.
        </p>
      )}

      {state.lastCheckedAt ? (
        <div className="mt-3 text-xs text-slate-500">
          Last checked {formatRunTimestamp(new Date(state.lastCheckedAt))}.
        </div>
      ) : null}
    </section>
  );
}

function TelemetryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-slate-900">{value}</div>
    </div>
  );
}

function DiffVerificationPanel({
  state,
  onChange,
  onPreview,
}: {
  state: DiffVerificationState;
  onChange: (unifiedDiff: string) => void;
  onPreview: () => void;
}) {
  const status = state.preview?.status ?? "not previewed";
  const isBlocked = state.preview?.status === "blocked";

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Check a Code Change</h2>
        <div
          className={`border px-2 py-1 text-xs font-semibold ${
            isBlocked
              ? "border-red-300 bg-red-50 text-red-900"
              : state.preview
                ? "border-green-300 bg-green-50 text-green-900"
                : "border-slate-300 bg-slate-50 text-slate-700"
          }`}
        >
          {status}
        </div>
      </div>

      <textarea
        className="mt-3 h-36 w-full resize-y border border-slate-300 bg-white p-3 font-mono text-sm text-slate-900 outline-none focus:border-slate-600"
        onChange={(event) => onChange(event.target.value)}
        placeholder="Paste a proposed code change here for a read-only safety check..."
        value={state.unifiedDiff}
      />

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          className="border border-slate-900 bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:border-slate-400 disabled:bg-slate-400"
          disabled={state.isChecking || state.unifiedDiff.trim().length === 0}
          onClick={onPreview}
          type="button"
        >
          {state.isChecking ? "Checking" : "Preview diff"}
        </button>
        {state.preview ? (
          <div className="text-sm text-slate-600">
            Safety level: {state.preview.risk ?? "unknown"} | Would change files:{" "}
            {state.preview.would_apply_diff ? "yes" : "no"} | Would run commands:{" "}
            {state.preview.would_execute ? "yes" : "no"}
          </div>
        ) : null}
      </div>

      {state.error ? (
        <div className="mt-3 border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
          {state.error}
        </div>
      ) : null}

      {state.preview ? (
        <div className="mt-3 space-y-3">
          {state.preview.blocked_reasons && state.preview.blocked_reasons.length > 0 ? (
            <div className="space-y-2">
              {state.preview.blocked_reasons.map((reason) => (
                <div
                  className="border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900"
                  key={`${reason.path}-${reason.reason_code}`}
                >
                  {reason.path}: {reason.reason_code}
                </div>
              ))}
            </div>
          ) : null}

          {state.preview.self_correction?.triggered ? (
            <div className="space-y-2 border border-yellow-300 bg-yellow-50 p-3">
              <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                <h3 className="text-sm font-semibold text-yellow-950">
                  Self-Correction
                </h3>
                <span className="border border-yellow-400 bg-white px-2 py-1 text-xs font-semibold text-yellow-900">
                  {state.preview.self_correction.severity ?? "review"}
                </span>
              </div>
              <div className="text-sm text-yellow-950">
                {state.preview.self_correction.safer_next_action}
              </div>
              {state.preview.self_correction.reasons &&
              state.preview.self_correction.reasons.length > 0 ? (
                <div className="space-y-1">
                  {state.preview.self_correction.reasons.map((reason) => (
                    <div
                      className="border border-yellow-200 bg-white px-3 py-2 text-sm text-slate-800"
                      key={reason}
                    >
                      {reason}
                    </div>
                  ))}
                </div>
              ) : null}
              {state.preview.self_correction.retry_prompt ? (
                <pre className="overflow-x-auto whitespace-pre-wrap border border-yellow-200 bg-white p-3 text-sm leading-6 text-slate-800">
                  {state.preview.self_correction.retry_prompt}
                </pre>
              ) : null}
            </div>
          ) : null}

          {state.preview.changed_files && state.preview.changed_files.length > 0 ? (
            <div className="grid gap-2 md:grid-cols-2">
              {state.preview.changed_files.map((file) => (
                <div
                  className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm"
                  key={file.path}
                >
                  <div className="truncate font-semibold text-slate-950">
                    {file.path}
                  </div>
                  <div className="text-slate-600">
                    {file.change_type ?? "modified"} | +{file.added_lines ?? 0} -{file.removed_lines ?? 0}
                  </div>
                  {file.risk_flags && file.risk_flags.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {file.risk_flags.map((flag) => (
                        <span
                          className="border border-yellow-300 bg-yellow-50 px-2 py-0.5 text-xs text-yellow-900"
                          key={flag}
                        >
                          {flag}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          ) : null}

          {state.preview.suggested_commands &&
          state.preview.suggested_commands.length > 0 ? (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-950">
                Suggested Checks to Run
              </h3>
              {state.preview.suggested_commands.map((item) => (
                <div
                  className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm"
                  key={`${item.command.join(" ")}-${item.reason}`}
                >
                  <code className="font-mono text-slate-900">
                    {item.command.join(" ")}
                  </code>
                  <div className="mt-1 text-slate-600">{item.reason}</div>
                </div>
              ))}
            </div>
          ) : null}

          {state.preview.verification_plan &&
          state.preview.verification_plan.length > 0 ? (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-950">
                How to Verify
              </h3>
              {state.preview.verification_plan.map((step) => (
                <div
                  className="border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
                  key={step}
                >
                  {step}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function LongRunningTaskPanel({
  state,
  onCancel,
  onDescriptionChange,
  onDiffSelect,
  onPoll,
  onStart,
}: {
  state: LongRunningTaskState;
  onCancel: () => void;
  onDescriptionChange: (description: string) => void;
  onDiffSelect: (unifiedDiff: string) => void;
  onPoll: () => void;
  onStart: () => void;
}) {
  const task = state.response?.task;
  const status = task?.status ?? "not started";
  const canPoll = Boolean(task) && !isTerminalLongTaskStatus(task?.status);
  const canCancel = Boolean(task) && !isTerminalLongTaskStatus(task?.status);
  const currentRole = normalizeLongTaskRole(task?.current_agent_role);
  const openDiffs = task?.open_diffs ?? [];

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Long Task Tracker</h2>
        <div
          className={`border px-2 py-1 text-xs font-semibold ${
            status === "cancelled"
              ? "border-red-300 bg-red-50 text-red-900"
              : status === "failed_needs_human"
                ? "border-red-300 bg-red-50 text-red-900"
              : status === "completed"
                ? "border-green-300 bg-green-50 text-green-900"
                : task
                  ? "border-yellow-300 bg-yellow-50 text-yellow-900"
                  : "border-slate-300 bg-slate-50 text-slate-700"
          }`}
        >
          {status}
        </div>
      </div>

      <textarea
        className="mt-3 h-24 w-full resize-y border border-slate-300 bg-white p-3 text-sm text-slate-900 outline-none focus:border-slate-600"
        onChange={(event) => onDescriptionChange(event.target.value)}
        value={state.description}
      />

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          className="border border-slate-900 bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:border-slate-400 disabled:bg-slate-400"
          disabled={state.isChecking || state.description.trim().length === 0}
          onClick={onStart}
          type="button"
        >
          {state.isChecking ? "Working" : "Start tracked task"}
        </button>
        <button
          className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:text-slate-400"
          disabled={state.isChecking || !canPoll}
          onClick={onPoll}
          type="button"
        >
          Check status
        </button>
        <button
          className="border border-red-700 bg-white px-3 py-2 text-sm font-semibold text-red-800 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
          disabled={state.isChecking || !canCancel}
          onClick={onCancel}
          type="button"
        >
          Cancel
        </button>
      </div>

      {state.error ? (
        <div className="mt-3 border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
          {state.error}
        </div>
      ) : null}

      {task ? (
        <div className="mt-3 space-y-3">
          <div className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
            Progress: {task.progress ?? 0}% | Would run commands:{" "}
            {task.would_execute ? "yes" : "no"} | Would write files:{" "}
            {task.writes_allowed ? "yes" : "no"}
          </div>
          <div className="grid gap-3 border border-slate-300 bg-white px-3 py-3 text-sm text-slate-800 md:grid-cols-[1fr_auto]">
            <div className="grid grid-cols-3 border border-slate-300 text-center text-xs font-semibold">
              {(["architect", "coder", "debugger"] as const).map((role) => (
                <div
                  className={`px-2 py-2 ${
                    currentRole === role
                      ? "bg-slate-900 text-white"
                      : "bg-slate-50 text-slate-600"
                  }`}
                  key={role}
                >
                  {longTaskRoleLabel(role)}
                </div>
              ))}
            </div>
            <div className="border border-slate-300 bg-slate-50 px-3 py-2 text-center text-xs font-semibold text-slate-700">
              Cycle {task.cycle_count ?? 0}
            </div>
          </div>
          <div className="h-2 border border-slate-300 bg-white">
            <div
              className="h-full bg-slate-900"
              style={{ width: `${Math.min(100, Math.max(0, task.progress ?? 0))}%` }}
            />
          </div>
          {task.next_action ? (
            <div className="border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700">
              {task.next_action}
            </div>
          ) : null}
          {task.steps && task.steps.length > 0 ? (
            <div className="space-y-2">
              {task.steps.map((step, index) => (
                <div
                  className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700"
                  key={`${step}-${index}`}
                >
                  {step}
                </div>
              ))}
            </div>
          ) : null}
          {openDiffs.length > 0 ? (
            <div className="space-y-2">
              {openDiffs.map((diff, index) => {
                const changedFiles = diff.changed_files ?? [];
                const diffText = typeof diff.diff === "string" ? diff.diff : "";
                return (
                  <div
                    className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700"
                    key={`${diff.status ?? "diff"}-${index}`}
                  >
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <div className="font-semibold text-slate-950">
                          Diff {index + 1}: {diff.status ?? "pending"}
                        </div>
                        <div className="mt-1 text-xs text-slate-600">
                          Risk {diff.risk ?? "unknown"} | {changedFiles.length} file
                          {changedFiles.length === 1 ? "" : "s"}
                        </div>
                      </div>
                      <button
                        className="border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-900 disabled:cursor-not-allowed disabled:text-slate-400"
                        disabled={!diffText}
                        onClick={() => onDiffSelect(diffText)}
                        type="button"
                      >
                        Preview diff
                      </button>
                    </div>
                    {changedFiles.length > 0 ? (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {changedFiles.slice(0, 6).map((file, fileIndex) => (
                          <code
                            className="border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700"
                            key={`${file.path ?? "file"}-${fileIndex}`}
                          >
                            {file.path ?? "unknown"}
                          </code>
                        ))}
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          ) : null}
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-600">
          Starts as read-only tracking. After Approval Gate confirmation, this is the
          execution progress surface for the approved diff.
        </p>
      )}
    </section>
  );
}

function isTerminalLongTaskStatus(status?: string) {
  return status === "cancelled" || status === "completed" || status === "failed_needs_human";
}

function normalizeLongTaskRole(role?: string) {
  if (role === "architect" || role === "coder" || role === "debugger") {
    return role;
  }
  return "architect";
}

function longTaskRoleLabel(role: "architect" | "coder" | "debugger") {
  if (role === "architect") {
    return "Architect";
  }
  if (role === "coder") {
    return "Coder";
  }
  return "Debugger";
}

function ApprovalGatePanel({
  gate,
  diffVerification,
  coderAgentLocalDiff,
  onActionChange,
  onApprove,
  onContentChange,
  onDeny,
  onPreview,
  onTargetChange,
}: {
  gate: ApprovalGateState;
  diffVerification: DiffVerificationState;
  coderAgentLocalDiff: boolean;
  onActionChange: (action: string) => void;
  onApprove: (event: MouseEvent<HTMLButtonElement>) => void;
  onContentChange: (content: string) => void;
  onDeny: () => void;
  onPreview: () => void;
  onTargetChange: (target: string) => void;
}) {
  const isBlocked = gate.preview?.decision === "blocked";
  const limits = diffVerification.preview?.limits;
  const fileWritesAllowed =
    typeof limits === "object" &&
    limits !== null &&
    (limits as Record<string, unknown>).file_writes_allowed === true;
  const hasDiffPayload =
    gate.proposedDiff.trim().length > 0 || diffVerification.unifiedDiff.trim().length > 0;
  const hasContentPayload = gate.content.trim().length > 0;
  const canExecuteApprovedAction = hasDiffPayload || hasContentPayload;
  // A preview may require approval before a diff exists; block execution until it does.
  const fileMutationIntent =
    gate.target.trim().length > 0 &&
    /\b(modify|create|implement|apply|update|add)\b/i.test(gate.action);
  const canApprove =
    Boolean(gate.preview) &&
    !isBlocked &&
    (gate.preview?.requires_human_approval === true ||
      (fileWritesAllowed && coderAgentLocalDiff && hasDiffPayload)) &&
    (!fileMutationIntent || canExecuteApprovedAction);
  const hasProposedAction = gate.action.trim().length > 0 || gate.target.trim().length > 0;
  const exactCommand = formatExactApprovalCommand(gate.action, gate.target);

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Approval Gate</h2>
        <div
          className={`border px-2 py-1 text-xs font-semibold ${
            isBlocked
              ? "border-red-300 bg-red-50 text-red-900"
              : canApprove
                ? "border-yellow-300 bg-yellow-50 text-yellow-900"
                : "border-slate-300 bg-slate-50 text-slate-700"
          }`}
        >
          {hasProposedAction ? (gate.preview?.decision ?? "ready") : "waiting"}
        </div>
      </div>

      {!hasProposedAction ? (
        <div className="mt-3 border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
          Waiting for a specific proposed file change or command from the agent.
        </div>
      ) : null}

      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <label className="text-sm font-semibold text-slate-700">
          What the agent wants to do
          <input
            className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm font-normal text-slate-900 outline-none focus:border-slate-600"
            onChange={(event) => onActionChange(event.target.value)}
            value={gate.action}
          />
        </label>
        <label className="text-sm font-semibold text-slate-700">
          Where it would happen
          <input
            className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm font-normal text-slate-900 outline-none focus:border-slate-600"
            onChange={(event) => onTargetChange(event.target.value)}
            value={gate.target}
          />
        </label>
      </div>

      <div className="mt-3 border border-slate-300 bg-slate-50 px-3 py-2 text-sm">
        <div className="font-semibold text-slate-950">Exact command or action</div>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap border border-slate-200 bg-white p-3 font-mono text-sm leading-6 text-slate-800">
          {exactCommand}
        </pre>
        <p className="mt-2 text-slate-600">
          This preview explains what will be reviewed. Approve applies only the reviewed
          diff or explicit file content through the protected execution layer.
        </p>
      </div>

      {gate.content ? (
        <label className="mt-3 block text-sm font-semibold text-slate-700">
          Approved file content
          <textarea
            className="mt-1 h-32 w-full resize-y border border-slate-300 bg-white p-3 font-mono text-sm font-normal text-slate-900 outline-none focus:border-slate-600"
            onChange={(event) => onContentChange(event.target.value)}
            value={gate.content}
          />
        </label>
      ) : null}

      {gate.proposedDiff ? (
        <div className="mt-3 border border-slate-300 bg-slate-50 px-3 py-2 text-sm">
          <div className="font-semibold text-slate-950">Approved diff payload</div>
          <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap border border-slate-200 bg-white p-3 font-mono text-xs leading-5 text-slate-800">
            {gate.proposedDiff}
          </pre>
        </div>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          className="border border-slate-900 bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:border-slate-400 disabled:bg-slate-400"
          disabled={gate.isChecking || !hasProposedAction}
          onClick={onPreview}
          type="button"
        >
          {gate.isChecking ? "Checking" : "Check action"}
        </button>
        <button
          className="border border-green-700 bg-green-700 px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:border-slate-300 disabled:bg-slate-300"
          disabled={!canApprove}
          onClick={(event) => {
            event.preventDefault();
            onApprove(event);
          }}
          type="button"
        >
          Approve
        </button>
        <button
          className="border border-red-700 bg-white px-3 py-2 text-sm font-semibold text-red-800 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
          disabled={!gate.preview || isBlocked}
          onClick={onDeny}
          type="button"
        >
          Deny
        </button>
      </div>

      {gate.error ? (
        <div className="mt-3 border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
          {gate.error}
        </div>
      ) : null}

      {gate.preview ? (
        <div className="mt-3 space-y-2">
          <div className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
            {gate.preview.safety_message ??
              gate.preview.next_step ??
              "No safety message returned."}
          </div>
          {gate.preview.reason_codes && gate.preview.reason_codes.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {gate.preview.reason_codes.map((reason) => (
                <span
                  className="border border-slate-300 bg-white px-2 py-1 text-xs text-slate-600"
                  key={reason}
                >
                  {reason}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      {gate.execution ? (
        <div
          className={`mt-3 border px-3 py-2 text-sm ${
            gate.execution.ok
              ? "border-green-200 bg-green-50 text-green-900"
              : "border-red-200 bg-red-50 text-red-900"
          }`}
        >
          {gate.execution.ok
            ? `Execution layer applied ${gate.execution.relativeFilePath ?? gate.target}.`
            : gate.execution.message ?? "Execution layer rejected the approved action."}
        </div>
      ) : null}

      {gate.approvedAt ? (
        <div className="mt-3 border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-900">
          Approved {formatRunTimestamp(new Date(gate.approvedAt))}. The protected tool
          layer handled the approved action.
        </div>
      ) : null}

      {gate.deniedAt ? (
        <div className="mt-3 border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
          Denied {formatRunTimestamp(new Date(gate.deniedAt))}. The action should not
          be retried without changing scope.
        </div>
      ) : null}
    </section>
  );
}

function PromptInput({
  files,
  inputText,
  isRunning,
  onChange,
  onFilesAdded,
  onStartNewTask,
  onSubmit,
}: {
  files: UploadedFile[];
  inputText: string;
  isRunning: boolean;
  onChange: (value: string) => void;
  onFilesAdded: (files: UploadedFile[]) => void;
  onStartNewTask: () => void;
  onSubmit: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  function addFiles(fileList: FileList | null) {
    if (!fileList) {
      return;
    }

    onFilesAdded(
      Array.from(fileList)
        .filter((file) => acceptedFileExtensions.has(fileExtension(file.name)))
        .map((file) => ({
          id: `${file.name}-${file.size}-${file.lastModified}`,
          lastModified: file.lastModified,
          name: file.name,
          size: file.size,
          type: file.type,
        })),
    );
  }

  return (
    <footer className="border-t border-slate-300 bg-slate-100 p-4">
      <div
        className="mb-3 border border-dashed border-slate-400 bg-white p-3 text-sm text-slate-700"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          addFiles(event.dataTransfer.files);
        }}
      >
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="font-semibold text-slate-950">Attach files (optional)</div>
            <div className="text-slate-600">
              Drop files here or pick images, video, XML, JSON, TypeScript, Python, CSS, HTML, or
              plain text.
            </div>
          </div>

          <button
            className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-100"
            onClick={() => fileInputRef.current?.click()}
            type="button"
          >
            Choose files
          </button>
        </div>

        <input
          accept={acceptedFileTypes}
          className="hidden"
          multiple
          onChange={(event) => addFiles(event.target.files)}
          ref={fileInputRef}
          type="file"
        />

        {files.length > 0 ? (
          <ul className="mt-3 grid gap-2 md:grid-cols-2">
            {files.map((file) => (
              <li
                className="flex items-center justify-between gap-3 border border-slate-200 bg-slate-50 px-3 py-2"
                key={file.id}
              >
                <span className="min-w-0 truncate">{file.name}</span>
                <span className="shrink-0 text-slate-500">{formatFileSize(file.size)}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 md:flex-row md:items-stretch">
        <textarea
          className="h-24 min-h-20 flex-1 resize-y border border-slate-300 bg-white p-3 text-sm outline-none focus:border-slate-600"
          onChange={(event) => onChange(event.target.value)}
          placeholder="Describe the coding task you want help with..."
          value={inputText}
        />

        <div className="flex flex-col gap-2 md:w-40">
          <button
            className="border border-slate-900 bg-slate-900 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:border-slate-400 disabled:bg-slate-400"
            disabled={isRunning}
            onClick={onSubmit}
            type="button"
          >
            {isRunning ? "Working..." : "Submit"}
          </button>
          <button
            className="border border-slate-400 bg-white px-3 py-2 text-xs font-semibold text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
            disabled={isRunning}
            onClick={() => onStartNewTask()}
            type="button"
          >
            Start new task
          </button>
          <p className="text-[11px] leading-snug text-slate-500">
            Clears approval state and activity log. Use after you are done with the current
            run.
          </p>
        </div>
      </div>
    </footer>
  );
}

function logLevelClassName(level: ProcessLog["level"]) {
  if (level === "success") {
    return "text-green-300";
  }

  if (level === "warning") {
    return "text-yellow-300";
  }

  return "text-cyan-300";
}

function modelFromDecision(decision: ProxyRouteDecisionResponse) {
  return (
    decision.model ??
    decision.recommended_model ??
    decision.primary_model ??
    decision.target_model_hint ??
    "not returned"
  );
}

async function callProxyRouteDecision({
  activeTaskId,
  attachedFiles,
  currentAgentRole,
  memoryEntries,
  priorTurns,
  task,
}: {
  activeTaskId?: string;
  attachedFiles: UploadedFile[];
  currentAgentRole?: string;
  memoryEntries: DecisionMemoryEntry[];
  priorTurns: CodingHistoryEntry[];
  task: string;
}): Promise<ProxyRouteDecisionResponse> {
  const hints = inferTaskHints(task, attachedFiles);
  const contextTokens = estimateTextTokens(
    formatProxyMemoryContext(priorTurns, memoryEntries),
  );
  const response = await fetch("/v1/decisions/route", {
    body: JSON.stringify({
      ...hints,
      attached_files: filesForProxy(attachedFiles),
      active_task_id: activeTaskId,
      conversation_context: historyForProxy(priorTurns),
      current_agent_role: currentAgentRole,
      decision_memory: decisionMemoryForProxy(memoryEntries),
      context_tokens: contextTokens,
      task: task || "No prompt supplied.",
    }),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });

  const payload = await readJsonResponse(response, "Action preview");

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "error" in payload &&
      typeof payload.error === "string"
        ? payload.error
        : `Route decision failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload as ProxyRouteDecisionResponse;
}

function buildMockDecision(task: string): ProxyRouteDecisionResponse {
  const normalizedTask = task || "No prompt supplied.";
  const estimatedTokens = Math.max(1, Math.round(normalizedTask.length / 4));

  return {
    task_classification: "mock_coding_test",
    recommended_route: "local_route",
    reason_codes: ["feature_flag_disabled", "mock_fallback"],
    risk_tier: "low",
    context_estimate: {
      estimated_task_tokens: estimatedTokens,
      total_estimated_tokens: estimatedTokens,
    },
    next_prompt_action: "mock_prompt_packet",
    research_recommended: false,
    research_sources: [],
  };
}

function buildMockPromptPacket(task: string): PromptPacketResponse {
  const normalizedTask = task || "No prompt supplied.";

  return {
    prompt_text: [
      "# Mock Source Prompt Packet",
      "",
      "Model: mock",
      "",
      "## Task",
      normalizedTask,
      "",
      "## Constraints",
      "- This is a mock fallback because SPIRIT_CODING_USE_PROXY is off.",
      "- No live proxy, research, or prompt-packet endpoint was called.",
      "",
      "## Requested Output",
      "- Confirm the coding page still works without the proxy flag.",
    ].join("\n"),
    requests_for_more_information: ["Enable SPIRIT_CODING_USE_PROXY=true for live proxy testing."],
    research_sources: [],
  };
}

async function callProxyResearchPreview({
  activeTaskId,
  attachedFiles,
  currentAgentRole,
  memoryEntries,
  priorTurns,
  task,
}: {
  activeTaskId?: string;
  attachedFiles: UploadedFile[];
  currentAgentRole?: string;
  memoryEntries: DecisionMemoryEntry[];
  priorTurns: CodingHistoryEntry[];
  task: string;
}): Promise<ProxyRouteDecisionResponse> {
  const hints = inferTaskHints(task, attachedFiles);
  const contextTokens = estimateTextTokens(
    formatProxyMemoryContext(priorTurns, memoryEntries),
  );
  const response = await fetch("/v1/decisions/route", {
    body: JSON.stringify({
      ...hints,
      attached_files: filesForProxy(attachedFiles),
      active_task_id: activeTaskId,
      conversation_context: historyForProxy(priorTurns),
      current_agent_role: currentAgentRole,
      decision_memory: decisionMemoryForProxy(memoryEntries),
      context_tokens: contextTokens,
      task: task || "No prompt supplied.",
      research_recommended: true,
    }),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });

  const payload: unknown = await response.json();

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "error" in payload &&
      typeof payload.error === "string"
        ? payload.error
        : `Research preview failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload as ProxyRouteDecisionResponse;
}

async function callProxyPromptPacket({
  activeTaskId,
  attachedFiles,
  currentAgentRole,
  memoryEntries,
  priorTurns,
  researchSources,
  task,
}: {
  activeTaskId?: string;
  attachedFiles: UploadedFile[];
  currentAgentRole?: string;
  memoryEntries: DecisionMemoryEntry[];
  priorTurns: CodingHistoryEntry[];
  researchSources: ResearchSource[];
  task: string;
}): Promise<PromptPacketResponse> {
  const hints = inferTaskHints(task, attachedFiles);
  const proxyMemoryContext = formatProxyMemoryContext(priorTurns, memoryEntries);
  const response = await fetch("/v1/decisions/prompt-packet", {
    body: JSON.stringify({
      ...hints,
      attached_files: filesForProxy(attachedFiles),
      active_task_id: activeTaskId,
      conversation_context: historyForProxy(priorTurns),
      current_agent_role: currentAgentRole,
      decision_memory: decisionMemoryForProxy(memoryEntries),
      context_tokens: estimateTextTokens(proxyMemoryContext),
      task: task || "No prompt supplied.",
      needs_current_info: hints.needs_current_info,
      relevant_context: formatRelevantContext(
        researchSources,
        attachedFiles,
        priorTurns,
        memoryEntries,
      ),
    }),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });

  const payload: unknown = await response.json();

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "error" in payload &&
      typeof payload.error === "string"
        ? payload.error
        : `Prompt packet failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload as PromptPacketResponse;
}

async function callDiffVerificationPreview(
  unifiedDiff: string,
  options?: { routeType?: string; nextPromptAction?: string },
): Promise<DiffVerificationPreviewResponse> {
  const body: Record<string, unknown> = { unified_diff: unifiedDiff };
  const routeType = options?.routeType;
  if (routeType && routeType !== "not run" && routeType !== "pending") {
    body.route_type = routeType;
  }
  const nextPromptAction = options?.nextPromptAction?.trim();
  if (nextPromptAction) {
    body.next_prompt_action = nextPromptAction;
  }
  const response = await fetch("/v1/verification/diff-preview", {
    body: JSON.stringify(body),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });

  const payload = await readJsonResponse(response, "Diff verification preview");

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(
        "Diff verification route was not found by Next.js. Restart the dev server so the new /v1/verification/diff-preview route is loaded.",
      );
    }

    const message =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof payload.detail === "object" &&
      payload.detail !== null &&
      "error" in payload.detail &&
      typeof payload.detail.error === "string"
        ? payload.detail.error
        : `Diff verification preview failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload as DiffVerificationPreviewResponse;
}

async function callLongRunningTaskCreate(
  description: string,
): Promise<LongRunningTaskResponse> {
  const response = await fetch("/v1/tasks/long-running", {
    body: JSON.stringify({ description }),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });

  return parseLongRunningTaskResponse(response, "Long-running task create");
}

async function callLongRunningTaskStatus(
  taskId: string,
): Promise<LongRunningTaskResponse> {
  const response = await fetch(`/v1/tasks/long-running/${encodeURIComponent(taskId)}`, {
    method: "GET",
  });

  return parseLongRunningTaskResponse(response, "Long-running task status");
}

async function callLongRunningTaskCancel(
  taskId: string,
): Promise<LongRunningTaskResponse> {
  const response = await fetch(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/cancel`,
    {
      method: "POST",
    },
  );

  return parseLongRunningTaskResponse(response, "Long-running task cancel");
}

async function callSourceTelemetry(): Promise<SourceTelemetryResponse> {
  const response = await fetch("/v1/self/status", {
    method: "GET",
  });
  const payload = await readJsonResponse(response, "Source telemetry");

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "error" in payload &&
      typeof payload.error === "string"
        ? payload.error
        : `Source telemetry failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload as SourceTelemetryResponse;
}

async function parseLongRunningTaskResponse(
  response: Response,
  label: string,
): Promise<LongRunningTaskResponse> {
  const payload = await readJsonResponse(response, label);

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof payload.detail === "object" &&
      payload.detail !== null &&
      "error" in payload.detail &&
      typeof payload.detail.error === "string"
        ? payload.detail.error
        : `${label} failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload as LongRunningTaskResponse;
}

function looksLikeUnifiedDiff(value: string) {
  const trimmed = value.trim();
  return trimmed.includes("diff --git ") || trimmed.includes("\n@@ ");
}

function normalizeDiffVerificationPreview(
  preview: DiffVerificationPreviewResponse,
): DiffVerificationPreviewResponse {
  if (preview.self_correction) {
    return preview;
  }

  const triggered =
    preview.status === "blocked" ||
    preview.risk === "high" ||
    preview.risk === "medium";
  if (!triggered) {
    return preview;
  }

  const reasons =
    preview.blocked_reasons?.map(
      (reason) => `${reason.path} was blocked for ${reason.reason_code}.`,
    ) ??
    preview.changed_files
      ?.filter((file) => file.risk_flags && file.risk_flags.length > 0)
      .map((file) => `${file.path} has risk flags: ${file.risk_flags?.join(", ")}.`) ??
    [];
  const saferNextAction =
    preview.status === "blocked"
      ? "Ask the next agent to regenerate the patch without blocked paths or secret-shaped files."
      : preview.risk === "high"
        ? "Ask for a smaller patch or explicit approval before touching high-impact files."
        : "Split the diff into smaller reviewable patches before applying.";

  return {
    ...preview,
    self_correction: {
      reasons,
      retry_prompt: [
        "Revise the proposed diff before implementation.",
        `Current status: ${preview.status ?? "unknown"}`,
        `Current risk: ${preview.risk ?? "unknown"}`,
        "Reasons:",
        ...reasons.map((reason) => `- ${reason}`),
        "Return a smaller unified diff that avoids blocked paths, preserves existing behavior, and lists the tests to run.",
      ].join("\n"),
      safer_next_action: saferNextAction,
      severity: preview.status === "blocked" ? "blocked" : (preview.risk ?? "review"),
      triggered: true,
    },
  };
}

async function callActionPreview({
  action,
  routeType,
  target,
}: {
  action: string;
  routeType: string;
  target: string;
}): Promise<ApprovalPreviewResponse> {
  const response = await fetch("/v1/actions/preview", {
    body: JSON.stringify({
      action: action || "preview action",
      route_type: routeType === "not run" ? undefined : routeType,
      target: target || undefined,
    }),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });

  const payload: unknown = await response.json();

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "error" in payload &&
      typeof payload.error === "string"
        ? payload.error
        : `Action preview failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload as ApprovalPreviewResponse;
}

function extractFastApiErrorMessage(payload: unknown): string | undefined {
  if (typeof payload !== "object" || payload === null) {
    return undefined;
  }
  const record = payload as Record<string, unknown>;
  if (typeof record.message === "string") {
    return record.message;
  }
  if (typeof record.error === "string") {
    return record.error;
  }
  const detail = record.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (typeof detail === "object" && detail !== null) {
    const d = detail as Record<string, unknown>;
    if (typeof d.error === "string" && typeof d.reason_code === "string") {
      return `${d.error} (${d.reason_code})`;
    }
    if (typeof d.error === "string") {
      return d.error;
    }
    if (typeof d.message === "string") {
      return d.message;
    }
  }
  return undefined;
}

async function callApprovedActionExecute({
  action,
  approvedDiff,
  content,
  target,
  taskId,
}: {
  action: string;
  approvedDiff?: string;
  content?: string;
  target: string;
  taskId?: string;
}): Promise<ApprovedActionExecutionResponse> {
  const response = await fetch("/v1/actions/execute-approved", {
    body: JSON.stringify({
      action,
      approved: true,
      approved_diff: approvedDiff,
      content,
      target,
      task_id: taskId,
    }),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });

  const payload = await readJsonResponse(response, "Approved action execution");
  if (!response.ok) {
    const extracted = extractFastApiErrorMessage(payload);
    const message =
      extracted ??
      `Approved action execution failed with status ${response.status}.`;
    throw new Error(message);
  }

  const record = payload as Record<string, unknown>;
  if ("execution" in record && "task" in record) {
    const execution = (record.execution ?? {}) as Record<string, unknown>;
    return {
      ...(execution as ApprovedActionExecutionResponse),
      ok: true,
      task: record.task as LongRunningTaskPayload,
      target,
    };
  }

  return payload as ApprovedActionExecutionResponse;
}

function normalizeApprovalPreview({
  action,
  preview,
  target,
}: {
  action: string;
  preview: ApprovalPreviewResponse;
  target: string;
}): ApprovalPreviewResponse {
  if (
    preview.decision !== "preview_only" ||
    !looksLikeCommandAction(`${action}\n${target}`)
  ) {
    return preview;
  }

  return {
    ...preview,
    decision: "requires_human_approval",
    next_step: "Approve or deny before allowing this command-shaped action.",
    reason_codes: [
      ...(preview.reason_codes ?? []).filter((reason) => reason !== "read_only_preview"),
      "implementation_or_terminal_action",
      "client_command_shape_detected",
    ],
    requires_human_approval: true,
    safety_message:
      "This looks like a terminal command. Human approval is required before any sandbox/tool layer may execute it.",
    would_execute: false,
  };
}

function looksLikeCommandAction(value: string) {
  const normalized = value.toLowerCase();
  return [
    "npm run",
    "pnpm ",
    "yarn ",
    "pytest",
    "python -m",
    "node ",
    "bash ",
    "sh ",
    "curl ",
    "git ",
    "terminal",
    "shell",
    "exec",
    "run command",
  ].some((needle) => normalized.includes(needle));
}

async function readJsonResponse(response: Response, label: string): Promise<unknown> {
  const text = await response.text();
  try {
    return JSON.parse(text) as unknown;
  } catch {
    const contentType = response.headers.get("content-type") ?? "unknown content-type";
    throw new Error(
      `${label} returned ${contentType} instead of JSON with status ${response.status}.`,
    );
  }
}

function friendlyRunErrorMessage(message: string) {
  if (/failed to fetch/i.test(message)) {
    return "The coding page could not reach its agent service. Make sure the Next.js app and Source proxy are both running, then try again.";
  }

  return message;
}

function friendlyTelemetryRoute(route: TelemetryRoute) {
  const routeName = route.display_name ?? friendlyRouteName(route.route_type);
  const status = route.status ?? "unknown";
  return `${routeName} (${status})`;
}

function formatExactApprovalCommand(action: string, target: string) {
  const cleanAction = action.trim() || "No action entered.";
  const cleanTarget = target.trim();
  if (!cleanTarget) {
    return cleanAction;
  }
  return `${cleanAction}\nTarget: ${cleanTarget}`;
}

function sourceKindLabel(source: ResearchSource) {
  return source.url?.startsWith("repo://") ? "Repo source" : "Web source";
}

function formatRelevantContext(
  researchSources: ResearchSource[],
  attachedFiles: UploadedFile[],
  priorTurns: CodingHistoryEntry[],
  memoryEntries: DecisionMemoryEntry[],
) {
  const sections: string[] = [];

  const proxyMemoryContext = formatProxyMemoryContext(priorTurns, memoryEntries);
  if (proxyMemoryContext) {
    sections.push(proxyMemoryContext);
  }

  if (researchSources.length > 0) {
    sections.push(
      researchSources
        .map((source, index) => {
      return [
        `Source ${index + 1}: ${source.title ?? "Untitled source"}`,
        `URL: ${source.url ?? "No URL returned"}`,
        `Snippet: ${source.snippet ?? "No snippet returned"}`,
      ].join("\n");
    })
        .join("\n\n"),
    );
  }

  if (attachedFiles.length > 0) {
    sections.push(
      [
        "Attached file metadata:",
        ...attachedFiles.map(
          (file) =>
            `- ${file.name} (${formatFileSize(file.size)}, ${
              file.type || "unknown type"
            }, last modified ${new Date(file.lastModified).toISOString()})`,
        ),
      ].join("\n"),
    );
  }

  return sections.length > 0 ? sections.join("\n\n") : undefined;
}

function formatProxyMemoryContext(
  priorTurns: CodingHistoryEntry[],
  memoryEntries: DecisionMemoryEntry[],
) {
  return [formatConversationContext(priorTurns), formatDecisionMemoryContext(memoryEntries)]
    .filter(Boolean)
    .join("\n\n");
}

function formatConversationContext(priorTurns: CodingHistoryEntry[]) {
  if (priorTurns.length === 0) {
    return "";
  }

  return [
    "Recent coding conversation context:",
    ...priorTurns.map((entry, index) =>
      [
        `Turn ${index + 1}: ${entry.task || "No prompt supplied."}`,
        `Route: ${entry.route}`,
        `Recommendation: ${entry.recommendation}`,
        `Risk: ${entry.risk}`,
        `Summary: ${entry.summary}`,
      ].join("\n"),
    ),
  ].join("\n\n");
}

function formatDecisionMemoryContext(memoryEntries: DecisionMemoryEntry[]) {
  if (memoryEntries.length === 0) {
    return "";
  }

  return [
    "Previous routing decision memory:",
    ...memoryEntries.map((entry, index) =>
      [
        `Memory ${index + 1}: ${entry.task || "No prompt supplied."}`,
        `Classification: ${entry.classification}`,
        `Route: ${entry.route}`,
        `Recommendation: ${entry.recommendation}`,
        `Risk: ${entry.risk}`,
        `Reason codes: ${
          entry.reasonCodes.length > 0 ? entry.reasonCodes.join(", ") : "none"
        }`,
      ].join("\n"),
    ),
  ].join("\n\n");
}

function historyForProxy(priorTurns: CodingHistoryEntry[]) {
  return priorTurns.map((entry) => ({
    completed_at: entry.completedAt,
    recommendation: entry.recommendation,
    risk: entry.risk,
    route: entry.route,
    run_id: entry.runId,
    summary: entry.summary,
    task: entry.task,
  }));
}

function decisionMemoryForProxy(memoryEntries: DecisionMemoryEntry[]) {
  return memoryEntries.map((entry) => ({
    classification: entry.classification,
    completed_at: entry.completedAt,
    recommendation: entry.recommendation,
    reason_codes: entry.reasonCodes,
    risk: entry.risk,
    route: entry.route,
    task: entry.task,
  }));
}

function estimateTextTokens(value: string) {
  return value ? Math.max(1, Math.round(value.length / 4)) : 0;
}

function normalizeTaskText(value: string) {
  return value.trim().replace(/\s+/g, " ").toLowerCase();
}

function filesForProxy(attachedFiles: UploadedFile[]) {
  return attachedFiles.map((file) => ({
    last_modified: file.lastModified,
    name: file.name,
    size: file.size,
    type: file.type,
  }));
}

function inferTaskHints(task: string, attachedFiles: UploadedFile[]) {
  const normalized = task.toLowerCase();
  const hasCodeAttachment = attachedFiles.some((file) =>
    [".ts", ".tsx", ".js", ".jsx", ".py", ".css", ".html", ".json", ".xml"].includes(
      fileExtension(file.name),
    ),
  );

  return {
    needs_codebase_context:
      hasCodeAttachment ||
      [
        "/coding",
        "coding page",
        "codebase",
        "repo",
        "file",
        "trace",
        "review",
        "debug",
        "button",
        "component",
        "create",
        "indicator",
        "interface",
        "style",
        "toggle",
        "prompt quality",
        "self-awareness",
        "summary",
        "label",
      ].some((term) =>
        normalized.includes(term),
      ),
    needs_current_info: [
      "latest",
      "current",
      "today",
      "recent",
      "lookup",
      "look up",
      "research",
    ].some((term) => normalized.includes(term)),
    wants_implementation:
      hasCodeAttachment ||
      [
        "implement",
        "fix",
        "patch",
        "add",
        "refactor",
        "write code",
        "improve",
        "update",
        "change",
        "make",
      ].some((term) =>
        normalized.includes(term),
      ),
  };
}

function routeActionForDecision(decision: ProxyRouteDecisionResponse): RouteAction {
  if (decision.recommended_route === "local_route") {
    return routeActions[0];
  }

  if (decision.recommended_route === "api_route") {
    return routeActions[3];
  }

  if (
    decision.recommended_route === "manual_route" &&
    decision.task_classification === "codebase_analysis"
  ) {
    return routeActions[2];
  }

  if (decision.task_classification === "implementation") {
    return routeActions[0];
  }

  if (decision.risk_tier === "high") {
    return routeActions[2];
  }

  return routeActions[3];
}

function buildClipboardPrompt(
  action: RouteAction,
  promptText: string,
  attachedFiles: UploadedFile[],
  selfCorrection: SelfCorrectionState,
) {
  const attachmentText =
    attachedFiles.length > 0
      ? [
          "",
          "## Attached Files",
          ...attachedFiles.map(
            (file) => `- ${file.name} (${formatFileSize(file.size)}, ${file.type || "unknown type"})`,
          ),
        ].join("\n")
      : "";
  const selfCorrectionText = selfCorrection.triggered
    ? ["", "## Self-Correction Note", selfCorrection.refinedInstruction].join("\n")
    : "";

  return [`# ${action.label}`, promptText, selfCorrectionText, attachmentText]
    .join("\n")
    .trim();
}

function buildSelfCorrectionState({
  decision,
  memoryEntries,
  promptPacket,
  task,
}: {
  decision: ProxyRouteDecisionResponse;
  memoryEntries: DecisionMemoryEntry[];
  promptPacket: PromptPacketResponse;
  task: string;
}): SelfCorrectionState {
  const proxyConfidence = decision.confidence_score ?? decision.confidence;
  const checks = normalizeSelfCorrectionChecks(decision.self_correction_checks);
  const reasons: string[] = [];
  let confidence =
    typeof proxyConfidence === "number" && Number.isFinite(proxyConfidence)
      ? normalizeConfidence(proxyConfidence)
      : 0.86;

  if (!task.trim()) {
    confidence -= 0.55;
    reasons.push("No task text was supplied.");
  }

  if (decision.recommended_route === "ask_user") {
    confidence -= 0.34;
    reasons.push("Proxy selected ask_user, which means the route needs user choice.");
  }

  if (
    !decision.task_classification ||
    decision.task_classification === "general_reasoning"
  ) {
    confidence -= 0.16;
    reasons.push("Task classification is broad, so the route may be underspecified.");
  }

  if (modelFromDecision(decision) === "not returned") {
    confidence -= 0.1;
    reasons.push("The agent service did not return a clear model choice.");
  }

  if ((promptPacket.requests_for_more_information?.length ?? 0) > 0) {
    confidence -= 0.18;
    reasons.push("Prompt packet requested more information before execution.");
  }

  if (hasConflictingDecisionMemory(decision, memoryEntries)) {
    confidence -= 0.14;
    reasons.push("Previous decision memory contains a different route for similar tasks.");
  }

  const failedChecks = checks.filter((check) => check.passed === false);
  if (failedChecks.length > 0) {
    confidence -= failedChecks.length * 0.12;
    reasons.push(
      ...failedChecks.map(
        (check) => `${check.question ?? "Self-correction check"}: ${check.answer ?? "Needs review."}`,
      ),
    );
  }

  confidence = clampConfidence(confidence);
  const triggered = confidence < 0.68 || reasons.length >= 3;

  return {
    checks,
    confidence,
    reasons: reasons.length > 0 ? reasons : ["No confidence issues detected."],
    refinedInstruction: buildSelfCorrectionInstruction({
      decision,
      reasons,
      task,
      triggered,
    }),
    triggered,
  };
}

function normalizeSelfCorrectionChecks(checks: SelfCorrectionCheck[] | undefined) {
  if (!Array.isArray(checks) || checks.length === 0) {
    return [
      {
        id: "passive_check",
        question: "Am I being passive?",
        passed: true,
        answer: "No obvious passive routing issue was reported.",
      },
      {
        id: "repo_first_check",
        question: "Did I scan the repo first?",
        passed: true,
        answer: "No repo-first issue was reported.",
      },
      {
        id: "route_scope_check",
        question: "Is the chosen route appropriate for this task?",
        passed: true,
        answer: "Route scope was not flagged as a problem.",
      },
    ];
  }

  return checks.map((check) => ({
    id: check.id,
    question: check.question ?? "Self-correction check",
    passed: check.passed !== false,
    answer: check.answer ?? "No detail returned.",
  }));
}

function buildSelfCorrectionInstruction({
  decision,
  reasons,
  task,
  triggered,
}: {
  decision: ProxyRouteDecisionResponse;
  reasons: string[];
  task: string;
  triggered: boolean;
}) {
  if (!triggered) {
    return "Proceed with the proxy recommendation.";
  }

  return [
    "Before implementing, walk through the self-correction checks below.",
    `Task: ${task || "No prompt supplied."}`,
    `Initial route: ${decision.recommended_route ?? "unknown route"}`,
    `Initial classification: ${decision.task_classification ?? "unclassified task"}`,
    "Reasons to verify:",
    ...reasons.map((reason) => `- ${reason}`),
    "Required checks:",
    "- Am I being passive?",
    "- Did I scan the repo first?",
    "- Is the chosen route appropriate for blast radius and approvals?",
    "If the route still looks right, continue. If not, ask one focused clarification or choose the safer path.",
  ].join("\n");
}

function hasConflictingDecisionMemory(
  decision: ProxyRouteDecisionResponse,
  memoryEntries: DecisionMemoryEntry[],
) {
  const route = decision.recommended_route;
  const classification = decision.task_classification;
  if (!route || !classification) {
    return false;
  }

  return memoryEntries.some(
    (entry) => entry.classification === classification && entry.route !== route,
  );
}

function normalizeConfidence(confidence: number) {
  return confidence > 1 ? confidence / 100 : confidence;
}

function clampConfidence(confidence: number) {
  return Math.min(1, Math.max(0, confidence));
}

function formatConfidence(confidence: number) {
  return `${Math.round(clampConfidence(confidence) * 100)}%`;
}

function buildDecisionSummary({
  attachedFiles,
  decision,
  memoryEntries,
  promptPacket,
  priorTurns,
  runId,
  researchSources,
}: {
  attachedFiles: UploadedFile[];
  decision: ProxyRouteDecisionResponse;
  memoryEntries: DecisionMemoryEntry[];
  promptPacket: PromptPacketResponse;
  priorTurns: CodingHistoryEntry[];
  runId: number;
  researchSources: ResearchSource[];
}) {
  const action = routeActionForDecision(decision);
  const route = friendlyRouteName(decision.recommended_route);
  const model = modelFromDecision(decision);
  const risk = formatRiskTier(decision.risk_tier);
  const classification = friendlyTaskName(decision.task_classification);
  const context = workflowContextLabel(promptPacket);
  const requestCount = promptPacket.requests_for_more_information?.length ?? 0;

  return [
    `Run #${runId} completed.`,
    `${context}: ${action.label} is the recommended path for this ${classification}.`,
    `The agent chose ${route}, with model ${friendlyModelHint(model)} and safety level ${risk}.`,
    `It used ${priorTurns.length} earlier run${priorTurns.length === 1 ? "" : "s"}, ${memoryEntries.length} saved decision${memoryEntries.length === 1 ? "" : "s"}, ${attachedFiles.length} attached file${attachedFiles.length === 1 ? "" : "s"}, and ${researchSources.length} research source${researchSources.length === 1 ? "" : "s"}.`,
    requestCount > 0
      ? `${requestCount} follow-up request${requestCount === 1 ? "" : "s"} returned before execution.`
      : "No follow-up questions were returned.",
  ].join(" ");
}

function workflowContextLabel(promptPacket?: PromptPacketResponse): string {
  const goal = promptPacket?.increment_goal?.trim();
  if (goal && goal.length <= 160) {
    return goal;
  }
  const summary = promptPacket?.task_summary?.trim();
  if (summary && summary.length <= 160) {
    return summary;
  }
  const phase = promptPacket?.phase_label?.trim();
  const increment = promptPacket?.increment_label?.trim();
  if (phase && increment) {
    return `${phase} / ${increment}`;
  }
  if (phase) {
    return phase;
  }
  if (increment) {
    return increment;
  }
  return "SpiritOS coding workspace";
}

function buildCodingHistoryEntry({
  attachedFiles,
  completedAt,
  decision,
  memoryEntries,
  promptPacket,
  priorTurns,
  researchSources,
  runId,
  task,
}: {
  attachedFiles: UploadedFile[];
  completedAt: string;
  decision: ProxyRouteDecisionResponse;
  memoryEntries: DecisionMemoryEntry[];
  promptPacket: PromptPacketResponse;
  priorTurns: CodingHistoryEntry[];
  researchSources: ResearchSource[];
  runId: number;
  task: string;
}): CodingHistoryEntry {
  const recommendation = routeActionForDecision(decision).label;
  const summary = buildDecisionSummary({
    attachedFiles,
    decision,
    memoryEntries,
    promptPacket,
    priorTurns,
    runId,
    researchSources,
  });

  return {
    attachedFileCount: attachedFiles.length,
    completedAt,
    contextTurnCount: priorTurns.length,
    id: `${completedAt}-${runId}`,
    model: modelFromDecision(decision),
    recommendation,
    researchSourceCount: researchSources.length,
    risk: formatRiskTier(decision.risk_tier),
    route: decision.recommended_route ?? "unknown route",
    runId,
    summary,
    task,
  };
}

function buildDecisionMemoryEntry(
  task: string,
  decision: ProxyRouteDecisionResponse,
): DecisionMemoryEntry {
  const completedAt = new Date().toISOString();

  return {
    classification: decision.task_classification ?? "unclassified task",
    completedAt,
    id: `${completedAt}-${decision.recommended_route ?? "unknown"}`,
    model: modelFromDecision(decision),
    recommendation: routeActionForDecision(decision).label,
    reasonCodes: decision.reason_codes ?? [],
    risk: formatRiskTier(decision.risk_tier),
    route: decision.recommended_route ?? "unknown route",
    task,
  };
}

function addDecisionMemoryEntry(
  currentMemory: DecisionMemoryEntry[],
  entry: DecisionMemoryEntry,
) {
  const duplicateIndex = currentMemory.findIndex(
    (memoryEntry) =>
      normalizeMemoryTask(memoryEntry.task) === normalizeMemoryTask(entry.task) &&
      memoryEntry.route === entry.route &&
      memoryEntry.recommendation === entry.recommendation,
  );
  const filteredMemory =
    duplicateIndex === -1
      ? currentMemory
      : currentMemory.filter((_, index) => index !== duplicateIndex);

  return [entry, ...filteredMemory].slice(0, maxDecisionMemoryEntries);
}

function buildErrorHistoryEntry({
  completedAt,
  contextTurnCount,
  message,
  runId,
  task,
}: {
  completedAt: string;
  contextTurnCount: number;
  message: string;
  runId: number;
  task: string;
}): CodingHistoryEntry {
  return {
    attachedFileCount: 0,
    completedAt,
    contextTurnCount,
    id: `${completedAt}-${runId}-error`,
    model: "not returned",
    recommendation: "Check Source Proxy",
    researchSourceCount: 0,
    risk: "not returned",
    route: "request failed",
    runId,
    summary: message,
    task,
  };
}

function addCodingHistoryEntry(
  currentHistory: CodingHistoryEntry[],
  entry: CodingHistoryEntry,
) {
  return [entry, ...currentHistory].slice(0, maxCodingHistoryEntries);
}

function loadCodingHistory(): CodingHistoryEntry[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const rawHistory = window.localStorage.getItem(codingHistoryStorageKey);
    if (!rawHistory) {
      return [];
    }

    const parsed: unknown = JSON.parse(rawHistory);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .filter(isCodingHistoryEntry)
      .map((entry) => ({
        ...entry,
        contextTurnCount: entry.contextTurnCount ?? 0,
      }))
      .slice(0, maxCodingHistoryEntries);
  } catch {
    return [];
  }
}

function saveCodingHistory(entries: CodingHistoryEntry[]) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(codingHistoryStorageKey, JSON.stringify(entries));
}

function loadDecisionMemory(): DecisionMemoryEntry[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const rawMemory = window.localStorage.getItem(codingDecisionMemoryStorageKey);
    if (!rawMemory) {
      return [];
    }

    const parsed: unknown = JSON.parse(rawMemory);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter(isDecisionMemoryEntry).slice(0, maxDecisionMemoryEntries);
  } catch {
    return [];
  }
}

function saveDecisionMemory(entries: DecisionMemoryEntry[]) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(codingDecisionMemoryStorageKey, JSON.stringify(entries));
}

function isCodingHistoryEntry(value: unknown): value is CodingHistoryEntry {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Partial<CodingHistoryEntry>;
  return (
    typeof candidate.completedAt === "string" &&
    typeof candidate.id === "string" &&
    typeof candidate.recommendation === "string" &&
    typeof candidate.route === "string" &&
    typeof candidate.runId === "number" &&
    typeof candidate.summary === "string" &&
    typeof candidate.task === "string"
  );
}

function isDecisionMemoryEntry(value: unknown): value is DecisionMemoryEntry {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Partial<DecisionMemoryEntry>;
  return (
    typeof candidate.classification === "string" &&
    typeof candidate.completedAt === "string" &&
    typeof candidate.id === "string" &&
    typeof candidate.model === "string" &&
    typeof candidate.recommendation === "string" &&
    Array.isArray(candidate.reasonCodes) &&
    typeof candidate.risk === "string" &&
    typeof candidate.route === "string" &&
    typeof candidate.task === "string"
  );
}

function normalizeMemoryTask(task: string) {
  return task.trim().toLowerCase().replace(/\s+/g, " ");
}

function formatRunTimestamp(date: Date) {
  return date.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

function isProxyFeatureFlagOff(message: string) {
  return message.includes("SPIRIT_CODING_USE_PROXY is not true");
}

function formatRiskTier(riskTier: string | undefined): ProxyMetrics["risk"] {
  if (riskTier === "high") {
    return "High";
  }

  if (riskTier === "medium") {
    return "Medium";
  }

  return "Low";
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const kilobytes = bytes / 1024;
  if (kilobytes < 1024) {
    return `${kilobytes.toFixed(1)} KB`;
  }

  return `${(kilobytes / 1024).toFixed(1)} MB`;
}

function fileExtension(name: string) {
  const extensionStart = name.lastIndexOf(".");
  return extensionStart === -1 ? "" : name.slice(extensionStart).toLowerCase();
}
