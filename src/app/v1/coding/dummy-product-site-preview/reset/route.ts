import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export async function POST() {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      {
        error: "SPIRIT_CODING_USE_PROXY is not true",
        reason_code: "coding_proxy_disabled",
      },
      { status: 409 },
    );
  }

  let response;
  try {
    response = await sourceProxyFetch("/v1/coding/dummy-product-site/reset", {
      method: "POST",
    });
  } catch (error) {
    return Response.json(
      {
        error: "Source Proxy dummy product site reset is unavailable",
        reason_code: "source_proxy_unavailable",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
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
