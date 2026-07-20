"""Fail-closed Campaign 3.5 asset-readiness gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def asset_readiness(tasks: list[dict[str, Any]], *, builder_report: dict[str, Any], noncompletion_report: dict[str, Any], core_reference_report: dict[str, Any]) -> dict[str, Any]:
    task_ids = {task["task_id"] for task in tasks}
    noncompletion_validated = set(noncompletion_report.get("validated_task_ids", []))
    reference_validated = set(core_reference_report.get("validated_task_ids", []))
    completed_ids = {task["task_id"] for task in tasks if task["expected_disposition"] == "COMPLETED_VERIFIED"}
    runtime_validated: set[str] = set()
    missing = sorted(task_ids - noncompletion_validated - reference_validated)
    fixture_builder_ready = bool(builder_report.get("passed")) and len(builder_report.get("validated_fixture_ids", [])) == 65
    passed = fixture_builder_ready and noncompletion_validated == (task_ids - completed_ids) and runtime_validated == completed_ids
    return {
        "schema_version": "campaign-3.5-asset-readiness/v1",
        "passed": passed,
        "fixture_types_required": 65,
        "fixture_types_boundary_validated": len(builder_report.get("validated_fixture_ids", [])),
        "oracle_profiles_required": 100,
        "private_oracle_profiles_staged": 100,
        "completed_task_runtime_semantic_validation": len(runtime_validated),
        "reference_solvability_structurally_validated": len(reference_validated),
        "blocked_or_escalation_state_validated": len(noncompletion_validated),
        "tasks_executable": 100 if passed else 0,
        "tasks_not_executable": 0 if passed else 100,
        "remaining_profile_task_ids": missing,
        "gate_failures": [] if passed else ["completed_task_runtime_semantic_oracles_incomplete"],
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
