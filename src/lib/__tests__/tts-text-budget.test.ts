import { describe, expect, it } from "vitest";

import {
  pickTtsSpeakPayload,
  splitTextIntoTtsChunks,
  summarizeTextForTts,
  TTS_TEXT_LIMIT,
} from "@/lib/tts/tts-text-budget";

describe("tts-text-budget", () => {
  it("summarizeTextForTts stays within TTS_TEXT_LIMIT", () => {
    const s = summarizeTextForTts("# Title\n\n" + "word ".repeat(400));
    expect(s.length).toBeLessThanOrEqual(TTS_TEXT_LIMIT);
  });

  it("splitTextIntoTtsChunks never exceeds TTS_TEXT_LIMIT", () => {
    const raw = "para ".repeat(500);
    const chunks = splitTextIntoTtsChunks(raw);
    expect(chunks.length).toBeGreaterThan(1);
    for (const c of chunks) {
      expect(c.length).toBeLessThanOrEqual(TTS_TEXT_LIMIT);
    }
  });

  it("pickTtsSpeakPayload summary path for long text", () => {
    const t = "x".repeat(900);
    const p = pickTtsSpeakPayload(t, "summary");
    expect(p.segments.length).toBe(1);
    expect(p.segments[0]!.length).toBeLessThanOrEqual(TTS_TEXT_LIMIT);
    expect(p.spokenSummaryLine).toContain("summary");
  });

  it("pickTtsSpeakPayload full-chunks splits long text", () => {
    const t = "Sentence one. Sentence two. " + "y".repeat(1200);
    const p = pickTtsSpeakPayload(t, "full-chunks");
    expect(p.segments.length).toBeGreaterThan(1);
    for (const c of p.segments) {
      expect(c.length).toBeLessThanOrEqual(TTS_TEXT_LIMIT);
    }
  });
});
