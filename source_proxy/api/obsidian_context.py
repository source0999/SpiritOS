from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from source_proxy.context.obsidian import query_obsidian_context

router = APIRouter(prefix="/v1/context")


class ObsidianContextQueryRequest(BaseModel):
    task: str = Field(min_length=1)


@router.post("/obsidian/query")
async def obsidian_context_query(request: ObsidianContextQueryRequest) -> dict[str, Any]:
    return query_obsidian_context(request.task)
