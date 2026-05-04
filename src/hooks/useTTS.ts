"use client";

// ── useTTS — localStorage-backed Piper/ElevenLabs via /api/tts (Prompt 9H + 9I) ───
// > Initial render must NOT read localStorage — Next will hydration-murder you.
// > isEnabledRef: onFinish auto-speak must not lose to a stale `speak` closure on desktop.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  AudioQueue,
  type AudioQueueState,
  type TtsLatency,
  type TtsPlaybackEvent,
  TTS_AUDIO_BLOCKED_MESSAGE,
} from "@/lib/tts/audio-queue";
import {
  clampTtsVoiceSpeed,
  TTS_SPEED_DEFAULT,
  TTS_VOICE_SPEED_PRESETS,
} from "@/lib/tts/voice-speed";

export type { TtsLatency, TtsPlaybackMode } from "@/lib/tts/audio-queue";

export { TTS_VOICE_SPEED_PRESETS };

export type TtsVoiceCatalogRow = {
  voice_id: string;
  name: string;
  category?: string;
  labels?: Record<string, string>;
  preview_url?: string | null;
};

const LS_ENABLED = "spirit:ttsEnabled";
const LS_START = "spirit:ttsStartDelayMs";
const LS_GAP = "spirit:ttsSentenceGapMs";
const LS_AUTO = "spirit:ttsAutoSpeak";
const LS_VOICE_SPEED = "spirit:ttsVoiceSpeed";
const LS_VOICE_ID = "spirit:ttsVoiceId";
const LS_VOICE_NAME = "spirit:ttsVoiceName";

function readBool(key: string, fallback: boolean): boolean {
  if (typeof window === "undefined") return fallback;
  try {
    const v = window.localStorage.getItem(key);
    if (v === null) return fallback;
    return v === "1" || v === "true";
  } catch {
    return fallback;
  }
}

function readNum(key: string, fallback: number): number {
  if (typeof window === "undefined") return fallback;
  try {
    const v = window.localStorage.getItem(key);
    if (v === null) return fallback;
    const n = Number(v);
    return Number.isFinite(n) ? n : fallback;
  } catch {
    return fallback;
  }
}

function readStr(key: string, fallback: string | null): string | null {
  if (typeof window === "undefined") return fallback;
  try {
    const v = window.localStorage.getItem(key);
    if (v === null) return fallback;
    const t = v.trim();
    return t ? t : fallback;
  } catch {
    return fallback;
  }
}

function writeLs(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* private mode / quota */
  }
}

export type UseTtsState = AudioQueueState & {
  isEnabled: boolean;
  startDelayMs: number;
  sentenceGapMs: number;
  autoSpeakAssistant: boolean;
  /** Clamped 0.7–1.2; POSTed to /api/tts as `speed`. */
  voiceSpeed: number;
  /** ElevenLabs voice_id (localStorage + Voice picker). */
  elevenLabsVoiceId: string | null;
  elevenLabsVoiceName: string | null;
  voices: TtsVoiceCatalogRow[];
  voicesStatus: "idle" | "loading" | "ok" | "error";
  voicesError?: string;
  lastError?: string;
  lastLatency?: TtsLatency;
  lastVoiceNote?: "interrupted";
  /** From GET /api/tts/voices (Prompt 9L). */
  voicesSource?: string;
  voicesAllowlistMode?: string;
  voicesWarnings?: string[];
};

