import "server-only";

import {
  clampTtsVoiceSpeed,
  TTS_SPEED_DEFAULT,
} from "@/lib/tts/voice-speed";
import {
  parseElevenLabsVoiceAllowlistFromEnv,
  pickDefaultElevenLabsVoice,
  sortElevenLabsVoicesForUi,
} from "@/lib/server/elevenlabs-voices";

// ── tts-provider — Piper + ElevenLabs server-side (Prompt 9C; no keys to client) ───

export type TtsProvider = "piper" | "elevenlabs";

export type TtsRequestInput = {
  text: string;
  /** Piper OpenAI-style voice name (e.g. fable). */
  voice?: string;
  /** ElevenLabs `voice_id` from client Voice picker; Piper ignores. */
  voiceId?: string;
  /** Client label for response headers / latency line — not used to pick ElevenLabs URL. */
  voiceName?: string;
  language?: string;
  responseFormat?: "wav" | "mp3";
  /** Client override (e.g. Voice settings); clamped 0.7–1.2. ElevenLabs only. */
  speed?: number;
};

export type TtsProviderResult = {
  audio: ArrayBuffer;
  contentType: string;
  provider: TtsProvider;
  upstreamMs?: number;
  /** Applied voice speed (ElevenLabs voice_settings; echoed for /api/tts headers). */
  speed?: number;
  /** ElevenLabs voice_id applied (echoed for client latency line). */
  voiceId?: string;
  /** Friendly label (from client `voiceName` or Piper `voice`). */
  voiceName?: string;
};

export class TtsProviderError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly provider: TtsProvider,
    public readonly detail?: string,
    public readonly code?: "elevenlabs_missing_key",
  ) {
    super(message);
    this.name = "TtsProviderError";
  }
}

const FETCH_TIMEOUT_MS = 60_000;

function envTtsVoiceSpeed(): number {
  const raw = process.env.ELEVENLABS_VOICE_SPEED;
  const v = raw === undefined || raw === "" ? NaN : Number.parseFloat(String(raw).trim());
  if (!Number.isFinite(v)) return TTS_SPEED_DEFAULT;
  return clampTtsVoiceSpeed(v);
}

/**
 * Final speed: finite client `override` wins (clamped), else env default (clamped).
 */
export function resolveTtsVoiceSpeed(override?: number | null): number {
  if (typeof override === "number" && Number.isFinite(override)) {
    return clampTtsVoiceSpeed(override);
  }
  return envTtsVoiceSpeed();
}

function resolveElevenLabsVoiceIdFromInput(input: TtsRequestInput): string {
  const req = input.voiceId?.trim();
  if (req) return req;
  const parsed = parseElevenLabsVoiceAllowlistFromEnv();
  if (parsed.explicitVoices.length > 0) {
    const picked = pickDefaultElevenLabsVoice(sortElevenLabsVoicesForUi(parsed.explicitVoices));
    if (picked.defaultVoiceId) return picked.defaultVoiceId;
  }
  return (
    process.env.ELEVENLABS_DEFAULT_VOICE_ID?.trim() ||
    process.env.ELEVENLABS_VOICE_ID?.trim() ||
    "fgDJOgmENIR82PueQrVs"
  );
}

function abortTimeout(): AbortSignal {
  try {
    return AbortSignal.timeout(FETCH_TIMEOUT_MS);
  } catch {
    const c = new AbortController();
    const t = setTimeout(() => c.abort(), FETCH_TIMEOUT_MS);
    void t.unref?.();
    return c.signal;
  }
}

export function getTtsProvider(): TtsProvider {
  const raw = process.env.TTS_PROVIDER?.trim().toLowerCase();
  if (raw === "elevenlabs") return "elevenlabs";
  if (raw === "piper" || raw === "" || raw === undefined) return "piper";
  console.warn(`[tts] unknown TTS_PROVIDER "${raw}", falling back to piper`);
  return "piper";
}

