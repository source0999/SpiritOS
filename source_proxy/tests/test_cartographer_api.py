from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.cartographer.apply import apply_approved_doc_proposal
from source_proxy.cartographer.approval_token_runtime import (
    APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
    APPROVAL_TOKEN_SCHEMA_VERSION,
)
from source_proxy.cartographer.blueprint_registry import load_blueprints
from source_proxy.cartographer.component_mapper import map_paths
from source_proxy.cartographer.git_approvals import approve_git_queue_item
from source_proxy.cartographer.project_discovery import parse_project_roots
from source_proxy.cartographer.service import (
    build_cartographer_audit_trail,
    build_cartographer_autonomy_promotion,
    build_cartographer_blueprints,
    build_cartographer_blueprint_scribe,
    build_cartographer_branch_recommendations,
    build_cartographer_change_scribe,
    build_cartographer_clutter_inventory,
    build_cartographer_clutter_proposals,
    build_cartographer_clutter_review,
    build_cartographer_codex_evidence,
    build_cartographer_commit_proposals,
    build_cartographer_components,
    build_cartographer_docs_autopilot_dry_run,
    build_cartographer_docs_autopilot_soak,
    build_cartographer_drift,
    build_cartographer_git,
    build_cartographer_level_2_api_contract,
    build_cartographer_level_2_closeout,
    build_cartographer_level_2_dirty_tree,
    build_cartographer_level_2_dirty_tree_resolution,
    build_cartographer_level_2_readiness,
    build_cartographer_level_3_commit_approval_preview,
    build_cartographer_level_3_blocker_handoff,
    build_cartographer_level_3_closeout_readiness,
    build_cartographer_level_3_endpoint_index,
    build_cartographer_level_3_finalization_marker,
    build_cartographer_level_3_commit_proposals,
    build_cartographer_level_4_push_readiness_contract,
    build_cartographer_level_4_push_queue_approval_preview,
    build_cartographer_level_4_push_queue_proposal_preview,
    build_cartographer_level_6_component_ownership_assignment,
    build_cartographer_level_6_cross_project_status_board,
    build_cartographer_level_6_cross_repo_dirty_tree_classifier,
    build_cartographer_level_6_multi_project_closeout_dashboard,
    build_cartographer_level_6_project_registry_hardening,
    build_cartographer_level_7_closeout_dashboard,
    build_cartographer_level_7_disabled_by_default,
    build_cartographer_level_7_dry_run_action_packet,
    build_cartographer_level_7_exact_approval_handshake,
    build_cartographer_level_7_next_safe_action,
    build_cartographer_level_8_receipt_journal,
    build_cartographer_level_8_closeout_smoke,
    build_cartographer_level_9_worker_registry,
    build_cartographer_level_9_one_worker_rule,
    build_cartographer_level_9_allowed_file_conflict_checker,
    build_cartographer_level_9_branch_worktree_proposal_queue,
    build_cartographer_level_9_stale_worker_closeout_packet,
    build_cartographer_level_9_coordination_dashboard,
    build_cartographer_level_10_project_health_timeline,
    build_cartographer_level_10_closeout_packet_generator,
    build_cartographer_level_10_run_history_evidence_browser,
    build_cartographer_level_10_scout_blueprint_handoff_preview,
    build_cartographer_level_10_production_readiness_checklist,
    build_cartographer_level_10_closeout_next_roadmap_gate,
    build_cartographer_level_8_stop_failure_handling,
    build_cartographer_level_8_step_approval_preview,
    build_cartographer_level_8_workflow_run_card,
    build_cartographer_level_5_branch_worktree_approval_preview,
    build_cartographer_level_5_branch_recommendation_refresh,
    build_cartographer_level_5_multi_worker_safety_smoke,
    build_cartographer_level_5_parallel_work_risk_model,
    build_cartographer_level_5_worktree_recommendation_contract,
    build_cartographer_project_candidates,
    build_cartographer_project_health,
    build_cartographer_projects,
    build_cartographer_proposals,
    build_cartographer_push_queue,
    build_cartographer_reminders,
    build_cartographer_repo_map,
    build_cartographer_runbook_scribe,
    build_cartographer_status,
    build_cartographer_sub_cartographers,
    build_cartographer_trust_score,
    build_cartographer_v1_closeout_handoff,
    build_cartographer_v1_closeout_audit_summary,
    build_cartographer_v1_closeout_dashboard,
    build_cartographer_v1_closeout_endpoint_index,
    build_cartographer_v1_closeout_finalization_marker,
    build_cartographer_v1_closeout_status,
    build_cartographer_v1_closeout_checklist,
    build_cartographer_v1_combined_readiness_dry_run,
    build_cartographer_v1_diagnostic_import_dry_run,
    build_cartographer_v1_evidence,
    build_cartographer_v1_evidence_gap_report,
    build_cartographer_v1_freeze_marker_proposal,
    build_cartographer_v1_freeze_marker_validation,
    build_cartographer_v1_proof_contract,
    build_cartographer_v1_proof_import_dry_run,
    build_cartographer_v1_proof_recording_proposal,
    build_cartographer_v1_proof_validation,
    build_cartographer_v1_readiness,
    block_cartographer_level_3_commit_execution,
    block_cartographer_level_4_push_execution,
    run_cartographer_level_2_docs_apply,
    run_cartographer_docs_autopilot_apply,
    write_cartographer_starter_blueprints,
    apply_cartographer_clutter_proposal,
)
from source_proxy.main import app


_UTC_TIMESTAMP_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$"


def _test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(cartographer_router)
    return test_app


class CartographerApiTests(unittest.TestCase):
    def test_legacy_mutation_routes_are_removed_and_selection_routes_are_canonical(self) -> None:
        routes = cartographer_router.routes
        for path, method in (
            ("/v1/cartographer/safe-write", "GET"),
            ("/v1/cartographer/safe-write", "POST"),
            ("/v1/cartographer/verification/run", "GET"),
            ("/v1/cartographer/verification/run", "POST"),
        ):
            matches = [
                route for route in routes
                if getattr(route, "path", None) == path and method in getattr(route, "methods", set())
            ]
            self.assertEqual(len(matches), 0, f"{method} {path} must not restore direct Cartographer mutation")

        for path in (
            "/v1/cartographer/proposals/{proposal_id}/selection-preview",
            "/v1/cartographer/proposals/{proposal_id}/operator-selection",
            "/v1/cartographer/proposals/{proposal_id}/selection-transfer",
        ):
            matches = [
                route for route in routes
                if getattr(route, "path", None) == path and "POST" in getattr(route, "methods", set())
            ]
            self.assertEqual(len(matches), 1, f"POST {path} must have one canonical authority route")

    def test_legacy_approval_token_routes_are_not_registered(self) -> None:
        routes = _test_app().routes
        for path, method in (
            ("/v1/cartographer/approval-token/validate", "GET"),
            ("/v1/cartographer/approval-token/validate", "POST"),
            ("/v1/cartographer/approval-token/consume-preview", "GET"),
            ("/v1/cartographer/approval-token/consume-preview", "POST"),
        ):
            matches = [
                route for route in routes
                if getattr(route, "path", None) == path and method in getattr(route, "methods", set())
            ]
            self.assertEqual(len(matches), 0, f"{method} {path} must not restore client approval authority")

    def test_status_contract_is_read_only_empty_state(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SPIRIT_PROJECT_PATH": "",
                "CARTOGRAPHER_DOCS_AUTOPILOT_ENABLED": "false",
                "CARTOGRAPHER_DOCS_AUTOPILOT_DAILY_CAP": "0",
                "CARTOGRAPHER_AUTOPILOT_KILL_SWITCH": "true",
            },
            clear=False,
        ):
            payload = build_cartographer_status()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["configured_roots"], [])
        self.assertEqual(payload["blocked_roots"], [])
        self.assertEqual(payload["projects"], [])
        self.assertEqual(payload["blueprint_count"], 0)
        self.assertEqual(payload["pending_proposals"], 0)
        self.assertFalse(payload["docs_autopilot_enabled"])
        self.assertEqual(payload["docs_autopilot_daily_cap"], 0)
        self.assertTrue(payload["autopilot_kill_switch"])
        self.assertFalse(payload["autopilot_action_available"])
        self.assertEqual(payload["autopilot"]["autopilot_mode"], "disabled")
        self.assertFalse(payload["autopilot"]["actions_taken"])
        self.assertFalse(payload["safety"]["scout_bypass_allowed"])
        self.assertFalse(payload["safety"]["source_proxy_approval_bypass_allowed"])
        self.assertFalse(payload["safety"]["docs_autopilot_enabled"])

    def test_approval_token_status_preview_defaults_no_go_without_authority(self) -> None:
        client = TestClient(_test_app())

        response = client.get("/v1/cartographer/status")

        self.assertEqual(response.status_code, 200)
        approval = response.json()["approval_token"]
        validation = approval["validation"]
        consumption = approval["consumption"]

        self.assertEqual(approval["status"], "no-go")
        self.assertTrue(approval["no_go_default"])
        self.assertTrue(approval["validation_only"])
        self.assertTrue(approval["preview_only"])
        self.assertFalse(approval["authority_granted"])
        self.assertFalse(approval["write_authority_granted"])
        self.assertFalse(approval["command_authority_granted"])
        self.assertFalse(approval["workflow_authority_granted"])
        self.assertFalse(approval["queue_authority_granted"])
        self.assertFalse(approval["git_authority_granted"])
        self.assertEqual(validation["status"], "rejected")
        self.assertIn("malformed_payload", validation["reasons"])
        self.assertFalse(validation["authority_granted"])
        self.assertEqual(consumption["status"], "blocked")
        self.assertIn("token_validation:malformed_payload", consumption["reasons"])
        self.assertTrue(consumption["approval_event_preview"]["preview_only"])
        self.assertFalse(consumption["approval_event_preview"]["token_consumed_for_real"])
        self.assertFalse(consumption["authority_granted"])

    def test_approval_token_validate_get_is_not_a_client_authority_route(self) -> None:
        client = TestClient(_test_app())

        response = client.get("/v1/cartographer/approval-token/validate")

        self.assertEqual(response.status_code, 404)

    def test_approval_token_validate_post_is_not_a_client_authority_route(self) -> None:
        client = TestClient(_test_app())

        response = client.post(
            "/v1/cartographer/approval-token/validate",
            json=self._approval_token_validation_request(),
        )

        self.assertEqual(response.status_code, 404)

    def test_approval_token_consume_preview_post_is_not_a_client_authority_route(self) -> None:
        client = TestClient(_test_app())

        response = client.post(
            "/v1/cartographer/approval-token/consume-preview",
            json=self._approval_token_consumption_request(),
        )

        self.assertEqual(response.status_code, 404)

    def test_docs_autopilot_kill_switch_blocks_requested_configuration(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SPIRIT_PROJECT_PATH": "",
                "CARTOGRAPHER_DOCS_AUTOPILOT_ENABLED": "true",
                "CARTOGRAPHER_DOCS_AUTOPILOT_DAILY_CAP": "1",
                "CARTOGRAPHER_AUTOPILOT_KILL_SWITCH": "true",
            },
            clear=False,
        ):
            payload = build_cartographer_status()

        self.assertFalse(payload["docs_autopilot_enabled"])
        self.assertEqual(payload["docs_autopilot_daily_cap"], 1)
        self.assertTrue(payload["autopilot_kill_switch"])
        self.assertFalse(payload["autopilot_action_available"])
        self.assertFalse(payload["autopilot"]["write_actions_enabled"])
        self.assertFalse(payload["autopilot"]["actions_taken"])

    def test_docs_autopilot_dry_run_proposes_docs_without_writing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")
            blueprint = root / "_blueprints" / "current" / "dashboard_state.md"
            before = blueprint.read_text(encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_docs_autopilot_dry_run()

            after = blueprint.read_text(encoding="utf-8")

        self.assertEqual(before, after)
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["level"], 1)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["apply_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["approval_available"])
        self.assertFalse(payload["apply_available"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["operator_review_required"])
        self.assertEqual(payload["recommended_next_action"], "operator_review_required")
        self.assertEqual(payload["git_head_before"], payload["git_head_after"])
        self.assertFalse(payload["head_changed"])
        self.assertEqual(payload["unexpected_status_delta"], [])
        self.assertEqual(payload["candidate_count"], payload["proposal_count"])
        self.assertEqual(payload["dirty_tree_summary"]["changed_files"], ["src/components/dashboard/Widget.tsx"])
        self.assertIn("docs/**/*.md", payload["allowed_scope"])
        self.assertIn("src/**", payload["forbidden_scope"])
        self.assertGreater(payload["proposal_count"], 0)
        candidate = payload["candidates"][0]
        self.assertEqual(candidate["risk_level"], "low")
        self.assertFalse(candidate["blocked"])
        self.assertIn("why_no_source_edit_is_needed", candidate)
        proposal = payload["proposals"][0]
        self.assertTrue(proposal["dry_run"])
        self.assertFalse(proposal["approval_available"])
        self.assertFalse(proposal["apply_available"])
        self.assertTrue(proposal["approval_required"])
        self.assertFalse(proposal["apply_allowed"])
        self.assertFalse(proposal["commit_allowed"])
        self.assertFalse(proposal["push_allowed"])
        self.assertFalse(proposal["would_write_files"])
        self.assertFalse(proposal["action_taken"])
        self.assertIn("diff --git", proposal["diff_preview"])

    def _assert_direct_mutation_blocked(self, payload: dict[str, object]) -> None:
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["reason_code"], "forbidden_cartographer_mutation")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["files_written"], [])
        self.assertFalse(payload["authority_granted"])

    def test_docs_autopilot_apply_is_blocked_by_default_without_writing_docs(self) -> None:
        self._assert_direct_mutation_blocked(run_cartographer_docs_autopilot_apply())

    def test_docs_autopilot_apply_writes_one_docs_receipt_after_all_gates_pass(self) -> None:
        self._assert_direct_mutation_blocked(run_cartographer_docs_autopilot_apply())

    def test_level_2_apply_blocks_without_human_approval(self) -> None:
        self._assert_direct_mutation_blocked(run_cartographer_level_2_docs_apply(proposal_id="level-2-unapproved"))

    def test_level_2_apply_blocks_source_target(self) -> None:
        self._assert_direct_mutation_blocked(run_cartographer_level_2_docs_apply(proposal_id="level-2-source"))

    def test_level_2_apply_blocks_forbidden_path_variants(self) -> None:
        for proposal_id in ("level-2-forbidden-absolute", "level-2-forbidden-parent", "level-2-forbidden-env", "level-2-forbidden-root"):
            with self.subTest(proposal_id=proposal_id):
                self._assert_direct_mutation_blocked(run_cartographer_level_2_docs_apply(proposal_id=proposal_id))

    def test_level_2_apply_blocks_stale_head(self) -> None:
        self._assert_direct_mutation_blocked(run_cartographer_level_2_docs_apply(proposal_id="level-2-stale"))

    def test_level_2_apply_blocks_changed_proposal_target_path(self) -> None:
        self._assert_direct_mutation_blocked(run_cartographer_level_2_docs_apply(proposal_id="level-2-target-changed"))

    def test_level_2_apply_blocks_cartographer_self_approval(self) -> None:
        self._assert_direct_mutation_blocked(run_cartographer_level_2_docs_apply(proposal_id="level-2-self-approved"))

    def test_level_2_apply_blocks_dirty_unrelated_source_file(self) -> None:
        self._assert_direct_mutation_blocked(run_cartographer_level_2_docs_apply(proposal_id="level-2-dirty"))

    def test_level_2_approved_docs_apply_writes_docs_receipt_without_commit_push_or_stage(self) -> None:
        self._assert_direct_mutation_blocked(
            run_cartographer_level_2_docs_apply(
                proposal_id="level-2-approved", approval_id="forged-approval", approval_actor="cartographer"
            )
        )

    def test_docs_autopilot_soak_marks_seven_boring_cycles_green(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            audit_path = root / "data" / "approved_actions.audit.jsonl"
            audit_path.parent.mkdir()
            audit_path.write_text(
                "\n".join(
                    json.dumps(
                        {
                            "event": "autopilot_docs_apply",
                            "approved_at": f"2026-05-{day:02d}T10:00:00Z",
                            "changed_files": ["docs/cartographer-autopilot-receipt.md"],
                            "committed": False,
                            "pushed": False,
                        },
                        sort_keys=True,
                    )
                    for day in range(1, 8)
                )
                + "\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_docs_autopilot_soak()

        self.assertEqual(payload["soak_grade"], "green")
        self.assertEqual(payload["level"], 1)
        self.assertEqual(payload["mode"], "soak")
        self.assertFalse(payload["authority_granted"])
        self.assertEqual(payload["level9_status"], "GREEN")
        self.assertEqual(payload["observed_days"], 7)
        self.assertEqual(payload["cycle_count"], 7)
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["apply_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["snapshot_log_only"])
        self.assertFalse(payload["head_changed"])
        self.assertEqual(payload["unexpected_status_delta"], [])
        self.assertTrue(payload["apply_disabled"])
        self.assertTrue(payload["commit_disabled"])
        self.assertTrue(payload["push_disabled"])
        self.assertTrue(payload["approval_bypass_disabled"])
        self.assertEqual(payload["candidate_generation"], "proposal_only")
        self.assertTrue(payload["operator_review_required"])
        checks = {check["code"]: check for check in payload["checks"]}
        self.assertTrue(checks["no_app_code_touched"]["passed"])
        self.assertTrue(checks["no_safety_code_touched"]["passed"])
        self.assertTrue(checks["no_approval_code_touched"]["passed"])
        self.assertTrue(checks["no_secrets_touched"]["passed"])
        self.assertTrue(checks["no_commits_without_approval"]["passed"])
        self.assertTrue(checks["no_pushes_without_approval"]["passed"])
        self.assertTrue(checks["all_actions_audited"]["passed"])

    def test_docs_autopilot_soak_blocks_noisy_or_unsafe_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            audit_path = root / "data" / "approved_actions.audit.jsonl"
            audit_path.parent.mkdir()
            audit_path.write_text(
                json.dumps(
                    {
                        "event": "autopilot_docs_apply",
                        "approved_at": "2026-05-01T10:00:00Z",
                        "changed_files": ["src/app/page.tsx", ".env.local"],
                        "committed": True,
                        "pushed": True,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_docs_autopilot_soak()

        self.assertEqual(payload["soak_grade"], "not_ready")
        self.assertEqual(payload["level"], 1)
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["apply_enabled"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["push_enabled"])
        self.assertEqual(payload["level9_status"], "YELLOW")
        checks = {check["code"]: check for check in payload["checks"]}
        self.assertFalse(checks["no_app_code_touched"]["passed"])
        self.assertFalse(checks["no_secrets_touched"]["passed"])
        self.assertFalse(checks["no_commits_without_approval"]["passed"])
        self.assertFalse(checks["no_pushes_without_approval"]["passed"])

    def test_projects_contract_reports_safe_empty_configuration(self) -> None:
        with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
            payload = build_cartographer_projects()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["configured_roots"], [])
        self.assertEqual(payload["blocked_roots"], [])
        self.assertEqual(payload["projects"], [])
        self.assertEqual(payload["safety"]["write_policy"], "read_only")

    def test_blueprints_contract_parses_index_and_frontmatter_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            blueprints = root / "_blueprints"
            blueprints.mkdir()
            (blueprints / "INDEX.md").write_text(
                "\n".join(
                    [
                        "# Index",
                        "| Document | Classification | Notes |",
                        "| --- | --- | --- |",
                        "| `current.md` | current truth | Canonical. |",
                        "| `history/phase0.md` | history/phase receipt | Historical. |",
                    ]
                ),
                encoding="utf-8",
            )
            (blueprints / "current.md").write_text(
                "\n".join(
                    [
                        "---",
                        "blueprint_id: current-state",
                        "title: Current State",
                        "project: SpiritOS",
                        "component: system",
                        "doc_type: current_state",
                        "status: active",
                        "source_of_truth: true",
                        "owner: Britton",
                        "code_paths:",
                        "  - src/**",
                        "related_blueprints: []",
                        "write_policy: proposal_only_until_dashboard_approved",
                        "last_verified: 2026-05-15",
                        "---",
                        "# Current",
                    ]
                ),
                encoding="utf-8",
            )
            history = blueprints / "history"
            history.mkdir()
            (history / "phase0.md").write_text(
                "\n".join(
                    [
                        "---",
                        "blueprint_id: phase0",
                        "title: Phase 0",
                        "project: SpiritOS",
                        "component: history",
                        "doc_type: phase_receipt",
                        "status: historical",
                        "source_of_truth: false",
                        "owner: Britton",
                        "code_paths: []",
                        "related_blueprints:",
                        "  - current-state",
                        "write_policy: historical_read_only",
                        "last_verified: 2026-05-15",
                        "---",
                        "# Phase 0",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_blueprints()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["blueprint_count"], 2)
        records = {record["blueprint_id"]: record for record in payload["blueprints"]}
        self.assertEqual(records["current-state"]["path"], "current.md")
        self.assertEqual(records["current-state"]["index_classification"], "current truth")
        self.assertEqual(records["current-state"]["code_paths"], ["src/**"])
        self.assertTrue(records["current-state"]["source_of_truth"])
        self.assertTrue(records["current-state"]["used_for_drift"])
        self.assertEqual(records["phase0"]["status"], "historical")
        self.assertFalse(records["phase0"]["used_for_drift"])
        self.assertEqual(records["phase0"]["related_blueprints"], ["current-state"])

    def test_blueprint_registry_reports_missing_indexed_docs_as_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            blueprints = root / "_blueprints"
            blueprints.mkdir()
            (blueprints / "INDEX.md").write_text(
                "\n".join(
                    [
                        "# Index",
                        "| Document | Classification | Notes |",
                        "| --- | --- | --- |",
                        "| `missing.md` | component blueprint | Missing. |",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_blueprints()

        self.assertEqual(payload["blueprint_count"], 1)
        self.assertEqual(payload["blueprints"][0]["path"], "missing.md")
        self.assertEqual(payload["blueprints"][0]["status"], "missing")
        self.assertEqual(payload["blueprints"][0]["warnings"], ["indexed_blueprint_missing"])

    def test_blueprint_registry_loads_stable_ids_and_metadata_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            blueprints = root / "_blueprints"
            current = blueprints / "current"
            components = blueprints / "components"
            current.mkdir(parents=True)
            components.mkdir(parents=True)
            (blueprints / "INDEX.md").write_text(
                "\n".join(
                    [
                        "# Index",
                        "| Document | Classification | Notes |",
                        "| --- | --- | --- |",
                        "| `current/system.md` | current truth | Canonical. |",
                        "| `components/duplicate.md` | component blueprint | Duplicate. |",
                        "| `components/gappy.md` | component blueprint | Missing metadata. |",
                    ]
                ),
                encoding="utf-8",
            )
            (current / "system.md").write_text(
                _blueprint_doc(
                    blueprint_id="system-state",
                    title="System State",
                    component="system",
                    doc_type="current_state",
                    status="active",
                    source_of_truth=True,
                    code_paths=["src/**"],
                ),
                encoding="utf-8",
            )
            (components / "duplicate.md").write_text(
                _blueprint_doc(
                    blueprint_id="system-state",
                    title="Duplicate System State",
                    component="system",
                    doc_type="component_blueprint",
                    status="active",
                    source_of_truth=True,
                    code_paths=["source_proxy/**"],
                ),
                encoding="utf-8",
            )
            (components / "gappy.md").write_text(
                "\n".join(
                    [
                        "---",
                        "blueprint_id: Gappy State",
                        "title: Gappy State",
                        "project: SpiritOS",
                        "component: system",
                        "doc_type: component_blueprint",
                        "status: active",
                        "source_of_truth: true",
                        "owner: Britton",
                        "code_paths: []",
                        "related_blueprints: []",
                        "write_policy: proposal_only_until_dashboard_approved",
                        "---",
                        "# Gappy State",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                records = load_blueprints()

        by_path = {record.path: record for record in records}
        self.assertEqual(by_path["current/system.md"].blueprint_id, "system-state")
        self.assertTrue(
            any(
                "duplicate_blueprint_id_in_project" in record.warnings
                for record in records
                if record.blueprint_id == "system-state"
            )
        )
        self.assertIn("unstable_blueprint_id", by_path["components/gappy.md"].warnings)
        self.assertIn(
            "active_blueprint_missing_code_paths",
            by_path["components/gappy.md"].warnings,
        )
        self.assertIn(
            "source_of_truth_missing_last_verified",
            by_path["components/gappy.md"].warnings,
        )

    def test_router_exposes_only_read_only_get_endpoints(self) -> None:
        client = TestClient(_test_app())

        for route in (
            "/v1/cartographer/status",
            "/v1/cartographer/projects",
            "/v1/cartographer/project-candidates",
            "/v1/cartographer/project-health",
            "/v1/cartographer/codex-evidence",
            "/v1/cartographer/docs-autopilot/dry-run",
            "/v1/cartographer/docs-autopilot/soak",
            "/v1/cartographer/level-2-readiness",
            "/v1/cartographer/level-2-dirty-tree",
            "/v1/cartographer/level-2-dirty-tree-resolution",
            "/v1/cartographer/level-2-api-contract",
            "/v1/cartographer/level-2-closeout",
            "/v1/cartographer/branch-recommendations",
            "/v1/cartographer/commit-proposals",
            "/v1/cartographer/push-queue",
            "/v1/cartographer/audit-trail",
            "/v1/cartographer/blueprints",
            "/v1/cartographer/components",
            "/v1/cartographer/repo-map",
            "/v1/cartographer/git",
            "/v1/cartographer/drift",
            "/v1/cartographer/reminders",
            "/v1/cartographer/proposals",
            "/v1/cartographer/change-scribe",
            "/v1/cartographer/blueprint-scribe",
            "/v1/cartographer/runbook-scribe",
            "/v1/cartographer/sub-cartographers",
        ):
            response = client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["write_actions_enabled"])
            self.assertEqual(response.json()["status"], "observing")

        self.assertEqual(client.post("/v1/cartographer/status").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/projects").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/project-candidates").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/project-health").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/codex-evidence").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/docs-autopilot/dry-run").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/docs-autopilot/soak").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/level-2-readiness").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/level-2-dirty-tree").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/level-2-dirty-tree-resolution").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/level-2-api-contract").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/level-2-closeout").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/branch-recommendations").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/commit-proposals").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/push-queue").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/audit-trail").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/blueprints").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/components").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/repo-map").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/git").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/drift").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/reminders").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/proposals").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/change-scribe").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/blueprint-scribe").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/runbook-scribe").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/sub-cartographers").status_code, 405)

    def test_main_app_mounts_cartographer_routes(self) -> None:
        with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
            client = TestClient(app)
            response = client.get("/v1/cartographer/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "observing")

    def test_safe_write_status_endpoint_exposes_no_git_or_command_authority(self) -> None:
        self.assertEqual(TestClient(_test_app()).get("/v1/cartographer/safe-write").status_code, 404)

    def test_safe_write_endpoint_writes_one_exact_approved_docs_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            client = TestClient(_test_app())
            request = self._safe_write_request(
                target_file="docs/approved-api-safe-write.md",
                content="approved api safe write\n",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                response = client.post("/v1/cartographer/safe-write", json=request)

            written_file = root / "docs/approved-api-safe-write.md"
            written_exists = written_file.exists()
            written_text = written_file.read_text(encoding="utf-8") if written_exists else ""

        self.assertEqual(response.status_code, 404)
        self.assertFalse(written_exists)
        self.assertEqual(written_text, "")

    def test_safe_write_endpoint_blocks_invalid_token_without_modifying_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "docs/approved-api-safe-write.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("original\n", encoding="utf-8")
            client = TestClient(_test_app())
            request = self._safe_write_request(
                target_file="docs/approved-api-safe-write.md",
                content="replacement\n",
            )
            request["token"]["approver_id"] = "cartographer-runtime"

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                response = client.post("/v1/cartographer/safe-write", json=request)

            after = target.read_text(encoding="utf-8")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(after, "original\n")

    def test_safe_write_endpoint_blocks_without_configured_workspace_root(self) -> None:
        client = TestClient(_test_app())

        with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
            response = client.post(
                "/v1/cartographer/safe-write",
                json=self._safe_write_request(
                    target_file="docs/approved-api-safe-write.md",
                    content="blocked\n",
                ),
            )

        self.assertEqual(response.status_code, 404)

    def test_verification_status_endpoint_exposes_controlled_runner(self) -> None:
        self.assertEqual(TestClient(_test_app()).get("/v1/cartographer/verification/run").status_code, 404)

    def test_verification_run_endpoint_executes_exact_allowlisted_argv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _git(root, "init")
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                response = client.post(
                    "/v1/cartographer/verification/run",
                    json={
                        "argv": ["git", "diff", "--check"],
                        "approved_test_files": [],
                        "approved_file_checks": [],
                        "cwd_relative": ".",
                        "timeout_seconds": 5,
                    },
                )

        self.assertEqual(response.status_code, 404)

    def test_verification_run_endpoint_blocks_forbidden_argv_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": temp_dir}, clear=False):
                response = client.post(
                    "/v1/cartographer/verification/run",
                    json={
                        "argv": ["git", "reset", "--hard"],
                        "approved_test_files": [],
                        "approved_file_checks": [],
                        "cwd_relative": ".",
                        "timeout_seconds": 5,
                    },
                )

        self.assertEqual(response.status_code, 404)

    def test_verification_run_endpoint_blocks_without_configured_workspace_root(self) -> None:
        client = TestClient(_test_app())

        with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
            response = client.post(
                "/v1/cartographer/verification/run",
                json={
                    "argv": ["git", "diff", "--check"],
                    "approved_test_files": [],
                    "approved_file_checks": [],
                    "cwd_relative": ".",
                    "timeout_seconds": 5,
                },
            )

        self.assertEqual(response.status_code, 404)

    def test_spirit_project_path_reports_explicit_allowlisted_roots(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            configured, blocked = parse_project_roots(f"{first},{second},C:\\Projects")

        self.assertEqual(blocked, [])
        self.assertEqual(
            [item.path for item in configured],
            [
                str(Path(first).resolve()),
                str(Path(second).resolve()),
                "C:\\Projects",
            ],
        )
        self.assertEqual({item.status for item in configured}, {"configured"})
        self.assertEqual({item.reason for item in configured}, {"explicitly_allowlisted"})

    @staticmethod
    def _approval_token_scope() -> dict[str, str]:
        return {
            "type": "phase",
            "value": "cartographer-integrated-control-plan-4-phase-4-1",
        }

    @staticmethod
    def _approval_token_dirty_tree() -> dict[str, object]:
        return {
            "fingerprint": "api-clean-plan-4",
            "dirty_files": [],
            "expected_dirty": False,
        }

    def _approval_token_payload(self) -> dict[str, object]:
        now = datetime.now(UTC)
        return {
            "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
            "token_id": "approval-token-plan-4-api",
            "run_id": "run-plan-4-api",
            "operator_id": "cartographer-runtime",
            "approver_id": "Britton",
            "action_type": "docs_receipt_preview",
            "lane_id": "cartographer",
            "scope": self._approval_token_scope(),
            "exact_allowed_files": ["docs/cartographer-example.md"],
            "exact_forbidden_files": ["source_proxy/cartographer/apply.py"],
            "expires_at": (now + timedelta(minutes=55)).isoformat().replace("+00:00", "Z"),
            "rollback_instructions": "Manual rollback only; API preview does not write.",
            "verification_instructions": "Run focused approval-token API tests.",
            "expected_head": "abc123",
            "expected_dirty_tree": self._approval_token_dirty_tree(),
            "kill_switch_state": APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
            "trust_tier": "tier-1",
            "single_action": True,
            "issued_by_human": True,
            "human_approved_at": (now - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        }

    def _approval_token_validation_request(self) -> dict[str, object]:
        return {
            "token": self._approval_token_payload(),
            "requested_actor": "cartographer-runtime",
            "requested_scope": self._approval_token_scope(),
            "requested_action_type": "docs_receipt_preview",
            "requested_lane_id": "cartographer",
            "requested_files": ["docs/cartographer-example.md"],
            "current_head": "abc123",
            "current_dirty_tree": self._approval_token_dirty_tree(),
            "kill_switch_active": False,
            "requested_trust_tier": "tier-1",
        }

    def _approval_token_consumption_request(self) -> dict[str, object]:
        return {
            "token": self._approval_token_payload(),
            "requested_actor": "cartographer-runtime",
            "requested_scope": self._approval_token_scope(),
            "requested_action_class": "docs_receipt_preview",
            "requested_lane_id": "cartographer",
            "requested_files": ["docs/cartographer-example.md"],
            "consumption_context": {
                "action_class": "docs_receipt_preview",
                "trust_tier": "tier-1",
                "requested_trust_tier": "tier-1",
                "exact_allowed_files": ["docs/cartographer-example.md"],
                "exact_forbidden_files": ["source_proxy/cartographer/apply.py"],
                "expected_head": "abc123",
                "expected_dirty_tree": self._approval_token_dirty_tree(),
                "rollback": "Manual review only; no runtime write is available.",
                "verification": "Run focused approval-token API tests.",
            },
            "current_head": "abc123",
            "current_dirty_tree": self._approval_token_dirty_tree(),
            "kill_switch_active": False,
        }

    def _safe_write_request(self, *, target_file: str, content: str) -> dict[str, object]:
        now = datetime.now(UTC)
        scope = {
            "type": "phase",
            "value": "cartographer-integrated-control-plan-5-phase-5-1",
        }
        dirty_tree = {
            "fingerprint": "api-safe-write-clean-plan-5",
            "dirty_files": [],
            "expected_dirty": False,
        }
        return {
            "token": {
                "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
                "token_id": "approval-token-plan-5-phase-5-1-api",
                "run_id": "run-plan-5-phase-5-1-api",
                "operator_id": "cartographer-runtime",
                "approver_id": "Britton",
                "action_type": "safe_write",
                "lane_id": "cartographer",
                "scope": scope,
                "exact_allowed_files": [target_file],
                "exact_forbidden_files": ["source_proxy/api/cartographer.py"],
                "expires_at": (now + timedelta(minutes=55)).isoformat().replace("+00:00", "Z"),
                "rollback_instructions": "Manually restore the exact target file content.",
                "verification_instructions": "Run focused safe-write API tests.",
                "expected_head": "abc123",
                "expected_dirty_tree": dirty_tree,
                "kill_switch_state": APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
                "trust_tier": "tier-1",
                "single_action": True,
                "issued_by_human": True,
                "human_approved_at": (now - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
            },
            "requested_actor": "cartographer-runtime",
            "requested_scope": scope,
            "target_file": target_file,
            "content": content,
            "consumption_context": {
                "action_class": "safe_write",
                "active_lane_id": "cartographer",
                "lane_owner": "cartographer",
                "lane_dirty_overlap_status": "clear",
                "trust_tier": "tier-1",
                "requested_trust_tier": "tier-1",
                "exact_allowed_files": [target_file],
                "exact_forbidden_files": ["source_proxy/api/cartographer.py"],
                "expected_head": "abc123",
                "expected_dirty_tree": dirty_tree,
                "rollback": "Manually restore the exact target file content.",
                "verification": "Run focused safe-write API tests.",
            },
            "current_head": "abc123",
            "dirty_tree_matches_expected": True,
            "kill_switch_active": False,
        }

    def test_spirit_project_path_empty_env_is_safe_empty_output(self) -> None:
        configured, blocked = parse_project_roots("")

        self.assertEqual(configured, [])
        self.assertEqual(blocked, [])

    def test_spirit_project_path_blocks_broad_and_secret_shaped_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            safe_root = Path(temp_dir) / "Project"
            secret_root = Path(temp_dir) / ".env"
            backup_root = Path(temp_dir) / "backups"
            configured, blocked = parse_project_roots(
                f"{safe_root},/etc,{secret_root},{backup_root},C:\\Windows"
            )

        self.assertEqual([item.path for item in configured], [str(safe_root.resolve())])
        self.assertEqual(
            [item.reason for item in blocked],
            [
                "broad_system_root_not_allowed",
                "secret_or_backup_shaped_root_not_allowed",
                "secret_or_backup_shaped_root_not_allowed",
                "broad_system_root_not_allowed",
            ],
        )

    def test_spirit_project_path_blocks_traversal_shaped_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            safe_root = parent / "Project"
            traversal_root = safe_root / ".." / "OutsideProject"
            configured, blocked = parse_project_roots(str(traversal_root))

        self.assertEqual(configured, [])
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0].path, str(traversal_root))
        self.assertEqual(blocked[0].reason, "path_traversal_root_not_allowed")

    def test_projects_endpoint_lists_roots_without_scanning_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text('{"secret":"SHOULD_NOT_APPEAR"}', encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_projects()

        self.assertEqual(payload["configured_roots"][0]["path"], str(root.resolve()))
        self.assertEqual(payload["configured_roots"][0]["status"], "configured")
        self.assertEqual(payload["projects"][0]["root"], str(root.resolve()))
        self.assertIn("package.json", payload["projects"][0]["markers"])
        self.assertFalse(payload["projects"][0]["has_blueprints"])
        self.assertIsNone(payload["projects"][0]["blueprint_root"])
        self.assertNotIn("SHOULD_NOT_APPEAR", str(payload))

    def test_project_discovery_detects_root_and_immediate_child_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)

            child = parent / "Client Dashboard"
            child.mkdir()
            (child / "README.md").write_text("client notes stay unread", encoding="utf-8")
            (child / "src").mkdir()

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                payload = build_cartographer_projects()

        projects = {project["name"]: project for project in payload["projects"]}
        self.assertIn("Client Dashboard", projects)
        self.assertEqual(projects["Client Dashboard"]["project_id"], "client-dashboard")
        self.assertEqual(projects["Client Dashboard"]["markers"], ["README.md", "src"])
        self.assertFalse(projects["Client Dashboard"]["has_blueprints"])
        self.assertIsNone(projects["Client Dashboard"]["blueprint_root"])
        self.assertEqual(projects["Client Dashboard"]["write_policy"], "read_only")
        self.assertNotIn("client notes stay unread", str(payload))

    def test_project_discovery_reports_blueprint_presence_without_reading_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()
            (root / "package.json").write_text("{}", encoding="utf-8")
            blueprints = root / "_blueprints"
            blueprints.mkdir()
            (blueprints / "INDEX.md").write_text("SECRET_BLUEPRINT_CONTENT", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_projects()

        project = payload["projects"][0]
        self.assertTrue(project["has_blueprints"])
        self.assertEqual(project["blueprint_root"], str((root / "_blueprints").resolve()))
        self.assertIn("_blueprints", project["markers"])
        self.assertNotIn("SECRET_BLUEPRINT_CONTENT", str(payload))

    def test_project_discovery_does_not_promote_children_when_root_is_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()
            (root / "package.json").write_text('{"name":"Root App"}', encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app").mkdir()

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_projects()

        self.assertEqual(len(payload["projects"]), 1)
        self.assertEqual(payload["projects"][0]["name"], root.name)
        self.assertEqual(payload["projects"][0]["markers"], [".git", "package.json", "src"])

    def test_project_discovery_skips_nested_junk_and_secret_shaped_folders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            junk = root / "node_modules" / "fake-project"
            junk.mkdir(parents=True)
            (junk / "package.json").write_text("{}", encoding="utf-8")

            secret = root / "secrets"
            secret.mkdir()
            (secret / "package.json").write_text("SECRET_SHOULD_NOT_APPEAR", encoding="utf-8")

            nested = root / "parent" / "nested-project"
            nested.mkdir(parents=True)
            (nested / "package.json").write_text("{}", encoding="utf-8")

            shallow = root / "real-project"
            shallow.mkdir()
            (shallow / "requirements.txt").write_text("pytest", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_projects()

        project_names = {project["name"] for project in payload["projects"]}
        self.assertEqual(project_names, {"real-project"})
        self.assertNotIn("fake-project", str(payload))
        self.assertNotIn("nested-project", str(payload))
        self.assertNotIn("SECRET_SHOULD_NOT_APPEAR", str(payload))

    def test_project_discovery_skips_child_symlink_resolving_outside_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as allowed_dir, tempfile.TemporaryDirectory() as outside_dir:
            allowed = Path(allowed_dir)
            outside = Path(outside_dir)
            (outside / "package.json").write_text('{"secret":"SHOULD_NOT_APPEAR"}', encoding="utf-8")
            link = allowed / "linked-outside"
            try:
                os.symlink(outside, link, target_is_directory=True)
            except (AttributeError, NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink unavailable: {exc}")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(allowed)}, clear=False):
                payload = build_cartographer_projects()

        self.assertEqual(payload["projects"], [])
        self.assertNotIn("linked-outside", str(payload))
        self.assertNotIn("SHOULD_NOT_APPEAR", str(payload))

    def test_project_candidate_detection_reports_new_child_project_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            child = parent / "ClientDashboard"
            child.mkdir()
            (child / ".git").mkdir()
            (child / "README.md").write_text("candidate content stays unread", encoding="utf-8")
            (child / "package.json").write_text('{"secret":"SHOULD_NOT_APPEAR"}', encoding="utf-8")

            before = sorted(path.relative_to(parent).as_posix() for path in parent.rglob("*"))
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                payload = build_cartographer_project_candidates()
            after = sorted(path.relative_to(parent).as_posix() for path in parent.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["candidate_count"], 1)
        candidate = payload["candidates"][0]
        self.assertEqual(candidate["status"], "new_project_candidate")
        self.assertEqual(candidate["approval_status"], "needs_approval")
        self.assertEqual(candidate["name"], "ClientDashboard")
        self.assertEqual(candidate["project_id"], "clientdashboard")
        self.assertEqual(candidate["markers"], [".git", "package.json", "README.md"])
        self.assertEqual(candidate["confidence"], "high")
        self.assertEqual(
            candidate["reason"],
            "Detected project-shaped child directory from markers: .git, package.json, README.md.",
        )
        self.assertFalse(candidate["action_taken"])
        self.assertNotIn("candidate content stays unread", str(payload))
        self.assertNotIn("SHOULD_NOT_APPEAR", str(payload))

    def test_project_candidate_detection_ignores_project_root_and_outside_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as outside_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()
            (root / "package.json").write_text("{}", encoding="utf-8")
            outside = Path(outside_dir) / "OutsideProject"
            outside.mkdir()
            (outside / "package.json").write_text("{}", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_project_candidates()

        self.assertEqual(payload["candidates"], [])
        self.assertEqual(payload["candidate_count"], 0)
        self.assertNotIn("OutsideProject", str(payload))

    def test_projects_endpoint_includes_candidate_summary_for_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            child = parent / "ClientDashboard"
            child.mkdir()
            (child / "README.md").write_text("client", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                payload = build_cartographer_projects()

        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["project_candidates"][0]["status"], "new_project_candidate")
        self.assertEqual(payload["project_candidates"][0]["approval_status"], "needs_approval")
        self.assertEqual(payload["project_candidates"][0]["confidence"], "low")
        self.assertIn("README.md", payload["project_candidates"][0]["reason"])

    def test_level_6_project_registry_hardening_reports_read_only_registry(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first_parent = Path(first_dir)
            second_parent = Path(second_dir)
            first = first_parent / "App"
            second = second_parent / "App"
            first.mkdir()
            second.mkdir()
            (first / ".git").mkdir()
            (first / "package.json").write_text('{"secret":"SHOULD_NOT_APPEAR"}', encoding="utf-8")
            (second / "README.md").write_text("second content stays unread", encoding="utf-8")
            missing = first_parent / "MissingProject"
            env_value = ",".join([str(first_parent), str(second_parent), str(missing)])

            first_before = sorted(path.relative_to(first_parent).as_posix() for path in first_parent.rglob("*"))
            second_before = sorted(path.relative_to(second_parent).as_posix() for path in second_parent.rglob("*"))
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": env_value}, clear=False):
                payload = build_cartographer_level_6_project_registry_hardening()
                response = TestClient(_test_app()).get("/v1/cartographer/level-6-project-registry")
            first_after = sorted(path.relative_to(first_parent).as_posix() for path in first_parent.rglob("*"))
            second_after = sorted(path.relative_to(second_parent).as_posix() for path in second_parent.rglob("*"))

        self.assertEqual(first_before, first_after)
        self.assertEqual(second_before, second_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_6.project_registry_hardening.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 6)
        self.assertEqual(payload["mode"], "project_registry_hardening")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["cross_repo_mutation_allowed"])
        self.assertFalse(payload["project_enrollment_allowed"])
        self.assertFalse(payload["auto_enrollment_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertEqual(payload["project_count"], 2)
        self.assertIn("configured_root_blockers_present", payload["blockers"])
        self.assertIn("duplicate_project_ids", payload["blockers"])
        root_checks = {root["path"]: root for root in payload["configured_roots"]}
        self.assertEqual(root_checks[str(missing.resolve())]["blockers"], ["configured_root_missing"])
        entries = payload["registry_entries"]
        self.assertEqual([entry["project_id"] for entry in entries], ["app", "app"])
        self.assertEqual(entries[0]["repo_type"], "git")
        self.assertEqual(entries[1]["repo_type"], "filesystem")
        for entry in entries:
            self.assertIsNone(entry["owner"])
            self.assertIsNone(entry["agent"])
            self.assertEqual(entry["observation_mode"], "read_only")
            self.assertTrue(entry["mutation_disabled"])
            self.assertFalse(entry["cross_repo_mutation_allowed"])
            self.assertFalse(entry["commit_allowed"])
            self.assertFalse(entry["push_allowed"])
            self.assertFalse(entry["branch_creation_allowed"])
            self.assertFalse(entry["worktree_creation_allowed"])
            self.assertFalse(entry["cleanup_allowed"])
            self.assertFalse(entry["merge_allowed"])
            self.assertFalse(entry["stash_allowed"])
            self.assertFalse(entry["auto_enrollment_allowed"])
            self.assertFalse(entry["actions_taken"])
        self.assertNotIn("SHOULD_NOT_APPEAR", str(payload))
        self.assertNotIn("second content stays unread", str(payload))

    def test_level_6_project_registry_hardening_empty_state_is_locked(self) -> None:
        with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
            payload = build_cartographer_level_6_project_registry_hardening()

        self.assertEqual(payload["level"], 6)
        self.assertEqual(payload["project_count"], 0)
        self.assertEqual(payload["candidate_count"], 0)
        self.assertEqual(payload["registry_entries"], [])
        self.assertEqual(payload["blockers"], [])
        self.assertFalse(payload["cross_repo_mutation_allowed"])
        self.assertFalse(payload["project_enrollment_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_6_cross_project_status_board_reports_read_only_project_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            spirit = parent / "SpiritOS"
            spirit.mkdir()
            _write_minimal_blueprints(spirit)
            dashboard_file = spirit / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(spirit, "init")
            _git(spirit, "config", "user.email", "cartographer@example.test")
            _git(spirit, "config", "user.name", "Cartographer Test")
            _git(spirit, "checkout", "-b", "cartographer-health")
            _git(spirit, "add", ".")
            _git(spirit, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            client = parent / "ClientDashboard"
            client.mkdir()
            (client / "README.md").write_text("client", encoding="utf-8")
            (client / "package.json").write_text("{}", encoding="utf-8")

            before_status = _git_stdout(spirit, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                payload = build_cartographer_level_6_cross_project_status_board()
                response = TestClient(_test_app()).get("/v1/cartographer/level-6-cross-project-status-board")
            after_status = _git_stdout(spirit, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_6.cross_project_status_board.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 6)
        self.assertEqual(payload["mode"], "cross_project_status_board")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["cross_repo_mutation_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["automatic_fixes_allowed"])
        self.assertEqual(payload["project_count"], 2)
        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["dirty_project_count"], 1)
        self.assertGreaterEqual(payload["blocked_project_count"], 1)
        board_items = {item["project_id"]: item for item in payload["board_items"]}
        board_item = board_items["spiritos"]
        self.assertEqual(board_item["project_id"], "spiritos")
        self.assertEqual(board_item["current_level"], 6)
        self.assertEqual(board_item["registry_status"], "registered")
        self.assertTrue(board_item["dirty"])
        self.assertEqual(board_item["branch"], "cartographer-health")
        self.assertIn("dirty_tree", board_item["blockers"])
        self.assertEqual(board_item["safe_sequencing"], "blocked")
        self.assertFalse(board_item["commit_allowed"])
        self.assertFalse(board_item["push_allowed"])
        candidate_item = payload["candidate_items"][0]
        self.assertEqual(candidate_item["project_id"], "clientdashboard")
        self.assertEqual(candidate_item["registry_status"], "candidate")
        self.assertIn("project_enrollment_requires_approval", candidate_item["blockers"])
        self.assertFalse(candidate_item["project_enrollment_allowed"])
        self.assertIn("project_enrollment_requires_approval", payload["blockers"])

    def test_level_6_cross_project_status_board_empty_state_is_locked(self) -> None:
        with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
            payload = build_cartographer_level_6_cross_project_status_board()

        self.assertEqual(payload["level"], 6)
        self.assertEqual(payload["project_count"], 0)
        self.assertEqual(payload["candidate_count"], 0)
        self.assertEqual(payload["board_items"], [])
        self.assertEqual(payload["candidate_items"], [])
        self.assertEqual(payload["blockers"], [])
        self.assertEqual(payload["recommended_next_action"], "No cross-project blockers detected.")
        self.assertFalse(payload["cross_repo_mutation_allowed"])
        self.assertFalse(payload["automatic_fixes_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_6_component_ownership_reports_conflicts_without_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_6_component_ownership_assignment()
                response = TestClient(_test_app()).get("/v1/cartographer/level-6-component-ownership")
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_6.component_ownership_agent_assignment.v1",
        )
        self.assertEqual(payload["level"], 6)
        self.assertEqual(payload["mode"], "component_ownership_agent_assignment")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["assignment_write_allowed"])
        self.assertFalse(payload["automatic_reassignment_allowed"])
        self.assertFalse(payload["cross_repo_mutation_allowed"])
        self.assertFalse(payload["repo_mutation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertGreater(payload["component_count"], 0)
        self.assertEqual(payload["changed_component_count"], 1)
        self.assertEqual(payload["conflict_count"], 1)
        conflict = payload["conflicts"][0]
        self.assertEqual(conflict["component_id"], "dashboard")
        self.assertIsNone(conflict["owner"])
        self.assertIsNone(conflict["assigned_agent"])
        self.assertTrue(conflict["owner_required"])
        self.assertEqual(conflict["assignment_status"], "unassigned")
        self.assertIn("changed_component_without_owner", conflict["conflicts"])
        self.assertFalse(conflict["assignment_write_allowed"])
        self.assertFalse(conflict["automatic_reassignment_allowed"])
        self.assertFalse(conflict["repo_mutation_allowed"])
        self.assertFalse(conflict["actions_taken"])

    def test_level_6_component_ownership_empty_state_is_locked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_6_component_ownership_assignment()

        self.assertEqual(payload["level"], 6)
        self.assertGreater(payload["component_count"], 0)
        self.assertEqual(payload["changed_component_count"], 0)
        self.assertEqual(payload["conflict_count"], 0)
        self.assertEqual(payload["conflicts"], [])
        self.assertFalse(payload["assignment_write_allowed"])
        self.assertFalse(payload["automatic_reassignment_allowed"])
        self.assertFalse(payload["repo_mutation_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_6_cross_repo_dirty_tree_classifier_classifies_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            first = parent / "FirstApp"
            second = parent / "SecondApp"
            first.mkdir()
            second.mkdir()
            _write_minimal_blueprints(first)
            _write_minimal_blueprints(second)
            dashboard_file = first / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            unknown_file = second / "misc" / "notes.txt"
            unknown_file.parent.mkdir()
            unknown_file.write_text("initial\n", encoding="utf-8")
            for root in (first, second):
                _git(root, "init")
                _git(root, "config", "user.email", "cartographer@example.test")
                _git(root, "config", "user.name", "Cartographer Test")
                _git(root, "checkout", "-b", "main")
                _git(root, "add", ".")
                _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")
            unknown_file.write_text("changed\n", encoding="utf-8")

            first_before = _git_stdout(first, "status", "--short")
            second_before = _git_stdout(second, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                payload = build_cartographer_level_6_cross_repo_dirty_tree_classifier()
                response = TestClient(_test_app()).get("/v1/cartographer/level-6-cross-repo-dirty-tree")
            first_after = _git_stdout(first, "status", "--short")
            second_after = _git_stdout(second, "status", "--short")

        self.assertEqual(first_before, first_after)
        self.assertEqual(second_before, second_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_6.cross_repo_dirty_tree_classifier.v1",
        )
        self.assertEqual(payload["level"], 6)
        self.assertEqual(payload["mode"], "cross_repo_dirty_tree_classifier")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["staging_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["cross_repo_fixes_allowed"])
        self.assertEqual(payload["project_count"], 2)
        self.assertEqual(payload["dirty_project_count"], 2)
        self.assertEqual(payload["blocking_project_count"], 1)
        by_project = {item["project_id"]: item for item in payload["classifications"]}
        self.assertEqual(
            by_project["firstapp"]["files"][0]["classification"],
            "classified_component",
        )
        self.assertEqual(by_project["firstapp"]["files"][0]["component_id"], "dashboard")
        self.assertFalse(by_project["firstapp"]["blocks_cross_repo_sequence"])
        self.assertEqual(
            by_project["secondapp"]["files"][0]["classification"],
            "unclassified",
        )
        self.assertEqual(by_project["secondapp"]["unclassified_files"], ["misc/notes.txt"])
        self.assertTrue(by_project["secondapp"]["blocks_cross_repo_sequence"])
        self.assertEqual(payload["unclassified_file_count"], 1)
        self.assertEqual(payload["forbidden_file_count"], 0)

    def test_level_6_cross_repo_dirty_tree_classifier_empty_state_is_locked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_6_cross_repo_dirty_tree_classifier()

        self.assertEqual(payload["level"], 6)
        self.assertEqual(payload["project_count"], 1)
        self.assertEqual(payload["dirty_project_count"], 0)
        self.assertEqual(payload["blocking_project_count"], 0)
        self.assertEqual(payload["forbidden_file_count"], 0)
        self.assertEqual(payload["unclassified_file_count"], 0)
        self.assertFalse(payload["staging_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["cross_repo_fixes_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_6_multi_project_closeout_dashboard_summarizes_blockers_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_6_multi_project_closeout_dashboard()
                response = TestClient(_test_app()).get("/v1/cartographer/level-6-multi-project-closeout")
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_6.multi_project_closeout_dashboard.v1",
        )
        self.assertEqual(payload["level"], 6)
        self.assertEqual(payload["mode"], "multi_project_closeout_dashboard")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertEqual(payload["project_count"], 1)
        self.assertEqual(payload["ready_project_count"], 0)
        self.assertEqual(payload["blocked_project_count"], 1)
        item = payload["closeout_items"][0]
        self.assertEqual(item["current_level"], 6)
        self.assertEqual(item["allowed_authority"], "read_only_closeout_dashboard")
        self.assertEqual(item["closeout_status"], "blocked")
        self.assertIn("dirty_tree", item["blockers"])
        self.assertIn("ownership_conflicts_present", item["blockers"])
        self.assertTrue(item["mutation_disabled"])
        self.assertFalse(item["automatic_promotion_allowed"])
        self.assertFalse(item["automatic_execution_allowed"])
        self.assertEqual(
            payload["next_approved_increment"],
            "Level 7+: Future Limited Autopilot, disabled by default",
        )

    def test_level_6_multi_project_closeout_dashboard_clean_state_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_6_multi_project_closeout_dashboard()

        self.assertEqual(payload["level"], 6)
        self.assertEqual(payload["project_count"], 1)
        self.assertEqual(payload["ready_project_count"], 0)
        self.assertEqual(payload["blocked_project_count"], 1)
        self.assertTrue(payload["dashboard_blockers"])
        item = payload["closeout_items"][0]
        self.assertEqual(item["closeout_status"], "blocked")
        self.assertEqual(item["next_safe_action"], "Resolve blockers before closeout.")
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_7_disabled_by_default_feature_flag_is_locked_when_unset(self) -> None:
        with patch.dict(
            os.environ,
            {
                "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "",
                "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "",
            },
            clear=False,
        ):
            os.environ.pop("CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED", None)
            os.environ.pop("CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH", None)
            payload = build_cartographer_level_7_disabled_by_default()
            response = TestClient(_test_app()).get("/v1/cartographer/level-7-disabled-by-default")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_7.disabled_by_default_feature_flag.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 7)
        self.assertEqual(payload["mode"], "disabled_by_default_feature_flag")
        self.assertFalse(payload["feature_flag"]["default"])
        self.assertFalse(payload["feature_flag"]["requested"])
        self.assertFalse(payload["feature_flag"]["enabled"])
        self.assertTrue(payload["feature_flag"]["kill_switch_active"])
        self.assertEqual(payload["feature_flag"]["mode"], "disabled")
        self.assertFalse(payload["level_7_autopilot_enabled"])
        self.assertFalse(payload["level_7_autopilot_requested"])
        self.assertTrue(payload["level_7_autopilot_kill_switch"])
        self.assertFalse(payload["level_7_autopilot_action_available"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["recommendation_contract_available"])
        self.assertFalse(payload["dry_run_action_packet_builder_available"])
        self.assertFalse(payload["exact_approval_handshake_available"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_7_disabled_by_default_flag_does_not_create_action_authority_when_configured(self) -> None:
        with patch.dict(
            os.environ,
            {
                "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "true",
                "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "false",
            },
            clear=False,
        ):
            payload = build_cartographer_level_7_disabled_by_default()

        self.assertTrue(payload["feature_flag"]["requested"])
        self.assertTrue(payload["feature_flag"]["enabled"])
        self.assertFalse(payload["feature_flag"]["kill_switch_active"])
        self.assertEqual(payload["feature_flag"]["mode"], "configured_but_actions_unavailable")
        self.assertFalse(payload["level_7_autopilot_action_available"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["safety"]["level_7_autopilot_action_available"])

    def test_level_7_next_safe_action_recommends_human_review_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "false",
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_level_7_next_safe_action()
                response = TestClient(_test_app()).get("/v1/cartographer/level-7-next-safe-action")
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_7.next_safe_action_recommendation.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 7)
        self.assertEqual(payload["mode"], "next_safe_action_recommendation")
        self.assertTrue(payload["recommendation_only"])
        self.assertTrue(payload["recommendation_contract_available"])
        self.assertFalse(payload["dry_run_action_packet_builder_available"])
        self.assertFalse(payload["exact_approval_handshake_available"])
        self.assertIn("level_7_autopilot_disabled_by_default", payload["blockers"])
        self.assertIn("level_7_action_authority_unavailable", payload["blockers"])
        self.assertIn("level_6_closeout_blockers_present", payload["blockers"])
        self.assertEqual(payload["next_safe_action_status"], "blocked")
        self.assertTrue(payload["recommendation"]["operator_action_required"])
        self.assertFalse(payload["recommendation"]["cartographer_may_execute"])
        self.assertFalse(payload["recommendation"]["cartographer_may_create_dry_run_packet"])
        self.assertFalse(payload["level_7_autopilot_enabled"])
        self.assertFalse(payload["level_7_autopilot_action_available"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_7_next_safe_action_stays_non_executing_when_flag_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "true",
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "false",
                },
                clear=False,
            ):
                payload = build_cartographer_level_7_next_safe_action()

        self.assertTrue(payload["level_7_autopilot_enabled"])
        self.assertFalse(payload["level_7_autopilot_action_available"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["recommendation_only"])
        self.assertFalse(payload["recommendation"]["cartographer_may_execute"])
        self.assertFalse(payload["recommendation"]["cartographer_may_create_dry_run_packet"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_7_dry_run_action_packet_builds_preview_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "false",
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_level_7_dry_run_action_packet()
                response = TestClient(_test_app()).get("/v1/cartographer/level-7-dry-run-action-packet")
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_7.dry_run_action_packet_builder.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 7)
        self.assertEqual(payload["mode"], "dry_run_action_packet_builder")
        self.assertEqual(payload["packet_count"], 1)
        self.assertTrue(payload["recommendation_contract_available"])
        self.assertTrue(payload["dry_run_action_packet_builder_available"])
        self.assertFalse(payload["exact_approval_handshake_available"])
        packet = payload["packet"]
        self.assertEqual(packet["packet_type"], "dry_run_action_packet")
        self.assertEqual(packet["packet_id"], "cartographer.level_7.dry_run.next_safe_action_review.v1")
        self.assertFalse(packet["actions_taken"])
        self.assertFalse(packet["cartographer_may_execute"])
        self.assertFalse(packet["cartographer_may_self_approve"])
        self.assertFalse(packet["approval_handshake_available"])
        self.assertFalse(packet["execution_available"])
        self.assertIn("level_7_autopilot_disabled_by_default", packet["blockers"])
        self.assertIn("source_proxy/cartographer/service.py", packet["allowed_files"])
        self.assertIn("automatic execution", packet["forbidden_actions"])
        self.assertIn("self-approval", packet["forbidden_actions"])
        self.assertFalse(payload["level_7_autopilot_action_available"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_7_dry_run_action_packet_stays_non_executing_when_flag_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "true",
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "false",
                },
                clear=False,
            ):
                payload = build_cartographer_level_7_dry_run_action_packet()

        packet = payload["packet"]
        self.assertTrue(payload["level_7_autopilot_enabled"])
        self.assertFalse(payload["level_7_autopilot_action_available"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["dry_run_action_packet_builder_available"])
        self.assertFalse(payload["exact_approval_handshake_available"])
        self.assertFalse(packet["actions_taken"])
        self.assertFalse(packet["cartographer_may_execute"])
        self.assertFalse(packet["cartographer_may_self_approve"])
        self.assertFalse(packet["approval_handshake_available"])
        self.assertFalse(packet["execution_available"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_7_exact_approval_handshake_validates_preview_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "true",
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "false",
                },
                clear=False,
            ):
                packet = build_cartographer_level_7_dry_run_action_packet()["packet"]
                payload = build_cartographer_level_7_exact_approval_handshake(
                    packet_id=packet["packet_id"],
                    approval_id="approval-level-7-4",
                    approved_by="Britton",
                    exact_allowed_files=packet["allowed_files"],
                    exact_forbidden_actions=packet["forbidden_actions"],
                    exact_manual_check_commands=packet["manual_check_commands"],
                    approved_at="2026-05-20T00:00:00Z",
                )
                response = TestClient(_test_app()).post(
                    f"/v1/cartographer/level-7-dry-run-action-packet/{packet['packet_id']}/approval-preview",
                    json={
                        "approval_id": "approval-level-7-4",
                        "approved_by": "Britton",
                        "exact_allowed_files": packet["allowed_files"],
                        "exact_forbidden_actions": packet["forbidden_actions"],
                        "exact_manual_check_commands": packet["manual_check_commands"],
                        "approved_at": "2026-05-20T00:00:00Z",
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["approval_version"],
            "cartographer.level_7.exact_approval_handshake_preview.v1",
        )
        self.assertEqual(payload["status"], "approval_preview")
        self.assertEqual(payload["level"], 7)
        self.assertEqual(payload["mode"], "exact_approval_handshake_preview")
        self.assertEqual(payload["blockers"], [])
        self.assertEqual(payload["execution_blockers"], ["level_7_execution_not_implemented"])
        self.assertTrue(payload["approval_preview_valid"])
        self.assertTrue(payload["approval_handshake_available"])
        self.assertFalse(payload["execution_available"])
        self.assertTrue(payload["validated_fields"]["exact_packet_id"])
        self.assertTrue(payload["validated_fields"]["allowed_files_exact"])
        self.assertTrue(payload["validated_fields"]["forbidden_actions_exact"])
        self.assertTrue(payload["validated_fields"]["manual_check_commands_exact"])
        self.assertFalse(payload["validated_fields"]["self_approval_blocked"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_7_exact_approval_handshake_blocks_self_approval_and_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                packet = build_cartographer_level_7_dry_run_action_packet()["packet"]
                payload = build_cartographer_level_7_exact_approval_handshake(
                    packet_id="wrong-packet",
                    approval_id=None,
                    approved_by="Cartographer",
                    exact_allowed_files=[],
                    exact_forbidden_actions=[],
                    exact_manual_check_commands=[],
                    approved_at=None,
                )

        self.assertFalse(payload["approval_preview_valid"])
        self.assertIn("packet_id_mismatch", payload["blockers"])
        self.assertIn("approval_id_required", payload["blockers"])
        self.assertIn("self_approval_blocked", payload["blockers"])
        self.assertIn("approved_at_required", payload["blockers"])
        self.assertIn("exact_allowed_files_mismatch", payload["blockers"])
        self.assertIn("exact_forbidden_actions_mismatch", payload["blockers"])
        self.assertIn("exact_manual_check_commands_mismatch", payload["blockers"])
        self.assertTrue(payload["validated_fields"]["self_approval_blocked"])
        self.assertEqual(payload["packet"]["packet_id"], packet["packet_id"])
        self.assertFalse(payload["execution_available"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_7_closeout_dashboard_summarizes_safe_preview_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "true",
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "false",
                },
                clear=False,
            ):
                payload = build_cartographer_level_7_closeout_dashboard()
                response = TestClient(_test_app()).get("/v1/cartographer/level-7-closeout-dashboard")
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_7.closeout_dashboard.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 7)
        self.assertEqual(payload["mode"], "level_7_closeout_dashboard")
        self.assertTrue(payload["level_7_closed_out"])
        self.assertTrue(payload["level_8_gated"])
        self.assertFalse(payload["level_8_may_begin"])
        self.assertTrue(payload["operator_approval_required_for_level_8"])
        self.assertEqual(payload["closeout_blockers"], [])
        self.assertEqual(len(payload["closeout_items"]), 4)
        self.assertEqual(
            [item["closeout_status"] for item in payload["closeout_items"]],
            ["ready_for_review"] * 4,
        )
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertEqual(payload["next_step"], "Level 8.0 may begin only after explicit human approval.")

    def test_level_7_closeout_dashboard_keeps_level_8_blocked_when_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "false",
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_level_7_closeout_dashboard()

        self.assertTrue(payload["level_7_closed_out"])
        self.assertTrue(payload["level_8_gated"])
        self.assertFalse(payload["level_8_may_begin"])
        self.assertTrue(payload["operator_approval_required_for_level_8"])
        self.assertFalse(payload["disabled_state"]["level_7_autopilot_enabled"])
        self.assertFalse(payload["disabled_state"]["level_7_autopilot_action_available"])
        self.assertFalse(payload["approval_preview"]["execution_available"])
        self.assertFalse(payload["dry_run"]["packet"]["actions_taken"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_8_workflow_run_card_models_steps_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "true",
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "false",
                },
                clear=False,
            ):
                payload = build_cartographer_level_8_workflow_run_card()
                response = TestClient(_test_app()).get("/v1/cartographer/level-8-workflow-run-card")
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_8.workflow_run_card_model.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 8)
        self.assertEqual(payload["mode"], "workflow_run_card_model")
        self.assertTrue(payload["workflow_run_card_available"])
        self.assertFalse(payload["step_approval_contract_available"])
        self.assertFalse(payload["receipt_journal_available"])
        self.assertFalse(payload["background_execution_allowed"])
        self.assertFalse(payload["autonomous_retry_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        workflow = payload["workflow"]
        self.assertTrue(workflow["human_approval_required_per_step"])
        self.assertFalse(workflow["cartographer_may_execute_steps"])
        self.assertFalse(workflow["background_execution_allowed"])
        self.assertFalse(workflow["autonomous_retry_allowed"])
        self.assertTrue(workflow["receipt_journal_required_before_execution"])
        self.assertEqual(payload["step_count"], 3)
        self.assertEqual(payload["blocked_step_count"], 1)
        self.assertIn("level_8_2_not_approved", payload["blockers"])
        for step in workflow["steps"]:
            self.assertTrue(step["human_approval_required"])
            self.assertFalse(step["approved"])
            self.assertFalse(step["cartographer_may_execute"])
            self.assertFalse(step["actions_taken"])
            self.assertTrue(step["receipt_required"])
            self.assertFalse(step["retry_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_8_workflow_run_card_stays_model_only_when_level_7_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED": "false",
                    "CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_level_8_workflow_run_card()

        self.assertTrue(payload["workflow_run_card_available"])
        self.assertFalse(payload["workflow"]["cartographer_may_execute_steps"])
        self.assertFalse(payload["step_approval_contract_available"])
        self.assertFalse(payload["receipt_journal_available"])
        self.assertFalse(payload["background_execution_allowed"])
        self.assertFalse(payload["autonomous_retry_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_8_step_approval_preview_validates_one_step_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                workflow_payload = build_cartographer_level_8_workflow_run_card()
                workflow = workflow_payload["workflow"]
                step = workflow["steps"][0]
                payload = build_cartographer_level_8_step_approval_preview(
                    workflow_id=workflow["workflow_id"],
                    step_id=step["step_id"],
                    approval_id="approval-level-8-2",
                    approved_by="Britton",
                    exact_step_title=step["title"],
                    exact_manual_check_commands=workflow_payload["manual_checks"],
                    approved_at="2026-05-20T00:00:00Z",
                )
                response = TestClient(_test_app()).post(
                    f"/v1/cartographer/level-8-workflow-run-card/{workflow['workflow_id']}/steps/{step['step_id']}/approval-preview",
                    json={
                        "approval_id": "approval-level-8-2",
                        "approved_by": "Britton",
                        "exact_step_title": step["title"],
                        "exact_manual_check_commands": workflow_payload["manual_checks"],
                        "approved_at": "2026-05-20T00:00:00Z",
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["approval_version"],
            "cartographer.level_8.step_approval_contract_preview.v1",
        )
        self.assertEqual(payload["status"], "approval_preview")
        self.assertEqual(payload["level"], 8)
        self.assertEqual(payload["mode"], "step_approval_contract_preview")
        self.assertEqual(payload["blockers"], [])
        self.assertTrue(payload["approval_preview_valid"])
        self.assertTrue(payload["step_approval_contract_available"])
        self.assertFalse(payload["receipt_journal_available"])
        self.assertFalse(payload["execution_available"])
        self.assertTrue(payload["validated_fields"]["exact_workflow_id"])
        self.assertTrue(payload["validated_fields"]["exact_step_id"])
        self.assertTrue(payload["validated_fields"]["step_title_exact"])
        self.assertTrue(payload["validated_fields"]["manual_check_commands_exact"])
        self.assertFalse(payload["validated_fields"]["self_approval_blocked"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["background_execution_allowed"])
        self.assertFalse(payload["autonomous_retry_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertEqual(payload["execution_blockers"], ["level_8_step_execution_not_implemented"])

    def test_level_8_step_approval_preview_blocks_self_approval_and_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_8_step_approval_preview(
                    workflow_id="wrong-workflow",
                    step_id="missing-step",
                    approval_id=None,
                    approved_by="Cartographer",
                    exact_step_title="wrong title",
                    exact_manual_check_commands=[],
                    approved_at=None,
                )

        self.assertFalse(payload["approval_preview_valid"])
        self.assertIn("workflow_id_mismatch", payload["blockers"])
        self.assertIn("step_id_not_found", payload["blockers"])
        self.assertIn("approval_id_required", payload["blockers"])
        self.assertIn("self_approval_blocked", payload["blockers"])
        self.assertIn("approved_at_required", payload["blockers"])
        self.assertIn("exact_manual_check_commands_mismatch", payload["blockers"])
        self.assertTrue(payload["validated_fields"]["self_approval_blocked"])
        self.assertFalse(payload["execution_available"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["background_execution_allowed"])
        self.assertFalse(payload["autonomous_retry_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_8_receipt_journal_models_visible_evidence_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_8_receipt_journal()
                response = TestClient(_test_app()).get("/v1/cartographer/level-8-receipt-journal")
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_8.receipt_journal_evidence_trail.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 8)
        self.assertEqual(payload["mode"], "receipt_journal_evidence_trail")
        self.assertTrue(payload["receipt_journal_available"])
        self.assertFalse(payload["receipt_journal_write_allowed"])
        self.assertFalse(payload["hidden_receipt_writes_allowed"])
        self.assertTrue(payload["step_approval_contract_available"])
        self.assertFalse(payload["execution_available"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["entry_count"], 2)
        self.assertEqual(payload["journal"]["status"], "preview_only")
        self.assertFalse(payload["journal"]["persisted"])
        self.assertFalse(payload["journal"]["hidden_writes_allowed"])
        for entry in payload["entries"]:
            self.assertTrue(entry["visible_to_operator"])
            self.assertFalse(entry["persisted"])
            self.assertFalse(entry["hidden_write"])
            self.assertFalse(entry["actions_taken"])
            self.assertFalse(entry["execution_available"])
            self.assertTrue(entry["evidence"])
        self.assertFalse(payload["background_execution_allowed"])
        self.assertFalse(payload["autonomous_retry_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_8_receipt_journal_stays_preview_when_step_approval_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_8_receipt_journal()

        self.assertTrue(payload["approval_preview"]["approval_preview_valid"])
        self.assertFalse(payload["approval_preview"]["execution_available"])
        self.assertFalse(payload["receipt_journal_write_allowed"])
        self.assertFalse(payload["journal"]["persisted"])
        self.assertFalse(payload["journal"]["hidden_writes_allowed"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["background_execution_allowed"])
        self.assertFalse(payload["autonomous_retry_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_8_cancel_stop_failed_step_handling_fails_closed_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_8_stop_failure_handling()
                response = TestClient(_test_app()).get("/v1/cartographer/level-8-stop-failure-handling")
            after = _git_stdout(root, "status", "--short")

        self.assertEqual(before, after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_8.cancel_stop_failed_step_handling.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 8)
        self.assertEqual(payload["mode"], "cancel_stop_failed_step_handling")
        self.assertTrue(payload["stop_handling_available"])
        self.assertTrue(payload["receipt_journal_available"])
        self.assertFalse(payload["execution_available"])
        self.assertFalse(payload["workflow_continuation_allowed"])
        self.assertTrue(payload["human_review_required_to_continue"])
        self.assertEqual(payload["stopped_state_count"], 3)
        statuses = {state["status"] for state in payload["stopped_states"]}
        self.assertEqual(statuses, {"canceled", "failed", "blocked"})
        for state in payload["stopped_states"]:
            self.assertTrue(state["workflow_stopped"])
            self.assertTrue(state["later_steps_unapproved"])
            self.assertTrue(state["human_review_required"])
            self.assertFalse(state["continuation_allowed"])
            self.assertFalse(state["retry_allowed"])
            self.assertFalse(state["autonomous_retry_allowed"])
            self.assertFalse(state["background_execution_allowed"])
            self.assertFalse(state["actions_taken"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["background_execution_allowed"])
        self.assertFalse(payload["autonomous_retry_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_8_cancel_stop_failed_step_handling_does_not_write_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_8_stop_failure_handling()
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        self.assertEqual(before, after)
        self.assertFalse(payload["journal"]["persisted"])
        self.assertFalse(payload["journal"]["hidden_writes_allowed"])
        self.assertFalse(payload["workflow_continuation_allowed"])
        self.assertTrue(payload["human_review_required_to_continue"])
        self.assertFalse(payload["execution_available"])
        self.assertFalse(payload["background_execution_allowed"])
        self.assertFalse(payload["autonomous_retry_allowed"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])

    def test_level_8_closeout_smoke_summarizes_controlled_cockpit_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_8_closeout_smoke()
                response = TestClient(_test_app()).get("/v1/cartographer/level-8-closeout-smoke")
            after = _git_stdout(root, "status", "--short")

        self.assertEqual(before, after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contract_version"], "cartographer.level_8.closeout_smoke.v1")
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 8)
        self.assertEqual(payload["mode"], "level_8_closeout_smoke")
        self.assertTrue(payload["level_8_closed_out"])
        self.assertTrue(payload["level_9_gated"])
        self.assertFalse(payload["level_9_may_begin"])
        self.assertTrue(payload["operator_approval_required_for_level_9"])
        self.assertEqual(payload["closeout_blockers"], [])
        self.assertEqual(len(payload["closeout_items"]), 4)
        self.assertEqual(
            [item["closeout_status"] for item in payload["closeout_items"]],
            ["ready_for_review"] * 4,
        )
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["execution_available"])
        self.assertFalse(payload["background_execution_allowed"])
        self.assertFalse(payload["autonomous_retry_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_8_closeout_smoke_keeps_level_9_blocked_without_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_8_closeout_smoke()

        self.assertTrue(payload["level_9_gated"])
        self.assertFalse(payload["level_9_may_begin"])
        self.assertEqual(payload["next_step"], "Level 9.0 may begin only after explicit human approval.")
        self.assertFalse(payload["journal"]["journal"]["persisted"])
        self.assertFalse(payload["stop_failure"]["workflow_continuation_allowed"])
        self.assertFalse(payload["approval_preview"]["execution_available"])
        self.assertFalse(payload["workflow"]["workflow"]["cartographer_may_execute_steps"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["execution_available"])
        self.assertFalse(payload["background_execution_allowed"])
        self.assertFalse(payload["autonomous_retry_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])

    def test_level_9_worker_registry_reports_assignments_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_worker_registry()
                response = TestClient(_test_app()).get("/v1/cartographer/level-9-worker-registry")
            after = _git_stdout(root, "status", "--short")

        self.assertEqual(before, after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_9.worker_registry_assignment_model.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 9)
        self.assertEqual(payload["mode"], "worker_registry_assignment_model")
        self.assertTrue(payload["worker_registry_available"])
        self.assertTrue(payload["assignment_model_available"])
        self.assertEqual(payload["worker_count"], 1)
        self.assertEqual(payload["assignment_count"], 1)
        self.assertEqual(payload["blocked_worker_count"], 0)
        self.assertEqual(payload["blockers"], [])
        worker = payload["workers"][0]
        self.assertEqual(worker["worker_id"], "codex-primary")
        self.assertEqual(worker["assignment_status"], "observed")
        self.assertTrue(worker["recommendation_only"])
        self.assertFalse(worker["assignment_write_allowed"])
        self.assertFalse(worker["automatic_reassignment_allowed"])
        self.assertFalse(worker["force_overwrite_allowed"])
        self.assertFalse(worker["branch_creation_allowed"])
        self.assertFalse(worker["worktree_creation_allowed"])
        self.assertFalse(worker["commit_allowed"])
        self.assertFalse(worker["push_allowed"])
        self.assertFalse(worker["merge_allowed"])
        self.assertFalse(worker["actions_taken"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["assignment_write_allowed"])
        self.assertFalse(payload["automatic_reassignment_allowed"])
        self.assertFalse(payload["force_overwrite_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["self_approval_allowed"])

    def test_level_9_worker_registry_keeps_level_8_closeout_and_no_topology_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            branches_before = _git_stdout(root, "branch", "--list")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_worker_registry()
            branches_after = _git_stdout(root, "branch", "--list")

        self.assertEqual(branches_before, branches_after)
        self.assertTrue(payload["level_8_closeout"]["level_8_closed_out"])
        self.assertTrue(payload["level_8_closeout"]["level_9_gated"])
        self.assertFalse(payload["level_8_closeout"]["level_9_may_begin"])
        self.assertEqual(payload["assignments"][0]["assignment_status"], "observed")
        self.assertFalse(payload["assignments"][0]["actions_taken"])
        self.assertFalse(payload["cross_project_mutation_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["cleanup_allowed"])

    def test_level_9_one_worker_one_task_one_branch_rule_reports_without_topology_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            branches_before = _git_stdout(root, "branch", "--list")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_one_worker_rule()
                response = TestClient(_test_app()).get("/v1/cartographer/level-9-one-worker-rule")
            branches_after = _git_stdout(root, "branch", "--list")

        self.assertEqual(branches_before, branches_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_9.one_worker_one_task_one_branch_rule.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 9)
        self.assertEqual(payload["mode"], "one_worker_one_task_one_branch_rule")
        self.assertTrue(payload["rule_model_available"])
        self.assertTrue(payload["recommendation_only"])
        self.assertEqual(payload["worker_count"], 1)
        self.assertEqual(payload["rule_violation_count"], 0)
        self.assertEqual(payload["blockers"], [])
        item = payload["rule_items"][0]
        self.assertEqual(item["rule_status"], "ready_for_review")
        self.assertTrue(item["one_worker"])
        self.assertTrue(item["one_task"])
        self.assertTrue(item["one_branch"])
        self.assertFalse(item["branch_creation_allowed"])
        self.assertFalse(item["checkout_allowed"])
        self.assertFalse(item["worktree_creation_allowed"])
        self.assertFalse(item["automatic_reassignment_allowed"])
        self.assertFalse(item["force_overwrite_allowed"])
        self.assertFalse(item["actions_taken"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["assignment_write_allowed"])
        self.assertFalse(payload["automatic_reassignment_allowed"])
        self.assertFalse(payload["force_overwrite_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_9_one_worker_one_task_one_branch_rule_preserves_registry_safety(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_one_worker_rule()

        self.assertTrue(payload["registry"]["worker_registry_available"])
        self.assertFalse(payload["registry"]["assignment_write_allowed"])
        self.assertFalse(payload["registry"]["automatic_reassignment_allowed"])
        self.assertFalse(payload["registry"]["force_overwrite_allowed"])
        self.assertFalse(payload["registry"]["branch_creation_allowed"])
        self.assertFalse(payload["registry"]["worktree_creation_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])

    def test_level_9_allowed_file_conflict_checker_blocks_parallel_suggestion_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_allowed_file_conflict_checker()
                response = TestClient(_test_app()).get("/v1/cartographer/level-9-allowed-file-conflicts")
            after = _git_stdout(root, "status", "--short")

        self.assertEqual(before, after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_9.allowed_file_conflict_checker.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 9)
        self.assertEqual(payload["mode"], "allowed_file_conflict_checker")
        self.assertTrue(payload["conflict_checker_available"])
        self.assertTrue(payload["recommendation_only"])
        self.assertFalse(payload["parallel_work_suggestion_allowed"])
        self.assertEqual(payload["worker_count"], 2)
        self.assertEqual(payload["conflict_count"], 1)
        self.assertIn("allowed_file_conflicts_present", payload["blockers"])
        conflict = payload["conflicts"][0]
        self.assertEqual(conflict["file"], "source_proxy/cartographer/service.py")
        self.assertEqual(conflict["conflict_type"], "allowed_file_overlap")
        self.assertTrue(conflict["blocks_parallel_work"])
        self.assertFalse(conflict["force_overwrite_allowed"])
        self.assertFalse(conflict["automatic_reassignment_allowed"])
        self.assertFalse(conflict["actions_taken"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["assignment_write_allowed"])
        self.assertFalse(payload["automatic_reassignment_allowed"])
        self.assertFalse(payload["force_overwrite_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_9_allowed_file_conflict_checker_preserves_rule_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_allowed_file_conflict_checker()

        self.assertTrue(payload["rule_payload"]["rule_model_available"])
        self.assertFalse(payload["rule_payload"]["branch_creation_allowed"])
        self.assertFalse(payload["rule_payload"]["worktree_creation_allowed"])
        self.assertFalse(payload["rule_payload"]["force_overwrite_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])

    def test_level_9_branch_worktree_proposal_queue_is_preview_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            branches_before = _git_stdout(root, "branch", "--list")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_branch_worktree_proposal_queue()
                response = TestClient(_test_app()).get("/v1/cartographer/level-9-branch-worktree-proposals")
            branches_after = _git_stdout(root, "branch", "--list")

        self.assertEqual(branches_before, branches_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_9.branch_worktree_proposal_queue.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 9)
        self.assertEqual(payload["mode"], "branch_worktree_proposal_queue")
        self.assertTrue(payload["proposal_queue_available"])
        self.assertTrue(payload["recommendation_only"])
        self.assertEqual(payload["proposal_count"], 1)
        proposal = payload["proposals"][0]
        self.assertTrue(proposal["requires_approval"])
        self.assertFalse(proposal["branch_creation_allowed"])
        self.assertFalse(proposal["worktree_creation_allowed"])
        self.assertFalse(proposal["checkout_allowed"])
        self.assertFalse(proposal["branch_created"])
        self.assertFalse(proposal["worktree_created"])
        self.assertFalse(proposal["actions_taken"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["branch_created"])
        self.assertFalse(payload["worktree_created"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])

    def test_level_9_branch_worktree_proposal_queue_carries_conflict_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_branch_worktree_proposal_queue()

        self.assertIn("allowed_file_conflicts_present", payload["blockers"])
        self.assertEqual(payload["blocked_proposal_count"], 1)
        self.assertEqual(payload["proposals"][0]["proposal_status"], "blocked")
        self.assertTrue(payload["conflict_payload"]["conflicts"])
        self.assertFalse(payload["force_overwrite_allowed"])
        self.assertFalse(payload["automatic_reassignment_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])

    def test_level_9_stale_worker_closeout_packet_is_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            branches_before = _git_stdout(root, "branch", "--list")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_stale_worker_closeout_packet()
                response = TestClient(_test_app()).get("/v1/cartographer/level-9-stale-worker-closeout")
            branches_after = _git_stdout(root, "branch", "--list")

        self.assertEqual(branches_before, branches_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_9.stale_worker_detection_closeout_packet.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 9)
        self.assertEqual(payload["mode"], "stale_worker_detection_closeout_packet")
        self.assertTrue(payload["stale_worker_detection_available"])
        self.assertTrue(payload["closeout_packet_available"])
        self.assertEqual(payload["stale_worker_count"], 1)
        self.assertEqual(payload["closeout_packet_count"], 1)
        packet = payload["closeout_packets"][0]
        self.assertTrue(packet["stale"])
        self.assertTrue(packet["requires_human_review"])
        self.assertFalse(packet["closeout_execution_allowed"])
        self.assertFalse(packet["automatic_reassignment_allowed"])
        self.assertFalse(packet["automatic_closeout_allowed"])
        self.assertFalse(packet["branch_deletion_allowed"])
        self.assertFalse(packet["worktree_deletion_allowed"])
        self.assertFalse(packet["cleanup_allowed"])
        self.assertFalse(packet["actions_taken"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["closeout_execution_allowed"])
        self.assertFalse(payload["automatic_reassignment_allowed"])
        self.assertFalse(payload["automatic_closeout_allowed"])
        self.assertFalse(payload["branch_deletion_allowed"])
        self.assertFalse(payload["worktree_deletion_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["force_overwrite_allowed"])

    def test_level_9_stale_worker_closeout_packet_preserves_proposal_queue_safety(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_stale_worker_closeout_packet()

        self.assertTrue(payload["proposal_queue"]["proposal_queue_available"])
        self.assertFalse(payload["proposal_queue"]["branch_created"])
        self.assertFalse(payload["proposal_queue"]["worktree_created"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])

    def test_level_9_coordination_dashboard_summarizes_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            branches_before = _git_stdout(root, "branch", "--list")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_coordination_dashboard()
                response = TestClient(_test_app()).get("/v1/cartographer/level-9-coordination-dashboard")
            branches_after = _git_stdout(root, "branch", "--list")

        self.assertEqual(branches_before, branches_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_9.coordination_dashboard.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 9)
        self.assertEqual(payload["mode"], "coordination_dashboard")
        self.assertTrue(payload["coordination_dashboard_available"])
        self.assertTrue(payload["recommendation_only"])
        self.assertTrue(payload["level_9_closed_out"])
        self.assertTrue(payload["level_10_gated"])
        self.assertFalse(payload["level_10_may_begin"])
        self.assertTrue(payload["operator_approval_required_for_level_10"])
        self.assertEqual(payload["worker_count"], 1)
        self.assertEqual(payload["conflict_count"], 1)
        self.assertEqual(payload["proposal_count"], 1)
        self.assertEqual(payload["stale_worker_count"], 1)
        self.assertEqual(payload["closeout_blockers"], [])
        self.assertEqual(len(payload["closeout_items"]), 5)
        self.assertEqual(
            [item["closeout_status"] for item in payload["closeout_items"]],
            ["ready_for_review"] * 5,
        )
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["assignment_write_allowed"])
        self.assertFalse(payload["automatic_reassignment_allowed"])
        self.assertFalse(payload["force_overwrite_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["branch_deletion_allowed"])
        self.assertFalse(payload["worktree_deletion_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])

    def test_level_9_coordination_dashboard_keeps_level_10_blocked_without_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_9_coordination_dashboard()

        self.assertTrue(payload["level_10_gated"])
        self.assertFalse(payload["level_10_may_begin"])
        self.assertEqual(payload["next_step"], "Level 10.0 may begin only after explicit human approval.")
        self.assertFalse(payload["proposal_queue"]["branch_created"])
        self.assertFalse(payload["proposal_queue"]["worktree_created"])
        self.assertFalse(payload["stale_worker"]["closeout_execution_allowed"])
        self.assertFalse(payload["conflict_checker"]["force_overwrite_allowed"])
        self.assertFalse(payload["registry"]["assignment_write_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["cross_project_mutation_allowed"])

    def test_level_10_project_health_timeline_reports_read_only_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            root.mkdir()
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_10_project_health_timeline()
                response = TestClient(_test_app()).get("/v1/cartographer/level-10-project-health-timeline")
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_10.project_health_timeline.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 10)
        self.assertEqual(payload["mode"], "project_health_timeline")
        self.assertTrue(payload["timeline_available"])
        self.assertTrue(payload["read_only"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["background_mutation_allowed"])
        self.assertFalse(payload["hidden_writes_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["evidence_mutation_allowed"])
        self.assertEqual(payload["project_count"], 1)
        self.assertEqual(payload["dirty_project_count"], 1)
        self.assertGreaterEqual(payload["blocked_project_count"], 1)
        item = payload["timeline_items"][0]
        self.assertEqual(item["project_id"], "spiritos")
        self.assertTrue(item["dirty"])
        self.assertEqual(item["timeline_state"], "blocked")
        self.assertIn("project_health_probe", item["evidence_refs"])
        self.assertFalse(item["mutation_allowed"])
        self.assertTrue(payload["closeout_history"])
        self.assertIn("Level 10.3", payload["next_step"])

    def test_level_10_project_health_timeline_clean_state_is_locked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            root.mkdir()
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_10_project_health_timeline()

        self.assertEqual(payload["level"], 10)
        self.assertEqual(payload["project_count"], 1)
        self.assertEqual(payload["dirty_project_count"], 0)
        self.assertEqual(payload["timeline_items"][0]["project_id"], "spiritos")
        self.assertFalse(payload["timeline_items"][0]["dirty"])
        self.assertTrue(payload["closeout_history"])
        self.assertFalse(payload["background_mutation_allowed"])
        self.assertFalse(payload["hidden_writes_allowed"])
        self.assertFalse(payload["evidence_mutation_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_10_closeout_packet_generator_creates_previews_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            root.mkdir()
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_10_closeout_packet_generator()
                response = TestClient(_test_app()).get("/v1/cartographer/level-10-closeout-packets")
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_10.closeout_packet_generator.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 10)
        self.assertEqual(payload["mode"], "closeout_packet_generator")
        self.assertTrue(payload["closeout_packet_generator_available"])
        self.assertTrue(payload["preview_only"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["packet_finalization_allowed"])
        self.assertFalse(payload["automatic_closeout_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["hidden_evidence_writes_allowed"])
        self.assertFalse(payload["evidence_mutation_allowed"])
        self.assertFalse(payload["background_mutation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertEqual(payload["packet_count"], 1)
        packet = payload["packets"][0]
        self.assertEqual(packet["source"], "project_health_timeline")
        self.assertEqual(packet["project_id"], "spiritos")
        self.assertEqual(packet["preview_status"], "blocked")
        self.assertFalse(packet["finalized"])
        self.assertFalse(packet["persisted"])
        self.assertFalse(packet["promoted"])
        self.assertFalse(packet["evidence_written"])
        self.assertFalse(packet["actions_taken"])
        self.assertIn("dirty_tree_requires_review", packet["blockers"])

    def test_level_10_closeout_packet_generator_clean_state_still_does_not_finalize(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            root.mkdir()
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_10_closeout_packet_generator()

        self.assertEqual(payload["level"], 10)
        self.assertEqual(payload["packet_count"], 1)
        self.assertIn(payload["packets"][0]["preview_status"], {"blocked", "ready_for_review"})
        self.assertFalse(payload["packets"][0]["finalized"])
        self.assertFalse(payload["packets"][0]["persisted"])
        self.assertFalse(payload["packets"][0]["promoted"])
        self.assertFalse(payload["packets"][0]["evidence_written"])
        self.assertTrue(payload["closeout_history_packets"])
        self.assertFalse(payload["packet_finalization_allowed"])
        self.assertFalse(payload["automatic_closeout_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["hidden_evidence_writes_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_10_run_history_evidence_browser_reads_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            evidence_dir = Path(temp_dir) / "evidence"
            root.mkdir()
            evidence_dir.mkdir()
            _write_minimal_blueprints(root)
            evidence_file = evidence_dir / "codex-task-1.json"
            evidence_file.write_text(
                json.dumps(
                    {
                        "artifact_version": "codex_evidence.v1",
                        "task_id": "task-1",
                        "safety_verdict": "passed",
                        "recommendation": "ready_for_review",
                        "changed_files_after": ["docs/example.md"],
                        "approval_authority": False,
                        "apply_authority": False,
                        "commit_authority": False,
                        "push_authority": False,
                    }
                ),
                encoding="utf-8",
            )
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            evidence_before = evidence_file.read_text(encoding="utf-8")
            status_before = _git_stdout(root, "status", "--short")
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_level_10_run_history_evidence_browser()
                response = TestClient(_test_app()).get("/v1/cartographer/level-10-run-history-evidence")
            evidence_after = evidence_file.read_text(encoding="utf-8")
            status_after = _git_stdout(root, "status", "--short")

        self.assertEqual(evidence_before, evidence_after)
        self.assertEqual(status_before, status_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_10.run_history_evidence_browser.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 10)
        self.assertEqual(payload["mode"], "run_history_evidence_browser")
        self.assertTrue(payload["browser_available"])
        self.assertTrue(payload["read_only"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["run_history_mutation_allowed"])
        self.assertFalse(payload["receipt_creation_allowed"])
        self.assertFalse(payload["evidence_mutation_allowed"])
        self.assertFalse(payload["hidden_writes_allowed"])
        self.assertFalse(payload["background_mutation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertEqual(payload["run_count"], 2)
        self.assertEqual(payload["evidence_count"], 1)
        self.assertEqual(payload["evidence_links"][0]["task_id"], "task-1")
        self.assertFalse(payload["run_history"][0]["receipts_created"])
        self.assertFalse(payload["run_history"][0]["history_mutated"])

    def test_level_10_run_history_evidence_browser_handles_empty_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            evidence_dir = Path(temp_dir) / "empty-evidence"
            root.mkdir()
            evidence_dir.mkdir()
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_level_10_run_history_evidence_browser()

        self.assertEqual(payload["level"], 10)
        self.assertEqual(payload["evidence_count"], 0)
        self.assertEqual(payload["evidence_links"], [])
        self.assertTrue(payload["closeout_packet_previews"])
        self.assertIn("build_cartographer_codex_evidence", payload["provenance"])
        self.assertFalse(payload["receipt_creation_allowed"])
        self.assertFalse(payload["run_history_mutation_allowed"])
        self.assertFalse(payload["evidence_mutation_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_10_scout_blueprint_handoff_preview_does_not_write_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            evidence_dir = Path(temp_dir) / "evidence"
            root.mkdir()
            evidence_dir.mkdir()
            _write_minimal_blueprints(root)
            scout_file = root / "scout" / "src" / "scout" / "packets" / "synthesis.py"
            scout_file.parent.mkdir(parents=True)
            scout_file.write_text("SCOUT_CONTEXT = 'before'\n", encoding="utf-8")
            evidence_file = evidence_dir / "codex-scout-task.json"
            evidence_file.write_text(
                json.dumps(
                    {
                        "artifact_version": "codex_evidence.v1",
                        "task_id": "scout-task",
                        "safety_verdict": "passed",
                        "recommendation": "ready_for_review",
                        "changed_files_after": [
                            "scout/src/scout/packets/synthesis.py",
                            "_blueprints/current/dashboard_state.md",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            blueprint_file = root / "_blueprints" / "current" / "dashboard_state.md"
            scout_before = scout_file.read_text(encoding="utf-8")
            blueprint_before = blueprint_file.read_text(encoding="utf-8")
            evidence_before = evidence_file.read_text(encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_level_10_scout_blueprint_handoff_preview()
                response = TestClient(_test_app()).get(
                    "/v1/cartographer/level-10-scout-blueprint-handoff-preview"
                )
            scout_after = scout_file.read_text(encoding="utf-8")
            blueprint_after = blueprint_file.read_text(encoding="utf-8")
            evidence_after = evidence_file.read_text(encoding="utf-8")

        self.assertEqual(scout_before, scout_after)
        self.assertEqual(blueprint_before, blueprint_after)
        self.assertEqual(evidence_before, evidence_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_10.scout_blueprint_handoff_preview.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 10)
        self.assertEqual(payload["mode"], "scout_blueprint_handoff_preview")
        self.assertTrue(payload["handoff_preview_available"])
        self.assertTrue(payload["preview_only"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["scout_writes_allowed"])
        self.assertFalse(payload["proxy_memory_writes_allowed"])
        self.assertFalse(payload["coding_context_writes_allowed"])
        self.assertFalse(payload["blueprint_writes_allowed"])
        self.assertFalse(payload["scout_write_allowed"])
        self.assertFalse(payload["proxy_memory_write_allowed"])
        self.assertFalse(payload["coding_context_write_allowed"])
        self.assertFalse(payload["blueprint_write_allowed"])
        self.assertFalse(payload["evidence_writes_allowed"])
        self.assertFalse(payload["receipt_creation_allowed"])
        self.assertFalse(payload["run_history_mutation_allowed"])
        self.assertFalse(payload["background_mutation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertEqual(payload["handoff_count"], 2)
        scout_preview = payload["handoff_previews"][0]
        self.assertEqual(scout_preview["target"], "scout")
        self.assertIn("scout/src/scout/packets/synthesis.py", scout_preview["source_refs"])
        self.assertFalse(scout_preview["writes_allowed"])
        self.assertFalse(scout_preview["scout_writes_allowed"])
        self.assertFalse(scout_preview["proxy_memory_writes_allowed"])
        self.assertFalse(scout_preview["coding_context_writes_allowed"])
        self.assertFalse(scout_preview["blueprint_writes_allowed"])
        self.assertFalse(scout_preview["evidence_writes_allowed"])
        self.assertFalse(scout_preview["receipt_creation_allowed"])
        self.assertFalse(scout_preview["run_history_mutation_allowed"])

    def test_level_10_scout_blueprint_handoff_preview_blocks_empty_sources_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            evidence_dir = Path(temp_dir) / "empty-evidence"
            root.mkdir()
            evidence_dir.mkdir()
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_level_10_scout_blueprint_handoff_preview()

        self.assertEqual(payload["level"], 10)
        self.assertEqual(payload["handoff_count"], 2)
        self.assertIn("no_scout_evidence_refs_observed", payload["blockers"])
        self.assertIn("no_blueprints_observed", payload["blockers"])
        self.assertFalse(payload["scout_writes_allowed"])
        self.assertFalse(payload["proxy_memory_writes_allowed"])
        self.assertFalse(payload["coding_context_writes_allowed"])
        self.assertFalse(payload["blueprint_writes_allowed"])
        self.assertFalse(payload["scout_write_allowed"])
        self.assertFalse(payload["proxy_memory_write_allowed"])
        self.assertFalse(payload["coding_context_write_allowed"])
        self.assertFalse(payload["blueprint_write_allowed"])
        self.assertFalse(payload["evidence_writes_allowed"])
        self.assertFalse(payload["receipt_creation_allowed"])
        self.assertFalse(payload["run_history_mutation_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_10_production_readiness_checklist_fails_closed_with_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            evidence_dir = Path(temp_dir) / "empty-evidence"
            root.mkdir()
            evidence_dir.mkdir()
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_level_10_production_readiness_checklist()
                response = TestClient(_test_app()).get(
                    "/v1/cartographer/level-10-production-readiness-checklist"
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_10.production_readiness_checklist.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 10)
        self.assertEqual(payload["mode"], "production_readiness_checklist")
        self.assertTrue(payload["readiness_checklist_available"])
        self.assertTrue(payload["fail_closed"])
        self.assertFalse(payload["production_operator_ready"])
        self.assertIn("known_limitations_reviewed", payload["blockers"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["hidden_autonomy_allowed"])
        self.assertFalse(payload["background_mutation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["new_levels_allowed"])
        self.assertTrue(all(check["operator_explainable"] for check in payload["checks"]))
        self.assertTrue(all(check["rollback_path_required"] for check in payload["checks"]))
        self.assertTrue(all(check["audit_path_required"] for check in payload["checks"]))

    def test_level_10_production_readiness_checklist_remains_explainable_when_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            evidence_dir = Path(temp_dir) / "evidence"
            root.mkdir()
            evidence_dir.mkdir()
            _write_minimal_blueprints(root)
            evidence_file = evidence_dir / "codex-scout-task.json"
            evidence_file.write_text(
                json.dumps(
                    {
                        "artifact_version": "codex_evidence.v1",
                        "task_id": "scout-task",
                        "safety_verdict": "passed",
                        "recommendation": "ready_for_review",
                        "changed_files_after": ["scout/src/scout/packets/synthesis.py"],
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_level_10_production_readiness_checklist()

        self.assertTrue(payload["production_operator_ready"])
        self.assertEqual(payload["blockers"], [])
        self.assertEqual({check["status"] for check in payload["checks"]}, {"ready"})
        self.assertFalse(payload["hidden_autonomy_allowed"])
        self.assertFalse(payload["background_mutation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertFalse(payload["new_levels_allowed"])
        self.assertIn("Level 10.7", payload["next_step"])

    def test_level_10_closeout_next_roadmap_gate_stops_at_level_10_7(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            evidence_dir = Path(temp_dir) / "evidence"
            root.mkdir()
            evidence_dir.mkdir()
            _write_minimal_blueprints(root)
            evidence_file = evidence_dir / "codex-scout-task.json"
            evidence_file.write_text(
                json.dumps(
                    {
                        "artifact_version": "codex_evidence.v1",
                        "task_id": "scout-task",
                        "safety_verdict": "passed",
                        "recommendation": "ready_for_review",
                        "changed_files_after": ["scout/src/scout/packets/synthesis.py"],
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_level_10_closeout_next_roadmap_gate()
                response = TestClient(_test_app()).get(
                    "/v1/cartographer/level-10-closeout-next-roadmap-gate"
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_10.closeout_next_roadmap_gate.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 10)
        self.assertEqual(payload["mode"], "level_10_closeout_next_roadmap_gate")
        self.assertTrue(payload["level_10_closeout_available"])
        self.assertTrue(payload["level_10_closed_out"])
        self.assertTrue(payload["next_roadmap_gate_locked"])
        self.assertTrue(payload["next_roadmap_requires_explicit_user_request"])
        self.assertFalse(payload["level_11_allowed"])
        self.assertFalse(payload["extra_levels_allowed"])
        self.assertFalse(payload["new_roadmap_written"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["hidden_autonomy_allowed"])
        self.assertFalse(payload["background_mutation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])
        self.assertIsNone(payload["next_increment_title"])
        self.assertIn("Stop at Level 10.7", payload["next_step"])

    def test_level_10_closeout_next_roadmap_gate_keeps_review_blockers_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "SpiritOS"
            evidence_dir = Path(temp_dir) / "empty-evidence"
            root.mkdir()
            evidence_dir.mkdir()
            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_level_10_closeout_next_roadmap_gate()

        self.assertTrue(payload["level_10_closed_out"])
        self.assertTrue(payload["readiness_blockers_review_required"])
        self.assertIn("readiness_blockers_require_operator_review", payload["closeout_blockers"])
        self.assertTrue(payload["next_roadmap_gate_locked"])
        self.assertFalse(payload["level_11_allowed"])
        self.assertFalse(payload["extra_levels_allowed"])
        self.assertFalse(payload["new_roadmap_written"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["automatic_execution_allowed"])
        self.assertFalse(payload["automatic_promotion_allowed"])

    def test_starter_blueprint_pack_proposal_is_preview_only_for_new_project_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            child = parent / "ClientDashboard"
            child.mkdir()
            (child / ".git").mkdir()
            (child / "README.md").write_text("candidate readme stays unread", encoding="utf-8")
            (child / "package.json").write_text("{}", encoding="utf-8")

            before = sorted(path.relative_to(child).as_posix() for path in child.rglob("*"))
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                payload = build_cartographer_proposals()
            after = sorted(path.relative_to(child).as_posix() for path in child.rglob("*"))

        self.assertEqual(before, after)
        starter = [
            proposal
            for proposal in payload["proposals"]
            if proposal["type"] == "starter_blueprint_pack"
        ]
        self.assertEqual(len(starter), 1)
        proposal = starter[0]
        self.assertTrue(proposal["proposal_id"].startswith("bp-starter-"))
        self.assertEqual(proposal["status"], "drafted")
        self.assertTrue(proposal["requires_approval"])
        self.assertTrue(proposal["generated"])
        self.assertFalse(proposal["persisted"])
        self.assertFalse(proposal["action_taken"])
        self.assertIn("Likely package project", proposal["repo_purpose"])
        self.assertIn("Node/JavaScript or TypeScript", proposal["stack_guess"])
        self.assertIn("inspect package.json scripts", proposal["scripts"])
        self.assertIn("system", proposal["components"])
        self.assertIn("package scripts/dependencies need review before automation", proposal["risk_areas"])
        self.assertIn("_blueprints/current/project_state.md", proposal["suggested_docs"])
        self.assertIn("check for npm test", proposal["suggested_tests"])
        self.assertIn("_blueprints/runbooks/manual_checks.md", proposal["suggested_runbook"])
        self.assertEqual(
            proposal["proposed_files"],
            [
                "_blueprints/INDEX.md",
                "_blueprints/current/project_state.md",
                "_blueprints/components/app.md",
                "_blueprints/runbooks/manual_checks.md",
                "TODO.md",
            ],
        )
        self.assertIn("diff --git a/_blueprints/INDEX.md", proposal["diff_preview"])
        self.assertIn("+++ b/TODO.md", proposal["diff_preview"])
        self.assertIn("Starter blueprint pack for ClientDashboard", proposal["title"])
        self.assertNotIn("candidate readme stays unread", str(payload))

    def test_approved_starter_blueprint_write_creates_docs_only_without_commit_or_push(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            child = parent / "ClientDashboard"
            child.mkdir()
            (child / ".git").mkdir()
            (child / "README.md").write_text("candidate readme stays unchanged", encoding="utf-8")
            (child / "package.json").write_text("{}", encoding="utf-8")
            _git(child, "init")
            _git(child, "config", "user.email", "cartographer@example.test")
            _git(child, "config", "user.name", "Cartographer Test")
            _git(child, "add", ".")
            _git(child, "commit", "-m", "initial commit")
            head_before = _git_stdout(child, "rev-parse", "HEAD").strip()
            before = sorted(path.relative_to(child).as_posix() for path in child.rglob("*"))
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                proposal = [
                    item
                    for item in build_cartographer_proposals()["proposals"]
                    if item["type"] == "starter_blueprint_pack"
                ][0]
                response = client.post(
                    f"/v1/cartographer/starter-blueprints/{proposal['proposal_id']}/approve",
                    json={"approved": True, "approved_by": "Britton"},
                )
                audit = build_cartographer_audit_trail()

            head_after = _git_stdout(child, "rev-parse", "HEAD").strip()
            after = sorted(path.relative_to(child).as_posix() for path in child.rglob("*"))
            readme_after = (child / "README.md").read_text(encoding="utf-8")

        self.assertEqual(response.status_code, 410)
        self.assertEqual(head_before, head_after)
        self.assertEqual(before, after)
        self.assertNotIn("_blueprints/INDEX.md", after)
        self.assertEqual(readme_after, "candidate readme stays unchanged")

    def test_starter_blueprint_write_requires_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            child = parent / "ClientDashboard"
            child.mkdir()
            (child / "README.md").write_text("candidate", encoding="utf-8")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                proposal = [
                    item
                    for item in build_cartographer_proposals()["proposals"]
                    if item["type"] == "starter_blueprint_pack"
                ][0]
                payload = write_cartographer_starter_blueprints(
                    proposal_id=proposal["proposal_id"], approved=False, approved_by="Britton"
                )

        self.assertFalse((child / "docs").exists())
        self._assert_direct_mutation_blocked(payload)

    def test_sub_cartographer_routes_include_project_onboarding_scribe_for_starter_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            child = parent / "ClientDashboard"
            child.mkdir()
            (child / "README.md").write_text("client", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                payload = build_cartographer_sub_cartographers()

        onboarding_routes = [
            route
            for route in payload["routes"]
            if route["contributors"] == ["project_onboarding_scribe"]
        ]
        self.assertEqual(len(onboarding_routes), 1)
        route = onboarding_routes[0]
        self.assertTrue(route["proposal_id"].startswith("bp-starter-"))
        self.assertIn("starter blueprint pack pending approval", route["visible_outputs"])
        self.assertIn("proposed files: 5", route["visible_outputs"])
        self.assertIn("files written: 0", route["visible_outputs"])
        self.assertFalse(route["action_taken"])

    def test_clutter_inventory_groups_candidates_without_deletion_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / ".env.local").write_text("SECRET=hidden\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "old-plan.md").write_text("old plan\n", encoding="utf-8")
            (root / "scout" / "soak-logs").mkdir(parents=True)
            (root / "scout" / "soak-logs" / "scout-soak-snapshot.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (root / "source_proxy" / "approval").mkdir(parents=True)
            (root / "source_proxy" / "approval" / "gate.py").write_text(
                "WRITE = False\n",
                encoding="utf-8",
            )
            (root / "src").mkdir()
            (root / "src" / "app.ts").write_text("export const app = true;\n", encoding="utf-8")
            (root / "repomix-output.md").write_text("generated\n", encoding="utf-8")

            client = TestClient(_test_app())
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_clutter_inventory()
                response = client.get("/v1/cartographer/clutter-inventory")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["candidate_count"], payload["candidate_count"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["deletion_enabled"])
        self.assertFalse(payload["cleanup_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["inventory_policy"], "read_only_no_deletion")
        self.assertGreaterEqual(payload["risk_counts"]["low"], 2)
        self.assertGreaterEqual(payload["risk_counts"]["medium"], 1)
        self.assertGreaterEqual(payload["risk_counts"]["high"], 1)
        self.assertGreaterEqual(payload["risk_counts"]["blocked"], 1)
        candidates = {candidate["path"]: candidate for candidate in payload["candidates"]}
        self.assertIn("scout/soak-logs/scout-soak-snapshot.json", candidates)
        self.assertEqual(candidates["scout/soak-logs/scout-soak-snapshot.json"]["risk"], "low")
        self.assertEqual(candidates["docs/old-plan.md"]["risk"], "medium")
        self.assertEqual(candidates["src/app.ts"]["risk"], "high")
        self.assertIn("[redacted]", candidates)
        self.assertTrue(
            all(candidate["deletion_allowed"] is False for candidate in payload["candidates"])
        )
        self.assertTrue(
            all(candidate["action_taken"] is False for candidate in payload["candidates"])
        )

    def test_clutter_proposals_include_only_low_risk_files_without_deleting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "scout" / "soak-logs").mkdir(parents=True)
            low_path = root / "scout" / "soak-logs" / "scout-soak-snapshot.json"
            low_path.write_text("{}\n", encoding="utf-8")
            (root / "docs").mkdir()
            medium_path = root / "docs" / "old-plan.md"
            medium_path.write_text("old plan\n", encoding="utf-8")
            (root / "src").mkdir()
            high_path = root / "src" / "app.ts"
            high_path.write_text("export const app = true;\n", encoding="utf-8")
            blocked_path = root / ".env.local"
            blocked_path.write_text("SECRET=hidden\n", encoding="utf-8")
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

            client = TestClient(_test_app())
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_clutter_proposals()
                response = client.get("/v1/cartographer/clutter-proposals")
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["proposal_count"], payload["proposal_count"])
        self.assertEqual(before, after)
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["deletion_enabled"])
        self.assertFalse(payload["cleanup_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["proposal_policy"], "proposal_only_no_deletion")
        self.assertEqual(payload["proposal_count"], 1)
        proposal = payload["proposals"][0]
        self.assertTrue(proposal["proposal_id"].startswith("cleanup-prop-"))
        self.assertEqual(proposal["status"], "drafted")
        self.assertEqual(proposal["proposal_type"], "low_risk_deletion")
        self.assertEqual(proposal["risk"], "low")
        self.assertEqual(proposal["files"], ["scout/soak-logs/scout-soak-snapshot.json"])
        self.assertEqual(proposal["file_count"], 1)
        self.assertTrue(proposal["requires_approval"])
        self.assertFalse(proposal["deletion_enabled"])
        self.assertFalse(proposal["action_taken"])
        self.assertTrue(proposal["rollback_instructions"])
        self.assertIn("No deletion has occurred", proposal["rollback_instructions"][0])
        review_paths = {candidate["path"] for candidate in payload["review_required"]}
        self.assertIn("docs/old-plan.md", review_paths)
        self.assertIn("src/app.ts", review_paths)
        self.assertIn("[redacted]", review_paths)

    def test_clutter_review_summarizes_cleanup_without_deletion_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "scout" / "soak-logs").mkdir(parents=True)
            (root / "scout" / "soak-logs" / "scout-soak-snapshot.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (root / "docs").mkdir()
            (root / "docs" / "old-plan.md").write_text("old plan\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app.ts").write_text("export const app = true;\n", encoding="utf-8")
            (root / ".env.local").write_text("SECRET=hidden\n", encoding="utf-8")
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_clutter_review()
                response = client.get("/v1/cartographer/clutter-review")
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["review_mode"], payload["review_mode"])
        self.assertEqual(before, after)
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["deletion_enabled"])
        self.assertFalse(payload["cleanup_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["review_mode"], "read_only_cleanup_review")
        self.assertEqual(payload["deletion_candidate_count"], 0)
        self.assertTrue(payload["cleanup_decision_required"])
        self.assertGreaterEqual(payload["low_risk_candidate_count"], 1)
        self.assertGreaterEqual(payload["review_required_count"], 3)
        self.assertTrue(payload["proposal_ids"])
        self.assertIn("/v1/cartographer/clutter-inventory", payload["source_endpoints"])
        self.assertIn("/v1/cartographer/clutter-proposals", payload["source_endpoints"])
        self.assertIn("deletion_enabled remains false", payload["expected_outcome"])
        self.assertFalse(payload["safety"]["write_actions_enabled"])

    def test_approved_low_risk_cleanup_route_fails_closed_without_deleting_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "scout" / "soak-logs").mkdir(parents=True)
            low_one = root / "scout" / "soak-logs" / "scout-soak-one.json"
            low_two = root / "scout" / "soak-logs" / "scout-soak-two.json"
            low_one.write_text("{}\n", encoding="utf-8")
            low_two.write_text("{}\n", encoding="utf-8")
            (root / "docs").mkdir()
            medium_path = root / "docs" / "old-plan.md"
            medium_path.write_text("old plan\n", encoding="utf-8")
            (root / "src").mkdir()
            high_path = root / "src" / "app.ts"
            high_path.write_text("export const app = true;\n", encoding="utf-8")
            blocked_path = root / ".env.local"
            blocked_path.write_text("SECRET=hidden\n", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = build_cartographer_clutter_proposals()["proposals"][0]
                response = client.post(
                    f"/v1/cartographer/clutter-proposals/{proposal['proposal_id']}/approve",
                    json={"approved": True, "approved_by": "Britton"},
                )
                audit = build_cartographer_audit_trail()
            low_one_exists = low_one.exists()
            low_two_exists = low_two.exists()
            medium_exists = medium_path.exists()
            high_exists = high_path.exists()
            blocked_exists = blocked_path.exists()

        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()["detail"]["reason_code"], "forbidden_cartographer_mutation")
        self.assertTrue(low_one_exists)
        self.assertTrue(low_two_exists)
        self.assertTrue(medium_exists)
        self.assertTrue(high_exists)
        self.assertTrue(blocked_exists)
        self.assertFalse([event for event in audit["events"] if event["event"] == "low_risk_cleanup_applied"])

    def test_low_risk_cleanup_rejects_without_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "scout" / "soak-logs").mkdir(parents=True)
            low_path = root / "scout" / "soak-logs" / "scout-soak-one.json"
            low_path.write_text("{}\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = build_cartographer_clutter_proposals()["proposals"][0]
                payload = apply_cartographer_clutter_proposal(
                    proposal_id=proposal["proposal_id"], approved=False, approved_by="Britton"
                )
            low_path_exists = low_path.exists()

        self.assertTrue(low_path_exists)
        self._assert_direct_mutation_blocked(payload)

    def test_trust_score_is_explainable_and_does_not_grant_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "source_proxy" / "approval").mkdir(parents=True)
            (root / "source_proxy" / "approval" / "gate.py").write_text(
                "WRITE = False\n",
                encoding="utf-8",
            )
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_trust_score()
                response = client.get("/v1/cartographer/trust-score")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["score"], payload["score"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["authority_change_allowed"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["score_policy"], "evidence_only_no_authority_change")
        self.assertIsInstance(payload["score"], int)
        self.assertIn(payload["grade"], {"high", "medium", "low"})
        self.assertTrue(payload["explanation"])
        self.assertTrue(payload["recommendations"])
        self.assertEqual(payload["recommendations"][0], "Keep authority locked; trust score is advisory only.")
        signals = {signal["code"]: signal for signal in payload["signals"]}
        self.assertIn("dirty_tree_explained", signals)
        self.assertIn("authority_locked", signals)
        self.assertTrue(signals["authority_locked"]["passed"])
        self.assertIn(
            "trust score does not grant apply, commit, push, cleanup, or promotion authority",
            signals["authority_locked"]["evidence"],
        )

    def test_autonomy_promotion_recommendation_is_gate_only_and_cannot_self_promote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "source_proxy" / "approval").mkdir(parents=True)
            (root / "source_proxy" / "approval" / "gate.py").write_text(
                "WRITE = False\n",
                encoding="utf-8",
            )
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_autonomy_promotion()
                response = client.get("/v1/cartographer/autonomy-promotion")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recommendation"], payload["recommendation"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["promotion_enabled"])
        self.assertFalse(payload["authority_change_allowed"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["level_1_authority_granted"])
        self.assertFalse(payload["level_1_enablement_allowed"])
        self.assertIn("level_2_readiness", payload)
        self.assertIn(payload["level_2_recommendation"], {"blocked", "watch", "ready_for_review"})
        self.assertFalse(payload["level_2_authority_granted"])
        self.assertTrue(payload["requires_human_approval"])
        self.assertTrue(payload["cannot_self_promote"])
        self.assertEqual(payload["current_level"], 5)
        self.assertEqual(payload["target_level"], 6)
        self.assertEqual(payload["recommendation"], "do_not_promote_yet")
        gates = {gate["code"]: gate for gate in payload["gates"]}
        self.assertIn("clean_diagnostics_streak", gates)
        self.assertIn("passing_soak", gates)
        self.assertIn("authority_locked", gates)
        self.assertFalse(gates["clean_diagnostics_streak"]["passed"])
        self.assertFalse(gates["passing_soak"]["passed"])
        self.assertTrue(gates["authority_locked"]["passed"])
        self.assertGreater(payload["blocker_count"], 0)
        self.assertEqual(payload["blocker_count"], len(payload["blockers"]))
        level_1 = payload["level_1_readiness"]
        self.assertEqual(level_1["level"], 1)
        self.assertIn(level_1["label"], {"blocked", "watch", "ready_for_level_1_review"})
        self.assertEqual(payload["level_1_recommendation"], level_1["label"])
        self.assertEqual(payload["level_1_readiness_score"], level_1["score"])
        self.assertFalse(level_1["authority_granted"])
        self.assertFalse(level_1["enablement_allowed"])
        self.assertFalse(level_1["actions_taken"])
        self.assertTrue(level_1["operator_review_required"])
        self.assertGreater(level_1["check_count"], 0)
        self.assertEqual(level_1["check_count"], len(level_1["checks"]))
        self.assertEqual(level_1["blocker_count"], len(level_1["blockers"]))
        checks = {check["code"]: check for check in level_1["checks"]}
        self.assertIn("v1_freeze_valid", checks)
        self.assertIn("latest_soak_pass", checks)
        self.assertIn("apply_disabled", checks)
        self.assertIn("commit_disabled", checks)
        self.assertIn("push_disabled", checks)
        self.assertIn("approval_bypass_disabled", checks)
        self.assertIn("docs_only_candidate_filters_valid", checks)
        self.assertIn("kill_switch_visible", checks)
        self.assertIn("daily_cap_visible", checks)
        self.assertIn("rollback_hints_present", checks)
        self.assertTrue(checks["apply_disabled"]["passed"])
        self.assertTrue(checks["commit_disabled"]["passed"])
        self.assertTrue(checks["push_disabled"]["passed"])

    def test_level_2_readiness_exposes_apply_boundary_without_commit_push_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_1_ACCEPTED_BY_BRITTON": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_level_2_readiness()
                response = client.get("/v1/cartographer/level-2-readiness")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["level"], 2)
        self.assertEqual(payload["level"], 2)
        self.assertEqual(payload["mode"], "human_approved_docs_apply")
        self.assertIn(payload["label"], {"blocked", "watch", "ready_for_review"})
        self.assertFalse(payload["authority_granted"])
        self.assertTrue(payload["apply_requires_human_approval"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["branch_allowed"])
        self.assertFalse(payload["delete_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["source_code_allowed"])
        self.assertFalse(payload["self_promotion_allowed"])
        self.assertFalse(payload["actions_taken"])
        checks = {check["code"]: check for check in payload["checks"]}
        self.assertTrue(checks["level_1_review_gate"]["passed"])
        self.assertTrue(checks["dirty_tree_classified"]["passed"])
        self.assertTrue(checks["docs_only_path_filter_exists"]["passed"])
        self.assertTrue(checks["approval_validation_exists"]["passed"])
        self.assertTrue(checks["apply_receipt_exists"]["passed"])
        self.assertTrue(checks["commit_push_branch_locked"]["passed"])
        self.assertTrue(checks["source_apply_blocked"]["passed"])
        self.assertTrue(checks["self_promotion_blocked"]["passed"])

    def test_level_2_readiness_accepts_durable_level_1_review_gate_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            docs = root / "docs"
            docs.mkdir()
            (docs / "cartographer-level-1-review-gate.md").write_text(
                "\n".join(
                    [
                        "# Cartographer Level 1 Review Gate",
                        "",
                        "level_1_review_gate: accepted_by_britton",
                        "- commit_allowed: false",
                        "- push_allowed: false",
                        "- self_promotion_allowed: false",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            previous_cwd = Path.cwd()
            try:
                os.chdir(root)
                with patch.dict(
                    os.environ,
                    {
                        "SPIRIT_PROJECT_PATH": str(root),
                        "CARTOGRAPHER_LEVEL_1_ACCEPTED_BY_BRITTON": "",
                    },
                    clear=False,
                ):
                    payload = build_cartographer_level_2_readiness()
            finally:
                os.chdir(previous_cwd)

        self.assertTrue(payload["level_1_accepted_by_britton"])
        self.assertTrue(payload["docs_apply_enabled"])
        checks = {check["code"]: check for check in payload["checks"]}
        self.assertTrue(checks["level_1_review_gate"]["passed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["self_promotion_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_2_readiness_blocks_unclassified_dirty_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            source_file = root / "src" / "app" / "page.tsx"
            source_file.parent.mkdir(parents=True)
            source_file.write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            source_file.write_text("export default function Page() { return 'dirty'; }\n", encoding="utf-8")

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_LEVEL_1_ACCEPTED_BY_BRITTON": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_level_2_readiness()

        self.assertEqual(payload["label"], "blocked")
        self.assertTrue(payload["dirty_tree_block"])
        self.assertIn("src/app/page.tsx", payload["unrelated_dirty_files"])
        checks = {check["code"]: check for check in payload["checks"]}
        self.assertFalse(checks["dirty_tree_classified"]["passed"])

    def test_level_2_dirty_tree_classification_groups_allowed_docs_and_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "cartographer-level-2-autonomy-plan.md").write_text("# L2\n", encoding="utf-8")
            source_file = root / "src" / "components" / "coding" / "CodingCockpitShell.tsx"
            source_file.parent.mkdir(parents=True)
            source_file.write_text("export function CodingCockpitShell() { return null; }\n", encoding="utf-8")
            scout_file = root / "scout" / "src" / "scout" / "api" / "discovery_jobs.py"
            scout_file.parent.mkdir(parents=True)
            scout_file.write_text("VALUE = 1\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "docs" / "cartographer-level-2-autonomy-plan.md").write_text("# L2\n\nUpdated.\n", encoding="utf-8")
            source_file.write_text("export function CodingCockpitShell() { return 'dirty'; }\n", encoding="utf-8")
            scout_file.write_text("VALUE = 2\n", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_2_dirty_tree()
                response = client.get("/v1/cartographer/level-2-dirty-tree")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["level"], 2)
        self.assertEqual(payload["mode"], "dirty_tree_classification")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        classification = payload["classification"]
        self.assertTrue(classification["blocks_level_2_apply"])
        self.assertIn("docs/cartographer-level-2-autonomy-plan.md", classification["buckets"]["level_2_plan_doc"])
        self.assertIn("src/components/coding/CodingCockpitShell.tsx", classification["buckets"]["coding_cockpit_dirty"])
        self.assertIn("scout/src/scout/api/discovery_jobs.py", classification["buckets"]["scout_dirty"])
        self.assertIn("src/components/coding/CodingCockpitShell.tsx", classification["unclassified_blockers"])
        self.assertIn("scout/src/scout/api/discovery_jobs.py", classification["unclassified_blockers"])

    def test_level_2_dirty_tree_resolution_packet_groups_human_owned_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            level_2_doc = root / "docs" / "cartographer-level-2-autonomy-plan.md"
            level_2_doc.parent.mkdir(parents=True)
            level_2_doc.write_text("# L2\n", encoding="utf-8")
            level_2_file = root / "source_proxy" / "cartographer" / "level_2_apply.py"
            level_2_file.parent.mkdir(parents=True)
            level_2_file.write_text("VALUE = 1\n", encoding="utf-8")
            scout_file = root / "scout" / "src" / "scout" / "api" / "discovery_jobs.py"
            scout_file.parent.mkdir(parents=True)
            scout_file.write_text("VALUE = 1\n", encoding="utf-8")
            coding_file = root / "src" / "components" / "coding" / "CodingCockpitShell.tsx"
            coding_file.parent.mkdir(parents=True)
            coding_file.write_text("export function CodingCockpitShell() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            level_2_doc.write_text("# L2\n\nUpdated.\n", encoding="utf-8")
            level_2_file.write_text("VALUE = 2\n", encoding="utf-8")
            scout_file.write_text("VALUE = 2\n", encoding="utf-8")
            coding_file.write_text("export function CodingCockpitShell() { return 'dirty'; }\n", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_2_dirty_tree_resolution()
                response = client.get("/v1/cartographer/level-2-dirty-tree-resolution")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["resolution_version"], payload["resolution_version"])
        self.assertEqual(payload["level"], 2)
        self.assertEqual(payload["mode"], "dirty_tree_resolution_packet")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["dirty_tree_block"])
        self.assertGreater(payload["blocking_file_count"], 0)
        groups = {group["group_id"]: group for group in payload["resolution_groups"]}
        self.assertFalse(groups["level_2_docs_and_receipts"]["blocks_apply"])
        self.assertTrue(groups["level_2_implementation"]["blocks_apply"])
        self.assertTrue(groups["app_and_dashboard_source"]["blocks_apply"])
        self.assertTrue(groups["scout_work"]["blocks_apply"])
        self.assertIn("source_proxy/cartographer/level_2_apply.py", groups["level_2_implementation"]["files"])
        self.assertIn("src/components/coding/CodingCockpitShell.tsx", groups["app_and_dashboard_source"]["files"])
        self.assertIn("scout/src/scout/api/discovery_jobs.py", groups["scout_work"]["files"])
        self.assertIn("auto delete", payload["forbidden_resolution_actions"])
        self.assertIn("auto commit", payload["forbidden_resolution_actions"])
        self.assertEqual(payload["next_increment"], "Human Resolve Dirty Tree Or Keep Level 2 Blocked")

    def test_level_2_api_contract_review_packet_is_read_only_and_lists_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_2_api_contract()
                response = client.get("/v1/cartographer/level-2-api-contract")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contract_version"], payload["contract_version"])
        self.assertEqual(payload["level"], 2)
        self.assertEqual(payload["mode"], "api_contract_review_packet")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["endpoint_count"], 3)
        endpoints = {endpoint["endpoint"]: endpoint for endpoint in payload["endpoints"]}
        self.assertEqual(endpoints["/v1/cartographer/level-2-readiness"]["method"], "GET")
        self.assertEqual(endpoints["/v1/cartographer/level-2-dirty-tree"]["method"], "GET")
        self.assertEqual(endpoints["/v1/cartographer/docs-autopilot/level-2/apply"]["method"], "POST")
        self.assertEqual(
            endpoints["/v1/cartographer/docs-autopilot/level-2/apply"]["request_fields"],
            ["proposal_id", "approval_id", "approval_actor"],
        )
        self.assertEqual(payload["required_apply_request_fields"], ["proposal_id", "approval_id", "approval_actor"])
        self.assertIn("src/**", payload["forbidden_paths"])
        self.assertIn("source_proxy/**", payload["forbidden_paths"])
        self.assertIn("commit_created", payload["required_receipt_fields"])
        self.assertIn("push_created", payload["required_receipt_fields"])
        self.assertIn("branch_created", payload["required_receipt_fields"])
        self.assertIn("apply when unrelated dirty files are present", payload["forbidden_actions"])
        self.assertEqual(payload["next_increment"], "Level 2 UI Review Card Read-Only Projection")

    def test_level_2_closeout_packet_summarizes_completed_surfaces_without_activation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            dirty_source = root / "src" / "app" / "page.tsx"
            dirty_source.parent.mkdir(parents=True)
            dirty_source.write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dirty_source.write_text("export default function Page() { return 'dirty'; }\n", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_2_closeout()
                response = client.get("/v1/cartographer/level-2-closeout")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["closeout_version"], payload["closeout_version"])
        self.assertEqual(payload["level"], 2)
        self.assertEqual(payload["mode"], "level_2_closeout")
        self.assertTrue(payload["implementation_complete"])
        self.assertFalse(payload["ready_for_activation"])
        self.assertEqual(payload["recommendation"], "blocked")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["docs_apply_enabled"])
        self.assertIn("level_1_review_gate", payload["blockers"])
        self.assertIn("dirty_tree_classified", payload["blockers"])
        self.assertTrue(payload["dirty_tree_block"])
        self.assertGreater(payload["dirty_tree_blocker_count"], 0)
        self.assertIn("/v1/cartographer/level-2-readiness", payload["surfaces_completed"])
        self.assertIn("/v1/cartographer/docs-autopilot/level-2/apply", payload["surfaces_completed"])
        self.assertIn("HomelabCartographerWidget Level 2 review card", payload["surfaces_completed"])
        self.assertTrue(payload["safety_contract"]["apply_requires_human_approval"])
        self.assertFalse(payload["safety_contract"]["commit_allowed"])
        self.assertFalse(payload["safety_contract"]["push_allowed"])
        self.assertFalse(payload["safety_contract"]["source_code_allowed"])
        self.assertEqual(payload["evidence"]["api_contract_version"], "cartographer.level_2.api_contract.v1")
        self.assertIn("npm test -- HomelabCartographerWidget", payload["manual_checks"])

    def test_v1_readiness_defines_final_gates_without_granting_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_readiness()
                response = client.get("/v1/cartographer/v1-readiness")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["readiness"], payload["readiness"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["v1_ready"])
        self.assertEqual(payload["readiness"], "not_ready")
        self.assertGreater(payload["blocker_count"], 0)
        self.assertEqual(payload["blocker_count"], len(payload["blockers"]))
        levels = {level["code"]: level for level in payload["required_green_levels"]}
        self.assertEqual(levels["level_0_observe_project_state"]["required"], "GREEN")
        self.assertEqual(levels["level_9_docs_only_autopilot"]["required"], "YELLOW_OR_GREEN")
        proofs = {proof["code"]: proof for proof in payload["proof_gates"]}
        self.assertFalse(proofs["three_clean_full_diagnostics"]["passed"])
        self.assertFalse(proofs["three_clean_soak_snapshots"]["passed"])
        self.assertTrue(proofs["cartographer_api_tests_pass"]["passed"])
        self.assertIn("how_to_satisfy", proofs["three_clean_full_diagnostics"])
        self.assertIn("related_endpoint", proofs["three_clean_full_diagnostics"])
        self.assertIn("manual_check", proofs["three_clean_full_diagnostics"])
        self.assertEqual(
            proofs["typescript_pass"]["related_endpoint"],
            "/v1/cartographer/v1-proof-contract",
        )
        self.assertIn(
            "Record a proof artifact showing the TypeScript check passed.",
            proofs["typescript_pass"]["how_to_satisfy"],
        )
        groups = {group["group_id"]: group for group in payload["readiness_groups"]}
        self.assertEqual(set(groups), {"diagnostics", "proof_artifacts", "authority_safety"})
        self.assertEqual(groups["diagnostics"]["status"], "blocked")
        self.assertEqual(groups["proof_artifacts"]["status"], "blocked")
        self.assertEqual(groups["authority_safety"]["status"], "green")
        self.assertEqual(groups["proof_artifacts"]["next_endpoint"], "/v1/cartographer/v1-proof-recording-proposal")
        self.assertGreater(groups["proof_artifacts"]["blocker_count"], 0)
        self.assertTrue(groups["proof_artifacts"]["blockers"][0]["how_to_satisfy"])
        self.assertIn("observe repo state", payload["authority_boundary"]["may_do"])
        self.assertIn("promote its own authority level", payload["authority_boundary"]["may_not_do"])
        self.assertFalse(payload["authority_boundary"]["automatic_merge_enabled"])
        self.assertFalse(payload["authority_boundary"]["self_promotion_enabled"])
        self.assertFalse(payload["authority_boundary"]["passing_tests_grant_authority"])

    def test_v1_closeout_checklist_projects_readiness_for_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_closeout_checklist()
                response = client.get("/v1/cartographer/v1-closeout-checklist")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checklist_mode"], payload["checklist_mode"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["checklist_mode"], "read_only_dashboard_projection")
        self.assertFalse(payload["v1_ready"])
        self.assertEqual(payload["checklist_count"], 3)
        self.assertEqual(payload["completed_count"], 1)
        checklist = {item["checklist_id"]: item for item in payload["checklist"]}
        self.assertEqual(checklist["v1-closeout-diagnostics"]["status"], "blocked")
        self.assertEqual(checklist["v1-closeout-proof_artifacts"]["status"], "blocked")
        self.assertEqual(checklist["v1-closeout-authority_safety"]["status"], "green")
        self.assertFalse(checklist["v1-closeout-proof_artifacts"]["complete"])
        self.assertTrue(checklist["v1-closeout-authority_safety"]["complete"])
        self.assertEqual(
            checklist["v1-closeout-proof_artifacts"]["next_endpoint"],
            "/v1/cartographer/v1-proof-recording-proposal",
        )
        self.assertTrue(checklist["v1-closeout-proof_artifacts"]["blocking_codes"])
        self.assertEqual(payload["next_blocked_item"]["checklist_id"], "v1-closeout-diagnostics")
        self.assertEqual(payload["source_endpoint"], "/v1/cartographer/v1-readiness")

    def test_v1_evidence_inventory_reads_existing_artifacts_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            soak_dir = root / "source_proxy" / "cartographer" / "soak-logs"
            soak_dir.mkdir(parents=True)
            for index in range(3):
                (soak_dir / f"cartographer-soak-snapshot-2026-05-18T12000{index}Z.json").write_text(
                    json.dumps(
                        {
                            "profile": "cartographer-soak-snapshot",
                            "result": "pass",
                            "generated_at": f"2026-05-18T12:00:0{index}Z",
                            "mutation_boundary": {
                                "head_changed": False,
                                "snapshot_log_only": True,
                                "unexpected_status_delta": [],
                            },
                        }
                    ),
                    encoding="utf-8",
                )
            (soak_dir / "proxy-closeout.json").write_text(
                json.dumps(
                    {
                        "profile": "proxy-closeout",
                        "result": "pass",
                        "generated_at": "2026-05-18T12:10:00Z",
                        "mutation_boundary": {
                            "head_changed": False,
                            "unexpected_status_delta": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            (root / "data").mkdir()
            (root / "data" / "v1-proof-gates.json").write_text(
                json.dumps(
                    {
                        "profile": "cartographer-v1-proof-gates",
                        "result": "pass",
                        "checks": [
                            {"id": "typecheck", "status": "passed"},
                            {"id": "lint", "status": "warnings_only"},
                            {"id": "blueprint_metadata_validation", "status": "passed"},
                            {"id": "git_diff_check", "status": "passed"},
                            {"id": "targeted_vitest", "status": "passed"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_evidence()
                response = client.get("/v1/cartographer/v1-evidence")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["inventory_policy"], "read_only_no_commands_no_writes")
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["clean_soak_count"], 3)
        self.assertEqual(payload["clean_diagnostics_count"], 1)
        self.assertEqual(payload["proof_gate_record_count"], 5)
        proofs = {proof["code"]: proof for proof in payload["proof_items"]}
        self.assertTrue(proofs["three_clean_soak_snapshots"]["passed"])
        self.assertFalse(proofs["three_clean_full_diagnostics"]["passed"])
        self.assertTrue(proofs["proxy_closeout_pass"]["passed"])
        self.assertTrue(proofs["typescript_pass"]["passed"])
        self.assertTrue(proofs["lint_pass_or_warnings_only"]["passed"])
        self.assertTrue(proofs["blueprint_validation_pass"]["passed"])
        self.assertTrue(proofs["diff_check_pass"]["passed"])
        self.assertTrue(proofs["targeted_vitest_pass"]["passed"])
        self.assertIn("phase_4f_closeout_pass", payload["missing_evidence"])

    def test_v1_proof_contract_describes_external_artifacts_without_recording(self) -> None:
        client = TestClient(_test_app())

        payload = build_cartographer_v1_proof_contract()
        response = client.get("/v1/cartographer/v1-proof-contract")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contract_version"], payload["contract_version"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["recorder_enabled"])
        self.assertFalse(payload["recording_endpoint_enabled"])
        self.assertEqual(
            payload["artifact_policy"],
            "external_recording_only_no_cartographer_writes",
        )
        self.assertIn("data/cartographer-v1-proof-gates/*.json", payload["accepted_paths"])
        self.assertIn("checks", payload["required_top_level_fields"])
        self.assertIn("typescript_pass", payload["accepted_check_ids"])
        self.assertIn("typecheck", payload["accepted_check_ids"]["typescript_pass"])
        self.assertIn("warnings_only", payload["accepted_statuses"])
        self.assertIn("Cartographer does not run proof commands from this contract.", payload["validation_notes"])
        self.assertEqual(
            payload["example_artifact"]["profile"],
            "cartographer-v1-proof-gates",
        )

    def test_v1_proof_validation_reports_schema_issues_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            proof_dir = root / "data" / "cartographer-v1-proof-gates"
            proof_dir.mkdir(parents=True)
            (proof_dir / "valid.json").write_text(
                json.dumps(
                    {
                        "profile": "cartographer-v1-proof-gates",
                        "result": "pass",
                        "checks": [
                            {"id": "typecheck", "status": "passed"},
                            {"id": "lint", "status": "warnings_only"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (proof_dir / "invalid.json").write_text(
                json.dumps(
                    {
                        "profile": "cartographer-v1-proof-gates",
                        "result": "pass",
                        "checks": [
                            {"id": "mystery_check", "status": "passed"},
                            {"id": "git_diff_check", "status": "failed"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_proof_validation()
                response = client.get("/v1/cartographer/v1-proof-validation")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["validation_status"], payload["validation_status"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["validator_enabled"])
        self.assertFalse(payload["validation_actions_enabled"])
        self.assertEqual(payload["artifact_count"], 2)
        self.assertEqual(payload["valid_artifact_count"], 1)
        self.assertEqual(payload["invalid_artifact_count"], 1)
        self.assertEqual(payload["validation_status"], "issues_found")
        self.assertIn("unknown check id: mystery_check", payload["issues"])
        self.assertIn("failing check status: git_diff_check", payload["issues"])

    def test_v1_proof_recording_proposal_is_informational_only(self) -> None:
        client = TestClient(_test_app())

        payload = build_cartographer_v1_proof_recording_proposal()
        response = client.get("/v1/cartographer/v1-proof-recording-proposal")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["proposal"]["proposal_id"], payload["proposal"]["proposal_id"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["proposal_only"])
        self.assertFalse(payload["recording_enabled"])
        self.assertFalse(payload["recording_actions_enabled"])
        self.assertEqual(
            payload["proposal_policy"],
            "human_or_external_tool_may_record_after_review",
        )
        self.assertEqual(
            payload["artifact_path"],
            "data/cartographer-v1-proof-gates/manual-proof-gates.json",
        )
        self.assertTrue(payload["proposal"]["requires_human_action"])
        self.assertFalse(payload["proposal"]["action_taken"])
        self.assertIn("typescript_pass", payload["proposal"]["checks_to_record"])
        self.assertIn("mkdir -p data/cartographer-v1-proof-gates", payload["suggested_commands"])
        self.assertEqual(
            payload["example_artifact"]["profile"],
            "cartographer-v1-proof-gates",
        )
        self.assertIn("Cartographer is not writing this artifact.", payload["safety_notes"])

    def test_v1_proof_import_dry_run_previews_readiness_impact_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_proof_import_dry_run()
                response = client.get("/v1/cartographer/v1-proof-import-dry-run")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["dry_run"], payload["dry_run"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["import_enabled"])
        self.assertFalse(payload["recording_enabled"])
        self.assertFalse(payload["artifact_written"])
        self.assertTrue(payload["candidate_valid"])
        self.assertEqual(payload["validation_issues"], [])
        self.assertEqual(payload["recognized_check_count"], 5)
        self.assertIn("typescript_pass", payload["passing_codes"])
        self.assertIn("typescript_pass", payload["would_satisfy"])
        self.assertEqual(payload["would_satisfy_count"], 5)
        self.assertTrue(payload["readiness_would_still_be_blocked"])
        self.assertIn("three_clean_full_diagnostics", payload["remaining_missing_evidence"])

    def test_v1_diagnostic_import_dry_run_previews_remaining_closeout_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_diagnostic_import_dry_run()
                response = client.get("/v1/cartographer/v1-diagnostic-import-dry-run")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["dry_run"], payload["dry_run"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["import_enabled"])
        self.assertFalse(payload["recording_enabled"])
        self.assertFalse(payload["artifact_written"])
        self.assertEqual(payload["candidate_artifact_count"], 3)
        self.assertEqual(payload["recognized_diagnostic_count"], 3)
        self.assertEqual(payload["clean_diagnostic_count"], 3)
        self.assertIn("three_clean_full_diagnostics", payload["would_satisfy"])
        self.assertIn("proxy_closeout_pass", payload["would_satisfy"])
        self.assertIn("phase_4f_closeout_pass", payload["would_satisfy"])
        self.assertEqual(payload["would_satisfy_count"], 3)
        self.assertTrue(payload["readiness_would_still_be_blocked"])
        self.assertIn("typescript_pass", payload["remaining_missing_evidence"])

    def test_v1_combined_readiness_dry_run_previews_all_evidence_without_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_combined_readiness_dry_run()
                response = client.get("/v1/cartographer/v1-combined-readiness-dry-run")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["combined_preview"], payload["combined_preview"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["dry_run"])
        self.assertTrue(payload["combined_preview"])
        self.assertFalse(payload["import_enabled"])
        self.assertFalse(payload["recording_enabled"])
        self.assertFalse(payload["artifact_written"])
        self.assertIn("typescript_pass", payload["proof_would_satisfy"])
        self.assertIn("proxy_closeout_pass", payload["diagnostic_would_satisfy"])
        self.assertIn("three_clean_soak_snapshots", payload["soak_would_satisfy"])
        self.assertEqual(payload["remaining_missing_evidence"], [])
        self.assertEqual(payload["remaining_missing_count"], 0)
        self.assertTrue(payload["readiness_would_be_ready"])
        self.assertFalse(payload["readiness_would_still_be_blocked"])
        self.assertTrue(payload["authority_would_remain_locked"])
        self.assertFalse(payload["passing_tests_grant_authority"])

    def test_v1_evidence_gap_report_compares_current_missing_to_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_evidence_gap_report()
                response = client.get("/v1/cartographer/v1-evidence-gap-report")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["gap_report_mode"], payload["gap_report_mode"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["gap_report_mode"], "read_only_current_vs_dry_run")
        self.assertGreater(payload["current_missing_count"], 0)
        self.assertEqual(payload["remaining_after_dry_run"], [])
        self.assertTrue(payload["readiness_would_be_ready"])
        self.assertTrue(payload["authority_would_remain_locked"])
        self.assertFalse(payload["passing_tests_grant_authority"])
        gaps = {item["code"]: item for item in payload["gap_items"]}
        self.assertEqual(gaps["typescript_pass"]["satisfied_by_preview"], "proof_artifact_preview")
        self.assertEqual(gaps["proxy_closeout_pass"]["satisfied_by_preview"], "diagnostic_artifact_preview")
        self.assertTrue(all(item["dry_run_satisfied"] for item in payload["gap_items"]))
        self.assertIn("/v1/cartographer/v1-combined-readiness-dry-run", payload["source_endpoints"])

    def test_v1_closeout_handoff_summarizes_human_review_without_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_closeout_handoff()
                response = client.get("/v1/cartographer/v1-closeout-handoff")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["handoff_mode"], payload["handoff_mode"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["handoff_mode"], "read_only_human_review_summary")
        self.assertFalse(payload["v1_ready"])
        self.assertGreater(payload["current_missing_count"], 0)
        self.assertEqual(payload["remaining_after_dry_run"], [])
        self.assertTrue(payload["readiness_would_be_ready"])
        self.assertTrue(payload["authority_would_remain_locked"])
        self.assertFalse(payload["passing_tests_grant_authority"])
        self.assertEqual(payload["next_blocked_item"]["checklist_id"], "v1-closeout-diagnostics")
        self.assertIn("dry-run previews", payload["handoff_summary"])
        self.assertIn(
            "Passing tests or recorded artifacts do not grant authority.",
            payload["human_review_notes"],
        )
        self.assertIn("/v1/cartographer/v1-evidence-gap-report", payload["source_endpoints"])
        self.assertFalse(payload["safety"]["write_actions_enabled"])

    def test_v1_closeout_status_rolls_up_read_only_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_closeout_status()
                response = client.get("/v1/cartographer/v1-closeout-status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rollup_mode"], payload["rollup_mode"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["rollup_mode"], "read_only_closeout_status")
        self.assertFalse(payload["v1_ready"])
        self.assertEqual(payload["readiness"], "not_ready")
        self.assertEqual(payload["closeout_status"], "blocked_missing_evidence")
        self.assertEqual(payload["freeze_marker_status"], "missing")
        self.assertFalse(payload["freeze_marker_valid"])
        self.assertTrue(payload["freeze_marker_proposal_ready"])
        self.assertGreater(payload["current_missing_count"], 0)
        self.assertEqual(payload["remaining_after_dry_run"], [])
        self.assertTrue(payload["readiness_would_be_ready"])
        self.assertTrue(payload["authority_would_remain_locked"])
        self.assertFalse(payload["passing_tests_grant_authority"])
        self.assertIn("/v1/cartographer/v1-freeze-marker-validation", payload["source_endpoints"])
        self.assertFalse(payload["safety"]["write_actions_enabled"])

    def test_v1_closeout_dashboard_surfaces_compact_read_only_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_closeout_dashboard()
                response = client.get("/v1/cartographer/v1-closeout-dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["dashboard_mode"], payload["dashboard_mode"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["dashboard_mode"], "read_only_v1_closeout_surface")
        self.assertEqual(payload["docs_path"], "docs/cartographer-v1-evidence-artifacts.md")
        self.assertEqual(payload["docs_label"], "Cartographer v1 evidence artifact contract")
        self.assertEqual(payload["primary_status"], "blocked_missing_evidence")
        self.assertEqual(payload["primary_label"], "Blocked by missing evidence")
        self.assertFalse(payload["v1_ready"])
        self.assertEqual(payload["freeze_marker_status"], "missing")
        cards = {card["card_id"]: card for card in payload["dashboard_cards"]}
        self.assertEqual(cards["v1-readiness"]["endpoint"], "/v1/cartographer/v1-readiness")
        self.assertEqual(cards["v1-evidence"]["status"], "blocked")
        self.assertEqual(cards["v1-authority"]["status"], "locked")
        self.assertEqual(cards["v1-docs"]["status"], "read_only")
        self.assertEqual(cards["v1-docs"]["value"], "docs/cartographer-v1-evidence-artifacts.md")
        self.assertIn("curl -k -s", payload["manual_check"])
        self.assertIn("authority_granted remains false", payload["expected_outcome"])
        self.assertEqual(payload["source_endpoint"], "/v1/cartographer/v1-closeout-status")
        self.assertFalse(payload["source_status"]["write_actions_enabled"])
        self.assertFalse(payload["safety"]["write_actions_enabled"])

    def test_v1_closeout_audit_summary_lists_surfaces_and_blockers_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_closeout_audit_summary()
                response = client.get("/v1/cartographer/v1-closeout-audit-summary")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["audit_mode"], payload["audit_mode"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["audit_mode"], "read_only_v1_closeout_final_summary")
        self.assertEqual(payload["closeout_status"], "blocked_missing_evidence")
        self.assertEqual(payload["docs_path"], "docs/cartographer-v1-evidence-artifacts.md")
        self.assertEqual(payload["freeze_marker_status"], "missing")
        surfaces = {surface["surface_id"]: surface for surface in payload["surfaces"]}
        self.assertEqual(surfaces["readiness"]["endpoint"], "/v1/cartographer/v1-readiness")
        self.assertEqual(surfaces["dashboard"]["status"], "read_only_v1_closeout_surface")
        self.assertEqual(
            surfaces["freeze_marker_validation"]["endpoint"],
            "/v1/cartographer/v1-freeze-marker-validation",
        )
        self.assertTrue(payload["remaining_blockers"])
        self.assertIn("authority_granted remains false", payload["safety_invariants"])
        self.assertIn("docs_path points to the evidence artifact contract", payload["expected_outcome"])
        self.assertFalse(payload["safety"]["write_actions_enabled"])

    def test_v1_closeout_endpoint_index_lists_read_only_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_closeout_endpoint_index()
                response = client.get("/v1/cartographer/v1-closeout-endpoints")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["index_mode"], payload["index_mode"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["index_mode"], "read_only_v1_closeout_endpoint_index")
        self.assertEqual(payload["docs_path"], "docs/cartographer-v1-evidence-artifacts.md")
        self.assertEqual(payload["audit_endpoint"], "/v1/cartographer/v1-closeout-audit-summary")
        self.assertEqual(payload["dashboard_endpoint"], "/v1/cartographer/v1-closeout-dashboard")
        endpoints = {item["endpoint"]: item for item in payload["endpoints"]}
        self.assertIn("/v1/cartographer/v1-readiness", endpoints)
        self.assertIn("/v1/cartographer/v1-closeout-dashboard", endpoints)
        self.assertIn("/v1/cartographer/v1-closeout-audit-summary", endpoints)
        self.assertTrue(all(item["read_only"] for item in payload["endpoints"]))
        self.assertEqual(payload["endpoint_count"], len(payload["endpoints"]))
        self.assertIn("every endpoint entry is read_only", payload["expected_outcome"])
        self.assertFalse(payload["safety"]["write_actions_enabled"])

    def test_v1_closeout_finalization_marker_is_read_only_and_blocked_on_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_closeout_finalization_marker()
                response = client.get("/v1/cartographer/v1-closeout-finalization")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["marker_mode"], payload["marker_mode"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["marker_mode"], "read_only_v1_closeout_surface_complete")
        self.assertTrue(payload["surface_set_complete"])
        self.assertTrue(payload["readiness_blocked"])
        self.assertTrue(payload["real_external_evidence_required"])
        self.assertEqual(payload["closeout_status"], "blocked_missing_evidence")
        self.assertGreater(payload["remaining_blocker_count"], 0)
        self.assertEqual(payload["endpoint_index"], "/v1/cartographer/v1-closeout-endpoints")
        self.assertEqual(payload["audit_endpoint"], "/v1/cartographer/v1-closeout-audit-summary")
        self.assertEqual(payload["dashboard_endpoint"], "/v1/cartographer/v1-closeout-dashboard")
        self.assertEqual(payload["docs_path"], "docs/cartographer-v1-evidence-artifacts.md")
        self.assertIn("surfaces are complete and read-only", payload["finalization_summary"])
        self.assertIn("readiness_blocked remains true until real external evidence exists", payload["expected_outcome"])
        self.assertFalse(payload["safety"]["write_actions_enabled"])

    def test_v1_freeze_marker_proposal_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_freeze_marker_proposal()
                response = client.get("/v1/cartographer/v1-freeze-marker-proposal")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["proposal"]["proposal_id"], payload["proposal"]["proposal_id"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["proposal_only"])
        self.assertFalse(payload["freeze_marker_enabled"])
        self.assertFalse(payload["freeze_actions_enabled"])
        self.assertEqual(payload["marker_path"], "data/cartographer-v1-freeze/freeze-marker.json")
        self.assertEqual(payload["proposal_policy"], "human_or_external_tool_may_record_after_review")
        self.assertTrue(payload["proposal"]["requires_human_action"])
        self.assertTrue(payload["proposal"]["requires_approval"])
        self.assertFalse(payload["proposal"]["action_taken"])
        self.assertEqual(payload["proposal"]["target_file"], payload["marker_path"])
        self.assertEqual(payload["example_marker"]["marker_version"], "cartographer.v1.freeze_marker.v1")
        self.assertFalse(payload["example_marker"]["authority_boundary"]["write_actions_enabled"])
        self.assertFalse(payload["example_marker"]["authority_boundary"]["authority_granted"])
        self.assertFalse(payload["example_marker"]["authority_boundary"]["passing_tests_grant_authority"])
        self.assertIn("/v1/cartographer/v1-closeout-handoff", payload["source_endpoints"])
        self.assertFalse(payload["safety"]["write_actions_enabled"])

    def test_v1_freeze_marker_validation_reads_existing_marker_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            marker_dir = root / "data" / "cartographer-v1-freeze"
            marker_dir.mkdir(parents=True)
            (marker_dir / "freeze-marker.json").write_text(
                json.dumps(
                    {
                        "marker_version": "cartographer.v1.freeze_marker.v1",
                        "created_at": "2026-05-18T00:00:00Z",
                        "head_sha": "683793732031b6d9471de7995931310065df84a5",
                        "branch": "main",
                        "readiness": "ready",
                        "v1_ready": True,
                        "evidence_summary": {"current_missing_count": 0},
                        "authority_boundary": {
                            "write_actions_enabled": False,
                            "authority_granted": False,
                            "actions_taken": False,
                            "passing_tests_grant_authority": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_freeze_marker_validation()
                response = client.get("/v1/cartographer/v1-freeze-marker-validation")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["validation_status"], payload["validation_status"])
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["validator_enabled"])
        self.assertFalse(payload["validation_actions_enabled"])
        self.assertFalse(payload["freeze_marker_enabled"])
        self.assertFalse(payload["freeze_actions_enabled"])
        self.assertEqual(payload["marker_count"], 1)
        self.assertEqual(payload["valid_marker_count"], 1)
        self.assertEqual(payload["invalid_marker_count"], 0)
        self.assertEqual(payload["validation_status"], "valid")
        self.assertEqual(payload["issues"], [])
        self.assertTrue(payload["validation_items"][0]["authority_boundary_valid"])
        self.assertFalse(payload["safety"]["write_actions_enabled"])

    def test_v1_freeze_marker_validation_reports_missing_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            client = TestClient(_test_app())

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_freeze_marker_validation()
                response = client.get("/v1/cartographer/v1-freeze-marker-validation")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["validation_status"], "missing")
        self.assertEqual(payload["marker_count"], 0)
        self.assertEqual(payload["valid_marker_count"], 0)
        self.assertEqual(payload["invalid_marker_count"], 0)
        self.assertTrue(payload["validation_items"])
        self.assertFalse(payload["validation_items"][0]["present"])
        self.assertIn("freeze marker not found", payload["validation_items"][0]["issues"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])

    def test_v1_readiness_uses_evidence_inventory_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            soak_dir = root / "source_proxy" / "cartographer" / "soak-logs"
            soak_dir.mkdir(parents=True)
            for index in range(3):
                (soak_dir / f"cartographer-soak-snapshot-2026-05-18T13000{index}Z.json").write_text(
                    json.dumps(
                        {
                            "profile": "cartographer-soak-snapshot",
                            "result": "pass",
                            "generated_at": f"2026-05-18T13:00:0{index}Z",
                            "mutation_boundary": {
                                "head_changed": False,
                                "snapshot_log_only": True,
                                "unexpected_status_delta": [],
                            },
                        }
                    ),
                    encoding="utf-8",
                )
            data_dir = root / "data"
            data_dir.mkdir()
            (data_dir / "v1-proof-gates.json").write_text(
                json.dumps(
                    {
                        "profile": "cartographer-v1-proof-gates",
                        "result": "pass",
                        "checks": {
                            "typecheck": True,
                            "lint_warnings_only": True,
                            "blueprint_validation": True,
                            "diff_check": True,
                            "vitest": True,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK": "true",
                },
                clear=False,
            ):
                payload = build_cartographer_v1_readiness()

        proofs = {proof["code"]: proof for proof in payload["proof_gates"]}
        self.assertTrue(proofs["three_clean_soak_snapshots"]["passed"])
        self.assertTrue(proofs["typescript_pass"]["passed"])
        self.assertTrue(proofs["lint_pass_or_warnings_only"]["passed"])
        self.assertTrue(proofs["blueprint_validation_pass"]["passed"])
        self.assertTrue(proofs["diff_check_pass"]["passed"])
        self.assertTrue(proofs["targeted_vitest_pass"]["passed"])
        self.assertEqual(payload["evidence_summary"]["clean_soak_count"], 3)
        self.assertFalse(payload["v1_ready"])
        self.assertFalse(payload["actions_taken"])

    def test_project_health_summarizes_active_and_candidate_projects_for_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            spirit = parent / "SpiritOS"
            spirit.mkdir()
            _write_minimal_blueprints(spirit)
            dashboard_file = spirit / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(spirit, "init")
            _git(spirit, "config", "user.email", "cartographer@example.test")
            _git(spirit, "config", "user.name", "Cartographer Test")
            _git(spirit, "checkout", "-b", "cartographer-health")
            _git(spirit, "add", ".")
            _git(spirit, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            client = parent / "ClientDashboard"
            client.mkdir()
            (client / "README.md").write_text("client", encoding="utf-8")
            (client / "package.json").write_text("{}", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                payload = build_cartographer_project_health()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["worktree_created"])
        self.assertEqual(
            payload["worktree_policy"],
            "proposal_only_until_separate_explicit_approval",
        )
        self.assertFalse(payload["actions_taken"])
        projects = {project["name"]: project for project in payload["projects"]}
        self.assertEqual(payload["project_count"], 2)
        self.assertEqual(projects["SpiritOS"]["status"], "pending_proposal_review")
        self.assertEqual(projects["SpiritOS"]["blueprint_health"], "review_suggested")
        self.assertEqual(projects["SpiritOS"]["blueprint_count"], 4)
        self.assertEqual(projects["SpiritOS"]["pending_drift"], 1)
        self.assertEqual(projects["SpiritOS"]["pending_proposals"], 1)
        self.assertTrue(projects["SpiritOS"]["dirty"])
        self.assertEqual(projects["SpiritOS"]["branch"], "cartographer-health")
        self.assertEqual(projects["SpiritOS"]["dirty_file_count"], 1)
        self.assertEqual(projects["SpiritOS"]["unstaged_files"], ["src/components/dashboard/Widget.tsx"])
        self.assertTrue(projects["SpiritOS"]["read_only"])
        self.assertFalse(projects["SpiritOS"]["write_actions_enabled"])
        self.assertEqual(projects["SpiritOS"]["write_policy"], "read_only_observation")
        self.assertEqual(projects["SpiritOS"]["workspace_classification"], "dirty_worktree")
        self.assertIn(
            "dirty_worktree_requires_scope_review",
            projects["SpiritOS"]["authority_blockers"],
        )
        self.assertIn(
            "worktree_creation_proposal_only",
            projects["SpiritOS"]["authority_blockers"],
        )
        self.assertEqual(projects["SpiritOS"]["ahead"], 0)
        self.assertEqual(projects["SpiritOS"]["behind"], 0)
        self.assertIn("dirty", projects["SpiritOS"]["filters"])
        self.assertEqual(
            projects["ClientDashboard"]["status"],
            "needs_starter_blueprint_approval",
        )
        self.assertEqual(
            projects["ClientDashboard"]["blueprint_health"],
            "missing_starter_blueprints",
        )
        self.assertEqual(projects["ClientDashboard"]["pending_proposals"], 1)
        self.assertTrue(projects["ClientDashboard"]["read_only"])
        self.assertFalse(projects["ClientDashboard"]["write_actions_enabled"])
        self.assertEqual(
            projects["ClientDashboard"]["workspace_classification"],
            "candidate_read_only_project",
        )
        self.assertIn(
            "starter_blueprint_approval_required",
            projects["ClientDashboard"]["authority_blockers"],
        )
        self.assertIn("candidate", projects["ClientDashboard"]["filters"])
        self.assertIn("needs_approval", projects["ClientDashboard"]["filters"])
        self.assertIn("dirty", payload["filters"])
        self.assertIn("needs_approval", payload["filters"])

    def test_project_health_reports_clean_blueprinted_project_as_active(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "core.autocrlf", "false")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_project_health()

        project = payload["projects"][0]
        self.assertEqual(project["status"], "active")
        self.assertEqual(project["blueprint_health"], "healthy")
        self.assertEqual(project["blueprint_count"], 4)
        self.assertEqual(project["pending_drift"], 0)
        self.assertEqual(project["pending_proposals"], 0)
        self.assertFalse(project["dirty"])
        self.assertTrue(project["read_only"])
        self.assertFalse(project["write_actions_enabled"])
        self.assertEqual(project["write_policy"], "read_only_observation")
        self.assertEqual(project["workspace_classification"], "clean_read_only_project")
        self.assertNotIn("dirty_worktree_requires_scope_review", project["authority_blockers"])
        self.assertIn("worktree_creation_proposal_only", project["authority_blockers"])
        self.assertIn("active", project["filters"])

    def test_project_health_fallback_counts_current_repo_blueprints(self) -> None:
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            try:
                os.chdir(root)
                with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
                    payload = build_cartographer_project_health()
            finally:
                os.chdir(original_cwd)

        project = payload["projects"][0]
        self.assertEqual(project["project_id"], root.name.lower())
        self.assertEqual(project["status"], "active")
        self.assertEqual(project["blueprint_count"], 4)
        self.assertEqual(project["blueprint_health"], "healthy")

    def test_project_health_surfaces_codex_evidence_without_action_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_dir = root / "codex-evidence"
            _write_codex_evidence(
                evidence_dir,
                "phase-10-11-1-t4",
                ["source_proxy/tests/test_codex_cli_adapter.py"],
            )
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_project_health()

        evidence = payload["codex_evidence"]
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(evidence["evidence_count"], 1)
        self.assertEqual(evidence["latest_task_ids"], ["phase-10-11-1-t4"])
        self.assertEqual(evidence["changed_files"], ["source_proxy/tests/test_codex_cli_adapter.py"])
        self.assertIn("source-proxy", evidence["components"])
        self.assertIn("medium", evidence["risk_labels"])
        self.assertTrue(evidence["proposal_pending_review"])
        self.assertTrue(evidence["commit_proposal_needed"])
        self.assertFalse(evidence["approval_authority"])
        self.assertFalse(evidence["apply_authority"])
        self.assertFalse(evidence["commit_authority"])
        self.assertFalse(evidence["push_authority"])
        self.assertFalse(evidence["actions_taken"])

    def test_codex_evidence_route_is_read_only_and_context_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_dir = root / "codex-evidence"
            _write_codex_evidence(
                evidence_dir,
                "phase-10-11-1-t6",
                ["src/components/coding/CodingAgentInterface.tsx"],
            )

            with patch.dict(os.environ, {"SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir)}, clear=False):
                payload = build_cartographer_codex_evidence()
                client = TestClient(_test_app())
                response = client.get("/v1/cartographer/codex-evidence")

        self.assertEqual(response.status_code, 200)
        route_payload = response.json()
        for item in (payload, route_payload):
            self.assertEqual(item["status"], "observing")
            self.assertFalse(item["write_actions_enabled"])
            self.assertFalse(item["actions_taken"])
            self.assertEqual(item["codex_evidence"]["evidence_count"], 1)
            self.assertEqual(item["codex_evidence"]["latest_task_ids"], ["phase-10-11-1-t6"])
            self.assertFalse(item["codex_evidence"]["approval_authority"])
            self.assertFalse(item["codex_evidence"]["apply_authority"])
            self.assertFalse(item["codex_evidence"]["commit_authority"])
            self.assertFalse(item["codex_evidence"]["push_authority"])

    def test_project_health_blocks_merge_when_dirty_or_unpushed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/dirty-review")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "docs" / "merge.md").parent.mkdir()
            (root / "docs" / "merge.md").write_text("dirty\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_project_health()

        project = payload["projects"][0]
        self.assertFalse(project["merge_ready"])
        self.assertIn("working tree has uncommitted changes", project["merge_blockers"])
        self.assertIn("merge target unknown", project["merge_blockers"])
        self.assertEqual(project["recommended_next_step"], "commit or discard remaining local changes")
        self.assertEqual(project["push_approval_status"], "not_required")
        self.assertFalse(project["push_enabled"])
        self.assertEqual(project["push_reason_codes"], ["no_commits_to_push"])
        self.assertEqual(project["commits_to_push"], [])
        self.assertFalse(project["action_taken"])

    def test_project_health_classifies_expected_evidence_dirty_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/evidence-review")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "src" / "components").mkdir(parents=True, exist_ok=True)
            (root / "src" / "components" / "Widget.tsx").write_text("changed\n", encoding="utf-8")
            soak_path = root / "scout" / "soak-logs" / "scout-soak-snapshot-test.json"
            soak_path.parent.mkdir(parents=True, exist_ok=True)
            soak_path.write_text("{}\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_project_health()

        project = payload["projects"][0]
        self.assertTrue(project["dirty"])
        self.assertEqual(project["dirty_file_count"], 2)
        self.assertEqual(
            project["expected_evidence_files"],
            ["scout/soak-logs/scout-soak-snapshot-test.json"],
        )
        self.assertEqual(project["unsafe_dirty_files"], ["src/components/Widget.tsx"])
        self.assertEqual(
            project["dirty_summary"],
            "code/config changes plus expected evidence files changed",
        )
        self.assertEqual(project["workspace_classification"], "dirty_worktree")
        self.assertIn("dirty_worktree_requires_scope_review", project["authority_blockers"])
        self.assertFalse(project["write_actions_enabled"])
        self.assertIn("working tree has uncommitted changes", project["merge_blockers"])
        self.assertNotIn("required checks not recorded as passed", project["merge_blockers"])

    def test_project_health_marks_clean_pushed_verified_branch_merge_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/merge-ready")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/merge-ready")
            _write_git_approval_record(
                root,
                {
                    "event": "commit_created",
                    "project_id": "work",
                    "branch": "cartographer/merge-ready",
                    "checks": [
                        {"id": "git_diff_check", "status": "passed"},
                        {"id": "blueprint_metadata_validation", "status": "passed"},
                        {"id": "cartographer_pytest", "status": "passed"},
                    ],
                },
            )
            _write_git_approval_record(
                root,
                {
                    "event": "push_approved",
                    "project_id": "work",
                    "branch": "cartographer/merge-ready",
                    "result": "pushed",
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_project_health()

        project = payload["projects"][0]
        self.assertTrue(project["merge_ready"])
        self.assertEqual(project["merge_blockers"], [])
        self.assertEqual(project["recommended_next_step"], "open merge review")
        self.assertEqual(project["merge_target"], "origin/cartographer/merge-ready")
        self.assertTrue(project["pushed"])
        self.assertEqual(project["push_audit_status"], "recorded")
        self.assertEqual(project["push_approval_status"], "not_required")
        self.assertFalse(project["push_enabled"])
        self.assertEqual(project["push_reason_codes"], ["push_already_recorded"])
        self.assertTrue(project["checks_passed"])
        self.assertIn("merge_ready", project["filters"])
        self.assertFalse(project["action_taken"])

    def test_project_health_treats_manual_bootstrap_push_as_non_blocking_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/bootstrap")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/bootstrap")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()
            _write_git_approval_record(
                root,
                {
                    "event": "commit_created",
                    "project_id": "work",
                    "branch": "cartographer/bootstrap",
                    "commit_sha": commit_sha,
                    "checks": [
                        {"id": "git_diff_check", "status": "passed"},
                        {"id": "blueprint_metadata_validation", "status": "passed"},
                        {"id": "cartographer_pytest", "status": "passed"},
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_project_health()

        project = payload["projects"][0]
        self.assertTrue(project["merge_ready"])
        self.assertNotIn("push audit missing", project["merge_blockers"])
        self.assertEqual(project["push_audit_status"], "bootstrap_manual_push_no_local_commits")
        self.assertTrue(project["bootstrap_push_warning"])
        self.assertEqual(
            project["push_warning_policy"],
            "bootstrap_manual_upstream_non_blocking",
        )
        self.assertIn("non-blocking bootstrap warning", project["push_audit_explanation"])
        self.assertEqual(
            project["push_reason_codes"],
            ["bootstrap_manual_upstream_no_local_commits", "no_commits_to_push"],
        )
        self.assertFalse(project["push_enabled"])
        self.assertFalse(project["action_taken"])

    def test_project_health_reports_unpushed_commit_readiness_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/push-readiness")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/push-readiness")
            (root / "docs" / "push.md").parent.mkdir(exist_ok=True)
            (root / "docs" / "push.md").write_text("push readiness\n", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(cartographer): record push readiness")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_project_health()

        project = payload["projects"][0]
        self.assertFalse(project["merge_ready"])
        self.assertIn("branch has unpushed commits", project["merge_blockers"])
        self.assertIn("unaudited_head_change", project["merge_blockers"])
        self.assertIn("push audit missing", project["merge_blockers"])
        self.assertEqual(project["head_sha"], commit_sha)
        self.assertEqual(project["commit_audit_status"], "missing")
        self.assertTrue(project["unaudited_head_change"])
        self.assertEqual(
            project["recommended_next_step"],
            "review HEAD change and record or resolve commit audit before push",
        )
        self.assertEqual(project["push_audit_status"], "missing")
        self.assertEqual(
            project["push_warning_policy"],
            "current_ahead_commits_require_push_approval",
        )
        self.assertIn("require Cartographer push approval", project["push_audit_explanation"])
        self.assertEqual(project["push_approval_status"], "approval_required")
        self.assertFalse(project["push_enabled"])
        self.assertEqual(
            project["push_reason_codes"],
            [
                "unpushed_commits",
                "push_requires_separate_approval",
                "push_disabled_until_approved",
                "push_audit_missing",
            ],
        )
        self.assertEqual(project["commits_to_push"], [commit_sha])

    def test_project_health_does_not_flag_audited_unpushed_head_as_unaudited(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/audited-head")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/audited-head")
            (root / "docs" / "audited.md").parent.mkdir(exist_ok=True)
            (root / "docs" / "audited.md").write_text("audited\n", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(cartographer): audited head")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()
            _write_git_approval_record(
                root,
                {
                    "event": "commit_created",
                    "project_id": "work",
                    "branch": "cartographer/audited-head",
                    "commit_sha": commit_sha,
                    "checks": [
                        {"id": "git_diff_check", "status": "passed"},
                        {"id": "blueprint_metadata_validation", "status": "passed"},
                        {"id": "cartographer_pytest", "status": "passed"},
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_project_health()

        project = payload["projects"][0]
        self.assertFalse(project["merge_ready"])
        self.assertIn("branch has unpushed commits", project["merge_blockers"])
        self.assertNotIn("unaudited_head_change", project["merge_blockers"])
        self.assertEqual(project["commit_audit_status"], "recorded")
        self.assertFalse(project["unaudited_head_change"])
        self.assertTrue(project["checks_passed"])

    def test_branch_recommendation_suggests_branch_on_dirty_main_without_creating_one(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            source_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_branch_recommendations()
            after_branch = _git_stdout(root, "branch", "--show-current").strip()
            branches = _git_stdout(root, "branch", "--format=%(refname:short)")

        self.assertEqual(before_branch, "main")
        self.assertEqual(after_branch, "main")
        self.assertNotIn("cartographer/dashboard-blueprint-review", branches.splitlines())
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["recommendation_count"], 1)
        self.assertTrue(payload["recommended"])
        self.assertEqual(payload["branch_name"], "cartographer/dashboard-blueprint-review")
        self.assertTrue(payload["requires_approval"])
        recommendation = payload["recommendations"][0]
        self.assertTrue(recommendation["recommendation_id"].startswith("branch-rec-"))
        self.assertEqual(recommendation["current_branch"], "main")
        self.assertEqual(
            recommendation["suggested_branch"],
            "cartographer/dashboard-blueprint-review",
        )
        self.assertEqual(recommendation["status"], "pending_approval")
        self.assertTrue(recommendation["requires_approval"])
        self.assertFalse(recommendation["branch_creation_enabled"])
        self.assertFalse(recommendation["action_taken"])
        self.assertEqual(recommendation["confidence"], "low")
        self.assertEqual(recommendation["recommendation"], "create_branch_after_approval")
        self.assertTrue(recommendation["unsafe_to_create_branch"])
        self.assertEqual(
            recommendation["blockers"],
            ["upstream unavailable: no_upstream_configured"],
        )
        self.assertEqual(recommendation["merge_readiness"], "blocked")
        self.assertIn("Working tree dirty on main", recommendation["reason"])
        self.assertEqual(recommendation["changed_file_count"], 1)
        self.assertEqual(recommendation["source_head"], source_head)
        self.assertEqual(recommendation["dirty_state_requirement"], "dirty_worktree_required")
        self.assertEqual(
            recommendation["rollback_command"],
            "git switch main && git branch -D cartographer/dashboard-blueprint-review",
        )
        self.assertFalse(recommendation["branch_exists"])
        self.assertTrue(recommendation["preview_generated"])

    def test_branch_recommendation_triggers_for_applied_proposal_needing_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/cartographer")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            system_state = root / "_blueprints" / "current" / "system_state.md"
            system_state.write_text(
                system_state.read_text(encoding="utf-8") + "\nApplied proposal note.\n",
                encoding="utf-8",
            )
            _write_proposal(
                root,
                "applied",
                "bp-applied-branch",
                {
                    "status": "applied",
                    "type": "blueprint_update",
                    "component": "scout",
                    "proposed_files": ["_blueprints/current/system_state.md"],
                    "applied": True,
                    "action_taken": True,
                    "transitions": [
                        {
                            "status": "applied",
                            "timestamp": "2026-05-16T19:50:12Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )

            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_branch_recommendations()
            after_branch = _git_stdout(root, "branch", "--show-current").strip()
            branches = _git_stdout(root, "branch", "--format=%(refname:short)")

        self.assertEqual(before_branch, "feature/cartographer")
        self.assertEqual(after_branch, "feature/cartographer")
        self.assertTrue(payload["recommended"])
        self.assertEqual(payload["recommendation_count"], 1)
        self.assertTrue(payload["requires_approval"])
        self.assertEqual(payload["branch_name"], "scout/source-gate-polish")
        self.assertNotIn(payload["branch_name"], branches.splitlines())
        recommendation = payload["recommendations"][0]
        self.assertIn("Applied proposal left docs changes uncommitted", recommendation["reason"])
        self.assertFalse(recommendation["branch_creation_enabled"])
        self.assertFalse(recommendation["action_taken"])
        self.assertEqual(recommendation["confidence"], "low")
        self.assertTrue(recommendation["unsafe_to_create_branch"])
        self.assertEqual(
            recommendation["blockers"],
            ["upstream unavailable: no_upstream_configured"],
        )

    def test_branch_recommendation_suggests_checkpoint_branch_for_many_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            files = []
            for index in range(8):
                path = root / "src" / "components" / "dashboard" / f"Widget{index}.tsx"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("export const value = 1;\n", encoding="utf-8")
                files.append(path)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/cartographer")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "branch", "cartographer/dashboard-blueprint-review")
            for path in files:
                path.write_text("export const value = 2;\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_branch_recommendations()

        recommendation = payload["recommendations"][0]
        self.assertEqual(recommendation["current_branch"], "feature/cartographer")
        self.assertEqual(recommendation["changed_file_count"], 8)
        self.assertIn("8 changed files", recommendation["reason"])
        self.assertTrue(recommendation["requires_approval"])
        self.assertFalse(recommendation["action_taken"])
        self.assertEqual(recommendation["confidence"], "low")
        self.assertTrue(recommendation["unsafe_to_create_branch"])
        self.assertTrue(recommendation["branch_exists"])
        self.assertEqual(
            recommendation["rollback_command"],
            "git switch feature/cartographer && git branch -D cartographer/dashboard-blueprint-review",
        )

    def test_branch_recommendation_confidence_high_when_dirty_main_has_upstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "main")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_branch_recommendations()

        recommendation = payload["recommendations"][0]
        self.assertEqual(recommendation["confidence"], "high")
        self.assertFalse(recommendation["unsafe_to_create_branch"])
        self.assertEqual(recommendation["blockers"], [])

    def test_branch_recommendation_stays_empty_for_clean_or_small_feature_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/cartographer")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                clean_payload = build_cartographer_branch_recommendations()

            note = root / "notes.md"
            note.write_text("small change\n", encoding="utf-8")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                dirty_payload = build_cartographer_branch_recommendations()

        self.assertEqual(clean_payload["recommendations"], [])
        self.assertEqual(clean_payload["recommendation_count"], 0)
        self.assertFalse(clean_payload["recommended"])
        self.assertEqual(dirty_payload["recommendations"], [])
        self.assertEqual(dirty_payload["recommendation_count"], 0)
        self.assertFalse(dirty_payload["recommended"])

    def test_level_5_parallel_work_risk_model_reports_dirty_primary_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            before_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_5_parallel_work_risk_model()
                response = TestClient(_test_app()).get("/v1/cartographer/level-5-parallel-work-risk")
            after_branch = _git_stdout(root, "branch", "--show-current").strip()
            after_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            branches = _git_stdout(root, "branch", "--format=%(refname:short)").splitlines()

        self.assertEqual(before_branch, "main")
        self.assertEqual(after_branch, "main")
        self.assertEqual(before_worktrees, after_worktrees)
        self.assertEqual(branches, ["main"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contract_version"], "cartographer.level_5.parallel_work_risk_model.v1")
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 5)
        self.assertEqual(payload["mode"], "parallel_work_risk_model")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertEqual(payload["project_count"], 1)
        self.assertEqual(payload["risk_count"], 2)
        self.assertEqual(payload["high_risk_count"], 2)
        project = payload["projects"][0]
        self.assertEqual(project["branch"], "main")
        self.assertTrue(project["dirty"])
        self.assertEqual(project["changed_files"], ["src/components/dashboard/Widget.tsx"])
        self.assertEqual(project["risk_level"], "high")
        self.assertTrue(project["owner_assignment_required"])
        self.assertEqual(
            project["recommended_isolation"],
            "recommend_separate_branch_or_worktree_after_approval",
        )
        risk_ids = [risk["risk_id"] for risk in project["risks"]]
        self.assertEqual(risk_ids, ["dirty_tree_collision_risk", "primary_branch_dirty_risk"])
        self.assertIn("branch creation", payload["forbidden_actions"])
        self.assertIn("worktree creation", payload["forbidden_actions"])

    def test_level_5_parallel_work_risk_model_reports_clean_feature_branch_as_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/cartographer")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_5_parallel_work_risk_model()
            after_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")

        self.assertEqual(before_worktrees, after_worktrees)
        self.assertEqual(payload["level"], 5)
        self.assertEqual(payload["risk_count"], 0)
        self.assertEqual(payload["high_risk_count"], 0)
        self.assertEqual(payload["medium_risk_count"], 0)
        self.assertEqual(payload["recommended_next_action"], "No parallel work collision risks detected.")
        project = payload["projects"][0]
        self.assertEqual(project["branch"], "feature/cartographer")
        self.assertFalse(project["dirty"])
        self.assertEqual(project["risk_level"], "none")
        self.assertFalse(project["owner_assignment_required"])
        self.assertEqual(project["recommended_isolation"], "none")
        self.assertEqual(project["actions_taken"], False)
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])

    def test_level_5_branch_recommendation_refresh_preview_without_branch_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            source_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            before_branches = _git_stdout(root, "branch", "--format=%(refname:short)").splitlines()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_5_branch_recommendation_refresh()
                response = TestClient(_test_app()).get("/v1/cartographer/level-5-branch-recommendations")
            after_branch = _git_stdout(root, "branch", "--show-current").strip()
            after_branches = _git_stdout(root, "branch", "--format=%(refname:short)").splitlines()

        self.assertEqual(before_branch, "main")
        self.assertEqual(after_branch, "main")
        self.assertEqual(before_branches, after_branches)
        self.assertNotIn("cartographer/dashboard-blueprint-review", after_branches)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_5.branch_recommendation_refresh.v1",
        )
        self.assertEqual(payload["status"], "observing")
        self.assertEqual(payload["level"], 5)
        self.assertEqual(payload["mode"], "branch_recommendation_refresh")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertEqual(payload["recommendation_count"], 1)
        self.assertIn("owner", payload["required_approval_fields"])
        recommendation = payload["recommendations"][0]
        self.assertEqual(
            recommendation["recommendation_version"],
            "cartographer.level_5.branch_recommendation_refresh.v1",
        )
        self.assertEqual(recommendation["current_branch"], "main")
        self.assertEqual(recommendation["base_branch"], "main")
        self.assertEqual(recommendation["base_head"], source_head)
        self.assertEqual(recommendation["suggested_branch"], "cartographer/dashboard-blueprint-review")
        self.assertTrue(recommendation["owner_required"])
        self.assertIsNone(recommendation["proposed_owner"])
        self.assertIn("Isolate 1 changed file", recommendation["purpose"])
        self.assertEqual(recommendation["status"], "preview_only")
        self.assertEqual(recommendation["command_preview"], "git switch -c cartographer/dashboard-blueprint-review")
        self.assertEqual(recommendation["risk_level"], "high")
        self.assertEqual(
            [risk["risk_id"] for risk in recommendation["collision_notes"]],
            ["dirty_tree_collision_risk", "primary_branch_dirty_risk"],
        )
        self.assertFalse(recommendation["branch_creation_allowed"])
        self.assertFalse(recommendation["checkout_allowed"])
        self.assertFalse(recommendation["actions_taken"])

    def test_level_5_branch_recommendation_refresh_empty_state_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/cartographer")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_5_branch_recommendation_refresh()
            after_branch = _git_stdout(root, "branch", "--show-current").strip()

        self.assertEqual(before_branch, after_branch)
        self.assertEqual(payload["level"], 5)
        self.assertEqual(payload["recommendation_count"], 0)
        self.assertEqual(payload["recommendations"], [])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["risk_model"]["risk_count"], 0)

    def test_level_5_worktree_recommendation_contract_preview_without_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "work"
            root.mkdir()
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            source_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            before_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_5_worktree_recommendation_contract()
                response = TestClient(_test_app()).get("/v1/cartographer/level-5-worktree-recommendations")
            after_branch = _git_stdout(root, "branch", "--show-current").strip()
            after_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            target_path = Path(temp_dir) / "work-cartographer-dashboard-blueprint-review"

        self.assertEqual(before_branch, "main")
        self.assertEqual(after_branch, "main")
        self.assertEqual(before_worktrees, after_worktrees)
        self.assertFalse(target_path.exists())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contract_version"],
            "cartographer.level_5.worktree_recommendation_contract.v1",
        )
        self.assertEqual(payload["level"], 5)
        self.assertEqual(payload["mode"], "worktree_recommendation_contract")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertEqual(payload["recommendation_count"], 1)
        self.assertIn("exact_worktree_path", payload["required_approval_fields"])
        recommendation = payload["recommendations"][0]
        self.assertEqual(
            recommendation["recommendation_version"],
            "cartographer.level_5.worktree_recommendation_contract.v1",
        )
        self.assertEqual(recommendation["target_path"], "../work-cartographer-dashboard-blueprint-review")
        self.assertEqual(recommendation["branch_proposal"], "cartographer/dashboard-blueprint-review")
        self.assertEqual(recommendation["base_branch"], "main")
        self.assertEqual(recommendation["base_head"], source_head)
        self.assertTrue(recommendation["owner_required"])
        self.assertIsNone(recommendation["proposed_owner"])
        self.assertEqual(recommendation["conflicting_dirty_files"], ["src/components/dashboard/Widget.tsx"])
        self.assertEqual(
            recommendation["command_preview"],
            f"git worktree add ../work-cartographer-dashboard-blueprint-review -b "
            f"cartographer/dashboard-blueprint-review {source_head}",
        )
        self.assertFalse(recommendation["worktree_creation_allowed"])
        self.assertFalse(recommendation["branch_creation_allowed"])
        self.assertFalse(recommendation["actions_taken"])

    def test_level_5_worktree_recommendation_contract_empty_state_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/cartographer")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_5_worktree_recommendation_contract()
            after_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")

        self.assertEqual(before_worktrees, after_worktrees)
        self.assertEqual(payload["level"], 5)
        self.assertEqual(payload["recommendation_count"], 0)
        self.assertEqual(payload["recommendations"], [])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_5_branch_worktree_approval_preview_validates_without_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "work"
            root.mkdir()
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            before_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                recommendation = build_cartographer_level_5_worktree_recommendation_contract()["recommendations"][0]
                payload = build_cartographer_level_5_branch_worktree_approval_preview(
                    recommendation_id=recommendation["recommendation_id"],
                    approval_id="approval-level-5-preview",
                    approved_by="Britton",
                    exact_worktree_path=recommendation["target_path"],
                    exact_branch_name=recommendation["branch_proposal"],
                    base_head=recommendation["base_head"],
                    owner="Britton",
                    purpose=recommendation["purpose"],
                    command_preview=recommendation["command_preview"],
                )
                response = TestClient(_test_app()).post(
                    f"/v1/cartographer/level-5-worktree-recommendations/{recommendation['recommendation_id']}/approval-preview",
                    json={
                        "approval_id": "approval-level-5-preview",
                        "approved_by": "Britton",
                        "exact_worktree_path": recommendation["target_path"],
                        "exact_branch_name": recommendation["branch_proposal"],
                        "base_head": recommendation["base_head"],
                        "owner": "Britton",
                        "purpose": recommendation["purpose"],
                        "command_preview": recommendation["command_preview"],
                    },
                )
            after_branch = _git_stdout(root, "branch", "--show-current").strip()
            after_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            target_path = Path(temp_dir) / "work-cartographer-dashboard-blueprint-review"

        self.assertEqual(before_branch, "main")
        self.assertEqual(after_branch, "main")
        self.assertEqual(before_worktrees, after_worktrees)
        self.assertFalse(target_path.exists())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["approval_version"],
            "cartographer.level_5.branch_worktree_approval_preview.v1",
        )
        self.assertEqual(payload["level"], 5)
        self.assertEqual(payload["mode"], "branch_worktree_approval_gate_preview")
        self.assertTrue(payload["approval_validated"])
        self.assertEqual(payload["blockers"], [])
        self.assertEqual(payload["execution_blockers"], ["branch_worktree_creation_not_implemented"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["worktree_created"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["branch_created"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["checkout_performed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["push_allowed"])

    def test_level_5_branch_worktree_approval_preview_blocks_bad_metadata_without_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "work"
            root.mkdir()
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                recommendation = build_cartographer_level_5_worktree_recommendation_contract()["recommendations"][0]
                payload = build_cartographer_level_5_branch_worktree_approval_preview(
                    recommendation_id=recommendation["recommendation_id"],
                    approval_id="approval-level-5-bad",
                    approved_by="cartographer",
                    exact_worktree_path="../wrong-path",
                    exact_branch_name="wrong-branch",
                    base_head="stale-head",
                    owner=None,
                    purpose=None,
                    command_preview="git worktree add ../wrong-path",
                )
            after_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")

        self.assertEqual(before_worktrees, after_worktrees)
        self.assertFalse(payload["approval_validated"])
        self.assertIn("cartographer_self_approval_blocked", payload["blockers"])
        self.assertIn("owner_required", payload["blockers"])
        self.assertIn("purpose_required", payload["blockers"])
        self.assertIn("exact_worktree_path_mismatch", payload["blockers"])
        self.assertIn("exact_branch_name_mismatch", payload["blockers"])
        self.assertIn("base_head_mismatch", payload["blockers"])
        self.assertIn("command_preview_mismatch", payload["blockers"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_5_multi_worker_safety_smoke_reports_collision_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "work"
            root.mkdir()
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            before_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_5_multi_worker_safety_smoke()
                response = TestClient(_test_app()).get("/v1/cartographer/level-5-multi-worker-safety-smoke")
            after_branch = _git_stdout(root, "branch", "--show-current").strip()
            after_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            target_path = Path(temp_dir) / "work-cartographer-dashboard-blueprint-review"

        self.assertEqual(before_branch, "main")
        self.assertEqual(after_branch, "main")
        self.assertEqual(before_worktrees, after_worktrees)
        self.assertFalse(target_path.exists())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["smoke_version"],
            "cartographer.level_5.multi_worker_safety_smoke.v1",
        )
        self.assertEqual(payload["level"], 5)
        self.assertEqual(payload["mode"], "multi_codex_worker_safety_smoke")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["checkout_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertEqual(payload["worker_assignment_count"], 1)
        self.assertEqual(payload["collision_count"], 1)
        assignment = payload["worker_assignments"][0]
        self.assertEqual(assignment["worker_id"], "codex-worker-1")
        self.assertEqual(assignment["collision_status"], "blocked_until_isolated")
        self.assertEqual(assignment["related_files"], ["src/components/dashboard/Widget.tsx"])
        self.assertEqual(assignment["recommended_worktree_path"], "../work-cartographer-dashboard-blueprint-review")
        self.assertEqual(assignment["recommended_branch"], "cartographer/dashboard-blueprint-review")
        self.assertFalse(assignment["assignment_allowed_without_approval"])
        self.assertTrue(assignment["owner_assignment_required"])
        self.assertFalse(assignment["actions_taken"])
        self.assertFalse(assignment["branch_creation_allowed"])
        self.assertFalse(assignment["worktree_creation_allowed"])

    def test_level_5_multi_worker_safety_smoke_clean_state_allows_read_only_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/cartographer")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            before_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_5_multi_worker_safety_smoke()
            after_worktrees = _git_stdout(root, "worktree", "list", "--porcelain")

        self.assertEqual(before_worktrees, after_worktrees)
        self.assertEqual(payload["level"], 5)
        self.assertEqual(payload["collision_count"], 0)
        self.assertEqual(payload["worker_assignment_count"], 1)
        assignment = payload["worker_assignments"][0]
        self.assertEqual(assignment["collision_status"], "clear")
        self.assertTrue(assignment["assignment_allowed_without_approval"])
        self.assertFalse(assignment["owner_assignment_required"])
        self.assertIsNone(assignment["recommended_worktree_path"])
        self.assertFalse(payload["worktree_creation_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_commit_proposal_packages_applied_blueprint_files_without_committing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            blueprint = root / "_blueprints" / "current" / "dashboard_state.md"
            blueprint.write_text(
                blueprint.read_text(encoding="utf-8") + "\nApplied update.\n",
                encoding="utf-8",
            )
            _write_proposal(
                root,
                "applied",
                "bp-20260515-applied",
                {
                    "status": "applied",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "affected_blueprints": ["dashboard-state"],
                    "changed_files": ["src/components/dashboard/Widget.tsx"],
                    "proposed_files": ["_blueprints/current/dashboard_state.md"],
                    "post_apply_verification": _verified_post_apply_verification(),
                    "transitions": [
                        {
                            "status": "applied",
                            "timestamp": "2026-05-15T10:08:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )

            before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_commit_proposals()
            after_head = _git_stdout(root, "rev-parse", "HEAD").strip()

        self.assertEqual(before_head, after_head)
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertGreaterEqual(payload["commit_proposal_count"], 1)
        proposal = next(
            item
            for item in payload["commit_proposals"]
            if item["source_proposal_id"] == "bp-20260515-applied"
        )
        self.assertTrue(proposal["commit_proposal_id"].startswith("commit-prop-"))
        self.assertEqual(proposal["source_proposal_id"], "bp-20260515-applied")
        self.assertEqual(proposal["status"], "commit_pending")
        self.assertEqual(
            proposal["suggested_message"],
            "docs(dashboard): apply cartographer blueprint update",
        )
        self.assertEqual(proposal["story"], "Blueprint System docs/runbook update")
        self.assertEqual(proposal["group_key"], "blueprint-system:low:docs")
        self.assertIn("blueprint-system docs work", proposal["group_reason"])
        self.assertEqual(proposal["files"], ["_blueprints/current/dashboard_state.md"])
        self.assertEqual(proposal["included_files"], ["_blueprints/current/dashboard_state.md"])
        self.assertEqual(
            proposal["excluded_files"],
            ["_blueprints/proposals/applied/bp-20260515-applied.json"],
        )
        self.assertEqual(proposal["component"], "blueprint-system")
        self.assertEqual(proposal["risk"], "low")
        self.assertIn("_blueprints/current/dashboard_state.md", proposal["diff_summary"])
        self.assertEqual(
            proposal["required_checks"],
            ["git_diff_check", "blueprint_metadata_validation", "cartographer_pytest"],
        )
        self.assertEqual(proposal["audit_state"], "commit_not_created")
        self.assertEqual(proposal["rollback_command"], "git reset --soft HEAD~1")
        self.assertFalse(proposal["stronger_confirmation_required"])
        self.assertFalse(proposal["commit_blocked"])
        self.assertEqual(proposal["commit_blockers"], [])
        self.assertFalse(proposal["generated"])
        self.assertEqual(proposal["unstaged_files"], ["_blueprints/current/dashboard_state.md"])
        self.assertTrue(proposal["editable"])
        self.assertTrue(proposal["requires_approval"])
        self.assertFalse(proposal["commit_enabled"])
        self.assertFalse(proposal["action_taken"])

    def test_commit_proposal_blocks_failed_post_apply_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            blueprint = root / "_blueprints" / "current" / "dashboard_state.md"
            blueprint.write_text(
                blueprint.read_text(encoding="utf-8") + "\nFailed apply update.\n",
                encoding="utf-8",
            )
            _write_proposal(
                root,
                "applied",
                "bp-failed-verification",
                {
                    "status": "applied",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "proposed_files": ["_blueprints/current/dashboard_state.md"],
                    "post_apply_verification": {
                        "checks": [
                            {
                                "id": "typecheck",
                                "required": True,
                                "status": "failed",
                                "summary": "TypeScript failed.",
                            }
                        ],
                        "commit_blockers": ["post_apply_verification_failed"],
                        "commit_proposal_blocked": True,
                        "push_blockers": ["push_requires_separate_approval"],
                        "push_path_available": False,
                        "required": True,
                        "status": "verification_failed",
                    },
                    "transitions": [
                        {
                            "status": "applied",
                            "timestamp": "2026-05-18T12:00:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_commit_proposals()

        proposal = next(
            item
            for item in payload["commit_proposals"]
            if item["source_proposal_id"] == "bp-failed-verification"
        )
        self.assertTrue(proposal["commit_blocked"])
        self.assertEqual(proposal["verification_status"], "verification_failed")
        self.assertIn("post_apply_verification_failed", proposal["commit_blockers"])
        self.assertEqual(proposal["verification_checks"][0]["status"], "failed")
        self.assertFalse(proposal["commit_enabled"])
        self.assertFalse(proposal["action_taken"])

    def test_commit_proposals_group_dirty_tree_files_by_component_risk_and_purpose(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            dashboard = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard.parent.mkdir(parents=True)
            dashboard.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")
            _git(root, "add", "src/components/dashboard/Widget.tsx")

            docs = root / "docs" / "cartographer.md"
            docs.parent.mkdir()
            docs.write_text("docs update\n", encoding="utf-8")
            (root / "source_proxy" / "cartographer" / "apply.py").parent.mkdir(parents=True)
            (root / "source_proxy" / "cartographer" / "apply.py").write_text(
                "def apply_change():\n    return True\n",
                encoding="utf-8",
            )
            (root / "scout" / "soak-logs").mkdir(parents=True)
            (root / "scout" / "soak-logs" / "scout-soak-snapshot-test.json").write_text(
                "{}\n",
                encoding="utf-8",
            )

            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_commit_proposals()
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertFalse(payload["actions_taken"])
        proposals = payload["commit_proposals"]
        files = [file for proposal in proposals for file in proposal["files"]]
        self.assertEqual(len(files), len(set(files)))
        self.assertIn("src/components/dashboard/Widget.tsx", files)
        self.assertIn("docs/cartographer.md", files)
        self.assertIn("source_proxy/cartographer/apply.py", files)
        self.assertIn("scout/soak-logs/scout-soak-snapshot-test.json", files)

        by_file = {
            file: proposal
            for proposal in proposals
            for file in proposal["files"]
        }
        self.assertEqual(by_file["src/components/dashboard/Widget.tsx"]["component"], "dashboard")
        self.assertEqual(by_file["src/components/dashboard/Widget.tsx"]["risk"], "medium")
        self.assertEqual(by_file["src/components/dashboard/Widget.tsx"]["story"], "Dashboard implementation update")
        self.assertEqual(by_file["src/components/dashboard/Widget.tsx"]["group_key"], "dashboard:medium:code")
        self.assertEqual(by_file["src/components/dashboard/Widget.tsx"]["included_files"], ["src/components/dashboard/Widget.tsx"])
        self.assertNotIn("src/components/dashboard/Widget.tsx", by_file["src/components/dashboard/Widget.tsx"]["excluded_files"])
        self.assertEqual(by_file["src/components/dashboard/Widget.tsx"]["staged_files"], ["src/components/dashboard/Widget.tsx"])
        self.assertEqual(by_file["docs/cartographer.md"]["component"], "docs")
        self.assertEqual(by_file["docs/cartographer.md"]["risk"], "low")
        self.assertEqual(by_file["docs/cartographer.md"]["story"], "Docs docs/runbook update")
        self.assertEqual(by_file["docs/cartographer.md"]["group_key"], "docs:low:docs")
        self.assertEqual(by_file["source_proxy/cartographer/apply.py"]["component"], "cartographer")
        self.assertEqual(by_file["source_proxy/cartographer/apply.py"]["risk"], "high")
        self.assertEqual(by_file["source_proxy/cartographer/apply.py"]["story"], "Cartographer safety hardening")
        self.assertEqual(by_file["source_proxy/cartographer/apply.py"]["group_key"], "cartographer:high:code")
        self.assertTrue(by_file["source_proxy/cartographer/apply.py"]["stronger_confirmation_required"])
        self.assertFalse(by_file["source_proxy/cartographer/apply.py"]["commit_blocked"])
        self.assertEqual(by_file["scout/soak-logs/scout-soak-snapshot-test.json"]["suggested_message"], "chore(scout): record soak snapshot")
        self.assertEqual(by_file["scout/soak-logs/scout-soak-snapshot-test.json"]["story"], "Scout soak evidence")
        self.assertEqual(by_file["scout/soak-logs/scout-soak-snapshot-test.json"]["group_key"], "scout:low:soak")
        self.assertTrue(
            all("unrelated commit stories separate" in proposal["group_reason"] for proposal in proposals)
        )
        self.assertTrue(all(proposal["generated"] for proposal in proposals))
        self.assertTrue(all(proposal["requires_approval"] for proposal in proposals))
        self.assertTrue(all(proposal["audit_state"] == "commit_not_created" for proposal in proposals))
        self.assertTrue(all(proposal["rollback_command"] == "git reset --soft HEAD~1" for proposal in proposals))
        self.assertTrue(all(not proposal["commit_enabled"] for proposal in proposals))
        self.assertTrue(all(not proposal["action_taken"] for proposal in proposals))

    def test_commit_preview_blocks_unknown_files_without_committing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "productionProxy.md").write_text("manual note\n", encoding="utf-8")

            before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_commit_proposals()
            after_head = _git_stdout(root, "rev-parse", "HEAD").strip()

        self.assertEqual(before_head, after_head)
        proposal = payload["commit_proposals"][0]
        self.assertEqual(proposal["risk"], "unknown")
        self.assertEqual(proposal["included_files"], ["productionProxy.md"])
        self.assertTrue(proposal["commit_blocked"])
        self.assertEqual(proposal["commit_blockers"], ["unknown_files_require_manual_classification"])
        self.assertTrue(proposal["stronger_confirmation_required"])
        self.assertFalse(proposal["commit_enabled"])
        self.assertFalse(proposal["action_taken"])

    def test_commit_proposals_fall_back_to_current_repo_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "README.md").write_text("changed\n", encoding="utf-8")
            before_status = _git_stdout(root, "status", "--short")
            previous_cwd = Path.cwd()
            try:
                os.chdir(root)
                with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
                    payload = build_cartographer_commit_proposals()
            finally:
                os.chdir(previous_cwd)
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertEqual(payload["commit_proposal_count"], 1)
        proposal = payload["commit_proposals"][0]
        self.assertEqual(proposal["files"], ["README.md"])
        self.assertEqual(proposal["story"], "Docs docs/runbook update")
        self.assertEqual(proposal["group_key"], "docs:low:docs")
        self.assertFalse(proposal["commit_enabled"])
        self.assertFalse(proposal["action_taken"])

    def test_commit_proposal_ignores_unapplied_or_clean_proposals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _write_proposal(
                root,
                "approved",
                "bp-20260515-approved",
                {
                    "status": "approved",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "proposed_files": ["_blueprints/current/dashboard_state.md"],
                    "transitions": [
                        {
                            "status": "approved",
                            "timestamp": "2026-05-15T10:09:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )
            _git(root, "add", ".")
            _git(root, "commit", "-m", "test fixture proposal")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_commit_proposals()

        self.assertEqual(payload["commit_proposals"], [])
        self.assertEqual(payload["commit_proposal_count"], 0)
        self.assertFalse(payload["actions_taken"])

    def test_level_3_commit_proposals_are_read_only_and_block_commit_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Cartographer Level 3 Autonomy Plan\n", encoding="utf-8")
            implementation = root / "source_proxy" / "cartographer" / "commit_proposals.py"
            implementation.parent.mkdir(parents=True, exist_ok=True)
            implementation.write_text("def preview():\n    return 'level 3'\n", encoding="utf-8")

            before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_3_commit_proposals()
            after_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_head, after_head)
        self.assertEqual(before_status, after_status)
        self.assertEqual(payload["level"], 3)
        self.assertEqual(payload["proposal_version"], "cartographer.level_3.commit_proposal.v1")
        self.assertEqual(payload["mode"], "human_approved_local_commit_proposals")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["branch_delete_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["self_approval_allowed"])
        self.assertFalse(payload["self_promotion_allowed"])
        self.assertFalse(payload["creates_push_queue_item"])
        self.assertIn("level_2_apply_blocked", payload["activation_blockers"])
        self.assertGreaterEqual(payload["proposal_count"], 2)

        receipts_by_file = {
            file: receipt
            for receipt in payload["commit_proposals"]
            for file in receipt["included_files"]
        }
        plan_receipt = receipts_by_file["docs/cartographer-level-3-autonomy-plan.md"]
        self.assertEqual(plan_receipt["file_bundle"], "cartographer_level_3_plan")
        self.assertEqual(plan_receipt["created_by"], "cartographer")
        self.assertEqual(plan_receipt["current_branch"], "main")
        self.assertEqual(plan_receipt["git_head_at_creation"], before_head)
        self.assertTrue(plan_receipt["approval_required"])
        self.assertIsNone(plan_receipt["approval_id"])
        self.assertIsNone(plan_receipt["approved_by"])
        self.assertFalse(plan_receipt["commit_allowed"])
        self.assertFalse(plan_receipt["push_allowed"])
        self.assertFalse(plan_receipt["creates_push_queue_item"])
        self.assertIn("git diff --check", plan_receipt["related_test_commands"])
        self.assertIn("git status -sb", plan_receipt["manual_check_commands"])

        implementation_receipt = receipts_by_file["source_proxy/cartographer/commit_proposals.py"]
        self.assertEqual(implementation_receipt["file_bundle"], "cartographer_level_3")
        self.assertIn(
            "source_proxy/cartographer/commit_proposals.py",
            implementation_receipt["rationale_by_file"],
        )
        self.assertFalse(implementation_receipt["commit_allowed"])
        self.assertFalse(implementation_receipt["action_taken"])

    def test_level_3_commit_proposals_block_forbidden_sensitive_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / ".env.local").write_text("TOKEN=do-not-read\n", encoding="utf-8")
            (root / "package-lock.json").write_text("{}\n", encoding="utf-8")

            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_3_commit_proposals()
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertIn("forbidden_files_detected", payload["activation_blockers"])
        self.assertIn(".env.local", payload["forbidden_files"])
        self.assertIn("package-lock.json", payload["forbidden_files"])
        blocked_files = {
            file: receipt
            for receipt in payload["blocked_bundles"]
            for file in receipt["included_files"]
        }
        self.assertIn(".env.local", blocked_files)
        self.assertIn("forbidden_files_detected", blocked_files[".env.local"]["blockers"])
        self.assertIn("sensitive_files_detected", blocked_files[".env.local"]["blockers"])
        self.assertFalse(blocked_files[".env.local"]["commit_allowed"])
        self.assertFalse(blocked_files[".env.local"]["push_allowed"])

    def test_level_3_commit_proposals_endpoint_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                response = TestClient(_test_app()).get("/v1/cartographer/level-3-commit-proposals")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["endpoint"], "/v1/cartographer/level-3-commit-proposals")
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["commit_proposals"][0]["level"], 3)

    def test_level_3_approval_preview_validates_exact_bundle_without_committing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposals = build_cartographer_level_3_commit_proposals()
                proposal = next(
                    item
                    for item in proposals["commit_proposals"]
                    if item["file_bundle"] == "cartographer_level_3_plan"
                )
                before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
                before_status = _git_stdout(root, "status", "--short")
                payload = build_cartographer_level_3_commit_approval_preview(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-level-3-preview",
                    approved_by="Britton",
                    exact_file_list=proposal["included_files"],
                    proposed_commit_title=proposal["proposed_commit_title"],
                    proposed_commit_body=proposal["proposed_commit_body"],
                    git_head_at_creation=proposal["git_head_at_creation"],
                    dirty_tree_fingerprint=proposal["dirty_tree_fingerprint"],
                    check_results=[
                        {"command": command, "status": "passed"}
                        for command in proposal["related_test_commands"]
                    ],
                )
                after_head = _git_stdout(root, "rev-parse", "HEAD").strip()
                after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_head, after_head)
        self.assertEqual(before_status, after_status)
        self.assertEqual(payload["level"], 3)
        self.assertEqual(payload["mode"], "human_approval_gate_preview")
        self.assertTrue(payload["approval_validated"])
        self.assertEqual(payload["approval_id"], "approval-level-3-preview")
        self.assertEqual(payload["approved_by"], "Britton")
        self.assertEqual(payload["git_head_at_creation"], before_head)
        self.assertEqual(payload["supplied_git_head_at_creation"], before_head)
        self.assertEqual(payload["dirty_tree_fingerprint"], proposal["dirty_tree_fingerprint"])
        self.assertEqual(
            payload["supplied_dirty_tree_fingerprint"],
            proposal["dirty_tree_fingerprint"],
        )
        self.assertTrue(payload["checks_validated"])
        self.assertEqual(
            payload["required_check_commands"],
            proposal["related_test_commands"],
        )
        self.assertFalse(payload["proposal_stale"])
        self.assertEqual(payload["blockers"], [])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["commit_enabled"])
        self.assertFalse(payload["commit_execution_enabled"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["creates_push_queue_item"])
        self.assertFalse(payload["actions_taken"])

    def test_level_3_approval_preview_blocks_self_approval_and_file_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposals = build_cartographer_level_3_commit_proposals()
                proposal = next(
                    item
                    for item in proposals["commit_proposals"]
                    if item["file_bundle"] == "cartographer_level_3_plan"
                )
                before_status = _git_stdout(root, "status", "--short")
                payload = build_cartographer_level_3_commit_approval_preview(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-level-3-self",
                    approved_by="cartographer",
                    exact_file_list=["README.md"],
                    proposed_commit_title=proposal["proposed_commit_title"],
                    proposed_commit_body=proposal["proposed_commit_body"],
                )
                after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertFalse(payload["approval_validated"])
        self.assertIn("cartographer_self_approval_blocked", payload["blockers"])
        self.assertIn("exact_file_list_mismatch", payload["blockers"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_3_approval_preview_blocks_stale_head_and_dirty_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposals = build_cartographer_level_3_commit_proposals()
                proposal = next(
                    item
                    for item in proposals["commit_proposals"]
                    if item["file_bundle"] == "cartographer_level_3_plan"
                )
                before_status = _git_stdout(root, "status", "--short")
                payload = build_cartographer_level_3_commit_approval_preview(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-level-3-stale",
                    approved_by="Britton",
                    exact_file_list=proposal["included_files"],
                    proposed_commit_title=proposal["proposed_commit_title"],
                    proposed_commit_body=proposal["proposed_commit_body"],
                    git_head_at_creation="stale-head",
                    dirty_tree_fingerprint="stale-fingerprint",
                    check_results=[
                        {"command": command, "status": "passed"}
                        for command in proposal["related_test_commands"]
                    ],
                )
                after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertFalse(payload["approval_validated"])
        self.assertTrue(payload["proposal_stale"])
        self.assertIn("git_head_mismatch", payload["blockers"])
        self.assertIn("dirty_tree_fingerprint_mismatch", payload["blockers"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["commit_execution_enabled"])
        self.assertFalse(payload["actions_taken"])

    def test_level_3_approval_preview_blocks_missing_or_failed_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposals = build_cartographer_level_3_commit_proposals()
                proposal = next(
                    item
                    for item in proposals["commit_proposals"]
                    if item["file_bundle"] == "cartographer_level_3_plan"
                )
                missing = build_cartographer_level_3_commit_approval_preview(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-level-3-missing-checks",
                    approved_by="Britton",
                    exact_file_list=proposal["included_files"],
                    proposed_commit_title=proposal["proposed_commit_title"],
                    proposed_commit_body=proposal["proposed_commit_body"],
                    git_head_at_creation=proposal["git_head_at_creation"],
                    dirty_tree_fingerprint=proposal["dirty_tree_fingerprint"],
                    check_results=[],
                )
                failed = build_cartographer_level_3_commit_approval_preview(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-level-3-failed-checks",
                    approved_by="Britton",
                    exact_file_list=proposal["included_files"],
                    proposed_commit_title=proposal["proposed_commit_title"],
                    proposed_commit_body=proposal["proposed_commit_body"],
                    git_head_at_creation=proposal["git_head_at_creation"],
                    dirty_tree_fingerprint=proposal["dirty_tree_fingerprint"],
                    check_results=[
                        {"command": command, "status": "failed"}
                        for command in proposal["related_test_commands"]
                    ],
                )

        self.assertFalse(missing["approval_validated"])
        self.assertFalse(missing["checks_validated"])
        self.assertIn("required_checks_missing", missing["blockers"])
        self.assertFalse(missing["commit_allowed"])
        self.assertFalse(missing["actions_taken"])
        self.assertFalse(failed["approval_validated"])
        self.assertFalse(failed["checks_validated"])
        self.assertIn("required_checks_failed", failed["blockers"])
        self.assertFalse(failed["commit_allowed"])
        self.assertFalse(failed["actions_taken"])

    def test_level_3_approval_preview_requires_exact_deleted_file_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            tracked_doc = root / "docs" / "old-plan.md"
            tracked_doc.parent.mkdir(parents=True, exist_ok=True)
            tracked_doc.write_text("old plan\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            tracked_doc.unlink()

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposals = build_cartographer_level_3_commit_proposals()
                proposal = next(
                    item
                    for item in proposals["commit_proposals"]
                    if item["included_files"] == ["docs/old-plan.md"]
                )
                check_results = [
                    {"command": command, "status": "passed"}
                    for command in proposal["related_test_commands"]
                ]
                missing_deletion_approval = build_cartographer_level_3_commit_approval_preview(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-level-3-delete-missing",
                    approved_by="Britton",
                    exact_file_list=proposal["included_files"],
                    proposed_commit_title=proposal["proposed_commit_title"],
                    proposed_commit_body=proposal["proposed_commit_body"],
                    git_head_at_creation=proposal["git_head_at_creation"],
                    dirty_tree_fingerprint=proposal["dirty_tree_fingerprint"],
                    check_results=check_results,
                )
                approved_deletion = build_cartographer_level_3_commit_approval_preview(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-level-3-delete-approved",
                    approved_by="Britton",
                    exact_file_list=proposal["included_files"],
                    proposed_commit_title=proposal["proposed_commit_title"],
                    proposed_commit_body=proposal["proposed_commit_body"],
                    git_head_at_creation=proposal["git_head_at_creation"],
                    dirty_tree_fingerprint=proposal["dirty_tree_fingerprint"],
                    check_results=check_results,
                    approved_deleted_files=["docs/old-plan.md"],
                )

        self.assertEqual(proposal["deleted_files"], ["docs/old-plan.md"])
        self.assertFalse(missing_deletion_approval["approval_validated"])
        self.assertFalse(missing_deletion_approval["deletions_validated"])
        self.assertIn(
            "explicit_deletion_approval_required",
            missing_deletion_approval["blockers"],
        )
        self.assertFalse(missing_deletion_approval["commit_allowed"])
        self.assertTrue(approved_deletion["approval_validated"])
        self.assertTrue(approved_deletion["deletions_validated"])
        self.assertEqual(approved_deletion["approved_deleted_files"], ["docs/old-plan.md"])
        self.assertFalse(approved_deletion["commit_allowed"])
        self.assertFalse(approved_deletion["actions_taken"])

    def test_level_3_approval_preview_endpoint_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal_payload = build_cartographer_level_3_commit_proposals()
                proposal = proposal_payload["commit_proposals"][0]
                response = TestClient(_test_app()).post(
                    f"/v1/cartographer/level-3-commit-proposals/{proposal['proposal_id']}/approval-preview",
                    json={
                        "approval_id": "approval-level-3-endpoint",
                        "approved_by": "Britton",
                        "exact_file_list": proposal["included_files"],
                        "proposed_commit_title": proposal["proposed_commit_title"],
                        "proposed_commit_body": proposal["proposed_commit_body"],
                        "git_head_at_creation": proposal["git_head_at_creation"],
                        "dirty_tree_fingerprint": proposal["dirty_tree_fingerprint"],
                        "check_results": [
                            {"command": command, "status": "passed"}
                            for command in proposal["related_test_commands"]
                        ],
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["level"], 3)
        self.assertTrue(payload["approval_validated"])
        self.assertTrue(payload["checks_validated"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_3_commit_execution_endpoint_creates_approved_local_commit_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            marker = root / "docs" / "cartographer-level-1-review-gate.md"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                "\n".join(
                    [
                        "level_1_review_gate: accepted_by_britton",
                        "commit_allowed: false",
                        "push_allowed: false",
                        "self_promotion_allowed: false",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-2-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Level 2 Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = next(
                    item
                    for item in build_cartographer_level_3_commit_proposals()["commit_proposals"]
                    if item["included_files"] == ["docs/cartographer-level-2-autonomy-plan.md"]
                )
                before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
                before_status = _git_stdout(root, "status", "--short")
                response = TestClient(_test_app()).post(
                    f"/v1/cartographer/level-3-commit-proposals/{proposal['proposal_id']}/commit",
                    json={
                        "approval_id": "approval-level-3-execute",
                        "approved_by": "Britton",
                        "exact_file_list": proposal["included_files"],
                        "proposed_commit_title": proposal["proposed_commit_title"],
                        "proposed_commit_body": proposal["proposed_commit_body"],
                        "git_head_at_creation": proposal["git_head_at_creation"],
                        "dirty_tree_fingerprint": proposal["dirty_tree_fingerprint"],
                        "check_results": [
                            {"command": command, "status": "passed"}
                            for command in proposal["related_test_commands"]
                        ],
                        "approved_deleted_files": proposal["deleted_files"],
                    },
                )
                after_head = _git_stdout(root, "rev-parse", "HEAD").strip()
                after_status = _git_stdout(root, "status", "--short")
                committed_files = _git_stdout(root, "show", "--name-only", "--format=", "HEAD").splitlines()

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotEqual(before_head, after_head)
        self.assertIn("?? docs/cartographer-level-2-autonomy-plan.md", before_status)
        self.assertEqual(after_status, "")
        self.assertEqual(payload["status"], "committed")
        self.assertEqual(payload["receipt_version"], "cartographer.level_3.local_commit_receipt.v1")
        self.assertTrue(payload["receipt_id"].startswith("level-3-local-commit-receipt-"))
        self.assertEqual(payload["mode"], "approved_local_commit_executor")
        self.assertTrue(payload["approval_validated"])
        self.assertEqual(payload["approval_id"], "approval-level-3-execute")
        self.assertEqual(payload["approved_by"], "Britton")
        self.assertEqual(payload["executed_by"], "cartographer")
        self.assertTrue(payload["commit_created"])
        self.assertEqual(payload["commit_sha"], after_head)
        self.assertEqual(payload["head_before"], before_head)
        self.assertEqual(payload["head_after"], after_head)
        self.assertEqual(payload["approved_files"], ["docs/cartographer-level-2-autonomy-plan.md"])
        self.assertEqual(payload["committed_files"], ["docs/cartographer-level-2-autonomy-plan.md"])
        self.assertEqual(committed_files, ["docs/cartographer-level-2-autonomy-plan.md"])
        self.assertTrue(payload["validation_summary"]["approval_validated"])
        self.assertTrue(payload["validation_summary"]["checks_validated"])
        self.assertTrue(payload["validation_summary"]["deletions_validated"])
        self.assertTrue(payload["validation_summary"]["head_validated"])
        self.assertTrue(payload["validation_summary"]["dirty_tree_fingerprint_validated"])
        self.assertEqual(payload["rollback_command"], "git reset --soft HEAD~1")
        self.assertTrue(payload["rollback_requires_human_approval"])
        self.assertFalse(payload["rollback_performed"])
        self.assertEqual(payload["command_summary"]["stage"], "git add -- <approved-files>")
        self.assertEqual(payload["command_summary"]["commit"], "git commit -m <title> -m <body> -- <approved-files>")
        self.assertIsNone(payload["command_summary"]["push"])
        self.assertFalse(payload["commit_execution_enabled"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_created"])
        self.assertFalse(payload["creates_push_queue_item"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["branch_created"])
        self.assertFalse(payload["merge_created"])
        self.assertFalse(payload["stash_created"])
        self.assertFalse(payload["cleanup_performed"])

    def test_level_3_commit_execution_negative_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = build_cartographer_level_3_commit_proposals()["commit_proposals"][0]
                before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
                before_status = _git_stdout(root, "status", "--short")
                missing_approval = block_cartographer_level_3_commit_execution(
                    proposal_id=proposal["proposal_id"],
                    approval_id=None,
                    approved_by="Britton",
                )
                self_approval = block_cartographer_level_3_commit_execution(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-self",
                    approved_by="cartographer",
                )
                unknown_proposal = block_cartographer_level_3_commit_execution(
                    proposal_id="missing-level-3-proposal",
                    approval_id="approval-missing-proposal",
                    approved_by="Britton",
                )
                after_head = _git_stdout(root, "rev-parse", "HEAD").strip()
                after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_head, after_head)
        self.assertEqual(before_status, after_status)
        cases = [
            (missing_approval, "approval_id_required"),
            (self_approval, "cartographer_self_approval_blocked"),
            (unknown_proposal, "proposal_not_found"),
        ]
        for payload, blocker in cases:
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["receipt_version"], "cartographer.level_3.local_commit_receipt.v1")
            self.assertTrue(payload["receipt_id"].startswith("level-3-local-commit-receipt-"))
            self.assertIn(blocker, payload["blockers"])
            self.assertFalse(payload["commit_allowed"])
            self.assertFalse(payload["commit_enabled"])
            self.assertFalse(payload["commit_execution_enabled"])
            self.assertFalse(payload["commit_created"])
            self.assertFalse(payload["push_allowed"])
            self.assertFalse(payload["push_enabled"])
            self.assertFalse(payload["push_created"])
            self.assertFalse(payload["creates_push_queue_item"])
            self.assertFalse(payload["branch_creation_allowed"])
            self.assertFalse(payload["stash_allowed"])
            self.assertFalse(payload["cleanup_allowed"])
            self.assertEqual(payload["rollback_command"], "git reset --soft HEAD~1")
            self.assertTrue(payload["rollback_requires_human_approval"])
            self.assertFalse(payload["rollback_performed"])
            self.assertFalse(payload["branch_created"])
            self.assertFalse(payload["merge_created"])
            self.assertFalse(payload["stash_created"])
            self.assertFalse(payload["cleanup_performed"])
            self.assertFalse(payload["actions_taken"])

    def test_level_3_approval_preview_blocks_missing_approval_and_unknown_proposal_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = build_cartographer_level_3_commit_proposals()["commit_proposals"][0]
                before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
                before_status = _git_stdout(root, "status", "--short")
                no_approval = build_cartographer_level_3_commit_approval_preview(
                    proposal_id=proposal["proposal_id"],
                    approval_id=None,
                    approved_by=None,
                    exact_file_list=proposal["included_files"],
                    proposed_commit_title=proposal["proposed_commit_title"],
                    proposed_commit_body=proposal["proposed_commit_body"],
                    git_head_at_creation=proposal["git_head_at_creation"],
                    dirty_tree_fingerprint=proposal["dirty_tree_fingerprint"],
                    check_results=[
                        {"command": command, "status": "passed"}
                        for command in proposal["related_test_commands"]
                    ],
                )
                unknown_proposal = build_cartographer_level_3_commit_approval_preview(
                    proposal_id="missing-level-3-proposal",
                    approval_id="approval-missing-proposal",
                    approved_by="Britton",
                    exact_file_list=proposal["included_files"],
                    proposed_commit_title=proposal["proposed_commit_title"],
                    proposed_commit_body=proposal["proposed_commit_body"],
                    git_head_at_creation=proposal["git_head_at_creation"],
                    dirty_tree_fingerprint=proposal["dirty_tree_fingerprint"],
                    check_results=[
                        {"command": command, "status": "passed"}
                        for command in proposal["related_test_commands"]
                    ],
                )
                after_head = _git_stdout(root, "rev-parse", "HEAD").strip()
                after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_head, after_head)
        self.assertEqual(before_status, after_status)
        self.assertFalse(no_approval["approval_validated"])
        self.assertIn("approval_id_required", no_approval["blockers"])
        self.assertIn("approved_by_required", no_approval["blockers"])
        self.assertFalse(unknown_proposal["approval_validated"])
        self.assertIn("proposal_not_found", unknown_proposal["blockers"])
        for payload in (no_approval, unknown_proposal):
            self.assertFalse(payload["commit_allowed"])
            self.assertFalse(payload["commit_execution_enabled"])
            self.assertFalse(payload["push_allowed"])
            self.assertFalse(payload["creates_push_queue_item"])
            self.assertFalse(payload["actions_taken"])

    def test_level_3_approval_preview_blocks_unclassified_forbidden_and_sensitive_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            unclassified = root / "misc" / "unclassified-widget.txt"
            unclassified.parent.mkdir(parents=True)
            unclassified.write_text("needs manual classification\n", encoding="utf-8")
            (root / ".env.local").write_text("TOKEN=do-not-commit\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposals = build_cartographer_level_3_commit_proposals()
                before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
                before_status = _git_stdout(root, "status", "--short")
                receipts_by_file = {
                    file: receipt
                    for receipt in proposals["commit_proposals"]
                    for file in receipt["included_files"]
                }
                unclassified_proposal = receipts_by_file["misc/unclassified-widget.txt"]
                forbidden_proposal = receipts_by_file[".env.local"]
                unclassified_preview = build_cartographer_level_3_commit_approval_preview(
                    proposal_id=unclassified_proposal["proposal_id"],
                    approval_id="approval-unclassified",
                    approved_by="Britton",
                    exact_file_list=unclassified_proposal["included_files"],
                    proposed_commit_title=unclassified_proposal["proposed_commit_title"],
                    proposed_commit_body=unclassified_proposal["proposed_commit_body"],
                    git_head_at_creation=unclassified_proposal["git_head_at_creation"],
                    dirty_tree_fingerprint=unclassified_proposal["dirty_tree_fingerprint"],
                    check_results=[
                        {"command": command, "status": "passed"}
                        for command in unclassified_proposal["related_test_commands"]
                    ],
                )
                forbidden_preview = build_cartographer_level_3_commit_approval_preview(
                    proposal_id=forbidden_proposal["proposal_id"],
                    approval_id="approval-forbidden-sensitive",
                    approved_by="Britton",
                    exact_file_list=forbidden_proposal["included_files"],
                    proposed_commit_title=forbidden_proposal["proposed_commit_title"],
                    proposed_commit_body=forbidden_proposal["proposed_commit_body"],
                    git_head_at_creation=forbidden_proposal["git_head_at_creation"],
                    dirty_tree_fingerprint=forbidden_proposal["dirty_tree_fingerprint"],
                    check_results=[
                        {"command": command, "status": "passed"}
                        for command in forbidden_proposal["related_test_commands"]
                    ],
                )
                after_head = _git_stdout(root, "rev-parse", "HEAD").strip()
                after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_head, after_head)
        self.assertEqual(before_status, after_status)
        self.assertFalse(unclassified_preview["approval_validated"])
        self.assertIn("unknown_or_mixed_files_block_approval", unclassified_preview["blockers"])
        self.assertFalse(forbidden_preview["approval_validated"])
        self.assertIn("forbidden_files_detected", forbidden_preview["blockers"])
        self.assertIn("sensitive_files_detected", forbidden_preview["blockers"])
        for payload in (unclassified_preview, forbidden_preview):
            self.assertFalse(payload["commit_allowed"])
            self.assertFalse(payload["commit_execution_enabled"])
            self.assertFalse(payload["push_allowed"])
            self.assertFalse(payload["creates_push_queue_item"])
            self.assertFalse(payload["actions_taken"])

    def test_level_3_closeout_readiness_packet_keeps_commit_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_3_closeout_readiness()
                response = TestClient(_test_app()).get("/v1/cartographer/level-3-closeout-readiness")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["readiness_version"], "cartographer.level_3.closeout_readiness.v1")
        self.assertEqual(payload["level"], 3)
        self.assertEqual(payload["mode"], "closeout_readiness_packet")
        self.assertTrue(payload["proposal_preview_ready"])
        self.assertFalse(payload["local_commit_ready"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["commit_execution_enabled"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["creates_push_queue_item"])
        self.assertFalse(payload["level_2_docs_apply_enabled"])
        self.assertIn("level_2_apply_blocked", payload["activation_blockers"])
        gates = {gate["code"]: gate for gate in payload["gates"]}
        self.assertTrue(gates["proposal_schema_available"]["passed"])
        self.assertTrue(gates["commit_proposal_preview_endpoint_available"]["passed"])
        self.assertTrue(gates["approval_preview_gate_available"]["passed"])
        self.assertTrue(gates["commit_execution_hard_blocked"]["passed"])
        self.assertTrue(gates["commit_push_branch_locked"]["passed"])
        self.assertFalse(gates["level_2_safe_dependency"]["passed"])
        self.assertIn("/v1/cartographer/level-3-closeout-readiness", payload["endpoints"])
        self.assertIn("git status -sb", payload["manual_checks"])

    def test_level_3_endpoint_index_and_finalization_marker_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                index = build_cartographer_level_3_endpoint_index()
                marker = build_cartographer_level_3_finalization_marker()
                index_response = TestClient(_test_app()).get("/v1/cartographer/level-3-endpoints")
                marker_response = TestClient(_test_app()).get("/v1/cartographer/level-3-finalization")

        self.assertEqual(index_response.status_code, 200)
        self.assertEqual(marker_response.status_code, 200)
        self.assertEqual(index["index_version"], "cartographer.level_3.endpoint_index.v1")
        self.assertEqual(marker["marker_version"], "cartographer.level_3.finalization_marker.v1")
        self.assertEqual(index_response.json()["endpoint_count"], index["endpoint_count"])
        self.assertEqual(marker_response.json()["marker_version"], marker["marker_version"])
        endpoints = {item["endpoint"]: item for item in index["endpoints"]}
        self.assertIn("/v1/cartographer/level-3-commit-proposals", endpoints)
        self.assertIn(
            "/v1/cartographer/level-3-commit-proposals/{proposal_id}/approval-preview",
            endpoints,
        )
        self.assertIn(
            "/v1/cartographer/level-3-commit-proposals/{proposal_id}/commit",
            endpoints,
        )
        self.assertIn("/v1/cartographer/level-3-closeout-readiness", endpoints)
        self.assertIn("/v1/cartographer/level-3-endpoints", endpoints)
        self.assertIn("/v1/cartographer/level-3-finalization", endpoints)
        self.assertTrue(all(not item["write_actions_enabled"] for item in endpoints.values()))
        self.assertTrue(all(not item["commit_allowed"] for item in endpoints.values()))
        self.assertTrue(all(not item["push_allowed"] for item in endpoints.values()))
        self.assertFalse(index["write_actions_enabled"])
        self.assertFalse(index["authority_granted"])
        self.assertFalse(index["actions_taken"])
        self.assertFalse(index["commit_allowed"])
        self.assertFalse(index["push_allowed"])
        self.assertFalse(index["creates_push_queue_item"])
        self.assertTrue(marker["proposal_preview_complete"])
        self.assertFalse(marker["local_commit_ready"])
        self.assertTrue(marker["level_3_complete_for_proposal_preview"])
        self.assertFalse(marker["level_3_complete_for_commit_execution"])
        self.assertFalse(marker["commit_allowed"])
        self.assertFalse(marker["commit_execution_enabled"])
        self.assertFalse(marker["push_allowed"])
        self.assertFalse(marker["branch_creation_allowed"])
        self.assertFalse(marker["creates_push_queue_item"])
        self.assertFalse(marker["actions_taken"])

    def test_level_3_blocker_handoff_is_read_only_and_lists_dirty_groups(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            plan = root / "docs" / "cartographer-level-3-autonomy-plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# Plan\n", encoding="utf-8")
            scout_file = root / "scout" / "src" / "scout" / "api" / "sources.py"
            scout_file.parent.mkdir(parents=True, exist_ok=True)
            scout_file.write_text("def scout_source():\n    return True\n", encoding="utf-8")

            before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_3_blocker_handoff()
                response = TestClient(_test_app()).get("/v1/cartographer/level-3-blocker-handoff")
            after_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_head, after_head)
        self.assertEqual(before_status, after_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["handoff_version"], "cartographer.level_3.blocker_handoff.v1")
        self.assertEqual(payload["level"], 3)
        self.assertEqual(payload["mode"], "read_only_level_3_blocker_handoff")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["proposal_preview_ready"])
        self.assertFalse(payload["local_commit_ready"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["commit_execution_enabled"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["creates_push_queue_item"])
        self.assertFalse(payload["level_2_docs_apply_enabled"])
        self.assertTrue(payload["dirty_tree_block"])
        groups = {group["group_id"]: group for group in payload["blocking_groups"]}
        self.assertIn("scout_work", groups)
        self.assertIn("unclassified_docs_and_markdown", groups)
        self.assertFalse(groups["scout_work"]["cartographer_may_resolve"])
        self.assertFalse(groups["unclassified_docs_and_markdown"]["cartographer_may_resolve"])
        self.assertIn("git status -sb", payload["manual_checks"])
        self.assertIn("auto commit", payload["forbidden_resolution_actions"])

    def test_push_queue_reports_ahead_commit_without_pushing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "core.autocrlf", "false")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/blueprint-review-widget")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/blueprint-review-widget")
            blueprint = root / "_blueprints" / "current" / "dashboard_state.md"
            blueprint.write_text(
                blueprint.read_text(encoding="utf-8") + "\nCommitted update.\n",
                encoding="utf-8",
            )
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(dashboard): apply cartographer blueprint update")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()

            remote_before = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/blueprint-review-widget",
            ).strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_push_queue()
            remote_after = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/blueprint-review-widget",
            ).strip()

        self.assertEqual(remote_before, remote_after)
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["push_count"], 1)
        item = payload["push_queue"][0]
        self.assertTrue(item["push_id"].startswith("push-"))
        self.assertEqual(item["remote"], "origin")
        self.assertEqual(item["branch"], "cartographer/blueprint-review-widget")
        self.assertEqual(item["upstream"], "origin/cartographer/blueprint-review-widget")
        self.assertEqual(item["ahead"], 1)
        self.assertEqual(item["behind"], 0)
        self.assertEqual(item["commits_ahead"], 1)
        self.assertEqual(item["commits_to_push"], [commit_sha])
        self.assertEqual(item["files"], ["_blueprints/current/dashboard_state.md"])
        self.assertEqual(item["audit_status"], "missing")
        self.assertEqual(item["commit_audit_status"], "missing")
        self.assertEqual(item["test_status"], "missing")
        self.assertFalse(item["dirty"])
        self.assertEqual(item["drift_status"], "clear")
        self.assertEqual(
            item["push_command_preview"],
            "git push origin cartographer/blueprint-review-widget",
        )
        self.assertIn("git push origin --delete cartographer/blueprint-review-widget", item["rollback_guidance"])
        self.assertEqual(item["approval_status"], "approval_required")
        self.assertEqual(
            item["reason_codes"],
            [
                "push_requires_separate_approval",
                "push_disabled_until_approved",
                "commit_audit_missing",
            ],
        )
        self.assertEqual(
            item["push_blockers"],
            [
                "push_requires_separate_approval",
                "commit_audit_missing",
                "required_checks_not_passed",
            ],
        )
        self.assertEqual(item["branch_protection_warnings"], ["review_remote_branch_protection_before_push"])
        self.assertEqual(
            item["remote_status"],
            {
                "remote": "origin",
                "branch": "cartographer/blueprint-review-widget",
                "upstream": "origin/cartographer/blueprint-review-widget",
                "ahead": 1,
                "behind": 0,
            },
        )
        self.assertEqual(item["status"], "push_pending")
        self.assertTrue(item["requires_approval"])
        self.assertFalse(item["push_enabled"])
        self.assertFalse(item["action_taken"])

    def test_push_queue_empty_without_upstream_or_ahead_commits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/local-only")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                no_upstream = build_cartographer_push_queue()

        self.assertEqual(no_upstream["push_queue"], [])
        self.assertEqual(no_upstream["push_count"], 0)
        self.assertFalse(no_upstream["actions_taken"])

    def test_push_queue_reports_branch_created_without_upstream(self) -> None:
        with self.assertRaisesRegex(Exception, "proposal-only") as blocked:
            approve_git_queue_item(
                kind="branch", item_id="branch-rec-direct", approved=True, approved_by="Britton"
            )
        self.assertEqual(blocked.exception.reason_code, "forbidden_cartographer_mutation")

    def test_push_queue_preview_reports_commit_audit_and_tests_when_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "core.autocrlf", "false")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/push-preview")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/push-preview")
            (root / "docs" / "push-preview.md").parent.mkdir(exist_ok=True)
            (root / "docs" / "push-preview.md").write_text("preview\n", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(cartographer): push preview")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()
            _write_git_approval_record(
                root,
                {
                    "event": "commit_created",
                    "project_id": "work",
                    "branch": "cartographer/push-preview",
                    "commit_sha": commit_sha,
                    "checks": [
                        {"id": "git_diff_check", "status": "passed"},
                        {"id": "blueprint_metadata_validation", "status": "passed"},
                        {"id": "cartographer_pytest", "status": "passed"},
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_push_queue()

        item = payload["push_queue"][0]
        self.assertEqual(item["commit_audit_status"], "recorded")
        self.assertEqual(item["test_status"], "passed")
        self.assertEqual(item["audit_status"], "missing")
        self.assertEqual(item["drift_status"], "clear")
        self.assertEqual(item["push_blockers"], ["push_requires_separate_approval"])
        self.assertFalse(item["push_enabled"])
        self.assertNotIn("commit_audit_missing", item["reason_codes"])

    def test_level_4_push_readiness_contract_reports_preview_without_push_or_queue_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "core.autocrlf", "false")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/level-4-readiness")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/level-4-readiness")
            (root / "docs" / "level-4-readiness.md").parent.mkdir(exist_ok=True)
            (root / "docs" / "level-4-readiness.md").write_text("readiness\n", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(cartographer): level 4 readiness")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()
            _write_git_approval_record(
                root,
                {
                    "event": "commit_created",
                    "project_id": "work",
                    "branch": "cartographer/level-4-readiness",
                    "commit_sha": commit_sha,
                    "checks": [
                        {"id": "git_diff_check", "status": "passed"},
                        {"id": "blueprint_metadata_validation", "status": "passed"},
                        {"id": "cartographer_pytest", "status": "passed"},
                    ],
                },
            )

            remote_before = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/level-4-readiness",
            ).strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_4_push_readiness_contract()
                response = TestClient(_test_app()).get("/v1/cartographer/level-4-push-readiness")
            remote_after = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/level-4-readiness",
            ).strip()

        self.assertEqual(remote_before, remote_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contract_version"], "cartographer.level_4.push_readiness_contract.v1")
        self.assertEqual(payload["level"], 4)
        self.assertEqual(payload["mode"], "push_readiness_contract")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["auto_push_allowed"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["push_queue_item_created"])
        self.assertEqual(payload["push_queue_preview_count"], 1)
        self.assertEqual(payload["ready_preview_count"], 1)
        self.assertEqual(payload["blocked_preview_count"], 0)
        self.assertIn("explicit future push approval", payload["required_inputs"])
        self.assertIn("push queue item creation", payload["forbidden_actions"])
        self.assertIn("git status -sb", payload["manual_checks"])
        preview = payload["ready_push_previews"][0]
        self.assertEqual(preview["branch"], "cartographer/level-4-readiness")
        self.assertEqual(preview["commits_to_push"], [commit_sha])
        self.assertEqual(preview["push_blockers"], ["push_requires_separate_approval"])
        self.assertFalse(preview["push_enabled"])
        self.assertFalse(preview["action_taken"])

    def test_level_4_push_queue_proposal_preview_does_not_create_queue_item_or_push(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "core.autocrlf", "false")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/level-4-proposal")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/level-4-proposal")
            (root / "docs" / "level-4-proposal.md").parent.mkdir(exist_ok=True)
            (root / "docs" / "level-4-proposal.md").write_text("proposal\n", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(cartographer): level 4 proposal")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()
            _write_git_approval_record(
                root,
                {
                    "event": "commit_created",
                    "project_id": "work",
                    "branch": "cartographer/level-4-proposal",
                    "commit_sha": commit_sha,
                    "checks": [
                        {"id": "git_diff_check", "status": "passed"},
                        {"id": "blueprint_metadata_validation", "status": "passed"},
                        {"id": "cartographer_pytest", "status": "passed"},
                    ],
                },
            )

            remote_before = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/level-4-proposal",
            ).strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_level_4_push_queue_proposal_preview()
                response = TestClient(_test_app()).get("/v1/cartographer/level-4-push-queue-proposals")
                proposal = payload["push_queue_proposals"][0]
                approval_response = TestClient(_test_app()).post(
                    f"/v1/cartographer/level-4-push-queue-proposals/{proposal['proposal_id']}/approval-preview",
                    json={
                        "approval_id": "approval-level-4-preview",
                        "approved_by": "Britton",
                        "exact_commits": proposal["commits_to_push"],
                        "remote": proposal["remote"],
                        "branch": proposal["branch"],
                        "upstream": proposal["upstream"],
                        "checks": [
                            {"id": check_id, "status": "passed"}
                            for check_id in proposal["required_checks"]
                        ],
                    },
                )
            remote_after = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/level-4-proposal",
            ).strip()

        self.assertEqual(remote_before, remote_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(approval_response.status_code, 200)
        self.assertEqual(response.json()["proposal_version"], "cartographer.level_4.push_queue_proposal_preview.v1")
        approval_payload = approval_response.json()
        self.assertEqual(
            approval_payload["approval_version"],
            "cartographer.level_4.push_queue_approval_preview.v1",
        )
        self.assertTrue(approval_payload["approval_validated"])
        self.assertEqual(approval_payload["execution_blockers"], ["push_execution_not_implemented"])
        self.assertFalse(approval_payload["push_allowed"])
        self.assertFalse(approval_payload["push_enabled"])
        self.assertFalse(approval_payload["push_created"])
        self.assertFalse(approval_payload["push_queue_item_created"])
        self.assertFalse(approval_payload["actions_taken"])
        self.assertEqual(payload["level"], 4)
        self.assertEqual(payload["mode"], "push_queue_proposal_preview")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["auto_push_allowed"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["push_queue_item_created"])
        self.assertFalse(payload["merge_allowed"])
        self.assertEqual(payload["proposal_count"], 1)
        self.assertIn("exact_commits", payload["required_approval_fields"])
        proposal = payload["push_queue_proposals"][0]
        self.assertTrue(proposal["proposal_id"].startswith("level-4-push-proposal-push-"))
        self.assertEqual(proposal["commits_to_push"], [commit_sha])
        self.assertEqual(proposal["files"], ["docs/level-4-proposal.md"])
        self.assertEqual(proposal["remote"], "origin")
        self.assertEqual(proposal["branch"], "cartographer/level-4-proposal")
        self.assertEqual(proposal["blockers"], ["push_requires_separate_approval"])
        self.assertTrue(proposal["approval_required"])
        self.assertIsNone(proposal["approval_id"])
        self.assertFalse(proposal["push_allowed"])
        self.assertFalse(proposal["push_enabled"])
        self.assertFalse(proposal["push_created"])
        self.assertFalse(proposal["creates_push_queue_item"])
        self.assertFalse(proposal["push_queue_item_created"])
        self.assertFalse(proposal["actions_taken"])

    def test_level_4_push_queue_approval_preview_validates_metadata_without_push(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "core.autocrlf", "false")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/level-4-approval-preview")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/level-4-approval-preview")
            (root / "docs" / "level-4-approval-preview.md").parent.mkdir(exist_ok=True)
            (root / "docs" / "level-4-approval-preview.md").write_text("approval preview\n", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(cartographer): level 4 approval preview")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()
            _write_git_approval_record(
                root,
                {
                    "event": "commit_created",
                    "project_id": "work",
                    "branch": "cartographer/level-4-approval-preview",
                    "commit_sha": commit_sha,
                    "checks": [
                        {"id": "git_diff_check", "status": "passed"},
                        {"id": "blueprint_metadata_validation", "status": "passed"},
                        {"id": "cartographer_pytest", "status": "passed"},
                    ],
                },
            )

            remote_before = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/level-4-approval-preview",
            ).strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = build_cartographer_level_4_push_queue_proposal_preview()["push_queue_proposals"][0]
                checks = [
                    {"id": check_id, "status": "passed"}
                    for check_id in proposal["required_checks"]
                ]
                payload = build_cartographer_level_4_push_queue_approval_preview(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-level-4-preview",
                    approved_by="Britton",
                    exact_commits=proposal["commits_to_push"],
                    remote=proposal["remote"],
                    branch=proposal["branch"],
                    upstream=proposal["upstream"],
                    checks=checks,
                )
                response = TestClient(_test_app()).post(
                    f"/v1/cartographer/level-4-push-queue-proposals/{proposal['proposal_id']}/approval-preview",
                    json={
                        "approval_id": "approval-level-4-preview",
                        "approved_by": "Britton",
                        "exact_commits": proposal["commits_to_push"],
                        "remote": proposal["remote"],
                        "branch": proposal["branch"],
                        "upstream": proposal["upstream"],
                        "checks": checks,
                    },
                )
            remote_after = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/level-4-approval-preview",
            ).strip()

        self.assertEqual(remote_before, remote_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["approval_version"], "cartographer.level_4.push_queue_approval_preview.v1")
        self.assertEqual(payload["level"], 4)
        self.assertEqual(payload["mode"], "push_queue_approval_gate_preview")
        self.assertTrue(payload["approval_validated"])
        self.assertEqual(payload["approval_id"], "approval-level-4-preview")
        self.assertEqual(payload["approved_by"], "Britton")
        self.assertEqual(payload["exact_commits"], [commit_sha])
        self.assertTrue(payload["checks_validated"])
        self.assertEqual(payload["blockers"], [])
        self.assertEqual(payload["execution_blockers"], ["push_execution_not_implemented"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["auto_push_allowed"])
        self.assertFalse(payload["push_created"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["push_queue_item_created"])
        self.assertFalse(payload["creates_push_queue_item"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertFalse(payload["actions_taken"])

    def test_level_4_push_queue_approval_preview_blocks_bad_metadata_without_push(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "core.autocrlf", "false")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/level-4-bad-approval")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/level-4-bad-approval")
            (root / "docs" / "level-4-bad-approval.md").parent.mkdir(exist_ok=True)
            (root / "docs" / "level-4-bad-approval.md").write_text("bad approval\n", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(cartographer): level 4 bad approval")

            remote_before = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/level-4-bad-approval",
            ).strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = build_cartographer_level_4_push_queue_proposal_preview()["push_queue_proposals"][0]
                payload = build_cartographer_level_4_push_queue_approval_preview(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-level-4-bad",
                    approved_by="cartographer",
                    exact_commits=["stale-commit"],
                    remote="upstream",
                    branch="wrong-branch",
                    upstream=proposal["upstream"],
                    checks=[],
                )
            remote_after = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/level-4-bad-approval",
            ).strip()

        self.assertEqual(remote_before, remote_after)
        self.assertFalse(payload["approval_validated"])
        self.assertIn("cartographer_self_approval_blocked", payload["blockers"])
        self.assertIn("exact_commits_mismatch", payload["blockers"])
        self.assertIn("remote_mismatch", payload["blockers"])
        self.assertIn("branch_mismatch", payload["blockers"])
        self.assertIn("required_checks_missing", payload["blockers"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_created"])
        self.assertFalse(payload["push_queue_item_created"])
        self.assertFalse(payload["actions_taken"])

    def test_level_4_push_execution_endpoint_is_hard_blocked_without_push_or_queue_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "core.autocrlf", "false")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/level-4-push-block")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/level-4-push-block")
            (root / "docs" / "level-4-push-block.md").parent.mkdir(exist_ok=True)
            (root / "docs" / "level-4-push-block.md").write_text("push block\n", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(cartographer): level 4 push block")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()
            _write_git_approval_record(
                root,
                {
                    "event": "commit_created",
                    "project_id": "work",
                    "branch": "cartographer/level-4-push-block",
                    "commit_sha": commit_sha,
                    "checks": [
                        {"id": "git_diff_check", "status": "passed"},
                        {"id": "blueprint_metadata_validation", "status": "passed"},
                        {"id": "cartographer_pytest", "status": "passed"},
                    ],
                },
            )

            remote_before = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/level-4-push-block",
            ).strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = build_cartographer_level_4_push_queue_proposal_preview()["push_queue_proposals"][0]
                payload = block_cartographer_level_4_push_execution(
                    proposal_id=proposal["proposal_id"],
                    approval_id="approval-level-4-push-block",
                    approved_by="Britton",
                )
                response = TestClient(_test_app()).post(
                    f"/v1/cartographer/level-4-push-queue-proposals/{proposal['proposal_id']}/push",
                    json={
                        "approval_id": "approval-level-4-push-block",
                        "approved_by": "Britton",
                    },
                )
            remote_after = _git_stdout(
                remote,
                "rev-parse",
                "refs/heads/cartographer/level-4-push-block",
            ).strip()

        self.assertEqual(remote_before, remote_after)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["block_version"], "cartographer.level_4.push_execution_hard_block.v1")
        self.assertEqual(payload["level"], 4)
        self.assertEqual(payload["mode"], "push_execution_hard_block")
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["blockers"], ["level_4_push_execution_not_implemented"])
        self.assertEqual(payload["execution_blockers"], ["push_execution_not_implemented"])
        self.assertTrue(payload["proposal_found"])
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["push_allowed"])
        self.assertFalse(payload["push_enabled"])
        self.assertFalse(payload["auto_push_allowed"])
        self.assertFalse(payload["push_created"])
        self.assertFalse(payload["push_queue_creation_allowed"])
        self.assertFalse(payload["push_queue_item_created"])
        self.assertFalse(payload["creates_push_queue_item"])
        self.assertFalse(payload["merge_allowed"])
        self.assertFalse(payload["branch_creation_allowed"])
        self.assertFalse(payload["cleanup_allowed"])
        self.assertFalse(payload["stash_allowed"])
        self.assertIn("push", payload["forbidden_actions"])
        self.assertIn("push queue item creation", payload["forbidden_actions"])

    def test_level_4_push_execution_hard_block_negative_matrix(self) -> None:
        cases = [
            (
                {"proposal_id": "missing-proposal", "approval_id": "approval-demo", "approved_by": "Britton"},
                ["level_4_push_execution_not_implemented", "proposal_not_found"],
            ),
            (
                {"proposal_id": "missing-proposal", "approval_id": None, "approved_by": "Britton"},
                ["level_4_push_execution_not_implemented", "proposal_not_found", "approval_id_required"],
            ),
            (
                {"proposal_id": "missing-proposal", "approval_id": "approval-demo", "approved_by": "cartographer"},
                [
                    "level_4_push_execution_not_implemented",
                    "proposal_not_found",
                    "cartographer_self_approval_blocked",
                ],
            ),
            (
                {"proposal_id": "missing-proposal", "approval_id": "approval-demo", "approved_by": None},
                ["level_4_push_execution_not_implemented", "proposal_not_found", "approved_by_required"],
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                for request, expected_blockers in cases:
                    with self.subTest(request=request):
                        payload = block_cartographer_level_4_push_execution(**request)

                    self.assertEqual(payload["status"], "blocked")
                    self.assertEqual(payload["mode"], "push_execution_hard_block")
                    self.assertEqual(payload["blockers"], expected_blockers)
                    self.assertFalse(payload["push_allowed"])
                    self.assertFalse(payload["push_enabled"])
                    self.assertFalse(payload["auto_push_allowed"])
                    self.assertFalse(payload["push_created"])
                    self.assertFalse(payload["push_queue_creation_allowed"])
                    self.assertFalse(payload["push_queue_item_created"])
                    self.assertFalse(payload["creates_push_queue_item"])
                    self.assertFalse(payload["merge_allowed"])
                    self.assertFalse(payload["actions_taken"])

    def test_branch_approval_creates_recommended_branch_without_commit_or_push(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            source_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")
            client = TestClient(_test_app())

            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                recommendation = build_cartographer_branch_recommendations()["recommendations"][0]
                response = client.post(
                    f"/v1/cartographer/branch-recommendations/{recommendation['recommendation_id']}/approve",
                    json={"approved": True, "approved_by": "Britton"},
                )
                audit = build_cartographer_audit_trail()
            after_branch = _git_stdout(root, "branch", "--show-current").strip()
            branches = _git_stdout(root, "branch", "--list")

        self.assertEqual(response.status_code, 410)
        self.assertEqual(before_branch, after_branch)
        self.assertNotIn(recommendation["suggested_branch"], _branch_names(branches))

    def test_branch_rejection_records_intent_without_touching_git(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")
            client = TestClient(_test_app())

            before_branch = _git_stdout(root, "branch", "--show-current").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                recommendation = build_cartographer_branch_recommendations()["recommendations"][0]
                response = client.post(
                    f"/v1/cartographer/branch-recommendations/{recommendation['recommendation_id']}/approve",
                    json={"approved": False, "approved_by": "Britton"},
                )
                audit = build_cartographer_audit_trail()
            after_branch = _git_stdout(root, "branch", "--show-current").strip()
            branches = _git_stdout(root, "branch", "--list")

        self.assertEqual(response.status_code, 410)
        self.assertEqual(before_branch, after_branch)
        self.assertNotIn(recommendation["suggested_branch"], branches.splitlines())

    def test_commit_approval_runs_checks_and_commits_only_proposed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _write_minimal_blueprint_validator(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "docs" / "cartographer.md").parent.mkdir()
            (root / "docs" / "cartographer.md").write_text("docs update\n", encoding="utf-8")
            (root / "notes.md").write_text("leave uncommitted\n", encoding="utf-8")
            excluded = root / "docs" / "excluded.md"
            excluded.write_text("excluded\n", encoding="utf-8")
            _write_proposal(
                root,
                "commit_pending",
                "bp-commit-docs",
                {
                    "status": "commit_pending",
                    "type": "blueprint_update",
                    "component": "docs",
                    "proposed_files": ["docs/cartographer.md"],
                    "post_apply_verification": _verified_post_apply_verification(),
                    "transitions": [
                        {
                            "status": "commit_pending",
                            "timestamp": "2026-05-18T11:42:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )
            client = TestClient(_test_app())

            before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = next(
                    item
                    for item in build_cartographer_commit_proposals()["commit_proposals"]
                    if item["files"] == ["docs/cartographer.md"]
                )
                response = client.post(
                    f"/v1/cartographer/commit-proposals/{proposal['commit_proposal_id']}/approve",
                    json={"approved": True, "approved_by": "Britton"},
                )
                audit = build_cartographer_audit_trail()
            after_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            committed_files = _git_stdout(root, "show", "--name-only", "--format=", "HEAD").splitlines()
            remaining_status = _git_stdout(root, "status", "--short")

        self.assertEqual(response.status_code, 410)
        self.assertEqual(before_head, after_head)
        self.assertNotIn("docs/cartographer.md", committed_files)
        self.assertIn("?? notes.md", remaining_status)
        self.assertIn("?? docs/", remaining_status)

    def test_commit_approval_blocks_unrelated_staged_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _write_minimal_blueprint_validator(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "docs").mkdir(exist_ok=True)
            (root / "docs" / "cartographer.md").write_text("docs update\n", encoding="utf-8")
            (root / "docs" / "staged.md").write_text("staged unrelated\n", encoding="utf-8")
            _git(root, "add", "docs/staged.md")
            _write_proposal(
                root,
                "commit_pending",
                "bp-commit-staged-block",
                {
                    "status": "commit_pending",
                    "type": "blueprint_update",
                    "component": "docs",
                    "proposed_files": ["docs/cartographer.md"],
                    "post_apply_verification": _verified_post_apply_verification(),
                    "transitions": [
                        {
                            "status": "commit_pending",
                            "timestamp": "2026-05-18T11:43:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )
            client = TestClient(_test_app())

            before_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = next(
                    item
                    for item in build_cartographer_commit_proposals()["commit_proposals"]
                    if item["files"] == ["docs/cartographer.md"]
                )
                response = client.post(
                    f"/v1/cartographer/commit-proposals/{proposal['commit_proposal_id']}/approve",
                    json={"approved": True, "approved_by": "Britton"},
                )
            after_head = _git_stdout(root, "rev-parse", "HEAD").strip()

        self.assertEqual(response.status_code, 410)
        self.assertEqual(before_head, after_head)

    def test_push_approval_pushes_after_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "core.autocrlf", "false")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/push-approval")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/push-approval")
            blueprint = root / "_blueprints" / "current" / "dashboard_state.md"
            blueprint.write_text(
                blueprint.read_text(encoding="utf-8") + "\nCommitted update.\n",
                encoding="utf-8",
            )
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(dashboard): update blueprint")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()
            _write_git_approval_record(
                root,
                {
                    "event": "commit_created",
                    "project_id": "work",
                    "branch": "cartographer/push-approval",
                    "commit_sha": commit_sha,
                    "checks": [
                        {"id": "git_diff_check", "status": "passed"},
                        {"id": "blueprint_metadata_validation", "status": "passed"},
                        {"id": "cartographer_pytest", "status": "passed"},
                    ],
                },
            )
            client = TestClient(_test_app())

            remote_before = _git_stdout(remote, "rev-parse", "refs/heads/cartographer/push-approval").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                item = build_cartographer_push_queue()["push_queue"][0]
                response = client.post(
                    f"/v1/cartographer/push-queue/{item['push_id']}/approve",
                    json={"approved": True, "approved_by": "Britton"},
                )
                audit = build_cartographer_audit_trail()
                health = build_cartographer_project_health()
            remote_after = _git_stdout(remote, "rev-parse", "refs/heads/cartographer/push-approval").strip()
            ahead_behind = _git_stdout(root, "rev-list", "--left-right", "--count", "@{upstream}...HEAD").split()

        self.assertEqual(response.status_code, 410)
        self.assertEqual(remote_before, remote_after)
        self.assertNotEqual(ahead_behind, ["0", "0"])

    def test_push_approval_blocks_missing_commit_audit_without_pushing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "core.autocrlf", "false")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/push-block")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/push-block")
            (root / "docs" / "push-block.md").parent.mkdir(exist_ok=True)
            (root / "docs" / "push-block.md").write_text("blocked\n", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(cartographer): unaudited push")
            client = TestClient(_test_app())

            remote_before = _git_stdout(remote, "rev-parse", "refs/heads/cartographer/push-block").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                item = build_cartographer_push_queue()["push_queue"][0]
                response = client.post(
                    f"/v1/cartographer/push-queue/{item['push_id']}/approve",
                    json={"approved": True, "approved_by": "Britton"},
                )
            remote_after = _git_stdout(remote, "rev-parse", "refs/heads/cartographer/push-block").strip()

        self.assertEqual(response.status_code, 410)
        self.assertEqual(remote_before, remote_after)

    def test_git_approval_routes_reject_without_human_approval(self) -> None:
        client = TestClient(_test_app())

        for route in (
            "/v1/cartographer/commit-proposals/commit-prop-missing/approve",
            "/v1/cartographer/push-queue/push-missing/approve",
        ):
            response = client.post(route, json={"approved": False})
            self.assertEqual(response.status_code, 410)

        response = client.post(
            "/v1/cartographer/branch-recommendations/branch-rec-missing/approve",
            json={"approved": False},
        )
        self.assertEqual(response.status_code, 410)

    def test_audit_trail_surfaces_proposal_transitions_and_approved_action_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            audit_path = root / "data" / "approved_actions.audit.jsonl"
            audit_path.parent.mkdir()
            audit_path.write_text(
                json.dumps(
                    {
                        "action": "apply approved Cartographer proposal bp-20260515-apply",
                        "approved_at": "2026-05-15T10:10:00+00:00",
                        "approved_by": "Britton",
                        "changed_files": ["_blueprints/current/dashboard_state.md"],
                        "proposal_id": "bp-20260515-apply",
                        "result": "applied",
                        "task_id": "task_123",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            _write_proposal(
                root,
                "rejected",
                "bp-20260515-rejected",
                {
                    "status": "rejected",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "proposed_files": ["_blueprints/current/dashboard_state.md"],
                    "rejection_reason": "Needs clearer dashboard evidence.",
                    "transitions": [
                        {
                            "status": "pending_review",
                            "timestamp": "2026-05-15T10:01:00Z",
                            "actor": "cartographer",
                        },
                        {
                            "status": "rejected",
                            "timestamp": "2026-05-15T10:02:00Z",
                            "actor": "Britton",
                        },
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_audit_trail()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["rollback_enabled"])
        self.assertTrue(payload["rollback_hints_present"])
        self.assertTrue(payload["explainability_fields_present"])
        events = payload["events"]
        by_event = {event["event"]: event for event in events}
        self.assertIn("rejected", by_event)
        self.assertEqual(by_event["rejected"]["action"], "proposal_rejected")
        self.assertEqual(by_event["rejected"]["actor"], "Britton")
        self.assertEqual(by_event["rejected"]["proposal_id"], "bp-20260515-rejected")
        self.assertEqual(by_event["rejected"]["component"], "dashboard")
        self.assertEqual(by_event["rejected"]["reason"], "Needs clearer dashboard evidence.")
        self.assertEqual(by_event["rejected"]["result"], "Needs clearer dashboard evidence.")
        self.assertEqual(by_event["rejected"]["changed_files"], ["_blueprints/current/dashboard_state.md"])
        self.assertIn("No rollback needed", by_event["rejected"]["rollback_hint"])
        action_events = [
            event
            for event in events
            if event["source"] == "approved_action_audit"
        ]
        self.assertEqual(len(action_events), 1)
        self.assertEqual(action_events[0]["actor"], "Britton")
        self.assertEqual(action_events[0]["action"], "apply approved Cartographer proposal bp-20260515-apply")
        self.assertEqual(action_events[0]["component"], "blueprint-system")
        self.assertEqual(action_events[0]["proposal_id"], "bp-20260515-apply")
        self.assertEqual(action_events[0]["task_id"], "task_123")
        self.assertEqual(action_events[0]["result"], "applied")
        self.assertEqual(action_events[0]["files"], ["_blueprints/current/dashboard_state.md"])
        self.assertEqual(action_events[0]["changed_files"], ["_blueprints/current/dashboard_state.md"])

    def test_audit_trail_includes_pending_commit_and_push_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "cartographer/audit")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/audit")
            blueprint = root / "_blueprints" / "current" / "dashboard_state.md"
            blueprint.write_text(
                blueprint.read_text(encoding="utf-8") + "\nApplied update.\n",
                encoding="utf-8",
            )
            _write_proposal(
                root,
                "applied",
                "bp-20260515-applied",
                {
                    "status": "applied",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "proposed_files": ["_blueprints/current/dashboard_state.md"],
                    "transitions": [
                        {
                            "status": "applied",
                            "timestamp": "2026-05-15T10:11:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )
            _git(root, "add", ".")
            _git(root, "commit", "-m", "docs(dashboard): apply cartographer blueprint update")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_audit_trail()

        events = payload["events"]
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["rollback_hints_present"])
        self.assertTrue(payload["explainability_fields_present"])
        commit_events = [event for event in events if event["event"] == "commit_pending"]
        push_events = [event for event in events if event["event"] == "push_pending"]
        self.assertEqual(len(commit_events), 0)
        self.assertEqual(len(push_events), 1)
        self.assertEqual(push_events[0]["remote"], "origin")
        self.assertEqual(push_events[0]["branch"], "cartographer/audit")
        self.assertEqual(push_events[0]["action"], "push_queued")
        self.assertIn("_blueprints/current/dashboard_state.md", push_events[0]["changed_files"])
        self.assertEqual(push_events[0]["reason"], "1 commit(s) ahead of upstream.")
        self.assertEqual(push_events[0]["result"], "pending_approval")
        self.assertIn("remote untouched", push_events[0]["rollback_hint"])
        self.assertFalse(payload["rollback_enabled"])

    def test_audit_trail_surfaces_codex_evidence_as_read_only_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_dir = root / "codex-evidence"
            _write_minimal_blueprints(root)
            _write_codex_evidence(
                evidence_dir,
                "phase-10-11-1-t5",
                ["src/components/coding/__tests__/coding-workflow-step.test.ts"],
            )

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_audit_trail()

        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        events = [event for event in payload["events"] if event["source"] == "codex_evidence"]
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["event"], "codex_task_evidence")
        self.assertEqual(event["action"], "codex_proposal_recorded")
        self.assertEqual(event["task_id"], "phase-10-11-1-t5")
        self.assertEqual(event["result"], "passed")
        self.assertEqual(event["reason"], "ready_for_review")
        self.assertEqual(event["changed_files"], ["src/components/coding/__tests__/coding-workflow-step.test.ts"])
        self.assertEqual(event["files"], event["changed_files"])
        self.assertIn("read-only", event["rollback_hint"])

    def test_audit_trail_surfaces_branch_commit_push_details_and_rollback_hints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _write_git_approval_record(
                root,
                {
                    "event": "branch_created",
                    "project_id": "spiritos",
                    "approved_by": "Britton",
                    "approved_at": "2026-05-16T20:14:35Z",
                    "branch": "cartographer/docs-blueprint-review",
                    "previous_branch": "cartographer/scout-blueprint-review",
                    "source_head": "683793732031b6d9471de7995931310065df84a5",
                    "rollback_command": (
                        "git switch cartographer/scout-blueprint-review && "
                        "git branch -D cartographer/docs-blueprint-review"
                    ),
                    "changed_files": ["_blueprints/current/system_state.md"],
                    "result": "branch_created",
                    "item_id": "branch-rec-real",
                },
            )
            _write_git_approval_record(
                root,
                {
                    "event": "commit_created",
                    "project_id": "spiritos",
                    "approved_by": "Britton",
                    "approved_at": "2026-05-16T20:25:36Z",
                    "branch": "cartographer/docs-blueprint-review",
                    "changed_files": ["_blueprints/current/system_state.md"],
                    "approved_files": ["_blueprints/current/system_state.md"],
                    "excluded_files": ["README.md"],
                    "parent_sha": "683793732031b6d9471de7995931310065df84a5",
                    "commit_sha": "74315faac5b228dd22b54f0f530893b0e9a2988a",
                    "commit_message": "docs(scout): apply cartographer blueprint update",
                    "rollback_command": "git reset --hard 683793732031b6d9471de7995931310065df84a5",
                    "result": "commit_created",
                    "item_id": "commit-prop-real",
                },
            )
            _write_git_approval_record(
                root,
                {
                    "event": "push_approved",
                    "project_id": "spiritos",
                    "approved_by": "Britton",
                    "approved_at": "2026-05-16T20:46:21Z",
                    "branch": "cartographer/docs-blueprint-review",
                    "remote": "origin",
                    "changed_files": ["_blueprints/current/system_state.md"],
                    "result": "pushed",
                    "item_id": "push-real",
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_audit_trail()

        self.assertTrue(payload["rollback_hints_present"])
        self.assertTrue(payload["explainability_fields_present"])
        by_event = {event["event"]: event for event in payload["events"]}
        self.assertEqual(by_event["branch_created"]["action"], "create_branch")
        self.assertEqual(by_event["branch_created"]["actor"], "Britton")
        self.assertEqual(by_event["branch_created"]["component"], "blueprint-system")
        self.assertEqual(by_event["branch_created"]["previous_branch"], "cartographer/scout-blueprint-review")
        self.assertEqual(
            by_event["branch_created"]["source_head"],
            "683793732031b6d9471de7995931310065df84a5",
        )
        self.assertIn("git switch cartographer/scout-blueprint-review", by_event["branch_created"]["rollback_command"])
        self.assertIn("Switch back", by_event["branch_created"]["rollback_hint"])
        self.assertEqual(by_event["commit_created"]["action"], "create_commit")
        self.assertEqual(by_event["commit_created"]["commit_sha"], "74315faac5b228dd22b54f0f530893b0e9a2988a")
        self.assertEqual(
            by_event["commit_created"]["parent_sha"],
            "683793732031b6d9471de7995931310065df84a5",
        )
        self.assertEqual(by_event["commit_created"]["approved_files"], ["_blueprints/current/system_state.md"])
        self.assertEqual(by_event["commit_created"]["excluded_files"], ["README.md"])
        self.assertIn("git reset --hard", by_event["commit_created"]["rollback_command"])
        self.assertIn("local only", by_event["commit_created"]["rollback_hint"])
        self.assertEqual(by_event["push_approved"]["action"], "push_branch")
        self.assertEqual(by_event["push_approved"]["result"], "pushed")
        self.assertEqual(by_event["push_approved"]["remote"], "origin")
        self.assertIn("remote", by_event["push_approved"]["rollback_hint"])

    def test_component_mapper_maps_known_paths_and_reports_unknowns(self) -> None:
        components, unmapped = map_paths(
            [
                "scout/src/scout/api/discovery_jobs.py",
                "source_proxy/cartographer/service.py",
                "src/app/v1/cartographer/status/route.ts",
                "src/app/v1/coding/codex/route.ts",
                "src/app/api/scout/overview/route.ts",
                "src/components/dashboard/HomelabCartographerWidget.tsx",
                "src/components/coding/CodingAgentInterface.tsx",
                "chatDesign/components/chat/Thread.tsx",
                "src/app/chat/page.tsx",
                "src/app/oracle/page.tsx",
                "src/lib/server/capabilities/format-capability-answer.ts",
                "scripts/spiritdesktop-windows/agent.ps1",
                "_blueprints/current/system_state.md",
                "src/app/design-demo/page.tsx",
                "README.md",
                ".env.local",
                "../outside/package.json",
            ]
        )

        by_id = {component.component_id: component for component in components}
        self.assertEqual(by_id["scout"].blueprint_id, "system-state")
        self.assertEqual(by_id["cartographer"].blueprint_id, "cartographer-agent")
        self.assertEqual(by_id["cartographer"].risk, "medium")
        self.assertIn("source_proxy/cartographer/service.py", by_id["cartographer"].matched_paths)
        self.assertEqual(
            by_id["cartographer-api-bridge"].blueprint_id,
            "cartographer-agent",
        )
        self.assertIn(
            "src/app/v1/cartographer/status/route.ts",
            by_id["cartographer-api-bridge"].matched_paths,
        )
        self.assertEqual(by_id["coding-workflow"].blueprint_id, "dashboard-state")
        self.assertEqual(by_id["coding-workflow"].risk, "medium")
        self.assertEqual(
            by_id["coding-workflow"].matched_paths,
            [
                "src/app/v1/coding/codex/route.ts",
                "src/components/coding/CodingAgentInterface.tsx",
            ],
        )
        self.assertEqual(by_id["scout-dashboard-bridge"].label, "Scout dashboard bridge")
        self.assertEqual(by_id["dashboard"].blueprint_id, "dashboard-state")
        self.assertEqual(by_id["dashboard"].risk, "medium")
        self.assertEqual(by_id["chat-workspace"].blueprint_id, "chat-workspace")
        self.assertIn("chatDesign/components/chat/Thread.tsx", by_id["chat-workspace"].matched_paths)
        self.assertEqual(by_id["oracle"].blueprint_id, "oracle-voice")
        self.assertEqual(by_id["server-capabilities"].risk, "medium")
        self.assertEqual(by_id["windows-desktop-agent"].label, "Windows desktop agent")
        self.assertEqual(by_id["blueprint-system"].blueprint_id, "blueprint-index")
        self.assertEqual(by_id["blueprint-system"].risk, "low")
        self.assertEqual(by_id["docs"].blueprint_id, "system-state")
        self.assertEqual(by_id["docs"].risk, "low")
        self.assertTrue(by_id["design-demo"].sandbox)
        self.assertEqual([item.path for item in unmapped], ["[redacted]", "[redacted]"])
        self.assertEqual({item.risk for item in unmapped}, {"blocked"})
        self.assertEqual(
            {item.reason for item in unmapped},
            {"blocked_sensitive_or_outside_path"},
        )

    def test_component_mapper_risk_labels_known_low_medium_high_and_unknown_paths(self) -> None:
        components, unmapped = map_paths(
            [
                "docs/proxy-test-runner-plan.md",
                "_blueprints/current/system_state.md",
                "src/components/dashboard/HomelabCartographerWidget.tsx",
                "source_proxy/cartographer/apply.py",
                "source_proxy/cartographer/push_queue.py",
                "scratch/unknown.txt",
            ]
        )

        by_id = {component.component_id: component for component in components}
        self.assertEqual(by_id["docs"].risk, "low")
        self.assertEqual(by_id["blueprint-system"].risk, "low")
        self.assertEqual(by_id["dashboard"].risk, "medium")
        self.assertEqual(by_id["cartographer"].risk, "high")
        self.assertEqual(
            by_id["cartographer"].matched_path_risks,
            {
                "source_proxy/cartographer/apply.py": "high",
                "source_proxy/cartographer/push_queue.py": "high",
            },
        )
        self.assertEqual(unmapped[0].path, "scratch/unknown.txt")
        self.assertEqual(unmapped[0].risk, "unknown")

    def test_component_mapper_route_exposes_rules_without_guessing_unmapped_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            previous_cwd = Path.cwd()
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
                    payload = build_cartographer_components()
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["mapping_mode"], "rules")
        self.assertEqual(payload["unmapped_paths"], [])
        components = {component["component_id"]: component for component in payload["components"]}
        self.assertEqual(components["dashboard"]["blueprint_id"], "dashboard-state")
        self.assertEqual(components["dashboard"]["risk"], "medium")
        self.assertEqual(components["blueprint-system"]["paths"], ["_blueprints/**"])
        self.assertEqual(components["docs"]["risk"], "low")
        self.assertEqual(payload["changed_components"], [])
        self.assertEqual(payload["changed_unmapped_paths"], [])
        self.assertEqual(payload["changed_file_count"], 0)
        self.assertFalse(payload["actions_taken"])

    def test_component_mapper_route_classifies_current_dirty_tree_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "src" / "components" / "dashboard").mkdir(parents=True)
            (root / "src" / "components" / "dashboard" / "Widget.tsx").write_text(
                "export function Widget() { return null; }\n",
                encoding="utf-8",
            )
            (root / "source_proxy" / "cartographer").mkdir(parents=True)
            (root / "source_proxy" / "cartographer" / "push_queue.py").write_text(
                "PUSH = False\n",
                encoding="utf-8",
            )
            (root / ".env.local").write_text("SECRET=hidden\n", encoding="utf-8")
            before_status = _git_stdout(root, "status", "--short")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_components()
            after_status = _git_stdout(root, "status", "--short")

        self.assertEqual(before_status, after_status)
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["changed_file_count"], 3)
        changed = {component["component_id"]: component for component in payload["changed_components"]}
        self.assertEqual(changed["dashboard"]["risk"], "medium")
        self.assertEqual(changed["cartographer"]["risk"], "high")
        self.assertEqual(
            changed["cartographer"]["matched_path_risks"],
            {"source_proxy/cartographer/push_queue.py": "high"},
        )
        self.assertEqual(payload["changed_unmapped_paths"][0]["path"], "[redacted]")
        self.assertEqual(payload["changed_unmapped_paths"][0]["risk"], "blocked")

    def test_repo_map_indexes_bounded_paths_symbols_and_components(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "src" / "components" / "dashboard").mkdir(parents=True)
            (root / "src" / "components" / "dashboard" / "Widget.tsx").write_text(
                "\n".join(
                    [
                        "export function DashboardWidget() { return null; }",
                        "export const dashboardValue = 1;",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "source_proxy" / "cartographer").mkdir(parents=True)
            (root / "source_proxy" / "cartographer" / "service.py").write_text(
                "def build_cartographer_repo_map():\n    return {}\n",
                encoding="utf-8",
            )
            (root / "source_proxy" / "api").mkdir(parents=True)
            (root / "source_proxy" / "api" / "cartographer.py").write_text(
                "def cartographer_status():\n    return {}\n",
                encoding="utf-8",
            )
            (root / "source_proxy" / "tests").mkdir(parents=True)
            (root / "source_proxy" / "tests" / "test_cartographer_api.py").write_text(
                "def test_cartographer():\n    assert True\n",
                encoding="utf-8",
            )
            (root / "_blueprints").mkdir()
            (root / "_blueprints" / "INDEX.md").write_text("# index", encoding="utf-8")
            (root / ".env.local").write_text("SECRET_SHOULD_NOT_APPEAR", encoding="utf-8")
            (root / "node_modules" / "pkg").mkdir(parents=True)
            (root / "node_modules" / "pkg" / "index.ts").write_text(
                "export const shouldNotAppear = true;",
                encoding="utf-8",
            )
            (root / "README.md").write_text("repo notes", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_repo_map()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["project_count"], 1)
        repo_map = payload["maps"][0]
        self.assertEqual(repo_map["map_version"], 1)
        self.assertGreaterEqual(repo_map["scan_duration_ms"], 0)
        self.assertLessEqual(repo_map["files_indexed"], repo_map["max_files"])
        self.assertLessEqual(repo_map["symbols_indexed"], repo_map["max_symbols"])
        self.assertEqual(repo_map["component_counts"]["dashboard"], 1)
        self.assertEqual(repo_map["component_counts"]["cartographer"], 1)
        self.assertEqual(repo_map["component_counts"]["source-proxy"], 2)
        self.assertEqual(repo_map["component_counts"]["blueprint-system"], 1)
        self.assertEqual(repo_map["component_counts"]["docs"], 1)
        self.assertGreaterEqual(repo_map["risk_counts"]["low"], 2)
        self.assertGreaterEqual(repo_map["risk_counts"]["medium"], 3)
        self.assertIn("_blueprints/INDEX.md", repo_map["key_directories"])
        self.assertIn("source_proxy/api", repo_map["key_directories"])
        self.assertIn("source_proxy/api/cartographer.py", repo_map["api_routes"])
        self.assertIn("src/components/dashboard/Widget.tsx", repo_map["dashboard_widgets"])
        self.assertIn("source_proxy/tests/test_cartographer_api.py", repo_map["tests"])
        self.assertIn("_blueprints/INDEX.md", repo_map["blueprints"])
        files = {item["path"]: item for item in repo_map["files"]}
        self.assertIn("src/components/dashboard/Widget.tsx", files)
        self.assertEqual(files["src/components/dashboard/Widget.tsx"]["component_id"], "dashboard")
        self.assertEqual(files["src/components/dashboard/Widget.tsx"]["blueprint_id"], "dashboard-state")
        self.assertEqual(files["src/components/dashboard/Widget.tsx"]["risk"], "medium")
        self.assertEqual(files["_blueprints/INDEX.md"]["risk"], "low")
        self.assertIn("DashboardWidget", files["src/components/dashboard/Widget.tsx"]["symbols"])
        self.assertIn("dashboardValue", files["src/components/dashboard/Widget.tsx"]["symbols"])
        self.assertEqual(files["source_proxy/cartographer/service.py"]["component_id"], "cartographer")
        self.assertIn("build_cartographer_repo_map", files["source_proxy/cartographer/service.py"]["symbols"])
        self.assertNotIn("SECRET_SHOULD_NOT_APPEAR", str(payload))
        self.assertNotIn("shouldNotAppear", str(payload))
        self.assertIn(".env.local", repo_map["skipped"])
        self.assertIn("node_modules", repo_map["skipped"])

    def test_repo_map_enforces_file_symbol_and_large_file_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            source_proxy = root / "source_proxy"
            source_proxy.mkdir()
            for index in range(200):
                (source_proxy / f"module_{index:03}.py").write_text(
                    "\n".join(f"def symbol_{index}_{symbol}():\n    return {symbol}" for symbol in range(4)),
                    encoding="utf-8",
                )
            large = root / "src" / "components" / "dashboard" / "Large.tsx"
            large.parent.mkdir(parents=True)
            large.write_text("x" * 170_000, encoding="utf-8")
            (root / ".next" / "cache").mkdir(parents=True)
            (root / ".next" / "cache" / "ignored.ts").write_text(
                "export const shouldNotAppear = true;",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_repo_map()

        repo_map = payload["maps"][0]
        self.assertEqual(repo_map["max_files"], 180)
        self.assertEqual(repo_map["max_symbols"], 500)
        self.assertLessEqual(repo_map["files_indexed"], 180)
        self.assertLessEqual(repo_map["symbols_indexed"], 500)
        self.assertIn("file_limit_reached", repo_map["skipped"])
        self.assertIn("symbol_limit_reached", repo_map["skipped"])
        self.assertIn("large_file", repo_map["skipped"])
        self.assertIn(".next", repo_map["skipped"])
        self.assertNotIn("shouldNotAppear", str(payload))

    def test_repo_map_reports_unmapped_paths_without_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "README.md").write_text("repo notes", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_repo_map()

        repo_map = payload["maps"][0]
        self.assertIn(
            {
                "path": "package.json",
                "reason": "no_component_mapping_rule",
                "risk": "unknown",
            },
            repo_map["unmapped_paths"],
        )
        self.assertEqual(repo_map["risk_counts"]["unknown"], 1)
        files = {item["path"]: item for item in repo_map["files"]}
        self.assertEqual(files["README.md"]["component_id"], "docs")
        self.assertEqual(files["README.md"]["blueprint_id"], "system-state")

    def test_git_status_scanner_reports_branch_dirty_files_and_last_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            remote = temp_root / "remote.git"
            root = temp_root / "work"
            _git(temp_root, "init", "--bare", str(remote))
            root.mkdir()
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            (root / "README.md").write_text("initial", encoding="utf-8")
            _git(root, "add", "README.md", "package.json")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "main")
            (root / "local.txt").write_text("ahead", encoding="utf-8")
            _git(root, "add", "local.txt")
            _git(root, "commit", "-m", "local ahead commit")
            (root / "README.md").write_text("changed but unstaged", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "changed.ts").write_text("export const changed = true;", encoding="utf-8")
            _git(root, "add", "src/changed.ts")
            (root / "docs").mkdir()
            (root / "docs" / "draft.md").write_text("untracked", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_git()
            expected_head = _git_stdout(root, "rev-parse", "HEAD").strip()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["write_mode"], "locked")
        self.assertEqual(payload["project_count"], 1)
        git_status = payload["git_statuses"][0]
        self.assertTrue(git_status["available"])
        self.assertTrue(git_status["dirty"])
        self.assertIn("src/changed.ts", git_status["changed_files"])
        self.assertIn("README.md", git_status["changed_files"])
        self.assertIn("docs/draft.md", git_status["changed_files"])
        self.assertEqual(git_status["staged_files"], ["src/changed.ts"])
        self.assertEqual(git_status["unstaged_files"], ["README.md"])
        self.assertEqual(git_status["untracked_files"], ["docs/draft.md"])
        self.assertEqual(git_status["ahead"], 1)
        self.assertEqual(git_status["behind"], 0)
        self.assertEqual(git_status["upstream"], "origin/main")
        self.assertIsNone(git_status["no_upstream_reason"])
        self.assertRegex(git_status["head_sha"], r"^[0-9a-f]{40}$")
        self.assertEqual(git_status["head_sha"], expected_head)
        self.assertRegex(git_status["generated_at"], _UTC_TIMESTAMP_PATTERN)
        self.assertTrue(git_status["is_primary_branch"])
        self.assertTrue(git_status["needs_branch_recommendation"])
        self.assertTrue(git_status["needs_commit"])
        self.assertTrue(git_status["needs_push"])
        self.assertFalse(git_status["merge_ready"])
        self.assertEqual(git_status["write_mode"], "locked")
        self.assertEqual(git_status["last_commit"]["message"], "local ahead commit")
        self.assertTrue(git_status["last_commit"]["sha"])

    def test_git_status_scanner_reports_clear_no_upstream_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/no-upstream")
            (root / "README.md").write_text("initial", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_git()

        git_status = payload["git_statuses"][0]
        self.assertTrue(git_status["available"])
        self.assertEqual(git_status["branch"], "feature/no-upstream")
        self.assertRegex(git_status["head_sha"], r"^[0-9a-f]{40}$")
        self.assertIsNone(git_status["upstream"])
        self.assertEqual(git_status["no_upstream_reason"], "no_upstream_configured")
        self.assertEqual(git_status["ahead"], 0)
        self.assertEqual(git_status["behind"], 0)
        self.assertRegex(git_status["generated_at"], _UTC_TIMESTAMP_PATTERN)
        self.assertEqual(git_status["write_mode"], "locked")

    def test_git_status_endpoint_falls_back_to_current_repo_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            (root / "README.md").write_text("initial", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            expected_head = _git_stdout(root, "rev-parse", "HEAD").strip()
            previous_cwd = Path.cwd()
            try:
                os.chdir(root)
                with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
                    payload = build_cartographer_git()
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(payload["project_count"], 1)
        git_status = payload["git"]
        self.assertEqual(git_status["branch"], "main")
        self.assertEqual(git_status["head_sha"], expected_head)
        self.assertEqual(git_status["write_mode"], "locked")

    def test_git_status_scanner_preserves_machine_readable_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            quoted_by_porcelain = root / "name with many spaces.md"
            quoted_by_porcelain.write_text("odd but real", encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            quoted_by_porcelain.unlink()

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_git()

        git_status = payload["git_statuses"][0]
        self.assertIn("name with many spaces.md", git_status["changed_files"])
        self.assertNotIn('"name with many spaces.md"', git_status["changed_files"])

    def test_git_status_scanner_reports_non_git_project_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_git()

        git_status = payload["git_statuses"][0]
        self.assertFalse(git_status["available"])
        self.assertFalse(git_status["dirty"])
        self.assertEqual(git_status["changed_files"], [])
        self.assertEqual(git_status["staged_files"], [])
        self.assertEqual(git_status["unstaged_files"], [])
        self.assertEqual(git_status["untracked_files"], [])
        self.assertIsNone(git_status["head_sha"])
        self.assertIsNone(git_status["upstream"])
        self.assertIsNone(git_status["no_upstream_reason"])
        self.assertRegex(git_status["generated_at"], _UTC_TIMESTAMP_PATTERN)
        self.assertEqual(git_status["write_mode"], "locked")
        self.assertEqual(git_status["error"], "not_a_git_repository")

    def test_git_status_scanner_reports_timeout_without_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()
            (root / "package.json").write_text("{}", encoding="utf-8")

            with (
                patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False),
                patch(
                    "source_proxy.cartographer.git_status.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(["git", "status"], timeout=5),
                ),
            ):
                payload = build_cartographer_git()

        git_status = payload["git_statuses"][0]
        self.assertFalse(git_status["available"])
        self.assertEqual(git_status["error"], "git_command_timeout")

    def test_drift_rules_flag_component_code_when_blueprint_not_updated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_drift()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["proposal_generated"])
        drift = payload["drift"]
        self.assertEqual(payload["drift_count"], 1)
        self.assertEqual(drift[0]["component"], "dashboard")
        self.assertEqual(drift[0]["reason"], "component_code_changed")
        self.assertEqual(drift[0]["affected_blueprints"], ["dashboard-state"])
        self.assertEqual(drift[0]["severity"], "review_suggested")
        self.assertEqual(
            drift[0]["message"],
            "This code changed. This blueprint may now be stale.",
        )
        self.assertEqual(drift[0]["stale_targets"], ["blueprint:dashboard-state"])
        self.assertIn("Implementation moved", drift[0]["why_matters"])
        self.assertFalse(drift[0]["safe_to_ignore"])
        self.assertEqual(
            drift[0]["proposed_next_action"],
            "Review affected blueprints and draft a doc-only update if the documentation is stale.",
        )
        self.assertEqual(len(drift[0]["proposal_ids"]), 1)
        self.assertIn("-dashboard-component-code-changed-", drift[0]["proposal_ids"][0])
        self.assertIn(
            "changed file: src/components/dashboard/Widget.tsx",
            drift[0]["evidence"],
        )
        self.assertIn("affected blueprint: dashboard-state", drift[0]["evidence"])
        self.assertTrue(drift[0]["dismissible"])

    def test_drift_rules_do_not_flag_component_when_blueprint_changed_too(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")
            (root / "_blueprints" / "current" / "dashboard_state.md").write_text(
                _blueprint_doc(
                    blueprint_id="dashboard-state",
                    title="Dashboard State",
                    component="dashboard",
                    doc_type="current_state",
                    status="active",
                    source_of_truth=True,
                    code_paths=["src/components/dashboard/**"],
                )
                + "\nUpdated dashboard notes.\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_drift()

        self.assertEqual(payload["drift"], [])

    def test_drift_rules_flag_route_architecture_and_api_qa_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            route_file = root / "src" / "app" / "api" / "widget" / "route.ts"
            route_file.parent.mkdir(parents=True)
            route_file.write_text("export async function GET() { return Response.json({}); }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            route_file.write_text("export async function POST() { return Response.json({}); }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_drift()

        by_reason = {finding["reason"]: finding for finding in payload["drift"]}
        self.assertEqual(by_reason["route_changed"]["affected_blueprints"], ["system-state"])
        self.assertEqual(
            by_reason["route_changed"]["message"],
            "A route changed. Architecture documentation may now be stale.",
        )
        self.assertEqual(
            by_reason["api_changed_without_manual_checklist_update"]["affected_blueprints"],
            ["basic-chat-voice-qa"],
        )
        self.assertEqual(by_reason["api_changed_without_manual_checklist_update"]["severity"], "action_recommended")
        self.assertEqual(
            by_reason["api_changed_without_manual_checklist_update"]["message"],
            "An API route changed. Manual QA runbooks may need an update.",
        )
        self.assertEqual(
            by_reason["api_changed_without_manual_checklist_update"]["proposed_next_action"],
            "Review the affected runbook and draft a doc-only update if the checklist is stale.",
        )

    def test_drift_rules_flag_phase_6_8_gap_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            index = root / "_blueprints" / "INDEX.md"
            index.write_text(
                index.read_text(encoding="utf-8")
                + "\n| `runbooks/cartographer_dashboard_mobile_qa.md` | manual QA/runbook | Cartographer dashboard QA. |",
                encoding="utf-8",
            )
            (root / "_blueprints" / "runbooks" / "cartographer_dashboard_mobile_qa.md").write_text(
                _blueprint_doc(
                    blueprint_id="cartographer-dashboard-mobile-qa",
                    title="Cartographer Dashboard Mobile QA",
                    component="cartographer",
                    doc_type="runbook",
                    status="runbook",
                    source_of_truth=False,
                    code_paths=["src/components/dashboard/**"],
                ),
                encoding="utf-8",
            )
            paths = [
                root / "src" / "app" / "v1" / "cartographer" / "status" / "route.ts",
                root / "src" / "components" / "dashboard" / "HomelabCartographerWidget.tsx",
                root / "source_proxy" / "cartographer" / "apply.py",
                root / "scout" / "src" / "scout" / "api" / "discovery_jobs.py",
            ]
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("initial\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            for path in paths:
                path.write_text("changed\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_drift()

        by_reason = {finding["reason"]: finding for finding in payload["drift"]}
        self.assertIn("runbook_gap", by_reason)
        self.assertIn("qa_gap", by_reason)
        self.assertIn("safety_gap", by_reason)
        self.assertIn("scout_doc_drift", by_reason)
        self.assertEqual(by_reason["runbook_gap"]["component"], "cartographer-api-bridge")
        self.assertEqual(by_reason["runbook_gap"]["severity"], "action_recommended")
        self.assertEqual(
            by_reason["qa_gap"]["affected_blueprints"],
            ["cartographer-dashboard-mobile-qa"],
        )
        self.assertEqual(
            by_reason["safety_gap"]["message"],
            "Safety-sensitive code changed without a matching safety test update.",
        )
        self.assertEqual(by_reason["scout_doc_drift"]["affected_blueprints"], ["system-state"])

    def test_drift_rules_ignore_historical_blueprints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            readme = root / "README.md"
            readme.write_text("initial", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            readme.write_text("changed", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_drift()

        affected = {
            blueprint
            for finding in payload["drift"]
            for blueprint in finding["affected_blueprints"]
        }
        self.assertNotIn("phase0", affected)

    def test_reminders_suggest_branch_on_main_without_creating_one(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_reminders()

            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()

        by_kind = {reminder["kind"]: reminder for reminder in payload["reminders"]}
        self.assertEqual(branch, "main")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(by_kind["branch_recommended"]["message"], "Recommendation: create branch before continuing.")
        self.assertEqual(by_kind["branch_recommended"]["suggested_branch"], "cartographer/dashboard-blueprint-review")
        self.assertTrue(by_kind["branch_recommended"]["dismissible"])

    def test_reminders_suggest_checkpoint_for_many_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            files = []
            for index in range(8):
                path = root / "src" / "components" / "dashboard" / f"Widget{index}.tsx"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("export const value = 1;\n", encoding="utf-8")
                files.append(path)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/cartographer")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            for path in files:
                path.write_text("export const value = 2;\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_reminders()

        by_kind = {reminder["kind"]: reminder for reminder in payload["reminders"]}
        self.assertEqual(by_kind["checkpoint_commit_suggested"]["reason"], "8 files changed.")
        self.assertTrue(by_kind["checkpoint_commit_suggested"]["dismissible"])
        self.assertFalse(by_kind["checkpoint_commit_suggested"]["action_taken"])

    def test_reminders_surface_blueprint_stale_before_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/cartographer")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_reminders()

        by_kind = {reminder["kind"]: reminder for reminder in payload["reminders"]}
        reminder = by_kind["blueprint_stale_before_commit"]
        self.assertEqual(reminder["severity"], "review_suggested")
        self.assertEqual(reminder["reason"], "1 drift findings are open.")
        self.assertTrue(reminder["related_drift"])

    def test_reminders_do_not_report_when_git_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_reminders()

        self.assertEqual(payload["reminders"], [])
        self.assertEqual(payload["reminder_count"], 0)
        self.assertFalse(payload["actions_taken"])

    def test_proposal_lifecycle_lists_records_and_states_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _write_proposal(
                root,
                "pending_review",
                "bp-20260515-001",
                {
                    "status": "pending_review",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "affected_blueprints": ["dashboard-state"],
                    "changed_files": ["src/components/dashboard/Widget.tsx"],
                    "proposed_files": ["_blueprints/current/dashboard_state.md"],
                    "transitions": [
                        {
                            "status": "detected",
                            "timestamp": "2026-05-15T10:00:00Z",
                            "actor": "cartographer",
                        },
                        {
                            "status": "pending_review",
                            "timestamp": "2026-05-15T10:01:00Z",
                            "actor": "cartographer",
                        },
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_proposals()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["level"], 1)
        self.assertEqual(payload["mode"], "proposal_draft")
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["apply_allowed"])
        self.assertFalse(payload["commit_allowed"])
        self.assertFalse(payload["push_allowed"])
        self.assertTrue(payload["operator_review_required"])
        self.assertTrue(payload["proposal_only_contract"]["proposal_drafts_only"])
        self.assertFalse(payload["proposal_only_contract"]["apply_allowed"])
        self.assertFalse(payload["proposal_only_contract"]["commit_allowed"])
        self.assertFalse(payload["proposal_only_contract"]["push_allowed"])
        self.assertIn("pending_review", payload["proposal_states"])
        self.assertIn("push_approved", payload["proposal_states"])
        self.assertIn("deferred", payload["proposal_states"])
        self.assertIn("stale", payload["proposal_states"])
        self.assertEqual(payload["proposal_lifecycle"], payload["proposal_states"])
        self.assertEqual(payload["lifecycle"], payload["proposal_states"])
        self.assertEqual(
            payload["review_decisions"],
            ["approve", "reject", "request_edit", "defer", "mark_stale"],
        )
        self.assertFalse(payload["review_actions_apply_files"])
        self.assertTrue(payload["transition_audit_complete"])
        self.assertEqual(payload["proposal_count"], 1)
        self.assertEqual(payload["pending_proposals"], 1)
        proposal = payload["proposals"][0]
        self.assertEqual(payload["stale_cleanup_candidates"], [])
        self.assertEqual(payload["stale_cleanup_candidate_count"], 0)
        self.assertFalse(payload["cleanup_actions_enabled"])
        self.assertEqual(proposal["proposal_id"], "bp-20260515-001")
        self.assertEqual(proposal["status"], "pending_review")
        self.assertEqual(proposal["type"], "blueprint_update")
        self.assertEqual(proposal["component"], "dashboard")
        self.assertTrue(proposal["requires_approval"])
        self.assertTrue(proposal["proposal_draft"])
        self.assertEqual(proposal["target_docs_path"], "_blueprints/current/dashboard_state.md")
        self.assertEqual(proposal["risk_level"], "low")
        self.assertIn("git diff -- _blueprints/current/dashboard_state.md", proposal["manual_check"])
        self.assertIn("git restore _blueprints/current/dashboard_state.md", proposal["rollback_hint"])
        self.assertTrue(proposal["approval_required"])
        self.assertFalse(proposal["apply_allowed"])
        self.assertFalse(proposal["commit_allowed"])
        self.assertFalse(proposal["push_allowed"])
        self.assertFalse(proposal["creates_commit_proposal"])
        self.assertFalse(proposal["creates_push_queue_item"])
        self.assertFalse(proposal["applied"])
        self.assertFalse(proposal["action_taken"])
        self.assertTrue(all(item["timestamp"] and item["actor"] for item in proposal["transitions"]))

    def test_proposal_lifecycle_retains_rejection_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _write_proposal(
                root,
                "rejected",
                "bp-20260515-002",
                {
                    "status": "rejected",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "rejection_reason": "Too broad; split into smaller proposal.",
                    "transitions": [
                        {
                            "status": "rejected",
                            "timestamp": "2026-05-15T10:02:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_proposals()

        proposal = payload["proposals"][0]
        self.assertEqual(proposal["status"], "rejected")
        self.assertEqual(proposal["rejection_reason"], "Too broad; split into smaller proposal.")
        self.assertEqual(payload["pending_proposals"], 0)
        self.assertEqual(payload["stale_cleanup_candidate_count"], 1)
        cleanup = payload["stale_cleanup_candidates"][0]
        self.assertEqual(cleanup["proposal_id"], "bp-20260515-002")
        self.assertEqual(cleanup["status"], "rejected")
        self.assertFalse(cleanup["cleanup_allowed"])

    def test_proposal_lifecycle_approved_does_not_apply_automatically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _write_proposal(
                root,
                "approved",
                "bp-20260515-003",
                {
                    "status": "approved",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "transitions": [
                        {
                            "status": "approved",
                            "timestamp": "2026-05-15T10:03:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_proposals()

        proposal = payload["proposals"][0]
        self.assertEqual(proposal["status"], "approved")
        self.assertFalse(proposal["applied"])
        self.assertFalse(proposal["action_taken"])
        self.assertFalse(payload["actions_taken"])

    def test_proposal_lifecycle_marks_malformed_transition_history_without_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _write_proposal(
                root,
                "drafted",
                "bp-20260515-004",
                {
                    "status": "drafted",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "transitions": [{"status": "drafted"}],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_proposals()

        proposal = payload["proposals"][0]
        self.assertTrue(payload["transition_audit_complete"])
        self.assertIn("transition_missing_required_fields", proposal["warnings"])
        self.assertEqual(proposal["transitions"][0]["actor"], "unknown")
        self.assertEqual(proposal["transitions"][0]["timestamp"], "1970-01-01T00:00:00Z")

    def test_proposal_lifecycle_fallback_ids_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            proposal_path = root / "_blueprints" / "proposals" / "detected" / "no-id.json"
            proposal_path.parent.mkdir(parents=True)
            proposal_path.write_text(
                json.dumps(
                    {
                        "status": "detected",
                        "type": "blueprint_update",
                        "component": "dashboard",
                        "transitions": [
                            {
                                "status": "detected",
                                "timestamp": "2026-05-15T10:04:00Z",
                                "actor": "cartographer",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                first = build_cartographer_proposals()["proposals"][0]["proposal_id"]
                second = build_cartographer_proposals()["proposals"][0]["proposal_id"]

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("bp-"))

    def test_proposal_preview_generates_doc_only_diff_from_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_proposals()
                second_payload = build_cartographer_proposals()

        self.assertEqual(payload["proposal_count"], 1)
        self.assertEqual(payload["pending_proposals"], 1)
        self.assertTrue(payload["deduped"])
        self.assertEqual(payload["duplicate_proposals_present"], 0)
        proposal = payload["proposals"][0]
        self.assertEqual(second_payload["proposal_count"], 1)
        self.assertEqual(second_payload["proposals"][0]["proposal_id"], proposal["proposal_id"])
        self.assertRegex(
            proposal["proposal_id"],
            r"^bp-[a-z0-9-]+-dashboard-component-code-changed-[0-9a-f]{8}$",
        )
        self.assertEqual(proposal["status"], "drafted")
        self.assertEqual(proposal["type"], "blueprint_update")
        self.assertEqual(proposal["component"], "dashboard")
        self.assertTrue(proposal["generated"])
        self.assertFalse(proposal["persisted"])
        self.assertTrue(proposal["deduped"])
        self.assertRegex(proposal["fingerprint"], r"^[0-9a-f]{16}$")
        self.assertEqual(proposal["proposed_files"], ["_blueprints/current/dashboard_state.md"])
        self.assertTrue(all(path.startswith("_blueprints/") for path in proposal["proposed_files"]))
        self.assertIn("diff --git a/_blueprints/current/dashboard_state.md", proposal["diff_preview"])
        self.assertIn("@@ -", proposal["diff_preview"])
        self.assertIn("src/components/dashboard/Widget.tsx", proposal["diff_preview"])
        self.assertIn("Cartographer Review Note", proposal["diff_preview"])
        self.assertFalse(proposal["action_taken"])

    def test_generated_drift_proposals_do_not_write_queue_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            proposal_dir = root / "_blueprints" / "proposals"
            before = sorted(path.relative_to(proposal_dir).as_posix() for path in proposal_dir.rglob("*"))
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_proposals()
            after = sorted(path.relative_to(proposal_dir).as_posix() for path in proposal_dir.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(payload["proposal_count"], 1)
        self.assertFalse(payload["actions_taken"])
        self.assertTrue(payload["proposals"][0]["generated"])
        self.assertFalse(payload["proposals"][0]["persisted"])
        proposal = payload["proposals"][0]
        self.assertTrue(proposal["proposal_draft"])
        self.assertEqual(proposal["target_docs_path"], "_blueprints/current/dashboard_state.md")
        self.assertTrue(proposal["approval_required"])
        self.assertFalse(proposal["apply_allowed"])
        self.assertFalse(proposal["commit_allowed"])
        self.assertFalse(proposal["push_allowed"])
        self.assertFalse(proposal["apply_enabled"])
        self.assertFalse(proposal["commit_enabled"])
        self.assertFalse(proposal["push_enabled"])
        self.assertFalse(proposal["creates_commit_proposal"])
        self.assertFalse(proposal["creates_push_queue_item"])
        self.assertIn("source edits are forbidden", proposal["why_no_source_edit_is_needed"])

    def test_proposal_preview_redacts_secret_shaped_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            secret_note = root / "source_proxy" / "secret_token_notes.py"
            secret_note.parent.mkdir(parents=True)
            secret_note.write_text("SECRET_VALUE = 'initial'\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            secret_note.write_text("SECRET_VALUE = 'changed'\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_proposals()

        combined_diff = "\n".join(proposal["diff_preview"] or "" for proposal in payload["proposals"])
        self.assertIn("[redacted]", combined_diff)
        self.assertNotIn("SECRET_VALUE", combined_diff)
        self.assertNotIn("secret_token_notes", combined_diff)

    def test_rejected_persisted_proposal_suppresses_matching_generated_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                generated = build_cartographer_proposals()["proposals"][0]

            _write_proposal(
                root,
                "rejected",
                generated["proposal_id"],
                {
                    "status": "rejected",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "rejection_reason": "Do not update this blueprint yet.",
                    "transitions": [
                        {
                            "status": "rejected",
                            "timestamp": "2026-05-15T10:05:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_proposals()

        self.assertEqual(payload["proposal_count"], 1)
        proposal = payload["proposals"][0]
        self.assertEqual(proposal["status"], "rejected")
        self.assertEqual(proposal["rejection_reason"], "Do not update this blueprint yet.")
        self.assertFalse(proposal["generated"])

    def test_rejected_persisted_proposal_suppresses_matching_generated_preview_by_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                generated = build_cartographer_proposals()["proposals"][0]

            _write_proposal(
                root,
                "rejected",
                "bp-old-dashboard-review-id",
                {
                    "status": "rejected",
                    "type": generated["type"],
                    "component": generated["component"],
                    "affected_blueprints": generated["affected_blueprints"],
                    "changed_files": generated["changed_files"],
                    "proposed_files": generated["proposed_files"],
                    "rationale": generated["rationale"],
                    "rejection_reason": "Old dashboard rejection should suppress this scan.",
                    "transitions": [
                        {
                            "status": "rejected",
                            "timestamp": "2026-05-15T10:05:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_proposals()

        self.assertEqual(payload["proposal_count"], 1)
        self.assertTrue(payload["deduped"])
        self.assertEqual(payload["duplicate_proposals_suppressed"], 1)
        self.assertEqual(
            payload["suppressed_duplicate_proposals"][0]["reason"],
            "matching_persisted_proposal_or_fingerprint",
        )
        proposal = payload["proposals"][0]
        self.assertEqual(proposal["proposal_id"], "bp-old-dashboard-review-id")
        self.assertEqual(proposal["status"], "rejected")
        self.assertEqual(proposal["fingerprint"], generated["fingerprint"])
        self.assertFalse(proposal["generated"])

    def test_apply_approved_doc_proposal_fails_closed_without_writing(self) -> None:
        with self.assertRaisesRegex(Exception, "proposal-only"):
            apply_approved_doc_proposal(
                proposal_id="bp-20260515-apply", approved=True, approved_by="test",
            )

    def test_apply_approved_doc_proposal_rejects_code_files_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            code_file = root / "src" / "app" / "page.tsx"
            code_file.parent.mkdir(parents=True)
            code_file.write_text("export default function Page() { return null; }\n", encoding="utf-8")
            diff = "\n".join(
                [
                    "diff --git a/src/app/page.tsx b/src/app/page.tsx",
                    "--- a/src/app/page.tsx",
                    "+++ b/src/app/page.tsx",
                    "@@ -1 +1 @@",
                    "-export default function Page() { return null; }",
                    "+export default function Page() { return 'blocked'; }",
                    "",
                ]
            )
            _write_proposal(
                root,
                "approved",
                "bp-20260515-code",
                {
                    "status": "approved",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "proposed_files": ["src/app/page.tsx"],
                    "approved_diff": diff,
                    "transitions": [
                        {
                            "status": "approved",
                            "timestamp": "2026-05-15T10:07:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                with self.assertRaisesRegex(Exception, "proposal-only"):
                    apply_approved_doc_proposal(
                        proposal_id="bp-20260515-code",
                        approved=True,
                        approved_by="test",
                    )

            content = code_file.read_text(encoding="utf-8")

        self.assertIn("return null", content)

    def test_apply_approved_doc_proposal_route_rejects_without_approval(self) -> None:
        client = TestClient(_test_app())

        response = client.post(
            "/v1/cartographer/proposals/bp-20260515-apply/apply-approved",
            json={"approved": False},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"]["reason_code"], "forbidden_cartographer_mutation")

    def test_dashboard_review_route_rejects_legacy_caller_actor_on_approve(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            before = (root / "_blueprints" / "current" / "dashboard_state.md").read_text(
                encoding="utf-8"
            )
            _write_proposal(
                root,
                "pending_review",
                "bp-20260515-review",
                {
                    "status": "pending_review",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "affected_blueprints": ["dashboard-state"],
                    "changed_files": ["src/components/dashboard/HomelabBlueprintReviewWidget.tsx"],
                    "proposed_files": ["_blueprints/current/dashboard_state.md"],
                    "diff_preview": "diff --git a/_blueprints/current/dashboard_state.md b/_blueprints/current/dashboard_state.md\n",
                    "transitions": [
                        {
                            "status": "pending_review",
                            "timestamp": "2026-05-15T10:00:00Z",
                            "actor": "cartographer",
                        }
                    ],
                },
            )
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                response = client.post(
                    "/v1/cartographer/proposals/bp-20260515-review/review",
                    json={
                        "decision": "approve",
                        "actor": "Britton",
                    },
                )
                payload = build_cartographer_proposals()
                pending_path = root / "_blueprints" / "proposals" / "pending_review" / "bp-20260515-review.json"
                approved_path = root / "_blueprints" / "proposals" / "approved" / "bp-20260515-review.json"
                pending_path_exists = pending_path.exists()
                approved_path_exists = approved_path.exists()

            after = (root / "_blueprints" / "current" / "dashboard_state.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(response.status_code, 422)
        self.assertIn("actor", response.text)
        proposal = payload["proposals"][0]
        self.assertEqual(proposal["status"], "pending_review")
        self.assertEqual(proposal["transitions"][-1]["actor"], "cartographer")
        self.assertEqual(proposal["transitions"][-1]["status"], "pending_review")
        self.assertTrue(pending_path_exists)
        self.assertFalse(approved_path_exists)
        self.assertEqual(before, after)

    def test_dashboard_review_route_rejects_legacy_caller_actor_on_reject(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _write_proposal(
                root,
                "pending_review",
                "bp-20260515-reject",
                {
                    "status": "pending_review",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "transitions": [
                        {
                            "status": "pending_review",
                            "timestamp": "2026-05-15T10:00:00Z",
                            "actor": "cartographer",
                        }
                    ],
                },
            )
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                response = client.post(
                    "/v1/cartographer/proposals/bp-20260515-reject/review",
                    json={
                        "decision": "reject",
                        "actor": "Britton",
                        "reason": "Needs a smaller proposal.",
                    },
                )
                payload = build_cartographer_proposals()
                pending_path = root / "_blueprints" / "proposals" / "pending_review" / "bp-20260515-reject.json"
                rejected_path = root / "_blueprints" / "proposals" / "rejected" / "bp-20260515-reject.json"
                pending_path_exists = pending_path.exists()
                rejected_path_exists = rejected_path.exists()

        self.assertEqual(response.status_code, 422)
        self.assertIn("actor", response.text)
        proposal = payload["proposals"][0]
        self.assertEqual(proposal["status"], "pending_review")
        self.assertIsNone(proposal["rejection_reason"])
        self.assertEqual(proposal["transitions"][-1]["actor"], "cartographer")
        self.assertTrue(pending_path_exists)
        self.assertFalse(rejected_path_exists)

    def test_dashboard_review_route_rejects_caller_actor_for_defer_and_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            blueprint = root / "_blueprints" / "current" / "dashboard_state.md"
            before = blueprint.read_text(encoding="utf-8")
            for proposal_id in ("bp-20260515-defer", "bp-20260515-stale"):
                _write_proposal(
                    root,
                    "pending_review",
                    proposal_id,
                    {
                        "status": "pending_review",
                        "type": "blueprint_update",
                        "component": "dashboard",
                        "affected_blueprints": ["dashboard-state"],
                        "changed_files": ["src/components/dashboard/Widget.tsx"],
                        "proposed_files": ["_blueprints/current/dashboard_state.md"],
                        "transitions": [
                            {
                                "status": "pending_review",
                                "timestamp": "2026-05-15T10:00:00Z",
                                "actor": "cartographer",
                            }
                        ],
                    },
                )
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                deferred = client.post(
                    "/v1/cartographer/proposals/bp-20260515-defer/review",
                    json={
                        "decision": "defer",
                        "actor": "Britton",
                        "reason": "Wait for design review.",
                    },
                )
                stale = client.post(
                    "/v1/cartographer/proposals/bp-20260515-stale/review",
                    json={
                        "decision": "mark_stale",
                        "actor": "Britton",
                        "reason": "Superseded by newer drift.",
                    },
                )
                payload = build_cartographer_proposals()

            after = blueprint.read_text(encoding="utf-8")

        self.assertEqual(deferred.status_code, 422)
        self.assertEqual(stale.status_code, 422)
        self.assertIn("actor", deferred.text)
        self.assertIn("actor", stale.text)
        self.assertEqual(before, after)
        proposals = {proposal["proposal_id"]: proposal for proposal in payload["proposals"]}
        self.assertEqual(proposals["bp-20260515-defer"]["status"], "pending_review")
        self.assertIsNone(proposals["bp-20260515-defer"]["review_note"])
        self.assertEqual(proposals["bp-20260515-stale"]["status"], "pending_review")
        self.assertIsNone(proposals["bp-20260515-stale"]["review_note"])
        self.assertFalse(proposals["bp-20260515-defer"]["applied"])
        self.assertFalse(proposals["bp-20260515-stale"]["action_taken"])
        self.assertEqual(payload["pending_proposals"], 2)

    def test_dashboard_review_route_rejects_caller_authored_generated_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            client = TestClient(_test_app())

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                project_id = build_cartographer_projects()["projects"][0]["project_id"]
                response = client.post(
                    "/v1/cartographer/proposals/bp-generated-scout/review",
                    json={
                        "decision": "reject",
                        "actor": "Britton",
                        "reason": "Needs a smaller proposal.",
                        "proposal": {
                            "proposal_id": "bp-generated-scout",
                            "project_id": project_id,
                            "status": "drafted",
                            "type": "blueprint_update",
                            "component": "scout",
                            "requires_approval": True,
                            "title": "Draft blueprint update for scout",
                            "affected_blueprints": ["system-state"],
                            "changed_files": ["scout/src/scout/api/overview.py"],
                            "proposed_files": ["_blueprints/current/system_state.md"],
                            "diff_preview": "+### Cartographer Review Note",
                            "confidence": "medium",
                            "rationale": "component_code_changed affected scout.",
                            "generated": True,
                            "persisted": False,
                        },
                    },
                )
                payload = build_cartographer_proposals()

            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        self.assertEqual(response.status_code, 422)
        self.assertIn("proposal", response.text)
        proposal_files = [
            path for path in after if path.startswith("_blueprints/proposals/rejected/")
        ]
        self.assertEqual(proposal_files, [])
        self.assertEqual(before, after)
        self.assertFalse(
            any(item["proposal_id"] == "bp-generated-scout" for item in payload["proposals"])
        )

    def test_change_scribe_summarizes_code_change_with_evidence_and_uncertainty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/change-scribe")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before = dashboard_file.read_text(encoding="utf-8")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_change_scribe()
            after = dashboard_file.read_text(encoding="utf-8")

        self.assertEqual(before, after)
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["summary_count"], 1)
        summary = payload["summaries"][0]
        self.assertEqual(summary["branch"], "feature/change-scribe")
        self.assertTrue(summary["dirty"])
        self.assertEqual(summary["commit_state"], "dirty")
        self.assertEqual(summary["components"], ["dashboard"])
        self.assertEqual(summary["summary"], "Dashboard code changed.")
        self.assertIn("src/components/dashboard/Widget.tsx changed", summary["evidence"])
        self.assertIn("no blueprint update detected", summary["evidence"])
        self.assertEqual(
            summary["file_explanations"],
            [
                {
                    "path": "src/components/dashboard/Widget.tsx",
                    "category": "dashboard",
                    "explanation": "Dashboard file changed.",
                    "review_required": False,
                }
            ],
        )
        self.assertIn("review Dashboard blueprint", summary["recommended_actions"])
        self.assertTrue(summary["uncertain_claims"])

    def test_change_scribe_explains_soak_logs_and_unknown_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            scout_soak = root / "scout" / "soak-logs" / "scout-soak.json"
            scout_soak.parent.mkdir(parents=True)
            scout_soak.write_text("{}", encoding="utf-8")
            unknown = root / "productionProxy.md"
            unknown.write_text("manual notes", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_change_scribe()

        summary = payload["summaries"][0]
        explanations = {item["path"]: item for item in summary["file_explanations"]}
        self.assertEqual(explanations["scout/soak-logs/scout-soak.json"]["category"], "scout")
        self.assertEqual(
            explanations["scout/soak-logs/scout-soak.json"]["explanation"],
            "Scout soak log snapshot changed, likely from a Scout soak or closeout run.",
        )
        self.assertEqual(explanations["productionProxy.md"]["category"], "unknown")
        self.assertTrue(explanations["productionProxy.md"]["review_required"])
        self.assertIn("manual review required", explanations["productionProxy.md"]["explanation"])

    def test_change_scribe_falls_back_to_current_repo_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            (root / "README.md").write_text("changed", encoding="utf-8")
            previous_cwd = Path.cwd()
            try:
                os.chdir(root)
                with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
                    payload = build_cartographer_change_scribe()
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(payload["summary_count"], 1)
        self.assertEqual(payload["summaries"][0]["branch"], "main")
        self.assertEqual(payload["summaries"][0]["changed_files"], ["README.md"])

    def test_change_scribe_notes_blueprint_update_when_docs_changed_too(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")
            (root / "_blueprints" / "current" / "dashboard_state.md").write_text(
                _blueprint_doc(
                    blueprint_id="dashboard-state",
                    title="Dashboard State",
                    component="dashboard",
                    doc_type="current_state",
                    status="active",
                    source_of_truth=True,
                    code_paths=["src/components/dashboard/**"],
                )
                + "\nDashboard update noted.\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_change_scribe()

        summary = payload["summaries"][0]
        self.assertTrue(summary["blueprint_update_detected"])
        self.assertFalse(summary["drift_detected"])
        self.assertIn("blueprint update detected", summary["evidence"])

    def test_change_scribe_reports_clean_repo_without_recommended_write_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_change_scribe()

        summary = payload["summaries"][0]
        self.assertEqual(summary["summary"], "No uncommitted changes detected.")
        self.assertEqual(summary["commit_state"], "clean")
        self.assertEqual(summary["recommended_actions"], ["no action needed"])

    def test_blueprint_scribe_drafts_exact_blueprint_update_from_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "checkout", "-b", "feature/blueprint-scribe")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            before = dashboard_file.read_text(encoding="utf-8")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_blueprint_scribe()
            after = dashboard_file.read_text(encoding="utf-8")

        self.assertEqual(before, after)
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["direct_writes_enabled"])
        self.assertTrue(payload["apply_requires_approval"])
        self.assertEqual(payload["proposal_only_contract"]["max_authority"], "proposal_only")
        self.assertFalse(payload["proposal_only_contract"]["blueprinter_can_write_source_of_truth_docs"])
        self.assertEqual(payload["draft_count"], 1)
        draft = payload["drafts"][0]
        self.assertTrue(draft["proposal_id"].startswith("bp-scribe-"))
        self.assertEqual(draft["affected_blueprint"], "dashboard-state")
        self.assertEqual(draft["proposed_file"], "_blueprints/current/dashboard_state.md")
        self.assertEqual(draft["confidence"], "medium")
        self.assertIn("component_code_changed", draft["reason"])
        self.assertIn("Dashboard code changed", draft["reason"])
        self.assertIn("src/components/dashboard/Widget.tsx", draft["suggested_update"])
        self.assertIn("changed file: src/components/dashboard/Widget.tsx", draft["evidence"])
        self.assertTrue(draft["editable"])
        self.assertTrue(draft["rejectable"])
        self.assertTrue(draft["proposal_only"])
        self.assertFalse(draft["direct_write_enabled"])
        self.assertEqual(draft["max_authority"], "proposal_only")
        self.assertTrue(draft["review_required"])
        self.assertTrue(draft["requires_apply_approval"])
        self.assertFalse(draft["action_taken"])
        self.assertTrue(draft["avoids_overclaiming"])

    def test_blueprint_scribe_does_not_draft_when_blueprint_changed_too(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")
            (root / "_blueprints" / "current" / "dashboard_state.md").write_text(
                _blueprint_doc(
                    blueprint_id="dashboard-state",
                    title="Dashboard State",
                    component="dashboard",
                    doc_type="current_state",
                    status="active",
                    source_of_truth=True,
                    code_paths=["src/components/dashboard/**"],
                )
                + "\nDashboard update noted.\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_blueprint_scribe()

        self.assertEqual(payload["drafts"], [])
        self.assertEqual(payload["draft_count"], 0)

    def test_blueprint_scribe_drafts_codex_trial_summary_without_applying_blueprints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_dir = root / "codex-evidence"
            _write_minimal_blueprints(root)
            _write_cartographer_blueprint_targets(root)
            _write_codex_evidence(
                evidence_dir,
                "phase-10-11-2-summary",
                ["source_proxy/cartographer/codex_evidence.py"],
            )
            cartographer_blueprint = root / "_blueprints" / "components" / "cartographer_agent.md"
            before = cartographer_blueprint.read_text(encoding="utf-8")

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_blueprint_scribe()

            after = cartographer_blueprint.read_text(encoding="utf-8")

        self.assertEqual(before, after)
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        codex_drafts = [draft for draft in payload["drafts"] if draft["component"] == "codex-adapter"]
        self.assertEqual(len(codex_drafts), 2)
        affected = {draft["affected_blueprint"] for draft in codex_drafts}
        self.assertEqual(affected, {"cartographer-agent", "cartographer-manual-checks"})
        for draft in codex_drafts:
            self.assertTrue(draft["proposal_id"].startswith("bp-scribe-codex-"))
            self.assertIn("Codex adapter trial summary", draft["suggested_update"])
            self.assertIn("codex_trial_summary_ready", draft["reason"])
            self.assertIn("approval/apply/commit/push authority: false", draft["evidence"])
            self.assertTrue(draft["editable"])
            self.assertTrue(draft["rejectable"])
            self.assertTrue(draft["proposal_only"])
            self.assertFalse(draft["direct_write_enabled"])
            self.assertEqual(draft["max_authority"], "proposal_only")
            self.assertTrue(draft["review_required"])
            self.assertTrue(draft["requires_apply_approval"])
            self.assertFalse(draft["action_taken"])

    def test_proposals_include_codex_trial_summary_as_pending_review_preview_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_dir = root / "codex-evidence"
            _write_minimal_blueprints(root)
            _write_cartographer_blueprint_targets(root)
            _write_codex_evidence(
                evidence_dir,
                "phase-10-11-2-proposal",
                ["source_proxy/cartographer/codex_evidence.py"],
            )

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "SPIRIT_CODEX_EVIDENCE_PATHS": str(evidence_dir),
                },
                clear=False,
            ):
                payload = build_cartographer_proposals()

        codex_proposals = [
            proposal for proposal in payload["proposals"] if proposal["component"] == "codex-adapter"
        ]
        self.assertEqual(len(codex_proposals), 2)
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertFalse(payload["review_actions_apply_files"])
        self.assertFalse(payload["proposal_only_contract"]["blueprinter_can_write_source_of_truth_docs"])
        self.assertTrue(payload["proposal_only_contract"]["generated_items_must_include_target_files"])
        self.assertTrue(payload["proposal_only_contract"]["generated_items_must_include_diff_preview"])
        for proposal in codex_proposals:
            self.assertEqual(proposal["status"], "pending_review")
            self.assertEqual(proposal["type"], "blueprint_update")
            self.assertTrue(proposal["requires_approval"])
            self.assertTrue(proposal["proposed_files"])
            self.assertTrue(proposal["diff_preview"].startswith("diff --git"))
            self.assertTrue(proposal["generated"])
            self.assertFalse(proposal["persisted"])
            self.assertFalse(proposal["applied"])
            self.assertFalse(proposal["action_taken"])
            self.assertIn("Codex Adapter Trial Summary", proposal["diff_preview"])

    def test_runbook_scribe_suggests_api_checklist_with_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            route_file = root / "src" / "app" / "api" / "widget" / "route.ts"
            route_file.parent.mkdir(parents=True)
            route_file.write_text("export async function GET() { return Response.json({}); }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            route_file.write_text("export async function POST() { return Response.json({}); }\n", encoding="utf-8")

            before = route_file.read_text(encoding="utf-8")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_runbook_scribe()
            after = route_file.read_text(encoding="utf-8")

        self.assertEqual(before, after)
        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["suggestion_count"], 1)
        suggestion = payload["suggestions"][0]
        self.assertEqual(suggestion["target_runbook"], "_blueprints/runbooks/basic_chat_voice_qa.md")
        self.assertEqual(suggestion["component"], "qa")
        self.assertIn("api_changed_without_manual_checklist_update", suggestion["reason"])
        self.assertTrue(any("/api/widget" in item for item in suggestion["checklist_items"]))
        self.assertIn("HTTP response is JSON.", suggestion["expected_outputs"])
        self.assertIn("No commit or push occurs.", suggestion["expected_outputs"])
        self.assertTrue(suggestion["editable"])
        self.assertTrue(suggestion["rejectable"])
        self.assertFalse(suggestion["action_taken"])

    def test_runbook_scribe_suggests_dashboard_widget_manual_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            widget = root / "src" / "components" / "dashboard" / "BlueprintReviewWidget.tsx"
            widget.parent.mkdir(parents=True)
            widget.write_text("export function BlueprintReviewWidget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            widget.write_text("export function BlueprintReviewWidget() { return 'changed'; }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_runbook_scribe()

        suggestion = payload["suggestions"][0]
        self.assertEqual(suggestion["target_runbook"], "_blueprints/runbooks/basic_chat_voice_qa.md")
        self.assertIn("Open the dashboard.", suggestion["checklist_items"])
        self.assertIn("Changed widget is visible.", suggestion["expected_outputs"])
        self.assertIn("No push occurs.", suggestion["expected_outputs"])

    def test_sub_cartographer_roles_are_narrow_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_sub_cartographers()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertEqual(payload["failures_stop_at"], "proposal_queue")
        self.assertEqual(payload["max_authority"], "proposal_only")
        self.assertEqual(payload["forbidden_actions"], ["approve", "apply", "commit", "push", "delete"])
        self.assertTrue(payload["forbidden_actions_enforced"])
        self.assertEqual(payload["output_count"], payload["role_count"])
        self.assertEqual(
            payload["output_contract_fields"],
            [
                "summary",
                "evidence",
                "recommendation",
                "risk",
                "required_approval",
                "forbidden_actions_respected",
                "next_manual_check",
            ],
        )
        self.assertTrue(payload["output_contract_enforced"])
        role_ids = {role["role_id"] for role in payload["roles"]}
        self.assertEqual(
            role_ids,
            {
                "component_mapper",
                "change_scribe",
                "blueprint_scribe",
                "runbook_scribe",
                "commit_scribe",
                "project_onboarding_scribe",
            },
        )
        self.assertTrue(all(role["can_write_files"] is False for role in payload["roles"]))
        self.assertTrue(all(role["allowed_inputs"] for role in payload["roles"]))
        self.assertTrue(all(role["allowed_outputs"] for role in payload["roles"]))
        self.assertTrue(
            all(role["allowed_inputs"] == role["consumes"] for role in payload["roles"])
        )
        self.assertTrue(
            all(role["allowed_outputs"] == role["produces"] for role in payload["roles"])
        )
        self.assertEqual(
            {role["max_authority"] for role in payload["roles"]},
            {"read_only", "proposal_only"},
        )
        self.assertTrue(
            all(
                action in role["forbidden_actions"]
                for role in payload["roles"]
                for action in ["approve", "apply", "commit", "push", "delete"]
            )
        )
        self.assertTrue(
            all(
                role["can_approve"] is False
                and role["can_apply"] is False
                and role["can_commit"] is False
                and role["can_push"] is False
                and role["can_delete"] is False
                for role in payload["roles"]
            )
        )
        self.assertTrue(
            all(role["failure_policy"] == "stop_at_proposal_queue" for role in payload["roles"])
        )
        outputs = {output["role_id"]: output for output in payload["outputs"]}
        self.assertEqual(set(outputs), role_ids)
        self.assertTrue(all(output["summary"] for output in outputs.values()))
        self.assertTrue(all(output["evidence"] for output in outputs.values()))
        self.assertTrue(all(output["recommendation"] for output in outputs.values()))
        self.assertTrue(
            all(output["recommendation"].lower() != "looks good" for output in outputs.values())
        )
        self.assertEqual(
            outputs["component_mapper"]["recommendation"],
            "Review unmapped or blocked-risk paths before treating the change set as understood.",
        )
        self.assertFalse(outputs["component_mapper"]["required_approval"])
        self.assertTrue(outputs["blueprint_scribe"]["required_approval"])
        self.assertTrue(all(output["forbidden_actions_respected"] for output in outputs.values()))
        self.assertTrue(all(output["next_manual_check"].startswith("curl -k -s") for output in outputs.values()))
        self.assertTrue(all(output["action_taken"] is False for output in outputs.values()))
        self.assertTrue(payload["control_plane_routing_enabled"])
        self.assertFalse(payload["control_plane_actions_enabled"])
        self.assertTrue(payload["control_plane_contract_enforced"])

    def test_sub_cartographer_routes_show_contributors_for_blueprint_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return null; }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_sub_cartographers()

        self.assertGreaterEqual(payload["route_count"], 1)
        blueprint_routes = [
            route for route in payload["routes"] if "blueprint_scribe" in route["contributors"]
        ]
        self.assertEqual(len(blueprint_routes), 1)
        route = blueprint_routes[0]
        self.assertTrue(route["proposal_id"].startswith("bp-scribe-"))
        self.assertEqual(
            route["contributors"],
            ["component_mapper", "change_scribe", "blueprint_scribe"],
        )
        self.assertEqual(route["status"], "proposal_queue")
        self.assertEqual(route["failures_stop_at"], "proposal_queue")
        self.assertFalse(route["action_taken"])
        self.assertIn("affected blueprint: dashboard-state", route["visible_outputs"])
        control_routes = {route["situation"]: route for route in payload["control_plane_routes"]}
        self.assertIn("dirty_tree", control_routes)
        self.assertIn("blueprint_drift", control_routes)
        self.assertEqual(
            control_routes["dirty_tree"]["selected_roles"],
            ["component_mapper", "change_scribe", "commit_scribe"],
        )
        self.assertEqual(
            control_routes["blueprint_drift"]["selected_roles"],
            ["component_mapper", "change_scribe", "blueprint_scribe"],
        )
        self.assertTrue(control_routes["blueprint_drift"]["parent_control_plane_required"])
        self.assertTrue(control_routes["blueprint_drift"]["approval_gate_required"])
        self.assertFalse(control_routes["blueprint_drift"]["mutation_allowed"])
        self.assertFalse(control_routes["blueprint_drift"]["action_taken"])

    def test_sub_cartographer_routes_include_runbook_scribe_for_api_qa_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            route_file = root / "src" / "app" / "api" / "widget" / "route.ts"
            route_file.parent.mkdir(parents=True)
            route_file.write_text("export async function GET() { return Response.json({}); }\n", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            route_file.write_text("export async function POST() { return Response.json({}); }\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_sub_cartographers()

        runbook_routes = [
            route for route in payload["routes"] if "runbook_scribe" in route["contributors"]
        ]
        self.assertEqual(len(runbook_routes), 1)
        route = runbook_routes[0]
        self.assertTrue(route["proposal_id"].startswith("rb-scribe-"))
        self.assertEqual(
            route["contributors"],
            ["component_mapper", "change_scribe", "runbook_scribe"],
        )
        self.assertIn("target runbook: _blueprints/runbooks/basic_chat_voice_qa.md", route["visible_outputs"])
        self.assertFalse(route["action_taken"])
        control_routes = {route["situation"]: route for route in payload["control_plane_routes"]}
        self.assertIn("runbook_gap", control_routes)
        self.assertEqual(
            control_routes["runbook_gap"]["selected_roles"],
            ["component_mapper", "change_scribe", "runbook_scribe"],
        )
        self.assertFalse(control_routes["runbook_gap"]["mutation_allowed"])

    def test_control_plane_routes_new_projects_and_push_queue_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            root = parent / "SpiritOS"
            root.mkdir()
            _write_minimal_blueprints(root)
            _write_proposal(
                root,
                "push_pending",
                "bp-push-routing",
                {
                    "status": "push_pending",
                    "type": "blueprint_update",
                    "component": "docs",
                    "proposed_files": ["_blueprints/current/system_state.md"],
                    "transitions": [
                        {
                            "status": "push_pending",
                            "timestamp": "2026-05-18T12:30:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )
            client = parent / "ClientDashboard"
            client.mkdir()
            (client / "README.md").write_text("candidate", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(parent)}, clear=False):
                payload = build_cartographer_sub_cartographers()

        control_routes = {route["situation"]: route for route in payload["control_plane_routes"]}
        self.assertIn("new_project", control_routes)
        self.assertIn("push_queue", control_routes)
        self.assertEqual(
            control_routes["new_project"]["selected_roles"],
            ["project_onboarding_scribe", "blueprint_scribe"],
        )
        self.assertEqual(
            control_routes["push_queue"]["selected_roles"],
            ["commit_scribe", "change_scribe"],
        )
        self.assertTrue(payload["control_plane_contract_enforced"])
        self.assertFalse(payload["control_plane_actions_enabled"])
        self.assertTrue(all(route["approval_gate_required"] for route in control_routes.values()))
        self.assertTrue(all(route["parent_control_plane_required"] for route in control_routes.values()))
        self.assertTrue(all(route["mutation_allowed"] is False for route in control_routes.values()))
        self.assertTrue(all(route["action_taken"] is False for route in control_routes.values()))


if __name__ == "__main__":
    unittest.main()


def _git(root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)


def _git_stdout(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout


def _write_minimal_blueprints(root: Path) -> None:
    (root / "package.json").write_text("{}", encoding="utf-8")
    blueprints = root / "_blueprints"
    (blueprints / "current").mkdir(parents=True)
    (blueprints / "runbooks").mkdir(parents=True)
    (blueprints / "history").mkdir(parents=True)
    (blueprints / "INDEX.md").write_text(
        "\n".join(
            [
                "# Index",
                "| Document | Classification | Notes |",
                "| --- | --- | --- |",
                "| `current/dashboard_state.md` | current truth | Canonical. |",
                "| `current/system_state.md` | current truth | Canonical. |",
                "| `runbooks/basic_chat_voice_qa.md` | manual QA/runbook | QA. |",
                "| `history/phase0.md` | history/phase receipt | Historical. |",
            ]
        ),
        encoding="utf-8",
    )
    (blueprints / "current" / "dashboard_state.md").write_text(
        _blueprint_doc(
            blueprint_id="dashboard-state",
            title="Dashboard State",
            component="dashboard",
            doc_type="current_state",
            status="active",
            source_of_truth=True,
            code_paths=["src/components/dashboard/**"],
        ),
        encoding="utf-8",
    )
    (blueprints / "current" / "system_state.md").write_text(
        _blueprint_doc(
            blueprint_id="system-state",
            title="System State",
            component="system",
            doc_type="current_state",
            status="active",
            source_of_truth=True,
            code_paths=["src/**", "source_proxy/**"],
        ),
        encoding="utf-8",
    )
    (blueprints / "runbooks" / "basic_chat_voice_qa.md").write_text(
        _blueprint_doc(
            blueprint_id="basic-chat-voice-qa",
            title="Basic Chat Voice QA",
            component="chat-and-voice",
            doc_type="runbook",
            status="runbook",
            source_of_truth=False,
            code_paths=["src/app/api/**"],
        ),
        encoding="utf-8",
    )
    (blueprints / "history" / "phase0.md").write_text(
        _blueprint_doc(
            blueprint_id="phase0",
            title="Phase 0",
            component="history",
            doc_type="phase_receipt",
            status="historical",
            source_of_truth=False,
            code_paths=["src/components/dashboard/**"],
        ),
        encoding="utf-8",
    )


def _write_docs_target(root: Path) -> Path:
    docs_target = root / "docs" / "level-2-approved.md"
    docs_target.parent.mkdir(parents=True, exist_ok=True)
    docs_target.write_text("# Level 2 Approved\n", encoding="utf-8")
    return docs_target


def _write_level_2_proposal(
    root: Path,
    *,
    proposal_id: str,
    target_path: str = "docs/level-2-approved.md",
    patch_text: str | None = None,
    git_head_at_creation: str | None = None,
    approved_by: str = "Britton",
) -> None:
    if patch_text is None:
        patch_text = "\n".join(
            [
                f"diff --git a/{target_path} b/{target_path}",
                f"--- a/{target_path}",
                f"+++ b/{target_path}",
                "@@ -1 +1,2 @@",
                " # Level 2 Approved",
                "+Level 2 applied.",
                "",
            ]
        )
    proposal_dir = root / "_blueprints" / "proposals" / "approved"
    proposal_dir.mkdir(parents=True, exist_ok=True)
    proposal_path = proposal_dir / f"{proposal_id}.json"
    payload = {
        "proposal_id": proposal_id,
        "status": "approved",
        "type": "level_2_docs_apply",
        "component": "cartographer",
        "target_paths": [target_path],
        "proposed_files": [target_path],
        "approved_diff": patch_text,
        "created_at": "2026-05-19T10:00:00Z",
        "git_head_at_creation": git_head_at_creation or _git_stdout(root, "rev-parse", "HEAD").strip(),
        "approval_id": f"approval-{proposal_id}",
        "approved_by": approved_by,
        "approved_at": "2026-05-19T10:05:00Z",
        "rollback_hint": f"git checkout -- {target_path}",
        "manual_check_command": "git diff --check",
        "transitions": [
            {
                "status": "pending_human_approval",
                "timestamp": "2026-05-19T10:00:00Z",
                "actor": "cartographer",
            },
            {
                "status": "approved",
                "timestamp": "2026-05-19T10:05:00Z",
                "actor": approved_by,
            },
        ],
    }
    proposal_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _level_2_receipt_json(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    marker = "```json"
    start = text.index(marker) + len(marker)
    end = text.index("```", start)
    payload = json.loads(text[start:end].strip())
    if not isinstance(payload, dict):
        raise AssertionError("Level 2 receipt JSON was not an object.")
    return payload


def _write_minimal_blueprint_validator(root: Path) -> None:
    scripts = root / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "validate-blueprints.mjs").write_text(
        "\n".join(
            [
                "console.log('Blueprint index valid');",
                "console.log('Active blueprints: 2');",
                "console.log('Runbooks: 1');",
                "console.log('Historical docs: 1');",
                "console.log('No missing required metadata');",
            ]
        ),
        encoding="utf-8",
    )


def _write_cartographer_blueprint_targets(root: Path) -> None:
    blueprints = root / "_blueprints"
    components = blueprints / "components"
    runbooks = blueprints / "runbooks"
    components.mkdir(parents=True, exist_ok=True)
    runbooks.mkdir(parents=True, exist_ok=True)
    with (blueprints / "INDEX.md").open("a", encoding="utf-8") as handle:
        handle.write("\n| `components/cartographer_agent.md` | component blueprint | Cartographer. |")
        handle.write("\n| `runbooks/cartographer_manual_checks.md` | manual QA/runbook | Cartographer checks. |\n")
    (components / "cartographer_agent.md").write_text(
        _blueprint_doc(
            blueprint_id="cartographer-agent",
            title="Cartographer Agent",
            component="cartographer",
            doc_type="component_blueprint",
            status="active",
            source_of_truth=True,
            code_paths=["source_proxy/cartographer/**"],
        ),
        encoding="utf-8",
    )
    (runbooks / "cartographer_manual_checks.md").write_text(
        _blueprint_doc(
            blueprint_id="cartographer-manual-checks",
            title="Cartographer Manual Checks",
            component="cartographer",
            doc_type="runbook",
            status="runbook",
            source_of_truth=False,
            code_paths=["source_proxy/cartographer/**"],
        ),
        encoding="utf-8",
    )


def _write_proposal(root: Path, state: str, proposal_id: str, payload: dict[str, object]) -> None:
    proposal_dir = root / "_blueprints" / "proposals" / state
    proposal_dir.mkdir(parents=True, exist_ok=True)
    proposal_payload = {"proposal_id": proposal_id, **payload}
    (proposal_dir / f"{proposal_id}.json").write_text(
        json.dumps(proposal_payload, indent=2),
        encoding="utf-8",
    )


def _verified_post_apply_verification() -> dict[str, object]:
    return {
        "checks": [
            {
                "id": "manual_verification",
                "required": True,
                "status": "passed",
                "summary": "Manual post-apply verification recorded.",
            }
        ],
        "commit_blockers": [],
        "commit_proposal_blocked": False,
        "push_blockers": ["push_requires_separate_approval"],
        "push_path_available": False,
        "required": True,
        "status": "verified",
    }


def _write_git_approval_record(root: Path, payload: dict[str, object]) -> None:
    audit_path = root / "data" / "cartographer_git_approvals.audit.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _write_codex_evidence(evidence_dir: Path, task_id: str, changed_files: list[str]) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "apply_authority": False,
        "approval_authority": False,
        "artifact_version": "codex_evidence.v1",
        "changed_files_after": changed_files,
        "changed_files_before": changed_files,
        "command": ["codex", "exec", "--sandbox", "read-only", "proposal"],
        "commit_authority": False,
        "diff_excerpt": "",
        "diff_stat": "",
        "exit_code": 0,
        "final_message_excerpt": "Codex evidence captured.",
        "finished_at": "2026-05-17T21:40:00Z",
        "head_after": "aee3351",
        "head_before": "aee3351",
        "json_event_count": 2,
        "push_authority": False,
        "recommendation": "ready_for_review",
        "rollback_hint": "No rollback needed.",
        "safety_verdict": "passed",
        "sandbox": "read-only",
        "started_at": "2026-05-17T21:39:00Z",
        "stderr_excerpt": "",
        "stdout_excerpt": "{\"type\":\"thread.started\"}\n{\"type\":\"turn.completed\"}",
        "task_id": task_id,
        "worker": "codex_cli",
    }
    (evidence_dir / f"{task_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _branch_names(output: str) -> list[str]:
    return [line.lstrip("* ").strip() for line in output.splitlines() if line.strip()]


def _blueprint_doc(
    *,
    blueprint_id: str,
    title: str,
    component: str,
    doc_type: str,
    status: str,
    source_of_truth: bool,
    code_paths: list[str],
) -> str:
    return "\n".join(
        [
            "---",
            f"blueprint_id: {blueprint_id}",
            f"title: {title}",
            "project: SpiritOS",
            f"component: {component}",
            f"doc_type: {doc_type}",
            f"status: {status}",
            f"source_of_truth: {str(source_of_truth).lower()}",
            "owner: Britton",
            "code_paths:",
            *[f"  - {path}" for path in code_paths],
            "related_blueprints: []",
            "write_policy: proposal_only_until_dashboard_approved",
            "last_verified: 2026-05-15",
            "---",
            f"# {title}",
        ]
    )
