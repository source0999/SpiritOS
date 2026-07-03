import { describe, expect, it } from "vitest";

import { selectedPromptAuditDiagnosticsLines } from "@/components/coding/CodingCockpitShell";

describe("selected prompt audit diagnostics", () => {
  it("preserves anti-cheat, hash, recovery, and runtime proof fields for copied diagnostics", () => {
    const lines = selectedPromptAuditDiagnosticsLines({
      grader: {
        provenance: {
          anti_cheat_advisory_ids: ["benchmark_specific_runtime_branch"],
          anti_cheat_hard_fail_ids: [],
          anti_cheat_reasons: ["benchmark_specific_runtime_branch:advisory only"],
          anti_cheat_status: "advisory",
        },
      } as any,
      state: {
        appliedDiffSha256: "applied-hash",
        applyMode: "git_apply_recount",
        approvedDiffSha256: "approved-hash",
        backendConvertedDiffSha256: "backend-hash",
        diffSource: "model_authored_prompt3_file_bundle_backend_converted_to_diff",
        fallbackUsed: false,
        modelFileBundleSha256: "bundle-hash",
        postApplyRediffSha256: "rediff-hash",
        provenanceHashNormalization: "lf_trailing_newline_v1",
        rawModelResponseSha256: "raw-hash",
        stalePatchRecovered: false,
        storefrontProbe: {
          storefront_runtime_engine: "module_loader_fallback",
          storefront_runtime_product_count: 6,
          storefront_runtime_status: "passed",
        } as any,
        trialResultTrustStatus: "model_authored_diff_proven",
      },
    }).join("\n");

    for (const field of [
      "anti_cheat_status",
      "anti_cheat_hard_fail_ids",
      "anti_cheat_advisory_ids",
      "anti_cheat_reasons",
      "raw_model_response_sha256",
      "model_file_bundle_sha256",
      "backend_converted_diff_sha256",
      "approved_diff_sha256",
      "applied_diff_sha256",
      "post_apply_rediff_sha256",
      "provenance_hash_normalization",
      "apply_mode",
      "stale_patch_recovered",
      "fallback_used",
      "diff_source",
      "trial_result_trust_status",
      "storefront_runtime_status",
      "storefront_runtime_engine",
      "storefront_runtime_product_count",
    ]) {
      expect(lines).toContain(`${field}:`);
    }
    expect(lines).toContain("model_authored_diff_proven");
    expect(lines).toContain("module_loader_fallback");
  });
});
