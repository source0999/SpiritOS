from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from source_proxy.jcode.adapter import (
    DEFAULT_ALLOWED_TOOLS,
    JCODE_EXECUTOR_ENABLED_ENV,
    JCODE_FORCED_ENV,
    JCODE_PINNED_COMMIT,
    REQUIRED_DENIED_TOOLS,
    JCodeEnvelopeError,
    JCodeExecutionEnvelope,
    build_jcode_cli_status,
    build_jcode_command,
    build_jcode_qualification_preview,
    jcode_executor_enabled,
    jcode_subprocess_env,
    render_jcode_provider_config,
    validate_jcode_cli_argv,
    validate_jcode_envelope,
)


def _envelope(tmp_path: Path, **changes: object) -> JCodeExecutionEnvelope:
    workspace = tmp_path / "workspace"
    jcode_home = tmp_path / "jcode-home"
    prompt = jcode_home / "input" / "request.json"
    context_packet = jcode_home / "input" / "context.json"
    evidence = jcode_home / "evidence" / "result.ndjson"
    workspace.mkdir()
    prompt.parent.mkdir(parents=True)
    evidence.parent.mkdir(parents=True)
    prompt.write_text('{"task":"repair bounded helper"}\n', encoding="utf-8")
    context_packet.write_text('{"files":["source_proxy/example.py"]}\n', encoding="utf-8")
    values: dict[str, object] = {
        "workspace": workspace,
        "task_id": "jq-task-001",
        "correlation_id": "jq-correlation-001",
        "repository_id": "spiritos-source-proxy",
        "base_commit": "1" * 40,
        "prompt_file": prompt,
        "immutable_prompt_sha256": hashlib.sha256(prompt.read_bytes()).hexdigest(),
        "context_packet_file": context_packet,
        "context_packet_sha256": hashlib.sha256(context_packet.read_bytes()).hexdigest(),
        "evidence_output_path": evidence,
        "jcode_home": jcode_home,
        "provider_profile": "spiritos-qualification",
        "model": "qwen2.5-coder:7b",
        "model_parameters": {"temperature": 0, "seed": 7, "max_tokens": 4096},
        "inference_endpoint": "http://127.0.0.1:4000/v1",
        "allowed_files": ("source_proxy/example.py",),
    }
    values.update(changes)
    return JCodeExecutionEnvelope(**values)  # type: ignore[arg-type]


def test_executor_is_disabled_by_default() -> None:
    assert not jcode_executor_enabled({})
    assert jcode_executor_enabled({JCODE_EXECUTOR_ENABLED_ENV: "true"})


def test_missing_binary_is_truthfully_config_blocked() -> None:
    status = build_jcode_cli_status(
        command_resolver=lambda _: None,
        environ={JCODE_EXECUTOR_ENABLED_ENV: "1"},
        authorized_binary_path="/definitely/missing/jcode",
    )

    assert status["status"] == "config_blocked"
    assert status["reason"] == "jcode_binary_not_found"
    assert status["would_run_task"] is False
    assert not any(status["authority"].values())


