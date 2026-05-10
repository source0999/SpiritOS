import { describe, expect, it, vi } from "vitest";

import { runSearxngWebSearch } from "@/lib/server/web-search/searxng-provider";
import type { WebSearchProviderConfig } from "@/lib/server/web-search/types";

function config(overrides: Partial<WebSearchProviderConfig> = {}): WebSearchProviderConfig {
  return {
    enabled: true,
    providerOrder: ["searxng"],
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

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

describe("runSearxngWebSearch", () => {
  it("queries /search with q and format=json", async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({
        results: [{ title: "SearXNG", url: "https://docs.searxng.org/", content: "Docs" }],
      }),
    ) as unknown as typeof fetch;

    const result = await runSearxngWebSearch({
      query: "searxng docs",
      maxResults: 5,
      config: config(),
      fetchImpl,
    });

    expect(result.ok).toBe(true);
    expect(result.provider).toBe("searxng");
    expect(result.ok ? result.sources : []).toEqual([
      {
        title: "SearXNG",
        url: "https://docs.searxng.org/",
        snippet: "Docs",
        provider: "searxng",
      },
    ]);
    const calledUrl = new URL(String(vi.mocked(fetchImpl).mock.calls[0]?.[0]));
    expect(calledUrl.pathname).toBe("/search");
    expect(calledUrl.searchParams.get("q")).toBe("searxng docs");
    expect(calledUrl.searchParams.get("format")).toBe("json");
  });

  it("filters invalid results and respects max result caps", async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({
        results: [
          { title: "One", url: "https://one.example/", content: "First" },
          { title: "Unsafe", url: "javascript:alert(1)", content: "Nope" },
          { title: "Two", url: "https://two.example/", content: "Second" },
        ],
      }),
    ) as unknown as typeof fetch;

    const result = await runSearxngWebSearch({
      query: "examples",
      maxResults: 1,
      config: config({ searxng: { url: "http://127.0.0.1:8080", maxResults: 8, timeoutMs: 10_000 } }),
      fetchImpl,
    });

    expect(result.ok && result.sources).toEqual([
      { title: "One", url: "https://one.example/", snippet: "First", provider: "searxng" },
    ]);
  });

  it("returns a clear failure when JSON output is forbidden", async () => {
    const fetchImpl = vi.fn(async () => new Response("json disabled", { status: 403 })) as unknown as typeof fetch;

    const result = await runSearxngWebSearch({
      query: "examples",
      maxResults: 5,
      config: config(),
      fetchImpl,
    });

    expect(result).toMatchObject({
      ok: false,
      provider: "searxng",
      error: "searxng_json_forbidden",
      detail: "json disabled",
    });
  });

  it("returns invalid-json failure for HTML responses", async () => {
    const fetchImpl = vi.fn(async () => new Response("<html></html>", { status: 200 })) as unknown as typeof fetch;

    const result = await runSearxngWebSearch({
      query: "examples",
      maxResults: 5,
      config: config(),
      fetchImpl,
    });

    expect(result).toMatchObject({
      ok: false,
      provider: "searxng",
      error: "searxng_invalid_json",
      detail: "<html></html>",
    });
  });

  it("returns unreachable failure when fetch throws", async () => {
    const fetchImpl = vi.fn(async () => {
      throw new Error("connect ECONNREFUSED");
    }) as unknown as typeof fetch;

    const result = await runSearxngWebSearch({
      query: "examples",
      maxResults: 5,
      config: config(),
      fetchImpl,
    });

    expect(result).toMatchObject({
      ok: false,
      provider: "searxng",
      error: "searxng_unreachable",
      detail: "connect ECONNREFUSED",
    });
  });
});
