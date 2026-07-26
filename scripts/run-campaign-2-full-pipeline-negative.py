#!/usr/bin/env python3
"""Generate a source-bound Campaign 2 negative receipt without product mutation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source_proxy.benchmarks.full_pipeline_authority import (
    APPLICABILITY_POLICY_VERSION,
    FROZEN_TASKS,
    RECEIPT_SCHEMA,
    build_contract,
    current_source_identity,
    score_run,
    write_receipt,
)


def _edge(capability: str) -> dict[str, object]:
    return {
        "registered": True,
        "invoked": True,
        "consumed": True,
        "influential": True,
        "failure_bound": True,
        "receipt_bound": True,
        "canonical_call_id": f"negative-call-{capability}",
        "consumer_ack_id": f"negative-ack-{capability}",
        "counterfactual_id": f"negative-counterfactual-{capability}",
        "failure_receipt_id": f"negative-failure-{capability}",
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
                "predicate": "frozen_campaign_2_negative_control",
                "applicable": True,
            }
            for capability in capabilities
        },
        "causal_edges": {capability: _edge(capability) for capability in capabilities},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--contract-output", type=Path, required=True)
    args = parser.parse_args()

    identity = current_source_identity(ROOT)
    if identity["clean"] != "True":
        print("C2_NEGATIVE_RECEIPT_REFUSED_SOURCE_NOT_CLEAN")
        return 2
    contract = build_contract(source_commit=identity["commit"], source_tree=identity["tree"])
    if args.contract_output.exists():
        print("C2_CONTRACT_REFUSED_PATH_EXISTS")
        return 2
    args.contract_output.parent.mkdir(parents=True, exist_ok=True)
    args.contract_output.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    source_identity = {
        "commit": identity["commit"],
        "tree": identity["tree"],
        "source_clean": True,
        "source_cwd": identity["cwd"],
        "runtime_cwd": identity["cwd"],
        "runtime_commit": identity["commit"],
        "runtime_tree": identity["tree"],
        "remote_commit": identity["commit"],
        "authenticated_principal": "campaign-2-authority-negative-runner",
    }
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "receipt_id": "C2-RCPT-001-negative-control",
        "contract_sha256": contract["contract_sha256"],
        "run_kind": "first",
        "namespace_id": "campaign-2-negative-first-20260726",
        "fresh_state_id": "campaign-2-negative-fresh-20260726",
        "source_runtime_identity": source_identity,
        "oracle_isolation": {
            "isolated_process": True,
            "private_content_available_to_participant": False,
            "forbidden_import_detected": False,
            "private_oracle_digest": "0" * 64,
            "access_audit": ["independent_verifier"],
        },
        "tasks": [_task_receipt(task, str(contract["contract_sha256"])) for task in FROZEN_TASKS],
        "injected_failure": "C2-FI-002",
        "claim": "a registered and invoked layer whose output is not consumed cannot pass",
    }
    # Deliberately neutralize the selected task's repository-discovery output.
    receipt["tasks"][2]["causal_edges"]["repository_discovery"]["consumed"] = False
    receipt["tasks"][2]["causal_edges"]["repository_discovery"]["consumer_ack_id"] = ""
    result = score_run(receipt, contract)
    if result.accepted or "C2-T03:repository_discovery:consumed_missing" not in result.failures:
        print("C2_NEGATIVE_CONTROL_DID_NOT_FAIL_CLOSED")
        return 1
    receipt["authority_result"] = result.as_dict()
    digest = write_receipt(args.output, receipt)
    args.contract_output.chmod(0o444)
    print("C2_NEGATIVE_CONTROL_REJECTED_NONCONSUMED_LAYER")
    print(f"receipt_sha256:{digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
