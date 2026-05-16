from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from source_proxy.decision import scout_research


class _FakeResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def json(self) -> dict[str, object]:
        return {
            "packets": [
                {
                    "packet_id": "surface_1",
                    "summary": "Surface packet summary",
                    "impact_analysis": "Surface packet impact",
                    "source_uri": "https://example.com/surface",
                    "timestamp": "2026-05-16T10:00:00+00:00",
                    "entity_tags": ["FastAPI", "release-notes"],
                    "_verdict": {"decision": "surface", "source_quality_score": 0.9},
                },
                {
                    "packet_id": "promote_1",
                    "summary": "Promote packet summary",
                    "impact_analysis": "Promote packet impact",
                    "source_uri": "https://example.com/promote",
                    "_verdict": {"decision": "promote"},
                },
                {
                    "packet_id": "stored_1",
                    "summary": "Stored packet summary",
                    "impact_analysis": "Stored packet impact",
                    "source_uri": "https://example.com/stored",
                    "_verdict": {"decision": "stored"},
                },
                {
                    "packet_id": "ignored_1",
                    "summary": "Ignored packet summary",
                    "impact_analysis": "Ignored packet impact",
                    "source_uri": "https://example.com/ignored",
                    "_verdict": {"decision": "ignored"},
                },
                {
                    "packet_id": "pending_1",
                    "summary": "Pending packet summary",
                    "impact_analysis": "Pending packet impact",
                    "source_uri": "https://example.com/pending",
                    "_verdict": {"decision": "debugger_pending"},
                },
            ]
        }


class _FakeAsyncClient:
    status_code = 200
    raise_on_get: Exception | None = None

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, *args: object, **kwargs: object) -> _FakeResponse:
        if self.raise_on_get:
            raise self.raise_on_get
        return _FakeResponse(self.status_code)


class ScoutResearchBridgeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        _FakeAsyncClient.status_code = 200
        _FakeAsyncClient.raise_on_get = None

    async def test_flag_off_returns_empty(self) -> None:
        with patch.dict(os.environ, {"SOURCE_PROXY_SCOUT_RESEARCH_ENABLED": "0"}):
            self.assertEqual(
                await scout_research.run_scout_research_preview("fastapi"),
                [],
            )

    async def test_unreachable_returns_empty(self) -> None:
        _FakeAsyncClient.raise_on_get = TimeoutError("timeout")
        with (
            patch.dict(os.environ, {"SOURCE_PROXY_SCOUT_RESEARCH_ENABLED": "1"}),
            patch.object(scout_research.httpx, "AsyncClient", _FakeAsyncClient),
        ):
            self.assertEqual(
                await scout_research.run_scout_research_preview("fastapi"),
                [],
            )

    async def test_non_200_returns_empty(self) -> None:
        _FakeAsyncClient.status_code = 503
        with (
            patch.dict(os.environ, {"SOURCE_PROXY_SCOUT_RESEARCH_ENABLED": "1"}),
            patch.object(scout_research.httpx, "AsyncClient", _FakeAsyncClient),
        ):
            self.assertEqual(
                await scout_research.run_scout_research_preview("fastapi"),
                [],
            )

    async def test_default_filters_to_surface_and_promote(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "SOURCE_PROXY_SCOUT_RESEARCH_ENABLED": "1",
                    "SOURCE_PROXY_SCOUT_ADMIN_INCLUDE_STORED": "0",
                },
            ),
            patch.object(scout_research.httpx, "AsyncClient", _FakeAsyncClient),
        ):
            results = await scout_research.run_scout_research_preview("fastapi")

        self.assertEqual(
            [result["scout_decision"] for result in results],
            ["surface", "promote"],
        )
        self.assertTrue(
            all(result["authority"] == "evidence_only" for result in results)
        )
        self.assertTrue(all(result["can_apply"] is False for result in results))
        self.assertTrue(all(result["can_approve"] is False for result in results))
        self.assertTrue(
            all(result["can_mutate_proxy_memory"] is False for result in results)
        )
        first_evidence = results[0]["evidence"]
        self.assertEqual(first_evidence["source"], "https://example.com/surface")
        self.assertEqual(first_evidence["freshness"], "2026-05-16T10:00:00+00:00")
        self.assertEqual(first_evidence["trust_status"], "high")
        self.assertEqual(first_evidence["review_status"], "surface")
        self.assertEqual(first_evidence["packet_summary"], "Surface packet summary")
        self.assertIn("FastAPI", first_evidence["why_relevant"])

    async def test_admin_adds_stored_but_never_ignored_or_pending(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "SOURCE_PROXY_SCOUT_RESEARCH_ENABLED": "1",
                    "SOURCE_PROXY_SCOUT_ADMIN_INCLUDE_STORED": "1",
                },
            ),
            patch.object(scout_research.httpx, "AsyncClient", _FakeAsyncClient),
        ):
            results = await scout_research.run_scout_research_preview("fastapi")

        self.assertEqual(
            [result["scout_decision"] for result in results],
            ["surface", "promote", "stored"],
        )


if __name__ == "__main__":
    unittest.main()
