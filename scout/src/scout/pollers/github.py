from __future__ import annotations

from urllib.parse import parse_qs, urlparse
import hashlib
import json
import time

import httpx
import structlog

from scout.config import ScoutSettings
from scout.pollers.models import PollResult
from scout.storage.jsonl import append_raw_event
from scout.storage.source_tracking import (
    get_source_state,
    insert_raw_event_index,
    mark_failure,
    mark_not_modified,
    mark_success,
    raw_event_exists,
)

logger = structlog.get_logger()

GITHUB_API = "https://api.github.com"


def _source_uri(owner: str, repo: str, endpoint: str) -> str:
    return f"github://{owner}/{repo}/{endpoint}"


def _rate_limit(headers: httpx.Headers) -> tuple[int | None, int | None]:
    remaining = headers.get("x-ratelimit-remaining")
    reset = headers.get("x-ratelimit-reset")
    return (
        int(remaining) if remaining and remaining.isdigit() else None,
        int(reset) if reset and reset.isdigit() else None,
    )


def _next_page(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        start = section.find("<")
        end = section.find(">")
        if start != -1 and end != -1 and end > start:
            return section[start + 1 : end]
    return None


def _page_key_from_url(url: str, fallback: int) -> str:
    page = parse_qs(urlparse(url).query).get("page", [""])[0]
    return page or ("" if fallback == 1 else str(fallback))


async def _read_capped(response: httpx.Response, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    async for chunk in response.aiter_bytes():
        size += len(chunk)
        if size > max_bytes:
            raise ValueError("response_too_large")
        chunks.append(chunk)
    return b"".join(chunks)


async def poll_repo(
    owner: str,
    repo: str,
    endpoint: str,
    *,
    settings: ScoutSettings,
    storage=None,
) -> PollResult:
    source_uri = _source_uri(owner, repo, endpoint)
    authed = bool(settings.github_token)
    url: str | None = f"{GITHUB_API}/repos/{owner}/{repo}/{endpoint}?per_page=30"
    page_index = 1
    events_added = 0
    saw_not_modified = False

    headers_base = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "SpiritOS-Scout-v0.1",
    }
    if settings.github_token:
        headers_base["Authorization"] = f"Bearer {settings.github_token}"

    try:
        async with httpx.AsyncClient(timeout=settings.fetch_timeout_seconds) as client:
            while url:
                page_key = _page_key_from_url(url, page_index)
                state = get_source_state(settings.database_path, source_uri, page_key)
                headers = dict(headers_base)
                if state.authed == authed:
                    if state.etag:
                        headers["If-None-Match"] = state.etag
                    elif state.last_modified:
                        headers["If-Modified-Since"] = state.last_modified

                async with client.stream("GET", url, headers=headers) as response:
                    remaining, reset_epoch = _rate_limit(response.headers)
                    if response.status_code == 304:
                        mark_not_modified(
                            settings.database_path,
                            source_uri,
                            page_key,
                            ratelimit_remaining=remaining,
                            ratelimit_reset_epoch=reset_epoch,
                            authed=authed,
                        )
                        saw_not_modified = True
                        break

                    if response.status_code in {401, 403, 404}:
                        failures = mark_failure(
                            settings.database_path,
                            source_uri,
                            page_key,
                            authed=authed,
                            ratelimit_remaining=remaining,
                            ratelimit_reset_epoch=reset_epoch,
                        )
                        reason = f"http_{response.status_code}"
                        logger.warning(
                            "github_poll_failed",
                            source_uri=source_uri,
                            page_key=page_key,
                            status_code=response.status_code,
                            consecutive_failures=failures,
                        )
                        return PollResult(
                            status="error",
                            source_uri=source_uri,
                            reason=reason,
                            pause_source=failures >= 3,
                        )

                    if response.status_code != 200:
                        failures = mark_failure(
                            settings.database_path,
                            source_uri,
                            page_key,
                            authed=authed,
                            ratelimit_remaining=remaining,
                            ratelimit_reset_epoch=reset_epoch,
                        )
                        return PollResult(
                            status="error",
                            source_uri=source_uri,
                            reason=f"http_{response.status_code}",
                            pause_source=failures >= 3,
                        )

                    body = await _read_capped(response, settings.fetch_max_bytes)
                    content_hash = hashlib.sha256(body).hexdigest()
                    if not raw_event_exists(
                        settings.database_path,
                        source_uri=source_uri,
                        content_hash=content_hash,
                    ):
                        text = body.decode(response.encoding or "utf-8", errors="replace")
                        try:
                            parsed_body = json.loads(text)
                        except json.JSONDecodeError:
                            parsed_body = text
                        rel_path, payload_sha = append_raw_event(
                            settings.data_dir,
                            source_uri,
                            f"github.{endpoint}",
                            {
                                "owner": owner,
                                "repo": repo,
                                "endpoint": endpoint,
                                "page_key": page_key,
                                "status_code": response.status_code,
                                "etag": response.headers.get("etag"),
                                "last_modified": response.headers.get("last-modified"),
                                "ratelimit_remaining": remaining,
                                "ratelimit_reset_epoch": reset_epoch,
                                "body": parsed_body,
                            },
                        )
                        if insert_raw_event_index(
                            settings.database_path,
                            source_uri=source_uri,
                            event_kind=f"github.{endpoint}",
                            payload_path=rel_path,
                            payload_sha256=payload_sha,
                            content_hash=content_hash,
                        ):
                            events_added += 1

                    mark_success(
                        settings.database_path,
                        source_uri,
                        page_key,
                        etag=response.headers.get("etag"),
                        last_modified=response.headers.get("last-modified"),
                        ratelimit_remaining=remaining,
                        ratelimit_reset_epoch=reset_epoch,
                        authed=authed,
                    )

                    if remaining is not None and remaining < settings.github_ratelimit_floor:
                        next_run = (reset_epoch or int(time.time() + 3600)) + 5
                        logger.warning(
                            "github_ratelimit_floor_reached",
                            source_uri=source_uri,
                            remaining=remaining,
                            next_run_epoch=next_run,
                        )
                        return PollResult(
                            status="updated" if events_added else "not_modified",
                            source_uri=source_uri,
                            events_added=events_added,
                            next_run_epoch=next_run,
                        )

                    url = _next_page(response.headers.get("link"))
                    page_index += 1

        status = "updated" if events_added else "not_modified"
        if saw_not_modified and events_added:
            status = "updated"
        return PollResult(status=status, source_uri=source_uri, events_added=events_added)
    except (httpx.HTTPError, ValueError) as exc:
        failures = mark_failure(settings.database_path, source_uri, authed=authed)
        logger.warning(
            "github_poll_exception",
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
