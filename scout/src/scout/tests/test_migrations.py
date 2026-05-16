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
        "source_registry",
        "source_candidates",
        "source_discovery_events",
        "blocked_sources",
        "discovery_jobs",
        "source_review_events",
    } <= tables
    assert version == "12"


def test_apply_migrations_is_idempotent_for_source_registry(tmp_path):
    db_path = tmp_path / "scout.db"

    apply_migrations(db_path)
    apply_migrations(db_path)

    conn = open_connection(db_path)
    try:
        version = conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'migration_version'"
        ).fetchone()["value"]
        indexes = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert version == "12"
    assert {
        "idx_source_registry_status",
        "idx_source_registry_kind",
        "idx_source_candidates_status",
        "idx_source_candidates_confidence",
        "idx_source_candidates_discovered_from",
        "idx_discovery_jobs_status",
        "idx_discovery_jobs_created",
        "idx_source_review_events_candidate",
        "idx_source_review_events_canonical",
        "idx_source_review_events_created",
    } <= indexes
