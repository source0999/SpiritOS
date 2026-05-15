"use client";

// Implementation diffs are produced exclusively by the backend Coder. Never synthesize.

import type { MouseEvent, ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

import { DashboardDemoV4Atmosphere } from "@/components/dashboard/demo-v4/DashboardDemoV4Atmosphere";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import {
  deriveApprovalGateProposal,
  resolvedTargetPathFromDecision,
} from "@/components/coding/approval-gate-binding";
import { normalizeRepoRelativePath } from "@/lib/coding/explicit-task-target";
import {
  fetchJsonWithTimeout,
  isPlanUnavailableEnvelope,
  parseRouteDecisionPayload,
  ROUTE_RESPONSE_INVALID_PREFIX,
} from "@/lib/coding/proxy-route-payload";
import {
  collectPathsFromUnifiedDiff,
  diffTouchesExplicitTarget,
} from "@/lib/coding/unified-diff-paths";
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
const SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE =
  "coder_subjective_improvement_requires_diff_or_review";
const VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE =
  "coder_visual_improvement_diff_too_shallow";

// ── Unified diff hygiene ─────────────────────────────────────────────────────
// `git apply` wants a trailing newline on the patch text. `String.trim()` on the
// whole payload deletes it — same class of bug as `str.strip()` on Python diffs.
function unifiedDiffPayloadOrEmpty(raw: string): string {
  return raw.trim().length > 0 ? raw : "";
}

const BUNDLE_SNAPSHOT_DRIFT_REASON_CODE = "bundle_snapshot_drift";
const NO_APPROVABLE_DIFF_MESSAGE = "No approvable diff was produced.";
const NO_APPROVABLE_DIFF_NEXT_ACTION =
  "Coder did not produce a valid approvable unified diff. Retry Local Coder with stricter output repair, or copy a manual browser prompt.";
const CLIENT_REJECTED_BACKEND_DIFF_MESSAGE =
  "Backend returned a proposed diff, but it did not pass client approval validation. No approval action is available.";

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
  resolved_target?: {
    exists?: boolean;
    path?: string;
    source?: string;
  };
  resolvedTarget?: {
    exists?: boolean;
    path?: string;
    source?: string;
  };
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
  coder_blocked?: boolean;
  coderBlocked?: boolean;
  blocked_reason?: string;
  blockedReason?: string;
  needed_context?: string;
  neededContext?: string;
  already_satisfied?: boolean;
  alreadySatisfied?: boolean;
  status?: string;
  reason_code?: string;
  reasonCode?: string;
  coder_diagnostics?: Record<string, unknown>;
  coderDiagnostics?: Record<string, unknown>;
  task_spec?: CoderTaskSpecResponse;
  taskSpec?: CoderTaskSpecResponse;
  manual_prompt_packet_available?: boolean;
  manualPromptPacketAvailable?: boolean;
  cloud_route_available?: boolean;
  cloudRouteAvailable?: boolean;
  next_actions?: string[];
};

type CoderTaskSpecResponse = {
  allowed_files?: string[];
  blockers?: string[];
  forbidden_files?: string[];
  literal_requirements?: string[];
  risk_tier?: string;
  schema_version?: number;
  source?: string;
  target?: string | null;
  task_type?: string;
  verification?: string[];
  allowedFiles?: string[];
  forbiddenFiles?: string[];
  literalRequirements?: string[];
  riskTier?: string;
  schemaVersion?: number;
  taskType?: string;
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
  fallbackScaffoldBlocked?: boolean;
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
  recoveryPrompt?: string;
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
  alreadySatisfied: boolean;
  approvedAt: string | null;
  coderDiagnostics?: Record<string, unknown>;
  content: string;
  deniedAt: string | null;
  error: string | null;
  execution: ApprovedActionExecutionResponse | null;
  fallbackScaffoldAccepted: boolean;
  fallbackScaffoldBlocked: boolean;
  fallbackScaffoldGenerated: boolean;
  isChecking: boolean;
  preview: ApprovalPreviewResponse | null;
  proposedDiff: string;
  target: string;
};

type ApprovalRejectionReason =
  | "wrong_target"
  | "wrong_approach"
  | "missing_constraint"
  | "style_violation"
  | "other";

const approvalRejectionReasons: { label: string; value: ApprovalRejectionReason }[] = [
  { label: "wrong_target", value: "wrong_target" },
  { label: "wrong_approach", value: "wrong_approach" },
  { label: "missing_constraint", value: "missing_constraint" },
  { label: "style_violation", value: "style_violation" },
  { label: "other", value: "other" },
];

type ApprovedActionExecutionResponse = {
  action?: string;
  appliedAt?: string;
  applied_at?: string;
  audit?: {
    changed_files?: string[];
    risk?: string;
    target?: string;
  };
  backup_root?: string;
  backupRelativePath?: string;
  changed_files?: DiffChangedFile[];
  code?: string;
  diff?: string;
  execution?: Record<string, unknown>;
  message?: string;
  ok: boolean;
  post_apply_verification?: PostApplyVerification;
  proposalId?: string;
  relativeFilePath?: string;
  risk?: string;
  status?: string;
  target?: string;
  task?: LongRunningTaskPayload;
  verification_plan?: string[];
};

