export const MAC_WORKER_NODE_ID = "spirit-mac-mini";
export const MAC_WORKER_JOB_ENVELOPE_VERSION = "source-proxy-mac-worker-job-v1";
export const MAC_WORKER_RESULT_ENVELOPE_VERSION = "source-proxy-mac-worker-result-v1";

export const macWorkerJobTypes = [
  "repo_context_search",
  "source_proxy_context_discovery",
  "trial_context_assist",
  "scout_research_packet",
  "browser_design_check",
  "mac_isolated_write_proof",
  "run_safe_check",
  "system_status",
] as const;

export type MacWorkerJobType = (typeof macWorkerJobTypes)[number];

export type MacWorkerJobInput = {
  prompt?: string;
  query?: string;
  repo_path?: string;
  cwd?: string;
  files?: string[];
  check_command?: string;
  url?: string;
  viewport?: string;
  check?: string;
  max_results?: number;
  mode?: string;
  provider?: string;
  provider_url?: string;
  contents?: string;
  proof_dir?: string;
};

export type MacWorkerJob = {
  job_id: string;
  job_type: MacWorkerJobType;
  input: MacWorkerJobInput;
  node_id: string;
  created_at: string;
  job_envelope_version?: string;
  trace_id?: string;
  invocation_event_id?: string;
  consumer_event_id?: string;
  consumer_subsystem?: string;
  task_id?: string;
};

export type MacWorkerJobResult = {
  job_id: string;
  job_type: MacWorkerJobType;
  input?: MacWorkerJobInput;
  node_id: string;
  started_at: string;
  completed_at: string;
  success: boolean;
  result: Record<string, unknown> | null;
  stdout: string;
  stderr: string;
  error: string | null;
  duration_ms: number;
  artifacts: string[];
  candidate_files: string[];
  recommended_checks: string[];
  result_envelope_version?: string;
  trace_id?: string;
  invocation_event_id?: string;
  consumer_event_id?: string;
  consumer_subsystem?: string;
  task_id?: string;
};

export type MacWorkerCapabilityStatus =
  | "AVAILABLE"
  | "UNAVAILABLE"
  | "BLOCKED_AUTH"
  | "BLOCKED_HUMAN"
  | "UNKNOWN";

export type MacWorkerCapabilityDescriptor = {
  worker: "mac";
  status: MacWorkerCapabilityStatus;
  capabilities: MacWorkerJobType[];
  write_capable: true;
  requires_human_first_write: true;
  allowed_workspace: string;
  job_envelope_version: string;
  result_envelope_version: string;
  last_health_check: string | null;
};

export type MacWorkerTraceFields = {
  trace_id: string;
  invocation_event_id: string;
  consumer_event_id?: string;
  consumer_subsystem: string;
  task_id: string;
};

export type MacWorkerNodeStatus = {
  node_id: string;
  label: string;
  hostname: string;
  ssh_alias: string;
  role: "macos-worker";
  online: boolean;
  worker_available: boolean;
  repo_present: boolean | null;
  supported_job_types: MacWorkerJobType[];
  last_job_type: MacWorkerJobType | null;
  last_used_at: string | null;
  last_success: boolean | null;
  result_summary: string;
  error: string | null;
  last_reason_code: string | null;
  blocked_command: string | null;
  safe_checks_blocked: boolean;
  last_result?: MacWorkerJobResult;
};

export type MacWorkerRunSummary = {
  mac_used: boolean;
  mac_node_status: "online" | "offline" | "unavailable";
  mac_job_type: MacWorkerJobType | null;
  mac_candidate_files: string[];
  mac_result_summary: string;
  mac_error: string | null;
  mac_duration_ms: number | null;
};
