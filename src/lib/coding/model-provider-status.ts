export type CodingProviderStatus = {
  authority: {
    apply: false;
    commit: false;
    externalCall: boolean;
    push: false;
  };
  id: "local" | "cloud" | "codex_worker" | "future";
  label: string;
  status: "default" | "configured" | "proposal-only" | "future" | "unavailable";
  summary: string;
};

export type CodingProviderId = CodingProviderStatus["id"];

export type CodingProviderModelId = "local-default" | "gpt-cloud" | "codex-proposal" | "future-provider";

export type CodingProviderModelTruthStatus =
  | "available"
  | "configured"
  | "unavailable"
  | "unknown"
  | "proposal_only";

export type HermesUsedForRunStatus = "yes" | "no" | "not_called" | "unknown";

export type CodingProviderModelTruthSource =
  | "runtime"
  | "config"
  | "ui-selection"
  | "inferred"
  | "unknown";

export type CodingProviderModelTruth = {
  authority: {
    canApply: boolean;
    canCommit: boolean;
    canDraft: boolean;
    canPreview: boolean;
    canPush: boolean;
    canVerify: boolean;
  };
  blockedReason: string;
  configured: boolean;
  configuredModel: string;
  configuredModelIsHermes: boolean | null;
  configuredOllamaModel?: string | null;
  externalCallAvailable: boolean;
  family: "local/ollama/hermes" | "cloud" | "codex/proposal" | "future" | "unknown";
  hermesLaneAvailable: boolean;
  hermesUsedForRunStatus: HermesUsedForRunStatus;
  hermesUsedForThisRun: boolean | null;
  modelCalledForGeneration: string | null;
  modelId: string;
  modelLabel: string;
  previewAvailable: boolean;
  providerCallAuthorized: boolean;
  providerCallMade: boolean;
  providerId: string;
  providerLabel: string;
  providerModelApiBaseHost?: string | null;
  providerModelProbeOk?: boolean | null;
  providerModelSelectedVia?: string | null;
  runtimeRouteModel: string;
  source: CodingProviderModelTruthSource;
  status: CodingProviderModelTruthStatus;
};

export type CodingProviderModelOption = {
  blockedReason: string;
  configured: boolean;
  costWarning: string;
  externalCallAvailable: boolean;
  id: CodingProviderModelId;
  label: string;
  modelLabel: string;
  previewAvailable: boolean;
  providerId: CodingProviderId;
  receiptLabel: string;
  status: CodingProviderStatus["status"];
};

const localHermesAuthority = {
  canApply: false,
  canCommit: false,
  canDraft: true,
  canPreview: true,
  canPush: false,
  canVerify: false,
};

