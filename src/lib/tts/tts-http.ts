// ── tts-http - /api/tts JSON helpers (Prompt 9H) ─────────────────────────────────

export type ParsedTtsSpeed =
  | { ok: true; value: number | undefined }
  | { ok: false; message: string };

/**
 * Optional `speed` on POST body: absent/null → undefined (use env).
 * Present but non-finite number → 400 via `{ ok: false }`.
 */
export function parseOptionalTtsSpeedField(body: Record<string, unknown>): ParsedTtsSpeed {
  if (!Object.prototype.hasOwnProperty.call(body, "speed")) {
    return { ok: true, value: undefined };
  }
  const v = body.speed;
  if (v === undefined || v === null) return { ok: true, value: undefined };
  if (typeof v !== "number" || !Number.isFinite(v)) {
    return { ok: false, message: "speed must be a finite number" };
  }
  return { ok: true, value: v };
}

export type ParsedTtsVoiceId =
  | { ok: true; value: string | undefined }
  | { ok: false; message: string };

const MAX_VOICE_ID_LEN = 80;

/**
 * Optional `voiceId` on POST body: absent → undefined (use server default chain).
 * Non-string or absurd length → 400.
 */
export function parseOptionalTtsVoiceIdField(body: Record<string, unknown>): ParsedTtsVoiceId {
  if (!Object.prototype.hasOwnProperty.call(body, "voiceId")) {
    return { ok: true, value: undefined };
  }
  const v = body.voiceId;
  if (v === undefined || v === null) return { ok: true, value: undefined };
  if (typeof v !== "string") {
    return { ok: false, message: "voiceId must be a string" };
  }
  const t = v.trim();
  if (!t) return { ok: true, value: undefined };
  if (t.length > MAX_VOICE_ID_LEN) {
    return { ok: false, message: `voiceId exceeds ${MAX_VOICE_ID_LEN} characters` };
  }
  return { ok: true, value: t };
}

export type ParsedTtsVoiceName =
  | { ok: true; value: string | undefined }
  | { ok: false; message: string };

const MAX_VOICE_NAME_LEN = 120;

/**
 * Optional `voiceName` - UI label only; never selects the ElevenLabs endpoint (use `voiceId`).
 */
export function parseOptionalTtsVoiceNameField(body: Record<string, unknown>): ParsedTtsVoiceName {
  if (!Object.prototype.hasOwnProperty.call(body, "voiceName")) {
    return { ok: true, value: undefined };
  }
  const v = body.voiceName;
  if (v === undefined || v === null) return { ok: true, value: undefined };
  if (typeof v !== "string") {
    return { ok: false, message: "voiceName must be a string" };
  }
  const t = v.trim();
  if (!t) return { ok: true, value: undefined };
  if (t.length > MAX_VOICE_NAME_LEN) {
    return { ok: false, message: `voiceName exceeds ${MAX_VOICE_NAME_LEN} characters` };
  }
  return { ok: true, value: t };
}
