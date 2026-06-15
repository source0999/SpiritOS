import { sourceProxyFetch } from "@/lib/source-proxy-origin";

type RouteContext = {
  params: Promise<{
    runId: string;
  }>;
};

export async function GET(_request: Request, context: RouteContext) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const { runId } = await context.params;
  let response;
  try {
    response = await sourceProxyFetch(
      `/v1/decisions/fip0-receipts/${encodeURIComponent(runId)}/trace`,
      { method: "GET" },
    );
  } catch (error) {
    return Response.json(
      {
        error:
          "The coding page could not reach the Source proxy trace retrieval route.",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
      },
      { status: 502 },
    );
  }

  const responseText = await response.text();
  const contentType = response.headers.get("content-type") ?? "application/json";
  return new Response(responseText, {
    headers: {
      "content-type": contentType,
    },
    status: response.status,
    statusText: response.statusText,
  });
}
