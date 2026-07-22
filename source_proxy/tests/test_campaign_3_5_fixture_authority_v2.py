from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from source_proxy.benchmarks.campaign_3_5_fixture_authority import (
    ENV_MANIFEST,
    MANIFEST_SCHEMA_V2,
    Campaign35FixtureAuthorityError,
    load_campaign_3_5_fixture_authority,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _fixture(tmp_path: Path) -> Path:
    root = tmp_path / "fixture"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir()
    (root / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_example.py").write_text("def test_value(): pass\n", encoding="utf-8")
    _git(root, "add", "--", "src/example.py", "tests/test_example.py")
    _git(root, "commit", "-qm", "baseline")
    return root.resolve()


def _manifest(root: Path) -> dict[str, object]:
    return {
        "schema_version": MANIFEST_SCHEMA_V2,
        "fixture_id": "basic-backend-fixture",
        "workspace_root": str(root),
        "baseline_commit": _git(root, "rev-parse", "HEAD"),
        "baseline_tree": _git(root, "rev-parse", "HEAD^{tree}"),
        "readable_paths": ["src/", "tests/"],
        "writable_paths": ["src/"],
        "execution_profile": "generic-architect-coder-packet-v1",
    }


def _write_manifest(parent: Path, payload: dict[str, object], name: str = "authority.json") -> Path:
    path = parent / name
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    os.chmod(path, 0o600)
    return path.resolve()


def _load(path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(ENV_MANIFEST, str(path))
    return load_campaign_3_5_fixture_authority()


def test_v2_binds_real_commit_tree_and_separate_scopes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path)
    payload = _manifest(root)
    path = _write_manifest(tmp_path, payload)

    authority = _load(path, monkeypatch)

    assert authority.schema_version == MANIFEST_SCHEMA_V2
    assert authority.baseline_commit == payload["baseline_commit"]
    assert authority.baseline_tree == payload["baseline_tree"]
    assert authority.readable_paths == ("src/", "tests/")
    assert authority.writable_paths == ("src/",)
    assert authority.allowed_paths == ("src/",)
    scope = authority.adapter_scope()
    assert scope["allowed_paths"] == ["src/"]
    assert scope["readable_paths"] == ["src/", "tests/"]
    assert scope["writable_paths"] == ["src/"]


def test_generic_adapter_rejects_manifest_with_wrong_execution_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from source_proxy.target_plugins.adapter import (
        GENERIC_WORKSPACE_CONTEXT_ID,
        GENERIC_WORKSPACE_PLUGIN_ID,
        GENERIC_WORKSPACE_PROFILE,
        GENERIC_WORKSPACE_PROMPT_ID,
        TARGET_PLUGIN_SCHEMA_VERSION,
        TargetPluginResolutionError,
        resolve_target_plugin,
    )

    root = _fixture(tmp_path)
    payload = _manifest(root)
    payload["execution_profile"] = "unexpected-profile"
    path = _write_manifest(tmp_path, payload)
    monkeypatch.setenv(ENV_MANIFEST, str(path))
    packet = {
        "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
        "target_plugin": {
            "schema_version": TARGET_PLUGIN_SCHEMA_VERSION,
            "id": GENERIC_WORKSPACE_PLUGIN_ID,
            "fixture_root": ".",
            "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
            "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID,
            "execution_profile": GENERIC_WORKSPACE_PROFILE,
        },
    }

    with pytest.raises(TargetPluginResolutionError, match="authority_execution_profile_mismatch"):
        resolve_target_plugin(packet, root)


@pytest.mark.parametrize(
    ("field", "replacement", "reason"),
    [
        ("baseline_commit", "0" * 40, "fixture_commit_mismatch"),
        ("baseline_tree", "0" * 40, "fixture_tree_mismatch"),
        ("writable_paths", ["docs/"], "writable_scope_invalid"),
        ("readable_paths", ["../src"], "readable_paths_invalid"),
        ("writable_paths", [".git/config"], "writable_paths_invalid"),
    ],
)
def test_v2_rejects_invalid_bindings_and_path_scopes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    replacement: object,
    reason: str,
) -> None:
    root = _fixture(tmp_path)
    payload = _manifest(root)
    payload[field] = replacement
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(Campaign35FixtureAuthorityError, match=reason):
        _load(path, monkeypatch)


def test_v2_requires_manifest_outside_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path)
    path = _write_manifest(root, _manifest(root))

    with pytest.raises(Campaign35FixtureAuthorityError, match="manifest_inside_workspace"):
        _load(path, monkeypatch)


