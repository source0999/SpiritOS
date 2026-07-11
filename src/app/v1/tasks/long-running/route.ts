import { sourceProxyFastJsonFetch, sourceProxyFetch } from "@/lib/source-proxy-origin";

const TASK_CREATE_CANDIDATE_TIMEOUT_MS = 5_000;

function taskCreationTimeoutEnvelope(input: {
  elapsedMs: number;
  error: unknown;
  lastCheckpoint: string;
}) {
  const machineReason =
    input.error instanceof Error
      ? `${input.error.name}: ${input.error.message || "source_proxy_fetch_failed"}`
      : String(input.error ?? "source_proxy_fetch_failed");
  return {
    stage_id: "next.long_running_task_create_proxy",
    subsystem: "nextjs_source_proxy_bridge",
    task_id: "missing: task_create_proxy_failed_before_task_id",
    selected_prompt_task_id: "missing: task_create_proxy_failed_before_task_id",
    status: "blocked",
    truth_status: "BLOCKED_SAFE",
    safe_block: true,
    error: "Source Proxy task creation did not return a durable task id.",
    error_code: "selected_prompt_task_create_timeout",
    reason_code: "selected_prompt_task_create_timeout",
    human_message:
      "The selected prompt stopped before Source Proxy returned a long-running task id.",
    machine_reason: machineReason,
    apply_block_layer: "task_create_before_model_call",
    task_creation_status: "timeout_before_task_id",
    task_creation_elapsed_ms: input.elapsedMs,
    task_creation_timeout_stage: "source_proxy_candidate_fetch",
    task_creation_last_checkpoint: input.lastCheckpoint,
    task_creation_blocking_subsystem: "source_proxy_long_running_task_route",
    recommended_next_action:
      "Verify the Source Proxy origin/protocol and rerun only the selected prompt after /v1/tasks/long-running returns a task id.",
    approval_binding: {
      approval_binding_status: "not_run: task_create_failed_before_model_call",
      apply_block_layer: "task_create_before_model_call",
      safe_block: true,
    },
    anti_cheat: {
      anti_cheat_status: "not_run",
      anti_cheat_reasons: ["task_create_failed_before_model_call"],
      grader_result_state: "not_applicable: task_create_failed_before_task_id",
    },
    acceptance_gate: {
      binary_verdict: "NO-GO",
      phase_verifier_status: "skipped_with_reason",
      fail_closed_lane_status: "skipped_with_reason",
      causal_crosscheck_status: "skipped_with_reason",
      reason: "selected_prompt_task_create_timeout",
    },
    final_truth_summary: {
      commit_safe: false,
      proof_level: "operator_ui_task_create_failure",
      raw_backend_status: "/v1/tasks/long-running:timeout",
      run_status: "blocked",
      truth_status: "BLOCKED_SAFE",
      why_not_go: "task creation failed before model call and before approval binding",
    },
    diagnostic_envelope: {
      stage_id: "next.long_running_task_create_proxy",
      subsystem: "nextjs_source_proxy_bridge",
      truth_status: "BLOCKED_SAFE",
      safe_block: true,
      reason_code: "selected_prompt_task_create_timeout",
      machine_reason: machineReason,
      apply_block_layer: "task_create_before_model_call",
      task_creation_status: "timeout_before_task_id",
      task_creation_elapsed_ms: input.elapsedMs,
      task_creation_timeout_stage: "source_proxy_candidate_fetch",
      task_creation_last_checkpoint: input.lastCheckpoint,
      task_creation_blocking_subsystem: "source_proxy_long_running_task_route",
    },
  };
}

export async function GET(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const sourceUrl = new URL(request.url);
  const query = sourceUrl.search;
  const response = await sourceProxyFetch(`/v1/tasks/long-running${query}`, {
    method: "GET",
  });

  return new Response(await response.text(), {
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
    status: response.status,
    statusText: response.statusText,
  });
}

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const startedAt = Date.now();
  let lastCheckpoint = "request_received";
  let body = "";
  try {
    body = await request.text();
    lastCheckpoint = "request_body_read";
    const response = await sourceProxyFastJsonFetch(
      "/v1/tasks/long-running",
      {
        body,
        headers: {
          "content-type": request.headers.get("content-type") ?? "application/json",
        },
        method: "POST",
      },
      { perCandidateTimeoutMs: TASK_CREATE_CANDIDATE_TIMEOUT_MS },
    );
    lastCheckpoint = "source_proxy_response_headers_received";

    return new Response(await response.text(), {
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
      status: response.status,
      statusText: response.statusText,
    });
  } catch (error) {
    const elapsedMs = Date.now() - startedAt;
    return Response.json(
      taskCreationTimeoutEnvelope({ elapsedMs, error, lastCheckpoint }),
      { status: 504 },
    );
  }
}
