from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from source_proxy.context.inventory import build_safe_context_inventory

router = APIRouter(prefix="/v1/context")


@router.get("/inventory")
async def context_inventory() -> dict[str, Any]:
    return build_safe_context_inventory()
