from qualification_fixture.frame_parser import parse_frames


def test_partial_and_concatenated_frames_are_handled() -> None:
    assert parse_frames(b"a\n\nb\n\n") == [b"a", b"b"]
    assert parse_frames(b"a\n") == []
