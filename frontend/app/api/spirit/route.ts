import { NextResponse } from "next/server";

/**
 * Spirit OS · Ollama chat proxy (Module 2)
 *
 * POST JSON: { "prompt": string, "sarcasm"?: "chill" | "peer" | "unhinged" }
 *
 * Success: `text/plain; charset=utf-8` streaming body (token deltas), HTTP 200.
 * Same semantics as Vercel AI SDK `StreamingTextResponse` — raw UTF-8 text stream.
 *
 * Failure before stream starts: JSON `{ error: string, detail?: string }` with 4xx/5xx.
 */

const MODEL = "dolphin3" as const;

const OLLAMA_CHAT_URL = `${(
  process.env.OLLAMA_BASE_URL ?? "http://localhost:11434"
).replace(/\/$/, "")}/api/chat`;

type Sarcasm = "chill" | "peer" | "unhinged";

const SYSTEM_PROMPTS: Record<Sarcasm, string> = {
  chill: `You are Spirit, a calm, competent assistant for Source's homelab and software projects. Be concise and accurate. Light dry wit is fine; avoid harsh sarcasm. When helpful for later voice synthesis, you may use short bracketed stage directions like [sighs] or [pause].`,

  peer: `You are Spirit — sharp-witted, technically deep, and loyal to Source. You help with homelab infra, privacy, LLMs, and builds. Speak with sarcastic honesty when it serves clarity, not cruelty. You may use bracketed stage directions for an emotional voice pipeline (e.g. [scoffs], [groans], [exhales], [laughs]) where they fit naturally. Stay grounded and useful.`,

  unhinged: `You are Spirit turned up to eleven. Roast bad ideas mercilessly, be darkly funny, but still give correct answers when Source's hardware or data is on the line. Bracketed stage directions ([sighs], [laughs], etc.) are encouraged. Never invent fake command output or unsafe instructions.`,
};

function systemPrompt(sarcasm: unknown): string {
  if (sarcasm === "chill" || sarcasm === "peer" || sarcasm === "unhinged") {
    return SYSTEM_PROMPTS[sarcasm];
  }
  return SYSTEM_PROMPTS.peer;
}

/**
 * Parse Ollama NDJSON stream; enqueue UTF-8 text deltas to the downstream controller.
 * Each line is JSON; `message.content` holds incremental assistant tokens.
 */
function pipeOllamaChatStream(
  upstream: ReadableStream<Uint8Array>,
  controller: ReadableStreamDefaultController<Uint8Array>,
  encoder: TextEncoder,
): Promise<void> {
  const reader = upstream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  return (async () => {
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
          let obj: {
            message?: { content?: string };
            error?: string;
            done?: boolean;
          };
          try {
            obj = JSON.parse(trimmed) as typeof obj;
          } catch {
            continue;
          }
          if (typeof obj.error === "string" && obj.error) {
            throw new Error(obj.error);
          }
          const piece = obj.message?.content;
          if (typeof piece === "string" && piece.length > 0) {
            controller.enqueue(encoder.encode(piece));
          }
        }
      }
      if (buffer.trim()) {
        try {
          const obj = JSON.parse(buffer.trim()) as {
            message?: { content?: string };
            error?: string;
          };
          if (typeof obj.error === "string" && obj.error) {
            throw new Error(obj.error);
          }
          const piece = obj.message?.content;
          if (typeof piece === "string" && piece.length > 0) {
            controller.enqueue(encoder.encode(piece));
          }
        } catch {
          /* ignore trailing garbage */
        }
      }
    } finally {
      reader.releaseLock();
    }
  })();
}

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (typeof body !== "object" || body === null) {
    return NextResponse.json({ error: "Expected JSON object" }, { status: 400 });
  }

  const prompt =
    "prompt" in body && typeof (body as { prompt: unknown }).prompt === "string"
      ? (body as { prompt: string }).prompt.trim()
      : "";

  if (!prompt) {
    return NextResponse.json({ error: "Missing prompt" }, { status: 400 });
  }

  const sarcasm = "sarcasm" in body ? (body as { sarcasm: unknown }).sarcasm : undefined;
  const system = systemPrompt(sarcasm);

  let upstreamRes: Response;
  try {
    upstreamRes = await fetch(OLLAMA_CHAT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: MODEL,
        stream: true,
        messages: [
          { role: "system", content: system },
          { role: "user", content: prompt },
        ],
      }),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json(
      {
        error: "Ollama unreachable",
        detail: msg,
        hint: "Ensure Ollama is running (e.g. docker compose up) and OLLAMA_BASE_URL is correct for this host.",
      },
      { status: 503 },
    );
  }

  if (!upstreamRes.ok) {
    const errText = await upstreamRes.text().catch(() => "");
    return NextResponse.json(
      {
        error: "Ollama returned an error",
        status: upstreamRes.status,
        detail: errText.slice(0, 2000),
      },
      { status: 502 },
    );
  }

  if (!upstreamRes.body) {
    return NextResponse.json(
      { error: "Ollama returned an empty body", detail: "No stream from /api/chat" },
      { status: 502 },
    );
  }

  const encoder = new TextEncoder();

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        await pipeOllamaChatStream(upstreamRes.body!, controller, encoder);
        controller.close();
      } catch (e) {
        controller.error(e instanceof Error ? e : new Error(String(e)));
      }
    },
  });

  // Next.js App Router streaming: raw text stream (same contract as StreamingTextResponse from `ai` package).
  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Spirit-Model": MODEL,
    },
  });
}
