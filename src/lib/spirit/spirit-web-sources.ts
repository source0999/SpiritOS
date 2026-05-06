// ── spirit-web-sources - parse `x-spirit-web-sources` from /api/spirit (client-safe) ─
// > No fake citations: only render what the server actually returned.

import { isVerifiedHttpUrl } from "@/lib/verified-http-url";

export type SpiritWebSourcesHeaderPayload = {
  provider: string;
  count: number;
  sources: Array<{ title: string; url: string; snippet?: string }>;
};

export function parseSpiritWebSourcesHeader(
  raw: string | null,
): SpiritWebSourcesHeaderPayload | null {
  if (!raw?.trim()) return null;
  try {
    const o = JSON.parse(raw) as unknown;
    if (!o || typeof o !== "object") return null;
    const r = o as Record<string, unknown>;
    const provider = typeof r.provider === "string" ? r.provider : "unknown";
    const count = typeof r.count === "number" && Number.isFinite(r.count) ? r.count : 0;
    const srcRaw = r.sources;
    const sources: SpiritWebSourcesHeaderPayload["sources"] = [];
    if (Array.isArray(srcRaw)) {
      for (const x of srcRaw) {
        if (!x || typeof x !== "object") continue;
        const s = x as Record<string, unknown>;
        const title = typeof s.title === "string" ? s.title : "";
        const url = typeof s.url === "string" ? s.url.trim() : "";
        const snippet = typeof s.snippet === "string" ? s.snippet.trim() : undefined;
        if (url && !isVerifiedHttpUrl(url)) continue;
        if (!title.trim() && !url.trim()) continue;
        sources.push({
          title: title.trim(),
          url: url.trim(),
          ...(snippet ? { snippet: snippet.slice(0, 400) } : {}),
        });
        if (sources.length >= 12) break;
      }
    }
    return { provider, count, sources };
  } catch {
    return null;
  }
}
