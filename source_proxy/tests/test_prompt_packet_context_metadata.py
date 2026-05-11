from __future__ import annotations

import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from source_proxy.decision.prompt_packet import PromptPacketInput, build_prompt_packet
from source_proxy.main import app


class PromptPacketContextMetadataTests(unittest.TestCase):
    def test_prompt_packet_marks_missing_context_without_claiming_file_contents(self) -> None:
        packet = build_prompt_packet(
            PromptPacketInput(
                task="Review the repo architecture",
                needs_codebase_context=True,
            )
        ).as_payload()

        metadata = packet["context_metadata"]
        self.assertEqual(metadata["context_inclusion_mode"], "none")
        self.assertFalse(metadata["file_contents_claimed"])
        self.assertEqual(metadata["included_paths"], [])
        self.assertIn("ask for the specific files", packet["relevant_context"])

    def test_prompt_packet_marks_path_listing_only_and_omits_secret_paths(self) -> None:
        packet = build_prompt_packet(
            PromptPacketInput(
                task="Review Windows project folder listing",
                relevant_context=(
                    "Path listing only:\n"
                    "C:\\Projects\\SpiritOS\\package.json\n"
                    "C:\\Projects\\SpiritOS\\.env\n"
                    "src/app/page.tsx\n"
                ),
                needs_codebase_context=True,
            )
        ).as_payload()

        metadata = packet["context_metadata"]
        self.assertEqual(metadata["context_inclusion_mode"], "path_listing_only")
        self.assertFalse(metadata["file_contents_claimed"])
        self.assertIn("C:\\Projects\\SpiritOS\\package.json", metadata["included_paths"])
        self.assertIn("src/app/page.tsx", metadata["included_paths"])
        self.assertNotIn("C:\\Projects\\SpiritOS\\.env", metadata["included_paths"])
        self.assertIn("C:\\Projects\\SpiritOS\\.env", metadata["omitted_paths"])

    def test_prompt_packet_marks_generated_bundle_reference(self) -> None:
        packet = build_prompt_packet(
            PromptPacketInput(
                task="Use compressed context",
                relevant_context="generated_context_bundle: repomix-output.ast.xml",
                context_tokens=12000,
            )
        ).as_payload()

        metadata = packet["context_metadata"]
        self.assertEqual(metadata["context_inclusion_mode"], "generated_bundle_reference")
        self.assertFalse(metadata["file_contents_claimed"])
        self.assertIn("repomix-output.ast.xml", metadata["included_paths"])
        self.assertGreater(metadata["estimated_context_tokens"], 0)

    def test_prompt_packet_endpoint_returns_context_metadata(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/v1/decisions/prompt-packet",
            json={
                "task": "Create prompt packet from listing",
                "relevant_context": "folder listing:\nsrc/lib/example.ts",
                "needs_codebase_context": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("context_metadata", payload)
        self.assertEqual(
            payload["context_metadata"]["context_inclusion_mode"],
            "path_listing_only",
        )

    def test_research_prompt_packet_endpoint_attaches_sources(self) -> None:
        client = TestClient(app)
        sources = [
            {
                "title": "Vite 6.0 is out!",
                "url": "https://vite.dev/blog/announcing-vite6",
                "snippet": "Vite 6 release notes.",
            }
        ]

        with patch(
            "source_proxy.decision.router.run_local_research_preview",
            new=AsyncMock(return_value=sources),
        ):
            with patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": "true"}, clear=False):
                response = client.post(
                    "/v1/decisions/prompt-packet",
                    json={"task": "What are the latest changes in Vite 6?"},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["route_decision"]["research_recommended"])
        self.assertEqual(payload["research_sources"], sources)
        self.assertEqual(payload["route_decision"]["research_sources"], sources)

    def test_research_route_endpoint_attaches_sources(self) -> None:
        client = TestClient(app)
        sources = [
            {
                "title": "Releases | Vite",
                "url": "https://vite.dev/releases",
                "snippet": "Current releases.",
            }
        ]

        with patch(
            "source_proxy.decision.router.run_local_research_preview",
            new=AsyncMock(return_value=sources),
        ):
            with patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": "true"}, clear=False):
                response = client.post(
                    "/v1/decisions/route",
                    json={"task": "What are the latest changes in Vite 6?"},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["research_recommended"])
        self.assertEqual(payload["research_sources"], sources)

    def test_proxy_research_sources_are_disabled_by_default(self) -> None:
        client = TestClient(app)
        search = AsyncMock(
            return_value=[
                {
                    "title": "Releases | Vite",
                    "url": "https://vite.dev/releases",
                    "snippet": "Current releases.",
                }
            ],
        )

        with (
            patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": ""}, clear=False),
            patch("source_proxy.decision.router.run_local_research_preview", new=search),
        ):
            response = client.post(
                "/v1/decisions/route",
                json={"task": "What are the latest changes in Vite 6?"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["research_recommended"])
        self.assertEqual(payload["research_sources"], [])
        search.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
