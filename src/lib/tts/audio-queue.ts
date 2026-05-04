// ── AudioQueue — /api/tts + WebAudio + HTMLAudio fallback (Prompt 9G hard interrupt) ─
// > Chaining speak() behind `this.chain.then` was leaving B waiting on A’s fetch — UX rot.
// > Interrupt resets the promise tail; stale runSession finally must not nuke the new session’s op.
// > Generation gate: every interrupt/stop bumps playGeneration; async tails bail before play.
import { parseTtsSegments, type TtsSegment } from "@/lib/tts/tts-parser";
import { decodeTtsVoiceNameFromHeader } from "@/lib/tts/safe-tts-headers";

/** User-facing copy — VoiceSettingsPanel + toast-adjacent; keep in sync with VoiceSettingsPanel filters. */
export const TTS_AUDIO_BLOCKED_MESSAGE =
  "Audio blocked. Tap Enable audio, then try Speak again.";

export type TtsPlaybackMode = "audio-context" | "html-audio";

export type TtsLatency = {
  fetchMs?: number;
  decodeMs?: number;
  totalMs?: number;
  /** First `/api/tts` fetch start → audible playback start (first chunk). */
  timeToFirstAudioMs?: number;
  startDelayMs?: number;
  provider?: string;
  upstreamMs?: number;
  playbackMode?: TtsPlaybackMode;
  /** Applied voice speed (X-Spirit-TTS-Speed / ElevenLabs). */
  speed?: number;
  /** ElevenLabs voice_id (header + client mirror). */
  voiceId?: string;
  /** Friendly label (client-selected name at request time). */
  voiceName?: string;
  /** Prompt 10B — e.g. "Spoken: summary (message was long)" */
  spokenSummaryLine?: string;
};

export type AudioQueueState = {
  isPlaying: boolean;
  queueLength: number;
  audioContextState: AudioContextState | "unknown";
};

export type TtsPlaybackEvent = "interrupted";

type QueueItem =
  | { kind: "pause"; ms: number }
  | { kind: "speech"; text: string };

function segmentsToQueue(segments: TtsSegment[]): QueueItem[] {
  const out: QueueItem[] = [];
  for (const s of segments) {
    if (s.type === "pause" && s.ms > 0) out.push({ kind: "pause", ms: s.ms });
    else if (s.type === "speech" && s.text.trim())
      out.push({ kind: "speech", text: s.text.trim() });
  }
  return out;
}

function nowMs(): number {
  try {
    if (typeof performance !== "undefined" && typeof performance.now === "function") {
      return performance.now();
    }
  } catch {
    /* ignore */
  }
  return Date.now();
}

function sniffAudioMime(buf: ArrayBuffer): string {
  const u = new Uint8Array(buf.byteLength > 16 ? buf.slice(0, 16) : buf);
  if (u.length >= 4 && u[0] === 0x52 && u[1] === 0x49 && u[2] === 0x46 && u[3] === 0x46) {
    return "audio/wav";
  }
  if (u.length >= 2 && u[0] === 0xff && (u[1] & 0xe0) === 0xe0) return "audio/mpeg";
  if (u.length >= 3 && u[0] === 0x49 && u[1] === 0x44 && u[2] === 0x33) return "audio/mpeg";
  return "audio/mpeg";
}

function isLikelyIos(): boolean {
  if (typeof navigator === "undefined") return false;
  return /iP(hone|ad|od)/i.test(navigator.userAgent);
}

export type AudioQueueOptions = {
  onState?: (s: AudioQueueState) => void;
  onError?: (message: string) => void;
  onLatency?: (m: TtsLatency) => void;
  /** Fired when a hard interrupt cuts active work (manual Speak / auto-speak / stop). */
  onPlaybackEvent?: (e: TtsPlaybackEvent) => void;
  ttsEndpoint?: string;
};

export class AudioQueue {
  private readonly ttsEndpoint: string;
  private readonly onState?: (s: AudioQueueState) => void;
  private readonly onError?: (message: string) => void;
  private readonly onLatency?: (m: TtsLatency) => void;
  private readonly onPlaybackEvent?: (e: TtsPlaybackEvent) => void;

  private ctx: AudioContext | null = null;
  private pending: QueueItem[] = [];
  private activeSources = new Set<AudioBufferSourceNode>();
  private chain: Promise<void> = Promise.resolve();
  private op: AbortController | null = null;
  private playing = false;
  private sessionChunkIndex = 0;
  /** Bumped on every interrupt-speak / stop; stale async tails compare against this. */
  private playGeneration = 0;

  private sessionPreferHtmlAudioFirst = false;
  /** Appended to final chunk latency row (Prompt 10B). */
  private sessionSpokenSummaryLine?: string;
  private htmlAudioEl: HTMLAudioElement | null = null;
  private htmlAudioObjectUrl: string | null = null;

  startDelayMs = 0;
  sentenceGapMs = 150;
  /** POSTed to /api/tts as `speed` (useTTS mirrors localStorage). */
  ttsVoiceSpeed = 1.12;
  /** POSTed to /api/tts as `voiceId` (ElevenLabs only). */
  ttsVoiceId: string | null = null;
  /** Shown on “Last voice” line when provider echoes id without name. */
  ttsVoiceName: string | null = null;

  constructor(opts: AudioQueueOptions = {}) {
    this.onState = opts.onState;
    this.onError = opts.onError;
    this.onLatency = opts.onLatency;
    this.onPlaybackEvent = opts.onPlaybackEvent;
    this.ttsEndpoint = opts.ttsEndpoint ?? "/api/tts";
  }

  private err(msg: string): void {
    try {
      this.onError?.(msg);
    } catch {
      /* swallow */
    }
    console.error("[audio-queue]", msg);
  }

  private emit(): void {
    try {
      this.onState?.({
        isPlaying: this.playing,
        queueLength: this.pending.length,
        audioContextState: this.ctx?.state ?? "unknown",
      });
    } catch {
      /* swallow */
    }
  }

  private logLatency(m: TtsLatency): void {
    try {
      this.onLatency?.(m);
    } catch {
      /* swallow */
    }
    if (process.env.NODE_ENV === "development") {
      const pm = m.playbackMode ?? "?";
      console.info(
        `[tts] latency mode=${pm} fetch=${m.fetchMs ?? "?"}ms decode=${m.decodeMs ?? "?"}ms ttfa=${m.timeToFirstAudioMs ?? "?"}ms total=${m.totalMs ?? "?"}ms`,
      );
    }
  }

