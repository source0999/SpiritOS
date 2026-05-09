"use client";

// ── OracleVoiceSurface - true hands-free Oracle session (Prompt 10D-E) ───────────
// > Start Session → listen → silence VAD auto-stops → Whisper → Oracle → TTS → relisten.
// > Source, "Finish now" is BACKUP only. If you put it back as the primary CTA the
// > Toxic Grader will eat the regression and Spirit will eat your morning.

import {
  type FormEvent,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { Activity, UserRound } from "lucide-react";

import { ChatActiveModeBadge } from "@/components/chat/ChatActiveModeBadge";
import { ModelProfileSelector } from "@/components/chat/ModelProfileSelector";
import { SpiritActivityPanel } from "@/components/chat/SpiritActivityPanel";
import { SpiritUserProfilePanel } from "@/components/chat/SpiritUserProfilePanel";
import { OracleVoiceControls } from "@/components/oracle/OracleVoiceControls";
import { OracleVoiceStatusCard } from "@/components/oracle/OracleVoiceStatusCard";
import { useOracleSpeechInput } from "@/hooks/useOracleSpeechInput";
import { useSpiritChatTransport } from "@/hooks/useSpiritChatTransport";
import { useSpiritModeRuntime } from "@/hooks/useSpiritModeRuntime";
import { useSpiritThreadRuntime } from "@/hooks/useSpiritThreadRuntime";
import { useSpiritVoiceRuntime, useTtsSpeakGateRef } from "@/hooks/useSpiritVoiceRuntime";
import { useTTS } from "@/hooks/useTTS";
import { useMediaMinWidthLg } from "@/lib/hooks/useMediaMinWidthLg";
import { useMounted } from "@/lib/hooks/useMounted";
import { dedupeUIMessagesById, textFromParts } from "@/lib/chat-utils";
import { appendOracleMemoryEvent, isOracleMemoryEnabled } from "@/lib/oracle/oracle-memory";
import {
  DEFAULT_ORACLE_LOOP_MODE,
  deriveOracleVoiceStatus,
  oracleSessionStatusLabel,
  shouldOracleAutoRestartListening,
  type OracleVoiceLoopMode,
} from "@/lib/oracle/oracle-voice-session";
import { getOracleVisualStateFromSessionStatus } from "@/lib/oracle/oracle-visual-state";
import "@/components/oracle/oracle-visuals.css";
import { OracleOrbSprite } from "@/components/oracle/OracleOrbSprite";
import { OracleSessionTranscript } from "@/components/oracle/OracleSessionTranscript";
import { OracleVoiceVisualizer } from "@/components/oracle/OracleVoiceVisualizer";
import { getModelProfile } from "@/lib/spirit/model-profiles";
import { getSpiritRuntimeSurfaceDisplayLabel } from "@/lib/spirit/spirit-client-runtime-hint";
import {
  appendSpiritActivityEvent,
  type SpiritActivityEvent,
} from "@/lib/spirit/spirit-activity-events";
const ACTIVITY_LS_KEY = "spirit:workspaceActivity:v1";
/** Small delay before relistening after TTS finishes - gives audio device time to settle. */
const ORACLE_RELISTEN_DELAY_MS = 500;

function loadOracleActivitySeed(): SpiritActivityEvent[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(ACTIVITY_LS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    const rows: SpiritActivityEvent[] = [];
    for (const x of parsed) {
      if (!x || typeof x !== "object") continue;
      const o = x as Record<string, unknown>;
      if (typeof o.id !== "string" || typeof o.label !== "string") continue;
      if (typeof o.at !== "number") continue;
      if (
        o.kind !== "message_submitted" &&
        o.kind !== "assistant_finished" &&
        o.kind !== "mode_changed" &&
        o.kind !== "voice_played" &&
        o.kind !== "voice_error" &&
        o.kind !== "workflow_step" &&
        o.kind !== "copy_feedback"
      ) {
        continue;
      }
      rows.push({
        id: o.id,
        at: o.at,
        kind: o.kind,
        label: o.label,
      });
    }
    return rows.slice(-20);
  } catch {
    return [];
  }
}

export function OracleVoiceSurface() {
  const mounted = useMounted();
  const threadRt = useSpiritThreadRuntime({
    enabled: false,
    sidebarFeaturesEnabled: false,
  });
  const persistent = threadRt.persistent;

  const modeRt = useSpiritModeRuntime({
    runtimeSurface: "oracle",
    persistenceEnabled: false,
    threadRuntime: {
      activeModelProfileId: persistent.activeModelProfileId,
      setActiveModelProfile: persistent.setActiveModelProfile,
    },
  });

  const tts = useTTS();
  const ttsRef = useRef(tts);
  useLayoutEffect(() => {
    ttsRef.current = tts;
  }, [tts]);
  const ttsSpeakGateRef = useTtsSpeakGateRef(tts);

  // SSR + first paint must match server ([]) - hydrate from LS after mount only.
  const [workspaceActivity, setWorkspaceActivity] = useState<SpiritActivityEvent[]>(() =>
    loadOracleActivitySeed(),
  );
  const [activityOpen, setActivityOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [modeToast, setModeToast] = useState<string | null>(null);
  const [loopMode, setLoopMode] = useState<OracleVoiceLoopMode>(DEFAULT_ORACLE_LOOP_MODE);
  const [sessionActive, setSessionActive] = useState(false);
  const [sessionStopped, setSessionStopped] = useState(false);
  const [requestingMic, setRequestingMic] = useState(false);
  const [restarting, setRestarting] = useState(false);
  const [fallbackOpen, setFallbackOpen] = useState(false);
  const [fallbackText, setFallbackText] = useState("");
  /** Non-chat STT lines for hallucination debugging - one row per Whisper final. */
  const [micPickupLines, setMicPickupLines] = useState<{ id: string; at: number; text: string }[]>(
    [],
  );

  const sessionActiveRef = useRef(false);
  const loopModeRef = useRef<OracleVoiceLoopMode>(DEFAULT_ORACLE_LOOP_MODE);
  /** Latch - true between assistant finish and TTS-end relisten. */
  const isProcessingTurnRef = useRef(false);
  /** Pending relisten timer cleared by Stop session / errors. */
  const autoRestartTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    sessionActiveRef.current = sessionActive;
  }, [sessionActive]);
  useEffect(() => {
    loopModeRef.current = loopMode;
  }, [loopMode]);

  const forceScrollOnNextMessageRef = useRef(false);
  const shouldStickToBottomRef = useRef(true);

  const pushActivity = useCallback((e: Omit<SpiritActivityEvent, "id" | "at">) => {
    setWorkspaceActivity((prev) => appendSpiritActivityEvent(prev, e));
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(ACTIVITY_LS_KEY, JSON.stringify(workspaceActivity));
    } catch {
      /* ignore */
    }
  }, [workspaceActivity]);

  const transport = useSpiritChatTransport({
    api: "/api/spirit",
    persistence: false,
    persistenceEnabled: false,
    savedChatShell: false,
    workspaceChrome: true,
    attachSpiritBody: true,
    persistent,
    modeRuntime: modeRt,
    activeModelProfileId: modeRt.activeModelProfileId,
    ttsRef,
    ttsSpeakGateRef,
    pushActivity,
    outboundScrollRefs: {
      forceScrollOnNextMessageRef,
      shouldStickToBottomRef,
    },
  });

  const transportRef = useRef(transport);
  useLayoutEffect(() => {
    transportRef.current = transport;
  }, [transport]);

  const voiceRt = useSpiritVoiceRuntime({
    tts,
    activityLoggingShell: true,
    messages: transport.messages,
    assistantSourceProof: transport.assistantSourceProof,
    pushActivity,
  });

  const speech = useOracleSpeechInput({
    silenceThreshold: 0.035,
    silenceDurationMs: 1200,
    minRecordingMs: 700,
    maxRecordingMs: 60_000,
    autoStopOnSilence: true,
  });

  const speechRef = useRef(speech);
  useLayoutEffect(() => {
    speechRef.current = speech;
  }, [speech]);

  const speechClearRef = useRef<() => void>(() => {});
  useLayoutEffect(() => {
    speechClearRef.current = speech.clearTranscript;
  }, [speech.clearTranscript]);

  const submitOracleTranscript = useCallback(
    async (text: string) => {
      const t = text.trim();
      if (!t || transport.isBusy) return;
      tts.setEnabled(true);
      isProcessingTurnRef.current = true;
      await transport.runSpiritOutbound(t);
      speechClearRef.current();
      pushActivity({ kind: "message_submitted", label: "Oracle prompt sent" });
    },
    [tts, transport, pushActivity],
  );

  const isLg = useMediaMinWidthLg();

  const prevModeRef = useRef<string | null>(null);
  useEffect(() => {
    const cur = modeRt.activeModelProfileId;
    if (prevModeRef.current === null) {
      prevModeRef.current = cur;
      return;
    }
    if (prevModeRef.current !== cur) {
      const label = getModelProfile(cur).shortLabel;
      pushActivity({ kind: "mode_changed", label: `Mode → ${label}` });
      setModeToast(`Mode switched to ${label}`);
      window.setTimeout(() => setModeToast(null), 2800);
      prevModeRef.current = cur;
    }
  }, [modeRt.activeModelProfileId, pushActivity]);

  const spiritTransportBanner = useMemo(() => {
    const err = transport.error;
    if (!err) return undefined;
    return err instanceof Error ? err.message : String(err);
  }, [transport.error]);

  const activityVoiceLine = voiceRt.activityVoiceLine;
  const activitySearchLine = useMemo(() => {
    const tc = transport;
    return `Search lane: ${tc.lastSearchStatus}`;
  }, [transport]);

  const webSearchDiagnosticLines = useMemo(() => {
    const tc = transport;
    return [
      `Web search (Researcher): ${tc.webSearchOptOut ? "disabled" : "enabled"}`,
      `Teacher web aids: ${tc.teacherWebSearchEnabled ? "enabled" : "disabled"}`,
    ];
  }, [transport]);

  const oracleVoiceBackendLabel = useMemo(() => {
    const p = tts.state.lastLatency?.provider;
    if (p) return p;
    if (tts.state.voicesSource) return tts.state.voicesSource;
    return "/api/tts";
  }, [tts.state.lastLatency?.provider, tts.state.voicesSource]);

  const oracleSelectedVoiceLabel = useMemo(() => {
    return (
      tts.state.elevenLabsVoiceName?.trim() ||
      tts.state.elevenLabsVoiceId?.trim() ||
      "System default"
    );
  }, [tts.state.elevenLabsVoiceName, tts.state.elevenLabsVoiceId]);

  const speechLabel =
    !mounted
      ? "Checking…"
      : speech.canUseMic
        ? "Whisper backend (/api/stt/transcribe)"
        : speech.captureBlockedHint
          ? "Unavailable (browser context)"
          : "Unsupported";

  const selectedMicLabel = useMemo(() => speech.selectedDeviceLabel, [speech.selectedDeviceLabel]);

  const hearingSpeech =
    speech.isRecording && speech.audioLevel >= speech.silenceThreshold;

  const oracleVoiceStatus = useMemo(
    () =>
      mounted
        ? deriveOracleVoiceStatus({
            inputMode: loopMode,
            recordingSupported: speech.supported,
            capabilityBlocked: !speech.canUseMic,
            requestingMic,
            micPermission:
              speech.permissionState === "unsupported" ? "unsupported" : speech.permissionState,
            isListening: speech.isRecording,
            hearingSpeech,
            silenceDetected: speech.silenceDetected,
            isTranscribing: speech.isTranscribing,
            isBusy: transport.isBusy,
            isPlaying: tts.state.isPlaying,
            queueLength: tts.state.queueLength,
            restarting,
            sessionStopped,
            sessionActive,
            ttsLastError: tts.state.lastError,
            speechLastError: speech.lastError,
            spiritTransportError: spiritTransportBanner,
            lastUserStopAtMs: tts.state.lastUserStopAtMs ?? null,
          })
        : "idle",
    [
      mounted,
      loopMode,
      speech.supported,
      speech.canUseMic,
      requestingMic,
      speech.permissionState,
      speech.isRecording,
      hearingSpeech,
      speech.silenceDetected,
      speech.isTranscribing,
      speech.lastError,
      transport.isBusy,
      tts.state.isPlaying,
      tts.state.queueLength,
      tts.state.lastError,
      tts.state.lastUserStopAtMs,
      restarting,
      sessionStopped,
      sessionActive,
      spiritTransportBanner,
    ],
  );

  const oracleVisualState = useMemo(
    () => getOracleVisualStateFromSessionStatus(oracleVoiceStatus),
    [oracleVoiceStatus],
  );

  const sessionActivityLine = useMemo(
    () => oracleSessionStatusLabel(oracleVoiceStatus),
    [oracleVoiceStatus],
  );

  const showVisualizerMeter =
    mounted &&
    loopMode !== "manual-text" &&
    (oracleVisualState === "listening" ||
      oracleVisualState === "processing" ||
      oracleVisualState === "speaking");

  const clearAutoRestartTimer = useCallback(() => {
    if (autoRestartTimerRef.current != null) {
      clearTimeout(autoRestartTimerRef.current);
      autoRestartTimerRef.current = null;
    }
    setRestarting(false);
  }, []);

  // Guards read from refs so this callback stays stable - unstable identity was nuking the
  // relisten setTimeout via effect cleanups every time isBusy / TTS blinked (hands-free death spiral).
  const beginListening = useCallback(async () => {
    const s = speechRef.current;
    const tc = transportRef.current;
    const ttsSt = ttsRef.current.state;
    if (!s.canUseMic) return;
    if (s.permissionState !== "granted") {
      const ok = await s.requestPermission();
      if (!ok) return;
    }
    if (s.isRecording || s.isTranscribing) return;
    if (tc.isBusy || ttsSt.isPlaying || ttsSt.queueLength > 0) return;
    await s.startRecording();
  }, []);

  const startSession = useCallback(async () => {
    if (loopMode === "manual-text") return;
    const s = speechRef.current;
    if (!s.canUseMic) return;
    setSessionStopped(false);
    setRequestingMic(true);
    try {
      tts.setEnabled(true);
      // iOS / WebKit: AudioContext.resume + first decode must chain from the Start session tap  - 
      // do NOT await mic permission first or the activation is gone by the time TTS runs.
      await tts.ensureAudioUnlocked();
      if (s.permissionState !== "granted") {
        const ok = await s.requestPermission();
        if (!ok) return;
      }
      sessionActiveRef.current = true;
      setSessionActive(true);
      isProcessingTurnRef.current = false;
      await beginListening();
    } finally {
      setRequestingMic(false);
    }
  }, [loopMode, tts, beginListening]);

  const stopSession = useCallback(() => {
    sessionActiveRef.current = false;
    isProcessingTurnRef.current = false;
    setSessionActive(false);
    setSessionStopped(true);
    clearAutoRestartTimer();
    speechRef.current.cancelRecording();
    tts.stop();
    pushActivity({ kind: "workflow_step", label: "Oracle session stopped" });
  }, [tts, pushActivity, clearAutoRestartTimer]);

  const finishThought = useCallback(async () => {
    if (loopMode === "manual-text") return;
    const s = speechRef.current;
    // Idempotent guard at hook-level too - this is just for the manual button.
    const text = await s.stopRecordingAndTranscribe();
    if (!text.trim()) {
      // Empty transcript - go back to listening if session is still active, no submit.
      if (sessionActiveRef.current && loopMode === "hands-free") {
        await beginListening();
      }
      return;
    }
    await submitOracleTranscript(text);
  }, [loopMode, submitOracleTranscript, beginListening]);

  // ── Hands-free silence auto-submit: when stopRecordingAndTranscribe resolves
  // ── via the silence VAD, we need to send the resulting transcript.
  // We defer to a microtask so the effect's render cycle finishes before the
  // transport setState chain begins - keeps React's "no setState in effects"
  // lint happy and avoids cascading renders.
  const lastTranscriptRef = useRef<string>("");
  useEffect(() => {
    const cur = speech.lastTranscript;
    if (!cur || cur === lastTranscriptRef.current) return;
    lastTranscriptRef.current = cur;
    if (!sessionActiveRef.current) return;
    if (loopModeRef.current === "manual-text") return;
    if (transport.isBusy) return;
    const wasPTT = loopModeRef.current === "push-to-talk";
    queueMicrotask(() => {
      if (!sessionActiveRef.current) return;
      void submitOracleTranscript(cur);
      if (wasPTT) {
        sessionActiveRef.current = false;
        setSessionActive(false);
      }
    });
  }, [speech.lastTranscript, transport.isBusy, submitOracleTranscript]);

  const lastTranscriptSigRef = useRef<string | undefined>(undefined);
  // ── Append each Whisper final to the mic pickup strip (chat UI is hidden on Oracle for now).
  useEffect(() => {
    const cur = speech.lastTranscript;
    if (cur === lastTranscriptSigRef.current) return;
    lastTranscriptSigRef.current = cur;
    const t = cur.trim();
    if (!t) return;
    queueMicrotask(() => {
      setMicPickupLines((prev) => [
        ...prev.slice(-24),
        { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, at: Date.now(), text: t },
      ]);
    });
  }, [speech.lastTranscript]);

  // ── If an empty transcript came back AND the session is alive, restart listening.
  const lastRecordingDurRef = useRef<number | null>(null);
  useEffect(() => {
    const dur = speech.lastRecordingDurationMs;
    if (dur == null || dur === lastRecordingDurRef.current) return;
    lastRecordingDurRef.current = dur;
    if (!sessionActiveRef.current) return;
    if (loopModeRef.current !== "hands-free") return;
    // Only chase relisten if Whisper genuinely returned nothing (no transcript change came in).
    if (speech.lastTranscript.trim()) return;
    if (transport.isBusy) return;
    if (tts.state.isPlaying || tts.state.queueLength > 0) return;
    if (speech.isRecording || speech.isTranscribing) return;
    if (speech.lastError) return;
    void beginListening();
  }, [
    speech.lastRecordingDurationMs,
    speech.lastTranscript,
    speech.isRecording,
    speech.isTranscribing,
    speech.lastError,
    transport.isBusy,
    tts.state.isPlaying,
    tts.state.queueLength,
    beginListening,
  ]);

  const displayMessages = useMemo(
    () => dedupeUIMessagesById(transport.messages),
    [transport.messages],
  );

  const latestMicPickup =
    micPickupLines.length > 0 ? micPickupLines[micPickupLines.length - 1]!.text : "";

  // ── Speak assistant replies + arm relisten latch.
  const spokenAssistantIdsRef = useRef(new Set<string>());
  useEffect(() => {
    if (transport.isBusy) return;
    const last = displayMessages[displayMessages.length - 1];
    if (!last || last.role !== "assistant") return;
    if (spokenAssistantIdsRef.current.has(last.id)) return;
    spokenAssistantIdsRef.current.add(last.id);
    if (isOracleMemoryEnabled()) {
      const prev = displayMessages[displayMessages.length - 2];
      const userText = prev?.role === "user" ? textFromParts(prev).trim() : undefined;
      const assistantText = textFromParts(last).trim();
      const summary = (userText ?? assistantText).slice(0, 120);
      if (summary) {
        void appendOracleMemoryEvent({
          summary,
          userText: userText?.slice(0, 500),
          assistantText: assistantText.slice(0, 500) || undefined,
          modelProfileId: modeRt.activeModelProfileId,
          source: "oracle-voice-surface",
          runtimeSurface: "oracle",
        });
      }
    }
    tts.setEnabled(true);
    const speakText = voiceRt.assistantSpeakableText(last);
    const trimmed = speakText.trim();
    if (trimmed) {
      void voiceRt.speakAssistantMessage(speakText);
    } else {
      // No spoken output - turn is over, clear processing latch so relisten effect can fire.
      isProcessingTurnRef.current = false;
    }
    pushActivity({ kind: "assistant_finished", label: "Assistant replied (Oracle)" });
  }, [displayMessages, transport.isBusy, voiceRt, tts, pushActivity]);

  // ── Hands-free relisten loop: after TTS finishes, schedule next listen turn.
  useEffect(() => {
    if (!mounted) return;
    if (!sessionActiveRef.current) {
      clearAutoRestartTimer();
      return;
    }
    const ok = shouldOracleAutoRestartListening({
      sessionActive: sessionActiveRef.current,
      inputMode: loopMode,
      isBusy: transport.isBusy,
      isPlaying: tts.state.isPlaying,
      queueLength: tts.state.queueLength,
      isTranscribing: speech.isTranscribing,
      isListening: speech.isRecording,
      micPermission: speech.permissionState,
      capabilityBlocked: !speech.canUseMic,
      spiritTransportError: spiritTransportBanner ?? null,
      ttsLastError: tts.state.lastError ?? null,
      speechLastError: speech.lastError ?? null,
    });
    if (!ok) return;
    if (!isProcessingTurnRef.current) return;

    setRestarting(true);
    autoRestartTimerRef.current = setTimeout(() => {
      autoRestartTimerRef.current = null;
      setRestarting(false);
      if (!sessionActiveRef.current) return;
      // Latch clears here - not before scheduling. Premature clear + effect cleanup was
      // canceling the timer and leaving hands-free permanently deaf.
      isProcessingTurnRef.current = false;
      void beginListening();
    }, ORACLE_RELISTEN_DELAY_MS);
    return () => {
      clearAutoRestartTimer();
    };
  }, [
    mounted,
    loopMode,
    transport.isBusy,
    tts.state.isPlaying,
    tts.state.queueLength,
    tts.state.lastError,
    speech.isTranscribing,
    speech.isRecording,
    speech.permissionState,
    speech.canUseMic,
    speech.lastError,
    spiritTransportBanner,
    beginListening,
    clearAutoRestartTimer,
  ]);

  // ── Hard cleanup on unmount.
  useEffect(() => {
    return () => {
      clearAutoRestartTimer();
    };
  }, [clearAutoRestartTimer]);

  const onFallbackSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      const t = fallbackText.trim();
      if (!t || transport.isBusy) return;
      tts.setEnabled(true);
      await transport.runSpiritOutbound(t);
      setFallbackText("");
      pushActivity({ kind: "message_submitted", label: "Oracle text fallback sent" });
    },
    [fallbackText, transport, tts, pushActivity],
  );

  const onFallbackKey = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        void onFallbackSubmit(e as unknown as FormEvent);
      }
    },
    [onFallbackSubmit],
  );

  return (
    <div className="relative flex min-h-dvh min-h-[100dvh] flex-col overflow-x-hidden bg-[color:var(--spirit-bg)] text-chalk/95 pb-[max(0px,env(safe-area-inset-bottom,0px))]">
      <header className="oracle-chrome-px shrink-0 border-b border-[color:var(--spirit-border)] bg-[color:color-mix(in_oklab,var(--spirit-panel)_42%,transparent)] py-2.5 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-4xl min-w-0 flex-wrap items-center justify-between gap-x-2 gap-y-2">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <p className="font-mono text-[11px] uppercase leading-tight tracking-[0.14em] text-chalk/50 sm:text-[10px] sm:tracking-[0.2em]">
              <span className="text-[color:var(--spirit-accent-strong)]">Spirit</span>
              <span className="text-chalk/35"> · </span>
              <span>Oracle Voice</span>
            </p>
            <span className="max-w-[min(100%,11rem)] truncate rounded-full border border-[color:color-mix(in_oklab,var(--spirit-accent)_35%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_10%,transparent)] px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-wider text-[color:var(--spirit-accent-strong)] sm:max-w-none sm:py-0.5 sm:text-[9px]">
              {sessionActivityLine}
            </span>
          </div>
          <div className="flex min-w-0 max-w-full flex-wrap items-center justify-end gap-1.5">
            <span className="shrink-0 rounded-full border border-white/[0.08] bg-black/25 px-2 py-1 font-mono text-[10px] text-chalk/65 sm:py-0.5 sm:text-[9px]">
              Whisper STT
            </span>
            <span className="max-w-[10rem] truncate rounded-full border border-white/[0.08] bg-black/25 px-2 py-1 font-mono text-[10px] text-chalk/65 sm:max-w-none sm:py-0.5 sm:text-[9px]">
              {loopMode === "hands-free"
                ? "Hands-free"
                : loopMode === "push-to-talk"
                  ? "Push-to-talk"
                  : "Text only"}
            </span>
            <span className="shrink-0 rounded-full border border-white/[0.08] bg-black/25 px-2 py-1 font-mono text-[10px] text-chalk/65 sm:py-0.5 sm:text-[9px]">
              {mounted && speech.capability.isSecureContext === true
                ? "Secure context"
                : mounted && speech.capability.isSecureContext === false
                  ? "Insecure"
                  : "Secure…"}
            </span>
          </div>
        </div>
      </header>

      <div className="oracle-chrome-px shrink-0 border-b border-[color:var(--spirit-border)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_90%,transparent)] py-2 backdrop-blur-md">
        {modeToast ? (
          <div className="mb-2 border-b border-white/[0.06] bg-white/[0.03] px-2 py-1 text-center font-mono text-[10px] text-chalk/65">
            {modeToast}
          </div>
        ) : null}
        <div className="mx-auto flex w-full max-w-4xl min-w-0 flex-col gap-2 lg:flex-row lg:flex-wrap lg:items-center">
          <ChatActiveModeBadge
            className="w-full max-w-[14rem] lg:w-auto"
            profileId={modeRt.activeModelProfileId}
          />
          <div className="min-w-0 sm:max-w-[16rem]">
            <ModelProfileSelector
              value={modeRt.activeModelProfileId}
              onChange={(id) => {
                void modeRt.setActiveModelProfile(id);
              }}
              compact
            />
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <button
              type="button"
              aria-label="Activity"
              onClick={() => {
                setActivityOpen((o) => !o);
                setProfileOpen(false);
              }}
              className="inline-flex h-11 min-h-[44px] w-11 min-w-[44px] touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70 [-webkit-tap-highlight-color:transparent]"
            >
              <Activity className="h-4 w-4" aria-hidden />
            </button>
            <button
              type="button"
              aria-label="Spirit profile"
              onClick={() => {
                setProfileOpen((o) => !o);
                setActivityOpen(false);
              }}
              className="inline-flex h-11 min-h-[44px] w-11 min-w-[44px] touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70 [-webkit-tap-highlight-color:transparent]"
            >
              <UserRound className="h-4 w-4" aria-hidden />
            </button>
          </div>
        </div>
      </div>

      <div className="oracle-chrome-px shrink-0 border-b border-[color:var(--spirit-border)]/80 bg-[color:color-mix(in_oklab,var(--spirit-bg)_88%,transparent)] py-4">
        <div className="mx-auto flex w-full max-w-4xl min-w-0 flex-col items-center gap-3">
          <OracleOrbSprite visualState={oracleVisualState} variant="chamber" />
          <OracleVoiceVisualizer
            state={oracleVisualState}
            audioLevel={showVisualizerMeter ? speech.audioLevel : undefined}
            className="w-full max-w-md"
          />
        </div>
      </div>

      <OracleVoiceControls
        mounted={mounted}
        status={oracleVoiceStatus}
        loopMode={loopMode}
        onLoopModeChange={setLoopMode}
        sessionActive={sessionActive}
        onStartSession={startSession}
        onStopSession={stopSession}
        onFinishThought={finishThought}
        speech={speech}
        ttsState={tts.state}
        onToggleTtsEnabled={tts.toggleEnabled}
        onEnableAudio={tts.ensureAudioUnlocked}
        onStopSpeech={tts.stop}
        onSpeakLatestAssistant={voiceRt.speakLatestAssistant}
        onStartDelayChange={tts.setStartDelayMs}
        onSentenceGapChange={tts.setSentenceGapMs}
        onVoiceSpeedChange={tts.setVoiceSpeed}
        onToggleAutoSpeak={tts.toggleAutoSpeakAssistant}
        onRequestVoiceCatalog={tts.refreshElevenLabsVoices}
        onElevenLabsVoiceChange={(id) => tts.setElevenLabsVoiceFromPicker(id)}
        transportBusy={transport.isBusy}
      />

      <details className="oracle-chrome-px shrink-0 border-b border-[color:var(--spirit-border)] bg-black/15 py-1">
        <summary className="oracle-details-summary cursor-pointer list-none font-mono text-[11px] uppercase tracking-wider text-chalk/50 [&::-webkit-details-marker]:hidden">
          Session telemetry
        </summary>
        <div className="pb-2 pt-1">
          <OracleVoiceStatusCard
            status={oracleVoiceStatus}
            modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
            runtimeLabel={getSpiritRuntimeSurfaceDisplayLabel("oracle")}
            loopModeLabel={
              loopMode === "hands-free"
                ? "Hands-free"
                : loopMode === "push-to-talk"
                  ? "Push-to-talk"
                  : "Text only"
            }
            speechInputLabel={speechLabel}
            micPermissionLabel={
              speech.permissionState === "granted"
                ? "Granted"
                : speech.permissionState === "denied"
                  ? "Denied"
                  : speech.permissionState === "unsupported"
                    ? "Unavailable"
                    : "Needed"
            }
            micLabel={selectedMicLabel}
            secureContextOk={mounted ? speech.capability.isSecureContext ?? false : null}
            audioLevel={speech.audioLevel}
            silenceMs={speech.silenceMs}
            silenceThresholdMs={speech.silenceDurationMs}
            lastTranscript={speech.lastTranscript}
            recordingStartedAt={speech.recordingStartedAt}
            voiceProviderLine={oracleVoiceBackendLabel}
            selectedVoiceLabel={oracleSelectedVoiceLabel}
            lastPlaybackWallMs={tts.state.lastPlaybackWallMs}
            lastError={tts.state.lastError}
            spiritTransportError={spiritTransportBanner}
            speechError={speech.lastError}
            className="mx-0 sm:mx-0 lg:mx-0"
          />
        </div>
      </details>

      <div
        data-testid="oracle-mic-pickup"
        className="oracle-chrome-px scrollbar-hide flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto overflow-x-hidden py-3"
      >
        {transport.error ? (
          <div
            className="mx-auto w-full max-w-3xl rounded-lg border border-rose-500/35 bg-rose-500/10 px-3 py-2 font-mono text-xs text-rose-100"
            role="alert"
          >
            {spiritTransportBanner}
          </div>
        ) : null}
        <OracleSessionTranscript
          className="mx-auto w-full max-w-3xl"
          messages={displayMessages}
          activityLine={sessionActivityLine}
        />
        <details className="mx-auto w-full max-w-3xl rounded-xl border border-[color:var(--spirit-border)] bg-white/[0.03] px-3 py-2 sm:px-4">
          <summary className="oracle-details-summary cursor-pointer list-none font-mono text-[11px] uppercase tracking-wider text-chalk/50 [&::-webkit-details-marker]:hidden">
            Whisper STT raw pickup
          </summary>
          <p className="mt-2 font-mono text-[11px] leading-relaxed text-chalk/55">
            Each Whisper final after an utterance - sanity-check hallucinations here.
          </p>
          <div className="mt-3 min-h-[3.5rem] rounded-lg border border-white/[0.06] bg-black/35 px-3 py-2">
            {latestMicPickup ? (
              <p className="font-mono text-sm leading-snug text-chalk/95">{latestMicPickup}</p>
            ) : (
              <p className="font-mono text-xs text-chalk/40">Nothing captured yet.</p>
            )}
          </div>
          {micPickupLines.length > 1 ? (
            <div className="mt-3 space-y-2">
              <p className="font-mono text-[10px] uppercase tracking-wider text-chalk/45">
                Earlier in this session
              </p>
              <ul className="space-y-2">
                {micPickupLines
                  .slice(0, -1)
                  .slice(-12)
                  .map((row) => (
                    <li
                      key={row.id}
                      className="rounded-lg border border-white/[0.05] bg-black/25 px-3 py-2 font-mono text-xs leading-snug text-chalk/75"
                    >
                      {row.text}
                    </li>
                  ))}
              </ul>
            </div>
          ) : null}
        </details>
      </div>

      <details
        className="oracle-chrome-px shrink-0 border-t border-[color:var(--spirit-border)] bg-black/20 py-2"
        open={fallbackOpen}
        onToggle={(e) => setFallbackOpen((e.target as HTMLDetailsElement).open)}
      >
        <summary className="oracle-details-summary cursor-pointer list-none font-mono text-[12px] uppercase tracking-wider text-chalk/55 sm:text-[11px] [&::-webkit-details-marker]:hidden">
          Text fallback / debug
        </summary>
        <form onSubmit={onFallbackSubmit} className="mt-2 flex flex-col gap-2 pb-[env(safe-area-inset-bottom)]">
          <textarea
            value={fallbackText}
            onChange={(e) => setFallbackText(e.target.value)}
            onKeyDown={onFallbackKey}
            rows={3}
            placeholder="Type if STT is unavailable…"
            disabled={transport.isBusy}
            className="min-h-[88px] w-full resize-y rounded-xl border border-[color:var(--spirit-border)] bg-black/40 px-3 py-2 text-base text-chalk placeholder:text-chalk/35"
          />
          <button
            type="submit"
            disabled={transport.isBusy || !fallbackText.trim()}
            className="inline-flex min-h-[44px] touch-manipulation items-center justify-center rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_14%,transparent)] px-4 font-mono text-xs font-semibold uppercase tracking-wide text-[color:var(--spirit-accent-strong)] disabled:opacity-35"
          >
            Send text
          </button>
        </form>
      </details>

      <SpiritActivityPanel
        open={activityOpen}
        onClose={() => setActivityOpen(false)}
        variant={!mounted ? "sheet" : isLg ? "popover" : "sheet"}
        modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
        runtimeLabel={getSpiritRuntimeSurfaceDisplayLabel("oracle")}
        voiceLabel={activityVoiceLine}
        searchLabel={activitySearchLine}
        memoryLabel="Local profile only"
        researchNote="OpenAI web prefetch via /api/spirit when Researcher web is on"
        webSearchDiagnosticLines={webSearchDiagnosticLines}
        events={workspaceActivity}
      />
      <SpiritUserProfilePanel
        open={profileOpen}
        onClose={() => setProfileOpen(false)}
        variant={!mounted ? "sheet" : isLg ? "popover" : "sheet"}
        activeModelProfileId={modeRt.activeModelProfileId}
      />
    </div>
  );
}
