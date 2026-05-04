"use client";

// ── useOracleSpeechInput — Whisper via MediaRecorder + /api/stt/transcribe ─────────
// > Oracle STT path is server-proxied Whisper — not browser Web Speech.
// > Silence-aware: amplitude meter doubles as a VAD so the user never has to click
// > "Finish thought" in normal hands-free use. Spirit refuses to call this an
// > advanced VAD — it's the simplest amplitude trick that survives hostile rooms.

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import {
  appendOracleVoiceEvent,
  capOracleVoiceEvents,
  createOracleVoiceEvent,
  type OracleSpeechProvider,
  type OracleVoiceSessionEvent,
} from "@/lib/oracle/oracle-voice-session";
import {
  getOracleBrowserCapabilityReport,
  type OracleBrowserCapabilityBlockedReason,
  type OracleBrowserCapabilityReport,
} from "@/lib/oracle/oracle-browser-capabilities";

export const ORACLE_MIC_LS_KEY = "spirit:oracle:selectedMicId";

/** Hard cap per utterance — the user might forget about us. */
export const ORACLE_MAX_RECORDING_MS = 60_000;

/** Default silence detection knobs — tuned for "casual conversation" not dictation. */
export const ORACLE_DEFAULT_SILENCE_THRESHOLD = 0.035;
export const ORACLE_DEFAULT_SILENCE_DURATION_MS = 1200;
export const ORACLE_DEFAULT_MIN_RECORDING_MS = 700;
/** Grace before any auto-stop happens — gives the user time to start talking. */
export const ORACLE_DEFAULT_START_GRACE_MS = 600;
/** Amplitude meter polling cadence (ms). 60Hz audio reads are wasteful for VAD. */
export const ORACLE_AUDIO_LEVEL_INTERVAL_MS = 60;

const DEFAULT_TRANSCRIBE_LANG = "en";

export type OracleAudioInputDevice = {
  deviceId: string;
  label: string;
  groupId?: string;
};

export type UseOracleSpeechInputOptions = {
  /** 0..1 normalized amplitude considered "silence" below. */
  silenceThreshold?: number;
  /** Required continuous silence ms before auto-stop fires. */
  silenceDurationMs?: number;
  /** Hard floor for any auto-stop after `startRecording`. */
  minRecordingMs?: number;
  /** Hard cap per utterance. */
  maxRecordingMs?: number;
  /** When true, recording auto-stops on detected silence. */
  autoStopOnSilence?: boolean;
  onSilenceDetected?: () => void;
  onAutoStop?: (reason: "silence" | "max-duration") => void;
  onAudioLevel?: (level: number) => void;
};

export type UseOracleSpeechInputReturn = {
  provider: OracleSpeechProvider;
  supported: boolean;
  permissionState: "unknown" | "prompt" | "granted" | "denied" | "unsupported";
  devices: OracleAudioInputDevice[];
  devicesEnumerateError: string | null;
  selectedDeviceId: string | null;
  selectedDeviceLabel: string;
  setSelectedDeviceId: (id: string | null) => void;
  isRecording: boolean;
  isTranscribing: boolean;
  isListening: boolean;
  audioLevel: number;
  lastTranscript: string;
  lastError: string | null;
  /** Why capture failed (insecure context, missing API, etc). Null when usable. */
  captureBlockedHint: string | null;
  /** When page is plain http:// on a non-localhost host, same URL with https://. */
  httpsSamePageUrl: string | null;
  /** Capability report — components can show secure-context copy directly from this. */
  capability: OracleBrowserCapabilityReport;
  canUseMic: boolean;
  blockedReason: OracleBrowserCapabilityBlockedReason;
  capabilityMessage: string;
  /** True for the brief window between silence detection and the auto-stop firing. */
  silenceDetected: boolean;
  /** Continuous silence ms accumulated this recording. Resets when speech resumes. */
  silenceMs: number;
  recordingStartedAt: number | null;
  lastRecordingDurationMs: number | null;
  autoStopOnSilence: boolean;
  setAutoStopOnSilence: (value: boolean) => void;
  silenceThreshold: number;
  setSilenceThreshold: (value: number) => void;
  silenceDurationMs: number;
  setSilenceDurationMs: (value: number) => void;
  requestPermission: () => Promise<boolean>;
  refreshDevices: () => Promise<void>;
  startRecording: () => Promise<void>;
  stopRecordingAndTranscribe: () => Promise<string>;
  cancelRecording: () => void;
  clearTranscript: () => void;
};

