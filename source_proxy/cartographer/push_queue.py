from __future__ import annotations

import subprocess
import json
import os
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
    base_ref: str | None = upstream or _branch_creation_base(project, branch)

    remote = _push_remote(root, upstream)
    if not remote:
        return None

    if not base_ref:
        return None

    ahead_text = _git_stdout(root, "rev-list", "--count", f"{base_ref}..HEAD").strip()
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
        upstream=upstream or None,
        commits_ahead=commits_ahead,
        files=_ahead_files(root, base_ref),
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
