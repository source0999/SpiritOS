from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage7Inputs:
    gauntlet_passed: bool
    soak_passed: bool
    hidden_mutation_drills_passed: bool
    approval_kill_switch_drills_passed: bool
    rollback_drills_passed: bool
    dashboard_proof_passed: bool
    residual_risks: tuple[str, ...]
    operator_decision: str
    requested_full_auto: bool
    requested_limited_unattended_operation: bool


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage7Decision:
    stage: str
    status: str
    readiness_score: int
    ready_for_operator_review: bool
    limited_unattended_operation_allowed: bool
    full_auto_granted: bool
    autonomy_granted: bool
    blocked_reasons: tuple[str, ...]
    next_increment: str


def build_final_proof_stage_7_readiness_decision_dry_run(
    inputs: CartographerFinalProofStage7Inputs,
) -> CartographerFinalProofStage7Decision:
    reasons: list[str] = []
    passed_checks = (
        inputs.gauntlet_passed,
        inputs.soak_passed,
        inputs.hidden_mutation_drills_passed,
        inputs.approval_kill_switch_drills_passed,
        inputs.rollback_drills_passed,
        inputs.dashboard_proof_passed,
    )
    score = int(sum(1 for passed in passed_checks if passed) / len(passed_checks) * 100)

    if not inputs.gauntlet_passed:
        reasons += ["gauntlet_not_passed"]
    if not inputs.soak_passed:
        reasons += ["soak_not_passed"]
    if not inputs.hidden_mutation_drills_passed:
        reasons += ["hidden_mutation_drills_not_passed"]
    if not inputs.approval_kill_switch_drills_passed:
        reasons += ["approval_kill_switch_drills_not_passed"]
    if not inputs.rollback_drills_passed:
        reasons += ["rollback_drills_not_passed"]
    if not inputs.dashboard_proof_passed:
        reasons += ["dashboard_proof_not_passed"]
    if inputs.residual_risks:
        reasons += ["residual_risks_require_operator_review"]
    if inputs.operator_decision != "review_only":
        reasons += ["operator_decision_must_remain_review_only"]
    if inputs.requested_full_auto:
        reasons += ["full_auto_request_forbidden"]
    if inputs.requested_limited_unattended_operation:
        reasons += ["limited_unattended_operation_not_granted_by_dry_run"]

    return CartographerFinalProofStage7Decision(
        stage="Final Proof Stage 7",
        status="autonomy-readiness-score-decision-gate-dry-run-only",
        readiness_score=score,
        ready_for_operator_review=score == 100,
        limited_unattended_operation_allowed=False,
        full_auto_granted=False,
        autonomy_granted=False,
        blocked_reasons=tuple(dict.fromkeys(reasons)),
        next_increment="Operator Decision: Explicit Future Roadmap Required",
    )
