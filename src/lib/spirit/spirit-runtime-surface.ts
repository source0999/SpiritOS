// ── spirit-runtime-surface — shared literal union (client + server; no server-only) ─
// > `model-routing.ts` stays server-only; UI + JSON parser import from here only.

export type SpiritRuntimeSurface = "chat" | "oracle";

/** Default POST body surface — `/oracle` overrides with `"oracle"`. */
export const DEFAULT_SPIRIT_RUNTIME_SURFACE: SpiritRuntimeSurface = "chat";

/**
 * Voice-layer context for `/oracle`. Mode text stays first (personality); this overrides
 * workspace/coding-default smell without replacing Peer/Teacher/etc. tone.
 */
export function buildRuntimeSurfaceInstruction(surface: SpiritRuntimeSurface): string {
  if (surface !== "oracle") return "";

  return `## Oracle Voice surface (live conversation context)
You are currently running inside Oracle Voice mode, a live spoken conversation surface.
This is not the coding workspace and not a support chat.
Do not default to coding, repos, debugging, terminal work, projects, or software advice unless the user explicitly brings those up.
Treat the user's speech like a real-time conversation.
Keep most replies short enough to speak aloud naturally.
If the user is vague, respond naturally or ask one simple follow-up.
Avoid customer-service phrases like "How may I assist you?" or "I am here to help with coding questions."
Do not say you are a chatbot unless the user directly asks what you are.
Preserve the selected mode's personality, but make it voice-first and conversational.`.trim();
}
