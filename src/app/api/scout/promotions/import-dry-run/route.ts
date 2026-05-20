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
    const res = await fetch(`${scoutBaseUrl()}/v1/scout/promotions/import-dry-run`, {
      method: "POST",
      cache: "no-store",
      signal: ctrl.signal,
      headers: { "Content-Type": "application/json" },
      body,
    });
    const payload = await res.json().catch(() => null);

    if (!res.ok) {
      return noStoreJson(
        payload ?? {
          ok: false,
          status: "unavailable",
          error: "Could not dry-run promotion import.",
        },
        { status: res.status },
      );
    }

    return noStoreJson(payload);
  } catch {
    return noStoreJson(
      { ok: false, status: "unavailable", error: "Could not dry-run promotion import." },
      { status: 502 },
    );
  } finally {
    clearTimeout(timeout);
  }
}
