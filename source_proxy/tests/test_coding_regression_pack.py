from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.decision import router as decision_router
from source_proxy.decision.router import DecisionInput, decide_route, resolve_target_from_task
from source_proxy.planning.architect import (
    FallthroughToLLM,
    Plan,
    plan_bounded_proposal_create_deterministically,
    plan_task_deterministically,
)
from source_proxy.planning.plan import task_spec_from_plan, save_plan
from source_proxy.tasks.long_running import (
    approval_id_for_approved_diff,
    create_long_running_task,
    execute_approved_long_running_task,
    propose_coder_agent_diff_payload_from_plan,
    propose_dummy_product_site_create_diff,
    record_post_apply_verification,
    reset_long_running_tasks,
)
from source_proxy.planning.bounded_create import bounded_create_replacement_content
from source_proxy.verification.diff import DiffVerificationError, preview_diff_verification


DOC_TARGET = "docs/phase-8-manual-check.md"
DOC_BASE = (
    "# Phase 8 Manual Check\n\n"
    "Approved diffs should require post-apply verification before completion.\n"
)
DOC_LITERAL = "Phase 1A backend regression pack confirms approval safe docs edits."
A_PLUS_FINAL_LABELS = {
    "pass_productive",
    "pass_blocked_safely",
    "fail_quality",
    "fail_verification",
    "fail_scope",
    "fail_safety",
    "fail_honesty",
    "inconclusive_environment",
    "inconclusive_missing_evidence",
}


def _doc_append_task(literal: str = DOC_LITERAL) -> str:
    return f'Append the sentence "{literal}" to {DOC_TARGET}. Do not edit any other file.'


