from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from source_proxy.cartographer.safe_write import (
    SAFE_WRITE_ACTION_CLASS,
    execute_safe_write_request as _execute_safe_write_request,
)
from source_proxy.cartographer.verification_runner import (
    run_verification_command as _run_verification_command,
)
from source_proxy.cartographer.workflow_event_ledger import (
    WorkflowLedgerEvent,
    build_workflow_ledger_event as _build_workflow_ledger_event,
    preview_append_workflow_ledger_event as _preview_append_workflow_ledger_event,
)

WORKFLOW_RUNNER_PHASE = (
    "Plan 5 Phase 4: First workflow: safe docs evidence write then verify"
)

SAFE_DOCS_EVIDENCE_WORKFLOW_CLASS = "safe_docs_evidence_write_then_verify"
SAFE_DOCS_EVIDENCE_PREFIX = "docs/cartographer-live-evidence/"


@dataclasses.dataclass(frozen=True)
class SafeDocsEvidenceWorkflowResult:
    status: str
    completed: bool
    blocked: bool
    reasons: tuple[str, ...]
    run_id: str
    step_id: str
    target_file: str
    safe_write_result: dict[str, Any]
    verification_result: dict[str, Any] | None
    ledger_events: tuple[WorkflowLedgerEvent, ...]
    workflow_class: str = SAFE_DOCS_EVIDENCE_WORKFLOW_CLASS
    workflow_execution_authority_granted: bool = False
    queue_authority_granted: bool = False
    command_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    no_git_mutation_guarantee: str = (
        "This workflow composes an approved safe docs evidence write with an "
        "exact allowlisted verification command. It does not stage, commit, "
        "push, branch, create worktrees, stash, clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_safe_docs_evidence_workflow_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Daily Driver Autonomy Roadmap Plan 5",
        "phase": WORKFLOW_RUNNER_PHASE,
        "status": "first-safe-docs-evidence-workflow-available",
        "workflow_class": SAFE_DOCS_EVIDENCE_WORKFLOW_CLASS,
        "safe_docs_evidence_prefix": SAFE_DOCS_EVIDENCE_PREFIX,
        "safe_write_action_class": SAFE_WRITE_ACTION_CLASS,
        "verification_required": True,
        "queue_authority_granted": False,
        "command_authority_granted": False,
        "workflow_execution_authority_granted": False,
        "git_mutation_authority_granted": False,
        "safe_next_action": "Run only with exact approved docs evidence file and exact allowlisted verification argv.",
    }


