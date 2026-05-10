import { describe, expect, it } from "vitest";

import { normalizeWebSearchSources } from "@/lib/server/web-search/source-normalizer";

describe("normalizeWebSearchSources", () => {
  it("removes unsafe and malformed URLs", () => {
    const sources = normalizeWebSearchSources(
      [
        { title: "Good", url: "https://example.com/a" },
        { title: "Script", url: "javascript:alert(1)" },
        { title: "Relative", url: "/docs" },
        { title: "Mail", url: "mailto:test@example.com" },
      ],
      { maxResults: 10, provider: "searxng" },
    );

    expect(sources).toEqual([{ title: "Good", url: "https://example.com/a", provider: "searxng" }]);
  });

  it("deduplicates by normalized URL and strips fragments", () => {
    const sources = normalizeWebSearchSources(
      [
        { title: "First", url: "https://example.com/a#intro" },
        { title: "Second", url: "https://example.com/a" },
        { title: "Third", url: "https://example.com/a/" },
      ],
      { maxResults: 10 },
    );

    expect(sources).toHaveLength(1);
    expect(sources[0]?.title).toBe("First");
  });

  it("trims text, fills missing titles, and caps result count", () => {
    const sources = normalizeWebSearchSources(
      [
        { title: "  ", url: "www.example.com/path", snippet: "  Useful snippet  " },
        { title: "Second", url: "https://second.example/path" },
      ],
      { maxResults: 1, provider: "fetch" },
    );

    expect(sources).toEqual([
      {
        title: "www.example.com",
        url: "https://www.example.com/path",
        snippet: "Useful snippet",
        provider: "fetch",
      },
    ]);
  });
});
