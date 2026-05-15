import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export async function POST(
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
  const response = await sourceProxyFetch(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/advance`,
    {
      body: await request.text(),
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
      method: "POST",
    },
  );

  return new Response(await response.text(), {
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
    status: response.status,
    statusText: response.statusText,
  });
}
