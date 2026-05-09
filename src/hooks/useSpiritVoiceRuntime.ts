"use client";

// ── useSpiritVoiceRuntime - TTS + speak helpers (shared by /chat and /oracle) ─────
import type { UIMessage } from "ai";
import { useCallback, useLayoutEffect, useMemo, useRef } from "react";

import { useTTS } from "@/hooks/useTTS";
import { textFromParts } from "@/lib/chat-utils";
import { sanitizeAssistantVisibleText } from "@/lib/spirit/assistant-output-sanitizer";
import {
  type SpiritActivityEvent,
} from "@/lib/spirit/spirit-activity-events";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { stripFakeCitationsWhenNoSources } from "@/lib/spirit/research-source-enforcement";
import type { SpiritWebSourcesHeaderPayload } from "@/lib/spirit/spirit-web-sources";
import { pickTtsSpeakPayload } from "@/lib/tts/tts-text-budget";

export type AssistantSourceProofState = {
  messageId: string;
  hadVerifiedUrls: boolean;
  profileId: ModelProfileId;
  webSources?: SpiritWebSourcesHeaderPayload | null;
} | null;

export type SpiritTTS = ReturnType<typeof useTTS>;

export type UseSpiritVoiceRuntimeInput = {
  /** Single `useTTS()` instance shared with transport `onFinish` */
  tts: SpiritTTS;
  /** Saved-chat logging + activity spam; Oracle can silence extras */
  activityLoggingShell: boolean;
  messages: UIMessage[];
  /** Proof row from last assistant finish - researcher citation hygiene */
  assistantSourceProof: AssistantSourceProofState;
  /** Called when voice timing / errors should touch SpiritActivityPanel */
  pushActivity?: (e: Omit<SpiritActivityEvent, "id" | "at">) => void;
};

export type SpiritVoiceRuntime = {
  tts: SpiritTTS;
  speakLatestAssistant: () => Promise<void>;
  speakAssistantText: (text: string, mode: "summary" | "full-chunks") => Promise<void>;
  speakAssistantMessage: (text: string) => Promise<void>;
  speakAssistantMessageFull: (text: string) => Promise<void>;
  stop: () => void;
  assistantSpeakableText: (m: UIMessage) => string;
  activityVoiceLine: string;
};

export function useSpiritVoiceRuntime(
  input: UseSpiritVoiceRuntimeInput,
): SpiritVoiceRuntime {
  const { tts } = input;

  const pushActivity = input.pushActivity;

  const assistantSpeakableText = useCallback(
    (m: UIMessage): string => {
      const raw = textFromParts(m);
      if (m.role !== "assistant") return raw;
      let t = sanitizeAssistantVisibleText(raw);
      const stripFake =
        input.assistantSourceProof?.messageId === m.id &&
        input.assistantSourceProof.profileId === "researcher" &&
        !input.assistantSourceProof.hadVerifiedUrls;
      if (stripFake) t = stripFakeCitationsWhenNoSources(t);
      return t;
    },
    [input.assistantSourceProof],
  );

  const speakAssistantText = useCallback(
    async (text: string, mode: "summary" | "full-chunks") => {
      const ok = await tts.ensureAudioUnlocked();
      if (!ok) return;
      const plan = pickTtsSpeakPayload(text, mode);
      if (!plan.segments.length) return;
      if (plan.segments.length === 1) {
        tts.speak(plan.segments[0]!, {
          interrupt: true,
          spokenSummaryLine: plan.spokenSummaryLine,
        });
      } else {
        tts.speakMany(plan.segments, {
          interrupt: true,
          spokenSummaryLine: plan.spokenSummaryLine,
        });
      }
      if (input.activityLoggingShell && pushActivity) {
        pushActivity({ kind: "voice_played", label: plan.spokenSummaryLine });
      }
    },
    [tts, input.activityLoggingShell, pushActivity],
  );

  const speakLatestAssistant = useCallback(async () => {
    const ok = await tts.ensureAudioUnlocked();
    if (!ok) return;
    for (let i = input.messages.length - 1; i >= 0; i--) {
      const m = input.messages[i]!;
      if (m.role === "assistant") {
        await speakAssistantText(assistantSpeakableText(m), "summary");
        return;
      }
    }
  }, [input.messages, speakAssistantText, tts, assistantSpeakableText]);

  const speakAssistantMessage = useCallback(
    async (text: string) => {
      await speakAssistantText(text, "summary");
    },
    [speakAssistantText],
  );

  const speakAssistantMessageFull = useCallback(
    async (text: string) => {
      await speakAssistantText(text, "full-chunks");
    },
    [speakAssistantText],
  );

  const activityVoiceLine =
    tts.state.elevenLabsVoiceId || tts.state.voicesSource === "elevenlabs"
      ? "ElevenLabs"
      : "Piper / local";

  return useMemo(
    (): SpiritVoiceRuntime => ({
      tts,
      speakLatestAssistant,
      speakAssistantText,
      speakAssistantMessage,
      speakAssistantMessageFull,
      stop: tts.stop,
      assistantSpeakableText,
      activityVoiceLine,
    }),
    [
      tts,
      speakLatestAssistant,
      speakAssistantText,
      speakAssistantMessage,
      speakAssistantMessageFull,
      assistantSpeakableText,
      activityVoiceLine,
    ],
  );
}

/** Ref snapshot for transport `onFinish` - avoids stale hook closures during streaming */
export function useTtsSpeakGateRef(tts: SpiritTTS) {
  const ttsSpeakGateRef = useRef({ isEnabled: false, autoSpeakAssistant: false });
  useLayoutEffect(() => {
    ttsSpeakGateRef.current = {
      isEnabled: tts.state.isEnabled,
      autoSpeakAssistant: tts.state.autoSpeakAssistant,
    };
  }, [tts.state.isEnabled, tts.state.autoSpeakAssistant]);
  return ttsSpeakGateRef;
}
