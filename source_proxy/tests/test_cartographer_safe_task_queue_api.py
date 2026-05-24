from __future__ import annotations

from datetime import UTC, datetime, timedelta
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.cartographer.safe_task_queue import SAFE_TASK_TRUST_TIER


def _test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(cartographer_router)
    return test_app


class CartographerSafeTaskQueueApiTests(unittest.TestCase):
    def test_run_next_status_route_exists_without_execution_authority(self) -> None:
        client = TestClient(_test_app())

        response = client.get("/v1/cartographer/queue/run-next")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["queue"]["status"], "model-only")
        self.assertEqual(payload["run_next"]["status"], "available")
        self.assertEqual(payload["run_next"]["method"], "POST")
        self.assertTrue(payload["run_next"]["selection_available"])
        self.assertFalse(payload["run_next"]["execution_available"])
        self.assertFalse(payload["run_next"]["durable_storage_available"])
        self.assertFalse(payload["run_next"]["queue_worker_available"])
        self.assertFalse(payload["run_next"]["background_loop_available"])
        self.assertTrue(payload["run_next"]["run_selected_task_available"])
        self.assertTrue(payload["run_next"]["receipt_available"])

    def test_run_next_post_selects_exactly_one_eligible_task(self) -> None:
        client = TestClient(_test_app())

        response = client.post(
            "/v1/cartographer/queue/run-next",
            json={
                "queue_records": [
                    self._record("task-1", "safe_docs_evidence_maintenance"),
                    self._record("task-2", "safe_receipt_closeout"),
                ],
                "expected_trust_tier": SAFE_TASK_TRUST_TIER,
                "expected_approval_token_id": "approval-token-plan-6-phase-3",
                "kill_switch_active": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        selection = payload["selection"]
        self.assertTrue(selection["selected"])
        self.assertFalse(selection["blocked"])
        self.assertEqual(selection["status"], "selected")
        self.assertEqual(selection["selected_count"], 1)
        self.assertEqual(selection["eligible_count"], 2)
        self.assertEqual(selection["selected_task_id"], "task-1")
        self.assertEqual(selection["selected_task"]["status"], "selected")
        self.assertEqual(selection["selected_task"]["task_class"], "safe_docs_evidence_maintenance")
        self.assertFalse(selection["execution_available"])
        self.assertFalse(selection["write_authority_granted"])
        self.assertFalse(selection["git_mutation_authority_granted"])
        self.assertFalse(selection["background_loop_available"])

    def test_run_next_post_runs_one_proposal_only_task_and_returns_receipt_when_requested(self) -> None:
        client = TestClient(_test_app())

        response = client.post(
            "/v1/cartographer/queue/run-next",
            json={
                "queue_records": [
                    self._record("task-1", "safe_blueprint_refresh_proposal_only"),
                    self._record("task-2", "safe_stale_plan_summary_proposal_only"),
                ],
                "expected_trust_tier": SAFE_TASK_TRUST_TIER,
                "expected_approval_token_id": "approval-token-plan-6-phase-3",
                "kill_switch_active": False,
                "run_selected_task": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        run = payload["run"]
        self.assertTrue(run["completed"])
        self.assertFalse(run["blocked"])
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["selected_count"], 1)
        self.assertEqual(run["completed_count"], 1)
        self.assertEqual(run["selected_task_id"], "task-1")
        self.assertEqual(run["receipt"]["schema_version"], "cartographer.safe_task_run_receipt.v1")
        self.assertEqual(run["receipt"]["task_class"], "safe_blueprint_refresh_proposal_only")
        self.assertFalse(run["source_write_performed"])
        self.assertFalse(run["safe_write_performed"])
        self.assertFalse(run["verification_run_performed"])
        self.assertFalse(run["command_run_performed"])
        self.assertFalse(run["git_mutation_performed"])
        self.assertFalse(run["background_loop_available"])

    def test_run_next_post_blocks_without_exact_token_or_when_kill_switch_active(self) -> None:
        client = TestClient(_test_app())
        cases = [
            (
                {
                    "queue_records": [self._record("task-1", "safe_docs_evidence_maintenance")],
                    "expected_trust_tier": SAFE_TASK_TRUST_TIER,
                    "expected_approval_token_id": "",
                    "kill_switch_active": False,
                },
                "no_eligible_pending_task",
            ),
            (
                {
                    "queue_records": [self._record("task-1", "safe_docs_evidence_maintenance")],
                    "expected_trust_tier": SAFE_TASK_TRUST_TIER,
                    "expected_approval_token_id": "approval-token-plan-6-phase-3",
                    "kill_switch_active": True,
                },
                "kill_switch_active",
            ),
        ]

        for body, reason in cases:
            with self.subTest(reason=reason):
                response = client.post("/v1/cartographer/queue/run-next", json=body)

                self.assertEqual(response.status_code, 200)
                selection = response.json()["selection"]
                self.assertFalse(selection["selected"])
                self.assertTrue(selection["blocked"])
                self.assertEqual(selection["selected_count"], 0)
                self.assertIn(reason, selection["reasons"])
                self.assertFalse(selection["execution_available"])
                self.assertFalse(selection["write_authority_granted"])

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 22, 12, 0, 0, tzinfo=UTC)

    def _record(self, task_id: str, task_class: str) -> dict[str, object]:
        return {
            "task_id": task_id,
            "task_class": task_class,
            "trust_tier": SAFE_TASK_TRUST_TIER,
            "approval_token_id": "approval-token-plan-6-phase-3",
            "allowed_files": ["docs/cartographer-live-evidence/example.md"],
            "forbidden_files": ["source_proxy/api/cartographer.py"],
            "status": "pending",
            "attempts": 0,
            "created_at": (self._now() - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
            "selected_at": None,
            "completed_at": None,
            "blocked_reason": None,
        }


if __name__ == "__main__":
    unittest.main()
