"""Independent mutation ledger and Git reconciliation for Gate 2-J.9E."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Sequence

from source_proxy.jcode.workspace import OverlayWorkspaceError, filesystem_manifest, validate_overlay_path


def collect_independent_diff(
    worktree: Path,
    initial: dict[str, dict[str, Any]],
    allowed_paths: Sequence[str],
    protected_paths: Sequence[str],
) -> dict[str, Any]:
    final = filesystem_manifest(worktree)
    changes: list[dict[str, Any]] = []
    ignored_paths: list[str] = []
    for path in sorted(set(initial) | set(final)):
        before, after = initial.get(path), final.get(path)
        if before == after:
            continue
        if _is_ignored(worktree, path) and not any(path == item or path.startswith(item.rstrip("/") + "/") for item in allowed_paths):
            ignored_paths.append(path)
            continue
        validate_overlay_path(path, allowed_paths, protected_paths)
        if after and after.get("type") == "symlink":
            raise OverlayWorkspaceError("overlay_symlink_denied")
        kind = "created" if before is None else "deleted" if after is None else "modified"
        changes.append({"path": path, "kind": kind, "before": before, "after": after})
    deleted_by_hash = {
        item["before"].get("sha256"): item
        for item in changes
        if item["kind"] == "deleted" and item["before"].get("type") == "file"
    }
    renamed_deletions: set[str] = set()
    for item in changes:
        after = item.get("after") or {}
        if item["kind"] == "created" and after.get("type") == "file":
            deleted = deleted_by_hash.get(after.get("sha256"))
            if deleted is not None:
                item["kind"] = "renamed"
                item["from_path"] = deleted["path"]
                renamed_deletions.add(deleted["path"])
    changes = [item for item in changes if item["path"] not in renamed_deletions]
    status = _git(worktree, "status", "--porcelain=v1", "--ignored")
    diff = _git_bytes(worktree, "diff", "--binary", "--no-ext-diff")
    git_paths = _status_paths(status)
    ledger_paths = {item["path"] for item in changes if item["kind"] != "directory"}
    ledger_paths.update(str(item["from_path"]) for item in changes if "from_path" in item)
    unexplained = sorted(git_paths.difference(ledger_paths))
    if unexplained:
        raise OverlayWorkspaceError("overlay_git_ledger_mismatch")
    return {
        "initial_manifest": initial,
        "final_manifest": final,
        "changes": changes,
        "ignored_paths": ignored_paths,
        "git_status": status,
        "git_diff_sha256": hashlib.sha256(diff).hexdigest(),
        "filesystem_ledger_sha256": hashlib.sha256(repr(changes).encode()).hexdigest(),
        "reconciled": True,
        "executor_claim_is_terminal_truth": False,
    }


def _git(worktree: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise OverlayWorkspaceError("overlay_git_command_failed")
    return result.stdout


def _git_bytes(worktree: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, check=False)
    if result.returncode:
        raise OverlayWorkspaceError("overlay_git_command_failed")
    return result.stdout


def _status_paths(status: str) -> set[str]:
    paths: set[str] = set()
    for line in status.splitlines():
        if len(line) >= 4 and line[:2] != "!!":
            paths.add(line[3:].split(" -> ")[-1])
    return paths


def _is_ignored(worktree: Path, path: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(worktree), "check-ignore", "-q", "--", path],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0
