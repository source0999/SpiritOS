from __future__ import annotations

from dataclasses import replace
import inspect
import unittest

from source_proxy.cartographer import level_12_workflow_runtime
from source_proxy.cartographer.level_12_workflow_runtime import (
    CartographerLevel12WorkflowEvent,
    CartographerLevel12WorkflowState,
    CartographerLevel12WorkflowStepState,
    build_level_12_closeout_level_13_access_check,
    build_level_12_step_approval_interruption_dry_run,
    build_level_12_workflow_closeout_packet,
    build_level_12_workflow_dry_run_packet,
    validate_level_12_cancellation_timeout_dry_run,
    validate_level_12_pause_resume_dry_run,
    validate_level_12_retry_policy_dry_run,
    validate_level_12_verification_rollback_metadata_dry_run,
    validate_level_12_workflow_event_ledger_dry_run,
    validate_level_12_workflow_state_dry_run,
)


class CartographerLevel12WorkflowRuntimeTests(unittest.TestCase):
    def test_12_1_workflow_state_schema_validates_without_execution_authority(self) -> None:
        result = validate_level_12_workflow_state_dry_run(self._state())

        self.assertEqual(result.level, "12.1")
        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.workflow_execution_authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.local_execution_authority_granted)

    def test_12_1_step_scope_cannot_exceed_workflow_scope(self) -> None:
        state = replace(
            self._state(),
            steps=(replace(self._step(), target_files=("src/app/coding/page.tsx",)),),
        )

        result = validate_level_12_workflow_state_dry_run(state)

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("step_scope_exceeds_workflow_scope:step-1", result.blocked_reasons)
        self.assertIn("protected_path_in_scope:step-1", result.blocked_reasons)

    def test_12_2_workflow_event_ledger_order_validates_for_dry_run_only(self) -> None:
        result = validate_level_12_workflow_event_ledger_dry_run(
            (
                self._event(1, "workflow_created"),
                self._event(2, "workflow_dry_run_created"),
                self._event(3, "workflow_paused"),
            )
        )

        self.assertEqual(result.level, "12.2")
        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.workflow_execution_authority_granted)

        bad = validate_level_12_workflow_event_ledger_dry_run(
            (self._event(1, "workflow_created"), self._event(3, "workflow_paused"))
        )
        self.assertFalse(bad.valid_for_dry_run)
        self.assertIn("workflow_event_sequence_gap_or_reorder", bad.blocked_reasons)

    def test_12_3_workflow_dry_run_packet_never_starts_work(self) -> None:
        packet = build_level_12_workflow_dry_run_packet(self._state())

        self.assertEqual(packet.level, "12.3")
        self.assertFalse(packet.blocked)
        self.assertFalse(packet.would_start_workflow)
        self.assertFalse(packet.would_execute_step)
        self.assertFalse(packet.would_write_files)
        self.assertFalse(packet.would_run_commands)

    def test_12_4_sensitive_step_pauses_for_approval(self) -> None:
        state = replace(
            self._state(),
            steps=(replace(self._step(), approval_token_id=None),),
        )

        packet = build_level_12_step_approval_interruption_dry_run(state)

        self.assertEqual(packet.level, "12.4")
        self.assertTrue(packet.blocked)
        self.assertIn("approval_interruption_required", packet.blocked_reasons)
        self.assertFalse(packet.would_execute_step)

    def test_12_5_resume_requires_exact_paused_state(self) -> None:
        ok = validate_level_12_pause_resume_dry_run(
            self._state(status="paused"),
            current_head="head-1",
            current_git_status="clean",
        )
        self.assertTrue(ok.valid_for_dry_run)

        stale = validate_level_12_pause_resume_dry_run(
            self._state(status="paused"),
            current_head="other-head",
            current_git_status="dirty",
        )
        self.assertFalse(stale.valid_for_dry_run)
        self.assertIn("head_changed", stale.blocked_reasons)
        self.assertIn("git_status_changed", stale.blocked_reasons)

    def test_12_6_cancelled_or_timed_out_workflows_cannot_continue(self) -> None:
        cancelled = validate_level_12_cancellation_timeout_dry_run(
            self._state(status="running", cancellation_requested=True)
        )
        self.assertFalse(cancelled.valid_for_dry_run)
        self.assertIn("cancellation_must_stop_or_cancel_workflow", cancelled.blocked_reasons)

        terminal_with_step = validate_level_12_cancellation_timeout_dry_run(
            self._state(status="timed_out", timeout_policy="continue")
        )
        self.assertFalse(terminal_with_step.valid_for_dry_run)
        self.assertIn("timeout_policy_must_pause_or_cancel", terminal_with_step.blocked_reasons)
        self.assertIn("terminal_stop_must_clear_current_step", terminal_with_step.blocked_reasons)

    def test_12_7_retry_policy_is_bounded_and_visible(self) -> None:
        result = validate_level_12_retry_policy_dry_run(
            replace(self._step(), retry_count=1, max_retries=1),
            retry_requested=True,
            blocked_reason="verification_failed",
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("max_retries_reached", result.blocked_reasons)

        protected = validate_level_12_retry_policy_dry_run(
            self._step(),
            retry_requested=True,
            blocked_reason="protected_path_in_scope",
        )
        self.assertFalse(protected.valid_for_dry_run)
        self.assertIn("retry_after_protected_path_block_forbidden", protected.blocked_reasons)

    def test_12_8_closeout_requires_terminal_state_verification_and_rollback(self) -> None:
        packet = build_level_12_workflow_closeout_packet(
            self._state(status="running"),
            verification_passed=False,
            rollback_available=False,
        )

        self.assertTrue(packet.blocked)
        self.assertIn("closeout_requires_terminal_status", packet.blocked_reasons)
        self.assertIn("closeout_requires_passing_verification", packet.blocked_reasons)
        self.assertIn("closeout_requires_rollback_reference", packet.blocked_reasons)
        self.assertFalse(packet.would_write_files)

    def test_12_9_sensitive_steps_require_verification_and_rollback_metadata(self) -> None:
        state = replace(
            self._state(),
            steps=(
                replace(
                    self._step(),
                    verification_reference=None,
                    rollback_reference=None,
                ),
            ),
        )

        result = validate_level_12_verification_rollback_metadata_dry_run(state)

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("missing_verification_reference:step-1", result.blocked_reasons)
        self.assertIn("missing_rollback_reference:step-1", result.blocked_reasons)

    def test_12_10_closeout_keeps_level_13_human_gated(self) -> None:
        payload = build_level_12_closeout_level_13_access_check()

        self.assertEqual(payload["level"], "12.10")
        self.assertEqual(payload["level_13_access"], "requires_explicit_human_verification")
        self.assertFalse(payload["workflow_execution_authority_granted"])
        self.assertFalse(payload["write_authority_granted"])
        self.assertFalse(payload["local_execution_authority_granted"])
        self.assertFalse(payload["worker_orchestration_authority_granted"])
        self.assertFalse(payload["autonomy_granted"])

    def test_module_exposes_no_write_execution_api_or_git_surface(self) -> None:
        source = inspect.getsource(level_12_workflow_runtime)
        forbidden_fragments = (
            "subprocess",
            "os.system",
            "Path(",
            "open(",
            ".write(",
            "write_text(",
            "requests",
            "urllib",
            "socket",
            "source_proxy.api",
            "source_proxy.codex",
            "source_proxy.testing.runner",
            "source_proxy.verification",
            "git add",
            "git commit",
            "git push",
            "git merge",
            "git checkout",
            "git stash",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    @staticmethod
    def _step() -> CartographerLevel12WorkflowStepState:
        return CartographerLevel12WorkflowStepState(
            step_id="step-1",
            title="Dry-run approved docs step",
            action_type="approved_docs_only_apply",
            status="paused",
            target_files=("docs/demo.md",),
            approval_required=True,
            approval_token_id="token-1",
            verification_reference="verify docs/demo.md",
            rollback_reference="rollback docs/demo.md",
            retry_count=0,
            max_retries=1,
            timeout_seconds=60,
        )

    @classmethod
    def _state(
        cls,
        *,
        status: str = "paused",
        cancellation_requested: bool = False,
        timeout_policy: str = "pause",
    ) -> CartographerLevel12WorkflowState:
        return CartographerLevel12WorkflowState(
            workflow_id="workflow-12",
            run_id="run-12",
            workflow_type="docs_dry_run",
            status=status,
            current_step_id="step-1",
            steps=(cls._step(),),
            allowed_files=("docs/demo.md",),
            forbidden_files=("src/**",),
            pause_requested=status == "paused",
            cancellation_requested=cancellation_requested,
            timeout_policy=timeout_policy,
            created_at="2026-05-22T00:00:00Z",
            updated_at="2026-05-22T00:00:00Z",
            head_expected="head-1",
            git_status_expected="clean",
        )

    @staticmethod
    def _event(sequence: int, event_type: str) -> CartographerLevel12WorkflowEvent:
        return CartographerLevel12WorkflowEvent(
            event_id=f"workflow-event-{sequence}",
            event_type=event_type,
            workflow_id="workflow-12",
            run_id="run-12",
            step_id="step-1",
            sequence=sequence,
            actor="cartographer-dry-run",
            reason="blocked for test" if event_type.endswith("_blocked") else None,
        )


if __name__ == "__main__":
    unittest.main()
