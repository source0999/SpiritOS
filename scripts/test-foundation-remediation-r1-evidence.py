#!/usr/bin/env python3
"""Focused regressions for the R1 immutable-evidence builder and validator."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(__file__).with_name("generate-foundation-remediation-r1-evidence.py")
VALIDATOR_PATH = Path(__file__).with_name("validate-foundation-remediation-r1-evidence.py")


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATOR = load_module("foundation_r1_evidence_generator", GENERATOR_PATH)
VALIDATOR = load_module("foundation_r1_evidence_validator", VALIDATOR_PATH)


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def initialize_repository(root: Path) -> str:
    git(root, "init", "-q")
    git(root, "config", "user.email", "foundation-r1@example.invalid")
    git(root, "config", "user.name", "Foundation R1 Test")
    (root / "seed.txt").write_text("source\n", encoding="utf-8")
    authority_validator = root / GENERATOR.AUTHORITY_VALIDATOR_PATH
    authority_validator.parent.mkdir(parents=True)
    authority_validator.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    git(root, "add", "seed.txt", GENERATOR.AUTHORITY_VALIDATOR_PATH)
    git(root, "commit", "-q", "-m", "source")
    return git(root, "rev-parse", "HEAD")


def protected_report(source_commit: str) -> dict:
    entries = []
    for name in sorted(GENERATOR.EXPECTED_PROTECTED_HEADS):
        entries.append(
            {
                "name": name,
                "protected_commit": GENERATOR.EXPECTED_PROTECTED_HEADS[name],
                "ref": GENERATOR.PROTECTED_REFS[name],
                "expected_tip": GENERATOR.EXPECTED_PROTECTED_REF_TIPS[name],
                "actual_tip": GENERATOR.EXPECTED_PROTECTED_REF_TIPS[name],
                "commit_readable": True,
                "ref_matches": True,
                "protected_commit_in_ref_history": True,
                "passed": True,
            }
        )
    return {
        "schema": GENERATOR.PROTECTED_REPORT_SCHEMA,
        "remediation_id": GENERATOR.REMEDIATION_ID,
        "source_commit": source_commit,
        "generated_at": "2026-07-17T20:00:00+00:00",
        "inventory_matches_state": True,
        "entries": entries,
        "passed": True,
    }


CLAIM_CEILING = "recovered_via_declared_fallback_only"
TARGET = "fixtures/dummy-product-site/README.md"
PROMPT_ID = "lumacart-dummy-product-site"
CONTEXT_ID = "coding-truth"


def proving_participants(prefix: str) -> list[dict]:
    return [
        {
            "role": proving_role,
            "service": f"{proving_role}-service",
            "model": f"{proving_role}-model",
            "invocation_id": f"{prefix}-{role}-invocation",
            "output_id": f"{prefix}-{role}-output",
            "consumer_acknowledgement_id": f"{prefix}-{role}-ack",
            "output_sha256": f"sha256:{str(index + 1) * 64}"[:71],
            "passed": True,
        }
        for index, (role, proving_role) in enumerate(GENERATOR.PROVING_PARTICIPANT_ROLES.items())
    ]


def proving_run(source_commit: str, *, ordinal: int) -> dict:
    prefix = f"run-{ordinal}"
    artifact_hash = ("a" if ordinal == 2 else "9") * 64
    result_hash = ("e" if ordinal == 2 else "8") * 64
    approval_id = f"apr_proving_{ordinal}"
    return {
        "ordinal": ordinal,
        "clean_rerun": ordinal == 2,
        "task_id": f"task-{ordinal}",
        "orchestrator_run_id": f"orchestrator-run-{ordinal}",
        "orchestrator_attempt_id": f"orchestrator-attempt-{ordinal}",
        "source_commit": source_commit,
        "task_prompt_sha256": "b" * 64,
        "cartographer_proposal": {"proposed_files": [TARGET]},
        "cartographer": {"authority_state": "consumed"},
        "selection_preview_id": f"selection-preview-{ordinal}",
        "selection_generation": ordinal,
        "prompt_packet": {"selected_prompt_id": PROMPT_ID},
        "target_proposal": {"approved_diff_sha256": "d" * 64},
        "context": {
            "context_hash": f"sha256:{'c' * 64}",
            "runtime_output_id": f"context-output-{ordinal}",
            "consumer_acknowledgement_id": f"context-ack-{ordinal}",
            "consumption_id": f"context-consumption-{ordinal}",
        },
        "target_adapter": {
            "provider": "fallback-provider",
            "model": "fallback-model",
            "terminal_proof_eligible": True,
        },
        "controlled_recovery": {
            "recovery_id": f"recovery-{ordinal}",
            "decision": "fallback",
            "failure": {
                "provider": "failed-provider",
                "model": "failed-model",
                "invocation_id": f"failed-invocation-{ordinal}",
            },
            "replacement": {
                "provider": "fallback-provider",
                "model": "fallback-model",
                "invocation_id": f"replacement-invocation-{ordinal}",
                "output_id": f"replacement-output-{ordinal}",
            },
            "claim_ceiling_impact": CLAIM_CEILING,
            "proof_eligible": True,
        },
        "diff_preview": {"status": "preview_ready"},
        "approval": {
            "preview_id": f"approval-preview-{ordinal}",
            "preview_generation": ordinal,
            "approval_id": approval_id,
            "approval_generation": ordinal,
            "preview_response_sha256": str(ordinal) * 64,
        },
        "execution_response_sha256": "1" * 64,
        "verification_response_sha256": "2" * 64,
        "final_readback_response_sha256": "3" * 64,
        "task_status": "completed",
        "verification_status": "verified",
        "real_browser_used": True,
        "browser_engine": "playwright_chromium",
        "artifact": {
            "artifact_sha256": f"sha256:{artifact_hash}",
            "result_sha256": f"sha256:{result_hash}",
            "approved_diff_sha256": "d" * 64,
            "approval_id": approval_id,
            "generation": ordinal,
        },
        "pre_apply_source_baseline": {"fixture_absent": True},
        "participants": proving_participants(prefix),
        "runtime_boundary": {"all_required_outputs_consumed": True},
        "production_proof": {
            "proof_sha256": f"sha256:{('f' if ordinal == 2 else '7') * 64}",
            "terminal_proof_eligible": True,
            "claim_ceiling": CLAIM_CEILING,
            "failures": [],
        },
        "approval_final_state": "consumed",
        "verification_preceded_final_result": True,
        "http_exchange_ordinals": [ordinal, ordinal + 10],
    }


def write_production_receipts(root: Path, source_commit: str) -> tuple[Path, Path, dict]:
    first = proving_run(source_commit, ordinal=1)
    second = proving_run(source_commit, ordinal=2)
    undo = {
        "original_task_id": first["task_id"],
        "undo_receipt_id": "undo-receipt-1",
        "selected_backup_manifest": "backup-manifest-1",
        "approved_diff_sha256": "d" * 64,
        "files_restored": [TARGET],
        "source_baseline_restored": True,
        "fixture_absent": True,
        "filesystem_verified": True,
        "untouched_scope_assertion": True,
        "final_truth_status": "UNDO_FILESYSTEM_VERIFIED",
    }
    reset = {
        "status": "reset_verified",
        "reset_receipt_id": "reset-receipt-1",
        "fixture_root": "fixtures/dummy-product-site",
        "removed_paths": [],
        "clean_verified": True,
        "source_head": source_commit,
        "source_baseline_verified": True,
        "source_baseline_sha256": "4" * 64,
        "source_baseline_tracked_paths": [],
        "target_plugin_result_identity": {"plugin_id": "lumacart"},
    }
    exchanges = [{"ordinal": index, "response_sha256": str(index % 10) * 64} for index in range(1, 4)]
    operator = {
        "operator_identity_sha256": "5" * 64,
        "role": "approval-issuer",
        "authenticated": True,
        "revoked": True,
        "revocation_response_sha256": "6" * 64,
        "retired_session_probe_response_sha256": "7" * 64,
        "retired_session_status": "revoked",
        "cookie_jar_cleared": True,
        "credential_recorded": False,
        "session_identifier_recorded": False,
    }
    binding = {
        "schema_version": "spiritos-production-http-run-binding/v1",
        "operator_identity_sha256": operator["operator_identity_sha256"],
        "revocation_response_sha256": operator["revocation_response_sha256"],
        "retired_session_probe_response_sha256": operator[
            "retired_session_probe_response_sha256"
        ],
        "source_head": source_commit,
        "first_run_summary_sha256": GENERATOR.compact_sha256(first),
        "second_run_summary_sha256": GENERATOR.compact_sha256(second),
        "undo_summary_sha256": GENERATOR.compact_sha256(undo),
        "reset_summary_sha256": GENERATOR.compact_sha256(reset),
    }
    inner = {
        "schema_version": GENERATOR.PRODUCTION_PROVING_RECEIPT_SCHEMA,
        "receipt_type": "foundation_r1_black_box_production_proving",
        "remediation_id": GENERATOR.REMEDIATION_ID,
        "run_mode": "production_http",
        "terminal_proof_eligible": True,
        "claim_ceiling": CLAIM_CEILING,
        "started_at": "2026-07-17T19:00:00+00:00",
        "completed_at": "2026-07-17T19:30:00+00:00",
        "source_commit": source_commit,
        "expected_runtime_identity": {
            "source_head": source_commit,
            "repository_id": "test-repository",
            "worktree_id": "test-proof-worktree",
            "worktree_id_source": "approval_preflight.stateNamespace",
        },
        "repository_identity": {
            "repository": "test-repository",
            "worktree": str(root),
            "root": str(root),
        },
        "transport": {
            "kind": "production_http",
            "source_origin": "http://127.0.0.1:18001",
            "next_origin": "https://127.0.0.1:18443",
            "origins_distinct": True,
            "redirects_allowed": False,
            "services_started_by_harness": False,
            "application_modules_imported": False,
            "test_modules_imported": False,
            "callback_transport_allowed": False,
        },
        "task_prompt": {"sha256": "b" * 64, "byte_count": 10, "raw_text_recorded": False},
        "target_plugin_identity": {
            "plugin_id": "lumacart",
            "repository_id": "test-repository",
            "worktree_id": "test-proof-worktree",
            "source_head": source_commit,
            "selected_prompt_id": PROMPT_ID,
            "selected_context_id": CONTEXT_ID,
        },
        "operator_session": operator,
        "runs": [first, second],
        "run_attestation": {
            "schema_version": "spiritos-production-http-run-attestation/v1",
            "transcript_sha256": GENERATOR.compact_sha256(exchanges),
            "binding_sha256": GENERATOR.compact_sha256(binding),
            "exchange_count": len(exchanges),
            "client_verified": True,
        },
        "undo": undo,
        "reset": reset,
        "clean_rerun": {
            "completed": True,
            "source_commit_unchanged": True,
            "source_baseline_sha256": reset["source_baseline_sha256"],
            "source_baseline_verified": True,
            "fixture_absent_before_each_run": True,
            "reset_was_idempotent_after_undo": True,
            "repository_identity_unchanged": True,
            "task_id_distinct": True,
            "run_id_distinct": True,
            "approval_id_distinct": True,
            "artifact_identity_distinct": True,
        },
        "expected_controlled_recovery": {
            "failed_provider": "failed-provider",
            "failed_model": "failed-model",
            "replacement_provider": "fallback-provider",
            "replacement_model": "fallback-model",
        },
        "http_exchanges": exchanges,
        "redaction": {"status": "passed"},
        "failures": [],
    }
    inner["receipt_sha256"] = GENERATOR.compact_sha256(inner)
    evidence_dir = root / "docs/evidence-manifests/foundation-remediation-r1"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    proving_path = evidence_dir / "production-proving-receipt.json"
    GENERATOR.write_json_atomic(proving_path, inner)

    services = []
    for name in ("source_proxy", "next", "next_tls"):
        services.append(
            {
                "name": name,
                "cwd_bound_to_proof_worktree": True,
                "loopback_bound": True,
                "stopped": True,
                "process_absent": True,
                "process_group_absent": True,
                "process_session_absent": True,
                "descendant_processes_absent": True,
                "port_closed": True,
                "listener_identity_sha256": "a" * 64,
                "raw_pid_recorded": False,
                "raw_port_recorded": False,
            }
        )
    outer = {
        "schema_version": GENERATOR.LIFECYCLE_RECEIPT_SCHEMA,
        "receipt_type": "foundation_r1_clean_production_service_lifecycle",
        "remediation_id": GENERATOR.REMEDIATION_ID,
        "status": "passed",
        "terminal_proof_eligible": False,
        "claim_ceiling": "subordinate_clean_checkout_build_service_and_revocation_proof_only",
        "started_at": "2026-07-17T18:50:00+00:00",
        "completed_at": "2026-07-17T19:35:00+00:00",
        "source": {
            "repository_id": "test-repository",
            "worktree_root": str(root),
            "source_head": source_commit,
            "worktree_id": "test-proof-worktree",
            "registered_linked_worktree": True,
            "clean_before_build": True,
        },
        "build": {
            "next": {"build_id_sha256": "8" * 64},
            "source_proxy": {"source_tree": "9" * 40},
        },
        "services": services,
        "inner_proving": {
            **inner,
            "execution": {"receipt_sha256": inner["receipt_sha256"]},
            "published_only_after_lifecycle_teardown": True,
        },
        "temporary_authority": {
            "state_root_removed": True,
            "shared_signing_key_preexisted": True,
            "shared_signing_key_unchanged": True,
        },
        "teardown": {
            "dependency_link_removed": True,
            "next_build_removed": True,
            "backup_state_removed": True,
            "runtime_receipts_removed": True,
            "tracked_status_clean": True,
            "ignored_status_restored": True,
            "source_head_unchanged": True,
            "branch_unchanged": True,
            "repository_identity_unchanged": True,
            "linked_worktree_registration_unchanged": True,
            "index_visibility_unchanged": True,
            "all_services_stopped": True,
            "all_service_processes_absent": True,
            "all_service_ports_closed": True,
            "temporary_state_removed": True,
            "operator_session_revoked": True,
            "temporary_approval_authority_inactive": True,
            "failures": [],
        },
        "redaction": {"status": "passed"},
        "failures": [],
    }
    outer["receipt_sha256"] = GENERATOR.compact_sha256(outer)
    lifecycle_path = evidence_dir / "lifecycle-receipt.json"
    GENERATOR.write_json_atomic(lifecycle_path, outer)
    return proving_path, lifecycle_path, second


def terminal_spec(root: Path, source_commit: str, tag_name: str, authority_path: str) -> dict:
    proving_path, lifecycle_path, second = write_production_receipts(root, source_commit)
    artifact_hash = "a" * 64
    result_hash = "e" * 64
    participants = {}
    proving_by_role = {item["role"]: item for item in second["participants"]}
    for role, proving_role in GENERATOR.PROVING_PARTICIPANT_ROLES.items():
        observed = proving_by_role[proving_role]
        participants[role] = {
            "status": "succeeded" if role == "executor" else "passed",
            "invocation_id": observed["invocation_id"],
            "output_id": observed["output_id"],
            "output_sha256": observed["output_sha256"].removeprefix("sha256:"),
            "consumer_acknowledgement_id": observed["consumer_acknowledgement_id"],
            "artifact_sha256": artifact_hash,
        }
    authority_file = root / authority_path
    return {
        "source_commit": source_commit,
        "repository_identity": {
            "repository_id": "test-repository",
            "worktree_id": "test-worktree",
            "worktree_realpath": str(root),
        },
        "protected_heads": dict(GENERATOR.EXPECTED_PROTECTED_HEADS),
        "shell_build_identity": {"build_id": "8" * 64, "source_commit": source_commit},
        "backend_build_identity": {"build_id": "9" * 40, "source_commit": source_commit},
        "target_plugin_identity": {"plugin_id": "lumacart", "source_head": source_commit},
        "prompt_identity": {"id": PROMPT_ID, "sha256": "b" * 64},
        "context_identity": {"id": CONTEXT_ID, "sha256": "c" * 64},
        "task_id": second["task_id"],
        "orchestrator_run_id": second["orchestrator_run_id"],
        "orchestrator_attempt_id": second["orchestrator_attempt_id"],
        "target": TARGET,
        "participants": participants,
        "approval": {
            "approval_id": second["approval"]["approval_id"],
            "generation": second["approval"]["approval_generation"],
            "state": "consumed",
            "artifact_sha256": artifact_hash,
            "orchestrator_run_id": second["orchestrator_run_id"],
        },
        "artifact_sha256": artifact_hash,
        "applied_diff_sha256": "d" * 64,
        "result_sha256": result_hash,
        "production_proof": {
            "proof_sha256": "f" * 64,
            "terminal_proof_eligible": True,
            "claim_ceiling": CLAIM_CEILING,
            "recovery_id": second["controlled_recovery"]["recovery_id"],
        },
        "production_proving_receipt": {
            "path": proving_path.relative_to(root).as_posix(),
            "sha256": GENERATOR.sha256_file(proving_path),
        },
        "lifecycle_receipt": {
            "path": lifecycle_path.relative_to(root).as_posix(),
            "sha256": GENERATOR.sha256_file(lifecycle_path),
        },
        "reviewer_result": {"status": "passed", "invocation_id": participants["reviewer"]["invocation_id"]},
        "verifier_result": {"status": "passed", "invocation_id": participants["verifier"]["invocation_id"]},
        "anti_cheat_result": {"status": "passed", "invocation_id": participants["anti_cheat"]["invocation_id"]},
        "authority_validation": {
            "source_commit": source_commit,
            "tag_name": tag_name,
            "validator_path": GENERATOR.AUTHORITY_VALIDATOR_PATH,
            "validator_sha256": GENERATOR.git_blob_sha256(
                root,
                source_commit,
                GENERATOR.AUTHORITY_VALIDATOR_PATH,
            ),
            "artifact_path": authority_path,
            "artifact_sha256": GENERATOR.sha256_file(authority_file),
            "result": "pass",
            "passed": True,
        },
        "redaction_verdict": {"verdict": "passed", "scanner": "test-secret-scanner"},
        "claim_ceiling": CLAIM_CEILING,
    }


class ImmutableEvidenceTests(unittest.TestCase):
    def test_contract_schemas_are_strict_draft_2020_12_documents(self) -> None:
        for relative, schema_identity in VALIDATOR.CONTRACT_SCHEMAS.items():
            payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertIs(payload["additionalProperties"], False)
            self.assertEqual(payload["properties"]["schema"]["const"], schema_identity)
            self.assertTrue(payload["required"])
        terminal_schema = json.loads(
            (
                ROOT
                / "packages/contracts/schemas/foundation-remediation-r1-terminal-receipt.v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(
            {
                "production_proving_receipt",
                "lifecycle_receipt",
                "task_id",
                "orchestrator_attempt_id",
                "artifact_sha256",
                "production_proof",
            }.issubset(terminal_schema["required"])
        )
        manifest_schema = json.loads(
            (
                ROOT
                / "packages/contracts/schemas/foundation-remediation-r1-immutable-evidence-manifest.v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(
            {"production_proving_receipt", "lifecycle_receipt"}.issubset(
                manifest_schema["required"]
            )
        )

    def test_evidence_set_hash_is_order_independent_and_path_bound(self) -> None:
        entries = [
            {"path": "docs/evidence/b.json", "sha256": "b" * 64},
            {"path": "docs/evidence/a.json", "sha256": "a" * 64},
        ]
        forward = GENERATOR.evidence_set_hash(entries)
        reverse = GENERATOR.evidence_set_hash(reversed(entries))
        changed_path = GENERATOR.evidence_set_hash(
            [{"path": "docs/evidence/c.json", "sha256": "a" * 64}, entries[0]]
        )
        self.assertEqual(forward, reverse)
        self.assertNotEqual(forward, changed_path)

    def test_profile_receipt_binds_exact_artifact_and_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = initialize_repository(root)
            artifact = root / "docs/evidence/profile-output.json"
            artifact.parent.mkdir(parents=True)
            execution = {
                "schema": GENERATOR.PROFILE_ARTIFACT_SCHEMA,
                "remediation_id": GENERATOR.REMEDIATION_ID,
                "profile_id": "typecheck",
                "command": "npm run typecheck",
                "source_commit": source,
                "started_at": "2026-07-17T19:59:00Z",
                "completed_at": "2026-07-17T20:00:00Z",
                "returncode": 0,
                "result": "pass",
                "passed": True,
                "stdout": "",
                "stderr": "",
                "claim_ceiling": "TypeScript static correctness only",
            }
            GENERATOR.write_json_atomic(artifact, execution)
            receipt = GENERATOR.build_profile_receipt(
                root,
                profile_id="typecheck",
                command="npm run typecheck",
                source_commit=source,
                artifact_path=artifact,
                claim_ceiling="TypeScript static correctness only",
                completed_at="2026-07-17T20:00:00Z",
            )
            self.assertEqual(receipt["source_commit"], source)
            self.assertEqual(receipt["artifact_path"], "docs/evidence/profile-output.json")
            self.assertEqual(receipt["artifact_sha256"], GENERATOR.sha256_file(artifact))
            self.assertTrue(receipt["passed"])

            execution.update({"returncode": 1, "result": "fail", "passed": False})
            GENERATOR.write_json_atomic(artifact, execution)
            with self.assertRaisesRegex(GENERATOR.EvidenceBuildError, "profile_execution_artifact_not_passed"):
                GENERATOR.build_profile_receipt(
                    root,
                    profile_id="typecheck",
                    command="npm run typecheck",
                    source_commit=source,
                    artifact_path=artifact,
                    claim_ceiling="TypeScript static correctness only",
                    completed_at="2026-07-17T20:00:00Z",
                )

    def test_protected_head_report_records_ref_tips_and_campaign_two_ancestry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "state.json"
            state.write_text(
                json.dumps({"protected_heads": GENERATOR.EXPECTED_PROTECTED_HEADS}),
                encoding="utf-8",
            )
            source = "f" * 40

            def fake_git(_root: Path, *args: str):
                completed = mock.Mock(returncode=0, stdout="", stderr="")
                if args[:2] == ("rev-parse", "--verify") and args[-1].endswith("^{commit}"):
                    completed.stdout = source + "\n"
                elif args[:2] == ("rev-parse", "--verify"):
                    ref = args[-1]
                    name = next(name for name, value in GENERATOR.PROTECTED_REFS.items() if value == ref)
                    completed.stdout = GENERATOR.EXPECTED_PROTECTED_REF_TIPS[name] + "\n"
                elif args == ("rev-parse", "HEAD"):
                    completed.stdout = source + "\n"
                return completed

            with mock.patch.object(GENERATOR, "run_git", side_effect=fake_git):
                report = GENERATOR.build_protected_head_report(
                    root,
                    source_commit=source,
                    state_path=state,
                    generated_at="2026-07-17T20:00:00Z",
                )
            self.assertTrue(report["passed"])
            campaign_two = next(
                entry for entry in report["entries"] if entry["name"] == "campaign_2_engineering_terminal"
            )
            self.assertEqual(campaign_two["protected_commit"], "2b8ead66578d7f7053c01cb987e011b763c1c03d")
            self.assertEqual(campaign_two["actual_tip"], "39de31bb73cb4a910281705259b35a6d42a0726c")
            self.assertTrue(campaign_two["protected_commit_in_ref_history"])

    def test_terminal_spec_binds_authority_validator_and_participant_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = initialize_repository(root)
            tag = "foundation-r1-test-terminal"
            authority = root / "docs/evidence-manifests/foundation-remediation-r1/authority-validation.json"
            authority.parent.mkdir(parents=True)
            authority.write_text('{"passed":true}\n', encoding="utf-8")
            payload = terminal_spec(root, source, tag, authority.relative_to(root).as_posix())
            GENERATOR.validate_terminal_spec(root, payload, source, tag)

            payload["authority_validation"]["validator_sha256"] = "f" * 64
            with self.assertRaisesRegex(
                GENERATOR.EvidenceBuildError,
                "terminal_spec_authority_validator_source_hash_mismatch",
            ):
                GENERATOR.validate_terminal_spec(root, payload, source, tag)

            payload = terminal_spec(root, source, tag, authority.relative_to(root).as_posix())
            payload["reviewer_result"]["invocation_id"] = "synthetic-reviewer-invocation"
            with self.assertRaisesRegex(
                GENERATOR.EvidenceBuildError,
                "terminal_spec_participant_result_invalid:reviewer",
            ):
                GENERATOR.validate_terminal_spec(root, payload, source, tag)

    def test_terminal_spec_requires_real_receipts_and_rejects_inner_self_hash_forgery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = initialize_repository(root)
            tag = "foundation-r1-test-terminal"
            authority = root / "docs/evidence-manifests/foundation-remediation-r1/authority-validation.json"
            authority.parent.mkdir(parents=True)
            authority.write_text('{"passed":true}\n', encoding="utf-8")
            payload = terminal_spec(root, source, tag, authority.relative_to(root).as_posix())
            payload.pop("production_proving_receipt")
            with self.assertRaisesRegex(
                GENERATOR.EvidenceBuildError,
                "terminal_spec_fields_missing:production_proving_receipt",
            ):
                GENERATOR.validate_terminal_spec(root, payload, source, tag)

            payload = terminal_spec(root, source, tag, authority.relative_to(root).as_posix())
            proving = root / payload["production_proving_receipt"]["path"]
            forged = json.loads(proving.read_text(encoding="utf-8"))
            forged["runs"][1]["task_id"] = "forged-task"
            GENERATOR.write_json_atomic(proving, forged)
            payload["production_proving_receipt"]["sha256"] = GENERATOR.sha256_file(proving)
            with self.assertRaisesRegex(
                GENERATOR.EvidenceBuildError,
                "production_proving_receipt_self_hash_mismatch",
            ):
                GENERATOR.validate_terminal_spec(root, payload, source, tag)

    def test_terminal_spec_rejects_outer_inner_mismatch_and_copied_terminal_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = initialize_repository(root)
            tag = "foundation-r1-test-terminal"
            authority = root / "docs/evidence-manifests/foundation-remediation-r1/authority-validation.json"
            authority.parent.mkdir(parents=True)
            authority.write_text('{"passed":true}\n', encoding="utf-8")
            payload = terminal_spec(root, source, tag, authority.relative_to(root).as_posix())
            lifecycle = root / payload["lifecycle_receipt"]["path"]
            forged = json.loads(lifecycle.read_text(encoding="utf-8"))
            forged["inner_proving"]["runs"][1]["task_id"] = "forged-embedded-task"
            forged.pop("receipt_sha256")
            forged["receipt_sha256"] = GENERATOR.compact_sha256(forged)
            GENERATOR.write_json_atomic(lifecycle, forged)
            payload["lifecycle_receipt"]["sha256"] = GENERATOR.sha256_file(lifecycle)
            with self.assertRaisesRegex(
                GENERATOR.EvidenceBuildError,
                "lifecycle_inner_proving_receipt_mismatch",
            ):
                GENERATOR.validate_terminal_spec(root, payload, source, tag)

            payload = terminal_spec(root, source, tag, authority.relative_to(root).as_posix())
            lifecycle = root / payload["lifecycle_receipt"]["path"]
            forged = json.loads(lifecycle.read_text(encoding="utf-8"))
            forged["teardown"]["all_service_ports_closed"] = False
            forged.pop("receipt_sha256")
            forged["receipt_sha256"] = GENERATOR.compact_sha256(forged)
            GENERATOR.write_json_atomic(lifecycle, forged)
            payload["lifecycle_receipt"]["sha256"] = GENERATOR.sha256_file(lifecycle)
            with self.assertRaisesRegex(
                GENERATOR.EvidenceBuildError,
                "lifecycle_teardown_invalid",
            ):
                GENERATOR.validate_terminal_spec(root, payload, source, tag)

            payload = terminal_spec(root, source, tag, authority.relative_to(root).as_posix())
            payload["task_id"] = "self-attested-terminal-task"
            with self.assertRaisesRegex(
                GENERATOR.EvidenceBuildError,
                "terminal_spec_proving_run_mismatch:task_id",
            ):
                GENERATOR.validate_terminal_spec(root, payload, source, tag)

    def test_validator_independently_recomputes_receipt_cross_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = initialize_repository(root)
            tag = "foundation-r1-test-terminal"
            authority = root / "docs/evidence-manifests/foundation-remediation-r1/authority-validation.json"
            authority.parent.mkdir(parents=True)
            authority.write_text('{"passed":true}\n', encoding="utf-8")
            payload = terminal_spec(root, source, tag, authority.relative_to(root).as_posix())
            receipt = GENERATOR.build_terminal_receipt(
                payload,
                evidence_hash="0" * 64,
                generated_at="2026-07-17T20:00:00+00:00",
            )
            VALIDATOR.validate_terminal_production_cross_binding(
                root,
                receipt,
                source_commit=source,
            )
            mutations = {
                "task": (("task_id",), "forged-task"),
                "run": (("orchestrator_run_id",), "forged-run"),
                "attempt": (("orchestrator_attempt_id",), "forged-attempt"),
                "participant": (
                    ("participants", "reviewer", "invocation_id"),
                    "forged-reviewer",
                ),
                "approval": (("approval", "approval_id"), "apr_forged"),
                "artifact": (("artifact_sha256",), "0" * 64),
                "diff": (("applied_diff_sha256",), "0" * 64),
                "result": (("result_sha256",), "0" * 64),
                "target": (("target",), "fixtures/forged/README.md"),
                "plugin": (("target_plugin_identity", "plugin_id"), "forged-plugin"),
                "prompt": (("prompt_identity", "id"), "forged-prompt"),
                "context": (("context_identity", "sha256"), "0" * 64),
                "recovery": (("production_proof", "recovery_id"), "forged-recovery"),
                "production-proof": (("production_proof", "proof_sha256"), "0" * 64),
                "claim": (("claim_ceiling",), "forged-claim-ceiling"),
            }
            for name, (path, replacement) in mutations.items():
                forged = json.loads(json.dumps(receipt))
                target = forged
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = replacement
                with self.subTest(binding=name), self.assertRaises(
                    VALIDATOR.EvidenceValidationError
                ):
                    VALIDATOR.validate_terminal_production_cross_binding(
                        root,
                        forged,
                        source_commit=source,
                    )

    def build_tagged_fixture(self, root: Path):
        source = initialize_repository(root)
        tag = "foundation-r1-test-terminal"
        evidence_dir = root / "docs/evidence-manifests/foundation-remediation-r1"
        evidence_dir.mkdir(parents=True)
        restoration = root / "docs/architecture/foundation-remediation-r1-restoration.md"
        restoration.parent.mkdir(parents=True)
        restoration.write_text("Restore from the verified bundle.\n", encoding="utf-8")
        authority = evidence_dir / "authority-validation.json"
        authority.write_text('{"passed":true}\n', encoding="utf-8")
        protected = evidence_dir / "protected-heads.json"
        GENERATOR.write_json_atomic(protected, protected_report(source))
        spec = evidence_dir / "terminal-spec.json"
        spec_payload = terminal_spec(root, source, tag, authority.relative_to(root).as_posix())
        proving = root / spec_payload["production_proving_receipt"]["path"]
        GENERATOR.write_json_atomic(spec, spec_payload)
        receipt_path = evidence_dir / "terminal-receipt.json"
        manifest_path = evidence_dir / "immutable-manifest.json"
        receipt, manifest = GENERATOR.build_terminal_evidence(
            root,
            spec_path=spec,
            artifact_paths=[authority],
            receipt_path=receipt_path,
            manifest_path=manifest_path,
            restoration_path=restoration,
            protected_report_path=protected,
            tag_name=tag,
            bundle_path="/tmp/foundation-r1-test.bundle",
            generated_at="2026-07-17T20:00:00Z",
        )
        git(root, "add", "docs")
        git(root, "commit", "-q", "-m", "closeout evidence")
        git(root, "tag", "-a", tag, "-m", "Foundation R1 test terminal")
        evidence = {
            "source_commit": source,
            "tag_name": tag,
            "bundle_path": "/tmp/foundation-r1-test.bundle",
            "restoration_instructions_path": restoration.relative_to(root).as_posix(),
            "receipt_sha256": GENERATOR.sha256_file(receipt_path),
        }
        return receipt, manifest, evidence, receipt_path, manifest_path, proving

    def test_manifest_validator_accepts_only_tag_bound_repository_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt, manifest, evidence, receipt_path, manifest_path, _ = self.build_tagged_fixture(root)
            failures: list[str] = []
            VALIDATOR.validate_manifest(
                root,
                manifest,
                evidence,
                receipt,
                receipt_path,
                manifest_path,
                failures,
            )
            self.assertEqual(failures, [])

    def test_manifest_requires_both_receipts_as_named_tagged_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt, manifest, evidence, receipt_path, manifest_path, _ = self.build_tagged_fixture(root)
            missing_named = json.loads(json.dumps(manifest))
            missing_named.pop("lifecycle_receipt")
            failures: list[str] = []
            VALIDATOR.validate_manifest(
                root,
                missing_named,
                evidence,
                receipt,
                receipt_path,
                manifest_path,
                failures,
            )
            self.assertIn("manifest_fields_missing:lifecycle_receipt", failures)
            self.assertIn("manifest_lifecycle_receipt_missing", failures)

            missing_artifact = json.loads(json.dumps(manifest))
            lifecycle_path = receipt["lifecycle_receipt"]["path"]
            missing_artifact["artifacts"] = [
                item for item in missing_artifact["artifacts"] if item["path"] != lifecycle_path
            ]
            new_hash = GENERATOR.evidence_set_hash(missing_artifact["artifacts"])
            missing_artifact["evidence_hash"] = new_hash
            forged_receipt = json.loads(json.dumps(receipt))
            forged_receipt["evidence_hash"] = new_hash
            failures = []
            VALIDATOR.validate_manifest(
                root,
                missing_artifact,
                evidence,
                forged_receipt,
                receipt_path,
                manifest_path,
                failures,
            )
            self.assertIn("manifest_lifecycle_receipt_artifact_missing", failures)

    def test_manifest_validator_rejects_current_bytes_not_present_in_terminal_tag(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt, manifest, evidence, receipt_path, manifest_path, proving = self.build_tagged_fixture(root)
            proving.write_text('{"passed":true,"tampered":true}\n', encoding="utf-8")
            relative = proving.relative_to(root).as_posix()
            for entry in manifest["artifacts"]:
                if entry["path"] == relative:
                    entry["sha256"] = GENERATOR.sha256_file(proving)
                    entry["size_bytes"] = proving.stat().st_size
            new_hash = GENERATOR.evidence_set_hash(manifest["artifacts"])
            manifest["evidence_hash"] = new_hash
            receipt["evidence_hash"] = new_hash
            failures: list[str] = []
            VALIDATOR.validate_manifest(
                root,
                manifest,
                evidence,
                receipt,
                receipt_path,
                manifest_path,
                failures,
            )
            self.assertTrue(
                any(item == f"manifest_artifact_not_bound_to_terminal_tag:{relative}" for item in failures),
                failures,
            )

    def test_manifest_validator_rejects_mutated_restoration_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt, manifest, evidence, receipt_path, manifest_path, _ = self.build_tagged_fixture(root)
            restoration = root / evidence["restoration_instructions_path"]
            restoration.write_text("Restore from an unverified location.\n", encoding="utf-8")
            relative = restoration.relative_to(root).as_posix()
            digest = GENERATOR.sha256_file(restoration)
            manifest["restoration_instructions"]["sha256"] = digest
            for entry in manifest["artifacts"]:
                if entry["path"] == relative:
                    entry["sha256"] = digest
                    entry["size_bytes"] = restoration.stat().st_size
            new_hash = GENERATOR.evidence_set_hash(manifest["artifacts"])
            manifest["evidence_hash"] = new_hash
            receipt["evidence_hash"] = new_hash
            failures: list[str] = []
            VALIDATOR.validate_manifest(
                root,
                manifest,
                evidence,
                receipt,
                receipt_path,
                manifest_path,
                failures,
            )
            self.assertIn(f"manifest_restoration_not_bound_to_terminal_tag:{relative}", failures)
            self.assertIn(f"manifest_artifact_not_bound_to_terminal_tag:{relative}", failures)

    def test_manifest_validator_rejects_untracked_and_unanchored_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt, manifest, evidence, receipt_path, manifest_path, _ = self.build_tagged_fixture(root)
            untracked = root / "docs/evidence-manifests/foundation-remediation-r1/untracked.json"
            untracked.write_text("{}\n", encoding="utf-8")
            manifest["artifacts"].append(GENERATOR.artifact_entry(root, untracked))
            new_hash = GENERATOR.evidence_set_hash(manifest["artifacts"])
            manifest["evidence_hash"] = new_hash
            receipt["evidence_hash"] = new_hash
            failures: list[str] = []
            VALIDATOR.validate_manifest(
                root,
                manifest,
                evidence,
                receipt,
                receipt_path,
                manifest_path,
                failures,
            )
            relative = untracked.relative_to(root).as_posix()
            self.assertIn(f"manifest_artifact_untracked:{relative}", failures)
            self.assertIn(f"manifest_artifact_not_bound_to_terminal_tag:{relative}", failures)


if __name__ == "__main__":
    unittest.main()
