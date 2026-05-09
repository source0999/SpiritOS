"use client";

// ── OracleVoiceStatusCard - compact session telemetry (hands-free aware) ──────────
import Link from "next/link";

import {
  oracleSessionStatusLabel,
  type OracleVoiceSessionStatus,
} from "@/lib/oracle/oracle-voice-session";
import { cn } from "@/lib/cn";

export type OracleVoiceStatusCardProps = {
  status: OracleVoiceSessionStatus;
  modeLabel: string;
  runtimeLabel: string;
  voiceProviderLine: string;
  selectedVoiceLabel: string;
  /** "Hands-free" / "Push-to-talk" / "Text only". */
  loopModeLabel?: string;
  /** Browser STT vs manual vs unsupported */
  speechInputLabel?: string;
  /** Resolved microphone label */
  micLabel?: string;
  /** "Granted" / "Denied" / "Unavailable" / "Needed" */
  micPermissionLabel?: string;
  /** True / false / null when not yet mounted. */
  secureContextOk?: boolean | null;
  audioLevel?: number;
  silenceMs?: number;
  silenceThresholdMs?: number;
  lastTranscript?: string;
  recordingStartedAt?: number | null;
  lastPlaybackWallMs?: number;
  lastError?: string | null;
  /** `/api/spirit` banner - orthogonal to TTS fetch failures. */
  spiritTransportError?: string | null;
  speechError?: string | null;
  className?: string;
};

function formatWallTime(wallMs: number): string {
  try {
    return new Date(wallMs).toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return " - ";
  }
}

