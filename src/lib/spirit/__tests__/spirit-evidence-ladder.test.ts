/// <reference types="vitest/globals" />

import {
  assessSpiritEvidence,
  buildEvidenceLadderInstruction,
} from "@/lib/spirit/spirit-evidence-ladder";
import { buildModelRuntime } from "@/lib/spirit/model-runtime";
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

describe("spirit-evidence-ladder Phase 4", () => {
  it("treats sensory troubleshooting clues as weak and measurements as direct evidence", () => {
    const block = buildEvidenceLadderInstruction(
      "My PC crashed and the GPU is warm to touch. Is it overheating?",
    );

    expect(block).toContain("[EVIDENCE LADDER]");
    expect(block).toContain("Task policy: troubleshooting-diagnosis");
    expect(block).toContain("Highest-priority calibration:");
    expect(block).toMatch(/Weak-clue troubleshooting guard/i);
    expect(block).toMatch(/possible, but not proven from that alone/i);
    expect(block).toMatch(/Do not open with 'that sounds like a bad sign,' 'definitely a clue,'/i);
    expect(block).toMatch(/Before suggesting swaps, replacements, outlets, or maintenance/i);
    expect(block).toMatch(/Heat-specific guard/i);
    expect(block).toMatch(/prioritize actual sensor temperature or gauge readings before dust, airflow, fan, thermal paste, reseating/i);
    expect(block).toMatch(/Maintenance belongs after measured high temps, failed fans, artifacts, repeated thermal shutdowns, smoke, burning smell, or visible damage/i);
    expect(block).toMatch(/Subjective symptom or sensory clue \(weak\)/i);
    expect(block).toMatch(/touch, feels hot, seems slow, sounds weird/i);
    expect(block).toMatch(/Do not call a weak clue a bad sign, a definite clue, or strong evidence/i);
    expect(block).toMatch(/Instrumented measurement \(direct\)/i);
    expect(block).toMatch(/actual temperatures, gauges, error codes, logs, profiler output/i);
  });

  it("adds high-stakes caution when the prompt has safety-sensitive language", () => {
    const assessment = assessSpiritEvidence("My car stalled on the highway and smelled like smoke.");
    const signalIds = assessment.signals.map((signal) => signal.id);

    expect(signalIds).toContain("safety-sensitive");
    expect(assessment.confidenceGuidance.join(" ")).toMatch(/stakes are high/i);
  });

  it("source and citation prompts treat model memory as weak and verified context as direct", () => {
    const block = buildEvidenceLadderInstruction(
      "Can you cite sources for this claim even if you do not have web access?",
    );

    expect(block).toContain("Task policy: citation-source-request");
    expect(block).toMatch(/Source guard/i);
    expect(block).toMatch(/do not reassure with 'standard,' 'common,' or 'generally known'/i);
    expect(block).toMatch(/Verified source context \(direct\)/i);
    expect(block).toMatch(/Model memory \(weak\)/i);
    expect(block).toMatch(/memory-only facts as unverified background/i);
    expect(block).toMatch(/Do not substitute 'this is standard\/common knowledge' for a citation/i);
  });

  it("warns not to promote suspected causes from weak evidence", () => {
    const block = buildEvidenceLadderInstruction(
      "My car stalled and the engine was hot. Is it the radiator?",
    );

    expect(block).toMatch(/Rank competing explanations/i);
    expect(block).toMatch(/possible, but not proven/i);
    expect(block).toMatch(/decisive measurement\/log\/gauge\/profiler check/i);
    expect(block).not.toMatch(/VRAM|DirectX/i);
  });

  it("provides confidence calibration without requiring confidence labels everywhere", () => {
    const block = buildEvidenceLadderInstruction("I think my answer might be wrong. Are you sure?");

    expect(block).toMatch(/High confidence requires direct evidence/i);
    expect(block).toMatch(/Medium confidence is appropriate/i);
    expect(block).toMatch(/Low confidence is appropriate/i);
    expect(block).toMatch(/Do not label every answer with confidence unless it materially helps/i);
  });

  it("injects evidence ladder after reasoning pattern and before semantic routing", () => {
    const runtime = buildModelRuntime("normal-peer", {
      lastUserMessage: "My PC crashed and the GPU is warm to touch. Is it overheating?",
      systemState: TEST_SYSTEM_STATE,
      deepThinkEnabled: true,
    });

    const idxTaskPolicy = runtime.systemPrompt.indexOf("[ACTIVE TASK POLICY]");
    const idxPattern = runtime.systemPrompt.indexOf("[REASONING PATTERN]");
    const idxEvidence = runtime.systemPrompt.indexOf("[EVIDENCE LADDER]");
    const idxRouting = runtime.systemPrompt.indexOf("[SEMANTIC ROUTING]");
    const idxDeep = runtime.systemPrompt.indexOf("## Deep Think Lite");

    expect(idxTaskPolicy).toBeGreaterThanOrEqual(0);
    expect(idxPattern).toBeGreaterThan(idxTaskPolicy);
    expect(idxEvidence).toBeGreaterThan(idxPattern);
    expect(idxRouting).toBeGreaterThan(idxEvidence);
    expect(idxDeep).toBeGreaterThan(idxRouting);
  });
});
