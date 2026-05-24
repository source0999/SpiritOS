from __future__ import annotations

import dataclasses


SAFE_TASK_CLASSES: tuple[str, ...] = (
    "manual_check_reminder",
    "docs_freshness_review",
    "roadmap_drift_review",
    "dirty_worktree_summary",
    "open_gate_summary",
    "blueprint_refresh_proposal",
    "safe_docs_evidence_maintenance_proposal",
    "autonomous_escalation_proposal",
)

PROTECTED_PATH_PREFIXES: tuple[str, ...] = (
    "src/",
    "source_proxy/api/",
    "source_proxy/verification/",
    "source_proxy/codex/",
    "source_proxy/testing/runner.py",
)


@dataclasses.dataclass(frozen=True)
class CartographerLevel14SafeTaskQueueItem:
    task_id: str
    task_class: str
    trust_tier: str
    lane: str
    approval_token_id: str | None
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    max_attempts: int
    rollback_reference: str | None
    verification_reference: str | None
    kill_switch_scope: str
    expires_at: str
    status: str


@dataclasses.dataclass(frozen=True)
class CartographerLevel14KillSwitchState:
    scope: str
    active: bool
    reason: str | None


@dataclasses.dataclass(frozen=True)
class CartographerLevel14Check:
    level: str
    valid_for_dry_run: bool
    queue_execution_authority_granted: bool
    automatic_task_selection_granted: bool
    recurring_scheduler_authority_granted: bool
    write_authority_granted: bool
    autonomy_granted: bool
    blocked_reasons: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class CartographerLevel14ProposalPacket:
    level: str
    title: str
    status: str
    mode: str
    would_execute_task: bool
    would_schedule_background_job: bool
    would_write_files: bool
    would_send_notification: bool
    queue_execution_authority_granted: bool
    autonomy_granted: bool
    blocked: bool
    blocked_reasons: tuple[str, ...]
    next_increment: str


def validate_level_14_safe_task_queue_dry_run(
    item: CartographerLevel14SafeTaskQueueItem,
) -> CartographerLevel14Check:
    reasons = _queue_item_reasons(item)
    return _check("14.1", reasons)


def validate_level_14_task_class_and_trust_tier_dry_run(
    item: CartographerLevel14SafeTaskQueueItem,
    *,
    allowed_trust_tiers: tuple[str, ...],
) -> CartographerLevel14Check:
    reasons = _queue_item_reasons(item)
    if item.task_class not in SAFE_TASK_CLASSES:
        reasons += ["unknown_or_unsafe_task_class"]
    if item.trust_tier not in allowed_trust_tiers:
        reasons += ["trust_tier_mismatch"]
    if item.task_class in ("cleanup", "commit", "push", "merge"):
        reasons += ["mutating_task_class_forbidden"]
    return _check("14.2", reasons)


def validate_level_14_kill_switch_dry_run(
    item: CartographerLevel14SafeTaskQueueItem,
    kill_switches: tuple[CartographerLevel14KillSwitchState, ...],
) -> CartographerLevel14Check:
    reasons = _queue_item_reasons(item)
    active_stops = tuple(stop for stop in kill_switches if stop.active)
    if any(stop.scope in ("global", item.lane, item.task_id, item.kill_switch_scope) for stop in active_stops):
        reasons += ["active_kill_switch_blocks_task"]
    if any(stop.active and not stop.reason for stop in kill_switches):
        reasons += ["active_kill_switch_missing_reason"]
    return _check("14.3", reasons)


def validate_level_14_stop_controls_dry_run(
    item: CartographerLevel14SafeTaskQueueItem,
    *,
    unexpected_head: bool,
    unexpected_git_status: bool,
    verification_failed: bool,
    hidden_mutation_suspected: bool,
) -> CartographerLevel14Check:
    reasons = _queue_item_reasons(item)
    if unexpected_head:
        reasons += ["unexpected_head_stop"]
    if unexpected_git_status:
        reasons += ["unexpected_git_status_stop"]
    if verification_failed:
        reasons += ["verification_failure_stop"]
    if hidden_mutation_suspected:
        reasons += ["hidden_mutation_stop"]
    return _check("14.4", reasons)


def build_level_14_recurring_health_check_dry_run(
    item: CartographerLevel14SafeTaskQueueItem,
    *,
    operator_invoked: bool,
) -> CartographerLevel14ProposalPacket:
    reasons = _queue_item_reasons(item)
    if item.task_class not in ("manual_check_reminder", "docs_freshness_review", "roadmap_drift_review", "dirty_worktree_summary", "open_gate_summary"):
        reasons += ["unsupported_health_check_class"]
    if not operator_invoked:
        reasons += ["background_scheduling_forbidden"]
    return _packet(
        level="14.5",
        title="Recurring Health Check Runtime Dry Run",
        status="recurring-health-check-dry-run-only",
        blocked_reasons=reasons,
        next_increment="Cartographer Level 14.6: Blueprint Refresh Proposal Runtime Dry Run",
    )


