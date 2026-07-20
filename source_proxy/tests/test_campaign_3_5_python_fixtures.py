from __future__ import annotations

import json
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import (
    IMPLEMENTED_FIXTURE_IDS,
    materialize_implemented_fixture,
)
from source_proxy.benchmarks.campaign_3_5_assets.seeding import Campaign35RunSeed, derive_task_seed, task_seed_commitment


ROOT = Path(__file__).resolve().parents[2]


def test_each_python_fixture_is_distinct_seeded_and_materializable(tmp_path: Path) -> None:
    tasks = json.loads((ROOT / "benchmarks/coder-backend-100/v1.1/tasks.json").read_text(encoding="utf-8"))
    by_fixture = {task["fixture"]: task for task in tasks if task["fixture"] in IMPLEMENTED_FIXTURE_IDS}
    seed = Campaign35RunSeed(raw=b"b" * 32, commitment="commitment")

    assert set(by_fixture) == IMPLEMENTED_FIXTURE_IDS
    contents = set()
    for index, fixture_id in enumerate(sorted(IMPLEMENTED_FIXTURE_IDS)):
        task = by_fixture[fixture_id]
        local_seed = derive_task_seed(seed, task["task_id"], fixture_id)
        parent = tmp_path / str(index)
        parent.mkdir()
        result = materialize_implemented_fixture(
            parent, task, task_seed=local_seed, task_seed_commitment=task_seed_commitment(local_seed)
        )
        contents.add(result.content_sha256)
        assert (result.fixture_root / ".git").is_dir()
        assert not any("hidden" in path.name.lower() for path in result.fixture_root.rglob("*"))
    assert len(contents) == len(IMPLEMENTED_FIXTURE_IDS)
