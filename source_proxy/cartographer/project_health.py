from __future__ import annotations

from collections import Counter
from pathlib import Path
import subprocess

from source_proxy.cartographer.blueprint_registry import list_blueprints
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.git_approvals import read_git_approval_records
from source_proxy.cartographer.git_status import read_git_status_for_project, read_git_statuses
from source_proxy.cartographer.models import CartographerProject, GitStatus, ProjectHealth
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
    git_statuses = read_git_statuses()
    projects = discover_projects()
    if not projects:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            project_id = cwd.name.lower()
            projects = [
                CartographerProject(
                    project_id=project_id,
                    name=cwd.name,
                    root=str(cwd),
                    markers=[".git"],
                )
            ]
            git_statuses = [read_git_status_for_project(project_id=project_id, root=cwd)]
            blueprints_by_project[project_id] = _fallback_blueprint_count(cwd)

    git_by_project = {
        status.project_id: status
        for status in git_statuses
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
                workspace_classification="candidate_read_only_project",
                authority_blockers=[
                    "starter_blueprint_approval_required",
                    "writes_require_explicit_approval_boundary",
                    "worktree_creation_proposal_only",
                ],
                filters=["candidate", "needs_approval"],
                action_taken=False,
            )
        )

    for project in projects:
        if project.root in candidate_roots:
            continue
        git_status = git_by_project.get(project.project_id)
        blueprint_count = blueprints_by_project[project.project_id]
        pending_drift = drift_by_project[project.project_id]
        pending_proposals = proposals_by_project[project.project_id]
        dirty_summary = _dirty_summary(git_status)
        authority = _workspace_authority(git_status)
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
                changed_files=list(git_status.changed_files) if git_status else [],
                staged_files=list(git_status.staged_files) if git_status else [],
                unstaged_files=list(git_status.unstaged_files) if git_status else [],
                untracked_files=list(git_status.untracked_files) if git_status else [],
                dirty_file_count=len(git_status.changed_files) if git_status else 0,
                expected_evidence_files=dirty_summary["expected_evidence_files"],
                unsafe_dirty_files=dirty_summary["unsafe_dirty_files"],
                dirty_summary=str(dirty_summary["dirty_summary"]),
                ahead=git_status.ahead if git_status else 0,
                behind=git_status.behind if git_status else 0,
                upstream=git_status.upstream if git_status else None,
                no_upstream_reason=git_status.no_upstream_reason if git_status else None,
                merge_ready=readiness["merge_ready"],
                merge_blockers=readiness["merge_blockers"],
                recommended_next_step=readiness["recommended_next_step"],
                merge_target=readiness["merge_target"],
                pushed=readiness["pushed"],
                head_sha=readiness["head_sha"],
                commit_audit_status=str(readiness["commit_audit_status"]),
                unaudited_head_change=bool(readiness["unaudited_head_change"]),
                push_audit_status=str(readiness["push_audit_status"]),
                push_audit_explanation=str(readiness["push_audit_explanation"]),
                push_warning_policy=str(readiness["push_warning_policy"]),
                bootstrap_push_warning=bool(readiness["bootstrap_push_warning"]),
                push_approval_status=str(readiness["push_approval_status"]),
                push_enabled=bool(readiness["push_enabled"]),
                push_reason_codes=list(readiness["push_reason_codes"]),
                commits_to_push=list(readiness["commits_to_push"]),
                checks_passed=readiness["checks_passed"],
                read_only=True,
                write_policy="read_only_observation",
                write_actions_enabled=False,
                workspace_classification=str(authority["workspace_classification"]),
                authority_blockers=list(authority["authority_blockers"]),
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


