import { describe, expect, it } from "vitest";

import { mapVisibleResultBadge } from "@/lib/coding/visible-result-badge";

describe("visible result badge mapper", () => {
  it("maps a simulated design report to PREVIEW ONLY with live proof warning", () => {
    const badge = mapVisibleResultBadge({
      status: "design",
      visible_failure: "none visible",
      provider_call_made: false,
      model_called_for_generation: "none",
      hermes_used_for_this_run: "not_called",
      next_action: "Use this design result as implementation context.",
    });

    expect(badge).toMatchObject({
      primary_label: "PREVIEW ONLY",
      primary_tone: "neutral",
      should_count_as_productive: false,
      should_count_as_live_model_proof: false,
      live_model_proof_status: "not_live_model_proof",
    });
    expect(badge.plain_summary).toBe("Preview-only diagnostic run. Not live proof.");
    expect(badge.secondary_badges.map((item) => item.label)).toContain("WARNING: No live model call");
  });

  it("maps productive preview warnings to PASS WITH WARNING", () => {
    const badge = mapVisibleResultBadge({
      actual_behavior: "productive_preview",
      actual_intelligence_category: "pass_productive_with_warning",
      result_category: "productive_preview",
      preview_changed_files: ["source_proxy/proxy_memory/scout_intake.py"],
      provider_call_made: true,
      model_called_for_generation: "ollama_chat/hermes4:latest",
      hermes_used_for_this_run: "yes",
    });

    expect(badge.primary_label).toBe("PREVIEW ONLY");
    expect(badge.primary_tone).toBe("neutral");
    expect(badge.should_count_as_productive).toBe(false);
    expect(badge.should_count_as_live_model_proof).toBe(true);
  });

  it("adds NOT LIVE MODEL PROOF when no provider call was made", () => {
    const badge = mapVisibleResultBadge({
      actual_behavior: "productive_preview",
      result_category: "productive_preview",
      provider_call_made: false,
      model_called_for_generation: "none",
      hermes_used_for_this_run: "not_called",
    });

    expect(badge.primary_label).toBe("PREVIEW ONLY");
    expect(badge.secondary_badges.map((item) => item.label)).toContain("WARNING: No live model call");
    expect(badge.live_model_proof_status).toBe("not_live_model_proof");
  });

  it("maps protected path blocks to BLOCKED plus safety success", () => {
    const badge = mapVisibleResultBadge({
      actual_behavior: "safe_block",
      reason_code: "protected_path_request",
      result_category: "blocked_for_safety",
      provider_call_made: false,
    });

    expect(badge.primary_label).toBe("BLOCKED");
    expect(badge.primary_tone).toBe("warning");
    expect(badge.secondary_badges.map((item) => item.label)).toContain("PASS: Safety gate worked");
    expect(badge.user_next_action).toBe("No files changed.");
  });

  it("maps missing scope clarification to WARNING instead of a safety block", () => {
    const badge = mapVisibleResultBadge({
      actual_behavior: "clarification_needed",
      reason_code: "manual_clarification_needed",
      result_category: "blocked_missing_scope",
      safety_state: "blocked",
      provider_call_made: false,
      model_called_for_generation: "none",
      hermes_used_for_this_run: "not_called",
    });

    expect(badge.primary_label).toBe("WARNING");
    expect(badge.primary_tone).toBe("warning");
    expect(badge.plain_summary).toBe("Needs a target or file before preview.");
    expect(badge.secondary_badges.map((item) => item.label)).not.toContain("PASS: Safety gate worked");
  });

  it("maps actual failed generation to FAIL", () => {
    const badge = mapVisibleResultBadge({
      actual_behavior: "failed",
      reason_code: "preview_generation_failed",
      result_category: "failed_verification",
      simple_result: "Failed",
    });

    expect(badge.primary_label).toBe("FAIL");
    expect(badge.primary_tone).toBe("danger");
    expect(badge.user_next_action).toBe("Copy diagnostics.");
  });

  it("maps live apply proof to LIVE PASS only when apply, disk, checks, and reversal exist", () => {
    const badge = mapVisibleResultBadge({
      allowed_files: ["src/demo.ts"],
      applied_changed_files: ["src/demo.ts"],
      checks_run: ["git diff --check"],
      disk_changed_files: ["src/demo.ts"],
      hermes_used_for_this_run: "yes",
      model_called_for_generation: "ollama_chat/hermes4:latest",
      preview_changed_files: ["src/demo.ts"],
      provider_call_made: true,
      reversal_available: true,
      status: "applied",
      trial_mode: "live_apply",
    });

    expect(badge.primary_label).toBe("LIVE PASS");
    expect(badge.live_apply_proof_status).toBe("proven");
    expect(badge.score_counts_as_live_usefulness).toBe(true);
  });
});
