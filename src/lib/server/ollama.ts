import "server-only";

import { createOpenAI } from "@ai-sdk/openai";

import { getSpiritChatModelId } from "@/lib/server/model-routing";

// ── Ollama OpenAI-compat client - server-only; env-derived base URL ───────────

export function getOllamaOpenAIBaseURL(): string {
  const explicit = process.env.OLLAMA_OPENAI_BASE_URL?.trim();
  if (explicit) return explicit.replace(/\/$/, "");

  const raw = (
    process.env.OLLAMA_BASE_URL?.trim() || "http://localhost:11434"
  ).replace(/\/api\/?$/i, "");

  return `${raw.replace(/\/$/, "")}/v1`;
}

/** Primary `/chat` lane model tag (OLLAMA_MODEL). */
export function getSpiritModelId(): string {
  return getSpiritChatModelId();
}

export const ollamaOpenAI = createOpenAI({
  baseURL: getOllamaOpenAIBaseURL(),
  apiKey: process.env.OLLAMA_API_KEY || "ollama",
});

const HEALTH_PROBE_TIMEOUT_MS = 2500;
const TOOL_SCHEMA_PROBE_TIMEOUT_MS = 4000;

/** GET /v1/models - same auth shape as createOpenAI; no prompts logged. */
export type OllamaProbeResult =
  | { ok: true; status: "online" }
  | { ok: false; status: "offline"; error: string };

export async function probeOllamaOpenAICompat(): Promise<OllamaProbeResult> {
  const url = `${getOllamaOpenAIBaseURL()}/models`;
  const apiKey = process.env.OLLAMA_API_KEY || "ollama";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), HEALTH_PROBE_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
    });
    if (!res.ok) {
      return {
        ok: false,
        status: "offline",
        error: `Health check failed: ${res.status}`,
      };
    }
    return { ok: true, status: "online" };
  } catch {
    return {
      ok: false,
      status: "offline",
      error: "Ollama is unreachable",
    };
  } finally {
    clearTimeout(timeout);
  }
}

/**
 * POST /v1/chat/completions with a minimal tools payload to see if this model
 * accepts OpenAI-style tools. Hermes4 and similar return 400 "does not support tools".
 * Cached per process in tool-registry; callers should not spam this.
 */
export async function probeOllamaChatCompletionsAcceptsToolSchema(modelId: string): Promise<boolean> {
  const url = `${getOllamaOpenAIBaseURL()}/chat/completions`;
  const apiKey = process.env.OLLAMA_API_KEY || "ollama";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TOOL_SCHEMA_PROBE_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: "POST",
      cache: "no-store",
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: modelId,
        stream: false,
        max_tokens: 1,
        messages: [{ role: "user", content: "." }],
        tools: [
          {
            type: "function",
            function: {
              name: "__spirit_tool_schema_probe",
              description: "Spirit internal probe; not for production use.",
              parameters: { type: "object", properties: {} },
            },
          },
        ],
        tool_choice: "auto",
      }),
    });

    const raw = await res.text();
    const lower = raw.toLowerCase();
    if (!res.ok) {
      if (res.status === 400 && lower.includes("does not support tools")) {
        return false;
      }
      return true;
    }
    if (lower.includes("does not support tools")) {
      return false;
    }
    return true;
  } catch {
    return true;
  } finally {
    clearTimeout(timeout);
  }
}
