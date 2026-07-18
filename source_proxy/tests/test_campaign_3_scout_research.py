from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from source_proxy.decision.scout_research import run_canonical_coding_research


def test_canonical_scout_research_binds_task_query_provenance_fetch_and_citations() -> None:
    scout = {"status": "used", "scout_sources": [{"url": "https://docs.python.org/3/", "title": "Python", "evidence": {"freshness": "2026-07-18T00:00:00Z"}}]}
    searxng = {"status": "used", "searxng_sources": [{"url": "https://example.com/secondary", "title": "Secondary", "evidence": {"freshness": "current"}}]}
    with patch("source_proxy.decision.scout_research.run_scout_research_diagnostics", AsyncMock(return_value=scout)), patch("source_proxy.decision.research.run_searxng_research_diagnostics", AsyncMock(return_value=searxng)), patch("source_proxy.decision.scout_research._bounded_fetch_sources", AsyncMock(return_value={"https://docs.python.org/3/": {"status": "fetched", "content_sha256": "sha256:abc", "fetched_at": "2026-07-18T00:00:00Z"}})):
        receipt = asyncio.run(run_canonical_coding_research(task_id="task-1", query="current Python documentation"))
    assert receipt["status"] == "used"
    assert receipt["task_id"] == "task-1"
    assert receipt["sources"][0]["url"] == "https://docs.python.org/3/"
    assert receipt["citations"][0]["freshness"] == "2026-07-18T00:00:00Z"
    assert receipt["mutation_authority"] is False


def test_canonical_scout_research_never_fabricates_unavailable_sources() -> None:
    with patch("source_proxy.decision.scout_research.run_scout_research_diagnostics", AsyncMock(return_value={"status": "blocked", "scout_sources": []})), patch("source_proxy.decision.research.run_searxng_research_diagnostics", AsyncMock(return_value={"status": "blocked", "searxng_sources": []})):
        receipt = asyncio.run(run_canonical_coding_research(task_id="task-1", query="current source"))
    assert receipt["status"] == "blocked"
    assert receipt["sources"] == []
    assert receipt["citations"] == []
