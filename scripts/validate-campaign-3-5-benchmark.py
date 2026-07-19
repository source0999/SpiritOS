#!/usr/bin/env python3
"""Read-only static validator for the immutable Campaign 3.5 benchmark import."""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "benchmarks" / "coder-backend-100" / "v1.1"
ARCHIVE = ROOT / "benchmarks" / "coder-backend-100" / "imports" / "source_proxy_coder_backend_100_v1.1.zip"
EXPECTED_ARCHIVE_HASH = "a1c7e98c0ff5cf85ad829350fac08a59e695a1101979b37eefdd02a61a531818"
EXPECTED_FILES = {
    "README.md", "fixture-blueprints.md", "harness-spec.md", "manifest.json",
    "oracle-contract.md", "task.schema.json", "tasks.json", "tasks.jsonl",
    "tasks.md", "validation-report.json", "_build_v1_1.py",
}
CALIBRATION_IDS = {"M15", "R10", "E01", "E06"}


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    results: dict[str, object] = {}
    if sha256(ARCHIVE) != EXPECTED_ARCHIVE_HASH:
        fail(errors, "archive SHA-256 mismatch")
    results["archive_sha256"] = sha256(ARCHIVE)

    with zipfile.ZipFile(ARCHIVE) as archive:
        if archive.testzip() is not None:
            fail(errors, "ZIP CRC/integrity failure")
        names = [entry.filename for entry in archive.infolist()]
        for info in archive.infolist():
            name = info.filename
            mode = (info.external_attr >> 16) & 0o170000
            if name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", name):
                fail(errors, f"absolute archive path: {name}")
            if ".." in Path(name).parts:
                fail(errors, f"traversal archive path: {name}")
            if mode == 0o120000:
                fail(errors, f"symlink archive entry: {name}")
            if (info.external_attr >> 16) & 0o111:
                fail(errors, f"unexpected executable archive entry: {name}")
            if not name.startswith("source_proxy_coder_backend_100_v1_1/"):
                fail(errors, f"unexpected archive root: {name}")
        results["zip_integrity"] = "passed" if not errors else "failed"
        results["archive_entries"] = len(names)

    extracted = {path.name for path in PACK.iterdir() if path.is_file()}
    if extracted != EXPECTED_FILES | {"file-hashes.json", "provenance.json", "core-30-selection.json", "trace-event-contract-map.json"}:
        fail(errors, f"unexpected extracted file set: {sorted(extracted)}")
    hash_manifest = json.loads((PACK / "file-hashes.json").read_text(encoding="utf-8"))
    for name, expected_hash in hash_manifest["files"].items():
        if sha256(PACK / name) != expected_hash:
            fail(errors, f"extracted hash mismatch: {name}")

    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    schema = json.loads((PACK / "task.schema.json").read_text(encoding="utf-8"))
    tasks = json.loads((PACK / "tasks.json").read_text(encoding="utf-8"))
    jsonl = [json.loads(line) for line in (PACK / "tasks.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if tasks != jsonl:
        fail(errors, "tasks.json and tasks.jsonl differ in ordered records")
    if len(tasks) != 100 or manifest["task_count"] != 100:
        fail(errors, "task count is not exactly 100")
    ids = [task.get("task_id") for task in tasks]
    if len(ids) != len(set(ids)):
        fail(errors, "task IDs are not unique")
    identifier = re.compile(schema["properties"]["task_id"]["pattern"])
    for task in tasks:
        if not identifier.fullmatch(task.get("task_id", "")):
            fail(errors, f"invalid task ID: {task.get('task_id')}")
        try:
            jsonschema.Draft202012Validator(schema).validate(task)
        except jsonschema.ValidationError as exc:
            fail(errors, f"schema failure {task.get('task_id')}: {exc.message}")
        scoring = task.get("scoring", {})
        if scoring.get("total") != 100 or sum(item.get("points", -1) for item in scoring.get("items", [])) != 100:
            fail(errors, f"scoring total failure: {task.get('task_id')}")
        for field in ("initial_state", "required_capabilities", "expected_artifacts", "expected_tests", "expected_diagnostics", "required_trace_events", "oracle_checks", "forbidden_behavior", "randomization", "hard_failures"):
            if not task.get(field):
                fail(errors, f"required array absent/empty {task.get('task_id')}: {field}")
        if not task.get("notes", "").strip():
            fail(errors, f"notes absent: {task.get('task_id')}")
    if Counter(task["category"] for task in tasks) != Counter(manifest["category_counts"]):
        fail(errors, "category distribution differs from manifest")
    if Counter(task["expected_disposition"] for task in tasks) != Counter(manifest["expected_disposition_counts"]):
        fail(errors, "disposition distribution differs from manifest")
    text = (PACK / "tasks.md").read_text(encoding="utf-8")
    for task in tasks:
        marker = f"### {task['task_id']}"
        if marker not in text or task["title"] not in text or task["expected_disposition"] not in text:
            fail(errors, f"tasks.md does not correspond to {task['task_id']}")

    generated = ast.parse((PACK / "_build_v1_1.py").read_text(encoding="utf-8"))
    imports = {alias.name.split(".")[0] for node in ast.walk(generated) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    # `os` is permitted solely for the documented SP100_V10_DIR environment
    # selection; destructive/process/network modules are not.
    forbidden_imports = {"subprocess", "shutil", "socket", "requests", "urllib"}
    if imports & forbidden_imports:
        fail(errors, f"generator imports unexpected capabilities: {sorted(imports & forbidden_imports)}")

    overlay = json.loads((PACK / "core-30-selection.json").read_text(encoding="utf-8"))
    selected = overlay["selected_task_ids"]
    by_id = {task["task_id"]: task for task in tasks}
    if len(selected) != 30 or len(selected) != len(set(selected)) or not set(selected) <= set(by_id):
        fail(errors, "core-30 selection is not 30 unique existing task IDs")
    covered_categories = {by_id[task_id]["category"] for task_id in selected}
    covered_dispositions = {by_id[task_id]["expected_disposition"] for task_id in selected}
    if covered_categories != set(manifest["category_counts"]):
        fail(errors, "core-30 does not cover all declared categories")
    if covered_dispositions != set(manifest["expected_disposition_counts"]):
        fail(errors, "core-30 does not cover all declared dispositions")
    if not CALIBRATION_IDS <= set(selected):
        fail(errors, "core-30 omits calibration-sensitive task")
    results.update({"task_count": len(tasks), "category_distribution": Counter(task["category"] for task in tasks), "disposition_distribution": Counter(task["expected_disposition"] for task in tasks), "core_30": "passed" if not errors else "failed"})
    print(json.dumps({"passed": not errors, "results": results, "errors": errors}, indent=2, sort_keys=True, default=dict))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
