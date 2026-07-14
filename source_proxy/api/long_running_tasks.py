from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from source_proxy.approval.gate import execute_approved_action
from source_proxy.approval.campaign_authority import CampaignApprovalError, issue_coding_execution_approval, persist_coding_execution_preview, reject_coding_execution_preview, resolve_coding_execution_preview
from source_proxy.approval.operator_session import OperatorSessionError, verify_operator_approval_assertion
from source_proxy.planning.plan import ArchitectPlan, load_plan, task_spec_from_plan
from source_proxy.tasks.long_running import (
    LongRunningTaskError,
    advance_long_running_task,
    cancel_long_running_task,
    create_long_running_task,
    get_long_running_task,
    get_long_running_task_snapshot,
    list_long_running_tasks,
    record_post_apply_verification,
    assert_coding_execution_preview, record_coding_execution_approval, record_coding_execution_preview,
    reject_long_running_task_plan,
    undo_last_approved_change,
    update_long_running_task,
)

router = APIRouter(prefix="/v1/tasks")


class LongRunningTaskCreateRequest(BaseModel):
    description: str = Field(min_length=1, max_length=4000)
    steps: list[str] | None = None


class LongRunningTaskAdvanceRequest(BaseModel):
    proposed_diff: str | None = Field(default=None, max_length=200_000)
    sandbox_result: dict[str, Any] | None = None
    test_command: list[str] | None = None


class LongRunningTaskExecuteApprovedRequest(BaseModel):
    action: str = Field(min_length=1, max_length=1000)
    approval_id: str = Field(min_length=1, max_length=120)
    approved_by: str = Field(default="human", max_length=120)
    approved_diff: str = Field(min_length=1, max_length=200_000)
    selected_prompt_id: str = Field(min_length=1, max_length=160)
    context_hash: str = Field(min_length=1, max_length=128)
    target: str | None = Field(default=None, max_length=1000)
    test_command: list[str] | None = None


class LongRunningTaskApprovalPreviewRequest(BaseModel):
    action: str = Field(min_length=1, max_length=1000)
    approved_diff: str = Field(min_length=1, max_length=200_000)
    target: str = Field(min_length=1, max_length=1000)
    selected_prompt_id: str = Field(min_length=1, max_length=160)
    context_hash: str = Field(min_length=1, max_length=128)


class LongRunningTaskOperatorApprovalRequest(BaseModel):
    action: str = Field(pattern="^(approve|reject)$")
    preview_id: str = Field(min_length=1, max_length=120)
    generation: int = Field(ge=1)


class LongRunningTaskVerificationRequest(BaseModel):
    checks: list[dict[str, Any]] | None = None
    confirm_backup_audit_present: bool = False
    confirm_changed_files_reviewed: bool = False
    confirm_expected_change_present: bool = False
    confirm_no_unintended_files: bool = False
    manual_browser_check_done: bool = False
    run_code_verification: bool = False
    verification_profile: str | None = Field(default=None, max_length=120)
    run_snapshot_verification: bool = False
    browser_evidence: dict[str, Any] | None = None
    skip_reason: str | None = Field(default=None, max_length=1000)
    verification_note: str | None = Field(default=None, max_length=1000)


class LongRunningTaskSelectedDummyApplyRequest(BaseModel):
    changed_files: list[str] = Field(default_factory=list)
    reason_code: str = Field(default="selected_dummy_apply_completed", max_length=120)


class LongRunningTaskUndoRequest(BaseModel):
    confirm_undo: bool
    expected_backup_manifest: str = Field(min_length=1, max_length=2000)
    requested_by: str = Field(default="coding-ui", max_length=120)


class LongRunningTaskRejectPlanRequest(BaseModel):
    reason_code: str = Field(min_length=1, max_length=80)
    details: str = Field(default="", max_length=1000)
    rejected_by: str = Field(default="human", max_length=120)


@router.post("/long-running")
async def long_running_task_create(
    request: LongRunningTaskCreateRequest,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        return create_long_running_task(
            request.description,
            request.steps,
            run_queue_checks=False,
        )
    except LongRunningTaskError as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(error),
                "reason_code": error.reason_code,
                "task_creation_status": "blocked_before_task_id",
                "task_creation_elapsed_ms": elapsed_ms,
                "task_creation_timeout_stage": "not_applicable: validation_error",
                "task_creation_last_checkpoint": "request_validated",
                "task_creation_blocking_subsystem": "source_proxy_long_running_task_route",
            },
        ) from error
    except sqlite3.Error as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        raise HTTPException(
            status_code=503,
            detail=_task_store_unavailable_envelope(error, elapsed_ms=elapsed_ms),
        ) from error


