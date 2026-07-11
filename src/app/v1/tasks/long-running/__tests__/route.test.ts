/// <reference types="vitest/globals" />

import { sourceProxyFastJsonFetch } from "@/lib/source-proxy-origin";

import { POST } from "../route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFastJsonFetch: vi.fn(),
  sourceProxyFetch: vi.fn(),
}));

const mockedSourceProxyFastJsonFetch = vi.mocked(sourceProxyFastJsonFetch);

function jsonRequest(body: unknown): Request {
  return new Request("http://localhost/v1/tasks/long-running", {
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
}

describe("long-running task route", () => {
  beforeEach(() => {
    mockedSourceProxyFastJsonFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns task creation diagnostics when Source Proxy does not return a task id", async () => {
    mockedSourceProxyFastJsonFetch.mockRejectedValueOnce(new DOMException("candidate timeout", "AbortError"));

    const response = await POST(jsonRequest({ description: "Target file: src/demo.ts\nUpdate it." }));
    const payload = await response.json();

    expect(response.status).toBe(504);
    expect(payload).toMatchObject({
      reason_code: "selected_prompt_task_create_timeout",
      selected_prompt_task_id: "missing: task_create_proxy_failed_before_task_id",
      task_creation_status: "timeout_before_task_id",
      task_creation_timeout_stage: "source_proxy_candidate_fetch",
      task_creation_last_checkpoint: "request_body_read",
      task_creation_blocking_subsystem: "source_proxy_long_running_task_route",
      truth_status: "BLOCKED_SAFE",
    });
    expect(payload.task_creation_elapsed_ms).toEqual(expect.any(Number));
    expect(payload.diagnostic_envelope).toMatchObject({
      reason_code: "selected_prompt_task_create_timeout",
      task_creation_status: "timeout_before_task_id",
    });
  });

  it("uses fast JSON fallback for task creation instead of the generic proxy fetch", async () => {
    mockedSourceProxyFastJsonFetch.mockResolvedValueOnce({
      headers: new Headers({ "content-type": "application/json" }),
      status: 200,
      statusText: "OK",
      text: async () =>
        JSON.stringify({
          task: { id: "task-fast-create" },
          task_creation_status: "persisted_task_id",
        }),
    } as unknown as Awaited<ReturnType<typeof sourceProxyFastJsonFetch>>);

    const response = await POST(jsonRequest({ description: "Target file: src/demo.ts\nUpdate it." }));
    const payload = await response.json();

    expect(response.status).toBe(200);
    expect(payload.task.id).toBe("task-fast-create");
    expect(mockedSourceProxyFastJsonFetch).toHaveBeenCalledWith(
      "/v1/tasks/long-running",
      expect.objectContaining({ method: "POST" }),
      { perCandidateTimeoutMs: 5000 },
    );
  });
});
