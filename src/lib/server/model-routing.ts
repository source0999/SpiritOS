import "server-only";

import type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";

// ── model-routing - /chat vs /oracle Ollama ids (Prompt 9C) ──────────────────────
// > Hermes-class chat stays on OLLAMA_MODEL; Oracle lane can opt into a smaller model.

export type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";

export const SPIRIT_ABLITERATED_CHAT_MODEL_ID = "hermes3:8b-abliterated";

export function getSpiritChatModelId(): string {
  return process.env.OLLAMA_MODEL?.trim() || "hermes4";
}

export function getAbliteratedChatModelId(): string {
  return SPIRIT_ABLITERATED_CHAT_MODEL_ID;
}

/** Oracle UI; falls back to chat model when ORACLE_OLLAMA_MODEL unset. */
export function getOracleModelId(): string {
  const o = process.env.ORACLE_OLLAMA_MODEL?.trim();
  if (o) return o;
  return getSpiritChatModelId();
}

export function resolveOllamaModelId(
  surface: SpiritRuntimeSurface,
  opts?: { abliteratedModeEnabled?: boolean },
): string {
  if (surface === "oracle") return getOracleModelId();
  return opts?.abliteratedModeEnabled
    ? getAbliteratedChatModelId()
    : getSpiritChatModelId();
}
