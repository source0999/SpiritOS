// ── Oracle Voice session - UI state machine (no Dexie, no server sync) ────────────
// > Prompt 10D-E: hands-free loop is the default - push-to-talk demoted to a knob,
// > silence VAD picks the moment we hand mic audio to Whisper, and TTS owns
// > "speaking" exclusively. If a status feels wrong in the UI, it's almost always
// > because someone forgot one of the priority rules in deriveOracleVoiceStatus.

export type OracleVoiceSessionStatus =
  | "idle"
  | "blocked"
  | "requesting-mic"
  | "permission-needed"
  | "ready"
  | "listening"
  | "hearing-speech"
  | "silence-detected"
  | "transcribing"
  | "thinking"
  | "speaking"
  | "restarting"
  | "stopped"
  | "unsupported"
  | "error";

/** Hands-free is the default loop mode for /oracle. Push-to-talk + manual stay as knobs. */
export type OracleVoiceLoopMode = "hands-free" | "push-to-talk" | "manual-text";

/** @deprecated keep until callers migrate - same shape as `hands-free` historically. */
export type OracleVoiceInputMode = OracleVoiceLoopMode;

/** Default loop mode for new sessions. */
export const DEFAULT_ORACLE_LOOP_MODE: OracleVoiceLoopMode = "hands-free";

export type OracleSpeechProvider =
  | "whisper-backend"
  | "browser-speech-recognition"
  | "manual-text"
  | "unsupported";

export type OracleVoiceSessionEventType =
  | "session_ready"
  | "session_started"
  | "session_stopped"
  | "permission_requested"
  | "permission_granted"
  | "permission_denied"
  | "device_selected"
  | "listening_started"
  | "listening_stopped"
  | "silence_detected"
  | "auto_stopped"
  | "transcript_ready"
  | "message_submitted"
  | "assistant_finished"
  | "speech_started"
  | "speech_stopped"
  | "speech_error"
  | "mode_changed"
  | "provider_unsupported"
  | "loop_restart"
  | "error";

export type OracleVoiceSessionEvent = {
  id: string;
  type: OracleVoiceSessionEventType;
  label: string;
  detail?: string;
  createdAt: number;
};

const EVENT_CAP = 80;

