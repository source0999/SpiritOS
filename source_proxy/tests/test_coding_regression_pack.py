from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.decision import router as decision_router
from source_proxy.decision.router import DecisionInput, decide_route, resolve_target_from_task
from source_proxy.planning.architect import Plan, plan_task_deterministically
from source_proxy.planning.plan import task_spec_from_plan, save_plan
from source_proxy.tasks.long_running import (
    create_long_running_task,
    execute_approved_long_running_task,
    propose_coder_agent_diff_payload_from_plan,
    record_post_apply_verification,
    reset_long_running_tasks,
)
from source_proxy.verification.diff import DiffVerificationError, preview_diff_verification


DOC_TARGET = "docs/phase-8-manual-check.md"
DOC_BASE = (
    "# Phase 8 Manual Check\n\n"
    "Approved diffs should require post-apply verification before completion.\n"
)
DOC_LITERAL = "Phase 1A backend regression pack confirms approval safe docs edits."


def _doc_append_task(literal: str = DOC_LITERAL) -> str:
    return f'Append the sentence "{literal}" to {DOC_TARGET}. Do not edit any other file.'


def _standard_doc_diff(literal: str = DOC_LITERAL, target: str = DOC_TARGET) -> str:
    return "\n".join(
        [
            f"--- a/{target}",
            f"+++ b/{target}",
            "@@ -1,3 +1,4 @@",
            " # Phase 8 Manual Check",
            " ",
            " Approved diffs should require post-apply verification before completion.",
            f"+{literal}",
            "",
        ]
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CodingRegressionPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_cwd = os.getcwd()
        self._previous_db = os.environ.get("SOURCE_PROXY_LONG_RUNNING_TASKS_DB")
        self._previous_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        self._previous_audit = os.environ.get("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG")
        self._tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tempdir.name)
        os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = str(self.root / "tasks.sqlite3")
        os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = str(self.root / "audit.jsonl")
        os.environ["SPIRIT_PROJECT_PATH"] = str(self.root)
        (self.root / "source_proxy").mkdir(parents=True, exist_ok=True)
        _write(self.root / DOC_TARGET, DOC_BASE)
        os.chdir(self.root)
        reset_long_running_tasks()

    def tearDown(self) -> None:
        reset_long_running_tasks()
        os.chdir(self._previous_cwd)
        self._restore_env("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", self._previous_db)
        self._restore_env("SPIRIT_PROJECT_PATH", self._previous_project_path)
        self._restore_env("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG", self._previous_audit)
        self._tempdir.cleanup()

    def _restore_env(self, name: str, value: str | None) -> None:
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value

    def _planned_doc_task(self, task: str | None = None, task_id: str = "task-doc"):
        planned = plan_task_deterministically(task or _doc_append_task(), task_id, self.root)
        self.assertIsInstance(planned, Plan, planned)
        return planned.plan

    def _decision_client(self) -> TestClient:
        app = FastAPI()
        app.include_router(decision_router)
        return TestClient(app)

    def test_simple_docs_edit_reaches_safe_preview_without_writing(self) -> None:
        task = _doc_append_task()
        resolved = resolve_target_from_task(task, workspace_root=self.root)
        plan = self._planned_doc_task(task)
        before = (self.root / DOC_TARGET).read_text(encoding="utf-8")

        out = propose_coder_agent_diff_payload_from_plan(
            architect_plan=plan,
            workspace_root=self.root,
            llm_call=lambda *_args: (_ for _ in ()).throw(AssertionError("LLM should not run")),
        )
        preview = preview_diff_verification(
            out["proposed_diff"],
            route_type="local_route",
            task_text=task,
            architect_plan=plan,
        )

        self.assertEqual(resolved.path, DOC_TARGET)
        self.assertTrue(resolved.exists)
        self.assertEqual(
            task_spec_from_plan(plan).to_dict(),
            {
                "schema_version": 1,
                "task_type": "modify_existing_file",
                "target": DOC_TARGET,
                "allowed_files": [DOC_TARGET],
                "forbidden_files": [
                    "source_proxy/",
                    "src/components/coding/",
                    "src/lib/coding/",
                    "src/lib/spirit/apply-unified-diff.ts",
                    "scripts/",
                    "masterProxyPlan.md",
                    "masterSwarmPlan.md",
                    "notes.md",
                ],
                "literal_requirements": [DOC_LITERAL],
                "verification": ["git apply check", "literal present", "target-only"],
                "risk_tier": "low",
                "source": "deterministic",
            },
        )
        self.assertEqual(out["coder_diagnostics"]["task_spec"]["allowed_files"], [DOC_TARGET])
        self.assertEqual(out["target"], DOC_TARGET)
        self.assertEqual([file["path"] for file in preview["changed_files"]], [DOC_TARGET])
        self.assertEqual(preview["status"], "preview_ready")
        self.assertEqual(
            preview["task_spec_check"],
            {
                "ok": True,
                "reason_codes": [],
                "allowed_files": [DOC_TARGET],
                "forbidden_files": [
                    "source_proxy/",
                    "src/components/coding/",
                    "src/lib/coding/",
                    "src/lib/spirit/apply-unified-diff.ts",
                    "scripts/",
                    "masterProxyPlan.md",
                    "masterSwarmPlan.md",
                    "notes.md",
                ],
                "changed_files": [DOC_TARGET],
                "target": DOC_TARGET,
                "task_type": "modify_existing_file",
                "summary": "TaskSpec check passed.",
                "violations": {"outside_allowed": [], "forbidden": []},
            },
        )
        self.assertTrue(preview["git_apply_check_ok"], preview.get("git_apply_check_error"))
        self.assertTrue(preview["requirement_coverage"]["ok"])
        self.assertTrue(preview["review_report"]["passed"])
        self.assertTrue(preview["limits"]["file_writes_allowed"])
        self.assertFalse(preview["would_apply_diff"])
        self.assertFalse(preview["would_execute"])
        self.assertEqual((self.root / DOC_TARGET).read_text(encoding="utf-8"), before)

    def test_coder_task_spec_allowed_file_passes_for_docs_diff(self) -> None:
        plan = self._planned_doc_task()

        preview = preview_diff_verification(
            _standard_doc_diff(),
            route_type="local_route",
            task_text=_doc_append_task(),
            architect_plan=plan,
        )

        self.assertEqual(preview["status"], "preview_ready")
        self.assertTrue(preview["task_spec_check"]["ok"])
        self.assertEqual(preview["task_spec_check"]["allowed_files"], [DOC_TARGET])
        self.assertEqual(preview["task_spec_check"]["changed_files"], [DOC_TARGET])
        self.assertIn(
            {
                "tier": 1,
                "id": "task_spec_allowed_files",
                "status": "passed",
                "duration_ms": 0,
                "output": (
                    "TaskSpec allowed-files check passed. "
                    f"changed=[{DOC_TARGET}] allowed=[{DOC_TARGET}]"
                ),
                "blocking": True,
            },
            preview["deterministic_checks"],
        )

    def test_coder_task_spec_blocks_wrong_file_diff(self) -> None:
        plan = self._planned_doc_task()
        wrong_path = "source_proxy/api/decision.py"
        _write(self.root / wrong_path, "old\n")
        wrong_diff = _standard_doc_diff(target=wrong_path)

        preview = preview_diff_verification(
            wrong_diff,
            route_type="local_route",
            task_text=_doc_append_task(),
            architect_plan=plan,
        )

        reason_codes = {reason["reason_code"] for reason in preview["blocked_reasons"]}
        self.assertEqual(preview["status"], "blocked")
        self.assertIn("task_spec_allowed_file_violation", reason_codes)
        self.assertFalse(preview["limits"]["file_writes_allowed"])
        self.assertFalse(preview["would_apply_diff"])
        self.assertFalse(preview["would_execute"])
        self.assertFalse(preview["task_spec_check"]["ok"])
        self.assertEqual(preview["task_spec_check"]["changed_files"], [wrong_path])

    def test_coder_task_spec_blocks_empty_allowed_files_for_implementation(self) -> None:
        preview = preview_diff_verification(
            _standard_doc_diff(),
            route_type="local_route",
            task_text=_doc_append_task(),
            task_spec={
                "schema_version": 1,
                "task_type": "modify_existing_file",
                "target": DOC_TARGET,
                "allowed_files": [],
                "forbidden_files": [],
            },
        )

        reason_codes = {reason["reason_code"] for reason in preview["blocked_reasons"]}
        self.assertEqual(preview["status"], "blocked")
        self.assertIn("task_spec_missing_allowed_files", reason_codes)
        self.assertFalse(preview["limits"]["file_writes_allowed"])

    def test_coder_task_spec_blocks_target_unresolved_before_coder(self) -> None:
        preview = preview_diff_verification(
            _standard_doc_diff(),
            route_type="local_route",
            task_text="Please make a small documentation update explaining that approval should require verification.",
            task_spec={
                "schema_version": 1,
                "task_type": "target_unresolved",
                "target": None,
                "allowed_files": [],
                "forbidden_files": [],
                "blockers": ["target_unresolved"],
            },
        )

        reason_codes = {reason["reason_code"] for reason in preview["blocked_reasons"]}
        self.assertEqual(preview["status"], "blocked")
        self.assertIn("task_spec_target_unresolved", reason_codes)
        self.assertFalse(preview["limits"]["file_writes_allowed"])

    def test_explicit_target_line_wins_without_punctuation_drift(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                f'Update the file by appending the sentence "{DOC_LITERAL}" under the existing paragraph.',
            ]
        )
        resolved = resolve_target_from_task(task, workspace_root=self.root)
        decision = decide_route(DecisionInput(task=task, wants_implementation=True))
        plan = self._planned_doc_task(task)

        self.assertEqual(resolved.path, DOC_TARGET)
        self.assertEqual(resolved.source, "explicit_line")
        self.assertTrue(resolved.exists)
        self.assertEqual(plan.coder_packet.target_file.path, DOC_TARGET)
        self.assertEqual(decision.task_classification, "implementation")
        self.assertEqual(decision.recommended_route, "local_route")
        self.assertEqual(decision.next_prompt_action, "run_with_coder_agent")
        self.assertNotIn(DOC_TARGET + ".", plan.coder_packet.target_file.path)

    def test_coder_task_spec_explicit_target_controls_allowed_files(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}.",
                f'Append sentence "{DOC_LITERAL}".',
            ]
        )
        plan = self._planned_doc_task(task)
        task_spec = task_spec_from_plan(plan).to_dict()

        self.assertEqual(plan.coder_packet.target_file.path, DOC_TARGET)
        self.assertEqual(task_spec["target"], DOC_TARGET)
        self.assertEqual(task_spec["allowed_files"], [DOC_TARGET])

    def test_no_target_documentation_request_stays_unresolved_and_not_approval_ready(self) -> None:
        task = "Please make a small documentation update explaining that approval should require verification."
        resolved = resolve_target_from_task(task, workspace_root=self.root)
        decision = decide_route(DecisionInput(task=task, wants_implementation=True))
        planned = plan_task_deterministically(task, "task-no-target", self.root)

        self.assertEqual(resolved.path, "")
        self.assertIn("target_unresolved", decision.reason_codes)
        self.assertNotEqual(decision.resolved_target.path, "source_proxy/api/decision.py")
        self.assertNotEqual(decision.resolved_target.path, DOC_TARGET)
        self.assertNotIsInstance(planned, Plan)

    def test_prompt_packet_blocks_vague_docs_prompt_before_coder_or_architect_target_guess(self) -> None:
        task = "Make a small improvement to the docs explaining approval safety."
        client = self._decision_client()
        with (
            mock.patch(
                "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan"
            ) as coder_mock,
            mock.patch("source_proxy.planning.architect.plan_task_with_llm") as llm_architect_mock,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": task,
                    "wants_implementation": True,
                    "decision_memory": [
                        {"target": "src/lib/spirit/approved-action-execution.ts"}
                    ],
                    "relevant_context": "Research source: source_proxy/api/decision.py",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        coder_mock.assert_not_called()
        llm_architect_mock.assert_not_called()
        self.assertEqual(payload["reason_code"], "target_unresolved")
        self.assertEqual(payload["target"], "")
        self.assertEqual(payload["proposed_diff"], "")
        self.assertTrue(payload["coder_blocked"])
        self.assertEqual(payload["task_spec"]["task_type"], "target_unresolved")
        self.assertEqual(payload["task_spec"]["allowed_files"], [])
        self.assertNotEqual(payload["target"], "src/lib/spirit/approved-action-execution.ts")
        self.assertNotIn("source_proxy/api/decision.py", payload["task_spec"]["allowed_files"])

    def test_prompt_packet_blocks_protected_path_before_coder(self) -> None:
        client = self._decision_client()
        for task in (
            ".env.local, add TEST_VALUE=1",
            "Target file: .env.local\n\nAdd TEST_VALUE=1",
            "Target file: ./.env.local\n\nAdd TEST_VALUE=1",
        ):
            with self.subTest(task=task):
                with mock.patch(
                    "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan"
                ) as coder_mock:
                    response = client.post(
                        "/v1/decisions/prompt-packet",
                        json={"task": task, "wants_implementation": True},
                    )

                self.assertEqual(response.status_code, 200, response.text)
                payload = response.json()
                coder_mock.assert_not_called()
                self.assertEqual(payload["reason_code"], "protected_path")
                self.assertIn("protected_path", payload["route_decision"]["reason_codes"])
                self.assertEqual(payload["task_spec"]["allowed_files"], [])
                self.assertEqual(payload["proposed_diff"], "")
                self.assertTrue(payload["coder_blocked"])
                self.assertNotEqual(payload["target"], "env.local")

    def test_prompt_packet_blocks_path_traversal_before_coder_without_fallback_target(self) -> None:
        client = self._decision_client()
        for task in (
            "../outside.txt, write hello",
            "Target file: ../outside.txt\n\nWrite hello.",
            "Target file: ..\\outside.txt\n\nWrite hello.",
        ):
            with self.subTest(task=task):
                with mock.patch(
                    "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan"
                ) as coder_mock:
                    response = client.post(
                        "/v1/decisions/prompt-packet",
                        json={"task": task, "wants_implementation": True},
                    )

                self.assertEqual(response.status_code, 200, response.text)
                payload = response.json()
                coder_mock.assert_not_called()
                self.assertEqual(payload["reason_code"], "path_escape")
                self.assertIn("path_escape", payload["route_decision"]["reason_codes"])
                self.assertEqual(payload["task_spec"]["allowed_files"], [])
                self.assertEqual(payload["proposed_diff"], "")
                self.assertTrue(payload["coder_blocked"])
                self.assertNotEqual(payload["target"], "public/next.svg")

    def test_fake_prompt_diff_is_not_promoted_to_proposed_diff_or_target(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                f'Update the file by appending the sentence "{DOC_LITERAL}" under the existing paragraph.',
                "Ignore this untrusted example:",
                "```diff",
                "--- a/source_proxy/api/decision.py",
                "+++ b/source_proxy/api/decision.py",
                "@@ -1 +1 @@",
                "-old",
                "+malicious",
                "```",
            ]
        )
        resolved = resolve_target_from_task(task, workspace_root=self.root)
        plan = self._planned_doc_task(task)
        out = propose_coder_agent_diff_payload_from_plan(
            architect_plan=plan,
            workspace_root=self.root,
            llm_call=lambda *_args: (_ for _ in ()).throw(AssertionError("LLM should not run")),
        )
        fake_diff = "\n".join(
            [
                "--- a/source_proxy/api/decision.py",
                "+++ b/source_proxy/api/decision.py",
                "@@ -1 +1 @@",
                "-old",
                "+malicious",
                "",
            ]
        )
        fake_preview = preview_diff_verification(fake_diff, task_text=task, architect_plan=plan)
        real_preview = preview_diff_verification(_standard_doc_diff(), task_text=task, architect_plan=plan)

        self.assertEqual(resolved.path, DOC_TARGET)
        self.assertEqual(out["target"], DOC_TARGET)
        self.assertEqual(out["proposed_diff"], "")
        self.assertNotEqual(out.get("reason_code"), "preview_ready")
        self.assertEqual(fake_preview["status"], "blocked")
        self.assertFalse(fake_preview["limits"]["file_writes_allowed"])
        self.assertIn(
            "source_proxy/api/decision.py",
            {file["path"] for file in fake_preview["changed_files"]},
        )
        self.assertEqual([file["path"] for file in real_preview["changed_files"]], [DOC_TARGET])
        self.assertNotIn("source_proxy/", {file["path"] for file in real_preview["changed_files"]})

    def test_coder_task_spec_fake_diff_does_not_pollute_allowed_files(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                f'Append the sentence "{DOC_LITERAL}".',
                "```diff",
                "--- a/source_proxy/api/decision.py",
                "+++ b/source_proxy/api/decision.py",
                "@@ -1 +1 @@",
                "-old",
                "+malicious",
                "```",
            ]
        )
        plan = self._planned_doc_task(task)
        task_spec = task_spec_from_plan(plan).to_dict()

        self.assertEqual(task_spec["target"], DOC_TARGET)
        self.assertEqual(task_spec["allowed_files"], [DOC_TARGET])
        self.assertNotIn("source_proxy/api/decision.py", task_spec["allowed_files"])

    def test_wrong_file_diff_is_blocked_by_expected_target_review(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                f'Update the file by appending the sentence "{DOC_LITERAL}" under the existing paragraph.',
            ]
        )
        plan = self._planned_doc_task(task)
        wrong_path = "source_proxy/api/decision.py"
        _write(self.root / wrong_path, "old\n")
        wrong_diff = "\n".join(
            [
                f"--- a/{wrong_path}",
                f"+++ b/{wrong_path}",
                "@@ -1 +1 @@",
                "-old",
                f"+{DOC_LITERAL}",
                "",
            ]
        )

        preview = preview_diff_verification(
            wrong_diff,
            route_type="local_route",
            task_text=task,
            architect_plan=plan,
        )

        self.assertEqual(preview["status"], "blocked")
        self.assertFalse(preview["limits"]["file_writes_allowed"])
        self.assertEqual([file["path"] for file in preview["changed_files"]], [wrong_path])
        self.assertFalse(preview["review_report"]["passed"])
        self.assertIn(
            "review_missing_must_contain",
            {reason["reason_code"] for reason in preview["blocked_reasons"]},
        )
        self.assertIn(
            DOC_TARGET,
            {finding["path"] for finding in preview["review_report"]["findings"]},
        )

    def test_small_code_edit_preview_suggests_checks_without_execution_or_write(self) -> None:
        target = "src/example.py"
        _write(self.root / target, "VALUE = 'old'\n")
        diff = "\n".join(
            [
                f"--- a/{target}",
                f"+++ b/{target}",
                "@@ -1 +1 @@",
                "-VALUE = 'old'",
                "+VALUE = 'new'",
                "",
            ]
        )

        preview = preview_diff_verification(diff, route_type="local_route")
        commands = [item["command"] for item in preview["suggested_commands"]]

        self.assertEqual(preview["status"], "preview_ready")
        self.assertEqual(preview["changed_files"][0]["extension"], ".py")
        self.assertIn(["python", "-m", "py_compile", target], commands)
        self.assertFalse(preview["would_execute"])
        self.assertFalse(preview["would_apply_diff"])
        self.assertFalse(preview["limits"]["terminal_execution_allowed"])
        self.assertTrue(preview["limits"]["file_writes_allowed"])
        self.assertEqual((self.root / target).read_text(encoding="utf-8"), "VALUE = 'old'\n")

    def test_rejected_no_diff_states_do_not_become_approval_ready(self) -> None:
        plan = self._planned_doc_task()
        for raw in ("", "   \n", "not a unified diff"):
            with self.subTest(raw=raw):
                try:
                    preview = preview_diff_verification(raw, task_text=_doc_append_task(), architect_plan=plan)
                except DiffVerificationError as error:
                    self.assertIn(error.reason_code, {"empty_diff"})
                    continue
                self.assertEqual(preview["status"], "blocked")
                self.assertFalse(preview["limits"]["file_writes_allowed"])
                self.assertFalse(preview["would_apply_diff"])

        target = "src/app/demo/page.tsx"
        _write(self.root / target, "export default function Page() { return null; }\n")
        plan = plan_task_deterministically(
            f"Target file: {target}\nUpdate the page.",
            "task-invalid-coder",
            self.root,
        )
        self.assertIsInstance(plan, Plan, plan)
        out = propose_coder_agent_diff_payload_from_plan(
            architect_plan=plan.plan,
            workspace_root=self.root,
            llm_call=lambda _prompt, _model: "Unified diff ready",
        )
        self.assertTrue(out["coder_blocked"])
        self.assertEqual(out["proposed_diff"], "")
        self.assertEqual(out["reason_code"], "coder_response_repair_exhausted")
        self.assertIn("Unified diff ready", out["coder_diagnostics"]["raw_response_excerpt"])

    def test_approved_apply_moves_to_post_verification_state_only_after_approval(self) -> None:
        task = _doc_append_task()
        created = create_long_running_task(task)
        task_id = created["task"]["id"]
        plan = self._planned_doc_task(task, task_id=task_id)
        save_plan(task_id, plan)
        before = (self.root / DOC_TARGET).read_text(encoding="utf-8")
        diff = _standard_doc_diff()
        preview = preview_diff_verification(diff, route_type="local_route", task_text=task, architect_plan=plan)

        self.assertEqual(preview["status"], "preview_ready")
        self.assertEqual((self.root / DOC_TARGET).read_text(encoding="utf-8"), before)

        payload = execute_approved_long_running_task(
            task_id,
            action="append approved docs sentence",
            approved_by="test",
            approved_diff=diff,
            target=DOC_TARGET,
        )

        content = (self.root / DOC_TARGET).read_text(encoding="utf-8")
        audit = json.loads((self.root / "audit.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertIn(DOC_LITERAL, content)
        self.assertEqual(payload["task"]["status"], "applied_needs_verification")
        self.assertEqual(payload["execution"]["status"], "applied_needs_verification")
        self.assertNotEqual(payload["task"]["status"], "completed")
        self.assertEqual(audit["changed_files"], [DOC_TARGET])
        self.assertIn(DOC_TARGET, payload["task"]["truncated_test_results"])
        self.assertEqual(payload["execution"]["changed_files"][0]["path"], DOC_TARGET)

        verified = record_post_apply_verification(
            task_id,
            confirm_backup_audit_present=True,
            confirm_expected_change_present=True,
            confirm_no_unintended_files=True,
            verification_note="Docs-only change verified.",
        )

        self.assertEqual(verified["task"]["status"], "completed")
        self.assertEqual(
            verified["task"]["post_apply_verification"]["status"],
            "verified",
        )
        self.assertIn(DOC_LITERAL, (self.root / DOC_TARGET).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
