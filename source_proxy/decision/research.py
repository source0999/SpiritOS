from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from source_proxy.decision.scout_research import run_scout_research_preview

DEFAULT_SEARXNG_TIMEOUT_SECONDS = 10.0
MAX_REPO_SOURCE_BYTES = 200_000

REPO_RESEARCH_PATHS = [
    "src/app/coding/page.tsx",
    "src/components/coding/CodingAgentInterface.tsx",
    "masterProxyPlan.md",
    "refinedProxy.md",
    "source_proxy/decision/research.py",
    "source_proxy/decision/router.py",
    "source_proxy/decision/recommendation.py",
    "source_proxy/decision/prompt_packet.py",
    "source_proxy/decision/preview.py",
    "source_proxy/api/decision.py",
    "src/app/v1/decisions/route/route.ts",
    "src/app/v1/decisions/prompt-packet/route.ts",
    "src/lib/spirit/spirit-route-decision.ts",
    "src/lib/spirit/spirit-reasoning-patterns.ts",
]

QUERY_STOP_WORDS = {
    "about",
    "after",
    "again",
    "before",
    "check",
    "could",
    "from",
    "have",
    "into",
    "latest",
    "please",
    "prompt",
    "should",
    "start",
    "that",
    "the",
    "this",
    "what",
    "when",
    "with",
    "would",
}


async def run_local_research_preview(query: str, max_results: int = 6) -> list[dict[str, str]]:
    normalized_query = query.strip()
    if not normalized_query:
        return []

    bounded_max_results = min(max(1, int(max_results)), 12)
    repo_sources = run_repo_research_preview(normalized_query, max_results=bounded_max_results)
    if len(repo_sources) >= bounded_max_results:
        return repo_sources

    scout_sources = await run_scout_research_preview(
        normalized_query,
        max_results=bounded_max_results - len(repo_sources),
    )
    combined_sources = [*repo_sources, *scout_sources]
    if len(combined_sources) >= bounded_max_results:
        return combined_sources

    searxng_url = os.environ.get("SEARXNG_URL", "").strip()
    if not searxng_url:
        return combined_sources

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
        return repo_sources

    web_sources = _normalize_sources(raw_results, bounded_max_results - len(combined_sources))
    return [*combined_sources, *web_sources]


