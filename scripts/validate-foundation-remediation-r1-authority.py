#!/usr/bin/env python3
"""Static falsification checks for the R1 production authority graph.

The validator has a deliberately narrow claim ceiling: it proves that required
production imports and invariant-bearing calls exist and that known bypasses do
not. Runtime profiles and the terminal receipt must still prove execution.
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
from collections import deque
from pathlib import Path
from typing import Iterable


CANONICAL_ORCHESTRATOR = "source_proxy.coding.orchestrator"
LIVE_API_MODULE = "source_proxy.api.long_running_tasks"
DIRECT_EXECUTOR = "execute_approved_long_running_task"
HARDCODED_CAMPAIGN_ROOT = re.compile(r"/home/source/SpiritOS-campaign-[^\"'\s]+")
MUTATING_PATH_CALLS = {
    "mkdir",
    "open",
    "rename",
    "replace",
    "rmdir",
    "touch",
    "unlink",
    "write_bytes",
    "write_text",
}
PARTICIPANT_IMPORT_TERMS = {
    "reviewer": ("reviewer",),
    "verifier": ("verifier",),
    "anti_cheat": ("anticheat", "anti_cheat"),
    "evidence": ("evidence",),
}
PARTICIPANT_ROLE_MARKERS = {
    "coding-executor:coder",
    "coding-reviewer",
    "coding-verifier",
    "coding-anti-cheat",
    "evidence-recorder",
}
STATE_RELATIVE = "docs/architecture/foundation-remediation-r1-state.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def terminal_candidate(state: dict[str, object]) -> bool:
    closeout = state.get("closeout")
    return bool(
        state.get("go_eligible") is True
        or "r1_complete" in (state.get("completed_gate_ids") or [])
        or (isinstance(closeout, dict) and closeout.get("status") == "complete")
    )


def terminal_authority_source(root: Path, failures: list[str]) -> tuple[bool, str | None]:
    try:
        state = json.loads((root / STATE_RELATIVE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"authority_state_unreadable_or_malformed:{error}")
        return False, None
    if not isinstance(state, dict):
        failures.append("authority_state_not_object")
        return False, None
    candidate = terminal_candidate(state)
    if not candidate:
        return False, None

    status = run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status.returncode != 0:
        failures.append("terminal_worktree_status_unreadable")
    elif status.stdout:
        failures.append("terminal_worktree_not_globally_clean")
    evidence = state.get("terminal_evidence")
    if not isinstance(evidence, dict):
        failures.append("terminal_authority_evidence_missing")
        return True, None
    source = evidence.get("source_commit")
    tag = evidence.get("tag_name")
    if not isinstance(source, str) or not HEX40.fullmatch(source):
        failures.append("terminal_authority_source_commit_invalid")
        return True, None
    if not isinstance(tag, str) or not tag:
        failures.append("terminal_authority_tag_name_invalid")
        return True, None
    if run_git(root, "cat-file", "-e", f"{source}^{{commit}}").returncode != 0:
        failures.append("terminal_authority_source_commit_unreadable")
        return True, None
    tag_type = run_git(root, "cat-file", "-t", f"refs/tags/{tag}")
    if tag_type.returncode != 0 or tag_type.stdout.strip() != "tag":
        failures.append("terminal_authority_tag_not_annotated")
        return True, None
    target = run_git(root, "rev-parse", f"refs/tags/{tag}^{{}}")
    head = run_git(root, "rev-parse", "HEAD")
    if target.returncode != 0 or head.returncode != 0 or target.stdout.strip() != head.stdout.strip():
        failures.append("terminal_authority_tag_target_mismatch")
        return True, None
    target_commit = target.stdout.strip()
    if source == target_commit or run_git(
        root, "merge-base", "--is-ancestor", source, target_commit
    ).returncode != 0:
        failures.append("terminal_authority_source_not_precloseout_ancestor")
        return True, None
    authority_diff = run_git(
        root,
        "diff",
        "--quiet",
        source,
        target_commit,
        "--",
        "source_proxy",
        "scripts/approval-authority.py",
        "src/app/v1/actions/execute-approved/route.ts",
        "src/app/v1/coding/dummy-product-site-preview/reset/route.ts",
        "src/components/coding/CodingCockpitShell.tsx",
        "src/lib/coding",
    )
    if authority_diff.returncode != 0:
        failures.append("terminal_authority_source_tag_tree_mismatch")
        return True, None
    return True, source


def extract_authority_source(
    root: Path,
    source: str,
    destination: Path,
    failures: list[str],
) -> bool:
    archived = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "archive",
            "--format=tar",
            source,
            "--",
            "source_proxy",
            "scripts/approval-authority.py",
            "src/app/v1/actions/execute-approved/route.ts",
            "src/app/v1/coding/dummy-product-site-preview/reset/route.ts",
            "src/components/coding/CodingCockpitShell.tsx",
            "src/lib/coding",
        ],
        capture_output=True,
        check=False,
    )
    if archived.returncode != 0:
        failures.append("terminal_authority_source_archive_failed")
        return False
    try:
        with tarfile.open(fileobj=io.BytesIO(archived.stdout), mode="r:") as archive:
            for member in archive.getmembers():
                target = (destination / member.name).resolve()
                try:
                    target.relative_to(destination.resolve())
                except ValueError:
                    failures.append("terminal_authority_source_archive_unsafe")
                    return False
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    extracted = archive.extractfile(member)
                    if extracted is None:
                        failures.append("terminal_authority_source_archive_unreadable")
                        return False
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(extracted.read())
    except (OSError, tarfile.TarError) as error:
        failures.append(f"terminal_authority_source_archive_invalid:{error}")
        return False
    return True


def production_python_files(root: Path) -> Iterable[Path]:
    for path in (root / "source_proxy").rglob("*.py"):
        relative = path.relative_to(root)
        if "tests" in relative.parts or path.name.startswith("test_"):
            continue
        yield path


def module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root).with_suffix("")
    return ".".join(relative.parts)


def parse_python(path: Path, failures: list[str]) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except (OSError, SyntaxError) as error:
        failures.append(f"python_parse_failed:{path}:{error}")
        return None


def import_modules(tree: ast.Module) -> set[str]:
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def import_symbols(tree: ast.Module) -> dict[str, str]:
    imported: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported[alias.asname or alias.name.split(".")[-1]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imported[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return imported


def call_name(node: ast.Call) -> str:
    target = node.func
    parts: list[str] = []
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts))


def reachable(graph: dict[str, set[str]], start: str, target: str) -> bool:
    queue = deque([start])
    seen: set[str] = set()
    while queue:
        item = queue.popleft()
        if item in seen:
            continue
        seen.add(item)
        if item == target:
            return True
        queue.extend(graph.get(item, set()) - seen)
    return False


def literal_dict_keys(node: ast.Dict) -> set[str]:
    return {
        key.value
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


def synthesized_acknowledgement_failures(root: Path, failures: list[str]) -> None:
    path = root / "source_proxy/tasks/long_running.py"
    tree = parse_python(path, failures)
    if tree is None:
        return
    required_provenance = {"invocation_id", "output_id", "consumer_acknowledgement_id", "artifact_sha256"}
    for node in ast.walk(tree):
        if isinstance(node, ast.DictComp):
            value_keys = literal_dict_keys(node.value) if isinstance(node.value, ast.Dict) else set()
            if {"approval_id", "generation", "target_plugin_identity"}.issubset(value_keys):
                failures.append("synthesized_participant_acknowledgement_comprehension")
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if not isinstance(key, ast.Constant) or key.value != "acknowledgements":
                continue
            if isinstance(value, ast.DictComp):
                failures.append("synthesized_participant_acknowledgements")
                continue
            if not isinstance(value, ast.Dict):
                continue
            for consumer_key, acknowledgement in zip(value.keys, value.values):
                if not (
                    isinstance(consumer_key, ast.Constant)
                    and isinstance(consumer_key.value, str)
                    and consumer_key.value.startswith("coding-")
                    and isinstance(acknowledgement, ast.Dict)
                ):
                    continue
                missing = required_provenance - literal_dict_keys(acknowledgement)
                if missing:
                    failures.append(
                        "participant_acknowledgement_provenance_missing:"
                        f"{consumer_key.value}:{','.join(sorted(missing))}"
                    )


def premature_success_finalization_failures(root: Path, failures: list[str]) -> None:
    path = root / "source_proxy/tasks/long_running.py"
    tree = parse_python(path, failures)
    if tree is None:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not call_name(node).endswith("finalize_coding_execution_approval"):
            continue
        for keyword in node.keywords:
            if (
                keyword.arg == "status"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == "succeeded"
            ):
                failures.append("coding_success_finalized_outside_orchestrator")


def cartographer_writer_failures(root: Path, failures: list[str]) -> None:
    path = root / "source_proxy/cartographer/proposal_reviews.py"
    tree = parse_python(path, failures)
    if tree is None:
        return
    mutations = sorted(
        {
            call_name(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and call_name(node).split(".")[-1] in MUTATING_PATH_CALLS
        }
    )
    if mutations:
        failures.append("cartographer_proposal_review_filesystem_writer:" + ",".join(mutations))
    api_path = root / "source_proxy/api/cartographer.py"
    if api_path.is_file() and "review_blueprint_proposal" in api_path.read_text(encoding="utf-8"):
        failures.append("cartographer_api_calls_direct_review_writer")


def cartographer_selection_invariant_failures(
    root: Path, failures: list[str]
) -> None:
    path = root / "source_proxy/cartographer/cartographer_selection_authority.py"
    if not path.is_file():
        failures.append("cartographer_selection_authority_missing")
        return
    text = path.read_text(encoding="utf-8")
    for marker in (
        "proposal.persisted is not True",
        "proposal.status not in",
        "proposal.warnings",
        "target not in proposed_files",
        "cartographer_selection_target_not_proposed",
        "cartographer.downstream-acknowledgement/v2",
        "consumer_output_id",
        "consumer_output_sha256",
        "consumer_artifact_sha256",
        "consumer_completed_at",
    ):
        if marker not in text:
            failures.append(f"cartographer_selection_invariant_missing:{marker}")
    orchestrator_path = root / "source_proxy/coding/orchestrator.py"
    orchestrator_tree = parse_python(orchestrator_path, failures)
    if orchestrator_tree is None:
        return
    definitions = {
        node.name: node
        for node in ast.walk(orchestrator_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for function_name in ("propose_target_plugin", "execute_approved"):
        function = definitions.get(function_name)
        if function is None:
            failures.append(f"cartographer_downstream_function_missing:{function_name}")
            continue
        calls = [
            (node.lineno, call_name(node))
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
        ]
        producer_lines = [
            line
            for line, name in calls
            if name in {"execute_target_plugin_command", "self._call_executor"}
        ]
        finalizer_lines = [
            line
            for line, name in calls
            if name == "self._finalize_cartographer_transfer_after_invocation"
        ]
        if finalizer_lines and (
            not producer_lines
            or any(not any(producer < finalizer for producer in producer_lines) for finalizer in finalizer_lines)
        ):
            failures.append(
                f"cartographer_selection_finalized_before_downstream_output:{function_name}"
            )


def cartographer_proposal_review_invariant_failures(
    root: Path, failures: list[str]
) -> None:
    path = root / "source_proxy/cartographer/proposal_review_authority.py"
    tree = parse_python(path, failures)
    if tree is None:
        return
    source = path.read_text(encoding="utf-8")
    definitions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for function_name in ("_build_review_plan", "_result_payload"):
        function = definitions.get(function_name)
        if function is None:
            failures.append(f"cartographer_review_plan_function_missing:{function_name}")
            continue
        segment = ast.get_source_segment(source, function) or ""
        if "participant_requirements" not in segment:
            failures.append(
                f"cartographer_review_participant_requirements_missing:{function_name}"
            )
        for forbidden in (
            '"invocation_id"',
            '"output_id"',
            '"consumer_acknowledgement_id"',
            '"invocations"',
            '"passed"',
            '"succeeded"',
        ):
            if forbidden in segment:
                failures.append(
                    f"cartographer_review_plan_presynthesizes_runtime_state:{function_name}:{forbidden}"
                )
    for marker in (
        '"schema_version": "cartographer.participant-invocation/v2"',
        "def _acknowledge_invocation(",
        '"schema_version": "cartographer.participant-acknowledgement/v1"',
        'acknowledgement.get("output_sha256") != record.get("output_sha256")',
    ):
        if marker not in source:
            failures.append(f"cartographer_review_runtime_proof_missing:{marker}")


def reset_source_baseline_invariant_failures(
    root: Path, failures: list[str]
) -> None:
    path = root / "source_proxy/api/codex_adapter.py"
    if not path.is_file():
        failures.append("dummy_product_reset_authority_missing")
        return
    text = path.read_text(encoding="utf-8")
    for marker in (
        "_source_head_fixture_baseline",
        '"ls-tree"',
        "reset_source_baseline_not_empty",
        '"source_baseline_verified": True',
        'target_plugin_identity.get("source_head")',
        "verify_operator_approval_assertion",
        "DUMMY_PRODUCT_SITE_RESET_ASSERTION_PREVIEW",
    ):
        if marker not in text:
            failures.append(f"dummy_product_reset_baseline_invariant_missing:{marker}")
    next_path = root / "src/app/v1/coding/dummy-product-site-preview/reset/route.ts"
    if not next_path.is_file():
        failures.append("dummy_product_reset_next_authority_missing")
        return
    next_text = next_path.read_text(encoding="utf-8")
    for marker in (
        "requireOperatorSession(request)",
        "createOperatorApprovalAssertion",
        '"x-spiritos-operator-assertion"',
        "auditOperatorAction",
    ):
        if marker not in next_text:
            failures.append(f"dummy_product_reset_next_invariant_missing:{marker}")


def production_debug_isolation_failures(root: Path, failures: list[str]) -> None:
    """Reject request-bearing ad-hoc debug sinks in the live decision route."""

    path = root / "source_proxy/api/decision.py"
    if not path.is_file():
        failures.append("production_decision_route_missing")
        return
    text = path.read_text(encoding="utf-8")
    for marker in (
        "_agent_debug_log",
        "/home/source/SpiritOS/.cursor/",
        "debug-9460b9.log",
    ):
        if marker in text:
            failures.append(f"production_request_debug_sink_present:{marker}")


def approval_finalization_reconciliation_failures(
    root: Path, failures: list[str]
) -> None:
    orchestrator_path = root / "source_proxy/coding/orchestrator.py"
    authority_path = root / "scripts/approval-authority.py"
    tasks_path = root / "source_proxy/tasks/long_running.py"
    required = {
        orchestrator_path: (
            "coding.authority-finalization-outbox/v1",
            "pending_authority_commit",
            "authority_committed_local_pending",
            "_resume_authority_finalization",
            "evidence_sha256",
        ),
        authority_path: (
            'row["result_id"] != result_id',
            'row["evidence"] != evidence',
            '"idempotent": True',
        ),
        tasks_path: (
            "coding_finalization_replay_mismatch",
            'normalized["authority_finalization"] = None',
            "exact_replay",
        ),
    }
    for path, markers in required.items():
        if not path.is_file():
            failures.append(f"approval_finalization_reconciliation_file_missing:{path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                failures.append(
                    f"approval_finalization_reconciliation_missing:{path.name}:{marker}"
                )


def terminal_projection_invariant_failures(root: Path, failures: list[str]) -> None:
    next_path = root / "src/lib/coding/durable-run-store.ts"
    task_path = root / "source_proxy/tasks/long_running.py"
    if not next_path.is_file():
        failures.append("next_coding_projection_missing")
    else:
        text = next_path.read_text(encoding="utf-8")
        for marker in (
            "coding.production-proof/v1",
            "terminal_proof_eligible",
            "production_proof_sha256",
            "terminal_production_proof_invalid",
            "sha256Json(proofBody)",
        ):
            if marker not in text:
                failures.append(f"next_terminal_projection_invariant_missing:{marker}")
    if not task_path.is_file():
        failures.append("source_coding_task_authority_missing")
    else:
        text = task_path.read_text(encoding="utf-8")
        for marker in (
            '"GO" if terminal_proof_eligible else "VERIFIED_NONTERMINAL"',
            '"verified_nonterminal_production_proof"',
            'production_proof.get("terminal_proof_eligible") is True',
        ):
            if marker not in text:
                failures.append(f"source_terminal_truth_invariant_missing:{marker}")


def hardcoded_root_failures(root: Path, failures: list[str]) -> None:
    candidates = [
        root / "scripts/approval-authority.py",
        root / "source_proxy/approval/campaign_authority.py",
        root / "source_proxy/target_plugins/adapter.py",
    ]
    candidates.extend((root / "src/lib/coding").glob("*authority*.ts"))
    for path in candidates:
        if not path.is_file():
            failures.append(f"authority_file_missing:{path.relative_to(root)}")
            continue
        match = HARDCODED_CAMPAIGN_ROOT.search(path.read_text(encoding="utf-8"))
        if match:
            failures.append(f"hardcoded_campaign_root:{path.relative_to(root)}:{match.group(0)}")


def orchestrator_invariant_failures(root: Path, failures: list[str]) -> None:
    path = root / "source_proxy/coding/orchestrator.py"
    tree = parse_python(path, failures)
    if tree is None:
        return
    text = path.read_text(encoding="utf-8")
    imports = import_symbols(tree)
    calls = {call_name(node) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    resolved_calls = {
        imports.get(name.split(".")[0], name)
        for name in calls
    }

    contract_call = any(
        "contract" in name.lower() and ("validate" in name.lower() or "enforce" in name.lower())
        for name in resolved_calls
    )
    if not contract_call:
        failures.append("runtime_contract_enforcement_call_missing")
    for marker in (
        "contract_version",
        "producer",
        "consumer",
        "output_id",
        "consumer_acknowledgement_id",
        "artifact_sha256",
    ):
        if marker not in text:
            failures.append(f"runtime_contract_invariant_missing:{marker}")

    for role in sorted(PARTICIPANT_ROLE_MARKERS):
        if role not in text:
            failures.append(f"participant_role_missing:{role}")
    for field in ("invocation_id", "output_id", "consumer_acknowledgement_id", "artifact_sha256"):
        if field not in text:
            failures.append(f"participant_event_field_missing:{field}")

    imported_and_called = "\n".join(sorted(set(imports.values()) | resolved_calls))
    for role, terms in PARTICIPANT_IMPORT_TERMS.items():
        if not any(term in imported_and_called.lower() for term in terms):
            failures.append(f"independent_participant_invocation_missing:{role}")

    evidence_path = root / "source_proxy/approval/campaign_evidence.py"
    evidence_text = evidence_path.read_text(encoding="utf-8") if evidence_path.is_file() else ""
    for field in ("invocation_id", "output_id", "consumer_acknowledgement_id", "artifact_sha256"):
        if field not in evidence_text:
            failures.append(f"participant_evidence_validator_missing:{field}")
    participant_path = root / "source_proxy/coding/participants.py"
    participant_text = (
        participant_path.read_text(encoding="utf-8") if participant_path.is_file() else ""
    )
    for marker in (
        "coding.participant-output/v2",
        "coding.participant-invocation/v2",
        "coding.participant-acknowledgement/v2",
        "dedicated_participant_subprocess",
        "_invoke_worker_process",
        "expected_executable_sha256",
        "expected_entrypoint_sha256",
        "acknowledge_coding_participant_output",
    ):
        if marker not in participant_text:
            failures.append(f"independent_participant_process_boundary_missing:{marker}")
    for marker in (
        "approval_acknowledgement_not_participant_owned",
        'record.get("consumer_acknowledgement") != acknowledgement',
    ):
        if marker not in evidence_text:
            failures.append(f"participant_acknowledgement_ownership_missing:{marker}")


def c1_participant_acknowledgement_failures(root: Path, failures: list[str]) -> None:
    paths = {
        root / "src/lib/coding/design-studio-approved-writeback-runtime.ts": (
            "acknowledgeDesignParticipantOutput",
            "evidenceOutput.invocation_id",
            "design-authority-finalizer-",
        ),
        root / "src/lib/coding/design-approval-authority.ts": (
            "design_participant_acknowledgement_invalid",
            "record.acknowledgement.output_hash !== record.output_hash",
            "record.acknowledgement.producer_invocation_id !== record.invocation_id",
        ),
        root / "src/lib/coding/spiritflix-admin-transaction.ts": (
            "acknowledgeInvocation",
            "spiritflix-admin-participant-output/v2",
            "recorderInvocationId",
            "spiritflix-authority-finalizer-",
        ),
        root / "src/lib/coding/spiritflix-admin-approval-authority.ts": (
            "spiritflix_admin_participant_evidence_mismatch",
            "item.acknowledgement.output_hash !== item.output_hash",
            "spiritflix_admin_participant_evidence_missing",
        ),
    }
    for path, markers in paths.items():
        if not path.is_file():
            failures.append(f"c1_participant_authority_file_missing:{path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                failures.append(
                    f"c1_participant_acknowledgement_boundary_missing:{path.name}:{marker}"
                )


def production_prompt_packet_authority_failures(
    root: Path, failures: list[str]
) -> None:
    """Keep the active LumaCart HTTP path and its UI identities fail closed."""

    decision_path = root / "source_proxy/api/decision.py"
    decision_tree = parse_python(decision_path, failures)
    if decision_tree is None:
        return
    imports = import_symbols(decision_tree)
    if imports.get("get_coding_orchestrator") != (
        "source_proxy.coding.orchestrator.get_coding_orchestrator"
    ):
        failures.append("prompt_packet_canonical_orchestrator_import_missing")
    decision_calls = {
        call_name(node) for node in ast.walk(decision_tree) if isinstance(node, ast.Call)
    }
    if any(name.endswith("advance_long_running_task") for name in decision_calls):
        failures.append("production_decision_direct_task_advance_bypass")

    definitions = {
        node.name: node
        for node in decision_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    helper = definitions.get("_run_production_target_plugin_proposal")
    architect_helper = definitions.get("_load_or_prepare_architect_plan")
    prompt_packet = definitions.get("prompt_packet")
    if helper is None:
        failures.append("prompt_packet_production_orchestrator_helper_missing")
    else:
        helper_calls = {
            call_name(node)
            for node in ast.walk(helper)
            if isinstance(node, ast.Call)
        }
        if "get_coding_orchestrator" not in helper_calls:
            failures.append("prompt_packet_get_coding_orchestrator_call_missing")
        for required_call in (
            "orchestrator.advance",
            "orchestrator.acknowledge_planner",
            "orchestrator.propose_target_plugin",
        ):
            if required_call not in helper_calls:
                failures.append(
                    f"prompt_packet_production_orchestrator_call_missing:{required_call}"
                )
    if architect_helper is None:
        failures.append("prompt_packet_architect_plan_helper_missing")
    else:
        architect_source = ast.get_source_segment(
            decision_path.read_text(encoding="utf-8"), architect_helper
        ) or ""
        if "get_coding_orchestrator().advance(task_id)" not in architect_source:
            failures.append("prompt_packet_architect_plan_canonical_advance_missing")

    if prompt_packet is None:
        failures.append("production_prompt_packet_handler_missing")
    else:
        prompt_names = {
            node.id for node in ast.walk(prompt_packet) if isinstance(node, ast.Name)
        }
        if "_run_production_target_plugin_proposal" not in prompt_names:
            failures.append("active_prompt_packet_orchestrator_entry_missing")
        prompt_source = ast.get_source_segment(
            decision_path.read_text(encoding="utf-8"), prompt_packet
        ) or ""
        for marker in (
            "reset_request.active_task_id",
            "is_lumacart_prompt_id(selected_prompt)",
            '"coding_orchestrator"',
            '"target_plugin_proposal"',
            '"runtime_output_id"',
            '"context_hash"',
        ):
            if marker not in prompt_source:
                failures.append(f"active_prompt_packet_binding_missing:{marker}")

    cockpit_path = root / "src/components/coding/CodingCockpitShell.tsx"
    if not cockpit_path.is_file():
        failures.append("coding_cockpit_authority_wiring_missing")
    else:
        cockpit = cockpit_path.read_text(encoding="utf-8")
        for marker in (
            "record.target_plugin_output_id",
            "record.runtime_output_id",
            "record.target_plugin_context_hash",
            "record.context_hash",
            "target_plugin_orchestrator_proposal_identity_missing",
        ):
            if marker not in cockpit:
                failures.append(f"coding_cockpit_proposal_identity_missing:{marker}")

        approval_start = cockpit.find("/approval-preview")
        approval_segment = (
            cockpit[approval_start : approval_start + 2500]
            if approval_start >= 0
            else ""
        )
        for marker in (
            "context_hash: contextHash",
            "runtime_output_id: targetPluginRuntimeOutputId",
        ):
            if marker not in approval_segment:
                failures.append(f"coding_cockpit_approval_identity_missing:{marker}")

        apply_start = cockpit.find(
            'fetchWithTimeout("/v1/actions/execute-approved"', approval_start
        )
        apply_segment = (
            cockpit[apply_start : apply_start + 2000] if apply_start >= 0 else ""
        )
        for marker in (
            "context_hash: contextHash",
            "runtime_output_id: targetPluginRuntimeOutputId",
        ):
            if marker not in apply_segment:
                failures.append(f"coding_cockpit_execute_identity_missing:{marker}")

    next_path = root / "src/app/v1/actions/execute-approved/route.ts"
    if not next_path.is_file():
        failures.append("next_execute_approved_authority_wiring_missing")
    else:
        next_text = next_path.read_text(encoding="utf-8")
        for marker in (
            "record.runtime_output_id",
            "record.context_hash",
            "target_plugin_orchestrator_proposal_identity_missing",
            "context_hash: contextHash",
            "runtime_output_id: runtimeOutputId",
        ):
            if marker not in next_text:
                failures.append(f"next_execute_approved_identity_missing:{marker}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("SPIRITOS_FOUNDATION_R1_ROOT", Path(__file__).resolve().parents[1])),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    failures: list[str] = []

    candidate, source = terminal_authority_source(root, failures)
    temporary: tempfile.TemporaryDirectory[str] | None = None
    scan_root = root
    if candidate:
        if source is None:
            scan_root = Path("/__invalid_terminal_authority_source__")
        else:
            temporary = tempfile.TemporaryDirectory(prefix="spiritos-r1-authority-")
            snapshot = Path(temporary.name).resolve()
            if extract_authority_source(root, source, snapshot, failures):
                scan_root = snapshot
            else:
                scan_root = Path("/__invalid_terminal_authority_source__")

    trees: dict[str, ast.Module] = {}
    graph: dict[str, set[str]] = {}
    for path in production_python_files(scan_root):
        tree = parse_python(path, failures)
        if tree is None:
            continue
        module = module_name(scan_root, path)
        trees[module] = tree
        graph[module] = import_modules(tree)

    if LIVE_API_MODULE not in trees:
        failures.append("production_long_running_api_missing")
    if CANONICAL_ORCHESTRATOR not in trees:
        failures.append("canonical_orchestrator_module_missing")
    if not reachable(graph, LIVE_API_MODULE, CANONICAL_ORCHESTRATOR):
        failures.append("canonical_orchestrator_not_reachable_from_live_api")
    production_importers = sorted(
        module for module, imports in graph.items() if CANONICAL_ORCHESTRATOR in imports
    )
    if not production_importers:
        failures.append("canonical_orchestrator_has_no_production_importer")

    for module, tree in trees.items():
        if module == CANONICAL_ORCHESTRATOR:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module != "source_proxy.tasks.long_running":
                continue
            if any(alias.name == DIRECT_EXECUTOR for alias in node.names):
                failures.append(f"production_executor_bypass_import:{module}")

    hardcoded_root_failures(scan_root, failures)
    cartographer_writer_failures(scan_root, failures)
    cartographer_selection_invariant_failures(scan_root, failures)
    cartographer_proposal_review_invariant_failures(scan_root, failures)
    reset_source_baseline_invariant_failures(scan_root, failures)
    production_debug_isolation_failures(scan_root, failures)
    approval_finalization_reconciliation_failures(scan_root, failures)
    terminal_projection_invariant_failures(scan_root, failures)
    premature_success_finalization_failures(scan_root, failures)
    synthesized_acknowledgement_failures(scan_root, failures)
    orchestrator_invariant_failures(scan_root, failures)
    c1_participant_acknowledgement_failures(scan_root, failures)
    production_prompt_packet_authority_failures(scan_root, failures)

    if temporary is not None:
        temporary.cleanup()

    if failures:
        print("FOUNDATION_REMEDIATION_R1_AUTHORITY_INVALID")
        print("\n".join(sorted(set(failures))))
        return 1
    print("FOUNDATION_REMEDIATION_R1_AUTHORITY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
