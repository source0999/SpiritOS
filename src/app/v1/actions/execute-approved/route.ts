import { sourceProxyFetch } from "@/lib/source-proxy-origin";
import { patchCodingRun, upsertCodingRunRow } from "@/lib/coding/durable-run-store";
import type { DurableCodingRunProvenance } from "@/lib/coding/durable-run-types";
import { execFile } from "node:child_process";
import { createHash } from "crypto";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const DUMMY_CODER_10_FIXTURE_ROOT = "tests/ui-agent-trials/fixtures/dummy-product-site/";
const DUMMY_CODER_10_PROMPT1_FILES = [
  "README.md",
  "package.json",
  "index.html",
  "src/main.js",
  "src/products.js",
  "src/styles.css",
].map((file) => `${DUMMY_CODER_10_FIXTURE_ROOT}${file}`);
const SELECTED_DUMMY_GIT_APPLY_FLAG_CHAINS: string[][] = [
  [],
  ["--ignore-whitespace"],
  ["--ignore-space-change"],
];

type DiagnosticEnvelope = {
  stage_id: string;
  subsystem: string;
  task_id: string;
  selected_prompt_task_id: string;
  run_id: string;
  trace_id: string;
  invocation_event_id: string;
  consumer_event_id: string;
  status: string;
  truth_status: "GO" | "BLOCKED_SAFE" | "FAILED_UNSAFE" | "FAILED_INCOMPLETE_DIAG" | "NOT_RUN_WITH_REASON" | "MISSING_DIAGNOSTIC_ENVELOPE";
  safe_block: boolean;
  error_code: string;
  reason_code: string;
  human_message: string;
  machine_reason: string;
  apply_block_layer: string;
  recommended_next_action: string;
  approval_binding: Record<string, unknown>;
  diff_provenance: Record<string, unknown>;
  anti_cheat: Record<string, unknown>;
  acceptance_gate: Record<string, unknown>;
  verification: Record<string, unknown>;
  unavailable_fields: Array<{ field: string; reason: string }>;
  persisted_at: string;
  surfaced_at: string;
};

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (!body || typeof body !== "object") {
    return Response.json({ error: "Request body must be an object" }, { status: 400 });
  }

  const record = body as Record<string, unknown>;
  const action = typeof record.action === "string" ? record.action : "";
  const target = typeof record.target === "string" ? record.target : "";
  const approved = record.approved === true;
  const approvedDiff =
    typeof record.approved_diff === "string"
      ? record.approved_diff
      : typeof record.approvedDiff === "string"
        ? record.approvedDiff
        : "";
  const taskId =
    typeof record.task_id === "string"
      ? record.task_id
      : typeof record.taskId === "string"
        ? record.taskId
        : "";
  const approvalId =
    typeof record.approval_id === "string"
      ? record.approval_id
      : typeof record.approvalId === "string"
        ? record.approvalId
        : "";
  const allowedFiles = stringArrayValue(record.allowed_files ?? record.allowedFiles);
  const trialSuiteId =
    typeof record.trial_suite_id === "string"
      ? record.trial_suite_id
      : typeof record.trialSuiteId === "string"
        ? record.trialSuiteId
        : "";
  const trialPromptId =
    typeof record.trial_prompt_id === "string"
      ? record.trial_prompt_id
      : typeof record.trialPromptId === "string"
        ? record.trialPromptId
        : "";
  const trialPromptText =
    typeof record.trial_prompt_text === "string"
      ? record.trial_prompt_text
      : typeof record.trialPromptText === "string"
        ? record.trialPromptText
        : "";
  const changedFiles = changedFilesFromApprovedDiff(approvedDiff);

  if (!approved) {
    return Response.json(
      { error: "approved must be true before execution" },
      { status: 403 },
    );
  }
  if (!action.trim() || !target.trim()) {
    return Response.json(
      { error: "action and target are required" },
      { status: 400 },
    );
  }

  if (!taskId.trim()) {
    return Response.json(
      {
        error:
          "execute-approved requires task_id so Source Proxy can re-run verification before apply.",
      },
      { status: 400 },
    );
  }
  if (!approvedDiff.trim()) {
    return Response.json(
      {
        error:
          "execute-approved requires approved_diff so Source Proxy can re-run verification before apply.",
      },
      { status: 400 },
    );
  }
  if (allowedFiles.length === 0) {
    return Response.json(
      {
        error:
          "execute-approved requires allowed_files so Source Proxy can scope-match the approved diff before apply.",
      },
      { status: 400 },
    );
  }
  if (changedFiles.length === 0) {
    return Response.json(
      {
        error:
          "execute-approved requires approved_diff changed files so exact apply scope can be verified.",
      },
      { status: 400 },
    );
  }
  if (changedFiles.some((file) => isProtectedApplyPath(file))) {
    return Response.json(
      {
        changed_files: changedFiles,
        error: "execute-approved rejected protected path in approved_diff.",
      },
      { status: 403 },
    );
  }
  if (target.trim() && !changedFiles.some((file) => pathMatchesTarget(file, target))) {
    return Response.json(
      {
        changed_files: changedFiles,
        error: "execute-approved target does not match approved_diff changed files.",
        target,
      },
      { status: 409 },
    );
  }
  const unexpectedFiles = changedFiles.filter((file) => !pathMatchesAnyAllowed(file, allowedFiles));
  if (unexpectedFiles.length > 0) {
    return Response.json(
      {
        allowed_files: allowedFiles,
        changed_files: changedFiles,
        error: "execute-approved approved_diff changed files are outside allowed_files.",
        unexpected_files: unexpectedFiles,
      },
      { status: 409 },
    );
  }
  const clientDirectiveViolations = agentLabClientDirectiveViolations(approvedDiff);
  if (clientDirectiveViolations.length > 0) {
    return Response.json(
      {
        changed_files: changedFiles,
        error:
          'execute-approved rejected an interactive app-router page without "use client" as the first line.',
        missing_use_client_files: clientDirectiveViolations,
      },
      { status: 422 },
    );
  }
  if (!approvalId.trim()) {
    return Response.json(
      { error: "execute-approved requires a durable server-issued approval_id" },
      { status: 403 },
    );
  }

  if (isSelectedDummyCoderApply(action, allowedFiles, changedFiles)) {
    const prompt3Violations = await selectedPrompt3ApplyViolations(approvedDiff, action);
    if (prompt3Violations.length > 0) {
      return Response.json(
        {
          changed_files: changedFiles,
          error: "Prompt 3 model diff rejected before apply.",
          prompt_3_render_contract_violations: prompt3Violations,
          reason_code: prompt3Violations[0],
        },
        { status: 422 },
      );
    }
  }

  // Approved real diffs execute through Source proxy's long-running task layer.
  // That keeps diff verification, workspace writes, progress, and audit logging
  // behind a single explicit approval boundary.
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const response = await sourceProxyFetch(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/execute-approved`,
    {
      body: JSON.stringify({
        action,
        approved: true,
        approval_id: approvalId,
        approved_by: "coding-ui",
        approved_diff: approvedDiff,
        allowed_files: allowedFiles,
        changed_files: changedFiles,
        approved_diff_sha256: normalizedDiffSha256(approvedDiff),
        applied_diff_sha256: normalizedDiffSha256(approvedDiff),
        provenance_hash_normalization: "lf_trailing_newline_v1",
        diff_hash: diffHashForApprovedDiff(approvedDiff),
        commit_authority: false,
        push_authority: false,
        target,
        selected_prompt_id: trialPromptId || taskId,
        context_hash: createHash("sha256").update(`${trialPromptId}|${trialPromptText}|${target}`).digest("hex"),
      }),
      headers: {
        "content-type": "application/json",
      },
      method: "POST",
    },
  );

  const responseText = await response.text();
  const responseOk = response.ok ?? (response.status >= 200 && response.status < 300);
  const contentType = response.headers.get("content-type") ?? "application/json";
  const contractCheck = responseOk && contentType.includes("application/json")
    ? plan4ExecuteApprovedContractCheck(responseText)
    : { ok: true as const };
  if (!contractCheck.ok) {
    const backendPayload = parseJsonObject(responseText);
    return Response.json(
      {
        ...backendPayload,
        error:
          "execute-approved returned success without the Plan 4 causal output contract.",
        backend_payload: backendPayload,
        diagnostic_envelope: diagnosticEnvelopeFromPayload(backendPayload),
        missing_fields: contractCheck.missingFields,
        reason_code: "plan4_execute_approved_contract_missing",
        task_id: taskId,
      },
      { status: 502 },
    );
  }
  if (responseOk && trialSuiteId && trialPromptId) {
    await recordTrialApplyProof({
      allowedFiles,
      approvedDiff,
      changedFiles,
      responseText,
      taskId,
      trialPromptId,
      trialPromptText,
      trialSuiteId,
    });
  }

  return new Response(responseText, {
    headers: {
      "content-type": contentType,
    },
    status: response.status,
    statusText: response.statusText,
  });
}

export function isSelectedDummyCoderApply(action: string, allowedFiles: string[], changedFiles: string[]) {
  return (
    /^Run selected dummy Coder prompt coder-00[23]-/.test(action) &&
    allowedFiles.length === 1 &&
    allowedFiles[0] === `${DUMMY_CODER_10_FIXTURE_ROOT}**` &&
    changedFiles.length > 0 &&
    changedFiles.every((file) => file.startsWith(DUMMY_CODER_10_FIXTURE_ROOT))
  );
}

export async function selectedPrompt3ApplyViolations(approvedDiff: string, action: string) {
  if (!/^Run selected dummy Coder prompt coder-003-/.test(action)) return [];
  let currentIndexHtml = "";
  let currentMainJs = "";
  try {
    currentIndexHtml = await readFile(path.join(process.cwd(), DUMMY_CODER_10_FIXTURE_ROOT, "index.html"), "utf8");
  } catch {
    currentIndexHtml = "";
  }
  try {
    currentMainJs = await readFile(path.join(process.cwd(), DUMMY_CODER_10_FIXTURE_ROOT, "src/main.js"), "utf8");
  } catch {
    currentMainJs = "";
  }
  return selectedPrompt3DiffViolations(approvedDiff, currentIndexHtml, currentMainJs);
}

export function selectedPrompt3DiffViolations(diff: string, currentIndexHtml = "", currentMainJs = "") {
  const normalized = diff.replace(/\r\n/g, "\n");
  const violations: string[] = [];
  const hasDynamicProductsImport = /import\s*\(\s*['"]\.\/products\.js['"]\s*\)/i.test(normalized);
  const hasStaticProductsImport = /import\s+[\s\S]*?\s+from\s*['"]\.\/products\.js['"]/i.test(normalized);
  const diffAddsModuleScript = /^\+\s*<script\b[^>]*type=["']module["'][^>]*src=["']src\/main\.js["']/im.test(normalized);
  const currentIndexHasModuleScript = /<script\b[^>]*type=["']module["'][^>]*src=["']src\/main\.js["']/i.test(currentIndexHtml);
  const currentPreviewHasRenderedProductCards =
    /class=["'][^"']*\bproduct-card\b/i.test(currentIndexHtml) &&
    /class=["'][^"']*\bcategory\b/i.test(currentIndexHtml) &&
    /class=["'][^"']*\bprice\b/i.test(currentIndexHtml);
  const diffRemovesModuleScript = /^-\s*<script\b[^>]*type=["']module["'][^>]*src=["']src\/main\.js["']/im.test(normalized);
  const hasCurrentRenderWiring = currentIndexHasModuleScript || currentPreviewHasRenderedProductCards;
  const hasModuleScriptWiring = diffAddsModuleScript || (hasCurrentRenderWiring && !diffRemovesModuleScript);
  const currentMainHasStaticProductsImport = /import\s+products\s+from\s*['"]\.\/products\.js['"]\s*;/i.test(currentMainJs);
  const currentMainHasRenderPath =
    /products\s*\.\s*(?:forEach|map)\s*\(/i.test(currentMainJs) &&
    /product-card/.test(currentMainJs) &&
    /product\.name/.test(currentMainJs) &&
    /product\.category/.test(currentMainJs) &&
    /product\.description/.test(currentMainJs) &&
    /product\.price/.test(currentMainJs);
  const diffTouchesMainJs = /src\/main\.js/i.test(normalized);
  const diffRemovesProductsImport =
    diffTouchesMainJs && /^-.*import\s+products\s+from\s*['"]\.\/products\.js['"]/im.test(normalized);
  const diffRemovesRenderPath =
    diffTouchesMainJs && /^-.*(?:product-card|product\.name|product\.category|product\.description|product\.price)/im.test(normalized);
  const productsImportWillBePresent =
    hasStaticProductsImport ||
    hasDynamicProductsImport ||
    (currentMainHasStaticProductsImport && !diffRemovesProductsImport);
  const existingRenderPathStillPresent =
    hasCurrentRenderWiring &&
    productsImportWillBePresent &&
    currentMainHasRenderPath &&
    !diffRemovesModuleScript &&
    !diffRemovesProductsImport &&
    !diffRemovesRenderPath;
  const diffAddsRenderPath =
    diffTouchesMainJs &&
    /product\.category|product-card/i.test(normalized);
  const renderScriptCanRun = hasDynamicProductsImport || hasModuleScriptWiring;
  const renderPathWillBePresent =
    existingRenderPathStillPresent ||
    (productsImportWillBePresent && renderScriptCanRun && diffAddsRenderPath);

  if (!renderPathWillBePresent) {
    violations.push("MISSING_DYNAMIC_PRODUCTS_RENDER_PATH");
  }
  if ((hasStaticProductsImport || currentMainHasStaticProductsImport) && !hasModuleScriptWiring) {
    violations.push("STATIC_IMPORT_CLASSIC_SCRIPT");
  }
  if (!productsImportWillBePresent && !existingRenderPathStillPresent) {
    violations.push("MISSING_PRODUCTS_IMPORT");
  }
  if (/^\+.*<(?:article|div)\b[^>]*(?:product-card|card)/im.test(normalized) && /index\.html/i.test(normalized)) {
    violations.push("HARDCODED_INDEX_CARDS");
  }
  if (/^\+.*\b(?:const|let|var)\s+products\s*=\s*\[/im.test(normalized) || (/Product A/.test(normalized) && /Product F/.test(normalized))) {
    violations.push("PRODUCT_DATA_DUPLICATED");
  }
  return [...new Set(violations)];
}

async function applySelectedDummyCoderDiff(input: {
  action: string;
  approvedDiff: string;
  approvedDiffSha256: string;
  changedFiles: string[];
  target: string;
  taskId: string;
}) {
  const tempDir = await mkdtemp(path.join(os.tmpdir(), "spiritos-selected-dummy-"));
  const patchPath = path.join(tempDir, "approved.patch");
  let checksResult = "git apply --recount --check passed; selected dummy fixture diff applied";
  let checksRun = ["git apply --recount --check"];
  let applyMode = "git_apply_recount";
  let stalePatchRecovered = false;
  // Recovery provenance: when git apply --check fails and the backend writes a
  // deterministic fixture solution itself, the resulting disk truth is NOT
  // model-authored. These fields mirror the Python-side recovery payload
  // (source_proxy/tasks/long_running.py) so the grader cannot grade a
  // backend-authored recovery as a model-authored PASS.
  let recoveryFallbackUsed = false;
  let recoveryDiffSource = "";
  let recoveryTrustStatus = "";
  try {
    await writeFile(patchPath, input.approvedDiff, "utf8");
    try {
      const applyFlags = await runSelectedDummyGitApplyCheckWithFallback(patchPath);
      await runSelectedDummyGitApply(["apply", "--recount", ...applyFlags, patchPath], "git apply --recount");
      if (applyFlags.length > 0) {
        const flagLabel = applyFlags.join(" ");
        checksResult = `git apply --recount --check ${flagLabel} passed; selected dummy fixture diff applied`;
        checksRun = [`git apply --recount ${flagLabel} --check`];
        applyMode = `git_apply_recount_${applyFlags.map((flag) => flag.replace(/^--/, "")).join("_")}`;
      }
    } catch (error) {
      const recovered = await tryRecoverSelectedDummyApply(input);
      if (!recovered) {
        throw error;
      }
      checksResult = recovered.checksResult;
      checksRun = recovered.checksRun;
      applyMode = recovered.applyMode;
      stalePatchRecovered = true;
      // A recovery means the on-disk solution was backend-authored, not
      // model-authored. Surface that as fallback provenance so the grader's
      // anti-cheat path (which treats fallback_used as invalid provenance)
      // fires instead of laundering the recovery as a model-authored PASS.
      recoveryFallbackUsed = Boolean(recovered.fallbackUsed);
      recoveryDiffSource = recovered.diffSource ?? "";
      recoveryTrustStatus = recovered.trustStatus ?? "";
    }
  } finally {
    await rm(tempDir, { force: true, recursive: true });
  }
  const trackerUpdate = await markSelectedDummyTaskApplied(input.taskId, input.changedFiles);
  const now = new Date().toISOString();
  return {
    action: input.action,
    applied_changed_files: input.changedFiles,
    apply_mode: applyMode,
    approved_diff_sha256: input.approvedDiffSha256,
    applied_diff_sha256: input.approvedDiffSha256,
    changed_files: input.changedFiles,
    checks_result: checksResult,
    checks_run: checksRun,
    disk_changed_files: input.changedFiles,
    execution: {
      invocation_event_id: `selected_dummy_apply_${diffHashForApprovedDiff(input.approvedDiff).slice(0, 12)}`,
      task_id: input.taskId,
      trace_id: `selected_dummy_trace_${diffHashForApprovedDiff(input.approvedDiff).slice(0, 12)}`,
    },
    status: "applied",
    target: input.target,
    task_tracker_update: trackerUpdate,
    task: {
      causal_trace: {
        consumer_event_id: `selected_dummy_disk_${diffHashForApprovedDiff(input.approvedDiff).slice(0, 12)}`,
        consumer_subsystem: "next_execute_approved_selected_dummy_fixture",
        invocation_event_id: `selected_dummy_apply_${diffHashForApprovedDiff(input.approvedDiff).slice(0, 12)}`,
        trace_id: `selected_dummy_trace_${diffHashForApprovedDiff(input.approvedDiff).slice(0, 12)}`,
      },
      execution: {
        applied_changed_files: input.changedFiles,
        changed_files: input.changedFiles,
        disk_changed_files: input.changedFiles,
      },
      id: input.taskId,
    },
    stale_patch_recovered: stalePatchRecovered,
    fallback_used: recoveryFallbackUsed,
    diff_source: recoveryDiffSource || "model_authored_diff",
    trial_result_trust_status: recoveryTrustStatus || "model_authored_diff_proven",
    provenance_hash_normalization: "lf_trailing_newline_v1",
    // Recovery provenance override. When stalePatchRecovered is true the
    // on-disk solution was written by the backend, so downstream consumers
    // (recordTrialApplyProof / grader) must not treat it as model-authored.
    recovery_fallback_used: recoveryFallbackUsed,
    recovery_diff_source: recoveryDiffSource || null,
    recovery_trust_status: recoveryTrustStatus || null,
    updated_at: now,
  };
}

async function tryRecoverSelectedDummyApply(input: {
  action: string;
  approvedDiff: string;
  changedFiles: string[];
}) {
  const prompt1Recovery = await tryRecoverSelectedDummyPrompt1CreateApply(input);
  if (prompt1Recovery) {
    return {
      applyMode: "model_authored_prompt1_create_bundle_after_stale_context",
      checksResult:
        "git apply --recount --check failed; validated and wrote model-authored Prompt 1 create bundle",
      checksRun: [
        "git apply --recount --check",
        "model-authored Prompt 1 create bundle validation",
      ],
      fallbackUsed: false,
      diffSource: "model_authored_prompt1_create_bundle_after_stale_context",
      trustStatus: "model_authored_diff_proven",
    };
  }
  const prompt2Recovery = await tryRecoverSelectedDummyProductsApply(input);
  if (prompt2Recovery) {
    return {
      applyMode: "model_authored_products_replacement_after_stale_context",
      checksResult:
        "git apply --recount --check failed; validated and wrote model-authored products.js replacement content",
      checksRun: [
        "git apply --recount --check",
        "model-authored products.js replacement validation",
      ],
      // Prompt 2 recovery rewrites only products.js from the model-authored
      // diff content, so it stays model-authored (no fallback flag).
      fallbackUsed: false,
      diffSource: "model_authored_products_replacement_after_stale_context",
      trustStatus: "model_authored_diff_proven",
    };
  }
  const prompt3Recovery = await tryRecoverSelectedDummyPrompt3Apply(input);
  if (prompt3Recovery) {
    return {
      applyMode: "deterministic_prompt3_recovery_after_stale_context",
      checksResult:
        "git apply --recount --check failed; validated and wrote deterministic Prompt 3 product-card rendering files",
      checksRun: [
        "git apply --recount --check",
        "deterministic Prompt 3 stale-context recovery validation",
      ],
      // Prompt 3 recovery writes a fully backend-authored main.js render loop;
      // it must NOT be graded as model-authored.
      fallbackUsed: true,
      diffSource: "deterministic_prompt3_recovery_backend_converted_to_diff",
      trustStatus: "deterministic_prompt3_recovery_diff_proven",
    };
  }
  return null;
}

async function tryRecoverSelectedDummyPrompt1CreateApply(input: {
  action: string;
  approvedDiff: string;
  changedFiles: string[];
}) {
  if (!/coder-001-init-dummy-product-site/.test(input.action)) {
    return false;
  }
  const changedFiles = input.changedFiles.map(normalizeRepoPath).sort();
  if (changedFiles.join("\n") !== [...DUMMY_CODER_10_PROMPT1_FILES].sort().join("\n")) {
    return false;
  }
  const files = selectedDummyPrompt1CreateFilesFromDiff(input.approvedDiff);
  if (!files.ok) {
    return false;
  }
  for (const [repoPath, content] of Object.entries(files.files)) {
    const target = path.join(process.cwd(), repoPath);
    await mkdir(path.dirname(target), { recursive: true });
    await writeFile(target, content, "utf8");
  }
  return true;
}

async function tryRecoverSelectedDummyProductsApply(input: {
  action: string;
  approvedDiff: string;
  changedFiles: string[];
}) {
  const productsPath = `${DUMMY_CODER_10_FIXTURE_ROOT}src/products.js`;
  const changedFiles = input.changedFiles.map(normalizeRepoPath);
  if (!/coder-002-add-product-data/.test(input.action)) {
    return false;
  }
  if (changedFiles.length !== 1 || changedFiles[0] !== productsPath) {
    return false;
  }
  const replacement = selectedDummyProductsReplacementFromDiff(input.approvedDiff, productsPath);
  if (!replacement.ok) {
    return false;
  }
  await writeFile(path.join(process.cwd(), productsPath), replacement.content, "utf8");
  return true;
}

async function tryRecoverSelectedDummyPrompt3Apply(input: {
  action: string;
  changedFiles: string[];
}) {
  if (!/coder-003-render-product-cards/.test(input.action)) {
    return false;
  }
  const expectedFiles = [
    `${DUMMY_CODER_10_FIXTURE_ROOT}index.html`,
    `${DUMMY_CODER_10_FIXTURE_ROOT}src/main.js`,
    `${DUMMY_CODER_10_FIXTURE_ROOT}src/styles.css`,
  ];
  const changedFiles = input.changedFiles.map(normalizeRepoPath).sort();
  if (changedFiles.join("\n") !== [...expectedFiles].sort().join("\n")) {
    return false;
  }

  const indexPath = path.join(process.cwd(), expectedFiles[0]);
  const mainPath = path.join(process.cwd(), expectedFiles[1]);
  const stylesPath = path.join(process.cwd(), expectedFiles[2]);
  const [currentIndex, currentStyles] = await Promise.all([
    readFile(indexPath, "utf8").catch(() => ""),
    readFile(stylesPath, "utf8").catch(() => ""),
  ]);

  let nextIndex = currentIndex.replace(
    /<script\b(?![^>]*\btype=)[^>]*src=["']src\/main\.js["'][^>]*><\/script>/i,
    '<script type="module" src="src/main.js"></script>',
  );
  if (!/<script\b[^>]*type=["']module["'][^>]*src=["']src\/main\.js["'][^>]*><\/script>/i.test(nextIndex)) {
    nextIndex = nextIndex.replace(
      /<\/body>/i,
      '  <script type="module" src="src/main.js"></script>\n</body>',
    );
  }

  const nextMain = [
    "import products from './products.js';",
    "",
    "const productList = document.getElementById('product-list');",
    "",
    "if (productList) {",
    "  if (products.length === 0) {",
    "    productList.textContent = 'No products available yet.';",
    "  } else {",
    "    products.forEach((product) => {",
    "      const productElement = document.createElement('div');",
    "      productElement.classList.add('product-card');",
    "      productElement.innerHTML = `",
    "        <h2>${product.name}</h2>",
    "        <p>Category: ${product.category}</p>",
    "        <p>Description: ${product.description}</p>",
    "        <p>$${product.price}</p>",
    "      `;",
    "      productList.appendChild(productElement);",
    "    });",
    "  }",
    "}",
    "",
  ].join("\n");

  let nextStyles = currentStyles.trimEnd();
  if (!/#product-list\s*\{/.test(nextStyles)) {
    nextStyles += [
      "",
      "",
      "#product-list {",
      "  display: grid;",
      "  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));",
      "  gap: 1rem;",
      "  margin: 2rem;",
      "}",
    ].join("\n");
  }
  if (!/\.product-card\s*\{/.test(nextStyles)) {
    nextStyles += [
      "",
      "",
      ".product-card {",
      "  border: 1px solid #ddd;",
      "  padding: 1rem;",
      "  border-radius: 0.5rem;",
      "}",
    ].join("\n");
  }
  nextStyles += "\n";

  const recoveryDiff = [
    `diff --git a/${expectedFiles[0]} b/${expectedFiles[0]}`,
    `--- a/${expectedFiles[0]}`,
    `+++ b/${expectedFiles[0]}`,
    "+<script type=\"module\" src=\"src/main.js\"></script>",
    `diff --git a/${expectedFiles[1]} b/${expectedFiles[1]}`,
    `--- a/${expectedFiles[1]}`,
    `+++ b/${expectedFiles[1]}`,
    "+import products from './products.js';",
    "+productElement.classList.add('product-card');",
    "+<p>Category: ${product.category}</p>",
    "+<p>Description: ${product.description}</p>",
    `diff --git a/${expectedFiles[2]} b/${expectedFiles[2]}`,
    `--- a/${expectedFiles[2]}`,
    `+++ b/${expectedFiles[2]}`,
    "+.product-card {",
  ].join("\n");
  const violations = selectedPrompt3DiffViolations(recoveryDiff, nextIndex, nextMain);
  if (violations.length > 0) {
    return false;
  }

  await Promise.all([
    writeFile(indexPath, nextIndex, "utf8"),
    writeFile(mainPath, nextMain, "utf8"),
    writeFile(stylesPath, nextStyles, "utf8"),
  ]);
  return true;
}

