from __future__ import annotations

from dataclasses import replace
import inspect
import unittest

from source_proxy.cartographer import level_14_autonomy_runtime
from source_proxy.cartographer.level_14_autonomy_runtime import (
    CartographerLevel14KillSwitchState,
    CartographerLevel14SafeTaskQueueItem,
    build_level_14_blueprint_refresh_proposal_dry_run,
    build_level_14_escalation_closeout_proposal_dry_run,
    build_level_14_final_review_gate_dry_run,
    build_level_14_recurring_health_check_dry_run,
    build_level_14_safe_docs_evidence_maintenance_dry_run,
    validate_level_14_kill_switch_dry_run,
    validate_level_14_safe_task_queue_dry_run,
    validate_level_14_stop_controls_dry_run,
    validate_level_14_task_class_and_trust_tier_dry_run,
)


class CartographerLevel14AutonomyRuntimeTests(unittest.TestCase):
    def test_14_1_safe_task_queue_validates_without_execution_authority(self) -> None:
        result = validate_level_14_safe_task_queue_dry_run(self._item())

        self.assertEqual(result.level, "14.1")
        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.queue_execution_authority_granted)
        self.assertFalse(result.automatic_task_selection_granted)
        self.assertFalse(result.autonomy_granted)

    def test_14_1_queue_blocks_unknown_class_and_protected_paths(self) -> None:
        result = validate_level_14_safe_task_queue_dry_run(
            replace(
                self._item(),
                task_class="cleanup",
                allowed_files=("src/app/coding/page.tsx",),
            )
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("unsupported_task_class", result.blocked_reasons)
        self.assertIn("protected_path_in_scope", result.blocked_reasons)

    def test_14_2_task_class_and_trust_tier_fail_closed(self) -> None:
        result = validate_level_14_task_class_and_trust_tier_dry_run(
            replace(self._item(), trust_tier="production_operator"),
            allowed_trust_tiers=("dry_run_only",),
        )

        self.assertEqual(result.level, "14.2")
        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("trust_tier_mismatch", result.blocked_reasons)
        self.assertFalse(result.queue_execution_authority_granted)

    def test_14_3_kill_switch_blocks_queue_item(self) -> None:
        result = validate_level_14_kill_switch_dry_run(
            self._item(),
            (CartographerLevel14KillSwitchState(scope="global", active=True, reason="operator stop"),),
        )

        self.assertEqual(result.level, "14.3")
        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("active_kill_switch_blocks_task", result.blocked_reasons)

    def test_14_4_stop_controls_block_every_runtime_scope(self) -> None:
        result = validate_level_14_stop_controls_dry_run(
            self._item(),
            unexpected_head=True,
            unexpected_git_status=True,
            verification_failed=True,
            hidden_mutation_suspected=True,
        )

        self.assertEqual(result.level, "14.4")
        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("unexpected_head_stop", result.blocked_reasons)
        self.assertIn("hidden_mutation_stop", result.blocked_reasons)

    def test_14_5_recurring_health_check_does_not_schedule_background_job(self) -> None:
        packet = build_level_14_recurring_health_check_dry_run(
            self._item(task_class="docs_freshness_review"),
            operator_invoked=False,
        )

        self.assertEqual(packet.level, "14.5")
        self.assertTrue(packet.blocked)
        self.assertIn("background_scheduling_forbidden", packet.blocked_reasons)
        self.assertFalse(packet.would_schedule_background_job)
        self.assertFalse(packet.would_execute_task)

    def test_14_6_blueprint_refresh_proposal_writes_nothing(self) -> None:
        packet = build_level_14_blueprint_refresh_proposal_dry_run(
            self._item(task_class="blueprint_refresh_proposal"),
            proposed_blueprint_write=True,
        )

        self.assertEqual(packet.level, "14.6")
        self.assertTrue(packet.blocked)
        self.assertIn("blueprint_write_forbidden", packet.blocked_reasons)
        self.assertFalse(packet.would_write_files)

    def test_14_7_safe_docs_evidence_maintenance_requires_level_11_approval(self) -> None:
        packet = build_level_14_safe_docs_evidence_maintenance_dry_run(
            self._item(task_class="safe_docs_evidence_maintenance_proposal"),
            attempts_delete=True,
            has_scoped_level_11_approval=False,
        )

        self.assertEqual(packet.level, "14.7")
        self.assertTrue(packet.blocked)
        self.assertIn("evidence_receipt_or_history_delete_forbidden", packet.blocked_reasons)
        self.assertIn("scoped_level_11_approval_required_before_future_write", packet.blocked_reasons)
        self.assertFalse(packet.would_write_files)

    def test_14_8_escalation_closeout_proposal_does_not_notify_or_close(self) -> None:
        packet = build_level_14_escalation_closeout_proposal_dry_run(
            self._item(task_class="autonomous_escalation_proposal"),
            would_notify=True,
            would_auto_close=True,
        )

        self.assertEqual(packet.level, "14.8")
        self.assertTrue(packet.blocked)
        self.assertIn("notification_send_forbidden", packet.blocked_reasons)
        self.assertIn("automatic_closeout_forbidden", packet.blocked_reasons)
        self.assertFalse(packet.would_send_notification)

    def test_14_9_final_gate_never_calls_system_full_auto(self) -> None:
        payload = build_level_14_final_review_gate_dry_run()

        self.assertEqual(payload["level"], "14.9")
        self.assertTrue(payload["safe_limited_autonomy_v1_ready_for_final_proof"])
        self.assertFalse(payload["full_auto_granted"])
        self.assertFalse(payload["queue_execution_authority_granted"])
        self.assertFalse(payload["recurring_scheduler_authority_granted"])
        self.assertFalse(payload["write_authority_granted"])
        self.assertFalse(payload["autonomy_granted"])

    def test_module_exposes_no_write_execution_network_or_git_surface(self) -> None:
        source = inspect.getsource(level_14_autonomy_runtime)
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
            "git branch",
            "git worktree",
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
    def _item(
        *,
        task_class: str = "manual_check_reminder",
    ) -> CartographerLevel14SafeTaskQueueItem:
        return CartographerLevel14SafeTaskQueueItem(
            task_id="task-14",
            task_class=task_class,
            trust_tier="dry_run_only",
            lane="cartographer_runtime_dry_run",
            approval_token_id="token-14",
            allowed_files=("docs/manual-check.md",),
            forbidden_files=("src/**",),
            max_attempts=1,
            rollback_reference="rollback reference required before future writes",
            verification_reference="verification reference required before future writes",
            kill_switch_scope="cartographer_runtime_dry_run",
            expires_at="2026-05-23T00:00:00Z",
            status="queued",
        )


if __name__ == "__main__":
    unittest.main()