def test_status_requires_the_pinned_source_commit(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[0] == "git":
            return subprocess.CompletedProcess(command, 0, JCODE_PINNED_COMMIT + "\n", "")
        return subprocess.CompletedProcess(command, 0, "jcode v0.58.51-dev (2444e7b6)\n", "")

    status = build_jcode_cli_status(
        command_resolver=lambda _: "/audit/jcode",
        command_runner=runner,
        source_checkout=tmp_path,
    )

    assert status["status"] == "detected_qualification_blocked"
    assert status["version"] == "0.58.51-dev"
    assert status["binary_version_match"] is True
    assert status["pinned_source_match"] is True
    assert status["binary_and_source_match"] is True
    assert status["can_run_live_task"] is False
    assert calls[0][1] == "--version"
    assert calls[0][0].endswith("/approved-binary/jcode")


def test_safe_envelope_builds_bounded_ndjson_command(tmp_path: Path) -> None:
    envelope = _envelope(tmp_path)

    validation = validate_jcode_envelope(envelope)
    command = build_jcode_command(envelope)

    assert validation["ok"] is True
    assert validation["live_ready"] is False
    assert command[0] == "jcode"
    assert "--no-update" in command
    assert "--no-selfdev" in command
    assert "--disable-base-tools" in command
    assert command[command.index("--tools") + 1] == ",".join(DEFAULT_ALLOWED_TOOLS)
    assert "--disabled-tools" in command
    assert command[-2] == "--ndjson"
    assert envelope.immutable_prompt_sha256 in command[-1]
    assert "repair bounded helper" not in command[-1]


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"allowed_files": ("../outside.py",)}, "allowed_file_path_escape"),
        ({"allowed_files": (".env",)}, "allowed_file_protected_path"),
        ({"allowed_files": ("%2e%2e/outside.py",)}, "allowed_file_encoded_path_not_allowed"),
        ({"allowed_files": (".",)}, "allowed_file_broad_or_empty_path_not_allowed"),
        ({"allowed_files": ("source_proxy/*.py",)}, "allowed_file_wildcard_path_not_allowed"),
        ({"allowed_tools": ("read", "bash")}, "unsafe_or_unknown_allowed_tool"),
        ({"command_policy": "shell_allowed"}, "unsafe_command_policy"),
        ({"network_policy": "unrestricted"}, "unsafe_network_policy"),
        ({"inference_endpoint": "https://api.example.com/v1"}, "inference_endpoint_not_loopback"),
        ({"fresh_session_required": False}, "fresh_session_required"),
        ({"approval_capability": True}, "jcode_approval_authority_forbidden"),
        ({"binary": "/usr/bin/bash"}, "jcode_binary_identity_invalid"),
        ({"task_id": "bad task id"}, "task_id_invalid"),
    ],
)
def test_envelope_rejects_authority_and_scope_expansion(
    tmp_path: Path,
    changes: dict[str, object],
    reason: str,
) -> None:
    validation = validate_jcode_envelope(_envelope(tmp_path, **changes))
    reasons = {item["reason_code"] for item in validation["blocked_reasons"]}

    assert validation["ok"] is False
    assert reason in reasons


def test_envelope_rejects_optional_feature_activation(tmp_path: Path) -> None:
    envelope = _envelope(
        tmp_path,
        feature_flags={"JCODE_MEMORY_ENABLED": True},
    )

    validation = validate_jcode_envelope(envelope)

    assert validation["ok"] is False
    assert {
        "path": "*",
        "reason_code": "unsafe_feature_enabled:JCODE_MEMORY_ENABLED",
    } in validation["blocked_reasons"]
    with pytest.raises(JCodeEnvelopeError, match="not safe"):
        build_jcode_command(envelope)


def test_envelope_requires_the_complete_feature_flag_set(tmp_path: Path) -> None:
    validation = validate_jcode_envelope(_envelope(tmp_path, feature_flags={}))

    assert validation["ok"] is False
    assert any(
        item["reason_code"].startswith("feature_flag_missing:")
        for item in validation["blocked_reasons"]
    )


def test_envelope_rejects_context_hash_drift(tmp_path: Path) -> None:
    envelope = _envelope(tmp_path, context_packet_sha256="3" * 64)

    validation = validate_jcode_envelope(envelope)

    assert validation["ok"] is False
    assert any(
        item["reason_code"] == "context_packet_hash_mismatch"
        for item in validation["blocked_reasons"]
    )


def test_envelope_rejects_unknown_or_out_of_range_model_parameters(
    tmp_path: Path,
) -> None:
    envelope = _envelope(
        tmp_path,
        model_parameters={"temperature": 4, "provider_override": 1},
    )

    reasons = {
        item["reason_code"]
        for item in validate_jcode_envelope(envelope)["blocked_reasons"]
    }

    assert "model_parameter_out_of_range:temperature" in reasons
    assert "model_parameter_unknown:provider_override" in reasons


def test_existing_state_markers_block_cross_task_contamination(tmp_path: Path) -> None:
    envelope = _envelope(tmp_path)
    (envelope.jcode_home / "mcp.json").write_text("{}", encoding="utf-8")

    validation = validate_jcode_envelope(envelope)

    assert validation["ok"] is False
    assert any(
        item["reason_code"] == "jcode_state_contamination"
        for item in validation["blocked_reasons"]
    )


