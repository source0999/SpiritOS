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
    build_cartographer_blueprints,
    build_cartographer_blueprint_scribe,
    build_cartographer_branch_recommendations,
    build_cartographer_change_scribe,
    build_cartographer_codex_evidence,
    build_cartographer_commit_proposals,
    build_cartographer_components,
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
)
from source_proxy.main import app


def _test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(cartographer_router)
    return test_app


class CartographerApiTests(unittest.TestCase):
    def test_status_contract_is_read_only_empty_state(self) -> None:
        with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": ""}, clear=False):
            payload = build_cartographer_status()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["configured_roots"], [])
        self.assertEqual(payload["blocked_roots"], [])
        self.assertEqual(payload["projects"], [])
        self.assertEqual(payload["blueprint_count"], 0)
        self.assertEqual(payload["pending_proposals"], 0)
        self.assertFalse(payload["safety"]["scout_bypass_allowed"])
        self.assertFalse(payload["safety"]["source_proxy_approval_bypass_allowed"])

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
        self.assertFalse(project["action_taken"])

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
        self.assertTrue(project["checks_passed"])
        self.assertIn("merge_ready", project["filters"])
        self.assertFalse(project["action_taken"])

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
        self.assertIn("Working tree dirty on main", recommendation["reason"])
        self.assertEqual(recommendation["changed_file_count"], 1)

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
        self.assertEqual(proposal["files"], ["_blueprints/current/dashboard_state.md"])
        self.assertEqual(proposal["component"], "blueprint-system")
        self.assertEqual(proposal["risk"], "low")
        self.assertFalse(proposal["generated"])
        self.assertEqual(proposal["unstaged_files"], ["_blueprints/current/dashboard_state.md"])
        self.assertTrue(proposal["editable"])
        self.assertTrue(proposal["requires_approval"])
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
        self.assertEqual(by_file["src/components/dashboard/Widget.tsx"]["staged_files"], ["src/components/dashboard/Widget.tsx"])
        self.assertEqual(by_file["docs/cartographer.md"]["component"], "docs")
        self.assertEqual(by_file["docs/cartographer.md"]["risk"], "low")
        self.assertEqual(by_file["source_proxy/cartographer/apply.py"]["component"], "cartographer")
        self.assertEqual(by_file["source_proxy/cartographer/apply.py"]["risk"], "high")
        self.assertEqual(by_file["scout/soak-logs/scout-soak-snapshot-test.json"]["suggested_message"], "chore(scout): record soak snapshot")
        self.assertTrue(all(proposal["generated"] for proposal in proposals))
        self.assertTrue(all(proposal["requires_approval"] for proposal in proposals))
        self.assertTrue(all(not proposal["commit_enabled"] for proposal in proposals))
        self.assertTrue(all(not proposal["action_taken"] for proposal in proposals))

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
        self.assertEqual(item["commits_ahead"], 1)
        self.assertEqual(item["files"], ["_blueprints/current/dashboard_state.md"])
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

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_push_queue()

        self.assertEqual(payload["push_count"], 1)
        item = payload["push_queue"][0]
        self.assertEqual(item["remote"], "origin")
        self.assertEqual(item["branch"], recommendation["suggested_branch"])
        self.assertIsNone(item["upstream"])
        self.assertEqual(item["commits_ahead"], 1)
        self.assertEqual(item["files"], ["src/components/dashboard/Widget.tsx"])

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
        self.assertEqual(after_branch, recommendation["suggested_branch"])
        self.assertIn(recommendation["suggested_branch"], _branch_names(branches))
        self.assertTrue(
            any(
                event["event"] == "branch_created"
                and event["actor"] == "Britton"
                and event["branch"] == recommendation["suggested_branch"]
                and event["source"] == "git_approval_record"
                for event in audit["events"]
            )
        )

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
        self.assertEqual(body["commit_message"], proposal["suggested_message"])
        self.assertTrue(all(check["status"] == "passed" for check in body["checks"]))
        self.assertEqual(committed_files, ["docs/cartographer.md"])
        self.assertIn("?? notes.md", remaining_status)
        self.assertTrue(
            any(
                event["event"] == "commit_created"
                and event["actor"] == "Britton"
                and event["source"] == "git_approval_record"
                for event in audit["events"]
            )
        )

    def test_push_approval_pushes_after_explicit_approval(self) -> None:
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
            client = TestClient(_test_app())

            remote_before = _git_stdout(remote, "rev-parse", "refs/heads/cartographer/push-approval").strip()
            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                item = build_cartographer_push_queue()["push_queue"][0]
                response = client.post(
                    f"/v1/cartographer/push-queue/{item['push_id']}/approve",
                    json={"approved": True, "approved_by": "Britton"},
                )
                audit = build_cartographer_audit_trail()
            remote_after = _git_stdout(remote, "rev-parse", "refs/heads/cartographer/push-approval").strip()

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "pushed")
        self.assertEqual(body["approval_kind"], "push")
        self.assertFalse(body["branch_created"])
        self.assertFalse(body["commit_created"])
        self.assertTrue(body["push_ran"])
        self.assertTrue(body["safety"]["push_enabled"])
        self.assertNotEqual(remote_before, remote_after)
        self.assertTrue(
            any(
                event["event"] == "push_approved"
                and event["actor"] == "Britton"
                and event["result"] == "pushed"
                and event["source"] == "git_approval_record"
                for event in audit["events"]
            )
        )

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
                    "commit_sha": "74315faac5b228dd22b54f0f530893b0e9a2988a",
                    "commit_message": "docs(scout): apply cartographer blueprint update",
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
        self.assertIn("Switch back", by_event["branch_created"]["rollback_hint"])
        self.assertEqual(by_event["commit_created"]["action"], "create_commit")
        self.assertEqual(by_event["commit_created"]["commit_sha"], "74315faac5b228dd22b54f0f530893b0e9a2988a")
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
                "src/app/chat/page.tsx",
                "src/app/oracle/page.tsx",
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
        self.assertEqual(by_id["oracle"].blueprint_id, "oracle-voice")
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
        payload = build_cartographer_components()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["mapping_mode"], "rules")
        self.assertEqual(payload["unmapped_paths"], [])
        components = {component["component_id"]: component for component in payload["components"]}
        self.assertEqual(components["dashboard"]["blueprint_id"], "dashboard-state")
        self.assertEqual(components["dashboard"]["risk"], "medium")
        self.assertEqual(components["blueprint-system"]["paths"], ["_blueprints/**"])
        self.assertEqual(components["docs"]["risk"], "low")

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
        self.assertTrue(git_status["is_primary_branch"])
        self.assertTrue(git_status["needs_branch_recommendation"])
        self.assertTrue(git_status["needs_commit"])
        self.assertTrue(git_status["needs_push"])
        self.assertFalse(git_status["merge_ready"])
        self.assertEqual(git_status["write_mode"], "locked")
        self.assertEqual(git_status["last_commit"]["message"], "local ahead commit")
        self.assertTrue(git_status["last_commit"]["sha"])

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
        self.assertEqual(payload["proposal_lifecycle"], payload["proposal_states"])
        self.assertEqual(payload["lifecycle"], payload["proposal_states"])
        self.assertTrue(payload["transition_audit_complete"])
        self.assertEqual(payload["proposal_count"], 1)
        self.assertEqual(payload["pending_proposals"], 1)
        proposal = payload["proposals"][0]
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
        self.assertIn("review Dashboard blueprint", summary["recommended_actions"])
        self.assertTrue(summary["uncertain_claims"])

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
        for proposal in codex_proposals:
            self.assertEqual(proposal["status"], "pending_review")
            self.assertEqual(proposal["type"], "blueprint_update")
            self.assertTrue(proposal["requires_approval"])
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
        self.assertTrue(
            all(role["failure_policy"] == "stop_at_proposal_queue" for role in payload["roles"])
        )

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
