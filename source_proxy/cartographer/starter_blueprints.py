from __future__ import annotations

from hashlib import sha256

from source_proxy.cartographer.models import ProjectCandidate, ProposalRecord, ProposalTransition
from source_proxy.cartographer.project_discovery import discover_project_candidates


STARTER_BLUEPRINT_FILES = [
    "_blueprints/INDEX.md",
    "_blueprints/current/project_state.md",
    "_blueprints/components/app.md",
    "_blueprints/runbooks/manual_checks.md",
    "TODO.md",
]


def draft_starter_blueprint_pack_proposals() -> list[ProposalRecord]:
    return [_proposal_for_candidate(candidate) for candidate in discover_project_candidates()]


def _proposal_for_candidate(candidate: ProjectCandidate) -> ProposalRecord:
    proposal_id = _proposal_id(candidate)
    return ProposalRecord(
        proposal_id=proposal_id,
        project_id=candidate.project_id,
        status="drafted",
        type="starter_blueprint_pack",
        component="project-onboarding",
        requires_approval=True,
        title=f"Starter blueprint pack for {candidate.name}",
        affected_blueprints=[],
        changed_files=[],
        proposed_files=STARTER_BLUEPRINT_FILES,
        diff_preview=_diff_preview(candidate),
        confidence="medium",
        rationale=(
            f"{candidate.name} was detected under an allowlisted root with markers: "
            f"{', '.join(candidate.markers)}. Cartographer drafted starter docs only."
        ),
        generated=True,
        persisted=False,
        transitions=[
            ProposalTransition(
                status="drafted",
                timestamp=None,
                actor="cartographer",
            )
        ],
        action_taken=False,
    )


def _diff_preview(candidate: ProjectCandidate) -> str:
    snippets = {
        "_blueprints/INDEX.md": _index_doc(candidate),
        "_blueprints/current/project_state.md": _project_state_doc(candidate),
        "_blueprints/components/app.md": _app_component_doc(candidate),
        "_blueprints/runbooks/manual_checks.md": _manual_checks_doc(candidate),
        "TODO.md": _todo_doc(candidate),
    }
    lines: list[str] = []
    for path in STARTER_BLUEPRINT_FILES:
        lines.extend(
            [
                f"diff --git a/{path} b/{path}",
                "new file mode 100644",
                "--- /dev/null",
                f"+++ b/{path}",
                "@@",
            ]
        )
        lines.extend(f"+{line}" for line in snippets[path].splitlines())
        lines.append("")
    return "\n".join(lines).rstrip()


def _index_doc(candidate: ProjectCandidate) -> str:
    return "\n".join(
        [
            f"# {candidate.name} Blueprint Index",
            "",
            "| Document | Classification | Notes |",
            "| --- | --- | --- |",
            "| `current/project_state.md` | current truth | Starter current-state record. |",
            "| `components/app.md` | component blueprint | Starter app component map. |",
            "| `runbooks/manual_checks.md` | manual QA/runbook | Starter manual verification checklist. |",
        ]
    )


def _project_state_doc(candidate: ProjectCandidate) -> str:
    markers = ", ".join(candidate.markers) or "none"
    return "\n".join(
        [
            "---",
            "blueprint_id: project-state",
            f"title: {candidate.name} Project State",
            f"project: {candidate.name}",
            "component: system",
            "doc_type: current_state",
            "status: active",
            "source_of_truth: true",
            "owner: Britton",
            "code_paths:",
            "  - \"**\"",
            "related_blueprints:",
            "  - app",
            "write_policy: proposal_only_until_dashboard_approved",
            "last_verified: 2026-05-16",
            "---",
            "",
            f"# {candidate.name} Project State",
            "",
            f"Starter state drafted from detected markers: {markers}.",
        ]
    )


def _app_component_doc(candidate: ProjectCandidate) -> str:
    return "\n".join(
        [
            "---",
            "blueprint_id: app",
            f"title: {candidate.name} App Component",
            f"project: {candidate.name}",
            "component: app",
            "doc_type: component_blueprint",
            "status: planned",
            "source_of_truth: false",
            "owner: Britton",
            "code_paths:",
            "  - src/**",
            "  - app/**",
            "related_blueprints:",
            "  - project-state",
            "write_policy: proposal_only_until_dashboard_approved",
            "last_verified: 2026-05-16",
            "---",
            "",
            f"# {candidate.name} App Component",
            "",
            "Document the primary app surfaces after human review.",
        ]
    )


def _manual_checks_doc(candidate: ProjectCandidate) -> str:
    return "\n".join(
        [
            "---",
            "blueprint_id: manual-checks",
            f"title: {candidate.name} Manual Checks",
            f"project: {candidate.name}",
            "component: qa",
            "doc_type: runbook",
            "status: runbook",
            "source_of_truth: false",
            "owner: Britton",
            "code_paths:",
            "  - \"**\"",
            "related_blueprints:",
            "  - project-state",
            "write_policy: proposal_only_until_dashboard_approved",
            "last_verified: 2026-05-16",
            "---",
            "",
            f"# {candidate.name} Manual Checks",
            "",
            "- Open the project locally.",
            "- Confirm the primary app or service starts without errors.",
            "- Confirm no commit or push occurs during onboarding review.",
        ]
    )


def _todo_doc(candidate: ProjectCandidate) -> str:
    return "\n".join(
        [
            f"# {candidate.name} TODO",
            "",
            "- Review starter blueprint pack.",
            "- Replace placeholder component coverage with project-specific ownership.",
            "- Add first manual verification result.",
        ]
    )


def _proposal_id(candidate: ProjectCandidate) -> str:
    key = "|".join([candidate.project_id, candidate.root, ",".join(candidate.markers)])
    return f"bp-starter-{sha256(key.encode('utf-8')).hexdigest()[:12]}"
