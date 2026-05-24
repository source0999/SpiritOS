from __future__ import annotations

from datetime import UTC, datetime, timedelta
import inspect
from pathlib import Path
import subprocess
import tempfile
import unittest

from source_proxy.cartographer import workflow_runner
from source_proxy.cartographer.approval_token_runtime import (
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
            target_file = "docs/cartographer-live-evidence/plan-5-phase-4.md"
            result = execute_safe_docs_evidence_workflow(
                run_id="run-5-4",
                step_id="step-write-evidence",
                approval_payload=self._valid_payload(),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file=target_file,
                content="# Plan 5 Phase 4 Evidence\n",
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
            self.assertEqual(written.read_text(encoding="utf-8"), "# Plan 5 Phase 4 Evidence\n")
            self.assertEqual(result.safe_write_result["status"], "written")
            self.assertEqual(result.verification_result["status"], "passed")
            self.assertEqual(result.verification_result["matched_command_id"], "git_diff_check")
            self.assertEqual(
                event_types,
                (
                    "workflow_created",
                    "step_started",
                    "step_completed",
                    "workflow_verified",
                    "workflow_closed_out",
                ),
            )
            self.assertTrue(validation.valid)
            self.assertFalse(result.workflow_execution_authority_granted)
            self.assertFalse(result.queue_authority_granted)
            self.assertFalse(result.command_authority_granted)
            self.assertFalse(result.git_mutation_authority_granted)

    def test_safe_write_block_prevents_verification(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = self._git_repo(Path(workspace))
            target_file = "docs/cartographer-live-evidence/not-approved.md"
            result = execute_safe_docs_evidence_workflow(
                run_id="run-5-4",
                step_id="step-write-evidence",
                approval_payload=self._valid_payload(),
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
                run_id="run-5-4",
                step_id="step-write-evidence",
                approval_payload=self._valid_payload(),
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
                run_id="run-5-4",
                step_id="step-write-evidence",
                approval_payload=self._valid_payload(),
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
                approval_payload=self._valid_payload(),
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
            "value": "cartographer-daily-driver-plan-5-phase-4",
        }

    def _valid_payload(self) -> dict[str, object]:
        return {
            "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
            "token_id": "approval-token-plan-5-phase-4",
            "issued_at": (self._now() - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
            "expires_at": (self._now() + timedelta(minutes=55)).isoformat().replace("+00:00", "Z"),
            "approved_by": "Britton",
            "approved_for_actor": "cartographer-runtime",
            "scope": self._scope(),
            "reason": "Approved Plan 5 Phase 4 first safe docs evidence workflow.",
        }

    @staticmethod
    def _context(target_file: str) -> dict[str, object]:
        return {
            "action_class": "safe_write",
            "trust_tier": "tier-1",
            "requested_trust_tier": "tier-1",
            "exact_allowed_files": [target_file],
            "exact_forbidden_files": [],
            "expected_head": "abc123",
            "rollback": "Review exact target file and restore the previous content manually.",
            "verification": "Run exact allowlisted verification command.",
        }


if __name__ == "__main__":
    unittest.main()
