from __future__ import annotations

from hashlib import sha256

from source_proxy.cartographer.blueprint_scribe import draft_blueprint_updates
from source_proxy.cartographer.change_scribe import summarize_changes
from source_proxy.cartographer.models import (
    BlueprintScribeDraft,
    ProposalRecord,
    RunbookScribeSuggestion,
    SubCartographerRole,
    SubCartographerRoute,
)
from source_proxy.cartographer.proposals import list_proposals
from source_proxy.cartographer.runbook_scribe import suggest_runbook_updates


def sub_cartographer_roles() -> list[SubCartographerRole]:
    return [
        SubCartographerRole(
            role_id="component_mapper",
            label="Component Mapper",
            responsibility="Map changed paths to known components and blueprint ownership.",
            consumes=["repo_map", "git_changed_files", "component_rules"],
            produces=["component_matches", "unmapped_paths"],
        ),
        SubCartographerRole(
            role_id="change_scribe",
            label="Change Scribe",
            responsibility="Summarize Git changes with evidence and uncertainty notes.",
            consumes=["git_status", "component_matches", "drift_findings"],
            produces=["change_summary", "recommended_review_actions"],
        ),
        SubCartographerRole(
            role_id="blueprint_scribe",
            label="Blueprint Scribe",
            responsibility="Draft editable blueprint update proposals from drift evidence.",
            consumes=["drift_findings", "change_summary", "blueprint_registry"],
            produces=["blueprint_update_draft"],
        ),
        SubCartographerRole(
            role_id="runbook_scribe",
            label="Runbook Scribe",
            responsibility="Suggest manual QA checklist updates for UI and API behavior changes.",
            consumes=["drift_findings", "change_summary", "runbook_registry"],
            produces=["runbook_checklist_suggestion"],
        ),
        SubCartographerRole(
            role_id="commit_scribe",
            label="Commit Scribe",
            responsibility="Prepare commit-summary guidance after approved review, without committing.",
            consumes=["proposal_state", "git_status", "verification_results"],
            produces=["commit_summary_suggestion"],
        ),
        SubCartographerRole(
            role_id="project_onboarding_scribe",
            label="Project Onboarding Scribe",
            responsibility="Suggest blueprint onboarding steps for newly detected projects.",
            consumes=["project_markers", "blueprint_registry", "component_rules"],
            produces=["onboarding_suggestion"],
        ),
    ]


def route_sub_cartographers() -> list[SubCartographerRoute]:
    summaries_by_project = {summary.project_id: summary for summary in summarize_changes()}
    routes: list[SubCartographerRoute] = []
    routes.extend(_route_for_blueprint_draft(draft) for draft in draft_blueprint_updates())
    routes.extend(_route_for_runbook_suggestion(suggestion) for suggestion in suggest_runbook_updates())
    routes.extend(
        _route_for_starter_pack(proposal)
        for proposal in list_proposals()
        if proposal.type == "starter_blueprint_pack" and proposal.generated
    )
    routes.extend(
        _route_for_persisted_proposal(proposal)
        for proposal in list_proposals()
        if proposal.persisted
    )

    if not routes:
        return [
            SubCartographerRoute(
                route_id=_route_id("idle", project_id),
                project_id=project_id,
                proposal_id="none",
                contributors=["component_mapper", "change_scribe"],
                visible_outputs=[summary.summary],
                status="observing",
                action_taken=False,
            )
            for project_id, summary in summaries_by_project.items()
            if summary.summary
        ]
    return routes


def _route_for_blueprint_draft(draft: BlueprintScribeDraft) -> SubCartographerRoute:
    return SubCartographerRoute(
        route_id=_route_id("blueprint", draft.proposal_id),
        project_id=draft.project_id,
        proposal_id=draft.proposal_id,
        contributors=["component_mapper", "change_scribe", "blueprint_scribe"],
        visible_outputs=[
            f"affected blueprint: {draft.affected_blueprint}",
            f"proposed file: {draft.proposed_file}",
            f"confidence: {draft.confidence}",
        ],
        action_taken=False,
    )


def _route_for_runbook_suggestion(suggestion: RunbookScribeSuggestion) -> SubCartographerRoute:
    return SubCartographerRoute(
        route_id=_route_id("runbook", suggestion.suggestion_id),
        project_id=suggestion.project_id,
        proposal_id=suggestion.suggestion_id,
        contributors=["component_mapper", "change_scribe", "runbook_scribe"],
        visible_outputs=[
            f"target runbook: {suggestion.target_runbook}",
            f"checklist items: {len(suggestion.checklist_items)}",
            f"expected outputs: {len(suggestion.expected_outputs)}",
        ],
        action_taken=False,
    )


def _route_for_starter_pack(proposal: ProposalRecord) -> SubCartographerRoute:
    return SubCartographerRoute(
        route_id=_route_id("starter", proposal.proposal_id),
        project_id=proposal.project_id,
        proposal_id=proposal.proposal_id,
        contributors=["project_onboarding_scribe"],
        visible_outputs=[
            "starter blueprint pack pending approval",
            f"proposed files: {len(proposal.proposed_files)}",
            "files written: 0",
        ],
        action_taken=False,
    )


def _route_for_persisted_proposal(proposal: ProposalRecord) -> SubCartographerRoute:
    contributors = ["component_mapper", "change_scribe"]
    if proposal.type == "blueprint_update":
        contributors.append("blueprint_scribe")
    if proposal.status in {"commit_pending", "commit_approved", "push_pending", "push_approved"}:
        contributors.append("commit_scribe")

    return SubCartographerRoute(
        route_id=_route_id("proposal", proposal.proposal_id),
        project_id=proposal.project_id,
        proposal_id=proposal.proposal_id,
        contributors=list(dict.fromkeys(contributors)),
        visible_outputs=[
            f"proposal status: {proposal.status}",
            f"component: {proposal.component}",
            f"proposed files: {len(proposal.proposed_files)}",
        ],
        action_taken=False,
    )


def _route_id(prefix: str, value: str) -> str:
    return f"sub-route-{sha256(f'{prefix}|{value}'.encode('utf-8')).hexdigest()[:12]}"
