#!/usr/bin/env python3
"""Fail closed when Campaign 2's canonical lane contracts or registry drift."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source_proxy.cartographer.lane_registry import (
    CORE_CODING_LANE_IDS,
    build_canonical_coding_lane_registry,
    build_lane_registry_model_status,
    validate_lane_registry_record,
)
from source_proxy.contracts.coding_lane_contracts import canonical_coding_lane_contracts
from source_proxy.contracts.validation import ContractValidationError


def main() -> int:
    failures: list[str] = []
    try:
        contracts = canonical_coding_lane_contracts()
    except ContractValidationError as error:
        print("CAMPAIGN_2_AUTHORITY_INVALID")
        print(f"contract_catalog_invalid:{error}")
        return 1

    registry = build_canonical_coding_lane_registry()
    if tuple(contracts) != CORE_CODING_LANE_IDS:
        failures.append("mandatory_contract_order_mismatch")
    if tuple(record.lane_id for record in registry) != CORE_CODING_LANE_IDS:
        failures.append("mandatory_registry_order_mismatch")
    for record in registry:
        validation = validate_lane_registry_record(record)
        if not validation.accepted:
            failures.extend(f"registry_invalid:{record.lane_id}:{reason}" for reason in validation.reason_codes)
        contract = contracts.get(record.lane_id, {})
        if record.contract_name != "coding/lane-contract":
            failures.append(f"registry_contract_name_mismatch:{record.lane_id}")
        for field in ("contract_version", "authority_class", "deprecation_state"):
            if getattr(record, field) != contract.get(field):
                failures.append(f"registry_contract_mismatch:{record.lane_id}:{field}")
        if list(record.compatible_consumer_versions) != contract.get("compatible_consumer_versions"):
            failures.append(f"registry_contract_mismatch:{record.lane_id}:compatible_consumer_versions")
        if record.authority_granted or record.can_mutate or record.write_actions_enabled:
            failures.append(f"registry_grants_unscoped_authority:{record.lane_id}")
    status = build_lane_registry_model_status()
    if status.get("status") != "authority-bearing":
        failures.append("registry_model_only_status_not_superseded")
    if failures:
        print("CAMPAIGN_2_AUTHORITY_INVALID")
        print("\n".join(failures))
        return 1
    print("CAMPAIGN_2_AUTHORITY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
