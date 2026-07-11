import { expect, test } from "@playwright/test";
import type { APIResponse, Page, Response as PlaywrightResponse, TestInfo } from "@playwright/test";
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const selectedPromptStorageKey = "spiritos:coding:dummy-coder-selected-run:v1";
const promptId = "coder-001-init-dummy-product-site";
const terminalStatusPattern = /^(applied|blocked|complete|error|timeout)$/;
const fixtureRoot = "tests/ui-agent-trials/fixtures/dummy-product-site";
const fixtureRelativePaths = [
  "README.md",
  "package.json",
  "index.html",
  "src/main.js",
  "src/products.js",
  "src/styles.css",
] as const;
const fixturePaths = fixtureRelativePaths.map((relativePath) => `${fixtureRoot}/${relativePath}`);
const canonicalStageNames = [
  "context",
  "post_apply_verification",
  "browser_verification",
  "anti_cheat",
  "final_receipt",
  "diagnostic_consistency",
] as const;

type HttpEvent = {
  method: string;
  observedAtMs: number;
  sequence: number;
  status: number;
  url: string;
};

type AuthoritativeStage = {
  status: string;
  [key: string]: unknown;
};

type AuthoritativeStages = Record<string, AuthoritativeStage>;

type PromptRunEvidence = {
  antiCheatStatus: string;
  applyStatus: string;
  authoritativeStages: AuthoritativeStages;
  browserProof: AuthoritativeStage;
  changedFiles: string;
  diagnostics: string;
  errorText: string;
  rawBackendStatus: string;
  completedAtMs: number;
  startedAtMs: number;
  taskId: string;
  terminalStatus: string;
};

test("Prompt 1 proves apply, manifest Undo, product reset, and a clean rerun through /coding", async ({ page }, testInfo) => {
  test.setTimeout(420_000);
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
      httpEvents.push({
        method: response.request().method(),
        observedAtMs: Date.now(),
        sequence: httpEvents.length + 1,
        status: response.status(),
        url,
      });
    }
  });

  const capture: Record<string, unknown> = {
    schema_version: process.env.E2E_LOOP_SCHEMA_VERSION ?? "missing",
    authoritative_stages: pendingLifecycleStages("Prompt 1 lifecycle has not started."),
    diagnostics: "",
    fixture_state: process.env.E2E_LOOP_FIXTURE_STATE ?? "unknown",
    http_events: httpEvents,
    selected_prompt_id: promptId,
  };
  const unrelatedWorkspaceBefore = captureUnrelatedWorktreeSnapshot(process.cwd());
  capture.unrelated_workspace_before = unrelatedSnapshotSummary(unrelatedWorkspaceBefore);

  await page.goto("/coding");
  await expect(page.getByRole("heading", { level: 1, name: "Coding" })).toBeVisible();
  await page.evaluate((key) => window.localStorage.removeItem(key), selectedPromptStorageKey);
  await page.reload();
  await expect(page.getByRole("heading", { level: 1, name: "Coding" })).toBeVisible();

  const initialCleanProbe = await probeCleanFixture(page, 0);
  capture.initial_fixture_clean_precondition = initialCleanProbe;
  writeEvidence(capture);
  expect(initialCleanProbe.status).toBe("GO");

  const initialRun = await runPrompt1(page, testInfo, "initial");
  const initialRunStage = promptRunLifecycleStage(initialRun, {
    fixtureWasCleanBeforeRun: initialCleanProbe.status === "GO",
    lifecycleSequence: 1,
  });
  const lifecycleStages: AuthoritativeStages = {
    ...initialRun.authoritativeStages,
    prompt1_initial_run: initialRunStage,
    manifest_backed_undo: pendingStage("UI Undo has not run."),
    clean_baseline_after_undo: pendingStage("Post-Undo clean baseline has not been probed."),
    product_reset_after_undo: pendingStage("Post-Undo product reset has not run."),
    prompt1_clean_rerun: pendingStage("Clean Prompt 1 rerun has not run."),
  };
  capture.authoritative_stages = lifecycleStages;
  capture.diagnostics = initialRun.diagnostics;
  capture.initial_prompt1_run = initialRun;
  writeEvidence(capture);
  assertCanonicalPromptRun(initialRun, initialRunStage);

  const initialReceiptPath = stringValue(initialRun.authoritativeStages.final_receipt?.receipt_path);
  const undoAndReset = await performUiManifestUndoAndReset(
    page,
    initialRun.taskId,
    initialReceiptPath,
    initialRun.completedAtMs,
    httpEvents,
    unrelatedWorkspaceBefore,
  );
  const cleanAfterUndo = await probeCleanFixture(page, 4);
  const cleanProbeOrdered = Boolean(
    typeof undoAndReset.productReset.response_observed_at_ms === "number" &&
      typeof cleanAfterUndo.probe_started_at_ms === "number" &&
      cleanAfterUndo.probe_started_at_ms >= undoAndReset.productReset.response_observed_at_ms,
  );
  const cleanBaselineStage: AuthoritativeStage = {
    ...cleanAfterUndo,
    status:
      cleanAfterUndo.status === "GO" && undoAndReset.productReset.status === "GO" && cleanProbeOrdered
        ? "GO"
        : "NO_GO",
    probe_started_after_product_reset: cleanProbeOrdered,
    verified_after_product_reset: undoAndReset.productReset.status === "GO",
    verified_after_reset_response_sequence: undoAndReset.productReset.response_sequence,
  };
  lifecycleStages.manifest_backed_undo = undoAndReset.manifestUndo;
  lifecycleStages.product_reset_after_undo = undoAndReset.productReset;
  lifecycleStages.clean_baseline_after_undo = cleanBaselineStage;
  capture.authoritative_stages = lifecycleStages;
  capture.manifest_backed_undo = undoAndReset.manifestUndo;
  capture.product_reset_after_undo = undoAndReset.productReset;
  capture.clean_baseline_after_undo = cleanBaselineStage;
  writeEvidence(capture);
  expect(undoAndReset.manifestUndo.status).toBe("GO");
  expect(undoAndReset.productReset.status).toBe("GO");
  expect(cleanBaselineStage.status).toBe("GO");

  await page.reload();
  await expect(page.getByRole("heading", { level: 1, name: "Coding" })).toBeVisible();
  const rerun = await runPrompt1(page, testInfo, "clean-rerun", [initialRun.taskId]);
  const unrelatedWorkspaceAfterRerun = captureUnrelatedWorktreeSnapshot(process.cwd());
  const unrelatedRerunComparison = compareUnrelatedWorktreeSnapshots(
    unrelatedWorkspaceBefore,
    unrelatedWorkspaceAfterRerun,
  );
  const rerunStage = promptRunLifecycleStage(rerun, {
    fixtureWasCleanBeforeRun: cleanBaselineStage.status === "GO",
    initialTaskId: initialRun.taskId,
    cleanBaselineCompletedAtMs:
      typeof cleanBaselineStage.probe_completed_at_ms === "number"
        ? cleanBaselineStage.probe_completed_at_ms
        : undefined,
    lifecycleSequence: 5,
    startedAfterProductReset: undoAndReset.productReset.status === "GO",
  });
  Object.assign(rerunStage, {
    unrelated_workspace_preservation: unrelatedRerunComparison,
    unrelated_workspace_after: unrelatedSnapshotSummary(unrelatedWorkspaceAfterRerun),
  });
  if (unrelatedRerunComparison.status !== "GO") rerunStage.status = "NO_GO";
  const finalAuthoritativeStages: AuthoritativeStages = {
    ...rerun.authoritativeStages,
    prompt1_initial_run: initialRunStage,
    manifest_backed_undo: undoAndReset.manifestUndo,
    clean_baseline_after_undo: cleanBaselineStage,
    product_reset_after_undo: undoAndReset.productReset,
    prompt1_clean_rerun: rerunStage,
  };
  const combinedDiagnostics = [
    "=== prompt1_initial_run ===",
    initialRun.diagnostics,
    "=== prompt1_clean_rerun ===",
    rerun.diagnostics,
  ].join("\n");
  capture.authoritative_stages = finalAuthoritativeStages;
  capture.diagnostics = combinedDiagnostics;
  capture.clean_prompt1_rerun = rerun;
  capture.lifecycle_order = [
    "prompt1_initial_run",
    "manifest_backed_undo",
    "product_reset_after_undo",
    "clean_baseline_after_undo",
    "prompt1_clean_rerun",
  ];
  writeEvidence(capture);

  assertCanonicalPromptRun(rerun, rerunStage);
  for (const stageName of [
    ...canonicalStageNames,
    "prompt1_initial_run",
    "manifest_backed_undo",
    "product_reset_after_undo",
    "clean_baseline_after_undo",
    "prompt1_clean_rerun",
  ]) {
    expect(finalAuthoritativeStages[stageName]?.status, `${stageName} must be authoritative GO`).toBe("GO");
  }
});

