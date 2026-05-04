import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { OracleVoiceControls } from "@/components/oracle/OracleVoiceControls";
import type { UseOracleSpeechInputReturn } from "@/hooks/useOracleSpeechInput";
import type { UseTtsState } from "@/hooks/useTTS";

vi.mock("@/lib/hooks/useMounted", () => ({
  useMounted: () => true,
}));

vi.mock("@/components/chat/VoiceControl", () => ({
  VoiceControl: () => <div data-testid="oracle-voice-output-stub">voice strip</div>,
}));

function mkSpeech(over: Partial<UseOracleSpeechInputReturn> = {}): UseOracleSpeechInputReturn {
  return {
    provider: "whisper-backend",
    supported: true,
    permissionState: "unknown",
    devices: [],
    devicesEnumerateError: null,
    selectedDeviceId: null,
    selectedDeviceLabel: "Default microphone",
    setSelectedDeviceId: vi.fn(),
    isRecording: false,
    isTranscribing: false,
    isListening: false,
    audioLevel: 0,
    lastTranscript: "",
    lastError: null,
    captureBlockedHint: null,
    httpsSamePageUrl: null,
    capability: {
      mounted: true,
      isSecureContext: true,
      hasNavigator: true,
      hasMediaDevices: true,
      hasGetUserMedia: true,
      hasMediaRecorder: true,
      hasAudioContext: true,
      canUseMic: true,
      blockedReason: null,
      userMessage: "Mic ready.",
    },
    canUseMic: true,
    blockedReason: null,
    capabilityMessage: "Mic ready.",
    silenceDetected: false,
    silenceMs: 0,
    recordingStartedAt: null,
    lastRecordingDurationMs: null,
    autoStopOnSilence: true,
    setAutoStopOnSilence: vi.fn(),
    silenceThreshold: 0.035,
    setSilenceThreshold: vi.fn(),
    silenceDurationMs: 1200,
    setSilenceDurationMs: vi.fn(),
    requestPermission: vi.fn(),
    refreshDevices: vi.fn(),
    startRecording: vi.fn(),
    stopRecordingAndTranscribe: vi.fn(async () => ""),
    cancelRecording: vi.fn(),
    clearTranscript: vi.fn(),
    ...over,
  };
}

const baseTts: UseTtsState = {
  isEnabled: true,
  isPlaying: false,
  queueLength: 0,
  audioContextState: "unknown",
  startDelayMs: 0,
  sentenceGapMs: 0,
  voiceSpeed: 1,
  autoSpeakAssistant: true,
  voices: [],
  voicesStatus: "idle",
  lastError: undefined,
  lastPlaybackWallMs: undefined,
  lastUserStopAtMs: undefined,
  elevenLabsVoiceId: "v1",
  elevenLabsVoiceName: "Clarice",
  voicesSource: "elevenlabs",
  lastLatency: undefined,
};

const noop = () => {};

function renderControls(over: Partial<Parameters<typeof OracleVoiceControls>[0]> = {}) {
  const props = {
    mounted: true,
    status: "ready" as const,
    loopMode: "hands-free" as const,
    onLoopModeChange: noop,
    sessionActive: false,
    onStartSession: noop,
    onStopSession: noop,
    onFinishThought: noop,
    speech: mkSpeech({ permissionState: "granted" }),
    ttsState: baseTts,
    onToggleTtsEnabled: noop,
    onEnableAudio: noop,
    onStopSpeech: noop,
    onSpeakLatestAssistant: noop,
    onStartDelayChange: noop,
    onSentenceGapChange: noop,
    onVoiceSpeedChange: noop,
    onToggleAutoSpeak: noop,
    onRequestVoiceCatalog: noop,
    onElevenLabsVoiceChange: noop,
    transportBusy: false,
    ...over,
  };
  return render(<OracleVoiceControls {...props} />);
}

