from __future__ import annotations

from datetime import UTC, datetime, timedelta
import inspect
import unittest

from source_proxy.cartographer import workflow_state
from source_proxy.cartographer.workflow_state import (
    FORBIDDEN_EXECUTION_CLASSES,
    WORKFLOW_ACTION_CLASS,
    WORKFLOW_STATUSES,
    WORKFLOW_TRUST_TIER,
    WorkflowRunState,
    WorkflowStepState,
    build_workflow_state_model_status,
    preview_workflow_transition,
)


class CartographerWorkflowStateModelTests(unittest.TestCase):
    def test_status_preview_is_model_only_and_grants_no_authority(self) -> None:
        status = build_workflow_state_model_status()

        self.assertEqual(status["status"], "model-only")
        self.assertEqual(status["workflow_statuses"], WORKFLOW_STATUSES)
        self.assertTrue(status["preview_only"])
        self.assertFalse(status["durable_storage_available"])
        self.assertFalse(status["execution_available"])
        self.assertFalse(status["workflow_execution_authority_granted"])
        self.assertFalse(status["queue_authority_granted"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])
        self.assertFalse(status["token_minting_available"])
        self.assertFalse(status["approval_storage_available"])

    def test_run_and_step_state_capture_phase_5_1_fields_as_data(self) -> None:
        step = WorkflowStepState(
            step_id="step-1",
            status="blocked",
            approval_token_id="token-1",
            allowed_files=("docs/cartographer-live-evidence/example.md",),
            forbidden_files=("source_proxy/api/cartographer.py",),
            blocker_reason="operator_review_required",
            verification_result={"status": "not-run"},
            rollback_reference="rollback-not-available-in-phase-5-1",
            receipt_path="docs/cartographer-live-receipts/example.md",
            closeout={"summary": "model only"},
        )
        run = WorkflowRunState(
            run_id="run-1",
            status="pending",
            steps=(step,),
            approval_token_id="token-1",
            allowed_files=("docs/cartographer-live-evidence/example.md",),
            forbidden_files=("source_proxy/api/cartographer.py",),
            blocker_reason=None,
            verification_result={"status": "not-run"},
            rollback_reference="rollback-not-available-in-phase-5-1",
            receipt_path="docs/cartographer-live-receipts/example.md",
            closeout={"summary": "model only"},
        )

        payload = run.to_dict()

        self.assertEqual(payload["run_id"], "run-1")
        self.assertEqual(payload["steps"][0]["step_id"], "step-1")
        self.assertEqual(payload["steps"][0]["approval_token_id"], "token-1")
        self.assertEqual(payload["allowed_files"], ("docs/cartographer-live-evidence/example.md",))
        self.assertEqual(payload["forbidden_files"], ("source_proxy/api/cartographer.py",))
        self.assertEqual(payload["verification_result"], {"status": "not-run"})
        self.assertEqual(payload["receipt_path"], "docs/cartographer-live-receipts/example.md")
        self.assertTrue(payload["model_only"])
        self.assertFalse(payload["durable_storage_available"])
        self.assertFalse(payload["execution_available"])
        self.assertFalse(payload["git_mutation_authority_granted"])

    def test_valid_transition_preview_accepts_without_execution_authority(self) -> None:
        preview = preview_workflow_transition(
            WorkflowRunState(run_id="run-1", status="pending", approval_token_id="token-1"),
            "approved",
            approval_context=self._approval_context(),
            now=self._now(),
        )

        self.assertTrue(preview.accepted)
        self.assertFalse(preview.blocked)
        self.assertEqual(preview.status, "accepted")
        self.assertEqual(preview.reasons, ())
        self.assertEqual(preview.run_id, "run-1")
        self.assertEqual(preview.current_status, "pending")
        self.assertEqual(preview.requested_status, "approved")
        self.assertTrue(preview.preview_only)
        self.assertTrue(preview.model_only)
        self.assertFalse(preview.execution_available)
        self.assertFalse(preview.workflow_execution_authority_granted)
        self.assertFalse(preview.queue_authority_granted)
        self.assertFalse(preview.command_authority_granted)
        self.assertFalse(preview.write_authority_granted)
        self.assertFalse(preview.git_mutation_authority_granted)

    def test_unknown_states_and_invalid_transitions_fail_closed(self) -> None:
        cases = [
            (
                {"run_id": "run-1", "status": "mystery"},
                "approved",
                "unknown_current_status",
            ),
            (
                {"run_id": "run-1", "status": "pending"},
                "mystery",
                "unknown_requested_status",
            ),
            (
                {"run_id": "run-1", "status": "pending"},
                "completed",
                "invalid_transition",
            ),
            (
                {"status": "pending"},
                "approved",
                "missing_run_id",
            ),
        ]

        for state, requested_status, reason in cases:
            with self.subTest(reason=reason):
                preview = preview_workflow_transition(
                    state,
                    requested_status,
                    approval_context=self._approval_context(),
                    now=self._now(),
                )

                self.assertFalse(preview.accepted)
                self.assertTrue(preview.blocked)
                self.assertIn(reason, preview.reasons)

    def test_missing_or_malformed_approval_context_fails_closed(self) -> None:
        cases = [
            (None, "missing_approval_context"),
            ({}, "missing_approval_context_field:token_id"),
            ({**self._approval_context(), "approved_by": ""}, "malformed_approval_context_field:approved_by"),
            ({**self._approval_context(), "issued_at": "not-a-date"}, "malformed_approval_context_field:issued_at"),
        ]

        for approval_context, reason in cases:
            with self.subTest(reason=reason):
                preview = preview_workflow_transition(
                    WorkflowRunState(run_id="run-1", status="pending"),
                    "approved",
                    approval_context=approval_context,
                    now=self._now(),
                )

                self.assertFalse(preview.accepted)
                self.assertIn(reason, preview.reasons)

    def test_safety_context_failures_block_transition_preview(self) -> None:
        cases = [
            ({"kill_switch_active": True}, "kill_switch_active"),
            ({"current_head": "different-head"}, "stale_head"),
            ({"dirty_tree_matches_expected": False}, "dirty_tree_mismatch"),
            ({"approved_by": "cartographer-runtime"}, "self_approval_rejected"),
            ({"approved_for_actor": "other-runtime"}, "wrong_actor"),
            ({"expires_at": "2026-05-22T11:59:59Z"}, "token_expired"),
            ({"action_class": "safe_write"}, "wrong_action_class"),
            ({"trust_tier": "tier-2"}, "wrong_trust_tier"),
            ({"execution_class": "command"}, "forbidden_execution_class"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                preview = preview_workflow_transition(
                    WorkflowRunState(run_id="run-1", status="pending"),
                    "approved",
                    approval_context={**self._approval_context(), **override},
                    now=self._now(),
                )

                self.assertFalse(preview.accepted)
                self.assertTrue(preview.blocked)
                self.assertIn(reason, preview.reasons)

    def test_every_forbidden_execution_class_blocks_as_data_only(self) -> None:
        for execution_class in FORBIDDEN_EXECUTION_CLASSES:
            with self.subTest(execution_class=execution_class):
                preview = preview_workflow_transition(
                    WorkflowRunState(run_id="run-1", status="pending"),
                    "approved",
                    approval_context={
                        **self._approval_context(),
                        "execution_class": execution_class,
                    },
                    now=self._now(),
                )

                self.assertFalse(preview.accepted)
                self.assertIn("forbidden_execution_class", preview.reasons)
                self.assertFalse(preview.execution_available)

    def test_model_surface_has_no_execution_storage_or_git_mutation_hooks(self) -> None:
        public_functions = {
            name
            for name, value in vars(workflow_state).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }
        self.assertEqual(
            public_functions,
            {
                "build_workflow_state_model_status",
                "preview_workflow_transition",
            },
        )

        public_classes = {
            name
            for name, value in vars(workflow_state).items()
            if inspect.isclass(value) and value.__module__ == workflow_state.__name__
        }
        self.assertEqual(
            public_classes,
            {
                "WorkflowRunState",
                "WorkflowStepState",
                "WorkflowTransitionPreview",
            },
        )

        source = inspect.getsource(workflow_state)
        forbidden_fragments = (
            "subprocess",
            "os.system",
            "Popen",
            "Path(",
            "open(",
            ".write(",
            "write_text(",
            "requests",
            "urllib",
            "socket",
            "source_proxy.api",
            "source_proxy.codex",
            "execute_safe_write_request",
            "run_verification_command",
            "mint_approval",
            "store_approval",
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
    def _now() -> datetime:
        return datetime(2026, 5, 22, 12, 0, 0, tzinfo=UTC)

    def _approval_context(self) -> dict[str, object]:
        return {
            "token_id": "token-1",
            "approved_by": "Britton",
            "approved_for_actor": "cartographer-runtime",
            "requested_actor": "cartographer-runtime",
            "action_class": WORKFLOW_ACTION_CLASS,
            "trust_tier": WORKFLOW_TRUST_TIER,
            "issued_at": (self._now() - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
            "expires_at": (self._now() + timedelta(minutes=55)).isoformat().replace("+00:00", "Z"),
            "expected_head": "head-1",
            "current_head": "head-1",
            "dirty_tree_matches_expected": True,
            "kill_switch_active": False,
        }


if __name__ == "__main__":
    unittest.main()
