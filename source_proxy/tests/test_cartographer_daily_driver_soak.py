from __future__ import annotations

from datetime import UTC, datetime
import inspect
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.cartographer import soak_promotion
from source_proxy.cartographer.soak_promotion import (
    FORBIDDEN_SOAK_AUTHORITIES,
    KILL_SWITCH_AND_ROLLBACK_DRILLS_PHASE,
    PROMOTION_DECISION_PHASE,
    PROMOTION_TIERS,
    REQUIRED_KILL_SWITCH_DRILL_STAGES,
    SAFE_SUPERVISED_ACTION_CLASSES,
    SEVENTY_TWO_HOUR_SOAK_PHASE,
    TEN_TASK_SUPERVISED_RUN_PHASE,
    TEN_TASK_SUPERVISED_RUN_REQUIRED_COUNT,
    TWENTY_FOUR_HOUR_SOAK_PHASE,
    DailyDriverSoakVerification,
    KillSwitchRollbackDrill,
    SupervisedSafeTaskReceipt,
    TwentyFourHourSoakSample,
    build_kill_switch_rollback_drill_status,
    build_promotion_decision_status,
    build_seventy_two_hour_soak_status,
    build_ten_task_supervised_run_status,
    build_twenty_four_hour_soak_status,
    record_promotion_decision,
    validate_kill_switch_rollback_drills,
    validate_seventy_two_hour_soak,
    validate_twenty_four_hour_soak,
    validate_ten_task_supervised_run,
)


