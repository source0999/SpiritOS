import { describe, expect, it, vi } from "vitest";

import { runWebSearch } from "@/lib/server/web-search/provider-router";
import type {
  WebSearchAdapter,
  WebSearchProvider,
  WebSearchProviderConfig,
  WebSearchResult,
  WebSearchSource,
} from "@/lib/server/web-search/types";

function config(overrides: Partial<WebSearchProviderConfig> = {}): WebSearchProviderConfig {
  return {
    enabled: true,
    providerOrder: ["cache", "searxng", "fetch"],
    maxResults: 8,
    cache: { enabled: true, ttlSeconds: 86_400 },
    searxng: { url: "http://127.0.0.1:8080", maxResults: 8, timeoutMs: 10_000 },
    fetchPage: {
      enabled: false,
      timeoutMs: 10_000,
      respectRobots: true,
      userAgent: "SpiritOSLocalSearch/0.1",
    },
    paidFallback: { enabled: false, requireApproval: true },
    ...overrides,
  };
}

function fetchEnabled(): WebSearchProviderConfig["fetchPage"] {
  return {
    enabled: true,
    timeoutMs: 10_000,
    respectRobots: true,
    userAgent: "SpiritOSLocalSearch/0.1",
  };
}

function ok(provider: WebSearchProvider, sources: WebSearchSource[]): WebSearchResult {
  return {
    ok: true,
    searched: true,
    provider,
    query: "test",
    sources,
    elapsedMs: 1,
    providerTrace: [],
  };
}

function fail(provider: WebSearchProvider, error = "failed"): WebSearchResult {
  return {
    ok: false,
    searched: true,
    provider,
    error,
    elapsedMs: 1,
    providerTrace: [],
  };
}

function adapter(provider: WebSearchProvider, result: WebSearchResult): WebSearchAdapter {
  return {
    provider,
    search: vi.fn(async () => result),
  };
}

const source: WebSearchSource = {
  title: "Example",
  url: "https://example.com",
  provider: "searxng",
};

