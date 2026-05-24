from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any

WORKFLOW_STATE_MODEL_PHASE = "Plan 5 Phase 1: Workflow State Model"

WORKFLOW_STATUSES: tuple[str, ...] = (
    "pending",
    "approved",
    "running",
    "completed",
    "blocked",
    "failed",
    "cancelled",
)

TERMINAL_WORKFLOW_STATUSES: tuple[str, ...] = (
    "completed",
    "failed",
    "cancelled",
)

WORKFLOW_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "pending": ("approved", "blocked", "cancelled"),
    "approved": ("running", "blocked", "cancelled"),
    "running": ("completed", "blocked", "failed", "cancelled"),
    "blocked": ("pending", "cancelled"),
    "failed": (),
    "completed": (),
    "cancelled": (),
}

REQUIRED_APPROVAL_CONTEXT_FIELDS: tuple[str, ...] = (
    "token_id",
    "approved_by",
    "approved_for_actor",
    "requested_actor",
    "action_class",
    "trust_tier",
    "issued_at",
    "expires_at",
    "expected_head",
    "current_head",
    "dirty_tree_matches_expected",
)

WORKFLOW_ACTION_CLASS = "workflow_state_transition"
WORKFLOW_TRUST_TIER = "tier-1"

FORBIDDEN_EXECUTION_CLASSES: tuple[str, ...] = (
    "command",
    "queue",
    "workflow_execution",
    "safe_write",
    "git_mutation",
    "commit",
    "push",
    "branch",
    "worktree",
    "stash",
    "clean",
    "reset",
    "checkout",
    "token_mint",
    "approval_storage",
    "durable_storage",
)


@dataclasses.dataclass(frozen=True)
class WorkflowStepState:
    step_id: str
    status: str = "pending"
    approval_token_id: str | None = None
    allowed_files: tuple[str, ...] = ()
    forbidden_files: tuple[str, ...] = ()
    blocker_reason: str | None = None
    verification_result: dict[str, Any] | None = None
    rollback_reference: str | None = None
    receipt_path: str | None = None
    closeout: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkflowRunState:
    run_id: str
    status: str = "pending"
    steps: tuple[WorkflowStepState, ...] = ()
    approval_token_id: str | None = None
    allowed_files: tuple[str, ...] = ()
    forbidden_files: tuple[str, ...] = ()
    blocker_reason: str | None = None
    verification_result: dict[str, Any] | None = None
    rollback_reference: str | None = None
    receipt_path: str | None = None
    closeout: dict[str, Any] | None = None
    model_only: bool = True
    durable_storage_available: bool = False
    execution_available: bool = False
    queue_authority_granted: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkflowTransitionPreview:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    run_id: str | None
    current_status: str | None
    requested_status: str
    approval_token_id: str | None
    preview_only: bool = True
    model_only: bool = True
    durable_storage_available: bool = False
    execution_available: bool = False
    workflow_execution_authority_granted: bool = False
    queue_authority_granted: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    token_minting_available: bool = False
    approval_storage_available: bool = False
    no_execution_guarantee: str = (
        "Plan 5 Phase 1 models workflow state and previews transitions only. "
        "It does not execute workflows, run queues, run commands, perform safe "
        "writes, mint or store approval tokens, stage, commit, push, branch, "
        "create worktrees, stash, clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_workflow_state_model_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Daily Driver Autonomy Roadmap Plan 5",
        "phase": WORKFLOW_STATE_MODEL_PHASE,
        "status": "model-only",
        "workflow_statuses": WORKFLOW_STATUSES,
        "terminal_statuses": TERMINAL_WORKFLOW_STATUSES,
        "required_approval_context_fields": REQUIRED_APPROVAL_CONTEXT_FIELDS,
        "workflow_action_class": WORKFLOW_ACTION_CLASS,
        "workflow_trust_tier": WORKFLOW_TRUST_TIER,
        "forbidden_execution_classes": FORBIDDEN_EXECUTION_CLASSES,
        "preview_only": True,
        "durable_storage_available": False,
        "execution_available": False,
        "workflow_execution_authority_granted": False,
        "queue_authority_granted": False,
        "command_authority_granted": False,
        "write_authority_granted": False,
        "git_mutation_authority_granted": False,
        "token_minting_available": False,
        "approval_storage_available": False,
        "safe_next_action": "Model state only; require later phase approval for ledger or execution.",
    }


