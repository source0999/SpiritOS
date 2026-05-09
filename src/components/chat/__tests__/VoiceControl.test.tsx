import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { VoiceControl } from "@/components/chat/VoiceControl";
import type { UseTtsState } from "@/hooks/useTTS";

function baseState(p: Partial<UseTtsState> = {}): UseTtsState {
  return {
    isPlaying: false,
    queueLength: 0,
    audioContextState: "running",
    isEnabled: false,
    startDelayMs: 0,
    sentenceGapMs: 150,
    autoSpeakAssistant: false,
    voiceSpeed: 1.12,
    elevenLabsVoiceId: null,
    elevenLabsVoiceName: null,
    voices: [],
    voicesSource: undefined,
    voicesAllowlistMode: undefined,
    voicesWarnings: [],
    voicesStatus: "idle",
    voicesError: undefined,
    ...p,
  };
}

function renderVoice(overrides: Partial<UseTtsState> = {}) {
  const state = baseState(overrides);
  return render(
    <VoiceControl
      state={state}
      onToggleEnabled={vi.fn()}
      onEnableAudio={vi.fn()}
      onStop={vi.fn()}
      onSpeakLatestAssistant={vi.fn()}
      onStartDelayChange={vi.fn()}
      onSentenceGapChange={vi.fn()}
      onVoiceSpeedChange={vi.fn()}
      onRequestVoiceCatalog={vi.fn()}
      onElevenLabsVoiceChange={vi.fn()}
      onToggleAutoSpeak={vi.fn()}
    />,
  );
}

