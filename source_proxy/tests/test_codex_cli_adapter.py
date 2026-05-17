from __future__ import annotations

import subprocess
import unittest

from source_proxy.codex.adapter import (
    build_codex_cli_status,
    validate_codex_cli_argv,
)


class CodexCliAdapterTests(unittest.TestCase):
    def test_missing_codex_returns_config_blocked(self) -> None:
        payload = build_codex_cli_status(command_resolver=lambda _: None)

        self.assertEqual(payload["tool"], "codex_cli")
        self.assertEqual(payload["status"], "config_blocked")
        self.assertFalse(payload["installed"])
        self.assertEqual(payload["reason"], "codex_binary_not_found")
        self.assertFalse(payload["can_run_live_task"])
        self.assertFalse(payload["would_run_task"])

    def test_detected_codex_captures_version_without_running_task(self) -> None:
        def runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                args=args[0],
                returncode=0,
                stdout="codex-cli 1.2.3\n",
                stderr="",
            )

        payload = build_codex_cli_status(
            command_resolver=lambda _: "/usr/local/bin/codex",
            command_runner=runner,
        )

        self.assertEqual(payload["status"], "detected")
        self.assertTrue(payload["installed"])
        self.assertEqual(payload["version"], "1.2.3")
        self.assertEqual(payload["raw_version"], "codex-cli 1.2.3")
        self.assertFalse(payload["would_run_task"])
        self.assertFalse(payload["approval_authority"])
        self.assertTrue(payload["safe_features"]["exec"])
        self.assertTrue(payload["safe_features"]["output_last_message"])

    def test_silent_version_probe_is_detected_but_unknown(self) -> None:
        def runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="", stderr="")

        payload = build_codex_cli_status(
            command_resolver=lambda _: "C:\\Windows\\System32\\codex",
            command_runner=runner,
        )

        self.assertEqual(payload["status"], "detected_version_unknown")
        self.assertEqual(payload["reason"], "version_probe_empty")
        self.assertTrue(payload["installed"])
        self.assertIsNone(payload["version"])

    def test_version_probe_retries_command_name_when_resolved_path_fails(self) -> None:
        calls: list[list[str]] = []

        def runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            command = list(args[0])  # type: ignore[arg-type]
            calls.append(command)
            if command[0].endswith("codex.EXE"):
                raise PermissionError("access denied")
            return subprocess.CompletedProcess(args=command, returncode=0, stdout="codex 2.3.4", stderr="")

        payload = build_codex_cli_status(
            command_resolver=lambda _: "C:\\Program Files\\WindowsApps\\codex.EXE",
            command_runner=runner,
        )

        self.assertEqual(payload["status"], "detected")
        self.assertEqual(payload["version"], "2.3.4")
        self.assertEqual(calls[-1], ["codex", "--version"])

    def test_dangerous_flags_are_blocked(self) -> None:
        payload = validate_codex_cli_argv(
            [
                "codex",
                "exec",
                "--dangerously-bypass-approvals-and-sandbox",
                "--sandbox",
                "danger-full-access",
            ]
        )

        self.assertFalse(payload["allowed"])
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", payload["blocked_reasons"])
        self.assertIn("--sandbox danger-full-access", payload["blocked_reasons"])

    def test_safe_readonly_probe_shape_is_allowed(self) -> None:
        payload = validate_codex_cli_argv(
            [
                "codex",
                "exec",
                "--json",
                "--output-last-message",
                "/tmp/final.md",
                "--sandbox=read-only",
            ]
        )

        self.assertTrue(payload["allowed"])
        self.assertEqual(payload["blocked_reasons"], [])


if __name__ == "__main__":
    unittest.main()
