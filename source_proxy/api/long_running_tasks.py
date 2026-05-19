from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from source_proxy.approval.gate import execute_approved_action
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
    reject_long_running_task_plan,
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
    approved: bool
    approval_id: str = Field(min_length=1, max_length=120)
    approved_by: str = Field(default="human", max_length=120)
    approved_diff: str = Field(min_length=1, max_length=200_000)
    target: str | None = Field(default=None, max_length=1000)
    test_command: list[str] | None = None


class LongRunningTaskVerificationRequest(BaseModel):
    checks: list[dict[str, Any]] | None = None
    confirm_backup_audit_present: bool = False
    confirm_changed_files_reviewed: bool = False
    confirm_expected_change_present: bool = False
    confirm_no_unintended_files: bool = False
    manual_browser_check_done: bool = False
    run_code_verification: bool = False
    skip_reason: str | None = Field(default=None, max_length=1000)
    verification_note: str | None = Field(default=None, max_length=1000)


class LongRunningTaskRejectPlanRequest(BaseModel):
    reason_code: str = Field(min_length=1, max_length=80)
    details: str = Field(default="", max_length=1000)
    rejected_by: str = Field(default="human", max_length=120)


@router.post("/long-running")
async def long_running_task_create(
    request: LongRunningTaskCreateRequest,
) -> dict[str, Any]:
    try:
        return create_long_running_task(request.description, request.steps)
    except LongRunningTaskError as error:
        raise HTTPException(
            status_code=400,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error


@router.get("/long-running")
async def long_running_task_queue(
    include_completed: bool = Query(default=True),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    return list_long_running_tasks(
        include_completed=include_completed,
        limit=limit,
    )


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


@router.post("/long-running/{task_id}/execute-approved")
async def long_running_task_execute_approved(
    task_id: str,
    request: LongRunningTaskExecuteApprovedRequest,
) -> dict[str, Any]:
    if request.approved is not True:
        raise HTTPException(
            status_code=403,
            detail={"error": "approved must be true before execution"},
        )
    try:
        return execute_approved_action(
            task_id=task_id,
            action=request.action,
            approval_id=request.approval_id,
            approved_by=request.approved_by,
            approved_diff=request.approved_diff,
            target=request.target,
            test_command=request.test_command,
        )
    except LongRunningTaskError as error:
        raise HTTPException(
            status_code=422,
            detail={"error": str(error), "reason_code": error.reason_code},
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
                "cancelled",
                "completed",
                "failed_needs_human",
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


@router.post("/long-running/{task_id}/cancel")
async def long_running_task_cancel(task_id: str) -> dict[str, Any]:
    try:
        return cancel_long_running_task(task_id)
    except LongRunningTaskError as error:
        raise HTTPException(
            status_code=404,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error
