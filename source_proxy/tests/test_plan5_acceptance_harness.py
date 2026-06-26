from __future__ import annotations

import os
import tempfile
import unittest

from source_proxy.acceptance.plan5_acceptance import build_plan5_acceptance_gate
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


if __name__ == "__main__":
    unittest.main()
