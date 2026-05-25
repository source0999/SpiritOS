from __future__ import annotations

from datetime import UTC, datetime
import inspect
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.cartographer import test_maintenance_proposals
from source_proxy.cartographer.test_maintenance_proposals import (
    FORBIDDEN_TEST_MAINTENANCE_AUTHORITIES,
    SAFE_TEST_MAINTENANCE_CLASSES,
    SAFE_TEST_MAINTENANCE_PROPOSALS_PHASE,
    SAFE_TEST_MAINTENANCE_REQUIRED_FIELDS,
    SafeTestMaintenanceProposal,
    build_safe_test_maintenance_proposal_status,
    validate_safe_test_maintenance_proposal,
)


class CartographerTestMaintenanceProposalTests(unittest.TestCase):
    def test_status_is_proposal_only_without_write_or_execution_authority(self) -> None:
        status = build_safe_test_maintenance_proposal_status()

        self.assertEqual(status["phase"], SAFE_TEST_MAINTENANCE_PROPOSALS_PHASE)
        self.assertEqual(status["status"], "proposal-only")
        self.assertEqual(status["safe_maintenance_classes"], SAFE_TEST_MAINTENANCE_CLASSES)
        self.assertEqual(status["required_fields"], SAFE_TEST_MAINTENANCE_REQUIRED_FIELDS)
        self.assertEqual(status["forbidden_authorities"], FORBIDDEN_TEST_MAINTENANCE_AUTHORITIES)
        self.assertTrue(status["proposal_only"])
        self.assertFalse(status["source_write_enabled"])
        self.assertFalse(status["test_write_enabled"])
        self.assertFalse(status["command_execution_enabled"])
        self.assertFalse(status["test_execution_enabled"])
        self.assertFalse(status["queue_execution_enabled"])
        self.assertFalse(status["commit_enabled"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["durable_storage_written"])
        self.assertFalse(status["api_mutation_available"])
        self.assertTrue(status["exact_scope_required"])
        self.assertTrue(status["approval_bound"])
        self.assertTrue(status["verification_plan_required"])
        self.assertTrue(status["automatic_test_edits_blocked"])

    def test_valid_safe_test_maintenance_proposal_accepts_without_writes(self) -> None:
        result = validate_safe_test_maintenance_proposal(
            self._proposal(),
            expected_trust_tier="tier-1",
            expected_approval_token_id="approval-token-plan-11-phase-11-1-test-maintenance",
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.proposal_id, "test-maintenance-plan-11-1-2")
        self.assertEqual(result.maintenance_class, "test_name_clarification")
        self.assertEqual(result.target_test_file, "source_proxy/tests/test_cartographer_daily_driver_soak.py")
        self.assertEqual(result.trust_tier, "tier-1")
        self.assertEqual(result.approval_token_id, "approval-token-plan-11-phase-11-1-test-maintenance")
        self.assertTrue(result.proposal_only)
        self.assertFalse(result.source_write_enabled)
        self.assertFalse(result.test_write_enabled)
        self.assertFalse(result.command_execution_enabled)
        self.assertFalse(result.test_execution_enabled)

    def test_required_fields_fail_closed(self) -> None:
        for field in SAFE_TEST_MAINTENANCE_REQUIRED_FIELDS:
            payload = self._proposal().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_safe_test_maintenance_proposal(
                    payload,
                    expected_trust_tier="tier-1",
                    expected_approval_token_id="approval-token-plan-11-phase-11-1-test-maintenance",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_scope_trust_token_and_status_rules_fail_closed(self) -> None:
        cases = [
            ({"maintenance_class": "source_refactor"}, "unknown_maintenance_class"),
            ({"target_test_file": "source_proxy/cartographer/soak_promotion.py"}, "target_must_be_exact_test_file"),
            ({"target_test_file": "source_proxy/tests/*.py"}, "target_must_be_exact_test_file"),
            ({"target_test_file": "source_proxy/tests/*.py"}, "broad_target_test_file"),
            ({"trust_tier": "tier-3"}, "wrong_trust_tier"),
            ({"approval_token_id": "other-token"}, "wrong_approval_token"),
            ({"status": "approved"}, "status_must_remain_proposed"),
            ({"verification_plan": ()}, "missing_verification_plan"),
            ({"exact_change_summary": "Apply now to simplify tests."}, "change_summary_must_not_request_application"),
            ({"rationale": "Also update source behavior."}, "rationale_must_not_expand_to_source_changes"),
            ({"created_at": "2026-05-23T12:10:00Z"}, "created_at_in_future"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_safe_test_maintenance_proposal(
                    {**self._proposal().to_dict(), **override},
                    expected_trust_tier="tier-1",
                    expected_approval_token_id="approval-token-plan-11-phase-11-1-test-maintenance",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.source_write_enabled)
                self.assertFalse(result.test_write_enabled)

    def test_module_exposes_no_write_execution_git_api_mutation_or_storage_surface(self) -> None:
        source = inspect.getsource(test_maintenance_proposals)
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
            "pytest",
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

    def test_test_maintenance_api_preview_is_proposal_only(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/expansion/test-maintenance/proposals")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["api_preview_only"])
        self.assertEqual(payload["test_maintenance_status"]["phase"], SAFE_TEST_MAINTENANCE_PROPOSALS_PHASE)
        self.assertEqual(payload["validation"]["status"], "accepted")
        self.assertFalse(payload["source_write_enabled"])
        self.assertFalse(payload["test_write_enabled"])
        self.assertFalse(payload["command_execution_enabled"])
        self.assertFalse(payload["test_execution_enabled"])
        self.assertFalse(payload["queue_execution_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])

    @staticmethod
    def _proposal() -> SafeTestMaintenanceProposal:
        return SafeTestMaintenanceProposal(
            proposal_id="test-maintenance-plan-11-1-2",
            maintenance_class="test_name_clarification",
            target_test_file="source_proxy/tests/test_cartographer_daily_driver_soak.py",
            exact_change_summary="Rename a focused test for clarity without changing assertions.",
            rationale="Improve reviewability of an existing safe soak validation test.",
            verification_plan=("manual_review_only", "run exact focused test after separate approval"),
            trust_tier="tier-1",
            approval_token_id="approval-token-plan-11-phase-11-1-test-maintenance",
            status="proposed",
            created_at="2026-05-23T12:00:00Z",
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
