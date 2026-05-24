from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage4Drill:
    drill_id: str
    approval_present: bool
    approval_expired: bool
    approval_revoked: bool
    self_approved: bool
    kill_switch_scopes_active: tuple[str, ...]
    requested_scope: str
    attempted_auto_clear: bool
    attempted_resume: bool
    attempted_retry: bool


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage4Result:
    stage: str
    status: str
    valid_for_dry_run: bool
    would_clear_kill_switch: bool
    would_resume: bool
    would_retry: bool
    would_execute: bool
    full_auto_granted: bool
    limited_unattended_operation_granted: bool
    blocked_reasons: tuple[str, ...]
    next_increment: str


def validate_final_proof_stage_4_approval_kill_switch_dry_run(
    drill: CartographerFinalProofStage4Drill,
) -> CartographerFinalProofStage4Result:
    reasons: list[str] = []

    if not drill.drill_id:
        reasons += ["missing_drill_id"]
    if not drill.approval_present:
        reasons += ["missing_approval"]
    if drill.approval_expired:
        reasons += ["approval_expired"]
    if drill.approval_revoked:
        reasons += ["approval_revoked"]
    if drill.self_approved:
        reasons += ["self_approval_forbidden"]
    if "global" in drill.kill_switch_scopes_active:
        reasons += ["global_kill_switch_active"]
    if drill.requested_scope in drill.kill_switch_scopes_active:
        reasons += ["requested_scope_kill_switch_active"]
    if drill.attempted_auto_clear:
        reasons += ["auto_clear_kill_switch_forbidden"]
    if drill.attempted_resume and reasons:
        reasons += ["resume_blocked_by_stop_state"]
    if drill.attempted_retry and reasons:
        reasons += ["retry_blocked_by_stop_state"]

    return CartographerFinalProofStage4Result(
        stage="Final Proof Stage 4",
        status="approval-expiration-kill-switch-drill-dry-run-only",
        valid_for_dry_run=not reasons,
        would_clear_kill_switch=False,
        would_resume=False,
        would_retry=False,
        would_execute=False,
        full_auto_granted=False,
        limited_unattended_operation_granted=False,
        blocked_reasons=tuple(dict.fromkeys(reasons)),
        next_increment="Final Proof Stage 5: Rollback Drills Dry Run",
    )
