from __future__ import annotations

from datetime import UTC, datetime
import inspect
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.cartographer import docs_runbook_updates
from source_proxy.cartographer.docs_runbook_updates import (
    FORBIDDEN_DOCS_RUNBOOK_AUTHORITIES,
    SAFE_DOCS_RUNBOOK_REQUIRED_FIELDS,
    SAFE_DOCS_RUNBOOK_TARGET_PREFIXES,
    SAFE_DOCS_RUNBOOK_UPDATE_CLASSES,
    SAFE_DOCS_RUNBOOK_UPDATES_PHASE,
    SafeDocsRunbookUpdateProposal,
    build_safe_docs_runbook_update_status,
    validate_safe_docs_runbook_update_proposal,
)


class CartographerDocsRunbookUpdateTests(unittest.TestCase):
    def test_status_is_proposal_only_without_write_or_execution_authority(self) -> None:
        status = build_safe_docs_runbook_update_status()

        self.assertEqual(status["phase"], SAFE_DOCS_RUNBOOK_UPDATES_PHASE)
        self.assertEqual(status["status"], "proposal-only")
        self.assertEqual(status["safe_update_classes"], SAFE_DOCS_RUNBOOK_UPDATE_CLASSES)
        self.assertEqual(status["safe_target_prefixes"], SAFE_DOCS_RUNBOOK_TARGET_PREFIXES)
        self.assertEqual(status["required_fields"], SAFE_DOCS_RUNBOOK_REQUIRED_FIELDS)
        self.assertEqual(status["forbidden_authorities"], FORBIDDEN_DOCS_RUNBOOK_AUTHORITIES)
        self.assertTrue(status["proposal_only"])
        self.assertFalse(status["docs_write_enabled"])
        self.assertFalse(status["runbook_write_enabled"])
        self.assertFalse(status["source_write_enabled"])
        self.assertFalse(status["test_write_enabled"])
        self.assertFalse(status["command_execution_enabled"])
        self.assertFalse(status["queue_execution_enabled"])
        self.assertFalse(status["commit_enabled"])
        self.assertFalse(status["push_enabled"])
        self.assertFalse(status["durable_storage_written"])
        self.assertFalse(status["api_mutation_available"])
        self.assertTrue(status["exact_scope_required"])
        self.assertTrue(status["approval_bound"])
        self.assertTrue(status["receipt_backed"])

    def test_valid_docs_runbook_update_proposal_accepts_without_writes(self) -> None:
        result = validate_safe_docs_runbook_update_proposal(
            self._proposal(),
            expected_trust_tier="tier-1",
            expected_approval_token_id="approval-token-plan-11-phase-11-1-docs",
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.proposal_id, "docs-runbook-plan-11-1-1")
        self.assertEqual(result.update_class, "operator_runbook_clarification")
        self.assertEqual(result.target_paths, ("docs/cartographer-operator-runbook.md",))
        self.assertEqual(result.receipt_path, "docs/cartographer-live-receipts/docs-runbook-plan-11-1-1.md")
        self.assertEqual(result.trust_tier, "tier-1")
        self.assertEqual(result.approval_token_id, "approval-token-plan-11-phase-11-1-docs")
        self.assertTrue(result.proposal_only)
        self.assertFalse(result.docs_write_enabled)
        self.assertFalse(result.runbook_write_enabled)
        self.assertFalse(result.command_execution_enabled)

    def test_required_fields_fail_closed(self) -> None:
        for field in SAFE_DOCS_RUNBOOK_REQUIRED_FIELDS:
            payload = self._proposal().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_safe_docs_runbook_update_proposal(
                    payload,
                    expected_trust_tier="tier-1",
                    expected_approval_token_id="approval-token-plan-11-phase-11-1-docs",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_scope_trust_token_status_and_receipt_rules_fail_closed(self) -> None:
        cases = [
            ({"update_class": "source_refactor"}, "unknown_update_class"),
            ({"target_paths": ()}, "missing_target_paths"),
            ({"target_paths": ("src/app/page.tsx",)}, "target_must_be_docs_or_runbook_markdown"),
            ({"target_paths": ("docs/*.md",)}, "broad_target_path"),
            ({"target_paths": ("docs/file.md", "docs/file.md")}, "duplicate_target_path"),
            ({"receipt_path": "source_proxy/receipt.md"}, "receipt_path_must_be_docs"),
            ({"receipt_path": "docs/receipt.json"}, "receipt_path_must_be_markdown"),
            ({"trust_tier": "tier-3"}, "wrong_trust_tier"),
            ({"approval_token_id": "other-token"}, "wrong_approval_token"),
            ({"status": "approved"}, "status_must_remain_proposed"),
            ({"verification_plan": ()}, "missing_verification_plan"),
            ({"exact_change_summary": "Apply now to update the runbook."}, "change_summary_must_not_request_application"),
            ({"rationale": "Also update production code."}, "rationale_must_not_expand_beyond_docs_runbooks"),
            ({"rollback_guidance": "Force push a rollback."}, "rollback_guidance_must_not_recommend_force"),
            ({"created_at": "2026-05-23T12:10:00Z"}, "created_at_in_future"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_safe_docs_runbook_update_proposal(
                    {**self._proposal().to_dict(), **override},
                    expected_trust_tier="tier-1",
                    expected_approval_token_id="approval-token-plan-11-phase-11-1-docs",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.docs_write_enabled)
                self.assertFalse(result.runbook_write_enabled)

    def test_module_exposes_no_write_execution_git_api_mutation_or_storage_surface(self) -> None:
        source = inspect.getsource(docs_runbook_updates)
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

    def test_docs_runbook_api_preview_is_proposal_only(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/expansion/docs-runbook/proposals")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["api_preview_only"])
        self.assertEqual(payload["docs_runbook_status"]["phase"], SAFE_DOCS_RUNBOOK_UPDATES_PHASE)
        self.assertEqual(payload["validation"]["status"], "accepted")
        self.assertFalse(payload["docs_write_enabled"])
        self.assertFalse(payload["runbook_write_enabled"])
        self.assertFalse(payload["source_write_enabled"])
        self.assertFalse(payload["test_write_enabled"])
        self.assertFalse(payload["command_execution_enabled"])
        self.assertFalse(payload["queue_execution_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])

    @staticmethod
    def _proposal() -> SafeDocsRunbookUpdateProposal:
        return SafeDocsRunbookUpdateProposal(
            proposal_id="docs-runbook-plan-11-1-1",
            update_class="operator_runbook_clarification",
            target_paths=("docs/cartographer-operator-runbook.md",),
            receipt_path="docs/cartographer-live-receipts/docs-runbook-plan-11-1-1.md",
            exact_change_summary="Clarify a manual operator runbook step without applying the edit.",
            rationale="Improve operator reviewability inside docs/runbook scope only.",
            rollback_guidance="No write has occurred; discard proposal if not approved.",
            verification_plan=("manual_review_only", "run exact docs/runbook check after separate approval"),
            trust_tier="tier-1",
            approval_token_id="approval-token-plan-11-phase-11-1-docs",
            status="proposed",
            created_at="2026-05-23T12:00:00Z",
        )

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 23, 12, 5, tzinfo=UTC)


def _test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(cartographer_router)
    return test_app


if __name__ == "__main__":
    unittest.main()
