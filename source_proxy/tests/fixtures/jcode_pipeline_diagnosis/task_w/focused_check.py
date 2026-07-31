from label import normalize_label


def test_normalize_label_is_lowercase_and_hyphenated():
    assert normalize_label("  Alpha Beta  ") == "alpha-beta"
    assert normalize_label("Already   Spaced") == "already-spaced"