def run_repo_research_preview(query: str, max_results: int = 6) -> list[dict[str, str]]:
    normalized_query = query.strip()
    if not normalized_query:
        return []

    project_root = _project_root()
    query_terms = _query_terms(normalized_query)
    scored_sources: list[tuple[int, int, dict[str, str]]] = []

    for priority, relative_path in enumerate(REPO_RESEARCH_PATHS):
        file_path = project_root / relative_path
        if not _is_readable_repo_file(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        score = _score_repo_file(relative_path, content, normalized_query, query_terms)
        if score <= 0:
            continue

        source = {
            "title": f"Repo: {relative_path}",
            "url": f"repo://{relative_path}",
            "snippet": _repo_snippet(relative_path, content, query_terms),
            "source": "repo",
            "evidence": {
                "source": f"repo://{relative_path}",
                "freshness": _file_freshness(file_path),
                "trust_status": "workspace",
                "review_status": "repo_first_match",
                "packet_summary": f"Repository file selected for local-first research: {relative_path}",
                "why_relevant": _repo_relevance_reason(relative_path, score, query_terms),
            },
        }
        scored_sources.append((score, -priority, source))

    scored_sources.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [source for _, _, source in scored_sources[: min(max(1, int(max_results)), 12)]]


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
        source["source"] = "web"
        source["evidence"] = {
            "source": url,
            "freshness": "unknown",
            "trust_status": "unreviewed_web_result",
            "review_status": "normalized_preview",
            "packet_summary": title,
            "why_relevant": "Search result returned by the configured local research provider.",
        }
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


def _project_root() -> Path:
    configured_root = os.environ.get("SPIRIT_PROJECT_PATH", "").strip()
    if configured_root:
        for candidate in _configured_project_root_candidates(configured_root):
            if _looks_like_project_root(candidate):
                return candidate

    for candidate in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        if _looks_like_project_root(candidate):
            return candidate
    return Path.cwd()


def _configured_project_root_candidates(configured_root: str) -> list[Path]:
    raw_candidates = [
        value.strip()
        for chunk in configured_root.split(os.pathsep)
        for value in chunk.split(",")
        if value.strip()
    ]
    return [Path(candidate) for candidate in raw_candidates]


def _looks_like_project_root(candidate: Path) -> bool:
    return (
        (candidate / "package.json").is_file()
        and (candidate / "source_proxy").is_dir()
        and (candidate / "src").is_dir()
    )


def _is_readable_repo_file(file_path: Path) -> bool:
    try:
        resolved = file_path.resolve()
    except OSError:
        return False
    if not resolved.is_file():
        return False
    try:
        return resolved.stat().st_size <= MAX_REPO_SOURCE_BYTES
    except OSError:
        return False


def _query_terms(query: str) -> list[str]:
    terms = []
    for term in re.findall(r"[a-zA-Z0-9_/-]+", query.lower()):
        cleaned = term.strip("/_-")
        if len(cleaned) < 3 or cleaned in QUERY_STOP_WORDS:
            continue
        terms.append(cleaned)
    return list(dict.fromkeys(terms))[:24]


def _score_repo_file(
    relative_path: str,
    content: str,
    query: str,
    query_terms: list[str],
) -> int:
    normalized_query = query.lower()
    normalized_path = relative_path.lower().replace("\\", "/")
    normalized_content = content.lower()
    score = 0

    for term in query_terms:
        if term in normalized_path:
            score += 8
        if term in normalized_content:
            score += min(normalized_content.count(term), 6)

    if "/coding" in normalized_query or "coding page" in normalized_query:
        if normalized_path in {
            "src/app/coding/page.tsx",
            "src/components/coding/codingagentinterface.tsx",
        }:
            score += 18
    if "history" in normalized_query and "codingagentinterface" in normalized_path:
        score += 12
    if "bug" in normalized_query and normalized_path.endswith((".tsx", ".ts", ".py")):
        score += 3
    if "decision" in normalized_query and "decision" in normalized_path:
        score += 14
    if "research" in normalized_query and "research.py" in normalized_path:
        score += 18
    if "router" in normalized_query or "route" in normalized_query:
        if "router.py" in normalized_path or "/route/" in normalized_path:
            score += 14
    if "plan" in normalized_query or "phase" in normalized_query or "increment" in normalized_query:
        if normalized_path in {"masterproxyplan.md", "refinedproxy.md"}:
            score += 12

    return score


def _repo_snippet(relative_path: str, content: str, query_terms: list[str]) -> str:
    lines = content.splitlines()
    matched_lines: list[str] = []
    lowered_terms = [term.lower() for term in query_terms]
    for index, line in enumerate(lines, start=1):
        lowered_line = line.lower()
        if lowered_terms and not any(term in lowered_line for term in lowered_terms):
            continue
        cleaned_line = _clean_text(line)
        if cleaned_line:
            matched_lines.append(f"L{index}: {cleaned_line}")
        if len(matched_lines) >= 3:
            break

    if matched_lines:
        return "Matched repo lines: " + " | ".join(matched_lines)
    return f"Relevant repository file selected for local-first research: {relative_path}"


def _file_freshness(file_path: Path) -> str:
    try:
        return f"mtime:{int(file_path.stat().st_mtime)}"
    except OSError:
        return "unknown"


def _repo_relevance_reason(relative_path: str, score: int, query_terms: list[str]) -> str:
    terms = ", ".join(query_terms[:6])
    if terms:
        return f"Matched query terms in {relative_path}; relevance score {score}. Terms: {terms}."
    return f"Selected by repo-first research rules for {relative_path}; relevance score {score}."


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
