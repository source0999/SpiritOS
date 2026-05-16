from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from source_proxy.cartographer.blueprint_registry import list_blueprints
from source_proxy.cartographer.component_mapper import map_paths
from source_proxy.cartographer.git_status import read_git_statuses
from source_proxy.cartographer.models import BlueprintRecord, DriftFinding


def detect_blueprint_drift() -> list[DriftFinding]:
    blueprints = list_blueprints()
    findings: list[DriftFinding] = []
    seen: set[str] = set()

    for git_status in read_git_statuses():
        project_id = git_status.project_id or "unknown"
        if not git_status.available or not git_status.dirty:
            continue

        project_blueprints = [
            blueprint for blueprint in blueprints if blueprint.project_id == project_id
        ]
        changed_files = [_normalize_repo_path(path) for path in git_status.changed_files]
        blueprint_changed = _changed_blueprint_ids(project_blueprints, changed_files)
        non_blueprint_changes = [
            path for path in changed_files if not path.startswith("_blueprints/")
        ]

        for finding in _component_code_drift(
            project_id=project_id,
            blueprints=project_blueprints,
            changed_files=non_blueprint_changes,
            blueprint_changed=blueprint_changed,
        ):
            _append_unique(findings, seen, finding)

        for finding in _readme_drift(
            project_id=project_id,
            blueprints=project_blueprints,
            changed_files=changed_files,
            blueprint_changed=blueprint_changed,
        ):
            _append_unique(findings, seen, finding)

        for finding in _todo_drift(
            project_id=project_id,
            blueprints=project_blueprints,
            changed_files=changed_files,
            blueprint_changed=blueprint_changed,
        ):
            _append_unique(findings, seen, finding)

        for finding in _route_architecture_drift(
            project_id=project_id,
            changed_files=changed_files,
            blueprint_changed=blueprint_changed,
        ):
            _append_unique(findings, seen, finding)

        for finding in _api_qa_gap(
            project_id=project_id,
            blueprints=project_blueprints,
            changed_files=changed_files,
            blueprint_changed=blueprint_changed,
        ):
            _append_unique(findings, seen, finding)

        for finding in _cartographer_api_runbook_gap(
            project_id=project_id,
            blueprints=project_blueprints,
            changed_files=changed_files,
            blueprint_changed=blueprint_changed,
        ):
            _append_unique(findings, seen, finding)

        for finding in _dashboard_qa_gap(
            project_id=project_id,
            blueprints=project_blueprints,
            changed_files=changed_files,
            blueprint_changed=blueprint_changed,
        ):
            _append_unique(findings, seen, finding)

        for finding in _safety_test_gap(
            project_id=project_id,
            changed_files=changed_files,
        ):
            _append_unique(findings, seen, finding)

        for finding in _scout_doc_drift(
            project_id=project_id,
            changed_files=changed_files,
            blueprint_changed=blueprint_changed,
        ):
            _append_unique(findings, seen, finding)

    return findings


def _component_code_drift(
    *,
    project_id: str,
    blueprints: list[BlueprintRecord],
    changed_files: list[str],
    blueprint_changed: set[str],
) -> list[DriftFinding]:
    findings: list[DriftFinding] = []
    used_for_drift = {
        blueprint.blueprint_id: blueprint for blueprint in blueprints if blueprint.used_for_drift
    }
    components, _unmapped = map_paths(changed_files)

    for component in components:
        if component.sandbox or not component.blueprint_id:
            continue
        blueprint = used_for_drift.get(component.blueprint_id)
        if not blueprint or blueprint.blueprint_id in blueprint_changed:
            continue
        findings.append(
            _finding(
                project_id=project_id,
                component=component.component_id,
                reason="component_code_changed",
                affected_blueprints=[blueprint.blueprint_id],
                changed_files=component.matched_paths,
                severity="review_suggested",
            )
        )

    return findings


def _readme_drift(
    *,
    project_id: str,
    blueprints: list[BlueprintRecord],
    changed_files: list[str],
    blueprint_changed: set[str],
) -> list[DriftFinding]:
    readme_changes = [
        path for path in changed_files if Path(path).name.lower() == "readme.md"
    ]
    if not readme_changes:
        return []

    affected = [
        blueprint.blueprint_id
        for blueprint in blueprints
        if blueprint.used_for_drift and blueprint.blueprint_id not in blueprint_changed
    ]
    if not affected:
        return []

    return [
        _finding(
            project_id=project_id,
            component="project",
            reason="readme_changed",
            affected_blueprints=affected,
            changed_files=readme_changes,
            severity="review_suggested",
        )
    ]


