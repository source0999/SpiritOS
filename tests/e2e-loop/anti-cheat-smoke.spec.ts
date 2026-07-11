import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const selectedPromptStorageKey = "spiritos:coding:dummy-coder-selected-run:v1";
const promptId = "coder-001-init-dummy-product-site";
const fixtureRoot = path.join(process.cwd(), "tests", "ui-agent-trials", "fixtures", "dummy-product-site");
const terminalStatusPattern = /^(applied|blocked|complete|error|timeout)$/;

type FixtureState = "bare" | "rendering";
type HttpEvent = {
  method: string;
  status: number;
  url: string;
};

test.describe.configure({ mode: "serial" });

test("Prompt 1 bare fixture and rendered fixture exercise anti-cheat round-trip", async ({ page }, testInfo) => {
  test.setTimeout(180_000);
  expect(process.env.E2E_LOOP_PRODUCT_RESET_VERIFIED).toBe("true");

  const httpEvents: HttpEvent[] = [];
  page.on("response", (response) => {
    const url = response.url();
    if (
      url.includes("/coding") ||
      url.includes("/v1/tasks/long-running") ||
      url.includes("/v1/decisions/prompt-packet") ||
      url.includes("/v1/verification/diff-preview") ||
      url.includes("/v1/actions/execute-approved")
    ) {
      httpEvents.push({ method: response.request().method(), status: response.status(), url });
    }
  });

  seedFixtureStateAfterVerifiedReset("bare");
  const bare = await runPrompt1(page, "bare");
  await testInfo.attach("bare-fixture-diagnostics", {
    body: bare.diagnostics,
    contentType: "text/plain",
  });
  console.log("ANTI_CHEAT_SMOKE_BARE_DIAGNOSTICS_BEGIN");
  console.log(bare.diagnostics);
  console.log("ANTI_CHEAT_SMOKE_BARE_DIAGNOSTICS_END");

  expect(bare.rawBackendStatus).not.toBe("already_satisfied");
  expect(bare.diagnostics).not.toContain("raw_backend_status: already_satisfied");
  expect(bare.diagnostics).not.toContain("SPIRIT_CODING_USE_PROXY is not true");
  expect(bare.antiCheatStatus).toBe("passed");
  expect(hasRejectedAntiCheatStatus(bare.antiCheatStatuses)).toBe(false);

  const bareChangedFiles = diagnosticValue(bare.diagnostics, "changed_files");
  const bareHasRealResult =
    (bareChangedFiles && bareChangedFiles !== "none") ||
    /blocked|coder_model_not_configured|model|source_proxy|No diff produced|NEEDS FIX|timeout/i.test(bare.diagnostics);
  expect(Boolean(bareHasRealResult)).toBe(true);

  seedFixtureStateAfterVerifiedReset("rendering");
  const rendering = await runPrompt1(page, "rendering");
  await testInfo.attach("rendering-fixture-diagnostics", {
    body: rendering.diagnostics,
    contentType: "text/plain",
  });
  console.log("ANTI_CHEAT_SMOKE_RENDERING_DIAGNOSTICS_BEGIN");
  console.log(rendering.diagnostics);
  console.log("ANTI_CHEAT_SMOKE_RENDERING_DIAGNOSTICS_END");

  writeCapture({
    schema_version: process.env.E2E_LOOP_SCHEMA_VERSION ?? "missing",
    authoritative_stages: authoritativeStagesFromDiagnostics(rendering.diagnostics),
    bare,
    http_events: httpEvents,
    rendering,
  });

  expect(rendering.rawBackendStatus).toBe("already_satisfied");
  expect(rendering.diagnostics).toContain("preview_behavior_status: PASS_STOREFRONT_RENDERED");
  expect(rendering.diagnostics).toContain("storefront_runtime_status: passed");
  expect(rendering.diagnostics).toContain("grader_label: PASS_NOOP");
  expect(rendering.antiCheatStatus).toBe("passed");
  expect(hasRejectedAntiCheatStatus(rendering.antiCheatStatuses)).toBe(false);
});

