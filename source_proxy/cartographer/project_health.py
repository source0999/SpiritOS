from __future__ import annotations

from collections import Counter

from source_proxy.cartographer.blueprint_registry import list_blueprints
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.git_status import read_git_statuses
from source_proxy.cartographer.models import ProjectHealth
from source_proxy.cartographer.project_discovery import discover_project_candidates, discover_projects
from source_proxy.cartographer.proposals import list_proposals


def build_project_health() -> list[ProjectHealth]:
    blueprints_by_project = Counter(blueprint.project_id for blueprint in list_blueprints())
    drift_by_project = Counter(finding.project_id for finding in detect_blueprint_drift())
    proposals_by_project = Counter(
        proposal.project_id
        for proposal in list_proposals()
        if proposal.status in {"detected", "drafted", "pending_review"}
    )
    git_by_project = {
        status.project_id: status
        for status in read_git_statuses()
        if status.project_id
    }

    health: list[ProjectHealth] = []
    candidate_roots = set()
    for candidate in discover_project_candidates():
        candidate_roots.add(candidate.root)
        health.append(
            ProjectHealth(
                project_id=candidate.project_id,
                name=candidate.name,
                root=candidate.root,
                status="needs_starter_blueprint_approval",
                blueprint_health="missing_starter_blueprints",
                blueprint_count=0,
                pending_drift=0,
                pending_proposals=proposals_by_project[candidate.project_id],
                markers=candidate.markers,
                filters=["candidate", "needs_approval"],
                action_taken=False,
            )
        )

    for project in discover_projects():
        if project.root in candidate_roots:
            continue
        git_status = git_by_project.get(project.project_id)
        blueprint_count = blueprints_by_project[project.project_id]
        pending_drift = drift_by_project[project.project_id]
        pending_proposals = proposals_by_project[project.project_id]
        health.append(
            ProjectHealth(
                project_id=project.project_id,
                name=project.name,
                root=project.root,
                status=_project_status(
                    blueprint_count=blueprint_count,
                    pending_drift=pending_drift,
                    pending_proposals=pending_proposals,
                ),
                blueprint_health=_blueprint_health(
                    blueprint_count=blueprint_count,
                    pending_drift=pending_drift,
                ),
                blueprint_count=blueprint_count,
                pending_drift=pending_drift,
                pending_proposals=pending_proposals,
                dirty=bool(git_status and git_status.dirty),
                branch=git_status.branch if git_status else None,
                markers=project.markers,
                filters=_filters(
                    blueprint_count=blueprint_count,
                    pending_drift=pending_drift,
                    pending_proposals=pending_proposals,
                    dirty=bool(git_status and git_status.dirty),
                ),
                action_taken=False,
            )
        )

    return sorted(health, key=lambda item: (item.status != "active", item.name.lower()))


def _project_status(
    *,
    blueprint_count: int,
    pending_drift: int,
    pending_proposals: int,
) -> str:
    if blueprint_count == 0:
        return "needs_starter_blueprint_approval"
    if pending_proposals:
        return "pending_proposal_review"
    if pending_drift:
        return "drift_review_suggested"
    return "active"


def _blueprint_health(*, blueprint_count: int, pending_drift: int) -> str:
    if blueprint_count == 0:
        return "missing_starter_blueprints"
    if pending_drift:
        return "review_suggested"
    return "healthy"


def _filters(
    *,
    blueprint_count: int,
    pending_drift: int,
    pending_proposals: int,
    dirty: bool,
) -> list[str]:
    filters = ["active" if blueprint_count else "needs_approval"]
    if pending_drift:
        filters.append("drift")
    if pending_proposals:
        filters.append("pending_proposals")
    if dirty:
        filters.append("dirty")
    return filters
