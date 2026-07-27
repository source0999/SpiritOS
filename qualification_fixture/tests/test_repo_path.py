import pytest

from qualification_fixture.repo_path import validate_repo_path


@pytest.mark.parametrize("value", ["../secret", "%2e%2e/secret", "/etc/passwd", ".env"])
def test_unsafe_paths_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        validate_repo_path(value)
