const allowedSandboxPath = "src/app/coding/design-demo/page.tsx";

export type DesignStudioRepairRequest = {
  anti_template_verdict?: string;
  critic_verdict?: string;
  critic_verdict_id: string;
  max_repair_attempts: number;
  proposed_changed_paths: string[];
  repair_attempt_index: number;
  trace_id: string;
};

export function runDesignStudioBoundedRepair(request: DesignStudioRepairRequest) {
  const repairAttemptId = `repair-${request.critic_verdict_id}-${request.repair_attempt_index}`;
  const forbiddenPaths = request.proposed_changed_paths.filter((path) => path !== allowedSandboxPath);
  const maxAttemptsValid =
    Number.isInteger(request.max_repair_attempts) &&
    request.max_repair_attempts > 0 &&
    request.max_repair_attempts <= 3;
  const attemptWithinBounds =
    Number.isInteger(request.repair_attempt_index) &&
    request.repair_attempt_index > 0 &&
    request.repair_attempt_index <= request.max_repair_attempts;
  const repairNeeded =
    request.critic_verdict === "DESIGN_CRITIC_REPAIR_REQUIRED" ||
    request.anti_template_verdict === "GENERIC_TEMPLATE_REJECT" ||
    request.anti_template_verdict === "GENERIC_TEMPLATE_REPAIR_REQUIRED";

  return {
    allowed_changed_paths: [allowedSandboxPath],
    apply_ready: repairNeeded && maxAttemptsValid && attemptWithinBounds && forbiddenPaths.length === 0,
    blockers: [
      maxAttemptsValid ? null : "invalid_or_unbounded_max_repair_attempts",
      attemptWithinBounds ? null : "repair_attempt_out_of_bounds",
      forbiddenPaths.length === 0 ? null : "forbidden_repair_path_requested",
      repairNeeded ? null : "repair_not_required_by_critic_or_anti_template_verdict",
    ].filter(Boolean),
    forbidden_paths: forbiddenPaths,
    max_repair_attempts: request.max_repair_attempts,
    repair_attempt_id: repairAttemptId,
    repair_attempt_ids: [repairAttemptId],
    repair_output_retest_required: true,
    sandbox_diff_required: true,
    trace_id: request.trace_id,
  };
}
