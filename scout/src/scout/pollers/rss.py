from __future__ import annotations

from calendar import timegm
from datetime import datetime, timezone
from email.utils import formatdate
import hashlib
import re

import feedparser
import httpx
import structlog

from scout.config import ScoutSettings
from scout.pollers.models import PollResult
from scout.storage.jsonl import append_raw_event
from scout.storage.source_tracking import (
    get_source_state,
    insert_raw_event_index,
    mark_failure,
    mark_success,
    raw_event_exists,
)

logger = structlog.get_logger()


def _entry_timestamp(entry) -> str:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if parsed:
        return datetime.fromtimestamp(timegm(parsed), tz=timezone.utc).isoformat()
    return getattr(entry, "published", None) or getattr(entry, "updated", None) or ""


def _feed_modified(feed) -> str | None:
    modified = getattr(feed, "modified", None)
    if modified:
        return str(modified)
    parsed = getattr(feed, "modified_parsed", None)
    if parsed:
        return formatdate(timegm(parsed), usegmt=True)
    return None


def _excluded(entry, regex_exclude: list[str]) -> bool:
    haystack = f"{getattr(entry, 'title', '')}\n{getattr(entry, 'summary', '')}"
    return any(re.search(pattern, haystack) for pattern in regex_exclude)


async def poll_feed(
    url: str,
    *,
    regex_exclude: list[str] | None = None,
    settings: ScoutSettings,
    storage=None,
) -> PollResult:
    source_uri = url
    state = get_source_state(settings.database_path, source_uri)
    headers = {"User-Agent": "SpiritOS-Scout-v0.1"}
    if state.etag:
        headers["If-None-Match"] = state.etag
    elif state.last_modified:
        headers["If-Modified-Since"] = state.last_modified

    try:
        async with httpx.AsyncClient(timeout=settings.fetch_timeout_seconds) as client:
            response = await client.get(url, headers=headers)
        if response.status_code == 304:
            mark_success(
                settings.database_path,
                source_uri,
                "",
                etag=state.etag,
                last_modified=state.last_modified,
            )
            return PollResult(status="not_modified", source_uri=source_uri)
        if response.status_code != 200:
            failures = mark_failure(settings.database_path, source_uri)
            logger.warning(
                "rss_poll_failed",
                source_uri=source_uri,
                status_code=response.status_code,
                consecutive_failures=failures,
            )
            return PollResult(
                status="error",
                source_uri=source_uri,
                reason=f"http_{response.status_code}",
                pause_source=failures >= 3,
            )
        if len(response.content) > settings.fetch_max_bytes:
            failures = mark_failure(settings.database_path, source_uri)
            return PollResult(
                status="error",
                source_uri=source_uri,
                reason="response_too_large",
                pause_source=failures >= 3,
            )

        parsed = feedparser.parse(response.content)
        patterns = regex_exclude or []
        events_added = 0
        for entry in parsed.entries:
            if _excluded(entry, patterns):
                continue
            link = getattr(entry, "link", "")
            timestamp = _entry_timestamp(entry)
            content_hash = hashlib.sha256(f"{link}|{timestamp}".encode("utf-8")).hexdigest()
            if raw_event_exists(
                settings.database_path,
                source_uri=source_uri,
                content_hash=content_hash,
            ):
                continue
            payload = {
                "feed_url": url,
                "title": getattr(entry, "title", ""),
                "link": link,
                "published": timestamp,
                "summary": getattr(entry, "summary", ""),
            }
            rel_path, payload_sha = append_raw_event(
                settings.data_dir,
                source_uri,
                "rss.entry",
                payload,
            )
            if insert_raw_event_index(
                settings.database_path,
                source_uri=source_uri,
                event_kind="rss.entry",
                payload_path=rel_path,
                payload_sha256=payload_sha,
                content_hash=content_hash,
            ):
                events_added += 1

        mark_success(
            settings.database_path,
            source_uri,
            "",
            etag=getattr(parsed, "etag", None) or response.headers.get("etag"),
            last_modified=_feed_modified(parsed.feed) or response.headers.get("last-modified"),
        )
        return PollResult(
            status="updated" if events_added else "not_modified",
            source_uri=source_uri,
            events_added=events_added,
        )
    except (httpx.HTTPError, OSError) as exc:
        failures = mark_failure(settings.database_path, source_uri)
        logger.warning(
            "rss_poll_exception",
            source_uri=source_uri,
            error=str(exc),
            consecutive_failures=failures,
        )
        return PollResult(
            status="error",
            source_uri=source_uri,
            reason=str(exc),
            pause_source=failures >= 3,
        )
