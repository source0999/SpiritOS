/// <reference types="vitest/globals" />

import {
  clearReadOnlyToolProbeCache,
  resolveSpiritToolsForOllamaModel,
} from "../tool-registry";

describe("resolveSpiritToolsForOllamaModel", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    clearReadOnlyToolProbeCache();
  });

  it("returns undefined before probing when local tools are disabled", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "false");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");

    await expect(resolveSpiritToolsForOllamaModel("hermes4")).resolves.toBeUndefined();
  });

  it("returns undefined before probing when tool transport is not opted in", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");

    await expect(resolveSpiritToolsForOllamaModel("hermes4")).resolves.toBeUndefined();
  });

  it("returns undefined for Coder role when file edit tools are disabled", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "false");

    await expect(
      resolveSpiritToolsForOllamaModel("hermes4", { swarmAgentRole: "coder" }),
    ).resolves.toBeUndefined();
  });

  it("returns undefined for Debugger role when sandbox tools are disabled", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_SANDBOX_TOOLS", "false");

    await expect(
      resolveSpiritToolsForOllamaModel("hermes4", { swarmAgentRole: "debugger" }),
    ).resolves.toBeUndefined();
  });
});
