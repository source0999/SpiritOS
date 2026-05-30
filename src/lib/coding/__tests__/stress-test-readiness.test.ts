import { describe, expect, it } from "vitest";

import { localHermesProviderModelTruth } from "@/lib/coding/model-provider-status";
import { buildStressTestReadiness } from "@/lib/coding/stress-test-readiness";

describe("stress test readiness", () => {
  it("is ready when Hermes is configured and fixtures are clean", () => {
    const truth = localHermesProviderModelTruth({
      modelId: "ollama_chat/hermes4",
      status: "configured",
      source: "config",
    });
    const readiness = buildStressTestReadiness({
      composerProviderTruth: truth,
      lastProviderCallSmoke: { pass: true, routedModel: "ollama_chat/hermes4" },
      ollamaStoragePath: "/mnt/spirit-8tb/ollama-models",
      sourceProxyReachable: true,
      staleTrialReceiptCount: 0,
      trialFixturesClean: "yes",
      trialRunnerProviderTruth: truth,
    });

    expect(readiness.readyForTenPromptStressTest).toBe(true);
    expect(readiness.manualComposerModelTruth).toBe("hermes4");
    expect(readiness.trialRunnerModelTruth).toBe("hermes4");
  });

  it("blocks when trial receipts are still active", () => {
    const truth = localHermesProviderModelTruth({
      modelId: "ollama_chat/hermes4",
      status: "configured",
    });
    const readiness = buildStressTestReadiness({
      composerProviderTruth: truth,
      sourceProxyReachable: true,
      staleTrialReceiptCount: 1,
      trialFixturesClean: "no",
      trialRunnerProviderTruth: truth,
    });

    expect(readiness.readyForTenPromptStressTest).toBe(false);
    expect(readiness.readyReason).toContain("Trial fixtures still have unreconciled applied changes");
  });
});
