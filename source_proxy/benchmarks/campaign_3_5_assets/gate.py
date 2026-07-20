"""Fail-closed Campaign 3.5 asset-readiness gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def asset_readiness(tasks: list[dict[str, Any]], *, builder_report: dict[str, Any], noncompletion_report: dict[str, Any], core_reference_report: dict[str, Any]) -> dict[str, Any]:
    task_ids = {task["task_id"] for task in tasks}
    validated = set(noncompletion_report.get("validated_task_ids", [])) | set(core_reference_report.get("validated_task_ids", []))
    missing = sorted(task_ids - validated)
    fixture_builder_ready = bool(builder_report.get("passed")) and len(builder_report.get("validated_fixture_ids", [])) == 65
    passed = fixture_builder_ready and len(validated) == 100
    return {
        "schema_version": "campaign-3.5-asset-readiness/v1",
        "passed": passed,
        "fixture_types_required": 65,
        "fixture_types_boundary_validated": len(builder_report.get("validated_fixture_ids", [])),
        "oracle_profiles_required": 100,
        "oracle_profiles_independently_validated": len(validated),
        "reference_solvability_validated": len(core_reference_report.get("validated_task_ids", [])),
        "blocked_or_escalation_state_validated": len(noncompletion_report.get("validated_task_ids", [])),
        "tasks_executable": 100 if passed else 0,
        "tasks_not_executable": 0 if passed else 100,
        "remaining_profile_task_ids": missing,
        "gate_failures": [] if passed else ["completed_task_private_reference_and_semantic_probes_incomplete"],
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--builder-report", type=Path, required=True)
    parser.add_argument("--noncompletion-report", type=Path, required=True)
    parser.add_argument("--core-reference-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = asset_readiness(
        json.loads(args.tasks.read_text(encoding="utf-8")),
        builder_report=json.loads(args.builder_report.read_text(encoding="utf-8")),
        noncompletion_report=json.loads(args.noncompletion_report.read_text(encoding="utf-8")),
        core_reference_report=json.loads(args.core_reference_report.read_text(encoding="utf-8")),
    )
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
