from __future__ import annotations

from datetime import UTC, datetime, timedelta
import inspect
import unittest

from source_proxy.cartographer import safe_task_queue
from source_proxy.cartographer.safe_task_queue import (
    DEFAULT_SAFE_TASK_RETRY_DELAY_SECONDS,
    DEFAULT_SAFE_TASK_TIMEOUT_SECONDS,
    MAX_SAFE_TASK_ATTEMPTS,
    MAX_SAFE_TASK_TIMEOUT_SECONDS,
    PLAN_7_SAFE_TASK_CLASSES,
    SAFE_TASK_CLASS_MODES,
    SAFE_TASK_CLASS_TRUST_TIERS,
    SAFE_TASK_STATUSES,
    SAFE_TASK_TRUST_TIER,
    SafeTaskRecord,
    build_safe_task_queue_model_status,
    drill_safe_task_kill_switch,
    run_first_auto_selected_safe_task,
    select_next_safe_task,
    validate_safe_task_record,
)


class CartographerSafeTaskQueueModelTests(unittest.TestCase):
    def test_status_is_model_only_and_grants_no_authority(self) -> None:
        status = build_safe_task_queue_model_status()

        self.assertEqual(status["status"], "model-only")
        self.assertEqual(status["task_statuses"], SAFE_TASK_STATUSES)
        self.assertEqual(status["allowed_task_classes"], PLAN_7_SAFE_TASK_CLASSES)
        self.assertEqual(status["task_class_trust_tiers"], SAFE_TASK_CLASS_TRUST_TIERS)
        self.assertEqual(status["task_class_modes"], SAFE_TASK_CLASS_MODES)
        self.assertEqual(status["required_trust_tier"], SAFE_TASK_TRUST_TIER)
        self.assertEqual(status["max_attempts"], MAX_SAFE_TASK_ATTEMPTS)
        self.assertEqual(status["max_timeout_seconds"], MAX_SAFE_TASK_TIMEOUT_SECONDS)
        self.assertEqual(status["default_timeout_seconds"], DEFAULT_SAFE_TASK_TIMEOUT_SECONDS)
        self.assertEqual(status["default_retry_delay_seconds"], DEFAULT_SAFE_TASK_RETRY_DELAY_SECONDS)
        self.assertTrue(status["run_next_endpoint_available"])
        self.assertEqual(status["plan"], "Cartographer Integrated Control Master Plan 7/10")
        self.assertEqual(status["kill_switch_drill_phase"], "Plan 7 Phase 7.2: Kill switch drill")
        self.assertEqual(status["first_run_phase"], "Plan 7 legacy first-run receipt disabled")
        self.assertFalse(status["first_run_available"])
        self.assertTrue(status["receipt_available"])
        self.assertTrue(status["selection_receipt_available"])
        self.assertTrue(status["one_task_only"])
        self.assertFalse(status["durable_storage_available"])
        self.assertFalse(status["selection_available"])
        self.assertFalse(status["execution_available"])
        self.assertFalse(status["queue_worker_available"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["verification_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])
        self.assertFalse(status["token_minting_available"])
        self.assertFalse(status["approval_storage_available"])

    def test_record_captures_phase_7_1_fields_as_data(self) -> None:
        record = self._record()
        payload = record.to_dict()

        self.assertEqual(payload["task_id"], "task-1")
        self.assertEqual(payload["task_class"], "safe_docs_evidence_maintenance")
        self.assertEqual(payload["trust_tier"], SAFE_TASK_TRUST_TIER)
        self.assertEqual(payload["approval_token_id"], "approval-token-plan-7-phase-1")
        self.assertEqual(payload["allowed_files"], ("docs/cartographer-live-evidence/example.md",))
        self.assertEqual(payload["forbidden_files"], ("source_proxy/api/cartographer.py",))
        self.assertEqual(payload["status"], "pending")
        self.assertEqual(payload["attempts"], 0)
        self.assertEqual(payload["created_at"], "2026-05-22T11:55:00Z")
        self.assertIsNone(payload["selected_at"])
        self.assertIsNone(payload["completed_at"])
        self.assertEqual(payload["timeout_seconds"], DEFAULT_SAFE_TASK_TIMEOUT_SECONDS)
        self.assertEqual(
            payload["retry_policy"],
            {
                "max_attempts": MAX_SAFE_TASK_ATTEMPTS,
                "retry_delay_seconds": DEFAULT_SAFE_TASK_RETRY_DELAY_SECONDS,
            },
        )
        self.assertIsNone(payload["cancelled_at"])
        self.assertIsNone(payload["cancellation_reason"])
        self.assertIsNone(payload["blocked_reason"])
        self.assertTrue(payload["model_only"])
        self.assertFalse(payload["durable_storage_available"])
        self.assertFalse(payload["selection_available"])
        self.assertFalse(payload["execution_available"])

    def test_valid_record_accepts_without_selecting_or_executing(self) -> None:
        result = validate_safe_task_record(
            self._record(),
            expected_approval_token_id="approval-token-plan-7-phase-1",
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.task_id, "task-1")
        self.assertEqual(result.task_class, "safe_docs_evidence_maintenance")
        self.assertEqual(result.trust_tier, SAFE_TASK_TRUST_TIER)
        self.assertEqual(result.approval_token_id, "approval-token-plan-7-phase-1")
        self.assertEqual(result.task_status, "pending")
        self.assertEqual(result.attempts, 0)
        self.assertEqual(result.timeout_seconds, DEFAULT_SAFE_TASK_TIMEOUT_SECONDS)
        self.assertEqual(
            result.retry_policy,
            {
                "max_attempts": MAX_SAFE_TASK_ATTEMPTS,
                "retry_delay_seconds": DEFAULT_SAFE_TASK_RETRY_DELAY_SECONDS,
            },
        )
        self.assertIsNone(result.cancelled_at)
        self.assertIsNone(result.cancellation_reason)
        self.assertTrue(result.model_only)
        self.assertFalse(result.durable_storage_available)
        self.assertFalse(result.selection_available)
        self.assertFalse(result.execution_available)
        self.assertFalse(result.queue_worker_available)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.git_mutation_authority_granted)
        self.assertFalse(result.token_minting_available)
        self.assertFalse(result.approval_storage_available)

    def test_required_fields_fail_closed(self) -> None:
        for field in (
            "task_id",
            "task_class",
            "trust_tier",
            "approval_token_id",
            "allowed_files",
            "forbidden_files",
            "status",
            "attempts",
            "created_at",
            "selected_at",
            "completed_at",
            "timeout_seconds",
            "retry_policy",
            "cancelled_at",
            "cancellation_reason",
            "blocked_reason",
        ):
            payload = self._record().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_safe_task_record(
                    payload,
                    expected_approval_token_id="approval-token-plan-7-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertTrue(result.blocked)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_task_class_trust_tier_and_approval_token_must_match_exactly(self) -> None:
        cases = [
            ({"task_class": "queue_model_validation_only"}, "unknown_task_class"),
            ({"trust_tier": "tier-2"}, "wrong_trust_tier"),
            ({"approval_token_id": "other-token"}, "wrong_approval_token"),
            ({}, "missing_expected_approval_token_id"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_safe_task_record(
                    {**self._record().to_dict(), **override},
                    expected_approval_token_id="" if reason == "missing_expected_approval_token_id" else "approval-token-plan-7-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_all_phase_7_2_task_classes_are_trust_tier_locked_data_only(self) -> None:
        expected_classes = (
            "safe_docs_evidence_maintenance",
            "safe_receipt_closeout",
            "safe_project_health_snapshot",
            "safe_blueprint_refresh_proposal_only",
            "safe_stale_plan_summary_proposal_only",
        )

        self.assertEqual(PLAN_7_SAFE_TASK_CLASSES, expected_classes)
        self.assertEqual(set(SAFE_TASK_CLASS_TRUST_TIERS), set(expected_classes))
        self.assertEqual(set(SAFE_TASK_CLASS_MODES), set(expected_classes))

        for task_class in expected_classes:
            with self.subTest(task_class=task_class):
                result = validate_safe_task_record(
                    self._record(task_class=task_class),
                    expected_approval_token_id="approval-token-plan-7-phase-1",
                    now=self._now(),
                )

                self.assertTrue(result.accepted)
                self.assertEqual(result.trust_tier, SAFE_TASK_CLASS_TRUST_TIERS[task_class])
                self.assertTrue(result.model_only)
                self.assertFalse(result.selection_available)
                self.assertFalse(result.execution_available)
                self.assertFalse(result.write_authority_granted)

    def test_known_task_class_rejects_wrong_class_trust_tier(self) -> None:
        result = validate_safe_task_record(
            self._record(trust_tier="tier-2"),
            expected_trust_tier="tier-2",
            expected_approval_token_id="approval-token-plan-7-phase-1",
            now=self._now(),
        )

        self.assertFalse(result.accepted)
        self.assertIn("wrong_task_class_trust_tier", result.reasons)

    def test_run_next_selects_exactly_one_eligible_pending_task_as_data(self) -> None:
        first = self._record(task_id="task-1")
        second = self._record(task_id="task-2", task_class="safe_receipt_closeout")

        result = select_next_safe_task(
            [first, second],
            expected_approval_token_id="approval-token-plan-7-phase-1",
            now=self._now(),
        )

        self.assertTrue(result.selected)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "selected")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.selected_count, 1)
        self.assertEqual(result.eligible_count, 2)
        self.assertEqual(result.evaluated_count, 2)
        self.assertEqual(result.selected_task_id, "task-1")
        self.assertIsNotNone(result.selected_task)
        self.assertEqual(result.selected_task["status"], "selected")
        self.assertEqual(result.selected_task["selected_at"], "2026-05-22T12:00:00Z")
        self.assertIsNotNone(result.selection_receipt)
        self.assertEqual(
            result.selection_receipt["schema_version"],
            "cartographer.safe_task_selection_receipt.v1",
        )
        self.assertEqual(result.selection_receipt["task_id"], "task-1")
        self.assertEqual(result.selection_receipt["selected_count"], 1)
        self.assertEqual(result.selection_receipt["eligible_count"], 2)
        self.assertEqual(result.selection_receipt["rejected_count"], 0)
        self.assertEqual(result.selection_receipt["evaluated_count"], 2)
        self.assertEqual(
            result.selection_receipt["approval_token_id"],
            "approval-token-plan-7-phase-1",
        )
        self.assertFalse(result.selection_receipt["background_loop_started"])
        self.assertFalse(result.selection_receipt["task_execution_performed"])
        self.assertFalse(result.selection_receipt["safe_write_performed"])
        self.assertFalse(result.selection_receipt["verification_run_performed"])
        self.assertFalse(result.selection_receipt["command_run_performed"])
        self.assertFalse(result.selection_receipt["git_mutation_performed"])
        self.assertFalse(result.selection_receipt["durable_storage_performed"])
        self.assertTrue(result.model_only)
        self.assertFalse(result.durable_storage_available)
        self.assertFalse(result.execution_available)
        self.assertFalse(result.queue_worker_available)
        self.assertFalse(result.background_loop_available)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.git_mutation_authority_granted)
        self.assertEqual(first.status, "pending")
        self.assertIsNone(first.selected_at)

    def test_one_task_selection_never_selects_more_than_one_task(self) -> None:
        result = select_next_safe_task(
            [
                self._record(task_id="task-1"),
                self._record(task_id="task-2"),
                self._record(task_id="task-3"),
            ],
            expected_approval_token_id="approval-token-plan-7-phase-1",
            now=self._now(),
        )

        self.assertTrue(result.selected)
        self.assertEqual(result.selected_count, 1)
        self.assertEqual(result.eligible_count, 3)
        self.assertEqual(result.selected_task_id, "task-1")
        self.assertFalse(result.execution_available)
        self.assertFalse(result.queue_worker_available)
        self.assertFalse(result.background_loop_available)

    def test_run_next_blocks_empty_malformed_kill_switch_and_ineligible_queues(self) -> None:
        cases = [
            ([], {}, "empty_queue"),
            ("not-a-queue", {}, "malformed_queue_records"),
            ([self._record()], {"kill_switch_active": True}, "kill_switch_active"),
            ([self._record(status="selected", selected_at="2026-05-22T11:59:00Z")], {}, "no_eligible_pending_task"),
            ([self._record(approval_token_id="wrong-token")], {}, "no_eligible_pending_task"),
        ]

        for records, kwargs, reason in cases:
            with self.subTest(reason=reason):
                result = select_next_safe_task(
                    records,
                    expected_approval_token_id="approval-token-plan-7-phase-1",
                    now=self._now(),
                    **kwargs,
                )

                self.assertFalse(result.selected)
                self.assertTrue(result.blocked)
                self.assertEqual(result.selected_count, 0)
                self.assertIsNone(result.selected_task)
                self.assertIsNone(result.selection_receipt)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.execution_available)
                self.assertFalse(result.write_authority_granted)

    def test_kill_switch_drill_blocks_selection_execution_resume_retry_closeout_and_verification(self) -> None:
        result = drill_safe_task_kill_switch(
            [self._record()],
            expected_approval_token_id="approval-token-plan-7-phase-1",
            now=self._now(),
        )

        self.assertTrue(result.passed)
        self.assertTrue(result.blocked)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.selected_task_id, "task-1")
        self.assertEqual(
            tuple(checkpoint["checkpoint"] for checkpoint in result.checkpoints),
            (
                "before_selection",
                "after_selection",
                "before_execution",
                "before_resume",
                "before_retry",
                "before_closeout",
                "before_write_verification",
            ),
        )
        for checkpoint in result.checkpoints:
            with self.subTest(checkpoint=checkpoint["checkpoint"]):
                self.assertTrue(checkpoint["blocked"])
                self.assertFalse(checkpoint["execution_available"])
                self.assertFalse(checkpoint["queue_authority_granted"])
                self.assertFalse(checkpoint["workflow_execution_authority_granted"])
                self.assertFalse(checkpoint["closeout_authority_granted"])
                self.assertFalse(checkpoint["write_authority_granted"])
                self.assertFalse(checkpoint["verification_authority_granted"])
                self.assertFalse(checkpoint["command_authority_granted"])
                self.assertFalse(checkpoint["git_mutation_authority_granted"])
        self.assertEqual(result.checkpoints[0]["selected_task_id"], None)
        for checkpoint in result.checkpoints[1:]:
            self.assertEqual(checkpoint["selected_task_id"], "task-1")
        self.assertIn("kill_switch_active", result.checkpoints[0]["reasons"])
        expected_reasons = {
            "after_selection": "kill_switch_active_after_selection",
            "before_execution": "kill_switch_active_before_execution",
            "before_resume": "kill_switch_active_before_resume",
            "before_retry": "kill_switch_active_before_retry",
            "before_closeout": "kill_switch_active_before_closeout",
            "before_write_verification": "kill_switch_active_before_write_verification",
        }
        by_checkpoint = {checkpoint["checkpoint"]: checkpoint for checkpoint in result.checkpoints}
        for checkpoint_name, reason in expected_reasons.items():
            self.assertIn(reason, by_checkpoint[checkpoint_name]["reasons"])
        self.assertTrue(result.model_only)
        self.assertFalse(result.durable_storage_available)
        self.assertFalse(result.execution_available)
        self.assertFalse(result.queue_worker_available)
        self.assertFalse(result.background_loop_available)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.verification_authority_granted)
        self.assertFalse(result.git_mutation_authority_granted)

    def test_kill_switch_drill_fails_closed_when_no_task_can_be_selected_for_later_checkpoints(self) -> None:
        result = drill_safe_task_kill_switch(
            [self._record(status="selected", selected_at="2026-05-22T11:59:00Z")],
            expected_approval_token_id="approval-token-plan-7-phase-1",
            now=self._now(),
        )

        self.assertFalse(result.passed)
        self.assertTrue(result.blocked)
        self.assertEqual(result.status, "failed")
        self.assertIn("checkpoint_not_blocked:after_selection", result.reasons)
        self.assertIn("checkpoint_not_blocked:before_execution", result.reasons)
        self.assertIn("checkpoint_not_blocked:before_resume", result.reasons)
        self.assertIn("checkpoint_not_blocked:before_retry", result.reasons)
        self.assertIn("checkpoint_not_blocked:before_closeout", result.reasons)
        self.assertIn("checkpoint_not_blocked:before_write_verification", result.reasons)
        self.assertIsNone(result.selected_task_id)
        self.assertFalse(result.execution_available)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.verification_authority_granted)

    def test_first_auto_selected_safe_task_run_is_disabled_and_does_not_select(self) -> None:
        result = run_first_auto_selected_safe_task(
            [
                self._record(task_id="task-1", task_class="safe_blueprint_refresh_proposal_only"),
                self._record(task_id="task-2", task_class="safe_stale_plan_summary_proposal_only"),
            ],
            expected_approval_token_id="approval-token-plan-7-phase-1",
            now=self._now(),
        )

        self.assertFalse(result.completed)
        self.assertTrue(result.blocked)
        self.assertEqual(result.status, "blocked")
        self.assertIn("run_selected_task_disabled", result.reasons)
        self.assertIsNone(result.selected_task_id)
        self.assertEqual(result.selected_count, 0)
        self.assertEqual(result.completed_count, 0)
        self.assertEqual(result.selection["eligible_count"], 0)
        self.assertIsNone(result.receipt)
        self.assertFalse(result.source_write_performed)
        self.assertFalse(result.safe_write_performed)
        self.assertFalse(result.verification_run_performed)
        self.assertFalse(result.command_run_performed)
        self.assertFalse(result.git_mutation_performed)
        self.assertFalse(result.durable_storage_available)
        self.assertFalse(result.queue_worker_available)
        self.assertFalse(result.background_loop_available)

    def test_first_run_blocks_without_selecting_when_kill_switch_or_legacy_run_requested(self) -> None:
        cases = [
            (
                [self._record(task_class="safe_blueprint_refresh_proposal_only")],
                {"expected_approval_token_id": "wrong-token"},
                "run_selected_task_disabled",
            ),
            (
                [self._record(task_class="safe_blueprint_refresh_proposal_only")],
                {"kill_switch_active": True},
                "kill_switch_active",
            ),
            (
                [self._record(task_class="safe_docs_evidence_maintenance")],
                {},
                "run_selected_task_disabled",
            ),
        ]

        for records, kwargs, reason in cases:
            with self.subTest(reason=reason):
                result = run_first_auto_selected_safe_task(
                    records,
                    expected_approval_token_id=kwargs.pop("expected_approval_token_id", "approval-token-plan-7-phase-1"),
                    now=self._now(),
                    **kwargs,
                )

                self.assertFalse(result.completed)
                self.assertTrue(result.blocked)
                self.assertEqual(result.completed_count, 0)
                self.assertEqual(result.selected_count, 0)
                self.assertIsNone(result.receipt)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.source_write_performed)
                self.assertFalse(result.safe_write_performed)
                self.assertFalse(result.command_run_performed)
                self.assertFalse(result.git_mutation_performed)

    def test_status_attempt_and_time_validation_fails_closed(self) -> None:
        cases = [
            ({"status": "queued"}, "unknown_status"),
            ({"attempts": -1}, "attempts_out_of_bounds"),
            ({"attempts": MAX_SAFE_TASK_ATTEMPTS + 1}, "attempts_out_of_bounds"),
            ({"attempts": True}, "malformed_field:attempts"),
            ({"timeout_seconds": 0}, "timeout_seconds_out_of_bounds"),
            ({"timeout_seconds": MAX_SAFE_TASK_TIMEOUT_SECONDS + 1}, "timeout_seconds_out_of_bounds"),
            ({"timeout_seconds": "900"}, "malformed_field:timeout_seconds"),
            (
                {"retry_policy": {"max_attempts": MAX_SAFE_TASK_ATTEMPTS + 1, "retry_delay_seconds": 60}},
                "unsupported_retry_max_attempts",
            ),
            (
                {"retry_policy": {"max_attempts": MAX_SAFE_TASK_ATTEMPTS, "retry_delay_seconds": -1}},
                "invalid_retry_delay_seconds",
            ),
            (
                {"retry_policy": {"max_attempts": MAX_SAFE_TASK_ATTEMPTS}},
                "malformed_field:retry_policy.retry_delay_seconds",
            ),
            ({"created_at": "2026-05-22T12:01:00Z"}, "created_at_in_future"),
            ({"created_at": "not-a-date"}, "malformed_field:created_at"),
            (
                {"status": "selected", "selected_at": None},
                "selected_at_required",
            ),
            (
                {"status": "running", "selected_at": None},
                "selected_at_required",
            ),
            (
                {"status": "completed", "completed_at": None},
                "completed_at_required",
            ),
            (
                {"status": "cancelled", "cancelled_at": None},
                "cancelled_at_required",
            ),
            (
                {
                    "status": "cancelled",
                    "cancelled_at": "2026-05-22T11:50:00Z",
                    "cancellation_reason": "operator cancelled",
                },
                "cancelled_at_before_created_at",
            ),
            (
                {"status": "cancelled", "cancelled_at": "2026-05-22T12:00:00Z"},
                "cancellation_reason_required",
            ),
            (
                {"status": "blocked", "blocked_reason": None},
                "blocked_reason_required",
            ),
            (
                {"status": "failed", "blocked_reason": ""},
                "malformed_field:blocked_reason",
            ),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_safe_task_record(
                    {**self._record().to_dict(), **override},
                    expected_approval_token_id="approval-token-plan-7-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_file_scope_validation_fails_closed(self) -> None:
        cases = [
            ({"allowed_files": ()}, "missing_allowed_files"),
            ({"allowed_files": "docs/example.md"}, "malformed_field:allowed_files"),
            ({"forbidden_files": ("",)}, "malformed_field:forbidden_files"),
            (
                {
                    "allowed_files": ("docs/example.md", "docs/example.md"),
                },
                "duplicate_field:allowed_files",
            ),
            (
                {
                    "allowed_files": ("docs/example.md",),
                    "forbidden_files": ("docs/example.md",),
                },
                "allowed_file_forbidden",
            ),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_safe_task_record(
                    {**self._record().to_dict(), **override},
                    expected_approval_token_id="approval-token-plan-7-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_model_surface_has_no_execution_storage_safe_write_or_git_hooks(self) -> None:
        public_functions = {
            name
            for name, value in vars(safe_task_queue).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }
        self.assertEqual(
            public_functions,
            {
                "build_safe_task_queue_model_status",
                "drill_safe_task_kill_switch",
                "run_first_auto_selected_safe_task",
                "select_next_safe_task",
                "validate_safe_task_record",
            },
        )

        public_classes = {
            name
            for name, value in vars(safe_task_queue).items()
            if inspect.isclass(value) and value.__module__ == safe_task_queue.__name__
        }
        self.assertEqual(
            public_classes,
            {
                "SafeTaskRecord",
                "SafeTaskKillSwitchDrill",
                "SafeTaskRecordValidation",
                "SafeTaskRunReceipt",
                "SafeTaskRunNextSelection",
            },
        )

        source = inspect.getsource(safe_task_queue)
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

    def _record(
        self,
        *,
        task_id: str = "task-1",
        task_class: str = "safe_docs_evidence_maintenance",
        trust_tier: str = SAFE_TASK_TRUST_TIER,
        approval_token_id: str = "approval-token-plan-7-phase-1",
        status: str = "pending",
        selected_at: str | None = None,
    ) -> SafeTaskRecord:
        return SafeTaskRecord(
            task_id=task_id,
            task_class=task_class,
            trust_tier=trust_tier,
            approval_token_id=approval_token_id,
            allowed_files=("docs/cartographer-live-evidence/example.md",),
            forbidden_files=("source_proxy/api/cartographer.py",),
            status=status,
            selected_at=selected_at,
            created_at=(self._now() - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        )


if __name__ == "__main__":
    unittest.main()
