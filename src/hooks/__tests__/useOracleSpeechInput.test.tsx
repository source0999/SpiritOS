// @vitest-environment jsdom
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useOracleSpeechInput } from "@/hooks/useOracleSpeechInput";

type MediaRecorderInstance = {
  state: "inactive" | "recording";
  start: ReturnType<typeof vi.fn>;
  stop: ReturnType<typeof vi.fn>;
  ondataavailable: ((e: BlobEvent) => void) | null;
  onstop: ((e: Event) => void) | null;
  onerror: ((e: Event) => void) | null;
  mimeType: string;
};

const createdRecorders: MediaRecorderInstance[] = [];

function makeAnalyserMock(getLevelByte: () => number) {
  return {
    fftSize: 256,
    frequencyBinCount: 4,
    getByteFrequencyData(out: Uint8Array) {
      const v = Math.max(0, Math.min(255, Math.round(getLevelByte())));
      for (let i = 0; i < out.length; i++) out[i] = v;
    },
  } as unknown as AnalyserNode;
}

let levelByte = 200;
function setLevel(level0to1: number) {
  levelByte = Math.max(0, Math.min(255, Math.round(level0to1 * 255)));
}

function installBrowserGlobals() {
  Object.defineProperty(window, "isSecureContext", {
    value: true,
    configurable: true,
  });

  vi.stubGlobal(
    "MediaRecorder",
    class {
      static isTypeSupported() {
        return true;
      }
      state: "inactive" | "recording" = "inactive";
      mimeType = "audio/webm";
      ondataavailable: ((e: BlobEvent) => void) | null = null;
      onstop: ((e: Event) => void) | null = null;
      onerror: ((e: Event) => void) | null = null;
      start = vi.fn(() => {
        this.state = "recording";
        // Simulate data slicing - ensures the chunks array is non-empty by stop time.
        const fakeData = new Blob(["a".repeat(64)], { type: "audio/webm" });
        const ev = { data: fakeData } as unknown as BlobEvent;
        queueMicrotask(() => this.ondataavailable?.(ev));
      });
      stop = vi.fn(() => {
        this.state = "inactive";
        queueMicrotask(() => this.onstop?.(new Event("stop")));
      });
      constructor() {
        createdRecorders.push(this as unknown as MediaRecorderInstance);
      }
    },
  );

  vi.stubGlobal("navigator", {
    ...navigator,
    mediaDevices: {
      getUserMedia: vi.fn().mockResolvedValue({
        getTracks: () => [{ stop: vi.fn() }],
      }),
      enumerateDevices: vi.fn().mockResolvedValue([]),
    },
  });

  class AudioContextMock {
    createMediaStreamSource() {
      return { connect: () => {} };
    }
    createAnalyser() {
      return makeAnalyserMock(() => levelByte);
    }
    close() {
      return Promise.resolve();
    }
  }
  vi.stubGlobal("AudioContext", AudioContextMock);
  Object.defineProperty(window, "AudioContext", {
    value: AudioContextMock,
    configurable: true,
  });

  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ ok: true, text: "hello world" }),
  }) as unknown as typeof fetch;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

