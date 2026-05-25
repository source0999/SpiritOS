from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api import cartographer as cartographer_api
from source_proxy.cartographer import live_state
from source_proxy.cartographer.live_state import collect_live_repo_state


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def _write(root: Path, relative_path: str, content: str = "content\n") -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "cartographer@example.test")
    _git(tmp_path, "config", "user.name", "Cartographer Test")
    _git(tmp_path, "branch", "-M", "main")
    _write(tmp_path, "README.md", "initial\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "initial")
    return tmp_path


def _state_with_dirty_file(
    tmp_path: Path,
    relative_path: str,
    *,
    tracked: bool,
    content: str = "changed\n",
) -> dict[str, object]:
    root = _repo(tmp_path)
    if tracked:
        _write(root, relative_path, "before\n")
        _git(root, "add", relative_path)
        _git(root, "commit", "-m", f"track {relative_path}")
    _write(root, relative_path, content)
    return collect_live_repo_state(root)


def test_clean_state_parsing_reports_clear_repo(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    state = collect_live_repo_state(root)
    truth_packet = state["truth_packet"]

    assert state["current_branch"] == "main"
    assert isinstance(state["current_head"], str)
    assert state["tracked_dirty_files"] == []
    assert state["untracked_files"] == []
    assert state["protected_lane_matches"] == []
    assert state["recommended_safety_state"] == "clear"
    assert state["blocker_reasons"] == []
    assert state["no_mutation_guarantee"]["mutates_files"] is False
    assert truth_packet["schema_version"] == "cartographer.truth-packet.v0.1"
    assert truth_packet["packet_kind"] == "cartographer_truth_packet"
    assert truth_packet["status"] == "clear"
    assert truth_packet["decision_default"] == "no_go"
    assert truth_packet["advisory_only"] is True
    assert truth_packet["facts"]["current_branch"] == "main"
    assert truth_packet["facts"]["tracked_dirty_count"] == 0
    assert truth_packet["facts"]["total_dirty_count"] == 0
    assert truth_packet["recommendations"]["recommended_safety_state"] == "clear"
    assert truth_packet["recommendations"]["confidence"] == "high"
    assert truth_packet["state_flags"]["verified"] is True
    assert truth_packet["state_flags"]["clear"] is True
    assert truth_packet["state_flags"]["no_go"] is True
    assert truth_packet["authority"]["authority_granted"] is False
    assert truth_packet["authority"]["write_actions_enabled"] is False
    assert truth_packet["authority"]["queue_authority_granted"] is False
    assert truth_packet["authority"]["can_mutate"] is False
    assert "facts.current_branch" in truth_packet["verified_fields"]
    assert truth_packet["unknown_fields"] == []
    assert truth_packet["stale_fields"] == []
    assert truth_packet["evidence_links"] == [
        {
            "label": "Live repo truth packet",
            "kind": "live_fact",
            "href": "/map/raw",
            "summary": (
                f"clear on main at {state['current_head'][:12]}; "
                "0 dirty file(s), 0 protected warning(s)."
            ),
            "authority_granted": False,
            "review_only": True,
        },
        {
            "label": "Current blockers",
            "kind": "blocker_summary",
            "href": "/map/raw#authority-boundary",
            "summary": "No blocker reasons reported; NO-GO still remains the decision default.",
            "authority_granted": False,
            "review_only": True,
        },
        {
            "label": "Unknown or stale fields",
            "kind": "freshness_summary",
            "href": "/map/raw#live-read-only-packet",
            "summary": "No unknown or stale fields reported; evidence remains review-only.",
            "authority_granted": False,
            "review_only": True,
        },
    ]


def test_dirty_tracked_files_are_reported(tmp_path: Path) -> None:
    state = _state_with_dirty_file(tmp_path, "docs/note.md", tracked=True)

    assert state["tracked_dirty_files"] == ["docs/note.md"]
    assert state["untracked_files"] == []
    assert state["recommended_safety_state"] == "caution"


def test_untracked_files_are_reported(tmp_path: Path) -> None:
    state = _state_with_dirty_file(tmp_path, "docs/new.md", tracked=False)

    assert state["tracked_dirty_files"] == []
    assert state["untracked_files"] == ["docs/new.md"]
    assert state["recommended_safety_state"] == "caution"


def test_protected_source_proxy_runtime_files_are_blocked(tmp_path: Path) -> None:
    state = _state_with_dirty_file(
        tmp_path,
        "source_proxy/cartographer/apply.py",
        tracked=True,
    )

    assert state["source_proxy_runtime_files_dirty"] is True
    assert {
        "path": "source_proxy/cartographer/apply.py",
        "lane": "source_proxy_runtime",
    } in state["protected_lane_matches"]
    assert state["recommended_safety_state"] == "blocked"
    assert "source_proxy runtime files are dirty" in state["blocker_reasons"]
    assert state["truth_packet"]["status"] == "blocked"
    assert state["truth_packet"]["state_flags"]["blocked"] is True
    assert state["truth_packet"]["state_flags"]["no_go"] is True
    assert "source_proxy_runtime_files_are_dirty" in state["truth_packet"]["blocked_reason_codes"]
    assert state["truth_packet"]["evidence_links"][1]["label"] == "Current blockers"
    assert state["truth_packet"]["evidence_links"][1]["authority_granted"] is False
    assert state["truth_packet"]["evidence_links"][1]["review_only"] is True
    assert (
        state["truth_packet"]["evidence_links"][1]["summary"]
        == "source_proxy runtime files are dirty"
    )


def test_package_config_and_env_files_are_blocked(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    for relative_path in ("package.json", "config/app.json", ".env.local"):
        _write(root, relative_path, "before\n")
    _git(root, "add", "package.json", "config/app.json", ".env.local")
    _git(root, "commit", "-m", "track package config env")
    for relative_path in ("package.json", "config/app.json", ".env.local"):
        _write(root, relative_path, "after\n")

    state = collect_live_repo_state(root)

    assert state["package_config_env_files_dirty"] is True
    assert state["recommended_safety_state"] == "blocked"
    assert "package, config, or env files are dirty" in state["blocker_reasons"]
    assert {
        "path": "package.json",
        "lane": "package_config_env",
    } in state["protected_lane_matches"]
    assert {
        "path": "config/app.json",
        "lane": "package_config_env",
    } in state["protected_lane_matches"]
    assert {
        "path": ".env.local",
        "lane": "package_config_env",
    } in state["protected_lane_matches"]


def test_coding_dirty_detection_blocks(tmp_path: Path) -> None:
    state = _state_with_dirty_file(
        tmp_path,
        "src/app/coding/page.tsx",
        tracked=True,
    )

    assert state["coding_files_dirty"] is True
    assert state["recommended_safety_state"] == "blocked"
    assert "/coding files are dirty" in state["blocker_reasons"]


def test_map_dirty_detection_cautions_without_blocking(tmp_path: Path) -> None:
    state = _state_with_dirty_file(tmp_path, "src/app/map/page.tsx", tracked=True)

    assert state["map_files_dirty"] is True
    assert state["recommended_safety_state"] == "caution"
    assert state["blocker_reasons"] == []


def test_unknown_file_classification_cautions(tmp_path: Path) -> None:
    state = _state_with_dirty_file(tmp_path, "docs/unknown.md", tracked=True)

    assert state["unknown_unclassified_dirty_files"] == ["docs/unknown.md"]
    assert state["recommended_safety_state"] == "caution"


def test_failed_git_command_fails_closed(monkeypatch, tmp_path: Path) -> None:
    def fail_git(
        root: Path,
        command: list[str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            returncode=2,
            stdout="",
            stderr="fatal: no git here",
        )

    monkeypatch.setattr(live_state, "_run_git", fail_git)

    state = collect_live_repo_state(tmp_path)
    truth_packet = state["truth_packet"]

    assert state["git_available"] is False
    assert state["recommended_safety_state"] == "blocked"
    assert state["tracked_dirty_files"] == []
    assert state["untracked_files"] == []
    assert state["blocker_reasons"] == [
        "git command failed closed: git branch --show-current",
        "git command failed closed: git rev-parse HEAD",
        "git command failed closed: git status --porcelain=v1 -z --untracked-files=all",
    ]
    assert truth_packet["status"] == "no_go"
    assert truth_packet["recommendations"]["confidence"] == "low"
    assert truth_packet["state_flags"]["unknown"] is True
    assert truth_packet["state_flags"]["blocked"] is True
    assert truth_packet["authority"]["authority_granted"] is False
    assert truth_packet["authority"]["write_actions_enabled"] is False
    assert "facts.current_branch" in truth_packet["unknown_fields"]
    assert "facts.current_head" in truth_packet["unknown_fields"]


def test_truth_packet_missing_critical_fields_fail_closed(monkeypatch) -> None:
    monkeypatch.setattr(live_state, "_utc_now", lambda: "2026-05-24T00:00:00Z")

    truth_packet = live_state.build_cartographer_truth_packet(
        {
            "git_available": True,
            "recommended_safety_state": "clear",
            "collected_at": "2026-05-24T00:00:00Z",
            "no_mutation_guarantee": live_state._no_mutation_guarantee(),
        }
    )

    assert truth_packet["status"] == "no_go"
    assert truth_packet["decision_default"] == "no_go"
    assert truth_packet["advisory_only"] is True
    assert truth_packet["state_flags"]["unknown"] is True
    assert truth_packet["state_flags"]["no_go"] is True
    assert truth_packet["recommendations"]["confidence"] == "low"
    assert truth_packet["recommendations"]["no_go_reason"] == "critical_fields_unknown"
    assert truth_packet["authority"]["authority_granted"] is False
    assert truth_packet["authority"]["write_actions_enabled"] is False
    assert truth_packet["authority"]["can_mutate"] is False
    assert "facts.current_branch" in truth_packet["unknown_fields"]
    assert "facts.current_head" in truth_packet["unknown_fields"]
    assert "facts.tracked_dirty_count" in truth_packet["unknown_fields"]
    assert "facts.untracked_dirty_count" in truth_packet["unknown_fields"]
    assert "facts.protected_lane_count" in truth_packet["unknown_fields"]
    assert truth_packet["stale_fields"] == []


def test_truth_packet_malformed_critical_fields_fail_closed(monkeypatch) -> None:
    monkeypatch.setattr(live_state, "_utc_now", lambda: "2026-05-24T00:00:00Z")

    truth_packet = live_state.build_cartographer_truth_packet(
        {
            "git_available": "true",
            "current_branch": ["main"],
            "current_head": 123,
            "tracked_dirty_files": "docs/note.md",
            "untracked_files": [42],
            "protected_lane_matches": ["source_proxy/cartographer/live_state.py"],
            "coding_files_dirty": "false",
            "map_files_dirty": None,
            "package_config_env_files_dirty": "false",
            "source_proxy_runtime_files_dirty": "false",
            "unknown_unclassified_dirty_files": "docs/unknown.md",
            "recommended_safety_state": "clear",
            "blocker_reasons": "none",
            "collected_at": "not-a-date",
            "no_mutation_guarantee": {"mutates_files": True},
            "git_errors": "fatal",
        }
    )

    assert truth_packet["status"] == "no_go"
    assert truth_packet["state_flags"]["unknown"] is True
    assert truth_packet["state_flags"]["blocked"] is True
    assert truth_packet["state_flags"]["no_go"] is True
    assert truth_packet["recommendations"]["confidence"] == "low"
    assert truth_packet["recommendations"]["no_go_reason"] == "critical_fields_unknown"
    assert truth_packet["authority"]["authority_granted"] is False
    assert truth_packet["authority"]["write_actions_enabled"] is False
    assert truth_packet["authority"]["can_mutate"] is False
    assert "facts.git_available" in truth_packet["unknown_fields"]
    assert "facts.current_branch" in truth_packet["unknown_fields"]
    assert "facts.current_head" in truth_packet["unknown_fields"]
    assert "facts.tracked_dirty_count" in truth_packet["unknown_fields"]
    assert "facts.untracked_dirty_count" in truth_packet["unknown_fields"]
    assert "facts.protected_lane_count" in truth_packet["unknown_fields"]
    assert "facts.no_mutation_guarantee" in truth_packet["unknown_fields"]
    assert "recency.collected_at" in truth_packet["unknown_fields"]
    assert truth_packet["facts"]["no_mutation_guarantee"]["mutates_files"] is False
    assert all(
        value is False for value in truth_packet["authority"].values()
    )


def test_truth_packet_stale_collected_at_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(live_state, "_utc_now", lambda: "2026-05-24T00:10:01Z")

    truth_packet = live_state.build_cartographer_truth_packet(
        {
            "git_available": True,
            "current_branch": "main",
            "current_head": "abc123",
            "tracked_dirty_files": [],
            "untracked_files": [],
            "protected_lane_matches": [],
            "coding_files_dirty": False,
            "map_files_dirty": False,
            "package_config_env_files_dirty": False,
            "source_proxy_runtime_files_dirty": False,
            "unknown_unclassified_dirty_files": [],
            "recommended_safety_state": "clear",
            "blocker_reasons": [],
            "collected_at": "2026-05-24T00:00:00Z",
            "no_mutation_guarantee": live_state._no_mutation_guarantee(),
            "git_errors": [],
        }
    )

    assert truth_packet["status"] == "stale"
    assert truth_packet["state_flags"]["stale"] is True
    assert truth_packet["state_flags"]["blocked"] is True
    assert truth_packet["state_flags"]["clear"] is False
    assert truth_packet["state_flags"]["no_go"] is True
    assert truth_packet["recommendations"]["confidence"] == "low"
    assert truth_packet["recommendations"]["no_go_reason"] == "stale_fields_present"
    assert "recency.collected_at" in truth_packet["stale_fields"]
    assert truth_packet["recency"]["stale"] is True
    assert truth_packet["recency"]["age_seconds"] == 601
    assert all(source["stale"] is True for source in truth_packet["sources"])
    assert all(source["status"] == "stale" for source in truth_packet["sources"])
    assert truth_packet["evidence_links"][2]["summary"] == (
        "Stale fields keep the packet NO-GO: recency.collected_at, "
        "sources.git.branch.current, sources.git.head.current, "
        "sources.git.status.porcelain."
    )
    assert truth_packet["authority"]["authority_granted"] is False
    assert truth_packet["authority"]["write_actions_enabled"] is False
    assert truth_packet["authority"]["can_mutate"] is False


def test_truth_packet_malformed_generated_at_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(live_state, "_utc_now", lambda: "not-a-date")

    truth_packet = live_state.build_cartographer_truth_packet(
        {
            "git_available": True,
            "current_branch": "main",
            "current_head": "abc123",
            "tracked_dirty_files": [],
            "untracked_files": [],
            "protected_lane_matches": [],
            "coding_files_dirty": False,
            "map_files_dirty": False,
            "package_config_env_files_dirty": False,
            "source_proxy_runtime_files_dirty": False,
            "unknown_unclassified_dirty_files": [],
            "recommended_safety_state": "clear",
            "blocker_reasons": [],
            "collected_at": "2026-05-24T00:00:00Z",
            "no_mutation_guarantee": live_state._no_mutation_guarantee(),
            "git_errors": [],
        }
    )

    assert truth_packet["status"] == "no_go"
    assert truth_packet["state_flags"]["unknown"] is True
    assert truth_packet["state_flags"]["stale"] is False
    assert truth_packet["recommendations"]["confidence"] == "low"
    assert truth_packet["recommendations"]["no_go_reason"] == "critical_fields_unknown"
    assert truth_packet["recency"]["generated_at_valid"] is False
    assert truth_packet["recency"]["collected_at_valid"] is True
    assert "recency.generated_at" in truth_packet["unknown_fields"]
    assert truth_packet["stale_fields"] == []
    assert truth_packet["authority"]["can_mutate"] is False


def test_truth_packet_malformed_status_source_is_labeled(monkeypatch) -> None:
    monkeypatch.setattr(live_state, "_utc_now", lambda: "2026-05-24T00:00:00Z")

    truth_packet = live_state.build_cartographer_truth_packet(
        {
            "git_available": True,
            "current_branch": "main",
            "current_head": "abc123",
            "tracked_dirty_files": "docs/note.md",
            "untracked_files": [],
            "protected_lane_matches": [],
            "coding_files_dirty": False,
            "map_files_dirty": False,
            "package_config_env_files_dirty": False,
            "source_proxy_runtime_files_dirty": False,
            "unknown_unclassified_dirty_files": [],
            "recommended_safety_state": "clear",
            "blocker_reasons": [],
            "collected_at": "2026-05-24T00:00:00Z",
            "no_mutation_guarantee": live_state._no_mutation_guarantee(),
            "git_errors": [],
        }
    )

    status_source = next(
        source
        for source in truth_packet["sources"]
        if source["name"] == "git.status.porcelain"
    )
    branch_source = next(
        source
        for source in truth_packet["sources"]
        if source["name"] == "git.branch.current"
    )

    assert truth_packet["status"] == "no_go"
    assert truth_packet["recommendations"]["confidence"] == "low"
    assert "facts.tracked_dirty_count" in truth_packet["unknown_fields"]
    assert "facts.total_dirty_count" in truth_packet["unknown_fields"]
    assert status_source["status"] == "malformed"
    assert status_source["verified"] is False
    assert status_source["unknown"] is True
    assert status_source["stale"] is False
    assert branch_source["status"] == "verified"
    assert truth_packet["authority"]["authority_granted"] is False
    assert truth_packet["authority"]["write_actions_enabled"] is False


def test_live_state_api_route_returns_collector_payload(monkeypatch) -> None:
    payload = {
        "current_branch": "main",
        "current_head": "abc123",
        "tracked_dirty_files": [],
        "untracked_files": [],
        "protected_lane_matches": [],
        "coding_files_dirty": False,
        "map_files_dirty": False,
        "package_config_env_files_dirty": False,
        "source_proxy_runtime_files_dirty": False,
        "unknown_unclassified_dirty_files": [],
        "recommended_safety_state": "clear",
        "blocker_reasons": [],
        "collected_at": "2026-05-22T00:00:00Z",
        "no_mutation_guarantee": {"mutates_files": False},
    }
    monkeypatch.setattr(cartographer_api, "collect_live_repo_state", lambda: payload)
    app = FastAPI()
    app.include_router(cartographer_api.router)

    response = TestClient(app).get("/v1/cartographer/live-state")

    assert response.status_code == 200
    assert response.json() == payload
