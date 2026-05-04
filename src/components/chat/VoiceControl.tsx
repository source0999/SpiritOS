"use client";

// ── VoiceControl — desktop strip + portal panel (Prompt 9J: no overflow clipping) ─
// > No “Prime” theatre. Delay/gap live under Debug voice timing only.
import { Settings2, Volume2, X } from "lucide-react";
import { memo, useCallback, useEffect, useId, useState } from "react";
import { createPortal } from "react-dom";

import { MobileSheet } from "@/components/chat/MobileSheet";
import { VoiceSettingsPanel } from "@/components/chat/VoiceSettingsPanel";
import type { UseTtsState } from "@/hooks/useTTS";
import { useMounted } from "@/lib/hooks/useMounted";
import { cn } from "@/lib/cn";

export type VoiceControlVariant = "desktop" | "mobile-bar";

export type VoiceControlProps = {
  state: UseTtsState;
  onToggleEnabled: () => void;
  /** Resume AudioContext — call from Speak tap path too (iOS gesture budget). */
  onEnableAudio: () => void | Promise<void | boolean>;
  onStop: () => void;
  /** Should await unlock internally via parent / Speak handler before queueing. */
  onSpeakLatestAssistant: () => void | Promise<void>;
  onStartDelayChange: (ms: number) => void;
  onSentenceGapChange: (ms: number) => void;
  onVoiceSpeedChange?: (speed: number) => void;
  onToggleAutoSpeak?: () => void;
  /** Fetch `/api/tts/voices` when settings sheet opens (ElevenLabs catalog). */
  onRequestVoiceCatalog?: () => void | Promise<void>;
  onElevenLabsVoiceChange?: (voiceId: string) => void;
  disabled?: boolean;
  variant?: VoiceControlVariant;
};

