from __future__ import annotations

import copy

import pytest

from source_proxy.benchmarks.full_pipeline_authority import (
    APPLICABILITY_POLICY_VERSION,
    BLOCKED_TOKEN,
    FROZEN_TASKS,
    FullPipelineAuthorityError,
    SUCCESS_TOKEN,
    build_contract,
    reject_basic_backend_full_pipeline_token,
    score_campaign,
    score_run,
    validate_contract,
)


COMMIT = "a" * 40
TREE = "b" * 40


def _edge(capability: str) -> dict[str, object]:
    return {
        "registered": True,
        "invoked": True,
        "consumed": True,
        "influential": True,
        "failure_bound": True,
        "receipt_bound": True,
        "canonical_call_id": f"call-{capability}",
        "consumer_ack_id": f"ack-{capability}",
        "counterfactual_id": f"counterfactual-{capability}",
        "failure_receipt_id": f"failure-{capability}",
        "mocked": False,
        "sidecar_only": False,
    }


def _task_receipt(task: dict[str, str], contract_digest: str) -> dict[str, object]:
    capabilities = ("canonical_lifecycle", "terminal_truth", task["capability"])
    return {
        "task_id": task["task_id"],
        "task_sha256": task["task_sha256"],
        "contract_sha256": contract_digest,
        "canonical_entry": "authenticated_coding_api",
        "terminal_truth_producer": "coding_orchestrator",
        "report_time_terminal_repair": False,
        "declared_passed": True,
        "applicability": {
            capability: {
                "policy_version": APPLICABILITY_POLICY_VERSION,
                "decided_before_outcome": True,
                "predicate": "task_capability_required",
                "applicable": True,
            }
            for capability in capabilities
        },
        "causal_edges": {capability: _edge(capability) for capability in capabilities},
    }


def _receipt(contract: dict[str, object], *, run_kind: str, namespace: str, state: str) -> dict[str, object]:
    return {
        "schema_version": "source-proxy-full-pipeline-receipt/v1",
        "contract_sha256": contract["contract_sha256"],
        "run_kind": run_kind,
        "namespace_id": namespace,
        "fresh_state_id": state,
        "source_runtime_identity": {
            "commit": COMMIT,
            "tree": TREE,
            "source_clean": True,
            "source_cwd": "/isolated/source",
            "runtime_cwd": "/isolated/source",
            "runtime_commit": COMMIT,
            "runtime_tree": TREE,
            "remote_commit": COMMIT,
            "authenticated_principal": "source-proxy-benchmark",
        },
        "oracle_isolation": {
            "isolated_process": True,
            "private_content_available_to_participant": False,
            "forbidden_import_detected": False,
            "private_oracle_digest": "c" * 64,
            "access_audit": ["independent_verifier"],
        },
        "tasks": [_task_receipt(task, str(contract["contract_sha256"])) for task in FROZEN_TASKS],
    }


def _contract() -> dict[str, object]:
    return build_contract(source_commit=COMMIT, source_tree=TREE)


def test_contract_freezes_literal_ten_task_manifest() -> None:
    contract = _contract()
    assert validate_contract(contract) == []
    contract["task_manifest"] = contract["task_manifest"][:-1]
    assert "contract_task_manifest_mutated" in validate_contract(contract)


def test_campaign_requires_two_independent_literal_ten_of_ten_runs() -> None:
    contract = _contract()
    result = score_campaign(
        _receipt(contract, run_kind="first", namespace="first", state="state-first"),
        _receipt(contract, run_kind="clean_rerun", namespace="clean", state="state-clean"),
        contract,
        operator_accepted=True,
    )
    assert result.accepted is True
    assert result.score == "10/10"
    assert result.terminal_token == SUCCESS_TOKEN


def test_consumed_boundary_is_rederived_not_trusted_from_declared_score() -> None:
    contract = _contract()
    receipt = _receipt(contract, run_kind="first", namespace="first", state="state-first")
    task = receipt["tasks"][2]
    task["causal_edges"]["repository_discovery"]["consumed"] = False
    result = score_run(receipt, contract)
    assert result.accepted is False
    assert result.terminal_token == BLOCKED_TOKEN
    assert "C2-T03:repository_discovery:consumed_missing" in result.failures
    assert "C2-T03:declared_score_disagrees_with_rederivation" in result.failures


@pytest.mark.parametrize("field", ["mocked", "sidecar_only"])
def test_mocked_or_sidecar_layer_cannot_pass(field: str) -> None:
    contract = _contract()
    receipt = _receipt(contract, run_kind="first", namespace="first", state="state-first")
    receipt["tasks"][4]["causal_edges"]["review_correction"][field] = True
    result = score_run(receipt, contract)
    assert "C2-T05:review_correction:noncanonical_integration" in result.failures


def test_missing_task_cannot_be_averaged_away() -> None:
    contract = _contract()
    receipt = _receipt(contract, run_kind="first", namespace="first", state="state-first")
    receipt["tasks"] = receipt["tasks"][:-1]
    result = score_run(receipt, contract)
    assert result.accepted is False
    assert "receipt_literal_ten_task_set_required" in result.failures
    assert "C2-T10:receipt_missing" in result.failures


def test_stale_runtime_and_oracle_leak_hard_fail() -> None:
    contract = _contract()
    receipt = _receipt(contract, run_kind="first", namespace="first", state="state-first")
    receipt["source_runtime_identity"]["runtime_commit"] = "d" * 40
    receipt["oracle_isolation"]["access_audit"] = ["independent_verifier", "coder"]
    result = score_run(receipt, contract)
    assert "source_runtime_loaded_identity_mismatch" in result.failures
    assert "oracle_access_audit_invalid" in result.failures


def test_clean_rerun_reused_state_and_missing_operator_acceptance_block_token() -> None:
    contract = _contract()
    first = _receipt(contract, run_kind="first", namespace="same", state="same-state")
    clean = _receipt(contract, run_kind="clean_rerun", namespace="same", state="same-state")
    result = score_campaign(first, clean, contract, operator_accepted=False)
    assert result.accepted is False
    assert "clean_rerun:namespace_id_reused" in result.failures
    assert "clean_rerun:fresh_state_id_reused" in result.failures
    assert "operator_acceptance_missing" in result.failures


def test_basic_backend_token_is_not_a_full_pipeline_authority() -> None:
    with pytest.raises(FullPipelineAuthorityError, match="cannot_authorize"):
        reject_basic_backend_full_pipeline_token("LOCAL_PROXY_BASIC_CODING_GATE_PASSED")
    with pytest.raises(FullPipelineAuthorityError, match="cannot_authorize"):
        reject_basic_backend_full_pipeline_token(SUCCESS_TOKEN)
