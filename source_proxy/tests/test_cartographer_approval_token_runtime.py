from __future__ import annotations

from datetime import UTC, datetime, timedelta
import inspect
import unittest

from source_proxy.cartographer import approval_token_runtime
from source_proxy.cartographer.approval_token_runtime import (
    APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
    APPROVAL_TOKEN_SCHEMA_VERSION,
    REQUIRED_APPROVAL_TOKEN_FIELDS,
    build_approval_token_runtime_status,
    validate_approval_token_payload,
)


class CartographerApprovalTokenRuntimeTests(unittest.TestCase):
    def test_valid_token_accepts_validation_without_granting_authority(self) -> None:
        result = validate_approval_token_payload(
            self._valid_payload(),
            requested_actor="cartographer-runtime",
            requested_scope=self._scope(),
            requested_action_type="docs_receipt_preview",
            requested_files=["docs/cartographer-example.md"],
            current_head="abc123",
            current_dirty_tree=self._dirty_tree(),
            requested_trust_tier="tier-1",
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.rejected)
        self.assertEqual(result.status, "accepted")
        self.assertFalse(result.go)
        self.assertTrue(result.no_go_default)
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.reason_details, ())
        self.assertEqual(result.token_id, "approval-token-plan-4-phase-4-1")
        self.assertEqual(result.run_id, "run-plan-4-phase-4-1")
        self.assertEqual(result.action_type, "docs_receipt_preview")
        self.assertEqual(result.lane_id, "cartographer")
        self.assertEqual(result.requested_lane_id, "cartographer")
        self.assertEqual(result.approval_actor, "Britton")
        self.assertEqual(result.approver_id, "Britton")
        self.assertEqual(result.approved_for_actor, "cartographer-runtime")
        self.assertEqual(result.operator_id, "cartographer-runtime")
        self.assertEqual(result.token_scope, self._scope())
        self.assertEqual(result.exact_allowed_files, ("docs/cartographer-example.md",))
        self.assertEqual(result.exact_forbidden_files, ("source_proxy/cartographer/apply.py",))
        self.assertEqual(result.requested_files, ("docs/cartographer-example.md",))
        self.assertEqual(result.expected_head, "abc123")
        self.assertEqual(result.current_head, "abc123")
        self.assertEqual(result.expected_dirty_tree, self._dirty_tree())
        self.assertEqual(result.current_dirty_tree, self._dirty_tree())
        self.assertEqual(result.kill_switch_state, APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE)
        self.assertEqual(result.trust_tier, "tier-1")
        self.assertEqual(result.requested_trust_tier, "tier-1")
        self.assertTrue(result.single_action)
        self.assertTrue(result.issued_by_human)
        self.assertFalse(result.authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.workflow_authority_granted)
        self.assertFalse(result.queue_authority_granted)
        self.assertFalse(result.git_authority_granted)
        self.assertTrue(result.validation_only)

    def test_missing_required_fields_fail_closed(self) -> None:
        for field in REQUIRED_APPROVAL_TOKEN_FIELDS:
            payload = self._valid_payload()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_approval_token_payload(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_type="docs_receipt_preview",
                    requested_files=["docs/cartographer-example.md"],
                    current_head="abc123",
                    current_dirty_tree=self._dirty_tree(),
                    requested_trust_tier="tier-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertTrue(result.rejected)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_malformed_payloads_fail_closed(self) -> None:
        cases: list[tuple[object, str]] = [
            (None, "malformed_payload"),
            ("not-a-token", "malformed_payload"),
            (
                {**self._valid_payload(), "human_approved_at": "not-a-date"},
                "malformed_field:human_approved_at",
            ),
            ({**self._valid_payload(), "expires_at": "not-a-date"}, "malformed_field:expires_at"),
            ({**self._valid_payload(), "approver_id": ""}, "malformed_field:approver_id"),
            ({**self._valid_payload(), "operator_id": ""}, "malformed_field:operator_id"),
            ({**self._valid_payload(), "lane_id": ""}, "malformed_field:lane_id"),
            (
                {**self._valid_payload(), "single_action": "yes"},
                "malformed_field:single_action",
            ),
            (
                {**self._valid_payload(), "issued_by_human": "yes"},
                "malformed_field:issued_by_human",
            ),
            ({**self._valid_payload(), "scope": "docs"}, "malformed_field:scope"),
            ({**self._valid_payload(), "scope": {"type": "phase"}}, "malformed_field:scope"),
            (
                {**self._valid_payload(), "exact_allowed_files": "docs"},
                "malformed_field:exact_allowed_files",
            ),
            (
                {**self._valid_payload(), "exact_allowed_files": [""]},
                "malformed_field:exact_allowed_files",
            ),
            (
                {**self._valid_payload(), "expected_dirty_tree": "clean"},
                "malformed_field:expected_dirty_tree",
            ),
            (
                {**self._valid_payload(), "expected_dirty_tree": {}},
                "malformed_field:expected_dirty_tree",
            ),
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
                    requested_action_type="docs_receipt_preview",
                    requested_files=["docs/cartographer-example.md"],
                    current_head="abc123",
                    current_dirty_tree=self._dirty_tree(),
                    requested_trust_tier="tier-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_wrong_actor_fails_closed(self) -> None:
        payload = {
            **self._valid_payload(),
            "operator_id": "other-runtime",
        }

        result = validate_approval_token_payload(
            payload,
            requested_actor="cartographer-runtime",
            requested_scope=self._scope(),
            requested_action_type="docs_receipt_preview",
            requested_files=["docs/cartographer-example.md"],
            current_head="abc123",
            current_dirty_tree=self._dirty_tree(),
            requested_trust_tier="tier-1",
            now=self._now(),
        )

        self.assertFalse(result.accepted)
        self.assertIn("wrong_actor", result.reasons)

    def test_missing_or_malformed_request_context_fails_closed(self) -> None:
        cases = [
            (
                {
                    "requested_actor": "",
                    "requested_scope": self._scope(),
                    "requested_lane_id": "cartographer",
                    "requested_files": ["docs/cartographer-example.md"],
                },
                "missing_requested_actor",
            ),
            (
                {
                    "requested_actor": "cartographer-runtime",
                    "requested_scope": {"type": "phase"},
                    "requested_lane_id": "cartographer",
                    "requested_files": ["docs/cartographer-example.md"],
                },
                "malformed_requested_scope",
            ),
            (
                {
                    "requested_actor": "cartographer-runtime",
                    "requested_scope": self._scope(),
                    "requested_lane_id": "",
                    "requested_files": ["docs/cartographer-example.md"],
                },
                "missing_requested_lane",
            ),
            (
                {
                    "requested_actor": "cartographer-runtime",
                    "requested_scope": self._scope(),
                    "requested_lane_id": "cartographer",
                    "requested_files": ["docs/cartographer-example.md", ""],
                },
                "malformed_requested_files",
            ),
        ]

        for overrides, reason in cases:
            with self.subTest(reason=reason):
                result = validate_approval_token_payload(
                    self._valid_payload(),
                    requested_actor=overrides["requested_actor"],
                    requested_scope=overrides["requested_scope"],
                    requested_action_type="docs_receipt_preview",
                    requested_lane_id=overrides["requested_lane_id"],
                    requested_files=overrides["requested_files"],
                    current_head="abc123",
                    current_dirty_tree=self._dirty_tree(),
                    requested_trust_tier="tier-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.authority_granted)

    def test_self_approval_is_rejected(self) -> None:
        cases = [
            {**self._valid_payload(), "approver_id": "cartographer-runtime"},
            {
                **self._valid_payload(),
                "approver_id": "Britton",
                "operator_id": "Britton",
            },
        ]

        for payload in cases:
            with self.subTest(payload=payload):
                result = validate_approval_token_payload(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_type="docs_receipt_preview",
                    requested_files=["docs/cartographer-example.md"],
                    current_head="abc123",
                    current_dirty_tree=self._dirty_tree(),
                    requested_trust_tier="tier-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn("self_approval_rejected", result.reasons)

    def test_wrong_scope_and_broad_scope_are_rejected(self) -> None:
        cases = [
            (
                self._valid_payload(),
                {"type": "phase", "value": "other-phase"},
                "scope_mismatch",
            ),
            (
                {
                    **self._valid_payload(),
                    "scope": {"type": "repo", "value": "*"},
                },
                {"type": "repo", "value": "*"},
                "broad_scope",
            ),
        ]

        for payload, requested_scope, reason in cases:
            with self.subTest(reason=reason):
                result = validate_approval_token_payload(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=requested_scope,
                    requested_action_type="docs_receipt_preview",
                    requested_files=["docs/cartographer-example.md"],
                    current_head="abc123",
                    current_dirty_tree=self._dirty_tree(),
                    requested_trust_tier="tier-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_lane_and_single_action_contract_fail_closed(self) -> None:
        cases = [
            (
                {**self._valid_payload(), "lane_id": "docs"},
                {"requested_lane_id": "cartographer"},
                "lane_mismatch",
            ),
            (
                {**self._valid_payload(), "lane_id": "*"},
                {"requested_lane_id": "*"},
                "broad_lane",
            ),
            (
                {**self._valid_payload(), "single_action": False},
                {},
                "single_action_required",
            ),
            (
                {**self._valid_payload(), "issued_by_human": False},
                {},
                "human_issued_required",
            ),
        ]

        for payload, overrides, reason in cases:
            with self.subTest(reason=reason):
                result = validate_approval_token_payload(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_type="docs_receipt_preview",
                    requested_lane_id=overrides.get("requested_lane_id", "cartographer"),
                    requested_files=["docs/cartographer-example.md"],
                    current_head="abc123",
                    current_dirty_tree=self._dirty_tree(),
                    requested_trust_tier="tier-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.authority_granted)

    def test_action_files_head_dirty_kill_switch_and_tier_fail_closed(self) -> None:
        cases = [
            (
                self._valid_payload(),
                {"requested_action_type": "other_action"},
                "action_type_mismatch",
            ),
            (
                {**self._valid_payload(), "exact_allowed_files": ["*"]},
                {},
                "wildcard_file_scope",
            ),
            (
                {**self._valid_payload(), "exact_allowed_files": ["."]},
                {},
                "broad_file_scope",
            ),
            (
                self._valid_payload(),
                {"requested_files": ["docs/not-approved.md"]},
                "requested_files_exceed_exact_allowed_files",
            ),
            (
                self._valid_payload(),
                {"requested_files": ["source_proxy/cartographer/apply.py"]},
                "requested_files_match_forbidden_files",
            ),
            (
                self._valid_payload(),
                {"current_head": "different"},
                "stale_head",
            ),
            (
                self._valid_payload(),
                {"current_dirty_tree": {"fingerprint": "dirty", "dirty_files": ["x"]}},
                "stale_dirty_tree",
            ),
            (
                self._valid_payload(),
                {"kill_switch_active": True},
                "kill_switch_active",
            ),
            (
                {**self._valid_payload(), "kill_switch_state": "active"},
                {},
                "kill_switch_state_not_inactive",
            ),
            (
                {**self._valid_payload(), "trust_tier": "*"},
                {},
                "broad_trust_tier",
            ),
            (
                self._valid_payload(),
                {"requested_trust_tier": "tier-2"},
                "trust_tier_mismatch",
            ),
        ]

        for payload, overrides, reason in cases:
            with self.subTest(reason=reason):
                result = validate_approval_token_payload(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_type=overrides.get(
                        "requested_action_type",
                        "docs_receipt_preview",
                    ),
                    requested_files=overrides.get(
                        "requested_files",
                        ["docs/cartographer-example.md"],
                    ),
                    current_head=overrides.get("current_head", "abc123"),
                    current_dirty_tree=overrides.get(
                        "current_dirty_tree",
                        self._dirty_tree(),
                    ),
                    kill_switch_active=overrides.get("kill_switch_active", False),
                    requested_trust_tier=overrides.get("requested_trust_tier", "tier-1"),
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.authority_granted)

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
                    "human_approved_at": "2026-05-20T11:59:59Z",
                },
                "token_stale",
            ),
            (
                {
                    **self._valid_payload(),
                    "human_approved_at": "2026-05-22T12:01:00Z",
                },
                "token_approved_in_future",
            ),
            (
                {
                    **self._valid_payload(),
                    "human_approved_at": "2026-05-22T12:05:00Z",
                    "expires_at": "2026-05-22T12:05:00Z",
                },
                "token_expiration_not_after_approval",
            ),
        ]

        for payload, reason in cases:
            with self.subTest(reason=reason):
                result = validate_approval_token_payload(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_type="docs_receipt_preview",
                    requested_files=["docs/cartographer-example.md"],
                    current_head="abc123",
                    current_dirty_tree=self._dirty_tree(),
                    requested_trust_tier="tier-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_status_preview_is_validation_only(self) -> None:
        status = build_approval_token_runtime_status()

        self.assertEqual(status["status"], "validation-only")
        self.assertEqual(status["schema_version"], APPROVAL_TOKEN_SCHEMA_VERSION)
        self.assertEqual(status["required_fields"], REQUIRED_APPROVAL_TOKEN_FIELDS)
        self.assertTrue(status["no_go_default"])
        self.assertFalse(status["authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["workflow_authority_granted"])
        self.assertFalse(status["queue_authority_granted"])
        self.assertFalse(status["git_authority_granted"])
        self.assertFalse(status["self_approval_allowed"])
        self.assertFalse(status["token_issuance_available"])
        self.assertFalse(status["token_storage_available"])
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
            "value": "cartographer-integrated-control-plan-4-phase-4-1",
        }

    @staticmethod
    def _dirty_tree() -> dict[str, object]:
        return {
            "fingerprint": "clean-plan-4",
            "dirty_files": [],
            "expected_dirty": False,
        }

    def _valid_payload(self) -> dict[str, object]:
        return {
            "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
            "token_id": "approval-token-plan-4-phase-4-1",
            "run_id": "run-plan-4-phase-4-1",
            "operator_id": "cartographer-runtime",
            "approver_id": "Britton",
            "action_type": "docs_receipt_preview",
            "lane_id": "cartographer",
            "scope": self._scope(),
            "exact_allowed_files": ["docs/cartographer-example.md"],
            "exact_forbidden_files": ["source_proxy/cartographer/apply.py"],
            "expires_at": (self._now() + timedelta(minutes=55)).isoformat().replace("+00:00", "Z"),
            "rollback_instructions": "Manual rollback instructions only; no runtime rollback.",
            "verification_instructions": "Run focused approval-token runtime tests.",
            "expected_head": "abc123",
            "expected_dirty_tree": self._dirty_tree(),
            "kill_switch_state": APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
            "trust_tier": "tier-1",
            "single_action": True,
            "issued_by_human": True,
            "human_approved_at": (self._now() - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        }


if __name__ == "__main__":
    unittest.main()
