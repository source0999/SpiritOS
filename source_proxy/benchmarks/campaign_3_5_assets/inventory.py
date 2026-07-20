"""Generate the Campaign 3.5 fixture inventory from immutable task records.

The generated JSON deliberately contains task contract metadata only.  Private
oracle code, reference transformations, and seeds live in a store that is not
below the coder-visible fixture root.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


STATUS_NOT_STARTED = "NOT_STARTED"
VALID_STATUSES = frozenset(
    {
        STATUS_NOT_STARTED,
        "BUILDER_IMPLEMENTED",
        "VISIBLE_TESTS_IMPLEMENTED",
        "PRIVATE_ORACLE_IMPLEMENTED",
        "SEEDING_IMPLEMENTED",
        "DECOYS_IMPLEMENTED",
        "BOUNDARY_VALIDATED",
        "FULLY_VALIDATED",
        "FROZEN",
    }
)


def _technology(fixture: str) -> str:
    if fixture.startswith("py-"):
        return "python"
    if fixture.startswith(("ts-", "react-")):
        return "typescript"
    if fixture.startswith("go-"):
        return "go"
    if fixture.startswith("rust-"):
        return "rust"
    if fixture.startswith("java-"):
        return "java"
    if fixture.startswith("sql-"):
        return "sql"
    if "context" in fixture or "monorepo" in fixture or "search" in fixture:
        return "multi-repository-context"
    return "control-plane"


def _needs_decoys(tasks: list[dict[str, Any]]) -> bool:
    return any(
        task["category"] in {"repository_search_knowledge_intensive", "context_overflow_or_complex_escalation"}
        or "search" in task["fixture"]
        or "decoy" in " ".join(task.get("oracle_checks", [])).lower()
        for task in tasks
    )


def _runtime_dependencies(technology: str) -> list[str]:
    return {
        "python": ["python3", "git", "pytest"],
        "typescript": ["node", "npm", "git"],
        "go": ["go", "git"],
        "rust": ["cargo", "git"],
        "java": ["java", "javac", "git"],
        "sql": ["python3", "sqlite3", "git"],
        "multi-repository-context": ["git", "python3"],
        "control-plane": ["git", "python3"],
    }[technology]


def build_inventory(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Return an ordered, lossless task-to-fixture readiness inventory."""
    by_fixture: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        by_fixture[task["fixture"]].append(task)

    fixtures: list[dict[str, Any]] = []
    for fixture_id in sorted(by_fixture):
        grouped = sorted(by_fixture[fixture_id], key=lambda task: task["task_id"])
        technology = _technology(fixture_id)
        task_ids = [task["task_id"] for task in grouped]
        disposition_counts = Counter(task["expected_disposition"] for task in grouped)
        categories = sorted({task["category"] for task in grouped})
        fixtures.append(
            {
                "fixture_id": fixture_id,
                "task_ids": task_ids,
                "technology": technology,
                "categories": categories,
                "expected_dispositions": dict(sorted(disposition_counts.items())),
                "base_repository_structure": "declared by private builder; fresh git repository per task",
                "required_initial_state": {task["task_id"]: task["initial_state"] for task in grouped},
                "visible_test_contract": {task["task_id"]: task["expected_tests"] for task in grouped},
                "private_oracle_contract": {task["task_id"]: task["oracle_checks"] for task in grouped},
                "required_capabilities": sorted({capability for task in grouped for capability in task["required_capabilities"]}),
                "forbidden_behaviors": sorted({behavior for task in grouped for behavior in task["forbidden_behavior"]}),
                "decoys_required": _needs_decoys(grouped),
                "randomizable_fields": sorted({field for task in grouped for field in task["randomization"]}),
                "semantic_invariants": {task["task_id"]: task["oracle_checks"] for task in grouped},
                "baseline_hash_strategy": "sha256(git write-tree) at immutable baseline commit",
                "cleanup_strategy": "owned disposable root removed by harness after oracle completion",
                "runtime_dependencies": _runtime_dependencies(technology),
                "outage_or_authority_behavior": sorted(
                    {
                        task["expected_disposition"]
                        for task in grouped
                        if task["expected_disposition"] != "COMPLETED_VERIFIED"
                    }
                ),
                "implementation_status": STATUS_NOT_STARTED,
                "validation_status": STATUS_NOT_STARTED,
            }
        )
    return {
        "schema_version": "campaign-3.5-fixture-inventory/v1",
        "source": "benchmarks/coder-backend-100/v1.1/tasks.json",
        "fixture_count": len(fixtures),
        "task_count": len(tasks),
        "fixtures": fixtures,
        "aggregate_readiness": summarize_inventory(fixtures),
    }


def summarize_inventory(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [fixture for fixture in fixtures if fixture["implementation_status"] in {"FULLY_VALIDATED", "FROZEN"}]
    executable = sum(len(fixture["task_ids"]) for fixture in complete)
    coverage = Counter(fixture["technology"] for fixture in fixtures)
    dependencies = sorted({dependency for fixture in fixtures for dependency in fixture["runtime_dependencies"]})
    return {
        "fixtures_total": len(fixtures),
        "fixtures_complete": len(complete),
        "fixtures_incomplete": len(fixtures) - len(complete),
        "tasks_executable": executable,
        "tasks_not_executable": sum(len(fixture["task_ids"]) for fixture in fixtures) - executable,
        "technology_coverage": dict(sorted(coverage.items())),
        "runtime_dependencies": dependencies,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tasks = json.loads(args.tasks.read_text(encoding="utf-8"))
    inventory = build_inventory(tasks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
