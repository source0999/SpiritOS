from __future__ import annotations

from typing import Any

from source_proxy.cartographer.blueprint_registry import count_blueprint_documents, list_blueprints
from source_proxy.cartographer.component_mapper import build_component_map
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.git_status import read_git_status, read_git_statuses
from source_proxy.cartographer.models import CartographerStatus, to_jsonable
from source_proxy.cartographer.project_discovery import (
    blocked_project_roots,
    configured_project_roots,
    discover_projects,
)
from source_proxy.cartographer.proposals import (
    list_proposals,
    pending_proposal_count,
    proposal_states,
)
from source_proxy.cartographer.reminders import build_reminders
from source_proxy.cartographer.repo_map import build_repo_maps
from source_proxy.cartographer.safety import cartographer_safety_manifest


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
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "configured_roots": to_jsonable(configured_project_roots()),
        "blocked_roots": to_jsonable(blocked_project_roots()),
        "projects": to_jsonable(discover_projects()),
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
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "proposals": to_jsonable(proposals),
        "proposal_count": len(proposals),
        "pending_proposals": pending_proposal_count(),
        "proposal_states": proposal_states(),
        "actions_taken": False,
        "safety": cartographer_safety_manifest(),
    }
