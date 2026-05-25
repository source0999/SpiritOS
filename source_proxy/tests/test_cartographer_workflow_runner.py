from __future__ import annotations

from datetime import UTC, datetime, timedelta
import inspect
from pathlib import Path
import subprocess
import tempfile
import unittest

from source_proxy.cartographer import workflow_runner
from source_proxy.cartographer.approval_token_runtime import (
    APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
    APPROVAL_TOKEN_SCHEMA_VERSION,
)
from source_proxy.cartographer.workflow_event_ledger import (
    validate_workflow_event_ledger,
)
from source_proxy.cartographer.workflow_runner import (
    SAFE_DOCS_EVIDENCE_PREFIX,
    SAFE_DOCS_EVIDENCE_WORKFLOW_CLASS,
    build_safe_docs_evidence_workflow_status,
    execute_safe_docs_evidence_workflow,
)


class CartographerWorkflowRunnerTests(unittest.TestCase):
    def test_status_exposes_only_first_safe_docs_evidence_workflow(self) -> None:
        status = build_safe_docs_evidence_workflow_status()

        self.assertEqual(status["status"], "first-safe-docs-evidence-workflow-available")
        self.assertEqual(status["workflow_class"], SAFE_DOCS_EVIDENCE_WORKFLOW_CLASS)
        self.assertEqual(status["safe_docs_evidence_prefix"], SAFE_DOCS_EVIDENCE_PREFIX)
        self.assertTrue(status["verification_required"])
        self.assertFalse(status["queue_authority_granted"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["workflow_execution_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])

    def test_safe_docs_evidence_workflow_writes_exact_file_then_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = self._git_repo(Path(workspace))
            target_file = "docs/cartographer-live-evidence/plan-7-phase-2.md"
            result = execute_safe_docs_evidence_workflow(
                run_id="run-7-2",
                step_id="step-write-evidence",
                approval_payload=self._valid_payload(target_file=target_file),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file=target_file,
                content="# Plan 7 Phase 2 Evidence\n",
                consumption_context=self._context(target_file),
                workspace_root=workspace_root,
                current_head="abc123",
                verification_argv=["git", "diff", "--check"],
                now=self._now(),
            )

            written = workspace_root / target_file
            event_types = tuple(event.event_type for event in result.ledger_events)
            validation = validate_workflow_event_ledger(result.ledger_events)

            self.assertEqual(result.status, "completed")
            self.assertTrue(result.completed)
            self.assertFalse(result.blocked)
            self.assertEqual(result.reasons, ())
            self.assertEqual(written.read_text(encoding="utf-8"), "# Plan 7 Phase 2 Evidence\n")
            self.assertEqual(result.safe_write_result["status"], "written")
            self.assertEqual(result.verification_result["status"], "passed")
            self.assertEqual(result.verification_result["matched_command_id"], "git_diff_check")
            self.assertEqual(
                event_types,
                (
                    "workflow_created",
                    "task_selected",
                    "step_started",
                    "step_completed",
                    "workflow_verified",
                    "workflow_closed_out",
                ),
            )
            self.assertTrue(validation.valid)
            self.assertEqual(
                result.ledger_events[-1].receipt_path,
                "docs/cartographer-live-receipts/run-7-2-closeout.md",
            )
            self.assertFalse(result.workflow_execution_authority_granted)
            self.assertFalse(result.queue_authority_granted)
            self.assertFalse(result.command_authority_granted)
            self.assertFalse(result.git_mutation_authority_granted)

    def test_safe_write_block_prevents_verification(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = self._git_repo(Path(workspace))
            target_file = "docs/cartographer-live-evidence/not-approved.md"
            result = execute_safe_docs_evidence_workflow(
                run_id="run-7-2",
                step_id="step-write-evidence",
                approval_payload=self._valid_payload(target_file=target_file),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file=target_file,
                content="should not write\n",
                consumption_context=self._context("docs/cartographer-live-evidence/other.md"),
                workspace_root=workspace_root,
                current_head="abc123",
                verification_argv=["git", "diff", "--check"],
                now=self._now(),
            )

            self.assertEqual(result.status, "blocked")
            self.assertFalse(result.completed)
            self.assertTrue(result.blocked)
            self.assertIn("safe_write:approval:requested_files_exceed_exact_allowed_files", result.reasons)
            self.assertIsNone(result.verification_result)
            self.assertFalse((workspace_root / target_file).exists())
            self.assertEqual(result.ledger_events[-1].event_type, "step_blocked")
            self.assertIn("requested_files_exceed_exact_allowed_files", result.ledger_events[-1].reason)

    def test_target_must_be_live_evidence_prefix_before_safe_write(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = self._git_repo(Path(workspace))
            result = execute_safe_docs_evidence_workflow(
                run_id="run-7-2",
                step_id="step-write-evidence",
                approval_payload=self._valid_payload(target_file="docs/approved-safe-write.md"),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file="docs/approved-safe-write.md",
                content="should not write\n",
                consumption_context=self._context("docs/approved-safe-write.md"),
                workspace_root=workspace_root,
                current_head="abc123",
                verification_argv=["git", "diff", "--check"],
                now=self._now(),
            )

            self.assertEqual(result.status, "blocked")
            self.assertIn("target_not_safe_docs_evidence", result.reasons)
            self.assertEqual(result.ledger_events, ())
            self.assertFalse((workspace_root / "docs/approved-safe-write.md").exists())

    def test_blocked_verification_is_reported_after_safe_write_without_git_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = self._git_repo(Path(workspace))
            target_file = "docs/cartographer-live-evidence/blocked-verification.md"
            result = execute_safe_docs_evidence_workflow(
                run_id="run-7-2",
                step_id="step-write-evidence",
                approval_payload=self._valid_payload(target_file=target_file),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file=target_file,
                content="# Evidence before blocked verification\n",
                consumption_context=self._context(target_file),
                workspace_root=workspace_root,
                current_head="abc123",
                verification_argv=["git", "reset", "--hard"],
                now=self._now(),
            )

            self.assertEqual(result.status, "blocked")
            self.assertFalse(result.completed)
            self.assertTrue((workspace_root / target_file).exists())
            self.assertEqual(result.safe_write_result["status"], "written")
            self.assertEqual(result.verification_result["status"], "blocked")
            self.assertFalse(result.verification_result["executed"])
            self.assertIn("verification:destructive_git_command_blocked", result.reasons)
            self.assertEqual(result.ledger_events[-1].event_type, "step_blocked")
            self.assertFalse(result.git_mutation_authority_granted)

    def test_missing_run_step_and_target_fail_closed_before_work(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = self._git_repo(Path(workspace))
            result = execute_safe_docs_evidence_workflow(
                run_id="",
                step_id="",
                approval_payload=self._valid_payload(target_file="docs/cartographer-live-evidence/missing.md"),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file="",
                content="should not write\n",
                consumption_context=self._context("docs/cartographer-live-evidence/missing.md"),
                workspace_root=workspace_root,
                current_head="abc123",
                verification_argv=["git", "diff", "--check"],
                now=self._now(),
            )

            self.assertEqual(result.status, "blocked")
            self.assertIn("missing_run_id", result.reasons)
            self.assertIn("missing_step_id", result.reasons)
            self.assertIn("missing_target_file", result.reasons)
            self.assertIsNone(result.verification_result)
            self.assertEqual(result.ledger_events, ())

    def test_module_surface_has_no_queue_api_ui_or_git_mutation_hooks(self) -> None:
        public_functions = {
            name
            for name, value in vars(workflow_runner).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }
        self.assertEqual(
            public_functions,
            {
                "build_safe_docs_evidence_workflow_status",
                "execute_safe_docs_evidence_workflow",
            },
        )

        public_classes = {
            name
            for name, value in vars(workflow_runner).items()
            if inspect.isclass(value) and value.__module__ == workflow_runner.__name__
        }
        self.assertEqual(public_classes, {"SafeDocsEvidenceWorkflowResult"})

        source = inspect.getsource(workflow_runner)
        forbidden_fragments = (
            "subprocess",
            "os.system",
            "Popen",
            "shell=True",
            "source_proxy.api",
            "source_proxy.codex",
            "source_proxy.tasks",
            "src/app",
            "src/components",
            "git add",
            "git commit",
            "git push",
            "git branch",
            "git worktree",
            "git stash",
            "git reset",
            "git clean",
            "git checkout",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    @staticmethod
    def _git_repo(workspace_root: Path) -> Path:
        subprocess.run(["git", "init"], cwd=workspace_root, check=True, capture_output=True)
        return workspace_root

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 22, 12, 0, 0, tzinfo=UTC)

    @staticmethod
    def _scope() -> dict[str, str]:
        return {
            "type": "phase",
            "value": "cartographer-daily-driver-plan-7-phase-2",
        }

    def _valid_payload(self, *, target_file: str = "docs/cartographer-live-evidence/plan-7-phase-2.md") -> dict[str, object]:
        return {
            "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
            "token_id": "approval-token-plan-7-phase-2",
            "run_id": "run-7-2",
            "operator_id": "cartographer-runtime",
            "approver_id": "Britton",
            "action_type": "safe_write",
            "lane_id": "cartographer",
            "expires_at": (self._now() + timedelta(minutes=55)).isoformat().replace("+00:00", "Z"),
            "scope": self._scope(),
            "exact_allowed_files": [target_file],
            "exact_forbidden_files": [],
            "rollback_instructions": "Review exact target file and restore previous content manually.",
            "verification_instructions": "Run exact allowlisted verification command.",
            "expected_head": "abc123",
            "expected_dirty_tree": self._dirty_tree(),
            "kill_switch_state": APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
            "trust_tier": "tier-1",
            "single_action": True,
            "issued_by_human": True,
            "human_approved_at": (self._now() - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        }

    @staticmethod
    def _context(target_file: str) -> dict[str, object]:
        return {
            "action_class": "safe_write",
            "active_lane_id": "cartographer",
            "lane_owner": "cartographer",
            "lane_dirty_overlap_status": "clear",
            "trust_tier": "tier-1",
            "requested_trust_tier": "tier-1",
            "exact_allowed_files": [target_file],
            "exact_forbidden_files": [],
            "expected_head": "abc123",
            "expected_dirty_tree": CartographerWorkflowRunnerTests._dirty_tree(),
            "rollback": "Review exact target file and restore the previous content manually.",
            "verification": "Run exact allowlisted verification command.",
        }

    @staticmethod
    def _dirty_tree() -> dict[str, object]:
        return {
            "fingerprint": "workflow-runner-clean-plan-7",
            "dirty_files": [],
            "expected_dirty": False,
        }


if __name__ == "__main__":
    unittest.main()
