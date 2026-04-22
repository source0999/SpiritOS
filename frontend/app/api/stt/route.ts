import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 120;

const GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions";
const GROQ_STT_MODEL = "whisper-large-v3";

export async function POST(req: Request) {
  const apiKey = process.env.GROQ_API_KEY?.trim();
  if (!apiKey) {
    return NextResponse.json({ error: "Missing GROQ_API_KEY" }, { status: 503 });
  }

  let incoming: FormData;
  try {
    incoming = await req.formData();
  } catch {
    return NextResponse.json({ error: "Expected multipart/form-data" }, { status: 400 });
  }

  const file = incoming.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json({ error: "Missing audio file" }, { status: 400 });
  }

  const fd = new FormData();
  fd.append("file", file, file.name || "speech.webm");
  fd.append("model", GROQ_STT_MODEL);

  let upstream: Response;
  try {
    upstream = await fetch(GROQ_STT_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      body: fd,
    });
  } catch (e) {
    return NextResponse.json(
      { error: "Groq STT unreachable", detail: e instanceof Error ? e.message : String(e) },
      { status: 503 },
    );
  }

  if (!upstream.ok) {
    const detail = await upstream.text().catch(() => "");
    return NextResponse.json(
      { error: "Groq STT returned an error", status: upstream.status, detail: detail.slice(0, 2000) },
      { status: 502 },
    );
  }

  const payload = await upstream.json().catch(() => null) as { text?: string } | null;
  const text = payload?.text?.trim() || "";
  return NextResponse.json({ text });
}