def execute_safe_docs_evidence_workflow(
    *,
    run_id: str,
    step_id: str,
    approval_payload: Any,
    requested_actor: str,
    requested_scope: dict[str, str],
    target_file: str,
    content: str,
    consumption_context: dict[str, Any] | None,
    workspace_root: Path,
    current_head: str | None,
    verification_argv: Any,
    approved_test_files: list[str] | tuple[str, ...] = (),
    now: datetime | None = None,
) -> SafeDocsEvidenceWorkflowResult:
    current_time = now or datetime.now(UTC)
    normalized_run_id = _required_string(run_id)
    normalized_step_id = _required_string(step_id)
    normalized_target = _required_string(target_file)
    reasons: list[str] = []
    events: tuple[WorkflowLedgerEvent, ...] = ()

    if not normalized_run_id:
        reasons.append("missing_run_id")
    if not normalized_step_id:
        reasons.append("missing_step_id")
    if not normalized_target:
        reasons.append("missing_target_file")
    if normalized_target and not normalized_target.startswith(SAFE_DOCS_EVIDENCE_PREFIX):
        reasons.append("target_not_safe_docs_evidence")

    if reasons:
        return _result(
            status="blocked",
            completed=False,
            reasons=reasons,
            run_id=normalized_run_id,
            step_id=normalized_step_id,
            target_file=normalized_target,
            safe_write_result={"status": "not_run", "written": False, "blocked": True},
            verification_result=None,
            ledger_events=events,
        )

    events = _append_event(
        events,
        event_id=f"{normalized_run_id}-workflow-created",
        event_type="workflow_created",
        run_id=normalized_run_id,
        sequence=1,
        actor=requested_actor,
        occurred_at=current_time,
        workflow_status="running",
        approval_token_id=_token_id(approval_payload),
    )
    events = _append_event(
        events,
        event_id=f"{normalized_run_id}-{normalized_step_id}-started",
        event_type="step_started",
        run_id=normalized_run_id,
        sequence=2,
        actor=requested_actor,
        occurred_at=current_time,
        step_id=normalized_step_id,
        workflow_status="running",
        approval_token_id=_token_id(approval_payload),
    )

    safe_write_result = _execute_safe_write_request(
        approval_payload,
        requested_actor=requested_actor,
        requested_scope=requested_scope,
        target_file=normalized_target,
        content=content,
        consumption_context=consumption_context,
        workspace_root=workspace_root,
        current_head=current_head,
        now=current_time,
    )
    safe_write_data = safe_write_result.to_dict()
    if safe_write_result.blocked:
        events = _append_event(
            events,
            event_id=f"{normalized_run_id}-{normalized_step_id}-blocked",
            event_type="step_blocked",
            run_id=normalized_run_id,
            sequence=len(events) + 1,
            actor=requested_actor,
            occurred_at=current_time,
            step_id=normalized_step_id,
            workflow_status="blocked",
            approval_token_id=_token_id(approval_payload),
            reason=",".join(safe_write_result.reasons) or "safe_write_blocked",
        )
        return _result(
            status="blocked",
            completed=False,
            reasons=[f"safe_write:{reason}" for reason in safe_write_result.reasons],
            run_id=normalized_run_id,
            step_id=normalized_step_id,
            target_file=normalized_target,
            safe_write_result=safe_write_data,
            verification_result=None,
            ledger_events=events,
        )

    events = _append_event(
        events,
        event_id=f"{normalized_run_id}-{normalized_step_id}-completed",
        event_type="step_completed",
        run_id=normalized_run_id,
        sequence=len(events) + 1,
        actor=requested_actor,
        occurred_at=current_time,
        step_id=normalized_step_id,
        workflow_status="running",
        approval_token_id=_token_id(approval_payload),
    )

    verification_result = _run_verification_command(
        verification_argv,
        workspace_root=workspace_root,
        approved_test_files=approved_test_files,
        timeout_seconds=10,
    )
    verification_data = verification_result.to_dict()
    if verification_result.blocked or verification_result.status != "passed":
        events = _append_event(
            events,
            event_id=f"{normalized_run_id}-verification-blocked",
            event_type="step_blocked",
            run_id=normalized_run_id,
            sequence=len(events) + 1,
            actor=requested_actor,
            occurred_at=current_time,
            step_id=normalized_step_id,
            workflow_status="blocked",
            approval_token_id=_token_id(approval_payload),
            reason="verification_not_passed",
        )
        return _result(
            status="blocked",
            completed=False,
            reasons=[f"verification:{reason}" for reason in verification_result.reasons]
            or [f"verification_status:{verification_result.status}"],
            run_id=normalized_run_id,
            step_id=normalized_step_id,
            target_file=normalized_target,
            safe_write_result=safe_write_data,
            verification_result=verification_data,
            ledger_events=events,
        )

    events = _append_event(
        events,
        event_id=f"{normalized_run_id}-verified",
        event_type="workflow_verified",
        run_id=normalized_run_id,
        sequence=len(events) + 1,
        actor=requested_actor,
        occurred_at=current_time,
        workflow_status="completed",
        approval_token_id=_token_id(approval_payload),
        verification_reference=verification_result.matched_command_id,
    )
    events = _append_event(
        events,
        event_id=f"{normalized_run_id}-closed-out",
        event_type="workflow_closed_out",
        run_id=normalized_run_id,
        sequence=len(events) + 1,
        actor=requested_actor,
        occurred_at=current_time,
        workflow_status="completed",
        approval_token_id=_token_id(approval_payload),
        closeout={
            "safe_write_status": safe_write_result.status,
            "verification_status": verification_result.status,
            "target_file": normalized_target,
        },
    )
    return _result(
        status="completed",
        completed=True,
        reasons=[],
        run_id=normalized_run_id,
        step_id=normalized_step_id,
        target_file=normalized_target,
        safe_write_result=safe_write_data,
        verification_result=verification_data,
        ledger_events=events,
    )


def _append_event(
    events: tuple[WorkflowLedgerEvent, ...],
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
    closeout: dict[str, Any] | None = None,
) -> tuple[WorkflowLedgerEvent, ...]:
    event = _build_workflow_ledger_event(
        event_id=event_id,
        event_type=event_type,
        run_id=run_id,
        sequence=sequence,
        actor=actor,
        occurred_at=occurred_at,
        step_id=step_id,
        approval_token_id=approval_token_id,
        workflow_status=workflow_status,
        reason=reason,
        verification_reference=verification_reference,
        closeout=closeout,
        previous_event_hash=events[-1].event_hash if events else None,
    )
    preview = _preview_append_workflow_ledger_event(events, event)
    if preview.blocked:
        return events
    return preview.appended_events


def _result(
    *,
    status: str,
    completed: bool,
    reasons: list[str],
    run_id: str,
    step_id: str,
    target_file: str,
    safe_write_result: dict[str, Any],
    verification_result: dict[str, Any] | None,
    ledger_events: tuple[WorkflowLedgerEvent, ...],
) -> SafeDocsEvidenceWorkflowResult:
    return SafeDocsEvidenceWorkflowResult(
        status=status,
        completed=completed,
        blocked=not completed,
        reasons=tuple(_dedupe(reasons)),
        run_id=run_id,
        step_id=step_id,
        target_file=target_file,
        safe_write_result=safe_write_result,
        verification_result=verification_result,
        ledger_events=ledger_events,
    )


def _token_id(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    return _required_string(payload.get("token_id"))


def _required_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _dedupe(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped
