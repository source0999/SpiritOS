from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from source_proxy.cartographer.apply import CartographerApplyError, apply_approved_doc_proposal
from source_proxy.cartographer.service import (
    build_cartographer_audit_trail,
    build_cartographer_branch_recommendations,
    build_cartographer_change_scribe,
    build_cartographer_commit_proposals,
    build_cartographer_project_health,
    build_cartographer_projects,
    build_cartographer_proposals,
    build_cartographer_push_queue,
    build_cartographer_repo_map,
    build_cartographer_status,
)


class CartographerSafetyAuditTests(unittest.TestCase):
    def test_allowlist_blocks_outside_roots_and_path_traversal_targets(self) -> None:
        with tempfile.TemporaryDirectory() as allowed_dir, tempfile.TemporaryDirectory() as outside_dir:
            allowed = Path(allowed_dir)
            outside = Path(outside_dir)
            _write_minimal_blueprints(allowed)
            (outside / "package.json").write_text('{"secret":"SHOULD_NOT_APPEAR"}', encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": f"{allowed},/etc"}, clear=False):
                projects = build_cartographer_projects()
                health = build_cartographer_project_health()

        self.assertEqual(projects["configured_roots"][0]["path"], str(allowed.resolve()))
        self.assertEqual(projects["blocked_roots"][0]["path"], "/etc")
        self.assertEqual(projects["blocked_roots"][0]["reason"], "broad_system_root_not_allowed")
        self.assertNotIn(str(outside), str(projects))
        self.assertNotIn("SHOULD_NOT_APPEAR", str(projects))
        self.assertNotIn(str(outside), str(health))

    def test_secret_shaped_files_are_skipped_or_redacted_from_cartographer_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            (root / ".env.local").write_text("SECRET_VALUE=do-not-summarize", encoding="utf-8")
            secret_note = root / "source_proxy" / "secret_token_notes.py"
            secret_note.parent.mkdir(parents=True)
            secret_note.write_text("SECRET_TOKEN = 'initial'\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            secret_note.write_text("SECRET_TOKEN = 'changed'\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                repo_map = build_cartographer_repo_map()
                proposals = build_cartographer_proposals()
                change_scribe = build_cartographer_change_scribe()

        combined = "\n".join([str(repo_map), str(proposals), str(change_scribe)])
        self.assertNotIn("do-not-summarize", combined)
        self.assertNotIn("SECRET_TOKEN = 'changed'", combined)
        if proposals["proposals"]:
            self.assertNotIn("secret_token_notes.py", str(proposals))
            self.assertIn("[redacted]", str(proposals))

    def test_unapproved_apply_commit_and_push_do_not_change_git_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "main")
            blueprint = root / "_blueprints" / "current" / "dashboard_state.md"
            blueprint.write_text(
                blueprint.read_text(encoding="utf-8") + "\nSafety audit change.\n",
                encoding="utf-8",
            )
            _write_proposal(
                root,
                "approved",
                "bp-safety-audit",
                {
                    "status": "approved",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "proposed_files": ["_blueprints/current/dashboard_state.md"],
                    "approved_diff": "",
                    "transitions": [
                        {
                            "status": "approved",
                            "timestamp": "2026-05-16T10:00:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )

            before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            before_remote = _git_stdout(remote, "rev-parse", "refs/heads/main").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                with self.assertRaises(CartographerApplyError):
                    apply_approved_doc_proposal(
                        proposal_id="bp-safety-audit",
                        approved=False,
                        approved_by="safety-test",
                    )
                branch_recommendations = build_cartographer_branch_recommendations()
                commit_proposals = build_cartographer_commit_proposals()
                push_queue = build_cartographer_push_queue()
                audit_trail = build_cartographer_audit_trail()
            after_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            after_branch = _git_stdout(root, "branch", "--show-current").strip()
            after_remote = _git_stdout(remote, "rev-parse", "refs/heads/main").strip()

        self.assertEqual(before_head, after_head)
        self.assertEqual(before_branch, after_branch)
        self.assertEqual(before_remote, after_remote)
        self.assertFalse(branch_recommendations["actions_taken"])
        self.assertFalse(commit_proposals["actions_taken"])
        self.assertFalse(push_queue["actions_taken"])
        self.assertFalse(audit_trail["actions_taken"])

    def test_cartographer_safety_manifest_keeps_bypass_and_write_controls_locked(self) -> None:
        with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
            payload = build_cartographer_status()

        safety = payload["safety"]
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(safety["write_actions_enabled"])
        self.assertEqual(safety["write_policy"], "read_only")
        self.assertTrue(safety["approval_required_for_file_writes"])
        self.assertTrue(safety["approval_required_for_commits"])
        self.assertTrue(safety["approval_required_for_pushes"])
        self.assertFalse(safety["scout_bypass_allowed"])
        self.assertFalse(safety["source_proxy_approval_bypass_allowed"])


def _git(root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)


def _git_stdout(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout


def _write_minimal_blueprints(root: Path) -> None:
    (root / "package.json").write_text("{}", encoding="utf-8")
    blueprints = root / "_blueprints"
    (blueprints / "current").mkdir(parents=True)
    (blueprints / "runbooks").mkdir(parents=True)
    (blueprints / "INDEX.md").write_text(
        "\n".join(
            [
                "# Index",
                "| Document | Classification | Notes |",
                "| --- | --- | --- |",
                "| `current/dashboard_state.md` | current truth | Canonical. |",
                "| `runbooks/basic_chat_voice_qa.md` | manual QA/runbook | QA. |",
            ]
        ),
        encoding="utf-8",
    )
    (blueprints / "current" / "dashboard_state.md").write_text(
        _blueprint_doc(
            blueprint_id="dashboard-state",
            title="Dashboard State",
            component="dashboard",
            doc_type="current_state",
            status="active",
            source_of_truth=True,
            code_paths=["src/components/dashboard/**", "source_proxy/**"],
        ),
        encoding="utf-8",
    )
    (blueprints / "runbooks" / "basic_chat_voice_qa.md").write_text(
        _blueprint_doc(
            blueprint_id="basic-chat-voice-qa",
            title="Basic Chat Voice QA",
            component="chat-and-voice",
            doc_type="runbook",
            status="runbook",
            source_of_truth=False,
            code_paths=["src/app/api/**"],
        ),
        encoding="utf-8",
    )


def _blueprint_doc(
    *,
    blueprint_id: str,
    title: str,
    component: str,
    doc_type: str,
    status: str,
    source_of_truth: bool,
    code_paths: list[str],
) -> str:
    return "\n".join(
        [
            "---",
            f"blueprint_id: {blueprint_id}",
            f"title: {title}",
            "project: SpiritOS",
            f"component: {component}",
            f"doc_type: {doc_type}",
            f"status: {status}",
            f"source_of_truth: {'true' if source_of_truth else 'false'}",
            "owner: Britton",
            "code_paths:",
            *[f"  - {path}" for path in code_paths],
            "related_blueprints: []",
            "write_policy: proposal_only_until_dashboard_approved",
            "last_verified: 2026-05-16",
            "---",
            f"# {title}",
        ]
    )


def _write_proposal(root: Path, state: str, proposal_id: str, payload: dict[str, object]) -> None:
    proposal_dir = root / "_blueprints" / "proposals" / state
    proposal_dir.mkdir(parents=True, exist_ok=True)
    proposal_payload = {"proposal_id": proposal_id, **payload}
    (proposal_dir / f"{proposal_id}.json").write_text(
        json.dumps(proposal_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
