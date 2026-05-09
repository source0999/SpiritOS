"use client";

// ── OracleVoiceControls - hands-free Oracle session controls (Prompt 10D-E) ─────
// > Big "Start session" CTA, big "Stop session" while running, tiny "Finish now"
// > backup that only shows mid-utterance. Mic + Whisper + secure-context info live
// > inline so the user never has to spelunk an advanced menu.

import { Mic, MicOff, RefreshCw, Square } from "lucide-react";
import { memo } from "react";

import { VoiceControl } from "@/components/chat/VoiceControl";
import "@/components/oracle/oracle-visuals.css";
import type { UseTtsState } from "@/hooks/useTTS";
import type { UseOracleSpeechInputReturn } from "@/hooks/useOracleSpeechInput";
import { useMounted } from "@/lib/hooks/useMounted";
import type {
  OracleVoiceLoopMode,
  OracleVoiceSessionStatus,
} from "@/lib/oracle/oracle-voice-session";
import { oracleSessionStatusLabel } from "@/lib/oracle/oracle-voice-session";
import { cn } from "@/lib/cn";

export type OracleVoiceControlsProps = {
  mounted: boolean;
  status: OracleVoiceSessionStatus;
  loopMode: OracleVoiceLoopMode;
  onLoopModeChange: (mode: OracleVoiceLoopMode) => void;
  sessionActive: boolean;
  onStartSession: () => void | Promise<void>;
  onStopSession: () => void;
  onFinishThought: () => void | Promise<void>;
  speech: UseOracleSpeechInputReturn;
  ttsState: UseTtsState;
  onToggleTtsEnabled: () => void;
  onEnableAudio: () => void | Promise<void | boolean>;
  onStopSpeech: () => void;
  onSpeakLatestAssistant: () => void | Promise<void>;
  onStartDelayChange: (ms: number) => void;
  onSentenceGapChange: (ms: number) => void;
  onVoiceSpeedChange: (speed: number) => void;
  onToggleAutoSpeak: () => void;
  onRequestVoiceCatalog: () => void | Promise<void>;
  onElevenLabsVoiceChange: (voiceId: string) => void;
  transportBusy: boolean;
};

function primaryLabel(
  mounted: boolean,
  status: OracleVoiceSessionStatus,
  sessionActive: boolean,
): string {
  if (!mounted) return "…";
  switch (status) {
    case "blocked":
    case "unsupported":
      return "Mic blocked";
    case "requesting-mic":
      return "Requesting mic…";
    case "permission-needed":
      return "Grant mic access";
    case "listening":
      return "Listening…";
    case "hearing-speech":
      return "Hearing you…";
    case "silence-detected":
      return "Sending…";
    case "transcribing":
      return "Transcribing…";
    case "thinking":
      return "Thinking…";
    case "speaking":
      return "Speaking…";
    case "ready":
      return sessionActive ? "Mic idle - waiting…" : "Start session";
    case "restarting":
      return "Restarting…";
    case "stopped":
      return "Resume session";
    case "error":
      return "Try again";
    default:
      if (sessionActive) return "Listening…";
      return "Start session";
  }
}

const SILENCE_PRESETS = [
  { value: 800, label: "0.8s" },
  { value: 1200, label: "1.2s · default" },
  { value: 1800, label: "1.8s" },
  { value: 2500, label: "2.5s" },
];

const SENSITIVITY_PRESETS: { value: "low" | "medium" | "high"; threshold: number; label: string }[] = [
  { value: "low", threshold: 0.06, label: "Low" },
  { value: "medium", threshold: 0.035, label: "Medium · default" },
  { value: "high", threshold: 0.018, label: "High" },
];

function thresholdToSensitivity(threshold: number): "low" | "medium" | "high" {
  if (threshold >= 0.05) return "low";
  if (threshold <= 0.025) return "high";
  return "medium";
}

