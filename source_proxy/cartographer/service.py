from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from source_proxy.cartographer.audit_trail import build_audit_trail
from source_proxy.cartographer.autopilot_config import docs_autopilot_config
from source_proxy.cartographer.autopilot_apply import run_docs_autopilot_apply
from source_proxy.cartographer.autopilot_dry_run import build_docs_autopilot_dry_run_proposals
from source_proxy.cartographer.autopilot_soak import build_docs_autopilot_soak_report
from source_proxy.cartographer.autonomy_promotion import build_autonomy_promotion_recommendation
from source_proxy.cartographer.blueprint_registry import count_blueprint_documents, list_blueprints
from source_proxy.cartographer.blueprint_scribe import draft_blueprint_updates
from source_proxy.cartographer.branch_recommendations import recommend_branches
from source_proxy.cartographer.change_scribe import summarize_changes
from source_proxy.cartographer.clutter_inventory import build_clutter_inventory
from source_proxy.cartographer.clutter_proposals import (
    apply_approved_low_risk_deletion_proposal,
    build_low_risk_deletion_proposals,
)
from source_proxy.cartographer.codex_evidence import build_codex_evidence_rollup
from source_proxy.cartographer.commit_proposals import (
    build_commit_proposals,
    build_level_3_commit_approval_preview,
    build_level_3_commit_execution_block,
    build_level_3_commit_proposal_preview,
)
from source_proxy.cartographer.component_mapper import build_component_map
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.git_status import (
    read_git_status,
    read_git_status_for_project,
    read_git_statuses,
)
from source_proxy.cartographer.level_2_apply import run_level_2_docs_apply
from source_proxy.cartographer.level_2_readiness import (
    build_level_2_api_contract_review_packet,
    build_level_2_closeout_packet,
    build_level_2_dirty_tree_classification,
    build_level_2_dirty_tree_resolution_packet,
    build_level_2_readiness,
)
from source_proxy.cartographer.models import CartographerStatus, to_jsonable
from source_proxy.cartographer.project_discovery import (
    blocked_project_roots,
    discover_project_candidates,
    configured_project_roots,
    discover_projects,
)
from source_proxy.cartographer.project_health import build_project_health
from source_proxy.cartographer.proposals import (
    list_proposals,
    pending_proposal_count,
    proposal_visibility_summary,
    proposal_states,
)
from source_proxy.cartographer.push_queue import build_push_queue
from source_proxy.cartographer.reminders import build_reminders
from source_proxy.cartographer.repo_map import build_repo_maps
from source_proxy.cartographer.runbook_scribe import suggest_runbook_updates
from source_proxy.cartographer.safety import cartographer_safety_manifest
from source_proxy.cartographer.starter_blueprints import write_approved_starter_blueprints
from source_proxy.cartographer.sub_cartographers import (
    route_control_plane_situations,
    route_sub_cartographers,
    sub_cartographer_outputs,
    sub_cartographer_roles,
)
from source_proxy.cartographer.trust_score import build_trust_score
from source_proxy.cartographer.v1_evidence import (
    build_v1_diagnostic_import_dry_run,
    build_v1_combined_readiness_dry_run,
    build_v1_evidence_inventory,
    build_v1_evidence_gap_report,
    build_v1_freeze_marker_validation,
    build_v1_proof_artifact_contract,
    build_v1_proof_artifact_validation,
    build_v1_proof_import_dry_run,
    build_v1_proof_recording_proposal,
)
from source_proxy.cartographer.v1_readiness import build_v1_closeout_checklist, build_v1_readiness


def build_cartographer_status() -> dict[str, Any]:
    blueprint_count = count_blueprint_documents()
    status = CartographerStatus(
        status="observing",
        write_actions_enabled=False,
        configured_roots=configured_project_roots(),
        blocked_roots=blocked_project_roots(),
        projects=discover_projects(),
        blueprint_count=blueprint_count,
        pending_proposals=pending_proposal_count(),
    )
    payload = to_jsonable(status)
    autopilot = docs_autopilot_config()
    payload.update(
        {
            "docs_autopilot_enabled": autopilot["docs_autopilot_enabled"],
            "docs_autopilot_daily_cap": autopilot["docs_autopilot_daily_cap"],
            "autopilot_kill_switch": autopilot["autopilot_kill_switch"],
            "autopilot_action_available": autopilot["autopilot_action_available"],
            "autopilot": autopilot,
        }
    )
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_projects() -> dict[str, Any]:
    candidates = discover_project_candidates()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "configured_roots": to_jsonable(configured_project_roots()),
        "blocked_roots": to_jsonable(blocked_project_roots()),
        "projects": to_jsonable(discover_projects()),
        "project_candidates": to_jsonable(candidates),
        "candidate_count": len(candidates),
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_project_candidates() -> dict[str, Any]:
    candidates = discover_project_candidates()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "candidates": to_jsonable(candidates),
        "candidate_count": len(candidates),
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_project_health() -> dict[str, Any]:
    projects = build_project_health()
    codex_evidence = build_codex_evidence_rollup()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "projects": to_jsonable(projects),
        "project_count": len(projects),
        "filters": sorted({filter_name for project in projects for filter_name in project.filters}),
        "codex_evidence": to_jsonable(codex_evidence),
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_codex_evidence() -> dict[str, Any]:
    codex_evidence = build_codex_evidence_rollup()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "codex_evidence": to_jsonable(codex_evidence),
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_docs_autopilot_dry_run() -> dict[str, Any]:
    payload = build_docs_autopilot_dry_run_proposals()
    payload["safety_manifest"] = cartographer_safety_manifest()
    return payload


def run_cartographer_docs_autopilot_apply() -> dict[str, Any]:
    return run_docs_autopilot_apply()


def run_cartographer_level_2_docs_apply(
    *,
    proposal_id: str,
    approval_id: str | None = None,
    approval_actor: str | None = None,
) -> dict[str, Any]:
    payload = run_level_2_docs_apply(
        proposal_id=proposal_id,
        approval_id=approval_id,
        approval_actor=approval_actor,
    )
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_docs_autopilot_soak() -> dict[str, Any]:
    return build_docs_autopilot_soak_report()


