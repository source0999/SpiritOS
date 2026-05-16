from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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
STALE_QUEUED_AFTER = timedelta(hours=6)
NOISY_QUERY_TERMS = {
    "coupon",
    "crack",
    "free download",
    "mirror spam",
    "spam",
}


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


@dataclass(frozen=True)
class DiscoveryJobBudget:
    daily_limit: int
    used_today: int
    remaining_today: int
    can_create_job: bool
    blocked_reason: str | None
    next_reset_hint: str
    queued_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int


@dataclass(frozen=True)
class DiscoveryJobComputedState:
    computed_status: str
    attention_label: str | None
    safe_next_action: str


def create_discovery_job(
    db_path: Path,
    *,
    query: str,
    topic_anchor: str | None = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    budget: int = DEFAULT_BUDGET,
    max_jobs_per_day: int | None = None,
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
        if max_jobs_per_day is not None:
            _enforce_daily_job_limit(conn, max_jobs_per_day=max_jobs_per_day, now=now)
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


def get_discovery_job_budget(
    db_path: Path,
    *,
    max_jobs_per_day: int,
) -> DiscoveryJobBudget:
    now = _now()
    day_start = _utc_day_start(now)
    conn = open_connection(db_path)
    try:
        used_today_row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM discovery_jobs
            WHERE created_at >= ?
            """,
            (day_start.isoformat(),),
        ).fetchone()
        status_counts = {
            row["status"]: row["count"]
            for row in conn.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM discovery_jobs
                GROUP BY status
                """
            ).fetchall()
        }
    finally:
        conn.close()

    used_today = used_today_row["count"] if used_today_row else 0
    if max_jobs_per_day < 1:
        return DiscoveryJobBudget(
            daily_limit=max_jobs_per_day,
            used_today=used_today,
            remaining_today=0,
            can_create_job=False,
            blocked_reason="daily_limit_invalid",
            next_reset_hint="next UTC day",
            queued_jobs=status_counts.get("queued", 0),
            running_jobs=status_counts.get("running", 0),
            completed_jobs=status_counts.get("completed", 0),
            failed_jobs=status_counts.get("failed", 0),
        )

    remaining_today = max(max_jobs_per_day - used_today, 0)
    return DiscoveryJobBudget(
        daily_limit=max_jobs_per_day,
        used_today=used_today,
        remaining_today=remaining_today,
        can_create_job=remaining_today > 0,
        blocked_reason="daily_limit_reached" if remaining_today == 0 else None,
        next_reset_hint="next UTC day",
        queued_jobs=status_counts.get("queued", 0),
        running_jobs=status_counts.get("running", 0),
        completed_jobs=status_counts.get("completed", 0),
        failed_jobs=status_counts.get("failed", 0),
    )


def classify_discovery_job_states(
    jobs: list[DiscoveryJob],
    *,
    budget: DiscoveryJobBudget | None = None,
    now: str | None = None,
) -> dict[str, DiscoveryJobComputedState]:
    current_time = datetime.fromisoformat(now or _now()).astimezone(timezone.utc)
    duplicate_keys = _duplicate_queued_keys(jobs)
    return {
        job.job_id: _classify_discovery_job_state(
            job,
            duplicate_keys=duplicate_keys,
            budget=budget,
            current_time=current_time,
        )
        for job in jobs
    }


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


def _enforce_daily_job_limit(
    conn: sqlite3.Connection,
    *,
    max_jobs_per_day: int,
    now: str,
) -> None:
    if max_jobs_per_day < 1:
        raise DiscoveryJobError("discovery job daily limit must be at least 1")
    day_start = _utc_day_start(now)
    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM discovery_jobs
        WHERE created_at >= ?
        """,
        (day_start.isoformat(),),
    ).fetchone()
    if row["count"] >= max_jobs_per_day:
        raise DiscoveryJobError("discovery job daily limit reached")


def _validate_status(status: str) -> None:
    if status not in DISCOVERY_JOB_STATUSES:
        raise DiscoveryJobError(f"unsupported discovery job status: {status}")


def _classify_discovery_job_state(
    job: DiscoveryJob,
    *,
    duplicate_keys: set[tuple[str, str | None]],
    budget: DiscoveryJobBudget | None,
    current_time: datetime,
) -> DiscoveryJobComputedState:
    if job.status == "running":
        return DiscoveryJobComputedState("running", None, "wait_for_completion")
    if job.status == "completed":
        return DiscoveryJobComputedState("completed", None, "inspect_results")
    if job.status == "failed":
        return DiscoveryJobComputedState("failed", "Discovery job failed", "inspect_error")
    if job.status == "paused":
        return DiscoveryJobComputedState("paused", "Discovery job paused", "resume_or_cancel")
    if job.status == "canceled":
        return DiscoveryJobComputedState("canceled", None, "none")
    if job.status != "queued":
        return DiscoveryJobComputedState(job.status, None, "inspect_job")

    normalized_key = _job_duplicate_key(job)
    if _is_noisy_query(job.query):
        return DiscoveryJobComputedState(
            "spam_test",
            "Noisy test search",
            "cancel_or_keep_for_test_evidence",
        )
    if normalized_key in duplicate_keys:
        return DiscoveryJobComputedState(
            "duplicate_queued",
            "Duplicate queued search",
            "cancel_duplicate_or_wait",
        )
    if _is_stale_queued(job, current_time=current_time):
        return DiscoveryJobComputedState(
            "stale_queued",
            "Stale queued search",
            "cancel_stale_or_investigate_worker",
        )
    if budget is not None and not budget.can_create_job:
        return DiscoveryJobComputedState(
            "blocked_by_budget",
            "Discovery budget exhausted",
            "wait_for_budget_reset",
        )
    return DiscoveryJobComputedState("queued", None, "wait_for_worker")


def _duplicate_queued_keys(jobs: list[DiscoveryJob]) -> set[tuple[str, str | None]]:
    counts: dict[tuple[str, str | None], int] = {}
    for job in jobs:
        if job.status != "queued":
            continue
        key = _job_duplicate_key(job)
        counts[key] = counts.get(key, 0) + 1
    return {key for key, count in counts.items() if count > 1}


def _job_duplicate_key(job: DiscoveryJob) -> tuple[str, str | None]:
    return (_normalize_text(job.query) or "", _normalize_text(job.topic_anchor))


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.strip().lower().split())


def _is_noisy_query(query: str) -> bool:
    normalized = _normalize_text(query) or ""
    return any(term in normalized for term in NOISY_QUERY_TERMS)


def _is_stale_queued(job: DiscoveryJob, *, current_time: datetime) -> bool:
    if job.started_at is not None:
        return False
    created_at = datetime.fromisoformat(job.created_at).astimezone(timezone.utc)
    return current_time - created_at >= STALE_QUEUED_AFTER


def _json_object(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {}, sort_keys=True)


def _json_object_from_row(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def _utc_day_start(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