class CartographerDailyDriverSoakTests(unittest.TestCase):
    def test_status_is_supervised_run_validation_only(self) -> None:
        status = build_ten_task_supervised_run_status()

        self.assertEqual(status["phase"], TEN_TASK_SUPERVISED_RUN_PHASE)
        self.assertEqual(status["status"], "supervised-run-validation-only")
        self.assertEqual(status["required_task_count"], TEN_TASK_SUPERVISED_RUN_REQUIRED_COUNT)
        self.assertEqual(status["safe_action_classes"], SAFE_SUPERVISED_ACTION_CLASSES)
        self.assertEqual(status["forbidden_authorities"], FORBIDDEN_SOAK_AUTHORITIES)
        self.assertTrue(status["operator_supervision_required"])
        self.assertTrue(status["human_review_required"])
        self.assertTrue(status["one_supervised_task_first"])
        self.assertTrue(status["ten_supervised_receipts_required"])
        self.assertTrue(status["false_positive_tracking_required"])
        self.assertTrue(status["false_negative_tracking_required"])
        self.assertTrue(status["supervised_trial_summary_available"])
        self.assertFalse(status["background_loop_enabled"])
        self.assertFalse(status["queue_execution_enabled"])
        self.assertFalse(status["task_execution_enabled"])
        self.assertFalse(status["command_execution_enabled"])
        self.assertFalse(status["safe_write_enabled"])
        self.assertFalse(status["commit_enabled"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["durable_storage_written"])
        self.assertFalse(status["api_mutation_available"])

    def test_valid_ten_task_supervised_run_accepts_receipts_without_execution(self) -> None:
        result = validate_ten_task_supervised_run(
            self._receipts(),
            expected_trust_tier="tier-1",
            expected_approval_token_prefix="approval-token-plan-10-1-",
            now=self._now(),
        )

        self.assertTrue(result.passed)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.task_count, 10)
        self.assertEqual(len(result.task_ids), 10)
        self.assertEqual(len(result.receipt_paths), 10)
        self.assertEqual(result.first_supervised_receipt_path, "docs/cartographer-live-receipts/task-00.md")
        self.assertEqual(result.false_positive_count, 0)
        self.assertEqual(result.false_negative_count, 0)
        self.assertEqual(
            result.supervised_trial_summary["schema_version"],
            "cartographer.supervised_daily_driver_trial_summary.v1",
        )
        self.assertEqual(result.supervised_trial_summary["first_task_id"], "task-00")
        self.assertEqual(
            result.supervised_trial_summary["first_receipt_path"],
            "docs/cartographer-live-receipts/task-00.md",
        )
        self.assertEqual(result.supervised_trial_summary["receipt_count"], 10)
        self.assertFalse(result.supervised_trial_summary["next_task_auto_started"])
        self.assertFalse(result.supervised_trial_summary["background_loop_started"])
        self.assertFalse(result.supervised_trial_summary["queue_execution_performed"])
        self.assertFalse(result.supervised_trial_summary["task_execution_performed"])
        self.assertFalse(result.supervised_trial_summary["safe_write_performed"])
        self.assertFalse(result.supervised_trial_summary["commit_performed"])
        self.assertFalse(result.supervised_trial_summary["push_performed"])
        self.assertFalse(result.supervised_trial_summary["authority_granted_by_summary"])
        self.assertTrue(result.operator_supervision_required)
        self.assertTrue(result.human_review_required)
        self.assertFalse(result.background_loop_enabled)
        self.assertFalse(result.queue_execution_enabled)
        self.assertFalse(result.task_execution_enabled)
        self.assertFalse(result.command_execution_enabled)
        self.assertFalse(result.safe_write_enabled)
        self.assertFalse(result.commit_enabled)
        self.assertFalse(result.push_enabled)
        self.assertFalse(result.durable_storage_written)
        self.assertFalse(result.api_mutation_available)

    def test_supervised_run_requires_exactly_ten_receipts(self) -> None:
        result = validate_ten_task_supervised_run(
            self._receipts()[:9],
            expected_trust_tier="tier-1",
            expected_approval_token_prefix="approval-token-plan-10-1-",
            now=self._now(),
        )

        self.assertFalse(result.passed)
        self.assertIn("ten_supervised_task_receipts_required", result.reasons)
        self.assertEqual(result.task_count, 9)

    def test_supervised_run_fail_closed_for_receipt_scope_and_authority(self) -> None:
        receipts = list(self._receipts())
        bad = receipts[0].to_dict()
        bad.update(
            {
                "action_class": "source",
                "trust_tier": "tier-3",
                "approval_token_id": "wrong-token",
                "exact_files": ("docs/*.md",),
                "receipt_path": "source_proxy/receipt.md",
                "status": "failed",
                "verification": {
                    "status": "failed",
                    "checks": ("pytest",),
                    "checked_at": "2026-05-23T12:00:00Z",
                },
                "rollback_guidance": "",
                "kill_switch_checked": False,
                "operator_supervised": False,
                "human_reviewed": False,
                "false_positive_count": -1,
                "false_negative_count": True,
                "next_task_auto_started": True,
                "background_loop_started": True,
                "completed_at": "2026-05-23T12:10:00Z",
                "task_executed_by_soak_model": True,
            }
        )
        receipts[0] = bad

        result = validate_ten_task_supervised_run(
            receipts,
            expected_trust_tier="tier-1",
            expected_approval_token_prefix="approval-token-plan-10-1-",
            now=self._now(),
        )

        self.assertFalse(result.passed)
        self.assertIn("unsafe_action_class:task-00", result.reasons)
        self.assertIn("wrong_trust_tier:task-00", result.reasons)
        self.assertIn("wrong_approval_token:task-00", result.reasons)
        self.assertIn("broad_exact_files:task-00", result.reasons)
        self.assertIn("receipt_path_must_be_docs:task-00", result.reasons)
        self.assertIn("task_not_passed:task-00", result.reasons)
        self.assertIn("verification_not_passed:task-00", result.reasons)
        self.assertIn("missing_rollback_guidance:task-00", result.reasons)
        self.assertIn("kill_switch_not_checked:task-00", result.reasons)
        self.assertIn("operator_supervision_missing:task-00", result.reasons)
        self.assertIn("human_review_missing:task-00", result.reasons)
        self.assertIn("invalid_false_positive_count:task-00", result.reasons)
        self.assertIn("invalid_false_negative_count:task-00", result.reasons)
        self.assertIn("next_task_auto_started:task-00", result.reasons)
        self.assertIn("background_loop_started:task-00", result.reasons)
        self.assertIn("completed_at_in_future:task-00", result.reasons)
        self.assertIn("soak_model_performed_forbidden_action:task-00", result.reasons)

    def test_supervised_run_blocks_duplicate_task_ids_and_receipts(self) -> None:
        receipts = [receipt.to_dict() for receipt in self._receipts()]
        receipts[1]["task_id"] = receipts[0]["task_id"]
        receipts[1]["receipt_path"] = receipts[0]["receipt_path"]

        result = validate_ten_task_supervised_run(
            receipts,
            expected_trust_tier="tier-1",
            expected_approval_token_prefix="approval-token-plan-10-1-",
            now=self._now(),
        )

        self.assertFalse(result.passed)
        self.assertIn("duplicate_task_id", result.reasons)
        self.assertIn("duplicate_receipt_path", result.reasons)

    def test_soak_status_api_is_preview_only(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/soak/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["api_preview_only"])
        self.assertEqual(payload["soak_status"]["phase"], TEN_TASK_SUPERVISED_RUN_PHASE)
        self.assertEqual(payload["validation"]["status"], "passed")
        self.assertEqual(payload["validation"]["task_count"], 10)
        self.assertEqual(
            payload["validation"]["supervised_trial_summary"]["schema_version"],
            "cartographer.supervised_daily_driver_trial_summary.v1",
        )
        self.assertEqual(payload["validation"]["first_supervised_receipt_path"], "docs/cartographer-live-receipts/task-00.md")
        self.assertFalse(payload["validation"]["supervised_trial_summary"]["authority_granted_by_summary"])
        self.assertFalse(payload["background_loop_enabled"])
        self.assertFalse(payload["queue_execution_enabled"])
        self.assertFalse(payload["task_execution_enabled"])
        self.assertFalse(payload["command_execution_enabled"])
        self.assertFalse(payload["safe_write_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])

    def test_twenty_four_hour_soak_status_is_bounded_validation_only(self) -> None:
        status = build_twenty_four_hour_soak_status()

        self.assertEqual(status["phase"], TWENTY_FOUR_HOUR_SOAK_PHASE)
        self.assertEqual(status["status"], "bounded-soak-validation-only")
        self.assertEqual(status["required_duration_hours"], 24)
        self.assertTrue(status["bounded_invocations_only"])
        self.assertTrue(status["false_positive_tracking_required"])
        self.assertTrue(status["false_negative_tracking_required"])
        self.assertTrue(status["stop_event_tracking_required"])
        self.assertTrue(status["operator_review_required"])
        self.assertFalse(status["background_loop_enabled"])
        self.assertFalse(status["hidden_loop_allowed"])
        self.assertFalse(status["queue_execution_enabled"])
        self.assertFalse(status["task_execution_enabled"])
        self.assertFalse(status["command_execution_enabled"])
        self.assertFalse(status["safe_write_enabled"])
        self.assertFalse(status["commit_enabled"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["durable_storage_written"])
        self.assertFalse(status["api_mutation_available"])

    def test_valid_twenty_four_hour_soak_accepts_bounded_samples_without_execution(self) -> None:
        result = validate_twenty_four_hour_soak(
            self._soak_samples(),
            requested_duration_hours=24,
            now=self._now(),
        )

        self.assertTrue(result.passed)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.requested_duration_hours, 24)
        self.assertEqual(result.sample_count, 3)
        self.assertEqual(result.sample_ids, ("sample-00", "sample-12", "sample-24"))
        self.assertTrue(result.bounded_invocations_only)
        self.assertTrue(result.false_positive_tracking_required)
        self.assertTrue(result.false_negative_tracking_required)
        self.assertTrue(result.stop_event_tracking_required)
        self.assertTrue(result.operator_review_required)
        self.assertFalse(result.background_loop_enabled)
        self.assertFalse(result.hidden_loop_allowed)
        self.assertFalse(result.queue_execution_enabled)
        self.assertFalse(result.task_execution_enabled)
        self.assertFalse(result.command_execution_enabled)
        self.assertFalse(result.safe_write_enabled)
        self.assertFalse(result.commit_enabled)
        self.assertFalse(result.push_enabled)
        self.assertFalse(result.durable_storage_written)
        self.assertFalse(result.api_mutation_available)

    def test_twenty_four_hour_soak_blocks_wrong_duration_and_missing_samples(self) -> None:
        result = validate_twenty_four_hour_soak((), requested_duration_hours=12, now=self._now())

        self.assertFalse(result.passed)
        self.assertIn("duration_must_be_exactly_24_hours", result.reasons)
        self.assertIn("missing_soak_samples", result.reasons)

    def test_twenty_four_hour_soak_blocks_hidden_loop_mutation_and_unbounded_activity(self) -> None:
        samples = list(self._soak_samples())
        bad = samples[1].to_dict()
        bad.update(
            {
                "hidden_loop_detected": True,
                "hidden_mutation_detected": True,
                "head_changed": True,
                "dirty_worktree_explained": False,
                "protected_lane_mutation_detected": True,
                "manual_intervention_required": True,
                "kill_switch_checked": False,
                "false_negative_count": 1,
                "stop_events": ("hidden mutation stop",),
                "operator_reviewed": False,
                "sampled_at": "2026-05-23T12:10:00Z",
                "queue_executed_by_soak_model": True,
            }
        )
        samples[1] = bad

        result = validate_twenty_four_hour_soak(samples, requested_duration_hours=24, now=self._now())

        self.assertFalse(result.passed)
        self.assertIn("kill_switch_not_checked:sample-12", result.reasons)
        self.assertIn("hidden_loop_detected:sample-12", result.reasons)
        self.assertIn("hidden_mutation_detected:sample-12", result.reasons)
        self.assertIn("head_changed:sample-12", result.reasons)
        self.assertIn("dirty_worktree_unexplained:sample-12", result.reasons)
        self.assertIn("protected_lane_mutation_detected:sample-12", result.reasons)
        self.assertIn("manual_intervention_required:sample-12", result.reasons)
        self.assertIn("false_negative_detected:sample-12", result.reasons)
        self.assertIn("stop_event_recorded:sample-12", result.reasons)
        self.assertIn("operator_review_missing:sample-12", result.reasons)
        self.assertIn("sampled_at_in_future:sample-12", result.reasons)
        self.assertIn("soak_model_performed_forbidden_action:sample-12", result.reasons)

    def test_twenty_four_hour_soak_blocks_duplicate_and_out_of_order_samples(self) -> None:
        samples = [sample.to_dict() for sample in self._soak_samples()]
        samples[1]["sample_id"] = samples[0]["sample_id"]
        samples[1]["hour"] = 24
        samples[2]["hour"] = 12

        result = validate_twenty_four_hour_soak(samples, requested_duration_hours=24, now=self._now())

        self.assertFalse(result.passed)
        self.assertIn("duplicate_sample_id", result.reasons)
        self.assertIn("sample_hours_not_increasing", result.reasons)

    def test_soak_status_api_includes_twenty_four_hour_preview_without_runtime_authority(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/soak/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["twenty_four_hour_soak_status"]["phase"], TWENTY_FOUR_HOUR_SOAK_PHASE)
        self.assertEqual(payload["twenty_four_hour_validation"]["status"], "passed")
        self.assertEqual(payload["twenty_four_hour_validation"]["sample_count"], 3)
        self.assertFalse(payload["background_loop_enabled"])
        self.assertFalse(payload["queue_execution_enabled"])
        self.assertFalse(payload["task_execution_enabled"])
        self.assertFalse(payload["command_execution_enabled"])

    def test_seventy_two_hour_soak_status_is_bounded_validation_only(self) -> None:
        status = build_seventy_two_hour_soak_status()

        self.assertEqual(status["phase"], SEVENTY_TWO_HOUR_SOAK_PHASE)
        self.assertEqual(status["status"], "bounded-soak-validation-only")
        self.assertEqual(status["required_duration_hours"], 72)
        self.assertTrue(status["drift_checks_required"])
        self.assertTrue(status["protected_lane_checks_required"])
        self.assertTrue(status["queue_checks_required"])
        self.assertTrue(status["bounded_invocations_only"])
        self.assertTrue(status["false_positive_tracking_required"])
        self.assertTrue(status["false_negative_tracking_required"])
        self.assertTrue(status["stop_event_tracking_required"])
        self.assertTrue(status["operator_review_required"])
        self.assertFalse(status["background_loop_enabled"])
        self.assertFalse(status["hidden_loop_allowed"])
        self.assertFalse(status["queue_execution_enabled"])
        self.assertFalse(status["task_execution_enabled"])
        self.assertFalse(status["command_execution_enabled"])
        self.assertFalse(status["safe_write_enabled"])
        self.assertFalse(status["commit_enabled"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["durable_storage_written"])
        self.assertFalse(status["api_mutation_available"])

    def test_valid_seventy_two_hour_soak_accepts_drift_protected_lane_and_queue_checks(self) -> None:
        result = validate_seventy_two_hour_soak(
            self._seventy_two_hour_samples(),
            requested_duration_hours=72,
            now=self._now(),
        )

        self.assertTrue(result.passed)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.requested_duration_hours, 72)
        self.assertEqual(result.sample_count, 4)
        self.assertEqual(result.sample_ids, ("sample-00", "sample-24", "sample-48", "sample-72"))
        self.assertTrue(result.drift_checks_required)
        self.assertTrue(result.protected_lane_checks_required)
        self.assertTrue(result.queue_checks_required)
        self.assertTrue(result.bounded_invocations_only)
        self.assertTrue(result.false_positive_tracking_required)
        self.assertTrue(result.false_negative_tracking_required)
        self.assertTrue(result.stop_event_tracking_required)
        self.assertTrue(result.operator_review_required)
        self.assertFalse(result.background_loop_enabled)
        self.assertFalse(result.hidden_loop_allowed)
        self.assertFalse(result.queue_execution_enabled)
        self.assertFalse(result.task_execution_enabled)
        self.assertFalse(result.command_execution_enabled)
        self.assertFalse(result.safe_write_enabled)
        self.assertFalse(result.commit_enabled)
        self.assertFalse(result.push_enabled)
        self.assertFalse(result.durable_storage_written)
        self.assertFalse(result.api_mutation_available)

    def test_seventy_two_hour_soak_blocks_wrong_duration_and_missing_terminal_sample(self) -> None:
        result = validate_seventy_two_hour_soak(
            self._soak_samples(),
            requested_duration_hours=24,
            now=self._now(),
        )

        self.assertFalse(result.passed)
        self.assertIn("duration_must_be_exactly_72_hours", result.reasons)
        self.assertIn("missing_hour_72_sample", result.reasons)

    def test_seventy_two_hour_soak_blocks_drift_protected_lane_and_queue_failures(self) -> None:
        samples = list(self._seventy_two_hour_samples())
        bad = samples[2].to_dict()
        bad.update(
            {
                "drift_status": "open",
                "protected_lane_status": "mutated",
                "queue_status": "wedged",
                "queue_depth": 3,
                "blocked_task_count": 2,
                "receipt_count": 9,
            }
        )
        samples[2] = bad

        result = validate_seventy_two_hour_soak(samples, requested_duration_hours=72, now=self._now())

        self.assertFalse(result.passed)
        self.assertIn("drift_not_clear:sample-48", result.reasons)
        self.assertIn("protected_lane_not_clear:sample-48", result.reasons)
        self.assertIn("queue_not_healthy:sample-48", result.reasons)
        self.assertIn("queue_depth_not_empty:sample-48", result.reasons)
        self.assertIn("blocked_tasks_present:sample-48", result.reasons)
        self.assertIn("receipt_count_below_supervised_run:sample-48", result.reasons)

    def test_soak_status_api_includes_seventy_two_hour_preview_without_runtime_authority(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/soak/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["seventy_two_hour_soak_status"]["phase"], SEVENTY_TWO_HOUR_SOAK_PHASE)
        self.assertEqual(payload["seventy_two_hour_validation"]["status"], "passed")
        self.assertEqual(payload["seventy_two_hour_validation"]["sample_count"], 4)
        self.assertFalse(payload["background_loop_enabled"])
        self.assertFalse(payload["queue_execution_enabled"])
        self.assertFalse(payload["task_execution_enabled"])
        self.assertFalse(payload["command_execution_enabled"])

    def test_kill_switch_rollback_drill_status_is_validation_only(self) -> None:
        status = build_kill_switch_rollback_drill_status()

        self.assertEqual(status["phase"], KILL_SWITCH_AND_ROLLBACK_DRILLS_PHASE)
        self.assertEqual(status["status"], "drill-validation-only")
        self.assertEqual(status["required_stages"], REQUIRED_KILL_SWITCH_DRILL_STAGES)
        self.assertTrue(status["rollback_guidance_required"])
        self.assertFalse(status["rollback_execution_enabled"])
        self.assertFalse(status["background_loop_enabled"])
        self.assertFalse(status["queue_execution_enabled"])
        self.assertFalse(status["task_execution_enabled"])
        self.assertFalse(status["command_execution_enabled"])
        self.assertFalse(status["safe_write_enabled"])
        self.assertFalse(status["commit_enabled"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["durable_storage_written"])
        self.assertFalse(status["api_mutation_available"])

    def test_valid_kill_switch_rollback_drills_accept_all_required_stages(self) -> None:
        result = validate_kill_switch_rollback_drills(self._kill_switch_drills(), now=self._now())

        self.assertTrue(result.passed)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.drill_count, 4)
        self.assertEqual(result.required_stages, REQUIRED_KILL_SWITCH_DRILL_STAGES)
        self.assertFalse(result.rollback_execution_enabled)
        self.assertFalse(result.background_loop_enabled)
        self.assertFalse(result.queue_execution_enabled)
        self.assertFalse(result.task_execution_enabled)
        self.assertFalse(result.command_execution_enabled)
        self.assertFalse(result.safe_write_enabled)
        self.assertFalse(result.commit_enabled)
        self.assertFalse(result.push_enabled)
        self.assertFalse(result.durable_storage_written)
        self.assertFalse(result.api_mutation_available)

    def test_kill_switch_rollback_drills_require_all_required_stages(self) -> None:
        result = validate_kill_switch_rollback_drills(
            self._kill_switch_drills()[:3],
            now=self._now(),
        )

        self.assertFalse(result.passed)
        self.assertIn("missing_required_drill_stage:before_commit_push", result.reasons)

    def test_kill_switch_rollback_drills_fail_closed_for_missing_blocks_and_forbidden_actions(self) -> None:
        drills = [drill.to_dict() for drill in self._kill_switch_drills()]
        bad = drills[1]
        bad.update(
            {
                "kill_switch_engaged": False,
                "action_blocked": False,
                "queue_execution_blocked": False,
                "task_execution_blocked": False,
                "command_execution_blocked": False,
                "write_blocked": False,
                "commit_blocked": False,
                "push_blocked": False,
                "rollback_guidance": "",
                "receipt_path": "source_proxy/drill.md",
                "verified_at": "2026-05-23T12:10:00Z",
                "rollback_executed_by_drill_model": True,
                "mutation_performed_by_drill_model": True,
            }
        )

        result = validate_kill_switch_rollback_drills(drills, now=self._now())

        self.assertFalse(result.passed)
        self.assertIn("kill_switch_not_engaged:drill-mid-workflow", result.reasons)
        self.assertIn("action_blocked_missing:drill-mid-workflow", result.reasons)
        self.assertIn("queue_execution_blocked_missing:drill-mid-workflow", result.reasons)
        self.assertIn("task_execution_blocked_missing:drill-mid-workflow", result.reasons)
        self.assertIn("command_execution_blocked_missing:drill-mid-workflow", result.reasons)
        self.assertIn("write_blocked_missing:drill-mid-workflow", result.reasons)
        self.assertIn("commit_blocked_missing:drill-mid-workflow", result.reasons)
        self.assertIn("push_blocked_missing:drill-mid-workflow", result.reasons)
        self.assertIn("missing_rollback_guidance:drill-mid-workflow", result.reasons)
        self.assertIn("receipt_path_must_be_docs:drill-mid-workflow", result.reasons)
        self.assertIn("verified_at_in_future:drill-mid-workflow", result.reasons)
        self.assertIn("rollback_executed_by_drill_model:drill-mid-workflow", result.reasons)
        self.assertIn("mutation_performed_by_drill_model:drill-mid-workflow", result.reasons)

    def test_kill_switch_rollback_drills_block_duplicate_stage_and_ids(self) -> None:
        drills = [drill.to_dict() for drill in self._kill_switch_drills()]
        drills[1]["drill_id"] = drills[0]["drill_id"]
        drills[1]["stage"] = drills[0]["stage"]

        result = validate_kill_switch_rollback_drills(drills, now=self._now())

        self.assertFalse(result.passed)
        self.assertIn("duplicate_drill_id", result.reasons)
        self.assertIn("duplicate_drill_stage", result.reasons)
        self.assertIn("missing_required_drill_stage:mid_workflow", result.reasons)

    def test_soak_status_api_includes_kill_switch_drill_preview_without_runtime_authority(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/soak/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["kill_switch_drill_status"]["phase"], KILL_SWITCH_AND_ROLLBACK_DRILLS_PHASE)
        self.assertEqual(payload["kill_switch_drill_validation"]["status"], "passed")
        self.assertEqual(payload["kill_switch_drill_validation"]["drill_count"], 4)
        self.assertFalse(payload["background_loop_enabled"])
        self.assertFalse(payload["queue_execution_enabled"])
        self.assertFalse(payload["task_execution_enabled"])
        self.assertFalse(payload["command_execution_enabled"])

    def test_promotion_decision_status_is_record_validation_only(self) -> None:
        status = build_promotion_decision_status()

        self.assertEqual(status["phase"], PROMOTION_DECISION_PHASE)
        self.assertEqual(status["status"], "decision-record-validation-only")
        self.assertEqual(status["promotion_tiers"], PROMOTION_TIERS)
        self.assertTrue(status["decision_packet_available"])
        self.assertTrue(status["activation_requires_plan_12_explicit_approval"])
        self.assertFalse(status["authority_granted_by_record"])
        self.assertFalse(status["limited_daily_driver_activation_allowed"])
        self.assertFalse(status["background_loop_enabled"])
        self.assertFalse(status["queue_execution_enabled"])
        self.assertFalse(status["task_execution_enabled"])
        self.assertFalse(status["command_execution_enabled"])
        self.assertFalse(status["safe_write_enabled"])
        self.assertFalse(status["commit_enabled"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["durable_storage_written"])
        self.assertFalse(status["api_mutation_available"])
        self.assertFalse(status["self_promotion_allowed"])

    def test_promotion_decision_records_exact_tier_and_allowed_actions_without_granting_authority(self) -> None:
        decision = record_promotion_decision(
            tier="tier-1",
            allowed_actions=PROMOTION_TIERS["tier-1"],
            decided_by="Britton",
            ten_task_validation=self._ten_task_validation(),
            twenty_four_hour_validation=self._twenty_four_hour_validation(),
            seventy_two_hour_validation=self._seventy_two_hour_validation(),
            kill_switch_drill_validation=self._kill_switch_drill_validation(),
            authority_change_requested=False,
            now=self._now(),
        )

        self.assertEqual(decision.phase, PROMOTION_DECISION_PHASE)
        self.assertEqual(decision.status, "recorded")
        self.assertTrue(decision.recorded)
        self.assertFalse(decision.blocked)
        self.assertEqual(decision.reasons, ())
        self.assertEqual(decision.tier, "tier-1")
        self.assertEqual(decision.allowed_actions, PROMOTION_TIERS["tier-1"])
        self.assertEqual(decision.decided_by, "Britton")
        self.assertEqual(decision.evidence["ten_task"], "passed")
        self.assertEqual(
            decision.decision_packet["schema_version"],
            "cartographer.promotion_decision_packet.v1",
        )
        self.assertEqual(decision.decision_packet["status"], "recorded")
        self.assertEqual(decision.decision_packet["tier"], "tier-1")
        self.assertTrue(decision.decision_packet["britton_manual_decision_required"])
        self.assertTrue(decision.decision_packet["plan_12_explicit_approval_required"])
        self.assertFalse(decision.decision_packet["authority_granted_by_packet"])
        self.assertFalse(decision.decision_packet["daily_driver_active"])
        self.assertFalse(decision.decision_packet["limited_daily_driver_activation_allowed"])
        self.assertFalse(decision.decision_packet["background_loop_enabled"])
        self.assertFalse(decision.decision_packet["queue_execution_enabled"])
        self.assertFalse(decision.decision_packet["task_execution_enabled"])
        self.assertFalse(decision.decision_packet["safe_write_enabled"])
        self.assertFalse(decision.decision_packet["commit_enabled"])
        self.assertFalse(decision.decision_packet["push_enabled"])
        self.assertFalse(decision.decision_packet["self_promotion_allowed"])
        self.assertFalse(decision.authority_change_requested)
        self.assertFalse(decision.authority_granted_by_record)
        self.assertTrue(decision.activation_requires_plan_12_explicit_approval)
        self.assertFalse(decision.limited_daily_driver_activation_allowed)
        self.assertFalse(decision.background_loop_enabled)
        self.assertFalse(decision.queue_execution_enabled)
        self.assertFalse(decision.task_execution_enabled)
        self.assertFalse(decision.command_execution_enabled)
        self.assertFalse(decision.safe_write_enabled)
        self.assertFalse(decision.commit_enabled)
        self.assertFalse(decision.push_enabled)
        self.assertFalse(decision.durable_storage_written)
        self.assertFalse(decision.api_mutation_available)
        self.assertFalse(decision.self_promotion_allowed)

    def test_promotion_decision_blocks_unknown_tier_and_disallowed_actions(self) -> None:
        decision = record_promotion_decision(
            tier="tier-1",
            allowed_actions=("auto_safe_docs", "auto_local_commit", "auto_isolated_branch_push"),
            decided_by="Britton",
            ten_task_validation=self._ten_task_validation(),
            twenty_four_hour_validation=self._twenty_four_hour_validation(),
            seventy_two_hour_validation=self._seventy_two_hour_validation(),
            kill_switch_drill_validation=self._kill_switch_drill_validation(),
            authority_change_requested=False,
            now=self._now(),
        )

        self.assertFalse(decision.recorded)
        self.assertIn("action_not_allowed_for_tier:auto_local_commit", decision.reasons)
        self.assertIn("action_not_allowed_for_tier:auto_isolated_branch_push", decision.reasons)
        self.assertFalse(decision.authority_granted_by_record)

    def test_promotion_decision_blocks_missing_evidence_self_promotion_and_authority_change(self) -> None:
        blocked_evidence = self._ten_task_validation().to_dict()
        blocked_evidence["status"] = "blocked"
        decision = record_promotion_decision(
            tier="tier-2",
            allowed_actions=PROMOTION_TIERS["tier-2"],
            decided_by="cartographer",
            ten_task_validation=blocked_evidence,
            twenty_four_hour_validation=self._twenty_four_hour_validation(),
            seventy_two_hour_validation=self._seventy_two_hour_validation(),
            kill_switch_drill_validation=self._kill_switch_drill_validation(),
            authority_change_requested=True,
            now=self._now(),
        )

        self.assertFalse(decision.recorded)
        self.assertIn("self_promotion_blocked", decision.reasons)
        self.assertIn("required_evidence_not_passed:ten_task", decision.reasons)
        self.assertIn("authority_change_requires_separate_implementation_approval", decision.reasons)
        self.assertFalse(decision.authority_granted_by_record)

    def test_promotion_decision_blocks_duplicate_or_empty_allowed_actions(self) -> None:
        duplicate = record_promotion_decision(
            tier="tier-1",
            allowed_actions=("auto_safe_docs", "auto_safe_docs"),
            decided_by="Britton",
            ten_task_validation=self._ten_task_validation(),
            twenty_four_hour_validation=self._twenty_four_hour_validation(),
            seventy_two_hour_validation=self._seventy_two_hour_validation(),
            kill_switch_drill_validation=self._kill_switch_drill_validation(),
            authority_change_requested=False,
            now=self._now(),
        )
        missing = record_promotion_decision(
            tier="tier-1",
            allowed_actions=(),
            decided_by="Britton",
            ten_task_validation=self._ten_task_validation(),
            twenty_four_hour_validation=self._twenty_four_hour_validation(),
            seventy_two_hour_validation=self._seventy_two_hour_validation(),
            kill_switch_drill_validation=self._kill_switch_drill_validation(),
            authority_change_requested=False,
            now=self._now(),
        )

        self.assertIn("duplicate_allowed_action", duplicate.reasons)
        self.assertIn("missing_allowed_actions", missing.reasons)

    def test_soak_status_api_includes_promotion_decision_preview_without_authority_grant(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/soak/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["promotion_decision_status"]["phase"], PROMOTION_DECISION_PHASE)
        self.assertEqual(payload["promotion_decision"]["status"], "recorded")
        self.assertEqual(payload["promotion_decision"]["tier"], "tier-1")
        self.assertEqual(
            payload["promotion_decision"]["decision_packet"]["schema_version"],
            "cartographer.promotion_decision_packet.v1",
        )
        self.assertFalse(payload["promotion_decision"]["decision_packet"]["daily_driver_active"])
        self.assertTrue(payload["promotion_decision"]["decision_packet"]["plan_12_explicit_approval_required"])
        self.assertFalse(payload["promotion_decision"]["authority_granted_by_record"])
        self.assertFalse(payload["background_loop_enabled"])
        self.assertFalse(payload["queue_execution_enabled"])
        self.assertFalse(payload["task_execution_enabled"])
        self.assertFalse(payload["command_execution_enabled"])

    def test_module_exposes_no_runtime_execution_write_git_api_mutation_or_storage_surface(self) -> None:
        source = inspect.getsource(soak_promotion)
        forbidden_fragments = (
            "subprocess",
            "os.system",
            "Path(",
            "open(",
            ".write(",
            "write_text(",
            "source_proxy.api",
            "requests",
            "urllib",
            "socket",
            "git add",
            "git commit",
            "git push",
            "git merge",
            "git branch",
            "git worktree",
            "git stash",
            "git clean",
            "git reset",
            "git checkout",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    @staticmethod
    def _receipts() -> tuple[SupervisedSafeTaskReceipt, ...]:
        return tuple(
            SupervisedSafeTaskReceipt(
                task_id=f"task-{index:02d}",
                action_class=("docs", "evidence", "receipt")[index % 3],
                trust_tier="tier-1",
                approval_token_id=f"approval-token-plan-10-1-{index:02d}",
                exact_files=(f"docs/cartographer-live-receipts/task-{index:02d}.md",),
                receipt_path=f"docs/cartographer-live-receipts/task-{index:02d}.md",
                status="passed",
                verification=DailyDriverSoakVerification(
                    status="passed",
                    checks=("manual_supervision", "receipt_review", "git diff --check"),
                    checked_at="2026-05-23T12:00:00Z",
                ).to_dict(),
                rollback_guidance="No automated rollback. Review receipt and rerun supervised task if needed.",
                kill_switch_checked=True,
                operator_supervised=True,
                started_at="2026-05-23T11:50:00Z",
                completed_at="2026-05-23T12:00:00Z",
            )
            for index in range(10)
        )

    @staticmethod
    def _soak_samples() -> tuple[TwentyFourHourSoakSample, ...]:
        return tuple(
            TwentyFourHourSoakSample(
                sample_id=f"sample-{hour:02d}",
                hour=hour,
                bounded_invocation_count=hour // 12,
                queue_depth=0,
                blocked_task_count=0,
                receipt_count=10,
                kill_switch_checked=True,
                hidden_loop_detected=False,
                hidden_mutation_detected=False,
                head_changed=False,
                dirty_worktree_explained=True,
                protected_lane_mutation_detected=False,
                manual_intervention_required=False,
                sampled_at=f"2026-05-23T{hour // 2:02d}:00:00Z",
            )
            for hour in (0, 12, 24)
        )

    @staticmethod
    def _seventy_two_hour_samples() -> tuple[TwentyFourHourSoakSample, ...]:
        return tuple(
            TwentyFourHourSoakSample(
                sample_id=f"sample-{hour:02d}",
                hour=hour,
                bounded_invocation_count=hour // 24,
                queue_depth=0,
                blocked_task_count=0,
                receipt_count=10,
                kill_switch_checked=True,
                hidden_loop_detected=False,
                hidden_mutation_detected=False,
                head_changed=False,
                dirty_worktree_explained=True,
                protected_lane_mutation_detected=False,
                manual_intervention_required=False,
                sampled_at=f"2026-05-{20 + hour // 24:02d}T00:00:00Z",
                drift_status="clear",
                protected_lane_status="clear",
                queue_status="healthy",
            )
            for hour in (0, 24, 48, 72)
        )

    @staticmethod
    def _kill_switch_drills() -> tuple[KillSwitchRollbackDrill, ...]:
        return tuple(
            KillSwitchRollbackDrill(
                drill_id=f"drill-{stage.replace('_', '-')}",
                stage=stage,
                kill_switch_engaged=True,
                action_blocked=True,
                queue_execution_blocked=True,
                task_execution_blocked=True,
                command_execution_blocked=True,
                write_blocked=True,
                commit_blocked=True,
                push_blocked=True,
                rollback_guidance="No automated rollback was executed; preserve receipt and restore only with operator approval.",
                receipt_path=f"docs/cartographer-live-receipts/kill-switch-{stage}.md",
                verified_at="2026-05-23T12:00:00Z",
            )
            for stage in REQUIRED_KILL_SWITCH_DRILL_STAGES
        )

    @staticmethod
    def _ten_task_validation():
        return validate_ten_task_supervised_run(
            CartographerDailyDriverSoakTests._receipts(),
            expected_trust_tier="tier-1",
            expected_approval_token_prefix="approval-token-plan-10-1-",
            now=CartographerDailyDriverSoakTests._now(),
        )

    @staticmethod
    def _twenty_four_hour_validation():
        return validate_twenty_four_hour_soak(
            CartographerDailyDriverSoakTests._soak_samples(),
            requested_duration_hours=24,
            now=CartographerDailyDriverSoakTests._now(),
        )

    @staticmethod
    def _seventy_two_hour_validation():
        return validate_seventy_two_hour_soak(
            CartographerDailyDriverSoakTests._seventy_two_hour_samples(),
            requested_duration_hours=72,
            now=CartographerDailyDriverSoakTests._now(),
        )

    @staticmethod
    def _kill_switch_drill_validation():
        return validate_kill_switch_rollback_drills(
            CartographerDailyDriverSoakTests._kill_switch_drills(),
            now=CartographerDailyDriverSoakTests._now(),
        )

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 23, 12, 5, tzinfo=UTC)


def _test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(cartographer_router)
    return test_app


if __name__ == "__main__":
    unittest.main()
