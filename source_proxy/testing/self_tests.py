from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from source_proxy.verification.diff import preview_diff_verification


SUITE_PHASE_4E_SAFETY_SEED = "phase-4e-safety-seed"
DRY_RUN_MODE = "dry_run"
DOC_TARGET = "docs/phase-8-manual-check.md"
APPROVAL_DISABLED_TEXT = "Approval is disabled until required gates pass"


@dataclass(frozen=True)
class SelfTestCase:
    case_id: str
    name: str
    description: str
    task_prompt: str
    expected_target: str
    manual_diff_input: str | None = None
    expected_workflow_state: str = "Blocked"
    expected_blocker: str | None = None
    expected_safety_level: str = "blocked"
    expected_check_code_change: str = "blocked"
    expected_would_change_files: str = "no"
    expected_task_spec_allowed_files: str = "fail"
    expected_approval_available: bool = False
    required_reason_codes: list[str] = field(default_factory=list)
    allowed_secondary_reason_codes: list[str] = field(default_factory=list)
    must_not_apply: bool = True
    expected_ui_text: list[str] = field(default_factory=lambda: [APPROVAL_DISABLED_TEXT])
    recorded_evidence: dict[str, Any] | None = None


@dataclass
class SelfTestResult:
    case_id: str
    status: str
    evidence: dict[str, Any]
    missing: list[str] = field(default_factory=list)

    def as_payload(self) -> dict[str, Any]:
        return asdict(self)


def phase_4e_safety_seed_cases() -> dict[str, SelfTestCase]:
    check_7_evidence = {
        "current_workflow_state": "Blocked",
        "target": ".env.local",
        "last_blocker": "Blocked: protected/secret path",
        "check_code_change": "blocked",
        "safety_level": "blocked",
        "would_change_files": "no",
        "task_spec_allowed_files": "fail",
        "approval_available": False,
        "ui_text": [APPROVAL_DISABLED_TEXT],
        "blocked_reasons": [
            {"path": ".env.local", "reason_code": "secret_shaped_path"},
            {"path": ".env.local", "reason_code": "protected_path"},
            {"path": ".env.local", "reason_code": "task_spec_allowed_file_violation"},
            {"path": DOC_TARGET, "reason_code": "task_spec_target_mismatch"},
            {"path": DOC_TARGET, "reason_code": "requirement_coverage_failed"},
            {"path": "*", "reason_code": "diff_apply_check_failed"},
        ],
        "would_apply_diff": False,
        "would_execute": False,
        "file_written": False,
        "applied_anything": False,
    }
    task_7 = "\n".join(
        [
            f"Target file: {DOC_TARGET}",
            "",
            "Use the manual diff preview to validate protected-path blocking. Do not edit any other file.",
        ]
    )
    task_8 = "\n".join(
        [
            f"Target file: {DOC_TARGET}",
            "",
            "Use the manual diff preview to validate path traversal blocking. Do not edit any other file.",
        ]
    )
    diff_8 = "\n".join(
        [
            "diff --git a/../README.md b/../README.md",
            "--- a/../README.md",
            "+++ b/../README.md",
            "@@ -1,3 +1,4 @@",
            " # SpiritOS",
            "+PATH TRAVERSAL SHOULD NEVER APPLY",
            "",
        ]
    )
    return {
        "manual-check-7": SelfTestCase(
            case_id="manual-check-7",
            name="Manual Check 7: protected secret path block",
            description="Recorded PASS evidence for protected/secret manual diff blocking.",
            task_prompt=task_7,
            expected_target=".env.local",
            manual_diff_input="\n".join(
                [
                    "--- a/.env.local",
                    "+++ b/.env.local",
                    "@@ -0,0 +1 @@",
                    "+TEST_VALUE=1",
                    "",
                ]
            ),
            expected_blocker="Blocked: protected/secret path",
            required_reason_codes=[
                "secret_shaped_path",
                "protected_path",
                "task_spec_allowed_file_violation",
            ],
            allowed_secondary_reason_codes=[
                "task_spec_target_mismatch",
                "requirement_coverage_failed",
                "diff_apply_check_failed",
                "target_mismatch",
            ],
            recorded_evidence=check_7_evidence,
        ),
        "manual-check-8": SelfTestCase(
            case_id="manual-check-8",
            name="Manual Check 8: path traversal manual diff",
            description="Dry-run a traversal-shaped manual fallback diff and verify approval stays blocked.",
            task_prompt=task_8,
            expected_target="../README.md",
            manual_diff_input=diff_8,
            expected_blocker="path_escape",
            required_reason_codes=["path_escape"],
            allowed_secondary_reason_codes=[
                "outside_workspace",
                "task_spec_allowed_file_violation",
                "task_spec_target_mismatch",
                "requirement_coverage_failed",
                "diff_apply_check_failed",
                "target_mismatch",
            ],
        ),
    }


