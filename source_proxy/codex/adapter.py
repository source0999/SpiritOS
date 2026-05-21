from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from source_proxy.safety.paths import (
    has_percent_encoded_path_syntax,
    is_secret_shaped_path,
    path_escapes_workspace,
)

SAFE_CODEX_SANDBOXES = ("read-only", "workspace-write")
BLOCKED_CODEX_SANDBOXES = ("danger-full-access",)
BLOCKED_CODEX_FLAGS = (
    "--dangerously-bypass-approvals-and-sandbox",
    "--yolo",
)
EXPECTED_CODEX_FEATURES = {
    "exec": True,
    "json_events": True,
    "output_last_message": True,
    "output_schema": True,
    "profile": True,
    "sandbox_read_only": True,
    "sandbox_workspace_write": True,
}
DEFAULT_CODEX_TIMEOUT_SECONDS = 300
DEFAULT_CODEX_MAX_OUTPUT_BYTES = 200_000
CODEX_ENV_ALLOWLIST = (
    "HOME",
    "PATH",
    "SHELL",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "USER",
    "USERNAME",
)
CODEX_COMMAND_ALLOWLIST = (
    "codex exec",
)

CommandResolver = Callable[[str], str | None]
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class CodexEnvelopeError(ValueError):
    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class CodexExecutionEnvelope:
    workspace: Path
    task_id: str
    prompt_file: Path
    output_file: Path
    output_dir: Path
    allowed_files: tuple[str, ...] = field(default_factory=tuple)
    blocked_files: tuple[str, ...] = field(default_factory=tuple)
    sandbox: str = "read-only"
    timeout_seconds: int = DEFAULT_CODEX_TIMEOUT_SECONDS
    model_mode: str = "default"
    max_output_bytes: int = DEFAULT_CODEX_MAX_OUTPUT_BYTES
    binary: str = "codex"


