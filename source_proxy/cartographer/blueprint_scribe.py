from __future__ import annotations

from hashlib import sha256

from source_proxy.cartographer.blueprint_registry import list_blueprints
from source_proxy.cartographer.change_scribe import summarize_changes
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.models import BlueprintRecord, BlueprintScribeDraft, ChangeScribeSummary, DriftFinding


def draft_blueprint_updates() -> list[BlueprintScribeDraft]:
    blueprints = {
        (blueprint.project_id, blueprint.blueprint_id): blueprint
        for blueprint in list_blueprints()
    }
    summaries = {
        summary.project_id: summary
        for summary in summarize_changes()
    }
    drafts: list[BlueprintScribeDraft] = []
    for finding in detect_blueprint_drift():
        summary = summaries.get(finding.project_id)
        for blueprint_id in finding.affected_blueprints:
            blueprint = blueprints.get((finding.project_id, blueprint_id))
            if not blueprint:
                continue
            drafts.append(_draft_for_finding(finding, blueprint, summary))
    return drafts


def _draft_for_finding(
    finding: DriftFinding,
    blueprint: BlueprintRecord,
    summary: ChangeScribeSummary | None,
) -> BlueprintScribeDraft:
    proposed_file = f"_blueprints/{blueprint.path}"
    reason = _reason(finding, blueprint, summary)
    return BlueprintScribeDraft(
        proposal_id=_proposal_id(finding, blueprint),
        project_id=finding.project_id,
        component=finding.component,
        affected_blueprint=blueprint.blueprint_id,
        proposed_file=proposed_file,
        suggested_update=_suggested_update(finding, blueprint),
        confidence="medium",
        reason=reason,
        evidence=_evidence(finding, blueprint, summary),
        changed_files=finding.changed_files,
        avoids_overclaiming=[
            "Draft is based on Git paths, drift rules, and blueprint metadata only.",
            "It does not claim runtime behavior changed unless a changed file path directly supports review.",
            "Human review can edit or reject before any file apply is possible.",
        ],
        editable=True,
        rejectable=True,
        requires_apply_approval=True,
        action_taken=False,
    )


def _suggested_update(finding: DriftFinding, blueprint: BlueprintRecord) -> str:
    changed = ", ".join(finding.changed_files[:3]) or "the changed implementation files"
    if finding.reason == "component_code_changed":
        return (
            f"Update {blueprint.path} to review the {finding.component} changes touching {changed}."
        )
    if finding.reason == "route_changed":
        return f"Update {blueprint.path} to review the route/API surface changed by {changed}."
    if finding.reason == "api_changed_without_manual_checklist_update":
        return f"Update {blueprint.path} with a manual QA note for {changed}."
    return f"Review {blueprint.path} against {changed}."


def _reason(
    finding: DriftFinding,
    blueprint: BlueprintRecord,
    summary: ChangeScribeSummary | None,
) -> str:
    base = (
        f"{finding.reason} maps to source-of-truth blueprint {blueprint.blueprint_id}."
    )
    if summary and summary.summary:
        return f"{base} Change Scribe observed: {summary.summary}"
    return base


def _evidence(
    finding: DriftFinding,
    blueprint: BlueprintRecord,
    summary: ChangeScribeSummary | None,
) -> list[str]:
    evidence = [
        f"affected blueprint: {blueprint.blueprint_id}",
        f"proposed file: _blueprints/{blueprint.path}",
        f"drift reason: {finding.reason}",
    ]
    evidence.extend(f"changed file: {path}" for path in finding.changed_files[:8])
    if summary:
        evidence.extend(summary.evidence[:5])
    return list(dict.fromkeys(evidence))


def _proposal_id(finding: DriftFinding, blueprint: BlueprintRecord) -> str:
    key = "|".join(
        [finding.project_id, finding.drift_id, blueprint.blueprint_id, blueprint.path]
    )
    return f"bp-scribe-{sha256(key.encode('utf-8')).hexdigest()[:12]}"
