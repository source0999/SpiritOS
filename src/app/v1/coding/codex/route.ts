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
        push_authority: false,
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