def build_codex_cli_status(
    *,
    binary_name: str = "codex",
    command_resolver: CommandResolver | None = None,
    command_runner: CommandRunner | None = None,
    timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    resolver = command_resolver or shutil.which
    runner = command_runner or subprocess.run
    binary_path = resolver(binary_name)

    status: dict[str, Any] = {
        "tool": "codex_cli",
        "status": "config_blocked",
        "installed": False,
        "binary": binary_name,
        "binary_path": binary_path,
        "version": None,
        "raw_version": None,
        "auth_status": "not_probed",
        "safe_features": EXPECTED_CODEX_FEATURES.copy(),
        "safe_sandboxes": list(SAFE_CODEX_SANDBOXES),
        "blocked_sandboxes": list(BLOCKED_CODEX_SANDBOXES),
        "blocked_flags": list(BLOCKED_CODEX_FLAGS),
        "can_run_live_task": False,
        "would_run_task": False,
        "approval_authority": False,
        "apply_authority": False,
        "commit_authority": False,
        "push_authority": False,
        "notes": [
            "Capability probe only; no Codex task is executed.",
            "Missing Codex CLI is config_blocked, not a Source Proxy failure.",
        ],
    }
    if not binary_path:
        status["reason"] = "codex_binary_not_found"
        return status

    status["installed"] = True
    status["status"] = "detected"
    try:
        completed = _run_version_probe(
            runner=runner,
            command=[binary_path, "--version"],
            fallback_command=[binary_name, "--version"],
            timeout_seconds=timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        status["status"] = "detected_version_unknown"
        status["reason"] = "version_probe_failed"
        status["version_error"] = str(exc)
        return status

    raw_version = "\n".join(
        part.strip()
        for part in (completed.stdout or "", completed.stderr or "")
        if part.strip()
    ).strip()
    status["raw_version"] = raw_version or None
    status["version"] = _parse_codex_version(raw_version)
    status["version_returncode"] = completed.returncode
    if completed.returncode != 0:
        status["status"] = "detected_version_unknown"
        status["reason"] = "version_probe_nonzero"
    elif not raw_version:
        status["status"] = "detected_version_unknown"
        status["reason"] = "version_probe_empty"
    return status


def build_codex_command(envelope: CodexExecutionEnvelope) -> list[str]:
    validation = validate_codex_envelope(envelope)
    if not validation["ok"]:
        reasons = validation["blocked_reasons"]
        reason_code = str(reasons[0]["reason_code"] if reasons else "codex_envelope_invalid")
        raise CodexEnvelopeError("Codex execution envelope is not safe.", reason_code)

    command = [
        envelope.binary,
        "exec",
        "--cd",
        str(envelope.workspace.resolve()),
        "--json",
        "--output-last-message",
        str(envelope.output_file.resolve()),
        "--sandbox",
        envelope.sandbox,
    ]
    if envelope.model_mode and envelope.model_mode != "default":
        command.extend(["--profile", envelope.model_mode])
    command.append(str(envelope.prompt_file.resolve()))

    argv_validation = validate_codex_cli_argv(command)
    if not argv_validation["allowed"]:
        raise CodexEnvelopeError("Codex command includes blocked flags.", "codex_dangerous_flag")
    return command


def validate_codex_envelope(envelope: CodexExecutionEnvelope) -> dict[str, Any]:
    blocked: list[dict[str, str]] = []
    workspace = envelope.workspace.resolve()
    output_dir = envelope.output_dir.resolve()

    if not envelope.task_id.strip():
        blocked.append({"path": "*", "reason_code": "missing_task_id"})
    if envelope.sandbox not in SAFE_CODEX_SANDBOXES:
        blocked.append({"path": "*", "reason_code": "unsafe_sandbox"})
    if envelope.timeout_seconds <= 0 or envelope.timeout_seconds > 3600:
        blocked.append({"path": "*", "reason_code": "unsafe_timeout"})
    if envelope.max_output_bytes <= 0 or envelope.max_output_bytes > 5_000_000:
        blocked.append({"path": "*", "reason_code": "unsafe_max_output_size"})

    for label, path in (
        ("workspace", workspace),
        ("prompt_file", envelope.prompt_file.resolve()),
        ("output_file", envelope.output_file.resolve()),
        ("output_dir", output_dir),
    ):
        if _secret_path_object(path):
            blocked.append({"path": str(path), "reason_code": f"{label}_protected_path"})

    for label, path in (
        ("prompt_file", envelope.prompt_file.resolve()),
        ("output_file", envelope.output_file.resolve()),
    ):
        if not (_is_relative_to(path, workspace) or _is_relative_to(path, output_dir)):
            blocked.append({"path": str(path), "reason_code": f"{label}_outside_workspace_or_output_dir"})

    for path in envelope.allowed_files:
        reason = _repo_path_block_reason(path, workspace=workspace)
        if reason:
            blocked.append({"path": path, "reason_code": f"allowed_file_{reason}"})
    for path in envelope.blocked_files:
        reason = _repo_path_block_reason(path, workspace=workspace)
        if reason:
            blocked.append({"path": path, "reason_code": f"blocked_file_{reason}"})

    return {
        "ok": not blocked,
        "blocked_reasons": _dedupe_blocked_reasons(blocked),
        "command_allowlist": list(CODEX_COMMAND_ALLOWLIST),
        "environment_allowlist": list(CODEX_ENV_ALLOWLIST),
        "dangerous_flag_denylist": list(BLOCKED_CODEX_FLAGS),
        "safe_sandboxes": list(SAFE_CODEX_SANDBOXES),
        "blocked_sandboxes": list(BLOCKED_CODEX_SANDBOXES),
        "limits": {
            "timeout_seconds": envelope.timeout_seconds,
            "max_output_bytes": envelope.max_output_bytes,
        },
        "would_run_task": False,
    }


def codex_subprocess_env(source_env: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in source_env.items() if key.upper() in CODEX_ENV_ALLOWLIST}


def validate_codex_cli_argv(argv: Sequence[str]) -> dict[str, Any]:
    blocked: list[str] = []
    normalized = [str(part).strip() for part in argv]
    lowered = [part.lower() for part in normalized]

    for flag in BLOCKED_CODEX_FLAGS:
        if flag in lowered:
            blocked.append(flag)

    for index, part in enumerate(lowered):
        sandbox_value: str | None = None
        if part == "--sandbox" and index + 1 < len(lowered):
            sandbox_value = lowered[index + 1]
        elif part.startswith("--sandbox="):
            sandbox_value = part.split("=", 1)[1]
        if sandbox_value in BLOCKED_CODEX_SANDBOXES:
            blocked.append(f"--sandbox {sandbox_value}")

    return {
        "allowed": not blocked,
        "blocked_reasons": sorted(set(blocked)),
        "blocked_flags": list(BLOCKED_CODEX_FLAGS),
        "blocked_sandboxes": list(BLOCKED_CODEX_SANDBOXES),
    }


def _parse_codex_version(raw_version: str) -> str | None:
    match = re.search(r"(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)", raw_version or "")
    if match:
        return match.group(1)
    return None


def _run_version_probe(
    *,
    runner: CommandRunner,
    command: list[str],
    fallback_command: list[str],
    timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    try:
        return runner(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except OSError:
        if command == fallback_command:
            raise
        return runner(
            fallback_command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )


def _repo_path_block_reason(path: str, *, workspace: Path) -> str | None:
    if has_percent_encoded_path_syntax(path):
        return "encoded_path_not_allowed"
    if path_escapes_workspace(path, workspace_root=workspace):
        return "path_escape"
    if is_secret_shaped_path(path):
        return "protected_path"
    return None


def _secret_path_object(path: Path) -> bool:
    return any(is_secret_shaped_path(part) for part in path.parts)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _dedupe_blocked_reasons(blocked: list[dict[str, str]]) -> list[dict[str, str]]:
    return [dict(item) for item in dict.fromkeys(tuple(item.items()) for item in blocked)]
