from __future__ import annotations

import dataclasses
import subprocess
from pathlib import Path
from typing import Any

VERIFICATION_RUNNER_PHASE = "Plan 4 Phase 3: Verification API"
MAX_TIMEOUT_SECONDS = 30

BASE_ALLOWED_ARGV: tuple[tuple[str, ...], ...] = (
    ("git", "diff", "--check"),
    ("git", "status", "--short"),
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
        "Plan 4 Phase 2 validates exact argv allowlist entries only. It does "
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


def build_verification_runner_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Daily Driver Autonomy Roadmap Plan 4",
        "phase": VERIFICATION_RUNNER_PHASE,
        "status": "verification-api-available",
        "argv_only": True,
        "shell_allowed": False,
        "execution_available": True,
        "command_authority_granted": False,
        "workflow_authority_granted": False,
        "queue_authority_granted": False,
        "git_mutation_authority_granted": False,
        "max_timeout_seconds": MAX_TIMEOUT_SECONDS,
        "safe_next_action": "Execute only exact allowlisted verification argv.",
    }


def build_verification_command_allowlist(
    *,
    approved_test_files: list[str] | tuple[str, ...] = (),
) -> tuple[VerificationCommandSpec, ...]:
    specs = [
        VerificationCommandSpec(
            command_id="git_diff_check",
            argv=BASE_ALLOWED_ARGV[0],
            purpose="Verify repository whitespace and conflict marker cleanliness.",
        ),
        VerificationCommandSpec(
            command_id="git_status_short",
            argv=BASE_ALLOWED_ARGV[1],
            purpose="Inspect repository status without mutating git state.",
        ),
    ]
    for test_file in _normalize_test_files(approved_test_files):
        specs.append(
            VerificationCommandSpec(
                command_id=f"pytest:{test_file}",
                argv=(*PYTEST_ARGV_PREFIX, test_file),
                purpose="Run one exact approved Python test file.",
            )
        )
        specs.append(
            VerificationCommandSpec(
                command_id=f"npm_test:{test_file}",
                argv=(*NPM_TEST_ARGV_PREFIX, test_file),
                purpose="Run one exact approved frontend test file through npm.",
            )
        )
    return tuple(specs)


def preview_verification_command(
    requested_argv: Any,
    *,
    approved_test_files: list[str] | tuple[str, ...] = (),
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
    cwd_relative: str = ".",
    timeout_seconds: int = 10,
) -> VerificationCommandResult:
    preview = preview_verification_command(
        requested_argv,
        approved_test_files=approved_test_files,
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
            stdout=error.stdout if isinstance(error.stdout, str) else "",
            stderr=error.stderr if isinstance(error.stderr, str) else "",
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
            stderr=str(error),
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
        stdout=completed.stdout,
        stderr=completed.stderr,
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


def _normalize_test_files(value: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            continue
        text = item.strip().replace("\\", "/")
        if text.startswith("/") or ".." in text or "*" in text:
            continue
        normalized.append(text)
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
