from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import posixpath
import sqlite3
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import uuid

from scout.api.source_trust import classify_source
from scout.sources.models import SourceCandidate, SourceRegistryEntry
from scout.storage.db import open_connection


class SourceRegistryError(RuntimeError):
    pass


CANDIDATE_STATUSES = {
    "recommended",
    "needs_review",
    "stored",
    "rejected",
    "blocked",
    "approved",
}
REGISTRY_STATUSES = {"active", "paused", "disabled"}
TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "spm",
}


def canonicalize_uri(uri: str) -> str:
    raw = uri.strip()
    if not raw:
        raise SourceRegistryError("source URI is required")

    parsed = urlparse(raw)
    scheme = parsed.scheme.lower()
    if scheme == "github":
        parts = [part for part in parsed.path.split("/") if part]
        if parsed.netloc:
            parts.insert(0, parsed.netloc)
        if len(parts) >= 2:
            return _github_repo_uri(parts[0], parts[1])
        return raw.lower().rstrip("/")

    if scheme not in {"http", "https"}:
        return raw.rstrip("/")

    host = (parsed.hostname or "").lower()
    if not host:
        raise SourceRegistryError("source URI host is required")

    path = _clean_path(parsed.path)
    if host in {"github.com", "www.github.com"}:
        parts = [part for part in path.split("/") if part]
        if len(parts) >= 2:
            return _github_repo_uri(parts[0], parts[1])

    query = _clean_query(parsed.query)
    netloc = host
    if parsed.port:
        netloc = f"{host}:{parsed.port}"
    return urlunparse((scheme, netloc, path, "", query, ""))


