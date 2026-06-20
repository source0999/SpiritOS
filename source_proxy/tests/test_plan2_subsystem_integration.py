from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from source_proxy.decision.current_research import run_current_research_for_task
from source_proxy.decision.mac_integration import run_mac_worker_for_task
from source_proxy.decision.specialist_integration import run_specialists_for_task
from source_proxy.tasks.long_running import (
    create_long_running_task,
    record_subsystem_integration_result,
    reset_long_running_tasks,
)


class Plan2SubsystemIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._previous_database_path = os.environ.get("SOURCE_PROXY_LONG_RUNNING_TASKS_DB")
        self._tempdir = tempfile.TemporaryDirectory()
        os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = os.path.join(self._tempdir.name, "tasks.sqlite3")
        reset_long_running_tasks()

    def tearDown(self) -> None:
        reset_long_running_tasks()
        if self._previous_database_path is None:
            os.environ.pop("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", None)
        else:
            os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = self._previous_database_path
        self._tempdir.cleanup()

    def test_subsystem_recorder_requires_real_upstream_state_and_output(self) -> None:
        task_id = create_long_running_task("Plan 2 recorder")["task"]["id"]

        with self.assertRaises(Exception):
            record_subsystem_integration_result(
                task_id,
                subsystem="mac_worker",
                consumer_subsystem="cartographer",
                upstream_state={},
                output={"summary": "no upstream"},
                status="INTEGRATED",
            )

    def test_subsystem_recorder_adds_invocation_and_consumer_events(self) -> None:
        task_id = create_long_running_task("Plan 2 recorder")["task"]["id"]

        payload = record_subsystem_integration_result(
            task_id,
            subsystem="mac_worker",
            consumer_subsystem="cartographer_mac_assignment_consumer",
            upstream_state={"task_id": task_id, "assignment": "system_status"},
            output={"summary": "Mac status returned", "job_id": "mac-job-1"},
            status="INTEGRATED",
        )

        trace = payload["task"]["causal_trace"]
        self.assertTrue(trace["trace_id"].startswith("trace_"))
        self.assertTrue(trace["invocation_event_id"].startswith("invocation_"))
        self.assertTrue(trace["consumer_event_id"].startswith("consumer_"))
        self.assertEqual(trace["consumer_subsystem"], "cartographer_mac_assignment_consumer")
        self.assertIn("mac_worker", payload["task"]["ast_snapshot"]["plan_2_subsystem_integrations"])

    def test_subsystem_failure_changes_task_outcome(self) -> None:
        task_id = create_long_running_task("Plan 2 failure")["task"]["id"]

        payload = record_subsystem_integration_result(
            task_id,
            subsystem="current_research",
            consumer_subsystem="cartographer_current_research_consumer",
            upstream_state={"task_id": task_id, "query": "current docs"},
            output={"summary": "provider unavailable", "reason": "searxng_unreachable"},
            status="BLOCKED_ENV",
            failure_reason="searxng_unreachable",
        )

        self.assertEqual(payload["task"]["status"], "blocked")
        self.assertEqual(payload["task"]["architect_reason"], "searxng_unreachable")

    async def test_current_research_does_not_use_generic_local_file_fallback(self) -> None:
        task_id = create_long_running_task("Current research")["task"]["id"]
        scout = {"status": "skipped", "reason": "scout_research_disabled", "scout_sources": []}
        searxng = {
            "status": "used",
            "reason": "live_searxng_provider_query_executed",
            "searxng_sources": [{"title": "Source", "url": "https://example.com", "source": "web"}],
        }
        with (
            patch("source_proxy.decision.current_research.run_scout_research_diagnostics", AsyncMock(return_value=scout)),
            patch("source_proxy.decision.current_research.run_searxng_research_diagnostics", AsyncMock(return_value=searxng)),
        ):
            result = await run_current_research_for_task(
                task_id,
                query="latest API status",
                upstream_state={"task_id": task_id, "route": "/coding"},
            )

        packet = result["research_packet"]
        self.assertEqual(result["status"], "INTEGRATED_LIVE")
        self.assertFalse(packet["generic_local_file_fallback_used"])
        self.assertTrue(packet["sources"][0]["untrusted"])
        self.assertEqual(packet["downstream_decision"], "research_sources_available")

    async def test_current_research_blocks_when_providers_are_unavailable(self) -> None:
        task_id = create_long_running_task("Current research unavailable")["task"]["id"]
        with (
            patch("source_proxy.decision.current_research.run_scout_research_diagnostics", AsyncMock(return_value={"status": "blocked", "reason": "scout_down", "scout_sources": []})),
            patch("source_proxy.decision.current_research.run_searxng_research_diagnostics", AsyncMock(return_value={"status": "blocked", "reason": "searxng_down", "searxng_sources": []})),
        ):
            result = await run_current_research_for_task(
                task_id,
                query="latest API status",
                upstream_state={"task_id": task_id, "route": "/coding"},
            )

        self.assertEqual(result["status"], "BLOCKED_ENV")
        self.assertEqual(result["task"]["status"], "blocked")

    async def test_specialist_packet_consumes_model_and_verifier_outputs(self) -> None:
        task_id = create_long_running_task("Specialists")["task"]["id"]
        fake_model_packet = {
            "gemma": {"status": "used", "intent": "test intent"},
            "hermes_critic": {"status": "used", "risks": []},
            "hermes_verifier": {"status": "skipped"},
            "fip3_model_packet_hash": "model-hash",
        }
        with patch(
            "source_proxy.decision.specialist_integration.build_fip3_model_lane_packet",
            AsyncMock(return_value=fake_model_packet),
        ):
            result = await run_specialists_for_task(
                task_id,
                task="Plan 2 specialist test",
                upstream_state={"task_id": task_id, "route": "/coding"},
                research_packet={"research_packet_hash": "research-hash"},
            )

        self.assertEqual(result["status"], "INTEGRATED_LIVE")
        self.assertEqual(
            result["task"]["causal_trace"]["consumer_subsystem"],
            "cartographer_specialist_packet_consumer",
        )
        self.assertIn("browser_functional_verifier", result["specialist_packet"])

    async def test_specialist_packet_blocks_when_model_lanes_fail(self) -> None:
        task_id = create_long_running_task("Specialists failed")["task"]["id"]
        fake_model_packet = {
            "gemma": {"status": "failed", "intent": ""},
            "hermes_critic": {"status": "timeout", "risks": []},
            "hermes_verifier": {"status": "skipped"},
            "fip3_model_packet_hash": "model-hash",
        }
        with patch(
            "source_proxy.decision.specialist_integration.build_fip3_model_lane_packet",
            AsyncMock(return_value=fake_model_packet),
        ):
            result = await run_specialists_for_task(
                task_id,
                task="Plan 2 specialist failure test",
                upstream_state={"task_id": task_id, "route": "/coding"},
                research_packet={"research_packet_hash": "research-hash"},
            )

        self.assertEqual(result["status"], "BLOCKED_ENV")
        self.assertEqual(
            result["task"]["ast_snapshot"]["plan_2_subsystem_integrations"]["specialist_model_lanes"]["status"],
            "BLOCKED_ENV",
        )

    def test_mac_worker_write_proof_sends_trace_fields_and_consumes_result(self) -> None:
        task_id = create_long_running_task("Mac write proof")["task"]["id"]
        fake_completed = type(
            "Completed",
            (),
            {
                "returncode": 0,
                "stdout": '{"job_id":"mac-job","job_type":"mac_isolated_write_proof","success":true,"result":{"summary":"ok","mac_write_performed":true,"mac_write_path":"/tmp/spiritos-plan2-mac-worker-proof/plan2-mac-write-proof.txt","rollback_status":"deleted"},"error":null}',
                "stderr": "",
            },
        )()

        captured: dict[str, object] = {}

        def fake_run(command, input, **kwargs):  # type: ignore[no-untyped-def]
            captured["command"] = command
            captured["input"] = input
            return fake_completed

        with patch("source_proxy.decision.mac_integration.subprocess.run", fake_run):
            result = run_mac_worker_for_task(
                task_id,
                mode="mac_isolated_write_proof",
                input_data={"contents": "proof"},
            )

        job = __import__("json").loads(str(captured["input"]))
        self.assertEqual(result["status"], "INTEGRATED_LIVE")
        self.assertEqual(job["worker"], "mac")
        self.assertEqual(job["task_id"], task_id)
        self.assertTrue(job["trace_id"].startswith("trace_"))
        self.assertTrue(job["invocation_event_id"].startswith("invocation_"))
        self.assertEqual(result["task"]["causal_trace"]["consumer_subsystem"], "cartographer_mac_assignment_consumer")

    def test_mac_worker_unavailable_changes_outcome_without_dell_fallback(self) -> None:
        task_id = create_long_running_task("Mac unavailable")["task"]["id"]
        fake_completed = type("Completed", (), {"returncode": 255, "stdout": "", "stderr": "ssh: connect failed"})()

        with patch("source_proxy.decision.mac_integration.subprocess.run", return_value=fake_completed):
            result = run_mac_worker_for_task(task_id, mode="mac_system_status", input_data={})

        self.assertEqual(result["status"], "BLOCKED_ENV")
        self.assertEqual(result["task"]["status"], "blocked")
        self.assertIn("ssh", result["task"]["architect_reason"])


if __name__ == "__main__":
    unittest.main()
