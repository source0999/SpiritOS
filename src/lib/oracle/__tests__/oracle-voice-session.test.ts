import { describe, expect, it } from "vitest";

import {
  appendOracleVoiceEvent,
  capOracleVoiceEvents,
  createOracleVoiceEvent,
  DEFAULT_ORACLE_LOOP_MODE,
  deriveOracleVoiceStatus,
  oracleSessionStatusHint,
  oracleSessionStatusLabel,
  shouldOracleAutoRestartListening,
  type DeriveOracleVoiceStatusInput,
  type OracleVoiceSessionStatus,
} from "@/lib/oracle/oracle-voice-session";

function base(over: Partial<DeriveOracleVoiceStatusInput>): DeriveOracleVoiceStatusInput {
  return {
    inputMode: "hands-free",
    recordingSupported: true,
    requestingMic: false,
    micPermission: "granted",
    isListening: false,
    isTranscribing: false,
    isBusy: false,
    isPlaying: false,
    queueLength: 0,
    ...over,
  };
}

describe("deriveOracleVoiceStatus", () => {
  it("hands-free is the default loop mode", () => {
    expect(DEFAULT_ORACLE_LOOP_MODE).toBe("hands-free");
  });

  it("returns blocked when capability blocked", () => {
    expect(deriveOracleVoiceStatus(base({ capabilityBlocked: true }))).toBe("blocked");
  });

  it("returns requesting-mic when flag set", () => {
    expect(deriveOracleVoiceStatus(base({ requestingMic: true }))).toBe("requesting-mic");
  });

  it("returns permission-needed when mic is not granted", () => {
    expect(
      deriveOracleVoiceStatus(
        base({ micPermission: "unknown", recordingSupported: true, requestingMic: false }),
      ),
    ).toBe("permission-needed");
  });

  it("returns ready when permission granted and idle", () => {
    expect(deriveOracleVoiceStatus(base({}))).toBe("ready");
  });

  it("listening when recording with no speech", () => {
    expect(deriveOracleVoiceStatus(base({ isListening: true }))).toBe("listening");
  });

  it("hearing-speech when recording with speech detected", () => {
    expect(
      deriveOracleVoiceStatus(base({ isListening: true, hearingSpeech: true })),
    ).toBe("hearing-speech");
  });

  it("silence-detected beats listening", () => {
    expect(
      deriveOracleVoiceStatus(
        base({ isListening: true, hearingSpeech: true, silenceDetected: true }),
      ),
    ).toBe("silence-detected");
  });

  it("transcribing beats listening", () => {
    expect(
      deriveOracleVoiceStatus(base({ isTranscribing: true, isListening: true })),
    ).toBe("transcribing");
  });

  it("thinking beats ready", () => {
    expect(deriveOracleVoiceStatus(base({ isBusy: true }))).toBe("thinking");
  });

  it("speaking beats ready", () => {
    expect(deriveOracleVoiceStatus(base({ isPlaying: true }))).toBe("speaking");
  });

  it("restarting beats listening when not yet recording", () => {
    expect(deriveOracleVoiceStatus(base({ restarting: true }))).toBe("restarting");
  });

  it("error from tts", () => {
    expect(deriveOracleVoiceStatus(base({ ttsLastError: "x" }))).toBe("error");
  });

  it("unsupported when no MediaRecorder path", () => {
    expect(deriveOracleVoiceStatus(base({ recordingSupported: false }))).toBe("unsupported");
  });

  it("manual-text skips capture gates", () => {
    expect(
      deriveOracleVoiceStatus(
        base({
          inputMode: "manual-text",
          recordingSupported: false,
          micPermission: "unknown",
        }),
      ),
    ).toBe("idle");
  });

  it("returns spirit transport error", () => {
    expect(deriveOracleVoiceStatus(base({ spiritTransportError: "dead" }))).toBe("error");
  });

  it("latches stopped when sessionStopped without active session", () => {
    expect(
      deriveOracleVoiceStatus(
        base({ sessionStopped: true, sessionActive: false, micPermission: "granted" }),
      ),
    ).toBe("stopped");
  });
});

describe("oracle status labels + hints", () => {
  it("labels are human readable", () => {
    const statuses: OracleVoiceSessionStatus[] = [
      "idle",
      "blocked",
      "requesting-mic",
      "permission-needed",
      "ready",
      "listening",
      "hearing-speech",
      "silence-detected",
      "transcribing",
      "thinking",
      "speaking",
      "restarting",
      "stopped",
      "unsupported",
      "error",
    ];
    for (const s of statuses) {
      expect(oracleSessionStatusLabel(s).length).toBeGreaterThan(0);
      expect(oracleSessionStatusHint(s).length).toBeGreaterThan(0);
    }
  });
});

describe("shouldOracleAutoRestartListening", () => {
  function rbase(over: Partial<Parameters<typeof shouldOracleAutoRestartListening>[0]> = {}) {
    return {
      sessionActive: true,
      inputMode: "hands-free" as const,
      isBusy: false,
      isPlaying: false,
      queueLength: 0,
      isTranscribing: false,
      isListening: false,
      micPermission: "granted" as const,
      ...over,
    };
  }

  it("restarts on a clean idle hands-free session", () => {
    expect(shouldOracleAutoRestartListening(rbase())).toBe(true);
  });

  it("does not restart when session inactive", () => {
    expect(shouldOracleAutoRestartListening(rbase({ sessionActive: false }))).toBe(false);
  });

  it("does not restart in push-to-talk", () => {
    expect(shouldOracleAutoRestartListening(rbase({ inputMode: "push-to-talk" }))).toBe(false);
  });

  it("does not restart when busy", () => {
    expect(shouldOracleAutoRestartListening(rbase({ isBusy: true }))).toBe(false);
  });

  it("does not restart while speaking", () => {
    expect(shouldOracleAutoRestartListening(rbase({ isPlaying: true }))).toBe(false);
  });

  it("does not restart with queued tts", () => {
    expect(shouldOracleAutoRestartListening(rbase({ queueLength: 2 }))).toBe(false);
  });

  it("does not restart while transcribing", () => {
    expect(shouldOracleAutoRestartListening(rbase({ isTranscribing: true }))).toBe(false);
  });

  it("does not restart when capability blocked", () => {
    expect(shouldOracleAutoRestartListening(rbase({ capabilityBlocked: true }))).toBe(false);
  });

  it("does not restart with transport error", () => {
    expect(shouldOracleAutoRestartListening(rbase({ spiritTransportError: "boom" }))).toBe(false);
  });
});

describe("oracle voice events", () => {
  it("caps events", () => {
    const rows = Array.from({ length: 100 }, (_, i) =>
      createOracleVoiceEvent({
        type: "message_submitted",
        label: String(i),
      }),
    );
    const capped = capOracleVoiceEvents(rows, 12);
    expect(capped).toHaveLength(12);
    expect(capped[0]?.label).toBe("88");
  });

  it("appendOracleVoiceEvent adds row", () => {
    const a = createOracleVoiceEvent({ type: "session_ready", label: "go" });
    const next = appendOracleVoiceEvent([], a);
    expect(next).toHaveLength(1);
  });
});
