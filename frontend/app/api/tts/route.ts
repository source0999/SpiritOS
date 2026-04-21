import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 120;

const OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech";
const OPENAI_TTS_MODEL = "tts-1";
const OPENAI_TTS_VOICE = process.env.OPENAI_TTS_VOICE?.trim() || "nova";
const OPENAI_TTS_FORMAT = "mp3";
const MAX_CHARS = 500;

export async function POST(req: Request) {
  const apiKey = process.env.OPENAI_API_KEY?.trim();
  if (!apiKey) {
    return NextResponse.json({ error: "Missing OPENAI_API_KEY" }, { status: 503 });
  }

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
  try {
    upstream = await fetch(OPENAI_TTS_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: OPENAI_TTS_MODEL,
        voice: OPENAI_TTS_VOICE,
        input: text,
        response_format: OPENAI_TTS_FORMAT,
        // Keep language in request path for compatibility if upstream adds support later.
        language,
      }),
    });
  } catch (e) {
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "openai-tts-1",
        hypothesisId: "C1",
        location: "app/api/tts/route.ts:POST",
        message: "OpenAI TTS fetch threw",
        data: {
          endpoint: OPENAI_TTS_URL,
          error: e instanceof Error ? e.message : String(e),
          textLen: text.length,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    return NextResponse.json(
      {
        error: "OpenAI TTS unreachable",
        detail: e instanceof Error ? e.message : String(e),
        endpoint: OPENAI_TTS_URL,
      },
      { status: 503 },
    );
  }

  if (!upstream.ok) {
    const detail = await upstream.text().catch(() => "");
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "openai-tts-1",
        hypothesisId: "C1",
        location: "app/api/tts/route.ts:POST",
        message: "OpenAI TTS non-OK response",
        data: {
          endpoint: OPENAI_TTS_URL,
          status: upstream.status,
          detail: detail.slice(0, 120),
          textLen: text.length,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    return NextResponse.json(
      { error: "OpenAI TTS returned an error", status: upstream.status, detail: detail.slice(0, 2000) },
      { status: upstream.status >= 500 ? 502 : upstream.status },
    );
  }

  if (!upstream.body) {
    return NextResponse.json({ error: "OpenAI TTS returned empty audio body" }, { status: 502 });
  }

  // #region agent log
  fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
    body: JSON.stringify({
      sessionId: "7d6688",
      runId: "openai-tts-1",
      hypothesisId: "C2",
      location: "app/api/tts/route.ts:POST",
      message: "OpenAI stream connected",
      data: {
        endpoint: OPENAI_TTS_URL,
        model: OPENAI_TTS_MODEL,
        voice: OPENAI_TTS_VOICE,
        upstreamContentType: upstream.headers.get("content-type") ?? "",
      },
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion

  const upstreamContentType = upstream.headers.get("content-type") || "";
  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": upstreamContentType || "audio/mpeg",
      "Cache-Control": "no-store",
    },
  });
}
