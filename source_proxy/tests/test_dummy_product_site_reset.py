from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from source_proxy.main import app


FIXTURE_ROOT = Path("tests/ui-agent-trials/fixtures/dummy-product-site")


def target_packet(prompt_id: str = "coder-001-init-dummy-product-site") -> dict[str, object]:
    contexts = {
        "coder-001-init-dummy-product-site": "init-storefront",
        "coder-002-add-product-data": "product-data",
    }
    return {
        "selected_prompt_id": prompt_id,
        "target_plugin": {
            "schema_version": "spiritos-target-plugin/v1",
            "id": "lumacart",
            "repository_id": "spiritos-campaign-1",
            "worktree_id": "spiritos-campaign-1-20260712",
            "fixture_root": "tests/ui-agent-trials/fixtures/dummy-product-site/",
            "selected_prompt_id": prompt_id,
            "selected_context_id": contexts[prompt_id],
            "execution_profile": "coder-10",
        },
    }


def initialize_workspace_git(workspace: Path) -> None:
    workspace.joinpath(".target-plugin-baseline").write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(workspace)], check=True)
    subprocess.run(["git", "-C", str(workspace), "config", "user.email", "campaign-test@local"], check=True)
    subprocess.run(["git", "-C", str(workspace), "config", "user.name", "Campaign Test"], check=True)
    subprocess.run(["git", "-C", str(workspace), "add", "."], check=True)
    subprocess.run(["git", "-C", str(workspace), "commit", "-qm", "target plugin baseline"], check=True)


class DummyProductSiteResetTests(unittest.TestCase):
    def test_reset_route_removes_only_fixed_fixture_and_writes_verified_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir).resolve()
            fixture = workspace / FIXTURE_ROOT
            fixture.joinpath("src").mkdir(parents=True)
            fixture.joinpath("index.html").write_text("<h1>LumaCart</h1>", encoding="utf-8")
            fixture.joinpath("src", "main.js").write_text("export {};", encoding="utf-8")
            untouched = workspace / "unrelated-user-work.txt"
            untouched.write_text("preserve me", encoding="utf-8")
            initialize_workspace_git(workspace)

            with patch("source_proxy.api.codex_adapter.Path.cwd", return_value=workspace):
                response = TestClient(app).post(
                    "/v1/coding/dummy-product-site/reset",
                    json=target_packet(),
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(
                set(payload),
                {
                    "status",
                    "reset_verified",
                    "fixture_root",
                    "existed",
                    "removed_paths",
                    "clean_verified",
                    "reset_receipt_id",
                    "target_plugin_identity",
                },
            )
            self.assertEqual(payload["status"], "reset_verified")
            self.assertTrue(payload["reset_verified"])
            self.assertEqual(
                payload["fixture_root"],
                "tests/ui-agent-trials/fixtures/dummy-product-site/",
            )
            self.assertTrue(payload["existed"])
            self.assertEqual(payload["removed_paths"], [payload["fixture_root"]])
            self.assertTrue(payload["clean_verified"])
            self.assertTrue(payload["reset_receipt_id"].startswith("dummy-product-site-reset-"))
            self.assertEqual(payload["target_plugin_identity"]["selected_prompt_id"], "coder-001-init-dummy-product-site")
            self.assertFalse(fixture.exists())
            self.assertEqual(untouched.read_text(encoding="utf-8"), "preserve me")

            receipt_path = (
                workspace
                / "data"
                / "source-proxy"
                / f"{payload['reset_receipt_id']}.json"
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            for key, value in payload.items():
                self.assertEqual(receipt[key], value)
            self.assertEqual(receipt["receipt_type"], "dummy_product_site_reset.v1")
            self.assertEqual(
                receipt["scope"],
                {
                    "fixed_fixture_only": True,
                    "generic_cleanup_tasks_started": False,
                },
            )

    def test_reset_route_is_idempotent_and_verifies_missing_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir).resolve()
            initialize_workspace_git(workspace)
            with patch("source_proxy.api.codex_adapter.Path.cwd", return_value=workspace):
                response = TestClient(app).post("/v1/coding/dummy-product-site/reset", json=target_packet())

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["reset_verified"])
            self.assertFalse(payload["existed"])
            self.assertEqual(payload["removed_paths"], [])
            self.assertTrue(payload["clean_verified"])
            receipt_path = workspace / "data" / "source-proxy" / f"{payload['reset_receipt_id']}.json"
            self.assertTrue(receipt_path.is_file())

    def test_reset_route_fails_closed_if_fixed_root_is_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir).resolve()
            outside = workspace / "outside"
            outside.mkdir()
            marker = outside / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            initialize_workspace_git(workspace)

            with (
                patch("source_proxy.api.codex_adapter.Path.cwd", return_value=workspace),
                patch(
                    "source_proxy.api.codex_adapter.DUMMY_PRODUCT_SITE_FIXTURE_ROOT",
                    "outside",
                ),
            ):
                response = TestClient(app).post("/v1/coding/dummy-product-site/reset", json=target_packet())

            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["detail"]["reason_code"], "unsafe_reset_target")
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            self.assertFalse((workspace / "data" / "source-proxy").exists())

    def test_reset_route_rejects_a_linked_fixture_path_before_removal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir).resolve()
            fixture = workspace / FIXTURE_ROOT
            fixture.mkdir(parents=True)
            marker = fixture / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            initialize_workspace_git(workspace)

            with (
                patch("source_proxy.api.codex_adapter.Path.cwd", return_value=workspace),
                patch(
                    "source_proxy.api.codex_adapter._path_is_link_like",
                    side_effect=lambda path: path.name == "dummy-product-site",
                ),
            ):
                response = TestClient(app).post("/v1/coding/dummy-product-site/reset", json=target_packet())

            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["detail"]["reason_code"], "unsafe_reset_target")
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            self.assertFalse((workspace / "data" / "source-proxy").exists())

    def test_reset_route_fails_closed_without_prompt_1_plugin_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir).resolve()
            initialize_workspace_git(workspace)
            with patch("source_proxy.api.codex_adapter.Path.cwd", return_value=workspace):
                missing = TestClient(app).post("/v1/coding/dummy-product-site/reset", json={})
                wrong_prompt = TestClient(app).post(
                    "/v1/coding/dummy-product-site/reset", json=target_packet("coder-002-add-product-data")
                )

            self.assertEqual(missing.status_code, 409)
            self.assertEqual(missing.json()["detail"]["reason_code"], "target_plugin_missing")
            self.assertEqual(wrong_prompt.status_code, 409)
            self.assertEqual(wrong_prompt.json()["detail"]["reason_code"], "target_plugin_reset_prompt_mismatch")


if __name__ == "__main__":
    unittest.main()
