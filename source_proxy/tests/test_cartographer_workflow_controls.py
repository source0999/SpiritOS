from __future__ import annotations

from datetime import UTC, datetime
import inspect
import unittest

from source_proxy.cartographer import workflow_controls
from source_proxy.cartographer.workflow_controls import (
    MAX_RETRY_COUNT,
    WORKFLOW_CONTROL_TYPES,
    WorkflowControlContext,
    build_workflow_controls_status,
    preview_workflow_control,
)
from source_proxy.cartographer.workflow_state import WorkflowRunState


class CartographerWorkflowControlsTests(unittest.TestCase):
    def test_status_is_control_preview_only_without_execution_authority(self) -> None:
        status = build_workflow_controls_status()

        self.assertEqual(status["status"], "control-preview-only")
        self.assertEqual(status["control_types"], WORKFLOW_CONTROL_TYPES)
        self.assertEqual(status["max_retry_count"], MAX_RETRY_COUNT)
        self.assertTrue(status["bounded_retry_counts"])
        self.assertFalse(status["cancelled_workflow_continues_work"])
        self.assertFalse(status["execution_available"])
        self.assertFalse(status["durable_write_available"])
        self.assertFalse(status["workflow_execution_authority_granted"])
        self.assertFalse(status["queue_authority_granted"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])

    def test_pause_resume_cancel_timeout_and_retry_controls_preview_expected_targets(self) -> None:
        cases = [
            ("pause", "running", "blocked", "workflow_paused", None),
            ("resume", "blocked", "running", "workflow_resumed", None),
            ("cancel", "running", "cancelled", "workflow_cancelled", None),
            ("timeout", "running", "failed", "workflow_timed_out", None),
            ("retry", "blocked", "running", "step_retried", 2),
        ]

        for control_type, current_status, target_status, event_type, next_retry_count in cases:
            with self.subTest(control_type=control_type):
                preview = preview_workflow_control(
                    WorkflowRunState(run_id="run-plan-7", status=current_status),
                    control_type,
                    context=self._context(step_id="step-1", retry_count=1),
                    now=self._now(),
                )

                self.assertTrue(preview.accepted)
                self.assertFalse(preview.blocked)
                self.assertEqual(preview.reasons, ())
                self.assertEqual(preview.control_type, control_type)
                self.assertEqual(preview.target_status, target_status)
                self.assertEqual(preview.event_type, event_type)
                self.assertIsNotNone(preview.event_preview)
                self.assertEqual(preview.event_preview["event_type"], event_type)
                self.assertEqual(preview.event_preview["actor"], "Britton")
                self.assertEqual(preview.event_preview["occurred_at"], "2026-05-22T12:00:00Z")
                self.assertTrue(preview.event_preview["preview_only"])
                self.assertFalse(preview.event_preview["execution_available"])
                self.assertFalse(preview.event_preview["durable_write_available"])
                self.assertEqual(preview.next_retry_count, next_retry_count)
                self.assertTrue(preview.preview_only)
                self.assertTrue(preview.control_only)
                self.assertFalse(preview.execution_available)
                self.assertFalse(preview.durable_write_available)
                self.assertFalse(preview.git_mutation_authority_granted)

    def test_retry_is_bounded_and_requires_step_id(self) -> None:
        cases = [
            ({"retry_count": MAX_RETRY_COUNT}, "retry_limit_exceeded"),
            ({"retry_count": -1}, "invalid_retry_count"),
            ({"retry_count": "hidden"}, "invalid_retry_count"),
            ({"max_retry_count": MAX_RETRY_COUNT + 1}, "unsupported_max_retry_count"),
            ({"step_id": None}, "missing_step_id"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                context = {**self._context(step_id="step-1"), **override}
                preview = preview_workflow_control(
                    WorkflowRunState(run_id="run-plan-7", status="blocked"),
                    "retry",
                    context=context,
                    now=self._now(),
                )

                self.assertFalse(preview.accepted)
                self.assertTrue(preview.blocked)
                self.assertIn(reason, preview.reasons)
                self.assertIsNone(preview.next_retry_count)

    def test_terminal_workflows_cannot_continue_with_controls(self) -> None:
        for current_status in ("completed", "cancelled"):
            for control_type in WORKFLOW_CONTROL_TYPES:
                with self.subTest(current_status=current_status, control_type=control_type):
                    preview = preview_workflow_control(
                        WorkflowRunState(run_id="run-plan-7", status=current_status),
                        control_type,
                        context=self._context(step_id="step-1"),
                        now=self._now(),
                    )

                    self.assertFalse(preview.accepted)
                    self.assertTrue(preview.blocked)
                    self.assertIn("terminal_workflow_cannot_continue", preview.reasons)
                    self.assertFalse(preview.execution_available)

    def test_controls_fail_closed_for_unknown_status_control_and_missing_context(self) -> None:
        cases = [
            (
                WorkflowRunState(run_id="run-plan-7", status="mystery"),
                "pause",
                self._context(),
                "unknown_current_status",
            ),
            (
                WorkflowRunState(run_id="run-plan-7", status="running"),
                "launch",
                self._context(),
                "unknown_control_type",
            ),
            (
                WorkflowRunState(run_id="", status="running"),
                "pause",
                self._context(),
                "missing_run_id",
            ),
            (
                WorkflowRunState(run_id="run-plan-7", status="running"),
                "pause",
                None,
                "missing_requested_by",
            ),
            (
                WorkflowRunState(run_id="run-plan-7", status="running"),
                "pause",
                {**self._context(), "reason": ""},
                "missing_reason",
            ),
            (
                WorkflowRunState(run_id="run-plan-7", status="running"),
                "pause",
                {**self._context(), "kill_switch_active": True},
                "kill_switch_active",
            ),
        ]

        for state, control_type, context, reason in cases:
            with self.subTest(reason=reason):
                preview = preview_workflow_control(
                    state,
                    control_type,
                    context=context,
                    now=self._now(),
                )

                self.assertFalse(preview.accepted)
                self.assertTrue(preview.blocked)
                self.assertIn(reason, preview.reasons)

    def test_resume_requires_approval_token_id(self) -> None:
        preview = preview_workflow_control(
            WorkflowRunState(run_id="run-plan-7", status="blocked"),
            "resume",
            context={**self._context(), "approval_token_id": None},
            now=self._now(),
        )

        self.assertFalse(preview.accepted)
        self.assertTrue(preview.blocked)
        self.assertIn("missing_resume_approval", preview.reasons)
        self.assertIsNotNone(preview.event_preview)
        self.assertEqual(preview.event_preview["status"], "blocked")
        self.assertFalse(preview.event_preview["execution_available"])

    def test_control_not_allowed_from_status_blocks(self) -> None:
        cases = [
            ("pause", "pending"),
            ("timeout", "pending"),
            ("retry", "running"),
        ]

        for control_type, current_status in cases:
            with self.subTest(control_type=control_type, current_status=current_status):
                preview = preview_workflow_control(
                    WorkflowRunState(run_id="run-plan-7", status=current_status),
                    control_type,
                    context=self._context(step_id="step-1"),
                    now=self._now(),
                )

                self.assertFalse(preview.accepted)
                self.assertIn("control_not_allowed_from_status", preview.reasons)

    def test_context_dataclass_is_supported_as_data_only(self) -> None:
        preview = preview_workflow_control(
            {"run_id": "run-plan-7", "status": "running"},
            "pause",
            context=WorkflowControlContext(
                requested_by="Britton",
                reason="operator pause",
                requested_at="2026-05-22T12:00:00Z",
            ),
            now=self._now(),
        )

        self.assertTrue(preview.accepted)
        self.assertEqual(preview.requested_by, "Britton")
        self.assertEqual(preview.reason, "operator pause")
        self.assertEqual(preview.requested_at, "2026-05-22T12:00:00Z")

    def test_module_surface_has_no_execution_storage_or_git_mutation_hooks(self) -> None:
        public_functions = {
            name
            for name, value in vars(workflow_controls).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }
        self.assertEqual(
            public_functions,
            {
                "build_workflow_controls_status",
                "preview_workflow_control",
            },
        )

        public_classes = {
            name
            for name, value in vars(workflow_controls).items()
            if inspect.isclass(value) and value.__module__ == workflow_controls.__name__
        }
        self.assertEqual(
            public_classes,
            {
                "WorkflowControlContext",
                "WorkflowControlPreview",
            },
        )

        source = inspect.getsource(workflow_controls)
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
            "preview_append_workflow_ledger_event",
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

    @staticmethod
    def _context(
        *,
        step_id: str | None = None,
        retry_count: int = 0,
    ) -> dict[str, object]:
        return {
            "requested_by": "Britton",
            "reason": "operator control",
            "retry_count": retry_count,
            "max_retry_count": MAX_RETRY_COUNT,
            "step_id": step_id,
            "requested_at": "2026-05-22T12:00:00Z",
            "approval_token_id": "approval-token-plan-7-phase-2",
            "kill_switch_active": False,
        }


if __name__ == "__main__":
    unittest.main()
