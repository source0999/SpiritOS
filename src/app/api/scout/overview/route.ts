export const dynamic = "force-dynamic";

const DEFAULT_SCOUT_API_URL = "http://localhost:8077";

function scoutBaseUrl(): string {
  const configured = process.env.SCOUT_API_URL?.trim();
  const base =
    configured && configured !== "undefined"
      ? configured
      : DEFAULT_SCOUT_API_URL;
  return base.replace(/\/+$/, "");
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
    const [overviewRes, promotionsRes, sourcesRes, sourceCandidatesRes, discoveryJobsRes] =
      await Promise.all([
        fetch(`${scoutBaseUrl()}/v1/scout/overview?limit=${limit}`, {
          cache: "no-store",
          signal: ctrl.signal,
        }),
        fetch(`${scoutBaseUrl()}/v1/scout/promotions`, {
          cache: "no-store",
          signal: ctrl.signal,
        }),
        fetch(`${scoutBaseUrl()}/v1/scout/sources`, {
          cache: "no-store",
          signal: ctrl.signal,
        }),
        fetch(`${scoutBaseUrl()}/v1/scout/source-candidates?limit=200`, {
          cache: "no-store",
          signal: ctrl.signal,
        }),
        fetch(`${scoutBaseUrl()}/v1/scout/discovery-jobs?limit=50`, {
          cache: "no-store",
          signal: ctrl.signal,
        }),
      ]);

    if (!overviewRes.ok) {
      return noStoreJson({
        ok: false,
        status: "unavailable",
        error: "Scout overview unavailable.",
      });
    }

    const overview = await overviewRes.json();
    const promotions = promotionsRes.ok ? await promotionsRes.json() : null;
    const sources = sourcesRes.ok ? await sourcesRes.json() : null;
    const sourceCandidates = sourceCandidatesRes.ok ? await sourceCandidatesRes.json() : null;
    const discoveryJobs = discoveryJobsRes.ok ? await discoveryJobsRes.json() : null;

    return noStoreJson({
      ...overview,
      ...(promotions ? { promotions } : {}),
      ...(sources?.sources ? { sources: sources.sources } : {}),
      ...(sourceCandidates ? { source_candidates: sourceCandidates } : {}),
      ...(discoveryJobs ? { discovery_jobs: discoveryJobs } : {}),
    });
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
