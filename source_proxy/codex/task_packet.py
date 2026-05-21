from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from source_proxy.safety.paths import normalize_repo_path_candidate, unsafe_target_finding

DEFAULT_CODEX_MANUAL_CHECKS = (
    "git status --short",
    "git diff --check",
)
DEFAULT_CODEX_EXPECTED_OUTPUT_FORMAT = {
    "summary": "Short description of work attempted.",
    "files_changed": "List of files changed, or [] for read-only/proposal-only runs.",
    "tests_run": "List commands run and pass/fail result.",
    "diff": "Unified diff when proposing edits; empty for read-only tasks.",
    "recommendation": "One of: ready_for_review, blocked, needs_followup.",
}
CODEX_TASK_SAFETY_RULES = (
    "Produce changes only inside allowed_files.",
    "Do not approve Source Proxy actions.",
    "Do not apply proposals.",
    "Do not commit.",
    "Do not push.",
    "Do not touch secrets, credentials, certificates, or environment files.",
    "Report tests run.",
    "Report files changed.",
    "Stop if the target is ambiguous.",
)


class CodexTaskPacketError(ValueError):
    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def build_codex_task_packet(
    *,
    task: str,
    target_file: str | None = None,
    allowed_files: list[str] | tuple[str, ...] | None = None,
    forbidden_files: list[str] | tuple[str, ...] | None = None,
    relevant_files: list[str] | tuple[str, ...] | None = None,
    manual_checks: list[str] | tuple[str, ...] | None = None,
    rollback_instruction: str | None = None,
    max_scope: str = "single_task",
    task_id: str | None = None,
    workspace: Path | None = None,
    current_branch: str | None = None,
    current_head: str | None = None,
) -> dict[str, Any]:
    workspace_root = (workspace or Path.cwd()).resolve()
    normalized_allowed = _normalize_paths(allowed_files or (), workspace_root=workspace_root)
    normalized_forbidden = _normalize_paths(forbidden_files or (), workspace_root=workspace_root)
    normalized_relevant = _normalize_paths(relevant_files or (), workspace_root=workspace_root)
    normalized_target = _normalize_optional_path(target_file, workspace_root=workspace_root)
    allowed_files_was_provided = allowed_files is not None
    if normalized_target and allowed_files_was_provided and normalized_target not in normalized_allowed:
        raise CodexTaskPacketError(
            "target_file must be present in allowed_files.",
            "codex_task_target_not_allowed",
        )
    if normalized_target and not allowed_files_was_provided and normalized_target not in normalized_allowed:
        normalized_allowed = _dedupe_paths((*normalized_allowed, normalized_target))
    if normalized_target and normalized_target not in normalized_relevant:
        normalized_relevant = _dedupe_paths((*normalized_relevant, normalized_target))

    summary = " ".join(task.strip().split())
    if not summary:
        raise CodexTaskPacketError("Task summary is required.", "codex_task_missing_summary")

    checks = tuple(manual_checks or DEFAULT_CODEX_MANUAL_CHECKS)
    return {
        "packet_version": "codex_task_packet.v1",
        "worker": "codex_cli",
        "task_id": task_id or _stable_task_id(summary, normalized_target, normalized_allowed),
        "task_summary": summary,
        "target_file": normalized_target,
        "allowed_files": list(normalized_allowed),
        "forbidden_files": list(normalized_forbidden),
        "current_branch": current_branch if current_branch is not None else _git_value(workspace_root, "branch"),
        "current_head": current_head if current_head is not None else _git_value(workspace_root, "head"),
        "relevant_files": list(normalized_relevant),
        "manual_checks_required": list(checks),
        "expected_output_format": DEFAULT_CODEX_EXPECTED_OUTPUT_FORMAT.copy(),
        "safety_rules": list(CODEX_TASK_SAFETY_RULES),
        "rollback_instruction": rollback_instruction or _default_rollback(normalized_allowed),
        "max_scope": max_scope,
        "contains_file_contents": False,
        "approval_authority": False,
        "apply_authority": False,
        "commit_authority": False,
        "push_authority": False,
    }


def _normalize_optional_path(path: str | None, *, workspace_root: Path) -> str | None:
    if path is None:
        return None
    normalized = _normalize_path(path, workspace_root=workspace_root)
    return normalized or None


def _normalize_paths(paths: list[str] | tuple[str, ...], *, workspace_root: Path) -> tuple[str, ...]:
    return _dedupe_paths(_normalize_path(path, workspace_root=workspace_root) for path in paths)


def _normalize_path(path: str, *, workspace_root: Path) -> str:
    normalized = normalize_repo_path_candidate(path)
    if not normalized:
        raise CodexTaskPacketError("Path must be non-empty.", "codex_task_empty_path")
    finding = unsafe_target_finding(normalized, workspace_root=workspace_root)
    if finding is not None:
        raise CodexTaskPacketError(finding.message, f"codex_task_{finding.reason_code}")
    return normalized


def _dedupe_paths(paths: tuple[str, ...] | list[str] | Any) -> tuple[str, ...]:
    return tuple(dict.fromkeys(path for path in paths if path))


def _stable_task_id(summary: str, target_file: str | None, allowed_files: tuple[str, ...]) -> str:
    seed = "|".join((summary, target_file or "", ",".join(allowed_files)))
    total = sum((index + 1) * ord(char) for index, char in enumerate(seed))
    return f"codex-task-{total % 1_000_000:06d}"


def _default_rollback(allowed_files: tuple[str, ...]) -> str:
    if not allowed_files:
        return "No rollback expected for read-only work; verify git status remains clean."
    return "Review proposed changes first; use git restore only for the exact allowed files if rollback is approved."


def _git_value(workspace: Path, field: str) -> str | None:
    command = {
        "branch": ["git", "branch", "--show-current"],
        "head": ["git", "rev-parse", "--short", "HEAD"],
    }[field]
    try:
        completed = subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = completed.stdout.strip()
    return value or None
