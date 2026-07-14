import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { clearSpiritFlixSessionsForTest, createOrdinarySession, SPIRITFLIX_SESSION_COOKIE } from "@/lib/spiritflix/server-session";
import { GET as imageGet } from "../jellyfin-image/route";
import { GET as hlsGet } from "../hls/route";
import { GET as streamGet } from "../stream/route";

async function ordinaryCookie() {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ AccessToken: "server-only-token", User: { Id: "jellyfin-user", Name: "ordinary" } }), { status: 200 })));
  const created = await createOrdinarySession({ password: "pass", serverUrl: "http://127.0.0.1:8096", username: "ordinary" });
  if (!created.ok) throw new Error(created.reason);
  return `${SPIRITFLIX_SESSION_COOKIE}=${created.id}`;
}

describe("ordinary SpiritFlix media BFF routes", () => {
  afterEach(() => { clearSpiritFlixSessionsForTest(); vi.unstubAllGlobals(); });

  it("rejects absent sessions and browser authority parameters across media routes", async () => {
    const missing = await streamGet(new NextRequest("https://spirit.test/api/spiritflix/stream?itemId=item-1"));
    expect(missing.status).toBe(401);

    const streamOverride = await streamGet(new NextRequest("https://spirit.test/api/spiritflix/stream?itemId=item-1&token=forged"));
    const imageOverride = await imageGet(new NextRequest("https://spirit.test/api/spiritflix/jellyfin-image?path=%2FItems%2Fitem-1%2FImages%2FPrimary&serverUrl=https%3A%2F%2Fevil.test"));
    const hlsOverride = await hlsGet(new NextRequest("https://spirit.test/api/spiritflix/hls?path=%2FVideos%2Fitem-1%2Fmaster.m3u8&api_key=forged"));
    await expect(streamOverride.json()).resolves.toEqual({ reason_code: "spiritflix_client_authority_forbidden" });
    await expect(imageOverride.json()).resolves.toEqual({ reason_code: "spiritflix_client_authority_forbidden" });
    await expect(hlsOverride.json()).resolves.toEqual({ reason_code: "spiritflix_client_authority_forbidden" });
  });

  it("uses the server-owned session for streams and never reflects its authorization", async () => {
    const cookie = await ordinaryCookie();
    const upstreamFetch = vi.fn().mockResolvedValue(new Response("media", { headers: { "Content-Type": "video/mp4" }, status: 200 }));
    vi.stubGlobal("fetch", upstreamFetch);

    const response = await streamGet(new NextRequest("https://spirit.test/api/spiritflix/stream?itemId=abc-123&audioStreamIndex=2", { headers: { cookie, range: "bytes=0-" } }));
    expect(response.status).toBe(200);
    const [upstreamUrl, upstreamInit] = upstreamFetch.mock.calls[0] as [string, { headers: Record<string, string> }];
    expect(String(upstreamUrl)).toContain("/Videos/abc-123/Stream");
    expect(upstreamInit.headers["X-Emby-Authorization"]).toContain("server-only-token");
    expect(upstreamInit.headers.Range).toBe("bytes=0-");
    expect(await response.text()).toBe("media");
    expect(JSON.stringify([...response.headers])).not.toContain("server-only-token");
  });

  it("rewrites HLS children through the BFF and keeps image identity server-side", async () => {
    const cookie = await ordinaryCookie();
    const upstreamFetch = vi.fn()
      .mockResolvedValueOnce(new Response("#EXTM3U\nsegment-1.ts\n", { headers: { "Content-Type": "application/vnd.apple.mpegurl" }, status: 200 }))
      .mockResolvedValueOnce(new Response("image", { headers: { "Content-Type": "image/jpeg" }, status: 200 }));
    vi.stubGlobal("fetch", upstreamFetch);

    const playlist = await hlsGet(new NextRequest("https://spirit.test/api/spiritflix/hls?path=%2FVideos%2Fitem-1%2Fmaster.m3u8", { headers: { cookie } }));
    expect(await playlist.text()).toContain("/api/spiritflix/hls?path=%2FVideos%2Fitem-1%2Fsegment-1.ts");
    const image = await imageGet(new NextRequest("https://spirit.test/api/spiritflix/jellyfin-image?path=%2FUsers%2F__spiritflix_session__%2FImages%2FPrimary", { headers: { cookie } }));
    expect(image.status).toBe(200);
    expect(upstreamFetch).toHaveBeenLastCalledWith("http://127.0.0.1:8096/Users/jellyfin-user/Images/Primary", expect.objectContaining({ headers: expect.objectContaining({ "X-Emby-Authorization": expect.stringContaining("server-only-token") }) }));
  });
});
