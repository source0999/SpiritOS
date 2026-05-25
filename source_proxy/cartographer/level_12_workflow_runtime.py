from __future__ import annotations

import dataclasses


WORKFLOW_TERMINAL_STATUSES: tuple[str, ...] = (
    "completed",
    "blocked",
    "failed",
    "cancelled",
    "timed_out",
    "review_required",
)

WORKFLOW_EVENT_TYPES: tuple[str, ...] = (
    "workflow_created",
    "workflow_dry_run_created",
    "workflow_paused",
    "workflow_resumed",
    "workflow_cancelled",
    "workflow_timed_out",
    "step_approval_required",
    "step_started",
    "step_blocked",
    "step_completed",
    "retry_requested",
    "retry_blocked",
    "verification_required",
    "rollback_required",
    "workflow_closed_out",
)


@dataclasses.dataclass(frozen=True)
class CartographerLevel12WorkflowStepState:
    step_id: str
    title: str
    action_type: str
    status: str
    target_files: tuple[str, ...]
    approval_required: bool
    approval_token_id: str | None
    verification_reference: str | None
    rollback_reference: str | None
    retry_count: int
    max_retries: int
    timeout_seconds: int
    sensitive: bool = True


@dataclasses.dataclass(frozen=True)
class CartographerLevel12WorkflowState:
    workflow_id: str
    run_id: str
    workflow_type: str
    status: str
    current_step_id: str | None
    steps: tuple[CartographerLevel12WorkflowStepState, ...]
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    pause_requested: bool
    cancellation_requested: bool
    timeout_policy: str
    created_at: str
    updated_at: str
    head_expected: str
    git_status_expected: str


@dataclasses.dataclass(frozen=True)
class CartographerLevel12WorkflowEvent:
    event_id: str
    event_type: str
    workflow_id: str
    run_id: str
    step_id: str | None
    sequence: int
    actor: str
    reason: str | None


@dataclasses.dataclass(frozen=True)
class CartographerLevel12WorkflowCheck:
    level: str
    valid_for_dry_run: bool
    workflow_execution_authority_granted: bool
    write_authority_granted: bool
    local_execution_authority_granted: bool
    blocked_reasons: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class CartographerLevel12WorkflowPacket:
    level: str
    title: str
    status: str
    mode: str
    workflow_id: str
    would_start_workflow: bool
    would_execute_step: bool
    would_write_files: bool
    would_run_commands: bool
    workflow_execution_authority_granted: bool
    blocked: bool
    blocked_reasons: tuple[str, ...]
    next_increment: str


def validate_level_12_workflow_state_dry_run(
    state: CartographerLevel12WorkflowState,
) -> CartographerLevel12WorkflowCheck:
    reasons = _state_reasons(state)
    return _check("12.1", reasons)


def validate_level_12_workflow_event_ledger_dry_run(
    events: tuple[CartographerLevel12WorkflowEvent, ...],
) -> CartographerLevel12WorkflowCheck:
    reasons: list[str] = []
    if not events:
        reasons += ["missing_workflow_events"]
    if len({event.event_id for event in events}) != len(events):
        reasons += ["duplicate_workflow_event_id"]

    expected_sequence = 1
    for event in events:
        if event.sequence != expected_sequence:
            reasons += ["workflow_event_sequence_gap_or_reorder"]
            break
        expected_sequence += 1

    for event in events:
        if event.event_type not in WORKFLOW_EVENT_TYPES:
            reasons += ["unsupported_workflow_event_type"]
        if not event.event_id:
            reasons += ["missing_workflow_event_id"]
        if not event.workflow_id:
            reasons += ["missing_workflow_id"]
        if not event.run_id:
            reasons += ["missing_run_id"]
        if not event.actor:
            reasons += ["missing_actor"]
        if event.event_type.endswith("_blocked") and not event.reason:
            reasons += ["blocked_event_missing_reason"]

    return _check("12.2", reasons)


