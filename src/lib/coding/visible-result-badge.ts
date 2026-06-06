export type VisibleResultPrimaryLabel =
  | "LIVE PASS"
  | "REVERTED PASS"
  | "PASS"
  | "PASS WITH WARNING"
  | "PREVIEW ONLY"
  | "WARNING"
  | "FAIL"
  | "BLOCKED"
  | "ALREADY SATISFIED"
  | "NOT PROVEN";

export type VisibleResultTone = "success" | "warning" | "danger" | "neutral";

export type VisibleResultSecondaryBadge = {
  label: string;
  tone: VisibleResultTone;
};

export type VisibleResultBadge = {
  primary_label: VisibleResultPrimaryLabel;
  primary_tone: VisibleResultTone;
  secondary_badges: VisibleResultSecondaryBadge[];
  plain_summary: string;
  should_count_as_productive: boolean;
  should_count_as_live_model_proof: boolean;
  user_next_action: string;
  live_model_proof_status: "live_model_proven" | "not_live_model_proof" | "not_required" | "unknown";
  live_apply_proof_status: "proven" | "not_proven" | "failed" | "blocked_protected_path" | "reverted";
  score_counts_as_live_usefulness: boolean;
};

export type VisibleResultBadgeInput = {
  trial_mode?: "preview_only" | "live_apply" | string | null;
  live_apply_status?: string | null;
  live_apply_proof_status?: string | null;
  status?: string | null;
  visible_failure?: string | null;
  result_category?: string | null;
  actual_intelligence_category?: string | null;
  expected_behavior?: string | null;
  actual_behavior?: string | null;
  simple_result?: string | null;
  reason_code?: string | null;
  confidence?: string | null;
  provider_call_made?: boolean | null;
  provider_call_authorized?: boolean | null;
  model_called_for_generation?: string | null;
  hermes_used_for_this_run?: string | boolean | null;
  counts_for_live_usefulness?: boolean | null;
  counts_for_coding_usefulness?: boolean | null;
  s_plus_eligible?: boolean | null;
  disqualifies_live_claim?: boolean | null;
  safety_state?: string | null;
  preview_changed_files?: string[];
  disk_changed_files?: string[];
  applied_changed_files?: string[];
  changed_files?: string[];
  allowed_files?: string[];
  protected_paths_touched?: string[];
  checks_run?: string[];
  checks_attempted?: boolean | null;
  checks_passed?: boolean | null;
  reversal_available?: boolean | null;
  reverted_at?: string | null;
  next_action?: string | null;
  next_recommended_action?: string | null;
};

function normalized(value: unknown) {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}

function hasAnyFile(input: VisibleResultBadgeInput) {
  return [
    input.preview_changed_files,
    input.disk_changed_files,
    input.applied_changed_files,
    input.changed_files,
  ].some((items) => Array.isArray(items) && items.length > 0);
}

