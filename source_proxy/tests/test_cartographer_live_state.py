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

    assert state["current_branch"] == "main"
    assert isinstance(state["current_head"], str)
    assert state["tracked_dirty_files"] == []
    assert state["untracked_files"] == []
    assert state["protected_lane_matches"] == []
    assert state["recommended_safety_state"] == "clear"
    assert state["blocker_reasons"] == []
    assert state["no_mutation_guarantee"]["mutates_files"] is False


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

    assert state["git_available"] is False
    assert state["recommended_safety_state"] == "blocked"
    assert state["tracked_dirty_files"] == []
    assert state["untracked_files"] == []
    assert state["blocker_reasons"] == [
        "git command failed closed: git branch --show-current",
        "git command failed closed: git rev-parse HEAD",
        "git command failed closed: git status --porcelain=v1 -z --untracked-files=all",
    ]


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
