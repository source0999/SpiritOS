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
from source_proxy.cartographer import local_commit_gate
from source_proxy.cartographer.local_commit_gate import (
    AUTO_SAFE_LOCAL_COMMIT_PHASE,
    AUTO_SAFE_LOCAL_COMMIT_PREFIXES,
    FORBIDDEN_LOCAL_COMMIT_AUTHORITIES,
    HUMAN_APPROVED_LOCAL_COMMIT_PERMISSION_PHRASE,
    HUMAN_APPROVED_LOCAL_COMMIT_PHASE,
    LOCAL_COMMIT_DIRTY_TREE_EXPECTATIONS,
    LOCAL_COMMIT_PROPOSAL_MODEL_PHASE,
    LOCAL_COMMIT_PROPOSAL_STATUSES,
    LOCAL_COMMIT_REQUIRED_FIELDS,
    LocalCommitProposal,
    LocalCommitVerificationResult,
    build_local_commit_proposal_model_status,
    run_auto_safe_local_commit,
    run_human_approved_local_commit,
    validate_local_commit_proposal,
)


class CartographerLocalCommitGateTests(unittest.TestCase):
    def test_status_is_model_only_and_grants_no_commit_authority(self) -> None:
        status = build_local_commit_proposal_model_status()

        self.assertEqual(status["phase"], LOCAL_COMMIT_PROPOSAL_MODEL_PHASE)
        self.assertEqual(status["status"], "model-only")
        self.assertEqual(status["proposal_statuses"], LOCAL_COMMIT_PROPOSAL_STATUSES)
        self.assertEqual(status["dirty_tree_expectations"], LOCAL_COMMIT_DIRTY_TREE_EXPECTATIONS)
        self.assertEqual(status["required_fields"], LOCAL_COMMIT_REQUIRED_FIELDS)
        self.assertEqual(status["forbidden_authorities"], FORBIDDEN_LOCAL_COMMIT_AUTHORITIES)
        self.assertTrue(status["proposal_only"])
        self.assertFalse(status["commit_enabled"])
        self.assertFalse(status["staging_enabled"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])
        self.assertFalse(status["file_write_authority_granted"])
        self.assertFalse(status["api_mutation_available"])
        self.assertFalse(status["durable_storage_available"])
        self.assertTrue(status["proposal_receipt_available"])

    def test_commit_proposal_captures_plan_9_1_fields_as_data(self) -> None:
        payload = self._proposal().to_dict()

        self.assertEqual(payload["proposal_id"], "commit-proposal-plan-9-1")
        self.assertEqual(payload["exact_file_list"], ("docs/cartographer-live-receipts/example.md",))
        self.assertEqual(payload["exact_commit_message"], "Add Cartographer receipt evidence")
        self.assertEqual(payload["verification_result"]["status"], "passed")
        self.assertEqual(payload["rollback_command"], "git revert abc1234")
        self.assertEqual(payload["expected_head"], "abc1234")
        self.assertEqual(payload["branch"], "main")
        self.assertEqual(payload["dirty_tree_expectation"], "exact_files_only")
        self.assertEqual(payload["blocked_files"], ("source_proxy/api/cartographer.py",))
        self.assertEqual(payload["status"], "proposed")
        self.assertEqual(payload["task_ids"], ("task-plan-9-1",))
        self.assertEqual(payload["receipt_paths"], ("docs/cartographer-live-receipts/example.md",))
        self.assertEqual(payload["approval_token_id"], "approval-token-plan-9-phase-1")
        self.assertTrue(payload["model_only"])
        self.assertTrue(payload["proposal_only"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["staging_enabled"])
        self.assertFalse(payload["push_enabled"])

    def test_valid_proposal_accepts_without_staging_or_commit(self) -> None:
        result = validate_local_commit_proposal(
            self._proposal(),
            expected_approval_token_id="approval-token-plan-9-phase-1",
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.proposal_id, "commit-proposal-plan-9-1")
        self.assertEqual(result.exact_file_list, ("docs/cartographer-live-receipts/example.md",))
        self.assertEqual(result.exact_commit_message, "Add Cartographer receipt evidence")
        self.assertEqual(result.rollback_command, "git revert abc1234")
        self.assertEqual(result.verification_checks, ("pytest:local_commit_gate", "git diff --check"))
        self.assertEqual(result.expected_head, "abc1234")
        self.assertEqual(result.branch, "main")
        self.assertEqual(result.dirty_tree_expectation, "exact_files_only")
        self.assertEqual(result.blocked_files, ("source_proxy/api/cartographer.py",))
        self.assertEqual(result.proposal_status, "proposed")
        self.assertEqual(result.task_ids, ("task-plan-9-1",))
        self.assertEqual(result.receipt_paths, ("docs/cartographer-live-receipts/example.md",))
        self.assertEqual(result.approval_token_id, "approval-token-plan-9-phase-1")
        self.assertTrue(result.model_only)
        self.assertTrue(result.proposal_only)
        self.assertFalse(result.commit_enabled)
        self.assertFalse(result.staging_enabled)
        self.assertFalse(result.push_enabled)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.git_mutation_authority_granted)
        self.assertFalse(result.file_write_authority_granted)
        self.assertFalse(result.api_mutation_available)
        self.assertFalse(result.durable_storage_available)
        self.assertIsNotNone(result.proposal_receipt)
        self.assertEqual(
            result.proposal_receipt["schema_version"],
            "cartographer.local_commit_proposal_receipt.v1",
        )
        self.assertEqual(result.proposal_receipt["proposal_id"], "commit-proposal-plan-9-1")
        self.assertEqual(result.proposal_receipt["exact_file_count"], 1)
        self.assertEqual(
            result.proposal_receipt["exact_file_list"],
            ("docs/cartographer-live-receipts/example.md",),
        )
        self.assertEqual(result.proposal_receipt["rollback_command"], "git revert abc1234")
        self.assertEqual(
            result.proposal_receipt["verification_checks"],
            ("pytest:local_commit_gate", "git diff --check"),
        )
        self.assertFalse(result.proposal_receipt["staging_performed"])
        self.assertFalse(result.proposal_receipt["commit_performed"])
        self.assertFalse(result.proposal_receipt["push_performed"])
        self.assertFalse(result.proposal_receipt["branch_or_worktree_created"])
        self.assertFalse(result.proposal_receipt["command_execution_performed"])
        self.assertFalse(result.proposal_receipt["git_mutation_performed"])
        self.assertFalse(result.proposal_receipt["file_write_performed"])
        self.assertFalse(result.proposal_receipt["approval_token_consumed"])
        self.assertFalse(result.proposal_receipt["self_approval_allowed"])
        self.assertFalse(result.proposal_receipt["durable_storage_performed"])

    def test_required_fields_fail_closed(self) -> None:
        for field in LOCAL_COMMIT_REQUIRED_FIELDS:
            payload = self._proposal().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_local_commit_proposal(
                    payload,
                    expected_approval_token_id="approval-token-plan-9-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertTrue(result.blocked)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_exact_scope_token_verification_and_status_rules_fail_closed(self) -> None:
        cases = [
            ({"exact_file_list": ()}, "missing_exact_file_list"),
            ({"exact_file_list": ("docs/*.md",)}, "broad_exact_file_list_entry"),
            ({"exact_file_list": ("docs/a.md", "docs/a.md")}, "duplicate_exact_file_list_entry"),
            ({"exact_commit_message": "wip"}, "commit_message_too_vague"),
            ({"exact_commit_message": "Title\nBody"}, "commit_message_must_be_exact_single_line"),
            ({"verification_result": {"status": "failed", "checks": ("pytest",), "checked_at": "2026-05-23T12:00:00Z"}}, "verification_not_passed"),
            ({"rollback_command": "git reset --hard HEAD~1"}, "rollback_command_must_be_git_revert"),
            ({"expected_head": "abc"}, "expected_head_too_short"),
            ({"dirty_tree_expectation": "unknown"}, "unknown_dirty_tree_expectation"),
            ({"status": "approved_later_phase"}, "approval_status_not_allowed_in_phase_9_1"),
            ({"status": "committed"}, "unknown_proposal_status"),
            ({"task_ids": ()}, "missing_task_ids"),
            ({"receipt_paths": ()}, "missing_receipt_paths"),
            ({"receipt_paths": ("docs/other.md",)}, "receipt_paths_must_be_in_exact_file_list"),
            ({"blocked_files": ("docs/cartographer-live-receipts/example.md",)}, "blocked_file_in_exact_file_list"),
            ({"approval_token_id": "other-token"}, "wrong_approval_token"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_local_commit_proposal(
                    {**self._proposal().to_dict(), **override},
                    expected_approval_token_id="approval-token-plan-9-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.commit_enabled)
                self.assertFalse(result.staging_enabled)
                self.assertFalse(result.push_enabled)

    def test_phase_9_1_module_limits_git_surface_to_exact_local_commit(self) -> None:
        source = inspect.getsource(local_commit_gate)
        forbidden_fragments = (
            "os.system",
            "open(",
            "source_proxy.api",
            "requests",
            "urllib",
            "socket",
            "shell=True",
            '("git", "add"',
            '("git", "commit"',
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
        self.assertIn("subprocess.run", source)
        self.assertIn('("git", *args)', source)

    def test_commit_proposal_get_api_is_preview_only(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/commit/proposal")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["api_preview_only"])
        self.assertEqual(payload["commit_proposal"]["phase"], LOCAL_COMMIT_PROPOSAL_MODEL_PHASE)
        self.assertTrue(payload["commit_proposal"]["proposal_receipt_available"])
        self.assertEqual(payload["validation"]["status"], "accepted")
        self.assertEqual(
            payload["validation"]["proposal_receipt"]["schema_version"],
            "cartographer.local_commit_proposal_receipt.v1",
        )
        self.assertFalse(payload["validation"]["proposal_receipt"]["commit_performed"])
        self.assertFalse(payload["staging_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["command_authority_granted"])
        self.assertFalse(payload["git_mutation_authority_granted"])

    def test_commit_proposal_post_api_validates_without_commit_authority(self) -> None:
        response = TestClient(_test_app()).post(
            "/v1/cartographer/commit/proposal",
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
        self.assertFalse(payload["staging_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["command_authority_granted"])
        self.assertFalse(payload["git_mutation_authority_granted"])

    def test_human_approved_local_commit_commits_exact_file_only_in_temp_repo(self) -> None:
        with TemporaryDirectory() as directory:
            repo = _init_temp_repo(Path(directory))
            receipt = repo / "docs" / "cartographer-live-receipts" / "example.md"
            receipt.write_text("receipt v2\n", encoding="utf-8")
            expected_head = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_human_approved_local_commit(
                self._proposal(expected_head=expected_head),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase=HUMAN_APPROVED_LOCAL_COMMIT_PERMISSION_PHRASE,
                now=self._now(),
            )

            self.assertEqual(result.phase, HUMAN_APPROVED_LOCAL_COMMIT_PHASE)
            self.assertEqual(result.status, "committed")
            self.assertTrue(result.committed)
            self.assertFalse(result.blocked)
            self.assertEqual(result.reasons, ())
            self.assertEqual(result.exact_file_list, ("docs/cartographer-live-receipts/example.md",))
            self.assertEqual(result.exact_commit_message, "Add Cartographer receipt evidence")
            self.assertNotEqual(result.new_head, expected_head)
            self.assertEqual(result.rollback_command, f"git revert {result.new_head}")
            self.assertTrue(result.human_approval_required)
            self.assertTrue(result.exact_file_list_only)
            self.assertFalse(result.broad_staging_allowed)
            self.assertFalse(result.push_enabled)
            self.assertFalse(result.branch_enabled)
            self.assertFalse(result.worktree_enabled)
            self.assertFalse(result.stash_enabled)
            self.assertFalse(result.clean_enabled)
            self.assertFalse(result.reset_enabled)
            self.assertFalse(result.checkout_enabled)
            self.assertFalse(result.api_mutation_available)
            self.assertFalse(result.self_approval_allowed)
            self.assertEqual(_git(repo, "log", "-1", "--format=%s").stdout.strip(), "Add Cartographer receipt evidence")
            self.assertEqual(_git(repo, "status", "--short").stdout.strip(), "")

    def test_human_approved_local_commit_requires_exact_human_approval(self) -> None:
        with TemporaryDirectory() as directory:
            repo = _init_temp_repo(Path(directory))
            receipt = repo / "docs" / "cartographer-live-receipts" / "example.md"
            receipt.write_text("receipt v2\n", encoding="utf-8")
            expected_head = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_human_approved_local_commit(
                self._proposal(expected_head=expected_head),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase="approve it",
                now=self._now(),
            )

            self.assertFalse(result.committed)
            self.assertTrue(result.blocked)
            self.assertIn("missing_exact_human_approval_phrase", result.reasons)
            self.assertEqual(_git(repo, "rev-parse", "--verify", "HEAD").stdout.strip(), expected_head)
            self.assertIn(" M docs/cartographer-live-receipts/example.md", _git(repo, "status", "--short").stdout)

    def test_human_approved_local_commit_blocks_expected_head_mismatch(self) -> None:
        with TemporaryDirectory() as directory:
            repo = _init_temp_repo(Path(directory))
            receipt = repo / "docs" / "cartographer-live-receipts" / "example.md"
            receipt.write_text("receipt v2\n", encoding="utf-8")
            expected_head = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_human_approved_local_commit(
                self._proposal(expected_head="0" * 40),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase=HUMAN_APPROVED_LOCAL_COMMIT_PERMISSION_PHRASE,
                now=self._now(),
            )

            self.assertFalse(result.committed)
            self.assertIn("expected_head_mismatch", result.reasons)
            self.assertEqual(_git(repo, "rev-parse", "--verify", "HEAD").stdout.strip(), expected_head)

    def test_human_approved_local_commit_blocks_extra_staged_files(self) -> None:
        with TemporaryDirectory() as directory:
            repo = _init_temp_repo(Path(directory))
            receipt = repo / "docs" / "cartographer-live-receipts" / "example.md"
            other = repo / "docs" / "cartographer-live-receipts" / "other.md"
            other.write_text("other\n", encoding="utf-8")
            _git(repo, "add", "--", "docs/cartographer-live-receipts/other.md")
            receipt.write_text("receipt v2\n", encoding="utf-8")
            expected_head = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_human_approved_local_commit(
                self._proposal(expected_head=expected_head),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase=HUMAN_APPROVED_LOCAL_COMMIT_PERMISSION_PHRASE,
                now=self._now(),
            )

            self.assertFalse(result.committed)
            self.assertTrue(result.blocked)
            self.assertIn("staged_files_do_not_match_exact_file_list", result.reasons)
            self.assertEqual(_git(repo, "rev-parse", "--verify", "HEAD").stdout.strip(), expected_head)

    def test_human_approved_local_commit_blocks_path_escape(self) -> None:
        with TemporaryDirectory() as directory:
            repo = _init_temp_repo(Path(directory))
            expected_head = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_human_approved_local_commit(
                self._proposal(
                    expected_head=expected_head,
                    exact_file_list=("../outside.md",),
                ),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                human_approval_phrase=HUMAN_APPROVED_LOCAL_COMMIT_PERMISSION_PHRASE,
                now=self._now(),
            )

            self.assertFalse(result.committed)
            self.assertIn("broad_exact_file_list_entry", result.reasons)
            self.assertIn("exact_file_outside_repo", result.reasons)

    def test_auto_safe_local_commit_blocks_even_after_soak_promotion(self) -> None:
        with TemporaryDirectory() as directory:
            repo = _init_temp_repo(Path(directory))
            receipt = repo / "docs" / "cartographer-live-receipts" / "example.md"
            receipt.write_text("receipt v2\n", encoding="utf-8")
            expected_head = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_auto_safe_local_commit(
                self._proposal(expected_head=expected_head),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                soak_promoted=True,
                now=self._now(),
            )

            self.assertEqual(result.phase, AUTO_SAFE_LOCAL_COMMIT_PHASE)
            self.assertEqual(result.status, "blocked")
            self.assertFalse(result.auto_committed)
            self.assertTrue(result.blocked)
            self.assertIn("auto_local_commit_requires_exact_human_approval", result.reasons)
            self.assertTrue(result.soak_promoted)
            self.assertEqual(result.exact_file_list, ("docs/cartographer-live-receipts/example.md",))
            self.assertTrue(result.exact_file_list_only)
            self.assertTrue(result.safe_docs_evidence_receipts_only)
            self.assertFalse(result.source_files_allowed)
            self.assertFalse(result.broad_staging_allowed)
            self.assertFalse(result.push_enabled)
            self.assertFalse(result.branch_enabled)
            self.assertFalse(result.worktree_enabled)
            self.assertFalse(result.stash_enabled)
            self.assertFalse(result.clean_enabled)
            self.assertFalse(result.reset_enabled)
            self.assertFalse(result.checkout_enabled)
            self.assertFalse(result.api_mutation_available)
            self.assertFalse(result.self_approval_allowed)
            self.assertIsNone(result.rollback_command)
            self.assertEqual(_git(repo, "rev-parse", "--verify", "HEAD").stdout.strip(), expected_head)

    def test_auto_safe_local_commit_requires_soak_promotion(self) -> None:
        with TemporaryDirectory() as directory:
            repo = _init_temp_repo(Path(directory))
            receipt = repo / "docs" / "cartographer-live-receipts" / "example.md"
            receipt.write_text("receipt v2\n", encoding="utf-8")
            expected_head = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_auto_safe_local_commit(
                self._proposal(expected_head=expected_head),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                soak_promoted=False,
                now=self._now(),
            )

            self.assertFalse(result.auto_committed)
            self.assertTrue(result.blocked)
            self.assertFalse(result.soak_promoted)
            self.assertIn("auto_local_commit_requires_exact_human_approval", result.reasons)
            self.assertIn("auto_local_commit_requires_soak_promotion", result.reasons)
            self.assertEqual(_git(repo, "rev-parse", "--verify", "HEAD").stdout.strip(), expected_head)

    def test_auto_safe_local_commit_rejects_source_files(self) -> None:
        with TemporaryDirectory() as directory:
            repo = _init_temp_repo(Path(directory))
            source_file = repo / "source_proxy" / "cartographer"
            source_file.mkdir(parents=True)
            (source_file / "unsafe.py").write_text("value = 2\n", encoding="utf-8")
            expected_head = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_auto_safe_local_commit(
                self._proposal(
                    expected_head=expected_head,
                    exact_file_list=("source_proxy/cartographer/unsafe.py",),
                ),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                soak_promoted=True,
                now=self._now(),
            )

            self.assertFalse(result.auto_committed)
            self.assertIn("unsafe_auto_commit_file_class", result.reasons)
            self.assertFalse(result.source_files_allowed)
            self.assertEqual(_git(repo, "rev-parse", "--verify", "HEAD").stdout.strip(), expected_head)

    def test_auto_safe_local_commit_rejects_non_markdown_docs(self) -> None:
        with TemporaryDirectory() as directory:
            repo = _init_temp_repo(Path(directory))
            artifact = repo / "docs" / "cartographer-live-receipts" / "artifact.json"
            artifact.write_text("{\"ok\": true}\n", encoding="utf-8")
            expected_head = _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()

            result = run_auto_safe_local_commit(
                self._proposal(
                    expected_head=expected_head,
                    exact_file_list=("docs/cartographer-live-receipts/artifact.json",),
                ),
                repo_root=repo,
                expected_approval_token_id="approval-token-plan-9-phase-1",
                soak_promoted=True,
                now=self._now(),
            )

            self.assertFalse(result.auto_committed)
            self.assertIn("unsafe_auto_commit_file_class", result.reasons)

    def test_auto_safe_local_commit_prefixes_are_docs_evidence_and_receipts(self) -> None:
        self.assertEqual(
            AUTO_SAFE_LOCAL_COMMIT_PREFIXES,
            (
                "docs/cartographer-live-receipts/",
                "docs/cartographer-receipts/",
                "docs/cartographer-evidence/",
                "docs/cartographer-daily-driver-autonomy-plan-",
            ),
        )

    @staticmethod
    def _proposal(
        *,
        expected_head: str = "abc1234",
        exact_file_list: tuple[str, ...] = ("docs/cartographer-live-receipts/example.md",),
    ) -> LocalCommitProposal:
        return LocalCommitProposal(
            proposal_id="commit-proposal-plan-9-1",
            exact_file_list=exact_file_list,
            exact_commit_message="Add Cartographer receipt evidence",
            verification_result=LocalCommitVerificationResult(
                status="passed",
                checks=("pytest:local_commit_gate", "git diff --check"),
                checked_at="2026-05-23T12:00:00Z",
            ).to_dict(),
            rollback_command="git revert abc1234",
            expected_head=expected_head,
            branch="main",
            dirty_tree_expectation="exact_files_only",
            blocked_files=("source_proxy/api/cartographer.py",),
            status="proposed",
            task_ids=("task-plan-9-1",),
            receipt_paths=("docs/cartographer-live-receipts/example.md",),
            approval_token_id="approval-token-plan-9-phase-1",
            created_at="2026-05-23T12:00:00Z",
        )

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 23, 12, 5, tzinfo=UTC)

def _test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(cartographer_router)
    return test_app


def _init_temp_repo(repo: Path) -> Path:
    _git(repo, "init")
    _git(repo, "config", "user.email", "cartographer@example.test")
    _git(repo, "config", "user.name", "Cartographer Test")
    receipt_dir = repo / "docs" / "cartographer-live-receipts"
    receipt_dir.mkdir(parents=True)
    (receipt_dir / "example.md").write_text("receipt v1\n", encoding="utf-8")
    _git(repo, "add", "--", "docs/cartographer-live-receipts/example.md")
    _git(repo, "commit", "-m", "Initial receipt")
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
