from __future__ import annotations

from source_proxy.decision.artifact_behavior_contract import build_artifact_behavior_contract
from source_proxy.decision.artifact_retest_result import build_artifact_retest_result


def _contract() -> dict:
    return build_artifact_behavior_contract(
        prompt="make a calculator app",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )


def _repair_result(status: str = "READY_FOR_RETEST", *, handoff: bool = False) -> dict:
    return {
        "status": status,
        "handoff_required": handoff,
        "handoff_reason": "repair_attempts_exhausted" if handoff else "",
        "attempts_used": 1,
        "changed_files": ["index.html"],
        "diffs": ["--- a/index.html\n+++ b/index.html\n"],
        "reason_codes": ["repair_ready_for_retest"] if not handoff else ["repair_attempts_exhausted"],
    }


def test_repaired_behavior_pass_becomes_final_pass() -> None:
    result = build_artifact_retest_result(
        repair_result=_repair_result(),
        behavior_contract=_contract(),
        artifact_ready=True,
        behavior_result={
            "verdict": "PASS",
            "test": "click 2 + 3 =",
            "observed": {"display": "5"},
            "expected": {"expression": "2 + 3", "result": "5"},
            "actual": {"display": "5"},
            "passed": True,
        },
    )

    assert result["canonical_final_verdict"] == "PASS"
    assert result["product_pass"] is True
    assert result["behavior_result"]["expected"]["result"] == "5"
    assert result["behavior_result"]["actual"]["display"] == "5"
    assert result["behavior_result"]["passed"] is True
    assert "behavior_pass_verified" in result["final_reason_codes"]
    assert "post_repair_behavior_pass" in result["final_reason_codes"]
    assert "post_behavior_repair_pass" in result["final_reason_codes"]


def test_unrepaired_behavior_fail_remains_final_fail() -> None:
    result = build_artifact_retest_result(
        repair_result=_repair_result(),
        behavior_contract=_contract(),
        artifact_ready=True,
        behavior_result={
            "verdict": "FAIL",
            "test": "click 2 + 3 =",
            "observed": {"display": "0"},
            "reason": "display did not equal 5",
        },
    )

    assert result["canonical_final_verdict"] == "FAIL"
    assert result["product_pass"] is False
    assert "behavior_failed" in result["final_reason_codes"]
    assert "post_repair_behavior_fail" in result["final_reason_codes"]
    assert "post_behavior_repair_failed" in result["final_reason_codes"]


def test_missing_preview_after_repair_is_fail_not_pass() -> None:
    result = build_artifact_retest_result(
        repair_result=_repair_result(),
        behavior_contract=_contract(),
        artifact_ready=False,
        behavior_result={
            "verdict": "UNVERIFIED",
            "test": "artifact readiness",
            "observed": {"artifact": "missing"},
            "reason": "preview file missing",
        },
    )

    assert result["canonical_final_verdict"] == "FAIL"
    assert result["product_pass"] is False
    assert "artifact_readiness_failed" in result["final_reason_codes"]
    assert "post_repair_artifact_not_ready" in result["final_reason_codes"]


def test_unverified_behavior_stays_unverified() -> None:
    result = build_artifact_retest_result(
        repair_result=_repair_result(),
        behavior_contract=_contract(),
        artifact_ready=True,
        behavior_result={
            "verdict": "UNVERIFIED",
            "test": "browser verifier skipped",
            "observed": {},
            "reason": "verifier not run",
        },
    )

    assert result["canonical_final_verdict"] == "UNVERIFIED"
    assert result["product_pass"] is False
    assert "behavior_required_but_unverified" in result["final_reason_codes"]


def test_handoff_repair_result_overrides_success_signals() -> None:
    result = build_artifact_retest_result(
        repair_result=_repair_result("HANDOFF", handoff=True),
        behavior_contract=_contract(),
        artifact_ready=True,
        behavior_result={
            "verdict": "PASS",
            "test": "click 2 + 3 =",
            "observed": {"display": "5"},
        },
    )

    assert result["canonical_final_verdict"] == "HANDOFF"
    assert result["product_pass"] is False
    assert result["handoff_required"] is True
    assert "handoff_required" in result["final_reason_codes"]


def test_verifier_error_becomes_needs_fix_not_pass() -> None:
    result = build_artifact_retest_result(
        repair_result=_repair_result(),
        behavior_contract=_contract(),
        artifact_ready=True,
        behavior_result={
            "verdict": "NEEDS_FIX",
            "test": "browser verifier",
            "observed": {},
            "reason": "verifier crashed",
        },
    )

    assert result["canonical_final_verdict"] == "NEEDS_FIX"
    assert result["product_pass"] is False
    assert "post_repair_verifier_needs_fix" in result["final_reason_codes"]


def test_behavior_proof_fields_default_from_verdict_when_missing() -> None:
    result = build_artifact_retest_result(
        repair_result=_repair_result(),
        behavior_contract=_contract(),
        artifact_ready=True,
        behavior_result={
            "verdict": "FAIL",
            "test": "legacy verifier",
            "observed": {"clicked": True},
        },
    )

    assert result["behavior_result"]["expected"] == {}
    assert result["behavior_result"]["actual"] == {}
    assert result["behavior_result"]["passed"] is False