type PostApplyVerification = {
  backup_root?: string;
  changed_files?: DiffChangedFile[];
  checks?: {
    command?: string[] | string;
    command_text?: string;
    duration_ms?: number;
    exit_code?: number;
    id?: string;
    output_tail?: string;
    required?: boolean;
    status?: string;
    summary?: string;
  }[];
  docs_only?: boolean;
  docs_only_confirmations?: {
    backup_audit_present?: boolean;
    file_changed_as_expected?: boolean;
    no_unintended_files?: boolean;
  };
  manual_browser_check_done?: boolean;
  manual_browser_check_required?: boolean;
  required?: boolean;
  risk?: string;
  skip_reason?: string;
  status?: string;
  unsupported_code_verification?: boolean;
  unsupported_file_types?: string[];
  updated_at?: string;
  verification_note?: string;
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

type DeterministicCheck = {
  blocking?: boolean;
  duration_ms?: number;
  id?: string;
  output?: string;
  status?: string;
  tier?: number;
};

type DiffVerificationPreviewResponse = {
  access_scope?: string;
  blocked_reasons?: { path: string; reason_code: string }[];
  changed_files?: DiffChangedFile[];
  limits?: Record<string, unknown>;
  deterministic_checks?: DeterministicCheck[];
  task_spec_check?: {
    allowed_files?: string[];
    changed_files?: string[];
    forbidden_files?: string[];
    ok?: boolean;
    reason_codes?: string[];
    skipped?: boolean;
    summary?: string;
    target?: string | null;
    task_type?: string | null;
  };
  manual_checks?: string[];
  requirement_coverage?: {
    ok?: boolean;
    missing?: string[];
    required?: Record<string, unknown>;
    summary?: string;
  };
  review_report?: {
    findings?: { details?: string; id?: string; path?: string }[];
    passed?: boolean;
    skipped?: boolean;
  };
  llm_review_report?: {
    findings?: { details?: string; id?: string; path?: string }[];
    passed?: boolean;
    reason?: string;
    skipped?: boolean;
  };
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
  typescript_check?: {
    ok?: boolean;
    skipped?: boolean;
    summary?: string;
  };
  tool?: string;
  verification_plan?: string[];
  would_apply_diff?: boolean;
  would_execute?: boolean;
  git_apply_check_ok?: boolean;
  git_apply_check_error?: string;
  unified_diff?: string;
};

type DiffVerificationState = {
  error: string | null;
  isChecking: boolean;
  preview: DiffVerificationPreviewResponse | null;
  unifiedDiff: string;
};

type LongRunningTaskPayload = {
  architect_reason?: string;
  architect_status?: string;
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
  post_apply_verification?: PostApplyVerification | null;
  progress?: number;
  role_transitions?: RoleTransitionPayload[];
  status: string;
  steps?: string[];
  truncated_test_results?: string;
  updated_at?: string;
  would_execute?: boolean;
  writes_allowed?: boolean;
};

type RoleTransitionPayload = {
  at?: string;
  from?: "architect" | "coder" | "debugger" | string;
  reason?: string;
  to?: "architect" | "coder" | "debugger" | string;
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

type ArchitectPlanResponse = {
  budget?: {
    cloud_escalation_allowed?: boolean;
    max_coder_attempts?: number;
    max_total_seconds?: number;
  };
  classification?: {
    designer_required?: boolean;
    estimated_complexity?: string;
    task_class?: string;
    visual_change?: boolean;
  };
  coder_packet?: {
    acceptance_criteria?: Array<{
      description?: string;
      id?: string;
      kind?: string;
    }>;
    constraints?: {
      must_contain?: string[];
      must_not_contain?: string[];
      preserve_exports?: string[];
      preserve_imports?: string[];
    };
    context_slices?: Array<{
      kind?: string;
      line_range?: [number, number] | number[];
      path?: string;
    }>;
    operation?: string;
    style_directives?: string[];
    target_file?: {
      exists?: boolean;
      path?: string;
      sha256_before?: string | null;
    };
  };
  created_at?: string;
  plan_id?: string;
  source_task?: string;
  task_spec?: CoderTaskSpecResponse;
  taskSpec?: CoderTaskSpecResponse;
  task_id?: string;
  verification_plan?: {
    required_checks?: Array<{
      blocking?: boolean;
      command?: string[];
      id?: string;
      timeout_seconds?: number;
    }>;
  };
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
  const loggedTaskActivityRef = useRef<Set<string>>(new Set());
  /** Survives into catch() so a post-route failure can still render the route decision summary. */
  const lastRouteDecisionRef = useRef<ProxyRouteDecisionResponse | null>(null);
  const lastSubmittedTaskRef = useRef("");
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
    alreadySatisfied: false,
    approvedAt: null,
    coderDiagnostics: undefined,
    content: "",
    deniedAt: null,
    error: null,
    execution: null,
    fallbackScaffoldAccepted: false,
    fallbackScaffoldBlocked: false,
    fallbackScaffoldGenerated: false,
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
  const [architectPlan, setArchitectPlan] = useState<ArchitectPlanResponse | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!toastMessage) {
      return;
    }
    const timeout = window.setTimeout(() => setToastMessage(null), 5000);
    return () => window.clearTimeout(timeout);
  }, [toastMessage]);

  useEffect(() => {
    const taskId = longRunningTask.response?.task.id;
    const status = longRunningTask.response?.task.status;
    if (!taskId || isTerminalLongTaskStatus(status)) {
      return;
    }

    const stream = new EventSource(
      `/v1/tasks/long-running/${encodeURIComponent(taskId)}/stream`,
    );

    stream.addEventListener("open", () => {
      if (!shouldAppendTaskActivityLog(loggedTaskActivityRef.current, taskId, "sse_connected")) {
        return;
      }
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Task stream",
          detail: "Live task updates connected (SSE).",
          level: "info",
        },
      ]);
    });

    stream.addEventListener("task", (event) => {
      try {
        const response = JSON.parse((event as MessageEvent).data) as LongRunningTaskResponse;
        setLongRunningTask((current) => {
          if (
            current.response?.task.id === response.task.id &&
            isNoDiffTerminalLongTaskStatus(current.response.task.status) &&
            !isTerminalLongTaskStatus(response.task.status)
          ) {
            return current;
          }
          return {
            ...current,
            error: null,
            response,
          };
        });
      } catch {
        setLongRunningTask((current) => ({
          ...current,
          error: "Long-running task stream returned an invalid payload.",
        }));
      }
    });

    stream.addEventListener("plan_updated", (event) => {
      try {
        const plan = JSON.parse((event as MessageEvent).data) as ArchitectPlanResponse;
        setArchitectPlan(plan);
      } catch {
        setLongRunningTask((current) => ({
          ...current,
          error: "Long-running task stream returned an invalid plan payload.",
        }));
      }
    });

    stream.addEventListener("role_transition", (event) => {
      try {
        const transition = JSON.parse((event as MessageEvent).data) as RoleTransitionPayload;
        const from = normalizeLongTaskRole(transition.from);
        const to = normalizeLongTaskRole(transition.to);
        setProcessLogs((currentLogs) => [
          ...currentLogs,
          {
            id: Date.now(),
            label: "Role transition",
            detail: `${longTaskRoleLabel(from)} -> ${longTaskRoleLabel(to)}${
              transition.reason ? `: ${transition.reason}` : ""
            }.`,
            level: "info",
          },
        ]);
      } catch {
        setLongRunningTask((current) => ({
          ...current,
          error: "Long-running task stream returned an invalid role transition payload.",
        }));
      }
    });

    stream.addEventListener("error", () => {
      if (shouldAppendTaskActivityLog(loggedTaskActivityRef.current, taskId, "stream_fallback")) {
        setProcessLogs((currentLogs) => [
          ...currentLogs,
          {
            id: Date.now() + 1,
            label: "Task stream",
            detail:
              "Stream unavailable; polling task status (1.5s interval) until this task finishes.",
            level: "warning",
          },
        ]);
      }
      stream.close();
    });

    return () => {
      stream.close();
    };
  }, [longRunningTask.response?.task.id, longRunningTask.response?.task.status]);

  useEffect(() => {
    const taskId = longRunningTask.response?.task.id;
    if (!taskId) {
      setArchitectPlan(null);
      return;
    }
    let cancelled = false;
    void callLongRunningTaskPlan(taskId)
      .then((plan) => {
        if (!cancelled) {
          setArchitectPlan(plan);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setArchitectPlan(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [longRunningTask.response?.task.id]);

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
          if (
            isNoDiffTerminalLongTaskStatus(current.response.task.status) &&
            !isTerminalLongTaskStatus(payload.task.status)
          ) {
            return current;
          }
          return { ...current, response: payload, error: null };
        });

        const diffEntry = payload.task.open_diffs?.[0];
        const diff = typeof diffEntry?.diff === "string" ? diffEntry.diff.trim() : "";
        if (
          normalizeTaskText(payload.task.description ?? "") !==
          normalizeTaskText(lastSubmittedTaskRef.current)
        ) {
          return;
        }
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
      } catch {
        /* Long-running status poll failed; next interval will retry. */
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

    const explicitFromTask = resolvedTargetPathFromDecision(finalOutput?.decision);
    if (
      explicitFromTask &&
      proposedDiff &&
      !diffTouchesExplicitTarget(proposedDiff, explicitFromTask)
    ) {
      setApprovalGate((current) => ({
        ...current,
        approvedAt: null,
        deniedAt: null,
        error: null,
        isChecking: false,
        preview: {
          decision: "blocked",
          reason_codes: ["target_mismatch_stale_diff"],
          requires_human_approval: false,
          safety_message:
            "Current task Target file does not match the diff paths. Re-run the task or paste a diff for that file.",
        },
      }));
      return;
    }

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
      let normalizedPreview = normalizeApprovalPreview({
        action: approvalGate.action,
        preview,
        target: approvalGate.target,
      });

      if (proposedDiff) {
        const diffPreview = await callDiffVerificationPreview(proposedDiff, {
          activeTaskId: longRunningTask.response?.task.id,
          routeType:
            proxyMetrics.route === "not run" || proxyMetrics.route === "pending"
              ? undefined
              : proxyMetrics.route,
          nextPromptAction: finalOutput?.decision?.next_prompt_action,
          taskText: inputText,
        });
        const normalizedDiffPreview = normalizeDiffVerificationPreview(diffPreview);
        setDiffVerification((current) => ({
          ...current,
          error: null,
          isChecking: false,
          preview: normalizedDiffPreview,
          unifiedDiff: proposedDiff,
        }));
        if (normalizedDiffPreview.status === "blocked") {
          const diffReasonCodes = normalizedDiffPreview.blocked_reasons?.map(
            (reason) => reason.reason_code,
          ) ?? ["diff_preview_blocked"];
          const requirementMessage =
            normalizedDiffPreview.requirement_coverage?.missing?.join(" ") ?? "";
          const diffMsg =
            requirementMessage ||
            normalizedDiffPreview.git_apply_check_error ||
            "Diff verification blocked this proposal. Review the diff preview details before approving.";
          normalizedPreview = {
            ...normalizedPreview,
            decision: "blocked",
            reason_codes: [
              ...(normalizedPreview.reason_codes ?? []),
              ...diffReasonCodes,
            ],
            requires_human_approval: false,
            safety_message: normalizedPreview.safety_message
              ? `${normalizedPreview.safety_message} ${diffMsg}`
              : diffMsg,
          };
        } else if (normalizedDiffPreview.git_apply_check_ok === false) {
          const applyErr =
            typeof normalizedDiffPreview.git_apply_check_error === "string" &&
            normalizedDiffPreview.git_apply_check_error.trim()
              ? normalizedDiffPreview.git_apply_check_error.trim()
              : "";
          const applyMsg = applyErr
            ? `Stale diff: git apply --check failed (${applyErr}). Regenerate from the current file.`
            : "Stale diff: git apply --check failed on this workspace. Regenerate from the current file.";
          normalizedPreview = {
            ...normalizedPreview,
            decision: "blocked",
            reason_codes: [
              ...(normalizedPreview.reason_codes ?? []),
              "diff_apply_check_failed",
            ],
            requires_human_approval: false,
            safety_message: normalizedPreview.safety_message
              ? `${normalizedPreview.safety_message} ${applyMsg}`
              : applyMsg,
          };
        }
      }

      setApprovalGate((current) => ({
        ...current,
        isChecking: false,
        preview: normalizedPreview,
      }));
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

  async function denyPreviewedAction(reasonCode: ApprovalRejectionReason) {
    setApprovalGate((current) => ({
      ...current,
      error: null,
      isChecking: true,
    }));
    const taskId = longRunningTask.response?.task.id ?? "";
    setApprovalGate((current) => ({
      ...current,
      approvedAt: null,
      deniedAt: new Date().toISOString(),
      execution: null,
      isChecking: false,
    }));
    let feedbackMessage =
      reasonCode === "other"
        ? "Plan rejection recorded."
        : "Plan will be regenerated with this feedback.";
    if (taskId) {
      try {
        const rejected = await callLongRunningTaskRejectPlan(taskId, reasonCode);
        feedbackMessage =
          typeof rejected.message === "string" ? rejected.message : feedbackMessage;
        setLongRunningTask((current) => ({
          ...current,
          error: null,
          isChecking: false,
          response: rejected,
        }));
        try {
          setArchitectPlan(await callLongRunningTaskPlan(taskId));
        } catch {
          setArchitectPlan(null);
        }
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Unknown plan rejection error.";
        setApprovalGate((current) => ({
          ...current,
          error: message,
          isChecking: false,
        }));
        setLongRunningTask((current) => ({
          ...current,
          error: message,
          isChecking: false,
        }));
        return;
      }
    }
    setToastMessage(feedbackMessage);
    setProcessLogs((currentLogs) => [
      ...currentLogs,
      {
        id: Date.now(),
        label: "Plan rejected",
        detail: `User rejected with ${reasonCode}: ${approvalGate.action} ${
          approvalGate.target ? `(${approvalGate.target})` : ""
        }. ${feedbackMessage}`,
        level: "warning",
      },
    ]);
  }

  async function previewDiffVerification(unifiedDiffOverride?: string) {
    const mergedFromState =
      unifiedDiffPayloadOrEmpty(diffVerification.unifiedDiff) ||
      unifiedDiffPayloadOrEmpty(approvalGate.proposedDiff);
    const unifiedDiffText =
      unifiedDiffOverride !== undefined ? unifiedDiffOverride : mergedFromState;

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
      ...(unifiedDiffPayloadOrEmpty(current.unifiedDiff) && unifiedDiffText
        ? { unifiedDiff: unifiedDiffText }
        : {}),
    }));

    try {
      const preview = await callDiffVerificationPreview(unifiedDiffText, {
        activeTaskId: longRunningTask.response?.task.id,
        routeType:
          proxyMetrics.route === "not run" || proxyMetrics.route === "pending"
            ? undefined
            : proxyMetrics.route,
        nextPromptAction: finalOutput?.decision?.next_prompt_action,
        taskText: inputText,
      });
      const normalizedPreview = normalizeDiffVerificationPreview(preview);
      const previewChangedFile = normalizedPreview.changed_files?.[0];
      const previewDiffPath =
        previewChangedFile?.path ?? collectPathsFromUnifiedDiff(unifiedDiffText)[0] ?? "";
      const previewAction =
        previewChangedFile?.change_type === "added" ? "create file" : "modify file";
      setDiffVerification((current) => ({
        ...current,
        isChecking: false,
        preview: normalizedPreview,
        ...(unifiedDiffOverride !== undefined
          ? { unifiedDiff: unifiedDiffText }
          : unifiedDiffPayloadOrEmpty(current.unifiedDiff)
            ? {}
            : { unifiedDiff: unifiedDiffText }),
      }));
      setApprovalGate((current) => ({
        ...current,
        action: previewDiffPath ? previewAction : current.action,
        approvedAt: null,
        deniedAt: null,
        error: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
        preview: normalizedPreview.status === "blocked"
          ? {
              decision: "blocked",
              reason_codes:
                normalizedPreview.blocked_reasons?.map(
                  (reason) => reason.reason_code,
                ) ?? ["diff_preview_blocked"],
              requires_human_approval: false,
              safety_message:
                normalizedPreview.requirement_coverage?.summary ||
                normalizedPreview.git_apply_check_error ||
                "Diff verification blocked this proposal.",
            }
          : current.preview,
        proposedDiff: unifiedDiffText,
        target: previewDiffPath || current.target,
      }));
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Diff verification",
          detail: `${normalizedPreview.status ?? "unknown"}: ${
            normalizedPreview.changed_files?.length ?? 0
          } changed file${(normalizedPreview.changed_files?.length ?? 0) === 1 ? "" : "s"}; risk ${
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

  async function previewManualResult() {
    const payload = diffVerification.unifiedDiff.trim();
    if (!payload) {
      setDiffVerification((current) => ({
        ...current,
        error: "Paste browser JSON or a unified diff before previewing.",
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
      const preview = await callManualResultPreview(payload, {
        activeTaskId: longRunningTask.response?.task.id,
        routeType:
          proxyMetrics.route === "not run" || proxyMetrics.route === "pending"
            ? undefined
            : proxyMetrics.route,
        nextPromptAction: finalOutput?.decision?.next_prompt_action,
        taskSpec: taskSpecForPlan(architectPlan) ?? undefined,
        taskText: inputText,
      });
      const normalizedPreview = normalizeDiffVerificationPreview(preview);
      const unifiedDiffText =
        typeof preview.unified_diff === "string" ? preview.unified_diff : payload;
      const previewChangedFile = normalizedPreview.changed_files?.[0];
      const previewDiffPath =
        previewChangedFile?.path ?? collectPathsFromUnifiedDiff(unifiedDiffText)[0] ?? "";
      const previewAction =
        previewChangedFile?.change_type === "added" ? "create file" : "modify file";
      setDiffVerification((current) => ({
        ...current,
        error: null,
        isChecking: false,
        preview: normalizedPreview,
        unifiedDiff: unifiedDiffText,
      }));
      setApprovalGate((current) => ({
        ...current,
        action: previewDiffPath ? previewAction : current.action,
        approvedAt: null,
        deniedAt: null,
        error: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
        preview:
          normalizedPreview.status === "blocked"
            ? {
                decision: "blocked",
                reason_codes:
                  normalizedPreview.blocked_reasons?.map((reason) => reason.reason_code) ??
                  ["diff_preview_blocked"],
                requires_human_approval: false,
                safety_message:
                  "Manual result preview blocked this proposal. Review the details before approving.",
              }
            : current.preview,
        proposedDiff: unifiedDiffText,
        target: previewDiffPath || current.target,
      }));
      await previewApprovalGate();
    } catch (error) {
      setDiffVerification((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Unknown manual result preview error.",
        isChecking: false,
        preview: null,
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

  async function verifyDocsOnlyLongRunningTask() {
    const taskId = longRunningTask.response?.task.id;
    if (!taskId) {
      setLongRunningTask((current) => ({
        ...current,
        error: "Apply an approved docs diff before marking verification complete.",
      }));
      return;
    }

    setLongRunningTask((current) => ({
      ...current,
      error: null,
      isChecking: true,
    }));
    try {
      const response = await callLongRunningTaskDocsOnlyVerify(taskId);
      setLongRunningTask((current) => ({
        ...current,
        isChecking: false,
        response,
      }));
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Docs verified",
          detail: "Changed files reviewed; expected docs change is present; no unintended files changed.",
          level: "success",
        },
      ]);
    } catch (error) {
      setLongRunningTask((current) => ({
        ...current,
        error:
          error instanceof Error
            ? error.message
            : "Unknown post-apply verification error.",
        isChecking: false,
      }));
    }
  }

  async function verifyCodeLongRunningTask() {
    const taskId = longRunningTask.response?.task.id;
    if (!taskId) {
      setLongRunningTask((current) => ({
        ...current,
        error: "Apply an approved code diff before running verification.",
      }));
      return;
    }

    setLongRunningTask((current) => ({
      ...current,
      error: null,
      isChecking: true,
    }));
    try {
      const response = await callLongRunningTaskCodeVerify(taskId);
      setLongRunningTask((current) => ({
        ...current,
        isChecking: false,
        response,
      }));
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Code verified",
          detail: "Server-side allowlisted code verification completed.",
          level: response.task.status === "completed" ? "success" : "warning",
        },
      ]);
    } catch (error) {
      setLongRunningTask((current) => ({
        ...current,
        error:
          error instanceof Error
            ? error.message
            : "Unknown code verification error.",
        isChecking: false,
      }));
    }
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
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Submit ignored",
          detail: "A proxy run is already in progress. Wait for it to finish or use Start new task.",
          level: "warning",
        },
      ]);
      return;
    }

    isRunningRef.current = true;
    lastRouteDecisionRef.current = null;
    const runId = runSequenceRef.current + 1;
    runSequenceRef.current = runId;
    const startedAt = new Date();
    setIsRunning(true);

    const task = inputText.trim();
    lastSubmittedTaskRef.current = task;
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
    applyDiscoveryWorkspaceForTask(task, { clearProposal: true });
    setFinalOutput(null);
    setArchitectPlan(null);
    setWorkflowStepFloor(null);
    setLongRunningTask((current) => ({
      ...current,
      description: task,
      error: null,
      isChecking: true,
      response: activeTask ? current.response : null,
    }));
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

    try {
      const decision = await callProxyRouteDecision({
        activeTaskId,
        attachedFiles,
        currentAgentRole,
        memoryEntries,
        priorTurns,
        task,
      });
      lastRouteDecisionRef.current = decision;
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Route decision received",
          detail: `Classification: ${friendlyTaskName(decision.task_classification)}; route: ${friendlyRouteName(decision.recommended_route ?? "unknown")}.`,
          level: "success",
        },
      ]);
      const explicitTaskTarget = resolvedTargetPathFromDecision(decision);
      let researchSources = decision.research_sources ?? [];

      if (decision.research_recommended) {
        const researchPreview = await callProxyResearchPreview({
          activeTaskId,
          attachedFiles,
          currentAgentRole,
          memoryEntries,
          priorTurns,
          task,
        });
        researchSources = researchPreview.research_sources ?? researchSources;
        setProcessLogs((currentLogs) => [
          ...currentLogs,
          {
            id: Date.now(),
            label: "Research preview merged",
            detail: `${researchSources.length} research source(s) ready for the prompt packet.`,
            level: "success",
          },
        ]);
      }

      let trackedTask = await syncArchitectPlanForSubmittedTask(
        task,
        activeTask ? longRunningTask.response : null,
      );
      if (trackedTask.task.architect_status !== "planned") {
        setArchitectPlan(null);
      }
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Fetching prompt packet",
          detail: "POST /v1/decisions/prompt-packet (this step can take minutes when Coder Agent runs).",
          level: "info",
        },
      ]);
      const promptPacket = await callProxyPromptPacket({
        activeTaskId: trackedTask.task.id,
        attachedFiles,
        currentAgentRole: trackedTask.task.current_agent_role,
        memoryEntries,
        priorTurns,
        researchSources,
        task,
      });
      try {
        trackedTask = await callLongRunningTaskStatus(trackedTask.task.id);
        setLongRunningTask((current) => ({
          ...current,
          description: task,
          error: null,
          isChecking: false,
          response: trackedTask,
        }));
      } catch {
        /* The plan and prompt-packet already loaded; task status will refresh via SSE/poll. */
      }
      researchSources = promptPacket.research_sources ?? researchSources;
      const rawPacketSnake =
        typeof promptPacket.proposed_diff === "string" ? promptPacket.proposed_diff : "";
      const rawPacketCamel =
        typeof promptPacket.proposedDiff === "string" ? promptPacket.proposedDiff : "";
      const backendReturnedProposedDiff =
        rawPacketSnake.trim().length > 0 || rawPacketCamel.trim().length > 0;
      let packetDiff =
        unifiedDiffPayloadOrEmpty(rawPacketSnake) || unifiedDiffPayloadOrEmpty(rawPacketCamel);
      const packetTarget =
        typeof promptPacket.target === "string" ? promptPacket.target.trim() : "";
      if (
        explicitTaskTarget &&
        packetDiff &&
        !diffTouchesExplicitTarget(packetDiff, explicitTaskTarget)
      ) {
        packetDiff = "";
        promptPacket.proposed_diff = "";
        promptPacket.proposedDiff = "";
        promptPacket.target = explicitTaskTarget;
      }
      const approvalProposal = deriveApprovalGateProposal(decision, promptPacket, {
        currentTaskText: task,
        resolvedTargetPath: explicitTaskTarget,
      });
      const mergedProposedDiff =
        unifiedDiffPayloadOrEmpty(approvalProposal?.proposedDiff ?? "") || packetDiff;
      const mergedTarget = (approvalProposal?.target ?? "").trim() || packetTarget;
      const mergedAction =
        mergedProposedDiff && mergedTarget
          ? "modify file"
          : (approvalProposal?.action ?? "");
      const coderBlocked = promptPacket.coder_blocked === true || promptPacket.coderBlocked === true;
      const coderBlockedReason =
        (typeof promptPacket.blocked_reason === "string" && promptPacket.blocked_reason.trim()) ||
        (typeof promptPacket.blockedReason === "string" && promptPacket.blockedReason.trim()) ||
        "Coder Agent could not produce validated replacement content for backend diff generation.";
      const coderReasonCode =
        (typeof promptPacket.reason_code === "string" && promptPacket.reason_code.trim()) ||
        (typeof promptPacket.reasonCode === "string" && promptPacket.reasonCode.trim()) ||
        "coder_agent_blocked";
      const alreadySatisfied =
        promptPacket.already_satisfied === true ||
        promptPacket.alreadySatisfied === true ||
        promptPacket.status === "already_satisfied" ||
        coderReasonCode === "coder_no_changes_needed";
      const subjectiveImprovementNeedsDiff =
        coderReasonCode === SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE ||
        coderReasonCode === VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE;
      const shallowVisualDiff =
        coderReasonCode === VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE;
      const coderNeededContext =
        (typeof promptPacket.needed_context === "string" && promptPacket.needed_context.trim()) ||
        (typeof promptPacket.neededContext === "string" && promptPacket.neededContext.trim()) ||
        "";
      let effectiveProposedDiff = mergedProposedDiff;
      let effectiveTarget = mergedTarget;
      let effectiveAction = mergedAction;
      let staleTargetMismatchPreview: ApprovalPreviewResponse | null = coderBlocked
        ? {
            decision:
              coderReasonCode === "coder_model_not_configured" ||
              coderReasonCode === "coder_empty_model_response"
                ? "blocked"
                : coderReasonCode === "coder_sync_timeout"
                  ? "blocked"
                  : subjectiveImprovementNeedsDiff
                    ? "needs_coder_diff"
                    : "blocked",
            reason_codes:
              coderReasonCode === "coder_model_not_configured"
                ? ["coder_model_not_configured", "coder_config_blocked"]
                : coderReasonCode === "coder_empty_model_response"
                  ? ["coder_empty_model_response", "coder_config_blocked"]
                  : coderReasonCode === "coder_sync_timeout"
                    ? ["coder_sync_timeout", "coder_proxy_deadline_blocked"]
                    : subjectiveImprovementNeedsDiff
                      ? ["needs_coder_diff", coderReasonCode]
                      : [coderReasonCode],
            requires_human_approval: false,
            safety_message: coderNeededContext
              ? `${coderBlockedReason} Needed context: ${coderNeededContext}`
              : coderBlockedReason,
            target: effectiveTarget || explicitTaskTarget || packetTarget || null,
          }
        : null;
      if (
        explicitTaskTarget &&
        effectiveProposedDiff &&
        !diffTouchesExplicitTarget(effectiveProposedDiff, explicitTaskTarget)
      ) {
        effectiveProposedDiff = "";
        effectiveTarget = explicitTaskTarget;
        effectiveAction = "needs_coder_diff";
        staleTargetMismatchPreview = {
          decision: "blocked",
          reason_codes: ["target_mismatch_stale_diff"],
          requires_human_approval: false,
          safety_message:
            "Stale diff targeted a different path than your current Target file line. Regenerate from the current file before approving.",
        };
      }
      const coderDiffReady = looksLikeUnifiedDiff(effectiveProposedDiff);
      const clientRejectedBackendProposedDiff =
        backendReturnedProposedDiff && !coderDiffReady && !alreadySatisfied;
      const fallbackScaffoldBlocked = false;
      const fallbackScaffoldGenerated = false;
      const selfCorrection = buildSelfCorrectionState({
        decision,
        memoryEntries,
        promptPacket,
        task,
      });
      const decisionForOutput =
        coderReasonCode === "coder_model_not_configured" ||
        coderReasonCode === "coder_empty_model_response" ||
        coderReasonCode === "coder_sync_timeout"
          ? { ...decision, model: coderReasonCode }
          : decision;

      let initialDiffPreview: DiffVerificationPreviewResponse | null = null;
      const routeForVerify =
        decision.recommended_route === "local_route"
          ? "local_route"
          : decision.recommended_route === "api_route"
            ? "api_route"
            : undefined;
      if (looksLikeUnifiedDiff(effectiveProposedDiff)) {
        try {
          const rawPreview = await callDiffVerificationPreview(effectiveProposedDiff, {
            activeTaskId: trackedTask.task.id,
            routeType: routeForVerify,
            nextPromptAction: decision.next_prompt_action,
            taskText: task,
          });
          initialDiffPreview = normalizeDiffVerificationPreview(rawPreview);
        } catch {
          initialDiffPreview = null;
        }
      }

      let combinedApprovalPreview: ApprovalPreviewResponse | null = alreadySatisfied
        ? {
            decision: "already_satisfied",
            reason_codes: ["coder_no_changes_needed"],
            requires_human_approval: false,
            safety_message:
              "No approval action is available because no file change is needed.",
            target: effectiveTarget || explicitTaskTarget || packetTarget || null,
          }
        : staleTargetMismatchPreview;
      if (
        !alreadySatisfied &&
        (decision.reason_codes?.includes("target_missing") ||
          decision.reason_codes?.includes("target_unresolved"))
      ) {
        combinedApprovalPreview = {
          decision: "blocked",
          reason_codes: [
            ...(decision.reason_codes?.filter((c) => c === "target_missing" || c === "target_unresolved") ??
              []),
          ],
          requires_human_approval: false,
          safety_message: decision.reason_codes?.includes("target_missing")
            ? "The resolved target path is not an existing file in this workspace. Fix the path spelling or create the file, then retry."
            : "No safe file target was resolved from your task. Add a `Target file:` line or mention an existing repo-relative path (for example docs/phase-8-manual-check.md).",
          target: explicitTaskTarget || null,
        };
      }
      if (
        !alreadySatisfied &&
        !effectiveProposedDiff &&
        !approvalProposal?.content &&
        !combinedApprovalPreview
      ) {
        combinedApprovalPreview = {
          decision:
            coderReasonCode === "coder_model_not_configured" ||
            coderReasonCode === "coder_empty_model_response" ||
            coderReasonCode === "coder_sync_timeout"
              ? "blocked"
              : "needs_coder_diff",
          reason_codes:
            coderReasonCode === "coder_model_not_configured"
              ? ["coder_model_not_configured", "coder_config_blocked"]
              : coderReasonCode === "coder_empty_model_response"
                ? ["coder_empty_model_response", "coder_config_blocked"]
                : coderReasonCode === "coder_sync_timeout"
                  ? ["coder_sync_timeout", "coder_proxy_deadline_blocked"]
                  : coderReasonCode === "blocked_after_retries"
                    ? ["blocked_after_retries", "reviewer_blocked"]
                  : subjectiveImprovementNeedsDiff
                    ? ["needs_coder_diff", coderReasonCode]
                    : ["needs_coder_diff"],
          requires_human_approval: false,
          safety_message:
            coderReasonCode === "coder_model_not_configured"
              ? "Coder model is not configured or the configured alias is not available on this proxy. Set SOURCE_PROXY_CODER_MODEL_ALIAS to a valid enabled alias, then retry."
              : coderReasonCode === "coder_empty_model_response"
                ? "Coder returned an empty model response. Verify SOURCE_PROXY_CODER_MODEL_ALIAS and provider availability, then retry."
                : coderReasonCode === "coder_sync_timeout"
                  ? "Coder repomix+LLM exceeded the proxy sync deadline. Raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC or narrow scope, then retry."
                  : coderReasonCode === "blocked_after_retries"
                    ? "Reviewer blocked the generated diff after bounded Coder retries. No approval action is available."
                  : shallowVisualDiff
                    ? "The generated diff was too shallow for this visual improvement task. It did not materially change styling, layout, hover, active, glow, spacing, or animation behavior."
                    : subjectiveImprovementNeedsDiff
                      ? "This is a subjective visual improvement task. No diff was produced, so it cannot be marked already satisfied."
                      : "Coder Agent did not provide validated replacement content for backend diff generation. Retry Local Coder with stricter output repair, or copy the manual browser prompt.",
          target: effectiveTarget || explicitTaskTarget || packetTarget || null,
        };
      }
      if (clientRejectedBackendProposedDiff) {
        combinedApprovalPreview = {
          decision: "blocked",
          reason_codes: ["needs_coder_diff", "client_rejected_proposed_diff"],
          requires_human_approval: false,
          safety_message: CLIENT_REJECTED_BACKEND_DIFF_MESSAGE,
          target: effectiveTarget || explicitTaskTarget || packetTarget || null,
        };
      }
      if (initialDiffPreview?.git_apply_check_ok === false) {
        const priorCodes = combinedApprovalPreview?.reason_codes ?? [];
        const applyErr =
          typeof initialDiffPreview.git_apply_check_error === "string" &&
          initialDiffPreview.git_apply_check_error.trim()
            ? initialDiffPreview.git_apply_check_error.trim()
            : "";
        const applyMsg = applyErr
          ? `Stale diff: git apply --check failed (${applyErr}). Regenerate from the current file.`
          : "Stale diff: git apply --check failed on this workspace. Regenerate from the current file.";
        combinedApprovalPreview = {
          decision: "blocked",
          reason_codes: [...priorCodes, "diff_apply_check_failed"],
          requires_human_approval: false,
          safety_message: combinedApprovalPreview?.safety_message
            ? `${combinedApprovalPreview.safety_message} ${applyMsg}`
            : applyMsg,
        };
      }

      setProxyMetrics({
        health: "online",
        route: decision.recommended_route ?? "unknown",
        model: modelLabelForCoderPacket(promptPacket, decisionForOutput, coderReasonCode),
        risk: formatRiskTier(decision.risk_tier),
        tokens: decision.context_estimate?.total_estimated_tokens ?? null,
      });
      const nextApprovalGate: ApprovalGateState = {
        ...approvalGate,
        action:
          alreadySatisfied
            ? "already_satisfied"
            : effectiveProposedDiff || approvalProposal?.content
              ? effectiveAction
              : "needs_coder_diff",
        alreadySatisfied,
        approvedAt: null,
        coderDiagnostics:
          (promptPacket.coder_diagnostics as Record<string, unknown> | undefined) ??
          (promptPacket.coderDiagnostics as Record<string, unknown> | undefined),
        content: effectiveProposedDiff ? "" : approvalProposal?.content ?? "",
        deniedAt: null,
        error: null,
        execution: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked,
        fallbackScaffoldGenerated,
        isChecking: false,
        preview: combinedApprovalPreview,
        proposedDiff: effectiveProposedDiff,
        target: effectiveTarget,
      };
      setApprovalGate((current) => ({
        ...current,
        ...nextApprovalGate,
      }));
      setDiffVerification({
        error: null,
        isChecking: false,
        preview: initialDiffPreview,
        unifiedDiff: effectiveProposedDiff,
      });
      setLongRunningTask((current) =>
        deriveTerminalLongTaskStateForApproval(nextApprovalGate, {
          ...current,
          response: current.response ?? trackedTask,
        }),
      );
      void refreshTelemetry();
      const finalPromptText = promptTextForCoderPacket({
        coderBlocked,
        coderBlockedReason,
        coderDiffReady,
        coderNeededContext,
        promptText: promptPacket.prompt_text,
      });
      setFinalOutput({
        attachedFiles,
        completedAt: new Date().toISOString(),
        contextTurnCount: priorTurns.length,
        decision: decisionForOutput,
        decisionPayload: JSON.stringify(decisionForOutput, null, 2),
        coderAgentLocalDiff: coderDiffReady,
        fallbackScaffoldBlocked,
        promptText: finalPromptText,
        researchSources,
        requests: promptPacket.requests_for_more_information ?? [],
        runId,
        selfCorrection,
        summary: buildDecisionSummary({
          attachedFiles,
          decision: decisionForOutput,
          memoryEntries,
          promptPacket,
          priorTurns,
          runId,
          researchSources,
          submittedTask: task,
        }),
      });
      setConversationHistory((currentHistory) =>
        addCodingHistoryEntry(
          currentHistory,
          buildCodingHistoryEntry({
            attachedFiles,
            completedAt: new Date().toISOString(),
            decision: decisionForOutput,
            memoryEntries,
            promptText: finalPromptText,
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
          label: coderDiffReady
            ? "Unified diff ready"
            : clientRejectedBackendProposedDiff
              ? "Backend diff rejected"
              : "No approvable diff",
          detail: coderDiffReady
            ? `Unified diff and target are ready for the approval gate (${workflowContextLabel(promptPacket, task)}).`
            : clientRejectedBackendProposedDiff
              ? CLIENT_REJECTED_BACKEND_DIFF_MESSAGE
              : NO_APPROVABLE_DIFF_NEXT_ACTION,
          level: coderDiffReady ? "success" : "warning",
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
            submittedTask: task,
          }),
          level: "success",
        },
      );

      setProcessLogs((currentLogs) => [...currentLogs, ...nextLogs]);
    } catch (error) {
      const message = friendlyRunErrorMessage(
        error instanceof Error ? error.message : "Unknown agent service error.",
      );
      if (isProxyFeatureFlagOff(message)) {
        runMockProxyFlow(task, priorTurns, memoryEntries);
        return;
      }

      const partialDecision = lastRouteDecisionRef.current;
      const invalidSummary = `${ROUTE_RESPONSE_INVALID_PREFIX}${message}`;

      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: 2,
          label: partialDecision ? "Run failed after route decision" : "Proxy unavailable - no implementation diff generated",
          detail: partialDecision
            ? `${message} See summary in Research / Plan.`
            : `${message} No client synthetic diff was generated.`,
          level: "warning",
        },
      ]);
      setApprovalGate((current) => ({
        ...current,
        preview: partialDecision
          ? {
              decision: "blocked",
              reason_codes: ["route_response_invalid"],
              requires_human_approval: false,
              safety_message: message,
              target: null,
            }
          : current.preview,
      }));
      setFinalOutput({
        attachedFiles: partialDecision ? attachedFiles : [],
        completedAt: new Date().toISOString(),
        contextTurnCount: priorTurns.length,
        decision: partialDecision ?? {},
        decisionPayload: partialDecision
          ? JSON.stringify(partialDecision, null, 2)
          : message,
        promptText: "",
        researchSources: [],
        requests: [
          partialDecision
            ? "Fix the failing step (research preview, long-running sync, prompt packet, or diff preview), then retry."
            : "Confirm SPIRIT_CODING_USE_PROXY=true and restart the dev server",
          ...(partialDecision ? [] : ["Re-run the task after the Source proxy is reachable"]),
        ],
        runId,
        selfCorrection: {
          checks: [],
          confidence: 0,
          reasons: [message],
          refinedInstruction: partialDecision
            ? "The route decision succeeded; a later step failed. Check the activity log for the first error after 'Route decision received'."
            : "Verify the Source proxy is enabled and reachable before continuing this task.",
          triggered: true,
        },
        summary: partialDecision ? invalidSummary : "Proxy unavailable - no implementation diff generated. Check that the Source proxy is running, then run the task again.",
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
        health: partialDecision ? "online" : "offline",
        route: partialDecision
          ? String(partialDecision.recommended_route ?? "request failed")
          : "request failed",
        model: "not returned",
        risk: partialDecision ? formatRiskTier(partialDecision.risk_tier) : "not returned",
        tokens: partialDecision?.context_estimate?.total_estimated_tokens ?? null,
      });
    } finally {
      isRunningRef.current = false;
      setIsRunning(false);
      setLongRunningTask((current) => ({
        ...current,
        isChecking: false,
      }));
    }
  }

  async function syncArchitectPlanForSubmittedTask(
    task: string,
    activeResponse: LongRunningTaskResponse | null,
  ): Promise<LongRunningTaskResponse> {
    let response = activeResponse ?? (await callLongRunningTaskCreate(task));
    setLongRunningTask((current) => ({
      ...current,
      description: task,
      error: null,
      isChecking: false,
      response,
    }));

    const status = response.task.architect_status ?? "";
    if (
      normalizeLongTaskRole(response.task.current_agent_role) === "architect" &&
      status !== "planned" &&
      status !== "awaiting_llm" &&
      status !== "blocked"
    ) {
      response = await callLongRunningTaskAdvance(response.task.id);
      setLongRunningTask((current) => ({
        ...current,
        description: task,
        error: null,
        isChecking: false,
        response,
      }));
    }

    if (response.task.architect_status === "planned") {
      try {
        setArchitectPlan(await callLongRunningTaskPlan(response.task.id));
      } catch {
        setArchitectPlan(null);
      }
    }
    return response;
  }

  function applyDiscoveryWorkspaceForTask(
    description: string,
    options?: { clearProposal?: boolean },
  ) {
    const clearProposal = options?.clearProposal !== false;
    if (clearProposal) {
      setApprovalGate({
        action: "",
        alreadySatisfied: false,
        approvedAt: null,
        coderDiagnostics: undefined,
        content: "",
        deniedAt: null,
        error: null,
        execution: null,
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
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
        fallbackScaffoldAccepted: false,
        fallbackScaffoldBlocked: false,
        fallbackScaffoldGenerated: false,
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
    lastSubmittedTaskRef.current = "";
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

  function restoreHistoryEntry(entry: CodingHistoryEntry) {
    const restoredTask = entry.task.trim();
    if (!restoredTask) {
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Restore skipped",
          detail: `Run #${entry.runId} did not include a restorable prompt.`,
          level: "warning",
        },
      ]);
      return;
    }

    setInputText(restoredTask);
    setFinalOutput(null);
    setWorkflowStepFloor(1);
    lastSubmittedTaskRef.current = "";
    const restoredPlan = restoredArchitectPlanForHistoryEntry(entry);
    if (restoredPlan) {
      setArchitectPlan(restoredPlan);
      setApprovalGate((current) => ({
        ...current,
        target: architectTargetPath(restoredPlan),
      }));
    }
    applyDiscoveryWorkspaceForTask(restoredTask, { clearProposal: !restoredPlan });
    setLongRunningTask((current) => ({
      description: restoredTask,
      error: null,
      isChecking: false,
      response: null,
    }));
    setProcessLogs((currentLogs) => [
      ...currentLogs,
      {
        id: Date.now(),
        label: "Prompt restored",
        detail: `Restored Run #${entry.runId}. Review the task text, then submit when ready.`,
        level: "success",
      },
    ]);
  }

  async function copyHistoryRecoveryPrompt(entry: CodingHistoryEntry) {
    const restoredPlan = restoredArchitectPlanForHistoryEntry(entry);
    const prompt =
      entry.recoveryPrompt ||
      manualBrowserPromptForCurrentState({
        architectPlan: restoredPlan ?? architectPlan,
        currentTask: entry.task,
        promptText: "",
        target: approvalGate.target || architectTargetPath(restoredPlan),
      });
    try {
      await navigator.clipboard.writeText(
        ["# Copy manual browser prompt", prompt].join("\n").trim(),
      );
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Manual browser prompt copied",
          detail: `Copied recovery prompt for Run #${entry.runId}. Paste it into GPT/Gemini/Grok/Claude, not into the SpiritOS task box.`,
          level: "success",
        },
      ]);
    } catch (error) {
      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: Date.now(),
          label: "Copy failed",
          detail: error instanceof Error ? error.message : "Clipboard unavailable.",
          level: "warning",
        },
      ]);
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
    const approvalProposal = deriveApprovalGateProposal(mockDecision, mockPacket, {
      currentTaskText: task,
    });
    setApprovalGate((current) => ({
      ...current,
      action: approvalProposal?.action ?? "",
      approvedAt: null,
      content: approvalProposal?.content ?? "",
      deniedAt: null,
      error: null,
      execution: null,
      fallbackScaffoldAccepted: false,
      fallbackScaffoldBlocked: false,
      fallbackScaffoldGenerated: false,
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
      fallbackScaffoldBlocked: false,
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
        submittedTask: task,
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
          promptText: mockPacket.prompt_text,
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
              architectPlan={architectPlan}
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
                setApprovalGate((current) => ({
                  ...current,
                  action,
                  fallbackScaffoldAccepted: false,
                }))
              }
              onApprovalContentChange={(content) =>
                setApprovalGate((current) => ({
                  ...current,
                  content,
                  fallbackScaffoldAccepted: false,
                }))
              }
              onApprovalTargetChange={(target) =>
                setApprovalGate((current) => ({
                  ...current,
                  target,
                  fallbackScaffoldAccepted: false,
                }))
              }
              onApprovePreviewedAction={approvePreviewedAction}
              onClearHistory={() => setConversationHistory([])}
              onClearMemory={() => setDecisionMemory([])}
              onDenyPreviewedAction={denyPreviewedAction}
              onDiffChange={(unifiedDiff) =>
                {
                  setDiffVerification((current) => ({ ...current, unifiedDiff }));
                  setApprovalGate((current) => ({
                    ...current,
                    fallbackScaffoldAccepted: false,
                  }));
                }
              }
              onFallbackScaffoldAcceptedChange={(accepted) =>
                setApprovalGate((current) => ({
                  ...current,
                  fallbackScaffoldAccepted: accepted,
                }))
              }
              onTrackedDiffSelect={loadTrackedDiffForVerification}
              onLongTaskCancel={cancelLongRunningTask}
              onLongTaskDescriptionChange={(description) =>
                setLongRunningTask((current) => ({ ...current, description }))
              }
              onLongTaskPoll={pollLongRunningTask}
              onLongTaskStart={startLongRunningTask}
              onLongTaskVerifyCode={verifyCodeLongRunningTask}
              onLongTaskVerifyDocsOnly={verifyDocsOnlyLongRunningTask}
              onInputChange={setInputText}
              onFilesAdded={(files) => setUploadedFiles((current) => [...current, ...files])}
              onPreviewApprovalGate={previewApprovalGate}
              onPreviewDiffVerification={previewDiffVerification}
              onPreviewManualResult={previewManualResult}
              onCopyHistoryRecoveryPrompt={copyHistoryRecoveryPrompt}
              onRestoreHistoryEntry={restoreHistoryEntry}
              onRunProxyFlow={runProxyFlow}
              onStartNewTask={startNewCodingTask}
              onSubmit={runProxyFlow}
              telemetry={telemetry}
              workflowStepFloor={workflowStepFloor}
            />
          </section>
        </div>
      </div>

      {toastMessage ? (
        <div className="fixed right-4 top-4 z-50 max-w-sm border border-green-300 bg-green-50 px-4 py-3 text-sm font-semibold text-green-950 shadow-lg">
          {toastMessage}
        </div>
      ) : null}

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

type CodingStabilityPrimaryState =
  | "Idle"
  | "Routing"
  | "Planning"
  | "Diff ready"
  | "Blocked"
  | "Needs approval"
  | "Applying"
  | "Applied, verification required"
  | "Verification ready"
  | "Verified"
  | "Done"
  | "Failed";

type CodingStabilitySummary = {
  approvalState: string;
  diffState: string;
  executionState: string;
  lastBlocker: string | null;
  primaryState: CodingStabilityPrimaryState;
  streamState: string;
  target: string;
  verificationState: string;
};

export function deriveCodingStabilitySummary({
  approvalGate,
  architectPlan,
  diffVerification,
  finalOutput,
  isRunning,
  logs = [],
  longRunningTask,
}: {
  approvalGate: ApprovalGateState;
  architectPlan?: ArchitectPlanResponse | null;
  diffVerification: DiffVerificationState;
  finalOutput: FinalOutput | null;
  isRunning: boolean;
  logs?: ProcessLog[];
  longRunningTask: LongRunningTaskState;
}): CodingStabilitySummary {
  const task = longRunningTask.response?.task;
  const taskStatus = task?.status ?? "";
  const postApplyVerification =
    task?.post_apply_verification ?? approvalGate.execution?.post_apply_verification ?? null;
  const reasonCodes = [
    ...(approvalGate.preview?.reason_codes ?? []),
    ...(finalOutput?.decision.reason_codes ?? []),
  ];
  const targetUnresolved =
    reasonCodes.includes("target_unresolved") || reasonCodes.includes("target_missing");
  const verificationFailed = isVerificationFailedStatus(taskStatus, postApplyVerification);
  const blocker =
    firstStabilityBlocker(reasonCodes) ??
    noDiffTerminalReason(taskStatus) ??
    (verificationFailed ? "verification_failed" : null) ??
    (diffVerification.preview?.git_apply_check_error ? "git_apply_check_failed" : null);
  const target = targetUnresolved
    ? "No target resolved"
    : firstNonEmpty([
        approvalGate.target,
        resolvedTargetPathFromDecision(finalOutput?.decision),
        architectTargetPath(architectPlan),
        firstTaskDiffPath(task),
      ]) ?? "No target resolved";
  const hasDiff =
    approvalGate.proposedDiff.trim().length > 0 ||
    diffVerification.unifiedDiff.trim().length > 0 ||
    approvalGate.content.trim().length > 0 ||
    Boolean(task?.open_diffs?.some((diff) => typeof diff.diff === "string" && diff.diff.trim()));
  const previewReady =
    diffVerification.preview?.status === "preview_ready" ||
    diffVerification.preview?.would_apply_diff === true ||
    diffVerification.preview?.git_apply_check_ok === true;
  const clientRejected = reasonCodes.includes("client_rejected_proposed_diff");
  const reviewerBlocked =
    approvalGate.preview?.decision === "blocked" ||
    diffVerification.preview?.review_report?.passed === false ||
    diffVerification.preview?.llm_review_report?.passed === false;
  const needsCoderDiff =
    approvalGate.action === "needs_coder_diff" ||
    approvalGate.preview?.decision === "needs_coder_diff" ||
    reasonCodes.includes("needs_coder_diff");
  const approvalRequired =
    approvalGate.preview?.requires_human_approval === true ||
    approvalGate.preview?.decision === "requires_human_approval";
  const approved = Boolean(approvalGate.approvedAt);
  const alreadySatisfied = isAlreadySatisfiedGate(approvalGate);

  const diffState = clientRejected
    ? "client rejected diff"
    : reviewerBlocked
      ? "reviewer blocked"
      : previewReady
        ? "preview ready"
        : hasDiff
          ? "diff ready"
          : needsCoderDiff
            ? "no approvable diff"
            : "no diff";

  const approvalState = alreadySatisfied
    ? "passing"
    : approved
      ? "approved"
      : clientRejected || needsCoderDiff || targetUnresolved || reviewerBlocked
        ? "unavailable"
        : approvalRequired
          ? "requires human approval"
          : approvalGate.preview
            ? "passing"
            : "blocked";

  const executionState =
    isVerificationCompleteState(task, approvalGate.execution) || alreadySatisfied
      ? "verified / completed"
      : taskStatus === "applied_needs_verification" ||
          postApplyVerification?.status === "verification_ready"
        ? "applied_needs_verification"
        : verificationFailed || taskStatus === "failed_needs_human"
          ? "failed"
          : taskStatus === "executing" || approved || longRunningTask.isChecking
            ? "applying"
            : "not started";

  const verificationState = deriveVerificationState(postApplyVerification, taskStatus);
  const streamState = deriveStreamState(logs, taskStatus, task?.id);

  let primaryState: CodingStabilityPrimaryState = "Idle";
  if (alreadySatisfied) {
    primaryState = "Done";
  } else if (isVerificationCompleteState(task, approvalGate.execution)) {
    primaryState = postApplyVerification?.status === "verified" ? "Done" : "Done";
  } else if (postApplyVerification?.status === "verified") {
    primaryState = "Verified";
  } else if (taskStatus === "applied_needs_verification") {
    primaryState = "Applied, verification required";
  } else if (postApplyVerification?.status === "verification_ready") {
    primaryState = "Verification ready";
  } else if (
    verificationFailed ||
    taskStatus === "failed_needs_human" ||
    diffVerification.error
  ) {
    primaryState = "Failed";
  } else if (approvalRequired) {
    primaryState = "Needs approval";
  } else if (clientRejected || needsCoderDiff || targetUnresolved || reviewerBlocked || isNoDiffTerminalLongTaskStatus(taskStatus)) {
    primaryState = "Blocked";
  } else if (previewReady || hasDiff) {
    primaryState = "Diff ready";
  } else if (taskStatus === "executing" || approved || longRunningTask.isChecking) {
    primaryState = "Applying";
  } else if (isRunning) {
    primaryState = finalOutput ? "Planning" : "Routing";
  } else if (finalOutput) {
    primaryState = "Planning";
  }

  return {
    approvalState,
    diffState,
    executionState,
    lastBlocker: blocker,
    primaryState,
    streamState,
    target,
    verificationState,
  };
}

export function workflowStep({
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
  const taskStatus = longRunningTask.response?.task.status;
  const task = longRunningTask.response?.task;
  const postApplyVerification = task?.post_apply_verification ?? approvalGate.execution?.post_apply_verification;
  const alreadySatisfied = isAlreadySatisfiedGate(approvalGate);
  const needsCoderDiff =
    approvalGate.action === "needs_coder_diff" ||
    approvalGate.preview?.decision === "needs_coder_diff" ||
    approvalGate.preview?.reason_codes?.includes("needs_coder_diff") === true;
  if (alreadySatisfied) {
    return 7;
  }
  if (finalOutput?.summary?.startsWith(ROUTE_RESPONSE_INVALID_PREFIX)) {
    return 2;
  }
  if (
    isVerificationCompleteState(task, approvalGate.execution) ||
    taskStatus === "completed" ||
    taskStatus === "verified" ||
    taskStatus === "done"
  ) {
    return 7;
  }
  if (
    taskStatus === "applied_needs_verification" ||
    taskStatus === "applied_verification_failed" ||
    taskStatus === "verification_failed" ||
    postApplyVerification?.status === "verification_failed" ||
    postApplyVerification?.status === "verification_ready" ||
    postApplyVerification?.status === "manual_verification_required"
  ) {
    return 6;
  }
  if (approvalGate.approvedAt || taskStatus === "executing") {
    return 5;
  }
  if (needsCoderDiff) {
    return 3;
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

function isAlreadySatisfiedGate(gate: ApprovalGateState): boolean {
  return (
    gate.alreadySatisfied ||
    gate.action === "already_satisfied" ||
    gate.preview?.decision === "already_satisfied" ||
    gate.preview?.reason_codes?.includes("coder_no_changes_needed") === true
  );
}

function postApplyVerificationFor(
  task?: LongRunningTaskPayload | null,
  execution?: ApprovedActionExecutionResponse | null,
): PostApplyVerification | null {
  return task?.post_apply_verification ?? execution?.post_apply_verification ?? null;
}

function isPostApplyOrDoneState(
  task?: LongRunningTaskPayload | null,
  execution?: ApprovedActionExecutionResponse | null,
): boolean {
  const status = task?.status ?? "";
  const verification = postApplyVerificationFor(task, execution);
  return (
    execution?.ok === true ||
    status === "applied_needs_verification" ||
    status === "verification_failed" ||
    status === "verification_ready" ||
    status === "verified" ||
    status === "completed" ||
    status === "done" ||
    verification?.status === "verification_ready" ||
    verification?.status === "manual_verification_required" ||
    verification?.status === "verified"
  );
}

function isPostApplyVerificationPending(
  task?: LongRunningTaskPayload | null,
  execution?: ApprovedActionExecutionResponse | null,
): boolean {
  const status = task?.status ?? "";
  const verification = postApplyVerificationFor(task, execution);
  if (isVerificationCompleteState(task, execution)) {
    return false;
  }
  return (
    status === "applied_needs_verification" ||
    status === "verification_ready" ||
    verification?.status === "verification_ready" ||
    verification?.status === "manual_verification_required"
  );
}

function isVerificationCompleteState(
  task?: LongRunningTaskPayload | null,
  execution?: ApprovedActionExecutionResponse | null,
): boolean {
  const status = task?.status ?? "";
  const verification = postApplyVerificationFor(task, execution);
  return (
    status === "completed" ||
    status === "verified" ||
    status === "done" ||
    verification?.status === "verified"
  );
}

function firstNonEmpty(values: Array<string | null | undefined>): string | null {
  for (const value of values) {
    const normalized = normalizeRepoRelativePath(value ?? "");
    if (normalized) {
      return normalized;
    }
  }
  return null;
}

function firstTaskDiffPath(task: LongRunningTaskPayload | null | undefined): string {
  const changedFile = task?.open_diffs?.[0]?.changed_files?.find((file) => file.path?.trim());
  return normalizeRepoRelativePath(changedFile?.path ?? "");
}

function firstStabilityBlocker(reasonCodes: string[]): string | null {
  const priority = [
    "target_unresolved",
    "target_missing",
    "client_rejected_proposed_diff",
    "needs_coder_diff",
    "review_literal_acceptance_missing",
    "coder_packet_missing_context",
    "git_apply_check_timeout",
    "git_apply_check_failed",
    "diff_apply_check_failed",
    "target_mismatch_stale_diff",
    "coder_sync_timeout",
    "coder_proxy_deadline_blocked",
    "route_response_invalid",
  ];
  return priority.find((reason) => reasonCodes.includes(reason)) ?? reasonCodes[0] ?? null;
}

function noDiffTerminalReason(status: string): string | null {
  if (status === "blocked_no_valid_diff" || status === "needs_coder_diff") {
    return "needs_coder_diff";
  }
  if (status === "coder_diff_rejected") {
    return "client_rejected_proposed_diff";
  }
  if (
    status === "blocked" ||
    status === "coder_config_blocked" ||
    status === "failed_needs_human" ||
    status === "needs_context"
  ) {
    return status;
  }
  return null;
}

function deriveVerificationState(
  verification: PostApplyVerification | null | undefined,
  taskStatus: string,
): string {
  if (isVerificationFailedStatus(taskStatus, verification)) {
    return "failed";
  }
  if (verification?.status === "verified" || taskStatus === "completed") {
    return "verified";
  }
  if (verification?.skip_reason) {
    return `skipped with reason: ${verification.skip_reason}`;
  }
  if (verification?.status === "verification_ready") {
    return "verification ready";
  }
  if (verification?.status === "manual_verification_required") {
    return "manual verification required";
  }
  if (verification?.required || taskStatus === "applied_needs_verification") {
    return "needs verification";
  }
  return "not required";
}

function isVerificationFailedStatus(
  taskStatus?: string,
  verification?: PostApplyVerification | null,
): boolean {
  return (
    taskStatus === "applied_verification_failed" ||
    taskStatus === "verification_failed" ||
    verification?.status === "failed" ||
    verification?.status === "verification_failed"
  );
}

function deriveStreamState(logs: ProcessLog[], taskStatus: string, taskId?: string): string {
  if (!taskId) {
    return "disconnected/unknown";
  }
  const taskStreamLogs = logs.filter((log) => log.label === "Task stream");
  const latest = taskStreamLogs[taskStreamLogs.length - 1]?.detail ?? "";
  if (latest.includes("polling task status")) {
    return "polling fallback";
  }
  if (latest.includes("Live task updates connected")) {
    return "SSE connected";
  }
  if (isTerminalLongTaskStatus(taskStatus)) {
    return "disconnected/unknown";
  }
  return "disconnected/unknown";
}

function architectTargetPath(plan: ArchitectPlanResponse | null | undefined): string {
  return normalizeRepoRelativePath(plan?.coder_packet?.target_file?.path ?? "");
}

function workflowBlockedStep({
  approvalGate,
  longRunningTask,
}: {
  approvalGate: ApprovalGateState;
  longRunningTask: LongRunningTaskState;
}): number | null {
  const task = longRunningTask.response?.task;
  const reasonCodes = approvalGate.preview?.reason_codes ?? [];
  const coderBlocked =
    task?.status === "blocked" &&
    (task.current_agent_role === "coder" ||
      reasonCodes.some((code) => code.startsWith("coder_") || code === "needs_coder_diff"));
  const blockedBeforeDiff =
    coderBlocked &&
    !approvalGate.proposedDiff.trim() &&
    !approvalGate.content.trim();
  return blockedBeforeDiff ? 3 : null;
}

function workflowStages(activeStep: number, blockedStep: number | null = null): WorkflowStageItem[] {
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
        blockedStep === step
          ? "blocked"
          :
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
              stage.status === "blocked"
                ? "border-red-300 bg-red-400/10 text-red-100"
                : stage.status === "active"
                ? "border-cyan-300 bg-cyan-300/10 text-white"
                : stage.status === "complete"
                  ? "border-green-400/50 bg-green-400/10 text-green-100"
                  : "border-slate-700 bg-slate-900 text-slate-400"
            }`}
            key={stage.index}
          >
            <span
              className={`grid h-7 w-7 shrink-0 place-items-center rounded-full border text-xs font-bold ${
                stage.status === "blocked"
                  ? "border-red-300 text-red-100"
                  : stage.status === "active"
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
        <WorkflowBadge tone={status === "complete" ? "success" : status === "active" ? "warning" : status === "blocked" ? "danger" : "muted"}>
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
  tone: "danger" | "info" | "muted" | "success" | "warning";
}) {
  const className =
    tone === "success"
      ? "border-green-300 bg-green-50 text-green-900"
      : tone === "warning"
        ? "border-yellow-300 bg-yellow-50 text-yellow-900"
        : tone === "danger"
          ? "border-red-300 bg-red-50 text-red-900"
        : tone === "info"
          ? "border-cyan-300 bg-cyan-50 text-cyan-900"
          : "border-slate-300 bg-slate-50 text-slate-700";
  return (
    <span className={`inline-flex shrink-0 border px-2 py-1 text-xs font-semibold ${className}`}>
      {children}
    </span>
  );
}

export function CodingStabilityCard({ summary }: { summary: CodingStabilitySummary }) {
  const tone = codingStabilityTone(summary.primaryState);
  const fields = [
    ["Target", summary.target],
    ["Diff", summary.diffState],
    ["Approval", summary.approvalState],
    ["Execution", summary.executionState],
    ["Verification", summary.verificationState],
    ["Stream", summary.streamState],
  ];
  return (
    <section className="border-b border-slate-300 bg-white px-4 py-3 shadow-sm">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex min-w-[13rem] flex-col gap-1">
          <div className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
            Current workflow state
          </div>
          <WorkflowBadge tone={tone}>{summary.primaryState}</WorkflowBadge>
        </div>
        <dl className="grid flex-1 grid-cols-1 gap-2 text-xs sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {fields.map(([label, value]) => (
            <div className="min-w-0 border border-slate-200 bg-slate-50 px-3 py-2" key={label}>
              <dt className="font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
              <dd className="mt-1 truncate font-medium text-slate-950" title={value}>
                {value}
              </dd>
            </div>
          ))}
        </dl>
      </div>
      {summary.lastBlocker ? (
        <div className="mt-2 inline-flex max-w-full border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-950">
          <span className="mr-2 shrink-0 text-red-700">Last blocker</span>
          <span className="truncate" title={summary.lastBlocker}>
            {summary.lastBlocker}
          </span>
        </div>
      ) : null}
    </section>
  );
}

function codingStabilityTone(
  state: CodingStabilityPrimaryState,
): "danger" | "info" | "muted" | "success" | "warning" {
  if (state === "Done" || state === "Verified") {
    return "success";
  }
  if (state === "Blocked" || state === "Failed") {
    return "danger";
  }
  if (
    state === "Needs approval" ||
    state === "Applied, verification required" ||
    state === "Verification ready"
  ) {
    return "warning";
  }
  if (state === "Idle") {
    return "muted";
  }
  return "info";
}

function EmptyWorkflowMessage({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600">
      {text}
    </div>
  );
}

function ProposalSummaryPanel({ gate }: { gate: ApprovalGateState }) {
  const alreadySatisfied = isAlreadySatisfiedGate(gate);
  const needsCoderDiff =
    !alreadySatisfied &&
    (gate.action === "needs_coder_diff" ||
      gate.preview?.decision === "needs_coder_diff" ||
      gate.preview?.reason_codes?.includes("needs_coder_diff") === true);
  const subjectiveImprovementNeedsDiff =
    gate.preview?.reason_codes?.includes(SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE) ===
      true ||
    gate.preview?.reason_codes?.includes(VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE) ===
      true;
  const shallowVisualDiff =
    gate.preview?.reason_codes?.includes(VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE) ===
    true;
  const bundleSnapshotDrift =
    gate.preview?.reason_codes?.includes(BUNDLE_SNAPSHOT_DRIFT_REASON_CODE) === true;
  const clientRejectedBackendDiff =
    gate.preview?.reason_codes?.includes("client_rejected_proposed_diff") === true;
  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Proposed Change</h2>
        <WorkflowBadge tone={gate.proposedDiff || gate.content || alreadySatisfied ? "success" : "muted"}>
          {alreadySatisfied
            ? "already_satisfied"
            : gate.proposedDiff
            ? "diff ready"
            : gate.content
              ? "content ready"
              : needsCoderDiff
                ? "needs coder diff"
                : "needs diff"}
        </WorkflowBadge>
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <TelemetryStat label="Action" value={gate.action || "No action proposed"} />
        <TelemetryStat label="Target" value={gate.target || "No target proposed"} />
      </div>
      {needsCoderDiff ? (
        <div className="mt-3 border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-950">
          {shallowVisualDiff
            ? "The generated diff was too shallow for this visual improvement task. It did not materially change styling, layout, hover, active, glow, spacing, or animation behavior."
            : subjectiveImprovementNeedsDiff
            ? "This is a subjective visual improvement task. No diff was produced, so it cannot be marked already satisfied."
            : bundleSnapshotDrift
            ? "Bundle changed since the Architect plan was created. Regenerate the plan, then retry Coder Agent."
            : clientRejectedBackendDiff
              ? CLIENT_REJECTED_BACKEND_DIFF_MESSAGE
              : `${NO_APPROVABLE_DIFF_MESSAGE} ${NO_APPROVABLE_DIFF_NEXT_ACTION}`}
        </div>
      ) : null}
      {alreadySatisfied ? (
        <div className="mt-3 border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-950">
          No code change is needed. The target file already satisfies this task.
        </div>
      ) : null}
      {gate.proposedDiff ? (
        <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap border border-slate-200 bg-slate-50 p-3 font-mono text-xs leading-5 text-slate-800">
          {gate.proposedDiff}
        </pre>
      ) : null}
    </section>
  );
}

