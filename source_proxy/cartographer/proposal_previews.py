from __future__ import annotations

from difflib import unified_diff
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from source_proxy.cartographer.blueprint_registry import list_blueprints
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.models import BlueprintRecord, DriftFinding, ProposalRecord, ProposalTransition
from source_proxy.cartographer.project_discovery import discover_projects


def draft_proposals_from_drift() -> list[ProposalRecord]:
    blueprints_by_key = {
        (blueprint.project_id, blueprint.blueprint_id): blueprint
        for blueprint in list_blueprints()
    }
    project_roots = {project.project_id: Path(project.root) for project in discover_projects()}
    proposals: list[ProposalRecord] = []
    for finding in detect_blueprint_drift():
        proposed_files = _proposed_files_for_finding(finding, blueprints_by_key)
        if not proposed_files:
            continue
        fingerprint = proposal_fingerprint(
            project_id=finding.project_id,
            proposal_type="blueprint_update",
            component=finding.component,
            reason=finding.reason,
            changed_files=finding.changed_files,
            proposed_files=proposed_files,
            affected_blueprints=finding.affected_blueprints,
        )
        proposal_id = proposal_id_from_fingerprint(
            project_id=finding.project_id,
            component=finding.component,
            reason=finding.reason,
            fingerprint=fingerprint,
        )
        proposals.append(
            ProposalRecord(
                proposal_id=proposal_id,
                project_id=finding.project_id,
                status="drafted",
                type="blueprint_update",
                component=finding.component,
                requires_approval=True,
                title=f"Draft blueprint update for {finding.component}",
                affected_blueprints=finding.affected_blueprints,
                changed_files=finding.changed_files,
                proposed_files=proposed_files,
                diff_preview=_diff_preview(finding, proposed_files, project_roots.get(finding.project_id)),
                confidence="medium",
                rationale=_rationale(finding),
                source_drift_id=finding.drift_id,
                generated=True,
                persisted=False,
                fingerprint=fingerprint,
                deduped=True,
                transitions=[
                    ProposalTransition(
                        status="drafted",
                        timestamp=_now_timestamp(),
                        actor="cartographer",
                    )
                ],
            )
        )
    return proposals


def _proposed_files_for_finding(
    finding: DriftFinding,
    blueprints_by_key: dict[tuple[str, str], BlueprintRecord],
) -> list[str]:
    proposed_files: list[str] = []
    for blueprint_id in finding.affected_blueprints:
        blueprint = blueprints_by_key.get((finding.project_id, blueprint_id))
        if not blueprint:
            continue
        proposed_files.append(f"_blueprints/{blueprint.path}")
    return sorted(set(proposed_files))


def _diff_preview(finding: DriftFinding, proposed_files: list[str], project_root: Path | None) -> str:
    lines: list[str] = []
    for proposed_file in proposed_files:
        lines.extend(_diff_for_file(finding, proposed_file, project_root))
    return "\n".join(lines).rstrip()


def _diff_for_file(finding: DriftFinding, proposed_file: str, project_root: Path | None) -> list[str]:
    note = [
        "",
        "### Cartographer Review Note",
        f"- Reason: {_redact(finding.reason)}.",
        f"- Component: {_redact(finding.component)}.",
        f"- Changed files: {', '.join(_redact(path) for path in finding.changed_files[:8])}.",
        "- Manual check: confirm this blueprint still matches the changed implementation.",
    ]
    if project_root is None:
        return _fallback_preview(finding, proposed_file)

    target = (project_root / proposed_file).resolve()
    try:
        original = target.read_text(encoding="utf-8")
    except OSError:
        return _fallback_preview(finding, proposed_file)

    original_lines = original.splitlines()
    updated_lines = [*original_lines, *note]
    diff_lines = [
        line
        for line in unified_diff(
            original_lines,
            updated_lines,
            fromfile=f"a/{proposed_file}",
            tofile=f"b/{proposed_file}",
            lineterm="",
        )
    ]
    return [f"diff --git a/{proposed_file} b/{proposed_file}", *diff_lines]


def _fallback_preview(finding: DriftFinding, proposed_file: str) -> list[str]:
    return [
        f"diff --git a/{proposed_file} b/{proposed_file}",
        f"--- a/{proposed_file}",
        f"+++ b/{proposed_file}",
        "@@",
        f"+### Cartographer Review Note",
        f"+- Reason: {_redact(finding.reason)}.",
        f"+- Component: {_redact(finding.component)}.",
        f"+- Changed files: {', '.join(_redact(path) for path in finding.changed_files[:8])}.",
        "+- Manual check: confirm this blueprint still matches the changed implementation.",
        "",
    ]


def _rationale(finding: DriftFinding) -> str:
    return (
        f"{finding.reason} affected {finding.component}; "
        "Cartographer drafted a doc-only preview for dashboard review."
    )


def proposal_fingerprint(
    *,
    project_id: str,
    proposal_type: str,
    component: str,
    reason: str,
    changed_files: list[str],
    proposed_files: list[str],
    affected_blueprints: list[str],
) -> str:
    changed_hash = sha256("\n".join(sorted(set(changed_files))).encode("utf-8")).hexdigest()[:12]
    target_hash = sha256("\n".join(sorted(set(proposed_files))).encode("utf-8")).hexdigest()[:12]
    key = {
        "project_id": project_id,
        "proposal_type": proposal_type,
        "component": component,
        "reason": reason,
        "changed_files_hash": changed_hash,
        "target_files_hash": target_hash,
        "affected_blueprints": sorted(set(affected_blueprints)),
    }
    return sha256(repr(sorted(key.items())).encode("utf-8")).hexdigest()[:16]


def proposal_id_from_fingerprint(
    *,
    project_id: str,
    component: str,
    reason: str,
    fingerprint: str,
) -> str:
    return f"bp-{_slug(project_id)}-{_slug(component)}-{_slug(reason)}-{fingerprint[:8]}"


def _slug(value: str) -> str:
    return "-".join(part for part in "".join(char if char.isalnum() else "-" for char in value.lower()).split("-") if part) or "unknown"


def _redact(value: str) -> str:
    lowered = value.lower()
    if any(token in lowered for token in ("secret", "token", "password", ".env")):
        return "[redacted]"
    return value


def _now_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
