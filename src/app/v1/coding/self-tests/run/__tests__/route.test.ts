/// <reference types="vitest/globals" />

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { POST } from "../route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);

function jsonRequest(body: unknown): Request {
  return new Request("http://localhost/v1/coding/self-tests/run", {
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
}

describe("coding self-tests route", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("forwards dry-run self-test requests to Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce({
      headers: new Headers({ "content-type": "application/json" }),
      status: 200,
      statusText: "OK",
      text: async () =>
        JSON.stringify({
          applied_anything: false,
          summary: { failed: 0, passed: 3, skipped: 0 },
        }),
    } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>);

    const body = {
      case_ids: ["manual-check-7", "manual-check-8", "manual-check-9"],
      mode: "dry_run",
      suite: "phase-4e-safety-seed",
    };
    const response = await POST(jsonRequest(body));

    await expect(response.json()).resolves.toEqual({
      applied_anything: false,
      summary: { failed: 0, passed: 3, skipped: 0 },
    });
    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/coding/self-tests/run",
      expect.objectContaining({
        body: JSON.stringify(body),
        method: "POST",
      }),
    );
  });

  it("forwards runner profile requests to Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce({
      headers: new Headers({ "content-type": "application/json" }),
      status: 200,
      statusText: "OK",
      text: async () =>
        JSON.stringify({
          applied_anything: false,
          mode: "dry_run",
          profile: "scout-smoke",
          recommendation: "ready for next increment",
          result: "pass",
        }),
    } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>);

    const body = {
      mode: "dry_run",
      profile: "scout-smoke",
    };
    const response = await POST(jsonRequest(body));

    await expect(response.json()).resolves.toEqual({
      applied_anything: false,
      mode: "dry_run",
      profile: "scout-smoke",
      recommendation: "ready for next increment",
      result: "pass",
    });
    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/coding/self-tests/run",
      expect.objectContaining({
        body: JSON.stringify(body),
        method: "POST",
      }),
    );
  });

  it("stays behind the proxy feature flag", async () => {
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "false");

    const response = await POST(jsonRequest({ mode: "dry_run" }));

    await expect(response.json()).resolves.toEqual({
      error: "SPIRIT_CODING_USE_PROXY is not true",
    });
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });
});
