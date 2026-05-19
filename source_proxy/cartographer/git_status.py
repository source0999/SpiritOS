from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from source_proxy.cartographer.models import GitStatus
from source_proxy.cartographer.project_discovery import discover_projects

_GIT_TIMEOUT_SECONDS = 30
_PRIMARY_BRANCHES = {"main", "master"}


def read_git_status() -> GitStatus:
    statuses = read_git_statuses()
    return statuses[0] if statuses else GitStatus()


def read_git_statuses() -> list[GitStatus]:
    return [
        read_git_status_for_project(project_id=project.project_id, root=Path(project.root))
        for project in discover_projects()
    ]


def read_git_status_for_project(project_id: str, root: Path) -> GitStatus:
    generated_at = _generated_at()
    if not (root / ".git").exists():
        return GitStatus(
            project_id=project_id,
            root=str(root),
            available=False,
            generated_at=generated_at,
            error="not_a_git_repository",
        )

    branch_result = _git(root, "branch", "--show-current")
    status_result = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    head_result = _git(root, "rev-parse", "HEAD")
    commit_result = _git(root, "log", "-1", "--format=%H%x00%s")
    upstream_result = _git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")

    errors = [
        result.stderr.strip()
        for result in (branch_result, status_result, head_result, commit_result)
        if result.returncode != 0 and result.stderr.strip()
    ]
    if errors:
        return GitStatus(
            project_id=project_id,
            root=str(root),
            available=False,
            generated_at=generated_at,
            error=errors[0],
        )

    branch = branch_result.stdout.strip() or None
    head_sha = head_result.stdout.strip() or None
    parsed_status = _parse_porcelain_status(status_result.stdout)
    last_commit = _parse_last_commit(commit_result.stdout)
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    no_upstream_reason = None if upstream else _no_upstream_reason(branch, upstream_result)
    ahead, behind = _ahead_behind(root, upstream)
    dirty = bool(parsed_status["changed_files"])
    is_primary_branch = branch in _PRIMARY_BRANCHES
    return GitStatus(
        project_id=project_id,
        root=str(root),
        available=True,
        dirty=dirty,
        branch=branch,
        head_sha=head_sha,
        changed_files=parsed_status["changed_files"],
        staged_files=parsed_status["staged_files"],
        unstaged_files=parsed_status["unstaged_files"],
        untracked_files=parsed_status["untracked_files"],
        ahead=ahead,
        behind=behind,
        upstream=upstream,
        no_upstream_reason=no_upstream_reason,
        generated_at=generated_at,
        is_primary_branch=is_primary_branch,
        needs_branch_recommendation=dirty and is_primary_branch,
        needs_commit=dirty,
        needs_push=ahead > 0,
        merge_ready=not dirty and ahead == 0 and behind == 0 and upstream is not None,
        write_mode="locked",
        last_commit=last_commit,
    )


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    command = ["git", *args]
    try:
        return subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            command,
            returncode=124,
            stdout="",
            stderr="git_command_timeout",
        )


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_porcelain_status(output: str) -> dict[str, list[str]]:
    changed: list[str] = []
    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []
    seen_changed: set[str] = set()
    seen_staged: set[str] = set()
    seen_unstaged: set[str] = set()
    seen_untracked: set[str] = set()
    records = output.split("\x00")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if len(record) < 4:
            continue
        status = record[:2]
        path = record[3:].strip()
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            index += 1
        normalized = path.replace("\\", "/")
        if not normalized:
            continue

        _append_unique(changed, seen_changed, normalized)
        if status == "??":
            _append_unique(untracked, seen_untracked, normalized)
            continue
        if status[0] != " ":
            _append_unique(staged, seen_staged, normalized)
        if status[1] != " ":
            _append_unique(unstaged, seen_unstaged, normalized)

    return {
        "changed_files": changed,
        "staged_files": staged,
        "unstaged_files": unstaged,
        "untracked_files": untracked,
    }


def _append_unique(values: list[str], seen: set[str], value: str) -> None:
    if value not in seen:
        seen.add(value)
        values.append(value)


def _ahead_behind(root: Path, upstream: str | None) -> tuple[int, int]:
    if not upstream:
        return 0, 0
    result = _git(root, "rev-list", "--left-right", "--count", f"{upstream}...HEAD")
    if result.returncode != 0:
        return 0, 0
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        return 0, 0
    try:
        behind = int(parts[0])
        ahead = int(parts[1])
    except ValueError:
        return 0, 0
    return ahead, behind


def _no_upstream_reason(
    branch: str | None,
    upstream_result: subprocess.CompletedProcess[str],
) -> str:
    if not branch:
        return "detached_head_or_no_current_branch"
    stderr = upstream_result.stderr.strip()
    if "no upstream configured" in stderr:
        return "no_upstream_configured"
    if upstream_result.returncode != 0:
        return "upstream_lookup_failed"
    return "no_upstream_configured"


def _parse_last_commit(output: str) -> dict[str, str] | None:
    value = output.strip()
    if not value:
        return None
    sha, _separator, message = value.partition("\x00")
    return {
        "sha": sha[:12],
        "full_sha": sha,
        "message": message,
    }
