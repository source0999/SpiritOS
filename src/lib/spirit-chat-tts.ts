// ── spirit-chat-tts — pure guards for outbound assistant finish (Prompt 9H) ───

export type AssistantOutboundFinishPlan =
  | { kind: "commit" }
  | { kind: "skip"; reason: string; keepOutcomeRef: boolean };

/**
 * Decide whether to persist + clear `assistantOutcomeThreadRef`.
 * Empty body / missing thread / wrong active thread → skip and usually **keep** ref
 * so a later legitimate finish still sees the outcome thread id.
 */
export function planAssistantOutboundFinish(opts: {
  threadId: string | null;
  body: string;
  activeThreadId: string | null;
  draftLaneActive: boolean;
}): AssistantOutboundFinishPlan {
  if (!opts.threadId) {
    return { kind: "skip", reason: "no-outcome-thread", keepOutcomeRef: true };
  }
  if (!opts.body.trim()) {
    return { kind: "skip", reason: "empty-assistant-text", keepOutcomeRef: true };
  }
  /* Draft lane: always commit outbound assistant for that thread id (Dexie lane has no activeThreadId). */
  if (opts.draftLaneActive) {
    return { kind: "commit" };
  }
  if (opts.activeThreadId != null && opts.threadId !== opts.activeThreadId) {
    return { kind: "skip", reason: "wrong-thread", keepOutcomeRef: true };
  }
  return { kind: "commit" };
}

/** Stop in-flight TTS when user sends a new prompt while auto-speak is on. */
export function shouldStopTtsOnOutboundSubmit(opts: {
  autoSpeakAssistant: boolean;
  isPlaying: boolean;
  queueLength: number;
}): boolean {
  return opts.autoSpeakAssistant && (opts.isPlaying || opts.queueLength > 0);
}

import { pickTtsSpeakPayload } from "@/lib/tts/tts-text-budget";

/**
 * Single auto-speak entry (Prompt 9K + 10B): long assistant replies → summary TTS path.
 */
export function runAutoSpeakAssistantFinish(opts: {
  text: string;
  messageId: string;
  speak: (
    text: string,
    o?: { interrupt?: boolean; preferHtmlAudioFirst?: boolean; spokenSummaryLine?: string },
  ) => void;
  voiceEnabled: boolean;
  autoSpeakAssistant: boolean;
}): void {
  if (!opts.voiceEnabled) {
    if (process.env.NODE_ENV === "development") {
      console.info("[tts] auto-speak skipped: disabled");
    }
    return;
  }
  if (!opts.autoSpeakAssistant) {
    if (process.env.NODE_ENV === "development") {
      console.info("[tts] auto-speak skipped: auto-speak off");
    }
    return;
  }
  const t = opts.text.trim();
  if (!t) {
    if (process.env.NODE_ENV === "development") {
      console.info("[tts] auto-speak skipped: no text");
    }
    return;
  }
  if (process.env.NODE_ENV === "development") {
    console.info(`[tts] auto-speaking finished assistant response ${opts.messageId}`);
  }
  const plan = pickTtsSpeakPayload(t, "summary");
  const chunk = plan.segments[0] ?? "";
  if (!chunk) return;
  opts.speak(chunk, {
    interrupt: true,
    preferHtmlAudioFirst: false,
    spokenSummaryLine: plan.spokenSummaryLine,
  });
}
