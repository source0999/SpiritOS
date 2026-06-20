from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from source_proxy.tasks.durable_execution import (
    apply_plan3_policy,
    create_plan3_durable_task,
    plan3_final_go_allowed,
    recover_plan3_task,
    record_plan3_failure_attempt,
    run_plan3_verifier_driven_repair,
    transition_plan3_status,
)
from source_proxy.tasks.long_running import (
    LongRunningTaskError,
    get_long_running_task,
    reset_long_running_tasks,
)


class Plan3DurableExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_database_path = os.environ.get("SOURCE_PROXY_LONG_RUNNING_TASKS_DB")
        self._previous_spirit_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        self._tempdir = tempfile.TemporaryDirectory()
        os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = os.path.join(
            self._tempdir.name,
            "tasks.sqlite3",
        )
        os.environ["SPIRIT_PROJECT_PATH"] = self._tempdir.name
        reset_long_running_tasks()

    def tearDown(self) -> None:
        reset_long_running_tasks()
        if self._previous_database_path is None:
            os.environ.pop("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", None)
        else:
            os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = self._previous_database_path
        if self._previous_spirit_project_path is None:
            os.environ.pop("SPIRIT_PROJECT_PATH", None)
        else:
            os.environ["SPIRIT_PROJECT_PATH"] = self._previous_spirit_project_path
        self._tempdir.cleanup()

    def test_status_transitions_persist_and_readback_exposes_plan3_state(self) -> None:
        created = create_plan3_durable_task("Plan 3 durable readback", max_attempts=2)
        task_id = created["task"]["id"]

        transition_plan3_status(task_id, "policy_checking", reason="policy start")
        transition_plan3_status(
            task_id,
            "executing",
            reason="policy allowed",
            policy_decision="allow",
        )
        readback = get_long_running_task(task_id)

        state = readback["task"]["plan_3_durable_state"]
        self.assertEqual(readback["task"]["status"], "executing")
        self.assertEqual(state["current_status"], "executing")
        self.assertEqual(state["previous_status"], "policy_checking")
        self.assertEqual(state["max_attempts"], 2)
        self.assertTrue(state["trace_id"])
        self.assertTrue(state["latest_invocation_event_id"])
        self.assertTrue(state["causal_events_json"])

    def test_invalid_transition_and_terminal_revert_are_rejected(self) -> None:
        created = create_plan3_durable_task("Plan 3 invalid transition")
        task_id = created["task"]["id"]

        with self.assertRaises(LongRunningTaskError) as invalid:
            transition_plan3_status(task_id, "verified", reason="skip states")
        self.assertEqual(invalid.exception.reason_code, "invalid_plan3_transition")

        transition_plan3_status(task_id, "cancelled", reason="operator cancel")
        with self.assertRaises(LongRunningTaskError) as terminal:
            transition_plan3_status(task_id, "queued", reason="revert")
        self.assertEqual(terminal.exception.reason_code, "terminal_status_revert_rejected")

    def test_policy_gate_fails_closed_and_cannot_count_as_go(self) -> None:
        created = create_plan3_durable_task("Plan 3 policy proof")
        task_id = created["task"]["id"]

        blocked = apply_plan3_policy(
            task_id,
            action="mac_write",
            target_path="../unsafe",
        )

        state = blocked["task"]["plan_3_durable_state"]
        self.assertEqual(blocked["task"]["status"], "policy_blocked")
        self.assertEqual(state["policy_decision"], "policy_blocked")
        self.assertEqual(state["last_failure_class"], "unsafe_path_rejected")
        self.assertIn("unsafe_path_rejected", state["blocked_reason"])
        self.assertTrue(
            any(event["event_type"] == "policy" for event in state["causal_events_json"])
        )
        self.assertFalse(
            plan3_final_go_allowed(
                plan_2_carryforward="PASS",
                durable_state="INTEGRATED_LIVE",
                policy_gates="NEEDS_FIX",
                retry_timeout_failure="INTEGRATED_LIVE",
                recovery="INTEGRATED_LIVE",
                repair_loop="INTEGRATED_LIVE",
                task_a_policy="FAIL",
                task_b_recovery="PASS",
                task_c_repair="PASS",
                operator_check="PASS",
                focused_tests="PASS",
                fake_go_detected={"policy_doc_only_go_detected": True},
                plan_4_started=False,
            )
        )

    def test_retryable_failure_is_bounded_and_visible(self) -> None:
        created = create_plan3_durable_task("Plan 3 retry proof", max_attempts=2)
        task_id = created["task"]["id"]
        transition_plan3_status(task_id, "policy_checking", reason="policy")
        transition_plan3_status(task_id, "executing", reason="allowed")

        first = record_plan3_failure_attempt(
            task_id,
            failure_class="model_timeout",
            last_error="timeout one",
            retryable=True,
        )
        second = record_plan3_failure_attempt(
            task_id,
            failure_class="model_timeout",
            last_error="timeout two",
            retryable=True,
        )

        self.assertEqual(first["task"]["plan_3_durable_state"]["attempt_count"], 1)
        self.assertEqual(second["task"]["status"], "failed_needs_human")
        state = second["task"]["plan_3_durable_state"]
        self.assertEqual(state["attempt_count"], 2)
        self.assertEqual(state["last_failure_class"], "model_timeout")
        self.assertIn("timeout two", state["last_error"])
        self.assertTrue(
            any(event["event_type"] in {"retry", "failure"} for event in state["causal_events_json"])
        )

    def test_recovery_marks_inflight_state_without_duplicate_action(self) -> None:
        created = create_plan3_durable_task("Plan 3 recovery proof")
        task_id = created["task"]["id"]
        transition_plan3_status(task_id, "policy_checking", reason="policy")
        transition_plan3_status(task_id, "executing", reason="allowed")
        transition_plan3_status(task_id, "worker_dispatched", reason="worker sent")

        recovered = recover_plan3_task(task_id)

        state = recovered["task"]["plan_3_durable_state"]
        self.assertEqual(recovered["task"]["status"], "worker_dispatched")
        self.assertEqual(state["recovery_marker"], "recovered_from_worker_dispatched")
        self.assertTrue(state["duplicate_action_prevented"])
        self.assertTrue(
            any(event["event_type"] == "recovery" for event in state["causal_events_json"])
        )

    def test_verifier_failure_triggers_actual_bounded_repair_and_reverify(self) -> None:
        created = create_plan3_durable_task("Plan 3 repair proof")
        task_id = created["task"]["id"]
        transition_plan3_status(task_id, "policy_checking", reason="policy")
        transition_plan3_status(task_id, "executing", reason="allowed")
        transition_plan3_status(task_id, "worker_returned", reason="worker output")
        workspace = Path(self._tempdir.name) / "disposable"
        workspace.mkdir()
        target = workspace / "proof.html"
        target.write_text("<main>broken</main>\n", encoding="utf-8")

        result = run_plan3_verifier_driven_repair(
            task_id,
            workspace=workspace,
            relative_file="proof.html",
            repair_content="<main>fixed</main>\n",
            verifier=lambda path: "fixed" in path.read_text(encoding="utf-8"),
            max_repair_attempts=2,
        )

        state = result["task"]["plan_3_durable_state"]
        self.assertEqual(result["task"]["status"], "verified")
        self.assertEqual(target.read_text(encoding="utf-8"), "<main>fixed</main>\n")
        self.assertEqual(state["repair_attempt_count"], 1)
        self.assertEqual(state["verification_result"], "VERIFIED")
        self.assertEqual(state["repair_result"], "repair_applied_and_reverified")
        event_types = {event["event_type"] for event in state["causal_events_json"]}
        self.assertIn("repair", event_types)
        self.assertIn("verification", event_types)


if __name__ == "__main__":
    unittest.main()
