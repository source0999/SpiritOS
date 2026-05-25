from __future__ import annotations

from datetime import UTC, datetime, timedelta
import inspect
import unittest

from source_proxy.cartographer import approval_token_consumption
from source_proxy.cartographer.approval_token_runtime import (
    APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
    APPROVAL_TOKEN_SCHEMA_VERSION,
)
from source_proxy.cartographer.approval_token_consumption import (
    build_approval_token_consumption_status,
    preview_approval_token_consumption,
)


class CartographerApprovalTokenConsumptionTests(unittest.TestCase):
    def test_eligible_preview_never_grants_authority(self) -> None:
        preview = preview_approval_token_consumption(
            self._valid_payload(),
            requested_actor="cartographer-runtime",
            requested_scope=self._scope(),
            requested_action_class="docs_receipt_preview",
            requested_files=["docs/cartographer-example.md"],
            consumption_context=self._context(),
            current_head="abc123",
            current_dirty_tree=self._dirty_tree(),
            now=self._now(),
        )

        self.assertTrue(preview.eligible)
        self.assertFalse(preview.blocked)
        self.assertEqual(preview.status, "eligible")
        self.assertFalse(preview.go)
        self.assertTrue(preview.no_go_default)
        self.assertEqual(preview.reasons, ())
        self.assertEqual(preview.reason_details, ())
        self.assertEqual(preview.token_id, "approval-token-plan-4-phase-4-1")
        self.assertEqual(preview.run_id, "run-plan-4-phase-4-1")
        self.assertEqual(preview.approver_id, "Britton")
        self.assertEqual(preview.operator_id, "cartographer-runtime")
        self.assertEqual(preview.approved_lane_id, "cartographer")
        self.assertEqual(preview.requested_lane_id, "cartographer")
        self.assertEqual(preview.expected_dirty_tree, self._dirty_tree())
        self.assertEqual(preview.current_dirty_tree, self._dirty_tree())
        self.assertEqual(
            preview.approval_event_preview["event_type"],
            "approval_consumed_preview",
        )
        self.assertTrue(preview.approval_event_preview["preview_only"])
        self.assertFalse(preview.approval_event_preview["token_consumed_for_real"])
        self.assertEqual(preview.consumption_mode, "preview_only")
        self.assertFalse(preview.durable_token_storage_available)
        self.assertFalse(preview.durable_consumption_record_available)
        self.assertFalse(preview.single_use_enforced_by_runtime)
        self.assertFalse(preview.token_consumed_for_real)
        self.assertEqual(
            preview.durable_record_decision,
            "blocked_until_explicit_human_approval_for_durable_single_use_storage",
        )
        self.assertTrue(preview.preview_only)
        self.assertFalse(preview.authority_granted)
        self.assertFalse(preview.write_authority_granted)
        self.assertFalse(preview.command_authority_granted)
        self.assertFalse(preview.workflow_authority_granted)
        self.assertFalse(preview.queue_authority_granted)
        self.assertFalse(preview.git_authority_granted)

    def test_invalid_token_blocks_consumption_preview(self) -> None:
        preview = preview_approval_token_consumption(
            {**self._valid_payload(), "approver_id": "cartographer-runtime"},
            requested_actor="cartographer-runtime",
            requested_scope=self._scope(),
            requested_action_class="docs_receipt_preview",
            requested_files=["docs/cartographer-example.md"],
            consumption_context=self._context(),
            current_head="abc123",
            current_dirty_tree=self._dirty_tree(),
            now=self._now(),
        )

        self.assertFalse(preview.eligible)
        self.assertIn("token_validation:self_approval_rejected", preview.reasons)
        self.assertEqual(preview.approval_event_preview["event_type"], "approval_rejected")
        self.assertFalse(preview.authority_granted)

    def test_missing_consumption_context_fields_fail_closed(self) -> None:
        for field in (
            "action_class",
            "trust_tier",
            "requested_trust_tier",
            "exact_allowed_files",
            "exact_forbidden_files",
            "expected_head",
            "expected_dirty_tree",
            "rollback",
            "verification",
        ):
            context = self._context()
            context.pop(field)

            with self.subTest(field=field):
                preview = preview_approval_token_consumption(
                    self._valid_payload(),
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_class="docs_receipt_preview",
                    requested_files=["docs/cartographer-example.md"],
                    consumption_context=context,
                    current_head="abc123",
                    current_dirty_tree=self._dirty_tree(),
                    now=self._now(),
                )

                self.assertFalse(preview.eligible)
                self.assertIn(f"missing_consumption_field:{field}", preview.reasons)

    def test_scope_action_head_and_trust_mismatches_fail_closed(self) -> None:
        cases = [
            (
                {"requested_scope": {"type": "phase", "value": "other"}},
                "token_validation:scope_mismatch",
            ),
            (
                {"requested_lane_id": "docs"},
                "token_validation:lane_mismatch",
            ),
            (
                {"requested_action_class": "other_action"},
                "action_class_mismatch",
            ),
            (
                {"current_head": "different"},
                "stale_head",
            ),
            (
                {"current_dirty_tree": {"fingerprint": "dirty", "dirty_files": ["x"]}},
                "stale_dirty_tree",
            ),
            (
                {
                    "consumption_context": {
                        **self._context(),
                        "requested_trust_tier": "tier-2",
                    },
                },
                "trust_tier_mismatch",
            ),
        ]

        for overrides, reason in cases:
            with self.subTest(reason=reason):
                preview = preview_approval_token_consumption(
                    self._valid_payload(),
                    requested_actor="cartographer-runtime",
                    requested_scope=overrides.get("requested_scope", self._scope()),
                    requested_action_class=overrides.get(
                        "requested_action_class",
                        "docs_receipt_preview",
                    ),
                    requested_lane_id=overrides.get("requested_lane_id", "cartographer"),
                    requested_files=["docs/cartographer-example.md"],
                    consumption_context=overrides.get(
                        "consumption_context",
                        self._context(),
                    ),
                    current_head=overrides.get("current_head", "abc123"),
                    current_dirty_tree=overrides.get(
                        "current_dirty_tree",
                        self._dirty_tree(),
                    ),
                    now=self._now(),
                )

                self.assertFalse(preview.eligible)
                self.assertIn(reason, preview.reasons)

    def test_file_boundaries_fail_closed(self) -> None:
        cases = [
            (
                ["docs/not-approved.md"],
                self._context(),
                "requested_files_exceed_exact_allowed_files",
            ),
            (
                ["source_proxy/cartographer/apply.py"],
                self._context(),
                "requested_files_match_forbidden_files",
            ),
            (
                ["docs/cartographer-example.md"],
                {**self._context(), "exact_allowed_files": ["*"]},
                "wildcard_file_scope",
            ),
            (
                ["docs/cartographer-example.md"],
                {**self._context(), "exact_forbidden_files": ["*"]},
                "wildcard_forbidden_file_scope",
            ),
        ]

        for requested_files, context, reason in cases:
            with self.subTest(reason=reason):
                preview = preview_approval_token_consumption(
                    self._valid_payload(),
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_class="docs_receipt_preview",
                    requested_files=requested_files,
                    consumption_context=context,
                    current_head="abc123",
                    current_dirty_tree=self._dirty_tree(),
                    now=self._now(),
                )

                self.assertFalse(preview.eligible)
                self.assertIn(reason, preview.reasons)

    def test_forbidden_action_and_kill_switch_fail_closed(self) -> None:
        cases = [
            (
                "command_execution",
                self._context(),
                False,
                "forbidden_action_class",
            ),
            (
                "docs_receipt_preview",
                {**self._context(), "action_class": "commit"},
                False,
                "approved_action_class_forbidden",
            ),
            (
                "docs_receipt_preview",
                self._context(),
                True,
                "kill_switch_active",
            ),
        ]

        for action_class, context, kill_switch_active, reason in cases:
            with self.subTest(reason=reason):
                preview = preview_approval_token_consumption(
                    self._valid_payload(),
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_class=action_class,
                    requested_files=["docs/cartographer-example.md"],
                    consumption_context=context,
                    current_head="abc123",
                    current_dirty_tree=self._dirty_tree(),
                    kill_switch_active=kill_switch_active,
                    now=self._now(),
                )

                self.assertFalse(preview.eligible)
                self.assertIn(reason, preview.reasons)

    def test_status_is_preview_only(self) -> None:
        status = build_approval_token_consumption_status()

        self.assertEqual(status["status"], "preview-only")
        self.assertTrue(status["preview_only"])
        self.assertTrue(status["no_go_default"])
        self.assertTrue(status["event_preview_only"])
        self.assertEqual(status["consumption_mode"], "preview_only")
        self.assertFalse(status["durable_token_storage_available"])
        self.assertFalse(status["durable_consumption_record_available"])
        self.assertFalse(status["single_use_enforced_by_runtime"])
        self.assertFalse(status["token_consumed_for_real"])
        self.assertEqual(
            status["durable_record_decision"],
            "blocked_until_explicit_human_approval_for_durable_single_use_storage",
        )
        self.assertFalse(status["authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["workflow_authority_granted"])
        self.assertFalse(status["queue_authority_granted"])
        self.assertFalse(status["git_authority_granted"])

    def test_consumption_surface_has_no_mutation_or_execution_hooks(self) -> None:
        public_functions = {
            name
            for name, value in vars(approval_token_consumption).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }

        self.assertEqual(
            public_functions,
            {
                "build_approval_token_consumption_status",
                "preview_approval_token_consumption",
            },
        )

        source = inspect.getsource(approval_token_consumption)
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
            "verification_instructions": "Run focused approval-token consumption tests.",
            "expected_head": "abc123",
            "expected_dirty_tree": self._dirty_tree(),
            "kill_switch_state": APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
            "trust_tier": "tier-1",
            "single_action": True,
            "issued_by_human": True,
            "human_approved_at": (self._now() - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        }

    @staticmethod
    def _context() -> dict[str, object]:
        return {
            "action_class": "docs_receipt_preview",
            "trust_tier": "tier-1",
            "requested_trust_tier": "tier-1",
            "exact_allowed_files": ["docs/cartographer-example.md"],
            "exact_forbidden_files": ["source_proxy/cartographer/apply.py"],
            "expected_head": "abc123",
            "expected_dirty_tree": CartographerApprovalTokenConsumptionTests._dirty_tree(),
            "rollback": "Manual review only; no runtime write is available.",
            "verification": "Run focused approval-token consumption tests.",
        }


if __name__ == "__main__":
    unittest.main()
