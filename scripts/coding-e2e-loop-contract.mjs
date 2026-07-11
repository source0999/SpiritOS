export const E2E_LOOP_SCHEMA_VERSION = "coding-e2e-loop/v4";

export const REQUIRED_AUTHORITATIVE_STAGES = Object.freeze([
  "context",
  "post_apply_verification",
  "browser_verification",
  "anti_cheat",
  "final_receipt",
  "diagnostic_consistency",
  "prompt1_initial_run",
  "manifest_backed_undo",
  "clean_baseline_after_undo",
  "product_reset_after_undo",
  "prompt1_clean_rerun",
]);

const PROMPT_RUN_STAGE_NAMES = Object.freeze([
  "context",
  "post_apply_verification",
  "browser_verification",
  "anti_cheat",
  "final_receipt",
  "diagnostic_consistency",
]);

const PROMPT1_EXPECTED_FIXTURE_PATHS = Object.freeze([
  "tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
  "tests/ui-agent-trials/fixtures/dummy-product-site/package.json",
  "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
  "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
  "tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
  "tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
].sort());

export function normalizeRepoRoot(value) {
  if (typeof value !== "string") return "";
  const normalized = value.trim().replace(/\\/gu, "/").replace(/\/+$/u, "");
  return process.platform === "win32" ? normalized.toLowerCase() : normalized;
}

export function repoRootsMatch(expected, reported) {
  const expectedRoot = normalizeRepoRoot(expected);
  const reportedRoot = normalizeRepoRoot(reported);
  return Boolean(expectedRoot && reportedRoot && expectedRoot === reportedRoot);
}

export function buildAuthoritativeFinalTruth({ capture, steps }) {
  const captureSchemaVersion =
    capture && typeof capture === "object" && typeof capture.schema_version === "string"
      ? capture.schema_version
      : "MISSING";
  const captureSchemaOk = captureSchemaVersion === E2E_LOOP_SCHEMA_VERSION;
  const authoritativeStages =
    capture && typeof capture === "object" && capture.authoritative_stages &&
    typeof capture.authoritative_stages === "object"
      ? capture.authoritative_stages
      : {};
  const requiredStages = Object.fromEntries(
    REQUIRED_AUTHORITATIVE_STAGES.map((name) => {
      const stage = authoritativeStages[name];
      const status = stage && typeof stage === "object" ? stage.status : null;
      const evidenceComplete = lifecycleStageEvidenceComplete(name, stage, authoritativeStages);
      return [name, {
        evidence_complete: evidenceComplete,
        ok: status === "GO" && evidenceComplete,
        status: typeof status === "string" && status ? status : "MISSING",
      }];
    }),
  );
  const finalReceipt = authoritativeStages.final_receipt;
  const finalReceiptCommitSafe = Boolean(
    finalReceipt &&
    typeof finalReceipt === "object" &&
    finalReceipt.commit_safe === true &&
    finalReceipt.status === "GO",
  );
  const infrastructureOk = Array.isArray(steps) && steps.length > 0 && steps.every((item) => item?.ok === true);
  const failedRequirements = [
    ...(infrastructureOk ? [] : ["infrastructure_or_harness_step_failed"]),
    ...(captureSchemaOk ? [] : [`schema_version:${captureSchemaVersion}`]),
    ...Object.entries(requiredStages)
      .filter(([, stage]) => !stage.ok)
      .map(([name, stage]) =>
        `${name}:${stage.status === "GO" && !stage.evidence_complete ? "INCOMPLETE_EVIDENCE" : stage.status}`,
      ),
    ...(requiredStages.final_receipt.ok && !finalReceiptCommitSafe ? ["final_receipt:COMMIT_UNSAFE"] : []),
  ];
  const truthStatus = failedRequirements.length === 0 && finalReceiptCommitSafe ? "GO" : "NO_GO";
  const commitSafe = truthStatus === "GO";

  return {
    schema_version: E2E_LOOP_SCHEMA_VERSION,
    capture_schema_version: captureSchemaVersion,
    truth_status: truthStatus,
    commit_safe: commitSafe,
    required_stages: requiredStages,
    failed_requirements: failedRequirements,
    recommended_action:
      truthStatus === "GO"
        ? "No harness action remains; preserve the evidence packet for review."
        : failedRequirements.length > 0
          ? `Resolve and rerun: ${failedRequirements.join(", ")}`
          : "Resolve the final receipt commit-safe gate and rerun.",
  };
}

