"""Private reference-solvability validation for the frozen ten-task set."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_basic_assets.catalog import (
    EXPECTED_TASK_IDS,
    load_basic_backend_tasks,
    render_basic_backend_task,
)
from source_proxy.benchmarks.campaign_3_5_basic_assets.fixtures import materialize_basic_backend_fixture
from source_proxy.benchmarks.campaign_3_5_basic_assets.oracles import evaluate_private_oracle
from source_proxy.benchmarks.campaign_3_5_basic_assets.references import apply_reference
from source_proxy.benchmarks.campaign_3_5_basic_assets.seeding import BasicBackendRunSeed
from source_proxy.benchmarks.campaign_3_5_fixture_authority import (
    ENV_MANIFEST,
    load_campaign_3_5_fixture_authority,
)


ASSET_ROOT = Path(__file__).resolve().parent
REFERENCE_REPORT = ASSET_ROOT / "reference-validation-report.json"


def validate_references() -> dict[str, Any]:
    tasks = load_basic_backend_tasks()
    seed = BasicBackendRunSeed.from_private_bytes(
        hashlib.sha256(b"basic-backend-10-private-reference-validation-v1").digest()
    )
    records: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="basic-backend-10-reference-") as temporary:
        temporary_root = Path(temporary).resolve()
        for task_id in EXPECTED_TASK_IDS:
            task_parent = temporary_root / task_id.lower()
            task_parent.mkdir(mode=0o700)
            rendered = render_basic_backend_task(
                task_id,
                run_seed=seed,
                run_nonce="private-reference-validation-v1",
                tasks=tasks,
            )
            fixture = materialize_basic_backend_fixture(task_parent, rendered)
            authority_path = task_parent / "authority.json"
            authority_path.write_text(
                json.dumps(fixture.authority_manifest, sort_keys=True),
                encoding="utf-8",
            )
            os.chmod(authority_path, 0o600)
            authority_passed = _authority_load_passed(authority_path, fixture)
            apply_reference(fixture)
            public = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=fixture.root,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
                env=_validation_environment(),
            )
            oracle = evaluate_private_oracle(task_id, fixture.root, rendered.values)
            changed = _git(fixture.root, "diff", "--name-only").splitlines()
            scope_passed = all(_in_scope(path, rendered.definition.writable_paths) for path in changed)
            record = {
                "task_id": task_id,
                "authority_passed": authority_passed,
                "public_tests_passed": public.returncode == 0,
                "private_oracle_passed": oracle.passed,
                "writable_scope_passed": scope_passed,
                "public_test_output_sha256": hashlib.sha256(
                    _stable_test_output(public.stdout + public.stderr).encode("utf-8")
                ).hexdigest(),
            }
            record["passed"] = all(
                bool(record[key])
                for key in (
                    "authority_passed",
                    "public_tests_passed",
                    "private_oracle_passed",
                    "writable_scope_passed",
                )
            )
            records.append(record)
    return {
        "schema_version": "source-proxy-basic-backend-10-reference-validation/v1",
        "definition_version": "source_proxy_basic_backend_10_v1",
        "task_count": len(records),
        "passed": len(records) == 10 and all(bool(record["passed"]) for record in records),
        "tasks": records,
    }


def write_reference_validation_report(path: Path = REFERENCE_REPORT) -> dict[str, Any]:
    report = validate_references()
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _authority_load_passed(path: Path, fixture: object) -> bool:
    previous = os.environ.get(ENV_MANIFEST)
    os.environ[ENV_MANIFEST] = str(path.resolve())
    try:
        authority = load_campaign_3_5_fixture_authority()
        return (
            authority.baseline_commit == fixture.baseline_commit
            and authority.baseline_tree == fixture.baseline_tree
            and authority.writable_paths == fixture.rendered_task.definition.writable_paths
        )
    finally:
        if previous is None:
            os.environ.pop(ENV_MANIFEST, None)
        else:
            os.environ[ENV_MANIFEST] = previous


def _validation_environment() -> dict[str, str]:
    keep = ("PATH", "SYSTEMROOT", "WINDIR", "TMP", "TEMP", "TMPDIR")
    environment = {key: os.environ[key] for key in keep if key in os.environ}
    environment.update(
        {
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
    )
    return environment


def _stable_test_output(value: str) -> str:
    """Remove runtime-only duration noise before freezing proof hashes."""
    return re.sub(r"\b\d+(?:\.\d+)?s\b", "<duration>", value.replace("\r\n", "\n"))


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args],
        text=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    ).strip()


def _in_scope(path: str, scopes: tuple[str, ...]) -> bool:
    return any(
        path == scope.rstrip("/") or path.startswith(scope.rstrip("/") + "/")
        for scope in scopes
    )


def main() -> int:
    report = write_reference_validation_report()
    print(json.dumps({"passed": report["passed"], "task_count": report["task_count"]}, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
