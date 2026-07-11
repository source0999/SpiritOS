import { describe, expect, it } from "vitest";

import {
  selectedPromptAuditDiagnosticsLines,
  selectedPromptFallbackDiagnosticLines,
  selectedPromptFailureDiagnosticLines,
  selectedPromptPreApplyBlockDiagnostic,
} from "@/components/coding/CodingCockpitShell";

describe("selected prompt audit diagnostics", () => {
  it("promotes a backend-verified managed apply receipt to one GO truth", () => {
    const lines = selectedPromptAuditDiagnosticsLines({
      grader: {
        label: "PASS",
        provenance: {
          anti_cheat_advisory_ids: [],
          anti_cheat_hard_fail_ids: [],
          anti_cheat_reasons: [],
          anti_cheat_status: "passed",
        },
      } as any,
      state: {
        appliedDiffSha256: "applied-hash",
        applyMode: "backend_git_apply_with_backup_manifest",
        approvedDiffSha256: "approved-hash",
        backend_anti_cheat_status: "passed",
        backend_anti_cheat_hard_fail_ids: [],
        backend_anti_cheat_advisory_ids: [],
        backend_anti_cheat_reasons: [],
        canonicalContextAcknowledgements: [
          "planner",
          "coder",
          "reviewer",
          "verifier",
          "final_receipt_builder",
        ],
        canonicalContextBlockers: [],
        canonicalContextReportHash: "context-hash",
        canonicalContextVerdict: "GO_ELIGIBLE",
        diffAddedPaths: [],
        diffFilesystemSnapshotSummary: [],
        diffSkippedPaths: [],
        diffSkippedReasons: [],
        generationSource: "model",
        patchVerificationStatus: "passed",
        rawModelResponseSha256: "model-hash",
        structuredBundleAcceptedPaths: [],
        structuredBundleRejectedPaths: [],
        storefrontProbe: {
          browser_evidence_source: "source_proxy_managed_playwright",
          product_count: 6,
          real_browser_used: true,
          storefront_runtime_status: "passed",
        },
        verificationStatus: "post-apply verified with browser proof",
      } as any,
    }).join("\n");

    expect(lines).toContain("apply_status: performed");
    expect(lines).toContain("commit_safe: true");
    expect(lines).toContain("final_truth_status: GO");
    expect(lines).toContain("final_receipt_status: GO");
  });

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
        structuredBundleStatus: "validated",
        structuredBundleParserStage: "patch_verification",
        structuredBundleFileCount: 6,
        structuredBundleAcceptedPaths: [
          "tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
          "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        ],
        structuredBundleRejectedPaths: [],
        structuredBundleRejectionReason: null,
        backend_anti_cheat_status: "fail",
        backend_anti_cheat_hard_fail_ids: ["route_existence_as_integration"],
        backend_anti_cheat_advisory_ids: [],
        backend_anti_cheat_report: "registry failed route-only proof",
        backend_anti_cheat_reasons: ["route-only proof"],
        diffSource: "model_authored_prompt3_file_bundle_backend_converted_to_diff",
        fallbackUsed: false,
        generationSource: "model",
        modelFileBundleSha256: "bundle-hash",
        modelOutputShapeSummary: "length=1200; has_xml_file_blocks=true",
        diffGenerationStatus: "produced_diff",
        diffGenerationReason: "model_bundle_converted_to_unified_diff",
        diffFileCount: 2,
        diffAddedPaths: [
          "tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
          "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        ],
        diffSkippedPaths: [],
        diffSkippedReasons: [],
        diffFilesystemSnapshotSummary: [],
        patchVerificationStatus: "passed",
        patchVerificationReason: "git apply --check passed",
        taskCreationStatus: "persisted_task_id",
        taskCreationElapsedMs: 42,
        taskCreationTimeoutStage: "not_applicable: task_id_persisted",
        taskCreationLastCheckpoint: "task_envelope_built",
        taskCreationBlockingSubsystem: "not_applicable: task_id_persisted",
        postApplyRediffSha256: "rediff-hash",
        provenanceHashNormalization: "lf_trailing_newline_v1",
        rawModelResponseSha256: "raw-hash",
        stalePatchRecovered: false,
        storefrontProbe: {
          storefront_runtime_engine: "playwright_chromium",
          real_browser_used: true,
          browser_evidence_source: "source_proxy_managed_playwright",
          storefront_runtime_product_count: 6,
          storefront_runtime_status: "passed",
        } as any,
        trialResultTrustStatus: "model_authored_diff_proven",
        verificationStatus: "post-apply verified with browser proof",
        canonicalContextVerdict: "GO_ELIGIBLE",
        canonicalContextReportHash: "context-hash",
        canonicalContextBlockers: [],
        canonicalContextAcknowledgements: [
          "planner",
          "coder",
          "reviewer",
          "verifier",
          "final_receipt_builder",
        ],
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
      "structured_bundle_status",
      "structured_bundle_parser_stage",
      "structured_bundle_file_count",
      "structured_bundle_accepted_paths",
      "structured_bundle_rejected_paths",
      "structured_bundle_rejection_reason",
      "model_output_shape_summary",
      "diff_generation_status",
      "diff_generation_reason",
      "diff_file_count",
      "diff_added_paths",
      "diff_skipped_paths",
      "diff_skipped_reasons",
      "patch_verification_status",
      "patch_verification_reason",
      "task_creation_status",
      "task_creation_elapsed_ms",
      "task_creation_timeout_stage",
      "task_creation_last_checkpoint",
      "task_creation_blocking_subsystem",
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
      "browser_evidence_source",
      "real_browser_used",
    ]) {
      expect(lines).toContain(`${field}:`);
    }
    expect(lines).toContain("model_authored_diff_proven");
    expect(lines).toContain("playwright_chromium");
    expect(lines).toContain("browser_evidence_source: source_proxy_managed_playwright");
    expect(lines).toContain("real_browser_used: true");
  });

  it.each(["blocked", "fail"])(
    "keeps a backend anti-cheat %s authoritative over a frontend grader PASS",
    (backendStatus) => {
      const lines = selectedPromptAuditDiagnosticsLines({
        grader: {
          label: "PASS",
          provenance: {
            anti_cheat_advisory_ids: [],
            anti_cheat_hard_fail_ids: [],
            anti_cheat_reasons: [],
            anti_cheat_status: "passed",
          },
        } as any,
        state: {
          appliedDiffSha256: "applied-hash",
          applyMode: "backend_git_apply_with_backup_manifest",
          approvedDiffSha256: "approved-hash",
          backendConvertedDiffSha256: "backend-hash",
          backend_anti_cheat_status: backendStatus,
          backend_anti_cheat_hard_fail_ids: ["backend_integrity_failure"],
          backend_anti_cheat_advisory_ids: [],
          backend_anti_cheat_report: "Backend anti-cheat blocked the run.",
          backend_anti_cheat_reasons: ["backend proof failed"],
          canonicalContextAcknowledgements: [
            "planner",
            "coder",
            "reviewer",
            "verifier",
            "final_receipt_builder",
          ],
          canonicalContextBlockers: [],
          canonicalContextReportHash: "context-hash",
          canonicalContextVerdict: "GO_ELIGIBLE",
          diffAddedPaths: [],
          diffFilesystemSnapshotSummary: [],
          diffSkippedPaths: [],
          diffSkippedReasons: [],
          diffSource: "model_authored_diff",
          fallbackUsed: false,
          generationSource: "model",
          modelFileBundleSha256: "bundle-hash",
          patchVerificationStatus: "passed",
          postApplyRediffSha256: "rediff-hash",
          provenanceHashNormalization: "lf_trailing_newline_v1",
          rawModelResponseSha256: "raw-hash",
          stalePatchRecovered: false,
          storefrontProbe: {
            product_count: 6,
            storefront_runtime_engine: "playwright_chromium",
            storefront_runtime_product_count: 6,
            storefront_runtime_status: "passed",
          } as any,
          structuredBundleAcceptedPaths: [],
          structuredBundleRejectedPaths: [],
          trialResultTrustStatus: "model_authored_diff_proven",
          verificationStatus: "post-apply verified with browser proof",
        } as any,
      });

      expect(lines).toContain("grader_anti_cheat_status: fail");
      expect(lines).toContain("anti_cheat_status: fail");
      expect(lines).toContain("anti_cheat_hard_fail_ids: backend_integrity_failure");
      expect(lines).toContain("anti_cheat_reasons: backend proof failed");
      expect(lines).toContain("commit_safe: false");
      expect(lines).toContain("final_truth_status: BLOCKED_SAFE");
      expect(lines).toContain("final_receipt_status: BLOCKED_SAFE");
    },
  );

  it("surfaces approval mismatch failure envelope fields for selected prompt copyout", () => {
    const lines = selectedPromptFailureDiagnosticLines({
      reason_code: "approval_id_mismatch",
      approval_binding: {
        approval_binding_status: "failed",
        approval_binding_safe_block: true,
        approval_binding_failure_reason: "approval_id_mismatch",
        expected_approval_id: "approval-expected",
        received_approval_id: "approval-received",
        task_id_match: true,
        target_match: true,
        diff_sha256_match: false,
        canonicalization_changed: true,
        safe_block: true,
      },
      anti_cheat: {
        anti_cheat_status: "not_run",
        anti_cheat_reasons: ["skipped_due_to_apply_block"],
      },
      final_truth_summary: {
        truth_status: "BLOCKED_SAFE",
        commit_safe: false,
        proof_level: "fixture_only",
      },
      verification: {
        post_apply_verification_status: "skipped_due_to_apply_block",
      },
    }).join("\n");

    for (const field of [
      "approval_binding_status: failed",
      "approval_binding_safe_block: true",
      "approval_binding_failure_reason: approval_id_mismatch",
      "expected_approval_id: approval-expected",
      "received_approval_id: approval-received",
      "task_id_match: true",
      "target_match: true",
      "diff_sha256_match: false",
      "canonicalization_changed: true",
      "safe_block: true",
      "anti_cheat_status: not_run",
      "post_apply_verification_status: skipped_due_to_apply_block",
      "truth_status: BLOCKED_SAFE",
      "commit_safe: false",
      "proof_level: fixture_only",
    ]) {
      expect(lines).toContain(field);
    }
  });

  it("surfaces valid approval binding receipt fields after apply still needs verification", () => {
    const lines = selectedPromptFailureDiagnosticLines({
      reason_code: "post_apply_verification_required",
      approval_binding: {
        approval_binding_status: "valid",
        approval_binding_failure_reason: "not_applicable: approval_binding_valid",
        expected_approval_id: "approval-matched",
        received_approval_id: "approval-matched",
        task_id_match: true,
        target_match: true,
        diff_sha256_match: true,
        apply_block_layer: "not_applicable: apply_succeeded",
        block_receipt_path: ".spirit-backups/manifest.json",
        safe_block: false,
      },
      anti_cheat: {
        anti_cheat_status: "not_applicable: execute_approved_apply_gate",
        anti_cheat_reasons: ["not_applicable: backend apply receipt is not the frontend anti-cheat grader"],
      },
      acceptance_gate: {
        binary_verdict: "GO",
        causal_crosscheck_status: "GO",
        fail_closed_lane_status: "GO",
        phase_verifier_status: "GO",
        plan5_gate_id: "plan5_execute_approved_acceptance",
        plan5_gate_present: true,
      },
      final_truth_summary: {
        truth_status: "BLOCKED_SAFE",
        commit_safe: false,
        proof_level: "approved_apply_receipt",
      },
      verification: {
        post_apply_verification_status: "manual_verification_required",
        commit_blockers: ["post_apply_verification_incomplete"],
      },
    }).join("\n");

    for (const field of [
      "reason_code: post_apply_verification_required",
      "approval_binding_status: valid",
      "approval_binding_failure_reason: not_applicable: approval_binding_valid",
      "expected_approval_id: approval-matched",
      "received_approval_id: approval-matched",
      "task_id_match: true",
      "target_match: true",
      "diff_sha256_match: true",
      "apply_block_layer: not_applicable: apply_succeeded",
      "block_receipt_path: .spirit-backups/manifest.json",
      "anti_cheat_status: not_applicable: execute_approved_apply_gate",
      "binary_verdict: GO",
      "causal_crosscheck_status: GO",
      "fail_closed_lane_status: GO",
      "phase_verifier_status: GO",
      "plan5_gate_id: plan5_execute_approved_acceptance",
      "plan5_gate_present: true",
      "post_apply_verification_status: manual_verification_required",
      "truth_status: BLOCKED_SAFE",
      "commit_safe: false",
      "proof_level: approved_apply_receipt",
    ]) {
      expect(lines).toContain(field);
    }
    expect(lines).not.toContain("missing: no diagnostic envelope received");
  });

  it("uses reasoned missing/not-run fallback text instead of bare diagnostic placeholders", () => {
    const lines = selectedPromptAuditDiagnosticsLines({
      grader: null,
      state: {
        appliedDiffSha256: null,
        applyMode: null,
        approvedDiffSha256: null,
        backendConvertedDiffSha256: null,
        structuredBundleStatus: null,
        structuredBundleParserStage: null,
        structuredBundleFileCount: null,
        structuredBundleAcceptedPaths: [],
        structuredBundleRejectedPaths: [],
        structuredBundleRejectionReason: null,
        backend_anti_cheat_status: null,
        backend_anti_cheat_hard_fail_ids: [],
        backend_anti_cheat_advisory_ids: [],
        backend_anti_cheat_report: null,
        backend_anti_cheat_reasons: [],
        diffSource: null,
        fallbackUsed: null,
        generationSource: null,
        modelFileBundleSha256: null,
        modelOutputShapeSummary: null,
        diffGenerationStatus: null,
        diffGenerationReason: null,
        diffFileCount: null,
        diffAddedPaths: [],
        diffSkippedPaths: [],
        diffSkippedReasons: [],
        diffFilesystemSnapshotSummary: [],
        patchVerificationStatus: null,
        patchVerificationReason: null,
        taskCreationStatus: null,
        taskCreationElapsedMs: null,
        taskCreationTimeoutStage: null,
        taskCreationLastCheckpoint: null,
        taskCreationBlockingSubsystem: null,
        postApplyRediffSha256: null,
        provenanceHashNormalization: null,
        rawModelResponseSha256: null,
        stalePatchRecovered: null,
        storefrontProbe: null,
        trialResultTrustStatus: null,
        verificationStatus: null,
        canonicalContextVerdict: null,
        canonicalContextReportHash: null,
        canonicalContextBlockers: [],
        canonicalContextAcknowledgements: [],
      },
    });

    expect(lines.join("\n")).toContain("anti_cheat_status: missing: no diagnostic envelope received");
    expect(lines.join("\n")).toContain("anti_cheat_reasons: missing: backend did not provide field");
    expect(lines.join("\n")).not.toMatch(/: not graded$/m);
    expect(lines.join("\n")).not.toMatch(/: not recorded$/m);
    expect(lines.join("\n")).not.toMatch(/: none$/m);
  });

  it("prints explicit not-applicable approval binding fields for pre-apply selected prompt blocks", () => {
    const lines = selectedPromptFallbackDiagnosticLines({
      backend_anti_cheat_advisory_ids: [],
      backend_anti_cheat_hard_fail_ids: [],
      backend_anti_cheat_reasons: [],
      backend_anti_cheat_report: null,
      backend_anti_cheat_status: null,
      backendConvertedDiffSha256: null,
      structuredBundleStatus: "rejected",
      structuredBundleParserStage: "content_validation",
      structuredBundleFileCount: 1,
      structuredBundleAcceptedPaths: [],
      structuredBundleRejectedPaths: ["package.json"],
      structuredBundleRejectionReason: "Create-mode file bundle failed dummy-root validation.",
      approvedDiffSha256: null,
      appliedDiffSha256: null,
      applyMode: null,
      changedFiles: [],
      checksRun: [],
      diffSource: null,
      errorText: null,
      fallbackUsed: null,
      finishedAt: Date.now(),
      generatedDiffByBackend: null,
      generationSource: null,
      grader: null,
      lastFailureDiagnostics: null,
      message: "Backend diff generation failed.",
      modelFileBundleSha256: null,
      modelOutputShapeSummary: "length=42; has_json_create_file_bundle=true",
      diffGenerationStatus: "blocked_no_diff",
      diffGenerationReason: "content_validation_failed",
      diffFileCount: 0,
      diffAddedPaths: [],
      diffSkippedPaths: ["package.json"],
      diffSkippedReasons: ["package.json: content_validation_failed"],
      diffFilesystemSnapshotSummary: [],
      patchVerificationStatus: "not_run",
      patchVerificationReason: "not_run: content_validation_failed",
      taskCreationStatus: "persisted_task_id",
      taskCreationElapsedMs: 18,
      taskCreationTimeoutStage: "not_applicable: task_id_persisted",
      taskCreationLastCheckpoint: "task_envelope_built",
      taskCreationBlockingSubsystem: "not_applicable: task_id_persisted",
      modelOutputClassification: null,
      noDiffFailureCause: null,
      packet: null,
      parserExtractorDecision: null,
      postApplyRediffSha256: null,
      provenanceHashNormalization: null,
      rawBackendStatus: "coder_backend_diff_generation_failed",
      rawModelResponseSha256: null,
      recommendedNextAction: "Clear dirty fixture state and rerun.",
      scaffoldUsed: null,
      selectedPromptId: "coder-001-init-dummy-product-site",
      stalePatchRecovered: null,
      startedAt: Date.now(),
      status: "blocked",
      storefrontProbe: null,
      taskId: "task-preapply",
      trialResultTrustStatus: null,
      verificationStatus: null,
      canonicalContextVerdict: null,
      canonicalContextReportHash: null,
      canonicalContextBlockers: [],
      canonicalContextAcknowledgements: [],
    }).join("\n");

    for (const field of [
      "truth_status: BLOCKED_SAFE",
      "reason_code: coder_backend_diff_generation_failed",
      "structured_bundle_status: rejected",
      "structured_bundle_file_count: 1",
      "structured_bundle_accepted_paths: missing: backend did not provide field",
      "structured_bundle_rejected_paths: package.json",
      "diff_generation_status: blocked_no_diff",
      "diff_generation_reason: content_validation_failed",
      "diff_file_count: 0",
      "diff_added_paths: not_applicable: no added paths",
      "diff_filesystem_snapshot_summary: not_applicable: no filesystem snapshot summary",
      "diff_skipped_paths: package.json",
      "diff_skipped_reasons: package.json: content_validation_failed",
      "patch_verification_status: not_run",
      "patch_verification_reason: not_run: content_validation_failed",
      "task_creation_status: persisted_task_id",
      "task_creation_elapsed_ms: 18",
      "task_creation_timeout_stage: not_applicable: task_id_persisted",
      "task_creation_last_checkpoint: task_envelope_built",
      "task_creation_blocking_subsystem: not_applicable: task_id_persisted",
      "approval_binding_status: not_run: execute_approved_not_reached",
      "approval_binding_failure_reason: not_applicable: execute_approved_not_reached",
      "expected_approval_id: not_applicable: execute_approved_not_reached",
      "received_approval_id: not_applicable: execute_approved_not_reached",
      "apply_block_layer: selected_prompt_pre_apply",
      "block_receipt_path: not_applicable: execute_approved_not_reached",
      "safe_block: true",
      "binary_verdict: NO-GO",
      "causal_crosscheck_status: skipped_with_reason",
      "fail_closed_lane_status: skipped_with_reason",
      "phase_verifier_status: skipped_with_reason",
      "plan5_gate_id: plan5_selected_prompt_pre_apply_block",
      "plan5_gate_present: false",
      "post_apply_verification_status: not_run: execute_approved_not_reached",
      "post_apply_verification_reason: not_applicable: execute_approved_not_reached",
      "verification_required_action: Resolve the pre-apply block, then rerun the selected prompt.",
      "commit_safe: false",
      "commit_safe_reason: selected_prompt_not_verified",
      "recommended_next_action: Clear dirty fixture state and rerun.",
    ]) {
      expect(lines).toContain(field);
    }
  });

  it("builds a safe fixture-baseline block receipt when dirty Prompt 1 cleanup fails", () => {
    const lines = selectedPromptFailureDiagnosticLines(
      selectedPromptPreApplyBlockDiagnostic({
        dirtyFiles: [
          "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
          "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        ],
        message: "Dummy fixture cleanup did not reach a clean baseline.",
        reasonCode: "dirty_dummy_fixture_reset_incomplete",
        selectedPromptId: "coder-001-init-dummy-product-site",
      }),
    ).join("\n");

    for (const field of [
      "truth_status: BLOCKED_SAFE",
      "reason_code: dirty_dummy_fixture_reset_incomplete",
      "approval_binding_status: not_run: execute_approved_not_reached",
      "expected_approval_id: not_applicable: execute_approved_not_reached",
      "received_approval_id: not_applicable: execute_approved_not_reached",
      "apply_block_layer: selected_prompt_pre_apply",
      "block_receipt_path: not_applicable: apply_did_not_happen",
      "safe_block: true",
      "anti_cheat_status: not_run",
      "anti_cheat_reasons: dirty_dummy_fixture_reset_incomplete",
      "binary_verdict: NO-GO",
      "causal_crosscheck_status: skipped_with_reason",
      "fail_closed_lane_status: skipped_with_reason",
      "phase_verifier_status: skipped_with_reason",
      "plan5_gate_id: plan5_selected_prompt_pre_apply_block",
      "plan5_gate_present: false",
      "post_apply_verification_status: not_run: execute_approved_not_reached",
      "post_apply_verification_reason: dirty_dummy_fixture_reset_incomplete",
      "verification_required_action: Verify the dummy fixture baseline, then rerun Prompt 1 from a clean missing-fixture state.",
      "commit_safe: false",
      "commit_safe_reason: dirty_dummy_fixture_reset_incomplete",
    ]) {
      expect(lines).toContain(field);
    }
  });

  it("prints structured missing-envelope route failure diagnostics", () => {
    const lines = selectedPromptFailureDiagnosticLines({
      reason_code: "network_fetch_error",
      approval_binding: {
        approval_binding_status: "not_run: route_error_before_model_call",
        safe_block: true,
        apply_block_layer: "route_error_before_model_call",
        block_receipt_path: "not_applicable: route_error_before_model_call_before_apply_receipt",
      },
      anti_cheat: {
        anti_cheat_status: "not_run",
        anti_cheat_reasons: ["route_error_before_model_call"],
      },
      acceptance_gate: {
        binary_verdict: "NO-GO",
        phase_verifier_status: "skipped_with_reason",
        fail_closed_lane_status: "skipped_with_reason",
        causal_crosscheck_status: "skipped_with_reason",
        plan5_gate_present: false,
      },
      final_truth_summary: {
        truth_status: "MISSING_DIAGNOSTIC_ENVELOPE",
        recommended_next_action: "Inspect Source Proxy route health.",
      },
    }).join("\n");

    expect(lines).toContain("truth_status: MISSING_DIAGNOSTIC_ENVELOPE");
    expect(lines).toContain("reason_code: network_fetch_error");
    expect(lines).toContain("approval_binding_status: not_run: route_error_before_model_call");
    expect(lines).toContain("block_receipt_path: not_applicable: route_error_before_model_call_before_apply_receipt");
    expect(lines).toContain("anti_cheat_status: not_run");
    expect(lines).toContain("anti_cheat_reasons: route_error_before_model_call");
    expect(lines).toContain("phase_verifier_status: skipped_with_reason");
    expect(lines).not.toMatch(/: not graded$/m);
    expect(lines).not.toMatch(/: not recorded$/m);
    expect(lines).not.toMatch(/: none$/m);
  });
});
