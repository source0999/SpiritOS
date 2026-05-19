from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel, Field

from source_proxy.cartographer.apply import CartographerApplyError, apply_approved_doc_proposal
from source_proxy.cartographer.clutter_proposals import ClutterCleanupError
from source_proxy.cartographer.git_approvals import (
    CartographerGitApprovalError,
    approve_git_queue_item,
)
from source_proxy.cartographer.proposal_reviews import (
    CartographerProposalReviewError,
    review_blueprint_proposal,
)
from source_proxy.cartographer.starter_blueprints import StarterBlueprintWriteError
from source_proxy.cartographer.service import (
    build_cartographer_audit_trail,
    build_cartographer_autonomy_promotion,
    build_cartographer_blueprints,
    build_cartographer_blueprint_scribe,
    build_cartographer_branch_recommendations,
    build_cartographer_change_scribe,
    build_cartographer_clutter_inventory,
    build_cartographer_clutter_proposals,
    build_cartographer_clutter_review,
    build_cartographer_codex_evidence,
    build_cartographer_commit_proposals,
    build_cartographer_components,
    build_cartographer_docs_autopilot_dry_run,
    build_cartographer_docs_autopilot_soak,
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
    build_cartographer_trust_score,
    build_cartographer_v1_closeout_handoff,
    build_cartographer_v1_closeout_audit_summary,
    build_cartographer_v1_closeout_dashboard,
    build_cartographer_v1_closeout_endpoint_index,
    build_cartographer_v1_closeout_finalization_marker,
    build_cartographer_v1_closeout_status,
    build_cartographer_v1_closeout_checklist,
    build_cartographer_v1_combined_readiness_dry_run,
    build_cartographer_v1_diagnostic_import_dry_run,
    build_cartographer_v1_evidence,
    build_cartographer_v1_evidence_gap_report,
    build_cartographer_v1_freeze_marker_proposal,
    build_cartographer_v1_freeze_marker_validation,
    build_cartographer_v1_proof_contract,
    build_cartographer_v1_proof_import_dry_run,
    build_cartographer_v1_proof_recording_proposal,
    build_cartographer_v1_proof_validation,
    build_cartographer_v1_readiness,
    apply_cartographer_clutter_proposal,
    run_cartographer_docs_autopilot_apply,
    write_cartographer_starter_blueprints,
)

router = APIRouter(prefix="/v1/cartographer")


class CartographerApplyApprovedRequest(BaseModel):
    approved: bool
    approved_by: str = Field(default="cartographer-ui", max_length=120)


class CartographerProposalReviewRequest(BaseModel):
    decision: str = Field(max_length=40)
    actor: str = Field(default="dashboard-blueprint-review", max_length=120)
    reason: str | None = Field(default=None, max_length=500)
    proposal: dict[str, Any] | None = None


class CartographerGitApprovalRequest(BaseModel):
    approved: bool
    approved_by: str = Field(default="cartographer-ui", max_length=120)


class CartographerStarterBlueprintWriteRequest(BaseModel):
    approved: bool
    approved_by: str = Field(default="cartographer-ui", max_length=120)


class CartographerClutterCleanupRequest(BaseModel):
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


@router.get("/codex-evidence")
async def cartographer_codex_evidence() -> dict[str, Any]:
    return build_cartographer_codex_evidence()


@router.get("/docs-autopilot/dry-run")
async def cartographer_docs_autopilot_dry_run() -> dict[str, Any]:
    return build_cartographer_docs_autopilot_dry_run()


@router.post("/docs-autopilot/apply")
async def cartographer_docs_autopilot_apply() -> dict[str, Any]:
    return run_cartographer_docs_autopilot_apply()


@router.get("/docs-autopilot/soak")
async def cartographer_docs_autopilot_soak() -> dict[str, Any]:
    return build_cartographer_docs_autopilot_soak()


@router.get("/trust-score")
async def cartographer_trust_score() -> dict[str, Any]:
    return build_cartographer_trust_score()


@router.get("/autonomy-promotion")
async def cartographer_autonomy_promotion() -> dict[str, Any]:
    return build_cartographer_autonomy_promotion()


@router.get("/v1-readiness")
async def cartographer_v1_readiness() -> dict[str, Any]:
    return build_cartographer_v1_readiness()


@router.get("/v1-closeout-checklist")
async def cartographer_v1_closeout_checklist() -> dict[str, Any]:
    return build_cartographer_v1_closeout_checklist()


@router.get("/v1-evidence")
async def cartographer_v1_evidence() -> dict[str, Any]:
    return build_cartographer_v1_evidence()


@router.get("/v1-proof-contract")
async def cartographer_v1_proof_contract() -> dict[str, Any]:
    return build_cartographer_v1_proof_contract()


@router.get("/v1-proof-validation")
async def cartographer_v1_proof_validation() -> dict[str, Any]:
    return build_cartographer_v1_proof_validation()


@router.get("/v1-proof-recording-proposal")
async def cartographer_v1_proof_recording_proposal() -> dict[str, Any]:
    return build_cartographer_v1_proof_recording_proposal()


@router.get("/v1-proof-import-dry-run")
async def cartographer_v1_proof_import_dry_run() -> dict[str, Any]:
    return build_cartographer_v1_proof_import_dry_run()


@router.get("/v1-diagnostic-import-dry-run")
async def cartographer_v1_diagnostic_import_dry_run() -> dict[str, Any]:
    return build_cartographer_v1_diagnostic_import_dry_run()


@router.get("/v1-combined-readiness-dry-run")
async def cartographer_v1_combined_readiness_dry_run() -> dict[str, Any]:
    return build_cartographer_v1_combined_readiness_dry_run()


