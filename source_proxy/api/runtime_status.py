from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from source_proxy.decision.runtime_health import build_runtime_health_status

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, Any]:
    return build_runtime_health_status()


@router.get("/v1/health")
async def v1_health() -> dict[str, Any]:
    return build_runtime_health_status()


@router.get("/v1/runtime/status")
async def runtime_status() -> dict[str, Any]:
    return build_runtime_health_status()
