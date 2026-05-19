from __future__ import annotations

from hashlib import sha256

from source_proxy.cartographer.blueprint_scribe import draft_blueprint_updates
from source_proxy.cartographer.change_scribe import summarize_changes
from source_proxy.cartographer.models import (
    BlueprintScribeDraft,
    ProposalRecord,
    SubCartographerControlRoute,
    SubCartographerOutput,
    RunbookScribeSuggestion,
    SubCartographerRole,
    SubCartographerRoute,
)
from source_proxy.cartographer.proposals import list_proposals
from source_proxy.cartographer.runbook_scribe import suggest_runbook_updates


FORBIDDEN_SUB_CARTOGRAPHER_ACTIONS = ["approve", "apply", "commit", "push", "delete"]
ROLE_OUTPUT_RECOMMENDATIONS = {
    "component_mapper": "Review unmapped or blocked-risk paths before treating the change set as understood.",
    "change_scribe": "Use the evidence list to decide whether the dirty tree needs human review.",
    "blueprint_scribe": "Review the draft before approving any doc-only blueprint update.",
    "runbook_scribe": "Run or update the named manual checklist before accepting the change.",
    "commit_scribe": "Review grouped files and required checks before any commit approval.",
    "project_onboarding_scribe": "Inspect the generated starter pack before approving any file write.",
}
ROLE_MANUAL_CHECKS = {
    "component_mapper": "curl -k -s https://localhost:3000/v1/cartographer/components | jq .",
    "change_scribe": "curl -k -s https://localhost:3000/v1/cartographer/change-scribe | jq .",
    "blueprint_scribe": "curl -k -s https://localhost:3000/v1/cartographer/blueprint-scribe | jq .",
    "runbook_scribe": "curl -k -s https://localhost:3000/v1/cartographer/runbook-scribe | jq .",
    "commit_scribe": "curl -k -s https://localhost:3000/v1/cartographer/commit-proposals | jq .",
    "project_onboarding_scribe": "curl -k -s https://localhost:3000/v1/cartographer/starter-blueprints | jq .",
}


def _role(
    *,
    role_id: str,
    label: str,
    responsibility: str,
    inputs: list[str],
    outputs: list[str],
    max_authority: str = "read_only",
) -> SubCartographerRole:
    return SubCartographerRole(
        role_id=role_id,
        label=label,
        responsibility=responsibility,
        consumes=inputs,
        produces=outputs,
        allowed_inputs=inputs,
        allowed_outputs=outputs,
        max_authority=max_authority,
        forbidden_actions=FORBIDDEN_SUB_CARTOGRAPHER_ACTIONS,
        can_write_files=False,
        can_approve=False,
        can_apply=False,
        can_commit=False,
        can_push=False,
        can_delete=False,
        failure_policy="stop_at_proposal_queue",
    )


def sub_cartographer_roles() -> list[SubCartographerRole]:
    return [
        _role(
            role_id="component_mapper",
            label="Component Mapper",
            responsibility="Map changed paths to known components and blueprint ownership.",
            inputs=["repo_map", "git_changed_files", "component_rules"],
            outputs=["component_matches", "unmapped_paths"],
        ),
        _role(
            role_id="change_scribe",
            label="Change Scribe",
            responsibility="Summarize Git changes with evidence and uncertainty notes.",
            inputs=["git_status", "component_matches", "drift_findings"],
            outputs=["change_summary", "recommended_review_actions"],
        ),
        _role(
            role_id="blueprint_scribe",
            label="Blueprint Scribe",
            responsibility="Draft editable blueprint update proposals from drift evidence.",
            inputs=["drift_findings", "change_summary", "blueprint_registry"],
            outputs=["blueprint_update_draft"],
            max_authority="proposal_only",
        ),
        _role(
            role_id="runbook_scribe",
            label="Runbook Scribe",
            responsibility="Suggest manual QA checklist updates for UI and API behavior changes.",
            inputs=["drift_findings", "change_summary", "runbook_registry"],
            outputs=["runbook_checklist_suggestion"],
            max_authority="proposal_only",
        ),
        _role(
            role_id="commit_scribe",
            label="Commit Scribe",
            responsibility="Prepare commit-summary guidance after approved review, without committing.",
            inputs=["proposal_state", "git_status", "verification_results"],
            outputs=["commit_summary_suggestion"],
            max_authority="proposal_only",
        ),
        _role(
            role_id="project_onboarding_scribe",
            label="Project Onboarding Scribe",
            responsibility="Suggest blueprint onboarding steps for newly detected projects.",
            inputs=["project_markers", "blueprint_registry", "component_rules"],
            outputs=["onboarding_suggestion"],
            max_authority="proposal_only",
        ),
    ]


def sub_cartographer_outputs() -> list[SubCartographerOutput]:
    return [_output_for_role(role) for role in sub_cartographer_roles()]


def route_control_plane_situations() -> list[SubCartographerControlRoute]:
    summaries = summarize_changes()
    blueprint_drafts = draft_blueprint_updates()
    runbook_suggestions = suggest_runbook_updates()
    proposals = list_proposals()
    routes: list[SubCartographerControlRoute] = []

    dirty_files = sorted({path for summary in summaries if summary.dirty for path in summary.changed_files})
    if dirty_files:
        routes.append(
            _control_route(
                situation="dirty_tree",
                selected_roles=["component_mapper", "change_scribe", "commit_scribe"],
                reason="Dirty tree needs component mapping, change explanation, and commit grouping review.",
                evidence=[
                    f"dirty files: {len(dirty_files)}",
                    *[f"changed: {path}" for path in dirty_files[:10]],
                ],
            )
        )

    if blueprint_drafts:
        routes.append(
            _control_route(
                situation="blueprint_drift",
                selected_roles=["component_mapper", "change_scribe", "blueprint_scribe"],
                reason="Blueprint drift needs affected-component context and a doc-only draft proposal.",
                evidence=[
                    f"drafts: {len(blueprint_drafts)}",
                    *[f"proposal: {draft.proposal_id}" for draft in blueprint_drafts[:10]],
                ],
            )
        )

    if runbook_suggestions:
        routes.append(
            _control_route(
                situation="runbook_gap",
                selected_roles=["component_mapper", "change_scribe", "runbook_scribe"],
                reason="Manual QA drift needs a runbook scribe suggestion before review.",
                evidence=[
                    f"suggestions: {len(runbook_suggestions)}",
                    *[f"suggestion: {suggestion.suggestion_id}" for suggestion in runbook_suggestions[:10]],
                ],
            )
        )

    starter_proposals = [
        proposal
        for proposal in proposals
        if proposal.type == "starter_blueprint_pack" and proposal.generated
    ]
    if starter_proposals:
        routes.append(
            _control_route(
                situation="new_project",
                selected_roles=["project_onboarding_scribe", "blueprint_scribe"],
                reason="New project candidates need starter blueprint review before any files are written.",
                evidence=[
                    f"starter proposals: {len(starter_proposals)}",
                    *[f"proposal: {proposal.proposal_id}" for proposal in starter_proposals[:10]],
                ],
            )
        )

    push_proposals = [
        proposal
        for proposal in proposals
        if proposal.status in {"push_pending", "push_approved"}
    ]
    if push_proposals:
        routes.append(
            _control_route(
                situation="push_queue",
                selected_roles=["commit_scribe", "change_scribe"],
                reason="Push readiness needs Git-state inspection and safety evidence before approval.",
                evidence=[
                    f"push proposals: {len(push_proposals)}",
                    *[f"proposal: {proposal.proposal_id}" for proposal in push_proposals[:10]],
                ],
            )
        )

    return routes


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


def _control_route(
    *,
    situation: str,
    selected_roles: list[str],
    reason: str,
    evidence: list[str],
) -> SubCartographerControlRoute:
    return SubCartographerControlRoute(
        route_id=_route_id("control-plane", situation),
        situation=situation,
        selected_roles=selected_roles,
        reason=reason,
        evidence=evidence,
        parent_control_plane_required=True,
        approval_gate_required=True,
        mutation_allowed=False,
        action_taken=False,
    )


def _output_for_role(role: SubCartographerRole) -> SubCartographerOutput:
    forbidden_respected = (
        all(action in role.forbidden_actions for action in FORBIDDEN_SUB_CARTOGRAPHER_ACTIONS)
        and not role.can_write_files
        and not role.can_approve
        and not role.can_apply
        and not role.can_commit
        and not role.can_push
        and not role.can_delete
    )
    return SubCartographerOutput(
        role_id=role.role_id,
        summary=f"{role.label} returns {', '.join(role.allowed_outputs)} from {', '.join(role.allowed_inputs)}.",
        evidence=[
            f"max authority: {role.max_authority}",
            f"allowed inputs: {', '.join(role.allowed_inputs)}",
            f"allowed outputs: {', '.join(role.allowed_outputs)}",
            f"forbidden actions: {', '.join(role.forbidden_actions)}",
        ],
        recommendation=ROLE_OUTPUT_RECOMMENDATIONS[role.role_id],
        risk="low" if role.max_authority == "read_only" else "medium",
        required_approval=role.max_authority != "read_only",
        forbidden_actions_respected=forbidden_respected,
        next_manual_check=ROLE_MANUAL_CHECKS[role.role_id],
        action_taken=False,
    )
