import { NextResponse } from "next/server";

import {
  synthesizeSpeech,
  TtsProviderError,
} from "@/lib/server/tts-provider";
import {
  encodeTtsVoiceNameForHeader,
  HEADER_TTS_VOICE_NAME_ENCODED,
} from "@/lib/tts/safe-tts-headers";
import {
  parseOptionalTtsSpeedField,
  parseOptionalTtsVoiceIdField,
  parseOptionalTtsVoiceNameField,
} from "@/lib/tts/tts-http";

// ── /api/tts — same-origin TTS (Piper / ElevenLabs); no browser → secrets (Prompt 9C) ─
// > Prompt 9K: voice name headers are percent-encoded — raw Unicode en-dash nuked ByteString on Tailscale.
export const dynamic = "force-dynamic";
export const maxDuration = 120;

const MAX_CHARS = 800;

type TtsBody = {
  text?: unknown;
  voice?: unknown;
  voiceId?: unknown;
  voiceName?: unknown;
  language?: unknown;
  responseFormat?: unknown;
  speed?: unknown;
};

function isWavOrMp3(v: unknown): v is "wav" | "mp3" {
  return v === "wav" || v === "mp3";
}

function buildTtsSuccessHeaders(result: {
  contentType: string;
  provider: string;
  upstreamMs?: number;
  speed?: number;
  voiceId?: string;
  voiceName?: string;
}): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": result.contentType,
    "Cache-Control": "no-store",
    "X-Spirit-TTS-Provider": result.provider,
  };
  if (typeof result.upstreamMs === "number" && Number.isFinite(result.upstreamMs)) {
    headers["X-Spirit-TTS-Upstream-Ms"] = String(Math.round(result.upstreamMs));
  }
  if (typeof result.speed === "number" && Number.isFinite(result.speed)) {
    headers["X-Spirit-TTS-Speed"] = String(result.speed);
  }
  if (typeof result.voiceId === "string" && result.voiceId.trim()) {
    headers["X-Spirit-TTS-Voice-Id"] = result.voiceId.trim();
  }
  if (typeof result.voiceName === "string" && result.voiceName.trim()) {
    headers[HEADER_TTS_VOICE_NAME_ENCODED] = encodeTtsVoiceNameForHeader(result.voiceName);
  }
  return headers;
}

export async function POST(req: Request) {
  let json: unknown;
  try {
    json = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (!json || typeof json !== "object") {
    return NextResponse.json({ error: "Request body must be an object" }, { status: 400 });
  }

  const body = json as TtsBody;
  if (typeof body.text !== "string") {
    return NextResponse.json({ error: "text is required" }, { status: 400 });
  }

  const text = body.text.trim();
  if (!text) {
    return NextResponse.json({ error: "text cannot be empty" }, { status: 400 });
  }
  if (text.length > MAX_CHARS) {
    return NextResponse.json(
      { error: `text exceeds ${MAX_CHARS} characters` },
      { status: 400 },
    );
  }

  const speedParse = parseOptionalTtsSpeedField(body as Record<string, unknown>);
  if (!speedParse.ok) {
    return NextResponse.json({ error: speedParse.message }, { status: 400 });
  }

  const voiceIdParse = parseOptionalTtsVoiceIdField(body as Record<string, unknown>);
  if (!voiceIdParse.ok) {
    return NextResponse.json({ error: voiceIdParse.message }, { status: 400 });
  }

  const voiceNameParse = parseOptionalTtsVoiceNameField(body as Record<string, unknown>);
  if (!voiceNameParse.ok) {
    return NextResponse.json({ error: voiceNameParse.message }, { status: 400 });
  }

  const voice =
    typeof body.voice === "string" && body.voice.trim()
      ? body.voice.trim()
      : undefined;
  const language =
    typeof body.language === "string" && body.language.trim()
      ? body.language.trim()
      : undefined;
  const responseFormat = isWavOrMp3(body.responseFormat)
    ? body.responseFormat
    : undefined;

  let result: Awaited<ReturnType<typeof synthesizeSpeech>>;
  try {
    result = await synthesizeSpeech({
      text,
      voice,
      voiceId: voiceIdParse.value,
      voiceName: voiceNameParse.value,
      language,
      responseFormat,
      speed: speedParse.value,
    });
  } catch (e) {
    if (e instanceof TtsProviderError) {
      if (e.code === "elevenlabs_missing_key") {
        return NextResponse.json(
          { error: "ElevenLabs API key missing", provider: e.provider },
          { status: 503 },
        );
      }
      return NextResponse.json(
        {
          error: "TTS provider unreachable",
          provider: e.provider,
          detail: e.detail ?? e.message,
        },
        { status: 503 },
      );
    }
    const detail = e instanceof Error ? e.message : String(e);
    return NextResponse.json(
      { error: "TTS provider unreachable", provider: "piper", detail },
      { status: 503 },
    );
  }

  try {
    const headers = buildTtsSuccessHeaders(result);
    return new NextResponse(result.audio, {
      status: 200,
      headers,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    const isByte =
      e instanceof TypeError && /ByteString|byte string|255/i.test(msg);
    console.error("[api/tts] response header build failed", msg);
    return NextResponse.json(
      {
        error: "TTS provider unreachable",
        provider: result.provider,
        detail: isByte ? "Invalid TTS response header value" : msg.slice(0, 200),
      },
      { status: 503 },
    );
  }
}