function readLsMic(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const v = window.localStorage.getItem(ORACLE_MIC_LS_KEY);
    return v?.trim() ? v.trim() : null;
  } catch {
    return null;
  }
}

function writeLsMic(id: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (id?.trim()) window.localStorage.setItem(ORACLE_MIC_LS_KEY, id.trim());
    else window.localStorage.removeItem(ORACLE_MIC_LS_KEY);
  } catch {
    /* private mode */
  }
}

function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  const types = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
  ];
  for (const t of types) {
    try {
      if (MediaRecorder.isTypeSupported(t)) return t;
    } catch {
      /* ignore */
    }
  }
  return undefined;
}

export function useOracleSpeechInput(
  options: UseOracleSpeechInputOptions = {},
): UseOracleSpeechInputReturn {
  const [mounted, setMounted] = useState(false);

  const [autoStopOnSilence, setAutoStopOnSilenceState] = useState<boolean>(
    options.autoStopOnSilence ?? true,
  );
  const [silenceThreshold, setSilenceThresholdState] = useState<number>(
    options.silenceThreshold ?? ORACLE_DEFAULT_SILENCE_THRESHOLD,
  );
  const [silenceDurationMs, setSilenceDurationMsState] = useState<number>(
    options.silenceDurationMs ?? ORACLE_DEFAULT_SILENCE_DURATION_MS,
  );
  const minRecordingMs = options.minRecordingMs ?? ORACLE_DEFAULT_MIN_RECORDING_MS;
  const maxRecordingMs = options.maxRecordingMs ?? ORACLE_MAX_RECORDING_MS;

  const onSilenceDetectedRef = useRef(options.onSilenceDetected);
  const onAutoStopRef = useRef(options.onAutoStop);
  const onAudioLevelRef = useRef(options.onAudioLevel);
  useEffect(() => {
    onSilenceDetectedRef.current = options.onSilenceDetected;
    onAutoStopRef.current = options.onAutoStop;
    onAudioLevelRef.current = options.onAudioLevel;
  }, [options.onSilenceDetected, options.onAutoStop, options.onAudioLevel]);

  const autoStopRef = useRef(autoStopOnSilence);
  const thresholdRef = useRef(silenceThreshold);
  const silenceDurRef = useRef(silenceDurationMs);
  useEffect(() => {
    autoStopRef.current = autoStopOnSilence;
  }, [autoStopOnSilence]);
  useEffect(() => {
    thresholdRef.current = silenceThreshold;
  }, [silenceThreshold]);
  useEffect(() => {
    silenceDurRef.current = silenceDurationMs;
  }, [silenceDurationMs]);

  const [permissionState, setPermissionState] = useState<
    "unknown" | "prompt" | "granted" | "denied" | "unsupported"
  >("unknown");

  const [devices, setDevices] = useState<OracleAudioInputDevice[]>([]);
  const [devicesEnumerateError, setDevicesEnumerateError] = useState<string | null>(null);
  const [internalSelected, setInternalSelected] = useState<string | null>(null);
  const selectedDeviceId = internalSelected;

  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [lastTranscript, setLastTranscript] = useState("");
  const [lastError, setLastError] = useState<string | null>(null);
  const [silenceDetected, setSilenceDetected] = useState(false);
  const [silenceMs, setSilenceMs] = useState(0);
  const [recordingStartedAt, setRecordingStartedAt] = useState<number | null>(null);
  const [lastRecordingDurationMs, setLastRecordingDurationMs] = useState<number | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const mimeRef = useRef<string | undefined>(undefined);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const meterIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const maxDurationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventsRef = useRef<OracleVoiceSessionEvent[]>([]);
  const recordingStartTsRef = useRef<number | null>(null);
  const lastSpeechTsRef = useRef<number | null>(null);
  /** Last reason for stop — drives onAutoStop callback after the recorder finishes. */
  const stopReasonRef = useRef<"silence" | "max-duration" | "user" | null>(null);
  /** Idempotency latch — silence + Finish-now clicked on top of each other shouldn't double submit. */
  const stopInFlightRef = useRef(false);

  const emit = useCallback((row: Omit<OracleVoiceSessionEvent, "id" | "createdAt">) => {
    const ev = createOracleVoiceEvent(row);
    eventsRef.current = capOracleVoiceEvents(appendOracleVoiceEvent(eventsRef.current, ev));
  }, []);

  useEffect(() => {
    queueMicrotask(() => setMounted(true));
  }, []);

  const capability = useMemo(() => getOracleBrowserCapabilityReport(mounted), [mounted]);

  // Keep permissionState honest about API support after mount. This is a real
  // sync between an external system (browser capability flip) and our state,
  // exactly the pattern React docs allow for setState-in-effect.
  /* eslint-disable react-hooks/set-state-in-effect -- mirrors browser capability into state */
  useEffect(() => {
    if (!mounted) return;
    if (capability.canUseMic) {
      setPermissionState((p) => (p === "unsupported" ? "unknown" : p));
    } else {
      setPermissionState((p) => (p === "granted" || p === "denied" ? p : "unsupported"));
    }
  }, [mounted, capability.canUseMic]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const supported = capability.canUseMic;
  const captureBlockedHint = mounted && !capability.canUseMic ? capability.userMessage : null;

  const [httpsSamePageUrl, setHttpsSamePageUrl] = useState<string | null>(null);
  useEffect(() => {
    if (typeof window === "undefined") return;
    let next: string | null = null;
    if (!window.isSecureContext && window.location.protocol === "http:") {
      const { host, pathname, search, hash } = window.location;
      next = `https://${host}${pathname}${search}${hash}`;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect -- mount-only URL helper for insecure LAN http://
    setHttpsSamePageUrl(next);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- mount-only LS read
    setInternalSelected(readLsMic());
  }, []);

  const selectedDeviceLabel = (() => {
    if (!selectedDeviceId) return "Default microphone";
    const row = devices.find((d) => d.deviceId === selectedDeviceId);
    return row?.label ?? selectedDeviceId.slice(0, 14);
  })();

  const setSelectedDeviceId = useCallback(
    (id: string | null) => {
      setInternalSelected(id);
      writeLsMic(id);
      emit({
        type: "device_selected",
        label: id ? "Microphone selected" : "Default microphone",
        detail: id ?? undefined,
      });
    },
    [emit],
  );

  const refreshDevices = useCallback(async () => {
    setDevicesEnumerateError(null);
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.enumerateDevices) {
      setDevices([]);
      setDevicesEnumerateError("Could not load microphones");
      return;
    }
    try {
      const raw = await navigator.mediaDevices.enumerateDevices();
      const inputs: OracleAudioInputDevice[] = [];
      for (const d of raw) {
        if (d.kind !== "audioinput") continue;
        inputs.push({
          deviceId: d.deviceId,
          label: d.label?.trim() ? d.label : `Microphone (${d.deviceId.slice(0, 6)}…)`,
          groupId: d.groupId || undefined,
        });
      }
      setDevices(inputs);
    } catch (e) {
      setDevices([]);
      setDevicesEnumerateError(e instanceof Error ? e.message : "Could not load microphones");
    }
  }, []);

  const stopLevelMeter = useCallback(() => {
    if (meterIntervalRef.current != null) {
      clearInterval(meterIntervalRef.current);
      meterIntervalRef.current = null;
    }
    setAudioLevel(0);
    setSilenceMs(0);
    setSilenceDetected(false);
    analyserRef.current = null;
    try {
      void audioCtxRef.current?.close();
    } catch {
      /* ignore */
    }
    audioCtxRef.current = null;
  }, []);

  const stopMediaTracks = useCallback(() => {
    const s = streamRef.current;
    streamRef.current = null;
    if (!s) return;
    for (const t of s.getTracks()) {
      try {
        t.stop();
      } catch {
        /* ignore */
      }
    }
  }, []);

  const clearMaxTimer = useCallback(() => {
    if (maxDurationTimerRef.current != null) {
      clearTimeout(maxDurationTimerRef.current);
      maxDurationTimerRef.current = null;
    }
  }, []);

  const requestPermission = useCallback(async (): Promise<boolean> => {
    setLastError(null);
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setPermissionState("unsupported");
      emit({ type: "error", label: "getUserMedia unavailable" });
      return false;
    }
    try {
      const constraints: MediaStreamConstraints = {
        audio: internalSelected ? { deviceId: { exact: internalSelected } } : true,
      };
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (e) {
        const name = e instanceof DOMException ? e.name : "";
        if (name === "NotFoundError" || name === "OverconstrainedError") {
          setLastError("Selected microphone unavailable — using default.");
          stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        } else {
          throw e;
        }
      }
      for (const t of stream.getTracks()) t.stop();
      setPermissionState("granted");
      emit({ type: "permission_granted", label: "Microphone unlocked" });
      await refreshDevices();
      return true;
    } catch (e) {
      const name = e instanceof DOMException ? e.name : "";
      if (name === "NotAllowedError" || name === "PermissionDeniedError") {
        setPermissionState("denied");
        emit({ type: "permission_denied", label: "Microphone permission denied" });
      } else {
        const msg = e instanceof Error ? e.message : String(e);
        setLastError(msg);
        emit({ type: "error", label: `Mic error: ${msg}` });
      }
      return false;
    }
  }, [emit, refreshDevices, internalSelected]);

  // ── Forward decl so the meter can call into stopRecordingAndTranscribe ───────
  const stopRecordingAndTranscribeRef = useRef<() => Promise<string>>(async () => "");

  const startLevelMeter = useCallback(
    (stream: MediaStream) => {
      stopLevelMeter();
      try {
        const Ctx =
          window.AudioContext ||
          (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        if (!Ctx) return;
        const ctx = new Ctx();
        audioCtxRef.current = ctx;
        const src = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        src.connect(analyser);
        analyserRef.current = analyser;
        const data = new Uint8Array(analyser.frequencyBinCount);

        let lastTickAt = Date.now();
        const tick = () => {
          const a = analyserRef.current;
          if (!a) return;
          a.getByteFrequencyData(data);
          let sum = 0;
          for (let i = 0; i < data.length; i++) sum += data[i]!;
          const avg = sum / (data.length * 255);
          const level = Math.min(1, avg * 2.5);
          setAudioLevel(level);
          onAudioLevelRef.current?.(level);

          const now = Date.now();
          const dt = now - lastTickAt;
          lastTickAt = now;
          const startedAt = recordingStartTsRef.current;
          if (startedAt == null) return;
          const sinceStart = now - startedAt;

          if (level >= thresholdRef.current) {
            lastSpeechTsRef.current = now;
            setSilenceMs(0);
            setSilenceDetected(false);
            return;
          }

          // Below threshold — accrue silence.
          // Don't accrue during the start grace window — gives the user time to begin speaking.
          if (sinceStart < ORACLE_DEFAULT_START_GRACE_MS) return;
          // Hold off auto-stop until we've heard at least one frame of speech this turn,
          // so a totally silent room doesn't get auto-finished after 1.2s of dead air.
          const everSpoke = lastSpeechTsRef.current != null;
          setSilenceMs((prev) => prev + dt);

          if (!autoStopRef.current) return;
          if (sinceStart < minRecordingMs) return;
          if (!everSpoke) return;

          // Refs are the live source — `silenceMs` state lags by a tick.
          const lastSpeechAt = lastSpeechTsRef.current ?? startedAt;
          const silenceSpan = now - lastSpeechAt;
          if (silenceSpan >= silenceDurRef.current) {
            setSilenceDetected(true);
            onSilenceDetectedRef.current?.();
            stopReasonRef.current = "silence";
            void stopRecordingAndTranscribeRef.current();
          }
        };

        meterIntervalRef.current = setInterval(tick, ORACLE_AUDIO_LEVEL_INTERVAL_MS);
      } catch {
        setAudioLevel(0);
      }
    },
    [stopLevelMeter, minRecordingMs],
  );

  const cancelRecording = useCallback(() => {
    clearMaxTimer();
    const rec = recorderRef.current;
    recorderRef.current = null;
    chunksRef.current = [];
    stopReasonRef.current = "user";
    if (rec && rec.state !== "inactive") {
      try {
        rec.stop();
      } catch {
        /* ignore */
      }
    }
    stopLevelMeter();
    stopMediaTracks();
    setIsRecording(false);
    setRecordingStartedAt(null);
    recordingStartTsRef.current = null;
    lastSpeechTsRef.current = null;
    stopInFlightRef.current = false;
    emit({ type: "listening_stopped", label: "Recording cancelled" });
  }, [clearMaxTimer, emit, stopLevelMeter, stopMediaTracks]);

  const clearTranscript = useCallback(() => {
    setLastTranscript("");
  }, []);

  const stopRecordingAndTranscribe = useCallback(async (): Promise<string> => {
    // Idempotent: silence VAD and the user's "Finish now" click can race — only one wins.
    if (stopInFlightRef.current) return "";
    stopInFlightRef.current = true;

    clearMaxTimer();
    const rec = recorderRef.current;
    if (!rec || rec.state === "inactive") {
      stopLevelMeter();
      stopMediaTracks();
      setIsRecording(false);
      setRecordingStartedAt(null);
      recordingStartTsRef.current = null;
      stopInFlightRef.current = false;
      return "";
    }

    const startedAt = recordingStartTsRef.current;
    if (stopReasonRef.current === null) stopReasonRef.current = "user";
    const reasonForCallback = stopReasonRef.current;

    return await new Promise<string>((resolve) => {
      rec.onstop = () => {
        stopLevelMeter();
        stopMediaTracks();
        setIsRecording(false);
        setRecordingStartedAt(null);
        const finishedAt = Date.now();
        const duration = startedAt ? finishedAt - startedAt : null;
        setLastRecordingDurationMs(duration);
        recordingStartTsRef.current = null;
        const mime = mimeRef.current || rec.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: mime });
        chunksRef.current = [];
        if (reasonForCallback === "silence" || reasonForCallback === "max-duration") {
          onAutoStopRef.current?.(reasonForCallback);
        }
        void (async () => {
          try {
            if (blob.size < 32) {
              setLastError("No speech captured");
              emit({ type: "error", label: "Empty recording" });
              resolve("");
              return;
            }
            setIsTranscribing(true);
            try {
              const fd = new FormData();
              fd.append("audio", blob, `oracle.${mime.includes("webm") ? "webm" : "audio"}`);
              fd.append("language", DEFAULT_TRANSCRIBE_LANG);
              const res = await fetch("/api/stt/transcribe", {
                method: "POST",
                body: fd,
              });
              let json: {
                ok?: boolean;
                text?: string;
                detail?: string;
              };
              try {
                json = (await res.json()) as typeof json;
              } catch {
                setLastError("Invalid STT response");
                resolve("");
                return;
              }
              if (!res.ok || !json.ok) {
                const d = json.detail || `STT ${res.status}`;
                setLastError(d);
                emit({ type: "error", label: d });
                resolve("");
                return;
              }
              const text = typeof json.text === "string" ? json.text.trim() : "";
              setLastTranscript(text);
              if (!text) {
                setLastError("No speech detected");
              } else {
                setLastError(null);
                emit({
                  type: "transcript_ready",
                  label: "Transcript",
                  detail: text.slice(0, 120),
                });
              }
              resolve(text);
            } catch (e) {
              const msg = e instanceof Error ? e.message : String(e);
              setLastError(msg);
              resolve("");
            } finally {
              setIsTranscribing(false);
            }
          } finally {
            stopReasonRef.current = null;
            stopInFlightRef.current = false;
          }
        })();
      };
      try {
        rec.stop();
      } catch {
        stopLevelMeter();
        stopMediaTracks();
        setIsRecording(false);
        setRecordingStartedAt(null);
        recordingStartTsRef.current = null;
        stopReasonRef.current = null;
        stopInFlightRef.current = false;
        resolve("");
      }
    });
  }, [clearMaxTimer, emit, stopLevelMeter, stopMediaTracks]);

  useLayoutEffect(() => {
    stopRecordingAndTranscribeRef.current = stopRecordingAndTranscribe;
  }, [stopRecordingAndTranscribe]);

  const startRecording = useCallback(async () => {
    if (!supported) {
      setLastError(captureBlockedHint || "Recording not supported in this browser");
      return;
    }
    if (permissionState !== "granted") {
      const ok = await requestPermission();
      if (!ok) return;
    }

    cancelRecording();
    setLastError(null);
    chunksRef.current = [];
    mimeRef.current = pickMimeType();
    stopReasonRef.current = null;
    stopInFlightRef.current = false;

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: internalSelected ? { deviceId: { exact: internalSelected } } : true,
      });
    } catch (e) {
      const name = e instanceof DOMException ? e.name : "";
      if (name === "NotFoundError" || name === "OverconstrainedError") {
        setLastError("Selected mic failed — using default capture.");
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } else {
        const msg = e instanceof Error ? e.message : String(e);
        setLastError(msg);
        emit({ type: "error", label: msg });
        return;
      }
    }

    streamRef.current = stream;
    startLevelMeter(stream);

    const opts: MediaRecorderOptions = {};
    if (mimeRef.current) opts.mimeType = mimeRef.current;
    let rec: MediaRecorder;
    try {
      rec = new MediaRecorder(stream, opts);
    } catch {
      rec = new MediaRecorder(stream);
    }
    recorderRef.current = rec;

    rec.ondataavailable = (ev) => {
      if (ev.data.size > 0) chunksRef.current.push(ev.data);
    };

    rec.onerror = () => {
      setLastError("MediaRecorder error");
    };

    rec.start(250);
    const startedAt = Date.now();
    recordingStartTsRef.current = startedAt;
    lastSpeechTsRef.current = null;
    setRecordingStartedAt(startedAt);
    setSilenceMs(0);
    setSilenceDetected(false);
    setIsRecording(true);
    emit({ type: "listening_started", label: "Recording" });

    clearMaxTimer();
    maxDurationTimerRef.current = setTimeout(() => {
      maxDurationTimerRef.current = null;
      stopReasonRef.current = "max-duration";
      void stopRecordingAndTranscribeRef.current();
    }, maxRecordingMs);
  }, [
    supported,
    captureBlockedHint,
    permissionState,
    requestPermission,
    cancelRecording,
    internalSelected,
    emit,
    startLevelMeter,
    clearMaxTimer,
    maxRecordingMs,
  ]);

  useEffect(() => {
    return () => {
      clearMaxTimer();
      cancelRecording();
    };
  }, [clearMaxTimer, cancelRecording]);

  const provider: OracleSpeechProvider = supported ? "whisper-backend" : "unsupported";

  const setAutoStopOnSilence = useCallback((value: boolean) => {
    setAutoStopOnSilenceState(value);
  }, []);
  const setSilenceThreshold = useCallback((value: number) => {
    if (!Number.isFinite(value)) return;
    const v = Math.max(0, Math.min(1, value));
    setSilenceThresholdState(v);
  }, []);
  const setSilenceDurationMs = useCallback((value: number) => {
    if (!Number.isFinite(value)) return;
    setSilenceDurationMsState(Math.max(200, Math.round(value)));
  }, []);

  return {
    provider,
    supported,
    permissionState,
    devices,
    devicesEnumerateError,
    selectedDeviceId,
    selectedDeviceLabel,
    setSelectedDeviceId,
    isRecording,
    isTranscribing,
    isListening: isRecording,
    audioLevel,
    lastTranscript,
    lastError,
    captureBlockedHint,
    httpsSamePageUrl,
    capability,
    canUseMic: capability.canUseMic,
    blockedReason: capability.blockedReason,
    capabilityMessage: capability.userMessage,
    silenceDetected,
    silenceMs,
    recordingStartedAt,
    lastRecordingDurationMs,
    autoStopOnSilence,
    setAutoStopOnSilence,
    silenceThreshold,
    setSilenceThreshold,
    silenceDurationMs,
    setSilenceDurationMs,
    requestPermission,
    refreshDevices,
    startRecording,
    stopRecordingAndTranscribe,
    cancelRecording,
    clearTranscript,
  };
}
