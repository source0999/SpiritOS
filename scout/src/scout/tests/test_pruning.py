from datetime import datetime, timezone, timedelta
import json

from scout.config import ScoutSettings
from scout.packets.storage import insert_packet
from scout.storage.db import init_database, open_connection
from scout.storage.migrations import apply_migrations
from scout.storage.pruning import prune_packet_embeddings
from scout.tests.test_packet_schema import make_packet


def _insert_embedding(conn, packet_id: str) -> None:
    conn.execute(
        "INSERT INTO packet_embeddings(packet_id, embedding) VALUES (?, ?)",
        (packet_id, json.dumps([0.0] * 384)),
    )


def test_prune_packet_embeddings_deletes_only_allowed_embeddings(tmp_path):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)

    old = datetime.now(timezone.utc) - timedelta(days=200)
    recent = datetime.now(timezone.utc)
    ignored = make_packet("ignored_old")
    ignored.timestamp = old
    ignored.status = "ignored"
    stored = make_packet("stored_old")
    stored.timestamp = old
    stored.status = "stored"
    surfaced = make_packet("surfaced_old")
    surfaced.timestamp = old
    surfaced.status = "surfaced"
    recent_ignored = make_packet("ignored_recent")
    recent_ignored.timestamp = recent
    recent_ignored.status = "ignored"
    for packet in [ignored, stored, surfaced, recent_ignored]:
        insert_packet(settings, packet)

    conn = open_connection(settings.database_path)
    try:
        conn.execute(
            """
            INSERT INTO source_quality(source_uri, score, updated_at)
            VALUES (?, 0.3, ?)
            """,
            ("https://example.com/feed.xml", recent.isoformat()),
        )
        for packet_id in ["ignored_old", "stored_old", "surfaced_old", "ignored_recent"]:
            _insert_embedding(conn, packet_id)
        conn.commit()
    finally:
        conn.close()

    result = prune_packet_embeddings(settings)

    conn = open_connection(settings.database_path)
    try:
        remaining = {
            row["packet_id"]
            for row in conn.execute("SELECT packet_id FROM packet_embeddings")
        }
    finally:
        conn.close()

    assert result["embeddings_pruned"] == 2
    assert remaining == {"surfaced_old", "ignored_recent"}
