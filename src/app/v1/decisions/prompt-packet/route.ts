import { mergeRepoFirstResearchSources } from "@/app/v1/decisions/_repo-research";
import { codingTargetPlugin } from "@/lib/coding/target-plugins";
import { sourceProxyFetch, sourceProxyLongJsonFetch } from "@/lib/source-proxy-origin";

import { readFile } from "node:fs/promises";
import path from "node:path";

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const startedAt = Date.now();
  let bodyText = await request.text();
  bodyText = await enrichPrompt3FixtureContext(bodyText);
  const prompt1AlreadySatisfied = await prompt1AlreadySatisfiedPayload(bodyText);
  if (prompt1AlreadySatisfied) {
    return Response.json(prompt1AlreadySatisfied);
  }
  const prompt3AlreadySatisfied = await prompt3AlreadySatisfiedPayload(bodyText);
  if (prompt3AlreadySatisfied) {
    return Response.json(prompt3AlreadySatisfied);
  }
  const directDocsOnlyPreview = await docsOnlyPreviewPayload(bodyText, {
    reason_code: "docs_only_bff_direct_preview",
    status: "preview_ready",
  });
  if (directDocsOnlyPreview) {
    return Response.json(JSON.parse(directDocsOnlyPreview));
  }

  let response;
  try {
    response = await sourceProxyLongJsonFetch("/v1/decisions/prompt-packet", {
      body: bodyText,
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
      method: "POST",
    });
  } catch (error) {
    return promptPacketTransportBlockedResponse(
      bodyText,
      error,
      "source_proxy_prompt_packet_fetch",
      startedAt,
      502,
    );
  }

  let responseText: string;
  try {
    responseText = await response.text();
  } catch (error) {
    return promptPacketTransportBlockedResponse(
      bodyText,
      error,
      "source_proxy_prompt_packet_body_read",
      startedAt,
      504,
      {
        source_proxy_status: response.status,
        source_proxy_status_text: response.statusText,
      },
    );
  }
  const contentType = response.headers.get("content-type") ?? "application/json";
  let body =
    contentType.includes("application/json") && response.ok
      ? await enrichProviderModelTruthFromStatus(
          mergeRepoFirstResearchSources(bodyText, responseText),
        )
      : responseText;
  if (contentType.includes("application/json") && response.ok) {
    body = (await docsOnlyFallbackPreview(bodyText, body)) ?? body;
  }

  return new Response(body, {
    headers: {
      "content-type": contentType,
    },
    status: response.status,
    statusText: response.statusText,
  });
}

type JsonRecord = Record<string, unknown>;

function promptPacketTransportBlockedResponse(
  bodyText: string,
  error: unknown,
  timeoutStage: "source_proxy_prompt_packet_fetch" | "source_proxy_prompt_packet_body_read",
  startedAt: number,
  status: number,
  upstream: JsonRecord = {},
) {
  const metadata = promptPacketRequestMetadata(bodyText);
  const detail = error instanceof Error ? error.message : "Unknown connection error.";
  const reasonCode =
    timeoutStage === "source_proxy_prompt_packet_body_read"
      ? "source_proxy_prompt_packet_body_read_failed"
      : "source_proxy_prompt_packet_fetch_failed";
  const errorText =
    timeoutStage === "source_proxy_prompt_packet_body_read"
      ? "The coding page lost the Source Proxy long response before a prompt packet body was returned."
      : "The coding page could not reach the Source Proxy prompt-packet endpoint.";

  return Response.json(
    {
      error: errorText,
      detail,
      status: "blocked",
      prompt_packet_status: "blocked",
      terminal_verdict: "BLOCKED_TIMEOUT",
      result_label: "BLOCKED",
      reason_code: reasonCode,
      blocked_reason: errorText,
      needed_context:
        "Retry the selected prompt after checking the active long-running task status; do not treat this as a model-authored diff.",
      proposed_diff: "",
      generation_source: "none",
      scaffold_used: false,
      fallback_used: false,
      selected_prompt_id: metadata.selected_prompt_id,
      selected_prompt_number: metadata.selected_prompt_number,
      task_id: metadata.task_id,
      active_task_id: metadata.task_id,
      selected_target: metadata.selected_target,
      target: metadata.selected_target,
      target_files: metadata.target_files,
      allowed_files: metadata.allowed_files,
      wants_implementation: metadata.wants_implementation,
      coder_diagnostics: {
        ...upstream,
        timeout_stage: timeoutStage,
        production_time_ms: Date.now() - startedAt,
        reason_code: reasonCode,
        error_type: error instanceof Error ? error.name : typeof error,
        error_message: detail,
      },
    },
    { status },
  );
}

