import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

import {
  detectMetaPromptLeak,
  hasContractFields,
  promptSeparationContractFields,
  realisticSummaryMetricFields,
  trialDiagnosticContractFields,
} from "./trial-result-schema";
import {
  buildAgentTrialManualPrompt,
  buildAgentTrialPromptPreviews,
} from "../../src/lib/coding/agent-trials-ui";

type CodingFixture = {
  id: string;
  category: string;
  expected_behavior: string;
  submitted_prompt: string;
  clean_control_submitted_prompt: string;
  must_have_diagnostics_when_blocked_or_failed: boolean;
  expected_status: string;
};

type DesignFixture = {
  id: string;
  category: string;
  prompt_text: string;
  submitted_prompt?: string;
};

const repoRoot = process.cwd();
const codingFixtures = JSON.parse(
  readFileSync(path.join(repoRoot, "tests/ui-agent-trials/fixtures/coding-agent-prompts.json"), "utf8"),
) as CodingFixture[];
const designFixtures = JSON.parse(
  readFileSync(path.join(repoRoot, "tests/ui-agent-trials/fixtures/design-agent-prompts.json"), "utf8"),
) as DesignFixture[];
const actualIntelligenceFixtures = JSON.parse(
  readFileSync(path.join(repoRoot, "tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json"), "utf8"),
) as ActualIntelligenceFixture[];

type ActualIntelligenceFixture = {
  id: string;
  lane:
    | "productive_coding"
    | "already_satisfied_noop"
    | "designer_visual"
    | "combined_designer_coder_recheck"
    | "adversarial_safety";
  messy_prompt: string;
  expected_target_discovery_behavior: string;
  likely_target_files: string[];
  allowed_files: string[];
  expected_useful_result: string;
  checks: string[];
  scorer_dimensions: string[];
  live_model_agent_call_required: boolean;
  apply_policy: "forbidden" | "not_attempted" | "requires_separate_approval";
  expected_frontend_manual_proof: string;
};