async function runPrompt1(
  page: Page,
  testInfo: TestInfo,
  evidenceLabel: string,
  disallowedTaskIds: string[] = [],
): Promise<PromptRunEvidence> {
  await expect(page.getByTestId("dummy-coder-prompt-select")).toBeVisible();
  await page.getByTestId("dummy-coder-prompt-select").selectOption(promptId);
  await expect(page.getByTestId("run-selected-dummy-coder-prompt")).toBeVisible();
  const diagnosticsNode = page.getByTestId("selected-prompt-diagnostics");
  const previousDiagnostics = ((await diagnosticsNode.textContent()) ?? "").trim();
  const previousTaskId = diagnosticValue(previousDiagnostics, "selected_prompt_task_id");
  const blockedTaskIds = new Set([previousTaskId, ...disallowedTaskIds].filter(Boolean));
  const startedAtMs = Date.now();
  await page.getByTestId("run-selected-dummy-coder-prompt").click();

  await expect
    .poll(
      async () => {
        const diagnostics = ((await diagnosticsNode.textContent()) ?? "").trim();
        const status = (await diagnosticsNode.getAttribute("data-selected-prompt-status")) ?? "";
        const taskId = diagnosticValue(diagnostics, "selected_prompt_task_id");
        if (!terminalStatusPattern.test(status)) return false;
        if (!taskId || taskId === "none" || blockedTaskIds.has(taskId)) return false;
        return hasSettledDiagnostics(diagnostics);
      },
      {
        intervals: [1_000, 2_000, 5_000],
        timeout: 120_000,
      },
    )
    .toBe(true);

  const diagnostics = ((await diagnosticsNode.textContent()) ?? "").trim();
  const taskId = diagnosticValue(diagnostics, "selected_prompt_task_id");
  const terminalStatus = (await diagnosticsNode.getAttribute("data-selected-prompt-status")) ?? "unknown";
  const diagnosticStages = authoritativeStagesFromDiagnostics(diagnostics);
  const browserProof = await verifyRealStorefrontInBrowser(page, taskId, testInfo, evidenceLabel);
  const evidence = {
    antiCheatStatus: diagnosticValue(diagnostics, "anti_cheat_status"),
    applyStatus: diagnosticValue(diagnostics, "apply_status"),
    authoritativeStages: {
      ...diagnosticStages,
      browser_verification: browserProof,
    },
    browserProof,
    changedFiles: diagnosticValue(diagnostics, "changed_files"),
    diagnostics,
    errorText: diagnosticValue(diagnostics, "error_text"),
    rawBackendStatus: diagnosticValue(diagnostics, "raw_backend_status"),
    completedAtMs: Date.now(),
    startedAtMs,
    taskId,
    terminalStatus,
  };

  await testInfo.attach(`${evidenceLabel}-selected-prompt-diagnostics`, {
    body: diagnostics,
    contentType: "text/plain",
  });
  return evidence;
}

