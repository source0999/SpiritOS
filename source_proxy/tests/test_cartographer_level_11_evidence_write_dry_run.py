from __future__ import annotations

import inspect
import unittest

from source_proxy.cartographer import level_11_evidence_write_dry_run
from source_proxy.cartographer.level_11_approval_token import (
    CartographerLevel11ApprovalTokenValidation,
)
from source_proxy.cartographer.level_11_event_ledger import (
    CartographerLevel11LedgerValidation,
)
from source_proxy.cartographer.level_11_evidence_write_dry_run import (
    build_level_11_evidence_write_dry_run_packet,
)


class CartographerLevel11EvidenceWriteDryRunTests(unittest.TestCase):
    def test_evidence_write_dry_run_never_grants_write_authority(self) -> None:
        packet = build_level_11_evidence_write_dry_run_packet(
            target_evidence_file="docs/evidence/level-11.md",
            evidence_purpose="record focused dry-run proof",
            allowed_files=("docs/evidence/level-11.md",),
            forbidden_files=("src/**",),
            approval_validation=self._approval(ok=True),
            ledger_validation=self._ledger(ok=True),
        )

        self.assertEqual(packet.level, "11.5")
        self.assertEqual(packet.status, "evidence-write-dry-run-only")
        self.assertEqual(packet.mode, "dry_run")
        self.assertFalse(packet.blocked)
        self.assertFalse(packet.would_write_file)
        self.assertFalse(packet.write_authority_granted)
        self.assertFalse(packet.local_execution_authority_granted)

    def test_evidence_write_dry_run_fails_closed_for_scope_and_control_gaps(self) -> None:
        packet = build_level_11_evidence_write_dry_run_packet(
            target_evidence_file="source_proxy/api/cartographer.py",
            evidence_purpose="",
            allowed_files=("docs/evidence/level-11.md",),
            forbidden_files=("source_proxy/api/cartographer.py",),
            approval_validation=self._approval(ok=False, reasons=("token_revoked",)),
            ledger_validation=self._ledger(ok=False, reasons=("sequence_gap_or_reorder",)),
        )

        self.assertTrue(packet.blocked)
        self.assertIn("missing_evidence_purpose", packet.blocked_reasons)
        self.assertIn("target_evidence_file_outside_docs", packet.blocked_reasons)
        self.assertIn("target_evidence_file_outside_allowed_files", packet.blocked_reasons)
        self.assertIn("target_evidence_file_intersects_forbidden_files", packet.blocked_reasons)
        self.assertIn("approval:token_revoked", packet.blocked_reasons)
        self.assertIn("ledger:sequence_gap_or_reorder", packet.blocked_reasons)
        self.assertFalse(packet.would_write_file)
        self.assertFalse(packet.write_authority_granted)

    def test_module_exposes_no_write_execution_or_git_surface(self) -> None:
        public_functions = {
            name
            for name, value in vars(level_11_evidence_write_dry_run).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }

        self.assertEqual(public_functions, {"build_level_11_evidence_write_dry_run_packet"})

        source = inspect.getsource(level_11_evidence_write_dry_run)
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

    @staticmethod
    def _approval(
        *,
        ok: bool,
        reasons: tuple[str, ...] = (),
    ) -> CartographerLevel11ApprovalTokenValidation:
        return CartographerLevel11ApprovalTokenValidation(
            valid_for_dry_run=ok,
            action_authority_granted=False,
            write_authority_granted=False,
            local_execution_authority_granted=False,
            blocked_reasons=reasons,
            next_required_human_step="operator_review_required",
        )

    @staticmethod
    def _ledger(
        *,
        ok: bool,
        reasons: tuple[str, ...] = (),
    ) -> CartographerLevel11LedgerValidation:
        return CartographerLevel11LedgerValidation(
            valid_for_dry_run=ok,
            append_only_runtime_enabled=False,
            action_authority_granted=False,
            blocked_reasons=reasons,
            event_count=3,
        )


if __name__ == "__main__":
    unittest.main()