def build_cartographer_trust_score() -> dict[str, Any]:
    payload = build_trust_score()
    payload["signals"] = to_jsonable(payload["signals"])
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_autonomy_promotion() -> dict[str, Any]:
    payload = build_autonomy_promotion_recommendation()
    payload["level_2_readiness"] = build_level_2_readiness()
    payload["level_2_recommendation"] = payload["level_2_readiness"]["label"]
    payload["level_2_authority_granted"] = False
    payload["level_2_enablement_allowed"] = bool(payload["level_2_readiness"]["docs_apply_enabled"])
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_level_2_readiness() -> dict[str, Any]:
    payload = build_level_2_readiness()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_level_2_dirty_tree() -> dict[str, Any]:
    payload = build_level_2_dirty_tree_classification()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_level_2_dirty_tree_resolution() -> dict[str, Any]:
    payload = build_level_2_dirty_tree_resolution_packet()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_level_2_api_contract() -> dict[str, Any]:
    payload = build_level_2_api_contract_review_packet()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_level_2_closeout() -> dict[str, Any]:
    payload = build_level_2_closeout_packet()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_readiness() -> dict[str, Any]:
    payload = build_v1_readiness()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_closeout_checklist() -> dict[str, Any]:
    payload = build_v1_closeout_checklist()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_evidence() -> dict[str, Any]:
    payload = build_v1_evidence_inventory()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_proof_contract() -> dict[str, Any]:
    payload = build_v1_proof_artifact_contract()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_proof_validation() -> dict[str, Any]:
    payload = build_v1_proof_artifact_validation()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_proof_recording_proposal() -> dict[str, Any]:
    payload = build_v1_proof_recording_proposal()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_proof_import_dry_run() -> dict[str, Any]:
    payload = build_v1_proof_import_dry_run()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_diagnostic_import_dry_run() -> dict[str, Any]:
    payload = build_v1_diagnostic_import_dry_run()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_combined_readiness_dry_run() -> dict[str, Any]:
    payload = build_v1_combined_readiness_dry_run()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_evidence_gap_report() -> dict[str, Any]:
    payload = build_v1_evidence_gap_report()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_freeze_marker_validation() -> dict[str, Any]:
    payload = build_v1_freeze_marker_validation()
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_v1_closeout_status() -> dict[str, Any]:
    readiness = build_v1_readiness()
    handoff = build_cartographer_v1_closeout_handoff()
    freeze_proposal = build_cartographer_v1_freeze_marker_proposal()
    freeze_validation = build_v1_freeze_marker_validation()
    checklist = build_v1_closeout_checklist()
    next_blocked_item = checklist["next_blocked_item"]
    freeze_marker_valid = freeze_validation["validation_status"] == "valid"
    closeout_status = (
        "ready_with_valid_freeze_marker"
        if readiness["v1_ready"] and freeze_marker_valid
        else "ready_missing_freeze_marker"
        if readiness["v1_ready"]
        else "blocked_missing_evidence"
    )
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "rollup_mode": "read_only_closeout_status",
        "v1_ready": readiness["v1_ready"],
        "readiness": readiness["readiness"],
        "blocker_count": readiness["blocker_count"],
        "closeout_status": closeout_status,
        "freeze_marker_status": freeze_validation["validation_status"],
        "freeze_marker_valid": freeze_marker_valid,
        "freeze_marker_path": freeze_validation["marker_path"],
        "freeze_marker_proposal_ready": freeze_proposal["proposal_only"],
        "current_missing_count": handoff["current_missing_count"],
        "remaining_after_dry_run": handoff["remaining_after_dry_run"],
        "readiness_would_be_ready": handoff["readiness_would_be_ready"],
        "authority_would_remain_locked": True,
        "passing_tests_grant_authority": False,
        "next_blocked_item": next_blocked_item,
        "summary": (
            "Cartographer v1 closeout is blocked by missing real evidence."
            if not readiness["v1_ready"]
            else "Cartographer v1 evidence is ready; freeze marker validation remains separate."
            if not freeze_marker_valid
            else "Cartographer v1 evidence and freeze marker validate as ready."
        ),
        "source_endpoints": [
            "/v1/cartographer/v1-readiness",
            "/v1/cartographer/v1-closeout-handoff",
            "/v1/cartographer/v1-freeze-marker-proposal",
            "/v1/cartographer/v1-freeze-marker-validation",
        ],
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_v1_closeout_dashboard() -> dict[str, Any]:
    closeout = build_cartographer_v1_closeout_status()
    docs_path = "docs/cartographer-v1-evidence-artifacts.md"
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "dashboard_mode": "read_only_v1_closeout_surface",
        "docs_path": docs_path,
        "docs_label": "Cartographer v1 evidence artifact contract",
        "primary_status": closeout["closeout_status"],
        "primary_label": _v1_closeout_dashboard_label(closeout["closeout_status"]),
        "v1_ready": closeout["v1_ready"],
        "readiness": closeout["readiness"],
        "blocker_count": closeout["blocker_count"],
        "freeze_marker_status": closeout["freeze_marker_status"],
        "next_action": closeout["next_blocked_item"]["next_action"]
        if closeout["next_blocked_item"]
        else "No action required.",
        "dashboard_cards": [
            {
                "card_id": "v1-readiness",
                "label": "V1 readiness",
                "status": closeout["readiness"],
                "value": "ready" if closeout["v1_ready"] else "blocked",
                "detail": f"{closeout['blocker_count']} blockers",
                "endpoint": "/v1/cartographer/v1-readiness",
            },
            {
                "card_id": "v1-evidence",
                "label": "Evidence",
                "status": "blocked" if closeout["current_missing_count"] else "green",
                "value": closeout["current_missing_count"],
                "detail": "missing real proof artifacts",
                "endpoint": "/v1/cartographer/v1-evidence",
            },
            {
                "card_id": "v1-freeze-marker",
                "label": "Freeze marker",
                "status": closeout["freeze_marker_status"],
                "value": closeout["freeze_marker_path"],
                "detail": "external marker validation",
                "endpoint": "/v1/cartographer/v1-freeze-marker-validation",
            },
            {
                "card_id": "v1-authority",
                "label": "Authority",
                "status": "locked",
                "value": "locked",
                "detail": "passing checks do not grant authority",
                "endpoint": "/v1/cartographer/v1-closeout-status",
            },
            {
                "card_id": "v1-docs",
                "label": "Evidence contract",
                "status": "read_only",
                "value": docs_path,
                "detail": "human-recorded artifact shapes",
                "endpoint": "/v1/cartographer/v1-closeout-dashboard",
            },
        ],
        "manual_check": (
            "curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-dashboard | jq ."
        ),
        "expected_outcome": [
            "write_actions_enabled remains false",
            "authority_granted remains false",
            "actions_taken remains false",
            "dashboard_cards contains readiness, evidence, freeze marker, authority, and docs",
        ],
        "source_endpoint": "/v1/cartographer/v1-closeout-status",
        "source_status": closeout,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_v1_closeout_audit_summary() -> dict[str, Any]:
    closeout = build_cartographer_v1_closeout_status()
    dashboard = build_cartographer_v1_closeout_dashboard()
    validation = build_v1_freeze_marker_validation()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "audit_mode": "read_only_v1_closeout_final_summary",
        "closeout_status": closeout["closeout_status"],
        "readiness": closeout["readiness"],
        "v1_ready": closeout["v1_ready"],
        "blocker_count": closeout["blocker_count"],
        "current_missing_count": closeout["current_missing_count"],
        "remaining_after_dry_run": closeout["remaining_after_dry_run"],
        "freeze_marker_status": closeout["freeze_marker_status"],
        "freeze_marker_valid": closeout["freeze_marker_valid"],
        "freeze_marker_path": closeout["freeze_marker_path"],
        "docs_path": dashboard["docs_path"],
        "docs_label": dashboard["docs_label"],
        "surfaces": [
            {
                "surface_id": "readiness",
                "endpoint": "/v1/cartographer/v1-readiness",
                "status": closeout["readiness"],
            },
            {
                "surface_id": "evidence",
                "endpoint": "/v1/cartographer/v1-evidence",
                "status": "blocked" if closeout["current_missing_count"] else "green",
            },
            {
                "surface_id": "closeout_status",
                "endpoint": "/v1/cartographer/v1-closeout-status",
                "status": closeout["closeout_status"],
            },
            {
                "surface_id": "dashboard",
                "endpoint": "/v1/cartographer/v1-closeout-dashboard",
                "status": dashboard["dashboard_mode"],
            },
            {
                "surface_id": "freeze_marker_validation",
                "endpoint": "/v1/cartographer/v1-freeze-marker-validation",
                "status": validation["validation_status"],
            },
        ],
        "remaining_blockers": [
            closeout["next_blocked_item"]
        ] if closeout["next_blocked_item"] else [],
        "safety_invariants": [
            "write_actions_enabled remains false",
            "authority_granted remains false",
            "actions_taken remains false",
            "passing_tests_grant_authority remains false",
            "apply, commit, push, cleanup, and promotion remain separate approvals",
        ],
        "manual_check": (
            "curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-audit-summary | jq ."
        ),
        "expected_outcome": [
            "audit_mode is read_only_v1_closeout_final_summary",
            "surfaces list all v1 closeout read-only endpoints",
            "docs_path points to the evidence artifact contract",
            "no authority or action flag is enabled",
        ],
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_v1_closeout_endpoint_index() -> dict[str, Any]:
    audit = build_cartographer_v1_closeout_audit_summary()
    endpoints = [
        {
            "endpoint": "/v1/cartographer/v1-readiness",
            "purpose": "Report v1 readiness gates and current blockers.",
            "surface_id": "readiness",
            "read_only": True,
        },
        {
            "endpoint": "/v1/cartographer/v1-evidence",
            "purpose": "Inventory existing proof and soak artifacts.",
            "surface_id": "evidence",
            "read_only": True,
        },
        {
            "endpoint": "/v1/cartographer/v1-proof-contract",
            "purpose": "Describe accepted proof artifact shape.",
            "surface_id": "proof_contract",
            "read_only": True,
        },
        {
            "endpoint": "/v1/cartographer/v1-proof-validation",
            "purpose": "Validate existing proof artifacts without recording them.",
            "surface_id": "proof_validation",
            "read_only": True,
        },
        {
            "endpoint": "/v1/cartographer/v1-freeze-marker-validation",
            "purpose": "Validate an existing external freeze marker.",
            "surface_id": "freeze_marker_validation",
            "read_only": True,
        },
        {
            "endpoint": "/v1/cartographer/v1-closeout-status",
            "purpose": "Roll readiness, evidence, and freeze marker status into closeout state.",
            "surface_id": "closeout_status",
            "read_only": True,
        },
        {
            "endpoint": "/v1/cartographer/v1-closeout-dashboard",
            "purpose": "Provide a compact dashboard surface for humans and UI.",
            "surface_id": "dashboard",
            "read_only": True,
        },
        {
            "endpoint": "/v1/cartographer/v1-closeout-audit-summary",
            "purpose": "Summarize closeout surfaces, docs, blockers, and safety invariants.",
            "surface_id": "audit_summary",
            "read_only": True,
        },
    ]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "index_mode": "read_only_v1_closeout_endpoint_index",
        "endpoint_count": len(endpoints),
        "endpoints": endpoints,
        "docs_path": audit["docs_path"],
        "audit_endpoint": "/v1/cartographer/v1-closeout-audit-summary",
        "dashboard_endpoint": "/v1/cartographer/v1-closeout-dashboard",
        "remaining_blocker_count": len(audit["remaining_blockers"]),
        "safety_invariants": audit["safety_invariants"],
        "manual_check": (
            "curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-endpoints | jq ."
        ),
        "expected_outcome": [
            "index_mode is read_only_v1_closeout_endpoint_index",
            "every endpoint entry is read_only",
            "no authority or action flag is enabled",
        ],
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_v1_closeout_finalization_marker() -> dict[str, Any]:
    audit = build_cartographer_v1_closeout_audit_summary()
    endpoint_index = build_cartographer_v1_closeout_endpoint_index()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "marker_mode": "read_only_v1_closeout_surface_complete",
        "surface_set_complete": True,
        "readiness_blocked": not audit["v1_ready"],
        "real_external_evidence_required": True,
        "closeout_status": audit["closeout_status"],
        "readiness": audit["readiness"],
        "remaining_blocker_count": len(audit["remaining_blockers"]),
        "remaining_blockers": audit["remaining_blockers"],
        "endpoint_count": endpoint_index["endpoint_count"],
        "endpoint_index": "/v1/cartographer/v1-closeout-endpoints",
        "audit_endpoint": endpoint_index["audit_endpoint"],
        "dashboard_endpoint": endpoint_index["dashboard_endpoint"],
        "docs_path": audit["docs_path"],
        "finalization_summary": (
            "Cartographer v1 closeout surfaces are complete and read-only; "
            "v1 readiness remains blocked until real external proof and freeze-marker evidence is recorded."
        ),
        "safety_invariants": audit["safety_invariants"],
        "manual_check": (
            "curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-finalization | jq ."
        ),
        "expected_outcome": [
            "marker_mode is read_only_v1_closeout_surface_complete",
            "surface_set_complete is true",
            "readiness_blocked remains true until real external evidence exists",
            "no authority or action flag is enabled",
        ],
        "safety": cartographer_safety_manifest(),
    }


