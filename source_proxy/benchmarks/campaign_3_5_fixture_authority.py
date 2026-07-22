"""Server-owned registration for a disposable Campaign 3.5 fixture workspace.

The production request never supplies a filesystem path or path scope.  The
benchmark harness provisions a private, mode-0600 manifest *outside* the
fixture and starts Source Proxy with its absolute path.  This module validates
that configuration before an adapter can see the fixture; it deliberately
contains no task IDs, prompts, seeds, oracle data, or expected outcomes.

Schema v2 binds the real Git commit and tree object IDs and distinguishes
readable context from writable scope.  The original v1 schema remains accepted
for existing Campaign 3.5 runs.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Sequence


MANIFEST_SCHEMA = "campaign-3.5-fixture-authority/v1"
MANIFEST_SCHEMA_V2 = "campaign-3.5-fixture-authority/v2"
ENV_MANIFEST = "SPIRITOS_CAMPAIGN_3_5_FIXTURE_MANIFEST"

_V1_KEYS = {
    "schema_version",
    "fixture_id",
    "workspace_root",
    "baseline_tree_sha256",
    "allowed_paths",
    "execution_profile",
}
_V2_KEYS = {
    "schema_version",
    "fixture_id",
    "workspace_root",
    "baseline_commit",
    "baseline_tree",
    "readable_paths",
    "writable_paths",
    "execution_profile",
}


class Campaign35FixtureAuthorityError(ValueError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class Campaign35FixtureAuthority:
    fixture_id: str
    workspace_root: Path
    baseline_tree_sha256: str
    allowed_paths: tuple[str, ...]
    execution_profile: str
    manifest_sha256: str
    schema_version: str = MANIFEST_SCHEMA
    baseline_commit: str | None = None
    baseline_tree: str | None = None
    readable_paths: tuple[str, ...] = ()
    writable_paths: tuple[str, ...] = ()
    current_state_sha256: str = ""
    current_state_paths: tuple[str, ...] = ()

    def adapter_scope(self) -> dict[str, Any]:
        """Return the legacy adapter keys plus the richer v2 evidence.

        ``allowed_paths`` remains the write scope so existing adapters cannot
        accidentally gain write authority from the broader readable scope.
        """
        readable = self.readable_paths or self.allowed_paths
        writable = self.writable_paths or self.allowed_paths
        scope: dict[str, Any] = {
            "fixture_id": self.fixture_id,
            "fixture_root": ".",
            "allowed_paths": list(writable),
            "readable_paths": list(readable),
            "writable_paths": list(writable),
            "workspace_root": str(self.workspace_root),
            "baseline_tree_sha256": self.baseline_tree_sha256,
            "execution_profile": self.execution_profile,
            "manifest_sha256": self.manifest_sha256,
            "authority_schema_version": self.schema_version,
            "current_state_sha256": self.current_state_sha256,
            "current_state_paths": list(self.current_state_paths),
        }
        if self.baseline_commit is not None:
            scope["baseline_commit"] = self.baseline_commit
        if self.baseline_tree is not None:
            scope["baseline_tree"] = self.baseline_tree
        return scope


def load_campaign_3_5_fixture_authority() -> Campaign35FixtureAuthority:
    raw = os.environ.get(ENV_MANIFEST, "").strip()
    if not raw:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_missing")
    supplied_manifest_path = Path(raw).expanduser()
    if not supplied_manifest_path.is_absolute():
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_not_absolute")
    # A manifest symlink can be retargeted after validation.  Require the
    # operator-provided spelling to already name the canonical file.
    if supplied_manifest_path != Path(os.path.realpath(supplied_manifest_path)):
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_unsafe")
    manifest_path = Path(os.path.realpath(supplied_manifest_path))
    try:
        metadata = manifest_path.stat()
        if not manifest_path.is_file() or stat.S_IMODE(metadata.st_mode) != 0o600:
            raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_unsafe")
        raw_manifest = manifest_path.read_bytes()
        payload = json.loads(raw_manifest)
    except Campaign35FixtureAuthorityError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_unreadable") from error
    if not isinstance(payload, dict):
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_schema_invalid")
    schema = str(payload.get("schema_version") or "")
    if schema == MANIFEST_SCHEMA:
        if set(payload) != _V1_KEYS:
            raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_schema_invalid")
        return _load_v1(payload, raw_manifest)
    if schema == MANIFEST_SCHEMA_V2:
        if set(payload) != _V2_KEYS:
            raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_schema_invalid")
        return _load_v2(payload, raw_manifest, manifest_path)
    raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_schema_invalid")


def _load_v1(payload: dict[str, object], raw_manifest: bytes) -> Campaign35FixtureAuthority:
    fixture_id = _identifier(payload.get("fixture_id"), "campaign_3_5_fixture_id_invalid")
    workspace_root = _workspace(payload.get("workspace_root"))
    baseline = _sha(payload.get("baseline_tree_sha256"), "campaign_3_5_fixture_baseline_invalid")
    allowed = _paths(payload.get("allowed_paths"), reason="campaign_3_5_fixture_allowed_paths_invalid")
    profile = _identifier(payload.get("execution_profile"), "campaign_3_5_fixture_profile_invalid")
    if _git_tree_hash(workspace_root) != baseline:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_baseline_mismatch")
    current_state_sha256, current_state_paths = campaign_3_5_workspace_state_commitment(
        workspace_root,
        writable_paths=allowed,
    )
    return Campaign35FixtureAuthority(
        fixture_id=fixture_id,
        workspace_root=workspace_root,
        baseline_tree_sha256=baseline,
        allowed_paths=allowed,
        execution_profile=profile,
        manifest_sha256=hashlib.sha256(raw_manifest).hexdigest(),
        schema_version=MANIFEST_SCHEMA,
        readable_paths=allowed,
        writable_paths=allowed,
        current_state_sha256=current_state_sha256,
        current_state_paths=current_state_paths,
    )


def _load_v2(
    payload: dict[str, object],
    raw_manifest: bytes,
    manifest_path: Path,
) -> Campaign35FixtureAuthority:
    fixture_id = _identifier(payload.get("fixture_id"), "campaign_3_5_fixture_id_invalid")
    workspace_root = _workspace(payload.get("workspace_root"))
    if manifest_path == workspace_root or workspace_root in manifest_path.parents:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_inside_workspace")
    baseline_commit = _git_oid(payload.get("baseline_commit"), "campaign_3_5_fixture_commit_invalid")
    baseline_tree = _git_oid(payload.get("baseline_tree"), "campaign_3_5_fixture_tree_invalid")
    readable = _paths(payload.get("readable_paths"), reason="campaign_3_5_fixture_readable_paths_invalid")
    writable = _paths(payload.get("writable_paths"), reason="campaign_3_5_fixture_writable_paths_invalid")
    if not all(_path_in_scope(path, readable) for path in writable):
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_writable_scope_invalid")
    _validate_resolved_scope(workspace_root, readable, reason="campaign_3_5_fixture_readable_paths_unsafe")
    _validate_resolved_scope(workspace_root, writable, reason="campaign_3_5_fixture_writable_paths_unsafe")
    profile = _identifier(payload.get("execution_profile"), "campaign_3_5_fixture_profile_invalid")

    head = _git(workspace_root, "rev-parse", "--verify", "HEAD")
    head_tree = _git(workspace_root, "rev-parse", "--verify", "HEAD^{tree}")
    if head != baseline_commit:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_commit_mismatch")
    if head_tree != baseline_tree:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_tree_mismatch")
    # Keep HEAD and the index pinned to the frozen baseline.  The worktree may
    # contain an evidence-guided repair; that current state is separately
    # committed below and only writable-scope changes are accepted.
    if _git(workspace_root, "write-tree") != baseline_tree or not _git_quiet(
        workspace_root,
        "diff",
        "--cached",
        "--quiet",
        baseline_commit,
        "--",
    ):
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_index_dirty")
    current_state_sha256, current_state_paths = campaign_3_5_workspace_state_commitment(
        workspace_root,
        writable_paths=writable,
    )

    # Preserve the v1 compatibility field without pretending that it is the
    # Git tree itself.  v2 callers should use ``baseline_tree``.
    compatibility_tree_sha256 = hashlib.sha256(baseline_tree.encode("ascii")).hexdigest()
    return Campaign35FixtureAuthority(
        fixture_id=fixture_id,
        workspace_root=workspace_root,
        baseline_tree_sha256=compatibility_tree_sha256,
        allowed_paths=writable,
        execution_profile=profile,
        manifest_sha256=hashlib.sha256(raw_manifest).hexdigest(),
        schema_version=MANIFEST_SCHEMA_V2,
        baseline_commit=baseline_commit,
        baseline_tree=baseline_tree,
        readable_paths=readable,
        writable_paths=writable,
        current_state_sha256=current_state_sha256,
        current_state_paths=current_state_paths,
    )


def campaign_3_5_workspace_state_commitment(
    root: Path,
    *,
    writable_paths: Sequence[str],
) -> tuple[str, tuple[str, ...]]:
    """Commit the exact unstaged repair state without broadening authority.

    HEAD and the index are included in the commitment.  Modified, deleted, and
    untracked files are accepted only inside ``writable_paths`` and every
    existing changed path must be a regular, non-symlinked path beneath the
    fixture root.  This lets a repair prompt bind current applied state while
    making an untracked file outside authority a hard failure.
    """
    workspace = root.resolve(strict=True)
    raw_status = _git_raw(workspace, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries: list[dict[str, str]] = []
    changed_paths: list[str] = []
    for token in raw_status.split("\x00"):
        if not token:
            continue
        if len(token) < 4 or token[2] != " ":
            raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_status_invalid")
        index_status, worktree_status = token[0], token[1]
        relative = token[3:]
        # A non-blank index status is staged state.  ``??`` is Git's untracked
        # marker, not an index entry.
        if index_status not in {" ", "?"}:
            raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_index_dirty")
        if index_status == "?" and worktree_status != "?":
            raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_status_invalid")
        normalized = _paths(
            [relative],
            reason="campaign_3_5_fixture_current_state_path_invalid",
        )[0]
        if not _path_in_scope(normalized, writable_paths):
            raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_current_state_outside_writable_scope")
        target = workspace.joinpath(*PurePosixPath(normalized).parts)
        if target.is_symlink():
            raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_current_state_path_unsafe")
        if target.exists():
            resolved = target.resolve(strict=True)
            if workspace not in resolved.parents:
                raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_current_state_path_unsafe")
            if not target.is_file():
                raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_current_state_path_unsafe")
            content_sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
        else:
            content_sha256 = "deleted"
        changed_paths.append(normalized)
        entries.append(
            {
                "path": normalized,
                "status": index_status + worktree_status,
                "content_sha256": content_sha256,
            }
        )
    # ``git status`` deliberately hides ignored untracked files.  They are
    # still mutable workspace state and must not become a blind spot in either
    # the writable-scope check or the commitment.  Enumerate ignored files
    # separately (without ``--directory``, so Git reports the actual leaves)
    # and bind them exactly like other untracked content.
    raw_ignored = _git_raw(
        workspace,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "-z",
    )
    for relative in raw_ignored.split("\x00"):
        if not relative:
            continue
        normalized = _paths(
            [relative],
            reason="campaign_3_5_fixture_current_state_path_invalid",
        )[0]
        if normalized in changed_paths:
            raise Campaign35FixtureAuthorityError(
                "campaign_3_5_fixture_status_invalid"
            )
        if not _path_in_scope(normalized, writable_paths):
            raise Campaign35FixtureAuthorityError(
                "campaign_3_5_fixture_current_state_outside_writable_scope"
            )
        target = workspace.joinpath(*PurePosixPath(normalized).parts)
        if target.is_symlink() or not target.is_file():
            raise Campaign35FixtureAuthorityError(
                "campaign_3_5_fixture_current_state_path_unsafe"
            )
        resolved = target.resolve(strict=True)
        if workspace not in resolved.parents:
            raise Campaign35FixtureAuthorityError(
                "campaign_3_5_fixture_current_state_path_unsafe"
            )
        changed_paths.append(normalized)
        entries.append(
            {
                "path": normalized,
                "status": "!!",
                "content_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }
        )
    canonical = {
        "schema_version": "campaign-3.5-workspace-state/v1",
        "head": _git(workspace, "rev-parse", "--verify", "HEAD"),
        "index_tree": _git(workspace, "write-tree"),
        "entries": sorted(entries, key=lambda item: item["path"]),
    }
    serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest(), tuple(sorted(changed_paths))


def _identifier(value: object, reason: str) -> str:
    text = str(value or "").strip()
    if not text or len(text) > 160 or any(
        character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        for character in text
    ):
        raise Campaign35FixtureAuthorityError(reason)
    return text


def _workspace(value: object) -> Path:
    raw = str(value or "").strip()
    path = Path(raw).expanduser()
    if not path.is_absolute() or path != Path(os.path.realpath(path)):
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_workspace_invalid")
    path = Path(os.path.realpath(path))
    if not path.is_dir() or not (path / ".git").exists():
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_workspace_invalid")
    try:
        top = Path(_git(path, "rev-parse", "--show-toplevel")).resolve()
    except Campaign35FixtureAuthorityError as error:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_workspace_invalid") from error
    if top != path:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_workspace_invalid")
    return path


def _sha(value: object, reason: str) -> str:
    text = str(value or "")
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text.lower()):
        raise Campaign35FixtureAuthorityError(reason)
    return text.lower()


def _git_oid(value: object, reason: str) -> str:
    text = str(value or "")
    if len(text) not in {40, 64} or text != text.lower() or any(
        character not in "0123456789abcdef" for character in text
    ):
        raise Campaign35FixtureAuthorityError(reason)
    return text


def _paths(value: object, *, reason: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise Campaign35FixtureAuthorityError(reason)
    paths: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise Campaign35FixtureAuthorityError(reason)
        path = item
        candidate = PurePosixPath(path.rstrip("/"))
        if (
            not path
            or path != path.strip()
            or path.startswith("/")
            or "\\" in path
            or "\x00" in path
            or any(ord(character) < 32 or ord(character) == 127 for character in path)
            or candidate.is_absolute()
            or any(part in {"", ".", ".."} for part in candidate.parts)
            or candidate.parts[0] == ".git"
        ):
            raise Campaign35FixtureAuthorityError(reason)
        canonical = candidate.as_posix() + ("/" if path.endswith("/") else "")
        if canonical != path:
            raise Campaign35FixtureAuthorityError(reason)
        paths.append(path)
    if len(paths) != len(set(paths)):
        raise Campaign35FixtureAuthorityError(reason)
    return tuple(paths)


def _allowed_paths(value: object) -> tuple[str, ...]:
    """Compatibility wrapper retained for internal/tests importing it."""
    return _paths(value, reason="campaign_3_5_fixture_allowed_paths_invalid")


def _path_in_scope(path: str, scopes: Sequence[str]) -> bool:
    normalized = path.rstrip("/")
    return any(
        normalized == scope.rstrip("/")
        or normalized.startswith(scope.rstrip("/") + "/")
        for scope in scopes
    )


def _validate_resolved_scope(root: Path, paths: Sequence[str], *, reason: str) -> None:
    root_resolved = root.resolve(strict=True)
    for raw in paths:
        current = root_resolved
        parts = PurePosixPath(raw.rstrip("/")).parts
        for index, part in enumerate(parts):
            current = current / part
            # Reject every existing symlink component, including a symlinked
            # leaf.  Nonexistent leaves are allowed for scoped file creation.
            if current.is_symlink():
                raise Campaign35FixtureAuthorityError(reason)
            if current.exists() and index < len(parts) - 1 and not current.is_dir():
                raise Campaign35FixtureAuthorityError(reason)
            if current.exists() and index == len(parts) - 1 and raw.endswith("/") and not current.is_dir():
                raise Campaign35FixtureAuthorityError(reason)
            if not current.exists():
                break
        resolved = current.resolve(strict=False)
        if resolved != root_resolved and root_resolved not in resolved.parents:
            raise Campaign35FixtureAuthorityError(reason)


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_git_unavailable") from error


def _git_raw(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_git_unavailable") from error


def _git_quiet(root: Path, *args: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
        )
    except OSError as error:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_git_unavailable") from error
    if completed.returncode not in {0, 1}:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_git_unavailable")
    return completed.returncode == 0


def _git_tree_hash(root: Path) -> str:
    tree = _git(root, "write-tree")
    return hashlib.sha256(tree.encode("ascii")).hexdigest()
