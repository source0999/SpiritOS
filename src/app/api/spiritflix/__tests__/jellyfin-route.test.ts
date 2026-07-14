import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { clearSpiritFlixSessionsForTest, createOrdinarySession, SPIRITFLIX_SESSION_COOKIE } from "@/lib/spiritflix/server-session";
import { POST } from "../jellyfin/route";

function proxyRequest(body: Record<string, unknown>, cookie?: string) {
  return new NextRequest("https://spirit.test/api/spiritflix/jellyfin", { body: JSON.stringify(body), headers: { "content-type": "application/json", ...(cookie ? { cookie } : {}) }, method: "POST" });
}

describe("/api/spiritflix/jellyfin", () => {
  afterEach(() => { clearSpiritFlixSessionsForTest(); vi.unstubAllGlobals(); });

  it("rejects browser-supplied authorization and server overrides", async () => {
    const response = await POST(proxyRequest({ authorization: "MediaBrowser Token=forged", path: "/System/Info/Public", serverUrl: "https://evil.test" }));
    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ reason_code: "spiritflix_client_authority_forbidden" });
  });

  it("requires an opaque application session for private Jellyfin paths", async () => {
    const response = await POST(proxyRequest({ method: "GET", path: "/Users/__spiritflix_session__/Views" }));
    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ reason_code: "spiritflix_session_missing" });
  });

  it("resolves opaque session identity and authorization only on the server", async () => {
    const authFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ AccessToken: "server-only-token", User: { Id: "jellyfin-user", Name: "ordinary" } }), { status: 200 }));
    vi.stubGlobal("fetch", authFetch);
    const created = await createOrdinarySession({ password: "pass", serverUrl: "http://127.0.0.1:8096", username: "ordinary" });
    if (!created.ok) throw new Error(created.reason);
    const upstreamFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ Items: [] }), { headers: { "Content-Type": "application/json" }, status: 200 }));
    vi.stubGlobal("fetch", upstreamFetch);
    const response = await POST(proxyRequest({ method: "GET", path: "/Users/__spiritflix_session__/Views" }, `${SPIRITFLIX_SESSION_COOKIE}=${created.id}`));
    expect(response.status).toBe(200);
    expect(upstreamFetch).toHaveBeenCalledWith("http://127.0.0.1:8096/Users/jellyfin-user/Views", expect.objectContaining({ headers: expect.objectContaining({ "X-Emby-Authorization": expect.stringContaining("server-only-token") }) }));
    expect(JSON.stringify(await response.json())).not.toContain("server-only-token");
  });

  it("requires trusted origin and the ordinary session CSRF value for mutations", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ AccessToken: "server-only-token", User: { Id: "jellyfin-user", Name: "ordinary" } }), { status: 200 })));
    const created = await createOrdinarySession({ password: "pass", serverUrl: "http://127.0.0.1:8096", username: "ordinary" });
    if (!created.ok) throw new Error(created.reason);
    const response = await POST(new NextRequest("https://spirit.test/api/spiritflix/jellyfin", {
      body: JSON.stringify({ body: { IsFavorite: true }, method: "POST", path: "/Users/__spiritflix_session__/FavoriteItems/item-1" }),
      headers: { "content-type": "application/json", cookie: `${SPIRITFLIX_SESSION_COOKIE}=${created.id}`, host: "spirit.test", origin: "https://spirit.test" },
      method: "POST",
    }));
    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({ reason_code: "spiritflix_mutation_untrusted" });
  });
});
