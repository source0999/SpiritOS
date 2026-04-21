import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 120;

const PIPER_TTS_URL = (process.env.PIPER_TTS_URL ?? "http://localhost:5200").replace(/\/$/, "");
const PIPER_TTS_VOICE = process.env.PIPER_TTS_VOICE?.trim() || "fable";
const TTS_MODEL = "tts-1";
/** Piper via openedai-speech: wav decodes reliably in the browser AudioContext. */
const RESPONSE_FORMAT = "wav";
const MAX_CHARS = 500;

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
  try {
    upstream = await fetch(`${PIPER_TTS_URL}/v1/audio/speech`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: TTS_MODEL,
        voice: PIPER_TTS_VOICE,
        input: text,
        response_format: RESPONSE_FORMAT,
        language,
      }),
    });
  } catch (e) {
    return NextResponse.json(
      {
        error: "Piper TTS unreachable",
        detail: e instanceof Error ? e.message : String(e),
        endpoint: `${PIPER_TTS_URL}/v1/audio/speech`,
      },
      { status: 503 },
    );
  }

  if (!upstream.ok) {
    const detail = await upstream.text().catch(() => "");
    return NextResponse.json(
      { error: "Piper TTS returned an error", status: upstream.status, detail: detail.slice(0, 2000) },
      { status: upstream.status >= 500 ? 502 : upstream.status },
    );
  }

  if (!upstream.body) {
    return NextResponse.json({ error: "Piper TTS returned empty audio body" }, { status: 502 });
  }

  const upstreamContentType = upstream.headers.get("content-type") || "";
  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": upstreamContentType || "audio/wav",
      "Cache-Control": "no-store",
    },
  });
}
