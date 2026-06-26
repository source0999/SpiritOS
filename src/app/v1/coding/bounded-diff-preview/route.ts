import { sourceProxyFetch } from "@/lib/source-proxy-origin";

const dormantRouteHeaders = {
  "x-spiritos-plan4-route-status": "dormant",
  "x-spiritos-plan4-canonical-replacement": "/v1/decisions/prompt-packet -> /v1/verification/diff-preview",
};

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      {
        error: "SPIRIT_CODING_USE_PROXY is not true",
        plan4_route_status: "dormant",
      },
      { headers: dormantRouteHeaders, status: 409 },
    );
  }

  let response;
  try {
    response = await sourceProxyFetch("/v1/coding/bounded-diff-preview", {
      body: await request.text(),
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
      method: "POST",
    });
  } catch (error) {
    return Response.json(
      {
        task_id: "",
        prompt: "",
        target_files: [],
        allowed_files: [],
        changed_files: [],
        unified_diff: "",
        diff_present: false,
        preview_only: true,
        apply_authority: false,
        commit_authority: false,
        push_authority: false,
        provider_call_made: false,
        queue_worker_started: false,
        shell_command_started: false,
        hidden_execution_started: false,
        human_review_required: true,
        unsafe_failures: 0,
        unexpected_files: 0,
        reason_code: "source_proxy_unavailable",
        receipt_class: "route_gap_not_ready",
        plan4_canonical_replacement: "/v1/decisions/prompt-packet -> /v1/verification/diff-preview",
        plan4_route_status: "dormant",
        message:
          "The bounded diff preview route could not reach Source Proxy. No files changed.",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
      },
      { headers: dormantRouteHeaders, status: 200 },
    );
  }

  return new Response(await response.text(), {
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
      ...dormantRouteHeaders,
    },
    status: response.status,
    statusText: response.statusText,
  });
}
