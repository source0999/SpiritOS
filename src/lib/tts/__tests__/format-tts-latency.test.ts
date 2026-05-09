import { describe, expect, it } from "vitest";

import {
  formatSecondsOneDecimal,
  formatTtsErrorLabel,
  formatTtsFriendlyStartSummary,
  formatTtsFriendlySummaryLines,
  formatTtsLastVoiceLine,
  formatTtsLatency,
  formatVoiceActivityPrimaryLine,
} from "@/lib/tts/format-tts-latency";
import type { TtsLatency } from "@/lib/tts/audio-queue";

describe("formatSecondsOneDecimal", () => {
  it("formats 710ms as 0.7s", () => {
    expect(formatSecondsOneDecimal(710)).toBe("0.7s");
  });
  it("formats 5700ms as 5.7s", () => {
    expect(formatSecondsOneDecimal(5700)).toBe("5.7s");
  });
});

describe("formatTtsFriendlyStartSummary", () => {
  it("uses under 1 second in mid sub-second range", () => {
    expect(formatTtsFriendlyStartSummary({ timeToFirstAudioMs: 850 })).toBe(
      "Audio started in under 1 second",
    );
  });
  it("uses decimal seconds below 500ms threshold", () => {
    expect(formatTtsFriendlyStartSummary({ timeToFirstAudioMs: 400 })).toMatch(/0\.4s/);
  });
  it("formats multi-second start", () => {
    expect(formatTtsFriendlyStartSummary({ timeToFirstAudioMs: 1700, provider: "elevenlabs" })).toBe(
      "Audio started in 1.7s",
    );
  });
  it("falls back to fetch+decode when ttfa missing", () => {
    expect(
      formatTtsFriendlyStartSummary({
        provider: "elevenlabs",
        fetchMs: 600,
        decodeMs: 100,
      }),
    ).toBe("Audio started in under 1 second");
  });
  it("returns not tested when no data", () => {
    expect(formatTtsFriendlyStartSummary(undefined)).toBe("Audio has not been tested yet");
  });
});

describe("formatTtsLastVoiceLine", () => {
  it("formats full ElevenLabs-style metrics", () => {
    const lat: TtsLatency = {
      provider: "elevenlabs",
      upstreamMs: 820,
      fetchMs: 940,
      decodeMs: 35,
      totalMs: 1100,
      timeToFirstAudioMs: 990,
      playbackMode: "html-audio",
    };
    expect(formatTtsLastVoiceLine(lat)).toBe(
      "Last voice: ElevenLabs · upstream 820ms · fetch 940ms · decode 35ms · time-to-audio 990ms · playback span 1.1s · HTMLAudioElement",
    );
    expect(formatTtsLatency(lat)).toBe(formatTtsLastVoiceLine(lat));
  });

  it("includes speed when present on latency", () => {
    const lat: TtsLatency = {
      provider: "elevenlabs",
      speed: 1.12,
      upstreamMs: 428,
      fetchMs: 533,
      totalMs: 5700,
      timeToFirstAudioMs: 800,
      playbackMode: "html-audio",
    };
    const line = formatTtsLastVoiceLine(lat);
    expect(line).toContain("speed 1.12x");
    expect(line).toContain("ElevenLabs");
    expect(line).toContain("playback span");
    expect(formatTtsLatency(lat)).toBe(formatTtsLastVoiceLine(lat));
  });

  it("includes speed and voice name in last voice line", () => {
    const lat: TtsLatency = {
      provider: "elevenlabs",
      voiceName: "Clarice",
      speed: 1.12,
      upstreamMs: 428,
      fetchMs: 533,
      totalMs: 5700,
      playbackMode: "html-audio",
    };
    const line = formatTtsLastVoiceLine(lat);
    expect(line).toContain("Clarice");
    expect(line).toContain("speed 1.12x");
  });

  it("handles Piper and AudioContext playback label", () => {
    const lat: TtsLatency = {
      provider: "piper",
      fetchMs: 200,
      decodeMs: 12,
      totalMs: 450,
      playbackMode: "audio-context",
    };
    expect(formatTtsLastVoiceLine(lat)).toContain("Piper");
    expect(formatTtsLastVoiceLine(lat)).toContain("AudioContext");
  });

  it("shows Not tested yet when metrics are missing", () => {
    expect(formatTtsLastVoiceLine(undefined)).toBe("Last voice: Not tested yet");
    expect(formatTtsLastVoiceLine({})).toBe("Last voice: Not tested yet");
  });

  it("includes optional start delay when > 0", () => {
    const lat: TtsLatency = {
      provider: "elevenlabs",
      fetchMs: 100,
      totalMs: 200,
      startDelayMs: 250,
      playbackMode: "html-audio",
    };
    expect(formatTtsLastVoiceLine(lat)).toContain("start delay 250ms");
  });
});

describe("formatTtsErrorLabel", () => {
  it("normalizes enable-audio / blocked copy", () => {
    expect(formatTtsErrorLabel("Tap Enable audio, then try Speak again.")).toContain(
      "Audio blocked",
    );
    expect(formatTtsErrorLabel("NotAllowedError")).toContain("Audio blocked");
  });

  it("labels aborted-ish copy", () => {
    expect(formatTtsErrorLabel("AbortError: aborted")).toBe("aborted");
  });
});

describe("formatVoiceActivityPrimaryLine", () => {
  it("prefers friendly error over latency", () => {
    expect(
      formatVoiceActivityPrimaryLine({
        lastLatency: { provider: "piper", fetchMs: 1, totalMs: 2 },
        lastError: "Tap Enable audio, then try Speak again.",
      }),
    ).toMatch(/Last voice error:.*Audio blocked/);
  });

  it("shows latency when present even if last interrupt note is set", () => {
    const lat: TtsLatency = { provider: "elevenlabs", fetchMs: 100, totalMs: 200 };
    expect(
      formatVoiceActivityPrimaryLine({
        lastLatency: lat,
        lastVoiceNote: "interrupted",
      }),
    ).toBe(formatTtsLastVoiceLine(lat));
  });

  it("shows interrupted when no latency yet", () => {
    expect(
      formatVoiceActivityPrimaryLine({ lastVoiceNote: "interrupted" }),
    ).toBe("Last voice: interrupted");
  });
});

describe("formatTtsFriendlySummaryLines", () => {
  it("formats success with audio start and ElevenLabs response in seconds", () => {
    const lines = formatTtsFriendlySummaryLines({
      lastLatency: {
        provider: "elevenlabs",
        voiceName: "Clarice",
        speed: 1.08,
        upstreamMs: 710,
        timeToFirstAudioMs: 1200,
        totalMs: 5700,
        playbackMode: "audio-context",
      },
    });
    expect(lines[0]).toMatch(/Audio started in 1\.2s/);
    expect(lines[1]).toMatch(/ElevenLabs responded in 0\.7s/);
    expect(lines[2]).toContain("WebAudio");
    expect(lines[3]).toContain("Clarice");
  });

  it("formats error as failed line", () => {
    const lines = formatTtsFriendlySummaryLines({
      lastError: "Internal Server Error",
    });
    expect(lines[0]).toMatch(/Last voice failed/);
  });

  it("formats interrupted without latency", () => {
    expect(formatTtsFriendlySummaryLines({ lastVoiceNote: "interrupted" })).toEqual([
      "Last voice was interrupted",
    ]);
  });
});
