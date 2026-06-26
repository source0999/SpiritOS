from __future__ import annotations

import os
import tempfile
import unittest

from source_proxy.acceptance.plan5_acceptance import (
    build_plan5_acceptance_gate,
    build_plan5_phase_verifier_gate,
)
from source_proxy.tasks.long_running import (
    create_long_running_task,
    record_subsystem_integration_result,
    reset_long_running_tasks,
)


class Plan5AcceptanceHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_database_path = os.environ.get("SOURCE_PROXY_LONG_RUNNING_TASKS_DB")
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
            os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = self._previous_database_path
        self._tempdir.cleanup()

    def test_acceptance_gate_go_requires_consumed_output_on_one_trace(self) -> None:
        task_id = create_long_running_task("Plan 5 acceptance")["task"]["id"]
        task_payload = record_subsystem_integration_result(
            task_id,
            subsystem="browser_functional_verifier",
            consumer_subsystem="coding_operator_surface",
            upstream_state={"task_id": task_id, "route": "/coding"},
            output={"summary": "Verifier result consumed", "status": "VERIFIED"},
            status="INTEGRATED_LIVE",
            changed_state_fields=["ast_snapshot.plan_5_acceptance.browser_functional_verifier"],
        )

        gate = build_plan5_acceptance_gate(
            task_payload,
            subsystem="browser_functional_verifier",
            focused_checks=["python -m unittest source_proxy.tests.test_plan5_acceptance_harness"],
            git_status="clean except ignored repomixes/",
            evidence_budget_status="within_plan_5_budget",
        )

        self.assertEqual(gate["status"], "GO")
        self.assertTrue(gate["same_trace"])
        self.assertTrue(gate["output_consumed_downstream"])
        self.assertEqual(gate["missing_fields"], [])
        self.assertEqual(gate["forbidden_states"], [])
        evidence = gate["evidence"]
        self.assertEqual(evidence["task_id"], task_id)
        self.assertTrue(evidence["trace_id"].startswith("trace_"))
        self.assertTrue(evidence["invocation_event_id"].startswith("invocation_"))
        self.assertTrue(evidence["consumer_event_id"].startswith("consumer_"))
        self.assertEqual(evidence["consumer_subsystem"], "coding_operator_surface")
        self.assertIn(
            "ast_snapshot.plan_5_acceptance.browser_functional_verifier",
            evidence["state_fields_changed"],
        )
        self.assertTrue(evidence["output_hash"])

    def test_acceptance_gate_rejects_unconsumed_output(self) -> None:
        task_id = create_long_running_task("Plan 5 unconsumed output")["task"]["id"]
        task_payload = record_subsystem_integration_result(
            task_id,
            subsystem="browser_functional_verifier",
            consumer_subsystem="coding_operator_surface",
            upstream_state={"task_id": task_id, "route": "/coding"},
            output={"summary": "Verifier result consumed", "status": "VERIFIED"},
            status="INTEGRATED_LIVE",
            changed_state_fields=["ast_snapshot.plan_5_acceptance.browser_functional_verifier"],
        )
        task_payload["task"]["ast_snapshot"]["plan_2_subsystem_integrations"][
            "browser_functional_verifier"
        ]["consumer_event_id"] = ""

        gate = build_plan5_acceptance_gate(
            task_payload,
            subsystem="browser_functional_verifier",
            focused_checks=["python -m unittest source_proxy.tests.test_plan5_acceptance_harness"],
            git_status="clean except ignored repomixes/",
            evidence_budget_status="within_plan_5_budget",
        )

        self.assertEqual(gate["status"], "NEEDS_FIX")
        self.assertIn("consumer_event_missing", gate["failures"])
        self.assertIn("consumer_event_id", gate["missing_fields"])
        self.assertFalse(gate["output_consumed_downstream"])

    def test_phase_verifier_gate_requires_operator_and_phase_consumption(self) -> None:
        task_id = create_long_running_task("Plan 5 phase verifier")["task"]["id"]
        task_payload = record_subsystem_integration_result(
            task_id,
            subsystem="current_research",
            consumer_subsystem="coding_operator_surface",
            upstream_state={"task_id": task_id, "route": "/coding", "query": "current docs"},
            output={"summary": "Research packet consumed", "status": "SOURCES_AVAILABLE"},
            status="INTEGRATED_LIVE",
            changed_state_fields=["ast_snapshot.plan_5_acceptance.current_research"],
        )
        output_hash = task_payload["task"]["ast_snapshot"]["plan_2_subsystem_integrations"][
            "current_research"
        ]["output_hash"]
        task_payload = record_subsystem_integration_result(
            task_id,
            subsystem="plan5_phase_verifier",
            consumer_subsystem="plan5_phase_acceptance_consumer",
            upstream_state={
                "task_id": task_id,
                "source_subsystem": "current_research",
                "accepted_output_hash": output_hash,
            },
            output={"summary": "Phase verifier accepted consumed output", "status": "GO"},
            status="INTEGRATED_LIVE",
            changed_state_fields=["ast_snapshot.plan_5_acceptance.phase_verifier"],
        )

        gate = build_plan5_phase_verifier_gate(
            task_payload,
            subsystem="current_research",
            phase_verifier_subsystem="plan5_phase_verifier",
            operator_consumer_subsystem="coding_operator_surface",
            phase_consumer_subsystem="plan5_phase_acceptance_consumer",
            focused_checks=["python -m unittest source_proxy.tests.test_plan5_acceptance_harness"],
            git_status="clean except ignored repomixes/",
            evidence_budget_status="within_plan_5_budget",
        )

        self.assertEqual(gate["status"], "GO")
        self.assertTrue(gate["same_trace"])
        self.assertTrue(gate["output_consumed_by_operator"])
        self.assertTrue(gate["output_consumed_by_phase_verifier"])
        self.assertEqual(gate["forbidden_states"], [])
        evidence = gate["evidence"]
        self.assertEqual(evidence["task_id"], task_id)
        self.assertEqual(evidence["accepted_output_hash"], output_hash)
        self.assertTrue(evidence["operator_consumer_event_id"].startswith("consumer_"))
        self.assertTrue(evidence["phase_verifier_invocation_event_id"].startswith("invocation_"))
        self.assertTrue(evidence["phase_verifier_consumer_event_id"].startswith("consumer_"))

    def test_phase_verifier_gate_rejects_verifier_without_output_hash_input(self) -> None:
        task_id = create_long_running_task("Plan 5 phase verifier reject")["task"]["id"]
        task_payload = record_subsystem_integration_result(
            task_id,
            subsystem="current_research",
            consumer_subsystem="coding_operator_surface",
            upstream_state={"task_id": task_id, "route": "/coding", "query": "current docs"},
            output={"summary": "Research packet consumed", "status": "SOURCES_AVAILABLE"},
            status="INTEGRATED_LIVE",
            changed_state_fields=["ast_snapshot.plan_5_acceptance.current_research"],
        )
        task_payload = record_subsystem_integration_result(
            task_id,
            subsystem="plan5_phase_verifier",
            consumer_subsystem="plan5_phase_acceptance_consumer",
            upstream_state={"task_id": task_id, "source_subsystem": "current_research"},
            output={"summary": "Phase verifier accepted packet metadata only", "status": "GO"},
            status="INTEGRATED_LIVE",
            changed_state_fields=["ast_snapshot.plan_5_acceptance.phase_verifier"],
        )

        gate = build_plan5_phase_verifier_gate(
            task_payload,
            subsystem="current_research",
            phase_verifier_subsystem="plan5_phase_verifier",
            operator_consumer_subsystem="coding_operator_surface",
            phase_consumer_subsystem="plan5_phase_acceptance_consumer",
            focused_checks=["python -m unittest source_proxy.tests.test_plan5_acceptance_harness"],
            git_status="clean except ignored repomixes/",
            evidence_budget_status="within_plan_5_budget",
        )

        self.assertEqual(gate["status"], "NEEDS_FIX")
        self.assertIn("phase_verifier_missing_output_hash_input", gate["failures"])
        self.assertFalse(gate["output_consumed_by_phase_verifier"])


if __name__ == "__main__":
    unittest.main()
