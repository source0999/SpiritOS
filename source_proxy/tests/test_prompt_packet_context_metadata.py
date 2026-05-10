from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