export function mapVisibleResultBadge(input: VisibleResultBadgeInput): VisibleResultBadge {
  const trialMode = normalized(input.trial_mode);
  const status = normalized(input.status);
  const visibleFailure = normalized(input.visible_failure);
  const resultCategory = normalized(input.result_category);
  const actualIntelligenceCategory = normalized(input.actual_intelligence_category);
  const expectedBehavior = normalized(input.expected_behavior);
  const actualBehavior = normalized(input.actual_behavior);
  const simpleResult = normalized(input.simple_result);
  const reasonCode = normalized(input.reason_code);
  const safetyState = normalized(input.safety_state);
  const secondary_badges: VisibleResultSecondaryBadge[] = [];
  const noVisibleFailure =
    !visibleFailure || visibleFailure === "none" || visibleFailure === "none visible";

  const modelCalled = input.model_called_for_generation?.trim() || "";
  const hermesStatus =
    typeof input.hermes_used_for_this_run === "boolean"
      ? input.hermes_used_for_this_run
        ? "yes"
        : "no"
      : normalized(input.hermes_used_for_this_run);
  const noLiveModelCall =
    input.provider_call_made === false ||
    modelCalled === "" ||
    modelCalled.toLowerCase() === "none" ||
    hermesStatus === "not_called";
  const hasLiveModelCall =
    input.provider_call_made === true &&
    Boolean(modelCalled) &&
    modelCalled.toLowerCase() !== "none" &&
    hermesStatus !== "not_called";
  const previewChangedFiles = Array.isArray(input.preview_changed_files) ? input.preview_changed_files : [];
  const appliedChangedFiles = Array.isArray(input.applied_changed_files) ? input.applied_changed_files : [];
  const diskChangedFiles = Array.isArray(input.disk_changed_files) ? input.disk_changed_files : [];
  const changedFiles = Array.isArray(input.changed_files) ? input.changed_files : [];
  const allowedFiles = Array.isArray(input.allowed_files) ? input.allowed_files : [];
  const protectedPathsTouched = Array.isArray(input.protected_paths_touched) ? input.protected_paths_touched : [];
  const checksRun = Array.isArray(input.checks_run) ? input.checks_run : [];
  const checksAttempted = input.checks_attempted === true || checksRun.length > 0 || input.checks_passed !== null && input.checks_passed !== undefined;
  const changedFilesInsideAllowed =
    allowedFiles.length === 0
      ? true
      : [...new Set([...previewChangedFiles, ...appliedChangedFiles, ...diskChangedFiles, ...changedFiles])]
          .every((filePath) => allowedFiles.includes(filePath));
  const liveApplyCriteriaMet =
    trialMode === "live_apply" &&
    hasLiveModelCall &&
    previewChangedFiles.length > 0 &&
    appliedChangedFiles.length > 0 &&
    diskChangedFiles.length > 0 &&
    changedFilesInsideAllowed &&
    protectedPathsTouched.length === 0 &&
    checksAttempted &&
    input.reversal_available === true &&
    input.disqualifies_live_claim !== true;
  const should_count_as_live_model_proof =
    (trialMode === "live_apply" ? liveApplyCriteriaMet : hasLiveModelCall) &&
    input.disqualifies_live_claim !== true;
  const live_model_proof_status = should_count_as_live_model_proof
    ? "live_model_proven"
    : noLiveModelCall || input.disqualifies_live_claim === true
      ? "not_live_model_proof"
      : "unknown";
  const explicitLiveApplyProof = normalized(input.live_apply_proof_status);
  const live_apply_proof_status =
    protectedPathsTouched.length > 0 || reasonCode.includes("protected")
      ? "blocked_protected_path"
      : input.reverted_at
        ? "reverted"
        : explicitLiveApplyProof === "failed"
          ? "failed"
          : liveApplyCriteriaMet
            ? "proven"
            : trialMode === "live_apply"
              ? "not_proven"
              : "not_proven";

  const blockedForSafety =
    resultCategory === "blocked_for_safety" ||
    actualIntelligenceCategory === "blocked_safety" ||
    actualBehavior === "safe_block" ||
    simpleResult === "blocked safely" ||
    reasonCode.includes("protected") ||
    reasonCode.includes("forbidden") ||
    safetyState.includes("blocked_for_safety") ||
    safetyState.includes("safety blocked");
  const blockedMissingScope =
    resultCategory === "blocked_missing_scope" ||
    actualIntelligenceCategory === "blocked_missing_scope" ||
    reasonCode.includes("clarification") ||
    reasonCode.includes("target_unresolved") ||
    reasonCode.includes("target_missing") ||
    expectedBehavior === "clarification_needed" ||
    actualBehavior === "clarification_needed";
  const alreadySatisfied =
    resultCategory === "already_satisfied" ||
    actualIntelligenceCategory === "already_satisfied_noop_useful" ||
    actualBehavior === "already_satisfied_noop" ||
    simpleResult === "already satisfied" ||
    status.includes("already_satisfied") ||
    status.includes("already satisfied");
  const failed =
    resultCategory.startsWith("failed") ||
    actualIntelligenceCategory.startsWith("failed") ||
    actualBehavior === "failed" ||
    simpleResult === "failed" ||
    status === "error" ||
    status.includes("failed") ||
    reasonCode.includes("failed");
  const usefulWithWarning =
    resultCategory === "pass_productive_with_warning" ||
    actualIntelligenceCategory === "pass_productive_with_warning";
  const useful =
    usefulWithWarning ||
    resultCategory === "productive_preview" ||
    resultCategory === "pass_productive" ||
    actualIntelligenceCategory === "pass_productive" ||
    actualBehavior === "productive_preview" ||
    simpleResult === "preview diff produced" ||
    status.includes("ready") ||
    status.includes("preview") ||
    hasAnyFile(input) ||
    (noVisibleFailure && Boolean(input.visible_failure));

  let primary_label: VisibleResultPrimaryLabel;
  let primary_tone: VisibleResultTone;
  let plain_summary: string;
  let should_count_as_productive = false;

  const previewOnlyProof =
    trialMode === "preview_only" ||
    input.provider_call_made === false ||
    modelCalled.toLowerCase() === "none" ||
    (
      (previewChangedFiles.length > 0 || status.includes("preview")) &&
      appliedChangedFiles.length === 0 &&
      diskChangedFiles.length === 0
    );

  if (blockedForSafety) {
    primary_label = "BLOCKED";
    primary_tone = "warning";
    plain_summary = reasonCode.includes("protected") ? "Protected path blocked." : "Safety gate blocked the request.";
    secondary_badges.push({ label: "PASS: Safety gate worked", tone: "success" });
  } else if (trialMode === "live_apply" && live_apply_proof_status === "reverted") {
    primary_label = "REVERTED PASS";
    primary_tone = "success";
    plain_summary = "Applied, verified, and reverted.";
    should_count_as_productive = true;
  } else if (trialMode === "live_apply" && live_apply_proof_status === "proven") {
    primary_label = "LIVE PASS";
    primary_tone = "success";
    plain_summary = input.reversal_available === true ? "Applied, verified, revert ready." : "Applied and verified.";
    should_count_as_productive = true;
  } else if (alreadySatisfied) {
    primary_label = "ALREADY SATISFIED";
    primary_tone = "success";
    plain_summary = "No change was needed.";
    should_count_as_productive = false;
  } else if (trialMode === "live_apply" && !liveApplyCriteriaMet && (noLiveModelCall || appliedChangedFiles.length === 0 || diskChangedFiles.length === 0)) {
    primary_label = "FAIL";
    primary_tone = "danger";
    plain_summary = noLiveModelCall
      ? "No live model call was recorded."
      : appliedChangedFiles.length === 0
        ? "No approved diff was applied."
        : "No disk change was verified.";
  } else if (failed) {
    primary_label = "FAIL";
    primary_tone = "danger";
    plain_summary = simpleResult === "failed" ? "Preview generation failed." : "The run failed before a useful result.";
  } else if (blockedMissingScope) {
    primary_label = "WARNING";
    primary_tone = "warning";
    plain_summary = "Needs a target or file before preview.";
  } else if (previewOnlyProof && useful) {
    primary_label = "PREVIEW ONLY";
    primary_tone = "neutral";
    plain_summary = "Preview-only diagnostic run. Not live proof.";
    should_count_as_productive = false;
  } else if (usefulWithWarning) {
    primary_label = "PASS WITH WARNING";
    primary_tone = "warning";
    plain_summary = "Preview diff produced.";
    should_count_as_productive = true;
  } else if (useful) {
    primary_label = "PASS";
    primary_tone = "success";
    plain_summary =
      actualBehavior === "productive_preview" || simpleResult === "preview diff produced" || hasAnyFile(input)
        ? "Preview diff produced."
        : expectedBehavior.includes("design") || status.includes("design")
          ? "Design critique produced."
          : "Useful result produced.";
    should_count_as_productive = true;
  } else {
    primary_label = "NOT PROVEN";
    primary_tone = "neutral";
    plain_summary = "No proven product result was recorded.";
  }

  if (noLiveModelCall) {
    secondary_badges.push({
      label: input.provider_call_made === false ? "WARNING: No live model call" : "LIVE MODEL CALL RECORDED",
      tone: "warning",
    });
  } else if (input.disqualifies_live_claim === true) {
    secondary_badges.push({ label: "NOT LIVE MODEL PROOF", tone: "warning" });
  }
  if (trialMode === "preview_only") {
    secondary_badges.push({ label: "0/100 live apply proof", tone: "neutral" });
  } else if (trialMode === "live_apply" && live_apply_proof_status === "not_proven") {
    secondary_badges.push({ label: "NOT LIVE APPLY PROOF", tone: "warning" });
  }

  return {
    primary_label,
    primary_tone,
    secondary_badges,
    plain_summary,
    should_count_as_productive,
    should_count_as_live_model_proof,
    user_next_action:
      input.next_recommended_action?.trim() ||
      input.next_action?.trim() ||
      (failed ? "Copy diagnostics." : blockedForSafety ? "No files changed." : "Continue with the next safe step."),
    live_model_proof_status,
    live_apply_proof_status,
    score_counts_as_live_usefulness: liveApplyCriteriaMet || live_apply_proof_status === "reverted",
  };
}
