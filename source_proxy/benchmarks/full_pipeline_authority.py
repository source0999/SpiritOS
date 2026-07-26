"""Frozen, fail-closed authority checks for the Campaign 2 benchmark.

This module evaluates receipts emitted by the canonical coding path.  It is not
an alternate executor: it never creates a task, supplies a patch, changes a
terminal state, or reads private oracle content.  A later Campaign can add a
versioned capability slice, but cannot weaken this contract in place.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


CONTRACT_SCHEMA = "source-proxy-full-pipeline-authority/v1"
RECEIPT_SCHEMA = "source-proxy-full-pipeline-receipt/v1"
CONTRACT_VERSION = "C2-FPA-001"
APPLICABILITY_POLICY_VERSION = "C2-APPLICABILITY-001"
SUCCESS_TOKEN = "CAMPAIGN_2_FULL_PIPELINE_BENCHMARK_AUTHORITY_ACCEPTED"
BLOCKED_TOKEN = "CAMPAIGN_2_BLOCKED_BENCHMARK_AUTHORITY_INCOMPLETE"
BASIC_BACKEND_TOKEN = "LOCAL_PROXY_BASIC_CODING_GATE_PASSED"


class FullPipelineAuthorityError(ValueError):
    """The contract or a receipt is not authoritative."""


@dataclass(frozen=True)
class AuthorityResult:
    accepted: bool
    terminal_token: str
    failures: tuple[str, ...]
    task_results: Mapping[str, Mapping[str, Any]]
    score: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "terminal_token": self.terminal_token,
            "failures": list(self.failures),
            "task_results": {key: dict(value) for key, value in self.task_results.items()},
            "score": self.score,
        }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _task(task_id: str, repository_class: str, capability: str, description: str) -> dict[str, str]:
    body = {
        "task_id": task_id,
        "repository_class": repository_class,
        "capability": capability,
        "description": description,
    }
    return {**body, "task_sha256": _sha256(body)}


FROZEN_TASKS = (
    _task("C2-T01", "controlled", "single_file_validation", "single-file validation baseline"),
    _task("C2-T02", "controlled", "multi_file_service_change", "multi-file service change"),
    _task("C2-T03", "unfamiliar", "repository_discovery", "repository discovery and context selection"),
    _task("C2-T04", "unfamiliar", "context_expansion", "context insufficiency requiring expansion"),
    _task("C2-T05", "controlled", "review_correction", "reviewer rejection and materially changed proposal"),
    _task("C2-T06", "controlled", "verifier_repair", "verifier failure and evidence-grounded repair"),
    _task("C2-T07", "unfamiliar", "strategy_change", "failure classification requiring changed strategy"),
    _task("C2-T08", "controlled", "escalation_or_refusal", "authorized escalation or truthful refusal"),
    _task("C2-T09", "unfamiliar", "restart_resume", "restart, resume, or cross-service evidence"),
    _task("C2-T10", "controlled", "negative_controls", "wrong-file, replay, fabrication, no-progress, impossible-task controls"),
)

# Every task always requires the canonical lifecycle and producer-owned terminal
# truth.  The selected capability is additionally required for its task; future
# Campaign 3-6 slices are deliberately represented as requirements, not labels.
BASE_CAPABILITIES = ("canonical_lifecycle", "terminal_truth")


def _required_capabilities(task: Mapping[str, Any]) -> tuple[str, ...]:
    return (*BASE_CAPABILITIES, str(task["capability"]))


def build_contract(*, source_commit: str, source_tree: str) -> dict[str, Any]:
    """Return the immutable public contract body for the selected source."""
    task_manifest = [dict(task) for task in FROZEN_TASKS]
    body = {
        "schema_version": CONTRACT_SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "campaign_id": "campaign-2",
        "source_commit": source_commit,
        "source_tree": source_tree,
        "task_manifest": task_manifest,
        "task_manifest_sha256": _sha256(task_manifest),
        "applicability_policy_version": APPLICABILITY_POLICY_VERSION,
        "required_boundaries": [
            "registered",
            "invoked",
            "consumed",
            "influential",
            "failure_bound",
            "receipt_bound",
        ],
        "literal_task_threshold": "10/10",
        "zero_safety_failure_required": True,
        "first_and_clean_rerun_required": True,
        "canonical_authenticated_entry_required": True,
        "private_oracle_isolation_required": True,
        "basic_backend_10_authority": "VALID_CORE_GATE_NOT_FULL_PIPELINE_GATE",
        "future_slice_policy": "versioned_add_only_no_weakening",
    }
    return {**body, "contract_sha256": _sha256(body)}


def validate_contract(contract: Mapping[str, Any]) -> list[str]:
    """Re-derive all frozen fields instead of trusting a claimed digest."""
    failures: list[str] = []
    if contract.get("schema_version") != CONTRACT_SCHEMA:
        failures.append("contract_schema_invalid")
    if contract.get("contract_version") != CONTRACT_VERSION:
        failures.append("contract_version_invalid")
    tasks = contract.get("task_manifest")
    if not isinstance(tasks, list) or tasks != [dict(task) for task in FROZEN_TASKS]:
        failures.append("contract_task_manifest_mutated")
    elif contract.get("task_manifest_sha256") != _sha256(tasks):
        failures.append("contract_task_manifest_digest_invalid")
    source_commit = str(contract.get("source_commit") or "")
    source_tree = str(contract.get("source_tree") or "")
    if len(source_commit) != 40 or len(source_tree) != 40:
        failures.append("contract_source_identity_invalid")
    expected = build_contract(source_commit=source_commit, source_tree=source_tree)
    if contract.get("contract_sha256") != expected["contract_sha256"]:
        failures.append("contract_digest_invalid")
    if contract.get("literal_task_threshold") != "10/10":
        failures.append("contract_threshold_not_literal_10_of_10")
    if contract.get("basic_backend_10_authority") != "VALID_CORE_GATE_NOT_FULL_PIPELINE_GATE":
        failures.append("contract_basic_backend_authority_invalid")
    return failures


def current_source_identity(root: Path) -> dict[str, str]:
    """Read Git identity only; no runtime or checkout mutation occurs."""
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    return {
        "branch": git("branch", "--show-current"),
        "commit": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "cwd": str(root.resolve()),
        "clean": str(not bool(git("status", "--porcelain=v1", "--untracked-files=all"))),
    }


def _is_truthy(value: Any) -> bool:
    return value is True


def _require_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _validate_oracle(oracle: Mapping[str, Any] | None) -> list[str]:
    if oracle is None:
        return ["oracle_missing"]
    failures: list[str] = []
    if not _is_truthy(oracle.get("isolated_process")):
        failures.append("oracle_not_isolated")
    if _is_truthy(oracle.get("private_content_available_to_participant")):
        failures.append("oracle_private_content_leaked")
    if _is_truthy(oracle.get("forbidden_import_detected")):
        failures.append("oracle_import_boundary_breached")
    if not isinstance(oracle.get("private_oracle_digest"), str) or len(str(oracle.get("private_oracle_digest"))) != 64:
        failures.append("oracle_digest_invalid")
    access = oracle.get("access_audit")
    if not isinstance(access, list) or any(str(actor) in {"coder", "recovery", "tool", "retrieval"} for actor in access):
        failures.append("oracle_access_audit_invalid")
    return failures


def _validate_identity(receipt: Mapping[str, Any], contract: Mapping[str, Any]) -> list[str]:
    identity = _require_mapping(receipt.get("source_runtime_identity"))
    if identity is None:
        return ["source_runtime_identity_missing"]
    failures: list[str] = []
    for key, contract_key in (("commit", "source_commit"), ("tree", "source_tree")):
        if identity.get(key) != contract.get(contract_key):
            failures.append(f"source_runtime_{key}_mismatch")
    if not _is_truthy(identity.get("source_clean")):
        failures.append("source_runtime_source_not_clean")
    if identity.get("runtime_cwd") != identity.get("source_cwd"):
        failures.append("source_runtime_cwd_mismatch")
    if identity.get("runtime_commit") != identity.get("commit") or identity.get("runtime_tree") != identity.get("tree"):
        failures.append("source_runtime_loaded_identity_mismatch")
    if identity.get("remote_commit") != identity.get("commit"):
        failures.append("source_runtime_remote_mismatch")
    if not identity.get("authenticated_principal"):
        failures.append("source_runtime_authentication_missing")
    return failures


def _validate_task(
    task_receipt: Mapping[str, Any] | None,
    task: Mapping[str, Any],
    *,
    contract_digest: str,
) -> tuple[list[str], dict[str, Any]]:
    task_id = str(task["task_id"])
    if task_receipt is None:
        return [f"{task_id}:receipt_missing"], {"passed": False, "failure_count": 1}
    failures: list[str] = []
    if task_receipt.get("task_sha256") != task["task_sha256"]:
        failures.append(f"{task_id}:task_identity_mismatch")
    if task_receipt.get("contract_sha256") != contract_digest:
        failures.append(f"{task_id}:contract_digest_mismatch")
    if task_receipt.get("canonical_entry") != "authenticated_coding_api":
        failures.append(f"{task_id}:canonical_entry_missing")
    if task_receipt.get("terminal_truth_producer") != "coding_orchestrator":
        failures.append(f"{task_id}:terminal_truth_not_producer_owned")
    if _is_truthy(task_receipt.get("report_time_terminal_repair")):
        failures.append(f"{task_id}:report_time_terminal_repair")
    applicability = _require_mapping(task_receipt.get("applicability"))
    edges = _require_mapping(task_receipt.get("causal_edges"))
    if applicability is None or edges is None:
        failures.append(f"{task_id}:causal_evidence_missing")
        return failures, {"passed": False, "failure_count": len(failures)}
    for capability in _required_capabilities(task):
        decision = _require_mapping(applicability.get(capability))
        edge = _require_mapping(edges.get(capability))
        if decision is None:
            failures.append(f"{task_id}:{capability}:applicability_missing")
            continue
        if decision.get("policy_version") != APPLICABILITY_POLICY_VERSION:
            failures.append(f"{task_id}:{capability}:applicability_policy_invalid")
        if decision.get("decided_before_outcome") is not True:
            failures.append(f"{task_id}:{capability}:applicability_post_outcome")
        if not isinstance(decision.get("predicate"), str) or not decision.get("predicate"):
            failures.append(f"{task_id}:{capability}:applicability_predicate_missing")
        if decision.get("applicable") is not True:
            failures.append(f"{task_id}:{capability}:required_capability_skipped")
            continue
        if edge is None:
            failures.append(f"{task_id}:{capability}:causal_edge_missing")
            continue
        for boundary in ("registered", "invoked", "consumed", "influential", "failure_bound", "receipt_bound"):
            if edge.get(boundary) is not True:
                failures.append(f"{task_id}:{capability}:{boundary}_missing")
        if not edge.get("canonical_call_id"):
            failures.append(f"{task_id}:{capability}:canonical_call_missing")
        if not edge.get("consumer_ack_id"):
            failures.append(f"{task_id}:{capability}:consumer_ack_missing")
        if not edge.get("counterfactual_id"):
            failures.append(f"{task_id}:{capability}:counterfactual_missing")
        if not edge.get("failure_receipt_id"):
            failures.append(f"{task_id}:{capability}:failure_receipt_missing")
        if edge.get("mocked") is True or edge.get("sidecar_only") is True:
            failures.append(f"{task_id}:{capability}:noncanonical_integration")
    if task_receipt.get("declared_passed") is True and failures:
        failures.append(f"{task_id}:declared_score_disagrees_with_rederivation")
    return failures, {"passed": not failures, "failure_count": len(failures)}


def score_run(receipt: Mapping[str, Any], contract: Mapping[str, Any]) -> AuthorityResult:
    """Strictly score one first-run or clean-rerun receipt without upgrading it."""
    failures = validate_contract(contract)
    if receipt.get("schema_version") != RECEIPT_SCHEMA:
        failures.append("receipt_schema_invalid")
    if receipt.get("contract_sha256") != contract.get("contract_sha256"):
        failures.append("receipt_contract_digest_mismatch")
    if receipt.get("run_kind") not in {"first", "clean_rerun"}:
        failures.append("receipt_run_kind_invalid")
    if not receipt.get("namespace_id") or not receipt.get("fresh_state_id"):
        failures.append("receipt_fresh_namespace_missing")
    failures.extend(_validate_identity(receipt, contract))
    failures.extend(_validate_oracle(_require_mapping(receipt.get("oracle_isolation"))))
    receipts = receipt.get("tasks")
    by_id: dict[str, Mapping[str, Any]] = {}
    if not isinstance(receipts, list):
        failures.append("receipt_tasks_invalid")
    else:
        for item in receipts:
            mapping = _require_mapping(item)
            if mapping is None or not mapping.get("task_id"):
                failures.append("receipt_task_entry_invalid")
                continue
            task_id = str(mapping["task_id"])
            if task_id in by_id:
                failures.append(f"receipt_task_duplicate:{task_id}")
            by_id[task_id] = mapping
    if set(by_id) != {str(task["task_id"]) for task in FROZEN_TASKS}:
        failures.append("receipt_literal_ten_task_set_required")
    results: dict[str, Mapping[str, Any]] = {}
    for task in FROZEN_TASKS:
        task_failures, task_result = _validate_task(
            by_id.get(str(task["task_id"])), task, contract_digest=str(contract.get("contract_sha256") or "")
        )
        failures.extend(task_failures)
        results[str(task["task_id"])] = task_result
    accepted = not failures and all(item["passed"] for item in results.values())
    return AuthorityResult(
        accepted=accepted,
        terminal_token=SUCCESS_TOKEN if accepted else BLOCKED_TOKEN,
        failures=tuple(sorted(set(failures))),
        task_results=results,
        score="10/10" if accepted else f"{sum(item['passed'] for item in results.values())}/10",
    )


def score_campaign(
    first_receipt: Mapping[str, Any],
    clean_rerun_receipt: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    operator_accepted: bool,
) -> AuthorityResult:
    """Require two independently fresh, literal 10/10 receipts for a token."""
    first = score_run(first_receipt, contract)
    clean = score_run(clean_rerun_receipt, contract)
    failures = [f"first:{reason}" for reason in first.failures]
    failures.extend(f"clean_rerun:{reason}" for reason in clean.failures)
    if first_receipt.get("run_kind") != "first":
        failures.append("first:run_kind_not_first")
    if clean_rerun_receipt.get("run_kind") != "clean_rerun":
        failures.append("clean_rerun:run_kind_not_clean_rerun")
    for field in ("namespace_id", "fresh_state_id"):
        if first_receipt.get(field) == clean_rerun_receipt.get(field):
            failures.append(f"clean_rerun:{field}_reused")
    if not operator_accepted:
        failures.append("operator_acceptance_missing")
    accepted = not failures and first.accepted and clean.accepted
    return AuthorityResult(
        accepted=accepted,
        terminal_token=SUCCESS_TOKEN if accepted else BLOCKED_TOKEN,
        failures=tuple(sorted(set(failures))),
        task_results={"first": first.as_dict(), "clean_rerun": clean.as_dict()},
        score="10/10" if accepted else "not_authoritative",
    )


def reject_basic_backend_full_pipeline_token(token: str) -> None:
    """Basic Backend 10 is a diagnostic gate and cannot issue this token."""
    if token == BASIC_BACKEND_TOKEN or token == SUCCESS_TOKEN:
        raise FullPipelineAuthorityError("basic_backend_10_cannot_authorize_full_pipeline")


def write_receipt(path: Path, receipt: Mapping[str, Any]) -> str:
    """Write a new immutable receipt with a deterministic public digest."""
    if path.exists():
        raise FullPipelineAuthorityError("receipt_path_already_exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    body = dict(receipt)
    body["receipt_sha256"] = _sha256(body)
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(path, 0o444)
    return str(body["receipt_sha256"])
