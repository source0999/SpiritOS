"""Canonical, portable runtime identity for mutation approval authorities.

The authority is allowed to bind only the real top-level path of a registered Git
worktree.  A caller may select an already-registered root through server
configuration, but cannot substitute a subdirectory, symlink, copied checkout, or
unregistered path.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


class AuthorityRuntimeIdentityError(ValueError):
    """The configured authority root is not a canonical registered worktree."""

    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class AuthorityRuntimeIdentity:
    repository: str
    root: Path
    worktree: str
    branch: str
    source_head: str
    common_git_dir: Path
    state_namespace: str

    def state_directory(self) -> Path:
        configured = os.environ.get("SPIRITOS_APPROVAL_STATE_DIR", "").strip()
        if configured:
            path = Path(configured).expanduser()
            if not path.is_absolute():
                raise AuthorityRuntimeIdentityError("approval_state_directory_not_absolute")
            return Path(os.path.realpath(path))
        return (
            Path.home()
            / ".local"
            / "state"
            / "spiritos"
            / "approval-authority"
            / self.state_namespace
        )


def resolve_authority_runtime_identity(
    configured_root: str | os.PathLike[str] | None = None,
) -> AuthorityRuntimeIdentity:
    raw_root = str(
        configured_root
        or os.environ.get("SPIRITOS_APPROVAL_ROOT", "").strip()
        or Path.cwd()
    )
    requested = Path(raw_root).expanduser()
    if not requested.is_absolute():
        raise AuthorityRuntimeIdentityError("approval_root_not_absolute")
    absolute = Path(os.path.abspath(requested))
    resolved = Path(os.path.realpath(requested))
    if absolute != resolved:
        raise AuthorityRuntimeIdentityError("approval_root_symlink_forbidden")
    if not resolved.is_dir():
        raise AuthorityRuntimeIdentityError("approval_root_unavailable")

    top_level = _git(resolved, "rev-parse", "--show-toplevel")
    canonical_top = Path(os.path.realpath(top_level))
    if canonical_top != resolved:
        raise AuthorityRuntimeIdentityError("approval_root_not_worktree_top_level")

    registered = {
        Path(os.path.realpath(path))
        for path in _registered_worktree_paths(resolved)
    }
    if resolved not in registered:
        raise AuthorityRuntimeIdentityError("approval_root_unregistered")

    source_head = _git(resolved, "rev-parse", "--verify", "HEAD")
    if len(source_head) != 40 or any(character not in "0123456789abcdef" for character in source_head.lower()):
        raise AuthorityRuntimeIdentityError("approval_source_head_invalid")
    branch = _git_optional(resolved, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not branch:
        raise AuthorityRuntimeIdentityError("approval_detached_worktree_forbidden")

    common_raw = Path(_git(resolved, "rev-parse", "--git-common-dir"))
    common_git_dir = Path(
        os.path.realpath(common_raw if common_raw.is_absolute() else resolved / common_raw)
    )
    repository = os.environ.get("SPIRITOS_APPROVAL_REPOSITORY", "").strip()
    if not repository:
        repository = common_git_dir.parent.name
    if not repository:
        raise AuthorityRuntimeIdentityError("approval_repository_identity_missing")
    namespace = hashlib.sha256(
        f"{common_git_dir}\0{resolved}".encode("utf-8")
    ).hexdigest()[:24]
    return AuthorityRuntimeIdentity(
        repository=repository,
        root=resolved,
        worktree=str(resolved),
        branch=branch,
        source_head=source_head,
        common_git_dir=common_git_dir,
        state_namespace=namespace,
    )


def _registered_worktree_paths(root: Path) -> tuple[str, ...]:
    output = _git(root, "worktree", "list", "--porcelain")
    paths = tuple(
        line.removeprefix("worktree ").strip()
        for line in output.splitlines()
        if line.startswith("worktree ") and line.removeprefix("worktree ").strip()
    )
    if not paths:
        raise AuthorityRuntimeIdentityError("approval_worktree_registry_empty")
    return paths


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise AuthorityRuntimeIdentityError("approval_git_identity_unavailable") from error


def _git_optional(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""
