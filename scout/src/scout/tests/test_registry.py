from pathlib import Path

import pytest

from scout.pollers.registry import load_registry


def test_load_registry_accepts_seed_sources():
    registry = load_registry(Path(__file__).parents[3] / "config" / "sources.yaml")

    assert registry.version == 1
    assert [repo.repo for repo in registry.github_repos] == [
        "anthropic-sdk-python",
        "fastapi",
    ]
    assert len(registry.rss_feeds) == 1


def test_load_registry_rejects_non_https_rss(tmp_path):
    path = tmp_path / "sources.yaml"
    path.write_text(
        """
version: 1
github_repos: []
rss_feeds:
  - url: http://example.com/feed.xml
    poll_interval_minutes: 60
web_pages: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="https"):
        load_registry(path)
