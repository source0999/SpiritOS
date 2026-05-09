import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AudioQueue } from "@/lib/tts/audio-queue";

describe("AudioQueue interrupt (Prompt 9G)", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>(() => {})),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("aborts the in-flight fetch signal when a new speak() interrupts", async () => {
    const q = new AudioQueue({});
    q.speak("first chunk of speech", { interrupt: true });
    for (let i = 0; i < 24; i += 1) {
      await Promise.resolve();
    }
    const firstInit = vi.mocked(fetch).mock.calls[0]?.[1] as RequestInit | undefined;
    expect(firstInit?.signal).toBeDefined();
    const sig = firstInit!.signal!;
    expect(sig.aborted).toBe(false);

    q.speak("second chunk replaces session", { interrupt: true });
    expect(sig.aborted).toBe(true);
  });

  it("stop() aborts active fetch", async () => {
    const q = new AudioQueue({});
    q.speak("hold the line", { interrupt: true });
    for (let i = 0; i < 24; i += 1) {
      await Promise.resolve();
    }
    const firstInit = vi.mocked(fetch).mock.calls[0]?.[1] as RequestInit | undefined;
    const sig = firstInit?.signal;
    expect(sig).toBeDefined();
    q.stop();
    expect(sig!.aborted).toBe(true);
  });

  it("second speak schedules a new fetch without waiting for the first hang to resolve", async () => {
    const q = new AudioQueue({});
    q.speak("aaaaaaaaaaaaaaaa", { interrupt: true });
    for (let i = 0; i < 40; i += 1) await Promise.resolve();
    expect(fetch).toHaveBeenCalledTimes(1);

    q.speak("bbbbbbbbbbbbbbbb", { interrupt: true });
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
    expect(fetch).toHaveBeenCalledTimes(2);
  });
});
