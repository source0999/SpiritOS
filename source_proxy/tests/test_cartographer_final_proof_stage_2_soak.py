from __future__ import annotations

import inspect
import unittest

from source_proxy.cartographer import final_proof_stage_2_soak
from source_proxy.cartographer.final_proof_stage_2_soak import (
    CartographerFinalProofStage2SoakSample,
    validate_final_proof_stage_2_soak_dry_run,
)


class CartographerFinalProofStage2SoakTests(unittest.TestCase):
    def test_valid_soak_dry_run_never_schedules_or_executes(self) -> None:
        result = validate_final_proof_stage_2_soak_dry_run(
            (
                self._sample("sample-0", 0),
                self._sample("sample-24", 24),
            ),
            requested_duration_hours=24,
        )

        self.assertEqual(result.stage, "Final Proof Stage 2")
        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.would_schedule_background_job)
        self.assertFalse(result.would_execute_queue)
        self.assertFalse(result.would_write_evidence)
        self.assertFalse(result.full_auto_granted)
        self.assertFalse(result.limited_unattended_operation_granted)

    def test_soak_dry_run_blocks_invalid_duration_and_missing_samples(self) -> None:
        result = validate_final_proof_stage_2_soak_dry_run((), requested_duration_hours=12)

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("duration_outside_24_to_72_hour_window", result.blocked_reasons)
        self.assertIn("missing_soak_samples", result.blocked_reasons)

    def test_soak_dry_run_blocks_hidden_mutation_head_change_and_unexplained_dirty_tree(self) -> None:
        result = validate_final_proof_stage_2_soak_dry_run(
            (
                self._sample("sample-0", 0),
                self._sample(
                    "sample-1",
                    1,
                    hidden_mutation_detected=True,
                    head_changed=True,
                    dirty_worktree_explained=False,
                    manual_intervention_required=True,
                    kill_switch_checked=False,
                ),
            ),
            requested_duration_hours=24,
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("kill_switch_not_checked:sample-1", result.blocked_reasons)
        self.assertIn("hidden_mutation_detected:sample-1", result.blocked_reasons)
        self.assertIn("head_changed:sample-1", result.blocked_reasons)
        self.assertIn("dirty_worktree_unexplained:sample-1", result.blocked_reasons)
        self.assertIn("manual_intervention_required:sample-1", result.blocked_reasons)
        self.assertFalse(result.full_auto_granted)

    def test_soak_dry_run_blocks_duplicate_and_out_of_order_samples(self) -> None:
        result = validate_final_proof_stage_2_soak_dry_run(
            (
                self._sample("sample-dup", 0),
                self._sample("sample-dup", 0),
            ),
            requested_duration_hours=24,
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("duplicate_sample_id", result.blocked_reasons)
        self.assertIn("sample_hours_not_increasing", result.blocked_reasons)

    def test_module_exposes_no_write_execution_network_or_git_surface(self) -> None:
        source = inspect.getsource(final_proof_stage_2_soak)
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
    def _sample(
        sample_id: str,
        hour: int,
        *,
        hidden_mutation_detected: bool = False,
        head_changed: bool = False,
        dirty_worktree_explained: bool = True,
        manual_intervention_required: bool = False,
        kill_switch_checked: bool = True,
    ) -> CartographerFinalProofStage2SoakSample:
        return CartographerFinalProofStage2SoakSample(
            sample_id=sample_id,
            hour=hour,
            queue_run_count=0,
            blocked_task_count=0,
            kill_switch_checked=kill_switch_checked,
            hidden_mutation_detected=hidden_mutation_detected,
            head_changed=head_changed,
            dirty_worktree_explained=dirty_worktree_explained,
            manual_intervention_required=manual_intervention_required,
        )


if __name__ == "__main__":
    unittest.main()
