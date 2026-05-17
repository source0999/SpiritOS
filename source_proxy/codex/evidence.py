from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from source_proxy.safety.paths import is_secret_shaped_path

DEFAULT_CODEX_EVIDENCE_DIR = Path("/tmp/spiritos-source-proxy-codex/artifacts")
DEFAULT_EXCERPT_CHARS = 2_000


class CodexEvidenceError(ValueError):
    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def build_codex_evidence_packet(
    *,
    task_id: str,
    command: list[str],
    sandbox: str,
    started_at: str,
    finished_at: str,
    exit_code: int | None,
    final_message: str = "",
    stdout: str = "",
    stderr: str = "",
    changed_files_before: list[str] | tuple[str, ...] | None = None,
    changed_files_after: list[str] | tuple[str, ...] | None = None,
    diff_stat: str = "",
    diff: str = "",
    head_before: str | None = None,
    head_after: str | None = None,
    recommendation: str | None = None,
    rollback_hint: str | None = None,
    excerpt_chars: int = DEFAULT_EXCERPT_CHARS,
) -> dict[str, Any]:
    if not task_id.strip():
        raise CodexEvidenceError("task_id is required.", "codex_evidence_missing_task_id")
    if sandbox not in {"read-only", "workspace-write"}:
        raise CodexEvidenceError("Unsupported Codex sandbox.", "codex_evidence_unsafe_sandbox")
    before = _safe_file_list(changed_files_before or ())
    after = _safe_file_list(changed_files_after or ())
    safety_verdict = _safety_verdict(
        exit_code=exit_code,
        changed_files_before=before,
        changed_files_after=after,
        head_before=head_before,
        head_after=head_after,
    )
    return {
        "artifact_version": "codex_evidence.v1",
        "task_id": task_id,
        "worker": "codex_cli",
        "command": _redact_command(command),
        "sandbox": sandbox,
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": exit_code,
        "final_message_excerpt": _excerpt(final_message, excerpt_chars),
        "stdout_excerpt": _excerpt(stdout, excerpt_chars),
        "stderr_excerpt": _excerpt(stderr, excerpt_chars),
        "json_event_count": _json_event_count(stdout),
        "changed_files_before": before,
        "changed_files_after": after,
        "diff_stat": _excerpt(diff_stat, excerpt_chars),
        "diff_excerpt": _excerpt(diff, excerpt_chars),
        "head_before": head_before,
        "head_after": head_after,
        "safety_verdict": safety_verdict,
        "recommendation": recommendation or _default_recommendation(safety_verdict),
        "rollback_hint": rollback_hint or _default_rollback_hint(safety_verdict, after),
        "approval_authority": False,
        "apply_authority": False,
        "commit_authority": False,
        "push_authority": False,
    }


def write_codex_evidence_packet(
    packet: dict[str, Any],
    *,
    output_dir: Path = DEFAULT_CODEX_EVIDENCE_DIR,
) -> Path:
    task_id = str(packet.get("task_id") or "").strip()
    if not task_id:
        raise CodexEvidenceError("task_id is required.", "codex_evidence_missing_task_id")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{_safe_artifact_name(task_id)}.json"
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safety_verdict(
    *,
    exit_code: int | None,
    changed_files_before: tuple[str, ...],
    changed_files_after: tuple[str, ...],
    head_before: str | None,
    head_after: str | None,
) -> str:
    if head_before and head_after and head_before != head_after:
        return "blocked_head_changed"
    if changed_files_before != changed_files_after:
        return "blocked_changed_files_delta"
    if exit_code not in (0, None):
        return "failed"
    return "passed"


def _default_recommendation(safety_verdict: str) -> str:
    if safety_verdict == "passed":
        return "ready_for_review"
    if safety_verdict.startswith("blocked"):
        return "blocked"
    return "needs_followup"


def _default_rollback_hint(safety_verdict: str, changed_files_after: tuple[str, ...]) -> str:
    if safety_verdict == "passed":
        return "No rollback needed; verify git status and HEAD remain expected."
    if changed_files_after:
        return "Review changed files and restore only approved targets if rollback is approved."
    return "No file rollback identified; inspect execution logs before retry."


def _safe_file_list(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    safe: list[str] = []
    for path in paths:
        value = str(path).strip()
        if not value:
            continue
        safe.append("[redacted-protected-path]" if is_secret_shaped_path(value) else value)
    return tuple(dict.fromkeys(safe))


def _redact_command(command: list[str]) -> list[str]:
    return [_redact_text(str(part), DEFAULT_EXCERPT_CHARS) for part in command]


def _excerpt(value: str, max_chars: int) -> str:
    text = _redact_text(value or "", max_chars)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[truncated]"


def _redact_text(value: str, max_chars: int) -> str:
    lines = []
    for line in value.splitlines():
        if is_secret_shaped_path(line) or _looks_secret_value(line):
            lines.append("[redacted-sensitive-line]")
        else:
            lines.append(line)
    text = "\n".join(lines)
    return text[: max(max_chars, 0) + 20]


def _looks_secret_value(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in ("api_key", "password", "secret=", "token="))


def _json_event_count(stdout: str) -> int:
    count = 0
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "type" in parsed:
            count += 1
    return count


def _safe_artifact_name(task_id: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in task_id)[:120]
