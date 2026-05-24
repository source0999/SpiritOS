from __future__ import annotations

from dataclasses import replace
import inspect
import unittest

from source_proxy.cartographer import level_11_event_ledger
from source_proxy.cartographer.level_11_event_ledger import (
    CartographerLevel11LedgerEvent,
    build_level_11_event_ledger_schema_preview,
    validate_level_11_event_ledger_dry_run,
)


class CartographerLevel11EventLedgerTests(unittest.TestCase):
    def test_schema_preview_does_not_enable_ledger_or_action_authority(self) -> None:
        preview = build_level_11_event_ledger_schema_preview()

        self.assertEqual(preview["level"], "11.3")
        self.assertEqual(preview["status"], "ledger-model-dry-run-only")
        self.assertFalse(preview["append_only_runtime_enabled"])
        self.assertFalse(preview["action_authority_granted"])
        self.assertFalse(preview["write_authority_granted"])
        self.assertFalse(preview["local_execution_authority_granted"])
        self.assertIn("file_write_blocked", preview["supported_event_types"])

    def test_ordered_blocked_ledger_events_validate_for_dry_run_only(self) -> None:
        result = validate_level_11_event_ledger_dry_run(
            (
                self._event(1, "action_packet_created"),
                self._event(2, "approval_requested"),
                self._event(3, "file_write_blocked", reason="approval_missing"),
            )
        )

        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.append_only_runtime_enabled)
        self.assertFalse(result.action_authority_granted)
        self.assertEqual(result.blocked_reasons, ())
        self.assertEqual(result.event_count, 3)

    def test_ledger_validation_fails_closed_for_bad_event_shape(self) -> None:
        valid_events = (
            self._event(1, "action_packet_created"),
            self._event(2, "approval_requested"),
            self._event(3, "file_write_blocked", reason="approval_missing"),
        )
        cases = [
            ((), "missing_events"),
            (
                (
                    self._event(1, "action_packet_created"),
                    replace(self._event(2, "approval_requested"), event_id="event-1"),
                ),
                "duplicate_event_id",
            ),
            (
                (
                    self._event(1, "action_packet_created"),
                    self._event(3, "approval_requested"),
                ),
                "sequence_gap_or_reorder",
            ),
            (
                (self._event(1, "unknown_event"),),
                "unsupported_event_type",
            ),
            (
                (replace(self._event(1, "action_packet_created"), event_id=""),),
                "missing_event_id",
            ),
            (
                (replace(self._event(1, "action_packet_created"), run_id=""),),
                "missing_run_id",
            ),
            (
                (replace(self._event(1, "action_packet_created"), actor=""),),
                "missing_actor",
            ),
            (
                (self._event(1, "file_write_blocked"),),
                "blocked_event_missing_reason",
            ),
            (
                (*valid_events, self._event(4, "verification_failed")),
                "failed_event_missing_reason",
            ),
            (
                (*valid_events, self._event(4, "file_write_completed")),
                "missing_required_completed_action_event:approval_granted",
            ),
        ]

        for events, reason in cases:
            with self.subTest(reason=reason):
                result = validate_level_11_event_ledger_dry_run(events)
                self.assertFalse(result.valid_for_dry_run)
                self.assertIn(reason, result.blocked_reasons)
                self.assertFalse(result.action_authority_granted)

    def test_module_exposes_no_append_write_execution_or_git_surface(self) -> None:
        public_functions = {
            name
            for name, value in vars(level_11_event_ledger).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }

        self.assertEqual(
            public_functions,
            {
                "build_level_11_event_ledger_schema_preview",
                "validate_level_11_event_ledger_dry_run",
            },
        )

        source = inspect.getsource(level_11_event_ledger)
        forbidden_fragments = (
            "subprocess",
            "os.system",
            "Path(",
            "open(",
            ".write(",
            "write_text(",
            "append(",
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
    def _event(
        sequence: int,
        event_type: str,
        *,
        reason: str | None = None,
    ) -> CartographerLevel11LedgerEvent:
        return CartographerLevel11LedgerEvent(
            event_id=f"event-{sequence}",
            event_type=event_type,
            run_id="run-11-3",
            action_id="action-11-3",
            token_id="token-11-3",
            sequence=sequence,
            actor="cartographer-dry-run",
            target_files=("docs/receipts/level-11.md",),
            head_before="40141f34d27d915503f265efba119673a412354a",
            git_status_before="dry-run-status",
            rollback_reference="rollback metadata required before future writes",
            verification_reference="verification metadata required before future writes",
            reason=reason,
        )


if __name__ == "__main__":
    unittest.main()
