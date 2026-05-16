from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import time
import uuid

from scout.storage.db import open_connection


@dataclass(frozen=True)
class SourceState:
    source_uri: str
    page_key: str = ""
    etag: str | None = None
    last_modified: str | None = None
    last_polled_epoch: float | None = None
    ratelimit_remaining: int | None = None
    ratelimit_reset_epoch: int | None = None
    consecutive_failures: int = 0
    authed: bool = False


def _state_from_row(row: sqlite3.Row | None, source_uri: str, page_key: str) -> SourceState:
    if row is None:
        return SourceState(source_uri=source_uri, page_key=page_key)
    return SourceState(
        source_uri=row["source_uri"],
        page_key=row["page_key"],
        etag=row["etag"],
        last_modified=row["last_modified"],
        last_polled_epoch=row["last_polled_epoch"],
        ratelimit_remaining=row["ratelimit_remaining"],
        ratelimit_reset_epoch=row["ratelimit_reset_epoch"],
        consecutive_failures=row["consecutive_failures"],
        authed=bool(row["authed"]),
    )


def get_source_state(db_path: Path, source_uri: str, page_key: str = "") -> SourceState:
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT * FROM source_tracking
            WHERE source_uri = ? AND page_key = ?
            """,
            (source_uri, page_key),
        ).fetchone()
        return _state_from_row(row, source_uri, page_key)
    finally:
        conn.close()


def mark_not_modified(
    db_path: Path,
    source_uri: str,
    page_key: str,
    *,
    ratelimit_remaining: int | None = None,
    ratelimit_reset_epoch: int | None = None,
    authed: bool = False,
) -> None:
    conn = open_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO source_tracking (
                source_uri, page_key, last_polled_epoch, ratelimit_remaining,
                ratelimit_reset_epoch, consecutive_failures, authed
            )
            VALUES (?, ?, ?, ?, ?, 0, ?)
            ON CONFLICT(source_uri, page_key) DO UPDATE SET
                last_polled_epoch = excluded.last_polled_epoch,
                ratelimit_remaining = excluded.ratelimit_remaining,
                ratelimit_reset_epoch = excluded.ratelimit_reset_epoch,
                consecutive_failures = 0,
                authed = excluded.authed
            """,
            (
                source_uri,
                page_key,
                time.time(),
                ratelimit_remaining,
                ratelimit_reset_epoch,
                int(authed),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def mark_success(
    db_path: Path,
    source_uri: str,
    page_key: str,
    *,
    etag: str | None,
    last_modified: str | None,
    ratelimit_remaining: int | None = None,
    ratelimit_reset_epoch: int | None = None,
    authed: bool = False,
) -> None:
    conn = open_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO source_tracking (
                source_uri, page_key, etag, last_modified, last_polled_epoch,
                ratelimit_remaining, ratelimit_reset_epoch,
                consecutive_failures, authed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
            ON CONFLICT(source_uri, page_key) DO UPDATE SET
                etag = excluded.etag,
                last_modified = excluded.last_modified,
                last_polled_epoch = excluded.last_polled_epoch,
                ratelimit_remaining = excluded.ratelimit_remaining,
                ratelimit_reset_epoch = excluded.ratelimit_reset_epoch,
                consecutive_failures = 0,
                authed = excluded.authed
            """,
            (
                source_uri,
                page_key,
                etag,
                last_modified,
                time.time(),
                ratelimit_remaining,
                ratelimit_reset_epoch,
                int(authed),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def mark_failure(
    db_path: Path,
    source_uri: str,
    page_key: str = "",
    *,
    authed: bool = False,
    ratelimit_remaining: int | None = None,
    ratelimit_reset_epoch: int | None = None,
) -> int:
    state = get_source_state(db_path, source_uri, page_key)
    failures = state.consecutive_failures + 1
    conn = open_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO source_tracking (
                source_uri, page_key, last_polled_epoch, ratelimit_remaining,
                ratelimit_reset_epoch, consecutive_failures, authed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_uri, page_key) DO UPDATE SET
                last_polled_epoch = excluded.last_polled_epoch,
                ratelimit_remaining = excluded.ratelimit_remaining,
                ratelimit_reset_epoch = excluded.ratelimit_reset_epoch,
                consecutive_failures = excluded.consecutive_failures,
                authed = excluded.authed
            """,
            (
                source_uri,
                page_key,
                time.time(),
                ratelimit_remaining,
                ratelimit_reset_epoch,
                failures,
                int(authed),
            ),
        )
        conn.commit()
        return failures
    finally:
        conn.close()


def insert_raw_event_index(
    db_path: Path,
    *,
    source_uri: str,
    event_kind: str,
    payload_path: str,
    payload_sha256: str,
    content_hash: str,
) -> bool:
    conn = open_connection(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO raw_event_index (
                event_id, source_uri, event_kind, payload_path,
                payload_sha256, captured_at_epoch, content_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                source_uri,
                event_kind,
                payload_path,
                payload_sha256,
                time.time(),
                content_hash,
            ),
        )
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()


def raw_event_exists(db_path: Path, *, source_uri: str, content_hash: str) -> bool:
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT 1 FROM raw_event_index
            WHERE source_uri = ? AND content_hash = ?
            """,
            (source_uri, content_hash),
        ).fetchone()
        return row is not None
    finally:
        conn.close()
