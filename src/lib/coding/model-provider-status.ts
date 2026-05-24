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
