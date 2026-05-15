import { mergeRepoFirstResearchSources } from "@/app/v1/decisions/_repo-research";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const bodyText = await request.text();
  let response;
  try {
    response = await sourceProxyFetch("/v1/decisions/prompt-packet", {
      body: bodyText,
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
      method: "POST",
    });
  } catch (error) {
    return Response.json(
      {
        error:
          "The coding page could not reach the Source proxy. Check that the proxy is running and that SOURCE_PROXY_ORIGIN, SOURCE_PROXY_HOST, and SOURCE_PROXY_PORT point to it.",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
      },
      { status: 502 },
    );
  }

  const responseText = await response.text();
  const contentType = response.headers.get("content-type") ?? "application/json";
  const body =
    contentType.includes("application/json") && response.ok
      ? mergeRepoFirstResearchSources(bodyText, responseText)
      : responseText;

  return new Response(body, {
    headers: {
      "content-type": contentType,
    },
    status: response.status,
    statusText: response.statusText,
  });
}
