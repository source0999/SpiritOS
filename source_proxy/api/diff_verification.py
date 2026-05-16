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
from source_proxy.tasks.long_running import (
    _workspace_root,
    generate_unified_diff_from_content,
)
import json

router = APIRouter(prefix="/v1/verification")


class DiffPreviewRequest(BaseModel):
    unified_diff: str = Field(min_length=1, max_length=MAX_DIFF_BYTES)
    test_command: list[str] | None = None
    route_type: str | None = None
    next_prompt_action: str | None = None
    task_text: str | None = None
    active_task_id: str | None = None
    task_spec: dict[str, Any] | None = None


class ManualResultPreviewRequest(BaseModel):
    payload: str = Field(min_length=1, max_length=MAX_DIFF_BYTES)
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


@router.post("/manual-result-preview")
async def manual_result_preview(request: ManualResultPreviewRequest) -> dict[str, Any]:
    try:
        architect_plan = None
        if request.active_task_id:
            try:
                architect_plan = load_plan(request.active_task_id)
            except KeyError:
                architect_plan = None
        unified_diff = _manual_result_to_unified_diff(request.payload)
        preview = preview_diff_verification(
            unified_diff,
            route_type=request.route_type,
            next_prompt_action=request.next_prompt_action,
            task_text=request.task_text,
            architect_plan=architect_plan,
            task_spec=request.task_spec,
        )
        return {
            **preview,
            "unified_diff": unified_diff,
            "manual_result_preview": True,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail={"error": str(error), "reason_code": "manual_result_invalid"},
        ) from error
    except DiffVerificationError as error:
        raise HTTPException(
            status_code=400,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error


def _manual_result_to_unified_diff(payload: str) -> str:
    raw = payload.strip()
    if raw.startswith("diff --git ") or (
        raw.startswith("--- ") and "\n+++ " in raw and "\n@@" in raw
    ):
        return raw
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].strip().lower() in {"```json", "```"} and lines[-1].strip() == "```":
            raw = "\n".join(lines[1:-1]).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start : end + 1]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"Manual result must be JSON replacement output or a unified diff: {error}") from error
    if not isinstance(parsed, dict) or parsed.get("action") != "replace_file":
        raise ValueError("Manual JSON must use action=replace_file.")
    target = parsed.get("target")
    if not isinstance(target, str) or not target.strip():
        raise ValueError("Manual JSON target must be a non-empty string.")
    if "content_lines" in parsed:
        lines = parsed.get("content_lines")
        if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
            raise ValueError("Manual JSON content_lines must be a list of strings.")
        content = "\n".join(lines)
    else:
        content = parsed.get("content")
        if not isinstance(content, str) or not content:
            raise ValueError("Manual JSON must include content_lines or content.")
    return generate_unified_diff_from_content(_workspace_root(), target, content)
