import "server-only";

// ── spirit-search-telemetry — [spirit-search] logs + response headers (Prompt 10C-D) ─
// > No secrets, no full prompts — trimmed query only.

export type SpiritSearchLogRoute =
  | "openai-web-search"
  | "teacher-web-aids"
  | "research-plan"
  | "local-chat"
  | "none";

export type SpiritSearchLogEvent = {
  route: SpiritSearchLogRoute;
  status: "starting" | "used" | "failed" | "skipped" | "disabled";
  mode: "researcher" | "teacher" | "other";
  queryTrimmed: string;
  provider?: string;
  sources?: number;
  elapsedMs?: number;
  reason?: string;
};

const QUERY_LOG_MAX = 160;

/** HTTP response headers must be ByteString (per-byte ≤255). No Unicode ellipsis in trim output. */
export function trimSearchQueryForLog(q: string): string {
  const t = q.replace(/\s+/g, " ").trim();
  if (t.length <= QUERY_LOG_MAX) return t;
  return `${t.slice(0, QUERY_LOG_MAX)}...`;
}

/** WHATWG ByteString / ISO-8859-1 header values: code points > U+00FF are invalid (8230 = … blows up). */
export function sanitizeForHttpByteStringHeader(value: string): string {
  let out = "";
  for (const ch of value) {
    const cp = ch.codePointAt(0)!;
    if (cp === 0x2026) {
      out += "...";
      continue;
    }
    if (cp <= 0xff) {
      if (cp === 9 || cp === 10 || cp === 13) out += " ";
      else if (cp < 32) out += " ";
      else out += String.fromCodePoint(cp);
    } else {
      out += "?";
    }
  }
  return out;
}

export function logSpiritSearchEvent(ev: SpiritSearchLogEvent): void {
  const parts = [
    `[spirit-search]`,
    `route=${ev.route}`,
    `status=${ev.status}`,
    `mode=${ev.mode}`,
    `query="${ev.queryTrimmed.replace(/"/g, '\\"')}"`,
  ];
  if (ev.provider) parts.push(`provider=${ev.provider}`);
  if (typeof ev.sources === "number") parts.push(`sources=${ev.sources}`);
  if (typeof ev.elapsedMs === "number") parts.push(`elapsedMs=${ev.elapsedMs}`);
  if (ev.reason) parts.push(`reason="${ev.reason.replace(/"/g, '\\"')}"`);
  console.log(parts.join(" "));
}

export function normalizeSearchStatus(
  raw: string | null | undefined,
): "used" | "skipped" | "failed" | "disabled" | "none" {
  const s = (raw ?? "none").trim().toLowerCase();
  if (s === "used") return "used";
  if (s === "failed") return "failed";
  if (s === "disabled") return "disabled";
  if (s === "skipped") return "skipped";
  return "none";
}

export type SpiritSearchHeaderInput = {
  routeLane: string;
  routeConfidence: string;
  webSearch: string;
  searchStatus: string;
  provider: string | null;
  sourceCount: number;
  queryTrimmed: string;
  elapsedMs: number | null;
  searchKind: "researcher" | "teacher" | "none";
  skipReason?: string | null;
  webSourcesJson: string | null;
};

export function buildSpiritSearchHeaders(input: SpiritSearchHeaderInput): Record<string, string> {
  const h: Record<string, string> = {
    "x-spirit-route-lane": input.routeLane,
    "x-spirit-route-confidence": input.routeConfidence,
    "x-spirit-web-search": input.webSearch,
    "x-spirit-search-status": input.searchStatus,
    "x-spirit-source-count": String(input.sourceCount),
    "x-spirit-search-query": input.queryTrimmed.slice(0, 200),
    "x-spirit-search-kind": input.searchKind,
  };
  if (input.provider) h["x-spirit-search-provider"] = input.provider;
  if (input.elapsedMs != null && Number.isFinite(input.elapsedMs)) {
    h["x-spirit-search-elapsed-ms"] = String(Math.round(input.elapsedMs));
  }
  if (input.skipReason?.trim()) {
    h["x-spirit-search-skip-reason"] = input.skipReason.trim().slice(0, 120);
  }
  if (input.webSourcesJson) h["x-spirit-web-sources"] = input.webSourcesJson;

  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(h)) {
    const s = sanitizeForHttpByteStringHeader(v);
    out[k] = s;
  }
  return out;
}
