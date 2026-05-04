// ── Client-visible Ollama label (optional NEXT_PUBLIC_OLLAMA_MODEL) ───────────────

export function getSpiritChatRuntimeDisplayLabel(): string {
  const v = process.env.NEXT_PUBLIC_OLLAMA_MODEL?.trim();
  if (v) return v;
  return "Hermes-class (local Ollama)";
}
