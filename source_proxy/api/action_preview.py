from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from source_proxy.self_status import build_action_preview

router = APIRouter(prefix="/v1/actions")


class ActionPreviewRequest(BaseModel):
    action: str = Field(min_length=1)
    target: str | None = None
    route_type: str | None = None


@router.post("/preview")
async def action_preview(request: ActionPreviewRequest) -> dict[str, Any]:
    return build_action_preview(
        action=request.action,
        target=request.target,
        route_type=request.route_type,
    )
