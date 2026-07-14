import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { chmod, mkdtemp, rm } from "node:fs/promises";
import path from "node:path";

const originalEnvironment = { ...process.env };
const origin = "https://operator.spirit.test";
let stateDirectory = "";

function request(headers: Record<string, string> = {}) {
  return new Request(`${origin}/v1/operator/session`, { headers: { origin, host: "operator.spirit.test", ...headers } });
}

describe("operator approval session", () => {
  beforeEach(async () => {
    vi.resetModules();
    vi.useRealTimers();
    process.env.SPIRITOS_OPERATOR_E2E_MODE = "true";
    process.env.SPIRITOS_OPERATOR_E2E_SECRET = "operator-session-test-credential";
    process.env.SPIRITOS_OPERATOR_ALLOWED_ORIGINS = origin;
    stateDirectory = await mkdtemp("/tmp/spiritos-operator-session-");
    await chmod(stateDirectory, 0o700);
    process.env.SPIRITOS_OPERATOR_E2E_STATE_PATH = path.join(stateDirectory, "state.json");
  });

  afterEach(async () => {
    vi.useRealTimers();
    await rm(stateDirectory, { force: true, recursive: true });
    process.env = { ...originalEnvironment };
  });

  it("requires a trusted origin, cookie, CSRF, and unrevoked unexpired session", async () => {
    const authority = await import("@/lib/coding/operator-approval-session");
    const created = await authority.createOperatorSession(request(), "operator-session-test-credential");
    const authenticated = request({ cookie: `${authority.operatorCookieName()}=${created.id}`, "x-spiritos-csrf": created.csrf });

    await expect(authority.requireOperatorSession(authenticated)).resolves.toMatchObject({ operator: "spiritos-local-operator", role: "approval-issuer" });
    await expect(authority.requireOperatorSession(request({ cookie: `${authority.operatorCookieName()}=${created.id}` }))).rejects.toThrow("operator_csrf_invalid");
    await authority.revokeOperatorSession(await authority.requireOperatorSession(authenticated));
    await expect(authority.requireOperatorSession(authenticated)).rejects.toThrow("operator_session_revoked");
  });

  it("rejects untrusted origins and expired sessions", async () => {
    const authority = await import("@/lib/coding/operator-approval-session");
    await expect(authority.createOperatorSession(new Request("https://evil.example/v1", { headers: { origin: "https://evil.example", host: "evil.example" } }), "operator-session-test-credential")).rejects.toThrow("operator_origin_untrusted");
    const created = await authority.createOperatorSession(request(), "operator-session-test-credential");
    vi.useFakeTimers();
    vi.setSystemTime(new Date(Date.parse(created.expires_at) + 1));
    await expect(authority.requireOperatorSession(request({ cookie: `${authority.operatorCookieName()}=${created.id}`, "x-spiritos-csrf": created.csrf }))).rejects.toThrow("operator_session_expired");
  });
});