def _fallback_blueprint_count(root: Path) -> int:
    blueprint_dir = root / "_blueprints"
    if not blueprint_dir.exists() or not blueprint_dir.is_dir():
        return 0
    try:
        return sum(
            1
            for path in blueprint_dir.rglob("*.md")
            if path.is_file() and path.name != "INDEX.md"
        )
    except OSError:
        return 0


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
    commit_audit_status = _commit_audit_status(
        project_id=project_id,
        branch=git_status.branch,
        head_sha=git_status.head_sha,
        ahead=git_status.ahead,
    )
    unaudited_head_change = commit_audit_status == "missing"
    push_audit_status = _push_audit_status(
        branch=git_status.branch,
        pushed=pushed,
        ahead=git_status.ahead,
        upstream=git_status.upstream,
    )
    bootstrap_push_warning = push_audit_status == "bootstrap_manual_push_no_local_commits"
    push_warning_policy = _push_warning_policy(push_audit_status=push_audit_status)
    push_audit_explanation = _push_audit_explanation(
        push_audit_status=push_audit_status,
        ahead=git_status.ahead,
    )
    push_reason_codes = _push_reason_codes(
        git_status=git_status,
        pushed=pushed,
        push_audit_status=push_audit_status,
    )
    commits_to_push = _commits_to_push(git_status)

    if git_status.dirty:
        blockers.append("working tree has uncommitted changes")
    if git_status.ahead > 0:
        blockers.append("branch has unpushed commits")
    if unaudited_head_change:
        blockers.append("unaudited_head_change")
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
    if push_audit_status not in {"not_needed", "bootstrap_manual_push_no_local_commits"} and not pushed:
        blockers.append("push audit missing")
    if _checks_required(git_status) and not checks_passed:
        blockers.append("required checks not recorded as passed")

    return _readiness_payload(
        blockers,
        pushed=pushed,
        head_sha=git_status.head_sha,
        commit_audit_status=commit_audit_status,
        unaudited_head_change=unaudited_head_change,
        checks_passed=checks_passed,
        merge_target=merge_target,
        push_audit_status=push_audit_status,
        push_audit_explanation=push_audit_explanation,
        push_warning_policy=push_warning_policy,
        bootstrap_push_warning=bootstrap_push_warning,
        push_approval_status="not_required" if git_status.ahead <= 0 else "approval_required",
        push_enabled=False,
        push_reason_codes=push_reason_codes,
        commits_to_push=commits_to_push,
    )


def _readiness_payload(
    blockers: list[str],
    *,
    pushed: bool,
    head_sha: str | None = None,
    commit_audit_status: str = "not_needed",
    unaudited_head_change: bool = False,
    checks_passed: bool,
    merge_target: str | None,
    push_audit_status: str = "missing",
    push_audit_explanation: str = "",
    push_warning_policy: str = "none",
    bootstrap_push_warning: bool = False,
    push_approval_status: str = "not_required",
    push_enabled: bool = False,
    push_reason_codes: list[str] | None = None,
    commits_to_push: list[str] | None = None,
) -> dict[str, object]:
    return {
        "merge_ready": not blockers,
        "merge_blockers": blockers,
        "recommended_next_step": _recommended_next_step(blockers),
        "merge_target": merge_target,
        "pushed": pushed,
        "head_sha": head_sha,
        "commit_audit_status": commit_audit_status,
        "unaudited_head_change": unaudited_head_change,
        "push_audit_status": push_audit_status,
        "push_audit_explanation": push_audit_explanation,
        "push_warning_policy": push_warning_policy,
        "bootstrap_push_warning": bootstrap_push_warning,
        "push_approval_status": push_approval_status,
        "push_enabled": push_enabled,
        "push_reason_codes": push_reason_codes or [],
        "commits_to_push": commits_to_push or [],
        "checks_passed": checks_passed,
    }


def _push_audit_status(*, branch: str | None, pushed: bool, ahead: int, upstream: str | None) -> str:
    if pushed:
        return "recorded"
    if branch in {None, "main", "master", "trunk"} and ahead == 0:
        return "not_needed"
    if ahead == 0 and upstream:
        return "bootstrap_manual_push_no_local_commits"
    return "missing"


def _push_audit_explanation(*, push_audit_status: str, ahead: int) -> str:
    if push_audit_status == "recorded":
        return "A Cartographer push approval record exists for this branch."
    if push_audit_status == "bootstrap_manual_push_no_local_commits":
        return (
            "Branch has an upstream and no local commits to push; treating earlier manual upstream setup "
            "as a non-blocking bootstrap warning."
        )
    if push_audit_status == "not_needed":
        return "No push audit is needed because there are no local commits to push."
    if ahead > 0:
        return "Local commits are ahead of upstream and require Cartographer push approval."
    return "Push audit is missing."