export function OracleVoiceStatusCard({
  status,
  modeLabel,
  runtimeLabel,
  voiceProviderLine,
  selectedVoiceLabel,
  loopModeLabel,
  speechInputLabel = " - ",
  micLabel = " - ",
  micPermissionLabel,
  secureContextOk,
  audioLevel,
  silenceMs,
  silenceThresholdMs,
  lastTranscript,
  recordingStartedAt,
  lastPlaybackWallMs,
  lastError,
  spiritTransportError,
  speechError,
  className,
}: OracleVoiceStatusCardProps) {
  const playedClock =
    typeof lastPlaybackWallMs === "number"
      ? formatWallTime(lastPlaybackWallMs)
      : null;
  const recordingClock =
    typeof recordingStartedAt === "number" ? formatWallTime(recordingStartedAt) : null;

  const tone =
    status === "error"
      ? "border-rose-500/35 bg-rose-500/[0.07]"
      : status === "blocked"
        ? "border-rose-500/45 bg-rose-950/30"
        : status === "thinking"
          ? "border-cyan-500/30 bg-cyan-500/[0.06]"
          : status === "speaking"
            ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] bg-white/[0.04]"
            : status === "stopped"
              ? "border-amber-500/30 bg-amber-500/[0.06]"
              : status === "listening" ||
                  status === "hearing-speech" ||
                  status === "silence-detected" ||
                  status === "transcribing"
                ? "border-violet-500/30 bg-violet-500/[0.06]"
                : status === "permission-needed"
                  ? "border-amber-500/25 bg-amber-500/[0.05]"
                  : status === "unsupported"
                    ? "border-rose-400/25 bg-rose-950/20"
                    : "border-[color:var(--spirit-border)] bg-black/[0.12]";

  const audioPct =
    typeof audioLevel === "number" ? `${Math.round(Math.min(1, Math.max(0, audioLevel)) * 100)}%` : null;

  const silenceLine =
    typeof silenceMs === "number" && typeof silenceThresholdMs === "number"
      ? `${silenceMs}ms / ${silenceThresholdMs}ms`
      : null;

  const transcriptShort = lastTranscript?.trim()
    ? lastTranscript.trim().slice(0, 140)
    : null;

  const secureLabel =
    secureContextOk === null || secureContextOk === undefined
      ? "Checking…"
      : secureContextOk
        ? "OK"
        : "Blocked";

  return (
    <section
      data-testid="oracle-voice-status-card"
      aria-label="Oracle voice status"
      className={cn(
        "mx-2 rounded-xl border px-3 py-2.5 font-mono text-[11px] leading-snug text-chalk/85 sm:mx-5 lg:mx-6",
        tone,
        className,
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.06] pb-2">
        <span className="text-[10px] uppercase tracking-[0.2em] text-chalk/55">Oracle session</span>
        <span className="rounded-full border border-emerald-500/35 bg-emerald-500/[0.07] px-2 py-0.5 text-[9px] uppercase tracking-wider text-emerald-300/95">
          Hands-free MVP
        </span>
      </div>
      <dl className="mt-2 grid gap-y-1.5 text-[11px] sm:grid-cols-2 sm:gap-x-4">
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-chalk/45">Runtime</dt>
          <dd className="text-[color:var(--spirit-accent-strong)]">{runtimeLabel}</dd>
        </div>
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-chalk/45">Mode</dt>
          <dd className="text-chalk/90">{modeLabel}</dd>
        </div>
        {loopModeLabel ? (
          <div className="flex flex-wrap gap-x-2">
            <dt className="text-chalk/45">Loop</dt>
            <dd className="text-chalk/90">{loopModeLabel}</dd>
          </div>
        ) : null}
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-chalk/45">Status</dt>
          <dd className="text-chalk">{oracleSessionStatusLabel(status)}</dd>
        </div>
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-chalk/45">Mic permission</dt>
          <dd className="min-w-0 truncate">{micPermissionLabel ?? "-"}</dd>
        </div>
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-chalk/45">Mic</dt>
          <dd className="min-w-0 truncate">{micLabel}</dd>
        </div>
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-chalk/45">Input</dt>
          <dd className="min-w-0 truncate">{speechInputLabel}</dd>
        </div>
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-chalk/45">Secure context</dt>
          <dd
            className={cn(
              "min-w-0 truncate",
              secureContextOk === false ? "text-rose-300/95" : "text-chalk/85",
            )}
          >
            {secureLabel}
          </dd>
        </div>
        {audioPct ? (
          <div className="flex flex-wrap gap-x-2">
            <dt className="text-chalk/45">Audio level</dt>
            <dd className="tabular-nums">{audioPct}</dd>
          </div>
        ) : null}
        {silenceLine ? (
          <div className="flex flex-wrap gap-x-2">
            <dt className="text-chalk/45">Silence</dt>
            <dd className="tabular-nums">{silenceLine}</dd>
          </div>
        ) : null}
        <div className="flex flex-wrap gap-x-2">
          <dt className="text-chalk/45">Voice backend</dt>
          <dd className="min-w-0 truncate">{voiceProviderLine}</dd>
        </div>
        <div className="flex flex-wrap gap-x-2 sm:col-span-2">
          <dt className="text-chalk/45">Voice</dt>
          <dd className="min-w-0 flex-1 truncate">{selectedVoiceLabel}</dd>
        </div>
        {transcriptShort ? (
          <div className="flex flex-wrap gap-x-2 sm:col-span-2">
            <dt className="text-chalk/45">Last transcript</dt>
            <dd className="min-w-0 flex-1 break-words text-chalk/85">{transcriptShort}</dd>
          </div>
        ) : null}
        {recordingClock ? (
          <div className="flex flex-wrap gap-x-2">
            <dt className="text-chalk/45">Recording started</dt>
            <dd>{recordingClock}</dd>
          </div>
        ) : null}
        {playedClock ? (
          <div className="flex flex-wrap gap-x-2">
            <dt className="text-chalk/45">Last audio (local)</dt>
            <dd>{playedClock}</dd>
          </div>
        ) : null}
        {lastError?.trim() || spiritTransportError?.trim() || speechError?.trim() ? (
          <div className="sm:col-span-2">
            <dt className="text-chalk/45">Last error</dt>
            <dd className="mt-0.5 space-y-1 text-rose-300/95">
              {spiritTransportError?.trim() ? (
                <p className="font-mono text-[10px] leading-snug">{spiritTransportError.trim()}</p>
              ) : null}
              {speechError?.trim() ? (
                <p className="font-mono text-[10px] leading-snug">STT: {speechError.trim()}</p>
              ) : null}
              {lastError?.trim() ? (
                <p className="font-mono text-[10px] leading-snug">TTS: {lastError.trim()}</p>
              ) : null}
            </dd>
          </div>
        ) : null}
      </dl>
      <div className="mt-2 border-t border-white/[0.06] pt-2 text-[10px] text-chalk/45">
        <Link
          href="/oracle"
          className="text-[color:var(--spirit-accent-strong)] underline underline-offset-4 hover:brightness-110"
        >
          Oracle voice session
        </Link>
        <span className="text-chalk/35"> · ephemeral · no saved threads</span>
      </div>
    </section>
  );
}
