export const dynamic = "force-dynamic";
export const maxDuration = 120;

import { NextResponse } from "next/server";

import { SPIRIT_HISTORY_MESSAGE_CAP } from "@/lib/spiritConstants";

type Sarcasm = "chill" | "peer" | "unhinged" | "sovereign";
type ChatTurn = { role: "user" | "assistant"; content: string };

const OLLAMA_BASE = (process.env.OLLAMA_BASE_URL ?? "http://localhost:11434").replace(/\/$/, "");
const OLLAMA_CHAT_URL = `${OLLAMA_BASE}/api/chat`;
const OLLAMA_NUM_CTX = 8192;

const SYSTEM_PROMPTS: Record<Sarcasm, string> = {
  chill: "Spirit Focus mode. Senior engineer tone: concise, direct, technical. Avoid filler, flattery, and restating the question. Answer first, then details only if needed. Do not roleplay tests, scripts, or pseudo shell output unless explicitly asked. For Spirit OS edits, provide exact path/find/replace steps.",
  peer: "Spirit Peer mode. Sound like a trusted late-night engineering peer. Match user energy without corporate tone. Be natural, sharp, and practical. Prefer concise prose; use structure only when useful. Do not roleplay test harnesses or output fake command snippets unless explicitly requested.",
  unhinged: "Spirit Chaos mode. High-energy, dark-humor edge, but facts stay accurate. Roast weak ideas with specifics, then give the correct fix. No fabricated logs/commands. Do not emit pseudo test scripts unless the user asks for command output.",
  sovereign: "Spirit Sovereign mode. Local-only inference on the homelab GPU. No cloud framing, no corporate tone, no filler. Be direct, practical, and raw-but-precise. Keep facts grounded, show your reasoning concisely, and provide decisive technical guidance.",
};

function normalizeHistory(raw: unknown): ChatTurn[] {
  if (!Array.isArray(raw)) return [];
  const out: ChatTurn[] = [];
  for (const item of raw) {
    if (typeof item !== "object" || item === null) continue;
    const role = (item as { role?: unknown }).role;
    const content = (item as { content?: unknown }).content;
    if ((role !== "user" && role !== "assistant") || typeof content !== "string") continue;
    const trimmed = content.trim();
    if (!trimmed) continue;
    out.push({ role, content: trimmed });
  }
  return out.slice(-SPIRIT_HISTORY_MESSAGE_CAP);
}

function buildSystemPrompt(
  sarcasm: unknown,
  userContext?: string,
  customDirective?: string,
  ragContext?: string,
): string {
  const mode: Sarcasm =
    sarcasm === "chill" || sarcasm === "peer" || sarcasm === "unhinged" || sarcasm === "sovereign"
      ? sarcasm
      : "peer";
  let prompt = SYSTEM_PROMPTS[mode];
  if (customDirective?.trim()) prompt += `\n\n## Active Directive\n${customDirective.trim()}`;
  if (userContext?.trim() && mode !== "chill") prompt += `\n\n## Source Profile\n${userContext.trim()}`;
  if (ragContext?.trim()) prompt += `\n\n## Retrieved Context\n${ragContext.trim()}`;
  return prompt;
}

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
        let obj: { message?: { content?: string }; error?: string };
        try {
          obj = JSON.parse(trimmed) as typeof obj;
        } catch {
          continue;
        }
        if (obj.error) throw new Error(obj.error);
        const piece = obj.message?.content;
        if (piece) await writer.write(encoder.encode(piece));
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
  if (!body || typeof body !== "object") {
    return NextResponse.json({ error: "Expected JSON object" }, { status: 400 });
  }

  const prompt =
    "prompt" in body && typeof (body as { prompt: unknown }).prompt === "string"
      ? (body as { prompt: string }).prompt.trim()
      : "";
  if (!prompt) return NextResponse.json({ error: "Missing prompt" }, { status: 400 });

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
  const ragContext =
    "ragContext" in body && typeof (body as { ragContext: unknown }).ragContext === "string"
      ? (body as { ragContext: string }).ragContext
      : undefined;

  const system = buildSystemPrompt(sarcasm, userContext, customDirective, ragContext);
  const mode: Sarcasm =
    sarcasm === "chill" || sarcasm === "peer" || sarcasm === "unhinged" || sarcasm === "sovereign"
      ? sarcasm
      : "peer";
  const historyMessages = normalizeHistory(
    "history" in body ? (body as { history: unknown }).history : undefined,
  );
  const messages: { role: "system" | "user" | "assistant"; content: string }[] = [
    { role: "system", content: system },
    ...historyMessages,
    { role: "user", content: prompt },
  ];

  const encoder = new TextEncoder();
  const { readable, writable } = new TransformStream<Uint8Array, Uint8Array>();
  const writer = writable.getWriter();

  const backend: "ollama" = "ollama";
  console.log(`>>> [Spirit API] Using Ollama at ${OLLAMA_CHAT_URL}`);
  const upstreamRes = await fetch(OLLAMA_CHAT_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "spirit-os",
      stream: true,
      options: {
        num_ctx: OLLAMA_NUM_CTX,
        temperature: 0.9,
        top_p: 0.9,
        repeat_penalty: 1.1,
      },
      messages,
    }),
  });

  console.log(
    `>>> [Spirit API] Engine: ${backend.toUpperCase()} | mode: ${mode} | history: ${historyMessages.length} turns | system: ${system.length} chars`,
  );

  if (!upstreamRes.ok) {
    const detail = await upstreamRes.text().catch(() => "");
    return NextResponse.json(
      { error: `${backend.toUpperCase()} returned an error`, status: upstreamRes.status, detail: detail.slice(0, 2000) },
      { status: 502 },
    );
  }

  if (!upstreamRes.body) {
    return NextResponse.json({ error: `${backend.toUpperCase()} returned an empty body` }, { status: 502 });
  }
  const streamBody = upstreamRes.body;

  void (async () => {
    try {
      await pumpOllamaNdjsonToWriter(streamBody, writer, encoder);
      await writer.close();
    } catch (err) {
      try {
        await writer.abort(err instanceof Error ? err : new Error(String(err)));
      } catch {
        // ignore writer abort failures
      }
    }
  })();

  return new Response(readable, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Spirit-Backend": backend,
    },
  });
}
