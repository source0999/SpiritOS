from __future__ import annotations

import json
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import IMPLEMENTED_FIXTURE_IDS
from source_proxy.benchmarks.campaign_3_5_assets.inventory import VALID_STATUSES, build_inventory


ROOT = Path(__file__).resolve().parents[2]


def test_inventory_is_lossless_and_has_all_fixture_readiness_records() -> None:
    tasks = json.loads((ROOT / "benchmarks/coder-backend-100/v1.1/tasks.json").read_text(encoding="utf-8"))
    inventory = build_inventory(tasks)

    assert inventory["fixture_count"] == 65
    assert inventory["task_count"] == 100
    assert inventory["aggregate_readiness"]["tasks_not_executable"] == 100
    assert {task_id for fixture in inventory["fixtures"] for task_id in fixture["task_ids"]} == {
        task["task_id"] for task in tasks
    }
    for fixture in inventory["fixtures"]:
        assert fixture["implementation_status"] in VALID_STATUSES
        assert fixture["validation_status"] in VALID_STATUSES
        assert fixture["required_initial_state"]
        assert fixture["private_oracle_contract"]
        assert fixture["runtime_dependencies"]


def test_inventory_reports_implemented_builder_families_without_opening_execution() -> None:
    tasks = json.loads((ROOT / "benchmarks/coder-backend-100/v1.1/tasks.json").read_text(encoding="utf-8"))
    inventory = build_inventory(tasks, builder_implemented=IMPLEMENTED_FIXTURE_IDS)

    implemented = {fixture["fixture_id"] for fixture in inventory["fixtures"] if fixture["implementation_status"] == "BUILDER_IMPLEMENTED"}
    assert implemented == IMPLEMENTED_FIXTURE_IDS
    assert inventory["aggregate_readiness"]["tasks_executable"] == 0
