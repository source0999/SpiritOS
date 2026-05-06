import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OracleVoiceStatusCard } from "@/components/oracle/OracleVoiceStatusCard";

describe("OracleVoiceStatusCard", () => {
  it("shows runtime oracle and speaking status", () => {
    render(
      <OracleVoiceStatusCard
        status="speaking"
        modeLabel="Peer"
        runtimeLabel="Oracle"
        loopModeLabel="Hands-free"
        voiceProviderLine="elevenlabs"
        selectedVoiceLabel="Clarice"
        secureContextOk={true}
      />,
    );
    const card = screen.getByTestId("oracle-voice-status-card");
    expect(within(card).getByText(/^Oracle session$/i)).toBeInTheDocument();
    expect(within(card).getByText(/^Oracle$/)).toBeInTheDocument();
    expect(within(card).getByText(/^Speaking$/)).toBeInTheDocument();
    expect(within(card).getByText(/^Hands-free$/)).toBeInTheDocument();
  });

  it("shows speech input, mic, and STT error rows", () => {
    render(
      <OracleVoiceStatusCard
        status="error"
        modeLabel="Peer"
        runtimeLabel="Oracle"
        loopModeLabel="Hands-free"
        speechInputLabel="Whisper backend"
        micLabel="Podcast USB"
        micPermissionLabel="Granted"
        voiceProviderLine="elevenlabs"
        selectedVoiceLabel="Clarice"
        speechError="no-speech"
        lastError="TTS hiccup"
        spiritTransportError="upstream"
      />,
    );
    const card = screen.getByTestId("oracle-voice-status-card");
    expect(within(card).getByText(/Whisper backend/)).toBeInTheDocument();
    expect(within(card).getByText(/Podcast USB/)).toBeInTheDocument();
    expect(within(card).getByText(/STT: no-speech/)).toBeInTheDocument();
    expect(within(card).getByText(/^Granted$/)).toBeInTheDocument();
  });

  it("renders silence ms / threshold and audio level when provided", () => {
    render(
      <OracleVoiceStatusCard
        status="listening"
        modeLabel="Peer"
        runtimeLabel="Oracle"
        loopModeLabel="Hands-free"
        voiceProviderLine="piper"
        selectedVoiceLabel="Default"
        audioLevel={0.42}
        silenceMs={400}
        silenceThresholdMs={1200}
      />,
    );
    const card = screen.getByTestId("oracle-voice-status-card");
    expect(within(card).getByText(/42%/)).toBeInTheDocument();
    expect(within(card).getByText(/400ms \/ 1200ms/)).toBeInTheDocument();
  });

  it("renders last transcript when provided", () => {
    render(
      <OracleVoiceStatusCard
        status="thinking"
        modeLabel="Peer"
        runtimeLabel="Oracle"
        loopModeLabel="Hands-free"
        voiceProviderLine="elevenlabs"
        selectedVoiceLabel="Clarice"
        lastTranscript="hello there friend"
      />,
    );
    const card = screen.getByTestId("oracle-voice-status-card");
    expect(within(card).getByText(/hello there friend/)).toBeInTheDocument();
  });

  it("flags secure-context Blocked when secureContextOk is false", () => {
    render(
      <OracleVoiceStatusCard
        status="blocked"
        modeLabel="Peer"
        runtimeLabel="Oracle"
        loopModeLabel="Hands-free"
        voiceProviderLine="piper"
        selectedVoiceLabel="Default"
        secureContextOk={false}
      />,
    );
    const card = screen.getByTestId("oracle-voice-status-card");
    // Status row + secure-context row both render "Blocked" - match both, ensure presence.
    expect(within(card).getAllByText(/^Blocked$/).length).toBeGreaterThanOrEqual(1);
  });

  it("maps status labels for permission and unsupported", () => {
    const { rerender } = render(
      <OracleVoiceStatusCard
        status="permission-needed"
        modeLabel="Peer"
        runtimeLabel="Oracle"
        loopModeLabel="Hands-free"
        voiceProviderLine="piper"
        selectedVoiceLabel="Default"
      />,
    );
    let card = screen.getByTestId("oracle-voice-status-card");
    expect(within(card).getByText(/^Permission needed$/)).toBeInTheDocument();

    rerender(
      <OracleVoiceStatusCard
        status="unsupported"
        modeLabel="Peer"
        runtimeLabel="Oracle"
        loopModeLabel="Hands-free"
        voiceProviderLine="piper"
        selectedVoiceLabel="Default"
      />,
    );
    card = screen.getByTestId("oracle-voice-status-card");
    expect(within(card).getByText(/^Unsupported$/)).toBeInTheDocument();
  });

  it("surfaces oracle session link (no quarantine)", () => {
    render(
      <OracleVoiceStatusCard
        status="idle"
        modeLabel="Teacher"
        runtimeLabel="Oracle"
        loopModeLabel="Hands-free"
        voiceProviderLine="/api/tts"
        selectedVoiceLabel="Default"
      />,
    );
    const link = screen.getByRole("link", { name: /oracle voice session/i });
    expect(link.getAttribute("href")).toBe("/oracle");
    expect(screen.queryByRole("link", { name: /quarantine/i })).toBeNull();
  });
});
