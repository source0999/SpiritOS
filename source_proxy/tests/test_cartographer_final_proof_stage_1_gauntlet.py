from __future__ import annotations

import inspect
import unittest

from source_proxy.cartographer import final_proof_stage_1_gauntlet
from source_proxy.cartographer.final_proof_stage_1_gauntlet import (
    CartographerFinalProofStage1Task,
    evaluate_final_proof_stage_1_task_dry_run,
    run_final_proof_stage_1_gauntlet_dry_run,
)


class CartographerFinalProofStage1GauntletTests(unittest.TestCase):
    def test_safe_review_task_is_eligible_for_dry_run_but_never_executes(self) -> None:
        result = evaluate_final_proof_stage_1_task_dry_run(self._task())

        self.assertTrue(result.eligible_for_dry_run)
        self.assertFalse(result.would_execute)
        self.assertFalse(result.would_write_files)
        self.assertFalse(result.would_run_commands)
        self.assertEqual(result.blocked_reasons, ())

    def test_unsafe_tasks_block_for_human_readable_reasons(self) -> None:
        result = evaluate_final_proof_stage_1_task_dry_run(
            self._task(
                task_class="commit",
                target_files=("src/app/coding/page.tsx",),
                approval_expired=True,
                kill_switch_active=True,
            )
        )

        self.assertFalse(result.eligible_for_dry_run)
        self.assertIn("forbidden_task_class", result.blocked_reasons)
        self.assertIn("unsupported_task_class", result.blocked_reasons)
        self.assertIn("protected_path_in_scope", result.blocked_reasons)
        self.assertIn("approval_expired", result.blocked_reasons)
        self.assertIn("kill_switch_active", result.blocked_reasons)
        self.assertFalse(result.would_execute)

    def test_gauntlet_passes_only_when_all_unsafe_tasks_block(self) -> None:
        result = run_final_proof_stage_1_gauntlet_dry_run(
            (
                self._task(task_id="safe-1"),
                self._task(task_id="unsafe-1", task_class="push"),
                self._task(
                    task_id="unsafe-2",
                    target_files=("source_proxy/api/cartographer.py",),
                ),
                self._task(task_id="unsafe-3", approval_expired=True),
            )
        )

        self.assertEqual(result.stage, "Final Proof Stage 1")
        self.assertEqual(result.status, "real-task-gauntlet-dry-run-only")
        self.assertTrue(result.passed)
        self.assertEqual(result.unsafe_task_count, 3)
        self.assertEqual(result.blocked_unsafe_task_count, 3)
        self.assertFalse(result.full_auto_granted)
        self.assertFalse(result.limited_unattended_operation_granted)
        self.assertFalse(result.queue_execution_authority_granted)

    def test_empty_gauntlet_does_not_pass(self) -> None:
        result = run_final_proof_stage_1_gauntlet_dry_run(())

        self.assertFalse(result.passed)
        self.assertFalse(result.full_auto_granted)

    def test_module_exposes_no_write_execution_network_or_git_surface(self) -> None:
        source = inspect.getsource(final_proof_stage_1_gauntlet)
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
    def _task(
        *,
        task_id: str = "task-safe",
        task_class: str = "docs_freshness_review",
        target_files: tuple[str, ...] = ("docs/manual-check.md",),
        approval_present: bool = True,
        approval_expired: bool = False,
        kill_switch_active: bool = False,
    ) -> CartographerFinalProofStage1Task:
        return CartographerFinalProofStage1Task(
            task_id=task_id,
            task_class=task_class,
            lane="cartographer_final_proof_dry_run",
            target_files=target_files,
            approval_present=approval_present,
            approval_expired=approval_expired,
            kill_switch_active=kill_switch_active,
            expected_result="dry_run_only",
        )


if __name__ == "__main__":
    unittest.main()
