import json

from scout.config import ScoutSettings
from scout.extractors import process_pending_raw_events
from scout.storage.db import init_database, open_connection
from scout.storage.jsonl import append_raw_event
from scout.storage.migrations import apply_migrations
from scout.storage.source_tracking import insert_raw_event_index


def test_process_pending_raw_events_extracts_rss_entry(tmp_path):
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        config_path=tmp_path / "sources.yaml",
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    payload = {
        "title": "A Scout Article",
        "link": "https://example.com/article",
        "published": "2026-05-14T00:00:00+00:00",
        "summary": "A useful summary.",
    }
    rel_path, payload_sha = append_raw_event(
        settings.data_dir,
        "https://example.com/feed.xml",
        "rss.entry",
        payload,
    )
    content_hash = "rss-hash"
    assert insert_raw_event_index(
        settings.database_path,
        source_uri="https://example.com/feed.xml",
        event_kind="rss.entry",
        payload_path=rel_path,
        payload_sha256=payload_sha,
        content_hash=content_hash,
    )

    result = process_pending_raw_events(settings)

    conn = open_connection(settings.database_path)
    try:
        rows = conn.execute("SELECT * FROM extracted_artifacts").fetchall()
    finally:
        conn.close()

    assert result["processed"] == 1
    assert len(rows) == 1
    artifact = tmp_path / rows[0]["artifact_path"]
    assert "A Scout Article" in artifact.read_text(encoding="utf-8")
    assert json.loads(rows[0]["metadata_json"])["kind"] == "rss_markdown"
