import { describe, expect, it, vi } from "vitest";

import {
  isAllowedByRobotsTxt,
  runFetchPageWebSearch,
} from "@/lib/server/web-search/fetch-page-provider";
import type { WebSearchProviderConfig } from "@/lib/server/web-search/types";

function config(overrides: Partial<WebSearchProviderConfig> = {}): WebSearchProviderConfig {
  return {
    enabled: true,
    providerOrder: ["fetch"],
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

describe("isAllowedByRobotsTxt", () => {
  it("uses the most specific allow/disallow rule", () => {
    const robots = `User-agent: *
Disallow: /private/
Allow: /private/public.html`;

    expect(isAllowedByRobotsTxt(robots, "https://example.com/private/public.html", "SpiritOSLocalSearch/0.1")).toBe(true);
    expect(isAllowedByRobotsTxt(robots, "https://example.com/private/secret.html", "SpiritOSLocalSearch/0.1")).toBe(false);
  });
});

describe("runFetchPageWebSearch", () => {
  it("extracts title, canonical URL, and snippet from static HTML", async () => {
    const fetchImpl = vi.fn(async (url: RequestInfo | URL) => {
      if (String(url).endsWith("/robots.txt")) {
        return new Response("User-agent: *\nAllow: /", { status: 200 });
      }
      return new Response(
        `<!doctype html>
        <html>
          <head>
            <link rel="canonical" href="https://example.com/canonical">
            <title>Example page</title>
            <meta name="description" content="A useful description.">
          </head>
          <body><p>This is a long readable paragraph with enough text to use as a fallback snippet.</p></body>
        </html>`,
        { status: 200, headers: { "Content-Type": "text/html" } },
      );
    }) as unknown as typeof fetch;

    const result = await runFetchPageWebSearch({
      query: "https://example.com/page",
      maxResults: 5,
      config: config(),
      fetchImpl,
    });

    expect(result.ok && result.sources).toEqual([
      {
        title: "Example page",
        url: "https://example.com/canonical",
        snippet: "A useful description.",
        provider: "fetch",
      },
    ]);
  });

  it("rejects non-URL queries", async () => {
    const result = await runFetchPageWebSearch({
      query: "latest vite release notes",
      maxResults: 5,
      config: config(),
      fetchImpl: vi.fn() as unknown as typeof fetch,
    });

    expect(result).toMatchObject({
      ok: false,
      searched: false,
      provider: "fetch",
      error: "fetch_query_not_url",
    });
  });

  it("returns robots-disallowed failure when strict robots mode blocks the page", async () => {
    const fetchImpl = vi.fn(async () => new Response("User-agent: *\nDisallow: /blocked", { status: 200 })) as unknown as typeof fetch;

    const result = await runFetchPageWebSearch({
      query: "https://example.com/blocked/page",
      maxResults: 5,
      config: config(),
      fetchImpl,
    });

    expect(result).toMatchObject({
      ok: false,
      searched: false,
      provider: "fetch",
      error: "robots_disallowed",
    });
  });

  it("returns timeout failure when page fetch aborts", async () => {
    const fetchImpl = vi.fn(async (url: RequestInfo | URL) => {
      if (String(url).endsWith("/robots.txt")) {
        return new Response("", { status: 404 });
      }
      const error = new Error("aborted");
      error.name = "AbortError";
      throw error;
    }) as unknown as typeof fetch;

    const result = await runFetchPageWebSearch({
      query: "https://example.com/page",
      maxResults: 5,
      config: config(),
      fetchImpl,
    });

    expect(result).toMatchObject({
      ok: false,
      provider: "fetch",
      error: "fetch_timeout",
    });
  });
});
