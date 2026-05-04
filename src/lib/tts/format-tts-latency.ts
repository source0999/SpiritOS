// ── formatTtsLatency — “last voice” copy + start-first summary (Prompt 9L) ────────
import type { TtsLatency } from "@/lib/tts/audio-queue";

function formatMs(ms: number | undefined): string {
  if (ms == null || !Number.isFinite(ms)) return "—";
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}

/** User-facing seconds (710ms → 0.7s; 5700ms → 5.7s). */
export function formatSecondsOneDecimal(ms: number | undefined): string {
  if (ms == null || !Number.isFinite(ms)) return "—";
  return `${(ms / 1000).toFixed(1)}s`;
}

function providerLabel(p?: string): string {
  if (!p || p === "—") return "—";
  if (p === "elevenlabs") return "ElevenLabs";
  if (p === "piper") return "Piper";
  return p;
}

function playbackLabel(m?: TtsLatency["playbackMode"]): string {
  if (m === "html-audio") return "HTMLAudioElement";
  if (m === "audio-context") return "AudioContext";
  return "—";
}

/** User-facing playback line (Voice card friendly block). */
function playbackFriendly(m?: TtsLatency["playbackMode"]): string {
  if (m === "html-audio") return "HTMLAudio (browser)";
  if (m === "audio-context") return "WebAudio (browser)";
  return "Browser audio";
}

function shortVoiceId(id: string): string {
  const t = id.trim();
  if (t.length <= 14) return t;
  return `${t.slice(0, 6)}…${t.slice(-4)}`;
}

/** Best-effort ms from first /api/tts request until playback starts. */
function resolveTimeToFirstAudioMs(lat: TtsLatency): number | undefined {
  if (typeof lat.timeToFirstAudioMs === "number" && Number.isFinite(lat.timeToFirstAudioMs)) {
    return lat.timeToFirstAudioMs;
  }
  const fetch = typeof lat.fetchMs === "number" && Number.isFinite(lat.fetchMs) ? lat.fetchMs : 0;
  const dec =
    typeof lat.decodeMs === "number" && Number.isFinite(lat.decodeMs) ? lat.decodeMs : 0;
  if (fetch > 0 || dec > 0) return fetch + dec;
  return undefined;
}

/**
 * Primary “audio started” line for the Voice card (Prompt 9L).
 * Under 1s uses “under 1 second” when ms ∈ [500, 1000); else one-decimal seconds.
 */
export function formatTtsFriendlyStartSummary(lat: TtsLatency | undefined): string {
  if (!lat) return "Audio has not been tested yet";
  const ms = resolveTimeToFirstAudioMs(lat);
  if (ms != null && Number.isFinite(ms) && ms >= 0) {
    if (ms < 500) {
      return ms < 100
        ? `Audio started in ${Math.round(ms)}ms`
        : `Audio started in ${formatSecondsOneDecimal(ms)}`;
    }
    if (ms < 1000) return "Audio started in under 1 second";
    return `Audio started in ${formatSecondsOneDecimal(ms)}`;
  }
  if (lat.fetchMs == null && lat.totalMs == null && !lat.provider) {
    return "Audio has not been tested yet";
  }
  return "Audio has not been tested yet";
}

/** Single readable line for Voice settings header (not buried in debug). */
export function formatTtsLastVoiceLine(lat: TtsLatency | undefined): string {
  if (!lat || (lat.fetchMs == null && lat.totalMs == null && !lat.provider)) {
    return "Last voice: Not tested yet";
  }
  const pb = playbackLabel(lat.playbackMode);
  const voiceLabel =
    typeof lat.voiceName === "string" && lat.voiceName.trim()
      ? lat.voiceName.trim()
      : typeof lat.voiceId === "string" && lat.voiceId.trim()
        ? shortVoiceId(lat.voiceId.trim())
        : null;
  const ttfa =
    typeof lat.timeToFirstAudioMs === "number" && Number.isFinite(lat.timeToFirstAudioMs)
      ? `time-to-audio ${formatMs(lat.timeToFirstAudioMs)}`
      : null;
  const spoken =
    typeof lat.spokenSummaryLine === "string" && lat.spokenSummaryLine.trim()
      ? lat.spokenSummaryLine.trim()
      : null;
  const parts = [
    `Last voice: ${providerLabel(lat.provider)}`,
    voiceLabel,
    typeof lat.speed === "number" && Number.isFinite(lat.speed)
      ? `speed ${lat.speed.toFixed(2)}x`
      : null,
    typeof lat.upstreamMs === "number" ? `upstream ${formatMs(lat.upstreamMs)}` : null,
    lat.fetchMs != null ? `fetch ${formatMs(lat.fetchMs)}` : null,
    lat.decodeMs != null ? `decode ${formatMs(lat.decodeMs)}` : null,
    ttfa,
    lat.totalMs != null ? `playback span ${formatMs(lat.totalMs)}` : null,
    typeof lat.startDelayMs === "number" && lat.startDelayMs > 0
      ? `start delay ${lat.startDelayMs}ms`
      : null,
    pb !== "—" ? pb : null,
    spoken,
  ].filter(Boolean);
  return parts.join(" · ");
}