function lifecycleStageEvidenceComplete(name, stage, authoritativeStages) {
  if (!stage || typeof stage !== "object") return false;
  if (PROMPT_RUN_STAGE_NAMES.includes(name)) return true;

  if (name === "prompt1_initial_run" || name === "prompt1_clean_rerun") {
    const taskId = nonEmptyString(stage.task_id);
    const runStartedAt = finiteNumber(stage.run_started_at_ms);
    const runCompletedAt = finiteNumber(stage.run_completed_at_ms);
    const canonicalStages = stage.canonical_stages;
    const canonicalStagesGo =
      canonicalStages &&
      typeof canonicalStages === "object" &&
      PROMPT_RUN_STAGE_NAMES.every((stageName) => canonicalStages[stageName] === "GO");
    const commonComplete = Boolean(
      taskId &&
      /^task_/u.test(taskId) &&
      ["applied", "complete"].includes(stage.terminal_status) &&
      stage.apply_status === "performed" &&
      stage.post_apply_verification_status === "GO" &&
      stage.browser_verification_status === "GO" &&
      stage.final_receipt_status === "GO" &&
      stage.commit_safe === true &&
      stage.grader_label === "PASS" &&
      stage.trial_result_trust_status === "model_authored_diff_proven" &&
      stage.changed_files_present === true &&
      stage.expected_prompt1_changed_files === true &&
      exactStringArray(stage.changed_paths, PROMPT1_EXPECTED_FIXTURE_PATHS) &&
      stage.fixture_was_clean_before_run === true &&
      stage.already_satisfied === false &&
      runStartedAt != null &&
      runCompletedAt != null &&
      runCompletedAt >= runStartedAt &&
      canonicalStagesGo
    );
    if (!commonComplete) return false;
    if (name === "prompt1_initial_run") return stage.lifecycle_sequence === 1;

    const initialTaskId = nonEmptyString(authoritativeStages.prompt1_initial_run?.task_id);
    const cleanCompletedAt = finiteNumber(authoritativeStages.clean_baseline_after_undo?.probe_completed_at_ms);
    const unrelatedPreservation = stage.unrelated_workspace_preservation;
    return Boolean(
      initialTaskId &&
      taskId !== initialTaskId &&
      cleanCompletedAt != null &&
      runStartedAt >= cleanCompletedAt &&
      stage.lifecycle_sequence === 5 &&
      stage.distinct_from_initial_task === true &&
      stage.started_after_clean_baseline === true &&
      stage.started_after_product_reset === true &&
      unrelatedWorktreeProofComplete(unrelatedPreservation)
    );
  }

  if (name === "manifest_backed_undo") {
    const initialTaskId = nonEmptyString(authoritativeStages.prompt1_initial_run?.task_id);
    const originalTaskId = nonEmptyString(stage.original_task_id);
    const selectedManifest = nonEmptyString(stage.selected_backup_manifest);
    const initialReceiptPath = nonEmptyString(authoritativeStages.prompt1_initial_run?.final_receipt_path);
    const initialCompletedAt = finiteNumber(authoritativeStages.prompt1_initial_run?.run_completed_at_ms);
    const undoObservedAt = finiteNumber(stage.response_observed_at_ms);
    const restoredFilesVerified = verifiedAbsentRestoredFiles(stage.files_restored);
    const persistedFilesVerified = verifiedAbsentRestoredFiles(stage.persisted_files_restored);
    const unrelatedWorktree = stage.independent_unrelated_worktree;
    return Boolean(
      initialTaskId &&
      originalTaskId === initialTaskId &&
      initialReceiptPath &&
      initialReceiptPath === nonEmptyString(stage.initial_final_receipt_path) &&
      initialReceiptPath === selectedManifest &&
      initialReceiptPath === nonEmptyString(stage.persisted_selected_backup_manifest) &&
      stage.ui_triggered === true &&
      stage.request_confirm_undo === true &&
      stage.requested_by === "coding-ui" &&
      selectedManifest &&
      selectedManifest === nonEmptyString(stage.expected_backup_manifest) &&
      nonEmptyString(stage.undo_receipt_id) &&
      nonEmptyString(stage.undo_receipt_path) &&
      stage.filesystem_verified === true &&
      stage.untouched_scope_assertion === true &&
      stage.expected_browser_state === "fixture_missing" &&
      Array.isArray(stage.unrelated_paths_touched) &&
      stage.unrelated_paths_touched.length === 0 &&
      unrelatedWorktreeProofComplete(unrelatedWorktree) &&
      stage.all_expected_files_restored === true &&
      stage.all_restored_to_absent === true &&
      exactStringArray(stage.restored_paths, PROMPT1_EXPECTED_FIXTURE_PATHS) &&
      restoredFilesVerified &&
      stage.persisted_receipt_verified === true &&
      stage.persisted_files_restored_verified === true &&
      exactStringArray(stage.persisted_restored_paths, PROMPT1_EXPECTED_FIXTURE_PATHS) &&
      persistedFilesVerified &&
      stage.open_diff_marked_undone === true &&
      stage.ui_pre_reset_preview_http_status === 404 &&
      stage.ui_pre_reset_preview_missing === true &&
      stage.ui_pre_reset_baseline_http_status === 200 &&
      stage.ui_pre_reset_baseline_checked === true &&
      stage.ui_pre_reset_baseline_clean_for_fresh_suite === true &&
      Array.isArray(stage.ui_pre_reset_baseline_dirty_files) &&
      stage.ui_pre_reset_baseline_dirty_files.length === 0 &&
      Array.isArray(stage.ui_pre_reset_dummy_fixture_dirty_files) &&
      stage.ui_pre_reset_dummy_fixture_dirty_files.length === 0 &&
      stage.lifecycle_sequence === 2 &&
      initialCompletedAt != null &&
      undoObservedAt != null &&
      undoObservedAt >= initialCompletedAt &&
      Number.isInteger(stage.response_sequence)
    );
  }

  if (name === "clean_baseline_after_undo") {
    const resetSequence = authoritativeStages.product_reset_after_undo?.response_sequence;
    const resetObservedAt = finiteNumber(authoritativeStages.product_reset_after_undo?.response_observed_at_ms);
    const probeStartedAt = finiteNumber(stage.probe_started_at_ms);
    const probeCompletedAt = finiteNumber(stage.probe_completed_at_ms);
    return Boolean(
      stage.baseline_http_status === 200 &&
      stage.baseline_clean_for_fresh_suite === true &&
      Array.isArray(stage.baseline_dirty_agent_lab_files) &&
      stage.baseline_dirty_agent_lab_files.length === 0 &&
      Array.isArray(stage.dummy_fixture_dirty_files) &&
      stage.dummy_fixture_dirty_files.length === 0 &&
      verifiedMissingFileProbes(stage.file_probes) &&
      stage.all_fixture_files_absent === true &&
      stage.preview_http_status === 404 &&
      stage.lifecycle_sequence === 4 &&
      stage.verified_after_product_reset === true &&
      stage.probe_started_after_product_reset === true &&
      resetObservedAt != null &&
      probeStartedAt != null &&
      probeCompletedAt != null &&
      probeStartedAt >= resetObservedAt &&
      probeCompletedAt >= probeStartedAt &&
      Number.isInteger(resetSequence) &&
      stage.verified_after_reset_response_sequence === resetSequence
    );
  }

  if (name === "product_reset_after_undo") {
    const undoSequence = authoritativeStages.manifest_backed_undo?.response_sequence;
    const undoObservedAt = finiteNumber(authoritativeStages.manifest_backed_undo?.response_observed_at_ms);
    const resetObservedAt = finiteNumber(stage.response_observed_at_ms);
    return Boolean(
      stage.response_status === "reset_verified" &&
      stage.ui_triggered === true &&
      stage.http_status === 200 &&
      stage.reset_verified === true &&
      stage.clean_verified === true &&
      stage.occurred_after_undo === true &&
      stage.lifecycle_sequence === 3 &&
      nonEmptyString(stage.reset_receipt_id) &&
      undoObservedAt != null &&
      resetObservedAt != null &&
      resetObservedAt >= undoObservedAt &&
      Number.isInteger(stage.response_sequence) &&
      Number.isInteger(undoSequence) &&
      stage.response_sequence > undoSequence
    );
  }

  return false;
}

