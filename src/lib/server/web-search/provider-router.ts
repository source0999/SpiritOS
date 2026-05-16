import "server-only";

import { cacheWebSearchProvider, storeWebSearchCacheResult } from "@/lib/server/web-search/cache-provider";
import { fetchPageProvider } from "@/lib/server/web-search/fetch-page-provider";
import { openAiWebSearchProvider } from "@/lib/server/web-search/openai-provider";
import { getWebSearchProviderConfig } from "@/lib/server/web-search/provider-config";
import { searxngProvider } from "@/lib/server/web-search/searxng-provider";
import type {
  WebSearchAdapter,
  WebSearchProvider,
  WebSearchProviderConfig,
  WebSearchProviderTrace,
  WebSearchResult,
} from "@/lib/server/web-search/types";

const KNOWN_PROVIDERS = new Set<WebSearchProvider>(["cache", "searxng", "ddgs", "fetch", "openai", "manual"]);
const DEFAULT_ADAPTERS: WebSearchAdapter[] = [
  cacheWebSearchProvider,
  searxngProvider,
  fetchPageProvider,
  openAiWebSearchProvider,
];

export type RunWebSearchOptions = {
  query: string;
  maxResults?: number;
  paidFallbackApproved?: boolean;
  config?: WebSearchProviderConfig;
  providers?: WebSearchAdapter[];
};

function nowMs(): number {
  return Date.now();
}

function isKnownProvider(provider: string): provider is WebSearchProvider {
  return KNOWN_PROVIDERS.has(provider as WebSearchProvider);
}

function fallbackFailure(opts: {
  query: string;
  providerTrace: WebSearchProviderTrace[];
  startedAt: number;
  searched: boolean;
  error: string;
  detail: string;
}): WebSearchResult {
  return {
    ok: false,
    searched: opts.searched,
    provider: "manual",
    error: opts.error,
    detail: opts.detail,
    elapsedMs: nowMs() - opts.startedAt,
    providerTrace: opts.providerTrace,
  };
}

export async function runWebSearch(opts: RunWebSearchOptions): Promise<WebSearchResult> {
  const startedAt = nowMs();
  const query = opts.query.trim();
  const config = opts.config ?? getWebSearchProviderConfig();
  const maxResults =
    typeof opts.maxResults === "number" && opts.maxResults > 0
      ? Math.min(Math.floor(opts.maxResults), 12)
      : config.maxResults;
  const providerTrace: WebSearchProviderTrace[] = [];
  const adapters = new Map((opts.providers ?? DEFAULT_ADAPTERS).map((adapter) => [adapter.provider, adapter]));
  let attempted = false;

  if (!query) {
    return fallbackFailure({
      query,
      providerTrace,
      startedAt,
      searched: false,
      error: "empty_query",
      detail: "Query is empty.",
    });
  }

  if (!config.enabled) {
    providerTrace.push({
      provider: "manual",
      status: "skipped",
      reason: "web_search_disabled",
      elapsedMs: nowMs() - startedAt,
    });
    return fallbackFailure({
      query,
      providerTrace,
      startedAt,
      searched: false,
      error: "disabled",
      detail: "WEB_SEARCH_ENABLED is not true - web search is off.",
    });
  }

  for (const providerName of config.providerOrder) {
    if (!isKnownProvider(providerName) || providerName === "manual") {
      providerTrace.push({ provider: providerName, status: "skipped", reason: "unknown_provider" });
      continue;
    }

    if (providerName === "openai") {
      if (!config.paidFallback.enabled) {
        providerTrace.push({ provider: "openai", status: "skipped", reason: "paid_fallback_disabled" });
        continue;
      }
      if (config.paidFallback.requireApproval && opts.paidFallbackApproved !== true) {
        providerTrace.push({ provider: "openai", status: "skipped", reason: "paid_fallback_approval_missing" });
        continue;
      }
    }

    if (providerName === "fetch" && !config.fetchPage.enabled) {
      providerTrace.push({ provider: "fetch", status: "skipped", reason: "fetch_page_disabled" });
      continue;
    }

    const adapter = adapters.get(providerName);
    if (!adapter) {
      providerTrace.push({ provider: providerName, status: "skipped", reason: "provider_unavailable" });
      continue;
    }

    const providerStartedAt = nowMs();
    providerTrace.push({ provider: providerName, status: "attempted" });
    attempted = true;

    try {
      const result = await adapter.search({ query, maxResults, config });
      const elapsedMs = nowMs() - providerStartedAt;
      const attemptedTrace = providerTrace[providerTrace.length - 1];

      if (result.ok && result.sources.length > 0) {
        attemptedTrace.status = "used";
        attemptedTrace.elapsedMs = elapsedMs;
        attemptedTrace.sourceCount = result.sources.length;
        if (providerName !== "cache") {
          storeWebSearchCacheResult({
            query,
            maxResults,
            config,
            sources: result.sources,
            answerPreview: result.answerPreview,
          });
        }
        return {
          ...result,
          provider: providerName,
          query,
          searched: true,
          elapsedMs: nowMs() - startedAt,
          providerTrace,
        };
      }

      attemptedTrace.status = "failed";
      attemptedTrace.elapsedMs = elapsedMs;
      attemptedTrace.sourceCount = result.ok ? result.sources.length : 0;
      attemptedTrace.reason = result.ok ? "no_verified_sources" : result.error;
    } catch (error) {
      const attemptedTrace = providerTrace[providerTrace.length - 1];
      attemptedTrace.status = "failed";
      attemptedTrace.elapsedMs = nowMs() - providerStartedAt;
      attemptedTrace.sourceCount = 0;
      attemptedTrace.reason = error instanceof Error ? error.message : String(error);
    }
  }

  return fallbackFailure({
    query,
    providerTrace,
    startedAt,
    searched: attempted,
    error: "no_local_provider_available",
    detail: "No free/local web-search provider returned verified sources.",
  });
}
