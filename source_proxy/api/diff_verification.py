from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from source_proxy.verification.diff import (
    MAX_DIFF_BYTES,
    DiffVerificationError,
    preview_diff_verification,
)
from source_proxy.planning.plan import load_plan

router = APIRouter(prefix="/v1/verification")


class DiffPreviewRequest(BaseModel):
    unified_diff: str = Field(min_length=1, max_length=MAX_DIFF_BYTES)
    test_command: list[str] | None = None
    route_type: str | None = None
    next_prompt_action: str | None = None
    task_text: str | None = None
    active_task_id: str | None = None
    task_spec: dict[str, Any] | None = None


@router.post("/diff-preview")
async def diff_preview(request: DiffPreviewRequest) -> dict[str, Any]:
    try:
        architect_plan = None
        if request.active_task_id:
            try:
                architect_plan = load_plan(request.active_task_id)
            except KeyError:
                architect_plan = None
        return preview_diff_verification(
            request.unified_diff,
            test_command=request.test_command,
            route_type=request.route_type,
            next_prompt_action=request.next_prompt_action,
            task_text=request.task_text,
            architect_plan=architect_plan,
            task_spec=request.task_spec,
        )
    except DiffVerificationError as error:
        raise HTTPException(
            status_code=400,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error
