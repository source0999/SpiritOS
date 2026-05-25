from __future__ import annotations

from datetime import UTC, datetime
import inspect
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.cartographer import blueprint_refresh_writes
from source_proxy.cartographer.blueprint_refresh_writes import (
    FORBIDDEN_BLUEPRINT_REFRESH_AUTHORITIES,
    SAFE_BLUEPRINT_REFRESH_CLASSES,
    SAFE_BLUEPRINT_REFRESH_REQUIRED_FIELDS,
    SAFE_BLUEPRINT_REFRESH_WRITES_PHASE,
    SAFE_BLUEPRINT_TARGET_PREFIXES,
    SafeBlueprintRefreshWriteProposal,
    build_safe_blueprint_refresh_write_status,
    validate_safe_blueprint_refresh_write_proposal,
)


class CartographerBlueprintRefreshWriteTests(unittest.TestCase):
    def test_status_is_proposal_only_proof_without_write_or_execution_authority(self) -> None:
        status = build_safe_blueprint_refresh_write_status()

        self.assertEqual(status["phase"], SAFE_BLUEPRINT_REFRESH_WRITES_PHASE)
        self.assertEqual(status["status"], "proposal-only-proof")
        self.assertEqual(status["safe_refresh_classes"], SAFE_BLUEPRINT_REFRESH_CLASSES)
        self.assertEqual(status["safe_target_prefixes"], SAFE_BLUEPRINT_TARGET_PREFIXES)
        self.assertEqual(status["required_fields"], SAFE_BLUEPRINT_REFRESH_REQUIRED_FIELDS)
        self.assertEqual(status["forbidden_authorities"], FORBIDDEN_BLUEPRINT_REFRESH_AUTHORITIES)
        self.assertTrue(status["proposal_only_proof_complete"])
        self.assertFalse(status["blueprint_write_enabled"])
        self.assertFalse(status["docs_write_enabled"])
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

    def test_valid_blueprint_refresh_write_proposal_accepts_without_writes(self) -> None:
        result = validate_safe_blueprint_refresh_write_proposal(
            self._proposal(),
            expected_trust_tier="tier-1",
            expected_approval_token_id="approval-token-plan-11-phase-11-1-blueprint",
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.proposal_id, "blueprint-refresh-plan-11-1-1")
        self.assertEqual(result.refresh_class, "project_state_refresh")
        self.assertEqual(result.target_blueprint_paths, ("_blueprints/current/project_state.md",))
        self.assertEqual(result.receipt_path, "docs/cartographer-live-receipts/blueprint-refresh-plan-11-1-1.md")
        self.assertEqual(result.source_evidence_paths, ("docs/cartographer-daily-driver-autonomy-plan-11-workflow-compliance-audit.md",))
        self.assertEqual(result.trust_tier, "tier-1")
        self.assertEqual(result.approval_token_id, "approval-token-plan-11-phase-11-1-blueprint")
        self.assertTrue(result.proposal_only_proof_complete)
        self.assertFalse(result.blueprint_write_enabled)
        self.assertFalse(result.docs_write_enabled)
        self.assertFalse(result.command_execution_enabled)

    def test_required_fields_fail_closed(self) -> None:
        for field in SAFE_BLUEPRINT_REFRESH_REQUIRED_FIELDS:
            payload = self._proposal().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_safe_blueprint_refresh_write_proposal(
                    payload,
                    expected_trust_tier="tier-1",
                    expected_approval_token_id="approval-token-plan-11-phase-11-1-blueprint",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_scope_trust_token_status_and_receipt_rules_fail_closed(self) -> None:
        cases = [
            ({"refresh_class": "source_refactor"}, "unknown_refresh_class"),
            ({"target_blueprint_paths": ()}, "missing_target_blueprint_paths"),
            ({"target_blueprint_paths": ("src/app/page.tsx",)}, "target_must_be_exact_blueprint_markdown"),
            ({"target_blueprint_paths": ("_blueprints/*.md",)}, "broad_target_blueprint_path"),
            ({"target_blueprint_paths": ("_blueprints/a.md", "_blueprints/a.md")}, "duplicate_target_blueprint_path"),
            ({"receipt_path": "source_proxy/receipt.md"}, "receipt_path_must_be_docs"),
            ({"receipt_path": "docs/receipt.json"}, "receipt_path_must_be_markdown"),
            ({"source_evidence_paths": ()}, "missing_source_evidence_paths"),
            ({"source_evidence_paths": ("docs/*.md",)}, "broad_source_evidence_path"),
            ({"source_evidence_paths": ("docs/evidence.json",)}, "source_evidence_must_be_markdown"),
            ({"trust_tier": "tier-3"}, "wrong_trust_tier"),
            ({"approval_token_id": "other-token"}, "wrong_approval_token"),
            ({"status": "approved"}, "status_must_remain_proposed"),
            ({"verification_plan": ()}, "missing_verification_plan"),
            ({"exact_change_summary": "Apply now to refresh the blueprint."}, "change_summary_must_not_request_application"),
            ({"rollback_guidance": "Force push a rollback."}, "rollback_guidance_must_not_recommend_force"),
            ({"created_at": "2026-05-23T12:10:00Z"}, "created_at_in_future"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_safe_blueprint_refresh_write_proposal(
                    {**self._proposal().to_dict(), **override},
                    expected_trust_tier="tier-1",
                    expected_approval_token_id="approval-token-plan-11-phase-11-1-blueprint",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.blueprint_write_enabled)
                self.assertFalse(result.docs_write_enabled)

    def test_module_exposes_no_write_execution_git_api_mutation_or_storage_surface(self) -> None:
        source = inspect.getsource(blueprint_refresh_writes)
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

    def test_blueprint_refresh_api_preview_is_proposal_only(self) -> None:
        response = TestClient(_test_app()).get("/v1/cartographer/expansion/blueprint-refresh/proposals")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["api_preview_only"])
        self.assertEqual(payload["blueprint_refresh_status"]["phase"], SAFE_BLUEPRINT_REFRESH_WRITES_PHASE)
        self.assertEqual(payload["validation"]["status"], "accepted")
        self.assertFalse(payload["blueprint_write_enabled"])
        self.assertFalse(payload["docs_write_enabled"])
        self.assertFalse(payload["source_write_enabled"])
        self.assertFalse(payload["test_write_enabled"])
        self.assertFalse(payload["command_execution_enabled"])
        self.assertFalse(payload["queue_execution_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])

    @staticmethod
    def _proposal() -> SafeBlueprintRefreshWriteProposal:
        return SafeBlueprintRefreshWriteProposal(
            proposal_id="blueprint-refresh-plan-11-1-1",
            refresh_class="project_state_refresh",
            target_blueprint_paths=("_blueprints/current/project_state.md",),
            receipt_path="docs/cartographer-live-receipts/blueprint-refresh-plan-11-1-1.md",
            exact_change_summary="Refresh the project-state blueprint after proposal-only proof without applying the edit.",
            source_evidence_paths=("docs/cartographer-daily-driver-autonomy-plan-11-workflow-compliance-audit.md",),
            rollback_guidance="No write has occurred; discard proposal if not approved.",
            verification_plan=("manual_review_only", "run exact blueprint validation after separate approval"),
            trust_tier="tier-1",
            approval_token_id="approval-token-plan-11-phase-11-1-blueprint",
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
