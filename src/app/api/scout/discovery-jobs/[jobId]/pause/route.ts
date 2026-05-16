export const dynamic = "force-dynamic";

const DEFAULT_SCOUT_API_URL = "http://localhost:8077";

function scoutBaseUrl(): string {
  return (process.env.SCOUT_API_URL ?? DEFAULT_SCOUT_API_URL).replace(/\/+$/, "");
}

function noStoreJson(body: unknown, init?: ResponseInit): Response {
  return Response.json(body, {
    ...init,
    headers: { "Cache-Control": "no-store", ...init?.headers },
  });
}

type RouteContext = {
  params: Promise<{ jobId: string }>;
};

export async function POST(_request: Request, context: RouteContext) {
  const { jobId } = await context.params;
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 5_000);

  try {
    const res = await fetch(
      `${scoutBaseUrl()}/v1/scout/discovery-jobs/${encodeURIComponent(jobId)}/pause`,
      { method: "POST", cache: "no-store", signal: ctrl.signal },
    );
    if (!res.ok) {
      return noStoreJson(
        { ok: false, status: "unavailable", error: "Could not pause discovery job." },
        { status: res.status },
      );
    }
    return noStoreJson(await res.json());
  } catch {
    return noStoreJson(
      { ok: false, status: "unavailable", error: "Could not pause discovery job." },
      { status: 502 },
    );
  } finally {
    clearTimeout(timeout);
  }
}