def _v1_closeout_dashboard_label(closeout_status: str) -> str:
    if closeout_status == "ready_with_valid_freeze_marker":
        return "Ready with freeze marker"
    if closeout_status == "ready_missing_freeze_marker":
        return "Ready, freeze marker missing"
    return "Blocked by missing evidence"


def build_cartographer_v1_closeout_handoff() -> dict[str, Any]:
    readiness = build_v1_readiness()
    checklist = build_v1_closeout_checklist()
    gap_report = build_v1_evidence_gap_report()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "handoff_mode": "read_only_human_review_summary",
        "v1_ready": readiness["v1_ready"],
        "readiness": readiness["readiness"],
        "blocker_count": readiness["blocker_count"],
        "current_missing_count": gap_report["current_missing_count"],
        "current_missing_evidence": gap_report["current_missing_evidence"],
        "dry_run_would_satisfy_count": gap_report["dry_run_would_satisfy_count"],
        "dry_run_would_satisfy": gap_report["dry_run_would_satisfy"],
        "remaining_after_dry_run": gap_report["remaining_after_dry_run"],
        "readiness_would_be_ready": gap_report["readiness_would_be_ready"],
        "authority_would_remain_locked": True,
        "passing_tests_grant_authority": False,
        "next_blocked_item": checklist["next_blocked_item"],
        "checklist": checklist["checklist"],
        "handoff_summary": (
            "Cartographer v1 is not ready because real proof artifacts are missing; "
            "dry-run previews show the evidence shape that would clear blockers, "
            "but authority remains locked until separate human approval."
        ),
        "human_review_notes": [
            "Review and record real proof artifacts outside Cartographer if appropriate.",
            "Validate recorded artifacts before relying on readiness.",
            "Do not treat dry-run readiness as approval to apply, commit, push, delete, or promote authority.",
            "Passing tests or recorded artifacts do not grant authority.",
        ],
        "source_endpoints": [
            "/v1/cartographer/v1-readiness",
            "/v1/cartographer/v1-closeout-checklist",
            "/v1/cartographer/v1-evidence-gap-report",
            "/v1/cartographer/v1-combined-readiness-dry-run",
        ],
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_v1_freeze_marker_proposal() -> dict[str, Any]:
    handoff = build_cartographer_v1_closeout_handoff()
    marker_path = "data/cartographer-v1-freeze/freeze-marker.json"
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "proposal_only": True,
        "freeze_marker_enabled": False,
        "freeze_actions_enabled": False,
        "marker_path": marker_path,
        "proposal_policy": "human_or_external_tool_may_record_after_review",
        "proposal": {
            "proposal_id": "v1-freeze-marker-proposal",
            "proposal_type": "manual_v1_freeze_marker_recording",
            "status": "drafted",
            "requires_human_action": True,
            "requires_approval": True,
            "action_taken": False,
            "target_file": marker_path,
            "reason": (
                "Record a reviewed v1 closeout freeze marker after real proof artifacts "
                "are present and validated."
            ),
        },
        "marker_schema": {
            "marker_version": "cartographer.v1.freeze_marker.v1",
            "required_fields": [
                "marker_version",
                "created_at",
                "head_sha",
                "branch",
                "readiness",
                "v1_ready",
                "evidence_summary",
                "authority_boundary",
            ],
            "authority_boundary_required_values": {
                "write_actions_enabled": False,
                "authority_granted": False,
                "actions_taken": False,
                "passing_tests_grant_authority": False,
            },
        },
        "example_marker": {
            "marker_version": "cartographer.v1.freeze_marker.v1",
            "created_at": "2026-05-18T00:00:00Z",
            "head_sha": "example-head-sha",
            "branch": "main",
            "readiness": handoff["readiness"],
            "v1_ready": handoff["v1_ready"],
            "evidence_summary": {
                "current_missing_count": handoff["current_missing_count"],
                "current_missing_evidence": handoff["current_missing_evidence"],
                "dry_run_would_satisfy_count": handoff["dry_run_would_satisfy_count"],
                "remaining_after_dry_run": handoff["remaining_after_dry_run"],
            },
            "authority_boundary": {
                "write_actions_enabled": False,
                "authority_granted": False,
                "actions_taken": False,
                "passing_tests_grant_authority": False,
            },
            "human_review_notes": handoff["human_review_notes"],
        },
        "source_endpoints": [
            "/v1/cartographer/v1-closeout-handoff",
            "/v1/cartographer/v1-evidence-gap-report",
            "/v1/cartographer/v1-proof-validation",
            "/v1/cartographer/v1-readiness",
        ],
        "safety_notes": [
            "Cartographer is not writing this freeze marker.",
            "The proposal is informational and does not grant authority.",
            "A freeze marker does not approve apply, commit, push, cleanup, or promotion.",
            "Validate real proof artifacts before recording any freeze marker.",
        ],
        "safety": cartographer_safety_manifest(),
    }


