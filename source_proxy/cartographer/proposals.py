from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from source_proxy.cartographer.blueprint_scribe import draft_codex_trial_summary_updates
from source_proxy.cartographer.models import ProposalRecord, ProposalTransition
from source_proxy.cartographer.proposal_previews import draft_proposals_from_drift, proposal_fingerprint
from source_proxy.cartographer.project_discovery import discover_projects
from source_proxy.cartographer.starter_blueprints import draft_starter_blueprint_pack_proposals


PROPOSAL_STATES = (
    "detected",
    "drafted",
    "pending_review",
    "approved",
    "rejected",
    "deferred",
    "stale",
    "applied",
    "commit_pending",
    "commit_approved",
    "push_pending",
    "push_approved",
    "pushed",
    "failed",
)
PENDING_PROPOSAL_STATES = {"detected", "drafted", "pending_review"}
FALLBACK_TRANSITION_TIMESTAMP = "1970-01-01T00:00:00Z"
FALLBACK_TRANSITION_ACTOR = "unknown"


def list_proposals() -> list[ProposalRecord]:
    proposals, _suppressed = _collect_proposals()
    return proposals


def proposal_visibility_summary() -> dict[str, object]:
    proposals, suppressed = _collect_proposals()
    stale_cleanup_candidates = [
        {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "component": proposal.component,
            "cleanup_allowed": False,
            "reason": _cleanup_reason(proposal),
        }
        for proposal in proposals
        if proposal.status in {"rejected", "deferred", "stale"}
    ]
    return {
        "duplicate_proposals_suppressed": len(suppressed),
        "suppressed_duplicate_proposals": suppressed,
        "stale_cleanup_candidates": stale_cleanup_candidates,
        "stale_cleanup_candidate_count": len(stale_cleanup_candidates),
        "cleanup_actions_enabled": False,
    }


def _collect_proposals() -> tuple[list[ProposalRecord], list[dict[str, str]]]:
    proposals: list[ProposalRecord] = []
    suppressed: list[dict[str, str]] = []
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

    persisted_ids = {proposal.proposal_id for proposal in proposals}
    persisted_fingerprints = {
        proposal.fingerprint
        for proposal in proposals
        if proposal.fingerprint
    }
    for draft in draft_proposals_from_drift():
        if draft.proposal_id not in persisted_ids and draft.fingerprint not in persisted_fingerprints:
            proposals.append(draft)
        else:
            suppressed.append(_suppressed_duplicate(draft))
    for starter_pack in draft_starter_blueprint_pack_proposals():
        if starter_pack.proposal_id not in persisted_ids:
            proposals.append(starter_pack)
        else:
            suppressed.append(_suppressed_duplicate(starter_pack))
    for codex_summary in _draft_codex_summary_proposals():
        if (
            codex_summary.proposal_id not in persisted_ids
            and codex_summary.fingerprint not in persisted_fingerprints
        ):
            proposals.append(codex_summary)
        else:
            suppressed.append(_suppressed_duplicate(codex_summary))

    return sorted(proposals, key=lambda proposal: proposal.proposal_id), suppressed


def _suppressed_duplicate(proposal: ProposalRecord) -> dict[str, str]:
    return {
        "proposal_id": proposal.proposal_id,
        "component": proposal.component,
        "fingerprint": proposal.fingerprint or "",
        "reason": "matching_persisted_proposal_or_fingerprint",
    }


def _cleanup_reason(proposal: ProposalRecord) -> str:
    if proposal.status == "stale":
        return "Marked stale; safe cleanup requires explicit future archive/delete approval."
    if proposal.status == "deferred":
        return "Deferred proposal remains visible; cleanup is not allowed automatically."
    return "Rejected proposal suppresses duplicate previews; cleanup is not allowed automatically."


def _draft_codex_summary_proposals() -> list[ProposalRecord]:
    proposals: list[ProposalRecord] = []
    for draft in draft_codex_trial_summary_updates():
        fingerprint = proposal_fingerprint(
            project_id=draft.project_id,
            proposal_type="blueprint_update",
            component=draft.component,
            reason=draft.reason,
            changed_files=draft.changed_files,
            proposed_files=[draft.proposed_file],
            affected_blueprints=[draft.affected_blueprint],
        )
        proposals.append(
            ProposalRecord(
                proposal_id=draft.proposal_id.replace("bp-scribe-", "bp-"),
                project_id=draft.project_id,
                status="pending_review",
                type="blueprint_update",
                component=draft.component,
                requires_approval=True,
                title="Codex adapter trial blueprint summary",
                affected_blueprints=[draft.affected_blueprint],
                changed_files=draft.changed_files,
                proposed_files=[draft.proposed_file],
                diff_preview=_codex_summary_diff_preview(draft),
                confidence=draft.confidence,
                rationale=draft.reason,
                generated=True,
                persisted=False,
                fingerprint=fingerprint,
                deduped=True,
                transitions=[
                    ProposalTransition(
                        status="pending_review",
                        timestamp=FALLBACK_TRANSITION_TIMESTAMP,
                        actor="blueprint_scribe",
                    )
                ],
                applied=False,
                action_taken=False,
            )
        )
    return proposals


