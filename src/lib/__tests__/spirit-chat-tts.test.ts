import { describe, expect, it, vi } from "vitest";

import {
  planAssistantOutboundFinish,
  runAutoSpeakAssistantFinish,
  shouldStopTtsOnOutboundSubmit,
} from "@/lib/spirit-chat-tts";

describe("planAssistantOutboundFinish", () => {
  it("commits when thread matches and body non-empty", () => {
    expect(
      planAssistantOutboundFinish({
        threadId: "t1",
        body: "hello",
        activeThreadId: "t1",
        draftLaneActive: false,
      }),
    ).toEqual({ kind: "commit" });
  });

  it("skips with keepOutcomeRef when thread id missing", () => {
    expect(
      planAssistantOutboundFinish({
        threadId: null,
        body: "hello",
        activeThreadId: "t1",
        draftLaneActive: false,
      }),
    ).toMatchObject({ kind: "skip", reason: "no-outcome-thread", keepOutcomeRef: true });
  });

  it("skips empty assistant text but keeps outcome ref", () => {
    expect(
      planAssistantOutboundFinish({
        threadId: "t1",
        body: "   ",
        activeThreadId: "t1",
        draftLaneActive: false,
      }),
    ).toMatchObject({ kind: "skip", reason: "empty-assistant-text", keepOutcomeRef: true });
  });

  it("skips wrong thread when not draft lane", () => {
    expect(
      planAssistantOutboundFinish({
        threadId: "t-old",
        body: "done",
        activeThreadId: "t-new",
        draftLaneActive: false,
      }),
    ).toMatchObject({ kind: "skip", reason: "wrong-thread", keepOutcomeRef: true });
  });

  it("does not reject wrong thread when draft lane is active", () => {
    expect(
      planAssistantOutboundFinish({
        threadId: "t-old",
        body: "done",
        activeThreadId: "t-new",
        draftLaneActive: true,
      }),
    ).toEqual({ kind: "commit" });
  });
});

describe("shouldStopTtsOnOutboundSubmit", () => {
  it("is true when auto-speak on and audio playing", () => {
    expect(
      shouldStopTtsOnOutboundSubmit({
        autoSpeakAssistant: true,
        isPlaying: true,
        queueLength: 0,
      }),
    ).toBe(true);
  });

  it("is true when auto-speak on and queue has items", () => {
    expect(
      shouldStopTtsOnOutboundSubmit({
        autoSpeakAssistant: true,
        isPlaying: false,
        queueLength: 2,
      }),
    ).toBe(true);
  });

  it("is false when auto-speak off", () => {
    expect(
      shouldStopTtsOnOutboundSubmit({
        autoSpeakAssistant: false,
        isPlaying: true,
        queueLength: 3,
      }),
    ).toBe(false);
  });

  it("is false when idle", () => {
    expect(
      shouldStopTtsOnOutboundSubmit({
        autoSpeakAssistant: true,
        isPlaying: false,
        queueLength: 0,
      }),
    ).toBe(false);
  });
});

describe("runAutoSpeakAssistantFinish", () => {
  it("calls speak with interrupt when enabled and auto on", () => {
    const speak = vi.fn();
    runAutoSpeakAssistantFinish({
      text: " hi ",
      messageId: "m1",
      speak,
      voiceEnabled: true,
      autoSpeakAssistant: true,
    });
    expect(speak).toHaveBeenCalledWith("hi", {
      interrupt: true,
      preferHtmlAudioFirst: false,
      spokenSummaryLine: "Spoken: full message",
    });
  });

  it("does not speak when voice disabled", () => {
    const speak = vi.fn();
    runAutoSpeakAssistantFinish({
      text: "x",
      messageId: "m1",
      speak,
      voiceEnabled: false,
      autoSpeakAssistant: true,
    });
    expect(speak).not.toHaveBeenCalled();
  });

  it("does not speak when auto off", () => {
    const speak = vi.fn();
    runAutoSpeakAssistantFinish({
      text: "x",
      messageId: "m1",
      speak,
      voiceEnabled: true,
      autoSpeakAssistant: false,
    });
    expect(speak).not.toHaveBeenCalled();
  });
});
