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

    def test_manual_check_9_normalized_target_mismatch_blocks_approval(self) -> None:
        payload = run_self_test_suite(
            suite=SUITE_PHASE_4E_SAFETY_SEED,
            case_ids=["manual-check-9"],
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
        self.assertNotIn("path_escape", reasons)
        self.assertNotIn("secret_shaped_path", reasons)
        self.assertNotIn("protected_path", reasons)
        self.assertEqual(case["evidence"]["changed_files"], ["source_proxy/api/decision.py"])
        self.assertIn("task_spec_allowed_file_violation", reasons)
        self.assertIn("task_spec_target_mismatch", reasons)
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
                    "case_ids": ["manual-check-7", "manual-check-8", "manual-check-9"],
                    "mode": "dry_run",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["applied_anything"])
        self.assertEqual(payload["summary"]["failed"], 0)
        if before is not None:
            self.assertEqual(doc_path.read_text(encoding="utf-8"), before)

    def test_endpoint_matches_cli_harness_for_seeded_cases(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)

        cli_payload = run_self_test_suite(
            suite=SUITE_PHASE_4E_SAFETY_SEED,
            case_ids=["manual-check-7", "manual-check-8", "manual-check-9"],
            mode="dry_run",
        )
        response = client.post(
            "/v1/coding/self-tests/run",
            json={
                "suite": SUITE_PHASE_4E_SAFETY_SEED,
                "case_ids": ["manual-check-7", "manual-check-8", "manual-check-9"],
                "mode": "dry_run",
            },
        )

        self.assertEqual(response.status_code, 200)
        api_payload = response.json()
        self.assertEqual(api_payload["summary"], cli_payload["summary"])
        self.assertEqual(api_payload["applied_anything"], cli_payload["applied_anything"])
        self.assertEqual(
            [case["case_id"] for case in api_payload["cases"]],
            [case["case_id"] for case in cli_payload["cases"]],
        )
        self.assertEqual(
            [case["status"] for case in api_payload["cases"]],
            [case["status"] for case in cli_payload["cases"]],
        )

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

    def test_endpoint_accepts_proxy_runner_profile_in_dry_run_mode(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)
        runner_payload = {
            "profile": "proxy-smoke",
            "result": "pass",
            "smoke_harness": {
                "summary": {"passed": 2, "failed": 0, "skipped": 0},
                "applied_anything": False,
            },
            "safety_verdict": {"applied_anything_false": True},
            "recommendation": "ready for next increment",
        }

        with mock.patch(
            "source_proxy.api.coding_self_tests.run_runner_profile",
            return_value=runner_payload,
        ) as run_profile:
            response = client.post(
                "/v1/coding/self-tests/run",
                json={"profile": "proxy-smoke", "mode": "dry_run"},
            )

        self.assertEqual(response.status_code, 200)
        run_profile.assert_called_once_with(profile="proxy-smoke")
        payload = response.json()
        self.assertEqual(payload["profile"], "proxy-smoke")
        self.assertEqual(payload["mode"], "dry_run")
        self.assertFalse(payload["applied_anything"])

    def test_endpoint_accepts_scout_runner_profile_in_dry_run_mode(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)
        runner_payload = {
            "profile": "scout-search-diagnostics",
            "result": "pass",
            "read_only_verdict": {"read_only": True, "mutated": False},
            "recommendation": "ready for search smoke",
        }

        with mock.patch(
            "source_proxy.api.coding_self_tests.run_runner_profile",
            return_value=runner_payload,
        ) as run_profile:
            response = client.post(
                "/v1/coding/self-tests/run",
                json={"profile": "scout-search-diagnostics", "mode": "dry_run"},
            )

        self.assertEqual(response.status_code, 200)
        run_profile.assert_called_once_with(profile="scout-search-diagnostics")
        payload = response.json()
        self.assertEqual(payload["profile"], "scout-search-diagnostics")
        self.assertEqual(payload["mode"], "dry_run")
        self.assertFalse(payload["applied_anything"])

    def test_endpoint_accepts_phase_4f_closeout_profile_in_dry_run_mode(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)
        runner_payload = {
            "profile": "phase-4f-closeout",
            "result": "pass",
            "checks": {"proxy_closeout": True, "scout_smoke": True},
            "recommendation": "ready for 4F closeout",
        }

        with mock.patch(
            "source_proxy.api.coding_self_tests.run_runner_profile",
            return_value=runner_payload,
        ) as run_profile:
            response = client.post(
                "/v1/coding/self-tests/run",
                json={"profile": "phase-4f-closeout", "mode": "dry_run"},
            )

        self.assertEqual(response.status_code, 200)
        run_profile.assert_called_once_with(profile="phase-4f-closeout")
        payload = response.json()
        self.assertEqual(payload["profile"], "phase-4f-closeout")
        self.assertEqual(payload["mode"], "dry_run")
        self.assertFalse(payload["applied_anything"])

    def test_endpoint_accepts_cartographer_safety_profile_in_dry_run_mode(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)
        runner_payload = {
            "profile": "cartographer-safety",
            "result": "pass",
            "checks": {
                "pytest_passed": True,
                "no_unapproved_writes": True,
                "no_unapproved_commits": True,
            },
            "recommendation": "ready for next increment",
        }

        with mock.patch(
            "source_proxy.api.coding_self_tests.run_runner_profile",
            return_value=runner_payload,
        ) as run_profile:
            response = client.post(
                "/v1/coding/self-tests/run",
                json={"profile": "cartographer-safety", "mode": "dry_run"},
            )

        self.assertEqual(response.status_code, 200)
        run_profile.assert_called_once_with(profile="cartographer-safety")
        payload = response.json()
        self.assertEqual(payload["profile"], "cartographer-safety")
        self.assertEqual(payload["mode"], "dry_run")
        self.assertFalse(payload["applied_anything"])

    def test_endpoint_accepts_cartographer_soak_snapshot_profile_in_dry_run_mode(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)
        runner_payload = {
            "profile": "cartographer-soak-snapshot",
            "result": "pass",
            "checks": {"snapshot_log_only": True},
            "recommendation": "ready for next increment",
        }

        with mock.patch(
            "source_proxy.api.coding_self_tests.run_runner_profile",
            return_value=runner_payload,
        ) as run_profile:
            response = client.post(
                "/v1/coding/self-tests/run",
                json={"profile": "cartographer-soak-snapshot", "mode": "dry_run"},
            )

        self.assertEqual(response.status_code, 200)
        run_profile.assert_called_once_with(profile="cartographer-soak-snapshot")
        payload = response.json()
        self.assertEqual(payload["profile"], "cartographer-soak-snapshot")
        self.assertEqual(payload["mode"], "dry_run")
        self.assertFalse(payload["applied_anything"])

    def test_endpoint_rejects_unknown_runner_profile(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)

        response = client.post(
            "/v1/coding/self-tests/run",
            json={"profile": "scout-apply", "mode": "dry_run"},
        )

        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertIn("Unsupported self-test profile", detail["error"])
        self.assertIn("proxy-smoke", detail["supported_profiles"])

    def test_endpoint_rejects_non_dry_run_profile_mode(self) -> None:
        app = FastAPI()
        app.include_router(coding_self_tests_router)
        client = TestClient(app)

        with mock.patch("source_proxy.api.coding_self_tests.run_runner_profile") as run_profile:
            response = client.post(
                "/v1/coding/self-tests/run",
                json={"profile": "proxy-smoke", "mode": "apply"},
            )

        self.assertEqual(response.status_code, 400)
        run_profile.assert_not_called()
        self.assertIn("dry_run", str(response.json()["detail"]))


if __name__ == "__main__":
    unittest.main()
