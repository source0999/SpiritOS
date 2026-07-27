import pytest

from qualification_fixture.plugins import Plugin, PluginRegistry


def test_registry_rejects_duplicates_and_unknown_capabilities() -> None:
    registry = PluginRegistry(allowed_capabilities={"read"})
    registry.register(Plugin("one", ("read",)))
    with pytest.raises(ValueError):
        registry.register(Plugin("one", ("read",)))
    with pytest.raises(ValueError):
        registry.register(Plugin("two", ("write",)))
