from __future__ import annotations

from datetime import UTC, datetime, timedelta
import inspect
from pathlib import Path
import tempfile
import unittest

from source_proxy.cartographer import safe_write
from source_proxy.cartographer.approval_token_runtime import (
    APPROVAL_TOKEN_SCHEMA_VERSION,
)
from source_proxy.cartographer.safe_write import (
    build_safe_write_status,
    build_safe_write_verification_receipt_content,
    execute_safe_write_request,
    preview_safe_write_request,
)
from source_proxy.cartographer.verification_runner import (
    run_verification_command,
)


class CartographerSafeWriteNegativeTests(unittest.TestCase):
    def test_valid_approval_context_is_eligible_without_granting_broad_authority(self) -> None:
        preview = preview_safe_write_request(
            self._valid_payload(),
            requested_actor="cartographer-runtime",
            requested_scope=self._scope(),
            requested_action_class="safe_write",
            requested_files=["docs/approved-safe-write.md"],
            consumption_context=self._context(),
            current_head="abc123",
            now=self._now(),
        )

        self.assertEqual(preview.status, "eligible")
        self.assertTrue(preview.eligible)
        self.assertFalse(preview.blocked)
        self.assertEqual(preview.reasons, ())
        self.assertFalse(preview.authority_granted)
        self.assertFalse(preview.write_authority_granted)
        self.assertFalse(preview.command_authority_granted)
        self.assertFalse(preview.workflow_authority_granted)
        self.assertFalse(preview.queue_authority_granted)
        self.assertFalse(preview.git_authority_granted)
        self.assertTrue(preview.safe_write_available)
        self.assertTrue(preview.preview_only)

    def test_approved_exact_docs_path_can_be_written_in_workspace_only(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            result = execute_safe_write_request(
                self._valid_payload(),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file="docs/approved-safe-write.md",
                content="approved safe write\n",
                consumption_context=self._context(),
                workspace_root=Path(workspace),
                current_head="abc123",
                now=self._now(),
            )

            written_file = Path(workspace) / "docs/approved-safe-write.md"
            self.assertEqual(result.status, "written")
            self.assertTrue(result.written)
            self.assertFalse(result.blocked)
            self.assertEqual(result.reasons, ())
            self.assertEqual(result.bytes_written, len("approved safe write\n"))
            self.assertEqual(written_file.read_text(encoding="utf-8"), "approved safe write\n")
            self.assertFalse(result.authority_granted)
            self.assertFalse(result.write_authority_granted)
            self.assertFalse(result.command_authority_granted)
            self.assertFalse(result.workflow_authority_granted)
            self.assertFalse(result.queue_authority_granted)
            self.assertFalse(result.git_authority_granted)

    def test_live_evidence_and_receipt_prefixes_can_be_written_when_exactly_approved(self) -> None:
        cases = [
            "docs/cartographer-live-evidence/plan-3-phase-2.md",
            "docs/cartographer-live-receipts/plan-3-phase-2.md",
        ]

        for target_file in cases:
            with self.subTest(target_file=target_file), tempfile.TemporaryDirectory() as workspace:
                context = {
                    **self._context(),
                    "exact_allowed_files": [target_file],
                    "exact_forbidden_files": [],
                }
                result = execute_safe_write_request(
                    self._valid_payload(),
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    target_file=target_file,
                    content=f"# {target_file}\n",
                    consumption_context=context,
                    workspace_root=Path(workspace),
                    current_head="abc123",
                    now=self._now(),
                )

                self.assertTrue(result.written)
                self.assertFalse(result.blocked)
                self.assertTrue((Path(workspace) / target_file).exists())

    def test_live_evidence_and_receipt_prefixes_still_require_exact_file_approval(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            target_file = "docs/cartographer-live-evidence/not-exactly-approved.md"
            result = execute_safe_write_request(
                self._valid_payload(),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file=target_file,
                content="should not write\n",
                consumption_context=self._context(),
                workspace_root=Path(workspace),
                current_head="abc123",
                now=self._now(),
            )

            self.assertTrue(result.blocked)
            self.assertFalse(result.written)
            self.assertIn("approval:requested_files_exceed_exact_allowed_files", result.reasons)
            self.assertIn("unapproved_docs_blocked", result.reasons)
            self.assertFalse((Path(workspace) / target_file).exists())

    def test_non_docs_targets_are_blocked_even_when_exactly_approved(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            target_file = "notes/approved-but-not-docs.md"
            context = {
                **self._context(),
                "exact_allowed_files": [target_file],
                "exact_forbidden_files": [],
            }
            result = execute_safe_write_request(
                self._valid_payload(),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file=target_file,
                content="should not write\n",
                consumption_context=context,
                workspace_root=Path(workspace),
                current_head="abc123",
                now=self._now(),
            )

            self.assertTrue(result.blocked)
            self.assertFalse(result.written)
            self.assertIn("unsafe_write_class_blocked", result.reasons)
            self.assertFalse((Path(workspace) / target_file).exists())

    def test_traversal_target_is_blocked_before_workspace_write(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            target_file = "docs/../outside.md"
            context = {
                **self._context(),
                "exact_allowed_files": [target_file],
                "exact_forbidden_files": [],
            }
            result = execute_safe_write_request(
                self._valid_payload(),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file=target_file,
                content="should not write\n",
                consumption_context=context,
                workspace_root=Path(workspace),
                current_head="abc123",
                now=self._now(),
            )

            self.assertTrue(result.blocked)
            self.assertFalse(result.written)
            self.assertIn("path_traversal_blocked", result.reasons)
            self.assertFalse((Path(workspace) / "outside.md").exists())

    def test_invalid_or_missing_approval_token_fails_closed(self) -> None:
        cases = [
            (None, "approval:token_validation:malformed_payload"),
            (
                {**self._valid_payload(), "approved_by": "cartographer-runtime"},
                "approval:token_validation:self_approval_rejected",
            ),
            (
                {
                    **self._valid_payload(),
                    "expires_at": "2026-05-22T11:59:59Z",
                },
                "approval:token_validation:token_expired",
            ),
        ]

        for payload, reason in cases:
            with self.subTest(reason=reason):
                preview = preview_safe_write_request(
                    payload,
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_class="safe_write",
                    requested_files=["docs/approved-safe-write.md"],
                    consumption_context=self._context(),
                    current_head="abc123",
                    now=self._now(),
                )

                self.assertTrue(preview.blocked)
                self.assertIn(reason, preview.reasons)
                self.assertFalse(preview.write_authority_granted)

    def test_blocked_safe_write_does_not_create_or_modify_files(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            approved_file = Path(workspace) / "docs/approved-safe-write.md"
            approved_file.parent.mkdir(parents=True, exist_ok=True)
            approved_file.write_text("original\n", encoding="utf-8")

            result = execute_safe_write_request(
                None,
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file="docs/approved-safe-write.md",
                content="replacement\n",
                consumption_context=self._context(),
                workspace_root=Path(workspace),
                current_head="abc123",
                now=self._now(),
            )

            self.assertTrue(result.blocked)
            self.assertFalse(result.written)
            self.assertIn("approval:token_validation:malformed_payload", result.reasons)
            self.assertEqual(approved_file.read_text(encoding="utf-8"), "original\n")

    def test_requested_files_must_match_exact_allowed_files(self) -> None:
        preview = preview_safe_write_request(
            self._valid_payload(),
            requested_actor="cartographer-runtime",
            requested_scope=self._scope(),
            requested_action_class="safe_write",
            requested_files=[
                "docs/approved-safe-write.md",
                "docs/not-approved-safe-write.md",
            ],
            consumption_context=self._context(),
            current_head="abc123",
            now=self._now(),
        )

        self.assertTrue(preview.blocked)
        self.assertIn("approval:requested_files_exceed_exact_allowed_files", preview.reasons)
        self.assertIn("unapproved_docs_blocked", preview.reasons)
        self.assertFalse(preview.write_authority_granted)

    def test_forbidden_paths_fail_closed(self) -> None:
        cases = [
            ("source_proxy/cartographer/service.py", "protected_path_blocked"),
            ("src/app/map/page.tsx", "protected_path_blocked"),
            ("package.json", "protected_path_blocked"),
            ("next.config.ts", "protected_path_blocked"),
            (".env.local", "protected_path_blocked"),
            ("/coding/operator.md", "protected_path_blocked"),
            ("Scout/recommendation.md", "protected_path_blocked"),
            ("generated/receipt.md", "protected_path_blocked"),
            (".git/config", "protected_path_blocked"),
            ("docs/*.md", "broad_glob_blocked"),
            ("../outside.md", "path_traversal_blocked"),
            ("docs/not-approved.md", "unapproved_docs_blocked"),
            ("docs/forbidden-safe-write.md", "forbidden_file_blocked"),
        ]

        for requested_file, reason in cases:
            with self.subTest(requested_file=requested_file):
                preview = preview_safe_write_request(
                    self._valid_payload(),
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_class="safe_write",
                    requested_files=[requested_file],
                    consumption_context=self._context(),
                    current_head="abc123",
                    now=self._now(),
                )

                self.assertTrue(preview.blocked)
                self.assertIn(reason, preview.reasons)
                self.assertFalse(preview.write_authority_granted)

    def test_head_dirty_tree_action_trust_and_kill_switch_fail_closed(self) -> None:
        cases = [
            ({"current_head": "different"}, "approval:stale_head"),
            ({"dirty_tree_matches_expected": False}, "dirty_tree_mismatch"),
            ({"requested_action_class": "docs_receipt_preview"}, "wrong_action_class"),
            (
                {
                    "consumption_context": {
                        **self._context(),
                        "requested_trust_tier": "tier-2",
                    },
                },
                "approval:trust_tier_mismatch",
            ),
            (
                {
                    "consumption_context": {
                        **self._context(),
                        "trust_tier": "tier-2",
                        "requested_trust_tier": "tier-2",
                    },
                },
                "wrong_trust_tier",
            ),
            ({"kill_switch_active": True}, "approval:kill_switch_active"),
        ]

        for overrides, reason in cases:
            with self.subTest(reason=reason):
                preview = preview_safe_write_request(
                    self._valid_payload(),
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_class=overrides.get("requested_action_class", "safe_write"),
                    requested_files=["docs/approved-safe-write.md"],
                    consumption_context=overrides.get("consumption_context", self._context()),
                    current_head=overrides.get("current_head", "abc123"),
                    dirty_tree_matches_expected=overrides.get(
                        "dirty_tree_matches_expected",
                        True,
                    ),
                    kill_switch_active=overrides.get("kill_switch_active", False),
                    now=self._now(),
                )

                self.assertTrue(preview.blocked)
                self.assertIn(reason, preview.reasons)
                self.assertFalse(preview.authority_granted)

    def test_forbidden_execution_and_git_actions_are_unavailable(self) -> None:
        forbidden_actions = (
            "command_execution",
            "queue_execution",
            "workflow_execution",
            "commit",
            "push",
            "branch",
            "worktree",
            "stash",
            "clean",
            "reset",
            "checkout",
        )

        for action_class in forbidden_actions:
            with self.subTest(action_class=action_class):
                preview = preview_safe_write_request(
                    self._valid_payload(),
                    requested_actor="cartographer-runtime",
                    requested_scope=self._scope(),
                    requested_action_class=action_class,
                    requested_files=["docs/approved-safe-write.md"],
                    consumption_context={**self._context(), "action_class": action_class},
                    current_head="abc123",
                    now=self._now(),
                )

                self.assertTrue(preview.blocked)
                self.assertIn("approval:forbidden_action_class", preview.reasons)
                self.assertIn("approval:approved_action_class_forbidden", preview.reasons)
                self.assertFalse(preview.command_authority_granted)
                self.assertFalse(preview.workflow_authority_granted)
                self.assertFalse(preview.queue_authority_granted)
                self.assertFalse(preview.git_authority_granted)

    def test_status_is_inert_and_grants_no_authority(self) -> None:
        status = build_safe_write_status()

        self.assertEqual(status["status"], "safe-write-service-available")
        self.assertTrue(status["safe_write_available"])
        self.assertTrue(status["preview_available"])
        self.assertFalse(status["authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["workflow_authority_granted"])
        self.assertFalse(status["queue_authority_granted"])
        self.assertFalse(status["git_authority_granted"])

    def test_verification_result_can_be_attached_to_safe_write_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            receipt_file = "docs/cartographer-live-receipts/verification-attached.md"
            context = {
                **self._context(),
                "exact_allowed_files": [receipt_file],
                "exact_forbidden_files": [],
            }
            verification_result = run_verification_command(
                ["git", "diff", "--check"],
                workspace_root=workspace_root,
                timeout_seconds=5,
            )
            planned_safe_write = safe_write.SafeWriteResult(
                status="planned",
                written=False,
                blocked=False,
                reasons=(),
                target_file=receipt_file,
                bytes_written=0,
                before_exists=False,
            )
            receipt_content = build_safe_write_verification_receipt_content(
                title="Verification Attached Safe Write Receipt",
                safe_write_result=planned_safe_write,
                verification_result=verification_result,
                generated_at=self._now(),
            )

            result = execute_safe_write_request(
                self._valid_payload(),
                requested_actor="cartographer-runtime",
                requested_scope=self._scope(),
                target_file=receipt_file,
                content=receipt_content,
                consumption_context=context,
                workspace_root=workspace_root,
                current_head="abc123",
                now=self._now(),
            )

            written = (workspace_root / receipt_file).read_text(encoding="utf-8")
            self.assertTrue(result.written)
            self.assertFalse(result.blocked)
            self.assertIn("Plan 4 Phase 4: Verification Receipt Attached To Safe Write", written)
            self.assertIn("Generated at: 2026-05-22T12:00:00Z", written)
            self.assertIn("- command: `git diff --check`", written)
            self.assertIn("- command id: `git_diff_check`", written)
            self.assertIn("- status: `failed`", written)
            self.assertIn("- exit code: `129`", written)
            self.assertIn("Not a git repository", written)
            self.assertIn("command authority granted: `false`", written)
            self.assertIn("workflow authority granted: `false`", written)
            self.assertIn("queue authority granted: `false`", written)
            self.assertIn("git mutation authority granted: `false`", written)
            self.assertIn("commit, push, branch, worktree, stash, clean, reset, and checkout", written)

    def test_blocked_verification_result_can_be_attached_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            verification_result = run_verification_command(
                ["git", "reset", "--hard"],
                workspace_root=Path(workspace),
                timeout_seconds=5,
            )
            receipt_content = build_safe_write_verification_receipt_content(
                title="Blocked Verification Receipt",
                safe_write_result={
                    "status": "blocked",
                    "written": False,
                    "blocked": True,
                    "target_file": "docs/cartographer-live-receipts/blocked.md",
                    "bytes_written": 0,
                },
                verification_result=verification_result,
                generated_at=self._now(),
            )

        self.assertIn("- command: `git reset --hard`", receipt_content)
        self.assertIn("- status: `blocked`", receipt_content)
        self.assertIn("- executed: `False`", receipt_content)
        self.assertIn("- blocked: `True`", receipt_content)
        self.assertIn("destructive_git_command_blocked", receipt_content)
        self.assertIn("git mutation authority granted: `false`", receipt_content)

    def test_safe_write_surface_has_no_mutation_execution_or_git_hooks(self) -> None:
        public_functions = {
            name
            for name, value in vars(safe_write).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }

        self.assertEqual(
            public_functions,
            {
                "build_safe_write_status",
                "build_safe_write_verification_receipt_content",
                "execute_safe_write_request",
                "preview_safe_write_request",
            },
        )

        public_classes = {
            name
            for name, value in vars(safe_write).items()
            if inspect.isclass(value) and value.__module__ == safe_write.__name__
        }
        self.assertEqual(public_classes, {"SafeWritePreview", "SafeWriteResult"})

        source = inspect.getsource(safe_write)
        forbidden_fragments = (
            "subprocess",
            "os.system",
            "requests",
            "urllib",
            "socket",
            "source_proxy.api",
            "source_proxy.codex",
            "source_proxy.testing.runner",
            "source_proxy.verification",
            "git add",
            "git commit",
            "git push",
            "git checkout",
            "git stash",
            "git worktree",
            "git reset",
            "git clean",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 22, 12, 0, 0, tzinfo=UTC)

    @staticmethod
    def _scope() -> dict[str, str]:
        return {
            "type": "phase",
            "value": "cartographer-daily-driver-plan-3-phase-2",
        }

    def _valid_payload(self) -> dict[str, object]:
        return {
            "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
            "token_id": "approval-token-plan-3-phase-2",
            "issued_at": (self._now() - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
            "expires_at": (self._now() + timedelta(minutes=55)).isoformat().replace("+00:00", "Z"),
            "approved_by": "Britton",
            "approved_for_actor": "cartographer-runtime",
            "scope": self._scope(),
            "reason": "Approved Plan 3 Phase 2 exact safe write service boundary.",
        }

    @staticmethod
    def _context() -> dict[str, object]:
        return {
            "action_class": "safe_write",
            "trust_tier": "tier-1",
            "requested_trust_tier": "tier-1",
            "exact_allowed_files": ["docs/approved-safe-write.md"],
            "exact_forbidden_files": ["docs/forbidden-safe-write.md"],
            "expected_head": "abc123",
            "rollback": "Review exact target file and restore the previous content manually.",
            "verification": "Run focused safe-write service tests.",
        }
