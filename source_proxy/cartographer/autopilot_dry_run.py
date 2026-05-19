from __future__ import annotations

from dataclasses import replace

from source_proxy.cartographer.autopilot_config import docs_autopilot_config
from source_proxy.cartographer.models import ProposalRecord
from source_proxy.cartographer.proposal_previews import draft_proposals_from_drift


def build_docs_autopilot_dry_run_proposals() -> dict[str, object]:
    config = docs_autopilot_config()
    proposals = [_dry_run_proposal(proposal) for proposal in draft_proposals_from_drift()]
    return {
        "dry_run": True,
        "status": "observing",
        "write_actions_enabled": False,
        "docs_autopilot_enabled": config["docs_autopilot_enabled"],
        "docs_autopilot_daily_cap": config["docs_autopilot_daily_cap"],
        "autopilot_kill_switch": config["autopilot_kill_switch"],
        "autopilot_action_available": False,
        "approval_available": False,
        "apply_available": False,
        "commit_enabled": False,
        "push_enabled": False,
        "proposals": proposals,
        "proposal_count": len(proposals),
        "actions_taken": False,
        "safety": {
            "dry_run_only": True,
            "writes_files": False,
            "approval_required_before_apply": True,
            "approval_unavailable_until_explicitly_enabled": True,
        },
    }


def _dry_run_proposal(proposal: ProposalRecord) -> dict[str, object]:
    preview = replace(
        proposal,
        status="drafted",
        requires_approval=False,
        generated=True,
        persisted=False,
        applied=False,
        action_taken=False,
    )
    return {
        "dry_run": True,
        "approval_available": False,
        "apply_available": False,
        "commit_enabled": False,
        "push_enabled": False,
        "would_write_files": False,
        "action_taken": False,
        **_proposal_payload(preview),
    }


def _proposal_payload(proposal: ProposalRecord) -> dict[str, object]:
    return {
        "proposal_id": proposal.proposal_id,
        "project_id": proposal.project_id,
        "status": proposal.status,
        "type": proposal.type,
        "component": proposal.component,
        "title": proposal.title,
        "affected_blueprints": proposal.affected_blueprints,
        "changed_files": proposal.changed_files,
        "proposed_files": proposal.proposed_files,
        "diff_preview": proposal.diff_preview or "",
        "confidence": proposal.confidence,
        "rationale": proposal.rationale,
        "source_drift_id": proposal.source_drift_id,
        "generated": proposal.generated,
        "persisted": proposal.persisted,
        "fingerprint": proposal.fingerprint,
    }
