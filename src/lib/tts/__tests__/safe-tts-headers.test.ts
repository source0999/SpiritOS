import { describe, expect, it } from "vitest";

import {
  decodeTtsVoiceNameFromHeader,
  encodeTtsVoiceNameForHeader,
} from "@/lib/tts/safe-tts-headers";

describe("safe-tts-headers", () => {
  it("round-trips Unicode through encodeURIComponent", () => {
    const raw = "Charlotte – Warm, Clear \u{1F7E2}";
    const enc = encodeTtsVoiceNameForHeader(raw);
    expect(enc).toMatch(/^[\x00-\x7F]+$/);
    expect(decodeTtsVoiceNameFromHeader(enc)).toBe(raw);
  });

  it("decode returns null on invalid percent sequence", () => {
    expect(decodeTtsVoiceNameFromHeader("%ZZ")).toBeNull();
  });
});
