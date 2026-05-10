from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from source_proxy.self_status import build_self_status_manifest

router = APIRouter(prefix="/v1/self")


@router.get("/status")
async def self_status() -> dict[str, Any]:
    return build_self_status_manifest()
