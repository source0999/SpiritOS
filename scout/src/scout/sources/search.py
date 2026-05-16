from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx


class SearchProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class SearchSource:
    title: str
    url: str
    snippet: str | None = None
    published_at: str | None = None
    provider: str = "searxng"


@dataclass(frozen=True)
class SearchProviderTrace:
    provider: str
    status: str
    reason: str | None = None
    elapsed_ms: int | None = None
    source_count: int | None = None


@dataclass(frozen=True)
class SearchResult:
    ok: bool
    searched: bool
    provider: str
    elapsed_ms: int
    query: str | None = None
    sources: list[SearchSource] = field(default_factory=list)
    error: str | None = None
    detail: str | None = None
    provider_trace: list[SearchProviderTrace] = field(default_factory=list)


def run_searxng_search(
    *,
    query: str,
    base_url: str | None,
    max_results: int,
    timeout_seconds: int = 10,
    user_agent: str = "ScoutSearch/0.3",
    client: httpx.Client | None = None,
) -> SearchResult:
    started = monotonic()
    clean_query = query.strip()
    if not clean_query:
        return _failure(
            started,
            error="empty_query",
            detail="Query is empty.",
            searched=False,
        )
    if not base_url or not base_url.strip():
        return _failure(
            started,
            query=clean_query,
            error="searxng_not_configured",
            detail="SCOUT_SEARXNG_URL is not configured.",
            searched=False,
        )
    if max_results < 1 or max_results > 50:
        raise SearchProviderError("max_results must be between 1 and 50")

    owns_client = client is None
    search_client = client or httpx.Client(timeout=timeout_seconds)
    try:
        response = search_client.get(
            _build_searxng_url(base_url, clean_query),
            headers={"Accept": "application/json", "User-Agent": user_agent},
        )
        text = response.text
        if response.status_code >= 400:
            return _failure(
                started,
                query=clean_query,
                error="searxng_json_forbidden"
                if response.status_code == 403
                else f"searxng_{response.status_code}",
                detail=text[:400],
            )
        try:
            body = response.json()
        except ValueError:
            return _failure(
                started,
                query=clean_query,
                error="searxng_invalid_json",
                detail=text[:400],
            )
        raw_results = body.get("results", []) if isinstance(body, dict) else []
        sources = normalize_search_sources(raw_results, max_results=max_results)
        return SearchResult(
            ok=True,
            searched=True,
            provider="searxng",
            query=clean_query,
            sources=sources,
            elapsed_ms=_elapsed_ms(started),
            provider_trace=[
                SearchProviderTrace(
                    provider="searxng",
                    status="used",
                    elapsed_ms=_elapsed_ms(started),
                    source_count=len(sources),
                )
            ],
        )
    except httpx.TimeoutException as exc:
        return _failure(
            started,
            query=clean_query,
            error="searxng_timeout",
            detail=str(exc),
        )
    except httpx.HTTPError as exc:
        return _failure(
            started,
            query=clean_query,
            error="searxng_unreachable",
            detail=str(exc),
        )
    finally:
        if owns_client:
            search_client.close()


def normalize_search_sources(
    raw_results: list[Any],
    *,
    max_results: int,
    provider: str = "searxng",
) -> list[SearchSource]:
    sources: list[SearchSource] = []
    seen: set[str] = set()
    for result in raw_results:
        if not isinstance(result, dict):
            continue
        url = _normalize_result_url(_string_value(result.get("url")))
        if not url or url in seen:
            continue
        seen.add(url)
        title = _string_value(result.get("title")) or url
        sources.append(
            SearchSource(
                title=title.strip()[:300],
                url=url,
                snippet=_string_value(result.get("content")),
                published_at=_string_value(result.get("publishedDate"))
                or _string_value(result.get("published_date")),
                provider=provider,
            )
        )
        if len(sources) >= max_results:
            break
    return sources


def search_result_to_dict(result: SearchResult) -> dict[str, Any]:
    body: dict[str, Any] = {
        "ok": result.ok,
        "searched": result.searched,
        "provider": result.provider,
        "elapsed_ms": result.elapsed_ms,
        "provider_trace": [
            {
                "provider": trace.provider,
                "status": trace.status,
                "reason": trace.reason,
                "elapsed_ms": trace.elapsed_ms,
                "source_count": trace.source_count,
            }
            for trace in result.provider_trace
        ],
    }
    if result.query is not None:
        body["query"] = result.query
    if result.ok:
        body["sources"] = [
            {
                "title": source.title,
                "url": source.url,
                "snippet": source.snippet,
                "published_at": source.published_at,
                "provider": source.provider,
            }
            for source in result.sources
        ]
    else:
        body["error"] = result.error
        body["detail"] = result.detail
    return body


def _failure(
    started: float,
    *,
    error: str,
    detail: str | None = None,
    query: str | None = None,
    searched: bool = True,
) -> SearchResult:
    elapsed = _elapsed_ms(started)
    return SearchResult(
        ok=False,
        searched=searched,
        provider="searxng",
        query=query,
        error=error,
        detail=detail,
        elapsed_ms=elapsed,
        provider_trace=[
            SearchProviderTrace(
                provider="searxng",
                status="failed" if searched else "skipped",
                reason=error,
                elapsed_ms=elapsed,
                source_count=0,
            )
        ],
    )


def _build_searxng_url(base_url: str, query: str) -> str:
    parsed = urlparse(base_url.strip())
    path = parsed.path.rstrip("/") + "/search"
    query_string = urlencode({"q": query, "format": "json"})
    return urlunparse((parsed.scheme, parsed.netloc, path, "", query_string, ""))


def _normalize_result_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"}:
        return None
    host = (parsed.hostname or "").lower()
    if not host:
        return None
    netloc = host if parsed.port is None else f"{host}:{parsed.port}"
    query = _clean_query(parsed.query)
    path = parsed.path or ""
    return urlunparse((parsed.scheme.lower(), netloc, path.rstrip("/"), "", query, ""))


def _clean_query(query: str) -> str:
    pairs = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "spm"}:
            continue
        pairs.append((key, value))
    return urlencode(sorted(pairs))


def _string_value(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _elapsed_ms(started: float) -> int:
    return int((monotonic() - started) * 1000)
