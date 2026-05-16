from __future__ import annotations

from dataclasses import dataclass
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from scout.config import ScoutSettings
from scout.sources.scoring import score_candidate
from scout.sources.storage import (
    canonicalize_uri,
    record_discovery_event,
    upsert_candidate,
)
from scout.storage.db import open_connection


MARKDOWN_LINK_RE = re.compile(r"\[[^\]]{0,200}\]\((?P<url>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
BARE_URL_RE = re.compile(r"https?://[^\s<>\]\)\"']+")
IMAGE_EXTENSIONS = {
    ".apng",
    ".avif",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".webp",
}
DENY_HOSTS = {
    "facebook.com",
    "www.facebook.com",
    "twitter.com",
    "www.twitter.com",
    "x.com",
    "www.x.com",
    "linkedin.com",
    "www.linkedin.com",
}
DENY_PATH_PARTS = {
    "/share",
    "/intent/",
    "/sharer",
}


@dataclass(frozen=True)
class DiscoveryUrl:
    raw_url: str
    canonical_uri: str
    source_kind: str
    reason_codes: list[str]


def run_artifact_discovery(
    settings: ScoutSettings,
    *,
    limit: int = 50,
) -> dict:
    limit = max(1, min(limit, 50))
    rows = _artifact_rows(settings.database_path, limit=limit)
    scanned_artifacts = 0
    missing_artifacts = 0
    candidates_seen = 0
    candidates_created = 0
    discovery_events = 0
    skipped_urls = 0
    errors: list[dict] = []

    for row in rows:
        try:
            artifact_path = _resolve_artifact_path(settings.data_dir, row["artifact_path"])
        except ValueError as exc:
            errors.append({"artifact_path": row["artifact_path"], "error": str(exc)})
            continue
        if not artifact_path.exists():
            missing_artifacts += 1
            continue
        scanned_artifacts += 1
        text = artifact_path.read_text(encoding="utf-8", errors="replace")
        discovered = extract_candidate_urls(text)
        skipped_urls += max(0, len(_raw_urls(text)) - len(discovered))
        for item in discovered:
            if _is_already_active(settings.database_path, item.canonical_uri):
                skipped_urls += 1
                continue
            before_exists = _candidate_exists(settings.database_path, item.canonical_uri)
            score = score_candidate(
                settings.database_path,
                canonical_uri=item.canonical_uri,
                source_kind=item.source_kind,
                discovered_from_uri=row["source_uri"],
            )
            candidate = upsert_candidate(
                settings.database_path,
                display_uri=item.raw_url,
                canonical_uri=item.canonical_uri,
                source_kind=item.source_kind,
                status=score.status,
                confidence_score=score.confidence_score,
                trust_label=score.trust_label,
                trust_tier=score.trust_tier,
                recommendation=score.recommendation,
                discovered_from_uri=row["source_uri"],
                discovered_from_event_id=row["event_id"],
                reason_codes=item.reason_codes
                + ["discovered_from_artifact"]
                + score.reason_codes,
                explanation=score.explanation,
                metadata={
                    "artifact_kind": row["artifact_kind"],
                    "artifact_path": row["artifact_path"],
                },
            )
            candidates_seen += 1
            candidates_created += 0 if before_exists else 1
            record_discovery_event(
                settings.database_path,
                candidate_id=candidate.candidate_id,
                discovery_kind="artifact_link",
                source_uri=row["source_uri"],
                artifact_path=row["artifact_path"],
                raw_url=item.raw_url,
                canonical_uri=item.canonical_uri,
                metadata={"artifact_kind": row["artifact_kind"]},
            )
            discovery_events += 1

    return {
        "checked_artifacts": len(rows),
        "scanned_artifacts": scanned_artifacts,
        "missing_artifacts": missing_artifacts,
        "candidates_seen": candidates_seen,
        "candidates_created": candidates_created,
        "discovery_events": discovery_events,
        "skipped_urls": skipped_urls,
        "errors": errors,
    }


def extract_candidate_urls(text: str) -> list[DiscoveryUrl]:
    candidates: list[DiscoveryUrl] = []
    seen: set[str] = set()
    for raw_url in _raw_urls(text):
        try:
            normalized = _clean_raw_url(raw_url)
            if not _is_allowed_url(normalized):
                continue
            canonical = canonicalize_uri(normalized)
        except Exception:
            continue
        if canonical in seen:
            continue
        seen.add(canonical)
        candidates.append(
            DiscoveryUrl(
                raw_url=normalized,
                canonical_uri=canonical,
                source_kind=classify_source_kind(canonical),
                reason_codes=["canonical_uri_valid"],
            )
        )
    return candidates


def classify_source_kind(canonical_uri: str) -> str:
    if canonical_uri.startswith("github://"):
        return "github_repo"
    parsed = urlparse(canonical_uri)
    host = parsed.hostname or ""
    path = parsed.path.lower()
    if "changelog" in path:
        return "changelog"
    if "release" in path or "releases" in path:
        return "release_feed"
    if host.startswith("docs.") or "/docs" in path:
        return "docs_page"
    if "blog" in host or "/blog" in path:
        return "blog"
    return "unknown"


def _artifact_rows(db_path: Path, *, limit: int) -> list[sqlite3.Row]:
    conn = open_connection(db_path)
    try:
        return conn.execute(
            """
            SELECT event_id, source_uri, event_kind, artifact_kind, artifact_path
            FROM extracted_artifacts
            WHERE artifact_kind LIKE '%markdown%'
               OR artifact_path LIKE '%.md'
            ORDER BY extracted_at_epoch DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()


def _resolve_artifact_path(data_dir: Path, artifact_path: str) -> Path:
    root = data_dir.resolve()
    path = Path(artifact_path)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"artifact path escapes data_dir: {artifact_path}") from exc
    return resolved


def _raw_urls(text: str) -> list[str]:
    urls: list[str] = []
    urls.extend(match.group("url") for match in MARKDOWN_LINK_RE.finditer(text))
    urls.extend(match.group(0) for match in BARE_URL_RE.finditer(text))
    return urls


def _clean_raw_url(raw_url: str) -> str:
    return raw_url.strip().strip(".,;:!?)]}'\"")


def _is_allowed_url(raw_url: str) -> bool:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    if parsed.fragment and not parsed.path:
        return False
    host = (parsed.hostname or "").lower()
    if host in DENY_HOSTS:
        return False
    lowered_path = parsed.path.lower()
    if any(part in lowered_path for part in DENY_PATH_PARTS):
        return False
    if Path(lowered_path).suffix in IMAGE_EXTENSIONS:
        return False
    return True


def _is_already_active(db_path: Path, canonical_uri: str) -> bool:
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM source_registry WHERE canonical_uri = ? AND status = 'active'",
            (canonical_uri,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _candidate_exists(db_path: Path, canonical_uri: str) -> bool:
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM source_candidates WHERE canonical_uri = ?",
            (canonical_uri,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()