def build_level_12_workflow_dry_run_packet(
    state: CartographerLevel12WorkflowState,
) -> CartographerLevel12WorkflowPacket:
    reasons = _state_reasons(state)
    for step in state.steps:
        if step.sensitive and not step.verification_reference:
            reasons += [f"step_missing_verification:{step.step_id}"]
        if step.sensitive and not step.rollback_reference:
            reasons += [f"step_missing_rollback:{step.step_id}"]

    return _packet(
        level="12.3",
        title="Workflow Dry-Run Packet Builder",
        status="workflow-dry-run-packet-only",
        workflow_id=state.workflow_id,
        blocked_reasons=reasons,
        next_increment="Cartographer Level 12.4: Step Approval Interruption Handling Dry Run",
    )


def build_level_12_step_approval_interruption_dry_run(
    state: CartographerLevel12WorkflowState,
) -> CartographerLevel12WorkflowPacket:
    reasons = _state_reasons(state)
    current_step = _current_step(state)
    if current_step is None:
        reasons += ["missing_current_step"]
    elif current_step.sensitive and not current_step.approval_token_id:
        reasons += ["approval_interruption_required"]

    return _packet(
        level="12.4",
        title="Step Approval Interruption Handling Dry Run",
        status="step-approval-interruption-dry-run-only",
        workflow_id=state.workflow_id,
        blocked_reasons=reasons,
        next_increment="Cartographer Level 12.5: Pause And Resume Runtime Dry Run",
    )


def validate_level_12_pause_resume_dry_run(
    state: CartographerLevel12WorkflowState,
    *,
    current_head: str,
    current_git_status: str,
) -> CartographerLevel12WorkflowCheck:
    reasons = _state_reasons(state)
    if state.status != "paused":
        reasons += ["resume_requires_paused_state"]
    if current_head != state.head_expected:
        reasons += ["head_changed"]
    if current_git_status != state.git_status_expected:
        reasons += ["git_status_changed"]
    if state.cancellation_requested:
        reasons += ["cancelled_workflow_cannot_resume"]

    return _check("12.5", reasons)


def validate_level_12_cancellation_timeout_dry_run(
    state: CartographerLevel12WorkflowState,
) -> CartographerLevel12WorkflowCheck:
    reasons = _state_reasons(state)
    if state.cancellation_requested and state.status not in ("cancelled", "cancelling"):
        reasons += ["cancellation_must_stop_or_cancel_workflow"]
    if state.status == "timed_out" and state.timeout_policy not in ("pause", "cancel"):
        reasons += ["timeout_policy_must_pause_or_cancel"]
    if state.status in ("cancelled", "timed_out") and state.current_step_id is not None:
        reasons += ["terminal_stop_must_clear_current_step"]

    return _check("12.6", reasons)


def validate_level_12_retry_policy_dry_run(
    step: CartographerLevel12WorkflowStepState,
    *,
    retry_requested: bool,
    blocked_reason: str | None,
) -> CartographerLevel12WorkflowCheck:
    reasons: list[str] = []
    if retry_requested and step.retry_count >= step.max_retries:
        reasons += ["max_retries_reached"]
    if retry_requested and not blocked_reason:
        reasons += ["retry_requires_human_readable_reason"]
    if retry_requested and blocked_reason == "protected_path_in_scope":
        reasons += ["retry_after_protected_path_block_forbidden"]

    return _check("12.7", reasons)


def build_level_12_workflow_closeout_packet(
    state: CartographerLevel12WorkflowState,
    *,
    verification_passed: bool,
    rollback_available: bool,
) -> CartographerLevel12WorkflowPacket:
    reasons = _state_reasons(state)
    if state.status not in WORKFLOW_TERMINAL_STATUSES:
        reasons += ["closeout_requires_terminal_status"]
    if not verification_passed:
        reasons += ["closeout_requires_passing_verification"]
    if not rollback_available:
        reasons += ["closeout_requires_rollback_reference"]

    return _packet(
        level="12.8",
        title="Workflow Closeout Packet Runtime Dry Run",
        status="workflow-closeout-packet-dry-run-only",
        workflow_id=state.workflow_id,
        blocked_reasons=reasons,
        next_increment="Cartographer Level 12.9: Verification And Rollback Metadata Enforcement Dry Run",
    )


