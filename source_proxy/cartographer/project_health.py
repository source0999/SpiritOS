from __future__ import annotations

from collections import Counter

from source_proxy.cartographer.blueprint_registry import list_blueprints
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.git_approvals import read_git_approval_records
from source_proxy.cartographer.git_status import read_git_statuses
from source_proxy.cartographer.models import GitStatus, ProjectHealth
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
        readiness = _merge_readiness(
            project_id=project.project_id,
            git_status=git_status,
            pending_drift=pending_drift,
            pending_proposals=pending_proposals,
        )
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
                merge_ready=readiness["merge_ready"],
                merge_blockers=readiness["merge_blockers"],
                recommended_next_step=readiness["recommended_next_step"],
                merge_target=readiness["merge_target"],
                pushed=readiness["pushed"],
                checks_passed=readiness["checks_passed"],
                markers=project.markers,
                filters=_filters(
                    blueprint_count=blueprint_count,
                    pending_drift=pending_drift,
                    pending_proposals=pending_proposals,
                    dirty=bool(git_status and git_status.dirty),
                    merge_ready=readiness["merge_ready"],
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
    merge_ready: bool,
) -> list[str]:
    filters = ["active" if blueprint_count else "needs_approval"]
    if pending_drift:
        filters.append("drift")
    if pending_proposals:
        filters.append("pending_proposals")
    if dirty:
        filters.append("dirty")
    if merge_ready:
        filters.append("merge_ready")
    return filters


def _merge_readiness(
    *,
    project_id: str,
    git_status: GitStatus | None,
    pending_drift: int,
    pending_proposals: int,
) -> dict[str, object]:
    blockers: list[str] = []
    if git_status is None or not git_status.available:
        blockers.append("git status unavailable")
        return _readiness_payload(blockers, pushed=False, checks_passed=False, merge_target=None)

    merge_target = _merge_target(git_status.upstream)
    pushed = _push_audit_exists(project_id, git_status.branch)
    checks_passed = _latest_commit_checks_passed(project_id, git_status.branch)

    if git_status.dirty:
        blockers.append("working tree has uncommitted changes")
    if git_status.ahead > 0:
        blockers.append("branch has unpushed commits")
    if git_status.behind > 0:
        blockers.append("branch is behind upstream")
    if not git_status.upstream:
        blockers.append("merge target unknown")
    if git_status.branch in {None, "main", "master", "trunk"}:
        blockers.append("work is not on a review branch")
    if pending_drift:
        blockers.append("blueprint drift unresolved")
    if pending_proposals:
        blockers.append("proposal review still pending")
    if not pushed:
        blockers.append("push audit missing")
    if not checks_passed:
        blockers.append("required checks not recorded as passed")

    return _readiness_payload(
        blockers,
        pushed=pushed,
        checks_passed=checks_passed,
        merge_target=merge_target,
    )


def _readiness_payload(
    blockers: list[str],
    *,
    pushed: bool,
    checks_passed: bool,
    merge_target: str | None,
) -> dict[str, object]:
    return {
        "merge_ready": not blockers,
        "merge_blockers": blockers,
        "recommended_next_step": _recommended_next_step(blockers),
        "merge_target": merge_target,
        "pushed": pushed,
        "checks_passed": checks_passed,
    }


def _recommended_next_step(blockers: list[str]) -> str:
    if not blockers:
        return "open merge review"
    if "working tree has uncommitted changes" in blockers:
        return "commit or discard remaining local changes"
    if "branch has unpushed commits" in blockers:
        return "push branch after approval"
    if "proposal review still pending" in blockers:
        return "review pending Cartographer proposals"
    if "blueprint drift unresolved" in blockers:
        return "resolve or accept blueprint drift"
    if "required checks not recorded as passed" in blockers:
        return "run required checks before merge review"
    if "merge target unknown" in blockers:
        return "set upstream or merge target"
    return "resolve merge blockers"


def _merge_target(upstream: str | None) -> str | None:
    if not upstream:
        return None
    remote, _separator, branch = upstream.partition("/")
    if not remote or not branch:
        return upstream
    return f"{remote}/{branch}"


def _push_audit_exists(project_id: str, branch: str | None) -> bool:
    if not branch:
        return False
    return any(
        record.get("project_id") == project_id
        and record.get("event") == "push_approved"
        and record.get("result") == "pushed"
        and record.get("branch") == branch
        for record in read_git_approval_records()
    )


def _latest_commit_checks_passed(project_id: str, branch: str | None) -> bool:
    if not branch:
        return False
    for record in reversed(read_git_approval_records()):
        if (
            record.get("project_id") == project_id
            and record.get("event") == "commit_created"
            and record.get("branch") == branch
        ):
            checks = record.get("checks")
            if not isinstance(checks, list) or not checks:
                return False
            required = {"git_diff_check", "blueprint_metadata_validation", "cartographer_pytest"}
            passed = {
                str(check.get("id"))
                for check in checks
                if isinstance(check, dict) and check.get("status") == "passed"
            }
            return required.issubset(passed)
    return False
