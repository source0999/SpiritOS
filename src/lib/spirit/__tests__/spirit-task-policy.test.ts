/// <reference types="vitest/globals" />

import { buildModelRuntime } from "@/lib/spirit/model-runtime";
import {
  buildActiveTaskPolicyInstruction,
  detectSpiritTaskPolicy,
  getSpiritTaskPolicy,
} from "@/lib/spirit/spirit-task-policy";
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

describe("spirit-task-policy Phase 2", () => {
  it("detects troubleshooting from misattributed-cause prompts across domains", () => {
    expect(
      detectSpiritTaskPolicy("My car stalled and the engine was hot. Is it the radiator?"),
    ).toBe("troubleshooting-diagnosis");
    expect(
      detectSpiritTaskPolicy("My app is slow and my CPU is high. Is React broken?"),
    ).toBe("troubleshooting-diagnosis");
    expect(
      detectSpiritTaskPolicy("My PC crashed and the GPU felt warm. Is it overheating?"),
    ).toBe("troubleshooting-diagnosis");
  });

  it("detects the non-troubleshooting Phase 0 task categories", () => {
    expect(detectSpiritTaskPolicy("Can you cite sources even if you do not have web access?")).toBe(
      "citation-source-request",
    );
    expect(detectSpiritTaskPolicy("I think my answer might be wrong. Are you sure?")).toBe(
      "uncertainty-check",
    );
    expect(detectSpiritTaskPolicy("Help me improve this master's discussion post")).toBe(
      "school-paper-help",
    );
    expect(detectSpiritTaskPolicy("Make a plan to fix my app but do not touch files yet")).toBe(
      "technical-planning",
    );
    expect(detectSpiritTaskPolicy("I'm overwhelmed and have a paper due tonight")).toBe(
      "emotional-practical-advice",
    );
    expect(detectSpiritTaskPolicy("Is it true that a 2024 study found this?")).toBe(
      "research-verification",
    );
  });

  it("falls back to casual direct answer for simple chat", () => {
    expect(detectSpiritTaskPolicy("hey")).toBe("casual-direct-answer");
    expect(detectSpiritTaskPolicy("")).toBe("casual-direct-answer");
  });

  it("builds an active troubleshooting policy without hard-coding one GPU example", () => {
    const block = buildActiveTaskPolicyInstruction(
      "My app is slow and my CPU is high. Is React broken?",
    );

    expect(block).toContain("[ACTIVE TASK POLICY]");
    expect(block).toContain("Troubleshooting / diagnosis");
    expect(block).toMatch(/suspected cause as proven/i);
    expect(block).toMatch(/Separate observed symptom from likely root cause/i);
    expect(block).toMatch(/Rank likely causes/i);
    expect(block).not.toMatch(/Palworld|DirectX|VRAM|thermal paste/i);
  });

  it("keeps policy objects explicit and readable", () => {
    const policy = getSpiritTaskPolicy("technical-planning");

    expect(policy.label).toBe("Technical planning");
    expect(policy.instructions.length).toBeGreaterThanOrEqual(4);
    expect(policy.instructions.join(" ")).toMatch(/Respect plan-only requests/i);
  });

  it("injects active task policy after global intelligence and before semantic routing", () => {
    const runtime = buildModelRuntime("normal-peer", {
      lastUserMessage: "My car stalled and the engine was hot. Is it the radiator?",
      systemState: TEST_SYSTEM_STATE,
      deepThinkEnabled: true,
    });

    const idxState = runtime.systemPrompt.search(/\[SYSTEM STATE\]\nTime:/);
    const idxIntelligence = runtime.systemPrompt.indexOf("[GENERAL INTELLIGENCE CONTRACT]");
    const idxTaskPolicy = runtime.systemPrompt.indexOf("[ACTIVE TASK POLICY]");
    const idxRouting = runtime.systemPrompt.indexOf("[SEMANTIC ROUTING]");
    const idxDeep = runtime.systemPrompt.indexOf("## Deep Think Lite");

    expect(idxState).toBeGreaterThanOrEqual(0);
    expect(idxIntelligence).toBeGreaterThan(idxState);
    expect(idxTaskPolicy).toBeGreaterThan(idxIntelligence);
    expect(idxRouting).toBeGreaterThan(idxTaskPolicy);
    expect(idxDeep).toBeGreaterThan(idxRouting);
  });

  it("active policy changes by task while profile voice remains selected profile", () => {
    const planning = buildModelRuntime("sassy-chaotic", {
      lastUserMessage: "Make a plan to fix my app but do not touch files yet",
    });
    const citation = buildModelRuntime("sassy-chaotic", {
      lastUserMessage: "Can you cite sources without web access?",
    });

    expect(planning.profile.id).toBe("sassy-chaotic");
    expect(citation.profile.id).toBe("sassy-chaotic");
    expect(planning.systemPrompt).toContain("Detected task policy: Technical planning");
    expect(citation.systemPrompt).toContain("Detected task policy: Citation / source request");
    expect(planning.systemPrompt).toContain("Sassy mode");
    expect(citation.systemPrompt).toContain("Sassy mode");
  });
});
