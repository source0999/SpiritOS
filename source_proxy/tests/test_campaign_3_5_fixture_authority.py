from __future__ import annotations

import json
import os
import subprocess
import hashlib
from pathlib import Path

import pytest

from source_proxy.benchmarks.campaign_3_5_fixture_authority import (
    ENV_MANIFEST,
    Campaign35FixtureAuthorityError,
    load_campaign_3_5_fixture_authority,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _manifest(root: Path) -> dict[str, object]:
    return {
        "schema_version": "campaign-3.5-fixture-authority/v1",
        "fixture_id": "fixture-alpha",
        "workspace_root": str(root),
        "baseline_tree_sha256": hashlib.sha256(_git(root, "write-tree").encode("ascii")).hexdigest(),
        "allowed_paths": ["src/", "tests/"],
        "execution_profile": "generic-unified-diff-v1",
    }


def test_loads_only_a_mode_600_git_fixture_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(_manifest(root)), encoding="utf-8"); os.chmod(path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(path))

    authority = load_campaign_3_5_fixture_authority()

    assert authority.workspace_root == root.resolve()
    assert authority.adapter_scope()["allowed_paths"] == ["src/", "tests/"]


def test_rejects_manifest_scope_or_baseline_tampering(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "a.txt").write_text("a\n", encoding="utf-8"); _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")
    manifest = _manifest(root); manifest["allowed_paths"] = ["../outside"]
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(manifest), encoding="utf-8"); os.chmod(path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(path))

    with pytest.raises(Campaign35FixtureAuthorityError, match="allowed_paths_invalid"):
        load_campaign_3_5_fixture_authority()
