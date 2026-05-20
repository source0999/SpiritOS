from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
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


def build_cartographer_level_6_project_registry_hardening() -> dict[str, Any]:
    configured = [to_jsonable(root) for root in configured_project_roots()]
    blocked = [to_jsonable(root) for root in blocked_project_roots()]
    projects = [to_jsonable(project) for project in discover_projects()]
    candidates = [to_jsonable(candidate) for candidate in discover_project_candidates()]
    configured_root_checks = [_level_6_configured_root_check(root) for root in configured]
    registry_entries = [
        _level_6_project_registry_entry(project)
        for project in projects
    ]
    registry_blockers = _level_6_registry_blockers(
        configured_root_checks=configured_root_checks,
        registry_entries=registry_entries,
        blocked_roots=blocked,
    )
    return {
        "status": "observing",
        "level": 6,
        "mode": "project_registry_hardening",
        "contract_version": "cartographer.level_6.project_registry_hardening.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "cross_repo_mutation_allowed": False,
        "project_enrollment_allowed": False,
        "auto_enrollment_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "configured_roots": configured_root_checks,
        "blocked_roots": blocked,
        "registry_entries": registry_entries,
        "project_candidates": candidates,
        "project_count": len(registry_entries),
        "candidate_count": len(candidates),
        "blockers": registry_blockers,
        "forbidden_actions": [
            "cross-repo mutation",
            "commits",
            "pushes",
            "branch creation",
            "worktree creation",
            "cleanup",
            "merge",
            "stash",
            "automatic project enrollment",
            "promotion beyond Level 6.1",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_project_registry"',
        ],
        "next_step": "Level 6.2 may add a cross-project status board only after Britton approves it.",
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


def build_cartographer_level_5_parallel_work_risk_model() -> dict[str, Any]:
    statuses = read_git_statuses()
    if not statuses:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            statuses = [read_git_status_for_project(project_id=cwd.name.lower(), root=cwd)]
    project_risks = [_level_5_project_risk(status) for status in statuses]
    active_risks = [
        risk
        for project in project_risks
        for risk in project["risks"]
    ]
    high_risks = [risk for risk in active_risks if risk["severity"] == "high"]
    medium_risks = [risk for risk in active_risks if risk["severity"] == "medium"]
    return {
        "status": "observing",
        "level": 5,
        "mode": "parallel_work_risk_model",
        "contract_version": "cartographer.level_5.parallel_work_risk_model.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "checkout_allowed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "push_allowed": False,
        "project_count": len(project_risks),
        "risk_count": len(active_risks),
        "high_risk_count": len(high_risks),
        "medium_risk_count": len(medium_risks),
        "projects": project_risks,
        "recommended_next_action": (
            "Review dirty files and worktree ownership before assigning parallel Codex work."
            if active_risks
            else "No parallel work collision risks detected."
        ),
        "forbidden_actions": [
            "branch creation",
            "worktree creation",
            "checkout",
            "merge",
            "cleanup",
            "stash",
            "push",
            "autonomous worker reassignment",
            "promotion beyond Level 5.1",
        ],
        "manual_checks": [
            "git status -sb",
            "git worktree list",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_5_parallel_work_risk"',
        ],
        "next_step": "Level 5.2 may refresh branch recommendations only after Britton approves it.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_5_branch_recommendation_refresh() -> dict[str, Any]:
    risk_model = build_cartographer_level_5_parallel_work_risk_model()
    base_payload = build_cartographer_branch_recommendations()
    recommendations = [
        _level_5_branch_recommendation(
            recommendation,
            risk_model=risk_model,
        )
        for recommendation in base_payload["recommendations"]
    ]
    return {
        "status": "observing",
        "level": 5,
        "mode": "branch_recommendation_refresh",
        "contract_version": "cartographer.level_5.branch_recommendation_refresh.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "checkout_allowed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "push_allowed": False,
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
        "risk_model": risk_model,
        "required_approval_fields": [
            "recommendation_id",
            "approval_id",
            "approved_by",
            "exact_branch_name",
            "base_branch",
            "base_head",
            "owner",
            "purpose",
            "command_preview",
        ],
        "forbidden_actions": [
            "branch creation",
            "checkout",
            "merge",
            "push",
            "cleanup",
            "stash",
            "executor behavior",
            "promotion beyond Level 5.2",
        ],
        "manual_checks": [
            "git status -sb",
            "git branch --show-current",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_5_branch_recommendation"',
        ],
        "next_step": "Level 5.3 may recommend worktrees only after Britton approves it.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_5_worktree_recommendation_contract() -> dict[str, Any]:
    branch_payload = build_cartographer_level_5_branch_recommendation_refresh()
    recommendations = [
        _level_5_worktree_recommendation(recommendation)
        for recommendation in branch_payload["recommendations"]
    ]
    return {
        "status": "observing",
        "level": 5,
        "mode": "worktree_recommendation_contract",
        "contract_version": "cartographer.level_5.worktree_recommendation_contract.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "worktree_creation_allowed": False,
        "branch_creation_allowed": False,
        "checkout_allowed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "push_allowed": False,
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
        "branch_recommendation_refresh": branch_payload,
        "required_approval_fields": [
            "recommendation_id",
            "approval_id",
            "approved_by",
            "exact_worktree_path",
            "exact_branch_name",
            "base_head",
            "owner",
            "purpose",
            "command_preview",
        ],
        "forbidden_actions": [
            "worktree creation",
            "branch creation",
            "checkout",
            "cleanup",
            "stash",
            "merge",
            "push",
            "executor behavior",
            "promotion beyond Level 5.3",
        ],
        "manual_checks": [
            "git status -sb",
            "git worktree list",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_5_worktree_recommendation"',
        ],
        "next_step": "Level 5.4 may add an approval preview gate only after Britton approves it.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_5_branch_worktree_approval_preview(
    *,
    recommendation_id: str,
    approval_id: str | None,
    approved_by: str | None,
    exact_worktree_path: str | None,
    exact_branch_name: str | None,
    base_head: str | None,
    owner: str | None,
    purpose: str | None,
    command_preview: str | None,
) -> dict[str, Any]:
    recommendations_payload = build_cartographer_level_5_worktree_recommendation_contract()
    recommendation = next(
        (
            item
            for item in recommendations_payload["recommendations"]
            if item["recommendation_id"] == recommendation_id
        ),
        None,
    )
    blockers: list[str] = []
    if recommendation is None:
        blockers.append("recommendation_not_found")
    if not approval_id:
        blockers.append("approval_id_required")
    if not approved_by:
        blockers.append("approved_by_required")
    if str(approved_by or "").strip().lower() == "cartographer":
        blockers.append("cartographer_self_approval_blocked")
    if not owner:
        blockers.append("owner_required")
    if not purpose:
        blockers.append("purpose_required")
    if recommendation is not None and exact_worktree_path != recommendation.get("target_path"):
        blockers.append("exact_worktree_path_mismatch")
    if recommendation is not None and exact_branch_name != recommendation.get("branch_proposal"):
        blockers.append("exact_branch_name_mismatch")
    if recommendation is not None and base_head != recommendation.get("base_head"):
        blockers.append("base_head_mismatch")
    if recommendation is not None and command_preview != recommendation.get("command_preview"):
        blockers.append("command_preview_mismatch")
    unique_blockers = list(dict.fromkeys(blockers))
    approval_validated = recommendation is not None and not unique_blockers
    return {
        "status": "approval_preview",
        "level": 5,
        "mode": "branch_worktree_approval_gate_preview",
        "approval_version": "cartographer.level_5.branch_worktree_approval_preview.v1",
        "recommendation_id": recommendation_id,
        "recommendation_found": recommendation is not None,
        "approval_required": True,
        "approval_id": approval_id,
        "approved_by": approved_by,
        "owner": owner,
        "purpose": purpose,
        "approval_validated": approval_validated,
        "exact_worktree_path": exact_worktree_path,
        "expected_worktree_path": recommendation.get("target_path") if recommendation else None,
        "exact_branch_name": exact_branch_name,
        "expected_branch_name": recommendation.get("branch_proposal") if recommendation else None,
        "base_head": base_head,
        "expected_base_head": recommendation.get("base_head") if recommendation else None,
        "command_preview": command_preview,
        "expected_command_preview": recommendation.get("command_preview") if recommendation else None,
        "blockers": unique_blockers,
        "execution_blockers": ["branch_worktree_creation_not_implemented"],
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "worktree_creation_allowed": False,
        "worktree_created": False,
        "branch_creation_allowed": False,
        "branch_created": False,
        "checkout_allowed": False,
        "checkout_performed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "push_allowed": False,
        "recommendation": recommendation,
        "next_step": (
            "Approval metadata validates, but branch and worktree creation remain disabled."
            if approval_validated
            else "Resolve approval preview blockers before requesting future branch or worktree creation."
        ),
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_5_multi_worker_safety_smoke() -> dict[str, Any]:
    risk_model = build_cartographer_level_5_parallel_work_risk_model()
    branch_payload = build_cartographer_level_5_branch_recommendation_refresh()
    worktree_payload = build_cartographer_level_5_worktree_recommendation_contract()
    worker_previews = _level_5_worker_assignment_previews(
        risk_model=risk_model,
        worktree_payload=worktree_payload,
    )
    collision_count = sum(
        1
        for preview in worker_previews
        if preview["collision_status"] != "clear"
    )
    return {
        "status": "observing",
        "level": 5,
        "mode": "multi_codex_worker_safety_smoke",
        "smoke_version": "cartographer.level_5.multi_worker_safety_smoke.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "checkout_allowed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "push_allowed": False,
        "worker_assignment_count": len(worker_previews),
        "collision_count": collision_count,
        "worker_assignments": worker_previews,
        "risk_model": risk_model,
        "branch_recommendation_refresh": branch_payload,
        "worktree_recommendation_contract": worktree_payload,
        "forbidden_actions": [
            "branch creation",
            "worktree creation",
            "checkout",
            "merge",
            "cleanup",
            "stash",
            "push",
            "autonomous task reassignment",
            "promotion beyond Level 5.5",
        ],
        "manual_checks": [
            "git status -sb",
            "git worktree list",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_5_multi_worker_safety"',
        ],
        "next_step": "Level 6.1 may harden the project registry only after Britton approves it.",
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


def build_cartographer_level_4_push_queue_approval_preview(
    *,
    proposal_id: str,
    approval_id: str | None,
    approved_by: str | None,
    exact_commits: list[str],
    remote: str | None,
    branch: str | None,
    upstream: str | None,
    checks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    proposals_payload = build_cartographer_level_4_push_queue_proposal_preview()
    proposal = next(
        (
            item
            for item in proposals_payload["push_queue_proposals"]
            if item["proposal_id"] == proposal_id
        ),
        None,
    )
    blockers: list[str] = []
    if proposal is None:
        blockers.append("proposal_not_found")
    if not approval_id:
        blockers.append("approval_id_required")
    if not approved_by:
        blockers.append("approved_by_required")
    if str(approved_by or "").strip().lower() == "cartographer":
        blockers.append("cartographer_self_approval_blocked")
    normalized_commits = [str(commit).strip() for commit in exact_commits if str(commit).strip()]
    expected_commits = list(proposal.get("commits_to_push", [])) if proposal else []
    if proposal is not None and normalized_commits != expected_commits:
        blockers.append("exact_commits_mismatch")
    if proposal is not None and remote != proposal.get("remote"):
        blockers.append("remote_mismatch")
    if proposal is not None and branch != proposal.get("branch"):
        blockers.append("branch_mismatch")
    if proposal is not None and upstream != proposal.get("upstream"):
        blockers.append("upstream_mismatch")
    check_blockers = _level_4_push_check_blockers(proposal, checks or [])
    blockers.extend(check_blockers)
    unique_blockers = list(dict.fromkeys(blockers))
    approval_validated = proposal is not None and not unique_blockers
    return {
        "status": "approval_preview",
        "level": 4,
        "mode": "push_queue_approval_gate_preview",
        "approval_version": "cartographer.level_4.push_queue_approval_preview.v1",
        "proposal_id": proposal_id,
        "proposal_found": proposal is not None,
        "approval_required": True,
        "approval_id": approval_id,
        "approved_by": approved_by,
        "approved_at": None,
        "approval_validated": approval_validated,
        "exact_commits": normalized_commits,
        "expected_commits": expected_commits,
        "remote": remote,
        "expected_remote": proposal.get("remote") if proposal else None,
        "branch": branch,
        "expected_branch": proposal.get("branch") if proposal else None,
        "upstream": upstream,
        "expected_upstream": proposal.get("upstream") if proposal else None,
        "required_checks": proposal.get("required_checks", []) if proposal else [],
        "checks": checks or [],
        "checks_validated": not check_blockers,
        "blockers": unique_blockers,
        "execution_blockers": ["push_execution_not_implemented"],
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "push_allowed": False,
        "push_enabled": False,
        "auto_push_allowed": False,
        "push_created": False,
        "push_queue_creation_allowed": False,
        "push_queue_item_created": False,
        "creates_push_queue_item": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "next_step": (
            "Approval metadata validates, but push execution remains disabled."
            if approval_validated
            else "Resolve approval preview blockers before requesting future push execution."
        ),
        "safety": cartographer_safety_manifest(),
    }


def block_cartographer_level_4_push_execution(
    *,
    proposal_id: str,
    approval_id: str | None,
    approved_by: str | None,
) -> dict[str, Any]:
    proposals_payload = build_cartographer_level_4_push_queue_proposal_preview()
    proposal = next(
        (
            item
            for item in proposals_payload["push_queue_proposals"]
            if item["proposal_id"] == proposal_id
        ),
        None,
    )
    blockers = ["level_4_push_execution_not_implemented"]
    if proposal is None:
        blockers.append("proposal_not_found")
    if not approval_id:
        blockers.append("approval_id_required")
    if not approved_by:
        blockers.append("approved_by_required")
    if str(approved_by or "").strip().lower() == "cartographer":
        blockers.append("cartographer_self_approval_blocked")
    unique_blockers = list(dict.fromkeys(blockers))
    return {
        "status": "blocked",
        "level": 4,
        "mode": "push_execution_hard_block",
        "block_version": "cartographer.level_4.push_execution_hard_block.v1",
        "proposal_id": proposal_id,
        "proposal_found": proposal is not None,
        "approval_id": approval_id,
        "approved_by": approved_by,
        "blockers": unique_blockers,
        "execution_blockers": ["push_execution_not_implemented"],
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "push_allowed": False,
        "push_enabled": False,
        "auto_push_allowed": False,
        "push_created": False,
        "push_queue_creation_allowed": False,
        "push_queue_item_created": False,
        "creates_push_queue_item": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "proposal": proposal,
        "forbidden_actions": [
            "push",
            "auto-push",
            "push queue item creation",
            "merge",
            "branch creation",
            "stash",
            "cleanup",
            "self-approval",
            "promotion beyond Level 4.4",
        ],
        "manual_checks": [
            "git status -sb",
            "git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_4_push_execution or push_queue"',
        ],
        "next_step": (
            "Push execution is hard-blocked; continue to future Level 4.5 planning only after approval."
        ),
        "safety": cartographer_safety_manifest(),
    }


def _level_5_project_risk(status: Any) -> dict[str, Any]:
    root = Path(status.root) if status.root else None
    worktrees = _level_5_worktrees(root)
    changed_files = list(getattr(status, "changed_files", []) or [])
    risks: list[dict[str, Any]] = []
    if not getattr(status, "available", False):
        risks.append(
            {
                "risk_id": "git_status_unavailable",
                "severity": "medium",
                "message": "Git status is unavailable; parallel work cannot be safely assigned.",
                "related_files": [],
            }
        )
    if getattr(status, "dirty", False):
        risks.append(
            {
                "risk_id": "dirty_tree_collision_risk",
                "severity": "high",
                "message": "Dirty files may collide with another Codex worker on the same branch.",
                "related_files": changed_files[:20],
            }
        )
    if getattr(status, "is_primary_branch", False) and getattr(status, "dirty", False):
        risks.append(
            {
                "risk_id": "primary_branch_dirty_risk",
                "severity": "high",
                "message": "Dirty work on a primary branch should be isolated before parallel work.",
                "related_files": changed_files[:20],
            }
        )
    if getattr(status, "ahead", 0) > 0:
        risks.append(
            {
                "risk_id": "unpushed_commit_collision_risk",
                "severity": "medium",
                "message": "Unpushed commits may confuse branch or worktree assignment.",
                "related_files": [],
            }
        )
    if len(worktrees) > 1:
        risks.append(
            {
                "risk_id": "multiple_worktrees_detected",
                "severity": "medium",
                "message": "Existing worktrees require ownership checks before assigning parallel work.",
                "related_files": [],
            }
        )
    return {
        "project_id": getattr(status, "project_id", None),
        "root": getattr(status, "root", None),
        "available": getattr(status, "available", False),
        "branch": getattr(status, "branch", None),
        "head_sha": getattr(status, "head_sha", None),
        "upstream": getattr(status, "upstream", None),
        "dirty": getattr(status, "dirty", False),
        "changed_file_count": len(changed_files),
        "changed_files": changed_files[:20],
        "ahead": getattr(status, "ahead", 0),
        "behind": getattr(status, "behind", 0),
        "worktree_count": len(worktrees),
        "worktrees": worktrees,
        "risks": risks,
        "risk_level": _level_5_risk_level(risks),
        "owner_assignment_required": bool(risks),
        "recommended_isolation": (
            "recommend_separate_branch_or_worktree_after_approval"
            if risks
            else "none"
        ),
        "actions_taken": False,
    }


def _level_6_configured_root_check(root: dict[str, Any]) -> dict[str, Any]:
    path = str(root.get("path") or "")
    exists = Path(path).exists() if path else False
    is_dir = Path(path).is_dir() if path else False
    blockers: list[str] = []
    if not path:
        blockers.append("configured_root_path_missing")
    elif not exists:
        blockers.append("configured_root_missing")
    elif not is_dir:
        blockers.append("configured_root_not_directory")
    return {
        "path": path,
        "status": root.get("status"),
        "source": root.get("source"),
        "reason": root.get("reason"),
        "exists": exists,
        "is_directory": is_dir,
        "observation_allowed": exists and is_dir,
        "mutation_allowed": False,
        "blockers": blockers,
    }


def _level_6_project_registry_entry(project: dict[str, Any]) -> dict[str, Any]:
    markers = list(project.get("markers", []))
    repo_type = "git" if ".git" in markers else "filesystem"
    root = str(project.get("root") or "")
    path_exists = Path(root).exists() if root else False
    return {
        "project_id": project.get("project_id"),
        "name": project.get("name"),
        "root": root,
        "owner": None,
        "agent": None,
        "repo_type": repo_type,
        "markers": markers,
        "has_blueprints": project.get("has_blueprints", False),
        "blueprint_root": project.get("blueprint_root"),
        "source_root": project.get("source_root"),
        "path_exists": path_exists,
        "observation_mode": "read_only",
        "allowed_observation_mode": "read_only",
        "write_policy": project.get("write_policy", "read_only"),
        "mutation_disabled": True,
        "cross_repo_mutation_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "auto_enrollment_allowed": False,
        "actions_taken": False,
        "blockers": [] if path_exists else ["project_path_missing"],
    }


def _level_6_registry_blockers(
    *,
    configured_root_checks: list[dict[str, Any]],
    registry_entries: list[dict[str, Any]],
    blocked_roots: list[dict[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    if blocked_roots:
        blockers.append("blocked_roots_present")
    if any(root["blockers"] for root in configured_root_checks):
        blockers.append("configured_root_blockers_present")
    if any(entry["blockers"] for entry in registry_entries):
        blockers.append("project_entry_blockers_present")
    if _level_6_duplicate_values(entry.get("project_id") for entry in registry_entries):
        blockers.append("duplicate_project_ids")
    if _level_6_duplicate_values(entry.get("root") for entry in registry_entries):
        blockers.append("duplicate_project_roots")
    if any(not entry["mutation_disabled"] for entry in registry_entries):
        blockers.append("unsafe_mutation_flag_enabled")
    return blockers


def _level_6_duplicate_values(values: Any) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        normalized = str(value or "")
        if not normalized:
            continue
        if normalized in seen:
            duplicates.add(normalized)
        seen.add(normalized)
    return sorted(duplicates)


def _level_5_branch_recommendation(
    recommendation: dict[str, Any],
    *,
    risk_model: dict[str, Any],
) -> dict[str, Any]:
    project = _level_5_project_for_recommendation(recommendation, risk_model)
    risks = project.get("risks", []) if project else []
    collision_notes = [
        {
            "risk_id": risk["risk_id"],
            "severity": risk["severity"],
            "message": risk["message"],
            "related_files": risk.get("related_files", []),
        }
        for risk in risks
    ]
    suggested_branch = recommendation.get("suggested_branch")
    current_branch = recommendation.get("current_branch")
    source_head = recommendation.get("source_head")
    return {
        "level": 5,
        "recommendation_version": "cartographer.level_5.branch_recommendation_refresh.v1",
        "recommendation_id": recommendation.get("recommendation_id"),
        "project_id": recommendation.get("project_id"),
        "current_branch": current_branch,
        "base_branch": current_branch,
        "base_head": source_head,
        "suggested_branch": suggested_branch,
        "owner_required": True,
        "proposed_owner": None,
        "purpose": _level_5_branch_purpose(recommendation),
        "reason": recommendation.get("reason"),
        "changed_file_count": recommendation.get("changed_file_count", 0),
        "related_files": recommendation.get("related_files", []),
        "collision_notes": collision_notes,
        "risk_level": project.get("risk_level", "none") if project else "unknown",
        "approval_required": True,
        "status": "preview_only",
        "command_preview": f"git switch -c {suggested_branch}" if suggested_branch else "",
        "rollback_preview": recommendation.get("rollback_command"),
        "branch_exists": recommendation.get("branch_exists", False),
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "checkout_allowed": False,
        "merge_allowed": False,
        "push_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "actions_taken": False,
        "forbidden_actions": [
            "branch creation",
            "checkout",
            "merge",
            "push",
            "cleanup",
            "stash",
        ],
    }


def _level_5_project_for_recommendation(
    recommendation: dict[str, Any],
    risk_model: dict[str, Any],
) -> dict[str, Any] | None:
    project_id = recommendation.get("project_id")
    for project in risk_model.get("projects", []):
        if project.get("project_id") == project_id:
            return project
    return None


def _level_5_branch_purpose(recommendation: dict[str, Any]) -> str:
    branch = recommendation.get("suggested_branch") or "recommended branch"
    changed_count = recommendation.get("changed_file_count", 0)
    return (
        f"Isolate {changed_count} changed file"
        f"{'' if changed_count == 1 else 's'} on {branch} for reviewed parallel work."
    )


def _level_5_worktree_recommendation(recommendation: dict[str, Any]) -> dict[str, Any]:
    branch = recommendation.get("suggested_branch") or "cartographer/work"
    target_path = _level_5_worktree_path(recommendation)
    base_head = recommendation.get("base_head")
    return {
        "level": 5,
        "recommendation_version": "cartographer.level_5.worktree_recommendation_contract.v1",
        "recommendation_id": f"worktree-{recommendation.get('recommendation_id')}",
        "source_branch_recommendation_id": recommendation.get("recommendation_id"),
        "project_id": recommendation.get("project_id"),
        "target_path": target_path,
        "branch_proposal": branch,
        "base_branch": recommendation.get("base_branch"),
        "base_head": base_head,
        "owner_required": True,
        "proposed_owner": None,
        "purpose": (
            "Isolate parallel Codex work in a separate worktree after explicit approval."
        ),
        "conflicting_dirty_files": recommendation.get("related_files", []),
        "collision_notes": recommendation.get("collision_notes", []),
        "approval_required": True,
        "status": "preview_only",
        "command_preview": f"git worktree add {target_path} -b {branch} {base_head or 'HEAD'}",
        "rollback_preview": f"git worktree remove {target_path}",
        "worktree_creation_allowed": False,
        "branch_creation_allowed": False,
        "checkout_allowed": False,
        "merge_allowed": False,
        "push_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "actions_taken": False,
        "forbidden_actions": [
            "worktree creation",
            "branch creation",
            "checkout",
            "cleanup",
            "stash",
            "merge",
            "push",
        ],
    }


def _level_5_worktree_path(recommendation: dict[str, Any]) -> str:
    project = str(recommendation.get("project_id") or "project")
    branch = str(recommendation.get("suggested_branch") or "cartographer/work")
    suffix = branch.replace("/", "-").replace("_", "-")
    return f"../{project}-{suffix}"


def _level_5_worker_assignment_previews(
    *,
    risk_model: dict[str, Any],
    worktree_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    recommendations_by_project = {
        recommendation.get("project_id"): recommendation
        for recommendation in worktree_payload.get("recommendations", [])
    }
    previews: list[dict[str, Any]] = []
    for index, project in enumerate(risk_model.get("projects", []), start=1):
        recommendation = recommendations_by_project.get(project.get("project_id"))
        related_files = project.get("changed_files", [])
        collision_status = "blocked_until_isolated" if project.get("risk_level") != "none" else "clear"
        previews.append(
            {
                "worker_id": f"codex-worker-{index}",
                "project_id": project.get("project_id"),
                "branch": project.get("branch"),
                "risk_level": project.get("risk_level"),
                "collision_status": collision_status,
                "related_files": related_files,
                "recommended_isolation": project.get("recommended_isolation"),
                "recommended_worktree_path": recommendation.get("target_path") if recommendation else None,
                "recommended_branch": recommendation.get("branch_proposal") if recommendation else None,
                "assignment_allowed_without_approval": collision_status == "clear",
                "owner_assignment_required": project.get("owner_assignment_required", False),
                "actions_taken": False,
                "branch_creation_allowed": False,
                "worktree_creation_allowed": False,
                "checkout_allowed": False,
            }
        )
    return previews


def _level_5_risk_level(risks: list[dict[str, Any]]) -> str:
    severities = {risk["severity"] for risk in risks}
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    return "none"


def _level_5_worktrees(root: Path | None) -> list[dict[str, Any]]:
    if root is None or not (root / ".git").exists():
        return []
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return [
            {
                "path": str(root),
                "head": None,
                "branch": None,
                "error": "git_worktree_list_timeout",
            }
        ]
    if result.returncode != 0:
        return [
            {
                "path": str(root),
                "head": None,
                "branch": None,
                "error": result.stderr.strip() or "git_worktree_list_failed",
            }
        ]
    worktrees: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in result.stdout.splitlines():
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["path"] = value
        elif key == "HEAD":
            current["head"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
        elif key == "detached":
            current["detached"] = True
    if current:
        worktrees.append(current)
    return worktrees


def _level_4_push_check_blockers(
    proposal: dict[str, Any] | None,
    checks: list[dict[str, Any]],
) -> list[str]:
    if proposal is None:
        return []
    required = list(proposal.get("required_checks", []))
    if not required:
        return []
    if not checks:
        return ["required_checks_missing"]
    by_id = {
        str(check.get("id") or check.get("command")): str(check.get("status")).lower()
        for check in checks
        if isinstance(check, dict) and (check.get("id") or check.get("command"))
    }
    missing = [check_id for check_id in required if check_id not in by_id]
    failed = [
        check_id
        for check_id in required
        if by_id.get(check_id) not in {"passed", "ok", "success"}
    ]
    blockers: list[str] = []
    if missing:
        blockers.append("required_checks_missing")
    if failed:
        blockers.append("required_checks_failed")
    return blockers


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
