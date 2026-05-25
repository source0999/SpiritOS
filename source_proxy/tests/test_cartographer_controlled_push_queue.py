from __future__ import annotations

from datetime import UTC, datetime
import inspect
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.cartographer import controlled_push_queue
from source_proxy.cartographer.controlled_push_queue import (
    FORBIDDEN_PUSH_AUTHORITIES,
    HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PERMISSION_PHRASE,
    HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PHASE,
    ISOLATED_BRANCH_AUTO_PUSH_DECISION_GATE_PHASE,
    PROTECTED_BASE_BRANCHES,
    PUSH_RECEIPT_AND_ROLLBACK_GUIDANCE_PHASE,
    PUSH_PROPOSAL_ONLY_PHASE,
    PUSH_PROPOSAL_REQUIRED_FIELDS,
    PUSH_PROPOSAL_RISK_LEVELS,
    PushProposal,
    PushProposalVerification,
    build_isolated_branch_auto_push_decision_gate,
    build_push_receipt_and_rollback_guidance,
    build_push_proposal_only_status,
    run_human_approved_dedicated_branch_push,
    validate_push_proposal,
)


class CartographerControlledPushQueueTests(unittest.TestCase):
    def test_status_is_push_proposal_only_without_push_authority(self) -> None:
        status = build_push_proposal_only_status()

        self.assertEqual(status["phase"], PUSH_PROPOSAL_ONLY_PHASE)
        self.assertEqual(status["status"], "proposal-only")
        self.assertEqual(status["required_fields"], PUSH_PROPOSAL_REQUIRED_FIELDS)
        self.assertEqual(status["risk_levels"], PUSH_PROPOSAL_RISK_LEVELS)
        self.assertEqual(status["forbidden_authorities"], FORBIDDEN_PUSH_AUTHORITIES)
        self.assertEqual(status["protected_base_branches"], PROTECTED_BASE_BRANCHES)
        self.assertTrue(status["proposal_only"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["force_push_enabled"])
        self.assertFalse(status["tag_push_enabled"])
        self.assertFalse(status["merge_enabled"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["api_mutation_available"])
        self.assertFalse(status["durable_storage_available"])
        self.assertTrue(status["proposal_receipt_available"])

    def test_push_proposal_captures_plan_9_2_fields_as_data(self) -> None:
        payload = self._proposal().to_dict()

        self.assertEqual(payload["proposal_id"], "push-proposal-plan-9-1")
        self.assertEqual(payload["remote"], "origin")
        self.assertEqual(payload["branch"], "cartographer/plan-9-proposal")
        self.assertEqual(payload["upstream"], "origin/cartographer/plan-9-proposal")
        self.assertEqual(payload["ahead_count"], 1)
        self.assertEqual(payload["behind_count"], 0)
        self.assertEqual(payload["local_commits"], ("a" * 40,))
        self.assertEqual(payload["commit_sha"], "a" * 40)
        self.assertEqual(payload["clean_status"], "clean")
        self.assertEqual(payload["exact_file_lineage"], ("docs/cartographer-live-receipts/example.md",))
        self.assertEqual(payload["verification"]["status"], "passed")
        self.assertEqual(payload["verification_receipts"], ("docs/cartographer-live-receipts/example.md",))
        self.assertEqual(payload["rollback_guidance"], "Revert the exact commit locally, then request a new reviewed push proposal.")
        self.assertEqual(payload["approval_token_id"], "approval-token-plan-9-phase-1")
        self.assertEqual(payload["risk"], "low")
        self.assertTrue(payload["proposal_only"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["force_push_enabled"])
        self.assertFalse(payload["tag_push_enabled"])

    def test_valid_push_proposal_accepts_without_push_authority(self) -> None:
        result = validate_push_proposal(
            self._proposal(),
            expected_approval_token_id="approval-token-plan-9-phase-1",
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.proposal_id, "push-proposal-plan-9-1")
        self.assertEqual(result.remote, "origin")
        self.assertEqual(result.branch, "cartographer/plan-9-proposal")
        self.assertEqual(result.upstream, "origin/cartographer/plan-9-proposal")
        self.assertEqual(result.ahead_count, 1)
        self.assertEqual(result.behind_count, 0)
        self.assertEqual(result.local_commits, ("a" * 40,))
        self.assertEqual(result.commit_sha, "a" * 40)
        self.assertEqual(result.clean_status, "clean")
        self.assertEqual(result.exact_file_lineage, ("docs/cartographer-live-receipts/example.md",))
        self.assertEqual(result.verification_receipts, ("docs/cartographer-live-receipts/example.md",))
        self.assertEqual(result.approval_token_id, "approval-token-plan-9-phase-1")
        self.assertEqual(result.risk, "low")
        self.assertTrue(result.proposal_only)
        self.assertFalse(result.push_enabled)
        self.assertFalse(result.force_push_enabled)
        self.assertFalse(result.tag_push_enabled)
        self.assertFalse(result.merge_enabled)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.api_mutation_available)
        self.assertFalse(result.durable_storage_available)
        self.assertIsNotNone(result.proposal_receipt)
        self.assertEqual(
            result.proposal_receipt["schema_version"],
            "cartographer.push_proposal_receipt.v1",
        )
        self.assertEqual(result.proposal_receipt["proposal_id"], "push-proposal-plan-9-1")
        self.assertEqual(result.proposal_receipt["remote"], "origin")
        self.assertEqual(result.proposal_receipt["branch"], "cartographer/plan-9-proposal")
        self.assertEqual(result.proposal_receipt["local_commit_count"], 1)
        self.assertEqual(result.proposal_receipt["exact_file_lineage_count"], 1)
        self.assertEqual(
            result.proposal_receipt["verification_checks"],
            ("pytest:controlled_push_queue", "git diff --check"),
        )
        self.assertFalse(result.proposal_receipt["push_performed"])
        self.assertFalse(result.proposal_receipt["force_push_performed"])
        self.assertFalse(result.proposal_receipt["tag_push_performed"])
        self.assertFalse(result.proposal_receipt["merge_performed"])
        self.assertFalse(result.proposal_receipt["branch_or_worktree_created"])
        self.assertFalse(result.proposal_receipt["command_execution_performed"])
        self.assertFalse(result.proposal_receipt["git_mutation_performed"])
        self.assertFalse(result.proposal_receipt["approval_token_consumed"])
        self.assertFalse(result.proposal_receipt["self_approval_allowed"])
        self.assertFalse(result.proposal_receipt["provider_call_performed"])
        self.assertFalse(result.proposal_receipt["durable_storage_performed"])

    def test_required_fields_fail_closed(self) -> None:
        for field in PUSH_PROPOSAL_REQUIRED_FIELDS:
            payload = self._proposal().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_push_proposal(
                    payload,
                    expected_approval_token_id="approval-token-plan-9-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertTrue(result.blocked)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_push_scope_token_clean_status_and_verification_rules_fail_closed(self) -> None:
        cases = [
            ({"remote": "upstream"}, "remote_must_be_exact_origin"),
            ({"branch": "main"}, "protected_base_branch_not_allowed_in_phase_9_2"),
            ({"branch": "feature/work"}, "branch_must_be_dedicated_cartographer_branch"),
            ({"upstream": "origin/other"}, "upstream_must_match_origin_branch"),
            ({"ahead_count": -1}, "ahead_count_must_not_be_negative"),
            ({"behind_count": 1}, "behind_count_must_be_zero"),
            ({"local_commits": ()}, "missing_local_commits"),
            ({"local_commits": ("b" * 40,)}, "commit_sha_must_be_in_local_commits"),
            ({"commit_sha": "abc1234"}, "commit_sha_must_be_full_hex_sha"),
            ({"clean_status": "dirty"}, "clean_status_required"),
            ({"exact_file_lineage": ()}, "missing_exact_file_lineage"),
            ({"exact_file_lineage": ("docs/*.md",)}, "broad_exact_file_lineage_entry"),
            ({"exact_file_lineage": ("docs/a.md", "docs/a.md")}, "duplicate_exact_file_lineage_entry"),
            ({"verification_receipts": ()}, "missing_verification_receipts"),
            ({"verification": {"status": "failed", "checks": ("pytest",), "checked_at": "2026-05-23T12:00:00Z"}}, "verification_not_passed"),
            ({"rollback_guidance": "Force push the remote branch."}, "rollback_guidance_must_not_recommend_force"),
            ({"approval_token_id": "other-token"}, "wrong_approval_token"),
            ({"risk": "unknown"}, "unknown_push_risk"),
            ({"risk": "blocked"}, "blocked_risk_cannot_be_pushed"),
            ({"created_at": "2026-05-23T12:10:00Z"}, "created_at_in_future"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_push_proposal(
                    {**self._proposal().to_dict(), **override},
                    expected_approval_token_id="approval-token-plan-9-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.push_enabled)
                self.assertFalse(result.force_push_enabled)
                self.assertFalse(result.tag_push_enabled)

    def test_phase_9_2_module_limits_push_surface_to_exact_dedicated_branch(self) -> None:
        source = inspect.getsource(controlled_push_queue)
        forbidden_fragments = (
            "os.system",
            "open(",
            ".write(",
            "write_text(",
            "source_proxy.api",
            "requests",
            "urllib",
            "socket",
            "shell=True",
            '("git", "push"',
            "--force",
            "--tags",
            ":main",
            ":master",
            ":trunk",
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
        self.assertIn("subprocess.run", source)
        self.assertIn('("git", *args)', source)
        self.assertIn("commit_sha}:refs/heads/{branch}", source)

    def test_push_proposal_get_api_is_preview_only(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/push/proposal")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["api_preview_only"])
        self.assertEqual(payload["push_proposal"]["phase"], PUSH_PROPOSAL_ONLY_PHASE)
        self.assertTrue(payload["push_proposal"]["proposal_receipt_available"])
        self.assertEqual(payload["validation"]["status"], "accepted")
        self.assertEqual(
            payload["validation"]["proposal_receipt"]["schema_version"],
            "cartographer.push_proposal_receipt.v1",
        )
        self.assertFalse(payload["validation"]["proposal_receipt"]["push_performed"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["force_push_enabled"])
        self.assertFalse(payload["tag_push_enabled"])
        self.assertFalse(payload["merge_enabled"])
        self.assertFalse(payload["command_authority_granted"])

    def test_push_proposal_post_api_validates_without_push_authority(self) -> None:
        response = TestClient(_test_app()).post(
            "/v1/cartographer/push/proposal",
            json={
                "proposal": self._proposal().to_dict(),
                "expected_approval_token_id": "wrong-token",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["validation"]["status"], "blocked")
        self.assertIn("wrong_approval_token", payload["validation"]["reasons"])
        self.assertTrue(payload["api_preview_only"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["force_push_enabled"])
        self.assertFalse(payload["tag_push_enabled"])
        self.assertFalse(payload["merge_enabled"])
        self.assertFalse(payload["command_authority_granted"])

    def test_human_approved_push_pushes_exact_sha_to_dedicated_branch_in_temp_repo(self) -> None:
        with TemporaryDirectory() as directory:
            temp_root = Path(directory)
            remote = temp_root / "remote.git"
            repo = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            _init_temp_repo(repo, remote)
            commit_sha = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_human_approved_dedicated_branch_push(
                self._proposal(commit_sha=commit_sha),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase=HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PERMISSION_PHRASE,
                now=self._now(),
            )
            remote_head = _git(remote, "rev-parse", "refs/heads/cartographer/plan-9-proposal").stdout.strip()

            self.assertEqual(result.phase, HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PHASE)
            self.assertEqual(result.status, "pushed")
            self.assertTrue(result.pushed)
            self.assertFalse(result.blocked)
            self.assertEqual(result.reasons, ())
            self.assertEqual(result.remote, "origin")
            self.assertEqual(result.branch, "cartographer/plan-9-proposal")
            self.assertEqual(result.commit_sha, commit_sha)
            self.assertEqual(remote_head, commit_sha)
            self.assertTrue(result.human_approval_required)
            self.assertTrue(result.exact_commit_sha_required)
            self.assertTrue(result.dedicated_branch_only)
            self.assertFalse(result.push_to_main_enabled)
            self.assertFalse(result.force_push_enabled)
            self.assertFalse(result.tag_push_enabled)
            self.assertFalse(result.merge_enabled)
            self.assertFalse(result.broad_push_enabled)
            self.assertFalse(result.branch_creation_enabled)
            self.assertFalse(result.worktree_enabled)
            self.assertFalse(result.stash_enabled)
            self.assertFalse(result.clean_enabled)
            self.assertFalse(result.reset_enabled)
            self.assertFalse(result.checkout_enabled)
            self.assertFalse(result.self_approval_allowed)

    def test_human_approved_push_requires_exact_human_phrase(self) -> None:
        with TemporaryDirectory() as directory:
            temp_root = Path(directory)
            remote = temp_root / "remote.git"
            repo = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            _init_temp_repo(repo, remote)
            commit_sha = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_human_approved_dedicated_branch_push(
                self._proposal(commit_sha=commit_sha),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase="approve push",
                now=self._now(),
            )

            self.assertFalse(result.pushed)
            self.assertTrue(result.blocked)
            self.assertIn("missing_exact_human_approval_phrase", result.reasons)
            self.assertNotEqual(_git(remote, "rev-parse", "refs/heads/cartographer/plan-9-proposal").returncode, 0)

    def test_human_approved_push_blocks_commit_sha_mismatch(self) -> None:
        with TemporaryDirectory() as directory:
            temp_root = Path(directory)
            remote = temp_root / "remote.git"
            repo = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            _init_temp_repo(repo, remote)

            result = run_human_approved_dedicated_branch_push(
                self._proposal(commit_sha="b" * 40),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase=HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PERMISSION_PHRASE,
                now=self._now(),
            )

            self.assertFalse(result.pushed)
            self.assertIn("commit_sha_mismatch", result.reasons)
            self.assertNotEqual(_git(remote, "rev-parse", "refs/heads/cartographer/plan-9-proposal").returncode, 0)

    def test_human_approved_push_blocks_dirty_worktree(self) -> None:
        with TemporaryDirectory() as directory:
            temp_root = Path(directory)
            remote = temp_root / "remote.git"
            repo = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            _init_temp_repo(repo, remote)
            commit_sha = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()
            (repo / "docs" / "cartographer-live-receipts" / "dirty.md").write_text("dirty\n", encoding="utf-8")

            result = run_human_approved_dedicated_branch_push(
                self._proposal(commit_sha=commit_sha),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase=HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PERMISSION_PHRASE,
                now=self._now(),
            )

            self.assertFalse(result.pushed)
            self.assertIn("working_tree_not_clean", result.reasons)
            self.assertNotEqual(_git(remote, "rev-parse", "refs/heads/cartographer/plan-9-proposal").returncode, 0)

    def test_human_approved_push_blocks_protected_base_branch(self) -> None:
        with TemporaryDirectory() as directory:
            temp_root = Path(directory)
            remote = temp_root / "remote.git"
            repo = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            _init_temp_repo(repo, remote)
            commit_sha = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_human_approved_dedicated_branch_push(
                self._proposal(commit_sha=commit_sha, branch="main"),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase=HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PERMISSION_PHRASE,
                now=self._now(),
            )

            self.assertFalse(result.pushed)
            self.assertIn("protected_base_branch_not_allowed_in_phase_9_2", result.reasons)
            self.assertIn("branch_must_be_dedicated_cartographer_branch", result.reasons)

    def test_push_receipt_records_success_without_new_push_authority(self) -> None:
        with TemporaryDirectory() as directory:
            temp_root = Path(directory)
            remote = temp_root / "remote.git"
            repo = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            _init_temp_repo(repo, remote)
            commit_sha = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()
            proposal = self._proposal(commit_sha=commit_sha)
            result = run_human_approved_dedicated_branch_push(
                proposal,
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase=HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PERMISSION_PHRASE,
                now=self._now(),
            )

            receipt = build_push_receipt_and_rollback_guidance(
                result,
                proposal=proposal,
                now=self._now(),
            )

            self.assertEqual(receipt.phase, PUSH_RECEIPT_AND_ROLLBACK_GUIDANCE_PHASE)
            self.assertEqual(receipt.status, "pushed")
            self.assertTrue(receipt.receipt_id.startswith("push-receipt-push-proposal-plan-9-1-"))
            self.assertEqual(receipt.proposal_id, "push-proposal-plan-9-1")
            self.assertEqual(receipt.remote, "origin")
            self.assertEqual(receipt.branch, "cartographer/plan-9-proposal")
            self.assertEqual(receipt.commit_sha, commit_sha)
            self.assertEqual(receipt.exact_file_lineage, ("docs/cartographer-live-receipts/example.md",))
            self.assertEqual(receipt.approval_token_id, "approval-token-plan-9-phase-1")
            self.assertEqual(receipt.pushed_at, "2026-05-23T12:05:00Z")
            self.assertEqual(receipt.generated_at, "2026-05-23T12:05:00Z")
            self.assertIn("do not force-push", receipt.rollback_guidance)
            self.assertIn("request a new exact human-approved push proposal", receipt.rollback_guidance)
            self.assertEqual(
                receipt.operator_next_steps,
                (
                    "review_remote_branch",
                    "open_pull_request_if_appropriate",
                    "record_any_followup_as_new_exact_proposal",
                ),
            )
            self.assertIn("do_not_force_push", receipt.safety_boundaries)
            self.assertIn("do_not_push_tags", receipt.safety_boundaries)
            self.assertFalse(receipt.durable_storage_written)
            self.assertFalse(receipt.push_performed_by_receipt_builder)
            self.assertFalse(receipt.force_push_allowed)
            self.assertFalse(receipt.tag_push_allowed)
            self.assertFalse(receipt.main_branch_push_allowed)
            self.assertFalse(receipt.auto_push_allowed)

    def test_push_receipt_records_blockers_without_remote_rollback(self) -> None:
        result = run_human_approved_dedicated_branch_push(
            self._proposal(commit_sha="b" * 40),
            repo_root="/missing/repo/root",
            expected_approval_token_id="approval-token-plan-9-phase-1",
            human_approval_phrase="approve push",
            now=self._now(),
        )

        receipt = build_push_receipt_and_rollback_guidance(
            result,
            proposal=self._proposal(commit_sha="b" * 40),
            now=self._now(),
        )

        self.assertEqual(receipt.status, "blocked")
        self.assertIn("No remote rollback is required", receipt.rollback_guidance)
        self.assertIn("missing_exact_human_approval_phrase", receipt.rollback_guidance)
        self.assertEqual(
            receipt.operator_next_steps,
            (
                "review_blockers",
                "do_not_retry_push_without_new_exact_approval",
                "rerun_required_verification_after_fixes",
            ),
        )
        self.assertIn("missing_exact_human_approval_phrase", receipt.evidence["result_reasons"])
        self.assertIn("invalid_repo_root", receipt.evidence["result_reasons"])

    def test_push_receipt_builder_does_not_run_git_or_write_storage(self) -> None:
        source = inspect.getsource(build_push_receipt_and_rollback_guidance)

        forbidden_fragments = (
            "subprocess",
            "_git(",
            "open(",
            ".write(",
            "write_text(",
            "git push",
            "--tags",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    def test_auto_push_decision_gate_defaults_blocked_without_promotion_inputs(self) -> None:
        gate = build_isolated_branch_auto_push_decision_gate(
            self._proposal(),
            expected_approval_token_id="approval-token-plan-9-phase-1",
            soak_passed=False,
            receipt_available=False,
            rollback_guidance_available=False,
            policy_approval_id="",
            now=self._now(),
        )

        self.assertEqual(gate.phase, ISOLATED_BRANCH_AUTO_PUSH_DECISION_GATE_PHASE)
        self.assertEqual(gate.status, "blocked")
        self.assertFalse(gate.candidate)
        self.assertTrue(gate.blocked)
        self.assertIn("auto_push_requires_completed_soak", gate.reasons)
        self.assertIn("auto_push_requires_push_receipt", gate.reasons)
        self.assertIn("auto_push_requires_rollback_guidance", gate.reasons)
        self.assertIn("auto_push_requires_explicit_policy_approval", gate.reasons)
        self.assertFalse(gate.auto_push_enabled)
        self.assertFalse(gate.push_performed)
        self.assertFalse(gate.push_to_main_enabled)
        self.assertFalse(gate.force_push_enabled)
        self.assertFalse(gate.tag_push_enabled)
        self.assertFalse(gate.broad_push_enabled)
        self.assertFalse(gate.self_approval_allowed)
        self.assertFalse(gate.durable_storage_written)
        self.assertFalse(gate.api_mutation_available)

    def test_auto_push_decision_gate_marks_candidate_but_stays_blocked_without_later_promotion(self) -> None:
        gate = build_isolated_branch_auto_push_decision_gate(
            self._proposal(),
            expected_approval_token_id="approval-token-plan-9-phase-1",
            soak_passed=True,
            receipt_available=True,
            rollback_guidance_available=True,
            policy_approval_id="policy-approval-plan-9-4",
            now=self._now(),
        )

        self.assertEqual(gate.status, "blocked_pending_later_promotion")
        self.assertTrue(gate.candidate)
        self.assertTrue(gate.blocked)
        self.assertEqual(gate.reasons, ("auto_push_runtime_not_promoted_in_plan_9",))
        self.assertEqual(gate.proposal_id, "push-proposal-plan-9-1")
        self.assertEqual(gate.remote, "origin")
        self.assertEqual(gate.branch, "cartographer/plan-9-proposal")
        self.assertEqual(gate.commit_sha, "a" * 40)
        self.assertEqual(gate.exact_file_lineage, ("docs/cartographer-live-receipts/example.md",))
        self.assertEqual(gate.approval_token_id, "approval-token-plan-9-phase-1")
        self.assertIn("passed_soak_window", gate.required_inputs)
        self.assertIn("decision_gate_does_not_push", gate.safety_boundaries)
        self.assertIn("auto_push_runtime_remains_disabled_in_plan_9", gate.safety_boundaries)
        self.assertIn("plan_9_auto_push_stays_blocked", gate.safety_boundaries)
        self.assertFalse(gate.auto_push_enabled)
        self.assertFalse(gate.push_performed)
        self.assertIn("later explicit promotion plan", gate.next_authority_required)

    def test_auto_push_decision_gate_rejects_non_isolated_or_unclean_proposals(self) -> None:
        gate = build_isolated_branch_auto_push_decision_gate(
            {**self._proposal(branch="feature/work").to_dict(), "clean_status": "dirty"},
            expected_approval_token_id="approval-token-plan-9-phase-1",
            soak_passed=True,
            receipt_available=True,
            rollback_guidance_available=True,
            policy_approval_id="policy-approval-plan-9-4",
            now=self._now(),
        )

        self.assertFalse(gate.candidate)
        self.assertIn("branch_must_be_dedicated_cartographer_branch", gate.reasons)
        self.assertIn("clean_status_required", gate.reasons)
        self.assertIn("auto_push_requires_isolated_cartographer_branch", gate.reasons)
        self.assertIn("auto_push_requires_clean_status", gate.reasons)
        self.assertFalse(gate.auto_push_enabled)

    def test_auto_push_decision_gate_does_not_run_git_write_storage_or_push(self) -> None:
        source = inspect.getsource(build_isolated_branch_auto_push_decision_gate)

        forbidden_fragments = (
            "subprocess",
            "_git(",
            "open(",
            ".write(",
            "write_text(",
            "git push",
            "--force",
            "--tags",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    @staticmethod
    def _proposal(
        *,
        commit_sha: str = "a" * 40,
        branch: str = "cartographer/plan-9-proposal",
    ) -> PushProposal:
        return PushProposal(
            proposal_id="push-proposal-plan-9-1",
            remote="origin",
            branch=branch,
            upstream=f"origin/{branch}",
            ahead_count=1,
            behind_count=0,
            local_commits=(commit_sha,),
            commit_sha=commit_sha,
            clean_status="clean",
            exact_file_lineage=("docs/cartographer-live-receipts/example.md",),
            verification=PushProposalVerification(
                status="passed",
                checks=("pytest:controlled_push_queue", "git diff --check"),
                checked_at="2026-05-23T12:00:00Z",
            ).to_dict(),
            verification_receipts=("docs/cartographer-live-receipts/example.md",),
            rollback_guidance="Revert the exact commit locally, then request a new reviewed push proposal.",
            approval_token_id="approval-token-plan-9-phase-1",
            risk="low",
            created_at="2026-05-23T12:00:00Z",
        )

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 23, 12, 5, tzinfo=UTC)


def _test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(cartographer_router)
    return test_app


def _init_temp_repo(repo: Path, remote: Path) -> Path:
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "cartographer@example.test")
    _git(repo, "config", "user.name", "Cartographer Test")
    _git(repo, "remote", "add", "origin", str(remote))
    receipt_dir = repo / "docs" / "cartographer-live-receipts"
    receipt_dir.mkdir(parents=True)
    (receipt_dir / "example.md").write_text("receipt\n", encoding="utf-8")
    _git(repo, "add", "--", "docs/cartographer-live-receipts/example.md")
    _git(repo, "commit", "-m", "Add receipt")
    return repo


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )


if __name__ == "__main__":
    unittest.main()
