import { sourceProxyStreamFetch } from "@/lib/source-proxy-origin";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ taskId: string }> },
) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const { taskId } = await params;
  const requestUrl = new URL(request.url);
  const path = `/v1/tasks/long-running/${encodeURIComponent(taskId)}/stream${requestUrl.search}`;

  const response = await sourceProxyStreamFetch(path, {
    headers: {
      accept: "text/event-stream",
    },
    method: "GET",
    signal: request.signal,
  });

  return new Response(response.body as unknown as BodyInit, {
    headers: {
      "cache-control": "no-cache, no-transform",
      "content-type": response.headers.get("content-type") ?? "text/event-stream",
      "x-accel-buffering": "no",
    },
    status: response.status,
    statusText: response.statusText,
  });
}
