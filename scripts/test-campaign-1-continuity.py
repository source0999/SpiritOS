#!/usr/bin/env python3
"""Focused pass/fail tests for the Campaign 1 continuity validator."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

VALIDATOR = Path(__file__).with_name("validate-campaign-1-continuity.py")


def git(directory: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(directory), *args], text=True).strip()


def init_repo(directory: Path) -> None:
    directory.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(directory)], check=True)
    subprocess.run(["git", "-C", str(directory), "config", "user.email", "campaign-test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(directory), "config", "user.name", "Campaign Test"], check=True)
    subprocess.run(["git", "-C", str(directory), "commit", "--allow-empty", "-qm", "fixture"], check=True)


class ContinuityValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.root, self.proxy, self.flix, self.audit = (base / name for name in ("campaign", "proxy", "flix", "audit"))
        for repo in (self.root, self.proxy, self.flix, self.audit): init_repo(repo)
        docs = self.root / "docs/architecture"; docs.mkdir(parents=True)
        (self.root / "src/app/v1/operator/session").mkdir(parents=True)
        (self.root / "src/app/v1/operator/session/route.ts").write_text("export {};\n", encoding="utf-8")
        head = git(self.root, "rev-parse", "HEAD")
        state = {"schema": "spiritos-campaign-1-state/v1", "campaign_id": "spiritos-campaign-1", "plan_path": "docs/architecture/campaign-1-plan.md", "ledger_path": "docs/architecture/campaign-1-ledger.md", "base_commit": head, "branch": git(self.root, "branch", "--show-current"), "recorded_head": head, "checkpoint_commit_policy": "parent_of_atomic_checkpoint", "current_phase": "Phase 1", "current_increment": "fixture", "completed_gate_ids": [], "partial_gate_ids": ["fixture"], "next_gate_id": "fixture_next", "protected_heads": {"source_proxy": git(self.proxy, "rev-parse", "HEAD"), "spiritflix": git(self.flix, "rev-parse", "HEAD"), "architecture_audit": git(self.audit, "rev-parse", "HEAD")}, "allowed_mutable_root": str(self.root), "dirty_state_policy": "fixture", "valid_stop_reasons": ["verification_failure"], "go_eligible": False, "last_verified_at": "2026-07-13T00:00:00Z"}
        (docs / "campaign-1-plan.md").write_text("# Campaign 1\nBorrowed `_worktrees/` remain untouched.\n", encoding="utf-8")
        (docs / "campaign-1-ledger.md").write_text(f"spiritos-campaign-1 campaign-1-plan.md {head}\nPhase: **Phase 1**\noperator-session\nBorrowed `_worktrees/` untouched.\nfixture_next\nGO eligibility: `false`\n", encoding="utf-8")
        self.state_path = docs / "campaign-1-state.json"; self.state_path.write_text(json.dumps(state), encoding="utf-8")
        self.env = {**os.environ, "SPIRITOS_CAMPAIGN1_CONTINUITY_ROOT": str(self.root), "SPIRITOS_CAMPAIGN1_SOURCE_PROXY_ROOT": str(self.proxy), "SPIRITOS_CAMPAIGN1_SPIRITFLIX_ROOT": str(self.flix), "SPIRITOS_CAMPAIGN1_ARCHITECTURE_AUDIT_ROOT": str(self.audit)}

    def tearDown(self) -> None: self.temp.cleanup()
    def run_validator(self) -> subprocess.CompletedProcess[str]: return subprocess.run([sys.executable, str(VALIDATOR)], text=True, capture_output=True, env=self.env, check=False)
    def test_accepts_consistent_checkpoint(self) -> None:
        result = self.run_validator(); self.assertEqual(result.returncode, 0, result.stdout + result.stderr); self.assertIn("CAMPAIGN_1_CONTINUITY_VALID", result.stdout)
    def test_rejects_recorded_head_mismatch(self) -> None:
        state = json.loads(self.state_path.read_text(encoding="utf-8")); state["recorded_head"] = "0" * 40; self.state_path.write_text(json.dumps(state), encoding="utf-8")
        result = self.run_validator(); self.assertNotEqual(result.returncode, 0); self.assertIn("recorded_head_mismatch", result.stdout)


if __name__ == "__main__": unittest.main()