def _codex_summary_diff_preview(draft: Any) -> str:
    return "\n".join(
        [
            f"diff --git a/{draft.proposed_file} b/{draft.proposed_file}",
            f"--- a/{draft.proposed_file}",
            f"+++ b/{draft.proposed_file}",
            "@@",
            "+### Codex Adapter Trial Summary",
            f"+- Reason: {draft.reason}",
            f"+- Suggested update: {draft.suggested_update}",
            "+- Manual check: confirm the Codex evidence remains proposal-only before applying this blueprint update.",
            "",
        ]
    )


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
    changed_files = _string_list(payload.get("changed_files"))
    proposed_files = _string_list(payload.get("proposed_files"))
    affected_blueprints = _string_list(payload.get("affected_blueprints"))
    proposal_type = str(payload.get("type") or "blueprint_update")
    component = str(payload.get("component") or "unknown")
    fingerprint = str(payload.get("fingerprint") or _fingerprint_from_payload(
        project_id=project_id,
        proposal_type=proposal_type,
        component=component,
        payload=payload,
        changed_files=changed_files,
        proposed_files=proposed_files,
        affected_blueprints=affected_blueprints,
    ))
    applied = bool(payload.get("applied")) or status in {"applied", "commit_pending", "commit_approved", "push_pending", "push_approved", "pushed"}

    return ProposalRecord(
        proposal_id=proposal_id,
        project_id=project_id,
        status=status,
        type=proposal_type,
        component=component,
        requires_approval=_bool(payload.get("requires_approval"), default=True),
        title=str(payload["title"]) if payload.get("title") is not None else None,
        affected_blueprints=affected_blueprints,
        changed_files=changed_files,
        proposed_files=proposed_files,
        approved_diff=str(payload["approved_diff"]) if payload.get("approved_diff") is not None else None,
        diff_preview=str(payload["diff_preview"]) if payload.get("diff_preview") is not None else None,
        confidence=str(payload["confidence"]) if payload.get("confidence") is not None else None,
        rationale=str(payload["rationale"]) if payload.get("rationale") is not None else None,
        source_drift_id=(
            str(payload["source_drift_id"])
            if payload.get("source_drift_id") is not None
            else None
        ),
        review_note=str(payload["review_note"]) if payload.get("review_note") is not None else None,
        generated=False,
        persisted=True,
        rejection_reason=(
            str(payload["rejection_reason"])
            if payload.get("rejection_reason") is not None
            else None
        ),
        transitions=transitions,
        applied=applied,
        action_taken=applied,
        fingerprint=fingerprint,
        deduped=True,
        warnings=warnings,
        post_apply_verification=(
            payload.get("post_apply_verification")
            if isinstance(payload.get("post_apply_verification"), dict)
            else None
        ),
    )


def _fingerprint_from_payload(
    *,
    project_id: str,
    proposal_type: str,
    component: str,
    payload: dict[str, Any],
    changed_files: list[str],
    proposed_files: list[str],
    affected_blueprints: list[str],
) -> str:
    reason = str(payload.get("reason") or "")
    if not reason and isinstance(payload.get("rationale"), str):
        reason = str(payload["rationale"]).split(" affected ", 1)[0]
    return proposal_fingerprint(
        project_id=project_id,
        proposal_type=proposal_type,
        component=component,
        reason=reason or "unknown",
        changed_files=changed_files,
        proposed_files=proposed_files,
        affected_blueprints=affected_blueprints,
    )


def _status_from_path(rel_path: str) -> str | None:
    first_part = rel_path.split("/", 1)[0]
    return first_part if first_part in PROPOSAL_STATES else None


def _transitions(value: Any, status: str, warnings: list[str]) -> list[ProposalTransition]:
    if not isinstance(value, list) or not value:
        warnings.append("missing_transition_history")
        return [
            ProposalTransition(
                status=status,
                timestamp=FALLBACK_TRANSITION_TIMESTAMP,
                actor=FALLBACK_TRANSITION_ACTOR,
            )
        ]

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
                timestamp=(
                    str(timestamp)
                    if timestamp is not None
                    else FALLBACK_TRANSITION_TIMESTAMP
                ),
                actor=str(actor) if actor is not None else FALLBACK_TRANSITION_ACTOR,
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
