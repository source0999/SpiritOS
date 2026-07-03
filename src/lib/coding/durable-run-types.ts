export type DurableCodingRunStatus =
  | "pending"
  | "running"
  | "needs_approval"
  | "completed"
  | "failed"
  | "timed_out"
  | "cancelled"
  | "cleared"
  | "reverted";

export type DurableCodingRunStepInstrumentation = {
  checks_completed_at?: string | null;
  checks_started_at?: string | null;
  diff_preview_completed_at?: string | null;
  diff_preview_requested_at?: string | null;
  disk_probe_completed_at?: string | null;
  disk_probe_started_at?: string | null;
  execute_approved_body_read_completed_at?: string | null;
  execute_approved_body_read_failed_at?: string | null;
  execute_approved_body_read_started_at?: string | null;
  execute_approved_completed_at?: string | null;
  execute_approved_content_type?: string | null;
  execute_approved_http_status?: string | null;
  execute_approved_requested_at?: string | null;
  last_progress_reason_code?: string | null;
  model_response_classification?: string | null;
  model_response_parse_decision?: string | null;
  model_response_raw_length?: number | null;
  model_response_safe_excerpt?: string | null;
  no_diff_reason_code?: string | null;
  prompt_packet_completed_at?: string | null;
  prompt_packet_requested_at?: string | null;
  result_finalized_at?: string | null;
  reverse_receipt_created_at?: string | null;
};

export type DurableCodingRunProvenance = {
  generation_source: string;
  diff_source: string;
  model_output_classification: string;
  raw_response_length: number;
  raw_response_excerpt_safe: string;
  scaffold_used: boolean;
  scaffold_kind: string;
  fallback_used: boolean;
  fallback_kind: string;
  parser_repair_used: boolean;
  bounded_create_used: boolean;
  known_scaffold_used: boolean;
  generic_scaffold_used: boolean;
  model_raw_diff_used: boolean;
  generated_diff_by_backend: boolean;
  trial_result_trust_status: string;
  raw_model_response_sha256?: string | null;
  model_file_bundle_sha256?: string | null;
  backend_converted_diff_sha256?: string | null;
  approved_diff_sha256?: string | null;
  applied_diff_sha256?: string | null;
  post_apply_rediff_sha256?: string | null;
  provenance_hash_normalization?: string | null;
  apply_mode?: string | null;
  stale_patch_recovered?: boolean | null;
};

export type DurableCodingRunOwnerKind =
  | "primary_runner"
  | "observer"
  | "refresh_recovery"
  | "stale_recovery"
  | "clear_action"
  | "stop_action"
  | "unknown";

export type DurableCodingRunWriteSource =
  | "create"
  | "run_patch"
  | "row_upsert"
  | "clear"
  | "stop"
  | "stale_guard"
  | "refresh_resume"
  | "unknown";

export type DurableCodingRunWriteDebugEntry = {
  at: string;
  accepted: boolean;
  decision: string;
  owner_kind: DurableCodingRunOwnerKind;
  source: DurableCodingRunWriteSource;
  prompt_id?: string | null;
  runner_instance_id?: string | null;
  client_instance_id?: string | null;
  lease_epoch?: number | null;
  completed_count_before?: number | null;
  completed_count_after?: number | null;
  status_before?: DurableCodingRunStatus | null;
  status_after?: DurableCodingRunStatus | null;
  invariant_violations?: string[];
};

export type DurableCodingRunRow = {
  prompt_id: string;
  run_id?: string;
  prompt_text: string;
  prompt_excerpt: string;
  status: DurableCodingRunStatus;
  started_at: string | null;
  updated_at: string;
  provider_call_made: boolean;
  model_called_for_generation: string;
  endpoint_statuses: string[];
  reason_code: string;
  generated_diff_present: boolean;
  preview_changed_files: string[];
  applied_changed_files: string[];
  disk_changed_files: string[];
  checks_run: string[];
  checks_result: string;
  reversal_available: boolean;
  reversal_status: string;
  reverse_diff?: string;
  result_label: string;
  error_summary: string;
  provenance?: DurableCodingRunProvenance;
  step_instrumentation?: DurableCodingRunStepInstrumentation;
  owner_kind?: DurableCodingRunOwnerKind | null;
  write_source?: DurableCodingRunWriteSource | null;
  runner_instance_id?: string | null;
  client_instance_id?: string | null;
  lease_epoch?: number | null;
};

export type DurableCodingRun = {
  run_id: string;
  suite_id: string;
  created_at: string;
  updated_at: string;
  suite_started_at?: string | null;
  current_prompt_started_at?: string | null;
  current_step_started_at?: string | null;
  started_by_surface: "coding";
  lane: "coder";
  benchmark_name: string;
  requested_count: number;
  completed_count: number;
  status: DurableCodingRunStatus;
  current_prompt_id: string | null;
  rows: DurableCodingRunRow[];
  provider: string;
  model: string;
  provider_call_made: boolean;
  model_called_for_generation: string;
  endpoint_statuses: string[];
  generated_diff_present: boolean;
  preview_changed_files: string[];
  applied_changed_files: string[];
  disk_changed_files: string[];
  checks_run: string[];
  checks_result: string;
  reversal_available: boolean;
  reversal_status: string;
  final_summary: string;
  last_error: string | null;
  reason_code: string | null;
  frontend_url: string;
  proxy_url: string;
  owner_kind?: DurableCodingRunOwnerKind | null;
  write_source?: DurableCodingRunWriteSource | null;
  runner_instance_id?: string | null;
  client_instance_id?: string | null;
  lease_epoch?: number | null;
  last_write_decision?: string | null;
  write_debug?: DurableCodingRunWriteDebugEntry[];
  invariant_violations?: string[];
};

export type DurableCodingRunCreateInput = Partial<DurableCodingRun> & {
  benchmark_name?: string;
  requested_count?: number;
};

export type DurableCodingRunPatchInput = Partial<Omit<DurableCodingRun, "run_id" | "suite_id" | "created_at">>;
