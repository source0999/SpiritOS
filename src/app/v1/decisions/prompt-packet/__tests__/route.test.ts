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

function proxyBodyReadFailure(error: Error) {
  return {
    headers: new Headers({ "content-type": "application/json" }),
    ok: true,
    status: 200,
    statusText: "OK",
    text: async () => {
      throw error;
    },
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

  it("returns a structured blocked timeout packet when the long Source Proxy body read fails", async () => {
    mockedSourceProxyLongJsonFetch.mockResolvedValueOnce(
      proxyBodyReadFailure(new TypeError("fetch failed")),
    );

    const response = await POST(
      jsonRequest({
        active_task_id: "task-prompt-3",
        allowed_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
        selected_prompt_id: "coder-003-render-product-cards",
        selected_target: "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
        target_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/index.html"],
        trial_prompt_id: "coder-003-render-product-cards",
        wants_implementation: true,
      }),
    );

    const body = await response.json();
    expect(response.status).toBe(504);
    expect(body.status).toBe("blocked");
    expect(body.prompt_packet_status).toBe("blocked");
    expect(body.terminal_verdict).toBe("BLOCKED_TIMEOUT");
    expect(body.reason_code).toBe("source_proxy_prompt_packet_body_read_failed");
    expect(body.proposed_diff).toBe("");
    expect(body.generation_source).toBe("none");
    expect(body.scaffold_used).toBe(false);
    expect(body.fallback_used).toBe(false);
    expect(body.selected_prompt_id).toBe("coder-003-render-product-cards");
    expect(body.selected_prompt_number).toBe(3);
    expect(body.task_id).toBe("task-prompt-3");
    expect(body.selected_target).toBe("tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js");
    expect(body.allowed_files).toEqual(["tests/ui-agent-trials/fixtures/dummy-product-site/**"]);
    expect(body.coder_diagnostics).toEqual(
      expect.objectContaining({
        error_message: "fetch failed",
        reason_code: "source_proxy_prompt_packet_body_read_failed",
        source_proxy_status: 200,
        timeout_stage: "source_proxy_prompt_packet_body_read",
      }),
    );
  });

  it("enriches Prompt 3 requests with fixture render context before proxying", async () => {
    mockedSourceProxyLongJsonFetch.mockResolvedValueOnce(
      proxyJson({
        proposed_diff: "",
        reason_code: "coder_packet_missing_context",
        status: "needs_context",
      }),
    );

    const response = await POST(
      jsonRequest({
        active_task_id: "task-prompt-3-context",
        allowed_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
        dummy_coder_10_packet: {
          expected_result_state: "PASS_DUMMY_UI_CHANGE",
        },
        selected_prompt_id: "coder-003-render-product-cards",
        selected_target: "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
        target_file: "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
        task: "make the dummy LumaCart page actually show the products as cards.",
        trial_mode: "live_apply",
        trial_prompt_id: "coder-003-render-product-cards",
        wants_implementation: true,
      }),
    );

    expect(response.status).toBe(200);
    const [, init] = mockedSourceProxyLongJsonFetch.mock.calls[0];
    const body = JSON.parse(String(init?.body));
    expect(body.selected_target).toBe("tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js");
    expect(body.target_file).toBe("tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js");
    expect(body.task).toContain("Prompt 3 fixture context:");
    expect(body.task).toContain("Option A is mandatory");
    expect(body.task).toContain('<script type="module" src="src/main.js"></script>');
    expect(body.task).toContain("import products from './products.js';");
    expect(body.task).toContain("Do not duplicate the product array or hardcode product cards in index.html.");
    expect(body.task).toContain("Do not use dynamic import().");
    expect(body.dummy_coder_10_packet.prompt_3_contract).toMatchObject({
      data_source: "tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      data_source_read_only: true,
      expected_product_count: expect.any(Number),
      required_index_target: "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
      required_render_target: "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
    });
  });
});
