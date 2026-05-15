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

type RouteContext = {
  params: Promise<{ candidateId: string }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { candidateId } = await context.params;
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 5_000);

  try {
    const body = await request.text();
    const res = await fetch(
      `${scoutBaseUrl()}/v1/scout/source-candidates/${encodeURIComponent(candidateId)}/approve`,
      {
        method: "POST",
        cache: "no-store",
        signal: ctrl.signal,
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body || undefined,
      },
    );

    if (!res.ok) {
      return noStoreJson(
        { ok: false, status: "unavailable", error: "Could not approve source candidate." },
        { status: res.status },
      );
    }

    return noStoreJson(await res.json());
  } catch {
    return noStoreJson(
      { ok: false, status: "unavailable", error: "Could not approve source candidate." },
      { status: 502 },
    );
  } finally {
    clearTimeout(timeout);
  }
}
