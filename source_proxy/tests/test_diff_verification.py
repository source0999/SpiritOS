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

    def test_dot_slash_secret_shaped_path_is_blocked(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/./.env.local b/./.env.local",
                    "--- a/./.env.local",
                    "+++ b/./.env.local",
                    "@@ -1 +1 @@",
                    "-OLD=1",
                    "+NEW=1",
                ]
            )
        )

        reason_codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("secret_shaped_path", reason_codes)

    def test_certificate_key_path_is_blocked(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/certificates/spirit-dev-key.pem b/certificates/spirit-dev-key.pem",
                    "--- a/certificates/spirit-dev-key.pem",
                    "+++ b/certificates/spirit-dev-key.pem",
                    "@@ -1 +1 @@",
                    "-OLD",
                    "+NEW",
                ]
            )
        )

        reason_codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["risk"], "blocked")
        self.assertFalse(payload["limits"]["file_writes_allowed"])
        self.assertIn("secret_shaped_path", reason_codes)
        self.assertIn("protected_path", reason_codes)

    def test_ssh_private_key_path_is_blocked(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/.ssh/id_rsa b/.ssh/id_rsa",
                    "--- a/.ssh/id_rsa",
                    "+++ b/.ssh/id_rsa",
                    "@@ -1 +1 @@",
                    "-OLD",
                    "+NEW",
                ]
            )
        )

        reason_codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["risk"], "blocked")
        self.assertFalse(payload["limits"]["file_writes_allowed"])
        self.assertFalse(payload["would_apply_diff"])
        self.assertFalse(payload["would_execute"])
        self.assertIn("secret_shaped_path", reason_codes)
        self.assertIn("protected_path", reason_codes)

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

    def test_percent_encoded_traversal_paths_are_blocked_by_policy(self) -> None:
        for path in ("%2e%2e/outside.md", "%252e%252e%252foutside.md"):
            with self.subTest(path=path):
                payload = preview_diff_verification(
                    "\n".join(
                        [
                            f"diff --git a/{path} b/{path}",
                            f"--- a/{path}",
                            f"+++ b/{path}",
                            "@@ -1 +1 @@",
                            "-old",
                            "+new",
                        ]
                    )
                )

                reason_codes = {
                    item["reason_code"] for item in payload["blocked_reasons"]
                }
                self.assertEqual(payload["status"], "blocked")
                self.assertFalse(payload["limits"]["file_writes_allowed"])
                self.assertFalse(payload["would_apply_diff"])
                self.assertIn("encoded_path_not_allowed", reason_codes)

    def test_windows_slash_path_escape_is_blocked(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/..\\outside.txt b/..\\outside.txt",
                    "--- a/..\\outside.txt",
                    "+++ b/..\\outside.txt",
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

    def test_dummy_product_site_package_is_not_high_impact(self) -> None:
        app = FastAPI()
        app.include_router(diff_verification_router)
        client = TestClient(app)

        response = client.post(
            "/v1/verification/diff-preview",
            json={
                "task_spec": {
                    "allowed_files": ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
                    "target": "tests/ui-agent-trials/fixtures/dummy-product-site/",
                    "task_type": "create_file_bundle",
                },
                "unified_diff": "\n".join(
                    [
                        "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/package.json b/tests/ui-agent-trials/fixtures/dummy-product-site/package.json",
                        "new file mode 100644",
                        "--- /dev/null",
                        "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/package.json",
                        "@@ -0,0 +1 @@",
                        '+{"name":"lumacart-dummy","private":true}',
                    ]
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "preview_ready")
        self.assertEqual(payload["risk"], "low")
        self.assertEqual(payload["changed_files"][0]["risk_flags"], [])
        checks = {item["id"]: item for item in payload["deterministic_checks"]}
        self.assertEqual(checks["syntax_parse"]["status"], "skipped")
        self.assertTrue(checks["syntax_parse"]["blocking"])
        self.assertTrue(
            all(
                item["status"] in {"passed", "skipped"}
                for item in payload["deterministic_checks"]
                if item["blocking"]
            )
        )

    def test_manual_result_preview_blocks_secret_shaped_path(self) -> None:
        app = FastAPI()
        app.include_router(diff_verification_router)
        client = TestClient(app)

        response = client.post(
            "/v1/verification/manual-result-preview",
            json={
                "payload": "\n".join(
                    [
                        "diff --git a/.env.local b/.env.local",
                        "--- a/.env.local",
                        "+++ b/.env.local",
                        "@@ -1 +1 @@",
                        "-OLD=1",
                        "+NEW=1",
                    ]
                ),
                "route_type": "local_route",
            },
        )

        payload = response.json()
        reason_codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["limits"]["file_writes_allowed"])
        self.assertIn("secret_shaped_path", reason_codes)
        self.assertIn("protected_path", reason_codes)

    def test_manual_result_preview_safe_intended_target_previews_only(self) -> None:
        app = FastAPI()
        app.include_router(diff_verification_router)
        client = TestClient(app)
        diff = "\n".join(
            [
                "--- a/docs/phase-8-manual-check.md",
                "+++ b/docs/phase-8-manual-check.md",
                "@@ -1,1 +1,2 @@",
                " # Phase 8 Manual Check",
                "+Phase 4E-2 manual fallback safe diff validation passed.",
                "",
            ]
        )

        response = client.post(
            "/v1/verification/manual-result-preview",
            json={
                "payload": diff,
                "route_type": "local_route",
                "task_spec": {
                    "schema_version": 1,
                    "task_type": "modify_existing_file",
                    "target": "docs/phase-8-manual-check.md",
                    "allowed_files": ["docs/phase-8-manual-check.md"],
                    "forbidden_files": [],
                },
            },
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "preview_ready")
        self.assertEqual(
            payload["task_spec_check"]["changed_files"],
            ["docs/phase-8-manual-check.md"],
        )
        self.assertTrue(payload["task_spec_check"]["ok"])
        self.assertTrue(payload["git_apply_check_ok"])
        self.assertFalse(payload["would_apply_diff"])
        self.assertFalse(payload["would_execute"])

    def test_manual_result_preview_wrong_file_blocks_allowed_files(self) -> None:
        app = FastAPI()
        app.include_router(diff_verification_router)
        client = TestClient(app)
        diff = "\n".join(
            [
                "--- a/source_proxy/api/decision.py",
                "+++ b/source_proxy/api/decision.py",
                "@@ -1,1 +1,2 @@",
                " from __future__ import annotations",
                "+# Phase 4E-2 wrong-file manual fallback should be blocked.",
                "",
            ]
        )

        response = client.post(
            "/v1/verification/manual-result-preview",
            json={
                "payload": diff,
                "route_type": "local_route",
                "task_spec": {
                    "schema_version": 1,
                    "task_type": "modify_existing_file",
                    "target": "docs/phase-8-manual-check.md",
                    "allowed_files": ["docs/phase-8-manual-check.md"],
                    "forbidden_files": [],
                },
            },
        )

        payload = response.json()
        reason_codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("task_spec_allowed_file_violation", reason_codes)
        self.assertFalse(payload["limits"]["file_writes_allowed"])
        self.assertFalse(payload["would_apply_diff"])

    def test_manual_result_preview_blocks_path_traversal(self) -> None:
        app = FastAPI()
        app.include_router(diff_verification_router)
        client = TestClient(app)

        response = client.post(
            "/v1/verification/manual-result-preview",
            json={
                "payload": "\n".join(
                    [
                        "--- a/../outside.txt",
                        "+++ b/../outside.txt",
                        "@@ -0,0 +1 @@",
                        "+hello",
                        "",
                    ]
                ),
                "route_type": "local_route",
            },
        )

        payload = response.json()
        reason_codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("path_escape", reason_codes)
        self.assertIn("outside_workspace", reason_codes)
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
            'Change the text "gap-2" to "gap-1.5"',
            'Replace "gap-2" with "gap-1.5"',
            'Replace the label "gap-2" with "gap-1.5"',
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

    def test_diff_transformations_reject_append_only_and_accept_short_prefix_destinations(
        self,
    ) -> None:
        append_only = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/status.ts b/src/status.ts",
                    "--- a/src/status.ts",
                    "+++ b/src/status.ts",
                    "@@ -1 +1,2 @@",
                    ' const label = "Old";',
                    '+const next = "New";',
                    "",
                ]
            ),
            task_text='Change the text "Old" to "New".',
            route_type="local_route",
        )
        self.assertEqual(append_only["status"], "blocked")
        self.assertIn(
            "missing replaced source text: Old",
            append_only["requirement_coverage"]["missing"],
        )

        cases = (("x", "y"), ("UI", "UX"), ("Old", "Old and New"))
        for source, final in cases:
            with self.subTest(source=source, final=final):
                payload = preview_diff_verification(
                    "\n".join(
                        [
                            "diff --git a/src/status.ts b/src/status.ts",
                            "--- a/src/status.ts",
                            "+++ b/src/status.ts",
                            "@@ -1 +1 @@",
                            f'-const label = "{source}";',
                            f'+const label = "{final}";',
                            "",
                        ]
                    ),
                    task_text=f'Change the text "{source}" to "{final}".',
                    route_type="local_route",
                )

                self.assertEqual(
                    payload["status"],
                    "preview_ready",
                    payload["requirement_coverage"],
                )
                self.assertEqual(
                    payload["requirement_coverage"]["required"]["transformations"],
                    [{"source": source, "final": final}],
                )

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

    def test_replacement_content_does_not_require_quoted_route_references(self) -> None:
        import tempfile
        from pathlib import Path

        task = (
            "make a todo page at `/agent-lab/todo` and link it from `/agent-lab`. "
            "i should be able to add a task, check it off, and delete it."
        )
        content = "\n".join(
            [
                '"use client";',
                "",
                "export default function TodoPage() {",
                "  return (",
                "    <main>",
                "      <h1>Todo</h1>",
                "      <input aria-label=\"Task\" />",
                "      <button>Add task</button>",
                "      <button>Delete</button>",
                "    </main>",
                "  );",
                "}",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_replacement_content(
                workspace_root=Path(tmp),
                target_path="src/app/agent-lab/todo/page.tsx",
                content=content,
                task_text=task,
            )

        self.assertTrue(result["ok"], result)
        self.assertNotIn("missing exact text: /agent-lab/todo", result["missing"])
        self.assertNotIn("missing exact text: /agent-lab", result["missing"])

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

    def test_path_tokens_are_not_exact_literals_but_displayed_filename_is(self) -> None:
        task = "\n".join(
            [
                "Target file: src/status.ts",
                'Read the worker implementation from "src/jobs/worker.py".',
                'Use shared types from "src/types.ts".',
                'Preserve compatibility with "src/legacy.js".',
                'Load JSON settings from "config/source.json".',
                'Load runtime configuration from "config/runtime.yaml".',
                'Read nested configuration from "nested/env/app.toml".',
                'Do not edit ".env".',
                'Load optional settings from ".env.local" and preserve ".gitignore".',
                'Keep behavior compatible with "service.conf" and "settings.ini".',
                'Display the exact filename "worker.py".',
                'Output must contain "worker.py".',
                'Include "config/settings.json" in the rendered output.',
                "Keep the status function callable.",
            ]
        )
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/status.ts b/src/status.ts",
                    "--- a/src/status.ts",
                    "+++ b/src/status.ts",
                    "@@ -1 +1 @@",
                    '-export function status() { return "old"; }',
                    '+export function status() { return "worker.py config/settings.json"; }',
                    "",
                ]
            ),
            task_text=task,
            route_type="local_route",
        )

        self.assertEqual(
            payload["status"],
            "preview_ready",
            payload["requirement_coverage"],
        )
        required_texts = payload["requirement_coverage"]["required"]["texts"]
        self.assertEqual(required_texts, ["worker.py", "config/settings.json"])
        for operational_path in (
            "src/jobs/worker.py",
            "src/types.ts",
            "src/legacy.js",
            "config/source.json",
            "config/runtime.yaml",
            "nested/env/app.toml",
            ".env",
            ".env.local",
            ".gitignore",
            "service.conf",
            "settings.ini",
        ):
            self.assertNotIn(operational_path, required_texts)
        self.assertTrue(payload["requirement_coverage"]["ok"])

    def test_exact_filename_and_path_forms_exclude_bare_artifact_nouns(self) -> None:
        task = "\n".join(
            [
                "Target file: src/status.ts",
                'Display the exact filename "worker.py".',
                'The filename must equal "runner.py".',
                'Show the exact text "config/settings.json".',
                '"nested/report.json" must be displayed.',
                'File "ignored.py" handles background jobs.',
                'Artifact "config/ignored.json" stores settings.',
                'Target "src/ignored.py" imports the worker.',
            ]
        )
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/status.ts b/src/status.ts",
                    "--- a/src/status.ts",
                    "+++ b/src/status.ts",
                    "@@ -1 +1 @@",
                    '-export const status = "old";',
                    '+export const status = "worker.py runner.py config/settings.json nested/report.json";',
                    "",
                ]
            ),
            task_text=task,
            route_type="local_route",
        )

        self.assertEqual(payload["status"], "preview_ready", payload)
        self.assertEqual(
            payload["requirement_coverage"]["required"]["texts"],
            [
                "worker.py",
                "runner.py",
                "config/settings.json",
                "nested/report.json",
            ],
        )

    def test_backend_endpoint_route_is_not_mapped_to_next_app_router(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/backend.py b/src/backend.py",
                    "--- a/src/backend.py",
                    "+++ b/src/backend.py",
                    "@@ -1,2 +1,2 @@",
                    "-def list_items():",
                    "+def list_items(limit=None):",
                    "     return ITEMS",
                    "",
                ]
            ),
            task_text=(
                "Target file: src/backend.py\n"
                "Add an optional limit query parameter to the existing `/items` endpoint."
            ),
            route_type="local_route",
        )

        self.assertEqual(payload["status"], "preview_ready", payload)
        required = payload["requirement_coverage"]["required"]
        self.assertIsNone(required["route"])
        self.assertIsNone(required["route_target"])

    def test_added_source_line_encoded_with_three_pluses_remains_hunk_content(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/counter.ts b/src/counter.ts",
                    "--- a/src/counter.ts",
                    "+++ b/src/counter.ts",
                    "@@ -1 +1,2 @@",
                    " let counter = 0;",
                    "+++ counter;",
                    "",
                ]
            ),
            route_type="local_route",
        )

        self.assertEqual(payload["status"], "preview_ready", payload)
        self.assertEqual(
            [item["path"] for item in payload["changed_files"]],
            ["src/counter.ts"],
        )

    def test_negated_transformation_preserves_source_without_requiring_destination(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/status.ts b/src/status.ts",
                    "--- a/src/status.ts",
                    "+++ b/src/status.ts",
                    "@@ -1 +1,2 @@",
                    "-export const status = 'Stable';",
                    "+export const status = 'Stable';",
                    "+// RequiredLiteral remains part of the public contract.",
                    "",
                ]
            ),
            task_text="\n".join(
                [
                    'Do not change the string "Stable" to "Unwanted".',
                    'Do not remove "RequiredLiteral".',
                ]
            ),
            route_type="local_route",
        )

        self.assertEqual(payload["status"], "preview_ready")
        required = payload["requirement_coverage"]["required"]["texts"]
        self.assertEqual(required, ["Stable", "RequiredLiteral"])
        self.assertNotIn("Unwanted", required)

    def test_requirement_coverage_ignores_pasted_current_file_context(self) -> None:
        task = "\n".join(
            [
                "Target file: src/lib/coding/unified-diff-paths.ts",
                "",
                "Add a short comment above collectPathsFromUnifiedDiff explaining that it supports both git-style diffs and standard unified diffs. Do not change runtime behavior.",
                "",
                "file content:",
                'const lines = diff.replace(/\\r\\n/g, "\\n").split("\\n");',
                'path = path.replace(/^(?:a|b)\\//, "");',
                'if (path === "/dev/null") return "";',
                'Ask: "Return only the JSON, using content_lines."',
            ]
        )
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/lib/coding/unified-diff-paths.ts b/src/lib/coding/unified-diff-paths.ts",
                    "--- a/src/lib/coding/unified-diff-paths.ts",
                    "+++ b/src/lib/coding/unified-diff-paths.ts",
                    "@@ -1,6 +1,9 @@",
                    ' import { normalizeRepoRelativePath } from "@/lib/coding/explicit-task-target";',
                    " ",
                    "-/** Paths touched by a unified diff, de-duplicated, order preserved. */",
                    "+/**",
                    "+ * Paths touched by a unified diff, de-duplicated, order preserved.",
                    "+ * Supports both git-style diffs and standard unified diffs.",
                    "+ */",
                    " export function collectPathsFromUnifiedDiff(diff: string): string[] {",
                    "   const out: string[] = [];",
                    "   const seen = new Set<string>();",
                ]
            ),
            route_type="local_route",
            task_text=task,
        )

        self.assertEqual(payload["status"], "preview_ready", payload["requirement_coverage"])
        self.assertTrue(payload["requirement_coverage"]["ok"])
        self.assertNotIn("content_lines", " ".join(payload["requirement_coverage"].get("missing", [])))

    def test_docs_append_without_target_line_uses_architect_plan_target(self) -> None:
        import tempfile
        from pathlib import Path

        from source_proxy.planning.architect import plan_task_deterministically
        from source_proxy.tasks.long_running import (
            generate_unified_diff_from_content,
            propose_coder_agent_diff_payload_from_plan,
        )

        task = "\n".join(
            [
                "Target file: docs/phase-8-manual-check.md",
                "",
                "Proposal task:",
                "",
                "```json",
                (
                    '{"target_file":"docs/phase-8-manual-check.md",'
                    '"task":"Append Proxy backend layout smoke test passed.",'
                    '"allowed_files":["docs/phase-8-manual-check.md"],'
                    '"forbidden_files":[".env"],'
                    '"expected_checks":["target-only"],'
                    '"mode":"proposal"}'
                ),
                "```",
            ]
        )
        preview_task = (
            "Append Proxy backend layout smoke test passed. "
            "Return only a unified diff. See /coding for unrelated context."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "docs" / "phase-8-manual-check.md"
            doc.parent.mkdir(parents=True)
            doc.write_text("# Manual\n", encoding="utf-8")
            result = plan_task_deterministically(task, "docs-append-route", root)
            self.assertTrue(hasattr(result, "plan"))
            out = propose_coder_agent_diff_payload_from_plan(
                architect_plan=result.plan,
                workspace_root=root,
                llm_call=lambda *_args: (_ for _ in ()).throw(AssertionError("no llm")),
            )
            diff = str(out.get("proposed_diff") or "")
            if not diff.strip():
                content = doc.read_text(encoding="utf-8").rstrip() + "\nProxy backend layout smoke test passed.\n"
                diff = generate_unified_diff_from_content(root, "docs/phase-8-manual-check.md", content)
            payload = preview_diff_verification(
                diff,
                route_type="local_route",
                task_text=preview_task,
                architect_plan=result.plan,
            )

        self.assertEqual(payload["status"], "preview_ready", payload.get("blocked_reasons"))
        self.assertTrue(payload["requirement_coverage"]["ok"], payload["requirement_coverage"])

    def _docs_append_smoke_task(self) -> str:
        return "\n".join(
            [
                "Append this exact sentence to docs/phase-8-manual-check.md:",
                "",
                "Proxy backend layout smoke test passed.",
                "",
                "Do not edit any other file.",
                "Do not modify /coding.",
                "Do not modify /proxy-backend.",
                "Do not modify Source Proxy backend files.",
                "Do not commit.",
                "Do not push.",
            ]
        )

    def _docs_append_diff(self, *, include_literal: bool = True) -> str:
        line = "+Proxy backend layout smoke test passed." if include_literal else "+WRONG SENTENCE"
        return "\n".join(
            [
                "diff --git a/docs/phase-8-manual-check.md b/docs/phase-8-manual-check.md",
                "--- a/docs/phase-8-manual-check.md",
                "+++ b/docs/phase-8-manual-check.md",
                "@@ -1,3 +1,4 @@",
                " # Phase 8 Manual Check",
                line,
            ]
        )

    def test_docs_append_negative_constraints_do_not_require_route_files(self) -> None:
        payload = preview_diff_verification(
            self._docs_append_diff(),
            route_type="local_route",
            task_text=self._docs_append_smoke_task(),
        )
        self.assertEqual(payload["status"], "preview_ready", payload.get("blocked_reasons"))
        self.assertTrue(payload["requirement_coverage"]["ok"], payload["requirement_coverage"])
        self.assertIsNone(payload["requirement_coverage"]["required"].get("route"))

    def test_plan3_set_b_docs_diff_remains_preview_only(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b2-docs-only-patch-20260625.md b/docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b2-docs-only-patch-20260625.md",
                    "new file mode 100644",
                    "index 0000000..1111111",
                    "--- /dev/null",
                    "+++ b/docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b2-docs-only-patch-20260625.md",
                    "@@ -0,0 +1,3 @@",
                    "+# Plan 3 Set B - B2 Docs-Only Patch",
                    "+",
                    "+B3-B10 remain gated behind later Britton approval.",
                ]
            )
        )

        self.assertEqual(payload["status"], "preview_ready", payload.get("blocked_reasons"))
        self.assertEqual(payload["risk"], "low")
        self.assertEqual(
            payload["changed_files"][0]["path"],
            "docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b2-docs-only-patch-20260625.md",
        )
        self.assertFalse(payload["would_apply_diff"])
        self.assertFalse(payload["would_execute"])
        self.assertIn(
            [
                "git",
                "diff",
                "--check",
                "--",
                "docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b2-docs-only-patch-20260625.md",
            ],
            [item["command"] for item in payload["suggested_commands"]],
        )

    def test_plan3_set_b_mdx_docs_diff_gets_diff_check_suggestion(self) -> None:
        path = "docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b9-integration-proof.mdx"
        payload = preview_diff_verification(
            "\n".join(
                [
                    f"diff --git a/{path} b/{path}",
                    "new file mode 100644",
                    "index 0000000..1111111",
                    "--- /dev/null",
                    f"+++ b/{path}",
                    "@@ -0,0 +1,3 @@",
                    "+# Plan 3 Set B - B9 Integration Proof",
                    "+",
                    "+MDX docs diffs get the same focused docs sanity check.",
                ]
            )
        )

        self.assertEqual(payload["status"], "preview_ready", payload.get("blocked_reasons"))
        self.assertEqual(payload["risk"], "low")
        self.assertIn(
            ["git", "diff", "--check", "--", path],
            [item["command"] for item in payload["suggested_commands"]],
        )

    def test_plan3_set_c_safe_docs_diff_gets_mixed_workflow_audit(self) -> None:
        path = "docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-c-evidence-20260625/c4-proof.md"
        payload = preview_diff_verification(
            "\n".join(
                [
                    f"diff --git a/{path} b/{path}",
                    "new file mode 100644",
                    "index 0000000..1111111",
                    "--- /dev/null",
                    f"+++ b/{path}",
                    "@@ -0,0 +1,3 @@",
                    "+# Plan 3 Set C - C4 Proof",
                    "+",
                    "+Backend verifier preview metadata is not implementation readiness.",
                ]
            )
        )

        audit = payload["mixed_workflow_audit"]
        self.assertEqual(payload["status"], "preview_ready", payload.get("blocked_reasons"))
        self.assertFalse(audit["research_proves_implementation"])
        self.assertTrue(audit["requires_focused_verification"])
        self.assertFalse(audit["browser_proof_required"])
        self.assertFalse(audit["lane_laundering_allowed"])
        self.assertFalse(audit["plan4_allowed"])
        self.assertFalse(audit["daily_driver_readiness_claimed"])
        self.assertFalse(audit["preview_is_implementation_readiness"])
        self.assertTrue(any("read-only metadata" in note for note in audit["notes"]))

    def test_plan3_set_c_blocked_secret_diff_keeps_audit_limited(self) -> None:
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

        audit = payload["mixed_workflow_audit"]
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["limits"]["file_writes_allowed"])
        self.assertFalse(audit["research_proves_implementation"])
        self.assertTrue(audit["requires_focused_verification"])
        self.assertFalse(audit["lane_laundering_allowed"])
        self.assertFalse(audit["plan4_allowed"])
        self.assertFalse(audit["daily_driver_readiness_claimed"])
        self.assertFalse(audit["preview_is_implementation_readiness"])
        self.assertTrue(any("Blocked preview lanes remain blocked" in note for note in audit["notes"]))

    def test_docs_append_fails_when_exact_sentence_missing(self) -> None:
        payload = preview_diff_verification(
            self._docs_append_diff(include_literal=False),
            route_type="local_route",
            task_text=self._docs_append_smoke_task(),
        )
        self.assertEqual(payload["status"], "blocked")
        codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertIn("requirement_coverage_failed", codes)
        missing = " ".join(payload["requirement_coverage"].get("missing", []))
        self.assertIn("Proxy backend layout smoke test passed.", missing)

    def test_docs_append_fails_when_coding_page_changes(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/app/coding/page.tsx b/src/app/coding/page.tsx",
                    "--- a/src/app/coding/page.tsx",
                    "+++ b/src/app/coding/page.tsx",
                    "@@ -1,3 +1,4 @@",
                    "+export const hacked = true;",
                ]
            ),
            route_type="local_route",
            task_text=self._docs_append_smoke_task(),
        )
        self.assertEqual(payload["status"], "blocked")
        codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertTrue(
            "requirement_coverage_failed" in codes
            or "task_spec_allowed_file_violation" in codes
            or "protected_path" in codes
            or len(codes) > 0,
        )

    def test_docs_append_fails_when_proxy_backend_page_changes(self) -> None:
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/src/app/proxy-backend/page.tsx b/src/app/proxy-backend/page.tsx",
                    "--- a/src/app/proxy-backend/page.tsx",
                    "+++ b/src/app/proxy-backend/page.tsx",
                    "@@ -1,3 +1,4 @@",
                    "+export const hacked = true;",
                ]
            ),
            route_type="local_route",
            task_text=self._docs_append_smoke_task(),
        )
        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(payload["blocked_reasons"])

    def test_route_coverage_still_applies_for_explicit_route_target(self) -> None:
        task = "\n".join(
            [
                "Target file: src/app/proxy-backend/page.tsx",
                "Create the proxy backend page at route /proxy-backend.",
                'Include <h1 className="text-2xl">Proxy Backend</h1>',
            ]
        )
        payload = preview_diff_verification(
            "\n".join(
                [
                    "diff --git a/notes/manual.md b/notes/manual.md",
                    "new file mode 100644",
                    "index 0000000..1111111",
                    "--- /dev/null",
                    "+++ b/notes/manual.md",
                    "@@ -0,0 +1,2 @@",
                    "+wrong file",
                    "+",
                ]
            ),
            route_type="local_route",
            task_text=task,
        )
        self.assertEqual(payload["status"], "blocked")
        codes = {item["reason_code"] for item in payload["blocked_reasons"]}
        self.assertIn("requirement_coverage_failed", codes)

    def test_forbidden_files_in_proposal_json_are_not_required_literals(self) -> None:
        import json

        from source_proxy.decision.proposal_task import effective_planning_task_text

        task = "\n".join(
            [
                "Target file: docs/phase-8-manual-check.md",
                "",
                "Proposal task:",
                "",
                "```json",
                json.dumps(
                    {
                        "allowed_files": ["docs/phase-8-manual-check.md"],
                        "forbidden_files": [".env", "src/app/coding/**", "src/app/proxy-backend/**"],
                        "expected_checks": ["target-only"],
                        "mode": "proposal",
                        "target_file": "docs/phase-8-manual-check.md",
                        "task": self._docs_append_smoke_task(),
                    },
                    indent=2,
                ),
                "```",
            ]
        )
        effective = effective_planning_task_text(task)
        self.assertNotIn("allowed_files", effective)
        payload = preview_diff_verification(
            self._docs_append_diff(),
            route_type="local_route",
            task_text=effective,
        )
        self.assertTrue(payload["requirement_coverage"]["ok"], payload["requirement_coverage"])
        missing = " ".join(payload["requirement_coverage"].get("missing", []))
        self.assertNotIn("allowed_files", missing)
        self.assertNotIn("forbidden_files", missing)

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
