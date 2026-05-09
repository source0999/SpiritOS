import { collectLocalNodeTelemetry } from "@/lib/server/telemetry/collect-local-node";

export const dynamic = "force-dynamic";

function checkToken(req: Request): boolean {
  const token = process.env.SPIRIT_TELEMETRY_TOKEN?.trim();
  if (!token) return true;
  const auth = req.headers.get("authorization");
  return auth === `Bearer ${token}`;
}

export async function GET(req: Request) {
  if (!checkToken(req)) {
    return Response.json(
      { ok: false, error: "Unauthorized" },
      { status: 401, headers: { "Cache-Control": "no-store" } },
    );
  }

  try {
    const node = await collectLocalNodeTelemetry();
    return Response.json(node, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return Response.json(
      {
        ok: false,
        id: process.env.SPIRIT_CLUSTER_LOCAL_ID?.trim() || "unknown",
        status: "offline",
        error: message,
        collectedAt: new Date().toISOString(),
      },
      { status: 500, headers: { "Cache-Control": "no-store" } },
    );
  }
}
