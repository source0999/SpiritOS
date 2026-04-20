import type { TtsSegment } from "@/lib/ttsParser";

type QueueOptions = {
  onPlayingChange?: (playing: boolean) => void;
};

export class AudioQueue {
  private ctx: AudioContext | null = null;
  private runId = 0;
  private source: AudioBufferSourceNode | null = null;
  private activeSources = new Set<AudioBufferSourceNode>();
  private activeAbort: AbortController | null = null;
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
    this.activeAbort?.abort();
    this.activeAbort = null;
    for (const src of this.activeSources) {
      try {
        src.stop();
      } catch {
        // ignore stale stop errors
      }
    }
    this.activeSources.clear();
    if (this.source) {
      try {
        this.source.stop();
      } catch {
        // ignore stale stop errors
      }
      this.source = null;
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
        return this.synthesizeSpeechSegment(seg.text, language, currentRun, ctx);
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

  private async synthesizeSpeechSegment(
    text: string,
    language: string,
    runId: number,
    ctx: AudioContext,
  ): Promise<AudioBuffer> {
    const abortCtrl = new AbortController();
    this.activeAbort = abortCtrl;
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language }),
      signal: abortCtrl.signal,
    });
    if (!res.ok) throw new Error(`TTS API ${res.status}`);
    if (!res.body) throw new Error("TTS stream missing body");

    const reader = res.body.getReader();
    const chunks: Uint8Array[] = [];
    let total = 0;
    let firstChunkAt = 0;
    let firstChunkBytes = 0;

    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!value || !value.length) continue;
      if (!firstChunkAt) {
        firstChunkAt = Date.now();
        firstChunkBytes = value.length;
        console.info("[Spirit TTS] TTS stream first chunk received", { bytes: value.length, t: firstChunkAt });
        // #region agent log
        fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
          body: JSON.stringify({
            sessionId: "7d6688",
            runId: "tts-stream-2",
            hypothesisId: "S4",
            location: "audioQueue.ts:synthesizeSpeechSegment",
            message: "TTS stream first chunk received",
            data: { bytes: value.length, textLen: text.length },
            timestamp: firstChunkAt,
          }),
        }).catch(() => {});
        // #endregion
      }
      chunks.push(value);
      total += value.length;
    }

    if (runId !== this.runId) {
      throw new Error("TTS synthesis aborted by newer run");
    }

    const all = new Uint8Array(total);
    let offset = 0;
    for (const c of chunks) {
      all.set(c, offset);
      offset += c.length;
    }
    const audioBuffer = await ctx.decodeAudioData(all.buffer.slice(0));
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "tts-stream-2",
        hypothesisId: "S5",
        location: "audioQueue.ts:synthesizeSpeechSegment",
        message: "Speech segment decoded",
        data: {
          textLen: text.length,
          totalBytes: total,
          firstChunkBytes,
          duration: audioBuffer.duration,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    return audioBuffer;
  }

  private playBuffer(buffer: AudioBuffer, runId: number): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      if (runId !== this.runId) {
        // #region agent log
        fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
          body: JSON.stringify({
            sessionId: "7d6688",
            runId: "tts-debug-3",
            hypothesisId: "H11",
            location: "audioQueue.ts:playBuffer",
            message: "Playback skipped due runId mismatch (interrupted by newer speak)",
            data: { incomingRunId: runId, currentRunId: this.runId },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        resolve();
        return;
      }

      const ctx = this.ensureContext();
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      this.source = source;
      // #region agent log
      fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
        body: JSON.stringify({
          sessionId: "7d6688",
          runId: "tts-debug-2",
          hypothesisId: "H8",
          location: "audioQueue.ts:playBuffer",
          message: "Audio source created",
          data: {
            ctxState: ctx.state,
            duration: buffer.duration,
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion

      source.onended = () => {
        if (this.source === source) this.source = null;
        // #region agent log
        fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
          body: JSON.stringify({
            sessionId: "7d6688",
            runId: "tts-debug-2",
            hypothesisId: "H8",
            location: "audioQueue.ts:playBuffer",
            message: "Audio source ended",
            data: {
              runId,
            },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        resolve();
      };

      try {
        source.start(0);
        // #region agent log
        fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
          body: JSON.stringify({
            sessionId: "7d6688",
            runId: "tts-debug-2",
            hypothesisId: "H8",
            location: "audioQueue.ts:playBuffer",
            message: "Audio source started",
            data: { runId },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
      } catch (e) {
        if (this.source === source) this.source = null;
        // #region agent log
        fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
          body: JSON.stringify({
            sessionId: "7d6688",
            runId: "tts-debug-2",
            hypothesisId: "H8",
            location: "audioQueue.ts:playBuffer",
            message: "Audio source start failed",
            data: { error: e instanceof Error ? e.message : String(e) },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        reject(e);
      }
    });
  }
}
