// ── spirit-runtime-surface — shared literal union (client + server; no server-only) ─
// > `model-routing.ts` stays server-only; UI + JSON parser import from here only.

export type SpiritRuntimeSurface = "chat" | "oracle";
