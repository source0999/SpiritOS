import "server-only";

// ── Spirit diagnostics — env-derived labels for health JSON (no secrets) ────────
// > Context/output/TTS copy matches runtime in route.ts + Piper wiring

/** Route `streamText` cap; override with SPIRIT_MAX_OUTPUT_TOKENS. */
export function getSpiritMaxOutputTokens(): number {
  const raw = process.env.SPIRIT_MAX_OUTPUT_TOKENS?.trim();
  if (!raw) return 1024;
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) return 1024;
  return n;
}

function getMaxOutputTokensMeta(): { value: number; source: string } {
  const raw = process.env.SPIRIT_MAX_OUTPUT_TOKENS?.trim();
  if (!raw) return { value: 1024, source: "default (1024)" };
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) return { value: 1024, source: "default (1024)" };
  return { value: n, source: "SPIRIT_MAX_OUTPUT_TOKENS" };
}

/**
 * Host-side context window when set on Ollama; never invent "~8k" without env.
 */
export function getSpiritContextWindow(): { label: string; source: string } {
  const raw = process.env.OLLAMA_NUM_CTX?.trim();
  if (!raw) {
    return { label: "Host default", source: "OLLAMA_NUM_CTX unset" };
  }
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) {
    return { label: "Host default", source: "OLLAMA_NUM_CTX unset" };
  }
  return { label: String(n), source: "OLLAMA_NUM_CTX" };
}

export function getSpiritTtsDiagnostics(): {
  provider: string;
  voice: string;
  source: string;
} {
  const url = process.env.PIPER_TTS_URL?.trim();
  const voice = process.env.PIPER_TTS_VOICE?.trim() || "fable";
  if (url) {
    return { provider: "Piper", voice, source: "PIPER_TTS_URL" };
  }
  return { provider: "Disabled", voice, source: "PIPER_TTS_URL unset" };
}

export type SpiritDiagnosticsPayload = {
  engine: string;
  maxOutputTokens: number;
  maxOutputTokensSource: string;
  context: { label: string; source: string };
  tts: { provider: string; voice: string; source: string };
};

/** Single merge-friendly blob for /api/spirit/health JSON. */
export function getSpiritDiagnostics(): SpiritDiagnosticsPayload {
  const ctx = getSpiritContextWindow();
  const tts = getSpiritTtsDiagnostics();
  const cap = getMaxOutputTokensMeta();
  return {
    engine: "Ollama",
    maxOutputTokens: cap.value,
    maxOutputTokensSource: cap.source,
    context: ctx,
    tts: {
      provider: tts.provider,
      voice: tts.voice,
      source: tts.source,
    },
  };
}
