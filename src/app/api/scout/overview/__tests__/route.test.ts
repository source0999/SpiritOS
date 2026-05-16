import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "../route";

const origFetch = globalThis.fetch;
const origScoutApiUrl = process.env.SCOUT_API_URL;

afterEach(() => {
  globalThis.fetch = origFetch;
  process.env.SCOUT_API_URL = origScoutApiUrl;
  vi.restoreAllMocks();
});

describe("GET /api/scout/overview", () => {
  it("passes the Scout overview response through with no-store caching", async () => {
    process.env.SCOUT_API_URL = "http://scout.local:8077/";
    const upstream = {
      counts: { raw_event_index: 2, extracted_artifacts: 1, packets: 1, verdicts: 0 },
      recent: { surfaced: [] },
    };
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(upstream), { status: 200 }),
    );
    globalThis.fetch = mockFetch;

    const res = await GET(new Request("http://localhost/api/scout/overview?limit=7"));

    expect(mockFetch).toHaveBeenCalledWith(
      "http://scout.local:8077/v1/scout/overview?limit=7",
      expect.objectContaining({ cache: "no-store" }),
    );
    expect(res.status).toBe(200);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    await expect(res.json()).resolves.toEqual(upstream);
  });

  it("returns a safe unavailable JSON response when Scout is offline", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("connection refused"));

    const res = await GET(new Request("http://localhost/api/scout/overview"));

    expect(res.status).toBe(200);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    await expect(res.json()).resolves.toEqual({
      ok: false,
      status: "unavailable",
      error: "Scout overview unavailable.",
    });
  });

  it("bounds the proxied limit to Scout's supported range", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ recent: { surfaced: [] } }), { status: 200 }),
    );
    globalThis.fetch = mockFetch;

    await GET(new Request("http://localhost/api/scout/overview?limit=999"));

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8077/v1/scout/overview?limit=50",
      expect.any(Object),
    );
  });
});
