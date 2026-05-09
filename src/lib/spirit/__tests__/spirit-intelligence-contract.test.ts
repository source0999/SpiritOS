/// <reference types="vitest/globals" />

import { buildModelRuntime } from "@/lib/spirit/model-runtime";
import { buildGeneralIntelligenceInstruction } from "@/lib/spirit/spirit-intelligence-contract";
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

describe("spirit-intelligence-contract Phase 1", () => {
  it("builds a global task policy block without adding tools or file access claims", () => {
    const block = buildGeneralIntelligenceInstruction();

    expect(block).toContain("[GENERAL INTELLIGENCE CONTRACT]");
    expect(block).toMatch(/profile as voice/i);
    expect(block).toMatch(/Profiles control tone/i);
    expect(block).toMatch(/Task policy controls reasoning shape/i);
    expect(block).toMatch(/Evidence controls confidence/i);
    expect(block).toMatch(/Do not wrap the answer in XML, HTML, markdown container tags/i);
    expect(block).toMatch(/Do not invent tool use, file access, web access/i);
    expect(block).not.toMatch(/call tool|read the repo|search the web automatically/i);
  });

  it("privately classifies broad task types before choosing an answer strategy", () => {
    const block = buildGeneralIntelligenceInstruction();

    expect(block).toMatch(/classify the user's task privately/i);
    expect(block).toMatch(/troubleshooting \/ diagnosis/i);
    expect(block).toMatch(/research \/ verification/i);
    expect(block).toMatch(/school \/ paper help/i);
    expect(block).toMatch(/technical planning/i);
    expect(block).toMatch(/emotional-practical advice/i);
    expect(block).toMatch(/uncertainty check/i);
    expect(block).toMatch(/citation\/source request/i);
    expect(block).toMatch(/casual direct answer/i);
  });

  it("defines a general troubleshooting pattern without hard-coding GPU or Palworld behavior", () => {
    const block = buildGeneralIntelligenceInstruction();

    expect(block).toMatch(/Separate the symptom from the likely root cause/i);
    expect(block).toMatch(/Rank likely causes/i);
    expect(block).toMatch(/red flags/i);
    expect(block).toMatch(/suggests a cause.*hypothesis, not a conclusion/i);
    expect(block).toMatch(/missing measurements, context, timing, logs, severity, and competing explanations/i);
    expect(block).not.toMatch(/Palworld|GPU|DirectX|VRAM|thermal paste/i);
  });

  it("defines source honesty, uncertainty, planning, writing, and emotional-practical behavior", () => {
    const block = buildGeneralIntelligenceInstruction();

    expect(block).toMatch(/Never fake citations/i);
    expect(block).toMatch(/Use confidence language only when it helps/i);
    expect(block).toMatch(/Respect execution boundaries/i);
    expect(block).toMatch(/Preserve the user's voice/i);
    expect(block).toMatch(/Validate briefly, then help with the next practical step/i);
  });

  it("adds a private critic pass without requiring an extra model call", () => {
    const block = buildGeneralIntelligenceInstruction();

    expect(block).toMatch(/Quiet critic pass before final answer/i);
    expect(block).toMatch(/Keep this check private/i);
    expect(block).not.toMatch(/second model|LLM judge|call OpenAI/i);
  });

  it("injects the intelligence contract into every profile runtime", () => {
    const profiles = ["normal-peer", "researcher", "teacher", "brutal", "sassy-chaotic"] as const;

    for (const profile of profiles) {
      const runtime = buildModelRuntime(profile, { lastUserMessage: "My PC crashed" });

      expect(runtime.systemPrompt, profile).toContain("[GENERAL INTELLIGENCE CONTRACT]");
      expect(runtime.systemPrompt, profile).toContain("[SEMANTIC ROUTING]");
      expect(runtime.systemPrompt, profile).toContain("## Final answer contract");
    }
  });

  it("places the intelligence contract after system state and before semantic routing", () => {
    const runtime = buildModelRuntime("normal-peer", {
      lastUserMessage: "My PC crashed",
      systemState: TEST_SYSTEM_STATE,
      deepThinkEnabled: true,
    });

    const idxBudget = runtime.systemPrompt.indexOf("## Response budget");
    const idxState = runtime.systemPrompt.search(/\[SYSTEM STATE\]\nTime:/);
    const idxIntelligence = runtime.systemPrompt.indexOf("[GENERAL INTELLIGENCE CONTRACT]");
    const idxRouting = runtime.systemPrompt.indexOf("[SEMANTIC ROUTING]");
    const idxDeep = runtime.systemPrompt.indexOf("## Deep Think Lite");

    expect(idxBudget).toBeGreaterThanOrEqual(0);
    expect(idxState).toBeGreaterThan(idxBudget);
    expect(idxIntelligence).toBeGreaterThan(idxState);
    expect(idxRouting).toBeGreaterThan(idxIntelligence);
    expect(idxDeep).toBeGreaterThan(idxRouting);
  });

  it("places the intelligence contract before research context and user preferences", () => {
    const runtime = buildModelRuntime("researcher", {
      lastUserMessage: "verify this claim",
      researchWebContext: "## Web research digest (stub)\nVerified URL sources (0):",
      personalizationSummary: "Prefer concise replies",
    });

    const idxIntelligence = runtime.systemPrompt.indexOf("[GENERAL INTELLIGENCE CONTRACT]");
    const idxResearch = runtime.systemPrompt.indexOf("## Web research digest");
    const idxPrefs = runtime.systemPrompt.indexOf("User style preferences");

    expect(idxIntelligence).toBeGreaterThanOrEqual(0);
    expect(idxResearch).toBeGreaterThan(idxIntelligence);
    expect(idxPrefs).toBeGreaterThan(idxResearch);
  });
});