function promptPacketRequestMetadata(bodyText: string) {
  let payload: unknown;
  try {
    payload = JSON.parse(bodyText);
  } catch {
    payload = null;
  }
  const record = isRecord(payload) ? payload : {};
  const selectedPromptId =
    stringFromUnknown(record.selected_prompt_id) ?? stringFromUnknown(record.trial_prompt_id);
  return {
    allowed_files: stringArrayFromUnknown(record.allowed_files),
    selected_prompt_id: selectedPromptId,
    selected_prompt_number: numberFromUnknown(record.selected_prompt_number) ?? promptNumberFromId(selectedPromptId),
    selected_target:
      stringFromUnknown(record.selected_target) ??
      stringArrayFromUnknown(record.target_files)[0] ??
      stringFromUnknown(record.target_file) ??
      "",
    target_files: stringArrayFromUnknown(record.target_files),
    task_id:
      stringFromUnknown(record.active_task_id) ??
      stringFromUnknown(record.task_id) ??
      "",
    wants_implementation: record.wants_implementation === true,
  };
}

function stringArrayFromUnknown(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function numberFromUnknown(value: unknown) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string" || !value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function promptNumberFromId(promptId: string | null) {
  if (!promptId) return null;
  const match = promptId.match(/coder-00(\d)-/);
  return match ? Number(match[1]) : null;
}

async function docsOnlyPreviewPayload(
  _bodyText: string,
  _overrides: JsonRecord,
): Promise<string | null> {
  return null;
}

async function docsOnlyFallbackPreview(
  _bodyText: string,
  _responseBodyText: string,
): Promise<string | null> {
  return null;
}

async function enrichPrompt3FixtureContext(bodyText: string) {
  let payload: unknown;
  try {
    payload = JSON.parse(bodyText);
  } catch {
    return bodyText;
  }
  if (!isRecord(payload)) return bodyText;
  const selectedPromptId =
    stringFromUnknown(payload.selected_prompt_id) ?? stringFromUnknown(payload.trial_prompt_id);
  if (selectedPromptId !== "coder-003-render-product-cards") return bodyText;

  const context = await readPrompt3FixtureContext();
  const task = stringFromUnknown(payload.task) ?? stringFromUnknown(payload.prompt) ?? "";
  const enrichedTask = [
    task,
    "",
    "Prompt 3 fixture context:",
    "src/products.js exists and is the source of truth. Import/read/render all products from that module.",
    "Product object fields available: name, price, category, description.",
    "Allowed write root: tests/ui-agent-trials/fixtures/dummy-product-site/.",
    "Forbidden paths: real app files, Source Proxy files, docs, root package files, and files outside the dummy root.",
    "Do not duplicate the product array or hardcode product cards in index.html.",
    "Option A is mandatory: change index.html to load src/main.js with <script type=\"module\" src=\"src/main.js\"></script>.",
    "src/main.js must statically import products with import products from './products.js'; and render all exported products dynamically.",
    "Do not use dynamic import(). Cards must show name, price, category, and description.",
    "src/styles.css may be updated for a simple responsive card grid.",
    `Current index.html:\n${context.indexHtml}`,
    `Current src/main.js:\n${context.mainJs}`,
    `Current src/styles.css:\n${context.stylesCss}`,
  ].filter(Boolean).join("\n");
  const packet = isRecord(payload.dummy_coder_10_packet)
    ? { ...payload.dummy_coder_10_packet }
    : {};
  const enriched = {
    ...payload,
    dummy_coder_10_packet: {
      ...packet,
      fixture_context: context,
      prompt_3_contract: {
        data_source: "tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
        data_source_read_only: true,
        product_fields: ["name", "price", "category", "description"],
        required_index_target: "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
        required_render_target: "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        allowed_style_target: "tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
        index_contract: "Use <script type=\"module\" src=\"src/main.js\"></script>; keep a product-list mount point; do not hardcode product cards.",
        main_contract: "Use import products from './products.js'; and render product-card markup from imported products.",
      },
    },
    selected_target: "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
    target_file: "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
    task: enrichedTask,
  };
  return JSON.stringify(enriched);
}

