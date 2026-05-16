from __future__ import annotations

from hashlib import sha256

from source_proxy.cartographer.blueprint_registry import list_blueprints
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.models import BlueprintRecord, DriftFinding, ProposalRecord, ProposalTransition


def draft_proposals_from_drift() -> list[ProposalRecord]:
    blueprints_by_key = {
        (blueprint.project_id, blueprint.blueprint_id): blueprint
        for blueprint in list_blueprints()
    }
    proposals: list[ProposalRecord] = []
    for finding in detect_blueprint_drift():
        proposed_files = _proposed_files_for_finding(finding, blueprints_by_key)
        if not proposed_files:
            continue
        proposal_id = _proposal_id(finding, proposed_files)
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
                diff_preview=_diff_preview(finding, proposed_files),
                confidence="medium",
                rationale=_rationale(finding),
                generated=True,
                persisted=False,
                transitions=[
                    ProposalTransition(
                        status="drafted",
                        timestamp=None,
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


def _diff_preview(finding: DriftFinding, proposed_files: list[str]) -> str:
    lines: list[str] = []
    for proposed_file in proposed_files:
        lines.extend(
            [
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
        )
    return "\n".join(lines).rstrip()


def _rationale(finding: DriftFinding) -> str:
    return (
        f"{finding.reason} affected {finding.component}; "
        "Cartographer drafted a doc-only preview for dashboard review."
    )


def _proposal_id(finding: DriftFinding, proposed_files: list[str]) -> str:
    key = "|".join(
        [
            finding.project_id,
            finding.drift_id,
            ",".join(finding.affected_blueprints),
            ",".join(proposed_files),
        ]
    )
    return f"bp-{sha256(key.encode('utf-8')).hexdigest()[:12]}"


def _redact(value: str) -> str:
    lowered = value.lower()
    if any(token in lowered for token in ("secret", "token", "password", ".env")):
        return "[redacted]"
    return value