/** Maps raw / internal errors to short UI labels (no console cosplay). */
export function formatTtsErrorLabel(raw: string | undefined): string | undefined {
  if (!raw?.trim()) return undefined;
  const t = raw.trim();
  if (/enable audio/i.test(t) || /notallowed/i.test(t) || /audio blocked/i.test(t)) {
    return "Audio blocked. Tap Enable audio.";
  }
  if (/aborted/i.test(t)) return "aborted";
  if (/fetch|api\/tts|network/i.test(t)) return "provider unavailable";
  return t.length > 120 ? `${t.slice(0, 117)}…` : t;
}

export type VoiceActivityLineInput = {
  lastLatency?: TtsLatency;
  lastError?: string;
  lastVoiceNote?: "interrupted";
};

/**
 * Plain-language lines for the Voice card “Last session” block (Prompt 9L).
 * Total playback / raw ms live under Debug voice timing.
 */
export function formatTtsFriendlySummaryLines(i: VoiceActivityLineInput): string[] {
  const err = formatTtsErrorLabel(i.lastError);
  if (err) {
    return [`Last voice failed: ${err}`];
  }
  if (i.lastVoiceNote === "interrupted" && !i.lastLatency) {
    return ["Last voice was interrupted"];
  }
  const lat = i.lastLatency;
  if (!lat || (lat.fetchMs == null && lat.totalMs == null && !lat.provider)) {
    return ["Audio has not been tested yet"];
  }

  const voiceLabel =
    typeof lat.voiceName === "string" && lat.voiceName.trim()
      ? lat.voiceName.trim()
      : typeof lat.voiceId === "string" && lat.voiceId.trim()
        ? shortVoiceId(lat.voiceId.trim())
        : "—";

  const primary = formatTtsFriendlyStartSummary(lat);

  const responseMs =
    typeof lat.upstreamMs === "number" && Number.isFinite(lat.upstreamMs)
      ? lat.upstreamMs
      : typeof lat.fetchMs === "number" && Number.isFinite(lat.fetchMs)
        ? lat.fetchMs
        : undefined;

  const prov = providerLabel(lat.provider);
  const responseLine =
    responseMs != null
      ? `${prov} responded in ${formatSecondsOneDecimal(responseMs)}`
      : `${prov} responded in —`;

  return [
    primary,
    responseLine,
    `Browser playback: ${playbackFriendly(lat.playbackMode)}`,
    `Voice: ${voiceLabel}`,
  ];
}

/**
 * One primary line for the voice card: error > latency metrics > interrupt-only hint.
 * Interrupted does not clobber an existing successful latency line (no junk suffix).
 */
export function formatVoiceActivityPrimaryLine(i: VoiceActivityLineInput): string {
  const err = formatTtsErrorLabel(i.lastError);
  if (err) return `Last voice error: ${err}`;
  if (i.lastLatency) return formatTtsLastVoiceLine(i.lastLatency);
  if (i.lastVoiceNote === "interrupted") return "Last voice: interrupted";
  return formatTtsLastVoiceLine(i.lastLatency);
}

/** Compact formatter for tests / logs. */
export function formatTtsLatency(lat: TtsLatency): string {
  return formatTtsLastVoiceLine(lat);
}
