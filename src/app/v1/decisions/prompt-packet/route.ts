import { mergeRepoFirstResearchSources } from "@/app/v1/decisions/_repo-research";
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
    "src/products.js is the source of truth. Do not duplicate the product array or hardcode product cards in index.html.",
    "Render all exported products dynamically in src/main.js. Cards must show name, price, category, and description.",
    "This selected-prompt packet replaces src/main.js only, so keep the current classic script loading and use dynamic import('./products.js') so preview actually runs.",
    "A static import is valid only with a matching index.html module-script change; do not mix static import with classic script loading.",
    "src/styles.css may be updated for a simple responsive card grid.",
    `Current index.html:\n${context.indexHtml}`,
    `Current src/main.js:\n${context.mainJs}`,
    `Current src/products.js:\n${context.productsJs}`,
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
        required_render_target: "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        allowed_style_target: "tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
        index_contract: "Keep a product-list mount point and script wiring; do not hardcode product cards.",
        expected_product_count: context.productCount,
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
    productCount: (productsJs.match(/\bid\s*:/g) ?? []).length,
    productsJs,
    stylesCss,
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
