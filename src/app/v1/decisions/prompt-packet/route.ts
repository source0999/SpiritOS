import { mergeRepoFirstResearchSources } from "@/app/v1/decisions/_repo-research";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { readFile } from "node:fs/promises";
import path from "node:path";

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const bodyText = await request.text();
  const directDocsOnlyPreview = await docsOnlyPreviewPayload(bodyText, {
    reason_code: "docs_only_bff_direct_preview",
    status: "preview_ready",
  });
  if (directDocsOnlyPreview) {
    return Response.json(JSON.parse(directDocsOnlyPreview));
  }

  let response;
  try {
    response = await sourceProxyFetch("/v1/decisions/prompt-packet", {
      body: bodyText,
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
      method: "POST",
    });
  } catch (error) {
    return Response.json(
      {
        error:
          "The coding page could not reach the Source proxy. Check that the proxy is running and that SOURCE_PROXY_ORIGIN, SOURCE_PROXY_HOST, and SOURCE_PROXY_PORT point to it.",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
      },
      { status: 502 },
    );
  }

  const responseText = await response.text();
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
      payload.provider ||
      payload.model,
  );
}

async function readConfiguredLocalRoute() {
  try {
    const response = await sourceProxyFetch("/v1/self/status", { method: "GET" });
    if (!response.ok) return null;
    const payload = await response.json() as unknown;
    if (!isRecord(payload)) return null;
    const routes = Array.isArray(payload.model_routes) ? payload.model_routes : [];
    return routes
      .filter(isRecord)
      .find((route) => route.alias === "local" && route.enabled === true) ?? null;
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
