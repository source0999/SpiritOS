import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { POST } from "../jellyfin/route";

function proxyRequest(body: Record<string, unknown>) {
  return new NextRequest("http://localhost/api/spiritflix/jellyfin", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

describe("/api/spiritflix/jellyfin", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("proxies allowed Jellyfin 8096 hosts through the local HTTP service", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ServerName: "Jellyfin" }), {
      headers: { "Content-Type": "application/json" },
      status: 200,
    }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(proxyRequest({
      serverUrl: "https://100.111.32.31:8096",
      path: "/System/Info/Public",
      method: "GET",
    }));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ServerName: "Jellyfin" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8096/System/Info/Public",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("returns a gateway timeout instead of hanging when Jellyfin stalls", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
        }),
      ),
    );

    const responsePromise = POST(proxyRequest({
      serverUrl: "http://127.0.0.1:8096",
      path: "/System/Info/Public",
      method: "GET",
    }));
    await vi.advanceTimersByTimeAsync(8000);
    const response = await responsePromise;

    expect(response.status).toBe(504);
    expect(await response.json()).toEqual({ error: "Jellyfin request timed out." });
  });
});
