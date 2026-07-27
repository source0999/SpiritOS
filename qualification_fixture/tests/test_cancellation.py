from qualification_fixture.runner import cancel_task


def test_cancellation_is_idempotent_and_terminal() -> None:
    first = cancel_task("task-1", at=1)
    second = cancel_task("task-1", at=2)
    assert first == second
    assert first["status"] == "cancelled"