async function readPrompt3FixtureContext() {
  const root = path.join(process.cwd(), "tests/ui-agent-trials/fixtures/dummy-product-site");
  const [indexHtml, mainJs, productsJs, stylesCss] = await Promise.all([
    readFixtureContextFile(root, "index.html"),
    readFixtureContextFile(root, "src/main.js"),
    readFixtureContextFile(root, "src/products.js"),
    readFixtureContextFile(root, "src/styles.css"),
  ]);
  return {
    indexHtml,
    mainJs,
    productsModule: {
      path: "src/products.js",
      export_shape: /export\s+default\s+/m.test(productsJs) ? "default export" : "named export or existing module export",
      fields: ["name", "price", "category", "description"],
    },
    stylesCss,
  };
}

const prompt1StarterFiles = [
  "README.md",
  "package.json",
  "index.html",
  "src/main.js",
  "src/products.js",
  "src/styles.css",
] as const;

async function prompt1AlreadySatisfiedPayload(bodyText: string) {
  const metadata = promptPacketRequestMetadata(bodyText);
  if (metadata.selected_prompt_id !== "coder-001-init-dummy-product-site") return null;

  const root = path.join(process.cwd(), "tests/ui-agent-trials/fixtures/dummy-product-site");
  const fileContents = await Promise.all(
    prompt1StarterFiles.map(async (file) => ({
      file,
      content: await readFixtureContextFile(root, file),
    })),
  );
  const presentFiles = fileContents
    .filter((item) => item.content.trim().length > 0)
    .map((item) => `tests/ui-agent-trials/fixtures/dummy-product-site/${item.file}`);
  if (presentFiles.length !== prompt1StarterFiles.length) return null;

  const filesByPath = Object.fromEntries(fileContents.map((item) => [item.file, item.content]));
  const probe = codingTargetPlugin.probeStorefront({
    files: {
      "index.html": filesByPath["index.html"] ?? "",
      "src/main.js": filesByPath["src/main.js"] ?? "",
      "src/products.js": filesByPath["src/products.js"] ?? "",
      "src/styles.css": filesByPath["src/styles.css"] ?? "",
    },
  });
  const storefrontRendered =
    probe.preview_behavior_status === "PASS_STOREFRONT_RENDERED" &&
    probe.preview_asset_status === "present" &&
    probe.product_count >= 6 &&
    probe.storefront_runtime_status === "passed";
  if (!storefrontRendered) return null;

  const checksRun = ["existing Prompt 1 starter-file validation", "existing Prompt 1 storefront render validation"];
  const target = "tests/ui-agent-trials/fixtures/dummy-product-site/";
  return {
    active_task_id: metadata.task_id,
    already_satisfied: true,
    alreadySatisfied: true,
    allowed_files: metadata.allowed_files,
    changed_files: [],
    checks_run: checksRun,
    coder_diagnostics: {
      checks_run: checksRun,
      existing_starter_files_present: true,
      existing_starter_files_validation: {
        ok: true,
        present_files: presentFiles,
      },
      storefront_probe: probe,
      generation_source: "disk_inspection",
      model_output_classification: "already_satisfied_noop",
      reason_code: "coder_no_changes_needed",
      trial_result_trust_status: "existing_starter_files_verified_no_diff_needed",
    },
    diff_source: "already_satisfied_existing_dummy_starter_files",
    fallback_used: false,
    generated_diff_by_backend: false,
    generation_source: "disk_inspection",
    message: "already_satisfied",
    model_output_classification: "already_satisfied_noop",
    proposed_diff: "",
    reason: "already_satisfied",
    reason_code: "coder_no_changes_needed",
    scaffold_used: false,
    selected_prompt_id: metadata.selected_prompt_id,
    selected_prompt_number: metadata.selected_prompt_number,
    selected_target: target,
    simple_reason: "already_satisfied",
    status: "already_satisfied",
    target,
    task_id: metadata.task_id,
    trial_result_trust_status: "existing_starter_files_verified_no_diff_needed",
    verification_status: "existing starter-file validation passed",
  };
}

