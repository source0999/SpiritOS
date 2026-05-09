"use client";

// ── VoiceSettingsPanel - Voice picker + timing (Prompt 9I mobile-first polish) ───
import { ChevronDown, ChevronRight } from "lucide-react";
import { memo, useState } from "react";

import type { UseTtsState } from "@/hooks/useTTS";
import { TTS_VOICE_SPEED_PRESETS } from "@/lib/tts/voice-speed";
import { cn } from "@/lib/cn";
import { formatTtsFriendlySummaryLines, formatTtsLastVoiceLine } from "@/lib/tts/format-tts-latency";

function voiceCatalogSourceLine(
  source: string | undefined,
  allowlistMode: string | undefined,
): string {
  if (!source && !allowlistMode) return "Source: -";
  if (source === "elevenlabs-api") return "Source: ElevenLabs catalog";
  if (source === "env-name-allowlist") {
    return "Source: allowlist (names resolved by catalog)";
  }
  if (source === "env-allowlist") return "Source: allowlist (voice IDs from env)";
  if (source === "mixed") return "Source: allowlist + catalog metadata";
  if (source) return `Source: ${source}`;
  return `Source: - · mode: ${allowlistMode ?? "-"}`;
}

const START_OPTS = [0, 250, 500, 1000] as const;
const GAP_OPTS = [0, 150, 300, 600] as const;

export type VoiceSettingsPanelProps = {
  state: UseTtsState;
  onEnableAudio: () => void | Promise<void | boolean>;
  onStartDelayChange: (ms: number) => void;
  onSentenceGapChange: (ms: number) => void;
  onVoiceSpeedChange?: (speed: number) => void;
  onToggleAutoSpeak?: () => void;
  /** ElevenLabs voice_id from catalog select. */
  onElevenLabsVoiceChange?: (voiceId: string) => void;
  /** Refetch `/api/tts/voices` after a catalog failure. */
  onRetryVoiceCatalog?: () => void | Promise<void>;
  disabled?: boolean;
};

