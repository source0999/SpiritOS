from scout.storage.db import open_connection
from scout.storage.migrations import apply_migrations


def test_apply_migrations_creates_phase_2_tables(tmp_path):
    db_path = tmp_path / "scout.db"

    apply_migrations(db_path)

    conn = open_connection(db_path)
    try:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        version = conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'migration_version'"
        ).fetchone()["value"]
    finally:
        conn.close()

    assert {
        "schema_meta",
        "source_tracking",
        "raw_event_index",
        "extracted_artifacts",
        "packets",
        "verdicts",
        "source_quality",
        "packet_embeddings",
        "promotion_queue",
    } <= tables
    assert version == "9"