export function VerificationSummary({
  diffVerification,
  execution,
  isVerifying,
  longRunningTask,
  onCodeVerify,
  onDocsOnlyVerify,
}: {
  diffVerification: DiffVerificationState;
  execution: ApprovedActionExecutionResponse | null;
  isVerifying: boolean;
  longRunningTask: LongRunningTaskState;
  onCodeVerify?: () => void;
  onDocsOnlyVerify: () => void;
}) {
  const task = longRunningTask.response?.task ?? null;
  const suggested =
    execution?.verification_plan ??
    diffVerification.preview?.verification_plan ??
    task?.open_diffs?.[0]?.suggested_commands?.map(
      (item) => item.reason,
    ) ??
    [];
  const commands =
    diffVerification.preview?.suggested_commands ??
    task?.open_diffs?.[0]?.suggested_commands ??
    [];
  const postApplyVerification = postApplyVerificationFor(task, execution);
  const docsOnlyConfirmations = postApplyVerification?.docs_only_confirmations;
  const verificationComplete = isVerificationCompleteState(task, execution);
  const verificationPending = isPostApplyVerificationPending(task, execution);
  const docsOnlyComplete =
    Boolean(docsOnlyConfirmations?.file_changed_as_expected) &&
    Boolean(docsOnlyConfirmations?.no_unintended_files) &&
    Boolean(docsOnlyConfirmations?.backup_audit_present);
  const canCompleteDocsOnly =
    postApplyVerification?.docs_only === true &&
    !verificationComplete &&
    task?.status === "applied_needs_verification";
  const unsupportedCodeVerification =
    postApplyVerification?.unsupported_code_verification === true ||
    postApplyVerification?.status === "manual_verification_required";
  const codeVerificationFlow =
    postApplyVerification &&
    postApplyVerification.docs_only === false &&
    !unsupportedCodeVerification;
  const codeVerificationRequired =
    Boolean(codeVerificationFlow) &&
    verificationPending &&
    !isVerificationFailedStatus(task?.status, postApplyVerification);
  const codeVerificationComplete =
    Boolean(codeVerificationFlow) &&
    (postApplyVerification?.status === "verified" || verificationComplete);
  const verificationFailed = isVerificationFailedStatus(task?.status, postApplyVerification);
  const displaySummary = buildPostApplyVerificationDisplaySummary({
    diffVerification,
    execution,
    postApplyVerification,
    task,
  });
  const showPrimaryVerificationPlan = !postApplyVerification;
  const advancedSnapshot = parseLongTaskVerificationSnapshot(task);
  const advancedVerificationPayload = postApplyVerification
    ? {
        post_apply_verification: postApplyVerification,
        snapshot: advancedSnapshot,
        truncated_test_results:
          task?.truncated_test_results && !advancedSnapshot ? task.truncated_test_results : undefined,
      }
    : null;
  const verificationBadge = verificationComplete
    ? "verified"
    : verificationPending
      ? "Applied, verification required"
      : execution?.ok
        ? "verification_ready"
        : "waiting";
  const primaryInstruction = verificationComplete
    ? "Post-apply verification is complete."
    : unsupportedCodeVerification
      ? "Manual verification is required because this file type is not supported by Phase 2B automation."
      : "The approved diff has been applied. Review the changed file and backup, then mark verification complete.";

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Verification Plan</h2>
        <WorkflowBadge tone={verificationComplete ? "success" : verificationPending || execution?.ok ? "warning" : "muted"}>
          {verificationBadge}
        </WorkflowBadge>
      </div>
      {postApplyVerification ? (
        <p className="mt-3 text-sm leading-6 text-slate-700">{primaryInstruction}</p>
      ) : null}
      {verificationPending && postApplyVerification?.docs_only ? (
        <div className="mt-3 border border-yellow-300 bg-yellow-50 px-4 py-3 text-sm text-yellow-950">
          <div className="font-semibold">Next step: complete docs-only verification</div>
          <div className="mt-1">
            Confirm the changed file, unintended-file check, and backup/audit evidence below.
          </div>
        </div>
      ) : null}
      {postApplyVerification ? (
        <div className="mt-3 space-y-2 border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-950">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <h3 className="font-semibold">Post-Apply Verification</h3>
            <span className="border border-yellow-400 bg-white px-2 py-1 text-xs font-semibold">
              {postApplyVerification.status ?? "verification_ready"}
            </span>
          </div>
          {codeVerificationRequired ? (
            <div className="border border-yellow-200 bg-white px-3 py-2 text-sm">
              <div className="font-semibold text-slate-950">Code verification required</div>
            </div>
          ) : null}
          {codeVerificationComplete ? (
            <div className="border border-green-200 bg-white px-3 py-2 text-sm font-semibold text-green-800">
              Code verification complete
            </div>
          ) : null}
          {verificationFailed ? (
            <div className="border border-red-200 bg-white px-3 py-2 text-sm font-semibold text-red-800">
              Verification failed
            </div>
          ) : null}
          {unsupportedCodeVerification ? (
            <div className="border border-yellow-200 bg-white px-3 py-2 text-sm text-slate-700">
              <div className="font-semibold text-slate-950">
                Manual verification required / unsupported code verification type
              </div>
              {postApplyVerification.unsupported_file_types?.length ? (
                <div className="mt-1">
                  Unsupported types: {postApplyVerification.unsupported_file_types.join(", ")}
                </div>
              ) : null}
            </div>
          ) : null}
          <div className="grid gap-2 md:grid-cols-3">
            <TelemetryStat
              label={displaySummary.changedFiles.length === 1 ? "Changed file" : "Changed files"}
              value={
                displaySummary.changedFiles.length > 0
                  ? displaySummary.changedFiles.join(", ")
                  : "Not reported yet"
              }
            />
            <TelemetryStat label="Backup" value={displaySummary.backupRoot} />
            <TelemetryStat label="Risk" value={displaySummary.risk} />
          </div>
          {postApplyVerification.checks?.length ? (
            <div className="space-y-2">
              {postApplyVerification.checks.map((check) => (
                <div
                  className="border border-yellow-200 bg-white px-3 py-2 text-sm"
                  key={check.id ?? verificationCommandLabel(check) ?? check.summary}
                >
                  <div className="font-mono text-slate-900">
                    {verificationCommandLabel(check)}
                  </div>
                  <div className="mt-1 text-slate-700">
                    {isVerifying && (check.status ?? "pending") === "pending"
                      ? "running"
                      : check.status ?? "pending"}
                    {check.required ? " | required" : ""}
                    {check.summary ? ` | ${check.summary}` : ""}
                    {typeof check.exit_code === "number" ? ` | exit ${check.exit_code}` : ""}
                    {typeof check.duration_ms === "number" ? ` | ${check.duration_ms}ms` : ""}
                  </div>
                  {check.output_tail ? (
                    <pre className="mt-2 max-h-44 overflow-auto whitespace-pre-wrap border border-slate-200 bg-slate-50 p-2 text-xs leading-5 text-slate-700">
                      {check.output_tail}
                    </pre>
                  ) : null}
                </div>
              ))}
            </div>
          ) : null}
          {postApplyVerification.manual_browser_check_required ? (
            <div className="border border-yellow-200 bg-white px-3 py-2 text-sm">
              Manual browser check required
              {postApplyVerification.manual_browser_check_done ? ": done" : ": pending"}
            </div>
          ) : null}
          {postApplyVerification.docs_only ? (
            <div className="space-y-2 border border-yellow-200 bg-white px-3 py-2 text-sm">
              <div className="font-semibold text-slate-950">Complete docs-only verification</div>
              <ul className="space-y-1 text-slate-700">
                <li>
                  {docsOnlyConfirmations?.file_changed_as_expected ? "[x]" : "[ ]"} Confirm file changed as expected
                </li>
                <li>
                  {docsOnlyConfirmations?.no_unintended_files ? "[x]" : "[ ]"} Confirm no unintended files changed
                </li>
                <li>
                  {docsOnlyConfirmations?.backup_audit_present ? "[x]" : "[ ]"} Confirm backup/audit exists
                </li>
              </ul>
              {postApplyVerification.verification_note ? (
                <div className="text-slate-600">{postApplyVerification.verification_note}</div>
              ) : null}
              {canCompleteDocsOnly ? (
                <button
                  className="border border-slate-900 bg-slate-950 px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isVerifying || docsOnlyComplete}
                  onClick={onDocsOnlyVerify}
                  type="button"
                >
                  {isVerifying ? "Marking verified..." : "Mark verification complete"}
                </button>
              ) : null}
            </div>
          ) : null}
          {codeVerificationRequired ? (
            <div className="space-y-2 border border-yellow-200 bg-white px-3 py-2 text-sm text-slate-700">
              <div className="font-semibold text-slate-950">Run code verification</div>
              <button
                className="border border-slate-900 bg-slate-950 px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isVerifying}
                onClick={onCodeVerify}
                type="button"
              >
                {isVerifying ? "Running verification..." : "Run code verification"}
              </button>
            </div>
          ) : null}
          {verificationFailed ? (
            <pre className="overflow-x-auto whitespace-pre-wrap border border-yellow-200 bg-white p-3 text-xs leading-5 text-slate-800">
              {generateVerificationFixPrompt(postApplyVerification)}
            </pre>
          ) : null}
        </div>
      ) : null}
      {showPrimaryVerificationPlan && commands.length > 0 ? (
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
      {showPrimaryVerificationPlan && suggested.length > 0 ? (
        <div className="mt-3 space-y-2">
          {suggested.map((step) => (
            <div className="border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700" key={step}>
              {step}
            </div>
          ))}
        </div>
      ) : !postApplyVerification ? (
        <p className="mt-3 text-sm text-slate-600">
          Verification steps appear here after a diff preview or approved execution.
        </p>
      ) : null}
      {postApplyVerification || longRunningTask.response?.task.truncated_test_results ? (
        <details className="mt-3 border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
          <summary className="cursor-pointer font-semibold text-slate-950">
            Advanced verification details
          </summary>
          {advancedVerificationPayload ? (
            <pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-800">
              {JSON.stringify(advancedVerificationPayload, null, 2)}
            </pre>
          ) : null}
          {commands.length > 0 ? (
            <div className="mt-3 space-y-2">
              {commands.map((item) => (
                <div
                  className="border border-slate-300 bg-white px-3 py-2 text-sm"
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
                <div
                  className="border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
                  key={step}
                >
                  {step}
                </div>
              ))}
            </div>
          ) : null}
          {longRunningTask.response?.task.truncated_test_results && !advancedVerificationPayload ? (
            <pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-800">
              {longRunningTask.response.task.truncated_test_results}
            </pre>
          ) : null}
        </details>
      ) : null}
    </section>
  );
}

type PostApplyVerificationDisplaySummary = {
  backupRoot: string;
  changedFiles: string[];
  risk: string;
};

function parseLongTaskVerificationSnapshot(
  task?: LongRunningTaskPayload | null,
): Record<string, unknown> | null {
  const raw = task?.truncated_test_results?.trim();
  if (!raw || !raw.startsWith("{")) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === "object" ? (parsed as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function stringArrayFromUnknown(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function firstRawNonEmpty(values: Array<string | null | undefined>): string | null {
  for (const value of values) {
    const normalized = value?.trim();
    if (normalized) {
      return normalized;
    }
  }
  return null;
}

function uniqueDisplayPaths(values: Array<string | null | undefined>): string[] {
  const seen = new Set<string>();
  const output: string[] = [];
  for (const value of values) {
    const normalized = normalizeRepoRelativePath(value ?? "");
    if (normalized && !seen.has(normalized)) {
      seen.add(normalized);
      output.push(normalized);
    }
  }
  return output;
}

function buildPostApplyVerificationDisplaySummary({
  diffVerification,
  execution,
  postApplyVerification,
  task,
}: {
  diffVerification: DiffVerificationState;
  execution: ApprovedActionExecutionResponse | null;
  postApplyVerification: PostApplyVerification | null;
  task: LongRunningTaskPayload | null;
}): PostApplyVerificationDisplaySummary {
  const snapshot = parseLongTaskVerificationSnapshot(task);
  const audit =
    snapshot?.audit && typeof snapshot.audit === "object"
      ? (snapshot.audit as Record<string, unknown>)
      : null;
  const changedFiles = uniqueDisplayPaths([
    ...(postApplyVerification?.changed_files?.map((file) => file.path) ?? []),
    ...(execution?.changed_files?.map((file) => file.path) ?? []),
    ...(task?.open_diffs?.flatMap((diff) => diff.changed_files?.map((file) => file.path) ?? []) ??
      []),
    ...(diffVerification.preview?.changed_files?.map((file) => file.path) ?? []),
    ...stringArrayFromUnknown(audit?.changed_files),
  ]);
  const backupRoot = firstRawNonEmpty([
    postApplyVerification?.backup_root,
    execution?.backup_root,
    typeof snapshot?.backup_root === "string" ? snapshot.backup_root : null,
    execution?.backupRelativePath,
  ]);
  const risk = firstRawNonEmpty([
    postApplyVerification?.risk,
    execution?.risk,
    task?.open_diffs?.find((diff) => diff.risk)?.risk,
    typeof audit?.risk === "string" ? audit.risk : null,
    diffVerification.preview?.risk,
  ]);

  return {
    backupRoot: backupRoot ?? "Not reported yet",
    changedFiles,
    risk: risk ?? "unknown",
  };
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
            <details className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
              <summary className="cursor-pointer text-base font-semibold text-slate-950">
                Raw Decision Details
              </summary>
              <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-md border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-800">
                {finalOutput.decisionPayload}
              </pre>
            </details>
          </>
        ) : null}
        {diffVerification.preview ? (
          <details className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
            <summary className="cursor-pointer text-base font-semibold text-slate-950">
              Raw Diff Preview
            </summary>
            <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-md border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-800">
              {JSON.stringify(diffVerification.preview, null, 2)}
            </pre>
          </details>
        ) : null}
      </div>
    </details>
  );
}

function OutputWindow({
  architectPlan,
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
  onFallbackScaffoldAcceptedChange,
  onTrackedDiffSelect,
  onLongTaskCancel,
  onLongTaskDescriptionChange,
  onLongTaskPoll,
  onLongTaskStart,
  onLongTaskVerifyCode,
  onLongTaskVerifyDocsOnly,
  onInputChange,
  onFilesAdded,
  onPreviewApprovalGate,
  onPreviewDiffVerification,
  onPreviewManualResult,
  onCopyHistoryRecoveryPrompt,
  onRestoreHistoryEntry,
  onRunProxyFlow,
  onStartNewTask,
  onSubmit,
  telemetry,
  workflowStepFloor,
}: {
  architectPlan: ArchitectPlanResponse | null;
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
  onDenyPreviewedAction: (reasonCode: ApprovalRejectionReason) => void;
  onDiffChange: (unifiedDiff: string) => void;
  onFallbackScaffoldAcceptedChange: (accepted: boolean) => void;
  onTrackedDiffSelect: (unifiedDiff: string) => void;
  onLongTaskCancel: () => void;
  onLongTaskDescriptionChange: (description: string) => void;
  onLongTaskPoll: () => void;
  onLongTaskStart: () => void;
  onLongTaskVerifyCode: () => void;
  onLongTaskVerifyDocsOnly: () => void;
  onInputChange: (value: string) => void;
  onFilesAdded: (files: UploadedFile[]) => void;
  onPreviewApprovalGate: () => void;
  onPreviewDiffVerification: () => void;
  onPreviewManualResult: () => void;
  onCopyHistoryRecoveryPrompt: (entry: CodingHistoryEntry) => void;
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
      const promptText =
        action.id === "cursor" && action.label.toLowerCase().includes("manual browser")
          ? manualBrowserPromptForCurrentState({
              architectPlan,
              currentTask: inputText,
              promptText: finalOutput.promptText,
              target: approvalGate.target,
            })
          : finalOutput.promptText;
      await navigator.clipboard.writeText(
        buildClipboardPrompt(
          action,
          promptText,
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
  const alreadySatisfied = isAlreadySatisfiedGate(approvalGate);
  const needsCoderDiff =
    !alreadySatisfied &&
    (approvalGate.action === "needs_coder_diff" ||
      approvalGate.preview?.decision === "needs_coder_diff" ||
      approvalGate.preview?.reason_codes?.includes("needs_coder_diff") === true ||
      approvalGate.preview?.reason_codes?.some((code) =>
        [
          "coder_model_not_configured",
          "coder_empty_model_response",
          "coder_no_usable_diff",
          "route_response_invalid",
          "coder_sync_timeout",
        ].includes(code),
      ) === true);
  const canManuallyPreviewDiff =
    needsCoderDiff ||
    Boolean(architectTargetPath(architectPlan)) ||
    Boolean(resolvedTargetPathFromDecision(finalOutput?.decision));
  const derivedStep = workflowStep({
    approvalGate,
    diffVerification,
    finalOutput,
    isRunning,
    longRunningTask,
  });
  const activeStep =
    workflowStepFloor != null ? Math.max(derivedStep, workflowStepFloor) : derivedStep;
  const blockedStep = workflowBlockedStep({
    approvalGate,
    longRunningTask,
  });
  const stages = workflowStages(activeStep, blockedStep);
  const stabilitySummary = deriveCodingStabilitySummary({
    approvalGate,
    architectPlan,
    diffVerification,
    finalOutput,
    isRunning,
    logs,
    longRunningTask,
  });

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

      <SwarmRolePipeline
        approvalGate={approvalGate}
        task={longRunningTask.response?.task ?? null}
      />
      <CodingStabilityCard summary={stabilitySummary} />

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
              {!finalOutput && conversationHistory.length > 0 ? (
                <div className="mt-4">
                  <ConversationHistoryPanel
                    entries={conversationHistory}
                    onCopyRecoveryPrompt={onCopyHistoryRecoveryPrompt}
                    onClear={onClearHistory}
                    onRestore={onRestoreHistoryEntry}
                    title="Recent Agent Runs"
                  />
                </div>
              ) : null}
            </WorkflowStage>

            <WorkflowStage
              description="The agent classifies the task, recalls prior decisions, and prepares a plan."
              index={2}
              status={stages[1].status}
              title="Research / Plan"
            >
              {finalOutput ? (
                <div className="space-y-4">
                  {finalOutput.summary.startsWith(ROUTE_RESPONSE_INVALID_PREFIX) ? (
                    <div className="rounded-lg border border-amber-400 bg-amber-50 px-4 py-3 text-sm text-amber-950">
                      <div className="font-semibold">route_response_invalid</div>
                      <p className="mt-1 font-mono text-xs leading-relaxed">
                        {finalOutput.summary.slice(ROUTE_RESPONSE_INVALID_PREFIX.length)}
                      </p>
                    </div>
                  ) : null}
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
                  <ArchitectPlanPanel
                    plan={architectPlan}
                    resolvedTargetPath={resolvedTargetPathFromDecision(finalOutput.decision)}
                    task={longRunningTask.response?.task ?? null}
                  />
                  <SelfCorrectionPanel selfCorrection={finalOutput.selfCorrection} />
                  <ConversationHistoryPanel
                    entries={conversationHistory}
                    onCopyRecoveryPrompt={onCopyHistoryRecoveryPrompt}
                    onClear={onClearHistory}
                    onRestore={onRestoreHistoryEntry}
                  />
                  <div className="grid gap-3 sm:grid-cols-2">
                    {routeActions.map((action) => {
                      const isRecommended =
                        action.id === routeActionForDecision(finalOutput.decision).id;
                      const displayAction =
                        needsCoderDiff && action.id === "proxy"
                          ? {
                              ...action,
                              label: "Retry Local Coder",
                              description: "Run local output repair/retry again with the current TaskSpec and repo context.",
                            }
                          : needsCoderDiff && action.id === "cursor"
                            ? {
                                ...action,
                                label: "Copy manual browser prompt",
                                description: "Paste a strict prompt into GPT/Gemini/Grok/Claude, then validate the returned JSON or diff here.",
                              }
                            : needsCoderDiff && action.id === "codex"
                              ? {
                                  ...action,
                                  label: "Use Cloud/API route",
                                  description: "Optional: use a configured API route only when you explicitly choose it.",
                                }
                              : action;
                      return (
                        <button
                          className={`border px-3 py-2 text-left text-sm hover:bg-slate-100 ${
                            isRecommended
                              ? "border-slate-900 bg-slate-900 text-white hover:bg-slate-800"
                              : "border-slate-300 bg-slate-50 text-slate-900"
                          }`}
                          disabled={isRunning && action.id === "proxy"}
                          key={action.id}
                          onClick={() => handleRouteAction(displayAction)}
                          type="button"
                        >
                          <span className="block font-semibold">{displayAction.label}</span>
                          <span
                            className={`mt-1 block text-xs ${
                              isRecommended ? "text-slate-200" : "text-slate-600"
                            }`}
                          >
                            {displayAction.description}
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
              {hasProposal || hasDiff || canManuallyPreviewDiff ? (
                <div className="space-y-4">
                  <ProposalSummaryPanel gate={approvalGate} />
                  {alreadySatisfied ? (
                    <EmptyWorkflowMessage text="No diff is needed because the target file already satisfies this task." />
                  ) : needsCoderDiff || (!hasDiff && canManuallyPreviewDiff) ? (
                    <div className="space-y-3">
                      <EmptyWorkflowMessage text="No backend diff is available yet. Paste a unified diff below to run the normal preview and approval gates." />
                      <DiffVerificationPanel
                        buttonLabel="Preview manual result"
                        fallbackUnifiedDiff={approvalGate.proposedDiff}
                        placeholder="Paste a unified diff here for a read-only safety check..."
                        state={diffVerification}
                        title="Paste Manual Diff"
                        onChange={onDiffChange}
                        onPreview={onPreviewDiffVerification}
                      />
                    </div>
                  ) : (
                    <DiffVerificationPanel
                      fallbackUnifiedDiff={approvalGate.proposedDiff}
                      state={diffVerification}
                      onChange={onDiffChange}
                      onPreview={onPreviewDiffVerification}
                    />
                  )}
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
              <div className="space-y-4">
                <QualityGatePanel
                  architectPlan={architectPlan}
                  diffVerification={diffVerification}
                  gate={approvalGate}
                  onFallbackAcceptChange={onFallbackScaffoldAcceptedChange}
                  resolvedTargetPath={resolvedTargetPathFromDecision(finalOutput?.decision)}
                />
                <ApprovalGatePanel
                  architectPlan={architectPlan}
                  gate={approvalGate}
                  diffVerification={diffVerification}
                  coderAgentLocalDiff={Boolean(finalOutput?.coderAgentLocalDiff)}
                  onActionChange={onApprovalActionChange}
                  onApprove={onApprovePreviewedAction}
                  onContentChange={onApprovalContentChange}
                  onDeny={onDenyPreviewedAction}
                  onPreview={onPreviewApprovalGate}
                  task={longRunningTask.response?.task ?? null}
                  onTargetChange={onApprovalTargetChange}
                  resolvedTargetPath={resolvedTargetPathFromDecision(finalOutput?.decision)}
                />
              </div>
            </WorkflowStage>

            <WorkflowStage
              description="After approval, execution progress comes from the long-running task layer."
              index={5}
              sectionId="spirit-coding-workflow-execution"
              status={stages[4].status}
              title="Execution"
            >
              {alreadySatisfied ? (
                <EmptyWorkflowMessage text="Skipped because there are no changes to apply." />
              ) : (
                <LongRunningTaskPanel
                  state={longRunningTask}
                  onCancel={onLongTaskCancel}
                  onDescriptionChange={onLongTaskDescriptionChange}
                  onDiffSelect={onTrackedDiffSelect}
                  onPoll={onLongTaskPoll}
                  onStart={onLongTaskStart}
                />
              )}
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
                isVerifying={longRunningTask.isChecking}
                longRunningTask={longRunningTask}
                onCodeVerify={onLongTaskVerifyCode}
                onDocsOnlyVerify={onLongTaskVerifyDocsOnly}
              />
            </WorkflowStage>

            <WorkflowStage
              description="Final activity summary and task completion state."
              index={7}
              status={stages[6].status}
              title="Status / Done"
            >
              <ProcessWindow logs={logs} />
              <TaskCompletionStatus
                alreadySatisfied={alreadySatisfied}
                execution={approvalGate.execution}
                task={longRunningTask.response?.task ?? null}
              />
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

export function TaskCompletionStatus({
  alreadySatisfied,
  execution,
  task,
}: {
  alreadySatisfied: boolean;
  execution: ApprovedActionExecutionResponse | null;
  task: LongRunningTaskPayload | null;
}) {
  if (alreadySatisfied) {
    return (
      <div className="mt-4 border border-green-200 bg-green-50 px-3 py-2 text-sm font-semibold text-green-900">
        Already satisfied
      </div>
    );
  }
  if (isVerificationCompleteState(task, execution)) {
    return (
      <div className="mt-4 border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-900">
        <div className="font-semibold">Task Complete</div>
        <div className="mt-1 text-green-800">
          {postApplyVerificationFor(task, execution)?.docs_only
            ? "Docs verified"
            : "Verification complete"}
        </div>
      </div>
    );
  }
  if (task?.status === "needs_context") {
    return (
      <div className="mt-4 border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-950">
        Needs CoderPacket context
      </div>
    );
  }
  if (task?.status === "blocked") {
    return (
      <div className="mt-4 border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-950">
        Coder blocked before diff
      </div>
    );
  }
  if (isPostApplyVerificationPending(task, execution) || execution?.ok) {
    return (
      <div className="mt-4 border border-yellow-300 bg-yellow-50 px-3 py-2 text-sm text-yellow-950">
        <div className="font-semibold">Waiting for verification</div>
        <div className="mt-1">Complete the checklist in Step 6 to finish.</div>
      </div>
    );
  }
  return null;
}

function ConversationHistoryPanel({
  entries,
  onCopyRecoveryPrompt,
  onClear,
  onRestore,
  title = "Recent Agent Runs",
}: {
  entries: CodingHistoryEntry[];
  onCopyRecoveryPrompt: (entry: CodingHistoryEntry) => void;
  onClear: () => void;
  onRestore: (entry: CodingHistoryEntry) => void;
  title?: string;
}) {
  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">{title}</h2>
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
                <div className="flex shrink-0 flex-wrap gap-2">
                  <button
                    className="border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-slate-100"
                    onClick={() => onRestore(entry)}
                    type="button"
                  >
                    Restore prompt
                  </button>
                  {entry.recommendation === "Run with Proxy Agent" ||
                  entry.recoveryPrompt ||
                  entry.route === "local_route" ? (
                    <button
                      className="border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-slate-100"
                      onClick={() => onCopyRecoveryPrompt(entry)}
                      type="button"
                    >
                      Copy manual browser prompt
                    </button>
                  ) : null}
                </div>
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

function ArchitectPlanPanel({
  plan,
  resolvedTargetPath,
  task,
}: {
  plan: ArchitectPlanResponse | null;
  resolvedTargetPath?: string;
  task: LongRunningTaskPayload | null;
}) {
  const targetPath = architectPlanDisplayTarget(plan, resolvedTargetPath);
  const criteria = plan?.coder_packet?.acceptance_criteria ?? [];
  const contextSlices = plan?.coder_packet?.context_slices ?? [];
  const mustContain = plan?.coder_packet?.constraints?.must_contain ?? [];
  const checks = plan?.verification_plan?.required_checks ?? [];
  const taskSpec = taskSpecForPlan(plan);
  const planSource = deterministicPlanSourceLabel(plan);
  const architectStatus = task?.architect_status ?? "";
  const architectReason = task?.architect_reason ?? "";

  return (
    <details className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm" open>
      <summary className="cursor-pointer text-base font-semibold text-slate-950">
        Architect Plan
      </summary>
      {plan ? (
        <div className="mt-4 space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <PlanFact label="Target" value={targetPath || "No target"} />
            <PlanFact
              label="Class"
              value={plan.classification?.task_class ?? "unknown"}
            />
            <PlanFact
              label="Complexity"
              value={plan.classification?.estimated_complexity ?? "unknown"}
            />
            <PlanFact
              label="Budget"
              value={`${plan.budget?.max_coder_attempts ?? "?"} attempts / ${
                plan.budget?.max_total_seconds ?? "?"
              }s`}
            />
            {planSource ? <PlanFact label="Source" value={planSource} /> : null}
            <PlanFact
              label="Context"
              value={`${contextSlices.length} slice${contextSlices.length === 1 ? "" : "s"}`}
            />
          </div>

          <section>
            <h3 className="text-sm font-semibold text-slate-900">Acceptance Criteria</h3>
            {criteria.length > 0 ? (
              <ul className="mt-2 space-y-2">
                {criteria.map((criterion, index) => (
                  <li
                    className="border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
                    key={criterion.id ?? index}
                  >
                    <span className="mr-2 font-semibold">[ ]</span>
                    {criterion.description ?? criterion.id ?? "Unnamed criterion"}
                    {criterion.kind ? (
                      <span className="ml-2 text-xs text-slate-500">({criterion.kind})</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-slate-600">No acceptance criteria yet.</p>
            )}
          </section>

          {mustContain.length > 0 ? (
            <section>
              <h3 className="text-sm font-semibold text-slate-900">Literal Requirements</h3>
              <ul className="mt-2 space-y-2">
                {mustContain.map((literal) => (
                  <li
                    className="border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-sm text-slate-800"
                    key={literal}
                  >
                    {literal}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section>
            <h3 className="text-sm font-semibold text-slate-900">Context Slices</h3>
            {contextSlices.length > 0 ? (
              <ul className="mt-2 space-y-2">
                {contextSlices.map((slice, index) => (
                  <li
                    className="border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
                    key={`${slice.path ?? "slice"}-${index}`}
                  >
                    <span className="font-mono text-slate-950">
                      {slice.path ?? "unknown path"}
                    </span>
                    <span className="ml-2 text-xs text-slate-500">
                      {slice.kind ?? "context"}
                      {Array.isArray(slice.line_range)
                        ? ` lines ${slice.line_range[0]}-${slice.line_range[1]}`
                        : ""}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-slate-600">No context slices yet.</p>
            )}
          </section>

          <section>
            <h3 className="text-sm font-semibold text-slate-900">Verification Checks</h3>
            {checks.length > 0 ? (
              <ul className="mt-2 space-y-2">
                {checks.map((check, index) => (
                  <li
                    className="border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
                    key={check.id ?? index}
                  >
                    <span className="mr-2">{check.blocking ? "!" : "i"}</span>
                    <span className="font-semibold">{check.id ?? "check"}</span>
                    <span className="ml-2 text-slate-600">
                      {(check.command ?? []).join(" ") || "No command"}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-slate-600">No verification checks yet.</p>
            )}
          </section>

          {taskSpec ? (
            <section>
              <h3 className="text-sm font-semibold text-slate-900">TaskSpec Contract</h3>
              <pre className="mt-2 max-h-72 overflow-auto border border-slate-200 bg-slate-950 p-3 text-xs leading-relaxed text-slate-50">
                {JSON.stringify(taskSpec, null, 2)}
              </pre>
            </section>
          ) : null}
        </div>
      ) : architectStatus === "awaiting_llm" ? (
        <div className="mt-4 flex items-start gap-3 border border-blue-200 bg-blue-50 px-3 py-3 text-sm text-blue-950">
          <span className="mt-0.5 h-4 w-4 animate-spin rounded-full border-2 border-blue-300 border-t-blue-900" />
          <div>
            <div className="font-semibold">Planning with LLM Architect...</div>
            <div className="mt-1 text-blue-800">
              Reason: {friendlyArchitectReason(architectReason)}
            </div>
          </div>
        </div>
      ) : architectStatus === "blocked" ? (
        <div className="mt-4 border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-950">
          <div className="font-semibold">Architect planning blocked</div>
          <div className="mt-1 text-red-800">
            Reason: {friendlyArchitectReason(architectReason)}
          </div>
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-600">
          No architect plan yet. Phase 10 will start generating these automatically; for now
          this panel updates when a plan is saved for the active long-running task.
        </p>
      )}
    </details>
  );
}

function friendlyArchitectReason(reason: string) {
  switch (reason) {
    case "no_explicit_target":
      return "no_explicit_target";
    case "creation_task":
      return "creation_task";
    case "target_missing":
      return "target_missing";
    case "task_too_long":
      return "task_too_long";
    case "target_outside_workspace":
      return "target_outside_workspace";
    default:
      return reason || "awaiting_llm";
  }
}

function PlanFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-slate-200 bg-slate-50 px-3 py-2">
      <div className="text-xs font-semibold uppercase text-slate-500">{label}</div>
      <div className="mt-1 break-words text-sm text-slate-900">{value}</div>
    </div>
  );
}

export function architectPlanDisplayTarget(
  plan: ArchitectPlanResponse | null | undefined,
  resolvedTargetPath?: string,
): string {
  return (
    normalizeRepoRelativePath(plan?.coder_packet?.target_file?.path ?? "") ||
    normalizeRepoRelativePath(resolvedTargetPath ?? "")
  );
}

export function taskSpecForPlan(
  plan: ArchitectPlanResponse | null | undefined,
): CoderTaskSpecResponse | null {
  const direct = plan?.task_spec ?? plan?.taskSpec;
  if (direct) {
    return normalizeTaskSpecForDisplay(direct);
  }
  const target = normalizeRepoRelativePath(plan?.coder_packet?.target_file?.path ?? "");
  if (!target) {
    return null;
  }
  const literalRequirements = plan?.coder_packet?.constraints?.must_contain ?? [];
  const checks = plan?.verification_plan?.required_checks ?? [];
  const packetOperation = plan?.coder_packet?.operation;
  const operation =
    packetOperation === "delete"
      ? "delete_file"
      : packetOperation === "create" || plan?.coder_packet?.target_file?.exists === false
        ? "create_new_file"
        : "modify_existing_file";
  return {
    schema_version: 1,
    task_type: operation,
    target,
    allowed_files: [target],
    forbidden_files: [],
    literal_requirements: literalRequirements,
    verification: [
      ...(checks.length > 0
        ? checks.map((check) => (check.id ?? "verification check").replace(/[_-]/g, " "))
        : ["git apply check"]),
      ...(literalRequirements.length > 0 ? ["literal present"] : []),
      "target-only",
    ],
    risk_tier:
      operation === "delete_file" ? "high" : operation === "create_new_file" ? "medium" : "low",
    source: "deterministic",
  };
}

function normalizeTaskSpecForDisplay(spec: CoderTaskSpecResponse): CoderTaskSpecResponse {
  return {
    schema_version: spec.schema_version ?? spec.schemaVersion,
    task_type: spec.task_type ?? spec.taskType,
    target: spec.target,
    allowed_files: spec.allowed_files ?? spec.allowedFiles ?? [],
    forbidden_files: spec.forbidden_files ?? spec.forbiddenFiles ?? [],
    literal_requirements: spec.literal_requirements ?? spec.literalRequirements ?? [],
    verification: spec.verification ?? [],
    risk_tier: spec.risk_tier ?? spec.riskTier,
    source: spec.source,
  };
}

function deterministicPlanSourceLabel(plan: ArchitectPlanResponse | null | undefined): string {
  const directives = plan?.coder_packet?.style_directives ?? [];
  const source = directives.find((item) =>
    item.toLowerCase().includes("deterministic small markdown append fallback"),
  );
  return source ? "deterministic small Markdown append" : "";
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

type QualityGateCheckStatus = "pass" | "fail" | "waiting" | "info" | "advisory";

type QualityGateCheck = {
  detail: string;
  label: string;
  required: boolean;
  status: QualityGateCheckStatus;
};

function QualityGatePanel({
  architectPlan,
  diffVerification,
  gate,
  onFallbackAcceptChange,
  resolvedTargetPath,
}: {
  architectPlan: ArchitectPlanResponse | null;
  diffVerification: DiffVerificationState;
  gate: ApprovalGateState;
  onFallbackAcceptChange: (accepted: boolean) => void;
  resolvedTargetPath?: string;
}) {
  const checks = buildQualityGateChecks({
    diffVerification,
    gate,
    resolvedTargetPath: resolvedTargetPath || architectTargetPath(architectPlan),
  });
  const requiredFailing = checks.filter(
    (check) => check.required && check.status !== "pass",
  );
  const fallbackNeedsExplicitAccept =
    gate.fallbackScaffoldGenerated && !gate.fallbackScaffoldBlocked;

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Quality Gate</h2>
        <div
          className={`border px-2 py-1 text-xs font-semibold ${
            requiredFailing.length === 0
              ? "border-green-300 bg-green-50 text-green-900"
              : "border-red-300 bg-red-50 text-red-900"
          }`}
        >
          {requiredFailing.length === 0 ? "passing" : "blocked"}
        </div>
      </div>

      <div className="mt-3 grid gap-2 md:grid-cols-2">
        {checks.map((check) => (
          <div
            className={`border px-3 py-2 text-sm ${
              check.status === "pass"
                ? "border-green-200 bg-green-50 text-green-950"
                : check.status === "fail"
                  ? "border-red-200 bg-red-50 text-red-950"
                  : check.status === "advisory"
                    ? "border-orange-300 bg-orange-50 text-orange-950"
                  : check.status === "waiting"
                    ? "border-yellow-300 bg-yellow-50 text-yellow-950"
                    : "border-slate-300 bg-slate-50 text-slate-700"
            }`}
            key={check.label}
          >
            <div className="flex items-center justify-between gap-3">
              <span className="font-semibold">{check.label}</span>
              <span className="border border-current bg-white/70 px-2 py-0.5 text-xs font-semibold">
                {check.status}
              </span>
            </div>
            <p className="mt-1 leading-6">{check.detail}</p>
          </div>
        ))}
      </div>

      {fallbackNeedsExplicitAccept ? (
        <label className="mt-3 flex items-start gap-2 border border-yellow-300 bg-yellow-50 px-3 py-2 text-sm text-yellow-950">
          <input
            checked={gate.fallbackScaffoldAccepted}
            className="mt-1"
            onChange={(event) => onFallbackAcceptChange(event.target.checked)}
            type="checkbox"
          />
          <span>
            <span className="font-semibold">Accept fallback scaffold</span>
            <span className="block leading-6">
              This is only available for safe placeholder-style tasks. Approval stays
              disabled until you explicitly accept it.
            </span>
          </span>
        </label>
      ) : null}

      {requiredFailing.length > 0 ? (
        <div className="mt-3 border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-950">
          Approval is disabled until required gates pass.
        </div>
      ) : null}
    </section>
  );
}

export function buildQualityGateChecks({
  diffVerification,
  gate,
  resolvedTargetPath,
}: {
  diffVerification: DiffVerificationState;
  gate: ApprovalGateState;
  resolvedTargetPath?: string;
}): QualityGateCheck[] {
  const explicitTarget = normalizeRepoRelativePath(resolvedTargetPath ?? "");
  const target = normalizeRepoRelativePath(gate.target);
  const diffPayload = unifiedDiffPayloadOrEmpty(
    gate.proposedDiff || diffVerification.unifiedDiff,
  );
  const diffPaths = diffPayload ? collectPathsFromUnifiedDiff(diffPayload) : [];
  const changedFiles = diffVerification.preview?.changed_files ?? [];
  const hasTsChange = changedFiles.some((file) =>
    /\.(?:tsx?|jsx?)$/i.test(file.path || file.extension || ""),
  );
  const reasonCodes = gate.preview?.reason_codes ?? [];
  const previewStatus = diffVerification.preview?.status;

  const checks: QualityGateCheck[] = [];

  if (isAlreadySatisfiedGate(gate)) {
    return [
      {
        detail: target ? `Target is ${target}.` : "The target file already matches.",
        label: "Target Match",
        required: true,
        status: "pass",
      },
      {
        detail: "No unified diff is needed because the task is already satisfied.",
        label: "Requirement Coverage",
        required: true,
        status: "pass",
      },
      {
        detail: "No TypeScript change is needed.",
        label: "TypeScript Syntax",
        required: false,
        status: "info",
      },
      {
        detail: "No patch needs to be applied.",
        label: "Git Apply Check",
        required: false,
        status: "info",
      },
      fallbackQualityCheck(gate),
      staleMemoryQualityCheck(reasonCodes, diffVerification.preview),
    ];
  }

  if (reasonCodes.includes(VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE)) {
    return [
      targetQualityCheck({ diffPayload, diffPaths, explicitTarget, target }),
      {
        detail:
          "Needs a material visual diff: styling, layout, hover, active, glow, spacing, or animation behavior must change.",
        label: "Requirement Coverage",
        required: true,
        status: "fail",
      },
      {
        detail: "No approvable unified diff is available.",
        label: "Git Apply Check",
        required: false,
        status: "info",
      },
      {
        detail: "Diff was rejected before TypeScript syntax validation.",
        label: "TypeScript Syntax",
        required: false,
        status: "info",
      },
      fallbackQualityCheck(gate),
      staleMemoryQualityCheck(reasonCodes, diffVerification.preview),
    ];
  }

  checks.push(targetQualityCheck({ diffPayload, diffPaths, explicitTarget, target }));
  checks.push(taskSpecQualityCheck(diffVerification.preview));
  checks.push(gitApplyQualityCheck(diffVerification.preview, diffPayload));
  checks.push(typescriptQualityCheck(diffVerification.preview, diffPayload, hasTsChange));
  checks.push(requirementQualityCheck(diffVerification.preview));
  checks.push(reviewerQualityCheck(diffVerification.preview));
  checks.push(llmReviewerQualityCheck(diffVerification.preview));
  checks.push(fallbackQualityCheck(gate));
  checks.push(staleMemoryQualityCheck(reasonCodes, diffVerification.preview));

  if (previewStatus === "blocked" && !checks.some((check) => check.status === "fail")) {
    checks.push({
      detail: "Diff preview returned blocked status. Review the preview findings.",
      label: "Preview Status",
      required: true,
      status: "fail",
    });
  }

  return checks;
}

function taskSpecQualityCheck(
  preview: DiffVerificationPreviewResponse | null,
): QualityGateCheck {
  const check = preview?.task_spec_check;
  if (!check || check.skipped) {
    return {
      detail: "No TaskSpec check was returned for this preview path.",
      label: "TaskSpec Allowed Files",
      required: false,
      status: "info",
    };
  }
  if (check.ok) {
    const allowed = check.allowed_files?.join(", ") || "none";
    const changed = check.changed_files?.join(", ") || "none";
    return {
      detail: `Changed files are within TaskSpec.allowed_files. allowed=[${allowed}] changed=[${changed}]`,
      label: "TaskSpec Allowed Files",
      required: true,
      status: "pass",
    };
  }
  const reasonCodes = check.reason_codes ?? [];
  return {
    detail: reasonCodes.includes("task_spec_allowed_file_violation")
      ? "TaskSpec blocked this diff because it touches files outside the allowed list."
      : check.summary || "TaskSpec blocked this diff.",
    label: "TaskSpec Allowed Files",
    required: true,
    status: "fail",
  };
}

function targetQualityCheck({
  diffPayload,
  diffPaths,
  explicitTarget,
  target,
}: {
  diffPayload: string;
  diffPaths: string[];
  explicitTarget: string;
  target: string;
}): QualityGateCheck {
  if (explicitTarget) {
    if (!target) {
      return {
        detail: `Expected target: ${explicitTarget}.`,
        label: "Target Match",
        required: true,
        status: "waiting",
      };
    }
    if (target !== explicitTarget) {
      return {
        detail: `Expected ${explicitTarget}; current proposal targets ${target}.`,
        label: "Target Match",
        required: true,
        status: "fail",
      };
    }
    if (diffPayload && !diffTouchesExplicitTarget(diffPayload, explicitTarget)) {
      return {
        detail: `Diff does not touch ${explicitTarget}.`,
        label: "Target Match",
        required: true,
        status: "fail",
      };
    }
    return {
      detail: `Proposal is pinned to ${explicitTarget}.`,
      label: "Target Match",
      required: true,
      status: "pass",
    };
  }

  if (diffPaths.length > 0 && target && !diffPaths.includes(target)) {
    return {
      detail: `Gate target is ${target}; diff touches ${diffPaths.join(", ")}.`,
      label: "Target Match",
      required: true,
      status: "fail",
    };
  }
  return {
    detail: target ? `Proposal target: ${target}.` : "No explicit target was provided.",
    label: "Target Match",
    required: Boolean(target || diffPayload),
    status: target || diffPayload ? "pass" : "info",
  };
}

function gitApplyQualityCheck(
  preview: DiffVerificationPreviewResponse | null,
  diffPayload: string,
): QualityGateCheck {
  if (!diffPayload) {
    return {
      detail: "No unified diff is available yet.",
      label: "Git Apply Check",
      required: true,
      status: "waiting",
    };
  }
  if (!preview) {
    return {
      detail: "Preview the diff before approval.",
      label: "Git Apply Check",
      required: true,
      status: "waiting",
    };
  }
  if (preview.git_apply_check_ok === false) {
    return {
      detail: preview.git_apply_check_error || "git apply --check failed.",
      label: "Git Apply Check",
      required: true,
      status: "fail",
    };
  }
  return {
    detail: "Patch shape applies cleanly in the preview workspace.",
    label: "Git Apply Check",
    required: true,
    status: "pass",
  };
}

function typescriptQualityCheck(
  preview: DiffVerificationPreviewResponse | null,
  diffPayload: string,
  hasTsChange: boolean,
): QualityGateCheck {
  if (!diffPayload) {
    return {
      detail: "No TS/TSX diff is available yet.",
      label: "TypeScript Syntax",
      required: true,
      status: "waiting",
    };
  }
  if (!preview) {
    return {
      detail: "Preview the diff to run syntax checks.",
      label: "TypeScript Syntax",
      required: true,
      status: "waiting",
    };
  }
  if (!hasTsChange && !preview.typescript_check) {
    return {
      detail: "No TypeScript or JSX files changed.",
      label: "TypeScript Syntax",
      required: false,
      status: "info",
    };
  }
  if (!hasTsChange && preview.typescript_check?.skipped === true) {
    return {
      detail: preview.typescript_check.summary || "No TypeScript or JSX files changed.",
      label: "TypeScript Syntax",
      required: false,
      status: "info",
    };
  }
  if (preview.typescript_check?.ok === true && preview.typescript_check.skipped !== true) {
    return {
      detail: preview.typescript_check.summary || "TypeScript parser accepted changed files.",
      label: "TypeScript Syntax",
      required: true,
      status: "pass",
    };
  }
  return {
    detail:
      preview.typescript_check?.summary ||
      "TypeScript syntax/typecheck did not pass for this preview.",
    label: "TypeScript Syntax",
    required: true,
    status: "fail",
  };
}

function requirementQualityCheck(
  preview: DiffVerificationPreviewResponse | null,
): QualityGateCheck {
  if (!preview) {
    return {
      detail: "Preview the diff to compare exact task requirements.",
      label: "Requirement Coverage",
      required: true,
      status: "waiting",
    };
  }
  if (preview.requirement_coverage?.ok === false) {
    return {
      detail:
        preview.requirement_coverage.missing?.join("; ") ||
        preview.requirement_coverage.summary ||
        "Required task items are missing.",
      label: "Requirement Coverage",
      required: true,
      status: "fail",
    };
  }
  if (preview.requirement_coverage?.ok === true) {
    return {
      detail: "Exact task requirements found in the proposed diff.",
      label: "Requirement Coverage",
      required: true,
      status: "pass",
    };
  }
  return {
    detail: "No exact requirements were extracted for this task.",
    label: "Requirement Coverage",
    required: false,
    status: "info",
  };
}

function reviewerQualityCheck(
  preview: DiffVerificationPreviewResponse | null,
): QualityGateCheck {
  if (!preview?.review_report || preview.review_report.skipped) {
    return {
      detail: "No Architect reviewer constraints were attached to this preview.",
      label: "Reviewer",
      required: false,
      status: "info",
    };
  }
  if (preview.review_report.passed === false) {
    const findings =
      preview.review_report.findings
        ?.map((finding) => `${finding.id ?? "finding"}: ${finding.details ?? ""}`.trim())
        .filter(Boolean)
        .join("; ") || "Architect reviewer found blocking issues.";
    return {
      detail: findings,
      label: "Reviewer",
      required: true,
      status: "fail",
    };
  }
  return {
    detail: "Architect reviewer constraints passed.",
    label: "Reviewer",
    required: true,
    status: "pass",
  };
}

function llmReviewerQualityCheck(
  preview: DiffVerificationPreviewResponse | null,
): QualityGateCheck {
  if (!preview?.llm_review_report || preview.llm_review_report.skipped) {
    return {
      detail:
        preview?.llm_review_report?.reason === "reviewer_model_not_configured"
          ? "LLM Reviewer is not configured; deterministic review still ran."
          : "No LLM Reviewer findings for this preview.",
      label: "Reviewer Advisory",
      required: false,
      status: "info",
    };
  }
  if (preview.llm_review_report.findings?.length) {
    const findings = preview.llm_review_report.findings
      .map((finding) => `${finding.id ?? "finding"}: ${finding.details ?? ""}`.trim())
      .filter(Boolean)
      .join("; ");
    return {
      detail: findings || "LLM Reviewer found advisory issues.",
      label: "Reviewer Advisory",
      required: false,
      status: "advisory",
    };
  }
  return {
    detail: "LLM Reviewer found no advisory issues.",
    label: "Reviewer Advisory",
    required: false,
    status: "pass",
  };
}

function fallbackQualityCheck(gate: ApprovalGateState): QualityGateCheck {
  if (gate.fallbackScaffoldBlocked) {
    return {
      detail: "Fallback scaffold blocked.",
      label: "Fallback Status",
      required: true,
      status: "fail",
    };
  }
  if (gate.fallbackScaffoldGenerated && !gate.fallbackScaffoldAccepted) {
    return {
      detail: "Fallback scaffold generated; explicit acceptance is required.",
      label: "Fallback Status",
      required: true,
      status: "fail",
    };
  }
  if (gate.fallbackScaffoldGenerated) {
    return {
      detail: "Fallback scaffold explicitly accepted for a safe placeholder task.",
      label: "Fallback Status",
      required: true,
      status: "pass",
    };
  }
  return {
    detail: "No client fallback scaffold is being used.",
    label: "Fallback Status",
    required: true,
    status: "pass",
  };
}

function staleMemoryQualityCheck(
  reasonCodes: string[],
  preview: DiffVerificationPreviewResponse | null,
): QualityGateCheck {
  const staleReason = [
    ...reasonCodes,
    ...(preview?.blocked_reasons?.map((reason) => reason.reason_code) ?? []),
  ].find((reason) => reason.includes("stale") || reason.includes("target_mismatch"));

  if (staleReason) {
    return {
      detail: staleReason,
      label: "Stale Memory",
      required: true,
      status: "fail",
    };
  }
  return {
    detail: "No stale target, route, diff, or phase contamination detected.",
    label: "Stale Memory",
    required: true,
    status: "pass",
  };
}

function DiffVerificationPanel({
  state,
  onChange,
  onPreview,
  fallbackUnifiedDiff = "",
  buttonLabel = "Preview diff",
  placeholder = "Paste a proposed code change here for a read-only safety check...",
  title = "Check a Code Change",
}: {
  state: DiffVerificationState;
  onChange: (unifiedDiff: string) => void;
  onPreview: () => void;
  /** When the textarea is empty but the approval gate already carries a diff, still allow Preview. */
  fallbackUnifiedDiff?: string;
  buttonLabel?: string;
  placeholder?: string;
  title?: string;
}) {
  const status = state.preview?.status ?? "not previewed";
  const isBlocked = state.preview?.status === "blocked";
  const hasAnyDiffSource =
    state.unifiedDiff.trim().length > 0 || fallbackUnifiedDiff.trim().length > 0;

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">{title}</h2>
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
        placeholder={placeholder}
        value={state.unifiedDiff}
      />

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          className="border border-slate-900 bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:border-slate-400 disabled:bg-slate-400"
          disabled={state.isChecking || !hasAnyDiffSource}
          onClick={() => onPreview()}
          type="button"
        >
          {state.isChecking ? "Checking" : buttonLabel}
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
          {state.preview.task_spec_check && !state.preview.task_spec_check.skipped ? (
            <div
              className={`border px-3 py-2 text-sm ${
                state.preview.task_spec_check.ok
                  ? "border-green-200 bg-green-50 text-green-950"
                  : "border-red-200 bg-red-50 text-red-950"
              }`}
            >
              <div className="font-semibold">
                TaskSpec allowed-files check:{" "}
                {state.preview.task_spec_check.ok ? "passed" : "failed"}
              </div>
              {!state.preview.task_spec_check.ok &&
              state.preview.task_spec_check.reason_codes?.includes(
                "task_spec_allowed_file_violation",
              ) ? (
                <div className="mt-1">
                  TaskSpec blocked this diff because it touches files outside the allowed list.
                </div>
              ) : null}
            </div>
          ) : null}

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

          {state.preview.requirement_coverage?.missing &&
          state.preview.requirement_coverage.missing.length > 0 ? (
            <div className="space-y-2 border border-red-200 bg-red-50 p-3">
              <h3 className="text-sm font-semibold text-red-950">Missing Requirements</h3>
              {state.preview.requirement_coverage.missing.map((item) => (
                <div
                  className="border border-red-200 bg-white px-3 py-2 text-sm text-red-900"
                  key={item}
                >
                  {item}
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

export function LongRunningTaskPanel({
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
  const visibleState = longTaskVisibleState(task);
  const canPoll = Boolean(task) && !isTerminalLongTaskStatus(task?.status);
  const canCancel = Boolean(task) && !isTerminalLongTaskStatus(task?.status);
  const currentRole = normalizeLongTaskRole(task?.current_agent_role);
  const openDiffs = task?.open_diffs ?? [];
  const postApplyPending = isPostApplyVerificationPending(task);
  const verificationComplete = isVerificationCompleteState(task);
  const taskActionsObsolete = Boolean(task) && isPostApplyOrDoneState(task);
  const progressCopy = task ? longTaskProgressCopy(task) : null;
  const progressPercent = verificationComplete ? 100 : Math.min(100, Math.max(0, task?.progress ?? 0));

  return (
    <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Long Task Tracker</h2>
        <div
          className={`border px-2 py-1 text-xs font-semibold ${
            visibleState.tone === "danger"
              ? "border-red-300 bg-red-50 text-red-900"
              : visibleState.tone === "success"
                ? "border-green-300 bg-green-50 text-green-900"
                : visibleState.tone === "warning"
                  ? "border-yellow-300 bg-yellow-50 text-yellow-900"
                  : "border-slate-300 bg-slate-50 text-slate-700"
          }`}
        >
          {visibleState.label}
        </div>
      </div>

      <textarea
        className="mt-3 h-24 w-full resize-y border border-slate-300 bg-white p-3 text-sm text-slate-900 outline-none focus:border-slate-600"
        onChange={(event) => onDescriptionChange(event.target.value)}
        value={state.description}
      />

      {taskActionsObsolete ? (
        <div className="mt-3 border border-yellow-300 bg-yellow-50 px-3 py-2 text-sm font-semibold text-yellow-950">
          {postApplyPending
            ? "Task is already applied; verification is pending."
            : "Task is complete."}
        </div>
      ) : (
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
      )}

      {state.error ? (
        <div className="mt-3 border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
          {state.error}
        </div>
      ) : null}

      {task ? (
        <div className="mt-3 space-y-3">
          <div className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
            <span className="font-semibold text-slate-900">{progressCopy?.primary}</span>
            {progressCopy?.secondary ? (
              <span className="ml-2 text-xs text-slate-500">{progressCopy.secondary}</span>
            ) : null}{" "}
            | Would run commands:{" "}
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
              style={{ width: `${progressPercent}%` }}
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

function longTaskProgressCopy(task: LongRunningTaskPayload): {
  primary: string;
  secondary?: string;
} {
  if (isVerificationCompleteState(task)) {
    return {
      primary: "Verification complete",
      secondary: "Progress: 100%",
    };
  }
  if (isPostApplyVerificationPending(task)) {
    return {
      primary: "Waiting for post-apply verification",
      secondary: `Internal progress: ${task.progress ?? 0}%`,
    };
  }
  if (isNoDiffTerminalLongTaskStatus(task.status)) {
    return {
      primary: NO_APPROVABLE_DIFF_MESSAGE,
      secondary: `Progress stopped at ${task.progress ?? 0}%`,
    };
  }
  if (task.status === "blocked" && task.current_agent_role === "coder") {
    return {
      primary: "Blocked before diff",
      secondary: `Progress: ${task.progress ?? 0}%`,
    };
  }
  return {
    primary: `Progress: ${task.progress ?? 0}%`,
  };
}

export function longTaskVisibleState(task?: LongRunningTaskPayload | null): {
  label: string;
  tone: "danger" | "muted" | "success" | "warning";
} {
  if (!task) {
    return { label: "Not started", tone: "muted" };
  }
  if (isVerificationCompleteState(task)) {
    return { label: "Verification complete", tone: "success" };
  }
  if (isPostApplyVerificationPending(task)) {
    return {
      label: task.post_apply_verification?.docs_only
        ? "Docs-only verification ready"
        : "Applied, verification required",
      tone: "warning",
    };
  }
  if (isNoDiffTerminalLongTaskStatus(task.status)) {
    return { label: `Blocked: ${task.status}`, tone: "danger" };
  }
  if (
    task.status === "blocked" ||
    task.status === "cancelled" ||
    task.status === "coder_config_blocked" ||
    task.status === "failed_needs_human" ||
    task.status === "needs_context"
  ) {
    return { label: `Blocked: ${task.status}`, tone: "danger" };
  }
  if (isVerificationFailedStatus(task.status, task.post_apply_verification)) {
    return { label: "Verification failed", tone: "danger" };
  }
  if (task.open_diffs?.some((diff) => diff.status === "pending_verification")) {
    return { label: "Ready for approval", tone: "warning" };
  }
  return { label: `Running: ${task.status}`, tone: "warning" };
}

function isTerminalLongTaskStatus(status?: string) {
  return (
    status === "cancelled" ||
    status === "blocked" ||
    status === "blocked_after_retries" ||
    status === "blocked_no_valid_diff" ||
    status === "coder_config_blocked" ||
    status === "coder_diff_rejected" ||
    status === "completed" ||
    status === "done" ||
    status === "failed_needs_human" ||
    status === "needs_coder_diff" ||
    status === "needs_context" ||
    status === "applied_needs_verification" ||
    status === "applied_verification_failed" ||
    status === "verification_failed" ||
    status === "verification_ready" ||
    status === "verified"
  );
}

function isNoDiffTerminalLongTaskStatus(status?: string) {
  return (
    status === "blocked_no_valid_diff" ||
    status === "blocked_after_retries" ||
    status === "coder_diff_rejected" ||
    status === "needs_coder_diff"
  );
}

type TaskActivityLogKind = "sse_connected" | "stream_fallback";

export function shouldAppendTaskActivityLog(
  loggedKeys: Set<string>,
  taskId: string,
  kind: TaskActivityLogKind,
) {
  const key = `${taskId}:${kind}`;
  if (loggedKeys.has(key)) {
    return false;
  }
  loggedKeys.add(key);
  return true;
}

function approvalGateNoDiffTerminalStatus(gate: ApprovalGateState): string | null {
  if (isAlreadySatisfiedGate(gate) || gate.approvedAt || gate.execution) {
    return null;
  }
  if (gate.proposedDiff.trim() || gate.content.trim()) {
    return null;
  }
  if (gate.preview?.reason_codes?.includes("client_rejected_proposed_diff")) {
    return "coder_diff_rejected";
  }
  if (
    gate.action === "needs_coder_diff" ||
    gate.preview?.decision === "needs_coder_diff" ||
    gate.preview?.reason_codes?.includes("needs_coder_diff") === true
  ) {
    return "blocked_no_valid_diff";
  }
  return null;
}

export function deriveTerminalLongTaskStateForApproval(
  gate: ApprovalGateState,
  state: LongRunningTaskState,
): LongRunningTaskState {
  const terminalStatus = approvalGateNoDiffTerminalStatus(gate);
  const task = state.response?.task;
  if (!terminalStatus || !task) {
    return state;
  }
  if (
    task.status === "completed" ||
    task.status === "cancelled" ||
    task.status === "applied_needs_verification" ||
    task.status === "applied_verification_failed" ||
    task.status === "verification_failed" ||
    task.status === "failed_needs_human"
  ) {
    return state;
  }

  const message =
    terminalStatus === "coder_diff_rejected"
      ? CLIENT_REJECTED_BACKEND_DIFF_MESSAGE
      : NO_APPROVABLE_DIFF_MESSAGE;
  const steps = appendUniqueStrings(task.steps ?? [], [message]);
  return {
    ...state,
    error: null,
    isChecking: false,
    response: state.response
      ? {
          ...state.response,
          task: {
            ...task,
            current_agent_role: "coder",
            next_action: NO_APPROVABLE_DIFF_NEXT_ACTION,
            progress: Math.min(task.progress ?? 50, 50),
            status: terminalStatus,
            steps,
            truncated_test_results:
              terminalStatus === "coder_diff_rejected"
                ? "client_rejected_proposed_diff"
                : task.truncated_test_results,
            would_execute: false,
            writes_allowed: false,
          },
        }
      : {
          task: {
            ...task,
            current_agent_role: "coder",
            next_action: NO_APPROVABLE_DIFF_NEXT_ACTION,
            progress: Math.min(task.progress ?? 50, 50),
            status: terminalStatus,
            steps,
            truncated_test_results:
              terminalStatus === "coder_diff_rejected"
                ? "client_rejected_proposed_diff"
                : task.truncated_test_results,
            would_execute: false,
            writes_allowed: false,
          },
        },
  };
}

function appendUniqueStrings(current: string[], additions: string[]) {
  const output = [...current];
  for (const addition of additions) {
    if (addition && !output.includes(addition)) {
      output.push(addition);
    }
  }
  return output;
}

function verificationCommandLabel(check: NonNullable<PostApplyVerification["checks"]>[number]) {
  if (check.command_text) {
    return check.command_text;
  }
  if (Array.isArray(check.command)) {
    return check.command.join(" ");
  }
  return check.command ?? check.id ?? "verification check";
}

function generateVerificationFixPrompt(verification: PostApplyVerification) {
  const failed = verification.checks?.filter((check) => check.status === "failed") ?? [];
  return [
    "Generate a fix patch for the failed post-apply verification.",
    `Verification status: ${verification.status ?? "unknown"}`,
    "Failures:",
    ...(failed.length
      ? failed.map(
          (check) =>
            `- ${verificationCommandLabel(check)}: ${check.summary ?? "failed"}`,
        )
      : ["- Review post_apply_verification for failure details."]),
    "Return ONLY a clean unified diff.",
  ].join("\n");
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

type PipelineStageId = "architect" | "coder" | "verifier" | "approval";

const pipelineStages: { id: PipelineStageId; label: string }[] = [
  { id: "architect", label: "architect" },
  { id: "coder", label: "coder" },
  { id: "verifier", label: "verifier" },
  { id: "approval", label: "approval" },
];

function SwarmRolePipeline({
  approvalGate,
  task,
}: {
  approvalGate: ApprovalGateState;
  task: LongRunningTaskPayload | null;
}) {
  const activeStage = activePipelineStage(task, approvalGate);
  const coderBlocked = approvalGate.preview?.reason_codes?.some((reason) =>
    reason.startsWith("coder_"),
  );
  const errorStage: PipelineStageId | null = coderBlocked
    ? "coder"
    : task?.status === "failed_needs_human" ||
        task?.status === "blocked" ||
        task?.status === "needs_context"
      ? roleToPipelineStage(task.current_agent_role)
      : null;
  const elapsed = pipelineElapsedByStage(task, activeStage);
  const transitions = task?.role_transitions ?? [];
  const latest = transitions[transitions.length - 1];

  return (
    <section className="border-b border-slate-300 bg-slate-50 px-4 py-3">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {pipelineStages.map((stage, index) => (
            <div className="flex items-center gap-2" key={stage.id}>
              <div
                className={`border px-3 py-1.5 text-xs font-semibold ${
                  errorStage === stage.id
                    ? "border-red-500 bg-red-50 text-red-950"
                    : activeStage === stage.id
                    ? "border-cyan-500 bg-cyan-50 text-cyan-950"
                    : elapsed[stage.id] > 0
                      ? "border-green-300 bg-green-50 text-green-900"
                      : "border-slate-300 bg-white text-slate-600"
                }`}
              >
                <span>{stage.label}</span>
                <span className="ml-2 font-normal">{formatDurationMs(elapsed[stage.id])}</span>
              </div>
              {index < pipelineStages.length - 1 ? (
                <span className="text-slate-400">-&gt;</span>
              ) : null}
            </div>
          ))}
        </div>
        <div className="text-xs text-slate-600">
          {errorStage
            ? `Stalled in ${pipelineStages.find((stage) => stage.id === errorStage)?.label ?? errorStage}: ${
                approvalGate.preview?.safety_message ||
                task?.truncated_test_results ||
                task?.next_action ||
                "human review required"
              }`
            : latest
            ? `${longTaskRoleLabel(normalizeLongTaskRole(latest.from))} -> ${longTaskRoleLabel(
                normalizeLongTaskRole(latest.to),
              )}: ${latest.reason ?? "role changed"}`
            : "Waiting for role transitions."}
        </div>
      </div>
    </section>
  );
}

function activePipelineStage(
  task: LongRunningTaskPayload | null,
  approvalGate: ApprovalGateState,
): PipelineStageId {
  if (approvalGate.preview?.reason_codes?.some((reason) => reason.startsWith("coder_"))) {
    return "coder";
  }
  if (
    task?.status === "failed_needs_human" ||
    task?.status === "blocked" ||
    task?.status === "needs_context"
  ) {
    return roleToPipelineStage(task.current_agent_role);
  }
  const hasApprovalSurface = Boolean(
    approvalGate.preview ||
      approvalGate.proposedDiff ||
      approvalGate.content ||
      approvalGate.action === "needs_coder_diff",
  );
  if (hasApprovalSurface && task?.current_agent_role !== "architect") {
    return "approval";
  }
  const role = normalizeLongTaskRole(task?.current_agent_role);
  return role === "debugger" ? "verifier" : role;
}

function pipelineElapsedByStage(
  task: LongRunningTaskPayload | null,
  activeStage: PipelineStageId,
): Record<PipelineStageId, number> {
  const elapsed: Record<PipelineStageId, number> = {
    architect: 0,
    coder: 0,
    verifier: 0,
    approval: 0,
  };
  if (!task?.created_at) {
    return elapsed;
  }
  const transitions = (task.role_transitions ?? [])
    .map((transition) => ({
      ...transition,
      atMs: Date.parse(transition.at ?? ""),
    }))
    .filter((transition) => Number.isFinite(transition.atMs))
    .sort((a, b) => a.atMs - b.atMs);
  let currentStage: PipelineStageId = "architect";
  let startedAt = Date.parse(task.created_at);
  const endAt = Date.parse(task.updated_at ?? "") || Date.now();
  for (const transition of transitions) {
    elapsed[currentStage] += Math.max(0, transition.atMs - startedAt);
    currentStage = roleToPipelineStage(transition.to);
    startedAt = transition.atMs;
  }
  elapsed[activeStage] += Math.max(0, endAt - startedAt);
  return elapsed;
}

function roleToPipelineStage(role?: string): PipelineStageId {
  const normalized = normalizeLongTaskRole(role);
  return normalized === "debugger" ? "verifier" : normalized;
}

function formatDurationMs(ms: number): string {
  if (ms <= 0) {
    return "0s";
  }
  const seconds = Math.max(1, Math.round(ms / 1000));
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}m ${remainder}s`;
}

export function ApprovalGatePanel({
  architectPlan,
  gate,
  diffVerification,
  coderAgentLocalDiff,
  onActionChange,
  onApprove,
  onContentChange,
  onDeny,
  onPreview,
  task,
  onTargetChange,
  resolvedTargetPath,
}: {
  architectPlan: ArchitectPlanResponse | null;
  gate: ApprovalGateState;
  diffVerification: DiffVerificationState;
  coderAgentLocalDiff: boolean;
  onActionChange: (action: string) => void;
  onApprove: (event: MouseEvent<HTMLButtonElement>) => void;
  onContentChange: (content: string) => void;
  onDeny: (reasonCode: ApprovalRejectionReason) => void;
  onPreview: () => void;
  task?: LongRunningTaskPayload | null;
  onTargetChange: (target: string) => void;
  resolvedTargetPath?: string;
}) {
  const [showRejectReasons, setShowRejectReasons] = useState(false);
  const isBlocked = gate.preview?.decision === "blocked";
  const alreadySatisfied = isAlreadySatisfiedGate(gate);
  const needsCoderDiff =
    !alreadySatisfied &&
    (gate.action === "needs_coder_diff" ||
      gate.preview?.decision === "needs_coder_diff" ||
      gate.preview?.reason_codes?.includes("needs_coder_diff") === true);
  const diffPreviewBlocked = diffVerification.preview?.status === "blocked";
  const applyCheckOk = diffVerification.preview?.git_apply_check_ok !== false;
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
  const qualityRequiredPasses = buildQualityGateChecks({
    diffVerification,
    gate,
    resolvedTargetPath,
  }).every((check) => !check.required || check.status === "pass");
  const canApprove =
    Boolean(gate.preview) &&
    !isBlocked &&
    !diffPreviewBlocked &&
    applyCheckOk &&
    qualityRequiredPasses &&
    (gate.preview?.requires_human_approval === true ||
      (fileWritesAllowed && coderAgentLocalDiff && hasDiffPayload)) &&
    (!fileMutationIntent || canExecuteApprovedAction);
  const hasProposedAction = gate.action.trim().length > 0 || gate.target.trim().length > 0;
  const hasExecutableApprovalPayload = canExecuteApprovedAction || alreadySatisfied;
  const showCheckAction = gate.action.trim().length > 0 || hasExecutableApprovalPayload;
  const showApprovalControls = showCheckAction || Boolean(gate.preview);
  const postApplyLocked = isPostApplyOrDoneState(task, gate.execution);
  const verificationComplete = isVerificationCompleteState(task, gate.execution);
  const exactCommand = formatExactApprovalCommand(gate.action, gate.target);
  const subjectiveImprovementNeedsDiff =
    gate.preview?.reason_codes?.includes(SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE) ===
      true ||
    gate.preview?.reason_codes?.includes(VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE) ===
      true;
  const shallowVisualDiff =
    gate.preview?.reason_codes?.includes(VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE) ===
    true;
  const bundleSnapshotDrift =
    gate.preview?.reason_codes?.includes(BUNDLE_SNAPSHOT_DRIFT_REASON_CODE) === true;
  const clientRejectedBackendDiff =
    gate.preview?.reason_codes?.includes("client_rejected_proposed_diff") === true;
  const fallbackScaffoldBlocked = !alreadySatisfied && gate.fallbackScaffoldBlocked;


  if (alreadySatisfied) {
    return (
      <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-base font-semibold text-slate-950">Approval Gate</h2>
          <div className="border border-green-300 bg-green-50 px-2 py-1 text-xs font-semibold text-green-900">
            no_approval_needed
          </div>
        </div>

        <div className="mt-3 border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-950">
          <div className="font-semibold">No approval action is available because no file change is needed.</div>
          <div className="mt-1">Skipped because there are no changes to apply.</div>
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <TelemetryStat label="State" value="no_approval_needed" />
          <TelemetryStat label="Target" value={gate.target || "No target proposed"} />
        </div>
      </section>
    );
  }

  if (postApplyLocked) {
    return (
      <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-base font-semibold text-slate-950">Approval Gate</h2>
          <WorkflowBadge tone={verificationComplete ? "success" : "warning"}>
            {verificationComplete ? "verified" : "applied"}
          </WorkflowBadge>
        </div>

        <div className="mt-3 space-y-3">
          <ApprovalArchitectMiniSummary
            plan={architectPlan}
            resolvedTargetPath={resolvedTargetPath}
          />
          <ApprovalCoderMiniSummary diffVerification={diffVerification} gate={gate} />
        </div>

        <div className="mt-3 border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-950">
          <div className="font-semibold">
            {verificationComplete
              ? "This diff has already been approved, applied, and verified."
              : "This diff has already been approved and applied. Complete verification below."}
          </div>
          {!verificationComplete ? (
            <div className="mt-1">Complete verification in Step 6 before treating the task as done.</div>
          ) : null}
        </div>

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
      </section>
    );
  }

  if (needsCoderDiff) {
    return (
      <section className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-base font-semibold text-slate-950">Approval Gate</h2>
          <div className="border border-slate-300 bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-700">
            needs_coder_diff
          </div>
        </div>

        <div className="mt-3 space-y-3">
          <ApprovalArchitectMiniSummary
            plan={architectPlan}
            resolvedTargetPath={resolvedTargetPath}
          />
          <ApprovalCoderMiniSummary diffVerification={diffVerification} gate={gate} />
        </div>

        <div className="mt-3 border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-950">
          <div className="font-semibold">No approval action is available yet</div>
          <div className="mt-1">
            {shallowVisualDiff
              ? "The generated diff was too shallow for this visual improvement task. It did not materially change styling, layout, hover, active, glow, spacing, or animation behavior."
              : subjectiveImprovementNeedsDiff
              ? "This is a subjective visual improvement task. No diff was produced, so it cannot be marked already satisfied."
              : bundleSnapshotDrift
              ? "Bundle changed since the Architect plan was created. Regenerate the plan, then retry Coder Agent."
              : clientRejectedBackendDiff
                ? CLIENT_REJECTED_BACKEND_DIFF_MESSAGE
                : NO_APPROVABLE_DIFF_NEXT_ACTION}
          </div>
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <TelemetryStat label="State" value="needs_coder_diff" />
          <TelemetryStat label="Target" value={gate.target || "No target proposed"} />
        </div>

        {gate.preview ? (
          <div className="mt-3 space-y-2">
            <div className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
              {gate.preview.safety_message ??
                gate.preview.next_step ??
                "No safety message returned."}
            </div>
            {subjectiveImprovementNeedsDiff ? (
              <div className="flex flex-wrap gap-2">
                {[
                  "Retry Local Coder with stricter output repair",
                  ...(bundleSnapshotDrift ? ["Regenerate plan"] : []),
                  "Copy manual browser prompt",
                  "Use Cloud/API route, if configured",
                  "Manual visual review",
                ].map((action) => (
                  <span
                    className="border border-amber-300 bg-white px-2 py-1 text-xs font-semibold text-amber-900"
                    key={action}
                  >
                    {action}
                  </span>
                ))}
              </div>
            ) : null}
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
            <h3 className="mt-3 text-sm font-semibold text-slate-950">3. Approve / Reject</h3>
            <button
              className="border border-red-700 bg-white px-3 py-2 text-sm font-semibold text-red-800 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
              disabled={!gate.preview || gate.isChecking}
              onClick={() => setShowRejectReasons((open) => !open)}
              type="button"
            >
              Reject
            </button>
            <RejectReasonPicker
              disabled={!gate.preview || gate.isChecking}
              onReject={(reason) => {
                setShowRejectReasons(false);
                onDeny(reason);
              }}
              open={showRejectReasons}
              onOpenChange={setShowRejectReasons}
            />
          </div>
        ) : null}
      </section>
    );
  }

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

      <div className="mt-3 space-y-3">
        <ApprovalArchitectMiniSummary
          plan={architectPlan}
          resolvedTargetPath={resolvedTargetPath}
        />
        <ApprovalCoderMiniSummary diffVerification={diffVerification} gate={gate} />
      </div>

      {needsCoderDiff ? (
        <div className="mt-3 border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-950">
          <div className="font-semibold">needs_coder_diff</div>
          <div className="mt-1">
            Retry Local Coder with stricter output repair, or copy the manual browser prompt.
          </div>
        </div>
      ) : null}

      {fallbackScaffoldBlocked ? (
        <div className="mt-3 border border-amber-300 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-950">
          Fallback scaffold blocked
        </div>
      ) : null}

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

      {showApprovalControls ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {showCheckAction ? (
            <button
              className="border border-slate-900 bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:border-slate-400 disabled:bg-slate-400"
              disabled={
                gate.isChecking ||
                !hasProposedAction ||
                !gate.action.trim() ||
                (!hasExecutableApprovalPayload && !gate.preview) ||
                needsCoderDiff
              }
              onClick={onPreview}
              type="button"
            >
              {gate.isChecking ? "Checking" : "Check action"}
            </button>
          ) : null}
          {hasExecutableApprovalPayload ? (
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
          ) : null}
          <button
            className="border border-red-700 bg-white px-3 py-2 text-sm font-semibold text-red-800 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
            disabled={!gate.preview || gate.isChecking}
            onClick={() => setShowRejectReasons((open) => !open)}
            type="button"
          >
            Reject
          </button>
        </div>
      ) : (
        <div className="mt-3 border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
          Approval controls are unavailable until the backend provides a diff or an explicit verified action.
        </div>
      )}

      <RejectReasonPicker
        disabled={!gate.preview || gate.isChecking}
        onReject={(reason) => {
          setShowRejectReasons(false);
          onDeny(reason);
        }}
        open={showRejectReasons}
        onOpenChange={setShowRejectReasons}
      />

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

function ApprovalArchitectMiniSummary({
  plan,
  resolvedTargetPath,
}: {
  plan: ArchitectPlanResponse | null;
  resolvedTargetPath?: string;
}) {
  const target = architectPlanDisplayTarget(plan, resolvedTargetPath) || "No target";
  const criteria = plan?.coder_packet?.acceptance_criteria ?? [];
  const checks = plan?.verification_plan?.required_checks ?? [];
  const taskSpec = taskSpecForPlan(plan);
  const planSource = deterministicPlanSourceLabel(plan);
  return (
    <section className="border border-slate-300 bg-slate-50 px-3 py-3 text-sm">
      <h3 className="font-semibold text-slate-950">1. Architect Plan</h3>
      <div className="mt-2 grid gap-2 md:grid-cols-2">
        <TelemetryStat label="Target" value={target} />
        <TelemetryStat
          label="Class"
          value={plan?.classification?.task_class ?? "unknown"}
        />
        {planSource ? <TelemetryStat label="Source" value={planSource} /> : null}
        {taskSpec?.allowed_files?.length ? (
          <TelemetryStat label="Allowed files" value={taskSpec.allowed_files.join(", ")} />
        ) : null}
      </div>
      <div className="mt-2 grid gap-2 md:grid-cols-2">
        <div>
          <div className="text-xs font-semibold uppercase text-slate-500">
            Acceptance criteria
          </div>
          <ul className="mt-1 space-y-1">
            {(criteria.length > 0 ? criteria : [{ description: "No criteria returned." }]).map(
              (criterion, index) => (
                <li className="text-slate-700" key={criterion.id ?? index}>
                  <span className="mr-1 text-green-700">ok</span>
                  {criterion.description ?? criterion.id}
                </li>
              ),
            )}
          </ul>
        </div>
        <div>
          <div className="text-xs font-semibold uppercase text-slate-500">
            Verification checks
          </div>
          <ul className="mt-1 space-y-1">
            {(checks.length > 0 ? checks : [{ id: "No checks returned.", command: [] }]).map(
              (check, index) => (
                <li className="text-slate-700" key={check.id ?? index}>
                  <span className="mr-1">{check.blocking ? "!" : "i"}</span>
                  {check.id ?? "check"} {(check.command ?? []).join(" ")}
                </li>
              ),
            )}
          </ul>
        </div>
      </div>
    </section>
  );
}

function numericDiagnostic(diagnostics: Record<string, unknown> | undefined, key: string): number | null {
  const value = diagnostics?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function stringDiagnostic(diagnostics: Record<string, unknown> | undefined, key: string): string {
  const value = diagnostics?.[key];
  return typeof value === "string" ? value.trim() : "";
}

function listDiagnostic(diagnostics: Record<string, unknown> | undefined, key: string): string[] {
  const value = diagnostics?.[key];
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function ApprovalCoderMiniSummary({
  diffVerification,
  gate,
}: {
  diffVerification: DiffVerificationState;
  gate: ApprovalGateState;
}) {
  const diffPayload = unifiedDiffPayloadOrEmpty(
    gate.proposedDiff || diffVerification.unifiedDiff,
  );
  const checks = buildQualityGateChecks({ diffVerification, gate });
  const attemptCount = numericDiagnostic(gate.coderDiagnostics, "coder_attempt_count");
  const retryCount = numericDiagnostic(gate.coderDiagnostics, "reviewer_retry_count");
  const retryReason = stringDiagnostic(gate.coderDiagnostics, "retry_reason");
  const blockerText = listDiagnostic(gate.coderDiagnostics, "last_reviewer_blockers").join("; ");
  return (
    <section className="border border-slate-300 bg-slate-50 px-3 py-3 text-sm">
      <h3 className="font-semibold text-slate-950">2. Coder Output</h3>
      {retryCount || retryReason ? (
        <div className="mt-2 border border-yellow-200 bg-yellow-50 px-3 py-2 text-xs text-yellow-950">
          <span className="font-semibold">
            {retryCount ? `Attempt ${attemptCount ?? retryCount + 1}` : "Attempt 1"}
          </span>
          {retryCount ? " after reviewer feedback" : " prepared without reviewer retry"}
          {blockerText ? ` (${blockerText})` : ""}
        </div>
      ) : null}
      <div className="mt-2 flex flex-wrap gap-2">
        {checks.map((check) => (
          <span
            className={`border px-2 py-1 text-xs font-semibold ${
              check.status === "pass"
                ? "border-green-300 bg-green-50 text-green-900"
                : check.status === "fail"
                  ? "border-red-300 bg-red-50 text-red-900"
                  : check.status === "waiting"
                    ? "border-yellow-300 bg-yellow-50 text-yellow-900"
                    : "border-slate-300 bg-white text-slate-700"
            }`}
            key={check.label}
          >
            {check.status} {check.label}
          </span>
        ))}
      </div>
      <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap border border-slate-200 bg-white p-3 font-mono text-xs leading-5 text-slate-800">
        {diffPayload || "No backend Coder diff is available yet."}
      </pre>
    </section>
  );
}

function RejectReasonPicker({
  disabled,
  onOpenChange,
  onReject,
  open,
}: {
  disabled: boolean;
  onOpenChange: (open: boolean) => void;
  onReject: (reasonCode: ApprovalRejectionReason) => void;
  open: boolean;
}) {
  if (!open) {
    return null;
  }
  return (
    <div className="mt-3 border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-950">
      <div className="font-semibold">Why reject this plan?</div>
      <div className="mt-2 flex flex-wrap gap-2">
        {approvalRejectionReasons.map((reason) => (
          <button
            className="border border-red-300 bg-white px-2 py-1 text-xs font-semibold text-red-900 hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={disabled}
            key={reason.value}
            onClick={() => onReject(reason.value)}
            type="button"
          >
            {reason.label}
          </button>
        ))}
        <button
          className="border border-slate-300 bg-white px-2 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100"
          onClick={() => onOpenChange(false)}
          type="button"
        >
          Cancel
        </button>
      </div>
    </div>
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

function modelLabelForCoderPacket(
  promptPacket: PromptPacketResponse,
  decision: ProxyRouteDecisionResponse,
  coderReasonCode: string,
) {
  if (
    coderReasonCode === "coder_model_not_configured" ||
    coderReasonCode === "coder_empty_model_response"
  ) {
    return coderReasonCode;
  }
  if (
    typeof promptPacket.coder_diagnostics?.selected_model_alias === "string" &&
    promptPacket.coder_diagnostics.selected_model_alias.trim()
  ) {
    return promptPacket.coder_diagnostics.selected_model_alias;
  }
  if (
    typeof promptPacket.coderDiagnostics?.selected_model_alias === "string" &&
    promptPacket.coderDiagnostics.selected_model_alias.trim()
  ) {
    return promptPacket.coderDiagnostics.selected_model_alias;
  }
  return modelFromDecision(decision);
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

  const parsed = parseRouteDecisionPayload(payload);
  if (!parsed.ok) {
    throw new Error(parsed.error);
  }

  return parsed.decision as ProxyRouteDecisionResponse;
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
  const { response, payload } = await fetchJsonWithTimeout(
    "/v1/decisions/route",
    {
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
    },
    { label: "Research preview (route)", timeoutMs: 90_000 },
  );

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

  const parsed = parseRouteDecisionPayload(payload);
  if (!parsed.ok) {
    throw new Error(parsed.error);
  }

  return parsed.decision as ProxyRouteDecisionResponse;
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
  const { response, payload } = await fetchJsonWithTimeout(
    "/v1/decisions/prompt-packet",
    {
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
    },
    { label: "Prompt packet", timeoutMs: 180_000 },
  );

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
  options?: {
    activeTaskId?: string;
    nextPromptAction?: string;
    routeType?: string;
    taskText?: string;
  },
): Promise<DiffVerificationPreviewResponse> {
  const body: Record<string, unknown> = { unified_diff: unifiedDiff };
  const activeTaskId = options?.activeTaskId?.trim();
  if (activeTaskId) {
    body.active_task_id = activeTaskId;
  }
  const routeType = options?.routeType;
  if (routeType && routeType !== "not run" && routeType !== "pending") {
    body.route_type = routeType;
  }
  const nextPromptAction = options?.nextPromptAction?.trim();
  if (nextPromptAction) {
    body.next_prompt_action = nextPromptAction;
  }
  const taskText = options?.taskText?.trim();
  if (taskText) {
    body.task_text = taskText;
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

async function callManualResultPreview(
  payloadText: string,
  options: {
    activeTaskId?: string;
    nextPromptAction?: string;
    routeType?: string;
    taskSpec?: CoderTaskSpecResponse;
    taskText?: string;
  } = {},
): Promise<DiffVerificationPreviewResponse> {
  const body: Record<string, unknown> = { payload: payloadText };
  const activeTaskId = options.activeTaskId?.trim();
  if (activeTaskId) {
    body.active_task_id = activeTaskId;
  }
  if (options.routeType && options.routeType !== "not run" && options.routeType !== "pending") {
    body.route_type = options.routeType;
  }
  const nextPromptAction = options.nextPromptAction?.trim();
  if (nextPromptAction) {
    body.next_prompt_action = nextPromptAction;
  }
  const taskText = options.taskText?.trim();
  if (taskText) {
    body.task_text = taskText;
  }
  if (options.taskSpec) {
    body.task_spec = options.taskSpec;
  }
  const response = await fetch("/v1/verification/manual-result-preview", {
    body: JSON.stringify(body),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });
  const payload = await readJsonResponse(response, "Manual result preview");

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
        : `Manual result preview failed with status ${response.status}.`;
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

async function callLongRunningTaskAdvance(
  taskId: string,
): Promise<LongRunningTaskResponse> {
  const response = await fetch(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/advance`,
    {
      body: "{}",
      headers: {
        "content-type": "application/json",
      },
      method: "POST",
    },
  );

  return parseLongRunningTaskResponse(response, "Long-running task advance");
}

async function callLongRunningTaskPlan(
  taskId: string,
): Promise<ArchitectPlanResponse | null> {
  const response = await fetch(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/plan`,
    {
      method: "GET",
    },
  );
  const payload = await readJsonResponse(response, "Long-running task plan");
  if (!response.ok) {
    throw new Error("No architect plan is available for this task.");
  }
  if (isPlanUnavailableEnvelope(payload)) {
    return null;
  }
  return payload as ArchitectPlanResponse;
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

async function callLongRunningTaskRejectPlan(
  taskId: string,
  reasonCode: ApprovalRejectionReason,
): Promise<LongRunningTaskResponse & { message?: string }> {
  const response = await fetch(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/reject-plan`,
    {
      body: JSON.stringify({
        reason_code: reasonCode,
        rejected_by: "human",
      }),
      headers: {
        "content-type": "application/json",
      },
      method: "POST",
    },
  );

  return parseLongRunningTaskResponse(response, "Long-running task plan rejection") as Promise<
    LongRunningTaskResponse & { message?: string }
  >;
}

async function callLongRunningTaskDocsOnlyVerify(
  taskId: string,
): Promise<LongRunningTaskResponse> {
  const response = await fetch(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/verify`,
    {
      body: JSON.stringify({
        confirm_backup_audit_present: true,
        confirm_changed_files_reviewed: true,
        confirm_expected_change_present: true,
        confirm_no_unintended_files: true,
        verification_note: "Docs-only change verified.",
      }),
      headers: {
        "content-type": "application/json",
      },
      method: "POST",
    },
  );

  return parseLongRunningTaskResponse(response, "Long-running task verification");
}

async function callLongRunningTaskCodeVerify(
  taskId: string,
): Promise<LongRunningTaskResponse> {
  const response = await fetch(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/verify`,
    {
      body: JSON.stringify({
        run_code_verification: true,
      }),
      headers: {
        "content-type": "application/json",
      },
      method: "POST",
    },
  );

  return parseLongRunningTaskResponse(response, "Long-running task code verification");
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
  if (typeof value !== "string") {
    return false;
  }
  const normalized = value.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
  return (
    normalized.includes("diff --git ") ||
    normalized.includes("\n@@ ") ||
    /^@@\s/m.test(normalized) ||
    (normalized.startsWith("--- ") && normalized.includes("\n+++ "))
  );
}

export function promptTextForCoderPacket({
  coderBlocked,
  coderBlockedReason,
  coderDiffReady,
  coderNeededContext,
  promptText,
}: {
  coderBlocked: boolean;
  coderBlockedReason: string;
  coderDiffReady: boolean;
  coderNeededContext: string;
  promptText?: string;
}) {
  if (coderDiffReady) {
    return "Coder Agent produced replacement content; the backend generated the unified diff for the approval gate (see Proposal / Diff Preview).";
  }
  if (
    coderBlocked &&
    typeof promptText === "string" &&
    promptText.includes("Manual Browser Prompt")
  ) {
    return promptText;
  }
  if (coderBlocked) {
    return coderNeededContext
      ? `${coderBlockedReason} Needed context: ${coderNeededContext}`
      : coderBlockedReason;
  }
  if (
    typeof promptText === "string" &&
    promptText.includes("backend-generated proposed_diff")
  ) {
    return CLIENT_REJECTED_BACKEND_DIFF_MESSAGE;
  }
  if (
    typeof promptText === "string" &&
    promptText.includes("backend converted into a unified diff")
  ) {
    return "Coder Agent did not provide an approvable unified diff for this run. Retry Local Coder with stricter output repair, or copy the manual browser prompt.";
  }
  return promptText ?? "No prompt_text returned.";
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
  if (/^Prompt packet timed out after/i.test(message)) {
    return "Coder timed out before producing a diff. No approval action is available; narrow the task or retry after increasing the proxy Coder deadline.";
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

function manualBrowserPromptForCurrentState({
  architectPlan,
  currentTask,
  promptText,
  target,
}: {
  architectPlan: ArchitectPlanResponse | null;
  currentTask: string;
  promptText: string;
  target: string;
}) {
  if (promptText.includes("Manual Browser Prompt: SpiritOS Coder Recovery")) {
    return promptText;
  }

  const taskSpec = taskSpecForPlan(architectPlan) ?? {};
  const resolvedTarget =
    normalizeRepoRelativePath(target) ||
    normalizeRepoRelativePath(String(taskSpec.target ?? "")) ||
    architectTargetPath(architectPlan);
  const allowedFiles = taskSpec.allowed_files ?? taskSpec.allowedFiles ?? [];
  const forbiddenFiles = taskSpec.forbidden_files ?? taskSpec.forbiddenFiles ?? [];
  const literalRequirements =
    taskSpec.literal_requirements ?? taskSpec.literalRequirements ?? [];
  const verification = taskSpec.verification ?? [];
  const criteria = architectPlan?.coder_packet?.acceptance_criteria ?? [];

  return [
    "# Manual Browser Prompt: SpiritOS Coder Recovery",
    "",
    "Use this in GPT, Gemini, Grok, Claude, or another browser model.",
    "Return the model output to the SpiritOS portal for validation. Do not bypass the portal.",
    "",
    "## Task",
    currentTask.trim() || `Modify ${resolvedTarget}.`,
    "",
    "## Required Output",
    "Return only JSON. Prefer content_lines.",
    "",
    "```json",
    JSON.stringify(
      {
        action: "replace_file",
        target: resolvedTarget || "REPO_RELATIVE_PATH",
        content_lines: ["line 1", "line 2"],
        notes: "short optional note",
      },
      null,
      2,
    ),
    "```",
    "",
    "## TaskSpec",
    "```json",
    JSON.stringify(
      {
        target: resolvedTarget || null,
        allowed_files: allowedFiles,
        forbidden_files: forbiddenFiles,
        literal_requirements: literalRequirements,
        verification,
      },
      null,
      2,
    ),
    "```",
    "",
    "## Acceptance Criteria",
    ...(criteria.length
      ? criteria.map((item) => `- ${item.description ?? item.id ?? "Criterion"}`)
      : ["- Modify only the TaskSpec target.", "- Preserve runtime behavior unless the task says otherwise."]),
    "",
    "## Portal Safety Contract",
    "- Target must exactly match TaskSpec.target.",
    "- Only edit files in TaskSpec.allowed_files.",
    "- Paste the returned JSON or diff back into SpiritOS.",
    "- SpiritOS must still run target-only, TaskSpec.allowed_files, git apply, reviewer, approval, protected apply, and verification.",
    "",
    "If you do not have enough file content to produce a safe full replacement, return blocked JSON explaining the missing context.",
  ].join("\n");
}

function restoredArchitectPlanForHistoryEntry(
  entry: CodingHistoryEntry,
): ArchitectPlanResponse | null {
  const target = explicitTargetFromText(entry.task);
  if (!target) {
    return null;
  }
  return {
    coder_packet: {
      acceptance_criteria: [
        {
          description: `Modify only ${target}.`,
          id: "target-only",
          kind: "behavioral",
        },
      ],
      constraints: {
        must_contain: [],
        must_not_contain: [],
        preserve_exports: [],
        preserve_imports: [],
      },
      context_slices: [{ kind: "target", path: target }],
      operation: "edit",
      target_file: { exists: true, path: target },
    },
    source_task: entry.task,
    task_spec: {
      schema_version: 1,
      task_type: "modify_existing_file",
      target,
      allowed_files: [target],
      forbidden_files: [],
      literal_requirements: [],
      verification: ["git apply check", "target-only"],
      risk_tier: "low",
      source: "restored_history",
    },
    verification_plan: {
      required_checks: [
        { blocking: true, command: ["git", "apply", "--check"], id: "git_apply_check" },
      ],
    },
  };
}

function explicitTargetFromText(text: string) {
  const match = text.match(/^\s*Target file:\s*(.+?)\s*$/im);
  return normalizeRepoRelativePath(match?.[1] ?? "");
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
  submittedTask,
}: {
  attachedFiles: UploadedFile[];
  decision: ProxyRouteDecisionResponse;
  memoryEntries: DecisionMemoryEntry[];
  promptPacket: PromptPacketResponse;
  priorTurns: CodingHistoryEntry[];
  runId: number;
  researchSources: ResearchSource[];
  submittedTask?: string;
}) {
  const action = routeActionForDecision(decision);
  const route = friendlyRouteName(decision.recommended_route);
  const model = modelFromDecision(decision);
  const risk = formatRiskTier(decision.risk_tier);
  const classification = friendlyTaskName(decision.task_classification);
  const context = workflowContextLabel(promptPacket, submittedTask);
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

function workflowContextLabel(
  promptPacket?: PromptPacketResponse,
  submittedTaskFirstLine?: string,
): string {
  const line = submittedTaskFirstLine?.trim().split("\n")[0]?.trim();
  if (line && line.length <= 200) {
    return line;
  }
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
  promptText,
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
  promptText?: string;
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
    submittedTask: task,
  });

  return {
    attachedFileCount: attachedFiles.length,
    completedAt,
    contextTurnCount: priorTurns.length,
    id: `${completedAt}-${runId}`,
    model: modelFromDecision(decision),
    recommendation,
    researchSourceCount: researchSources.length,
    recoveryPrompt: promptText?.includes("Manual Browser Prompt")
      ? promptText
      : undefined,
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
