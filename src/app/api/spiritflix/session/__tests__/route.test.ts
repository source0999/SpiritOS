/// <reference types="vitest/globals" />

import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { clearSpiritFlixSessionsForTest } from "@/lib/spiritflix/server-session";
import { DELETE, GET, POST } from "../route";

const headers = { "content-type": "application/json", host: "spirit.test", origin: "https://spirit.test" };

describe("ordinary SpiritFlix session route", () => {
  afterEach(() => { clearSpiritFlixSessionsForTest(); vi.unstubAllGlobals(); });

  it("creates an opaque HTTP-only server session without returning a Jellyfin token", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ AccessToken: "server-only-token", User: { Id: "jellyfin-user", Name: "ordinary" } }), { status: 200 })));
    const response = await POST(new NextRequest("https://spirit.test/api/spiritflix/session", { body: JSON.stringify({ password: "pass", serverUrl: "http://127.0.0.1:8096", username: "ordinary" }), headers, method: "POST" }));
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ authenticated: true, session: expect.objectContaining({ userId: "__spiritflix_session__", username: "ordinary" }) });
    expect(response.headers.get("set-cookie")).toContain("HttpOnly");
    expect(response.headers.get("set-cookie")).toContain("SameSite=strict");
    expect(response.headers.get("set-cookie")).not.toContain("server-only-token");
  });

  it("fails closed for an untrusted mutation origin", async () => {
    const response = await POST(new NextRequest("https://spirit.test/api/spiritflix/session", { body: "{}", headers: { ...headers, origin: "https://evil.test" }, method: "POST" }));
    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({ reason_code: "spiritflix_origin_untrusted" });
  });

  it("revokes the session and rejects subsequent use", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ AccessToken: "server-only-token", User: { Id: "jellyfin-user", Name: "ordinary" } }), { status: 200 })));
    const created = await POST(new NextRequest("https://spirit.test/api/spiritflix/session", { body: JSON.stringify({ password: "pass", serverUrl: "http://127.0.0.1:8096", username: "ordinary" }), headers, method: "POST" }));
    const cookie = created.headers.get("set-cookie")!.split(";")[0];
    const status = await GET(new NextRequest("https://spirit.test/api/spiritflix/session", { headers: { cookie }, method: "GET" }));
    const csrf = ((await status.json()) as { session: { csrf: string } }).session.csrf;
    const revoked = await DELETE(new NextRequest("https://spirit.test/api/spiritflix/session", { headers: { cookie, host: "spirit.test", origin: "https://spirit.test", "x-spiritflix-csrf": csrf }, method: "DELETE" }));
    expect(revoked.status).toBe(200);
    const after = await GET(new NextRequest("https://spirit.test/api/spiritflix/session", { headers: { cookie }, method: "GET" }));
    expect(after.status).toBe(401);
  });
});
