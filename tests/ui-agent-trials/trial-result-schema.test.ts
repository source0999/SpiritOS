import { describe, expect, it } from "vitest";

import {
  hasContractFields,
  promptSeparationContractFields,
  trialDiagnosticContractFields,
} from "./trial-result-schema";

describe("trial result contracts", () => {
  it("names the prompt separation fields Britton needs to audit realistic intake", () => {
    expect(promptSeparationContractFields).toEqual([
      "operator_command",
      "operator_run_request",
      "submitted_prompt",
      "prompt_fixture_id",
      "prompt_profile",
      "submitted_through_ui",
      "composer_selector_used",
      "transcript_match",
      "prompt_preview_matches_submitted_prompt",
      "meta_prompt_leak",
    ]);
  });

  it("requires the blocked and failed diagnostic fields for copy-paste debugging", () => {
    const diagnostic = Object.fromEntries(trialDiagnosticContractFields.map((field) => [field, "present"]));

    expect(hasContractFields(diagnostic, trialDiagnosticContractFields)).toBe(true);
    expect(trialDiagnosticContractFields).toContain("reason_code");
    expect(trialDiagnosticContractFields).toContain("expected_behavior");
    expect(trialDiagnosticContractFields).toContain("actual_behavior");
    expect(trialDiagnosticContractFields).toContain("missing_fields");
    expect(trialDiagnosticContractFields).toContain("target_candidates");
    expect(trialDiagnosticContractFields).toContain("selected_files");
    expect(trialDiagnosticContractFields).toContain("preview_diff_produced");
    expect(trialDiagnosticContractFields).toContain("false_block");
    expect(trialDiagnosticContractFields).toContain("recommended_checks");
    expect(trialDiagnosticContractFields).toContain("actual_intelligence_category");
    expect(trialDiagnosticContractFields).toContain("counts_for_coding_usefulness");
    expect(trialDiagnosticContractFields).toContain("disqualifies_live_claim");
    expect(trialDiagnosticContractFields).toContain("copy_paste_block");
  });
});
