from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from source_proxy.testing.runner import (
    PROFILE_PROXY_CLOSEOUT,
    PROFILE_PROXY_REGRESSION,
    PROFILE_PROXY_SMOKE,
    PROFILE_PHASE_4F_CLOSEOUT,
    PROFILE_SCOUT_SEARCH_DIAGNOSTICS,
    PROFILE_SCOUT_SEARCH_SMOKE,
    PROFILE_SCOUT_SOAK_SNAPSHOT,
    PROFILE_SCOUT_SOURCE_GATE,
    PROFILE_SCOUT_SMOKE,
    format_runner_report,
    main,
    run_runner_profile,
)


class ProxyRunnerTests(unittest.TestCase):
    def test_proxy_smoke_profile_reports_seeded_safety_pass(self) -> None:
        payload = run_runner_profile(profile=PROFILE_PROXY_SMOKE)

        self.assertEqual(payload["result"], "pass")
        self.assertEqual(payload["smoke_harness"]["summary"]["passed"], 3)
        self.assertEqual(payload["smoke_harness"]["summary"]["failed"], 0)
        self.assertFalse(payload["smoke_harness"]["applied_anything"])
        self.assertTrue(payload["safety_verdict"]["no_approve"])
        self.assertTrue(payload["safety_verdict"]["no_apply"])
        self.assertTrue(payload["safety_verdict"]["no_execute_approved"])
        self.assertTrue(
            payload["safety_verdict"]["approval_unavailable_for_blocked_cases"]
        )
        self.assertTrue(payload["safety_verdict"]["applied_anything_false"])

    def test_proxy_smoke_report_names_cases_and_next_step(self) -> None:
        payload = run_runner_profile(profile=PROFILE_PROXY_SMOKE)
        report = format_runner_report(payload)

        self.assertIn("PROXY TEST RUNNER", report)
        self.assertIn("manual-check-7: PASS", report)
        self.assertIn("manual-check-8: PASS", report)
        self.assertIn("manual-check-9: PASS", report)
        self.assertIn("Recommendation: ready for next increment", report)

    def test_unknown_profile_returns_usage_error_code(self) -> None:
        self.assertEqual(main(["--profile", "missing-profile"]), 2)

    def test_proxy_regression_profile_reports_pytest_pass(self) -> None:
        completed = mock.Mock(returncode=0, stdout="7 passed\n", stderr="")

        with mock.patch("source_proxy.testing.runner.subprocess.run", return_value=completed):
            payload = run_runner_profile(profile=PROFILE_PROXY_REGRESSION)

        self.assertEqual(payload["result"], "pass")
        self.assertEqual(payload["regression_tests"]["result"], "pass")
        self.assertEqual(payload["regression_tests"]["returncode"], 0)
        self.assertEqual(payload["regression_tests"]["missing_files"], [])
        self.assertIn("test_coding_self_tests.py", payload["regression_tests"]["command"])

    def test_proxy_regression_profile_reports_pytest_failure(self) -> None:
        completed = mock.Mock(returncode=1, stdout="1 failed\n", stderr="")

        with mock.patch("source_proxy.testing.runner.subprocess.run", return_value=completed):
            payload = run_runner_profile(profile=PROFILE_PROXY_REGRESSION)

        self.assertEqual(payload["result"], "fail")
        self.assertEqual(payload["recommendation"], "fix needed")

    def test_proxy_regression_profile_reports_missing_files_plainly(self) -> None:
        with mock.patch(
            "source_proxy.testing.runner.REGRESSION_TEST_FILES",
            ["source_proxy/tests/missing_test_file.py"],
        ):
            payload = run_runner_profile(profile=PROFILE_PROXY_REGRESSION)

        self.assertEqual(payload["result"], "fail")
        self.assertEqual(payload["regression_tests"]["result"], "missing_files")
        self.assertEqual(
            payload["regression_tests"]["missing_files"],
            ["source_proxy/tests/missing_test_file.py"],
        )

    def test_proxy_regression_report_includes_failures(self) -> None:
        payload = {
            "profile": PROFILE_PROXY_REGRESSION,
            "result": "fail",
            "regression_tests": {
                "command": "python -m pytest source_proxy/tests/test_example.py",
                "result": "fail",
                "returncode": 1,
                "missing_files": [],
                "stdout": "1 failed\n",
                "stderr": "",
            },
            "recommendation": "fix needed",
        }

        report = format_runner_report(payload)

        self.assertIn("Profile: proxy-regression", report)
        self.assertIn("- result: FAIL", report)
        self.assertIn("1 failed", report)

    def test_proxy_closeout_combines_smoke_regression_and_file_status(self) -> None:
        smoke = run_runner_profile(profile=PROFILE_PROXY_SMOKE)
        regression = {
            "profile": PROFILE_PROXY_REGRESSION,
            "result": "pass",
            "regression_tests": {
                "command": "python -m pytest source_proxy/tests/test_coding_self_tests.py",
                "result": "pass",
                "returncode": 0,
                "missing_files": [],
                "stdout": "6 passed\n",
                "stderr": "",
            },
            "recommendation": "ready for next increment",
        }

        with mock.patch(
            "source_proxy.testing.runner._run_proxy_smoke_profile",
            return_value=smoke,
        ), mock.patch(
            "source_proxy.testing.runner._run_proxy_regression_profile",
            return_value=regression,
        ), mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", "clean"],
        ):
            payload = run_runner_profile(profile=PROFILE_PROXY_CLOSEOUT)

        self.assertEqual(payload["result"], "pass")
        self.assertFalse(payload["file_change_verdict"]["changed_by_test_run"])
        report = format_runner_report(payload)
        self.assertIn("PROXY TEST RUNNER CLOSEOUT", report)
        self.assertIn("manual-check-7: PASS", report)
        self.assertIn("- failures: none", report)
        self.assertIn("- changed by test run: false", report)

    def test_proxy_closeout_fails_when_file_status_changes(self) -> None:
        smoke = run_runner_profile(profile=PROFILE_PROXY_SMOKE)
        regression = {
            "profile": PROFILE_PROXY_REGRESSION,
            "result": "pass",
            "regression_tests": {
                "command": "python -m pytest source_proxy/tests/test_coding_self_tests.py",
                "result": "pass",
                "returncode": 0,
                "missing_files": [],
                "stdout": "6 passed\n",
                "stderr": "",
            },
            "recommendation": "ready for next increment",
        }

        with mock.patch(
            "source_proxy.testing.runner._run_proxy_smoke_profile",
            return_value=smoke,
        ), mock.patch(
            "source_proxy.testing.runner._run_proxy_regression_profile",
            return_value=regression,
        ), mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", " M README.md"],
        ):
            payload = run_runner_profile(profile=PROFILE_PROXY_CLOSEOUT)

        self.assertEqual(payload["result"], "fail")
        self.assertTrue(payload["file_change_verdict"]["changed_by_test_run"])

    def test_phase_4f_closeout_combines_safe_runner_and_scout_checks(self) -> None:
        proxy_closeout = {"profile": PROFILE_PROXY_CLOSEOUT, "result": "pass"}
        command_result = {
            "command": "python -m pytest source_proxy/tests/test_proxy_runner.py",
            "returncode": 0,
            "stdout": "35 passed\n",
            "stderr": "",
            "error": None,
        }
        scout_payload = {"result": "pass"}
        soak_payload = {
            "result": "pass",
            "snapshot_path": "scout/soak-logs/scout-soak-snapshot-2026.json",
        }

        with mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", "clean"],
        ), mock.patch(
            "source_proxy.testing.runner._run_proxy_closeout_profile",
            return_value=proxy_closeout,
        ), mock.patch(
            "source_proxy.testing.runner._run_command",
            return_value=command_result,
        ) as run_command, mock.patch(
            "source_proxy.testing.runner._run_scout_smoke_profile",
            return_value=scout_payload,
        ), mock.patch(
            "source_proxy.testing.runner._run_scout_source_gate_profile",
            return_value=scout_payload,
        ), mock.patch(
            "source_proxy.testing.runner._run_scout_search_diagnostics_profile",
            return_value=scout_payload,
        ), mock.patch(
            "source_proxy.testing.runner._run_scout_soak_snapshot_profile",
            return_value=soak_payload,
        ):
            payload = run_runner_profile(profile=PROFILE_PHASE_4F_CLOSEOUT)

        self.assertEqual(payload["result"], "pass")
        self.assertFalse(payload["file_change_verdict"]["changed_by_test_run"])
        self.assertEqual(payload["optional_checks"]["scout_search_smoke"]["status"], "not_run")
        run_command.assert_called_once()
        report = format_runner_report(payload)
        self.assertIn("PHASE 4F CLOSEOUT", report)
        self.assertIn("proxy closeout: PASS", report)
        self.assertIn("runner self tests: PASS", report)
        self.assertIn("scout search smoke: not run by default", report)
        self.assertIn("approve/apply/commit/push: not run", report)

    def test_phase_4f_closeout_fails_when_required_check_fails(self) -> None:
        proxy_closeout = {"profile": PROFILE_PROXY_CLOSEOUT, "result": "pass"}
        command_result = {
            "command": "python -m pytest source_proxy/tests/test_proxy_runner.py",
            "returncode": 1,
            "stdout": "1 failed\n",
            "stderr": "",
            "error": None,
        }
        scout_payload = {"result": "pass"}

        with mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", "clean"],
        ), mock.patch(
            "source_proxy.testing.runner._run_proxy_closeout_profile",
            return_value=proxy_closeout,
        ), mock.patch(
            "source_proxy.testing.runner._run_command",
            return_value=command_result,
        ), mock.patch(
            "source_proxy.testing.runner._run_scout_smoke_profile",
            return_value=scout_payload,
        ), mock.patch(
            "source_proxy.testing.runner._run_scout_source_gate_profile",
            return_value=scout_payload,
        ), mock.patch(
            "source_proxy.testing.runner._run_scout_search_diagnostics_profile",
            return_value=scout_payload,
        ), mock.patch(
            "source_proxy.testing.runner._run_scout_soak_snapshot_profile",
            return_value=scout_payload,
        ):
            payload = run_runner_profile(profile=PROFILE_PHASE_4F_CLOSEOUT)

        self.assertEqual(payload["result"], "fail")
        self.assertEqual(payload["recommendation"], "fix needed")

    def test_scout_smoke_profile_reports_read_only_snapshot(self) -> None:
        responses = {
            "http://localhost:8077/health": {
                "ok": True,
                "status": 200,
                "url": "http://localhost:8077/health",
                "body": {"status": "ok"},
                "error": None,
            },
            "http://localhost:8077/v1/scout/source-candidates": {
                "ok": True,
                "status": 200,
                "url": "http://localhost:8077/v1/scout/source-candidates",
                "body": {"counts": {"recommended": 2, "blocked": 1}, "candidates": []},
                "error": None,
            },
            "http://localhost:8077/v1/scout/sources": {
                "ok": True,
                "status": 200,
                "url": "http://localhost:8077/v1/scout/sources",
                "body": {
                    "count": 1,
                    "sources": [
                        {
                            "display_uri": "github://fastapi/fastapi",
                            "poller_supported": True,
                        }
                    ],
                },
                "error": None,
            },
            "http://localhost:8077/v1/scout/discovery-jobs": {
                "ok": True,
                "status": 200,
                "url": "http://localhost:8077/v1/scout/discovery-jobs",
                "body": {"count": 3, "jobs": [{"job_id": "job-1"}]},
                "error": None,
            },
        }

        with mock.patch(
            "source_proxy.testing.runner._http_get_json",
            side_effect=lambda url: responses[url],
        ) as get_json:
            payload = run_runner_profile(profile=PROFILE_SCOUT_SMOKE)

        self.assertEqual(payload["result"], "pass")
        self.assertTrue(payload["read_only"])
        self.assertFalse(payload["mutated"])
        self.assertEqual(payload["summary"]["candidate_counts"]["recommended"], 2)
        self.assertEqual(payload["summary"]["active_source_count"], 1)
        self.assertEqual(payload["summary"]["discovery_job_count"], 3)
        self.assertEqual(get_json.call_count, 4)
        report = format_runner_report(payload)
        self.assertIn("SCOUT TEST RUNNER", report)
        self.assertIn("Profile: scout-smoke", report)
        self.assertIn("read_only: true", report)
        self.assertIn("mutated: false", report)
        self.assertIn("github://fastapi/fastapi", report)

    def test_scout_smoke_profile_reports_unavailable_api_plainly(self) -> None:
        with mock.patch(
            "source_proxy.testing.runner._http_get_json",
            return_value={
                "ok": False,
                "status": None,
                "url": "http://localhost:8077/health",
                "body": {},
                "error": "connection refused",
            },
        ):
            payload = run_runner_profile(profile=PROFILE_SCOUT_SMOKE)

        self.assertEqual(payload["result"], "fail")
        self.assertEqual(payload["recommendation"], "fix needed")
        report = format_runner_report(payload)
        self.assertIn("FAIL: connection refused", report)

    def test_scout_source_gate_profile_reports_read_only_invariants(self) -> None:
        responses = {
            "http://localhost:8077/v1/scout/source-candidates?limit=200": {
                "ok": True,
                "status": 200,
                "url": "http://localhost:8077/v1/scout/source-candidates?limit=200",
                "body": {
                    "counts": {"approved": 1, "rejected": 1, "blocked": 1},
                    "candidates": [
                        {
                            "candidate_id": "approved-1",
                            "canonical_uri": "github://fastapi/fastapi",
                            "display_uri": "https://github.com/fastapi/fastapi",
                            "status": "approved",
                            "review_history": [{"action": "approve"}],
                        },
                        {
                            "candidate_id": "rejected-1",
                            "canonical_uri": "https://noisy.example/blog",
                            "status": "rejected",
                            "review_history": [{"action": "reject"}],
                        },
                        {
                            "candidate_id": "blocked-1",
                            "canonical_uri": "https://spam.example/tracker",
                            "status": "blocked",
                            "review_history": [{"action": "block"}],
                        },
                    ],
                },
                "error": None,
            },
            "http://localhost:8077/v1/scout/sources": {
                "ok": True,
                "status": 200,
                "url": "http://localhost:8077/v1/scout/sources",
                "body": {
                    "count": 2,
                    "sources": [
                        {
                            "canonical_uri": "github://fastapi/fastapi",
                            "display_uri": "github://fastapi/fastapi",
                            "poller_supported": True,
                        },
                        {
                            "canonical_uri": "https://www.python.org/downloads/release/python-3130",
                            "display_uri": "https://www.python.org/downloads/release/python-3130/",
                            "poller_supported": False,
                        },
                    ],
                },
                "error": None,
            },
        }

        with mock.patch(
            "source_proxy.testing.runner._http_get_json",
            side_effect=lambda url: responses[url],
        ) as get_json:
            payload = run_runner_profile(profile=PROFILE_SCOUT_SOURCE_GATE)

        self.assertEqual(payload["result"], "pass")
        self.assertTrue(payload["read_only"])
        self.assertFalse(payload["mutated"])
        self.assertTrue(payload["invariants"]["rejected_blocked_not_active"])
        self.assertTrue(payload["invariants"]["approved_candidates_active"])
        self.assertEqual(
            payload["summary"]["unsupported_active_sources"],
            ["https://www.python.org/downloads/release/python-3130/"],
        )
        self.assertEqual(get_json.call_count, 2)
        report = format_runner_report(payload)
        self.assertIn("SCOUT SOURCE GATE RUNNER", report)
        self.assertIn("rejected/blocked candidates not active: true", report)
        self.assertIn("approved candidates active: true", report)
        self.assertIn("mutated: false", report)

    def test_scout_source_gate_profile_fails_when_rejected_candidate_is_active(self) -> None:
        responses = {
            "http://localhost:8077/v1/scout/source-candidates?limit=200": {
                "ok": True,
                "status": 200,
                "url": "http://localhost:8077/v1/scout/source-candidates?limit=200",
                "body": {
                    "counts": {"rejected": 1},
                    "candidates": [
                        {
                            "candidate_id": "rejected-1",
                            "canonical_uri": "https://noisy.example/blog",
                            "status": "rejected",
                        },
                    ],
                },
                "error": None,
            },
            "http://localhost:8077/v1/scout/sources": {
                "ok": True,
                "status": 200,
                "url": "http://localhost:8077/v1/scout/sources",
                "body": {
                    "count": 1,
                    "sources": [
                        {
                            "canonical_uri": "https://noisy.example/blog",
                            "display_uri": "https://noisy.example/blog",
                            "poller_supported": False,
                        }
                    ],
                },
                "error": None,
            },
        }

        with mock.patch(
            "source_proxy.testing.runner._http_get_json",
            side_effect=lambda url: responses[url],
        ):
            payload = run_runner_profile(profile=PROFILE_SCOUT_SOURCE_GATE)

        self.assertEqual(payload["result"], "fail")
        self.assertFalse(payload["invariants"]["rejected_blocked_not_active"])
        self.assertEqual(
            payload["summary"]["rejected_or_blocked_active"],
            ["https://noisy.example/blog"],
        )

    def test_scout_search_diagnostics_reports_missing_env_wiring(self) -> None:
        compose = {
            "ok": True,
            "path": "scout/docker-compose.scout.yml",
            "error": None,
            "env_file_mentions": [".env"],
            "search_env_wired": False,
            "searxng_url_wired": False,
        }
        env = {
            "command": "docker exec scout_v0_1 env",
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "error": None,
            "keys": [],
            "search_enabled_present": False,
            "searxng_url_present": False,
        }
        settings = {
            "command": "docker exec scout_v0_1 python",
            "returncode": 0,
            "stdout": "{}",
            "stderr": "",
            "error": None,
            "settings": {
                "search_enabled": False,
                "searxng_url_present": False,
                "search_provider": "searxng",
            },
        }
        host = {
            "ok": True,
            "status": 200,
            "url": "http://localhost:8080/search?q=fastapi&format=json",
            "body": {"results": []},
            "error": None,
        }
        probe = {
            "ok": False,
            "status": None,
            "url": "http://spirit-searxng:8080/search?q=fastapi&format=json",
            "body": {},
            "error": "name resolution failed",
        }

        with mock.patch(
            "source_proxy.testing.runner._inspect_scout_compose",
            return_value=compose,
        ), mock.patch(
            "source_proxy.testing.runner._inspect_scout_container_env",
            return_value=env,
        ), mock.patch(
            "source_proxy.testing.runner._inspect_scout_container_settings",
            return_value=settings,
        ), mock.patch(
            "source_proxy.testing.runner._http_get_json",
            return_value=host,
        ), mock.patch(
            "source_proxy.testing.runner._probe_container_url",
            return_value=probe,
        ):
            payload = run_runner_profile(profile=PROFILE_SCOUT_SEARCH_DIAGNOSTICS)

        self.assertEqual(payload["result"], "fail")
        self.assertTrue(payload["read_only"])
        self.assertFalse(payload["mutated"])
        self.assertIn(
            "Scout container does not receive SCOUT_SEARCH_ENABLED / SCOUT_SEARXNG_URL",
            payload["findings"],
        )
        self.assertIn(
            "SearXNG reachable from host but returned 0 results",
            payload["findings"],
        )
        report = format_runner_report(payload)
        self.assertIn("SCOUT SEARCH DIAGNOSTICS", report)
        self.assertIn("SCOUT_SEARCH_ENABLED present: false", report)
        self.assertIn("Recommendation: fix needed", report)

    def test_scout_search_diagnostics_passes_when_env_and_provider_work(self) -> None:
        compose = {
            "ok": True,
            "path": "scout/docker-compose.scout.yml",
            "error": None,
            "env_file_mentions": [".env"],
            "search_env_wired": True,
            "searxng_url_wired": True,
        }
        env = {
            "command": "docker exec scout_v0_1 env",
            "returncode": 0,
            "stdout": "SCOUT_SEARCH_ENABLED=true\nSCOUT_SEARXNG_URL=http://searxng:8080\n",
            "stderr": "",
            "error": None,
            "keys": ["SCOUT_SEARCH_ENABLED", "SCOUT_SEARXNG_URL"],
            "search_enabled_present": True,
            "searxng_url_present": True,
        }
        settings = {
            "command": "docker exec scout_v0_1 python",
            "returncode": 0,
            "stdout": "{}",
            "stderr": "",
            "error": None,
            "settings": {
                "search_enabled": True,
                "searxng_url_present": True,
                "search_provider": "searxng",
                "search_max_results": 5,
                "search_timeout_seconds": 10,
                "discovery_jobs_enabled": True,
                "discovery_jobs_per_day": 3,
                "discovery_candidates_per_job": 5,
            },
        }
        ok_search = {
            "ok": True,
            "status": 200,
            "url": "http://localhost:8080/search?q=fastapi&format=json",
            "body": {"results": [{"url": "https://fastapi.tiangolo.com"}]},
            "error": None,
        }

        with mock.patch(
            "source_proxy.testing.runner._inspect_scout_compose",
            return_value=compose,
        ), mock.patch(
            "source_proxy.testing.runner._inspect_scout_container_env",
            return_value=env,
        ), mock.patch(
            "source_proxy.testing.runner._inspect_scout_container_settings",
            return_value=settings,
        ), mock.patch(
            "source_proxy.testing.runner._http_get_json",
            return_value=ok_search,
        ), mock.patch(
            "source_proxy.testing.runner._probe_container_url",
            return_value=ok_search,
        ):
            payload = run_runner_profile(profile=PROFILE_SCOUT_SEARCH_DIAGNOSTICS)

        self.assertEqual(payload["result"], "pass")
        self.assertEqual(payload["findings"], [])
        self.assertEqual(payload["recommendation"], "ready for search smoke")

    def test_scout_compose_wires_search_environment(self) -> None:
        from source_proxy.testing.runner import _inspect_scout_compose

        payload = _inspect_scout_compose(Path("scout/docker-compose.scout.yml"))

        self.assertTrue(payload["ok"])
        self.assertTrue(payload["search_env_wired"])
        self.assertTrue(payload["searxng_url_wired"])
        self.assertTrue(payload["search_max_results_wired"])
        self.assertTrue(payload["search_timeout_wired"])
        self.assertEqual(payload["env_file_mentions"], [".env"])

    def test_scout_local_compose_adds_host_gateway_for_all_api_profiles(self) -> None:
        text = Path("scout/docker-compose.local.yml").read_text(encoding="utf-8")

        self.assertIn("scout-api:", text)
        self.assertIn("scout-api-nvidia:", text)
        self.assertIn("scout-api-amd:", text)
        self.assertEqual(text.count("host.docker.internal:host-gateway"), 3)

    def test_scout_search_smoke_profile_bounds_preview_extract_effects(self) -> None:
        before_candidates = {
            "ok": True,
            "status": 200,
            "url": "http://localhost:8077/v1/scout/source-candidates?limit=200",
            "body": {"counts": {"recommended": 1, "approved": 2}, "candidates": [{"candidate_id": "old-1"}]},
            "error": None,
        }
        after_preview_candidates = {
            **before_candidates,
            "body": {"counts": {"recommended": 1, "approved": 2}, "candidates": [{"candidate_id": "old-1"}]},
        }
        after_extract_candidates = {
            **before_candidates,
            "body": {
                "counts": {"recommended": 2, "approved": 2},
                "candidates": [
                    {"candidate_id": "old-1"},
                    {
                        "candidate_id": "new-1",
                        "canonical_uri": "https://github.com/pydantic/pydantic/releases",
                        "status": "recommended",
                        "discovered_from_uri": "search://official-pydantic-github-repository-release-notes",
                        "reason_codes": ["discovered_from_search_result"],
                    },
                ],
            },
        }
        sources = {
            "ok": True,
            "status": 200,
            "url": "http://localhost:8077/v1/scout/sources",
            "body": {"count": 5, "sources": [{"canonical_uri": "github://fastapi/fastapi"}]},
            "error": None,
        }
        create = {
            "ok": True,
            "status": 201,
            "url": "http://localhost:8077/v1/scout/discovery-jobs",
            "body": {"job": {"job_id": "job-search-smoke"}},
            "error": None,
        }
        preview = {
            "ok": True,
            "status": 200,
            "url": "http://localhost:8077/v1/scout/discovery-jobs/job-search-smoke/search-preview",
            "body": {"result": {"results": [{"url": "https://github.com/pydantic/pydantic/releases"}]}},
            "error": None,
        }
        extract = {
            "ok": True,
            "status": 200,
            "url": "http://localhost:8077/v1/scout/discovery-jobs/job-search-smoke/extract-candidates",
            "body": {"candidate_effect": "created_or_updated"},
            "error": None,
        }
        get_responses = [
            before_candidates,
            sources,
            after_preview_candidates,
            sources,
            after_extract_candidates,
            sources,
        ]
        post_responses = [create, preview, extract]

        with mock.patch(
            "source_proxy.testing.runner._http_get_json",
            side_effect=get_responses,
        ) as get_json, mock.patch(
            "source_proxy.testing.runner._http_post_json",
            side_effect=post_responses,
        ) as post_json:
            payload = run_runner_profile(profile=PROFILE_SCOUT_SEARCH_SMOKE)

        self.assertEqual(payload["result"], "pass")
        self.assertFalse(payload["read_only"])
        self.assertTrue(payload["bounded"])
        self.assertTrue(payload["mutated"])
        self.assertEqual(payload["summary"]["preview_candidate_delta"], 0)
        self.assertEqual(payload["summary"]["extract_candidate_delta"], 1)
        self.assertEqual(payload["summary"]["source_count_delta"], 0)
        self.assertEqual(payload["summary"]["approved_count_before"], 2)
        self.assertEqual(payload["summary"]["approved_count_after"], 2)
        self.assertTrue(payload["invariants"]["preview_does_not_create_candidates"])
        self.assertTrue(payload["invariants"]["extract_does_not_change_sources"])
        self.assertTrue(payload["invariants"]["no_auto_approval"])
        self.assertEqual(get_json.call_count, 6)
        self.assertEqual(post_json.call_count, 3)
        report = format_runner_report(payload)
        self.assertIn("SCOUT SEARCH SMOKE RUNNER", report)
        self.assertIn("preview candidate delta: 0", report)
        self.assertIn("source count delta: 0", report)
        self.assertIn("no auto approval: true", report)

    def test_scout_search_smoke_fails_if_preview_creates_candidates(self) -> None:
        before_candidates = {
            "ok": True,
            "status": 200,
            "url": "",
            "body": {"counts": {"recommended": 1}, "candidates": [{"candidate_id": "old-1"}]},
            "error": None,
        }
        after_preview_candidates = {
            **before_candidates,
            "body": {
                "counts": {"recommended": 2},
                "candidates": [{"candidate_id": "old-1"}, {"candidate_id": "preview-created"}],
            },
        }
        sources = {"ok": True, "status": 200, "url": "", "body": {"count": 1, "sources": []}, "error": None}
        create = {"ok": True, "status": 201, "url": "", "body": {"job": {"job_id": "job-1"}}, "error": None}
        ok_post = {"ok": True, "status": 200, "url": "", "body": {"result": {"results": []}}, "error": None}

        with mock.patch(
            "source_proxy.testing.runner._http_get_json",
            side_effect=[
                before_candidates,
                sources,
                after_preview_candidates,
                sources,
                after_preview_candidates,
                sources,
            ],
        ), mock.patch(
            "source_proxy.testing.runner._http_post_json",
            side_effect=[create, ok_post, ok_post],
        ):
            payload = run_runner_profile(profile=PROFILE_SCOUT_SEARCH_SMOKE)

        self.assertEqual(payload["result"], "fail")
        self.assertFalse(payload["invariants"]["preview_does_not_create_candidates"])

    def test_scout_search_smoke_report_includes_create_job_error_detail(self) -> None:
        candidates = {
            "ok": True,
            "status": 200,
            "url": "",
            "body": {"counts": {}, "candidates": []},
            "error": None,
        }
        sources = {
            "ok": True,
            "status": 200,
            "url": "",
            "body": {"count": 0, "sources": []},
            "error": None,
        }
        create_error = {
            "ok": False,
            "status": 422,
            "url": "http://localhost:8077/v1/scout/discovery-jobs",
            "body": {"detail": "daily discovery job limit reached"},
            "error": "HTTP Error 422: Unprocessable Entity",
        }

        with mock.patch(
            "source_proxy.testing.runner._http_get_json",
            side_effect=[candidates, sources, candidates, sources, candidates, sources],
        ), mock.patch(
            "source_proxy.testing.runner._http_post_json",
            return_value=create_error,
        ):
            payload = run_runner_profile(profile=PROFILE_SCOUT_SEARCH_SMOKE)

        report = format_runner_report(payload)

        self.assertEqual(payload["result"], "fail")
        self.assertIn("create discovery job: FAIL (422): daily discovery job limit reached", report)

    def test_scout_soak_snapshot_writes_timestamped_report(self) -> None:
        import tempfile
        from source_proxy.testing.runner import _run_scout_soak_snapshot_profile

        health = {"ok": True, "status": 200, "url": "", "body": {"status": "observing"}, "error": None}
        candidates = {
            "ok": True,
            "status": 200,
            "url": "",
            "body": {"counts": {"recommended": 2}, "candidates": []},
            "error": None,
        }
        sources = {
            "ok": True,
            "status": 200,
            "url": "",
            "body": {"count": 1, "sources": [{"canonical_uri": "github://fastapi/fastapi"}]},
            "error": None,
        }
        jobs = {
            "ok": True,
            "status": 200,
            "url": "",
            "body": {"count": 1, "jobs": [{"job_id": "job-1"}]},
            "error": None,
        }
        logs = {
            "command": "docker logs --tail 80 scout_v0_1",
            "returncode": 0,
            "stdout": "INFO all quiet\n",
            "stderr": "",
            "error": None,
        }

        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch(
            "source_proxy.testing.runner._http_get_json",
            side_effect=[health, candidates, sources, jobs],
        ), mock.patch(
            "source_proxy.testing.runner._file_size",
            return_value={"path": "scout/data/scout.db", "size_bytes": 1234, "error": None},
        ), mock.patch(
            "source_proxy.testing.runner._run_command",
            return_value=logs,
        ):
            payload = _run_scout_soak_snapshot_profile(output_dir=Path(tmp_dir))

            snapshot_path = Path(payload["snapshot_path"])
            self.assertTrue(snapshot_path.is_file())
            saved = json.loads(snapshot_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["result"], "pass")
        self.assertFalse(payload["mutated"])
        self.assertTrue(payload["wrote_snapshot"])
        self.assertEqual(saved["summary"]["db_size_bytes"], 1234)
        self.assertEqual(saved["summary"]["warnings"], [])
        report = format_runner_report(payload)
        self.assertIn("SCOUT SOAK SNAPSHOT", report)
        self.assertIn("wrote_snapshot: true", report)

    def test_scout_soak_snapshot_reports_log_warnings(self) -> None:
        import tempfile
        from source_proxy.testing.runner import _run_scout_soak_snapshot_profile

        ok = {"ok": True, "status": 200, "url": "", "body": {}, "error": None}
        logs = {
            "command": "docker logs --tail 80 scout_v0_1",
            "returncode": 0,
            "stdout": "ERROR search provider failed\n",
            "stderr": "",
            "error": None,
        }

        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch(
            "source_proxy.testing.runner._http_get_json",
            side_effect=[ok, ok, ok, ok],
        ), mock.patch(
            "source_proxy.testing.runner._file_size",
            return_value={"path": "scout/data/scout.db", "size_bytes": 1234, "error": None},
        ), mock.patch(
            "source_proxy.testing.runner._run_command",
            return_value=logs,
        ):
            payload = _run_scout_soak_snapshot_profile(output_dir=Path(tmp_dir))

        self.assertEqual(payload["result"], "fail")
        self.assertIn("recent docker logs contain error", payload["summary"]["warnings"])

    def test_scout_soak_snapshot_ignores_empty_error_counters(self) -> None:
        import tempfile
        from source_proxy.testing.runner import _run_scout_soak_snapshot_profile

        ok = {"ok": True, "status": 200, "url": "", "body": {}, "error": None}
        logs = {
            "command": "docker logs --tail 80 scout_v0_1",
            "returncode": 0,
            "stdout": (
                '{"checked": 0, "processed": 0, "errors": 0, "event": "debugger_run_complete"}\n'
                '{"checked": 0, "processed": 0, "errors": [], "event": "packet_synthesis_run_complete"}\n'
            ),
            "stderr": "",
            "error": None,
        }

        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch(
            "source_proxy.testing.runner._http_get_json",
            side_effect=[ok, ok, ok, ok],
        ), mock.patch(
            "source_proxy.testing.runner._file_size",
            return_value={"path": "scout/data/scout.db", "size_bytes": 1234, "error": None},
        ), mock.patch(
            "source_proxy.testing.runner._run_command",
            return_value=logs,
        ):
            payload = _run_scout_soak_snapshot_profile(output_dir=Path(tmp_dir))

        self.assertEqual(payload["result"], "pass")
        self.assertEqual(payload["summary"]["warnings"], [])


if __name__ == "__main__":
    unittest.main()
