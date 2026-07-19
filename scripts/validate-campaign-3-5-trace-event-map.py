#!/usr/bin/env python3
"""Independently validate the Campaign 3.5 benchmark-to-production trace map."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "benchmarks/coder-backend-100/v1.1/trace-event-contract-map.json"
REQUIRED_EVENTS = {
    "authenticated_model_call_authority",
    "durable_task_creation",
    "planner_router_decision",
    "retained_context_consumption",
    "model_provider_invocation",
    "model_call_authority_check",
    "coder_proposal_or_nonmutation",
    "reviewer_result",
    "verifier_and_test_result",
    "evidence_envelope_and_final_receipt",
    "cancellation_restart_and_recovery",
    "truthful_failure_or_impossibility",
}
REQUIRED_FIELDS = {
    "benchmark_event",
    "production_event",
    "payload_mapping",
    "semantic_equivalence",
    "missing_field_analysis",
    "amendment_version",
    "approval_record",
    "independent_evaluator_acceptance",
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"trace map unreadable: {error}"]
    if document.get("schema") != "source-proxy-coder-backend-100-trace-event-contract-map/v1":
        errors.append("trace map schema is invalid")
    if document.get("status") != "MAPPED_PENDING_PHASE_0_RUNTIME_CONFIRMATION":
        errors.append("trace map status does not require Phase 0 runtime confirmation")
    mappings = document.get("mappings")
    if not isinstance(mappings, list):
        return [*errors, "mappings is not a list"]
    names: list[str] = []
    for index, mapping in enumerate(mappings):
        label = f"mapping[{index}]"
        if not isinstance(mapping, dict):
            errors.append(f"{label} is not an object")
            continue
        missing = REQUIRED_FIELDS - set(mapping)
        if missing:
            errors.append(f"{label} missing required fields: {sorted(missing)}")
            continue
        event = str(mapping.get("benchmark_event") or "")
        names.append(event)
        production = mapping.get("production_event")
        if not isinstance(production, dict):
            errors.append(f"{label} production_event is not an object")
            continue
        name = str(production.get("name") or "")
        source_location = str(production.get("source_location") or "")
        if not name or not source_location:
            errors.append(f"{label} production event name or source location is missing")
        else:
            source_path = ROOT / source_location.split(":", 1)[0]
            if not source_path.is_file():
                errors.append(f"{label} source emitter is missing: {source_location}")
            elif f'"{name}"' not in source_path.read_text(encoding="utf-8-sig"):
                errors.append(f"{label} production event is not emitted: {name}")
        payload = mapping.get("payload_mapping")
        if not isinstance(payload, dict) or not payload:
            errors.append(f"{label} payload mapping is missing")
        elif not ({"task_id", "run_id", "authorization_id"} & set(payload)):
            errors.append(f"{label} has no task/run/authority correlation field")
        if not isinstance(mapping.get("missing_field_analysis"), list):
            errors.append(f"{label} missing_field_analysis is not a list")
        elif mapping["missing_field_analysis"]:
            errors.append(f"{label} declares unresolved payload gaps")
        if not str(mapping.get("semantic_equivalence") or "").strip():
            errors.append(f"{label} semantic equivalence is empty")
        if not str(mapping.get("approval_record") or "").strip():
            errors.append(f"{label} approval/evidence record is empty")
        if not str(mapping.get("independent_evaluator_acceptance") or "").startswith("scripts/validate-campaign-3-5-trace-event-map.py:"):
            errors.append(f"{label} lacks independent validator binding")
    duplicates = sorted({name for name in names if names.count(name) > 1 and name})
    if duplicates:
        errors.append(f"duplicate benchmark mappings conceal coverage: {duplicates}")
    missing_events = sorted(REQUIRED_EVENTS - set(names))
    unknown_events = sorted(set(names) - REQUIRED_EVENTS)
    if missing_events:
        errors.append(f"required benchmark events are unmapped: {missing_events}")
    if unknown_events:
        errors.append(f"unknown benchmark events are mapped: {unknown_events}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_MAP)
    arguments = parser.parse_args()
    errors = validate(arguments.path)
    print(json.dumps({"path": str(arguments.path), "passed": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
