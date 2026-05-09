// ── spirit-search-response-headers - parse /api/spirit proof headers (client-safe) ─
// > Server telemetry lives in spirit-search-telemetry (server-only); keep this import-free of that.

export type SpiritSearchStatusNormalized = "used" | "skipped" | "failed" | "disabled" | "none";

export type ParsedSpiritSearchHeaders = {
  routeLane: string | null;
  routeConfidence: string | null;
  webSearch: string | null;
  searchStatus: SpiritSearchStatusNormalized;
  searchProvider: string | null;
  sourceCount: number | null;
  searchQuery: string | null;
  searchElapsedMs: number | null;
  searchKind: "researcher" | "teacher" | "none";
  skipReason: string | null;
  webSourcesJson: string | null;
};

export function normalizeClientSearchStatus(raw: string | null | undefined): SpiritSearchStatusNormalized {
  const s = (raw ?? "none").trim().toLowerCase();
  if (s === "used") return "used";
  if (s === "failed") return "failed";
  if (s === "disabled") return "disabled";
  if (s === "skipped") return "skipped";
  return "none";
}

export function parseSpiritSearchHeaders(res: Response): ParsedSpiritSearchHeaders {
  const routeLane = res.headers.get("x-spirit-route-lane");
  const routeConfidence = res.headers.get("x-spirit-route-confidence");
  const webSearch = res.headers.get("x-spirit-web-search");
  const searchStatusRaw =
    res.headers.get("x-spirit-search-status") ?? res.headers.get("x-spirit-web-search");
  const searchProvider = res.headers.get("x-spirit-search-provider");
  const sc = res.headers.get("x-spirit-source-count");
  const sourceCount = sc != null && sc.trim() !== "" ? Number.parseInt(sc, 10) : null;
  const searchQuery = res.headers.get("x-spirit-search-query");
  const el = res.headers.get("x-spirit-search-elapsed-ms");
  const searchElapsedMs =
    el != null && el.trim() !== "" && Number.isFinite(Number(el)) ? Math.round(Number(el)) : null;
  const sk = res.headers.get("x-spirit-search-kind");
  const searchKind: "researcher" | "teacher" | "none" =
    sk === "researcher" || sk === "teacher" ? sk : "none";
  const skipReason = res.headers.get("x-spirit-search-skip-reason");
  const webSourcesJson = res.headers.get("x-spirit-web-sources");

  return {
    routeLane,
    routeConfidence,
    webSearch,
    searchStatus: normalizeClientSearchStatus(searchStatusRaw),
    searchProvider: searchProvider?.trim() || null,
    sourceCount: sourceCount != null && Number.isFinite(sourceCount) ? sourceCount : null,
    searchQuery: searchQuery?.trim() || null,
    searchElapsedMs,
    searchKind,
    skipReason: skipReason?.trim() || null,
    webSourcesJson,
  };
}
