from __future__ import annotations

import dataclasses
import subprocess
from pathlib import Path
from typing import Any

VERIFICATION_RUNNER_PHASE = "Plan 6 Phase 6.1: Verification And Command Runner"
MAX_TIMEOUT_SECONDS = 30
VERIFICATION_OUTPUT_SUMMARY_LIMIT = 400

BASE_ALLOWED_ARGV: tuple[tuple[str, ...], ...] = (
    ("git", "diff", "--check"),
)

PYTEST_ARGV_PREFIX: tuple[str, ...] = (".venv/bin/python", "-m", "pytest")
NPM_TEST_ARGV_PREFIX: tuple[str, ...] = ("npm", "test", "--")

SHELL_EXECUTABLES: tuple[str, ...] = (
    "bash",
    "sh",
    "zsh",
    "fish",
    "powershell",
    "pwsh",
    "cmd",
)
SHELL_METACHARS: tuple[str, ...] = (
    "|",
    ">",
    "<",
    "&&",
    "||",
    ";",
    "$(",
    "`",
)
DESTRUCTIVE_GIT_PREFIXES: tuple[tuple[str, ...], ...] = (
    ("git", "clean"),
    ("git", "reset"),
    ("git", "checkout"),
    ("git", "push"),
    ("git", "add"),
    ("git", "commit"),
    ("git", "branch"),
    ("git", "worktree"),
    ("git", "stash"),
)
PACKAGE_INSTALL_PREFIXES: tuple[tuple[str, ...], ...] = (
    ("npm", "install"),
    ("npm", "i"),
    ("pnpm", "install"),
    ("yarn", "add"),
    ("pip", "install"),
    ("uv", "pip", "install"),
)
MUTATING_COMMANDS: tuple[str, ...] = (
    "rm",
    "mv",
    "cp",
    "mkdir",
    "touch",
    "chmod",
    "chown",
    "curl",
    "wget",
)
PROVIDER_OR_NETWORK_COMMANDS: tuple[str, ...] = (
    "curl",
    "wget",
    "ssh",
    "scp",
    "rsync",
    "nc",
)
LONG_RUNNING_COMMANDS: tuple[str, ...] = (
    "sleep",
    "tail",
    "watch",
    "yes",
)


@dataclasses.dataclass(frozen=True)
class VerificationCommandSpec:
    command_id: str
    argv: tuple[str, ...]
    purpose: str
    exact_match_required: bool = True
    shell_allowed: bool = False
    execution_available: bool = False
    command_authority_granted: bool = False
    workflow_authority_granted: bool = False
    queue_authority_granted: bool = False
    git_mutation_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class VerificationCommandPreview:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    requested_argv: tuple[str, ...]
    matched_command_id: str | None
    execution_available: bool = False
    command_authority_granted: bool = False
    workflow_authority_granted: bool = False
    queue_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    preview_only: bool = True
    no_execution_guarantee: str = (
        "Plan 6 Phase 6.1 validates exact argv allowlist entries only. It does "
        "not run commands, open a shell, execute workflows, execute queues, "
        "stage files, commit, push, branch, create worktrees, stash, clean, "
        "reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class VerificationCommandResult:
    status: str
    executed: bool
    blocked: bool
    reasons: tuple[str, ...]
    argv: tuple[str, ...]
    matched_command_id: str | None
    cwd: str
    timeout_seconds: int
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False
    shell_allowed: bool = False
    command_authority_granted: bool = False
    workflow_authority_granted: bool = False
    queue_authority_granted: bool = False
    git_mutation_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_verification_result_receipt_summary(result: Any) -> dict[str, Any]:
    data = _result_to_dict(result)
    status = _string_value(data.get("status"))
    blocked = data.get("blocked") is True
    timed_out = data.get("timed_out") is True
    exit_code = data.get("exit_code")
    return {
        "command_id": _string_value(data.get("matched_command_id")),
        "argv": tuple(str(part) for part in data.get("argv", ()) if isinstance(part, str)),
        "exit_code": exit_code if isinstance(exit_code, int) else None,
        "stdout_summary": _summarize_output(data.get("stdout")),
        "stderr_summary": _summarize_output(data.get("stderr")),
        "timeout_seconds": data.get("timeout_seconds") if isinstance(data.get("timeout_seconds"), int) else None,
        "status": status,
        "passed": status == "passed" and not blocked and not timed_out,
        "blocked": blocked,
        "timed_out": timed_out,
        "reasons": tuple(str(reason) for reason in data.get("reasons", ()) if isinstance(reason, str)),
    }


def build_verification_runner_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 6/10",
        "phase": VERIFICATION_RUNNER_PHASE,
        "status": "verification-boundary-available",
        "argv_only": True,
        "shell_allowed": False,
        "execution_available": True,
        "command_authority_granted": False,
        "workflow_authority_granted": False,
        "queue_authority_granted": False,
        "git_mutation_authority_granted": False,
        "max_timeout_seconds": MAX_TIMEOUT_SECONDS,
        "output_summary_limit": VERIFICATION_OUTPUT_SUMMARY_LIMIT,
        "allowed_base_argv": BASE_ALLOWED_ARGV,
        "file_checks_available": True,
        "safe_next_action": "Execute only exact allowlisted verification argv.",
    }


