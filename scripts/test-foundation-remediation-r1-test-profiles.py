#!/usr/bin/env python3
"""Focused regressions for R1 test-profile definition honesty."""
from __future__ import annotations

import importlib.util
import json
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = Path(__file__).with_name("validate-foundation-remediation-r1-test-profiles.py")
SCANNER_PATH = Path(__file__).with_name("scan-foundation-remediation-r1-secrets.py")
REGISTRY_PATH = ROOT / "docs/architecture/foundation-remediation-r1-test-profiles.json"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_module("foundation_r1_test_profile_validator", VALIDATOR_PATH)
SCANNER = load_module("foundation_r1_secret_scanner", SCANNER_PATH)


class TestProfileDefinitionTests(unittest.TestCase):
    def test_placeholders_are_rejected_before_terminal_closeout(self) -> None:
        failure = VALIDATOR.command_definition_failure(
            "portable-authority",
            "focused runtime identity and approval authority tests",
        )
        self.assertEqual(failure, "profile_command_placeholder:portable-authority")

    def test_evidence_and_registry_profiles_cannot_invoke_terminal_validators(self) -> None:
        for profile_id, command in (
            (
                "evidence-provenance",
                "python3 scripts/validate-foundation-remediation-r1-evidence.py",
            ),
            (
                "test-profiles",
                "python3 scripts/validate-foundation-remediation-r1-test-profiles.py",
            ),
        ):
            with self.subTest(profile_id=profile_id):
                self.assertEqual(
                    VALIDATOR.command_definition_failure(profile_id, command),
                    f"profile_command_recursive:{profile_id}",
                )

    def test_clean_proving_task_cannot_be_replaced_by_a_test_profile(self) -> None:
        self.assertEqual(
            VALIDATOR.command_definition_failure(
                "clean-proving-task",
                "python3 -m pytest -q source_proxy/tests/test_source_proxy_end_to_end.py",
            ),
            "terminal_proof_must_not_be_test_profile:clean-proving-task",
        )

    def test_checked_in_registry_has_only_concrete_nonrecursive_commands(self) -> None:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        profiles = registry["profiles"]
        self.assertEqual({profile["id"] for profile in profiles}, VALIDATOR.REQUIRED_IDS)
        for profile in profiles:
            profile_id = profile["id"]
            command = profile["command"]
            with self.subTest(profile_id=profile_id):
                self.assertIsNone(VALIDATOR.command_definition_failure(profile_id, command))
                for token in shlex.split(command):
                    if token.startswith(("scripts/", "source_proxy/", "src/")) and token.endswith(
                        (".py", ".ts", ".tsx")
                    ):
                        self.assertTrue((ROOT / token).is_file(), f"missing command target: {token}")

    def test_secret_scan_detects_tracked_high_confidence_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
            clean = root / "clean.txt"
            clean.write_text("no credentials here\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "clean.txt"], check=True)
            self.assertEqual(SCANNER.scan_tracked_files(root), [])

            secret = root / "secret.txt"
            secret.write_text("ghp_" + "a" * 40 + "\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "secret.txt"], check=True)
            self.assertEqual(
                SCANNER.scan_tracked_files(root),
                ["high_confidence_secret:github_token:secret.txt"],
            )


if __name__ == "__main__":
    unittest.main()
