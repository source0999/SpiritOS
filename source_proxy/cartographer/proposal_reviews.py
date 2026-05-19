from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from source_proxy.cartographer.models import ProposalRecord
from source_proxy.cartographer.models import ProposalTransition
from source_proxy.cartographer.project_discovery import discover_projects
from source_proxy.cartographer.proposals import PROPOSAL_STATES, list_proposals


ReviewDecision = Literal["approve", "reject", "request_edit", "defer", "mark_stale"]


class CartographerProposalReviewError(ValueError):
    def __init__(self, message: str, reason_code: str):
        super().__init__(message)
        self.reason_code = reason_code


def review_blueprint_proposal(
    *,
    proposal_id: str,
    decision: ReviewDecision,
    actor: str,
    reason: str | None = None,
    proposal_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if decision not in {"approve", "reject", "request_edit", "defer", "mark_stale"}:
        raise CartographerProposalReviewError(
            "Unknown proposal review decision.",
            "invalid_review_decision",
        )

    proposal = _proposal_by_id(proposal_id)
    if proposal is None and proposal_snapshot is not None:
        proposal = _proposal_from_snapshot(proposal_id, proposal_snapshot)
    if proposal is None:
        raise CartographerProposalReviewError("Proposal was not found.", "proposal_not_found")

    project_root = _project_root(proposal.project_id)
    if project_root is None:
        raise CartographerProposalReviewError(
            "Proposal project root was not found.",
            "project_not_found",
        )

    next_status = _status_for_decision(decision)
    transition_status = "approved" if decision == "approve" else next_status
    timestamp = _now_timestamp()
    payload = _payload_for_proposal(proposal)
    payload["status"] = next_status
    payload["proposal_id"] = proposal.proposal_id
    payload["project_id"] = proposal.project_id
    payload["fingerprint"] = proposal.fingerprint
    payload["deduped"] = True
    payload["transitions"] = [
        *_transition_payloads(proposal),
        {
            "status": transition_status,
            "timestamp": timestamp,
            "actor": actor or "dashboard-blueprint-review",
        },
    ]
    if decision == "approve":
        payload["approved_by"] = actor or "dashboard-blueprint-review"
        payload["approved_at"] = timestamp
        payload["approved_diff"] = proposal.approved_diff or proposal.diff_preview
        payload["applied"] = False
        payload["action_taken"] = False
    elif decision == "reject":
        payload["rejected_by"] = actor or "dashboard-blueprint-review"
        payload["rejected_at"] = timestamp
        payload["rejection_reason"] = reason or "Rejected from dashboard review."
        payload["applied"] = False
        payload["action_taken"] = False
    elif decision == "defer":
        payload["deferred_by"] = actor or "dashboard-blueprint-review"
        payload["deferred_at"] = timestamp
        payload["review_note"] = reason or "Deferred from dashboard review."
        payload["applied"] = False
        payload["action_taken"] = False
    elif decision == "mark_stale":
        payload["marked_stale_by"] = actor or "dashboard-blueprint-review"
        payload["marked_stale_at"] = timestamp
        payload["review_note"] = reason or "Marked stale from dashboard review."
        payload["applied"] = False
        payload["action_taken"] = False
    else:
        payload["review_note"] = reason or "Edit requested from dashboard review."
        payload["applied"] = False
        payload["action_taken"] = False

    proposal_root = project_root / "_blueprints" / "proposals"
    existing_path = _existing_proposal_path(proposal_root, proposal.proposal_id)
    proposal_path = _proposal_path(project_root, proposal, next_status)
    proposal_path.parent.mkdir(parents=True, exist_ok=True)
    proposal_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if existing_path is not None and existing_path != proposal_path:
        existing_path.unlink(missing_ok=True)

    updated = _proposal_by_id(proposal.proposal_id)
    return {
        "status": "review_recorded",
        "write_actions_enabled": False,
        "proposal": asdict(updated) if updated else payload,
        "decision": decision,
        "actions_taken": False,
        "apply_ran": False,
        "commit_ran": False,
        "push_ran": False,
    }


def _proposal_by_id(proposal_id: str) -> ProposalRecord | None:
    for proposal in list_proposals():
        if proposal.proposal_id == proposal_id:
            return proposal
    return None


def _proposal_from_snapshot(proposal_id: str, payload: dict[str, Any]) -> ProposalRecord | None:
    if str(payload.get("proposal_id") or "") != proposal_id:
        return None
    project_id = str(payload.get("project_id") or "")
    if not project_id:
        return None
    return ProposalRecord(
        proposal_id=proposal_id,
        project_id=project_id,
        status=str(payload.get("status") or "drafted"),
        type=str(payload.get("type") or "blueprint_update"),
        component=str(payload.get("component") or "unknown"),
        requires_approval=bool(payload.get("requires_approval", True)),
        title=str(payload["title"]) if payload.get("title") is not None else None,
        affected_blueprints=_string_list(payload.get("affected_blueprints")),
        changed_files=_string_list(payload.get("changed_files")),
        proposed_files=_safe_proposed_files(payload.get("proposed_files")),
        approved_diff=str(payload["approved_diff"]) if payload.get("approved_diff") is not None else None,
        diff_preview=str(payload["diff_preview"]) if payload.get("diff_preview") is not None else None,
        confidence=str(payload["confidence"]) if payload.get("confidence") is not None else None,
        rationale=str(payload["rationale"]) if payload.get("rationale") is not None else None,
        source_drift_id=str(payload["source_drift_id"]) if payload.get("source_drift_id") is not None else None,
        review_note=str(payload["review_note"]) if payload.get("review_note") is not None else None,
        generated=bool(payload.get("generated", True)),
        persisted=False,
        transitions=[
            ProposalTransition(
                status="drafted",
                timestamp=_now_timestamp(),
                actor="dashboard-blueprint-review",
            )
        ],
        applied=False,
        action_taken=False,
        fingerprint=str(payload["fingerprint"]) if payload.get("fingerprint") is not None else None,
        deduped=True,
        warnings=["review_recorded_from_dashboard_snapshot"],
    )


def _project_root(project_id: str) -> Path | None:
    for project in discover_projects():
        if project.project_id == project_id:
            return Path(project.root)
    return None


def _status_for_decision(decision: ReviewDecision) -> str:
    if decision == "approve":
        return "approved"
    if decision == "reject":
        return "rejected"
    if decision == "defer":
        return "deferred"
    if decision == "mark_stale":
        return "stale"
    return "drafted"


def _proposal_path(project_root: Path, proposal: ProposalRecord, next_status: str) -> Path:
    proposal_root = project_root / "_blueprints" / "proposals"
    status = next_status if next_status in PROPOSAL_STATES else "drafted"
    return proposal_root / status / f"{proposal.proposal_id}.json"


def _existing_proposal_path(proposal_root: Path, proposal_id: str) -> Path | None:
    if not proposal_root.exists() or not proposal_root.is_dir():
        return None
    try:
        files = sorted(proposal_root.rglob("*.json"))
    except OSError:
        return None
    for path in files:
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("proposal_id") or "") == proposal_id:
            return path
    return None


def _payload_for_proposal(proposal: ProposalRecord) -> dict[str, Any]:
    payload = asdict(proposal)
    payload.pop("warnings", None)
    payload["generated"] = False
    payload["persisted"] = True
    payload["deduped"] = True
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _safe_proposed_files(value: Any) -> list[str]:
    return [
        path
        for path in _string_list(value)
        if path.startswith("_blueprints/")
        and ".." not in path.split("/")
        and not path.startswith("_blueprints/proposals/")
    ]


def _transition_payloads(proposal: ProposalRecord) -> list[dict[str, str]]:
    transitions: list[dict[str, str]] = []
    for transition in proposal.transitions:
        if transition.status and transition.timestamp and transition.actor:
            transitions.append(
                {
                    "status": str(transition.status),
                    "timestamp": str(transition.timestamp),
                    "actor": str(transition.actor),
                }
            )
    return transitions


def _now_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
