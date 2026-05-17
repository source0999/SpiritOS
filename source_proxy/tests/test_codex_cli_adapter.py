from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from source_proxy.codex.adapter import (
    CodexEnvelopeError,
    CodexExecutionEnvelope,
    build_codex_command,
    build_codex_cli_status,
    codex_subprocess_env,
    validate_codex_envelope,
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

    def test_command_builder_emits_safe_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            envelope = CodexExecutionEnvelope(
                workspace=root,
                task_id="codex-task-1",
                prompt_file=root / "tmp" / "codex" / "task.md",
                output_file=root / "tmp" / "codex" / "final.md",
                output_dir=root / "tmp" / "codex",
                allowed_files=("docs/codex-cli-adapter-plan.md",),
                blocked_files=("source_proxy/main.py",),
                sandbox="workspace-write",
            )

            command = build_codex_command(envelope)

        self.assertEqual(command[:5], ["codex", "exec", "--cd", str(root), "--json"])
        self.assertIn("--output-last-message", command)
        self.assertIn("--sandbox", command)
        self.assertIn("workspace-write", command)
        self.assertEqual(command[-1], str((root / "tmp" / "codex" / "task.md").resolve()))

    def test_envelope_rejects_dangerous_sandbox(self) -> None:
        root = Path("/repo").resolve()
        envelope = CodexExecutionEnvelope(
            workspace=root,
            task_id="codex-task-2",
            prompt_file=root / "tmp" / "task.md",
            output_file=root / "tmp" / "final.md",
            output_dir=root / "tmp",
            sandbox="danger-full-access",
        )

        validation = validate_codex_envelope(envelope)

        self.assertFalse(validation["ok"])
        self.assertIn(
            {"path": "*", "reason_code": "unsafe_sandbox"},
            validation["blocked_reasons"],
        )
        with self.assertRaises(CodexEnvelopeError):
            build_codex_command(envelope)

    def test_envelope_rejects_secret_and_escape_paths(self) -> None:
        root = Path("/repo").resolve()
        envelope = CodexExecutionEnvelope(
            workspace=root,
            task_id="codex-task-3",
            prompt_file=root / "tmp" / "task.md",
            output_file=root / "tmp" / "final.md",
            output_dir=root / "tmp",
            allowed_files=("../outside.py", ".env.local"),
        )

        validation = validate_codex_envelope(envelope)
        reason_codes = {item["reason_code"] for item in validation["blocked_reasons"]}

        self.assertFalse(validation["ok"])
        self.assertIn("allowed_file_path_escape", reason_codes)
        self.assertIn("allowed_file_protected_path", reason_codes)

    def test_env_allowlist_drops_secret_values(self) -> None:
        env = codex_subprocess_env(
            {
                "PATH": "/usr/bin",
                "HOME": "/home/source",
                "OPENAI_API_KEY": "secret",
                "SOURCE_PROXY_TOKEN": "secret",
            }
        )

        self.assertEqual(env, {"PATH": "/usr/bin", "HOME": "/home/source"})


if __name__ == "__main__":
    unittest.main()
