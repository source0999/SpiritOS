"use client";

import { useCallback, useEffect, useState } from "react";

import type { ScoutOverview, ScoutOverviewRouteError } from "@/lib/scout-overview";

export type ScoutOverviewFetchState = "loading" | "loaded" | "error";

export type UseScoutOverviewResult = {
  data: ScoutOverview | null;
  state: ScoutOverviewFetchState;
  error: string | null;
  refresh: () => Promise<void>;
};

function isScoutOverviewRouteError(
  value: ScoutOverview | ScoutOverviewRouteError,
): value is ScoutOverviewRouteError {
  return "ok" in value && value.ok === false;
}

export function useScoutOverview(pollMs = 30_000): UseScoutOverviewResult {
  const [data, setData] = useState<ScoutOverview | null>(null);
  const [state, setState] = useState<ScoutOverviewFetchState>("loading");
  const [error, setError] = useState<string | null>(null);

  const fetchScoutOverview = useCallback(async (signal?: AbortSignal): Promise<ScoutOverview> => {
    const overviewRes = await fetch("/api/scout/overview", {
      cache: "no-store",
      signal,
    });
    const overviewJson = (await overviewRes.json()) as ScoutOverview | ScoutOverviewRouteError;

    if (!overviewRes.ok || isScoutOverviewRouteError(overviewJson)) {
      throw new Error(
        isScoutOverviewRouteError(overviewJson)
          ? overviewJson.error
          : "Scout overview unavailable.",
      );
    }

    const promotionsRes = await fetch("/api/scout/promotions", {
      cache: "no-store",
      signal,
    });
    if (!promotionsRes.ok) return overviewJson;
    const promotionsJson = await promotionsRes.json();
    const withPromotions =
      promotionsJson && typeof promotionsJson === "object" && "ok" in promotionsJson
        ? overviewJson
        : { ...overviewJson, promotions: promotionsJson };

    const sourcesRes = await fetch("/api/scout/sources", {
      cache: "no-store",
      signal,
    });
    let withSources = withPromotions;
    if (sourcesRes.ok) {
      const sourcesJson = await sourcesRes.json();
      if (!(sourcesJson && typeof sourcesJson === "object" && "ok" in sourcesJson)) {
        withSources = {
          ...withPromotions,
          sources:
            sourcesJson &&
            typeof sourcesJson === "object" &&
            "sources" in sourcesJson &&
            Array.isArray(sourcesJson.sources)
              ? sourcesJson.sources
              : withPromotions.sources,
        };
      }
    }

    const sourceCandidatesRes = await fetch("/api/scout/source-candidates?limit=200", {
      cache: "no-store",
      signal,
    });
    if (!sourceCandidatesRes.ok) return withSources;
    const sourceCandidatesJson = await sourceCandidatesRes.json();
    if (
      sourceCandidatesJson &&
      typeof sourceCandidatesJson === "object" &&
      "ok" in sourceCandidatesJson
    ) {
      return withSources;
    }
    const withSourceCandidates = { ...withSources, source_candidates: sourceCandidatesJson };

    const discoveryJobsRes = await fetch("/api/scout/discovery-jobs?limit=50", {
      cache: "no-store",
      signal,
    });
    if (!discoveryJobsRes.ok) return withSourceCandidates;
    const discoveryJobsJson = await discoveryJobsRes.json();
    if (
      discoveryJobsJson &&
      typeof discoveryJobsJson === "object" &&
      "ok" in discoveryJobsJson
    ) {
      return withSourceCandidates;
    }
    return { ...withSourceCandidates, discovery_jobs: discoveryJobsJson };
  }, []);

  const refresh = useCallback(async () => {
    try {
      const json = await fetchScoutOverview();
      setData(json);
      setState("loaded");
      setError(null);
    } catch (e) {
      setData(null);
      setState("error");
      setError(e instanceof Error ? e.message : "Scout overview unavailable.");
    }
  }, [fetchScoutOverview]);

  useEffect(() => {
    let active = true;
    let ctrl = new AbortController();

    async function poll() {
      try {
        const json = await fetchScoutOverview(ctrl.signal);
        if (!active) return;

        setData(json);
        setState("loaded");
        setError(null);
      } catch (e) {
        if (!active) return;
        if (e instanceof DOMException && e.name === "AbortError") return;
        if (e instanceof Error && e.name === "AbortError") return;
        setData(null);
        setState("error");
        setError(e instanceof Error ? e.message : "Scout overview unavailable.");
      }
    }

    void poll();
    const pollTimer = setInterval(() => {
      ctrl.abort();
      ctrl = new AbortController();
      void poll();
    }, pollMs);

    return () => {
      active = false;
      clearInterval(pollTimer);
      ctrl.abort();
    };
  }, [fetchScoutOverview, pollMs]);

  return { data, state, error, refresh };
}
