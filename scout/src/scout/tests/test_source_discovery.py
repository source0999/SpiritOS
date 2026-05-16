import json
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

import scout.api.sources as sources_api
from scout.api.sources import router
from scout.config import ScoutSettings
from scout.sources.discovery import extract_candidate_urls, run_artifact_discovery
from scout.sources.storage import block_candidate, list_candidates, upsert_candidate
from scout.storage.db import init_database, open_connection
from scout.storage.migrations import apply_migrations


def _settings(tmp_path) -> ScoutSettings:
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    return settings


def _insert_artifact(settings: ScoutSettings, *, text: str, source_uri: str = "https://blog.python.org/feed") -> str:
    artifact_dir = settings.data_dir / "extracted" / "blog.python.org"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "artifact.md"
    artifact_path.write_text(text, encoding="utf-8")
    rel_path = str(artifact_path.relative_to(settings.data_dir))
    conn = open_connection(settings.database_path)
    try:
        conn.execute(
            """
            INSERT INTO raw_event_index (
                event_id, source_uri, event_kind, payload_path, payload_sha256,
                captured_at_epoch, content_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "event_1",
                source_uri,
                "rss.entry",
                "logs/source-discovery-test.jsonl",
                "sha256",
                time.time(),
                f"hash-{rel_path}",
            ),
        )
        conn.execute(
            """
            INSERT INTO extracted_artifacts (
                event_id, source_uri, event_kind, artifact_kind, artifact_path,
                metadata_json, extracted_at_epoch
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "event_1",
                source_uri,
                "rss.entry",
                "rss_markdown",
                rel_path,
                json.dumps({"kind": "rss_markdown"}),
                time.time(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return rel_path


def test_extract_candidate_urls_filters_noise_and_dedupes():
    urls = extract_candidate_urls(
        """
        [FastAPI](https://github.com/FastAPI/FastAPI?utm_source=newsletter)
        Duplicate: https://github.com/fastapi/fastapi/
        [Docs](https://docs.example.com/tutorial/?utm_campaign=x)
        [Share](https://twitter.com/share?url=https://docs.example.com)
        ![Logo](https://example.com/logo.png)
        [Mail](mailto:team@example.com)
        """
    )

    assert [item.canonical_uri for item in urls] == [
        "github://fastapi/fastapi",
        "https://docs.example.com/tutorial",
    ]
    assert urls[0].source_kind == "github_repo"
    assert urls[1].source_kind == "docs_page"


def test_run_artifact_discovery_writes_candidates_and_events(tmp_path):
    settings = _settings(tmp_path)
    rel_path = _insert_artifact(
        settings,
        text="""
        See [FastAPI](https://github.com/fastapi/fastapi?utm_source=rss)
        and https://docs.example.dev/changelog.
        Ignore https://example.dev/image.svg
        """,
    )

    result = run_artifact_discovery(settings, limit=10)
    candidates = list_candidates(settings.database_path, limit=10)
    conn = open_connection(settings.database_path)
    try:
        events = conn.execute("SELECT * FROM source_discovery_events").fetchall()
    finally:
        conn.close()

    assert result["checked_artifacts"] == 1
    assert result["scanned_artifacts"] == 1
    assert result["candidates_created"] == 2
    by_uri = {candidate.canonical_uri: candidate for candidate in candidates}
    assert set(by_uri) == {"github://fastapi/fastapi", "https://docs.example.dev/changelog"}
    assert by_uri["github://fastapi/fastapi"].status == "recommended"
    assert by_uri["github://fastapi/fastapi"].confidence_score >= 0.9
    assert "official_repo_pattern" in by_uri["github://fastapi/fastapi"].reason_codes
    assert len(events) == 2
    assert {row["artifact_path"] for row in events} == {rel_path}


def test_run_artifact_discovery_respects_blocked_candidates(tmp_path):
    settings = _settings(tmp_path)
    candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://spam.example/tracker",
    )
    block_candidate(
        settings.database_path,
        candidate.candidate_id,
        reason="spam",
        blocked_by="tester",
    )
    _insert_artifact(settings, text="Again: https://spam.example/tracker?utm_source=rss")

    result = run_artifact_discovery(settings, limit=10)
    rediscovered = list_candidates(settings.database_path)[0]

    assert result["candidates_seen"] == 1
    assert rediscovered.status == "blocked"
    assert rediscovered.blocked_reason == "spam"


def test_source_discovery_debug_api_runs_artifact_scan(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    _insert_artifact(settings, text="Docs: https://docs.example.com/guide")
    monkeypatch.setattr(sources_api, "get_settings", lambda: settings)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    body = client.post("/v1/scout/source-discovery/run-debug", json={"limit": 5}).json()

    assert body["checked_artifacts"] == 1
    assert body["candidates_created"] == 1
    assert list_candidates(settings.database_path)[0].canonical_uri == (
        "https://docs.example.com/guide"
    )