def _todo_drift(
    *,
    project_id: str,
    blueprints: list[BlueprintRecord],
    changed_files: list[str],
    blueprint_changed: set[str],
) -> list[DriftFinding]:
    todo_changes = [
        path
        for path in changed_files
        if "todo" in Path(path).name.lower() or "roadmap" in Path(path).name.lower()
    ]
    if not todo_changes:
        return []

    roadmaps = [
        blueprint.blueprint_id
        for blueprint in blueprints
        if blueprint.status == "planned"
        and "roadmap" in blueprint.doc_type
        and blueprint.blueprint_id not in blueprint_changed
    ]
    if not roadmaps:
        return []

    return [
        _finding(
            project_id=project_id,
            component="roadmap",
            reason="todo_changed",
            affected_blueprints=roadmaps,
            changed_files=todo_changes,
            severity="review_suggested",
        )
    ]


def _route_architecture_drift(
    *,
    project_id: str,
    changed_files: list[str],
    blueprint_changed: set[str],
) -> list[DriftFinding]:
    route_changes = [
        path for path in changed_files if path.startswith("src/app/") and path.endswith("/route.ts")
    ]
    if not route_changes or "system-state" in blueprint_changed:
        return []

    return [
        _finding(
            project_id=project_id,
            component="architecture",
            reason="route_changed",
            affected_blueprints=["system-state"],
            changed_files=route_changes,
            severity="review_suggested",
        )
    ]


def _api_qa_gap(
    *,
    project_id: str,
    blueprints: list[BlueprintRecord],
    changed_files: list[str],
    blueprint_changed: set[str],
) -> list[DriftFinding]:
    api_changes = [
        path
        for path in changed_files
        if path.startswith("src/app/api/") and path.endswith("/route.ts")
    ]
    if not api_changes:
        return []

    runbooks = [
        blueprint.blueprint_id
        for blueprint in blueprints
        if blueprint.status == "runbook" and blueprint.blueprint_id not in blueprint_changed
    ]
    if not runbooks:
        return []

    return [
        _finding(
            project_id=project_id,
            component="qa",
            reason="api_changed_without_manual_checklist_update",
            affected_blueprints=runbooks,
            changed_files=api_changes,
            severity="action_recommended",
        )
    ]


def _cartographer_api_runbook_gap(
    *,
    project_id: str,
    blueprints: list[BlueprintRecord],
    changed_files: list[str],
    blueprint_changed: set[str],
) -> list[DriftFinding]:
    route_changes = [
        path
        for path in changed_files
        if path.startswith("src/app/v1/cartographer/")
    ]
    if not route_changes or _runbook_changed(changed_files):
        return []

    runbooks = [
        blueprint.blueprint_id
        for blueprint in blueprints
        if blueprint.status == "runbook" and blueprint.blueprint_id not in blueprint_changed
    ]
    if not runbooks:
        return []

    return [
        _finding(
            project_id=project_id,
            component="cartographer-api-bridge",
            reason="runbook_gap",
            affected_blueprints=runbooks,
            changed_files=route_changes,
            severity="action_recommended",
        )
    ]


def _dashboard_qa_gap(
    *,
    project_id: str,
    blueprints: list[BlueprintRecord],
    changed_files: list[str],
    blueprint_changed: set[str],
) -> list[DriftFinding]:
    dashboard_changes = [
        path
        for path in changed_files
        if path.startswith("src/components/dashboard/")
    ]
    if not dashboard_changes or _runbook_changed(changed_files):
        return []

    target_runbooks = [
        blueprint.blueprint_id
        for blueprint in blueprints
        if blueprint.blueprint_id == "cartographer-dashboard-mobile-qa"
        and blueprint.blueprint_id not in blueprint_changed
    ]
    if not target_runbooks:
        return []

    return [
        _finding(
            project_id=project_id,
            component="dashboard",
            reason="qa_gap",
            affected_blueprints=target_runbooks,
            changed_files=dashboard_changes,
            severity="action_recommended",
        )
    ]


