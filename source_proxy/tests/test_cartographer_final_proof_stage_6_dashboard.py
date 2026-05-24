from __future__ import annotations

import inspect
import unittest

from source_proxy.cartographer import final_proof_stage_6_dashboard
from source_proxy.cartographer.final_proof_stage_6_dashboard import (
    CartographerFinalProofStage6DashboardSnapshot,
    validate_final_proof_stage_6_dashboard_dry_run,
)


class CartographerFinalProofStage6DashboardTests(unittest.TestCase):
    def test_complete_dashboard_snapshot_validates_without_authority(self) -> None:
        result = validate_final_proof_stage_6_dashboard_dry_run(self._snapshot())

        self.assertEqual(result.stage, "Final Proof Stage 6")
        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.would_execute_queue)
        self.assertFalse(result.would_mutate_dashboard)
        self.assertFalse(result.dashboard_authority_granted)
        self.assertFalse(result.full_auto_granted)

    def test_missing_visibility_and_dashboard_authority_block(self) -> None:
        result = validate_final_proof_stage_6_dashboard_dry_run(
            self._snapshot(
                queue_visible=False,
                ledger_visible=False,
                dashboard_can_grant_authority=True,
                queue_runs_observed=0,
                queue_runs_executed=1,
            )
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("dashboard_missing_queue_visible", result.blocked_reasons)
        self.assertIn("dashboard_missing_ledger_visible", result.blocked_reasons)
        self.assertIn("dashboard_authority_forbidden", result.blocked_reasons)
        self.assertIn("missing_repeated_queue_run_observation", result.blocked_reasons)
        self.assertIn("queue_execution_forbidden_in_dry_run", result.blocked_reasons)
        self.assertFalse(result.dashboard_authority_granted)

    def test_module_exposes_no_write_execution_network_or_git_surface(self) -> None:
        source = inspect.getsource(final_proof_stage_6_dashboard)
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
    def _snapshot(
        *,
        queue_visible: bool = True,
        ledger_visible: bool = True,
        dashboard_can_grant_authority: bool = False,
        queue_runs_observed: int = 3,
        queue_runs_executed: int = 0,
    ) -> CartographerFinalProofStage6DashboardSnapshot:
        return CartographerFinalProofStage6DashboardSnapshot(
            snapshot_id="snapshot-6",
            queue_visible=queue_visible,
            trust_tiers_visible=True,
            approvals_visible=True,
            ledger_visible=ledger_visible,
            stop_state_visible=True,
            blocked_reasons_visible=True,
            evidence_visible=True,
            final_readiness_visible=True,
            dashboard_can_grant_authority=dashboard_can_grant_authority,
            queue_runs_observed=queue_runs_observed,
            queue_runs_executed=queue_runs_executed,
        )


if __name__ == "__main__":
    unittest.main()
