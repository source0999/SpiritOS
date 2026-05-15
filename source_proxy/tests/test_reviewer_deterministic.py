from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.diff_verification import router as diff_verification_router
from source_proxy.planning.plan import (
    PLAN_SCHEMA_VERSION,
    AcceptanceCriterion,
    ArchitectPlan,
    BundleSnapshot,
    CoderPacket,
    ContentConstraints,
    ContextSlice,
    PlanBudget,
    TargetFile,
    TaskClassification,
    VerificationPlan,
    save_plan,
)
from source_proxy.planning.reviewer import (
    _materialize_target_content,
    _patch_for_path,
    review_diff_deterministically,
    review_diff_with_llm,
)
from source_proxy.tasks.long_running import create_long_running_task, reset_long_running_tasks
from source_proxy.verification.diff import preview_diff_verification


def _plan(
    *,
    task_id: str = "task-review",
    target_path: str = "src/example.tsx",
    target_content: str | None = None,
    constraints: ContentConstraints | None = None,
    criteria: list[AcceptanceCriterion] | None = None,
    style_directives: list[str] | None = None,
) -> ArchitectPlan:
    content = target_content or (
        'import React from "react";\n'
        "export default function Page() {\n"
        "  return <main>Old</main>;\n"
        "}\n"
    )
    return ArchitectPlan(
        plan_id="plan-review",
        task_id=task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at="2026-05-14T00:00:00Z",
        source_task="Target file: src/example.tsx\nReview constraints.",
        bundle_snapshot=BundleSnapshot(
            bundle_path="/tmp/repomix-output.ast.xml",
            bundle_sha256="0" * 64,
            workspace_root="/tmp",
            generated_at="2026-05-14T00:00:00Z",
        ),
        classification=TaskClassification(
            task_class="implement",
            visual_change=False,
            designer_required=False,
            estimated_complexity="trivial",
        ),
        coder_packet=CoderPacket(
            target_file=TargetFile(target_path, True, "a" * 64),
            operation="edit",
            acceptance_criteria=criteria or [],
            constraints=constraints
            or ContentConstraints([], [], [], [], None, None),
            context_slices=[
                ContextSlice(
                    path=target_path,
                    kind="target",
                    sha256="a" * 64,
                    content=content,
                    line_range=(1, 4),
                )
            ],
            forbidden_paths=[],
            style_directives=style_directives or [],
        ),
        verification_plan=VerificationPlan(
            required_checks=[],
            designer_review_required=False,
            architect_review_required=False,
        ),
        budget=PlanBudget(3, 120, True),
    )


def _diff(new_body: str) -> str:
    return "\n".join(
        [
            "diff --git a/src/example.tsx b/src/example.tsx",
            "--- a/src/example.tsx",
            "+++ b/src/example.tsx",
            "@@ -1,4 +1,4 @@",
            '-import React from "react";',
            "-export default function Page() {",
            "-  return <main>Old</main>;",
            "-}",
            *new_body.splitlines(),
            "",
        ]
    )