export const VoiceSettingsPanel = memo(function VoiceSettingsPanel({
  state,
  onEnableAudio,
  onStartDelayChange,
  onSentenceGapChange,
  onVoiceSpeedChange,
  onToggleAutoSpeak,
  onElevenLabsVoiceChange,
  onRetryVoiceCatalog,
  disabled = false,
}: VoiceSettingsPanelProps) {
  const [debugTimingOpen, setDebugTimingOpen] = useState(false);
  const ctx = state.audioContextState;
  const showVoiceRetry =
    Boolean(onRetryVoiceCatalog) &&
    (state.voicesStatus === "error" ||
      (state.voicesStatus === "ok" &&
        state.voices.length === 0 &&
        (state.voicesWarnings?.length ?? 0) > 0));
  const showEnableAudioInSettings =
    ctx === "suspended" ||
    (typeof state.lastError === "string" &&
      (/audio blocked/i.test(state.lastError) || /enable audio/i.test(state.lastError)));

  return (
    <div
      className={cn(
        "flex min-w-0 flex-col gap-3.5",
        disabled && "pointer-events-none opacity-40",
      )}
    >
      <section className="flex min-w-0 flex-col gap-2 rounded-lg border border-white/[0.06] bg-black/20 p-2.5">
        <p className="font-mono text-[9px] font-semibold uppercase tracking-[0.18em] text-chalk/45">
          Playback
        </p>
        <div className="font-mono text-[10px] text-chalk/50">
          Audio engine:{" "}
          <span className="text-chalk/75">{ctx === "unknown" ? " - " : ctx}</span>
        </div>

        {showEnableAudioInSettings ? (
          <div className="flex flex-col gap-1">
            <button
              type="button"
              onClick={() => void onEnableAudio()}
              className="touch-manipulation rounded-md border border-[color:color-mix(in_oklab,var(--spirit-accent)_40%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_12%,transparent)] px-3 py-2 text-left font-mono text-[10px] font-semibold uppercase tracking-wide text-[color:var(--spirit-accent-strong)]"
            >
              Enable audio
            </button>
            <p className="font-mono text-[9px] leading-snug text-chalk/45">
              iOS/Android may block playback until you tap here once.
            </p>
          </div>
        ) : null}

        {onToggleAutoSpeak ? (
          <button
            type="button"
            onClick={onToggleAutoSpeak}
            aria-pressed={state.autoSpeakAssistant}
            className={cn(
              "touch-manipulation rounded-md border px-3 py-2 text-left font-mono text-[10px] uppercase tracking-wide",
              state.autoSpeakAssistant
                ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_40%,transparent)] text-[color:var(--spirit-accent-strong)]"
                : "border-[color:var(--spirit-border)] text-chalk/55",
            )}
          >
            Auto-speak assistant: {state.autoSpeakAssistant ? "on" : "off"}
          </button>
        ) : null}

        {onElevenLabsVoiceChange ? (
          <label className="flex min-w-0 flex-col gap-1">
            <span className="font-mono text-[10px] font-semibold uppercase tracking-wide text-chalk/55">
              Voice
            </span>
            <span className="font-mono text-[9px] leading-snug text-chalk/40">
              ElevenLabs library (same as your account).
            </span>
            <p className="font-mono text-[9px] leading-snug text-chalk/48">
              {voiceCatalogSourceLine(state.voicesSource, state.voicesAllowlistMode)}
            </p>
            {state.voicesWarnings && state.voicesWarnings.length > 0 ? (
              <p
                className="line-clamp-3 font-mono text-[9px] leading-snug text-amber-200/75"
                title={state.voicesWarnings.join("\n")}
              >
                {state.voicesWarnings.slice(0, 2).join(" ")}
              </p>
            ) : null}
            {state.voicesStatus === "loading" ? (
              <p className="font-mono text-[10px] text-chalk/50">Loading voices…</p>
            ) : null}
            {state.voicesStatus === "error" ? (
              <div className="flex flex-col gap-2">
                <p className="font-mono text-[10px] text-rose-200/80">
                  Could not load voices{state.voicesError ? ` - ${state.voicesError}` : ""}
                </p>
              </div>
            ) : null}
            {showVoiceRetry && onRetryVoiceCatalog ? (
              <button
                type="button"
                aria-label="Retry or refresh ElevenLabs voices"
                onClick={() => void onRetryVoiceCatalog()}
                className="touch-manipulation self-start rounded-md border border-[color:color-mix(in_oklab,var(--spirit-accent)_40%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_12%,transparent)] px-3 py-2 font-mono text-[10px] font-semibold uppercase tracking-wide text-[color:var(--spirit-accent-strong)]"
              >
                Retry / Refresh voices
              </button>
            ) : null}
            <select
              className="touch-manipulation min-h-[40px] w-full rounded-md border border-[color:var(--spirit-border)] bg-black/40 px-2 py-2 font-mono text-[15px] leading-snug text-chalk sm:text-[14px] lg:text-[13px]"
              aria-label="ElevenLabs voice"
              value={state.elevenLabsVoiceId ?? ""}
              disabled={
                state.voicesStatus === "loading" ||
                (state.voices.length === 0 && state.voicesStatus !== "error")
              }
              onChange={(e) => onElevenLabsVoiceChange(e.target.value)}
            >
              {state.elevenLabsVoiceId &&
              !state.voices.some((v) => v.voice_id === state.elevenLabsVoiceId) ? (
                <option value={state.elevenLabsVoiceId}>
                  {state.elevenLabsVoiceName ?? state.elevenLabsVoiceId}
                </option>
              ) : null}
              {state.voices.length === 0 && state.voicesStatus !== "loading" ? (
                <option value="">No voices loaded</option>
              ) : null}
              {state.voices.map((v) => (
                <option key={v.voice_id} value={v.voice_id}>
                  {v.name}
                  {v.category ? ` · ${v.category}` : ""}
                </option>
              ))}
            </select>
            {state.elevenLabsVoiceName ? (
              <p className="truncate font-mono text-[9px] text-chalk/38">
                Selected: {state.elevenLabsVoiceName}
                {state.elevenLabsVoiceId && state.elevenLabsVoiceId.length > 12 ? (
                  <span className="text-chalk/28">
                    {" "}
                    · {state.elevenLabsVoiceId.slice(0, 8)}…
                  </span>
                ) : state.elevenLabsVoiceId ? (
                  <span className="text-chalk/28"> · {state.elevenLabsVoiceId}</span>
                ) : null}
              </p>
            ) : null}
          </label>
        ) : null}

        {onVoiceSpeedChange ? (
          <label className="flex min-w-0 flex-col gap-1">
            <span className="font-mono text-[10px] font-semibold uppercase tracking-wide text-chalk/55">
              Voice speed
            </span>
            <span className="font-mono text-[9px] leading-snug text-chalk/40">
              Controls speaking pace (ElevenLabs).
            </span>
            <select
              value={state.voiceSpeed}
              onChange={(e) => onVoiceSpeedChange(Number(e.target.value))}
              className="touch-manipulation min-h-[40px] w-full rounded-md border border-[color:var(--spirit-border)] bg-black/40 px-2 py-2 font-mono text-[15px] text-chalk sm:text-[14px] lg:text-[13px]"
              aria-label="Voice speed"
            >
              {TTS_VOICE_SPEED_PRESETS.map((s) => (
                <option key={s} value={s}>
                  {s <= 1.001
                    ? "1.00x Normal"
                    : s <= 1.085
                      ? "1.08x Slightly faster"
                      : s <= 1.15
                        ? "1.12x Faster"
                        : "1.18x Fast"}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </section>

      <section className="flex min-w-0 flex-col gap-1.5">
        <p className="font-mono text-[9px] font-semibold uppercase tracking-[0.18em] text-chalk/45">
          Last session
        </p>
        <div className="space-y-1.5 rounded-md border border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] bg-black/25 px-2.5 py-2">
          {formatTtsFriendlySummaryLines({
            lastLatency: state.lastLatency,
            lastError: state.lastError,
            lastVoiceNote: state.lastVoiceNote,
          }).map((line, idx) => (
            <p
              key={idx}
              className="font-mono text-[11px] leading-relaxed text-chalk/85 sm:text-[12px]"
            >
              {line}
            </p>
          ))}
        </div>
      </section>

      <div className="border-t border-white/[0.06] pt-1">
        <button
          type="button"
          onClick={() => setDebugTimingOpen((v) => !v)}
          aria-expanded={debugTimingOpen}
          className="flex w-full items-center justify-between gap-2 rounded-md py-1.5 text-left font-mono text-[9px] font-semibold uppercase tracking-wide text-chalk/45"
        >
          Debug voice timing
          {debugTimingOpen ? (
            <ChevronDown className="h-3.5 w-3.5 shrink-0" aria-hidden />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 shrink-0" aria-hidden />
          )}
        </button>
        {debugTimingOpen ? (
          <div className="mt-2 flex flex-col gap-3">
            <p className="font-mono text-[9px] leading-snug text-chalk/40">
              Only for testing timing - leave at zero in production unless you enjoy suffering.
            </p>
            <div className="grid min-w-0 gap-2 sm:grid-cols-2">
              <label className="flex min-w-0 flex-col gap-0.5">
                <span className="font-mono text-[9px] font-semibold uppercase tracking-wide text-chalk/50">
                  Delay before voice starts
                </span>
                <span className="font-mono text-[8px] leading-snug text-chalk/38">
                  Milliseconds before the first chunk plays
                </span>
                <select
                  value={state.startDelayMs}
                  onChange={(e) => onStartDelayChange(Number(e.target.value))}
                  className="touch-manipulation min-h-[44px] w-full rounded-md border border-[color:var(--spirit-border)] bg-black/40 px-2 py-1.5 font-mono text-[16px] text-chalk max-lg:text-[16px] lg:text-[11px]"
                  aria-label="Delay before voice starts"
                >
                  {START_OPTS.map((ms) => (
                    <option key={ms} value={ms}>
                      {ms}ms
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex min-w-0 flex-col gap-0.5">
                <span className="font-mono text-[9px] font-semibold uppercase tracking-wide text-chalk/50">
                  Pause between chunks
                </span>
                <span className="font-mono text-[8px] leading-snug text-chalk/38">
                  Silence between TTS segments
                </span>
                <select
                  value={state.sentenceGapMs}
                  onChange={(e) => onSentenceGapChange(Number(e.target.value))}
                  className="touch-manipulation min-h-[44px] w-full rounded-md border border-[color:var(--spirit-border)] bg-black/40 px-2 py-1.5 font-mono text-[16px] text-chalk max-lg:text-[16px] lg:text-[11px]"
                  aria-label="Pause between speech chunks"
                >
                  {GAP_OPTS.map((ms) => (
                    <option key={ms} value={ms}>
                      {ms}ms
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <p className="font-mono text-[9px] text-chalk/45">
              Queue {state.queueLength}
              {state.lastLatency ? (
                <span className="mt-1 block text-chalk/55">
                  Technical: {formatTtsLastVoiceLine(state.lastLatency)}
                </span>
              ) : null}
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
});
