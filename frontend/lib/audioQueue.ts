import type { TtsSegment } from "@/lib/ttsParser";

type QueueOptions = {
  onPlayingChange?: (playing: boolean) => void;
  onQueuedDepthChange?: (depth: number) => void;
  onContextStateChange?: (state: AudioContextState) => void;
};

export class AudioQueue {
  private ctx: AudioContext | null = null;
  private runId = 0;
  private activeSource: AudioBufferSourceNode | null = null;
  private activeAborts = new Set<AbortController>();
  private onPlayingChange?: (playing: boolean) => void;
  private onQueuedDepthChange?: (depth: number) => void;
  private onContextStateChange?: (state: AudioContextState) => void;
  private contextEventsBound = false;
  /** Number of `enqueue()` units not yet finished (scheduled or in-flight). */
  private queuedDepth = 0;

  /** Serialized tail of `enqueue()` work — appended without `stop()`, unlike `play()`. */
  private enqueueChain: Promise<void> = Promise.resolve();

  constructor(options?: QueueOptions) {
    this.onPlayingChange = options?.onPlayingChange;
    this.onQueuedDepthChange = options?.onQueuedDepthChange;
    this.onContextStateChange = options?.onContextStateChange;
  }

  private ensureContext(): AudioContext {
    if (!this.ctx) {
      this.ctx = new AudioContext();
      this.bindContextEvents(this.ctx);
      this.onContextStateChange?.(this.ctx.state);
    }
    return this.ctx;
  }

  private bindContextEvents(ctx: AudioContext): void {
    if (this.contextEventsBound) return;
    this.contextEventsBound = true;
    ctx.addEventListener("statechange", () => {
      this.onContextStateChange?.(ctx.state);
    });
  }

  /** Read current context state without creating an AudioContext. */
  peekContextState(): AudioContextState {
    return this.ctx?.state ?? "suspended";
  }

  private bumpQueuedDepth(delta: number): void {
    this.queuedDepth = Math.max(0, this.queuedDepth + delta);
    this.onQueuedDepthChange?.(this.queuedDepth);
  }

  /**
   * Unlock playback from a user gesture (call from mic click / before async TTS).
   * Browsers may start AudioContext in "suspended" until resume() after interaction.
   */
  public prime(): void {
    const ctx = this.ensureContext();
    console.log("[SpiritOS] AudioContext State:", ctx.state);
    if (ctx.state !== "running") {
      ctx.resume().catch(() => {});
    }
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
    this.bumpQueuedDepth(1);
    this.enqueueChain = this.enqueueChain
      .catch(() => {})
      .then(() => this.runEnqueueUnit(trimmed, language))
      .finally(() => {
        this.bumpQueuedDepth(-1);
      })
      .catch((err: unknown) => {
        console.error("[SpiritOS] AudioQueue enqueue failed:", err);
      });
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
      if (ctx.state !== "running") await ctx.resume().catch(() => {});
      const buffer = await this.fetchAndDecodeSpeechSegment(text, language, currentRun, ctx);
      await this.playBuffer(buffer, currentRun);
    } finally {
      // no-op: keep playing state stable across queued sentence boundaries
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
      if (ctx.state !== "running") await ctx.resume().catch(() => {});

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
    if (!res.ok) {
      throw new Error(`TTS API ${res.status}`);
    }
    const bytes = await res.arrayBuffer();
    if (bytes.byteLength === 0) {
      console.error("[SpiritOS] CRITICAL: Audio Buffer is Corrupt or Empty");
      throw new Error("TTS returned empty audio body");
    }
    let decoded: AudioBuffer;
    try {
      decoded = await ctx.decodeAudioData(bytes.slice(0));
    } catch (e) {
      console.error("[SpiritOS] CRITICAL: Audio Buffer is Corrupt or Empty");
      throw e instanceof Error ? e : new Error(String(e));
    }
    if (runId !== this.runId) {
      throw new Error("TTS fetch aborted by newer run");
    }
    return decoded;
  }

  private async playBuffer(buffer: AudioBuffer, runId: number): Promise<void> {
    const ctx = this.ensureContext();
    if (ctx.state !== "running") {
      await ctx.resume().catch(() => {});
    }
    return new Promise<void>((resolve, reject) => {
      if (runId !== this.runId) {
        resolve();
        return;
      }
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
