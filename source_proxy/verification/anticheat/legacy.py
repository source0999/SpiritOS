from __future__ import annotations

from typing import Any

from source_proxy.verification.anticheat.registry import run_anticheat_detectors


def copied_legacy_anticheat_verdict(payload: dict[str, Any]) -> dict[str, Any]:
    """Copied parity surface for legacy self-test style verdicts.

    This does not replace existing verification modules. It keeps a stable pass/fail
    payload that legacy runners can compare against while F2 introduces the new
    independent registry.
    """
    report = run_anticheat_detectors(payload)
    return {
        "passed": report.passed,
        "status": report.status,
        "violation_codes": [violation.violation_code for violation in report.violations],
    }


def new_registry_parity_verdict(payload: dict[str, Any]) -> dict[str, Any]:
    report = run_anticheat_detectors(payload)
    return {
        "passed": report.passed,
        "status": report.status,
        "violation_codes": [violation.violation_code for violation in report.violations],
    }