def build_verification_command_allowlist(
    *,
    approved_test_files: list[str] | tuple[str, ...] = (),
    approved_file_checks: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
) -> tuple[VerificationCommandSpec, ...]:
    specs = [
        VerificationCommandSpec(
            command_id="git_diff_check",
            argv=BASE_ALLOWED_ARGV[0],
            purpose="Verify repository whitespace and conflict marker cleanliness.",
        ),
    ]
    for test_file in _normalize_test_files(approved_test_files):
        if test_file.endswith(".py"):
            specs.append(
                VerificationCommandSpec(
                    command_id=f"pytest:{test_file}",
                    argv=(*PYTEST_ARGV_PREFIX, test_file),
                    purpose="Run one exact approved Python test file.",
                )
            )
        if test_file.endswith((".ts", ".tsx")):
            specs.append(
                VerificationCommandSpec(
                    command_id=f"npm_test:{test_file}",
                    argv=(*NPM_TEST_ARGV_PREFIX, test_file),
                    purpose="Run one exact approved frontend test file through npm.",
                )
            )
    for file_check in _normalize_file_checks(approved_file_checks):
        path = file_check["path"]
        specs.append(
            VerificationCommandSpec(
                command_id=f"file_exists:{path}",
                argv=("test", "-f", path),
                purpose="Verify one exact approved file exists.",
            )
        )
        contains = file_check.get("contains")
        if contains:
            specs.append(
                VerificationCommandSpec(
                    command_id=f"grep_contains:{path}",
                    argv=("grep", "-nF", contains, path),
                    purpose="Verify one exact approved file contains expected text.",
                )
            )
    return tuple(specs)


def preview_verification_command(
    requested_argv: Any,
    *,
    approved_test_files: list[str] | tuple[str, ...] = (),
    approved_file_checks: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
) -> VerificationCommandPreview:
    normalized_argv = _normalize_argv(requested_argv)
    reasons: list[str] = []
    matched_command_id: str | None = None

    if not normalized_argv:
        reasons.append("malformed_argv")
    else:
        reasons.extend(_forbidden_argv_reasons(normalized_argv))

    for spec in build_verification_command_allowlist(
        approved_test_files=approved_test_files,
        approved_file_checks=approved_file_checks,
    ):
        if normalized_argv == spec.argv:
            matched_command_id = spec.command_id
            break

    if normalized_argv and matched_command_id is None:
        reasons.append("argv_not_exactly_allowed")

    accepted = not reasons
    return VerificationCommandPreview(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=tuple(_dedupe(reasons)),
        requested_argv=normalized_argv,
        matched_command_id=matched_command_id,
    )


