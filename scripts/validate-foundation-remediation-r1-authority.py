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
    premature_success_finalization_failures(scan_root, failures)
    synthesized_acknowledgement_failures(scan_root, failures)
    orchestrator_invariant_failures(scan_root, failures)

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
