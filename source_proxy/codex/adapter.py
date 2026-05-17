from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from typing import Any

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

CommandResolver = Callable[[str], str | None]
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


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
