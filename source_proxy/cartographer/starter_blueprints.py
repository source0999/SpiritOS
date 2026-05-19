from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from source_proxy.cartographer.models import ProjectCandidate, ProposalRecord, ProposalTransition
from source_proxy.cartographer.project_discovery import discover_project_candidates


STARTER_BLUEPRINT_FILES = [
    "_blueprints/INDEX.md",
    "_blueprints/current/project_state.md",
    "_blueprints/components/app.md",
    "_blueprints/runbooks/manual_checks.md",
    "TODO.md",
]
APPROVED_STARTER_FILES = [
    "docs/blueprint.md",
    "docs/runbook.md",
    "docs/progress.md",
]
AUDIT_PATH = "data/approved_actions.audit.jsonl"


class StarterBlueprintWriteError(ValueError):
    def __init__(self, message: str, reason_code: str):
        super().__init__(message)
        self.reason_code = reason_code


def draft_starter_blueprint_pack_proposals() -> list[ProposalRecord]:
    return [_proposal_for_candidate(candidate) for candidate in discover_project_candidates()]


def write_approved_starter_blueprints(
    *,
    proposal_id: str,
    approved: bool,
    approved_by: str,
) -> dict[str, Any]:
    if approved is not True:
        raise StarterBlueprintWriteError(
            "approved must be true before starter blueprints can be written.",
            "approval_required",
        )
    candidate = _candidate_for_proposal(proposal_id)
    if candidate is None:
        raise StarterBlueprintWriteError("Starter blueprint proposal was not found.", "proposal_not_found")

    root = Path(candidate.root)
    before_files = _file_listing(root)
    docs = {
        "docs/blueprint.md": _approved_blueprint_doc(candidate),
        "docs/runbook.md": _approved_runbook_doc(candidate),
        "docs/progress.md": _approved_progress_doc(candidate),
    }
    for path, content in docs.items():
        if not _is_allowed_starter_path(path):
            raise StarterBlueprintWriteError(
                "Starter blueprint write attempted a forbidden path.",
                "starter_path_blocked",
            )
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    timestamp = _now_timestamp()
    _append_audit(
        root=root,
        payload={
            "event": "starter_blueprints_written",
            "action": "write approved starter blueprint docs",
            "approved_at": timestamp,
            "approved_by": approved_by or "cartographer-ui",
            "proposal_id": proposal_id,
            "project_id": candidate.project_id,
            "changed_files": APPROVED_STARTER_FILES,
            "result": "written",
            "committed": False,
            "pushed": False,
            "rollback_hint": "Review and remove docs/blueprint.md, docs/runbook.md, and docs/progress.md if this starter pack is not wanted.",
        },
    )
    after_files = _file_listing(root)
    return {
        "status": "starter_blueprints_written",
        "write_actions_enabled": True,
        "proposal_id": proposal_id,
        "project_id": candidate.project_id,
        "created_files": [path for path in APPROVED_STARTER_FILES if path not in before_files and path in after_files],
        "changed_files": APPROVED_STARTER_FILES,
        "audit_event": "starter_blueprints_written",
        "audit_path": AUDIT_PATH,
        "committed": False,
        "pushed": False,
        "rollback_hint": "Remove the created docs files after review if rollback is approved.",
        "actions_taken": True,
        "safety": {
            "allowed_files": APPROVED_STARTER_FILES,
            "app_code_allowed": False,
            "package_changes_allowed": False,
            "env_changes_allowed": False,
            "commit_enabled": False,
            "push_enabled": False,
        },
    }


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
        rationale=_rationale(candidate),
        repo_purpose=_repo_purpose(candidate),
        stack_guess=_stack_guess(candidate),
        scripts=_script_suggestions(candidate),
        components=_component_suggestions(candidate),
        risk_areas=_risk_areas(candidate),
        suggested_docs=STARTER_BLUEPRINT_FILES,
        suggested_tests=_test_suggestions(candidate),
        suggested_runbook=[
            "_blueprints/runbooks/manual_checks.md",
            "Confirm project start command after human review.",
            "Record first manual verification before any apply/commit/push.",
        ],
        generated=True,
        persisted=False,
        transitions=[
            ProposalTransition(
                status="drafted",
                timestamp=_now_timestamp(),
                actor="cartographer",
            )
        ],
        action_taken=False,
    )


def _candidate_for_proposal(proposal_id: str) -> ProjectCandidate | None:
    for candidate in discover_project_candidates():
        if _proposal_id(candidate) == proposal_id:
            return candidate
    return None


def _is_allowed_starter_path(path: str) -> bool:
    return path.replace("\\", "/").strip("/") in APPROVED_STARTER_FILES


