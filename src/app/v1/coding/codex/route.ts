import { sourceProxyFetch } from "@/lib/source-proxy-origin";

const dormantRouteHeaders = {
  "x-spiritos-plan4-route-status": "dormant",
  "x-spiritos-plan4-canonical-replacement": "/v1/decisions/prompt-packet -> /v1/verification/diff-preview -> /v1/actions/execute-approved",
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
    response = await sourceProxyFetch("/v1/coding/codex", {
      body: await request.text(),
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
      method: "POST",
    });
  } catch (error) {
    return Response.json(
      {
        service: "source-proxy",
        route: "codex_adapter",
        status: "config_blocked",
        execution_state: "config_blocked",
        reason_code: "source_proxy_unavailable",
        message:
          "The Codex route could not reach Source Proxy. No Codex task was executed.",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
        would_run_task: false,
        changed_files: [],
        approval_authority: false,
        apply_authority: false,
        commit_authority: false,
        plan4_canonical_replacement: "/v1/decisions/prompt-packet -> /v1/verification/diff-preview -> /v1/actions/execute-approved",
        plan4_route_status: "dormant",
        push_authority: false,
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
