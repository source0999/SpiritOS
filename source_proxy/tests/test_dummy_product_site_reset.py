from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from source_proxy.main import app


FIXTURE_ROOT = Path("tests/ui-agent-trials/fixtures/dummy-product-site")


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

            with patch("source_proxy.api.codex_adapter.Path.cwd", return_value=workspace):
                response = TestClient(app).post(
                    "/v1/coding/dummy-product-site/reset",
                    json={"fixture_root": "unrelated-user-work.txt"},
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
            with patch("source_proxy.api.codex_adapter.Path.cwd", return_value=workspace):
                response = TestClient(app).post("/v1/coding/dummy-product-site/reset")

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

            with (
                patch("source_proxy.api.codex_adapter.Path.cwd", return_value=workspace),
                patch(
                    "source_proxy.api.codex_adapter.DUMMY_PRODUCT_SITE_FIXTURE_ROOT",
                    "outside",
                ),
            ):
                response = TestClient(app).post("/v1/coding/dummy-product-site/reset")

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

            with (
                patch("source_proxy.api.codex_adapter.Path.cwd", return_value=workspace),
                patch(
                    "source_proxy.api.codex_adapter._path_is_link_like",
                    side_effect=lambda path: path.name == "dummy-product-site",
                ),
            ):
                response = TestClient(app).post("/v1/coding/dummy-product-site/reset")

            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["detail"]["reason_code"], "unsafe_reset_target")
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            self.assertFalse((workspace / "data" / "source-proxy").exists())


if __name__ == "__main__":
    unittest.main()
