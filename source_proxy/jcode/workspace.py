"""Disposable Git worktrees for Gate 2-J.9E deterministic fixtures."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


class OverlayWorkspaceError(ValueError):
    pass


@dataclass(frozen=True)
class DisposableWorktree:
    repository: Path
    base_commit: str
    run_root: Path
    worktree: Path
    initial_status: str
    initial_manifest: dict[str, dict[str, Any]]


def create_disposable_worktree(repository: Path, base_commit: str, run_root: Path) -> DisposableWorktree:
    repo = repository.resolve()
    root = run_root.resolve()
    if not repo.is_dir() or not (repo / ".git").exists() or root.exists():
        raise OverlayWorkspaceError("overlay_worktree_input_invalid")
    worktree = root / "worktree"
    root.mkdir(parents=True)
    created = subprocess.run(
        ["git", "-C", str(repo), "worktree", "add", "--detach", str(worktree), base_commit],
        capture_output=True, text=True, check=False,
    )
    if created.returncode:
        shutil.rmtree(root, ignore_errors=True)
        raise OverlayWorkspaceError("overlay_worktree_create_failed")
    status = _git(worktree, "status", "--porcelain")
    if status:
        cleanup_disposable_worktree(repo, root, worktree)
        raise OverlayWorkspaceError("overlay_worktree_not_clean")
    return DisposableWorktree(repo, base_commit, root, worktree, status, filesystem_manifest(worktree))


def filesystem_manifest(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            continue
        stat = path.lstat()
        if path.is_symlink():
            result[relative] = {"type": "symlink", "mode": oct(stat.st_mode & 0o777), "target": path.readlink().as_posix()}
        elif path.is_file():
            result[relative] = {"type": "file", "mode": oct(stat.st_mode & 0o777), "sha256": _hash_file(path), "size": stat.st_size}
        elif path.is_dir():
            result[relative] = {"type": "directory", "mode": oct(stat.st_mode & 0o777)}
    return result


def validate_overlay_path(path: str, allowed_paths: Sequence[str], protected_paths: Sequence[str]) -> None:
    normalized = path.replace("\\", "/").strip()
    if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
        raise OverlayWorkspaceError("overlay_path_escape")
    if any(normalized == item or normalized.startswith(item.rstrip("/") + "/") for item in protected_paths):
        raise OverlayWorkspaceError("overlay_protected_path")
    if not any(normalized == item or normalized.startswith(item.rstrip("/") + "/") for item in allowed_paths):
        raise OverlayWorkspaceError("overlay_path_not_allowed")


def cleanup_disposable_worktree(repository: Path, run_root: Path, worktree: Path) -> bool:
    subprocess.run(["git", "-C", str(repository), "worktree", "remove", "--force", str(worktree)], capture_output=True, text=True, check=False)
    shutil.rmtree(run_root, ignore_errors=True)
    return not run_root.exists() and not worktree.exists()


def _git(worktree: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise OverlayWorkspaceError("overlay_git_command_failed")
    return result.stdout


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()
