/// <reference types="vitest/globals" />
import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { POST } from "../route";
import { clearE2ESessionsForTest, createE2ESession } from "@/lib/spiritflix/e2e-session";

describe("SpiritFlix E2E session route", () => {
  afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); clearE2ESessionsForTest(); });

  it("fails closed when explicit integration mode is absent", async () => {
    const response = await POST(new NextRequest("https://example.test/api/spiritflix/e2e/session", { method: "POST" }));
    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ ready: false, reason: "e2e_session_mode_disabled" });
    expect(response.headers.get("set-cookie")).toBeNull();
  });

  it("does not create a cookie when the dedicated secret is missing", async () => {
    vi.stubEnv("SPIRITFLIX_E2E_SESSION_ENABLED", "true");
    vi.stubEnv("SPIRITFLIX_E2E_USERNAME", "");
    vi.stubEnv("SPIRITFLIX_E2E_PASSWORD", "");
    vi.stubEnv("SPIRITFLIX_E2E_SECRET_FILE", "/tmp/spiritos-e2e-secret-missing");
    const response = await POST(new NextRequest("https://example.test/api/spiritflix/e2e/session", { method: "POST" }));
    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ ready: false, reason: "dedicated_e2e_secret_not_configured" });
    expect(response.headers.get("set-cookie")).toBeNull();
  });

  it("rejects an authenticated identity without assigned libraries", async () => {
    vi.stubEnv("SPIRITFLIX_E2E_SESSION_ENABLED", "true");
    vi.stubEnv("SPIRITFLIX_E2E_USERNAME", "spiritos-e2e");
    vi.stubEnv("SPIRITFLIX_E2E_PASSWORD", "not-a-real-secret");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ AccessToken: "server-only-token", User: { Id: "e2e-user", Policy: { IsAdministrator: false, EnableContentDeletion: false, EnableAllFolders: false, EnabledFolders: [] } } }), { status: 200 })));
    await expect(createE2ESession()).resolves.toEqual({ ok: false, reason: "dedicated_e2e_identity_no_library_access" });
  });
});
