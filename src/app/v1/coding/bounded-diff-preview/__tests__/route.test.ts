/// <reference types="vitest/globals" />

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { POST } from "../route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);

function jsonRequest(body: unknown): Request {
  return new Request("http://localhost/v1/coding/bounded-diff-preview", {
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
}

describe("coding bounded diff preview route", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("forwards bounded preview requests to Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce({
      headers: new Headers({ "content-type": "application/json" }),
      status: 200,
      statusText: "OK",
      text: async () =>
        JSON.stringify({
          task_id: "CG-001",
          changed_files: ["src/lib/coding/workflow-progress-copy.ts"],
          diff_present: true,
          preview_only: true,
          apply_authority: false,
          commit_authority: false,
          push_authority: false,
          provider_call_made: false,
          queue_worker_started: false,
          shell_command_started: false,
          hidden_execution_started: false,
          receipt_class: "productive_preview",
          reason_code: "preview_ready",
        }),
    } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>);

    const body = {
      allowed_files: ["src/lib/coding/workflow-progress-copy.ts"],
      micro_batch: "run_300_cg001_cg005",
      prompt: "tighten one preview-only helper phrase for clearer coding progress evidence",
      target_files: ["src/lib/coding/workflow-progress-copy.ts"],
      task_id: "CG-001",
    };
    const response = await POST(jsonRequest(body));

    await expect(response.json()).resolves.toMatchObject({
      task_id: "CG-001",
      diff_present: true,
      preview_only: true,
      apply_authority: false,
      commit_authority: false,
      push_authority: false,
      provider_call_made: false,
      queue_worker_started: false,
      shell_command_started: false,
      hidden_execution_started: false,
      receipt_class: "productive_preview",
      reason_code: "preview_ready",
    });
    expect(response.status).toBe(200);
    expect(response.headers.get("x-spiritos-plan4-route-status")).toBe("dormant");
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/coding/bounded-diff-preview",
      expect.objectContaining({
        body: JSON.stringify(body),
        method: "POST",
      }),
    );
  });

  it("returns a preview-only route-gap packet when Source Proxy is unavailable", async () => {
    mockedSourceProxyFetch.mockRejectedValueOnce(new Error("connect ECONNREFUSED"));

    const response = await POST(
      jsonRequest({
        allowed_files: ["src/lib/coding/workflow-progress-copy.ts"],
        prompt: "tighten one preview-only helper phrase for clearer coding progress evidence",
        target_files: ["src/lib/coding/workflow-progress-copy.ts"],
        task_id: "CG-001",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      changed_files: [],
      diff_present: false,
      preview_only: true,
      apply_authority: false,
      commit_authority: false,
      push_authority: false,
      provider_call_made: false,
      queue_worker_started: false,
      shell_command_started: false,
      hidden_execution_started: false,
      reason_code: "source_proxy_unavailable",
      receipt_class: "route_gap_not_ready",
      plan4_route_status: "dormant",
    });
    expect(response.status).toBe(200);
    expect(response.headers.get("x-spiritos-plan4-route-status")).toBe("dormant");
  });

  it("stays behind the proxy feature flag", async () => {
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "false");

    const response = await POST(jsonRequest({ task_id: "CG-001" }));

    await expect(response.json()).resolves.toEqual({
      error: "SPIRIT_CODING_USE_PROXY is not true",
      plan4_route_status: "dormant",
    });
    expect(response.status).toBe(409);
    expect(response.headers.get("x-spiritos-plan4-route-status")).toBe("dormant");
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });
});
