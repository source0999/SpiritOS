import { afterEach, describe, expect, it, vi } from "vitest";
import { clearMobileOptimizedSourceCache, JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";

const item: JellyfinItem = {
  Id: "video-cache-1",
  Name: "Cache Clip",
  Type: "Video",
  MediaType: "Video",
};

describe("JellyfinClient mobile optimized cache", () => {
  afterEach(() => {
    clearMobileOptimizedSourceCache();
    vi.restoreAllMocks();
  });

  it("caches mobile optimized metadata by item id", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            available: true,
            mode: "mobile optimized",
            url: "/api/spiritflix/mobile-optimized?stream=1&key=video-cache-1",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = new JellyfinClient("http://127.0.0.1:8096");
    const first = await client.getMobileOptimizedSource(item);
    const second = await client.getMobileOptimizedSource(item);

    expect(first.available).toBe(true);
    expect(second.url).toBe(first.url);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(client.getCachedMobileOptimizedSource(item.Id)?.url).toBe(first.url);
  });

  it("queries only itemId for mobile optimized lookup", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ available: false }), { status: 404 }));
    vi.stubGlobal("fetch", fetchMock);

    const client = new JellyfinClient("http://127.0.0.1:8096");
    await client.getMobileOptimizedSource(item);

    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("itemId=video-cache-1");
    expect(String(fetchMock.mock.calls[0]?.[0])).not.toContain("sourcePathSha256=");
  });
});
