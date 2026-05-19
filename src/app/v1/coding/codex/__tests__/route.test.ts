/// <reference types="vitest/globals" />

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { POST } from "../route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);

function jsonRequest(body: unknown): Request {
  return new Request("http://localhost/v1/coding/codex", {
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
}

describe("coding Codex route", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("forwards Codex validation requests to Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce({
      headers: new Headers({ "content-type": "application/json" }),
      status: 200,
      statusText: "OK",
      text: async () =>
        JSON.stringify({
          execution_state: "config_blocked",
          status: "config_blocked",
          would_run_task: false,
        }),
    } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>);

    const body = {
      allowed_files: [],
      mode: "readonly",
      target_file: null,
      task: "Summarize Source Proxy safety boundaries.",
    };
    const response = await POST(jsonRequest(body));

    await expect(response.json()).resolves.toEqual({
      execution_state: "config_blocked",
      status: "config_blocked",
      would_run_task: false,
    });
    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/coding/codex",
      expect.objectContaining({
        body: JSON.stringify(body),
        method: "POST",
      }),
    );
  });

  it("returns config-blocked JSON when Source Proxy is unavailable", async () => {
    mockedSourceProxyFetch.mockRejectedValueOnce(new Error("connect ECONNREFUSED"));

    const response = await POST(
      jsonRequest({
        allowed_files: [],
        mode: "readonly",
        target_file: null,
        task: "Summarize Source Proxy safety boundaries.",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      status: "config_blocked",
      execution_state: "config_blocked",
      reason_code: "source_proxy_unavailable",
      would_run_task: false,
      changed_files: [],
      approval_authority: false,
      apply_authority: false,
      commit_authority: false,
      push_authority: false,
    });
    expect(response.status).toBe(200);
  });

  it("stays behind the proxy feature flag", async () => {
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "false");

    const response = await POST(jsonRequest({ mode: "readonly", task: "No-op." }));

    await expect(response.json()).resolves.toEqual({
      error: "SPIRIT_CODING_USE_PROXY is not true",
    });
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });
});
