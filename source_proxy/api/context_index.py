from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from source_proxy.self_status import build_context_index_manifest

router = APIRouter(prefix="/v1/context")


@router.get("/index")
async def context_index() -> dict[str, Any]:
    return build_context_index_manifest()
