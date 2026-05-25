from __future__ import annotations

import dataclasses


PROTECTED_PATH_PREFIXES: tuple[str, ...] = (
    "src/",
    "source_proxy/api/",
    "source_proxy/verification/",
    "source_proxy/codex/",
    "source_proxy/testing/runner.py",
)


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage5RollbackDrill:
    drill_id: str
    original_action_id: str
    rollback_reference: str | None
    rollback_target_files: tuple[str, ...]
    allowed_files: tuple[str, ...]
    approval_present: bool
    verification_after_rollback: str | None
    rollback_command_would_execute: bool
    rollback_failed: bool
    cleanup_attempted: bool
    operator_reviewed: bool = True


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage5RollbackResult:
    stage: str
    status: str
    valid_for_dry_run: bool
    would_execute_rollback: bool
    would_write_files: bool
    would_cleanup: bool
    would_closeout: bool
    full_auto_granted: bool
    limited_unattended_operation_granted: bool
    blocked_reasons: tuple[str, ...]
    next_increment: str
    operator_review_required: bool = True


def validate_final_proof_stage_5_rollback_dry_run(
    drill: CartographerFinalProofStage5RollbackDrill,
) -> CartographerFinalProofStage5RollbackResult:
    reasons: list[str] = []

    if not drill.drill_id:
        reasons += ["missing_drill_id"]
    if not drill.original_action_id:
        reasons += ["missing_original_action_id"]
    if not drill.rollback_reference:
        reasons += ["missing_rollback_reference"]
    if not drill.rollback_target_files:
        reasons += ["missing_rollback_target_files"]
    if not set(drill.rollback_target_files).issubset(set(drill.allowed_files)):
        reasons += ["rollback_scope_exceeds_allowed_files"]
    if any(path.startswith(PROTECTED_PATH_PREFIXES) for path in drill.rollback_target_files):
        reasons += ["protected_path_in_rollback_scope"]
    if not drill.approval_present:
        reasons += ["missing_rollback_approval"]
    if not drill.verification_after_rollback:
        reasons += ["missing_post_rollback_verification"]
    if drill.rollback_command_would_execute:
        reasons += ["rollback_execution_forbidden_in_dry_run"]
    if drill.rollback_failed:
        reasons += ["rollback_failure_blocks_closeout"]
    if drill.cleanup_attempted:
        reasons += ["cleanup_forbidden"]
    if drill.operator_reviewed is not True:
        reasons += ["operator_review_missing"]

    return CartographerFinalProofStage5RollbackResult(
        stage="Final Proof Stage 5",
        status="rollback-drill-dry-run-only",
        valid_for_dry_run=not reasons,
        would_execute_rollback=False,
        would_write_files=False,
        would_cleanup=False,
        would_closeout=False,
        full_auto_granted=False,
        limited_unattended_operation_granted=False,
        blocked_reasons=tuple(dict.fromkeys(reasons)),
        next_increment="Final Proof Stage 6: Repeated Queue Runs And Dashboard Proof Dry Run",
    )
