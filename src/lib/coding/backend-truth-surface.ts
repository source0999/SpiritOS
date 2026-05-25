import type { CodingProviderModelOption, CodingProviderStatus } from "@/lib/coding/model-provider-status";

export type BackendTruthState =
  | "available"
  | "unavailable"
  | "config-blocked"
  | "proposal-only"
  | "not-wired";

export type BackendTruthRow = {
  authority: string;
  evidence: string;
  fallback: string;
  id: string;
  route: string;
  state: BackendTruthState;
  title: string;
};

type BackendTruthInput = {
  provider: CodingProviderStatus;
  model: CodingProviderModelOption;
};

function providerTruthState(provider: CodingProviderStatus): BackendTruthState {
  if (provider.status === "default" || provider.status === "configured") {
    return "available";
  }
  if (provider.status === "proposal-only") {
    return "proposal-only";
  }
  if (provider.status === "unavailable") {
    return "config-blocked";
  }
  return "unavailable";
}

export function buildBackendTruthRows(input: BackendTruthInput): BackendTruthRow[] {
  const providerState = providerTruthState(input.provider);

  return [
    {
      authority: "Read-only manifest route; UI does not call it during render.",
      evidence: "source_proxy/api/self_status.py exposes GET /v1/self/status.",
      fallback: "not-wired until a live read is explicitly approved and handled as read-only.",
      id: "self-status",
      route: "GET /v1/self/status",
      state: "not-wired",
      title: "Source Proxy self status",
    },
    {
      authority: "Read-only tools manifest route; no tool execution.",
      evidence: "source_proxy/api/tools_manifest.py exposes GET /v1/tools/manifest.",
      fallback: "not-wired until a live read is explicitly approved and handled as read-only.",
      id: "tools-manifest",
      route: "GET /v1/tools/manifest",
      state: "not-wired",
      title: "Tools manifest",
    },
    {
      authority: "Read/list-only workspace proof; no project creation, write, branch, commit, or push.",
      evidence: "source_proxy/api/workspace_tools.py exposes list/read routes; PR-2 UI uses helper truth.",
      fallback: "unavailable for path_escape, secret-shaped, outside-workspace, or future Windows targets.",
      id: "workspace-api",
      route: "POST /v1/workspace/list, POST /v1/workspace/read",
      state: "available",
      title: "Workspace API",
    },
    {
      authority: "Read-only session metadata only; no terminal run is invoked by this surface.",
      evidence: "source_proxy/api/sandbox_terminal.py exposes sessions, detail, and presets GET routes.",
      fallback: "terminal command results remain unavailable unless a real receipt supplies them.",
      id: "sandbox-terminal",
      route: "GET /v1/sandbox/terminal/sessions, GET /v1/sandbox/terminal/presets",
      state: "not-wired",
      title: "Sandbox terminal status",
    },
    {
      authority: "Read-only queue/status routes only; no create, advance, execute-approved, verify, cancel, stream, or worker start.",
      evidence: "source_proxy/api/long_running_tasks.py exposes queue and task status GET routes.",
      fallback: "not-wired in this shell; active task state remains UI-local until a read-only route is wired.",
      id: "long-running-tasks",
      route: "GET /v1/tasks/long-running, GET /v1/tasks/long-running/{task_id}",
      state: "not-wired",
      title: "Long-running task status",
    },
    {
      authority: "Provider/model intent only; no provider call or API-cost action.",
      evidence: `${input.provider.label}; ${input.model.modelLabel}; provider_call_made=false.`,
      fallback: input.model.blockedReason || "local/default intent only.",
      id: "provider-model",
      route: "UI helper: model-provider-status",
      state: providerState,
      title: "Provider/model status",
    },
    {
      authority: "Budget status is display-only only when a real report exists; no budget writes.",
      evidence: "source_proxy/budget/manager.py can read LiteLLM budget status; this shell has no real budget report.",
      fallback: "unavailable; do not invent budget remaining, token usage, or cost.",
      id: "budget-usage",
      route: "source_proxy.budget.manager.collect_budget_status",
      state: "unavailable",
      title: "Budget/usage status",
    },
    {
      authority: "CLI status is receipt-only; no shell command is run by this truth panel.",
      evidence: "Sandbox terminal read routes exist, but command result source is not wired into this shell.",
      fallback: "unavailable unless a real command receipt supplies command/check duration and output.",
      id: "custom-cli",
      route: "terminal receipt source",
      state: "unavailable",
      title: "Custom CLI status",
    },
    {
      authority: "Codex route remains validation/preview only; no live execution.",
      evidence: "source_proxy/api/codex_adapter.py returns codex_route_live_execution_not_enabled.",
      fallback: "config-blocked; would_run_task=false and changed_files=[] until a later approval gate.",
      id: "codex-adapter",
      route: "POST /v1/coding/codex",
      state: "config-blocked",
      title: "Codex adapter status",
    },
    {
      authority: "Truth display only; no hidden polling, provider call, queue, worker, shell, apply, or execute-approved route.",
      evidence: "Rows are helper-built from static route inventory and current UI-local/provider state.",
      fallback: "blocked if any truth row would need an unwired live route without saying not-wired or unavailable.",
      id: "hidden-execution-guard",
      route: "UI helper: backend-truth-surface",
      state: "available",
      title: "No hidden execution guard",
    },
  ];
}

export function backendTruthReceiptLines(rows: BackendTruthRow[]): string[] {
  return [
    "Backend truth receipt",
    "no_fake_backend_data: true",
    "hidden_execution_started: false",
    "provider_call_made: false",
    "queue_worker_started: false",
    "shell_command_started: false",
    ...rows.map(
      (row) =>
        `${row.title}: ${row.state}; route=${row.route}; evidence=${row.evidence}; fallback=${row.fallback}; authority=${row.authority}`,
    ),
  ];
}
