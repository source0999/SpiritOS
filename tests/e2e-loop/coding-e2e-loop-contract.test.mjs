import assert from "node:assert/strict";
import test from "node:test";

import {
  E2E_LOOP_SCHEMA_VERSION,
  buildAuthoritativeFinalTruth,
  repoRootsMatch,
} from "../../scripts/coding-e2e-loop-contract.mjs";

const expectedPrompt1Paths = [
  "tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
  "tests/ui-agent-trials/fixtures/dummy-product-site/package.json",
  "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
  "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
  "tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
  "tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
];

const restoredFiles = () => expectedPrompt1Paths.map((path) => ({
  path,
  verified: true,
  absent: true,
  actual_sha256: null,
}));

const missingFileProbes = (reasonCode = "not_found") => expectedPrompt1Paths.map((path) => ({
  path,
  http_status: 400,
  reason_code: reasonCode,
  missing: true,
}));

const unrelatedWorktreeProof = () => ({
  status: "GO",
  snapshot_matches: true,
  tracked_diff_matches: true,
  untracked_files_match: true,
  before_snapshot_sha256: "a".repeat(64),
  after_snapshot_sha256: "a".repeat(64),
  changed_paths: [],
});

const goCapture = () => ({
  schema_version: E2E_LOOP_SCHEMA_VERSION,
  authoritative_stages: {
    context: { status: "GO" },
    post_apply_verification: { status: "GO" },
    browser_verification: { status: "GO" },
    anti_cheat: { status: "GO" },
    final_receipt: { status: "GO", commit_safe: true },
    diagnostic_consistency: { status: "GO" },
    prompt1_initial_run: {
      status: "GO",
      task_id: "task_initial",
      terminal_status: "applied",
      apply_status: "performed",
      post_apply_verification_status: "GO",
      browser_verification_status: "GO",
      final_receipt_status: "GO",
      final_receipt_path: ".source-proxy/backups/task_initial/manifest.json",
      commit_safe: true,
      grader_label: "PASS",
      trial_result_trust_status: "model_authored_diff_proven",
      changed_files_present: true,
      expected_prompt1_changed_files: true,
      changed_paths: expectedPrompt1Paths,
      fixture_was_clean_before_run: true,
      already_satisfied: false,
      lifecycle_sequence: 1,
      run_started_at_ms: 100,
      run_completed_at_ms: 200,
      canonical_stages: {
        context: "GO",
        post_apply_verification: "GO",
        browser_verification: "GO",
        anti_cheat: "GO",
        final_receipt: "GO",
        diagnostic_consistency: "GO",
      },
    },
    manifest_backed_undo: {
      status: "GO",
      ui_triggered: true,
      request_confirm_undo: true,
      requested_by: "coding-ui",
      original_task_id: "task_initial",
      initial_final_receipt_path: ".source-proxy/backups/task_initial/manifest.json",
      expected_backup_manifest: ".source-proxy/backups/task_initial/manifest.json",
      selected_backup_manifest: ".source-proxy/backups/task_initial/manifest.json",
      undo_receipt_id: "undo-123",
      undo_receipt_path: ".source-proxy/backups/task_initial/undo-receipt.json",
      filesystem_verified: true,
      untouched_scope_assertion: true,
      expected_browser_state: "fixture_missing",
      unrelated_paths_touched: [],
      independent_unrelated_worktree: unrelatedWorktreeProof(),
      all_expected_files_restored: true,
      all_restored_to_absent: true,
      restored_paths: expectedPrompt1Paths,
      files_restored: restoredFiles(),
      persisted_receipt_verified: true,
      persisted_selected_backup_manifest: ".source-proxy/backups/task_initial/manifest.json",
      persisted_restored_paths: expectedPrompt1Paths,
      persisted_files_restored: restoredFiles(),
      persisted_files_restored_verified: true,
      open_diff_marked_undone: true,
      ui_pre_reset_preview_http_status: 404,
      ui_pre_reset_preview_missing: true,
      ui_pre_reset_baseline_http_status: 200,
      ui_pre_reset_baseline_checked: true,
      ui_pre_reset_baseline_clean_for_fresh_suite: true,
      ui_pre_reset_baseline_dirty_files: [],
      ui_pre_reset_dummy_fixture_dirty_files: [],
      lifecycle_sequence: 2,
      response_observed_at_ms: 210,
      response_sequence: 20,
    },
    clean_baseline_after_undo: {
      status: "GO",
      baseline_http_status: 200,
      baseline_clean_for_fresh_suite: true,
      baseline_dirty_agent_lab_files: [],
      dummy_fixture_dirty_files: [],
      file_probes: missingFileProbes(),
      all_fixture_files_absent: true,
      preview_http_status: 404,
      lifecycle_sequence: 4,
      verified_after_product_reset: true,
      probe_started_after_product_reset: true,
      probe_started_at_ms: 230,
      probe_completed_at_ms: 240,
      verified_after_reset_response_sequence: 24,
    },
    product_reset_after_undo: {
      status: "GO",
      ui_triggered: true,
      http_status: 200,
      response_status: "reset_verified",
      reset_verified: true,
      clean_verified: true,
      occurred_after_undo: true,
      reset_receipt_id: "reset-123",
      lifecycle_sequence: 3,
      response_observed_at_ms: 220,
      response_sequence: 24,
    },
    prompt1_clean_rerun: {
      status: "GO",
      task_id: "task_rerun",
      terminal_status: "applied",
      apply_status: "performed",
      post_apply_verification_status: "GO",
      browser_verification_status: "GO",
      final_receipt_status: "GO",
      final_receipt_path: ".source-proxy/backups/task_rerun/manifest.json",
      commit_safe: true,
      grader_label: "PASS",
      trial_result_trust_status: "model_authored_diff_proven",
      changed_files_present: true,
      expected_prompt1_changed_files: true,
      changed_paths: expectedPrompt1Paths,
      fixture_was_clean_before_run: true,
      already_satisfied: false,
      distinct_from_initial_task: true,
      started_after_clean_baseline: true,
      started_after_product_reset: true,
      lifecycle_sequence: 5,
      run_started_at_ms: 250,
      run_completed_at_ms: 300,
      unrelated_workspace_preservation: unrelatedWorktreeProof(),
      canonical_stages: {
        context: "GO",
        post_apply_verification: "GO",
        browser_verification: "GO",
        anti_cheat: "GO",
        final_receipt: "GO",
        diagnostic_consistency: "GO",
      },
    },
  },
});

