"""Run Python private semantic probes in isolated materializations."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import materialize_implemented_fixture
from source_proxy.benchmarks.campaign_3_5_assets.python_runtime_references import PYTHON_RUNTIME_TASKS, apply_python_runtime_reference, probe_python_runtime
from source_proxy.benchmarks.campaign_3_5_assets.seeding import Campaign35RunSeed, derive_task_seed, task_seed_commitment


def validate_python_runtime_references(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {task["task_id"]: task for task in tasks}; records=[]
    seed=Campaign35RunSeed(raw=b"campaign35-python-runtime".ljust(32,b"0"), commitment="python-runtime")
    with tempfile.TemporaryDirectory(prefix="campaign35-python-runtime-") as temporary:
        for index, task_id in enumerate(sorted(PYTHON_RUNTIME_TASKS)):
            task=by_id[task_id]; parent=Path(temporary)/str(index); parent.mkdir()
            local=derive_task_seed(seed,task_id,task["fixture"])
            fixture=materialize_implemented_fixture(parent,task,task_seed=local,task_seed_commitment=task_seed_commitment(local))
            apply_python_runtime_reference(task_id,fixture.fixture_root)
            passed,category=probe_python_runtime(task_id,fixture.fixture_root)
            records.append({"task_id":task_id,"passed":passed,"category":category})
    return {"schema_version":"campaign-3.5-python-runtime-validation/v1","passed":all(row["passed"] for row in records),"task_count":len(records),"tasks":records,"validated_task_ids":[row["task_id"] for row in records if row["passed"]]}
