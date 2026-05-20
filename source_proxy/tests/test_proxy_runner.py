from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from source_proxy.testing.runner import (
    GLOBAL_SAFETY_SCOUT_BACKEND_TIMEOUT_SECONDS,
    PROFILE_CARTOGRAPHER_SAFETY,
    PROFILE_CARTOGRAPHER_SOAK_SNAPSHOT,
    PROFILE_DEPENDENCY_ENVIRONMENT_CHECKS,
    PROFILE_GLOBAL_SAFETY_REGRESSION,
    PROFILE_MOBILE_LAN_TAILSCALE_QA,
    PROFILE_PROXY_CLOSEOUT,
    PROFILE_PROXY_REGRESSION,
    PROFILE_PROXY_SMOKE,
    PROFILE_PHASE_4F_CLOSEOUT,
    PROFILE_SCOUT_SEARCH_DIAGNOSTICS,
    PROFILE_SCOUT_SEARCH_SMOKE,
    PROFILE_SCOUT_SOAK_SNAPSHOT,
    PROFILE_SCOUT_SOURCE_GATE,
    PROFILE_SCOUT_SMOKE,
    _global_safety_mutation_notes,
    _unexpected_level_2_evidence_delta,
    _unexpected_level_2_evidence_in_global_safety,
    _unexpected_status_delta,
    format_runner_report,
    main,
    run_runner_profile,
)


