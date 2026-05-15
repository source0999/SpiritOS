from __future__ import annotations

import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.diff_verification import router as diff_verification_router
from source_proxy.verification.diff import preview_diff_verification, validate_replacement_content


class DiffVerificationPreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self._apply_mock = mock.patch(
            "source_proxy.tasks.long_running.git_apply_check_for_preview",
            return_value=(True, ""),
        )
        self._apply_mock.start()

    def tearDown(self) -> None:
        self._apply_mock.stop()

    def test_typescript_diff_suggests_typecheck_and_lint(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/app/coding/page.tsx b/src/app/coding/page.tsx",
                    "--- a/src/app/coding/page.tsx",
                    "+++ b/src/app/coding/page.tsx",
                    "@@ -1 +1 @@",
                    "-old",
                    "+new",
                ]
            )
        )

        commands = [item["command"] for item in payload["suggested_commands"]]
        self.assertEqual(payload["tool"], "diff_verification_preview")
        self.assertEqual(payload["status"], "preview_ready")
        self.assertEqual(payload["risk"], "low")
        self.assertEqual(payload["changed_files"][0]["path"], "src/app/coding/page.tsx")
        self.assertEqual(payload["changed_files"][0]["change_type"], "modified")
        self.assertIn(["npm", "run", "typecheck"], commands)
        self.assertFalse(payload["self_correction"]["triggered"])
        self.assertFalse(payload["would_apply_diff"])
        self.assertFalse(payload["would_execute"])
        self.assertFalse(payload["limits"]["file_writes_allowed"])
        checks = payload["deterministic_checks"]
        self.assertEqual(checks[0]["tier"], 1)
        self.assertEqual(checks[0]["id"], "git_apply_check")
        self.assertEqual(checks[0]["status"], "passed")
        self.assertEqual(checks[1]["id"], "syntax_parse")
        self.assertIn(checks[2]["status"], {"skipped", "passed"})

    def test_local_route_sets_file_writes_allowed_when_safe(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/app/coding/page.tsx b/src/app/coding/page.tsx",
                    "--- a/src/app/coding/page.tsx",
                    "+++ b/src/app/coding/page.tsx",
                    "@@ -1 +1 @@",
                    "-old",
                    "+new",
                ]
            ),
            route_type="local_route",
        )
        self.assertEqual(payload["status"], "preview_ready")
        self.assertTrue(payload["limits"]["file_writes_allowed"])

    def test_local_route_keeps_file_writes_disallowed_when_blocked(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/.env.local b/.env.local",
                    "--- a/.env.local",
                    "+++ b/.env.local",
                    "@@ -1 +1 @@",
                    "-OLD=1",
                    "+NEW=1",
                ]
            ),
            route_type="local_route",
        )
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["limits"]["file_writes_allowed"])

    def test_coder_agent_next_prompt_sets_file_writes_without_route_type(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/app/coding/page.tsx b/src/app/coding/page.tsx",
                    "--- a/src/app/coding/page.tsx",
                    "+++ b/src/app/coding/page.tsx",
                    "@@ -1 +1 @@",
                    "-old",
                    "+new",
                ]
            ),
            next_prompt_action="run_with_coder_agent",
        )
        self.assertEqual(payload["status"], "preview_ready")
        self.assertTrue(payload["limits"]["file_writes_allowed"])

    def test_secret_shaped_path_is_blocked(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/.env.local b/.env.local",
                    "--- a/.env.local",
                    "+++ b/.env.local",
                    "@@ -1 +1 @@",
                    "-OLD=1",
                    "+NEW=1",
                ]
            )
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["risk"], "blocked")
        self.assertEqual(payload["blocked_reasons"][0]["reason_code"], "secret_shaped_path")
        self.assertTrue(payload["self_correction"]["triggered"])
        self.assertIn("regenerate the patch", payload["self_correction"]["safer_next_action"])
        self.assertIn(".env.local", payload["self_correction"]["retry_prompt"])

    def test_path_escape_is_blocked(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/../outside.txt b/../outside.txt",
                    "--- a/../outside.txt",
                    "+++ b/../outside.txt",
                    "@@ -1 +1 @@",
                    "-old",
                    "+new",
                ]
            )
        )

        reason_codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertIn("path_escape", reason_codes)
        self.assertEqual(payload["status"], "blocked")

    def test_router_returns_preview_payload(self) -> None:
        app = FastAPI()
        app.include_router(diff_verification_router)
        client = TestClient(app)

        response = client.post(
            "/v1/verification/diff-preview",
            json={
                "unified_diff": "\n".join(
                    [
                        "diff --git a/source_proxy/main.py b/source_proxy/main.py",
                        "--- a/source_proxy/main.py",
                        "+++ b/source_proxy/main.py",
                        "@@ -1 +1 @@",
                        "-old",
                        "+new",
                    ]
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["risk"], "high")
        self.assertEqual(payload["changed_files"][0]["risk_flags"], ["high_impact_file"])
        self.assertTrue(payload["self_correction"]["triggered"])
        self.assertEqual(payload["self_correction"]["severity"], "high")
        self.assertFalse(payload["limits"]["file_writes_allowed"])

    def test_git_apply_check_failure_blocks_preview(self) -> None:
        with mock.patch(
            "source_proxy.tasks.long_running.git_apply_check_for_preview",
            return_value=(False, "corrupt patch at line 2"),
        ):
            payload = preview_diff_verification(
                "\n".join(
                    [
                        "diff --git a/src/app/coding/page.tsx b/src/app/coding/page.tsx",
                        "--- a/src/app/coding/page.tsx",
                        "+++ b/src/app/coding/page.tsx",
                        "@@ -1 +1 @@",
                        "-old",
                        "+new",
                    ]
                ),
                route_type="local_route",
            )
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["git_apply_check_ok"])
        self.assertIn("corrupt patch", payload["git_apply_check_error"])
        checks = payload["deterministic_checks"]
        self.assertEqual(checks[0]["id"], "git_apply_check")
        self.assertEqual(checks[0]["status"], "failed")
        codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertIn("diff_apply_check_failed", codes)
        self.assertFalse(payload["limits"]["file_writes_allowed"])

    def test_invalid_tsx_diff_is_blocked_before_approval(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/app/coding/design-demo/page.tsx b/src/app/coding/design-demo/page.tsx",
                    "new file mode 100644",
                    "index 0000000..1111111",
                    "--- /dev/null",
                    "+++ b/src/app/coding/design-demo/page.tsx",
                    "@@ -0,0 +1,6 @@",
                    "+Target file: src/app/coding/design-demo/page.tsx",
                    "+",
                    "+Make it a beautif",
                    "+",
                    "+export default function Page() {",
                    "+  return <main />;",
                ]
            ),
            route_type="local_route",
        )

        self.assertEqual(payload["status"], "blocked")
        codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertIn("typescript_syntax_or_typecheck_failed", codes)
        self.assertFalse(payload["limits"]["file_writes_allowed"])
        self.assertIn("TS", payload["typescript_check"]["summary"])

    def test_valid_new_tsx_diff_remains_preview_ready(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/app/coding/valid-preview/page.tsx b/src/app/coding/valid-preview/page.tsx",
                    "new file mode 100644",
                    "index 0000000..1111111",
                    "--- /dev/null",
                    "+++ b/src/app/coding/valid-preview/page.tsx",
                    "@@ -0,0 +1,5 @@",
                    "+export default function Page() {",
                    '+  return <main className="min-h-screen">Valid preview</main>;',
                    "+}",
                    "+",
                    "+",
                ]
            ),
            route_type="local_route",
        )

        self.assertEqual(payload["status"], "preview_ready")
        self.assertTrue(payload["typescript_check"]["ok"])
        self.assertTrue(payload["limits"]["file_writes_allowed"])

    def test_design_demo_diff_blocks_when_exact_requirements_missing(self) -> None:
        task = "\n".join(
            [
                "Target file: src/app/coding/design-demo/page.tsx",
                "Create a brand new clean design-demo page at /coding/design-demo.",
                'Big centered <h1 className="text-6xl font-light tracking-tighter">Design Demo — Vibe Test Canvas</h1>',
                'Import GlassPanel from "@/components/ui/GlassPanel"',
            ]
        )
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/app/coding/design-demo/page.tsx b/src/app/coding/design-demo/page.tsx",
                    "new file mode 100644",
                    "index 0000000..1111111",
                    "--- /dev/null",
                    "+++ b/src/app/coding/design-demo/page.tsx",
                    "@@ -0,0 +1,5 @@",
                    "+export default function Page() {",
                    '+  return <main><h1 className="text-xl">Design Demo</h1></main>;',
                    "+}",
                    "+",
                    "+",
                ]
            ),
            route_type="local_route",
            task_text=task,
        )

        self.assertEqual(payload["status"], "blocked")
        codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertIn("requirement_coverage_failed", codes)
        missing = payload["requirement_coverage"]["missing"]
        self.assertIn("missing exact text: Design Demo — Vibe Test Canvas", missing)
        self.assertNotIn("missing exact text: text-6xl font-light tracking-tighter", missing)
        self.assertIn("missing className: text-6xl", missing)
        self.assertIn("missing import: GlassPanel from @/components/ui/GlassPanel", missing)
        self.assertFalse(payload["limits"]["file_writes_allowed"])

    def test_design_demo_diff_passes_when_exact_requirements_present(self) -> None:
        task = "\n".join(
            [
                "Target file: src/app/coding/design-demo/page.tsx",
                "Create a brand new clean design-demo page at /coding/design-demo.",
                'Big centered <h1 className="text-6xl font-light tracking-tighter">Design Demo — Vibe Test Canvas</h1>',
                'Import GlassPanel from "@/components/ui/GlassPanel"',
            ]
        )
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/app/coding/design-demo/page.tsx b/src/app/coding/design-demo/page.tsx",
                    "new file mode 100644",
                    "index 0000000..1111111",
                    "--- /dev/null",
                    "+++ b/src/app/coding/design-demo/page.tsx",
                    "@@ -0,0 +1,12 @@",
                    '+import { GlassPanel } from "@/components/ui/GlassPanel";',
                    "+",
                    "+export default function Page() {",
                    "+  return (",
                    '+    <main className="min-h-screen bg-black">',
                    '+      <GlassPanel><h1 className="text-6xl font-light tracking-tighter">Design Demo — Vibe Test Canvas</h1></GlassPanel>',
                    "+    </main>",
                    "+  );",
                    "+}",
                    "+",
                    "+",
                    "+",
                ]
            ),
            route_type="local_route",
            task_text=task,
        )

        self.assertEqual(payload["status"], "preview_ready")
        self.assertTrue(payload["requirement_coverage"]["ok"])

    def test_valid_full_replacement_content_passes(self) -> None:
        import tempfile
        from pathlib import Path

        task = "\n".join(
            [
                "Target file: src/app/coding/design-demo/page.tsx",
                "Create a brand new clean design-demo page at /coding/design-demo.",
                'Big centered <h1 className="text-6xl font-light tracking-tighter">Design Demo — Vibe Test Canvas</h1>',
                'Import GlassPanel from "@/components/ui/GlassPanel"',
            ]
        )
        content = (
            'import { GlassPanel } from "@/components/ui/GlassPanel";\n\n'
            "const panels = ['Motion', 'Glass'];\n\n"
            "export default function Page() {\n"
            "  return (\n"
            '    <main className="min-h-screen bg-black">\n'
            '      <h1 className="text-6xl font-light tracking-tighter">Design Demo — Vibe Test Canvas</h1>\n'
            "      {panels.map((panel) => <GlassPanel key={panel}>{panel}</GlassPanel>)}\n"
            "    </main>\n"
            "  );\n"
            "}\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_replacement_content(
                workspace_root=Path(tmp),
                target_path="src/app/coding/design-demo/page.tsx",
                content=content,
                task_text=task,
            )

        self.assertTrue(result["ok"], result)

    def test_replacement_content_transform_patterns_require_final_text_only(self) -> None:
        import tempfile
        from pathlib import Path

        tasks = [
            'Change "gap-2" to "gap-1.5"',
            'Replace "gap-2" with "gap-1.5"',
            'Rename "gap-2" to "gap-1.5"',
            'Swap "gap-2" for "gap-1.5"',
            'Update the class from "gap-2" to "gap-1.5"',
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for task in tasks:
                with self.subTest(task=task):
                    result = validate_replacement_content(
                        workspace_root=Path(tmp),
                        target_path="src/app/demo/classes.txt",
                        content='className="gap-1.5"',
                        task_text=task,
                    )

                    self.assertTrue(result["ok"], result)

    def test_replacement_content_change_fails_when_final_text_missing(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            result = validate_replacement_content(
                workspace_root=Path(tmp),
                target_path="src/app/demo/classes.txt",
                content='className="gap-2"',
                task_text='Change "gap-2" to "gap-1.5"',
            )

        self.assertFalse(result["ok"])
        self.assertIn("missing exact text: gap-1.5", result["missing"])
        self.assertNotIn("missing exact text: gap-2", result["missing"])

    def test_replacement_content_add_keeps_normal_final_text_requirement(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            result = validate_replacement_content(
                workspace_root=Path(tmp),
                target_path="src/app/demo/classes.txt",
                content='className="gap-2"',
                task_text='Add "transition-all duration-200 ease-out"',
            )

        self.assertFalse(result["ok"])
        self.assertIn(
            "missing exact text: transition-all duration-200 ease-out",
            result["missing"],
        )

    def test_replacement_content_missing_h1_blocks(self) -> None:
        import tempfile
        from pathlib import Path

        task = "Target file: src/app/coding/design-demo/page.tsx\nDesign Demo — Vibe Test Canvas"
        content = (
            'import { GlassPanel } from "@/components/ui/GlassPanel";\n'
            'export default function Page() { return <main className="min-h-screen"><GlassPanel /><GlassPanel /></main>; }\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_replacement_content(
                workspace_root=Path(tmp),
                target_path="src/app/coding/design-demo/page.tsx",
                content=content,
                task_text=task,
            )

        self.assertFalse(result["ok"])
        self.assertIn("missing exact text: Design Demo — Vibe Test Canvas", result["missing"])

    def test_replacement_content_missing_glasspanel_import_blocks(self) -> None:
        import tempfile
        from pathlib import Path

        content = (
            "export default function Page() {\n"
            '  return <main className="min-h-screen"><h1 className="text-6xl font-light tracking-tighter">Design Demo — Vibe Test Canvas</h1></main>;\n'
            "}\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_replacement_content(
                workspace_root=Path(tmp),
                target_path="src/app/coding/design-demo/page.tsx",
                content=content,
                task_text='Import GlassPanel from "@/components/ui/GlassPanel"',
            )

        self.assertFalse(result["ok"])
        self.assertIn("missing GlassPanel import", result["missing"])

    def test_replacement_content_raw_prompt_text_blocks(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            result = validate_replacement_content(
                workspace_root=Path(tmp),
                target_path="src/app/demo/page.tsx",
                content="Target file: src/app/demo/page.tsx\nexport default function Page() { return <main />; }\n",
                task_text="Target file: src/app/demo/page.tsx",
            )

        self.assertFalse(result["ok"])
        self.assertIn("raw prompt text detected: Target file:", result["missing"])

    def test_replacement_content_duplicate_h1_blocks(self) -> None:
        import tempfile
        from pathlib import Path

        content = (
            'import { GlassPanel } from "@/components/ui/GlassPanel";\n'
            "export default function Page() {\n"
            '  return <main className="min-h-screen"><h1 className="text-6xl font-light tracking-tighter">Design Demo — Vibe Test Canvas</h1><GlassPanel><h1>Design Demo — Vibe Test Canvas</h1></GlassPanel><GlassPanel /></main>;\n'
            "}\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_replacement_content(
                workspace_root=Path(tmp),
                target_path="src/app/coding/design-demo/page.tsx",
                content=content,
                task_text="Target file: src/app/coding/design-demo/page.tsx",
            )

        self.assertFalse(result["ok"])
        self.assertIn("duplicate nested h1 detected", result["missing"])

    def test_no_exact_requirements_are_not_overblocked(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/app/coding/simple/page.tsx b/src/app/coding/simple/page.tsx",
                    "new file mode 100644",
                    "index 0000000..1111111",
                    "--- /dev/null",
                    "+++ b/src/app/coding/simple/page.tsx",
                    "@@ -0,0 +1,4 @@",
                    "+export default function Page() {",
                    '+  return <main className="min-h-screen">Simple</main>;',
                    "+}",
                    "+",
                ]
            ),
            route_type="local_route",
            task_text="Create a simple page.",
        )

        self.assertEqual(payload["status"], "preview_ready")
        self.assertTrue(payload["requirement_coverage"]["ok"])
        self.assertTrue(payload["requirement_coverage"]["skipped"])

    def test_output_only_diff_task_blocks_raw_task_text_in_code(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/notes/manual.md b/notes/manual.md",
                    "new file mode 100644",
                    "index 0000000..1111111",
                    "--- /dev/null",
                    "+++ b/notes/manual.md",
                    "@@ -0,0 +1,2 @@",
                    "+Target file: notes/manual.md",
                    "+Here is the implementation.",
                ]
            ),
            task_text="Output ONLY a clean unified diff for notes/manual.md.",
        )

        self.assertEqual(payload["status"], "blocked")
        codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertIn("requirement_coverage_failed", codes)


