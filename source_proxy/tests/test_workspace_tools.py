from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.workspace_tools import router as workspace_tools_router
from source_proxy.context.workspace_tools import (
    WorkspaceToolError,
    list_workspace_path,
    read_workspace_excerpt,
)


class WorkspaceReadOnlyToolsTests(unittest.TestCase):
    def test_list_workspace_path_returns_safe_non_recursive_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "src" / "app.ts").write_text("console.log('ok')", encoding="utf-8")
            (root / ".env").write_text("SECRET=1", encoding="utf-8")

            payload = list_workspace_path("src", project_root=root)

        self.assertEqual(payload["tool"], "workspace_list")
        self.assertEqual(payload["path"], "src")
        self.assertEqual(payload["entries"][0]["path"], "src/app.ts")
        self.assertNotIn("SECRET=1", str(payload))
        self.assertFalse(payload["limits"]["recursive"])

    def test_list_workspace_root_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("ok", encoding="utf-8")
            (root / ".hidden").write_text("hidden", encoding="utf-8")

            payload = list_workspace_path(".", project_root=root)

        self.assertEqual(payload["path"], ".")
        self.assertEqual([entry["path"] for entry in payload["entries"]], ["README.md"])

    def test_read_workspace_excerpt_returns_limited_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("abcdef", encoding="utf-8")

            payload = read_workspace_excerpt("README.md", project_root=root, max_bytes=3)

        self.assertEqual(payload["tool"], "workspace_read_excerpt")
        self.assertEqual(payload["path"], "README.md")
        self.assertEqual(payload["excerpt"], "abc")
        self.assertTrue(payload["truncated"])
        self.assertFalse(payload["limits"]["writes_allowed"])

    def test_read_workspace_excerpt_blocks_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            with self.assertRaises(WorkspaceToolError) as error:
                read_workspace_excerpt("../outside.txt", project_root=root)

        self.assertEqual(error.exception.reason_code, "path_escape")

    def test_read_workspace_excerpt_blocks_secret_shaped_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "token.txt").write_text("SECRET=1", encoding="utf-8")

            with self.assertRaises(WorkspaceToolError) as error:
                read_workspace_excerpt("token.txt", project_root=root)

        self.assertEqual(error.exception.reason_code, "blocked_path")

    def test_workspace_router_returns_structured_errors(self) -> None:
        app = FastAPI()
        app.include_router(workspace_tools_router)
        client = TestClient(app)

        response = client.post(
            "/v1/workspace/read",
            json={"path": "C:\\Windows\\system.ini"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["reason_code"], "path_escape")


if __name__ == "__main__":
    unittest.main()