def _safety_test_gap(
    *,
    project_id: str,
    changed_files: list[str],
) -> list[DriftFinding]:
    safety_changes = [
        path
        for path in changed_files
        if (
            path.startswith("source_proxy/approval/")
            or path in {
                "source_proxy/cartographer/apply.py",
                "source_proxy/cartographer/commit_proposals.py",
                "source_proxy/cartographer/push_queue.py",
                "source_proxy/cartographer/safety.py",
            }
        )
    ]
    if not safety_changes:
        return []
    if any(path.startswith("source_proxy/tests/") and "safety" in path for path in changed_files):
        return []

    return [
        _finding(
            project_id=project_id,
            component="safety",
            reason="safety_gap",
            affected_blueprints=["system-state"],
            changed_files=safety_changes,
            severity="action_recommended",
        )
    ]


def _scout_doc_drift(
    *,
    project_id: str,
    changed_files: list[str],
    blueprint_changed: set[str],
) -> list[DriftFinding]:
    scout_changes = [
        path
        for path in changed_files
        if path.startswith("scout/") and not path.startswith("scout/docs/")
    ]
    if not scout_changes:
        return []
    if any(path.startswith("scout/docs/") or path.startswith("docs/scout") for path in changed_files):
        return []
    if "system-state" in blueprint_changed:
        return []

    return [
        _finding(
            project_id=project_id,
            component="scout",
            reason="scout_doc_drift",
            affected_blueprints=["system-state"],
            changed_files=scout_changes,
            severity="review_suggested",
        )
    ]


def _changed_blueprint_ids(
    blueprints: list[BlueprintRecord], changed_files: list[str]
) -> set[str]:
    changed = set(changed_files)
    return {
        blueprint.blueprint_id
        for blueprint in blueprints
        if f"_blueprints/{blueprint.path}" in changed
    }


def _runbook_changed(changed_files: list[str]) -> bool:
    return any(path.startswith("_blueprints/runbooks/") for path in changed_files)


def _finding(
    *,
    project_id: str,
    component: str,
    reason: str,
    affected_blueprints: list[str],
    changed_files: list[str],
    severity: str,
) -> DriftFinding:
    normalized_files = sorted({_normalize_repo_path(path) for path in changed_files})
    normalized_blueprints = sorted(set(affected_blueprints))
    drift_key = "|".join(
        [project_id, component, reason, ",".join(normalized_blueprints), ",".join(normalized_files)]
    )
    return DriftFinding(
        project_id=project_id,
        drift_id=sha256(drift_key.encode("utf-8")).hexdigest()[:16],
        component=component,
        reason=reason,
        affected_blueprints=normalized_blueprints,
        changed_files=normalized_files,
        message=_message_for_reason(reason),
        evidence=_evidence_for_finding(
            reason=reason,
            affected_blueprints=normalized_blueprints,
            changed_files=normalized_files,
        ),
        severity=severity,  # type: ignore[arg-type]
    )


def _message_for_reason(reason: str) -> str:
    if reason == "component_code_changed":
        return "This code changed. This blueprint may now be stale."
    if reason == "readme_changed":
        return "README changed. Current blueprints may need review."
    if reason == "todo_changed":
        return "Planning notes changed. Roadmap blueprints may need review."
    if reason == "route_changed":
        return "A route changed. Architecture documentation may now be stale."
    if reason == "api_changed_without_manual_checklist_update":
        return "An API route changed. Manual QA runbooks may need an update."
    if reason == "runbook_gap":
        return "A Cartographer API route changed. Operating runbooks may need an update."
    if reason == "qa_gap":
        return "Dashboard UI changed. Manual QA notes may need an update."
    if reason == "safety_gap":
        return "Safety-sensitive code changed without a matching safety test update."
    if reason == "scout_doc_drift":
        return "Scout changed. Scout documentation or system blueprints may need review."
    return "Repository state changed. Blueprint review may be needed."


def _evidence_for_finding(
    *,
    reason: str,
    affected_blueprints: list[str],
    changed_files: list[str],
) -> list[str]:
    evidence = [f"rule: {reason}"]
    evidence.extend(f"changed file: {path}" for path in changed_files[:8])
    evidence.extend(f"affected blueprint: {blueprint}" for blueprint in affected_blueprints)
    return evidence


def _append_unique(
    findings: list[DriftFinding], seen: set[str], finding: DriftFinding
) -> None:
    if finding.drift_id in seen:
        return
    seen.add(finding.drift_id)
    findings.append(finding)


def _normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized
