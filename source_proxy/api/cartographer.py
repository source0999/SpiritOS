from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel, Field

from source_proxy.cartographer.apply import CartographerApplyError, apply_approved_doc_proposal
from source_proxy.cartographer.service import (
    build_cartographer_audit_trail,
    build_cartographer_blueprints,
    build_cartographer_blueprint_scribe,
    build_cartographer_branch_recommendations,
    build_cartographer_change_scribe,
    build_cartographer_commit_proposals,
    build_cartographer_components,
    build_cartographer_drift,
    build_cartographer_git,
    build_cartographer_projects,
    build_cartographer_project_candidates,
    build_cartographer_project_health,
    build_cartographer_proposals,
    build_cartographer_push_queue,
    build_cartographer_reminders,
    build_cartographer_repo_map,
    build_cartographer_runbook_scribe,
    build_cartographer_status,
    build_cartographer_sub_cartographers,
)

router = APIRouter(prefix="/v1/cartographer")


class CartographerApplyApprovedRequest(BaseModel):
    approved: bool
    approved_by: str = Field(default="cartographer-ui", max_length=120)


@router.get("/status")
async def cartographer_status() -> dict[str, Any]:
    return build_cartographer_status()


@router.get("/projects")
async def cartographer_projects() -> dict[str, Any]:
    return build_cartographer_projects()


@router.get("/project-candidates")
async def cartographer_project_candidates() -> dict[str, Any]:
    return build_cartographer_project_candidates()


@router.get("/project-health")
async def cartographer_project_health() -> dict[str, Any]:
    return build_cartographer_project_health()


@router.get("/branch-recommendations")
async def cartographer_branch_recommendations() -> dict[str, Any]:
    return build_cartographer_branch_recommendations()


@router.get("/commit-proposals")
async def cartographer_commit_proposals() -> dict[str, Any]:
    return build_cartographer_commit_proposals()


@router.get("/push-queue")
async def cartographer_push_queue() -> dict[str, Any]:
    return build_cartographer_push_queue()


@router.get("/audit-trail")
async def cartographer_audit_trail() -> dict[str, Any]:
    return build_cartographer_audit_trail()


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


@router.get("/change-scribe")
async def cartographer_change_scribe() -> dict[str, Any]:
    return build_cartographer_change_scribe()


@router.get("/blueprint-scribe")
async def cartographer_blueprint_scribe() -> dict[str, Any]:
    return build_cartographer_blueprint_scribe()


@router.get("/runbook-scribe")
async def cartographer_runbook_scribe() -> dict[str, Any]:
    return build_cartographer_runbook_scribe()


@router.get("/sub-cartographers")
async def cartographer_sub_cartographers() -> dict[str, Any]:
    return build_cartographer_sub_cartographers()


@router.post("/proposals/{proposal_id}/apply-approved")
async def cartographer_apply_approved_proposal(
    proposal_id: str,
    request: CartographerApplyApprovedRequest,
) -> dict[str, Any]:
    try:
        return apply_approved_doc_proposal(
            proposal_id=proposal_id,
            approved=request.approved,
            approved_by=request.approved_by,
        )
    except CartographerApplyError as error:
        raise HTTPException(
            status_code=422,
            detail={"message": str(error), "reason_code": error.reason_code},
        ) from error
