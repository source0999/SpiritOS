from __future__ import annotations

from source_proxy.benchmarks.campaign_3_5_assets.gate import asset_readiness


def test_gate_refuses_execution_until_every_task_has_independent_profile_validation() -> None:
    tasks = [{"task_id": "S01"}, {"task_id": "U01"}]
    result = asset_readiness(
        tasks,
        builder_report={"passed": True, "validated_fixture_ids": [str(index) for index in range(65)]},
        noncompletion_report={"validated_task_ids": ["U01"]},
        core_reference_report={"validated_task_ids": []},
    )
    assert result["passed"] is False
    assert result["tasks_executable"] == 0
    assert result["remaining_profile_task_ids"] == ["S01"]