@router.get("/long-running")
async def long_running_task_queue(
    include_completed: bool = Query(default=True),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    try:
        return list_long_running_tasks(
            include_completed=include_completed,
            limit=limit,
        )
    except sqlite3.Error as error:
        raise HTTPException(
            status_code=503,
            detail=_task_store_unavailable_envelope(error),
        ) from error


def _task_store_unavailable_envelope(
    error: sqlite3.Error,
    *,
    elapsed_ms: float | None = None,
) -> dict[str, Any]:
    message = str(error) or error.__class__.__name__
    reason_code = (
        "task_store_sqlite_locked"
        if "locked" in message.lower()
        else "task_store_unavailable"
    )
    now = "not_recorded: task_store_unavailable_before_task_id"
    return {
        "stage_id": "source_proxy.long_running_task_store",
        "subsystem": "source_proxy_backend",
        "task_id": "missing: task_store_unavailable_before_task_id",
        "selected_prompt_task_id": "missing: task_store_unavailable_before_task_id",
        "status": "blocked",
        "truth_status": "BLOCKED_SAFE",
        "safe_block": True,
        "error": "Source Proxy task store is unavailable before task creation.",
        "error_code": reason_code,
        "reason_code": reason_code,
        "human_message": "Source Proxy could not create or read the long-running task store.",
        "machine_reason": message,
        "apply_block_layer": "task_store_before_model_call",
        "task_creation_status": "blocked_before_task_id",
        "task_creation_elapsed_ms": elapsed_ms,
        "task_creation_timeout_stage": "not_applicable: task_store_unavailable",
        "task_creation_last_checkpoint": "task_store_write",
        "task_creation_blocking_subsystem": "source_proxy_long_running_task_store",
        "recommended_next_action": (
            "Inspect the long-running task SQLite store path and live process locks, "
            "then retry the selected prompt after the task route returns a task id."
        ),
        "approval_binding": {
            "approval_binding_status": "not_run: task_store_unavailable_before_task_id",
            "apply_block_layer": "task_store_before_model_call",
            "safe_block": True,
        },
        "diff_provenance": {
            "approved_diff_sha256": now,
            "applied_diff_sha256": "not_applicable: apply_blocked_before_task_id",
        },
        "anti_cheat": {
            "anti_cheat_status": "not_run",
            "anti_cheat_reasons": ["task_store_unavailable_before_model_call"],
            "grader_result_state": "not_applicable: task_store_unavailable_before_task_id",
        },
        "acceptance_gate": {
            "binary_verdict": "NO-GO",
            "phase_verifier_status": "skipped_with_reason",
            "reason": reason_code,
        },
        "verification": {
            "post_apply_verification_status": "skipped_due_to_task_store_unavailable",
        },
        "final_truth_summary": {
            "commit_safe": False,
            "raw_backend_status": "task_store_unavailable",
            "run_status": "blocked",
            "truth_status": "BLOCKED_SAFE",
            "why_not_go": "task store failed before model call and before task id creation",
        },
        "unavailable_fields": [
            {
                "field": "task_id",
                "reason": "task store failed before durable task id creation",
            },
            {
                "field": "source_proxy_apply_receipt",
                "reason": "apply did not run because task creation failed",
            },
        ],
        "diagnostic_envelope": {
            "stage_id": "source_proxy.long_running_task_store",
            "subsystem": "source_proxy_backend",
            "truth_status": "BLOCKED_SAFE",
            "safe_block": True,
            "reason_code": reason_code,
            "machine_reason": message,
            "apply_block_layer": "task_store_before_model_call",
            "task_creation_status": "blocked_before_task_id",
            "task_creation_elapsed_ms": elapsed_ms,
            "task_creation_timeout_stage": "not_applicable: task_store_unavailable",
            "task_creation_last_checkpoint": "task_store_write",
            "task_creation_blocking_subsystem": "source_proxy_long_running_task_store",
        },
    }


@router.post("/long-running/{task_id}/advance")
async def long_running_task_advance(
    task_id: str,
    request: LongRunningTaskAdvanceRequest,
) -> dict[str, Any]:
    try:
        return advance_long_running_task(
            task_id,
            proposed_diff=request.proposed_diff,
            sandbox_result=request.sandbox_result,
            test_command=request.test_command,
        )
    except LongRunningTaskError as error:
        raise HTTPException(
            status_code=404,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error


@router.post("/long-running/{task_id}/approval-preview")
async def long_running_task_approval_preview(
    task_id: str,
    request: LongRunningTaskApprovalPreviewRequest,
) -> dict[str, Any]:
    try:
        preview = persist_coding_execution_preview(
            task_id=task_id, action=request.action, approved_diff=request.approved_diff,
            target=request.target, selected_prompt_id=request.selected_prompt_id,
            context_hash=request.context_hash,
        )
        record_coding_execution_preview(task_id, preview_id=str(preview["preview_id"]), generation=int(preview["generation"]))
        return {"authority": "spiritos-approval-authority", "consumer": "coding-executor", "preview": preview}
    except CampaignApprovalError as error:
        raise HTTPException(status_code=422, detail={"reason_code": error.reason_code}) from error


@router.post("/long-running/{task_id}/operator-approval")
async def long_running_task_operator_approval(
    task_id: str,
    request: LongRunningTaskOperatorApprovalRequest,
    x_spiritos_operator_assertion: str = Header(default=""),
) -> dict[str, Any]:
    try:
        assertion = verify_operator_approval_assertion(x_spiritos_operator_assertion)
        if assertion["task_id"] != task_id or assertion["preview_id"] != request.preview_id or assertion["generation"] != request.generation or assertion["action"] != request.action:
            raise OperatorSessionError("operator_assertion_mismatch")
        assert_coding_execution_preview(task_id, preview_id=request.preview_id, generation=request.generation)
        preview = resolve_coding_execution_preview(preview_id=request.preview_id, expected_generation=request.generation)
        if request.action == "reject":
            rejected = reject_coding_execution_preview(preview_id=request.preview_id, expected_generation=request.generation)
            return {"authority": "spiritos-approval-authority", "consumer": "coding-executor", "preview": preview, "rejected": rejected}
        approval = issue_coding_execution_approval(preview_id=request.preview_id, expected_generation=request.generation)
        record_coding_execution_approval(
            task_id,
            approval_id=str(approval["approval_id"]),
            generation=int(approval["generation"]),
        )
        return {
            "authority": "spiritos-approval-authority",
            "consumer": "coding-executor",
            "operation": "coding_execution",
            "preview": preview,
            "approval": approval,
        }
    except OperatorSessionError as error:
        raise HTTPException(status_code=403, detail={"reason_code": str(error)}) from error
    except LongRunningTaskError as error:
        raise HTTPException(status_code=422, detail={"reason_code": error.reason_code}) from error
    except CampaignApprovalError as error:
        raise HTTPException(status_code=422, detail={"reason_code": error.reason_code}) from error


@router.post("/long-running/{task_id}/approval")
async def long_running_task_approval_removed(task_id: str) -> dict[str, Any]:
    raise HTTPException(status_code=410, detail={"reason_code": "approval_client_authority_removed", "task_id": task_id})


@router.post("/long-running/{task_id}/execute-approved")
async def long_running_task_execute_approved(
    task_id: str,
    request: LongRunningTaskExecuteApprovedRequest,
) -> dict[str, Any]:
    try:
        return execute_approved_action(
            task_id=task_id,
            action=request.action,
            approval_id=request.approval_id,
            approved_by=request.approved_by,
            approved_diff=request.approved_diff,
            selected_prompt_id=request.selected_prompt_id,
            context_hash=request.context_hash,
            target=request.target,
            test_command=request.test_command,
        )
    except LongRunningTaskError as error:
        detail = {"error": str(error), "reason_code": error.reason_code}
        if error.diagnostics:
            detail.update(error.diagnostics)
        raise HTTPException(
            status_code=422,
            detail=detail,
        ) from error


@router.get("/long-running/{task_id}/stream")
async def long_running_task_stream(
    task_id: str,
    interval_seconds: float = Query(default=1.0, ge=0.1, le=10.0),
    max_events: int | None = Query(default=None, ge=1, le=100),
) -> StreamingResponse:
    async def events():
        emitted = 0
        last_plan_json = ""
        emitted_role_transition_count = 0
        while True:
            try:
                payload = get_long_running_task_snapshot(task_id)
            except LongRunningTaskError as error:
                error_payload = {
                    "error": str(error),
                    "reason_code": error.reason_code,
                }
                if error.diagnostics:
                    error_payload.update(error.diagnostics)
                yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"
                return

            yield f"event: task\ndata: {json.dumps(payload)}\n\n"
            transitions = payload.get("task", {}).get("role_transitions", [])
            if isinstance(transitions, list):
                for transition in transitions[emitted_role_transition_count:]:
                    if isinstance(transition, dict):
                        yield f"event: role_transition\ndata: {json.dumps(transition)}\n\n"
                emitted_role_transition_count = len(transitions)
            try:
                plan = load_plan(task_id)
            except KeyError:
                plan = None
            if plan is not None:
                plan_json = json.dumps(_architect_plan_response_payload(plan), sort_keys=True)
                if plan_json != last_plan_json:
                    last_plan_json = plan_json
                    yield f"event: plan_updated\ndata: {plan_json}\n\n"
            emitted += 1

            status = payload["task"]["status"]
            if status in {
                "blocked",
                "blocked_approval_mismatch",
                "blocked_after_retries",
                "blocked_by_review",
                "cancelled",
                "completed",
                "coder_config_blocked",
                "failed_needs_human",
                "needs_context",
                "waiting_for_operator_browser",
                "applied_needs_verification",
                "applied_verification_failed",
                "verification_failed",
            }:
                return
            if max_events is not None and emitted >= max_events:
                return
            await asyncio.sleep(interval_seconds)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


def _plan_unavailable_envelope(task_id: str) -> dict[str, Any]:
    """Honest 200 payload when the task exists but Architect never persisted JSON (blocked, queued, etc.)."""
    try:
        envelope = get_long_running_task(task_id)
    except LongRunningTaskError:
        envelope = {}
    task = envelope.get("task") if isinstance(envelope, dict) else None
    task_dict = task if isinstance(task, dict) else {}
    return {
        "plan_available": False,
        "reason_code": "plan_not_ready",
        "task_id": task_id,
        "task_status": task_dict.get("status"),
        "architect_status": task_dict.get("architect_status"),
        "architect_reason": task_dict.get("architect_reason"),
    }


@router.get("/long-running/{task_id}/plan")
async def long_running_task_plan(task_id: str) -> dict[str, Any]:
    try:
        plan = load_plan(task_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail={"error": str(error), "reason_code": "task_not_found"},
        ) from error
    if plan is None:
        return _plan_unavailable_envelope(task_id)
    return _architect_plan_response_payload(plan)


def _architect_plan_response_payload(plan: ArchitectPlan) -> dict[str, Any]:
    payload = plan.to_dict()
    payload["task_spec"] = task_spec_from_plan(plan).to_dict()
    return payload


@router.get("/long-running/{task_id}")
async def long_running_task_status(task_id: str) -> dict[str, Any]:
    try:
        return get_long_running_task(task_id)
    except LongRunningTaskError as error:
        raise HTTPException(
            status_code=404,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error


@router.post("/long-running/{task_id}/reject-plan")
async def long_running_task_reject_plan(
    task_id: str,
    request: LongRunningTaskRejectPlanRequest,
) -> dict[str, Any]:
    try:
        return reject_long_running_task_plan(
            task_id,
            reason_code=request.reason_code,
            details=request.details,
            rejected_by=request.rejected_by,
        )
    except LongRunningTaskError as error:
        raise HTTPException(
            status_code=422,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error


@router.post("/long-running/{task_id}/verification")
async def long_running_task_verification(
    task_id: str,
    request: LongRunningTaskVerificationRequest,
) -> dict[str, Any]:
    try:
        return record_post_apply_verification(
            task_id,
            checks=request.checks,
            confirm_backup_audit_present=request.confirm_backup_audit_present,
            confirm_changed_files_reviewed=request.confirm_changed_files_reviewed,
            confirm_expected_change_present=request.confirm_expected_change_present,
            confirm_no_unintended_files=request.confirm_no_unintended_files,
            manual_browser_check_done=request.manual_browser_check_done,
            run_code_verification=request.run_code_verification,
            verification_profile=request.verification_profile,
            run_snapshot_verification=request.run_snapshot_verification,
            browser_evidence=request.browser_evidence,
            skip_reason=request.skip_reason,
            verification_note=request.verification_note,
        )
    except LongRunningTaskError as error:
        raise HTTPException(
            status_code=422,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error


@router.post("/long-running/{task_id}/verify")
async def long_running_task_verify(
    task_id: str,
    request: LongRunningTaskVerificationRequest,
) -> dict[str, Any]:
    return await long_running_task_verification(task_id, request)


@router.post("/long-running/{task_id}/undo")
async def long_running_task_undo(
    task_id: str,
    request: LongRunningTaskUndoRequest,
) -> dict[str, Any]:
    try:
        return undo_last_approved_change(
            task_id,
            confirm_undo=request.confirm_undo,
            expected_backup_manifest=request.expected_backup_manifest,
            requested_by=request.requested_by,
        )
    except LongRunningTaskError as error:
        raise HTTPException(
            status_code=422,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error


@router.post("/long-running/{task_id}/cancel")
async def long_running_task_cancel(task_id: str) -> dict[str, Any]:
    try:
        return cancel_long_running_task(task_id)
    except LongRunningTaskError as error:
        raise HTTPException(
            status_code=404,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error


@router.post("/long-running/{task_id}/selected-dummy-applied")
async def long_running_task_selected_dummy_applied(
    task_id: str,
    request: LongRunningTaskSelectedDummyApplyRequest,
) -> dict[str, Any]:
    try:
        changed = ", ".join(request.changed_files[:8])
        return update_long_running_task(
            task_id,
            status="completed",
            current_agent_role="debugger",
            architect_status="completed",
            architect_reason=request.reason_code,
            truncated_test_results=(
                f"reason_code: {request.reason_code}; changed_files={changed}"
            ),
        )
    except LongRunningTaskError as error:
        raise HTTPException(
            status_code=404,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error
