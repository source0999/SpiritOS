import type { TtsSegment } from "@/lib/ttsParser";

type QueueOptions = {
  onPlayingChange?: (playing: boolean) => void;
};

export class AudioQueue {
  private ctx: AudioContext | null = null;
  private runId = 0;
  private activeSource: AudioBufferSourceNode | null = null;
  private activeAborts = new Set<AbortController>();
  private onPlayingChange?: (playing: boolean) => void;

  constructor(options?: QueueOptions) {
    this.onPlayingChange = options?.onPlayingChange;
  }

  private ensureContext(): AudioContext {
    if (!this.ctx) this.ctx = new AudioContext();
    return this.ctx;
  }

  stop(): void {
    this.runId += 1;
    for (const ctrl of this.activeAborts) {
      try {
        ctrl.abort();
      } catch {
        // ignore abort errors
      }
    }
    this.activeAborts.clear();
    if (this.activeSource) {
      try {
        this.activeSource.stop();
      } catch {
        // ignore stale stop errors
      }
      this.activeSource = null;
    }
    this.onPlayingChange?.(false);
  }

  async play(segments: TtsSegment[], language = "en"): Promise<void> {
    this.stop();
    const currentRun = this.runId;
    const speechSegments = segments.some((s) => s.type === "speech");
    if (!speechSegments) return;

    this.onPlayingChange?.(true);

    try {
      const ctx = this.ensureContext();
      if (ctx.state === "suspended") await ctx.resume();

      let lookAheadPromise: Promise<AudioBuffer> | null = null;

      const getNextSpeechIndex = (start: number) => {
        for (let i = start; i < segments.length; i += 1) {
          if (segments[i]?.type === "speech") return i;
        }
        return -1;
      };

      const preloadSpeech = (index: number): Promise<AudioBuffer> => {
        const seg = segments[index];
        if (!seg || seg.type !== "speech") {
          throw new Error(`Expected speech segment at index ${index}`);
        }
        return this.fetchAndDecodeSpeechSegment(seg.text, language, currentRun, ctx);
      };

      const firstSpeechIndex = getNextSpeechIndex(0);
      if (firstSpeechIndex !== -1) lookAheadPromise = preloadSpeech(firstSpeechIndex);

      for (let i = 0; i < segments.length; i += 1) {
        if (currentRun !== this.runId) return;
        const segment = segments[i];
        if (!segment) continue;

        if (segment.type === "pause") {
          await new Promise<void>((resolve) => {
            window.setTimeout(resolve, segment.ms);
          });
          continue;
        }

        if (!lookAheadPromise) {
          lookAheadPromise = preloadSpeech(i);
        }
        const audioBuffer = await lookAheadPromise;
        lookAheadPromise = null;

        const nextSpeechIndex = getNextSpeechIndex(i + 1);
        if (nextSpeechIndex !== -1) {
          lookAheadPromise = preloadSpeech(nextSpeechIndex);
          // #region agent log
          fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
            body: JSON.stringify({
              sessionId: "7d6688",
              runId: "tts-debug-4",
              hypothesisId: "H13",
              location: "audioQueue.ts:play",
              message: "Look-ahead fetch started",
              data: { nextSpeechIndex },
              timestamp: Date.now(),
            }),
          }).catch(() => {});
          // #endregion
        }

        await this.playBuffer(audioBuffer, currentRun);
      }
    } finally {
      if (currentRun === this.runId) {
        this.onPlayingChange?.(false);
      }
    }
  }

  private async fetchAndDecodeSpeechSegment(
    text: string,
    language: string,
    runId: number,
    ctx: AudioContext,
  ): Promise<AudioBuffer> {
    const fetchStartedAt = Date.now();
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "pivot-debug-1",
        hypothesisId: "H1",
        location: "audioQueue.ts:fetchSpeechSegment",
        message: "Sentence fetch started",
        data: { textLen: text.length, runId },
        timestamp: fetchStartedAt,
      }),
    }).catch(() => {});
    // #endregion
    const abortCtrl = new AbortController();
    this.activeAborts.add(abortCtrl);
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language }),
      signal: abortCtrl.signal,
    });
    this.activeAborts.delete(abortCtrl);
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "pivot-debug-1",
        hypothesisId: "H1",
        location: "audioQueue.ts:fetchSpeechSegment",
        message: "Sentence fetch response received",
        data: { status: res.status, elapsedMs: Date.now() - fetchStartedAt, runId },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    if (!res.ok) throw new Error(`TTS API ${res.status}`);
    const bytes = await res.arrayBuffer();
    const decoded = await ctx.decodeAudioData(bytes.slice(0));
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "pivot-debug-1",
        hypothesisId: "H1",
        location: "audioQueue.ts:fetchAndDecodeSpeechSegment",
        message: "Sentence decoded via decodeAudioData",
        data: { decodedDuration: decoded.duration, bytes: bytes.byteLength, runId },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    if (runId !== this.runId) {
      throw new Error("TTS fetch aborted by newer run");
    }
    return decoded;
  }

  private playBuffer(buffer: AudioBuffer, runId: number): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      if (runId !== this.runId) {
        resolve();
        return;
      }
      const ctx = this.ensureContext();
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      this.activeSource = source;
      source.onended = () => {
        if (this.activeSource === source) this.activeSource = null;
        resolve();
      };
      try {
        source.start(0);
      } catch (e) {
        if (this.activeSource === source) this.activeSource = null;
        reject(e instanceof Error ? e : new Error(String(e)));
      }
    });
  }
}
