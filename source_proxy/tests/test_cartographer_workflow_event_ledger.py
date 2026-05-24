from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import inspect
import unittest

from source_proxy.cartographer import workflow_event_ledger
from source_proxy.cartographer.workflow_event_ledger import (
    WORKFLOW_LEDGER_EVENT_TYPES,
    WorkflowLedgerEvent,
    build_workflow_event_ledger_status,
    build_workflow_ledger_event,
    preview_append_workflow_ledger_event,
    validate_workflow_event_ledger,
)


class CartographerWorkflowEventLedgerTests(unittest.TestCase):
    def test_status_is_append_only_model_without_execution_authority(self) -> None:
        status = build_workflow_event_ledger_status()

        self.assertEqual(status["status"], "append-only-ledger-model")
        self.assertTrue(status["append_only"])
        self.assertEqual(status["supported_event_types"], WORKFLOW_LEDGER_EVENT_TYPES)
        self.assertIn("workflow_created", status["supported_event_types"])
        self.assertIn("step_started", status["supported_event_types"])
        self.assertIn("step_blocked", status["supported_event_types"])
        self.assertIn("step_completed", status["supported_event_types"])
        self.assertIn("workflow_paused", status["supported_event_types"])
        self.assertIn("workflow_cancelled", status["supported_event_types"])
        self.assertIn("workflow_timed_out", status["supported_event_types"])
        self.assertIn("step_retried", status["supported_event_types"])
        self.assertIn("workflow_verified", status["supported_event_types"])
        self.assertIn("workflow_closed_out", status["supported_event_types"])
        self.assertFalse(status["execution_available"])
        self.assertFalse(status["durable_write_available"])
        self.assertFalse(status["workflow_execution_authority_granted"])
        self.assertFalse(status["queue_authority_granted"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])
        self.assertFalse(status["token_minting_available"])
        self.assertFalse(status["approval_storage_available"])

    def test_append_preview_returns_new_tuple_and_preserves_existing_events(self) -> None:
        first = self._event(1, "workflow_created")
        second = self._event(
            2,
            "step_started",
            previous_event_hash=first.event_hash,
            step_id="step-1",
        )
        events = (first,)

        preview = preview_append_workflow_ledger_event(events, second)

        self.assertTrue(preview.accepted)
        self.assertFalse(preview.blocked)
        self.assertEqual(preview.reasons, ())
        self.assertEqual(preview.next_sequence, 2)
        self.assertEqual(preview.previous_event_hash, first.event_hash)
        self.assertEqual(events, (first,))
        self.assertEqual(preview.appended_events, (first, second))
        self.assertIsNot(preview.appended_events, events)
        self.assertTrue(preview.preview_only)
        self.assertFalse(preview.execution_available)
        self.assertFalse(preview.durable_write_available)
        self.assertFalse(preview.git_mutation_authority_granted)

    def test_valid_lifecycle_ledger_accepts_named_phase_events(self) -> None:
        events: tuple[WorkflowLedgerEvent, ...] = ()
        for event in (
            self._event(1, "workflow_created"),
            self._event(2, "step_started", step_id="step-1"),
            self._event(3, "step_blocked", step_id="step-1", reason="approval_required"),
            self._event(4, "step_retried", step_id="step-1", reason="operator_retry"),
            self._event(5, "step_completed", step_id="step-1"),
            self._event(6, "workflow_paused", reason="operator_pause"),
            self._event(7, "workflow_cancelled", reason="operator_cancelled"),
            self._event(8, "workflow_timed_out", reason="timeout_seconds_exceeded"),
            self._event(9, "workflow_verified", verification_reference="verification-1"),
            self._event(10, "workflow_closed_out", closeout={"summary": "closed"}),
        ):
            event = replace(event, previous_event_hash=events[-1].event_hash if events else None)
            event = self._rehash(event)
            preview = preview_append_workflow_ledger_event(events, event)
            self.assertTrue(preview.accepted, preview.reasons)
            events = preview.appended_events

        validation = validate_workflow_event_ledger(events)

        self.assertTrue(validation.valid)
        self.assertFalse(validation.blocked)
        self.assertEqual(validation.reasons, ())
        self.assertEqual(validation.event_count, 10)
        self.assertTrue(validation.append_only)
        self.assertFalse(validation.execution_available)
        self.assertFalse(validation.workflow_execution_authority_granted)

    def test_validation_fails_closed_for_rewrites_reorders_and_bad_hashes(self) -> None:
        first = self._event(1, "workflow_created")
        second = self._event(2, "step_started", previous_event_hash=first.event_hash, step_id="step-1")
        cases = [
            ((replace(first, sequence=2),), "sequence_gap_or_reorder"),
            ((first, replace(second, event_id=first.event_id)), "duplicate_event_id"),
            ((first, replace(second, run_id="other-run")), "run_id_mismatch"),
            ((first, replace(second, previous_event_hash="wrong-hash")), "previous_event_hash_mismatch"),
            ((first, replace(second, actor="changed-after-hash")), "event_hash_mismatch"),
        ]

        for events, reason in cases:
            with self.subTest(reason=reason):
                result = validate_workflow_event_ledger(events)

                self.assertFalse(result.valid)
                self.assertTrue(result.blocked)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.execution_available)

    def test_append_preview_blocks_non_next_event_and_does_not_mutate_ledger(self) -> None:
        first = self._event(1, "workflow_created")
        bad_next = self._event(3, "step_started", previous_event_hash=first.event_hash, step_id="step-1")

        preview = preview_append_workflow_ledger_event((first,), bad_next)

        self.assertFalse(preview.accepted)
        self.assertTrue(preview.blocked)
        self.assertIn("next_sequence_mismatch", preview.reasons)
        self.assertEqual(preview.appended_events, (first,))

    def test_event_shape_validation_fails_closed(self) -> None:
        cases = [
            (replace(self._event(1, "workflow_created"), event_id=""), "missing_event_id"),
            (self._event(1, "unknown"), "unsupported_event_type"),
            (replace(self._event(1, "workflow_created"), run_id=""), "missing_run_id"),
            (replace(self._event(1, "workflow_created"), sequence=0), "invalid_sequence"),
            (replace(self._event(1, "workflow_created"), occurred_at=""), "missing_occurred_at"),
            (replace(self._event(1, "workflow_created"), actor=""), "missing_actor"),
            (self._event(1, "step_started"), "missing_step_id"),
            (self._event(1, "step_blocked", step_id="step-1"), "missing_reason"),
            (self._event(1, "workflow_verified"), "missing_verification_reference"),
            (self._event(1, "workflow_closed_out"), "missing_closeout"),
        ]

        for event, reason in cases:
            with self.subTest(reason=reason):
                result = validate_workflow_event_ledger((event,))

                self.assertFalse(result.valid)
                self.assertIn(reason, result.reasons)

    def test_module_surface_has_no_execution_storage_or_git_mutation_hooks(self) -> None:
        public_functions = {
            name
            for name, value in vars(workflow_event_ledger).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }
        self.assertEqual(
            public_functions,
            {
                "build_workflow_event_ledger_status",
                "build_workflow_ledger_event",
                "preview_append_workflow_ledger_event",
                "validate_workflow_event_ledger",
            },
        )

        public_classes = {
            name
            for name, value in vars(workflow_event_ledger).items()
            if inspect.isclass(value) and value.__module__ == workflow_event_ledger.__name__
        }
        self.assertEqual(
            public_classes,
            {
                "WorkflowLedgerAppendPreview",
                "WorkflowLedgerEvent",
                "WorkflowLedgerValidation",
            },
        )

        source = inspect.getsource(workflow_event_ledger)
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

    def _event(
        self,
        sequence: int,
        event_type: str,
        *,
        previous_event_hash: str | None = None,
        step_id: str | None = None,
        reason: str | None = None,
        verification_reference: str | None = None,
        closeout: dict[str, object] | None = None,
    ) -> WorkflowLedgerEvent:
        return build_workflow_ledger_event(
            event_id=f"event-{sequence}",
            event_type=event_type,
            run_id="run-5-2",
            sequence=sequence,
            actor="cartographer-runtime",
            occurred_at=self._now() + timedelta(seconds=sequence),
            step_id=step_id,
            approval_token_id="token-5-2",
            workflow_status="pending",
            reason=reason,
            verification_reference=verification_reference,
            closeout=closeout,
            previous_event_hash=previous_event_hash,
        )

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 22, 12, 0, 0, tzinfo=UTC)

    @staticmethod
    def _rehash(event: WorkflowLedgerEvent) -> WorkflowLedgerEvent:
        return build_workflow_ledger_event(
            event_id=event.event_id,
            event_type=event.event_type,
            run_id=event.run_id,
            sequence=event.sequence,
            actor=event.actor,
            occurred_at=datetime.fromisoformat(event.occurred_at.replace("Z", "+00:00")),
            step_id=event.step_id,
            approval_token_id=event.approval_token_id,
            workflow_status=event.workflow_status,
            reason=event.reason,
            verification_reference=event.verification_reference,
            receipt_path=event.receipt_path,
            closeout=event.closeout,
            previous_event_hash=event.previous_event_hash,
        )


if __name__ == "__main__":
    unittest.main()
