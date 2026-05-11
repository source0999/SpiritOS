from __future__ import annotations

import os
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

DEFAULT_SEARXNG_TIMEOUT_SECONDS = 10.0


async def run_local_research_preview(query: str, max_results: int = 6) -> list[dict[str, str]]:
    normalized_query = query.strip()
    if not normalized_query:
        return []

    searxng_url = os.environ.get("SEARXNG_URL", "").strip()
    if not searxng_url:
        return []

    bounded_max_results = min(max(1, int(max_results)), 12)
    timeout_seconds = _read_timeout_seconds()
    search_url = urljoin(searxng_url.rstrip("/") + "/", "search")

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
            response = await client.get(
                search_url,
                params={"q": normalized_query, "format": "json"},
                headers={
                    "Accept": "application/json",
                    "User-Agent": os.environ.get(
                        "WEB_SEARCH_USER_AGENT",
                        "SpiritOSLocalSearch/0.1",
                    ),
                },
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        return []

    raw_results = payload.get("results", []) if isinstance(payload, dict) else []
    if not isinstance(raw_results, list):
        return []

    return _normalize_sources(raw_results, bounded_max_results)


def _normalize_sources(raw_results: list[Any], max_results: int) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for raw_result in raw_results:
        if not isinstance(raw_result, dict):
            continue

        title = _clean_text(raw_result.get("title"))
        url = _clean_url(raw_result.get("url"))
        snippet = _clean_text(raw_result.get("content"))
        if not title or not url or url in seen_urls:
            continue

        seen_urls.add(url)
        source = {"title": title, "url": url}
        if snippet:
            source["snippet"] = snippet
        sources.append(source)

        if len(sources) >= max_results:
            break

    return sources


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:500]


def _clean_url(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    candidate = value.strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return candidate


def _read_timeout_seconds() -> float:
    raw = os.environ.get("SEARXNG_TIMEOUT_MS", "").strip()
    if not raw:
        return DEFAULT_SEARXNG_TIMEOUT_SECONDS
    try:
        timeout_ms = int(raw)
    except ValueError:
        return DEFAULT_SEARXNG_TIMEOUT_SECONDS
    if timeout_ms <= 0:
        return DEFAULT_SEARXNG_TIMEOUT_SECONDS
    return min(timeout_ms / 1000, 30.0)
