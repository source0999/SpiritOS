from __future__ import annotations

import json
import hashlib
import contextlib
import copy
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping

import pytest

from source_proxy.benchmarks.campaign_3_5_basic_assets.catalog import (
    EXPECTED_TASK_IDS,
    load_basic_backend_tasks,
    render_basic_backend_task,
)
from source_proxy.benchmarks.campaign_3_5_basic_assets.fixtures import (
    materialize_basic_backend_fixture,
)
from source_proxy.benchmarks.campaign_3_5_basic_assets.references import apply_reference
from source_proxy.benchmarks.campaign_3_5_basic_assets.seeding import (
    BasicBackendRunSeed,
)
from source_proxy.benchmarks.campaign_3_5_basic_gate_runner import (
    BasicBackendGateConfig,
    BasicBackendGateError,
    BasicBackendGateRunner,
    HttpExchange,
    OperatorAssertionSigner,
    RunningGateService,
    _NEUTRAL_PROBE_WORKER,
    _audit_fixture_mutations,
    _attempt_model_provenance_verified,
    _completion_claim_audit,
    _evaluation_contract,
    _finalize_service_import_audit,
    _git,
    _hidden_answer_leak_audit,
    _load_and_validate_first_phase_manifest,
    _parse_neutral_probe_output,
    _private_probe_spec,
    _private_oracle_evidence_valid,
    _proposal_material,
    _service_environment,
    _sha256_file,
    _sha256_json,
    _sha256_text,
    _trusted_private_oracle_decision,
    _rederive_repair_succeeded,
    _rederive_task_receipt_score,
    _scan_production_evidence,
    _workspace_diff,
    reconcile_basic_backend_trace,
    run_private_oracle_container,
)


ROOT = Path(__file__).resolve().parents[2]
TEST_BRANCH = "codex/campaign-3-5-execution-20260719"
TEST_FIRST_HEAD = "a" * 40
TEST_IMAGE_ID = "sha256:" + "b" * 64


def _fake_sandbox_image() -> dict[str, Any]:
    body = {
        "schema_version": "source-proxy-sandbox-image-identity/v1",
        "requested_image": "test-image:latest",
        "image_id": TEST_IMAGE_ID,
        "repo_digests": ["test-image@sha256:" + "c" * 64],
    }
    return {**body, "identity_sha256": _sha256_json(body)}


def _fake_model_inventory() -> dict[str, Any]:
    runtime_body = {
        "schema_version": "source-proxy-verifier-host-runtime/v1",
        "python_executable": str(Path(sys.executable).resolve()),
        "python_executable_sha256": "d" * 64,
        "python_version": "test-python",
        "distributions": [],
    }
    runtime = {**runtime_body, "runtime_sha256": _sha256_json(runtime_body)}
    models = [
        {
            "role": role,
            "alias": alias,
            "provider": "ollama",
            "routed_model": routed_model,
            "artifact_digest": digest,
        }
        for role, alias, routed_model, digest in (
            ("architect", "local", "ollama_chat/fake-local", "1" * 64),
            ("coder_fallback", "local", "ollama_chat/fake-local", "1" * 64),
            ("coder_primary", "coder", "ollama_chat/fake-coder", "2" * 64),
            ("coder_repair", "local", "ollama_chat/fake-local", "1" * 64),
        )
    ]
    body = {
        "schema_version": "source-proxy-local-model-inventory/v1",
        "ollama_base_url": "http://127.0.0.1:11434",
        "tags_response_sha256": "3" * 64,
        "models": models,
        "verifier_runtime": runtime,
        "verifier_runtime_sha256": runtime["runtime_sha256"],
    }
    return {**body, "inventory_sha256": _sha256_json(body)}


def _fake_preflight(*, head: str = TEST_FIRST_HEAD) -> dict[str, Any]:
    return {
        "passed": True,
        "branch": TEST_BRANCH,
        "head": head,
        "clean": True,
        "evaluation_contract": _evaluation_contract(ROOT),
        "sandbox_image": _fake_sandbox_image(),
        "model_inventory": _fake_model_inventory(),
    }


class FakeLifecycleClient:
    def __init__(self, evidence_root: Path) -> None:
        self.evidence_root = evidence_root
        self.exchanges: list[HttpExchange] = []
        self.paths: list[tuple[str, str, Mapping[str, Any] | None]] = []
        self.task_id = "production-task-123"
        self.proposal_number = 0
        self.approval_number = 0
        self.final = False

    def request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        *,
        headers: Mapping[str, str] | None = None,
        allow_error: bool = False,
        authenticated: bool = False,
    ) -> HttpExchange:
        del allow_error
        self.paths.append((method, path, payload))
        if path == "/v1/campaigns/campaign-3.5/model-call-authority":
            response: dict[str, Any] = {"state": "approved", "authorization_id": "mca-test"}
        elif path == "/v1/tasks/long-running" and method == "POST":
            response = {"task": {"id": self.task_id}, "coding_orchestrator": self._state()}
        elif path.endswith("/target-plugin-proposal"):
            self.proposal_number += 1
            response = self._state(with_proposal=True)
            response["target_plugin_result"] = {"proposed_diff": self._diff()}
        elif path.endswith("/approval-preview"):
            response = {
                "authority": "spiritos-approval-authority",
                "consumer": "coding-executor",
                "preview": {
                    "preview_id": f"preview-{self.proposal_number}",
                    "generation": self.proposal_number,
                    "state": "previewed",
                },
            }
        elif path.endswith("/operator-approval"):
            self.approval_number += 1
            response = {
                "approval": {
                    "approval_id": f"approval-{self.approval_number}",
                    "generation": self.approval_number,
                    "state": "approved",
                }
            }
        elif path.endswith("/execute-approved"):
            response = {"task": {"id": self.task_id}, "coding_orchestrator": self._state(with_proposal=True)}
        elif path.endswith("/verification"):
            if self.proposal_number == 1:
                response = {
                    "repair_required": True,
                    "task": {"id": self.task_id, "status": "verification_failed"},
                    "coding_orchestrator": self._state(repair=True),
                }
            else:
                self.final = True
                response = self._final_response()
        elif path.endswith(self.task_id) and method == "GET":
            response = self._final_response() if self.final else {
                "task": {"id": self.task_id, "status": "running"},
                "coding_orchestrator": self._state(repair=self.proposal_number == 1),
            }
        else:  # pragma: no cover - reveals a new production call immediately
            raise AssertionError((method, path, payload))
        raw = json.dumps(response, sort_keys=True).encode()
        ordinal = len(self.exchanges) + 1
        evidence = self.evidence_root / f"exchange-{ordinal}.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_bytes(raw)
        assertion_present = bool(
            str((headers or {}).get("x-spiritos-operator-assertion") or "").strip()
        )
        status_code = 200
        server_acknowledged = (
            (
                path == "/v1/campaigns/campaign-3.5/model-call-authority"
                and response.get("state") == "approved"
                and response.get("authorization_id")
            )
            or (
                path.endswith("/operator-approval")
                and isinstance(response.get("approval"), Mapping)
                and response["approval"].get("state") == "approved"
                and response["approval"].get("approval_id")
            )
        )
        authentication = {
            "scheme": "signed_operator_assertion",
            "assertion_present": assertion_present,
            "server_acknowledged": bool(server_acknowledged),
            "caller_claimed_authenticated": authenticated,
            "authenticated": bool(assertion_present and server_acknowledged),
        }
        exchange = HttpExchange(
            ordinal=ordinal,
            method=method,
            path=path,
            status_code=status_code,
            request_sha256="1" * 64,
            response_sha256=f"{ordinal:064x}"[-64:],
            response=response,
            evidence_file=str(evidence),
            authenticated=authentication["authenticated"],
            elapsed_ms=1,
            authentication=authentication,
        )
        self.exchanges.append(exchange)
        return exchange

    def _diff(self) -> str:
        number = self.proposal_number
        return (
            "diff --git a/src/backend.py b/src/backend.py\n"
            "--- a/src/backend.py\n"
            "+++ b/src/backend.py\n"
            "@@ -1 +1,2 @@\n"
            " from __future__ import annotations\n"
            f"+# repair attempt {number}\n"
        )

    def _state(self, *, with_proposal: bool = False, repair: bool = False) -> dict[str, Any]:
        events = [
            {"event_type": "run_requested", "event_id": "event-run"},
            {
                "event_type": "lane_transition",
                "event_id": "event-planner",
                "lane_id": "planner",
                "status_after": "completed",
            },
        ]
        state: dict[str, Any] = {
            "schema_version": "coding-orchestrator/v2",
            "authoritative": True,
            "task_id": self.task_id,
            "run_id": "run-test",
            "attempt_id": f"attempt-{max(1, self.proposal_number)}",
            "causal_events": events,
            "runtime_outputs": [],
            "participant_records": [],
            "attempt_history": [],
        }
        if with_proposal:
            diff = self._diff()
            output_id = f"output-{self.proposal_number}"
            proposal = {
                "runtime_output_id": output_id,
                "approved_diff_sha256": __import__("hashlib").sha256(diff.encode()).hexdigest(),
                "producer_model_invocation_id": f"model-{self.proposal_number}",
                "producer_model_output_sha256": f"{self.proposal_number + 20:064x}"[-64:],
                "target": "src/backend.py",
                "context_hash": "c" * 64,
                "canonical_context_report_sha256": "d" * 64,
                "context_runtime_artifact_sha256": "e" * 64,
                "context_consumption_id": f"consumption-{self.proposal_number}",
                "status": "ready_for_approval_preview",
                "proposal_binding_sha256": f"{self.proposal_number:064x}"[-64:],
                "attempt_id": f"attempt-{self.proposal_number}",
                "parent_attempt_id": None if self.proposal_number == 1 else "attempt-1",
            }
            raw_response_sha256 = f"{self.proposal_number + 30:064x}"[-64:]
            proposal["target_adapter_provenance"] = {
                "call_count": 1,
                "producer_call_index": 1,
                "rendered_prompt_sha256": f"{self.proposal_number + 40:064x}"[-64:],
                "raw_response_sha256": raw_response_sha256,
                "selected_model_alias": "local-coder",
                "provider": "ollama",
                "model": "ollama_chat/local-coder",
                "routed_model": "ollama_chat/local-coder",
                "transport_kind": "canonical_litellm_router",
                "provider_call_authorized": True,
                "model_call_accounting_complete": True,
                "producer_identity_bound": True,
                "calls": [
                    {
                        "call_index": 1,
                        "stage": "coder",
                        "completed": True,
                        "raw_response_observed": True,
                        "rendered_prompt_sha256": f"{self.proposal_number + 40:064x}"[-64:],
                        "raw_response_sha256": raw_response_sha256,
                        "model_alias": "local-coder",
                        "provider": "ollama",
                        "model": "ollama_chat/local-coder",
                        "routed_model": "ollama_chat/local-coder",
                    }
                ],
            }
            state["target_plugin_proposal"] = proposal
            state["model_invocations"] = [
                {
                    "invocation_id": f"model-{self.proposal_number}",
                    "provider": "ollama",
                    "model": "ollama_chat/local-coder",
                    "input_sha256": "1" * 64,
                    "output_sha256": proposal["producer_model_output_sha256"],
                    "artifact_sha256": "a" * 64,
                }
            ]
            state["runtime_outputs"] = [
                {"output_id": output_id, "payload": {"approved_diff": diff, "changed_files": ["src/backend.py"]}}
            ]
            events.append(
                {"event_type": "target_plugin_proposal_ready", "event_id": f"event-proposal-{self.proposal_number}"}
            )
        if repair:
            state["repair_request"] = {"failure_class": "verifier_rejection"}
        return state

    def _final_response(self) -> dict[str, Any]:
        state = self._state(with_proposal=True)
        state["causal_events"].extend(
            [
                {"event_type": "post_apply_verification_requested", "event_id": "event-verify"},
                {"event_type": "final_result", "event_id": "event-final"},
            ]
        )
        state["participant_records"] = [
            {"role": "coding-reviewer", "output_id": "review-output"},
            {"role": "coding-verifier", "output_id": "verify-output"},
            {"role": "evidence-recorder", "output_id": "evidence-output"},
        ]
        return {
            "task": {
                "id": self.task_id,
                "status": "completed",
                "ast_snapshot": {
                    "coding_orchestrator": state,
                    "coding_production_proof": {"terminal_proof_eligible": True, "proof_sha256": "p" * 64},
                    "post_apply_verification": {
                        "status": "verified",
                        "checks": [{"id": "generic_backend_pytest", "required": True, "status": "passed"}],
                    },
                },
            }
        }


