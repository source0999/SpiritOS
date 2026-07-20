"""Apply private references in disposable roots to prove Core-30 solvability."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_assets.core_references import CORE_COMPLETED_TASKS, apply_core_reference, probe_core_reference
from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import materialize_implemented_fixture
from source_proxy.benchmarks.campaign_3_5_assets.seeding import Campaign35RunSeed, derive_task_seed, task_seed_commitment


def validate_core_references(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {task["task_id"]: task for task in tasks}
    seed = Campaign35RunSeed(raw=b"campaign-3.5-core-reference".ljust(32, b"0"), commitment="core-reference")
    records = []
    with tempfile.TemporaryDirectory(prefix="campaign35-core-reference-") as temporary:
        temporary_root = Path(temporary)
        for index, task_id in enumerate(sorted(CORE_COMPLETED_TASKS)):
            task = by_id[task_id]; parent = temporary_root / str(index); parent.mkdir()
            local_seed = derive_task_seed(seed, task_id, task["fixture"])
            fixture = materialize_implemented_fixture(parent, task, task_seed=local_seed, task_seed_commitment=task_seed_commitment(local_seed))
            apply_core_reference(task_id, fixture.fixture_root)
            passed, category = probe_core_reference(task_id, fixture.fixture_root)
            records.append({"task_id": task_id, "passed": passed, "category": category})
    return {"schema_version":"campaign-3.5-core-reference-validation/v1", "task_count":len(records), "passed":all(item["passed"] for item in records), "tasks":records, "validated_task_ids":[item["task_id"] for item in records if item["passed"]]}