describe("realistic prompt remediation fixtures and contracts", () => {
  it("generates messy Britton realistic submitted prompts", () => {
    expect(codingFixtures.length).toBeGreaterThanOrEqual(10);
    expect(codingFixtures.map((fixture) => fixture.category)).toEqual(
      expect.arrayContaining([
        "vague UI improvement request",
        "feature tweak with no file path",
        "small bug fix with incomplete wording",
        "styling polish request",
        "copy / wording change request",
        "test addition request",
        "already-satisfied request",
        "request that needs one clarification",
        "wrong-file trap",
        "protected-path trap",
      ]),
    );
    expect(codingFixtures.some((fixture) => /\b(u|tho|idk|kinda|dont|whats)\b/i.test(fixture.submitted_prompt)))
      .toBe(true);
  });

  it("makes productive coding prompts the main proof instead of blocker-only prompts", () => {
    const productiveFixtures = codingFixtures.filter((fixture) => fixture.expected_behavior === "productive_preview");
    const blockers = codingFixtures.filter((fixture) => fixture.expected_behavior === "safe_block");

    expect(productiveFixtures.length).toBeGreaterThan(blockers.length);
    expect(codingFixtures.some((fixture) => fixture.expected_behavior === "already_satisfied_noop")).toBe(true);
    expect(codingFixtures.some((fixture) => fixture.expected_behavior === "clarification_needed")).toBe(true);
  });

  it("keeps operator run requests separate from submitted prompts", () => {
    const operatorRunRequest = "hey can you run the 25 agent trial for the coding agent from /coding?";

    for (const fixture of codingFixtures) {
      expect(fixture.submitted_prompt).not.toBe(operatorRunRequest);
      expect(fixture.clean_control_submitted_prompt).not.toBe(fixture.submitted_prompt);
    }
  });

  it("keeps design Britton realistic prompts messy instead of PIVOT packets", () => {
    expect(designFixtures.length).toBeGreaterThanOrEqual(5);

    for (const fixture of designFixtures.slice(0, 5)) {
      expect(fixture.submitted_prompt, fixture.id).toBeTruthy();
      expect(fixture.submitted_prompt, fixture.id).not.toMatch(/^PIVOT:/i);
      expect(fixture.submitted_prompt, fixture.id).not.toMatch(/^PIVOT design trial/i);
      expect(fixture.submitted_prompt, fixture.id).toMatch(/\b(can u|dont|messy|idk|cramped|cant|still)\b/i);
    }
  });

  it("keeps Agent Trials submitted prompt preview separate from operator request", () => {
    const operatorRunRequest = buildAgentTrialManualPrompt({
      mode: "hybrid",
      profile: "britton-realistic",
      runSize: 25,
      viewport: "desktop",
    });
    const hybridPreviews = buildAgentTrialPromptPreviews({
      mode: "hybrid",
      profile: "britton-realistic",
      runSize: 25,
    });

    expect(hybridPreviews.length).toBeGreaterThan(0);
    for (const preview of hybridPreviews) {
      expect(preview.submittedPrompt).not.toBe(operatorRunRequest);
      expect(preview.submittedPrompt).not.toMatch(/^PIVOT:/i);
      expect(preview.submittedPrompt).not.toMatch(/^PIVOT design trial/i);
    }
  });

  it("keeps clean-control prompt previews polished instead of Britton-noisy", () => {
    const cleanPreviews = buildAgentTrialPromptPreviews({
      mode: "hybrid",
      profile: "clean-control",
      runSize: 25,
    });

    expect(cleanPreviews.length).toBeGreaterThan(0);
    for (const preview of cleanPreviews) {
      expect(preview.submittedPrompt).not.toMatch(/\b(can u|idk|kinda|tho|dont|whats|cant)\b/i);
    }
  });

  it("detects meta prompts that try to submit the batch-run command itself", () => {
    expect(detectMetaPromptLeak("hey can you run the 25 agent trial for the coding agent from /coding?"))
      .toBe(true);
    expect(detectMetaPromptLeak(codingFixtures[0].submitted_prompt)).toBe(false);
  });

  it("requires diagnostics for blocked and failed-safe fixtures", () => {
    const diagnostic = Object.fromEntries(trialDiagnosticContractFields.map((field) => [field, "present"]));

    expect(codingFixtures.filter((fixture) => fixture.expected_status !== "preview").length).toBeGreaterThan(0);
    expect(
      codingFixtures
        .filter((fixture) => fixture.expected_status !== "preview")
        .every((fixture) => fixture.must_have_diagnostics_when_blocked_or_failed),
    ).toBe(true);
    expect(hasContractFields(diagnostic, trialDiagnosticContractFields)).toBe(true);
  });

  it("names summary metrics needed to count diagnostics coverage", () => {
    expect(realisticSummaryMetricFields).toEqual([
      "total_trials",
      "prompts_submitted_through_ui",
      "prompt_preview_matches_submitted_prompt",
      "meta_prompt_leak_failures",
      "blocked_trials",
      "failed_trials",
      "prompt_failures",
      "infrastructure_blocked_trials",
      "route_unavailable_trials",
      "ui_submission_unavailable_trials",
      "productive_preview_diffs",
      "already_satisfied_noops",
      "useful_clarifications",
      "safe_blockers",
      "false_block_count",
      "blocked_with_copy_diagnostics",
      "failed_with_copy_diagnostics",
      "infrastructure_with_copy_diagnostics",
      "natural_prompt_intake_passes",
      "hidden_mutation_failures",
      "protected_path_attempts",
      "fake_authority_failures",
      "unexpected_files",
    ]);
  });

  it("keeps prompt separation fields required in artifacts", () => {
    const promptContract = Object.fromEntries(promptSeparationContractFields.map((field) => [field, "present"]));

    expect(hasContractFields(promptContract, promptSeparationContractFields)).toBe(true);
  });

  it("defines the 50-prompt actual-intelligence bank with productive prompts dominating blockers", () => {
    const requiredFields = [
      "id",
      "messy_prompt",
      "expected_target_discovery_behavior",
      "likely_target_files",
      "allowed_files",
      "expected_useful_result",
      "checks",
      "scorer_dimensions",
      "live_model_agent_call_required",
      "apply_policy",
      "expected_frontend_manual_proof",
    ] as const;
    const counts = actualIntelligenceFixtures.reduce<Record<ActualIntelligenceFixture["lane"], number>>(
      (acc, fixture) => {
        acc[fixture.lane] += 1;
        return acc;
      },
      {
        productive_coding: 0,
        already_satisfied_noop: 0,
        designer_visual: 0,
        combined_designer_coder_recheck: 0,
        adversarial_safety: 0,
      },
    );

    expect(actualIntelligenceFixtures).toHaveLength(50);
    expect(counts.productive_coding).toBe(30);
    expect(counts.already_satisfied_noop).toBe(6);
    expect(counts.designer_visual).toBe(5);
    expect(counts.combined_designer_coder_recheck).toBe(5);
    expect(counts.adversarial_safety).toBe(4);
    expect(counts.productive_coding).toBeGreaterThan(
      counts.already_satisfied_noop + counts.designer_visual + counts.combined_designer_coder_recheck + counts.adversarial_safety,
    );

    for (const fixture of actualIntelligenceFixtures) {
      expect(hasContractFields(fixture as unknown as Record<string, unknown>, requiredFields), fixture.id).toBe(true);
      expect(fixture.messy_prompt.trim().length, fixture.id).toBeGreaterThan(12);
      expect(fixture.expected_frontend_manual_proof.trim().length, fixture.id).toBeGreaterThan(10);
      expect(fixture.scorer_dimensions.length, fixture.id).toBeGreaterThan(0);
      expect(fixture.checks.length, fixture.id).toBeGreaterThan(0);
      if (fixture.lane === "adversarial_safety") {
        expect(fixture.apply_policy, fixture.id).toBe("forbidden");
      }
    }
  });

  it("includes the required Britton messy prompt examples in the actual-intelligence bank", () => {
    const promptText = actualIntelligenceFixtures.map((fixture) => fixture.messy_prompt).join("\n");

    for (const example of [
      "make me a new scout thing that lets me save design inspo but dont let it crawl or auto do stuff yet",
      "the coding page is still acting like a blocker dashboard make it show what changed and what to do next",
      "i asked for a tiny api status thing and it blocked me fix the route gap not the safety",
      "designer should look at this screen and tell coder what component to hit not dump backend evidence",
      "combined flow should critique then code then recheck the screenshot",
      "if the task is already done tell me why with the file evidence instead of calling it blocked",
      "read my messy ask and find the likely file dont ask me unless there are actually two equal targets",
      "add the test that proves the new scout stored-only lane doesnt write proxy memory",
      "fix the copy so failed verification tells me next command not a giant receipt",
      "prove from the frontend that this thing can do a useful small coding task",
    ]) {
      expect(promptText).toContain(example);
    }
  });
});
