"""Server-owned registration for a disposable Campaign 3.5 fixture workspace.

The production request never supplies a filesystem path or allowed-file set.
The benchmark harness provisions a private, mode-0600 manifest and starts the
Source Proxy with its absolute path.  This module validates that configuration
before an adapter can see the fixture; it deliberately contains no task IDs,
prompts, seeds, oracle data, or expected outcomes.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA = "campaign-3.5-fixture-authority/v1"
ENV_MANIFEST = "SPIRITOS_CAMPAIGN_3_5_FIXTURE_MANIFEST"


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

    def adapter_scope(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "fixture_root": ".",
            "allowed_paths": list(self.allowed_paths),
            "workspace_root": str(self.workspace_root),
            "baseline_tree_sha256": self.baseline_tree_sha256,
            "execution_profile": self.execution_profile,
            "manifest_sha256": self.manifest_sha256,
        }


def load_campaign_3_5_fixture_authority() -> Campaign35FixtureAuthority:
    raw = os.environ.get(ENV_MANIFEST, "").strip()
    if not raw:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_missing")
    manifest_path = Path(raw).expanduser()
    if not manifest_path.is_absolute():
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_not_absolute")
    manifest_path = Path(os.path.realpath(manifest_path))
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
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version", "fixture_id", "workspace_root", "baseline_tree_sha256",
        "allowed_paths", "execution_profile",
    }:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_schema_invalid")
    if payload.get("schema_version") != MANIFEST_SCHEMA:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_manifest_schema_invalid")
    fixture_id = _identifier(payload.get("fixture_id"), "campaign_3_5_fixture_id_invalid")
    workspace_root = _workspace(payload.get("workspace_root"))
    baseline = _sha(payload.get("baseline_tree_sha256"), "campaign_3_5_fixture_baseline_invalid")
    allowed = _allowed_paths(payload.get("allowed_paths"))
    profile = _identifier(payload.get("execution_profile"), "campaign_3_5_fixture_profile_invalid")
    if _git_tree_hash(workspace_root) != baseline:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_baseline_mismatch")
    return Campaign35FixtureAuthority(
        fixture_id=fixture_id,
        workspace_root=workspace_root,
        baseline_tree_sha256=baseline,
        allowed_paths=allowed,
        execution_profile=profile,
        manifest_sha256=hashlib.sha256(raw_manifest).hexdigest(),
    )


def _identifier(value: object, reason: str) -> str:
    text = str(value or "").strip()
    if not text or len(text) > 160 or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in text):
        raise Campaign35FixtureAuthorityError(reason)
    return text


def _workspace(value: object) -> Path:
    raw = str(value or "").strip()
    path = Path(raw).expanduser()
    if not path.is_absolute() or Path(os.path.abspath(path)) != Path(os.path.realpath(path)):
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_workspace_invalid")
    path = Path(os.path.realpath(path))
    if not path.is_dir() or not (path / ".git").exists():
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_workspace_invalid")
    try:
        top = Path(subprocess.check_output(["git", "-C", str(path), "rev-parse", "--show-toplevel"], text=True).strip()).resolve()
    except (OSError, subprocess.CalledProcessError) as error:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_workspace_invalid") from error
    if top != path:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_workspace_invalid")
    return path


def _sha(value: object, reason: str) -> str:
    text = str(value or "")
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text.lower()):
        raise Campaign35FixtureAuthorityError(reason)
    return text.lower()


def _allowed_paths(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_allowed_paths_invalid")
    paths = tuple(str(item) for item in value)
    if len(paths) != len(set(paths)) or any(
        not path or path.startswith("/") or "\\" in path or ".." in Path(path).parts
        for path in paths
    ):
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_allowed_paths_invalid")
    return paths


def _git_tree_hash(root: Path) -> str:
    try:
        tree = subprocess.check_output(["git", "-C", str(root), "write-tree"], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise Campaign35FixtureAuthorityError("campaign_3_5_fixture_tree_unavailable") from error
    return hashlib.sha256(tree.encode("ascii")).hexdigest()
