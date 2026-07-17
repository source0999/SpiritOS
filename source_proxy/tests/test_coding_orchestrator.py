from __future__ import annotations

import pytest

from source_proxy.coding.orchestrator import (
    CodingLaneStateMachine,
    CodingOrchestrator,
    CodingOrchestratorError,
    LANE_SEQUENCE,
)
from source_proxy.tasks.long_running import execute_approved_long_running_task


def test_lane_state_machine_has_explicit_dependency_order_and_terminal_states() -> None:
    state = CodingLaneStateMachine(task_id="task-1", run_id="run-1")

    assert tuple(state.lane_states) == LANE_SEQUENCE
    state.transition("context-broker", "running")
    state.transition("context-broker", "completed")
    state.transition("planner", "running")
    state.transition("planner", "completed")
    state.transition("coder", "running")
    state.transition("coder", "failed", reason="provider_timeout")
    state.transition("coder", "recovering")
    state.transition("coder", "completed")
    state.transition("repair", "skipped", reason="no_repair_needed")

    assert state.lane_states["coder"] == "completed"
    assert state.lane_reasons["repair"] == "no_repair_needed"
    with pytest.raises(CodingOrchestratorError, match="invalid_coding_lane_transition"):
        state.transition("coder", "running")


def test_orchestrator_delegates_execution_to_the_existing_executor_by_default() -> None:
    orchestrator = CodingOrchestrator()

    assert orchestrator._executor is execute_approved_long_running_task
