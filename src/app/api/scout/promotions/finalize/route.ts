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

export async function POST(request: Request) {
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 5_000);

  try {
    const body = await request.text();
    const res = await fetch(`${scoutBaseUrl()}/v1/scout/promotions/finalize`, {
      method: "POST",
      cache: "no-store",
      signal: ctrl.signal,
      headers: { "Content-Type": "application/json" },
      body,
    });

    if (!res.ok) {
      return noStoreJson(
        { ok: false, status: "unavailable", error: "Could not finalize promotion." },
        { status: res.status },
      );
    }

    return noStoreJson(await res.json());
  } catch {
    return noStoreJson(
      { ok: false, status: "unavailable", error: "Could not finalize promotion." },
      { status: 502 },
    );
  } finally {
    clearTimeout(timeout);
  }
}
