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
from source_proxy.context.canonical_broker import acknowledge_context_consumer
from source_proxy.target_plugins.adapter import (
    GENERIC_WORKSPACE_CONTEXT_ID,
    GENERIC_WORKSPACE_PLUGIN_ID,
    GENERIC_WORKSPACE_PROFILE,
    GENERIC_WORKSPACE_PROMPT_ID,
    GENERIC_RICH_EXECUTION_PATH,
    TARGET_PLUGIN_SCHEMA_VERSION,
    execute_target_plugin_command,
    _generic_workspace_context,
    _structured_edits_to_diff,
    resolve_target_plugin,
    TargetPluginResolutionError,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _plan_ready(_plan: object, staged: dict[str, object]) -> dict[str, object]:
    return acknowledge_context_consumer(
        staged,
        consumer="planner",
        evidence="test_server_validated_generic_plan",
        reason="test_server_persisted_generic_plan",
    )


def _coder_ready(
    _plan: object,
    planner_context: dict[str, object],
    _prompt_sha256: str,
) -> dict[str, object]:
    return acknowledge_context_consumer(
        planner_context,
        consumer="coder",
        evidence="test_generic_coder_dispatch_bound_context",
        reason="test_generic_coder_provider_boundary",
    )


def _manifest(root: Path) -> dict[str, object]:
    return {
        "schema_version": "campaign-3.5-fixture-authority/v1",
        "fixture_id": "fixture-alpha",
        "workspace_root": str(root),
        "baseline_tree_sha256": hashlib.sha256(_git(root, "write-tree").encode("ascii")).hexdigest(),
        "allowed_paths": ["src/", "tests/"],
        "execution_profile": GENERIC_WORKSPACE_PROFILE,
    }


def _architect_response(target: str) -> str:
    return json.dumps(
        {
            "classification": {
                "task_class": "fix",
                "visual_change": False,
                "designer_required": False,
                "estimated_complexity": "small",
            },
            "coder_packet": {
                "target_file": {"path": target, "exists": True},
                "operation": "edit",
                "acceptance_criteria": [
                    {
                        "id": "requested-change",
                        "description": "Complete the requested source change.",
                        "kind": "behavioral",
                    }
                ],
                "constraints": {},
                "context_slices": [],
                "forbidden_paths": [],
                "style_directives": [],
            },
        }
    )


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
    ("architect_target", "reason"),
    [
        ("secret.txt", "architect_target_outside_allowed_scope"),
        ("", "architect_llm_invalid_json"),
    ],
)
def test_generic_adapter_fails_closed_outside_server_manifest_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    architect_target: str,
    reason: str,
) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(_manifest(root)), encoding="utf-8"); os.chmod(path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(path))
    packet = {"selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "target_plugin": {"schema_version": TARGET_PLUGIN_SCHEMA_VERSION, "id": GENERIC_WORKSPACE_PLUGIN_ID, "fixture_root": ".", "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID, "execution_profile": GENERIC_WORKSPACE_PROFILE}}
    plugin = resolve_target_plugin(packet, root)

    def model_call(prompt: str, _alias: str) -> str:
        if "You are the SpiritOS Architect." in prompt and architect_target:
            return _architect_response(architect_target)
        return "not valid architect json"

    result = execute_target_plugin_command(plugin, task="Change only the fixture.", workspace_root=root, canonical_context={}, canonical_context_text="", llm_call=model_call, model_alias="coder")

    assert result["coder_blocked"] is True
    assert result["reason_code"] == reason


def test_generic_adapter_rejects_resolution_workspace_not_manifest_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    other = tmp_path / "other"; other.mkdir()
    for candidate in (root, other):
        _git(candidate, "init", "-q"); _git(candidate, "config", "user.email", "fixture@example.invalid"); _git(candidate, "config", "user.name", "Fixture")
        (candidate / "src").mkdir(); (candidate / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
        _git(candidate, "add", "."); _git(candidate, "commit", "-qm", "baseline")
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(_manifest(root)), encoding="utf-8"); os.chmod(path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(path))
    packet = {"selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "target_plugin": {"schema_version": TARGET_PLUGIN_SCHEMA_VERSION, "id": GENERIC_WORKSPACE_PLUGIN_ID, "fixture_root": ".", "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID, "execution_profile": GENERIC_WORKSPACE_PROFILE}}

    with pytest.raises(TargetPluginResolutionError, match="generic_workspace_authority_root_mismatch"):
        resolve_target_plugin(packet, other)