def write_cartographer_starter_blueprints(
    *,
    proposal_id: str,
    approved: bool,
    approved_by: str,
) -> dict[str, Any]:
    return write_approved_starter_blueprints(
        proposal_id=proposal_id,
        approved=approved,
        approved_by=approved_by,
    )


def build_cartographer_branch_recommendations() -> dict[str, Any]:
    recommendations = recommend_branches()
    first = recommendations[0] if recommendations else None
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "recommended": first is not None,
        "branch_name": first.suggested_branch if first else None,
        "reason": first.reason if first else None,
        "requires_approval": first.requires_approval if first else False,
        "recommendations": to_jsonable(recommendations),
        "recommendation_count": len(recommendations),
        "approval_type": "branch_creation",
        "approval_endpoint_template": "/v1/cartographer/branch-recommendations/{recommendation_id}/approve",
        "branch_creation_enabled": False,
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_commit_proposals() -> dict[str, Any]:
    proposals = build_commit_proposals()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "commit_proposals": to_jsonable(proposals),
        "commit_proposal_count": len(proposals),
        "approval_type": "commit_creation",
        "approval_endpoint_template": "/v1/cartographer/commit-proposals/{commit_proposal_id}/approve",
        "commit_enabled": False,
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_3_commit_proposals() -> dict[str, Any]:
    payload = build_level_3_commit_proposal_preview(
        level_2_readiness=build_level_2_readiness(),
    )
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_level_3_commit_approval_preview(
    *,
    proposal_id: str,
    approval_id: str | None,
    approved_by: str | None,
    exact_file_list: list[str],
    proposed_commit_title: str,
    proposed_commit_body: str,
    git_head_at_creation: str | None = None,
    dirty_tree_fingerprint: str | None = None,
    check_results: list[dict[str, Any]] | None = None,
    approved_deleted_files: list[str] | None = None,
) -> dict[str, Any]:
    payload = build_level_3_commit_approval_preview(
        proposal_id=proposal_id,
        approval_id=approval_id,
        approved_by=approved_by,
        exact_file_list=exact_file_list,
        proposed_commit_title=proposed_commit_title,
        proposed_commit_body=proposed_commit_body,
        git_head_at_creation=git_head_at_creation,
        dirty_tree_fingerprint=dirty_tree_fingerprint,
        check_results=check_results,
        approved_deleted_files=approved_deleted_files,
    )
    payload["safety"] = cartographer_safety_manifest()
    return payload


