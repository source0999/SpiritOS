"""Safe deterministic materialization primitives for Campaign 3.5 fixtures.

This module deliberately has no production imports.  It is run by the private
benchmark harness to create a one-task disposable Git repository.  The caller
owns the secret seed and may expose only the returned public manifest to the
fixture-execution process.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping


class Campaign35FixtureBuildError(ValueError):
    """Raised before any unsafe fixture write can occur."""


@dataclass(frozen=True)
class FixtureMaterialization:
    fixture_root: Path
    baseline_tree_sha256: str
    content_sha256: str
    public_manifest: dict[str, object]


def _safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise Campaign35FixtureBuildError("campaign_3_5_fixture_path_invalid")
    return path


def _write_files(root: Path, files: Mapping[str, str]) -> None:
    if not files:
        raise Campaign35FixtureBuildError("campaign_3_5_fixture_files_empty")
    root_resolved = root.resolve()
    for relative, content in sorted(files.items()):
        path = root.joinpath(*_safe_relative_path(relative).parts)
        resolved_parent = path.parent.resolve()
        if resolved_parent != root_resolved and root_resolved not in resolved_parent.parents:
            raise Campaign35FixtureBuildError("campaign_3_5_fixture_path_invalid")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )
    return completed.stdout.strip()


def _initialize_baseline(root: Path) -> str:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "campaign35-fixture@example.invalid")
    _git(root, "config", "user.name", "Campaign 3.5 Fixture")
    _git(root, "add", "--all")
    _git(root, "commit", "-qm", "campaign-3.5 immutable fixture baseline")
    tree = _git(root, "write-tree")
    return hashlib.sha256(tree.encode("ascii")).hexdigest()


def materialize_fixture(root: Path, *, files: Mapping[str, str], seed: str) -> str:
    """Compatibility primitive returning a deterministic content commitment.

    New callers should use :func:`materialize_git_fixture`, which also records
    a Git baseline and enforces that the root is owned by a fixture parent.
    """
    if not seed:
        raise Campaign35FixtureBuildError("campaign_3_5_fixture_seed_invalid")
    if root.exists():
        raise Campaign35FixtureBuildError("campaign_3_5_fixture_root_exists")
    root.mkdir(parents=True, exist_ok=False)
    _write_files(root, files)
    canonical = {path: files[path] for path in sorted(files)}
    return hashlib.sha256(json.dumps({"seed": seed, "files": canonical}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def materialize_git_fixture(
    fixture_parent: Path,
    fixture_name: str,
    *,
    fixture_id: str,
    files: Mapping[str, str],
    seed_commitment: str,
    allowed_paths: list[str],
    execution_profile: str = "generic-architect-coder-packet-v1",
) -> FixtureMaterialization:
    """Create an owned fixture repository and return non-secret authority data.

    `fixture_parent` is a harness-owned disposable directory, not an active
    product repository.  The raw seed never enters the fixture tree or public
    manifest; its commitment is sufficient to bind audit records.
    """
    if not fixture_id or not seed_commitment or not allowed_paths:
        raise Campaign35FixtureBuildError("campaign_3_5_fixture_manifest_input_invalid")
    parent = fixture_parent.resolve()
    if not parent.is_dir() or (parent / ".git").exists():
        raise Campaign35FixtureBuildError("campaign_3_5_fixture_parent_invalid")
    name = _safe_relative_path(fixture_name)
    if len(name.parts) != 1:
        raise Campaign35FixtureBuildError("campaign_3_5_fixture_name_invalid")
    root = (parent / name.name).resolve()
    if root.parent != parent or root.exists():
        raise Campaign35FixtureBuildError("campaign_3_5_fixture_root_invalid")
    for allowed in allowed_paths:
        _safe_relative_path(allowed.rstrip("/"))

    root.mkdir(mode=0o700)
    _write_files(root, files)
    baseline_tree_sha256 = _initialize_baseline(root)
    canonical = {path: files[path] for path in sorted(files)}
    content_sha256 = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return FixtureMaterialization(
        fixture_root=root,
        baseline_tree_sha256=baseline_tree_sha256,
        content_sha256=content_sha256,
        public_manifest={
            "schema_version": "campaign-3.5-fixture-authority/v1",
            "fixture_id": fixture_id,
            "workspace_root": str(root),
            "baseline_tree_sha256": baseline_tree_sha256,
            "allowed_paths": allowed_paths,
            "execution_profile": execution_profile,
            "seed_commitment": seed_commitment,
            "content_sha256": content_sha256,
        },
    )