async function verifyRealStorefrontInBrowser(
  page: Page,
  taskId: string,
  testInfo: TestInfo,
  evidenceLabel: string,
): Promise<AuthoritativeStage> {
  const previewPath = "/v1/coding/dummy-product-site-preview";
  const expectedAssetPaths = [
    previewPath,
    `${previewPath}/src/main.js`,
    `${previewPath}/src/products.js`,
    `${previewPath}/src/styles.css`,
  ];
  const responseEvents: Array<{ path: string; status: number; url: string }> = [];
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const requestFailures: Array<{ error: string; url: string }> = [];
  const previewPage = await page.context().newPage();
  previewPage.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  previewPage.on("pageerror", (error) => pageErrors.push(String(error)));
  previewPage.on("requestfailed", (request) => {
    requestFailures.push({
      error: request.failure()?.errorText ?? "request_failed",
      url: request.url(),
    });
  });
  previewPage.on("response", (response) => {
    const url = new URL(response.url());
    if (url.pathname.startsWith(previewPath)) {
      responseEvents.push({ path: url.pathname, status: response.status(), url: response.url() });
    }
  });

  let navigationStatus: number | null = null;
  let directProof: Record<string, unknown> = {};
  let runtimeError = "";
  try {
    const previewUrl = new URL(`${previewPath}?lifecycle_browser_proof=${Date.now()}`, page.url());
    const navigation = await previewPage.goto(previewUrl.toString(), {
      timeout: 30_000,
      waitUntil: "domcontentloaded",
    });
    navigationStatus = navigation?.status() ?? null;
    await previewPage.waitForFunction(
      () =>
        [...document.querySelectorAll(".product-card")].filter((element) => {
          const style = window.getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
        }).length >= 6,
      undefined,
      { timeout: 15_000 },
    );
    await previewPage.waitForLoadState("networkidle", { timeout: 15_000 });
    directProof = await previewPage.evaluate(async (productsUrl) => {
      const normalize = (value: unknown) => String(value ?? "").replace(/\s+/g, " ").trim();
      const visible = (element: Element) => {
        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
      };
      const productModule = await import(productsUrl);
      const products = Array.isArray(productModule.default)
        ? productModule.default
        : Array.isArray(productModule.products)
          ? productModule.products
          : [];
      const cards = [...document.querySelectorAll(".product-card")]
        .filter(visible)
        .map((card) => ({
          heading: normalize(card.querySelector("h1,h2,h3,h4")?.textContent),
          text: normalize((card as HTMLElement).innerText || card.textContent),
        }));
      const productFieldMatches = products.map((product: Record<string, unknown>) => {
        const fields = {
          name: normalize(product.name),
          price: normalize(product.price),
          category: normalize(product.category),
          description: normalize(product.description),
        };
        return {
          fields_present: Object.values(fields).every(Boolean),
          name: fields.name,
          rendered: cards.some((card) =>
            Object.values(fields).every((value) => value && card.text.includes(value)),
          ),
        };
      });
      return {
        document_ready_state: document.readyState,
        module_script_loaded: [...document.scripts].some(
          (script) => script.type === "module" && new URL(script.src).pathname.endsWith("/src/main.js"),
        ),
        noscript_card_count: document.querySelectorAll("noscript .product-card").length,
        product_count: products.length,
        product_field_matches: productFieldMatches,
        rendered_card_count: cards.length,
        rendered_headings: cards.map((card) => card.heading).filter(Boolean),
        stylesheet_loaded: [...document.styleSheets].some(
          (sheet) => sheet.href && new URL(sheet.href).pathname.endsWith("/src/styles.css"),
        ),
      };
    }, `${new URL(previewPage.url()).origin}${previewPath}/src/products.js`);
  } catch (error) {
    runtimeError = error instanceof Error ? error.message : String(error);
  }

  const taskResponse = await page.request.get(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}?browser_proof=${Date.now()}`,
  );
  const taskPayload = await jsonRecord(taskResponse);
  const task = recordValue(taskPayload.task);
  const postApply = recordValue(task.post_apply_verification);
  const backendEvidence = recordValue(postApply.browser_evidence);
  const snapshot = recordValue(task.ast_snapshot);
  const executionEvidence = recordValue(snapshot.approved_execution_evidence);
  const snapshotVerification = recordValue(postApply.snapshot_verification);
  const directProductMatches = recordArray(directProof.product_field_matches);
  const directRenderedCount = Number(directProof.rendered_card_count ?? 0);
  const directProductCount = Number(directProof.product_count ?? 0);
  const responseStatuses = Object.fromEntries(
    expectedAssetPaths.map((path) => [
      path,
      [...responseEvents].reverse().find((event) => event.path === path)?.status ?? null,
    ]),
  );
  const backendPreviewUrl = stringValue(backendEvidence.preview_url);
  const backendPreview = (() => {
    try {
      return new URL(backendPreviewUrl);
    } catch {
      return null;
    }
  })();
  const backendBound = Boolean(
    taskResponse.ok() &&
      task.status === "completed" &&
      postApply.status === "verified" &&
      backendEvidence.schema_version === "dummy-storefront-browser-proof/v1" &&
      backendEvidence.storefront_runtime_engine === "playwright_chromium" &&
      backendEvidence.real_browser_used === true &&
      backendEvidence.managed_frontend_origin === "https://localhost:3000" &&
      backendPreview?.origin === "https://localhost:3000" &&
      backendPreview?.pathname === previewPath &&
      backendEvidence.task_id === taskId &&
      backendEvidence.approved_diff_sha256 === executionEvidence.approved_diff_sha256 &&
      backendEvidence.backup_manifest === executionEvidence.backup_manifest &&
      backendEvidence.post_apply_rediff_sha256 === snapshotVerification.post_apply_rediff_sha256 &&
      stringValue(postApply.browser_evidence_sha256) &&
      postApply.browser_evidence_sha256 === backendEvidence.browser_evidence_sha256 &&
      backendEvidence.product_count === 6 &&
      backendEvidence.rendered_card_count === 6
  );
  const directBrowserPassed = Boolean(
    navigationStatus === 200 &&
      new URL(previewPage.url()).origin === "https://localhost:3000" &&
      directProof.document_ready_state === "complete" &&
      directProof.module_script_loaded === true &&
      directProof.stylesheet_loaded === true &&
      directProductCount === 6 &&
      directRenderedCount === 6 &&
      directProductMatches.length === 6 &&
      directProductMatches.every(
        (item) => item.fields_present === true && item.rendered === true,
      ) &&
      directProof.noscript_card_count === 0 &&
      Object.values(responseStatuses).every((status) => status === 200) &&
      consoleErrors.length === 0 &&
      pageErrors.length === 0 &&
      requestFailures.length === 0 &&
      !runtimeError
  );
  const proof: AuthoritativeStage = {
    status: directBrowserPassed && backendBound ? "GO" : "NO_GO",
    source: "playwright_direct_preview_plus_backend_managed_playwright_receipt",
    real_browser_used: true,
    managed_frontend_origin: new URL(previewPage.url()).origin,
    preview_url: previewPage.url(),
    preview_http_status: navigationStatus,
    product_count: directProductCount,
    rendered_card_count: directRenderedCount,
    product_field_matches: directProductMatches,
    rendered_headings: directProof.rendered_headings,
    module_script_loaded: directProof.module_script_loaded === true,
    stylesheet_loaded: directProof.stylesheet_loaded === true,
    noscript_card_count: directProof.noscript_card_count,
    asset_responses: responseStatuses,
    console_errors: consoleErrors,
    page_errors: pageErrors,
    request_failures: requestFailures,
    runtime_error: runtimeError || null,
    backend_receipt_bound: backendBound,
    backend_browser_engine: stringValue(backendEvidence.storefront_runtime_engine) || "missing",
    backend_browser_evidence_sha256: stringValue(postApply.browser_evidence_sha256) || "missing",
    backend_backup_manifest: stringValue(executionEvidence.backup_manifest) || "missing",
    backend_post_apply_rediff_sha256:
      stringValue(snapshotVerification.post_apply_rediff_sha256) || "missing",
    task_id: taskId,
  };
  await testInfo.attach(`${evidenceLabel}-real-browser-proof`, {
    body: JSON.stringify(proof, null, 2),
    contentType: "application/json",
  });
  await previewPage.close();
  return proof;
}

function promptRunLifecycleStage(
  run: PromptRunEvidence,
  options: {
    fixtureWasCleanBeforeRun: boolean;
    initialTaskId?: string;
    cleanBaselineCompletedAtMs?: number;
    lifecycleSequence: number;
    startedAfterProductReset?: boolean;
  },
): AuthoritativeStage {
  const canonicalStages = Object.fromEntries(
    canonicalStageNames.map((name) => [name, run.authoritativeStages[name]?.status ?? "MISSING"]),
  );
  const canonicalStagesGo = canonicalStageNames.every((name) => canonicalStages[name] === "GO");
  const changedPaths = diagnosticList(run.changedFiles).sort();
  const expectedChangedPaths = [...fixturePaths].sort();
  const expectedPrompt1ChangedFiles = sameStrings(changedPaths, expectedChangedPaths);
  const changedFilesPresent = expectedPrompt1ChangedFiles;
  const alreadySatisfied = /^already_satisfied(?:\b|:)/iu.test(run.rawBackendStatus);
  const distinctFromInitialTask = options.initialTaskId ? run.taskId !== options.initialTaskId : undefined;
  const startedAfterCleanBaseline =
    options.cleanBaselineCompletedAtMs === undefined
      ? undefined
      : run.startedAtMs >= options.cleanBaselineCompletedAtMs;
  const status =
    /^task_/u.test(run.taskId) &&
    ["applied", "complete"].includes(run.terminalStatus) &&
    run.applyStatus === "performed" &&
    changedFilesPresent &&
    options.fixtureWasCleanBeforeRun &&
    !alreadySatisfied &&
    canonicalStagesGo &&
    (!options.initialTaskId || distinctFromInitialTask === true) &&
    (options.cleanBaselineCompletedAtMs === undefined || startedAfterCleanBaseline === true) &&
    (options.startedAfterProductReset === undefined || options.startedAfterProductReset)
      ? "GO"
      : "NO_GO";

  return {
    status,
    task_id: run.taskId || "missing",
    terminal_status: run.terminalStatus,
    apply_status: run.applyStatus || "missing",
    post_apply_verification_status: canonicalStages.post_apply_verification,
    browser_verification_status: canonicalStages.browser_verification,
    final_receipt_status: canonicalStages.final_receipt,
    final_receipt_path: stringValue(run.authoritativeStages.final_receipt?.receipt_path) || "missing",
    commit_safe: run.authoritativeStages.final_receipt?.commit_safe === true,
    grader_label: stringValue(run.authoritativeStages.anti_cheat?.grader_label) || "missing",
    trial_result_trust_status:
      stringValue(run.authoritativeStages.anti_cheat?.trial_result_trust_status) || "missing",
    changed_files: run.changedFiles || "missing",
    changed_paths: changedPaths,
    changed_files_present: changedFilesPresent,
    expected_prompt1_changed_files: expectedPrompt1ChangedFiles,
    fixture_was_clean_before_run: options.fixtureWasCleanBeforeRun,
    already_satisfied: alreadySatisfied,
    canonical_stages: canonicalStages,
    lifecycle_sequence: options.lifecycleSequence,
    run_started_at_ms: run.startedAtMs,
    run_completed_at_ms: run.completedAtMs,
    ...(options.initialTaskId
      ? {
          distinct_from_initial_task: distinctFromInitialTask,
          initial_task_id: options.initialTaskId,
          clean_baseline_completed_at_ms: options.cleanBaselineCompletedAtMs,
          started_after_clean_baseline: startedAfterCleanBaseline === true,
          started_after_product_reset: options.startedAfterProductReset === true,
        }
      : {}),
  };
}

function assertCanonicalPromptRun(run: PromptRunEvidence, lifecycleStage: AuthoritativeStage) {
  expect(run.diagnostics).toContain(`selected_prompt_id: ${promptId}`);
  expect(run.errorText).not.toBe("SPIRIT_CODING_USE_PROXY is not true");
  expect(run.diagnostics).not.toContain("SPIRIT_CODING_USE_PROXY is not true");
  expect(run.rawBackendStatus).not.toBe("/v1/tasks/long-running:no_task_id");
  expect(run.antiCheatStatus).toBe("passed");
  expect(lifecycleStage.status).toBe("GO");
  for (const stageName of canonicalStageNames) {
    expect(run.authoritativeStages[stageName]?.status, `${stageName} must be GO`).toBe("GO");
  }
}

async function performUiManifestUndoAndReset(
  page: Page,
  initialTaskId: string,
  initialReceiptPath: string,
  initialRunCompletedAtMs: number,
  httpEvents: HttpEvent[],
  unrelatedWorkspaceBefore: ReturnType<typeof captureUnrelatedWorktreeSnapshot>,
) {
  const runner = page.getByRole("region", { name: "Trial Runner" });
  const undoControl = runner
    .getByTestId("selected-prompt-undo-last-change")
    .or(runner.getByRole("button", { name: "Undo last change", exact: true }))
    .or(runner.getByRole("button", { name: "Reverse trial edits and clear results", exact: true }))
    .first();
  await expect(undoControl).toBeVisible();
  await expect(undoControl).toBeEnabled();
  const controlLabel = ((await undoControl.textContent()) ?? "").trim();
  const sequenceBeforeClick = httpEvents.at(-1)?.sequence ?? 0;
  const undoPath = `/v1/tasks/long-running/${encodeURIComponent(initialTaskId)}/undo`;
  const resetPath = "/v1/coding/dummy-product-site-preview/reset";
  const undoResponsePromise = page.waitForResponse(
    (response) => response.request().method() === "POST" && urlPath(response.url()) === undoPath,
    { timeout: 180_000 },
  );
  const resetResponsePromise = page.waitForResponse(
    (response) => response.request().method() === "POST" && urlPath(response.url()) === resetPath,
    { timeout: 180_000 },
  );
  const preResetPreviewResponsePromise = page.waitForResponse(
    (response) =>
      response.request().method() === "GET" &&
      urlPath(response.url()) === "/v1/coding/dummy-product-site-preview/index.html",
    { timeout: 180_000 },
  );
  const preResetBaselineResponsePromise = page.waitForResponse(
    (response) =>
      response.request().method() === "GET" &&
      urlPath(response.url()) === "/v1/coding/agent-lab-baseline",
    { timeout: 180_000 },
  );
  await undoControl.click();
  const [undoResponse, preResetPreviewResponse, preResetBaselineResponse, resetResponse] = await Promise.all([
    undoResponsePromise,
    preResetPreviewResponsePromise,
    preResetBaselineResponsePromise,
    resetResponsePromise,
  ]);

  await expect
    .poll(
      () => page.getByTestId("selected-prompt-diagnostics").getAttribute("data-selected-prompt-status"),
      { intervals: [500, 1_000, 2_000], timeout: 120_000 },
    )
    .toBe("cleared");

  const undoRequest = postDataRecord(undoResponse);
  const undoPayload = await jsonRecord(undoResponse);
  const undo = recordValue(undoPayload.undo);
  const restoredFiles = recordArray(undo.files_restored);
  const restoredPaths = restoredFiles.map((item) => stringValue(item.path)).filter(Boolean).sort();
  const expectedPaths = [...fixturePaths].sort();
  const allExpectedFilesRestored = sameStrings(restoredPaths, expectedPaths);
  const allRestoredToAbsent =
    restoredFiles.length === expectedPaths.length &&
    restoredFiles.every((item) => item.verified === true && item.absent === true && item.actual_sha256 == null);
  const unrelatedPathsTouched = stringArray(undo.unrelated_paths_touched);
  const undoReceiptId = stringValue(undo.undo_receipt_id);
  const undoReceiptPath = stringValue(undo.receipt_path);
  const expectedBackupManifest = stringValue(undoRequest.expected_backup_manifest);
  const selectedBackupManifest = stringValue(undo.selected_backup_manifest);

  const persistedResponse = await page.request.get(
    `/v1/tasks/long-running/${encodeURIComponent(initialTaskId)}?e2e=${Date.now()}`,
  );
  const persistedPayload = await jsonRecord(persistedResponse);
  const persistedTask = recordValue(persistedPayload.task);
  const persistedSnapshot = recordValue(persistedTask.ast_snapshot);
  const persistedUndo = recordValue(persistedSnapshot.undo_receipt);
  const persistedRestoredFiles = recordArray(persistedUndo.files_restored);
  const persistedRestoredPaths = persistedRestoredFiles
    .map((item) => stringValue(item.path))
    .filter(Boolean)
    .sort();
  const persistedFilesRestoredVerified = Boolean(
    sameStrings(persistedRestoredPaths, expectedPaths) &&
      persistedRestoredFiles.length === expectedPaths.length &&
      persistedRestoredFiles.every(
        (item) => item.verified === true && item.absent === true && item.actual_sha256 == null,
      ),
  );
  const persistedReceiptVerified = Boolean(
    persistedResponse.ok() &&
      persistedSnapshot.undo_status === "filesystem_verified" &&
      persistedUndo.undo_receipt_id === undoReceiptId &&
      persistedUndo.receipt_path === undoReceiptPath &&
      persistedUndo.original_task_id === initialTaskId &&
      persistedUndo.selected_backup_manifest === initialReceiptPath &&
      persistedUndo.filesystem_verified === true &&
      persistedUndo.untouched_scope_assertion === true &&
      persistedFilesRestoredVerified
  );
  const persistedOpenDiffs = recordArray(persistedTask.open_diffs);
  const openDiffMarkedUndone = persistedOpenDiffs.some(
    (diff) => diff.status === "undone" && diff.undo_receipt_id === undoReceiptId,
  );

  const undoEvent = responseEvent(httpEvents, sequenceBeforeClick, "POST", undoPath);
  const resetEvent = responseEvent(httpEvents, sequenceBeforeClick, "POST", resetPath);
  const undoSequence = undoEvent?.sequence ?? null;
  const resetSequence = resetEvent?.sequence ?? null;
  const preResetPreview = httpEvents.find(
    (event) =>
      undoSequence != null &&
      resetSequence != null &&
      event.sequence > undoSequence &&
      event.sequence < resetSequence &&
      event.method === "GET" &&
      urlPath(event.url) === "/v1/coding/dummy-product-site-preview/index.html" &&
      event.status === 404,
  );
  const preResetBaseline = httpEvents.find(
    (event) =>
      undoSequence != null &&
      resetSequence != null &&
      event.sequence > undoSequence &&
      event.sequence < resetSequence &&
      event.method === "GET" &&
      urlPath(event.url) === "/v1/coding/agent-lab-baseline" &&
      event.status === 200,
  );
  const preResetBaselinePayload = await jsonRecord(preResetBaselineResponse);
  const preResetDirtyFiles = stringArray(preResetBaselinePayload.baseline_dirty_agent_lab_files);
  const preResetDummyDirtyFiles = preResetDirtyFiles.filter((item) => item.startsWith(`${fixtureRoot}/`));
  const preResetBaselineClean = Boolean(
    preResetBaselineResponse.ok() &&
      preResetBaselinePayload.baseline_clean_for_fresh_suite === true &&
      preResetDummyDirtyFiles.length === 0,
  );
  const preResetPreviewMissing = preResetPreviewResponse.status() === 404;
  const unrelatedWorkspaceAfterUndo = captureUnrelatedWorktreeSnapshot(process.cwd());
  const unrelatedWorkspaceComparison = compareUnrelatedWorktreeSnapshots(
    unrelatedWorkspaceBefore,
    unrelatedWorkspaceAfterUndo,
  );
  const manifestUndoGo = Boolean(
    undoResponse.ok() &&
      /Undo|Reverse/u.test(controlLabel) &&
      undoRequest.confirm_undo === true &&
      undoRequest.requested_by === "coding-ui" &&
      expectedBackupManifest &&
      initialReceiptPath === expectedBackupManifest &&
      selectedBackupManifest === expectedBackupManifest &&
      undo.original_task_id === initialTaskId &&
      undoReceiptId &&
      undoReceiptPath &&
      undo.filesystem_verified === true &&
      undo.untouched_scope_assertion === true &&
      undo.expected_browser_state === "fixture_missing" &&
      unrelatedPathsTouched.length === 0 &&
      allExpectedFilesRestored &&
      allRestoredToAbsent &&
      persistedReceiptVerified &&
      persistedFilesRestoredVerified &&
      openDiffMarkedUndone &&
      undoSequence != null &&
      undoEvent != null &&
      undoEvent.observedAtMs >= initialRunCompletedAtMs &&
      preResetPreview &&
      preResetBaseline &&
      preResetPreviewMissing &&
      preResetBaselineClean &&
      unrelatedWorkspaceComparison.status === "GO"
  );
  const manifestUndo: AuthoritativeStage = {
    status: manifestUndoGo ? "GO" : "NO_GO",
    ui_control_label: controlLabel || "missing",
    ui_triggered: true,
    request_url: undoResponse.url(),
    http_status: undoResponse.status(),
    request_confirm_undo: undoRequest.confirm_undo === true,
    requested_by: stringValue(undoRequest.requested_by) || "missing",
    original_task_id: stringValue(undo.original_task_id) || "missing",
    expected_backup_manifest: expectedBackupManifest || "missing",
    initial_final_receipt_path: initialReceiptPath || "missing",
    selected_backup_manifest: selectedBackupManifest || "missing",
    undo_receipt_id: undoReceiptId || "missing",
    undo_receipt_path: undoReceiptPath || "missing",
    filesystem_verified: undo.filesystem_verified === true,
    untouched_scope_assertion: undo.untouched_scope_assertion === true,
    unrelated_paths_touched: unrelatedPathsTouched,
    independent_unrelated_worktree: unrelatedWorkspaceComparison,
    independent_unrelated_worktree_after: unrelatedSnapshotSummary(unrelatedWorkspaceAfterUndo),
    expected_browser_state: stringValue(undo.expected_browser_state) || "missing",
    restored_paths: restoredPaths,
    files_restored: restoredFiles,
    all_expected_files_restored: allExpectedFilesRestored,
    all_restored_to_absent: allRestoredToAbsent,
    persisted_task_http_status: persistedResponse.status(),
    persisted_receipt_verified: persistedReceiptVerified,
    persisted_selected_backup_manifest: stringValue(persistedUndo.selected_backup_manifest) || "missing",
    persisted_restored_paths: persistedRestoredPaths,
    persisted_files_restored: persistedRestoredFiles,
    persisted_files_restored_verified: persistedFilesRestoredVerified,
    open_diff_marked_undone: openDiffMarkedUndone,
    ui_pre_reset_preview_http_status: preResetPreviewResponse.status(),
    ui_pre_reset_preview_missing: Boolean(preResetPreview && preResetPreviewMissing),
    ui_pre_reset_baseline_http_status: preResetBaselineResponse.status(),
    ui_pre_reset_baseline_checked: Boolean(preResetBaseline),
    ui_pre_reset_baseline_clean_for_fresh_suite: preResetBaselineClean,
    ui_pre_reset_baseline_dirty_files: preResetDirtyFiles,
    ui_pre_reset_dummy_fixture_dirty_files: preResetDummyDirtyFiles,
    lifecycle_sequence: 2,
    initial_run_completed_at_ms: initialRunCompletedAtMs,
    response_observed_at_ms: undoEvent?.observedAtMs ?? null,
    response_sequence: undoSequence,
  };

  const resetPayload = await jsonRecord(resetResponse);
  const productResetGo = Boolean(
    resetResponse.ok() &&
      resetPayload.status === "reset_verified" &&
      resetPayload.reset_verified === true &&
      resetPayload.clean_verified === true &&
      stringValue(resetPayload.reset_receipt_id) &&
      resetSequence != null &&
      undoSequence != null &&
      resetSequence > undoSequence &&
      resetEvent != null &&
      undoEvent != null &&
      resetEvent.observedAtMs >= undoEvent.observedAtMs
  );
  const productReset: AuthoritativeStage = {
    status: productResetGo ? "GO" : "NO_GO",
    ui_triggered: true,
    request_url: resetResponse.url(),
    http_status: resetResponse.status(),
    response_status: stringValue(resetPayload.status) || "missing",
    reset_verified: resetPayload.reset_verified === true,
    clean_verified: resetPayload.clean_verified === true,
    reset_receipt_id: stringValue(resetPayload.reset_receipt_id) || "missing",
    fixture_root: stringValue(resetPayload.fixture_root) || "missing",
    lifecycle_sequence: 3,
    response_observed_at_ms: resetEvent?.observedAtMs ?? null,
    response_sequence: resetSequence,
    occurred_after_undo: resetSequence != null && undoSequence != null && resetSequence > undoSequence,
  };

  return { manifestUndo, productReset };
}

async function probeCleanFixture(page: Page, lifecycleSequence: number): Promise<AuthoritativeStage> {
  const probeStartedAtMs = Date.now();
  const baselineResponse = await page.request.get(`/v1/coding/agent-lab-baseline?e2e=${Date.now()}`);
  const baselinePayload = await jsonRecord(baselineResponse);
  const dirtyFiles = stringArray(baselinePayload.baseline_dirty_agent_lab_files);
  const dummyFixtureDirtyFiles = dirtyFiles.filter((item) => item.startsWith(`${fixtureRoot}/`));
  const fileProbes = await Promise.all(
    fixturePaths.map(async (fixturePath) => {
      const response = await page.request.post("/v1/coding/workspace-read", {
        data: { path: fixturePath },
      });
      const payload = await jsonRecord(response);
      const detail = recordValue(payload.detail);
      const reasonCode = stringValue(detail.reason_code) || stringValue(payload.reason_code);
      return {
        path: fixturePath,
        http_status: response.status(),
        reason_code: reasonCode || "missing",
        missing:
          response.status() === 400 &&
          (reasonCode === "not_file" || reasonCode === "not_found"),
      };
    }),
  );
  const previewResponse = await page.request.get(
    `/v1/coding/dummy-product-site-preview/index.html?e2e=${Date.now()}`,
  );
  const baselineClean = baselineResponse.ok() && baselinePayload.baseline_clean_for_fresh_suite === true;
  const allFixtureFilesAbsent = fileProbes.every((probe) => probe.missing);
  const previewMissing = previewResponse.status() === 404;
  const go = baselineClean && dummyFixtureDirtyFiles.length === 0 && allFixtureFilesAbsent && previewMissing;
  const probeCompletedAtMs = Date.now();

  return {
    status: go ? "GO" : "NO_GO",
    baseline_http_status: baselineResponse.status(),
    baseline_clean_for_fresh_suite: baselineClean,
    baseline_dirty_agent_lab_files: dirtyFiles,
    dummy_fixture_dirty_files: dummyFixtureDirtyFiles,
    file_probes: fileProbes,
    all_fixture_files_absent: allFixtureFilesAbsent,
    preview_http_status: previewResponse.status(),
    preview_missing: previewMissing,
    lifecycle_sequence: lifecycleSequence,
    probe_started_at_ms: probeStartedAtMs,
    probe_completed_at_ms: probeCompletedAtMs,
  };
}

function hasSettledDiagnostics(diagnostics: string) {
  const antiCheatStatus = diagnosticValue(diagnostics, "anti_cheat_status");
  const graderLabel = diagnosticValue(diagnostics, "grader_label");
  return Boolean(
    antiCheatStatus &&
      antiCheatStatus !== "not graded" &&
      antiCheatStatus !== "not_run" &&
      graderLabel &&
      graderLabel !== "not graded" &&
      graderLabel !== "not_run",
  );
}

type UnrelatedWorktreeSnapshot = {
  schema_version: string;
  snapshot_sha256: string;
  tracked_diff_bytes: number;
  tracked_diff_sha256: string;
  untracked_file_count: number;
  untracked_files: Array<{ path: string; [key: string]: unknown }>;
  captured_at_ms: number;
};

function captureUnrelatedWorktreeSnapshot(repoRoot: string): UnrelatedWorktreeSnapshot {
  const result = spawnSync(
    process.execPath,
    [path.join(repoRoot, "scripts/unrelated-worktree-proof.mjs"), "--full"],
    {
      cwd: repoRoot,
      encoding: "utf8",
      maxBuffer: 256 * 1024 * 1024,
      windowsHide: true,
    },
  );
  if (result.status !== 0) {
    throw new Error(
      `Independent unrelated-worktree snapshot failed (${result.status}): ${result.stderr || result.stdout}`,
    );
  }
  return JSON.parse(result.stdout) as UnrelatedWorktreeSnapshot;
}

function compareUnrelatedWorktreeSnapshots(
  before: UnrelatedWorktreeSnapshot,
  after: UnrelatedWorktreeSnapshot,
) {
  const beforeFiles = new Map(before.untracked_files.map((item) => [item.path, item]));
  const afterFiles = new Map(after.untracked_files.map((item) => [item.path, item]));
  const changedPaths = [...new Set([...beforeFiles.keys(), ...afterFiles.keys()])]
    .filter((relativePath) =>
      JSON.stringify(beforeFiles.get(relativePath)) !== JSON.stringify(afterFiles.get(relativePath)),
    )
    .sort();
  const trackedDiffMatches = before.tracked_diff_sha256 === after.tracked_diff_sha256;
  const untrackedFilesMatch = changedPaths.length === 0;
  const snapshotMatches = before.snapshot_sha256 === after.snapshot_sha256;
  return {
    status: trackedDiffMatches && untrackedFilesMatch && snapshotMatches ? "GO" : "NO_GO",
    snapshot_matches: snapshotMatches,
    tracked_diff_matches: trackedDiffMatches,
    untracked_files_match: untrackedFilesMatch,
    before_snapshot_sha256: before.snapshot_sha256,
    after_snapshot_sha256: after.snapshot_sha256,
    before_tracked_diff_sha256: before.tracked_diff_sha256,
    after_tracked_diff_sha256: after.tracked_diff_sha256,
    before_untracked_file_count: before.untracked_file_count,
    after_untracked_file_count: after.untracked_file_count,
    changed_paths: changedPaths,
    compared_at_ms: Date.now(),
  };
}

function unrelatedSnapshotSummary(snapshot: UnrelatedWorktreeSnapshot) {
  return {
    schema_version: snapshot.schema_version,
    snapshot_sha256: snapshot.snapshot_sha256,
    tracked_diff_bytes: snapshot.tracked_diff_bytes,
    tracked_diff_sha256: snapshot.tracked_diff_sha256,
    untracked_file_count: snapshot.untracked_file_count,
    captured_at_ms: snapshot.captured_at_ms,
  };
}

function writeEvidence(payload: Record<string, unknown>) {
  const diagnosticsPath = process.env.E2E_LOOP_DIAGNOSTICS_PATH;
  if (diagnosticsPath && typeof payload.diagnostics === "string") {
    mkdirSync(path.dirname(diagnosticsPath), { recursive: true });
    writeFileSync(diagnosticsPath, `${payload.diagnostics}\n`, "utf8");
  }

  const capturePath = process.env.E2E_LOOP_CAPTURE_PATH;
  if (capturePath) {
    mkdirSync(path.dirname(capturePath), { recursive: true });
    writeFileSync(capturePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  }
}

function pendingLifecycleStages(reason: string): AuthoritativeStages {
  return {
    prompt1_initial_run: pendingStage(reason),
    manifest_backed_undo: pendingStage(reason),
    clean_baseline_after_undo: pendingStage(reason),
    product_reset_after_undo: pendingStage(reason),
    prompt1_clean_rerun: pendingStage(reason),
  };
}

function pendingStage(reason: string): AuthoritativeStage {
  return { status: "NO_GO", reason };
}

function diagnosticValue(diagnostics: string, key: string) {
  return diagnosticValues(diagnostics, key).at(-1) ?? "";
}

function diagnosticValues(diagnostics: string, key: string) {
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matches = [...diagnostics.matchAll(new RegExp(`^${escaped}:\\s*(.*)$`, "gm"))];
  return matches.map((match) => match[1]?.trim() ?? "").filter(Boolean);
}

function diagnosticValueFromKeys(diagnostics: string, keys: string[]) {
  for (const key of keys) {
    const value = diagnosticValue(diagnostics, key);
    if (value) return value;
  }
  return "";
}

function authoritativeStagesFromDiagnostics(diagnostics: string): AuthoritativeStages {
  const contextRaw = diagnosticValueFromKeys(diagnostics, [
    "canonical_context_final_verdict",
    "canonical_context_verdict",
    "canonical_context_status",
    "context_broker_verdict",
    "context_verdict",
  ]);
  const contextConsumptionRaw = diagnosticValueFromKeys(diagnostics, [
    "canonical_context_consumption_status",
    "context_consumption_status",
  ]);
  const contextAcknowledgementRaw = diagnosticValueFromKeys(diagnostics, [
    "downstream_context_acknowledgement_status",
    "context_acknowledgement_status",
  ]);
  const requiredContextRaw = diagnosticValueFromKeys(diagnostics, [
    "required_context_status",
    "required_context_fail_closed_status",
  ]);
  const postApplyRaw = diagnosticValue(diagnostics, "post_apply_verification_status");
  const previewBehavior = diagnosticValue(diagnostics, "preview_behavior_status");
  const storefrontRuntime = diagnosticValue(diagnostics, "storefront_runtime_status");
  const storefrontRuntimeEngine = diagnosticValue(diagnostics, "storefront_runtime_engine");
  const browserEvidenceSource = diagnosticValue(diagnostics, "browser_evidence_source");
  const realBrowserUsed = diagnosticValue(diagnostics, "real_browser_used");
  const antiCheatStatuses = diagnosticValues(diagnostics, "anti_cheat_status");
  const antiCheatRaw = antiCheatStatuses.at(-1) ?? "";
  const graderLabels = diagnosticValues(diagnostics, "grader_label");
  const graderLabel = graderLabels.at(-1) ?? "";
  const trustStatuses = diagnosticValues(diagnostics, "trial_result_trust_status");
  const trustStatus = trustStatuses.at(-1) ?? "";
  const truthStatus = diagnosticValueFromKeys(diagnostics, [
    "truth_status",
    "final_truth_status",
    "final_truth_summary_truth_status",
  ]);
  const commitSafeRaw = diagnosticValue(diagnostics, "commit_safe");
  const runStatus = diagnosticValue(diagnostics, "run_status");
  const receiptPath = diagnosticValueFromKeys(diagnostics, [
    "final_receipt_path",
    "backup_manifest",
    "receipt_path",
    "block_receipt_path",
  ]);
  const finalReceiptRaw = diagnosticValue(diagnostics, "final_receipt_status");
  const conflicts = {
    ...diagnosticConflicts(diagnostics, [
      "truth_status",
      "final_truth_status",
      "commit_safe",
      "run_status",
      "raw_backend_status",
      "anti_cheat_status",
      "trial_result_trust_status",
    ]),
    ...diagnosticAliasConflicts(diagnostics, {
      truth_status_aliases: [
        "truth_status",
        "final_truth_status",
        "final_truth_summary_truth_status",
      ],
    }),
    ...diagnosticStatusAliasConflicts(diagnostics, {
      context_verdict_aliases: [
        "canonical_context_final_verdict",
        "canonical_context_verdict",
        "canonical_context_status",
        "context_broker_verdict",
        "context_verdict",
      ],
      context_consumption_aliases: [
        "canonical_context_consumption_status",
        "context_consumption_status",
      ],
      context_acknowledgement_aliases: [
        "downstream_context_acknowledgement_status",
        "context_acknowledgement_status",
      ],
      required_context_aliases: [
        "required_context_status",
        "required_context_fail_closed_status",
      ],
    }),
  };

  const contextGo =
    ["GO", "GO_ELIGIBLE", "passed", "verified"].includes(contextRaw) &&
    ["GO", "passed", "consumed"].includes(contextConsumptionRaw) &&
    ["GO", "passed", "acknowledged"].includes(contextAcknowledgementRaw) &&
    ["GO", "passed"].includes(requiredContextRaw);
  const postApplyGo = ["GO", "passed", "verified", "complete", "completed"].includes(postApplyRaw);
  const browserGo =
    previewBehavior === "PASS_STOREFRONT_RENDERED" &&
    storefrontRuntime === "passed" &&
    storefrontRuntimeEngine === "playwright_chromium" &&
    browserEvidenceSource === "source_proxy_managed_playwright" &&
    realBrowserUsed === "true";
  const antiCheatGo =
    antiCheatRaw === "passed" &&
    antiCheatStatuses.length > 0 &&
    !antiCheatStatuses.some((status) => ["blocked", "fail", "failed", "not graded", "not_run"].includes(status.toLowerCase())) &&
    graderLabels.length > 0 &&
    graderLabels.every((label) => label === "PASS") &&
    graderLabel === "PASS" &&
    trustStatuses.length > 0 &&
    trustStatuses.every((status) => status === "model_authored_diff_proven") &&
    trustStatus === "model_authored_diff_proven";
  const commitSafe = commitSafeRaw === "true";
  const receiptRecorded = Boolean(receiptPath && !/^(missing|not_applicable|none)/iu.test(receiptPath));
  const finalReceiptGo =
    truthStatus === "GO" &&
    commitSafe &&
    postApplyGo &&
    receiptRecorded &&
    (!finalReceiptRaw || finalReceiptRaw === "GO") &&
    ["applied", "complete", "completed"].includes(runStatus);

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
      storefront_runtime_engine: storefrontRuntimeEngine || "missing",
      browser_evidence_source: browserEvidenceSource || "missing",
      real_browser_used: realBrowserUsed === "true",
    },
    anti_cheat: {
      status: antiCheatGo ? "GO" : "NO_GO",
      raw_statuses: antiCheatStatuses,
      grader_label: graderLabel || "missing",
      grader_labels: graderLabels,
      trial_result_trust_status: trustStatus || "missing",
      trial_result_trust_statuses: trustStatuses,
    },
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

function diagnosticConflicts(diagnostics: string, keys: string[]) {
  return Object.fromEntries(
    keys.flatMap((key) => {
      const values = [...new Set(diagnosticValues(diagnostics, key))];
      return values.length > 1 ? [[key, values]] : [];
    }),
  );
}

function diagnosticAliasConflicts(diagnostics: string, groups: Record<string, string[]>) {
  return Object.fromEntries(
    Object.entries(groups).flatMap(([groupName, keys]) => {
      const values = [
        ...new Set(keys.flatMap((key) => diagnosticValues(diagnostics, key))),
      ];
      return values.length > 1 ? [[groupName, values]] : [];
    }),
  );
}

function diagnosticStatusAliasConflicts(diagnostics: string, groups: Record<string, string[]>) {
  return Object.fromEntries(
    Object.entries(groups).flatMap(([groupName, keys]) => {
      const values = [
        ...new Set(
          keys
            .flatMap((key) => diagnosticValues(diagnostics, key))
            .map(diagnosticStatusPolarity),
        ),
      ];
      return values.length > 1 ? [[groupName, values]] : [];
    }),
  );
}

function diagnosticStatusPolarity(value: string) {
  return ["GO", "GO_ELIGIBLE", "passed", "verified", "consumed", "acknowledged"].includes(value)
    ? "GO"
    : "NO_GO";
}

function postDataRecord(response: PlaywrightResponse) {
  try {
    return recordValue(response.request().postDataJSON());
  } catch {
    return {};
  }
}

async function jsonRecord(response: APIResponse | PlaywrightResponse) {
  try {
    return recordValue(await response.json());
  } catch {
    return {};
  }
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function recordArray(value: unknown) {
  return Array.isArray(value) ? value.map(recordValue) : [];
}

function stringArray(value: unknown) {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function diagnosticList(value: string) {
  if (!value || /^(missing|none|not_applicable|not_recorded)/iu.test(value)) return [];
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function sameStrings(left: string[], right: string[]) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function urlPath(url: string) {
  try {
    return new URL(url).pathname;
  } catch {
    return "";
  }
}

function responseEvent(
  events: HttpEvent[],
  afterSequence: number,
  method: string,
  pathname: string,
) {
  return events.find(
    (event) =>
      event.sequence > afterSequence && event.method === method && urlPath(event.url) === pathname,
  );
}
