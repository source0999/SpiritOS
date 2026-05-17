from __future__ import annotations

from typing import Any

from source_proxy.cartographer.audit_trail import build_audit_trail
from source_proxy.cartographer.blueprint_registry import count_blueprint_documents, list_blueprints
from source_proxy.cartographer.blueprint_scribe import draft_blueprint_updates
from source_proxy.cartographer.branch_recommendations import recommend_branches
from source_proxy.cartographer.change_scribe import summarize_changes
from source_proxy.cartographer.codex_evidence import build_codex_evidence_rollup
from source_proxy.cartographer.commit_proposals import build_commit_proposals
from source_proxy.cartographer.component_mapper import build_component_map
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.git_status import read_git_status, read_git_statuses
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
    proposal_states,
)
from source_proxy.cartographer.push_queue import build_push_queue
from source_proxy.cartographer.reminders import build_reminders
from source_proxy.cartographer.repo_map import build_repo_maps
from source_proxy.cartographer.runbook_scribe import suggest_runbook_updates
from source_proxy.cartographer.safety import cartographer_safety_manifest
from source_proxy.cartographer.sub_cartographers import route_sub_cartographers, sub_cartographer_roles


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
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "components": to_jsonable(component_map["components"]),
        "unmapped_paths": to_jsonable(component_map["unmapped_paths"]),
        "mapping_mode": component_map["mapping_mode"],
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
    fingerprints = [
        proposal.fingerprint
        for proposal in proposals
        if proposal.fingerprint
    ]
    duplicate_proposals = len(fingerprints) - len(set(fingerprints))
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "proposals": to_jsonable(proposals),
        "proposal_count": len(proposals),
        "pending_proposals": pending_proposal_count(),
        "deduped": duplicate_proposals == 0,
        "duplicate_proposals_suppressed": 0,
        "duplicate_proposals_present": duplicate_proposals,
        "proposal_states": lifecycle,
        "proposal_lifecycle": lifecycle,
        "lifecycle": lifecycle,
        "transition_audit_complete": all(
            transition.actor and transition.timestamp
            for proposal in proposals
            for transition in proposal.transitions
        ),
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }


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


def build_cartographer_sub_cartographers() -> dict[str, Any]:
    roles = sub_cartographer_roles()
    routes = route_sub_cartographers()
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "roles": to_jsonable(roles),
        "role_count": len(roles),
        "routes": to_jsonable(routes),
        "route_count": len(routes),
        "actions_taken": False,
        "failures_stop_at": "proposal_queue",
        "safety": cartographer_safety_manifest(),
    }
