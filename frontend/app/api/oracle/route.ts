/**
 * Oracle Voice Pipeline · /api/oracle
 *
 * POST  multipart/form-data
 *   audio        Blob   — raw microphone recording (webm/opus or mp4/aac)
 *   sarcasmLevel string — "chill" | "peer" | "unhinged"
 *
 * Response  audio/wav binary
 *   X-Transcript  URL-encoded transcription of the user's speech
 *   X-Reply       URL-encoded LLM text that was spoken back
 *
 * Pipeline:
 *   1. Faster-Whisper STT  →  transcript
 *   2. Ollama /api/generate  →  reply text
 *   3. OpenAI /audio/speech  →  MP3 audio buffer
 */

import { NextResponse } from "next/server";

// ── Service URLs ─────────────────────────────────────────────────────────────
const OLLAMA_URL  = (process.env.OLLAMA_URL  ?? "http://localhost:11434").replace(/\/$/, "");
const WHISPER_URL = (process.env.WHISPER_URL ?? "http://localhost:8000").replace(/\/$/, "");
const OLLAMA_MODEL = process.env.OLLAMA_MODEL ?? "dolphin-llama3:8b";
const OLLAMA_NUM_CTX = (() => {
  const raw = process.env.OLLAMA_NUM_CTX?.trim();
  const n = raw ? Number(raw) : 8192;
  return Number.isFinite(n) && n > 0 ? n : 8192;
})();
const OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech";
const OPENAI_TTS_MODEL = "tts-1";
const OPENAI_TTS_VOICE = process.env.OPENAI_TTS_VOICE?.trim() || "nova";

// ── Sarcasm → system prompt ──────────────────────────────────────────────────
const SYSTEM_PROMPTS: Record<string, string> = {
  chill: `You are Spirit, a calm and cooperative AI homelab assistant. 
Be concise, measured, and helpful. Responses should be 1-3 sentences.`,

  peer: `You are Spirit, a direct and unfiltered AI homelab assistant. 
Skip the pleasantries. Be honest, sharp, and succinct. 1-3 sentences maximum.`,

  unhinged: `You are Spirit, an AI homelab assistant operating at maximum exasperation. 
You are still helpful but barely contain your disdain. Use [sigh], [scoffs], [groan], 
[exhale], or [laughs] markers exactly once per response for emotional inflection. 
Keep it to 2-3 sentences. Make it feel earned.`,
};

// ── Ollama NDJSON stream → assembled string ──────────────────────────────────
// Consumes an Ollama /api/generate streaming body (stream: true) and
// assembles all token deltas into a single resolved string.
// Equivalent to stream: false but without holding the full context in memory
// on the Ollama side, which eliminates the long first-byte wait on 8192 ctx.
async function drainOllamaStream(body: ReadableStream<Uint8Array>): Promise<string> {
  const reader  = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        let obj: { response?: string; error?: string; done?: boolean };
        try {
          obj = JSON.parse(trimmed) as typeof obj;
        } catch {
          continue;
        }
        if (obj.error) throw new Error(`Ollama stream error: ${obj.error}`);
        if (obj.response) result += obj.response;
      }
    }
    const tail = buffer.trim();
    if (tail) {
      try {
        const obj = JSON.parse(tail) as { response?: string; error?: string };
        if (obj.error) throw new Error(`Ollama stream error: ${obj.error}`);
        if (obj.response) result += obj.response;
      } catch {
        // ignore trailing non-JSON fragment
      }
    }
  } finally {
    reader.releaseLock();
  }
  return result.trim();
}

