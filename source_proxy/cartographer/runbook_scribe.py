from __future__ import annotations

from hashlib import sha256

from source_proxy.cartographer.blueprint_registry import list_blueprints
from source_proxy.cartographer.change_scribe import summarize_changes
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.models import BlueprintRecord, ChangeScribeSummary, DriftFinding, RunbookScribeSuggestion


def suggest_runbook_updates() -> list[RunbookScribeSuggestion]:
    runbooks_by_project = _runbooks_by_project()
    summaries = {summary.project_id: summary for summary in summarize_changes()}
    findings = detect_blueprint_drift()
    qa_gap_files = _qa_gap_files_by_project(findings)
    suggestions: list[RunbookScribeSuggestion] = []
    for finding in findings:
        if _covered_by_qa_gap(finding, qa_gap_files):
            continue
        if not _needs_runbook_suggestion(finding):
            continue
        runbook = _target_runbook(finding, runbooks_by_project.get(finding.project_id, []))
        if not runbook:
            continue
        suggestions.append(_suggestion_for_finding(finding, runbook, summaries.get(finding.project_id)))
    return suggestions


def _qa_gap_files_by_project(findings: list[DriftFinding]) -> dict[str, set[str]]:
    covered: dict[str, set[str]] = {}
    for finding in findings:
        if finding.reason != "api_changed_without_manual_checklist_update":
            continue
        covered.setdefault(finding.project_id, set()).update(finding.changed_files)
    return covered


def _covered_by_qa_gap(
    finding: DriftFinding,
    qa_gap_files: dict[str, set[str]],
) -> bool:
    if finding.reason != "route_changed":
        return False
    return bool(set(finding.changed_files) & qa_gap_files.get(finding.project_id, set()))


def _runbooks_by_project() -> dict[str, list[BlueprintRecord]]:
    runbooks: dict[str, list[BlueprintRecord]] = {}
    for blueprint in list_blueprints():
        if blueprint.status != "runbook":
            continue
        runbooks.setdefault(blueprint.project_id, []).append(blueprint)
    return runbooks


def _needs_runbook_suggestion(finding: DriftFinding) -> bool:
    return (
        finding.reason == "api_changed_without_manual_checklist_update"
        or finding.reason == "route_changed"
        or any(_is_ui_path(path) for path in finding.changed_files)
    )


def _target_runbook(
    finding: DriftFinding,
    runbooks: list[BlueprintRecord],
) -> BlueprintRecord | None:
    for blueprint in runbooks:
        if blueprint.blueprint_id in finding.affected_blueprints:
            return blueprint
    return runbooks[0] if runbooks else None


def _suggestion_for_finding(
    finding: DriftFinding,
    runbook: BlueprintRecord,
    summary: ChangeScribeSummary | None,
) -> RunbookScribeSuggestion:
    target_runbook = f"_blueprints/{runbook.path}"
    checklist_items, expected_outputs = _checklist_and_outputs(finding)
    return RunbookScribeSuggestion(
        suggestion_id=_suggestion_id(finding, runbook),
        project_id=finding.project_id,
        component=finding.component,
        target_runbook=target_runbook,
        reason=_reason(finding, runbook, summary),
        changed_files=finding.changed_files,
        checklist_items=checklist_items,
        expected_outputs=expected_outputs,
        evidence=_evidence(finding, runbook, summary),
        editable=True,
        rejectable=True,
        action_taken=False,
    )


def _checklist_and_outputs(finding: DriftFinding) -> tuple[list[str], list[str]]:
    if finding.reason == "api_changed_without_manual_checklist_update":
        endpoint_hint = _endpoint_hint(finding.changed_files)
        return (
            [
                f"Call {endpoint_hint} with the expected local credentials or dev proxy settings.",
                "Confirm the response is read-only unless an explicit approval action is being tested.",
                "Confirm failed or missing inputs return a structured error instead of writing files.",
            ],
            [
                "HTTP response is JSON.",
                "write_actions_enabled remains false for read-only checks.",
                "No commit or push occurs.",
            ],
        )
    if finding.reason == "route_changed":
        return (
            [
                "Open the affected dashboard or API route through the local dev server.",
                "Confirm the route renders or returns JSON without a server error.",
                "Confirm the visible state matches the approved blueprint behavior.",
            ],
            [
                "Route responds successfully.",
                "No unexpected write, commit, or push action appears.",
            ],
        )
    return (
        [
            "Open the dashboard.",
            "Confirm the changed widget appears in the expected section.",
            "Expand any preview or detail control related to the changed widget.",
            "Confirm approval controls do not apply, commit, or push without explicit approval.",
        ],
        [
            "Changed widget is visible.",
            "Preview/details can be inspected.",
            "No push occurs.",
        ],
    )


def _reason(
    finding: DriftFinding,
    runbook: BlueprintRecord,
    summary: ChangeScribeSummary | None,
) -> str:
    base = f"{finding.reason} suggests manual QA coverage in {runbook.blueprint_id}."
    if summary and summary.summary:
        return f"{base} Change Scribe observed: {summary.summary}"
    return base


def _evidence(
    finding: DriftFinding,
    runbook: BlueprintRecord,
    summary: ChangeScribeSummary | None,
) -> list[str]:
    evidence = [
        f"target runbook: {runbook.blueprint_id}",
        f"drift reason: {finding.reason}",
    ]
    evidence.extend(f"changed file: {path}" for path in finding.changed_files[:8])
    if summary:
        evidence.extend(summary.evidence[:4])
    return list(dict.fromkeys(evidence))


def _endpoint_hint(changed_files: list[str]) -> str:
    for path in changed_files:
        normalized = path.replace("\\", "/")
        if normalized.startswith("src/app/api/") and normalized.endswith("/route.ts"):
            route = normalized.removeprefix("src/app").removesuffix("/route.ts")
            return route or "/api"
    return "the changed API route"


def _is_ui_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith("src/components/")
        or normalized.startswith("src/app/")
    ) and normalized.endswith((".tsx", ".jsx", ".css"))


def _suggestion_id(finding: DriftFinding, runbook: BlueprintRecord) -> str:
    key = "|".join([finding.project_id, finding.drift_id, runbook.blueprint_id, runbook.path])
    return f"rb-scribe-{sha256(key.encode('utf-8')).hexdigest()[:12]}"
