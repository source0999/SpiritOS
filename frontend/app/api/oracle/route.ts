/**
 * Oracle Voice Pipeline · /api/oracle
 *
 * POST  multipart/form-data
 *   audio        Blob   — raw microphone recording (webm/opus or mp4/aac)
 *   sarcasmLevel string — "chill" | "peer" | "unhinged"
 *
 * Response  text/event-stream (SSE)
 *   data: {"transcript":"..."}  — user speech (first event)
 *   data: {"text":"..."}       — LLM token chunks
 *   data: [DONE]
 *
 * Pipeline:
 *   1. Faster-Whisper STT  →  transcript (must finish before LLM)
 *   2. Ollama /api/generate (stream)  →  SSE token stream (client TTS via /api/tts)
 */

export const dynamic = "force-dynamic";
export const maxDuration = 120;

// ── Service URLs ─────────────────────────────────────────────────────────────
const OLLAMA_URL = (
  process.env.OLLAMA_BASE_URL ?? process.env.OLLAMA_URL ?? "http://localhost:11434"
).replace(/\/$/, "");
const WHISPER_URL = (process.env.WHISPER_URL ?? "http://localhost:8000").replace(/\/$/, "");
/** Voice pipeline uses a modest ctx window; chat uses a larger default elsewhere. */
const OLLAMA_NUM_CTX = (() => {
  const raw = process.env.OLLAMA_NUM_CTX?.trim();
  const n = raw ? Number(raw) : 2048;
  return Number.isFinite(n) && n > 0 ? n : 2048;
})();

// ── Sarcasm → system prompt (injected as Ollama `system` alongside transcript) ─
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
      return new Response(JSON.stringify({ error: "Missing or empty audio blob" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }
    audioBlob = audio;
  } catch {
    return new Response(JSON.stringify({ error: "Invalid multipart form data" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
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
    return new Response(JSON.stringify({ error: `Speech recognition failed: ${String(err)}` }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }

  if (!transcript) {
    return new Response(JSON.stringify({ error: "No speech detected in recording" }), {
      status: 422,
      headers: { "Content-Type": "application/json" },
    });
  }

  // 3. LLM inference via Ollama (stream → SSE) ───────────────────────────────
  const systemPrompt = SYSTEM_PROMPTS[sarcasmLevel] ?? SYSTEM_PROMPTS.peer;

  let ollamaResponse: Response;
  try {
    ollamaResponse = await fetch(`${OLLAMA_URL}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "spirit-os",
        system: systemPrompt,
        prompt: transcript,
        stream: true,
        options: {
          num_ctx: OLLAMA_NUM_CTX,
          num_predict: 180,
          temperature: 0.75,
        },
      }),
      signal: AbortSignal.timeout(120_000),
    });
  } catch (err) {
    console.error("[oracle] LLM error:", err);
    return new Response(JSON.stringify({ error: `LLM inference failed: ${String(err)}` }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }

  if (!ollamaResponse.ok) {
    const detail = await ollamaResponse.text().catch(() => "");
    return new Response(
      JSON.stringify({ error: `Ollama HTTP ${ollamaResponse.status}`, detail: detail.slice(0, 2000) }),
      { status: 502, headers: { "Content-Type": "application/json" } },
    );
  }

  if (!ollamaResponse.body) {
    return new Response(JSON.stringify({ error: "Ollama returned an empty body on streaming request" }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }

  const upstreamBody = ollamaResponse.body;

  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();
      let sentDone = false;
      const markDone = () => {
        if (sentDone) return;
        sentDone = true;
        try {
          controller.enqueue(encoder.encode("data: [DONE]\n\n"));
        } catch {
          // ignore
        }
      };

      try {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ transcript })}\n\n`));
      } catch {
        return;
      }

      const reader = upstreamBody.getReader();
      const decoder = new TextDecoder();
      let ndjsonBuffer = "";
      let streamFatal = false;
      try {
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          ndjsonBuffer += decoder.decode(value, { stream: true });
          const lines = ndjsonBuffer.split("\n");
          ndjsonBuffer = lines.pop() ?? "";
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;
            try {
              const json = JSON.parse(trimmed) as { response?: string; done?: boolean; error?: string };
              if (json.error) {
                controller.enqueue(
                  encoder.encode(`data: ${JSON.stringify({ error: json.error })}\n\n`),
                );
                markDone();
                streamFatal = true;
                break;
              }
              const text = json.response ?? "";
              if (text) {
                controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text })}\n\n`));
              }
              if (json.done) {
                markDone();
              }
            } catch {
              // ignore malformed NDJSON line fragments
            }
          }
          if (streamFatal) break;
        }
        const tail = ndjsonBuffer.trim();
        if (tail) {
          try {
            const json = JSON.parse(tail) as { response?: string; done?: boolean; error?: string };
            if (json.error) {
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({ error: json.error })}\n\n`));
            } else {
              const text = json.response ?? "";
              if (text) {
                controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text })}\n\n`));
              }
              if (json.done) {
                markDone();
              }
            }
          } catch {
            // ignore trailing fragment
          }
        }
        markDone();
      } finally {
        try {
          reader.releaseLock();
        } catch {
          // ignore
        }
        try {
          controller.close();
        } catch {
          // ignore
        }
      }
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}