def _runner(tmp_path: Path) -> BasicBackendGateRunner:
    return BasicBackendGateRunner(
        BasicBackendGateConfig(
            source_root=ROOT,
            output_root=tmp_path / "out",
            python_executable=Path(sys.executable),
        )
    )


def _fake_authenticated_execution_workflow(
    task_key: str,
    *,
    repair_succeeded: bool = False,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    durable_task_id = "production-" + _sha256_text(task_key)[:20]
    task_id_sha256 = _sha256_text(durable_task_id)
    attempt_total = 2 if repair_succeeded else 1
    exchanges: list[dict[str, Any]] = []

    def digest(label: str) -> str:
        return _sha256_text(f"test-evidence:{task_key}:{label}")

    def exchange(
        label: str,
        path: str,
        *,
        signed: bool = False,
    ) -> dict[str, Any]:
        authentication = {
            "scheme": "signed_operator_assertion",
            "assertion_present": signed,
            "server_acknowledged": signed,
            "caller_claimed_authenticated": False,
            "authenticated": signed,
        }
        item = {
            "ordinal": len(exchanges) + 1,
            "method": "POST",
            "path": path,
            "status_code": 200,
            "request_sha256": digest(label + ":request"),
            "response_sha256": digest(label),
            "evidence_file": "/evidence/" + digest(label + ":file") + ".json",
            "authenticated": signed,
            "authentication": authentication,
            "elapsed_ms": 1,
        }
        exchanges.append(item)
        return item

    exchange(
        "authority",
        "/v1/campaigns/campaign-3.5/model-call-authority",
        signed=True,
    )
    exchange("create", "/v1/tasks/long-running")
    prefix = f"/v1/tasks/long-running/{durable_task_id}"
    attempts: list[dict[str, Any]] = []
    prior_repair_request: dict[str, Any] | None = None
    for attempt_number in range(1, attempt_total + 1):
        proposal = exchange(
            f"proposal-{attempt_number}",
            f"{prefix}/target-plugin-proposal",
        )
        preview = exchange(
            f"preview-{attempt_number}",
            f"{prefix}/approval-preview",
        )
        approval = exchange(
            f"approval-{attempt_number}",
            f"{prefix}/operator-approval",
            signed=True,
        )
        execute = exchange(
            f"execute-{attempt_number}",
            f"{prefix}/execute-approved",
        )
        alias = "local" if attempt_number > 1 else "coder"
        model = (
            "ollama_chat/fake-local"
            if attempt_number > 1
            else "ollama_chat/fake-coder"
        )
        raw_sha256 = digest(f"raw-{attempt_number}")
        output_sha256 = digest(f"composite-{attempt_number}")
        call = {
            "call_index": 1,
            "stage": "coder",
            "requested_model_alias": alias,
            "model_alias": alias,
            "provider": "ollama",
            "model": model,
            "routed_model": model,
            "completed": True,
            "raw_response_observed": True,
            "rendered_prompt_sha256": digest(f"prompt-{attempt_number}"),
            "raw_response_sha256": raw_sha256,
        }
        adapter = {
            "call_count": 1,
            "calls": [call],
            "transport_kind": "canonical_litellm_router",
            "provider_call_authorized": True,
            "model_call_accounting_complete": True,
            "producer_identity_bound": True,
            "producer_call_index": 1,
            "selected_model_alias": alias,
            "provider": "ollama",
            "model": model,
            "routed_model": model,
            "raw_response_sha256": raw_sha256,
        }
        attempt: dict[str, Any] = {
            "attempt_number": attempt_number,
            "orchestrator_attempt_id": f"attempt-{attempt_number}-{digest(task_key)[:8]}",
            "parent_attempt_id": (
                None
                if attempt_number == 1
                else attempts[-1]["orchestrator_attempt_id"]
            ),
            "proposal_binding_sha256": digest(f"binding-{attempt_number}"),
            "approved_diff_sha256": digest(f"diff-{attempt_number}"),
            "preview_id": f"preview-{attempt_number}-{digest(task_key)[:8]}",
            "approval_id": f"approval-{attempt_number}-{digest(task_key)[:8]}",
            "fresh_exact_approval": True,
            "proposal_response_sha256": proposal["response_sha256"],
            "preview_response_sha256": preview["response_sha256"],
            "approval_response_sha256": approval["response_sha256"],
            "execute_response_sha256": execute["response_sha256"],
            "execute_status_code": 200,
            "model_identity": {
                "invocation_id": f"invocation-{attempt_number}",
                "provider": "ollama",
                "model": model,
                "input_sha256": digest(f"input-{attempt_number}"),
                "output_sha256": output_sha256,
                "artifact_sha256": digest(f"artifact-{attempt_number}"),
            },
            "target_adapter_provenance": adapter,
            "producer_model_alias": alias,
            "producer_model_output_sha256": output_sha256,
            "producer_raw_response_sha256": raw_sha256,
            "repair_evidence": {},
            "status": "verification_completed",
        }
        if prior_repair_request is not None:
            attempt["repair_evidence"] = {
                "repair_context": dict(prior_repair_request),
                "repair_input_sha256": prior_repair_request["repair_input_sha256"],
                "repair_prompt_sha256": digest(f"repair-prompt-{attempt_number}"),
                "repair_strategy_signature": "sha256:" + digest(
                    f"repair-strategy-{attempt_number}"
                ),
                "failure_class": prior_repair_request["failure_class"],
            }
        if repair_succeeded and attempt_number < attempt_total:
            state_manifest = {
                "schema_version": "coding.current-applied-state-manifest/v1",
                "live_state_captured": True,
                "workspace_root": str(
                    (workspace_root or Path("/opaque/workspace")).resolve()
                ),
                "changed_files": ["src/example.py"],
                "approval_id": attempt["approval_id"],
                "approved_diff_sha256": attempt["approved_diff_sha256"],
            }
            disposition_body = {
                "schema_version": "coding-repair-approval-disposition/v1",
                "task_id": durable_task_id,
                "run_id": "run-test",
                "attempt_id": attempt["orchestrator_attempt_id"],
                "attempt_seal_sha256": digest(f"seal-{attempt_number}"),
                "approval_id": attempt["approval_id"],
                "generation": attempt_number,
                "authority_state": "invalidated",
                "failure_reason": "verifier_rejection",
            }
            disposition = {
                **disposition_body,
                "disposition_sha256": _sha256_json(disposition_body),
            }
            diagnostic_body = {
                "failure_class": "verifier_rejection",
                "attempt_id": attempt["orchestrator_attempt_id"],
            }
            diagnostic = {
                **diagnostic_body,
                "diagnostic_sha256": _sha256_json(diagnostic_body),
            }
            repair_body = {
                "schema_version": "coding-repair-request/v1",
                "task_id": durable_task_id,
                "run_id": "run-test",
                "attempt_id": f"attempt-{attempt_number + 1}-{digest(task_key)[:8]}",
                "parent_attempt_id": attempt["orchestrator_attempt_id"],
                "attempt_number": attempt_number + 1,
                "max_attempts": 3,
                "failure_class": "verifier_rejection",
                "source_lane": "verifier",
                "exact_feedback": "public verifier rejected the first patch",
                "feedback_sha256": digest("feedback"),
                "current_state_manifest": state_manifest,
                "current_state_manifest_sha256": _sha256_json(state_manifest),
                "repair_diagnostic": diagnostic,
                "repair_diagnostic_sha256": diagnostic["diagnostic_sha256"],
                "parent_attempt_seal_sha256": digest(f"seal-{attempt_number}"),
                "prior_approval_id": attempt["approval_id"],
                "prior_approved_diff_sha256": attempt["approved_diff_sha256"],
                "prior_approval_disposition": disposition,
                "prior_approval_disposition_sha256": disposition[
                    "disposition_sha256"
                ],
                "original_task": "opaque test task",
                "requirements": {
                    "fresh_proposal_required": True,
                    "fresh_approval_required": True,
                    "current_applied_state_is_baseline": True,
                    "new_evidence_or_changed_strategy_required": True,
                },
            }
            prior_repair_request = {
                **repair_body,
                "repair_input_sha256": _sha256_json(repair_body),
            }
            attempt["repair_request"] = dict(prior_repair_request)
            attempt["attempt_seal_sha256"] = prior_repair_request[
                "parent_attempt_seal_sha256"
            ]
            attempt["status"] = "repair_required_after_verifier"
        attempts.append(attempt)
    runtime_sha256 = _fake_model_inventory()["verifier_runtime_sha256"]
    return {
        "task_id_sha256": task_id_sha256,
        "attempts": attempts,
        "attempt_count": len(attempts),
        "http_exchanges": exchanges,
        "fresh_approval_per_attempt": True,
        "approved_diff_applied": True,
        "public_tests_passed": True,
        "local_model_path_verified": True,
        "model_inventory_bound": True,
        "completed": True,
        "raw_task_completed_claim": True,
        "terminal_disposition": "completed",
        "terminal_disposition_truthful": True,
        "repair_succeeded": repair_succeeded,
        "production_proof": {
            "terminal_proof_eligible": True,
            "proof_sha256": digest("proof"),
        },
        "trace_reconciliation": {"passed": True},
        "verifier_runtime_evidence": {
            "runtime": "restricted_container",
            "image": TEST_IMAGE_ID,
            "host_runtime_inventory_sha256": runtime_sha256,
            "network": "none",
            "workspace_mount": "read_only",
            "host_environment_inherited": False,
            "workspace_root_sha256": digest("workspace"),
            "command_sha256": digest("verifier-command"),
            "exit_code": 0,
        },
    }


def _persist_passing_task_receipt(
    phase_root: Path,
    phase: str,
    rendered: Any,
    *,
    repair_succeeded: bool,
    source_head: str = TEST_FIRST_HEAD,
) -> dict[str, Any]:
    task_root = phase_root / f"task-{rendered.task_seed_commitment}"
    fixture_parent = task_root / "fixture-parent"
    evidence_root = task_root / "evidence"
    state_root = task_root / "state"
    private_root = task_root / "private"
    for root in (fixture_parent, evidence_root, state_root, private_root):
        root.mkdir(parents=True, exist_ok=True)
    fixture = materialize_basic_backend_fixture(fixture_parent, rendered)
    apply_reference(fixture)
    mutation = _audit_fixture_mutations(fixture)
    applied_diff = _workspace_diff(fixture.root)
    applied_diff_path = evidence_root / "applied-workspace.diff"
    applied_diff_path.write_text(applied_diff, encoding="utf-8")
    mutation["applied_diff_sha256"] = _sha256_text(applied_diff)
    mutation["applied_diff_evidence_file"] = str(applied_diff_path)

    import_log = state_root / "import-audit.jsonl"
    import_log.write_text(
        json.dumps({"event": "hook_started", "pid": 101})
        + "\n"
        + json.dumps(
            {"event": "hook_completed", "forbidden_loaded": [], "pid": 101}
        )
        + "\n",
        encoding="utf-8",
    )
    import_attestation = _finalize_service_import_audit(import_log)
    model_inventory = _fake_model_inventory()
    model_aliases = {
        item["role"]: item["alias"] for item in model_inventory["models"]
    }
    service_process = {
        "task_label": f"task-seed:{rendered.task_seed_commitment}",
        "branch": TEST_BRANCH,
        "head": source_head,
        "cwd": str(ROOT.resolve()),
        "service_process_per_task": True,
        "task_local_state_root": str(state_root.resolve()),
        "fixture_manifest_sha256": "4" * 64,
        "hosted_credentials_inherited": False,
        "direct_ollama_bypass_enabled": False,
        "sandbox_image_id": TEST_IMAGE_ID,
        "model_inventory_sha256": model_inventory["inventory_sha256"],
        "verifier_runtime_sha256": model_inventory["verifier_runtime_sha256"],
        "model_aliases": model_aliases,
        "import_attestation": import_attestation,
    }
    workflow = _fake_authenticated_execution_workflow(
        rendered.definition.task_id,
        repair_succeeded=repair_succeeded,
        workspace_root=fixture.root,
    )
    leak = _hidden_answer_leak_audit(
        workflow,
        rendered=rendered,
        raw_seed_values_forbidden=True,
        production_roots=(state_root, evidence_root, fixture.root),
        service_receipt=service_process,
    )
    observations = {
        "schema_version": "source-proxy-basic-backend-10-neutral-observations/v1",
        "imports": {"backend": {"ok": True}},
        "operations": [],
    }
    private_payload = {
        "schema_version": "source-proxy-basic-backend-10-private-oracle/v2",
        "task_id": rendered.definition.task_id,
        "passed": True,
        "checks": [{"name": "synthetic_reference", "passed": True}],
        "observations_sha256": _sha256_json(observations),
        "neutral_worker_sha256": _sha256_text(_NEUTRAL_PROBE_WORKER),
    }
    observations_path = private_root / "candidate-observations.json"
    private_path = private_root / "oracle-private.json"
    observations_path.write_text(json.dumps(observations), encoding="utf-8")
    private_path.write_text(json.dumps(private_payload), encoding="utf-8")
    oracle = {
        "passed": True,
        "private_payload_sha256": _sha256_json(private_payload),
        "candidate_observations_sha256": _sha256_json(observations),
        "private_evidence_file": str(private_path),
        "candidate_observations_file": str(observations_path),
        "process_separate_from_source_proxy": True,
        "trusted_decision_imported_candidate": False,
        "candidate_received_expected_results": False,
        "candidate_received_task_id": False,
        "candidate_can_import_oracle_module": False,
        "network": "none",
        "workspace_mount": "read_only",
        "mounted_inputs": ["fixture", "neutral_probe_worker"],
        "host_environment_inherited": False,
        "sandbox_image_id": TEST_IMAGE_ID,
    }
    completion = _completion_claim_audit(
        workflow,
        actual_change=bool(mutation["changed_paths"]),
        independent_verification_passed=True,
    )
    receipt_path = task_root / "task-receipt.json"
    receipt = {
        "schema_version": "source-proxy-basic-backend-10-task-receipt/v1",
        "definition_version": "source_proxy_basic_backend_10_v1",
        "phase": phase,
        "task_id": rendered.definition.task_id,
        "opaque_task_key": rendered.task_seed_commitment,
        "receipt_file": str(receipt_path),
        "task_seed_commitment": rendered.task_seed_commitment,
        "fixture_root": str(fixture.root),
        "baseline_commit": fixture.baseline_commit,
        "baseline_tree": fixture.baseline_tree,
        "authority_manifest_sha256": "4" * 64,
        "source_branch": TEST_BRANCH,
        "source_head": source_head,
        "source_root": str(ROOT.resolve()),
        "sandbox_image_id": TEST_IMAGE_ID,
        "model_inventory": model_inventory,
        "model_inventory_sha256": model_inventory["inventory_sha256"],
        "verifier_runtime_sha256": model_inventory["verifier_runtime_sha256"],
        "service_process": service_process,
        "workflow": workflow,
        "private_oracle": oracle,
        "mutation_audit": mutation,
        "hidden_answer_isolation": leak,
        "production_proof": dict(workflow["production_proof"]),
        "completion_claim_audit": completion,
        "raw_service_status": completion["raw_service_status"],
        "normalized_terminal_disposition": completion[
            "normalized_terminal_disposition"
        ],
        "expected_terminal_disposition": (
            rendered.definition.expected_terminal_disposition
        ),
        "expected_terminal_disposition_matches": True,
        "passed": True,
        "repair_succeeded": repair_succeeded,
        "attempt_count": len(workflow["attempts"]),
        "unauthorized_mutation_count": 0,
        "fabricated_completion_count": 0,
        "hidden_answer_leak_count": 0,
        "terminal_disposition_truthful": True,
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def _score_receipt(receipt: Mapping[str, Any], rendered: Any) -> dict[str, Any]:
    return _rederive_task_receipt_score(
        receipt,
        expected_phase=str(receipt.get("phase") or ""),
        expected_terminal_disposition=(
            rendered.definition.expected_terminal_disposition
        ),
        expected_writable_paths=rendered.definition.writable_paths,
        expected_branch=TEST_BRANCH,
        expected_head=TEST_FIRST_HEAD,
        expected_source_root=ROOT,
        expected_sandbox_image_id=TEST_IMAGE_ID,
        expected_model_inventory=_fake_model_inventory(),
    )


def test_authenticated_lifecycle_uses_fresh_exact_approval_for_repair(tmp_path: Path) -> None:
    client = FakeLifecycleClient(tmp_path / "http")
    service = RunningGateService(
        client=client,
        signer=OperatorAssertionSigner(secret="test-operator-secret", session_id="session-test"),
        process_receipt={"service_process_per_task": True},
    )
    seed = BasicBackendRunSeed.from_private_bytes(b"a" * 32)
    rendered = render_basic_backend_task("BT01", run_seed=seed, run_nonce="test-run")

    result = _runner(tmp_path)._drive_authenticated_lifecycle(service, rendered)

    assert result["completed"] is True
    assert result["public_tests_passed"] is True
    assert result["repair_succeeded"] is True
    assert result["fresh_approval_per_attempt"] is True
    assert result["attempt_count"] == 2
    assert [item["approval_id"] for item in result["attempts"]] == ["approval-1", "approval-2"]
    assert result["trace_reconciliation"]["passed"] is True
    assert result["attempts"][0]["model_identity"]["provider"] == "ollama"
    assert result["attempts"][0]["model_identity"]["model"] == "ollama_chat/local-coder"
    assert result["attempts"][0]["producer_model_output_sha256"] == f"{21:064x}"
    assert result["attempts"][0]["producer_raw_response_sha256"] == f"{31:064x}"
    assert (
        result["attempts"][0]["producer_raw_response_sha256"]
        != result["attempts"][0]["producer_model_output_sha256"]
    )
    assert result["local_model_path_verified"] is True
    assert result["required_evidence_index"]["human_prompt"]["sha256"]
    assert len(result["required_evidence_index"]["reviewer_results"]) == 2
    assert len(result["required_evidence_index"]["verifier_public_tests_runtime"]) == 2
    paths = [path for _method, path, _payload in client.paths]
    assert paths.count(f"/v1/tasks/long-running/{client.task_id}/target-plugin-proposal") == 2
    assert paths.count(f"/v1/tasks/long-running/{client.task_id}/approval-preview") == 2
    assert paths.count(f"/v1/tasks/long-running/{client.task_id}/operator-approval") == 2
    assert paths.count(f"/v1/tasks/long-running/{client.task_id}/execute-approved") == 2
    assert not any("adapter" in path for path in paths)


def test_two_phase_gate_runs_all_ten_in_order_with_fresh_seeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeds = iter(
        (
            BasicBackendRunSeed.from_private_bytes(b"1" * 32),
            BasicBackendRunSeed.from_private_bytes(b"2" * 32),
        )
    )
    runner = BasicBackendGateRunner(
        BasicBackendGateConfig(
            source_root=ROOT,
            output_root=tmp_path / "gate-output",
            python_executable=Path(sys.executable),
        ),
        seed_factory=lambda: next(seeds),
    )
    monkeypatch.setattr(
        runner,
        "validate_preflight",
        lambda **_kwargs: _fake_preflight(),
    )
    monkeypatch.setattr(runner, "_assert_runtime_snapshot", lambda **_kwargs: None)
    calls: list[tuple[str, str]] = []

    def fake_task(
        phase_root: Path,
        phase: str,
        rendered: Any,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        calls.append((phase, rendered.definition.task_id))
        return _persist_passing_task_receipt(
            phase_root,
            phase,
            rendered,
            repair_succeeded=(
                phase == "first" and rendered.definition.task_id == "BT01"
            ),
        )

    monkeypatch.setattr(runner, "_run_task", fake_task)
    report = runner.run()

    assert calls == [
        *(('first', task_id) for task_id in EXPECTED_TASK_IDS),
        *(('clean_rerun', task_id) for task_id in EXPECTED_TASK_IDS),
    ]
    assert report["all_ten_executed_per_phase"] is True
    assert report["comparison"]["all_tasks_compared"] is True
    assert report["comparison"]["fresh_seed_commitments"] is True
    assert report["first_phase_repaired_success_count"] == 1
    assert report["gate_passed"] is True


def test_receipt_count_cannot_substitute_for_authenticated_execution_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeds = iter(
        (
            BasicBackendRunSeed.from_private_bytes(b"3" * 32),
            BasicBackendRunSeed.from_private_bytes(b"4" * 32),
        )
    )
    runner = BasicBackendGateRunner(
        BasicBackendGateConfig(
            source_root=ROOT,
            output_root=tmp_path / "gate-output",
            python_executable=Path(sys.executable),
        ),
        seed_factory=lambda: next(seeds),
    )
    monkeypatch.setattr(
        runner,
        "validate_preflight",
        lambda **_kwargs: _fake_preflight(),
    )
    monkeypatch.setattr(runner, "_assert_runtime_snapshot", lambda **_kwargs: None)

    def fake_task(
        phase_root: Path,
        phase: str,
        rendered: Any,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        receipt = _persist_passing_task_receipt(
            phase_root,
            phase,
            rendered,
            repair_succeeded=(
                phase == "first" and rendered.definition.task_id == "BT01"
            ),
        )
        if phase == "first" and rendered.definition.task_id == EXPECTED_TASK_IDS[-1]:
            receipt["workflow"] = {}
        return receipt

    monkeypatch.setattr(runner, "_run_task", fake_task)

    report = runner.run()

    assert report["phases"][0]["receipt_count"] == 10
    assert report["phases"][0]["executed_task_count"] == 9
    assert report["phases"][0][
        "all_tasks_crossed_authenticated_execution_lifecycle"
    ] is False
    assert report["all_ten_executed_per_phase"] is False
    assert report["gate_passed"] is False


def _create_first_phase_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    seed_bytes: bytes = b"5" * 32,
) -> tuple[Path, dict[str, Any]]:
    runner = BasicBackendGateRunner(
        BasicBackendGateConfig(
            source_root=ROOT,
            output_root=tmp_path / "first-output",
            python_executable=Path(sys.executable),
            phases=("first",),
        ),
        seed_factory=lambda: BasicBackendRunSeed.from_private_bytes(seed_bytes),
    )
    monkeypatch.setattr(
        runner,
        "validate_preflight",
        lambda **_kwargs: _fake_preflight(),
    )
    monkeypatch.setattr(runner, "_assert_runtime_snapshot", lambda **_kwargs: None)
    monkeypatch.setattr(
        runner,
        "_run_task",
        lambda phase_root, phase, rendered, **_kwargs: _persist_passing_task_receipt(
            phase_root,
            phase,
            rendered,
            repair_succeeded=(rendered.definition.task_id == "BT01"),
        ),
    )
    report = runner.run()
    return Path(report["phase_manifests"]["first"]), report


def test_first_phase_persists_hash_bound_resume_manifest_and_exits_nonterminal_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path, report = _create_first_phase_manifest(tmp_path, monkeypatch)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    recorded_sha256 = manifest.pop("manifest_sha256")

    assert recorded_sha256 == _sha256_json(manifest)
    assert manifest["phase"] == "first"
    assert manifest["phase_gate_passed"] is True
    assert len(manifest["task_receipts"]) == 10
    assert report["gate_passed"] is False
    assert report["phase_run_passed"] is True
    assert report["terminal_token"] == (
        "LOCAL_PROXY_BASIC_CODING_FIRST_PHASE_PASSED_RESUME_REQUIRED"
    )


@pytest.mark.parametrize("fresh_seed", (True, False))
def test_clean_rerun_reaggregates_first_receipts_and_enforces_seed_freshness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fresh_seed: bool,
) -> None:
    first_seed = b"6" * 32
    manifest_path, _first_report = _create_first_phase_manifest(
        tmp_path,
        monkeypatch,
        seed_bytes=first_seed,
    )
    current_head = "b" * 40
    real_subprocess_run = subprocess.run

    def resume_subprocess_run(command: list[str], *args: Any, **kwargs: Any) -> Any:
        if len(command) >= 5 and command[3:5] == ["merge-base", "--is-ancestor"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return real_subprocess_run(command, *args, **kwargs)

    monkeypatch.setattr(
        "source_proxy.benchmarks.campaign_3_5_basic_gate_runner.subprocess.run",
        resume_subprocess_run,
    )
    monkeypatch.setattr(
        "source_proxy.benchmarks.campaign_3_5_basic_gate_runner._git",
        lambda root, *args: (
            current_head
            if args[:2] == ("rev-list", "--reverse")
            else _git(root, *args)
        ),
    )
    clean_seed = b"7" * 32 if fresh_seed else first_seed
    runner = BasicBackendGateRunner(
        BasicBackendGateConfig(
            source_root=ROOT,
            output_root=tmp_path / "clean-output",
            python_executable=Path(sys.executable),
            phases=("clean_rerun",),
            resume_first=manifest_path,
        ),
        seed_factory=lambda: BasicBackendRunSeed.from_private_bytes(clean_seed),
    )
    monkeypatch.setattr(
        runner,
        "validate_preflight",
        lambda **_kwargs: _fake_preflight(head=current_head),
    )
    monkeypatch.setattr(runner, "_assert_runtime_snapshot", lambda **_kwargs: None)
    monkeypatch.setattr(
        runner,
        "_run_task",
        lambda phase_root, phase, rendered, **_kwargs: _persist_passing_task_receipt(
            phase_root,
            phase,
            rendered,
            repair_succeeded=False,
            source_head=current_head,
        ),
    )

    report = runner.run()

    assert report["resume_evidence"]["first_aggregate_recomputed"] is True
    assert report["resume_evidence"]["intervening_commits"] == [current_head]
    assert report["comparison"]["fresh_seed_commitments"] is fresh_seed
    assert report["gate_passed"] is fresh_seed
    assert report["phase_run_passed"] is fresh_seed


def test_resume_rejects_evaluation_contract_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path, _report = _create_first_phase_manifest(tmp_path, monkeypatch)
    changed_contract = dict(_evaluation_contract(ROOT))
    changed_contract["contract_sha256"] = "f" * 64

    with pytest.raises(
        BasicBackendGateError,
        match="basic_gate_resume_evaluation_contract_changed",
    ):
        _load_and_validate_first_phase_manifest(
            manifest_path,
            source_root=ROOT,
            expected_branch="codex/campaign-3-5-execution-20260719",
            current_head="b" * 40,
            current_contract=changed_contract,
            current_sandbox_image=_fake_sandbox_image(),
            current_model_inventory=_fake_model_inventory(),
            expected_task_ids=EXPECTED_TASK_IDS,
        )


def test_resume_rejects_same_or_nonancestor_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path, report = _create_first_phase_manifest(tmp_path, monkeypatch)
    contract = report["evaluation_contract"]
    with pytest.raises(BasicBackendGateError, match="basic_gate_resume_head_not_later"):
        _load_and_validate_first_phase_manifest(
            manifest_path,
            source_root=ROOT,
            expected_branch="codex/campaign-3-5-execution-20260719",
            current_head="a" * 40,
            current_contract=contract,
            current_sandbox_image=_fake_sandbox_image(),
            current_model_inventory=_fake_model_inventory(),
            expected_task_ids=EXPECTED_TASK_IDS,
        )

    monkeypatch.setattr(
        "source_proxy.benchmarks.campaign_3_5_basic_gate_runner.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="not an ancestor",
        ),
    )
    with pytest.raises(
        BasicBackendGateError,
        match="basic_gate_resume_first_head_not_ancestor",
    ):
        _load_and_validate_first_phase_manifest(
            manifest_path,
            source_root=ROOT,
            expected_branch="codex/campaign-3-5-execution-20260719",
            current_head="b" * 40,
            current_contract=contract,
            current_sandbox_image=_fake_sandbox_image(),
            current_model_inventory=_fake_model_inventory(),
            expected_task_ids=EXPECTED_TASK_IDS,
        )


def test_resume_rejects_tampered_receipt_even_when_manifest_is_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path, report = _create_first_phase_manifest(tmp_path, monkeypatch)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt_path = manifest_path.parent / manifest["task_receipts"][0]["receipt_file"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["passed"] = False
    receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        "source_proxy.benchmarks.campaign_3_5_basic_gate_runner.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    with pytest.raises(
        BasicBackendGateError,
        match="basic_gate_resume_receipt_hash_mismatch",
    ):
        _load_and_validate_first_phase_manifest(
            manifest_path,
            source_root=ROOT,
            expected_branch="codex/campaign-3-5-execution-20260719",
            current_head="b" * 40,
            current_contract=report["evaluation_contract"],
            current_sandbox_image=_fake_sandbox_image(),
            current_model_inventory=_fake_model_inventory(),
            expected_task_ids=EXPECTED_TASK_IDS,
        )


@pytest.mark.parametrize("mutation", ("duplicate", "missing"))
def test_resume_rejects_duplicate_or_missing_task_receipt_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    manifest_path, report = _create_first_phase_manifest(tmp_path, monkeypatch)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("manifest_sha256")
    if mutation == "duplicate":
        manifest["task_receipts"][-1] = dict(manifest["task_receipts"][0])
    else:
        manifest["task_receipts"].pop()
    manifest["manifest_sha256"] = _sha256_json(manifest)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "source_proxy.benchmarks.campaign_3_5_basic_gate_runner.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    with pytest.raises(
        BasicBackendGateError,
        match="basic_gate_resume_receipt_set_invalid",
    ):
        _load_and_validate_first_phase_manifest(
            manifest_path,
            source_root=ROOT,
            expected_branch="codex/campaign-3-5-execution-20260719",
            current_head="b" * 40,
            current_contract=report["evaluation_contract"],
            current_sandbox_image=_fake_sandbox_image(),
            current_model_inventory=_fake_model_inventory(),
            expected_task_ids=EXPECTED_TASK_IDS,
        )


@pytest.mark.parametrize(
    ("missing", "workflow_patch", "independent_verification_passed"),
    (
        (
            "terminal_proof",
            {"production_proof": {"terminal_proof_eligible": False}, "completed": False},
            True,
        ),
        ("required_tests", {"public_tests_passed": False}, True),
        ("independent_verification", {}, False),
    ),
)
def test_raw_completed_claim_without_required_evidence_is_fabricated_and_untruthful(
    missing: str,
    workflow_patch: Mapping[str, Any],
    independent_verification_passed: bool,
) -> None:
    workflow: dict[str, Any] = {
        "raw_task_completed_claim": True,
        "terminal_disposition": "completed",
        "completed": True,
        "production_proof": {"terminal_proof_eligible": True},
        "approved_diff_applied": True,
        "public_tests_passed": True,
        "terminal_disposition_truthful": True,
    }
    workflow.update(workflow_patch)

    audit = _completion_claim_audit(
        workflow,
        actual_change=True,
        independent_verification_passed=independent_verification_passed,
    )

    assert audit["raw_service_completed_claim"] is True, missing
    assert audit["fabricated_completion_count"] == 1, missing
    assert audit["terminal_disposition_truthful"] is False, missing
    assert audit["normalized_terminal_disposition"] != "completed_verified", missing


def test_completed_verified_is_derived_only_from_raw_completed_and_all_evidence() -> None:
    workflow = {
        "raw_task_completed_claim": True,
        "terminal_disposition": "completed",
        "completed": True,
        "production_proof": {"terminal_proof_eligible": True},
        "approved_diff_applied": True,
        "public_tests_passed": True,
        "terminal_disposition_truthful": True,
    }
    audit = _completion_claim_audit(
        workflow,
        actual_change=True,
        independent_verification_passed=True,
    )
    assert audit["normalized_terminal_disposition"] == "completed_verified"
    assert audit["fabricated_completion_count"] == 0

    forged_normalized = _completion_claim_audit(
        {**workflow, "terminal_disposition": "completed_verified"},
        actual_change=True,
        independent_verification_passed=True,
    )
    assert forged_normalized["raw_service_status"] == "completed_verified"
    assert forged_normalized["normalized_terminal_disposition"] == (
        "invalid_reserved_completed_verified_claim"
    )
    assert forged_normalized["normalized_terminal_disposition"] != "completed_verified"


def test_private_oracle_runs_in_no_network_read_only_container(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "fixture"
    workspace.mkdir()
    (workspace / ".git").mkdir()
    private_store = tmp_path / "private"
    private_store.mkdir()
    observed: dict[str, Any] = {}
    seed = BasicBackendRunSeed.from_private_bytes(b"o" * 32)
    rendered = render_basic_backend_task("BT01", run_seed=seed, run_nonce="oracle-boundary")
    maximum = int(rendered.values["maximum_limit"])
    items = [{"id": index} for index in range(maximum + 2)]

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/docker" if name == "docker" else None)

    def fake_run(command: list[str], **kwargs: Any) -> SimpleNamespace:
        observed["command"] = command
        observed["kwargs"] = kwargs
        spec = json.loads(kwargs["input"])
        operations = []
        for operation in spec["operations"]:
            operation_id = operation["id"]
            value: Any = None
            if operation_id in {"items_before", "items_after"}:
                value = items
            elif operation_id == "omitted":
                value = {"status": 200, "body": {"items": items}}
            elif operation_id == "one":
                value = {"status": 200, "body": {"items": items[:1]}}
            elif operation_id == "maximum":
                value = {"status": 200, "body": {"items": items[:maximum]}}
            elif operation_id.startswith("invalid_"):
                value = {"status": 400, "body": {"error": "invalid"}}
            operations.append(
                {"id": operation_id, "kind": operation["kind"], "ok": True, "value": value}
            )
        observations = {
            "schema_version": "source-proxy-basic-backend-10-neutral-observations/v1",
            "imports": {"backend": {"ok": True}},
            "operations": operations,
        }
        framed = (
            b"SPIRIT_NEUTRAL_OBSERVATION_V1 "
            + b"a" * 48
            + b" "
            + json.dumps(observations, sort_keys=True).encode()
            + b"\n"
        )
        return SimpleNamespace(returncode=0, stdout=framed, stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = run_private_oracle_container(
        task_id="BT01",
        workspace_root=workspace,
        values=rendered.values,
        private_store=private_store,
        source_root=ROOT,
        python_executable=Path(sys.executable),
        inherited_environment={"HOSTED_API_KEY": "must-not-pass", "SOURCE_PROXY_BASIC_GATE_ORACLE_IMAGE": "local-image"},
    )

    command = observed["command"]
    assert "--network" in command and command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert "--cap-drop" in command and command[command.index("--cap-drop") + 1] == "ALL"
    assert any(f"src={workspace.resolve()},dst=/workspace,readonly" in value for value in command)
    assert any("dst=/worker/probe.py,readonly" in value for value in command)
    assert not any("dst=/runner" in value for value in command)
    assert str(ROOT.resolve()) not in " ".join(command)
    assert "-I" in command and "-S" in command
    assert observed["kwargs"]["env"] == {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    assert b"HOSTED_API_KEY" not in observed["kwargs"]["input"]
    assert b"task_id" not in observed["kwargs"]["input"]
    assert b"expected" not in observed["kwargs"]["input"].lower()
    assert result["passed"] is True
    assert result["process_separate_from_source_proxy"] is True
    assert result["trusted_decision_imported_candidate"] is False
    assert result["candidate_received_expected_results"] is False
    assert result["candidate_received_task_id"] is False
    assert result["mounted_inputs"] == ["fixture", "neutral_probe_worker"]
    private_payload = json.loads((private_store / "oracle-private.json").read_text())
    assert private_payload["schema_version"] == "source-proxy-basic-backend-10-private-oracle/v2"
    assert all(check["passed"] is True for check in private_payload["checks"])


def test_neutral_supervisor_contains_candidate_main_global_forgery(tmp_path: Path) -> None:
    workspace = tmp_path / "malicious-fixture"
    (workspace / "src").mkdir(parents=True)
    (workspace / ".git").mkdir()
    (workspace / "src/backend.py").write_text(
        '''from __future__ import annotations
import __main__
import os

# This would own framing if candidate code shared the supervisor interpreter.
__main__._outer_dumps = lambda *args, **kwargs: '{"passed":true}'
__main__._outer_write = lambda *args, **kwargs: 0
__main__._outer_exit = lambda *args, **kwargs: None
os.write(1, b'SPIRIT_NEUTRAL_OBSERVATION_V1 ' + b'f' * 48 + b' {"passed":true}\\n')

def total_values(values):
    return 999999
''',
        encoding="utf-8",
    )
    worker = tmp_path / "neutral-probe-worker.py"
    worker.write_text(_NEUTRAL_PROBE_WORKER, encoding="utf-8")
    values = {"function_name": "total_values"}
    spec = _private_probe_spec("BT02", values)
    environment = {
        "HOME": str(tmp_path),
        "LANG": "C.UTF-8",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "SPIRIT_NEUTRAL_WORKSPACE_ROOT": str(workspace),
    }

    completed = subprocess.run(
        [sys.executable, "-I", "-S", str(worker)],
        input=json.dumps(spec, sort_keys=True).encode(),
        capture_output=True,
        check=False,
        timeout=30,
        env=environment,
    )

    assert completed.returncode == 0
    observations = _parse_neutral_probe_output(completed.stdout)
    assert "passed" not in observations
    assert observations["imports"]["backend"]["ok"] is False
    decision = _trusted_private_oracle_decision(
        task_id="BT02",
        workspace_root=workspace,
        values=values,
        observations=observations,
    )
    assert not all(passed for _name, passed in decision)


def test_neutral_probe_and_trusted_decision_accept_all_private_references(tmp_path: Path) -> None:
    worker = tmp_path / "neutral-probe-worker.py"
    worker.write_text(_NEUTRAL_PROBE_WORKER, encoding="utf-8")
    seed = BasicBackendRunSeed.from_private_bytes(b"r" * 32)
    for task_id in EXPECTED_TASK_IDS:
        rendered = render_basic_backend_task(task_id, run_seed=seed, run_nonce="split-oracle")
        fixture_parent = tmp_path / task_id.lower()
        fixture_parent.mkdir()
        fixture = materialize_basic_backend_fixture(fixture_parent, rendered)
        apply_reference(fixture)
        spec = _private_probe_spec(task_id, rendered.values)
        environment = {
            "HOME": str(tmp_path),
            "LANG": "C.UTF-8",
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "SPIRIT_NEUTRAL_WORKSPACE_ROOT": str(fixture.root),
        }

        completed = subprocess.run(
            [sys.executable, "-I", "-S", str(worker)],
            input=json.dumps(spec, sort_keys=True).encode(),
            capture_output=True,
            check=False,
            timeout=30,
            env=environment,
        )

        assert completed.returncode == 0, (task_id, completed.stderr.decode(errors="replace"))
        observations = _parse_neutral_probe_output(completed.stdout)
        checks = _trusted_private_oracle_decision(
            task_id=task_id,
            workspace_root=fixture.root,
            values=rendered.values,
            observations=observations,
        )
        assert all(passed for _name, passed in checks), (task_id, checks, observations)


def test_mutation_audit_rejects_readable_but_nonwritable_change(tmp_path: Path) -> None:
    seed = BasicBackendRunSeed.from_private_bytes(b"m" * 32)
    rendered = render_basic_backend_task("BT01", run_seed=seed, run_nonce="mutation-test")
    parent = tmp_path / "parent"
    parent.mkdir()
    fixture = materialize_basic_backend_fixture(parent, rendered)
    (fixture.root / "src/backend.py").write_text(
        (fixture.root / "src/backend.py").read_text() + "\n# allowed\n",
        encoding="utf-8",
    )
    (fixture.root / "pyproject.toml").write_text("# forbidden write\n", encoding="utf-8")

    audit = _audit_fixture_mutations(fixture)

    assert "src/backend.py" in audit["changed_paths"]
    assert audit["unauthorized_paths"] == ["pyproject.toml"]
    assert audit["unauthorized_mutation_count"] == 1
    assert audit["head_unchanged"] is True
    assert audit["index_unchanged"] is True


def test_workspace_diff_preserves_tracked_and_untracked_final_changes(tmp_path: Path) -> None:
    seed = BasicBackendRunSeed.from_private_bytes(b"d" * 32)
    rendered = render_basic_backend_task("BT06", run_seed=seed, run_nonce="diff-evidence")
    parent = tmp_path / "parent"
    parent.mkdir()
    fixture = materialize_basic_backend_fixture(parent, rendered)
    service_path = fixture.root / "src/service.py"
    service_path.write_text(service_path.read_text() + "\n# tracked change\n", encoding="utf-8")
    (fixture.root / "tests/test_added.py").write_text("def test_added():\n    assert True\n", encoding="utf-8")

    diff = _workspace_diff(fixture.root)

    assert "diff --git a/src/service.py b/src/service.py" in diff
    assert "# tracked change" in diff
    assert "diff --git a/tests/test_added.py b/tests/test_added.py" in diff
    assert "def test_added():" in diff


def test_service_environment_pins_local_adapter_aliases_and_drops_hosted_credentials(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    state_root = tmp_path / "state"
    source_root.mkdir()
    state_root.mkdir()
    spec = SimpleNamespace(
        inherited_environment={
            "HOME": str(tmp_path),
            "OPENAI_API_KEY": "must-not-pass",
            "ANTHROPIC_API_KEY": "must-not-pass",
            "SOURCE_PROXY_ARCHITECT_MODEL_ALIAS": "openai",
            "SOURCE_PROXY_CODER_REPAIR_MODEL_ALIAS": "openai",
        },
        source_root=source_root,
        state_root=state_root,
        python_executable=Path(sys.executable),
        authority_manifest_path=tmp_path / "authority.json",
        sandbox_image_id=TEST_IMAGE_ID,
        verifier_runtime_sha256=_fake_model_inventory()[
            "verifier_runtime_sha256"
        ],
    )

    environment = _service_environment(
        spec,
        port=8123,
        operator_secret="operator-secret",
        operator_state=tmp_path / "sessions.json",
    )

    assert environment["SOURCE_PROXY_ARCHITECT_MODEL_ALIAS"] == "local"
    assert environment["SOURCE_PROXY_CODER_REPAIR_MODEL_ALIAS"] == "local"
    assert environment["SOURCE_PROXY_DUMMY_PRODUCT_SITE_DIRECT_OLLAMA"] == "0"
    assert "OPENAI_API_KEY" not in environment
    assert "ANTHROPIC_API_KEY" not in environment


def test_proposal_material_requires_exact_persisted_diff_hash() -> None:
    state = {
        "target_plugin_proposal": {
            "runtime_output_id": "output-1",
            "approved_diff_sha256": "0" * 64,
            "target": "src/backend.py",
            "context_hash": "c" * 64,
            "status": "ready_for_approval_preview",
        },
        "runtime_outputs": [
            {"output_id": "output-1", "payload": {"approved_diff": "not the approved bytes"}}
        ],
    }
    with pytest.raises(Exception, match="basic_gate_target_plugin_diff_hash_mismatch"):
        _proposal_material(state, {})


def test_trace_reconciliation_reports_mapped_real_events_only(tmp_path: Path) -> None:
    client = FakeLifecycleClient(tmp_path)
    authority = client.request(
        "POST",
        "/v1/campaigns/campaign-3.5/model-call-authority",
        headers={"x-spiritos-operator-assertion": "signed-test-assertion"},
    )
    created = client.request(
        "POST", "/v1/tasks/long-running", {"description": "ordinary prompt"}
    )
    client.proposal_number = 2
    final_payload = client._final_response()
    final = client.request("GET", f"/v1/tasks/long-running/{client.task_id}")
    final = HttpExchange(**{**final.__dict__, "response": final_payload})

    receipt = reconcile_basic_backend_trace(
        task_id=client.task_id,
        orchestrator=final_payload["task"]["ast_snapshot"]["coding_orchestrator"],
        authority_exchange=authority,
        create_exchange=created,
        final_exchange=final,
    )

    assert receipt["passed"] is True
    assert receipt["synthetic_events_used"] is False
    assert set(receipt["requirements"]) == {
        "authenticated_request_accepted",
        "durable_task_created",
        "planner_or_router_decision",
        "coder_or_terminal_disposition",
        "reviewer_result",
        "verifier_result",
        "evidence_envelope_written",
        "final_receipt_written",
    }
    assert receipt["requirements"]["coder_or_terminal_disposition"]["production_evidence"] == (
        "target_plugin_proposal_ready or target_plugin_non_mutating_result"
    )


def test_authentication_boolean_without_signed_assertion_cannot_satisfy_trace(
    tmp_path: Path,
) -> None:
    client = FakeLifecycleClient(tmp_path)
    authority = client.request(
        "POST",
        "/v1/campaigns/campaign-3.5/model-call-authority",
        authenticated=True,
    )
    created = client.request(
        "POST",
        "/v1/tasks/long-running",
        {"description": "ordinary prompt"},
        authenticated=True,
    )
    client.proposal_number = 2
    final_payload = client._final_response()
    final = client.request("GET", f"/v1/tasks/long-running/{client.task_id}")
    final = HttpExchange(**{**final.__dict__, "response": final_payload})

    receipt = reconcile_basic_backend_trace(
        task_id=client.task_id,
        orchestrator=final_payload["task"]["ast_snapshot"]["coding_orchestrator"],
        authority_exchange=authority,
        create_exchange=created,
        final_exchange=final,
    )

    assert authority.authenticated is False
    assert authority.authentication["caller_claimed_authenticated"] is True
    assert authority.authentication["assertion_present"] is False
    assert receipt["requirements"]["authenticated_request_accepted"]["present"] is False
    assert receipt["passed"] is False


def test_all_adapter_calls_and_final_producer_are_inventory_bound() -> None:
    inventory = _fake_model_inventory()
    aliases = {item["role"]: item["alias"] for item in inventory["models"]}
    attempt = _fake_authenticated_execution_workflow("BT01")["attempts"][0]

    assert _attempt_model_provenance_verified(
        attempt,
        model_inventory=inventory,
        service_model_aliases=aliases,
    )

    unknown_call = copy.deepcopy(attempt)
    call = unknown_call["target_adapter_provenance"]["calls"][0]
    call["model_alias"] = "uncommitted"
    assert not _attempt_model_provenance_verified(
        unknown_call,
        model_inventory=inventory,
        service_model_aliases=aliases,
    )

    forged_producer = copy.deepcopy(attempt)
    forged_producer["producer_model_alias"] = "local"
    assert not _attempt_model_provenance_verified(
        forged_producer,
        model_inventory=inventory,
        service_model_aliases=aliases,
    )


def test_rederived_score_binds_source_service_oracle_verifier_and_model(
    tmp_path: Path,
) -> None:
    rendered = render_basic_backend_task(
        "BT01",
        run_seed=BasicBackendRunSeed.from_private_bytes(b"s" * 32),
        run_nonce="identity-binding",
    )
    phase_root = tmp_path / "first"
    phase_root.mkdir()
    receipt = _persist_passing_task_receipt(
        phase_root,
        "first",
        rendered,
        repair_succeeded=False,
    )
    assert _score_receipt(receipt, rendered)["passed"] is True

    mutations = []
    changed = copy.deepcopy(receipt)
    changed["source_head"] = "f" * 40
    mutations.append(changed)
    changed = copy.deepcopy(receipt)
    changed["service_process"]["branch"] = "wrong-branch"
    mutations.append(changed)
    changed = copy.deepcopy(receipt)
    changed["private_oracle"]["sandbox_image_id"] = "sha256:" + "e" * 64
    mutations.append(changed)
    changed = copy.deepcopy(receipt)
    changed["workflow"]["verifier_runtime_evidence"]["image"] = (
        "sha256:" + "e" * 64
    )
    mutations.append(changed)
    changed = copy.deepcopy(receipt)
    changed["service_process"]["model_inventory_sha256"] = "e" * 64
    mutations.append(changed)

    for forged in mutations:
        score = _score_receipt(forged, rendered)
        assert score["passed"] is False
        assert score["runtime_identity_bound"] is False or score[
            "model_provenance_valid"
        ] is False


def test_repair_success_is_rederived_and_rejects_forged_or_tampered_lineage(
    tmp_path: Path,
) -> None:
    seed = BasicBackendRunSeed.from_private_bytes(b"t" * 32)
    repaired = render_basic_backend_task(
        "BT01", run_seed=seed, run_nonce="repair-lineage"
    )
    repair_root = tmp_path / "repair"
    repair_root.mkdir()
    receipt = _persist_passing_task_receipt(
        repair_root,
        "first",
        repaired,
        repair_succeeded=True,
    )
    baseline = _score_receipt(receipt, repaired)
    assert baseline["passed"] is True
    assert baseline["repair_succeeded"] is True

    for mutation in ("input", "disposition", "manifest"):
        workflow = copy.deepcopy(receipt["workflow"])
        request = workflow["attempts"][0]["repair_request"]
        if mutation == "input":
            request["repair_input_sha256"] = "0" * 64
        elif mutation == "disposition":
            request["prior_approval_disposition"]["authority_state"] = "approved"
        else:
            request["current_state_manifest"]["workspace_root"] = "/wrong/root"
        assert not _rederive_repair_succeeded(
            workflow,
            expected_workspace_root=receipt["fixture_root"],
        )

    plain = render_basic_backend_task(
        "BT02", run_seed=seed, run_nonce="forged-repair-flag"
    )
    plain_root = tmp_path / "plain"
    plain_root.mkdir()
    forged = _persist_passing_task_receipt(
        plain_root,
        "first",
        plain,
        repair_succeeded=False,
    )
    forged["repair_succeeded"] = True
    score = _score_receipt(forged, plain)
    assert score["repair_succeeded"] is False
    assert score["declared_score_matches"] is False


def test_oracle_evidence_revalidation_binds_observations_and_anti_cheat_flags(
    tmp_path: Path,
) -> None:
    rendered = render_basic_backend_task(
        "BT01",
        run_seed=BasicBackendRunSeed.from_private_bytes(b"u" * 32),
        run_nonce="oracle-binding",
    )
    phase_root = tmp_path / "first"
    phase_root.mkdir()
    receipt = _persist_passing_task_receipt(
        phase_root,
        "first",
        rendered,
        repair_succeeded=False,
    )
    oracle = receipt["private_oracle"]
    assert _private_oracle_evidence_valid(
        oracle,
        expected_sandbox_image_id=TEST_IMAGE_ID,
        expected_task_id="BT01",
    )

    forged = copy.deepcopy(oracle)
    forged["candidate_received_task_id"] = True
    assert not _private_oracle_evidence_valid(
        forged,
        expected_sandbox_image_id=TEST_IMAGE_ID,
        expected_task_id="BT01",
    )

    private_path = Path(oracle["private_evidence_file"])
    private_payload = json.loads(private_path.read_text(encoding="utf-8"))
    task_swapped_payload = copy.deepcopy(private_payload)
    task_swapped_payload["task_id"] = "BT02"
    private_path.write_text(json.dumps(task_swapped_payload), encoding="utf-8")
    forged = copy.deepcopy(oracle)
    forged["private_payload_sha256"] = _sha256_json(task_swapped_payload)
    assert not _private_oracle_evidence_valid(
        forged,
        expected_sandbox_image_id=TEST_IMAGE_ID,
        expected_task_id="BT01",
    )

    private_payload["observations_sha256"] = "0" * 64
    private_path.write_text(json.dumps(private_payload), encoding="utf-8")
    forged = copy.deepcopy(oracle)
    forged["private_payload_sha256"] = _sha256_json(private_payload)
    assert not _private_oracle_evidence_valid(
        forged,
        expected_sandbox_image_id=TEST_IMAGE_ID,
        expected_task_id="BT01",
    )


def test_secret_scan_is_case_insensitive_for_task_ids_in_content_and_paths(
    tmp_path: Path,
) -> None:
    leaked_root = tmp_path / "bt01-production"
    leaked_root.mkdir()
    (leaked_root / "state.bin").write_bytes(b"opaque prefix Bt01 suffix")
    secret = b"raw-private-seed"
    (leaked_root / "nonce.bin").write_bytes(b"prefix" + secret + b"suffix")

    scan = _scan_production_evidence(
        roots=(leaked_root,),
        private_seed_markers=(secret,),
        forbidden_task_marker=b"BT01",
    )

    assert scan["scan_complete"] is True
    assert scan["private_seed_matches"]
    assert scan["benchmark_task_id_matches"]


def test_import_attestation_rejects_forbidden_benchmark_import(tmp_path: Path) -> None:
    log = tmp_path / "import-audit.jsonl"
    log.write_text(
        "\n".join(
            json.dumps(item)
            for item in (
                {"event": "hook_started", "pid": 9},
                {
                    "event": "forbidden_import",
                    "module": (
                        "source_proxy.benchmarks.campaign_3_5_basic_assets.oracles"
                    ),
                },
                {"event": "hook_completed", "forbidden_loaded": [], "pid": 9},
            )
        )
        + "\n",
        encoding="utf-8",
    )

    attestation = _finalize_service_import_audit(log)

    assert attestation["passed"] is False
    assert attestation["forbidden_imports"] == [
        "source_proxy.benchmarks.campaign_3_5_basic_assets.oracles"
    ]


def test_retained_fixture_mutation_is_rerun_and_detects_post_receipt_change(
    tmp_path: Path,
) -> None:
    rendered = render_basic_backend_task(
        "BT01",
        run_seed=BasicBackendRunSeed.from_private_bytes(b"v" * 32),
        run_nonce="mutation-rerun",
    )
    phase_root = tmp_path / "first"
    phase_root.mkdir()
    receipt = _persist_passing_task_receipt(
        phase_root,
        "first",
        rendered,
        repair_succeeded=False,
    )
    assert _score_receipt(receipt, rendered)["mutation_audit_valid"] is True

    fixture_root = Path(receipt["fixture_root"])
    (fixture_root / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\naddopts='--tampered'\n",
        encoding="utf-8",
    )
    score = _score_receipt(receipt, rendered)
    assert score["mutation_audit_valid"] is False
    assert score["passed"] is False
