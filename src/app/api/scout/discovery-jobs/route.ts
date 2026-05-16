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

function discoveryJobsQuery(request: Request): string {
  const incoming = new URL(request.url).searchParams;
  const outgoing = new URLSearchParams();
  const status = incoming.get("status");
  const rawLimit = incoming.get("limit");
  const limit = Number.parseInt(rawLimit ?? "20", 10);

  if (status) outgoing.set("status", status);
  outgoing.set("limit", String(Number.isFinite(limit) ? Math.min(200, Math.max(1, limit)) : 20));
  return outgoing.toString();
}

export async function GET(request: Request) {
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 5_000);

  try {
    const query = discoveryJobsQuery(request);
    const res = await fetch(`${scoutBaseUrl()}/v1/scout/discovery-jobs?${query}`, {
      cache: "no-store",
      signal: ctrl.signal,
    });

    if (!res.ok) {
      return noStoreJson(
        { ok: false, status: "unavailable", error: "Scout discovery jobs unavailable." },
        { status: res.status },
      );
    }

    return noStoreJson(await res.json());
  } catch {
    return noStoreJson(
      { ok: false, status: "unavailable", error: "Scout discovery jobs unavailable." },
      { status: 502 },
    );
  } finally {
    clearTimeout(timeout);
  }
}

export async function POST(request: Request) {
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 5_000);

  try {
    const body = await request.text();
    const res = await fetch(`${scoutBaseUrl()}/v1/scout/discovery-jobs`, {
      method: "POST",
      cache: "no-store",
      signal: ctrl.signal,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body || undefined,
    });

    if (!res.ok) {
      return noStoreJson(
        { ok: false, status: "unavailable", error: "Could not create discovery job." },
        { status: res.status },
      );
    }

    return noStoreJson(await res.json(), { status: 201 });
  } catch {
    return noStoreJson(
      { ok: false, status: "unavailable", error: "Could not create discovery job." },
      { status: 502 },
    );
  } finally {
    clearTimeout(timeout);
  }
}
