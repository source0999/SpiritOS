from __future__ import annotations

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
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["approval_available"])
        self.assertFalse(payload["apply_available"])
        self.assertFalse(payload["actions_taken"])
        self.assertGreater(payload["proposal_count"], 0)
        proposal = payload["proposals"][0]
        self.assertTrue(proposal["dry_run"])
        self.assertFalse(proposal["approval_available"])
        self.assertFalse(proposal["apply_available"])
        self.assertFalse(proposal["would_write_files"])
        self.assertFalse(proposal["action_taken"])
        self.assertIn("diff --git", proposal["diff_preview"])

    def test_docs_autopilot_apply_is_blocked_by_default_without_writing_docs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
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
                    "CARTOGRAPHER_DOCS_AUTOPILOT_ENABLED": "false",
                    "CARTOGRAPHER_DOCS_AUTOPILOT_DAILY_CAP": "0",
                    "CARTOGRAPHER_AUTOPILOT_KILL_SWITCH": "true",
                },
                clear=False,
            ):
                payload = run_cartographer_docs_autopilot_apply()

        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
        self.assertIn("docs_autopilot_enabled", payload["blockers"])
        self.assertFalse((root / "docs" / "cartographer-autopilot-receipt.md").exists())

    def test_docs_autopilot_apply_writes_one_docs_receipt_after_all_gates_pass(self) -> None:
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
            _git(root, "checkout", "-b", "cartographer/docs-autopilot")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "cartographer/docs-autopilot")
            head_before = _git_stdout(root, "rev-parse", "HEAD").strip()

            with patch.dict(
                os.environ,
                {
                    "SPIRIT_PROJECT_PATH": str(root),
                    "CARTOGRAPHER_DOCS_AUTOPILOT_ENABLED": "true",
                    "CARTOGRAPHER_DOCS_AUTOPILOT_DAILY_CAP": "1",
                    "CARTOGRAPHER_AUTOPILOT_KILL_SWITCH": "false",
                },
                clear=False,
            ):
                payload = run_cartographer_docs_autopilot_apply()
                audit = build_cartographer_audit_trail()
                blocked_second = run_cartographer_docs_autopilot_apply()

            head_after = _git_stdout(root, "rev-parse", "HEAD").strip()
            ahead_behind = _git_stdout(root, "rev-list", "--left-right", "--count", "@{upstream}...HEAD").split()
            receipt = root / "docs" / "cartographer-autopilot-receipt.md"
            receipt_exists = receipt.exists()
            receipt_text = receipt.read_text(encoding="utf-8") if receipt_exists else ""

        self.assertEqual(payload["status"], "applied")
        self.assertTrue(payload["write_actions_enabled"])
        self.assertTrue(payload["actions_taken"])
        self.assertEqual(payload["changed_files"], ["docs/cartographer-autopilot-receipt.md"])
        self.assertEqual(payload["audit_event"], "autopilot_docs_apply")
        self.assertFalse(payload["committed"])
        self.assertFalse(payload["pushed"])
        self.assertEqual(head_before, head_after)
        self.assertEqual(ahead_behind, ["0", "0"])
        self.assertTrue(receipt_exists)
        self.assertIn("committed: false", receipt_text)
        events = [event for event in audit["events"] if event["event"] == "autopilot_docs_apply"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["changed_files"], ["docs/cartographer-autopilot-receipt.md"])
        self.assertEqual(blocked_second["status"], "blocked")
        self.assertIn("daily_cap_available", blocked_second["blockers"])

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
        self.assertEqual(payload["level9_status"], "GREEN")
        self.assertEqual(payload["observed_days"], 7)
        self.assertEqual(payload["cycle_count"], 7)
        self.assertFalse(payload["write_actions_enabled"])
        self.assertFalse(payload["actions_taken"])
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

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "starter_blueprints_written")
        self.assertTrue(body["write_actions_enabled"])
        self.assertEqual(
            body["created_files"],
            ["docs/blueprint.md", "docs/runbook.md", "docs/progress.md"],
        )
        self.assertFalse(body["committed"])
        self.assertFalse(body["pushed"])
        self.assertTrue(body["actions_taken"])
        self.assertEqual(head_before, head_after)
        self.assertIn("docs/blueprint.md", after)
        self.assertIn("docs/runbook.md", after)
        self.assertIn("docs/progress.md", after)
        self.assertNotIn("_blueprints/INDEX.md", after)
        self.assertEqual(readme_after, "candidate readme stays unchanged")
        self.assertNotEqual(before, after)
        events = [event for event in audit["events"] if event["event"] == "starter_blueprints_written"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["actor"], "Britton")
        self.assertEqual(
            events[0]["changed_files"],
            ["docs/blueprint.md", "docs/runbook.md", "docs/progress.md"],
        )

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
                with self.assertRaisesRegex(Exception, "approved must be true"):
                    write_cartographer_starter_blueprints(
                        proposal_id=proposal["proposal_id"],
                        approved=False,
                        approved_by="Britton",
                    )

        self.assertFalse((child / "docs").exists())

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

    def test_approved_low_risk_cleanup_deletes_only_approved_files_and_audits(self) -> None:
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

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "cleanup_applied")
        self.assertTrue(body["write_actions_enabled"])
        self.assertTrue(body["deletion_enabled"])
        self.assertTrue(body["cleanup_actions_enabled"])
        self.assertTrue(body["actions_taken"])
        self.assertEqual(
            body["deleted_files"],
            [
                "scout/soak-logs/scout-soak-one.json",
                "scout/soak-logs/scout-soak-two.json",
            ],
        )
        self.assertEqual(body["deleted_file_count"], 2)
        self.assertFalse(body["committed"])
        self.assertFalse(body["pushed"])
        self.assertFalse(low_one_exists)
        self.assertFalse(low_two_exists)
        self.assertTrue(medium_exists)
        self.assertTrue(high_exists)
        self.assertTrue(blocked_exists)
        self.assertIn("No deletion has occurred", body["rollback_instructions"][0])
        cleanup_events = [event for event in audit["events"] if event["event"] == "low_risk_cleanup_applied"]
        self.assertEqual(len(cleanup_events), 1)
        self.assertEqual(cleanup_events[0]["action"], "delete_low_risk_clutter")
        self.assertEqual(cleanup_events[0]["actor"], "Britton")
        self.assertEqual(cleanup_events[0]["changed_files"], body["deleted_files"])

    def test_low_risk_cleanup_rejects_without_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "scout" / "soak-logs").mkdir(parents=True)
            low_path = root / "scout" / "soak-logs" / "scout-soak-one.json"
            low_path.write_text("{}\n", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                proposal = build_cartographer_clutter_proposals()["proposals"][0]
                with self.assertRaisesRegex(Exception, "approved must be true"):
                    apply_cartographer_clutter_proposal(
                        proposal_id=proposal["proposal_id"],
                        approved=False,
                        approved_by="Britton",
                    )
            low_path_exists = low_path.exists()

        self.assertTrue(low_path_exists)

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
            _git(root, "checkout", "-b", "main")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            _git(root, "remote", "add", "origin", str(remote))
            _git(root, "push", "-u", "origin", "main")
            dashboard_file = root / "src" / "components" / "dashboard" / "Widget.tsx"
            dashboard_file.parent.mkdir(parents=True)
            dashboard_file.write_text("export function Widget() { return 'changed'; }\n", encoding="utf-8")
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                recommendation = build_cartographer_branch_recommendations()["recommendations"][0]
                approve_git_queue_item(
                    kind="branch",
                    item_id=recommendation["recommendation_id"],
                    approved=True,
                    approved_by="Britton",
                )
            _git(root, "add", "src/components/dashboard/Widget.tsx")
            _git(root, "commit", "-m", "feat(dashboard): update dashboard")
            commit_sha = _git_stdout(root, "rev-parse", "HEAD").strip()

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_push_queue()

        self.assertEqual(payload["push_count"], 1)
        item = payload["push_queue"][0]
        self.assertEqual(item["remote"], "origin")
        self.assertEqual(item["branch"], recommendation["suggested_branch"])
        self.assertIsNone(item["upstream"])
        self.assertEqual(item["ahead"], 1)
        self.assertEqual(item["behind"], 0)
        self.assertEqual(item["commits_ahead"], 1)
        self.assertEqual(item["commits_to_push"], [commit_sha])
        self.assertEqual(item["files"], ["src/components/dashboard/Widget.tsx"])
        self.assertEqual(item["push_command_preview"], f"git push -u origin {recommendation['suggested_branch']}")
        self.assertEqual(
            item["reason_codes"],
            [
                "push_requires_separate_approval",
                "push_disabled_until_approved",
                "commit_audit_missing",
                "no_upstream_push_would_set_upstream",
            ],
        )
        self.assertEqual(
            item["branch_protection_warnings"],
            [
                "review_remote_branch_protection_before_push",
                "new_remote_branch_may_not_have_protection_rules",
            ],
        )

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

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "branch_created")
        self.assertEqual(body["approval_kind"], "branch")
        self.assertTrue(body["branch_created"])
        self.assertFalse(body["commit_created"])
        self.assertFalse(body["push_ran"])
        self.assertTrue(body["safety"]["branch_creation_enabled"])
        self.assertEqual(body["previous_branch"], before_branch)
        self.assertEqual(body["source_head"], source_head)
        self.assertEqual(
            body["rollback_command"],
            f"git switch {before_branch} && git branch -D {recommendation['suggested_branch']}",
        )
        self.assertEqual(after_branch, recommendation["suggested_branch"])
        self.assertIn(recommendation["suggested_branch"], _branch_names(branches))
        branch_events = [
            event for event in audit["events"] if event["event"] == "branch_created"
        ]
        self.assertEqual(len(branch_events), 1)
        event = branch_events[0]
        self.assertEqual(event["actor"], "Britton")
        self.assertEqual(event["branch"], recommendation["suggested_branch"])
        self.assertEqual(event["previous_branch"], before_branch)
        self.assertEqual(event["source_head"], source_head)
        self.assertEqual(
            event["rollback_command"],
            f"git switch {before_branch} && git branch -D {recommendation['suggested_branch']}",
        )
        self.assertEqual(event["source"], "git_approval_record")

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

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "branch_rejected")
        self.assertFalse(body["branch_created"])
        self.assertFalse(body["commit_created"])
        self.assertFalse(body["push_ran"])
        self.assertEqual(before_branch, after_branch)
        self.assertNotIn(recommendation["suggested_branch"], branches.splitlines())
        self.assertTrue(
            any(
                event["event"] == "branch_rejected"
                and event["actor"] == "Britton"
                and event["branch"] == recommendation["suggested_branch"]
                for event in audit["events"]
            )
        )

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

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "commit_created")
        self.assertEqual(body["approval_kind"], "commit")
        self.assertFalse(body["branch_created"])
        self.assertTrue(body["commit_created"])
        self.assertFalse(body["push_ran"])
        self.assertTrue(body["safety"]["commit_enabled"])
        self.assertNotEqual(before_head, after_head)
        self.assertEqual(body["commit_sha"], after_head)
        self.assertEqual(body["parent_sha"], before_head)
        self.assertEqual(body["commit_message"], proposal["suggested_message"])
        self.assertEqual(body["approved_files"], ["docs/cartographer.md"])
        self.assertIn("docs/excluded.md", body["excluded_files"])
        self.assertEqual(body["rollback_command"], f"git reset --hard {before_head}")
        self.assertTrue(all(check["status"] == "passed" for check in body["checks"]))
        self.assertEqual(committed_files, ["docs/cartographer.md"])
        self.assertIn("?? notes.md", remaining_status)
        self.assertIn("?? docs/excluded.md", remaining_status)
        commit_events = [event for event in audit["events"] if event["event"] == "commit_created"]
        self.assertEqual(len(commit_events), 1)
        event = commit_events[0]
        self.assertEqual(event["actor"], "Britton")
        self.assertEqual(event["source"], "git_approval_record")
        self.assertEqual(event["commit_sha"], after_head)
        self.assertEqual(event["parent_sha"], before_head)
        self.assertEqual(event["approved_files"], ["docs/cartographer.md"])
        self.assertIn("docs/excluded.md", event["excluded_files"])
        self.assertEqual(event["rollback_command"], f"git reset --hard {before_head}")

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

        self.assertEqual(response.status_code, 422)
        self.assertEqual(before_head, after_head)
        self.assertEqual(response.json()["detail"]["reason_code"], "unrelated_staged_files_present")

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

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "pushed")
        self.assertEqual(body["approval_kind"], "push")
        self.assertFalse(body["branch_created"])
        self.assertFalse(body["commit_created"])
        self.assertTrue(body["push_ran"])
        self.assertTrue(body["safety"]["push_enabled"])
        self.assertEqual(body["commits_to_push"], [commit_sha])
        self.assertEqual(body["push_command_preview"], "git push origin cartographer/push-approval")
        self.assertNotEqual(remote_before, remote_after)
        self.assertEqual(ahead_behind, ["0", "0"])
        project = health["projects"][0]
        self.assertEqual(project["push_audit_status"], "recorded")
        self.assertNotIn("push audit missing", project["merge_blockers"])
        self.assertTrue(
            any(
                event["event"] == "push_approved"
                and event["actor"] == "Britton"
                and event["result"] == "pushed"
                and event["source"] == "git_approval_record"
                for event in audit["events"]
            )
        )
        self.assertTrue(
            any(
                event["event"] == "push_completed"
                and event["actor"] == "Britton"
                and event["result"] == "push_completed"
                and event["source"] == "git_approval_record"
                for event in audit["events"]
            )
        )

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

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"]["reason_code"], "commit_audit_missing")
        self.assertEqual(remote_before, remote_after)

    def test_git_approval_routes_reject_without_human_approval(self) -> None:
        client = TestClient(_test_app())

        for route in (
            "/v1/cartographer/commit-proposals/commit-prop-missing/approve",
            "/v1/cartographer/push-queue/push-missing/approve",
        ):
            response = client.post(route, json={"approved": False})
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()["detail"]["reason_code"], "approval_required")

        response = client.post(
            "/v1/cartographer/branch-recommendations/branch-rec-missing/approve",
            json={"approved": False},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"]["reason_code"], "approval_item_not_found")

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
        self.assertFalse(payload["actions_taken"])
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

    def test_apply_approved_doc_proposal_applies_and_verifies_blueprint_only_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_minimal_blueprints(root)
            _write_minimal_blueprint_validator(root)
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "initial commit")
            diff = "\n".join(
                [
                    "diff --git a/_blueprints/current/dashboard_state.md b/_blueprints/current/dashboard_state.md",
                    "--- a/_blueprints/current/dashboard_state.md",
                    "+++ b/_blueprints/current/dashboard_state.md",
                    "@@ -17,3 +17,5 @@ last_verified: 2026-05-15",
                    " ---",
                    " # Dashboard State",
                    "+",
                    "+Cartographer approved doc apply note.",
                    "",
                ]
            )
            _write_proposal(
                root,
                "approved",
                "bp-20260515-apply",
                {
                    "status": "approved",
                    "type": "blueprint_update",
                    "component": "dashboard",
                    "affected_blueprints": ["dashboard-state"],
                    "changed_files": ["src/components/dashboard/HomelabBlueprintReviewWidget.tsx"],
                    "proposed_files": ["_blueprints/current/dashboard_state.md"],
                    "approved_diff": diff,
                    "transitions": [
                        {
                            "status": "approved",
                            "timestamp": "2026-05-15T10:06:00Z",
                            "actor": "Britton",
                        }
                    ],
                },
            )

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = apply_approved_doc_proposal(
                    proposal_id="bp-20260515-apply",
                    approved=True,
                    approved_by="test",
                )
                proposals = build_cartographer_proposals()
                audit = build_cartographer_audit_trail()

            content = (root / "_blueprints" / "current" / "dashboard_state.md").read_text(
                encoding="utf-8"
            )
            approved_path = root / "_blueprints" / "proposals" / "approved" / "bp-20260515-apply.json"
            applied_path = root / "_blueprints" / "proposals" / "applied" / "bp-20260515-apply.json"
            approved_path_exists = approved_path.exists()
            applied_path_exists = applied_path.exists()
            backup_root = root / payload["execution"]["backup_root"]
            backup_manifest = json.loads(
                (root / payload["execution"]["audit"]["backup_manifest"]).read_text(encoding="utf-8")
            )
            approved_diff_copy = (root / payload["execution"]["audit"]["approved_diff_path"]).read_text(
                encoding="utf-8"
            )
            backup_root_exists = backup_root.is_dir()

        self.assertEqual(payload["status"], "applied")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["applied_files"], ["_blueprints/current/dashboard_state.md"])
        self.assertEqual(payload["changed_files"], ["_blueprints/current/dashboard_state.md"])
        self.assertFalse(payload["committed"])
        self.assertFalse(payload["pushed"])
        self.assertIn("Cartographer approved doc apply note.", content)
        self.assertTrue(payload["verification"]["allowed_files_passed"])
        self.assertTrue(payload["verification"]["markdown_validation_passed"])
        self.assertTrue(payload["verification"]["blueprint_metadata_validation_passed"])
        self.assertTrue(payload["verification"]["git_diff_check_passed"])
        self.assertEqual(payload["verification"]["status"], "verified")
        self.assertFalse(payload["safety"]["commits_enabled"])
        self.assertFalse(payload["safety"]["pushes_enabled"])
        self.assertTrue(backup_root_exists)
        self.assertEqual(approved_diff_copy, diff.strip())
        self.assertEqual(backup_manifest["stage"], "applied")
        self.assertEqual(backup_manifest["approved_by"], "test")
        self.assertEqual(backup_manifest["task_id"], payload["task_id"])
        self.assertEqual(backup_manifest["audit_record"]["task_id"], payload["task_id"])
        self.assertEqual(
            backup_manifest["backed_up_files"][0]["path"],
            "_blueprints/current/dashboard_state.md",
        )
        self.assertIn("rollback", backup_manifest["rollback_hint"].lower())
        self.assertFalse(approved_path_exists)
        self.assertTrue(applied_path_exists)
        proposal = next(
            item for item in proposals["proposals"] if item["proposal_id"] == "bp-20260515-apply"
        )
        self.assertEqual(proposal["status"], "applied")
        self.assertTrue(proposal["applied"])
        self.assertTrue(proposal["action_taken"])
        self.assertEqual(proposal["transitions"][-1]["status"], "applied")
        self.assertEqual(proposal["transitions"][-1]["actor"], "test")
        applied_events = [
            event
            for event in audit["events"]
            if event["proposal_id"] == "bp-20260515-apply" and event["event"] == "applied"
        ]
        self.assertEqual(len(applied_events), 1)
        self.assertEqual(applied_events[0]["files"], ["_blueprints/current/dashboard_state.md"])

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
                with self.assertRaisesRegex(Exception, "Markdown files under _blueprints"):
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
        self.assertEqual(response.json()["detail"]["reason_code"], "approval_required")

    def test_dashboard_review_route_approves_without_applying_files(self) -> None:
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

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "review_recorded")
        self.assertEqual(body["decision"], "approve")
        self.assertFalse(body["actions_taken"])
        self.assertFalse(body["apply_ran"])
        self.assertFalse(body["commit_ran"])
        self.assertFalse(body["push_ran"])
        proposal = payload["proposals"][0]
        self.assertEqual(proposal["status"], "approved")
        self.assertEqual(proposal["transitions"][-1]["actor"], "Britton")
        self.assertEqual(proposal["transitions"][-1]["status"], "approved")
        self.assertFalse(pending_path_exists)
        self.assertTrue(approved_path_exists)
        self.assertEqual(before, after)

    def test_dashboard_review_route_rejects_with_reason(self) -> None:
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

        self.assertEqual(response.status_code, 200)
        proposal = payload["proposals"][0]
        self.assertEqual(proposal["status"], "rejected")
        self.assertEqual(proposal["rejection_reason"], "Needs a smaller proposal.")
        self.assertEqual(proposal["transitions"][-1]["actor"], "Britton")
        self.assertFalse(pending_path_exists)
        self.assertTrue(rejected_path_exists)

    def test_dashboard_review_route_defers_and_marks_stale_without_applying_files(self) -> None:
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

        self.assertEqual(deferred.status_code, 200)
        self.assertEqual(stale.status_code, 200)
        self.assertEqual(before, after)
        proposals = {proposal["proposal_id"]: proposal for proposal in payload["proposals"]}
        self.assertEqual(proposals["bp-20260515-defer"]["status"], "deferred")
        self.assertEqual(proposals["bp-20260515-defer"]["review_note"], "Wait for design review.")
        self.assertEqual(proposals["bp-20260515-stale"]["status"], "stale")
        self.assertEqual(proposals["bp-20260515-stale"]["review_note"], "Superseded by newer drift.")
        self.assertFalse(proposals["bp-20260515-defer"]["applied"])
        self.assertFalse(proposals["bp-20260515-stale"]["action_taken"])
        self.assertEqual(payload["pending_proposals"], 0)

    def test_dashboard_review_route_records_generated_draft_snapshot(self) -> None:
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

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "review_recorded")
        proposal_files = [
            path for path in after if path.startswith("_blueprints/proposals/rejected/")
        ]
        self.assertEqual(len(proposal_files), 1)
        self.assertIn("_blueprints/proposals/rejected/bp-generated-scout.json", proposal_files)
        self.assertNotEqual(before, after)
        proposal = next(
            item for item in payload["proposals"] if item["proposal_id"] == "bp-generated-scout"
        )
        self.assertEqual(proposal["status"], "rejected")
        self.assertEqual(proposal["rejection_reason"], "Needs a smaller proposal.")
        self.assertFalse(proposal["applied"])
        self.assertFalse(proposal["action_taken"])

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
