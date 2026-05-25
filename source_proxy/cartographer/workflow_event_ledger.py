from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

WORKFLOW_EVENT_LEDGER_PHASE = "Plan 7 Phase 7.1: Event Ledger"
APPROVAL_EVENT_PREVIEW_PHASE = "Plan 4 Phase 4.1: Approval Event Preview"

APPROVAL_EVENT_PREVIEW_TYPES: tuple[str, ...] = (
    "approval_requested",
    "approval_granted",
    "approval_rejected",
    "approval_expired",
    "approval_blocked",
    "approval_consumed_preview",
)

WORKFLOW_LEDGER_EVENT_TYPES: tuple[str, ...] = (
    "workflow_created",
    "task_selected",
    "step_started",
    "step_blocked",
    "step_completed",
    "workflow_paused",
    "workflow_resumed",
    "workflow_cancelled",
    "workflow_timed_out",
    "workflow_failed",
    "step_retried",
    "workflow_verified",
    "workflow_closed_out",
)

STEP_EVENT_TYPES: tuple[str, ...] = (
    "task_selected",
    "step_started",
    "step_blocked",
    "step_completed",
    "step_retried",
)

REASON_REQUIRED_EVENT_TYPES: tuple[str, ...] = (
    "step_blocked",
    "workflow_paused",
    "workflow_resumed",
    "workflow_cancelled",
    "workflow_timed_out",
    "workflow_failed",
    "step_retried",
)

REFERENCE_REQUIRED_EVENT_TYPES: tuple[str, ...] = (
    "workflow_verified",
    "workflow_closed_out",
)

RECEIPT_REQUIRED_EVENT_TYPES: tuple[str, ...] = (
    "workflow_closed_out",
)

FORBIDDEN_LEDGER_EXECUTION_CLASSES: tuple[str, ...] = (
    "workflow_execution",
    "queue_execution",
    "command_execution",
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
)

APPROVAL_EVENT_REASON_MESSAGES: dict[str, str] = {
    "unsupported_approval_event_type": "Approval event type is not supported.",
    "missing_run_id": "Approval event preview requires a run id.",
    "missing_token_id": "Approval event preview requires a token id.",
    "missing_actor": "Approval event preview requires the actor recording the preview.",
    "missing_reason_codes": "Blocked, rejected, or expired approval events require reason codes.",
}


@dataclasses.dataclass(frozen=True)
class ApprovalEventPreview:
    status: str
    accepted: bool
    blocked: bool
    event_id: str
    event_type: str
    run_id: str
    token_id: str
    occurred_at: str
    actor: str
    approver_id: str | None
    operator_id: str | None
    action_type: str | None
    reason_codes: tuple[str, ...]
    reason_messages: tuple[str, ...]
    preview_only: bool = True
    durable_write_available: bool = False
    event_storage_available: bool = False
    token_consumed_for_real: bool = False
    authority_granted: bool = False
    write_authority_granted: bool = False
    command_authority_granted: bool = False
    workflow_execution_authority_granted: bool = False
    queue_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    no_execution_guarantee: str = (
        "Approval event previews are data-only audit records. They do not "
        "persist production ledger entries, consume approval tokens for real, "
        "run commands, execute queues, mutate files, or perform git actions."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkflowLedgerEvent:
    event_id: str
    event_type: str
    run_id: str
    sequence: int
    occurred_at: str
    actor: str
    step_id: str | None = None
    approval_token_id: str | None = None
    workflow_status: str | None = None
    reason: str | None = None
    verification_reference: str | None = None
    receipt_path: str | None = None
    closeout: dict[str, Any] | None = None
    previous_event_hash: str | None = None
    event_hash: str | None = None
    append_only: bool = True
    execution_available: bool = False
    durable_write_available: bool = False
    queue_authority_granted: bool = False
    command_authority_granted: bool = False
    workflow_execution_authority_granted: bool = False
    git_mutation_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkflowLedgerValidation:
    status: str
    valid: bool
    blocked: bool
    reasons: tuple[str, ...]
    event_count: int
    append_only: bool = True
    execution_available: bool = False
    durable_write_available: bool = False
    queue_authority_granted: bool = False
    command_authority_granted: bool = False
    workflow_execution_authority_granted: bool = False
    git_mutation_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkflowLedgerAppendPreview:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    next_sequence: int | None
    previous_event_hash: str | None
    appended_events: tuple[WorkflowLedgerEvent, ...]
    preview_only: bool = True
    append_only: bool = True
    execution_available: bool = False
    durable_write_available: bool = False
    queue_authority_granted: bool = False
    command_authority_granted: bool = False
    workflow_execution_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    no_execution_guarantee: str = (
        "Plan 7 Phase 7.1 models an append-only workflow event ledger only. It "
        "does not execute workflows, run queues, run commands, perform safe "
        "writes, mint or store approval tokens, stage, commit, push, branch, "
        "create worktrees, stash, clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_workflow_event_ledger_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 7/10",
        "phase": WORKFLOW_EVENT_LEDGER_PHASE,
        "status": "append-only-ledger-model",
        "append_only": True,
        "supported_event_types": WORKFLOW_LEDGER_EVENT_TYPES,
        "step_event_types": STEP_EVENT_TYPES,
        "reason_required_event_types": REASON_REQUIRED_EVENT_TYPES,
        "reference_required_event_types": REFERENCE_REQUIRED_EVENT_TYPES,
        "receipt_required_event_types": RECEIPT_REQUIRED_EVENT_TYPES,
        "forbidden_execution_classes": FORBIDDEN_LEDGER_EXECUTION_CLASSES,
        "execution_available": False,
        "durable_write_available": False,
        "workflow_execution_authority_granted": False,
        "queue_authority_granted": False,
        "command_authority_granted": False,
        "write_authority_granted": False,
        "git_mutation_authority_granted": False,
        "token_minting_available": False,
        "approval_storage_available": False,
        "safe_next_action": "Append validated event data only; require later approval for runtime execution.",
    }


def build_approval_event_preview_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 4",
        "phase": APPROVAL_EVENT_PREVIEW_PHASE,
        "status": "preview-only",
        "supported_event_types": APPROVAL_EVENT_PREVIEW_TYPES,
        "preview_only": True,
        "durable_write_available": False,
        "event_storage_available": False,
        "token_consumed_for_real": False,
        "authority_granted": False,
        "write_authority_granted": False,
        "command_authority_granted": False,
        "workflow_execution_authority_granted": False,
        "queue_authority_granted": False,
        "git_mutation_authority_granted": False,
        "safe_next_action": "Render approval event previews only; do not persist or execute.",
    }


