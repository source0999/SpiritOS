from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from source_proxy.cartographer.autopilot_config import docs_autopilot_config
from source_proxy.cartographer.git_status import read_git_status_for_project
from source_proxy.cartographer.models import ProposalRecord
from source_proxy.cartographer.proposal_previews import draft_proposals_from_drift
from source_proxy.cartographer.project_discovery import discover_projects


def build_docs_autopilot_dry_run_proposals() -> dict[str, object]:
    config = docs_autopilot_config()
    git_before = _git_status()
    proposals = [_dry_run_proposal(proposal) for proposal in draft_proposals_from_drift()]
    git_after = _git_status()
    status_delta = sorted(set(git_after["changed_files"]) - set(git_before["changed_files"]))
    return {
        "dry_run": True,
        "level": 1,
        "mode": "dry_run",
        "status": "observing",
        "authority_granted": False,
        "write_actions_enabled": False,
        "docs_autopilot_enabled": config["docs_autopilot_enabled"],
        "docs_autopilot_daily_cap": config["docs_autopilot_daily_cap"],
        "autopilot_kill_switch": config["autopilot_kill_switch"],
        "autopilot_action_available": False,
        "apply_enabled": False,
        "approval_available": False,
        "apply_available": False,
        "commit_enabled": False,
        "push_enabled": False,
        "operator_review_required": True,
        "recommended_next_action": "operator_review_required",
        "git_head_before": git_before["head_sha"],
        "git_head_after": git_after["head_sha"],
        "head_changed": git_before["head_sha"] != git_after["head_sha"],
        "unexpected_status_delta": status_delta,
        "dirty_tree_summary": {
            "changed_files": git_after["changed_files"],
            "staged_files": git_after["staged_files"],
            "unstaged_files": git_after["unstaged_files"],
            "untracked_files": git_after["untracked_files"],
        },
        "allowed_scope": ["docs/**/*.md", "README.md", "named top-level markdown plans"],
        "forbidden_scope": ["src/**", "source_proxy/**", "scout/src/**", "tests/**", ".env*", "secrets"],
        "candidates": [_dry_run_candidate(proposal) for proposal in proposals],
        "candidate_count": len(proposals),
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
        "approval_required": True,
        "apply_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "commit_enabled": False,
        "push_enabled": False,
        "would_write_files": False,
        "action_taken": False,
        **_proposal_payload(preview),
    }


def _dry_run_candidate(proposal: dict[str, object]) -> dict[str, object]:
    return {
        "proposal_id": proposal["proposal_id"],
        "project_id": proposal["project_id"],
        "component": proposal["component"],
        "title": proposal["title"],
        "changed_files": proposal["changed_files"],
        "proposed_files": proposal["proposed_files"],
        "risk_level": "low",
        "blocked": False,
        "why_no_source_edit_is_needed": "Dry run creates proposal evidence only; source edits require later human approval.",
    }


def _git_status() -> dict[str, object]:
    project = _first_project()
    if project is None:
        return {
            "head_sha": None,
            "changed_files": [],
            "staged_files": [],
            "unstaged_files": [],
            "untracked_files": [],
        }
    status = read_git_status_for_project(project_id=project.project_id, root=Path(project.root))
    return {
        "head_sha": status.head_sha,
        "changed_files": list(status.changed_files),
        "staged_files": list(status.staged_files),
        "unstaged_files": list(status.unstaged_files),
        "untracked_files": list(status.untracked_files),
    }


def _first_project() -> object | None:
    projects = discover_projects()
    if projects:
        return projects[0]
    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return type("CurrentProject", (), {"project_id": cwd.name.lower(), "root": str(cwd)})()
    return None


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
