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
from source_proxy.target_plugins.adapter import (
    GENERIC_WORKSPACE_CONTEXT_ID,
    GENERIC_WORKSPACE_PLUGIN_ID,
    GENERIC_WORKSPACE_PROFILE,
    GENERIC_WORKSPACE_PROMPT_ID,
    TARGET_PLUGIN_SCHEMA_VERSION,
    execute_target_plugin_command,
    _structured_edits_to_diff,
    resolve_target_plugin,
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


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        ("```diff\ndiff --git a/secret.txt b/secret.txt\n--- a/secret.txt\n+++ b/secret.txt\n@@ -0,0 +1 @@\n+x\n```", "generic_workspace_scope_violation"),
        ("not a diff", "generic_workspace_model_diff_invalid"),
    ],
)
def test_generic_adapter_fails_closed_outside_server_manifest_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, response: str, reason: str
) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(_manifest(root)), encoding="utf-8"); os.chmod(path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(path))
    packet = {"selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "target_plugin": {"schema_version": TARGET_PLUGIN_SCHEMA_VERSION, "id": GENERIC_WORKSPACE_PLUGIN_ID, "fixture_root": ".", "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID, "execution_profile": GENERIC_WORKSPACE_PROFILE}}
    plugin = resolve_target_plugin(packet, root)
    result = execute_target_plugin_command(plugin, task="Change only the fixture.", workspace_root=root, canonical_context={}, canonical_context_text="", llm_call=lambda _prompt, _alias: response, model_alias="coder")

    assert result["coder_blocked"] is True
    assert result["reason_code"] == reason


def test_generic_adapter_accepts_a_pure_unfenced_unified_diff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(_manifest(root)), encoding="utf-8"); os.chmod(path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(path))
    packet = {"selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "target_plugin": {"schema_version": TARGET_PLUGIN_SCHEMA_VERSION, "id": GENERIC_WORKSPACE_PLUGIN_ID, "fixture_root": ".", "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID, "execution_profile": GENERIC_WORKSPACE_PROFILE}}
    plugin = resolve_target_plugin(packet, root)
    diff = "diff --git a/src/example.py b/src/example.py\n--- a/src/example.py\n+++ b/src/example.py\n@@ -1 +1 @@\n-value = 1\n+value = 2\n"
    result = execute_target_plugin_command(plugin, task="Change the value.", workspace_root=root, canonical_context={}, canonical_context_text="", llm_call=lambda _prompt, _alias: diff, model_alias="coder")

    assert result["coder_blocked"] is False
    assert result["coder_diagnostics"]["model_response_format"] == "unfenced_unified_diff"


def test_structured_edits_reject_python_syntax_before_apply(tmp_path: Path) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "example.py").write_text("def value():\n    return 1\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")

    diff, files, category = _structured_edits_to_diff(root, ["src/"], json.dumps({"edits": [{"path": "src/example.py", "old": "return 1", "new": "return {"}]}))

    assert diff == ""
    assert files == []
    assert category == "structured_edits_python_syntax_invalid"
