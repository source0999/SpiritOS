from __future__ import annotations

import json
import os
from hashlib import sha256
from pathlib import Path
from typing import Any

from source_proxy.cartographer.codex_evidence import list_codex_evidence_records
from source_proxy.cartographer.commit_proposals import build_commit_proposals
from source_proxy.cartographer.component_mapper import map_paths
from source_proxy.cartographer.git_approvals import read_git_approval_records
from source_proxy.cartographer.models import AuditTrailEvent, CartographerProject, ProposalRecord
from source_proxy.cartographer.project_discovery import discover_project_candidates, discover_projects
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
    project_roots = {project.root for project in projects.values()}
    for candidate in discover_project_candidates():
        if candidate.root in project_roots:
            continue
        events.extend(_events_from_approved_action_log(candidate))
    events.extend(_events_from_codex_evidence(_codex_project_id(projects)))
    events.extend(_events_from_git_approval_records())
    for proposal in build_commit_proposals():
        events.append(
            AuditTrailEvent(
                event_id=_event_id("commit_pending", proposal.project_id, proposal.commit_proposal_id),
                project_id=proposal.project_id,
                event="commit_pending",
                action="commit_proposed",
                proposal_id=proposal.source_proposal_id,
                component=proposal.component,
                reason=proposal.reason,
                result="pending_approval",
                files=proposal.files,
                changed_files=proposal.files,
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
                action="push_queued",
                result="pending_approval",
                files=item.files,
                changed_files=item.files,
                branch=item.branch,
                remote=item.remote,
                reason=f"{item.commits_ahead} commit(s) ahead of upstream.",
                rollback_hint="Push has not run; reject approval to leave remote untouched.",
                source="push_queue",
            )
        )
    return sorted(events, key=lambda event: (event.timestamp or "", event.event_id))


def _events_from_codex_evidence(project_id: str) -> list[AuditTrailEvent]:
    events: list[AuditTrailEvent] = []
    for record in list_codex_evidence_records():
        events.append(
            AuditTrailEvent(
                event_id=_event_id("codex_evidence", record.task_id, record.artifact_path),
                project_id=project_id,
                event="codex_task_evidence",
                action="codex_proposal_recorded",
                task_id=record.task_id,
                component=record.components[0] if record.components else "unknown",
                reason=record.recommendation,
                result=record.safety_verdict,
                files=record.changed_files,
                changed_files=record.changed_files,
                rollback_hint="Codex evidence is read-only; review the referenced artifact before changing files.",
                source="codex_evidence",
            )
        )
    return events


def _codex_project_id(projects: dict[str, CartographerProject]) -> str:
    if "spiritos" in projects:
        return "spiritos"
    if projects:
        return next(iter(projects))
    return "spiritos"


def _events_from_git_approval_records() -> list[AuditTrailEvent]:
    events: list[AuditTrailEvent] = []
    for index, payload in enumerate(read_git_approval_records()):
        event = str(payload.get("event") or "git_approval_recorded")
        events.append(
            AuditTrailEvent(
                event_id=_event_id(
                    str(payload.get("project_id") or "unknown"),
                    event,
                    str(payload.get("item_id") or ""),
                    str(index),
                ),
                project_id=str(payload.get("project_id") or "unknown"),
                event=event,
                action=_action_for_git_event(event),
                actor=str(payload.get("approved_by") or "unknown"),
                timestamp=str(payload.get("approved_at") or ""),
                component=_component_from_files(_string_list(payload.get("changed_files"))),
                reason=str(payload["reason"]) if payload.get("reason") is not None else None,
                result=str(payload.get("result") or "approval_recorded_no_execution"),
                files=_string_list(payload.get("changed_files")),
                changed_files=_string_list(payload.get("changed_files")),
                branch=str(payload["branch"]) if payload.get("branch") is not None else None,
                previous_branch=(
                    str(payload["previous_branch"]) if payload.get("previous_branch") is not None else None
                ),
                remote=str(payload["remote"]) if payload.get("remote") is not None else None,
                commit_sha=str(payload["commit_sha"]) if payload.get("commit_sha") is not None else None,
                parent_sha=str(payload["parent_sha"]) if payload.get("parent_sha") is not None else None,
                approved_files=_string_list(payload.get("approved_files")),
                excluded_files=_string_list(payload.get("excluded_files")),
                source_head=str(payload["source_head"]) if payload.get("source_head") is not None else None,
                rollback_command=(
                    str(payload["rollback_command"]) if payload.get("rollback_command") is not None else None
                ),
                rollback_hint=_rollback_hint_for_git_event(event),
                source="git_approval_record",
            )
        )
    return events