def build_approval_event_preview(
    *,
    event_type: str,
    run_id: str,
    token_id: str,
    actor: str,
    occurred_at: datetime,
    approver_id: str | None = None,
    operator_id: str | None = None,
    action_type: str | None = None,
    reason_codes: list[str] | tuple[str, ...] = (),
) -> ApprovalEventPreview:
    normalized_event_type = _normalize_string(event_type)
    normalized_run_id = _normalize_string(run_id)
    normalized_token_id = _normalize_string(token_id)
    normalized_actor = _normalize_string(actor)
    normalized_reasons = _normalize_string_tuple(reason_codes)
    shape_reasons = _approval_event_shape_reasons(
        event_type=normalized_event_type,
        run_id=normalized_run_id,
        token_id=normalized_token_id,
        actor=normalized_actor,
        reason_codes=normalized_reasons,
    )
    reason_codes = tuple(_dedupe([*shape_reasons, *normalized_reasons]))
    accepted = not shape_reasons

    return ApprovalEventPreview(
        status="previewed" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        event_id=_approval_event_id(
            normalized_event_type,
            normalized_run_id,
            normalized_token_id,
            occurred_at,
        ),
        event_type=normalized_event_type,
        run_id=normalized_run_id,
        token_id=normalized_token_id,
        occurred_at=_format_utc(occurred_at),
        actor=normalized_actor,
        approver_id=_optional_string(approver_id),
        operator_id=_optional_string(operator_id),
        action_type=_optional_string(action_type),
        reason_codes=reason_codes,
        reason_messages=tuple(_approval_event_reason_message(reason) for reason in reason_codes),
    )


def build_workflow_ledger_event(
    *,
    event_id: str,
    event_type: str,
    run_id: str,
    sequence: int,
    actor: str,
    occurred_at: datetime,
    step_id: str | None = None,
    approval_token_id: str | None = None,
    workflow_status: str | None = None,
    reason: str | None = None,
    verification_reference: str | None = None,
    receipt_path: str | None = None,
    closeout: dict[str, Any] | None = None,
    previous_event_hash: str | None = None,
) -> WorkflowLedgerEvent:
    timestamp = _format_utc(occurred_at)
    event = WorkflowLedgerEvent(
        event_id=event_id.strip() if isinstance(event_id, str) else "",
        event_type=event_type.strip() if isinstance(event_type, str) else "",
        run_id=run_id.strip() if isinstance(run_id, str) else "",
        sequence=sequence,
        occurred_at=timestamp,
        actor=actor.strip() if isinstance(actor, str) else "",
        step_id=_optional_string(step_id),
        approval_token_id=_optional_string(approval_token_id),
        workflow_status=_optional_string(workflow_status),
        reason=_optional_string(reason),
        verification_reference=_optional_string(verification_reference),
        receipt_path=_optional_string(receipt_path),
        closeout=closeout if isinstance(closeout, dict) else None,
        previous_event_hash=_optional_string(previous_event_hash),
    )
    return dataclasses.replace(event, event_hash=_event_hash(event))


def preview_append_workflow_ledger_event(
    events: tuple[WorkflowLedgerEvent, ...],
    event: WorkflowLedgerEvent,
) -> WorkflowLedgerAppendPreview:
    existing_validation = validate_workflow_event_ledger(events)
    reasons = list(existing_validation.reasons)
    previous_hash = events[-1].event_hash if events else None
    next_sequence = len(events) + 1

    if event.sequence != next_sequence:
        reasons.append("next_sequence_mismatch")
    if event.previous_event_hash != previous_hash:
        reasons.append("previous_event_hash_mismatch")
    if any(existing.event_id == event.event_id for existing in events):
        reasons.append("duplicate_event_id")
    if events and any(existing.run_id != event.run_id for existing in events):
        reasons.append("run_id_mismatch")

    reasons.extend(_event_shape_reasons(event))
    appended_events = (*events, event) if not reasons else events
    accepted = not reasons

    return WorkflowLedgerAppendPreview(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=tuple(_dedupe(reasons)),
        next_sequence=next_sequence,
        previous_event_hash=previous_hash,
        appended_events=appended_events,
    )


