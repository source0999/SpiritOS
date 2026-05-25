import { afterEach, describe, expect, it } from "vitest";

import {
  getAbliteratedChatModelId,
  getOracleModelId,
  getSpiritChatModelId,
  resolveOllamaModelId,
  SPIRIT_ABLITERATED_CHAT_MODEL_ID,
} from "@/lib/server/model-routing";

describe("model-routing", () => {
  afterEach(() => {
    delete process.env.OLLAMA_MODEL;
    delete process.env.ORACLE_OLLAMA_MODEL;
  });

  it("getSpiritChatModelId reads OLLAMA_MODEL", () => {
    process.env.OLLAMA_MODEL = "hermes4:latest";
    expect(getSpiritChatModelId()).toBe("hermes4:latest");
  });

  it("getOracleModelId falls back to chat model when ORACLE_OLLAMA_MODEL unset", () => {
    process.env.OLLAMA_MODEL = "chat-model";
    delete process.env.ORACLE_OLLAMA_MODEL;
    expect(getOracleModelId()).toBe("chat-model");
  });

  it("getOracleModelId uses ORACLE_OLLAMA_MODEL when set", () => {
    process.env.OLLAMA_MODEL = "chat-model";
    process.env.ORACLE_OLLAMA_MODEL = "oracle-fast";
    expect(getOracleModelId()).toBe("oracle-fast");
  });

  it("resolveOllamaModelId picks lane", () => {
    process.env.OLLAMA_MODEL = "a";
    process.env.ORACLE_OLLAMA_MODEL = "b";
    expect(resolveOllamaModelId("chat")).toBe("a");
    expect(resolveOllamaModelId("oracle")).toBe("b");
  });

  it("resolveOllamaModelId picks the fixed 8B abliterated chat lane per request", () => {
    process.env.OLLAMA_MODEL = "a";
    process.env.ORACLE_OLLAMA_MODEL = "b";
    expect(getAbliteratedChatModelId()).toBe(SPIRIT_ABLITERATED_CHAT_MODEL_ID);
    expect(resolveOllamaModelId("chat", { abliteratedModeEnabled: true })).toBe(
      "hermes3:8b-abliterated",
    );
    expect(resolveOllamaModelId("oracle", { abliteratedModeEnabled: true })).toBe(
      "b",
    );
  });
});
