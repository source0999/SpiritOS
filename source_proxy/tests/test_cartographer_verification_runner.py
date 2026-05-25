from __future__ import annotations

import inspect
from pathlib import Path
import subprocess
import tempfile
import unittest

from source_proxy.cartographer import verification_runner
from source_proxy.cartographer.verification_runner import (
    build_verification_command_allowlist,
    build_verification_result_receipt_summary,
    build_verification_runner_status,
    preview_verification_command,
    run_verification_command,
)


class CartographerVerificationRunnerAllowlistTests(unittest.TestCase):
    def test_status_is_allowlist_only_and_grants_no_execution_authority(self) -> None:
        status = build_verification_runner_status()

        self.assertEqual(status["status"], "verification-boundary-available")
        self.assertEqual(status["plan"], "Cartographer Integrated Control Master Plan 6/10")
        self.assertEqual(status["phase"], "Plan 6 Phase 6.1: Verification And Command Runner")
        self.assertTrue(status["argv_only"])
        self.assertFalse(status["shell_allowed"])
        self.assertTrue(status["execution_available"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["workflow_authority_granted"])
        self.assertFalse(status["queue_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])
        self.assertTrue(status["file_checks_available"])

    def test_allowlist_represents_commands_as_exact_argv_arrays(self) -> None:
        allowlist = build_verification_command_allowlist(
            approved_test_files=[
                "source_proxy/tests/test_cartographer_safe_write.py",
                "src/app/map/__tests__/map-display-shell.test.ts",
            ],
            approved_file_checks=[
                {
                    "path": "docs/cartographer-integrated-control-master-plan-v0.1.md",
                    "contains": "Plan 5",
                },
            ],
        )

        argv_by_id = {spec.command_id: spec.argv for spec in allowlist}
        self.assertEqual(argv_by_id["git_diff_check"], ("git", "diff", "--check"))
        self.assertEqual(
            argv_by_id["pytest:source_proxy/tests/test_cartographer_safe_write.py"],
            (
                ".venv/bin/python",
                "-m",
                "pytest",
                "source_proxy/tests/test_cartographer_safe_write.py",
            ),
        )
        self.assertEqual(
            argv_by_id["npm_test:src/app/map/__tests__/map-display-shell.test.ts"],
            (
                "npm",
                "test",
                "--",
                "src/app/map/__tests__/map-display-shell.test.ts",
            ),
        )
        self.assertEqual(
            argv_by_id["file_exists:docs/cartographer-integrated-control-master-plan-v0.1.md"],
            ("test", "-f", "docs/cartographer-integrated-control-master-plan-v0.1.md"),
        )
        self.assertEqual(
            argv_by_id["grep_contains:docs/cartographer-integrated-control-master-plan-v0.1.md"],
            (
                "grep",
                "-nF",
                "Plan 5",
                "docs/cartographer-integrated-control-master-plan-v0.1.md",
            ),
        )
        for spec in allowlist:
            with self.subTest(command_id=spec.command_id):
                self.assertIsInstance(spec.argv, tuple)
                self.assertTrue(spec.exact_match_required)
                self.assertFalse(spec.shell_allowed)
                self.assertFalse(spec.execution_available)
                self.assertFalse(spec.command_authority_granted)

    def test_preview_accepts_only_exact_allowlisted_argv(self) -> None:
        preview = preview_verification_command(
            ["git", "diff", "--check"],
            approved_test_files=["source_proxy/tests/test_cartographer_safe_write.py"],
        )

        self.assertTrue(preview.accepted)
        self.assertFalse(preview.blocked)
        self.assertEqual(preview.status, "accepted")
        self.assertEqual(preview.reasons, ())
        self.assertEqual(preview.matched_command_id, "git_diff_check")
        self.assertFalse(preview.execution_available)
        self.assertFalse(preview.command_authority_granted)
        self.assertTrue(preview.preview_only)

    def test_preview_blocks_shell_strings_and_near_misses(self) -> None:
        cases = [
            ("git diff --check", "malformed_argv"),
            (["git", "diff", "--check", "--cached"], "argv_not_exactly_allowed"),
            (["git", "status"], "argv_not_exactly_allowed"),
            (
                ["python", "-m", "pytest", "source_proxy/tests/test_cartographer_safe_write.py"],
                "argv_not_exactly_allowed",
            ),
            (
                [".venv/bin/python", "-m", "pytest", "source_proxy/tests/not-approved.py"],
                "argv_not_exactly_allowed",
            ),
            (["npm", "test"], "argv_not_exactly_allowed"),
            (
                ["npm", "test", "--", "src/app/map/__tests__/not-approved.test.ts"],
                "argv_not_exactly_allowed",
            ),
            (["git", "status", "--short"], "argv_not_exactly_allowed"),
        ]

        for requested_argv, reason in cases:
            with self.subTest(requested_argv=requested_argv):
                preview = preview_verification_command(
                    requested_argv,
                    approved_test_files=["source_proxy/tests/test_cartographer_safe_write.py"],
                )

                self.assertFalse(preview.accepted)
                self.assertTrue(preview.blocked)
                self.assertIn(reason, preview.reasons)
                self.assertFalse(preview.execution_available)
                self.assertFalse(preview.command_authority_granted)

    def test_phase_6_blocks_shell_forms_pipes_and_redirects(self) -> None:
        cases = [
            (["bash", "-c", "git diff --check"], "shell_invocation_blocked"),
            (["sh", "-c", "pytest"], "shell_invocation_blocked"),
            (["git", "diff", "--check", "|", "cat"], "shell_metachar_blocked"),
            (["git", "status", "--short", ">", "out.txt"], "shell_metachar_blocked"),
            (["git", "status", "--short", "&&", "echo", "done"], "shell_metachar_blocked"),
            (["git", "status", "--short;rm", "-rf", "docs"], "shell_metachar_blocked"),
        ]

        for requested_argv, reason in cases:
            with self.subTest(requested_argv=requested_argv):
                preview = preview_verification_command(
                    requested_argv,
                    approved_test_files=["source_proxy/tests/test_cartographer_safe_write.py"],
                )

                self.assertFalse(preview.accepted)
                self.assertTrue(preview.blocked)
                self.assertIn(reason, preview.reasons)
                self.assertFalse(preview.execution_available)
                self.assertFalse(preview.command_authority_granted)

    def test_phase_6_blocks_destructive_git_cleanup_package_install_and_long_running(self) -> None:
        cases = [
            (["rm", "-rf", "docs"], "mutating_command_blocked"),
            (["curl", "https://example.test"], "provider_or_network_command_blocked"),
            (["sleep", "100"], "long_running_command_blocked"),
            (["git", "clean", "-fd"], "destructive_git_command_blocked"),
            (["git", "reset", "--hard"], "destructive_git_command_blocked"),
            (["git", "checkout", "--", "source_proxy/api/cartographer.py"], "destructive_git_command_blocked"),
            (["git", "push"], "destructive_git_command_blocked"),
            (["git", "add", "."], "destructive_git_command_blocked"),
            (["git", "commit", "-m", "test"], "destructive_git_command_blocked"),
            (["git", "branch", "tmp"], "destructive_git_command_blocked"),
            (["git", "worktree", "add", "../tmp"], "destructive_git_command_blocked"),
            (["git", "stash"], "destructive_git_command_blocked"),
            (["npm", "install"], "package_install_blocked"),
            (["npm", "i", "left-pad"], "package_install_blocked"),
            (["pnpm", "install"], "package_install_blocked"),
            (["yarn", "add", "left-pad"], "package_install_blocked"),
            (["pip", "install", "requests"], "package_install_blocked"),
        ]

        for requested_argv, reason in cases:
            with self.subTest(requested_argv=requested_argv):
                preview = preview_verification_command(requested_argv)

                self.assertFalse(preview.accepted)
                self.assertTrue(preview.blocked)
                self.assertIn(reason, preview.reasons)
                self.assertFalse(preview.execution_available)
                self.assertFalse(preview.command_authority_granted)
                self.assertFalse(preview.git_mutation_authority_granted)

    def test_phase_6_keeps_exact_read_only_git_diff_check_accepted(self) -> None:
        preview = preview_verification_command(["git", "diff", "--check"])

        self.assertTrue(preview.accepted)
        self.assertFalse(preview.blocked)
        self.assertEqual(preview.reasons, ())
        self.assertFalse(preview.execution_available)
        self.assertFalse(preview.command_authority_granted)

    def test_preview_accepts_focused_file_existence_and_grep_checks(self) -> None:
        file_checks = [
            {
                "path": "docs/cartographer-integrated-control-master-plan-v0.1.md",
                "contains": "Plan 5",
            },
        ]
        cases = [
            (
                ["test", "-f", "docs/cartographer-integrated-control-master-plan-v0.1.md"],
                "file_exists:docs/cartographer-integrated-control-master-plan-v0.1.md",
            ),
            (
                [
                    "grep",
                    "-nF",
                    "Plan 5",
                    "docs/cartographer-integrated-control-master-plan-v0.1.md",
                ],
                "grep_contains:docs/cartographer-integrated-control-master-plan-v0.1.md",
            ),
        ]

        for argv, command_id in cases:
            with self.subTest(command_id=command_id):
                preview = preview_verification_command(
                    argv,
                    approved_file_checks=file_checks,
                )

                self.assertTrue(preview.accepted)
                self.assertFalse(preview.blocked)
                self.assertEqual(preview.matched_command_id, command_id)

    def test_untrusted_file_checks_are_not_promoted_into_allowlist(self) -> None:
        allowlist = build_verification_command_allowlist(
            approved_file_checks=[
                {"path": "/absolute.md"},
                {"path": "../outside.md"},
                {"path": "docs/*.md"},
                {"path": "docs"},
                {
                    "path": "docs/cartographer-integrated-control-master-plan-v0.1.md",
                    "contains": "Plan 5",
                },
                {
                    "path": "docs/unsafe.md",
                    "contains": "Plan 5; rm -rf docs",
                },
            ],
        )

        argv_by_id = {spec.command_id: spec.argv for spec in allowlist}
        self.assertNotIn("file_exists:/absolute.md", argv_by_id)
        self.assertNotIn("file_exists:../outside.md", argv_by_id)
        self.assertNotIn("file_exists:docs/*.md", argv_by_id)
        self.assertNotIn("file_exists:docs", argv_by_id)
        self.assertIn(
            "file_exists:docs/cartographer-integrated-control-master-plan-v0.1.md",
            argv_by_id,
        )
        self.assertNotIn("grep_contains:docs/unsafe.md", argv_by_id)

    def test_run_executes_exact_allowlisted_command_without_shell(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True)
            result = run_verification_command(
                ["git", "diff", "--check"],
                workspace_root=Path(workspace),
                timeout_seconds=5,
            )

        self.assertTrue(result.executed)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.argv, ("git", "diff", "--check"))
        self.assertFalse(result.shell_allowed)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.workflow_authority_granted)
        self.assertFalse(result.queue_authority_granted)
        self.assertFalse(result.git_mutation_authority_granted)

    def test_run_blocks_forbidden_command_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            result = run_verification_command(
                ["git", "reset", "--hard"],
                workspace_root=Path(workspace),
                timeout_seconds=5,
            )

        self.assertFalse(result.executed)
        self.assertTrue(result.blocked)
        self.assertEqual(result.status, "blocked")
        self.assertIn("destructive_git_command_blocked", result.reasons)
        self.assertFalse(result.command_authority_granted)

    def test_run_returns_bounded_stdout_and_stderr_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / "docs").mkdir()
            (root / "docs/check.md").write_text(f"{'x' * 800}\n", encoding="utf-8")
            result = run_verification_command(
                ["grep", "-nF", "x", "docs/check.md"],
                workspace_root=root,
                approved_file_checks=[{"path": "docs/check.md", "contains": "x"}],
                timeout_seconds=5,
            )

        self.assertTrue(result.executed)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "passed")
        self.assertTrue(result.stdout.endswith("... [truncated]"))
        self.assertLessEqual(len(result.stdout), 416)
        self.assertEqual(result.stderr, "")

    def test_run_blocks_cwd_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            result = run_verification_command(
                ["git", "diff", "--check"],
                workspace_root=Path(workspace),
                cwd_relative="../outside",
                timeout_seconds=5,
            )

        self.assertFalse(result.executed)
        self.assertTrue(result.blocked)
        self.assertIn("cwd_outside_workspace", result.reasons)

    def test_run_captures_nonzero_exit_code_for_allowed_grep_check(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / "docs").mkdir()
            (root / "docs/check.md").write_text("different\n", encoding="utf-8")
            result = run_verification_command(
                ["grep", "-nF", "missing", "docs/check.md"],
                workspace_root=root,
                approved_file_checks=[{"path": "docs/check.md", "contains": "missing"}],
                timeout_seconds=5,
            )

        self.assertTrue(result.executed)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.exit_code, 1)

    def test_receipt_summary_records_command_output_and_blocked_reasons(self) -> None:
        summary = build_verification_result_receipt_summary(
            {
                "status": "blocked",
                "matched_command_id": "git_diff_check",
                "argv": ("git", "diff", "--check"),
                "exit_code": None,
                "stdout": "x" * 500,
                "stderr": "blocked",
                "timeout_seconds": 5,
                "blocked": True,
                "timed_out": False,
                "reasons": ("argv_not_exactly_allowed",),
            },
        )

        self.assertEqual(summary["command_id"], "git_diff_check")
        self.assertEqual(summary["argv"], ("git", "diff", "--check"))
        self.assertIsNone(summary["exit_code"])
        self.assertTrue(summary["stdout_summary"].endswith("... [truncated]"))
        self.assertEqual(summary["stderr_summary"], "blocked")
        self.assertEqual(summary["timeout_seconds"], 5)
        self.assertFalse(summary["passed"])
        self.assertTrue(summary["blocked"])
        self.assertEqual(summary["reasons"], ("argv_not_exactly_allowed",))

    def test_malformed_argv_blocks_closed(self) -> None:
        cases = [
            None,
            [],
            ["git", ""],
            ["git", None],
        ]

        for requested_argv in cases:
            with self.subTest(requested_argv=requested_argv):
                preview = preview_verification_command(requested_argv)

                self.assertFalse(preview.accepted)
                self.assertTrue(preview.blocked)
                self.assertIn("malformed_argv", preview.reasons)

    def test_untrusted_test_file_inputs_are_not_promoted_into_allowlist(self) -> None:
        allowlist = build_verification_command_allowlist(
            approved_test_files=[
                "/absolute/test.py",
                "../outside.py",
                "source_proxy/tests/*.py",
                "source_proxy/tests",
                "source_proxy/tests/test_cartographer_safe_write.py",
            ],
        )

        command_ids = {spec.command_id for spec in allowlist}
        self.assertNotIn("pytest:/absolute/test.py", command_ids)
        self.assertNotIn("pytest:../outside.py", command_ids)
        self.assertNotIn("pytest:source_proxy/tests/*.py", command_ids)
        self.assertNotIn("pytest:source_proxy/tests", command_ids)
        self.assertIn("pytest:source_proxy/tests/test_cartographer_safe_write.py", command_ids)

    def test_allowlist_surface_has_no_execution_or_git_mutation_hooks(self) -> None:
        public_functions = {
            name
            for name, value in vars(verification_runner).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }
        self.assertEqual(
            public_functions,
            {
                "build_verification_command_allowlist",
                "build_verification_result_receipt_summary",
                "build_verification_runner_status",
                "preview_verification_command",
                "run_verification_command",
            },
        )

        public_classes = {
            name
            for name, value in vars(verification_runner).items()
            if inspect.isclass(value) and value.__module__ == verification_runner.__name__
        }
        self.assertEqual(
            public_classes,
            {
                "VerificationCommandPreview",
                "VerificationCommandResult",
                "VerificationCommandSpec",
            },
        )

        source = inspect.getsource(verification_runner)
        forbidden_fragments = (
            "os.system",
            "Popen",
            "shell=True",
            "open(",
            "write_text(",
            "source_proxy.api",
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


if __name__ == "__main__":
    unittest.main()
