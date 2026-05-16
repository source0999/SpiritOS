from pathlib import Path

import pytest

from scout.config import ScoutSettings
from scout.pollers.registry import load_merged_registry, load_registry, register_jobs
from scout.sources.storage import approve_candidate, upsert_candidate
from scout.storage.db import init_database
from scout.storage.migrations import apply_migrations


class FakeScheduler:
    def __init__(self):
        self.jobs = []

    def add_job(self, fn, trigger, **kwargs):
        self.jobs.append({"fn": fn, "trigger": trigger, **kwargs})


def _settings(tmp_path, config_text: str | None = None) -> ScoutSettings:
    config_path = tmp_path / "sources.yaml"
    config_path.write_text(
        config_text
        or """
version: 1
github_repos:
  - owner: fastapi
    repo: fastapi
    poll_interval_minutes: 60
rss_feeds:
  - url: https://blog.python.org/feeds/posts/default
    poll_interval_minutes: 60
web_pages: []
""",
        encoding="utf-8",
    )
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        config_path=config_path,
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    return settings


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


def test_load_merged_registry_adds_approved_github_and_rss_sources(tmp_path):
    settings = _settings(tmp_path)
    github_candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/anthropics/anthropic-sdk-python",
        source_kind="github_repo",
    )
    rss_candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://example.com/feed.xml",
        source_kind="rss_feed",
    )
    approve_candidate(
        settings.database_path,
        github_candidate.candidate_id,
        approved_by="tester",
        poll_interval_minutes=45,
    )
    approve_candidate(
        settings.database_path,
        rss_candidate.candidate_id,
        approved_by="tester",
        poll_interval_minutes=30,
    )

    registry = load_merged_registry(settings)

    assert {(source.owner, source.repo) for source in registry.github_repos} == {
        ("fastapi", "fastapi"),
        ("anthropics", "anthropic-sdk-python"),
    }
    assert {str(source.url).rstrip("/") for source in registry.rss_feeds} == {
        "https://blog.python.org/feeds/posts/default",
        "https://example.com/feed.xml",
    }
    assert next(
        source
        for source in registry.github_repos
        if source.owner == "anthropics"
    ).poll_interval_minutes == 45


def test_load_merged_registry_ignores_unapproved_candidates(tmp_path):
    settings = _settings(tmp_path)
    upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/anthropics/anthropic-sdk-python",
        source_kind="github_repo",
        status="recommended",
    )

    registry = load_merged_registry(settings)

    assert [(source.owner, source.repo) for source in registry.github_repos] == [
        ("fastapi", "fastapi")
    ]


def test_load_merged_registry_dedupes_static_sources(tmp_path):
    settings = _settings(tmp_path)
    candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/fastapi/fastapi",
        source_kind="github_repo",
    )
    approve_candidate(settings.database_path, candidate.candidate_id, approved_by="tester")

    registry = load_merged_registry(settings)

    assert [(source.owner, source.repo) for source in registry.github_repos] == [
        ("fastapi", "fastapi")
    ]


def test_register_jobs_schedules_supported_approved_sources_only(tmp_path):
    settings = _settings(tmp_path)
    github_candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/anthropics/anthropic-sdk-python",
        source_kind="github_repo",
    )
    web_candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://docs.example.com/guide",
        source_kind="docs_page",
    )
    approve_candidate(settings.database_path, github_candidate.candidate_id, approved_by="tester")
    approve_candidate(settings.database_path, web_candidate.candidate_id, approved_by="tester")
    scheduler = FakeScheduler()

    registry = register_jobs(scheduler, settings)

    job_ids = {job["id"] for job in scheduler.jobs}
    assert "github:fastapi/fastapi:commits" in job_ids
    assert "github:anthropics/anthropic-sdk-python:commits" in job_ids
    assert "rss:https://blog.python.org/feeds/posts/default" in job_ids
    assert all("docs.example.com" not in job_id for job_id in job_ids)
    assert len(registry.web_pages) == 1
