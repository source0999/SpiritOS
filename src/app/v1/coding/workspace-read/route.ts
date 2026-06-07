import { sourceProxyFetch } from "@/lib/source-proxy-origin";

type JsonRecord = Record<string, unknown>;

function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" ? (value as JsonRecord) : {};
}

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json({ error: "SPIRIT_CODING_USE_PROXY is not true" }, { status: 409 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const bodyRecord = asRecord(body);
  const path = typeof bodyRecord.path === "string" ? bodyRecord.path.trim() : "";
  if (!path) {
    return Response.json({ error: "path is required" }, { status: 400 });
  }

  try {
    const response = await sourceProxyFetch("/v1/workspace/read", {
      body: JSON.stringify({ max_bytes: 64000, path }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    if (!response.ok) {
      return new Response(await response.text(), {
        headers: { "content-type": response.headers.get("content-type") ?? "application/json" },
        status: response.status,
      });
    }
    const payload = await response.json();
    return Response.json(payload);
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : "workspace read failed" },
      { status: 502 },
    );
  }
}
