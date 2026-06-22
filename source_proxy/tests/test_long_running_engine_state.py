from __future__ import annotations

from source_proxy.tasks import long_running
from source_proxy.tasks.engine.state import (
    append_unique_steps,
    has_approved_execution,
    task_blocker_reason_code,
    task_is_waiting_for_coder_output,
    task_queue_title,
    terminal_or_waiting_statuses,
)


def test_terminal_statuses_match_long_running_alias() -> None:
    assert terminal_or_waiting_statuses() == long_running._terminal_or_waiting_statuses()
    assert "completed" in terminal_or_waiting_statuses()
    assert "running" not in terminal_or_waiting_statuses()


def test_approved_execution_detection_matches_long_running_alias() -> None:
    open_diffs = [{"status": "pending_verification"}, {"status": "applied_needs_verification"}]

    assert has_approved_execution(open_diffs) is True
    assert long_running._has_approved_execution(open_diffs) is True
    assert has_approved_execution([{"status": "pending_verification"}]) is False


def test_append_unique_steps_preserves_order_and_cap() -> None:
    current = [f"step-{index}" for index in range(10)]
    merged = append_unique_steps(current, ["step-3", "step-10", "step-11", "step-12"])

    assert merged == long_running._append_unique_steps(current, ["step-3", "step-10", "step-11", "step-12"])
    assert merged[-2:] == ["step-10", "step-11"]
    assert len(merged) == 12


def test_waiting_for_coder_output_predicate_matches_task_wrapper() -> None:
    task = long_running.LongRunningTask(description="demo")
    task.current_agent_role = "coder"
    task.architect_status = "planned"
    task.open_diffs = []

    assert task_is_waiting_for_coder_output(
        current_agent_role=task.current_agent_role,
        architect_status=task.architect_status,
        open_diffs=task.open_diffs,
    ) is True
    assert long_running._task_is_waiting_for_coder_output(task) is True
    task.open_diffs = [{"status": "pending_verification"}]
    assert long_running._task_is_waiting_for_coder_output(task) is False


def test_blocker_reason_and_title_match_long_running_aliases() -> None:
    assert task_blocker_reason_code("reason_code: write_scope_conflict") == "write_scope_conflict"
    assert long_running._task_blocker_reason_code("write_scope_conflict: blocked") == "write_scope_conflict"
    assert task_queue_title("\n  First title line\nSecond") == "First title line"
    assert long_running._task_queue_title("") == "Untitled task"
