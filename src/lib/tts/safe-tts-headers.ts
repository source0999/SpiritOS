// ── safe-tts-headers - ASCII-only TTS response headers (Prompt 9K ByteString crash) ─
// > Next/Headers reject Unicode in ByteString fields - en dash in voice names nuked Tailscale.

export const HEADER_TTS_VOICE_NAME_ENCODED = "X-Spirit-TTS-Voice-Name-Encoded";

/** Percent-encode for header transport; result is ASCII. */
export function encodeTtsVoiceNameForHeader(name: string): string {
  return encodeURIComponent(name.trim());
}

/** Decode header value; returns null on garbage. */
export function decodeTtsVoiceNameFromHeader(encoded: string | null | undefined): string | null {
  if (encoded == null) return null;
  const t = encoded.trim();
  if (!t) return null;
  try {
    const out = decodeURIComponent(t);
    return out.trim() || null;
  } catch {
    return null;
  }
}
