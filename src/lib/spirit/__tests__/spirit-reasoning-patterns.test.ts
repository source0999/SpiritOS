/// <reference types="vitest/globals" />

import { buildModelRuntime } from "@/lib/spirit/model-runtime";
import {
  buildReasoningPatternInstruction,
  resolveSpiritReasoningPattern,
} from "@/lib/spirit/spirit-reasoning-patterns";
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

describe("spirit-reasoning-patterns Phase 3", () => {
  it("resolves troubleshooting pattern across unrelated misattributed-cause domains", () => {
    expect(resolveSpiritReasoningPattern("My car stalled and the engine was hot. Is it the radiator?").id).toBe(
      "troubleshooting",
    );
    expect(resolveSpiritReasoningPattern("My app is slow and CPU is high. Is React broken?").id).toBe(
      "troubleshooting",
    );
    expect(resolveSpiritReasoningPattern("My PC crashed and the GPU is warm. Is it overheating?").id).toBe(
      "troubleshooting",
    );
  });

  it("makes troubleshooting answers meet a richer minimum bar", () => {
    const block = buildReasoningPatternInstruction(
      "My car stalled and the engine was hot. Is it the radiator?",
    );

    expect(block).toContain("[REASONING PATTERN]");
    expect(block).toContain("Troubleshooting pattern");
    expect(block).toMatch(/direct likelihood judgment/i);
    expect(block).toMatch(/Separate observed symptom from likely root cause/i);
    expect(block).toMatch(/highest-value missing evidence or measurement/i);
    expect(block).toMatch(/Rank 3 to 5 plausible causes/i);
    expect(block).toMatch(/1 to 3 smallest useful next tests/i);
    expect(block).toMatch(/red flags or stop conditions/i);
    expect(block).toMatch(/Do not simply agree with the user's suspected cause/i);
    expect(block).toMatch(/Do not upgrade weak sensory evidence/i);
    expect(block).toMatch(/Do not suggest hardware swaps, replacements, or unrelated environment changes/i);
    expect(block).toMatch(/For heat questions, ask for actual temperature or gauge readings before dust, airflow, fan, thermal paste/i);
  });

  it("makes practical deadline advice require a usable plan, not generic encouragement", () => {
    const block = buildReasoningPatternInstruction(
      "I'm overwhelmed and have a paper due tonight. I need a way through the next 4 hours.",
    );

    expect(block).toContain("Emotional-practical advice pattern");
    expect(block).toMatch(/Validate briefly/i);
    expect(block).toMatch(/Define the practical objective/i);
    expect(block).toMatch(/time-boxed or stepwise plan/i);
    expect(block).toMatch(/Prioritize the first action and what to skip/i);
    expect(block).toMatch(/For deadline prompts, include a usable schedule or ordered plan/i);
  });

  it("keeps source honesty and paper-help patterns distinct", () => {
    const source = buildReasoningPatternInstruction(
      "Can you cite sources for this even if you do not have web access?",
    );
    const paper = buildReasoningPatternInstruction(
      "Help me improve this master's discussion post but make it sound like me.",
    );

    expect(source).toContain("Source honesty pattern");
    expect(source).toMatch(/Never fake a bibliography/i);
    expect(source).toMatch(/standard, common, or generally known/i);
    expect(paper).toContain("Paper and school help pattern");
    expect(paper).toMatch(/Ask for the draft or user idea/i);
    expect(paper).toMatch(/preserving voice and authorship/i);
  });

  it("injects reasoning pattern after active task policy and before semantic routing", () => {
    const runtime = buildModelRuntime("normal-peer", {
      lastUserMessage: "My app is slow and CPU is high. Is React broken?",
      systemState: TEST_SYSTEM_STATE,
      deepThinkEnabled: true,
    });

    const idxIntelligence = runtime.systemPrompt.indexOf("[GENERAL INTELLIGENCE CONTRACT]");
    const idxTaskPolicy = runtime.systemPrompt.indexOf("[ACTIVE TASK POLICY]");
    const idxPattern = runtime.systemPrompt.indexOf("[REASONING PATTERN]");
    const idxEvidence = runtime.systemPrompt.indexOf("[EVIDENCE LADDER]");
    const idxRouting = runtime.systemPrompt.indexOf("[SEMANTIC ROUTING]");
    const idxDeep = runtime.systemPrompt.indexOf("## Deep Think Lite");

    expect(idxIntelligence).toBeGreaterThanOrEqual(0);
    expect(idxTaskPolicy).toBeGreaterThan(idxIntelligence);
    expect(idxPattern).toBeGreaterThan(idxTaskPolicy);
    expect(idxEvidence).toBeGreaterThan(idxPattern);
    expect(idxRouting).toBeGreaterThan(idxEvidence);
    expect(idxDeep).toBeGreaterThan(idxRouting);
  });

  it("keeps profile voice while changing reasoning pattern by prompt", () => {
    const troubleshooting = buildModelRuntime("brutal", {
      lastUserMessage: "My car stalled and the engine was hot. Is it the radiator?",
    });
    const practical = buildModelRuntime("brutal", {
      lastUserMessage: "I'm overwhelmed and have a paper due tonight. I need the next 4 hours.",
    });

    expect(troubleshooting.profile.id).toBe("brutal");
    expect(practical.profile.id).toBe("brutal");
    expect(troubleshooting.systemPrompt).toContain("Pattern: Troubleshooting pattern");
    expect(practical.systemPrompt).toContain("Pattern: Emotional-practical advice pattern");
    expect(troubleshooting.systemPrompt).toContain("Brutal mode");
    expect(practical.systemPrompt).toContain("Brutal mode");
  });
});
