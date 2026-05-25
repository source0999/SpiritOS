from __future__ import annotations

import inspect
import unittest

from source_proxy.cartographer import final_proof_stage_5_rollback
from source_proxy.cartographer.final_proof_stage_5_rollback import (
    CartographerFinalProofStage5RollbackDrill,
    validate_final_proof_stage_5_rollback_dry_run,
)


class CartographerFinalProofStage5RollbackTests(unittest.TestCase):
    def test_valid_rollback_drill_remains_dry_run_only(self) -> None:
        result = validate_final_proof_stage_5_rollback_dry_run(self._drill())

        self.assertEqual(result.stage, "Final Proof Stage 5")
        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.would_execute_rollback)
        self.assertFalse(result.would_write_files)
        self.assertFalse(result.would_cleanup)
        self.assertFalse(result.would_closeout)
        self.assertFalse(result.full_auto_granted)
        self.assertTrue(result.operator_review_required)

    def test_missing_metadata_and_broad_scope_block(self) -> None:
        result = validate_final_proof_stage_5_rollback_dry_run(
            self._drill(
                rollback_reference=None,
                rollback_target_files=("docs/rollback.md", "src/app/coding/page.tsx"),
                allowed_files=("docs/rollback.md",),
                approval_present=False,
                verification_after_rollback=None,
            )
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("missing_rollback_reference", result.blocked_reasons)
        self.assertIn("rollback_scope_exceeds_allowed_files", result.blocked_reasons)
        self.assertIn("protected_path_in_rollback_scope", result.blocked_reasons)
        self.assertIn("missing_rollback_approval", result.blocked_reasons)
        self.assertIn("missing_post_rollback_verification", result.blocked_reasons)

    def test_execution_failure_and_cleanup_attempts_block_closeout(self) -> None:
        result = validate_final_proof_stage_5_rollback_dry_run(
            self._drill(
                rollback_command_would_execute=True,
                rollback_failed=True,
                cleanup_attempted=True,
            )
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("rollback_execution_forbidden_in_dry_run", result.blocked_reasons)
        self.assertIn("rollback_failure_blocks_closeout", result.blocked_reasons)
        self.assertIn("cleanup_forbidden", result.blocked_reasons)
        self.assertFalse(result.would_execute_rollback)
        self.assertFalse(result.would_closeout)

    def test_operator_review_is_required(self) -> None:
        result = validate_final_proof_stage_5_rollback_dry_run(
            self._drill(operator_reviewed=False)
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("operator_review_missing", result.blocked_reasons)

    def test_module_exposes_no_write_execution_network_or_git_surface(self) -> None:
        source = inspect.getsource(final_proof_stage_5_rollback)
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
        rollback_reference: str | None = "manual rollback reference",
        rollback_target_files: tuple[str, ...] = ("docs/rollback.md",),
        allowed_files: tuple[str, ...] = ("docs/rollback.md",),
        approval_present: bool = True,
        verification_after_rollback: str | None = "verify rollback",
        rollback_command_would_execute: bool = False,
        rollback_failed: bool = False,
        cleanup_attempted: bool = False,
        operator_reviewed: bool = True,
    ) -> CartographerFinalProofStage5RollbackDrill:
        return CartographerFinalProofStage5RollbackDrill(
            drill_id="drill-5",
            original_action_id="action-5",
            rollback_reference=rollback_reference,
            rollback_target_files=rollback_target_files,
            allowed_files=allowed_files,
            approval_present=approval_present,
            verification_after_rollback=verification_after_rollback,
            rollback_command_would_execute=rollback_command_would_execute,
            rollback_failed=rollback_failed,
            cleanup_attempted=cleanup_attempted,
            operator_reviewed=operator_reviewed,
        )


if __name__ == "__main__":
    unittest.main()
