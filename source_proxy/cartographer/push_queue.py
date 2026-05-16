from __future__ import annotations

import subprocess
from hashlib import sha256
from pathlib import Path

from source_proxy.cartographer.models import CartographerProject, PushQueueItem
from source_proxy.cartographer.project_discovery import discover_projects


GIT_TIMEOUT_SECONDS = 5


def build_push_queue() -> list[PushQueueItem]:
    items: list[PushQueueItem] = []
    for project in discover_projects():
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
    if not upstream:
        return None

    remote, _separator, upstream_branch = upstream.partition("/")
    if not remote or not upstream_branch:
        return None

    ahead_text = _git_stdout(root, "rev-list", "--count", f"{upstream}..HEAD").strip()
    try:
        commits_ahead = int(ahead_text)
    except ValueError:
        commits_ahead = 0
    if commits_ahead <= 0:
        return None

    return PushQueueItem(
        push_id=_push_id(project.project_id, upstream, branch, commits_ahead),
        project_id=project.project_id,
        remote=remote,
        branch=branch,
        upstream=upstream,
        commits_ahead=commits_ahead,
        files=_ahead_files(root, upstream),
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