describe("useOracleSpeechInput", () => {
  beforeEach(() => {
    createdRecorders.length = 0;
    localStorage.clear();
    vi.unstubAllGlobals();
    installBrowserGlobals();
    setLevel(0.5);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("imports without throwing (SSR-safe module)", async () => {
    const { useOracleSpeechInput: hook } = await import("@/hooks/useOracleSpeechInput");
    expect(typeof hook).toBe("function");
  });

  it("becomes supported after mount when APIs exist", async () => {
    const { result } = renderHook(() => useOracleSpeechInput());
    await waitFor(() => expect(result.current.supported).toBe(true));
    expect(result.current.canUseMic).toBe(true);
    expect(result.current.blockedReason).toBeNull();
  });

  it("reports insecure context as blocked after mount", async () => {
    Object.defineProperty(window, "isSecureContext", { value: false, configurable: true });
    const { result } = renderHook(() => useOracleSpeechInput());
    await waitFor(() => expect(result.current.capability.mounted).toBe(true));
    expect(result.current.canUseMic).toBe(false);
    expect(result.current.blockedReason).toBe("insecure-context");
    expect(result.current.captureBlockedHint).toMatch(/HTTP/);
  });

  it("auto-stops on silence after threshold and submits transcript", async () => {
    const onAutoStop = vi.fn();
    const { result } = renderHook(() =>
      useOracleSpeechInput({
        silenceThreshold: 0.1,
        silenceDurationMs: 250,
        minRecordingMs: 100,
        onAutoStop,
      }),
    );
    await waitFor(() => expect(result.current.canUseMic).toBe(true));

    setLevel(0.4);
    await act(async () => {
      await result.current.startRecording();
    });
    expect(result.current.isRecording).toBe(true);

    await act(async () => {
      await sleep(300);
    });

    setLevel(0.0);
    await act(async () => {
      await sleep(700);
    });

    await waitFor(() => expect(result.current.isRecording).toBe(false), { timeout: 2000 });
    expect(onAutoStop).toHaveBeenCalledWith("silence");
  });

  it("does not auto-stop before minRecordingMs", async () => {
    const onAutoStop = vi.fn();
    const { result } = renderHook(() =>
      useOracleSpeechInput({
        silenceThreshold: 0.1,
        silenceDurationMs: 80,
        minRecordingMs: 3000,
        onAutoStop,
      }),
    );
    await waitFor(() => expect(result.current.canUseMic).toBe(true));

    setLevel(0.4);
    await act(async () => {
      await result.current.startRecording();
    });
    await act(async () => {
      await sleep(200);
    });
    setLevel(0.0);
    await act(async () => {
      await sleep(800);
    });

    expect(result.current.isRecording).toBe(true);
    expect(onAutoStop).not.toHaveBeenCalled();
  });

  it("voice above threshold resets silence timer", async () => {
    const { result } = renderHook(() =>
      useOracleSpeechInput({
        silenceThreshold: 0.1,
        silenceDurationMs: 400,
        minRecordingMs: 100,
      }),
    );
    await waitFor(() => expect(result.current.canUseMic).toBe(true));

    setLevel(0.5);
    await act(async () => {
      await result.current.startRecording();
    });

    // Speak.
    await act(async () => {
      await sleep(300);
    });
    // Quick gap shorter than the 400ms threshold.
    setLevel(0.0);
    await act(async () => {
      await sleep(150);
    });
    // Speak again.
    setLevel(0.5);
    await act(async () => {
      await sleep(400);
    });

    expect(result.current.isRecording).toBe(true);
  });

  it("stopRecordingAndTranscribe is idempotent", async () => {
    const { result } = renderHook(() =>
      useOracleSpeechInput({
        silenceThreshold: 0.05,
        silenceDurationMs: 5000,
        minRecordingMs: 200,
      }),
    );
    await waitFor(() => expect(result.current.canUseMic).toBe(true));

    setLevel(0.5);
    await act(async () => {
      await result.current.startRecording();
    });
    await act(async () => {
      await sleep(150);
    });

    let firstResult = "x";
    let secondResult = "x";
    await act(async () => {
      const [a, b] = await Promise.all([
        result.current.stopRecordingAndTranscribe(),
        result.current.stopRecordingAndTranscribe(),
      ]);
      firstResult = a;
      secondResult = b;
    });

    const submitted = (global.fetch as ReturnType<typeof vi.fn>).mock.calls.length;
    expect(submitted).toBe(1);
    expect([firstResult, secondResult].filter((s) => s.length > 0)).toHaveLength(1);
  });

  it("max-recording auto-stop fires after maxRecordingMs", async () => {
    const onAutoStop = vi.fn();
    const { result } = renderHook(() =>
      useOracleSpeechInput({
        silenceThreshold: 1,
        silenceDurationMs: 999_999,
        minRecordingMs: 100,
        maxRecordingMs: 400,
        onAutoStop,
      }),
    );
    await waitFor(() => expect(result.current.canUseMic).toBe(true));

    setLevel(0.9);
    await act(async () => {
      await result.current.startRecording();
    });

    await act(async () => {
      await sleep(700);
    });

    await waitFor(() => expect(result.current.isRecording).toBe(false), { timeout: 2000 });
    expect(onAutoStop).toHaveBeenCalledWith("max-duration");
  });

  it("cleanup cancels meter loop on unmount", async () => {
    const { result, unmount } = renderHook(() => useOracleSpeechInput());
    await waitFor(() => expect(result.current.canUseMic).toBe(true));

    setLevel(0.5);
    await act(async () => {
      await result.current.startRecording();
    });
    expect(result.current.isRecording).toBe(true);

    unmount();
    await sleep(150);
    // No throw and no further fetch calls.
    expect((global.fetch as ReturnType<typeof vi.fn>).mock.calls.length).toBe(0);
  });
});