def upsert_candidate(
    db_path: Path,
    *,
    display_uri: str,
    source_kind: str = "unknown",
    status: str = "needs_review",
    canonical_uri: str | None = None,
    confidence_score: float = 0.5,
    trust_label: str | None = None,
    trust_tier: str | None = None,
    recommendation: str | None = None,
    discovered_from_uri: str | None = None,
    discovered_from_event_id: str | None = None,
    discovered_from_packet_id: str | None = None,
    reason_codes: list[str] | None = None,
    explanation: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> SourceCandidate:
    canonical = canonical_uri or canonicalize_uri(display_uri)
    _validate_candidate_status(status)
    now = _now()
    conn = open_connection(db_path)
    try:
        blocked = conn.execute(
            "SELECT reason FROM blocked_sources WHERE canonical_uri = ?",
            (canonical,),
        ).fetchone()
        active = conn.execute(
            "SELECT 1 FROM source_registry WHERE canonical_uri = ? AND status = 'active'",
            (canonical,),
        ).fetchone()
        effective_status = "blocked" if blocked else "approved" if active else status
        blocked_reason = blocked["reason"] if blocked else None
        existing = conn.execute(
            "SELECT * FROM source_candidates WHERE canonical_uri = ?",
            (canonical,),
        ).fetchone()
        if existing:
            effective_status = _merge_candidate_status(existing["status"], effective_status)
            conn.execute(
                """
                UPDATE source_candidates
                SET display_uri = ?,
                    source_kind = ?,
                    status = ?,
                    confidence_score = ?,
                    trust_label = ?,
                    trust_tier = ?,
                    recommendation = ?,
                    discovered_from_uri = COALESCE(?, discovered_from_uri),
                    discovered_from_event_id = COALESCE(?, discovered_from_event_id),
                    discovered_from_packet_id = COALESCE(?, discovered_from_packet_id),
                    reason_codes_json = ?,
                    explanation = ?,
                    last_seen_at = ?,
                    blocked_reason = COALESCE(?, blocked_reason),
                    metadata_json = ?
                WHERE canonical_uri = ?
                """,
                (
                    display_uri,
                    source_kind,
                    effective_status,
                    confidence_score,
                    trust_label,
                    trust_tier,
                    recommendation,
                    discovered_from_uri,
                    discovered_from_event_id,
                    discovered_from_packet_id,
                    _json_list(reason_codes),
                    explanation,
                    now,
                    blocked_reason,
                    _json_object(metadata),
                    canonical,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO source_candidates (
                    candidate_id, canonical_uri, display_uri, source_kind, status,
                    confidence_score, trust_label, trust_tier, recommendation,
                    discovered_from_uri, discovered_from_event_id,
                    discovered_from_packet_id, reason_codes_json, explanation,
                    first_seen_at, last_seen_at, blocked_reason, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    canonical,
                    display_uri,
                    source_kind,
                    effective_status,
                    confidence_score,
                    trust_label,
                    trust_tier,
                    recommendation,
                    discovered_from_uri,
                    discovered_from_event_id,
                    discovered_from_packet_id,
                    _json_list(reason_codes),
                    explanation,
                    now,
                    now,
                    blocked_reason,
                    _json_object(metadata),
                ),
            )
        conn.commit()
        return _get_candidate_by_canonical(conn, canonical)
    finally:
        conn.close()


def list_candidates(
    db_path: Path,
    *,
    status: str | None = None,
    limit: int = 50,
) -> list[SourceCandidate]:
    if status is not None:
        _validate_candidate_status(status)
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
            FROM source_candidates
            {where}
            ORDER BY confidence_score DESC, last_seen_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [SourceCandidate.from_row(row) for row in rows]
    finally:
        conn.close()


def candidate_counts(db_path: Path) -> dict[str, int]:
    counts = {status: 0 for status in CANDIDATE_STATUSES}
    conn = open_connection(db_path)
    try:
        for row in conn.execute(
            "SELECT status, COUNT(*) AS count FROM source_candidates GROUP BY status"
        ).fetchall():
            counts[row["status"]] = row["count"]
        return counts
    finally:
        conn.close()


def get_candidate(db_path: Path, candidate_id: str) -> SourceCandidate | None:
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM source_candidates WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        return SourceCandidate.from_row(row) if row else None
    finally:
        conn.close()


def approve_candidate(
    db_path: Path,
    candidate_id: str,
    *,
    approved_by: str = "manual-review",
    poll_interval_minutes: int | None = None,
) -> SourceRegistryEntry:
    now = _now()
    conn = open_connection(db_path)
    try:
        candidate = conn.execute(
            "SELECT * FROM source_candidates WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        if not candidate:
            raise SourceRegistryError("source candidate not found")
        if candidate["status"] == "blocked" or _is_blocked(conn, candidate["canonical_uri"]):
            raise SourceRegistryError("blocked source candidate cannot be approved")

        trust_label = candidate["trust_label"]
        trust_tier = candidate["trust_tier"]
        if not trust_label or not trust_tier:
            trust = classify_source(candidate["canonical_uri"])
            trust_label = trust_label or trust.trust_label
            trust_tier = trust_tier or trust.trust_tier

        existing = conn.execute(
            "SELECT source_id, created_at FROM source_registry WHERE canonical_uri = ?",
            (candidate["canonical_uri"],),
        ).fetchone()
        source_id = existing["source_id"] if existing else str(uuid.uuid4())
        created_at = existing["created_at"] if existing else now
        conn.execute(
            """
            INSERT INTO source_registry (
                source_id, canonical_uri, display_uri, source_kind, trust_label,
                trust_tier, status, poll_interval_minutes, approved_at,
                approved_by, created_at, updated_at, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)
            ON CONFLICT(canonical_uri) DO UPDATE SET
                display_uri = excluded.display_uri,
                source_kind = excluded.source_kind,
                trust_label = excluded.trust_label,
                trust_tier = excluded.trust_tier,
                status = 'active',
                poll_interval_minutes = excluded.poll_interval_minutes,
                approved_at = excluded.approved_at,
                approved_by = excluded.approved_by,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json
            """,
            (
                source_id,
                candidate["canonical_uri"],
                candidate["display_uri"],
                candidate["source_kind"],
                trust_label,
                trust_tier,
                poll_interval_minutes,
                now,
                approved_by,
                created_at,
                now,
                candidate["metadata_json"],
            ),
        )
        conn.execute(
            """
            UPDATE source_candidates
            SET status = 'approved',
                reviewed_at = ?,
                reviewed_by = ?
            WHERE candidate_id = ?
            """,
            (now, approved_by, candidate_id),
        )
        conn.commit()
        return _get_registry_by_canonical(conn, candidate["canonical_uri"])
    finally:
        conn.close()


def reject_candidate(
    db_path: Path,
    candidate_id: str,
    *,
    reason: str,
    reviewed_by: str = "manual-review",
) -> SourceCandidate:
    return _review_candidate(
        db_path,
        candidate_id,
        status="rejected",
        reason_column="rejection_reason",
        reason=reason,
        reviewed_by=reviewed_by,
    )


def block_candidate(
    db_path: Path,
    candidate_id: str,
    *,
    reason: str,
    blocked_by: str = "manual-review",
) -> SourceCandidate:
    now = _now()
    conn = open_connection(db_path)
    try:
        candidate = conn.execute(
            "SELECT * FROM source_candidates WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        if not candidate:
            raise SourceRegistryError("source candidate not found")
        conn.execute(
            """
            INSERT INTO blocked_sources (
                canonical_uri, reason, blocked_at, blocked_by, metadata_json
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(canonical_uri) DO UPDATE SET
                reason = excluded.reason,
                blocked_at = excluded.blocked_at,
                blocked_by = excluded.blocked_by,
                metadata_json = excluded.metadata_json
            """,
            (
                candidate["canonical_uri"],
                reason,
                now,
                blocked_by,
                candidate["metadata_json"],
            ),
        )
        conn.execute(
            """
            UPDATE source_candidates
            SET status = 'blocked',
                reviewed_at = ?,
                reviewed_by = ?,
                blocked_reason = ?
            WHERE candidate_id = ?
            """,
            (now, blocked_by, reason, candidate_id),
        )
        conn.commit()
        return _get_candidate(conn, candidate_id)
    finally:
        conn.close()


def list_registry_entries(
    db_path: Path,
    *,
    status: str | None = None,
) -> list[SourceRegistryEntry]:
    if status is not None and status not in REGISTRY_STATUSES:
        raise SourceRegistryError(f"unsupported source registry status: {status}")
    conn = open_connection(db_path)
    try:
        params: list[Any] = []
        where = ""
        if status:
            where = "WHERE status = ?"
            params.append(status)
        rows = conn.execute(
            f"""
            SELECT *
            FROM source_registry
            {where}
            ORDER BY approved_at DESC, created_at DESC
            """,
            params,
        ).fetchall()
        return [SourceRegistryEntry.from_row(row) for row in rows]
    finally:
        conn.close()


def record_discovery_event(
    db_path: Path,
    *,
    candidate_id: str,
    discovery_kind: str,
    canonical_uri: str,
    source_uri: str | None = None,
    artifact_path: str | None = None,
    raw_url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    event_id = str(uuid.uuid4())
    conn = open_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO source_discovery_events (
                event_id, candidate_id, discovery_kind, source_uri, artifact_path,
                raw_url, canonical_uri, created_at, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                candidate_id,
                discovery_kind,
                source_uri,
                artifact_path,
                raw_url,
                canonical_uri,
                _now(),
                _json_object(metadata),
            ),
        )
        conn.commit()
        return event_id
    finally:
        conn.close()


def _review_candidate(
    db_path: Path,
    candidate_id: str,
    *,
    status: str,
    reason_column: str,
    reason: str,
    reviewed_by: str,
) -> SourceCandidate:
    now = _now()
    conn = open_connection(db_path)
    try:
        cursor = conn.execute(
            f"""
            UPDATE source_candidates
            SET status = ?,
                reviewed_at = ?,
                reviewed_by = ?,
                {reason_column} = ?
            WHERE candidate_id = ?
            """,
            (status, now, reviewed_by, reason, candidate_id),
        )
        if cursor.rowcount != 1:
            raise SourceRegistryError("source candidate not found")
        conn.commit()
        return _get_candidate(conn, candidate_id)
    finally:
        conn.close()


def _get_candidate(conn: sqlite3.Connection, candidate_id: str) -> SourceCandidate:
    row = conn.execute(
        "SELECT * FROM source_candidates WHERE candidate_id = ?",
        (candidate_id,),
    ).fetchone()
    if not row:
        raise SourceRegistryError("source candidate not found")
    return SourceCandidate.from_row(row)


def _get_candidate_by_canonical(
    conn: sqlite3.Connection,
    canonical_uri: str,
) -> SourceCandidate:
    row = conn.execute(
        "SELECT * FROM source_candidates WHERE canonical_uri = ?",
        (canonical_uri,),
    ).fetchone()
    if not row:
        raise SourceRegistryError("source candidate not found")
    return SourceCandidate.from_row(row)


def _get_registry_by_canonical(
    conn: sqlite3.Connection,
    canonical_uri: str,
) -> SourceRegistryEntry:
    row = conn.execute(
        "SELECT * FROM source_registry WHERE canonical_uri = ?",
        (canonical_uri,),
    ).fetchone()
    if not row:
        raise SourceRegistryError("source registry entry not found")
    return SourceRegistryEntry.from_row(row)


def _is_blocked(conn: sqlite3.Connection, canonical_uri: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM blocked_sources WHERE canonical_uri = ?",
        (canonical_uri,),
    ).fetchone()
    return row is not None


def _merge_candidate_status(current: str, incoming: str) -> str:
    if current in {"rejected", "blocked", "approved"}:
        return current
    return incoming


def _validate_candidate_status(status: str) -> None:
    if status not in CANDIDATE_STATUSES:
        raise SourceRegistryError(f"unsupported source candidate status: {status}")


def _github_repo_uri(owner: str, repo: str) -> str:
    normalized_repo = repo.removesuffix(".git").lower()
    return f"github://{owner.lower()}/{normalized_repo}"


def _clean_path(path: str) -> str:
    if not path or path == "/":
        return ""
    cleaned = posixpath.normpath(path)
    if path.endswith("/") and cleaned != "/":
        cleaned = cleaned.rstrip("/")
    return cleaned if cleaned.startswith("/") else f"/{cleaned}"


def _clean_query(query: str) -> str:
    pairs = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in TRACKING_QUERY_PARAMS:
            continue
        if any(lowered.startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES):
            continue
        pairs.append((key, value))
    return urlencode(sorted(pairs))


def _json_object(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {}, sort_keys=True)


def _json_list(value: list[str] | None) -> str:
    return json.dumps(value or [])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
