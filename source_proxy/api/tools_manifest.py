from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from source_proxy.self_status import build_tools_manifest

router = APIRouter(prefix="/v1/tools")


@router.get("/manifest")
async def tools_manifest() -> dict[str, Any]:
    return build_tools_manifest()
