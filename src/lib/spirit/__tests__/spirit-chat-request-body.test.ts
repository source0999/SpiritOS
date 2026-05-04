import { describe, expect, it } from "vitest";

import {
  parseSpiritChatRequestBody,
  SpiritRequestValidationError,
  SPIRIT_PERSONALIZATION_SUMMARY_MAX,
} from "@/lib/spirit/spirit-chat-request-body";
import { DEFAULT_MODEL_PROFILE_ID } from "@/lib/spirit/model-profile.types";

const minimalUserMessage = {
  role: "user",
  parts: [{ type: "text", text: "hi" }],
};

describe("parseSpiritChatRequestBody", () => {
  it("accepts valid modelProfileId", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      modelProfileId: "researcher",
    });
    expect(out.modelProfileId).toBe("researcher");
  });

  it("defaults missing modelProfileId", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
    });
    expect(out.modelProfileId).toBe(DEFAULT_MODEL_PROFILE_ID);
  });

  it("defaults invalid modelProfileId string safely", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      modelProfileId: "not-a-real-profile",
    });
    expect(out.modelProfileId).toBe(DEFAULT_MODEL_PROFILE_ID);
  });

  it("defaults non-string modelProfileId", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      modelProfileId: 999,
    });
    expect(out.modelProfileId).toBe(DEFAULT_MODEL_PROFILE_ID);
  });

  it("invalid runtimeSurface strings fall back to chat", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      runtimeSurface: "nope",
    });
    expect(out.runtimeSurface).toBe("chat");
  });

  it("accepts runtimeSurface oracle", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      runtimeSurface: "oracle",
    });
    expect(out.runtimeSurface).toBe("oracle");
  });

  it("defaults runtimeSurface to chat", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
    });
    expect(out.runtimeSurface).toBe("chat");
  });

  it("accepts personalizationSummary", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      personalizationSummary: "  hello prefs  ",
    });
    expect(out.personalizationSummary).toBe("hello prefs");
  });

  it("rejects non-string personalizationSummary", () => {
    expect(() =>
      parseSpiritChatRequestBody({
        messages: [minimalUserMessage],
        personalizationSummary: 123,
      } as unknown),
    ).toThrow(SpiritRequestValidationError);
  });

  it("rejects oversized personalizationSummary", () => {
    expect(() =>
      parseSpiritChatRequestBody({
        messages: [minimalUserMessage],
        personalizationSummary: "x".repeat(SPIRIT_PERSONALIZATION_SUMMARY_MAX + 1),
      }),
    ).toThrow(SpiritRequestValidationError);
  });

  it("throws on empty messages", () => {
    expect(() =>
      parseSpiritChatRequestBody({ messages: [] }),
    ).toThrow(SpiritRequestValidationError);
  });

  it("defaults deepThinkEnabled and webSearchOptOut", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
    });
    expect(out.deepThinkEnabled).toBe(false);
    expect(out.webSearchOptOut).toBe(false);
    expect(out.teacherWebSearchEnabled).toBe(true);
  });

  it("accepts teacherWebSearchEnabled false to opt out", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      teacherWebSearchEnabled: false,
    });
    expect(out.teacherWebSearchEnabled).toBe(false);
  });

  it("accepts teacherWebSearchEnabled boolean", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      teacherWebSearchEnabled: true,
    });
    expect(out.teacherWebSearchEnabled).toBe(true);
  });

  it("accepts webSearchOptOut boolean", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      deepThinkEnabled: true,
      webSearchOptOut: true,
    });
    expect(out.deepThinkEnabled).toBe(true);
    expect(out.webSearchOptOut).toBe(true);
  });

  it("maps legacy webSearchRequested true → webSearchOptOut false", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      webSearchRequested: true,
    });
    expect(out.webSearchOptOut).toBe(false);
  });

  it("maps legacy webSearchRequested false → webSearchOptOut true", () => {
    const out = parseSpiritChatRequestBody({
      messages: [minimalUserMessage],
      webSearchRequested: false,
    });
    expect(out.webSearchOptOut).toBe(true);
  });

  it("rejects non-boolean deepThinkEnabled", () => {
    expect(() =>
      parseSpiritChatRequestBody({
        messages: [minimalUserMessage],
        deepThinkEnabled: "yes",
      } as unknown),
    ).toThrow(SpiritRequestValidationError);
  });
});