describe("VoiceControl", () => {
  it("does not surface Prime in UI copy", () => {
    renderVoice();
    expect(screen.queryByText(/Prime/i)).not.toBeInTheDocument();
  });

  it("default UI does not show delay/gap selects", () => {
    renderVoice();
    expect(screen.queryByLabelText(/Delay before voice starts/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Pause between speech chunks/i)).not.toBeInTheDocument();
  });

  it("Voice settings reveals Enable audio when context suspended", async () => {
    renderVoice({ audioContextState: "suspended" });
    fireEvent.click(screen.getByRole("button", { name: /Voice settings/i }));
    await waitFor(() => {
      expect(
        within(document.body).getByRole("button", { name: /^Enable audio$/i }),
      ).toBeInTheDocument();
    });
  });

  it("Voice settings shows friendly last session when latency set", async () => {
    renderVoice({
      lastLatency: {
        fetchMs: 10,
        decodeMs: 2,
        totalMs: 5700,
        timeToFirstAudioMs: 5700,
        provider: "elevenlabs",
        upstreamMs: 420,
        playbackMode: "html-audio",
        voiceName: "Clarice",
        speed: 1.12,
      },
    });
    fireEvent.click(screen.getByRole("button", { name: /Voice settings/i }));
    await waitFor(() => {
      const root = within(document.body);
      expect(root.getByText(/Audio started in 5\.7s/)).toBeInTheDocument();
      expect(root.getByText(/ElevenLabs responded in 0\.4s/)).toBeInTheDocument();
      expect(root.getByText(/Browser playback:.*HTMLAudio/)).toBeInTheDocument();
      expect(root.getByText(/Voice: Clarice/)).toBeInTheDocument();
    });
  });

  it("Speak calls latest handler", () => {
    const onLatest = vi.fn();
    render(
      <VoiceControl
        state={baseState({ isEnabled: true })}
        onToggleEnabled={vi.fn()}
        onEnableAudio={vi.fn()}
        onStop={vi.fn()}
        onSpeakLatestAssistant={onLatest}
        onStartDelayChange={vi.fn()}
        onSentenceGapChange={vi.fn()}
        onVoiceSpeedChange={vi.fn()}
        onRequestVoiceCatalog={vi.fn()}
        onElevenLabsVoiceChange={vi.fn()}
        onToggleAutoSpeak={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /^Speak$/i }));
    expect(onLatest).toHaveBeenCalledTimes(1);
  });

  it("shows Stop when playing or queued", () => {
    const { rerender } = render(
      <VoiceControl
        state={baseState({ isPlaying: false, queueLength: 0 })}
        onToggleEnabled={vi.fn()}
        onEnableAudio={vi.fn()}
        onStop={vi.fn()}
        onSpeakLatestAssistant={vi.fn()}
        onStartDelayChange={vi.fn()}
        onSentenceGapChange={vi.fn()}
        onVoiceSpeedChange={vi.fn()}
        onRequestVoiceCatalog={vi.fn()}
        onElevenLabsVoiceChange={vi.fn()}
        onToggleAutoSpeak={vi.fn()}
      />,
    );
    expect(screen.queryByRole("button", { name: /^Stop$/i })).not.toBeInTheDocument();
    rerender(
      <VoiceControl
        state={baseState({ isPlaying: true, queueLength: 0 })}
        onToggleEnabled={vi.fn()}
        onEnableAudio={vi.fn()}
        onStop={vi.fn()}
        onSpeakLatestAssistant={vi.fn()}
        onStartDelayChange={vi.fn()}
        onSentenceGapChange={vi.fn()}
        onVoiceSpeedChange={vi.fn()}
        onRequestVoiceCatalog={vi.fn()}
        onElevenLabsVoiceChange={vi.fn()}
        onToggleAutoSpeak={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /^Stop$/i })).toBeInTheDocument();
  });

  it("Voice settings shows Voice speed when handler provided", async () => {
    const onSpeed = vi.fn();
    render(
      <VoiceControl
        state={baseState({ voiceSpeed: 1.08 })}
        onToggleEnabled={vi.fn()}
        onEnableAudio={vi.fn()}
        onStop={vi.fn()}
        onSpeakLatestAssistant={vi.fn()}
        onStartDelayChange={vi.fn()}
        onSentenceGapChange={vi.fn()}
        onVoiceSpeedChange={onSpeed}
        onRequestVoiceCatalog={vi.fn()}
        onElevenLabsVoiceChange={vi.fn()}
        onToggleAutoSpeak={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Voice settings/i }));
    const sel = await waitFor(() =>
      within(document.body).getByLabelText(/Voice speed/i),
    );
    expect(sel).toBeInTheDocument();
    fireEvent.change(sel, { target: { value: "1.18" } });
    expect(onSpeed).toHaveBeenCalledWith(1.18);
  });

  it("debug timing disclosure reveals delay controls", async () => {
    renderVoice();
    fireEvent.click(screen.getByRole("button", { name: /Voice settings/i }));
    await waitFor(() => {
      expect(
        within(document.body).getByRole("button", { name: /Debug voice timing/i }),
      ).toBeInTheDocument();
    });
    fireEvent.click(
      within(document.body).getByRole("button", { name: /Debug voice timing/i }),
    );
    expect(
      within(document.body).getByLabelText(/Delay before voice starts/i),
    ).toBeInTheDocument();
    expect(
      within(document.body).getByLabelText(/Pause between speech chunks/i),
    ).toBeInTheDocument();
  });
});

function renderMobileBar(overrides: Partial<UseTtsState> = {}) {
  const state = baseState(overrides);
  return render(
    <VoiceControl
      variant="mobile-bar"
      state={state}
      onToggleEnabled={vi.fn()}
      onEnableAudio={vi.fn()}
      onStop={vi.fn()}
      onSpeakLatestAssistant={vi.fn()}
      onStartDelayChange={vi.fn()}
      onSentenceGapChange={vi.fn()}
      onVoiceSpeedChange={vi.fn()}
      onRequestVoiceCatalog={vi.fn()}
      onElevenLabsVoiceChange={vi.fn()}
      onToggleAutoSpeak={vi.fn()}
    />,
  );
}

describe("VoiceControl mobile-bar", () => {
  it("does not surface delay/gap controls until the Voice sheet is opened", () => {
    renderMobileBar();
    expect(screen.queryByLabelText(/Delay before voice starts/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Pause between speech chunks/i)).not.toBeInTheDocument();
  });

  it("Voice button opens settings sheet", async () => {
    renderMobileBar();
    fireEvent.click(screen.getByRole("button", { name: /^Voice$/i }));
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /Debug voice timing/i }));
    expect(screen.getByLabelText(/Delay before voice starts/i)).toBeInTheDocument();
  });
});
