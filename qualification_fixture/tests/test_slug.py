from qualification_fixture.slug import slugify


def test_slugifies_unicode_and_repeated_separators() -> None:
    assert slugify("Cafe Cafe---TEA") == "cafe-cafe-tea"


def test_empty_slug_is_empty() -> None:
    assert slugify("") == ""
