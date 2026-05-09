// ── voice-speed - shared clamp for client + server TTS (Prompt 9H) ───────────────

export const TTS_SPEED_MIN = 0.7;
export const TTS_SPEED_MAX = 1.2;
export const TTS_SPEED_DEFAULT = 1.12;

export function clampTtsVoiceSpeed(n: number): number {
  return Math.min(TTS_SPEED_MAX, Math.max(TTS_SPEED_MIN, n));
}

/** UI / localStorage presets (must stay inside clamp range). */
export const TTS_VOICE_SPEED_PRESETS = [1.0, 1.08, 1.12, 1.18] as const;
