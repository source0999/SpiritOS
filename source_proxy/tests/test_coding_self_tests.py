from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.coding_self_tests import router as coding_self_tests_router
from source_proxy.testing.self_tests import (
    SUITE_PHASE_4E_SAFETY_SEED,
    run_self_test_suite,
)


class CodingSelfTests(unittest.TestCase):
    def test_manual_check_7_recorded_pass_evidence_validates(self) -> None:
        payload = run_self_test_suite(
            suite=SUITE_PHASE_4E_SAFETY_SEED,
            case_ids=["manual-check-7"],
            mode="dry_run",
        )

        case = payload["cases"][0]
        reasons = {item["reason_code"] for item in case["evidence"]["blocked_reasons"]}
        self.assertEqual(case["status"], "pass")
        self.assertIn("secret_shaped_path", reasons)
        self.assertIn("protected_path", reasons)
        self.assertIn("task_spec_allowed_file_violation", reasons)
        self.assertFalse(case["evidence"]["approval_available"])
        self.assertFalse(payload["applied_anything"])

    def test_manual_check_7_allows_secondary_blockers(self) -> None:
        payload = run_self_test_suite(
            suite=SUITE_PHASE_4E_SAFETY_SEED,
            case_ids=["manual-check-7"],
            mode="dry_run",
        )

        case = payload["cases"][0]
        reasons = {item["reason_code"] for item in case["evidence"]["blocked_reasons"]}
        self.assertEqual(case["status"], "pass")
        self.assertIn("task_spec_target_mismatch", reasons)
        self.assertIn("requirement_coverage_failed", reasons)
        self.assertIn("diff_apply_check_failed", reasons)

    def test_manual_check_8_path_traversal_blocks_approval(self) -> None:
        payload = run_self_test_suite(
            suite=SUITE_PHASE_4E_SAFETY_SEED,
            case_ids=["manual-check-8"],
            mode="dry_run",
        )

        case = payload["cases"][0]
        reasons = {item["reason_code"] for item in case["evidence"]["blocked_reasons"]}
        self.assertEqual(case["status"], "pass")
        self.assertEqual(case["evidence"]["current_workflow_state"], "Blocked")
        self.assertEqual(case["evidence"]["check_code_change"], "blocked")
        self.assertEqual(case["evidence"]["safety_level"], "blocked")
        self.assertEqual(case["evidence"]["would_change_files"], "no")
        self.assertEqual(case["evidence"]["task_spec_allowed_files"], "fail")
        self.assertFalse(case["evidence"]["approval_available"])
        self.assertIn("path_escape", reasons)
        self.assertFalse(payload["applied_anything"])

    def test_endpoint_only_supports_dry_run(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)

        response = client.post(
            "/v1/coding/self-tests/run",
            json={"suite": SUITE_PHASE_4E_SAFETY_SEED, "mode": "apply"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("dry_run", str(response.json()["detail"]))

    def test_endpoint_never_applies_files(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)
        doc_path = Path("docs/phase-8-manual-check.md")
        before = doc_path.read_text(encoding="utf-8") if doc_path.exists() else None

        with mock.patch(
            "source_proxy.tasks.long_running.execute_approved_long_running_task",
            side_effect=AssertionError("self-tests must not execute approved actions"),
        ):
            response = client.post(
                "/v1/coding/self-tests/run",
                json={
                    "suite": SUITE_PHASE_4E_SAFETY_SEED,
                    "case_ids": ["manual-check-7", "manual-check-8"],
                    "mode": "dry_run",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["applied_anything"])
        self.assertEqual(payload["summary"]["failed"], 0)
        if before is not None:
            self.assertEqual(doc_path.read_text(encoding="utf-8"), before)

    def test_codex_style_caller_can_trigger_dry_run_without_extra_permissions(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)

        response = client.post(
            "/v1/coding/self-tests/run",
            json={
                "suite": SUITE_PHASE_4E_SAFETY_SEED,
                "case_ids": ["manual-check-8"],
                "mode": "dry_run",
            },
            headers={"user-agent": "codex-self-test"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["cases"][0]["status"], "pass")
        self.assertFalse(payload["cases"][0]["evidence"]["approval_available"])
        self.assertFalse(payload["applied_anything"])


if __name__ == "__main__":
    unittest.main()