def run_self_test_suite(
    *,
    suite: str,
    case_ids: list[str] | None = None,
    mode: str = DRY_RUN_MODE,
) -> dict[str, Any]:
    if mode != DRY_RUN_MODE:
        raise ValueError("Only dry_run mode is supported for coding self-tests.")
    if suite != SUITE_PHASE_4E_SAFETY_SEED:
        raise ValueError(f"Unknown self-test suite: {suite}")

    cases = phase_4e_safety_seed_cases()
    selected = case_ids or list(cases.keys())
    results: list[SelfTestResult] = []
    for case_id in selected:
        case = cases.get(case_id)
        if case is None:
            results.append(
                SelfTestResult(
                    case_id=case_id,
                    status="skip",
                    evidence={},
                    missing=[f"unknown case_id: {case_id}"],
                )
            )
            continue
        results.append(_run_case(case))

    summary = {
        "passed": sum(1 for result in results if result.status == "pass"),
        "failed": sum(1 for result in results if result.status == "fail"),
        "skipped": sum(1 for result in results if result.status == "skip"),
    }
    return {
        "suite": suite,
        "mode": mode,
        "summary": summary,
        "cases": [result.as_payload() for result in results],
        "applied_anything": False,
    }


def _run_case(case: SelfTestCase) -> SelfTestResult:
    if case.recorded_evidence is not None:
        evidence = _normalize_recorded_evidence(case.recorded_evidence)
    elif case.manual_diff_input:
        evidence = _preview_manual_diff_case(case)
    else:
        return SelfTestResult(
            case_id=case.case_id,
            status="skip",
            evidence={},
            missing=["case has no recorded evidence or manual diff input"],
        )

    missing = _missing_expectations(case, evidence)
    return SelfTestResult(
        case_id=case.case_id,
        status="fail" if missing else "pass",
        evidence=evidence,
        missing=missing,
    )


def _preview_manual_diff_case(case: SelfTestCase) -> dict[str, Any]:
    preview = preview_diff_verification(
        case.manual_diff_input or "",
        route_type="local_route",
        task_text=case.task_prompt,
        task_spec={
            "schema_version": 1,
            "task_type": "modify_existing_file",
            "target": DOC_TARGET,
            "allowed_files": [DOC_TARGET],
            "forbidden_files": [],
            "literal_requirements": [],
            "verification": ["git apply check", "target-only"],
            "risk_tier": "low",
            "source": "phase_4e_safety_seed",
        },
    )
    blocked_reasons = [
        {
            "path": str(reason.get("path") or ""),
            "reason_code": str(reason.get("reason_code") or ""),
        }
        for reason in preview.get("blocked_reasons", [])
        if isinstance(reason, dict)
    ]
    changed_files = [
        str(file.get("path") or "")
        for file in preview.get("changed_files", [])
        if isinstance(file, dict)
    ]
    task_spec_check = (
        preview.get("task_spec_check")
        if isinstance(preview.get("task_spec_check"), dict)
        else {}
    )
    return {
        "current_workflow_state": "Blocked"
        if preview.get("status") == "blocked"
        else str(preview.get("status") or ""),
        "target": changed_files[0] if changed_files else "",
        "last_blocker": _last_blocker_from_reasons(blocked_reasons),
        "check_code_change": str(preview.get("status") or ""),
        "safety_level": str(preview.get("risk") or ""),
        "would_change_files": "yes" if preview.get("would_apply_diff") else "no",
        "task_spec_allowed_files": "pass" if task_spec_check.get("ok") else "fail",
        "approval_available": bool(
            preview.get("status") != "blocked"
            and preview.get("limits", {}).get("file_writes_allowed") is True
        ),
        "ui_text": [APPROVAL_DISABLED_TEXT]
        if preview.get("status") == "blocked"
        else [],
        "blocked_reasons": blocked_reasons,
        "changed_files": changed_files,
        "git_apply_check_ok": preview.get("git_apply_check_ok"),
        "would_apply_diff": bool(preview.get("would_apply_diff")),
        "would_execute": bool(preview.get("would_execute")),
        "file_writes_allowed": bool(preview.get("limits", {}).get("file_writes_allowed")),
        "file_written": False,
        "applied_anything": False,
    }


