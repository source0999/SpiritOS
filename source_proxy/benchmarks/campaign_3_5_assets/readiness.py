"""Refresh the checked-in asset readiness record without changing v1.1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import IMPLEMENTED_FIXTURE_IDS
from source_proxy.benchmarks.campaign_3_5_assets.inventory import build_inventory
from source_proxy.benchmarks.campaign_3_5_assets.validation import validate_builders


def refresh(tasks_path: Path, output_path: Path, *, validation_report_path: Path | None = None) -> dict[str, object]:
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    report = validate_builders(tasks) if validation_report_path else None
    if report and validation_report_path:
        validation_report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    boundary_validated = frozenset(report["validated_fixture_ids"]) if report and report["passed"] else frozenset()
    inventory = build_inventory(tasks, builder_implemented=IMPLEMENTED_FIXTURE_IDS, boundary_validated=boundary_validated)
    output_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validation-output", type=Path)
    args = parser.parse_args()
    refresh(args.tasks, args.output, validation_report_path=args.validation_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
