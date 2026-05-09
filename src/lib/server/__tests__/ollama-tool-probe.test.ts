import { afterEach, describe, expect, it, vi } from "vitest";

import { probeOllamaChatCompletionsAcceptsToolSchema } from "../ollama";

describe("probeOllamaChatCompletionsAcceptsToolSchema", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("returns false when Ollama responds 400 with does-not-support-tools", async () => {
    vi.stubEnv("OLLAMA_BASE_URL", "http://127.0.0.1:11434");
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 400,
      text: async () =>
        JSON.stringify({
          error: { message: "registry.ollama.ai/library/hermes4:latest does not support tools" },
        }),
    } as Response);

    const ok = await probeOllamaChatCompletionsAcceptsToolSchema("hermes4");
    expect(ok).toBe(false);
    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it("returns true on HTTP 200", async () => {
    vi.stubEnv("OLLAMA_BASE_URL", "http://127.0.0.1:11434");
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => '{"choices":[{"message":{"content":"."}}]}',
    } as Response);

    const ok = await probeOllamaChatCompletionsAcceptsToolSchema("llama3.1");
    expect(ok).toBe(true);
  });
});
