import { describe, expect, it } from "vitest";

import { buildModelRuntime } from "@/lib/spirit/model-runtime";
import { MODEL_PROFILES } from "@/lib/spirit/model-profiles";

describe("buildModelRuntime", () => {
  it("returns profile systemPrompt and temperature", () => {
    const r = buildModelRuntime("brutal");
    expect(r.profile.id).toBe("brutal");
    expect(r.systemPrompt).toContain(MODEL_PROFILES.brutal.systemPrompt);
    expect(r.systemPrompt).toContain("## Response budget");
    expect(r.temperature).toBe(0.62);
  });

  it("defaults unknown ids to normal-peer", () => {
    const r = buildModelRuntime("garbage");
    expect(r.profile.id).toBe("normal-peer");
    expect(r.temperature).toBe(0.72);
  });

  it("appends personalization summary when provided", () => {
    const r = buildModelRuntime("teacher", {
      personalizationSummary: "- Tone: terse",
    });
    expect(r.systemPrompt).toContain("User style preferences");
    expect(r.systemPrompt).toContain("- Tone: terse");
  });

  it("appends Peer final-answer contract with coding-default + banned phrases", () => {
    const r = buildModelRuntime("normal-peer", { lastUserMessage: "yo" });
    expect(r.systemPrompt).toContain("Final answer contract — Peer mode");
    expect(r.systemPrompt).toContain("Not coding mode");
    expect(r.systemPrompt).toContain("How may I assist you?");
  });

  it("appends Sassy max-3-sentences contract", () => {
    const r = buildModelRuntime("sassy-chaotic", { lastUserMessage: "hi" });
    expect(r.systemPrompt).toContain("Max 3 short sentences");
  });

  it("appends Brutal max-2-paragraphs contract", () => {
    const r = buildModelRuntime("brutal", { lastUserMessage: "hi" });
    expect(r.systemPrompt).toContain("Max 2 short paragraphs");
  });

  it("appends Teacher study aids / no-fake-links rule", () => {
    const r = buildModelRuntime("teacher", { lastUserMessage: "what is gravity" });
    expect(r.systemPrompt).toContain("do not invent links");
  });

  it("Teacher + verified digest shifts budget to link-first Study aids", () => {
    const digest = `## Web research digest (OpenAI Responses + web_search)
Provider: OpenAI
Search used: yes
User query: test
Verified URL sources (2):
1. **A** | url: https://a.edu/x
2. **B** | url: https://b.org/y
`;
    const r = buildModelRuntime("teacher", {
      lastUserMessage: "explain stimulus overselectivity",
      researchWebContext: digest,
    });
    expect(r.systemPrompt).toContain("markdown link bullets first");
    expect(r.systemPrompt).toContain("https://a.edu/x");
  });

  it("Teacher + webVerifiedUrlCount enables link-first budget without digest regex", () => {
    const r = buildModelRuntime("teacher", {
      lastUserMessage: "x",
      researchWebContext: "no Verified URL sources line here",
      webVerifiedUrlCount: 2,
    });
    expect(r.systemPrompt).toContain("markdown link bullets first");
  });

  it("appends Researcher source honesty + Executive Summary heading rule", () => {
    const r = buildModelRuntime("researcher", { lastUserMessage: "sources please" });
    expect(r.systemPrompt).toContain("Executive Summary");
    expect(r.systemPrompt).toContain("No fake citations");
  });

  it("Researcher + webVerifiedUrlCount enables digest link budget (parity with Teacher)", () => {
    const r = buildModelRuntime("researcher", {
      lastUserMessage: "x",
      researchWebContext: "stub",
      webVerifiedUrlCount: 1,
    });
    expect(r.systemPrompt).toContain("Verified URLs are attached");
  });

  it("Deep Think keeps Sassy contract (no essay escape hatch)", () => {
    const r = buildModelRuntime("sassy-chaotic", {
      lastUserMessage: "hi",
      deepThinkEnabled: true,
    });
    expect(r.systemPrompt).toContain("Deep Think modifier");
    expect(r.systemPrompt).toContain("Max 3 short sentences");
  });

  it("Deep Think bumps maxOutputTokens modestly", () => {
    const shallow = buildModelRuntime("researcher", { lastUserMessage: "x" });
    const deep = buildModelRuntime("researcher", {
      lastUserMessage: "x",
      deepThinkEnabled: true,
    });
    expect(deep.maxOutputTokens).toBeGreaterThan(shallow.maxOutputTokens!);
    expect(deep.maxOutputTokens).toBeLessThanOrEqual(4096);
  });
});
