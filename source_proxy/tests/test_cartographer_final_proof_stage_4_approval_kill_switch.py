from __future__ import annotations

import inspect
import unittest

from source_proxy.cartographer import final_proof_stage_4_approval_kill_switch
from source_proxy.cartographer.final_proof_stage_4_approval_kill_switch import (
    CartographerFinalProofStage4Drill,
    validate_final_proof_stage_4_approval_kill_switch_dry_run,
)


class CartographerFinalProofStage4ApprovalKillSwitchTests(unittest.TestCase):
    def test_valid_drill_still_never_executes_or_grants_autonomy(self) -> None:
        result = validate_final_proof_stage_4_approval_kill_switch_dry_run(self._drill())

        self.assertEqual(result.stage, "Final Proof Stage 4")
        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.would_execute)
        self.assertFalse(result.would_resume)
        self.assertFalse(result.would_retry)
        self.assertFalse(result.full_auto_granted)
        self.assertTrue(result.operator_review_required)

    def test_expired_revoked_self_approval_and_kill_switches_block(self) -> None:
        result = validate_final_proof_stage_4_approval_kill_switch_dry_run(
            self._drill(
                approval_expired=True,
                approval_revoked=True,
                self_approved=True,
                kill_switch_scopes_active=("global", "workflow"),
                attempted_resume=True,
                attempted_retry=True,
            )
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("approval_expired", result.blocked_reasons)
        self.assertIn("approval_revoked", result.blocked_reasons)
        self.assertIn("self_approval_forbidden", result.blocked_reasons)
        self.assertIn("global_kill_switch_active", result.blocked_reasons)
        self.assertIn("requested_scope_kill_switch_active", result.blocked_reasons)
        self.assertIn("resume_blocked_by_stop_state", result.blocked_reasons)
        self.assertIn("retry_blocked_by_stop_state", result.blocked_reasons)

    def test_auto_clear_kill_switch_is_forbidden(self) -> None:
        result = validate_final_proof_stage_4_approval_kill_switch_dry_run(
            self._drill(attempted_auto_clear=True)
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("auto_clear_kill_switch_forbidden", result.blocked_reasons)
        self.assertFalse(result.would_clear_kill_switch)

    def test_operator_review_is_required(self) -> None:
        result = validate_final_proof_stage_4_approval_kill_switch_dry_run(
            self._drill(operator_reviewed=False)
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("operator_review_missing", result.blocked_reasons)

    def test_module_exposes_no_write_execution_network_or_git_surface(self) -> None:
        source = inspect.getsource(final_proof_stage_4_approval_kill_switch)
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
    def _drill(
        *,
        approval_expired: bool = False,
        approval_revoked: bool = False,
        self_approved: bool = False,
        kill_switch_scopes_active: tuple[str, ...] = (),
        attempted_auto_clear: bool = False,
        attempted_resume: bool = False,
        attempted_retry: bool = False,
        operator_reviewed: bool = True,
    ) -> CartographerFinalProofStage4Drill:
        return CartographerFinalProofStage4Drill(
            drill_id="drill-4",
            approval_present=True,
            approval_expired=approval_expired,
            approval_revoked=approval_revoked,
            self_approved=self_approved,
            kill_switch_scopes_active=kill_switch_scopes_active,
            requested_scope="workflow",
            attempted_auto_clear=attempted_auto_clear,
            attempted_resume=attempted_resume,
            attempted_retry=attempted_retry,
            operator_reviewed=operator_reviewed,
        )


if __name__ == "__main__":
    unittest.main()
