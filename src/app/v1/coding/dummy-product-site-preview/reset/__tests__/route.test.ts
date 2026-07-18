/// <reference types="vitest/globals" />

import { sourceProxyFetch } from "@/lib/source-proxy-origin";
import { auditOperatorAction, createOperatorApprovalAssertion, requireOperatorSession } from "@/lib/coding/operator-approval-session";

import { POST } from "../route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
}));
vi.mock("@/lib/coding/operator-approval-session", () => ({
  auditOperatorAction: vi.fn(),
  createOperatorApprovalAssertion: vi.fn(),
  requireOperatorSession: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);
const mockedAuditOperatorAction = vi.mocked(auditOperatorAction);
const mockedCreateOperatorApprovalAssertion = vi.mocked(createOperatorApprovalAssertion);
const mockedRequireOperatorSession = vi.mocked(requireOperatorSession);

describe("dummy product site preview reset route", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
    mockedAuditOperatorAction.mockReset().mockResolvedValue(undefined);
    mockedCreateOperatorApprovalAssertion.mockReset().mockResolvedValue("signed-reset-assertion");
    mockedRequireOperatorSession.mockReset().mockResolvedValue({ operator: "spiritos-local-operator", role: "approval-issuer" } as Awaited<ReturnType<typeof requireOperatorSession>>);
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("forwards the verified reset receipt from Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce({
      headers: new Headers({ "content-type": "application/json" }),
      status: 200,
      statusText: "OK",
      text: async () =>
        JSON.stringify({
          reset_verified: true,
          fixture_root: "tests/ui-agent-trials/fixtures/dummy-product-site/",
          existed: true,
          removed_paths: ["tests/ui-agent-trials/fixtures/dummy-product-site/"],
          clean_verified: true,
          reset_receipt_id: "dummy-product-site-reset-20260711T120000000000Z-test",
        }),
    } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>);

    const request = new Request("http://localhost/v1/coding/dummy-product-site-preview/reset", {
      body: JSON.stringify({ target_plugin: { id: "lumacart" } }),
      method: "POST",
    });
    const response = await POST(request);

    await expect(response.json()).resolves.toEqual({
      reset_verified: true,
      fixture_root: "tests/ui-agent-trials/fixtures/dummy-product-site/",
      existed: true,
      removed_paths: ["tests/ui-agent-trials/fixtures/dummy-product-site/"],
      clean_verified: true,
      reset_receipt_id: "dummy-product-site-reset-20260711T120000000000Z-test",
    });
    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/coding/dummy-product-site/reset",
      {
        body: JSON.stringify({ target_plugin: { id: "lumacart" } }),
        headers: {
          "content-type": "application/json",
          "x-spiritos-operator-assertion": "signed-reset-assertion",
        },
        method: "POST",
      },
    );
    expect(mockedAuditOperatorAction).toHaveBeenCalledWith(
      expect.objectContaining({ role: "approval-issuer" }),
      "approve",
      "dummy-product-site-reset",
    );
  });

  it("preserves a Source Proxy reset failure", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce({
      headers: new Headers({ "content-type": "application/json" }),
      status: 409,
      statusText: "Conflict",
      text: async () => JSON.stringify({ detail: { reason_code: "unsafe_reset_target" } }),
    } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>);

    const response = await POST(new Request("http://localhost/reset", { method: "POST" }));

    await expect(response.json()).resolves.toEqual({
      detail: { reason_code: "unsafe_reset_target" },
    });
    expect(response.status).toBe(409);
  });

  it("reports a Source Proxy connection failure", async () => {
    mockedSourceProxyFetch.mockRejectedValueOnce(new Error("connect ECONNREFUSED 127.0.0.1:8787"));

    const response = await POST(new Request("http://localhost/reset", { method: "POST" }));

    await expect(response.json()).resolves.toEqual({
      error: "Source Proxy dummy product site reset is unavailable",
      reason_code: "source_proxy_unavailable",
      detail: "connect ECONNREFUSED 127.0.0.1:8787",
    });
    expect(response.status).toBe(502);
  });

  it("stays behind the proxy feature flag", async () => {
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "false");

    const response = await POST(new Request("http://localhost/reset", { method: "POST" }));

    await expect(response.json()).resolves.toEqual({
      error: "SPIRIT_CODING_USE_PROXY is not true",
      reason_code: "coding_proxy_disabled",
    });
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("rejects reset without a live operator session", async () => {
    mockedRequireOperatorSession.mockRejectedValueOnce(new Error("operator_session_missing"));

    const response = await POST(new Request("http://localhost/reset", { method: "POST" }));

    await expect(response.json()).resolves.toEqual({
      error: "Authenticated dummy product site reset is forbidden",
      reason_code: "operator_session_missing",
    });
    expect(response.status).toBe(403);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });
});
