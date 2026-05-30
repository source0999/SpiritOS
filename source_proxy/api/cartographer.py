from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
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
from source_proxy.cartographer.approval_token_runtime import (
    APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
    APPROVAL_TOKEN_SCHEMA_VERSION,
    build_approval_token_runtime_status,
    validate_approval_token_payload,
)
from source_proxy.cartographer.approval_token_consumption import (
    build_approval_token_consumption_status,
    preview_approval_token_consumption,
)
from source_proxy.cartographer.live_state import collect_live_repo_state
from source_proxy.cartographer.local_commit_gate import (
    LocalCommitProposal,
    LocalCommitVerificationResult,
    build_local_commit_proposal_model_status,
    validate_local_commit_proposal,
)
from source_proxy.cartographer.controlled_push_queue import (
    PushProposal,
    PushProposalVerification,
    build_push_proposal_only_status,
    validate_push_proposal,
)
from source_proxy.cartographer.soak_promotion import (
    DailyDriverSoakVerification,
    KillSwitchRollbackDrill,
    SupervisedSafeTaskReceipt,
    TwentyFourHourSoakSample,
    PROMOTION_TIERS,
    REQUIRED_KILL_SWITCH_DRILL_STAGES,
    build_kill_switch_rollback_drill_status,
    build_promotion_decision_status,
    build_seventy_two_hour_soak_status,
    build_ten_task_supervised_run_status,
    build_twenty_four_hour_soak_status,
    record_promotion_decision,
    validate_kill_switch_rollback_drills,
    validate_seventy_two_hour_soak,
    validate_twenty_four_hour_soak,
    validate_ten_task_supervised_run,
)
from source_proxy.cartographer.test_maintenance_proposals import (
    SafeTestMaintenanceProposal,
    build_safe_test_maintenance_proposal_status,
    validate_safe_test_maintenance_proposal,
)
from source_proxy.cartographer.docs_runbook_updates import (
    SafeDocsRunbookUpdateProposal,
    build_safe_docs_runbook_update_status,
    validate_safe_docs_runbook_update_proposal,
)
from source_proxy.cartographer.blueprint_refresh_writes import (
    SafeBlueprintRefreshWriteProposal,
    build_safe_blueprint_refresh_write_status,
    validate_safe_blueprint_refresh_write_proposal,
)
from source_proxy.cartographer.multi_worker_branch_workflow import (
    ControlledMultiWorkerBranchWorkflow,
    MultiWorkerSlot,
    build_controlled_multi_worker_branch_workflow_status,
    validate_controlled_multi_worker_branch_workflow,
)
from source_proxy.cartographer.trust_tier_decision_gate import (
    TrustTierDecisionGate,
    build_trust_tier_decision_gate_status,
    validate_trust_tier_decision_gate,
)
from source_proxy.cartographer.project_discovery import parse_project_roots
from source_proxy.cartographer.proposal_reviews import (
    CartographerProposalReviewError,
    review_blueprint_proposal,
)
from source_proxy.cartographer.safe_write import (
    build_safe_write_status,
    execute_safe_write_request,
)
from source_proxy.cartographer.safe_task_queue import (
    build_safe_task_queue_model_status,
    run_first_auto_selected_safe_task,
    select_next_safe_task,
)
from source_proxy.cartographer.verification_runner import (
    build_verification_result_receipt_summary,
    build_verification_runner_status,
    run_verification_command,
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
    build_cartographer_level_2_api_contract,
    build_cartographer_level_2_closeout,
    build_cartographer_level_2_dirty_tree,
    build_cartographer_level_2_dirty_tree_resolution,
    build_cartographer_level_2_readiness,
    build_cartographer_level_3_commit_approval_preview,
    build_cartographer_level_3_blocker_handoff,
    build_cartographer_level_3_closeout_readiness,
    build_cartographer_level_3_endpoint_index,
    build_cartographer_level_3_finalization_marker,
    build_cartographer_level_3_commit_proposals,
    build_cartographer_level_4_push_readiness_contract,
    build_cartographer_level_4_push_queue_approval_preview,
    build_cartographer_level_4_push_queue_proposal_preview,
    build_cartographer_level_6_component_ownership_assignment,
    build_cartographer_level_6_cross_project_status_board,
    build_cartographer_level_6_cross_repo_dirty_tree_classifier,
    build_cartographer_level_6_multi_project_closeout_dashboard,
    build_cartographer_level_6_project_registry_hardening,
    build_cartographer_level_7_closeout_dashboard,
    build_cartographer_level_7_disabled_by_default,
    build_cartographer_level_7_dry_run_action_packet,
    build_cartographer_level_7_exact_approval_handshake,
    build_cartographer_level_7_next_safe_action,
    build_cartographer_level_8_stop_failure_handling,
    build_cartographer_level_8_closeout_smoke,
    build_cartographer_level_9_worker_registry,
    build_cartographer_level_9_one_worker_rule,
    build_cartographer_level_9_allowed_file_conflict_checker,
    build_cartographer_level_9_branch_worktree_proposal_queue,
    build_cartographer_level_9_stale_worker_closeout_packet,
    build_cartographer_level_9_coordination_dashboard,
    build_cartographer_level_10_project_health_timeline,
    build_cartographer_level_10_closeout_packet_generator,
    build_cartographer_level_10_run_history_evidence_browser,
    build_cartographer_level_10_scout_blueprint_handoff_preview,
    build_cartographer_level_10_production_readiness_checklist,
    build_cartographer_level_10_closeout_next_roadmap_gate,
    build_cartographer_level_8_receipt_journal,
    build_cartographer_level_8_step_approval_preview,
    build_cartographer_level_8_workflow_run_card,
    build_cartographer_level_5_branch_worktree_approval_preview,
    build_cartographer_level_5_branch_recommendation_refresh,
    build_cartographer_level_5_multi_worker_safety_smoke,
    build_cartographer_level_5_parallel_work_risk_model,
    build_cartographer_level_5_worktree_recommendation_contract,
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
    block_cartographer_level_3_commit_execution,
    block_cartographer_level_4_push_execution,
    run_cartographer_docs_autopilot_apply,
    run_cartographer_level_2_docs_apply,
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


class CartographerLevel2ApplyRequest(BaseModel):
    proposal_id: str = Field(max_length=160)
    approval_id: str | None = Field(default=None, max_length=160)
    approval_actor: str | None = Field(default=None, max_length=120)


class CartographerLevel3CommitApprovalPreviewRequest(BaseModel):
    approval_id: str | None = Field(default=None, max_length=160)
    approved_by: str | None = Field(default=None, max_length=120)
    exact_file_list: list[str] = Field(default_factory=list, max_length=200)
    proposed_commit_title: str = Field(default="", max_length=240)
    proposed_commit_body: str = Field(default="", max_length=5000)
    git_head_at_creation: str | None = Field(default=None, max_length=80)
    dirty_tree_fingerprint: str | None = Field(default=None, max_length=80)
    check_results: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    approved_deleted_files: list[str] = Field(default_factory=list, max_length=200)


class CartographerLevel3CommitExecutionRequest(BaseModel):
    approval_id: str | None = Field(default=None, max_length=160)
    approved_by: str | None = Field(default=None, max_length=120)
    exact_file_list: list[str] = Field(default_factory=list, max_length=200)
    proposed_commit_title: str = Field(default="", max_length=240)
    proposed_commit_body: str = Field(default="", max_length=5000)
    git_head_at_creation: str | None = Field(default=None, max_length=80)
    dirty_tree_fingerprint: str | None = Field(default=None, max_length=80)
    check_results: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    approved_deleted_files: list[str] = Field(default_factory=list, max_length=200)


class CartographerLevel4PushQueueApprovalPreviewRequest(BaseModel):
    approval_id: str | None = Field(default=None, max_length=160)
    approved_by: str | None = Field(default=None, max_length=120)
    exact_commits: list[str] = Field(default_factory=list, max_length=100)
    remote: str | None = Field(default=None, max_length=120)
    branch: str | None = Field(default=None, max_length=240)
    upstream: str | None = Field(default=None, max_length=240)
    checks: list[dict[str, Any]] = Field(default_factory=list, max_length=50)


class CartographerLevel4PushExecutionRequest(BaseModel):
    approval_id: str | None = Field(default=None, max_length=160)
    approved_by: str | None = Field(default=None, max_length=120)


class CartographerLevel5BranchWorktreeApprovalPreviewRequest(BaseModel):
    approval_id: str | None = Field(default=None, max_length=160)
    approved_by: str | None = Field(default=None, max_length=120)
    exact_worktree_path: str | None = Field(default=None, max_length=500)
    exact_branch_name: str | None = Field(default=None, max_length=240)
    base_head: str | None = Field(default=None, max_length=80)
    owner: str | None = Field(default=None, max_length=120)
    purpose: str | None = Field(default=None, max_length=500)
    command_preview: str | None = Field(default=None, max_length=1000)


class CartographerLevel7ExactApprovalHandshakeRequest(BaseModel):
    approval_id: str | None = Field(default=None, max_length=160)
    approved_by: str | None = Field(default=None, max_length=120)
    exact_allowed_files: list[str] = Field(default_factory=list, max_length=200)
    exact_forbidden_actions: list[str] = Field(default_factory=list, max_length=200)
    exact_manual_check_commands: list[str] = Field(default_factory=list, max_length=50)
    approved_at: str | None = Field(default=None, max_length=80)


class CartographerLevel8StepApprovalPreviewRequest(BaseModel):
    approval_id: str | None = Field(default=None, max_length=160)
    approved_by: str | None = Field(default=None, max_length=120)
    exact_step_title: str = Field(default="", max_length=240)
    exact_manual_check_commands: list[str] = Field(default_factory=list, max_length=50)
    approved_at: str | None = Field(default=None, max_length=80)


class CartographerApprovalTokenValidateRequest(BaseModel):
    token: dict[str, Any] | None = None
    requested_actor: str = Field(default="cartographer-runtime", max_length=120)
    requested_scope: dict[str, str] = Field(
        default_factory=lambda: {
            "type": "phase",
            "value": "cartographer-integrated-control-plan-4-phase-4-1",
        },
    )
    requested_action_type: str = Field(default="docs_receipt_preview", max_length=120)
    requested_lane_id: str = Field(default="cartographer", max_length=80)
    requested_files: list[str] = Field(
        default_factory=lambda: ["docs/cartographer-example.md"],
        max_length=200,
    )
    current_head: str | None = Field(default=None, max_length=80)
    current_dirty_tree: dict[str, Any] | None = None
    kill_switch_active: bool = False
    requested_trust_tier: str | None = Field(default="tier-1", max_length=40)


class CartographerApprovalTokenConsumePreviewRequest(BaseModel):
    token: dict[str, Any] | None = None
    requested_actor: str = Field(default="cartographer-runtime", max_length=120)
    requested_scope: dict[str, str] = Field(
        default_factory=lambda: {
            "type": "phase",
            "value": "cartographer-integrated-control-plan-4-phase-4-1",
        },
    )
    requested_action_class: str = Field(default="", max_length=120)
    requested_lane_id: str = Field(default="cartographer", max_length=80)
    requested_files: list[str] = Field(default_factory=list, max_length=200)
    consumption_context: dict[str, Any] | None = None
    current_head: str | None = Field(default=None, max_length=80)
    current_dirty_tree: dict[str, Any] | None = None
    kill_switch_active: bool = False


class CartographerSafeWriteRequest(BaseModel):
    token: dict[str, Any] | None = None
    requested_actor: str = Field(default="cartographer-runtime", max_length=120)
    requested_scope: dict[str, str] = Field(
        default_factory=lambda: {
            "type": "phase",
            "value": "cartographer-integrated-control-plan-5-phase-5-1",
        },
    )
    target_file: str = Field(default="", max_length=500)
    content: str = Field(default="", max_length=20000)
    consumption_context: dict[str, Any] | None = None
    current_head: str | None = Field(default=None, max_length=80)
    dirty_tree_matches_expected: bool = True
    kill_switch_active: bool = False


class CartographerVerificationRunRequest(BaseModel):
    argv: list[str] = Field(default_factory=list, max_length=20)
    approved_test_files: list[str] = Field(default_factory=list, max_length=50)
    approved_file_checks: list[dict[str, str]] = Field(default_factory=list, max_length=50)
    cwd_relative: str = Field(default=".", max_length=300)
    timeout_seconds: int = Field(default=10, ge=1, le=30)


class CartographerQueueRunNextRequest(BaseModel):
    queue_records: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    expected_trust_tier: str = Field(default="tier-1", max_length=40)
    expected_approval_token_id: str = Field(default="", max_length=160)
    kill_switch_active: bool = False
    run_selected_task: bool = False


class CartographerCommitProposalRequest(BaseModel):
    proposal: dict[str, Any] | None = None
    expected_approval_token_id: str = Field(default="", max_length=160)


class CartographerPushProposalRequest(BaseModel):
    proposal: dict[str, Any] | None = None
    expected_approval_token_id: str = Field(default="", max_length=160)


@router.get("/status")
async def cartographer_status() -> dict[str, Any]:
    return {
        **build_cartographer_status(),
        "approval_token": _approval_token_status_preview(),
    }


@router.get("/live-state")
async def cartographer_live_state() -> dict[str, Any]:
    return collect_live_repo_state()


@router.get("/approval-token/validate")
async def cartographer_approval_token_validate_preview() -> dict[str, Any]:
    validation = validate_approval_token_payload(
        _self_approval_demo_token(),
        requested_actor="cartographer-runtime",
        requested_scope={
            "type": "phase",
            "value": "cartographer-integrated-control-plan-4-phase-4-1",
        },
        requested_action_type="docs_receipt_preview",
        requested_lane_id="cartographer",
        requested_files=["docs/cartographer-example.md"],
        current_head="demo-head",
        current_dirty_tree=_demo_dirty_tree(),
        requested_trust_tier="tier-1",
    )
    return {
        "runtime": build_approval_token_runtime_status(),
        "validation": validation.to_dict(),
    }


@router.post("/approval-token/validate")
async def cartographer_approval_token_validate(
    request: CartographerApprovalTokenValidateRequest,
) -> dict[str, Any]:
    validation = validate_approval_token_payload(
        request.token,
        requested_actor=request.requested_actor,
        requested_scope=request.requested_scope,
        requested_action_type=request.requested_action_type,
        requested_lane_id=request.requested_lane_id,
        requested_files=request.requested_files,
        current_head=request.current_head,
        current_dirty_tree=request.current_dirty_tree,
        kill_switch_active=request.kill_switch_active,
        requested_trust_tier=request.requested_trust_tier,
    )
    return {
        "runtime": build_approval_token_runtime_status(),
        "validation": validation.to_dict(),
    }


@router.get("/approval-token/consume-preview")
async def cartographer_approval_token_consume_preview_demo() -> dict[str, Any]:
    preview = preview_approval_token_consumption(
        _self_approval_demo_token(
            scope_value="cartographer-integrated-control-plan-4-phase-4-1",
        ),
        requested_actor="cartographer-runtime",
        requested_scope={
            "type": "phase",
            "value": "cartographer-integrated-control-plan-4-phase-4-1",
        },
        requested_action_class="docs_receipt_preview",
        requested_lane_id="cartographer",
        requested_files=["docs/cartographer-example.md"],
        consumption_context=_demo_consumption_context(),
        current_head="demo-head",
        current_dirty_tree=_demo_dirty_tree(),
        kill_switch_active=True,
    )
    return {
        "runtime": build_approval_token_consumption_status(),
        "preview": preview.to_dict(),
    }


@router.post("/approval-token/consume-preview")
async def cartographer_approval_token_consume_preview(
    request: CartographerApprovalTokenConsumePreviewRequest,
) -> dict[str, Any]:
    preview = preview_approval_token_consumption(
        request.token,
        requested_actor=request.requested_actor,
        requested_scope=request.requested_scope,
        requested_action_class=request.requested_action_class,
        requested_lane_id=request.requested_lane_id,
        requested_files=request.requested_files,
        consumption_context=request.consumption_context,
        current_head=request.current_head,
        current_dirty_tree=request.current_dirty_tree,
        kill_switch_active=request.kill_switch_active,
    )
    return {
        "runtime": build_approval_token_consumption_status(),
        "preview": preview.to_dict(),
    }


@router.get("/safe-write")
async def cartographer_safe_write_status() -> dict[str, Any]:
    return build_safe_write_status()


@router.post("/safe-write")
async def cartographer_safe_write(
    request: CartographerSafeWriteRequest,
) -> dict[str, Any]:
    workspace_root = _safe_write_workspace_root()
    if workspace_root is None:
        return {
            "status": "blocked",
            "written": False,
            "blocked": True,
            "reasons": ["missing_configured_workspace_root"],
            "target_file": request.target_file,
            "bytes_written": 0,
            "safe_write": build_safe_write_status(),
        }
    result = execute_safe_write_request(
        request.token,
        requested_actor=request.requested_actor,
        requested_scope=request.requested_scope,
        target_file=request.target_file,
        content=request.content,
        consumption_context=request.consumption_context,
        workspace_root=workspace_root,
        current_head=request.current_head,
        dirty_tree_matches_expected=request.dirty_tree_matches_expected,
        kill_switch_active=request.kill_switch_active,
    )
    return {
        "safe_write": build_safe_write_status(),
        "result": result.to_dict(),
    }


@router.get("/verification/run")
async def cartographer_verification_run_status() -> dict[str, Any]:
    return build_verification_runner_status()


@router.post("/verification/run")
async def cartographer_verification_run(
    request: CartographerVerificationRunRequest,
) -> dict[str, Any]:
    workspace_root = _safe_write_workspace_root()
    if workspace_root is None:
        return {
            "status": "blocked",
            "executed": False,
            "blocked": True,
            "reasons": ["missing_configured_workspace_root"],
            "verification": build_verification_runner_status(),
        }
    result = run_verification_command(
        request.argv,
        workspace_root=workspace_root,
        approved_test_files=request.approved_test_files,
        approved_file_checks=request.approved_file_checks,
        cwd_relative=request.cwd_relative,
        timeout_seconds=request.timeout_seconds,
    )
    return {
        "verification": build_verification_runner_status(),
        "result": result.to_dict(),
        "receipt_summary": build_verification_result_receipt_summary(result),
    }


@router.get("/queue/run-next")
async def cartographer_queue_run_next_status() -> dict[str, Any]:
    return {
        "queue": build_safe_task_queue_model_status(),
        "run_next": {
            "status": "available",
            "method": "POST",
            "selection_available": True,
            "execution_available": False,
            "durable_storage_available": False,
            "queue_worker_available": False,
            "background_loop_available": False,
            "run_selected_task_available": False,
            "receipt_available": True,
            "safe_next_action": "POST queue_records with an exact approval token to select at most one eligible task as data only.",
        },
    }


@router.post("/queue/run-next")
async def cartographer_queue_run_next(
    request: CartographerQueueRunNextRequest,
) -> dict[str, Any]:
    if request.run_selected_task:
        run = run_first_auto_selected_safe_task(
            request.queue_records,
            expected_trust_tier=request.expected_trust_tier,
            expected_approval_token_id=request.expected_approval_token_id,
            kill_switch_active=request.kill_switch_active,
        )
        return {
            "queue": build_safe_task_queue_model_status(),
            "run": run.to_dict(),
        }
    selection = select_next_safe_task(
        request.queue_records,
        expected_trust_tier=request.expected_trust_tier,
        expected_approval_token_id=request.expected_approval_token_id,
        kill_switch_active=request.kill_switch_active,
    )
    return {
        "queue": build_safe_task_queue_model_status(),
        "selection": selection.to_dict(),
    }


@router.get("/commit/proposal")
async def cartographer_commit_proposal_preview() -> dict[str, Any]:
    proposal = _demo_local_commit_proposal()
    validation = validate_local_commit_proposal(
        proposal,
        expected_approval_token_id=proposal.approval_token_id,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    return {
        "commit_proposal": build_local_commit_proposal_model_status(),
        "proposal": proposal.to_dict(),
        "validation": validation.to_dict(),
        "api_preview_only": True,
        "staging_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "command_authority_granted": False,
        "git_mutation_authority_granted": False,
    }


@router.post("/commit/proposal")
async def cartographer_commit_proposal_validate(
    request: CartographerCommitProposalRequest,
) -> dict[str, Any]:
    validation = validate_local_commit_proposal(
        request.proposal,
        expected_approval_token_id=request.expected_approval_token_id,
    )
    return {
        "commit_proposal": build_local_commit_proposal_model_status(),
        "validation": validation.to_dict(),
        "api_preview_only": True,
        "staging_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "command_authority_granted": False,
        "git_mutation_authority_granted": False,
    }


@router.get("/push/proposal")
async def cartographer_push_proposal_preview() -> dict[str, Any]:
    proposal = _demo_push_proposal()
    validation = validate_push_proposal(
        proposal,
        expected_approval_token_id=proposal.approval_token_id,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    return {
        "push_proposal": build_push_proposal_only_status(),
        "proposal": proposal.to_dict(),
        "validation": validation.to_dict(),
        "api_preview_only": True,
        "push_enabled": False,
        "force_push_enabled": False,
        "tag_push_enabled": False,
        "merge_enabled": False,
        "command_authority_granted": False,
        "api_mutation_available": False,
        "durable_storage_available": False,
    }


@router.post("/push/proposal")
async def cartographer_push_proposal_validate(
    request: CartographerPushProposalRequest,
) -> dict[str, Any]:
    validation = validate_push_proposal(
        request.proposal,
        expected_approval_token_id=request.expected_approval_token_id,
    )
    return {
        "push_proposal": build_push_proposal_only_status(),
        "validation": validation.to_dict(),
        "api_preview_only": True,
        "push_enabled": False,
        "force_push_enabled": False,
        "tag_push_enabled": False,
        "merge_enabled": False,
        "command_authority_granted": False,
        "api_mutation_available": False,
        "durable_storage_available": False,
    }


@router.get("/soak/status")
async def cartographer_soak_status_preview() -> dict[str, Any]:
    receipts = _demo_supervised_task_receipts()
    samples = _demo_twenty_four_hour_soak_samples()
    seventy_two_hour_samples = _demo_seventy_two_hour_soak_samples()
    kill_switch_drills = _demo_kill_switch_rollback_drills()
    validation = validate_ten_task_supervised_run(
        receipts,
        expected_trust_tier="tier-1",
        expected_approval_token_prefix="approval-token-plan-10-1-",
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    twenty_four_hour_validation = validate_twenty_four_hour_soak(
        samples,
        requested_duration_hours=24,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    seventy_two_hour_validation = validate_seventy_two_hour_soak(
        seventy_two_hour_samples,
        requested_duration_hours=72,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    kill_switch_drill_validation = validate_kill_switch_rollback_drills(
        kill_switch_drills,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    promotion_decision = record_promotion_decision(
        tier="tier-1",
        allowed_actions=PROMOTION_TIERS["tier-1"],
        decided_by="Britton",
        ten_task_validation=validation,
        twenty_four_hour_validation=twenty_four_hour_validation,
        seventy_two_hour_validation=seventy_two_hour_validation,
        kill_switch_drill_validation=kill_switch_drill_validation,
        authority_change_requested=False,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    return {
        "soak_status": build_ten_task_supervised_run_status(),
        "twenty_four_hour_soak_status": build_twenty_four_hour_soak_status(),
        "seventy_two_hour_soak_status": build_seventy_two_hour_soak_status(),
        "kill_switch_drill_status": build_kill_switch_rollback_drill_status(),
        "promotion_decision_status": build_promotion_decision_status(),
        "receipts": [receipt.to_dict() for receipt in receipts],
        "twenty_four_hour_samples": [sample.to_dict() for sample in samples],
        "seventy_two_hour_samples": [sample.to_dict() for sample in seventy_two_hour_samples],
        "kill_switch_drills": [drill.to_dict() for drill in kill_switch_drills],
        "validation": validation.to_dict(),
        "twenty_four_hour_validation": twenty_four_hour_validation.to_dict(),
        "seventy_two_hour_validation": seventy_two_hour_validation.to_dict(),
        "kill_switch_drill_validation": kill_switch_drill_validation.to_dict(),
        "promotion_decision": promotion_decision.to_dict(),
        "api_preview_only": True,
        "background_loop_enabled": False,
        "queue_execution_enabled": False,
        "task_execution_enabled": False,
        "command_execution_enabled": False,
        "safe_write_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
    }


@router.get("/expansion/test-maintenance/proposals")
async def cartographer_safe_test_maintenance_proposals_preview() -> dict[str, Any]:
    proposal = _demo_safe_test_maintenance_proposal()
    validation = validate_safe_test_maintenance_proposal(
        proposal,
        expected_trust_tier="tier-1",
        expected_approval_token_id=proposal.approval_token_id,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    return {
        "test_maintenance_status": build_safe_test_maintenance_proposal_status(),
        "proposal": proposal.to_dict(),
        "validation": validation.to_dict(),
        "api_preview_only": True,
        "source_write_enabled": False,
        "test_write_enabled": False,
        "command_execution_enabled": False,
        "test_execution_enabled": False,
        "queue_execution_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
    }


@router.get("/expansion/docs-runbook/proposals")
async def cartographer_safe_docs_runbook_update_proposals_preview() -> dict[str, Any]:
    proposal = _demo_safe_docs_runbook_update_proposal()
    validation = validate_safe_docs_runbook_update_proposal(
        proposal,
        expected_trust_tier="tier-1",
        expected_approval_token_id=proposal.approval_token_id,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    return {
        "docs_runbook_status": build_safe_docs_runbook_update_status(),
        "proposal": proposal.to_dict(),
        "validation": validation.to_dict(),
        "api_preview_only": True,
        "docs_write_enabled": False,
        "runbook_write_enabled": False,
        "source_write_enabled": False,
        "test_write_enabled": False,
        "command_execution_enabled": False,
        "queue_execution_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
    }


@router.get("/expansion/blueprint-refresh/proposals")
async def cartographer_safe_blueprint_refresh_write_proposals_preview() -> dict[str, Any]:
    proposal = _demo_safe_blueprint_refresh_write_proposal()
    validation = validate_safe_blueprint_refresh_write_proposal(
        proposal,
        expected_trust_tier="tier-1",
        expected_approval_token_id=proposal.approval_token_id,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    return {
        "blueprint_refresh_status": build_safe_blueprint_refresh_write_status(),
        "proposal": proposal.to_dict(),
        "validation": validation.to_dict(),
        "api_preview_only": True,
        "blueprint_write_enabled": False,
        "docs_write_enabled": False,
        "source_write_enabled": False,
        "test_write_enabled": False,
        "command_execution_enabled": False,
        "queue_execution_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
    }


@router.get("/expansion/multi-worker-branch/workflow")
async def cartographer_controlled_multi_worker_branch_workflow_preview() -> dict[str, Any]:
    workflow = _demo_controlled_multi_worker_branch_workflow()
    validation = validate_controlled_multi_worker_branch_workflow(
        workflow,
        expected_trust_tier="tier-1",
        expected_approval_token_id=workflow.approval_token_id,
        expected_branch_worktree_approval_id=workflow.branch_worktree_approval_id,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    return {
        "multi_worker_branch_status": build_controlled_multi_worker_branch_workflow_status(),
        "workflow": workflow.to_dict(),
        "validation": validation.to_dict(),
        "api_preview_only": True,
        "worker_spawn_enabled": False,
        "task_execution_enabled": False,
        "queue_execution_enabled": False,
        "branch_creation_enabled": False,
        "worktree_creation_enabled": False,
        "checkout_enabled": False,
        "merge_enabled": False,
        "command_execution_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
    }


@router.get("/expansion/trust-tier/decision")
async def cartographer_trust_tier_decision_gate_preview() -> dict[str, Any]:
    decision = _demo_trust_tier_decision_gate()
    validation = validate_trust_tier_decision_gate(
        decision,
        expected_approval_token_id=decision.approval_token_id,
        now=datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
    )
    return {
        "trust_tier_gate_status": build_trust_tier_decision_gate_status(),
        "decision": decision.to_dict(),
        "validation": validation.to_dict(),
        "api_preview_only": True,
        "expansion_enabled": False,
        "trust_tier_promotion_recorded": False,
        "approval_token_minted": False,
        "self_approval_allowed": False,
        "command_execution_enabled": False,
        "queue_execution_enabled": False,
        "task_execution_enabled": False,
        "safe_write_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "branch_enabled": False,
        "worktree_enabled": False,
        "durable_storage_written": False,
    }


def _safe_write_workspace_root() -> Path | None:
    configured, blocked = parse_project_roots()
    if blocked or len(configured) != 1:
        return None
    return Path(configured[0].path)


def _demo_local_commit_proposal() -> LocalCommitProposal:
    return LocalCommitProposal(
        proposal_id="commit-proposal-plan-9-1-demo",
        exact_file_list=("docs/cartographer-live-receipts/example.md",),
        exact_commit_message="Add Cartographer receipt evidence",
        verification_result=LocalCommitVerificationResult(
            status="passed",
            checks=("pytest:local_commit_gate", "git diff --check"),
            checked_at="2026-05-23T12:00:00Z",
        ).to_dict(),
        rollback_command="git revert abc1234",
        expected_head="abc1234",
        branch="main",
        dirty_tree_expectation="exact_files_only",
        blocked_files=("source_proxy/api/cartographer.py",),
        status="proposed",
        task_ids=("task-plan-9-1",),
        receipt_paths=("docs/cartographer-live-receipts/example.md",),
        approval_token_id="approval-token-plan-9-phase-1",
        created_at="2026-05-23T12:00:00Z",
    )


def _demo_push_proposal() -> PushProposal:
    return PushProposal(
        proposal_id="push-proposal-plan-9-2-demo",
        remote="origin",
        branch="cartographer/plan-9-proposal",
        upstream="origin/cartographer/plan-9-proposal",
        ahead_count=1,
        behind_count=0,
        local_commits=("a" * 40,),
        commit_sha="a" * 40,
        clean_status="clean",
        exact_file_lineage=("docs/cartographer-live-receipts/example.md",),
        verification=PushProposalVerification(
            status="passed",
            checks=("pytest:controlled_push_queue", "git diff --check"),
            checked_at="2026-05-23T12:00:00Z",
        ).to_dict(),
        verification_receipts=("docs/cartographer-live-receipts/example.md",),
        rollback_guidance="Revert the exact commit locally, then request a new reviewed push proposal.",
        approval_token_id="approval-token-plan-9-phase-2",
        risk="low",
        created_at="2026-05-23T12:00:00Z",
    )


def _demo_supervised_task_receipts() -> tuple[SupervisedSafeTaskReceipt, ...]:
    return tuple(
        SupervisedSafeTaskReceipt(
            task_id=f"task-{index:02d}",
            action_class=("docs", "evidence", "receipt")[index % 3],
            trust_tier="tier-1",
            approval_token_id=f"approval-token-plan-10-1-{index:02d}",
            exact_files=(f"docs/cartographer-live-receipts/task-{index:02d}.md",),
            receipt_path=f"docs/cartographer-live-receipts/task-{index:02d}.md",
            status="passed",
            verification=DailyDriverSoakVerification(
                status="passed",
                checks=("manual_supervision", "receipt_review", "git diff --check"),
                checked_at="2026-05-23T12:00:00Z",
            ).to_dict(),
            rollback_guidance="No automated rollback. Review receipt and rerun supervised task if needed.",
            kill_switch_checked=True,
            operator_supervised=True,
            started_at="2026-05-23T11:50:00Z",
            completed_at="2026-05-23T12:00:00Z",
        )
        for index in range(10)
    )


def _demo_twenty_four_hour_soak_samples() -> tuple[TwentyFourHourSoakSample, ...]:
    return tuple(
        TwentyFourHourSoakSample(
            sample_id=f"sample-{hour:02d}",
            hour=hour,
            bounded_invocation_count=hour // 12,
            queue_depth=0,
            blocked_task_count=0,
            receipt_count=10,
            kill_switch_checked=True,
            hidden_loop_detected=False,
            hidden_mutation_detected=False,
            head_changed=False,
            dirty_worktree_explained=True,
            protected_lane_mutation_detected=False,
            manual_intervention_required=False,
            sampled_at=f"2026-05-23T{hour // 2:02d}:00:00Z",
        )
        for hour in (0, 12, 24)
    )


def _demo_seventy_two_hour_soak_samples() -> tuple[TwentyFourHourSoakSample, ...]:
    return tuple(
        TwentyFourHourSoakSample(
            sample_id=f"sample-{hour:02d}",
            hour=hour,
            bounded_invocation_count=hour // 24,
            queue_depth=0,
            blocked_task_count=0,
            receipt_count=10,
            kill_switch_checked=True,
            hidden_loop_detected=False,
            hidden_mutation_detected=False,
            head_changed=False,
            dirty_worktree_explained=True,
            protected_lane_mutation_detected=False,
            manual_intervention_required=False,
            sampled_at=f"2026-05-{20 + hour // 24:02d}T00:00:00Z",
            drift_status="clear",
            protected_lane_status="clear",
            queue_status="healthy",
        )
        for hour in (0, 24, 48, 72)
    )


def _demo_kill_switch_rollback_drills() -> tuple[KillSwitchRollbackDrill, ...]:
    return tuple(
        KillSwitchRollbackDrill(
            drill_id=f"drill-{stage.replace('_', '-')}",
            stage=stage,
            kill_switch_engaged=True,
            action_blocked=True,
            queue_execution_blocked=True,
            task_execution_blocked=True,
            command_execution_blocked=True,
            write_blocked=True,
            commit_blocked=True,
            push_blocked=True,
            rollback_guidance="No automated rollback was executed; preserve receipt and restore only with operator approval.",
            receipt_path=f"docs/cartographer-live-receipts/kill-switch-{stage}.md",
            verified_at="2026-05-23T12:00:00Z",
        )
        for stage in REQUIRED_KILL_SWITCH_DRILL_STAGES
    )


def _demo_safe_test_maintenance_proposal() -> SafeTestMaintenanceProposal:
    return SafeTestMaintenanceProposal(
        proposal_id="test-maintenance-plan-11-1-2-demo",
        maintenance_class="test_name_clarification",
        target_test_file="source_proxy/tests/test_cartographer_daily_driver_soak.py",
        exact_change_summary="Rename a focused test for clarity without changing assertions.",
        rationale="Improve reviewability of an existing safe soak validation test.",
        verification_plan=("manual_review_only", "run exact focused test after separate approval"),
        trust_tier="tier-1",
        approval_token_id="approval-token-plan-11-phase-11-1-test-maintenance",
        status="proposed",
        created_at="2026-05-23T12:00:00Z",
    )


def _demo_safe_docs_runbook_update_proposal() -> SafeDocsRunbookUpdateProposal:
    return SafeDocsRunbookUpdateProposal(
        proposal_id="docs-runbook-plan-11-1-1-demo",
        update_class="operator_runbook_clarification",
        target_paths=("docs/cartographer-operator-runbook.md",),
        receipt_path="docs/cartographer-live-receipts/docs-runbook-plan-11-1-1.md",
        exact_change_summary="Clarify a manual operator runbook step without applying the edit.",
        rationale="Improve operator reviewability inside docs/runbook scope only.",
        rollback_guidance="No write has occurred; discard proposal if not approved.",
        verification_plan=("manual_review_only", "run exact docs/runbook check after separate approval"),
        trust_tier="tier-1",
        approval_token_id="approval-token-plan-11-phase-11-1-docs",
        status="proposed",
        created_at="2026-05-23T12:00:00Z",
    )


def _demo_safe_blueprint_refresh_write_proposal() -> SafeBlueprintRefreshWriteProposal:
    return SafeBlueprintRefreshWriteProposal(
        proposal_id="blueprint-refresh-plan-11-1-1-demo",
        refresh_class="project_state_refresh",
        target_blueprint_paths=("_blueprints/current/project_state.md",),
        receipt_path="docs/cartographer-live-receipts/blueprint-refresh-plan-11-1-1.md",
        exact_change_summary="Refresh the project-state blueprint after proposal-only proof without applying the edit.",
        source_evidence_paths=("docs/cartographer-daily-driver-autonomy-plan-11-workflow-compliance-audit.md",),
        rollback_guidance="No write has occurred; discard proposal if not approved.",
        verification_plan=("manual_review_only", "run exact blueprint validation after separate approval"),
        trust_tier="tier-1",
        approval_token_id="approval-token-plan-11-phase-11-1-blueprint",
        status="proposed",
        created_at="2026-05-23T12:00:00Z",
    )


def _demo_controlled_multi_worker_branch_workflow() -> ControlledMultiWorkerBranchWorkflow:
    return ControlledMultiWorkerBranchWorkflow(
        workflow_id="multi-worker-branch-plan-9-2-1-demo",
        worker_slots=(
            MultiWorkerSlot(worker_id="worker-alpha", task_id="task-docs-a", file_zone=("docs/a.md",)),
            MultiWorkerSlot(worker_id="worker-beta", task_id="task-docs-b", file_zone=("docs/b.md",)),
        ),
        proposed_branches=("cartographer/worker-alpha", "cartographer/worker-beta"),
        proposed_worktrees=(".cartographer/worktrees/worker-alpha", ".cartographer/worktrees/worker-beta"),
        branch_worktree_approval_id="branch-worktree-approval-plan-9-phase-9-2",
        coordination_receipt_path="docs/cartographer-live-receipts/multi-worker-branch-plan-9-2-1.md",
        rollback_guidance="No branch or worktree has been created; discard workflow design if not approved.",
        verification_plan=("manual_review_only", "confirm exact worker/file zones before separate approval"),
        trust_tier="tier-1",
        approval_token_id="approval-token-plan-9-phase-9-2-branch-worktree",
        status="proposed",
        created_at="2026-05-23T12:00:00Z",
    )


def _demo_trust_tier_decision_gate() -> TrustTierDecisionGate:
    return TrustTierDecisionGate(
        decision_id="trust-tier-plan-11-2-2-demo",
        requested_expansion_class="controlled_multi_worker_branch_workflow",
        current_trust_tier="tier-1",
        requested_trust_tier="tier-2",
        decision_outcome="advance",
        evidence_paths=("docs/cartographer-plan-11-trust-tier-proof.md",),
        soak_evidence_hours=72,
        rollback_proof_recorded=True,
        false_positive_count=0,
        false_negative_count=0,
        stop_event_count=0,
        operator_review_required=True,
        operator_review_recorded=True,
        approval_token_id="approval-token-plan-11-phase-11-2-trust-tier",
        status="proposed",
        created_at="2026-05-23T12:00:00Z",
    )


def _self_approval_demo_token(
    scope_value: str = "cartographer-integrated-control-plan-4-phase-4-1",
) -> dict[str, Any]:
    human_approved_at = datetime.now(UTC) - timedelta(minutes=5)
    expires_at = datetime.now(UTC) + timedelta(minutes=55)
    return {
        "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
        "token_id": "validation-preview-self-approval",
        "run_id": "approval-preview-run",
        "operator_id": "cartographer-runtime",
        "approver_id": "cartographer-runtime",
        "action_type": "docs_receipt_preview",
        "lane_id": "cartographer",
        "scope": {
            "type": "phase",
            "value": scope_value,
        },
        "exact_allowed_files": ["docs/cartographer-example.md"],
        "exact_forbidden_files": ["source_proxy/cartographer/apply.py"],
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        "rollback_instructions": "Manual rollback only; API preview cannot roll back.",
        "verification_instructions": "Run focused approval-token API tests.",
        "expected_head": "demo-head",
        "expected_dirty_tree": _demo_dirty_tree(),
        "kill_switch_state": APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
        "trust_tier": "tier-1",
        "single_action": True,
        "issued_by_human": True,
        "human_approved_at": human_approved_at.isoformat().replace("+00:00", "Z"),
    }


def _approval_token_status_preview() -> dict[str, Any]:
    requested_scope = {
        "type": "phase",
        "value": "cartographer-integrated-control-plan-4-phase-4-1",
    }
    requested_files = ["docs/cartographer-example.md"]
    validation = validate_approval_token_payload(
        None,
        requested_actor="cartographer-runtime",
        requested_scope=requested_scope,
        requested_action_type="docs_receipt_preview",
        requested_lane_id="cartographer",
        requested_files=requested_files,
        current_head="demo-head",
        current_dirty_tree=_demo_dirty_tree(),
        requested_trust_tier="tier-1",
    )
    consumption = preview_approval_token_consumption(
        None,
        requested_actor="cartographer-runtime",
        requested_scope=requested_scope,
        requested_action_class="docs_receipt_preview",
        requested_lane_id="cartographer",
        requested_files=requested_files,
        consumption_context=None,
        current_head="demo-head",
        current_dirty_tree=_demo_dirty_tree(),
    )
    return {
        "status": "no-go",
        "summary": "Approval token is missing; validation is preview-only and grants no authority.",
        "runtime": build_approval_token_runtime_status(),
        "consumption_runtime": build_approval_token_consumption_status(),
        "validation": validation.to_dict(),
        "consumption": consumption.to_dict(),
        "authority_granted": False,
        "write_authority_granted": False,
        "command_authority_granted": False,
        "workflow_authority_granted": False,
        "queue_authority_granted": False,
        "git_authority_granted": False,
        "validation_only": True,
        "preview_only": True,
        "no_go_default": True,
    }


def _demo_dirty_tree() -> dict[str, Any]:
    return {
        "fingerprint": "demo-clean-plan-4",
        "dirty_files": [],
        "expected_dirty": False,
    }


def _demo_consumption_context() -> dict[str, Any]:
    return {
        "action_class": "docs_receipt_preview",
        "trust_tier": "tier-1",
        "requested_trust_tier": "tier-1",
        "exact_allowed_files": ["docs/cartographer-example.md"],
        "exact_forbidden_files": ["source_proxy/cartographer/apply.py"],
        "expected_head": "demo-head",
        "expected_dirty_tree": _demo_dirty_tree(),
        "rollback": "Manual review only; no runtime write is available.",
        "verification": "Run focused approval-token consumption tests.",
    }


@router.get("/live-state")
async def cartographer_live_state() -> dict[str, Any]:
    return collect_live_repo_state()


@router.get("/approval-token/validate")
async def cartographer_approval_token_validate_preview() -> dict[str, Any]:
    validation = validate_approval_token_payload(
        _self_approval_demo_token(),
        requested_actor="cartographer-runtime",
        requested_scope={
            "type": "phase",
            "value": "cartographer-daily-driver-plan-2-phase-1",
        },
    )
    return {
        "runtime": build_approval_token_runtime_status(),
        "validation": validation.to_dict(),
    }


@router.post("/approval-token/validate")
async def cartographer_approval_token_validate(
    request: CartographerApprovalTokenValidateRequest,
) -> dict[str, Any]:
    validation = validate_approval_token_payload(
        request.token,
        requested_actor=request.requested_actor,
        requested_scope=request.requested_scope,
    )
    return {
        "runtime": build_approval_token_runtime_status(),
        "validation": validation.to_dict(),
    }


@router.get("/approval-token/consume-preview")
async def cartographer_approval_token_consume_preview_demo() -> dict[str, Any]:
    preview = preview_approval_token_consumption(
        _self_approval_demo_token(
            scope_value="cartographer-daily-driver-plan-2-phase-2",
        ),
        requested_actor="cartographer-runtime",
        requested_scope={
            "type": "phase",
            "value": "cartographer-daily-driver-plan-2-phase-2",
        },
        requested_action_class="docs_receipt_preview",
        requested_files=["docs/cartographer-example.md"],
        consumption_context=_demo_consumption_context(),
        current_head="demo-head",
        kill_switch_active=True,
    )
    return {
        "runtime": build_approval_token_consumption_status(),
        "preview": preview.to_dict(),
    }


@router.post("/approval-token/consume-preview")
async def cartographer_approval_token_consume_preview(
    request: CartographerApprovalTokenConsumePreviewRequest,
) -> dict[str, Any]:
    preview = preview_approval_token_consumption(
        request.token,
        requested_actor=request.requested_actor,
        requested_scope=request.requested_scope,
        requested_action_class=request.requested_action_class,
        requested_files=request.requested_files,
        consumption_context=request.consumption_context,
        current_head=request.current_head,
        kill_switch_active=request.kill_switch_active,
    )
    return {
        "runtime": build_approval_token_consumption_status(),
        "preview": preview.to_dict(),
    }


@router.get("/safe-write")
async def cartographer_safe_write_status() -> dict[str, Any]:
    return build_safe_write_status()


@router.post("/safe-write")
async def cartographer_safe_write(
    request: CartographerSafeWriteRequest,
) -> dict[str, Any]:
    workspace_root = _safe_write_workspace_root()
    if workspace_root is None:
        return {
            "status": "blocked",
            "written": False,
            "blocked": True,
            "reasons": ["missing_configured_workspace_root"],
            "target_file": request.target_file,
            "bytes_written": 0,
            "safe_write": build_safe_write_status(),
        }
    result = execute_safe_write_request(
        request.token,
        requested_actor=request.requested_actor,
        requested_scope=request.requested_scope,
        target_file=request.target_file,
        content=request.content,
        consumption_context=request.consumption_context,
        workspace_root=workspace_root,
        current_head=request.current_head,
        dirty_tree_matches_expected=request.dirty_tree_matches_expected,
        kill_switch_active=request.kill_switch_active,
    )
    return {
        "safe_write": build_safe_write_status(),
        "result": result.to_dict(),
    }


@router.get("/verification/run")
async def cartographer_verification_run_status() -> dict[str, Any]:
    return build_verification_runner_status()


@router.post("/verification/run")
async def cartographer_verification_run(
    request: CartographerVerificationRunRequest,
) -> dict[str, Any]:
    workspace_root = _safe_write_workspace_root()
    if workspace_root is None:
        return {
            "status": "blocked",
            "executed": False,
            "blocked": True,
            "reasons": ["missing_configured_workspace_root"],
            "verification": build_verification_runner_status(),
        }
    result = run_verification_command(
        request.argv,
        workspace_root=workspace_root,
        approved_test_files=request.approved_test_files,
        cwd_relative=request.cwd_relative,
        timeout_seconds=request.timeout_seconds,
    )
    return {
        "verification": build_verification_runner_status(),
        "result": result.to_dict(),
    }


@router.get("/queue/run-next")
async def cartographer_queue_run_next_status() -> dict[str, Any]:
    return {
        "queue": build_safe_task_queue_model_status(),
        "run_next": {
            "status": "available",
            "method": "POST",
            "selection_available": True,
            "execution_available": False,
            "durable_storage_available": False,
            "queue_worker_available": False,
            "background_loop_available": False,
            "run_selected_task_available": True,
            "receipt_available": True,
            "safe_next_action": "POST queue_records with an exact approval token to select or run at most one eligible task.",
        },
    }


@router.post("/queue/run-next")
async def cartographer_queue_run_next(
    request: CartographerQueueRunNextRequest,
) -> dict[str, Any]:
    if request.run_selected_task:
        run = run_first_auto_selected_safe_task(
            request.queue_records,
            expected_trust_tier=request.expected_trust_tier,
            expected_approval_token_id=request.expected_approval_token_id,
            kill_switch_active=request.kill_switch_active,
        )
        return {
            "queue": build_safe_task_queue_model_status(),
            "run": run.to_dict(),
        }
    selection = select_next_safe_task(
        request.queue_records,
        expected_trust_tier=request.expected_trust_tier,
        expected_approval_token_id=request.expected_approval_token_id,
        kill_switch_active=request.kill_switch_active,
    )
    return {
        "queue": build_safe_task_queue_model_status(),
        "selection": selection.to_dict(),
    }


def _safe_write_workspace_root() -> Path | None:
    configured, blocked = parse_project_roots()
    if blocked or len(configured) != 1:
        return None
    return Path(configured[0].path)


def _self_approval_demo_token(
    scope_value: str = "cartographer-daily-driver-plan-2-phase-1",
) -> dict[str, Any]:
    issued_at = datetime.now(UTC) - timedelta(minutes=5)
    expires_at = datetime.now(UTC) + timedelta(minutes=55)
    return {
        "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
        "token_id": "validation-preview-self-approval",
        "issued_at": issued_at.isoformat().replace("+00:00", "Z"),
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        "approved_by": "cartographer-runtime",
        "approved_for_actor": "cartographer-runtime",
        "scope": {
            "type": "phase",
            "value": scope_value,
        },
        "reason": "Demonstrate fail-closed self-approval rejection.",
    }


def _demo_consumption_context() -> dict[str, Any]:
    return {
        "action_class": "docs_receipt_preview",
        "trust_tier": "tier-1",
        "requested_trust_tier": "tier-1",
        "exact_allowed_files": ["docs/cartographer-example.md"],
        "exact_forbidden_files": ["source_proxy/cartographer/apply.py"],
        "expected_head": "demo-head",
        "rollback": "Manual review only; no runtime write is available.",
        "verification": "Run focused approval-token consumption tests.",
    }


@router.get("/projects")
async def cartographer_projects() -> dict[str, Any]:
    return build_cartographer_projects()


@router.get("/project-candidates")
async def cartographer_project_candidates() -> dict[str, Any]:
    return build_cartographer_project_candidates()


@router.get("/level-6-project-registry")
async def cartographer_level_6_project_registry() -> dict[str, Any]:
    return build_cartographer_level_6_project_registry_hardening()


@router.get("/level-6-cross-project-status-board")
async def cartographer_level_6_cross_project_status_board() -> dict[str, Any]:
    return build_cartographer_level_6_cross_project_status_board()


@router.get("/level-6-component-ownership")
async def cartographer_level_6_component_ownership() -> dict[str, Any]:
    return build_cartographer_level_6_component_ownership_assignment()


@router.get("/level-6-cross-repo-dirty-tree")
async def cartographer_level_6_cross_repo_dirty_tree() -> dict[str, Any]:
    return build_cartographer_level_6_cross_repo_dirty_tree_classifier()


@router.get("/level-6-multi-project-closeout")
async def cartographer_level_6_multi_project_closeout() -> dict[str, Any]:
    return build_cartographer_level_6_multi_project_closeout_dashboard()


@router.get("/level-7-disabled-by-default")
async def cartographer_level_7_disabled_by_default() -> dict[str, Any]:
    return build_cartographer_level_7_disabled_by_default()


@router.get("/level-7-next-safe-action")
async def cartographer_level_7_next_safe_action() -> dict[str, Any]:
    return build_cartographer_level_7_next_safe_action()


@router.get("/level-7-dry-run-action-packet")
async def cartographer_level_7_dry_run_action_packet() -> dict[str, Any]:
    return build_cartographer_level_7_dry_run_action_packet()


@router.post("/level-7-dry-run-action-packet/{packet_id}/approval-preview")
async def cartographer_level_7_exact_approval_handshake(
    packet_id: str,
    request: CartographerLevel7ExactApprovalHandshakeRequest,
) -> dict[str, Any]:
    return build_cartographer_level_7_exact_approval_handshake(
        packet_id=packet_id,
        approval_id=request.approval_id,
        approved_by=request.approved_by,
        exact_allowed_files=request.exact_allowed_files,
        exact_forbidden_actions=request.exact_forbidden_actions,
        exact_manual_check_commands=request.exact_manual_check_commands,
        approved_at=request.approved_at,
    )


@router.get("/level-7-closeout-dashboard")
async def cartographer_level_7_closeout_dashboard() -> dict[str, Any]:
    return build_cartographer_level_7_closeout_dashboard()


@router.get("/level-8-workflow-run-card")
async def cartographer_level_8_workflow_run_card() -> dict[str, Any]:
    return build_cartographer_level_8_workflow_run_card()


@router.post("/level-8-workflow-run-card/{workflow_id}/steps/{step_id}/approval-preview")
async def cartographer_level_8_step_approval_preview(
    workflow_id: str,
    step_id: str,
    request: CartographerLevel8StepApprovalPreviewRequest,
) -> dict[str, Any]:
    return build_cartographer_level_8_step_approval_preview(
        workflow_id=workflow_id,
        step_id=step_id,
        approval_id=request.approval_id,
        approved_by=request.approved_by,
        exact_step_title=request.exact_step_title,
        exact_manual_check_commands=request.exact_manual_check_commands,
        approved_at=request.approved_at,
    )


@router.get("/level-8-receipt-journal")
async def cartographer_level_8_receipt_journal() -> dict[str, Any]:
    return build_cartographer_level_8_receipt_journal()


@router.get("/level-8-stop-failure-handling")
async def cartographer_level_8_stop_failure_handling() -> dict[str, Any]:
    return build_cartographer_level_8_stop_failure_handling()


@router.get("/level-8-closeout-smoke")
async def cartographer_level_8_closeout_smoke() -> dict[str, Any]:
    return build_cartographer_level_8_closeout_smoke()


@router.get("/level-9-worker-registry")
async def cartographer_level_9_worker_registry() -> dict[str, Any]:
    return build_cartographer_level_9_worker_registry()


@router.get("/level-9-one-worker-rule")
async def cartographer_level_9_one_worker_rule() -> dict[str, Any]:
    return build_cartographer_level_9_one_worker_rule()


@router.get("/level-9-allowed-file-conflicts")
async def cartographer_level_9_allowed_file_conflicts() -> dict[str, Any]:
    return build_cartographer_level_9_allowed_file_conflict_checker()


@router.get("/level-9-branch-worktree-proposals")
async def cartographer_level_9_branch_worktree_proposals() -> dict[str, Any]:
    return build_cartographer_level_9_branch_worktree_proposal_queue()


@router.get("/level-9-stale-worker-closeout")
async def cartographer_level_9_stale_worker_closeout() -> dict[str, Any]:
    return build_cartographer_level_9_stale_worker_closeout_packet()


@router.get("/level-9-coordination-dashboard")
async def cartographer_level_9_coordination_dashboard() -> dict[str, Any]:
    return build_cartographer_level_9_coordination_dashboard()


@router.get("/level-10-project-health-timeline")
async def cartographer_level_10_project_health_timeline() -> dict[str, Any]:
    return build_cartographer_level_10_project_health_timeline()


@router.get("/level-10-closeout-packets")
async def cartographer_level_10_closeout_packets() -> dict[str, Any]:
    return build_cartographer_level_10_closeout_packet_generator()


@router.get("/level-10-run-history-evidence")
async def cartographer_level_10_run_history_evidence() -> dict[str, Any]:
    return build_cartographer_level_10_run_history_evidence_browser()


@router.get("/level-10-scout-blueprint-handoff-preview")
async def cartographer_level_10_scout_blueprint_handoff_preview() -> dict[str, Any]:
    return build_cartographer_level_10_scout_blueprint_handoff_preview()


@router.get("/level-10-production-readiness-checklist")
async def cartographer_level_10_production_readiness_checklist() -> dict[str, Any]:
    return build_cartographer_level_10_production_readiness_checklist()


@router.get("/level-10-closeout-next-roadmap-gate")
async def cartographer_level_10_closeout_next_roadmap_gate() -> dict[str, Any]:
    return build_cartographer_level_10_closeout_next_roadmap_gate()


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


@router.post("/docs-autopilot/level-2/apply")
async def cartographer_level_2_docs_apply(
    request: CartographerLevel2ApplyRequest,
) -> dict[str, Any]:
    return run_cartographer_level_2_docs_apply(
        proposal_id=request.proposal_id,
        approval_id=request.approval_id,
        approval_actor=request.approval_actor,
    )


@router.get("/docs-autopilot/soak")
async def cartographer_docs_autopilot_soak() -> dict[str, Any]:
    return build_cartographer_docs_autopilot_soak()


@router.get("/trust-score")
async def cartographer_trust_score() -> dict[str, Any]:
    return build_cartographer_trust_score()


@router.get("/autonomy-promotion")
async def cartographer_autonomy_promotion() -> dict[str, Any]:
    return build_cartographer_autonomy_promotion()


@router.get("/level-2-readiness")
async def cartographer_level_2_readiness() -> dict[str, Any]:
    return build_cartographer_level_2_readiness()


@router.get("/level-2-dirty-tree")
async def cartographer_level_2_dirty_tree() -> dict[str, Any]:
    return build_cartographer_level_2_dirty_tree()


@router.get("/level-2-dirty-tree-resolution")
async def cartographer_level_2_dirty_tree_resolution() -> dict[str, Any]:
    return build_cartographer_level_2_dirty_tree_resolution()


@router.get("/level-2-api-contract")
async def cartographer_level_2_api_contract() -> dict[str, Any]:
    return build_cartographer_level_2_api_contract()


@router.get("/level-2-closeout")
async def cartographer_level_2_closeout() -> dict[str, Any]:
    return build_cartographer_level_2_closeout()


@router.get("/level-3-commit-proposals")
async def cartographer_level_3_commit_proposals() -> dict[str, Any]:
    return build_cartographer_level_3_commit_proposals()


@router.post("/level-3-commit-proposals/{proposal_id}/approval-preview")
async def cartographer_level_3_commit_approval_preview(
    proposal_id: str,
    request: CartographerLevel3CommitApprovalPreviewRequest,
) -> dict[str, Any]:
    return build_cartographer_level_3_commit_approval_preview(
        proposal_id=proposal_id,
        approval_id=request.approval_id,
        approved_by=request.approved_by,
        exact_file_list=request.exact_file_list,
        proposed_commit_title=request.proposed_commit_title,
        proposed_commit_body=request.proposed_commit_body,
        git_head_at_creation=request.git_head_at_creation,
        dirty_tree_fingerprint=request.dirty_tree_fingerprint,
        check_results=request.check_results,
        approved_deleted_files=request.approved_deleted_files,
    )


@router.post("/level-3-commit-proposals/{proposal_id}/commit")
async def cartographer_level_3_commit_execution_block(
    proposal_id: str,
    request: CartographerLevel3CommitExecutionRequest,
) -> dict[str, Any]:
    return block_cartographer_level_3_commit_execution(
        proposal_id=proposal_id,
        approval_id=request.approval_id,
        approved_by=request.approved_by,
        exact_file_list=request.exact_file_list,
        proposed_commit_title=request.proposed_commit_title,
        proposed_commit_body=request.proposed_commit_body,
        git_head_at_creation=request.git_head_at_creation,
        dirty_tree_fingerprint=request.dirty_tree_fingerprint,
        check_results=request.check_results,
        approved_deleted_files=request.approved_deleted_files,
    )


@router.get("/level-3-closeout-readiness")
async def cartographer_level_3_closeout_readiness() -> dict[str, Any]:
    return build_cartographer_level_3_closeout_readiness()


@router.get("/level-3-endpoints")
async def cartographer_level_3_endpoints() -> dict[str, Any]:
    return build_cartographer_level_3_endpoint_index()


@router.get("/level-3-finalization")
async def cartographer_level_3_finalization() -> dict[str, Any]:
    return build_cartographer_level_3_finalization_marker()


@router.get("/level-3-blocker-handoff")
async def cartographer_level_3_blocker_handoff() -> dict[str, Any]:
    return build_cartographer_level_3_blocker_handoff()


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


@router.get("/level-5-parallel-work-risk")
async def cartographer_level_5_parallel_work_risk() -> dict[str, Any]:
    return build_cartographer_level_5_parallel_work_risk_model()


@router.get("/level-5-branch-recommendations")
async def cartographer_level_5_branch_recommendations() -> dict[str, Any]:
    return build_cartographer_level_5_branch_recommendation_refresh()


@router.get("/level-5-worktree-recommendations")
async def cartographer_level_5_worktree_recommendations() -> dict[str, Any]:
    return build_cartographer_level_5_worktree_recommendation_contract()


@router.post("/level-5-worktree-recommendations/{recommendation_id}/approval-preview")
async def cartographer_level_5_branch_worktree_approval_preview(
    recommendation_id: str,
    request: CartographerLevel5BranchWorktreeApprovalPreviewRequest,
) -> dict[str, Any]:
    return build_cartographer_level_5_branch_worktree_approval_preview(
        recommendation_id=recommendation_id,
        approval_id=request.approval_id,
        approved_by=request.approved_by,
        exact_worktree_path=request.exact_worktree_path,
        exact_branch_name=request.exact_branch_name,
        base_head=request.base_head,
        owner=request.owner,
        purpose=request.purpose,
        command_preview=request.command_preview,
    )


@router.get("/level-5-multi-worker-safety-smoke")
async def cartographer_level_5_multi_worker_safety_smoke() -> dict[str, Any]:
    return build_cartographer_level_5_multi_worker_safety_smoke()


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


@router.get("/level-4-push-readiness")
async def cartographer_level_4_push_readiness() -> dict[str, Any]:
    return build_cartographer_level_4_push_readiness_contract()


@router.get("/level-4-push-queue-proposals")
async def cartographer_level_4_push_queue_proposals() -> dict[str, Any]:
    return build_cartographer_level_4_push_queue_proposal_preview()


@router.post("/level-4-push-queue-proposals/{proposal_id}/approval-preview")
async def cartographer_level_4_push_queue_approval_preview(
    proposal_id: str,
    request: CartographerLevel4PushQueueApprovalPreviewRequest,
) -> dict[str, Any]:
    return build_cartographer_level_4_push_queue_approval_preview(
        proposal_id=proposal_id,
        approval_id=request.approval_id,
        approved_by=request.approved_by,
        exact_commits=request.exact_commits,
        remote=request.remote,
        branch=request.branch,
        upstream=request.upstream,
        checks=request.checks,
    )


@router.post("/level-4-push-queue-proposals/{proposal_id}/push")
async def cartographer_level_4_push_execution_hard_block(
    proposal_id: str,
    request: CartographerLevel4PushExecutionRequest,
) -> dict[str, Any]:
    return block_cartographer_level_4_push_execution(
        proposal_id=proposal_id,
        approval_id=request.approval_id,
        approved_by=request.approved_by,
    )


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
