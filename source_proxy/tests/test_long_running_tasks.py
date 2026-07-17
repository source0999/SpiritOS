from __future__ import annotations

import difflib
import os
import json
import sqlite3
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.long_running_tasks import router as long_running_tasks_router
from source_proxy.context.canonical_broker import build_context_broker_report
from source_proxy.approval.campaign_authority import persist_coding_execution_preview
from source_proxy.planning.plan import (
    PLAN_SCHEMA_VERSION,
    AcceptanceCriterion,
    ArchitectPlan,
    BundleSnapshot,
    CoderPacket,
    ContentConstraints,
    ContextSlice,
    PlanBudget,
    TargetFile,
    TaskClassification,
    VerificationPlan,
    save_plan,
)
from source_proxy.tasks.long_running import (
    _canonical_diff_sha256,
    advance_long_running_task,
    create_long_running_task,
    execute_approved_long_running_task,
    get_long_running_task,
    get_long_running_task_snapshot,
    list_long_running_tasks,
    LongRunningTaskError,
    record_post_apply_verification,
    record_coding_execution_approval,
    reject_long_running_task_plan,
    reset_long_running_tasks,
    update_long_running_task,
)
import source_proxy.tasks.long_running as long_running_module


def _approval_id(task_id: str, diff: str, target: str) -> str:
    preview = persist_coding_execution_preview(
        task_id=task_id,
        action="implement proposed file change",
        approved_diff=diff,
        target=target,
        selected_prompt_id="legacy-test",
        context_hash="legacy-test",
    )
    result = subprocess.run(
        ["python3", str(Path(__file__).resolve().parents[2] / "scripts" / "approval-authority.py"), "issue"],
        input=json.dumps({
            "preview_id": preview["preview_id"],
            "expected_generation": str(preview["generation"]),
            "consumer": "coding-executor:coder",
            "operation": "coding_execution",
            "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
        }),
        text=True,
        capture_output=True,
        check=True,
    )
    return str(json.loads(result.stdout)["approval_id"])


def _passing_managed_browser_proof() -> dict[str, object]:
    return {
        "schema_version": "dummy-storefront-browser-proof/v1",
        "status": "passed",
        "browser_verification_status": "passed",
        "storefront_runtime_status": "passed",
        "storefront_runtime_engine": "playwright_chromium",
        "real_browser_used": True,
        "managed_frontend_origin": "https://localhost:3000",
        "preview_url": "https://localhost:3000/v1/coding/dummy-product-site-preview",
        "preview_http_status": 200,
        "document_ready_state": "complete",
        "product_count": 6,
        "rendered_card_count": 6,
        "module_script_loaded": True,
        "stylesheet_loaded": True,
        "noscript_card_count": 0,
        "asset_responses": {
            "/v1/coding/dummy-product-site-preview": 200,
            "/v1/coding/dummy-product-site-preview/src/main.js": 200,
            "/v1/coding/dummy-product-site-preview/src/products.js": 200,
            "/v1/coding/dummy-product-site-preview/src/styles.css": 200,
        },
        "visible_fields": {
            "name": True,
            "price": True,
            "category": True,
            "description": True,
        },
        "console_errors": [],
        "page_errors": [],
        "request_failures": [],
        "observed_at": "2026-07-11T12:00:00Z",
    }


def _dummy_product_site_lifecycle_diff(
    readme_before: str,
) -> tuple[str, dict[str, str]]:
    root = "tests/ui-agent-trials/fixtures/dummy-product-site"
    applied_contents = {
        f"{root}/README.md": "# LumaCart\n\nA model-authored demo storefront.\n",
        f"{root}/package.json": (
            '{"name":"lumacart-lifecycle-test","private":true,"type":"module"}\n'
        ),
        f"{root}/index.html": (
            "<!doctype html><html><body><main id=\"products\"></main>"
            "<script type=\"module\" src=\"src/main.js\"></script></body></html>\n"
        ),
        f"{root}/src/main.js": (
            'import products from "./products.js";\n'
            'const root = document.querySelector("#products");\n'
            "products.forEach((product) => {\n"
            "  root.insertAdjacentHTML(\"beforeend\", `<article class=\"product-card\">"
            "<h2>${product.name}</h2><p>${product.category}</p>"
            "<p>${product.description}</p><strong>${product.price}</strong></article>`);\n"
            "});\n"
        ),
        f"{root}/src/products.js": (
            "export default [\n"
            + "\n".join(
                f'  {{ id: {index}, name: "Product {index}", price: {index}.99, '
                f'category: "Demo", description: "Product {index} description" }},'
                for index in range(1, 7)
            )
            + "\n];\n"
        ),
        f"{root}/src/styles.css": ".product-card { border: 1px solid #ddd; padding: 1rem; }\n",
    }

    patches: list[str] = []
    for path, after in applied_contents.items():
        before = readme_before if path.endswith("/README.md") else ""
        fromfile = f"a/{path}" if before else "/dev/null"
        patch_lines = difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=fromfile,
            tofile=f"b/{path}",
            lineterm="",
        )
        patches.append(
            "\n".join(
                [
                    f"diff --git a/{path} b/{path}",
                    *(["new file mode 100644"] if not before else []),
                    *patch_lines,
                    "",
                ]
            )
        )
    return "".join(patches), applied_contents


def _manual_plan(task_id: str) -> ArchitectPlan:
    return ArchitectPlan(
        plan_id="plan-api-test",
        task_id=task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at="2026-05-13T00:00:00Z",
        source_task="Test plan API",
        bundle_snapshot=BundleSnapshot(
            bundle_path="/tmp/repomix-output.xml",
            bundle_sha256="0" * 64,
            workspace_root="/tmp",
            generated_at="2026-05-13T00:00:00Z",
        ),
        classification=TaskClassification(
            task_class="implement",
            visual_change=False,
            designer_required=False,
            estimated_complexity="trivial",
        ),
        coder_packet=CoderPacket(
            target_file=TargetFile("src/app/page.tsx", False, None),
            operation="create",
            acceptance_criteria=[],
            constraints=ContentConstraints([], [], [], [], None, None),
            context_slices=[],
            forbidden_paths=[],
            style_directives=[],
        ),
        verification_plan=VerificationPlan(
            required_checks=[],
            designer_review_required=False,
            architect_review_required=False,
        ),
        budget=PlanBudget(3, 120, True),
    )


class LongRunningTaskTrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_database_path = os.environ.get(
            "SOURCE_PROXY_LONG_RUNNING_TASKS_DB"
        )
        self._previous_spirit_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        self._previous_audit_path = os.environ.get("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG")
        self._previous_gate_state_path = os.environ.get("SOURCE_PROXY_GATE_STATE_PATH")
        self._previous_gate_increment = os.environ.get("SOURCE_PROXY_GATE_INCREMENT")
        self._previous_gate_allowed_actions = os.environ.get("SOURCE_PROXY_GATE_ALLOWED_ACTIONS")
        self._tempdir = tempfile.TemporaryDirectory()
        os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = os.path.join(
            self._tempdir.name,
            "tasks.sqlite3",
        )
        os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = os.path.join(
            self._tempdir.name,
            "approved_actions.audit.jsonl",
        )
        gate_state_path = os.path.join(self._tempdir.name, "gate-state.json")
        os.environ["SOURCE_PROXY_GATE_STATE_PATH"] = gate_state_path
        os.environ["SOURCE_PROXY_GATE_INCREMENT"] = "1.3"
        os.environ["SOURCE_PROXY_GATE_ALLOWED_ACTIONS"] = "apply,gate_implementation,model_call"
        with open(gate_state_path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "status": "APPROVED_INCREMENT",
                    "approved_increment": "1.3",
                    "approval_token": "test-token",
                },
                handle,
            )
        os.environ["SPIRIT_PROJECT_PATH"] = self._tempdir.name
        os.makedirs(os.path.join(self._tempdir.name, "source_proxy"), exist_ok=True)
        with open(
            os.path.join(self._tempdir.name, "source_proxy", "main.py"),
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write("old\n")
        reset_long_running_tasks()

    def tearDown(self) -> None:
        reset_long_running_tasks()
        if self._previous_database_path is None:
            os.environ.pop("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", None)
        else:
            os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = (
                self._previous_database_path
            )
        if self._previous_spirit_project_path is None:
            os.environ.pop("SPIRIT_PROJECT_PATH", None)
        else:
            os.environ["SPIRIT_PROJECT_PATH"] = self._previous_spirit_project_path
        if self._previous_audit_path is None:
            os.environ.pop("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG", None)
        else:
            os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = (
                self._previous_audit_path
            )
        if self._previous_gate_state_path is None:
            os.environ.pop("SOURCE_PROXY_GATE_STATE_PATH", None)
        else:
            os.environ["SOURCE_PROXY_GATE_STATE_PATH"] = self._previous_gate_state_path
        if self._previous_gate_increment is None:
            os.environ.pop("SOURCE_PROXY_GATE_INCREMENT", None)
        else:
            os.environ["SOURCE_PROXY_GATE_INCREMENT"] = self._previous_gate_increment
        if self._previous_gate_allowed_actions is None:
            os.environ.pop("SOURCE_PROXY_GATE_ALLOWED_ACTIONS", None)
        else:
            os.environ["SOURCE_PROXY_GATE_ALLOWED_ACTIONS"] = self._previous_gate_allowed_actions
        self._tempdir.cleanup()

    def test_create_and_poll_task_without_execution(self) -> None:
        created = create_long_running_task("Review a large patch")
        task_id = created["task"]["id"]

        first_poll = get_long_running_task(task_id)

        self.assertEqual(created["tool"], "long_running_task_tracker")
        self.assertEqual(created["task"]["status"], "queued")
        self.assertEqual(first_poll["task"]["status"], "running")
        self.assertFalse(first_poll["task"]["would_execute"])
        self.assertFalse(first_poll["task"]["writes_allowed"])

    def test_polling_alone_never_completes_task(self) -> None:
        created = create_long_running_task("Review a large patch")
        task_id = created["task"]["id"]

        statuses = [get_long_running_task(task_id)["task"]["status"] for _ in range(12)]
        final = get_long_running_task(task_id)

        self.assertNotIn("completed", statuses)
        self.assertEqual(final["task"]["status"], "running")
        self.assertGreaterEqual(final["task"]["poll_count"], 13)
        self.assertFalse(final["task"]["would_execute"])
        self.assertFalse(final["task"]["writes_allowed"])

    def test_stale_browser_dependent_task_waits_for_operator_readback(self) -> None:
        created = create_long_running_task("Target file: docs/stale.md\nAppend a stale note.")
        task_id = created["task"]["id"]

        from source_proxy.tasks import long_running

        task = long_running._lookup_task(task_id)
        task.status = "running"
        task.created_at = (datetime.now(UTC) - timedelta(minutes=16)).isoformat()
        task.updated_at = task.created_at
        long_running._save_task(task)

        payload = get_long_running_task(task_id)

        self.assertEqual(payload["task"]["status"], "waiting_for_operator_browser")
        self.assertEqual(payload["task"]["architect_status"], "blocked")
        self.assertIn("/coding", payload["task"]["architect_reason"])
        self.assertTrue(
            any(
                event["event_type"] == "status_transition"
                and event["status_after"] == "waiting_for_operator_browser"
                for event in payload["task"]["causal_events"]
            )
        )

    def test_create_advance_and_poll_do_not_write_files_or_claim_execution(self) -> None:
        target = os.path.join(self._tempdir.name, "docs", "no-write.md")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("# No Write\n\nBefore.\n")
        audit_path = os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"]
        task_text = "Target file: docs/no-write.md\nAppend a note."

        created = create_long_running_task(task_text)
        task_id = created["task"]["id"]
        polled = get_long_running_task(task_id)
        advanced = advance_long_running_task(task_id)

        with open(target, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "# No Write\n\nBefore.\n")
        self.assertFalse(os.path.exists(audit_path))
        self.assertNotIn("execution", created)
        self.assertFalse(created["task"]["would_execute"])
        self.assertFalse(polled["task"]["writes_allowed"])
        self.assertNotEqual(advanced["task"]["status"], "completed")

    def test_list_long_running_tasks_returns_read_only_queue_items(self) -> None:
        created = create_long_running_task("Target file: source_proxy/main.py\nUpdate docs.")
        task_id = created["task"]["id"]
        update_long_running_task(
            task_id,
            current_agent_role="coder",
            open_diffs=[
                {
                    "changed_files": [
                        {"path": "source_proxy/main.py"},
                        {"path": "docs/source-proxy.md"},
                    ],
                    "status": "pending_verification",
                }
            ],
            status="running",
        )

        queue = list_long_running_tasks()

        self.assertEqual(queue["access_scope"], "read_only_task_queue")
        self.assertEqual(queue["count"], 1)
        item = queue["tasks"][0]
        self.assertEqual(item["task_id"], task_id)
        self.assertEqual(item["worker"], "coder")
        self.assertEqual(item["mode"], "read_only_status_tracking")
        self.assertEqual(item["scope_key"], "source_proxy/main.py")
        self.assertTrue(item["write_capable"])
        self.assertEqual(item["target_file"], "source_proxy/main.py")
        self.assertEqual(
            item["allowed_files"],
            ["source_proxy/main.py", "docs/source-proxy.md"],
        )
        self.assertFalse("apply" in item)
        self.assertFalse("commit" in item)
        self.assertFalse("push" in item)
        lane_ids = {lane["id"] for lane in item["worker_lanes"]}
        self.assertIn("codex_cli", lane_ids)
        self.assertIn("deterministic_verifier", lane_ids)
        self.assertIn("cartographer", lane_ids)
        for lane in item["worker_lanes"]:
            self.assertEqual(lane["mode"], "read_only_evidence")
            self.assertFalse(lane["approval_authority"])
            self.assertFalse(lane["apply_authority"])
            self.assertFalse(lane["commit_authority"])
            self.assertFalse(lane["push_authority"])

    def test_create_blocks_second_live_write_task_on_same_scope(self) -> None:
        first = create_long_running_task(
            "Target file: source_proxy/main.py\nUpdate implementation."
        )
        second = create_long_running_task(
            "Target file: source_proxy/main.py\nFix the same implementation."
        )

        self.assertEqual(first["task"]["status"], "queued")
        self.assertEqual(first["task"]["scope_key"], "source_proxy/main.py")
        self.assertTrue(first["task"]["write_capable"])
        self.assertEqual(second["task"]["status"], "blocked")
        self.assertEqual(second["task"]["architect_reason"], "write_scope_conflict")
        self.assertEqual(second["task"]["scope_key"], "source_proxy/main.py")
        self.assertTrue(second["task"]["write_capable"])
        self.assertIn("write_scope_conflict", second["task"]["truncated_test_results"])
        self.assertEqual(second["truth_status"], "BLOCKED_SAFE")
        self.assertEqual(second["reason_code"], "write_scope_conflict")
        self.assertEqual(second["approval_binding_status"], "not_run: route_error_before_model_call")
        self.assertEqual(second["anti_cheat_status"], "not_run")
        self.assertEqual(
            second["anti_cheat_reasons"],
            ["route_error_before_model_call"],
        )
        self.assertEqual(
            second["diagnostic_envelope"]["acceptance_gate"]["phase_verifier_status"],
            "skipped_with_reason",
        )
        self.assertEqual(
            second["task"]["ast_snapshot"]["queue_policy"],
            "one_write_capable_task_per_scope",
        )

    def test_create_returns_persisted_task_id_with_creation_diagnostics(self) -> None:
        with mock.patch.object(long_running_module.subprocess, "run") as run:
            created = create_long_running_task(
                "Target file: source_proxy/main.py\nUpdate implementation."
            )

        self.assertRegex(created["task"]["id"], r"^task_[0-9a-f]+$")
        self.assertEqual(created["task_creation_status"], "persisted_task_id")
        self.assertEqual(created["task"]["task_creation_status"], "persisted_task_id")
        self.assertGreaterEqual(created["task_creation_elapsed_ms"], 0)
        self.assertEqual(
            created["task_creation_timeout_stage"],
            "not_applicable: task_id_persisted",
        )
        self.assertEqual(created["task_creation_last_checkpoint"], "task_envelope_built")
        self.assertEqual(
            created["task_creation_blocking_subsystem"],
            "not_applicable: task_id_persisted",
        )
        checkpoint_stages = [
            checkpoint["stage"]
            for checkpoint in created["task_creation_checkpoints"]
        ]
        self.assertIn("task_persisted", checkpoint_stages)
        self.assertIn("task_envelope_built", checkpoint_stages)
        self.assertNotIn("prompt_packet_requested", checkpoint_stages)
        self.assertNotIn("diff_generation_started", checkpoint_stages)
        run.assert_not_called()

    def test_create_route_surfaces_creation_diagnostics(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        with mock.patch.object(
            long_running_module,
            "_write_scope_conflict_for_task",
            side_effect=AssertionError("route task create must return id before queue checks"),
        ):
            response = client.post(
                "/v1/tasks/long-running",
                json={"description": "Target file: source_proxy/main.py\nUpdate implementation."},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertRegex(payload["task"]["id"], r"^task_[0-9a-f]+$")
        self.assertEqual(payload["task_creation_status"], "persisted_task_id")
        self.assertEqual(payload["task"]["task_creation_status"], "persisted_task_id")
        self.assertEqual(
            payload["task_creation_timeout_stage"],
            "not_applicable: task_id_persisted",
        )
        checkpoint_stages = [
            checkpoint["stage"]
            for checkpoint in payload["task_creation_checkpoints"]
        ]
        self.assertIn("write_scope_conflict_deferred", checkpoint_stages)
        self.assertIn("old_tasks_prune_deferred", checkpoint_stages)

    def test_create_ignores_pre_execution_safety_block_on_same_scope(self) -> None:
        poisoned = create_long_running_task(
            "Target file: source_proxy/main.py\nUpdate implementation."
        )
        update_long_running_task(
            poisoned["task"]["id"],
            status="running",
            current_agent_role="coder",
            architect_status="planned",
            open_diffs=[],
            causal_events=[
                {
                    "event_type": "failure",
                    "notes": ["approved_diff_blocked"],
                }
            ],
        )

        retry = create_long_running_task(
            "Target file: source_proxy/main.py\nRetry the same implementation."
        )

        self.assertEqual(retry["task"]["status"], "queued")
        self.assertEqual(retry["task"]["scope_key"], "source_proxy/main.py")
        self.assertNotEqual(retry["task"]["architect_reason"], "write_scope_conflict")

    def test_create_ignores_abandoned_pre_preview_write_lock_on_same_scope(self) -> None:
        stale = create_long_running_task(
            "Target file: source_proxy/main.py\nUpdate implementation."
        )
        old = (datetime.now(UTC) - timedelta(minutes=20)).isoformat()
        update_long_running_task(
            stale["task"]["id"],
            status="queued",
            current_agent_role="architect",
            architect_status="idle",
            architect_reason="",
            open_diffs=[],
            causal_events=[],
            created_at=old,
        )

        retry = create_long_running_task(
            "Target file: source_proxy/main.py\nRetry the same implementation."
        )

        self.assertEqual(retry["task"]["status"], "queued")
        self.assertEqual(retry["task"]["scope_key"], "source_proxy/main.py")
        self.assertNotEqual(retry["task"]["architect_reason"], "write_scope_conflict")

    def test_create_ignores_dummy_selected_prompt_placeholder_lock_on_same_scope(self) -> None:
        selected_prompt_description = "\n".join(
            [
                "make the dummy LumaCart page actually show the products as cards.",
                "",
                "Target file: tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
                "Allowed files: tests/ui-agent-trials/fixtures/dummy-product-site/**",
                "Fixture root: tests/ui-agent-trials/fixtures/dummy-product-site/",
                "Pass expectations: Products render from src/products.js.",
                "Fail conditions: Edits SpiritOS UI files.",
                "LumaCart is a small isolated fake product storefront fixture used only for coder-agent testing.",
            ]
        )
        first = create_long_running_task(selected_prompt_description)

        retry = create_long_running_task(selected_prompt_description)

        self.assertEqual(first["task"]["status"], "queued")
        self.assertEqual(
            first["task"]["scope_key"],
            "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        )
        self.assertEqual(retry["task"]["status"], "queued")
        self.assertEqual(
            retry["task"]["scope_key"],
            "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        )
        self.assertNotEqual(retry["task"]["architect_reason"], "write_scope_conflict")

    def test_create_ignores_dummy_cleanup_delete_verification_lock_on_same_scope(self) -> None:
        cleanup = create_long_running_task(
            "Agent-lab cleanup delete tests/ui-agent-trials/fixtures/dummy-product-site/README.md"
        )
        update_long_running_task(
            cleanup["task"]["id"],
            status="applied_needs_verification",
            current_agent_role="debugger",
            architect_status="planned",
        )

        retry = create_long_running_task(
            "\n".join(
                [
                    "make a tiny fake product website project for testing the coder agent. call it LumaCart.",
                    "Target file: tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
                    "Allowed files: tests/ui-agent-trials/fixtures/dummy-product-site/**",
                    "Pass expectations: Creates the LumaCart fixture.",
                    "Fail conditions: Edits SpiritOS UI files.",
                ]
            )
        )

        self.assertEqual(retry["task"]["status"], "queued")
        self.assertNotEqual(retry["task"]["architect_reason"], "write_scope_conflict")

    def test_create_ignores_stale_dummy_selected_prompt_verification_lock(self) -> None:
        selected_prompt_description = "\n".join(
            [
                "make a tiny fake product website project for testing the coder agent. call it LumaCart.",
                "Target file: tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
                "Allowed files: tests/ui-agent-trials/fixtures/dummy-product-site/**",
                "Pass expectations: Creates the LumaCart fixture.",
                "Fail conditions: Edits SpiritOS UI files.",
            ]
        )
        stale = create_long_running_task(selected_prompt_description)
        old = (datetime.now(UTC) - timedelta(minutes=2)).isoformat()
        update_long_running_task(
            stale["task"]["id"],
            status="applied_needs_verification",
            current_agent_role="debugger",
            architect_status="planned",
            updated_at=old,
        )

        retry = create_long_running_task(selected_prompt_description)

        self.assertEqual(retry["task"]["status"], "queued")
        self.assertNotEqual(retry["task"]["architect_reason"], "write_scope_conflict")

    def test_create_allows_read_only_parallel_review_on_same_scope(self) -> None:
        first = create_long_running_task(
            "Target file: source_proxy/main.py\nUpdate implementation."
        )
        review = create_long_running_task(
            "Read-only review only. Target file: source_proxy/main.py."
        )

        self.assertEqual(first["task"]["status"], "queued")
        self.assertEqual(review["task"]["status"], "queued")
        self.assertEqual(review["task"]["scope_key"], "source_proxy/main.py")
        self.assertFalse(review["task"]["write_capable"])

    def test_task_payload_lists_multi_worker_lanes_as_evidence_only(self) -> None:
        created = create_long_running_task("Target file: source_proxy/main.py\nUpdate docs.")
        task_id = created["task"]["id"]
        update_long_running_task(
            task_id,
            current_agent_role="coder",
            open_diffs=[
                {
                    "changed_files": [{"path": "source_proxy/main.py"}],
                    "diff": "diff --git a/source_proxy/main.py b/source_proxy/main.py\n",
                    "status": "pending_verification",
                }
            ],
            status="running",
        )

        payload = get_long_running_task_snapshot(task_id)

        lanes = payload["task"]["worker_lanes"]
        self.assertEqual(
            [lane["id"] for lane in lanes],
            [
                "codex_cli",
                "deterministic_verifier",
                "reviewer",
                "cartographer",
                "scout_intake",
                "local_model_reviewer",
            ],
        )
        self.assertEqual(lanes[0]["status"], "evidence")
        self.assertEqual(lanes[-1]["status"], "config_blocked")
        for lane in lanes:
            self.assertEqual(lane["mode"], "read_only_evidence")
            self.assertFalse(lane["apply_authority"])
            self.assertFalse(lane["commit_authority"])
            self.assertFalse(lane["push_authority"])

    def test_task_queue_blocker_uses_reason_code_not_full_log(self) -> None:
        created = create_long_running_task("Target file: source_proxy/main.py\nUpdate docs.")
        task_id = created["task"]["id"]
        update_long_running_task(
            task_id,
            status="blocked",
            truncated_test_results=(
                "CODER_BLOCKED reason_code: coder_packet_missing_context; "
                "long diagnostic details"
            ),
        )

        queue = list_long_running_tasks()

        self.assertEqual(queue["tasks"][0]["blocker"], "coder_packet_missing_context")

    def test_router_lists_long_running_task_queue(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = client.post(
            "/v1/tasks/long-running",
            json={"description": "Queue item"},
        )
        listed = client.get("/v1/tasks/long-running")

        self.assertEqual(created.status_code, 200)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["access_scope"], "read_only_task_queue")
        self.assertEqual(listed.json()["tasks"][0]["title"], "Queue item")

    def test_coder_blocked_before_diff_does_not_report_nearly_complete_progress(self) -> None:
        created = create_long_running_task("Target file: source_proxy/main.py\nUpdate docs.")
        task_id = created["task"]["id"]

        update_long_running_task(
            task_id,
            status="blocked",
            current_agent_role="coder",
            truncated_test_results="coder_status=blocked; reason_code=coder_sync_timeout",
        )
        payload = get_long_running_task(task_id)

        self.assertEqual(payload["task"]["status"], "blocked")
        self.assertEqual(payload["task"]["current_agent_role"], "coder")
        self.assertLessEqual(payload["task"]["progress"], 50)

    def test_task_stays_running_after_multiple_polls_without_execution(self) -> None:
        created = create_long_running_task("Prepare verification plan")
        task_id = created["task"]["id"]

        for _ in range(4):
            payload = get_long_running_task(task_id)

        self.assertEqual(payload["task"]["status"], "running")
        self.assertLess(payload["task"]["progress"], 100)

    def test_router_can_cancel_task(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = client.post(
            "/v1/tasks/long-running",
            json={"description": "Run a staged verification pass"},
        )
        task_id = created.json()["task"]["id"]
        cancelled = client.post(f"/v1/tasks/long-running/{task_id}/cancel")

        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["task"]["status"], "cancelled")

    def test_router_can_cancel_waiting_for_operator_browser_task(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = create_long_running_task(
            "Target file: tests/ui-agent-trials/fixtures/dummy-product-site/README.md\n"
            "Run selected dummy prompt."
        )
        task_id = created["task"]["id"]
        update_long_running_task(
            task_id,
            status="waiting_for_operator_browser",
            architect_status="blocked",
            architect_reason="operator must run preview/apply from /coding",
            truncated_test_results=(
                "reason_code: operator_browser_required; "
                "operator must run preview/apply from /coding"
            ),
        )

        cancelled = client.post(f"/v1/tasks/long-running/{task_id}/cancel")

        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["task"]["status"], "cancelled")
        self.assertIsNotNone(cancelled.json()["task"]["cancelled_at"])

    def test_router_marks_selected_dummy_apply_completed(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = client.post(
            "/v1/tasks/long-running",
            json={
                "description": (
                    "Target file: tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js\n"
                    "Add LumaCart product data."
                )
            },
        )
        task_id = created.json()["task"]["id"]
        response = client.post(
            f"/v1/tasks/long-running/{task_id}/selected-dummy-applied",
            json={
                "changed_files": [
                    "tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js"
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["task"]
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["architect_status"], "completed")
        self.assertEqual(payload["architect_reason"], "selected_dummy_apply_completed")
        self.assertIn("selected_dummy_apply_completed", payload["truncated_test_results"])

    def test_router_returns_saved_architect_plan(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = client.post(
            "/v1/tasks/long-running",
            json={"description": "Plan API"},
        )
        task_id = created.json()["task"]["id"]
        missing = client.get(f"/v1/tasks/long-running/{task_id}/plan")
        save_plan(task_id, _manual_plan(task_id))
        found = client.get(f"/v1/tasks/long-running/{task_id}/plan")

        self.assertEqual(missing.status_code, 200)
        self.assertEqual(missing.json().get("plan_available"), False)
        self.assertEqual(missing.json().get("reason_code"), "plan_not_ready")
        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.json()["plan_id"], "plan-api-test")
        self.assertEqual(
            found.json()["coder_packet"]["target_file"]["path"],
            "src/app/page.tsx",
        )

    def test_plan_rejection_is_audited_and_regenerates(self) -> None:
        audit_path = os.path.join(self._tempdir.name, "audit.jsonl")
        previous_audit_path = os.environ.get("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG")
        os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = audit_path
        try:
            created = create_long_running_task(
                "Target file: source_proxy/main.py\nAdd a comment"
            )
            task_id = created["task"]["id"]
            save_plan(task_id, _manual_plan(task_id))

            rejected = reject_long_running_task_plan(
                task_id,
                reason_code="other",
                details="manual test rejection",
            )

            self.assertEqual(rejected["rejection"]["reason_code"], "other")
            self.assertEqual(rejected["task"]["architect_status"], "planned")
            self.assertEqual(rejected["task"]["current_agent_role"], "coder")
            with open(audit_path, encoding="utf-8") as handle:
                audit = json.loads(handle.readline())
            self.assertEqual(audit["event"], "plan_rejected")
            self.assertEqual(audit["reason_code"], "other")
            self.assertEqual(audit["task_id"], task_id)
        finally:
            if previous_audit_path is None:
                os.environ.pop("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG", None)
            else:
                os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = previous_audit_path

    def test_task_persists_blackboard_fields_to_sqlite(self) -> None:
        created = create_long_running_task("Track swarm state")
        task_id = created["task"]["id"]

        update_long_running_task(
            task_id,
            ast_snapshot={"files": ["source_proxy/tasks/long_running.py"]},
            open_diffs=[{"path": "a.py", "status": "pending"}],
            truncated_test_results="ok",
            current_agent_role="coder",
        )

        with closing(
            sqlite3.connect(os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"])
        ) as db:
            columns = {
                row[1]
                for row in db.execute("PRAGMA table_info(long_running_tasks)")
            }
            row = db.execute(
                """
                SELECT
                    ast_snapshot_json,
                    open_diffs_json,
                    truncated_test_results,
                    current_agent_role,
                    cycle_count
                FROM long_running_tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()

        self.assertIn("ast_snapshot_json", columns)
        self.assertIn("open_diffs_json", columns)
        self.assertIn("truncated_test_results", columns)
        self.assertIn("current_agent_role", columns)
        self.assertIn("source_proxy/tasks/long_running.py", row[0])
        self.assertIn("a.py", row[1])
        self.assertEqual(row[2], "ok")
        self.assertEqual(row[3], "coder")
        self.assertEqual(row[4], 0)

    def test_store_initialization_skips_schema_write_when_schema_complete(self) -> None:
        create_long_running_task("Initialize task store schema")
        long_running_module._TASK_STORE_INITIALIZED_PATHS.clear()

        with mock.patch.object(
            long_running_module,
            "_ensure_column",
            side_effect=AssertionError("schema migration should not run"),
        ):
            created = create_long_running_task("Create without schema write")

        self.assertEqual(created["task"]["description"], "Create without schema write")

    def test_default_sqlite_path_ignores_spirit_project_apply_roots(self) -> None:
        configured_db = os.environ.pop("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", None)
        configured_spirit_root = os.environ.get("SPIRIT_PROJECT_PATH")
        try:
            external_root = os.path.join(self._tempdir.name, "external-apply-root")
            os.makedirs(external_root, exist_ok=True)
            os.environ["SPIRIT_PROJECT_PATH"] = external_root

            sqlite_path = long_running_module._sqlite_path()

            self.assertEqual(sqlite_path.name, "long_running_tasks.sqlite3")
            self.assertNotIn("external-apply-root", str(sqlite_path))
            self.assertEqual(sqlite_path.parent.name, "data")
        finally:
            if configured_db is not None:
                os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = configured_db
            if configured_spirit_root is not None:
                os.environ["SPIRIT_PROJECT_PATH"] = configured_spirit_root

    def test_two_near_simultaneous_task_creates_do_not_lock_store(self) -> None:
        def create(index: int) -> str:
            payload = create_long_running_task(f"Concurrent queue item {index}")
            return payload["task"]["id"]

        with ThreadPoolExecutor(max_workers=2) as executor:
            task_ids = list(executor.map(create, [1, 2]))

        self.assertEqual(len(set(task_ids)), 2)
        queue = list_long_running_tasks(limit=10)
        queued_ids = {item["task_id"] for item in queue["tasks"]}
        self.assertTrue(set(task_ids).issubset(queued_ids))

    def test_router_returns_structured_diagnostic_when_store_is_locked(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        with mock.patch(
            "source_proxy.api.long_running_tasks.create_long_running_task",
            side_effect=sqlite3.OperationalError("database is locked"),
        ):
            response = client.post(
                "/v1/tasks/long-running",
                json={"description": "Selected prompt store failure"},
            )

        self.assertEqual(response.status_code, 503)
        detail = response.json()["detail"]
        self.assertEqual(detail["truth_status"], "BLOCKED_SAFE")
        self.assertEqual(detail["reason_code"], "task_store_sqlite_locked")
        self.assertEqual(
            detail["approval_binding"]["approval_binding_status"],
            "not_run: task_store_unavailable_before_task_id",
        )
        self.assertEqual(detail["anti_cheat"]["anti_cheat_status"], "not_run")
        self.assertEqual(
            detail["diagnostic_envelope"]["apply_block_layer"],
            "task_store_before_model_call",
        )

    def test_pre_save_hook_truncates_logs_and_purges_verified_diffs(self) -> None:
        created = create_long_running_task("Trim debugger output")
        task_id = created["task"]["id"]
        stderr_log = "x" * 20_000

        updated = update_long_running_task(
            task_id,
            open_diffs=[
                {"path": "verified.py", "verified": True},
                {"path": "pending.py", "status": "pending"},
            ],
            truncated_test_results=stderr_log,
        )

        task = updated["task"]
        self.assertEqual(len(task["truncated_test_results"]), 1500)
        self.assertEqual(task["truncated_test_results"], stderr_log[-1500:])
        self.assertEqual(
            task["open_diffs"],
            [{"path": "pending.py", "status": "pending"}],
        )

    def test_swarm_handoff_runs_architect_to_coder_to_debugger_to_complete(self) -> None:
        created = create_long_running_task(
            "Target file: source_proxy/main.py\nPatch a small Python file"
        )
        task_id = created["task"]["id"]

        architect = advance_long_running_task(task_id)
        self.assertEqual(architect["task"]["current_agent_role"], "coder")
        self.assertEqual(architect["task"]["status"], "running")
        self.assertIsNotNone(architect["task"]["ast_snapshot"])

        diff = "\n".join(
            [
                "diff --git a/source_proxy/main.py b/source_proxy/main.py",
                "--- a/source_proxy/main.py",
                "+++ b/source_proxy/main.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
                "",
            ]
        )
        coder = advance_long_running_task(task_id, proposed_diff=diff)
        self.assertEqual(coder["task"]["current_agent_role"], "debugger")
        self.assertEqual(coder["task"]["open_diffs"][0]["status"], "pending_verification")

        debugger = advance_long_running_task(
            task_id,
            sandbox_result={"returncode": 0, "stdout": "ok\n", "stderr": ""},
        )
        self.assertEqual(debugger["task"]["status"], "completed")
        self.assertEqual(debugger["task"]["cycle_count"], 1)
        self.assertEqual(debugger["task"]["open_diffs"], [])
        self.assertIn("ok", debugger["task"]["truncated_test_results"])

    def test_swarm_debugger_failure_returns_to_coder_with_truncated_output(self) -> None:
        created = create_long_running_task(
            "Target file: source_proxy/main.py\nRetry a failing patch"
        )
        task_id = created["task"]["id"]
        advance_long_running_task(task_id)
        diff = "\n".join(
            [
                "diff --git a/source_proxy/main.py b/source_proxy/main.py",
                "--- a/source_proxy/main.py",
                "+++ b/source_proxy/main.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
                "",
            ]
        )
        advance_long_running_task(task_id, proposed_diff=diff)

        failed = advance_long_running_task(
            task_id,
            sandbox_result={
                "returncode": 1,
                "stdout": "",
                "stderr": "x" * 20_000,
            },
        )

        self.assertEqual(failed["task"]["current_agent_role"], "coder")
        self.assertEqual(failed["task"]["status"], "running")
        self.assertEqual(failed["task"]["cycle_count"], 1)
        self.assertEqual(len(failed["task"]["truncated_test_results"]), 1500)
        self.assertEqual(failed["task"]["open_diffs"][0]["status"], "needs_revision")

    def test_reviewer_blocked_diff_sets_terminal_blocked_status(self) -> None:
        created = create_long_running_task(
            "Target file: source_proxy/main.py\nAdd the approved literal"
        )
        task_id = created["task"]["id"]
        save_plan(
            task_id,
            ArchitectPlan(
                plan_id="plan-review-blocked",
                task_id=task_id,
                schema_version=PLAN_SCHEMA_VERSION,
                created_at="2026-05-14T00:00:00Z",
                source_task="Target file: source_proxy/main.py\nAdd the approved literal",
                bundle_snapshot=BundleSnapshot(
                    bundle_path="/tmp/repomix-output.xml",
                    bundle_sha256="0" * 64,
                    workspace_root=self._tempdir.name,
                    generated_at="2026-05-14T00:00:00Z",
                ),
                classification=TaskClassification(
                    task_class="implement",
                    visual_change=False,
                    designer_required=False,
                    estimated_complexity="trivial",
                ),
                coder_packet=CoderPacket(
                    target_file=TargetFile("source_proxy/main.py", True, "a" * 64),
                    operation="edit",
                    acceptance_criteria=[
                        AcceptanceCriterion(
                            "literal-required",
                            'Output must contain "RequiredLiteral".',
                            "literal",
                        )
                    ],
                    constraints=ContentConstraints(
                        ["RequiredLiteral"], [], [], [], None, None
                    ),
                    context_slices=[
                        ContextSlice(
                            path="source_proxy/main.py",
                            kind="target",
                            sha256="a" * 64,
                            content="old\n",
                            line_range=(1, 1),
                        )
                    ],
                    forbidden_paths=[],
                    style_directives=[],
                ),
                verification_plan=VerificationPlan(
                    required_checks=[],
                    designer_review_required=False,
                    architect_review_required=False,
                ),
                budget=PlanBudget(3, 120, True),
            ),
        )
        update_long_running_task(
            task_id,
            status="running",
            current_agent_role="coder",
            architect_status="planned",
        )
        diff = "\n".join(
            [
                "diff --git a/source_proxy/main.py b/source_proxy/main.py",
                "--- a/source_proxy/main.py",
                "+++ b/source_proxy/main.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
                "",
            ]
        )

        payload = advance_long_running_task(task_id, proposed_diff=diff)

        self.assertEqual(payload["task"]["status"], "blocked_by_review")
        self.assertNotEqual(payload["task"]["status"], "running")
        self.assertEqual(payload["task"]["current_agent_role"], "coder")
        self.assertEqual(payload["task"]["open_diffs"][0]["status"], "blocked_by_review")
        self.assertFalse(payload["task"]["writes_allowed"])
        self.assertFalse(payload["task"]["would_execute"])

        polled = get_long_running_task(task_id)
        self.assertEqual(polled["task"]["status"], "blocked_by_review")

    def test_router_can_advance_swarm_task(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = client.post(
            "/v1/tasks/long-running",
            json={"description": "Target file: source_proxy/main.py\nRun handoff"},
        )
        task_id = created.json()["task"]["id"]
        advanced = client.post(f"/v1/tasks/long-running/{task_id}/advance", json={})

        self.assertEqual(advanced.status_code, 200)
        self.assertEqual(advanced.json()["task"]["current_agent_role"], "coder")
        self.assertEqual(advanced.json()["task"]["architect_status"], "planned")

    def test_architect_timeout_uses_deterministic_markdown_append_fallback(self) -> None:
        docs = Path(self._tempdir.name) / "docs"
        docs.mkdir(parents=True)
        (docs / "phase-8-manual-check.md").write_text(
            "# Phase 8 Manual Check\n\nExisting paragraph.\n",
            encoding="utf-8",
        )
        created = create_long_running_task(
            'Target file: docs/phase-8-manual-check.md\n\n'
            'Append one short sentence under the existing paragraph:\n'
            '"Manual verification should clearly report whether a diff was produced."'
        )
        task_id = created["task"]["id"]

        from source_proxy.planning.architect import ArchitectLLMError, FallthroughToLLM

        with (
            mock.patch(
                "source_proxy.planning.architect.plan_task_deterministically",
                return_value=FallthroughToLLM("forced_llm_for_test"),
            ),
            mock.patch(
                "source_proxy.planning.architect.plan_task_with_llm",
                side_effect=ArchitectLLMError(
                    "architect_llm_timeout",
                    "LLM Architect timed out after 20 seconds.",
                ),
            ),
        ):
            advanced = advance_long_running_task(task_id)

        self.assertEqual(advanced["task"]["architect_status"], "planned")
        self.assertEqual(
            advanced["task"]["architect_reason"],
            "deterministic_markdown_append_fallback",
        )
        self.assertEqual(advanced["task"]["current_agent_role"], "coder")

    def test_architect_blocks_vague_write_without_llm_target_guess(self) -> None:
        created = create_long_running_task(
            "Make a small improvement to the docs explaining approval safety."
        )
        task_id = created["task"]["id"]

        with mock.patch("source_proxy.planning.architect.plan_task_with_llm") as llm_mock:
            advanced = advance_long_running_task(task_id)

        llm_mock.assert_not_called()
        self.assertEqual(advanced["task"]["status"], "blocked")
        self.assertEqual(advanced["task"]["architect_status"], "blocked")
        self.assertEqual(advanced["task"]["architect_reason"], "target_unresolved")
        self.assertFalse(advanced["task"]["writes_allowed"])

    def test_approved_execution_applies_verified_diff_and_audits(self) -> None:
        previous_cwd = os.getcwd()
        audit_path = os.path.join(self._tempdir.name, "audit.jsonl")
        previous_audit_path = os.environ.get("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG")
        os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = audit_path
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export default function Demo() { return null; }\n")

            created = create_long_running_task("Apply approved demo diff")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export default function Demo() { return null; }",
                    "+export default function Demo() { return <main>Done</main>; }",
                    "",
                ]
            )

            with mock.patch("source_proxy.tasks.long_running.central_gate_check"):
                payload = execute_approved_long_running_task(
                    task_id,
                    action="implement proposed file change",
                    approval_id=_approval_id(task_id, diff, "src/app/demo/page.tsx"),
                    approved_by="test",
                    approved_diff=diff,
                    target="src/app/demo/page.tsx",
                )

            with open("src/app/demo/page.tsx", encoding="utf-8") as handle:
                content = handle.read()
            with open(audit_path, encoding="utf-8") as handle:
                audit_line = handle.readline()

            self.assertIn("<main>Done</main>", content)
            self.assertTrue(payload["execution"]["ok"])
            self.assertEqual(payload["task"]["status"], "applied_needs_verification")
            self.assertEqual(payload["execution"]["status"], "applied_needs_verification")
            self.assertEqual(
                payload["task"]["post_apply_verification"]["status"],
                "verification_ready",
            )
            self.assertTrue(payload["task"]["writes_allowed"])
            self.assertIn("src/app/demo/page.tsx", audit_line)
            events = payload["task"]["causal_events"]
            self.assertGreaterEqual(len(events), 3)
            event_ids = [event["event_id"] for event in events]
            self.assertEqual(len(event_ids), len(set(event_ids)))
            trace_ids = {event["trace_id"] for event in events}
            self.assertEqual(len(trace_ids), 1)
            invocation = next(
                event for event in events if event["event_type"] == "invocation"
            )
            consumer = next(
                event for event in events
                if event["event_type"] == "consumer"
                and event["consumer_subsystem"] == "long_running_status_observer"
            )
            self.assertEqual(invocation["task_id"], task_id)
            self.assertTrue(str(invocation["approval_id"]).startswith("apr_"))
            self.assertEqual(invocation["run_id"], f"execute_approved_long_running_task:{task_id}")
            self.assertEqual(invocation["subsystem"], "source_proxy_long_running")
            self.assertEqual(consumer["consumer_subsystem"], "long_running_status_observer")
            self.assertEqual(consumer["trace_id"], invocation["trace_id"])
            self.assertEqual(
                payload["task"]["causal_trace"]["consumer_event_id"],
                consumer["event_id"],
            )
            self.assertEqual(
                payload["execution"]["invocation_event_id"],
                invocation["event_id"],
            )
            self.assertEqual(payload["execution"]["acceptance"]["binary_verdict"], "GO")
            self.assertEqual(
                payload["execution"]["acceptance"]["fail_closed_lane_status"],
                "GO",
            )
            self.assertEqual(payload["diagnostic_envelope"]["reason_code"], "post_apply_verification_required")
            self.assertEqual(
                payload["diagnostic_envelope"]["approval_binding"]["approval_binding_status"],
                "valid",
            )
            self.assertTrue(
                str(payload["diagnostic_envelope"]["approval_binding"]["expected_approval_id"]).startswith("apr_")
            )
            self.assertEqual(
                payload["diagnostic_envelope"]["approval_binding"]["received_approval_id"],
                invocation["approval_id"],
            )
            self.assertEqual(payload["diagnostic_envelope"]["acceptance_gate"]["plan5_gate_present"], True)
            self.assertEqual(
                payload["diagnostic_envelope"]["verification"]["post_apply_verification_reason"],
                "post_apply_verification_incomplete",
            )
            self.assertIn(
                "Run the listed post-apply verification checks",
                payload["diagnostic_envelope"]["verification"]["verification_required_action"],
            )
            self.assertEqual(payload["task"]["approval_binding_status"], "valid")
            self.assertEqual(payload["task"]["truth_status"], "BLOCKED_SAFE")
            self.assertEqual(payload["task"]["commit_safe"], False)
            self.assertEqual(
                payload["task"]["commit_safe_reason"],
                "post_apply_verification_incomplete",
            )
            audit_payload = json.loads(audit_line)
            self.assertEqual(audit_payload["acceptance"]["binary_verdict"], "GO")
            self.assertEqual(
                audit_payload["acceptance"]["gate_id"],
                "plan5_execute_approved_acceptance",
            )
        finally:
            os.chdir(previous_cwd)
            if previous_audit_path is None:
                os.environ.pop("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG", None)
            else:
                os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"] = (
                previous_audit_path
            )

    def test_execute_approved_acceptance_no_go_when_causal_evidence_missing(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/nogo.md", "w", encoding="utf-8") as handle:
                handle.write("# No Go\n\nBefore.\n")

            created = create_long_running_task("Append docs note with stripped causal evidence")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/nogo.md b/docs/nogo.md",
                    "--- a/docs/nogo.md",
                    "+++ b/docs/nogo.md",
                    "@@ -1,3 +1,4 @@",
                    " # No Go",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )

            with mock.patch(
                "source_proxy.tasks.long_running._record_execute_approved_plan2_integration",
                return_value=None,
            ):
                payload = execute_approved_long_running_task(
                    task_id,
                    action="append docs note",
                    approval_id=_approval_id(task_id, diff, "docs/nogo.md"),
                    approved_by="test",
                    approved_diff=diff,
                    target="docs/nogo.md",
                )

            acceptance = payload["execution"]["acceptance"]
            self.assertEqual(payload["task"]["status"], "applied_needs_verification")
            self.assertEqual(acceptance["binary_verdict"], "NO-GO")
            self.assertIn("subsystem_record_missing", acceptance["failures"])
            with open(os.environ["SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG"], encoding="utf-8") as handle:
                audit_payload = json.loads(handle.readline())
            self.assertEqual(audit_payload["acceptance"]["binary_verdict"], "NO-GO")
        finally:
            os.chdir(previous_cwd)

    def test_causal_events_persist_with_task_record(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/causal.md", "w", encoding="utf-8") as handle:
                handle.write("# Causal\n\nBefore.\n")

            created = create_long_running_task("Append causal note")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/causal.md b/docs/causal.md",
                    "--- a/docs/causal.md",
                    "+++ b/docs/causal.md",
                    "@@ -1,3 +1,4 @@",
                    " # Causal",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )
            with mock.patch("source_proxy.tasks.long_running.central_gate_check"):
                payload = execute_approved_long_running_task(
                    task_id,
                    action="append docs note",
                    approval_id=_approval_id(task_id, diff, "docs/causal.md"),
                    approved_diff=diff,
                    target="docs/causal.md",
            )
            trace_id = payload["task"]["causal_trace"]["trace_id"]
            from source_proxy.tasks import long_running

            long_running._tasks.clear()

            reloaded = get_long_running_task_snapshot(task_id)

            self.assertEqual(reloaded["task"]["causal_trace"]["trace_id"], trace_id)
            self.assertTrue(reloaded["task"]["causal_events"])
            self.assertEqual(
                len({event["trace_id"] for event in reloaded["task"]["causal_events"]}),
                1,
            )
        finally:
            os.chdir(previous_cwd)

    def test_causal_event_notes_do_not_emit_secret_shaped_strings(self) -> None:
        created = create_long_running_task("Secret-shaped event guard")
        task_id = created["task"]["id"]

        from source_proxy.tasks import long_running

        task = long_running._lookup_task(task_id)
        event = long_running._append_causal_event(
            task,
            event_type="status_transition",
            subsystem="source_proxy_long_running",
            notes=["token=abcd1234abcd1234abcd1234"],
        )

        self.assertNotIn("abcd1234abcd1234abcd1234", json.dumps(event))
        self.assertIn("[REDACTED]", event["notes"][0])

    def test_diff_hash_uses_canonical_lf_trailing_newline_normalization(self) -> None:
        lf_no_trailing = "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new"
        lf_trailing = f"{lf_no_trailing}\n"
        crlf_trailing = lf_trailing.replace("\n", "\r\n")

        baseline = _canonical_diff_sha256(lf_no_trailing)

        self.assertEqual(
            baseline,
            _canonical_diff_sha256(lf_trailing),
        )
        self.assertEqual(
            baseline,
            _canonical_diff_sha256(crlf_trailing),
        )

    def test_central_gate_failure_creates_failure_event_without_status_advance(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/gate.md", "w", encoding="utf-8") as handle:
                handle.write("# Gate\n\nBefore.\n")

            created = create_long_running_task("Append gate note")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/gate.md b/docs/gate.md",
                    "--- a/docs/gate.md",
                    "+++ b/docs/gate.md",
                    "@@ -1,3 +1,4 @@",
                    " # Gate",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )

            with mock.patch(
                "source_proxy.tasks.long_running.central_gate_check",
                side_effect=RuntimeError("central gate blocked"),
            ):
                with self.assertRaises(RuntimeError):
                    execute_approved_long_running_task(
                        task_id,
                        action="append docs note",
                        approval_id=_approval_id(task_id, diff, "docs/gate.md"),
                        approved_diff=diff,
                        target="docs/gate.md",
                    )

            readback = get_long_running_task_snapshot(task_id)
            self.assertEqual(readback["task"]["status"], "failed_needs_human")
            events = readback["task"]["causal_events"]
            self.assertEqual(events[0]["event_type"], "invocation")
            self.assertEqual(events[1]["event_type"], "failure")
            self.assertEqual(events[2]["event_type"], "consumer")
            self.assertEqual(events[0]["trace_id"], events[1]["trace_id"])
            self.assertEqual(events[1]["status_after"], "failed_needs_human")
            self.assertEqual(events[2]["status_after"], "failed_needs_human")
        finally:
            os.chdir(previous_cwd)

    def test_router_rejects_legacy_caller_approved_diff(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            created = client.post(
                "/v1/tasks/long-running",
                json={"description": "Apply approved route diff"},
            )
            task_id = created.json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )

            approval = client.post(
                f"/v1/tasks/long-running/{task_id}/approval",
                json={
                    "action": "modify file",
                    "approved": True,
                    "approved_by": "test",
                    "approved_diff": diff,
                    "target": "src/app/demo/page.tsx",
                    "selected_prompt_id": "legacy-test",
                    "context_hash": "legacy-test",
                },
            )
            self.assertEqual(approval.status_code, 410)
            self.assertEqual(approval.json()["detail"]["reason_code"], "approval_client_authority_removed")
            with open("src/app/demo/page.tsx", encoding="utf-8") as handle:
                self.assertIn("'old'", handle.read())
        finally:
            os.chdir(previous_cwd)

    def test_cancelling_task_invalidates_its_server_issued_approval(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Cancel durable approval"},
            ).json()["task"]["id"]
            diff = "\n".join([
                "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                "--- a/src/app/demo/page.tsx",
                "+++ b/src/app/demo/page.tsx",
                "@@ -1 +1 @@",
                "-export const value = 'old';",
                "+export const value = 'new';",
                "",
            ])
            approval_id = _approval_id(task_id, diff, "src/app/demo/page.tsx")
            record_coding_execution_approval(task_id, approval_id=approval_id, generation=1)
            cancelled = client.post(f"/v1/tasks/long-running/{task_id}/cancel")
            self.assertEqual(cancelled.status_code, 200)
            self.assertEqual(cancelled.json()["task"]["status"], "cancelled")
            self.assertEqual(
                cancelled.json()["task"]["ast_snapshot"]["campaign_2_pending_approval"]["state"],
                "cancelled",
            )
            rejected = client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "implement proposed file change", "approved": True, "approval_id": approval_id,
                    "approved_diff": diff, "target": "src/app/demo/page.tsx",
                    "selected_prompt_id": "legacy-test", "context_hash": "legacy-test",
                },
            )
            self.assertEqual(rejected.status_code, 422)
            self.assertEqual(rejected.json()["detail"]["reason_code"], "approval_cancelled")
        finally:
            os.chdir(previous_cwd)

    def test_execute_approved_rejects_stale_approval_id(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            created = create_long_running_task("Apply approved stale route diff")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )

            with self.assertRaises(LongRunningTaskError) as blocked:
                execute_approved_long_running_task(
                    task_id,
                    action="modify file",
                    approval_id="approval-stale",
                    approved_diff=diff,
                    target="src/app/demo/page.tsx",
                )

            self.assertEqual(blocked.exception.reason_code, "approval_not_found")
            diagnostic = blocked.exception.diagnostics
            self.assertEqual(diagnostic["stage_id"], "execute_approved.approval_binding")
            self.assertEqual(diagnostic["truth_status"], "BLOCKED_SAFE")
            self.assertTrue(diagnostic["safe_block"])
            self.assertEqual(diagnostic["reason_code"], "approval_not_found")
            self.assertEqual(diagnostic["apply_block_layer"], "source_proxy")
            self.assertIn("recommended_next_action", diagnostic)
            self.assertIn("unavailable_fields", diagnostic)
            self.assertEqual(
                diagnostic["approval_binding"]["approval_binding_status"],
                "failed",
            )
            self.assertTrue(
                diagnostic["approval_binding"]["approval_binding_safe_block"]
            )
            self.assertEqual(
                diagnostic["approval_binding"]["approval_binding_failure_reason"],
                "approval_not_found",
            )
            self.assertEqual(
                diagnostic["approval_binding"]["expected_approval_id"],
                "server-owned-durable-approval",
            )
            self.assertEqual(
                diagnostic["approval_binding"]["received_approval_id"],
                "approval-stale",
            )
            self.assertIn(
                diagnostic["approval_binding"]["task_id_match"],
                {True, "unknown"},
            )
            self.assertIn(
                diagnostic["approval_binding"]["target_match"],
                {True, "unknown"},
            )
            self.assertIn(
                diagnostic["approval_binding"]["diff_sha256_match"],
                {True, False, "unknown"},
            )
            self.assertEqual(
                diagnostic["anti_cheat"]["anti_cheat_status"],
                "not_run",
            )
            self.assertEqual(
                diagnostic["anti_cheat"]["anti_cheat_reasons"],
                ["skipped_due_to_apply_block"],
            )
            self.assertEqual(
                diagnostic["verification"]["post_apply_verification_status"],
                "skipped_due_to_apply_block",
            )
            self.assertEqual(
                diagnostic["acceptance_gate"]["binary_verdict"],
                "NO-GO",
            )
            self.assertEqual(
                diagnostic["acceptance_gate"]["phase_verifier_status"],
                "skipped_with_reason",
            )
            self.assertEqual(
                diagnostic["acceptance_gate"]["fail_closed_lane_status"],
                "skipped_with_reason",
            )
            self.assertEqual(
                diagnostic["acceptance_gate"]["causal_crosscheck_status"],
                "skipped_with_reason",
            )
            self.assertEqual(
                diagnostic["final_truth_summary"]["truth_status"],
                "BLOCKED_SAFE",
            )
            poll_payload = get_long_running_task_snapshot(task_id)
            self.assertEqual(poll_payload["truth_status"], "BLOCKED_SAFE")
            self.assertEqual(
                poll_payload["approval_binding_status"],
                "failed",
            )
            self.assertEqual(
                poll_payload["expected_approval_id"],
                "server-owned-durable-approval",
            )
            self.assertEqual(poll_payload["received_approval_id"], "approval-stale")
            self.assertEqual(poll_payload["safe_block"], True)
            self.assertEqual(poll_payload["anti_cheat_status"], "not_run")
            self.assertEqual(
                poll_payload["anti_cheat_reasons"],
                ["skipped_due_to_apply_block"],
            )
            self.assertEqual(
                poll_payload["task"]["approval_binding_status"],
                "failed",
            )
            blocked_receipt_path = os.path.join("data", "blocked_actions.audit.jsonl")
            self.assertTrue(os.path.exists(blocked_receipt_path))
            with open(blocked_receipt_path, encoding="utf-8") as handle:
                receipt = json.loads(handle.readlines()[-1])
            self.assertEqual(receipt["task_id"], task_id)
            self.assertEqual(receipt["truth_status"], "BLOCKED_SAFE")
            self.assertTrue(receipt["safe_block"])
            self.assertEqual(receipt["reason_code"], "approval_not_found")
            self.assertEqual(receipt["approval_id"], "approval-stale")
            self.assertEqual(
                receipt["expected_approval_id"],
                "server-owned-durable-approval",
            )
            self.assertEqual(
                receipt["anti_cheat"]["anti_cheat_reasons"],
                ["skipped_due_to_apply_block"],
            )
            with open("src/app/demo/page.tsx", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "export const value = 'old';\n")
        finally:
            os.chdir(previous_cwd)

    def test_execute_approved_api_preserves_approval_mismatch_envelope(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            created = client.post(
                "/v1/tasks/long-running",
                json={"description": "Apply approved stale route diff"},
            )
            task_id = created.json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )

            blocked = client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "modify file",
                    "approval_id": "approval-stale",
                    "approved": True,
                    "approved_diff": diff,
                    "target": "src/app/demo/page.tsx",
                    "selected_prompt_id": "legacy-test",
                    "context_hash": "legacy-test",
                },
            )

            self.assertEqual(blocked.status_code, 422)
            detail = blocked.json()["detail"]
            self.assertEqual(detail["truth_status"], "BLOCKED_SAFE")
            self.assertEqual(detail["approval_binding"]["approval_binding_status"], "failed")
            self.assertEqual(detail["anti_cheat"]["anti_cheat_reasons"], ["skipped_due_to_apply_block"])
            self.assertEqual(detail["acceptance_gate"]["phase_verifier_status"], "skipped_with_reason")

            poll = client.get(f"/v1/tasks/long-running/{task_id}").json()
            self.assertEqual(poll["truth_status"], "BLOCKED_SAFE")
            self.assertEqual(poll["approval_binding_status"], "failed")
            self.assertEqual(poll["task"]["status"], "blocked_approval_mismatch")
            self.assertEqual(poll["task"]["anti_cheat_status"], "not_run")

            with client.stream(
                "GET",
                f"/v1/tasks/long-running/{task_id}/stream?max_events=10&interval_seconds=0.1",
            ) as response:
                stream_text = response.read().decode("utf-8")
            self.assertIn("event: task", stream_text)
            self.assertIn('"truth_status": "BLOCKED_SAFE"', stream_text)
            self.assertIn('"approval_binding_status": "failed"', stream_text)
            self.assertIn('"status": "blocked_approval_mismatch"', stream_text)
        finally:
            os.chdir(previous_cwd)

    def test_execute_approved_does_not_create_commit_or_push(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            subprocess.run(["git", "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], check=True)
            os.makedirs("docs", exist_ok=True)
            with open("docs/apply.md", "w", encoding="utf-8") as handle:
                handle.write("# Apply\n\nBefore.\n")
            subprocess.run(["git", "add", "docs/apply.md"], check=True)
            subprocess.run(["git", "commit", "-m", "initial"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout.strip()

            created = create_long_running_task("Append docs apply note")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/apply.md b/docs/apply.md",
                    "--- a/docs/apply.md",
                    "+++ b/docs/apply.md",
                    "@@ -1,3 +1,4 @@",
                    " # Apply",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )
            payload = execute_approved_long_running_task(
                task_id,
                action="append docs note",
                approval_id=_approval_id(task_id, diff, "docs/apply.md"),
                approved_diff=diff,
                target="docs/apply.md",
            )
            head_after = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout.strip()

            self.assertEqual(head_after, head_before)
            self.assertFalse(payload["execution"]["commit_created"])
            self.assertFalse(payload["execution"]["push_ran"])
            status = subprocess.run(
                ["git", "status", "--short"],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout
            self.assertIn(" M docs/apply.md", status)
        finally:
            os.chdir(previous_cwd)

    def test_post_apply_verification_failure_prevents_completed(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            created = create_long_running_task("Apply approved route diff")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            execute_approved_long_running_task(
                task_id,
                action="modify file",
                approval_id=_approval_id(task_id, diff, "src/app/demo/page.tsx"),
                approved_diff=diff,
                target="src/app/demo/page.tsx",
            )

            failed = record_post_apply_verification(
                task_id,
                checks=[
                    {
                        "id": "typecheck",
                        "status": "failed",
                        "summary": "TypeScript failed.",
                    }
                ],
            )

            self.assertEqual(failed["task"]["status"], "verification_failed")
            self.assertEqual(
                failed["task"]["post_apply_verification"]["status"],
                "verification_failed",
            )
            self.assertTrue(
                failed["task"]["post_apply_verification"]["commit_proposal_blocked"]
            )
            self.assertIn(
                "post_apply_verification_failed",
                failed["task"]["post_apply_verification"]["commit_blockers"],
            )
            self.assertFalse(
                failed["task"]["post_apply_verification"]["push_path_available"]
            )
            self.assertNotEqual(failed["task"]["status"], "completed")
        finally:
            os.chdir(previous_cwd)

    def test_docs_only_post_apply_verification_requires_explicit_confirmations(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/phase-2a.md", "w", encoding="utf-8") as handle:
                handle.write("# Phase 2A\n\nPending verification.\n")

            created = create_long_running_task("Append docs-only verification note")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/phase-2a.md b/docs/phase-2a.md",
                    "--- a/docs/phase-2a.md",
                    "+++ b/docs/phase-2a.md",
                    "@@ -1,3 +1,4 @@",
                    " # Phase 2A",
                    " ",
                    " Pending verification.",
                    "+Docs-only change verified.",
                    "",
                ]
            )
            applied = execute_approved_long_running_task(
                task_id,
                action="append docs note",
                approval_id=_approval_id(task_id, diff, "docs/phase-2a.md"),
                approved_diff=diff,
                target="docs/phase-2a.md",
            )

            self.assertEqual(applied["task"]["status"], "applied_needs_verification")
            self.assertTrue(applied["task"]["post_apply_verification"]["docs_only"])

            with self.assertRaises(LongRunningTaskError) as missing:
                record_post_apply_verification(task_id)
            self.assertEqual(
                missing.exception.reason_code,
                "missing_post_apply_confirmations",
            )

            completed = record_post_apply_verification(
                task_id,
                confirm_backup_audit_present=True,
                confirm_changed_files_reviewed=True,
                confirm_expected_change_present=True,
                confirm_no_unintended_files=True,
                verification_note="Docs-only change verified.",
            )
            verification = completed["task"]["post_apply_verification"]
            self.assertEqual(completed["task"]["status"], "completed")
            self.assertEqual(verification["status"], "verified")
            self.assertFalse(verification["commit_proposal_blocked"])
            self.assertEqual(verification["commit_blockers"], [])
            self.assertFalse(verification["push_path_available"])
            self.assertEqual(verification["push_blockers"], ["push_requires_separate_approval"])
            self.assertEqual(
                verification["verification_note"],
                "Docs-only change verified.",
            )
            self.assertTrue(
                verification["docs_only_confirmations"]["file_changed_as_expected"]
            )
            self.assertTrue(
                verification["docs_only_confirmations"]["backup_audit_present"]
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_verify_completes_docs_only_post_apply_verification(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/router-verify.md", "w", encoding="utf-8") as handle:
                handle.write("# Router Verify\n\nBefore.\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Append router verification docs note"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/router-verify.md b/docs/router-verify.md",
                    "--- a/docs/router-verify.md",
                    "+++ b/docs/router-verify.md",
                    "@@ -1,3 +1,4 @@",
                    " # Router Verify",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )
            client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "append docs note",
                    "approval_id": _approval_id(task_id, diff, "docs/router-verify.md"),
                    "approved": True,
                    "approved_diff": diff,
                    "target": "docs/router-verify.md",
                    "selected_prompt_id": "legacy-test",
                    "context_hash": "legacy-test",
                },
            )

            response = client.post(
                f"/v1/tasks/long-running/{task_id}/verify",
                json={
                    "confirm_backup_audit_present": True,
                    "confirm_changed_files_reviewed": True,
                    "confirm_expected_change_present": True,
                    "confirm_no_unintended_files": True,
                    "verification_note": "Docs-only change verified.",
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["task"]["status"], "completed")
            self.assertEqual(
                response.json()["task"]["post_apply_verification"]["status"],
                "verified",
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_verify_rejects_missing_docs_confirmations(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/missing-confirm.md", "w", encoding="utf-8") as handle:
                handle.write("# Missing Confirm\n\nBefore.\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Append docs note"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/missing-confirm.md b/docs/missing-confirm.md",
                    "--- a/docs/missing-confirm.md",
                    "+++ b/docs/missing-confirm.md",
                    "@@ -1,3 +1,4 @@",
                    " # Missing Confirm",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )
            client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "append docs note",
                    "approval_id": _approval_id(task_id, diff, "docs/missing-confirm.md"),
                    "approved": True,
                    "approved_diff": diff,
                    "target": "docs/missing-confirm.md",
                    "selected_prompt_id": "legacy-test",
                    "context_hash": "legacy-test",
                },
            )

            response = client.post(
                f"/v1/tasks/long-running/{task_id}/verify",
                json={
                    "confirm_expected_change_present": True,
                    "confirm_no_unintended_files": True,
                },
            )

            self.assertEqual(response.status_code, 422)
            self.assertEqual(
                response.json()["detail"]["reason_code"],
                "missing_post_apply_confirmations",
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_verify_rejects_unapplied_task(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)
        task_id = client.post(
            "/v1/tasks/long-running",
            json={"description": "Task has not been applied"},
        ).json()["task"]["id"]

        response = client.post(
            f"/v1/tasks/long-running/{task_id}/verify",
            json={
                "confirm_backup_audit_present": True,
                "confirm_expected_change_present": True,
                "confirm_no_unintended_files": True,
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["detail"]["reason_code"],
            "invalid_post_apply_verification_state",
        )

    def test_router_code_verify_rejects_unapplied_task(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)
        task_id = client.post(
            "/v1/tasks/long-running",
            json={"description": "Task has not been applied"},
        ).json()["task"]["id"]

        response = client.post(
            f"/v1/tasks/long-running/{task_id}/verify",
            json={"run_code_verification": True},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["detail"]["reason_code"],
            "invalid_post_apply_verification_state",
        )

    def test_router_verify_runs_allowlisted_code_verification(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/lib/coding/__tests__", exist_ok=True)
            with open("package.json", "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "scripts": {
                            "test:coding-frontend-regression": "vitest run coding",
                        }
                    },
                    handle,
                )
            with open(
                "src/lib/coding/__tests__/unified-diff-paths.test.ts",
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("export const value = 'old';\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Update coding frontend test"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/lib/coding/__tests__/unified-diff-paths.test.ts b/src/lib/coding/__tests__/unified-diff-paths.test.ts",
                    "--- a/src/lib/coding/__tests__/unified-diff-paths.test.ts",
                    "+++ b/src/lib/coding/__tests__/unified-diff-paths.test.ts",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            applied = client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "modify coding test",
                    "approval_id": _approval_id(
                        task_id,
                        diff,
                        "src/lib/coding/__tests__/unified-diff-paths.test.ts",
                    ),
                    "approved": True,
                    "approved_diff": diff,
                    "target": "src/lib/coding/__tests__/unified-diff-paths.test.ts",
                    "selected_prompt_id": "legacy-test",
                    "context_hash": "legacy-test",
                },
            )
            applied_verification = applied.json()["task"]["post_apply_verification"]
            self.assertEqual(applied_verification["status"], "verification_ready")
            self.assertEqual(
                [check["id"] for check in applied_verification["checks"]],
                ["coding_frontend_regression", "typescript_typecheck"],
            )
            self.assertTrue(
                all(check["status"] == "pending" for check in applied_verification["checks"])
            )

            completed_process = mock.Mock()
            completed_process.returncode = 0
            completed_process.stdout = "ok"
            completed_process.stderr = ""
            with mock.patch(
                "source_proxy.tasks.long_running.subprocess.run",
                return_value=completed_process,
            ) as run_mock:
                response = client.post(
                    f"/v1/tasks/long-running/{task_id}/verify",
                    json={"run_code_verification": True},
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["task"]["status"], "completed")
            verification = payload["task"]["post_apply_verification"]
            self.assertEqual(verification["status"], "verified")
            self.assertEqual(
                [check["id"] for check in verification["checks"]],
                ["coding_frontend_regression", "typescript_typecheck"],
            )
            self.assertEqual(
                [call.args[0] for call in run_mock.call_args_list],
                [
                    ["npm", "run", "test:coding-frontend-regression"],
                    ["npx", "tsc", "--noEmit", "-p", "tsconfig.json"],
                ],
            )
            self.assertTrue(
                all(check["status"] == "passed" for check in verification["checks"])
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_code_verify_failure_records_output_without_completion(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("package.json", "w", encoding="utf-8") as handle:
                json.dump({"scripts": {}}, handle)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Update route code"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "modify route",
                    "approval_id": _approval_id(task_id, diff, "src/app/demo/page.tsx"),
                    "approved": True,
                    "approved_diff": diff,
                    "target": "src/app/demo/page.tsx",
                    "selected_prompt_id": "legacy-test",
                    "context_hash": "legacy-test",
                },
            )

            failed_process = mock.Mock()
            failed_process.returncode = 1
            failed_process.stdout = ""
            failed_process.stderr = "x" * 4100 + "TYPECHECK_FAILED_TAIL"
            with mock.patch(
                "source_proxy.tasks.long_running.subprocess.run",
                return_value=failed_process,
            ):
                response = client.post(
                    f"/v1/tasks/long-running/{task_id}/verify",
                    json={"run_code_verification": True},
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["task"]["status"], "verification_failed")
            self.assertNotEqual(payload["task"]["status"], "completed")
            verification = payload["task"]["post_apply_verification"]
            self.assertEqual(verification["status"], "verification_failed")
            failed_check = verification["checks"][0]
            self.assertEqual(failed_check["id"], "typescript_typecheck")
            self.assertEqual(failed_check["status"], "failed")
            self.assertLessEqual(len(failed_check["output_tail"]), 4000)
            self.assertIn("TYPECHECK_FAILED_TAIL", failed_check["output_tail"])
            with open("src/app/demo/page.tsx", encoding="utf-8") as handle:
                self.assertIn("'new'", handle.read())
        finally:
            os.chdir(previous_cwd)

    def test_code_verify_keeps_route_change_pending_until_browser_review(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            created = create_long_running_task("Apply route change requiring browser review")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            applied = execute_approved_long_running_task(
                task_id,
                action="modify route file",
                approval_id=_approval_id(task_id, diff, "src/app/demo/page.tsx"),
                approved_diff=diff,
                target="src/app/demo/page.tsx",
            )
            self.assertEqual(applied["task"]["status"], "applied_needs_verification")
            self.assertTrue(
                applied["task"]["post_apply_verification"][
                    "manual_browser_check_required"
                ]
            )

            completed_process = mock.Mock()
            completed_process.returncode = 0
            completed_process.stdout = "ok"
            completed_process.stderr = ""
            with mock.patch(
                "source_proxy.tasks.long_running.subprocess.run",
                return_value=completed_process,
            ):
                pending = record_post_apply_verification(
                    task_id,
                    run_code_verification=True,
                )

            verification = pending["task"]["post_apply_verification"]
            self.assertEqual(pending["task"]["status"], "applied_needs_verification")
            self.assertEqual(verification["status"], "verification_ready")
            self.assertTrue(verification["commit_proposal_blocked"])
            self.assertEqual(
                verification["commit_blockers"],
                ["post_apply_verification_incomplete"],
            )
            self.assertTrue(verification["manual_browser_check_required"])
            self.assertFalse(verification["manual_browser_check_done"])
            self.assertFalse(verification["push_path_available"])
            self.assertEqual(
                verification["push_blockers"],
                ["push_requires_separate_approval"],
            )
            self.assertEqual(
                pending["task"]["open_diffs"][0]["status"],
                "applied_needs_verification",
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_code_verify_rejects_docs_only_task(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/code-verify-docs.md", "w", encoding="utf-8") as handle:
                handle.write("# Docs\n\nBefore.\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Append docs note"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/code-verify-docs.md b/docs/code-verify-docs.md",
                    "--- a/docs/code-verify-docs.md",
                    "+++ b/docs/code-verify-docs.md",
                    "@@ -1,3 +1,4 @@",
                    " # Docs",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )
            client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "append docs note",
                    "approval_id": _approval_id(task_id, diff, "docs/code-verify-docs.md"),
                    "approved": True,
                    "approved_diff": diff,
                    "target": "docs/code-verify-docs.md",
                    "selected_prompt_id": "legacy-test",
                    "context_hash": "legacy-test",
                },
            )

            response = client.post(
                f"/v1/tasks/long-running/{task_id}/verify",
                json={"run_code_verification": True},
            )

            self.assertEqual(response.status_code, 422)
            self.assertEqual(
                response.json()["detail"]["reason_code"],
                "code_verification_not_applicable",
            )
        finally:
            os.chdir(previous_cwd)

    def test_unsupported_code_file_requires_manual_verification(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            with open("source_proxy/demo.py", "w", encoding="utf-8") as handle:
                handle.write("VALUE = 'old'\n")

            app = FastAPI()
            app.include_router(long_running_tasks_router)
            client = TestClient(app)
            task_id = client.post(
                "/v1/tasks/long-running",
                json={"description": "Update Python file"},
            ).json()["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/source_proxy/demo.py b/source_proxy/demo.py",
                    "--- a/source_proxy/demo.py",
                    "+++ b/source_proxy/demo.py",
                    "@@ -1 +1 @@",
                    "-VALUE = 'old'",
                    "+VALUE = 'new'",
                    "",
                ]
            )
            applied = client.post(
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                json={
                    "action": "modify python",
                    "approval_id": _approval_id(task_id, diff, "source_proxy/demo.py"),
                    "approved": True,
                    "approved_diff": diff,
                    "target": "source_proxy/demo.py",
                    "selected_prompt_id": "legacy-test",
                    "context_hash": "legacy-test",
                },
            )

            self.assertEqual(applied.status_code, 200)
            verification = applied.json()["task"]["post_apply_verification"]
            self.assertEqual(verification["status"], "manual_verification_required")
            self.assertTrue(verification["unsupported_code_verification"])
            self.assertEqual(verification["unsupported_file_types"], [".py"])

            response = client.post(
                f"/v1/tasks/long-running/{task_id}/verify",
                json={"run_code_verification": True},
            )

            self.assertEqual(response.status_code, 422)
            self.assertEqual(
                response.json()["detail"]["reason_code"],
                "unsupported_code_verification_type",
            )
            self.assertEqual(
                get_long_running_task(task_id)["task"]["status"],
                "applied_needs_verification",
            )
        finally:
            os.chdir(previous_cwd)

    def test_docs_only_verification_preserves_audit_and_backup_metadata(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("docs", exist_ok=True)
            with open("docs/preserve.md", "w", encoding="utf-8") as handle:
                handle.write("# Preserve\n\nBefore.\n")

            created = create_long_running_task("Append docs preserve note")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/docs/preserve.md b/docs/preserve.md",
                    "--- a/docs/preserve.md",
                    "+++ b/docs/preserve.md",
                    "@@ -1,3 +1,4 @@",
                    " # Preserve",
                    " ",
                    " Before.",
                    "+After.",
                    "",
                ]
            )
            applied = execute_approved_long_running_task(
                task_id,
                action="append docs note",
                approval_id=_approval_id(task_id, diff, "docs/preserve.md"),
                approved_diff=diff,
                target="docs/preserve.md",
            )
            before = applied["task"]["ast_snapshot"]["approved_execution_evidence"]

            completed = record_post_apply_verification(
                task_id,
                confirm_backup_audit_present=True,
                confirm_expected_change_present=True,
                confirm_no_unintended_files=True,
            )
            after = completed["task"]["ast_snapshot"]["approved_execution_evidence"]

            self.assertEqual(after["audit"], before["audit"])
            self.assertEqual(after["backup_root"], before["backup_root"])
            verification = json.loads(completed["task"]["truncated_test_results"])
            self.assertEqual(verification["post_apply_verification"]["status"], "verified")
        finally:
            os.chdir(previous_cwd)

    def test_code_file_changed_task_is_not_completed_by_docs_checklist(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            created = create_long_running_task("Apply approved route diff")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            execute_approved_long_running_task(
                task_id,
                action="modify file",
                approval_id=_approval_id(task_id, diff, "src/app/demo/page.tsx"),
                approved_diff=diff,
                target="src/app/demo/page.tsx",
            )

            with self.assertRaises(LongRunningTaskError) as blocked:
                record_post_apply_verification(
                    task_id,
                    confirm_backup_audit_present=True,
                    confirm_expected_change_present=True,
                    confirm_no_unintended_files=True,
                )

            self.assertEqual(
                blocked.exception.reason_code,
                "code_verification_not_implemented",
            )
            self.assertEqual(
                get_long_running_task(task_id)["task"]["status"],
                "applied_needs_verification",
            )
        finally:
            os.chdir(previous_cwd)

    def test_post_apply_verification_skip_requires_reason_to_complete(self) -> None:
        previous_cwd = os.getcwd()
        try:
            os.chdir(self._tempdir.name)
            os.makedirs("src/app/demo", exist_ok=True)
            with open("src/app/demo/page.tsx", "w", encoding="utf-8") as handle:
                handle.write("export const value = 'old';\n")

            created = create_long_running_task("Apply approved route diff")
            task_id = created["task"]["id"]
            diff = "\n".join(
                [
                    "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                    "--- a/src/app/demo/page.tsx",
                    "+++ b/src/app/demo/page.tsx",
                    "@@ -1 +1 @@",
                    "-export const value = 'old';",
                    "+export const value = 'new';",
                    "",
                ]
            )
            execute_approved_long_running_task(
                task_id,
                action="modify file",
                approval_id=_approval_id(task_id, diff, "src/app/demo/page.tsx"),
                approved_diff=diff,
                target="src/app/demo/page.tsx",
            )

            with self.assertRaises(LongRunningTaskError) as blocked:
                record_post_apply_verification(
                    task_id,
                    checks=[{"id": "typecheck", "status": "skipped"}],
                    manual_browser_check_done=False,
                )
            self.assertEqual(
                blocked.exception.reason_code,
                "code_verification_not_implemented",
            )

            completed = record_post_apply_verification(
                task_id,
                checks=[
                    {"id": "typecheck", "status": "skipped"},
                    {"id": "lint", "status": "skipped"},
                ],
                manual_browser_check_done=False,
                skip_reason="Verified externally in CI.",
            )
            self.assertEqual(completed["task"]["status"], "completed")
            self.assertEqual(
                completed["task"]["post_apply_verification"]["status"],
                "verified",
            )
        finally:
            os.chdir(previous_cwd)

    def test_router_streams_swarm_telemetry_as_sse(self) -> None:
        app = FastAPI()
        app.include_router(long_running_tasks_router)
        client = TestClient(app)

        created = client.post(
            "/v1/tasks/long-running",
            json={
                "description": "Target file: source_proxy/main.py\nStream handoff telemetry"
            },
        )
        task_id = created.json()["task"]["id"]
        client.post(f"/v1/tasks/long-running/{task_id}/advance", json={})

        with client.stream(
            "GET",
            f"/v1/tasks/long-running/{task_id}/stream?max_events=1",
        ) as response:
            body = response.read().decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        self.assertIn("event: task", body)
        self.assertIn("event: role_transition", body)
        data_line = next(line for line in body.splitlines() if line.startswith("data: "))
        payload = json.loads(data_line.removeprefix("data: "))
        self.assertEqual(payload["task"]["current_agent_role"], "coder")
        self.assertEqual(payload["task"]["cycle_count"], 0)
        role_transition_lines = [
            line.removeprefix("data: ")
            for index, line in enumerate(body.splitlines())
            if line.startswith("data: ")
            and index > 0
            and body.splitlines()[index - 1] == "event: role_transition"
        ]
        role_transition = json.loads(role_transition_lines[0])
        self.assertEqual(role_transition["from"], "architect")
        self.assertEqual(role_transition["to"], "coder")
        self.assertEqual(role_transition["reason"], "architect_plan_ready")

    def test_swarm_halts_at_cycle_five_when_sandbox_keeps_failing(self) -> None:
        created = create_long_running_task(
            "Target file: source_proxy/main.py\nStop an endless failing loop"
        )
        task_id = created["task"]["id"]
        advance_long_running_task(task_id)
        diff = "\n".join(
            [
                "diff --git a/source_proxy/main.py b/source_proxy/main.py",
                "--- a/source_proxy/main.py",
                "+++ b/source_proxy/main.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
                "",
            ]
        )

        payload = None
        for cycle in range(1, 6):
            advance_long_running_task(task_id, proposed_diff=diff)
            payload = advance_long_running_task(
                task_id,
                sandbox_result={
                    "returncode": 1,
                    "stdout": "",
                    "stderr": f"failure {cycle}",
                },
            )

        assert payload is not None
        task = payload["task"]
        self.assertEqual(task["cycle_count"], 5)
        self.assertEqual(task["status"], "failed_needs_human")
        self.assertEqual(task["current_agent_role"], "debugger")
        self.assertIn("safety cycle limit", task["next_action"])

        still_failed = advance_long_running_task(
            task_id,
            sandbox_result={"returncode": 0, "stdout": "late pass", "stderr": ""},
        )
        self.assertEqual(still_failed["task"]["cycle_count"], 5)
        self.assertEqual(still_failed["task"]["status"], "failed_needs_human")

    def test_coder_config_blocked_status_uses_terminal_progress_band(self) -> None:
        created = create_long_running_task("Coder config smoke")
        task_id = created["task"]["id"]
        update_long_running_task(task_id, status="coder_config_blocked", poll_count=3)
        payload = get_long_running_task(task_id)
        self.assertEqual(payload["task"]["status"], "coder_config_blocked")
        self.assertLessEqual(payload["task"]["progress"], 95)
        self.assertGreaterEqual(payload["task"]["progress"], 50)
        self.assertIn("SOURCE_PROXY_CODER_MODEL_ALIAS", payload["task"]["next_action"])

    def test_managed_dummy_browser_verifier_is_pinned_to_port_3000(self) -> None:
        workspace = Path(self._tempdir.name).resolve()
        script = workspace / "scripts/verify-dummy-storefront-browser.mjs"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("// test placeholder\n", encoding="utf-8")
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(_passing_managed_browser_proof()),
            stderr="",
        )
        with mock.patch.object(
            long_running_module.subprocess,
            "run",
            return_value=completed,
        ) as run_mock:
            proof = long_running_module._run_managed_dummy_storefront_browser_proof(
                workspace
            )

        command = run_mock.call_args.args[0]
        self.assertEqual(command[0], "node")
        self.assertEqual(command[1], str(script.resolve()))
        self.assertEqual(command[2:4], ["--url", "https://localhost:3000/v1/coding/dummy-product-site-preview"])
        self.assertNotIn("3100", " ".join(command))
        self.assertEqual(run_mock.call_args.kwargs["cwd"], workspace)
        self.assertEqual(proof["storefront_runtime_engine"], "playwright_chromium")
        self.assertTrue(proof["real_browser_used"])

    def _apply_and_verify_manifest_backed_dummy_fixture(
        self,
        managed_browser_proof: dict[str, object] | None = None,
        *,
        tamper_manifest_before_postapply: bool = False,
    ) -> dict[str, object]:
        workspace = Path(self._tempdir.name).resolve()
        fixture = workspace / "tests/ui-agent-trials/fixtures/dummy-product-site"
        fixture.mkdir(parents=True, exist_ok=True)
        readme_before = "# Prior fixture\n\nPreserve this exact prior state.\n"
        (fixture / "README.md").write_text(readme_before, encoding="utf-8")
        sentinel = workspace / "unrelated-sentinel.txt"
        sentinel.write_text("unrelated user state\n", encoding="utf-8")

        diff, applied_contents = _dummy_product_site_lifecycle_diff(readme_before)
        created = create_long_running_task(
            "Target file: tests/ui-agent-trials/fixtures/dummy-product-site/\n"
            "Run selected dummy coder prompt 1."
        )
        task_id = created["task"]["id"]
        context_report = build_context_broker_report(
            [
                {
                    "source": "supplied_context",
                    "status": "used",
                    "reason": "selected_prompt_context_supplied",
                    "considered": True,
                    "required": True,
                    "selected": True,
                    "included": True,
                }
            ],
            downstream_consumers={
                "planner": {
                    "applicable": True,
                    "acknowledged": True,
                    "sources": ["supplied_context"],
                    "evidence": "planner_built_context_bound_task",
                },
                "coder": {
                    "applicable": True,
                    "acknowledged": True,
                    "sources": ["supplied_context"],
                    "evidence": "coder_authored_context_bound_diff",
                },
            },
            applicable_consumers=("planner", "coder", "reviewer"),
        )
        long_running_module.record_canonical_context_broker(task_id, context_report)

        previous_cwd = os.getcwd()
        try:
            os.chdir(workspace)
            applied = execute_approved_long_running_task(
                task_id,
                action="Run selected dummy coder prompt 1",
                approval_id=_approval_id(
                    task_id,
                    diff,
                    "tests/ui-agent-trials/fixtures/dummy-product-site/",
                ),
                approved_diff=diff,
                target="tests/ui-agent-trials/fixtures/dummy-product-site/",
            )
            manifest_rel = applied["task"]["ast_snapshot"][
                "approved_execution_evidence"
            ]["backup_manifest"]
            if tamper_manifest_before_postapply:
                manifest_path = workspace / manifest_rel
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["rollback_hint"] = "tampered after approved apply"
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            with mock.patch.object(
                long_running_module,
                "_run_managed_dummy_storefront_browser_proof",
                return_value=managed_browser_proof or _passing_managed_browser_proof(),
            ):
                verified = record_post_apply_verification(
                    task_id,
                    verification_profile="dummy_product_site",
                    run_snapshot_verification=True,
                    browser_evidence={
                        "browser_verification_status": "passed",
                        "product_count": 999,
                        "storefront_runtime_engine": "frontend_simulation",
                    },
                )
        finally:
            os.chdir(previous_cwd)
        return {
            "workspace": workspace,
            "fixture": fixture,
            "readme_before": readme_before,
            "sentinel": sentinel,
            "diff": diff,
            "applied_contents": applied_contents,
            "task_id": task_id,
            "manifest_rel": manifest_rel,
            "verified": verified,
        }

    def test_dummy_manifest_postapply_syncs_evidence_context_and_exact_undo(self) -> None:
        lifecycle = self._apply_and_verify_manifest_backed_dummy_fixture()
        workspace = lifecycle["workspace"]
        fixture = lifecycle["fixture"]
        task_id = lifecycle["task_id"]
        manifest_rel = lifecycle["manifest_rel"]
        verified = lifecycle["verified"]
        assert isinstance(workspace, Path)
        assert isinstance(fixture, Path)
        assert isinstance(task_id, str)
        assert isinstance(manifest_rel, str)
        assert isinstance(verified, dict)

        task = verified["task"]
        verification = task["post_apply_verification"]
        snapshot = task["ast_snapshot"]
        execution_evidence = snapshot["approved_execution_evidence"]
        context_report = snapshot["canonical_context_broker"]
        manifest_path = workspace / manifest_rel
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(task["status"], "completed")
        self.assertEqual(verification["status"], "verified")
        self.assertEqual(snapshot["post_apply_verification"], verification)
        self.assertEqual(execution_evidence["post_apply_verification"], verification)
        self.assertEqual(len(task["open_diffs"]), 1)
        self.assertEqual(task["open_diffs"][0]["status"], "verified")
        self.assertEqual(manifest["post_apply_verification"], verification)
        self.assertEqual(execution_evidence["final_truth_status"], "GO")
        self.assertTrue(execution_evidence["commit_safe"])
        self.assertEqual(manifest["stage"], "post_apply_verified")
        self.assertEqual(manifest["final_truth_status"], "GO")
        self.assertTrue(manifest["commit_safe"])
        finalized_manifest_sha256 = long_running_module._sha256_file(manifest_path)
        self.assertEqual(
            execution_evidence["backup_manifest_sha256"],
            finalized_manifest_sha256,
        )
        self.assertEqual(
            execution_evidence["backup_manifest_finalized_sha256"],
            finalized_manifest_sha256,
        )
        self.assertNotEqual(
            execution_evidence["backup_manifest_applied_sha256"],
            finalized_manifest_sha256,
        )
        browser_evidence = verification["browser_evidence"]
        self.assertEqual(
            browser_evidence["storefront_runtime_engine"],
            "playwright_chromium",
        )
        self.assertTrue(browser_evidence["real_browser_used"])
        self.assertEqual(browser_evidence["managed_frontend_origin"], "https://localhost:3000")
        self.assertEqual(browser_evidence["task_id"], task_id)
        self.assertEqual(
            browser_evidence["backup_manifest_sha256"],
            execution_evidence["backup_manifest_applied_sha256"],
        )
        self.assertEqual(browser_evidence["product_count"], 6)
        self.assertNotEqual(browser_evidence["product_count"], 999)
        self.assertFalse(verification["client_browser_evidence_decision_bearing"])
        self.assertTrue(
            verification["snapshot_verification"]["client_browser_evidence_ignored"]
        )
        self.assertEqual(manifest["browser_evidence"], browser_evidence)
        self.assertEqual(
            verification["browser_evidence_sha256"],
            browser_evidence["browser_evidence_sha256"],
        )
        self.assertTrue(context_report["go_eligible"])
        self.assertEqual(context_report["verdict"], "GO_ELIGIBLE")
        self.assertEqual(context_report["consumed_sources"], ["supplied_context"])
        self.assertTrue(
            context_report["downstream_acknowledgements"]["verifier"][
                "acknowledged"
            ]
        )
        self.assertTrue(
            context_report["downstream_acknowledgements"]["final_receipt_builder"][
                "acknowledged"
            ]
        )
        self.assertEqual(
            manifest["canonical_context_report_hash"],
            context_report["canonical_report_hash"],
        )
        undo = long_running_module.undo_last_approved_change(
            task_id,
            confirm_undo=True,
            expected_backup_manifest=manifest_rel,
            requested_by="lifecycle-test",
        )

        self.assertEqual(
            (fixture / "README.md").read_text(encoding="utf-8"),
            lifecycle["readme_before"],
        )
        self.assertEqual(
            sorted(
                str(path.relative_to(fixture)).replace("\\", "/")
                for path in fixture.rglob("*")
                if path.is_file()
            ),
            ["README.md"],
        )
        self.assertFalse((fixture / "src").exists())
        self.assertEqual(
            lifecycle["sentinel"].read_text(encoding="utf-8"),
            "unrelated user state\n",
        )
        receipt = undo["undo"]
        self.assertTrue(receipt["filesystem_verified"])
        self.assertEqual(receipt["unrelated_paths_touched"], [])
        self.assertTrue(receipt["untouched_scope_assertion"])
        self.assertEqual(len(receipt["files_restored"]), 6)
        self.assertTrue(all(item["verified"] for item in receipt["files_restored"]))
        self.assertTrue((workspace / receipt["receipt_path"]).is_file())
        undone_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(undone_manifest["stage"], "undone")
        self.assertEqual(
            undone_manifest["undo_receipt"]["undo_receipt_id"],
            receipt["undo_receipt_id"],
        )
        undone_evidence = undo["task"]["ast_snapshot"]["approved_execution_evidence"]
        self.assertEqual(
            undone_evidence["backup_manifest_sha256"],
            long_running_module._sha256_file(manifest_path),
        )
        self.assertEqual(
            undone_evidence["backup_manifest_undone_sha256"],
            undone_evidence["backup_manifest_sha256"],
        )
        undone_open_diffs = undo["task"]["open_diffs"]
        self.assertEqual(len(undone_open_diffs), 1)
        self.assertEqual(undone_open_diffs[0]["status"], "undone")
        self.assertFalse(undone_open_diffs[0]["verified"])
        self.assertEqual(
            undone_open_diffs[0]["undo_receipt_id"],
            receipt["undo_receipt_id"],
        )
        self.assertEqual(
            undone_open_diffs[0]["undo_receipt_path"],
            receipt["receipt_path"],
        )

    def test_dummy_postapply_uses_the_exact_applied_root_when_project_roots_differ(self) -> None:
        with tempfile.TemporaryDirectory() as unrelated_project_root:
            with mock.patch.dict(
                os.environ,
                {"SPIRIT_PROJECT_PATH": unrelated_project_root},
                clear=False,
            ):
                lifecycle = self._apply_and_verify_manifest_backed_dummy_fixture()

        verified = lifecycle["verified"]
        workspace = lifecycle["workspace"]
        assert isinstance(verified, dict)
        assert isinstance(workspace, Path)
        evidence = verified["task"]["ast_snapshot"]["approved_execution_evidence"]
        self.assertEqual(verified["task"]["status"], "completed")
        self.assertEqual(Path(evidence["workspace_root"]), workspace)

    def test_dummy_postapply_rejects_tampered_backup_manifest(self) -> None:
        with self.assertRaises(LongRunningTaskError) as blocked:
            self._apply_and_verify_manifest_backed_dummy_fixture(
                tamper_manifest_before_postapply=True,
            )

        self.assertEqual(
            blocked.exception.reason_code,
            "post_apply_manifest_hash_mismatch",
        )

    def test_dummy_postapply_rejects_frontend_pass_when_managed_browser_fails(self) -> None:
        failed_proof = {
            **_passing_managed_browser_proof(),
            "status": "failed",
            "browser_verification_status": "failed",
            "storefront_runtime_status": "failed",
            "real_browser_used": True,
            "rendered_card_count": 0,
            "visible_fields": {
                "name": False,
                "price": False,
                "category": False,
                "description": False,
            },
            "page_errors": ["ReferenceError: products is not defined"],
        }
        lifecycle = self._apply_and_verify_manifest_backed_dummy_fixture(failed_proof)
        verified = lifecycle["verified"]
        assert isinstance(verified, dict)
        task = verified["task"]
        verification = task["post_apply_verification"]

        self.assertEqual(task["status"], "verification_failed")
        self.assertEqual(verification["status"], "verification_failed")
        self.assertEqual(
            verification["browser_evidence"]["storefront_runtime_engine"],
            "playwright_chromium",
        )
        self.assertEqual(verification["browser_evidence"]["rendered_card_count"], 0)
        self.assertFalse(verification["client_browser_evidence_decision_bearing"])
        self.assertTrue(
            verification["snapshot_verification"]["client_browser_evidence_ignored"]
        )
        self.assertIn(
            "post_apply_verification_failed",
            verification["commit_blockers"],
        )

    def test_dummy_manifest_undo_hash_drift_fails_before_touching_any_file(self) -> None:
        lifecycle = self._apply_and_verify_manifest_backed_dummy_fixture()
        workspace = lifecycle["workspace"]
        fixture = lifecycle["fixture"]
        task_id = lifecycle["task_id"]
        manifest_rel = lifecycle["manifest_rel"]
        assert isinstance(workspace, Path)
        assert isinstance(fixture, Path)
        assert isinstance(task_id, str)
        assert isinstance(manifest_rel, str)

        (fixture / "index.html").write_text("tampered after verification\n", encoding="utf-8")
        state_before_undo = {
            str(path.relative_to(fixture)).replace("\\", "/"): path.read_bytes()
            for path in fixture.rglob("*")
            if path.is_file()
        }

        with self.assertRaises(LongRunningTaskError) as blocked:
            long_running_module.undo_last_approved_change(
                task_id,
                confirm_undo=True,
                expected_backup_manifest=manifest_rel,
                requested_by="lifecycle-test",
            )

        self.assertEqual(blocked.exception.reason_code, "undo_hash_drift")
        self.assertEqual(
            {
                str(path.relative_to(fixture)).replace("\\", "/"): path.read_bytes()
                for path in fixture.rglob("*")
                if path.is_file()
            },
            state_before_undo,
        )
        self.assertEqual(
            lifecycle["sentinel"].read_text(encoding="utf-8"),
            "unrelated user state\n",
        )
        manifest_path = workspace / manifest_rel
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["stage"], "post_apply_verified")
        self.assertFalse((manifest_path.parent / "undo-receipt.json").exists())

    def test_dummy_manifest_undo_rejects_tampered_finalized_manifest(self) -> None:
        lifecycle = self._apply_and_verify_manifest_backed_dummy_fixture()
        workspace = lifecycle["workspace"]
        fixture = lifecycle["fixture"]
        task_id = lifecycle["task_id"]
        manifest_rel = lifecycle["manifest_rel"]
        assert isinstance(workspace, Path)
        assert isinstance(fixture, Path)
        assert isinstance(task_id, str)
        assert isinstance(manifest_rel, str)

        manifest_path = workspace / manifest_rel
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["rollback_hint"] = "tampered after post-apply finalization"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        state_before_undo = {
            str(path.relative_to(fixture)).replace("\\", "/"): path.read_bytes()
            for path in fixture.rglob("*")
            if path.is_file()
        }

        with self.assertRaises(LongRunningTaskError) as blocked:
            long_running_module.undo_last_approved_change(
                task_id,
                confirm_undo=True,
                expected_backup_manifest=manifest_rel,
                requested_by="lifecycle-test",
            )

        self.assertEqual(blocked.exception.reason_code, "undo_manifest_hash_mismatch")
        self.assertEqual(
            {
                str(path.relative_to(fixture)).replace("\\", "/"): path.read_bytes()
                for path in fixture.rglob("*")
                if path.is_file()
            },
            state_before_undo,
        )
        self.assertFalse((manifest_path.parent / "undo-receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
