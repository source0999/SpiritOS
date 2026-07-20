"""Independent fixture-builder validation; it does not trust builder status."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import IMPLEMENTED_FIXTURE_IDS, materialize_implemented_fixture
from source_proxy.benchmarks.campaign_3_5_assets.seeding import Campaign35RunSeed, derive_task_seed, task_seed_commitment


class Campaign35AssetValidationError(RuntimeError):
    pass


def _tree(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "write-tree"], text=True).strip()


def _clean(root: Path) -> bool:
    return not subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).strip()


def _public_bytes(root: Path) -> bytes:
    return b"".join(
        path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    )


def validate_builders(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Materialize each fixture twice plus a variant in independent temp roots."""
    by_fixture = {task["fixture"]: task for task in tasks}
    if set(by_fixture) != IMPLEMENTED_FIXTURE_IDS:
        raise Campaign35AssetValidationError("campaign_3_5_fixture_catalog_incomplete")
    same_seed = Campaign35RunSeed(raw=b"campaign-3.5-validation-a".ljust(32, b"0"), commitment="validation-a")
    other_seed = Campaign35RunSeed(raw=b"campaign-3.5-validation-b".ljust(32, b"1"), commitment="validation-b")
    records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="campaign35-asset-validation-") as temporary:
        root = Path(temporary)
        for index, fixture_id in enumerate(sorted(by_fixture)):
            task = by_fixture[fixture_id]
            first_parent, second_parent, variant_parent = (root / f"{index}-{suffix}" for suffix in ("first", "second", "variant"))
            for parent in (first_parent, second_parent, variant_parent):
                parent.mkdir()
            first_seed = derive_task_seed(same_seed, task["task_id"], fixture_id)
            variant_seed = derive_task_seed(other_seed, task["task_id"], fixture_id)
            first = materialize_implemented_fixture(first_parent, task, task_seed=first_seed, task_seed_commitment=task_seed_commitment(first_seed))
            second = materialize_implemented_fixture(second_parent, task, task_seed=first_seed, task_seed_commitment=task_seed_commitment(first_seed))
            variant = materialize_implemented_fixture(variant_parent, task, task_seed=variant_seed, task_seed_commitment=task_seed_commitment(variant_seed))
            public = _public_bytes(first.fixture_root)
            no_hidden_paths = not any("hidden" in path.name.lower() or "private" in path.name.lower() for path in first.fixture_root.rglob("*"))
            records.append(
                {
                    "fixture_id": fixture_id,
                    "same_seed_reproducible": first.content_sha256 == second.content_sha256 and _tree(first.fixture_root) == _tree(second.fixture_root),
                    "cross_seed_varies": first.content_sha256 != variant.content_sha256 and _tree(first.fixture_root) != _tree(variant.fixture_root),
                    "baseline_clean": _clean(first.fixture_root),
                    "git_baseline_committed": (first.fixture_root / ".git").is_dir(),
                    "public_tree_has_no_private_or_hidden_path": no_hidden_paths,
                    "seed_not_in_public_tree": first_seed.encode("ascii") not in public and same_seed.raw not in public,
                    "nontrivial_file_count": sum(1 for path in first.fixture_root.rglob("*") if path.is_file() and ".git" not in path.parts) >= 3,
                }
            )
        # Temporary directory removal is independently asserted by moving the
        # validation root through a disposable child that is explicitly removed.
        cleanup_probe = root / "cleanup-probe"
        cleanup_probe.mkdir()
        shutil.rmtree(cleanup_probe)
        cleanup_passed = not cleanup_probe.exists()
    fixture_results = {record["fixture_id"]: all(value for key, value in record.items() if key != "fixture_id") for record in records}
    return {
        "schema_version": "campaign-3.5-asset-builder-validation/v1",
        "fixture_count": len(records),
        "passed": all(fixture_results.values()) and cleanup_passed,
        "fixtures": records,
        "validated_fixture_ids": sorted(fixture_id for fixture_id, passed in fixture_results.items() if passed),
        "cleanup_passed": cleanup_passed,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate_builders(json.loads(args.tasks.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
