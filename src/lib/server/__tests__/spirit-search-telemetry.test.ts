import { describe, expect, it, vi } from "vitest";

import {
  buildSpiritSearchHeaders,
  logSpiritSearchEvent,
  sanitizeForHttpByteStringHeader,
  trimSearchQueryForLog,
} from "@/lib/server/spirit-search-telemetry";

describe("spirit-search-telemetry", () => {
  it("trimSearchQueryForLog caps length with ASCII ellipsis (ByteString-safe)", () => {
    const long = "x".repeat(200);
    expect(trimSearchQueryForLog(long).endsWith("...")).toBe(true);
    expect(trimSearchQueryForLog(long).length).toBe(163);
  });

  it("sanitizeForHttpByteStringHeader maps ellipsis and non-Latin1", () => {
    expect(sanitizeForHttpByteStringHeader("a\u2026b")).toBe("a...b");
    expect(sanitizeForHttpByteStringHeader("café")).toBe("café");
    expect(sanitizeForHttpByteStringHeader("emoji\uD83D\uDE00")).toBe("emoji?");
  });

  it("buildSpiritSearchHeaders yields only ByteString-safe header values", () => {
    const h = buildSpiritSearchHeaders({
      routeLane: "openai-web-search",
      routeConfidence: "high",
      webSearch: "used",
      searchStatus: "used",
      provider: "openai",
      sourceCount: 1,
      queryTrimmed: "hello\u2026world",
      elapsedMs: 1,
      searchKind: "researcher",
      skipReason: "café",
      webSourcesJson: '{"title":"T\u2026"}',
    });
    for (const v of Object.values(h)) {
      for (let i = 0; i < v.length; i++) {
        expect(v.charCodeAt(i)).toBeLessThanOrEqual(255);
      }
    }
    expect(h["x-spirit-search-query"]).toContain("...");
    expect(h["x-spirit-search-query"]).not.toContain("\u2026");
  });

  it("logSpiritSearchEvent never includes api key shaped strings", () => {
    const spy = vi.spyOn(console, "log").mockImplementation(() => {});
    logSpiritSearchEvent({
      route: "openai-web-search",
      status: "failed",
      mode: "researcher",
      queryTrimmed: "ok",
      reason: "provider_timeout",
    });
    const line = spy.mock.calls[0]?.[0] as string;
    expect(line).toContain("[spirit-search]");
    expect(line).not.toMatch(/sk_live/i);
    spy.mockRestore();
  });

  it("buildSpiritSearchHeaders emits source count and search status", () => {
    const h = buildSpiritSearchHeaders({
      routeLane: "openai-web-search",
      routeConfidence: "high",
      webSearch: "used",
      searchStatus: "used",
      provider: "openai",
      sourceCount: 3,
      queryTrimmed: "aba reinforcement",
      elapsedMs: 1200,
      searchKind: "researcher",
      skipReason: null,
      webSourcesJson: '{"provider":"openai","count":3,"sources":[]}',
    });
    expect(h["x-spirit-source-count"]).toBe("3");
    expect(h["x-spirit-search-status"]).toBe("used");
    expect(h["x-spirit-search-provider"]).toBe("openai");
    expect(h["x-spirit-search-elapsed-ms"]).toBe("1200");
    expect(h["x-spirit-search-query"]).toContain("aba");
  });
});
