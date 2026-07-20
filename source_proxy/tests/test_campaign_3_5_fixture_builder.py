from pathlib import Path

import pytest

from source_proxy.benchmarks.campaign_3_5_fixture_builder import (
    Campaign35FixtureBuildError,
    materialize_fixture,
    materialize_git_fixture,
)
from source_proxy.benchmarks.campaign_3_5_assets.seeding import (
    Campaign35RunSeed,
    derive_task_seed,
    task_seed_commitment,
)

def test_fixture_materialization_is_deterministic(tmp_path: Path) -> None:
    files={"src/app.py":"value = 1\n"}
    assert materialize_fixture(tmp_path / "a", files=files, seed="secret") == materialize_fixture(tmp_path / "b", files=files, seed="secret")


def test_git_fixture_is_isolated_committed_and_seed_secret(tmp_path: Path) -> None:
    seed = Campaign35RunSeed(raw=b"a" * 32, commitment="commitment")
    task_seed = derive_task_seed(seed, "S01", "py-fastapi-small")
    result = materialize_git_fixture(
        tmp_path,
        "fixture",
        fixture_id="py-fastapi-small",
        files={"src/app.py": "value = 1\n", "tests/test_app.py": "assert True\n"},
        seed_commitment=task_seed_commitment(task_seed),
        allowed_paths=["src/", "tests/"],
    )

    assert (result.fixture_root / ".git").is_dir()
    assert result.public_manifest["baseline_tree_sha256"] == result.baseline_tree_sha256
    public_bytes = b"".join(
        path.read_bytes()
        for path in result.fixture_root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )
    assert task_seed.encode("ascii") not in public_bytes


def test_fixture_rejects_traversal_and_active_repository_parent(tmp_path: Path) -> None:
    with pytest.raises(Campaign35FixtureBuildError, match="path_invalid"):
        materialize_fixture(tmp_path / "escape", files={"../escape": "no"}, seed="secret")