export async function synthesizeWithPiper(
  input: TtsRequestInput,
): Promise<TtsProviderResult> {
  const t0 = Date.now();
  const voice =
    input.voice?.trim() ||
    process.env.PIPER_TTS_VOICE?.trim() ||
    "fable";
  const language = input.language?.trim() || "en";
  const responseFormat = input.responseFormat ?? "wav";

  const base = process.env.PIPER_TTS_URL?.trim() || "http://localhost:5200";
  const endpoint = `${base.replace(/\/$/, "")}/v1/audio/speech`;

  const upstreamBody = {
    model: "tts-1",
    voice,
    input: input.text,
    response_format: responseFormat,
    language,
  };

  let upstream: Response;
  try {
    upstream = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(upstreamBody),
      signal: abortTimeout(),
    });
  } catch (e) {
    const detail = e instanceof Error ? e.message : String(e);
    throw new TtsProviderError("TTS provider unreachable", 503, "piper", detail);
  }

  if (!upstream.ok) {
    const detail = await upstream.text().catch(() => upstream.statusText);
    throw new TtsProviderError("TTS provider unreachable", 503, "piper", detail);
  }

  const audio = await upstream.arrayBuffer();
  const contentType =
    upstream.headers.get("content-type") ||
    (responseFormat === "mp3" ? "audio/mpeg" : "audio/wav");

  const speed = resolveTtsVoiceSpeed(input.speed ?? null);

  return {
    audio,
    contentType,
    provider: "piper",
    upstreamMs: Date.now() - t0,
    speed,
    voiceName: voice,
  };
}

export async function synthesizeWithElevenLabs(
  input: TtsRequestInput,
): Promise<TtsProviderResult> {
  const key = process.env.ELEVENLABS_API_KEY?.trim();
  if (!key) {
    throw new TtsProviderError(
      "ElevenLabs API key missing",
      503,
      "elevenlabs",
      "Set ELEVENLABS_API_KEY",
      "elevenlabs_missing_key",
    );
  }

  const voiceId = resolveElevenLabsVoiceIdFromInput(input);
  const echoVoiceName = input.voiceName?.trim() || undefined;
  const modelId =
    process.env.ELEVENLABS_MODEL_ID?.trim() || "eleven_turbo_v2_5";
  const outputFormat =
    process.env.ELEVENLABS_OUTPUT_FORMAT?.trim() || "mp3_44100_128";

  const speed = resolveTtsVoiceSpeed(input.speed ?? null);

  const t0 = Date.now();
  const url = new URL(
    `https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(voiceId)}`,
  );
  url.searchParams.set("output_format", outputFormat);

  const body = {
    text: input.text,
    model_id: modelId,
    voice_settings: {
      stability: 0.45,
      similarity_boost: 0.75,
      style: 0.25,
      use_speaker_boost: true,
      speed,
    },
  };

  let res: Response;
  try {
    res = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "xi-api-key": key,
        "Content-Type": "application/json",
        Accept: "audio/mpeg, audio/*, */*",
      },
      body: JSON.stringify(body),
      signal: abortTimeout(),
    });
  } catch (e) {
    const detail = e instanceof Error ? e.message : String(e);
    throw new TtsProviderError("TTS provider unreachable", 503, "elevenlabs", detail);
  }

  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new TtsProviderError(
      "TTS provider unreachable",
      res.status >= 400 && res.status < 600 ? res.status : 503,
      "elevenlabs",
      detail.slice(0, 500),
    );
  }

  const audio = await res.arrayBuffer();
  const contentType =
    res.headers.get("content-type")?.split(";")[0]?.trim() || "audio/mpeg";

  return {
    audio,
    contentType,
    provider: "elevenlabs",
    upstreamMs: Date.now() - t0,
    speed,
    voiceId,
    voiceName: echoVoiceName,
  };
}

/**
 * Primary = env TTS_PROVIDER; ElevenLabs errors fall back to Piper when primary was ElevenLabs.
 */
export async function synthesizeSpeech(
  input: TtsRequestInput,
): Promise<TtsProviderResult> {
  const primary = getTtsProvider();

  if (primary === "elevenlabs") {
    try {
      return await synthesizeWithElevenLabs(input);
    } catch (e) {
      if (
        e instanceof TtsProviderError &&
        e.code === "elevenlabs_missing_key"
      ) {
        throw e;
      }
      console.warn("[tts] ElevenLabs failed, falling back to Piper:", e);
      return await synthesizeWithPiper(input);
    }
  }

  return await synthesizeWithPiper(input);
}
