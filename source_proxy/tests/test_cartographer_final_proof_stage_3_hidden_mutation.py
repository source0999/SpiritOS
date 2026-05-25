from __future__ import annotations

import inspect
import unittest

from source_proxy.cartographer import final_proof_stage_3_hidden_mutation
from source_proxy.cartographer.final_proof_stage_3_hidden_mutation import (
    CartographerFinalProofStage3Drill,
    validate_final_proof_stage_3_hidden_mutation_dry_run,
)


class CartographerFinalProofStage3HiddenMutationTests(unittest.TestCase):
    def test_clean_explained_drill_validates_without_mutation_authority(self) -> None:
        result = validate_final_proof_stage_3_hidden_mutation_dry_run(self._drill())

        self.assertEqual(result.stage, "Final Proof Stage 3")
        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.would_clean_worktree)
        self.assertFalse(result.would_stash)
        self.assertFalse(result.would_checkout)
        self.assertFalse(result.would_overwrite_files)
        self.assertFalse(result.full_auto_granted)
        self.assertTrue(result.dirty_tree_fingerprint_required)
        self.assertTrue(result.operator_review_required)

    def test_hidden_mutation_head_change_and_protected_paths_block(self) -> None:
        result = validate_final_proof_stage_3_hidden_mutation_dry_run(
            self._drill(
                dirty_files=("docs/known.md", "src/app/coding/page.tsx"),
                unexpected_files=("source_proxy/api/cartographer.py",),
                head_after="other-head",
                dirty_tree_fingerprint_after="dirty-after",
                mutation_explained=False,
                protected_lane_touched=True,
            )
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("head_changed", result.blocked_reasons)
        self.assertIn("dirty_tree_fingerprint_changed", result.blocked_reasons)
        self.assertIn("unexpected_dirty_worktree_files", result.blocked_reasons)
        self.assertIn("unexpected_generated_files", result.blocked_reasons)
        self.assertIn("protected_path_touched", result.blocked_reasons)
        self.assertIn("protected_lane_touched", result.blocked_reasons)
        self.assertIn("hidden_mutation_suspected", result.blocked_reasons)
        self.assertFalse(result.would_overwrite_files)

    def test_cleanup_stash_and_checkout_attempts_block(self) -> None:
        result = validate_final_proof_stage_3_hidden_mutation_dry_run(
            self._drill(attempted_cleanup=True, attempted_stash=True, attempted_checkout=True)
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("cleanup_forbidden", result.blocked_reasons)
        self.assertIn("stash_forbidden", result.blocked_reasons)
        self.assertIn("checkout_forbidden", result.blocked_reasons)
        self.assertFalse(result.would_clean_worktree)
        self.assertFalse(result.would_stash)
        self.assertFalse(result.would_checkout)

    def test_missing_fingerprint_and_operator_review_block(self) -> None:
        result = validate_final_proof_stage_3_hidden_mutation_dry_run(
            self._drill(
                dirty_tree_fingerprint_before="",
                dirty_tree_fingerprint_after="",
                operator_reviewed=False,
            )
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("missing_dirty_tree_fingerprint", result.blocked_reasons)
        self.assertIn("operator_review_missing", result.blocked_reasons)

    def test_module_exposes_no_write_execution_network_or_git_surface(self) -> None:
        source = inspect.getsource(final_proof_stage_3_hidden_mutation)
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
        dirty_files: tuple[str, ...] = ("docs/known.md",),
        unexpected_files: tuple[str, ...] = (),
        head_after: str = "head-before",
        mutation_explained: bool = True,
        protected_lane_touched: bool = False,
        attempted_cleanup: bool = False,
        attempted_stash: bool = False,
        attempted_checkout: bool = False,
        dirty_tree_fingerprint_before: str = "dirty-before",
        dirty_tree_fingerprint_after: str = "dirty-before",
        operator_reviewed: bool = True,
    ) -> CartographerFinalProofStage3Drill:
        return CartographerFinalProofStage3Drill(
            drill_id="drill-3",
            dirty_files=dirty_files,
            unexpected_files=unexpected_files,
            head_before="head-before",
            head_after=head_after,
            expected_dirty_files=("docs/known.md",),
            protected_lane_touched=protected_lane_touched,
            mutation_explained=mutation_explained,
            attempted_cleanup=attempted_cleanup,
            attempted_stash=attempted_stash,
            attempted_checkout=attempted_checkout,
            dirty_tree_fingerprint_before=dirty_tree_fingerprint_before,
            dirty_tree_fingerprint_after=dirty_tree_fingerprint_after,
            operator_reviewed=operator_reviewed,
        )


if __name__ == "__main__":
    unittest.main()
