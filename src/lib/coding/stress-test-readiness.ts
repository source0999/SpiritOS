import type { CodingProviderModelTruth } from "@/lib/coding/model-provider-status";
import { formatHermesUsedForRunStatus } from "@/lib/coding/model-provider-status";

export type ProviderCallSmokeResult = {
  pass: boolean;
  provider?: string | null;
  responseContent?: string | null;
  responseTimeMs?: number | null;
  routedModel?: string | null;
  zeroCostLocalRoute?: boolean;
};

export type StressTestReadinessInput = {
  composerProviderTruth: CodingProviderModelTruth;
  lastProviderCallSmoke?: ProviderCallSmokeResult | null;
  ollamaStoragePath?: string | null;
  sourceProxyReachable: boolean;
  staleTrialReceiptCount: number;
  trialFixturesClean: "yes" | "no" | "unknown";
  trialRunnerProviderTruth: CodingProviderModelTruth;
};

export type StressTestReadiness = {
  composerProviderTruth: CodingProviderModelTruth;
  lastProviderCallSmoke: "pass" | "fail" | "not_run";
  manualComposerModelTruth: string;
  ollamaStoragePath: string;
  readyForTenPromptStressTest: boolean;
  readyReason: string;
  sourceProxyLocalModel: string;
  sourceProxyReachable: boolean;
  staleTrialReceipts: number;
  trialFixturesClean: "yes" | "no" | "unknown";
  trialRunnerModelTruth: string;
};

function modelTruthLabel(truth: CodingProviderModelTruth): string {
  if (truth.modelLabel && truth.modelLabel !== "Unknown local model" && truth.modelLabel !== "not recorded") {
    return truth.modelLabel;
  }
  if (truth.configuredModel && truth.configuredModel !== "unknown") {
    return truth.configuredModel;
  }
  return "unknown";
}

function hermesConfigured(truth: CodingProviderModelTruth): boolean {
  return truth.configuredModelIsHermes === true || /hermes/i.test(truth.runtimeRouteModel);
}

export function buildStressTestReadiness(input: StressTestReadinessInput): StressTestReadiness {
  const manualComposerModelTruth = modelTruthLabel(input.composerProviderTruth);
  const trialRunnerModelTruth = modelTruthLabel(input.trialRunnerProviderTruth);
  const sourceProxyLocalModel =
    input.trialRunnerProviderTruth.runtimeRouteModel ||
    input.composerProviderTruth.runtimeRouteModel ||
    manualComposerModelTruth;
  const lastProviderCallSmoke = !input.lastProviderCallSmoke
    ? "not_run"
    : input.lastProviderCallSmoke.pass
      ? "pass"
      : "fail";

  const blockers: string[] = [];
  if (!input.sourceProxyReachable) {
    blockers.push("Source Proxy is not reachable on /v1/self/status");
  }
  if (!hermesConfigured(input.composerProviderTruth)) {
    blockers.push("Manual composer does not report configured Hermes");
  }
  if (!hermesConfigured(input.trialRunnerProviderTruth)) {
    blockers.push("Trial runner does not report configured Hermes");
  }
  if (input.trialFixturesClean === "no") {
    blockers.push("Trial fixtures still have unreconciled applied changes");
  }
  if (input.staleTrialReceiptCount > 0) {
    blockers.push(`${input.staleTrialReceiptCount} stale trial receipt(s) still tracked as active`);
  }
  if (lastProviderCallSmoke === "fail") {
    blockers.push("Last Hermes provider-call smoke failed");
  }

  const readyForTenPromptStressTest = blockers.length === 0;
  const readyReason = readyForTenPromptStressTest
    ? "Hermes 4 is configured across composer and trial runner; fixtures and receipts look clean enough for a 10-prompt stress run."
    : blockers[0] ?? "Stress-test readiness is not confirmed yet.";

  return {
    composerProviderTruth: input.composerProviderTruth,
    lastProviderCallSmoke,
    manualComposerModelTruth,
    ollamaStoragePath: input.ollamaStoragePath?.trim() || "unknown",
    readyForTenPromptStressTest,
    readyReason,
    sourceProxyLocalModel,
    sourceProxyReachable: input.sourceProxyReachable,
    staleTrialReceipts: input.staleTrialReceiptCount,
    trialFixturesClean: input.trialFixturesClean,
    trialRunnerModelTruth,
  };
}

export function formatStressTestReadinessLines(
  readiness: StressTestReadiness,
  smoke?: ProviderCallSmokeResult | null,
): string[] {
  return [
    "stress_test_readiness:",
    `source_proxy_reachable: ${readiness.sourceProxyReachable ? "yes" : "no"}`,
    `source_proxy_local_model: ${readiness.sourceProxyLocalModel}`,
    `ollama_storage: ${readiness.ollamaStoragePath}`,
    `manual_composer_model_truth: ${readiness.manualComposerModelTruth}`,
    `trial_runner_model_truth: ${readiness.trialRunnerModelTruth}`,
    `configured_model: ${readiness.composerProviderTruth.configuredModel}`,
    `runtime_route_model: ${readiness.composerProviderTruth.runtimeRouteModel}`,
    `provider_call_made: ${readiness.composerProviderTruth.providerCallMade}`,
    `model_called_for_generation: ${readiness.composerProviderTruth.modelCalledForGeneration ?? "none"}`,
    `hermes_used_for_this_run: ${formatHermesUsedForRunStatus(readiness.composerProviderTruth)}`,
    `last_provider_call_smoke: ${readiness.lastProviderCallSmoke}`,
    ...(smoke
      ? [
          `last_smoke_routed_model: ${smoke.routedModel ?? "unknown"}`,
          `last_smoke_response_content: ${smoke.responseContent ?? "none"}`,
          `last_smoke_response_time_ms: ${smoke.responseTimeMs ?? "unknown"}`,
          `last_smoke_zero_cost_local_route: ${smoke.zeroCostLocalRoute ? "yes" : "no"}`,
        ]
      : []),
    `stale_trial_receipts: ${readiness.staleTrialReceipts}`,
    `trial_fixtures_clean: ${readiness.trialFixturesClean}`,
    `ready_for_10_prompt_stress_test: ${readiness.readyForTenPromptStressTest ? "yes" : "no"}`,
    `ready_reason: ${readiness.readyReason}`,
  ];
}