function randomId(): string {
  try {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
      return crypto.randomUUID();
    }
  } catch {
    /* ignore */
  }
  return `evt_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export function createOracleVoiceEvent(
  input: Omit<OracleVoiceSessionEvent, "id" | "createdAt">,
): OracleVoiceSessionEvent {
  return {
    id: randomId(),
    createdAt: Date.now(),
    ...input,
  };
}

export function appendOracleVoiceEvent(
  prev: OracleVoiceSessionEvent[],
  next: OracleVoiceSessionEvent,
): OracleVoiceSessionEvent[] {
  return [...prev, next];
}

export function capOracleVoiceEvents(
  rows: OracleVoiceSessionEvent[],
  cap = EVENT_CAP,
): OracleVoiceSessionEvent[] {
  if (rows.length <= cap) return rows;
  return rows.slice(rows.length - cap);
}

export type MicPermissionState = "unknown" | "prompt" | "granted" | "denied" | "unsupported";

export type DeriveOracleVoiceStatusInput = {
  inputMode: OracleVoiceLoopMode;
  /** getUserMedia + MediaRecorder available */
  recordingSupported: boolean;
  /** True when capability check says mic cannot be used (insecure ctx, missing API). */
  capabilityBlocked?: boolean;
  /** User tapped Start session; waiting on getUserMedia */
  requestingMic: boolean;
  micPermission: MicPermissionState;
  isListening: boolean;
  /** Recording AND amplitude above threshold = "hearing-speech". */
  hearingSpeech?: boolean;
  /** Silence threshold reached, stop+transcribe pending. */
  silenceDetected?: boolean;
  isTranscribing: boolean;
  isBusy: boolean;
  isPlaying: boolean;
  queueLength: number;
  /** True for the small grace window between TTS finishing and the next listen turn. */
  restarting?: boolean;
  /** True when user has explicitly stopped the session. Latches "stopped" until session restart. */
  sessionStopped?: boolean;
  /** True when a hands-free session is currently in progress. */
  sessionActive?: boolean;
  ttsLastError?: string | null;
  speechLastError?: string | null;
  spiritTransportError?: string | null;
  lastUserStopAtMs?: number | null;
  nowMs?: number;
  stoppedWindowMs?: number;
};

/** Maps machine status to short human copy for hints + status card */
export function oracleSessionStatusLabel(status: OracleVoiceSessionStatus): string {
  switch (status) {
    case "idle":
      return "Idle";
    case "blocked":
      return "Blocked";
    case "requesting-mic":
      return "Requesting mic";
    case "permission-needed":
      return "Permission needed";
    case "ready":
      return "Ready";
    case "listening":
      return "Listening";
    case "hearing-speech":
      return "Hearing you";
    case "silence-detected":
      return "Silence detected";
    case "transcribing":
      return "Transcribing";
    case "thinking":
      return "Thinking";
    case "speaking":
      return "Speaking";
    case "restarting":
      return "Restarting";
    case "stopped":
      return "Stopped";
    case "unsupported":
      return "Unsupported";
    case "error":
      return "Error";
    default:
      return status;
  }
}

/** Short per-status hint for UI subtitles. */
export function oracleSessionStatusHint(status: OracleVoiceSessionStatus): string {
  switch (status) {
    case "idle":
      return "Tap Start session to begin.";
    case "blocked":
      return "Mic blocked - see secure-context warning.";
    case "requesting-mic":
      return "Asking the browser for microphone access…";
    case "permission-needed":
      return "Grant the browser mic permission to continue.";
    case "ready":
      return "Mic ready - start a session whenever you are.";
    case "listening":
      return "Waiting for speech…";
    case "hearing-speech":
      return "Speak naturally - Oracle stops when you do.";
    case "silence-detected":
      return "Heard the gap - sending to Whisper.";
    case "transcribing":
      return "Transcribing with Whisper…";
    case "thinking":
      return "Oracle is thinking…";
    case "speaking":
      return "Oracle is speaking - listening resumes after.";
    case "restarting":
      return "Returning to listening…";
    case "stopped":
      return "Session stopped. Tap Start session to resume.";
    case "unsupported":
      return "Voice capture isn't available in this browser.";
    case "error":
      return "Something failed - see the status card for details.";
    default:
      return "";
  }
}

/**
 * Priority (highest first):
 *   error → unsupported / blocked → requesting mic → permission needed →
 *   silence-detected → transcribing → thinking → speaking → restarting →
 *   hearing-speech → listening → stopped (latched) → ready → idle.
 */
export function deriveOracleVoiceStatus(input: DeriveOracleVoiceStatusInput): OracleVoiceSessionStatus {
  const now = input.nowMs ?? Date.now();
  const windowMs = input.stoppedWindowMs ?? 3500;

  const voicePath = input.inputMode !== "manual-text";

  if (input.spiritTransportError?.trim()) return "error";
  if (input.ttsLastError?.trim()) return "error";
  if (input.speechLastError?.trim()) return "error";

  if (voicePath && input.capabilityBlocked) return "blocked";
  if (voicePath && input.micPermission === "unsupported") return "unsupported";
  if (voicePath && !input.recordingSupported) return "unsupported";

  if (voicePath && input.requestingMic) return "requesting-mic";

  if (
    voicePath &&
    input.recordingSupported &&
    input.micPermission !== "granted" &&
    input.micPermission !== "unsupported"
  ) {
    return "permission-needed";
  }

  if (input.silenceDetected) return "silence-detected";
  if (input.isTranscribing) return "transcribing";
  if (input.isBusy) return "thinking";
  if (input.isPlaying || input.queueLength > 0) return "speaking";
  if (input.restarting) return "restarting";

  if (input.isListening) {
    return input.hearingSpeech ? "hearing-speech" : "listening";
  }

  // Latched stopped after the user clicked Stop session - until a new session starts.
  if (input.sessionStopped && !input.sessionActive) return "stopped";

  const stoppedAt = input.lastUserStopAtMs;
  if (typeof stoppedAt === "number" && now - stoppedAt >= 0 && now - stoppedAt < windowMs) {
    return "stopped";
  }

  if (voicePath && input.micPermission === "granted" && !input.isListening && !input.isBusy) {
    return "ready";
  }

  if (!voicePath) {
    return input.isBusy ? "thinking" : "idle";
  }

  return "idle";
}

/**
 * Returns true when the hands-free loop should auto-restart listening after
 * the assistant's TTS finishes. We latch on session active + hands-free + no
 * pending error / busy / queue. Stage 4 calls this before starting a new turn.
 */
export function shouldOracleAutoRestartListening(input: {
  sessionActive: boolean;
  inputMode: OracleVoiceLoopMode;
  isBusy: boolean;
  isPlaying: boolean;
  queueLength: number;
  isTranscribing: boolean;
  isListening: boolean;
  micPermission: MicPermissionState;
  capabilityBlocked?: boolean;
  spiritTransportError?: string | null;
  ttsLastError?: string | null;
  speechLastError?: string | null;
}): boolean {
  if (!input.sessionActive) return false;
  if (input.inputMode !== "hands-free") return false;
  if (input.capabilityBlocked) return false;
  if (input.micPermission !== "granted") return false;
  if (input.isBusy) return false;
  if (input.isPlaying || input.queueLength > 0) return false;
  if (input.isTranscribing) return false;
  if (input.isListening) return false;
  if (input.spiritTransportError?.trim()) return false;
  if (input.ttsLastError?.trim()) return false;
  if (input.speechLastError?.trim()) return false;
  return true;
}