def _action_for_git_event(event: str) -> str:
    return {
        "branch_created": "create_branch",
        "branch_rejected": "reject_branch_recommendation",
        "branch_approved": "record_branch_approval",
        "commit_created": "create_commit",
        "commit_approved": "record_commit_approval",
        "push_approved": "push_branch",
        "push_completed": "push_completed",
    }.get(event, event)


def _rollback_hint_for_git_event(event: str) -> str:
    if event == "branch_created":
        return "Switch back to the previous branch and delete the created branch only after confirming no needed work depends on it."
    if event == "branch_rejected":
        return "No rollback needed; rejected branch recommendation left Git untouched."
    if event == "commit_created":
        return "Commit is local only; inspect the commit and use a normal revert/reset workflow before any push."
    if event in {"push_approved", "push_completed"}:
        return "Push already reached the remote; use a normal revert or reviewed remote-branch cleanup workflow."
    return "Approval metadata only; no branch, commit, or push ran."


def _events_from_proposal(proposal: ProposalRecord) -> list[AuditTrailEvent]:
    events: list[AuditTrailEvent] = []
    for index, transition in enumerate(proposal.transitions):
        event_name = str(transition.status)
        events.append(
            AuditTrailEvent(
                event_id=_event_id(proposal.proposal_id, event_name, str(index)),
                project_id=proposal.project_id,
                event=event_name,
                action=_action_for_proposal_event(event_name),
                actor=transition.actor,
                timestamp=transition.timestamp,
                proposal_id=proposal.proposal_id,
                component=proposal.component,
                reason=proposal.rejection_reason if event_name == "rejected" else proposal.rationale,
                result=_proposal_result(proposal, event_name),
                files=proposal.proposed_files,
                changed_files=proposal.proposed_files,
                rollback_hint=_rollback_hint_for_proposal(proposal, event_name),
                source="proposal_transition",
            )
        )
    return events


def _action_for_proposal_event(event: str) -> str:
    return {
        "detected": "proposal_detected",
        "drafted": "proposal_drafted",
        "pending_review": "proposal_submitted_for_review",
        "approved": "proposal_approved",
        "rejected": "proposal_rejected",
        "applied": "proposal_applied",
        "commit_pending": "commit_proposed",
        "commit_approved": "commit_approved",
        "push_pending": "push_queued",
        "push_approved": "push_approved",
        "pushed": "push_completed",
    }.get(event, event)


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
        action=str(payload.get("action") or event),
        actor=str(actor) if actor is not None else None,
        timestamp=timestamp,
        proposal_id=str(payload["proposal_id"]) if payload.get("proposal_id") is not None else None,
        task_id=str(payload["task_id"]) if payload.get("task_id") is not None else None,
        component=_component_from_files(files),
        reason=str(payload["reason"]) if payload.get("reason") is not None else None,
        result=str(payload.get("result") or payload.get("reason_code") or "recorded"),
        files=files,
        changed_files=files,
        branch=str(payload["branch"]) if payload.get("branch") is not None else None,
        remote=str(payload["remote"]) if payload.get("remote") is not None else None,
        commit_sha=str(payload["commit_sha"]) if payload.get("commit_sha") is not None else None,
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


def _component_from_files(files: list[str]) -> str | None:
    if not files:
        return None
    components, _unmapped = map_paths(files)
    return components[0].component_id if components else "unknown"


def _event_id(*parts: str) -> str:
    key = "|".join(parts)
    return f"audit-{sha256(key.encode('utf-8')).hexdigest()[:12]}"
