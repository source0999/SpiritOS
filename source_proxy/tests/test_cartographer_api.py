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
from source_proxy.cartographer.component_mapper import map_paths
from source_proxy.cartographer.project_discovery import parse_project_roots
from source_proxy.cartographer.service import (
    build_cartographer_blueprints,
    build_cartographer_components,
    build_cartographer_drift,
    build_cartographer_git,
    build_cartographer_projects,
    build_cartographer_proposals,
    build_cartographer_reminders,
    build_cartographer_repo_map,
    build_cartographer_status,
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

    def test_router_exposes_only_read_only_get_endpoints(self) -> None:
        client = TestClient(_test_app())

        for route in (
            "/v1/cartographer/status",
            "/v1/cartographer/projects",
            "/v1/cartographer/blueprints",
            "/v1/cartographer/components",
            "/v1/cartographer/repo-map",
            "/v1/cartographer/git",
            "/v1/cartographer/drift",
            "/v1/cartographer/reminders",
            "/v1/cartographer/proposals",
        ):
            response = client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["write_actions_enabled"])
            self.assertEqual(response.json()["status"], "observing")

        self.assertEqual(client.post("/v1/cartographer/status").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/projects").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/blueprints").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/components").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/repo-map").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/git").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/drift").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/reminders").status_code, 405)
        self.assertEqual(client.post("/v1/cartographer/proposals").status_code, 405)

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
        self.assertEqual(projects["Client Dashboard"]["write_policy"], "read_only")
        self.assertNotIn("client notes stay unread", str(payload))

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

    def test_component_mapper_maps_known_paths_and_reports_unknowns(self) -> None:
        components, unmapped = map_paths(
            [
                "scout/src/scout/api/discovery_jobs.py",
                "source_proxy/cartographer/service.py",
                "src/app/api/scout/overview/route.ts",
                "src/components/dashboard/HomelabCartographerWidget.tsx",
                "src/app/chat/page.tsx",
                "src/app/oracle/page.tsx",
                "scripts/spiritdesktop-windows/agent.ps1",
                "_blueprints/current/system_state.md",
                "src/app/design-demo/page.tsx",
                "README.md",
            ]
        )

        by_id = {component.component_id: component for component in components}
        self.assertEqual(by_id["scout"].blueprint_id, "system-state")
        self.assertEqual(by_id["source-proxy"].blueprint_id, "system-state")
        self.assertEqual(by_id["scout-dashboard-bridge"].label, "Scout dashboard bridge")
        self.assertEqual(by_id["dashboard"].blueprint_id, "dashboard-state")
        self.assertEqual(by_id["chat-workspace"].blueprint_id, "chat-workspace")
        self.assertEqual(by_id["oracle"].blueprint_id, "oracle-voice")
        self.assertEqual(by_id["windows-desktop-agent"].label, "Windows desktop agent")
        self.assertEqual(by_id["blueprint-system"].blueprint_id, "blueprint-index")
        self.assertTrue(by_id["design-demo"].sandbox)
        self.assertEqual([item.path for item in unmapped], ["README.md"])

    def test_component_mapper_route_exposes_rules_without_guessing_unmapped_paths(self) -> None:
        payload = build_cartographer_components()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["mapping_mode"], "rules")
        self.assertEqual(payload["unmapped_paths"], [])
        components = {component["component_id"]: component for component in payload["components"]}
        self.assertEqual(components["dashboard"]["blueprint_id"], "dashboard-state")
        self.assertEqual(components["blueprint-system"]["paths"], ["_blueprints/**"])

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
        files = {item["path"]: item for item in repo_map["files"]}
        self.assertIn("src/components/dashboard/Widget.tsx", files)
        self.assertEqual(files["src/components/dashboard/Widget.tsx"]["component_id"], "dashboard")
        self.assertEqual(files["src/components/dashboard/Widget.tsx"]["blueprint_id"], "dashboard-state")
        self.assertIn("DashboardWidget", files["src/components/dashboard/Widget.tsx"]["symbols"])
        self.assertIn("dashboardValue", files["src/components/dashboard/Widget.tsx"]["symbols"])
        self.assertIn("build_cartographer_repo_map", files["source_proxy/cartographer/service.py"]["symbols"])
        self.assertNotIn("SECRET_SHOULD_NOT_APPEAR", str(payload))
        self.assertNotIn("shouldNotAppear", str(payload))
        self.assertIn("node_modules", repo_map["skipped"])

    def test_repo_map_reports_unmapped_paths_without_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "README.md").write_text("repo notes", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_repo_map()

        repo_map = payload["maps"][0]
        self.assertIn({"path": "README.md", "reason": "no_component_mapping_rule"}, repo_map["unmapped_paths"])

    def test_git_status_scanner_reports_branch_dirty_files_and_last_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            _git(root, "init")
            _git(root, "config", "user.email", "cartographer@example.test")
            _git(root, "config", "user.name", "Cartographer Test")
            (root / "README.md").write_text("initial", encoding="utf-8")
            _git(root, "add", "README.md")
            _git(root, "commit", "-m", "initial commit")
            (root / "src").mkdir()
            (root / "src" / "changed.ts").write_text("export const changed = true;", encoding="utf-8")

            with patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False):
                payload = build_cartographer_git()

        self.assertEqual(payload["status"], "observing")
        self.assertFalse(payload["write_actions_enabled"])
        self.assertEqual(payload["project_count"], 1)
        git_status = payload["git_statuses"][0]
        self.assertTrue(git_status["available"])
        self.assertTrue(git_status["dirty"])
        self.assertIn("src/changed.ts", git_status["changed_files"])
        self.assertEqual(git_status["last_commit"]["message"], "initial commit")
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
            by_reason["api_changed_without_manual_checklist_update"]["affected_blueprints"],
            ["basic-chat-voice-qa"],
        )
        self.assertEqual(by_reason["api_changed_without_manual_checklist_update"]["severity"], "action_recommended")

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


def _write_proposal(root: Path, state: str, proposal_id: str, payload: dict[str, object]) -> None:
    proposal_dir = root / "_blueprints" / "proposals" / state
    proposal_dir.mkdir(parents=True, exist_ok=True)
    proposal_payload = {"proposal_id": proposal_id, **payload}
    (proposal_dir / f"{proposal_id}.json").write_text(
        json.dumps(proposal_payload, indent=2),
        encoding="utf-8",
    )


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
