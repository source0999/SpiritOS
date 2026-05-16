from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from source_proxy.context.workspace_tools import (
    MAX_LIST_ENTRIES,
    MAX_READ_BYTES,
    WorkspaceToolError,
    list_workspace_path,
    read_workspace_excerpt,
)

router = APIRouter(prefix="/v1/workspace")


class WorkspaceListRequest(BaseModel):
    path: str | None = None
    max_entries: int = Field(default=MAX_LIST_ENTRIES, ge=1, le=MAX_LIST_ENTRIES)


class WorkspaceReadRequest(BaseModel):
    path: str = Field(min_length=1)
    max_bytes: int = Field(default=MAX_READ_BYTES, ge=1, le=MAX_READ_BYTES)


@router.post("/list")
async def workspace_list(request: WorkspaceListRequest) -> dict[str, Any]:
    try:
        return list_workspace_path(request.path, max_entries=request.max_entries)
    except WorkspaceToolError as error:
        raise HTTPException(
            status_code=400,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error


@router.post("/read")
async def workspace_read(request: WorkspaceReadRequest) -> dict[str, Any]:
    try:
        return read_workspace_excerpt(request.path, max_bytes=request.max_bytes)
    except WorkspaceToolError as error:
        raise HTTPException(
            status_code=400,
            detail={"error": str(error), "reason_code": error.reason_code},
        ) from error