test("managed root identity compares normalized exact roots", () => {
  assert.equal(repoRootsMatch("/home/source/SpiritOS/", "/home/source/SpiritOS"), true);
  assert.equal(repoRootsMatch("/home/source/SpiritOS", "/home/source/other"), false);
  assert.equal(repoRootsMatch("/home/source/SpiritOS", ""), false);
});

test("authoritative truth is GO only when every required stage and commit-safe receipt are GO", () => {
  const truth = buildAuthoritativeFinalTruth({ capture: goCapture(), steps: [{ name: "health", ok: true }] });
  assert.equal(truth.schema_version, E2E_LOOP_SCHEMA_VERSION);
  assert.equal(truth.truth_status, "GO");
  assert.equal(truth.commit_safe, true);
  assert.deepEqual(truth.failed_requirements, []);
});

test("legacy not_file missing probes remain accepted", () => {
  const capture = goCapture();
  capture.authoritative_stages.clean_baseline_after_undo.file_probes = missingFileProbes("not_file");
  const truth = buildAuthoritativeFinalTruth({ capture, steps: [{ name: "health", ok: true }] });
  assert.equal(truth.truth_status, "GO");
});

test("hardcoded untouched claims cannot replace independent worktree comparison", () => {
  const capture = goCapture();
  delete capture.authoritative_stages.manifest_backed_undo.independent_unrelated_worktree;
  capture.authoritative_stages.prompt1_clean_rerun.unrelated_workspace_preservation.changed_paths = [
    "src/unrelated.ts",
  ];
  capture.authoritative_stages.prompt1_clean_rerun.unrelated_workspace_preservation.status = "NO_GO";

  const truth = buildAuthoritativeFinalTruth({ capture, steps: [{ name: "health", ok: true }] });
  assert.equal(truth.truth_status, "NO_GO");
  assert.deepEqual(truth.failed_requirements, [
    "manifest_backed_undo:INCOMPLETE_EVIDENCE",
    "prompt1_clean_rerun:INCOMPLETE_EVIDENCE",
  ]);
});

test("anti-cheat failure and missing post-apply proof fail closed", () => {
  const capture = goCapture();
  capture.authoritative_stages.anti_cheat = { status: "NO_GO" };
  delete capture.authoritative_stages.post_apply_verification;
  const truth = buildAuthoritativeFinalTruth({ capture, steps: [{ name: "health", ok: true }] });
  assert.equal(truth.truth_status, "NO_GO");
  assert.equal(truth.commit_safe, false);
  assert.deepEqual(truth.failed_requirements, ["post_apply_verification:MISSING", "anti_cheat:NO_GO"]);
});

test("failed infrastructure step overrides otherwise green product stages", () => {
  const truth = buildAuthoritativeFinalTruth({
    capture: goCapture(),
    steps: [{ name: "product_reset", ok: false }],
  });
  assert.equal(truth.truth_status, "NO_GO");
  assert.equal(truth.failed_requirements[0], "infrastructure_or_harness_step_failed");
});

test("GO-labeled receipt without commit-safe proof is rejected", () => {
  const capture = goCapture();
  capture.authoritative_stages.final_receipt.commit_safe = false;
  const truth = buildAuthoritativeFinalTruth({ capture, steps: [{ name: "health", ok: true }] });
  assert.equal(truth.truth_status, "NO_GO");
  assert.equal(truth.commit_safe, false);
  assert.deepEqual(truth.failed_requirements, ["final_receipt:COMMIT_UNSAFE"]);
});