def test_workspace_and_jcode_home_must_be_disjoint(tmp_path: Path) -> None:
    nested_workspace = tmp_path / "jcode-home" / "workspace"
    nested_workspace.mkdir(parents=True)

    validation = validate_jcode_envelope(
        _envelope(tmp_path, workspace=nested_workspace)
    )

    assert validation["ok"] is False
    assert any(
        item["reason_code"] == "jcode_home_not_isolated"
        for item in validation["blocked_reasons"]
    )


def test_existing_evidence_output_is_rejected(tmp_path: Path) -> None:
    envelope = _envelope(tmp_path)
    envelope.evidence_output_path.write_text("stale\n", encoding="utf-8")

    reasons = {
        item["reason_code"]
        for item in validate_jcode_envelope(envelope)["blocked_reasons"]
    }

    assert "evidence_output_not_fresh" in reasons
    assert "jcode_state_unexpected_file" in reasons


def test_nested_allowed_and_protected_paths_cannot_overlap(tmp_path: Path) -> None:
    envelope = _envelope(
        tmp_path,
        allowed_files=("source_proxy/example.py",),
        protected_files=("source_proxy",),
    )

    validation = validate_jcode_envelope(envelope)

    assert validation["ok"] is False
    assert any(
        item["reason_code"] == "allowed_protected_path_overlap"
        for item in validation["blocked_reasons"]
    )


def test_environment_is_allowlisted_and_forced_safe(tmp_path: Path) -> None:
    envelope = _envelope(tmp_path)

    env = jcode_subprocess_env(
        {
            "PATH": "/usr/bin",
            "LANG": "C.UTF-8",
            "OPENAI_API_KEY": "secret",
            "SOURCE_PROXY_TOKEN": "secret",
        },
        envelope,
    )

    assert "OPENAI_API_KEY" not in env
    assert "SOURCE_PROXY_TOKEN" not in env
    assert env["JCODE_HOME"] == str(envelope.jcode_home.resolve())
    assert env["HOME"] == str(envelope.jcode_home.resolve())
    assert all(env[key] == value for key, value in JCODE_FORCED_ENV.items())
    assert "bash" in env["JCODE_DISABLED_TOOLS"]


def test_argv_policy_rejects_resume_server_and_unrestricted_tools() -> None:
    unsafe = validate_jcode_cli_argv(
        [
            "jcode",
            "--resume=session-1",
            "--no-update",
            "--no-selfdev",
            "--disable-base-tools",
            "--tools=all",
            "serve",
            "--ndjson",
        ]
    )

    assert unsafe["allowed"] is False
    assert "--resume" in unsafe["blocked_reasons"]
    assert "unrestricted_tools" in unsafe["blocked_reasons"]
    assert "missing:run" in unsafe["blocked_reasons"]


def test_argv_policy_rejects_direct_provider_override() -> None:
    unsafe = validate_jcode_cli_argv(
        [
            "jcode",
            "--cwd=/tmp/worktree",
            "--provider=openrouter",
            "--provider-profile=spiritos-qualification",
            "--model=qwen2.5-coder:7b",
            "--no-update",
            "--no-selfdev",
            "--disable-base-tools",
            "--tools=read",
            "--disabled-tools=" + ",".join(REQUIRED_DENIED_TOOLS),
            "run",
            "--ndjson",
            "task",
        ]
    )

    assert unsafe["allowed"] is False
    assert "--provider" in unsafe["blocked_reasons"]


def test_provider_config_is_local_no_auth_and_fixed_model(tmp_path: Path) -> None:
    envelope = _envelope(tmp_path)

    config = render_jcode_provider_config(envelope)

    assert "[providers.spiritos-qualification]" in config
    assert 'base_url = "http://127.0.0.1:4000/v1"' in config
    assert 'auth = "none"' in config
    assert 'default_model = "qwen2.5-coder:7b"' in config
    assert "\napi_key =" not in config
    assert "api_key_env" not in config


def test_preview_never_claims_execution_or_authority(tmp_path: Path) -> None:
    preview = build_jcode_qualification_preview(
        _envelope(tmp_path),
        environ={JCODE_EXECUTOR_ENABLED_ENV: "1"},
    )

    assert preview["status"] == "config_blocked"
    assert preview["reason_code"] == "jcode_qualification_live_execution_not_enabled"
    assert preview["would_run_task"] is False
    assert not any(preview["authority"].values())
    assert preview["claim_ceiling"] == "qualification_preview_only_no_runtime_integration"
