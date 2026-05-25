export type CodingUsageTimeState =
  | "current-session"
  | "unavailable"
  | "real-provider-report"
  | "real-budget-report"
  | "projected-only"
  | "gated-durable";

export type CodingUsageTimeRow = {
  actualProviderUsageClaimed: boolean;
  authority: string;
  id:
    | "elapsed-chat-time"
    | "active-run-time"
    | "live-coding-time"
    | "active-diagnostic-time"
    | "custom-cli-time"
    | "command-check-duration"
    | "token-usage"
    | "actual-cost"
    | "projected-api-cost"
    | "budget-status"
    | "durable-usage-storage";
  label: string;
  source: string;
  state: CodingUsageTimeState;
  value: string;
};

export type CodingProviderUsageReport = {
  costUsd?: number | null;
  inputTokens?: number | null;
  outputTokens?: number | null;
  reportedAt?: string;
  source: "provider-report" | "budget-manager";
  totalTokens?: number | null;
};

export type CodingUsageTimeInput = {
  budgetStatusLabel?: string;
  chatStartedAtMs: number | null;
  commandCheckStartedAtMs?: number | null;
  commandCheckEndedAtMs?: number | null;
  diagnosticTimerActive: boolean;
  lifecycleProgressSourceText: string;
  nowMs: number;
  progressElapsedText: string;
  progressStartedAtMs: number | null;
  progressTimerActive: boolean;
  projectedCostLabel?: string;
  providerCallMade: boolean;
  providerUsageReport?: CodingProviderUsageReport | null;
  receiptCommandsRunText: string;
};

const UNAVAILABLE = "unavailable";

