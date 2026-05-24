from __future__ import annotations

from datetime import UTC, datetime, timedelta
import inspect
import unittest

from source_proxy.cartographer import approval_token_runtime
from source_proxy.cartographer.approval_token_runtime import (
    APPROVAL_TOKEN_SCHEMA_VERSION,
    build_approval_token_runtime_status,
    validate_approval_token_payload,
)


class CartographerApprovalTokenRuntimeTests(unittest.TestCase):
    def test_valid_token_accepts_validation_without_granting_authority(self) -> None:
        result = validate_approval_token_payload(
            self._valid_payload(),
            requested_actor="cartographer-runtime",
            requested_scope=self._scope(),
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.rejected)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.approval_actor, "Britton")
        self.assertEqual(result.approved_for_actor, "cartographer-runtime")
        self.assertEqual(result.token_scope, self._scope())
        self.assertFalse(result.authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.workflow_authority_granted)
        self.assertFalse(result.queue_authority_granted)
        self.assertFalse(result.git_authority_granted)
        self.assertTrue(result.validation_only)

    def test_missing_required_fields_fail_closed(self) -> None:
        for field in (
            "schema_version",
            "token_id",
            "issued_at",
            "expires_at",
            "approved_by",
            "approved_for_actor",
            "scope",
            "reason",
        ):
            payload = self._valid_payload()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_approval_token_payload(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertTrue(result.rejected)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_malformed_payloads_fail_closed(self) -> None:
        cases: list[tuple[object, str]] = [
            (None, "malformed_payload"),
            ("not-a-token", "malformed_payload"),
            ({**self._valid_payload(), "issued_at": "not-a-date"}, "malformed_field:issued_at"),
            ({**self._valid_payload(), "expires_at": "not-a-date"}, "malformed_field:expires_at"),
            ({**self._valid_payload(), "approved_by": ""}, "malformed_field:approved_by"),
            ({**self._valid_payload(), "scope": "docs"}, "malformed_field:scope"),
            ({**self._valid_payload(), "scope": {"type": "phase"}}, "malformed_field:scope"),
            (
                {**self._valid_payload(), "schema_version": "cartographer.other"},
                "schema_version_mismatch",
            ),
        ]

        for payload, reason in cases:
            with self.subTest(reason=reason):
                result = validate_approval_token_payload(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_wrong_actor_fails_closed(self) -> None:
        payload = {
            **self._valid_payload(),
            "approved_for_actor": "other-runtime",
        }

        result = validate_approval_token_payload(
            payload,
            requested_actor="cartographer-runtime",
            requested_scope=self._scope(),
            now=self._now(),
        )

        self.assertFalse(result.accepted)
        self.assertIn("wrong_actor", result.reasons)

    def test_self_approval_is_rejected(self) -> None:
        cases = [
            {**self._valid_payload(), "approved_by": "cartographer-runtime"},
            {
                **self._valid_payload(),
                "approved_by": "cartographer-runtime",
                "approved_for_actor": "cartographer-runtime",
            },
        ]

        for payload in cases:
            with self.subTest(payload=payload):
                result = validate_approval_token_payload(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn("self_approval_rejected", result.reasons)

    def test_scope_mismatch_is_rejected(self) -> None:
        result = validate_approval_token_payload(
            self._valid_payload(),
            requested_actor="cartographer-runtime",
            requested_scope={"type": "phase", "value": "plan-2-phase-2"},
            now=self._now(),
        )

        self.assertFalse(result.accepted)
        self.assertIn("scope_mismatch", result.reasons)

    def test_expired_stale_and_future_tokens_are_rejected(self) -> None:
        cases = [
            (
                {
                    **self._valid_payload(),
                    "expires_at": "2026-05-22T11:59:59Z",
                },
                "token_expired",
            ),
            (
                {
                    **self._valid_payload(),
                    "issued_at": "2026-05-20T11:59:59Z",
                },
                "token_stale",
            ),
            (
                {
                    **self._valid_payload(),
                    "issued_at": "2026-05-22T12:01:00Z",
                },
                "token_issued_in_future",
            ),
            (
                {
                    **self._valid_payload(),
                    "issued_at": "2026-05-22T12:00:00Z",
                    "expires_at": "2026-05-22T12:00:00Z",
                },
                "token_expiration_not_after_issue",
            ),
        ]

        for payload, reason in cases:
            with self.subTest(reason=reason):
                result = validate_approval_token_payload(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_status_preview_is_validation_only(self) -> None:
        status = build_approval_token_runtime_status()

        self.assertEqual(status["status"], "validation-only")
        self.assertEqual(status["schema_version"], APPROVAL_TOKEN_SCHEMA_VERSION)
        self.assertFalse(status["authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["workflow_authority_granted"])
        self.assertFalse(status["queue_authority_granted"])
        self.assertFalse(status["git_authority_granted"])
        self.assertFalse(status["self_approval_allowed"])
        self.assertTrue(status["validation_only"])

    def test_validation_surface_has_no_mutation_or_execution_hooks(self) -> None:
        public_functions = {
            name
            for name, value in vars(approval_token_runtime).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }

        self.assertEqual(
            public_functions,
            {
                "build_approval_token_runtime_status",
                "validate_approval_token_payload",
            },
        )

        source = inspect.getsource(approval_token_runtime)
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
            "git checkout",
            "git stash",
            "git worktree",
            "git reset",
            "git clean",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 22, 12, 0, 0, tzinfo=UTC)

    @staticmethod
    def _scope() -> dict[str, str]:
        return {
            "type": "phase",
            "value": "cartographer-daily-driver-plan-2-phase-1",
        }

    def _valid_payload(self) -> dict[str, object]:
        return {
            "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
            "token_id": "approval-token-plan-2-phase-1",
            "issued_at": (self._now() - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
            "expires_at": (self._now() + timedelta(minutes=55)).isoformat().replace("+00:00", "Z"),
            "approved_by": "Britton",
            "approved_for_actor": "cartographer-runtime",
            "scope": self._scope(),
            "reason": "Validate Plan 2 Phase 1 approval token runtime only.",
        }


if __name__ == "__main__":
    unittest.main()
