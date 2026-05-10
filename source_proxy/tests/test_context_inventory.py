from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from source_proxy.context.inventory import build_safe_context_inventory
from source_proxy.main import app


class SafeContextInventoryTests(unittest.TestCase):
    def test_inventory_reports_verified_roots_without_contents_or_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "repomix-output.xml").write_text(
                "SECRET_SHOULD_NOT_APPEAR",
                encoding="utf-8",
            )

            inventory = build_safe_context_inventory(root)

        self.assertEqual(inventory["inventory_version"], "2.8-1")
        self.assertIn("without reading file contents", inventory["access_scope"])
        self.assertFalse(inventory["inventory_limits"]["file_contents_included"])
        self.assertFalse(inventory["inventory_limits"]["directory_entries_included"])
        self.assertFalse(inventory["inventory_limits"]["recursive_expansion"])
        self.assertGreaterEqual(len(inventory["verified_context_roots"]), 1)
        self.assertNotIn("SECRET_SHOULD_NOT_APPEAR", str(inventory))

    def test_inventory_distinguishes_unavailable_and_windows_allowlisted_roots(self) -> None:
        env = {
            "SPIRIT_PROJECT_PATH": "/path/that/does/not/exist",
            "SPIRIT_WINDOWS_FS_ENABLED": "true",
            "SPIRIT_WINDOWS_FS_BASE_URL": "http://windows-host:3000",
            "SPIRIT_WINDOWS_FS_TOKEN": "secret-token",
            "SPIRIT_WINDOWS_FS_ALLOWLIST": "C:\\Projects,C:\\Dev",
        }
        with patch.dict(os.environ, env, clear=False):
            inventory = build_safe_context_inventory(Path.cwd())

        unavailable_paths = {item["path"] for item in inventory["unavailable_roots"]}
        verified_paths = {item["path"] for item in inventory["verified_context_roots"]}
        self.assertIn("/path/that/does/not/exist", unavailable_paths)
        self.assertIn("C:\\Projects", verified_paths)
        self.assertIn("C:\\Dev", verified_paths)
        self.assertNotIn("secret-token", str(inventory))

    def test_inventory_policy_blocks_broad_and_secret_shaped_paths(self) -> None:
        inventory = build_safe_context_inventory(Path.cwd())
        policy = inventory["blocked_paths_policy"]

        self.assertTrue(policy["no_arbitrary_drive_browsing"])
        self.assertTrue(policy["no_recursive_expansion_by_default"])
        self.assertTrue(policy["no_hidden_files"])
        self.assertIn(".env", policy["blocked_name_patterns"])
        self.assertIn("C:\\Windows", policy["blocked_path_prefixes"])

    def test_context_inventory_endpoint_returns_structured_inventory(self) -> None:
        client = TestClient(app)
        response = client.get("/v1/context/inventory")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["inventory_version"], "2.8-1")
        self.assertIn("verified_context_roots", payload)
        self.assertIn("blocked_paths_policy", payload)
        self.assertIn("available_read_only_sources", payload)
        self.assertIn("next_context_selection_action", payload)


if __name__ == "__main__":
    unittest.main()
