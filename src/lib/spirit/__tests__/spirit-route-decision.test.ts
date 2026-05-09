import { describe, expect, it } from "vitest";

import {
  decideSpiritRoute,
  shouldPrefetchOpenAiWebForResearcher,
} from "@/lib/spirit/spirit-route-decision";

describe("shouldPrefetchOpenAiWebForResearcher", () => {
  it("returns false when not researcher", () => {
    expect(
      shouldPrefetchOpenAiWebForResearcher({
        modelProfileId: "normal-peer",
        lastUserText: "What is the capital of France today?",
        webSearchGloballyEnabled: true,
      }),
    ).toBe(false);
  });

  it("returns false when web globally off", () => {
    expect(
      shouldPrefetchOpenAiWebForResearcher({
        modelProfileId: "researcher",
        lastUserText: "Long question",
        webSearchGloballyEnabled: false,
      }),
    ).toBe(false);
  });

  it("returns false when user opted out", () => {
    expect(
      shouldPrefetchOpenAiWebForResearcher({
        modelProfileId: "researcher",
        lastUserText: "hi",
        webSearchOptOut: true,
        webSearchGloballyEnabled: true,
      }),
    ).toBe(false);
  });

  it("returns true for researcher with text when web on and not opted out", () => {
    expect(
      shouldPrefetchOpenAiWebForResearcher({
        modelProfileId: "researcher",
        lastUserText: "hey",
        webSearchGloballyEnabled: true,
      }),
    ).toBe(true);
  });

  it("returns false for empty trimmed prompt", () => {
    expect(
      shouldPrefetchOpenAiWebForResearcher({
        modelProfileId: "researcher",
        lastUserText: "   ",
        webSearchGloballyEnabled: true,
      }),
    ).toBe(false);
  });
});

describe("decideSpiritRoute", () => {
  const base = {
    modelHint: "hermes4:latest",
    webSearchGloballyEnabled: true,
    deepThinkEnabled: false,
    webSearchOptOut: false,
  };

  it("peer + casual → local-chat, no web", () => {
    const d = decideSpiritRoute({
      ...base,
      modelProfileId: "normal-peer",
      lastUserText: "sup",
    });
    expect(d.lane).toBe("local-chat");
    expect(d.shouldSearchWeb).toBe(false);
    expect(d.shouldDraftResearchPlan).toBe(false);
    expect(d.shouldShowVisualizer).toBe(false);
  });

  it("researcher + depth → openai-web-search lane when prefetch triggers", () => {
    const d = decideSpiritRoute({
      ...base,
      modelProfileId: "researcher",
      lastUserText: "Summarize the latest systematic reviews on sleep and cognition",
    });
    expect(d.lane).toBe("openai-web-search");
    expect(d.shouldSearchWeb).toBe(true);
    expect(d.shouldDraftResearchPlan).toBe(true);
    expect(d.shouldShowVisualizer).toBe(true);
  });

  it("researcher + casual → still prefetches web by default, hides visualizer", () => {
    const d = decideSpiritRoute({
      ...base,
      modelProfileId: "researcher",
      lastUserText: "yo",
    });
    expect(d.shouldSearchWeb).toBe(true);
    expect(d.lane).toBe("openai-web-search");
    expect(d.shouldShowVisualizer).toBe(false);
  });

  it("researcher + substantive + web off → research-plan lane, no prefetch", () => {
    const d = decideSpiritRoute({
      ...base,
      webSearchGloballyEnabled: false,
      modelProfileId: "researcher",
      lastUserText:
        "Walk me through how heterogeneity is measured in random-effects meta-analysis models.",
    });
    expect(d.shouldSearchWeb).toBe(false);
    expect(d.lane).toBe("research-plan");
    expect(d.shouldDraftResearchPlan).toBe(true);
  });

  it("teacher + teaching depth shows visualizer", () => {
    const d = decideSpiritRoute({
      ...base,
      modelProfileId: "teacher",
      lastUserText: "Explain this homework step by step",
    });
    expect(d.shouldShowVisualizer).toBe(true);
  });

  it("deep think forces visualizer for casual peer", () => {
    const d = decideSpiritRoute({
      ...base,
      deepThinkEnabled: true,
      modelProfileId: "normal-peer",
      lastUserText: "hi",
    });
    expect(d.shouldShowVisualizer).toBe(true);
  });

  it("teacher + teacher web + study-aids prompt → openai-web-search and shouldSearchTeacherWeb", () => {
    const d = decideSpiritRoute({
      ...base,
      modelProfileId: "teacher",
      teacherWebSearchEnabled: true,
      lastUserText: "Explain the latest peer-reviewed studies on sleep and cognition for my exam",
    });
    expect(d.shouldSearchTeacherWeb).toBe(true);
    expect(d.lane).toBe("openai-web-search");
  });

  it("teacher + study prompt + omitted teacherWebSearchEnabled defaults to teacher web aids", () => {
    const d = decideSpiritRoute({
      ...base,
      modelProfileId: "teacher",
      lastUserText: "Define negative punishment with an ABA example for my exam",
    });
    expect(d.shouldSearchTeacherWeb).toBe(true);
    expect(d.lane).toBe("openai-web-search");
  });

  it("teacher + sensory topic without explain/teach verbs → still OpenAI web aids lane", () => {
    const d = decideSpiritRoute({
      ...base,
      modelProfileId: "teacher",
      lastUserText: "How is sensory overload different from a tantrum in young kids?",
    });
    expect(d.shouldSearchTeacherWeb).toBe(true);
    expect(d.lane).toBe("openai-web-search");
  });

  it("teacher web toggle off → no teacher web search", () => {
    const d = decideSpiritRoute({
      ...base,
      modelProfileId: "teacher",
      teacherWebSearchEnabled: false,
      lastUserText: "Find the latest peer-reviewed studies on sleep and cognition",
    });
    expect(d.shouldSearchTeacherWeb).toBe(false);
  });
});