def block_cartographer_level_3_commit_execution(
    *,
    proposal_id: str,
    approval_id: str | None,
    approved_by: str | None,
    exact_file_list: list[str] | None = None,
    proposed_commit_title: str = "",
    proposed_commit_body: str = "",
    git_head_at_creation: str | None = None,
    dirty_tree_fingerprint: str | None = None,
    check_results: list[dict[str, Any]] | None = None,
    approved_deleted_files: list[str] | None = None,
) -> dict[str, Any]:
    payload = build_level_3_commit_execution_block(
        proposal_id=proposal_id,
        approval_id=approval_id,
        approved_by=approved_by,
        exact_file_list=exact_file_list,
        proposed_commit_title=proposed_commit_title,
        proposed_commit_body=proposed_commit_body,
        git_head_at_creation=git_head_at_creation,
        dirty_tree_fingerprint=dirty_tree_fingerprint,
        check_results=check_results,
        approved_deleted_files=approved_deleted_files,
        level_2_readiness=build_level_2_readiness(),
    )
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_level_3_closeout_readiness() -> dict[str, Any]:
    proposals = build_cartographer_level_3_commit_proposals()
    level_2 = build_level_2_readiness()
    gates = [
        _level_3_closeout_gate(
            "proposal_schema_available",
            proposals["proposal_version"] == "cartographer.level_3.commit_proposal.v1",
            "Level 3 proposal receipts expose branch, HEAD, dirty-tree fingerprint, file bundle, tests, blockers, rollback, and safety flags.",
        ),
        _level_3_closeout_gate(
            "commit_proposal_preview_endpoint_available",
            proposals["endpoint"] == "/v1/cartographer/level-3-commit-proposals",
            "Read-only Level 3 proposal endpoint is available.",
        ),
        _level_3_closeout_gate(
            "approval_preview_gate_available",
            True,
            "Approval preview validates actor, exact files, title/body, HEAD, dirty-tree fingerprint, checks, and explicit deletions.",
        ),
        _level_3_closeout_gate(
            "commit_execution_hard_blocked",
            True,
            "Level 3 commit execution endpoint exists only as a hard block and cannot create commits.",
        ),
        _level_3_closeout_gate(
            "commit_push_branch_locked",
            not proposals["commit_allowed"]
            and not proposals["push_allowed"]
            and not proposals["branch_creation_allowed"],
            "Level 3 proposal surface keeps commit, push, and branch creation disabled.",
        ),
        _level_3_closeout_gate(
            "level_2_safe_dependency",
            bool(level_2["docs_apply_enabled"]),
            (
                "Level 2 docs apply is usable."
                if level_2["docs_apply_enabled"]
                else "Level 2 docs apply remains blocked; Level 3 must stay proposal-only."
            ),
        ),
        _level_3_closeout_gate(
            "dirty_tree_groups_classified",
            "unknown_files_require_manual_classification" not in proposals["activation_blockers"],
            (
                "Dirty tree groups are classified."
                if "unknown_files_require_manual_classification" not in proposals["activation_blockers"]
                else "Unknown files remain and block Level 3 commit readiness."
            ),
        ),
    ]
    blockers = [gate for gate in gates if not gate["passed"]]
    proposal_preview_ready = not any(
        gate["code"] in {
            "proposal_schema_available",
            "commit_proposal_preview_endpoint_available",
            "approval_preview_gate_available",
            "commit_execution_hard_blocked",
            "commit_push_branch_locked",
        }
        and not gate["passed"]
        for gate in gates
    )
    local_commit_ready = not blockers
    return {
        "status": "observing",
        "level": 3,
        "mode": "closeout_readiness_packet",
        "readiness_version": "cartographer.level_3.closeout_readiness.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "proposal_preview_ready": proposal_preview_ready,
        "local_commit_ready": local_commit_ready,
        "commit_allowed": False,
        "commit_execution_enabled": False,
        "push_allowed": False,
        "branch_creation_allowed": False,
        "creates_push_queue_item": False,
        "level_2_docs_apply_enabled": level_2["docs_apply_enabled"],
        "level_2_blockers": [blocker["code"] for blocker in level_2["blockers"]],
        "proposal_count": proposals["proposal_count"],
        "activation_blockers": proposals["activation_blockers"],
        "gates": gates,
        "gate_count": len(gates),
        "passed_count": len([gate for gate in gates if gate["passed"]]),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "endpoints": [
            "/v1/cartographer/level-3-commit-proposals",
            "/v1/cartographer/level-3-commit-proposals/{proposal_id}/approval-preview",
            "/v1/cartographer/level-3-commit-proposals/{proposal_id}/commit",
            "/v1/cartographer/level-3-closeout-readiness",
        ],
        "manual_checks": [
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_3 or commit"',
            "PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py",
            "git status -sb",
        ],
        "next_step": (
            "Resolve Level 2 and unknown dirty-tree blockers before implementing local commit execution."
            if blockers
            else "Level 3 proposal/approval gates are ready for a separately approved local commit execution increment."
        ),
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_3_endpoint_index() -> dict[str, Any]:
    closeout = build_cartographer_level_3_closeout_readiness()
    endpoints = [
        {
            "endpoint": "/v1/cartographer/level-3-commit-proposals",
            "method": "GET",
            "surface_id": "commit_proposal_preview",
            "mode": "read_only_commit_bundle_preview",
            "purpose": "Return Level 3 commit proposal receipts, bundles, blockers, and required checks.",
            "write_actions_enabled": False,
            "commit_allowed": False,
            "push_allowed": False,
        },
        {
            "endpoint": "/v1/cartographer/level-3-commit-proposals/{proposal_id}/approval-preview",
            "method": "POST",
            "surface_id": "approval_preview",
            "mode": "read_only_approval_gate_preview",
            "purpose": "Validate human approval fields without staging or committing.",
            "write_actions_enabled": False,
            "commit_allowed": False,
            "push_allowed": False,
        },
        {
            "endpoint": "/v1/cartographer/level-3-commit-proposals/{proposal_id}/commit",
            "method": "POST",
            "surface_id": "commit_execution_block",
            "mode": "hard_blocked_commit_execution",
            "purpose": "Return a hard block for Level 3 commit execution until a separate implementation is approved.",
            "write_actions_enabled": False,
            "commit_allowed": False,
            "push_allowed": False,
        },
        {
            "endpoint": "/v1/cartographer/level-3-closeout-readiness",
            "method": "GET",
            "surface_id": "closeout_readiness",
            "mode": "read_only_closeout_readiness_packet",
            "purpose": "Summarize Level 3 proposal readiness and remaining commit blockers.",
            "write_actions_enabled": False,
            "commit_allowed": False,
            "push_allowed": False,
        },
        {
            "endpoint": "/v1/cartographer/level-3-endpoints",
            "method": "GET",
            "surface_id": "endpoint_index",
            "mode": "read_only_level_3_endpoint_index",
            "purpose": "List Level 3 read-only and hard-blocked surfaces.",
            "write_actions_enabled": False,
            "commit_allowed": False,
            "push_allowed": False,
        },
        {
            "endpoint": "/v1/cartographer/level-3-finalization",
            "method": "GET",
            "surface_id": "finalization_marker",
            "mode": "read_only_level_3_finalization_marker",
            "purpose": "Record Level 3 proposal-preview closeout state without granting commit authority.",
            "write_actions_enabled": False,
            "commit_allowed": False,
            "push_allowed": False,
        },
    ]
    return {
        "status": "observing",
        "level": 3,
        "mode": "read_only_level_3_endpoint_index",
        "index_version": "cartographer.level_3.endpoint_index.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "endpoint_count": len(endpoints),
        "endpoints": endpoints,
        "proposal_preview_ready": closeout["proposal_preview_ready"],
        "local_commit_ready": closeout["local_commit_ready"],
        "commit_allowed": False,
        "push_allowed": False,
        "creates_push_queue_item": False,
        "closeout_readiness_endpoint": "/v1/cartographer/level-3-closeout-readiness",
        "finalization_endpoint": "/v1/cartographer/level-3-finalization",
        "manual_checks": closeout["manual_checks"],
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_3_finalization_marker() -> dict[str, Any]:
    closeout = build_cartographer_level_3_closeout_readiness()
    endpoint_index = build_cartographer_level_3_endpoint_index()
    return {
        "status": "observing",
        "level": 3,
        "mode": "read_only_level_3_finalization_marker",
        "marker_version": "cartographer.level_3.finalization_marker.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "proposal_preview_complete": closeout["proposal_preview_ready"],
        "local_commit_ready": closeout["local_commit_ready"],
        "level_3_complete_for_proposal_preview": closeout["proposal_preview_ready"],
        "level_3_complete_for_commit_execution": False,
        "commit_allowed": False,
        "commit_execution_enabled": False,
        "push_allowed": False,
        "branch_creation_allowed": False,
        "creates_push_queue_item": False,
        "blocker_count": closeout["blocker_count"],
        "blockers": closeout["blockers"],
        "endpoint_index": "/v1/cartographer/level-3-endpoints",
        "endpoint_count": endpoint_index["endpoint_count"],
        "next_step": (
            "Stop Level 3 here until Level 2 and dirty-tree blockers are resolved."
            if not closeout["local_commit_ready"]
            else "Request explicit approval for a future local commit execution implementation."
        ),
        "manual_checks": closeout["manual_checks"],
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_3_blocker_handoff() -> dict[str, Any]:
    level_2 = build_cartographer_level_2_readiness()
    resolution = build_cartographer_level_2_dirty_tree_resolution()
    closeout = build_cartographer_level_3_closeout_readiness()
    blocking_groups = resolution["blocking_groups"]
    handoff_groups = [
        {
            "group_id": group["group_id"],
            "label": group["label"],
            "file_count": group["file_count"],
            "files": group["files"],
            "recommended_disposition": group["recommended_disposition"],
            "required_human_action": _level_3_handoff_action(str(group["group_id"])),
            "cartographer_may_resolve": False,
        }
        for group in blocking_groups
    ]
    return {
        "status": "observing",
        "level": 3,
        "mode": "read_only_level_3_blocker_handoff",
        "handoff_version": "cartographer.level_3.blocker_handoff.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "proposal_preview_ready": closeout["proposal_preview_ready"],
        "local_commit_ready": False,
        "commit_allowed": False,
        "commit_execution_enabled": False,
        "push_allowed": False,
        "branch_creation_allowed": False,
        "stash_allowed": False,
        "cleanup_allowed": False,
        "creates_push_queue_item": False,
        "level_2_docs_apply_enabled": level_2["docs_apply_enabled"],
        "level_2_blockers": [blocker["code"] for blocker in level_2["blockers"]],
        "dirty_tree_block": resolution["dirty_tree_block"],
        "blocking_file_count": resolution["blocking_file_count"],
        "blocking_group_count": resolution["blocking_group_count"],
        "blocking_groups": handoff_groups,
        "forbidden_resolution_actions": resolution["forbidden_resolution_actions"],
        "recommended_sequence": [
            "Review each blocking group as separate human-owned work.",
            "Land, restore, or isolate unrelated dirty files outside Cartographer Level 3.",
            "Re-run Level 2 readiness until docs_apply_enabled is true.",
            "Re-run Level 3 closeout readiness before requesting commit execution implementation.",
        ],
        "manual_checks": [
            "git status -sb",
            "PYTHONPATH=. .venv/bin/python - <<'PY'\nfrom source_proxy.cartographer.service import build_cartographer_level_3_blocker_handoff\npayload = build_cartographer_level_3_blocker_handoff()\nprint(payload['handoff_version'])\nprint(payload['level_2_docs_apply_enabled'])\nprint(payload['local_commit_ready'])\nprint(payload['blocking_file_count'])\nprint([group['group_id'] for group in payload['blocking_groups']])\nPY",
        ],
        "next_step": "Human resolves or isolates blocking groups; Cartographer remains read-only for this handoff.",
        "safety": cartographer_safety_manifest(),
    }


def _level_3_handoff_action(group_id: str) -> str:
    actions = {
        "level_2_implementation": "Review as source work and land separately before Level 2 apply.",
        "source_proxy_unrelated": "Classify, land, or isolate source_proxy changes outside Level 2 apply.",
        "app_and_dashboard_source": "Review app/dashboard changes as a separate workstream.",
        "scout_work": "Handle Scout files through Scout closeout or a Scout-specific commit plan.",
        "deleted_old_plans": "Britton explicitly decides whether to preserve, restore, or land deletions.",
        "unclassified_docs_and_markdown": "Classify docs as an explicit docs proposal or keep Level 2 blocked.",
        "unclassified_other": "Manually classify or isolate these files before Level 2 apply.",
    }
    return actions.get(group_id, "Human classification required before Level 2 or Level 3 commit readiness.")


def _level_3_closeout_gate(code: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {
        "code": code,
        "passed": passed,
        "evidence": evidence,
        "required": True,
    }


def build_cartographer_push_queue() -> dict[str, Any]:
    items = build_push_queue()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "push_queue": to_jsonable(items),
        "push_count": len(items),
        "approval_type": "push",
        "approval_endpoint_template": "/v1/cartographer/push-queue/{push_id}/approve",
        "push_enabled": False,
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_4_push_readiness_contract() -> dict[str, Any]:
    items = [to_jsonable(item) for item in build_push_queue()]
    ready_items = [
        item
        for item in items
        if not item.get("dirty")
        and item.get("test_status") == "passed"
        and item.get("commit_audit_status") == "recorded"
        and item.get("behind") == 0
        and item.get("drift_status") == "clear"
    ]
    blockers = sorted(
        {
            str(blocker)
            for item in items
            for blocker in item.get("push_blockers", [])
            if blocker
        }
    )
    return {
        "status": "observing",
        "level": 4,
        "mode": "push_readiness_contract",
        "contract_version": "cartographer.level_4.push_readiness_contract.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "push_allowed": False,
        "push_enabled": False,
        "auto_push_allowed": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "push_queue_creation_allowed": False,
        "push_queue_item_created": False,
        "push_queue_preview_count": len(items),
        "ready_preview_count": len(ready_items),
        "blocked_preview_count": len(items) - len(ready_items),
        "push_previews": items,
        "ready_push_previews": ready_items,
        "blockers": blockers,
        "required_inputs": [
            "local commit receipt",
            "clean working tree",
            "branch and upstream identity",
            "recorded passing checks",
            "commit audit record",
            "no blueprint drift",
            "explicit future push approval",
        ],
        "forbidden_actions": [
            "push",
            "auto-push",
            "push queue item creation",
            "merge",
            "branch creation",
            "stash",
            "cleanup",
            "self-approval",
            "promotion beyond Level 4.1",
        ],
        "manual_checks": [
            "git status -sb",
            "git log --oneline @{u}..HEAD",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "push_readiness or push_queue"',
        ],
        "next_step": (
            "Review push readiness previews; push remains disabled until a separate approved increment."
            if items
            else "No push readiness previews are available."
        ),
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_4_push_queue_proposal_preview() -> dict[str, Any]:
    readiness = build_cartographer_level_4_push_readiness_contract()
    proposals = [
        _level_4_push_queue_proposal(item)
        for item in readiness["push_previews"]
    ]
    return {
        "status": "observing",
        "level": 4,
        "mode": "push_queue_proposal_preview",
        "proposal_version": "cartographer.level_4.push_queue_proposal_preview.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "push_allowed": False,
        "push_enabled": False,
        "auto_push_allowed": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "push_queue_creation_allowed": False,
        "push_queue_item_created": False,
        "proposal_count": len(proposals),
        "push_queue_proposals": proposals,
        "required_approval_fields": [
            "proposal_id",
            "approval_id",
            "approved_by",
            "exact_commits",
            "remote",
            "branch",
            "upstream",
            "checks",
        ],
        "forbidden_actions": readiness["forbidden_actions"],
        "manual_checks": [
            "git status -sb",
            "git log --oneline @{u}..HEAD",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_4_push_queue_proposal or push_queue"',
        ],
        "next_step": (
            "Review proposal preview; approval gate remains separate and push execution is disabled."
            if proposals
            else "No push queue proposal previews are available."
        ),
        "safety": cartographer_safety_manifest(),
    }


def _level_4_push_queue_proposal(item: dict[str, Any]) -> dict[str, Any]:
    proposal_id = f"level-4-push-proposal-{item['push_id']}"
    blockers = list(dict.fromkeys(item.get("push_blockers", [])))
    return {
        "level": 4,
        "proposal_id": proposal_id,
        "proposal_version": "cartographer.level_4.push_queue_proposal_preview.v1",
        "source_push_id": item["push_id"],
        "remote": item["remote"],
        "branch": item["branch"],
        "upstream": item.get("upstream"),
        "ahead": item.get("ahead", 0),
        "behind": item.get("behind", 0),
        "commits_to_push": item.get("commits_to_push", []),
        "files": item.get("files", []),
        "push_command_preview": item.get("push_command_preview", ""),
        "rollback_guidance": item.get("rollback_guidance", ""),
        "risk_notes": [
            *item.get("branch_protection_warnings", []),
            *item.get("reason_codes", []),
        ],
        "required_checks": [
            "commit_audit_status_recorded",
            "test_status_passed",
            "dirty_tree_clean",
            "drift_clear",
            "branch_not_behind",
        ],
        "check_status": {
            "commit_audit_status": item.get("commit_audit_status"),
            "test_status": item.get("test_status"),
            "dirty": item.get("dirty"),
            "drift_status": item.get("drift_status"),
            "behind": item.get("behind", 0),
        },
        "blockers": blockers,
        "approval_required": True,
        "approval_id": None,
        "approved_by": None,
        "approved_at": None,
        "push_allowed": False,
        "push_enabled": False,
        "push_created": False,
        "creates_push_queue_item": False,
        "push_queue_item_created": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "actions_taken": False,
        "expected_output": "human-reviewable push queue proposal preview only",
    }


def build_cartographer_audit_trail() -> dict[str, Any]:
    events = build_audit_trail()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "events": to_jsonable(events),
        "event_count": len(events),
        "rollback_hints_present": all(bool(event.rollback_hint) for event in events),
        "explainability_fields_present": all(
            bool(event.event_id)
            and bool(event.event)
            and event.action is not None
            and event.result is not None
            and event.changed_files == event.files
            for event in events
        ),
        "actions_taken": False,
        "rollback_enabled": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_blueprints() -> dict[str, Any]:
    blueprints = list_blueprints()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "blueprints": to_jsonable(blueprints),
        "blueprint_count": count_blueprint_documents(),
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_clutter_inventory() -> dict[str, Any]:
    candidates = build_clutter_inventory()
    by_risk = {
        risk: [candidate for candidate in candidates if candidate.risk == risk]
        for risk in ("low", "medium", "high", "blocked")
    }
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "deletion_enabled": False,
        "cleanup_actions_enabled": False,
        "actions_taken": False,
        "candidate_count": len(candidates),
        "risk_counts": {risk: len(items) for risk, items in by_risk.items()},
        "candidates": to_jsonable(candidates),
        "candidates_by_risk": to_jsonable(by_risk),
        "inventory_policy": "read_only_no_deletion",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_clutter_proposals() -> dict[str, Any]:
    payload = build_low_risk_deletion_proposals()
    payload["proposals"] = to_jsonable(payload["proposals"])
    payload["review_required"] = to_jsonable(payload["review_required"])
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_clutter_review() -> dict[str, Any]:
    inventory = build_cartographer_clutter_inventory()
    proposals = build_cartographer_clutter_proposals()
    risk_counts = inventory["risk_counts"]
    proposal_items = proposals["proposals"]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "deletion_enabled": False,
        "cleanup_actions_enabled": False,
        "actions_taken": False,
        "review_mode": "read_only_cleanup_review",
        "candidate_count": inventory["candidate_count"],
        "risk_counts": risk_counts,
        "proposal_count": proposals["proposal_count"],
        "low_risk_candidate_count": proposals["low_risk_candidate_count"],
        "review_required_count": proposals["review_required_count"],
        "deletion_candidate_count": 0,
        "cleanup_decision_required": bool(proposal_items),
        "review_summary": (
            f"{proposals['low_risk_candidate_count']} low-risk candidates are proposal-only; "
            f"{proposals['review_required_count']} candidates require manual review. "
            "No cleanup or deletion is enabled."
        ),
        "low_risk_sample": inventory["candidates_by_risk"]["low"][:10],
        "review_required_sample": (
            inventory["candidates_by_risk"]["blocked"][:5]
            + inventory["candidates_by_risk"]["high"][:5]
            + inventory["candidates_by_risk"]["medium"][:5]
        ),
        "proposal_ids": [proposal["proposal_id"] for proposal in proposal_items],
        "source_endpoints": [
            "/v1/cartographer/clutter-inventory",
            "/v1/cartographer/clutter-proposals",
        ],
        "manual_check": (
            "curl -k -s https://localhost:3000/v1/cartographer/clutter-review | jq ."
        ),
        "expected_outcome": [
            "review_mode is read_only_cleanup_review",
            "deletion_enabled remains false",
            "cleanup_actions_enabled remains false",
            "actions_taken remains false",
            "low-risk candidates remain proposal-only",
        ],
        "safety": cartographer_safety_manifest(),
    }


def apply_cartographer_clutter_proposal(
    *,
    proposal_id: str,
    approved: bool,
    approved_by: str,
) -> dict[str, Any]:
    payload = apply_approved_low_risk_deletion_proposal(
        proposal_id=proposal_id,
        approved=approved,
        approved_by=approved_by,
    )
    payload["safety"] = cartographer_safety_manifest()
    return payload


def build_cartographer_observation() -> dict[str, Any]:
    proposals = list_proposals()
    return {
        "git": to_jsonable(read_git_status()),
        "git_statuses": to_jsonable(read_git_statuses()),
        "proposals": to_jsonable(proposals),
        "pending_proposals": len(proposals),
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_components() -> dict[str, Any]:
    component_map = build_component_map()
    statuses = read_git_statuses()
    if not statuses:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            statuses = [
                read_git_status_for_project(
                    project_id=cwd.name.lower(),
                    root=cwd,
                )
            ]
    changed_files = [
        path
        for status in statuses
        if status.available
        for path in status.changed_files
    ]
    changed_map = build_component_map(changed_files)
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "components": to_jsonable(component_map["components"]),
        "unmapped_paths": to_jsonable(component_map["unmapped_paths"]),
        "changed_components": to_jsonable(changed_map["components"]),
        "changed_unmapped_paths": to_jsonable(changed_map["unmapped_paths"]),
        "changed_file_count": len(changed_files),
        "mapping_mode": component_map["mapping_mode"],
        "changed_mapping_mode": changed_map["mapping_mode"],
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_repo_map() -> dict[str, Any]:
    repo_maps = build_repo_maps()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "maps": to_jsonable(repo_maps),
        "project_count": len(repo_maps),
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_git() -> dict[str, Any]:
    statuses = read_git_statuses()
    if not statuses:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            statuses = [
                read_git_status_for_project(
                    project_id=cwd.name.lower(),
                    root=cwd,
                )
            ]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "write_mode": "locked",
        "git_statuses": to_jsonable(statuses),
        "git": to_jsonable(statuses[0]) if statuses else to_jsonable(read_git_status()),
        "project_count": len(statuses),
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_drift() -> dict[str, Any]:
    drift = detect_blueprint_drift()
    proposals_by_drift: dict[str, list[str]] = {}
    for proposal in list_proposals():
        if proposal.source_drift_id:
            proposals_by_drift.setdefault(proposal.source_drift_id, []).append(proposal.proposal_id)
    drift = [
        replace(finding, proposal_ids=sorted(proposals_by_drift.get(finding.drift_id, [])))
        for finding in drift
    ]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "drift": to_jsonable(drift),
        "drift_count": len(drift),
        "proposal_generated": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_reminders() -> dict[str, Any]:
    reminders = build_reminders()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "reminders": to_jsonable(reminders),
        "reminder_count": len(reminders),
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_proposals() -> dict[str, Any]:
    proposals = list_proposals()
    lifecycle = proposal_states()
    visibility = proposal_visibility_summary()
    fingerprints = [
        proposal.fingerprint
        for proposal in proposals
        if proposal.fingerprint
    ]
    duplicate_proposals = len(fingerprints) - len(set(fingerprints))
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "level": 1,
        "mode": "proposal_draft",
        "authority_granted": False,
        "proposals": [_proposal_draft_payload(proposal) for proposal in proposals],
        "proposal_count": len(proposals),
        "pending_proposals": pending_proposal_count(),
        "deduped": duplicate_proposals == 0,
        "duplicate_proposals_suppressed": visibility["duplicate_proposals_suppressed"],
        "suppressed_duplicate_proposals": visibility["suppressed_duplicate_proposals"],
        "duplicate_proposals_present": duplicate_proposals,
        "stale_cleanup_candidates": visibility["stale_cleanup_candidates"],
        "stale_cleanup_candidate_count": visibility["stale_cleanup_candidate_count"],
        "cleanup_actions_enabled": visibility["cleanup_actions_enabled"],
        "proposal_states": lifecycle,
        "proposal_lifecycle": lifecycle,
        "lifecycle": lifecycle,
        "review_decisions": ["approve", "reject", "request_edit", "defer", "mark_stale"],
        "review_actions_apply_files": False,
        "apply_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "operator_review_required": True,
        "proposal_only_contract": _proposal_only_contract(),
        "transition_audit_complete": all(
            transition.actor and transition.timestamp
            for proposal in proposals
            for transition in proposal.transitions
        ),
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def _proposal_draft_payload(proposal: Any) -> dict[str, Any]:
    payload = to_jsonable(proposal)
    proposed_files = [
        str(path)
        for path in payload.get("proposed_files", [])
        if str(path)
    ]
    target_path = proposed_files[0] if proposed_files else ""
    payload.update(
        {
            "level": 1,
            "proposal_draft": True,
            "target_docs_path": target_path,
            "reason": payload.get("rationale") or payload.get("title") or "Cartographer proposal draft.",
            "risk_level": _proposal_risk_level(proposed_files),
            "proposed_change_summary": payload.get("title") or "Review proposed docs update.",
            "rollback_hint": f"git restore {target_path}" if target_path else "No rollback needed; no files were changed.",
            "manual_check": f"git diff -- {target_path}" if target_path else "git status -sb",
            "why_no_source_edit_is_needed": "Level 1 proposal drafts are review evidence only; source edits are forbidden.",
            "approval_required": True,
            "apply_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "apply_enabled": False,
            "commit_enabled": False,
            "push_enabled": False,
            "creates_commit_proposal": False,
            "creates_push_queue_item": False,
        }
    )
    return payload


def _proposal_risk_level(proposed_files: list[str]) -> str:
    if not proposed_files:
        return "blocked"
    if any(
        path.startswith(
            (
                "src/",
                "source_proxy/",
                "scout/src/",
                "backend/",
                "scripts/",
            )
        )
        or path.startswith(".env")
        or "secret" in path.lower()
        or "token" in path.lower()
        or "certificate" in path.lower()
        for path in proposed_files
    ):
        return "blocked"
    return "low"


def build_cartographer_change_scribe() -> dict[str, Any]:
    summaries = summarize_changes()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "summaries": to_jsonable(summaries),
        "summary_count": len(summaries),
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_blueprint_scribe() -> dict[str, Any]:
    drafts = draft_blueprint_updates()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "drafts": to_jsonable(drafts),
        "draft_count": len(drafts),
        "proposal_only_contract": _proposal_only_contract(),
        "direct_writes_enabled": False,
        "apply_requires_approval": True,
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_runbook_scribe() -> dict[str, Any]:
    suggestions = suggest_runbook_updates()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "suggestions": to_jsonable(suggestions),
        "suggestion_count": len(suggestions),
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


def _proposal_only_contract() -> dict[str, Any]:
    return {
        "max_authority": "proposal_only",
        "level": 1,
        "proposal_drafts_only": True,
        "blueprinter_can_write_source_of_truth_docs": False,
        "review_required": True,
        "approval_required": True,
        "apply_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "apply_requires_approval": True,
        "commit_requires_separate_approval": True,
        "push_requires_separate_approval": True,
        "generated_items_must_include_target_files": True,
        "generated_items_must_include_diff_preview": True,
    }


def build_cartographer_sub_cartographers() -> dict[str, Any]:
    roles = sub_cartographer_roles()
    outputs = sub_cartographer_outputs()
    routes = route_sub_cartographers()
    control_routes = route_control_plane_situations()
    forbidden_actions = ["approve", "apply", "commit", "push", "delete"]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "roles": to_jsonable(roles),
        "role_count": len(roles),
        "outputs": to_jsonable(outputs),
        "output_count": len(outputs),
        "output_contract_fields": [
            "summary",
            "evidence",
            "recommendation",
            "risk",
            "required_approval",
            "forbidden_actions_respected",
            "next_manual_check",
        ],
        "output_contract_enforced": all(
            output.summary
            and output.evidence
            and output.recommendation
            and output.recommendation.lower() != "looks good"
            and output.next_manual_check
            and output.forbidden_actions_respected
            and not output.action_taken
            for output in outputs
        ),
        "max_authority": "proposal_only",
        "forbidden_actions": forbidden_actions,
        "forbidden_actions_enforced": all(
            all(action in role.forbidden_actions for action in forbidden_actions)
            and not role.can_approve
            and not role.can_apply
            and not role.can_commit
            and not role.can_push
            and not role.can_delete
            for role in roles
        ),
        "routes": to_jsonable(routes),
        "route_count": len(routes),
        "control_plane_routes": to_jsonable(control_routes),
        "control_plane_route_count": len(control_routes),
        "control_plane_routing_enabled": True,
        "control_plane_actions_enabled": False,
        "control_plane_contract_enforced": all(
            route.selected_roles
            and route.reason
            and route.evidence
            and route.parent_control_plane_required
            and route.approval_gate_required
            and not route.mutation_allowed
            and not route.action_taken
            for route in control_routes
        ),
        "actions_taken": False,
        "failures_stop_at": "proposal_queue",
        "safety": cartographer_safety_manifest(),
    }
