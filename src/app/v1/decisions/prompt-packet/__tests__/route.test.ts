/// <reference types="vitest/globals" />

import { sourceProxyFetch, sourceProxyLongJsonFetch } from "@/lib/source-proxy-origin";

import { POST } from "../route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
  sourceProxyLongJsonFetch: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);
const mockedSourceProxyLongJsonFetch = vi.mocked(sourceProxyLongJsonFetch);

function jsonRequest(body: unknown): Request {
  return new Request("http://localhost/v1/decisions/prompt-packet", {
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
}

function proxyJson(body: unknown) {
  return {
    headers: new Headers({ "content-type": "application/json" }),
    ok: true,
    status: 200,
    statusText: "OK",
    text: async () => JSON.stringify(body),
  } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>;
}

describe("prompt-packet route", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
    mockedSourceProxyLongJsonFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns the narrow docs-only preview directly before waiting on Source Proxy", async () => {
    mockedSourceProxyLongJsonFetch.mockResolvedValueOnce(
      proxyJson({
        proposed_diff:
          "diff --git a/docs/proxy-test-runner-plan.md b/docs/proxy-test-runner-plan.md\n+Direct preview tests should keep unique expected text for stable coverage.",
        reason_code: "docs_only_bff_direct_preview",
        status: "preview_ready",
        target: "docs/proxy-test-runner-plan.md",
        task_id: "task-123",
      }),
    );

    const response = await POST(
      jsonRequest({
        active_task_id: "task-123",
        allowed_files: ["docs/proxy-test-runner-plan.md"],
        target_files: ["docs/proxy-test-runner-plan.md"],
        task:
          "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence explaining that direct preview tests should keep unique expected text for stable coverage.",
        wants_implementation: true,
      }),
    );

    const body = await response.json();
    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith("/v1/self/status", { method: "GET" });
    expect(mockedSourceProxyLongJsonFetch).toHaveBeenCalled();
    expect(body.status).toBe("preview_ready");
    expect(body.reason_code).toBe("docs_only_bff_direct_preview");
    expect(body.task_id).toBe("task-123");
    expect(body.target).toBe("docs/proxy-test-runner-plan.md");
    expect(body.proposed_diff).toContain(
      "diff --git a/docs/proxy-test-runner-plan.md b/docs/proxy-test-runner-plan.md",
    );
    expect(body.proposed_diff).toContain(
      "+Direct preview tests should keep unique expected text for stable coverage.",
    );
  });

  it("returns direct docs-only preview for the safe trial even without a task id", async () => {
    mockedSourceProxyLongJsonFetch.mockResolvedValueOnce(
      proxyJson({
        proposed_diff:
          "diff --git a/docs/proxy-test-runner-plan.md b/docs/proxy-test-runner-plan.md\n+Direct preview without task id should keep unique expected text.",
        reason_code: "docs_only_bff_direct_preview",
        status: "preview_ready",
        target: "docs/proxy-test-runner-plan.md",
      }),
    );

    const response = await POST(
      jsonRequest({
        allowed_files: ["docs/proxy-test-runner-plan.md"],
        target_files: ["docs/proxy-test-runner-plan.md"],
        task:
          "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence explaining that direct preview without task id should keep unique expected text.",
        wants_implementation: true,
      }),
    );

    const body = await response.json();
    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith("/v1/self/status", { method: "GET" });
    expect(mockedSourceProxyLongJsonFetch).toHaveBeenCalled();
    expect(body.status).toBe("preview_ready");
    expect(body.reason_code).toBe("docs_only_bff_direct_preview");
    expect(body.target).toBe("docs/proxy-test-runner-plan.md");
    expect(body.proposed_diff).toContain(
      "diff --git a/docs/proxy-test-runner-plan.md b/docs/proxy-test-runner-plan.md",
    );
    expect(body.proposed_diff).toContain(
      "+Direct preview without task id should keep unique expected text.",
    );
  });

  it("returns already-satisfied when the requested docs sentence already exists", async () => {
    mockedSourceProxyLongJsonFetch.mockResolvedValueOnce(
      proxyJson({
        already_satisfied: true,
        alreadySatisfied: true,
        proposed_diff: "",
        reason_code: "coder_no_changes_needed",
        status: "already_satisfied",
        target: "docs/proxy-test-runner-plan.md",
        task_id: "task-123",
      }),
    );

    const response = await POST(
      jsonRequest({
        active_task_id: "task-123",
        allowed_files: ["docs/proxy-test-runner-plan.md"],
        target_files: ["docs/proxy-test-runner-plan.md"],
        task:
          "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence explaining that the proxy test runner turns proxy safety checks into a repeatable Codex-run lane.",
        wants_implementation: true,
      }),
    );

    const body = await response.json();
    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith("/v1/self/status", { method: "GET" });
    expect(mockedSourceProxyLongJsonFetch).toHaveBeenCalled();
    expect(body.status).toBe("already_satisfied");
    expect(body.reason_code).toBe("coder_no_changes_needed");
    expect(body.already_satisfied).toBe(true);
    expect(body.alreadySatisfied).toBe(true);
    expect(body.proposed_diff).toBe("");
    expect(body.task_id).toBe("task-123");
    expect(body.target).toBe("docs/proxy-test-runner-plan.md");
  });

  it("does not fallback when the docs target is not explicitly allowed", async () => {
    mockedSourceProxyLongJsonFetch.mockResolvedValueOnce(
      proxyJson({
        proposed_diff: "",
        reason_code: "coder_packet_missing_context",
        status: "needs_context",
      }),
    );

    const response = await POST(
      jsonRequest({
        allowed_files: ["docs/other.md"],
        target_files: ["docs/proxy-test-runner-plan.md"],
        task:
          "Target file: docs/proxy-test-runner-plan.md. Add one short sentence explaining that verification receipts should include changed files, commands run, and pass/fail results.",
        wants_implementation: true,
      }),
    );

    const body = await response.json();
    expect(body.status).toBe("needs_context");
    expect(body.reason_code).toBe("coder_packet_missing_context");
    expect(body.proposed_diff).toBe("");
    expect(mockedSourceProxyLongJsonFetch).toHaveBeenCalledWith(
      "/v1/decisions/prompt-packet",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