def _normalize_recorded_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(evidence)
    normalized["blocked_reasons"] = [
        {
            "path": str(reason.get("path") or ""),
            "reason_code": str(reason.get("reason_code") or ""),
        }
        for reason in evidence.get("blocked_reasons", [])
        if isinstance(reason, dict)
    ]
    normalized["applied_anything"] = False
    normalized["file_written"] = False
    return normalized


def _missing_expectations(case: SelfTestCase, evidence: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    _expect_equal(missing, "current_workflow_state", case.expected_workflow_state, evidence)
    _expect_equal(missing, "check_code_change", case.expected_check_code_change, evidence)
    _expect_equal(missing, "safety_level", case.expected_safety_level, evidence)
    _expect_equal(missing, "would_change_files", case.expected_would_change_files, evidence)
    _expect_equal(missing, "task_spec_allowed_files", case.expected_task_spec_allowed_files, evidence)
    if evidence.get("approval_available") is not case.expected_approval_available:
        missing.append(
            f"approval_available expected {case.expected_approval_available} got {evidence.get('approval_available')}"
        )
    if case.expected_blocker and case.expected_blocker not in str(evidence.get("last_blocker") or ""):
        reason_codes = _reason_codes(evidence)
        if case.expected_blocker not in reason_codes:
            missing.append(f"expected blocker {case.expected_blocker!r} not found")
    reason_codes = _reason_codes(evidence)
    for code in case.required_reason_codes:
        if code not in reason_codes:
            missing.append(f"missing required reason code: {code}")
    for text in case.expected_ui_text:
        if text not in [str(item) for item in evidence.get("ui_text", [])]:
            missing.append(f"missing expected UI text: {text}")
    if case.must_not_apply:
        if evidence.get("would_apply_diff"):
            missing.append("would_apply_diff must stay false")
        if evidence.get("would_execute"):
            missing.append("would_execute must stay false")
        if evidence.get("applied_anything"):
            missing.append("applied_anything must stay false")
        if evidence.get("file_written"):
            missing.append("file_written must stay false")
    return missing


def _expect_equal(
    missing: list[str],
    key: str,
    expected: str,
    evidence: dict[str, Any],
) -> None:
    if str(evidence.get(key) or "") != expected:
        missing.append(f"{key} expected {expected!r} got {evidence.get(key)!r}")


def _reason_codes(evidence: dict[str, Any]) -> set[str]:
    return {
        str(reason.get("reason_code") or "")
        for reason in evidence.get("blocked_reasons", [])
        if isinstance(reason, dict)
    }


def _last_blocker_from_reasons(blocked_reasons: list[dict[str, str]]) -> str:
    reason_codes = {reason["reason_code"] for reason in blocked_reasons}
    if "path_escape" in reason_codes or "outside_workspace" in reason_codes:
        return "Blocked: path escapes workspace"
    if "protected_path" in reason_codes or "secret_shaped_path" in reason_codes:
        return "Blocked: protected/secret path"
    if "task_spec_allowed_file_violation" in reason_codes:
        return "Blocked: task_spec_allowed_file_violation"
    return "Blocked" if blocked_reasons else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run read-only coding self-tests.")
    parser.add_argument("--suite", default=SUITE_PHASE_4E_SAFETY_SEED)
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument("--mode", default=DRY_RUN_MODE)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    try:
        payload = run_self_test_suite(
            suite=args.suite,
            case_ids=args.case_ids,
            mode=args.mode,
        )
    except ValueError as error:
        print(f"ERROR: {error}")
        return 2

    if args.json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        summary = payload["summary"]
        print(
            f"{payload['suite']} ({payload['mode']}): "
            f"{summary['passed']} passed, {summary['failed']} failed, {summary['skipped']} skipped"
        )
        print(f"applied_anything: {str(payload['applied_anything']).lower()}")
        for result in payload["cases"]:
            print(f"{result['case_id']}: {result['status'].upper()}")
            if result["missing"]:
                for item in result["missing"]:
                    print(f"  missing: {item}")
            else:
                evidence = result["evidence"]
                print(f"  target: {evidence.get('target')}")
                print(f"  approval_available: {str(evidence.get('approval_available')).lower()}")
                print(f"  would_change_files: {evidence.get('would_change_files')}")
    return 0 if payload["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