def validate_level_12_verification_rollback_metadata_dry_run(
    state: CartographerLevel12WorkflowState,
) -> CartographerLevel12WorkflowCheck:
    reasons = _state_reasons(state)
    for step in state.steps:
        if step.sensitive and not step.verification_reference:
            reasons += [f"missing_verification_reference:{step.step_id}"]
        if step.sensitive and not step.rollback_reference:
            reasons += [f"missing_rollback_reference:{step.step_id}"]

    return _check("12.9", reasons)


def build_level_12_closeout_level_13_access_check() -> dict[str, object]:
    return {
        "level": "12.10",
        "title": "Fail-Closed Workflow Gate And Level 13 Access Check",
        "status": "level-12-runtime-dry-run-closeout",
        "level_13_access": "requires_explicit_human_verification",
        "workflow_execution_authority_granted": False,
        "write_authority_granted": False,
        "local_execution_authority_granted": False,
        "worker_orchestration_authority_granted": False,
        "branch_worktree_authority_granted": False,
        "commit_push_merge_authority_granted": False,
        "autonomy_granted": False,
        "protected_lanes_remain_locked": (
            "proxy_ui_makeover",
            "coding_ui_implementation_wiring",
            "source_proxy_stress_testing",
            "codex_adapter_lane",
        ),
        "next_increment": "Cartographer Level 13.1: Worker Identity Registry Runtime Dry Run",
    }


def _state_reasons(state: CartographerLevel12WorkflowState) -> list[str]:
    reasons: list[str] = []
    if not state.workflow_id:
        reasons += ["missing_workflow_id"]
    if not state.run_id:
        reasons += ["missing_run_id"]
    if not state.steps:
        reasons += ["missing_steps"]
    if not state.allowed_files:
        reasons += ["missing_allowed_files"]
    if state.current_step_id and state.current_step_id not in {step.step_id for step in state.steps}:
        reasons += ["current_step_not_in_steps"]
    for step in state.steps:
        if not set(step.target_files).issubset(set(state.allowed_files)):
            reasons += [f"step_scope_exceeds_workflow_scope:{step.step_id}"]
        if set(step.target_files).intersection(state.forbidden_files):
            reasons += [f"step_intersects_forbidden_files:{step.step_id}"]
        if any(_protected_path(path) for path in step.target_files):
            reasons += [f"protected_path_in_scope:{step.step_id}"]
        if step.retry_count < 0 or step.max_retries < 0:
            reasons += [f"invalid_retry_policy:{step.step_id}"]
        if step.timeout_seconds < 1:
            reasons += [f"invalid_timeout_policy:{step.step_id}"]
        if step.sensitive and step.approval_required and not step.approval_token_id:
            reasons += [f"sensitive_step_missing_approval:{step.step_id}"]
    return reasons


def _current_step(
    state: CartographerLevel12WorkflowState,
) -> CartographerLevel12WorkflowStepState | None:
    for step in state.steps:
        if step.step_id == state.current_step_id:
            return step
    return None


def _protected_path(path: str) -> bool:
    return path.startswith(
        (
            "src/",
            "source_proxy/api/",
            "source_proxy/verification/",
            "source_proxy/codex/",
            "source_proxy/testing/runner.py",
        )
    )


def _check(level: str, blocked_reasons: list[str]) -> CartographerLevel12WorkflowCheck:
    return CartographerLevel12WorkflowCheck(
        level=level,
        valid_for_dry_run=not blocked_reasons,
        workflow_execution_authority_granted=False,
        write_authority_granted=False,
        local_execution_authority_granted=False,
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
    )


def _packet(
    *,
    level: str,
    title: str,
    status: str,
    workflow_id: str,
    blocked_reasons: list[str],
    next_increment: str,
) -> CartographerLevel12WorkflowPacket:
    return CartographerLevel12WorkflowPacket(
        level=level,
        title=title,
        status=status,
        mode="dry_run",
        workflow_id=workflow_id,
        would_start_workflow=False,
        would_execute_step=False,
        would_write_files=False,
        would_run_commands=False,
        workflow_execution_authority_granted=False,
        blocked=bool(blocked_reasons),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        next_increment=next_increment,
    )
