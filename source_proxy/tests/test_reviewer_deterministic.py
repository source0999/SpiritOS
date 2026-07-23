from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
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
    plan_id: str = "plan-review",
    task_id: str = "task-review",
    target_path: str = "src/example.tsx",
    target_content: str | None = None,
    source_task: str | None = None,
    secondary_slices: list[ContextSlice] | None = None,
    constraints: ContentConstraints | None = None,
    criteria: list[AcceptanceCriterion] | None = None,
    style_directives: list[str] | None = None,
) -> ArchitectPlan:
    content = target_content if target_content is not None else (
        'import React from "react";\n'
        "export default function Page() {\n"
        "  return <main>Old</main>;\n"
        "}\n"
    )
    return ArchitectPlan(
        plan_id=plan_id,
        task_id=task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at="2026-05-14T00:00:00Z",
        source_task=source_task
        or f"Target file: {target_path}\nReview constraints.",
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
                ),
                *(secondary_slices or []),
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


def _replacement_diff(path: str, old: str, new: str) -> str:
    old_lines = old.rstrip("\n").splitlines() if old else []
    new_lines = new.rstrip("\n").splitlines() if new else []
    old_start = 1 if old_lines else 0
    new_start = 1 if new_lines else 0
    old_path = f"a/{path}" if old_lines else "/dev/null"
    new_path = f"b/{path}" if new_lines else "/dev/null"
    return "\n".join(
        [
            f"diff --git a/{path} b/{path}",
            f"--- {old_path}",
            f"+++ {new_path}",
            f"@@ -{old_start},{len(old_lines)} +{new_start},{len(new_lines)} @@",
            *[f"-{line}" for line in old_lines],
            *[f"+{line}" for line in new_lines],
            "",
        ]
    )


def _join_diffs(*diffs: str) -> str:
    return "".join(value if value.endswith("\n") else value + "\n" for value in diffs)


def _content_after_real_git_apply(
    path: str,
    baseline: str | None,
    diff: str,
) -> str:
    """Return Git's exact post-apply bytes for comparison with review evidence."""

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / path
        if baseline is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(baseline.encode("utf-8"))
        completed = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", "-"],
            cwd=root,
            input=diff.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
        return target.read_bytes().decode("utf-8") if target.exists() else ""


