#!/usr/bin/env python3
"""Run non-benchmark Campaign 3.5 adapter calibration cases through the canonical route."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

# The harness is invoked as a script from operator automation, where Python
# does not automatically add the repository root to sys.path.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from source_proxy.benchmarks.campaign_3_5_fixture_authority import ENV_MANIFEST
from source_proxy.target_plugins.adapter import (
    GENERIC_WORKSPACE_CONTEXT_ID,
    GENERIC_WORKSPACE_PLUGIN_ID,
    GENERIC_WORKSPACE_PROFILE,
    GENERIC_WORKSPACE_PROMPT_ID,
    TARGET_PLUGIN_SCHEMA_VERSION,
    execute_target_plugin_command,
    resolve_target_plugin,
)


SCHEMA_VERSION = "campaign-3.5-calibration/v1"


@dataclass(frozen=True)
class CalibrationCase:
    case_id: str
    files: dict[str, str]
    task: str
    required_fragments: dict[str, str]


CASES: tuple[CalibrationCase, ...] = (
    CalibrationCase("C01-python-constant", {"src/settings.py": "TIMEOUT_SECONDS = 30\n"}, "Change TIMEOUT_SECONDS from 30 to 45.", {"src/settings.py": "45"}),
    CalibrationCase("C02-python-function", {"src/greeting.py": "def greeting():\n    return 'draft'\n"}, "Make greeting return the exact string 'ready' instead of 'draft'.", {"src/greeting.py": "'ready'"}),
    CalibrationCase("C03-typescript-constant", {"src/status.ts": "export const status = 'draft';\n"}, "Change the exported status from 'draft' to the exact value 'ready'.", {"src/status.ts": "'ready'"}),
    CalibrationCase("C04-go-function", {"src/label.go": "package label\n\nfunc Value() string { return \"draft\" }\n"}, "Change Value so it returns the exact string \"ready\" instead of \"draft\".", {"src/label.go": '"ready"'}),
    CalibrationCase("C05-java-method", {"src/State.java": "class State { static String value() { return \"draft\"; } }\n"}, "Change State.value so it returns the exact string \"ready\" instead of \"draft\".", {"src/State.java": '"ready"'}),
    CalibrationCase("C06-rust-constant", {"src/lib.rs": "pub const STATE: &str = \"draft\";\n"}, "Change STATE from \"draft\" to the exact string \"ready\".", {"src/lib.rs": '"ready"'}),
    CalibrationCase("C07-sql-query", {"migrations/query.sql": "SELECT id FROM users WHERE state = 'draft';\n"}, "Change the query so it selects rows whose state is exactly 'ready' rather than 'draft'.", {"migrations/query.sql": "'ready'"}),
    CalibrationCase("C08-two-file-python", {"src/config.py": "DEFAULT_LABEL = 'draft'\n", "tests/test_config.py": "EXPECTED_LABEL = 'draft'\n"}, "Update both existing files so the default and expected label are exactly 'ready'.", {"src/config.py": "'ready'", "tests/test_config.py": "'ready'"}),
)


@contextmanager
def _authority(path: Path) -> Iterator[None]:
    previous = os.environ.get(ENV_MANIFEST)
    os.environ[ENV_MANIFEST] = str(path)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(ENV_MANIFEST, None)
        else:
            os.environ[ENV_MANIFEST] = previous


class _PrivateOutputCapture:
    def __init__(self, root: Path, run_id: str) -> None:
        self.root = root / "private-model-output"
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        self.run_id = run_id
        self.hashes: list[dict[str, Any]] = []

    def __call__(self, call: dict[str, Any], raw: str) -> None:
        path = self.root / f"{self.run_id}-call-{int(call['call_index'])}.txt"
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(raw)
        os.chmod(path, 0o600)
        self.hashes.append({"call_index": int(call["call_index"]), "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()})


def _run(command: list[str], cwd: Path, *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, input=input_text, text=True, capture_output=True, check=False, timeout=20)


def _prepare(case: CalibrationCase, parent: Path) -> tuple[Path, Path]:
    root = Path(tempfile.mkdtemp(prefix=f"{case.case_id}-", dir=parent))
    _run(["git", "init", "-q"], root); _run(["git", "config", "user.email", "calibration@example.invalid"], root); _run(["git", "config", "user.name", "Calibration"], root)
    for relative, content in case.files.items():
        path = root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content, encoding="utf-8")
    _run(["git", "add", "."], root); _run(["git", "commit", "-qm", "baseline"], root)
    tree = _run(["git", "write-tree"], root).stdout.strip()
    manifest = {
        "schema_version": "campaign-3.5-fixture-authority/v1",
        "fixture_id": f"calibration-{case.case_id}",
        "workspace_root": str(root.resolve()),
        "baseline_tree_sha256": hashlib.sha256(tree.encode("ascii")).hexdigest(),
        "allowed_paths": ["src/", "tests/", "migrations/"],
        "execution_profile": GENERIC_WORKSPACE_PROFILE,
    }
    authority = root.parent / f"{root.name}-authority.json"
    authority.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8"); os.chmod(authority, 0o600)
    return root, authority


def _packet() -> dict[str, Any]:
    return {"selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "target_plugin": {"schema_version": TARGET_PLUGIN_SCHEMA_VERSION, "id": GENERIC_WORKSPACE_PLUGIN_ID, "fixture_root": ".", "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID, "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID, "execution_profile": GENERIC_WORKSPACE_PROFILE}}


def _case_result(case: CalibrationCase, output_dir: Path, model_alias: str) -> dict[str, Any]:
    run_id = f"calibration-{uuid4().hex}"
    fixture_parent = output_dir / "fixtures"; fixture_parent.mkdir(exist_ok=True, mode=0o700); os.chmod(fixture_parent, 0o700)
    root, authority = _prepare(case, fixture_parent)
    capture = _PrivateOutputCapture(output_dir, run_id)
    result: dict[str, Any] = {}
    apply_error: str | None = None
    try:
        with _authority(authority):
            plugin = resolve_target_plugin(_packet(), root)
            result = execute_target_plugin_command(plugin, task=case.task, workspace_root=root, canonical_context={}, canonical_context_text="", model_alias=model_alias, model_output_observer=capture)
        diff = str(result.get("proposed_diff") or "")
        if diff and result.get("target_adapter_provenance", {}).get("terminal_proof_eligible") is True:
            applied = _run(["git", "apply", "--recount", "-"], root, input_text=diff)
            if applied.returncode:
                apply_error = "synthetic_apply_failed"
    except Exception as error:  # Preserve type only in public calibration evidence.
        apply_error = f"execution_error:{type(error).__name__}"
    fragments_ok = all(fragment in (root / path).read_text(encoding="utf-8") for path, fragment in case.required_fragments.items())
    provenance = result.get("target_adapter_provenance", {}) if isinstance(result, dict) else {}
    diagnostics = result.get("coder_diagnostics", {}) if isinstance(result, dict) else {}
    record = {
        "case_id": case.case_id,
        "run_id": run_id,
        "model_alias": model_alias,
        "provider": provenance.get("provider"),
        "model": provenance.get("model"),
        "call_count": provenance.get("call_count"),
        "response_format": diagnostics.get("model_response_format"),
        "reason_code": result.get("reason_code") if isinstance(result, dict) else None,
        "apply_error": apply_error,
        "acceptance_passed": bool(apply_error is None and fragments_ok),
        "raw_output": {"captured_privately": bool(capture.hashes), "call_hashes": capture.hashes, "public_contains_raw_text": False},
    }
    shutil.rmtree(root, ignore_errors=True); authority.unlink(missing_ok=True)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--model-alias", default="coder")
    parser.add_argument("--case", action="append", choices=[case.case_id for case in CASES])
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True, mode=0o700); os.chmod(args.output_dir, 0o700)
    selected = [case for case in CASES if not args.case or case.case_id in args.case]
    records = [_case_result(case, args.output_dir, args.model_alias) for case in selected]
    report = {"schema_version": SCHEMA_VERSION, "recorded_at": datetime.now(UTC).isoformat(), "nonbenchmark": True, "records": records, "summary": {"case_count": len(records), "accepted_count": sum(bool(record["acceptance_passed"]) for record in records)}}
    path = args.output_dir / "campaign-3-5-calibration-v1.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"); os.chmod(path, 0o600)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0 if report["summary"]["accepted_count"] == len(records) else 2


if __name__ == "__main__":
    raise SystemExit(main())
