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
      label: "Local LLM",
      status: "default",
      summary: "Default route where local coding support is available.",
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
      modelLabel: "Local LLM default",
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
