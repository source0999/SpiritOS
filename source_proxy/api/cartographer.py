from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from source_proxy.cartographer.service import (
    build_cartographer_blueprints,
    build_cartographer_components,
    build_cartographer_drift,
    build_cartographer_git,
    build_cartographer_projects,
    build_cartographer_proposals,
    build_cartographer_reminders,
    build_cartographer_repo_map,
    build_cartographer_status,
)

router = APIRouter(prefix="/v1/cartographer")


@router.get("/status")
async def cartographer_status() -> dict[str, Any]:
    return build_cartographer_status()


@router.get("/projects")
async def cartographer_projects() -> dict[str, Any]:
    return build_cartographer_projects()


@router.get("/blueprints")
async def cartographer_blueprints() -> dict[str, Any]:
    return build_cartographer_blueprints()


@router.get("/components")
async def cartographer_components() -> dict[str, Any]:
    return build_cartographer_components()


@router.get("/repo-map")
async def cartographer_repo_map() -> dict[str, Any]:
    return build_cartographer_repo_map()


@router.get("/git")
async def cartographer_git() -> dict[str, Any]:
    return build_cartographer_git()


@router.get("/drift")
async def cartographer_drift() -> dict[str, Any]:
    return build_cartographer_drift()


@router.get("/reminders")
async def cartographer_reminders() -> dict[str, Any]:
    return build_cartographer_reminders()


@router.get("/proposals")
async def cartographer_proposals() -> dict[str, Any]:
    return build_cartographer_proposals()