export const VoiceControl = memo(function VoiceControl({
  state,
  onToggleEnabled,
  onEnableAudio,
  onStop,
  onSpeakLatestAssistant,
  onStartDelayChange,
  onSentenceGapChange,
  onVoiceSpeedChange,
  onToggleAutoSpeak,
  onRequestVoiceCatalog,
  onElevenLabsVoiceChange,
  disabled = false,
  variant = "desktop",
}: VoiceControlProps) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [mobileSheetOpen, setMobileSheetOpen] = useState(false);
  const panelId = useId();
  const mounted = useMounted();

  useEffect(() => {
    if (!onRequestVoiceCatalog) return;
    if (mobileSheetOpen || settingsOpen) {
      void onRequestVoiceCatalog();
    }
  }, [mobileSheetOpen, settingsOpen, onRequestVoiceCatalog]);

  const closeSettings = useCallback(() => {
    setSettingsOpen(false);
  }, []);

  const showStop = state.isPlaying || state.queueLength > 0;
  const statusDot =
    state.lastError != null
      ? "bg-rose-400 shadow-[0_0_10px_rgba(248,113,113,0.45)]"
      : state.isPlaying
        ? "bg-[color:var(--spirit-accent-strong)] shadow-[0_0_10px_color-mix(in_oklab,var(--spirit-glow)_55%,transparent)]"
        : "bg-chalk/35";

  if (variant === "mobile-bar") {
    return (
      <>
        <button
          type="button"
          onClick={() => setMobileSheetOpen(true)}
          disabled={disabled}
          aria-label="Voice"
          className={cn(
            "touch-manipulation inline-flex h-9 max-w-[5.5rem] shrink-0 items-center gap-1.5 rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.04] px-2 font-mono text-[9px] font-semibold uppercase tracking-wider text-chalk/80 transition hover:bg-white/[0.07]",
            disabled && "pointer-events-none opacity-40",
          )}
        >
          <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", statusDot)} aria-hidden />
          <Volume2 className="h-3.5 w-3.5 shrink-0 text-chalk/60" aria-hidden strokeWidth={2} />
          <span className="truncate max-[340px]:sr-only">Voice</span>
        </button>

        <MobileSheet
          open={mobileSheetOpen}
          title="Voice"
          onClose={() => setMobileSheetOpen(false)}
          side="bottom"
        >
          <div className="flex flex-col gap-2.5 px-0.5">
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={onToggleEnabled}
                aria-pressed={state.isEnabled}
                className={cn(
                  "touch-manipulation inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-2 font-mono text-[10px] font-semibold uppercase tracking-wider",
                  state.isEnabled
                    ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_48%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_14%,transparent)] text-[color:var(--spirit-accent-strong)]"
                    : "border-[color:var(--spirit-border)] bg-white/[0.04] text-chalk/60",
                )}
              >
                <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", statusDot)} aria-hidden />
                {mounted ? (state.isEnabled ? "Voice on" : "Voice off") : "Voice"}
              </button>
              <button
                type="button"
                disabled={!state.isEnabled}
                aria-disabled={!state.isEnabled}
                onClick={() => void onSpeakLatestAssistant()}
                className="touch-manipulation inline-flex shrink-0 items-center rounded-full border border-[color:color-mix(in_oklab,var(--spirit-accent)_38%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_10%,transparent)] px-3 py-2 font-mono text-[10px] font-semibold uppercase tracking-wider text-[color:var(--spirit-accent-strong)] disabled:opacity-35"
              >
                Speak
              </button>
              {showStop ? (
                <button
                  type="button"
                  onClick={onStop}
                  className="touch-manipulation inline-flex shrink-0 items-center rounded-full border border-[color:color-mix(in_oklab,var(--color-rose)_35%,transparent)] bg-rose-500/10 px-3 py-2 font-mono text-[10px] font-semibold uppercase tracking-wider text-rose-100/90"
                >
                  Stop
                </button>
              ) : null}
            </div>
            <VoiceSettingsPanel
              state={state}
              onEnableAudio={onEnableAudio}
              onStartDelayChange={onStartDelayChange}
              onSentenceGapChange={onSentenceGapChange}
              onVoiceSpeedChange={onVoiceSpeedChange}
              onToggleAutoSpeak={onToggleAutoSpeak}
              onElevenLabsVoiceChange={onElevenLabsVoiceChange}
              onRetryVoiceCatalog={onRequestVoiceCatalog}
              disabled={disabled}
            />
          </div>
        </MobileSheet>
      </>
    );
  }

  return (
    <div
      className={cn(
        "relative flex w-full min-w-0 flex-col gap-1",
        disabled && "pointer-events-none opacity-40",
      )}
      onPointerDown={(e) => e.stopPropagation()}
    >
      <div className="flex min-h-[40px] min-w-0 items-center gap-1.5 sm:min-h-[36px]">
        <button
          type="button"
          onClick={onToggleEnabled}
          aria-pressed={state.isEnabled}
          className={cn(
            "touch-manipulation inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1.5 font-mono text-[9px] font-semibold uppercase tracking-wider sm:text-[10px]",
            state.isEnabled
              ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_48%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_14%,transparent)] text-[color:var(--spirit-accent-strong)]"
              : "border-[color:var(--spirit-border)] bg-white/[0.04] text-chalk/60",
          )}
        >
          <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", statusDot)} aria-hidden />
          {mounted ? (state.isEnabled ? "Voice on" : "Voice off") : "Voice"}
        </button>
        <button
          type="button"
          disabled={!state.isEnabled}
          aria-disabled={!state.isEnabled}
          onClick={() => void onSpeakLatestAssistant()}
          className="touch-manipulation inline-flex shrink-0 items-center rounded-full border border-[color:color-mix(in_oklab,var(--spirit-accent)_38%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_10%,transparent)] px-2.5 py-1.5 font-mono text-[9px] font-semibold uppercase tracking-wider text-[color:var(--spirit-accent-strong)] disabled:opacity-35 sm:text-[10px]"
        >
          Speak
        </button>
        {showStop ? (
          <button
            type="button"
            onClick={onStop}
            className="touch-manipulation inline-flex shrink-0 items-center rounded-full border border-[color:color-mix(in_oklab,var(--color-rose)_35%,transparent)] bg-rose-500/10 px-2.5 py-1.5 font-mono text-[9px] font-semibold uppercase tracking-wider text-rose-100/90 sm:text-[10px]"
          >
            Stop
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => setSettingsOpen((o) => !o)}
          aria-expanded={settingsOpen}
          aria-controls={panelId}
          aria-label="Voice settings"
          className="touch-manipulation ml-auto inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.04] text-chalk/70 transition hover:bg-white/[0.08] sm:h-8 sm:w-8"
        >
          <Settings2 className="h-4 w-4" aria-hidden strokeWidth={2} />
        </button>
      </div>

      {settingsOpen && mounted
        ? createPortal(
            <>
              <button
                type="button"
                aria-label="Close voice settings"
                className="fixed inset-0 z-[84] bg-black/55 backdrop-blur-[1px]"
                onClick={closeSettings}
              />
              <div
                id={panelId}
                role="dialog"
                aria-label="Voice settings"
                className={cn(
                  "fixed z-[85] flex flex-col gap-3 overflow-y-auto rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-border)_45%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_94%,black)] p-3 shadow-2xl",
                  "inset-x-2 bottom-[max(0.5rem,env(safe-area-inset-bottom))] max-h-[min(85dvh,520px)] min-w-0 max-lg:max-h-[80dvh]",
                  "lg:inset-x-auto lg:bottom-auto lg:right-4 lg:top-[max(5rem,env(safe-area-inset-top))] lg:min-w-[420px] lg:w-[min(440px,calc(100vw-2rem))] lg:max-h-[min(70vh,640px)]",
                )}
              >
                <div className="flex items-center justify-between gap-2 border-b border-white/[0.06] pb-2 lg:hidden">
                  <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-chalk/55">
                    Voice settings
                  </p>
                  <button
                    type="button"
                    onClick={closeSettings}
                    aria-label="Close"
                    className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-[color:var(--spirit-border)] text-chalk/70"
                  >
                    <X className="h-4 w-4" aria-hidden />
                  </button>
                </div>
                <VoiceSettingsPanel
                  state={state}
                  onEnableAudio={onEnableAudio}
                  onStartDelayChange={onStartDelayChange}
                  onSentenceGapChange={onSentenceGapChange}
                  onVoiceSpeedChange={onVoiceSpeedChange}
                  onToggleAutoSpeak={onToggleAutoSpeak}
                  onElevenLabsVoiceChange={onElevenLabsVoiceChange}
                  onRetryVoiceCatalog={onRequestVoiceCatalog}
                  disabled={disabled}
                />
              </div>
            </>,
            document.body,
          )
        : null}
    </div>
  );
});
