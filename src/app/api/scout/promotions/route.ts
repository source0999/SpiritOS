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

export async function GET() {
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 5_000);

  try {
    const res = await fetch(`${scoutBaseUrl()}/v1/scout/promotions`, {
      cache: "no-store",
      signal: ctrl.signal,
    });

    if (!res.ok) {
      return noStoreJson({
        ok: false,
        status: "unavailable",
        error: "Scout promotions unavailable.",
      });
    }

    return noStoreJson(await res.json());
  } catch {
    return noStoreJson({
      ok: false,
      status: "unavailable",
      error: "Scout promotions unavailable.",
    });
  } finally {
    clearTimeout(timeout);
  }
}
