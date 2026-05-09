import "server-only";

import { getOracleModelId, getSpiritChatModelId } from "@/lib/server/model-routing";
import { getSttDiagnostics } from "@/lib/server/stt-provider";

// ── Spirit diagnostics - env-derived labels for health JSON (no secrets) ────────
// > Context/output/TTS copy matches runtime in route.ts + Piper / ElevenLabs wiring

/** Route `streamText` cap; override with SPIRIT_MAX_OUTPUT_TOKENS. */
export function getSpiritMaxOutputTokens(): number {
  const raw = process.env.SPIRIT_MAX_OUTPUT_TOKENS?.trim();
  if (!raw) return 1024;
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) return 1024;
  return n;
}

/** Oracle lane cap; ORACLE_MAX_OUTPUT_TOKENS unset → same as chat cap. */
export function getOracleMaxOutputTokens(): number {
  const raw = process.env.ORACLE_MAX_OUTPUT_TOKENS?.trim();
  if (!raw) return getSpiritMaxOutputTokens();
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) return getSpiritMaxOutputTokens();
  return n;
}

function getMaxOutputTokensMeta(): { value: number; source: string } {
  const raw = process.env.SPIRIT_MAX_OUTPUT_TOKENS?.trim();
  if (!raw) return { value: 1024, source: "default (1024)" };
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) return { value: 1024, source: "default (1024)" };
  return { value: n, source: "SPIRIT_MAX_OUTPUT_TOKENS" };
}

function getOracleMaxOutputTokensMeta(): { value: number; source: string } {
  const raw = process.env.ORACLE_MAX_OUTPUT_TOKENS?.trim();
  if (!raw) {
    return {
      value: getSpiritMaxOutputTokens(),
      source: "inherits SPIRIT_MAX_OUTPUT_TOKENS (ORACLE_MAX_OUTPUT_TOKENS unset)",
    };
  }
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) {
    return {
      value: getSpiritMaxOutputTokens(),
      source: "invalid ORACLE_MAX_OUTPUT_TOKENS → chat cap",
    };
  }
  return { value: n, source: "ORACLE_MAX_OUTPUT_TOKENS" };
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
  const prov = process.env.TTS_PROVIDER?.trim().toLowerCase() || "piper";
  if (prov === "elevenlabs") {
    const hasKey = Boolean(process.env.ELEVENLABS_API_KEY?.trim());
    const voice =
      process.env.ELEVENLABS_VOICE_ID?.trim() || "fgDJOgmENIR82PueQrVs";
    return {
      provider: hasKey ? "ElevenLabs" : "ElevenLabs (no API key)",
      voice,
      source: hasKey
        ? "TTS_PROVIDER=elevenlabs"
        : "TTS_PROVIDER=elevenlabs but ELEVENLABS_API_KEY unset",
    };
  }
  const url = process.env.PIPER_TTS_URL?.trim();
  const voice = process.env.PIPER_TTS_VOICE?.trim() || "fable";
  if (url) {
    return { provider: "Piper", voice, source: "PIPER_TTS_URL" };
  }
  return { provider: "Piper (no URL)", voice, source: "PIPER_TTS_URL unset" };
}

export type SpiritDiagnosticsPayload = {
  engine: string;
  maxOutputTokens: number;
  maxOutputTokensSource: string;
  oracleMaxOutputTokens: number;
  oracleMaxOutputTokensSource: string;
  chatModel: string;
  oracleLaneModel: string;
  context: { label: string; source: string };
  tts: { provider: string; voice: string; source: string };
  stt: { provider: string; url: string; source: string; transcribePath: string };
};

/** Single merge-friendly blob for /api/spirit/health JSON. */
export function getSpiritDiagnostics(): SpiritDiagnosticsPayload {
  const ctx = getSpiritContextWindow();
  const tts = getSpiritTtsDiagnostics();
  const cap = getMaxOutputTokensMeta();
  const oracleCap = getOracleMaxOutputTokensMeta();
  const stt = getSttDiagnostics();
  return {
    engine: "Ollama",
    maxOutputTokens: cap.value,
    maxOutputTokensSource: cap.source,
    oracleMaxOutputTokens: oracleCap.value,
    oracleMaxOutputTokensSource: oracleCap.source,
    chatModel: getSpiritChatModelId(),
    oracleLaneModel: getOracleModelId(),
    context: ctx,
    tts: {
      provider: tts.provider,
      voice: tts.voice,
      source: tts.source,
    },
    stt: {
      provider: stt.provider,
      url: stt.url,
      source: stt.source,
      transcribePath: stt.transcribePath,
    },
  };
}