async function runPrompt1(page: import("@playwright/test").Page, fixtureState: FixtureState) {
  await page.goto("/coding");
  await expect(page.getByRole("heading", { level: 1, name: "Coding" })).toBeVisible();
  await page.evaluate((key) => window.localStorage.removeItem(key), selectedPromptStorageKey);
  await page.reload();
  await expect(page.getByTestId("dummy-coder-prompt-select")).toBeVisible();
  await page.getByTestId("dummy-coder-prompt-select").selectOption(promptId);

  const diagnosticsNode = page.getByTestId("selected-prompt-diagnostics");
  const previousDiagnostics = ((await diagnosticsNode.textContent()) ?? "").trim();
  const previousTaskId = diagnosticValue(previousDiagnostics, "selected_prompt_task_id");
  await page.getByTestId("run-selected-dummy-coder-prompt").click();

  await expect
    .poll(
      async () => {
        const diagnostics = ((await diagnosticsNode.textContent()) ?? "").trim();
        const status = (await diagnosticsNode.getAttribute("data-selected-prompt-status")) ?? "";
        const taskId = diagnosticValue(diagnostics, "selected_prompt_task_id");
        if (!terminalStatusPattern.test(status)) return "";
        if (!taskId || taskId === "none" || taskId === previousTaskId) return "";
        if (!hasSettledDiagnostics(diagnostics)) return "";
        return `${status}:${taskId}`;
      },
      {
        intervals: [1_000, 2_000, 5_000],
        timeout: 90_000,
      },
    )
    .toMatch(/^(applied|blocked|complete|error|timeout):task_/u);

  const diagnostics = ((await diagnosticsNode.textContent()) ?? "").trim();
  return {
    antiCheatStatus: diagnosticValue(diagnostics, "anti_cheat_status"),
    antiCheatStatuses: diagnosticValues(diagnostics, "anti_cheat_status"),
    diagnostics,
    fixtureState,
    rawBackendStatus: diagnosticValue(diagnostics, "raw_backend_status"),
    terminalStatus: (await diagnosticsNode.getAttribute("data-selected-prompt-status")) ?? "unknown",
  };
}

function hasRejectedAntiCheatStatus(statuses: string[]) {
  return statuses.some((status) => ["blocked", "fail", "failed", "not graded", "not_run"].includes(status.toLowerCase()));
}

function hasSettledDiagnostics(diagnostics: string) {
  const antiCheatStatus = diagnosticValue(diagnostics, "anti_cheat_status");
  const graderLabel = diagnosticValue(diagnostics, "grader_label");
  return Boolean(
    antiCheatStatus &&
      antiCheatStatus !== "not graded" &&
      graderLabel &&
      graderLabel !== "not graded",
  );
}

function seedFixtureStateAfterVerifiedReset(state: FixtureState) {
  // This only seeds an explicit anti-cheat test precondition. The managed loop must
  // verify the product reset endpoint before Playwright is allowed to reach here.
  mkdirSync(path.join(fixtureRoot, "src"), { recursive: true });
  writeFileSync(
    path.join(fixtureRoot, "README.md"),
    "# LumaCart\n\nIsolated dummy product storefront fixture for Source Proxy coder trials.\n",
    "utf8",
  );
  writeFileSync(
    path.join(fixtureRoot, "package.json"),
    `${JSON.stringify({ private: true, scripts: { start: "vite --host 127.0.0.1" } }, null, 2)}\n`,
    "utf8",
  );
  writeFileSync(path.join(fixtureRoot, "src", "products.js"), productsModule(), "utf8");
  writeFileSync(path.join(fixtureRoot, "src", "styles.css"), stylesCss(), "utf8");

  if (state === "bare") {
    writeFileSync(
      path.join(fixtureRoot, "index.html"),
      [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        "  <title>LumaCart</title>",
        '  <link rel="stylesheet" href="src/styles.css">',
        "</head>",
        "<body>",
        "  <h1>LumaCart</h1>",
        '  <main id="product-list"></main>',
        '  <script src="src/main.js"></script>',
        "</body>",
        "</html>",
        "",
      ].join("\n"),
      "utf8",
    );
    writeFileSync(
      path.join(fixtureRoot, "src", "main.js"),
      "console.log('LumaCart fixture loaded without rendering products.');\n",
      "utf8",
    );
    return;
  }

  writeFileSync(
    path.join(fixtureRoot, "index.html"),
    [
      "<!doctype html>",
      '<html lang="en">',
      "<head>",
      '  <meta charset="utf-8">',
      "  <title>LumaCart</title>",
      '  <link rel="stylesheet" href="src/styles.css">',
      "</head>",
      "<body>",
      "  <h1>LumaCart</h1>",
      '  <main id="product-list" aria-label="Products"></main>',
      '  <script type="module" src="src/main.js"></script>',
      "</body>",
      "</html>",
      "",
    ].join("\n"),
    "utf8",
  );
  writeFileSync(
    path.join(fixtureRoot, "src", "main.js"),
    [
      "import products from './products.js';",
      "",
      "const list = document.querySelector('#product-list');",
      "",
      "products.forEach((product) => {",
      "  const card = document.createElement('article');",
      "  card.className = 'product-card';",
      "  const name = document.createElement('h2');",
      "  name.textContent = product.name;",
      "  const price = document.createElement('p');",
      "  price.className = 'price';",
      "  price.textContent = `$${product.price}`;",
      "  const category = document.createElement('p');",
      "  category.className = 'category';",
      "  category.textContent = product.category;",
      "  const description = document.createElement('p');",
      "  description.className = 'description';",
      "  description.textContent = product.description;",
      "  card.appendChild(name);",
      "  card.appendChild(price);",
      "  card.appendChild(category);",
      "  card.appendChild(description);",
      "  list.appendChild(card);",
      "});",
      "",
    ].join("\n"),
    "utf8",
  );
}

