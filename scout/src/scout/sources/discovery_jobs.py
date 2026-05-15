from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
import uuid

from scout.storage.db import open_connection


class DiscoveryJobError(RuntimeError):
    pass


DISCOVERY_JOB_STATUSES = {
    "queued",
    "paused",
    "running",
    "completed",
    "failed",
    "canceled",
}
ACTIVE_DISCOVERY_JOB_STATUSES = {"queued", "paused", "running"}
DEFAULT_MAX_RESULTS = 10
MAX_RESULTS_LIMIT = 50
DEFAULT_BUDGET = 10


@dataclass(frozen=True)
class DiscoveryJob:
    job_id: str
    query: str
    topic_anchor: str | None
    status: str
    max_results: int
    budget: int
    created_at: str
    updated_at: str
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> DiscoveryJob:
        return cls(
            job_id=row["job_id"],
            query=row["query"],
            topic_anchor=row["topic_anchor"],
            status=row["status"],
            max_results=row["max_results"],
            budget=row["budget"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            error=row["error"],
            metadata=_json_object_from_row(row["metadata_json"]),
        )


def create_discovery_job(
    db_path: Path,
    *,
    query: str,
    topic_anchor: str | None = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    budget: int = DEFAULT_BUDGET,
    metadata: dict[str, Any] | None = None,
) -> DiscoveryJob:
    clean_query = query.strip()
    if not clean_query:
        raise DiscoveryJobError("discovery job query is required")
    _validate_limits(max_results=max_results, budget=budget)
    now = _now()
    job_id = str(uuid.uuid4())
    conn = open_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO discovery_jobs (
                job_id, query, topic_anchor, status, max_results, budget,
                created_at, updated_at, metadata_json
            )
            VALUES (?, ?, ?, 'queued', ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                clean_query,
                topic_anchor.strip() if topic_anchor else None,
                max_results,
                budget,
                now,
                now,
                _json_object(metadata),
            ),
        )
        conn.commit()
        return _get_job(conn, job_id)
    finally:
        conn.close()


def list_discovery_jobs(
    db_path: Path,
    *,
    status: str | None = None,
    limit: int = 50,
) -> list[DiscoveryJob]:
    if status is not None:
        _validate_status(status)
    if limit < 1 or limit > 200:
        raise DiscoveryJobError("discovery job limit must be between 1 and 200")
    conn = open_connection(db_path)
    try:
        params: list[Any] = []
        where = ""
        if status:
            where = "WHERE status = ?"
            params.append(status)
        params.append(limit)
        rows = conn.execute(
            f"""
            SELECT *
            FROM discovery_jobs
            {where}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [DiscoveryJob.from_row(row) for row in rows]
    finally:
        conn.close()


def get_discovery_job(db_path: Path, job_id: str) -> DiscoveryJob | None:
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM discovery_jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        return DiscoveryJob.from_row(row) if row else None
    finally:
        conn.close()


def pause_discovery_job(db_path: Path, job_id: str) -> DiscoveryJob:
    return _set_status(db_path, job_id, from_statuses={"queued", "running"}, to_status="paused")


def resume_discovery_job(db_path: Path, job_id: str) -> DiscoveryJob:
    return _set_status(db_path, job_id, from_statuses={"paused"}, to_status="queued")


def cancel_discovery_job(db_path: Path, job_id: str) -> DiscoveryJob:
    return _set_status(
        db_path,
        job_id,
        from_statuses=ACTIVE_DISCOVERY_JOB_STATUSES,
        to_status="canceled",
        finished=True,
    )


def mark_discovery_job_started(db_path: Path, job_id: str) -> DiscoveryJob:
    now = _now()
    conn = open_connection(db_path)
    try:
        cursor = conn.execute(
            """
            UPDATE discovery_jobs
            SET status = 'running',
                started_at = COALESCE(started_at, ?),
                updated_at = ?
            WHERE job_id = ? AND status = 'queued'
            """,
            (now, now, job_id),
        )
        if cursor.rowcount != 1:
            raise DiscoveryJobError("discovery job is not queued")
        conn.commit()
        return _get_job(conn, job_id)
    finally:
        conn.close()


def finish_discovery_job(
    db_path: Path,
    job_id: str,
    *,
    error: str | None = None,
) -> DiscoveryJob:
    now = _now()
    status = "failed" if error else "completed"
    conn = open_connection(db_path)
    try:
        cursor = conn.execute(
            """
            UPDATE discovery_jobs
            SET status = ?,
                finished_at = ?,
                updated_at = ?,
                error = ?
            WHERE job_id = ? AND status = 'running'
            """,
            (status, now, now, error, job_id),
        )
        if cursor.rowcount != 1:
            raise DiscoveryJobError("discovery job is not running")
        conn.commit()
        return _get_job(conn, job_id)
    finally:
        conn.close()


def _set_status(
    db_path: Path,
    job_id: str,
    *,
    from_statuses: set[str],
    to_status: str,
    finished: bool = False,
) -> DiscoveryJob:
    _validate_status(to_status)
    now = _now()
    placeholders = ",".join("?" for _ in from_statuses)
    params: list[Any] = [to_status, now]
    finished_sql = ""
    if finished:
        finished_sql = ", finished_at = ?"
        params.append(now)
    params.extend(sorted(from_statuses))
    params.append(job_id)
    conn = open_connection(db_path)
    try:
        cursor = conn.execute(
            f"""
            UPDATE discovery_jobs
            SET status = ?,
                updated_at = ?
                {finished_sql}
            WHERE status IN ({placeholders}) AND job_id = ?
            """,
            params,
        )
        if cursor.rowcount != 1:
            raise DiscoveryJobError("discovery job status transition is not allowed")
        conn.commit()
        return _get_job(conn, job_id)
    finally:
        conn.close()


def _get_job(conn: sqlite3.Connection, job_id: str) -> DiscoveryJob:
    row = conn.execute(
        "SELECT * FROM discovery_jobs WHERE job_id = ?",
        (job_id,),
    ).fetchone()
    if not row:
        raise DiscoveryJobError("discovery job not found")
    return DiscoveryJob.from_row(row)


def _validate_limits(*, max_results: int, budget: int) -> None:
    if max_results < 1 or max_results > MAX_RESULTS_LIMIT:
        raise DiscoveryJobError("max_results must be between 1 and 50")
    if budget < 1 or budget > MAX_RESULTS_LIMIT:
        raise DiscoveryJobError("budget must be between 1 and 50")


def _validate_status(status: str) -> None:
    if status not in DISCOVERY_JOB_STATUSES:
        raise DiscoveryJobError(f"unsupported discovery job status: {status}")


def _json_object(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {}, sort_keys=True)


def _json_object_from_row(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
