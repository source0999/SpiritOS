from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class ContractValidationError(ValueError):
    """A boundary payload did not satisfy its shared JSON Schema."""


_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_ROOT = _ROOT / "packages" / "contracts" / "schemas"
_SCHEMAS = {
    "source-proxy/task": "source-proxy/task.schema.json",
    "verification/retest-result": "verification/retest-result.schema.json",
    "shared/applied-run-receipt": "shared/applied-run-receipt.schema.json",
    "design/approval": "design/approval.schema.json",
    "deployment/provenance": "deployment/provenance.schema.json",
    "spiritflix/admin-receipt": "spiritflix/admin-receipt.schema.json",
    "scout/packet": "scout/packet.schema.json",
    "cartographer/proposal": "cartographer/proposal.schema.json",
    "mac-worker/job": "mac-worker/job.schema.json",
    "coding/lane-contract": "coding/lane-contract.schema.json",
}


@lru_cache(maxsize=None)
def contract_validator(name: str) -> Draft202012Validator:
    try:
        relative_path = _SCHEMAS[name]
    except KeyError as error:
        raise ContractValidationError(f"unknown shared contract: {name}") from error
    with (_SCHEMA_ROOT / relative_path).open(encoding="utf-8") as handle:
        return Draft202012Validator(json.load(handle))


def validate_contract(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a transport payload without giving it any lifecycle authority."""
    errors = sorted(contract_validator(name).iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.path) or "<root>"
        raise ContractValidationError(f"{name} invalid at {location}: {first.message}")
    return payload
