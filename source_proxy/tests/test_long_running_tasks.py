from __future__ import annotations

import os
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.long_running_tasks import router as long_running_tasks_router
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
from source_proxy.tasks.long_running import (
    advance_long_running_task,
    create_long_running_task,
    execute_approved_long_running_task,
    get_long_running_task,
    LongRunningTaskError,
    record_post_apply_verification,
    reject_long_running_task_plan,
    reset_long_running_tasks,
    update_long_running_task,
)


def _manual_plan(task_id: str) -> ArchitectPlan:
    return ArchitectPlan(
        plan_id="plan-api-test",
        task_id=task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at="2026-05-13T00:00:00Z",
        source_task="Test plan API",
        bundle_snapshot=BundleSnapshot(
            bundle_path="/tmp/repomix-output.xml",
            bundle_sha256="0" * 64,
            workspace_root="/tmp",
            generated_at="2026-05-13T00:00:00Z",
        ),
        classification=TaskClassification(
            task_class="implement",
            visual_change=False,
            designer_required=False,
            estimated_complexity="trivial",
        ),
        coder_packet=CoderPacket(
            target_file=TargetFile("src/app/page.tsx", False, None),
            operation="create",
            acceptance_criteria=[],
            constraints=ContentConstraints([], [], [], [], None, None),
            context_slices=[],
            forbidden_paths=[],
            style_directives=[],
        ),
        verification_plan=VerificationPlan(
            required_checks=[],
            designer_review_required=False,
            architect_review_required=False,
        ),
        budget=PlanBudget(3, 120, True),
    )


class LongRunningTaskTrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_database_path = os.environ.get(
            "SOURCE_PROXY_LONG_RUNNING_TASKS_DB"
        )
        self._previous_spirit_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        self._previous_audit_path = os.environ.get("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG")
        self._tempdir = tempfile.TemporaryDirectory()
        os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = os.path.join(
            self._tempdir.name,
            "tasks.sqlite3",
        )
        os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = os.path.join(
            self._tempdir.name,
            "approved_actions.audit.jsonl",
        )
        os.environ["SPIRIT_PROJECT_PATH"] = self._tempdir.name
        os.makedirs(os.path.join(self._tempdir.name, "source_proxy"), exist_ok=True)
        with open(
            os.path.join(self._tempdir.name, "source_proxy", "main.py"),
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write("old\n")
        reset_long_running_tasks()

    def tearDown(self) -> None:
        reset_long_running_tasks()
        if self._previous_database_path is None:
            os.environ.pop("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", None)
        else:
            os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = (
                self._previous_database_path
            )
        if self._previous_spirit_project_path is None:
            os.environ.pop("SPIRIT_PROJECT_PATH", None)
        else:
            os.environ["SPIRIT_PROJECT_PATH"] = self._previous_spirit_project_path
        if self._previous_audit_path is None:
            os.environ.pop("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG", None)
        else:
            os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = (
                self._previous_audit_path
            )
        self._tempdir.cleanup()

    def test_create_and_poll_task_without_execution(self) -> None:
        created = create_long_running_task("Review a large patch")
        task_id = created["task"]["id"]

        first_poll = get_long_running_task(task_id)

        self.assertEqual(created["tool"], "long_running_task_tracker")
        self.assertEqual(created["task"]["status"], "queued")
        self.assertEqual(first_poll["task"]["status"], "running")
        self.assertFalse(first_poll["task"]["would_execute"])
        self.assertFalse(first_poll["task"]["writes_allowed"])

    def test_coder_blocked_before_diff_does_not_report_nearly_complete_progress(self) -> None:
        created = create_long_running_task("Target file: source_proxy/main.py\nUpdate docs.")
        task_id = created["task"]["id"]

        update_long_running_task(
            task_id,
            status="blocked",
            current_agent_role="coder",
            truncated_test_results="coder_status=blocked; reason_code=coder_sync_timeout",
        )
        payload = get_long_running_task(task_id)

        self.assertEqual(payload["task"]["status"], "blocked")
        self.assertEqual(payload["task"]["current_agent_role"], "coder")
        self.assertLessEqual(payload["task"]["progress"], 50)

    def test_task_completes_after_multiple_polls(self) -> None:
        created = create_long_running_task("Prepare verification plan")
        task_id = created["task"]["id"]

        for _ in range(4):
            payload = get_long_running_task(task_id)

        self.assertEqual(payload["task"]["status"], "completed")
        self.assertEqual(payload["task"]["progress"], 100)

    def test_router_can_cancel_task(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = client.post(
            "/v1/tasks/long-running",
            json={"description": "Run a staged verification pass"},
        )
        task_id = created.json()["task"]["id"]
        cancelled = client.post(f"/v1/tasks/long-running/{task_id}/cancel")

        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["task"]["status"], "cancelled")

    def test_router_returns_saved_architect_plan(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = client.post(
            "/v1/tasks/long-running",
            json={"description": "Plan API"},
        )
        task_id = created.json()["task"]["id"]
        missing = client.get(f"/v1/tasks/long-running/{task_id}/plan")
        save_plan(task_id, _manual_plan(task_id))
        found = client.get(f"/v1/tasks/long-running/{task_id}/plan")

        self.assertEqual(missing.status_code, 200)
        self.assertEqual(missing.json().get("plan_available"), False)
        self.assertEqual(missing.json().get("reason_code"), "plan_not_ready")
        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.json()["plan_id"], "plan-api-test")
        self.assertEqual(
            found.json()["coder_packet"]["target_file"]["path"],
            "src/app/page.tsx",
        )

    def test_plan_rejection_is_audited_and_regenerates(self) -> None:
        audit_path = os.path.join(self._tempdir.name, "audit.jsonl")
        previous_audit_path = os.environ.get("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG")
        os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = audit_path
        try:
            created = create_long_running_task(
                "Target file: source_proxy/main.py\nAdd a comment"
            )
            task_id = created["task"]["id"]
            save_plan(task_id, _manual_plan(task_id))

            rejected = reject_long_running_task_plan(
                task_id,
                reason_code="other",
                details="manual test rejection",
            )

            self.assertEqual(rejected["rejection"]["reason_code"], "other")
            self.assertEqual(rejected["task"]["architect_status"], "planned")
            self.assertEqual(rejected["task"]["current_agent_role"], "coder")
            with open(audit_path, encoding="utf-8") as handle:
                audit = json.loads(handle.readline())
            self.assertEqual(audit["event"], "plan_rejected")
            self.assertEqual(audit["reason_code"], "other")
            self.assertEqual(audit["task_id"], task_id)
        finally:
            if previous_audit_path is None:
                os.environ.pop("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG", None)
            else:
                os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = previous_audit_path

    def test_task_persists_blackboard_fields_to_sqlite(self) -> None:
        created = create_long_running_task("Track swarm state")
        task_id = created["task"]["id"]

        update_long_running_task(
            task_id,
            ast_snapshot={"files": ["source_proxy/tasks/long_running.py"]},
            open_diffs=[{"path": "a.py", "status": "pending"}],
            truncated_test_results="ok",
            current_agent_role="coder",
        )

        with closing(
            sqlite3.connect(os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"])
        ) as db:
            columns = {
                row[1]
                for row in db.execute("PRAGMA table_info(long_running_tasks)")
            }
            row = db.execute(
                """
                SELECT
                    ast_snapshot_json,
                    open_diffs_json,
                    truncated_test_results,
                    current_agent_role,
                    cycle_count
                FROM long_running_tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()

        self.assertIn("ast_snapshot_json", columns)
        self.assertIn("open_diffs_json", columns)
        self.assertIn("truncated_test_results", columns)
        self.assertIn("current_agent_role", columns)
        self.assertIn("source_proxy/tasks/long_running.py", row[0])
        self.assertIn("a.py", row[1])
        self.assertEqual(row[2], "ok")
        self.assertEqual(row[3], "coder")
        self.assertEqual(row[4], 0)

    def test_pre_save_hook_truncates_logs_and_purges_verified_diffs(self) -> None:
        created = create_long_running_task("Trim debugger output")
        task_id = created["task"]["id"]
        stderr_log = "x" * 20_000

        updated = update_long_running_task(
            task_id,
            open_diffs=[
                {"path": "verified.py", "verified": True},
                {"path": "pending.py", "status": "pending"},
            ],
            truncated_test_results=stderr_log,
        )

        task = updated["task"]
        self.assertEqual(len(task["truncated_test_results"]), 1500)
        self.assertEqual(task["truncated_test_results"], stderr_log[-1500:])
        self.assertEqual(
            task["open_diffs"],
            [{"path": "pending.py", "status": "pending"}],
        )

    def test_swarm_handoff_runs_architect_to_coder_to_debugger_to_complete(self) -> None:
        created = create_long_running_task(
            "Target file: source_proxy/main.py\nPatch a small Python file"
        )
        task_id = created["task"]["id"]

        architect = advance_long_running_task(task_id)
        self.assertEqual(architect["task"]["current_agent_role"], "coder")
        self.assertEqual(architect["task"]["status"], "running")
        self.assertIsNotNone(architect["task"]["ast_snapshot"])

        diff = "\n".join(
            [
                "diff --git a/source_proxy/main.py b/source_proxy/main.py",
                "--- a/source_proxy/main.py",
                "+++ b/source_proxy/main.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
                "",
            ]
        )
        coder = advance_long_running_task(task_id, proposed_diff=diff)
        self.assertEqual(coder["task"]["current_agent_role"], "debugger")
        self.assertEqual(coder["task"]["open_diffs"][0]["status"], "pending_verification")

        debugger = advance_long_running_task(
            task_id,
            sandbox_result={"returncode": 0, "stdout": "ok\n", "stderr": ""},
        )
        self.assertEqual(debugger["task"]["status"], "completed")
        self.assertEqual(debugger["task"]["cycle_count"], 1)
        self.assertEqual(debugger["task"]["open_diffs"], [])
        self.assertIn("ok", debugger["task"]["truncated_test_results"])

    def test_swarm_debugger_failure_returns_to_coder_with_truncated_output(self) -> None:
        created = create_long_running_task(
            "Target file: source_proxy/main.py\nRetry a failing patch"
        )
        task_id = created["task"]["id"]
        advance_long_running_task(task_id)
        diff = "\n".join(
            [
                "diff --git a/source_proxy/main.py b/source_proxy/main.py",
                "--- a/source_proxy/main.py",
                "+++ b/source_proxy/main.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
                "",
            ]
        )
        advance_long_running_task(task_id, proposed_diff=diff)

        failed = advance_long_running_task(
            task_id,
            sandbox_result={
                "returncode": 1,
                "stdout": "",
                "stderr": "x" * 20_000,
            },
        )

        self.assertEqual(failed["task"]["current_agent_role"], "coder")
        self.assertEqual(failed["task"]["status"], "running")
        self.assertEqual(failed["task"]["cycle_count"], 1)
        self.assertEqual(len(failed["task"]["truncated_test_results"]), 1500)
        self.assertEqual(failed["task"]["open_diffs"][0]["status"], "needs_revision")

    def test_reviewer_blocked_diff_sets_terminal_blocked_status(self) -> None:
        created = create_long_running_task(
            "Target file: source_proxy/main.py\nAdd the approved literal"
        )
        task_id = created["task"]["id"]
        save_plan(
            task_id,
            ArchitectPlan(
                plan_id="plan-review-blocked",
                task_id=task_id,
                schema_version=PLAN_SCHEMA_VERSION,
                created_at="2026-05-14T00:00:00Z",
                source_task="Target file: source_proxy/main.py\nAdd the approved literal",
                bundle_snapshot=BundleSnapshot(
                    bundle_path="/tmp/repomix-output.xml",
                    bundle_sha256="0" * 64,
                    workspace_root=self._tempdir.name,
                    generated_at="2026-05-14T00:00:00Z",
                ),
                classification=TaskClassification(
                    task_class="implement",
                    visual_change=False,
                    designer_required=False,
                    estimated_complexity="trivial",
                ),
                coder_packet=CoderPacket(
                    target_file=TargetFile("source_proxy/main.py", True, "a" * 64),
                    operation="edit",
                    acceptance_criteria=[
                        AcceptanceCriterion(
                            "literal-required",
                            'Output must contain "RequiredLiteral".',
                            "literal",
                        )
                    ],
                    constraints=ContentConstraints(
                        ["RequiredLiteral"], [], [], [], None, None
                    ),
                    context_slices=[
                        ContextSlice(
                            path="source_proxy/main.py",
                            kind="target",
                            sha256="a" * 64,
                            content="old\n",
                            line_range=(1, 1),
                        )
                    ],
                    forbidden_paths=[],
                    style_directives=[],
                ),
                verification_plan=VerificationPlan(
                    required_checks=[],
                    designer_review_required=False,
                    architect_review_required=False,
                ),
                budget=PlanBudget(3, 120, True),
            ),
        )
        update_long_running_task(
            task_id,
            status="running",
            current_agent_role="coder",
            architect_status="planned",
        )
        diff = "\n".join(
            [
                "diff --git a/source_proxy/main.py b/source_proxy/main.py",
                "--- a/source_proxy/main.py",
                "+++ b/source_proxy/main.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
                "",
            ]
        )

        payload = advance_long_running_task(task_id, proposed_diff=diff)

        self.assertEqual(payload["task"]["status"], "blocked_by_review")
        self.assertNotEqual(payload["task"]["status"], "running")
        self.assertEqual(payload["task"]["current_agent_role"], "coder")
        self.assertEqual(payload["task"]["open_diffs"][0]["status"], "blocked_by_review")
        self.assertFalse(payload["task"]["writes_allowed"])
        self.assertFalse(payload["task"]["would_execute"])

        polled = get_long_running_task(task_id)
        self.assertEqual(polled["task"]["status"], "blocked_by_review")

    def test_router_can_advance_swarm_task(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = client.post(
            "/v1/tasks/long-running",
            json={"description": "Target file: source_proxy/main.py\nRun handoff"},
        )
        task_id = created.json()["task"]["id"]
        advanced = client.post(f"/v1/tasks/long-running/{task_id}/advance", json={})

        self.assertEqual(advanced.status_code, 200)
        self.assertEqual(advanced.json()["task"]["current_agent_role"], "coder")
        self.assertEqual(advanced.json()["task"]["architect_status"], "planned")

    def test_architect_timeout_uses_deterministic_markdown_append_fallback(self) -> None:
        docs = Path(self._tempdir.name) / "docs"
        docs.mkdir(parents=True)
        (docs / "phase-8-manual-check.md").write_text(
            "# Phase 8 Manual Check\n\nExisting paragraph.\n",
            encoding="utf-8",
        )
        created = create_long_running_task(
            'Target file: docs/phase-8-manual-check.md\n\n'
            'Append one short sentence under the existing paragraph:\n'
            '"Manual verification should clearly report whether a diff was produced."'
        )
        task_id = created["task"]["id"]

        from source_proxy.planning.architect import ArchitectLLMError, FallthroughToLLM

        with (
            mock.patch(
                "source_proxy.planning.architect.plan_task_deterministically",
                return_value=FallthroughToLLM("forced_llm_for_test"),
            ),
            mock.patch(
                "source_proxy.planning.architect.plan_task_with_llm",
                side_effect=ArchitectLLMError(
                    "architect_llm_timeout",
                    "LLM Architect timed out after 20 seconds.",
                ),
            ),
        ):
            advanced = advance_long_running_task(task_id)

        self.assertEqual(advanced["task"]["architect_status"], "planned")
        self.assertEqual(
            advanced["task"]["architect_reason"],
            "deterministic_markdown_append_fallback",
        )
        self.assertEqual(advanced["task"]["current_agent_role"], "coder")

    def test_architect_blocks_vague_write_without_llm_target_guess(self) -> None:
        created = create_long_running_task(
            "Make a small improvement to the docs explaining approval safety."
        )
        task_id = created["task"]["id"]

        with mock.patch("source_proxy.planning.architect.plan_task_with_llm") as llm_mock:
            advanced = advance_long_running_task(task_id)

        llm_mock.assert_not_called()
        self.assertEqual(advanced["task"]["status"], "blocked")
        self.assertEqual(advanced["task"]["architect_status"], "blocked")
        self.assertEqual(advanced["task"]["architect_reason"], "target_unresolved")
        self.assertFalse(advanced["task"]["writes_allowed"])

    def test_approved_execution_applies_verified_diff_and_audits(self) -> None:
        previous_cwd = os.getcwd()
        audit_path = os.path.join(self._tempdir.name, "audit.jsonl")
        previous_audit_path = os.environ.get("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG")
        os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = audit_path
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export default function Demo() { return null; }\n")

            created = create_long_running_task("Apply approved demo diff")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export default function Demo() { return null; }",
                    "+export default function Demo() { return <main>Done</main>; }",
                    "",
                ]
            )

            payload = execute_approved_long_running_task(
                task_id,
                action="implement proposed file change",
                approved_by="test",
                approved_diff=diff,
                target="src/app/demo/page.tsx",
            )

            with open("src/app/demo/page.tsx", encoding="utf-8") as handle:
                content = handle.read()
            with open(audit_path, encoding="utf-8") as handle:
                audit_line = handle.readline()

            self.assertIn("<main>Done</main>", content)
            self.assertTrue(payload["execution"]["ok"])
            self.assertEqual(payload["task"]["status"], "applied_needs_verification")
            self.assertEqual(payload["execution"]["status"], "applied_needs_verification")
            self.assertEqual(
                payload["task"]["post_apply_verification"]["status"],
                "verification_ready",
            )
            self.assertTrue(payload["task"]["writes_allowed"])
            self.assertIn("src/app/demo/page.tsx", audit_line)
        finally:
            os.chdir(previous_cwd)
            if previous_audit_path is None:
                os.environ.pop("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG", None)
            else:
                os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = (
                    previous_audit_path
                )

    def test_router_executes_approved_diff(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            created = client.post(
                "/v1/tasks/long-running",
                json={"description": "Apply approved route diff"},
            )
            task_id = created.json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )

            response = client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "modify file",
                    "approved": True,
                    "approved_diff": diff,
                    "target": "src/app/demo/page.tsx",
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["execution"]["ok"])
            self.assertEqual(
                response.json()["task"]["status"],
                "applied_needs_verification",
            )
            with open("src/app/demo/page.tsx", encoding="utf-8") as handle:
                self.assertIn("'new'", handle.read())
        finally:
            os.chdir(previous_cwd)

    def test_post_apply_verification_failure_prevents_completed(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            created = create_long_running_task("Apply approved route diff")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            execute_approved_long_running_task(
                task_id,
                action="modify file",
                approved_diff=diff,
                target="src/app/demo/page.tsx",
            )

            failed = record_post_apply_verification(
                task_id,
                checks=[
                    {
                        "id": "typecheck",
                        "status": "failed",
                        "summary": "TypeScript failed.",
                    }
                ],
            )

            self.assertEqual(failed["task"]["status"], "verification_failed")
            self.assertEqual(
                failed["task"]["post_apply_verification"]["status"],
                "verification_failed",
            )
            self.assertNotEqual(failed["task"]["status"], "completed")
        finally:
            os.chdir(previous_cwd)

    def test_docs_only_post_apply_verification_requires_explicit_confirmations(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/phase-2a.md", "w", encoding="utf-8") as handle:
                handle.write("# Phase 2A\n\nPending verification.\n")

            created = create_long_running_task("Append docs-only verification note")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/phase-2a.md b/docs/phase-2a.md",
                    "--- a/docs/phase-2a.md",
                    "+++ b/docs/phase-2a.md",
                    "@@ -1,3 +1,4 @@",
                    " # Phase 2A",
                    " ",
                    " Pending verification.",
                    "+Docs-only change verified.",
                    "",
                ]
            )
            applied = execute_approved_long_running_task(
                task_id,
                action="append docs note",
                approved_diff=diff,
                target="docs/phase-2a.md",
            )

            self.assertEqual(applied["task"]["status"], "applied_needs_verification")
            self.assertTrue(applied["task"]["post_apply_verification"]["docs_only"])

            with self.assertRaises(LongRunningTaskError) as missing:
                record_post_apply_verification(task_id)
            self.assertEqual(
                missing.exception.reason_code,
                "missing_post_apply_confirmations",
            )

            completed = record_post_apply_verification(
                task_id,
                confirm_backup_audit_present=True,
                confirm_changed_files_reviewed=True,
                confirm_expected_change_present=True,
                confirm_no_unintended_files=True,
                verification_note="Docs-only change verified.",
            )
            verification = completed["task"]["post_apply_verification"]
            self.assertEqual(completed["task"]["status"], "completed")
            self.assertEqual(verification["status"], "verified")
            self.assertEqual(
                verification["verification_note"],
                "Docs-only change verified.",
            )
            self.assertTrue(
                verification["docs_only_confirmations"]["file_changed_as_expected"]
            )
            self.assertTrue(
                verification["docs_only_confirmations"]["backup_audit_present"]
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_verify_completes_docs_only_post_apply_verification(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/router-verify.md", "w", encoding="utf-8") as handle:
                handle.write("# Router Verify\n\nBefore.\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Append router verification docs note"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/router-verify.md b/docs/router-verify.md",
                    "--- a/docs/router-verify.md",
                    "+++ b/docs/router-verify.md",
                    "@@ -1,3 +1,4 @@",
                    " # Router Verify",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )
            client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "append docs note",
                    "approved": True,
                    "approved_diff": diff,
                    "target": "docs/router-verify.md",
                },
            )

            response = client.post(
                f"/v1/tasks/long-running/{task_id}/verify",
                json={
                    "confirm_backup_audit_present": True,
                    "confirm_changed_files_reviewed": True,
                    "confirm_expected_change_present": True,
                    "confirm_no_unintended_files": True,
                    "verification_note": "Docs-only change verified.",
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["task"]["status"], "completed")
            self.assertEqual(
                response.json()["task"]["post_apply_verification"]["status"],
                "verified",
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_verify_rejects_missing_docs_confirmations(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/missing-confirm.md", "w", encoding="utf-8") as handle:
                handle.write("# Missing Confirm\n\nBefore.\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Append docs note"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/missing-confirm.md b/docs/missing-confirm.md",
                    "--- a/docs/missing-confirm.md",
                    "+++ b/docs/missing-confirm.md",
                    "@@ -1,3 +1,4 @@",
                    " # Missing Confirm",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )
            client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "append docs note",
                    "approved": True,
                    "approved_diff": diff,
                    "target": "docs/missing-confirm.md",
                },
            )

            response = client.post(
                f"/v1/tasks/long-running/{task_id}/verify",
                json={
                    "confirm_expected_change_present": True,
                    "confirm_no_unintended_files": True,
                },
            )

            self.assertEqual(response.status_code, 422)
            self.assertEqual(
                response.json()["detail"]["reason_code"],
                "missing_post_apply_confirmations",
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_verify_rejects_unapplied_task(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)
        task_id = client.post(
            "/v1/tasks/long-running",
            json={"description": "Task has not been applied"},
        ).json()["task"]["id"]

        response = client.post(
            f"/v1/tasks/long-running/{task_id}/verify",
            json={
                "confirm_backup_audit_present": True,
                "confirm_expected_change_present": True,
                "confirm_no_unintended_files": True,
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["detail"]["reason_code"],
            "invalid_post_apply_verification_state",
        )

    def test_router_code_verify_rejects_unapplied_task(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)
        task_id = client.post(
            "/v1/tasks/long-running",
            json={"description": "Task has not been applied"},
        ).json()["task"]["id"]

        response = client.post(
            f"/v1/tasks/long-running/{task_id}/verify",
            json={"run_code_verification": True},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["detail"]["reason_code"],
            "invalid_post_apply_verification_state",
        )

    def test_router_verify_runs_allowlisted_code_verification(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/lib/coding/__tests__", exist_ok=True)
            with open("package.json", "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "scripts": {
                            "test:coding-frontend-regression": "vitest run coding",
                        }
                    },
                    handle,
                )
            with open(
                "src/lib/coding/__tests__/unified-diff-paths.test.ts",
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("export const value = 'old';\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Update coding frontend test"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/lib/coding/__tests__/unified-diff-paths.test.ts b/src/lib/coding/__tests__/unified-diff-paths.test.ts",
                    "--- a/src/lib/coding/__tests__/unified-diff-paths.test.ts",
                    "+++ b/src/lib/coding/__tests__/unified-diff-paths.test.ts",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            applied = client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "modify coding test",
                    "approved": True,
                    "approved_diff": diff,
                    "target": "src/lib/coding/__tests__/unified-diff-paths.test.ts",
                },
            )
            applied_verification = applied.json()["task"]["post_apply_verification"]
            self.assertEqual(applied_verification["status"], "verification_ready")
            self.assertEqual(
                [check["id"] for check in applied_verification["checks"]],
                ["coding_frontend_regression", "typescript_typecheck"],
            )
            self.assertTrue(
                all(check["status"] == "pending" for check in applied_verification["checks"])
            )

            completed_process = mock.Mock()
            completed_process.returncode = 0
            completed_process.stdout = "ok"
            completed_process.stderr = ""
            with mock.patch(
                "source_proxy.tasks.long_running.subprocess.run",
                return_value=completed_process,
            ) as run_mock:
                response = client.post(
                    f"/v1/tasks/long-running/{task_id}/verify",
                    json={"run_code_verification": True},
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["task"]["status"], "completed")
            verification = payload["task"]["post_apply_verification"]
            self.assertEqual(verification["status"], "verified")
            self.assertEqual(
                [check["id"] for check in verification["checks"]],
                ["coding_frontend_regression", "typescript_typecheck"],
            )
            self.assertEqual(
                [call.args[0] for call in run_mock.call_args_list],
                [
                    ["npm", "run", "test:coding-frontend-regression"],
                    ["npx", "tsc", "--noEmit", "-p", "tsconfig.json"],
                ],
            )
            self.assertTrue(
                all(check["status"] == "passed" for check in verification["checks"])
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_code_verify_failure_records_output_without_completion(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("package.json", "w", encoding="utf-8") as handle:
                json.dump({"scripts": {}}, handle)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Update route code"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "modify route",
                    "approved": True,
                    "approved_diff": diff,
                    "target": "src/app/demo/page.tsx",
                },
            )

            failed_process = mock.Mock()
            failed_process.returncode = 1
            failed_process.stdout = ""
            failed_process.stderr = "x" * 4100 + "TYPECHECK_FAILED_TAIL"
            with mock.patch(
                "source_proxy.tasks.long_running.subprocess.run",
                return_value=failed_process,
            ):
                response = client.post(
                    f"/v1/tasks/long-running/{task_id}/verify",
                    json={"run_code_verification": True},
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["task"]["status"], "verification_failed")
            self.assertNotEqual(payload["task"]["status"], "completed")
            verification = payload["task"]["post_apply_verification"]
            self.assertEqual(verification["status"], "verification_failed")
            failed_check = verification["checks"][0]
            self.assertEqual(failed_check["id"], "typescript_typecheck")
            self.assertEqual(failed_check["status"], "failed")
            self.assertLessEqual(len(failed_check["output_tail"]), 4000)
            self.assertIn("TYPECHECK_FAILED_TAIL", failed_check["output_tail"])
            with open("src/app/demo/page.tsx", encoding="utf-8") as handle:
                self.assertIn("'new'", handle.read())
        finally:
            os.chdir(previous_cwd)

    def test_router_code_verify_rejects_docs_only_task(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/code-verify-docs.md", "w", encoding="utf-8") as handle:
                handle.write("# Docs\n\nBefore.\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Append docs note"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/code-verify-docs.md b/docs/code-verify-docs.md",
                    "--- a/docs/code-verify-docs.md",
                    "+++ b/docs/code-verify-docs.md",
                    "@@ -1,3 +1,4 @@",
                    " # Docs",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )
            client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "append docs note",
                    "approved": True,
                    "approved_diff": diff,
                    "target": "docs/code-verify-docs.md",
                },
            )

            response = client.post(
                f"/v1/tasks/long-running/{task_id}/verify",
                json={"run_code_verification": True},
            )

            self.assertEqual(response.status_code, 422)
            self.assertEqual(
                response.json()["detail"]["reason_code"],
                "code_verification_not_applicable",
            )
        finally:
            os.chdir(previous_cwd)

    def test_unsupported_code_file_requires_manual_verification(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            with open("source_proxy/demo.py", "w", encoding="utf-8") as handle:
                handle.write("VALUE = 'old'\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Update Python file"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/source_proxy/demo.py b/source_proxy/demo.py",
                    "--- a/source_proxy/demo.py",
                    "+++ b/source_proxy/demo.py",
                    "@@ -1 +1 @@",
                    "-VALUE = 'old'",
                    "+VALUE = 'new'",
                    "",
                ]
            )
            applied = client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "modify python",
                    "approved": True,
                    "approved_diff": diff,
                    "target": "source_proxy/demo.py",
                },
            )

            self.assertEqual(applied.status_code, 200)
            verification = applied.json()["task"]["post_apply_verification"]
            self.assertEqual(verification["status"], "manual_verification_required")
            self.assertTrue(verification["unsupported_code_verification"])
            self.assertEqual(verification["unsupported_file_types"], [".py"])

            response = client.post(
                f"/v1/tasks/long-running/{task_id}/verify",
                json={"run_code_verification": True},
            )

            self.assertEqual(response.status_code, 422)
            self.assertEqual(
                response.json()["detail"]["reason_code"],
                "unsupported_code_verification_type",
            )
            self.assertEqual(
                get_long_running_task(task_id)["task"]["status"],
                "applied_needs_verification",
            )
        finally:
            os.chdir(previous_cwd)

    def test_docs_only_verification_preserves_audit_and_backup_metadata(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/preserve.md", "w", encoding="utf-8") as handle:
                handle.write("# Preserve\n\nBefore.\n")

            created = create_long_running_task("Append docs preserve note")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/preserve.md b/docs/preserve.md",
                    "--- a/docs/preserve.md",
                    "+++ b/docs/preserve.md",
                    "@@ -1,3 +1,4 @@",
                    " # Preserve",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )
            applied = execute_approved_long_running_task(
                task_id,
                action="append docs note",
                approved_diff=diff,
                target="docs/preserve.md",
            )
            before = json.loads(applied["task"]["truncated_test_results"])

            completed = record_post_apply_verification(
                task_id,
                confirm_backup_audit_present=True,
                confirm_expected_change_present=True,
                confirm_no_unintended_files=True,
            )
            after = json.loads(completed["task"]["truncated_test_results"])

            self.assertEqual(after["audit"], before["audit"])
            self.assertEqual(after["backup_root"], before["backup_root"])
            self.assertEqual(after["post_apply_verification"]["status"], "verified")
        finally:
            os.chdir(previous_cwd)

    def test_code_file_changed_task_is_not_completed_by_docs_checklist(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            created = create_long_running_task("Apply approved route diff")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            execute_approved_long_running_task(
                task_id,
                action="modify file",
                approved_diff=diff,
                target="src/app/demo/page.tsx",
            )

            with self.assertRaises(LongRunningTaskError) as blocked:
                record_post_apply_verification(
                    task_id,
                    confirm_backup_audit_present=True,
                    confirm_expected_change_present=True,
                    confirm_no_unintended_files=True,
                )

            self.assertEqual(
                blocked.exception.reason_code,
                "code_verification_not_implemented",
            )
            self.assertEqual(
                get_long_running_task(task_id)["task"]["status"],
                "applied_needs_verification",
            )
        finally:
            os.chdir(previous_cwd)

    def test_post_apply_verification_skip_requires_reason_to_complete(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            created = create_long_running_task("Apply approved route diff")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            execute_approved_long_running_task(
                task_id,
                action="modify file",
                approved_diff=diff,
                target="src/app/demo/page.tsx",
            )

            with self.assertRaises(LongRunningTaskError) as blocked:
                record_post_apply_verification(
                    task_id,
                    checks=[{"id": "typecheck", "status": "skipped"}],
                    manual_browser_check_done=False,
                )
            self.assertEqual(
                blocked.exception.reason_code,
                "code_verification_not_implemented",
            )

            completed = record_post_apply_verification(
                task_id,
                checks=[
                    {"id": "typecheck", "status": "skipped"},
                    {"id": "lint", "status": "skipped"},
                ],
                manual_browser_check_done=False,
                skip_reason="Verified externally in CI.",
            )
            self.assertEqual(completed["task"]["status"], "completed")
            self.assertEqual(
                completed["task"]["post_apply_verification"]["status"],
                "verified",
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_streams_swarm_telemetry_as_sse(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = client.post(
            "/v1/tasks/long-running",
            json={
                "description": "Target file: source_proxy/main.py\nStream handoff telemetry"
            },
        )
        task_id = created.json()["task"]["id"]
        client.post(f"/v1/tasks/long-running/{task_id}/advance", json={})

        with client.stream(
            "GET",
            f"/v1/tasks/long-running/{task_id}/stream?max_events=1",
        ) as response:
            body = response.read().decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        self.assertIn("event: task", body)
        self.assertIn("event: role_transition", body)
        data_line = next(line for line in body.splitlines() if line.startswith("data: "))
        payload = json.loads(data_line.removeprefix("data: "))
        self.assertEqual(payload["task"]["current_agent_role"], "coder")
        self.assertEqual(payload["task"]["cycle_count"], 0)
        role_transition_lines = [
            line.removeprefix("data: ")
            for index, line in enumerate(body.splitlines())
            if line.startswith("data: ")
            and index > 0
            and body.splitlines()[index - 1] == "event: role_transition"
        ]
        role_transition = json.loads(role_transition_lines[0])
        self.assertEqual(role_transition["from"], "architect")
        self.assertEqual(role_transition["to"], "coder")
        self.assertEqual(role_transition["reason"], "architect_plan_ready")

    def test_swarm_halts_at_cycle_five_when_sandbox_keeps_failing(self) -> None:
        created = create_long_running_task(
            "Target file: source_proxy/main.py\nStop an endless failing loop"
        )
        task_id = created["task"]["id"]
        advance_long_running_task(task_id)
        diff = "\n".join(
            [
                "diff --git a/source_proxy/main.py b/source_proxy/main.py",
                "--- a/source_proxy/main.py",
                "+++ b/source_proxy/main.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
                "",
            ]
        )

        payload = None
        for cycle in range(1, 6):
            advance_long_running_task(task_id, proposed_diff=diff)
            payload = advance_long_running_task(
                task_id,
                sandbox_result={
                    "returncode": 1,
                    "stdout": "",
                    "stderr": f"failure {cycle}",
                },
            )

        assert payload is not None
        task = payload["task"]
        self.assertEqual(task["cycle_count"], 5)
        self.assertEqual(task["status"], "failed_needs_human")
        self.assertEqual(task["current_agent_role"], "debugger")
        self.assertIn("safety cycle limit", task["next_action"])

        still_failed = advance_long_running_task(
            task_id,
            sandbox_result={"returncode": 0, "stdout": "late pass", "stderr": ""},
        )
        self.assertEqual(still_failed["task"]["cycle_count"], 5)
        self.assertEqual(still_failed["task"]["status"], "failed_needs_human")

    def test_coder_config_blocked_status_uses_terminal_progress_band(self) -> None:
        created = create_long_running_task("Coder config smoke")
        task_id = created["task"]["id"]
        update_long_running_task(task_id, status="coder_config_blocked", poll_count=3)
        payload = get_long_running_task(task_id)
        self.assertEqual(payload["task"]["status"], "coder_config_blocked")
        self.assertLessEqual(payload["task"]["progress"], 95)
        self.assertGreaterEqual(payload["task"]["progress"], 50)
        self.assertIn("SOURCE_PROXY_CODER_MODEL_ALIAS", payload["task"]["next_action"])


if __name__ == "__main__":
    unittest.main()
