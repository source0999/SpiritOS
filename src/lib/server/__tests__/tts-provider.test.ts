import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getTtsProvider,
  resolveTtsVoiceSpeed,
  synthesizeSpeech,
  synthesizeWithElevenLabs,
  synthesizeWithPiper,
} from "@/lib/server/tts-provider";

describe("tts-provider", () => {
  const origFetch = globalThis.fetch;

  afterEach(() => {
    delete process.env.TTS_PROVIDER;
    delete process.env.ELEVENLABS_API_KEY;
    delete process.env.ELEVENLABS_VOICE_ID;
    delete process.env.ELEVENLABS_MODEL_ID;
    delete process.env.ELEVENLABS_OUTPUT_FORMAT;
    delete process.env.ELEVENLABS_VOICE_SPEED;
    delete process.env.PIPER_TTS_URL;
    globalThis.fetch = origFetch;
    vi.restoreAllMocks();
  });

  it("getTtsProvider: unknown TTS_PROVIDER falls back to piper with warn", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    process.env.TTS_PROVIDER = "kokoro";
    expect(getTtsProvider()).toBe("piper");
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it("resolveTtsVoiceSpeed uses env default when unset", () => {
    delete process.env.ELEVENLABS_VOICE_SPEED;
    expect(resolveTtsVoiceSpeed(undefined)).toBeCloseTo(1.12, 5);
  });

  it("resolveTtsVoiceSpeed reads ELEVENLABS_VOICE_SPEED when no override", () => {
    process.env.ELEVENLABS_VOICE_SPEED = "0.95";
    expect(resolveTtsVoiceSpeed(null)).toBeCloseTo(0.95, 5);
  });

  it("resolveTtsVoiceSpeed clamps override over env", () => {
    process.env.ELEVENLABS_VOICE_SPEED = "0.9";
    expect(resolveTtsVoiceSpeed(99)).toBe(1.2);
    expect(resolveTtsVoiceSpeed(0.01)).toBe(0.7);
  });

  it("synthesizeWithElevenLabs throws safe error when API key missing", async () => {
    delete process.env.ELEVENLABS_API_KEY;
    await expect(synthesizeWithElevenLabs({ text: "hi" })).rejects.toMatchObject({
      code: "elevenlabs_missing_key",
      provider: "elevenlabs",
    });
  });

  it("synthesizeWithElevenLabs builds correct voice endpoint", async () => {
    process.env.ELEVENLABS_API_KEY = "test-key";
    process.env.ELEVENLABS_VOICE_ID = "voiceABC";
    process.env.ELEVENLABS_MODEL_ID = "eleven_turbo_v2_5";
    process.env.ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128";

    const mockFetch = vi.fn().mockResolvedValue(
      new Response(new Uint8Array([1, 2]).buffer, {
        status: 200,
        headers: { "Content-Type": "audio/mpeg" },
      }),
    );
    globalThis.fetch = mockFetch;

    await synthesizeWithElevenLabs({ text: "hello" });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("https://api.elevenlabs.io/v1/text-to-speech/voiceABC");
    expect(url).toContain("output_format=mp3_44100_128");
    expect(init.method).toBe("POST");
    const headers = init.headers as Record<string, string>;
    expect(headers["xi-api-key"]).toBe("test-key");
    const body = JSON.parse(init.body as string);
    expect(body.text).toBe("hello");
    expect(body.model_id).toBe("eleven_turbo_v2_5");
    expect(body.voice_settings).toMatchObject({
      stability: 0.45,
      similarity_boost: 0.75,
      style: 0.25,
      use_speaker_boost: true,
      speed: expect.closeTo(1.12, 5),
    });
  });

  it("synthesizeWithElevenLabs uses request speed over env", async () => {
    process.env.ELEVENLABS_API_KEY = "test-key";
    process.env.ELEVENLABS_VOICE_ID = "voiceABC";
    process.env.ELEVENLABS_MODEL_ID = "eleven_turbo_v2_5";
    process.env.ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128";
    process.env.ELEVENLABS_VOICE_SPEED = "0.88";

    const mockFetch = vi.fn().mockResolvedValue(
      new Response(new Uint8Array([1, 2]).buffer, {
        status: 200,
        headers: { "Content-Type": "audio/mpeg" },
      }),
    );
    globalThis.fetch = mockFetch;

    await synthesizeWithElevenLabs({ text: "hello", speed: 1.18 });

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(init.body as string);
    expect(body.voice_settings.speed).toBeCloseTo(1.18, 5);
  });

  it("synthesizeWithElevenLabs uses voiceId from request input", async () => {
    process.env.ELEVENLABS_API_KEY = "test-key";
    process.env.ELEVENLABS_VOICE_ID = "legacyVid";
    process.env.ELEVENLABS_MODEL_ID = "eleven_turbo_v2_5";
    process.env.ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128";

    const mockFetch = vi.fn().mockResolvedValue(
      new Response(new Uint8Array([1, 2]).buffer, {
        status: 200,
        headers: { "Content-Type": "audio/mpeg" },
      }),
    );
    globalThis.fetch = mockFetch;

    await synthesizeWithElevenLabs({ text: "yo", voiceId: "customVid" });

    const [url] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/text-to-speech/customVid");
  });

  it("echoes voiceName in provider result for headers/UI", async () => {
    process.env.ELEVENLABS_API_KEY = "test-key";
    process.env.ELEVENLABS_VOICE_ID = "legacyVid";
    process.env.ELEVENLABS_MODEL_ID = "eleven_turbo_v2_5";
    process.env.ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(new Uint8Array([1]).buffer, {
        status: 200,
        headers: { "Content-Type": "audio/mpeg" },
      }),
    );
    const r = await synthesizeWithElevenLabs({
      text: "yo",
      voiceId: "customVid",
      voiceName: "Ada",
    });
    expect(r.voiceName).toBe("Ada");
    expect(r.voiceId).toBe("customVid");
  });

  it("synthesizeWithPiper posts /v1/audio/speech", async () => {
    process.env.PIPER_TTS_URL = "http://piper.test";
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(new Uint8Array([9]).buffer, {
        status: 200,
        headers: { "Content-Type": "audio/wav" },
      }),
    );
    globalThis.fetch = mockFetch;

    const r = await synthesizeWithPiper({ text: "yo", responseFormat: "wav" });
    expect(r.provider).toBe("piper");
    expect(mockFetch).toHaveBeenCalledWith(
      "http://piper.test/v1/audio/speech",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"input":"yo"'),
      }),
    );
  });

  it("synthesizeSpeech uses piper when TTS_PROVIDER unset", async () => {
    delete process.env.TTS_PROVIDER;
    process.env.PIPER_TTS_URL = "http://piper.test";
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(new Uint8Array([1]).buffer, {
        status: 200,
        headers: { "Content-Type": "audio/wav" },
      }),
    );
    globalThis.fetch = mockFetch;
    const r = await synthesizeSpeech({ text: "a" });
    expect(r.provider).toBe("piper");
  });
});
