from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import inspect
import unittest

from source_proxy.cartographer import level_11_approval_token
from source_proxy.cartographer.level_11_approval_token import (
    CartographerLevel11ApprovalToken,
    build_level_11_approval_token_schema_preview,
    validate_level_11_approval_token_dry_run,
)


class CartographerLevel11ApprovalTokenTests(unittest.TestCase):
    def test_schema_preview_does_not_grant_authority(self) -> None:
        preview = build_level_11_approval_token_schema_preview()

        self.assertEqual(preview["level"], "11.2")
        self.assertEqual(preview["status"], "schema-validation-dry-run-only")
        self.assertFalse(preview["authority_granted"])
        self.assertFalse(preview["write_authority_granted"])
        self.assertFalse(preview["local_execution_authority_granted"])
        self.assertFalse(preview["token_issuance_enabled"])
        self.assertFalse(preview["token_consumption_enabled"])
        self.assertIn("operator_id", preview["required_fields"])

    def test_valid_preview_shape_can_only_validate_for_dry_run(self) -> None:
        result = validate_level_11_approval_token_dry_run(
            self._valid_token(),
            requested_run_id="run-11-2",
            requested_action_type="approved_receipt_write",
            requested_target_files=("docs/receipts/level-11.md",),
            operator_id="cartographer-runtime",
            now=datetime(2026, 5, 21, tzinfo=UTC),
        )

        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.action_authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.local_execution_authority_granted)
        self.assertEqual(result.blocked_reasons, ())
        self.assertEqual(result.next_required_human_step, "operator_review_required")

    def test_validation_fails_closed_for_missing_or_mismatched_controls(self) -> None:
        valid = self._valid_token()
        cases = [
            (replace(valid, token_id=""), "missing_token_id"),
            (replace(valid, run_id="other"), "run_id_mismatch"),
            (replace(valid, action_type="commit"), "unsupported_action_type"),
            (replace(valid, target_files=("docs/other.md",)), "target_files_mismatch"),
            (replace(valid, allowed_files=()), "missing_allowed_files"),
            (
                replace(valid, allowed_files=("docs/other.md",)),
                "target_files_outside_allowed_files",
            ),
            (
                replace(valid, forbidden_files=("docs/receipts/level-11.md",)),
                "target_files_intersect_forbidden_files",
            ),
            (
                replace(
                    valid,
                    target_files=("src/app/coding/page.tsx",),
                    allowed_files=("src/app/coding/page.tsx",),
                ),
                "protected_path_in_scope",
            ),
            (replace(valid, expires_at="2026-05-20T00:00:00Z"), "token_expired_or_malformed"),
            (replace(valid, expires_at="not-a-date"), "token_expired_or_malformed"),
            (replace(valid, max_attempts=0), "invalid_max_attempts"),
            (replace(valid, rollback_command=""), "missing_rollback_metadata"),
            (replace(valid, verification_command=""), "missing_verification_metadata"),
            (
                replace(valid, operator_id="cartographer-runtime"),
                "self_approval_or_missing_external_operator",
            ),
            (replace(valid, used_at="2026-05-21T12:00:00Z"), "token_already_used"),
            (replace(valid, revoked=True), "token_revoked"),
        ]

        for token, reason in cases:
            with self.subTest(reason=reason):
                result = validate_level_11_approval_token_dry_run(
                    token,
                    requested_run_id="run-11-2",
                    requested_action_type="approved_receipt_write",
                    requested_target_files=("docs/receipts/level-11.md",),
                    operator_id="cartographer-runtime",
                    now=datetime(2026, 5, 21, tzinfo=UTC),
                )
                self.assertFalse(result.valid_for_dry_run)
                self.assertIn(reason, result.blocked_reasons)
                self.assertFalse(result.action_authority_granted)

    def test_module_exposes_no_write_execution_or_git_function_surface(self) -> None:
        public_functions = {
            name
            for name, value in vars(level_11_approval_token).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }

        self.assertEqual(
            public_functions,
            {
                "build_level_11_approval_token_schema_preview",
                "validate_level_11_approval_token_dry_run",
            },
        )

        source = inspect.getsource(level_11_approval_token)
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
    def _valid_token() -> CartographerLevel11ApprovalToken:
        return CartographerLevel11ApprovalToken(
            token_id="token-11-2",
            run_id="run-11-2",
            action_type="approved_receipt_write",
            target_files=("docs/receipts/level-11.md",),
            allowed_files=("docs/receipts/level-11.md",),
            forbidden_files=("src/**", "source_proxy/api/cartographer.py"),
            expires_at="2026-05-22T00:00:00Z",
            max_attempts=1,
            rollback_command="manual rollback note required before future writes",
            verification_command="manual verification command required before future writes",
            operator_id="external-human-operator",
            created_at="2026-05-21T00:00:00Z",
        )


if __name__ == "__main__":
    unittest.main()