export const OracleVoiceControls = memo(function OracleVoiceControls({
  mounted,
  status,
  loopMode,
  onLoopModeChange,
  sessionActive,
  onStartSession,
  onStopSession,
  onFinishThought,
  speech,
  ttsState,
  onToggleTtsEnabled,
  onEnableAudio,
  onStopSpeech,
  onSpeakLatestAssistant,
  onStartDelayChange,
  onSentenceGapChange,
  onVoiceSpeedChange,
  onToggleAutoSpeak,
  onRequestVoiceCatalog,
  onElevenLabsVoiceChange,
  transportBusy,
}: OracleVoiceControlsProps) {
  const localMounted = useMounted();
  const readyForHints = mounted && localMounted;

  const showStopSpeech = ttsState.isPlaying || ttsState.queueLength > 0;
  const showSessionButtons = loopMode !== "manual-text";

  const insecureContext =
    readyForHints && speech.capability.isSecureContext === false;
  const blocked = readyForHints && (!speech.canUseMic || speech.blockedReason !== null);
  const showFinishNow =
    readyForHints &&
    (status === "listening" || status === "hearing-speech") &&
    speech.isRecording &&
    loopMode !== "manual-text";

  const hint = (() => {
    if (!readyForHints) return "Checking voice input…";
    if (loopMode === "manual-text") return "Text fallback - type below.";
    if (insecureContext) return speech.capabilityMessage;
    if (blocked) return speech.captureBlockedHint ?? speech.capabilityMessage;
    if (speech.permissionState === "denied")
      return "Mic permission denied - use text fallback or adjust browser site settings.";
    if (speech.devicesEnumerateError) return `Mic list: ${speech.devicesEnumerateError}`;
    if (status === "thinking") return "Thinking…";
    if (status === "speaking") {
      const name = ttsState.elevenLabsVoiceName ?? ttsState.elevenLabsVoiceId ?? "voice";
      return `Speaking with ${name}`;
    }
    if (status === "silence-detected") return "Heard the gap - sending to Whisper.";
    if (status === "restarting") return "Returning to listening…";
    if (status === "hearing-speech")
      return `Auto-send after ${(speech.silenceDurationMs / 1000).toFixed(1)}s of silence.`;
    if (status === "listening") return "Waiting for speech…";
    if (speech.permissionState === "granted")
      return sessionActive
        ? "Session active - speak naturally, Oracle hears the gap."
        : "Mic ready - tap Start session to begin.";
    return oracleSessionStatusLabel(status);
  })();

  const primaryDisabled =
    transportBusy ||
    status === "thinking" ||
    status === "speaking" ||
    status === "transcribing" ||
    status === "silence-detected" ||
    status === "requesting-mic" ||
    status === "restarting" ||
    blocked;

  const micPermissionLabel =
    !readyForHints
      ? "…"
      : speech.permissionState === "granted"
        ? "Granted"
        : speech.permissionState === "denied"
          ? "Denied"
          : speech.permissionState === "unsupported"
            ? "Unavailable"
            : "Needed";

  const meterPct = Math.round((speech.audioLevel ?? 0) * 100);
  const silenceLabel = (() => {
    if (!speech.isRecording) return "Idle";
    if (status === "silence-detected") return "Silence detected - sending…";
    if (status === "hearing-speech") return "Hearing speech";
    return `Waiting for speech (${Math.min(
      Math.round((speech.silenceMs / Math.max(1, speech.silenceDurationMs)) * 100),
      100,
    )}% of ${(speech.silenceDurationMs / 1000).toFixed(1)}s)`;
  })();

  const sensitivity = thresholdToSensitivity(speech.silenceThreshold);

  return (
    <section
      data-testid="oracle-voice-controls"
      aria-label="Oracle voice controls"
      className="oracle-chrome-px flex w-full min-w-0 flex-col gap-3 pb-2 pt-1"
    >
      {/* ── Secure-context warning - impossible to miss when blocked ───────────────── */}
      {readyForHints && insecureContext ? (
        <div
          role="alert"
          data-testid="oracle-secure-context-warning"
          className="rounded-xl border border-rose-500/40 bg-rose-950/30 px-3 py-3 text-rose-50 sm:px-4"
        >
          <p className="font-mono text-[11px] font-semibold uppercase tracking-wider text-rose-200">
            Mic blocked - insecure context
          </p>
          <p className="mt-1 font-mono text-[11px] leading-snug text-rose-100/95">
            This page is open over plain HTTP from a LAN/Tailscale IP. Browsers refuse
            mic access here. Use one of:
          </p>
          <ul className="mt-2 list-disc pl-5 font-mono text-[11px] leading-snug text-rose-100/90">
            <li>
              <span className="rounded border border-white/10 bg-black/30 px-1.5 py-0.5">http://localhost:3000</span>
            </li>
            <li>
              <span className="rounded border border-white/10 bg-black/30 px-1.5 py-0.5">http://127.0.0.1:3000</span>
            </li>
            <li>An HTTPS tunnel (Tailscale Serve/Funnel, Caddy, ngrok, trusted local cert).</li>
          </ul>
          {speech.httpsSamePageUrl ? (
            <a
              href={speech.httpsSamePageUrl}
              data-testid="oracle-https-upgrade-cta"
              className="mt-3 inline-flex min-h-[44px] w-full touch-manipulation items-center justify-center break-all rounded-lg border border-cyan-400/40 bg-cyan-500/15 px-3 py-2 text-center font-mono text-[11px] font-semibold leading-snug text-cyan-50 hover:bg-cyan-500/25"
            >
              Open {speech.httpsSamePageUrl}
            </a>
          ) : null}
        </div>
      ) : null}

      {/* ── Status strip: STT backend / mic permission / mic name ──────────────────── */}
      <div className="flex min-w-0 flex-wrap gap-2 rounded-xl border border-white/[0.06] bg-black/25 px-3 py-2 font-mono text-[11px] text-chalk/75 sm:gap-4">
        <div>
          <span className="text-chalk/45">STT</span> Whisper backend
        </div>
        <div>
          <span className="text-chalk/45">Mic permission</span> {micPermissionLabel}
        </div>
        <div className="min-w-0 truncate">
          <span className="text-chalk/45">Selected mic</span> {speech.selectedDeviceLabel}
        </div>
        <div>
          <span className="text-chalk/45">Secure</span>{" "}
          {readyForHints
            ? speech.capability.isSecureContext
              ? "OK"
              : "Blocked"
            : "…"}
        </div>
      </div>

      {/* ── Loop mode + microphone select (mic select stays accessible) ───────────── */}
      <div className="flex min-w-0 flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
        <label className="flex min-w-0 flex-col gap-1 font-mono text-[10px] uppercase tracking-wider text-chalk/50">
          Session mode
          <select
            value={loopMode}
            onChange={(e) => onLoopModeChange(e.target.value as OracleVoiceLoopMode)}
            className="min-h-[44px] rounded-lg border border-[color:var(--spirit-border)] bg-black/40 px-2 py-2 text-base text-chalk sm:max-w-[16rem]"
          >
            <option value="hands-free">Hands-free session (default)</option>
            <option value="push-to-talk">Push-to-talk</option>
            <option value="manual-text">Text only</option>
          </select>
        </label>

        <label className="flex min-w-0 flex-1 flex-col gap-1 font-mono text-[10px] uppercase tracking-wider text-chalk/50">
          Microphone
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <select
              disabled={
                speech.permissionState !== "granted" || Boolean(speech.devicesEnumerateError)
              }
              value={speech.selectedDeviceId ?? ""}
              onChange={(e) =>
                speech.setSelectedDeviceId(e.target.value ? e.target.value : null)
              }
              className="min-h-[44px] min-w-0 flex-1 rounded-lg border border-[color:var(--spirit-border)] bg-black/40 px-2 py-2 text-base text-chalk disabled:opacity-40 sm:max-w-[min(100%,22rem)]"
            >
              <option value="">Default microphone</option>
              {speech.devices.map((d) => (
                <option key={d.deviceId} value={d.deviceId}>
                  {d.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={speech.permissionState !== "granted"}
              onClick={() => void speech.refreshDevices()}
              className="inline-flex h-11 min-h-[44px] min-w-[44px] shrink-0 touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.04] text-chalk/80 [-webkit-tap-highlight-color:transparent] disabled:opacity-35"
              aria-label="Refresh microphone list"
            >
              <RefreshCw className="h-4 w-4" aria-hidden />
            </button>
          </div>
        </label>
      </div>

      {/* ── Audio meter + silence indicator (only when recording) ──────────────────── */}
      {readyForHints && loopMode !== "manual-text" ? (
        <div
          data-testid="oracle-audio-meter"
          className="flex min-w-0 flex-col gap-1 rounded-xl border border-white/[0.06] bg-black/15 px-3 py-2"
        >
          <div className="flex items-center gap-2">
            <span className="shrink-0 font-mono text-[10px] uppercase tracking-wider text-chalk/45">
              Input level
            </span>
            <div
              className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-white/10"
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={meterPct}
              aria-label="Microphone input level"
            >
              <div
                className={cn(
                  "h-full rounded-full transition-[width] duration-75",
                  status === "hearing-speech"
                    ? "bg-emerald-400/80"
                    : status === "silence-detected"
                      ? "bg-amber-400/80"
                      : "bg-cyan-400/70",
                )}
                style={{ width: `${Math.min(100, meterPct)}%` }}
              />
            </div>
            <span className="shrink-0 font-mono text-[10px] tabular-nums text-chalk/50">
              {meterPct}%
            </span>
          </div>
          <p className="font-mono text-[10px] text-chalk/55" data-testid="oracle-silence-indicator">
            {silenceLabel}
          </p>
        </div>
      ) : null}

      {/* ── Primary CTA + Stop session ─────────────────────────────────────────────── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-stretch">
        {showSessionButtons ? (
          <div className="flex min-w-0 flex-1 flex-col gap-2 sm:flex-row">
            <button
              type="button"
              data-testid="oracle-start-session"
              disabled={primaryDisabled}
              onClick={() => void onStartSession()}
              className={cn(
                "flex min-h-[52px] flex-1 touch-manipulation items-center justify-center gap-2 rounded-2xl border px-4 py-3 font-mono text-[13px] font-semibold uppercase tracking-wide transition sm:min-h-[54px]",
                blocked
                  ? "border-rose-500/45 bg-rose-500/15 text-rose-100"
                  : sessionActive
                    ? "border-cyan-400/45 bg-cyan-500/12 text-chalk"
                    : "border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_12%,transparent)] text-chalk",
                primaryDisabled && "opacity-60",
              )}
            >
              {blocked ? (
                <MicOff className="h-5 w-5 shrink-0" aria-hidden />
              ) : (
                <Mic className="h-5 w-5 shrink-0" aria-hidden />
              )}
              {primaryLabel(mounted, status, sessionActive)}
            </button>

            {sessionActive ? (
              <button
                type="button"
                data-testid="oracle-stop-session"
                onClick={onStopSession}
                className="inline-flex min-h-[52px] shrink-0 touch-manipulation items-center justify-center rounded-2xl border border-amber-400/35 bg-amber-500/15 px-4 font-mono text-[12px] font-semibold uppercase tracking-wide text-amber-50 sm:min-h-[54px]"
              >
                Stop session
              </button>
            ) : null}

            {showFinishNow ? (
              <button
                type="button"
                data-testid="oracle-finish-now"
                onClick={() => void onFinishThought()}
                className="inline-flex min-h-[44px] shrink-0 touch-manipulation items-center justify-center rounded-xl border border-white/10 bg-white/[0.05] px-3 font-mono text-[10px] font-semibold uppercase tracking-wider text-chalk/80 hover:bg-white/[0.08]"
                title="Backup - Oracle will normally auto-send when you stop talking."
              >
                Finish now
              </button>
            ) : null}
          </div>
        ) : (
          <p className="flex flex-1 items-center rounded-xl border border-dashed border-[color:var(--spirit-border)] px-3 py-3 font-mono text-xs text-chalk/55">
            Text-only mode - open the composer below.
          </p>
        )}

        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <div className="font-mono text-[10px] uppercase tracking-wider text-chalk/45">
            Output voice
          </div>
          <VoiceControl
            hideVoiceEnableToggle
            state={ttsState}
            onToggleEnabled={onToggleTtsEnabled}
            onEnableAudio={onEnableAudio}
            onStop={onStopSpeech}
            onSpeakLatestAssistant={onSpeakLatestAssistant}
            onStartDelayChange={onStartDelayChange}
            onSentenceGapChange={onSentenceGapChange}
            onVoiceSpeedChange={onVoiceSpeedChange}
            onToggleAutoSpeak={onToggleAutoSpeak}
            onRequestVoiceCatalog={onRequestVoiceCatalog}
            onElevenLabsVoiceChange={onElevenLabsVoiceChange}
            disabled={transportBusy}
          />
        </div>
      </div>

      {showStopSpeech ? (
        <button
          type="button"
          onClick={onStopSpeech}
          className="inline-flex min-h-[48px] touch-manipulation items-center justify-center gap-2 rounded-xl border border-rose-400/40 bg-rose-500/15 px-4 font-mono text-xs font-semibold uppercase tracking-wide text-rose-50"
        >
          <Square className="h-4 w-4 fill-current" aria-hidden />
          Stop speech
        </button>
      ) : null}

      {/* ── Advanced settings (silence + sensitivity + text fallback toggle) ──────── */}
      <details
        className="rounded-xl border border-white/[0.06] bg-black/15 px-3 py-1"
        data-testid="oracle-vad-settings"
      >
        <summary className="oracle-details-summary cursor-pointer list-none font-mono text-[11px] uppercase tracking-wider text-chalk/55 [&::-webkit-details-marker]:hidden">
          Advanced · silence + sensitivity
        </summary>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          <label className="flex min-w-0 flex-1 flex-col gap-1 font-mono text-[10px] uppercase tracking-wider text-chalk/50">
            Silence duration
            <select
              data-testid="oracle-silence-duration"
              value={String(speech.silenceDurationMs)}
              onChange={(e) => speech.setSilenceDurationMs(Number(e.target.value))}
              className="min-h-[44px] rounded-lg border border-[color:var(--spirit-border)] bg-black/40 px-2 py-2 text-base text-chalk"
            >
              {SILENCE_PRESETS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex min-w-0 flex-1 flex-col gap-1 font-mono text-[10px] uppercase tracking-wider text-chalk/50">
            Sensitivity
            <select
              data-testid="oracle-sensitivity"
              value={sensitivity}
              onChange={(e) => {
                const choice = SENSITIVITY_PRESETS.find((p) => p.value === e.target.value);
                if (choice) speech.setSilenceThreshold(choice.threshold);
              }}
              className="min-h-[44px] rounded-lg border border-[color:var(--spirit-border)] bg-black/40 px-2 py-2 text-base text-chalk"
            >
              {SENSITIVITY_PRESETS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex min-w-0 flex-1 items-center gap-2 self-end font-mono text-[11px] text-chalk/70">
            <input
              data-testid="oracle-text-fallback-toggle"
              type="checkbox"
              checked={loopMode === "manual-text"}
              onChange={(e) =>
                onLoopModeChange(e.target.checked ? "manual-text" : "hands-free")
              }
              className="h-4 w-4 accent-cyan-400"
            />
            Text fallback only
          </label>
        </div>
      </details>

      <p className="font-mono text-[11px] leading-snug text-chalk/55">{hint}</p>
      {speech.permissionState === "granted" &&
      speech.devices.length === 0 &&
      !speech.devicesEnumerateError ? (
        <p className="font-mono text-[10px] text-chalk/45">
          No labeled mics yet - default capture still works.
        </p>
      ) : null}
    </section>
  );
});