class ProxyRunnerTests(unittest.TestCase):
    def test_cartographer_safety_profile_reports_pytest_and_write_verdicts(self) -> None:
        completed = mock.Mock(returncode=0, stdout="94 passed\n", stderr="")

        with mock.patch("source_proxy.testing.runner.subprocess.run") as run:
            run.side_effect = [
                mock.Mock(returncode=0, stdout="", stderr=""),
                mock.Mock(returncode=0, stdout="abc123\n", stderr=""),
                completed,
                mock.Mock(returncode=0, stdout="", stderr=""),
                mock.Mock(returncode=0, stdout="abc123\n", stderr=""),
            ]
            payload = run_runner_profile(profile=PROFILE_CARTOGRAPHER_SAFETY)

        self.assertEqual(payload["result"], "pass")
        self.assertEqual(payload["regression_tests"]["result"], "pass")
        self.assertIn("test_cartographer_safety_audit.py", payload["regression_tests"]["command"])
        self.assertTrue(payload["safety_verdict"]["no_unapproved_writes"])
        self.assertTrue(payload["safety_verdict"]["no_unapproved_commits"])
        self.assertFalse(payload["mutated"])
        self.assertFalse(payload["applied_anything"])
        self.assertFalse(payload["commit_ran"])
        self.assertFalse(payload["push_ran"])

    def test_cartographer_safety_report_names_expected_outcomes(self) -> None:
        payload = {
            "profile": PROFILE_CARTOGRAPHER_SAFETY,
            "result": "pass",
            "regression_tests": {
                "command": "python -m pytest source_proxy/tests/test_cartographer_safety_audit.py",
                "result": "pass",
                "returncode": 0,
                "stdout": "94 passed\n",
                "stderr": "",
            },
            "safety_verdict": {
                "no_unapproved_writes": True,
                "no_unapproved_apply": True,
                "no_unapproved_commits": True,
                "no_unapproved_pushes": True,
                "approval_bypass_locked": True,
            },
            "file_change_verdict": {
                "before": "clean",
                "after": "clean",
                "changed_by_test_run": False,
                "head_changed": False,
            },
            "expected_outcomes": [
                "Cartographer safety audit: passed",
                "No unapproved writes",
                "No unapproved commits",
                "No unapproved pushes",
            ],
            "recommendation": "ready for next increment",
        }

        report = format_runner_report(payload)

        self.assertIn("CARTOGRAPHER SAFETY AUDIT", report)
        self.assertIn("No unapproved writes", report)
        self.assertIn("Recommendation: ready for next increment", report)

    def test_cartographer_safety_profile_ignores_background_scout_soak_snapshot(self) -> None:
        completed = mock.Mock(returncode=0, stdout="94 passed\n", stderr="")
        after_status = "?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212901Z.json\n"

        with mock.patch("source_proxy.testing.runner.subprocess.run") as run:
            run.side_effect = [
                mock.Mock(returncode=0, stdout="", stderr=""),
                mock.Mock(returncode=0, stdout="abc123\n", stderr=""),
                completed,
                mock.Mock(returncode=0, stdout=after_status, stderr=""),
                mock.Mock(returncode=0, stdout="abc123\n", stderr=""),
            ]
            payload = run_runner_profile(profile=PROFILE_CARTOGRAPHER_SAFETY)

        self.assertEqual(payload["result"], "pass")
        self.assertFalse(payload["file_change_verdict"]["changed_by_test_run"])
        self.assertEqual(payload["file_change_verdict"]["unexpected_status_delta"], [])
        self.assertEqual(
            payload["file_change_verdict"]["background_status_delta"],
            [after_status.strip()],
        )

    def test_mutation_policy_allows_level_2_evidence_only_in_explicit_profile(self) -> None:
        level_2_status = "?? scout/soak-logs/scout-level-2-evidence-2026-05-20T015829Z.json"
        scout_soak_status = "?? scout/soak-logs/scout-soak-snapshot-2026-05-20T015829Z.json"

        self.assertEqual(_unexpected_level_2_evidence_delta([level_2_status]), [])
        self.assertEqual(_unexpected_status_delta([scout_soak_status]), [])
        self.assertEqual(_unexpected_status_delta([level_2_status]), [level_2_status])
        self.assertEqual(
            _unexpected_level_2_evidence_in_global_safety([level_2_status]),
            [level_2_status],
        )
        self.assertEqual(_unexpected_level_2_evidence_in_global_safety([scout_soak_status]), [])

    def test_global_safety_level_2_evidence_note_explains_concurrent_snapshot_risk(self) -> None:
        level_2_status = "?? scout/soak-logs/scout-level-2-evidence-2026-05-20T015829Z.json"

        notes = _global_safety_mutation_notes([level_2_status])

        self.assertEqual(len(notes), 1)
        self.assertIn("expected only during the explicit scout-level-2-evidence-snapshot profile", notes[0])
        self.assertIn("concurrent/manual Level 2 evidence run", notes[0])
        self.assertIn("another wrapper invoked that profile nearby", notes[0])

    def test_cartographer_soak_snapshot_writes_reliability_report(self) -> None:
        from source_proxy.testing.runner import _run_cartographer_soak_snapshot_profile

        safety = {
            "write_policy": "read_only",
            "approval_required_for_file_writes": True,
            "approval_required_for_commits": True,
            "approval_required_for_pushes": True,
            "scout_bypass_allowed": False,
            "source_proxy_approval_bypass_allowed": False,
            "docs_autopilot_enabled": False,
            "docs_autopilot_daily_cap": 0,
            "autopilot_kill_switch": True,
            "autopilot_action_available": False,
        }
        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", "clean"],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_status",
            return_value={
                "status": "observing",
                "write_actions_enabled": False,
                "projects": [{"project_id": "spiritos"}],
                "blueprint_count": 8,
                "safety": safety,
            },
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_git",
            return_value={
                "git_statuses": [
                    {
                        "branch": "cartographer/docs-blueprint-review",
                        "dirty": False,
                        "changed_file_count": 0,
                        "staged": 0,
                        "unstaged": 0,
                        "untracked": 0,
                    }
                ]
            },
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_project_health",
            return_value={"projects": [{"merge_ready": True, "merge_blockers": []}]},
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_proposals",
            return_value={
                "proposal_count": 2,
                "pending_proposals": 0,
                "deduped": True,
                "duplicate_proposals_present": 0,
            },
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_drift",
            return_value={"drift_count": 0},
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_commit_proposals",
            return_value={"commit_proposal_count": 0},
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_push_queue",
            return_value={"push_count": 0},
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_audit_trail",
            return_value={"events": [{"event": "commit_created"}, {"event": "push_approved"}]},
        ):
            payload = _run_cartographer_soak_snapshot_profile(output_dir=Path(tmp_dir))
            self.assertTrue(Path(payload["snapshot_path"]).is_file())

        self.assertEqual(payload["profile"], PROFILE_CARTOGRAPHER_SOAK_SNAPSHOT)
        self.assertEqual(payload["result"], "pass")
        self.assertEqual(payload["summary"]["proposal_count"], 2)
        self.assertEqual(payload["summary"]["audit_event_counts"]["commit_created"], 1)
        self.assertGreaterEqual(payload["reliability"]["score"], 90)
        self.assertTrue(payload["mutation_boundary"]["snapshot_log_only"])
        self.assertTrue(payload["autonomy_escalation"]["passed"])
        self.assertTrue(payload["autonomy_escalation"]["checks"]["autonomous_apply_disabled"])
        self.assertTrue(payload["autonomy_escalation"]["checks"]["autonomous_commit_disabled"])
        self.assertTrue(payload["autonomy_escalation"]["checks"]["autonomous_push_disabled"])

    def test_cartographer_soak_snapshot_report_names_manual_outcomes(self) -> None:
        payload = {
            "profile": PROFILE_CARTOGRAPHER_SOAK_SNAPSHOT,
            "result": "pass",
            "timestamp": "2026-05-16T21:40:00+00:00",
            "snapshot_path": "source_proxy/cartographer/soak-logs/cartographer-soak-snapshot.json",
            "summary": {
                "branch": "cartographer/docs-blueprint-review",
                "dirty": False,
                "changed_file_count": 0,
                "blueprint_count": 8,
                "proposal_count": 2,
                "pending_proposals": 0,
                "duplicate_proposals_present": 0,
                "drift_count": 0,
                "commit_proposal_count": 0,
                "push_queue_count": 0,
                "audit_event_count": 4,
            },
            "reliability": {"score": 95, "grade": "boring", "penalties": []},
            "mutation_boundary": {
                "snapshot_log_only": True,
                "unexpected_status_delta": [],
                "head_changed": False,
            },
            "autonomy_escalation": {
                "passed": True,
                "checks": {
                    "autonomous_apply_disabled": True,
                    "autonomous_commit_disabled": True,
                    "autonomous_push_disabled": True,
                    "docs_autopilot_disabled_or_explicit": True,
                    "approval_bypasses_locked": True,
                },
                "failures": [],
            },
            "warnings": [],
            "next_actions": [
                "Run two more cartographer-soak-snapshot checks before considering 6.21.",
            ],
            "expected_outcomes": [
                "cartographer-soak-snapshot: pass",
                "mutation boundary: snapshot log only",
                "recommendation: ready for next increment",
            ],
            "recommendation": "ready for next increment",
        }

        report = format_runner_report(payload)

        self.assertIn("CARTOGRAPHER SOAK SNAPSHOT", report)
        self.assertIn("score: 95", report)
        self.assertIn("mutation boundary: snapshot log only", report)
        self.assertIn("autonomous apply disabled: true", report)
        self.assertIn("Recommendation: ready for next increment", report)

    def test_cartographer_soak_snapshot_watch_grade_recommends_continue_soak(self) -> None:
        from source_proxy.testing.runner import _run_cartographer_soak_snapshot_profile

        safety = {
            "write_policy": "read_only",
            "approval_required_for_file_writes": True,
            "approval_required_for_commits": True,
            "approval_required_for_pushes": True,
            "scout_bypass_allowed": False,
            "source_proxy_approval_bypass_allowed": False,
            "docs_autopilot_enabled": False,
            "docs_autopilot_daily_cap": 0,
            "autopilot_kill_switch": True,
            "autopilot_action_available": False,
        }
        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch(
            "source_proxy.cartographer.service.build_cartographer_status",
            return_value={
                "status": "observing",
                "write_actions_enabled": False,
                "projects": [{"project_id": "spiritos"}],
                "blueprint_count": 8,
                "safety": safety,
            },
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_git",
            return_value={
                "git_statuses": [
                    {
                        "branch": "cartographer/docs-blueprint-review",
                        "dirty": True,
                        "changed_files": ["source_proxy/cartographer/service.py"],
                    }
                ]
            },
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_project_health",
            return_value={"projects": [{"merge_ready": False, "merge_blockers": ["working tree has uncommitted changes"]}]},
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_proposals",
            return_value={
                "proposal_count": 12,
                "pending_proposals": 10,
                "deduped": True,
                "duplicate_proposals_present": 0,
                "proposals": [
                    {
                        "proposal_id": "bp-project-scout-component-code-changed-24f17bf2",
                        "status": "drafted",
                        "component": "scout",
                        "risk": "medium",
                        "changed_file_count": 29,
                        "proposed_files": ["_blueprints/current/system_state.md"],
                    }
                ],
            },
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_drift",
            return_value={
                "drift_count": 10,
                "drift": [
                    {
                        "drift_id": "drift-scout-component-code-changed",
                        "component": "scout",
                        "reason": "component_code_changed",
                        "changed_files": ["scout/src/scout/api/sources.py"],
                    }
                ],
            },
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_commit_proposals",
            return_value={
                "commit_proposal_count": 22,
                "commit_proposals": [
                    {
                        "commit_proposal_id": "commit-prop-46a7e40f39aa",
                        "component": "scout",
                        "risk": "medium",
                        "suggested_message": "feat(scout): update scout",
                        "files": ["scout/src/scout/api/sources.py"],
                    }
                ],
            },
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_push_queue",
            return_value={"push_count": 0},
        ), mock.patch(
            "source_proxy.cartographer.service.build_cartographer_audit_trail",
            return_value={"events": []},
        ):
            payload = _run_cartographer_soak_snapshot_profile(output_dir=Path(tmp_dir))

        self.assertEqual(payload["result"], "pass")
        self.assertEqual(payload["reliability"]["grade"], "watch")
        self.assertEqual(payload["summary"]["changed_file_count"], 1)
        self.assertEqual(payload["recommendation"], "continue soak")
        self.assertIn("recommendation: continue soak", payload["expected_outcomes"])
        next_actions = "\n".join(payload["next_actions"])
        self.assertIn("bp-project-scout-component-code-changed-24f17bf2", next_actions)
        self.assertIn("drift-scout-component-code-changed", next_actions)
        self.assertIn("commit-prop-46a7e40f39aa", next_actions)
        self.assertIn("/v1/cartographer/proposals", next_actions)
        self.assertIn("/v1/cartographer/drift", next_actions)
        self.assertIn("/v1/cartographer/commit-proposals", next_actions)

    def test_cartographer_autonomy_escalation_check_blocks_enabled_commit_or_push(self) -> None:
        from source_proxy.testing.runner import _cartographer_autonomy_escalation_check

        payload = _cartographer_autonomy_escalation_check(
            {
                "write_actions_enabled": False,
                "commit_enabled": True,
                "push_enabled": True,
                "safety": {
                    "approval_required_for_file_writes": True,
                    "approval_required_for_commits": True,
                    "approval_required_for_pushes": True,
                    "scout_bypass_allowed": False,
                    "source_proxy_approval_bypass_allowed": False,
                    "docs_autopilot_enabled": False,
                    "autopilot_action_available": False,
                },
            }
        )

        self.assertFalse(payload["passed"])
        self.assertIn("autonomous_commit_disabled", payload["failures"])
        self.assertIn("autonomous_push_disabled", payload["failures"])

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
            "source_proxy.testing.runner._run_command",
            return_value={
                "command": "python -m pytest source_proxy/tests/test_codex_cli_adapter.py",
                "returncode": 0,
                "stdout": "22 passed\n",
                "stderr": "",
                "error": None,
            },
        ), mock.patch(
            "source_proxy.testing.runner._run_dashboard_smoke_tests",
            return_value={
                "command": "npx vitest run src/components/coding/__tests__/coding-workflow-step.test.ts",
                "returncode": 0,
                "stdout": "passed\n",
                "stderr": "",
                "error": None,
            },
        ), mock.patch(
            "source_proxy.testing.runner._proxy_closeout_route_validation",
            return_value={"ok": True, "base_url": "http://localhost:3000", "checks": {}, "project_health": {}},
        ), mock.patch(
            "source_proxy.testing.runner._proxy_closeout_cartographer_health",
            return_value={
                "ok": True,
                "project_id": "spiritos",
                "status": "active",
                "dirty": False,
                "dirty_file_count": 0,
                "expected_evidence_files": [],
                "unsafe_dirty_files": [],
                "merge_ready": True,
                "merge_blockers": [],
                "recommended_next_step": "open merge review",
                "write_actions_enabled": False,
            },
        ), mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", "clean"],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
        ):
            payload = run_runner_profile(profile=PROFILE_PROXY_CLOSEOUT)

        self.assertEqual(payload["result"], "pass")
        self.assertEqual(payload["closeout_status"], "PASS")
        self.assertFalse(payload["file_change_verdict"]["changed_by_test_run"])
        self.assertEqual(payload["next_safe_action"], "continue to the next increment")
        report = format_runner_report(payload)
        self.assertIn("PROXY TEST RUNNER CLOSEOUT", report)
        self.assertIn("Closeout status: PASS", report)
        self.assertIn("manual-check-7: PASS", report)
        self.assertIn("- failures: none", report)
        self.assertIn("Codex adapter tests:", report)
        self.assertIn("Dashboard smoke tests:", report)
        self.assertIn("Cartographer project health:", report)
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
            "source_proxy.testing.runner._run_command",
            return_value={"command": "pytest codex", "returncode": 0, "stdout": "", "stderr": "", "error": None},
        ), mock.patch(
            "source_proxy.testing.runner._run_dashboard_smoke_tests",
            return_value={"command": "vitest", "returncode": 0, "stdout": "", "stderr": "", "error": None},
        ), mock.patch(
            "source_proxy.testing.runner._proxy_closeout_route_validation",
            return_value={"ok": True, "base_url": "http://localhost:3000", "checks": {}, "project_health": {}},
        ), mock.patch(
            "source_proxy.testing.runner._proxy_closeout_cartographer_health",
            return_value={"ok": True, "write_actions_enabled": False},
        ), mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", " M README.md"],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
        ):
            payload = run_runner_profile(profile=PROFILE_PROXY_CLOSEOUT)

        self.assertEqual(payload["result"], "fail")
        self.assertTrue(payload["file_change_verdict"]["changed_by_test_run"])
        self.assertIn("closeout_changed_files_or_head", payload["blockers"])

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
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
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
        self.assertFalse(payload["file_change_verdict"]["evidence_review_needed"])
        self.assertEqual(payload["file_change_verdict"]["unexpected_status_delta"], [])
        self.assertEqual(payload["optional_checks"]["scout_search_smoke"]["status"], "not_run")
        run_command.assert_called_once()
        report = format_runner_report(payload)
        self.assertIn("PHASE 4F CLOSEOUT", report)
        self.assertIn("proxy closeout: PASS", report)
        self.assertIn("runner self tests: PASS", report)
        self.assertIn("scout search smoke: not run by default", report)
        self.assertIn("approve/apply/commit/push: not run", report)
        self.assertIn("unexpected status delta: none", report)
        self.assertIn("REMOTE CHECK RECEIPT", report)
        self.assertIn("CHECK: phase-4f-closeout", report)
        self.assertIn("RESULT: PASS", report)
        self.assertIn("HEAD_BEFORE: abc123", report)
        self.assertIn("HEAD_AFTER: abc123", report)
        self.assertIn("BLOCKERS: none", report)

    def test_phase_4f_closeout_labels_expected_snapshot_writes_as_evidence_review(self) -> None:
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
        snapshot_status = "?? scout/soak-logs/scout-soak-snapshot-2026-05-18T110315Z.json"

        with mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", snapshot_status],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
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
            return_value=soak_payload,
        ):
            payload = run_runner_profile(profile=PROFILE_PHASE_4F_CLOSEOUT)

        self.assertEqual(payload["result"], "pass")
        self.assertFalse(payload["file_change_verdict"]["changed_by_test_run"])
        self.assertTrue(payload["file_change_verdict"]["evidence_review_needed"])
        self.assertEqual(payload["file_change_verdict"]["expected_status_delta"], [snapshot_status])
        self.assertEqual(payload["file_change_verdict"]["unexpected_status_delta"], [])
        self.assertIn("review expected evidence snapshot", payload["recommendation"])
        report = format_runner_report(payload)
        self.assertIn("expected status delta: ?? scout/soak-logs/scout-soak-snapshot", report)
        self.assertIn("unexpected status delta: none", report)
        self.assertIn("evidence review needed: true", report)
        self.assertIn(f"EXPECTED_DIRTY: {snapshot_status}", report)

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
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
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

    def test_global_safety_regression_combines_required_phase_10_1_checks(self) -> None:
        proxy_smoke = {"profile": PROFILE_PROXY_SMOKE, "result": "pass"}
        cartographer = {"profile": PROFILE_CARTOGRAPHER_SAFETY, "result": "pass"}
        command_result = {
            "command": "python -m pytest test_file.py",
            "returncode": 0,
            "stdout": "passed\n",
            "stderr": "",
            "error": None,
        }

        with mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", "clean"],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
        ), mock.patch(
            "source_proxy.testing.runner._run_proxy_smoke_profile",
            return_value=proxy_smoke,
        ), mock.patch(
            "source_proxy.testing.runner._run_cartographer_safety_profile",
            return_value=cartographer,
        ), mock.patch(
            "source_proxy.testing.runner._run_command",
            side_effect=[command_result, command_result, command_result],
        ):
            payload = run_runner_profile(profile=PROFILE_GLOBAL_SAFETY_REGRESSION)

        self.assertEqual(payload["result"], "pass")
        self.assertTrue(payload["checks"]["proxy_safety_harness"])
        self.assertTrue(payload["checks"]["source_proxy_tests"])
        self.assertTrue(payload["checks"]["scout_backend_tests"])
        self.assertTrue(payload["checks"]["cartographer_safety"])
        self.assertTrue(payload["checks"]["dashboard_smoke_tests"])
        self.assertTrue(payload["safety_boundary"]["no_approve"])
        self.assertFalse(payload["file_change_verdict"]["changed_by_test_run"])

        report = format_runner_report(payload)

        self.assertIn("GLOBAL SAFETY REGRESSION PACK", report)
        self.assertIn("source proxy tests: PASS", report)
        self.assertIn("Scout backend tests: PASS", report)
        self.assertIn("dashboard smoke tests: PASS", report)

    def test_global_safety_regression_gives_scout_backend_enough_time(self) -> None:
        proxy_smoke = {"profile": PROFILE_PROXY_SMOKE, "result": "pass"}
        cartographer = {"profile": PROFILE_CARTOGRAPHER_SAFETY, "result": "pass"}
        command_result = {
            "command": "python -m pytest test_file.py",
            "returncode": 0,
            "stdout": "passed\n",
            "stderr": "",
            "error": None,
        }

        with mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", "clean"],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
        ), mock.patch(
            "source_proxy.testing.runner._run_proxy_smoke_profile",
            return_value=proxy_smoke,
        ), mock.patch(
            "source_proxy.testing.runner._run_cartographer_safety_profile",
            return_value=cartographer,
        ), mock.patch(
            "source_proxy.testing.runner._run_command",
            side_effect=[command_result, command_result, command_result],
        ) as run_command:
            payload = run_runner_profile(profile=PROFILE_GLOBAL_SAFETY_REGRESSION)

        self.assertEqual(payload["result"], "pass")
        self.assertEqual(
            run_command.call_args_list[1].kwargs["timeout_seconds"],
            GLOBAL_SAFETY_SCOUT_BACKEND_TIMEOUT_SECONDS,
        )

    def test_global_safety_regression_fails_on_unexpected_mutation(self) -> None:
        proxy_smoke = {"profile": PROFILE_PROXY_SMOKE, "result": "pass"}
        cartographer = {"profile": PROFILE_CARTOGRAPHER_SAFETY, "result": "pass"}
        command_result = {
            "command": "python -m pytest test_file.py",
            "returncode": 0,
            "stdout": "passed\n",
            "stderr": "",
            "error": None,
        }

        with mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", " M src/app/page.tsx"],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
        ), mock.patch(
            "source_proxy.testing.runner._run_proxy_smoke_profile",
            return_value=proxy_smoke,
        ), mock.patch(
            "source_proxy.testing.runner._run_cartographer_safety_profile",
            return_value=cartographer,
        ), mock.patch(
            "source_proxy.testing.runner._run_command",
            side_effect=[command_result, command_result, command_result],
        ):
            payload = run_runner_profile(profile=PROFILE_GLOBAL_SAFETY_REGRESSION)

        self.assertEqual(payload["result"], "fail")
        self.assertTrue(payload["file_change_verdict"]["changed_by_test_run"])
        self.assertEqual(payload["recommendation"], "fix needed")

    def test_global_safety_regression_explains_unexpected_level_2_evidence(self) -> None:
        proxy_smoke = {"profile": PROFILE_PROXY_SMOKE, "result": "pass"}
        cartographer = {"profile": PROFILE_CARTOGRAPHER_SAFETY, "result": "pass"}
        command_result = {
            "command": "python -m pytest test_file.py",
            "returncode": 0,
            "stdout": "passed\n",
            "stderr": "",
            "error": None,
        }
        level_2_status = "?? scout/soak-logs/scout-level-2-evidence-2026-05-20T015829Z.json"

        with mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", level_2_status],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
        ), mock.patch(
            "source_proxy.testing.runner._run_proxy_smoke_profile",
            return_value=proxy_smoke,
        ), mock.patch(
            "source_proxy.testing.runner._run_cartographer_safety_profile",
            return_value=cartographer,
        ), mock.patch(
            "source_proxy.testing.runner._run_command",
            side_effect=[command_result, command_result, command_result],
        ):
            payload = run_runner_profile(profile=PROFILE_GLOBAL_SAFETY_REGRESSION)

        self.assertEqual(payload["result"], "fail")
        self.assertEqual(payload["file_change_verdict"]["unexpected_status_delta"], [level_2_status])
        self.assertEqual(
            payload["file_change_verdict"]["unexpected_level_2_evidence_files"],
            [level_2_status],
        )
        self.assertIn("global-safety-regression allows scout-soak-snapshot-*", payload["file_change_verdict"]["mutation_policy"])
        self.assertTrue(payload["file_change_verdict"]["mutation_notes"])
        report = format_runner_report(payload)
        self.assertIn("unexpected Level 2 evidence", report)
        self.assertIn("concurrent/manual Level 2 evidence run", report)

    def test_dependency_environment_checks_report_required_baseline(self) -> None:
        dependency_payload = {"result": "pass", "blockers": [], "warnings": []}
        service_payload = {
            **dependency_payload,
            "scout_api": {"ok": True, "status": 200, "body": {}, "error": None},
            "searxng": {"ok": True, "status": 200, "body": {}, "error": None},
            "dashboard": {"ok": True, "status": 200, "body": "", "error": None},
        }
        environment_payload = {
            **dependency_payload,
            "spirit_project_paths": ["/repo"],
            "missing_spirit_project_paths": [],
            "source_proxy_origin": None,
            "scout_api_url": "http://localhost:8077",
        }
        python_payload = {
            "result": "pass",
            "blockers": [],
            "imports": {"returncode": 0, "stdout": "ok", "stderr": "", "error": None},
            "pip_check": {"returncode": 0, "stdout": "ok", "stderr": "", "error": None},
        }
        node_payload = {
            "result": "pass",
            "blockers": [],
            "missing_paths": [],
            "checks": {
                "node": {"returncode": 0, "stdout": "v20", "stderr": "", "error": None},
                "typescript": {"returncode": 0, "stdout": "Version 5", "stderr": "", "error": None},
                "vitest": {"returncode": 0, "stdout": "vitest/4", "stderr": "", "error": None},
                "eslint": {"returncode": 0, "stdout": "v9", "stderr": "", "error": None},
            },
        }

        with mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", "clean"],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
        ), mock.patch(
            "source_proxy.testing.runner._python_dependency_check",
            return_value=python_payload,
        ), mock.patch(
            "source_proxy.testing.runner._node_dependency_check",
            return_value=node_payload,
        ), mock.patch(
            "source_proxy.testing.runner._service_availability_check",
            return_value=service_payload,
        ), mock.patch(
            "source_proxy.testing.runner._environment_variable_check",
            return_value=environment_payload,
        ), mock.patch(
            "source_proxy.testing.runner._database_freshness_check",
            return_value={**dependency_payload, "databases": []},
        ):
            payload = run_runner_profile(profile=PROFILE_DEPENDENCY_ENVIRONMENT_CHECKS)

        self.assertEqual(payload["result"], "pass")
        self.assertTrue(payload["checks"]["python_dependencies"])
        self.assertTrue(payload["checks"]["node_dependencies"])
        self.assertTrue(payload["checks"]["required_services"])
        self.assertTrue(payload["checks"]["environment_variables"])
        self.assertTrue(payload["checks"]["databases"])

        report = format_runner_report(payload)

        self.assertIn("DEPENDENCY AND ENVIRONMENT CHECKS", report)
        self.assertIn("Python dependencies:", report)
        self.assertIn("Node dependencies:", report)
        self.assertIn("Databases:", report)

    def test_dependency_environment_checks_fail_on_missing_node_dependency(self) -> None:
        dependency_payload = {"result": "pass", "blockers": [], "warnings": []}
        service_payload = {
            **dependency_payload,
            "scout_api": {"ok": True, "status": 200, "body": {}, "error": None},
            "searxng": {"ok": True, "status": 200, "body": {}, "error": None},
            "dashboard": {"ok": True, "status": 200, "body": "", "error": None},
        }
        environment_payload = {
            **dependency_payload,
            "spirit_project_paths": ["/repo"],
            "missing_spirit_project_paths": [],
            "source_proxy_origin": None,
            "scout_api_url": "http://localhost:8077",
        }
        node_payload = {
            "result": "fail",
            "blockers": ["missing node_modules/vitest/vitest.mjs"],
            "missing_paths": ["node_modules/vitest/vitest.mjs"],
            "checks": {
                "node": {"returncode": 0, "stdout": "v20", "stderr": "", "error": None},
                "typescript": {"returncode": None, "stdout": "", "stderr": "", "error": "skipped"},
                "vitest": {"returncode": None, "stdout": "", "stderr": "", "error": "skipped"},
                "eslint": {"returncode": None, "stdout": "", "stderr": "", "error": "skipped"},
            },
        }

        with mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", "clean"],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
        ), mock.patch(
            "source_proxy.testing.runner._python_dependency_check",
            return_value={**dependency_payload, "imports": {}, "pip_check": {}},
        ), mock.patch(
            "source_proxy.testing.runner._node_dependency_check",
            return_value=node_payload,
        ), mock.patch(
            "source_proxy.testing.runner._service_availability_check",
            return_value=service_payload,
        ), mock.patch(
            "source_proxy.testing.runner._environment_variable_check",
            return_value=environment_payload,
        ), mock.patch(
            "source_proxy.testing.runner._database_freshness_check",
            return_value={**dependency_payload, "databases": []},
        ):
            payload = run_runner_profile(profile=PROFILE_DEPENDENCY_ENVIRONMENT_CHECKS)

        self.assertEqual(payload["result"], "fail")
        self.assertFalse(payload["checks"]["node_dependencies"])
        self.assertEqual(payload["recommendation"], "fix dependency or environment blockers")

    def test_mobile_lan_tailscale_qa_reports_dashboard_and_approval_safety(self) -> None:
        dashboard = {
            "command": "node node_modules/vitest/vitest.mjs run mobile.test.ts",
            "result": "pass",
            "returncode": 0,
            "missing_files": [],
            "stdout": "9 passed",
            "stderr": "",
            "error": None,
        }
        approval = {
            "result": "pass",
            "blockers": [],
            "warnings": [],
            "checks": {"apply_requires_approved_status": True},
        }
        network = {
            "result": "pass",
            "blockers": [],
            "warnings": ["dashboard localhost unavailable; start Next before browser QA"],
            "dashboard_localhost": {"ok": False, "status": None, "body": "", "error": "closed"},
            "tailscale_ip": {"returncode": None, "stdout": "", "stderr": "", "error": "missing"},
            "manual_targets": ["desktop browser at http://localhost:3000"],
        }

        with mock.patch(
            "source_proxy.testing.runner._git_status_short",
            side_effect=["clean", "clean"],
        ), mock.patch(
            "source_proxy.testing.runner._git_head",
            side_effect=["abc123", "abc123"],
        ), mock.patch(
            "source_proxy.testing.runner._run_dashboard_mobile_qa_tests",
            return_value=dashboard,
        ), mock.patch(
            "source_proxy.testing.runner._dashboard_approval_safety_check",
            return_value=approval,
        ), mock.patch(
            "source_proxy.testing.runner._lan_tailscale_reachability_check",
            return_value=network,
        ):
            payload = run_runner_profile(profile=PROFILE_MOBILE_LAN_TAILSCALE_QA)

        self.assertEqual(payload["result"], "pass")
        self.assertTrue(payload["checks"]["dashboard_mobile_tests"])
        self.assertTrue(payload["checks"]["approval_cannot_be_accidental"])
        self.assertTrue(payload["checks"]["lan_tailscale_diagnostics"])

        report = format_runner_report(payload)

        self.assertIn("MOBILE LAN TAILSCALE QA", report)
        self.assertIn("dashboard localhost unavailable", report)
        self.assertIn("approval_cannot_be_accidental: PASS", report)

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

    def test_scout_search_diagnostics_treats_missing_docker_as_warning_when_host_search_works(self) -> None:
        compose = {
            "ok": True,
            "path": "scout/docker-compose.scout.yml",
            "error": None,
            "env_file_mentions": [".env"],
            "search_env_wired": True,
            "searxng_url_wired": True,
        }
        docker_error = (
            "failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; "
            "check if the path is correct and if the daemon is running"
        )
        unavailable = {
            "command": "docker exec scout_v0_1 env",
            "returncode": 1,
            "stdout": "",
            "stderr": docker_error,
            "error": None,
            "keys": [],
            "search_enabled_present": False,
            "searxng_url_present": False,
        }
        host = {
            "ok": True,
            "status": 200,
            "url": "http://localhost:8080/search?q=fastapi&format=json",
            "body": {"results": [{"url": "https://fastapi.tiangolo.com"}]},
            "error": None,
        }
        probe = {
            "ok": False,
            "status": None,
            "url": "http://searxng:8080/search?q=fastapi&format=json",
            "body": {},
            "returncode": 1,
            "stdout": "",
            "stderr": docker_error,
            "error": docker_error,
        }

        with mock.patch(
            "source_proxy.testing.runner._inspect_scout_compose",
            return_value=compose,
        ), mock.patch(
            "source_proxy.testing.runner._inspect_scout_container_env",
            return_value=unavailable,
        ), mock.patch(
            "source_proxy.testing.runner._inspect_scout_container_settings",
            return_value=unavailable,
        ), mock.patch(
            "source_proxy.testing.runner._http_get_json",
            return_value=host,
        ), mock.patch(
            "source_proxy.testing.runner._probe_container_url",
            return_value=probe,
        ):
            payload = run_runner_profile(profile=PROFILE_SCOUT_SEARCH_DIAGNOSTICS)

        self.assertEqual(payload["result"], "pass")
        self.assertEqual(payload["findings"], [])
        self.assertIn(
            "docker unavailable; skipped Scout container SearXNG probes",
            payload["warnings"],
        )
        self.assertIn("Warnings:", format_runner_report(payload))

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

    def test_scout_search_smoke_reports_budget_blocked_create_job(self) -> None:
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

        self.assertEqual(payload["result"], "blocked_by_budget")
        self.assertEqual(payload["summary"]["blocked_reason"], "daily_limit_reached")
        self.assertIn("create discovery job: FAIL (422): daily discovery job limit reached", report)
        self.assertIn("Result: BLOCKED_BY_BUDGET", report)
        self.assertIn("blocked reason: daily_limit_reached", report)
        self.assertIn("wait for the next UTC budget reset", report)

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

    def test_scout_soak_snapshot_treats_missing_docker_logs_as_non_fatal_warning(self) -> None:
        import tempfile
        from source_proxy.testing.runner import _run_scout_soak_snapshot_profile

        ok = {"ok": True, "status": 200, "url": "", "body": {}, "error": None}
        logs = {
            "command": "docker logs --tail 80 scout_v0_1",
            "returncode": 1,
            "stdout": "",
            "stderr": (
                "failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; "
                "check if the path is correct and if the daemon is running"
            ),
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
        self.assertEqual(payload["recommendation"], "ready with warnings")
        self.assertEqual(payload["summary"]["warnings"], ["docker logs command failed"])

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

    def test_scout_soak_snapshot_reports_list_error_counters(self) -> None:
        import tempfile
        from source_proxy.testing.runner import _run_scout_soak_snapshot_profile

        ok = {"ok": True, "status": 200, "url": "", "body": {}, "error": None}
        logs = {
            "command": "docker logs --tail 80 scout_v0_1",
            "returncode": 0,
            "stdout": (
                '{"checked": 1, "processed": 0, "errors": ["provider timeout"], '
                '"event": "debugger_run_complete"}\n'
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

        self.assertEqual(payload["result"], "fail")
        self.assertIn("recent docker logs contain error", payload["summary"]["warnings"])

    def test_scout_soak_snapshot_ignores_errors_before_latest_startup(self) -> None:
        import tempfile
        from source_proxy.testing.runner import _run_scout_soak_snapshot_profile

        ok = {"ok": True, "status": 200, "url": "", "body": {}, "error": None}
        logs = {
            "command": "docker logs --tail 80 scout_v0_1",
            "returncode": 0,
            "stdout": (
                "ERROR old missing config from previous container boot\n"
                '{"db_path": "/app/data/scout.db", "event": "scout_starting"}\n'
                '{"checked": 0, "processed": 0, "errors": [], '
                '"event": "packet_synthesis_run_complete"}\n'
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
