import "server-only";

import type {
  WebSearchAdapter,
  WebSearchProviderConfig,
  WebSearchSource,
  WebSearchResult,
} from "@/lib/server/web-search/types";

type CacheEntry = {
  query: string;
  sources: WebSearchSource[];
  answerPreview?: string;
  storedAt: number;
  ttlMs: number;
};

const cache = new Map<string, CacheEntry>();

function cacheKey(query: string, maxResults: number): string {
  return `${query.trim().toLowerCase()}\n${maxResults}`;
}

function elapsedSince(startedAt: number): number {
  return Date.now() - startedAt;
}

export function clearWebSearchCache(): void {
  cache.clear();
}

export function storeWebSearchCacheResult(opts: {
  query: string;
  maxResults: number;
  config: WebSearchProviderConfig;
  sources: WebSearchSource[];
  answerPreview?: string;
}): void {
  if (!opts.config.cache.enabled || opts.sources.length === 0) return;
  cache.set(cacheKey(opts.query, opts.maxResults), {
    query: opts.query.trim(),
    sources: opts.sources.map((source) => ({ ...source })),
    ...(opts.answerPreview ? { answerPreview: opts.answerPreview } : {}),
    storedAt: Date.now(),
    ttlMs: opts.config.cache.ttlSeconds * 1000,
  });
}

export async function runCacheWebSearch(opts: {
  query: string;
  maxResults: number;
  config: WebSearchProviderConfig;
}): Promise<WebSearchResult> {
  const startedAt = Date.now();
  if (!opts.config.cache.enabled) {
    return {
      ok: false,
      searched: false,
      provider: "cache",
      error: "cache_disabled",
      elapsedMs: elapsedSince(startedAt),
      providerTrace: [],
    };
  }

  const key = cacheKey(opts.query, opts.maxResults);
  const entry = cache.get(key);
  if (!entry) {
    return {
      ok: true,
      searched: true,
      provider: "cache",
      query: opts.query.trim(),
      sources: [],
      elapsedMs: elapsedSince(startedAt),
      providerTrace: [],
    };
  }

  if (Date.now() - entry.storedAt > entry.ttlMs) {
    cache.delete(key);
    return {
      ok: true,
      searched: true,
      provider: "cache",
      query: opts.query.trim(),
      sources: [],
      elapsedMs: elapsedSince(startedAt),
      providerTrace: [],
    };
  }

  return {
    ok: true,
    searched: true,
    provider: "cache",
    query: entry.query,
    sources: entry.sources.map((source) => ({ ...source })),
    ...(entry.answerPreview ? { answerPreview: entry.answerPreview } : {}),
    elapsedMs: elapsedSince(startedAt),
    providerTrace: [],
  };
}

export const cacheWebSearchProvider: WebSearchAdapter = {
  provider: "cache",
  search: ({ query, maxResults, config }) => runCacheWebSearch({ query, maxResults, config }),
};
