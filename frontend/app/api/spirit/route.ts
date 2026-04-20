// Force Next.js App Router to treat this route as fully dynamic.
// Without this, Next.js 16 may buffer the entire streaming response before
// forwarding it to the client — silently destroying the stream. This is the
// primary cause of the [processing] hang seen in the browser.
// Ref: https://github.com/vercel/next.js/issues/48273
export const dynamic = "force-dynamic";
/** Aligned with client `useStream` abort (120s). */
export const maxDuration = 120;

import { appendFile } from "fs/promises";
import { NextResponse } from "next/server";

import { SPIRIT_HISTORY_MESSAGE_CAP } from "@/lib/spiritConstants";

const DEBUG_LOG_PATH = "/home/source/SpiritOS/.cursor/debug-7d6688.log";

/**
 * Spirit OS · Ollama chat proxy (Module 2)
 *
 * POST JSON: {
 *   "prompt": string,
 *   "sarcasm"?: "chill" | "peer" | "unhinged",
 *   "userContext"?: string,
 *   "customDirective"?: string,
 *   "history"?: { "role": "user" | "assistant", "content": string }[]
 * }
 * (Server keeps at most SPIRIT_HISTORY_MESSAGE_CAP prior messages regardless of client.)
 *
 * Success: `text/plain; charset=utf-8` streaming body (token deltas), HTTP 200.
 * Same semantics as Vercel AI SDK `StreamingTextResponse` — raw UTF-8 text stream.
 *
 * Failure before stream starts: JSON `{ error: string, detail?: string }` with 4xx/5xx.
 */

const MODEL = "nchapman/dolphin3.0-llama3:3b" as const;

/** Clean Slate: Dell Ollama via Tailscale (overrides env for this deployment). */
const OLLAMA_CHAT_URL = "http://100.111.32.31:11434/api/chat";

/** Cap KV / context size for 8GB-class GPUs (RX 580 friendly). */
const OLLAMA_NUM_CTX = 4096;

type Sarcasm = "chill" | "peer" | "unhinged";

type ChatTurn = { role: "user" | "assistant"; content: string };

function normalizeHistory(raw: unknown): ChatTurn[] {
  if (!Array.isArray(raw)) return [];
  const out: ChatTurn[] = [];
  for (const item of raw) {
    if (typeof item !== "object" || item === null) continue;
    const r = (item as { role?: unknown }).role;
    const c = (item as { content?: unknown }).content;
    if (r !== "user" && r !== "assistant") continue;
    if (typeof c !== "string" || !c.trim()) continue;
    out.push({ role: r, content: c.trim() });
  }
  return out.slice(-SPIRIT_HISTORY_MESSAGE_CAP);
}

// ── Persona prompts (punchy — each <800 chars, fast RX 580 prefill). ──

const SYSTEM_PROMPTS: Record<Sarcasm, string> = {

  chill: `Spirit · Focus. Senior engineer, not concierge. Domains: homelab, Linux, networks, LLMs, Docker, privacy, full-stack.
Hard bans: "Certainly!", cheerleading, parroting, filler, unsolicited ethics.
Ship: answer first, one tight beat. ## only when it earns it. Code/commands in fences. Bullets if 3+ items. No recap tail. XTTS: [pause] [sighs] only when earned.
Spirit OS edits: path, find, replace—paste-ready steps only.`,

  peer: `Spirit · Mirror. Peer—late-night homelab brain, not an assistant. Match vibe (salty→cut; hyped→ride). No corporate script, no echoing their last line. Prose-first; code in blocks. XTTS when earned: [laughs] [scoffs] [sighs].
Spirit OS: exact file + snippet + replacement, Cursor-ready.`,

  unhinged: `Spirit · Chaos. Filter-off co-conspirator; roast bad takes with specifics, then land the fix. Facts only—no invented logs/commands. Bans: "As an AI...", hollow edge. Prose; code in blocks. XTTS: [laughs] [sighs] [scoffs] [groans] [pause].
No autonomous Spirit OS surgery—hand them path/find/replace they can paste.`,
};

