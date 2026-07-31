from source_file import qualification_result


def test_qualification_result_is_the_sealed_value() -> None:
    assert qualification_result() == "SAFE_WRITE_SMOKE_OK"
