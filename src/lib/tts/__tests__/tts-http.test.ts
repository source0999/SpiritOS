import { describe, expect, it } from "vitest";

import { parseOptionalTtsSpeedField, parseOptionalTtsVoiceIdField, parseOptionalTtsVoiceNameField } from "@/lib/tts/tts-http";

describe("parseOptionalTtsSpeedField", () => {
  it("returns undefined when speed absent", () => {
    expect(parseOptionalTtsSpeedField({ text: "hi" })).toEqual({ ok: true, value: undefined });
  });

  it("returns undefined for null speed", () => {
    expect(parseOptionalTtsSpeedField({ speed: null })).toEqual({ ok: true, value: undefined });
  });

  it("accepts finite number", () => {
    expect(parseOptionalTtsSpeedField({ speed: 1.12 })).toEqual({ ok: true, value: 1.12 });
  });

  it("rejects non-number speed", () => {
    const r = parseOptionalTtsSpeedField({ speed: "1.12" });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.message).toMatch(/finite number/);
  });

  it("rejects NaN", () => {
    const r = parseOptionalTtsSpeedField({ speed: NaN });
    expect(r.ok).toBe(false);
  });
});

describe("parseOptionalTtsVoiceIdField", () => {
  it("returns undefined when absent", () => {
    expect(parseOptionalTtsVoiceIdField({ text: "hi" })).toEqual({ ok: true, value: undefined });
  });

  it("accepts trimmed string", () => {
    expect(parseOptionalTtsVoiceIdField({ voiceId: "  abc123  " })).toEqual({
      ok: true,
      value: "abc123",
    });
  });

  it("rejects non-string", () => {
    const r = parseOptionalTtsVoiceIdField({ voiceId: 1 });
    expect(r.ok).toBe(false);
  });
});

describe("parseOptionalTtsVoiceNameField", () => {
  it("returns undefined when absent", () => {
    expect(parseOptionalTtsVoiceNameField({ text: "hi" })).toEqual({ ok: true, value: undefined });
  });

  it("accepts trimmed string", () => {
    expect(parseOptionalTtsVoiceNameField({ voiceName: "  Ada  " })).toEqual({
      ok: true,
      value: "Ada",
    });
  });

  it("rejects absurd length", () => {
    const r = parseOptionalTtsVoiceNameField({ voiceName: "x".repeat(200) });
    expect(r.ok).toBe(false);
  });
});
