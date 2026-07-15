from __future__ import annotations

import pytest

from source_proxy.contracts.validation import ContractValidationError, validate_contract
from source_proxy.decision.artifact_retest_result import build_artifact_retest_result


def test_verification_retest_result_is_contract_validated() -> None:
    result = build_artifact_retest_result(
        repair_result={"status": "READY_FOR_RETEST"},
        behavior_contract={"behavior_required": True},
        artifact_ready=True,
        behavior_result={"verdict": "PASS", "passed": True},
    )
    assert result["canonical_final_verdict"] == "PASS"


def test_shared_contract_rejects_deliberate_verdict_violation() -> None:
    with pytest.raises(ContractValidationError, match="canonical_final_verdict"):
        validate_contract(
            "verification/retest-result",
            {
                "result_version": "source-proxy-artifact-retest-result-v0.2.phase-6",
                "repair_status": "READY_FOR_RETEST",
                "artifact_ready": True,
                "behavior_required": True,
                "canonical_final_verdict": "GO",
                "product_pass": True,
                "final_reason_codes": [],
            },
        )
