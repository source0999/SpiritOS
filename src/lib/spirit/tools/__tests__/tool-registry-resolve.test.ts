import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/server/ollama", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/server/ollama")>();
  return {
    ...actual,
    probeOllamaChatCompletionsAcceptsToolSchema: vi.fn(),
  };
});

import {
  clearReadOnlyToolProbeCache,
  resolveSpiritToolsForOllamaModel,
} from "../tool-registry";

describe("resolveSpiritToolsForOllamaModel", () => {
  beforeEach(async () => {
    clearReadOnlyToolProbeCache();
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    const { probeOllamaChatCompletionsAcceptsToolSchema } = await import("@/lib/server/ollama");
    vi.mocked(probeOllamaChatCompletionsAcceptsToolSchema).mockResolvedValue(true);
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
    clearReadOnlyToolProbeCache();
  });

  it("returns undefined when the model probe reports tools unsupported", async () => {
    const { probeOllamaChatCompletionsAcceptsToolSchema } = await import("@/lib/server/ollama");
    vi.mocked(probeOllamaChatCompletionsAcceptsToolSchema).mockResolvedValue(false);
    await expect(resolveSpiritToolsForOllamaModel("hermes4")).resolves.toBeUndefined();
    expect(probeOllamaChatCompletionsAcceptsToolSchema).toHaveBeenCalledWith("hermes4");
  });

  it("returns the four read-only tools when the probe accepts tools", async () => {
    const { probeOllamaChatCompletionsAcceptsToolSchema } = await import("@/lib/server/ollama");
    vi.mocked(probeOllamaChatCompletionsAcceptsToolSchema).mockResolvedValue(true);
    const tools = await resolveSpiritToolsForOllamaModel("llama3.1");
    expect(tools).toBeDefined();
    if (!tools) throw new Error("tools");
    expect(Object.keys(tools).sort()).toEqual(
      [
        "get_system_status",
        "list_workspace_files",
        "read_log_tail",
        "read_workspace_file",
      ].sort(),
    );
  });
});
