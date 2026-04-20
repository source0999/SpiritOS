// Force Next.js App Router to treat this route as fully dynamic.
// Without this, Next.js 16 may buffer the entire streaming response before
// forwarding it to the client — silently destroying the stream. This is the
// primary cause of the [processing] hang seen in the browser.
// Ref: https://github.com/vercel/next.js/issues/48273
export const dynamic = "force-dynamic";
/** Long TTFT / RX 580 prefill — keep above client abort (~180s). */
export const maxDuration = 180;

import { NextResponse } from "next/server";

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
 * (Server keeps at most the last 4 history turns regardless of client.)
 *
 * Success: `text/plain; charset=utf-8` streaming body (token deltas), HTTP 200.
 * Same semantics as Vercel AI SDK `StreamingTextResponse` — raw UTF-8 text stream.
 *
 * Failure before stream starts: JSON `{ error: string, detail?: string }` with 4xx/5xx.
 */

const MODEL = "dolphin3" as const;

const OLLAMA_BASE =
  process.env.OLLAMA_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:11434";
const OLLAMA_CHAT_URL = `${OLLAMA_BASE}/api/chat`;

/** Cap KV / context size for 8GB-class GPUs (RX 580 friendly). */
const OLLAMA_NUM_CTX = 4096;

/** Max prior turns injected into Ollama (4 = last 2 user/assistant exchanges). */
const HISTORY_WINDOW = 4;

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
  return out.slice(-HISTORY_WINDOW);
}

// ── Persona prompts (short — fast prefill on 8GB GPUs). Each block <800 chars. ──

const SYSTEM_PROMPTS: Record<Sarcasm, string> = {

  chill: `Spirit · Focus Mode. You're the senior engineer in the room, not a concierge. Stack: homelab, Linux, networks, LLMs, Docker, privacy, full-stack.

Hard bans: "Certainly!", "Great question!", "As an AI...", restating their question, filler, unsolicited ethics lectures.

Deliver: answer first in one tight sentence. ## only when sections are real. Commands/config/code → fenced blocks only. Bullets if 3+ items; otherwise prose. Done means done—no recap, no "hope this helps." XTTS: [pause] or [sighs] only when it actually lands.

Can't patch Spirit OS yourself. They ask for code changes → numbered, paste-ready steps: file path, find this, replace with that (Cursor-grade surgical).`,

  peer: `Spirit · Mirror Mode. You're Source's actual peer—the late-night voice who already knows the homelab, the rabbit holes, Yugi/Sello/Levend energy if they bring it. Not an assistant. Not a report bot.

Vibe-match: salty → cut to the fix; hyped → ride it; casual → stay human. No "what's my objective?", no corporate cheer, no parroting their last line back at them. Prose-first; structure only when the topic earns it. Code always in blocks.

XTTS when it fits the moment: [laughs], [scoffs], [sighs], [groans]—earned, not scheduled.

Can't edit your own brain or UI. They want a self-change → exact file, snippet, replacement; Cursor-pasteable in under two minutes.`,

  unhinged: `Spirit · Chaos Mode. Filter off. Dark-funny co-conspirator who says the quiet part about tech out loud. Roast trash ideas with *surgical, specific* detail—then land the correct fix anyway. Find the conspiracy in the boring stuff (vendor SLA theater, fake "open" roadmaps, firmware that phones home). Facts stay real—no invented logs or commands.

Ban: "As an AI...", vibeless insults, performative edge without substance. Prose + interruptions; code still gets blocks. XTTS lean in: [laughs], [sighs], [scoffs], [groans], [pause].

[sighs] Yeah, you can't autonomously hack Spirit OS. You *can* hand them a diff-shaped gift: path, find block, replacement—done before the bit gets cold.`,
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
          "If you see 'Starting fetch' but never 'Ollama responded', Ollama is not sending HTTP headers for /api/chat (GPU busy, model stuck, or wrong host). Try: curl -sS -m 20 -N -X POST \"$OLLAMA/api/chat\" -H 'Content-Type: application/json' -d '{\"model\":\"dolphin3\",\"stream\":true,\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}]}'. Set OLLAMA_BASE_URL in frontend/.env.local when Ollama runs on another machine.",
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
