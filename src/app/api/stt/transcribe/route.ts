import { NextResponse } from "next/server";

import { SttProviderError, transcribeSpeech } from "@/lib/server/stt-provider";

// ── /api/stt/transcribe - browser audio → Whisper (same-origin; no key exposure) ─
// > Spirit owns the response shape: { ok, provider, text, durationMs? }.
// > Headers: x-spirit-stt-provider: whisper, x-spirit-stt-duration-ms when known.
// > Dev console traces audio size + upstream status - we never log raw transcripts
// > unless SPIRIT_DEV_STT_DUMP=1 (off by default - Source has been roasted for less).
export const dynamic = "force-dynamic";
export const maxDuration = 120;

const PROVIDER_HEADER = "x-spirit-stt-provider";
const DURATION_HEADER = "x-spirit-stt-duration-ms";

function isDev(): boolean {
  return process.env.NODE_ENV !== "production";
}

function devLog(...args: unknown[]): void {
  if (!isDev()) return;
  console.log("[stt]", ...args);
}

function withProviderHeaders(
  payload: unknown,
  init: ResponseInit,
  durationMs?: number,
): NextResponse {
  const res = NextResponse.json(payload, init);
  res.headers.set(PROVIDER_HEADER, "whisper");
  if (typeof durationMs === "number") {
    res.headers.set(DURATION_HEADER, String(Math.round(durationMs)));
  }
  return res;
}

export async function POST(req: Request) {
  const ct = req.headers.get("content-type") || "";
  if (!ct.toLowerCase().includes("multipart/form-data")) {
    devLog("rejected non-multipart content-type:", ct);
    return withProviderHeaders(
      { ok: false, provider: "whisper", text: "", detail: "Expected multipart/form-data" },
      { status: 400 },
    );
  }

  let form: FormData;
  try {
    form = await req.formData();
  } catch {
    devLog("invalid form data");
    return withProviderHeaders(
      { ok: false, provider: "whisper", text: "", detail: "Invalid form data" },
      { status: 400 },
    );
  }

  const audioBlob = form.get("audio");
  if (!audioBlob) {
    devLog("missing audio field");
    return withProviderHeaders(
      { ok: false, provider: "whisper", text: "", detail: "Missing audio field" },
      { status: 400 },
    );
  }

  // size guard before we hand to upstream - Whisper hates 0-byte uploads.
  const sizeForLog =
    typeof (audioBlob as Blob).size === "number" ? (audioBlob as Blob).size : -1;
  const typeForLog =
    typeof (audioBlob as Blob).type === "string" ? (audioBlob as Blob).type : "";
  devLog(`audio received size=${sizeForLog} bytes type=${typeForLog || "unknown"}`);

  if (sizeForLog === 0) {
    devLog("rejected empty audio");
    return withProviderHeaders(
      { ok: false, provider: "whisper", text: "", detail: "Empty audio (0 bytes)" },
      { status: 400 },
    );
  }

  try {
    const result = await transcribeSpeech(form);
    const tLen = (result.text ?? "").length;
    devLog(
      `upstream ok provider=whisper transcript_len=${tLen} duration_ms=${result.durationMs ?? "n/a"}`,
    );
    if (process.env.SPIRIT_DEV_STT_DUMP === "1") {
      devLog("transcript=", result.text);
    }
    return withProviderHeaders(
      {
        ok: true,
        provider: result.provider,
        text: result.text,
        ...(typeof result.durationMs === "number" ? { durationMs: result.durationMs } : {}),
      },
      { status: 200 },
      result.durationMs,
    );
  } catch (e) {
    if (e instanceof SttProviderError) {
      devLog(`upstream error status=${e.statusCode} message=${e.message}`);
      const status = e.statusCode === 400 ? 400 : e.statusCode === 503 ? 503 : 502;
      return withProviderHeaders(
        { ok: false, provider: "whisper", text: "", detail: e.message },
        { status },
      );
    }
    const msg = e instanceof Error ? e.message : "STT failed";
    devLog("unhandled STT failure:", msg);
    return withProviderHeaders(
      { ok: false, provider: "whisper", text: "", detail: msg },
      { status: 502 },
    );
  }
}
