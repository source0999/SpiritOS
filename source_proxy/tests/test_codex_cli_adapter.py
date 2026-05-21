from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from source_proxy.codex.adapter import (
    CodexEnvelopeError,
    CodexExecutionEnvelope,
    build_codex_command,
    build_codex_cli_status,
    codex_subprocess_env,
    validate_codex_envelope,
    validate_codex_cli_argv,
)
from source_proxy.codex.task_packet import CodexTaskPacketError, build_codex_task_packet
from source_proxy.codex.evidence import (
    build_codex_evidence_packet,
    summarize_codex_evidence,
    write_codex_evidence_packet,
)
from source_proxy.main import app


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
            allowed_files=("../outside.py", ".env.local", "%2e%2e/outside.md"),
        )

        validation = validate_codex_envelope(envelope)
        reason_codes = {item["reason_code"] for item in validation["blocked_reasons"]}

        self.assertFalse(validation["ok"])
        self.assertIn("allowed_file_path_escape", reason_codes)
        self.assertIn("allowed_file_protected_path", reason_codes)
        self.assertIn("allowed_file_encoded_path_not_allowed", reason_codes)

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

    def test_codex_route_readonly_returns_config_blocked_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            (root / ".git").mkdir()
            with patch("source_proxy.api.codex_adapter.Path.cwd", return_value=root):
                client = TestClient(app)
                response = client.post(
                    "/v1/coding/codex",
                    json={
                        "mode": "readonly",
                        "task": "Summarize the proxy runner safety contract.",
                        "allowed_files": [],
                        "target_file": None,
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "config_blocked")
        self.assertEqual(payload["execution_state"], "config_blocked")
        self.assertEqual(payload["reason_code"], "codex_route_live_execution_not_enabled")
        self.assertFalse(payload["live_execution"]["enabled"])
        self.assertEqual(payload["live_execution"]["allowed_modes"], ["proposal", "readonly"])
        self.assertEqual(payload["live_execution"]["blocked_modes"], ["apply", "commit", "push"])
        self.assertEqual(payload["changed_files"], [])
        self.assertTrue(payload["preview_ready"])
        self.assertEqual(
            payload["authority"],
            {
                "approval_authority": False,
                "apply_authority": False,
                "commit_authority": False,
                "push_authority": False,
            },
        )
        self.assertFalse(payload["would_run_task"])
        self.assertFalse(payload["approval_authority"])
        self.assertFalse(payload["apply_authority"])
        self.assertFalse(payload["commit_authority"])
        self.assertFalse(payload["push_authority"])

    def test_codex_route_surfaces_missing_cli_status_while_config_blocked(self) -> None:
        missing_cli_status = build_codex_cli_status(command_resolver=lambda _: None)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            (root / ".git").mkdir()
            with (
                patch("source_proxy.api.codex_adapter.Path.cwd", return_value=root),
                patch(
                    "source_proxy.api.codex_adapter.build_codex_cli_status",
                    return_value=missing_cli_status,
                ),
            ):
                client = TestClient(app)
                response = client.post(
                    "/v1/coding/codex",
                    json={
                        "mode": "readonly",
                        "task": "Summarize the proxy runner safety contract.",
                        "allowed_files": [],
                        "target_file": None,
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "config_blocked")
        self.assertEqual(payload["execution_state"], "config_blocked")
        self.assertEqual(payload["reason_code"], "codex_route_live_execution_not_enabled")
        self.assertFalse(payload["live_execution"]["enabled"])
        self.assertEqual(payload["changed_files"], [])
        self.assertTrue(payload["preview_ready"])
        self.assertFalse(payload["would_run_task"])
        self.assertFalse(payload["approval_authority"])
        self.assertFalse(payload["apply_authority"])
        self.assertFalse(payload["commit_authority"])
        self.assertFalse(payload["push_authority"])
        self.assertEqual(payload["codex_cli_status"]["tool"], "codex_cli")
        self.assertEqual(payload["codex_cli_status"]["status"], "config_blocked")
        self.assertEqual(payload["codex_cli_status"]["reason"], "codex_binary_not_found")
        self.assertFalse(payload["codex_cli_status"]["installed"])
        self.assertFalse(payload["codex_cli_status"]["can_run_live_task"])
        self.assertFalse(payload["codex_cli_status"]["would_run_task"])

    def test_codex_route_requires_allowed_files_for_proposal(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/v1/coding/codex",
            json={
                "mode": "proposal",
                "task": "Append one docs sentence.",
                "target_file": "docs/phase-8-manual-check.md",
                "allowed_files": [],
            },
        )

        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertEqual(detail["status"], "blocked")
        self.assertEqual(detail["reason_code"], "codex_proposal_missing_allowed_files")
        self.assertFalse(detail["approval_authority"])
        self.assertFalse(detail["apply_authority"])
        self.assertFalse(detail["commit_authority"])
        self.assertFalse(detail["push_authority"])

    def test_codex_route_proposal_config_blocked_has_no_authority(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/v1/coding/codex",
            json={
                "mode": "proposal",
                "task": "Append one docs sentence.",
                "target_file": "docs/phase-8-manual-check.md",
                "allowed_files": ["docs/phase-8-manual-check.md"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "config_blocked")
        self.assertEqual(payload["execution_state"], "config_blocked")
        self.assertEqual(payload["reason_code"], "codex_route_live_execution_not_enabled")
        self.assertEqual(
            payload["authority"],
            {
                "approval_authority": False,
                "apply_authority": False,
                "commit_authority": False,
                "push_authority": False,
            },
        )
        self.assertFalse(payload["would_run_task"])
        self.assertFalse(payload["approval_authority"])
        self.assertFalse(payload["apply_authority"])
        self.assertFalse(payload["commit_authority"])
        self.assertFalse(payload["push_authority"])

    def test_codex_route_proposal_exposes_honest_config_block_state(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/v1/coding/codex",
            json={
                "mode": "proposal",
                "task": "Append one docs sentence.",
                "target_file": "docs/phase-8-manual-check.md",
                "allowed_files": ["docs/phase-8-manual-check.md"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "config_blocked")
        self.assertEqual(payload["execution_state"], "config_blocked")
        self.assertEqual(payload["reason_code"], "codex_route_live_execution_not_enabled")
        self.assertTrue(payload["proposal_ready"])
        self.assertFalse(payload["preview_ready"])
        self.assertFalse(payload["live_execution"]["enabled"])
        self.assertEqual(
            payload["live_execution"]["reason_code"],
            "codex_route_live_execution_not_enabled",
        )
        self.assertEqual(payload["command_preview"][:2], ["codex", "exec"])
        self.assertEqual(
            payload["authority"],
            {
                "approval_authority": False,
                "apply_authority": False,
                "commit_authority": False,
                "push_authority": False,
            },
        )
        self.assertFalse(payload["would_run_task"])
        self.assertFalse(payload["approval_authority"])
        self.assertFalse(payload["apply_authority"])
        self.assertFalse(payload["commit_authority"])
        self.assertFalse(payload["push_authority"])

    def test_codex_route_rejects_apply_commit_push_modes(self) -> None:
        client = TestClient(app)
        for mode in ("apply", "commit", "push"):
            response = client.post(
                "/v1/coding/codex",
                json={
                    "mode": mode,
                    "task": "Do unsafe thing.",
                    "allowed_files": [],
                },
            )

            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["detail"]["reason_code"], "codex_mode_blocked")

    def test_codex_route_rejects_unsafe_target_and_sandbox(self) -> None:
        client = TestClient(app)

        unsafe_target = client.post(
            "/v1/coding/codex",
            json={
                "mode": "proposal",
                "task": "Update env.",
                "target_file": ".env",
                "allowed_files": [".env"],
            },
        )
        unsafe_sandbox = client.post(
            "/v1/coding/codex",
            json={
                "mode": "readonly",
                "task": "Summarize docs.",
                "sandbox_policy": "danger-full-access",
                "allowed_files": [],
            },
        )

        self.assertEqual(unsafe_target.status_code, 400)
        self.assertEqual(unsafe_target.json()["detail"]["reason_code"], "codex_protected_path")
        self.assertEqual(unsafe_sandbox.status_code, 400)
        self.assertEqual(unsafe_sandbox.json()["detail"]["reason_code"], "unsafe_sandbox")

    def test_codex_route_blocks_protected_allowed_files_and_escape_paths(self) -> None:
        client = TestClient(app)
        cases = [
            (
                {
                    "mode": "proposal",
                    "task": "Update local env.",
                    "target_file": ".env.local",
                    "allowed_files": [".env.local"],
                },
                "codex_protected_path",
            ),
            (
                {
                    "mode": "proposal",
                    "task": "Update certificate.",
                    "target_file": "certificates/spirit-dev-key.pem",
                    "allowed_files": ["certificates/spirit-dev-key.pem"],
                },
                "codex_protected_path",
            ),
            (
                {
                    "mode": "proposal",
                    "task": "Update outside file.",
                    "target_file": "../outside.md",
                    "allowed_files": ["../outside.md"],
                },
                "codex_path_escape",
            ),
            (
                {
                    "mode": "proposal",
                    "task": "Update encoded outside file.",
                    "target_file": "%2e%2e/outside.md",
                    "allowed_files": ["%2e%2e/outside.md"],
                },
                "codex_encoded_path_not_allowed",
            ),
            (
                {
                    "mode": "proposal",
                    "task": "Update encoded outside file.",
                    "target_file": "%2e%2e%2foutside.md",
                    "allowed_files": ["%2e%2e%2foutside.md"],
                },
                "codex_encoded_path_not_allowed",
            ),
            (
                {
                    "mode": "proposal",
                    "task": "Update double encoded outside file.",
                    "target_file": "%252e%252e%252foutside.md",
                    "allowed_files": ["%252e%252e%252foutside.md"],
                },
                "codex_encoded_path_not_allowed",
            ),
            (
                {
                    "mode": "proposal",
                    "task": "Update absolute file.",
                    "target_file": "/tmp/outside.md",
                    "allowed_files": ["/tmp/outside.md"],
                },
                "codex_path_escape",
            ),
            (
                {
                    "mode": "proposal",
                    "task": "Update Windows absolute file.",
                    "target_file": "C:\\Users\\source\\.env",
                    "allowed_files": ["C:\\Users\\source\\.env"],
                },
                "codex_path_escape",
            ),
        ]

        for body, reason_code in cases:
            with self.subTest(reason_code=reason_code, body=body):
                response = client.post("/v1/coding/codex", json=body)

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["detail"]["reason_code"], reason_code)

    def test_codex_route_rejects_proposal_target_not_in_allowed_files(self) -> None:
        client = TestClient(app)

        response = client.post(
            "/v1/coding/codex",
            json={
                "mode": "proposal",
                "task": "Update one docs file.",
                "target_file": "docs/phase-8-manual-check.md",
                "allowed_files": ["docs/proxy-test-runner-plan.md"],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["reason_code"], "codex_target_not_allowed")

    def test_codex_route_readonly_preserves_empty_allowed_files_without_authority(self) -> None:
        client = TestClient(app)

        response = client.post(
            "/v1/coding/codex",
            json={
                "mode": "readonly",
                "task": "Summarize Source Proxy safety boundaries.",
                "allowed_files": [],
                "target_file": None,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["allowed_files"], [])
        self.assertIsNone(payload["target_file"])
        self.assertFalse(payload["would_run_task"])
        self.assertFalse(payload["approval_authority"])
        self.assertFalse(payload["apply_authority"])
        self.assertFalse(payload["commit_authority"])
        self.assertFalse(payload["push_authority"])

    def test_task_packet_includes_target_scope_and_safety_boundaries(self) -> None:
        packet = build_codex_task_packet(
            task="Append one docs sentence",
            target_file="docs/phase-8-manual-check.md",
            allowed_files=["docs/phase-8-manual-check.md"],
            current_branch="cartographer/next-increment",
            current_head="aee3351",
        )

        self.assertEqual(packet["packet_version"], "codex_task_packet.v1")
        self.assertEqual(packet["target_file"], "docs/phase-8-manual-check.md")
        self.assertEqual(packet["allowed_files"], ["docs/phase-8-manual-check.md"])
        self.assertEqual(packet["relevant_files"], ["docs/phase-8-manual-check.md"])
        self.assertIn("git status --short", packet["manual_checks_required"])
        self.assertIn("Do not commit.", packet["safety_rules"])
        self.assertIn("Do not push.", packet["safety_rules"])
        self.assertFalse(packet["contains_file_contents"])
        self.assertFalse(packet["approval_authority"])
        self.assertFalse(packet["apply_authority"])
        self.assertFalse(packet["commit_authority"])
        self.assertFalse(packet["push_authority"])

    def test_task_packet_is_deterministic_for_same_inputs(self) -> None:
        first = build_codex_task_packet(
            task="Append one docs sentence",
            target_file="docs/phase-8-manual-check.md",
            allowed_files=["docs/phase-8-manual-check.md"],
            current_branch="cartographer/next-increment",
            current_head="aee3351",
        )
        second = build_codex_task_packet(
            task="Append one docs sentence",
            target_file="docs/phase-8-manual-check.md",
            allowed_files=["docs/phase-8-manual-check.md"],
            current_branch="cartographer/next-increment",
            current_head="aee3351",
        )

        self.assertEqual(first, second)

    def test_task_packet_rejects_secret_and_escape_paths(self) -> None:
        with self.assertRaises(CodexTaskPacketError) as secret:
            build_codex_task_packet(task="Read secrets", target_file=".env", allowed_files=[".env"])
        with self.assertRaises(CodexTaskPacketError) as escape:
            build_codex_task_packet(task="Edit outside", target_file="../outside.md", allowed_files=["../outside.md"])
        with self.assertRaises(CodexTaskPacketError) as encoded:
            build_codex_task_packet(
                task="Edit encoded outside",
                target_file="%2e%2e/outside.md",
                allowed_files=["%2e%2e/outside.md"],
            )

        self.assertEqual(secret.exception.reason_code, "codex_task_protected_path")
        self.assertEqual(escape.exception.reason_code, "codex_task_path_escape")
        self.assertEqual(
            encoded.exception.reason_code,
            "codex_task_encoded_path_not_allowed",
        )

    def test_task_packet_rejects_target_not_in_explicit_allowed_files(self) -> None:
        with self.assertRaises(CodexTaskPacketError) as blocked:
            build_codex_task_packet(
                task="Append docs note",
                target_file="docs/phase-8-manual-check.md",
                allowed_files=["docs/proxy-test-runner-plan.md"],
            )

        self.assertEqual(blocked.exception.reason_code, "codex_task_target_not_allowed")

    def test_evidence_packet_captures_run_summary_and_safety_verdict(self) -> None:
        packet = build_codex_evidence_packet(
            task_id="codex-task-1",
            command=["codex", "exec", "--sandbox", "read-only", "summarize docs"],
            sandbox="read-only",
            started_at="2026-05-17T20:00:00Z",
            finished_at="2026-05-17T20:00:05Z",
            exit_code=0,
            final_message="Summary complete.",
            stdout='{"type":"thread.started"}\n{"type":"turn.completed"}\n',
            stderr="",
            changed_files_before=[],
            changed_files_after=[],
            diff_stat="",
            diff="",
            head_before="aee3351",
            head_after="aee3351",
        )

        self.assertEqual(packet["artifact_version"], "codex_evidence.v1")
        self.assertEqual(packet["worker"], "codex_cli")
        self.assertEqual(packet["json_event_count"], 2)
        self.assertEqual(packet["safety_verdict"], "passed")
        self.assertEqual(packet["recommendation"], "ready_for_review")
        self.assertFalse(packet["truncation"]["stdout"])
        self.assertEqual(packet["replay_summary"]["task_id"], "codex-task-1")
        self.assertEqual(packet["replay_summary"]["mode"], "readonly")
        self.assertFalse(packet["replay_summary"]["changed_files_delta"])
        self.assertFalse(packet["approval_authority"])
        self.assertFalse(packet["apply_authority"])
        self.assertFalse(packet["commit_authority"])
        self.assertFalse(packet["push_authority"])

    def test_evidence_summary_is_truncated_replayable_and_authority_free(self) -> None:
        packet = build_codex_evidence_packet(
            task_id="codex-task-long",
            command=["codex", "exec", "--sandbox", "workspace-write"],
            sandbox="workspace-write",
            started_at="2026-05-17T20:00:00Z",
            finished_at="2026-05-17T20:00:05Z",
            exit_code=0,
            final_message="M" * 80,
            stdout='{"type":"thread.started"}\n' + ("O" * 80),
            stderr="E" * 80,
            changed_files_before=[],
            changed_files_after=["docs/phase-8-manual-check.md"],
            diff_stat="docs/phase-8-manual-check.md | 1 +",
            diff="D" * 80,
            head_before="aee3351",
            head_after="aee3351",
            excerpt_chars=24,
        )
        summary = summarize_codex_evidence(packet)

        self.assertTrue(packet["truncation"]["final_message"])
        self.assertTrue(packet["truncation"]["stdout"])
        self.assertTrue(packet["truncation"]["stderr"])
        self.assertTrue(packet["truncation"]["diff"])
        self.assertIn("[truncated]", summary["stdout_excerpt"])
        self.assertEqual(summary["mode"], "proposal")
        self.assertEqual(summary["changed_files_after"], ["docs/phase-8-manual-check.md"])
        self.assertTrue(summary["changed_files_delta"])
        self.assertEqual(summary["safety_verdict"], "blocked_changed_files_delta")
        self.assertEqual(summary["recommendation"], "blocked")
        self.assertFalse(summary["approval_authority"])
        self.assertFalse(summary["apply_authority"])
        self.assertFalse(summary["commit_authority"])
        self.assertFalse(summary["push_authority"])

    def test_evidence_packet_blocks_head_or_changed_file_drift(self) -> None:
        changed = build_codex_evidence_packet(
            task_id="codex-task-2",
            command=["codex", "exec"],
            sandbox="read-only",
            started_at="2026-05-17T20:00:00Z",
            finished_at="2026-05-17T20:00:05Z",
            exit_code=0,
            changed_files_before=[],
            changed_files_after=["docs/phase-8-manual-check.md"],
            head_before="aee3351",
            head_after="aee3351",
        )
        head = build_codex_evidence_packet(
            task_id="codex-task-3",
            command=["codex", "exec"],
            sandbox="read-only",
            started_at="2026-05-17T20:00:00Z",
            finished_at="2026-05-17T20:00:05Z",
            exit_code=0,
            changed_files_before=[],
            changed_files_after=[],
            head_before="aee3351",
            head_after="abcdef0",
        )

        self.assertEqual(changed["safety_verdict"], "blocked_changed_files_delta")
        self.assertEqual(changed["recommendation"], "blocked")
        self.assertEqual(head["safety_verdict"], "blocked_head_changed")
        self.assertEqual(head["recommendation"], "blocked")

    def test_evidence_packet_redacts_secret_shaped_paths_and_writes_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            packet = build_codex_evidence_packet(
                task_id="codex/task:secret",
                command=["codex", "exec", "OPENAI_API_KEY=secret"],
                sandbox="read-only",
                started_at="2026-05-17T20:00:00Z",
                finished_at="2026-05-17T20:00:05Z",
                exit_code=0,
                final_message="Read .env.local",
                stdout="token=secret\nok",
                stderr="",
                changed_files_before=[".env.local"],
                changed_files_after=[".env.local"],
                head_before="aee3351",
                head_after="aee3351",
            )
            path = write_codex_evidence_packet(packet, output_dir=Path(temp_dir))
            content = path.read_text()

        self.assertEqual(path.name, "codex-task-secret.json")
        self.assertIn("[redacted-protected-path]", content)
        self.assertNotIn(".env.local", content)
        self.assertNotIn("token=secret", content)


if __name__ == "__main__":
    unittest.main()
