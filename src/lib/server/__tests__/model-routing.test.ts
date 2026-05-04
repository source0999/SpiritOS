import { afterEach, describe, expect, it } from "vitest";

import {
  getOracleModelId,
  getSpiritChatModelId,
  resolveOllamaModelId,
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
});