export function useTTS() {
  const [isEnabled, setIsEnabledState] = useState(false);
  const isEnabledRef = useRef(false);

  const [startDelayMs, setStartDelayMsState] = useState(0);
  const [sentenceGapMs, setSentenceGapMsState] = useState(150);
  const [autoSpeakAssistant, setAutoSpeakAssistantState] = useState(false);
  const [voiceSpeed, setVoiceSpeedState] = useState(TTS_SPEED_DEFAULT);
  const [elevenLabsVoiceId, setElevenLabsVoiceIdState] = useState<string | null>(null);
  const [elevenLabsVoiceName, setElevenLabsVoiceNameState] = useState<string | null>(null);
  const [voices, setVoices] = useState<TtsVoiceCatalogRow[]>([]);
  const [voicesSource, setVoicesSource] = useState<string | undefined>(undefined);
  const [voicesAllowlistMode, setVoicesAllowlistMode] = useState<string | undefined>(undefined);
  const [voicesWarnings, setVoicesWarnings] = useState<string[]>([]);
  const [voicesStatus, setVoicesStatus] = useState<"idle" | "loading" | "ok" | "error">(
    "idle",
  );
  const [voicesError, setVoicesError] = useState<string | undefined>(undefined);
  const [queueUi, setQueueUi] = useState<AudioQueueState>({
    isPlaying: false,
    queueLength: 0,
    audioContextState: "unknown",
  });
  const [lastError, setLastError] = useState<string | undefined>(undefined);
  const [lastLatency, setLastLatency] = useState<TtsLatency | undefined>(undefined);
  const [lastVoiceNote, setLastVoiceNote] = useState<"interrupted" | undefined>(
    undefined,
  );

  const queueRef = useRef<AudioQueue | null>(null);

  const onPlaybackEvent = useCallback((e: TtsPlaybackEvent) => {
    if (e === "interrupted") setLastVoiceNote("interrupted");
  }, []);

  const getQueue = useCallback(() => {
    if (!queueRef.current) {
      queueRef.current = new AudioQueue({
        onState: (s) => setQueueUi(s),
        onError: (msg) => setLastError(msg),
        onLatency: (m) => {
          setLastVoiceNote(undefined);
          setLastLatency(m);
        },
        onPlaybackEvent,
      });
    }
    return queueRef.current;
  }, [onPlaybackEvent]);

  useEffect(() => {
    queueMicrotask(() => {
      const en = readBool(LS_ENABLED, false);
      isEnabledRef.current = en;
      setIsEnabledState(en);
      setStartDelayMsState(readNum(LS_START, 0));
      setSentenceGapMsState(readNum(LS_GAP, 150));
      setAutoSpeakAssistantState(readBool(LS_AUTO, false));
      const raw = readNum(LS_VOICE_SPEED, TTS_SPEED_DEFAULT);
      setVoiceSpeedState(clampTtsVoiceSpeed(raw));
      setElevenLabsVoiceIdState(readStr(LS_VOICE_ID, null));
      setElevenLabsVoiceNameState(readStr(LS_VOICE_NAME, null));
    });
  }, []);

  useEffect(() => {
    const q = getQueue();
    q.startDelayMs = startDelayMs;
    q.sentenceGapMs = sentenceGapMs;
    q.ttsVoiceSpeed = voiceSpeed;
    q.ttsVoiceId = elevenLabsVoiceId?.trim() ? elevenLabsVoiceId.trim() : null;
    q.ttsVoiceName = elevenLabsVoiceName?.trim() ? elevenLabsVoiceName.trim() : null;
  }, [getQueue, startDelayMs, sentenceGapMs, voiceSpeed, elevenLabsVoiceId, elevenLabsVoiceName]);

  useEffect(() => {
    if (!isEnabled) {
      getQueue().stop();
    }
  }, [getQueue, isEnabled]);

  const applyVoiceSelection = useCallback((id: string, name: string | null) => {
    const tid = id.trim();
    if (!tid) return;
    setElevenLabsVoiceIdState(tid);
    setElevenLabsVoiceNameState(name?.trim() ? name.trim() : null);
    writeLs(LS_VOICE_ID, tid);
    if (name?.trim()) writeLs(LS_VOICE_NAME, name.trim());
    else {
      try {
        window.localStorage.removeItem(LS_VOICE_NAME);
      } catch {
        /* ignore */
      }
    }
  }, []);

  const refreshElevenLabsVoices = useCallback(async () => {
    setVoicesError(undefined);
    setVoicesStatus("loading");
    setVoicesWarnings([]);
    try {
      const res = await fetch("/api/tts/voices", { method: "GET", cache: "no-store" });
      let json: {
        ok?: boolean;
        voices?: TtsVoiceCatalogRow[];
        defaultVoiceId?: string | null;
        defaultVoiceName?: string | null;
        error?: string;
        detail?: string;
        status?: number;
        source?: string;
        allowlistMode?: string;
        warnings?: unknown[];
        pickWarning?: string;
      };
      try {
        json = (await res.json()) as typeof json;
      } catch {
        throw new Error(`voices_${res.status}_invalid_json`);
      }
      if (!res.ok || !json.ok) {
        const parts = [json.error || `voices_${res.status}`];
        if (json.detail) parts.push(json.detail);
        throw new Error(parts.join(" — "));
      }
      const list = Array.isArray(json.voices) ? json.voices : [];
      setVoices(list);
      setVoicesStatus("ok");
      setVoicesSource(typeof json.source === "string" ? json.source : undefined);
      setVoicesAllowlistMode(typeof json.allowlistMode === "string" ? json.allowlistMode : undefined);
      const w: string[] = [];
      if (Array.isArray(json.warnings)) {
        for (const x of json.warnings) {
          if (typeof x === "string" && x.trim()) w.push(x.trim());
        }
      }
      if (typeof json.pickWarning === "string" && json.pickWarning.trim()) {
        w.push(json.pickWarning.trim());
      }
      setVoicesWarnings(w);

      const savedId = readStr(LS_VOICE_ID, null);
      if (savedId) {
        const row = list.find((v) => v.voice_id === savedId);
        if (row) {
          applyVoiceSelection(row.voice_id, row.name);
        } else if (json.defaultVoiceId) {
          applyVoiceSelection(json.defaultVoiceId, json.defaultVoiceName ?? null);
        } else if (list[0]) {
          applyVoiceSelection(list[0].voice_id, list[0].name);
        }
      } else if (json.defaultVoiceId) {
        applyVoiceSelection(json.defaultVoiceId, json.defaultVoiceName ?? null);
      } else if (list[0]) {
        applyVoiceSelection(list[0].voice_id, list[0].name);
      }
    } catch (e) {
      setVoicesStatus("error");
      setVoicesError(e instanceof Error ? e.message : String(e));
      setVoicesSource(undefined);
      setVoicesAllowlistMode(undefined);
      setVoicesWarnings([]);
    }
  }, [applyVoiceSelection]);

  const setEnabled = useCallback(
    (next: boolean) => {
      isEnabledRef.current = next;
      setIsEnabledState(next);
      writeLs(LS_ENABLED, next ? "1" : "0");
      if (!next) getQueue().stop();
    },
    [getQueue],
  );

  const toggleEnabled = useCallback(() => {
    setEnabled(!isEnabled);
  }, [isEnabled, setEnabled]);

  const setStartDelayMs = useCallback((ms: number) => {
    setStartDelayMsState(ms);
    writeLs(LS_START, String(ms));
  }, []);

  const setSentenceGapMs = useCallback((ms: number) => {
    setSentenceGapMsState(ms);
    writeLs(LS_GAP, String(ms));
  }, []);

  const setAutoSpeakAssistant = useCallback((next: boolean) => {
    setAutoSpeakAssistantState(next);
    writeLs(LS_AUTO, next ? "1" : "0");
  }, []);

  const toggleAutoSpeakAssistant = useCallback(() => {
    setAutoSpeakAssistantState((v) => {
      const n = !v;
      writeLs(LS_AUTO, n ? "1" : "0");
      return n;
    });
  }, []);

  const setVoiceSpeed = useCallback((next: number) => {
    const v = clampTtsVoiceSpeed(next);
    setVoiceSpeedState(v);
    writeLs(LS_VOICE_SPEED, String(v));
  }, []);

  const setElevenLabsVoiceFromPicker = useCallback(
    (voiceId: string, name?: string | null) => {
      const row = voices.find((v) => v.voice_id === voiceId);
      applyVoiceSelection(voiceId, name ?? row?.name ?? null);
    },
    [applyVoiceSelection, voices],
  );

  const ensureAudioUnlocked = useCallback(async (): Promise<boolean> => {
    const ok = await getQueue().ensureAudioUnlocked();
    if (ok) setLastError(undefined);
    else setLastError(TTS_AUDIO_BLOCKED_MESSAGE);
    return ok;
  }, [getQueue]);

  const prime = ensureAudioUnlocked;

  const stop = useCallback(() => {
    getQueue().stop();
  }, [getQueue]);

  const speak = useCallback(
    (
      text: string,
      options?: {
        interrupt?: boolean;
        preferHtmlAudioFirst?: boolean;
        spokenSummaryLine?: string;
      },
    ) => {
      if (!isEnabledRef.current) return;
      setLastError(undefined);
      getQueue().speak(text, {
        interrupt: options?.interrupt ?? true,
        preferHtmlAudioFirst: options?.preferHtmlAudioFirst,
        spokenSummaryLine: options?.spokenSummaryLine,
      });
    },
    [getQueue],
  );

  const speakMany = useCallback(
    (
      texts: string[],
      options?: {
        interrupt?: boolean;
        preferHtmlAudioFirst?: boolean;
        spokenSummaryLine?: string;
      },
    ) => {
      if (!isEnabledRef.current) return;
      setLastError(undefined);
      getQueue().speakMany(texts, {
        interrupt: options?.interrupt ?? true,
        preferHtmlAudioFirst: options?.preferHtmlAudioFirst,
        spokenSummaryLine: options?.spokenSummaryLine,
      });
    },
    [getQueue],
  );

  const enqueue = useCallback(
    (text: string) => {
      if (!isEnabledRef.current) return;
      setLastError(undefined);
      getQueue().enqueue(text);
    },
    [getQueue],
  );

  const drain = useCallback(async () => {
    await getQueue().drain();
  }, [getQueue]);

  const state: UseTtsState = useMemo(
    () => ({
      ...queueUi,
      isEnabled,
      startDelayMs,
      sentenceGapMs,
      autoSpeakAssistant,
      voiceSpeed,
      elevenLabsVoiceId,
      elevenLabsVoiceName,
      voices,
      voicesSource,
      voicesAllowlistMode,
      voicesWarnings,
      voicesStatus,
      voicesError,
      lastError,
      lastLatency,
      lastVoiceNote,
    }),
    [
      queueUi,
      isEnabled,
      startDelayMs,
      sentenceGapMs,
      autoSpeakAssistant,
      voiceSpeed,
      elevenLabsVoiceId,
      elevenLabsVoiceName,
      voices,
      voicesSource,
      voicesAllowlistMode,
      voicesWarnings,
      voicesStatus,
      voicesError,
      lastError,
      lastLatency,
      lastVoiceNote,
    ],
  );

  return {
    state,
    speak,
    speakMany,
    enqueue,
    stop,
    ensureAudioUnlocked,
    prime,
    drain,
    setEnabled,
    toggleEnabled,
    setStartDelayMs,
    setSentenceGapMs,
    setAutoSpeakAssistant,
    toggleAutoSpeakAssistant,
    setVoiceSpeed,
    refreshElevenLabsVoices,
    setElevenLabsVoiceFromPicker,
  };
}
