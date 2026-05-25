from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage6DashboardSnapshot:
    snapshot_id: str
    queue_visible: bool
    trust_tiers_visible: bool
    approvals_visible: bool
    ledger_visible: bool
    stop_state_visible: bool
    blocked_reasons_visible: bool
    evidence_visible: bool
    final_readiness_visible: bool
    dashboard_can_grant_authority: bool
    queue_runs_observed: int
    queue_runs_executed: int


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage6Result:
    stage: str
    status: str
    valid_for_dry_run: bool
    would_execute_queue: bool
    would_mutate_dashboard: bool
    dashboard_authority_granted: bool
    full_auto_granted: bool
    limited_unattended_operation_granted: bool
    blocked_reasons: tuple[str, ...]
    next_increment: str


def validate_final_proof_stage_6_dashboard_dry_run(
    snapshot: CartographerFinalProofStage6DashboardSnapshot,
) -> CartographerFinalProofStage6Result:
    reasons: list[str] = []

    if not snapshot.snapshot_id:
        reasons += ["missing_snapshot_id"]
    required_visibility = {
        "queue_visible": snapshot.queue_visible,
        "trust_tiers_visible": snapshot.trust_tiers_visible,
        "approvals_visible": snapshot.approvals_visible,
        "ledger_visible": snapshot.ledger_visible,
        "stop_state_visible": snapshot.stop_state_visible,
        "blocked_reasons_visible": snapshot.blocked_reasons_visible,
        "evidence_visible": snapshot.evidence_visible,
        "final_readiness_visible": snapshot.final_readiness_visible,
    }
    for name, visible in required_visibility.items():
        if not visible:
            reasons += [f"dashboard_missing_{name}"]
    if snapshot.dashboard_can_grant_authority:
        reasons += ["dashboard_authority_forbidden"]
    if snapshot.queue_runs_observed < 1:
        reasons += ["missing_repeated_queue_run_observation"]
    if snapshot.queue_runs_executed > 0:
        reasons += ["queue_execution_forbidden_in_dry_run"]

    return CartographerFinalProofStage6Result(
        stage="Final Proof Stage 6",
        status="repeated-queue-runs-dashboard-proof-dry-run-only",
        valid_for_dry_run=not reasons,
        would_execute_queue=False,
        would_mutate_dashboard=False,
        dashboard_authority_granted=False,
        full_auto_granted=False,
        limited_unattended_operation_granted=False,
        blocked_reasons=tuple(dict.fromkeys(reasons)),
        next_increment="Final Proof Stage 7: Autonomy Readiness Score And Decision Gate Dry Run",
    )