def _push_warning_policy(*, push_audit_status: str) -> str:
    if push_audit_status == "bootstrap_manual_push_no_local_commits":
        return "bootstrap_manual_upstream_non_blocking"
    if push_audit_status == "missing":
        return "current_ahead_commits_require_push_approval"
    return "none"


def _push_reason_codes(
    *,
    git_status: GitStatus,
    pushed: bool,
    push_audit_status: str,
) -> list[str]:
    if git_status.ahead <= 0:
        if pushed:
            return ["push_already_recorded"]
        if push_audit_status == "bootstrap_manual_push_no_local_commits":
            return ["bootstrap_manual_upstream_no_local_commits", "no_commits_to_push"]
        return ["no_commits_to_push"]
    codes = ["unpushed_commits", "push_requires_separate_approval", "push_disabled_until_approved"]
    if not git_status.upstream:
        codes.append("merge_target_unknown")
    if git_status.behind > 0:
        codes.append("branch_behind_upstream")
    if push_audit_status == "missing":
        codes.append("push_audit_missing")
    return codes


def _checks_required(git_status: GitStatus) -> bool:
    if git_status.dirty:
        return False
    if git_status.branch in {None, "main", "master", "trunk"}:
        return False
    return bool(git_status.upstream)


def _dirty_summary(git_status: GitStatus | None) -> dict[str, object]:
    if git_status is None or not git_status.changed_files:
        return {
            "expected_evidence_files": [],
            "unsafe_dirty_files": [],
            "dirty_summary": "clean",
        }

    expected = [
        path
        for path in git_status.changed_files
        if _is_expected_evidence_file(path)
    ]
    expected_set = set(expected)
    unsafe = [path for path in git_status.changed_files if path not in expected_set]
    if expected and not unsafe:
        summary = "expected evidence files changed"
    elif expected:
        summary = "code/config changes plus expected evidence files changed"
    else:
        summary = "code/config changes changed outside expected evidence paths"
    return {
        "expected_evidence_files": expected,
        "unsafe_dirty_files": unsafe,
        "dirty_summary": summary,
    }


def _workspace_authority(git_status: GitStatus | None) -> dict[str, object]:
    blockers = [
        "writes_require_explicit_approval_boundary",
        "worktree_creation_proposal_only",
    ]
    if git_status is None or not git_status.available:
        blockers.insert(0, "git_status_unavailable")
        return {
            "workspace_classification": "read_only_project_status_unknown",
            "authority_blockers": blockers,
        }
    if git_status.dirty:
        blockers.insert(0, "dirty_worktree_requires_scope_review")
        return {
            "workspace_classification": "dirty_worktree",
            "authority_blockers": blockers,
        }
    return {
        "workspace_classification": "clean_read_only_project",
        "authority_blockers": blockers,
    }


def _is_expected_evidence_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith("scout/soak-logs/")
        or normalized.startswith("source_proxy/cartographer/soak-logs/")
    ) and normalized.endswith(".json")


def _commits_to_push(git_status: GitStatus) -> list[str]:
    if git_status.ahead <= 0 or not git_status.root or not git_status.upstream:
        return []
    result = subprocess.run(
        ["git", "log", "--format=%H", f"{git_status.upstream}..HEAD"],
        cwd=git_status.root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _recommended_next_step(blockers: list[str]) -> str:
    if not blockers:
        return "open merge review"
    if "working tree has uncommitted changes" in blockers:
        return "commit or discard remaining local changes"
    if "unaudited_head_change" in blockers:
        return "review HEAD change and record or resolve commit audit before push"
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


def _commit_audit_status(
    *,
    project_id: str,
    branch: str | None,
    head_sha: str | None,
    ahead: int,
) -> str:
    if ahead <= 0:
        return "not_needed"
    if not branch or not head_sha:
        return "missing"
    for record in reversed(read_git_approval_records()):
        if (
            record.get("project_id") == project_id
            and record.get("event") == "commit_created"
            and record.get("branch") == branch
            and record.get("commit_sha") == head_sha
        ):
            return "recorded"
    return "missing"


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
