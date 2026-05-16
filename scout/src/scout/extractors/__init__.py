from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import json
import time

import structlog

from scout.config import ScoutSettings
from scout.storage.db import open_connection
from scout.extractors.trafilatura_ext import extract_markdown

logger = structlog.get_logger()


SUPPORTED_EVENT_KINDS = {
    "github.commits",
    "github_release",
    "github_readme",
    "rss.entry",
    "rss_item",
    "web_page",
}


def _load_raw_event(data_dir: Path, payload_path: str, payload_sha256: str) -> dict | None:
    full_path = data_dir / payload_path
    if not full_path.exists():
        return None
    for line in full_path.read_text(encoding="utf-8").splitlines():
        candidate_sha = hashlib.sha256((line + "\n").encode("utf-8")).hexdigest()
        if candidate_sha == payload_sha256:
            return json.loads(line)
    return None


def _artifact_path(data_dir: Path, source_uri: str, event_id: str, suffix: str = ".md") -> Path:
    host = (urlparse(source_uri).hostname or source_uri.split("://", 1)[0]).replace(":", "_")
    out_dir = data_dir / "extracted" / host
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{event_id}{suffix}"


def _write_rss_artifact(data_dir: Path, event_id: str, source_uri: str, payload: dict) -> tuple[Path, dict]:
    out_path = _artifact_path(data_dir, source_uri, event_id)
    title = payload.get("title") or "Untitled"
    link = payload.get("link") or ""
    published = payload.get("published") or ""
    summary = payload.get("summary") or ""
    content = f"# {title}\n\nSource: {link}\n\nPublished: {published}\n\n{summary}\n"
    out_path.write_text(content, encoding="utf-8")
    return out_path, {"chars": len(content), "kind": "rss_markdown"}


def _write_github_commits_artifact(
    data_dir: Path,
    event_id: str,
    source_uri: str,
    payload: dict,
) -> tuple[Path, dict]:
    out_path = _artifact_path(data_dir, source_uri, event_id)
    body = payload.get("body")
    commits = body if isinstance(body, list) else []
    lines = [f"# GitHub commits: {source_uri}", ""]
    for commit in commits[:50]:
        sha = str(commit.get("sha", ""))[:12]
        commit_info = commit.get("commit") if isinstance(commit, dict) else {}
        message = ""
        author = ""
        if isinstance(commit_info, dict):
            message = str(commit_info.get("message", "")).splitlines()[0]
            author_info = commit_info.get("author") or {}
            if isinstance(author_info, dict):
                author = str(author_info.get("name", ""))
        lines.append(f"- `{sha}` {message}")
        if author:
            lines.append(f"  - author: {author}")
    content = "\n".join(lines).strip() + "\n"
    out_path.write_text(content, encoding="utf-8")
    return out_path, {"chars": len(content), "commits": len(commits), "kind": "github_commits_markdown"}


def _write_readme_artifact(
    data_dir: Path,
    event_id: str,
    source_uri: str,
    payload: dict,
) -> tuple[Path | None, dict]:
    body = payload.get("body")
    if not isinstance(body, str):
        return None, {"reason": "missing_body"}
    out_path = _artifact_path(data_dir, source_uri, event_id)
    out_path.write_text(body, encoding="utf-8")
    return out_path, {"chars": len(body), "kind": "github_readme_markdown"}


def _write_web_artifact(
    data_dir: Path,
    event_id: str,
    source_uri: str,
    payload: dict,
) -> tuple[Path | None, dict]:
    raw_html = payload.get("raw_html") or payload.get("html") or payload.get("body")
    if not isinstance(raw_html, str):
        return None, {"reason": "missing_html"}
    path, metadata = extract_markdown(raw_html, source_uri, data_dir)
    if path is None:
        return None, metadata
    final_path = _artifact_path(data_dir, source_uri, event_id)
    final_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return final_path, metadata | {"kind": "web_markdown"}


def _record_artifact(
    settings: ScoutSettings,
    *,
    event_id: str,
    source_uri: str,
    event_kind: str,
    artifact_path: Path,
    metadata: dict,
) -> None:
    conn = open_connection(settings.database_path)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO extracted_artifacts (
                event_id, source_uri, event_kind, artifact_kind, artifact_path,
                metadata_json, extracted_at_epoch
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                source_uri,
                event_kind,
                metadata.get("kind", "markdown"),
                str(artifact_path.relative_to(settings.data_dir)),
                json.dumps(metadata, sort_keys=True),
                time.time(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def process_pending_raw_events(settings: ScoutSettings, storage=None, *, limit: int = 100) -> dict:
    conn = open_connection(settings.database_path)
    try:
        rows = conn.execute(
            """
            SELECT rei.event_id, rei.source_uri, rei.event_kind, rei.payload_path,
                   rei.payload_sha256
            FROM raw_event_index rei
            LEFT JOIN extracted_artifacts ea ON ea.event_id = rei.event_id
            WHERE ea.event_id IS NULL
              AND rei.event_kind IN (?, ?, ?, ?, ?, ?)
            ORDER BY rei.captured_at_epoch ASC
            LIMIT ?
            """,
            (*sorted(SUPPORTED_EVENT_KINDS), limit),
        ).fetchall()
    finally:
        conn.close()

    processed = 0
    skipped = 0
    for row in rows:
        raw_event = _load_raw_event(
            settings.data_dir,
            row["payload_path"],
            row["payload_sha256"],
        )
        if not raw_event:
            skipped += 1
            continue
        payload = raw_event.get("payload") or {}
        event_payload = payload if isinstance(payload, dict) else {"body": payload}
        event_kind = row["event_kind"]
        if event_kind in {"rss.entry", "rss_item"}:
            artifact_path, metadata = _write_rss_artifact(
                settings.data_dir,
                row["event_id"],
                row["source_uri"],
                event_payload,
            )
        elif event_kind == "github.commits":
            artifact_path, metadata = _write_github_commits_artifact(
                settings.data_dir,
                row["event_id"],
                row["source_uri"],
                event_payload,
            )
        elif event_kind == "github_readme":
            artifact_path, metadata = _write_readme_artifact(
                settings.data_dir,
                row["event_id"],
                row["source_uri"],
                event_payload,
            )
        else:
            artifact_path, metadata = _write_web_artifact(
                settings.data_dir,
                row["event_id"],
                row["source_uri"],
                event_payload,
            )
        if artifact_path is None:
            skipped += 1
            logger.warning(
                "raw_event_extraction_skipped",
                event_id=row["event_id"],
                event_kind=event_kind,
                metadata=metadata,
            )
            continue
        _record_artifact(
            settings,
            event_id=row["event_id"],
            source_uri=row["source_uri"],
            event_kind=event_kind,
            artifact_path=artifact_path,
            metadata=metadata,
        )
        processed += 1

    result = {
        "processed": processed,
        "skipped": skipped,
        "checked": len(rows),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("extractor_run_complete", **result)
    return result


def register_extractor_job(scheduler, settings: ScoutSettings) -> None:
    scheduler.add_job(
        process_pending_raw_events,
        "interval",
        minutes=5,
        id="extractors:process_pending_raw_events",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        args=[settings],
    )
