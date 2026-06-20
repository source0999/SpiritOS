from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
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
    async def test_searxng_diagnostics_explicit_provider_does_not_fallback(self) -> None:
        class FailingAsyncClient:
            def __init__(self, *args: object, **kwargs: object) -> None:
                return None

            async def __aenter__(self) -> "FailingAsyncClient":
                return self

            async def __aexit__(self, *args: object) -> None:
                return None

            async def get(self, *args: object, **kwargs: object) -> object:
                raise research.httpx.ConnectError("connection refused")

        with (
            patch.dict(os.environ, {"SEARXNG_URL": "http://127.0.0.1:8080"}, clear=False),
            patch.object(research.httpx, "AsyncClient", FailingAsyncClient),
        ):
            diagnostics = await research.run_searxng_research_diagnostics(
                "latest Vite 6",
                provider_url="http://127.0.0.1:1",
            )

        self.assertEqual(diagnostics["status"], "blocked")
        self.assertEqual(diagnostics["reason"], "searxng_unreachable")
        self.assertEqual(diagnostics["provider_candidates"], ["http://127.0.0.1:1"])
        self.assertEqual(diagnostics["provider_url_used"], "")

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
                    "source": "web",
                    "evidence": {
                        "source": "https://vite.dev/blog/vite6",
                        "freshness": "unknown",
                        "trust_status": "unreviewed_web_result",
                        "review_status": "normalized_preview",
                        "packet_summary": "Vite 6 release notes",
                        "why_relevant": "Search result returned by the configured local research provider.",
                    },
                }
            ],
        )

    async def test_run_local_research_preview_returns_empty_when_searxng_missing(self) -> None:
        with patch.dict(os.environ, {"SEARXNG_URL": ""}, clear=False):
            self.assertEqual(await research.run_local_research_preview("latest Vite 6"), [])

    async def test_run_local_research_preview_includes_scout_when_enabled(self) -> None:
        async def fake_scout(query: str, max_results: int = 6) -> list[dict[str, str]]:
            return [
                {
                    "title": "Scout result",
                    "url": "https://example.com/scout",
                    "snippet": "Scout impact",
                    "source": "scout",
                }
            ]

        with (
            patch.dict(os.environ, {"SEARXNG_URL": ""}, clear=False),
            patch.object(research, "run_scout_research_preview", fake_scout),
        ):
            sources = await research.run_local_research_preview("latest Vite 6")

        self.assertEqual(sources[0]["source"], "scout")

    async def test_run_local_research_preview_returns_repo_sources_before_web(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "package.json").write_text("{}", encoding="utf-8")
            coding_component = project_root / "src/components/coding/CodingAgentInterface.tsx"
            router = project_root / "source_proxy/decision/router.py"
            coding_component.parent.mkdir(parents=True)
            router.parent.mkdir(parents=True)
            coding_component.write_text(
                "export function CodingAgentInterface() {\n"
                "  const historyBug = 'history bug on the coding page';\n"
                "  return historyBug;\n"
                "}\n",
                encoding="utf-8",
            )
            router.write_text(
                "def decide_route():\n"
                "    return 'decision router'\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"SPIRIT_PROJECT_PATH": str(project_root), "SEARXNG_URL": ""},
                clear=False,
            ):
                sources = await research.run_local_research_preview(
                    "fix the history bug on the /coding page",
                    max_results=4,
                )

        self.assertGreaterEqual(len(sources), 1)
        self.assertEqual(
            sources[0]["url"],
            "repo://src/components/coding/CodingAgentInterface.tsx",
        )
        self.assertIn("history bug", sources[0]["snippet"])
        self.assertEqual(sources[0]["source"], "repo")
        self.assertEqual(sources[0]["evidence"]["trust_status"], "workspace")
        self.assertEqual(sources[0]["evidence"]["review_status"], "repo_first_match")
        self.assertIn("relevance score", sources[0]["evidence"]["why_relevant"])

    async def test_repo_research_finds_project_root_when_proxy_starts_in_source_proxy(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_proxy_root = project_root / "source_proxy"
            coding_page = project_root / "src/app/coding/page.tsx"
            source_proxy_root.mkdir(parents=True)
            coding_page.parent.mkdir(parents=True)
            (project_root / "package.json").write_text("{}", encoding="utf-8")
            coding_page.write_text(
                "export default function CodingPage() { return 'coding page history'; }\n",
                encoding="utf-8",
            )

            with (
                patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": "", "SEARXNG_URL": ""}, clear=False),
                patch.object(research.Path, "cwd", return_value=source_proxy_root),
            ):
                sources = await research.run_local_research_preview(
                    "fix the history bug on the /coding page",
                    max_results=4,
                )

        self.assertTrue(any(source["url"] == "repo://src/app/coding/page.tsx" for source in sources))

    async def test_repo_research_ignores_stale_configured_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            stale_root = project_root / "missing-linux-root"
            source_proxy_root = project_root / "source_proxy"
            coding_page = project_root / "src/app/coding/page.tsx"
            source_proxy_root.mkdir(parents=True)
            coding_page.parent.mkdir(parents=True)
            (project_root / "package.json").write_text("{}", encoding="utf-8")
            coding_page.write_text(
                "export default function CodingPage() { return 'coding page history'; }\n",
                encoding="utf-8",
            )

            with (
                patch.dict(
                    os.environ,
                    {
                        "SPIRIT_PROJECT_PATH": f"{stale_root},/mnt/spirit-projects/spiritOS",
                        "SEARXNG_URL": "",
                    },
                    clear=False,
                ),
                patch.object(research.Path, "cwd", return_value=source_proxy_root),
            ):
                sources = await research.run_local_research_preview(
                    "fix the history bug on the /coding page",
                    max_results=4,
                )

        self.assertTrue(any(source["url"] == "repo://src/app/coding/page.tsx" for source in sources))


if __name__ == "__main__":
    unittest.main()
