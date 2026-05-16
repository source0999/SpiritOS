import "server-only";

import { resolveVerifiedHttpUrl } from "@/lib/verified-http-url";
import type { WebSearchProvider, WebSearchSource } from "@/lib/server/web-search/types";

export type RawWebSearchSource = {
  title?: string | null;
  url?: string | null;
  snippet?: string | null;
  publishedAt?: string | null;
  provider?: WebSearchProvider;
  source?: WebSearchProvider;
};

function trimToUndefined(value: string | null | undefined, maxLength: number): string | undefined {
  const trimmed = value?.trim();
  if (!trimmed) return undefined;
  return trimmed.length > maxLength ? trimmed.slice(0, maxLength).trimEnd() : trimmed;
}

function fallbackTitle(url: string): string {
  try {
    return new URL(url).hostname || "Untitled";
  } catch {
    return "Untitled";
  }
}

function dedupeKey(url: string): string {
  try {
    const parsed = new URL(url);
    parsed.hash = "";
    if (parsed.pathname !== "/") parsed.pathname = parsed.pathname.replace(/\/+$/, "");
    return parsed.toString().toLowerCase();
  } catch {
    return url.toLowerCase();
  }
}

export function normalizeWebSearchSources(
  sources: RawWebSearchSource[],
  opts: {
    maxResults: number;
    provider?: WebSearchProvider;
  },
): WebSearchSource[] {
  const maxResults = Math.max(0, Math.floor(opts.maxResults));
  const normalized: WebSearchSource[] = [];
  const seen = new Set<string>();

  for (const source of sources) {
    if (normalized.length >= maxResults) break;

    const url = resolveVerifiedHttpUrl(source.url ?? undefined);
    if (!url) continue;

    const key = dedupeKey(url);
    if (seen.has(key)) continue;
    seen.add(key);

    const title = trimToUndefined(source.title, 180) ?? fallbackTitle(url);
    const snippet = trimToUndefined(source.snippet, 500);
    const publishedAt = trimToUndefined(source.publishedAt, 80);
    const provider = source.provider ?? source.source ?? opts.provider;

    normalized.push({
      title,
      url,
      ...(snippet ? { snippet } : {}),
      ...(publishedAt ? { publishedAt } : {}),
      ...(provider ? { provider } : {}),
    });
  }

  return normalized;
}
