from __future__ import annotations

import pytest

from source_proxy.coding.extended_lane_registry import (
    EXTENDED_LANE_IDS,
    ExtendedLaneRegistryError,
    canonical_extended_lane_registry,
    selectable_extended_lanes,
)
from source_proxy.coding.runtime_lane_boundary import RuntimeLaneBoundary
from source_proxy.contracts.coding_lane_contracts import canonical_extended_coding_lane_contracts


def test_registry_has_one_contract_bound_selectable_record_per_retained_lane() -> None:
    registry = canonical_extended_lane_registry()
    assert tuple(item.lane_id for item in registry) == EXTENDED_LANE_IDS
    assert all(item.selectable for item in registry)
    assert all(item.production_caller and item.production_consumer for item in registry)


def test_non_registry_or_nonselectable_lane_cannot_be_selected() -> None:
    with pytest.raises(ExtendedLaneRegistryError, match="unknown_extended_lane"):
        selectable_extended_lanes(applicable_lane_ids=["extended.searxng-provider"])


def test_extended_output_requires_contract_bound_downstream_consumption() -> None:
    boundary = RuntimeLaneBoundary(contracts=canonical_extended_coding_lane_contracts())
    output = boundary.issue_output(
        lane_id="extended-scout-research",
        contract_version="coding.lane-contract/v1.0.0",
        producer_invocation_id="scout-invocation-1",
        payload={"research_id": "research-1", "sources": [{"url": "https://example.test"}], "freshness": "current"},
    )
    acknowledgement = boundary.record_consumer_acknowledgement(
        output_id=output.output_id,
        consumer_version="coding-orchestrator/v1",
        consumer_invocation_id="planner-invocation-1",
        payload={"consumer": "planner", "research_id": "research-1"},
    )
    consumption = boundary.mark_output_consumed(output_id=output.output_id, acknowledgement_id=acknowledgement.acknowledgement_id)
    assert consumption.output_id == output.output_id
