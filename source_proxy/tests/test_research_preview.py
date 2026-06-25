from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from source_proxy.decision import current_research, research


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

    async def test_current_research_retries_zero_sources_and_remains_blocked(self) -> None:
        async def fake_scout(query: str, max_results: int = 6) -> dict[str, object]:
            return {
                "status": "skipped",
                "reason": "scout_research_disabled",
                "scout_result_count": 0,
                "scout_sources": [],
                "provider_errors": [],
            }

        async def fake_searxng(query: str, max_results: int = 6) -> dict[str, object]:
            return {
                "status": "blocked",
                "reason": "searxng_query_returned_no_usable_results",
                "searxng_result_count": 0,
                "searxng_sources": [],
                "provider_call_made": True,
                "provider_url_used": "http://127.0.0.1:8080",
                "provider_errors": [],
            }

        def fake_record(task_id: str, **kwargs: object) -> dict[str, object]:
            return {"task": {"id": task_id, "ast_snapshot": {}}}

        with (
            patch.dict(
                os.environ,
                {
                    "SOURCE_PROXY_CURRENT_RESEARCH_MAX_RETRIES": "2",
                    "SOURCE_PROXY_CURRENT_RESEARCH_RETRY_BACKOFF_SECONDS": "0",
                },
                clear=False,
            ),
            patch.object(current_research, "run_scout_research_diagnostics", fake_scout),
            patch.object(current_research, "run_searxng_research_diagnostics", fake_searxng),
            patch.object(current_research, "record_subsystem_integration_result", fake_record),
        ):
            result = await current_research.run_current_research_for_task(
                "task_provider_zero",
                query="Android Jetpack Compose share intent local task app receipt polling",
                upstream_state={"test": "zero_sources"},
                max_results=6,
            )

        packet = result["research_packet"]
        self.assertEqual(result["status"], "BLOCKED_ENV")
        self.assertEqual(packet["source_count"], 0)
        self.assertEqual(packet["research_provider_retry_count"], 2)
        self.assertEqual(packet["research_provider_result_counts"], [0, 0, 0])
        self.assertEqual(packet["research_provider_failure_classification"], "PROVIDER_ZERO_RESULTS")

    async def test_current_research_successful_retry_uses_returned_sources_only(self) -> None:
        async def fake_scout(query: str, max_results: int = 6) -> dict[str, object]:
            return {
                "status": "skipped",
                "reason": "scout_research_disabled",
                "scout_result_count": 0,
                "scout_sources": [],
                "provider_errors": [],
            }

        calls = {"count": 0}

        async def fake_searxng(query: str, max_results: int = 6) -> dict[str, object]:
            calls["count"] += 1
            if calls["count"] == 1:
                return {
                    "status": "blocked",
                    "reason": "searxng_query_returned_no_usable_results",
                    "searxng_result_count": 0,
                    "searxng_sources": [],
                    "provider_call_made": True,
                    "provider_url_used": "http://127.0.0.1:8080",
                    "provider_errors": [],
                }
            return {
                "status": "used",
                "reason": "live_searxng_provider_query_executed",
                "searxng_result_count": 1,
                "searxng_sources": [
                    {
                        "title": "Send simple data to other apps",
                        "url": "https://developer.android.com/training/sharing/send",
                        "snippet": "Android intents share data between apps.",
                    }
                ],
                "provider_call_made": True,
                "provider_url_used": "http://127.0.0.1:8080",
                "provider_errors": [],
            }

        def fake_record(task_id: str, **kwargs: object) -> dict[str, object]:
            return {"task": {"id": task_id, "ast_snapshot": {}}}

        with (
            patch.dict(
                os.environ,
                {
                    "SOURCE_PROXY_CURRENT_RESEARCH_MAX_RETRIES": "2",
                    "SOURCE_PROXY_CURRENT_RESEARCH_RETRY_BACKOFF_SECONDS": "0",
                },
                clear=False,
            ),
            patch.object(current_research, "run_scout_research_diagnostics", fake_scout),
            patch.object(current_research, "run_searxng_research_diagnostics", fake_searxng),
            patch.object(current_research, "record_subsystem_integration_result", fake_record),
        ):
            result = await current_research.run_current_research_for_task(
                "task_provider_retry",
                query="Android Jetpack Compose share intent local task app receipt polling",
                upstream_state={"test": "retry_success"},
                max_results=6,
            )

        packet = result["research_packet"]
        self.assertEqual(result["status"], "INTEGRATED_LIVE")
        self.assertEqual(packet["source_count"], 1)
        self.assertEqual(packet["research_provider_retry_count"], 1)
        self.assertEqual(packet["research_provider_result_counts"], [0, 1])
        self.assertEqual(packet["sources"][0]["provider"], "searxng")
        self.assertEqual(packet["sources"][0]["url"], "https://developer.android.com/training/sharing/send")

    async def test_current_research_timeout_classifies_blocked_env(self) -> None:
        async def fake_scout(query: str, max_results: int = 6) -> dict[str, object]:
            return {
                "status": "skipped",
                "reason": "scout_research_disabled",
                "scout_result_count": 0,
                "scout_sources": [],
                "provider_errors": [],
            }

        async def fake_searxng(query: str, max_results: int = 6) -> dict[str, object]:
            return {
                "status": "blocked",
                "reason": "searxng_unreachable",
                "searxng_result_count": 0,
                "searxng_sources": [],
                "provider_call_made": True,
                "provider_url_used": "",
                "provider_errors": ["http://127.0.0.1:8080: timeout: "],
            }

        def fake_record(task_id: str, **kwargs: object) -> dict[str, object]:
            return {"task": {"id": task_id, "ast_snapshot": {}}}

        with (
            patch.dict(
                os.environ,
                {
                    "SOURCE_PROXY_CURRENT_RESEARCH_MAX_RETRIES": "1",
                    "SOURCE_PROXY_CURRENT_RESEARCH_RETRY_BACKOFF_SECONDS": "0",
                },
                clear=False,
            ),
            patch.object(current_research, "run_scout_research_diagnostics", fake_scout),
            patch.object(current_research, "run_searxng_research_diagnostics", fake_searxng),
            patch.object(current_research, "record_subsystem_integration_result", fake_record),
        ):
            result = await current_research.run_current_research_for_task(
                "task_provider_timeout",
                query="Android Jetpack Compose share intent local task app receipt polling",
                upstream_state={"test": "timeout"},
                max_results=6,
            )

        packet = result["research_packet"]
        self.assertEqual(result["status"], "BLOCKED_ENV")
        self.assertEqual(packet["source_count"], 0)
        self.assertEqual(packet["research_provider_retry_count"], 1)
        self.assertEqual(packet["research_provider_failure_classification"], "PROVIDER_TIMEOUT")


if __name__ == "__main__":
    unittest.main()