class DeterministicReviewerTests(unittest.TestCase):
    def test_materialization_exactly_matches_git_for_file_lifecycle_and_newlines(
        self,
    ) -> None:
        path = "src/example.tsx"
        cases = {
            "create": (
                None,
                "\n".join(
                    [
                        f"diff --git a/{path} b/{path}",
                        "new file mode 100644",
                        "--- /dev/null",
                        f"+++ b/{path}",
                        "@@ -0,0 +1,2 @@",
                        "+alpha",
                        "+beta",
                        "",
                    ]
                ),
                "alpha\nbeta\n",
            ),
            "edit": (
                "alpha\nbeta\n",
                "\n".join(
                    [
                        f"diff --git a/{path} b/{path}",
                        f"--- a/{path}",
                        f"+++ b/{path}",
                        "@@ -1,2 +1,3 @@",
                        " alpha",
                        "+middle",
                        " beta",
                        "",
                    ]
                ),
                "alpha\nmiddle\nbeta\n",
            ),
            "delete": (
                "alpha\nbeta\n",
                "\n".join(
                    [
                        f"diff --git a/{path} b/{path}",
                        "deleted file mode 100644",
                        f"--- a/{path}",
                        "+++ /dev/null",
                        "@@ -1,2 +0,0 @@",
                        "-alpha",
                        "-beta",
                        "",
                    ]
                ),
                "",
            ),
            "no-newline-marker": (
                "old",
                "\n".join(
                    [
                        f"diff --git a/{path} b/{path}",
                        f"--- a/{path}",
                        f"+++ b/{path}",
                        "@@ -1 +1 @@",
                        "-old",
                        r"\ No newline at end of file",
                        "+new",
                        r"\ No newline at end of file",
                        "",
                    ]
                ),
                "new",
            ),
        }

        for label, (baseline, diff, expected) in cases.items():
            with self.subTest(label=label):
                plan = _plan(target_content=baseline or "")
                materialized = _materialize_target_content(plan, diff)
                git_applied = _content_after_real_git_apply(path, baseline, diff)

                self.assertEqual(git_applied, expected)
                self.assertEqual(materialized, git_applied)

    def test_added_source_line_starting_with_two_pluses_is_not_a_file_header(
        self,
    ) -> None:
        target_content = "let counter = 0;\n"
        diff = "\n".join(
            [
                "diff --git a/src/example.tsx b/src/example.tsx",
                "--- a/src/example.tsx",
                "+++ b/src/example.tsx",
                "@@ -1 +1,2 @@",
                " let counter = 0;",
                "+++ counter;",
                "",
            ]
        )
        plan = _plan(target_content=target_content)

        self.assertEqual(
            _materialize_target_content(plan, diff),
            "let counter = 0;\n++ counter;\n",
        )
        self.assertIn("+++ counter;", _patch_for_path(diff, "src/example.tsx"))
        self.assertTrue(review_diff_deterministically(plan, diff).passed)

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
        self.assertEqual(
            report.findings[0].id,
            "must_contain_misplaced_wrong_production",
        )
        self.assertEqual(report.findings[0].path, "src/other.tsx")

    def test_literal_in_test_doc_decoy_or_generated_evidence_does_not_satisfy_target(
        self,
    ) -> None:
        plan = _plan(
            constraints=ContentConstraints(
                ["RequiredLiteral"], [], [], [], None, None
            )
        )
        cases = {
            "test": "tests/test_example.tsx",
            "documentation": "docs/requirements.md",
            "decoy": "src/example.tsx.decoy",
            "generated_evidence": "docs/evidence/run-output.txt",
        }

        for label, path in cases.items():
            with self.subTest(label=label, path=path):
                report = review_diff_deterministically(
                    plan,
                    _replacement_diff(path, "old\n", "RequiredLiteral\n"),
                    task_id="task-review",
                    attempt_id=f"attempt-{label}",
                )

                self.assertFalse(report.passed)
                self.assertEqual(
                    report.findings[0].id,
                    f"must_contain_misplaced_{label}",
                )
                self.assertEqual(report.findings[0].path, path)
                requirement = next(
                    item
                    for item in report.evidence
                    if item.requirement_id == "constraint.must_contain.0"
                )
                self.assertEqual(requirement.intended_paths, ["src/example.tsx"])
                self.assertEqual(requirement.inspected_path, "src/example.tsx")
                self.assertFalse(requirement.satisfied)

    def test_unchanged_baseline_literal_does_not_satisfy_add_requirement(self) -> None:
        target_content = "RequiredLiteral\nOld\n"
        plan = _plan(
            target_content=target_content,
            criteria=[
                AcceptanceCriterion(
                    "add-required",
                    'Add "RequiredLiteral" to the target file.',
                    "literal",
                )
            ],
        )

        report = review_diff_deterministically(
            plan,
            _replacement_diff(
                "src/example.tsx",
                target_content,
                "RequiredLiteral\nNew\n",
            ),
            task_id="task-review",
            attempt_id="attempt-baseline",
        )

        self.assertFalse(report.passed)
        self.assertEqual(
            report.findings[0].id,
            "literal_acceptance_not_introduced",
        )
        evidence = next(item for item in report.evidence if item.requirement_id == "add-required")
        self.assertEqual(evidence.baseline_match_count, 1)
        self.assertEqual(evidence.applied_match_count, 1)
        self.assertFalse(evidence.introduced)

    def test_requirement_fragments_cannot_be_combined_across_files(self) -> None:
        plan = _plan(
            constraints=ContentConstraints(
                ["Alpha\nBeta"], [], [], [], None, None
            )
        )
        diff = _join_diffs(
            _replacement_diff("src/alpha.ts", "old\n", "Alpha\n"),
            _replacement_diff("src/beta.ts", "old\n", "Beta\n"),
        )

        report = review_diff_deterministically(plan, diff)

        self.assertFalse(report.passed)
        self.assertEqual(report.findings[0].id, "missing_must_contain")

    def test_same_basename_in_different_directory_does_not_satisfy_target(self) -> None:
        plan = _plan(
            constraints=ContentConstraints(
                ["RequiredLiteral"], [], [], [], None, None
            )
        )

        report = review_diff_deterministically(
            plan,
            _replacement_diff(
                "other/example.tsx",
                "old\n",
                "RequiredLiteral\n",
            ),
        )

        self.assertFalse(report.passed)
        self.assertEqual(report.findings[0].path, "other/example.tsx")
        self.assertEqual(
            report.findings[0].id,
            "must_contain_misplaced_wrong_production",
        )

    def test_review_evidence_is_bound_to_current_task_and_attempt(self) -> None:
        plan = _plan(
            constraints=ContentConstraints(
                ["RequiredLiteral"], [], [], [], None, None
            )
        )
        diff = _replacement_diff(
            "src/example.tsx",
            plan.coder_packet.context_slices[0].content,
            "RequiredLiteral\n",
        )

        first = review_diff_deterministically(
            plan,
            diff,
            task_id="task-review",
            attempt_id="attempt-one",
        )
        second = review_diff_deterministically(
            plan,
            diff,
            task_id="task-review",
            attempt_id="attempt-two",
        )
        foreign_task = review_diff_deterministically(
            plan,
            diff,
            task_id="task-other",
            attempt_id="attempt-one",
        )

        self.assertTrue(first.passed)
        self.assertTrue(second.passed)
        self.assertNotEqual(first.to_dict(), second.to_dict())
        self.assertEqual(
            {item.attempt_id for item in first.evidence},
            {"attempt-one"},
        )
        self.assertFalse(foreign_task.passed)
        self.assertEqual(
            foreign_task.findings[0].id,
            "review_task_binding_mismatch",
        )

    def test_deleted_target_cannot_be_satisfied_by_surviving_other_file(self) -> None:
        target_content = "Old target\n"
        plan = _plan(
            target_content=target_content,
            constraints=ContentConstraints(
                ["RequiredLiteral"], [], [], [], None, None
            ),
        )
        diff = _join_diffs(
            _replacement_diff("src/example.tsx", target_content, ""),
            _replacement_diff("src/other.tsx", "old\n", "RequiredLiteral\n"),
        )

        report = review_diff_deterministically(plan, diff)

        self.assertFalse(report.passed)
        self.assertEqual(
            report.findings[0].id,
            "must_contain_misplaced_wrong_production",
        )
        self.assertEqual(report.findings[0].path, "src/other.tsx")

    def test_exact_authorized_secondary_file_can_satisfy_named_requirement(self) -> None:
        target_content = "Primary old\n"
        secondary_content = "Secondary old\n"
        plan = _plan(
            target_content=target_content,
            secondary_slices=[
                ContextSlice(
                    path="src/secondary.ts",
                    kind="sibling",
                    sha256="b" * 64,
                    content=secondary_content,
                    line_range=(1, 1),
                )
            ],
            criteria=[
                AcceptanceCriterion(
                    "secondary-literal",
                    'File "src/secondary.ts" must contain "SecondaryLiteral".',
                    "literal",
                )
            ],
        )
        diff = _join_diffs(
            _replacement_diff("src/example.tsx", target_content, "Primary new\n"),
            _replacement_diff(
                "src/secondary.ts",
                secondary_content,
                "SecondaryLiteral\n",
            ),
        )

        report = review_diff_deterministically(
            plan,
            diff,
            task_spec={
                "allowed_files": ["src/example.tsx", "src/secondary.ts"]
            },
            task_id="task-review",
            attempt_id="attempt-secondary",
        )

        self.assertTrue(report.passed)
        evidence = next(
            item
            for item in report.evidence
            if item.requirement_id == "secondary-literal"
        )
        self.assertEqual(evidence.intended_paths, ["src/secondary.ts"])
        self.assertEqual(evidence.inspected_path, "src/secondary.ts")
        self.assertEqual(evidence.task_id, "task-review")
        self.assertEqual(evidence.attempt_id, "attempt-secondary")
        self.assertEqual(len(evidence.baseline_sha256), 64)
        self.assertEqual(len(evidence.applied_sha256), 64)
        self.assertEqual(len(evidence.diff_hunk_sha256), 64)
        self.assertGreater(evidence.diff_hunk_line_count, 0)
        self.assertTrue(evidence.satisfied)

    def test_glob_scope_does_not_authorize_secondary_literal_evidence(self) -> None:
        plan = _plan(
            criteria=[
                AcceptanceCriterion(
                    "secondary-literal",
                    'File "src/secondary.ts" must contain "SecondaryLiteral".',
                    "literal",
                )
            ],
        )

        report = review_diff_deterministically(
            plan,
            _replacement_diff("src/secondary.ts", "old\n", "SecondaryLiteral\n"),
            task_spec={"allowed_files": ["src/**"]},
        )

        self.assertFalse(report.passed)
        self.assertEqual(
            report.findings[0].id,
            "literal_acceptance_path_unauthorized",
        )
        self.assertEqual(report.findings[0].path, "src/secondary.ts")

    def test_backtick_literals_bind_to_target_and_exact_secondary_artifacts(self) -> None:
        target_content = "Primary old\n"
        secondary_content = "Secondary old\n"
        plan = _plan(
            target_content=target_content,
            secondary_slices=[
                ContextSlice(
                    path="src/secondary.ts",
                    kind="sibling",
                    sha256="b" * 64,
                    content=secondary_content,
                    line_range=(1, 1),
                )
            ],
            criteria=[
                AcceptanceCriterion(
                    "backtick-primary",
                    "File `src/example.tsx` must contain `PrimaryLiteral`.",
                    "literal",
                ),
                AcceptanceCriterion(
                    "backtick-secondary",
                    "File `src/secondary.ts` must contain `SecondaryLiteral`.",
                    "literal",
                ),
            ],
        )
        diff = _join_diffs(
            _replacement_diff(
                "src/example.tsx",
                target_content,
                "PrimaryLiteral\n",
            ),
            _replacement_diff(
                "src/secondary.ts",
                secondary_content,
                "SecondaryLiteral\n",
            ),
        )

        report = review_diff_deterministically(
            plan,
            diff,
            task_spec={
                "allowed_files": ["src/example.tsx", "src/secondary.ts"]
            },
        )

        self.assertTrue(report.passed)
        by_requirement = {
            item.requirement_id: (item.intended_paths, item.inspected_path)
            for item in report.evidence
            if item.requirement_id in {"backtick-primary", "backtick-secondary"}
        }
        self.assertEqual(
            by_requirement,
            {
                "backtick-primary": (["src/example.tsx"], "src/example.tsx"),
                "backtick-secondary": (
                    ["src/secondary.ts"],
                    "src/secondary.ts",
                ),
            },
        )

    def test_path_shaped_literal_is_distinct_from_artifact_binding(self) -> None:
        target_content = "Primary old\n"
        secondary_content = "Secondary old\n"
        plan = _plan(
            target_content=target_content,
            secondary_slices=[
                ContextSlice(
                    path="src/secondary.ts",
                    kind="sibling",
                    sha256="b" * 64,
                    content=secondary_content,
                    line_range=(1, 1),
                )
            ],
            criteria=[
                AcceptanceCriterion(
                    "display-target-path",
                    'Display "src/example.tsx" in the rendered output.',
                    "literal",
                ),
                AcceptanceCriterion(
                    "same-path-value-twice",
                    'File "src/secondary.ts" must contain "src/secondary.ts".',
                    "literal",
                ),
            ],
        )
        diff = _join_diffs(
            _replacement_diff(
                "src/example.tsx",
                target_content,
                "src/example.tsx\n",
            ),
            _replacement_diff(
                "src/secondary.ts",
                secondary_content,
                "src/secondary.ts\n",
            ),
        )

        report = review_diff_deterministically(
            plan,
            diff,
            task_spec={
                "allowed_files": ["src/example.tsx", "src/secondary.ts"]
            },
        )

        self.assertTrue(report.passed)
        display_evidence = next(
            item
            for item in report.evidence
            if item.requirement_id == "display-target-path"
        )
        repeated_evidence = next(
            item
            for item in report.evidence
            if item.requirement_id == "same-path-value-twice"
        )
        self.assertEqual(display_evidence.intended_paths, ["src/example.tsx"])
        self.assertEqual(display_evidence.applied_match_count, 1)
        self.assertEqual(repeated_evidence.intended_paths, ["src/secondary.ts"])
        self.assertEqual(repeated_evidence.inspected_path, "src/secondary.ts")
        self.assertEqual(repeated_evidence.applied_match_count, 1)

    def test_root_level_secondary_artifact_can_supply_exact_literal(self) -> None:
        target_content = "Primary old\n"
        secondary_content = "# Old\n"
        plan = _plan(
            target_content=target_content,
            secondary_slices=[
                ContextSlice(
                    path="README.md",
                    kind="sibling",
                    sha256="b" * 64,
                    content=secondary_content,
                    line_range=(1, 1),
                )
            ],
            criteria=[
                AcceptanceCriterion(
                    "root-secondary",
                    'File "README.md" must contain "RootLiteral".',
                    "literal",
                )
            ],
        )

        report = review_diff_deterministically(
            plan,
            _replacement_diff("README.md", secondary_content, "RootLiteral\n"),
            task_spec={"allowed_files": ["src/example.tsx", "README.md"]},
        )

        self.assertTrue(report.passed)
        evidence = next(
            item for item in report.evidence if item.requirement_id == "root-secondary"
        )
        self.assertEqual(evidence.intended_paths, ["README.md"])
        self.assertEqual(evidence.inspected_path, "README.md")

    def test_repo_directories_named_a_and_b_are_not_stripped_as_diff_prefixes(self) -> None:
        for path in ("a/module.py", "b/module.py"):
            with self.subTest(path=path):
                plan = _plan(
                    target_path=path,
                    target_content="old = True\n",
                    constraints=ContentConstraints(
                        ["RequiredLiteral"], [], [], [], None, None
                    ),
                )
                diff = _replacement_diff(
                    path,
                    "old = True\n",
                    'value = "RequiredLiteral"\n',
                )

                report = review_diff_deterministically(plan, diff)

                self.assertTrue(report.passed)
                evidence = next(
                    item
                    for item in report.evidence
                    if item.requirement_id == "constraint.must_contain.0"
                )
                self.assertEqual(evidence.intended_paths, [path])
                self.assertEqual(evidence.inspected_path, path)

    def test_replace_and_update_do_not_accept_an_unchanged_baseline_literal(self) -> None:
        target_content = "ExistingLiteral\nOld state\n"
        for verb in ("Replace", "Update"):
            with self.subTest(verb=verb):
                criterion_id = f"{verb.lower()}-existing"
                plan = _plan(
                    target_content=target_content,
                    criteria=[
                        AcceptanceCriterion(
                            criterion_id,
                            f'{verb} the target with "ExistingLiteral".',
                            "literal",
                        )
                    ],
                )

                report = review_diff_deterministically(
                    plan,
                    _replacement_diff(
                        "src/example.tsx",
                        target_content,
                        "ExistingLiteral\nNew state\n",
                    ),
                )

                self.assertFalse(report.passed)
                self.assertEqual(
                    report.findings[0].id,
                    "literal_acceptance_not_introduced",
                )
                evidence = next(
                    item
                    for item in report.evidence
                    if item.requirement_id == criterion_id
                )
                self.assertEqual(evidence.baseline_match_count, 1)
                self.assertEqual(evidence.applied_match_count, 1)
                self.assertFalse(evidence.introduced)
                self.assertFalse(evidence.satisfied)

    def test_relocating_existing_literal_is_not_introduction_and_hashes_its_hunk(
        self,
    ) -> None:
        target_content = "ExistingLiteral\nAlpha\nBeta\n"
        plan = _plan(
            target_content=target_content,
            criteria=[
                AcceptanceCriterion(
                    "add-existing-relocated",
                    'Add "ExistingLiteral" to the target.',
                    "literal",
                )
            ],
        )
        diff = _replacement_diff(
            "src/example.tsx",
            target_content,
            "Alpha\nBeta\nExistingLiteral\n",
        )

        report = review_diff_deterministically(plan, diff)

        self.assertFalse(report.passed)
        self.assertEqual(
            report.findings[0].id,
            "literal_acceptance_not_introduced",
        )
        evidence = next(
            item
            for item in report.evidence
            if item.requirement_id == "add-existing-relocated"
        )
        expected_patch = "\n".join(_patch_for_path(diff, "src/example.tsx"))
        self.assertEqual(evidence.baseline_match_count, 1)
        self.assertEqual(evidence.applied_match_count, 1)
        self.assertFalse(evidence.introduced)
        self.assertFalse(evidence.satisfied)
        self.assertEqual(
            evidence.diff_hunk_sha256,
            hashlib.sha256(expected_patch.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            evidence.diff_hunk_line_count,
            len(_patch_for_path(diff, "src/example.tsx")),
        )

    def test_python_relative_from_import_removal_is_not_hidden_by_triple_string(
        self,
    ) -> None:
        cases = {
            ".helpers": "from .helpers import helper",
            "..shared.helpers": "from ..shared.helpers import helper",
        }
        for import_name, statement in cases.items():
            with self.subTest(import_name=import_name):
                target_content = f"{statement}\nVALUE = helper()\n"
                applied = (
                    f'"""Inactive example only:\n{statement}\n"""\n'
                    "VALUE = 1\n"
                )
                plan = _plan(
                    target_path="src/module.py",
                    target_content=target_content,
                    constraints=ContentConstraints(
                        [], [], [import_name], [], None, None
                    ),
                )

                report = review_diff_deterministically(
                    plan,
                    _replacement_diff("src/module.py", target_content, applied),
                )

                self.assertFalse(report.passed)
                self.assertEqual(report.findings[0].id, "imports_violated")
                self.assertEqual(report.findings[0].details, import_name)

    def test_multiline_js_import_removal_is_not_hidden_by_inactive_decoys(self) -> None:
        target_content = (
            "import {\n"
            "  helper,\n"
            "  other,\n"
            '} from "./helpers";\n'
            "export const value = helper;\n"
        )
        applied = (
            '// import { helper } from "./helpers";\n'
            "/* import {\n"
            "  helper,\n"
            '} from "./helpers"; */\n'
            'const template = `import { helper } from "./helpers";`;\n'
            'const quoted = "import helper from \'./helpers\';";\n'
            "export const value = 1;\n"
        )
        plan = _plan(
            target_path="src/module.ts",
            target_content=target_content,
            constraints=ContentConstraints(
                [], [], ["./helpers"], [], None, None
            ),
        )

        report = review_diff_deterministically(
            plan,
            _replacement_diff("src/module.ts", target_content, applied),
        )

        self.assertFalse(report.passed)
        self.assertEqual(report.findings[0].id, "imports_violated")
        self.assertEqual(report.findings[0].details, "./helpers")

    def test_inactive_comments_and_strings_do_not_preserve_exports(self) -> None:
        cases = {
            "default": "export default function Page() {}\n",
            "Ready": "export const Ready = true;\n",
        }
        for export_name, target_content in cases.items():
            with self.subTest(export_name=export_name):
                active_spelling = target_content.strip()
                applied = (
                    f"// {active_spelling}\n"
                    f"/* {active_spelling} */\n"
                    f'const quoted = "{active_spelling}";\n'
                    f"const template = `{active_spelling}`;\n"
                )
                plan = _plan(
                    target_path="src/module.ts",
                    target_content=target_content,
                    constraints=ContentConstraints(
                        [], [], [], [export_name], None, None
                    ),
                )

                report = review_diff_deterministically(
                    plan,
                    _replacement_diff("src/module.ts", target_content, applied),
                )

                self.assertFalse(report.passed)
                self.assertEqual(report.findings[0].id, "exports_violated")
                self.assertEqual(report.findings[0].details, export_name)

    def test_export_preservation_handles_alias_direction_and_typescript_forms(
        self,
    ) -> None:
        baseline = (
            "const localPublic = 1;\n"
            "const localDefault = () => 1;\n"
            "export { localPublic as Public, localDefault as default };\n"
            "export enum Mode { One }\n"
            "export abstract class Base {}\n"
            "export declare function contract(): void;\n"
            "export namespace API { export const value = 1; }\n"
        )
        preserved = (
            "const replacement = 2;\n"
            "const nextDefault = () => 2;\n"
            "export { replacement as Public, nextDefault as default };\n"
            "export enum Mode { Two }\n"
            "export abstract class Base {}\n"
            "export declare function contract(): void;\n"
            "export namespace API { export const value = 2; }\n"
        )
        constraints = ContentConstraints(
            [],
            [],
            [],
            ["Public", "default", "Mode", "Base", "contract", "API"],
            None,
            None,
        )
        plan = _plan(
            target_path="src/module.ts",
            target_content=baseline,
            constraints=constraints,
        )

        report = review_diff_deterministically(
            plan,
            _replacement_diff("src/module.ts", baseline, preserved),
        )
        self.assertTrue(report.passed, report.findings)

        wrong_direction = preserved.replace(
            "export { replacement as Public, nextDefault as default };",
            "export { Public as Renamed, nextDefault as default };",
        )
        report = review_diff_deterministically(
            plan,
            _replacement_diff("src/module.ts", baseline, wrong_direction),
        )

        self.assertFalse(report.passed)
        self.assertIn(
            ("exports_violated", "Public"),
            [(finding.id, finding.details) for finding in report.findings],
        )

    def test_filename_literal_is_distinct_from_file_artifact_binding(self) -> None:
        plan = _plan(
            target_path="worker.py",
            target_content="old\n",
            criteria=[
                AcceptanceCriterion(
                    "display-filename",
                    'The exact filename "worker.py" must be displayed.',
                    "literal",
                ),
                AcceptanceCriterion(
                    "artifact-literal",
                    'File "worker.py" must contain "RequiredLiteral".',
                    "literal",
                ),
            ],
        )
        report = review_diff_deterministically(
            plan,
            _replacement_diff(
                "worker.py",
                "old\n",
                "print('worker.py RequiredLiteral')\n",
            ),
            task_spec={"allowed_files": ["worker.py"]},
        )

        self.assertTrue(report.passed, report.findings)
        evidence = {
            item.requirement_id: item
            for item in report.evidence
            if item.requirement_id in {"display-filename", "artifact-literal"}
        }
        self.assertEqual(evidence["display-filename"].intended_paths, ["worker.py"])
        self.assertEqual(evidence["display-filename"].applied_match_count, 1)
        self.assertEqual(evidence["artifact-literal"].applied_match_count, 1)

    def test_common_secondary_path_phrasings_bind_to_authorized_artifact(self) -> None:
        path = "src/secondary.ts"
        target_content = "Primary old\n"
        secondary_content = "Secondary old\n"
        descriptions = [
            f'File {path} must contain "SecondaryLiteral".',
            f'In {path}, add "SecondaryLiteral".',
            f'Add "SecondaryLiteral" to {path}.',
            f'Ensure "SecondaryLiteral" is present in the file {path}.',
            f'"SecondaryLiteral" must appear in {path}.',
        ]
        for index, description in enumerate(descriptions):
            with self.subTest(description=description):
                plan = _plan(
                    target_content=target_content,
                    secondary_slices=[
                        ContextSlice(
                            path=path,
                            kind="sibling",
                            sha256="b" * 64,
                            content=secondary_content,
                            line_range=(1, 1),
                        )
                    ],
                    criteria=[
                        AcceptanceCriterion(
                            f"secondary-{index}",
                            description,
                            "literal",
                        )
                    ],
                )
                report = review_diff_deterministically(
                    plan,
                    _replacement_diff(path, secondary_content, "SecondaryLiteral\n"),
                    task_spec={"allowed_files": ["src/example.tsx", path]},
                )

                self.assertTrue(report.passed, report.findings)
                evidence = next(
                    item
                    for item in report.evidence
                    if item.requirement_id == f"secondary-{index}"
                )
                self.assertEqual(evidence.intended_paths, [path])
                self.assertEqual(evidence.inspected_path, path)

    def test_existing_secondary_without_server_snapshot_fails_closed(self) -> None:
        path = "src/secondary.ts"
        plan = _plan(target_content="Primary old\n")

        report = review_diff_deterministically(
            plan,
            _replacement_diff(path, "Secondary old\n", "Secondary new\n"),
            task_spec={"allowed_files": ["src/example.tsx", path]},
        )

        self.assertFalse(report.passed)
        self.assertIn(
            ("artifact_baseline_unbound", path),
            [(finding.id, finding.path) for finding in report.findings],
        )

    def test_authorized_secondary_path_is_not_a_prefix_authority_match(self) -> None:
        path = "src/secondary.ts"
        target_content = "Primary old\n"
        secondary_content = "Secondary old\n"
        plan = _plan(
            target_content=target_content,
            secondary_slices=[
                ContextSlice(
                    path=path,
                    kind="sibling",
                    sha256="b" * 64,
                    content=secondary_content,
                    line_range=(1, 1),
                )
            ],
            criteria=[
                AcceptanceCriterion(
                    "longer-path",
                    'Add "SecondaryLiteral" to src/secondary.ts.backup.',
                    "literal",
                )
            ],
        )

        report = review_diff_deterministically(
            plan,
            _replacement_diff(path, secondary_content, "SecondaryLiteral\n"),
            task_spec={"allowed_files": ["src/example.tsx", path]},
        )

        self.assertFalse(report.passed)
        evidence = next(
            item for item in report.evidence if item.requirement_id == "longer-path"
        )
        self.assertEqual(evidence.intended_paths, ["src/example.tsx"])

    def test_transformations_reject_append_only_but_allow_source_in_destination(
        self,
    ) -> None:
        path = "src/example.tsx"
        append_plan = _plan(
            target_content='const label = "Old";\n',
            source_task='Change the text "Old" to "New".',
        )
        append_report = review_diff_deterministically(
            append_plan,
            _replacement_diff(
                path,
                'const label = "Old";\n',
                'const label = "Old";\nconst next = "New";\n',
            ),
        )
        self.assertFalse(append_report.passed)
        self.assertIn(
            "transformation_source_not_replaced",
            [finding.id for finding in append_report.findings],
        )

        for source, final in (("x", "y"), ("UI", "UI ready"), ("Old", "Old and New")):
            with self.subTest(source=source, final=final):
                baseline = f'const label = "{source}";\n'
                applied = f'const label = "{final}";\n'
                plan = _plan(
                    target_content=baseline,
                    source_task=f'Change the text "{source}" to "{final}".',
                )
                report = review_diff_deterministically(
                    plan,
                    _replacement_diff(path, baseline, applied),
                )
                self.assertTrue(report.passed, report.findings)

    def test_duplicate_transformation_final_keeps_each_secondary_path_binding(
        self,
    ) -> None:
        primary_path = "src/example.tsx"
        secondary_path = "src/secondary.ts"
        primary_content = 'const value = "X";\n'
        secondary_content = 'const value = "A";\n'
        plan = _plan(
            target_content=primary_content,
            source_task="\n".join(
                [
                    f'Change "A" to "B" in {secondary_path}.',
                    f'Change "X" to "B" in {primary_path}.',
                ]
            ),
            secondary_slices=[
                ContextSlice(
                    path=secondary_path,
                    kind="sibling",
                    sha256="b" * 64,
                    content=secondary_content,
                    line_range=(1, 1),
                )
            ],
        )
        diff = _join_diffs(
            _replacement_diff(primary_path, primary_content, 'const value = "B";\n'),
            _replacement_diff(
                secondary_path,
                secondary_content,
                'const value = "B";\n',
            ),
        )

        report = review_diff_deterministically(
            plan,
            diff,
            task_spec={"allowed_files": [primary_path, secondary_path]},
        )

        self.assertTrue(report.passed, report.findings)
        transformations = [
            item
            for item in report.evidence
            if item.requirement_kind == "transformation"
        ]
        self.assertEqual(len(transformations), 2)
        self.assertEqual(
            {item.inspected_path for item in transformations},
            {primary_path, secondary_path},
        )
        self.assertTrue(all(item.satisfied for item in transformations))

    def test_duplicate_git_and_plain_unified_sections_are_rejected(self) -> None:
        target_content = "Old\n"
        plan = _plan(target_content=target_content)
        git_diff = _join_diffs(
            _replacement_diff("src/example.tsx", target_content, "First\n"),
            _replacement_diff("src/example.tsx", "First\n", "Second\n"),
        )
        plain_section_one = "\n".join(
            [
                "--- a/src/example.tsx",
                "+++ b/src/example.tsx",
                "@@ -1,1 +1,1 @@",
                "-Old",
                "+First",
                "",
            ]
        )
        plain_section_two = "\n".join(
            [
                "--- a/src/example.tsx",
                "+++ b/src/example.tsx",
                "@@ -1,1 +1,1 @@",
                "-First",
                "+Second",
                "",
            ]
        )

        for style, diff in {
            "git": git_diff,
            "plain": _join_diffs(plain_section_one, plain_section_two),
        }.items():
            with self.subTest(style=style):
                report = review_diff_deterministically(plan, diff)

                self.assertFalse(report.passed)
                duplicates = [
                    finding
                    for finding in report.findings
                    if finding.id == "duplicate_diff_path_sections"
                ]
                self.assertEqual(len(duplicates), 1)
                self.assertEqual(duplicates[0].path, "src/example.tsx")

    def test_unauthorized_path_evidence_is_never_marked_satisfied(self) -> None:
        plan = _plan(
            criteria=[
                AcceptanceCriterion(
                    "unauthorized-secondary",
                    'File "src/unauthorized.ts" must contain "UnauthorizedLiteral".',
                    "literal",
                )
            ],
        )
        diff = _replacement_diff(
            "src/unauthorized.ts",
            "",
            "UnauthorizedLiteral\n",
        )

        report = review_diff_deterministically(
            plan,
            diff,
            task_spec={"allowed_files": ["src/example.tsx"]},
        )

        self.assertFalse(report.passed)
        self.assertEqual(
            report.findings[0].id,
            "literal_acceptance_path_unauthorized",
        )
        self.assertEqual(report.findings[0].path, "src/unauthorized.ts")
        evidence = [
            item
            for item in report.evidence
            if item.requirement_id == "unauthorized-secondary"
        ]
        self.assertTrue(evidence)
        self.assertEqual(
            {item.inspected_path for item in evidence},
            {"src/unauthorized.ts"},
        )
        self.assertTrue(
            all(item.extraction_method.endswith(":unauthorized_path") for item in evidence)
        )
        self.assertTrue(all(item.satisfied is False for item in evidence))

    def test_new_file_snapshot_binds_literal_and_content_hash_evidence(self) -> None:
        secondary_path = "new-helper.ts"
        secondary_content = "NewLiteral\n"
        plan = _plan(
            criteria=[
                AcceptanceCriterion(
                    "new-secondary",
                    f'File "{secondary_path}" must contain "NewLiteral".',
                    "literal",
                )
            ],
        )
        diff = _replacement_diff(secondary_path, "", secondary_content)
        empty_sha256 = hashlib.sha256(b"").hexdigest()
        snapshots = {
            secondary_path: {
                "schema_version": "coding.review-artifact-snapshot/v1",
                "path": secondary_path,
                "exists": False,
                "content": "",
                "content_sha256": empty_sha256,
            }
        }

        report = review_diff_deterministically(
            plan,
            diff,
            task_spec={"allowed_files": ["src/example.tsx", secondary_path]},
            task_id="task-review",
            attempt_id="attempt-new-file",
            artifact_snapshots=snapshots,
        )

        self.assertTrue(report.passed)
        evidence = next(
            item for item in report.evidence if item.requirement_id == "new-secondary"
        )
        expected_patch = "\n".join(_patch_for_path(diff, secondary_path))
        self.assertEqual(evidence.inspected_path, secondary_path)
        self.assertEqual(evidence.baseline_sha256, empty_sha256)
        self.assertEqual(
            evidence.applied_sha256,
            hashlib.sha256(b"NewLiteral\n").hexdigest(),
        )
        self.assertEqual(
            evidence.diff_hunk_sha256,
            hashlib.sha256(expected_patch.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(evidence.task_id, "task-review")
        self.assertEqual(evidence.attempt_id, "attempt-new-file")
        self.assertTrue(evidence.introduced)
        self.assertTrue(evidence.satisfied)

    def test_misplaced_evidence_records_exact_category_and_path(self) -> None:
        plan = _plan(
            constraints=ContentConstraints(
                ["RequiredLiteral"], [], [], [], None, None
            )
        )
        cases = {
            "wrong_production": "src/other.ts",
            "test": "tests/example.test.ts",
            "documentation": "docs/guide.md",
            "decoy": "src/example.decoy.ts",
            "generated_evidence": "artifacts/result.ts",
        }

        for category, path in cases.items():
            with self.subTest(category=category, path=path):
                report = review_diff_deterministically(
                    plan,
                    _replacement_diff(path, "", "RequiredLiteral\n"),
                )

                self.assertFalse(report.passed)
                self.assertEqual(
                    report.findings[0].id,
                    f"must_contain_misplaced_{category}",
                )
                self.assertEqual(report.findings[0].path, path)
                misplaced = next(
                    item
                    for item in report.evidence
                    if item.requirement_id == "constraint.must_contain.0"
                    and ":misplaced:" in item.extraction_method
                )
                self.assertEqual(misplaced.intended_paths, ["src/example.tsx"])
                self.assertEqual(misplaced.inspected_path, path)
                self.assertTrue(
                    misplaced.extraction_method.endswith(f":misplaced:{category}")
                )
                self.assertFalse(misplaced.satisfied)

    def test_effective_task_ignores_pasted_context_outside_bounded_proposal(self) -> None:
        target_content = "ExistingLiteral\nOld state\n"
        source_task = (
            'Pasted context only: Add "ExistingLiteral" to src/example.tsx.\n\n'
            "Proposal task:\n"
            "```json\n"
            '{"task":"Keep ExistingLiteral present while changing the status.",'
            '"mode":"proposal","target_file":"src/example.tsx",'
            '"allowed_files":["src/example.tsx"],"forbidden_files":[],'
            '"expected_checks":[],"rollback_hint":"restore"}\n'
            "```"
        )
        plan = _plan(
            target_content=target_content,
            source_task=source_task,
            constraints=ContentConstraints(
                ["ExistingLiteral"], [], [], [], None, None
            ),
        )

        report = review_diff_deterministically(
            plan,
            _replacement_diff(
                "src/example.tsx",
                target_content,
                "ExistingLiteral\nNew state\n",
            ),
        )

        self.assertTrue(report.passed)
        evidence = next(
            item
            for item in report.evidence
            if item.requirement_id == "constraint.must_contain.0"
        )
        self.assertEqual(evidence.baseline_match_count, 1)
        self.assertEqual(evidence.applied_match_count, 1)
        self.assertFalse(evidence.introduced)
        self.assertTrue(evidence.satisfied)

    def test_unquoted_authorized_secondary_path_binds_literal_evidence(self) -> None:
        target_content = "Primary old\n"
        secondary_content = "Secondary old\n"
        plan = _plan(
            target_content=target_content,
            secondary_slices=[
                ContextSlice(
                    path="src/secondary.ts",
                    kind="sibling",
                    sha256="b" * 64,
                    content=secondary_content,
                    line_range=(1, 1),
                )
            ],
            criteria=[
                AcceptanceCriterion(
                    "unquoted-secondary",
                    'File src/secondary.ts must contain "SecondaryLiteral".',
                    "literal",
                )
            ],
        )

        report = review_diff_deterministically(
            plan,
            _replacement_diff(
                "src/secondary.ts",
                secondary_content,
                "SecondaryLiteral\n",
            ),
            task_spec={
                "allowed_files": ["src/example.tsx", "src/secondary.ts"]
            },
        )

        self.assertTrue(report.passed)
        evidence = next(
            item
            for item in report.evidence
            if item.requirement_id == "unquoted-secondary"
        )
        self.assertEqual(evidence.intended_paths, ["src/secondary.ts"])
        self.assertEqual(evidence.inspected_path, "src/secondary.ts")
        self.assertTrue(evidence.satisfied)

    def test_behavioral_equivalent_is_not_forced_to_use_exact_spelling(self) -> None:
        plan = _plan(
            criteria=[
                AcceptanceCriterion(
                    "behavioral-success",
                    "Return a successful response without prescribing source spelling.",
                    "behavioral",
                )
            ],
        )

        report = review_diff_deterministically(
            plan,
            _diff(
                "+export default function Page() {\n"
                "+  return <main>Ready</main>;\n"
                "+}"
            ),
        )

        self.assertTrue(report.passed)
        evidence = next(
            item
            for item in report.evidence
            if item.requirement_id == "behavioral-success"
        )
        self.assertIsNone(evidence.satisfied)
        self.assertEqual(
            evidence.extraction_method,
            "behavioral_deferred_to_tests_and_verifier",
        )

    def test_valid_multi_file_requirements_bind_to_their_own_artifacts(self) -> None:
        target_content = "Primary old\n"
        secondary_content = "Secondary old\n"
        plan = _plan(
            target_content=target_content,
            secondary_slices=[
                ContextSlice(
                    path="src/secondary.ts",
                    kind="sibling",
                    sha256="b" * 64,
                    content=secondary_content,
                    line_range=(1, 1),
                )
            ],
            criteria=[
                AcceptanceCriterion(
                    "primary-literal",
                    'File "src/example.tsx" must contain "PrimaryLiteral".',
                    "literal",
                ),
                AcceptanceCriterion(
                    "secondary-literal",
                    'File "src/secondary.ts" must contain "SecondaryLiteral".',
                    "literal",
                ),
            ],
        )
        diff = _join_diffs(
            _replacement_diff(
                "src/example.tsx",
                target_content,
                "PrimaryLiteral\n",
            ),
            _replacement_diff(
                "src/secondary.ts",
                secondary_content,
                "SecondaryLiteral\n",
            ),
        )

        report = review_diff_deterministically(
            plan,
            diff,
            task_spec={
                "allowed_files": ["src/example.tsx", "src/secondary.ts"]
            },
        )

        self.assertTrue(report.passed)
        by_requirement = {
            item.requirement_id: item.inspected_path
            for item in report.evidence
            if item.requirement_id in {"primary-literal", "secondary-literal"}
        }
        self.assertEqual(
            by_requirement,
            {
                "primary-literal": "src/example.tsx",
                "secondary-literal": "src/secondary.ts",
            },
        )

    def test_forbidden_content_is_attributed_to_exact_offending_path(self) -> None:
        plan = _plan(
            constraints=ContentConstraints(
                [], ["ForbiddenLiteral"], [], [], None, None
            )
        )
        diff = _join_diffs(
            _diff(
                "+export default function Page() {\n"
                "+  return <main>ForbiddenLiteral</main>;\n"
                "+}"
            ),
            _replacement_diff(
                "src/secondary.ts",
                "old\n",
                "clean\n",
            ),
        )

        report = review_diff_deterministically(plan, diff)

        self.assertFalse(report.passed)
        finding = next(
            item
            for item in report.findings
            if item.id == "forbidden_must_not_contain"
        )
        self.assertEqual(finding.path, "src/example.tsx")

    def test_target_forbidden_constraint_does_not_reject_secondary_test_mention(
        self,
    ) -> None:
        target_content = "export const value = 'Legacy';\n"
        test_path = "tests/example.test.ts"
        test_content = "expect(value).not.toContain('other');\n"
        plan = _plan(
            target_content=target_content,
            source_task=(
                'Remove "Legacy" from src/example.tsx and add '
                "tests/example.test.ts to verify it is absent."
            ),
            constraints=ContentConstraints([], ["Legacy"], [], [], None, None),
            secondary_slices=[
                ContextSlice(
                    path=test_path,
                    kind="sibling",
                    sha256="b" * 64,
                    content=test_content,
                    line_range=(1, 1),
                )
            ],
        )
        diff = _join_diffs(
            _replacement_diff(
                "src/example.tsx",
                target_content,
                "export const value = 'Ready';\n",
            ),
            _replacement_diff(
                test_path,
                test_content,
                "expect(value).not.toContain('Legacy');\n",
            ),
        )

        report = review_diff_deterministically(
            plan,
            diff,
            task_spec={"allowed_files": ["src/example.tsx", test_path]},
        )

        self.assertTrue(report.passed, report.findings)
        forbidden_evidence = [
            item
            for item in report.evidence
            if item.requirement_kind == "must_not_contain"
        ]
        self.assertEqual(
            [item.inspected_path for item in forbidden_evidence],
            ["src/example.tsx"],
        )

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

    def test_literal_kind_without_an_explicit_literal_is_not_treated_as_source_text(self) -> None:
        plan = _plan(
            criteria=[
                AcceptanceCriterion(
                    "behavior-worded-as-literal",
                    "Render OK.",
                    "literal",
                )
            ],
        )

        report = review_diff_deterministically(
            plan,
            _diff("+export default function Page() { return <main>OK</main>; }"),
        )

        self.assertTrue(report.passed)

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