async function prompt3AlreadySatisfiedPayload(bodyText: string) {
  const metadata = promptPacketRequestMetadata(bodyText);
  if (metadata.selected_prompt_id !== "coder-003-render-product-cards") return null;

  const context = await readPrompt3FixtureContext();
  const root = path.join(process.cwd(), "tests/ui-agent-trials/fixtures/dummy-product-site");
  const productsJs = await readFixtureContextFile(root, "src/products.js");
  const probe = codingTargetPlugin.probeStorefront({
    files: {
      "index.html": context.indexHtml,
      "src/main.js": context.mainJs,
      "src/products.js": productsJs,
      "src/styles.css": context.stylesCss,
    },
  });
  const alreadyRendered =
    probe.preview_behavior_status === "PASS_STOREFRONT_RENDERED" &&
    probe.preview_asset_status === "present" &&
    probe.product_count >= 6 &&
    probe.card_render_path_present &&
    probe.category_render_path_present &&
    probe.description_render_path_present &&
    probe.price_render_path_present &&
    probe.storefront_runtime_status === "passed";
  if (!alreadyRendered) return null;

  const target = "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js";
  const checksRun = ["existing Prompt 3 storefront render validation"];
  return {
    active_task_id: metadata.task_id,
    already_satisfied: true,
    alreadySatisfied: true,
    allowed_files: metadata.allowed_files,
    changed_files: [],
    checks_run: checksRun,
    coder_diagnostics: {
      checks_run: checksRun,
      existing_product_cards_present: true,
      existing_product_cards_validation: {
        ok: true,
        storefront_probe: probe,
      },
      generation_source: "disk_inspection",
      model_output_classification: "already_satisfied_noop",
      reason_code: "coder_no_changes_needed",
      trial_result_trust_status: "existing_product_cards_verified_no_diff_needed",
    },
    diff_source: "already_satisfied_existing_dummy_product_cards",
    fallback_used: false,
    generated_diff_by_backend: false,
    generation_source: "disk_inspection",
    message: "already_satisfied",
    model_output_classification: "already_satisfied_noop",
    proposed_diff: "",
    reason: "already_satisfied",
    reason_code: "coder_no_changes_needed",
    scaffold_used: false,
    selected_prompt_id: metadata.selected_prompt_id,
    selected_prompt_number: metadata.selected_prompt_number,
    selected_target: target,
    simple_reason: "already_satisfied",
    status: "already_satisfied",
    target,
    task_id: metadata.task_id,
    trial_result_trust_status: "existing_product_cards_verified_no_diff_needed",
    verification_status: "existing storefront render validation passed",
  };
}

async function readFixtureContextFile(root: string, relativePath: string) {
  try {
    return await readFile(path.join(root, relativePath), "utf8");
  } catch {
    return "";
  }
}

