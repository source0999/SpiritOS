from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from source_proxy.cartographer.clutter_inventory import build_clutter_inventory
from source_proxy.cartographer.models import ClutterCandidate, ClutterDeletionProposal
from source_proxy.cartographer.project_discovery import discover_projects
from source_proxy.approval.external_gate import central_gate_check

_MAX_LOW_RISK_FILES_PER_PROPOSAL = 50


class ClutterCleanupError(ValueError):
    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def build_low_risk_deletion_proposals() -> dict[str, object]:
    candidates = build_clutter_inventory()
    low_risk = [
        candidate
        for candidate in candidates
        if candidate.risk == "low" and not candidate.deletion_allowed and not candidate.action_taken
    ][:_MAX_LOW_RISK_FILES_PER_PROPOSAL]
    review_required = [candidate for candidate in candidates if candidate.risk != "low"]
    proposals = [_proposal_for_low_risk_candidates(low_risk)] if low_risk else []
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "deletion_enabled": False,
        "cleanup_actions_enabled": False,
        "actions_taken": False,
        "proposal_count": len(proposals),
        "proposals": proposals,
        "low_risk_candidate_count": len(low_risk),
        "review_required_count": len(review_required),
        "review_required": review_required,
        "proposal_policy": "proposal_only_no_deletion",
    }


def apply_approved_low_risk_deletion_proposal(
    *,
    proposal_id: str,
    approved: bool,
    approved_by: str,
) -> dict[str, object]:
    central_gate_check("apply", run_id=f"cartographer_clutter_cleanup:{proposal_id}")
    if not approved:
        raise ClutterCleanupError(
            "approved must be true before low-risk cleanup can run.",
            "approval_required",
        )
    proposal = _find_proposal(proposal_id)
    files = list(proposal.files)
    if not files:
        raise ClutterCleanupError("Deletion proposal has no files.", "empty_proposal")

    projects = discover_projects()
    if len(projects) != 1:
        raise ClutterCleanupError(
            "Approved low-risk cleanup requires exactly one configured project root.",
            "ambiguous_project_root",
        )
    root = Path(projects[0].root)
    low_risk_paths = {candidate.path for candidate in build_clutter_inventory() if candidate.risk == "low"}
    deleted_files: list[str] = []
    for relative in files:
        if relative not in low_risk_paths:
            raise ClutterCleanupError(
                f"Refusing to delete non-low-risk path: {relative}",
                "non_low_risk_path",
            )
        target = _safe_target(root, relative)
        if not target.exists() or not target.is_file():
            continue
        target.unlink()
        deleted_files.append(relative)

    audit_event = _write_cleanup_audit(
        root=root,
        proposal=proposal,
        deleted_files=deleted_files,
        approved_by=approved_by,
    )
    return {
        "status": "cleanup_applied",
        "write_actions_enabled": True,
        "deletion_enabled": True,
        "cleanup_actions_enabled": True,
        "actions_taken": bool(deleted_files),
        "proposal_id": proposal.proposal_id,
        "approved_by": approved_by,
        "deleted_files": deleted_files,
        "deleted_file_count": len(deleted_files),
        "rollback_instructions": proposal.rollback_instructions,
        "audit_event": audit_event,
        "committed": False,
        "pushed": False,
    }


def _proposal_for_low_risk_candidates(candidates: list[ClutterCandidate]) -> ClutterDeletionProposal:
    files = [candidate.path for candidate in candidates]
    return ClutterDeletionProposal(
        proposal_id=f"cleanup-prop-{_fingerprint(files)}",
        files=files,
        file_count=len(files),
        reason="Low-risk generated clutter candidates may be deleted only after explicit future approval.",
        confidence="high" if all(candidate.confidence == "high" for candidate in candidates) else "medium",
        rollback_instructions=[
            "No deletion has occurred; this is a proposal only.",
            "Before any approved deletion, ensure files are committed, backed up, or intentionally disposable.",
            "For tracked files, restore with git restore -- <file> after review.",
            "For untracked generated files, regenerate them from the owning soak/report command if needed.",
        ],
        requires_approval=True,
        deletion_enabled=False,
        action_taken=False,
    )


def _fingerprint(files: list[str]) -> str:
    return sha256("\n".join(sorted(files)).encode("utf-8")).hexdigest()[:12]


def _find_proposal(proposal_id: str) -> ClutterDeletionProposal:
    proposals = build_low_risk_deletion_proposals()["proposals"]
    for proposal in proposals:
        if isinstance(proposal, ClutterDeletionProposal) and proposal.proposal_id == proposal_id:
            return proposal
    raise ClutterCleanupError("Cleanup proposal was not found.", "proposal_not_found")


def _safe_target(root: Path, relative: str) -> Path:
    if relative.startswith("/") or ".." in Path(relative).parts:
        raise ClutterCleanupError("Refusing unsafe cleanup path.", "unsafe_path")
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as error:
        raise ClutterCleanupError("Refusing cleanup path outside project root.", "path_outside_root") from error
    return target


def _write_cleanup_audit(
    *,
    root: Path,
    proposal: ClutterDeletionProposal,
    deleted_files: list[str],
    approved_by: str,
) -> dict[str, object]:
    approved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload: dict[str, object] = {
        "event": "low_risk_cleanup_applied",
        "action": "delete_low_risk_clutter",
        "proposal_id": proposal.proposal_id,
        "approved_by": approved_by,
        "approved_at": approved_at,
        "changed_files": deleted_files,
        "deleted_files": deleted_files,
        "reason": proposal.reason,
        "result": "deleted" if deleted_files else "no_matching_files",
        "rollback_instructions": proposal.rollback_instructions,
        "committed": False,
        "pushed": False,
    }
    audit_path = root / "data" / "approved_actions.audit.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return payload
