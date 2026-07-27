import pytest

from qualification_fixture.ttl import parse_ttl


@pytest.mark.parametrize("value", [True, -1, "-2s", 2**63])
def test_invalid_ttls_are_rejected(value: object) -> None:
    with pytest.raises(ValueError):
        parse_ttl(value)


def test_seconds_are_accepted() -> None:
    assert parse_ttl("12s") == 12
