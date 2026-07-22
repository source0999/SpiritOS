from __future__ import annotations

import json
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import IMPLEMENTED_FIXTURE_IDS
from source_proxy.benchmarks.campaign_3_5_assets.inventory import (
    OPENAI_AGENTS_CAPABILITY_REQUIREMENT,
    OPENAI_AGENTS_SEMANTIC_REQUIREMENT,
    VALID_STATUSES,
    build_inventory,
)


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


def test_m15_inventory_states_capability_requirement_without_fabricating_sdk_trace() -> None:
    tasks = json.loads((ROOT / "benchmarks/coder-backend-100/v1.1/tasks.json").read_text(encoding="utf-8"))
    inventory = build_inventory(tasks)
    fixture = next(record for record in inventory["fixtures"] if "M15" in record["task_ids"])
    checked_in = json.loads(
        (ROOT / "source_proxy/benchmarks/campaign_3_5_assets/inventory.json").read_text(
            encoding="utf-8"
        )
    )
    checked_in_fixture = next(
        record for record in checked_in["fixtures"] if "M15" in record["task_ids"]
    )

    assert OPENAI_AGENTS_CAPABILITY_REQUIREMENT in fixture["required_capabilities"]
    assert "openai_agents_sdk_adapter" not in fixture["required_capabilities"]
    assert OPENAI_AGENTS_SEMANTIC_REQUIREMENT in fixture["semantic_invariants"]["M15"]
    assert OPENAI_AGENTS_SEMANTIC_REQUIREMENT in fixture["private_oracle_contract"]["M15"]
    assert not any(
        "openai_agents_sdk_adapter invocation traced" in invariant
        for invariant in fixture["semantic_invariants"]["M15"]
    )
    assert checked_in_fixture["required_capabilities"] == fixture["required_capabilities"]
    assert checked_in_fixture["semantic_invariants"]["M15"] == fixture[
        "semantic_invariants"
    ]["M15"]
    assert checked_in_fixture["private_oracle_contract"]["M15"] == fixture[
        "private_oracle_contract"
    ]["M15"]
