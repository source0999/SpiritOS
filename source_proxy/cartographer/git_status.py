from __future__ import annotations

import subprocess
from pathlib import Path

from source_proxy.cartographer.models import GitStatus
from source_proxy.cartographer.project_discovery import discover_projects

_GIT_TIMEOUT_SECONDS = 5


def read_git_status() -> GitStatus:
    statuses = read_git_statuses()
    return statuses[0] if statuses else GitStatus()


def read_git_statuses() -> list[GitStatus]:
    return [
        read_git_status_for_project(project_id=project.project_id, root=Path(project.root))
        for project in discover_projects()
    ]


def read_git_status_for_project(project_id: str, root: Path) -> GitStatus:
    if not (root / ".git").exists():
        return GitStatus(
            project_id=project_id,
            root=str(root),
            available=False,
            error="not_a_git_repository",
        )

    branch_result = _git(root, "branch", "--show-current")
    status_result = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    commit_result = _git(root, "log", "-1", "--format=%H%x00%s")

    errors = [
        result.stderr.strip()
        for result in (branch_result, status_result, commit_result)
        if result.returncode != 0 and result.stderr.strip()
    ]
    if errors:
        return GitStatus(
            project_id=project_id,
            root=str(root),
            available=False,
            error=errors[0],
        )

    branch = branch_result.stdout.strip() or None
    changed_files = _parse_changed_files(status_result.stdout)
    last_commit = _parse_last_commit(commit_result.stdout)
    return GitStatus(
        project_id=project_id,
        root=str(root),
        available=True,
        dirty=bool(changed_files),
        branch=branch,
        changed_files=changed_files,
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


def _parse_changed_files(output: str) -> list[str]:
    changed: list[str] = []
    seen: set[str] = set()
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
        if normalized and normalized not in seen:
            seen.add(normalized)
            changed.append(normalized)
    return changed


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
