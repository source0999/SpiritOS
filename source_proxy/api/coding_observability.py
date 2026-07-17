from __future__ import annotations

from fastapi import APIRouter, HTTPException

from source_proxy.tasks.long_running import LongRunningTaskError
from source_proxy.coding.observability import build_coding_shell_observability


router = APIRouter(prefix="/v1/coding")


@router.get("/tasks/{task_id}/observability")
async def coding_task_observability(task_id: str) -> dict[str, object]:
    try:
        return build_coding_shell_observability(task_id)
    except LongRunningTaskError as error:
        raise HTTPException(status_code=404, detail=error.reason_code) from error
