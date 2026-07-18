from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from source_proxy.approval.runtime_identity import (
    AuthorityRuntimeIdentityError,
    resolve_authority_runtime_identity,
)


ROOT = Path(__file__).resolve().parents[2]


def test_current_checkout_resolves_as_registered_worktree(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SPIRITOS_APPROVAL_STATE_DIR", str(tmp_path / "authority-state"))
    identity = resolve_authority_runtime_identity(ROOT)
    assert identity.root == ROOT.resolve()
    assert identity.worktree == str(ROOT.resolve())
    assert identity.source_head == _git(ROOT, "rev-parse", "HEAD")
    assert identity.branch == _git(ROOT, "branch", "--show-current")
    assert len(identity.state_namespace) == 24
    assert identity.state_directory() == (tmp_path / "authority-state").resolve()


def test_registered_linked_worktree_is_accepted(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    linked = tmp_path / "linked"
    repository.mkdir()
    _run(repository, "git", "init", "-q")
    _run(repository, "git", "config", "user.email", "runtime-identity@example.invalid")
    _run(repository, "git", "config", "user.name", "Runtime Identity Test")
    (repository / "tracked.txt").write_text("registered\n", encoding="utf-8")
    _run(repository, "git", "add", "tracked.txt")
    _run(repository, "git", "commit", "-qm", "initial")
    _run(repository, "git", "worktree", "add", "-qb", "linked-test", str(linked), "HEAD")

    identity = resolve_authority_runtime_identity(linked)
    assert identity.root == linked.resolve()
    assert identity.branch == "linked-test"
    assert identity.common_git_dir == (repository / ".git").resolve()


def test_subdirectory_and_unregistered_copy_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(AuthorityRuntimeIdentityError, match="approval_root_not_worktree_top_level"):
        resolve_authority_runtime_identity(ROOT / "source_proxy")

    copied = tmp_path / "copied"
    copied.mkdir()
    (copied / ".git").write_text("gitdir: /does/not/exist\n", encoding="utf-8")
    with pytest.raises(AuthorityRuntimeIdentityError, match="approval_git_identity_unavailable"):
        resolve_authority_runtime_identity(copied)


def test_symlinked_root_is_rejected(tmp_path: Path) -> None:
    link = tmp_path / "linked-root"
    try:
        os.symlink(ROOT, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(AuthorityRuntimeIdentityError, match="approval_root_symlink_forbidden"):
        resolve_authority_runtime_identity(link)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _run(root: Path, *args: str) -> None:
    subprocess.run(list(args), cwd=root, check=True, capture_output=True, text=True)
