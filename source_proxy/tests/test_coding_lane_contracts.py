from __future__ import annotations

import copy

import pytest

from source_proxy.contracts.coding_lane_contracts import (
    CORE_CODING_LANE_IDS,
    canonical_coding_lane_contracts,
)
from source_proxy.contracts.validation import ContractValidationError, validate_contract


def test_canonical_coding_lane_contract_catalog_is_complete_and_versioned() -> None:
    contracts = canonical_coding_lane_contracts()

    assert tuple(contracts) == CORE_CODING_LANE_IDS
    for lane_id, contract in contracts.items():
        assert contract["lane_id"] == lane_id
        assert contract["contract_version"] == "coding.lane-contract/v1.0.0"
        assert contract["deprecation_state"] == "active"
        assert contract["compatible_consumer_versions"]
        for field in (
            "input_schema",
            "output_schema",
            "failure_schema",
            "acknowledgement_schema",
            "evidence_schema",
        ):
            assert contract[field]["type"] == "object"
            assert contract[field]["additionalProperties"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("contract_version", "v1"),
        ("authority_class", "unbounded"),
        ("compatible_consumer_versions", []),
        ("deprecation_state", "unknown"),
    ],
)
def test_lane_contract_rejects_unversioned_or_incompatible_shape(field: str, value: object) -> None:
    contract = copy.deepcopy(canonical_coding_lane_contracts()["coder"])
    contract[field] = value

    with pytest.raises(ContractValidationError):
        validate_contract("coding/lane-contract", contract)