describe("OracleVoiceControls", () => {
  it('shows stable "Checking" hint until mounted', () => {
    renderControls({ mounted: false, speech: mkSpeech() });
    expect(screen.getByText(/Checking voice input/i)).toBeInTheDocument();
  });

  it("shows Start session by default", () => {
    renderControls();
    expect(screen.getByTestId("oracle-start-session")).toHaveTextContent(/Start session/i);
    expect(screen.getByText(/Whisper backend/i)).toBeInTheDocument();
  });

  it("does not show 'Voice on' or 'Tap to talk' as primary copy", () => {
    renderControls();
    expect(screen.queryByText(/Voice on/i)).toBeNull();
    expect(screen.queryByText(/Voice off/i)).toBeNull();
    expect(screen.queryByText(/^Tap to talk$/i)).toBeNull();
  });

  it("shows mic selector and Whisper backend label", () => {
    renderControls();
    expect(screen.getByLabelText(/^Microphone$/i)).toBeInTheDocument();
    expect(screen.getByText(/Whisper backend/i)).toBeInTheDocument();
  });

  it("shows audio meter when not in manual-text", () => {
    renderControls();
    expect(screen.getByTestId("oracle-audio-meter")).toBeInTheDocument();
  });

  it("shows Stop session while session is active", () => {
    renderControls({ sessionActive: true, status: "listening" });
    expect(screen.getByTestId("oracle-stop-session")).toBeInTheDocument();
  });

  it("shows Finish now only while listening/hearing", () => {
    const { rerender } = renderControls({
      status: "ready",
      sessionActive: false,
      speech: mkSpeech({ permissionState: "granted" }),
    });
    expect(screen.queryByTestId("oracle-finish-now")).toBeNull();

    rerender(
      <OracleVoiceControls
        mounted
        status="listening"
        loopMode="hands-free"
        onLoopModeChange={noop}
        sessionActive
        onStartSession={noop}
        onStopSession={noop}
        onFinishThought={noop}
        speech={mkSpeech({ permissionState: "granted", isRecording: true })}
        ttsState={baseTts}
        onToggleTtsEnabled={noop}
        onEnableAudio={noop}
        onStopSpeech={noop}
        onSpeakLatestAssistant={noop}
        onStartDelayChange={noop}
        onSentenceGapChange={noop}
        onVoiceSpeedChange={noop}
        onToggleAutoSpeak={noop}
        onRequestVoiceCatalog={noop}
        onElevenLabsVoiceChange={noop}
        transportBusy={false}
      />,
    );
    expect(screen.getByTestId("oracle-finish-now")).toBeInTheDocument();
  });

  it("shows hearing-speech label in hint when status is hearing-speech", () => {
    renderControls({
      status: "hearing-speech",
      sessionActive: true,
      speech: mkSpeech({
        permissionState: "granted",
        isRecording: true,
        audioLevel: 0.4,
      }),
    });
    expect(screen.getByText(/Auto-send after/i)).toBeInTheDocument();
  });

  it("shows secure-context warning when capability is blocked by insecure context", () => {
    renderControls({
      status: "blocked",
      speech: mkSpeech({
        supported: false,
        canUseMic: false,
        permissionState: "unsupported",
        capability: {
          mounted: true,
          isSecureContext: false,
          hasNavigator: true,
          hasMediaDevices: false,
          hasGetUserMedia: false,
          hasMediaRecorder: true,
          hasAudioContext: true,
          canUseMic: false,
          blockedReason: "insecure-context",
          userMessage:
            "Mic access is blocked on this HTTP address. Use localhost, 127.0.0.1, or HTTPS.",
        },
        captureBlockedHint:
          "Mic access is blocked on this HTTP address. Use localhost, 127.0.0.1, or HTTPS.",
      }),
    });
    expect(screen.getByTestId("oracle-secure-context-warning")).toBeInTheDocument();
    // Start session button is rendered but disabled.
    const start = screen.getByTestId("oracle-start-session") as HTMLButtonElement;
    expect(start.disabled).toBe(true);
  });

  it("shows HTTPS upgrade CTA when httpsSamePageUrl is set in insecure context", () => {
    renderControls({
      status: "blocked",
      speech: mkSpeech({
        supported: false,
        canUseMic: false,
        permissionState: "unsupported",
        capability: {
          mounted: true,
          isSecureContext: false,
          hasNavigator: true,
          hasMediaDevices: false,
          hasGetUserMedia: false,
          hasMediaRecorder: true,
          hasAudioContext: true,
          canUseMic: false,
          blockedReason: "insecure-context",
          userMessage: "Mic access is blocked on this HTTP address.",
        },
        httpsSamePageUrl: "https://10.0.0.186:3000/oracle",
      }),
    });
    expect(screen.getByTestId("oracle-https-upgrade-cta")).toHaveAttribute(
      "href",
      "https://10.0.0.186:3000/oracle",
    );
  });

  it("fires loop mode change", () => {
    const onMode = vi.fn();
    renderControls({ onLoopModeChange: onMode });
    fireEvent.change(screen.getByLabelText(/^Session mode$/i), {
      target: { value: "manual-text" },
    });
    expect(onMode).toHaveBeenCalledWith("manual-text");
  });

  it("text-fallback toggle drives loopMode change", () => {
    const onMode = vi.fn();
    renderControls({ onLoopModeChange: onMode });
    const toggle = screen.getByTestId("oracle-text-fallback-toggle") as HTMLInputElement;
    fireEvent.click(toggle);
    expect(onMode).toHaveBeenCalledWith("manual-text");
  });

  it("silence duration select renders preset options", () => {
    renderControls();
    const sel = screen.getByTestId("oracle-silence-duration") as HTMLSelectElement;
    const values = Array.from(sel.options).map((o) => o.value);
    expect(values).toEqual(["800", "1200", "1800", "2500"]);
  });

  it("sensitivity select fires setSilenceThreshold", () => {
    const setSilenceThreshold = vi.fn();
    renderControls({
      speech: mkSpeech({ permissionState: "granted", setSilenceThreshold }),
    });
    fireEvent.change(screen.getByTestId("oracle-sensitivity"), {
      target: { value: "high" },
    });
    expect(setSilenceThreshold).toHaveBeenCalled();
  });
});
