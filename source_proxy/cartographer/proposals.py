from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from source_proxy.cartographer.models import ProposalRecord, ProposalTransition
from source_proxy.cartographer.project_discovery import discover_projects


PROPOSAL_STATES = (
    "detected",
    "drafted",
    "pending_review",
    "approved",
    "rejected",
    "applied",
    "commit_pending",
    "commit_approved",
    "push_pending",
    "push_approved",
    "pushed",
    "failed",
)
PENDING_PROPOSAL_STATES = {"detected", "drafted", "pending_review"}


def list_proposals() -> list[ProposalRecord]:
    proposals: list[ProposalRecord] = []
    for project in discover_projects():
        proposal_dir = Path(project.root) / "_blueprints" / "proposals"
        if not proposal_dir.exists() or not proposal_dir.is_dir():
            continue
        for path in _proposal_files(proposal_dir):
            proposals.append(
                _proposal_from_file(
                    project_id=project.project_id,
                    proposal_dir=proposal_dir,
                    path=path,
                )
            )

    return sorted(proposals, key=lambda proposal: proposal.proposal_id)


def pending_proposal_count() -> int:
    return sum(1 for proposal in list_proposals() if proposal.status in PENDING_PROPOSAL_STATES)


def proposal_states() -> list[str]:
    return list(PROPOSAL_STATES)


def _proposal_files(proposal_dir: Path) -> list[Path]:
    try:
        return sorted(
            path
            for path in proposal_dir.rglob("*.json")
            if path.is_file()
        )
    except OSError:
        return []


def _proposal_from_file(
    *, project_id: str, proposal_dir: Path, path: Path
) -> ProposalRecord:
    rel_path = path.relative_to(proposal_dir).as_posix()
    warnings: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ProposalRecord(
            proposal_id=_stable_proposal_id(project_id, rel_path, {}),
            project_id=project_id,
            status="failed",
            type="unknown",
            component="unknown",
            requires_approval=True,
            warnings=["proposal_file_unreadable"],
        )

    if not isinstance(payload, dict):
        payload = {}
        warnings.append("proposal_payload_not_object")

    status = str(payload.get("status") or _status_from_path(rel_path) or "detected")
    if status not in PROPOSAL_STATES:
        warnings.append("invalid_proposal_status")

    transitions = _transitions(payload.get("transitions"), status, warnings)
    proposal_id = str(payload.get("proposal_id") or _stable_proposal_id(project_id, rel_path, payload))
    applied = bool(payload.get("applied")) or status in {"applied", "commit_pending", "commit_approved", "push_pending", "push_approved", "pushed"}

    return ProposalRecord(
        proposal_id=proposal_id,
        project_id=project_id,
        status=status,
        type=str(payload.get("type") or "blueprint_update"),
        component=str(payload.get("component") or "unknown"),
        requires_approval=_bool(payload.get("requires_approval"), default=True),
        title=str(payload["title"]) if payload.get("title") is not None else None,
        affected_blueprints=_string_list(payload.get("affected_blueprints")),
        changed_files=_string_list(payload.get("changed_files")),
        proposed_files=_string_list(payload.get("proposed_files")),
        rejection_reason=(
            str(payload["rejection_reason"])
            if payload.get("rejection_reason") is not None
            else None
        ),
        transitions=transitions,
        applied=applied,
        action_taken=applied,
        warnings=warnings,
    )


def _status_from_path(rel_path: str) -> str | None:
    first_part = rel_path.split("/", 1)[0]
    return first_part if first_part in PROPOSAL_STATES else None


def _transitions(value: Any, status: str, warnings: list[str]) -> list[ProposalTransition]:
    if not isinstance(value, list) or not value:
        warnings.append("missing_transition_history")
        return [ProposalTransition(status=status, timestamp=None, actor=None)]

    transitions: list[ProposalTransition] = []
    for item in value:
        if not isinstance(item, dict):
            warnings.append("invalid_transition_record")
            continue
        transition_status = str(item.get("status") or "")
        timestamp = item.get("timestamp")
        actor = item.get("actor")
        if not transition_status or timestamp is None or actor is None:
            warnings.append("transition_missing_required_fields")
        transitions.append(
            ProposalTransition(
                status=transition_status or status,
                timestamp=str(timestamp) if timestamp is not None else None,
                actor=str(actor) if actor is not None else None,
            )
        )
    return transitions


def _stable_proposal_id(project_id: str, rel_path: str, payload: dict[str, Any]) -> str:
    digest = sha256(
        json.dumps(
            {
                "project_id": project_id,
                "path": rel_path,
                "type": payload.get("type"),
                "component": payload.get("component"),
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"bp-{digest}"


def _bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]
