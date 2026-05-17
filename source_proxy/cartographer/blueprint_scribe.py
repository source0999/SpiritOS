from __future__ import annotations

from hashlib import sha256

from source_proxy.cartographer.blueprint_registry import list_blueprints
from source_proxy.cartographer.change_scribe import summarize_changes
from source_proxy.cartographer.codex_evidence import build_codex_evidence_rollup
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
    drafts.extend(_codex_trial_summary_drafts(list(blueprints.values())))
    return drafts


def draft_codex_trial_summary_updates() -> list[BlueprintScribeDraft]:
    return _codex_trial_summary_drafts(list_blueprints())


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


def _codex_trial_summary_drafts(blueprints: list[BlueprintRecord]) -> list[BlueprintScribeDraft]:
    rollup = build_codex_evidence_rollup()
    if not rollup["evidence_count"]:
        return []
    if any(rollup[name] for name in ("approval_authority", "apply_authority", "commit_authority", "push_authority")):
        return []

    targets = _codex_summary_targets(blueprints)
    return [_draft_for_codex_rollup(rollup, blueprint) for blueprint in targets]


def _codex_summary_targets(blueprints: list[BlueprintRecord]) -> list[BlueprintRecord]:
    preferred_ids = ["cartographer-agent", "cartographer-manual-checks"]
    by_id = {blueprint.blueprint_id: blueprint for blueprint in blueprints}
    return [by_id[blueprint_id] for blueprint_id in preferred_ids if blueprint_id in by_id]


def _draft_for_codex_rollup(rollup: dict[str, object], blueprint: BlueprintRecord) -> BlueprintScribeDraft:
    changed_files = [str(path) for path in rollup["changed_files"]]  # type: ignore[index]
    evidence_count = int(rollup["evidence_count"])
    latest_task_ids = [str(task_id) for task_id in rollup["latest_task_ids"]]  # type: ignore[index]
    risk_labels = [str(risk) for risk in rollup["risk_labels"]]  # type: ignore[index]
    proposed_file = f"_blueprints/{blueprint.path}"
    key = "|".join(
        [
            blueprint.project_id,
            blueprint.blueprint_id,
            str(evidence_count),
            ",".join(latest_task_ids),
            ",".join(changed_files),
        ]
    )
    return BlueprintScribeDraft(
        proposal_id=f"bp-scribe-codex-{sha256(key.encode('utf-8')).hexdigest()[:12]}",
        project_id=blueprint.project_id,
        component="codex-adapter",
        affected_blueprint=blueprint.blueprint_id,
        proposed_file=proposed_file,
        suggested_update=(
            f"Update {blueprint.path} with the Codex adapter trial summary: "
            f"{evidence_count} evidence record(s), latest tasks {', '.join(latest_task_ids[-5:])}, "
            "proposal-only evidence capture, known read-only shell limitation, and manual checks."
        ),
        confidence="medium",
        reason="codex_trial_summary_ready maps clean Codex evidence into proposal-only blueprint review.",
        evidence=[
            f"codex evidence count: {evidence_count}",
            f"latest task ids: {', '.join(latest_task_ids[-5:])}",
            f"risk labels: {', '.join(risk_labels) or 'not reported'}",
            "approval/apply/commit/push authority: false",
            *[f"changed file: {path}" for path in changed_files[:8]],
        ],
        changed_files=changed_files,
        avoids_overclaiming=[
            "Draft is based on Codex evidence artifacts and the trial closeout only.",
            "It does not treat Codex evidence as approval.",
            "Human review must approve any blueprint apply separately.",
        ],
        editable=True,
        rejectable=True,
        requires_apply_approval=True,
        action_taken=False,
    )