@router.get("/v1-evidence-gap-report")
async def cartographer_v1_evidence_gap_report() -> dict[str, Any]:
    return build_cartographer_v1_evidence_gap_report()


@router.get("/v1-closeout-handoff")
async def cartographer_v1_closeout_handoff() -> dict[str, Any]:
    return build_cartographer_v1_closeout_handoff()


@router.get("/v1-closeout-audit-summary")
async def cartographer_v1_closeout_audit_summary() -> dict[str, Any]:
    return build_cartographer_v1_closeout_audit_summary()


@router.get("/v1-closeout-endpoints")
async def cartographer_v1_closeout_endpoints() -> dict[str, Any]:
    return build_cartographer_v1_closeout_endpoint_index()


@router.get("/v1-closeout-finalization")
async def cartographer_v1_closeout_finalization() -> dict[str, Any]:
    return build_cartographer_v1_closeout_finalization_marker()


@router.get("/v1-closeout-dashboard")
async def cartographer_v1_closeout_dashboard() -> dict[str, Any]:
    return build_cartographer_v1_closeout_dashboard()


@router.get("/v1-closeout-status")
async def cartographer_v1_closeout_status() -> dict[str, Any]:
    return build_cartographer_v1_closeout_status()


@router.get("/v1-freeze-marker-proposal")
async def cartographer_v1_freeze_marker_proposal() -> dict[str, Any]:
    return build_cartographer_v1_freeze_marker_proposal()


@router.get("/v1-freeze-marker-validation")
async def cartographer_v1_freeze_marker_validation() -> dict[str, Any]:
    return build_cartographer_v1_freeze_marker_validation()


@router.get("/branch-recommendations")
async def cartographer_branch_recommendations() -> dict[str, Any]:
    return build_cartographer_branch_recommendations()


@router.post("/branch-recommendations/{recommendation_id}/approve")
async def cartographer_approve_branch_recommendation(
    recommendation_id: str,
    request: CartographerGitApprovalRequest,
) -> dict[str, Any]:
    try:
        return approve_git_queue_item(
            kind="branch",
            item_id=recommendation_id,
            approved=request.approved,
            approved_by=request.approved_by,
        )
    except CartographerGitApprovalError as error:
        raise HTTPException(
            status_code=422,
            detail={"message": str(error), "reason_code": error.reason_code},
        ) from error


@router.get("/commit-proposals")
async def cartographer_commit_proposals() -> dict[str, Any]:
    return build_cartographer_commit_proposals()


@router.get("/clutter-inventory")
async def cartographer_clutter_inventory() -> dict[str, Any]:
    return build_cartographer_clutter_inventory()


@router.get("/clutter-proposals")
async def cartographer_clutter_proposals() -> dict[str, Any]:
    return build_cartographer_clutter_proposals()


@router.get("/clutter-review")
async def cartographer_clutter_review() -> dict[str, Any]:
    return build_cartographer_clutter_review()


@router.post("/clutter-proposals/{proposal_id}/approve")
async def cartographer_approve_clutter_proposal(
    proposal_id: str,
    request: CartographerClutterCleanupRequest,
) -> dict[str, Any]:
    try:
        return apply_cartographer_clutter_proposal(
            proposal_id=proposal_id,
            approved=request.approved,
            approved_by=request.approved_by,
        )
    except ClutterCleanupError as error:
        raise HTTPException(
            status_code=422,
            detail={"message": str(error), "reason_code": error.reason_code},
        ) from error


@router.post("/commit-proposals/{commit_proposal_id}/approve")
async def cartographer_approve_commit_proposal(
    commit_proposal_id: str,
    request: CartographerGitApprovalRequest,
) -> dict[str, Any]:
    try:
        return approve_git_queue_item(
            kind="commit",
            item_id=commit_proposal_id,
            approved=request.approved,
            approved_by=request.approved_by,
        )
    except CartographerGitApprovalError as error:
        raise HTTPException(
            status_code=422,
            detail={"message": str(error), "reason_code": error.reason_code},
        ) from error


@router.get("/push-queue")
async def cartographer_push_queue() -> dict[str, Any]:
    return build_cartographer_push_queue()


@router.post("/push-queue/{push_id}/approve")
async def cartographer_approve_push_queue_item(
    push_id: str,
    request: CartographerGitApprovalRequest,
) -> dict[str, Any]:
    try:
        return approve_git_queue_item(
            kind="push",
            item_id=push_id,
            approved=request.approved,
            approved_by=request.approved_by,
        )
    except CartographerGitApprovalError as error:
        raise HTTPException(
            status_code=422,
            detail={"message": str(error), "reason_code": error.reason_code},
        ) from error


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


@router.post("/starter-blueprints/{proposal_id}/approve")
async def cartographer_approve_starter_blueprints(
    proposal_id: str,
    request: CartographerStarterBlueprintWriteRequest,
) -> dict[str, Any]:
    try:
        return write_cartographer_starter_blueprints(
            proposal_id=proposal_id,
            approved=request.approved,
            approved_by=request.approved_by,
        )
    except StarterBlueprintWriteError as error:
        raise HTTPException(
            status_code=422,
            detail={"message": str(error), "reason_code": error.reason_code},
        ) from error


@router.post("/proposals/{proposal_id}/review")
async def cartographer_review_proposal(
    proposal_id: str,
    request: CartographerProposalReviewRequest,
) -> dict[str, Any]:
    try:
        return review_blueprint_proposal(
            proposal_id=proposal_id,
            decision=request.decision,  # type: ignore[arg-type]
            actor=request.actor,
            reason=request.reason,
            proposal_snapshot=request.proposal,
        )
    except CartographerProposalReviewError as error:
        raise HTTPException(
            status_code=422,
            detail={"message": str(error), "reason_code": error.reason_code},
        ) from error


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
