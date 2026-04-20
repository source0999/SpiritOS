import type { TtsSegment } from "@/lib/ttsParser";

type QueueOptions = {
  onPlayingChange?: (playing: boolean) => void;
};

export class AudioQueue {
  private ctx: AudioContext | null = null;
  private runId = 0;
  private source: AudioBufferSourceNode | null = null;
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
      for (const segment of segments) {
        if (currentRun !== this.runId) return;

        if (segment.type === "pause") {
          await new Promise<void>((resolve) => {
            window.setTimeout(resolve, segment.ms);
          });
          continue;
        }

        const fetchTts = async () =>
          fetch("/api/tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              text: segment.text,
              language,
            }),
          });

        let res = await fetchTts().catch(() => null);
        if (!res || !res.ok) {
          // #region agent log
          fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
            body: JSON.stringify({
              sessionId: "7d6688",
              runId: "tts-debug-3",
              hypothesisId: "H10",
              location: "audioQueue.ts:play",
              message: "TTS API first attempt failed; retrying once",
              data: { status: res?.status ?? null, speechTextLen: segment.text.length },
              timestamp: Date.now(),
            }),
          }).catch(() => {});
          // #endregion
          res = await fetchTts().catch(() => null);
        }
        if (!res) throw new Error("TTS API network failure");
        // #region agent log
        fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
          body: JSON.stringify({
            sessionId: "7d6688",
            runId: "tts-debug-1",
            hypothesisId: "H1",
            location: "audioQueue.ts:play",
            message: "TTS API response",
            data: { ok: res.ok, status: res.status, speechTextLen: segment.text.length },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        if (!res.ok) throw new Error(`TTS API ${res.status}`);

        const arrayBuffer = await res.arrayBuffer();
        const ctx = this.ensureContext();
        if (ctx.state === "suspended") await ctx.resume();
        // #region agent log
        fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
          body: JSON.stringify({
            sessionId: "7d6688",
            runId: "tts-debug-1",
            hypothesisId: "H3",
            location: "audioQueue.ts:play",
            message: "Audio context state before decode",
            data: { ctxState: ctx.state, bytes: arrayBuffer.byteLength },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        const audioBuffer = await ctx.decodeAudioData(arrayBuffer.slice(0));
        // #region agent log
        fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
          body: JSON.stringify({
            sessionId: "7d6688",
            runId: "tts-debug-2",
            hypothesisId: "H7",
            location: "audioQueue.ts:play",
            message: "Audio decoded successfully",
            data: {
              duration: audioBuffer.duration,
              sampleRate: audioBuffer.sampleRate,
              channels: audioBuffer.numberOfChannels,
            },
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        await this.playBuffer(audioBuffer, currentRun);
      }
    } finally {
      if (currentRun === this.runId) {
        this.onPlayingChange?.(false);
      }
    }
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
