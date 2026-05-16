from __future__ import annotations

import json
import os
from hashlib import sha256
from pathlib import Path
from typing import Any

from source_proxy.cartographer.commit_proposals import build_commit_proposals
from source_proxy.cartographer.models import AuditTrailEvent, CartographerProject, ProposalRecord
from source_proxy.cartographer.project_discovery import discover_projects
from source_proxy.cartographer.proposals import list_proposals
from source_proxy.cartographer.push_queue import build_push_queue


MAX_AUDIT_LINES = 100


def build_audit_trail() -> list[AuditTrailEvent]:
    projects = {project.project_id: project for project in discover_projects()}
    events: list[AuditTrailEvent] = []
    for proposal in list_proposals():
        events.extend(_events_from_proposal(proposal))
    for project in projects.values():
        events.extend(_events_from_approved_action_log(project))
    for proposal in build_commit_proposals():
        events.append(
            AuditTrailEvent(
                event_id=_event_id("commit_pending", proposal.project_id, proposal.commit_proposal_id),
                project_id=proposal.project_id,
                event="commit_pending",
                proposal_id=proposal.source_proposal_id,
                result="pending_approval",
                files=proposal.files,
                rollback_hint="Commit has not run; reject approval to leave Git untouched.",
                source="commit_proposals",
            )
        )
    for item in build_push_queue():
        events.append(
            AuditTrailEvent(
                event_id=_event_id("push_pending", item.project_id, item.push_id),
                project_id=item.project_id,
                event="push_pending",
                result="pending_approval",
                files=item.files,
                branch=item.branch,
                remote=item.remote,
                rollback_hint="Push has not run; reject approval to leave remote untouched.",
                source="push_queue",
            )
        )
    return sorted(events, key=lambda event: (event.timestamp or "", event.event_id))


def _events_from_proposal(proposal: ProposalRecord) -> list[AuditTrailEvent]:
    events: list[AuditTrailEvent] = []
    for index, transition in enumerate(proposal.transitions):
        event_name = str(transition.status)
        events.append(
            AuditTrailEvent(
                event_id=_event_id(proposal.proposal_id, event_name, str(index)),
                project_id=proposal.project_id,
                event=event_name,
                actor=transition.actor,
                timestamp=transition.timestamp,
                proposal_id=proposal.proposal_id,
                result=_proposal_result(proposal, event_name),
                files=proposal.proposed_files,
                rollback_hint=_rollback_hint_for_proposal(proposal, event_name),
                source="proposal_transition",
            )
        )
    return events


def _events_from_approved_action_log(project: CartographerProject) -> list[AuditTrailEvent]:
    audit_path = _audit_path(project)
    if not audit_path.exists() or not audit_path.is_file():
        return []

    events: list[AuditTrailEvent] = []
    try:
        lines = audit_path.read_text(encoding="utf-8").splitlines()[-MAX_AUDIT_LINES:]
    except OSError:
        return []

    for index, line in enumerate(lines):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        events.append(_event_from_audit_payload(project.project_id, payload, index))
    return events


def _event_from_audit_payload(
    project_id: str,
    payload: dict[str, Any],
    index: int,
) -> AuditTrailEvent:
    event = str(payload.get("event") or payload.get("action") or "approved_action")
    timestamp = str(
        payload.get("approved_at")
        or payload.get("rejected_at")
        or payload.get("created_at")
        or ""
    ) or None
    actor = payload.get("approved_by") or payload.get("rejected_by") or payload.get("actor")
    files = _string_list(payload.get("changed_files"))
    if not files and payload.get("target"):
        files = [str(payload["target"])]
    return AuditTrailEvent(
        event_id=_event_id(project_id, event, str(index), str(payload.get("task_id") or "")),
        project_id=project_id,
        event=event,
        actor=str(actor) if actor is not None else None,
        timestamp=timestamp,
        proposal_id=str(payload["proposal_id"]) if payload.get("proposal_id") is not None else None,
        task_id=str(payload["task_id"]) if payload.get("task_id") is not None else None,
        result=str(payload.get("result") or payload.get("reason_code") or "recorded"),
        files=files,
        branch=str(payload["branch"]) if payload.get("branch") is not None else None,
        remote=str(payload["remote"]) if payload.get("remote") is not None else None,
        rollback_hint="Review backup/audit artifacts before reverting approved workspace changes.",
        source="approved_action_audit",
    )


def _audit_path(project: CartographerProject) -> Path:
    configured = os.getenv("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG")
    if configured:
        return Path(configured)
    return Path(project.root) / "data" / "approved_actions.audit.jsonl"


def _proposal_result(proposal: ProposalRecord, event_name: str) -> str:
    if event_name == "rejected" and proposal.rejection_reason:
        return proposal.rejection_reason
    if event_name in {"applied", "pushed", "failed"}:
        return event_name
    return "recorded"


def _rollback_hint_for_proposal(proposal: ProposalRecord, event_name: str) -> str:
    if event_name == "rejected":
        return "No rollback needed; rejected proposal should not change files."
    if event_name == "applied":
        return "Use Git diff and backup audit artifacts before reverting applied files."
    if event_name in {"commit_pending", "commit_approved"}:
        return "Commit not pushed by Cartographer; review local Git history before reverting."
    if event_name in {"push_pending", "push_approved", "pushed"}:
        return "Review remote branch and audit event before any revert or force action."
    return "No rollback action is available from this read-only trail."


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _event_id(*parts: str) -> str:
    key = "|".join(parts)
    return f"audit-{sha256(key.encode('utf-8')).hexdigest()[:12]}"
