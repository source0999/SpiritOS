from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from source_proxy.decision import research


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {
            "results": [
                {
                    "title": " Vite 6 release notes ",
                    "url": "https://vite.dev/blog/vite6",
                    "content": " Latest Vite changes. ",
                },
                {
                    "title": "Duplicate",
                    "url": "https://vite.dev/blog/vite6",
                    "content": "Duplicate should be dropped.",
                },
                {
                    "title": "Bad URL",
                    "url": "javascript:alert(1)",
                    "content": "<script>not a source</script>",
                },
            ],
        }


class _FakeAsyncClient:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, *args: object, **kwargs: object) -> _FakeResponse:
        return _FakeResponse()


class ResearchPreviewTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_local_research_preview_returns_clean_verified_sources(self) -> None:
        with (
            patch.dict(os.environ, {"SEARXNG_URL": "http://127.0.0.1:8080"}, clear=False),
            patch.object(research.httpx, "AsyncClient", _FakeAsyncClient),
        ):
            sources = await research.run_local_research_preview("latest Vite 6", max_results=6)

        self.assertEqual(
            sources,
            [
                {
                    "title": "Vite 6 release notes",
                    "url": "https://vite.dev/blog/vite6",
                    "snippet": "Latest Vite changes.",
                }
            ],
        )

    async def test_run_local_research_preview_returns_empty_when_searxng_missing(self) -> None:
        with patch.dict(os.environ, {"SEARXNG_URL": ""}, clear=False):
            self.assertEqual(await research.run_local_research_preview("latest Vite 6"), [])


if __name__ == "__main__":
    unittest.main()