def _file_listing(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def _append_audit(*, root: Path, payload: dict[str, Any]) -> None:
    audit_path = root / AUDIT_PATH
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


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


def _rationale(candidate: ProjectCandidate) -> str:
    return (
        f"{candidate.name} was detected under an allowlisted root with markers: "
        f"{', '.join(candidate.markers)}. Cartographer drafted starter docs only; "
        "repo purpose, stack, scripts, tests, and risks are marker-based suggestions for review."
    )


def _repo_purpose(candidate: ProjectCandidate) -> str:
    marker_set = set(candidate.markers)
    if "package.json" in marker_set and ("src" in marker_set or "app" in marker_set):
        return "Likely app or package project; confirm product purpose before writing starter docs."
    if "package.json" in marker_set:
        return "Likely package project; confirm product purpose before writing starter docs."
    if "pyproject.toml" in marker_set or "requirements.txt" in marker_set:
        return "Likely Python service or tool; confirm runtime and deployment purpose."
    if "README.md" in marker_set:
        return "Project purpose should be summarized from README after human review."
    return "Unknown project purpose; manual review required."


def _stack_guess(candidate: ProjectCandidate) -> str:
    marker_set = set(candidate.markers)
    guesses: list[str] = []
    if "package.json" in marker_set:
        guesses.append("Node/JavaScript or TypeScript")
    if "pyproject.toml" in marker_set:
        guesses.append("Python/pyproject")
    if "requirements.txt" in marker_set:
        guesses.append("Python/requirements")
    if "src" in marker_set:
        guesses.append("source-tree project")
    if "app" in marker_set:
        guesses.append("app-directory project")
    return ", ".join(guesses) if guesses else "unknown from markers"


def _script_suggestions(candidate: ProjectCandidate) -> list[str]:
    marker_set = set(candidate.markers)
    if "package.json" in marker_set:
        return ["inspect package.json scripts", "npm test or equivalent", "npm run build if present"]
    if "pyproject.toml" in marker_set or "requirements.txt" in marker_set:
        return ["inspect Python project scripts", "pytest if present", "python -m compileall for simple syntax check"]
    return ["identify start/test commands during onboarding review"]


def _component_suggestions(candidate: ProjectCandidate) -> list[str]:
    marker_set = set(candidate.markers)
    components = ["system"]
    if "src" in marker_set:
        components.append("src")
    if "app" in marker_set:
        components.append("app")
    if "tests" in marker_set:
        components.append("tests")
    return components


def _risk_areas(candidate: ProjectCandidate) -> list[str]:
    marker_set = set(candidate.markers)
    risks = ["new project not yet covered by source-of-truth blueprints"]
    if "package.json" in marker_set:
        risks.append("package scripts/dependencies need review before automation")
    if "pyproject.toml" in marker_set or "requirements.txt" in marker_set:
        risks.append("Python dependencies and test runner need review")
    if ".git" in marker_set:
        risks.append("Git state should stay read-only until starter docs are approved")
    return risks


def _test_suggestions(candidate: ProjectCandidate) -> list[str]:
    marker_set = set(candidate.markers)
    if "tests" in marker_set:
        return ["inspect existing tests", "record first passing test command"]
    if "package.json" in marker_set:
        return ["check for npm test", "add manual smoke checklist if no tests exist"]
    if "pyproject.toml" in marker_set or "requirements.txt" in marker_set:
        return ["check for pytest", "add manual smoke checklist if no tests exist"]
    return ["define first manual smoke test"]


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


def _approved_blueprint_doc(candidate: ProjectCandidate) -> str:
    return "\n".join(
        [
            f"# {candidate.name} Blueprint",
            "",
            f"- project_id: {candidate.project_id}",
            f"- markers: {', '.join(candidate.markers) or 'none'}",
            f"- confidence: {candidate.confidence}",
            f"- purpose: {_repo_purpose(candidate)}",
            f"- stack_guess: {_stack_guess(candidate)}",
            "",
            "## Components",
            *[f"- {component}" for component in _component_suggestions(candidate)],
            "",
            "## Risk Areas",
            *[f"- {risk}" for risk in _risk_areas(candidate)],
            "",
        ]
    )


def _approved_runbook_doc(candidate: ProjectCandidate) -> str:
    return "\n".join(
        [
            f"# {candidate.name} Runbook",
            "",
            "## Suggested Scripts",
            *[f"- {script}" for script in _script_suggestions(candidate)],
            "",
            "## Manual Checks",
            "- Confirm the project starts locally.",
            "- Record the first passing verification.",
            "- Confirm no commit or push is performed by starter onboarding.",
            "",
        ]
    )


def _approved_progress_doc(candidate: ProjectCandidate) -> str:
    return "\n".join(
        [
            f"# {candidate.name} Progress",
            "",
            "- Starter blueprint docs written after explicit approval.",
            "- Next: replace marker-based guesses with reviewed project facts.",
            "- Commit and push remain separate approvals.",
            "",
        ]
    )


def _proposal_id(candidate: ProjectCandidate) -> str:
    key = "|".join([candidate.project_id, candidate.root, ",".join(candidate.markers)])
    return f"bp-starter-{sha256(key.encode('utf-8')).hexdigest()[:12]}"


def _now_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
