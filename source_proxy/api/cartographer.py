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
    APPROVAL_TOKEN_SCHEMA_VERSION,
    build_approval_token_runtime_status,
    validate_approval_token_payload,
)
from source_proxy.cartographer.approval_token_consumption import (
    build_approval_token_consumption_status,
    preview_approval_token_consumption,
)
from source_proxy.cartographer.live_state import collect_live_repo_state
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
            "value": "cartographer-daily-driver-plan-2-phase-1",
        },
    )


class CartographerApprovalTokenConsumePreviewRequest(BaseModel):
    token: dict[str, Any] | None = None
    requested_actor: str = Field(default="cartographer-runtime", max_length=120)
    requested_scope: dict[str, str] = Field(
        default_factory=lambda: {
            "type": "phase",
            "value": "cartographer-daily-driver-plan-2-phase-2",
        },
    )
    requested_action_class: str = Field(default="", max_length=120)
    requested_files: list[str] = Field(default_factory=list, max_length=200)
    consumption_context: dict[str, Any] | None = None
    current_head: str | None = Field(default=None, max_length=80)
    kill_switch_active: bool = False


class CartographerSafeWriteRequest(BaseModel):
    token: dict[str, Any] | None = None
    requested_actor: str = Field(default="cartographer-runtime", max_length=120)
    requested_scope: dict[str, str] = Field(
        default_factory=lambda: {
            "type": "phase",
            "value": "cartographer-daily-driver-plan-3-phase-3",
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
    cwd_relative: str = Field(default=".", max_length=300)
    timeout_seconds: int = Field(default=10, ge=1, le=30)


class CartographerQueueRunNextRequest(BaseModel):
    queue_records: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    expected_trust_tier: str = Field(default="tier-1", max_length=40)
    expected_approval_token_id: str = Field(default="", max_length=160)
    kill_switch_active: bool = False
    run_selected_task: bool = False


@router.get("/status")
async def cartographer_status() -> dict[str, Any]:
    return build_cartographer_status()


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