test("legacy one-pass capture without Undo, reset, and clean rerun proof is rejected", () => {
  const capture = goCapture();
  delete capture.authoritative_stages.manifest_backed_undo;
  delete capture.authoritative_stages.clean_baseline_after_undo;
  delete capture.authoritative_stages.product_reset_after_undo;
  delete capture.authoritative_stages.prompt1_clean_rerun;
  const truth = buildAuthoritativeFinalTruth({ capture, steps: [{ name: "health", ok: true }] });
  assert.equal(truth.truth_status, "NO_GO");
  assert.deepEqual(truth.failed_requirements, [
    "manifest_backed_undo:MISSING",
    "clean_baseline_after_undo:MISSING",
    "product_reset_after_undo:MISSING",
    "prompt1_clean_rerun:MISSING",
  ]);
});

test("GO labels cannot hide incomplete or out-of-order lifecycle evidence", () => {
  const capture = goCapture();
  capture.authoritative_stages.manifest_backed_undo.persisted_receipt_verified = false;
  capture.authoritative_stages.product_reset_after_undo.response_sequence = 19;
  capture.authoritative_stages.prompt1_clean_rerun.task_id = "task_initial";
  const truth = buildAuthoritativeFinalTruth({ capture, steps: [{ name: "health", ok: true }] });
  assert.equal(truth.truth_status, "NO_GO");
  assert.deepEqual(truth.failed_requirements, [
    "manifest_backed_undo:INCOMPLETE_EVIDENCE",
    "clean_baseline_after_undo:INCOMPLETE_EVIDENCE",
    "product_reset_after_undo:INCOMPLETE_EVIDENCE",
    "prompt1_clean_rerun:INCOMPLETE_EVIDENCE",
  ]);
});

test("a stale capture schema cannot be promoted to the current authoritative truth", () => {
  const capture = goCapture();
  capture.schema_version = "coding-e2e-loop/v2";
  const truth = buildAuthoritativeFinalTruth({ capture, steps: [{ name: "health", ok: true }] });
  assert.equal(truth.truth_status, "NO_GO");
  assert.deepEqual(truth.failed_requirements, ["schema_version:coding-e2e-loop/v2"]);
});

test("summary booleans cannot replace exact changed, restored, and missing-file evidence", () => {
  const capture = goCapture();
  capture.authoritative_stages.prompt1_initial_run.changed_paths = [];
  capture.authoritative_stages.manifest_backed_undo.files_restored = [];
  capture.authoritative_stages.clean_baseline_after_undo.file_probes = [];
  capture.authoritative_stages.prompt1_clean_rerun.changed_paths = ["[]"];
  const truth = buildAuthoritativeFinalTruth({ capture, steps: [{ name: "health", ok: true }] });
  assert.equal(truth.truth_status, "NO_GO");
  assert.deepEqual(truth.failed_requirements, [
    "prompt1_initial_run:INCOMPLETE_EVIDENCE",
    "manifest_backed_undo:INCOMPLETE_EVIDENCE",
    "clean_baseline_after_undo:INCOMPLETE_EVIDENCE",
    "prompt1_clean_rerun:INCOMPLETE_EVIDENCE",
  ]);
});

test("matching Undo request and response paths cannot substitute for the initial run manifest", () => {
  const capture = goCapture();
  const undo = capture.authoritative_stages.manifest_backed_undo;
  undo.initial_final_receipt_path = ".source-proxy/backups/unrelated/manifest.json";
  undo.expected_backup_manifest = ".source-proxy/backups/unrelated/manifest.json";
  undo.selected_backup_manifest = ".source-proxy/backups/unrelated/manifest.json";
  undo.persisted_selected_backup_manifest = ".source-proxy/backups/unrelated/manifest.json";
  const truth = buildAuthoritativeFinalTruth({ capture, steps: [{ name: "health", ok: true }] });
  assert.equal(truth.truth_status, "NO_GO");
  assert.deepEqual(truth.failed_requirements, ["manifest_backed_undo:INCOMPLETE_EVIDENCE"]);
});

test("GO labels cannot override failed grader or trust diagnostics", () => {
  const capture = goCapture();
  capture.authoritative_stages.prompt1_initial_run.grader_label = "FAILED";
  capture.authoritative_stages.prompt1_clean_rerun.trial_result_trust_status = "blocked_before_apply";
  const truth = buildAuthoritativeFinalTruth({ capture, steps: [{ name: "health", ok: true }] });
  assert.equal(truth.truth_status, "NO_GO");
  assert.deepEqual(truth.failed_requirements, [
    "prompt1_initial_run:INCOMPLETE_EVIDENCE",
    "prompt1_clean_rerun:INCOMPLETE_EVIDENCE",
  ]);
});
