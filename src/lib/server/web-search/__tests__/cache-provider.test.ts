import { beforeEach, describe, expect, it } from "vitest";

import {
  clearWebSearchCache,
  runCacheWebSearch,
  storeWebSearchCacheResult,
} from "@/lib/server/web-search/cache-provider";
import type { WebSearchProviderConfig } from "@/lib/server/web-search/types";

function config(overrides: Partial<WebSearchProviderConfig> = {}): WebSearchProviderConfig {
  return {
    enabled: true,
    providerOrder: ["cache"],
    maxResults: 8,
    cache: { enabled: true, ttlSeconds: 86_400 },
    searxng: { url: "http://127.0.0.1:8080", maxResults: 8, timeoutMs: 10_000 },
    fetchPage: {
      enabled: true,
      timeoutMs: 10_000,
      respectRobots: true,
      userAgent: "SpiritOSLocalSearch/0.1",
    },
    paidFallback: { enabled: false, requireApproval: true },
    ...overrides,
  };
}

describe("cache web-search provider", () => {
  beforeEach(() => clearWebSearchCache());

  it("returns an empty successful miss", async () => {
    const result = await runCacheWebSearch({ query: "docs", maxResults: 5, config: config() });

    expect(result).toMatchObject({
      ok: true,
      searched: true,
      provider: "cache",
      sources: [],
    });
  });

  it("returns stored sources for matching query and max result count", async () => {
    storeWebSearchCacheResult({
      query: "Docs",
      maxResults: 5,
      config: config(),
      sources: [{ title: "Docs", url: "https://example.com/docs", provider: "searxng" }],
      answerPreview: "preview",
    });

    const result = await runCacheWebSearch({ query: "docs", maxResults: 5, config: config() });

    expect(result).toMatchObject({
      ok: true,
      provider: "cache",
      answerPreview: "preview",
      sources: [{ title: "Docs", url: "https://example.com/docs", provider: "searxng" }],
    });
  });

  it("does not read or write when cache is disabled", async () => {
    const disabledConfig = config({ cache: { enabled: false, ttlSeconds: 86_400 } });
    storeWebSearchCacheResult({
      query: "docs",
      maxResults: 5,
      config: disabledConfig,
      sources: [{ title: "Docs", url: "https://example.com/docs" }],
    });

    const result = await runCacheWebSearch({ query: "docs", maxResults: 5, config: disabledConfig });

    expect(result).toMatchObject({
      ok: false,
      searched: false,
      provider: "cache",
      error: "cache_disabled",
    });
  });
});
