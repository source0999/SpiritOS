from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.decision import router as decision_router
from source_proxy.decision.prompt_packet import PromptPacketInput, build_prompt_packet
from source_proxy.tasks.long_running import (
    advance_long_running_task,
    create_long_running_task,
    get_long_running_task,
    reset_long_running_tasks,
    update_long_running_task,
)


class PromptPacketContextMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_database_path = os.environ.get(
            "SOURCE_PROXY_LONG_RUNNING_TASKS_DB"
        )
        self._tempdir = tempfile.TemporaryDirectory()
        os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = os.path.join(
            self._tempdir.name,
            "tasks.sqlite3",
        )
        reset_long_running_tasks()

    def tearDown(self) -> None:
        reset_long_running_tasks()
        if self._previous_database_path is None:
            os.environ.pop("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", None)
        else:
            os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = (
                self._previous_database_path
            )
        self._tempdir.cleanup()

    def _client(self) -> TestClient:
        app = FastAPI()
        app.include_router(decision_router)
        return TestClient(app)

    def test_prompt_packet_marks_missing_context_without_claiming_file_contents(self) -> None:
        packet = build_prompt_packet(
            PromptPacketInput(
                task="Review the repo architecture",
                needs_codebase_context=True,
            )
        ).as_payload()

        metadata = packet["context_metadata"]
        self.assertEqual(metadata["context_inclusion_mode"], "none")
        self.assertFalse(metadata["file_contents_claimed"])
        self.assertEqual(metadata["included_paths"], [])
        self.assertIn("ask for the specific files", packet["relevant_context"])

    def test_prompt_packet_marks_path_listing_only_and_omits_secret_paths(self) -> None:
        packet = build_prompt_packet(
            PromptPacketInput(
                task="Review Windows project folder listing",
                relevant_context=(
                    "Path listing only:\n"
                    "C:\\Projects\\SpiritOS\\package.json\n"
                    "C:\\Projects\\SpiritOS\\.env\n"
                    "src/app/page.tsx\n"
                ),
                needs_codebase_context=True,
            )
        ).as_payload()

        metadata = packet["context_metadata"]
        self.assertEqual(metadata["context_inclusion_mode"], "path_listing_only")
        self.assertFalse(metadata["file_contents_claimed"])
        self.assertIn("C:\\Projects\\SpiritOS\\package.json", metadata["included_paths"])
        self.assertIn("src/app/page.tsx", metadata["included_paths"])
        self.assertNotIn("C:\\Projects\\SpiritOS\\.env", metadata["included_paths"])
        self.assertIn("C:\\Projects\\SpiritOS\\.env", metadata["omitted_paths"])

    def test_prompt_packet_marks_generated_bundle_reference(self) -> None:
        packet = build_prompt_packet(
            PromptPacketInput(
                task="Use compressed context",
                relevant_context="generated_context_bundle: repomix-output.ast.xml",
                context_tokens=12000,
            )
        ).as_payload()

        metadata = packet["context_metadata"]
        self.assertEqual(metadata["context_inclusion_mode"], "generated_bundle_reference")
        self.assertFalse(metadata["file_contents_claimed"])
        self.assertIn("repomix-output.ast.xml", metadata["included_paths"])
        self.assertGreater(metadata["estimated_context_tokens"], 0)

    def test_prompt_packet_endpoint_returns_context_metadata(self) -> None:
        client = self._client()
        response = client.post(
            "/v1/decisions/prompt-packet",
            json={
                "task": "Create prompt packet from listing",
                "relevant_context": "folder listing:\nsrc/lib/example.ts",
                "needs_codebase_context": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("context_metadata", payload)
        self.assertEqual(
            payload["context_metadata"]["context_inclusion_mode"],
            "path_listing_only",
        )

    def test_research_prompt_packet_endpoint_attaches_sources(self) -> None:
        client = self._client()
        sources = [
            {
                "title": "Vite 6.0 is out!",
                "url": "https://vite.dev/blog/announcing-vite6",
                "snippet": "Vite 6 release notes.",
            }
        ]

        with patch(
            "source_proxy.decision.router.run_local_research_preview",
            new=AsyncMock(return_value=sources),
        ):
            with patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": "true"}, clear=False):
                response = client.post(
                    "/v1/decisions/prompt-packet",
                    json={"task": "What are the latest changes in Vite 6?"},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["route_decision"]["research_recommended"])
        self.assertEqual(payload["research_sources"], sources)
        self.assertEqual(payload["route_decision"]["research_sources"], sources)

    def test_research_route_endpoint_attaches_sources(self) -> None:
        client = self._client()
        sources = [
            {
                "title": "Releases | Vite",
                "url": "https://vite.dev/releases",
                "snippet": "Current releases.",
            }
        ]

        with patch(
            "source_proxy.decision.router.run_local_research_preview",
            new=AsyncMock(return_value=sources),
        ):
            with patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": "true"}, clear=False):
                response = client.post(
                    "/v1/decisions/route",
                    json={"task": "What are the latest changes in Vite 6?"},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["research_recommended"])
        self.assertEqual(payload["research_sources"], sources)

    def test_proxy_research_sources_are_disabled_by_default(self) -> None:
        client = self._client()
        search = AsyncMock(
            return_value=[
                {
                    "title": "Releases | Vite",
                    "url": "https://vite.dev/releases",
                    "snippet": "Current releases.",
                }
            ],
        )

        with (
            patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": ""}, clear=False),
            patch("source_proxy.decision.router.run_local_research_preview", new=search),
        ):
            response = client.post(
                "/v1/decisions/route",
                json={"task": "What are the latest changes in Vite 6?"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["research_recommended"])
        self.assertEqual(payload["research_sources"], [])
        search.assert_not_awaited()

    def test_route_endpoint_injects_role_prompt_from_active_task(self) -> None:
        client = self._client()
        created = create_long_running_task("Swarm route")
        task_id = created["task"]["id"]
        update_long_running_task(task_id, current_agent_role="debugger")

        response = client.post(
            "/v1/decisions/route",
            json={"task": "Run verification", "active_task_id": task_id},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["current_agent_role"], "debugger")
        self.assertIn("Debugger", payload["role_system_prompt"])
        self.assertIn("sandboxed tools", payload["role_system_prompt"])

    def test_route_endpoint_explicit_role_overrides_active_task(self) -> None:
        client = self._client()
        created = create_long_running_task("Swarm route")
        task_id = created["task"]["id"]
        update_long_running_task(task_id, current_agent_role="debugger")

        response = client.post(
            "/v1/decisions/route",
            json={
                "task": "Plan implementation",
                "active_task_id": task_id,
                "current_agent_role": "architect",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["current_agent_role"], "architect")
        self.assertIn("Architect", payload["role_system_prompt"])

    def test_prompt_packet_active_task_uses_saved_architect_packet_context(self) -> None:
        client = self._client()
        previous_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            target = root / "docs/phase-8-manual-check.md"
            target.parent.mkdir(parents=True)
            target.write_text("# Manual Check\n", encoding="utf-8")
            os.environ["SPIRIT_PROJECT_PATH"] = workspace
            task = (
                "Target file: docs/phase-8-manual-check.md\n"
                'Add "Manual check complete." as one short sentence.'
            )
            created = create_long_running_task(task)
            task_id = created["task"]["id"]
            advance_long_running_task(task_id)

            def fake_coder(*, architect_plan, **_kwargs):
                packet = architect_plan.coder_packet
                self.assertEqual(
                    packet.target_file.path,
                    "docs/phase-8-manual-check.md",
                )
                self.assertEqual(
                    [item.path for item in packet.context_slices],
                    ["docs/phase-8-manual-check.md"],
                )
                self.assertIn(
                    "Manual check complete.",
                    packet.constraints.must_contain,
                )
                return {
                    "proposed_diff": "\n".join(
                        [
                            "diff --git a/docs/phase-8-manual-check.md b/docs/phase-8-manual-check.md",
                            "--- a/docs/phase-8-manual-check.md",
                            "+++ b/docs/phase-8-manual-check.md",
                            "@@ -1 +1,2 @@",
                            " # Manual Check",
                            '+Manual check complete.',
                            "",
                        ]
                    ),
                    "target": "docs/phase-8-manual-check.md",
                    "coder_notes": ["ok"],
                    "bundle": None,
                    "coder_diagnostics": {
                        "context_mode": "user_app",
                        "target_exists": True,
                        "context_slices": [
                            {"path": "docs/phase-8-manual-check.md", "kind": "target"}
                        ],
                        "forbidden_paths": ["source_proxy/"],
                    },
                }

            try:
                with patch(
                    "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
                    side_effect=fake_coder,
                ) as coder_mock:
                    response = client.post(
                        "/v1/decisions/prompt-packet",
                        json={
                            "task": task,
                            "wants_implementation": True,
                            "active_task_id": task_id,
                            "current_agent_role": "coder",
                        },
                    )
            finally:
                if previous_project_path is None:
                    os.environ.pop("SPIRIT_PROJECT_PATH", None)
                else:
                    os.environ["SPIRIT_PROJECT_PATH"] = previous_project_path

        self.assertEqual(response.status_code, 200, response.text)
        coder_mock.assert_called_once()
        body = response.json()
        self.assertEqual(body["target"], "docs/phase-8-manual-check.md")
        self.assertIn("diff --git", body["proposed_diff"])
        self.assertEqual(
            body["coder_packet"]["target_file"]["path"],
            "docs/phase-8-manual-check.md",
        )
        self.assertEqual(
            body["coder_packet"]["context_slices"][0]["path"],
            "docs/phase-8-manual-check.md",
        )
        self.assertIn(
            "Manual check complete.",
            body["coder_packet"]["constraints"]["must_contain"],
        )
        self.assertEqual(
            body["verification_plan"]["required_checks"][0]["id"],
            "git_apply_check",
        )

    def test_prompt_packet_coder_missing_context_marks_task_needs_context(self) -> None:
        client = self._client()
        previous_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            target = root / "docs/phase-8-manual-check.md"
            target.parent.mkdir(parents=True)
            target.write_text("# Manual Check\n", encoding="utf-8")
            os.environ["SPIRIT_PROJECT_PATH"] = workspace
            task = (
                "Target file: docs/phase-8-manual-check.md\n"
                'Add "Manual check complete." as one short sentence.'
            )
            created = create_long_running_task(task)
            task_id = created["task"]["id"]
            advance_long_running_task(task_id)

            with patch(
                "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
                return_value={
                    "proposed_diff": "",
                    "target": "docs/phase-8-manual-check.md",
                    "coder_notes": ["CODER_BLOCKED reason_code: coder_packet_missing_context"],
                    "bundle": None,
                    "coder_blocked": True,
                    "blocked_reason": "Coder requires an Architect CoderPacket.",
                    "needed_context": "Regenerate Architect plan.",
                    "reason_code": "coder_packet_missing_context",
                    "coder_diagnostics": {
                        "context_mode": "user_app",
                        "target_exists": True,
                        "context_slices": [],
                        "forbidden_paths": ["source_proxy/"],
                    },
                },
            ):
                response = client.post(
                    "/v1/decisions/prompt-packet",
                    json={
                        "task": task,
                        "wants_implementation": True,
                        "active_task_id": task_id,
                        "current_agent_role": "coder",
                    },
                )
            try:
                for _ in range(4):
                    payload = get_long_running_task(task_id)
            finally:
                if previous_project_path is None:
                    os.environ.pop("SPIRIT_PROJECT_PATH", None)
                else:
                    os.environ["SPIRIT_PROJECT_PATH"] = previous_project_path

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "needs_context")
        self.assertEqual(body["reason_code"], "coder_packet_missing_context")
        self.assertEqual(payload["task"]["status"], "needs_context")
        self.assertNotEqual(payload["task"]["status"], "completed")
        self.assertIn("CoderPacket", payload["task"]["next_action"])

    def test_prompt_packet_pinned_app_page_invokes_sync_coder(self) -> None:
        client = self._client()
        task = (
            "Target file: src/app/(dashboard)/design/page.tsx\n\n"
            "Add a visible status widget at the top of the page."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/app/(dashboard)/design/page.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "blocked_reason": "Coder model returned no content.",
                "needed_context": "Set SOURCE_PROXY_CODER_MODEL_ALIAS.",
                "reason_code": "coder_empty_model_response",
                "coder_diagnostics": {
                    "context_mode": "user_app",
                    "target_exists": True,
                    "context_slices": [
                        {"path": "src/app/(dashboard)/design/page.tsx", "kind": "target"}
                    ],
                    "forbidden_paths": ["source_proxy/"],
                },
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )
        self.assertEqual(response.status_code, 200, response.text)
        coder_mock.assert_not_called()
        body = response.json()
        self.assertEqual(
            body.get("target"),
            "src/app/(dashboard)/design/page.tsx",
        )
        self.assertEqual(body.get("proposed_diff"), "")
        self.assertFalse(body.get("coder_agent_local_diff"))
        self.assertTrue(body.get("manual_prompt_packet_available"))
        self.assertEqual(body.get("reason_code"), "target_missing")
        rd = body.get("route_decision") or {}
        self.assertEqual(rd.get("recommended_route"), "local_route")

    def test_prompt_packet_already_satisfied_maps_to_no_approval_needed(self) -> None:
        client = self._client()
        task = (
            "Target file: src/app/coding/design-demo/page.tsx\n\n"
            "Ensure the design demo page is already complete."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/app/coding/design-demo/page.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": False,
                "already_satisfied": True,
                "alreadySatisfied": True,
                "blocked_reason": "",
                "needed_context": "",
                "reason_code": "coder_no_changes_needed",
                "coder_diagnostics": {
                    "validation_status": "already_satisfied",
                    "generated_diff_length": 0,
                    "already_satisfied": True,
                    "no_changes_needed": True,
                },
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["proposed_diff"], "")
        coder_mock.assert_called_once()
        self.assertFalse(body["coder_blocked"])
        self.assertTrue(body["already_satisfied"])
        self.assertEqual(body["reason_code"], "coder_no_changes_needed")
        self.assertFalse(body["manual_prompt_packet_available"])
        self.assertEqual(body["status"], "already_satisfied")
        self.assertEqual(
            body["coder_packet"]["target_file"]["path"],
            "src/app/coding/design-demo/page.tsx",
        )

    def test_prompt_packet_subjective_improvement_noop_maps_to_needs_diff(self) -> None:
        client = self._client()
        task = (
            "make ThemeStrip feel more premium and alive, tighter spacing, better glow, "
            "smoother hover states.\n"
            "Target file: src/components/dashboard/ThemeStrip.tsx"
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/components/dashboard/ThemeStrip.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "already_satisfied": False,
                "blocked_reason": (
                    "This task asks for subjective visual improvement, so identical "
                    "replacement content cannot be treated as already satisfied."
                ),
                "needed_context": (
                    "Produce an actual visual refinement diff or use manual visual review."
                ),
                "reason_code": "coder_subjective_improvement_requires_diff_or_review",
                "coder_diagnostics": {
                    "validation_status": "subjective_improvement_requires_diff_or_review",
                    "already_satisfied": False,
                    "no_changes_needed": False,
                    "subjective_improvement_detected": True,
                },
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["manual_prompt_packet_available"])
        self.assertTrue(body["cloud_route_available"])
        self.assertFalse(body["already_satisfied"])
        self.assertEqual(
            body["reason_code"],
            "coder_subjective_improvement_requires_diff_or_review",
        )
        self.assertEqual(body["status"], "needs_coder_diff")
        self.assertEqual(
            body["coder_packet"]["target_file"]["path"],
            "src/components/dashboard/ThemeStrip.tsx",
        )

    def test_prompt_packet_shallow_visual_diff_maps_to_needs_diff(self) -> None:
        client = self._client()
        task = (
            "make ThemeStrip feel more premium and alive, tighter spacing, better glow, "
            "smoother hover states.\n"
            "Target file: src/components/dashboard/ThemeStrip.tsx"
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/components/dashboard/ThemeStrip.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "already_satisfied": False,
                "blocked_reason": (
                    "The generated diff does not materially change UI styling, layout, "
                    "hover, active, glow, spacing, or visual behavior for this subjective "
                    "improvement task."
                ),
                "needed_context": (
                    "Generate a concrete visual refinement diff that changes className, "
                    "styling, layout, hover, active, glow, spacing, or animation behavior."
                ),
                "reason_code": "coder_visual_improvement_diff_too_shallow",
                "coder_diagnostics": {
                    "validation_status": "visual_improvement_diff_too_shallow",
                    "visual_materiality_ok": False,
                    "visual_materiality_reasons": [
                        "subjective visual task produced only comment or non-visual changes"
                    ],
                    "subjective_improvement_detected": True,
                },
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["manual_prompt_packet_available"])
        self.assertTrue(body["cloud_route_available"])
        self.assertEqual(body["proposed_diff"], "")
        self.assertEqual(body["reason_code"], "coder_visual_improvement_diff_too_shallow")
        self.assertEqual(body["status"], "needs_coder_diff")

    def test_prompt_packet_pinned_app_page_backticks_invokes_sync_coder(self) -> None:
        client = self._client()
        task = (
            "Target file: `src/app/(dashboard)/design/page.tsx`\n\n"
            "Add a visible status widget at the top of the page."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/app/(dashboard)/design/page.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "blocked_reason": "Coder model returned no content.",
                "needed_context": "Set SOURCE_PROXY_CODER_MODEL_ALIAS.",
                "reason_code": "coder_empty_model_response",
                "coder_diagnostics": {
                    "context_mode": "user_app",
                    "target_exists": True,
                    "context_slices": [
                        {"path": "src/app/(dashboard)/design/page.tsx", "kind": "target"}
                    ],
                    "forbidden_paths": ["source_proxy/"],
                },
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )
        self.assertEqual(response.status_code, 200, response.text)
        coder_mock.assert_not_called()
        self.assertEqual(
            response.json().get("target"),
            "src/app/(dashboard)/design/page.tsx",
        )
        body = response.json()
        self.assertEqual(body.get("context_mode"), "user_app")
        self.assertEqual(
            body.get("coder_packet", {}).get("context_slices"),
            [],
        )
        self.assertIn(
            "source_proxy/",
            body.get("coder_packet", {}).get("forbidden_paths") or [],
        )

    def test_prompt_packet_derives_context_mode_when_coder_diagnostics_missing(self) -> None:
        client = self._client()
        task = (
            "Target file: source_proxy/decision/router.py\n\n"
            "Fix the route classification for empty tasks."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "source_proxy/decision/router.py",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "blocked_reason": "Coder timed out.",
                "needed_context": "Retry.",
                "reason_code": "coder_timeout",
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body.get("context_mode"), "agent_internal")
        self.assertEqual(
            body.get("coder_packet", {}).get("context_slices", [])[0].get("path"),
            "source_proxy/decision/router.py",
        )
        self.assertIn(
            "src/app/",
            body.get("coder_packet", {}).get("forbidden_paths") or [],
        )

    def test_prompt_packet_last_target_line_wins_for_fast_path(self) -> None:
        client = self._client()
        task = (
            "Target file: src/lib/ignore-me.ts\n"
            "Target file: src/app/(group)/final/page.tsx\n\n"
            "Add padding to the hero section."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/app/(group)/final/page.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "blocked_reason": "Coder model returned no content.",
                "needed_context": "Set SOURCE_PROXY_CODER_MODEL_ALIAS.",
                "reason_code": "coder_empty_model_response",
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )
        self.assertEqual(response.status_code, 200, response.text)
        coder_mock.assert_not_called()
        self.assertEqual(
            response.json().get("target"),
            "src/app/(group)/final/page.tsx",
        )

    def test_prompt_packet_pinned_lib_file_still_invokes_sync_coder(self) -> None:
        client = self._client()
        task = (
            "Target file: src/lib/coding/example.ts\n\n"
            "Add export const FOO = 1."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/lib/coding/example.ts",
                "coder_notes": [],
                "bundle": "test",
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
        )
        self.assertEqual(response.status_code, 200, response.text)
        coder_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
