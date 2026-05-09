import { describe, expect, it } from "vitest";

import {
  buildWebSearchSourcesHeader,
  formatResearchContextForHermes,
} from "@/lib/server/spirit-web-research-guard";

describe("buildWebSearchSourcesHeader", () => {
  it("returns JSON with provider, count, and sources when search succeeded", () => {
    const raw = buildWebSearchSourcesHeader({
      ok: true,
      provider: "openai",
      query: "q",
      searched: true,
      sources: [
        { title: "Example", url: "https://example.com/a" },
        { title: "B", url: "https://b.test" },
      ],
    });
    expect(raw).toBeTruthy();
    const o = JSON.parse(raw!) as { provider: string; count: number; sources: unknown[] };
    expect(o.provider).toBe("openai");
    expect(o.count).toBe(2);
    expect(Array.isArray(o.sources)).toBe(true);
    expect(o.sources).toHaveLength(2);
  });

  it("returns null when search failed", () => {
    expect(
      buildWebSearchSourcesHeader({
        ok: false,
        provider: "openai",
        searched: false,
        error: "disabled",
      }),
    ).toBeNull();
  });

  it("normalizes bare-host URLs in header JSON", () => {
    const raw = buildWebSearchSourcesHeader({
      ok: true,
      provider: "openai",
      query: "q",
      searched: true,
      sources: [{ title: "X", url: "www.example.com/abc" }],
    });
    expect(raw).toBeTruthy();
    const o = JSON.parse(raw!) as { count: number; sources: Array<{ url: string }> };
    expect(o.count).toBe(1);
    expect(o.sources[0]?.url).toBe("https://www.example.com/abc");
  });
});

describe("formatResearchContextForHermes", () => {
  it("uses short no-URL banner when search ok but sources lack URLs", () => {
    const ctx = formatResearchContextForHermes("q", {
      ok: true,
      searched: true,
      provider: "openai",
      query: "q",
      sources: [{ title: "No link", url: "" }],
    });
    expect(ctx).toContain("no verified external URLs");
    expect(ctx).not.toContain("Web research digest");
  });

  it("includes digest only when real URLs exist", () => {
    const ctx = formatResearchContextForHermes("q", {
      ok: true,
      searched: true,
      provider: "openai",
      query: "q",
      sources: [{ title: "T", url: "https://example.com/x", snippet: "snip" }],
    });
    expect(ctx).toContain("Web research digest");
    expect(ctx).toContain("https://example.com/x");
    expect(ctx).toContain("snippet:");
  });

  it("normalizes bare-host sources into digest with https links", () => {
    const ctx = formatResearchContextForHermes("q", {
      ok: true,
      searched: true,
      provider: "openai",
      query: "q",
      sources: [{ title: "T", url: "www.example.com/x" }],
    });
    expect(ctx).toContain("Web research digest");
    expect(ctx).toContain("https://www.example.com/x");
  });

  it("ignores non-http schemes for digest", () => {
    const ctx = formatResearchContextForHermes("q", {
      ok: true,
      searched: true,
      provider: "openai",
      query: "q",
      sources: [{ title: "T", url: "ftp://example.com/x" }],
    });
    expect(ctx).toContain("no verified external URLs");
  });
});
