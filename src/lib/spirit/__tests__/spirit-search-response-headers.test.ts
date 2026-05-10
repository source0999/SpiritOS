import { describe, expect, it } from "vitest";

import { normalizeClientSearchStatus, parseSpiritSearchHeaders } from "@/lib/spirit/spirit-search-response-headers";

describe("parseSpiritSearchHeaders", () => {
  it("parses headers into structured fields", () => {
    const headers = new Headers();
    headers.set("x-spirit-route-lane", "local-web-search");
    headers.set("x-spirit-route-confidence", "high");
    headers.set("x-spirit-web-search", "used");
    headers.set("x-spirit-search-status", "used");
    headers.set("x-spirit-search-provider", "searxng");
    headers.set("x-spirit-source-count", "4");
    headers.set("x-spirit-search-query", "history of telegraph");
    headers.set("x-spirit-search-elapsed-ms", "900");
    headers.set("x-spirit-search-kind", "teacher");
    const res = new Response(null, { headers });
    const p = parseSpiritSearchHeaders(res);
    expect(p.searchStatus).toBe("used");
    expect(p.sourceCount).toBe(4);
    expect(p.searchElapsedMs).toBe(900);
    expect(p.searchKind).toBe("teacher");
    expect(p.searchQuery).toContain("telegraph");
    expect(p.searchProvider).toBe("searxng");
    expect(p.routeLane).toBe("local-web-search");
  });

  it("keeps legacy openai-web-search lane readable for older responses", () => {
    const headers = new Headers();
    headers.set("x-spirit-route-lane", "openai-web-search");
    const res = new Response(null, { headers });
    expect(parseSpiritSearchHeaders(res).routeLane).toBe("openai-web-search");
  });

  it("normalizeClientSearchStatus maps none for garbage", () => {
    expect(normalizeClientSearchStatus("weird")).toBe("none");
  });
});
