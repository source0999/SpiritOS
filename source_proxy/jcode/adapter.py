"""Fail-closed command seam for an isolated JCode qualification process.

This module deliberately does not dispatch JCode or join the production coding
orchestrator. It validates a bounded executor envelope, exposes a capability
probe, and builds an auditable command preview for a future controlled gate.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import stat
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from source_proxy.jcode.constants import JCODE_BINARY_PATH, JCODE_BINARY_SHA256, JCODE_VERSION

from source_proxy.safety.paths import (
    has_percent_encoded_path_syntax,
    is_secret_shaped_path,
    path_escapes_workspace,
)


JCODE_QUALIFICATION_SCHEMA_VERSION = "coding.jcode-qualification/v1"
JCODE_EXECUTION_REQUEST_SCHEMA_VERSION = "coding.jcode-execution-request/v1"
JCODE_EXECUTION_RESULT_SCHEMA_VERSION = "coding.jcode-execution-result/v1"
JCODE_ADAPTER_VERSION = "jcode-qualification-adapter/v1"
JCODE_EXECUTOR_ID = "candidate.jcode-executor"
JCODE_EXECUTOR_ENABLED_ENV = "JCODE_EXECUTOR_ENABLED"
JCODE_PINNED_COMMIT = "2444e7b6bc80d421ae3ee404081bdb41150a1830"
JCODE_PINNED_RELEASE = "v0.58.51-dev"

DEFAULT_JCODE_TIMEOUT_SECONDS = 300
DEFAULT_JCODE_MAX_OUTPUT_BYTES = 2_000_000
DEFAULT_ALLOWED_TOOLS = (
    "read",
    "glob",
    "grep",
    "ls",
    "write",
    "edit",
    "multiedit",
    "patch",
    "apply_patch",
)
REQUIRED_DENIED_TOOLS = (
    "bash",
    "batch",
    "browser",
    "communicate",
    "launch",
    "memory",
    "open",
    "selfdev",
    "swarm",
    "webfetch",
    "websearch",
)
JCODE_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "PATH",
    "TZ",
)
JCODE_FORCED_ENV = {
    "DO_NOT_TRACK": "1",
    "JCODE_ALLOW_COMMIT": "0",
    "JCODE_ALLOW_DEPLOY": "0",
    "JCODE_ALLOW_PUSH": "0",
    "JCODE_AUTO_UPDATE_ENABLED": "0",
    "JCODE_BROWSER_ENABLED": "0",
    "JCODE_DISABLE_BASE_TOOLS": "1",
    "JCODE_MEMORY_ENABLED": "0",
    "JCODE_NETWORK_ENABLED": "0",
    "JCODE_NO_TELEMETRY": "1",
    "JCODE_PERSIST_MEMORY_INJECTIONS": "0",
    "JCODE_RUN_AUTO_POKE": "0",
    "JCODE_RUN_AUTO_POKE_MAX_TURNS": "1",
    "JCODE_RUN_MCP": "0",
    "JCODE_RUN_MCP_WAIT_MS": "0",
    "JCODE_SESSION_RESUME_ENABLED": "0",
    "JCODE_SWARM_ENABLED": "0",
    "JCODE_TELEMETRY_ENABLED": "0",
}
JCODE_FEATURE_FLAG_DEFAULTS = {
    "JCODE_ALLOW_COMMIT": False,
    "JCODE_ALLOW_DEPLOY": False,
    "JCODE_ALLOW_PUSH": False,
    "JCODE_AUTO_UPDATE_ENABLED": False,
    "JCODE_BROWSER_ENABLED": False,
    "JCODE_MEMORY_ENABLED": False,
    "JCODE_NETWORK_ENABLED": False,
    "JCODE_SESSION_RESUME_ENABLED": False,
    "JCODE_SWARM_ENABLED": False,
    "JCODE_TELEMETRY_ENABLED": False,
}
JCODE_EXECUTION_RESULT_FIELDS = (
    "task_id",
    "correlation_id",
    "adapter_version",
    "jcode_commit",
    "provider_profile",
    "actual_model",
    "start_time",
    "end_time",
    "termination_reason",
    "process_exit_code",
    "event_log",
    "transcript",
    "model_requests",
    "model_responses",
    "tool_calls",
    "tool_results",
    "commands_attempted",
    "commands_denied",
    "files_read",
    "files_written",
    "files_created",
    "files_deleted",
    "claimed_outcome",
    "stdout",
    "stderr",
    "usage",
    "retry_count",
    "timeout_state",
    "cancellation_state",
    "evidence_hashes",
)

CommandResolver = Callable[[str], str | None]
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class JCodeEnvelopeError(ValueError):
    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class JCodeExecutionEnvelope:
    workspace: Path
    task_id: str
    correlation_id: str
    repository_id: str
    base_commit: str
    prompt_file: Path
    immutable_prompt_sha256: str
    context_packet_file: Path
    context_packet_sha256: str
    evidence_output_path: Path
    jcode_home: Path
    provider_profile: str
    model: str
    model_parameters: Mapping[str, int | float]
    inference_endpoint: str
    allowed_files: tuple[str, ...]
    protected_files: tuple[str, ...] = field(default_factory=tuple)
    allowed_tools: tuple[str, ...] = DEFAULT_ALLOWED_TOOLS
    denied_tools: tuple[str, ...] = REQUIRED_DENIED_TOOLS
    command_policy: str = "no_shell"
    network_policy: str = "inference_only_external_guard_required"
    environment_allowlist: tuple[str, ...] = JCODE_ENV_ALLOWLIST
    turn_budget: int = 4
    token_budget: int = 32_768
    timeout_seconds: int = DEFAULT_JCODE_TIMEOUT_SECONDS
    max_output_bytes: int = DEFAULT_JCODE_MAX_OUTPUT_BYTES
    approval_capability: bool = False
    fresh_session_required: bool = True
    feature_flags: Mapping[str, bool] = field(
        default_factory=lambda: dict(JCODE_FEATURE_FLAG_DEFAULTS)
    )
    binary: str = "jcode"


def jcode_executor_enabled(environ: Mapping[str, str] | None = None) -> bool:
    raw = (environ or os.environ).get(JCODE_EXECUTOR_ENABLED_ENV, "0")
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def build_jcode_cli_status(
    *,
    binary_name: str = "jcode",
    source_checkout: Path | None = None,
    command_resolver: CommandResolver | None = None,
    command_runner: CommandRunner | None = None,
    environ: Mapping[str, str] | None = None,
    timeout_seconds: float = 5.0,
    authorized_binary_path: str | Path | None = None,
) -> dict[str, Any]:
    resolver = command_resolver or shutil.which
    runner = command_runner or subprocess.run
    configured = Path(authorized_binary_path or JCODE_BINARY_PATH)
    binary_path: str | None = None
    binary_attestation_error: str | None = None
    try:
        mode = configured.lstat().st_mode
        if stat.S_ISLNK(mode): binary_attestation_error = 'jcode_binary_symlink_denied'
        elif not stat.S_ISREG(mode): binary_attestation_error = 'jcode_binary_not_regular'
        elif not (mode & stat.S_IXUSR): binary_attestation_error = 'jcode_binary_not_executable'
        elif hashlib.sha256(configured.read_bytes()).hexdigest() != JCODE_BINARY_SHA256: binary_attestation_error = 'jcode_binary_hash_mismatch'
        else: binary_path = str(configured)
    except OSError:
        binary_attestation_error = 'jcode_binary_not_found'
    diagnostic_path = resolver(binary_name)
    enabled = jcode_executor_enabled(environ)
    status: dict[str, Any] = {
        "schema_version": JCODE_QUALIFICATION_SCHEMA_VERSION,
        "tool": "jcode_cli",
        "executor_id": JCODE_EXECUTOR_ID,
        "status": "config_blocked",
        "reason": binary_attestation_error or ("jcode_source_not_verified" if binary_path else "jcode_binary_not_found"),
        "installed": bool(binary_path),
        "binary": binary_name,
        "binary_path": binary_path,
        "configured_binary_path": str(configured),
        "path_fallback_diagnostic": diagnostic_path,
        "binary_sha256_expected": JCODE_BINARY_SHA256,
        "binary_sha256_match": binary_attestation_error is None,
        "version": None,
        "raw_version": None,
        "expected_version": JCODE_PINNED_RELEASE.removeprefix("v"),
        "binary_version_match": False,
        "source_checkout": str(source_checkout.resolve()) if source_checkout else None,
        "source_commit": None,
        "expected_source_commit": JCODE_PINNED_COMMIT,
        "pinned_source_match": False,
        "binary_and_source_match": False,
        "feature_flag": JCODE_EXECUTOR_ENABLED_ENV,
        "feature_flag_enabled": enabled,
        "would_run_task": False,
        "can_run_live_task": False,
        "authority": _no_authority_payload(),
        "safe_features": {
            "headless_run": True,
            "ndjson": True,
            "explicit_tool_allowlist": True,
            "fresh_jcode_home": True,
            "mcp_forced_off": True,
            "auto_poke_forced_off": True,
            "telemetry_forced_off": True,
        },
        "qualification_blockers": [
            "campaign_2_operator_acceptance_pending",
            "inference_only_egress_guard_not_implemented",
            "general_tool_path_not_bound_to_jcode_safety_classifier",
            "stable_execution_result_api_not_available",
            "model_parameter_and_budget_enforcement_not_implemented",
            "pinned_binary_hash_not_verified",
        ],
    }
    if not binary_path:
        return status

    try:
        completed = runner(
            [binary_path, "--version"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        status["reason"] = "jcode_version_probe_failed"
        status["version_error"] = str(error)
        return status

    raw_version = "\n".join(
        part.strip()
        for part in (completed.stdout or "", completed.stderr or "")
        if part.strip()
    ).strip()
    status["raw_version"] = raw_version or None
    status["version"] = _parse_version(raw_version)
    status["binary_version_match"] = (
        status["version"] == JCODE_VERSION
    )
    status["version_returncode"] = completed.returncode
    if completed.returncode != 0 or not raw_version:
        status["reason"] = "jcode_version_probe_nonzero_or_empty"
        return status

    if source_checkout is not None:
        try:
            source = runner(
                ["git", "-C", str(source_checkout.resolve()), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            status["reason"] = "jcode_source_probe_failed"
            status["source_error"] = str(error)
            return status
        source_commit = (source.stdout or "").strip()
        status["source_commit"] = source_commit or None
        status["pinned_source_match"] = (
            source.returncode == 0 and source_commit == JCODE_PINNED_COMMIT
        )

    status["binary_and_source_match"] = bool(
        status["binary_version_match"] and status["pinned_source_match"]
    )
    status["reason"] = (
        "jcode_qualification_live_execution_not_enabled"
        if status["binary_and_source_match"]
        else "jcode_binary_or_source_pin_mismatch_or_unverified"
    )
    status["status"] = "detected_qualification_blocked"
    return status


def validate_jcode_envelope(envelope: JCodeExecutionEnvelope) -> dict[str, Any]:
    blocked: list[dict[str, str]] = []
    workspace = envelope.workspace.resolve()
    jcode_home = envelope.jcode_home.resolve()
    prompt_file = envelope.prompt_file.resolve()
    context_packet_file = envelope.context_packet_file.resolve()
    evidence_output = envelope.evidence_output_path.resolve()

    _require_text(envelope.task_id, "missing_task_id", blocked)
    _require_text(envelope.correlation_id, "missing_correlation_id", blocked)
    _require_text(envelope.repository_id, "missing_repository_id", blocked)
    for label, value in (
        ("task_id", envelope.task_id),
        ("correlation_id", envelope.correlation_id),
        ("repository_id", envelope.repository_id),
    ):
        if value and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}", value):
            blocked.append({"path": "*", "reason_code": f"{label}_invalid"})
    if not workspace.is_dir():
        blocked.append({"path": str(workspace), "reason_code": "workspace_missing"})
    if not _valid_sha(envelope.base_commit, lengths=(40, 64)):
        blocked.append({"path": "*", "reason_code": "base_commit_invalid"})
    if not _valid_sha(envelope.immutable_prompt_sha256):
        blocked.append({"path": str(prompt_file), "reason_code": "prompt_hash_invalid"})
    if not _valid_sha(envelope.context_packet_sha256):
        blocked.append({"path": "*", "reason_code": "context_packet_hash_invalid"})
    if (
        workspace == jcode_home
        or _is_relative_to(jcode_home, workspace)
        or _is_relative_to(workspace, jcode_home)
    ):
        blocked.append({"path": str(jcode_home), "reason_code": "jcode_home_not_isolated"})
    if not _is_relative_to(prompt_file, jcode_home / "input"):
        blocked.append({"path": str(prompt_file), "reason_code": "prompt_file_outside_input_root"})
    if not _is_relative_to(context_packet_file, jcode_home / "input"):
        blocked.append(
            {
                "path": str(context_packet_file),
                "reason_code": "context_packet_outside_input_root",
            }
        )
    if not _is_relative_to(evidence_output, jcode_home / "evidence"):
        blocked.append(
            {"path": str(evidence_output), "reason_code": "evidence_output_outside_evidence_root"}
        )
    if evidence_output.exists():
        blocked.append(
            {"path": str(evidence_output), "reason_code": "evidence_output_not_fresh"}
        )
    if prompt_file.is_file():
        actual_hash = hashlib.sha256(prompt_file.read_bytes()).hexdigest()
        if actual_hash != _bare_sha(envelope.immutable_prompt_sha256):
            blocked.append({"path": str(prompt_file), "reason_code": "prompt_hash_mismatch"})
    else:
        blocked.append({"path": str(prompt_file), "reason_code": "prompt_file_missing"})
    if context_packet_file.is_file():
        actual_context_hash = hashlib.sha256(context_packet_file.read_bytes()).hexdigest()
        if actual_context_hash != _bare_sha(envelope.context_packet_sha256):
            blocked.append(
                {
                    "path": str(context_packet_file),
                    "reason_code": "context_packet_hash_mismatch",
                }
            )
    else:
        blocked.append(
            {
                "path": str(context_packet_file),
                "reason_code": "context_packet_file_missing",
            }
        )

    contamination_markers = (
        jcode_home / "mcp.json",
        jcode_home / "AGENTS.md",
        jcode_home / "config.toml",
        jcode_home / "memory",
        jcode_home / "prompt-overlay.md",
        jcode_home / "runtime",
        jcode_home / "sessions",
        workspace / ".jcode" / "prompt-overlay.md",
    )
    for marker in contamination_markers:
        if marker.exists():
            blocked.append({"path": str(marker), "reason_code": "jcode_state_contamination"})
    allowed_input_files = {prompt_file, context_packet_file}
    if jcode_home.is_dir():
        for candidate in jcode_home.rglob("*"):
            if candidate.is_symlink():
                blocked.append(
                    {
                        "path": str(candidate),
                        "reason_code": "jcode_state_symlink_forbidden",
                    }
                )
            elif candidate.is_file() and candidate.resolve() not in allowed_input_files:
                blocked.append(
                    {
                        "path": str(candidate),
                        "reason_code": "jcode_state_unexpected_file",
                    }
                )

    for label, paths in (
        ("allowed_file", envelope.allowed_files),
        ("protected_file", envelope.protected_files),
    ):
        for path in paths:
            reason = _repo_path_block_reason(path, workspace=workspace)
            if reason:
                blocked.append({"path": path, "reason_code": f"{label}_{reason}"})
    for allowed_path in envelope.allowed_files:
        for protected_path in envelope.protected_files:
            if _repo_paths_overlap(allowed_path, protected_path):
                blocked.append(
                    {
                        "path": allowed_path,
                        "reason_code": "allowed_protected_path_overlap",
                    }
                )
    if not envelope.allowed_files:
        blocked.append({"path": "*", "reason_code": "allowed_files_missing"})

    allowed_tools = set(envelope.allowed_tools)
    denied_tools = set(envelope.denied_tools)
    if not allowed_tools or not allowed_tools.issubset(DEFAULT_ALLOWED_TOOLS):
        blocked.append({"path": "*", "reason_code": "unsafe_or_unknown_allowed_tool"})
    if allowed_tools.intersection(denied_tools):
        blocked.append({"path": "*", "reason_code": "allowed_denied_tool_overlap"})
    if not set(REQUIRED_DENIED_TOOLS).issubset(denied_tools):
        blocked.append({"path": "*", "reason_code": "required_denied_tool_missing"})
    if envelope.command_policy != "no_shell":
        blocked.append({"path": "*", "reason_code": "unsafe_command_policy"})
    if envelope.network_policy != "inference_only_external_guard_required":
        blocked.append({"path": "*", "reason_code": "unsafe_network_policy"})
    if not _safe_loopback_endpoint(envelope.inference_endpoint):
        blocked.append({"path": "*", "reason_code": "inference_endpoint_not_loopback"})
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,62}", envelope.provider_profile):
        blocked.append({"path": "*", "reason_code": "provider_profile_invalid"})
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}", envelope.model):
        blocked.append({"path": "*", "reason_code": "model_invalid"})
    binary_name = Path(envelope.binary).name
    if binary_name not in {"jcode", "jcode.exe"}:
        blocked.append({"path": "*", "reason_code": "jcode_binary_identity_invalid"})
    _validate_model_parameters(envelope.model_parameters, blocked)
    if not 1 <= envelope.turn_budget <= 8:
        blocked.append({"path": "*", "reason_code": "turn_budget_invalid"})
    if not 1 <= envelope.token_budget <= 200_000:
        blocked.append({"path": "*", "reason_code": "token_budget_invalid"})
    if not 1 <= envelope.timeout_seconds <= 1800:
        blocked.append({"path": "*", "reason_code": "timeout_invalid"})
    if not 1 <= envelope.max_output_bytes <= 5_000_000:
        blocked.append({"path": "*", "reason_code": "max_output_bytes_invalid"})
    if envelope.approval_capability:
        blocked.append({"path": "*", "reason_code": "jcode_approval_authority_forbidden"})
    if not envelope.fresh_session_required:
        blocked.append({"path": "*", "reason_code": "fresh_session_required"})
    missing_feature_flags = sorted(
        set(JCODE_FEATURE_FLAG_DEFAULTS).difference(envelope.feature_flags)
    )
    for name in missing_feature_flags:
        blocked.append({"path": "*", "reason_code": f"feature_flag_missing:{name}"})
    for name in JCODE_FEATURE_FLAG_DEFAULTS:
        if envelope.feature_flags.get(name) is not False:
            blocked.append({"path": "*", "reason_code": f"unsafe_feature_enabled:{name}"})
    unknown_feature_flags = sorted(
        set(envelope.feature_flags).difference(JCODE_FEATURE_FLAG_DEFAULTS)
    )
    for name in unknown_feature_flags:
        blocked.append({"path": "*", "reason_code": f"feature_flag_unknown:{name}"})
    if tuple(envelope.environment_allowlist) != JCODE_ENV_ALLOWLIST:
        blocked.append({"path": "*", "reason_code": "environment_allowlist_drift"})

    deduped = _dedupe_blocked_reasons(blocked)
    return {
        "ok": not deduped,
        "blocked_reasons": deduped,
        "live_ready": False,
        "live_blockers": [
            "feature_flag_disabled_by_default",
            "inference_only_egress_guard_not_implemented",
            "campaign_2_operator_acceptance_pending",
            "model_parameter_and_budget_enforcement_not_implemented",
            "pinned_binary_hash_not_verified",
        ],
        "authority": _no_authority_payload(),
        "independent_proxy_checks_required": [
            "git_diff",
            "protected_path_policy",
            "tests",
            "reviewer",
            "verifier",
            "anti_cheat",
            "terminal_truth",
        ],
    }


def build_jcode_command(envelope: JCodeExecutionEnvelope) -> list[str]:
    validation = validate_jcode_envelope(envelope)
    if not validation["ok"]:
        first = validation["blocked_reasons"][0]
        raise JCodeEnvelopeError(
            "JCode qualification envelope is not safe.",
            str(first["reason_code"]),
        )
    prompt_path = envelope.prompt_file.resolve()
    message = (
        "Read the immutable SpiritOS executor packet at "
        f"{prompt_path}. Verify SHA-256 {_bare_sha(envelope.immutable_prompt_sha256)} "
        "before acting. Read the immutable context packet at "
        f"{envelope.context_packet_file.resolve()} and verify SHA-256 "
        f"{_bare_sha(envelope.context_packet_sha256)}. Stay inside the declared "
        "file and tool scope. Do not "
        "commit, push, deploy, resume a session, use memory, use MCP, or claim "
        "final success; Source Proxy independently decides the outcome."
    )
    command = [
        envelope.binary,
        "--cwd",
        str(envelope.workspace.resolve()),
        "--no-update",
        "--no-selfdev",
        "--quiet",
        "--trace",
        "--provider-profile",
        envelope.provider_profile,
        "--model",
        envelope.model,
        "--disable-base-tools",
        "--tools",
        ",".join(envelope.allowed_tools),
        "--disabled-tools",
        ",".join(envelope.denied_tools),
        "run",
        "--ndjson",
        message,
    ]
    argv_validation = validate_jcode_cli_argv(command)
    if not argv_validation["allowed"]:
        raise JCodeEnvelopeError(
            "JCode command includes an unsafe option.",
            "jcode_command_policy_violation",
        )
    return command


def validate_jcode_cli_argv(argv: Sequence[str]) -> dict[str, Any]:
    values = [str(item).strip() for item in argv]
    lowered = [item.lower() for item in values]
    blocked: list[str] = []
    required = {
        "--cwd",
        "--no-update",
        "--no-selfdev",
        "--provider-profile",
        "--model",
        "--disable-base-tools",
        "--tools",
        "--disabled-tools",
        "--ndjson",
    }
    missing = sorted(required.difference(lowered))
    blocked.extend(f"missing:{item}" for item in missing)
    if "run" not in lowered:
        blocked.append("missing:run")
    for flag in (
        "--auto-update",
        "--debug-socket",
        "--fresh-spawn",
        "--onboarding-sim",
        "--provider",
        "--remote-working-dir",
        "--resume",
        "--socket",
        "--spawn-hotkey",
        "--tool-profile",
    ):
        if any(item == flag or item.startswith(f"{flag}=") for item in lowered):
            blocked.append(flag)
    command_prefix = lowered[
        : lowered.index("run") if "run" in lowered else len(lowered)
    ]
    if any(item in {"serve", "connect", "acp", "update"} for item in command_prefix):
        blocked.append("non_run_subcommand")
    for option in ("--cwd", "--provider-profile", "--model"):
        value = _option_value(values, option)
        if value is None or not value or value.startswith("-"):
            blocked.append(f"invalid:{option}")
    tools_value = _option_value(values, "--tools")
    if tools_value is None:
        blocked.append("missing:--tools")
    else:
        tools = {item.strip() for item in tools_value.split(",") if item.strip()}
        if "*" in tools or "all" in {item.lower() for item in tools}:
            blocked.append("unrestricted_tools")
        if not tools.issubset(DEFAULT_ALLOWED_TOOLS):
            blocked.append("unsafe_tool_requested")
    denied_value = _option_value(values, "--disabled-tools")
    if denied_value is None:
        blocked.append("missing:--disabled-tools")
    else:
        denied = {item.strip() for item in denied_value.split(",") if item.strip()}
        if not set(REQUIRED_DENIED_TOOLS).issubset(denied):
            blocked.append("required_denied_tool_missing")
    return {
        "allowed": not blocked,
        "blocked_reasons": sorted(set(blocked)),
        "required_flags": sorted(required),
        "allowed_tools": list(DEFAULT_ALLOWED_TOOLS),
        "denied_tools": list(REQUIRED_DENIED_TOOLS),
    }


def jcode_subprocess_env(
    source_env: Mapping[str, str],
    envelope: JCodeExecutionEnvelope,
) -> dict[str, str]:
    validation = validate_jcode_envelope(envelope)
    if not validation["ok"]:
        first = validation["blocked_reasons"][0]
        raise JCodeEnvelopeError(
            "JCode subprocess environment cannot be built from an unsafe envelope.",
            str(first["reason_code"]),
        )
    env = {
        key.upper(): value
        for key, value in source_env.items()
        if key.upper() in JCODE_ENV_ALLOWLIST
    }
    home = str(envelope.jcode_home.resolve())
    env.update(JCODE_FORCED_ENV)
    env.update(
        {
            "HOME": home,
            "JCODE_DISABLED_TOOLS": ",".join(envelope.denied_tools),
            "JCODE_HOME": home,
            "JCODE_RUNTIME_DIR": str((envelope.jcode_home / "runtime").resolve()),
        }
    )
    return env


def render_jcode_provider_config(envelope: JCodeExecutionEnvelope) -> str:
    validation = validate_jcode_envelope(envelope)
    if not validation["ok"]:
        first = validation["blocked_reasons"][0]
        raise JCodeEnvelopeError(
            "JCode provider profile cannot be rendered from an unsafe envelope.",
            str(first["reason_code"]),
        )
    profile = envelope.provider_profile
    endpoint = envelope.inference_endpoint.replace("\\", "\\\\").replace('"', '\\"')
    model = envelope.model.replace("\\", "\\\\").replace('"', '\\"')
    return (
        "[provider]\n"
        f'default_provider = "{profile}"\n'
        f'default_model = "{model}"\n\n'
        f"[providers.{profile}]\n"
        'type = "openai-compatible"\n'
        f'base_url = "{endpoint}"\n'
        'auth = "none"\n'
        f'default_model = "{model}"\n'
        "requires_api_key = false\n"
        "provider_routing = false\n"
        "model_catalog = false\n\n"
        f"[[providers.{profile}.models]]\n"
        f'id = "{model}"\n'
    )


def build_jcode_qualification_preview(
    envelope: JCodeExecutionEnvelope,
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    validation = validate_jcode_envelope(envelope)
    command = build_jcode_command(envelope) if validation["ok"] else []
    enabled = jcode_executor_enabled(environ)
    return {
        "schema_version": JCODE_QUALIFICATION_SCHEMA_VERSION,
        "request_schema_version": JCODE_EXECUTION_REQUEST_SCHEMA_VERSION,
        "result_schema_version": JCODE_EXECUTION_RESULT_SCHEMA_VERSION,
        "adapter_version": JCODE_ADAPTER_VERSION,
        "executor_id": JCODE_EXECUTOR_ID,
        "status": "config_blocked" if validation["ok"] else "blocked",
        "reason_code": (
            "jcode_qualification_live_execution_not_enabled"
            if enabled
            else "jcode_executor_disabled"
        )
        if validation["ok"]
        else "jcode_execution_envelope_invalid",
        "feature_flag_enabled": enabled,
        "envelope_validation": validation,
        "command_preview": command,
        "provider_config_preview": render_jcode_provider_config(envelope)
        if validation["ok"]
        else "",
        "model_parameters": dict(envelope.model_parameters),
        "would_run_task": False,
        "authority": _no_authority_payload(),
        "result_contract_fields": list(JCODE_EXECUTION_RESULT_FIELDS),
        "claim_ceiling": "qualification_preview_only_no_runtime_integration",
    }


def _safe_loopback_endpoint(value: str) -> bool:
    parsed = urlparse(value)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.hostname in {"127.0.0.1", "::1"}
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
    )


def _validate_model_parameters(
    parameters: Mapping[str, int | float],
    blocked: list[dict[str, str]],
) -> None:
    allowed = {"max_tokens", "seed", "temperature", "top_k", "top_p"}
    unknown = sorted(set(parameters).difference(allowed))
    for name in unknown:
        blocked.append({"path": "*", "reason_code": f"model_parameter_unknown:{name}"})
    limits = {
        "max_tokens": (1, 200_000),
        "seed": (0, 2_147_483_647),
        "temperature": (0, 2),
        "top_k": (0, 200),
        "top_p": (0, 1),
    }
    for name, value in parameters.items():
        if name not in limits:
            continue
        minimum, maximum = limits[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            blocked.append(
                {"path": "*", "reason_code": f"model_parameter_invalid:{name}"}
            )
        elif not minimum <= value <= maximum:
            blocked.append(
                {
                    "path": "*",
                    "reason_code": f"model_parameter_out_of_range:{name}",
                }
            )


def _repo_path_block_reason(path: str, *, workspace: Path) -> str | None:
    normalized = str(path or "").replace("\\", "/").strip()
    if normalized in {"", ".", "./"}:
        return "broad_or_empty_path_not_allowed"
    if any(character in normalized for character in "*?[]"):
        return "wildcard_path_not_allowed"
    if any(ord(character) < 32 for character in normalized):
        return "control_character_not_allowed"
    if has_percent_encoded_path_syntax(path):
        return "encoded_path_not_allowed"
    if path_escapes_workspace(path, workspace_root=workspace):
        return "path_escape"
    if is_secret_shaped_path(path):
        return "protected_path"
    return None


def _repo_paths_overlap(left: str, right: str) -> bool:
    left_parts = tuple(
        part for part in str(left).replace("\\", "/").strip("/").split("/") if part
    )
    right_parts = tuple(
        part for part in str(right).replace("\\", "/").strip("/").split("/") if part
    )
    if not left_parts or not right_parts:
        return False
    shortest = min(len(left_parts), len(right_parts))
    return left_parts[:shortest] == right_parts[:shortest]


def _require_text(value: str, reason_code: str, blocked: list[dict[str, str]]) -> None:
    if not str(value or "").strip():
        blocked.append({"path": "*", "reason_code": reason_code})


def _valid_sha(value: str, *, lengths: tuple[int, ...] = (64,)) -> bool:
    bare = _bare_sha(value)
    return len(bare) in lengths and all(character in "0123456789abcdef" for character in bare)


def _bare_sha(value: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized.removeprefix("sha256:")


def _parse_version(raw: str) -> str | None:
    match = re.search(r"(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)", raw or "")
    return match.group(1) if match else None


def _option_value(argv: Sequence[str], name: str) -> str | None:
    for index, item in enumerate(argv):
        if item == name and index + 1 < len(argv):
            return str(argv[index + 1])
        if item.startswith(f"{name}="):
            return item.split("=", 1)[1]
    return None


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _dedupe_blocked_reasons(blocked: list[dict[str, str]]) -> list[dict[str, str]]:
    return [dict(item) for item in dict.fromkeys(tuple(item.items()) for item in blocked)]


def _no_authority_payload() -> dict[str, bool]:
    return {
        "approval_authority": False,
        "apply_authority": False,
        "commit_authority": False,
        "deployment_authority": False,
        "final_outcome_authority": False,
        "push_authority": False,
        "review_authority": False,
        "verification_authority": False,
    }
