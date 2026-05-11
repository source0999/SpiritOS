import { Agent, fetch } from "undici";

const sourceProxyOrigin =
  process.env.SOURCE_PROXY_ORIGIN ??
  `https://${process.env.SOURCE_PROXY_HOST ?? "127.0.0.1"}:${
    process.env.SOURCE_PROXY_PORT ?? "8787"
  }`;

const httpsAgent = new Agent({
  connect: {
    rejectUnauthorized: false,
  },
});

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const response = await fetch(`${sourceProxyOrigin}/v1/decisions/prompt-packet`, {
    body: await request.text(),
    dispatcher: sourceProxyOrigin.startsWith("https://") ? httpsAgent : undefined,
    headers: {
      "content-type": request.headers.get("content-type") ?? "application/json",
    },
    method: "POST",
  });

  return new Response(await response.text(), {
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
    status: response.status,
    statusText: response.statusText,
  });
}
