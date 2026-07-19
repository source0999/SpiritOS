from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from source_proxy.approval import model_call_authority
from source_proxy.approval.external_gate import ExternalGateError, central_gate_check
from source_proxy.approval.model_call_authority import (
    ModelCallAuthorityError,
    issue_campaign_3_5_model_call_authorization,
    revoke_campaign_3_5_model_call_authorization,
    validate_campaign_3_5_model_call_authorization,
)


class Campaign35ModelCallAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tempdir.name) / "worktree"
        self.root.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "campaign35@example.invalid")
        self._git("config", "user.name", "Campaign 3.5 Test")
        (self.root / "package.json").write_text("{}\n", encoding="utf-8")
        (self.root / "source_proxy").mkdir()
        (self.root / "source_proxy" / "placeholder.py").write_text("# test\n", encoding="utf-8")
        self._git("add", "package.json", "source_proxy/placeholder.py")
        self._git("commit", "-qm", "test worktree")
        self.branch = self._git("branch", "--show-current")
        self.environment = {
            "SPIRITOS_APPROVAL_ROOT": str(self.root),
            "SPIRITOS_APPROVAL_REPOSITORY": "campaign-3-5-test",
            "SPIRITOS_APPROVAL_STATE_DIR": str(Path(self._tempdir.name) / "state"),
        }

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_issued_authority_is_durable_scoped_and_checked_by_central_gate(self) -> None:
        with self._authority_environment():
            issued = issue_campaign_3_5_model_call_authorization(
                operator="spiritos-local-operator"
            )
            receipt = central_gate_check(
                "model_call",
                increment_id="campaign-3.5",
                run_id="task-1:architect",
                model_alias="coder",
            )

        self.assertEqual(issued["state"], "approved")
        self.assertEqual(issued["campaign_id"], "campaign-3.5")
        self.assertEqual(issued["allowed_actions"], ["apply", "model_call"])
        self.assertTrue(issued["revocable"])
        self.assertTrue(issued["secret_exposed"] is False)
        self.assertEqual(receipt.approved_increment, "campaign-3.5")
        self.assertTrue(receipt.approval_token_id.startswith("mca_"))
        with self._authority_environment():
            apply_receipt = central_gate_check(
                "apply",
                increment_id="campaign-3.5",
                run_id="coding-run-test",
            )
        self.assertEqual(apply_receipt.action, "apply")

    def test_provider_scope_replay_and_revocation_fail_closed(self) -> None:
        with self._authority_environment():
            issued = issue_campaign_3_5_model_call_authorization(
                operator="spiritos-local-operator"
            )
            with self.assertRaises(ModelCallAuthorityError) as forbidden:
                validate_campaign_3_5_model_call_authorization(
                    action="model_call", model_alias="openai", run_id="task-1"
                )
            revoked = revoke_campaign_3_5_model_call_authorization(
                operator="spiritos-local-operator"
            )
            with self.assertRaises(ExternalGateError) as replay:
                central_gate_check(
                    "model_call",
                    increment_id="campaign-3.5",
                    run_id="task-1:replay",
                    model_alias="coder",
                )

        self.assertEqual(forbidden.exception.reason_code, "model_call_authority_model_forbidden")
        self.assertEqual(revoked["authorization_id"], issued["authorization_id"])
        self.assertEqual(replay.exception.reason_code, "model_call_authority_missing")

    def test_issuance_refuses_a_dirty_worktree(self) -> None:
        (self.root / "untracked-change.txt").write_text("unsafe authority drift\n", encoding="utf-8")
        with self._authority_environment():
            with self.assertRaises(ModelCallAuthorityError) as blocked:
                issue_campaign_3_5_model_call_authorization(
                    operator="spiritos-local-operator"
                )
        self.assertEqual(blocked.exception.reason_code, "model_call_authority_dirty_worktree")

    def _authority_environment(self):
        return _AuthorityEnvironment(self.environment, self.branch)

    def _git(self, *arguments: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(self.root), *arguments], text=True
        ).strip()


class _AuthorityEnvironment:
    def __init__(self, environment: dict[str, str], branch: str) -> None:
        self._environment = environment
        self._branch = branch

    def __enter__(self) -> None:
        self._environment_patch = patch.dict(os.environ, self._environment, clear=False)
        self._branch_patch = patch.object(
            model_call_authority, "AUTHORIZED_BRANCH", self._branch
        )
        self._environment_patch.start()
        self._branch_patch.start()

    def __exit__(self, *_args: object) -> None:
        self._branch_patch.stop()
        self._environment_patch.stop()
