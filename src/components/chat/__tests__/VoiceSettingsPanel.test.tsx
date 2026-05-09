import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { VoiceSettingsPanel } from "@/components/chat/VoiceSettingsPanel";
import type { UseTtsState } from "@/hooks/useTTS";

function s(p: Partial<UseTtsState> = {}): UseTtsState {
  return {
    isPlaying: false,
    queueLength: 0,
    audioContextState: "running",
    isEnabled: true,
    startDelayMs: 0,
    sentenceGapMs: 150,
    autoSpeakAssistant: false,
    voiceSpeed: 1.12,
    elevenLabsVoiceId: "vidvidvidvid",
    elevenLabsVoiceName: "Clarice",
    voices: [{ voice_id: "vidvidvidvid", name: "Clarice" }],
    voicesSource: "env-allowlist",
    voicesAllowlistMode: "explicit-id",
    voicesWarnings: [
      "Some allowlist names could not be resolved in the ElevenLabs catalog: Zed.",
    ],
    voicesStatus: "ok",
    voicesError: undefined,
    lastError: undefined,
    lastLatency: undefined,
    lastVoiceNote: undefined,
    ...p,
  };
}

describe("VoiceSettingsPanel (Prompt 9L)", () => {
  it("renders catalog source line and warning snippet", () => {
    render(
      <VoiceSettingsPanel
        state={s()}
        onEnableAudio={vi.fn()}
        onStartDelayChange={vi.fn()}
        onSentenceGapChange={vi.fn()}
        onVoiceSpeedChange={vi.fn()}
        onToggleAutoSpeak={vi.fn()}
        onElevenLabsVoiceChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/Source: allowlist \(voice IDs from env\)/)).toBeInTheDocument();
    expect(screen.getByText(/could not be resolved/i)).toBeInTheDocument();
  });

  it("shows Retry when catalog empty but warnings present", () => {
    const onRetry = vi.fn();
    render(
      <VoiceSettingsPanel
        state={s({
          voices: [],
          elevenLabsVoiceId: null,
          elevenLabsVoiceName: null,
          voicesWarnings: [
            "Voice allowlist uses names only, but ElevenLabs catalog lookup failed.",
          ],
        })}
        onEnableAudio={vi.fn()}
        onStartDelayChange={vi.fn()}
        onSentenceGapChange={vi.fn()}
        onVoiceSpeedChange={vi.fn()}
        onToggleAutoSpeak={vi.fn()}
        onElevenLabsVoiceChange={vi.fn()}
        onRetryVoiceCatalog={onRetry}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /retry or refresh elevenlabs voices/i }));
    expect(onRetry).toHaveBeenCalled();
  });

  it("dropdown lists only returned voices", () => {
    render(
      <VoiceSettingsPanel
        state={s({
          voices: [
            { voice_id: "aaaaaaaaaaaa", name: "One" },
            { voice_id: "bbbbbbbbbbbb", name: "Two" },
          ],
          elevenLabsVoiceId: "aaaaaaaaaaaa",
        })}
        onEnableAudio={vi.fn()}
        onStartDelayChange={vi.fn()}
        onSentenceGapChange={vi.fn()}
        onVoiceSpeedChange={vi.fn()}
        onToggleAutoSpeak={vi.fn()}
        onElevenLabsVoiceChange={vi.fn()}
      />,
    );
    const sel = screen.getByLabelText(/ElevenLabs voice/i);
    const opts = within(sel).getAllByRole("option");
    expect(opts).toHaveLength(2);
  });
});
