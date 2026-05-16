from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from source_proxy.tasks.long_running import (
    _new_file_relpaths_from_unified_diff,
    _next_app_router_duplicate_route_files,
    _next_app_router_route_hint,
    _normalize_next_app_router_diff_targets,
    _pick_apply_workspace_root_and_candidate,
    _unified_diff_adds_new_file_at,
    next_app_router_path_to_route,
    next_app_router_route_to_path,
)


class NextAppRouterMappingTests(unittest.TestCase):
    def test_route_to_path_mapping_is_segment_ordered(self) -> None:
        self.assertEqual(
            next_app_router_route_to_path("/coding/design-demo"),
            "src/app/coding/design-demo/page.tsx",
        )
        self.assertEqual(
            next_app_router_route_to_path("/design-demo/coding"),
            "src/app/design-demo/coding/page.tsx",
        )

    def test_route_groups_are_not_public_url_segments(self) -> None:
        self.assertEqual(
            next_app_router_path_to_route("src/app/(dashboard)/page.tsx"),
            "/",
        )
        self.assertEqual(
            next_app_router_path_to_route("src/app/(dashboard)/coding/page.tsx"),
            "/coding",
        )

    def test_private_folders_are_not_routable(self) -> None:
        self.assertIsNone(
            next_app_router_path_to_route("src/app/_internal/coding/page.tsx"),
        )
        self.assertIsNone(next_app_router_route_to_path("/_internal/coding"))

    def test_route_mismatch_warns_without_retargeting(self) -> None:
        hint = _next_app_router_route_hint(
            Path.cwd(),
            "src/app/design-demo/coding/page.tsx",
            requested_route="/coding/design-demo",
        )

        self.assertIn("src/app/coding/design-demo/page.tsx", hint or "")
        self.assertIn("src/app/design-demo/coding/page.tsx", hint or "")

    def test_duplicate_route_files_warn_without_normalizing_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary = root / "src/app/coding/page.tsx"
            duplicate = root / "src/app/(dashboard)/coding/page.tsx"
            primary.parent.mkdir(parents=True, exist_ok=True)
            duplicate.parent.mkdir(parents=True, exist_ok=True)
            primary.write_text("export default function Page() { return null }\n")
            duplicate.write_text("export default function Page() { return null }\n")

            self.assertEqual(
                _next_app_router_duplicate_route_files(root, "src/app/coding/page.tsx"),
                ["src/app/(dashboard)/coding/page.tsx"],
            )
            self.assertIn(
                "warning only",
                _next_app_router_route_hint(root, "src/app/coding/page.tsx") or "",
            )

    def test_normalizer_does_not_retarget_explicit_design_demo_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            other = root / "src/app/design-demo/coding/page.tsx"
            other.parent.mkdir(parents=True, exist_ok=True)
            other.write_text("line1\n")
            diff = "\n".join(
                [
                    "diff --git a/src/app/coding/design-demo/page.tsx b/src/app/coding/design-demo/page.tsx",
                    "--- a/src/app/coding/design-demo/page.tsx",
                    "+++ b/src/app/coding/design-demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-line1",
                    "+line2",
                ]
            )

            changed, out, did = _normalize_next_app_router_diff_targets(
                [root],
                [{"path": "src/app/coding/design-demo/page.tsx"}],
                diff,
            )

            self.assertFalse(did)
            self.assertEqual(changed[0]["path"], "src/app/coding/design-demo/page.tsx")
            self.assertIn("src/app/coding/design-demo/page.tsx", out)
            self.assertNotIn("src/app/design-demo/coding/page.tsx", out)

    def test_new_file_relpaths_parsed_from_dev_null(self) -> None:
        diff = "\n".join(
            [
                "diff --git a/x b/y",
                "new file mode 100644",
                "--- /dev/null",
                "+++ b/src/app/coding/design-demo/page.tsx",
                "@@ -0,0 +1 @@",
                "+z",
            ]
        )
        self.assertEqual(
            _new_file_relpaths_from_unified_diff(diff),
            {"src/app/coding/design-demo/page.tsx"},
        )

    def test_execute_pick_does_not_require_blob_for_pure_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text("{}\n", encoding="utf-8")
            (root / "src").mkdir()
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "t@e.st"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
            subprocess.run(["git", "add", "package.json"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-m", "init"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            diff = (
                "\n".join(
                    [
                        "diff --git a/src/app/coding/design-demo/page.tsx b/src/app/coding/design-demo/page.tsx",
                        "new file mode 100644",
                        "--- /dev/null",
                        "+++ b/src/app/coding/design-demo/page.tsx",
                        "@@ -0,0 +1,3 @@",
                        "+// hi",
                        "+export default function Page() { return null }",
                        "+",
                    ]
                )
                + "\n"
            )
            failures: list[str] = []
            with mock.patch(
                "source_proxy.tasks.long_running._ordered_workspace_roots_for_apply",
                return_value=[root],
            ):
                picked = _pick_apply_workspace_root_and_candidate(
                    unified_diff=diff,
                    changed_files=[{"path": "src/app/coding/design-demo/page.tsx"}],
                    patch_candidates=[diff],
                    check_failures=failures,
                    require_existing_targets=True,
                )
            self.assertIsNotNone(picked)
            self.assertEqual(picked[0].resolve(), root.resolve())

    def test_new_file_detection_keeps_explicit_path(self) -> None:
        diff = "\n".join(
            [
                "diff --git a/src/app/coding/design-demo/page.tsx b/src/app/coding/design-demo/page.tsx",
                "new file mode 100644",
                "--- /dev/null",
                "+++ b/src/app/coding/design-demo/page.tsx",
                "@@ -0,0 +1,1 @@",
                "+x",
            ]
        )

        self.assertTrue(
            _unified_diff_adds_new_file_at(
                diff,
                "src/app/coding/design-demo/page.tsx",
            ),
        )


if __name__ == "__main__":
    unittest.main()
