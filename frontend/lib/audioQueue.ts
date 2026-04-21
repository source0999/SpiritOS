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

  /** Serialized tail of `enqueue()` work — appended without `stop()`, unlike `play()`. */
  private enqueueChain: Promise<void> = Promise.resolve();

  constructor(options?: QueueOptions) {
    this.onPlayingChange = options?.onPlayingChange;
  }

  private ensureContext(): AudioContext {
    if (!this.ctx) this.ctx = new AudioContext();
    return this.ctx;
  }

  stop(): void {
    this.runId += 1;
    this.enqueueChain = Promise.resolve();
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

  /**
   * Queue a single utterance after any prior `enqueue()` work, without calling
   * `stop()` — so streaming sentences play back-to-back.
   */
  enqueue(text: string, language = "en"): void {
    const trimmed = text.trim();
    if (!trimmed) return;
    this.enqueueChain = this.enqueueChain
      .catch(() => {})
      .then(() => this.runEnqueueUnit(trimmed, language));
  }

  /** Await until all `enqueue()` units scheduled so far have finished. */
  drain(): Promise<void> {
    return this.enqueueChain.catch(() => {}).then(() => undefined);
  }

  private async runEnqueueUnit(text: string, language: string): Promise<void> {
    const currentRun = this.runId;
    this.onPlayingChange?.(true);
    try {
      const ctx = this.ensureContext();
      if (ctx.state === "suspended") await ctx.resume();
      const buffer = await this.fetchAndDecodeSpeechSegment(text, language, currentRun, ctx);
      await this.playBuffer(buffer, currentRun);
    } finally {
      if (currentRun === this.runId) {
        this.onPlayingChange?.(false);
      }
    }
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
    const abortCtrl = new AbortController();
    this.activeAborts.add(abortCtrl);
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language }),
      signal: abortCtrl.signal,
    });
    this.activeAborts.delete(abortCtrl);
    if (!res.ok) throw new Error(`TTS API ${res.status}`);
    const bytes = await res.arrayBuffer();
    const decoded = await ctx.decodeAudioData(bytes.slice(0));
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