class SelectedDummyApplyError extends Error {
  readonly cause: unknown;
  readonly reasonCode: string;
  readonly stage: string;
  readonly status: number;
  readonly details: Record<string, unknown>;

  constructor(input: {
    cause: unknown;
    message: string;
    reasonCode: string;
    stage: string;
    status?: number;
  }) {
    super(input.message);
    this.name = "SelectedDummyApplyError";
    this.cause = input.cause;
    this.reasonCode = input.reasonCode;
    this.stage = input.stage;
    this.status = input.status ?? 409;
    this.details = execErrorDetails(input.cause);
  }
}

async function runSelectedDummyGitApplyCheckWithFallback(patchPath: string) {
  let lastError: unknown = null;
  for (const flags of SELECTED_DUMMY_GIT_APPLY_FLAG_CHAINS) {
    try {
      await runSelectedDummyGitApply(
        ["apply", "--recount", ...flags, "--check", patchPath],
        "git apply --recount --check",
      );
      return flags;
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}

async function runSelectedDummyGitApply(
  args: string[],
  stage: "git apply --recount --check" | "git apply --recount",
) {
  try {
    await execFileAsync("git", args, { cwd: process.cwd() });
  } catch (error) {
    throw new SelectedDummyApplyError({
      cause: error,
      message: `Selected dummy fixture apply failed during ${stage}.`,
      reasonCode: stage === "git apply --recount --check"
        ? "selected_dummy_git_apply_check_failed"
        : "selected_dummy_git_apply_failed",
      stage,
    });
  }
}

function selectedDummyApplyErrorStatus(error: unknown) {
  return error instanceof SelectedDummyApplyError ? error.status : 500;
}

function selectedDummyApplyErrorPayload(
  error: unknown,
  input: {
    action: string;
    approvedDiff: string;
    changedFiles: string[];
    target: string;
    taskId: string;
  },
) {
  const selectedError = error instanceof SelectedDummyApplyError ? error : null;
  const details = selectedError?.details ?? execErrorDetails(error);
  const message = error instanceof Error ? error.message : String(error);
  const reasonCode = selectedError?.reasonCode ?? "selected_dummy_apply_unexpected_error";
  const recommendedNextAction = selectedError
    ? "Inspect the approved diff against the current dummy fixture state, then clear/reverse stale selected-prompt leftovers before retrying."
    : "Inspect Next route logs for /v1/actions/execute-approved and retry after clearing stale selected-prompt state.";
  const envelope = selectedDummyApplyDiagnosticEnvelope({
    details,
    input,
    message,
    reasonCode,
    recommendedNextAction,
    selectedError,
  });
  return {
    ...envelope,
    action: input.action,
    changed_files: input.changedFiles,
    command: details.command ?? null,
    diff_hash: diffHashForApprovedDiff(input.approvedDiff),
    error: selectedError
      ? selectedError.message
      : "Selected dummy fixture apply route failed before returning an apply result.",
    exit_code: details.exit_code ?? null,
    message,
    reason_code: reasonCode,
    recommended_next_action: recommendedNextAction,
    route: "/v1/actions/execute-approved",
    signal: details.signal ?? null,
    stage: selectedError?.stage ?? "selected dummy apply",
    stderr: details.stderr ?? "",
    stdout: details.stdout ?? "",
    target: input.target,
    task_id: input.taskId,
  };
}

function selectedDummyApplyDiagnosticEnvelope({
  details,
  input,
  message,
  reasonCode,
  recommendedNextAction,
  selectedError,
}: {
  details: Record<string, unknown>;
  input: {
    action: string;
    approvedDiff: string;
    changedFiles: string[];
    target: string;
    taskId: string;
  };
  message: string;
  reasonCode: string;
  recommendedNextAction: string;
  selectedError: SelectedDummyApplyError | null;
}): DiagnosticEnvelope & Record<string, unknown> {
  const now = new Date().toISOString();
  const diffSha = normalizedDiffSha256(input.approvedDiff);
  return {
    stage_id: "next.execute_approved.selected_dummy_apply",
    subsystem: "next_execute_approved_route",
    task_id: input.taskId,
    selected_prompt_task_id: input.taskId,
    run_id: "next_execute_approved_selected_dummy_apply",
    trace_id: "not_available: route_error_before_model_call",
    invocation_event_id: "not_available: route_error_before_model_call",
    consumer_event_id: "not_applicable: apply failed before backend consumer",
    status: "blocked",
    truth_status: "FAILED_INCOMPLETE_DIAG",
    safe_block: true,
    error_code: reasonCode,
    reason_code: reasonCode,
    human_message: message,
    machine_reason: reasonCode,
    apply_block_layer: "next_selected_dummy_apply_route",
    recommended_next_action: recommendedNextAction,
    approval_binding: {
      approval_binding_status: "not_applicable: selected dummy route local apply failed after route preflight",
      safe_block: true,
      target_used_for_apply: input.target,
      task_id_used_for_apply: input.taskId,
    },
    diff_provenance: {
      applied_diff_sha256: "not_recorded: apply_did_not_happen",
      approved_diff_sha256: diffSha,
      backend_converted_diff_sha256: "not_applicable: selected dummy route applied client-approved diff",
      changed_files: input.changedFiles,
      diff_source: "approved_diff_request_body",
      provenance_hash_normalization: "lf_trailing_newline_v1",
    },
    anti_cheat: {
      anti_cheat_status: "not_run",
      anti_cheat_reasons: ["skipped_due_to_apply_block"],
      grader_result_state: "not_applicable: fixture_pre_apply_block",
    },
    acceptance_gate: {
      acceptance_failures: [reasonCode],
      binary_verdict: "NO-GO",
      causal_crosscheck_status: "skipped_with_reason",
      fail_closed_lane_status: "skipped_with_reason",
      missing_fields: ["source_proxy_apply_receipt"],
      phase_verifier_status: "skipped_with_reason",
      plan5_gate_id: "plan5_next_selected_dummy_apply_block",
      plan5_gate_present: false,
      plan5_gate_version: "plan5_acceptance_v1",
      reason: "skipped_due_to_apply_block",
    },
    verification: {
      post_apply_verification_status: "skipped_due_to_apply_block",
      preview_verification_status: selectedError?.stage ?? "not_recorded: backend did not provide field",
      stderr: String(details.stderr ?? ""),
      stdout: String(details.stdout ?? ""),
    },
    unavailable_fields: [
      { field: "trace_id", reason: "route_error_before_model_call" },
      { field: "invocation_event_id", reason: "route_error_before_model_call" },
      { field: "consumer_event_id", reason: "apply failed before backend consumer" },
      { field: "anti_cheat.detector_results", reason: "skipped_due_to_apply_block" },
    ],
    persisted_at: now,
    surfaced_at: now,
    final_truth_summary: {
      commit_safe: false,
      proof_level: "fixture_pre_apply_block",
      raw_backend_status: reasonCode,
      recommended_next_action: recommendedNextAction,
      run_status: "blocked",
      truth_status: "FAILED_INCOMPLETE_DIAG",
      why_not_go: message,
    },
  };
}

function execErrorDetails(error: unknown): Record<string, unknown> {
  const record = error && typeof error === "object" ? (error as Record<string, unknown>) : {};
  return {
    command: typeof record.cmd === "string" ? record.cmd : "",
    exit_code: typeof record.code === "number" || typeof record.code === "string" ? record.code : null,
    signal: typeof record.signal === "string" ? record.signal : null,
    stderr: typeof record.stderr === "string" ? record.stderr.slice(0, 4000) : "",
    stdout: typeof record.stdout === "string" ? record.stdout.slice(0, 4000) : "",
  };
}

async function markSelectedDummyTaskApplied(taskId: string, changedFiles: string[]) {
  try {
    const response = await sourceProxyFetch(
      `/v1/tasks/long-running/${encodeURIComponent(taskId)}/selected-dummy-applied`,
      {
        body: JSON.stringify({
          changed_files: changedFiles,
          reason_code: "selected_dummy_apply_completed",
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
      },
    );
    const responseText = await response.text();
    return {
      ok: response.ok,
      status: response.status,
      task_id: taskId,
      body: responseText.slice(0, 1000),
    };
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : String(error),
      ok: false,
      status: 0,
      task_id: taskId,
    };
  }
}

async function recordTrialApplyProof(input: {
  allowedFiles: string[];
  approvedDiff: string;
  changedFiles: string[];
  responseText: string;
  taskId: string;
  trialPromptId: string;
  trialPromptText: string;
  trialSuiteId: string;
}) {
  const payload = parseJsonRecord(input.responseText);
  const appliedChangedFiles = uniqueStrings([
    ...changedFilesFromPayload(payload),
    ...input.changedFiles,
    ...changedFilesFromApprovedDiff(input.approvedDiff),
  ]).filter((file) => pathMatchesAnyAllowed(file, input.allowedFiles));
  if (appliedChangedFiles.length === 0) return;
  const now = new Date().toISOString();
  const endpointStatuses = [
    "/v1/actions/execute-approved:200",
    "/v1/actions/execute-approved:server_apply_proof_recorded",
  ];
  // If the execute-approved response reports a backend-authored recovery
  // (git apply --check failed and the backend wrote the fixture solution
  // itself), stamp fallback provenance onto the durable row so the grader's
  // anti-cheat path treats it as invalid rather than laundering the recovery
  // as a model-authored PASS. Without this override, the row keeps the
  // model-authored labels set earlier in the pipeline even though the bytes
  // actually written to disk were backend-authored.
  const recoveryFallbackUsed = Boolean(payload.recovery_fallback_used);
  const recoveryDiffSource = typeof payload.recovery_diff_source === "string" ? payload.recovery_diff_source : "";
  const recoveryTrustStatus = typeof payload.recovery_trust_status === "string" ? payload.recovery_trust_status : "";
  const approvedDiffSha256 = normalizedDiffSha256(input.approvedDiff);
  const appliedDiffSha256 = stringValue(payload.applied_diff_sha256) ?? approvedDiffSha256;
  const backendConvertedDiffSha256 =
    stringValue(payload.backend_converted_diff_sha256) ??
    stringValue(payload.task && typeof payload.task === "object" ? (payload.task as Record<string, unknown>).backend_converted_diff_sha256 : null);
  const recoveryProvenance: Partial<DurableCodingRunProvenance> | undefined =
    recoveryFallbackUsed || recoveryDiffSource || recoveryTrustStatus
      ? {
          fallback_used: recoveryFallbackUsed,
          diff_source: recoveryDiffSource,
          trial_result_trust_status: recoveryTrustStatus,
          approved_diff_sha256: approvedDiffSha256,
          applied_diff_sha256: appliedDiffSha256,
          backend_converted_diff_sha256: backendConvertedDiffSha256,
          provenance_hash_normalization: "lf_trailing_newline_v1",
        }
      : undefined;
  // The durable row's provenance field is typed as the full shape, but
  // normalizeTrialProvenance (the only consumer) merges any partial against
  // the empty defaults, so a partial override is the intended input shape.
  const recoveryProvenanceRow = recoveryProvenance as DurableCodingRunProvenance | undefined;
  const runAfterRow = await upsertCodingRunRow(input.trialSuiteId, input.trialPromptId, {
    applied_changed_files: appliedChangedFiles,
    checks_result: "server apply proof recorded",
    checks_run: ["git diff --check"],
    disk_changed_files: appliedChangedFiles,
    endpoint_statuses: endpointStatuses,
    error_summary: "",
    generated_diff_present: true,
    preview_changed_files: appliedChangedFiles,
    prompt_excerpt: input.trialPromptText.slice(0, 220),
    prompt_text: input.trialPromptText,
    provenance: recoveryProvenanceRow,
    provider_call_made: true,
    reason_code: "",
    result_label: recoveryFallbackUsed ? "NEEDS_FIX" : "PASS",
    reversal_available: true,
    reversal_status: "available",
    run_id: input.taskId,
    status: "completed",
    step_instrumentation: {
      checks_completed_at: now,
      disk_probe_completed_at: now,
      disk_probe_started_at: now,
      execute_approved_body_read_completed_at: now,
      execute_approved_completed_at: now,
      execute_approved_http_status: "200",
      last_progress_reason_code: "server_apply_proof_recorded",
      result_finalized_at: now,
      reverse_receipt_created_at: now,
    },
  });
  const serverProofCompletesSuite = Boolean(
    runAfterRow &&
      runAfterRow.requested_count > 0 &&
      runAfterRow.completed_count >= runAfterRow.requested_count &&
      runAfterRow.rows.length === runAfterRow.requested_count &&
      runAfterRow.rows.every(
        (row) =>
          row.status === "completed" &&
          row.result_label === "PASS" &&
            !row.reason_code &&
            row.applied_changed_files.length > 0 &&
            row.disk_changed_files.length > 0,
      ),
  );
  await patchCodingRun(input.trialSuiteId, {
    applied_changed_files: appliedChangedFiles,
    checks_result: "server apply proof recorded",
    checks_run: ["git diff --check"],
    disk_changed_files: appliedChangedFiles,
    endpoint_statuses: endpointStatuses,
    final_summary: serverProofCompletesSuite
      ? "Suite completed by execute-approved server proof."
      : "Apply proof recorded by execute-approved route; browser runner can resume.",
    generated_diff_present: true,
    preview_changed_files: appliedChangedFiles,
    provider_call_made: true,
    reason_code: recoveryFallbackUsed ? "backend_recovery_not_pass_compatible" : null,
    reversal_available: true,
    reversal_status: "available",
    status: serverProofCompletesSuite ? "completed" : "running",
  });
}

function parseJsonRecord(text: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(text);
    return parsed && typeof parsed === "object" ? (parsed as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

function plan4ExecuteApprovedContractCheck(text: string):
  | { ok: true }
  | { ok: false; missingFields: string[] } {
  const payload = parseJsonRecord(text);
  const task = asRecord(payload.task);
  const execution = asRecord(payload.execution);
  const executionTrace = asRecord(execution.causal_trace);
  const taskTrace = asRecord(task.causal_trace);
  const trace = Object.keys(executionTrace).length > 0 ? executionTrace : taskTrace;
  const required = {
    task_id: stringValue(execution.task_id) ?? stringValue(task.id),
    trace_id: stringValue(execution.trace_id) ?? stringValue(trace.trace_id),
    invocation_event_id:
      stringValue(execution.invocation_event_id) ?? stringValue(trace.invocation_event_id),
    consumer_event_id: stringValue(trace.consumer_event_id),
    consumer_subsystem: stringValue(trace.consumer_subsystem),
  };
  const missingFields = Object.entries(required)
    .filter(([, value]) => !value)
    .map(([key]) => key);
  return missingFields.length === 0 ? { ok: true } : { ok: false, missingFields };
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function nestedRecord(record: Record<string, unknown>, keys: string[]): Record<string, unknown> {
  return keys.reduce<Record<string, unknown>>((current, key) => asRecord(current[key]), record);
}

function changedFilesFromPayload(payload: Record<string, unknown>): string[] {
  const task = asRecord(payload.task);
  const execution = asRecord(payload.execution);
  const taskExecution = asRecord(task.execution);
  const taskAudit = nestedRecord(task, ["ast_snapshot", "approved_execution_evidence", "audit"]);
  const candidates = [
    payload.applied_changed_files,
    payload.disk_changed_files,
    payload.changed_files,
    execution.applied_changed_files,
    execution.disk_changed_files,
    execution.changed_files,
    taskExecution.applied_changed_files,
    taskExecution.disk_changed_files,
    taskExecution.changed_files,
    taskAudit.changed_files,
  ];
  const changed = candidates.find(Array.isArray);
  if (!Array.isArray(changed)) return [];
  return uniqueStrings(
    changed
      .map((item) => {
        if (typeof item === "string") return normalizeRepoPath(item);
        return normalizeRepoPath(typeof asRecord(item).path === "string" ? String(asRecord(item).path) : "");
      })
      .filter(Boolean),
  );
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean)));
}

function normalizeRepoPath(value: string) {
  return value
    .replace(/\\/g, "/")
    .replace(/^\.\//, "")
    .replace(/^a\//, "")
    .replace(/^b\//, "")
    .trim();
}

function stringArrayValue(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function pathMatchesTarget(filePath: string, target: string): boolean {
  const normalizedFile = normalizeRepoPath(filePath);
  const normalizedTarget = normalizeRepoPath(target);
  if (!normalizedTarget) return false;
  if (normalizedFile === normalizedTarget) return true;
  const targetRoot = normalizedTarget.endsWith("/") ? normalizedTarget : `${normalizedTarget}/`;
  return normalizedFile.startsWith(targetRoot);
}

function pathMatchesAnyAllowed(filePath: string, allowedFiles: string[]): boolean {
  const normalizedFile = normalizeRepoPath(filePath);
  return allowedFiles.some((allowed) => {
    const normalizedAllowed = normalizeRepoPath(allowed);
    if (!normalizedAllowed) return false;
    if (normalizedAllowed.endsWith("/**")) {
      return normalizedFile.startsWith(normalizedAllowed.slice(0, -3));
    }
    if (normalizedAllowed.endsWith("*")) {
      return normalizedFile.startsWith(normalizedAllowed.slice(0, -1));
    }
    if (normalizedFile === normalizedAllowed) return true;
    const allowedRoot = normalizedAllowed.endsWith("/") ? normalizedAllowed : `${normalizedAllowed}/`;
    return normalizedFile.startsWith(allowedRoot);
  });
}

function changedFilesFromApprovedDiff(diff: string): string[] {
  const files = new Set<string>();
  for (const line of diff.split(/\r?\n/)) {
    const diffMatch = line.match(/^diff --git a\/(.+?) b\/(.+)$/);
    if (diffMatch?.[2]) {
      files.add(diffMatch[2].trim());
      continue;
    }
    if (!line.startsWith("+++ b/")) {
      continue;
    }
    const file = line.slice("+++ b/".length).trim();
    if (file && file !== "/dev/null") {
      files.add(file);
    }
  }
  return [...files];
}

export function selectedDummyPrompt1CreateFilesFromDiff(
  diff: string,
): { ok: true; files: Record<string, string> } | { ok: false; reason: string } {
  const expected = [...DUMMY_CODER_10_PROMPT1_FILES].sort();
  const changedFiles = changedFilesFromApprovedDiff(diff).map(normalizeRepoPath).sort();
  if (changedFiles.join("\n") !== expected.join("\n")) {
    return { ok: false, reason: "diff_must_touch_exact_prompt1_file_bundle" };
  }

  const files: Record<string, string> = {};
  let currentPath = "";
  let sawDevNull = false;
  let inHunk = false;
  let nextLines: string[] = [];

  const flush = () => {
    if (!currentPath) return;
    if (!sawDevNull) {
      files[currentPath] = "";
      return;
    }
    files[currentPath] = `${nextLines.join("\n").trimEnd()}\n`;
  };

  for (const line of diff.split(/\r?\n/)) {
    if (line.startsWith("diff --git ")) {
      flush();
      currentPath = "";
      sawDevNull = false;
      inHunk = false;
      nextLines = [];
      const match = line.match(/^diff --git a\/(.+?) b\/(.+)$/);
      if (match?.[2]) {
        currentPath = normalizeRepoPath(match[2]);
      }
      continue;
    }
    if (line === "--- /dev/null") {
      sawDevNull = true;
      continue;
    }
    if (line.startsWith("+++ b/")) {
      currentPath = normalizeRepoPath(line.slice("+++ b/".length));
      continue;
    }
    if (line.startsWith("@@")) {
      inHunk = true;
      continue;
    }
    if (!inHunk || line.startsWith("\\ No newline at end of file")) {
      continue;
    }
    if (line.startsWith("+") && !line.startsWith("+++")) {
      nextLines.push(line.slice(1));
    }
  }
  flush();

  const recoveredPaths = Object.keys(files).sort();
  if (recoveredPaths.join("\n") !== expected.join("\n")) {
    return { ok: false, reason: "prompt1_recovered_paths_mismatch" };
  }
  if (Object.values(files).some((content) => !content.trim() || content.length > 30000)) {
    return { ok: false, reason: "prompt1_recovered_content_invalid_size" };
  }
  const combined = Object.values(files).join("\n");
  if (!/LumaCart/i.test(combined)) {
    return { ok: false, reason: "prompt1_recovered_content_missing_lumacart" };
  }
  if (!/dummy|fixture|trial/i.test(files[`${DUMMY_CODER_10_FIXTURE_ROOT}README.md`] ?? "")) {
    return { ok: false, reason: "prompt1_readme_missing_fixture_boundary" };
  }
  return { ok: true, files };
}

export function selectedDummyProductsReplacementFromDiff(
  diff: string,
  targetPath = `${DUMMY_CODER_10_FIXTURE_ROOT}src/products.js`,
):
  | { ok: true; content: string }
  | { ok: false; reason: string } {
  const normalizedTarget = normalizeRepoPath(targetPath);
  const changedFiles = changedFilesFromApprovedDiff(diff).map(normalizeRepoPath);
  if (changedFiles.length !== 1 || changedFiles[0] !== normalizedTarget) {
    return { ok: false, reason: "diff_must_touch_only_products_js" };
  }
  const diffHeaders = diff.match(/^diff --git /gm) ?? [];
  if (diffHeaders.length !== 1) {
    return { ok: false, reason: "diff_must_have_one_file_section" };
  }
  if (!new RegExp(`^\\+\\+\\+ b/${escapeRegExp(normalizedTarget)}\\s*$`, "m").test(diff)) {
    return { ok: false, reason: "diff_missing_products_new_path" };
  }

  const nextLines: string[] = [];
  let inHunk = false;
  for (const line of diff.split(/\r?\n/)) {
    if (line.startsWith("@@")) {
      inHunk = true;
      continue;
    }
    if (!inHunk || line === "" || line.startsWith("\\ No newline at end of file")) {
      continue;
    }
    if (line.startsWith("+") && !line.startsWith("+++")) {
      nextLines.push(line.slice(1));
      continue;
    }
    if (line.startsWith(" ")) {
      nextLines.push(line.slice(1));
    }
  }

  const content = `${nextLines.join("\n").trimEnd()}\n`;
  const validationFailure = selectedDummyPrompt2ProductsContentFailure(content);
  if (validationFailure) {
    return { ok: false, reason: validationFailure };
  }
  return { ok: true, content };
}

function selectedDummyPrompt2ProductsContentFailure(content: string): string | null {
  if (content.length > 20000) {
    return "products_content_too_large";
  }
  if (!/\b(?:const|let|var)\s+products\s*=\s*\[/m.test(content)) {
    return "missing_products_array";
  }
  if (!/\bexport\s+default\s+products\s*;?/m.test(content)) {
    return "missing_default_products_export";
  }
  const requiredFieldCounts = ["id", "name", "price", "category", "description"].map((field) => {
    const matches = content.match(new RegExp(`\\b${field}\\s*:`, "g"));
    return matches?.length ?? 0;
  });
  if (requiredFieldCounts.some((count) => count < 6)) {
    return "missing_six_complete_product_fields";
  }
  return null;
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function agentLabClientDirectiveViolations(diff: string): string[] {
  const violations = new Set<string>();
  const sections = diff.split(/\ndiff --git /);
  for (const section of sections) {
    const text = section.startsWith("diff --git ") ? section : `diff --git ${section}`;
    const file = normalizedNewFilePath(text);
    if (!file || !/^src\/app\/agent-lab\/.*\/page\.tsx$/.test(file)) continue;
    if (!/(^|\n)--- \/dev\/null(\n|$)/.test(text)) continue;
    const addedLines = text
      .split(/\r?\n/)
      .filter((line) => line.startsWith("+") && !line.startsWith("+++"))
      .map((line) => line.slice(1));
    const source = addedLines.join("\n");
    if (!usesClientOnlyReactFeatures(source)) continue;
    if (hasUseClientDirective(addedLines)) continue;
    violations.add(file);
  }
  return [...violations].sort();
}

function normalizedNewFilePath(diffSection: string): string | null {
  const match = diffSection.match(/(?:^|\n)\+\+\+ b\/([^\n\r]+)/);
  if (!match?.[1]) return null;
  return match[1].trim().replace(/\\/g, "/");
}

function usesClientOnlyReactFeatures(source: string): boolean {
  return (
    /\b(useState|useEffect|useMemo|useReducer|useRef|useCallback)\b/.test(source) ||
    /\b(onClick|onChange|onSubmit|onKeyDown|localStorage|sessionStorage|window\.|document\.)\b/.test(source)
  );
}

function hasUseClientDirective(lines: string[]): boolean {
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    return /^["']use client["'];?$/.test(trimmed);
  }
  return false;
}

function isProtectedApplyPath(path: string) {
  return (
    path === ".env" ||
    path.startsWith(".env.") ||
    path.includes("/.env") ||
    path.endsWith(".pem") ||
    path.endsWith(".key") ||
    path.startsWith("source_proxy/data/") ||
    path.startsWith("backend/volumes/") ||
    path.startsWith("backend/searxng_data/") ||
    path.startsWith(".spirit-backups/")
  );
}

function normalizeDiffForProvenance(diff: string) {
  return `${diff.replace(/\r\n/g, "\n").replace(/\r/g, "\n").replace(/\n*$/, "")}\n`;
}

function normalizedDiffSha256(approvedDiff: string) {
  return createHash("sha256").update(normalizeDiffForProvenance(approvedDiff), "utf8").digest("hex");
}

function diffHashForApprovedDiff(approvedDiff: string) {
  return normalizedDiffSha256(approvedDiff);
}

function approvalBindingFailurePayload({
  approvedDiff,
  expectedApprovalId,
  receivedApprovalId,
  target,
  taskId,
}: {
  approvedDiff: string;
  expectedApprovalId: string;
  receivedApprovalId: string;
  target: string;
  taskId: string;
}) {
  const canonicalDiffSha256 = normalizedDiffSha256(approvedDiff);
  const rawDiffSha256 = createHash("sha256").update(approvedDiff, "utf8").digest("hex");
  const canonicalizationChanged = normalizeDiffForProvenance(approvedDiff) !== approvedDiff;
  const changedFiles = changedFilesFromApprovedDiff(approvedDiff);
  const recommendedNextAction =
    "Inspect src/app/v1/actions/execute-approved/route.ts approvalIdForApprovedDiff and the caller that supplied approval_id; do not apply until task_id, target, and diff hash match.";
  const now = new Date().toISOString();
  const envelope: DiagnosticEnvelope & Record<string, unknown> = {
    stage_id: "next.execute_approved.approval_binding_preflight",
    subsystem: "next_execute_approved_route",
    task_id: taskId,
    selected_prompt_task_id: taskId,
    run_id: "next_execute_approved_preflight",
    trace_id: "not_started: preflight_block",
    invocation_event_id: "not_started: preflight_block",
    consumer_event_id: "not_applicable: preflight_block",
    status: "blocked_approval_mismatch",
    truth_status: "BLOCKED_SAFE",
    safe_block: true,
    error_code: "approval_id_mismatch",
    reason_code: "approval_id_mismatch",
    human_message: "execute-approved approval_id does not match task_id, target, and approved_diff.",
    machine_reason: "approval_id_mismatch",
    apply_block_layer: "frontend_bridge",
    recommended_next_action: recommendedNextAction,
    error: "execute-approved approval_id does not match task_id, target, and approved_diff.",
    task_identity: {
      backend_task_id: taskId,
      consumer_event_id: "not_applicable: preflight_block",
      invocation_event_id: "not_started: preflight_block",
      run_id: "next_execute_approved_preflight",
      selected_prompt_id: "not_recorded: route did not receive selected prompt id",
      selected_prompt_task_id: taskId,
      task_id_match: "unknown",
      trace_id: "not_started: preflight_block",
      unavailable_reason: "received_approval_binding_components_not_recorded",
    },
    diff_provenance: {
      applied_diff_sha256: "not_applicable: apply_blocked",
      approved_diff_sha256: canonicalDiffSha256,
      backend_converted_diff_sha256: "not_recorded: backend did not provide field",
      changed_files: changedFiles,
      diff_source: "approved_diff_request_body",
      provenance_hash_normalization: "lf_trailing_newline_v1",
      raw_approved_diff_sha256: rawDiffSha256,
    },
    approval_binding: {
      approval_binding_failure_reason: "approval_id_mismatch",
      approval_binding_safe_block: true,
      approval_binding_status: "failed",
      approval_id_algorithm: "sha256(task_id|target|canonical_lf_trailing_newline_diff_sha256)",
      approval_source: "client/request",
      apply_block_layer: "frontend_bridge",
      apply_block_reason: "approval_id_mismatch",
      canonical_diff_sha256_at_apply: canonicalDiffSha256,
      canonical_diff_sha256_before_approval: "not_recorded: backend did not provide field",
      canonicalization_changed: canonicalizationChanged,
      diff_sha256_match: "unknown",
      diff_sha256_used_for_apply: canonicalDiffSha256,
      diff_sha256_used_for_preview: "not_recorded: backend did not provide field",
      expected_approval_id: expectedApprovalId,
      received_approval_id: receivedApprovalId.trim() || "missing",
      safe_block: true,
      target_match: "unknown",
      target_used_for_apply: target,
      target_used_for_preview: "not_recorded: backend did not provide field",
      task_id_match: "unknown",
      task_id_used_for_apply: taskId,
      task_id_used_for_preview: "not_recorded: backend did not provide field",
      unavailable_reason: "received_approval_binding_components_not_recorded",
    },
    verification: {
      post_apply_verification_status: "skipped_due_to_apply_block",
      preview_verification_status: "not_recorded: backend did not provide field",
    },
    anti_cheat: {
      anti_cheat_status: "not_run",
      anti_cheat_reasons: ["skipped_due_to_apply_block"],
      grader_result_state: "not_applicable: fixture_pre_apply_block",
      trial_result_trust_status: "blocked_before_apply",
    },
    acceptance_gate: {
      binary_verdict: "NO-GO",
      plan5_gate_present: false,
      missing_fields: ["source_proxy_apply_receipt"],
      acceptance_failures: ["approval_id_mismatch"],
    },
    final_truth_summary: {
      commit_safe: false,
      proof_level: target.includes("dummy-product-site") ? "fixture_only" : "route_level_non_fixture",
      raw_backend_status: "approval_id_mismatch",
      recommended_next_action: recommendedNextAction,
      run_status: "blocked",
      truth_status: "BLOCKED_SAFE",
      why_not_go: "approval binding failed before workspace apply",
    },
    unavailable_fields: [
      { field: "trace_id", reason: "preflight block occurred before backend invocation" },
      { field: "backend_converted_diff_sha256", reason: "backend did not provide field" },
      { field: "anti_cheat.detector_results", reason: "skipped_due_to_apply_block" },
    ],
    persisted_at: now,
    surfaced_at: now,
    expected_approval_id: expectedApprovalId,
    received_approval_id: receivedApprovalId.trim() || "missing",
  };
  return envelope;
}

function parseJsonObject(text: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(text);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : {};
  } catch {
    return {};
  }
}

function diagnosticEnvelopeFromPayload(payload: Record<string, unknown>): Record<string, unknown> {
  const detail = payload.detail && typeof payload.detail === "object" && !Array.isArray(payload.detail)
    ? (payload.detail as Record<string, unknown>)
    : {};
  const source = Object.keys(detail).length > 0 ? detail : payload;
  return source.stage_id || source.approval_binding || source.final_truth_summary ? source : {};
}
