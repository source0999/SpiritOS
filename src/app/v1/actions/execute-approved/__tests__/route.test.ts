/// <reference types="vitest/globals" />

import { execFile } from "node:child_process";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";
import { patchCodingRun, upsertCodingRunRow } from "@/lib/coding/durable-run-store";

import {
  isSelectedDummyCoderApply,
  selectedDummyProductsReplacementFromDiff,
  selectedPrompt3DiffViolations,
  POST,
} from "../route";

vi.mock("node:child_process", async (importOriginal) => {
  const actual = await importOriginal<typeof import("node:child_process")>();
  const execFileMock = vi.fn();
  return {
    ...actual,
    default: { ...actual, execFile: execFileMock },
    execFile: execFileMock,
  };
});
vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
}));
vi.mock("@/lib/coding/durable-run-store", () => ({
  patchCodingRun: vi.fn(),
  upsertCodingRunRow: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);
const mockedPatchCodingRun = vi.mocked(patchCodingRun);
const mockedUpsertCodingRunRow = vi.mocked(upsertCodingRunRow);
const mockedExecFile = vi.mocked(execFile);

function jsonRequest(body: unknown): Request {
  return new Request("http://localhost/v1/actions/execute-approved", {
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
}

function executeApprovedContractPayload(overrides: Record<string, unknown> = {}) {
  return {
    execution: {
      invocation_event_id: "invoke-123",
      task_id: "task-123",
      trace_id: "trace-123",
    },
    task: {
      causal_trace: {
        consumer_event_id: "consume-123",
        consumer_subsystem: "long_running_status_observer",
        invocation_event_id: "invoke-123",
        trace_id: "trace-123",
      },
      id: "task-123",
    },
    tool: "long_running_task_tracker",
    ...overrides,
  };
}

describe("execute-approved route", () => {
  beforeEach(() => {
    mockedExecFile.mockReset();
    mockedSourceProxyFetch.mockReset();
    mockedPatchCodingRun.mockReset();
    mockedUpsertCodingRunRow.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("blocks approved file edits without a task_id", async () => {
    const response = await POST(
      jsonRequest({
        action: "modify file",
        approved: true,
        approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
        content: "new\n",
        target: "src/demo.ts",
      }),
    );

    await expect(response.json()).resolves.toEqual({
      error:
        "execute-approved requires task_id so Source Proxy can re-run verification before apply.",
    });
    expect(response.status).toBe(400);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("forwards task-backed approved diffs to Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      {
        headers: new Headers({ "content-type": "application/json" }),
        status: 200,
        statusText: "OK",
        text: async () => JSON.stringify(executeApprovedContractPayload()),
      } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
    );

    const response = await POST(
      jsonRequest({
        action: "modify file",
        allowed_files: ["src/demo.ts"],
        approved: true,
        approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
        target: "src/demo.ts",
        task_id: "task-123",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      execution: expect.objectContaining({
        invocation_event_id: "invoke-123",
        trace_id: "trace-123",
      }),
      task: expect.objectContaining({
        causal_trace: expect.objectContaining({
          consumer_event_id: "consume-123",
          consumer_subsystem: "long_running_status_observer",
        }),
      }),
    });
    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledTimes(1);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/tasks/long-running/task-123/execute-approved",
      expect.objectContaining({
        method: "POST",
      }),
    );
    const [, init] = mockedSourceProxyFetch.mock.calls[0];
    expect(JSON.parse(String(init?.body))).toEqual({
      action: "modify file",
      allowed_files: ["src/demo.ts"],
      approved: true,
      approval_id: "approval-54865365133e9340",
      approved_by: "coding-ui",
      approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
      changed_files: ["src/demo.ts"],
      commit_authority: false,
      diff_hash: "fe27d77ea2ed4d425e08fda5fb202b554aff43e0b591c8477efa7ad86d7889fe",
      push_authority: false,
      target: "src/demo.ts",
    });
  });

  it("forwards selected prompt bundle diffs under a wildcard allowed root", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      {
        headers: new Headers({ "content-type": "application/json" }),
        status: 200,
        statusText: "OK",
        text: async () => JSON.stringify(executeApprovedContractPayload()),
      } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
    );

    const approvedDiff = [
      "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/README.md b/tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
      "new file mode 100644",
      "--- /dev/null",
      "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
      "@@ -0,0 +1 @@",
      "+# LumaCart",
      "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js b/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
      "new file mode 100644",
      "--- /dev/null",
      "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
      "@@ -0,0 +1 @@",
      "+console.log('LumaCart');",
      "",
    ].join("\n");

    const response = await POST(
      jsonRequest({
        action: "Run selected dummy Coder prompt coder-001-init-dummy-product-site",
        allowed_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
        approved: true,
        approved_diff: approvedDiff,
        target: "tests/ui-agent-trials/fixtures/dummy-product-site/",
        task_id: "task-selected-001",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      task: expect.objectContaining({ id: "task-123" }),
    });
    expect(response.status).toBe(200);
    const [, init] = mockedSourceProxyFetch.mock.calls[0];
    expect(JSON.parse(String(init?.body))).toMatchObject({
      allowed_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
      changed_files: [
        "tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
        "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
      ],
      target: "tests/ui-agent-trials/fixtures/dummy-product-site/",
    });
  });

  it("limits selected dummy local apply eligibility to the isolated fixture root", () => {
    expect(
      isSelectedDummyCoderApply(
        "Run selected dummy Coder prompt coder-002-add-product-data",
        ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
        ["tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js"],
      ),
    ).toBe(true);
    expect(
      isSelectedDummyCoderApply(
        "Run selected dummy Coder prompt coder-002-add-product-data",
        ["src/components/**"],
        ["src/components/coding/CodingCockpitShell.tsx"],
      ),
    ).toBe(false);
    expect(
      isSelectedDummyCoderApply(
        "modify file",
        ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
        ["tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js"],
      ),
    ).toBe(false);
    expect(
      isSelectedDummyCoderApply(
        "Run selected dummy Coder prompt coder-001-init-dummy-product-site",
        ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
        ["tests/ui-agent-trials/fixtures/dummy-product-site/README.md"],
      ),
    ).toBe(false);
  });

  it("classifies Prompt 3 module wiring before local selected apply", () => {
    const staticMainOnly = [
      "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js b/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
      "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
      "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
      "@@ -1,2 +1,4 @@",
      "+import products from './products.js';",
      "+products.forEach((product) => { card.className = 'product-card'; category.textContent = product.category; });",
    ].join("\n");
    const moduleIndexAndStaticMain = [
      "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/index.html b/tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
      "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
      "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
      "@@ -8,1 +8,1 @@",
      "-  <script src=\"src/main.js\"></script>",
      "+  <script type=\"module\" src=\"src/main.js\"></script>",
      staticMainOnly,
    ].join("\n");
    const dynamicMainOnly = staticMainOnly.replace(
      "import products from './products.js';",
      "const module = await import('./products.js'); const products = module.default ?? [];",
    );

    expect(selectedPrompt3DiffViolations(staticMainOnly)).toContain("STATIC_IMPORT_CLASSIC_SCRIPT");
    expect(selectedPrompt3DiffViolations(moduleIndexAndStaticMain)).not.toContain("STATIC_IMPORT_CLASSIC_SCRIPT");
    expect(selectedPrompt3DiffViolations(dynamicMainOnly)).not.toContain("STATIC_IMPORT_CLASSIC_SCRIPT");
    expect(
      selectedPrompt3DiffViolations(
        [
          "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/index.html b/tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
          "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
          "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
          "@@ -8,1 +8,1 @@",
          "-  <script src=\"src/main.js\"></script>",
          "+  <script type=\"module\" src=\"src/main.js\"></script>",
          "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js b/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
          "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
          "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
          "@@ -4,6 +4,8 @@",
          " products.forEach(product => {",
          "   const productElement = document.createElement('div');",
          "+  productElement.classList.add('product-card');",
          "   productElement.innerHTML = `",
          "     <h2>${product.name}</h2>",
          "+    <p>${product.category}</p>",
          "     <p>${product.description}</p>",
          "     <p>$${product.price}</p>",
        ].join("\n"),
        '<script src="src/main.js"></script>',
        [
          "import products from './products.js';",
          "const productList = document.getElementById('product-list');",
          "products.forEach(product => {",
          "  const productElement = document.createElement('div');",
          "  productElement.innerHTML = `<h2>${product.name}</h2><p>${product.description}</p><p>$${product.price}</p>`;",
          "  productList.appendChild(productElement);",
          "});",
        ].join("\n"),
      ),
    ).toEqual([]);
  });

  it("allows Prompt 3 style-only diffs when the current fixture already renders product cards", () => {
    const stylesOnly = [
      "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css b/tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
      "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
      "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
      "@@ -1 +1 @@",
      "-.product-card { padding: 8px; }",
      "+.product-card { padding: 12px; display: grid; gap: 6px; }",
      "",
    ].join("\n");
    const currentIndexHtml = '<script type="module" src="src/main.js"></script>';
    const renderedPreviewHtml = [
      '<article class="product-card">',
      '<p class="category">Lighting</p>',
      '<p class="price">$34.99</p>',
      "</article>",
    ].join("");
    const currentMainJs = [
      "import products from './products.js';",
      "products.forEach(product => {",
      "  const productCard = document.createElement('div');",
      "  productCard.classList.add('product-card');",
      "  product.name; product.category; product.description; product.price;",
      "});",
    ].join("\n");

    expect(selectedPrompt3DiffViolations(stylesOnly)).toContain("MISSING_PRODUCTS_IMPORT");
    expect(selectedPrompt3DiffViolations(stylesOnly, currentIndexHtml, currentMainJs)).toEqual([]);
    expect(selectedPrompt3DiffViolations(stylesOnly, renderedPreviewHtml, currentMainJs)).toEqual([]);
  });

  it("uses git apply --recount for selected dummy fixture diffs", async () => {
    mockedExecFile.mockImplementation((...args: unknown[]) => {
      const callback = args[args.length - 1];
      if (typeof callback !== "function") {
        throw new Error("expected callback");
      }
      callback(null, "", "");
      return {} as ReturnType<typeof execFile>;
    });
    mockedSourceProxyFetch.mockResolvedValueOnce(
      {
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ ok: true }),
      } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
    );

    const approvedDiff = [
      "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js b/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      "@@ -1,99 +1,99 @@",
      " const products = [",
      "-  { name: 'Product A' }",
      "+  { id: 'desk-lamp', name: 'Desk Lamp', price: 24.99, category: 'Home', description: 'Small lamp.' }",
      " ];",
      "",
    ].join("\n");

    const response = await POST(
      jsonRequest({
        action: "Run selected dummy Coder prompt coder-002-add-product-data",
        allowed_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
        approved: true,
        approved_diff: approvedDiff,
        target: "tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
        task_id: "task-selected-recount",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      checks_run: ["git apply --recount --check"],
      status: "applied",
    });
    expect(response.status).toBe(200);
    const checkArgs = mockedExecFile.mock.calls[0]?.[1] as string[];
    const applyArgs = mockedExecFile.mock.calls[1]?.[1] as string[];
    expect(checkArgs.slice(0, 3)).toEqual(["apply", "--recount", "--check"]);
    expect(applyArgs.slice(0, 2)).toEqual(["apply", "--recount"]);
  });

  it("reconstructs a valid Prompt 2 products.js replacement from a stale unified diff", () => {
    const approvedDiff = [
      "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js b/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      "@@ -1,10 +1,12 @@",
      " const products = [",
      "-  { name: 'Product A', description: 'Old starter item.', price: 19.99 },",
      "-  { name: 'Product B', description: 'Old starter item.', price: 29.99 }",
      "+  { id: 'desk-lamp', name: 'Desk Lamp', price: 24.99, category: 'Home', description: 'Small lamp for a tidy desk.' },",
      "+  { id: 'coffee-maker', name: 'Coffee Maker', price: 149.99, category: 'Appliances', description: 'Efficient coffee maker for busy mornings.' },",
      "+  { id: 'water-bottle', name: 'Water Bottle', price: 7.99, category: 'Beverages', description: 'Stainless steel water bottle for staying hydrated.' },",
      "+  { id: 'headphones', name: 'Headphones', price: 49.99, category: 'Electronics', description: 'Noise-cancelling headphones for focused work.' },",
      "+  { id: 't-shirt', name: 'T-Shirt', price: 19.99, category: 'Apparel', description: 'Comfortable cotton shirt in simple colors.' },",
      "+  { id: 'book', name: 'Book', price: 12.99, category: 'Books', description: 'A compact paperback for a weekend read.' }",
      " ];",
      " ",
      " export default products;",
      "",
    ].join("\n");

    const replacement = selectedDummyProductsReplacementFromDiff(approvedDiff);

    expect(replacement).toMatchObject({ ok: true });
    if (!replacement.ok) {
      throw new Error(replacement.reason);
    }
    expect(replacement.content).toContain("id: 'desk-lamp'");
    expect(replacement.content).toContain("category: 'Books'");
    expect(replacement.content).toContain("export default products;");
    expect(replacement.content).not.toContain("Old starter item");
  });

  it("returns structured selected dummy apply diagnostics when git apply check fails", async () => {
    mockedExecFile.mockImplementation((...args: unknown[]) => {
      const callback = args[args.length - 1];
      if (typeof callback !== "function") {
        throw new Error("expected callback");
      }
      const error = Object.assign(new Error("patch does not apply"), {
        code: 1,
        cmd: "git apply --recount --check approved.patch",
        stderr: "error: patch failed: tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js:1",
        stdout: "",
      });
      callback(error, "", error.stderr);
      return {} as ReturnType<typeof execFile>;
    });

    const approvedDiff = [
      "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js b/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      "@@ -1,3 +1,3 @@",
      " const products = [",
      "-  { name: 'Old product' }",
      "+  { id: 'new-product', name: 'New product', price: 9.99, category: 'Home', description: 'Simple item.' }",
      " ];",
      "",
    ].join("\n");

    const response = await POST(
      jsonRequest({
        action: "Run selected dummy Coder prompt coder-002-add-product-data",
        allowed_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
        approved: true,
        approved_diff: approvedDiff,
        target: "tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
        task_id: "task-selected-002",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      changed_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js"],
      error: "Selected dummy fixture apply failed during git apply --recount --check.",
      reason_code: "selected_dummy_git_apply_check_failed",
      route: "/v1/actions/execute-approved",
      stage: "git apply --recount --check",
      stderr: expect.stringContaining("patch failed"),
      task_id: "task-selected-002",
    });
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("records suite apply proof server-side before browser post-apply parsing can reload", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      {
        headers: new Headers({ "content-type": "application/json" }),
        status: 200,
        statusText: "OK",
        text: async () =>
          JSON.stringify(executeApprovedContractPayload({
            task: {
              causal_trace: {
                consumer_event_id: "consume-123",
                consumer_subsystem: "long_running_status_observer",
                invocation_event_id: "invoke-123",
                trace_id: "trace-123",
              },
              id: "task-apply-proof",
              ast_snapshot: {
                approved_execution_evidence: {
                  audit: {
                    changed_files: ["src/app/agent-lab/page.tsx"],
                  },
                },
              },
            },
            tool: "long_running_task_tracker",
          })),
      } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
    );

    const response = await POST(
      jsonRequest({
        action: "Live trial coder-001",
        allowed_files: ["src/app/agent-lab/page.tsx"],
        approved: true,
        approved_diff:
          "--- /dev/null\n+++ b/src/app/agent-lab/page.tsx\n@@ -0,0 +1 @@\n+export default function AgentLabPage() { return null; }\n",
        target: "src/app/agent-lab/page.tsx",
        task_id: "task-apply-proof",
        trial_prompt_id: "coder-001",
        trial_prompt_text: "make a new isolated test area",
        trial_suite_id: "suite-apply-proof",
      }),
    );

    expect(response.status).toBe(200);
    expect(mockedUpsertCodingRunRow).toHaveBeenCalledWith(
      "suite-apply-proof",
      "coder-001",
      expect.objectContaining({
        applied_changed_files: ["src/app/agent-lab/page.tsx"],
        disk_changed_files: ["src/app/agent-lab/page.tsx"],
        endpoint_statuses: expect.arrayContaining([
          "/v1/actions/execute-approved:server_apply_proof_recorded",
        ]),
        result_label: "PASS",
        status: "completed",
        step_instrumentation: expect.objectContaining({
          last_progress_reason_code: "server_apply_proof_recorded",
          result_finalized_at: expect.any(String),
        }),
      }),
    );
    expect(mockedPatchCodingRun).toHaveBeenCalledWith(
      "suite-apply-proof",
      expect.objectContaining({
        applied_changed_files: ["src/app/agent-lab/page.tsx"],
        disk_changed_files: ["src/app/agent-lab/page.tsx"],
        final_summary: "Apply proof recorded by execute-approved route; browser runner can resume.",
        status: "running",
      }),
    );
  });

  it("marks the suite completed when server proof records the final clean prompt", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      {
        headers: new Headers({ "content-type": "application/json" }),
        status: 200,
        statusText: "OK",
        text: async () =>
          JSON.stringify(executeApprovedContractPayload({
            task: {
              causal_trace: {
                consumer_event_id: "consume-123",
                consumer_subsystem: "long_running_status_observer",
                invocation_event_id: "invoke-123",
                trace_id: "trace-123",
              },
              id: "task-final-proof",
              ast_snapshot: {
                approved_execution_evidence: {
                  audit: {
                    changed_files: ["src/app/agent-lab/proxy-health/page.tsx"],
                  },
                },
              },
            },
          })),
      } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
    );
    mockedUpsertCodingRunRow.mockResolvedValueOnce({
      completed_count: 10,
      requested_count: 10,
      rows: Array.from({ length: 10 }, (_, index) => ({
        applied_changed_files: [`src/app/agent-lab/${index}.tsx`],
        disk_changed_files: [`src/app/agent-lab/${index}.tsx`],
        prompt_id: `coder-${String(index + 1).padStart(3, "0")}`,
        reason_code: "",
        result_label: "PASS",
        status: "completed",
      })),
    } as Awaited<ReturnType<typeof upsertCodingRunRow>>);

    const response = await POST(
      jsonRequest({
        action: "Live trial coder-010",
        allowed_files: ["src/app/agent-lab/proxy-health/page.tsx"],
        approved: true,
        approved_diff:
          "--- /dev/null\n+++ b/src/app/agent-lab/proxy-health/page.tsx\n@@ -0,0 +1 @@\n+export default function ProxyHealthPage() { return null; }\n",
        target: "src/app/agent-lab/proxy-health/page.tsx",
        task_id: "task-final-proof",
        trial_prompt_id: "coder-010",
        trial_prompt_text: "make a fake proxy health page",
        trial_suite_id: "suite-final-proof",
      }),
    );

    expect(response.status).toBe(200);
    expect(mockedPatchCodingRun).toHaveBeenCalledWith(
      "suite-final-proof",
      expect.objectContaining({
        final_summary: "Suite completed by execute-approved server proof.",
        status: "completed",
      }),
    );
  });

  it("forwards reverse diffs that delete newly-created files", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      {
        headers: new Headers({ "content-type": "application/json" }),
        status: 200,
        statusText: "OK",
        text: async () => JSON.stringify(executeApprovedContractPayload({ task: {
          causal_trace: {
            consumer_event_id: "consume-123",
            consumer_subsystem: "long_running_status_observer",
            invocation_event_id: "invoke-123",
            trace_id: "trace-123",
          },
          id: "task-revert-123",
        } })),
      } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
    );

    const deletionDiff = [
      "diff --git a/src/app/agent-lab/revert-smoke/page.tsx b/src/app/agent-lab/revert-smoke/page.tsx",
      "deleted file mode 100644",
      "--- b/src/app/agent-lab/revert-smoke/page.tsx",
      "+++ /dev/null",
      "@@ -1 +0,0 @@",
      "-export default function RevertSmoke() { return null; }",
      "",
    ].join("\n");

    const response = await POST(
      jsonRequest({
        action: "Revert live trial coder-001",
        allowed_files: ["src/app/agent-lab/revert-smoke/page.tsx"],
        approved: true,
        approved_diff: deletionDiff,
        target: "src/app/agent-lab/revert-smoke/page.tsx",
        task_id: "task-revert-123",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      task: expect.objectContaining({ id: "task-revert-123" }),
    });
    expect(response.status).toBe(200);
    const [, init] = mockedSourceProxyFetch.mock.calls[0];
    expect(JSON.parse(String(init?.body))).toMatchObject({
      action: "Revert live trial coder-001",
      allowed_files: ["src/app/agent-lab/revert-smoke/page.tsx"],
      changed_files: ["src/app/agent-lab/revert-smoke/page.tsx"],
      target: "src/app/agent-lab/revert-smoke/page.tsx",
    });
  });

  it("rejects approved diffs outside allowed_files before forwarding", async () => {
    const response = await POST(
      jsonRequest({
        action: "modify file",
        allowed_files: ["docs/safe.md"],
        approved: true,
        approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
        target: "src/demo.ts",
        task_id: "task-123",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      allowed_files: ["docs/safe.md"],
      changed_files: ["src/demo.ts"],
      error: "execute-approved approved_diff changed files are outside allowed_files.",
      unexpected_files: ["src/demo.ts"],
    });
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("rejects new interactive agent-lab app-router pages without use client before forwarding", async () => {
    const response = await POST(
      jsonRequest({
        action: "Live trial coder-002",
        allowed_files: ["src/app/agent-lab/calculator/page.tsx"],
        approved: true,
        approved_diff: [
          "diff --git a/src/app/agent-lab/calculator/page.tsx b/src/app/agent-lab/calculator/page.tsx",
          "new file mode 100644",
          "--- /dev/null",
          "+++ b/src/app/agent-lab/calculator/page.tsx",
          "@@ -0,0 +1,6 @@",
          "+import React, { useState } from 'react';",
          "+",
          "+export default function CalculatorPage() {",
          "+  const [num1, setNum1] = useState('');",
          "+  return <input value={num1} onChange={(event) => setNum1(event.target.value)} />;",
          "+}",
          "",
        ].join("\n"),
        target: "src/app/agent-lab/calculator/page.tsx",
        task_id: "task-client-directive",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      error:
        'execute-approved rejected an interactive app-router page without "use client" as the first line.',
      missing_use_client_files: ["src/app/agent-lab/calculator/page.tsx"],
    });
    expect(response.status).toBe(422);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("rejects protected paths before forwarding", async () => {
    const response = await POST(
      jsonRequest({
        action: "modify file",
        allowed_files: [".env.local"],
        approved: true,
        approved_diff: "--- a/.env.local\n+++ b/.env.local\n@@ -1 +1 @@\n-old\n+new\n",
        target: ".env.local",
        task_id: "task-123",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      changed_files: [".env.local"],
      error: "execute-approved rejected protected path in approved_diff.",
    });
    expect(response.status).toBe(403);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("rejects stale approval ids before forwarding", async () => {
    const response = await POST(
      jsonRequest({
        action: "modify file",
        allowed_files: ["src/demo.ts"],
        approval_id: "approval-stale",
        approved: true,
        approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
        target: "src/demo.ts",
        task_id: "task-123",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      error:
        "execute-approved approval_id does not match task_id, target, and approved_diff.",
      expected_approval_id: "approval-54865365133e9340",
    });
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("fails closed when Source Proxy success lacks the Plan 4 causal contract", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      {
        headers: new Headers({ "content-type": "application/json" }),
        status: 200,
        statusText: "OK",
        text: async () => JSON.stringify({ ok: true }),
      } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
    );

    const response = await POST(
      jsonRequest({
        action: "modify file",
        allowed_files: ["src/demo.ts"],
        approved: true,
        approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
        target: "src/demo.ts",
        task_id: "task-123",
      }),
    );

    await expect(response.json()).resolves.toEqual({
      error: "execute-approved returned success without the Plan 4 causal output contract.",
      missing_fields: [
        "task_id",
        "trace_id",
        "invocation_event_id",
        "consumer_event_id",
        "consumer_subsystem",
      ],
      reason_code: "plan4_execute_approved_contract_missing",
      task_id: "task-123",
    });
    expect(response.status).toBe(502);
    expect(mockedUpsertCodingRunRow).not.toHaveBeenCalled();
    expect(mockedPatchCodingRun).not.toHaveBeenCalled();
  });
});
