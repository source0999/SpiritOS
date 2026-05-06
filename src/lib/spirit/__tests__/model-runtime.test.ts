import { describe, expect, it } from "vitest";

import { buildModelRuntime, buildSemanticRoutingInstruction } from "@/lib/spirit/model-runtime";
import { MODEL_PROFILES } from "@/lib/spirit/model-profiles";
import type { SpiritSystemStateInput } from "@/lib/spirit/system-state";

const TEST_SYSTEM_STATE: SpiritSystemStateInput = {
  currentTimeIso: "2026-05-06T00:00:00.000Z",
  runtimeSurface: "chat",
  modelHint: "hermes-test-model",
  modelProfileId: "normal-peer",
  modelProfileLabel: "Peer",
  hardwareProfile: "unknown",
  projectPathConfigured: false,
  availableCapabilities: ["chat", "tts", "stt", "web_search_when_enabled"],
  unavailableCapabilities: [
    "workspace_file_read",
    "workspace_file_list",
    "log_tail_read",
    "system_status",
    "file_editing",
    "terminal_execution",
    "email_access",
    "calendar_access",
  ],
};

describe("buildModelRuntime", () => {
  it("includes capability registry hint (no full JSON dump)", () => {
    const r = buildModelRuntime("normal-peer", { lastUserMessage: "yo" });
    expect(r.systemPrompt).toContain("## SpiritOS live capability registry");
    expect(r.systemPrompt).toMatch(/\/api\/spirit/);
  });

  it("Chat Peer does not include Oracle Voice surface instruction", () => {
    const r = buildModelRuntime("normal-peer", { lastUserMessage: "yo" });
    expect(r.systemPrompt).not.toContain("## Oracle Voice surface");
  });

  it("Oracle Peer includes live voice / spoken conversation surface instruction", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      runtimeSurface: "oracle",
    });
    expect(r.systemPrompt).toContain("## Oracle Voice surface");
    expect(r.systemPrompt).toMatch(/live spoken conversation|spoken conversation surface/i);
  });

  it("Oracle Peer forbids defaulting to coding unless user brings it up", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      runtimeSurface: "oracle",
    });
    expect(r.systemPrompt).toMatch(/Do not default to coding|coding workspace/i);
  });

  it("Oracle Peer includes short spoken response guidance", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      runtimeSurface: "oracle",
    });
    expect(r.systemPrompt).toMatch(/short enough to speak|Voice-first|90 words/i);
  });

  it("Oracle Peer puts dating/social advice explicitly in scope", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "what should I text her",
      runtimeSurface: "oracle",
    });
    expect(r.systemPrompt).toMatch(/dating|texting|flirting/i);
    expect(r.systemPrompt).toMatch(/in scope|Normal human social advice/i);
  });

  it("Oracle Peer includes consent/boundary/safety rails for social advice", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      runtimeSurface: "oracle",
    });
    expect(r.systemPrompt).toMatch(/Consent|boundaries|harassment|rejection/i);
    expect(r.systemPrompt).toMatch(/manipulation|coerc/i);
  });

  it("Oracle Peer instructs not to over-professionalize or dodge normal dating/social questions", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      runtimeSurface: "oracle",
    });
    expect(r.systemPrompt).toMatch(/over-professionalize|generic AI disclaimers/i);
  });

  it("Chat Peer does not include Oracle dating/social scope block", () => {
    const r = buildModelRuntime("normal-peer", { lastUserMessage: "yo" });
    expect(r.systemPrompt).not.toMatch(/Normal human social advice is in scope/i);
  });

  it("Oracle surface instruction appears after profile prompt and before personalization", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "x",
      runtimeSurface: "oracle",
      personalizationSummary: "Tone: dry humor",
    });
    const idxPeer = r.systemPrompt.indexOf(MODEL_PROFILES["normal-peer"].systemPrompt);
    const idxOracle = r.systemPrompt.indexOf("## Oracle Voice surface");
    const idxPrefs = r.systemPrompt.indexOf("User style preferences");
    expect(idxPeer).toBeGreaterThanOrEqual(0);
    expect(idxOracle).toBeGreaterThan(idxPeer);
    expect(idxPrefs).toBeGreaterThan(idxOracle);
  });

  it("Oracle surface instruction does not remove personalization summary", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "x",
      runtimeSurface: "oracle",
      personalizationSummary: "Prefer concise replies",
    });
    expect(r.systemPrompt).toContain("Prefer concise replies");
  });

  it("Teacher + oracle surface still builds valid runtime", () => {
    const r = buildModelRuntime("teacher", {
      lastUserMessage: "what is gravity",
      runtimeSurface: "oracle",
    });
    expect(r.profile.id).toBe("teacher");
    expect(r.systemPrompt).toContain("## Oracle Voice surface");
    expect(r.systemPrompt).toContain("Teacher mode");
  });

  it("Researcher + oracle surface still builds valid runtime", () => {
    const r = buildModelRuntime("researcher", {
      lastUserMessage: "sources please",
      runtimeSurface: "oracle",
    });
    expect(r.profile.id).toBe("researcher");
    expect(r.systemPrompt).toContain("## Oracle Voice surface");
    expect(r.systemPrompt).toContain("Researcher mode");
  });

  it("Oracle surface instruction precedes web research digest", () => {
    const digest = "## Web research digest (stub)\nVerified URL sources (1):";
    const r = buildModelRuntime("researcher", {
      lastUserMessage: "x",
      runtimeSurface: "oracle",
      researchWebContext: digest,
    });
    expect(r.systemPrompt.indexOf("## Oracle Voice surface")).toBeLessThan(
      r.systemPrompt.indexOf("## Web research digest"),
    );
  });

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
    expect(r.systemPrompt).toMatch(/## Final answer contract.{1,5}Peer mode\n- Not coding mode/);
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

  // ── Phase 2: [SEMANTIC ROUTING] block ────────────────────────────────────────

  it("includes [SEMANTIC ROUTING] in every profile", () => {
    const profiles = ["normal-peer", "researcher", "teacher", "brutal", "sassy-chaotic"] as const;
    for (const id of profiles) {
      const r = buildModelRuntime(id, { lastUserMessage: "yo" });
      expect(r.systemPrompt, `profile: ${id}`).toContain("[SEMANTIC ROUTING]");
    }
  });

  it("[SEMANTIC ROUTING] describes the profile as a style bias, not a hard limit", () => {
    const r = buildModelRuntime("normal-peer", { lastUserMessage: "yo" });
    expect(r.systemPrompt).toMatch(/style bias|not a hard capability limit/i);
  });

  it("[SEMANTIC ROUTING] allows technical depth for code, repo, and architecture questions", () => {
    const r = buildModelRuntime("normal-peer", { lastUserMessage: "yo" });
    expect(r.systemPrompt).toMatch(/technical precision.*enough structure|enough structure.*genuinely useful/i);
  });

  it("[SEMANTIC ROUTING] instructs not to claim unavailable capabilities when system state is present", () => {
    const r = buildModelRuntime("normal-peer", { lastUserMessage: "yo" });
    expect(r.systemPrompt).toMatch(
      /When the \[SYSTEM STATE\] block is present.*lists as unavailable|lists as unavailable/i,
    );
    expect(r.systemPrompt).toMatch(
      /Obey \[SYSTEM STATE\] capability boundaries when the \[SYSTEM STATE\] block is present/i,
    );
  });

  it("[SEMANTIC ROUTING] appears after [SYSTEM STATE] block when systemState is present", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      systemState: TEST_SYSTEM_STATE,
    });
    const idxState = r.systemPrompt.search(/\[SYSTEM STATE\]\nTime:/);
    const idxRouting = r.systemPrompt.indexOf("[SEMANTIC ROUTING]");
    expect(idxState).toBeGreaterThanOrEqual(0);
    expect(idxRouting).toBeGreaterThan(idxState);
  });

  it("[SEMANTIC ROUTING] appears before deep think block", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      deepThinkEnabled: true,
    });
    const idxRouting = r.systemPrompt.indexOf("[SEMANTIC ROUTING]");
    const idxDeep = r.systemPrompt.indexOf("## Deep Think Lite");
    expect(idxRouting).toBeGreaterThanOrEqual(0);
    expect(idxDeep).toBeGreaterThan(idxRouting);
  });

  it("[SEMANTIC ROUTING] appears before research context", () => {
    const r = buildModelRuntime("researcher", {
      lastUserMessage: "sources",
      researchWebContext: "## Web research digest (stub)\nVerified URL sources (0):",
    });
    const idxRouting = r.systemPrompt.indexOf("[SEMANTIC ROUTING]");
    const idxResearch = r.systemPrompt.indexOf("## Web research digest");
    expect(idxRouting).toBeGreaterThanOrEqual(0);
    expect(idxResearch).toBeGreaterThan(idxRouting);
  });

  it("buildSemanticRoutingInstruction embeds profile id", () => {
    const profile = MODEL_PROFILES.researcher;
    const block = buildSemanticRoutingInstruction(profile);
    expect(block).toContain("researcher");
  });

  it("existing [SYSTEM STATE] order test still holds with routing block inserted", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      deepThinkEnabled: true,
      systemState: TEST_SYSTEM_STATE,
    });
    const idxBudget = r.systemPrompt.indexOf("## Response budget");
    const idxState = r.systemPrompt.search(/\[SYSTEM STATE\]\nTime:/);
    const idxRouting = r.systemPrompt.indexOf("[SEMANTIC ROUTING]");
    const idxDeep = r.systemPrompt.indexOf("## Deep Think Lite");
    expect(idxBudget).toBeGreaterThanOrEqual(0);
    expect(idxState).toBeGreaterThan(idxBudget);
    expect(idxRouting).toBeGreaterThan(idxState);
    expect(idxDeep).toBeGreaterThan(idxRouting);
  });

  // ── Phase 1: [SYSTEM STATE] block ─────────────────────────────────────────────

  it("includes [SYSTEM STATE] block when systemState is provided", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      systemState: TEST_SYSTEM_STATE,
    });
    // Block header always starts "[SYSTEM STATE]\nTime:"; cross-references in routing don't match
    expect(r.systemPrompt).toMatch(/\[SYSTEM STATE\]\nTime:/);
  });

  it("does not include [SYSTEM STATE] block when systemState is not provided", () => {
    const r = buildModelRuntime("normal-peer", { lastUserMessage: "yo" });
    // Semantic routing may reference "[SYSTEM STATE]" by name; the block header includes "\nTime:"
    expect(r.systemPrompt).not.toMatch(/\[SYSTEM STATE\]\nTime:/);
  });

  it("[SYSTEM STATE] block appears after response budget and before deep think", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      deepThinkEnabled: true,
      systemState: TEST_SYSTEM_STATE,
    });
    const idxBudget = r.systemPrompt.indexOf("## Response budget");
    // Use block header (includes "\nTime:") to distinguish from routing cross-references
    const idxState = r.systemPrompt.search(/\[SYSTEM STATE\]\nTime:/);
    const idxDeep = r.systemPrompt.indexOf("## Deep Think Lite");
    expect(idxBudget).toBeGreaterThanOrEqual(0);
    expect(idxState).toBeGreaterThan(idxBudget);
    expect(idxDeep).toBeGreaterThan(idxState);
  });

  it("[SYSTEM STATE] includes the anti-hallucination rule", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      systemState: TEST_SYSTEM_STATE,
    });
    expect(r.systemPrompt).toMatch(/Do not claim you used a tool/i);
  });

  it("Oracle surface instruction still precedes [SYSTEM STATE] block when both present", () => {
    const oracleState: SpiritSystemStateInput = {
      ...TEST_SYSTEM_STATE,
      runtimeSurface: "oracle",
    };
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      runtimeSurface: "oracle",
      systemState: oracleState,
    });
    const idxOracle = r.systemPrompt.indexOf("## Oracle Voice surface");
    const idxState = r.systemPrompt.search(/\[SYSTEM STATE\]\nTime:/);
    expect(idxOracle).toBeGreaterThanOrEqual(0);
    expect(idxState).toBeGreaterThan(idxOracle);
  });

  // ── Phase 3: [ORACLE MEMORY CONTEXT] block ───────────────────────────────────────

  it("does not include [ORACLE MEMORY CONTEXT] when oracleMemoryContext is not provided", () => {
    const r = buildModelRuntime("normal-peer", { lastUserMessage: "yo" });
    expect(r.systemPrompt).not.toContain("[ORACLE MEMORY CONTEXT]");
  });

  it("includes [ORACLE MEMORY CONTEXT] when oracleMemoryContext is provided", () => {
    const ctx = "[ORACLE MEMORY CONTEXT]\nRecent topics:\n1. Asked about recursion";
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      oracleMemoryContext: ctx,
    });
    expect(r.systemPrompt).toContain("[ORACLE MEMORY CONTEXT]");
    expect(r.systemPrompt).toContain("Asked about recursion");
  });

  it("[ORACLE MEMORY CONTEXT] appears after plan block and before personalization", () => {
    const ctx = "[ORACLE MEMORY CONTEXT]\nRecent topics:\n1. Test memory";
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      oracleMemoryContext: ctx,
      personalizationSummary: "Tone: terse",
      researchPlanSummary: "Plan: investigate X",
    });
    const idxOracle = r.systemPrompt.indexOf("[ORACLE MEMORY CONTEXT]");
    const idxPrefs = r.systemPrompt.indexOf("User style preferences");
    expect(idxOracle).toBeGreaterThanOrEqual(0);
    expect(idxPrefs).toBeGreaterThan(idxOracle);
  });

  it("[ORACLE MEMORY CONTEXT] appears after research context and before personalization", () => {
    const digest = "## Web research digest (stub)\nVerified URL sources (0):";
    const ctx = "[ORACLE MEMORY CONTEXT]\nRecent topics:\n1. Voice session memory";
    const r = buildModelRuntime("researcher", {
      lastUserMessage: "sources",
      researchWebContext: digest,
      oracleMemoryContext: ctx,
      personalizationSummary: "- Tone: dry",
    });
    const idxResearch = r.systemPrompt.indexOf("## Web research digest");
    const idxOracle = r.systemPrompt.indexOf("[ORACLE MEMORY CONTEXT]");
    const idxPrefs = r.systemPrompt.indexOf("User style preferences");
    expect(idxResearch).toBeGreaterThanOrEqual(0);
    expect(idxOracle).toBeGreaterThan(idxResearch);
    expect(idxPrefs).toBeGreaterThan(idxOracle);
  });

  it("does not include [ORACLE MEMORY CONTEXT] when value is empty string", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      oracleMemoryContext: "",
    });
    expect(r.systemPrompt).not.toContain("[ORACLE MEMORY CONTEXT]");
  });

  it("does not include [ORACLE MEMORY CONTEXT] when value is null", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "yo",
      oracleMemoryContext: null,
    });
    expect(r.systemPrompt).not.toContain("[ORACLE MEMORY CONTEXT]");
  });
});