function nonEmptyString(value) {
  return typeof value === "string" && value.trim() ? value.trim() : "";
}

function finiteNumber(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function exactStringArray(value, expected) {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) return false;
  const normalized = [...value].sort();
  return normalized.length === expected.length && normalized.every((item, index) => item === expected[index]);
}

function verifiedAbsentRestoredFiles(value) {
  if (!Array.isArray(value) || value.length !== PROMPT1_EXPECTED_FIXTURE_PATHS.length) return false;
  const paths = value.map((item) => item && typeof item === "object" ? item.path : null);
  return Boolean(
    exactStringArray(paths, PROMPT1_EXPECTED_FIXTURE_PATHS) &&
    value.every((item) =>
      item &&
      typeof item === "object" &&
      item.verified === true &&
      item.absent === true &&
      item.actual_sha256 == null
    )
  );
}

function verifiedMissingFileProbes(value) {
  if (!Array.isArray(value) || value.length !== PROMPT1_EXPECTED_FIXTURE_PATHS.length) return false;
  const paths = value.map((item) => item && typeof item === "object" ? item.path : null);
  return Boolean(
    exactStringArray(paths, PROMPT1_EXPECTED_FIXTURE_PATHS) &&
    value.every((item) =>
      item &&
      typeof item === "object" &&
      item.http_status === 400 &&
      (item.reason_code === "not_file" || item.reason_code === "not_found") &&
      item.missing === true
    )
  );
}

function unrelatedWorktreeProofComplete(value) {
  return Boolean(
    value &&
    typeof value === "object" &&
    value.status === "GO" &&
    value.snapshot_matches === true &&
    value.tracked_diff_matches === true &&
    value.untracked_files_match === true &&
    nonEmptyString(value.before_snapshot_sha256) &&
    nonEmptyString(value.after_snapshot_sha256) &&
    value.before_snapshot_sha256 === value.after_snapshot_sha256 &&
    Array.isArray(value.changed_paths) &&
    value.changed_paths.length === 0
  );
}