def preview_workflow_transition(
    workflow_state: Any,
    requested_status: str,
    *,
    approval_context: dict[str, Any] | None,
    now: datetime | None = None,
) -> WorkflowTransitionPreview:
    current_time = now or datetime.now(UTC)
    run_id = _string_value(workflow_state, "run_id")
    current_status = _string_value(workflow_state, "status")
    approval_token_id = _string_value(workflow_state, "approval_token_id")
    requested_status = requested_status.strip() if isinstance(requested_status, str) else ""
    reasons: list[str] = []

    if not run_id:
        reasons.append("missing_run_id")
    if current_status not in WORKFLOW_STATUSES:
        reasons.append("unknown_current_status")
    if requested_status not in WORKFLOW_STATUSES:
        reasons.append("unknown_requested_status")
    if (
        current_status in WORKFLOW_STATUSES
        and requested_status in WORKFLOW_STATUSES
        and requested_status not in WORKFLOW_TRANSITIONS[current_status]
    ):
        reasons.append("invalid_transition")

    reasons.extend(_approval_context_reasons(approval_context, current_time))
    accepted = not reasons

    return WorkflowTransitionPreview(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=tuple(_dedupe(reasons)),
        run_id=run_id,
        current_status=current_status,
        requested_status=requested_status,
        approval_token_id=approval_token_id,
    )


def _approval_context_reasons(
    approval_context: dict[str, Any] | None,
    current_time: datetime,
) -> list[str]:
    reasons: list[str] = []
    if not isinstance(approval_context, dict):
        return ["missing_approval_context"]

    for field in REQUIRED_APPROVAL_CONTEXT_FIELDS:
        if field not in approval_context:
            reasons.append(f"missing_approval_context_field:{field}")

    approved_by = _normalized_context_string(approval_context, "approved_by", reasons)
    approved_for_actor = _normalized_context_string(
        approval_context,
        "approved_for_actor",
        reasons,
    )
    requested_actor = _normalized_context_string(
        approval_context,
        "requested_actor",
        reasons,
    )
    _normalized_context_string(approval_context, "token_id", reasons)
    action_class = _normalized_context_string(approval_context, "action_class", reasons)
    trust_tier = _normalized_context_string(approval_context, "trust_tier", reasons)
    expected_head = _normalized_context_string(approval_context, "expected_head", reasons)
    current_head = _normalized_context_string(approval_context, "current_head", reasons)

    if approval_context.get("kill_switch_active") is True:
        reasons.append("kill_switch_active")
    if expected_head and current_head and expected_head != current_head:
        reasons.append("stale_head")
    if approval_context.get("dirty_tree_matches_expected") is not True:
        reasons.append("dirty_tree_mismatch")
    if approved_by and requested_actor and approved_by == requested_actor:
        reasons.append("self_approval_rejected")
    if approved_by and approved_for_actor and approved_by == approved_for_actor:
        reasons.append("self_approval_rejected")
    if approved_for_actor and requested_actor and approved_for_actor != requested_actor:
        reasons.append("wrong_actor")
    if action_class and action_class != WORKFLOW_ACTION_CLASS:
        reasons.append("wrong_action_class")
    if trust_tier and trust_tier != WORKFLOW_TRUST_TIER:
        reasons.append("wrong_trust_tier")

    execution_class = approval_context.get("execution_class")
    if isinstance(execution_class, str) and execution_class.strip() in FORBIDDEN_EXECUTION_CLASSES:
        reasons.append("forbidden_execution_class")

    expires_at = _context_datetime(approval_context, "expires_at", reasons)
    _context_datetime(approval_context, "issued_at", reasons)
    if expires_at is not None and expires_at <= current_time:
        reasons.append("token_expired")

    return reasons


def _string_value(value: Any, field: str) -> str | None:
    if isinstance(value, WorkflowRunState):
        item = getattr(value, field)
    elif isinstance(value, dict):
        item = value.get(field)
    else:
        return None
    if not isinstance(item, str) or not item.strip():
        return None
    return item.strip()


def _normalized_context_string(
    context: dict[str, Any],
    field: str,
    reasons: list[str],
) -> str | None:
    if field not in context:
        return None
    value = context[field]
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"malformed_approval_context_field:{field}")
        return None
    return value.strip()


def _context_datetime(
    context: dict[str, Any],
    field: str,
    reasons: list[str],
) -> datetime | None:
    value = _normalized_context_string(context, field, reasons)
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        reasons.append(f"malformed_approval_context_field:{field}")
        return None
    if parsed.tzinfo is None:
        reasons.append(f"malformed_approval_context_field:{field}")
        return None
    return parsed.astimezone(UTC)


def _dedupe(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped
