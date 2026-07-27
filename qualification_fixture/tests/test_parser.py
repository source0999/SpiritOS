from qualification_fixture.parser import parse


def test_stdlib_fallback_when_optional_parser_is_absent() -> None:
    assert parse("kind=value") == {"kind": "value"}
