/// <reference types="vitest/globals" />

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { POST } from "../route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);

describe("long-running approval preview route", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("forwards the persisted preview request without accepting caller issuance", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(new Response(JSON.stringify({ preview: { preview_id: "prv_server", generation: 1 } }), {
      headers: { "content-type": "application/json" }, status: 200,
    }) as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>);

    const response = await POST(
      new Request("http://localhost/v1/tasks/long-running/task-1/approval-preview", {
        body: JSON.stringify({ action: "Live trial coder-001", approved_diff: "diff --git a/a b/a", context_hash: "a".repeat(64), selected_prompt_id: "coder-001", target: "tests/ui-agent-trials/fixtures/dummy-product-site/" }),
        headers: { "content-type": "application/json" }, method: "POST",
      }),
      { params: Promise.resolve({ taskId: "task-1" }) },
    );

    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({ preview: { preview_id: "prv_server", generation: 1 } });
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/tasks/long-running/task-1/approval-preview",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("fails closed when the coding proxy is disabled", async () => {
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "false");
    const response = await POST(new Request("http://localhost", { method: "POST" }), { params: Promise.resolve({ taskId: "task-1" }) });
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });
});
