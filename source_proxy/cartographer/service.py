from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
from typing import Any

from source_proxy.cartographer.audit_trail import build_audit_trail
from source_proxy.cartographer.autopilot_config import docs_autopilot_config, level_7_autopilot_config
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
from source_proxy.cartographer.component_mapper import build_component_map, map_paths
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


def build_cartographer_level_6_cross_project_status_board() -> dict[str, Any]:
    registry = build_cartographer_level_6_project_registry_hardening()
    health_payload = build_cartographer_project_health()
    health_by_project = {
        project["project_id"]: project
        for project in health_payload["projects"]
    }
    board_items = [
        _level_6_status_board_item(entry, health_by_project.get(entry["project_id"]))
        for entry in registry["registry_entries"]
    ]
    candidate_items = [
        _level_6_candidate_board_item(candidate)
        for candidate in registry["project_candidates"]
    ]
    blockers = sorted(
        {
            blocker
            for item in [*board_items, *candidate_items]
            for blocker in item["blockers"]
        }
    )
    return {
        "status": "observing",
        "level": 6,
        "mode": "cross_project_status_board",
        "contract_version": "cartographer.level_6.cross_project_status_board.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "cross_repo_mutation_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "push_queue_creation_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "automatic_fixes_allowed": False,
        "registry": registry,
        "project_count": len(board_items),
        "candidate_count": len(candidate_items),
        "dirty_project_count": sum(1 for item in board_items if item["dirty"]),
        "blocked_project_count": sum(1 for item in board_items if item["blockers"]),
        "board_items": board_items,
        "candidate_items": candidate_items,
        "blockers": blockers,
        "recommended_next_action": (
            "Review blocked or dirty projects before sequencing cross-project work."
            if blockers
            else "No cross-project blockers detected."
        ),
        "forbidden_actions": [
            "commits",
            "pushes",
            "push queue creation",
            "branch creation",
            "worktree creation",
            "cleanup",
            "merge",
            "stash",
            "automatic fixes",
            "promotion beyond Level 6.2",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_cross_project_status_board"',
        ],
        "next_step": "Level 6.3 may add component ownership only after Britton approves it.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_6_component_ownership_assignment() -> dict[str, Any]:
    status_board = build_cartographer_level_6_cross_project_status_board()
    components_payload = build_cartographer_components()
    changed_by_component = {
        component["component_id"]: component
        for component in components_payload["changed_components"]
    }
    ownership_items = [
        _level_6_component_ownership_item(
            component,
            changed_component=changed_by_component.get(component["component_id"]),
            status_board=status_board,
        )
        for component in components_payload["components"]
    ]
    conflict_items = [
        item
        for item in ownership_items
        if item["changed"] and item["owner"] is None
    ]
    return {
        "status": "observing",
        "level": 6,
        "mode": "component_ownership_agent_assignment",
        "contract_version": "cartographer.level_6.component_ownership_agent_assignment.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "assignment_write_allowed": False,
        "automatic_reassignment_allowed": False,
        "cross_repo_mutation_allowed": False,
        "repo_mutation_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "component_count": len(ownership_items),
        "unassigned_component_count": sum(1 for item in ownership_items if item["owner"] is None),
        "changed_component_count": len(changed_by_component),
        "conflict_count": len(conflict_items),
        "ownership_items": ownership_items,
        "conflicts": conflict_items,
        "status_board": status_board,
        "forbidden_actions": [
            "repo mutation",
            "branch creation",
            "worktree creation",
            "push",
            "merge",
            "cleanup",
            "autonomous reassignment",
            "promotion beyond Level 6.3",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_component_ownership"',
        ],
        "next_step": "Level 6.4 may classify cross-repo dirty trees only after Britton approves it.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_6_cross_repo_dirty_tree_classifier() -> dict[str, Any]:
    registry = build_cartographer_level_6_project_registry_hardening()
    statuses = read_git_statuses()
    if not statuses:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            statuses = [read_git_status_for_project(project_id=cwd.name.lower(), root=cwd)]
    status_by_project = {
        status.project_id: status
        for status in statuses
        if status.project_id
    }
    classifications = [
        _level_6_project_dirty_classification(
            entry,
            status_by_project.get(entry["project_id"]),
        )
        for entry in registry["registry_entries"]
    ]
    dirty_projects = [item for item in classifications if item["dirty"]]
    blocking_projects = [item for item in classifications if item["blocks_cross_repo_sequence"]]
    forbidden_files = [
        file
        for item in classifications
        for file in item["forbidden_files"]
    ]
    unclassified_files = [
        file
        for item in classifications
        for file in item["unclassified_files"]
    ]
    return {
        "status": "observing",
        "level": 6,
        "mode": "cross_repo_dirty_tree_classifier",
        "contract_version": "cartographer.level_6.cross_repo_dirty_tree_classifier.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "staging_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "cross_repo_fixes_allowed": False,
        "registry": registry,
        "project_count": len(classifications),
        "dirty_project_count": len(dirty_projects),
        "blocking_project_count": len(blocking_projects),
        "forbidden_file_count": len(forbidden_files),
        "unclassified_file_count": len(unclassified_files),
        "classifications": classifications,
        "forbidden_files": forbidden_files,
        "unclassified_files": unclassified_files,
        "recommended_sequence": [
            {
                "project_id": item["project_id"],
                "recommended_next_action": item["recommended_next_action"],
                "sequencing_status": item["sequencing_status"],
            }
            for item in classifications
        ],
        "forbidden_actions": [
            "staging",
            "committing",
            "pushing",
            "branch creation",
            "worktree creation",
            "cleanup",
            "merge",
            "stash",
            "cross-repo fixes",
            "promotion beyond Level 6.4",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_cross_repo_dirty_tree"',
        ],
        "next_step": "Level 6.5 may add a multi-project closeout dashboard only after Britton approves it.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_6_multi_project_closeout_dashboard() -> dict[str, Any]:
    status_board = build_cartographer_level_6_cross_project_status_board()
    ownership = build_cartographer_level_6_component_ownership_assignment()
    dirty_classifier = build_cartographer_level_6_cross_repo_dirty_tree_classifier()
    closeout_items = [
        _level_6_closeout_item(
            board_item,
            ownership=ownership,
            dirty_classifier=dirty_classifier,
        )
        for board_item in status_board["board_items"]
    ]
    dashboard_blockers = sorted(
        {
            blocker
            for item in closeout_items
            for blocker in item["blockers"]
        }
    )
    ready_count = sum(1 for item in closeout_items if item["closeout_status"] == "ready_for_review")
    blocked_count = len(closeout_items) - ready_count
    return {
        "status": "observing",
        "level": 6,
        "mode": "multi_project_closeout_dashboard",
        "contract_version": "cartographer.level_6.multi_project_closeout_dashboard.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "commit_allowed": False,
        "push_allowed": False,
        "push_queue_creation_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "automatic_promotion_allowed": False,
        "automatic_execution_allowed": False,
        "project_count": len(closeout_items),
        "ready_project_count": ready_count,
        "blocked_project_count": blocked_count,
        "dashboard_blockers": dashboard_blockers,
        "closeout_items": closeout_items,
        "status_board": status_board,
        "ownership": ownership,
        "dirty_classifier": dirty_classifier,
        "next_approved_increment": "Level 7+: Future Limited Autopilot, disabled by default",
        "recommended_next_action": (
            "Resolve closeout blockers before any future Level 7 autopilot discussion."
            if dashboard_blockers
            else "Level 6 closeout is ready for human review; Level 7 remains disabled by default."
        ),
        "forbidden_actions": [
            "commits",
            "pushes",
            "queue creation",
            "branch creation",
            "worktree creation",
            "cleanup",
            "merge",
            "stash",
            "automatic promotion",
            "automatic execution",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_multi_project_closeout"',
        ],
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_7_disabled_by_default() -> dict[str, Any]:
    config = level_7_autopilot_config()
    return {
        "status": "observing",
        "level": 7,
        "mode": "disabled_by_default_feature_flag",
        "contract_version": "cartographer.level_7.disabled_by_default_feature_flag.v1",
        "feature_flag": {
            "name": "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED",
            "default": False,
            "requested": config["level_7_autopilot_requested"],
            "enabled": config["level_7_autopilot_enabled"],
            "kill_switch_name": "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH",
            "kill_switch_default": True,
            "kill_switch_active": config["level_7_autopilot_kill_switch"],
            "mode": config["level_7_autopilot_mode"],
        },
        "level_7_autopilot_enabled": config["level_7_autopilot_enabled"],
        "level_7_autopilot_requested": config["level_7_autopilot_requested"],
        "level_7_autopilot_kill_switch": config["level_7_autopilot_kill_switch"],
        "level_7_autopilot_action_available": False,
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "recommendation_contract_available": False,
        "dry_run_action_packet_builder_available": False,
        "exact_approval_handshake_available": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "push_queue_creation_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "forbidden_actions": [
            "push",
            "push queue creation",
            "branch creation",
            "worktree creation",
            "cleanup",
            "stash",
            "merge",
            "automatic commit",
            "automatic execution",
            "automatic promotion",
            "self-approval",
            "Level 7.2 recommendations",
            "Level 7.3 dry-run action packets",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"',
        ],
        "next_step": "Level 7.2 may define recommendations only after Level 7.1 is closed out and explicitly approved.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_7_next_safe_action() -> dict[str, Any]:
    disabled_state = build_cartographer_level_7_disabled_by_default()
    closeout = build_cartographer_level_6_multi_project_closeout_dashboard()
    blockers = _level_7_next_safe_action_blockers(
        disabled_state=disabled_state,
        closeout=closeout,
    )
    return {
        "status": "observing",
        "level": 7,
        "mode": "next_safe_action_recommendation",
        "contract_version": "cartographer.level_7.next_safe_action_recommendation.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "recommendation_only": True,
        "recommendation_contract_available": True,
        "dry_run_action_packet_builder_available": False,
        "exact_approval_handshake_available": False,
        "level_7_autopilot_enabled": disabled_state["level_7_autopilot_enabled"],
        "level_7_autopilot_action_available": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "push_queue_creation_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "blockers": blockers,
        "next_safe_action": _level_7_next_safe_action_title(blockers),
        "next_safe_action_status": "blocked" if blockers else "available_for_human_review",
        "recommendation": {
            "action_id": "level_7_next_safe_action_review",
            "title": _level_7_next_safe_action_title(blockers),
            "status": "blocked" if blockers else "available_for_human_review",
            "operator_action_required": True,
            "cartographer_may_execute": False,
            "cartographer_may_create_dry_run_packet": False,
            "evidence": [
                "docs/cartographer-level-7-autopilot-boundary-contract.md",
                "docs/cartographer-level-7-disabled-by-default-feature-flag.md",
                "source_proxy/tests/test_cartographer_api.py",
            ],
            "reason": _level_7_next_safe_action_reason(blockers),
        },
        "forbidden_actions": [
            "push",
            "push queue creation",
            "branch creation",
            "worktree creation",
            "cleanup",
            "stash",
            "merge",
            "automatic commit",
            "automatic execution",
            "automatic promotion",
            "self-approval",
            "dry-run action packet creation",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"',
        ],
        "next_step": "Level 7.3 may build dry-run action packets only after Level 7.2 is closed out and explicitly approved.",
        "disabled_state": disabled_state,
        "level_6_closeout": closeout,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_7_dry_run_action_packet() -> dict[str, Any]:
    recommendation = build_cartographer_level_7_next_safe_action()
    packet = _level_7_dry_run_action_packet(recommendation)
    return {
        "status": "observing",
        "level": 7,
        "mode": "dry_run_action_packet_builder",
        "contract_version": "cartographer.level_7.dry_run_action_packet_builder.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "recommendation_contract_available": True,
        "dry_run_action_packet_builder_available": True,
        "exact_approval_handshake_available": False,
        "level_7_autopilot_enabled": recommendation["level_7_autopilot_enabled"],
        "level_7_autopilot_action_available": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "push_queue_creation_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "packet_count": 1,
        "packets": [packet],
        "packet": packet,
        "blockers": packet["blockers"],
        "forbidden_actions": packet["forbidden_actions"],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_dry_run_action_packet or level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"',
        ],
        "next_step": "Level 7.4 may define an exact approval handshake only after Level 7.3 is closed out and explicitly approved.",
        "recommendation": recommendation,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_7_exact_approval_handshake(
    *,
    packet_id: str,
    approval_id: str | None,
    approved_by: str | None,
    exact_allowed_files: list[str],
    exact_forbidden_actions: list[str],
    exact_manual_check_commands: list[str],
    approved_at: str | None,
) -> dict[str, Any]:
    packet_payload = build_cartographer_level_7_dry_run_action_packet()
    packet = packet_payload["packet"]
    blockers = _level_7_exact_approval_blockers(
        packet=packet,
        packet_id=packet_id,
        approval_id=approval_id,
        approved_by=approved_by,
        exact_allowed_files=exact_allowed_files,
        exact_forbidden_actions=exact_forbidden_actions,
        exact_manual_check_commands=exact_manual_check_commands,
        approved_at=approved_at,
    )
    return {
        "status": "approval_preview",
        "level": 7,
        "mode": "exact_approval_handshake_preview",
        "approval_version": "cartographer.level_7.exact_approval_handshake_preview.v1",
        "packet_id": packet_id,
        "packet_found": packet_id == packet["packet_id"],
        "approval_id": approval_id,
        "approved_by": approved_by,
        "approved_at": approved_at,
        "blockers": blockers,
        "execution_blockers": ["level_7_execution_not_implemented"],
        "approval_preview_valid": not blockers,
        "approval_handshake_available": True,
        "execution_available": False,
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "push_queue_creation_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "validated_fields": {
            "exact_packet_id": packet_id == packet["packet_id"],
            "approval_id_present": bool(approval_id),
            "approved_by_present": bool(approved_by),
            "approved_at_present": bool(approved_at),
            "allowed_files_exact": exact_allowed_files == packet["allowed_files"],
            "forbidden_actions_exact": exact_forbidden_actions == packet["forbidden_actions"],
            "manual_check_commands_exact": (
                exact_manual_check_commands == packet["manual_check_commands"]
            ),
            "self_approval_blocked": _level_7_is_self_approval(approved_by),
        },
        "forbidden_actions": [
            "execution",
            "push",
            "push queue creation",
            "branch creation",
            "worktree creation",
            "cleanup",
            "stash",
            "merge",
            "automatic commit",
            "automatic execution",
            "automatic promotion",
            "self-approval",
        ],
        "packet": packet,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_7_closeout_dashboard() -> dict[str, Any]:
    disabled_state = build_cartographer_level_7_disabled_by_default()
    recommendation = build_cartographer_level_7_next_safe_action()
    dry_run = build_cartographer_level_7_dry_run_action_packet()
    packet = dry_run["packet"]
    approval_preview = build_cartographer_level_7_exact_approval_handshake(
        packet_id=packet["packet_id"],
        approval_id="level-7-closeout-preview",
        approved_by="human-operator",
        exact_allowed_files=packet["allowed_files"],
        exact_forbidden_actions=packet["forbidden_actions"],
        exact_manual_check_commands=packet["manual_check_commands"],
        approved_at="2026-05-20T00:00:00Z",
    )
    closeout_items = [
        _level_7_closeout_item(
            "Level 7.1",
            "Disabled-By-Default Feature Flag",
            disabled_state,
            "feature_flag_locked",
        ),
        _level_7_closeout_item(
            "Level 7.2",
            "Next Safe Action Recommendation Contract",
            recommendation,
            "recommendation_only",
        ),
        _level_7_closeout_item(
            "Level 7.3",
            "Dry-Run Action Packet Builder",
            dry_run,
            "dry_run_only",
        ),
        _level_7_closeout_item(
            "Level 7.4",
            "Exact Approval Handshake Contract",
            approval_preview,
            "approval_preview_only",
        ),
    ]
    closeout_blockers = sorted(
        {
            blocker
            for item in closeout_items
            for blocker in item["blockers"]
        }
    )
    return {
        "status": "observing",
        "level": 7,
        "mode": "level_7_closeout_dashboard",
        "contract_version": "cartographer.level_7.closeout_dashboard.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "level_7_closed_out": not closeout_blockers,
        "level_8_gated": True,
        "level_8_may_begin": False,
        "operator_approval_required_for_level_8": True,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "push_queue_creation_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "closeout_items": closeout_items,
        "closeout_blockers": closeout_blockers,
        "disabled_state": disabled_state,
        "recommendation": recommendation,
        "dry_run": dry_run,
        "approval_preview": approval_preview,
        "recommended_next_action": (
            "Request explicit human approval before starting Level 8.0."
            if not closeout_blockers
            else "Resolve Level 7 closeout blockers before any Level 8 discussion."
        ),
        "forbidden_actions": [
            "push",
            "push queue creation",
            "branch creation",
            "worktree creation",
            "cleanup",
            "stash",
            "merge",
            "automatic commit",
            "automatic execution",
            "automatic promotion",
            "self-approval",
            "Level 8 work without explicit approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_closeout_dashboard or level_7_exact_approval_handshake or level_7_dry_run_action_packet or level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"',
        ],
        "next_step": "Level 8.0 may begin only after explicit human approval.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_8_workflow_run_card() -> dict[str, Any]:
    level_7_closeout = build_cartographer_level_7_closeout_dashboard()
    steps = [
        _level_8_workflow_step_card(
            step_id="level-8-step-1-review-level-7-closeout",
            title="Review Level 7 closeout dashboard",
            source="cartographer.level_7.closeout_dashboard.v1",
            blockers=[] if level_7_closeout["level_7_closed_out"] else ["level_7_not_closed_out"],
        ),
        _level_8_workflow_step_card(
            step_id="level-8-step-2-confirm-workflow-boundary",
            title="Confirm Level 8 workflow runner boundary",
            source="docs/cartographer-level-8-workflow-runner-boundary-contract.md",
            blockers=[],
        ),
        _level_8_workflow_step_card(
            step_id="level-8-step-3-plan-step-approval-contract",
            title="Plan Step Approval UI/API Contract",
            source="Level 8.2 future increment",
            blockers=["level_8_2_not_approved"],
        ),
    ]
    workflow_blockers = sorted(
        {
            blocker
            for step in steps
            for blocker in step["blockers"]
        }
    )
    return {
        "status": "observing",
        "level": 8,
        "mode": "workflow_run_card_model",
        "contract_version": "cartographer.level_8.workflow_run_card_model.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "workflow_run_card_available": True,
        "step_approval_contract_available": False,
        "receipt_journal_available": False,
        "background_execution_allowed": False,
        "autonomous_retry_allowed": False,
        "cross_project_mutation_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "workflow": {
            "workflow_id": "cartographer.level_8.workflow_run_card.v1",
            "title": "Level 8 controlled workflow preview",
            "status": "blocked" if workflow_blockers else "ready_for_human_review",
            "human_approval_required_per_step": True,
            "cartographer_may_execute_steps": False,
            "background_execution_allowed": False,
            "autonomous_retry_allowed": False,
            "receipt_journal_required_before_execution": True,
            "steps": steps,
            "blockers": workflow_blockers,
        },
        "step_count": len(steps),
        "blocked_step_count": sum(1 for step in steps if step["blockers"]),
        "blockers": workflow_blockers,
        "forbidden_actions": [
            "execution",
            "background execution",
            "autonomous retry loops",
            "hidden receipt writes",
            "cross-project mutation",
            "push",
            "merge",
            "branch creation",
            "worktree creation",
            "cleanup",
            "stash",
            "automatic commit",
            "automatic promotion",
            "self-approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_workflow_run_card or level_7_closeout_dashboard or level_6_multi_project_closeout"',
        ],
        "next_step": "Level 8.2 may define step approval UI/API only after Level 8.1 is closed out and explicitly approved.",
        "level_7_closeout": level_7_closeout,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_8_step_approval_preview(
    *,
    workflow_id: str,
    step_id: str,
    approval_id: str | None,
    approved_by: str | None,
    exact_step_title: str,
    exact_manual_check_commands: list[str],
    approved_at: str | None,
) -> dict[str, Any]:
    workflow_payload = build_cartographer_level_8_workflow_run_card()
    workflow = workflow_payload["workflow"]
    step = next((item for item in workflow["steps"] if item["step_id"] == step_id), None)
    blockers = _level_8_step_approval_blockers(
        workflow=workflow,
        step=step,
        workflow_id=workflow_id,
        approval_id=approval_id,
        approved_by=approved_by,
        exact_step_title=exact_step_title,
        exact_manual_check_commands=exact_manual_check_commands,
        approved_at=approved_at,
    )
    return {
        "status": "approval_preview",
        "level": 8,
        "mode": "step_approval_contract_preview",
        "approval_version": "cartographer.level_8.step_approval_contract_preview.v1",
        "workflow_id": workflow_id,
        "workflow_found": workflow_id == workflow["workflow_id"],
        "step_id": step_id,
        "step_found": step is not None,
        "approval_id": approval_id,
        "approved_by": approved_by,
        "approved_at": approved_at,
        "blockers": blockers,
        "approval_preview_valid": not blockers,
        "step_approval_contract_available": True,
        "receipt_journal_available": False,
        "execution_available": False,
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "background_execution_allowed": False,
        "autonomous_retry_allowed": False,
        "cross_project_mutation_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "validated_fields": {
            "exact_workflow_id": workflow_id == workflow["workflow_id"],
            "exact_step_id": step is not None,
            "approval_id_present": bool(approval_id),
            "approved_by_present": bool(approved_by),
            "approved_at_present": bool(approved_at),
            "step_title_exact": bool(step and exact_step_title == step["title"]),
            "manual_check_commands_exact": (
                exact_manual_check_commands == workflow_payload["manual_checks"]
            ),
            "self_approval_blocked": _level_7_is_self_approval(approved_by),
        },
        "execution_blockers": ["level_8_step_execution_not_implemented"],
        "forbidden_actions": [
            "step execution",
            "background execution",
            "autonomous retry loops",
            "receipt journal writes",
            "cross-project mutation",
            "push",
            "merge",
            "branch creation",
            "worktree creation",
            "cleanup",
            "stash",
            "automatic commit",
            "automatic promotion",
            "self-approval",
        ],
        "workflow": workflow,
        "step": step,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_8_receipt_journal() -> dict[str, Any]:
    workflow_payload = build_cartographer_level_8_workflow_run_card()
    workflow = workflow_payload["workflow"]
    first_step = workflow["steps"][0]
    approval_preview = build_cartographer_level_8_step_approval_preview(
        workflow_id=workflow["workflow_id"],
        step_id=first_step["step_id"],
        approval_id="level-8-receipt-preview",
        approved_by="human-operator",
        exact_step_title=first_step["title"],
        exact_manual_check_commands=workflow_payload["manual_checks"],
        approved_at="2026-05-20T00:00:00Z",
    )
    entries = [
        _level_8_receipt_journal_entry(
            event_id="level-8-receipt-001",
            event_type="workflow_proposed",
            status="recorded_preview",
            source_id=workflow["workflow_id"],
            evidence=[
                "docs/cartographer-level-8-workflow-run-card-model.md",
                "source_proxy/tests/test_cartographer_api.py",
            ],
        ),
        _level_8_receipt_journal_entry(
            event_id="level-8-receipt-002",
            event_type="step_approval_previewed",
            status="recorded_preview",
            source_id=first_step["step_id"],
            evidence=[
                "docs/cartographer-level-8-step-approval-contract.md",
                "source_proxy/tests/test_cartographer_api.py",
            ],
        ),
    ]
    return {
        "status": "observing",
        "level": 8,
        "mode": "receipt_journal_evidence_trail",
        "contract_version": "cartographer.level_8.receipt_journal_evidence_trail.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "receipt_journal_available": True,
        "receipt_journal_write_allowed": False,
        "hidden_receipt_writes_allowed": False,
        "step_approval_contract_available": True,
        "execution_available": False,
        "background_execution_allowed": False,
        "autonomous_retry_allowed": False,
        "cross_project_mutation_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "journal": {
            "journal_id": "cartographer.level_8.receipt_journal.preview.v1",
            "status": "preview_only",
            "visible_to_operator": True,
            "persisted": False,
            "hidden_writes_allowed": False,
            "entry_count": len(entries),
            "entries": entries,
        },
        "entry_count": len(entries),
        "entries": entries,
        "workflow": workflow,
        "approval_preview": approval_preview,
        "forbidden_actions": [
            "receipt journal writes",
            "hidden receipt writes",
            "step execution",
            "background execution",
            "autonomous retry loops",
            "cross-project mutation",
            "push",
            "merge",
            "branch creation",
            "worktree creation",
            "cleanup",
            "stash",
            "automatic commit",
            "automatic promotion",
            "self-approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_receipt_journal or level_8_step_approval or level_8_workflow_run_card"',
        ],
        "next_step": "Level 8.4 may define cancel, stop, and failed-step handling only after Level 8.3 is closed out and explicitly approved.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_8_stop_failure_handling() -> dict[str, Any]:
    journal_payload = build_cartographer_level_8_receipt_journal()
    workflow = journal_payload["workflow"]
    first_step = workflow["steps"][0]
    stopped_states = [
        _level_8_stopped_state(
            state_id="level-8-canceled-step",
            status="canceled",
            step_id=first_step["step_id"],
            reason="Human canceled the step before execution.",
        ),
        _level_8_stopped_state(
            state_id="level-8-failed-step",
            status="failed",
            step_id=first_step["step_id"],
            reason="Manual check failed or blocker appeared.",
        ),
        _level_8_stopped_state(
            state_id="level-8-blocked-step",
            status="blocked",
            step_id=workflow["steps"][-1]["step_id"],
            reason="Future Level 8.5 closeout is not approved.",
        ),
    ]
    return {
        "status": "observing",
        "level": 8,
        "mode": "cancel_stop_failed_step_handling",
        "contract_version": "cartographer.level_8.cancel_stop_failed_step_handling.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "stop_handling_available": True,
        "receipt_journal_available": True,
        "execution_available": False,
        "workflow_continuation_allowed": False,
        "human_review_required_to_continue": True,
        "background_execution_allowed": False,
        "autonomous_retry_allowed": False,
        "cross_project_mutation_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "stopped_state_count": len(stopped_states),
        "stopped_states": stopped_states,
        "journal": journal_payload["journal"],
        "workflow": workflow,
        "forbidden_actions": [
            "workflow continuation without human review",
            "step execution",
            "background execution",
            "autonomous retry loops",
            "receipt journal writes",
            "cross-project mutation",
            "push",
            "merge",
            "branch creation",
            "worktree creation",
            "cleanup",
            "stash",
            "automatic commit",
            "automatic promotion",
            "self-approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_cancel_stop_failed_step or level_8_receipt_journal or level_8_step_approval"',
        ],
        "next_step": "Level 8.5 may add closeout smoke only after Level 8.4 is closed out and explicitly approved.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_8_closeout_smoke() -> dict[str, Any]:
    workflow = build_cartographer_level_8_workflow_run_card()
    approval = build_cartographer_level_8_step_approval_preview(
        workflow_id=workflow["workflow"]["workflow_id"],
        step_id=workflow["workflow"]["steps"][0]["step_id"],
        approval_id="level-8-closeout-preview",
        approved_by="human-operator",
        exact_step_title=workflow["workflow"]["steps"][0]["title"],
        exact_manual_check_commands=workflow["manual_checks"],
        approved_at="2026-05-20T00:00:00Z",
    )
    journal = build_cartographer_level_8_receipt_journal()
    stop_failure = build_cartographer_level_8_stop_failure_handling()
    closeout_items = [
        _level_8_closeout_item("Level 8.1", "Workflow Run Card Model", workflow),
        _level_8_closeout_item("Level 8.2", "Step Approval UI/API Contract", approval),
        _level_8_closeout_item("Level 8.3", "Receipt Journal And Evidence Trail", journal),
        _level_8_closeout_item("Level 8.4", "Cancel, Stop, And Failed-Step Handling", stop_failure),
    ]
    blockers = sorted({blocker for item in closeout_items for blocker in item["blockers"]})
    return {
        "status": "observing",
        "level": 8,
        "mode": "level_8_closeout_smoke",
        "contract_version": "cartographer.level_8.closeout_smoke.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "level_8_closed_out": not blockers,
        "level_9_gated": True,
        "level_9_may_begin": False,
        "operator_approval_required_for_level_9": True,
        "execution_available": False,
        "background_execution_allowed": False,
        "autonomous_retry_allowed": False,
        "cross_project_mutation_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "closeout_items": closeout_items,
        "closeout_blockers": blockers,
        "workflow": workflow,
        "approval_preview": approval,
        "journal": journal,
        "stop_failure": stop_failure,
        "recommended_next_action": (
            "Request explicit human approval before starting Level 9.0."
            if not blockers
            else "Resolve Level 8 closeout blockers before any Level 9 discussion."
        ),
        "forbidden_actions": [
            "Level 9 work without explicit approval",
            "step execution",
            "background execution",
            "autonomous retry loops",
            "receipt journal writes",
            "cross-project mutation",
            "push",
            "merge",
            "branch creation",
            "worktree creation",
            "cleanup",
            "stash",
            "automatic commit",
            "automatic promotion",
            "self-approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_closeout_smoke or level_8_cancel_stop_failed_step or level_8_receipt_journal or level_8_step_approval or level_8_workflow_run_card"',
        ],
        "next_step": "Level 9.0 may begin only after explicit human approval.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_9_worker_registry() -> dict[str, Any]:
    level_8_closeout = build_cartographer_level_8_closeout_smoke()
    workers = [
        _level_9_worker_registry_entry(
            worker_id="codex-primary",
            task_id="cartographer-level-9-worker-registry",
            branch="main",
            allowed_files=[
                "docs/cartographer-level-9-worker-registry-assignment-model.md",
                "source_proxy/cartographer/service.py",
                "source_proxy/api/cartographer.py",
                "source_proxy/tests/test_cartographer_api.py",
            ],
            owner="human-operator",
        )
    ]
    assignment_blockers = sorted(
        {
            blocker
            for worker in workers
            for blocker in worker["blockers"]
        }
    )
    return {
        "status": "observing",
        "level": 9,
        "mode": "worker_registry_assignment_model",
        "contract_version": "cartographer.level_9.worker_registry_assignment_model.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "worker_registry_available": True,
        "assignment_model_available": True,
        "assignment_write_allowed": False,
        "automatic_reassignment_allowed": False,
        "force_overwrite_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "cross_project_mutation_allowed": False,
        "worker_count": len(workers),
        "assignment_count": len([worker for worker in workers if worker["task_id"]]),
        "blocked_worker_count": len([worker for worker in workers if worker["blockers"]]),
        "workers": workers,
        "assignments": [
            {
                "worker_id": worker["worker_id"],
                "task_id": worker["task_id"],
                "branch": worker["branch"],
                "allowed_files": worker["allowed_files"],
                "assignment_status": worker["assignment_status"],
                "actions_taken": False,
            }
            for worker in workers
        ],
        "blockers": assignment_blockers,
        "forbidden_actions": [
            "assignment writes",
            "automatic reassignment",
            "force overwrite",
            "branch creation",
            "worktree creation",
            "commit",
            "push",
            "merge",
            "cleanup",
            "stash",
            "automatic execution",
            "automatic promotion",
            "self-approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_worker_registry or level_8_closeout_smoke"',
        ],
        "next_step": "Level 9.2 may define one worker, one task, one branch rules only after Level 9.1 is closed out and explicitly approved.",
        "level_8_closeout": level_8_closeout,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_9_one_worker_rule() -> dict[str, Any]:
    registry = build_cartographer_level_9_worker_registry()
    rule_items = [_level_9_one_worker_rule_item(worker) for worker in registry["workers"]]
    blockers = sorted({blocker for item in rule_items for blocker in item["blockers"]})
    return {
        "status": "observing",
        "level": 9,
        "mode": "one_worker_one_task_one_branch_rule",
        "contract_version": "cartographer.level_9.one_worker_one_task_one_branch_rule.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "rule_model_available": True,
        "recommendation_only": True,
        "assignment_write_allowed": False,
        "automatic_reassignment_allowed": False,
        "force_overwrite_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "checkout_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "cross_project_mutation_allowed": False,
        "worker_count": len(rule_items),
        "rule_violation_count": sum(1 for item in rule_items if item["blockers"]),
        "rule_items": rule_items,
        "blockers": blockers,
        "forbidden_actions": [
            "branch creation",
            "branch checkout",
            "worktree creation",
            "assignment writes",
            "automatic reassignment",
            "force overwrite",
            "commit",
            "push",
            "merge",
            "cleanup",
            "stash",
            "automatic execution",
            "automatic promotion",
            "self-approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_one_worker_one_task_one_branch or level_9_worker_registry"',
        ],
        "next_step": "Level 9.3 may define allowed-file conflict checking only after Level 9.2 is closed out and explicitly approved.",
        "registry": registry,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_9_allowed_file_conflict_checker() -> dict[str, Any]:
    rule_payload = build_cartographer_level_9_one_worker_rule()
    workers = [
        *rule_payload["registry"]["workers"],
        _level_9_worker_registry_entry(
            worker_id="codex-sidecar",
            task_id="cartographer-level-9-conflict-review",
            branch="main",
            allowed_files=[
                "source_proxy/cartographer/service.py",
                "docs/cartographer-level-9-allowed-file-conflict-checker.md",
            ],
            owner="human-operator",
        ),
    ]
    conflicts = _level_9_allowed_file_conflicts(workers)
    blockers = ["allowed_file_conflicts_present"] if conflicts else []
    return {
        "status": "observing",
        "level": 9,
        "mode": "allowed_file_conflict_checker",
        "contract_version": "cartographer.level_9.allowed_file_conflict_checker.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "conflict_checker_available": True,
        "recommendation_only": True,
        "parallel_work_suggestion_allowed": not conflicts,
        "assignment_write_allowed": False,
        "automatic_reassignment_allowed": False,
        "force_overwrite_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "checkout_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "cross_project_mutation_allowed": False,
        "worker_count": len(workers),
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "blockers": blockers,
        "workers": workers,
        "forbidden_actions": [
            "force overwrite",
            "automatic reassignment",
            "branch creation",
            "worktree creation",
            "checkout",
            "commit",
            "push",
            "merge",
            "cleanup",
            "stash",
            "automatic execution",
            "automatic promotion",
            "self-approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_allowed_file_conflict_checker or level_9_one_worker_one_task_one_branch"',
        ],
        "next_step": "Level 9.4 may define branch/worktree proposal queues only after Level 9.3 is closed out and explicitly approved.",
        "rule_payload": rule_payload,
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_9_branch_worktree_proposal_queue() -> dict[str, Any]:
    conflict_payload = build_cartographer_level_9_allowed_file_conflict_checker()
    proposals = [
        _level_9_branch_worktree_proposal(
            proposal_id="cartographer-level-9-branch-worktree-proposal-001",
            worker_id="codex-primary",
            task_id="cartographer-level-9-worker-registry",
            proposed_branch="cartographer/level-9-worker-registry",
            proposed_worktree="../SpiritOS-cartographer-level-9-worker-registry",
            blockers=conflict_payload["blockers"],
        )
    ]
    blockers = sorted({blocker for proposal in proposals for blocker in proposal["blockers"]})
    return {
        "status": "observing",
        "level": 9,
        "mode": "branch_worktree_proposal_queue",
        "contract_version": "cartographer.level_9.branch_worktree_proposal_queue.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "proposal_queue_available": True,
        "recommendation_only": True,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "checkout_allowed": False,
        "branch_created": False,
        "worktree_created": False,
        "assignment_write_allowed": False,
        "automatic_reassignment_allowed": False,
        "force_overwrite_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "cross_project_mutation_allowed": False,
        "proposal_count": len(proposals),
        "blocked_proposal_count": sum(1 for proposal in proposals if proposal["blockers"]),
        "proposals": proposals,
        "blockers": blockers,
        "conflict_payload": conflict_payload,
        "forbidden_actions": [
            "automatic branch creation",
            "automatic worktree creation",
            "checkout",
            "cleanup",
            "stash",
            "commit",
            "push",
            "merge",
            "force overwrite",
            "automatic reassignment",
            "automatic execution",
            "automatic promotion",
            "self-approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_branch_worktree_proposal_queue or level_9_allowed_file_conflict_checker"',
        ],
        "next_step": "Level 9.5 may define stale worker detection only after Level 9.4 is closed out and explicitly approved.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_9_stale_worker_closeout_packet() -> dict[str, Any]:
    proposal_queue = build_cartographer_level_9_branch_worktree_proposal_queue()
    stale_workers = [
        _level_9_stale_worker_packet(
            worker_id="codex-sidecar",
            task_id="cartographer-level-9-conflict-review",
            stale_reason="allowed_file_conflict_blocks_parallel_work",
            recommended_action="human_review_before_closeout",
        )
    ]
    return {
        "status": "observing",
        "level": 9,
        "mode": "stale_worker_detection_closeout_packet",
        "contract_version": "cartographer.level_9.stale_worker_detection_closeout_packet.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "stale_worker_detection_available": True,
        "closeout_packet_available": True,
        "closeout_execution_allowed": False,
        "automatic_reassignment_allowed": False,
        "automatic_closeout_allowed": False,
        "branch_deletion_allowed": False,
        "worktree_deletion_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "force_overwrite_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "stale_worker_count": len(stale_workers),
        "closeout_packet_count": len(stale_workers),
        "stale_workers": stale_workers,
        "closeout_packets": stale_workers,
        "proposal_queue": proposal_queue,
        "forbidden_actions": [
            "automatic reassignment",
            "automatic closeout",
            "branch deletion",
            "worktree deletion",
            "cleanup",
            "stash",
            "commit",
            "push",
            "merge",
            "force overwrite",
            "branch creation",
            "worktree creation",
            "automatic execution",
            "automatic promotion",
            "self-approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_stale_worker_closeout_packet or level_9_branch_worktree_proposal_queue"',
        ],
        "next_step": "Level 9.6 may add the coordination dashboard only after Level 9.5 is closed out and explicitly approved.",
        "safety": cartographer_safety_manifest(),
    }


def build_cartographer_level_9_coordination_dashboard() -> dict[str, Any]:
    registry = build_cartographer_level_9_worker_registry()
    one_worker_rule = build_cartographer_level_9_one_worker_rule()
    conflict_checker = build_cartographer_level_9_allowed_file_conflict_checker()
    proposal_queue = build_cartographer_level_9_branch_worktree_proposal_queue()
    stale_worker = build_cartographer_level_9_stale_worker_closeout_packet()
    closeout_items = [
        _level_9_coordination_dashboard_item(
            "Level 9.1",
            "Worker Registry And Assignment Model",
            registry,
        ),
        _level_9_coordination_dashboard_item(
            "Level 9.2",
            "One Worker One Task One Branch Rule",
            one_worker_rule,
        ),
        _level_9_coordination_dashboard_item(
            "Level 9.3",
            "Allowed-File Conflict Checker",
            conflict_checker,
        ),
        _level_9_coordination_dashboard_item(
            "Level 9.4",
            "Branch And Worktree Proposal Queue",
            proposal_queue,
        ),
        _level_9_coordination_dashboard_item(
            "Level 9.5",
            "Stale Worker Detection And Closeout Packet",
            stale_worker,
        ),
    ]
    blockers = sorted({blocker for item in closeout_items for blocker in item["blockers"]})
    return {
        "status": "observing",
        "level": 9,
        "mode": "coordination_dashboard",
        "contract_version": "cartographer.level_9.coordination_dashboard.v1",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "coordination_dashboard_available": True,
        "recommendation_only": True,
        "level_9_closed_out": not blockers,
        "level_10_gated": True,
        "level_10_may_begin": False,
        "operator_approval_required_for_level_10": True,
        "assignment_write_allowed": False,
        "automatic_reassignment_allowed": False,
        "force_overwrite_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "checkout_allowed": False,
        "branch_deletion_allowed": False,
        "worktree_deletion_allowed": False,
        "cleanup_allowed": False,
        "stash_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "automatic_execution_allowed": False,
        "automatic_promotion_allowed": False,
        "self_approval_allowed": False,
        "cross_project_mutation_allowed": False,
        "worker_count": registry["worker_count"],
        "conflict_count": conflict_checker["conflict_count"],
        "proposal_count": proposal_queue["proposal_count"],
        "stale_worker_count": stale_worker["stale_worker_count"],
        "closeout_items": closeout_items,
        "closeout_blockers": blockers,
        "registry": registry,
        "one_worker_rule": one_worker_rule,
        "conflict_checker": conflict_checker,
        "proposal_queue": proposal_queue,
        "stale_worker": stale_worker,
        "recommended_next_action": (
            "Resolve coordination blockers before any Level 10 discussion."
            if blockers
            else "Request explicit human approval before starting Level 10.0."
        ),
        "forbidden_actions": [
            "Level 10 work without explicit approval",
            "assignment writes",
            "automatic reassignment",
            "force overwrite",
            "branch creation",
            "worktree creation",
            "checkout",
            "branch deletion",
            "worktree deletion",
            "cleanup",
            "stash",
            "commit",
            "push",
            "merge",
            "automatic execution",
            "automatic promotion",
            "self-approval",
        ],
        "manual_checks": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_coordination_dashboard or level_9_stale_worker_closeout_packet or level_9_allowed_file_conflict_checker"',
        ],
        "next_step": "Level 10.0 may begin only after explicit human approval.",
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


def _level_7_next_safe_action_blockers(
    *,
    disabled_state: dict[str, Any],
    closeout: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if not disabled_state["level_7_autopilot_enabled"]:
        blockers.append("level_7_autopilot_disabled_by_default")
    if not disabled_state["level_7_autopilot_action_available"]:
        blockers.append("level_7_action_authority_unavailable")
    if closeout["dashboard_blockers"]:
        blockers.append("level_6_closeout_blockers_present")
    if closeout["blocked_project_count"]:
        blockers.append("blocked_projects_present")
    return sorted(set(blockers))


def _level_7_next_safe_action_title(blockers: list[str]) -> str:
    if "level_7_autopilot_disabled_by_default" in blockers:
        return "Keep Level 7 disabled and review the Level 7.2 recommendation contract."
    if blockers:
        return "Resolve blockers before considering any Level 7 recommendation."
    return "Review the proposed next human action; Cartographer cannot execute it."


def _level_7_next_safe_action_reason(blockers: list[str]) -> str:
    if "level_7_autopilot_disabled_by_default" in blockers:
        return "Level 7 is disabled by default, so the only safe action is human review."
    if blockers:
        return "Cartographer found blockers that prevent a safe recommendation from advancing."
    return "No blockers were detected, but the contract remains recommendation-only."


def _level_7_dry_run_action_packet(recommendation: dict[str, Any]) -> dict[str, Any]:
    blockers = sorted(set(recommendation["blockers"]))
    return {
        "packet_id": "cartographer.level_7.dry_run.next_safe_action_review.v1",
        "packet_type": "dry_run_action_packet",
        "title": "Review the Level 7 next safe action recommendation.",
        "purpose": (
            "Describe the human review step that could follow the Level 7.2 "
            "recommendation without executing it."
        ),
        "status": "blocked" if blockers else "ready_for_human_review",
        "actions_taken": False,
        "cartographer_may_execute": False,
        "cartographer_may_self_approve": False,
        "approval_handshake_available": False,
        "execution_available": False,
        "allowed_files": [
            "docs/cartographer-level-7-dry-run-action-packet-builder.md",
            "source_proxy/cartographer/service.py",
            "source_proxy/api/cartographer.py",
            "source_proxy/tests/test_cartographer_api.py",
        ],
        "forbidden_actions": [
            "push",
            "push queue creation",
            "branch creation",
            "worktree creation",
            "cleanup",
            "stash",
            "merge",
            "automatic commit",
            "automatic execution",
            "automatic promotion",
            "self-approval",
            "approval handshake execution",
        ],
        "required_approvals": [
            "explicit human approval for Level 7.4 before approval handshake work",
            "explicit human approval before any future execution gate",
        ],
        "expected_output": "A human-readable dry-run packet with actions_taken false.",
        "manual_check_commands": [
            "git status -sb",
            'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_dry_run_action_packet"',
        ],
        "expected_manual_check_result": (
            "Focused tests pass and all mutation, promotion, execution, and "
            "self-approval flags remain false."
        ),
        "rollback_notes": (
            "Remove the Level 7.3 doc and revert the Level 7.3 service, API, "
            "and test additions. No branch, worktree, stash, push queue, commit, "
            "or generated evidence cleanup should be needed."
        ),
        "blockers": blockers,
        "evidence_references": recommendation["recommendation"]["evidence"],
        "source_recommendation": {
            "action_id": recommendation["recommendation"]["action_id"],
            "status": recommendation["recommendation"]["status"],
            "reason": recommendation["recommendation"]["reason"],
        },
    }


def _level_7_exact_approval_blockers(
    *,
    packet: dict[str, Any],
    packet_id: str,
    approval_id: str | None,
    approved_by: str | None,
    exact_allowed_files: list[str],
    exact_forbidden_actions: list[str],
    exact_manual_check_commands: list[str],
    approved_at: str | None,
) -> list[str]:
    blockers: list[str] = []
    if packet_id != packet["packet_id"]:
        blockers.append("packet_id_mismatch")
    if not approval_id:
        blockers.append("approval_id_required")
    if not approved_by:
        blockers.append("approved_by_required")
    if _level_7_is_self_approval(approved_by):
        blockers.append("self_approval_blocked")
    if not approved_at:
        blockers.append("approved_at_required")
    if exact_allowed_files != packet["allowed_files"]:
        blockers.append("exact_allowed_files_mismatch")
    if exact_forbidden_actions != packet["forbidden_actions"]:
        blockers.append("exact_forbidden_actions_mismatch")
    if exact_manual_check_commands != packet["manual_check_commands"]:
        blockers.append("exact_manual_check_commands_mismatch")
    return list(dict.fromkeys(blockers))


def _level_7_is_self_approval(approved_by: str | None) -> bool:
    actor = str(approved_by or "").strip().lower()
    return actor in {"cartographer", "codex", "cartographer-ui"}


def _level_7_closeout_item(
    increment: str,
    title: str,
    payload: dict[str, Any],
    expected_mode: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    if payload["write_actions_enabled"]:
        blockers.append("write_actions_enabled")
    if payload["authority_granted"]:
        blockers.append("authority_granted")
    if payload["actions_taken"]:
        blockers.append("actions_taken")
    for flag in (
        "automatic_execution_allowed",
        "automatic_promotion_allowed",
        "self_approval_allowed",
        "commit_allowed",
        "push_allowed",
        "branch_creation_allowed",
        "worktree_creation_allowed",
        "cleanup_allowed",
        "merge_allowed",
        "stash_allowed",
    ):
        if payload.get(flag):
            blockers.append(flag)
    if expected_mode == "feature_flag_locked" and payload["level_7_autopilot_action_available"]:
        blockers.append("level_7_action_available")
    if expected_mode == "recommendation_only" and not payload["recommendation_only"]:
        blockers.append("recommendation_not_marked_preview_only")
    if expected_mode == "dry_run_only" and payload["packet"]["actions_taken"]:
        blockers.append("dry_run_packet_actions_taken")
    if expected_mode == "approval_preview_only" and payload["execution_available"]:
        blockers.append("approval_preview_execution_available")
    return {
        "increment": increment,
        "title": title,
        "mode": expected_mode,
        "closeout_status": "ready_for_review" if not blockers else "blocked",
        "blockers": blockers,
        "write_actions_enabled": payload["write_actions_enabled"],
        "authority_granted": payload["authority_granted"],
        "actions_taken": payload["actions_taken"],
        "automatic_execution_allowed": payload.get("automatic_execution_allowed", False),
        "automatic_promotion_allowed": payload.get("automatic_promotion_allowed", False),
        "self_approval_allowed": payload.get("self_approval_allowed", False),
    }


def _level_8_workflow_step_card(
    *,
    step_id: str,
    title: str,
    source: str,
    blockers: list[str],
) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "title": title,
        "source": source,
        "status": "blocked" if blockers else "pending_human_approval",
        "human_approval_required": True,
        "approved": False,
        "cartographer_may_execute": False,
        "actions_taken": False,
        "receipt_required": True,
        "retry_allowed": False,
        "blockers": blockers,
    }


def _level_8_step_approval_blockers(
    *,
    workflow: dict[str, Any],
    step: dict[str, Any] | None,
    workflow_id: str,
    approval_id: str | None,
    approved_by: str | None,
    exact_step_title: str,
    exact_manual_check_commands: list[str],
    approved_at: str | None,
) -> list[str]:
    blockers: list[str] = []
    if workflow_id != workflow["workflow_id"]:
        blockers.append("workflow_id_mismatch")
    if step is None:
        blockers.append("step_id_not_found")
    if not approval_id:
        blockers.append("approval_id_required")
    if not approved_by:
        blockers.append("approved_by_required")
    if _level_7_is_self_approval(approved_by):
        blockers.append("self_approval_blocked")
    if not approved_at:
        blockers.append("approved_at_required")
    if step is not None and exact_step_title != step["title"]:
        blockers.append("exact_step_title_mismatch")
    if exact_manual_check_commands != [
        "git status -sb",
        'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_workflow_run_card or level_7_closeout_dashboard or level_6_multi_project_closeout"',
    ]:
        blockers.append("exact_manual_check_commands_mismatch")
    return list(dict.fromkeys(blockers))


def _level_8_receipt_journal_entry(
    *,
    event_id: str,
    event_type: str,
    status: str,
    source_id: str,
    evidence: list[str],
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "event_type": event_type,
        "status": status,
        "source_id": source_id,
        "visible_to_operator": True,
        "persisted": False,
        "hidden_write": False,
        "actions_taken": False,
        "execution_available": False,
        "evidence": evidence,
    }


def _level_8_stopped_state(
    *,
    state_id: str,
    status: str,
    step_id: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "state_id": state_id,
        "status": status,
        "step_id": step_id,
        "reason": reason,
        "workflow_stopped": True,
        "later_steps_unapproved": True,
        "human_review_required": True,
        "continuation_allowed": False,
        "retry_allowed": False,
        "autonomous_retry_allowed": False,
        "background_execution_allowed": False,
        "actions_taken": False,
    }


def _level_8_closeout_item(increment: str, title: str, payload: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    for flag in (
        "write_actions_enabled",
        "authority_granted",
        "actions_taken",
        "execution_available",
        "background_execution_allowed",
        "autonomous_retry_allowed",
        "cross_project_mutation_allowed",
        "automatic_execution_allowed",
        "automatic_promotion_allowed",
        "self_approval_allowed",
        "commit_allowed",
        "push_allowed",
        "merge_allowed",
        "branch_creation_allowed",
        "worktree_creation_allowed",
        "cleanup_allowed",
        "stash_allowed",
    ):
        if payload.get(flag):
            blockers.append(flag)
    if payload.get("journal", {}).get("persisted"):
        blockers.append("receipt_journal_persisted")
    if payload.get("journal", {}).get("hidden_writes_allowed"):
        blockers.append("hidden_receipt_writes_allowed")
    if payload.get("workflow_continuation_allowed"):
        blockers.append("workflow_continuation_allowed")
    return {
        "increment": increment,
        "title": title,
        "closeout_status": "ready_for_review" if not blockers else "blocked",
        "blockers": blockers,
        "write_actions_enabled": payload.get("write_actions_enabled", False),
        "authority_granted": payload.get("authority_granted", False),
        "actions_taken": payload.get("actions_taken", False),
        "execution_available": payload.get("execution_available", False),
        "background_execution_allowed": payload.get("background_execution_allowed", False),
        "autonomous_retry_allowed": payload.get("autonomous_retry_allowed", False),
    }


def _level_9_worker_registry_entry(
    *,
    worker_id: str,
    task_id: str,
    branch: str,
    allowed_files: list[str],
    owner: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not worker_id:
        blockers.append("worker_id_required")
    if not task_id:
        blockers.append("task_id_required")
    if not branch:
        blockers.append("branch_required")
    if not allowed_files:
        blockers.append("allowed_files_required")
    return {
        "worker_id": worker_id,
        "task_id": task_id,
        "owner": owner,
        "branch": branch,
        "allowed_files": allowed_files,
        "assignment_status": "observed" if not blockers else "blocked",
        "recommendation_only": True,
        "assignment_write_allowed": False,
        "automatic_reassignment_allowed": False,
        "force_overwrite_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "actions_taken": False,
        "blockers": blockers,
    }


def _level_9_one_worker_rule_item(worker: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if not worker["worker_id"]:
        blockers.append("worker_id_required")
    if not worker["task_id"]:
        blockers.append("one_task_required")
    if not worker["branch"]:
        blockers.append("one_branch_required")
    if len(worker["allowed_files"]) == 0:
        blockers.append("allowed_files_required")
    return {
        "worker_id": worker["worker_id"],
        "task_id": worker["task_id"],
        "branch": worker["branch"],
        "rule_status": "ready_for_review" if not blockers else "blocked",
        "one_worker": bool(worker["worker_id"]),
        "one_task": bool(worker["task_id"]),
        "one_branch": bool(worker["branch"]),
        "branch_creation_allowed": False,
        "checkout_allowed": False,
        "worktree_creation_allowed": False,
        "automatic_reassignment_allowed": False,
        "force_overwrite_allowed": False,
        "actions_taken": False,
        "blockers": blockers,
    }


def _level_9_allowed_file_conflicts(workers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_file: dict[str, list[str]] = {}
    for worker in workers:
        for file_path in worker["allowed_files"]:
            by_file.setdefault(file_path, []).append(worker["worker_id"])
    return [
        {
            "file": file_path,
            "worker_ids": worker_ids,
            "conflict_type": "allowed_file_overlap",
            "blocks_parallel_work": True,
            "force_overwrite_allowed": False,
            "automatic_reassignment_allowed": False,
            "actions_taken": False,
        }
        for file_path, worker_ids in sorted(by_file.items())
        if len(worker_ids) > 1
    ]


def _level_9_branch_worktree_proposal(
    *,
    proposal_id: str,
    worker_id: str,
    task_id: str,
    proposed_branch: str,
    proposed_worktree: str,
    blockers: list[str],
) -> dict[str, Any]:
    return {
        "proposal_id": proposal_id,
        "worker_id": worker_id,
        "task_id": task_id,
        "proposed_branch": proposed_branch,
        "proposed_worktree": proposed_worktree,
        "proposal_status": "blocked" if blockers else "ready_for_human_review",
        "requires_approval": True,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "checkout_allowed": False,
        "branch_created": False,
        "worktree_created": False,
        "actions_taken": False,
        "blockers": blockers,
    }


def _level_9_stale_worker_packet(
    *,
    worker_id: str,
    task_id: str,
    stale_reason: str,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "packet_id": f"cartographer.level_9.stale_worker.{worker_id}.v1",
        "worker_id": worker_id,
        "task_id": task_id,
        "stale": True,
        "stale_reason": stale_reason,
        "recommended_action": recommended_action,
        "requires_human_review": True,
        "closeout_execution_allowed": False,
        "automatic_reassignment_allowed": False,
        "automatic_closeout_allowed": False,
        "branch_deletion_allowed": False,
        "worktree_deletion_allowed": False,
        "cleanup_allowed": False,
        "actions_taken": False,
        "blockers": ["human_review_required"],
    }


def _level_9_coordination_dashboard_item(
    increment: str,
    title: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    for flag in (
        "write_actions_enabled",
        "authority_granted",
        "actions_taken",
        "assignment_write_allowed",
        "automatic_reassignment_allowed",
        "force_overwrite_allowed",
        "branch_creation_allowed",
        "worktree_creation_allowed",
        "checkout_allowed",
        "branch_deletion_allowed",
        "worktree_deletion_allowed",
        "cleanup_allowed",
        "stash_allowed",
        "commit_allowed",
        "push_allowed",
        "merge_allowed",
        "automatic_execution_allowed",
        "automatic_promotion_allowed",
        "self_approval_allowed",
        "cross_project_mutation_allowed",
    ):
        if payload.get(flag):
            blockers.append(flag)
    return {
        "increment": increment,
        "title": title,
        "closeout_status": "ready_for_review" if not blockers else "blocked",
        "blockers": blockers,
        "write_actions_enabled": payload.get("write_actions_enabled", False),
        "authority_granted": payload.get("authority_granted", False),
        "actions_taken": payload.get("actions_taken", False),
        "recommendation_only": payload.get("recommendation_only", True),
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


def _level_6_status_board_item(
    registry_entry: dict[str, Any],
    health: dict[str, Any] | None,
) -> dict[str, Any]:
    blockers = list(registry_entry.get("blockers", []))
    if health is None:
        blockers.append("project_health_missing")
    else:
        blockers.extend(str(blocker) for blocker in health.get("merge_blockers", []))
        if health.get("dirty"):
            blockers.append("dirty_tree")
        if health.get("pending_drift", 0) > 0:
            blockers.append("pending_drift")
        if health.get("pending_proposals", 0) > 0:
            blockers.append("pending_proposals")
    unique_blockers = list(dict.fromkeys(blockers))
    return {
        "project_id": registry_entry.get("project_id"),
        "name": registry_entry.get("name"),
        "root": registry_entry.get("root"),
        "owner": registry_entry.get("owner"),
        "agent": registry_entry.get("agent"),
        "current_level": 6,
        "registry_status": "registered",
        "status": health.get("status") if health else "unknown",
        "blueprint_health": health.get("blueprint_health") if health else "unknown",
        "dirty": bool(health and health.get("dirty")),
        "branch": health.get("branch") if health else None,
        "ahead": health.get("ahead", 0) if health else 0,
        "behind": health.get("behind", 0) if health else 0,
        "merge_ready": bool(health and health.get("merge_ready")),
        "blockers": unique_blockers,
        "recommended_next_action": (
            health.get("recommended_next_step")
            if health
            else "Inspect project health probe failure before assigning work."
        ),
        "safe_sequencing": "blocked" if unique_blockers else "ready_for_review",
        "write_actions_enabled": False,
        "actions_taken": False,
        "commit_allowed": False,
        "push_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
    }


def _level_6_candidate_board_item(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate.get("candidate_id"),
        "project_id": candidate.get("project_id"),
        "name": candidate.get("name"),
        "root": candidate.get("root"),
        "owner": None,
        "agent": None,
        "current_level": 6,
        "registry_status": "candidate",
        "status": candidate.get("status"),
        "approval_status": candidate.get("approval_status"),
        "blockers": ["project_enrollment_requires_approval"],
        "recommended_next_action": "Review project candidate before enrollment.",
        "safe_sequencing": "blocked",
        "write_actions_enabled": False,
        "actions_taken": False,
        "project_enrollment_allowed": False,
        "auto_enrollment_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
    }


def _level_6_component_ownership_item(
    component: dict[str, Any],
    *,
    changed_component: dict[str, Any] | None,
    status_board: dict[str, Any],
) -> dict[str, Any]:
    component_id = component.get("component_id")
    related_projects = [
        item["project_id"]
        for item in status_board.get("board_items", [])
        if item.get("project_id")
    ]
    matched_paths = list((changed_component or {}).get("matched_paths", []))
    changed = changed_component is not None
    owner = None
    assigned_agent = None
    conflicts: list[str] = []
    if changed and owner is None:
        conflicts.append("changed_component_without_owner")
    return {
        "component_id": component_id,
        "label": component.get("label"),
        "blueprint_id": component.get("blueprint_id"),
        "risk": component.get("risk"),
        "sandbox": component.get("sandbox", False),
        "owner": owner,
        "assigned_agent": assigned_agent,
        "owner_required": changed,
        "assignment_status": "unassigned",
        "assignment_source": "preview_only",
        "related_projects": related_projects,
        "matched_paths": matched_paths,
        "changed": changed,
        "conflicts": conflicts,
        "recommended_next_action": (
            "Assign an explicit owner before parallel work continues."
            if conflicts
            else "No ownership action required."
        ),
        "assignment_write_allowed": False,
        "automatic_reassignment_allowed": False,
        "repo_mutation_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "cleanup_allowed": False,
        "actions_taken": False,
    }


def _level_6_project_dirty_classification(
    registry_entry: dict[str, Any],
    git_status: Any | None,
) -> dict[str, Any]:
    changed_files = list(git_status.changed_files) if git_status is not None else []
    records = [_level_6_dirty_file_record(path) for path in changed_files]
    forbidden_files = [
        record["path"]
        for record in records
        if record["classification"] == "forbidden_path"
    ]
    sensitive_files = [
        record["path"]
        for record in records
        if record["classification"] == "sensitive_path"
    ]
    unclassified_files = [
        record["path"]
        for record in records
        if record["classification"] == "unclassified"
    ]
    buckets: dict[str, list[str]] = {}
    for record in records:
        buckets.setdefault(record["classification"], []).append(record["path"])
    blocks = bool(forbidden_files or sensitive_files or unclassified_files or (git_status is None))
    return {
        "project_id": registry_entry.get("project_id"),
        "name": registry_entry.get("name"),
        "root": registry_entry.get("root"),
        "git_available": bool(git_status and git_status.available),
        "branch": git_status.branch if git_status is not None else None,
        "dirty": bool(changed_files),
        "dirty_files": changed_files,
        "dirty_file_count": len(changed_files),
        "files": records,
        "buckets": buckets,
        "forbidden_files": forbidden_files,
        "sensitive_files": sensitive_files,
        "unclassified_files": unclassified_files,
        "blocks_cross_repo_sequence": blocks,
        "sequencing_status": "blocked" if blocks else "classified",
        "recommended_next_action": (
            "Inspect project git status before sequencing cross-repo work."
            if git_status is None
            else "Human must classify or clear blocked dirty files before cross-repo sequencing."
            if blocks
            else "Dirty tree is clean or classified for read-only sequencing."
        ),
        "staging_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "actions_taken": False,
    }


def _level_6_closeout_item(
    board_item: dict[str, Any],
    *,
    ownership: dict[str, Any],
    dirty_classifier: dict[str, Any],
) -> dict[str, Any]:
    project_id = board_item.get("project_id")
    dirty_item = next(
        (
            item
            for item in dirty_classifier.get("classifications", [])
            if item.get("project_id") == project_id
        ),
        None,
    )
    ownership_conflicts = [
        conflict
        for conflict in ownership.get("conflicts", [])
        if project_id in conflict.get("related_projects", [])
    ]
    blockers = list(board_item.get("blockers", []))
    if dirty_item and dirty_item.get("blocks_cross_repo_sequence"):
        blockers.append("dirty_tree_blocks_cross_repo_sequence")
    if ownership_conflicts:
        blockers.append("ownership_conflicts_present")
    unique_blockers = list(dict.fromkeys(blockers))
    return {
        "project_id": project_id,
        "name": board_item.get("name"),
        "root": board_item.get("root"),
        "current_level": 6,
        "allowed_authority": "read_only_closeout_dashboard",
        "owner": board_item.get("owner"),
        "agent": board_item.get("agent"),
        "dirty": board_item.get("dirty", False),
        "branch": board_item.get("branch"),
        "closeout_status": "blocked" if unique_blockers else "ready_for_review",
        "blockers": unique_blockers,
        "ownership_conflict_count": len(ownership_conflicts),
        "dirty_tree_status": dirty_item.get("sequencing_status") if dirty_item else "unknown",
        "next_safe_action": (
            "Resolve blockers before closeout."
            if unique_blockers
            else "Ready for human closeout review."
        ),
        "mutation_disabled": True,
        "commit_allowed": False,
        "push_allowed": False,
        "push_queue_creation_allowed": False,
        "branch_creation_allowed": False,
        "worktree_creation_allowed": False,
        "cleanup_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "automatic_promotion_allowed": False,
        "automatic_execution_allowed": False,
        "actions_taken": False,
    }


def _level_6_dirty_file_record(path: str) -> dict[str, Any]:
    components, unmapped = map_paths([path])
    sensitive = _level_6_sensitive_path(path)
    forbidden = _level_6_forbidden_path(path)
    if sensitive:
        classification = "sensitive_path"
        component_id = None
        reason = "sensitive path marker blocks cross-repo sequencing"
    elif forbidden:
        classification = "forbidden_path"
        component_id = None
        reason = "forbidden path shape blocks cross-repo sequencing"
    elif components:
        classification = "classified_component"
        component_id = components[0].component_id
        reason = f"mapped to component {component_id}"
    else:
        classification = "unclassified"
        component_id = None
        reason = unmapped[0].reason if unmapped else "no_component_mapping_rule"
    return {
        "path": path,
        "classification": classification,
        "component_id": component_id,
        "reason": reason,
        "blocks_cross_repo_sequence": classification != "classified_component",
    }


def _level_6_forbidden_path(path: str) -> bool:
    normalized = path.strip().replace("\\", "/").lstrip("./")
    lowered = normalized.lower()
    if (
        not normalized
        or normalized.startswith("/")
        or normalized.startswith("~")
        or any(segment == ".." for segment in normalized.split("/"))
    ):
        return True
    return lowered.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip"))


def _level_6_sensitive_path(path: str) -> bool:
    lowered = path.strip().replace("\\", "/").lower()
    return any(
        marker in lowered
        for marker in ("secret", "token", "credential", "password", ".env", "private-key")
    )


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
