import { sourceProxyFetch } from "@/lib/source-proxy-origin";

type RouteContext = {
  params: Promise<{
    proposalId: string;
  }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { proposalId } = await context.params;
  const body = await request.text();
  let response;
  try {
    response = await sourceProxyFetch(
      `/v1/cartographer/proposals/${encodeURIComponent(proposalId)}/apply-approved`,
      {
        body,
        headers: {
          "content-type": request.headers.get("content-type") ?? "application/json",
        },
        method: "POST",
      },
    );
  } catch (error) {
    return Response.json(
      {
        status: "unavailable",
        write_actions_enabled: false,
        ok: false,
        proposal_id: proposalId,
        committed: false,
        pushed: false,
        detail: {
          message: "The dashboard could not reach the Source Proxy apply-approved endpoint.",
          reason_code: "source_proxy_unavailable",
          error: error instanceof Error ? error.message : "Unknown connection error.",
        },
      },
      { status: 502 },
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
