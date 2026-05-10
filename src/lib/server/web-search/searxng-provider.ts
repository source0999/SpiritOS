import "server-only";

import { normalizeWebSearchSources } from "@/lib/server/web-search/source-normalizer";
import type {
  WebSearchAdapter,
  WebSearchProviderConfig,
  WebSearchResult,
} from "@/lib/server/web-search/types";

type SearxngSearchResult = {
  title?: unknown;
  url?: unknown;
  content?: unknown;
  publishedDate?: unknown;
  published_date?: unknown;
};

const DEFAULT_TIMEOUT_MS = 10_000;

function elapsedSince(startedAt: number): number {
  return Date.now() - startedAt;
}

function failure(opts: {
  query: string;
  startedAt: number;
  error: string;
  detail?: string;
  searched?: boolean;
}): WebSearchResult {
  return {
    ok: false,
    searched: opts.searched ?? true,
    provider: "searxng",
    error: opts.error,
    ...(opts.detail ? { detail: opts.detail } : {}),
    elapsedMs: elapsedSince(opts.startedAt),
    providerTrace: [],
  };
}

function buildSearxngUrl(baseUrl: string, query: string): string {
  const url = new URL("/search", baseUrl);
  url.searchParams.set("q", query);
  url.searchParams.set("format", "json");
  return url.toString();
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

export async function runSearxngWebSearch(opts: {
  query: string;
  maxResults: number;
  config: WebSearchProviderConfig;
  fetchImpl?: typeof fetch;
}): Promise<WebSearchResult> {
  const startedAt = Date.now();
  const query = opts.query.trim();
  if (!query) {
    return failure({ query, startedAt, error: "empty_query", detail: "Query is empty.", searched: false });
  }

  if (!opts.config.searxng.url.trim()) {
    return failure({
      query,
      startedAt,
      error: "searxng_not_configured",
      detail: "SEARXNG_URL is not configured.",
      searched: false,
    });
  }

  const fetchImpl = opts.fetchImpl ?? fetch;
  const timeoutMs = opts.config.searxng.timeoutMs || DEFAULT_TIMEOUT_MS;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetchImpl(buildSearxngUrl(opts.config.searxng.url, query), {
      method: "GET",
      headers: {
        Accept: "application/json",
        "User-Agent": opts.config.fetchPage.userAgent,
      },
      signal: controller.signal,
    });

    const text = await response.text();
    if (!response.ok) {
      return failure({
        query,
        startedAt,
        error: response.status === 403 ? "searxng_json_forbidden" : `searxng_${response.status}`,
        detail: text.slice(0, 400),
      });
    }

    let json: unknown;
    try {
      json = JSON.parse(text) as unknown;
    } catch {
      return failure({
        query,
        startedAt,
        error: "searxng_invalid_json",
        detail: text.slice(0, 400),
      });
    }

    const results =
      json && typeof json === "object" && Array.isArray((json as { results?: unknown }).results)
        ? ((json as { results: SearxngSearchResult[] }).results)
        : [];
    const sources = normalizeWebSearchSources(
      results.map((result) => ({
        title: stringValue(result.title),
        url: stringValue(result.url),
        snippet: stringValue(result.content),
        publishedAt: stringValue(result.publishedDate) ?? stringValue(result.published_date),
        provider: "searxng",
      })),
      { maxResults: Math.min(opts.maxResults, opts.config.searxng.maxResults), provider: "searxng" },
    );

    return {
      ok: true,
      searched: true,
      provider: "searxng",
      query,
      sources,
      elapsedMs: elapsedSince(startedAt),
      providerTrace: [],
    };
  } catch (error) {
    const aborted = error instanceof Error && error.name === "AbortError";
    return failure({
      query,
      startedAt,
      error: aborted ? "searxng_timeout" : "searxng_unreachable",
      detail: error instanceof Error ? error.message : String(error),
    });
  } finally {
    clearTimeout(timeout);
  }
}

export const searxngProvider: WebSearchAdapter = {
  provider: "searxng",
  search: ({ query, maxResults, config }) => runSearxngWebSearch({ query, maxResults, config }),
};
