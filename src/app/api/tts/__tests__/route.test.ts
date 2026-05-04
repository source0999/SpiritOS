import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/tts/route";
import {
  decodeTtsVoiceNameFromHeader,
  encodeTtsVoiceNameForHeader,
  HEADER_TTS_VOICE_NAME_ENCODED,
} from "@/lib/tts/safe-tts-headers";

describe("POST /api/tts", () => {
  const origFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = origFetch;
    delete process.env.PIPER_TTS_URL;
    delete process.env.TTS_PROVIDER;
    delete process.env.ELEVENLABS_API_KEY;
    delete process.env.ELEVENLABS_VOICE_ID;
    delete process.env.ELEVENLABS_VOICE_SPEED;
    delete process.env.ELEVENLABS_VOICE_ALLOWLIST;
    delete process.env.ELEVENLABS_VOICE_ALLOWLIST_JSON;
    vi.restoreAllMocks();
  });

  it("returns 400 on invalid JSON", async () => {
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: "{",
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
  });

  it("returns 400 when text missing", async () => {
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({ voice: "fable" }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
  });

  it("returns 503 when Piper upstream fetch throws", async () => {
    process.env.TTS_PROVIDER = "piper";
    process.env.PIPER_TTS_URL = "http://piper.test";
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("ECONNREFUSED"));
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({ text: "hello" }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(503);
    const j = (await res.json()) as { error: string; provider: string };
    expect(j.error).toBe("TTS provider unreachable");
    expect(j.provider).toBe("piper");
  });

  it("returns 503 when Piper upstream is not ok", async () => {
    process.env.PIPER_TTS_URL = "http://piper.test";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response("nope", { status: 500, statusText: "Internal Error" }),
    );
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({ text: "hello" }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(503);
  });

  it("returns 503 JSON when ElevenLabs key missing with TTS_PROVIDER=elevenlabs", async () => {
    process.env.TTS_PROVIDER = "elevenlabs";
    delete process.env.ELEVENLABS_API_KEY;
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({ text: "hello" }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(503);
    const j = (await res.json()) as { error: string; provider: string };
    expect(j.error).toBe("ElevenLabs API key missing");
    expect(j.provider).toBe("elevenlabs");
  });

  it("proxies successful audio with content-type and X-Spirit-TTS-Provider", async () => {
    process.env.PIPER_TTS_URL = "http://piper.test";
    const wav = new Uint8Array([1, 2, 3, 4]).buffer;
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(wav, {
        status: 200,
        headers: { "Content-Type": "audio/wav" },
      }),
    );
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({ text: "hi" }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(200);
    expect(res.headers.get("Content-Type")).toBe("audio/wav");
    expect(res.headers.get("X-Spirit-TTS-Provider")).toBe("piper");
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(res.headers.get("X-Spirit-TTS-Speed")).toBe("1.12");
    expect(res.headers.get(HEADER_TTS_VOICE_NAME_ENCODED)).toBe(
      encodeTtsVoiceNameForHeader("fable"),
    );
    const body = await res.arrayBuffer();
    expect(new Uint8Array(body).length).toBe(4);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://piper.test/v1/audio/speech",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });

  it("returns 400 when speed is not a finite number", async () => {
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({ text: "hi", speed: "1.12" }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
  });

  it("clamps speed and sets X-Spirit-TTS-Speed for ElevenLabs", async () => {
    process.env.TTS_PROVIDER = "elevenlabs";
    process.env.ELEVENLABS_API_KEY = "secret-eleven-key";
    process.env.ELEVENLABS_VOICE_ID = "vid";
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(new Uint8Array([9, 9]).buffer, {
        status: 200,
        headers: { "Content-Type": "audio/mpeg" },
      }),
    );
    globalThis.fetch = mockFetch;
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({ text: "hi", speed: 9 }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(200);
    expect(res.headers.get("X-Spirit-TTS-Speed")).toBe("1.2");
    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(init.body as string);
    expect(body.voice_settings.speed).toBe(1.2);
  });

  it("passes voiceId to ElevenLabs URL and echoes voice headers", async () => {
    process.env.TTS_PROVIDER = "elevenlabs";
    process.env.ELEVENLABS_API_KEY = "secret-eleven-key";
    process.env.ELEVENLABS_VOICE_ID = "vid";
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(new Uint8Array([2]).buffer, {
        status: 200,
        headers: { "Content-Type": "audio/mpeg" },
      }),
    );
    globalThis.fetch = mockFetch;
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({
        text: "hi",
        voiceId: "otherVid",
        voiceName: "Clarice",
      }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(200);
    expect(res.headers.get("X-Spirit-TTS-Voice-Id")).toBe("otherVid");
    const enc = res.headers.get(HEADER_TTS_VOICE_NAME_ENCODED);
    expect(enc).toBeTruthy();
    expect(decodeTtsVoiceNameFromHeader(enc)).toBe("Clarice");
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("text-to-speech/otherVid");
  });

  it("ElevenLabs upstream failure falls back to Piper; final 503 has no API key", async () => {
    process.env.TTS_PROVIDER = "elevenlabs";
    process.env.ELEVENLABS_API_KEY = "secret-eleven-key";
    process.env.PIPER_TTS_URL = "http://piper.test";
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(new Response("upstream boom", { status: 500 }))
      .mockResolvedValueOnce(new Response("piper also dead", { status: 500 }));
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({ text: "hi" }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(503);
    const raw = await res.text();
    expect(raw).not.toContain("secret-eleven-key");
  });

  it("encodes Unicode voiceName in header without throwing", async () => {
    process.env.TTS_PROVIDER = "elevenlabs";
    process.env.ELEVENLABS_API_KEY = "secret-eleven-key";
    process.env.ELEVENLABS_VOICE_ID = "vid";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(new Uint8Array([2]).buffer, {
        status: 200,
        headers: { "Content-Type": "audio/mpeg" },
      }),
    );
    const name = "Charlotte – Warm, Clear \u{1F7E2}";
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({ text: "hi", voiceId: "v1", voiceName: name }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(200);
    const enc = res.headers.get(HEADER_TTS_VOICE_NAME_ENCODED);
    expect(enc).toBeTruthy();
    expect(decodeTtsVoiceNameFromHeader(enc)).toBe(name);
  });

  it("uses allowlisted default voice id when body omits voiceId", async () => {
    process.env.TTS_PROVIDER = "elevenlabs";
    process.env.ELEVENLABS_API_KEY = "k";
    process.env.ELEVENLABS_VOICE_ALLOWLIST =
      "Zed:zzzzzzzzzzzz,Clarice:claricevoice1";
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(new Uint8Array([3]).buffer, {
        status: 200,
        headers: { "Content-Type": "audio/mpeg" },
      }),
    );
    globalThis.fetch = mockFetch;
    const req = new Request("http://localhost/api/tts", {
      method: "POST",
      body: JSON.stringify({ text: "hi" }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await POST(req);
    expect(res.status).toBe(200);
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("text-to-speech/claricevoice1");
  });
});
