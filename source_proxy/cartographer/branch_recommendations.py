from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess

from source_proxy.cartographer.component_mapper import map_paths
from source_proxy.cartographer.git_status import read_git_status_for_project, read_git_statuses
from source_proxy.cartographer.models import BranchRecommendation, GitStatus
from source_proxy.cartographer.proposals import list_proposals


PRIMARY_BRANCHES = {"main", "master", "trunk"}
MANY_CHANGED_FILES_THRESHOLD = 8


def recommend_branches() -> list[BranchRecommendation]:
    recommendations: list[BranchRecommendation] = []
    statuses = read_git_statuses()
    if not statuses:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            statuses = [read_git_status_for_project(project_id=cwd.name.lower(), root=cwd)]
    for git_status in statuses:
        recommendation = _recommendation_for_status(git_status)
        if recommendation:
            recommendations.append(recommendation)
    return recommendations


def _recommendation_for_status(git_status: GitStatus) -> BranchRecommendation | None:
    if not git_status.available or not git_status.dirty:
        return None

    project_id = git_status.project_id or "unknown"
    changed_files = [_normalize_repo_path(path) for path in git_status.changed_files]
    changed_count = len(changed_files)
    current_branch = git_status.branch
    on_primary = current_branch in PRIMARY_BRANCHES
    many_changes = changed_count >= MANY_CHANGED_FILES_THRESHOLD
    applied_proposal_component = _applied_proposal_commit_component(project_id)
    applied_proposal_commit_needed = applied_proposal_component is not None

    if not on_primary and not many_changes and not applied_proposal_commit_needed:
        return None

    blockers = _blockers(git_status=git_status)
    suggested_branch = _suggested_branch(changed_files, fallback_component=applied_proposal_component)
    reason = _reason(
        current_branch=current_branch,
        changed_count=changed_count,
        on_primary=on_primary,
        many_changes=many_changes,
        applied_proposal_commit_needed=applied_proposal_commit_needed,
    )
    return BranchRecommendation(
        recommendation_id=_recommendation_id(project_id, current_branch, suggested_branch, changed_files),
        project_id=project_id,
        current_branch=current_branch,
        suggested_branch=suggested_branch,
        reason=reason,
        changed_file_count=changed_count,
        source_head=git_status.head_sha,
        dirty_state_requirement="dirty_worktree_required",
        rollback_command=_rollback_command(current_branch, suggested_branch),
        branch_exists=_branch_exists(git_status.root, suggested_branch),
        preview_generated=True,
        confidence=_confidence(
            on_primary=on_primary,
            many_changes=many_changes,
            applied_proposal_commit_needed=applied_proposal_commit_needed,
            blockers=blockers,
        ),
        recommendation="create_branch_after_approval",
        unsafe_to_create_branch=bool(blockers),
        blockers=blockers,
        merge_readiness="blocked",
        related_files=changed_files[:12],
        status="pending_approval",
        requires_approval=True,
        branch_creation_enabled=False,
        action_taken=False,
    )


def _reason(
    *,
    current_branch: str | None,
    changed_count: int,
    on_primary: bool,
    many_changes: bool,
    applied_proposal_commit_needed: bool,
) -> str:
    branch = current_branch or "detached"
    if applied_proposal_commit_needed and on_primary:
        return f"Applied proposal left docs changes uncommitted on {branch}; branch creation requires approval."
    if applied_proposal_commit_needed:
        return "Applied proposal left docs changes uncommitted; checkpoint branch requires approval."
    if many_changes:
        return f"Working tree has {changed_count} changed files; checkpoint branch requires approval."
    if on_primary:
        return f"Working tree dirty on {branch}; branch creation requires approval."
    return f"Working tree has {changed_count} changed files; checkpoint branch requires approval."


def _blockers(*, git_status: GitStatus) -> list[str]:
    blockers: list[str] = []
    if git_status.ahead > 0:
        blockers.append("branch has unpushed commits")
    if git_status.behind > 0:
        blockers.append("branch is behind upstream")
    if not git_status.upstream:
        reason = git_status.no_upstream_reason or "no_upstream_configured"
        blockers.append(f"upstream unavailable: {reason}")
    return blockers


def _confidence(
    *,
    on_primary: bool,
    many_changes: bool,
    applied_proposal_commit_needed: bool,
    blockers: list[str],
) -> str:
    if blockers:
        return "low"
    if applied_proposal_commit_needed or many_changes or on_primary:
        return "high"
    return "medium"


def _suggested_branch(changed_files: list[str], *, fallback_component: str | None = None) -> str:
    components, _unmapped = map_paths(
        [path for path in changed_files if not path.startswith("_blueprints/")]
    )
    component = components[0].component_id if components else fallback_component or "work"
    if component == "scout":
        return "scout/source-gate-polish"
    if component == "source-proxy":
        return "proxy/runner-closeout"
    if component.startswith("cartographer"):
        return "cartographer/scout-blueprint-review"
    return f"cartographer/{_slug(component)}-blueprint-review"


def _applied_proposal_commit_component(project_id: str) -> str | None:
    for proposal in list_proposals():
        if proposal.project_id == project_id and proposal.status == "applied" and proposal.applied:
            return proposal.component
    return None


def _recommendation_id(
    project_id: str,
    current_branch: str | None,
    suggested_branch: str,
    changed_files: list[str],
) -> str:
    key = "|".join([project_id, current_branch or "detached", suggested_branch, ",".join(changed_files)])
    return f"branch-rec-{sha256(key.encode('utf-8')).hexdigest()[:12]}"


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-") or "work"


def _normalize_repo_path(path: str) -> str:
    return path.strip().replace("\\", "/").lstrip("./")


def _branch_exists(root: str, branch: str) -> bool:
    if not root or not branch:
        return False
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0


def _rollback_command(current_branch: str | None, suggested_branch: str) -> str:
    previous = current_branch or "-"
    return f"git switch {previous} && git branch -D {suggested_branch}"
