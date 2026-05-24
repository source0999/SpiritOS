from __future__ import annotations

import inspect
import unittest

from source_proxy.cartographer import final_proof_stage_7_readiness
from source_proxy.cartographer.final_proof_stage_7_readiness import (
    CartographerFinalProofStage7Inputs,
    build_final_proof_stage_7_readiness_decision_dry_run,
)


class CartographerFinalProofStage7ReadinessTests(unittest.TestCase):
    def test_complete_score_is_review_ready_but_grants_no_autonomy(self) -> None:
        decision = build_final_proof_stage_7_readiness_decision_dry_run(self._inputs())

        self.assertEqual(decision.stage, "Final Proof Stage 7")
        self.assertEqual(decision.readiness_score, 100)
        self.assertTrue(decision.ready_for_operator_review)
        self.assertFalse(decision.limited_unattended_operation_allowed)
        self.assertFalse(decision.full_auto_granted)
        self.assertFalse(decision.autonomy_granted)
        self.assertEqual(decision.blocked_reasons, ())

    def test_missing_proof_residual_risks_and_autonomy_requests_block(self) -> None:
        decision = build_final_proof_stage_7_readiness_decision_dry_run(
            self._inputs(
                soak_passed=False,
                rollback_drills_passed=False,
                residual_risks=("manual review still required",),
                operator_decision="allow_full_auto",
                requested_full_auto=True,
                requested_limited_unattended_operation=True,
            )
        )

        self.assertEqual(decision.readiness_score, 66)
        self.assertFalse(decision.ready_for_operator_review)
        self.assertIn("soak_not_passed", decision.blocked_reasons)
        self.assertIn("rollback_drills_not_passed", decision.blocked_reasons)
        self.assertIn("residual_risks_require_operator_review", decision.blocked_reasons)
        self.assertIn("operator_decision_must_remain_review_only", decision.blocked_reasons)
        self.assertIn("full_auto_request_forbidden", decision.blocked_reasons)
        self.assertIn("limited_unattended_operation_not_granted_by_dry_run", decision.blocked_reasons)
        self.assertFalse(decision.full_auto_granted)

    def test_module_exposes_no_write_execution_network_or_git_surface(self) -> None:
        source = inspect.getsource(final_proof_stage_7_readiness)
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
    def _inputs(
        *,
        soak_passed: bool = True,
        rollback_drills_passed: bool = True,
        residual_risks: tuple[str, ...] = (),
        operator_decision: str = "review_only",
        requested_full_auto: bool = False,
        requested_limited_unattended_operation: bool = False,
    ) -> CartographerFinalProofStage7Inputs:
        return CartographerFinalProofStage7Inputs(
            gauntlet_passed=True,
            soak_passed=soak_passed,
            hidden_mutation_drills_passed=True,
            approval_kill_switch_drills_passed=True,
            rollback_drills_passed=rollback_drills_passed,
            dashboard_proof_passed=True,
            residual_risks=residual_risks,
            operator_decision=operator_decision,
            requested_full_auto=requested_full_auto,
            requested_limited_unattended_operation=requested_limited_unattended_operation,
        )


if __name__ == "__main__":
    unittest.main()
