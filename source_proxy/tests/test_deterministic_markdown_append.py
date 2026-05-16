from __future__ import annotations

import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest import mock

from source_proxy.api.decision import _coder_agent_stub_prompt_text
from source_proxy.planning.architect import (
    FallthroughToLLM,
    Plan,
    _class_fragments,
    plan_task_deterministically,
    plan_markdown_append_deterministically,
)
from source_proxy.tasks.long_running import propose_coder_agent_diff_payload_from_plan
from source_proxy.verification.diff import (
    _extract_class_fragments,
    _requirement_coverage,
    preview_diff_verification,
)


TASK = """Target file: docs/phase-8-manual-check.md

Append one short sentence under the existing paragraph:
"Manual verification should clearly report whether a diff was produced."
"""
LITERAL = "Manual verification should clearly report whether a diff was produced."
SMOKE_LITERAL = "Phase 2A post-apply verification smoke test."


class DeterministicMarkdownAppendTests(unittest.TestCase):
    def _root_with_markdown(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        target = root / "docs/phase-8-manual-check.md"
        target.parent.mkdir(parents=True)
        target.write_text(
            "# Phase 8 Manual Check\n\n"
            "Approved diffs should require post-apply verification before completion.\n",
            encoding="utf-8",
        )
        return tmp, root

    def test_explicit_markdown_append_creates_deterministic_packet(self) -> None:
        tmp, root = self._root_with_markdown()
        with tmp:
            result = plan_markdown_append_deterministically(TASK, "task-md", root)

            self.assertIsInstance(result, Plan)
            plan = result.plan
            self.assertTrue(plan.plan_id.startswith("det-md-append-"))
            self.assertEqual(plan.bundle_snapshot.bundle_path, "deterministic:markdown_append")
            self.assertEqual(plan.bundle_snapshot.bundle_sha256, "")
            self.assertEqual(plan.classification.task_class, "implement")
            self.assertEqual(plan.classification.estimated_complexity, "small")
            self.assertEqual(plan.coder_packet.target_file.path, "docs/phase-8-manual-check.md")
            self.assertEqual(
                [criterion.description for criterion in plan.coder_packet.acceptance_criteria],
                [
                    "Modify only docs/phase-8-manual-check.md.",
                    f'Output must contain the appended literal sentence: "{LITERAL}".',
                ],
            )
            self.assertEqual(plan.coder_packet.constraints.must_contain, [LITERAL])
            self.assertEqual(len(plan.coder_packet.context_slices), 1)
            self.assertEqual(plan.coder_packet.context_slices[0].kind, "target")
            self.assertEqual(
                plan.verification_plan.required_checks[0].command,
                ["git", "apply", "--check"],
            )
            self.assertIn("deterministic small Markdown append fallback", " ".join(plan.coder_packet.style_directives))

    def test_backend_produces_real_unified_diff_touching_only_target(self) -> None:
        tmp, root = self._root_with_markdown()
        with tmp:
            result = plan_markdown_append_deterministically(TASK, "task-md", root)
            self.assertIsInstance(result, Plan)

            out = propose_coder_agent_diff_payload_from_plan(
                architect_plan=result.plan,
                workspace_root=root,
                llm_call=lambda *_args: (_ for _ in ()).throw(AssertionError("LLM should not run")),
                model_alias="local",
            )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertEqual(out["target"], "docs/phase-8-manual-check.md")
            self.assertIn(f"+{LITERAL}", out["proposed_diff"])
            self.assertIn("--- a/docs/phase-8-manual-check.md", out["proposed_diff"])
            self.assertEqual(out["coder_diagnostics"]["validation_status"], "preview_ready")
            with mock.patch.dict("os.environ", {"SPIRIT_PROJECT_PATH": str(root)}):
                preview = preview_diff_verification(
                    out["proposed_diff"],
                    task_text=TASK,
                    architect_plan=result.plan,
                )
            self.assertEqual(
                [file["path"] for file in preview["changed_files"]],
                ["docs/phase-8-manual-check.md"],
            )
            self.assertTrue(preview["git_apply_check_ok"])

    def test_exact_smoke_diff_passes_requirement_coverage_and_reviewer(self) -> None:
        tmp, root = self._root_with_markdown()
        with tmp:
            task = (
                f"Append the sentence `{SMOKE_LITERAL}` to "
                "docs/phase-8-manual-check.md. Do not edit any other file."
            )
            result = plan_task_deterministically(task, "task-md-smoke", root)
            self.assertIsInstance(result, Plan)
            self.assertEqual(result.plan.coder_packet.constraints.must_contain, [SMOKE_LITERAL])
            self.assertNotIn("post-apply", _class_fragments(task))
            self.assertNotIn(
                "post-apply",
                _requirement_coverage("", [], task).get("required", {}).get("class_fragments", []),
            )
            self.assertFalse(
                any(
                    "class fragment post-apply" in criterion.description
                    for criterion in result.plan.coder_packet.acceptance_criteria
                )
            )
            diff = "\n".join(
                [
                    "--- a/docs/phase-8-manual-check.md",
                    "+++ b/docs/phase-8-manual-check.md",
                    "@@ -1,3 +1,4 @@",
                    " # Phase 8 Manual Check",
                    " ",
                    " Approved diffs should require post-apply verification before completion.",
                    f"+{SMOKE_LITERAL}",
                    "",
                ]
            )

            with mock.patch.dict("os.environ", {"SPIRIT_PROJECT_PATH": str(root)}):
                preview = preview_diff_verification(
                    diff,
                    task_text=task,
                    architect_plan=result.plan,
                )

            self.assertEqual(preview["status"], "preview_ready")
            self.assertTrue(preview["git_apply_check_ok"])
            self.assertTrue(preview["requirement_coverage"]["ok"])
            self.assertTrue(preview["review_report"]["passed"])
            self.assertEqual(preview["blocked_reasons"], [])
            self.assertEqual(
                preview["requirement_coverage"]["required"]["texts"],
                [SMOKE_LITERAL],
            )
            self.assertNotIn(
                "post-apply",
                preview["requirement_coverage"]["required"]["class_fragments"],
            )
            reason_codes = {reason["reason_code"] for reason in preview["blocked_reasons"]}
            self.assertNotIn("review_missing_must_contain", reason_codes)
            self.assertNotIn("review_literal_acceptance_missing", reason_codes)

    def test_hyphenated_prose_terms_are_not_class_fragments(self) -> None:
        task = " ".join(
            [
                "Explain post-apply docs-only no-diff target-only phase-8",
                "phase-2a human-readable status in the manual.",
            ]
        )

        for term in ("post-apply", "docs-only", "no-diff", "target-only", "phase-8"):
            self.assertNotIn(term, _class_fragments(task))
            self.assertNotIn(term, _extract_class_fragments(task))

    def test_file_path_fragments_are_not_class_fragments(self) -> None:
        task = (
            "Add a Vitest case for docs/file with spaces.md, spaces.md, "
            "phase-8-manual-check.md, and unified-diff-paths.test.ts."
        )

        planner_fragments = _class_fragments(task)
        verifier_fragments = _extract_class_fragments(task)

        for fragment in (
            "spaces.md",
            "file with spaces.md",
            "docs/file with spaces.md",
            "phase-8-manual-check.md",
            "unified-diff-paths.test.ts",
        ):
            self.assertNotIn(fragment, planner_fragments)
            self.assertNotIn(fragment, verifier_fragments)

    def test_code_like_fragments_remain_requirements(self) -> None:
        task = (
            "Update CodingAgentInterface, CoderPacket, function_name, "
            "camelCaseIdentifier, collectPathsFromUnifiedDiff, diffTouchesExplicitTarget, "
            "TaskSpec, and source_proxy.tasks.long_running. "
            "className fragments: text-6xl transition-all"
        )

        planner_fragments = _class_fragments(task)
        verifier_fragments = _extract_class_fragments(task)

        for fragment in (
            "CodingAgentInterface",
            "CoderPacket",
            "function_name",
            "camelCaseIdentifier",
            "collectPathsFromUnifiedDiff",
            "diffTouchesExplicitTarget",
            "TaskSpec",
            "source_proxy.tasks.long_running",
            "text-6xl",
            "transition-all",
        ):
            self.assertIn(fragment, planner_fragments)
            self.assertIn(fragment, verifier_fragments)

    def test_backend_coder_stub_points_clients_to_proposed_diff_validation(self) -> None:
        text = _coder_agent_stub_prompt_text(
            "docs/phase-8-manual-check.md",
            "--- a/docs/phase-8-manual-check.md\n+++ b/docs/phase-8-manual-check.md\n@@ -1 +1 @@\n-old\n+new\n",
        )

        self.assertIn("proposed_diff", text)
        self.assertIn("approval-gate validation", text)
        self.assertIn("If the client rejects the diff", text)
        self.assertNotIn("converted into a unified diff", text)

    def test_git_apply_timeout_fails_closed_as_blocked_payload(self) -> None:
        tmp, root = self._root_with_markdown()
        with tmp:
            result = plan_markdown_append_deterministically(TASK, "task-md", root)
            self.assertIsInstance(result, Plan)

            with mock.patch(
                "source_proxy.tasks.long_running._git_apply_recount_check",
                side_effect=subprocess.TimeoutExpired(["git", "apply"], 15),
            ):
                out = propose_coder_agent_diff_payload_from_plan(
                    architect_plan=result.plan,
                    workspace_root=root,
                    llm_call=lambda *_args: (_ for _ in ()).throw(AssertionError("LLM should not run")),
                    model_alias="local",
                )

            self.assertEqual(out["proposed_diff"], "")
            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_backend_diff_generation_failed")
            self.assertIn("timed out", out["blocked_reason"])

    def test_missing_target_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = plan_markdown_append_deterministically(TASK, "task-md", Path(tmp))

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "target_missing")

    def test_non_markdown_target_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "docs/phase-8-manual-check.txt"
            target.parent.mkdir(parents=True)
            target.write_text("Current text.\n", encoding="utf-8")

            result = plan_markdown_append_deterministically(
                TASK.replace("docs/phase-8-manual-check.md", "docs/phase-8-manual-check.txt"),
                "task-md",
                root,
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "not_markdown_append_target")

    def test_ambiguous_append_text_fails_closed(self) -> None:
        tmp, root = self._root_with_markdown()
        with tmp:
            result = plan_markdown_append_deterministically(
                """Target file: docs/phase-8-manual-check.md

Append "First sentence." and "Second sentence."
""",
                "task-md",
                root,
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "ambiguous_markdown_append_literal")


if __name__ == "__main__":
    unittest.main()
