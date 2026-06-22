from __future__ import annotations

import re
from typing import Any

APPROVED_EXECUTION_STATUSES = frozenset({
    "executing",
    "applied",
    "applied_needs_verification",
    "applied_verification_failed",
    "verification_failed",
    "verified",
})

TERMINAL_OR_WAITING_STATUSES = frozenset({
    "blocked",
    "blocked_after_retries",
    "blocked_by_review",
    "cancelled",
    "completed",
    "coder_config_blocked",
    "failed_needs_human",
    "needs_context",
    "applied_needs_verification",
    "applied_verification_failed",
    "verification_failed",
})


def append_unique_steps(current_steps: list[str], next_steps: list[str]) -> list[str]:
    merged = list(current_steps)
    for step in next_steps:
        if step not in merged:
            merged.append(step)
    return merged[:12]


def has_approved_execution(open_diffs: list[dict[str, Any]]) -> bool:
    return any(str(diff.get("status") or "") in APPROVED_EXECUTION_STATUSES for diff in open_diffs)


def terminal_or_waiting_statuses() -> set[str]:
    return set(TERMINAL_OR_WAITING_STATUSES)


def task_is_waiting_for_coder_output(
    *,
    current_agent_role: str,
    architect_status: str,
    open_diffs: list[dict[str, Any]],
) -> bool:
    return current_agent_role == "coder" and architect_status == "planned" and not open_diffs


def task_blocker_reason_code(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None
    for pattern in (
        r"reason_code[:=]\s*([A-Za-z0-9_-]+)",
        r"^([A-Za-z0-9_-]+):",
    ):
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def task_queue_title(description: str) -> str:
    first_line = next((line.strip() for line in description.splitlines() if line.strip()), "")
    return first_line[:120] if first_line else "Untitled task"
