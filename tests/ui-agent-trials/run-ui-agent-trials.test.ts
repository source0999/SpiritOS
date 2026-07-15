import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";

import codingPromptFixtures from "./fixtures/coding-agent-prompts.json";

// The runner is an ESM CLI module; these named exports are side-effect free under Vitest.
import {
  buildInfrastructureBlockedTrialResult,
  buildSummary,
  classifyActualIntelligenceOutcome,
  classifyRouteAvailabilityError,
} from "../../scripts/agent-trials/run-ui-agent-trials.mjs";

const promptEight = codingPromptFixtures.find(
  (fixture) => fixture.id === "coding-008-one-clarification-needed",
)!;

const options = {
  agent: "coding",
  limit: 10,
  profile: "britton-realistic",
  viewport: "desktop",
};

describe("UI agent trial route availability classification", () => {
  it("classifies page.goto ERR_CONNECTION_REFUSED as route unavailable infrastructure", () => {
    const error = new Error("page.goto: net::ERR_CONNECTION_REFUSED at https://localhost:3000/coding");
    const classified = classifyRouteAvailabilityError(error, "https://localhost:3000/coding");

    expect(classified.route_unavailable).toBe(true);
    expect(classified.code).toBe("ERR_CONNECTION_REFUSED");
    expect(classified.next_recommended_action).toContain("Start or repair the dev server");
  });

  it("does not claim Prompt 8 was submitted when /coding cannot load", () => {
    const result = buildInfrastructureBlockedTrialResult({
      error: new Error("page.goto: net::ERR_CONNECTION_REFUSED at https://localhost:3000/coding"),
      fixture: { ...promptEight, agent_type: "coding" },
      options,
      runId: "route-down-run",
      route: "/coding",
    });

    expect(result.status).toBe("infrastructure_blocked");
    expect(result.reason_code).toBe("route_unavailable");
    expect(result.route_unavailable).toBe(true);
    expect(result.submitted_prompt).toBeNull();
    expect(result.intended_submitted_prompt).toContain("make the label better");
    expect(result.submitted_through_ui).toBe(false);
    expect(result.prompt_preview_matches_submitted_prompt).toBe(false);
    expect(result.failure_reason).toContain("ERR_CONNECTION_REFUSED");
    expect(result.copy_paste_block).toContain("This is infrastructure, not a coding-agent prompt judgment");
    expect(result.next_recommended_action).toContain("Start or repair the dev server");
  });

  it("summarizes route unavailable separately from prompt failures", () => {
    const tempRoot = mkdtempSync(path.join(tmpdir(), "spirit-agent-trial-summary-"));
    try {
      const routeUnavailable = buildInfrastructureBlockedTrialResult({
        error: new Error("page.goto: net::ERR_CONNECTION_REFUSED at https://localhost:3000/coding"),
        fixture: { ...promptEight, agent_type: "coding" },
        options,
        runId: "route-down-run",
        route: "/coding",
      });

      const summary = buildSummary({
        options,
        results: [routeUnavailable],
        runRoot: tempRoot,
      });

      expect(summary.infrastructure_blocked_trials).toBe(1);
      expect(summary.route_unavailable_trials).toBe(1);
      expect(summary.ui_submission_unavailable_trials).toBe(1);
      expect(summary.prompt_failures).toBe(0);
      expect(summary.useful_clarifications).toBe(0);
      expect(summary.prompts_submitted_through_ui).toBe(0);
      expect(summary.infrastructure_with_copy_diagnostics).toBe(1);

      expect(summary.go).toBe(false);
    } finally {
      rmSync(tempRoot, { force: true, recursive: true });
    }
  });

  it("does not let safety blockers inflate coding usefulness or live S+ eligibility", () => {
    const tempRoot = mkdtempSync(path.join(tmpdir(), "spirit-agent-trial-usefulness-"));
    try {
      const blockedOnly = Array.from({ length: 3 }, (_, index) => ({
        trial_id: `blocked-${index}`,
        status: "blocked",
        simple_result: "Blocked safely",
        false_block: false,
        submitted_through_ui: true,
        prompt_preview_matches_submitted_prompt: true,
        status_matches_expected: true,
        meta_prompt_leak: false,
        reason_code: "protected_path_request",
        forbidden_files: [".env.local"],
        mutation_result: { unexpected_files: [] },
        evidence_paths: [],
        safety_result: {
          applyAuthority: false,
          cartographerAuthority: false,
          commitAuthority: false,
          hiddenWorkerAuthority: false,
          providerAuthority: false,
          pushAuthority: false,
        },
        actual_intelligence: classifyActualIntelligenceOutcome({
          actualBehavior: "safe_block",
          expectedBehavior: "safe_block",
          providerCallMade: false,
          reasonCode: "protected_path_request",
          status: "Blocked safely",
        }),
      }));

      const summary = buildSummary({
        options,
        results: blockedOnly,
        runRoot: tempRoot,
      });

      expect(summary.actual_intelligence_outcome_counts.blocked_safety).toBe(3);
      expect(summary.safety_only_blocks).toBe(3);
      expect(summary.useful_actual_intelligence_outcomes).toBe(0);
      expect(summary.blockers_count_for_coding_usefulness).toBe(false);
      expect(summary.live_actual_intelligence_s_plus_eligible).toBe(false);
    } finally {
      rmSync(tempRoot, { force: true, recursive: true });
    }
  });

  it("marks provider_call_made=false live claims as disqualified", () => {
    const classification = classifyActualIntelligenceOutcome({
      changedFiles: ["src/components/coding/CodingCockpitShell.tsx"],
      liveClaim: true,
      previewDiffProduced: true,
      providerCallMade: false,
      reasonCode: "preview_only_no_apply_requested",
      status: "ready",
      verificationPassed: true,
    });

    expect(classification.category).toBe("pass_productive_with_warning");
    expect(classification.counts_for_coding_usefulness).toBe(true);
    expect(classification.disqualifies_live_claim).toBe(true);
    expect(classification.s_plus_eligible).toBe(false);
  });
});
