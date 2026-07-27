from qualification_fixture.clock import now


def test_clock_is_injectable() -> None:
    assert callable(now)