def build_level_14_blueprint_refresh_proposal_dry_run(
    item: CartographerLevel14SafeTaskQueueItem,
    *,
    proposed_blueprint_write: bool,
) -> CartographerLevel14ProposalPacket:
    reasons = _queue_item_reasons(item)
    if item.task_class != "blueprint_refresh_proposal":
        reasons += ["task_class_must_be_blueprint_refresh_proposal"]
    if proposed_blueprint_write:
        reasons += ["blueprint_write_forbidden"]
    return _packet(
        level="14.6",
        title="Blueprint Refresh Proposal Runtime Dry Run",
        status="blueprint-refresh-proposal-dry-run-only",
        blocked_reasons=reasons,
        next_increment="Cartographer Level 14.7: Safe Docs Evidence Maintenance Runtime Dry Run",
    )


def build_level_14_safe_docs_evidence_maintenance_dry_run(
    item: CartographerLevel14SafeTaskQueueItem,
    *,
    attempts_delete: bool,
    has_scoped_level_11_approval: bool,
) -> CartographerLevel14ProposalPacket:
    reasons = _queue_item_reasons(item)
    if item.task_class != "safe_docs_evidence_maintenance_proposal":
        reasons += ["task_class_must_be_maintenance_proposal"]
    if attempts_delete:
        reasons += ["evidence_receipt_or_history_delete_forbidden"]
    if not has_scoped_level_11_approval:
        reasons += ["scoped_level_11_approval_required_before_future_write"]
    return _packet(
        level="14.7",
        title="Safe Docs Evidence Maintenance Runtime Dry Run",
        status="safe-docs-evidence-maintenance-dry-run-only",
        blocked_reasons=reasons,
        next_increment="Cartographer Level 14.8: Autonomous Escalation And Closeout Proposal Runtime Dry Run",
    )


def build_level_14_escalation_closeout_proposal_dry_run(
    item: CartographerLevel14SafeTaskQueueItem,
    *,
    would_notify: bool,
    would_auto_close: bool,
) -> CartographerLevel14ProposalPacket:
    reasons = _queue_item_reasons(item)
    if item.task_class != "autonomous_escalation_proposal":
        reasons += ["task_class_must_be_escalation_proposal"]
    if would_notify:
        reasons += ["notification_send_forbidden"]
    if would_auto_close:
        reasons += ["automatic_closeout_forbidden"]
    return _packet(
        level="14.8",
        title="Autonomous Escalation And Closeout Proposal Runtime Dry Run",
        status="escalation-closeout-proposal-dry-run-only",
        blocked_reasons=reasons,
        next_increment="Cartographer Level 14.9: Final Review Gate Runtime Dry Run",
    )


def build_level_14_final_review_gate_dry_run() -> dict[str, object]:
    return {
        "level": "14.9",
        "title": "Final Review Gate Runtime Dry Run",
        "status": "safe-limited-autonomy-v1-readiness-dry-run-only",
        "safe_limited_autonomy_v1_ready_for_final_proof": True,
        "full_auto_granted": False,
        "queue_execution_authority_granted": False,
        "recurring_scheduler_authority_granted": False,
        "write_authority_granted": False,
        "local_execution_authority_granted": False,
        "worker_orchestration_authority_granted": False,
        "branch_worktree_authority_granted": False,
        "commit_push_merge_authority_granted": False,
        "cleanup_authority_granted": False,
        "autonomy_granted": False,
        "next_increment": "Final Proof Stage 1: Real Task Gauntlet",
    }


def _queue_item_reasons(item: CartographerLevel14SafeTaskQueueItem) -> list[str]:
    reasons: list[str] = []
    if not item.task_id:
        reasons += ["missing_task_id"]
    if item.task_class not in SAFE_TASK_CLASSES:
        reasons += ["unsupported_task_class"]
    if not item.approval_token_id:
        reasons += ["missing_approval_token"]
    if not item.allowed_files:
        reasons += ["missing_allowed_files"]
    if set(item.allowed_files).intersection(item.forbidden_files):
        reasons += ["allowed_files_intersect_forbidden_files"]
    if any(path.startswith(PROTECTED_PATH_PREFIXES) for path in item.allowed_files):
        reasons += ["protected_path_in_scope"]
    if item.max_attempts < 1:
        reasons += ["invalid_max_attempts"]
    if not item.rollback_reference:
        reasons += ["missing_rollback_reference"]
    if not item.verification_reference:
        reasons += ["missing_verification_reference"]
    if item.status not in ("queued", "blocked", "preview", "dry_run"):
        reasons += ["unsupported_queue_status"]
    return reasons


def _check(level: str, blocked_reasons: list[str]) -> CartographerLevel14Check:
    return CartographerLevel14Check(
        level=level,
        valid_for_dry_run=not blocked_reasons,
        queue_execution_authority_granted=False,
        automatic_task_selection_granted=False,
        recurring_scheduler_authority_granted=False,
        write_authority_granted=False,
        autonomy_granted=False,
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
    )


def _packet(
    *,
    level: str,
    title: str,
    status: str,
    blocked_reasons: list[str],
    next_increment: str,
) -> CartographerLevel14ProposalPacket:
    return CartographerLevel14ProposalPacket(
        level=level,
        title=title,
        status=status,
        mode="dry_run",
        would_execute_task=False,
        would_schedule_background_job=False,
        would_write_files=False,
        would_send_notification=False,
        queue_execution_authority_granted=False,
        autonomy_granted=False,
        blocked=bool(blocked_reasons),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        next_increment=next_increment,
    )