export function formatUsageDuration(startedAtMs: number | null, nowMs: number): string {
  if (
    startedAtMs === null ||
    !Number.isFinite(startedAtMs) ||
    !Number.isFinite(nowMs) ||
    nowMs < startedAtMs
  ) {
    return UNAVAILABLE;
  }

  const totalSeconds = Math.floor((nowMs - startedAtMs) / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const minuteSecond = `${minutes}m ${seconds.toString().padStart(2, "0")}s`;

  return hours > 0 ? `${hours}h ${minuteSecond}` : minuteSecond;
}

export function buildCodingUsageTimeRows(input: CodingUsageTimeInput): CodingUsageTimeRow[] {
  const chatElapsed = formatUsageDuration(input.chatStartedAtMs, input.nowMs);
  const commandDuration = formatCommandCheckDuration(input);
  const commandDurationUnavailable = commandDuration === UNAVAILABLE || commandDuration.startsWith("unavailable");
  const tokenReport = providerTokenReport(input.providerUsageReport);
  const costReport = providerCostReport(input.providerUsageReport);
  const diagnosticActive = input.diagnosticTimerActive && input.progressTimerActive;

  return [
    {
      actualProviderUsageClaimed: false,
      authority: "Current-session UI timer only; no durable chat history or backend time is claimed.",
      id: "elapsed-chat-time",
      label: "Elapsed chat time",
      source: "UI render/session clock.",
      state: chatElapsed === UNAVAILABLE ? "unavailable" : "current-session",
      value: chatElapsed === UNAVAILABLE ? UNAVAILABLE : `${chatElapsed} current-session`,
    },
    {
      actualProviderUsageClaimed: false,
      authority: "UI-local progress timer only; no worker, queue, provider, or backend stream authority.",
      id: "active-run-time",
      label: "Active run time",
      source: "UI-local progress timer.",
      state: input.progressTimerActive ? "current-session" : "unavailable",
      value: input.progressTimerActive ? input.progressElapsedText : "unavailable; no active run timer",
    },
    {
      actualProviderUsageClaimed: false,
      authority: "Live coding/apply loops remain gated; no hidden worker or shell execution.",
      id: "live-coding-time",
      label: "Live coding time",
      source: "No approved live coding/apply loop is running in this lane.",
      state: "unavailable",
      value: "unavailable; live coding loop not approved",
    },
    {
      actualProviderUsageClaimed: false,
      authority: "Diagnostic timer is UI-local and stops when the active run is no longer queued/running.",
      id: "active-diagnostic-time",
      label: "Active diagnostic time",
      source: input.lifecycleProgressSourceText,
      state: diagnosticActive ? "current-session" : "unavailable",
      value: diagnosticActive ? input.progressElapsedText : "unavailable; no active diagnostic timer",
    },
    {
      actualProviderUsageClaimed: false,
      authority: "No shell mutation, command execution, terminal write, queue, or worker authority.",
      id: "custom-cli-time",
      label: "Custom CLI time",
      source: "No CLI event stream is wired into this shell.",
      state: "unavailable",
      value: "unavailable; custom CLI timing source missing",
    },
    {
      actualProviderUsageClaimed: false,
      authority: "Command/check duration is shown only when a real receipt or local timer supplies it.",
      id: "command-check-duration",
      label: "Command/check duration",
      source: "Receipt command field and optional current-session command timer.",
      state: commandDurationUnavailable ? "unavailable" : "current-session",
      value: commandDuration,
    },
    {
      actualProviderUsageClaimed: Boolean(tokenReport),
      authority: "Token usage is absent unless a real provider usage report supplies it.",
      id: "token-usage",
      label: "Token usage",
      source: tokenReport?.source ?? "No provider usage report is present.",
      state: tokenReport ? "real-provider-report" : "unavailable",
      value: tokenReport?.value ?? "unavailable; no real provider token report",
    },
    {
      actualProviderUsageClaimed: Boolean(costReport),
      authority: "Actual cost is absent unless a real provider or budget report supplies it.",
      id: "actual-cost",
      label: "Actual cost",
      source: costReport?.source ?? "No provider cost report is present.",
      state: costReport ? "real-provider-report" : "unavailable",
      value: costReport?.value ?? "unavailable; no real provider cost report",
    },
    {
      actualProviderUsageClaimed: false,
      authority: "Projected cost must stay labeled projected and must not be shown as actual spend.",
      id: "projected-api-cost",
      label: "Projected API cost",
      source: input.projectedCostLabel ? "Existing projected_api_cost receipt field." : "No projected cost receipt.",
      state: input.projectedCostLabel ? "projected-only" : "unavailable",
      value: input.projectedCostLabel
        ? `projected only: ${input.projectedCostLabel}`
        : "unavailable; no projected_api_cost receipt",
    },
    {
      actualProviderUsageClaimed: false,
      authority: "Budget status is read-only only when an existing truthful route supplies it; no budget writes.",
      id: "budget-status",
      label: "Budget status",
      source: input.budgetStatusLabel ? "Existing budget manager/status route truth." : "Budget truth unavailable here.",
      state: input.budgetStatusLabel ? "real-budget-report" : "unavailable",
      value: input.budgetStatusLabel ?? "unavailable; no budget status read in this shell",
    },
    {
      actualProviderUsageClaimed: false,
      authority: "Durable usage storage is later-gated; no localStorage, database, config, or budget writes.",
      id: "durable-usage-storage",
      label: "Durable usage storage",
      source: "PR-5 durable storage later gate.",
      state: "gated-durable",
      value: "gated; current-session display only",
    },
  ];
}

export function usageTimeReceiptLines(rows: CodingUsageTimeRow[]): string[] {
  return [
    "Usage/time receipt",
    "no_fake_usage: true",
    "durable_usage_storage: gated",
    "provider_call_made: false",
    ...rows.map(
      (row) =>
        `${row.label}: ${row.state}; value=${row.value}; source=${row.source}; actual_provider_usage_claimed=${row.actualProviderUsageClaimed}; authority=${row.authority}`,
    ),
  ];
}

function formatCommandCheckDuration(input: CodingUsageTimeInput): string {
  const timedDuration = formatTimedCommandDuration(input);

  if (timedDuration !== UNAVAILABLE) {
    return timedDuration;
  }

  const receipt = input.receiptCommandsRunText.trim();

  if (!receipt || receipt === "not run yet") {
    return "unavailable; no command/check result recorded";
  }

  const durationMatch = receipt.match(/\b(\d+(?:\.\d+)?)\s*(ms|s|sec|secs|seconds|m|min|mins|minutes)\b/i);

  if (!durationMatch) {
    return "unavailable; command/check receipt has no duration field";
  }

  return `receipt duration: ${durationMatch[1]}${durationMatch[2]}`;
}

function formatTimedCommandDuration(input: CodingUsageTimeInput): string {
  if (
    input.commandCheckStartedAtMs === undefined ||
    input.commandCheckEndedAtMs === undefined ||
    input.commandCheckStartedAtMs === null ||
    input.commandCheckEndedAtMs === null
  ) {
    return UNAVAILABLE;
  }

  const duration = formatUsageDuration(input.commandCheckStartedAtMs, input.commandCheckEndedAtMs);
  return duration === UNAVAILABLE ? UNAVAILABLE : `current-session ${duration}`;
}

function providerTokenReport(
  report: CodingProviderUsageReport | null | undefined,
): { source: string; value: string } | null {
  if (!report || !Number.isFinite(report.totalTokens ?? Number.NaN)) {
    return null;
  }

  const inputTokens = Number.isFinite(report.inputTokens ?? Number.NaN)
    ? `input=${report.inputTokens}`
    : "input=unavailable";
  const outputTokens = Number.isFinite(report.outputTokens ?? Number.NaN)
    ? `output=${report.outputTokens}`
    : "output=unavailable";

  return {
    source: `${report.source}${report.reportedAt ? ` at ${report.reportedAt}` : ""}`,
    value: `actual tokens: total=${report.totalTokens}; ${inputTokens}; ${outputTokens}`,
  };
}

function providerCostReport(
  report: CodingProviderUsageReport | null | undefined,
): { source: string; value: string } | null {
  if (!report || !Number.isFinite(report.costUsd ?? Number.NaN)) {
    return null;
  }

  return {
    source: `${report.source}${report.reportedAt ? ` at ${report.reportedAt}` : ""}`,
    value: `actual cost: $${Number(report.costUsd).toFixed(4)}`,
  };
}
