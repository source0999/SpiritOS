from __future__ import annotations

import subprocess
import json
import os
from hashlib import sha256
from pathlib import Path

from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.models import CartographerProject, PushQueueItem
from source_proxy.cartographer.project_discovery import discover_projects


GIT_TIMEOUT_SECONDS = 5


def build_push_queue() -> list[PushQueueItem]:
    items: list[PushQueueItem] = []
    projects = discover_projects()
    if not projects:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            projects = [
                CartographerProject(
                    project_id=cwd.name.lower(),
                    name=cwd.name,
                    root=str(cwd),
                    markers=[".git"],
                )
            ]
    for project in projects:
        item = _push_item_for_project(project)
        if item:
            items.append(item)
    return items


def _push_item_for_project(project: CartographerProject) -> PushQueueItem | None:
    root = Path(project.root)
    if not (root / ".git").exists():
        return None

    branch = _git_stdout(root, "branch", "--show-current").strip()
    if not branch:
        return None

    upstream = _git_stdout(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").strip()
    base_ref: str | None = upstream or _branch_creation_base(project, branch)

    remote = _push_remote(root, upstream)
    if not remote:
        return None

    if not base_ref:
        return None

    commits_ahead, commits_behind = _ahead_behind(root, upstream, base_ref)
    if commits_ahead <= 0:
        return None

    commits_to_push = _commits_to_push(root, base_ref)
    approval_records = _read_git_approval_records_for_project_and_cwd(project)
    commit_audit_status = _commit_audit_status(
        records=approval_records,
        project_id=project.project_id,
        branch=branch,
        commits_to_push=commits_to_push,
    )
    test_status = _test_status(
        records=approval_records,
        project_id=project.project_id,
        branch=branch,
        head_sha=commits_to_push[0] if commits_to_push else None,
    )
    dirty = _dirty(root)
    drift_status = _drift_status(project.project_id)
    return PushQueueItem(
        push_id=_push_id(project.project_id, upstream, branch, commits_ahead),
        project_id=project.project_id,
        remote=remote,
        branch=branch,
        upstream=upstream or None,
        ahead=commits_ahead,
        behind=commits_behind,
        commits_ahead=commits_ahead,
        commits_to_push=commits_to_push,
        files=_ahead_files(root, base_ref),
        audit_status=_push_audit_status(project.project_id, branch),
        commit_audit_status=commit_audit_status,
        test_status=test_status,
        dirty=dirty,
        drift_status=drift_status,
        push_command_preview=_push_command_preview(remote, branch, upstream or None),
        rollback_guidance=_rollback_guidance(remote, branch),
        approval_status="approval_required",
        reason_codes=_reason_codes(
            upstream=upstream or None,
            behind=commits_behind,
            commit_audit_status=commit_audit_status,
        ),
        push_blockers=_push_blockers(
            dirty=dirty,
            drift_status=drift_status,
            test_status=test_status,
            commit_audit_status=commit_audit_status,
            behind=commits_behind,
        ),
        branch_protection_warnings=_branch_protection_warnings(
            branch=branch,
            upstream=upstream or None,
        ),
        remote_status={
            "remote": remote,
            "branch": branch,
            "upstream": upstream or None,
            "ahead": commits_ahead,
            "behind": commits_behind,
        },
        status="push_pending",
        requires_approval=True,
        push_enabled=False,
        action_taken=False,
    )


def _ahead_files(root: Path, upstream: str) -> list[str]:
    output = _git_stdout(root, "diff", "--name-only", f"{upstream}..HEAD")
    files: list[str] = []
    seen: set[str] = set()
    for line in output.splitlines():
        normalized = line.strip().replace("\\", "/")
        if normalized and normalized not in seen:
            seen.add(normalized)
            files.append(normalized)
    return files[:50]


def _commits_to_push(root: Path, base_ref: str) -> list[str]:
    output = _git_stdout(root, "log", "--format=%H", f"{base_ref}..HEAD")
    return [line.strip() for line in output.splitlines() if line.strip()]


def _ahead_behind(root: Path, upstream: str, base_ref: str) -> tuple[int, int]:
    if upstream:
        output = _git_stdout(root, "rev-list", "--left-right", "--count", f"{upstream}...HEAD").strip()
        parts = output.split()
        if len(parts) == 2:
            try:
                return int(parts[1]), int(parts[0])
            except ValueError:
                pass
    ahead_text = _git_stdout(root, "rev-list", "--count", f"{base_ref}..HEAD").strip()
    try:
        return int(ahead_text), 0
    except ValueError:
        return 0, 0


def _push_audit_status(project_id: str, branch: str) -> str:
    for record in reversed(_read_git_approval_records_for_discovered_projects()):
        if (
            record.get("project_id") == project_id
            and record.get("event") == "push_approved"
            and record.get("branch") == branch
            and record.get("result") == "pushed"
        ):
            return "recorded"
    return "missing"


def _commit_audit_status(
    *,
    records: list[dict[str, object]],
    project_id: str,
    branch: str,
    commits_to_push: list[str],
) -> str:
    if not commits_to_push:
        return "not_needed"
    audited = {
        str(record.get("commit_sha"))
        for record in records
        if record.get("project_id") == project_id
        and record.get("event") == "commit_created"
        and record.get("branch") == branch
        and record.get("commit_sha")
    }
    if all(commit in audited for commit in commits_to_push):
        return "recorded"
    return "missing"


def _test_status(
    *,
    records: list[dict[str, object]],
    project_id: str,
    branch: str,
    head_sha: str | None,
) -> str:
    if not head_sha:
        return "not_required"
    for record in reversed(records):
        if (
            record.get("project_id") == project_id
            and record.get("event") == "commit_created"
            and record.get("branch") == branch
            and record.get("commit_sha") == head_sha
        ):
            checks = record.get("checks")
            if not isinstance(checks, list) or not checks:
                return "missing"
            if all(isinstance(check, dict) and check.get("status") == "passed" for check in checks):
                return "passed"
            return "failed"
    return "missing"


def _dirty(root: Path) -> bool:
    return bool(_git_stdout(root, "status", "--porcelain=v1", "--untracked-files=all").strip())


def _drift_status(project_id: str) -> str:
    return "open" if any(finding.project_id == project_id for finding in detect_blueprint_drift()) else "clear"


def _push_command_preview(remote: str, branch: str, upstream: str | None) -> str:
    if upstream:
        return f"git push {remote} {branch}"
    return f"git push -u {remote} {branch}"


def _rollback_guidance(remote: str, branch: str) -> str:
    return (
        f"If this push is wrong, do not force-push automatically; review and revert locally, "
        f"or delete remote branch with approval: git push {remote} --delete {branch}."
    )


def _reason_codes(*, upstream: str | None, behind: int, commit_audit_status: str) -> list[str]:
    codes = ["push_requires_separate_approval", "push_disabled_until_approved"]
    if commit_audit_status == "missing":
        codes.append("commit_audit_missing")
    if not upstream:
        codes.append("no_upstream_push_would_set_upstream")
    if behind > 0:
        codes.append("branch_behind_upstream")
    return codes


def _push_blockers(
    *,
    dirty: bool,
    drift_status: str,
    test_status: str,
    commit_audit_status: str,
    behind: int,
) -> list[str]:
    blockers = ["push_requires_separate_approval"]
    if commit_audit_status == "missing":
        blockers.append("commit_audit_missing")
    if test_status != "passed":
        blockers.append("required_checks_not_passed")
    if dirty:
        blockers.append("working_tree_dirty")
    if drift_status == "open":
        blockers.append("blueprint_drift_open")
    if behind > 0:
        blockers.append("branch_behind_upstream")
    return blockers


def _branch_protection_warnings(*, branch: str, upstream: str | None) -> list[str]:
    warnings = ["review_remote_branch_protection_before_push"]
    if branch in {"main", "master", "trunk"}:
        warnings.append("base_branch_push_requires_extra_review")
    if not upstream:
        warnings.append("new_remote_branch_may_not_have_protection_rules")
    return warnings


def _branch_creation_base(project: CartographerProject, branch: str) -> str | None:
    for record in reversed(_read_git_approval_records(Path(project.root))):
        if (
            record.get("event") == "branch_created"
            and record.get("project_id") == project.project_id
            and record.get("branch") == branch
            and record.get("previous_branch")
        ):
            return str(record["previous_branch"])
    return None


def _read_git_approval_records_for_discovered_projects() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for project in discover_projects():
        records.extend(_read_git_approval_records(Path(project.root)))
    cwd = Path.cwd()
    if (cwd / ".git").exists():
        records.extend(_read_git_approval_records(cwd))
    return records


def _read_git_approval_records_for_project_and_cwd(project: CartographerProject) -> list[dict[str, object]]:
    records = _read_git_approval_records(Path(project.root))
    cwd = Path.cwd()
    if cwd != Path(project.root) and (cwd / ".git").exists():
        records.extend(_read_git_approval_records(cwd))
    return records


def _push_remote(root: Path, upstream: str) -> str | None:
    remote, _separator, upstream_branch = upstream.partition("/")
    if remote and upstream_branch:
        return remote
    remotes = _git_stdout(root, "remote").splitlines()
    return remotes[0].strip() if remotes else None


def _read_git_approval_records(project_root: Path) -> list[dict[str, object]]:
    path = _approval_record_path(project_root)
    if not path.exists() or not path.is_file():
        return []
    records: list[dict[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-100:]
    except OSError:
        return []
    for line in lines:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _approval_record_path(project_root: Path) -> Path:
    configured = os.getenv("SOURCE_PROXY_CARTOGRAPHER_GIT_APPROVAL_LOG")
    if configured:
        return Path(configured)
    return project_root / "data" / "cartographer_git_approvals.audit.jsonl"


def _git_stdout(root: Path, *args: str) -> str:
    result = _git(root, *args)
    if result.returncode != 0:
        return ""
    return result.stdout


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    command = ["git", *args]
    try:
        return subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            command,
            returncode=124,
            stdout="",
            stderr="git_command_timeout",
        )


def _push_id(project_id: str, upstream: str, branch: str, commits_ahead: int) -> str:
    key = "|".join([project_id, upstream, branch, str(commits_ahead)])
    return f"push-{sha256(key.encode('utf-8')).hexdigest()[:12]}"
