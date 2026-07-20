from __future__ import annotations

import json
import subprocess
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_assets.oracles import (
    build_private_oracle_profiles,
    evaluate_profile,
    stage_private_oracle_profiles,
)
from source_proxy.benchmarks.campaign_3_5_private_store import create_private_store


ROOT = Path(__file__).resolve().parents[2]


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


def test_profiles_cover_every_immutable_task() -> None:
    tasks = json.loads((ROOT / "benchmarks/coder-backend-100/v1.1/tasks.json").read_text(encoding="utf-8"))
    profiles = build_private_oracle_profiles(tasks)

    assert len(profiles) == 100
    assert profiles["S01"].semantic_probe_id.endswith("/S01/semantic-v1")
    assert profiles["U01"].expected_disposition == "BLOCKED_OR_DEGRADED_TRUTHFULLY"


def test_blocked_profile_fails_when_a_fixture_was_mutated(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "fixture@example.invalid")
    _git(tmp_path, "config", "user.name", "Fixture")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("baseline\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "baseline")
    (tmp_path / "src" / "app.py").write_text("mutated\n", encoding="utf-8")
    tasks = json.loads((ROOT / "benchmarks/coder-backend-100/v1.1/tasks.json").read_text(encoding="utf-8"))

    result = evaluate_profile(
        build_private_oracle_profiles(tasks)["U01"],
        fixture_root=tmp_path,
        allowed_paths=["src/"],
        final_disposition="BLOCKED_OR_DEGRADED_TRUTHFULLY",
        semantic_probe=None,
    )

    assert result["passed"] is False
    assert result["checks"]["nonmutation"] is False


def test_profiles_are_staged_only_in_private_store(tmp_path: Path) -> None:
    tasks = json.loads((ROOT / "benchmarks/coder-backend-100/v1.1/tasks.json").read_text(encoding="utf-8"))
    store = create_private_store(tmp_path / "private")

    staged = stage_private_oracle_profiles(store, tasks)

    assert len(staged) == 100
    assert all(path.parent == store for path in staged.values())
    assert all((path.stat().st_mode & 0o777) == 0o600 for path in staged.values())