function productsModule() {
  return [
    "const products = [",
    "  { id: 'desk-lamp', name: 'Desk Lamp', price: 32, category: 'Home', description: 'Warm light for a desk.' },",
    "  { id: 'coffee-maker', name: 'Coffee Maker', price: 58, category: 'Kitchen', description: 'Small brewer for mornings.' },",
    "  { id: 'water-bottle', name: 'Water Bottle', price: 18, category: 'Outdoor', description: 'Steel bottle for day trips.' },",
    "  { id: 'wireless-mouse', name: 'Wireless Mouse', price: 24, category: 'Office', description: 'Compact mouse for laptops.' },",
    "  { id: 'canvas-tote', name: 'Canvas Tote', price: 16, category: 'Everyday', description: 'Reusable carry bag.' },",
    "  { id: 'notebook-set', name: 'Notebook Set', price: 12, category: 'Office', description: 'Three soft-cover notebooks.' },",
    "];",
    "",
    "export default products;",
    "",
  ].join("\n");
}

function stylesCss() {
  return [
    "body { font-family: system-ui, sans-serif; margin: 2rem; }",
    "#product-list { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); }",
    ".product-card { border: 1px solid #ddd; border-radius: 0.5rem; padding: 1rem; }",
    ".price, .category { font-weight: 700; }",
    "",
  ].join("\n");
}

function writeCapture(payload: Record<string, unknown>) {
  const diagnosticsPath = process.env.E2E_LOOP_DIAGNOSTICS_PATH;
  const diagnostics = diagnosticsFromCapture(payload);
  if (diagnosticsPath && diagnostics) {
    mkdirSync(path.dirname(diagnosticsPath), { recursive: true });
    writeFileSync(diagnosticsPath, `${diagnostics}
`, "utf8");
  }

  const capturePath = process.env.E2E_LOOP_CAPTURE_PATH;
  if (!capturePath) return;
  mkdirSync(path.dirname(capturePath), { recursive: true });
  writeFileSync(capturePath, `${JSON.stringify(payload, null, 2)}
`, "utf8");
}

function diagnosticsFromCapture(payload: Record<string, unknown>) {
  const rendering = payload.rendering;
  if (rendering && typeof rendering === "object" && "diagnostics" in rendering) {
    const diagnostics = rendering.diagnostics;
    if (typeof diagnostics === "string" && diagnostics.trim()) return diagnostics.trim();
  }
  const bare = payload.bare;
  if (bare && typeof bare === "object" && "diagnostics" in bare) {
    const diagnostics = bare.diagnostics;
    if (typeof diagnostics === "string" && diagnostics.trim()) return diagnostics.trim();
  }
  return "";
}

