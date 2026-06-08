from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.action_preview import router as action_preview_router
from source_proxy.api.context_index import router as context_index_router
from source_proxy.api.obsidian_context import router as obsidian_context_router
from source_proxy.api.self_status import router as self_status_router
from source_proxy.api.tools_manifest import router as tools_manifest_router
from source_proxy.self_status import (
    build_action_preview,
    build_context_index_manifest,
    build_self_status_manifest,
    build_tools_manifest,
)


def _test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(action_preview_router)
    app.include_router(context_index_router)
    app.include_router(obsidian_context_router)
    app.include_router(self_status_router)
    app.include_router(tools_manifest_router)
    return app


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
        self.assertEqual(
            manifest["memory_context_diagnostics"]["obsidian_status"],
            "disabled",
        )
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
        client = TestClient(_test_app())
        response = client.get("/v1/self/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["service"], "source-proxy")
        self.assertIn("configured_roots", payload)
        self.assertIn("approval_boundaries", payload)
        self.assertEqual(payload["codex_cli_status"]["tool"], "codex_cli")
        self.assertFalse(payload["codex_cli_status"]["would_run_task"])
        self.assertIn("provider_capabilities", payload)
        self.assertFalse(payload["provider_capabilities"]["codex_cli"]["apply_authority"])

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
        self.assertIn("provider_capabilities", manifest)
        self.assertEqual(manifest["model_routes"][0]["alias"], "local")
        self.assertEqual(manifest["model_routes"][0]["model"], "ollama_chat/hermes4")
        self.assertIn("selected_via", manifest["model_routes"][0])
        self.assertIn("probe_ok", manifest["model_routes"][0])
        self.assertIn("requested_local_default", manifest["model_routes"][0])
        self.assertIn("resolved_model", manifest["model_routes"][0])
        self.assertIn("model_storage_status", manifest["model_routes"][0])
        self.assertEqual(manifest["provider_capabilities"]["local_ollama"]["status"], "config_blocked")
        self.assertTrue(manifest["provider_capabilities"]["local_ollama"]["recommendation_only"])
        self.assertFalse(manifest["provider_capabilities"]["local_ollama"]["apply_authority"])
        self.assertEqual(manifest["codex_cli_status"]["tool"], "codex_cli")
        self.assertFalse(manifest["codex_cli_status"]["approval_authority"])
        self.assertIn(
            "paid_api_chat_routes",
            {tool["name"] for tool in manifest["enabled_tools"]},
        )
        self.assertIn(
            "terminal_execution",
            {tool["name"] for tool in manifest["disabled_tools"]},
        )
        coding_surface = next(
            tool
            for tool in manifest["enabled_tools"]
            if tool["name"] == "coding_proxy_test_surface"
        )
        self.assertEqual(coding_surface["endpoint"], "GET /coding")
        self.assertEqual(coding_surface["feature_flag"], "SPIRIT_CODING_USE_PROXY")
        self.assertIn(
            "POST /v1/decisions/route",
            coding_surface["proxy_endpoints_used"],
        )
        self.assertIn(
            "research_preview",
            {tool["name"] for tool in manifest["disabled_tools"]},
        )
        workspace_tool = next(
            tool
            for tool in manifest["enabled_tools"]
            if tool["name"] == "workspace_read_only_tools"
        )
        self.assertEqual(workspace_tool["access"], "read_only_allowlisted_workspace")
        self.assertIn("POST /v1/workspace/read", workspace_tool["endpoints"])
        sandbox_tool = next(
            tool
            for tool in manifest["enabled_tools"]
            if tool["name"] == "sandboxed_terminal_run"
        )
        self.assertEqual(sandbox_tool["access"], "bubblewrap_sandboxed_terminal")
        self.assertFalse(sandbox_tool["limits"]["workspace_writable"])
        diff_tool = next(
            tool
            for tool in manifest["enabled_tools"]
            if tool["name"] == "diff_verification_preview"
        )
        self.assertEqual(diff_tool["access"], "read_only_diff_preview")
        self.assertFalse(diff_tool["limits"]["would_apply_diff"])
        long_task_tool = next(
            tool
            for tool in manifest["enabled_tools"]
            if tool["name"] == "long_running_task_tracker"
        )
        self.assertEqual(long_task_tool["access"], "read_only_status_tracking")
        self.assertFalse(long_task_tool["limits"]["executes_commands"])
        api_route = next(
            route
            for route in manifest["available_routes"]
            if route["route_type"] == "api_route"
        )
        self.assertEqual(api_route["approval"], "spend_before_send_required")
        coder_route = next(
            route
            for route in manifest["available_routes"]
            if route["next_prompt_action"] == "run_with_coder_agent"
        )
        self.assertEqual(coder_route["route_type"], "local_route")
        self.assertEqual(coder_route["display_name"], "Coder Agent")
        self.assertEqual(coder_route["execution_path"], "coder_agent")
        self.assertEqual(coder_route["status"], "available")

    def test_tools_manifest_lists_research_preview_when_enabled(self) -> None:
        with patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": "true"}, clear=False):
            manifest = build_tools_manifest([])

        research_tool = next(
            tool
            for tool in manifest["enabled_tools"]
            if tool["name"] == "research_preview"
        )
        self.assertEqual(research_tool["provider"], "searxng")
        self.assertEqual(research_tool["access"], "read_only_local_search_preview")
        self.assertEqual(research_tool["output_contract"], "title_url_snippet_sources_only")

    def test_tools_manifest_endpoint_returns_manifest(self) -> None:
        client = TestClient(_test_app())
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
        client = TestClient(_test_app())
        response = client.get("/v1/context/index")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["manifest_version"], "2.7A-3")
        self.assertIn("context_bundle_status", payload)
        self.assertIn("context_inclusion_policy", payload)
        self.assertIn("memory_context_diagnostics", payload)

    def test_obsidian_context_endpoint_is_disabled_by_default(self) -> None:
        client = TestClient(_test_app())
        with patch.dict(os.environ, {"OBSIDIAN_CONTEXT_ENABLED": ""}, clear=False):
            response = client.post(
                "/v1/context/obsidian/query",
                json={"task": "find notes about coder trials"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "disabled")
        self.assertFalse(payload["diagnostics"]["obsidian_context_used"])
        self.assertEqual(payload["notes"], [])

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

    def test_action_preview_requires_approval_for_create_file_action(self) -> None:
        preview = build_action_preview(
            action="create file",
            target="src/app/design-demo/coding/page.tsx",
        )

        self.assertEqual(preview["decision"], "requires_human_approval")
        self.assertTrue(preview["requires_human_approval"])
        self.assertFalse(preview["would_execute"])
        self.assertIn("implementation_or_terminal_action", preview["reason_codes"])

    def test_action_preview_requires_approval_for_implement_file_change_action(self) -> None:
        preview = build_action_preview(
            action="implement proposed file change",
            target="src/app/design-demo/coding/page.tsx",
        )

        self.assertEqual(preview["decision"], "requires_human_approval")
        self.assertTrue(preview["requires_human_approval"])
        self.assertFalse(preview["would_execute"])
        self.assertIn("implementation_or_terminal_action", preview["reason_codes"])

    def test_action_preview_endpoint_returns_preview_without_execution(self) -> None:
        client = TestClient(_test_app())
        response = client.post(
            "/v1/actions/preview",
            json={"action": "plan manual prompt packet", "route_type": "manual_route"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["manifest_version"], "2.7A-4")
        self.assertEqual(payload["decision"], "preview_only")
        self.assertFalse(payload["would_execute"])

    def test_action_preview_labels_research_preview_as_read_only(self) -> None:
        preview = build_action_preview(action="preview latest web sources")

        self.assertEqual(preview["decision"], "preview_only")
        self.assertFalse(preview["would_execute"])
        self.assertIn("research_preview_requested", preview["reason_codes"])
        self.assertIn("title, URL, and snippet", preview["safety_message"])


if __name__ == "__main__":
    unittest.main()