function displayLocalModel(modelId: string | null | undefined): string {
  const cleaned = (modelId ?? "").trim();
  if (!cleaned || cleaned === "unknown-local-model") return "Unknown local model";
  const withoutProvider = cleaned.replace(/^ollama_chat\//, "");
  if (/hermes/i.test(withoutProvider)) return withoutProvider;
  return withoutProvider;
}

export function resolveHermesUsedForRunStatus(options: {
  configuredModelIsHermes?: boolean | null;
  modelCalledForGeneration?: string | null;
  providerCallMade: boolean;
}): HermesUsedForRunStatus {
  if (!options.providerCallMade) return "not_called";
  const calledModel = options.modelCalledForGeneration ?? "";
  if (/hermes/i.test(calledModel)) return "yes";
  if (options.configuredModelIsHermes === true) return "yes";
  if (options.configuredModelIsHermes === false) return "no";
  return "unknown";
}

export function formatHermesUsedForRunStatus(truth: Pick<
  CodingProviderModelTruth,
  "configuredModelIsHermes" | "hermesUsedForRunStatus" | "hermesUsedForThisRun" | "modelCalledForGeneration" | "providerCallMade"
>): string {
  if (truth.hermesUsedForRunStatus) return truth.hermesUsedForRunStatus;
  if (!truth.providerCallMade) return "not_called";
  if (truth.hermesUsedForThisRun === true) return "yes";
  if (truth.hermesUsedForThisRun === false) return "no";
  return "unknown";
}

function withHermesRunStatus(
  truth: Omit<CodingProviderModelTruth, "hermesUsedForRunStatus" | "hermesUsedForThisRun"> & {
    hermesUsedForThisRun?: boolean | null;
  },
): CodingProviderModelTruth {
  const hermesUsedForRunStatus = resolveHermesUsedForRunStatus({
    configuredModelIsHermes: truth.configuredModelIsHermes,
    modelCalledForGeneration: truth.modelCalledForGeneration,
    providerCallMade: truth.providerCallMade,
  });
  return {
    ...truth,
    hermesUsedForRunStatus,
    hermesUsedForThisRun:
      truth.hermesUsedForThisRun ??
      (hermesUsedForRunStatus === "yes"
        ? true
        : hermesUsedForRunStatus === "no"
          ? false
          : null),
  };
}

export function mergePreviewWithConfiguredProviderTruth(
  previewTruth: CodingProviderModelTruth,
  configuredTruth?: CodingProviderModelTruth | null,
): CodingProviderModelTruth {
  if (!configuredTruth) return previewTruth;

  const configuredModelId = (configuredTruth.modelId ?? "").trim();
  const hasConfiguredModel =
    configuredModelId !== "" && configuredModelId !== "unknown-local-model";
  if (!hasConfiguredModel) return previewTruth;

  const previewModelId = (previewTruth.modelId ?? "").trim();
  const previewHasConcreteModel =
    previewModelId !== "" &&
    previewModelId !== "unknown-local-model" &&
    previewTruth.modelLabel !== "Unknown local model";
  const previewLooksLikeLabelOnly =
    !previewHasConcreteModel ||
    previewModelId === previewTruth.modelLabel ||
    previewModelId === configuredTruth.configuredModel ||
    previewModelId === configuredTruth.modelLabel;

  if (!previewLooksLikeLabelOnly) return previewTruth;

  return localHermesProviderModelTruth({
    blockedReason: previewTruth.blockedReason || configuredTruth.blockedReason || undefined,
    modelId: configuredModelId,
    providerCallAuthorized: previewTruth.providerCallMade
      ? true
      : (previewTruth.providerCallAuthorized ?? configuredTruth.providerCallAuthorized),
    providerCallMade: previewTruth.providerCallMade,
    providerModelApiBaseHost:
      previewTruth.providerModelApiBaseHost ?? configuredTruth.providerModelApiBaseHost,
    providerModelProbeOk:
      previewTruth.providerModelProbeOk ?? configuredTruth.providerModelProbeOk,
    providerModelSelectedVia:
      previewTruth.providerModelSelectedVia ?? configuredTruth.providerModelSelectedVia,
    source: previewTruth.providerCallMade ? previewTruth.source : configuredTruth.source,
    status: previewTruth.providerCallMade ? previewTruth.status : configuredTruth.status,
  });
}

export function providerTruthFromPreviewState(
  preview: {
    model: string | null;
    providerCallAuthorized?: boolean;
    providerCallMade?: boolean;
    providerModelBlockedReason?: string;
    providerModelApiBaseHost?: string | null;
    providerModelProbeOk?: boolean | null;
    providerModelSelectedVia?: string | null;
    providerModelSource?: string;
    providerModelStatus?: string;
  },
  configuredTruth?: CodingProviderModelTruth | null,
): CodingProviderModelTruth {
  const previewModelId =
    preview.model && preview.model !== "Unknown local model" ? preview.model : null;
  const fromPreview = localHermesProviderModelTruth({
    blockedReason:
      preview.providerModelBlockedReason ||
      (preview.providerModelStatus === "unknown"
        ? "Local/Ollama lane is selected, but this run did not record the exact runtime model."
        : undefined),
    modelId: previewModelId,
    providerCallAuthorized: preview.providerCallAuthorized,
    providerCallMade: preview.providerCallMade,
    providerModelApiBaseHost: preview.providerModelApiBaseHost,
    providerModelProbeOk: preview.providerModelProbeOk,
    providerModelSelectedVia: preview.providerModelSelectedVia,
    source:
      preview.providerModelSource === "runtime"
        ? "runtime"
        : preview.providerModelSource === "inferred"
          ? "inferred"
          : preview.providerModelSource === "config"
            ? "config"
            : preview.providerModelSource === "unknown"
              ? "unknown"
              : "ui-selection",
    status:
      preview.providerModelStatus === "available"
        ? "available"
        : preview.providerModelStatus === "configured"
          ? "configured"
          : preview.providerModelStatus === "unavailable"
            ? "unavailable"
            : preview.providerModelStatus === "proposal_only"
              ? "proposal_only"
              : "unknown",
  });
  return mergePreviewWithConfiguredProviderTruth(fromPreview, configuredTruth);
}

export function localHermesProviderModelTruth(options?: {
  blockedReason?: string;
  modelId?: string | null;
  providerModelApiBaseHost?: string | null;
  providerModelProbeOk?: boolean | null;
  providerModelSelectedVia?: string | null;
  providerCallAuthorized?: boolean;
  providerCallMade?: boolean;
  source?: CodingProviderModelTruthSource;
  status?: CodingProviderModelTruthStatus;
}): CodingProviderModelTruth {
  const modelId = (options?.modelId ?? "").trim();
  const modelLabel = modelId ? displayLocalModel(modelId) : "Unknown local model";
  const configuredModel = modelId ? displayLocalModel(modelId) : "unknown";
  const runtimeRouteModel = modelId || "unknown";
  const configuredModelIsHermes =
    modelId && modelId !== "unknown-local-model" ? /hermes/i.test(modelId) : null;
  const providerCallMade = options?.providerCallMade ?? false;
  const modelCalledForGeneration = providerCallMade && modelId ? runtimeRouteModel : null;
  return withHermesRunStatus({
    authority: localHermesAuthority,
    blockedReason:
      options?.blockedReason ??
      (!modelId
        ? "Local/Ollama lane is selected, but the exact runtime model was not recorded."
        : configuredModelIsHermes === false
          ? "Local/Ollama lane is configured, but the selected model is not Hermes."
          : ""),
    configured: Boolean(modelId && modelId !== "unknown-local-model"),
    configuredModel,
    configuredModelIsHermes,
    configuredOllamaModel: modelId ? displayLocalModel(modelId) : null,
    externalCallAvailable: false,
    family: "local/ollama/hermes",
    hermesLaneAvailable: true,
    modelCalledForGeneration,
    modelId: modelId || "unknown-local-model",
    modelLabel,
    previewAvailable: true,
    providerCallAuthorized: options?.providerCallAuthorized ?? false,
    providerCallMade,
    providerId: "local",
    providerLabel: "Local / Ollama",
    providerModelApiBaseHost: options?.providerModelApiBaseHost ?? null,
    providerModelProbeOk: options?.providerModelProbeOk ?? null,
    providerModelSelectedVia: options?.providerModelSelectedVia ?? null,
    runtimeRouteModel,
    source: options?.source ?? "ui-selection",
    status: options?.status ?? (modelId ? "configured" : "unknown"),
  });
}

export function unknownProviderModelTruth(blockedReason = "Provider/model was not recorded."): CodingProviderModelTruth {
  return withHermesRunStatus({
    authority: {
      canApply: false,
      canCommit: false,
      canDraft: false,
      canPreview: false,
      canPush: false,
      canVerify: false,
    },
    blockedReason,
    configured: false,
    configuredModel: "unknown",
    configuredModelIsHermes: null,
    configuredOllamaModel: null,
    externalCallAvailable: false,
    family: "unknown",
    hermesLaneAvailable: false,
    modelCalledForGeneration: null,
    modelId: "not-recorded",
    modelLabel: "not recorded",
    previewAvailable: false,
    providerCallAuthorized: false,
    providerCallMade: false,
    providerId: "not-recorded",
    providerLabel: "not recorded",
    providerModelApiBaseHost: null,
    providerModelProbeOk: null,
    providerModelSelectedVia: null,
    runtimeRouteModel: "unknown",
    source: "unknown",
    status: "unknown",
  });
}

export function providerModelTruthFromPayload(
  payload: unknown,
  fallback: CodingProviderModelTruth = localHermesProviderModelTruth(),
): CodingProviderModelTruth {
  const record = payload && typeof payload === "object" ? payload as Record<string, unknown> : {};
  const nestedRaw = record.provider_model_truth ?? record.providerModelTruth;
  const nested = nestedRaw && typeof nestedRaw === "object" ? nestedRaw as Record<string, unknown> : {};
  const diagnosticsRaw = record.coder_diagnostics ?? record.coderDiagnostics;
  const diagnostics = diagnosticsRaw && typeof diagnosticsRaw === "object" ? diagnosticsRaw as Record<string, unknown> : {};
  const provider = stringFromUnknown(nested.providerId) ?? stringFromUnknown(record.provider) ?? stringFromUnknown(diagnostics.provider);
  const model =
    stringFromUnknown(nested.modelId) ??
    stringFromUnknown(record.model) ??
    stringFromUnknown(diagnostics.model) ??
    stringFromUnknown(diagnostics.litellm_model);
  const source =
    truthSourceFromUnknown(nested.source) ??
    truthSourceFromUnknown(record.provider_model_source) ??
    (provider || model ? "runtime" : fallback.source);
  const providerCallMade = booleanFromUnknown(nested.providerCallMade) ?? booleanFromUnknown(record.provider_call_made) ?? booleanFromUnknown(diagnostics.router_call_attempted) ?? fallback.providerCallMade;
  const providerCallAuthorized =
    booleanFromUnknown(nested.providerCallAuthorized) ??
    booleanFromUnknown(record.provider_call_authorized) ??
    providerCallMade;
  const normalizedProvider = (provider ?? fallback.providerId).toLowerCase();
  if (normalizedProvider === "ollama" || normalizedProvider === "local" || normalizedProvider === "local/ollama") {
    return localHermesProviderModelTruth({
      blockedReason: stringFromUnknown(nested.blockedReason) ?? undefined,
      modelId: model ?? fallback.modelId,
      providerCallAuthorized,
      providerCallMade,
      providerModelApiBaseHost: stringFromUnknown(nested.apiBaseHost),
      providerModelProbeOk: booleanFromUnknown(nested.probeOk),
      providerModelSelectedVia: stringFromUnknown(nested.selectedVia),
      source,
      status:
        truthStatusFromUnknown(nested.status) ??
        truthStatusFromUnknown(record.provider_model_status) ??
        (providerCallMade ? "available" : fallback.status),
    });
  }
  if (!provider && !model) return fallback;
  const modelId = model ?? "not-recorded";
  return withHermesRunStatus({
    ...fallback,
    blockedReason: stringFromUnknown(nested.blockedReason) ?? "",
    configuredModel: displayLocalModel(modelId),
    externalCallAvailable: normalizedProvider !== "local",
    family: normalizedProvider === "codex_worker" ? "codex/proposal" : normalizedProvider === "future" ? "future" : "cloud",
    hermesLaneAvailable: fallback.hermesLaneAvailable,
    configuredModelIsHermes: false,
    configuredOllamaModel: null,
    modelCalledForGeneration: providerCallMade ? modelId : null,
    modelId,
    modelLabel: model ?? "not recorded",
    providerCallAuthorized,
    providerCallMade,
    providerId: provider ?? "not-recorded",
    providerLabel: provider ?? "not recorded",
    runtimeRouteModel: modelId,
    source,
    status:
      truthStatusFromUnknown(nested.status) ??
      truthStatusFromUnknown(record.provider_model_status) ??
      "configured",
  });
}

export function providerModelTruthFromSelfStatus(
  payload: unknown,
  fallback: CodingProviderModelTruth = localHermesProviderModelTruth(),
): CodingProviderModelTruth {
  const record = payload && typeof payload === "object" ? payload as Record<string, unknown> : {};
  const routes = Array.isArray(record.model_routes) ? record.model_routes : [];
  const localRoute = routes
    .filter((route): route is Record<string, unknown> => Boolean(route && typeof route === "object" && !Array.isArray(route)))
    .find((route) => route.alias === "local" && route.enabled === true);
  if (!localRoute) return fallback;

  const provider = stringFromUnknown(localRoute.provider) ?? "ollama";
  const model =
    stringFromUnknown(localRoute.resolved_model) ??
    stringFromUnknown(localRoute.model) ??
    stringFromUnknown(localRoute.litellm_model) ??
    stringFromUnknown(localRoute.ollama_model) ??
    fallback.modelId;
  const providerIsLocal = provider === "ollama" || provider === "local";
  if (!providerIsLocal) return fallback;

  return localHermesProviderModelTruth({
    modelId: model,
    providerCallAuthorized: false,
    providerCallMade: false,
    providerModelApiBaseHost: stringFromUnknown(localRoute.api_base_host),
    providerModelProbeOk: booleanFromUnknown(localRoute.probe_ok),
    providerModelSelectedVia: stringFromUnknown(localRoute.selected_via),
    source: "config",
    status: model && model !== "unknown-local-model" ? "configured" : fallback.status,
  });
}

export function ollamaStoragePathFromSelfStatus(payload: unknown): string | null {
  const record = payload && typeof payload === "object" ? payload as Record<string, unknown> : {};
  const routes = Array.isArray(record.model_routes) ? record.model_routes : [];
  const localRoute = routes
    .filter((route): route is Record<string, unknown> => Boolean(route && typeof route === "object" && !Array.isArray(route)))
    .find((route) => route.alias === "local" && route.enabled === true);
  if (!localRoute) return null;
  const path = stringFromUnknown(localRoute.model_storage_path);
  if (!path) return null;
  const status = stringFromUnknown(localRoute.model_storage_status);
  return status === "proven" ? path : path;
}

function stringFromUnknown(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function booleanFromUnknown(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function truthSourceFromUnknown(value: unknown): CodingProviderModelTruthSource | null {
  return value === "runtime" ||
    value === "config" ||
    value === "ui-selection" ||
    value === "inferred" ||
    value === "unknown"
    ? value
    : null;
}

function truthStatusFromUnknown(value: unknown): CodingProviderModelTruthStatus | null {
  return value === "available" ||
    value === "configured" ||
    value === "unavailable" ||
    value === "unknown" ||
    value === "proposal_only"
    ? value
    : null;
}

export function getCodingProviderStatuses(options?: {
  cloudConfigured?: boolean;
}): CodingProviderStatus[] {
  const cloudConfigured = options?.cloudConfigured === true;
  return [
    {
      authority: {
        apply: false,
        commit: false,
        externalCall: false,
        push: false,
      },
      id: "local",
      label: "Local / Ollama",
      status: "default",
      summary: "Default local lane for Hermes/Ollama planning and preview when the backend route is configured.",
    },
    {
      authority: {
        apply: false,
        commit: false,
        externalCall: cloudConfigured,
        push: false,
      },
      id: "cloud",
      label: "GPT/cloud",
      status: cloudConfigured ? "configured" : "unavailable",
      summary: cloudConfigured
        ? "Selectable when configured; route use must be shown after the call."
        : "Unavailable until GPT/cloud configuration is detected.",
    },
    {
      authority: {
        apply: false,
        commit: false,
        externalCall: false,
        push: false,
      },
      id: "codex_worker",
      label: "Codex worker",
      status: "proposal-only",
      summary: "Proposal and evidence lane only; cannot apply, commit, or push.",
    },
    {
      authority: {
        apply: false,
        commit: false,
        externalCall: false,
        push: false,
      },
      id: "future",
      label: "Future providers",
      status: "future",
      summary: "Visible placeholder until a safe configured Source Proxy route exists.",
    },
  ];
}

export function describeCodingProviderIntent(
  providerId: CodingProviderId,
  providers: CodingProviderStatus[] = getCodingProviderStatuses(),
): string {
  const provider = providers.find((item) => item.id === providerId);
  if (!provider || provider.id === "local") {
    return "Intent: local LLM route. No provider call has run yet.";
  }
  if (provider.id === "codex_worker") {
    return "Intent: Codex worker proposal route. No apply, commit, push, or provider call has run yet.";
  }
  if (provider.id === "future") {
    return "Intent: future provider route requested, but unavailable until a safe Source Proxy route is configured. No provider call has run yet.";
  }
  if (provider.status === "configured") {
    return "Intent: GPT/cloud route when submitted. No provider call has run yet.";
  }
  return "Intent: GPT/cloud route requested, but unavailable until configured. No provider call has run yet.";
}

export function getCodingProviderModelOptions(options?: {
  cloudConfigured?: boolean;
}): CodingProviderModelOption[] {
  const cloudConfigured = options?.cloudConfigured === true;
  return [
    {
      blockedReason: "",
      configured: true,
      costWarning: "No external API cost; local/default intent only.",
      externalCallAvailable: false,
      id: "local-default",
      label: "Local default",
      modelLabel: "Unknown local model",
      previewAvailable: true,
      providerId: "local",
      receiptLabel: "local default model; no external provider call",
      status: "default",
    },
    {
      blockedReason: cloudConfigured
        ? "Configured status still requires explicit provider-call approval before use."
        : "Missing GPT/cloud configuration or key.",
      configured: cloudConfigured,
      costWarning: cloudConfigured
        ? "External API cost possible only after a separate provider-call approval."
        : "External API cost blocked; no GPT/cloud configuration is available.",
      externalCallAvailable: cloudConfigured,
      id: "gpt-cloud",
      label: "GPT/cloud",
      modelLabel: cloudConfigured ? "Configured GPT/cloud model" : "GPT/cloud missing config",
      previewAvailable: false,
      providerId: "cloud",
      receiptLabel: cloudConfigured
        ? "configured GPT/cloud model; provider call still gated"
        : "GPT/cloud unavailable; missing config",
      status: cloudConfigured ? "configured" : "unavailable",
    },
    {
      blockedReason: "Codex worker is proposal-only in this shell.",
      configured: false,
      costWarning: "No provider call from this selector; proposal-only route remains gated.",
      externalCallAvailable: false,
      id: "codex-proposal",
      label: "Codex proposal",
      modelLabel: "Codex worker proposal",
      previewAvailable: false,
      providerId: "codex_worker",
      receiptLabel: "Codex proposal-only model; no apply/provider authority",
      status: "proposal-only",
    },
    {
      blockedReason: "Future providers do not have a safe configured route.",
      configured: false,
      costWarning: "No external API cost; future provider route is unavailable.",
      externalCallAvailable: false,
      id: "future-provider",
      label: "Future provider",
      modelLabel: "Future provider placeholder",
      previewAvailable: false,
      providerId: "future",
      receiptLabel: "future provider unavailable",
      status: "future",
    },
  ];
}

export function defaultModelIdForProvider(providerId: CodingProviderId): CodingProviderModelId {
  if (providerId === "cloud") return "gpt-cloud";
  if (providerId === "codex_worker") return "codex-proposal";
  if (providerId === "future") return "future-provider";
  return "local-default";
}

export function codingProviderModelOptionById(
  id: CodingProviderModelId | string | null | undefined,
  options: CodingProviderModelOption[] = getCodingProviderModelOptions(),
): CodingProviderModelOption {
  return options.find((option) => option.id === id) ?? options[0];
}

export function providerModelReceiptLines(input: {
  model: CodingProviderModelOption;
  provider: CodingProviderStatus;
  providerCallMade?: boolean;
}): string[] {
  return [
    `Provider selected: ${input.provider.label}`,
    `Provider status: ${input.provider.status}`,
    `Model selected: ${input.model.modelLabel}`,
    `Model status: ${input.model.status}`,
    `Model configured: ${input.model.configured ? "true" : "false"}`,
    `Provider external call available: ${input.model.externalCallAvailable ? "true" : "false"}`,
    `Provider call made: ${input.providerCallMade === true ? "true" : "false"}`,
    `Provider cost warning: ${input.model.costWarning}`,
    `Provider blocked reason: ${input.model.blockedReason || "none"}`,
    `Provider authority: apply=false; commit=false; push=false`,
  ];
}