  private ensureContext(): AudioContext | null {
    if (typeof window === "undefined") return null;
    if (this.ctx) return this.ctx;
    const Ctx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctx) return null;
    this.ctx = new Ctx();
    this.emit();
    return this.ctx;
  }

  /**
   * Resume AudioContext — call from a tap/handler before playback.
   * @returns false if context exists but could not enter `running` (mobile gesture / policy).
   */
  async ensureAudioUnlocked(): Promise<boolean> {
    const c = this.ensureContext();
    if (!c) return true;
    try {
      if (c.state === "suspended") await c.resume();
    } catch (e) {
      console.error("[audio-queue] ensureAudioUnlocked resume:", e);
      this.emit();
      return false;
    }
    this.emit();
    return c.state === "running";
  }

  /** @deprecated alias for ensureAudioUnlocked */
  async prime(): Promise<boolean> {
    return this.ensureAudioUnlocked();
  }

  private async resumeIfNeeded(): Promise<void> {
    const c = this.ctx;
    if (!c) return;
    try {
      if (c.state === "suspended") await c.resume();
    } catch (e) {
      console.error("[audio-queue] resume:", e);
    }
    this.emit();
  }

  private tearDownHtmlAudio(): void {
    const el = this.htmlAudioEl;
    const url = this.htmlAudioObjectUrl;
    this.htmlAudioEl = null;
    this.htmlAudioObjectUrl = null;
    if (el) {
      try {
        el.pause();
        el.removeAttribute("src");
        el.load();
      } catch {
        /* ignore */
      }
    }
    if (url) {
      try {
        URL.revokeObjectURL(url);
      } catch {
        /* ignore */
      }
    }
  }

  private hardStopPlayback(): void {
    this.op?.abort();
    this.op = null;
    for (const s of this.activeSources) {
      try {
        s.stop(0);
      } catch {
        /* already stopped */
      }
    }
    this.activeSources.clear();
    this.tearDownHtmlAudio();
    this.playing = false;
    this.emit();
  }

  stop(): void {
    this.playGeneration += 1;
    this.pending = [];
    this.hardStopPlayback();
    this.emit();
  }

  private snapshotHadActivePlayback(): boolean {
    return (
      this.playing ||
      this.activeSources.size > 0 ||
      this.htmlAudioEl != null ||
      (this.op != null && !this.op.signal.aborted)
    );
  }

  speak(
    text: string,
    options?: {
      interrupt?: boolean;
      preferHtmlAudioFirst?: boolean;
      spokenSummaryLine?: string;
    },
  ): void {
    const interrupt = options?.interrupt !== false;
    if (!interrupt) {
      this.enqueue(text);
      return;
    }
    const hadActive = this.snapshotHadActivePlayback();
    this.playGeneration += 1;
    const generation = this.playGeneration;
    this.hardStopPlayback();
    this.pending = segmentsToQueue(parseTtsSegments(text));
    this.sessionPreferHtmlAudioFirst = Boolean(options?.preferHtmlAudioFirst);
    this.sessionSpokenSummaryLine = options?.spokenSummaryLine;
    if (hadActive) {
      try {
        this.onPlaybackEvent?.("interrupted");
      } catch {
        /* swallow */
      }
    }
    if (process.env.NODE_ENV === "development") {
      console.info("[tts] interrupt current playback");
    }
    // ── Do NOT chain behind the old tail — B must not wait for A’s fetch/decode/play.
    this.chain = Promise.resolve()
      .catch(() => {})
      .then(async () => {
        if (generation !== this.playGeneration) {
          if (process.env.NODE_ENV === "development") {
            console.info("[tts] session skipped stale audio");
          }
          return;
        }
        await this.runSession(generation);
      });
    void this.chain.catch(() => {});
  }

  /**
   * Speak multiple segments in one session (chunked long reads).
   * Each segment must already respect /api/tts char limits.
   */
  speakMany(
    texts: string[],
    options?: {
      interrupt?: boolean;
      preferHtmlAudioFirst?: boolean;
      spokenSummaryLine?: string;
    },
  ): void {
    const parts = texts.map((t) => t.trim()).filter(Boolean);
    if (!parts.length) return;
    const interrupt = options?.interrupt !== false;
    if (!interrupt) {
      for (const t of parts) this.enqueue(t);
      return;
    }
    const hadActive = this.snapshotHadActivePlayback();
    this.playGeneration += 1;
    const generation = this.playGeneration;
    this.hardStopPlayback();
    const q: QueueItem[] = [];
    for (const t of parts) q.push(...segmentsToQueue(parseTtsSegments(t)));
    this.pending = q;
    this.sessionPreferHtmlAudioFirst = Boolean(options?.preferHtmlAudioFirst);
    this.sessionSpokenSummaryLine = options?.spokenSummaryLine;
    if (hadActive) {
      try {
        this.onPlaybackEvent?.("interrupted");
      } catch {
        /* swallow */
      }
    }
    this.chain = Promise.resolve()
      .catch(() => {})
      .then(async () => {
        if (generation !== this.playGeneration) return;
        await this.runSession(generation);
      });
    void this.chain.catch(() => {});
  }

  enqueue(text: string): void {
    const extra = segmentsToQueue(parseTtsSegments(text));
    const scheduledGen = this.playGeneration;
    this.chain = this.chain
      .catch(() => {})
      .then(async () => {
        if (scheduledGen !== this.playGeneration) return;
        this.pending.push(...extra);
        const gen = this.playGeneration;
        if (!this.playing && this.pending.length > 0) {
          await this.runSession(gen);
        }
      });
    void this.chain.catch(() => {});
  }

  async drain(): Promise<void> {
    await this.chain;
  }

  private sleep(ms: number, signal: AbortSignal): Promise<void> {
    return new Promise((resolve, reject) => {
      if (signal.aborted) {
        reject(new DOMException("aborted", "AbortError"));
        return;
      }
      const t = window.setTimeout(() => {
        signal.removeEventListener("abort", onAbort);
        resolve();
      }, ms);
      const onAbort = () => {
        window.clearTimeout(t);
        reject(new DOMException("aborted", "AbortError"));
      };
      signal.addEventListener("abort", onAbort, { once: true });
    });
  }

  private async fetchSpeechBuffer(
    text: string,
    signal: AbortSignal,
  ): Promise<{
    buffer: ArrayBuffer;
    provider?: string;
    upstreamMs?: number;
    speed?: number;
    voiceId?: string;
    voiceName?: string;
  }> {
    const res = await fetch(this.ttsEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        speed: this.ttsVoiceSpeed,
        ...(this.ttsVoiceId ? { voiceId: this.ttsVoiceId } : {}),
        ...(this.ttsVoiceName ? { voiceName: this.ttsVoiceName } : {}),
      }),
      signal,
    });
    if (!res.ok) {
      const errText = await res.text().catch(() => res.statusText);
      throw new Error(errText.slice(0, 200) || res.statusText);
    }
    const prov = res.headers.get("x-spirit-tts-provider")?.trim();
    const upstreamRaw = res.headers.get("x-spirit-tts-upstream-ms")?.trim();
    const upstreamMsParsed = upstreamRaw ? Number.parseInt(upstreamRaw, 10) : NaN;
    const upstreamMs =
      Number.isFinite(upstreamMsParsed) && upstreamMsParsed >= 0
        ? upstreamMsParsed
        : undefined;
    const speedRaw = res.headers.get("x-spirit-tts-speed")?.trim();
    const speedParsed = speedRaw ? Number.parseFloat(speedRaw) : NaN;
    const speed =
      Number.isFinite(speedParsed) && speedParsed > 0 ? speedParsed : undefined;
    const voiceIdHdr = res.headers.get("x-spirit-tts-voice-id")?.trim();
    const encHdr =
      res.headers.get("x-spirit-tts-voice-name-encoded")?.trim();
    const legacyAscii = res.headers.get("x-spirit-tts-voice-name")?.trim();
    const decoded = decodeTtsVoiceNameFromHeader(encHdr);
    const voiceNameResolved = decoded ?? legacyAscii ?? this.ttsVoiceName ?? undefined;
    const buffer = await res.arrayBuffer();
    return {
      buffer,
      provider: prov || undefined,
      upstreamMs,
      speed,
      voiceId: voiceIdHdr || this.ttsVoiceId || undefined,
      voiceName: voiceNameResolved || undefined,
    };
  }

  private stale(gen: number): boolean {
    return gen !== this.playGeneration;
  }

  private async playHtmlAudioSegment(
    buf: ArrayBuffer,
    signal: AbortSignal,
    requestStart: number,
    responseReceived: number,
    provider: string | undefined,
    upstreamMs: number | undefined,
    isFirstSpeechChunk: boolean,
    expectedGeneration: number,
    ttsSpeed?: number,
    ttsVoiceId?: string,
    ttsVoiceName?: string,
    extraLatency?: Partial<TtsLatency>,
  ): Promise<boolean> {
    if (signal.aborted || this.stale(expectedGeneration)) return false;
    this.tearDownHtmlAudio();
    const mime = sniffAudioMime(buf);
    const blob = new Blob([buf], { type: mime });
    const url = URL.createObjectURL(blob);
    this.htmlAudioObjectUrl = url;
    const el = new Audio(url);
    el.setAttribute("playsinline", "");
    (el as HTMLAudioElement & { playsInline?: boolean }).playsInline = true;
    this.htmlAudioEl = el;

    try {
      await el.play().catch((e: unknown) => {
        const name = e && typeof e === "object" && "name" in e ? String((e as Error).name) : "";
        if (name === "NotAllowedError") {
          this.err(TTS_AUDIO_BLOCKED_MESSAGE);
        }
        throw e;
      });

      const playbackStartAt = nowMs();

      if (this.stale(expectedGeneration)) {
        try {
          el.pause();
        } catch {
          /* ignore */
        }
        return false;
      }

      await new Promise<void>((resolve, reject) => {
        const cleanup = () => {
          el.removeEventListener("ended", onEnded);
          el.removeEventListener("error", onErr);
          signal.removeEventListener("abort", onAbort);
        };
        const onEnded = () => {
          cleanup();
          resolve();
        };
        const onErr = () => {
          cleanup();
          reject(new Error("HTMLAudioElement error"));
        };
        const onAbort = () => {
          cleanup();
          try {
            el.pause();
          } catch {
            /* ignore */
          }
          reject(new DOMException("aborted", "AbortError"));
        };
        el.addEventListener("ended", onEnded, { once: true });
        el.addEventListener("error", onErr, { once: true });
        signal.addEventListener("abort", onAbort, { once: true });
      });

      if (this.stale(expectedGeneration)) return false;

      const endedAt = nowMs();
      this.logLatency({
        fetchMs: Math.round(responseReceived - requestStart),
        decodeMs: 0,
        totalMs: Math.round(endedAt - requestStart),
        timeToFirstAudioMs: Math.round(playbackStartAt - requestStart),
        startDelayMs: isFirstSpeechChunk ? this.startDelayMs : 0,
        provider,
        upstreamMs,
        playbackMode: "html-audio",
        speed: ttsSpeed,
        voiceId: ttsVoiceId,
        voiceName: ttsVoiceName,
        ...extraLatency,
      });
      return true;
    } catch (e) {
      if ((e as Error)?.name === "AbortError") return false;
      if (
        e &&
        typeof e === "object" &&
        "name" in e &&
        (e as Error).name === "NotAllowedError"
      ) {
        return false;
      }
      this.err(e instanceof Error ? e.message : "HTML audio playback failed");
      return false;
    } finally {
      this.tearDownHtmlAudio();
    }
  }

  private async tryPlayWithAudioContext(
    buf: ArrayBuffer,
    signal: AbortSignal,
    requestStart: number,
    responseReceived: number,
    provider: string | undefined,
    upstreamMs: number | undefined,
    isFirstSpeechChunk: boolean,
    expectedGeneration: number,
    ttsSpeed?: number,
    ttsVoiceId?: string,
    ttsVoiceName?: string,
    extraLatency?: Partial<TtsLatency>,
  ): Promise<boolean> {
    const ctx = this.ensureContext();
    if (!ctx) return false;

    await this.resumeIfNeeded();
    if (ctx.state !== "running" || this.stale(expectedGeneration)) return false;

    const decodeStart = nowMs();
    let audio: AudioBuffer;
    try {
      const copy = buf.slice(0);
      audio = await new Promise((resolve, reject) => {
        ctx.decodeAudioData(copy, resolve, () => reject(new Error("decodeAudioData failed")));
      });
    } catch {
      return false;
    }
    const decodeEnd = nowMs();
    if (signal.aborted || this.stale(expectedGeneration)) return false;

    await this.resumeIfNeeded();
    if (ctx.state !== "running" || this.stale(expectedGeneration)) return false;

    try {
      let playbackStartAt = 0;
      await new Promise<void>((resolve, reject) => {
        const src = ctx.createBufferSource();
        src.buffer = audio;
        src.connect(ctx.destination);
        this.activeSources.add(src);
        src.onended = () => {
          this.activeSources.delete(src);
          resolve();
        };
        try {
          src.start(0);
          playbackStartAt = nowMs();
        } catch (e) {
          this.activeSources.delete(src);
          reject(e);
        }
      });
      if (this.stale(expectedGeneration)) return false;
      const endedAt = nowMs();
      this.logLatency({
        fetchMs: Math.round(responseReceived - requestStart),
        decodeMs: Math.round(decodeEnd - decodeStart),
        totalMs: Math.round(endedAt - requestStart),
        timeToFirstAudioMs: Math.round(playbackStartAt - requestStart),
        startDelayMs: isFirstSpeechChunk ? this.startDelayMs : 0,
        provider,
        upstreamMs,
        playbackMode: "audio-context",
        speed: ttsSpeed,
        voiceId: ttsVoiceId,
        voiceName: ttsVoiceName,
        ...extraLatency,
      });
      return true;
    } catch (e) {
      if ((e as Error)?.name === "AbortError") return false;
      return false;
    }
  }

  private async runSession(expectedGeneration: number): Promise<void> {
    if (this.playing) return;

    try {
      const unlocked = await this.ensureAudioUnlocked();
      if (this.stale(expectedGeneration)) return;
      if (!unlocked) {
        this.err(TTS_AUDIO_BLOCKED_MESSAGE);
        return;
      }

      this.op = new AbortController();
      const signal = this.op.signal;
      this.playing = true;
      this.sessionChunkIndex = 0;
      this.emit();

      if (this.startDelayMs > 0) {
        try {
          await this.sleep(this.startDelayMs, signal);
        } catch {
          return;
        }
      }

      if (this.stale(expectedGeneration)) return;

      while (!signal.aborted && !this.stale(expectedGeneration)) {
        const item = this.pending.shift();
        if (!item) break;

        if (item.kind === "pause") {
          try {
            await this.sleep(item.ms, signal);
          } catch {
            break;
          }
          continue;
        }

        const requestStart = nowMs();
        let buf: ArrayBuffer;
        let provider: string | undefined;
        let upstreamMs: number | undefined;
        let ttsSpeed: number | undefined;
        let ttsVoiceId: string | undefined;
        let ttsVoiceName: string | undefined;
        try {
          const fetched = await this.fetchSpeechBuffer(item.text, signal);
          buf = fetched.buffer;
          provider = fetched.provider;
          upstreamMs = fetched.upstreamMs;
          ttsSpeed = fetched.speed;
          ttsVoiceId = fetched.voiceId;
          ttsVoiceName = fetched.voiceName;
        } catch (e) {
          if ((e as Error)?.name === "AbortError") break;
          this.err(e instanceof Error ? e.message : "fetch /api/tts failed");
          continue;
        }
        const responseReceived = nowMs();

        if (signal.aborted || this.stale(expectedGeneration)) {
          if (process.env.NODE_ENV === "development" && this.stale(expectedGeneration)) {
            console.info("[tts] session skipped stale audio");
          }
          break;
        }

        const isFirstSpeechChunk = this.sessionChunkIndex === 0;
        this.sessionChunkIndex += 1;

        const moreSpeechLater = this.pending.some((x) => x.kind === "speech");
        const tail: Partial<TtsLatency> =
          !moreSpeechLater && this.sessionSpokenSummaryLine
            ? { spokenSummaryLine: this.sessionSpokenSummaryLine }
            : {};

        const preferHtmlFirst =
          this.sessionPreferHtmlAudioFirst ||
          (typeof window !== "undefined" &&
            (isLikelyIos() ||
              !(
                window.AudioContext ||
                (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
              )));

        let played = false;
        if (preferHtmlFirst) {
          played = await this.playHtmlAudioSegment(
            buf,
            signal,
            requestStart,
            responseReceived,
            provider,
            upstreamMs,
            isFirstSpeechChunk,
            expectedGeneration,
            ttsSpeed,
            ttsVoiceId,
            ttsVoiceName,
            tail,
          );
          if (!played && !this.stale(expectedGeneration)) {
            played = await this.tryPlayWithAudioContext(
              buf,
              signal,
              requestStart,
              responseReceived,
              provider,
              upstreamMs,
              isFirstSpeechChunk,
              expectedGeneration,
              ttsSpeed,
              ttsVoiceId,
              ttsVoiceName,
              tail,
            );
          }
        } else {
          played = await this.tryPlayWithAudioContext(
            buf,
            signal,
            requestStart,
            responseReceived,
            provider,
            upstreamMs,
            isFirstSpeechChunk,
            expectedGeneration,
            ttsSpeed,
            ttsVoiceId,
            ttsVoiceName,
            tail,
          );
          if (!played && !this.stale(expectedGeneration)) {
            played = await this.playHtmlAudioSegment(
              buf,
              signal,
              requestStart,
              responseReceived,
              provider,
              upstreamMs,
              isFirstSpeechChunk,
              expectedGeneration,
              ttsSpeed,
              ttsVoiceId,
              ttsVoiceName,
              tail,
            );
          }
        }

        if (this.sentenceGapMs > 0 && !signal.aborted && !this.stale(expectedGeneration)) {
          try {
            await this.sleep(this.sentenceGapMs, signal);
          } catch {
            break;
          }
        }
      }
    } finally {
      this.sessionPreferHtmlAudioFirst = false;
      this.sessionSpokenSummaryLine = undefined;
      // ── Stale tail must NOT call hardStopPlayback — it would murder the new session’s op/sources.
      if (!this.stale(expectedGeneration)) {
        this.hardStopPlayback();
      }
      this.emit();
    }
  }
}