describe("runWebSearch", () => {
  it("cache hit stops before SearXNG", async () => {
    const cache = adapter("cache", ok("cache", [{ ...source, provider: "cache" }]));
    const searxng = adapter("searxng", ok("searxng", [source]));

    const result = await runWebSearch({
      query: "latest docs",
      config: config(),
      providers: [cache, searxng],
    });

    expect(result.ok).toBe(true);
    expect(result.provider).toBe("cache");
    expect(cache.search).toHaveBeenCalledTimes(1);
    expect(searxng.search).not.toHaveBeenCalled();
    expect(result.providerTrace.map((trace) => trace.status)).toEqual(["used"]);
  });

  it("cache miss tries SearXNG next", async () => {
    const cache = adapter("cache", ok("cache", []));
    const searxng = adapter("searxng", ok("searxng", [source]));

    const result = await runWebSearch({
      query: "latest docs",
      config: config(),
      providers: [cache, searxng],
    });

    expect(result.ok).toBe(true);
    expect(result.provider).toBe("searxng");
    expect(cache.search).toHaveBeenCalledTimes(1);
    expect(searxng.search).toHaveBeenCalledTimes(1);
    expect(result.providerTrace.map((trace) => trace.status)).toEqual(["failed", "used"]);
    expect(result.providerTrace[0]?.reason).toBe("no_verified_sources");
  });

  it("SearXNG verified results stop before fetch", async () => {
    const searxng = adapter("searxng", ok("searxng", [source]));
    const fetchPage = adapter("fetch", ok("fetch", [{ ...source, provider: "fetch" }]));

    const result = await runWebSearch({
      query: "latest docs",
      config: config({ providerOrder: ["searxng", "fetch"], fetchPage: fetchEnabled() }),
      providers: [searxng, fetchPage],
    });

    expect(result.provider).toBe("searxng");
    expect(fetchPage.search).not.toHaveBeenCalled();
  });

  it("SearXNG failure falls through to fetch", async () => {
    const searxng = adapter("searxng", fail("searxng", "searxng_unreachable"));
    const fetchPage = adapter("fetch", ok("fetch", [{ ...source, provider: "fetch" }]));

    const result = await runWebSearch({
      query: "latest docs",
      config: config({ providerOrder: ["searxng", "fetch"], fetchPage: fetchEnabled() }),
      providers: [searxng, fetchPage],
    });

    expect(result.ok).toBe(true);
    expect(result.provider).toBe("fetch");
    expect(result.providerTrace[0]?.reason).toBe("searxng_unreachable");
  });

  it("empty verified sources count as failure and fall through", async () => {
    const searxng = adapter("searxng", ok("searxng", []));
    const fetchPage = adapter("fetch", ok("fetch", [{ ...source, provider: "fetch" }]));

    const result = await runWebSearch({
      query: "latest docs",
      config: config({ providerOrder: ["searxng", "fetch"], fetchPage: fetchEnabled() }),
      providers: [searxng, fetchPage],
    });

    expect(result.provider).toBe("fetch");
    expect(result.providerTrace[0]?.status).toBe("failed");
    expect(result.providerTrace[0]?.sourceCount).toBe(0);
  });

  it("OpenAI is skipped when paid fallback is disabled", async () => {
    const openai = adapter("openai", ok("openai", [{ ...source, provider: "openai" }]));

    const result = await runWebSearch({
      query: "latest docs",
      config: config({ providerOrder: ["openai"], paidFallback: { enabled: false, requireApproval: true } }),
      providers: [openai],
    });

    expect(result.ok).toBe(false);
    expect(openai.search).not.toHaveBeenCalled();
    expect(result.providerTrace[0]).toMatchObject({
      provider: "openai",
      status: "skipped",
      reason: "paid_fallback_disabled",
    });
  });

  it("OpenAI is skipped when paid fallback is enabled but approval is missing", async () => {
    const openai = adapter("openai", ok("openai", [{ ...source, provider: "openai" }]));

    const result = await runWebSearch({
      query: "latest docs",
      config: config({ providerOrder: ["openai"], paidFallback: { enabled: true, requireApproval: true } }),
      providers: [openai],
    });

    expect(result.ok).toBe(false);
    expect(openai.search).not.toHaveBeenCalled();
    expect(result.providerTrace[0]?.reason).toBe("paid_fallback_approval_missing");
  });

  it("OpenAI is attempted only when enabled, approved, and earlier providers fail", async () => {
    const searxng = adapter("searxng", ok("searxng", []));
    const openai = adapter("openai", ok("openai", [{ ...source, provider: "openai" }]));

    const result = await runWebSearch({
      query: "latest docs",
      paidFallbackApproved: true,
      config: config({ providerOrder: ["searxng", "openai"], paidFallback: { enabled: true, requireApproval: true } }),
      providers: [searxng, openai],
    });

    expect(result.ok).toBe(true);
    expect(result.provider).toBe("openai");
    expect(searxng.search).toHaveBeenCalledTimes(1);
    expect(openai.search).toHaveBeenCalledTimes(1);
    expect(result.providerTrace.map((trace) => trace.status)).toEqual(["failed", "used"]);
  });

  it("runs the full ladder in order and uses OpenAI last only after local/free providers fail with approval", async () => {
    const calls: WebSearchProvider[] = [];
    const orderedAdapter = (provider: WebSearchProvider, result: WebSearchResult): WebSearchAdapter => ({
      provider,
      search: vi.fn(async () => {
        calls.push(provider);
        return result;
      }),
    });
    const cache = orderedAdapter("cache", ok("cache", []));
    const searxng = orderedAdapter("searxng", ok("searxng", []));
    const fetchPage = orderedAdapter("fetch", ok("fetch", []));
    const openai = orderedAdapter("openai", ok("openai", [{ ...source, provider: "openai" }]));

    const result = await runWebSearch({
      query: "latest docs",
      paidFallbackApproved: true,
      config: config({
        providerOrder: ["cache", "searxng", "fetch", "openai"],
        fetchPage: fetchEnabled(),
        paidFallback: { enabled: true, requireApproval: true },
      }),
      providers: [cache, searxng, fetchPage, openai],
    });

    expect(result.ok).toBe(true);
    expect(result.provider).toBe("openai");
    expect(calls).toEqual(["cache", "searxng", "fetch", "openai"]);
    expect(openai.search).toHaveBeenCalledTimes(1);
    expect(result.providerTrace.map((trace) => [trace.provider, trace.status])).toEqual([
      ["cache", "failed"],
      ["searxng", "failed"],
      ["fetch", "failed"],
      ["openai", "used"],
    ]);
  });

  it("skips fetch without calling the adapter unless direct fetch is explicitly enabled", async () => {
    const fetchPage = adapter("fetch", ok("fetch", [{ ...source, provider: "fetch" }]));

    const result = await runWebSearch({
      query: "https://example.com",
      config: config({ providerOrder: ["fetch"] }),
      providers: [fetchPage],
    });

    expect(result.ok).toBe(false);
    expect(fetchPage.search).not.toHaveBeenCalled();
    expect(result.providerTrace).toEqual([
      { provider: "fetch", status: "skipped", reason: "fetch_page_disabled" },
    ]);
  });

  it("provider trace records skipped, attempted, used, and failed states", async () => {
    const cache = adapter("cache", ok("cache", []));
    const searxng = adapter("searxng", ok("searxng", [source]));

    const result = await runWebSearch({
      query: "latest docs",
      config: config({ providerOrder: ["ddgs", "cache", "openai", "searxng"] }),
      providers: [cache, searxng],
    });

    expect(result.providerTrace.map((trace) => [trace.provider, trace.status, trace.reason])).toEqual([
      ["ddgs", "skipped", "provider_unavailable"],
      ["cache", "failed", "no_verified_sources"],
      ["openai", "skipped", "paid_fallback_disabled"],
      ["searxng", "used", undefined],
    ]);
  });

  it("unknown provider names do not crash the router", async () => {
    const result = await runWebSearch({
      query: "latest docs",
      config: config({ providerOrder: ["bogus"] }),
      providers: [],
    });

    expect(result.ok).toBe(false);
    expect(result.providerTrace).toEqual([{ provider: "bogus", status: "skipped", reason: "unknown_provider" }]);
  });
});