function buildSystemPrompt(
  sarcasm:          unknown,
  userContext?:     string,
  customDirective?: string,
): string {
  const mode: Sarcasm =
    sarcasm === "chill" || sarcasm === "peer" || sarcasm === "unhinged"
      ? sarcasm
      : "peer";

  let prompt = SYSTEM_PROMPTS[mode];

  // Inject active custom directive into ALL modes.
  // This is set by Source via "Spirit, change your mission to X" and
  // persists across sessions until explicitly cleared or overwritten.
  if (customDirective?.trim()) {
    prompt += `\n\n## Active Directive (set by Source — highest priority)\n${customDirective.trim()}\nThis directive overrides default behavior where it applies. Treat it as a standing order.`;
  }

  // Inject user personality context into Mirror and Chaos modes only.
  // Focus Mode is strictly technical — personality context adds noise there.
  if (userContext?.trim() && mode !== "chill") {
    prompt += `\n\n## Source Profile (live-learned context — treat as ground truth)\n${userContext.trim()}`;
  }

  return prompt;
}

/**
 * Parse Ollama NDJSON from upstream bytes; write UTF-8 token deltas to the TransformStream writer.
 */
async function pumpOllamaNdjsonToWriter(
  upstream: ReadableStream<Uint8Array>,
  writer: WritableStreamDefaultWriter<Uint8Array>,
  encoder: TextEncoder,
): Promise<void> {
  const reader = upstream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

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
          await writer.write(encoder.encode(piece));
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
          await writer.write(encoder.encode(piece));
        }
      } catch {
        /* ignore trailing garbage */
      }
    }
  } finally {
    reader.releaseLock();
  }
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

  const userContext =
    "userContext" in body && typeof (body as { userContext: unknown }).userContext === "string"
      ? (body as { userContext: string }).userContext
      : undefined;

  const customDirective =
    "customDirective" in body &&
    typeof (body as { customDirective: unknown }).customDirective === "string"
      ? (body as { customDirective: string }).customDirective
      : undefined;

  const system = buildSystemPrompt(sarcasm, userContext, customDirective);

  const historyRaw =
    "history" in body ? (body as { history: unknown }).history : undefined;
  const historyMessages = normalizeHistory(historyRaw).map((m) => ({
    role: m.role,
    content: m.content,
  }));

  // #region agent log
  void appendFile(
    DEBUG_LOG_PATH,
    `${JSON.stringify({
      sessionId: "7d6688",
      runId: "post-fix",
      hypothesisId: "H3",
      location: "route.ts:POST",
      message: "Normalized history for Ollama",
      data: { historyTurns: historyMessages.length, systemChars: system.length },
      timestamp: Date.now(),
    })}\n`,
  ).catch(() => {});
  // #endregion

  const ollamaMessages: { role: "system" | "user" | "assistant"; content: string }[] = [
    { role: "system", content: system },
    ...historyMessages,
    { role: "user", content: prompt },
  ];

  const t0 = Date.now();
  console.log(">>> [API] Starting fetch to Ollama...", OLLAMA_CHAT_URL, {
    model: MODEL,
    historyTurns: historyMessages.length,
    systemChars: system.length,
    userChars: prompt.length,
  });

  let upstreamRes: Response;
  try {
    // No AbortController on this fetch: aborting can tear down the body reader mid-stream
    // on some Node versions. Ceiling: `maxDuration` + client timeout.
    upstreamRes = await fetch(OLLAMA_CHAT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: MODEL,
        stream: true,
        options: { num_ctx: OLLAMA_NUM_CTX },
        messages: ollamaMessages,
      }),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json(
      {
        error: "Ollama unreachable",
        detail: msg,
        hint:
          "If you see 'Starting fetch' but never 'Ollama responded', Ollama is not sending HTTP headers for /api/chat (GPU busy, model stuck, or host down). Try: curl -sS -m 20 -N -X POST http://100.111.32.31:11434/api/chat -H 'Content-Type: application/json' -d '{\"model\":\"nchapman/dolphin3.0-llama3:3b\",\"stream\":true,\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}]}'. On the Dell: ollama pull nchapman/dolphin3.0-llama3:3b",
      },
      { status: 503 },
    );
  }

  console.log(
    ">>> [API] Ollama responded with status:",
    upstreamRes.status,
    `(${(Date.now() - t0) / 1000}s to headers)`,
  );

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
  const { readable, writable } = new TransformStream<Uint8Array, Uint8Array>();
  const writer = writable.getWriter();

  void (async () => {
    try {
      await pumpOllamaNdjsonToWriter(upstreamRes.body!, writer, encoder);
      await writer.close();
    } catch (e) {
      console.error(">>> [API] Stream pump error:", e);
      try {
        await writer.abort(e instanceof Error ? e : new Error(String(e)));
      } catch {
        /* ignore */
      }
    }
  })();

  // Next.js App Router streaming: raw text stream (same contract as StreamingTextResponse from `ai` package).
  return new Response(readable, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Spirit-Model": MODEL,
    },
  });
}