function authoritativeStagesFromDiagnostics(diagnostics: string) {
  const valueFromKeys = (keys: string[]) => {
    for (const key of keys) {
      const value = diagnosticValue(diagnostics, key);
      if (value) return value;
    }
    return "";
  };
  const contextRaw = valueFromKeys([
    "canonical_context_final_verdict",
    "canonical_context_verdict",
    "canonical_context_status",
    "context_broker_verdict",
    "context_verdict",
  ]);
  const contextConsumptionRaw = valueFromKeys([
    "canonical_context_consumption_status",
    "context_consumption_status",
  ]);
  const contextAcknowledgementRaw = valueFromKeys([
    "downstream_context_acknowledgement_status",
    "context_acknowledgement_status",
  ]);
  const requiredContextRaw = valueFromKeys([
    "required_context_status",
    "required_context_fail_closed_status",
  ]);
  const postApplyRaw = diagnosticValue(diagnostics, "post_apply_verification_status");
  const previewBehavior = diagnosticValue(diagnostics, "preview_behavior_status");
  const storefrontRuntime = diagnosticValue(diagnostics, "storefront_runtime_status");
  const antiCheatStatuses = diagnosticValues(diagnostics, "anti_cheat_status");
  const antiCheatRaw = antiCheatStatuses.at(-1) ?? "";
  const truthStatus = diagnosticValue(diagnostics, "truth_status");
  const commitSafeRaw = diagnosticValue(diagnostics, "commit_safe");
  const runStatus = diagnosticValue(diagnostics, "run_status");
  const receiptPath = valueFromKeys(["final_receipt_path", "receipt_path", "block_receipt_path"]);
  const finalReceiptRaw = diagnosticValue(diagnostics, "final_receipt_status");
  const conflictKeys = [
    "truth_status",
    "commit_safe",
    "run_status",
    "raw_backend_status",
    "anti_cheat_status",
    "trial_result_trust_status",
  ];
  const conflicts = Object.fromEntries(
    conflictKeys.flatMap((key) => {
      const values = [...new Set(diagnosticValues(diagnostics, key))];
      return values.length > 1 ? [[key, values]] : [];
    }),
  );
  const contextGo =
    ["GO", "GO_ELIGIBLE", "passed", "verified"].includes(contextRaw) &&
    ["GO", "passed", "consumed"].includes(contextConsumptionRaw) &&
    ["GO", "passed", "acknowledged"].includes(contextAcknowledgementRaw) &&
    ["GO", "passed"].includes(requiredContextRaw);
  const postApplyGo = ["GO", "passed", "verified", "complete", "completed"].includes(postApplyRaw);
  const browserGo = previewBehavior === "PASS_STOREFRONT_RENDERED" && storefrontRuntime === "passed";
  const antiCheatGo =
    antiCheatRaw === "passed" &&
    antiCheatStatuses.length > 0 &&
    !antiCheatStatuses.some((status) => ["blocked", "fail", "failed", "not graded", "not_run"].includes(status.toLowerCase()));
  const commitSafe = commitSafeRaw === "true";
  const receiptRecorded = Boolean(receiptPath && !/^(missing|not_applicable|none)/iu.test(receiptPath));
  const finalReceiptGo =
    truthStatus === "GO" &&
    commitSafe &&
    postApplyGo &&
    receiptRecorded &&
    (!finalReceiptRaw || finalReceiptRaw === "GO") &&
    ["complete", "completed"].includes(runStatus);
  return {
    context: {
      status: contextGo ? "GO" : "NO_GO",
      acknowledgement_status: contextAcknowledgementRaw || "missing",
      broker_status: contextRaw || "missing",
      consumption_status: contextConsumptionRaw || "missing",
      required_context_status: requiredContextRaw || "missing",
    },
    post_apply_verification: { status: postApplyGo ? "GO" : "NO_GO", raw_status: postApplyRaw || "missing" },
    browser_verification: {
      status: browserGo ? "GO" : "NO_GO",
      preview_behavior_status: previewBehavior || "missing",
      storefront_runtime_status: storefrontRuntime || "missing",
    },
    anti_cheat: { status: antiCheatGo ? "GO" : "NO_GO", raw_statuses: antiCheatStatuses },
    final_receipt: {
      status: finalReceiptGo ? "GO" : "NO_GO",
      commit_safe: commitSafe,
      receipt_path: receiptPath || "missing",
      run_status: runStatus || "missing",
      truth_status: truthStatus || "missing",
    },
    diagnostic_consistency: {
      status: Object.keys(conflicts).length === 0 ? "GO" : "NO_GO",
      conflicts,
    },
  };
}

function diagnosticValue(diagnostics: string, key: string) {
  return diagnosticValues(diagnostics, key).at(-1) ?? "";
}

function diagnosticValues(diagnostics: string, key: string) {
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matches = [...diagnostics.matchAll(new RegExp(`^${escaped}:\\s*(.*)$`, "gm"))];
  return matches.map((match) => match[1]?.trim() ?? "").filter(Boolean);
}