def test_v2_requires_canonical_resolved_workspace_spelling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path)
    payload = _manifest(root)
    payload["workspace_root"] = str(root / ".." / root.name)
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(Campaign35FixtureAuthorityError, match="workspace_invalid"):
        _load(path, monkeypatch)


def test_v2_rejects_staged_index_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path)
    payload = _manifest(root)
    path = _write_manifest(tmp_path, payload)
    (root / "src" / "example.py").write_text("value = 2\n", encoding="utf-8")
    _git(root, "add", "--", "src/example.py")

    with pytest.raises(Campaign35FixtureAuthorityError, match="fixture_index_dirty"):
        _load(path, monkeypatch)


@pytest.mark.parametrize("change", ["unstaged", "untracked"])
def test_v2_binds_unstaged_in_scope_current_repair_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    root = _fixture(tmp_path)
    path = _write_manifest(tmp_path, _manifest(root))
    baseline_authority = _load(path, monkeypatch)
    if change == "unstaged":
        (root / "src" / "example.py").write_text("value = 2\n", encoding="utf-8")
    else:
        (root / "src" / "new.py").write_text("value = 2\n", encoding="utf-8")

    authority = _load(path, monkeypatch)

    assert authority.current_state_paths == (
        "src/example.py" if change == "unstaged" else "src/new.py",
    )
    assert authority.current_state_sha256 != baseline_authority.current_state_sha256


def test_v2_rejects_unstaged_state_outside_writable_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path)
    path = _write_manifest(tmp_path, _manifest(root))
    (root / "tests" / "test_example.py").write_text("def test_changed(): pass\n", encoding="utf-8")

    with pytest.raises(Campaign35FixtureAuthorityError, match="current_state_outside_writable_scope"):
        _load(path, monkeypatch)


def test_v2_binds_ignored_file_inside_writable_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path)
    (root / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
    _git(root, "add", "--", ".gitignore")
    _git(root, "commit", "-qm", "ignore generated fixture file")
    path = _write_manifest(tmp_path, _manifest(root))
    baseline = _load(path, monkeypatch)
    (root / "src" / "ignored.py").write_text("value = 2\n", encoding="utf-8")

    authority = _load(path, monkeypatch)

    assert authority.current_state_paths == ("src/ignored.py",)
    assert authority.current_state_sha256 != baseline.current_state_sha256


def test_v2_rejects_ignored_file_outside_writable_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path)
    (root / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
    _git(root, "add", "--", ".gitignore")
    _git(root, "commit", "-qm", "ignore generated fixture file")
    path = _write_manifest(tmp_path, _manifest(root))
    (root / "tests" / "ignored.py").write_text("value = 2\n", encoding="utf-8")

    with pytest.raises(
        Campaign35FixtureAuthorityError,
        match="current_state_outside_writable_scope",
    ):
        _load(path, monkeypatch)


def test_v2_rejects_untracked_symlink_even_inside_writable_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path)
    path = _write_manifest(tmp_path, _manifest(root))
    outside = tmp_path / "outside.py"
    outside.write_text("secret = True\n", encoding="utf-8")
    (root / "src" / "linked.py").symlink_to(outside)

    with pytest.raises(Campaign35FixtureAuthorityError, match="current_state_path_unsafe"):
        _load(path, monkeypatch)


def test_v2_rejects_symlinked_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)
    # Commit the symlink so the baseline itself is internally consistent.  It
    # must still never become an authority scope.
    _git(root, "add", "--", "linked")
    _git(root, "commit", "-qm", "add unsafe link")
    payload = _manifest(root)
    payload["readable_paths"] = ["src/", "linked/"]
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(Campaign35FixtureAuthorityError, match="readable_paths_unsafe"):
        _load(path, monkeypatch)


def test_v2_rejects_symlinked_manifest_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path)
    target = _write_manifest(tmp_path, _manifest(root), "target.json")
    link = tmp_path / "link.json"
    link.symlink_to(target)
    monkeypatch.setenv(ENV_MANIFEST, str(link.absolute()))

    with pytest.raises(Campaign35FixtureAuthorityError, match="manifest_unsafe"):
        load_campaign_3_5_fixture_authority()