def test_generic_adapter_rejects_execution_workspace_not_manifest_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    other = tmp_path / "other"; other.mkdir()
    for candidate in (root, other):
        _git(candidate, "init", "-q"); _git(candidate, "config", "user.email", "fixture@example.invalid"); _git(candidate, "config", "user.name", "Fixture")
        (candidate / "src").mkdir(); (candidate / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
        _git(candidate, "add", "."); _git(candidate, "commit", "-qm", "baseline")
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(_manifest(root)), encoding="utf-8"); os.chmod(path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(path))
    packet = {"selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "target_plugin": {"schema_version": TARGET_PLUGIN_SCHEMA_VERSION, "id": GENERIC_WORKSPACE_PLUGIN_ID, "fixture_root": ".", "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID, "execution_profile": GENERIC_WORKSPACE_PROFILE}}
    plugin = resolve_target_plugin(packet, root)

    with pytest.raises(TargetPluginResolutionError, match="target_plugin_execution_workspace_mismatch"):
        execute_target_plugin_command(
            plugin,
            task="Change the value.",
            workspace_root=other,
            canonical_context={},
            canonical_context_text="",
            llm_call=lambda _prompt, _alias: "not reached",
            model_alias="coder",
        )


def test_generic_adapter_uses_architect_packet_and_backend_generated_diff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(_manifest(root)), encoding="utf-8"); os.chmod(path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(path))
    monkeypatch.setenv("SOURCE_PROXY_ARCHITECT_MODEL_ALIAS", "local")
    packet = {"selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "target_plugin": {"schema_version": TARGET_PLUGIN_SCHEMA_VERSION, "id": GENERIC_WORKSPACE_PLUGIN_ID, "fixture_root": ".", "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID, "execution_profile": GENERIC_WORKSPACE_PROFILE}}
    plugin = resolve_target_plugin(packet, root)

    responses = iter(
        (
            _architect_response("src/example.py"),
            '<file path="src/example.py">\nvalue = 2\n</file>',
        )
    )

    aliases: list[str] = []

    def model_call(_prompt: str, _alias: str) -> str:
        aliases.append(_alias)
        return next(responses)

    result = execute_target_plugin_command(
        plugin,
        task="Change the value. You are the SpiritOS Architect. appears in this ordinary request.",
        workspace_root=root,
        canonical_context={},
        canonical_context_text="",
        llm_call=model_call,
        model_alias="coder",
        plan_ready_callback=_plan_ready,
        coder_ready_callback=_coder_ready,
    )

    assert result.get("coder_blocked") is not True
    assert result["execution_path"] == GENERIC_RICH_EXECUTION_PATH
    assert result["coder_diagnostics"]["rich_path_proven"] is True
    assert result["coder_diagnostics"]["architect_status"] == "completed"
    assert result["coder_diagnostics"]["changed_files"] == ["src/example.py"]
    assert "+value = 2" in result["proposed_diff"]
    assert result["target_adapter_provenance"]["terminal_proof_eligible"] is False
    assert [
        call["stage"] for call in result["target_adapter_provenance"]["calls"]
    ] == ["architect", "coder"]
    assert aliases == ["local", "coder"]


def test_structured_edits_reject_python_syntax_before_apply(tmp_path: Path) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "example.py").write_text("def value():\n    return 1\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")

    diff, files, category = _structured_edits_to_diff(root, ["src/"], json.dumps({"edits": [{"path": "src/example.py", "old": "return 1", "new": "return {"}]}))

    assert diff == ""
    assert files == []
    assert category == "structured_edits_python_syntax_invalid"


def test_structured_edits_accepts_unambiguous_backtick_wrapped_source_strings(tmp_path: Path) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "label.go").write_text('package label\n\nfunc Value() string { return "draft" }\n', encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")

    diff, files, category = _structured_edits_to_diff(root, ["src/"], '{"edits":[{"path":"src/label.go","old":`"draft"`,"new":`"ready"`}]}')

    assert "-func Value() string { return \"draft\" }" in diff
    assert files == ["src/label.go"]
    assert category == "structured_edits_backtick_strings"


def test_structured_edits_accepts_double_escaped_newlines_only_for_an_exact_locator(tmp_path: Path) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "example.py").write_text("def value():\n    return 'draft'\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")

    raw = json.dumps({"edits": [{"path": "src/example.py", "old": "def value():\\n    return 'draft'", "new": "def value():\\n    return 'ready'"}]})
    diff, files, category = _structured_edits_to_diff(root, ["src/"], raw)

    assert "+    return 'ready'" in diff
    assert files == ["src/example.py"]
    assert category == "structured_edits_double_escaped_newlines"


