#!/usr/bin/env python3
"""Focused fail-closed tests for the Foundation R1 production proving client."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


SCRIPT = Path(__file__).with_name("run-foundation-remediation-r1-proving.py")


def load_script() -> ModuleType:
    name = "foundation_remediation_r1_proving"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("proving script could not be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PROVER = load_script()


def plugin_identity(source_head: str) -> dict:
    return {
        "schema_version": "spiritos-target-plugin/v1",
        "plugin_id": "lumacart",
        "repository_id": "SpiritOS",
        "worktree_id": "foundation-r1",
        "workspace_root": "/srv/SpiritOS",
        "branch": "codex/foundation-r1",
        "state_namespace": "foundation-r1",
        "fixture_root": PROVER.FIXTURE_ROOT,
        "source_head": source_head,
        "selected_prompt_id": PROVER.PROMPT_ID,
        "selected_context_id": PROVER.CONTEXT_ID,
        "execution_profile": "coder-10",
        "allowed_actions": ["propose", "approve", "execute", "verify", "record-evidence"],
        "result_identity": f"lumacart:{PROVER.PROMPT_ID}:{source_head[:12]}",
        "approval_id": None,
        "approval_generation": None,
        "evidence_pointer": None,
        "failure_reason": None,
        "acknowledgement_status": "pending",
    }


def proposal_state(*, transport: str = "canonical_litellm_router") -> tuple[dict, object]:
    task_id = "task-production-1"
    run_id = "run-production-1"
    source_head = "a" * 40
    selection_id = "apr_selection_1"
    expected = PROVER.RecoveryExpectation(
        failed_provider="model-router",
        failed_model="intentionally-failing-alias",
        replacement_provider="ollama",
        replacement_model="qwen2.5-coder:14b",
    )
    diff = "\n".join(
        [
            f"diff --git a/{path} b/{path}\n--- /dev/null\n+++ b/{path}\n@@ -0,0 +1 @@\n+fixture"
            for path in PROVER.PROMPT1_FILES
        ]
    )
    context = {
        "canonical": True,
        "go_eligible": True,
        "canonical_report_hash": "context-report-hash",
    }
    adapter = {
        "schema_version": "spiritos-target-adapter-provenance/v1",
        "plugin_id": "lumacart",
        "selected_prompt_id": PROVER.PROMPT_ID,
        "rendered_prompt_sha256": "1" * 64,
        "raw_response_sha256": "2" * 64,
        "hash_algorithm": "sha256",
        "hash_encoding": "utf-8",
        "transport_kind": transport,
        "configured_transport_kind": transport,
        "provider_call_made": True,
        "provider_call_authorized": True,
        "generation_source": "model",
        "trust_status": "canonical_model_generation",
        "terminal_proof_eligible": True,
        "terminal_proof_ineligibility_reason": None,
        "selected_model_alias": "fallback-alias",
        "provider": expected.replacement_provider,
        "model": expected.replacement_model,
        "call_count": 1,
        "calls": [
            {
                "call_index": 1,
                "rendered_prompt_sha256": "1" * 64,
                "raw_response_sha256": "2" * 64,
                "raw_response_observed": True,
                "transport_kind": transport,
                "completed": True,
            }
        ],
    }
    model_output = {
        "schema_version": "coding.target-plugin-model-output-provenance/v1",
        "approved_diff_sha256": PROVER._sha256_text(diff),
        "changed_files": list(PROVER.PROMPT1_FILES),
        "blocked": False,
        "reason_code": "",
        "target_adapter_provenance": adapter,
    }
    failed = {
        "schema_version": "coding.recovery-participant/v1",
        "role": "target-plugin-model",
        "lane_id": "coder",
        "run_id": run_id,
        "task_id": task_id,
        "attempt_id": "attempt-primary",
        "invocation_id": "invocation-primary",
        "output_id": "output-primary",
        "provider": expected.failed_provider,
        "model": expected.failed_model,
        "input_sha256": PROVER._sha256_json({"input": 1}),
        "output_sha256": PROVER._sha256_json({"failed": True}),
        "artifact_sha256": None,
        "result_id": None,
        "error_code": "controlled_primary_route_failure",
        "error_message": "controlled failure",
        "started_at": "2026-07-17T00:00:00+00:00",
        "completed_at": "2026-07-17T00:00:01+00:00",
        "passed": False,
    }
    selected = {
        **failed,
        "attempt_id": "attempt-fallback",
        "invocation_id": "invocation-fallback",
        "output_id": "output-fallback",
        "provider": expected.replacement_provider,
        "model": expected.replacement_model,
        "output_sha256": PROVER._sha256_json(model_output),
        "artifact_sha256": PROVER._sha256_json(
            {"proposed_diff": diff, "changed_files": list(PROVER.PROMPT1_FILES)}
        ),
        "result_id": "target-plugin-result-1",
        "error_code": None,
        "error_message": None,
        "started_at": "2026-07-17T00:00:02+00:00",
        "completed_at": "2026-07-17T00:00:03+00:00",
        "passed": True,
    }
    failure_event = {
        "schema_version": "coding.orchestrator-event/v1",
        "event_id": "event-failure",
        "parent_event_id": "event-parent",
        "run_id": run_id,
        "attempt_id": "attempt-primary",
        "task_id": task_id,
        "event_type": "participant_failure",
        "lane_id": "coder",
        "status_before": "running",
        "status_after": "failed",
        "detail": {},
        "recorded_at": "2026-07-17T00:00:01+00:00",
    }

    def event(event_id: str, event_type: str, attempt_id: str) -> dict:
        return {
            **failure_event,
            "event_id": event_id,
            "event_type": event_type,
            "attempt_id": attempt_id,
        }

    recovery = {
        "schema_version": "coding.controlled-recovery/v1",
        "recovery_id": "recovery-1",
        "state": "completed",
        "run_id": run_id,
        "task_id": task_id,
        "failure": {
            "attempt_id": "attempt-primary",
            "event": failure_event,
            "participant": failed,
            "participant_sha256": PROVER._sha256_json(failed),
        },
        "decision": {
            "kind": "fallback",
            "event": event("event-decision", "controlled_recovery_decision", "attempt-primary"),
            "policy": {
                "schema_version": "coding.recovery-policy/v1",
                "allow_retry": False,
                "allow_fallback": True,
                "allowed_replacement_routes": [
                    {
                        "provider": expected.replacement_provider,
                        "model": expected.replacement_model,
                    }
                ],
            },
            "policy_sha256": "unused-by-client-test",
        },
        "replacement": {
            "attempt_id": "attempt-fallback",
            "parent_attempt_id": "attempt-primary",
            "provider": expected.replacement_provider,
            "model": expected.replacement_model,
            "start_event": event("event-start", "controlled_recovery_attempt_started", "attempt-fallback"),
            "participant": selected,
            "participant_sha256": PROVER._sha256_json(selected),
            "outcome_event": event("event-outcome", "controlled_recovery_attempt_succeeded", "attempt-fallback"),
            "outcome": "succeeded",
        },
        "claim_ceiling_impact": "recovered_via_declared_fallback_only",
        "proof_eligible": True,
        "created_at": "2026-07-17T00:00:01+00:00",
        "updated_at": "2026-07-17T00:00:03+00:00",
    }
    recovery["record_sha256"] = PROVER._sha256_json(recovery)
    output_payload = {
        "approved_diff": diff,
        "changed_files": list(PROVER.PROMPT1_FILES),
    }
    output = {
        "schema_version": "coding.runtime-lane-output/v1",
        "output_id": "runtime-coder-output",
        "lane_id": "coder",
        "contract_version": "coding.coder-output/v1",
        "producer_invocation_id": selected["invocation_id"],
        "artifact_hash": PROVER._sha256_json(output_payload),
        "issued_at": "2026-07-17T00:00:03+00:00",
        "payload": output_payload,
    }
    proposal = {
        "schema_version": "coding.target-plugin-proposal/v1",
        "task_id": task_id,
        "run_id": run_id,
        "runtime_output_id": output["output_id"],
        "runtime_output_artifact_sha256": output["artifact_hash"],
        "producer_model_invocation_id": selected["invocation_id"],
        "producer_model_output_sha256": selected["output_sha256"],
        "producer_model_artifact_sha256": selected["artifact_sha256"],
        "model_output_provenance": model_output,
        "target_adapter_provenance": adapter,
        "target_plugin_identity": plugin_identity(source_head),
        "selected_prompt_id": PROVER.PROMPT_ID,
        "selected_context_id": PROVER.CONTEXT_ID,
        "context_hash": context["canonical_report_hash"],
        "canonical_context_report": context,
        "canonical_context_report_sha256": PROVER._sha256_json(context),
        "context_runtime_output_id": "context-output",
        "context_runtime_artifact_sha256": PROVER._sha256_json({"context": 1}),
        "context_consumer_acknowledgement_id": "context-ack",
        "context_consumption_id": "context-consumption",
        "source_head": source_head,
        "target": PROVER.TARGET,
        "approved_diff_sha256": PROVER._sha256_text(diff),
        "changed_files": list(PROVER.PROMPT1_FILES),
        "status": "ready_for_approval_preview",
    }
    proposal["proposal_binding_sha256"] = PROVER._sha256_json(proposal)
    transfer = {
        "schema_version": "cartographer.coding-transfer/v1",
        "proposal_id": "proposal-1",
        "selection_id": selection_id,
        "selection_approval_id": selection_id,
        "selection_generation": 1,
        "consumer": PROVER.CONSUMER,
        "target": PROVER.TARGET,
        "task_id": task_id,
        "run_id": run_id,
        "transfer_event_id": "transfer-event-1",
        "downstream_consumer_invocation_id": selected["invocation_id"],
        "provenance": {
            "content_hash": "c" * 64,
            "context": "context-json",
            "preview_id": "selection-preview-1",
            "source_head": source_head,
        },
    }
    acknowledgement = {
        "schema_version": "cartographer.downstream-acknowledgement/v2",
        "acknowledgement_id": "cartographer-ack-1",
        "transfer_event_id": transfer["transfer_event_id"],
        "consumer_invocation_id": selected["invocation_id"],
        "consumer_output_id": selected["output_id"],
        "consumer_output_sha256": selected["output_sha256"],
        "consumer_artifact_sha256": selected["artifact_sha256"],
        "consumer_completed_at": selected["completed_at"],
        "consumer_passed": True,
        "proposal_id": "proposal-1",
        "selection_id": selection_id,
        "task_id": task_id,
        "run_id": run_id,
        "consumed": True,
    }
    state = {
        "schema_version": PROVER.ORCHESTRATOR_SCHEMA,
        "authoritative": True,
        "task_id": task_id,
        "run_id": run_id,
        "attempt_id": "attempt-primary",
        "target_plugin_proposal": proposal,
        "runtime_outputs": [output],
        "model_invocations": [failed, selected],
        "recovery_lineage": [recovery],
        "cartographer_transfer": transfer,
        "cartographer_finalization": {
            "state": "consumed",
            "authority_receipt": {"state": "consumed"},
            "downstream_acknowledgement": acknowledgement,
        },
        "target_plugin_result": {"proposed_diff": "CLIENT_OR_RESPONSE_ONLY_DIFF_MUST_NOT_WIN"},
    }
    return state, expected


def runtime_boundary_payload() -> dict:
    payload = {"passed": True}
    output = {
        "schema_version": "coding.runtime-lane-output/v1",
        "output_id": "output-1",
        "lane_id": "reviewer",
        "contract_version": "reviewer/v1",
        "producer_invocation_id": "producer-1",
        "artifact_hash": PROVER._sha256_json(payload),
        "issued_at": "2026-07-17T00:00:00+00:00",
        "payload": payload,
    }
    acknowledgement = {
        "schema_version": "coding.runtime-lane-acknowledgement/v1",
        "acknowledgement_id": "ack-1",
        "output_id": "output-1",
        "lane_id": "reviewer",
        "contract_version": "reviewer/v1",
        "producer_invocation_id": "producer-1",
        "artifact_hash": output["artifact_hash"],
        "consumer_version": "coding-orchestrator/v1",
        "consumer_invocation_id": "consumer-1",
        "acknowledged_at": "2026-07-17T00:00:01+00:00",
        "payload": {"consumed": True},
    }
    consumption = {
        "schema_version": "coding.runtime-lane-consumption/v1",
        "consumption_id": "consumption-1",
        "output_id": "output-1",
        "acknowledgement_id": "ack-1",
        "lane_id": "reviewer",
        "contract_version": "reviewer/v1",
        "artifact_hash": output["artifact_hash"],
        "consumer_version": "coding-orchestrator/v1",
        "consumer_invocation_id": "consumer-1",
        "consumed_at": "2026-07-17T00:00:02+00:00",
    }
    return {
        "runtime_outputs": [output],
        "runtime_acknowledgements": [acknowledgement],
        "runtime_consumptions": [consumption],
        "required_output_ids": ["output-1"],
    }


class FoundationR1ProvingTests(unittest.TestCase):
    def test_failure_diagnostics_emit_only_allowlisted_reason_codes(self) -> None:
        self.assertEqual(
            PROVER._safe_diagnostic_reason_codes(
                {
                    "detail": {
                        "production_proof_failures": [
                            "runtime_lane_boundary_invalid",
                            "anti_cheat_model_authorship_proof_invalid",
                            "runtime_lane_boundary_invalid",
                        ]
                    }
                }
            ),
            [
                "anti_cheat_model_authorship_proof_invalid",
                "runtime_lane_boundary_invalid",
            ],
        )
        for unsafe in (
            ["reason code with spaces"],
            ["safe_code", {"response_body": "forbidden"}],
            "runtime_lane_boundary_invalid",
            [],
        ):
            with self.subTest(unsafe=unsafe):
                self.assertEqual(
                    PROVER._safe_diagnostic_reason_codes(
                        {"detail": {"production_proof_failures": unsafe}}
                    ),
                    [],
                )

    def test_production_script_has_no_application_test_or_process_imports(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "import source_proxy",
            "from source_proxy",
            "import src.",
            "from src.",
            "import subprocess",
            "from unittest",
            "llm_call=",
            '"/target-plugin-proposal"',
        ):
            self.assertNotIn(forbidden, source)

    def test_next_plain_http_is_limited_to_loopback(self) -> None:
        self.assertEqual(
            PROVER._normalize_origin("http://localhost:3000/", role="next"),
            "http://localhost:3000",
        )
        with self.assertRaisesRegex(PROVER.ProvingError, "next_origin_plain_http_must_be_loopback"):
            PROVER._normalize_origin("http://10.0.0.9:3000", role="next")
        with self.assertRaisesRegex(PROVER.ProvingError, "source_origin_plain_http_must_be_loopback"):
            PROVER._normalize_origin("http://10.0.0.9:8000", role="source")
        with self.assertRaisesRegex(PROVER.ProvingError, "origin_contains_forbidden_components"):
            PROVER._normalize_origin("https://operator:secret@example.test", role="next")

    def test_next_requests_bind_same_origin_and_session_csrf(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task_file = root / "task.txt"
            task_file.write_text("A sufficiently long production proving task.", encoding="utf-8")
            config = PROVER.ProvingConfig(
                source_origin="http://localhost:8000",
                next_origin="http://localhost:3000",
                proposal_id="proposal-1",
                task_file=task_file,
                output=root / "receipt.json",
                timeout_seconds=10,
                recovery=PROVER.RecoveryExpectation("p1", "m1", "p2", "m2"),
                expected_source_head="a" * 40,
                expected_repository_id="SpiritOS",
                expected_worktree_id="foundation-r1",
            )
            captured = []

            class Response:
                status = 200
                headers = {"content-type": "application/json"}

                def read(self, _limit):
                    return b"{}"

            class Opener:
                def open(self, request, timeout):
                    del timeout
                    captured.append(request)
                    return Response()

            client = PROVER.ProductionHttpClient(config)
            client._opener = Opener()
            client.json("next", "POST", "/v1/operator/session", {"credential": "redacted"})
            self.assertEqual(captured[-1].get_header("Origin"), config.next_origin)
            self.assertIsNone(captured[-1].get_header("X-spiritos-csrf"))
            client.bind_csrf("csrf-value")
            client.json("next", "POST", "/v1/operator/approval", {"action": "approve"})
            self.assertEqual(captured[-1].get_header("Origin"), config.next_origin)
            self.assertEqual(captured[-1].get_header("X-spiritos-csrf"), "csrf-value")

    def test_persisted_runtime_output_is_the_only_accepted_diff_source(self) -> None:
        state, expected = proposal_state()
        diff, material = PROVER._extract_persisted_proposal(
            state,
            task_id=state["task_id"],
            proposal_id="proposal-1",
            selection_id="apr_selection_1",
            expectation=expected,
        )
        self.assertNotIn("CLIENT_OR_RESPONSE_ONLY_DIFF", diff)
        self.assertEqual(PROVER._sha256_text(diff), material["approved_diff_sha256"])
        self.assertTrue(material["recovery"]["proof_eligible"])

    def test_injected_callback_or_direct_transport_is_never_production_proof(self) -> None:
        for transport in ("injected_callback", "direct_ollama"):
            state, expected = proposal_state(transport=transport)
            with self.subTest(transport=transport), self.assertRaisesRegex(
                PROVER.ProvingError, "target_adapter_transport_kind_invalid"
            ):
                PROVER._extract_persisted_proposal(
                    state,
                    task_id=state["task_id"],
                    proposal_id="proposal-1",
                    selection_id="apr_selection_1",
                    expectation=expected,
                )

    def test_recovery_route_must_match_predeclared_provider_and_model(self) -> None:
        state, expected = proposal_state()
        wrong = PROVER.RecoveryExpectation(
            failed_provider=expected.failed_provider,
            failed_model="another-primary",
            replacement_provider=expected.replacement_provider,
            replacement_model=expected.replacement_model,
        )
        with self.assertRaisesRegex(PROVER.ProvingError, "controlled_recovery_failed_model_mismatch"):
            PROVER._extract_persisted_proposal(
                state,
                task_id=state["task_id"],
                proposal_id="proposal-1",
                selection_id="apr_selection_1",
                expectation=wrong,
            )

    def test_runtime_output_requires_distinct_acknowledgement_and_consumption(self) -> None:
        state = runtime_boundary_payload()
        summary = PROVER._validate_runtime_boundary(state)
        self.assertTrue(summary["all_required_outputs_consumed"])
        state["runtime_acknowledgements"][0]["consumer_invocation_id"] = "producer-1"
        with self.assertRaisesRegex(PROVER.ProvingError, "runtime_acknowledgement_not_independent"):
            PROVER._validate_runtime_boundary(state)

    def test_runtime_output_cannot_be_left_unconsumed(self) -> None:
        state = runtime_boundary_payload()
        state["runtime_consumptions"] = []
        with self.assertRaisesRegex(PROVER.ProvingError, "runtime_output_consumption_incomplete"):
            PROVER._validate_runtime_boundary(state)

    def test_diff_preview_must_be_read_only_and_scope_exact(self) -> None:
        payload = {
            "tool": "diff_verification_preview",
            "access_scope": "read_only_diff_preview",
            "status": "preview_ready",
            "would_apply_diff": False,
            "would_execute": False,
            "git_apply_check_ok": True,
            "blocked_reasons": [],
            "changed_files": [{"path": path} for path in PROVER.PROMPT1_FILES],
            "limits": {"terminal_execution_allowed": False},
            "task_spec_check": {"ok": True},
            "deterministic_checks": [
                {"id": "git_apply", "blocking": True, "status": "passed"},
                {"id": "syntax_parse", "blocking": True, "status": "skipped"},
            ],
            "risk": "low",
        }
        self.assertEqual(
            PROVER._validate_diff_preview(payload, PROVER.PROMPT1_FILES)["status"],
            "preview_ready",
        )
        for status in ("failed", "timeout"):
            invalid = {
                **payload,
                "deterministic_checks": [
                    {"id": "syntax_parse", "blocking": True, "status": status}
                ],
            }
            with self.subTest(status=status), self.assertRaisesRegex(
                PROVER.ProvingError,
                "diff_preview_blocking_check_failed",
            ):
                PROVER._validate_diff_preview(invalid, PROVER.PROMPT1_FILES)
        payload["would_execute"] = True
        with self.assertRaisesRegex(PROVER.ProvingError, "diff_preview_would_execute_invalid"):
            PROVER._validate_diff_preview(payload, PROVER.PROMPT1_FILES)

    def test_cartographer_exact_proposal_must_be_persisted_and_actionable(self) -> None:
        proposal = {
            "proposal_id": "proposal-1",
            "persisted": True,
            "generated": False,
            "status": "pending_review",
            "type": "coding_target_selection",
            "component": "coding-foundation",
            "proposed_files": [PROVER.TARGET],
            "warnings": [],
            "requires_approval": True,
            "fingerprint": "a" * 16,
            "transitions": [
                {
                    "status": "pending_review",
                    "timestamp": "2026-07-17T00:00:00Z",
                    "actor": "foundation-remediation-r1-control-plane",
                }
            ],
        }
        def collection(item):
            return {
                "status": "observing",
                "write_actions_enabled": False,
                "authority_granted": False,
                "apply_allowed": False,
                "commit_allowed": False,
                "push_allowed": False,
                "actions_taken": False,
                "transition_audit_complete": True,
                "proposals": [item],
            }

        summary = PROVER._validate_cartographer_proposal_collection(
            collection(proposal),
            proposal_id="proposal-1",
        )
        self.assertTrue(summary["persisted"])
        self.assertEqual(summary["fingerprint"], "a" * 16)
        self.assertRegex(summary["selection_content_sha256"], r"^[0-9a-f]{64}$")
        for key, value, reason in (
            ("persisted", False, "persisted_invalid"),
            ("generated", True, "generated_invalid"),
            ("warnings", ["malformed"], "warnings_invalid"),
            ("proposed_files", ["README.md"], "proposed_files_invalid"),
        ):
            invalid = {**proposal, key: value}
            with self.subTest(key=key), self.assertRaisesRegex(
                PROVER.ProvingError,
                reason,
            ):
                PROVER._validate_cartographer_proposal_collection(
                    collection(invalid),
                    proposal_id="proposal-1",
                )

        for fingerprint in ("a" * 15, "a" * 17, "A" * 16, "g" * 16, "a" * 64):
            with self.subTest(fingerprint=fingerprint), self.assertRaisesRegex(
                PROVER.ProvingError,
                "cartographer_proposal_fingerprint_invalid",
            ):
                PROVER._validate_cartographer_proposal_collection(
                    collection({**proposal, "fingerprint": fingerprint}),
                    proposal_id="proposal-1",
                )

        changed_summary = PROVER._validate_cartographer_proposal_collection(
            collection({**proposal, "fingerprint": "b" * 16}),
            proposal_id="proposal-1",
        )
        self.assertNotEqual(
            summary["selection_content_sha256"],
            changed_summary["selection_content_sha256"],
        )
        PROVER._validate_cartographer_selection_binding(
            summary,
            {"content_hash": summary["selection_content_sha256"]},
        )
        with self.assertRaisesRegex(
            PROVER.ProvingError,
            "cartographer_selection_proposal_binding_mismatch",
        ):
            PROVER._validate_cartographer_selection_binding(
                summary,
                {"content_hash": changed_summary["selection_content_sha256"]},
            )

    def test_reset_requires_exact_absent_source_head_baseline(self) -> None:
        source_head = "a" * 40
        payload = {
            "status": "reset_verified",
            "reset_verified": True,
            "clean_verified": True,
            "fixture_root": PROVER.FIXTURE_ROOT,
            "source_head": source_head,
            "source_baseline_verified": True,
            "source_baseline_sha256": "b" * 64,
            "source_baseline_tracked_paths": [],
            "removed_paths": [],
            "reset_receipt_id": "dummy-product-site-reset-1",
            "target_plugin_identity": plugin_identity(source_head),
        }
        summary = PROVER._validate_reset(payload, source_head)
        self.assertTrue(summary["source_baseline_verified"])
        for key, value, reason in (
            ("source_head", "c" * 40, "source_head_mismatch"),
            ("source_baseline_verified", False, "baseline_not_verified"),
            ("source_baseline_tracked_paths", [PROVER.TARGET], "baseline_not_absent"),
            ("removed_paths", [PROVER.FIXTURE_ROOT], "not_post_undo_idempotent"),
        ):
            invalid = {**payload, key: value}
            with self.subTest(key=key), self.assertRaisesRegex(
                PROVER.ProvingError,
                reason,
            ):
                PROVER._validate_reset(invalid, source_head)

    def test_canonical_transcript_has_one_proposal_generation_per_run(self) -> None:
        source_head = "a" * 40

        def result(ordinal: int):
            return PROVER.RunResult(
                summary={"task_id": f"task-{ordinal}"},
                approved_diff="diff",
                prompt_packet_diff="diff",
                backup_manifest=f"backup-{ordinal}.json",
                source_commit=source_head,
                repository_identity={"repository": "SpiritOS"},
                target_plugin_identity=plugin_identity(source_head),
            )

        sequence = PROVER._expected_exchange_sequence(
            "proposal-1",
            result(1),
            result(2),
        )
        paths = [path for _service, _method, path in sequence]
        self.assertEqual(paths.count("/v1/decisions/prompt-packet"), 2)
        self.assertEqual(paths.count("/v1/cartographer/proposals"), 2)
        self.assertFalse(any(path.endswith("/target-plugin-proposal") for path in paths))
        self.assertEqual(paths[-2:], ["/v1/operator/session", "/v1/operator/session"])

    def test_redaction_rejects_raw_values_and_forbidden_keys(self) -> None:
        secret = "credential-value-never-record"
        with self.assertRaisesRegex(PROVER.ProvingError, "sensitive_value_present"):
            PROVER._assert_receipt_redacted({"safe": secret}, [secret])
        with self.assertRaisesRegex(PROVER.ProvingError, "forbidden_key_present"):
            PROVER._assert_receipt_redacted({"approved_diff": "hash-only-was-required"}, [])
        for key in ("access_token_hash", "client_secret_state", "authorization_present"):
            with self.subTest(key=key), self.assertRaisesRegex(
                PROVER.ProvingError,
                "forbidden_key_present",
            ):
                PROVER._assert_receipt_redacted({key: False}, [])

    def test_nonproduction_transport_cannot_seal_a_receipt(self) -> None:
        class FakeClient:
            production_http = False

        with self.assertRaisesRegex(PROVER.ProvingError, "nonproduction_transport"):
            PROVER._build_receipt(
                client=FakeClient(),
                config=None,
                started_at="now",
                completed_at="later",
                task_text="a sufficiently long proving task",
                operator_hash="hash",
                first=None,
                second=None,
                undo={},
                reset={},
                attestation=None,
                revocation_response_sha256="",
                retired_session_probe_response_sha256="",
                forbidden_values=[],
            )

    def test_exact_client_with_synthetic_runs_and_no_http_cannot_seal_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task_file = root / "task.txt"
            task_file.write_text("Build the bounded LumaCart production proving fixture.", encoding="utf-8")
            config = PROVER.ProvingConfig(
                source_origin="http://localhost:8000",
                next_origin="http://localhost:3000",
                proposal_id="proposal-1",
                task_file=task_file,
                output=root / "receipt.json",
                timeout_seconds=10,
                recovery=PROVER.RecoveryExpectation(
                    failed_provider="model-router",
                    failed_model="failed-alias",
                    replacement_provider="ollama",
                    replacement_model="qwen",
                ),
                expected_source_head="a" * 40,
                expected_repository_id="SpiritOS",
                expected_worktree_id="foundation-r1",
            )
            client = PROVER.ProductionHttpClient(config)
            source_head = "a" * 40
            repository = {
                "repository": "SpiritOS",
                "worktree": "/srv/SpiritOS",
                "root": "/srv/SpiritOS",
            }

            def result(ordinal: int) -> object:
                return PROVER.RunResult(
                    summary={
                        "task_id": f"task-{ordinal}",
                        "orchestrator_run_id": f"run-{ordinal}",
                        "approval": {"approval_id": f"apr_{ordinal}"},
                        "artifact": {"artifact_sha256": f"sha256:{str(ordinal) * 64}"},
                    },
                    approved_diff=f"raw-diff-{ordinal}-must-not-appear",
                    prompt_packet_diff=f"unused-prompt-diff-{ordinal}-must-not-appear",
                    backup_manifest=f"data/backup-{ordinal}/manifest.json",
                    source_commit=source_head,
                    repository_identity=repository,
                    target_plugin_identity=plugin_identity(source_head),
                )

            task_text = task_file.read_text(encoding="utf-8")
            first = result(1)
            second = result(2)
            arguments = {
                "client": client,
                "config": config,
                "started_at": "2026-07-17T00:00:00+00:00",
                "completed_at": "2026-07-17T00:01:00+00:00",
                "task_text": task_text,
                "operator_hash": "f" * 64,
                "first": first,
                "second": second,
                "undo": {"filesystem_verified": True},
                "reset": {"clean_verified": True},
                "revocation_response_sha256": "e" * 64,
                "retired_session_probe_response_sha256": "d" * 64,
                "forbidden_values": [
                    task_text,
                    first.approved_diff,
                    first.prompt_packet_diff,
                    second.approved_diff,
                    second.prompt_packet_diff,
                ],
            }
            for attestation in (
                None,
                PROVER.ProductionRunAttestation(
                    schema_version="spiritos-production-http-run-attestation/v1",
                    transcript_sha256="sha256:" + "1" * 64,
                    binding_sha256="sha256:" + "2" * 64,
                    exchange_count=27,
                    _attestation_mac="3" * 64,
                ),
            ):
                with self.subTest(attestation=attestation), self.assertRaisesRegex(
                    PROVER.ProvingError,
                    "production_run_attestation_missing",
                ):
                    PROVER._build_receipt(
                        **arguments,
                        attestation=attestation,
                    )

    def test_atomic_receipt_writer_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "receipt.json"
            PROVER._write_new_receipt(output, {"receipt_sha256": "sha256:" + "a" * 64})
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["receipt_sha256"], "sha256:" + "a" * 64)
            with self.assertRaisesRegex(PROVER.ProvingError, "output_already_exists"):
                PROVER._write_new_receipt(output, {"replacement": True})


if __name__ == "__main__":
    unittest.main()