def run_verification_command(
    requested_argv: Any,
    *,
    workspace_root: Path,
    approved_test_files: list[str] | tuple[str, ...] = (),
    approved_file_checks: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
    cwd_relative: str = ".",
    timeout_seconds: int = 10,
) -> VerificationCommandResult:
    preview = preview_verification_command(
        requested_argv,
        approved_test_files=approved_test_files,
        approved_file_checks=approved_file_checks,
    )
    cwd = _resolve_cwd(workspace_root, cwd_relative)
    timeout = _normalize_timeout(timeout_seconds)
    if preview.blocked:
        return _blocked_result(preview, cwd, timeout)
    if cwd is None:
        return _blocked_result(preview, None, timeout, extra_reason="cwd_outside_workspace")

    try:
        completed = subprocess.run(
            list(preview.requested_argv),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return VerificationCommandResult(
            status="timed_out",
            executed=True,
            blocked=False,
            reasons=("timeout_expired",),
            argv=preview.requested_argv,
            matched_command_id=preview.matched_command_id,
            cwd=str(cwd),
            timeout_seconds=timeout,
            exit_code=None,
            stdout=_summarize_output(error.stdout),
            stderr=_summarize_output(error.stderr),
            timed_out=True,
        )
    except OSError as error:
        return VerificationCommandResult(
            status="error",
            executed=True,
            blocked=False,
            reasons=("execution_error",),
            argv=preview.requested_argv,
            matched_command_id=preview.matched_command_id,
            cwd=str(cwd),
            timeout_seconds=timeout,
            exit_code=None,
            stdout="",
            stderr=_summarize_output(str(error)),
        )

    return VerificationCommandResult(
        status="passed" if completed.returncode == 0 else "failed",
        executed=True,
        blocked=False,
        reasons=(),
        argv=preview.requested_argv,
        matched_command_id=preview.matched_command_id,
        cwd=str(cwd),
        timeout_seconds=timeout,
        exit_code=completed.returncode,
        stdout=_summarize_output(completed.stdout),
        stderr=_summarize_output(completed.stderr),
    )


def _normalize_argv(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return ()
        normalized.append(item.strip())
    return tuple(normalized)


def _result_to_dict(value: Any) -> dict[str, Any]:
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict") and callable(value.to_dict):
        result = value.to_dict()
        if isinstance(result, dict):
            return result
    return {}


def _string_value(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _summarize_output(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return ""
    if len(value) <= VERIFICATION_OUTPUT_SUMMARY_LIMIT:
        return value
    return f"{value[:VERIFICATION_OUTPUT_SUMMARY_LIMIT]}... [truncated]"


def _normalize_test_files(value: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            continue
        text = item.strip().replace("\\", "/")
        if text.startswith("/") or ".." in text or "*" in text:
            continue
        if not text.endswith((".py", ".ts", ".tsx")):
            continue
        if text.endswith(("/", "\\")):
            continue
        normalized.append(text)
    return tuple(normalized)


def _normalize_file_checks(
    value: list[dict[str, str]] | tuple[dict[str, str], ...],
) -> tuple[dict[str, str], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if not isinstance(path, str):
            continue
        text = path.strip().replace("\\", "/")
        if not text or text.startswith("/") or ".." in text or "*" in text:
            continue
        if text.endswith("/") or text in {".", "docs", "src", "source_proxy"}:
            continue
        file_check = {"path": text}
        contains = item.get("contains")
        if isinstance(contains, str) and contains.strip():
            contains_text = contains.strip()
            if not _contains_shell_metachar(contains_text):
                file_check["contains"] = contains_text
        normalized.append(file_check)
    return tuple(normalized)


def _forbidden_argv_reasons(argv: tuple[str, ...]) -> list[str]:
    reasons: list[str] = []
    executable = argv[0]
    if executable in SHELL_EXECUTABLES:
        reasons.append("shell_invocation_blocked")
    if any(_contains_shell_metachar(part) for part in argv):
        reasons.append("shell_metachar_blocked")
    if executable in MUTATING_COMMANDS:
        reasons.append("mutating_command_blocked")
    if executable in PROVIDER_OR_NETWORK_COMMANDS:
        reasons.append("provider_or_network_command_blocked")
    if executable in LONG_RUNNING_COMMANDS:
        reasons.append("long_running_command_blocked")
    if _matches_any_prefix(argv, DESTRUCTIVE_GIT_PREFIXES):
        reasons.append("destructive_git_command_blocked")
    if _matches_any_prefix(argv, PACKAGE_INSTALL_PREFIXES):
        reasons.append("package_install_blocked")
    return reasons


def _contains_shell_metachar(value: str) -> bool:
    return any(marker in value for marker in SHELL_METACHARS)


def _matches_any_prefix(
    argv: tuple[str, ...],
    prefixes: tuple[tuple[str, ...], ...],
) -> bool:
    return any(argv[: len(prefix)] == prefix for prefix in prefixes)


def _resolve_cwd(workspace_root: Path, cwd_relative: str) -> Path | None:
    if not isinstance(cwd_relative, str) or not cwd_relative.strip():
        return None
    if Path(cwd_relative).is_absolute() or ".." in cwd_relative.replace("\\", "/").split("/"):
        return None
    root = workspace_root.resolve()
    cwd = (root / cwd_relative).resolve()
    try:
        cwd.relative_to(root)
    except ValueError:
        return None
    return cwd


def _normalize_timeout(timeout_seconds: int) -> int:
    if not isinstance(timeout_seconds, int):
        return 10
    if timeout_seconds < 1:
        return 1
    return min(timeout_seconds, MAX_TIMEOUT_SECONDS)


def _blocked_result(
    preview: VerificationCommandPreview,
    cwd: Path | None,
    timeout_seconds: int,
    *,
    extra_reason: str | None = None,
) -> VerificationCommandResult:
    reasons = list(preview.reasons)
    if extra_reason:
        reasons.append(extra_reason)
    return VerificationCommandResult(
        status="blocked",
        executed=False,
        blocked=True,
        reasons=tuple(_dedupe(reasons)),
        argv=preview.requested_argv,
        matched_command_id=preview.matched_command_id,
        cwd=str(cwd) if cwd is not None else "",
        timeout_seconds=timeout_seconds,
        exit_code=None,
        stdout="",
        stderr="",
    )


def _dedupe(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped
