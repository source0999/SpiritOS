import { describe, expect, it } from "vitest";

import {
  localHermesProviderModelTruth,
  providerModelTruthFromPayload,
  providerModelTruthFromSelfStatus,
  providerTruthFromPreviewState,
} from "@/lib/coding/model-provider-status";

describe("coding provider/model truth", () => {
  it("represents the local Hermes/Ollama lane without faking an exact model", () => {
    const truth = localHermesProviderModelTruth();

    expect(truth.providerId).toBe("local");
    expect(truth.providerLabel).toBe("Local / Ollama");
    expect(truth.modelLabel).toBe("Unknown local model");
    expect(truth.family).toBe("local/ollama/hermes");
    expect(truth.source).toBe("ui-selection");
    expect(truth.status).toBe("unknown");
    expect(truth.configuredModelIsHermes).toBeNull();
    expect(truth.hermesLaneAvailable).toBe(true);
    expect(truth.hermesUsedForRunStatus).toBe("not_called");
    expect(truth.hermesUsedForThisRun).toBeNull();
    expect(truth.authority.canApply).toBe(false);
    expect(truth.authority.canCommit).toBe(false);
    expect(truth.authority.canPush).toBe(false);
  });

  it("prefers backend runtime provider/model truth when present", () => {
    const truth = providerModelTruthFromPayload({
      coder_diagnostics: {
        litellm_model: "ollama_chat/hermes4:latest",
        provider: "ollama",
        router_call_attempted: true,
      },
    });

    expect(truth.providerLabel).toBe("Local / Ollama");
    expect(truth.modelLabel).toBe("hermes4:latest");
    expect(truth.source).toBe("runtime");
    expect(truth.status).toBe("available");
    expect(truth.configuredModelIsHermes).toBe(true);
    expect(truth.providerCallMade).toBe(true);
    expect(truth.hermesUsedForRunStatus).toBe("yes");
    expect(truth.hermesUsedForThisRun).toBe(true);
    expect(truth.modelCalledForGeneration).toBe("ollama_chat/hermes4:latest");
  });

  it("reports configured local non-Hermes models without pretending Hermes ran", () => {
    const truth = providerModelTruthFromPayload({
      model: "ollama_chat/qwen2.5-coder:7b",
      provider: "local",
      provider_model_source: "config",
      provider_model_status: "configured",
      provider_call_made: false,
    });

    expect(truth.providerLabel).toBe("Local / Ollama");
    expect(truth.modelLabel).toBe("qwen2.5-coder:7b");
    expect(truth.source).toBe("config");
    expect(truth.configuredModelIsHermes).toBe(false);
    expect(truth.hermesUsedForThisRun).toBeNull();
    expect(truth.blockedReason).toContain("not Hermes");
  });

  it("shows configured local model when preview state still has the unknown placeholder", () => {
    const configured = providerModelTruthFromSelfStatus({
      model_routes: [
        {
          alias: "local",
          enabled: true,
          model: "ollama_chat/hermes4",
          provider: "ollama",
        },
      ],
    });
    const active = providerTruthFromPreviewState(
      {
        model: "Unknown local model",
        providerModelSource: "ui-selection",
        providerModelStatus: "unknown",
      },
      configured,
    );

    expect(active.modelLabel).toBe("hermes4");
    expect(active.source).toBe("config");
    expect(active.status).toBe("configured");
  });

  it("hydrates configured Hermes truth from self status model routes", () => {
    const truth = providerModelTruthFromSelfStatus({
      model_routes: [
        {
          alias: "local",
          api_base_host: "127.0.0.1:11434",
          enabled: true,
          model: "ollama_chat/hermes4",
          probe_ok: true,
          provider: "ollama",
          selected_via: "probe:fallback_default",
        },
      ],
    });

    expect(truth.providerLabel).toBe("Local / Ollama");
    expect(truth.modelLabel).toBe("hermes4");
    expect(truth.source).toBe("config");
    expect(truth.status).toBe("configured");
    expect(truth.providerModelProbeOk).toBe(true);
    expect(truth.providerModelSelectedVia).toBe("probe:fallback_default");
    expect(truth.configuredModelIsHermes).toBe(true);
  });
});
