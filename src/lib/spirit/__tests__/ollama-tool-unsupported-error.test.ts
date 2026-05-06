import { APICallError } from "ai";
import { describe, expect, it } from "vitest";

import { isOllamaModelToolUnsupportedError } from "../ollama-tool-unsupported-error";

describe("isOllamaModelToolUnsupportedError", () => {
  it("returns true for Ollama does-not-support-tools APICallError", () => {
    const err = new APICallError({
      message: "registry.ollama.ai/library/hermes4:latest does not support tools",
      url: "http://100.111.32.31:11434/v1/chat/completions",
      requestBodyValues: {},
      statusCode: 400,
      responseBody:
        '{"error":{"message":"registry.ollama.ai/library/hermes4:latest does not support tools"}}',
    });
    expect(isOllamaModelToolUnsupportedError(err)).toBe(true);
  });

  it("returns true when only responseBody mentions unsupported tools", () => {
    const err = new APICallError({
      message: "Bad Request",
      url: "http://localhost/v1/chat/completions",
      requestBodyValues: {},
      statusCode: 400,
      responseBody: '{"error":{"message":"model does not support tools"}}',
    });
    expect(isOllamaModelToolUnsupportedError(err)).toBe(true);
  });

  it("returns false for unrelated errors", () => {
    expect(isOllamaModelToolUnsupportedError(new Error("network"))).toBe(false);
    const err = new APICallError({
      message: "rate limited",
      url: "http://localhost/v1/chat/completions",
      requestBodyValues: {},
      statusCode: 429,
    });
    expect(isOllamaModelToolUnsupportedError(err)).toBe(false);
  });
});
