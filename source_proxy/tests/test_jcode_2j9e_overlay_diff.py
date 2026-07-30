"""Gate 2-J.9E deterministic disposable-worktree and diff proofs."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from source_proxy.jcode.diff_collector import collect_independent_diff
from source_proxy.jcode.workspace import (
    OverlayWorkspaceError,
    cleanup_disposable_worktree,
    create_disposable_worktree,
    validate_overlay_path,
)


def _git(path: Path, *args: str) -> None:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def _repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "fixture")
    (repo / "allowed").mkdir()
    (repo / "allowed" / "text.txt").write_text("before\n")
    (repo / "allowed" / "binary.bin").write_bytes(b"\x00\x01")
    (repo / "allowed" / "rename.txt").write_text("rename\n")
    (repo / "protected.txt").write_text("protected\n")
    (repo / ".gitignore").write_text("ignored.tmp\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "fixture")
    return repo, subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def test_mutations_are_accounted_and_git_ledger_reconcile(tmp_path: Path) -> None:
    repo, commit = _repo(tmp_path)
    workspace = create_disposable_worktree(repo, commit, tmp_path / "run")
    root = workspace.worktree
    (root / "allowed" / "text.txt").write_text("after\n")
    (root / "allowed" / "created.txt").write_text("created\n")
    (root / "allowed" / "binary.bin").unlink()
    (root / "allowed" / "rename.txt").rename(root / "allowed" / "renamed.txt")
    (root / "allowed" / "text.txt").chmod(0o755)
    (root / "ignored.tmp").write_text("ignored\n")
    receipt = collect_independent_diff(root, workspace.initial_manifest, ["allowed"], ["protected.txt", ".git"])
    assert receipt["reconciled"] is True
    assert {item["path"] for item in receipt["changes"]} >= {"allowed/text.txt", "allowed/created.txt", "allowed/binary.bin", "allowed/renamed.txt"}
    assert any(item["kind"] == "renamed" and item["from_path"] == "allowed/rename.txt" for item in receipt["changes"])
    assert receipt["executor_claim_is_terminal_truth"] is False
    assert receipt["ignored_paths"] == ["ignored.tmp"]
    assert subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True) == ""
    assert cleanup_disposable_worktree(repo, workspace.run_root, root) is True


@pytest.mark.parametrize("path, reason", [("../escape", "escape"), ("/absolute", "escape"), ("protected.txt", "protected"), ("other.txt", "not_allowed")])
def test_path_policy_rejects_traversal_protected_and_aliases(path: str, reason: str) -> None:
    with pytest.raises(OverlayWorkspaceError, match=reason):
        validate_overlay_path(path, ["allowed"], ["protected.txt", ".git"])


def test_protected_symlink_and_restoration_fail_or_reconcile(tmp_path: Path) -> None:
    repo, commit = _repo(tmp_path)
    workspace = create_disposable_worktree(repo, commit, tmp_path / "run")
    root = workspace.worktree
    (root / "protected.txt").write_text("changed\n")
    with pytest.raises(OverlayWorkspaceError, match="protected"):
        collect_independent_diff(root, workspace.initial_manifest, ["allowed"], ["protected.txt", ".git"])
    (root / "protected.txt").write_text("protected\n")
    (root / "allowed" / "link").symlink_to("/etc/passwd")
    with pytest.raises(OverlayWorkspaceError, match="symlink"):
        collect_independent_diff(root, workspace.initial_manifest, ["allowed"], ["protected.txt", ".git"])
    (root / "allowed" / "link").unlink()
    (root / "allowed" / "text.txt").write_text("temporary\n")
    (root / "allowed" / "text.txt").write_text("before\n")
    receipt = collect_independent_diff(root, workspace.initial_manifest, ["allowed"], ["protected.txt", ".git"])
    assert receipt["changes"] == []
    assert cleanup_disposable_worktree(repo, workspace.run_root, root) is True
