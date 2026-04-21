/**
 * Oracle Voice Pipeline · /api/oracle
 *
 * POST  multipart/form-data
 *   audio        Blob   — raw microphone recording (webm/opus or mp4/aac)
 *   sarcasmLevel string — "chill" | "peer" | "unhinged"
 *
 * Response  audio/wav binary (Piper)
 *   X-Transcript  URL-encoded transcription of the user's speech
 *   X-Reply       URL-encoded LLM text that was spoken back
 *
 * Pipeline:
 *   1. Faster-Whisper STT  →  transcript
 *   2. Ollama /api/generate  →  reply text
 *   3. Piper (openedai-speech) /v1/audio/speech  →  WAV audio buffer
 */

import { NextResponse } from "next/server";

// ── Service URLs ─────────────────────────────────────────────────────────────
const OLLAMA_URL = (
  process.env.OLLAMA_BASE_URL ?? process.env.OLLAMA_URL ?? "http://localhost:11434"
).replace(/\/$/, "");
const WHISPER_URL = (process.env.WHISPER_URL ?? "http://localhost:8000").replace(/\/$/, "");
const OLLAMA_MODEL = process.env.OLLAMA_MODEL ?? "dolphin-llama3:8b";
/** Voice pipeline uses a modest ctx window; chat uses a larger default elsewhere. */
const OLLAMA_NUM_CTX = (() => {
  const raw = process.env.OLLAMA_NUM_CTX?.trim();
  const n = raw ? Number(raw) : 2048;
  return Number.isFinite(n) && n > 0 ? n : 2048;
})();
const PIPER_TTS_URL = (process.env.PIPER_TTS_URL ?? "http://localhost:5200").replace(/\/$/, "");
const PIPER_TTS_VOICE = process.env.PIPER_TTS_VOICE?.trim() || "fable";
const PIPER_TTS_MODEL = "tts-1";

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
        let obj: { response?: string; error?: string };
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
        stream: true,
        options: {
          num_ctx: OLLAMA_NUM_CTX,
          num_predict: 180,
          temperature: 0.75,
        },
      }),
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

  // 4. Text-to-Speech via Piper (openedai-speech) ───────────────────────────
  let audioBuffer: ArrayBuffer;
  try {
    const ttsRes = await fetch(`${PIPER_TTS_URL}/v1/audio/speech`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: PIPER_TTS_MODEL,
        voice: PIPER_TTS_VOICE,
        input: replyText,
        response_format: "wav",
      }),
      signal: AbortSignal.timeout(60_000),
    });

    if (!ttsRes.ok) {
      const detail = await ttsRes.text().catch(() => "");
      throw new Error(`Piper TTS HTTP ${ttsRes.status}: ${detail}`);
    }

    audioBuffer = await ttsRes.arrayBuffer();
  } catch (err) {
    console.error("[oracle] TTS error:", err);
    return NextResponse.json({ error: `Speech synthesis failed: ${String(err)}` }, { status: 502 });
  }

  // 5. Return WAV + metadata headers ────────────────────────────────────────
  return new Response(audioBuffer, {
    status: 200,
    headers: {
      "Content-Type": "audio/wav",
      "X-Transcript": encodeURIComponent(transcript),
      "X-Reply":      encodeURIComponent(replyText),
      "Access-Control-Expose-Headers": "X-Transcript, X-Reply",
    },
  });
}
