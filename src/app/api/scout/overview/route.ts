export const dynamic = "force-dynamic";

const DEFAULT_SCOUT_API_URL = "http://localhost:8077";

function scoutBaseUrl(): string {
  return (process.env.SCOUT_API_URL ?? DEFAULT_SCOUT_API_URL).replace(/\/+$/, "");
}

function noStoreJson(body: unknown, init?: ResponseInit): Response {
  return Response.json(body, {
    ...init,
    headers: {
      "Cache-Control": "no-store",
      ...init?.headers,
    },
  });
}

function limitFromRequest(request: Request): number {
  const raw = new URL(request.url).searchParams.get("limit");
  const parsed = Number.parseInt(raw ?? "10", 10);
  if (!Number.isFinite(parsed)) return 10;
  return Math.min(50, Math.max(1, parsed));
}

export async function GET(request: Request) {
  const limit = limitFromRequest(request);
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 5_000);

  try {
    const res = await fetch(`${scoutBaseUrl()}/v1/scout/overview?limit=${limit}`, {
      cache: "no-store",
      signal: ctrl.signal,
    });

    if (!res.ok) {
      return noStoreJson({
        ok: false,
        status: "unavailable",
        error: "Scout overview unavailable.",
      });
    }

    return noStoreJson(await res.json());
  } catch {
    return noStoreJson({
      ok: false,
      status: "unavailable",
      error: "Scout overview unavailable.",
    });
  } finally {
    clearTimeout(timeout);
  }
}