class SanitizeUnifiedDiffTests(unittest.TestCase):
    def test_prefixes_bare_context_lines_when_env_enabled(self) -> None:
        import os
        from unittest import mock

        from source_proxy.verification.diff import sanitize_unified_diff_for_git_apply

        raw = "\n".join(
            [
                "diff --git a/foo.ts b/foo.ts",
                "--- a/foo.ts",
                "+++ b/foo.ts",
                "@@ -1,3 +1,3 @@",
                " context line",
                "-old",
                'import { x } from "y";',
                '+import { x } from "z";',
            ]
        )
        with mock.patch.dict(os.environ, {"SOURCE_PROXY_DIFF_PREFIX_BARE_LINES": "1"}):
            fixed = sanitize_unified_diff_for_git_apply(raw)
        self.assertIn('\n import { x } from "y";', fixed)

    def test_repair_llm_typo_plus_side_and_counts(self) -> None:
        from source_proxy.verification.diff import sanitize_unified_diff_for_git_apply

        raw = "\n".join(
            [
                "diff --git a/t.txt b/t.txt",
                "--- a/t.txt",
                "+++ b/t.txt",
                "@@ -1,9 +9 @@",
                "a",
                "-b",
                "+c",
            ]
        )
        fixed = sanitize_unified_diff_for_git_apply(raw)
        self.assertIn("@@ -1,2 +1,2 @@", fixed)


if __name__ == "__main__":
    unittest.main()
