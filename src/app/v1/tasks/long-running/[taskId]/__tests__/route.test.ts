/// <reference types="vitest/globals" />

import { sourceProxyLongJsonFetch } from "@/lib/source-proxy-origin";

import { GET, POST } from "../route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyLongJsonFetch: vi.fn(),
}));

const mockedSourceProxyLongJsonFetch = vi.mocked(sourceProxyLongJsonFetch);

describe("long-running task route", () => {
  beforeEach(() => {
    mockedSourceProxyLongJsonFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("uses the long-lived JSON dispatcher for queued task status readback", async () => {
    mockedSourceProxyLongJsonFetch.mockResolvedValueOnce(new Response(JSON.stringify({ task: { id: "task-1" } }), {
      headers: { "content-type": "application/json" }, status: 200,
    }) as unknown as Awaited<ReturnType<typeof sourceProxyLongJsonFetch>>);

    const response = await GET(new Request("http://localhost/v1/tasks/long-running/task-1"), {
      params: Promise.resolve({ taskId: "task-1" }),
    });

    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({ task: { id: "task-1" } });
    expect(mockedSourceProxyLongJsonFetch).toHaveBeenCalledWith(
      "/v1/tasks/long-running/task-1",
      { method: "GET" },
    );
  });

  it("uses the same long-lived dispatcher for post-apply verification", async () => {
    mockedSourceProxyLongJsonFetch.mockResolvedValueOnce(new Response(JSON.stringify({ status: "verified" }), {
      headers: { "content-type": "application/json" }, status: 200,
    }) as unknown as Awaited<ReturnType<typeof sourceProxyLongJsonFetch>>);

    const response = await POST(
      new Request("http://localhost/v1/tasks/long-running/task-1", {
        body: JSON.stringify({ confirm_expected_change_present: true }),
        headers: { "content-type": "application/json" },
        method: "POST",
      }),
      { params: Promise.resolve({ taskId: "task-1" }) },
    );

    expect(response.status).toBe(200);
    expect(mockedSourceProxyLongJsonFetch).toHaveBeenCalledWith(
      "/v1/tasks/long-running/task-1/verification",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