class DeterministicReviewerTests(unittest.TestCase):
    def test_standard_unified_diff_materializes_target_content(self) -> None:
        literal = "Frontend coding proxy smoke test after diff path patch."
        plan = _plan(
            target_path="docs/phase-8-manual-check.md",
            target_content=(
                "# Phase 8 Manual Check\n\n"
                "Approved diffs should require post-apply verification before completion.\n"
            ),
        )
        diff = "\n".join(
            [
                "--- a/docs/phase-8-manual-check.md",
                "+++ b/docs/phase-8-manual-check.md",
                "@@ -1,3 +1,4 @@",
                " # Phase 8 Manual Check",
                " ",
                " Approved diffs should require post-apply verification before completion.",
                f"+{literal}",
                "",
            ]
        )

        self.assertTrue(_patch_for_path(diff, "docs/phase-8-manual-check.md"))
        self.assertIn(literal, _materialize_target_content(plan, diff))

    def test_git_style_diff_materializes_target_content(self) -> None:
        plan = _plan()

        self.assertIn(
            "<main>New</main>",
            _materialize_target_content(
                plan,
                _diff("+export default function Page() {\n+  return <main>New</main>;\n+}"),
            ),
        )

    def test_wrong_target_diff_does_not_satisfy_target(self) -> None:
        plan = _plan(
            constraints=ContentConstraints(["RequiredLiteral"], [], [], [], None, None)
        )
        diff = "\n".join(
            [
                "--- a/src/other.tsx",
                "+++ b/src/other.tsx",
                "@@ -1 +1 @@",
                "-old",
                "+RequiredLiteral",
                "",
            ]
        )

        report = review_diff_deterministically(plan, diff)

        self.assertFalse(_patch_for_path(diff, "src/example.tsx"))
        self.assertFalse(report.passed)
        self.assertEqual(report.findings[0].id, "missing_must_contain")

    def test_standard_unified_diff_satisfies_must_contain(self) -> None:
        literal = "Frontend coding proxy smoke test after diff path patch."
        plan = _plan(
            target_path="docs/phase-8-manual-check.md",
            target_content=(
                "# Phase 8 Manual Check\n\n"
                "Approved diffs should require post-apply verification before completion.\n"
            ),
            constraints=ContentConstraints([literal], [], [], [], None, None),
        )
        diff = "\n".join(
            [
                "--- a/docs/phase-8-manual-check.md",
                "+++ b/docs/phase-8-manual-check.md",
                "@@ -1,3 +1,4 @@",
                " # Phase 8 Manual Check",
                " ",
                " Approved diffs should require post-apply verification before completion.",
                f"+{literal}",
                "",
            ]
        )

        report = review_diff_deterministically(plan, diff)

        self.assertTrue(report.passed)

    def test_quoted_literal_acceptance_passes_when_literal_is_present(self) -> None:
        plan = _plan(
            criteria=[
                AcceptanceCriterion(
                    "literal-smoke",
                    'Output must contain "Frontend coding proxy smoke test after diff path patch.".',
                    "literal",
                )
            ],
        )

        report = review_diff_deterministically(
            plan,
            _diff(
                "+export default function Page() {\n"
                '+  return <main>Frontend coding proxy smoke test after diff path patch.</main>;\n'
                "+}"
            ),
        )

        self.assertTrue(report.passed)

    def test_quoted_literal_acceptance_fails_when_literal_is_missing(self) -> None:
        plan = _plan(
            criteria=[
                AcceptanceCriterion(
                    "literal-smoke",
                    "Output must contain 'Frontend coding proxy smoke test after diff path patch.'.",
                    "literal",
                )
            ],
        )

        report = review_diff_deterministically(
            plan,
            _diff("+export default function Page() {\n+  return <main>New</main>;\n+}"),
        )

        self.assertFalse(report.passed)
        self.assertEqual(report.findings[0].id, "literal_acceptance_missing")

    def test_class_fragment_literal_acceptance_checks_fragment_only(self) -> None:
        plan = _plan(
            criteria=[
                AcceptanceCriterion(
                    "class-fragment-1",
                    "Output must contain class fragment collectPathsFromUnifiedDiff.",
                    "literal",
                )
            ],
        )

        report = review_diff_deterministically(
            plan,
            _diff(
                "+export default function Page() {\n"
                "+  collectPathsFromUnifiedDiff(DOCS_APPEND_UNIFIED_DIFF_WITH_SPACES);\n"
                "+  return <main>New</main>;\n"
                "+}"
            ),
        )

        self.assertTrue(report.passed)

    def test_multi_hunk_ts_diff_materializes_patched_content_for_literals(self) -> None:
        target_content = (
            'import { collectPathsFromUnifiedDiff } from "@/lib/coding/unified-diff-paths";\n\n'
            "const FIRST = 'old';\n"
            "const SECOND = 'old';\n"
        )
        plan = _plan(
            target_path="src/lib/coding/__tests__/unified-diff-paths.test.ts",
            target_content=target_content,
            constraints=ContentConstraints(
                ["collectPathsFromUnifiedDiff"],
                [],
                ["@/lib/coding/unified-diff-paths"],
                [],
                None,
                None,
            ),
            criteria=[
                AcceptanceCriterion(
                    "class-fragment-1",
                    "Output must contain class fragment collectPathsFromUnifiedDiff.",
                    "literal",
                )
            ],
        )
        diff = "\n".join(
            [
                "--- a/src/lib/coding/__tests__/unified-diff-paths.test.ts",
                "+++ b/src/lib/coding/__tests__/unified-diff-paths.test.ts",
                "@@ -1,3 +1,3 @@",
                ' import { collectPathsFromUnifiedDiff } from "@/lib/coding/unified-diff-paths";',
                " ",
                "-const FIRST = 'old';",
                "+const FIRST = 'docs/file with spaces.md';",
                "@@ -4 +4,4 @@",
                "-const SECOND = 'old';",
                "+const SECOND = collectPathsFromUnifiedDiff(DOCS_APPEND_UNIFIED_DIFF_WITH_SPACES);",
                "+expect(SECOND).toEqual(['docs/file with spaces.md']);",
                "+expect(SECOND[0].endsWith('spaces.md')).toBe(true);",
                "",
            ]
        )

        materialized = _materialize_target_content(plan, diff)
        report = review_diff_deterministically(plan, diff)

        self.assertIn("collectPathsFromUnifiedDiff(DOCS_APPEND_UNIFIED_DIFF_WITH_SPACES)", materialized)
        self.assertIn("docs/file with spaces.md", materialized)
        self.assertTrue(report.passed)

    def test_unchanged_existing_import_is_not_reported_as_imports_violated(self) -> None:
        plan = _plan(
            target_content=(
                'import { collectPathsFromUnifiedDiff } from "@/lib/coding/unified-diff-paths";\n\n'
                "export default function Page() {\n"
                "  return <main>Old</main>;\n"
                "}\n"
            ),
            constraints=ContentConstraints(
                [],
                [],
                ["@/lib/coding/unified-diff-paths"],
                [],
                None,
                None,
            ),
        )
        diff = "\n".join(
            [
                "--- a/src/example.tsx",
                "+++ b/src/example.tsx",
                "@@ -3 +3 @@",
                "-  return <main>Old</main>;",
                "+  return <main>New</main>;",
                "",
            ]
        )

        report = review_diff_deterministically(plan, diff)

        self.assertTrue(report.passed)

    def test_modified_existing_import_still_blocks_when_preserve_import_policy_requires(self) -> None:
        plan = _plan(
            target_content=(
                'import { collectPathsFromUnifiedDiff } from "@/lib/coding/unified-diff-paths";\n\n'
                "export default function Page() {\n"
                "  return <main>Old</main>;\n"
                "}\n"
            ),
            constraints=ContentConstraints(
                [],
                [],
                ["@/lib/coding/unified-diff-paths"],
                [],
                None,
                None,
            ),
        )
        diff = "\n".join(
            [
                "--- a/src/example.tsx",
                "+++ b/src/example.tsx",
                "@@ -1 +1 @@",
                '-import { collectPathsFromUnifiedDiff } from "@/lib/coding/unified-diff-paths";',
                '+import { collectPathsFromUnifiedDiff } from "@/lib/coding/other";',
                "",
            ]
        )

        report = review_diff_deterministically(plan, diff)

        self.assertFalse(report.passed)
        self.assertEqual(report.findings[0].id, "imports_violated")

    def test_missing_must_contain_blocks_review(self) -> None:
        plan = _plan(
            constraints=ContentConstraints(["GlassPanel"], [], [], [], None, None)
        )
        report = review_diff_deterministically(
            plan,
            _diff("+export default function Page() {\n+  return <main>New</main>;\n+}"),
        )

        self.assertFalse(report.passed)
        self.assertEqual(report.findings[0].id, "missing_must_contain")
        self.assertEqual(report.findings[0].details, "GlassPanel")

    def test_removed_default_export_blocks_review(self) -> None:
        plan = _plan(
            constraints=ContentConstraints([], [], [], ["default"], None, None)
        )
        report = review_diff_deterministically(
            plan,
            _diff('+export function Page() {\n+  return <main>New</main>;\n+}'),
        )

        self.assertFalse(report.passed)
        self.assertEqual(report.findings[0].id, "exports_violated")
        self.assertEqual(report.findings[0].details, "default")

    def test_preview_blocks_when_architect_reviewer_fails(self) -> None:
        plan = _plan(
            constraints=ContentConstraints(["GlassPanel"], [], [], [], None, None)
        )
        with mock.patch(
            "source_proxy.tasks.long_running.git_apply_check_for_preview",
            return_value=(True, ""),
        ):
            payload = preview_diff_verification(
                _diff("+export default function Page() {\n+  return <main>New</main>;\n+}"),
                architect_plan=plan,
                route_type="local_route",
            )

        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["limits"]["file_writes_allowed"])
        self.assertFalse(payload["review_report"]["passed"])
        self.assertIn(
            "review_missing_must_contain",
            {reason["reason_code"] for reason in payload["blocked_reasons"]},
        )

    def test_llm_reviewer_flags_style_directive_advisory(self) -> None:
        plan = _plan(
            style_directives=["use Tailwind utility classes, no inline styles"]
        )

        def fake_llm(prompt: str, alias: str) -> str:
            self.assertEqual(alias, "local")
            self.assertIn("no inline styles", prompt)
            return (
                '{"passed": false, "findings": ['
                '{"id": "style_directive_violation", '
                '"details": "Inline style object remains in the JSX.", '
                '"path": "src/example.tsx"}]}'
            )

        report = review_diff_with_llm(
            plan,
            _diff(
                '+export default function Page() {\n'
                '+  return <main style={{ color: "red" }}>New</main>;\n'
                "+}"
            ),
            llm_call=fake_llm,
        )

        self.assertFalse(report.passed)
        self.assertEqual(report.findings[0].id, "style_directive_violation")

    def test_preview_surfaces_llm_reviewer_as_advisory_not_blocking(self) -> None:
        plan = _plan(
            style_directives=["use Tailwind utility classes, no inline styles"]
        )

        def fake_llm(_prompt: str, _alias: str) -> str:
            return (
                '{"passed": false, "findings": ['
                '{"id": "style_directive_violation", '
                '"details": "Inline style object remains in the JSX.", '
                '"path": "src/example.tsx"}]}'
            )

        with mock.patch(
            "source_proxy.tasks.long_running.git_apply_check_for_preview",
            return_value=(True, ""),
        ):
            payload = preview_diff_verification(
                _diff(
                    '+export default function Page() {\n'
                    '+  return <main style={{ color: "red" }}>New</main>;\n'
                    "+}"
                ),
                architect_plan=plan,
                route_type="local_route",
                reviewer_llm_call=fake_llm,
            )

        self.assertEqual(payload["status"], "preview_ready")
        self.assertTrue(payload["limits"]["file_writes_allowed"])
        self.assertFalse(payload["llm_review_report"]["passed"])
        self.assertEqual(
            payload["llm_review_report"]["findings"][0]["id"],
            "style_directive_violation",
        )
        self.assertNotIn(
            "review_style_directive_violation",
            {reason["reason_code"] for reason in payload["blocked_reasons"]},
        )

    def test_diff_preview_endpoint_loads_active_task_plan(self) -> None:
        previous_database_path = os.environ.get("SOURCE_PROXY_LONG_RUNNING_TASKS_DB")
        try:
            with tempfile.TemporaryDirectory() as tempdir:
                os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = os.path.join(
                    tempdir,
                    "tasks.sqlite3",
                )
                reset_long_running_tasks()
                created = create_long_running_task("Reviewer endpoint test")
                task_id = created["task"]["id"]
                save_plan(
                    task_id,
                    _plan(
                        task_id=task_id,
                        constraints=ContentConstraints(
                            ["GlassPanel"], [], [], [], None, None
                        ),
                    ),
                )
                app = FastAPI()
                app.include_router(diff_verification_router)
                client = TestClient(app)

                with mock.patch(
                    "source_proxy.tasks.long_running.git_apply_check_for_preview",
                    return_value=(True, ""),
                ):
                    response = client.post(
                        "/v1/verification/diff-preview",
                        json={
                            "active_task_id": task_id,
                            "route_type": "local_route",
                            "unified_diff": _diff(
                                "+export default function Page() {\n+  return <main>New</main>;\n+}"
                            ),
                        },
                    )

                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["status"], "blocked")
                self.assertEqual(
                    payload["review_report"]["findings"][0]["id"],
                    "missing_must_contain",
                )
                reset_long_running_tasks()
        finally:
            if previous_database_path is None:
                os.environ.pop("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", None)
            else:
                os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = previous_database_path