def _standard_doc_diff(literal: str = DOC_LITERAL, target: str = DOC_TARGET) -> str:
    return "\n".join(
        [
            f"--- a/{target}",
            f"+++ b/{target}",
            "@@ -1,3 +1,4 @@",
            " # Phase 8 Manual Check",
            " ",
            " Approved diffs should require post-apply verification before completion.",
            f"+{literal}",
            "",
        ]
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CodingRegressionPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_cwd = os.getcwd()
        self._previous_db = os.environ.get("SOURCE_PROXY_LONG_RUNNING_TASKS_DB")
        self._previous_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        self._previous_audit = os.environ.get("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG")
        self._tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tempdir.name)
        os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = str(self.root / "tasks.sqlite3")
        os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = str(self.root / "audit.jsonl")
        os.environ["SPIRIT_PROJECT_PATH"] = str(self.root)
        (self.root / "source_proxy").mkdir(parents=True, exist_ok=True)
        _write(self.root / DOC_TARGET, DOC_BASE)
        os.chdir(self.root)
        reset_long_running_tasks()

    def tearDown(self) -> None:
        reset_long_running_tasks()
        os.chdir(self._previous_cwd)
        self._restore_env("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", self._previous_db)
        self._restore_env("SPIRIT_PROJECT_PATH", self._previous_project_path)
        self._restore_env("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG", self._previous_audit)
        self._tempdir.cleanup()

    def _restore_env(self, name: str, value: str | None) -> None:
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value

    def _planned_doc_task(self, task: str | None = None, task_id: str = "task-doc"):
        planned = plan_task_deterministically(task or _doc_append_task(), task_id, self.root)
        self.assertIsInstance(planned, Plan, planned)
        return planned.plan

    def _decision_client(self) -> TestClient:
        app = FastAPI()
        app.include_router(decision_router)
        return TestClient(app)

    def test_simple_docs_edit_reaches_safe_preview_without_writing(self) -> None:
        task = _doc_append_task()
        resolved = resolve_target_from_task(task, workspace_root=self.root)
        plan = self._planned_doc_task(task)
        before = (self.root / DOC_TARGET).read_text(encoding="utf-8")

        out = propose_coder_agent_diff_payload_from_plan(
            architect_plan=plan,
            workspace_root=self.root,
            llm_call=lambda *_args: (_ for _ in ()).throw(AssertionError("LLM should not run")),
        )
        preview = preview_diff_verification(
            out["proposed_diff"],
            route_type="local_route",
            task_text=task,
            architect_plan=plan,
        )

        self.assertEqual(resolved.path, DOC_TARGET)
        self.assertTrue(resolved.exists)
        self.assertEqual(
            task_spec_from_plan(plan).to_dict(),
            {
                "schema_version": 1,
                "task_type": "modify_existing_file",
                "target": DOC_TARGET,
                "allowed_files": [DOC_TARGET],
                "forbidden_files": [
                    "source_proxy/",
                    "src/components/coding/",
                    "src/lib/coding/",
                    "src/lib/spirit/apply-unified-diff.ts",
                    "scripts/",
                    "masterProxyPlan.md",
                    "masterSwarmPlan.md",
                    "notes.md",
                ],
                "literal_requirements": [DOC_LITERAL],
                "verification": ["git apply check", "literal present", "target-only"],
                "risk_tier": "low",
                "source": "deterministic",
            },
        )
        self.assertEqual(out["coder_diagnostics"]["task_spec"]["allowed_files"], [DOC_TARGET])
        self.assertEqual(out["target"], DOC_TARGET)
        self.assertEqual([file["path"] for file in preview["changed_files"]], [DOC_TARGET])
        self.assertEqual(preview["status"], "preview_ready")
        self.assertEqual(
            preview["task_spec_check"],
            {
                "ok": True,
                "reason_codes": [],
                "allowed_files": [DOC_TARGET],
                "forbidden_files": [
                    "source_proxy/",
                    "src/components/coding/",
                    "src/lib/coding/",
                    "src/lib/spirit/apply-unified-diff.ts",
                    "scripts/",
                    "masterProxyPlan.md",
                    "masterSwarmPlan.md",
                    "notes.md",
                ],
                "changed_files": [DOC_TARGET],
                "target": DOC_TARGET,
                "task_type": "modify_existing_file",
                "summary": "TaskSpec check passed.",
                "violations": {"outside_allowed": [], "forbidden": []},
            },
        )
        self.assertTrue(preview["git_apply_check_ok"], preview.get("git_apply_check_error"))
        self.assertTrue(preview["requirement_coverage"]["ok"])
        self.assertTrue(preview["review_report"]["passed"])
        self.assertTrue(preview["limits"]["file_writes_allowed"])
        self.assertFalse(preview["would_apply_diff"])
        self.assertFalse(preview["would_execute"])
        self.assertEqual((self.root / DOC_TARGET).read_text(encoding="utf-8"), before)

    def test_a_plus_receipt_final_label_contract_has_expected_values(self) -> None:
        expected = {
            "pass_productive",
            "pass_blocked_safely",
            "fail_quality",
            "fail_verification",
            "fail_scope",
            "fail_safety",
            "fail_honesty",
            "inconclusive_environment",
            "inconclusive_missing_evidence",
        }

        self.assertEqual(A_PLUS_FINAL_LABELS, expected)
        for label in A_PLUS_FINAL_LABELS:
            self.assertRegex(label, r"^[a-z]+(?:_[a-z]+)*$")

    def test_coder_task_spec_allowed_file_passes_for_docs_diff(self) -> None:
        plan = self._planned_doc_task()

        preview = preview_diff_verification(
            _standard_doc_diff(),
            route_type="local_route",
            task_text=_doc_append_task(),
            architect_plan=plan,
        )

        self.assertEqual(preview["status"], "preview_ready")
        self.assertTrue(preview["task_spec_check"]["ok"])
        self.assertEqual(preview["task_spec_check"]["allowed_files"], [DOC_TARGET])
        self.assertEqual(preview["task_spec_check"]["changed_files"], [DOC_TARGET])
        self.assertIn(
            {
                "tier": 1,
                "id": "task_spec_allowed_files",
                "status": "passed",
                "duration_ms": 0,
                "output": (
                    "TaskSpec allowed-files check passed. "
                    f"changed=[{DOC_TARGET}] allowed=[{DOC_TARGET}]"
                ),
                "blocking": True,
            },
            preview["deterministic_checks"],
        )

    def test_coder_001_create_bundle_task_spec_preview_allows_dummy_root_wildcard(self) -> None:
        from source_proxy.tasks.long_running import generate_unified_diff_from_content

        files = {
            "README.md": "# LumaCart\n",
            "package.json": '{"name":"lumacart-dummy","private":true}\n',
            "index.html": '<div id="app">LumaCart</div>\n',
            "src/main.js": "console.log('LumaCart');\n",
            "src/products.js": "export const products = [];\n",
            "src/styles.css": "body { font-family: system-ui; }\n",
        }
        diff = "\n".join(
            generate_unified_diff_from_content(
                self.root,
                f"tests/ui-agent-trials/fixtures/dummy-product-site/{path}",
                content,
            ).strip()
            for path, content in files.items()
        ) + "\n"

        preview = preview_diff_verification(
            diff,
            route_type="local_route",
            task_text="make LumaCart under tests/ui-agent-trials/fixtures/dummy-product-site/",
            task_spec={
                "schema_version": 1,
                "task_type": "create_file_bundle",
                "target": "tests/ui-agent-trials/fixtures/dummy-product-site/",
                "allowed_files": ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
                "forbidden_files": ["package.json", "source_proxy/**", "src/app/**", ".env*"],
            },
        )

        self.assertEqual(preview["status"], "preview_ready", preview.get("blocked_reasons"))
        self.assertTrue(preview["task_spec_check"]["ok"])
        self.assertEqual(
            preview["task_spec_check"]["allowed_files"],
            ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
        )

    def test_coder_001_create_bundle_task_spec_still_rejects_root_package(self) -> None:
        from source_proxy.tasks.long_running import generate_unified_diff_from_content

        diff = generate_unified_diff_from_content(self.root, "package.json", "{}\n")

        preview = preview_diff_verification(
            diff,
            route_type="local_route",
            task_text="make LumaCart under tests/ui-agent-trials/fixtures/dummy-product-site/",
            task_spec={
                "schema_version": 1,
                "task_type": "create_file_bundle",
                "target": "tests/ui-agent-trials/fixtures/dummy-product-site/",
                "allowed_files": ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
                "forbidden_files": ["package.json", "source_proxy/**", "src/app/**", ".env*"],
            },
        )

        reason_codes = {reason["reason_code"] for reason in preview["blocked_reasons"]}
        self.assertEqual(preview["status"], "blocked")
        self.assertIn("task_spec_allowed_file_violation", reason_codes)
        self.assertIn("task_spec_forbidden_file_violation", reason_codes)

    def test_coder_task_spec_blocks_wrong_file_diff(self) -> None:
        plan = self._planned_doc_task()
        wrong_path = "source_proxy/api/decision.py"
        _write(self.root / wrong_path, "old\n")
        wrong_diff = _standard_doc_diff(target=wrong_path)

        preview = preview_diff_verification(
            wrong_diff,
            route_type="local_route",
            task_text=_doc_append_task(),
            architect_plan=plan,
        )

        reason_codes = {reason["reason_code"] for reason in preview["blocked_reasons"]}
        self.assertEqual(preview["status"], "blocked")
        self.assertIn("task_spec_allowed_file_violation", reason_codes)
        self.assertFalse(preview["limits"]["file_writes_allowed"])
        self.assertFalse(preview["would_apply_diff"])
        self.assertFalse(preview["would_execute"])
        self.assertFalse(preview["task_spec_check"]["ok"])
        self.assertEqual(preview["task_spec_check"]["changed_files"], [wrong_path])

    def test_coder_task_spec_blocks_empty_allowed_files_for_implementation(self) -> None:
        preview = preview_diff_verification(
            _standard_doc_diff(),
            route_type="local_route",
            task_text=_doc_append_task(),
            task_spec={
                "schema_version": 1,
                "task_type": "modify_existing_file",
                "target": DOC_TARGET,
                "allowed_files": [],
                "forbidden_files": [],
            },
        )

        reason_codes = {reason["reason_code"] for reason in preview["blocked_reasons"]}
        self.assertEqual(preview["status"], "blocked")
        self.assertIn("task_spec_missing_allowed_files", reason_codes)
        self.assertFalse(preview["limits"]["file_writes_allowed"])

    def test_coder_task_spec_blocks_target_unresolved_before_coder(self) -> None:
        preview = preview_diff_verification(
            _standard_doc_diff(),
            route_type="local_route",
            task_text="Please make a small documentation update explaining that approval should require verification.",
            task_spec={
                "schema_version": 1,
                "task_type": "target_unresolved",
                "target": None,
                "allowed_files": [],
                "forbidden_files": [],
                "blockers": ["target_unresolved"],
            },
        )

        reason_codes = {reason["reason_code"] for reason in preview["blocked_reasons"]}
        self.assertEqual(preview["status"], "blocked")
        self.assertIn("task_spec_target_unresolved", reason_codes)
        self.assertFalse(preview["limits"]["file_writes_allowed"])

    def test_bounded_proposal_json_target_file_wins_over_forbidden_env(self) -> None:
        task = "\n".join(
            [
                "Proposal task:",
                "",
                "```json",
                json.dumps(
                    {
                        "allowed_files": ["src/app/proxy-backend/page.tsx"],
                        "expected_checks": ["git diff --check", "target-only"],
                        "forbidden_files": [".env", ".env.local", ".env.*", "package.json"],
                        "mode": "proposal",
                        "rollback_hint": "git restore <target_file>",
                        "target_file": "src/app/proxy-backend/page.tsx",
                        "task": "Create the proxy backend page.",
                    },
                    indent=2,
                ),
                "```",
                "",
                "Safety: proposal draft only. Do not apply, commit, push, or edit files from this draft.",
            ]
        )
        resolved = resolve_target_from_task(task, workspace_root=self.root)
        decision = decide_route(DecisionInput(task=task, wants_implementation=True))

        self.assertEqual(resolved.path, "src/app/proxy-backend/page.tsx")
        self.assertEqual(resolved.source, "explicit_line")
        self.assertNotEqual(resolved.path, ".env")
        self.assertNotIn("protected_path", decision.reason_codes)
        self.assertNotIn("target_missing", decision.reason_codes)

    def _bounded_proxy_backend_proposal_task(self) -> str:
        return "\n".join(
            [
                "Target file: src/app/proxy-backend/page.tsx",
                "",
                "Create the proxy backend page.",
                "",
                "Proposal task:",
                "",
                "```json",
                json.dumps(
                    {
                        "allowed_files": ["src/app/proxy-backend/page.tsx"],
                        "expected_checks": ["git diff --check", "target-only"],
                        "forbidden_files": [
                            ".env",
                            ".env.local",
                            ".env.*",
                            "package.json",
                            "next.config.ts",
                            "README.md",
                        ],
                        "mode": "proposal",
                        "rollback_hint": "git restore <target_file>",
                        "target_file": "src/app/proxy-backend/page.tsx",
                        "task": "Create the proxy backend page.",
                    },
                    indent=2,
                ),
                "```",
            ]
        )

    def test_bounded_proposal_new_file_not_target_missing(self) -> None:
        task = self._bounded_proxy_backend_proposal_task()
        decision = decide_route(DecisionInput(task=task, wants_implementation=True))
        self.assertNotIn("target_missing", decision.reason_codes)

    def test_bounded_proposal_new_file_deterministic_coder_diff_without_llm(self) -> None:
        task = self._bounded_proxy_backend_proposal_task()
        result = plan_task_deterministically(task, "task-proxy-backend-coder", self.root)
        self.assertIsInstance(result, Plan, result)

        def fail_llm(_prompt: str, _model: str) -> str:
            raise RuntimeError("router unavailable for test")

        out = propose_coder_agent_diff_payload_from_plan(
            architect_plan=result.plan,
            workspace_root=self.root,
            llm_call=fail_llm,
        )
        self.assertFalse(out.get("coder_blocked"), out)
        self.assertIn("src/app/proxy-backend/page.tsx", out.get("target", ""))
        diff = str(out.get("proposed_diff") or "")
        self.assertIn("--- /dev/null", diff)
        self.assertIn("+++ b/src/app/proxy-backend/page.tsx", diff)
        self.assertIn("CodingAgentInterface", diff)

    def _bounded_doc_append_proposal_task(
        self,
        literal: str = "Proxy backend layout smoke test passed.",
    ) -> str:
        return "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                "",
                f'Append this exact sentence to {DOC_TARGET}: "{literal}"',
                "",
                "Proposal task:",
                "",
                "```json",
                json.dumps(
                    {
                        "allowed_files": [DOC_TARGET],
                        "expected_checks": ["git diff --check", "target-only"],
                        "forbidden_files": [
                            ".env",
                            ".env.local",
                            ".env.*",
                            "package.json",
                            "README.md",
                        ],
                        "mode": "proposal",
                        "rollback_hint": f"git restore {DOC_TARGET}",
                        "target_file": DOC_TARGET,
                        "task": f'Append this exact sentence to {DOC_TARGET}: "{literal}"',
                    },
                    indent=2,
                ),
                "```",
            ]
        )

    def test_bounded_doc_append_preview_empty_proposal_task_ignores_json_envelope(self) -> None:
        import json

        from source_proxy.decision.proposal_task import effective_planning_task_text
        from source_proxy.verification.diff import preview_diff_verification

        literal = "Proxy backend layout smoke test passed."
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                "",
                f'Append this exact sentence to {DOC_TARGET}: "{literal}"',
                "",
                "Proposal task:",
                "",
                "```json",
                json.dumps(
                    {
                        "allowed_files": [DOC_TARGET],
                        "expected_checks": ["target-only"],
                        "forbidden_files": [".env"],
                        "mode": "proposal",
                        "target_file": DOC_TARGET,
                        "task": "",
                    },
                    indent=2,
                ),
                "```",
            ]
        )
        effective = effective_planning_task_text(task)
        self.assertNotIn("allowed_files", effective)
        result = plan_task_deterministically(task, "task-empty-proposal-task", self.root)
        self.assertIsInstance(result, Plan, result)
        from source_proxy.tasks.long_running import propose_coder_agent_diff_payload_from_plan

        out = propose_coder_agent_diff_payload_from_plan(
            architect_plan=result.plan,
            workspace_root=self.root,
            llm_call=lambda *_args: (_ for _ in ()).throw(AssertionError("LLM should not run")),
        )
        diff = str(out.get("proposed_diff") or "")
        self.assertIn(literal, diff)
        preview = preview_diff_verification(
            diff,
            route_type="local_route",
            task_text=task,
            architect_plan=result.plan,
        )
        self.assertTrue(preview["requirement_coverage"]["ok"], preview["requirement_coverage"])
        self.assertEqual(preview["status"], "preview_ready", preview.get("blocked_reasons"))

    def test_bounded_doc_append_plan_and_validation_ignore_json_envelope(self) -> None:
        from source_proxy.verification.contracts import validate_replacement_content

        task = self._bounded_doc_append_proposal_task()
        result = plan_task_deterministically(task, "task-bounded-doc-append", self.root)
        self.assertIsInstance(result, Plan, result)
        self.assertTrue(result.plan.plan_id.startswith("det-md-append-"))
        literal = "Proxy backend layout smoke test passed."
        base = (self.root / DOC_TARGET).read_text(encoding="utf-8")
        content = f"{base.rstrip()}\n{literal}\n"
        validation = validate_replacement_content(
            workspace_root=self.root,
            target_path=DOC_TARGET,
            content=content,
            task_text=task,
        )
        self.assertTrue(validation["ok"], validation)
        missing_text = " ".join(validation.get("missing", []))
        for token in ("allowed_files", "forbidden_files", "expected_checks", ".env.local"):
            self.assertNotIn(token, missing_text, missing_text)

        out = propose_coder_agent_diff_payload_from_plan(
            architect_plan=result.plan,
            workspace_root=self.root,
            llm_call=lambda *_args: (_ for _ in ()).throw(AssertionError("LLM should not run")),
        )
        self.assertFalse(out.get("coder_blocked"), out)
        self.assertIn(literal, str(out.get("proposed_diff") or ""))

    def test_bounded_proposal_diff_preview_ignores_json_envelope_requirements(self) -> None:
        task = self._bounded_proxy_backend_proposal_task()
        plan = plan_task_deterministically(task, "task-proxy-preview", self.root)
        self.assertIsInstance(plan, Plan, plan)
        from source_proxy.planning.bounded_create import bounded_create_replacement_content
        from source_proxy.tasks.long_running import generate_unified_diff_from_content

        content = bounded_create_replacement_content(
            "src/app/proxy-backend/page.tsx",
            "Create the proxy backend page.",
        )
        diff = generate_unified_diff_from_content(
            self.root,
            "src/app/proxy-backend/page.tsx",
            content or "",
        )
        preview = preview_diff_verification(
            diff,
            route_type="local_route",
            next_prompt_action="run_with_coder_agent",
            task_text=task,
            architect_plan=plan.plan,
        )
        self.assertEqual(preview["status"], "preview_ready")
        self.assertTrue(preview["limits"]["file_writes_allowed"])

    def test_bounded_create_scaffold_content(self) -> None:
        content = bounded_create_replacement_content(
            "src/app/proxy-backend/page.tsx",
            "Create the proxy backend page.",
        )
        self.assertIsNotNone(content)
        assert content is not None
        self.assertIn("ProxyBackendPage", content)
        self.assertIn("CodingAgentInterface", content)

    def test_bounded_proposal_new_file_deterministic_architect_plan(self) -> None:
        task = self._bounded_proxy_backend_proposal_task()
        result = plan_task_deterministically(task, "task-proxy-backend-create", self.root)
        self.assertIsInstance(result, Plan, result)
        self.assertEqual(result.plan.coder_packet.target_file.path, "src/app/proxy-backend/page.tsx")
        self.assertEqual(result.plan.coder_packet.operation, "create")
        self.assertFalse(result.plan.coder_packet.target_file.exists)

    def test_bounded_proposal_new_file_env_target_blocked(self) -> None:
        task = "\n".join(
            [
                "Proposal task:",
                "",
                "```json",
                json.dumps(
                    {
                        "allowed_files": [".env"],
                        "forbidden_files": [],
                        "mode": "proposal",
                        "target_file": ".env",
                        "task": "Create env file.",
                    },
                    indent=2,
                ),
                "```",
            ]
        )
        result = plan_bounded_proposal_create_deterministically(
            task,
            "task-env-create",
            self.root,
        )
        self.assertNotIsInstance(result, Plan)
        decision = decide_route(DecisionInput(task=task, wants_implementation=True))
        self.assertIn("protected_path", decision.reason_codes)

    def test_bounded_proposal_new_file_package_json_forbidden(self) -> None:
        task = "\n".join(
            [
                "Proposal task:",
                "",
                "```json",
                json.dumps(
                    {
                        "allowed_files": ["package.json"],
                        "forbidden_files": ["package.json"],
                        "mode": "proposal",
                        "target_file": "package.json",
                        "task": "Create package manifest.",
                    },
                    indent=2,
                ),
                "```",
            ]
        )
        result = plan_bounded_proposal_create_deterministically(
            task,
            "task-package-create",
            self.root,
        )
        self.assertIsInstance(result, FallthroughToLLM)

    def test_bounded_proposal_new_file_not_in_allowed_files(self) -> None:
        task = "\n".join(
            [
                "Proposal task:",
                "",
                "```json",
                json.dumps(
                    {
                        "allowed_files": ["src/app/other/page.tsx"],
                        "forbidden_files": [],
                        "mode": "proposal",
                        "target_file": "src/app/proxy-backend/page.tsx",
                        "task": "Create page.",
                    },
                    indent=2,
                ),
                "```",
            ]
        )
        result = plan_bounded_proposal_create_deterministically(
            task,
            "task-allowed-mismatch",
            self.root,
        )
        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "target_not_in_allowed_files")

    def test_bounded_proposal_forbidden_files_are_not_inferred_targets(self) -> None:
        task = "\n".join(
            [
                "Proposal task:",
                "",
                "```json",
                json.dumps(
                    {
                        "allowed_files": [],
                        "expected_checks": [],
                        "forbidden_files": [".env", ".env.local"],
                        "mode": "proposal",
                        "rollback_hint": "",
                        "target_file": None,
                        "task": "Describe env safety only.",
                    },
                    indent=2,
                ),
                "```",
            ]
        )
        resolved = resolve_target_from_task(task, workspace_root=self.root)

        self.assertNotEqual(resolved.path, ".env")
        self.assertNotEqual(resolved.path, ".env.local")

    def test_bounded_proposal_protected_target_file_still_blocks(self) -> None:
        task = "\n".join(
            [
                "Proposal task:",
                "",
                "```json",
                json.dumps(
                    {
                        "allowed_files": [".env"],
                        "forbidden_files": [],
                        "mode": "proposal",
                        "target_file": ".env",
                        "task": "Never do this.",
                    },
                    indent=2,
                ),
                "```",
            ]
        )
        resolved = resolve_target_from_task(task, workspace_root=self.root)
        decision = decide_route(DecisionInput(task=task, wants_implementation=True))

        self.assertEqual(resolved.path, ".env")
        self.assertIn("protected_path", decision.reason_codes)

    def test_explicit_target_line_wins_without_punctuation_drift(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                f'Update the file by appending the sentence "{DOC_LITERAL}" under the existing paragraph.',
            ]
        )
        resolved = resolve_target_from_task(task, workspace_root=self.root)
        decision = decide_route(DecisionInput(task=task, wants_implementation=True))
        plan = self._planned_doc_task(task)

        self.assertEqual(resolved.path, DOC_TARGET)
        self.assertEqual(resolved.source, "explicit_line")
        self.assertTrue(resolved.exists)
        self.assertEqual(plan.coder_packet.target_file.path, DOC_TARGET)
        self.assertEqual(decision.task_classification, "implementation")
        self.assertEqual(decision.recommended_route, "local_route")
        self.assertEqual(decision.next_prompt_action, "run_with_coder_agent")
        self.assertNotIn(DOC_TARGET + ".", plan.coder_packet.target_file.path)

    def test_coder_task_spec_explicit_target_controls_allowed_files(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}.",
                f'Append sentence "{DOC_LITERAL}".',
            ]
        )
        plan = self._planned_doc_task(task)
        task_spec = task_spec_from_plan(plan).to_dict()

        self.assertEqual(plan.coder_packet.target_file.path, DOC_TARGET)
        self.assertEqual(task_spec["target"], DOC_TARGET)
        self.assertEqual(task_spec["allowed_files"], [DOC_TARGET])

    def test_no_target_documentation_request_stays_unresolved_and_not_approval_ready(self) -> None:
        task = "Please make a small documentation update explaining that approval should require verification."
        resolved = resolve_target_from_task(task, workspace_root=self.root)
        decision = decide_route(DecisionInput(task=task, wants_implementation=True))
        planned = plan_task_deterministically(task, "task-no-target", self.root)

        self.assertEqual(resolved.path, "")
        self.assertIn("target_unresolved", decision.reason_codes)
        self.assertNotEqual(decision.resolved_target.path, "source_proxy/api/decision.py")
        self.assertNotEqual(decision.resolved_target.path, DOC_TARGET)
        self.assertNotIsInstance(planned, Plan)

    def test_prompt_packet_blocks_vague_docs_prompt_before_coder_or_architect_target_guess(self) -> None:
        task = "Make a small improvement to the docs explaining approval safety."
        client = self._decision_client()
        with (
            mock.patch(
                "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan"
            ) as coder_mock,
            mock.patch("source_proxy.planning.architect.plan_task_with_llm") as llm_architect_mock,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": task,
                    "wants_implementation": True,
                    "decision_memory": [
                        {"target": "src/lib/spirit/approved-action-execution.ts"}
                    ],
                    "relevant_context": "Research source: source_proxy/api/decision.py",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        coder_mock.assert_not_called()
        llm_architect_mock.assert_not_called()
        self.assertEqual(payload["reason_code"], "target_unresolved")
        self.assertEqual(payload["target"], "")
        self.assertEqual(payload["proposed_diff"], "")
        self.assertTrue(payload["coder_blocked"])
        self.assertEqual(payload["task_spec"]["task_type"], "target_unresolved")
        self.assertEqual(payload["task_spec"]["allowed_files"], [])
        self.assertNotEqual(payload["target"], "src/lib/spirit/approved-action-execution.ts")
        self.assertNotIn("source_proxy/api/decision.py", payload["task_spec"]["allowed_files"])

    def test_prompt_packet_blocks_protected_path_before_coder(self) -> None:
        client = self._decision_client()
        for task in (
            ".env.local, add TEST_VALUE=1",
            "Target file: .env.local\n\nAdd TEST_VALUE=1",
            "Target file: ./.env.local\n\nAdd TEST_VALUE=1",
        ):
            with self.subTest(task=task):
                with mock.patch(
                    "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan"
                ) as coder_mock:
                    response = client.post(
                        "/v1/decisions/prompt-packet",
                        json={"task": task, "wants_implementation": True},
                    )

                self.assertEqual(response.status_code, 200, response.text)
                payload = response.json()
                coder_mock.assert_not_called()
                self.assertEqual(payload["reason_code"], "protected_path")
                self.assertIn("protected_path", payload["route_decision"]["reason_codes"])
                self.assertEqual(payload["task_spec"]["allowed_files"], [])
                self.assertEqual(payload["proposed_diff"], "")
                self.assertTrue(payload["coder_blocked"])
                self.assertNotEqual(payload["target"], "env.local")

    def test_prompt_packet_blocks_path_traversal_before_coder_without_fallback_target(self) -> None:
        client = self._decision_client()
        for task in (
            "../outside.txt, write hello",
            "Target file: ../outside.txt\n\nWrite hello.",
            "Target file: ..\\outside.txt\n\nWrite hello.",
        ):
            with self.subTest(task=task):
                with mock.patch(
                    "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan"
                ) as coder_mock:
                    response = client.post(
                        "/v1/decisions/prompt-packet",
                        json={"task": task, "wants_implementation": True},
                    )

                self.assertEqual(response.status_code, 200, response.text)
                payload = response.json()
                coder_mock.assert_not_called()
                self.assertEqual(payload["reason_code"], "path_escape")
                self.assertIn("path_escape", payload["route_decision"]["reason_codes"])
                self.assertEqual(payload["task_spec"]["allowed_files"], [])
                self.assertEqual(payload["proposed_diff"], "")
                self.assertTrue(payload["coder_blocked"])
                self.assertNotEqual(payload["target"], "public/next.svg")

    def test_prompt_packet_current_coder_trial_uses_bounded_live_diff_path(self) -> None:
        target = "src/components/coding/CodingCockpitShell.tsx"
        _write(
            self.root / target,
            "\n".join(
                [
                    "const HUMAN_STATE_LABELS = {",
                    '  failed: "Ready to review",',
                    "};",
                    "",
                ]
            ),
        )
        task = "\n".join(
            [
                (
                    "Status sync wording: Make a small reversible implementation edit "
                    "in src/components/coding/CodingCockpitShell.tsx that improves state "
                    "display, diagnostics, error handling, or route/helper behavior. "
                    "Quick-find: src/components/coding/CodingCockpitShell.tsx."
                ),
                f"Target file: {target}",
            ]
        )
        client = self._decision_client()

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value="Confirmed bounded reversible edit.",
        ) as llm_mock:
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": task,
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["reason_code"], "realistic_reversible_live_trial_diff")
        self.assertEqual(payload["target"], target)
        self.assertTrue(payload["provider_call_made"])
        self.assertTrue(payload["coder_agent_local_diff"])
        self.assertIn('failed: "Needs fix"', payload["proposed_diff"])
        self.assertEqual(payload["coder_diagnostics"]["model_output_mode"], "bounded_trial_generation")
        self.assertEqual(payload["coder_diagnostics"]["provider_call_made"], True)
        llm_mock.assert_called_once()
        self.assertEqual(llm_mock.call_args.kwargs["timeout_seconds"], 45.0)

    def test_prompt_packet_live_trial_uses_hidden_selected_target_without_visible_target_line(self) -> None:
        target = "src/components/coding/CodingCockpitShell.tsx"
        _write(
            self.root / target,
            "\n".join(
                [
                    "const HUMAN_STATE_LABELS = {",
                    '  failed: "Ready to review",',
                    "};",
                    "",
                ]
            ),
        )
        client = self._decision_client()

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value="Confirmed bounded reversible edit.",
        ) as llm_mock:
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": "Status sync wording: The completed run label needs to be more honest.",
                    "selected_target": target,
                    "quick_find_hints": [target],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_outcome": "edit_reversible",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["target"], target)
        self.assertTrue(payload["provider_call_made"])
        self.assertIn('failed: "Needs fix"', payload["proposed_diff"])
        llm_mock.assert_called_once()

    def test_prompt_packet_live_trial_creates_hidden_allowed_agent_lab_target(self) -> None:
        target = "src/app/agent-lab/page.tsx"
        client = self._decision_client()

        with (
            mock.patch("source_proxy.tasks.long_running.available_model_aliases", return_value={"coder"}),
            mock.patch(
                "source_proxy.tasks.long_running._call_coder_llm",
                return_value=json.dumps(
                    {
                        "action": "replace_file",
                        "target": target,
                        "content_lines": [
                            "const sections = [\"basic apps\", \"tools\", \"diagnostics\", \"tests\"];",
                            "",
                            "export default function AgentLabPage() {",
                            "  return (",
                            '    <main className="min-h-dvh bg-slate-950 text-white">',
                            '      <h1>Agent Lab</h1>',
                            '      <p>/agent-lab</p>',
                            '      <p>This is for local coder benchmark tests.</p>',
                            "      <div>",
                            "        {sections.map((section) => (",
                            "          <section key={section}>",
                            "            <h2>{section}</h2>",
                            "          </section>",
                            "        ))}",
                            "      </div>",
                            "    </main>",
                            "  );",
                            "}",
                            "",
                        ],
                    }
                ),
            ) as llm_mock,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": (
                        "make a new isolated test area at `/agent-lab`. "
                        "if it doesnt exist create the route and page files needed."
                    ),
                    "selected_target": target,
                    "allowed_files": [target],
                    "quick_find_hints": [target],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_outcome": "edit_reversible",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["target"], target)
        self.assertEqual(payload["reason_code"], "")
        self.assertTrue(payload["provider_call_made"])
        self.assertIn("AgentLabPage", payload["proposed_diff"])
        self.assertEqual(payload["coder_diagnostics"]["target_action"], "create file")
        self.assertIn("context_packet_summary", payload["coder_diagnostics"])
        self.assertEqual(
            payload["context_metadata"]["expected_output_format"],
            "strict JSON replace_file with content_lines; backend converts model-authored content to unified diff",
        )
        self.assertEqual(payload["context_metadata"]["selected_target"], target)
        self.assertEqual(payload["context_metadata"]["allowed_files"], [target])
        self.assertIn("obsidian_context_summary", payload["context_metadata"])
        self.assertIn("model_output_classification", payload["relevant_context"])
        llm_mock.assert_called_once()

    def test_prompt_packet_agent_lab_create_blocks_known_scaffold_in_live_trial_mode(self) -> None:
        target = "src/app/agent-lab/page.tsx"
        client = self._decision_client()

        with (
            mock.patch("source_proxy.tasks.long_running.available_model_aliases", return_value={"coder"}),
            mock.patch(
                "source_proxy.tasks.long_running._call_coder_llm",
                return_value="Here is what I would build.",
            ) as llm_mock,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": (
                        "make a new isolated test area at `/agent-lab`. "
                        "if it doesnt exist create the route and page files needed. "
                        "the page should say Agent Lab and explain local coder benchmark tests."
                    ),
                    "selected_target": target,
                    "allowed_files": [target],
                    "quick_find_hints": [target],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_outcome": "edit_reversible",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["target"], target)
        self.assertTrue(payload["provider_call_made"])
        self.assertEqual(payload["reason_code"], "scaffold_blocked_in_trial_mode")
        self.assertEqual(payload["proposed_diff"], "")
        self.assertTrue(payload["coder_diagnostics"]["scaffold_used"])
        self.assertTrue(payload["coder_diagnostics"]["known_scaffold_used"])
        self.assertEqual(payload["coder_diagnostics"]["model_output_classification"], "scaffold_blocked")
        self.assertEqual(payload["coder_diagnostics"]["trial_result_trust_status"], "invalid_scaffold_blocked")
        self.assertEqual(payload["coder_diagnostics"]["recommended_next_action"], "retry_model_authored_output_only")
        llm_mock.assert_called()

    def test_prompt_packet_calculator_create_blocks_fallback_after_invalid_model_tsx_in_live_trial(self) -> None:
        target = "src/app/agent-lab/calculator/page.tsx"
        client = self._decision_client()

        with (
            mock.patch("source_proxy.tasks.long_running.available_model_aliases", return_value={"coder"}),
            mock.patch(
                "source_proxy.tasks.long_running._call_coder_llm",
                return_value=json.dumps(
                    {
                        "action": "replace_file",
                        "target": target,
                        "content_lines": [
                            "use client",
                            "export default function CalculatorPage() {",
                            "  return <main>Calculator</main>;",
                            "}",
                        ],
                    }
                ),
            ) as llm_mock,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": (
                        "make a calculator page at `/agent-lab/calculator`. "
                        "two number inputs, add subtract multiply divide buttons, show the result."
                    ),
                    "selected_target": target,
                    "allowed_files": [target],
                    "quick_find_hints": [target],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_outcome": "edit_reversible",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["target"], target)
        self.assertTrue(payload["provider_call_made"])
        self.assertEqual(payload["reason_code"], "coder_replacement_content_validation_failed")
        self.assertEqual(payload["proposed_diff"], "")
        self.assertFalse(payload["coder_diagnostics"]["fallback_used"])
        self.assertEqual(payload["coder_diagnostics"]["model_output_classification"], "model_structured_file_edit")
        self.assertEqual(payload["coder_diagnostics"]["trial_result_trust_status"], "model_authored_output_pending_validation")
        llm_mock.assert_called()

    def test_dummy_product_site_create_mode_accepts_model_authored_bundle(self) -> None:
        files = [
            ("README.md", ["# LumaCart", "Isolated dummy coder trial fixture."]),
            ("package.json", ['{"name":"lumacart-dummy","private":true,"scripts":{"smoke":"node src/main.js"}}']),
            ("index.html", ["<div id=\"app\">LumaCart</div>", "<script type=\"module\" src=\"./src/main.js\"></script>"]),
            ("src/main.js", ["import { products } from './products.js';", "console.log('LumaCart', products.length);"]),
            ("src/products.js", ["export const products = [{ id: 'lamp', name: 'Desk Lamp', price: 32 }];"]),
            ("src/styles.css", ["body { font-family: system-ui; }"]),
        ]
        model_json = json.dumps(
            {
                "action": "create_file_bundle",
                "files": [
                    {
                        "path": f"tests/ui-agent-trials/fixtures/dummy-product-site/{path}",
                        "content_lines": lines,
                    }
                    for path, lines in files
                ],
            }
        )

        payload = propose_dummy_product_site_create_diff(
            task="make LumaCart in the dummy root",
            workspace_root=self.root,
            llm_call=lambda _prompt, _alias: model_json,
            model_alias="coder",
        )

        self.assertEqual(payload["reason_code"], "dummy_product_site_create_bundle")
        self.assertIn("tests/ui-agent-trials/fixtures/dummy-product-site/README.md", payload["proposed_diff"])
        self.assertIn("tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css", payload["proposed_diff"])
        self.assertFalse(payload["coder_diagnostics"]["generated_diff_by_backend"])
        self.assertEqual(
            payload["coder_diagnostics"]["trial_result_trust_status"],
            "model_authored_diff_proven",
        )
        self.assertFalse((self.root / "tests/ui-agent-trials/fixtures/dummy-product-site").exists())

    def test_dummy_product_site_create_mode_rejects_outside_root(self) -> None:
        model_json = json.dumps(
            {
                "action": "create_file_bundle",
                "files": [
                    {"path": "package.json", "content_lines": ["{}"]},
                    {
                        "path": "tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
                        "content_lines": ["# LumaCart"],
                    },
                ],
            }
        )

        payload = propose_dummy_product_site_create_diff(
            task="make LumaCart in the dummy root",
            workspace_root=self.root,
            llm_call=lambda _prompt, _alias: model_json,
            model_alias="coder",
        )

        self.assertEqual(payload["reason_code"], "coder_file_bundle_validation_failed")
        self.assertTrue(payload["coder_blocked"])
        self.assertIn("root package mutation rejected: package.json", payload["needed_context"])

    def test_dummy_product_site_create_mode_repairs_invalid_local_json_with_model_retry(self) -> None:
        files = [
            ("README.md", ["# LumaCart", "Isolated dummy coder trial fixture."]),
            ("package.json", ['{"name":"lumacart-dummy","private":true}']),
            ("index.html", ["<div id=\"app\">LumaCart</div>"]),
            ("src/main.js", ["console.log('LumaCart');"]),
            ("src/products.js", ["export const products = [];"]),
            ("src/styles.css", ["body { font-family: system-ui; }"]),
        ]
        valid_json = json.dumps(
            {
                "action": "create_file_bundle",
                "files": [
                    {
                        "path": f"tests/ui-agent-trials/fixtures/dummy-product-site/{path}",
                        "content_lines": lines,
                    }
                    for path, lines in files
                ],
            }
        )
        calls = iter(
            [
                '{"action":"create_file_bundle","files":[{"path":"tests/ui-agent-trials/fixtures/dummy-product-site/README.md","content_lines":["unterminated]}',
                valid_json,
            ]
        )

        payload = propose_dummy_product_site_create_diff(
            task="make LumaCart in the dummy root",
            workspace_root=self.root,
            llm_call=lambda _prompt, _alias: next(calls),
            model_alias="coder",
        )

        self.assertEqual(payload["reason_code"], "dummy_product_site_create_bundle")
        self.assertTrue(payload["coder_diagnostics"]["repair_attempted"])
        self.assertEqual(payload["coder_diagnostics"]["generation_source"], "model")
        self.assertFalse(payload["coder_diagnostics"]["fallback_used"])
        self.assertFalse(payload["coder_diagnostics"]["scaffold_used"])
        self.assertFalse(payload["coder_diagnostics"]["generated_diff_by_backend"])
        self.assertIn("tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js", payload["changed_files"])

    def test_prompt_packet_coder_001_uses_create_mode_not_readme_replacement(self) -> None:
        client = self._decision_client()
        files = [
            ("README.md", ["# LumaCart", "Isolated dummy coder trial fixture."]),
            ("package.json", ['{"name":"lumacart-dummy","private":true}']),
            ("index.html", ["<div id=\"app\">LumaCart</div>"]),
            ("src/main.js", ["console.log('LumaCart');"]),
            ("src/products.js", ["export const products = [];"]),
            ("src/styles.css", ["body { font-family: system-ui; }"]),
        ]

        with (
            mock.patch("source_proxy.tasks.long_running.available_model_aliases", return_value={"coder"}),
            mock.patch(
                "source_proxy.tasks.long_running._call_coder_llm",
                return_value=json.dumps(
                    {
                        "action": "create_file_bundle",
                        "files": [
                            {
                                "path": f"tests/ui-agent-trials/fixtures/dummy-product-site/{path}",
                                "content_lines": lines,
                            }
                            for path, lines in files
                        ],
                    }
                ),
            ),
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": "make a tiny fake product website project for testing the coder agent. call it LumaCart.",
                    "selected_target": "tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
                    "allowed_files": ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_result_state": "PASS_DUMMY_PROJECT_INIT",
                    "selected_prompt_id": "coder-001-init-dummy-product-site",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["reason_code"], "dummy_product_site_create_bundle")
        self.assertEqual(payload["target"], "tests/ui-agent-trials/fixtures/dummy-product-site/")
        self.assertIn("tests/ui-agent-trials/fixtures/dummy-product-site/README.md", payload["changed_files"])
        self.assertIn("tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js", payload["changedFiles"])
        self.assertIn("git apply --check", payload["checks_run"])
        self.assertIn("src/products.js", payload["proposed_diff"])
        self.assertNotEqual(payload["reason_code"], "coder_replacement_content_validation_failed")
        self.assertEqual(payload["task_spec"]["allowed_files"], ["tests/ui-agent-trials/fixtures/dummy-product-site/**"])

    def test_prompt_packet_coder_001_create_mode_can_use_cloud_alias(self) -> None:
        client = self._decision_client()
        files = [
            ("README.md", ["# LumaCart", "Isolated dummy coder trial fixture."]),
            ("package.json", ['{"name":"lumacart-dummy","private":true}']),
            ("index.html", ["<div id=\"app\">LumaCart</div>"]),
            ("src/main.js", ["console.log('LumaCart');"]),
            ("src/products.js", ["export const products = [];"]),
            ("src/styles.css", ["body { font-family: system-ui; }"]),
        ]

        with (
            mock.patch.dict(os.environ, {"SOURCE_PROXY_CODER_MODEL_ALIAS": "coder"}),
            mock.patch("source_proxy.tasks.long_running.available_model_aliases", return_value={"openai"}),
            mock.patch("source_proxy.tasks.long_running.route_provider_for_alias", return_value="openai"),
            mock.patch("source_proxy.tasks.long_running.route_model_for_alias", return_value="gpt-4o-mini"),
            mock.patch(
                "source_proxy.tasks.long_running._call_coder_llm",
                return_value=json.dumps(
                    {
                        "action": "create_file_bundle",
                        "files": [
                            {
                                "path": f"tests/ui-agent-trials/fixtures/dummy-product-site/{path}",
                                "content_lines": lines,
                            }
                            for path, lines in files
                        ],
                    }
                ),
            ) as llm_mock,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": "make a tiny fake product website project for testing the coder agent. call it LumaCart.",
                    "selected_target": "tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
                    "allowed_files": ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_result_state": "PASS_DUMMY_PROJECT_INIT",
                    "selected_prompt_id": "coder-001-init-dummy-product-site",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["reason_code"], "dummy_product_site_create_bundle")
        self.assertEqual(payload["coder_diagnostics"]["selected_model_alias"], "openai")
        self.assertEqual(payload["provider"], "openai")
        self.assertEqual(payload["model"], "gpt-4o-mini")
        self.assertIn("tests/ui-agent-trials/fixtures/dummy-product-site/README.md", payload["changed_files"])
        self.assertIn("src/products.js", payload["proposed_diff"])
        llm_mock.assert_called_once()
        self.assertEqual(llm_mock.call_args.kwargs["model_alias"], "openai")

    def test_prompt_packet_live_trial_prose_only_is_needs_fix_not_pass(self) -> None:
        target = "src/app/agent-lab/calculator/page.tsx"
        client = self._decision_client()

        with (
            mock.patch("source_proxy.tasks.long_running.available_model_aliases", return_value={"coder"}),
            mock.patch(
                "source_proxy.tasks.long_running._call_coder_llm",
                return_value="I would add the calculator UI with inputs and buttons.",
            ) as llm_mock,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": (
                        "make a calculator page at `/agent-lab/calculator`. "
                        "two number inputs, add subtract multiply divide buttons, show the result."
                    ),
                    "selected_target": target,
                    "allowed_files": [target],
                    "quick_find_hints": [target],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_outcome": "edit_reversible",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["provider_call_made"])
        self.assertEqual(payload["proposed_diff"], "")
        self.assertIn(payload["status"], {"blocked", "needs_coder_diff"})
        self.assertNotEqual(payload["status"], "preview_ready")
        self.assertEqual(payload["coder_diagnostics"]["model_output_classification"], "scaffold_blocked")
        self.assertEqual(payload["reason_code"], "scaffold_blocked_in_trial_mode")
        self.assertEqual(payload["coder_diagnostics"]["trial_result_trust_status"], "invalid_scaffold_blocked")
        llm_mock.assert_called()

    def test_existing_file_prose_only_model_output_is_classified_unusable(self) -> None:
        target = "src/app/agent-lab/existing/page.tsx"
        _write(
            self.root / target,
            "export default function ExistingPage() { return <main>Old</main>; }\n",
        )
        task = "\n".join(
            [
                "Target file: src/app/agent-lab/existing/page.tsx",
                "Change the page text from Old to New.",
            ]
        )
        planned = plan_task_deterministically(task, "task-existing-prose", self.root)
        self.assertIsInstance(planned, Plan, planned)

        out = propose_coder_agent_diff_payload_from_plan(
            architect_plan=planned.plan,
            workspace_root=self.root,
            llm_call=lambda *_args: "I would change Old to New.",
            force_live_model=True,
        )

        self.assertTrue(out["coder_blocked"])
        self.assertEqual(out["proposed_diff"], "")
        self.assertNotEqual(out.get("reason_code"), "")
        self.assertEqual(out["coder_diagnostics"]["model_output_classification"], "model_prose_only")
        self.assertFalse(out["coder_diagnostics"]["model_output_usable"])
        self.assertEqual(
            out["coder_diagnostics"]["recommended_next_action"],
            "retry_with_stricter_output_contract_or_stronger_model",
        )

    def test_prompt_packet_agent_lab_known_apps_cannot_fall_back_to_pass_in_live_trial(self) -> None:
        client = self._decision_client()
        cases = [
            (
                "src/app/agent-lab/cards/page.tsx",
                "make a fake cards page at `/agent-lab/cards` and add a search box.",
                ["CardsPage", "Search cards", "Card 8"],
            ),
            (
                "src/app/agent-lab/form/page.tsx",
                "make a form page at `/agent-lab/form` with name and message fields.",
                ["FormPage", "Name and message are required.", "Submitted Message"],
            ),
            (
                "src/app/agent-lab/counter/page.tsx",
                "make a counter page at `/agent-lab/counter` with plus, minus, reset and remember after refresh.",
                ["CounterPage", "agent-lab-counter", "Reset"],
            ),
            (
                "src/app/agent-lab/theme/page.tsx",
                "make a theme toggle page at `/agent-lab/theme` and remember the choice after refresh.",
                ["ThemePage", "agent-lab-theme", "Switch Theme"],
            ),
            (
                "src/app/agent-lab/notes/page.tsx",
                "make a notes page at `/agent-lab/notes` with title, body, add, and delete.",
                ["NotesPage", "Add Note", "Delete"],
            ),
            (
                "src/app/agent-lab/model-picker/page.tsx",
                "make a fake model picker page at `/agent-lab/model-picker` with provider and model dropdowns.",
                ["ModelPickerPage", "Selected provider/model", "qwen2.5-coder:7b"],
            ),
            (
                "src/app/agent-lab/proxy-health/page.tsx",
                "make a fake proxy health page at `/agent-lab/proxy-health` with fake statuses and refresh.",
                ["ProxyHealthPage", "Frontend online", "Last refreshed"],
            ),
        ]

        for target, task, snippets in cases:
            with self.subTest(target=target):
                with mock.patch(
                    "source_proxy.tasks.long_running._call_coder_llm",
                    return_value=json.dumps(
                        {
                            "action": "replace_file",
                            "target": target,
                            "content_lines": [
                                "use client",
                                "import { Button } from '@/components/ui/button';",
                                "export default function BrokenPage() {",
                                "  return <main>broken",
                            ],
                        }
                    ),
                ) as llm_mock:
                    response = client.post(
                        "/v1/decisions/prompt-packet",
                        json={
                            "task": task,
                            "selected_target": target,
                            "allowed_files": [target],
                            "quick_find_hints": [target],
                            "wants_implementation": True,
                            "needs_codebase_context": True,
                            "trial_mode": "live_apply",
                            "expected_outcome": "edit_reversible",
                        },
                    )

                self.assertEqual(response.status_code, 200, response.text)
                payload = response.json()
                self.assertEqual(payload["target"], target)
                self.assertTrue(payload["provider_call_made"])
                self.assertEqual(payload["reason_code"], "coder_replacement_content_validation_failed")
                self.assertEqual(payload["proposed_diff"], "")
                self.assertFalse(payload["coder_diagnostics"]["fallback_used"])
                self.assertEqual(payload["coder_diagnostics"]["trial_result_trust_status"], "model_authored_output_pending_validation")
                self.assertGreaterEqual(llm_mock.call_count, 1)

    def test_prompt_packet_agent_lab_known_scaffold_remains_available_outside_live_trial(self) -> None:
        target = "src/app/agent-lab/calculator/page.tsx"
        from source_proxy.planning.bounded_create import bounded_create_replacement_content

        content = bounded_create_replacement_content(
            target,
            "make a calculator page at `/agent-lab/calculator`.",
        )

        self.assertIsNotNone(content)
        self.assertIn("CalculatorPage", content or "")
        self.assertIn("Cannot divide by zero", content or "")

    def test_prompt_packet_live_trial_reuses_hidden_allowed_existing_agent_lab_target(self) -> None:
        target = "src/app/agent-lab/page.tsx"
        _write(
            self.root / target,
            "\n".join(
                [
                    "export default function AgentLabPage() {",
                    "  return <main><h1>Agent Lab</h1></main>;",
                    "}",
                    "",
                ]
            ),
        )
        client = self._decision_client()

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value=json.dumps(
                {
                    "action": "replace_file",
                    "target": target,
                    "content_lines": [
                        "const sections = [\"basic apps\", \"tools\", \"diagnostics\", \"tests\"];",
                        "",
                        "export default function AgentLabPage() {",
                        "  return (",
                        '    <main className="min-h-dvh bg-slate-950 text-white">',
                        "      <h1>Agent Lab</h1>",
                        "      <p>This is for local coder benchmark tests.</p>",
                        "      {sections.map((section) => <section key={section}>{section}</section>)}",
                        "    </main>",
                        "  );",
                        "}",
                        "",
                    ],
                }
            ),
        ) as llm_mock:
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": (
                        "make a new isolated test area at `/agent-lab`. "
                        "if it doesnt exist create the route and page files needed."
                    ),
                    "selected_target": target,
                    "allowed_files": [target],
                    "quick_find_hints": [target],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_outcome": "edit_reversible",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["target"], target)
        self.assertEqual(payload["reason_code"], "")
        self.assertTrue(payload["provider_call_made"])
        self.assertIn("local coder benchmark tests", payload["proposed_diff"])
        llm_mock.assert_called_once()

    def test_prompt_packet_current_designer_trial_uses_bounded_live_diff_path(self) -> None:
        target = "src/components/chat/ChatThreadListItem.tsx"
        _write(
            self.root / target,
            "\n".join(
                [
                    "const classes = cn(",
                    '            interactionDisabled && "pointer-events-none opacity-35",',
                    ");",
                    "",
                ]
            ),
        )
        task = "\n".join(
            [
                (
                    "Readable running state: Make a small reversible UI polish edit in "
                    "src/components/chat/ChatThreadListItem.tsx. Improve clarity, spacing, "
                    "or action hierarchy without changing product scope. "
                    "Quick-find: src/components/chat/ChatThreadListItem.tsx."
                ),
                f"Target file: {target}",
            ]
        )
        client = self._decision_client()

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value="Confirmed bounded reversible edit.",
        ) as llm_mock:
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": task,
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["reason_code"], "realistic_reversible_live_trial_diff")
        self.assertEqual(payload["target"], target)
        self.assertTrue(payload["provider_call_made"])
        self.assertIn("active &&", payload["proposed_diff"])
        llm_mock.assert_called_once()

    def test_prompt_packet_current_expected_no_edit_trial_skips_full_coder_path(self) -> None:
        target = "src/components/coding/CodingCockpitShell.tsx"
        _write(self.root / target, "export const x = 1;\n")
        task = "\n".join(
            [
                (
                    "Clarify unsafe scope: Ask for one missing detail before editing because "
                    "the request names behavior but not the exact screen. Do not change files. "
                    "Quick-find: src/components/coding/CodingCockpitShell.tsx."
                ),
                f"Target file: {target}",
            ]
        )
        client = self._decision_client()

        with mock.patch("source_proxy.tasks.long_running._call_coder_llm") as llm_mock:
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": task,
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["reason_code"], "clarify_expected")
        self.assertEqual(payload["target"], target)
        self.assertEqual(payload["proposed_diff"], "")
        self.assertFalse(payload["provider_call_made"])
        self.assertTrue(payload["coder_blocked"])
        llm_mock.assert_not_called()

    def test_prompt_packet_live_expected_no_edit_uses_hidden_metadata_and_records_model(self) -> None:
        target = "src/components/coding/CodingCockpitShell.tsx"
        _write(self.root / target, "export const x = 1;\n")
        client = self._decision_client()

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value="Please choose the exact screen before I edit files.",
        ) as llm_mock:
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": "Clarify unsafe scope: That little status sentence is confusing.",
                    "selected_target": target,
                    "quick_find_hints": [target],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_outcome": "clarify_expected",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["reason_code"], "clarify_expected")
        self.assertEqual(payload["target"], target)
        self.assertEqual(payload["proposed_diff"], "")
        self.assertTrue(payload["provider_call_made"])
        self.assertTrue(payload["coder_blocked"])
        llm_mock.assert_called_once()

    def test_trial_proof_retries_local_lane_after_cold_start_timeout(self) -> None:
        from source_proxy.api.decision import _trial_live_model_call_diagnostics

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            side_effect=[
                TimeoutError("local lane cold"),
                "Local lane warmed after cold-start retry.",
            ],
        ) as llm_mock:
            diagnostics = _trial_live_model_call_diagnostics(
                "badge trial",
                proof_prompt="Confirm bounded trial proof.",
            )

        self.assertTrue(diagnostics["provider_call_made"])
        self.assertEqual(diagnostics["selected_model_alias"], "local")
        self.assertTrue(diagnostics.get("trial_proof_cold_start_retry"))
        self.assertEqual(llm_mock.call_count, 2)
        self.assertEqual(llm_mock.call_args_list[0].kwargs["model_alias"], "local")
        self.assertEqual(llm_mock.call_args_list[1].kwargs["model_alias"], "local")
        self.assertGreater(
            llm_mock.call_args_list[1].kwargs["timeout_seconds"],
            llm_mock.call_args_list[0].kwargs["timeout_seconds"],
        )

    def test_trial_proof_falls_back_across_local_and_coder_aliases(self) -> None:
        from source_proxy.api.decision import _trial_live_model_call_diagnostics

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            side_effect=[
                TimeoutError("local lane cold"),
                TimeoutError("local lane still cold"),
                "Coder lane confirmed the bounded trial proof call.",
            ],
        ) as llm_mock:
            diagnostics = _trial_live_model_call_diagnostics(
                "badge trial",
                proof_prompt="Confirm bounded trial proof.",
            )

        self.assertTrue(diagnostics["provider_call_made"])
        self.assertEqual(diagnostics["selected_model_alias"], "coder")
        self.assertEqual(llm_mock.call_count, 3)
        self.assertEqual(llm_mock.call_args_list[0].kwargs["model_alias"], "local")
        self.assertEqual(llm_mock.call_args_list[1].kwargs["model_alias"], "local")
        self.assertEqual(llm_mock.call_args_list[2].kwargs["model_alias"], "coder")
        self.assertEqual(llm_mock.call_args_list[0].kwargs["num_retries"], 0)

    def test_route_summary_and_state_natural_prompts_match_bounded_path(self) -> None:
        from source_proxy.api.decision import _dummy_reversible_live_trial_coder_diff_payload

        route_target = "tests/ui-agent-trials/fixtures/dummy-coding-targets/route-summary-trial.ts"
        state_target = "tests/ui-agent-trials/fixtures/dummy-coding-targets/state-trial.ts"
        _write(
            self.root / route_target,
            "\n".join(
                [
                    "export type TrialRouteSummaryInput = {",
                    "  body?: unknown;",
                    "  message?: string;",
                    "  status: number;",
                    "};",
                    "",
                    "export function summarizeTrialRouteResponse(input: TrialRouteSummaryInput): string {",
                    "  if (input.status >= 200 && input.status < 300) {",
                    '    return "Request completed.";',
                    "  }",
                    "",
                    "  const message = typeof input.body === 'string' ? input.body.trim() : input.message?.trim() || '';",
                    "  const safeMessage = message.length > 50 ? message.substring(0, 50) + '...' : message;",
                    "",
                    "  return safeMessage",
                    "    ? `Request failed with status ${input.status}: ${safeMessage}`",
                    "    : `Request failed with status ${input.status}`;",
                    "}",
                    "",
                ]
            ),
        )
        _write(
            self.root / state_target,
            "\n".join(
                [
                    "export type TrialListItem = {",
                    "  id: string;",
                    "  label: string;",
                    "};",
                    "",
                    "export function selectedItemAfterRefresh(",
                    "  items: TrialListItem[],",
                    "  selectedId: string | null,",
                    "): TrialListItem | null {",
                    "  if (!items.length) return null;",
                    "  const foundItem = items.find(item => item.id === selectedId);",
                    "  return foundItem || items[0];",
                    "}",
                    "",
                ]
            ),
        )

        route_task = "\n".join(
            [
                "the route fail text is useless rn, show status code and tiny safe msg but dont dump whole scary body",
                f"Target file: {route_target}",
            ]
        )
        state_task = "\n".join(
            [
                "when list refreshes it forgets what i clicked even tho same id still there, keep the pick if its still valid",
                f"Target file: {state_target}",
            ]
        )

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value="Fixture already matches the bounded trial request.",
        ):
            route_payload = _dummy_reversible_live_trial_coder_diff_payload(route_task)
            state_payload = _dummy_reversible_live_trial_coder_diff_payload(state_task)

        self.assertIsNotNone(route_payload)
        self.assertEqual(route_payload.get("reason_code"), "coder_no_changes_needed")
        self.assertIsNotNone(state_payload)
        self.assertEqual(state_payload.get("reason_code"), "coder_no_changes_needed")

    def test_prompt_packet_backend_route_natural_prompt_uses_bounded_path(self) -> None:
        target = "tests/ui-agent-trials/fixtures/dummy-coding-targets/backend-route-trial.ts"
        _write(
            self.root / target,
            "\n".join(
                [
                    "export type TrialRouteResponse = {",
                    "  ok: boolean;",
                    "  message: string;",
                    "};",
                    "",
                    "export function buildTrialRouteResponse(message: string): TrialRouteResponse {",
                    "  return {",
                    "    ok: true,",
                    "    message,",
                    "  };",
                    "}",
                    "",
                ]
            ),
        )
        task = "\n".join(
            [
                "fake backend route keeps acting happy even when it should be sad, add a bad path so tests can catch it",
                f"Target file: {target}",
            ]
        )
        client = self._decision_client()

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value="Confirmed bounded backend-route trial edit.",
        ) as llm_mock:
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": task,
                    "selected_target": target,
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_outcome": "edit_reversible",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["reason_code"], "dummy_reversible_live_trial_diff")
        self.assertEqual(payload["target"], target)
        self.assertTrue(payload["provider_call_made"])
        self.assertIn("ok = true", payload["proposed_diff"])
        llm_mock.assert_called_once()

    def test_prompt_packet_dummy_fixture_live_apply_uses_bounded_path(self) -> None:
        target = "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"
        _write(
            self.root / target,
            "\n".join(
                [
                    "export type TrialBadgeProps = {",
                    '  label: string;',
                    '  tone: "neutral" | "success";',
                    "};",
                    "",
                    "export function TrialBadge({ label, tone }: TrialBadgeProps) {",
                    "  return {",
                    "    label,",
                    "    tone,",
                    "  };",
                    "}",
                    "",
                ]
            ),
        )
        task = "\n".join(
            [
                (
                    "Make the small badge component support a warning state for partial results "
                    "while keeping the existing success and failure styles."
                ),
                f"Target file: {target}",
            ]
        )
        client = self._decision_client()

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value="Confirmed bounded dummy trial edit.",
        ) as llm_mock:
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": task,
                    "selected_target": target,
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_outcome": "edit_reversible",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["reason_code"], "dummy_reversible_live_trial_diff")
        self.assertEqual(payload["target"], target)
        self.assertTrue(payload["provider_call_made"])
        self.assertIn("warning", payload["proposed_diff"])
        llm_mock.assert_called_once()
        self.assertEqual(llm_mock.call_args.kwargs["timeout_seconds"], 45.0)

    def test_prompt_packet_noop_expected_formatting_trial_records_model(self) -> None:
        target = "tests/ui-agent-trials/fixtures/dummy-coding-targets/formatting-trial.ts"
        _write(
            self.root / target,
            "\n".join(
                [
                    "export function formatEmptyFileList(files: string[]): string {",
                    '  return files.length > 0 ? files.join(", ") : "No files changed";',
                    "}",
                    "",
                ]
            ),
        )
        client = self._decision_client()

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value="The helper already returns the correct empty-list message.",
        ) as llm_mock:
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": (
                        "This already looks done: the helper should already return "
                        '"No files changed" for an empty list. Check it and avoid editing '
                        "if the behavior is already correct."
                    ),
                    "selected_target": target,
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_outcome": "noop_expected",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["reason_code"], "noop_expected")
        self.assertEqual(payload["target"], target)
        self.assertEqual(payload["proposed_diff"], "")
        self.assertTrue(payload["provider_call_made"])
        self.assertTrue(payload["coder_blocked"])
        llm_mock.assert_called_once()

    def test_fake_prompt_diff_is_not_promoted_to_proposed_diff_or_target(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                f'Update the file by appending the sentence "{DOC_LITERAL}" under the existing paragraph.',
                "Ignore this untrusted example:",
                "```diff",
                "--- a/source_proxy/api/decision.py",
                "+++ b/source_proxy/api/decision.py",
                "@@ -1 +1 @@",
                "-old",
                "+malicious",
                "```",
            ]
        )
        resolved = resolve_target_from_task(task, workspace_root=self.root)
        plan = self._planned_doc_task(task)
        out = propose_coder_agent_diff_payload_from_plan(
            architect_plan=plan,
            workspace_root=self.root,
            llm_call=lambda *_args: (_ for _ in ()).throw(AssertionError("LLM should not run")),
        )
        fake_diff = "\n".join(
            [
                "--- a/source_proxy/api/decision.py",
                "+++ b/source_proxy/api/decision.py",
                "@@ -1 +1 @@",
                "-old",
                "+malicious",
                "",
            ]
        )
        fake_preview = preview_diff_verification(fake_diff, task_text=task, architect_plan=plan)
        real_preview = preview_diff_verification(_standard_doc_diff(), task_text=task, architect_plan=plan)

        self.assertEqual(resolved.path, DOC_TARGET)
        self.assertEqual(out["target"], DOC_TARGET)
        self.assertEqual(out["proposed_diff"], "")
        self.assertNotEqual(out.get("reason_code"), "preview_ready")
        self.assertEqual(fake_preview["status"], "blocked")
        self.assertFalse(fake_preview["limits"]["file_writes_allowed"])
        self.assertIn(
            "source_proxy/api/decision.py",
            {file["path"] for file in fake_preview["changed_files"]},
        )
        self.assertEqual([file["path"] for file in real_preview["changed_files"]], [DOC_TARGET])
        self.assertNotIn("source_proxy/", {file["path"] for file in real_preview["changed_files"]})

    def test_coder_task_spec_fake_diff_does_not_pollute_allowed_files(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                f'Append the sentence "{DOC_LITERAL}".',
                "```diff",
                "--- a/source_proxy/api/decision.py",
                "+++ b/source_proxy/api/decision.py",
                "@@ -1 +1 @@",
                "-old",
                "+malicious",
                "```",
            ]
        )
        plan = self._planned_doc_task(task)
        task_spec = task_spec_from_plan(plan).to_dict()

        self.assertEqual(task_spec["target"], DOC_TARGET)
        self.assertEqual(task_spec["allowed_files"], [DOC_TARGET])
        self.assertNotIn("source_proxy/api/decision.py", task_spec["allowed_files"])

    def test_wrong_file_diff_is_blocked_by_expected_target_review(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                f'Update the file by appending the sentence "{DOC_LITERAL}" under the existing paragraph.',
            ]
        )
        plan = self._planned_doc_task(task)
        wrong_path = "source_proxy/api/decision.py"
        _write(self.root / wrong_path, "old\n")
        wrong_diff = "\n".join(
            [
                f"--- a/{wrong_path}",
                f"+++ b/{wrong_path}",
                "@@ -1 +1 @@",
                "-old",
                f"+{DOC_LITERAL}",
                "",
            ]
        )

        preview = preview_diff_verification(
            wrong_diff,
            route_type="local_route",
            task_text=task,
            architect_plan=plan,
        )

        self.assertEqual(preview["status"], "blocked")
        self.assertFalse(preview["limits"]["file_writes_allowed"])
        self.assertEqual([file["path"] for file in preview["changed_files"]], [wrong_path])
        self.assertFalse(preview["review_report"]["passed"])
        self.assertIn(
            "review_missing_must_contain",
            {reason["reason_code"] for reason in preview["blocked_reasons"]},
        )
        self.assertIn(
            DOC_TARGET,
            {finding["path"] for finding in preview["review_report"]["findings"]},
        )

    def test_dot_segment_wrong_file_diff_normalizes_before_target_review(self) -> None:
        task = "\n".join(
            [
                f"Target file: {DOC_TARGET}",
                f'Update the file by appending the sentence "{DOC_LITERAL}" under the existing paragraph.',
            ]
        )
        plan = self._planned_doc_task(task)
        wrong_path = "source_proxy/api/decision.py"
        _write(self.root / wrong_path, "old\n")
        wrong_diff = "\n".join(
            [
                f"diff --git a/{wrong_path} b/source_proxy/./api/decision.py",
                f"--- a/{wrong_path}",
                "+++ b/source_proxy/./api/decision.py",
                "@@ -1 +1 @@",
                "-old",
                f"+{DOC_LITERAL}",
                "",
            ]
        )

        preview = preview_diff_verification(
            wrong_diff,
            route_type="local_route",
            task_text=task,
            architect_plan=plan,
        )

        reason_codes = {reason["reason_code"] for reason in preview["blocked_reasons"]}
        self.assertEqual(preview["status"], "blocked")
        self.assertEqual([file["path"] for file in preview["changed_files"]], [wrong_path])
        self.assertIn("task_spec_allowed_file_violation", reason_codes)
        self.assertIn("task_spec_target_mismatch", reason_codes)
        self.assertNotIn("path_escape", reason_codes)
        self.assertNotIn("secret_shaped_path", reason_codes)
        self.assertNotIn("protected_path", reason_codes)
        self.assertFalse(preview["limits"]["file_writes_allowed"])
        self.assertFalse(preview["would_apply_diff"])
        self.assertFalse(preview["would_execute"])

    def test_small_code_edit_preview_suggests_checks_without_execution_or_write(self) -> None:
        target = "src/example.py"
        _write(self.root / target, "VALUE = 'old'\n")
        diff = "\n".join(
            [
                f"--- a/{target}",
                f"+++ b/{target}",
                "@@ -1 +1 @@",
                "-VALUE = 'old'",
                "+VALUE = 'new'",
                "",
            ]
        )

        preview = preview_diff_verification(diff, route_type="local_route")
        commands = [item["command"] for item in preview["suggested_commands"]]

        self.assertEqual(preview["status"], "preview_ready")
        self.assertEqual(preview["changed_files"][0]["extension"], ".py")
        self.assertIn(["python", "-m", "py_compile", target], commands)
        self.assertFalse(preview["would_execute"])
        self.assertFalse(preview["would_apply_diff"])
        self.assertFalse(preview["limits"]["terminal_execution_allowed"])
        self.assertTrue(preview["limits"]["file_writes_allowed"])
        self.assertEqual((self.root / target).read_text(encoding="utf-8"), "VALUE = 'old'\n")

    def test_rejected_no_diff_states_do_not_become_approval_ready(self) -> None:
        plan = self._planned_doc_task()
        for raw in ("", "   \n", "not a unified diff"):
            with self.subTest(raw=raw):
                try:
                    preview = preview_diff_verification(raw, task_text=_doc_append_task(), architect_plan=plan)
                except DiffVerificationError as error:
                    self.assertIn(error.reason_code, {"empty_diff"})
                    continue
                self.assertEqual(preview["status"], "blocked")
                self.assertFalse(preview["limits"]["file_writes_allowed"])
                self.assertFalse(preview["would_apply_diff"])

        target = "src/app/demo/page.tsx"
        _write(self.root / target, "export default function Page() { return null; }\n")
        plan = plan_task_deterministically(
            f"Target file: {target}\nUpdate the page.",
            "task-invalid-coder",
            self.root,
        )
        self.assertIsInstance(plan, Plan, plan)
        out = propose_coder_agent_diff_payload_from_plan(
            architect_plan=plan.plan,
            workspace_root=self.root,
            llm_call=lambda _prompt, _model: "Unified diff ready",
        )
        self.assertTrue(out["coder_blocked"])
        self.assertEqual(out["proposed_diff"], "")
        self.assertEqual(out["reason_code"], "coder_response_repair_exhausted")
        self.assertIn("Unified diff ready", out["coder_diagnostics"]["raw_response_excerpt"])

    def test_approved_apply_moves_to_post_verification_state_only_after_approval(self) -> None:
        task = _doc_append_task()
        created = create_long_running_task(task)
        task_id = created["task"]["id"]
        plan = self._planned_doc_task(task, task_id=task_id)
        save_plan(task_id, plan)
        before = (self.root / DOC_TARGET).read_text(encoding="utf-8")
        diff = _standard_doc_diff()
        preview = preview_diff_verification(diff, route_type="local_route", task_text=task, architect_plan=plan)

        self.assertEqual(preview["status"], "preview_ready")
        self.assertEqual((self.root / DOC_TARGET).read_text(encoding="utf-8"), before)

        payload = execute_approved_long_running_task(
            task_id,
            action="append approved docs sentence",
            approval_id=approval_id_for_approved_diff(
                task_id=task_id,
                approved_diff=diff,
                target=DOC_TARGET,
            ),
            approved_by="test",
            approved_diff=diff,
            target=DOC_TARGET,
        )

        content = (self.root / DOC_TARGET).read_text(encoding="utf-8")
        audit = json.loads((self.root / "audit.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertIn(DOC_LITERAL, content)
        self.assertEqual(payload["task"]["status"], "applied_needs_verification")
        self.assertEqual(payload["execution"]["status"], "applied_needs_verification")
        self.assertNotEqual(payload["task"]["status"], "completed")
        self.assertEqual(audit["changed_files"], [DOC_TARGET])
        self.assertIn(DOC_TARGET, payload["task"]["truncated_test_results"])
        self.assertEqual(payload["execution"]["changed_files"][0]["path"], DOC_TARGET)
        snapshots = payload["execution"]["changed_file_snapshots"]
        self.assertEqual(snapshots[0]["path"], DOC_TARGET)
        self.assertIsNotNone(snapshots[0]["sha256_before"])
        self.assertIsNotNone(snapshots[0]["sha256_after"])
        self.assertNotEqual(snapshots[0]["sha256_before"], snapshots[0]["sha256_after"])

        verified = record_post_apply_verification(
            task_id,
            confirm_backup_audit_present=True,
            confirm_expected_change_present=True,
            confirm_no_unintended_files=True,
            verification_note="Docs-only change verified.",
        )

        self.assertEqual(verified["task"]["status"], "completed")
        self.assertEqual(
            verified["task"]["post_apply_verification"]["status"],
            "verified",
        )
        self.assertIn(DOC_LITERAL, (self.root / DOC_TARGET).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
