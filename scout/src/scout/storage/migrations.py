from collections.abc import Callable
from pathlib import Path
import sqlite3

from scout.storage.db import open_connection

Migration = Callable[[sqlite3.Connection], None]

MIGRATIONS: list[tuple[int, Migration]] = []


def register(version: int):
    def deco(fn: Migration) -> Migration:
        MIGRATIONS.append((version, fn))
        return fn

    return deco


@register(1)
def _v1_source_tracking(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS source_tracking (
            source_uri TEXT NOT NULL,
            page_key TEXT NOT NULL DEFAULT '',
            etag TEXT,
            last_modified TEXT,
            last_polled_epoch REAL,
            ratelimit_remaining INTEGER,
            ratelimit_reset_epoch INTEGER,
            consecutive_failures INTEGER NOT NULL DEFAULT 0,
            authed INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (source_uri, page_key)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_event_index (
            event_id TEXT PRIMARY KEY,
            source_uri TEXT NOT NULL,
            event_kind TEXT NOT NULL,
            payload_path TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            captured_at_epoch REAL NOT NULL,
            content_hash TEXT NOT NULL,
            UNIQUE (source_uri, content_hash)
        )
        """
    )


@register(2)
def _v2_extracted_artifacts(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS extracted_artifacts (
            event_id TEXT PRIMARY KEY,
            source_uri TEXT NOT NULL,
            event_kind TEXT NOT NULL,
            artifact_kind TEXT NOT NULL,
            artifact_path TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            extracted_at_epoch REAL NOT NULL,
            FOREIGN KEY(event_id) REFERENCES raw_event_index(event_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_extracted_artifacts_source
        ON extracted_artifacts(source_uri)
        """
    )


@register(3)
def _v3_packets(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS packets (
            packet_id TEXT PRIMARY KEY,
            schema_version INTEGER NOT NULL,
            source_uri TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            packet_json TEXT NOT NULL,
            synthesized_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_packets_status ON packets(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_packets_source ON packets(source_uri)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_packets_synthesized ON packets(synthesized_at)"
    )


@register(4)
def _v4_verdicts(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS verdicts (
            packet_id TEXT PRIMARY KEY REFERENCES packets(packet_id) ON DELETE CASCADE,
            decision TEXT NOT NULL,
            tier_reached INTEGER NOT NULL,
            verdict_json TEXT NOT NULL,
            evaluated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_verdicts_decision ON verdicts(decision)"
    )


@register(5)
def _v5_source_quality(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS source_quality (
            source_uri TEXT PRIMARY KEY,
            packets_total INTEGER NOT NULL DEFAULT 0,
            packets_promoted INTEGER NOT NULL DEFAULT 0,
            packets_surfaced INTEGER NOT NULL DEFAULT 0,
            packets_ignored INTEGER NOT NULL DEFAULT 0,
            score REAL NOT NULL DEFAULT 0.5,
            updated_at TEXT NOT NULL
        )
        """
    )


@register(6)
def _v6_packet_embeddings(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS packet_embeddings USING vec0(
            packet_id TEXT PRIMARY KEY,
            embedding float[384]
        )
        """
    )


@register(7)
def _v7_promotion_queue(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS promotion_queue (
            promotion_id TEXT PRIMARY KEY,
            packet_id TEXT NOT NULL REFERENCES packets(packet_id) ON DELETE CASCADE,
            requested_at TEXT NOT NULL,
            approved_at TEXT,
            approved_by TEXT,
            rejected_at TEXT,
            rejected_reason TEXT,
            payload_sha256 TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued'
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_promotion_queue_status
        ON promotion_queue(status)
        """
    )


@register(8)
def _v8_promotion_queue_request_metadata(conn: sqlite3.Connection) -> None:
    _ensure_promotion_queue_request_metadata(conn)


@register(9)
def _v9_repair_promotion_queue_request_metadata(conn: sqlite3.Connection) -> None:
    _ensure_promotion_queue_request_metadata(conn)


def _ensure_promotion_queue_request_metadata(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(promotion_queue)").fetchall()
    }
    if "requested_by" not in columns:
        conn.execute("ALTER TABLE promotion_queue ADD COLUMN requested_by TEXT")
    if "reason" not in columns:
        conn.execute("ALTER TABLE promotion_queue ADD COLUMN reason TEXT")


def apply_migrations(db_path: Path) -> None:
    conn = open_connection(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        current = conn.execute(
            "SELECT value FROM schema_meta WHERE key='migration_version'"
        ).fetchone()
        current_version = int(current["value"]) if current else 0
        for version, fn in sorted(MIGRATIONS):
            if version > current_version:
                fn(conn)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO schema_meta (key, value)
                    VALUES ('migration_version', ?)
                    """,
                    (str(version),),
                )
                conn.commit()
    finally:
        conn.close()
