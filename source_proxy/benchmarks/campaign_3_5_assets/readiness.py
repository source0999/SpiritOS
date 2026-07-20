"""Refresh the checked-in asset readiness record without changing v1.1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import IMPLEMENTED_FIXTURE_IDS
from source_proxy.benchmarks.campaign_3_5_assets.inventory import build_inventory


def refresh(tasks_path: Path, output_path: Path) -> dict[str, object]:
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    inventory = build_inventory(tasks, builder_implemented=IMPLEMENTED_FIXTURE_IDS)
    output_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    refresh(args.tasks, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