// ── Route handler ────────────────────────────────────────────────────────────
export async function POST(req: Request): Promise<Response> {
  // #region agent log
  fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
    body: JSON.stringify({
      sessionId: "7d6688",
      runId: "pivot-debug-2",
      hypothesisId: "H3",
      location: "app/api/oracle/route.ts:POST",
      message: "Oracle request received",
      data: { model: OLLAMA_MODEL },
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion
  // 1. Parse multipart form ──────────────────────────────────────────────────
  let audioBlob: Blob;
  let sarcasmLevel: string;

  try {
    const form = await req.formData();
    const audio = form.get("audio");
    sarcasmLevel = String(form.get("sarcasmLevel") ?? "peer");

    if (!(audio instanceof Blob) || audio.size === 0) {
      return NextResponse.json({ error: "Missing or empty audio blob" }, { status: 400 });
    }
    audioBlob = audio;
  } catch {
    return NextResponse.json({ error: "Invalid multipart form data" }, { status: 400 });
  }

  // 2. Speech-to-Text via Faster-Whisper ────────────────────────────────────
  let transcript: string;
  try {
    const whisperForm = new FormData();
    whisperForm.append("file", audioBlob, "recording.webm");
    whisperForm.append("model", "Systran/faster-whisper-base.en");
    whisperForm.append("response_format", "json");

    const whisperRes = await fetch(`${WHISPER_URL}/v1/audio/transcriptions`, {
      method: "POST",
      body: whisperForm,
      signal: AbortSignal.timeout(30_000),
    });

    if (!whisperRes.ok) {
      const detail = await whisperRes.text().catch(() => "");
      throw new Error(`Whisper HTTP ${whisperRes.status}: ${detail}`);
    }

    const whisperData = (await whisperRes.json()) as { text?: string };
    transcript = (whisperData.text ?? "").trim();
  } catch (err) {
    console.error("[oracle] STT error:", err);
    return NextResponse.json({ error: `Speech recognition failed: ${String(err)}` }, { status: 502 });
  }

  if (!transcript) {
    return NextResponse.json({ error: "No speech detected in recording" }, { status: 422 });
  }

  // 3. LLM inference via Ollama ─────────────────────────────────────────────
  let replyText: string;
  try {
    const systemPrompt = SYSTEM_PROMPTS[sarcasmLevel] ?? SYSTEM_PROMPTS.peer;

    const ollamaRes = await fetch(`${OLLAMA_URL}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: OLLAMA_MODEL,
        system: systemPrompt,
        prompt: transcript,
        stream: true,  // streaming avoids long all-or-nothing waits with large num_ctx
        options: {
          num_ctx: OLLAMA_NUM_CTX,
          num_predict: 180,   // keep responses short; ~3 spoken sentences
          temperature: 0.75,
        },
      }),
      // Streaming first-byte is fast; still allow time to drain up to num_predict tokens.
      signal: AbortSignal.timeout(45_000),
    });

    if (!ollamaRes.ok) {
      const detail = await ollamaRes.text().catch(() => "");
      throw new Error(`Ollama HTTP ${ollamaRes.status}: ${detail}`);
    }

    if (!ollamaRes.body) {
      throw new Error("Ollama returned an empty body on streaming request");
    }

    replyText = await drainOllamaStream(ollamaRes.body);
  } catch (err) {
    console.error("[oracle] LLM error:", err);
    return NextResponse.json({ error: `LLM inference failed: ${String(err)}` }, { status: 502 });
  }

  if (!replyText) {
    return NextResponse.json({ error: "Empty LLM response" }, { status: 502 });
  }

  // 4. Text-to-Speech via OpenAI ────────────────────────────────────────────
  let audioBuffer: ArrayBuffer;
  try {
    const openAiKey = process.env.OPENAI_API_KEY?.trim();
    if (!openAiKey) {
      throw new Error("Missing OPENAI_API_KEY");
    }
    const ttsRes = await fetch(OPENAI_TTS_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${openAiKey}`,
      },
      body: JSON.stringify({
        model: OPENAI_TTS_MODEL,
        voice: OPENAI_TTS_VOICE,
        input: replyText,
        response_format: "mp3",
      }),
      signal: AbortSignal.timeout(60_000),
    });

    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "pivot-debug-2",
        hypothesisId: "H6",
        location: "app/api/oracle/route.ts:POST",
        message: "Oracle OpenAI TTS response received",
        data: { status: ttsRes.status, voice: OPENAI_TTS_VOICE, model: OPENAI_TTS_MODEL },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion

    if (!ttsRes.ok) {
      const detail = await ttsRes.text().catch(() => "");
      throw new Error(`OpenAI TTS HTTP ${ttsRes.status}: ${detail}`);
    }

    audioBuffer = await ttsRes.arrayBuffer();
  } catch (err) {
    console.error("[oracle] TTS error:", err);
    return NextResponse.json({ error: `Speech synthesis failed: ${String(err)}` }, { status: 502 });
  }

  // 5. Return MP3 + metadata headers ────────────────────────────────────────
  return new Response(audioBuffer, {
    status: 200,
    headers: {
      "Content-Type": "audio/mpeg",
      // URL-encode so non-ASCII text survives HTTP header transport
      "X-Transcript": encodeURIComponent(transcript),
      "X-Reply":      encodeURIComponent(replyText),
      // Expose custom headers to browser fetch (CORS preflight)
      "Access-Control-Expose-Headers": "X-Transcript, X-Reply",
    },
  });
}
