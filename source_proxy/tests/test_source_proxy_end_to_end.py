from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from source_proxy.budget.manager import BudgetStatus
from source_proxy.diagnostics.gpu import VramMetrics
from source_proxy.main import app


class SourceProxyEndToEndTests(unittest.TestCase):
    def test_read_only_preview_flow_preserves_safety_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / ".git").mkdir()
            (project_root / "repomix-output.ast.xml").write_text(
                "<repository_context />",
                encoding="utf-8",
            )

            env = {
                "SPIRIT_PROJECT_PATH": str(project_root),
                "SPIRIT_DESKTOP_FS_ENABLED": "true",
                "SPIRIT_DESKTOP_FS_ALLOWLIST": "C:\\Projects",
                "SPIRIT_DESKTOP_TOKEN": "secret-token",
            }

            with (
                patch.dict(os.environ, env, clear=False),
                patch("source_proxy.self_status.Path.cwd", return_value=project_root),
                patch("source_proxy.context.inventory.Path.cwd", return_value=project_root),
                patch(
                    "source_proxy.api.healthcheck.collect_vram_metrics",
                    return_value=VramMetrics(used_gb=2.25, total_gb=12.0, source="test"),
                ),
                patch(
                    "source_proxy.api.healthcheck.collect_budget_status",
                    return_value=BudgetStatus(
                        user="source",
                        total_budget=5.0,
                        current_cost=1.25,
                    ),
                ),
            ):
                client = TestClient(app)

                root = client.get("/").json()
                health = client.get("/healthcheck").json()
                status = client.get("/v1/self/status").json()
                tools = client.get("/v1/tools/manifest").json()
                context_index = client.get("/v1/context/index").json()
                inventory = client.get("/v1/context/inventory").json()
                route = client.post(
                    "/v1/decisions/route",
                    json={
                        "task": "Review this repo with large generated context",
                        "context_tokens": 42000,
                        "needs_codebase_context": True,
                    },
                ).json()
                research_route = client.post(
                    "/v1/decisions/route",
                    json={
                        "task": "What are the latest changes in Vite 6?",
                        "needs_codebase_context": False,
                    },
                ).json()
                packet = client.post(
                    "/v1/decisions/prompt-packet",
                    json={
                        "task": "Prepare an external review packet",
                        "relevant_context": (
                            "folder listing:\n"
                            "C:\\Projects\\SpiritOS\\package.json\n"
                            "C:\\Projects\\SpiritOS\\.env\n"
                            "source_proxy/main.py\n"
                        ),
                        "needs_codebase_context": True,
                    },
                ).json()
                preview = client.post(
                    "/v1/decisions/api-vs-manual-preview",
                    json={
                        "task": "Compare paid API and manual browser routes for repo review",
                        "api_model_alias": "openai",
                        "context_tokens": 42000,
                        "needs_codebase_context": True,
                    },
                ).json()
                action = client.post(
                    "/v1/actions/preview",
                    json={
                        "action": "read all files and send through OpenAI",
                        "target": "C:\\Users\\smith\\.env",
                        "route_type": "api_route",
                    },
                ).json()
                research_sources = [
                    {
                        "title": "Vite 6.0 is out!",
                        "url": "https://vite.dev/blog/announcing-vite6",
                        "snippet": "Vite 6 release notes.",
                    }
                ]
                with (
                    patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": "true"}, clear=False),
                    patch(
                    "source_proxy.decision.router.run_local_research_preview",
                    new=AsyncMock(return_value=research_sources),
                ),
                patch(
                    "source_proxy.api.decision._build_fip2_research_packet",
                    new=AsyncMock(return_value={}),
                ),
            ):
                    research_packet = client.post(
                        "/v1/decisions/prompt-packet",
                        json={
                            "task": "What are the latest changes in Vite 6?",
                            "needs_codebase_context": False,
                        },
                    ).json()

        self.assertEqual(root["service"], "source-proxy")
        self.assertEqual(root["status"], "bootstrapped")
        self.assertEqual(
            root["write_policy"],
            {
                "apply_requires_approval": True,
                "commit_requires_separate_approval": True,
                "push_requires_separate_approval": True,
            },
        )

        self.assertEqual(health["vram_total"], "12 GB")
        self.assertEqual(health["budget_remaining"], "$3.75")

        self.assertEqual(status["manifest_version"], "2.7A-1")
        self.assertIn("full-machine", status["access_scope"])
        self.assertEqual(status["windows_bridge_status"]["allowlisted_roots"], ["C:\\Projects"])
        self.assertNotIn("secret-token", str(status))

        self.assertEqual(tools["manifest_version"], "2.7A-2")
        self.assertIn("approval_boundaries", tools)

        self.assertEqual(context_index["manifest_version"], "2.7A-3")
        self.assertFalse(context_index["context_inclusion_policy"]["contents_included"])
        self.assertFalse(context_index["context_bundle_status"]["content_included"])

        self.assertEqual(inventory["inventory_version"], "2.8-1")
        self.assertFalse(inventory["inventory_limits"]["file_contents_included"])
        self.assertIn(
            "C:\\Projects",
            {root["path"] for root in inventory["verified_context_roots"]},
        )

        self.assertEqual(route["recommended_route"], "manual_route")
        self.assertIn("large_context", route["reason_codes"])
        self.assertTrue(route["research_recommended"])
        self.assertIn("repo_first_research", route["reason_codes"])
        self.assertTrue(research_route["research_recommended"])

        metadata = packet["context_metadata"]
        self.assertEqual(metadata["context_inclusion_mode"], "path_listing_only")
        self.assertFalse(metadata["file_contents_claimed"])
        self.assertIn("source_proxy/main.py", metadata["included_paths"])
        self.assertIn("C:\\Projects\\SpiritOS\\.env", metadata["omitted_paths"])

        self.assertEqual(preview["execution_status"], "paused_for_human_decision")
        self.assertFalse(preview["would_execute"])
        self.assertEqual(preview["required_human_decision"]["default_choice"], "manual")
        self.assertIn("projected_api_cost", preview)

        self.assertEqual(action["decision"], "blocked")
        self.assertFalse(action["would_execute"])
        self.assertIn("broad_filesystem_scope", action["reason_codes"])
        self.assertIn("possible_secret_or_credential_scope", action["reason_codes"])

        self.assertTrue(research_packet["route_decision"]["research_recommended"])
        self.assertEqual(research_packet["research_sources"], research_sources)
        self.assertEqual(research_packet["route_decision"]["research_sources"], research_sources)


if __name__ == "__main__":
    unittest.main()
