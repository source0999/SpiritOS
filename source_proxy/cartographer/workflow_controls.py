from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any

from source_proxy.cartographer.workflow_state import (
    WORKFLOW_STATUSES,
    WorkflowRunState,
)

WORKFLOW_CONTROLS_PHASE = "Plan 5 Phase 3: Pause/cancel/timeout/retry controls"

WORKFLOW_CONTROL_TYPES: tuple[str, ...] = (
    "pause",
    "cancel",
    "timeout",
    "retry",
)

MAX_RETRY_COUNT = 3

CONTROL_TARGET_STATUS: dict[str, str] = {
    "pause": "blocked",
    "cancel": "cancelled",
    "timeout": "failed",
    "retry": "running",
}

CONTROL_EVENT_TYPE: dict[str, str] = {
    "pause": "workflow_paused",
    "cancel": "workflow_cancelled",
    "timeout": "workflow_timed_out",
    "retry": "step_retried",
}

CONTROL_ALLOWED_FROM: dict[str, tuple[str, ...]] = {
    "pause": ("approved", "running", "blocked"),
    "cancel": ("pending", "approved", "running", "blocked", "failed"),
    "timeout": ("approved", "running", "blocked"),
    "retry": ("blocked", "failed"),
}

TERMINAL_STATUSES: tuple[str, ...] = ("completed", "cancelled")


@dataclasses.dataclass(frozen=True)
class WorkflowControlContext:
    requested_by: str
    reason: str
    retry_count: int = 0
    max_retry_count: int = MAX_RETRY_COUNT
    step_id: str | None = None
    requested_at: str | None = None
    kill_switch_active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkflowControlPreview:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    control_type: str
    run_id: str | None
    step_id: str | None
    current_status: str | None
    target_status: str | None
    event_type: str | None
    retry_count: int
    max_retry_count: int
    next_retry_count: int | None
    requested_by: str | None
    requested_at: str | None
    reason: str | None
    preview_only: bool = True
    control_only: bool = True
    execution_available: bool = False
    durable_write_available: bool = False
    workflow_execution_authority_granted: bool = False
    queue_authority_granted: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    no_execution_guarantee: str = (
        "Plan 5 Phase 3 previews workflow controls only. It does not execute "
        "workflows, continue cancelled work, run queues, run commands, perform "
        "safe writes, append durable events, stage, commit, push, branch, "
        "create worktrees, stash, clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_workflow_controls_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Daily Driver Autonomy Roadmap Plan 5",
        "phase": WORKFLOW_CONTROLS_PHASE,
        "status": "control-preview-only",
        "control_types": WORKFLOW_CONTROL_TYPES,
        "control_target_status": CONTROL_TARGET_STATUS,
        "control_event_type": CONTROL_EVENT_TYPE,
        "control_allowed_from": CONTROL_ALLOWED_FROM,
        "max_retry_count": MAX_RETRY_COUNT,
        "bounded_retry_counts": True,
        "cancelled_workflow_continues_work": False,
        "execution_available": False,
        "durable_write_available": False,
        "workflow_execution_authority_granted": False,
        "queue_authority_granted": False,
        "command_authority_granted": False,
        "write_authority_granted": False,
        "git_mutation_authority_granted": False,
        "safe_next_action": "Preview controls only; require later approval for workflow execution.",
    }


def preview_workflow_control(
    workflow_state: Any,
    control_type: str,
    *,
    context: WorkflowControlContext | dict[str, Any] | None,
    now: datetime | None = None,
) -> WorkflowControlPreview:
    current_time = now or datetime.now(UTC)
    normalized_control = control_type.strip() if isinstance(control_type, str) else ""
    run_id = _string_value(workflow_state, "run_id")
    current_status = _string_value(workflow_state, "status")
    normalized_context = _normalize_context(context, current_time)
    retry_count = normalized_context.get("retry_count", 0)
    max_retry_count = normalized_context.get("max_retry_count", MAX_RETRY_COUNT)
    reasons: list[str] = []

    if not run_id:
        reasons.append("missing_run_id")
    if current_status not in WORKFLOW_STATUSES:
        reasons.append("unknown_current_status")
    if normalized_control not in WORKFLOW_CONTROL_TYPES:
        reasons.append("unknown_control_type")
    if not normalized_context["requested_by"]:
        reasons.append("missing_requested_by")
    if not normalized_context["reason"]:
        reasons.append("missing_reason")
    if normalized_context["kill_switch_active"]:
        reasons.append("kill_switch_active")
    if max_retry_count != MAX_RETRY_COUNT:
        reasons.append("unsupported_max_retry_count")
    if retry_count < 0:
        reasons.append("invalid_retry_count")
    if current_status in TERMINAL_STATUSES:
        reasons.append("terminal_workflow_cannot_continue")

    if (
        normalized_control in WORKFLOW_CONTROL_TYPES
        and current_status in WORKFLOW_STATUSES
        and current_status not in CONTROL_ALLOWED_FROM[normalized_control]
    ):
        reasons.append("control_not_allowed_from_status")
    if normalized_control == "retry":
        if not normalized_context["step_id"]:
            reasons.append("missing_step_id")
        if retry_count >= MAX_RETRY_COUNT:
            reasons.append("retry_limit_exceeded")

    accepted = not reasons
    next_retry_count = retry_count + 1 if accepted and normalized_control == "retry" else None

    return WorkflowControlPreview(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=tuple(_dedupe(reasons)),
        control_type=normalized_control,
        run_id=run_id,
        step_id=normalized_context["step_id"],
        current_status=current_status,
        target_status=CONTROL_TARGET_STATUS.get(normalized_control),
        event_type=CONTROL_EVENT_TYPE.get(normalized_control),
        retry_count=retry_count,
        max_retry_count=max_retry_count,
        next_retry_count=next_retry_count,
        requested_by=normalized_context["requested_by"],
        requested_at=normalized_context["requested_at"],
        reason=normalized_context["reason"],
    )


def _normalize_context(
    context: WorkflowControlContext | dict[str, Any] | None,
    current_time: datetime,
) -> dict[str, Any]:
    if isinstance(context, WorkflowControlContext):
        context = context.to_dict()
    if not isinstance(context, dict):
        context = {}

    retry_count = context.get("retry_count", 0)
    if not isinstance(retry_count, int):
        retry_count = -1
    max_retry_count = context.get("max_retry_count", MAX_RETRY_COUNT)
    if not isinstance(max_retry_count, int):
        max_retry_count = -1

    requested_at = context.get("requested_at")
    if not isinstance(requested_at, str) or not requested_at.strip():
        requested_at = _format_utc(current_time)

    return {
        "requested_by": _optional_string(context.get("requested_by")),
        "reason": _optional_string(context.get("reason")),
        "retry_count": retry_count,
        "max_retry_count": max_retry_count,
        "step_id": _optional_string(context.get("step_id")),
        "requested_at": requested_at.strip(),
        "kill_switch_active": context.get("kill_switch_active") is True,
    }


def _string_value(value: Any, field: str) -> str | None:
    if isinstance(value, WorkflowRunState):
        item = getattr(value, field)
    elif isinstance(value, dict):
        item = value.get(field)
    else:
        return None
    return _optional_string(item)


def _optional_string(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _dedupe(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped
