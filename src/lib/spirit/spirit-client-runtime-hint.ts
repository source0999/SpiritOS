// ── Client-visible Ollama label (optional NEXT_PUBLIC_OLLAMA_MODEL) ───────────────

import type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";

export function getSpiritChatRuntimeDisplayLabel(): string {
  const v = process.env.NEXT_PUBLIC_OLLAMA_MODEL?.trim();
  if (v) return v;
  return "Hermes-class (local Ollama)";
}

/** Activity panel + Oracle chrome - chat shows local model hint; Oracle is explicit. */
export function getSpiritRuntimeSurfaceDisplayLabel(surface: SpiritRuntimeSurface): string {
  if (surface === "oracle") return "Oracle";
  return getSpiritChatRuntimeDisplayLabel();
}
