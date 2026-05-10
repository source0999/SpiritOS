from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from source_proxy.main import app
from source_proxy.self_status import (
    build_action_preview,
    build_context_index_manifest,
    build_self_status_manifest,
    build_tools_manifest,
)


class SelfStatusManifestTests(unittest.TestCase):
    def test_manifest_is_read_only_and_does_not_imply_full_machine_access(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "repomix-output.ast.xml").write_text("<bundle />", encoding="utf-8")

            manifest = build_self_status_manifest(root)

        self.assertEqual(manifest["manifest_version"], "2.7A-1")
        self.assertIn("does not imply full-machine", manifest["access_scope"])
        self.assertEqual(
            manifest["context_bundle_status"]["bundles"][0]["status"],
            "present",
        )
        self.assertFalse(manifest["context_bundle_status"]["content_included"])
        self.assertIn(
            "full_drive_browsing",
            {tool["name"] for tool in manifest["disabled_tools"]},
        )

    def test_windows_bridge_reports_only_configured_allowlist(self) -> None:
        env = {
            "SPIRIT_WINDOWS_FS_ENABLED": "true",
            "SPIRIT_WINDOWS_FS_BASE_URL": "http://windows-host:3000",
            "SPIRIT_WINDOWS_FS_TOKEN": "secret-token",
            "SPIRIT_WINDOWS_FS_ALLOWLIST": "C:\\Projects",
        }
        with patch.dict(os.environ, env, clear=False):
            manifest = build_self_status_manifest(Path.cwd())

        bridge = manifest["windows_bridge_status"]
        self.assertEqual(bridge["status"], "configured_not_probed")
        self.assertEqual(bridge["allowlisted_roots"], ["C:\\Projects"])
        self.assertTrue(bridge["token_present"])
        self.assertNotIn("secret-token", str(bridge))

    def test_endpoint_returns_manifest(self) -> None:
        client = TestClient(app)
        response = client.get("/v1/self/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["service"], "source-proxy")
        self.assertIn("configured_roots", payload)
        self.assertIn("approval_boundaries", payload)

    def test_tools_manifest_lists_gated_and_disabled_capabilities(self) -> None:
        manifest = build_tools_manifest(
            [
                {
                    "alias": "local",
                    "provider": "ollama",
                    "model": "ollama_chat/hermes4",
                    "enabled": True,
                    "reason": None,
                },
                {
                    "alias": "openai",
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "enabled": True,
                    "reason": None,
                },
            ]
        )

        self.assertEqual(manifest["manifest_version"], "2.7A-2")
        self.assertIn("not permission to execute", manifest["access_scope"])
        self.assertIn(
            "paid_api_chat_routes",
            {tool["name"] for tool in manifest["enabled_tools"]},
        )
        self.assertIn(
            "terminal_execution",
            {tool["name"] for tool in manifest["disabled_tools"]},
        )
        api_route = next(
            route
            for route in manifest["available_routes"]
            if route["route_type"] == "api_route"
        )
        self.assertEqual(api_route["approval"], "spend_before_send_required")

    def test_tools_manifest_endpoint_returns_manifest(self) -> None:
        client = TestClient(app)
        response = client.get("/v1/tools/manifest")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["manifest_version"], "2.7A-2")
        self.assertIn("enabled_tools", payload)
        self.assertNotIn("configured_roots", payload)

    def test_context_index_reports_bundle_presence_without_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "repomix-output.xml").write_text(
                "SECRET_SHOULD_NOT_APPEAR",
                encoding="utf-8",
            )

            manifest = build_context_index_manifest(root)

        self.assertEqual(manifest["manifest_version"], "2.7A-3")
        self.assertIn("without reading file contents", manifest["access_scope"])
        self.assertFalse(manifest["context_inclusion_policy"]["contents_included"])
        self.assertFalse(manifest["context_inclusion_policy"]["recursive_expansion"])
        bundle = next(
            item
            for item in manifest["context_bundle_status"]["bundles"]
            if item["name"] == "repomix-output.xml"
        )
        self.assertEqual(bundle["status"], "present")
        self.assertEqual(bundle["size_bytes"], 24)
        self.assertFalse(bundle["content_included"])
        self.assertNotIn("SECRET_SHOULD_NOT_APPEAR", str(manifest))

    def test_context_index_endpoint_returns_manifest(self) -> None:
        client = TestClient(app)
        response = client.get("/v1/context/index")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["manifest_version"], "2.7A-3")
        self.assertIn("context_bundle_status", payload)
        self.assertIn("context_inclusion_policy", payload)

    def test_action_preview_blocks_secret_or_broad_filesystem_scope(self) -> None:
        preview = build_action_preview(
            action="read all files",
            target="C:\\Users\\smith\\.env",
        )

        self.assertEqual(preview["manifest_version"], "2.7A-4")
        self.assertEqual(preview["decision"], "blocked")
        self.assertFalse(preview["would_execute"])
        self.assertIn("broad_filesystem_scope", preview["reason_codes"])
        self.assertIn("possible_secret_or_credential_scope", preview["reason_codes"])

    def test_action_preview_requires_approval_for_paid_or_implementation_action(self) -> None:
        preview = build_action_preview(
            action="send this through OpenAI",
            route_type="api_route",
        )

        self.assertEqual(preview["decision"], "requires_human_approval")
        self.assertTrue(preview["requires_human_approval"])
        self.assertFalse(preview["would_execute"])
        self.assertIn("paid_api_route_possible", preview["reason_codes"])

    def test_action_preview_endpoint_returns_preview_without_execution(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/v1/actions/preview",
            json={"action": "plan manual prompt packet", "route_type": "manual_route"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["manifest_version"], "2.7A-4")
        self.assertEqual(payload["decision"], "preview_only")
        self.assertFalse(payload["would_execute"])


if __name__ == "__main__":
    unittest.main()
