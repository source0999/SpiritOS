import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
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
        message:
          "The bounded diff preview route could not reach Source Proxy. No files changed.",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
      },
      { status: 200 },
    );
  }

  return new Response(await response.text(), {
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
    status: response.status,
    statusText: response.statusText,
  });
}
