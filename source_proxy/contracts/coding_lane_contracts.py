"""Load the versioned contracts for the mandatory core coding participants."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from source_proxy.contracts.validation import ContractValidationError, validate_contract


CORE_CODING_LANE_IDS = (
    "context-broker",
    "planner",
    "coder",
    "reviewer",
    "verifier",
    "anti-cheat",
    "repair",
    "evidence-recorder",
)
_ROOT = Path(__file__).resolve().parents[2]
_CATALOG = _ROOT / "packages" / "contracts" / "schemas" / "coding" / "core-lane-contracts.v1.json"


@lru_cache(maxsize=1)
def canonical_coding_lane_contracts() -> dict[str, dict[str, Any]]:
    """Return the only accepted v1 contract catalog, rejecting drift at load time."""
    try:
        value = json.loads(_CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractValidationError("coding lane contract catalog unavailable") from error
    if not isinstance(value, list):
        raise ContractValidationError("coding lane contract catalog must be a list")

    contracts: dict[str, dict[str, Any]] = {}
    for contract in value:
        if not isinstance(contract, dict):
            raise ContractValidationError("coding lane contract entry must be an object")
        validate_contract("coding/lane-contract", contract)
        lane_id = str(contract["lane_id"])
        if lane_id in contracts:
            raise ContractValidationError(f"duplicate coding lane contract:{lane_id}")
        contracts[lane_id] = contract

    if tuple(contracts) != CORE_CODING_LANE_IDS:
        raise ContractValidationError("coding lane contract catalog does not match mandatory lane order")
    return contracts
