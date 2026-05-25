from __future__ import annotations

from datetime import UTC, datetime
import inspect
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.cartographer import multi_worker_branch_workflow
from source_proxy.cartographer.multi_worker_branch_workflow import (
    CONTROLLED_MULTI_WORKER_BRANCH_WORKFLOW_PHASE,
    FORBIDDEN_MULTI_WORKER_BRANCH_AUTHORITIES,
    MULTI_WORKER_BRANCH_WORKFLOW_REQUIRED_FIELDS,
    PLAN_9_MULTI_LANE_SOURCE_EDIT_BOUNDARY,
    PROTECTED_BASE_BRANCHES,
    WORKER_SLOT_REQUIRED_FIELDS,
    ControlledMultiWorkerBranchWorkflow,
    MultiWorkerSlot,
    build_controlled_multi_worker_branch_workflow_status,
    validate_controlled_multi_worker_branch_workflow,
)


class CartographerMultiWorkerBranchWorkflowTests(unittest.TestCase):
    def test_status_is_design_only_without_branch_worktree_or_execution_authority(self) -> None:
        status = build_controlled_multi_worker_branch_workflow_status()

        self.assertEqual(status["phase"], CONTROLLED_MULTI_WORKER_BRANCH_WORKFLOW_PHASE)
        self.assertEqual(status["status"], "design-only")
        self.assertEqual(status["required_fields"], MULTI_WORKER_BRANCH_WORKFLOW_REQUIRED_FIELDS)
        self.assertEqual(status["worker_slot_required_fields"], WORKER_SLOT_REQUIRED_FIELDS)
        self.assertEqual(status["protected_base_branches"], PROTECTED_BASE_BRANCHES)
        self.assertEqual(status["forbidden_authorities"], FORBIDDEN_MULTI_WORKER_BRANCH_AUTHORITIES)
        self.assertTrue(status["design_only"])
        self.assertTrue(status["explicit_branch_worktree_approval_required"])
        self.assertTrue(status["exact_approval_before_creation_required"])
        self.assertTrue(status["ownership_proof_required"])
        self.assertTrue(status["rollback_proof_required"])
        self.assertTrue(status["implicit_creation_blocked"])
        self.assertFalse(status["worker_spawn_enabled"])
        self.assertFalse(status["task_execution_enabled"])
        self.assertFalse(status["queue_execution_enabled"])
        self.assertFalse(status["branch_creation_enabled"])
        self.assertFalse(status["worktree_creation_enabled"])
        self.assertFalse(status["checkout_enabled"])
        self.assertFalse(status["merge_enabled"])
        self.assertFalse(status["command_execution_enabled"])
        self.assertFalse(status["commit_enabled"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["durable_storage_written"])
        self.assertFalse(status["api_mutation_available"])
        self.assertEqual(
            status["plan_9_multi_lane_source_edit_boundary"],
            PLAN_9_MULTI_LANE_SOURCE_EDIT_BOUNDARY,
        )
        self.assertTrue(status["parallel_source_edits_without_ownership_blocked"])

    def test_valid_multi_worker_branch_workflow_accepts_without_creation(self) -> None:
        result = validate_controlled_multi_worker_branch_workflow(
            self._workflow(),
            expected_trust_tier="tier-1",
            expected_approval_token_id="approval-token-plan-9-phase-9-2-branch-worktree",
            expected_branch_worktree_approval_id="branch-worktree-approval-plan-9-phase-9-2",
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.workflow_id, "multi-worker-branch-plan-9-2-1")
        self.assertEqual(result.worker_ids, ("worker-alpha", "worker-beta"))
        self.assertEqual(result.task_ids, ("task-docs-a", "task-docs-b"))
        self.assertEqual(result.file_zones, ("docs/a.md", "docs/b.md"))
        self.assertEqual(result.proposed_branches, ("cartographer/worker-alpha", "cartographer/worker-beta"))
        self.assertEqual(
            result.proposed_worktrees,
            (".cartographer/worktrees/worker-alpha", ".cartographer/worktrees/worker-beta"),
        )
        self.assertTrue(result.explicit_branch_worktree_approval_required)
        self.assertTrue(result.exact_approval_before_creation_required)
        self.assertTrue(result.ownership_proof_required)
        self.assertTrue(result.rollback_proof_required)
        self.assertTrue(result.implicit_creation_blocked)
        self.assertFalse(result.branch_creation_enabled)
        self.assertFalse(result.worktree_creation_enabled)
        self.assertFalse(result.worker_spawn_enabled)

    def test_required_fields_fail_closed(self) -> None:
        for field in MULTI_WORKER_BRANCH_WORKFLOW_REQUIRED_FIELDS:
            payload = self._workflow().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_controlled_multi_worker_branch_workflow(
                    payload,
                    expected_trust_tier="tier-1",
                    expected_approval_token_id="approval-token-plan-9-phase-9-2-branch-worktree",
                    expected_branch_worktree_approval_id="branch-worktree-approval-plan-9-phase-9-2",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_scope_approval_and_uniqueness_rules_fail_closed(self) -> None:
        cases = [
            ({"worker_slots": (self._slot("worker-alpha", "task-docs-a", ("docs/a.md",)),)}, "multi_worker_workflow_requires_at_least_two_workers"),
            ({"worker_slots": (self._slot("worker-alpha", "task-a", ("docs/a.md",)), self._slot("worker-alpha", "task-b", ("docs/b.md",)))}, "duplicate_worker_id"),
            ({"worker_slots": (self._slot("worker-a", "task-a", ("docs/a.md",)), self._slot("worker-b", "task-a", ("docs/b.md",)))}, "duplicate_task_id"),
            ({"worker_slots": (self._slot("worker-a", "task-a", ("docs/a.md",)), self._slot("worker-b", "task-b", ("docs/a.md",)))}, "overlapping_file_zone"),
            ({"worker_slots": (self._slot("worker-a", "task-a", ("docs/*.md",)), self._slot("worker-b", "task-b", ("docs/b.md",)))}, "broad_file_zone"),
            ({"proposed_branches": ("cartographer/only-one",)}, "one_branch_per_worker_required"),
            ({"proposed_worktrees": (".cartographer/worktrees/only-one",)}, "one_worktree_per_worker_required"),
            ({"proposed_branches": ("main", "cartographer/worker-beta")}, "protected_base_branch_blocked"),
            ({"proposed_branches": ("feature/worker-alpha", "cartographer/worker-beta")}, "proposed_branch_must_be_cartographer_scoped"),
            ({"proposed_worktrees": ("../worker-alpha", ".cartographer/worktrees/worker-beta")}, "broad_proposed_worktree"),
            ({"proposed_worktrees": ("tmp/worker-alpha", ".cartographer/worktrees/worker-beta")}, "proposed_worktree_must_be_cartographer_scoped"),
            ({"branch_worktree_approval_id": "other-approval"}, "wrong_branch_worktree_approval"),
            ({"coordination_receipt_path": "source_proxy/receipt.md"}, "coordination_receipt_path_must_be_docs"),
            ({"coordination_receipt_path": "docs/receipt.json"}, "coordination_receipt_path_must_be_markdown"),
            ({"trust_tier": "tier-3"}, "wrong_trust_tier"),
            ({"approval_token_id": "other-token"}, "wrong_approval_token"),
            ({"status": "approved"}, "status_must_remain_proposed"),
            ({"verification_plan": ()}, "missing_verification_plan"),
            ({"rollback_guidance": "Force push the rollback."}, "rollback_guidance_must_not_recommend_force"),
            ({"created_at": "2026-05-23T12:10:00Z"}, "created_at_in_future"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_controlled_multi_worker_branch_workflow(
                    {**self._workflow().to_dict(), **override},
                    expected_trust_tier="tier-1",
                    expected_approval_token_id="approval-token-plan-9-phase-9-2-branch-worktree",
                    expected_branch_worktree_approval_id="branch-worktree-approval-plan-9-phase-9-2",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.branch_creation_enabled)
                self.assertFalse(result.worktree_creation_enabled)
                self.assertFalse(result.worker_spawn_enabled)

    def test_module_exposes_no_execution_git_creation_api_mutation_or_storage_surface(self) -> None:
        source = inspect.getsource(multi_worker_branch_workflow)
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

    def test_multi_worker_branch_api_preview_is_design_only(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/expansion/multi-worker-branch/workflow")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["api_preview_only"])
        self.assertEqual(payload["multi_worker_branch_status"]["phase"], CONTROLLED_MULTI_WORKER_BRANCH_WORKFLOW_PHASE)
        self.assertEqual(payload["validation"]["status"], "accepted")
        self.assertFalse(payload["worker_spawn_enabled"])
        self.assertFalse(payload["task_execution_enabled"])
        self.assertFalse(payload["queue_execution_enabled"])
        self.assertFalse(payload["branch_creation_enabled"])
        self.assertFalse(payload["worktree_creation_enabled"])
        self.assertFalse(payload["command_execution_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])

    @staticmethod
    def _workflow() -> ControlledMultiWorkerBranchWorkflow:
        return ControlledMultiWorkerBranchWorkflow(
            workflow_id="multi-worker-branch-plan-9-2-1",
            worker_slots=(
                MultiWorkerSlot(worker_id="worker-alpha", task_id="task-docs-a", file_zone=("docs/a.md",)),
                MultiWorkerSlot(worker_id="worker-beta", task_id="task-docs-b", file_zone=("docs/b.md",)),
            ),
            proposed_branches=("cartographer/worker-alpha", "cartographer/worker-beta"),
            proposed_worktrees=(".cartographer/worktrees/worker-alpha", ".cartographer/worktrees/worker-beta"),
            branch_worktree_approval_id="branch-worktree-approval-plan-9-phase-9-2",
            coordination_receipt_path="docs/cartographer-live-receipts/multi-worker-branch-plan-9-2-1.md",
            rollback_guidance="No branch or worktree has been created; discard workflow design if not approved.",
            verification_plan=("manual_review_only", "confirm exact worker/file zones before separate approval"),
            trust_tier="tier-1",
            approval_token_id="approval-token-plan-9-phase-9-2-branch-worktree",
            status="proposed",
            created_at="2026-05-23T12:00:00Z",
        )

    @staticmethod
    def _slot(worker_id: str, task_id: str, file_zone: tuple[str, ...]) -> MultiWorkerSlot:
        return MultiWorkerSlot(worker_id=worker_id, task_id=task_id, file_zone=file_zone)

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 23, 12, 5, tzinfo=UTC)


def _test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(cartographer_router)
    return test_app


if __name__ == "__main__":
    unittest.main()
