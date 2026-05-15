from fastapi import FastAPI
from fastapi.testclient import TestClient

import scout.api.sources as sources_api
from scout.api.sources import router
from scout.config import ScoutSettings
from scout.pollers.registry import register_jobs
from scout.sources.storage import approve_candidate, block_candidate, upsert_candidate
from scout.storage.db import init_database
from scout.storage.migrations import apply_migrations


class FakeScheduler:
    def __init__(self):
        self.jobs = []

    def add_job(self, fn, trigger, **kwargs):
        self.jobs.append({"fn": fn, "trigger": trigger, **kwargs})


def _settings(tmp_path) -> ScoutSettings:
    config_path = tmp_path / "sources.yaml"
    config_path.write_text(
        """
version: 1
github_repos:
  - owner: fastapi
    repo: fastapi
    poll_interval_minutes: 60
rss_feeds: []
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


def test_v02_source_gate_checkpoint_separates_review_queue_from_pollers(
    tmp_path,
    monkeypatch,
):
    settings = _settings(tmp_path)
    monkeypatch.setattr(sources_api, "get_settings", lambda: settings)
    recommended = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/anthropics/anthropic-sdk-python",
        source_kind="github_repo",
        status="recommended",
        confidence_score=0.92,
    )
    approved_rss = upsert_candidate(
        settings.database_path,
        display_uri="https://example.com/feed.xml",
        source_kind="rss_feed",
        status="recommended",
        confidence_score=0.95,
    )
    blocked_docs = upsert_candidate(
        settings.database_path,
        display_uri="https://docs.example.com/noisy",
        source_kind="docs_page",
        status="needs_review",
    )
    approve_candidate(
        settings.database_path,
        approved_rss.candidate_id,
        approved_by="phase0-checkpoint",
        poll_interval_minutes=45,
    )
    block_candidate(
        settings.database_path,
        blocked_docs.candidate_id,
        reason="noisy source",
        blocked_by="phase0-checkpoint",
    )
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    candidates_body = client.get("/v1/scout/source-candidates").json()
    sources_body = client.get("/v1/scout/sources").json()
    scheduler = FakeScheduler()
    register_jobs(scheduler, settings)

    assert candidates_body["counts"]["recommended"] == 1
    assert candidates_body["counts"]["approved"] == 1
    assert candidates_body["counts"]["blocked"] == 1
    assert recommended.candidate_id in {
        candidate["candidate_id"] for candidate in candidates_body["candidates"]
    }
    assert {
        source["canonical_uri"] for source in sources_body["sources"]
    } == {
        "github://fastapi/fastapi",
        "https://example.com/feed.xml",
    }
    assert {
        job["id"] for job in scheduler.jobs
    } == {
        "github:fastapi/fastapi:commits",
        "rss:https://example.com/feed.xml",
    }
