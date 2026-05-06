// ── ollama-tool-unsupported-error - detect Ollama "no tools" 400 for safe retry ──

import { APICallError } from "ai";

/** True when Ollama OpenAI-compat rejected the request because the model does not support tools. */
export function isOllamaModelToolUnsupportedError(error: unknown): boolean {
  if (!APICallError.isInstance(error)) return false;
  const msg = String(error.message).toLowerCase();
  if (msg.includes("does not support tools")) return true;
  const body = (error.responseBody ?? "").toLowerCase();
  if (body.includes("does not support tools")) return true;
  return false;
}
