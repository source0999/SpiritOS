from io import StringIO

import pytest

from qualification_fixture.jsonl import write_record


def test_records_have_one_newline() -> None:
    stream = StringIO()
    write_record(stream, {"id": 1})
    assert stream.getvalue() == '{"id": 1}\n'


def test_non_serializable_value_has_typed_error() -> None:
    with pytest.raises(ValueError):
        write_record(StringIO(), {"bad": object()})