async function enrichProviderModelTruthFromStatus(responseBodyText: string) {
  let payload: unknown;
  try {
    payload = JSON.parse(responseBodyText);
  } catch {
    return responseBodyText;
  }
  if (!isRecord(payload) || hasProviderModelTruth(payload)) {
    return responseBodyText;
  }

  const localRoute = await readConfiguredLocalRoute();
  if (!localRoute) {
    return responseBodyText;
  }

  const providerModelTruth = providerModelTruthForLocalRoute(localRoute);
  payload.provider = providerModelTruth.providerId;
  payload.model = providerModelTruth.modelId;
  payload.provider_model_truth = providerModelTruth;
  payload.providerModelTruth = providerModelTruth;
  payload.provider_model_source = providerModelTruth.source;
  payload.provider_model_status = providerModelTruth.status;
  payload.provider_call_made = providerModelTruth.providerCallMade;
  payload.provider_call_authorized = providerModelTruth.providerCallAuthorized;
  payload.hermes_lane_available = providerModelTruth.hermesLaneAvailable;
  payload.hermes_used_for_this_run = providerModelTruth.hermesUsedForThisRun;
  payload.provider_model_probe_ok = providerModelTruth.probeOk;
  payload.provider_model_selected_via = providerModelTruth.selectedVia;
  payload.provider_model_api_base_host = providerModelTruth.apiBaseHost;
  return JSON.stringify(payload);
}

function hasProviderModelTruth(payload: JsonRecord) {
  return Boolean(
    payload.provider_model_truth ||
      payload.providerModelTruth ||
      typeof payload.provider_call_made === "boolean",
  );
}

async function readConfiguredLocalRoute() {
  try {
    const response = await sourceProxyFetch("/v1/self/status", { method: "GET" });
    if (!response.ok) return null;
    const payload = await response.json() as unknown;
    if (!isRecord(payload)) return null;
    const routes = Array.isArray(payload.model_routes) ? payload.model_routes : [];
    const normalized = routes.filter(isRecord);
    return (
      normalized.find((route) => route.alias === "coder" && route.enabled === true) ??
      normalized.find((route) => route.alias === "local" && route.enabled === true) ??
      null
    );
  } catch {
    return null;
  }
}

function providerModelTruthForLocalRoute(route: JsonRecord) {
  const provider = stringFromUnknown(route.provider) || "ollama";
  const model =
    stringFromUnknown(route.resolved_model) ||
    stringFromUnknown(route.model) ||
    "";
  const providerIsLocal = provider === "ollama" || provider === "local";
  const modelLabel = model ? model.replace(/^ollama_chat\//, "") : "Unknown local model";
  const configuredModelIsHermes = model ? /hermes/i.test(model) : null;
  return {
    authority: {
      canApply: false,
      canCommit: false,
      canDraft: true,
      canPreview: true,
      canPush: false,
      canVerify: false,
    },
    blockedReason: !model
      ? "Local/Ollama lane is configured, but the exact runtime model was not recorded."
      : configuredModelIsHermes === false
        ? "Local/Ollama lane is configured, but the selected model is not Hermes."
        : "",
    configured: Boolean(model),
    configuredModelIsHermes,
    configuredOllamaModel: stringFromUnknown(route.configured_ollama_model) || modelLabel,
    externalCallAvailable: !providerIsLocal,
    family: providerIsLocal ? "local/ollama/hermes" : "unknown",
    hermesLaneAvailable: providerIsLocal,
    hermesUsedForThisRun: null,
    modelId: model || "unknown-local-model",
    modelLabel,
    previewAvailable: true,
    providerCallAuthorized: false,
    providerCallMade: false,
    providerId: providerIsLocal ? "local" : provider,
    providerLabel: providerIsLocal ? "Local / Ollama" : provider,
    apiBaseHost: stringFromUnknown(route.api_base_host),
    probeOk: typeof route.probe_ok === "boolean" ? route.probe_ok : null,
    selectedVia: stringFromUnknown(route.selected_via),
    source: "config",
    status: model ? "configured" : "unknown",
  };
}

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function stringFromUnknown(value: unknown) {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}
