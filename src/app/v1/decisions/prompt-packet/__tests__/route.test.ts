/// <reference types="vitest/globals" />

import { readFile } from "node:fs/promises";

import { sourceProxyFetch, sourceProxyLongJsonFetch } from "@/lib/source-proxy-origin";

import { POST } from "../route";

const fsPromisesMock = vi.hoisted(() => ({
  readFile: vi.fn(),
}));

vi.mock("node:fs/promises", () => ({
  default: {
    readFile: fsPromisesMock.readFile,
  },
  readFile: fsPromisesMock.readFile,
}));

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
  sourceProxyLongJsonFetch: vi.fn(),
}));

const mockedReadFile = vi.mocked(readFile);
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
    mockedReadFile.mockReset();
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
        active_task_id: "task-prompt-4",
        allowed_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
        selected_prompt_id: "coder-004-add-search-filter",
        selected_target: "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        target_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js"],
        trial_prompt_id: "coder-004-add-search-filter",
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
    expect(body.selected_prompt_id).toBe("coder-004-add-search-filter");
    expect(body.selected_prompt_number).toBe(4);
    expect(body.task_id).toBe("task-prompt-4");
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

  it("returns already-satisfied for Prompt 3 when the fixture already renders product cards", async () => {
    mockedReadFile.mockImplementation(async (filePath) => {
      const normalized = String(filePath).replace(/\\/g, "/");
      if (normalized.endsWith("/index.html")) {
        return '<!doctype html><html><body><main id="product-list"></main><script type="module" src="src/main.js"></script></body></html>';
      }
      if (normalized.endsWith("/src/main.js")) {
        return [
          "import products from './products.js';",
          "const list = document.querySelector('#product-list');",
          "products.forEach((product) => {",
          "  const card = document.createElement('article');",
          "  card.className = 'product-card';",
          "  card.innerHTML = `<h2>${product.name}</h2><p class=\"price\">${product.price}</p><p class=\"category\">${product.category}</p><p>${product.description}</p>`;",
          "  list.appendChild(card);",
          "});",
        ].join("\n");
      }
      if (normalized.endsWith("/src/products.js")) {
        return [
          "export default [",
          "  { id: 'one', name: 'One', price: 1, category: 'A', description: 'First' },",
          "  { id: 'two', name: 'Two', price: 2, category: 'B', description: 'Second' },",
          "  { id: 'three', name: 'Three', price: 3, category: 'C', description: 'Third' },",
          "  { id: 'four', name: 'Four', price: 4, category: 'D', description: 'Fourth' },",
          "  { id: 'five', name: 'Five', price: 5, category: 'E', description: 'Fifth' },",
          "  { id: 'six', name: 'Six', price: 6, category: 'F', description: 'Sixth' },",
          "];",
        ].join("\n");
      }
      if (normalized.endsWith("/src/styles.css")) {
        return ".product-card { display: grid; }";
      }
      throw new Error(`Unexpected fixture read: ${normalized}`);
    });

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
    expect(mockedSourceProxyLongJsonFetch).not.toHaveBeenCalled();
    const body = await response.json();
    expect(body.status).toBe("already_satisfied");
    expect(body.reason_code).toBe("coder_no_changes_needed");
    expect(body.proposed_diff).toBe("");
    expect(body.task_id).toBe("task-prompt-3-context");
    expect(body.selected_prompt_id).toBe("coder-003-render-product-cards");
    expect(body.diff_source).toBe("already_satisfied_existing_dummy_product_cards");
    expect(body.selected_target).toBe("tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js");
    expect(body.checks_run).toContain("existing Prompt 3 storefront render validation");
    expect(body.coder_diagnostics).toMatchObject({
      existing_product_cards_present: true,
      existing_product_cards_validation: {
        ok: true,
        storefront_probe: {
          preview_behavior_status: "PASS_STOREFRONT_RENDERED",
          product_count: 6,
        },
      },
    });
  });
});