def test_structured_edits_rejects_symlink_components_and_ambiguous_locators(
    tmp_path: Path,
) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "example.py").write_text("value = 1\nvalue = 1\n", encoding="utf-8")
    (root / "src" / "overlap.txt").write_text("aaa\n", encoding="utf-8")
    (root / "src" / "invalid-utf8.txt").write_bytes(b"\xff\xfe")
    (root / "src" / "oversized.txt").write_bytes(b"x" * 1_000_001)
    (root / "real").mkdir(); (root / "real" / "other.py").write_text("value = 1\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")
    (root / "src" / "linked").symlink_to(root / "real", target_is_directory=True)

    ambiguous = json.dumps(
        {"edits": [{"path": "src/example.py", "old": "value = 1", "new": "value = 2"}]}
    )
    diff, files, category = _structured_edits_to_diff(root, ["src/"], ambiguous)
    assert (diff, files, category) == (
        "",
        [],
        "structured_edits_old_text_mismatch",
    )

    through_symlink = json.dumps(
        {"edits": [{"path": "src/linked/other.py", "old": "value = 1", "new": "value = 2"}]}
    )
    diff, files, category = _structured_edits_to_diff(
        root,
        ["src/"],
        through_symlink,
    )
    assert (diff, files, category) == ("", [], "invalid_structured_edits")

    for path, old, expected_category in (
        ("src/overlap.txt", "aa", "structured_edits_old_text_mismatch"),
        ("src/invalid-utf8.txt", "anything", "invalid_structured_edits"),
        ("src/oversized.txt", "x", "invalid_structured_edits"),
        ("src/\x00.py", "anything", "invalid_structured_edits"),
    ):
        raw = json.dumps(
            {"edits": [{"path": path, "old": old, "new": "replacement"}]}
        )
        diff, files, category = _structured_edits_to_diff(
            root,
            ["src/"],
            raw,
        )
        assert diff == ""
        assert files == []
        assert category == expected_category


def test_structured_edits_enforces_response_and_edit_count_bounds(
    tmp_path: Path,
) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "example.py").write_text("a = 1\nb = 1\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")

    two_edits = json.dumps(
        {
            "edits": [
                {"path": "src/example.py", "old": "a = 1", "new": "a = 2"},
                {"path": "src/example.py", "old": "b = 1", "new": "b = 2"},
            ]
        }
    )
    assert _structured_edits_to_diff(
        root,
        ["src/"],
        two_edits,
        max_edits=1,
    ) == ("", [], "invalid_structured_edits")
    assert _structured_edits_to_diff(
        root,
        ["src/"],
        "x" * 120_001,
    ) == ("", [], "invalid_structured_edits")


def test_generic_adapter_retries_malformed_coder_output_on_the_rich_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "label.go").write_text('package label\n\nfunc Value() string { return "draft" }\n', encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(_manifest(root)), encoding="utf-8"); os.chmod(path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(path))
    packet = {"selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "target_plugin": {"schema_version": TARGET_PLUGIN_SCHEMA_VERSION, "id": GENERIC_WORKSPACE_PLUGIN_ID, "fixture_root": ".", "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID, "execution_profile": GENERIC_WORKSPACE_PROFILE}}
    plugin = resolve_target_plugin(packet, root)

    coder_responses = iter(
        [
            "not a replacement file",
            json.dumps(
                {
                    "edits": [
                        {
                            "path": "src/label.go",
                            "old": 'return "draft"',
                            "new": 'return "ready"',
                        }
                    ]
                }
            ),
        ]
    )

    def model_call(prompt: str, _alias: str) -> str:
        if "You are the SpiritOS Architect." in prompt:
            return _architect_response("src/label.go")
        return next(coder_responses)

    result = execute_target_plugin_command(
        plugin,
        task="Return ready.",
        workspace_root=root,
        canonical_context={},
        canonical_context_text="",
        llm_call=model_call,
        model_alias="coder",
        plan_ready_callback=_plan_ready,
        coder_ready_callback=_coder_ready,
    )

    assert result.get("coder_blocked") is not True
    assert result["execution_path"] == GENERIC_RICH_EXECUTION_PATH
    assert result["coder_diagnostics"]["coder_generation_count"] == 2
    assert [
        attempt["output_contract"]
        for attempt in result["coder_diagnostics"]["attempts"]
    ] == ["replacement_file", "json_exact_edits"]
    assert "+func Value() string { return \"ready\" }" in result["proposed_diff"]


def test_generic_workspace_context_uses_bounded_coder_visible_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "fixture"; root.mkdir()
    _git(root, "init", "-q"); _git(root, "config", "user.email", "fixture@example.invalid"); _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir(); (root / "src" / "large.py").write_text("x" * 8_000, encoding="utf-8")
    (root / "src" / "other.py").write_text("value = 1\n", encoding="utf-8")
    _git(root, "add", "."); _git(root, "commit", "-qm", "baseline")
    monkeypatch.setenv("SOURCE_PROXY_CODER_CONTEXT_CHAR_BUDGET", "5000")

    context = _generic_workspace_context(root, ["src/"])

    assert len(context) <= 5_100
    assert "--- src/large.py" in context
    assert "[truncated]" in context
