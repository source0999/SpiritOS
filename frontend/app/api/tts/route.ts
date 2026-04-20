import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 120;

const XTTS_BASE_URL = process.env.XTTS_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8020";
const XTTS_TTS_URL = `${XTTS_BASE_URL}/tts`;
const XTTS_STUDIO_SPEAKERS_URL = `${XTTS_BASE_URL}/studio_speakers`;
const XTTS_DEFAULT_SPEAKER = process.env.XTTS_DEFAULT_SPEAKER?.trim();
const MAX_CHARS = 500;

type XttsSpeaker = {
  speaker_embedding: number[];
  gpt_cond_latent: number[][];
};

let cachedSpeaker: XttsSpeaker | null = null;

async function getSpeakerConditioning(): Promise<XttsSpeaker> {
  if (cachedSpeaker) return cachedSpeaker;
  const res = await fetch(XTTS_STUDIO_SPEAKERS_URL, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`studio_speakers failed with ${res.status}`);
  }
  const payload = await res.json() as Record<string, XttsSpeaker>;
  const entries = Object.entries(payload);
  if (!entries.length) throw new Error("studio_speakers returned no voices");
  const preferred =
    XTTS_DEFAULT_SPEAKER && payload[XTTS_DEFAULT_SPEAKER]
      ? payload[XTTS_DEFAULT_SPEAKER]
      : entries[0][1];
  if (!preferred?.speaker_embedding?.length || !preferred?.gpt_cond_latent?.length) {
    throw new Error("speaker payload missing conditioning vectors");
  }
  cachedSpeaker = preferred;
  return preferred;
}

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (!body || typeof body !== "object") {
    return NextResponse.json({ error: "Expected JSON object" }, { status: 400 });
  }

  const text =
    "text" in body && typeof (body as { text: unknown }).text === "string"
      ? (body as { text: string }).text.trim()
      : "";
  const language =
    "language" in body && typeof (body as { language: unknown }).language === "string"
      ? (body as { language: string }).language.trim()
      : "en";

  if (!text) return NextResponse.json({ error: "Missing text" }, { status: 400 });
  if (text.length > MAX_CHARS) {
    return NextResponse.json(
      { error: `Text too long (${text.length}/${MAX_CHARS})` },
      { status: 400 },
    );
  }

  let upstream: Response;
  let speaker: XttsSpeaker;
  try {
    speaker = await getSpeakerConditioning();
  } catch (e) {
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "tts-debug-2",
        hypothesisId: "H5",
        location: "app/api/tts/route.ts:getSpeakerConditioning",
        message: "Failed loading XTTS speaker conditioning",
        data: {
          endpoint: XTTS_STUDIO_SPEAKERS_URL,
          error: e instanceof Error ? e.message : String(e),
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    return NextResponse.json(
      { error: "XTTS speaker conditioning unavailable", detail: e instanceof Error ? e.message : String(e) },
      { status: 503 },
    );
  }

  const payload = JSON.stringify({
    text,
    language,
    speaker_embedding: speaker.speaker_embedding,
    gpt_cond_latent: speaker.gpt_cond_latent,
  });
  const callXtts = async () =>
    fetch(XTTS_TTS_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
    });

  try {
    upstream = await callXtts();
  } catch (e) {
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "tts-debug-1",
        hypothesisId: "H1",
        location: "app/api/tts/route.ts:POST",
        message: "XTTS fetch threw",
        data: {
          endpoint: XTTS_TTS_URL,
          error: e instanceof Error ? e.message : String(e),
          textLen: text.length,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    return NextResponse.json(
      {
        error: "XTTS unreachable",
        detail: e instanceof Error ? e.message : String(e),
        endpoint: XTTS_TTS_URL,
      },
      { status: 503 },
    );
  }

  if (!upstream.ok) {
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "tts-debug-3",
        hypothesisId: "H10",
        location: "app/api/tts/route.ts:POST",
        message: "XTTS first response non-OK; retrying once",
        data: { status: upstream.status, endpoint: XTTS_TTS_URL },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    try {
      upstream = await callXtts();
    } catch {
      // Keep first failure handling path below.
    }
  }

  if (!upstream.ok) {
    const detail = await upstream.text().catch(() => "");
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "tts-debug-1",
        hypothesisId: "H1",
        location: "app/api/tts/route.ts:POST",
        message: "XTTS non-OK response",
        data: {
          endpoint: XTTS_TTS_URL,
          status: upstream.status,
          detail: detail.slice(0, 120),
          textLen: text.length,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    return NextResponse.json(
      { error: "XTTS returned an error", status: upstream.status, detail: detail.slice(0, 2000) },
      { status: 502 },
    );
  }

  if (!upstream.body) {
    return NextResponse.json({ error: "XTTS returned empty audio body" }, { status: 502 });
  }

  const upstreamContentType = upstream.headers.get("content-type") || "";
  if (upstreamContentType.includes("application/json")) {
    const payload = await upstream.json().catch(() => null) as unknown;
    if (typeof payload !== "string") {
      return NextResponse.json(
        { error: "XTTS JSON response was not a base64 audio string" },
        { status: 502 },
      );
    }
    let audioBytes: Uint8Array;
    try {
      audioBytes = Uint8Array.from(Buffer.from(payload, "base64"));
    } catch {
      return NextResponse.json({ error: "Failed to decode XTTS base64 audio" }, { status: 502 });
    }
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "post-fix-tts-1",
        hypothesisId: "H6",
        location: "app/api/tts/route.ts:POST",
        message: "Decoded XTTS JSON base64 payload to WAV bytes",
        data: {
          upstreamContentType,
          decodedBytes: audioBytes.byteLength,
          riffMagic: String.fromCharCode(...audioBytes.slice(0, 4)),
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion

    const safeBytes = new Uint8Array(audioBytes);
    return new Response(new Blob([safeBytes], { type: "audio/wav" }), {
      status: 200,
      headers: {
        "Content-Type": "audio/wav",
        "Cache-Control": "no-store",
      },
    });
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": upstreamContentType || "audio/wav",
      "Cache-Control": "no-store",
    },
  });
}
