from __future__ import annotations

from datetime import UTC, datetime
import inspect
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.cartographer import trust_tier_decision_gate
from source_proxy.cartographer.trust_tier_decision_gate import (
    EXPANSION_CLASSES_REQUIRING_TRUST_TIER_REVIEW,
    FORBIDDEN_TRUST_TIER_DECISION_AUTHORITIES,
    TRUST_TIER_ADVANCEMENT_CRITERIA,
    TRUST_TIERS,
    TRUST_TIER_DECISION_OUTCOMES,
    TRUST_TIER_DECISION_GATE_PHASE,
    TRUST_TIER_DECISION_REQUIRED_FIELDS,
    TRUST_TIER_REGRESSION_SIGNALS,
    TrustTierDecisionGate,
    build_trust_tier_decision_gate_status,
    validate_trust_tier_decision_gate,
)


class CartographerTrustTierDecisionGateTests(unittest.TestCase):
    def test_status_is_gate_only_without_authority_expansion(self) -> None:
        status = build_trust_tier_decision_gate_status()

        self.assertEqual(status["phase"], TRUST_TIER_DECISION_GATE_PHASE)
        self.assertEqual(status["status"], "gate-only")
        self.assertEqual(status["trust_tiers"], TRUST_TIERS)
        self.assertEqual(status["current_trust_tier"], "tier-1")
        self.assertEqual(status["decision_outcomes"], TRUST_TIER_DECISION_OUTCOMES)
        self.assertEqual(status["advancement_criteria"], TRUST_TIER_ADVANCEMENT_CRITERIA)
        self.assertEqual(status["regression_signals"], TRUST_TIER_REGRESSION_SIGNALS)
        self.assertEqual(
            status["expansion_classes_requiring_review"],
            EXPANSION_CLASSES_REQUIRING_TRUST_TIER_REVIEW,
        )
        self.assertEqual(status["required_fields"], TRUST_TIER_DECISION_REQUIRED_FIELDS)
        self.assertEqual(status["forbidden_authorities"], FORBIDDEN_TRUST_TIER_DECISION_AUTHORITIES)
        self.assertTrue(status["gate_only"])
        self.assertFalse(status["expansion_enabled"])
        self.assertFalse(status["trust_tier_promotion_recorded"])
        self.assertFalse(status["approval_token_minted"])
        self.assertFalse(status["self_approval_allowed"])
        self.assertFalse(status["command_execution_enabled"])
        self.assertFalse(status["queue_execution_enabled"])
        self.assertFalse(status["task_execution_enabled"])
        self.assertFalse(status["safe_write_enabled"])
        self.assertFalse(status["commit_enabled"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["branch_enabled"])
        self.assertFalse(status["worktree_enabled"])
        self.assertFalse(status["durable_storage_written"])
        self.assertFalse(status["api_mutation_available"])
        self.assertTrue(status["human_promotion_decision_required"])
        self.assertFalse(status["automatic_tier_advancement_enabled"])
        self.assertFalse(status["full_auto_enabled"])
        self.assertFalse(status["push_promotion_enabled"])
        self.assertEqual(
            status["next_explicit_decision_gate"],
            "human operator review of the Plan 10/10 trust-tier decision packet",
        )

    def test_valid_trust_tier_decision_accepts_for_review_without_promotion(self) -> None:
        result = validate_trust_tier_decision_gate(
            self._decision(),
            expected_approval_token_id="approval-token-plan-10-phase-11-2-trust-tier",
            now=self._now(),
        )

        self.assertTrue(result.accepted_for_review)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted_for_review")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.decision_id, "trust-tier-plan-10-2-2")
        self.assertEqual(result.requested_expansion_class, "controlled_multi_worker_branch_workflow")
        self.assertEqual(result.current_trust_tier, "tier-1")
        self.assertEqual(result.requested_trust_tier, "tier-2")
        self.assertEqual(result.decision_outcome, "advance")
        self.assertEqual(result.evidence_paths, ("docs/cartographer-plan-10-trust-tier-proof.md",))
        self.assertEqual(result.soak_evidence_hours, 72)
        self.assertTrue(result.rollback_proof_recorded)
        self.assertEqual(result.false_positive_count, 0)
        self.assertEqual(result.false_negative_count, 0)
        self.assertEqual(result.stop_event_count, 0)
        self.assertFalse(result.expansion_enabled)
        self.assertFalse(result.trust_tier_promotion_recorded)
        self.assertFalse(result.approval_token_minted)
        self.assertTrue(result.human_promotion_decision_required)

    def test_hold_and_demote_decisions_accept_for_review_without_promotion(self) -> None:
        hold_payload = {
            **self._decision().to_dict(),
            "decision_id": "trust-tier-plan-10-2-2-hold",
            "decision_outcome": "hold",
            "requested_trust_tier": "tier-1",
            "false_positive_count": 1,
        }
        demote_payload = {
            **self._decision().to_dict(),
            "decision_id": "trust-tier-plan-10-2-2-demote",
            "decision_outcome": "demote",
            "current_trust_tier": "tier-2",
            "requested_trust_tier": "tier-1",
            "false_negative_count": 1,
        }

        for payload in (hold_payload, demote_payload):
            with self.subTest(outcome=payload["decision_outcome"]):
                result = validate_trust_tier_decision_gate(
                    payload,
                    expected_approval_token_id="approval-token-plan-10-phase-11-2-trust-tier",
                    now=self._now(),
                )

                self.assertTrue(result.accepted_for_review)
                self.assertEqual(result.reasons, ())
                self.assertFalse(result.expansion_enabled)
                self.assertFalse(result.trust_tier_promotion_recorded)

    def test_required_fields_fail_closed(self) -> None:
        for field in TRUST_TIER_DECISION_REQUIRED_FIELDS:
            payload = self._decision().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_trust_tier_decision_gate(
                    payload,
                    expected_approval_token_id="approval-token-plan-10-phase-11-2-trust-tier",
                    now=self._now(),
                )

                self.assertFalse(result.accepted_for_review)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_tier_evidence_token_and_status_rules_fail_closed(self) -> None:
        cases = [
            ({"requested_expansion_class": "full_auto"}, "unknown_requested_expansion_class"),
            ({"current_trust_tier": "tier-0"}, "unknown_current_trust_tier"),
            ({"requested_trust_tier": "tier-9"}, "unknown_requested_trust_tier"),
            ({"decision_outcome": "full_auto"}, "unknown_decision_outcome"),
            ({"requested_trust_tier": "tier-1"}, "advance_must_request_next_trust_tier"),
            ({"requested_trust_tier": "tier-3"}, "advance_must_request_next_trust_tier"),
            ({"decision_outcome": "hold", "requested_trust_tier": "tier-2"}, "hold_must_keep_current_trust_tier"),
            ({"decision_outcome": "demote"}, "demote_must_lower_trust_tier"),
            (
                {
                    "decision_outcome": "demote",
                    "current_trust_tier": "tier-2",
                    "requested_trust_tier": "tier-1",
                },
                "demote_requires_regression_signal",
            ),
            ({"soak_evidence_hours": -1}, "soak_evidence_hours_must_be_non_negative"),
            ({"soak_evidence_hours": 24}, "advance_requires_72_hour_soak"),
            ({"rollback_proof_recorded": False}, "advance_requires_rollback_proof"),
            ({"false_positive_count": -1}, "false_positive_count_must_be_non_negative"),
            ({"false_positive_count": 1}, "advance_blocked_by_false_positives"),
            ({"false_negative_count": -1}, "false_negative_count_must_be_non_negative"),
            ({"false_negative_count": 1}, "advance_blocked_by_false_negatives"),
            ({"stop_event_count": -1}, "stop_event_count_must_be_non_negative"),
            ({"stop_event_count": 1}, "advance_blocked_by_stop_events"),
            ({"evidence_paths": ()}, "missing_evidence_paths"),
            ({"evidence_paths": ("docs/evidence.md", "docs/evidence.md")}, "duplicate_evidence_path"),
            ({"evidence_paths": ("docs/*.md",)}, "broad_evidence_path"),
            ({"evidence_paths": ("source_proxy/evidence.md",)}, "evidence_path_must_be_docs"),
            ({"evidence_paths": ("docs/evidence.json",)}, "evidence_path_must_be_markdown"),
            ({"operator_review_required": False}, "operator_review_must_be_required"),
            ({"operator_review_recorded": False}, "operator_review_must_be_recorded"),
            ({"approval_token_id": "other-token"}, "wrong_approval_token"),
            ({"status": "approved"}, "status_must_remain_proposed"),
            ({"created_at": "2026-05-23T12:10:00Z"}, "created_at_in_future"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_trust_tier_decision_gate(
                    {**self._decision().to_dict(), **override},
                    expected_approval_token_id="approval-token-plan-10-phase-11-2-trust-tier",
                    now=self._now(),
                )

                self.assertFalse(result.accepted_for_review)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.expansion_enabled)
                self.assertFalse(result.trust_tier_promotion_recorded)

    def test_module_exposes_no_execution_git_mutation_promotion_or_storage_surface(self) -> None:
        source = inspect.getsource(trust_tier_decision_gate)
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

    def test_trust_tier_decision_api_preview_is_gate_only(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/expansion/trust-tier/decision")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["api_preview_only"])
        self.assertEqual(payload["trust_tier_gate_status"]["phase"], TRUST_TIER_DECISION_GATE_PHASE)
        self.assertEqual(payload["validation"]["status"], "accepted_for_review")
        self.assertFalse(payload["expansion_enabled"])
        self.assertFalse(payload["trust_tier_promotion_recorded"])
        self.assertFalse(payload["approval_token_minted"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["command_execution_enabled"])
        self.assertFalse(payload["queue_execution_enabled"])
        self.assertFalse(payload["task_execution_enabled"])
        self.assertFalse(payload["safe_write_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["branch_enabled"])
        self.assertFalse(payload["worktree_enabled"])

    @staticmethod
    def _decision() -> TrustTierDecisionGate:
        return TrustTierDecisionGate(
            decision_id="trust-tier-plan-10-2-2",
            requested_expansion_class="controlled_multi_worker_branch_workflow",
            current_trust_tier="tier-1",
            requested_trust_tier="tier-2",
            decision_outcome="advance",
            evidence_paths=("docs/cartographer-plan-10-trust-tier-proof.md",),
            soak_evidence_hours=72,
            rollback_proof_recorded=True,
            false_positive_count=0,
            false_negative_count=0,
            stop_event_count=0,
            operator_review_required=True,
            operator_review_recorded=True,
            approval_token_id="approval-token-plan-10-phase-11-2-trust-tier",
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