def validate_workflow_event_ledger(
    events: tuple[WorkflowLedgerEvent, ...],
) -> WorkflowLedgerValidation:
    reasons: list[str] = []
    if not isinstance(events, tuple):
        reasons.append("ledger_events_must_be_tuple")
        events = ()

    seen_ids: set[str] = set()
    run_id: str | None = None
    previous_hash: str | None = None
    for index, event in enumerate(events, start=1):
        reasons.extend(_event_shape_reasons(event))
        if not isinstance(event, WorkflowLedgerEvent):
            continue
        if event.sequence != index:
            reasons.append("sequence_gap_or_reorder")
        if event.event_id in seen_ids:
            reasons.append("duplicate_event_id")
        seen_ids.add(event.event_id)
        if run_id is None:
            run_id = event.run_id
        elif event.run_id != run_id:
            reasons.append("run_id_mismatch")
        if event.previous_event_hash != previous_hash:
            reasons.append("previous_event_hash_mismatch")
        if event.event_hash != _event_hash(event):
            reasons.append("event_hash_mismatch")
        previous_hash = event.event_hash

    valid = not reasons
    return WorkflowLedgerValidation(
        status="valid" if valid else "blocked",
        valid=valid,
        blocked=not valid,
        reasons=tuple(_dedupe(reasons)),
        event_count=len(events),
    )


def _event_shape_reasons(event: Any) -> list[str]:
    if not isinstance(event, WorkflowLedgerEvent):
        return ["malformed_event"]

    reasons: list[str] = []
    if not event.event_id:
        reasons.append("missing_event_id")
    if event.event_type not in WORKFLOW_LEDGER_EVENT_TYPES:
        reasons.append("unsupported_event_type")
    if not event.run_id:
        reasons.append("missing_run_id")
    if event.sequence < 1:
        reasons.append("invalid_sequence")
    if not event.occurred_at:
        reasons.append("missing_occurred_at")
    if not event.actor:
        reasons.append("missing_actor")
    if event.event_type in STEP_EVENT_TYPES and not event.step_id:
        reasons.append("missing_step_id")
    if event.event_type in REASON_REQUIRED_EVENT_TYPES and not event.reason:
        reasons.append("missing_reason")
    if event.event_type == "workflow_verified" and not event.verification_reference:
        reasons.append("missing_verification_reference")
    if event.event_type == "workflow_closed_out" and not event.closeout:
        reasons.append("missing_closeout")
    if event.event_type in RECEIPT_REQUIRED_EVENT_TYPES and not event.receipt_path:
        reasons.append("missing_receipt_path")
    return reasons


def _approval_event_shape_reasons(
    *,
    event_type: str,
    run_id: str,
    token_id: str,
    actor: str,
    reason_codes: tuple[str, ...],
) -> list[str]:
    reasons: list[str] = []
    if event_type not in APPROVAL_EVENT_PREVIEW_TYPES:
        reasons.append("unsupported_approval_event_type")
    if not run_id:
        reasons.append("missing_run_id")
    if not token_id:
        reasons.append("missing_token_id")
    if not actor:
        reasons.append("missing_actor")
    if event_type in {
        "approval_rejected",
        "approval_expired",
        "approval_blocked",
    } and not reason_codes:
        reasons.append("missing_reason_codes")
    return reasons


def _event_hash(event: WorkflowLedgerEvent) -> str:
    payload = (
        event.event_id,
        event.event_type,
        event.run_id,
        str(event.sequence),
        event.occurred_at,
        event.actor,
        event.step_id or "",
        event.approval_token_id or "",
        event.workflow_status or "",
        event.reason or "",
        event.verification_reference or "",
        event.receipt_path or "",
        repr(sorted((event.closeout or {}).items())),
        event.previous_event_hash or "",
    )
    return sha256("\x1f".join(payload).encode("utf-8")).hexdigest()


def _approval_event_id(
    event_type: str,
    run_id: str,
    token_id: str,
    occurred_at: datetime,
) -> str:
    payload = "\x1f".join((event_type, run_id, token_id, _format_utc(occurred_at)))
    return f"approval-preview-{sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _approval_event_reason_message(reason: str) -> str:
    base_reason = reason.split(":", 1)[0]
    return APPROVAL_EVENT_REASON_MESSAGES.get(
        base_reason,
        "Approval event preview records a fail-closed approval reason.",
    )


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _optional_string(value: str | None) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _normalize_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _normalize_string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[str] = []
    for item in value:
        text = _normalize_string(item)
        if text:
            normalized.append(text)
    return tuple(normalized)


def _dedupe(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped
