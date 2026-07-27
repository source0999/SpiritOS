import pytest

from qualification_fixture.state import TaskState


def test_terminal_state_cannot_resume() -> None:
    state = TaskState()
    assert state.transition("completed") == "completed"
    with pytest.raises(ValueError):
        state.transition("running")


def test_duplicate_terminal_write_is_idempotent() -> None:
    state = TaskState()
    state.transition("completed")
    assert state.transition("completed") == "completed"
