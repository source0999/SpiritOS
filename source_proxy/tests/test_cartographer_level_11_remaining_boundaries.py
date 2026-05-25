from __future__ import annotations

import inspect
import unittest

from source_proxy.cartographer import level_11_remaining_boundaries
from source_proxy.cartographer.level_11_remaining_boundaries import (
    build_level_11_closeout_level_12_access_check,
    build_level_11_docs_only_apply_dry_run_packet,
    build_level_11_local_verification_execution_dry_run_packet,
    build_level_11_rollback_closeout_dry_run_packet,
)


class CartographerLevel11RemainingBoundariesTests(unittest.TestCase):
    def test_docs_only_apply_dry_run_never_writes(self) -> None:
        packet = build_level_11_docs_only_apply_dry_run_packet(
            target_docs_files=("docs/demo.md",),
            allowed_files=("docs/demo.md",),
            forbidden_files=("src/**",),
        )

        self.assertEqual(packet.level, "11.6")
        self.assertFalse(packet.blocked)
        self.assertFalse(packet.would_write_files)
        self.assertFalse(packet.authority_granted)

    def test_docs_only_apply_blocks_non_docs_targets(self) -> None:
        packet = build_level_11_docs_only_apply_dry_run_packet(
            target_docs_files=("src/app/coding/page.tsx",),
            allowed_files=("src/app/coding/page.tsx",),
            forbidden_files=("src/app/coding/page.tsx",),
        )

        self.assertTrue(packet.blocked)
        self.assertIn("non_docs_target_in_scope", packet.blocked_reasons)
        self.assertIn("protected_path_in_scope", packet.blocked_reasons)
        self.assertFalse(packet.would_write_files)

    def test_local_verification_dry_run_never_executes_commands(self) -> None:
        packet = build_level_11_local_verification_execution_dry_run_packet(
            command=("git", "diff", "--check"),
            allowed_files=("docs/demo.md",),
            forbidden_files=(),
        )

        self.assertEqual(packet.level, "11.7")
        self.assertFalse(packet.blocked)
        self.assertFalse(packet.would_execute_commands)
        self.assertFalse(packet.authority_granted)

    def test_local_verification_blocks_mutating_commands(self) -> None:
        packet = build_level_11_local_verification_execution_dry_run_packet(
            command=("git", "commit"),
            allowed_files=("docs/demo.md",),
            forbidden_files=("src/**",),
        )

        self.assertTrue(packet.blocked)
        self.assertIn("mutating_or_git_authority_command_forbidden", packet.blocked_reasons)
        self.assertIn("forbidden_files_declared", packet.blocked_reasons)
        self.assertFalse(packet.would_execute_commands)

    def test_rollback_closeout_dry_run_requires_rollback_and_verification(self) -> None:
        packet = build_level_11_rollback_closeout_dry_run_packet(
            closeout_receipt_file="source_proxy/api/cartographer.py",
            rollback_reference="",
            verification_reference="",
            allowed_files=("docs/receipts/closeout.md",),
            forbidden_files=("source_proxy/api/cartographer.py",),
        )

        self.assertEqual(packet.level, "11.8")
        self.assertTrue(packet.blocked)
        self.assertIn("protected_path_in_scope", packet.blocked_reasons)
        self.assertIn("missing_rollback_reference", packet.blocked_reasons)
        self.assertIn("missing_verification_reference", packet.blocked_reasons)
        self.assertFalse(packet.would_write_files)

    def test_level_11_closeout_keeps_level_12_human_gated(self) -> None:
        payload = build_level_11_closeout_level_12_access_check()

        self.assertEqual(payload["level"], "11.9")
        self.assertEqual(payload["level_12_access"], "requires_explicit_human_verification")
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["write_authority_granted"])
        self.assertFalse(payload["local_execution_authority_granted"])
        self.assertFalse(payload["workflow_execution_authority_granted"])
        self.assertFalse(payload["worker_orchestration_authority_granted"])
        self.assertFalse(payload["safe_task_queue_execution_authority_granted"])
        self.assertFalse(payload["autonomy_granted"])

    def test_module_exposes_no_write_execution_or_git_surface(self) -> None:
        public_functions = {
            name
            for name, value in vars(level_11_remaining_boundaries).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }

        self.assertEqual(
            public_functions,
            {
                "build_level_11_docs_only_apply_dry_run_packet",
                "build_level_11_local_verification_execution_dry_run_packet",
                "build_level_11_rollback_closeout_dry_run_packet",
                "build_level_11_closeout_level_12_access_check",
            },
        )

        source = inspect.getsource(level_11_remaining_boundaries)
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
            "git commit",
            "git push",
            "git merge",
            "git checkout",
            "git stash",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)


if __name__ == "__main__":
    unittest.main()
