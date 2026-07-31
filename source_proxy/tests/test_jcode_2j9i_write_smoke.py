from __future__ import annotations

import pytest

from source_proxy.jcode.write_smoke import WriteSmokePolicy, WriteSmokeSafetyError


@pytest.mark.parametrize(
    ("operation", "path", "reason"),
    [
        ("modify", "qualification_write_fixture/test_source_file.py", "protected"),
        ("modify", "qualification_write_fixture/second_source.py", "protected"),
        ("modify", "docs/note.md", "protected"),
        ("modify", "source_proxy/authority.py", "protected"),
        ("modify", "../escape.py", "escape"),
        ("modify", "/tmp/escape.py", "escape"),
        ("delete", "qualification_write_fixture/source_file.py", "operation"),
        ("rename", "qualification_write_fixture/source_file.py", "operation"),
        ("symlink", "qualification_write_fixture/source_file.py", "operation"),
        ("hardlink", "qualification_write_fixture/source_file.py", "operation"),
    ],
)
def test_mutation_boundary_denies_all_non_authorized_changes(operation: str, path: str, reason: str) -> None:
    with pytest.raises(WriteSmokeSafetyError, match=reason):
        WriteSmokePolicy().authorize_mutation(operation, path)


def test_only_the_sealed_source_modification_is_permitted() -> None:
    WriteSmokePolicy().authorize_mutation("modify", "qualification_write_fixture/source_file.py")


def test_command_policy_is_exact() -> None:
    policy = WriteSmokePolicy()
    policy.authorize_command(policy.focused_validation)
    with pytest.raises(WriteSmokeSafetyError, match="command"):
        policy.authorize_command("python -m pytest -q")


@pytest.mark.parametrize(
    "kwargs, reason",
    [
        ({"direct_ollama": True}, "direct_ollama"),
        ({"model": "qwen2.5-coder:7b"}, "model"),
        ({"digest": "wrong"}, "digest"),
        ({"provider_profile_id": "other"}, "provider"),
        ({"fallback": True}, "fallback"),
    ],
)
def test_model_policy_denies_substitution_and_direct_access(kwargs: dict[str, object], reason: str) -> None:
    policy = WriteSmokePolicy()
    values: dict[str, object] = {"provider_profile_id": policy.provider_profile_id, "model": policy.model, "digest": policy.model_digest, "fallback": False, "direct_ollama": False}
    values.update(kwargs)
    with pytest.raises(WriteSmokeSafetyError, match=reason):
        policy.verify_model_binding(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs, reason",
    [
        ({"model_timeout": True}, "model_timeout"),
        ({"tool_timeout": True}, "tool_timeout"),
        ({"cancelled": True}, "cancelled"),
        ({"crashed_after_partial_write": True}, "crashed_after_partial_write"),
        ({"evidence_written": False}, "evidence_destination"),
        ({"terminal_event": False}, "terminal_event"),
        ({"filesystem_ledger_complete": False}, "filesystem_ledger"),
        ({"git_ledger_reconciled": False}, "git_ledger"),
        ({"cleanup_complete": False}, "cleanup"),
    ],
)
def test_terminal_integrity_fails_closed(kwargs: dict[str, bool], reason: str) -> None:
    with pytest.raises(WriteSmokeSafetyError, match=reason):
        WriteSmokePolicy().verify_terminal_integrity(**kwargs)
