import { describe, expect, it, vi, beforeEach } from "vitest";

const runWebSearchSpy = vi.hoisted(() => vi.fn());

vi.mock("@/lib/server/web-search/provider-router", () => ({
  runWebSearch: runWebSearchSpy,
}));

import { POST } from "@/app/api/research/web-search/route";

function jsonRequest(body: unknown): Request {
  return new Request("http://localhost/api/research/web-search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

describe("POST /api/research/web-search", () => {
  beforeEach(() => {
    runWebSearchSpy.mockReset();
  });

  it("returns provider-neutral validation errors", async () => {
    const res = await POST(jsonRequest({ query: "" }));

    expect(res.status).toBe(400);
    expect(await res.json()).toMatchObject({
      ok: false,
      provider: "manual",
      searched: false,
      error: "missing_query",
    });
    expect(runWebSearchSpy).not.toHaveBeenCalled();
  });

  it("calls the provider router with max result clamp and explicit paid approval", async () => {
    runWebSearchSpy.mockResolvedValueOnce({
      ok: true,
      searched: true,
      provider: "searxng",
      query: "docs",
      sources: [{ title: "Docs", url: "https://example.com/docs", provider: "searxng" }],
      elapsedMs: 12,
      providerTrace: [
        { provider: "cache", status: "failed" },
        { provider: "searxng", status: "used" },
      ],
    });

    const res = await POST(jsonRequest({ query: " docs ", maxResults: 99, paidFallbackApproved: true }));

    expect(res.status).toBe(200);
    expect(runWebSearchSpy).toHaveBeenCalledWith({
      query: "docs",
      maxResults: 12,
      paidFallbackApproved: true,
    });
    expect(await res.json()).toMatchObject({
      ok: true,
      provider: "searxng",
      sources: [{ url: "https://example.com/docs" }],
    });
  });

  it("does not approve paid fallback unless the body explicitly passes true", async () => {
    runWebSearchSpy.mockResolvedValueOnce({
      ok: false,
      searched: false,
      provider: "manual",
      error: "no_local_provider_available",
      detail: "No free/local web-search provider returned verified sources.",
      elapsedMs: 1,
      providerTrace: [],
    });

    const res = await POST(jsonRequest({ query: "docs", paidFallbackApproved: "true" }));

    expect(res.status).toBe(422);
    expect(runWebSearchSpy).toHaveBeenCalledWith({
      query: "docs",
      maxResults: undefined,
      paidFallbackApproved: false,
    });
  });

  it("maps disabled search to 403", async () => {
    runWebSearchSpy.mockResolvedValueOnce({
      ok: false,
      searched: false,
      provider: "manual",
      error: "disabled",
      detail: "WEB_SEARCH_ENABLED is not true - web search is off.",
      elapsedMs: 1,
      providerTrace: [],
    });

    const res = await POST(jsonRequest({ query: "docs" }));

    expect(res.status).toBe(403);
    expect(await res.json()).toMatchObject({ ok: false, error: "disabled" });
  });
});
