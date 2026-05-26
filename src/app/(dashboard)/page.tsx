// ── Dashboard route (/) - widget command center (chat lives at /chat) ─────────────
import SpiritDashboardHome from "@/components/dashboard/SpiritDashboardHome";
import type { ScoutOverview, ScoutOverviewRouteError } from "@/lib/scout-overview";

export const dynamic = "force-dynamic";

function scoutBaseUrl(): string {
  const configured = process.env.SCOUT_API_URL?.trim();
  const base =
    configured && configured !== "undefined"
      ? configured
      : "http://localhost:8077";
  return base.replace(/\/+$/, "");
}

function isScoutOverviewRouteError(
  value: ScoutOverview | ScoutOverviewRouteError,
): value is ScoutOverviewRouteError {
  return "ok" in value && value.ok === false;
}

async function collectInitialScoutOverview(): Promise<ScoutOverview | null> {
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 5_000);

  try {
    const [overviewRes, sourcesRes, sourceCandidatesRes, discoveryJobsRes] = await Promise.all([
      fetch(`${scoutBaseUrl()}/v1/scout/overview?limit=10`, {
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
    if (!overviewRes.ok) return null;

    const overview = (await overviewRes.json()) as ScoutOverview | ScoutOverviewRouteError;
    if (isScoutOverviewRouteError(overview)) return null;

    const sources = sourcesRes.ok ? await sourcesRes.json() : null;
    const sourceCandidates = sourceCandidatesRes.ok ? await sourceCandidatesRes.json() : null;
    const discoveryJobs = discoveryJobsRes.ok ? await discoveryJobsRes.json() : null;

    return {
      ...overview,
      ...(sources &&
      typeof sources === "object" &&
      "sources" in sources &&
      Array.isArray(sources.sources)
        ? { sources: sources.sources }
        : {}),
      ...(sourceCandidates ? { source_candidates: sourceCandidates } : {}),
      ...(discoveryJobs ? { discovery_jobs: discoveryJobs } : {}),
    };
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

export default async function DashboardPage() {
  const initialScoutOverview = await collectInitialScoutOverview();

  return (
    <SpiritDashboardHome
      initialTelemetry={null}
      initialScoutOverview={initialScoutOverview}
    />
  );
}
