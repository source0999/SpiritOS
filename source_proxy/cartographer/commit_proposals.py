from __future__ import annotations

from hashlib import sha256

from source_proxy.cartographer.component_mapper import map_paths
from source_proxy.cartographer.git_status import read_git_statuses
from source_proxy.cartographer.models import CommitProposal, GitStatus, ProposalRecord
from source_proxy.cartographer.proposals import list_proposals


COMMIT_READY_STATES = {"applied", "commit_pending"}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "blocked": 3, "unknown": 4}


def build_commit_proposals() -> list[CommitProposal]:
    git_by_project = {
        status.project_id: status
        for status in read_git_statuses()
        if status.project_id and status.available
    }
    proposals: list[CommitProposal] = []
    claimed_files_by_project: dict[str, set[str]] = {}
    for proposal in list_proposals():
        if proposal.status not in COMMIT_READY_STATES:
            continue
        git_status = git_by_project.get(proposal.project_id)
        if not git_status:
            continue
        files = _commit_files(proposal, git_status)
        if not files:
            continue
        proposals.append(_commit_proposal(proposal, files, git_status))
        claimed_files_by_project.setdefault(proposal.project_id, set()).update(files)

    for project_id, git_status in git_by_project.items():
        claimed_files = claimed_files_by_project.get(project_id, set())
        remaining_files = [
            _normalize_repo_path(path)
            for path in git_status.changed_files
            if _normalize_repo_path(path) not in claimed_files
        ]
        proposals.extend(_dirty_tree_commit_proposals(git_status, remaining_files))

    return proposals


def _commit_files(proposal: ProposalRecord, git_status: GitStatus) -> list[str]:
    changed = {_normalize_repo_path(path) for path in git_status.changed_files}
    proposed = [_normalize_repo_path(path) for path in proposal.proposed_files]
    if proposed:
        return [path for path in proposed if path in changed]
    return sorted(changed)


def _commit_proposal(
    proposal: ProposalRecord,
    files: list[str],
    git_status: GitStatus,
) -> CommitProposal:
    component, risk = _component_and_risk(files)
    staged_files, unstaged_files, untracked_files = _status_buckets(files, git_status)
    return CommitProposal(
        commit_proposal_id=_commit_proposal_id(proposal, files),
        project_id=proposal.project_id,
        source_proposal_id=proposal.proposal_id,
        status="commit_pending",
        suggested_message=_suggested_message(proposal),
        files=files,
        reason=(
            f"Proposal {proposal.proposal_id} is {proposal.status}; "
            "package reviewed files into a commit only after approval."
        ),
        component=component,
        risk=risk,
        generated=False,
        staged_files=staged_files,
        unstaged_files=unstaged_files,
        untracked_files=untracked_files,
        editable=True,
        requires_approval=True,
        commit_enabled=False,
        action_taken=False,
    )


def _dirty_tree_commit_proposals(
    git_status: GitStatus,
    changed_files: list[str],
) -> list[CommitProposal]:
    grouped: dict[tuple[str, str, str], list[str]] = {}
    for path in sorted(dict.fromkeys(changed_files)):
        component, risk = _component_and_risk([path])
        purpose = _purpose_for_path(path)
        grouped.setdefault((component, risk, purpose), []).append(path)

    proposals: list[CommitProposal] = []
    for (component, risk, purpose), files in sorted(grouped.items()):
        staged_files, unstaged_files, untracked_files = _status_buckets(files, git_status)
        proposals.append(
            CommitProposal(
                commit_proposal_id=_dirty_commit_proposal_id(
                    git_status.project_id or "unknown",
                    component,
                    risk,
                    purpose,
                    files,
                ),
                project_id=git_status.project_id or "unknown",
                source_proposal_id="dirty-tree",
                status="commit_pending",
                suggested_message=_dirty_tree_message(component, risk, purpose),
                files=files,
                reason=(
                    "Dirty tree files are grouped by component, risk, and purpose; "
                    "stage and commit only after explicit approval."
                ),
                component=component,
                risk=risk,
                generated=True,
                staged_files=staged_files,
                unstaged_files=unstaged_files,
                untracked_files=untracked_files,
                editable=True,
                requires_approval=True,
                commit_enabled=False,
                action_taken=False,
            )
        )
    return proposals


def _suggested_message(proposal: ProposalRecord) -> str:
    if proposal.type == "starter_blueprint_pack":
        return "docs(cartographer): add starter blueprint pack"
    if proposal.component and proposal.component != "unknown":
        return f"docs({proposal.component}): apply cartographer blueprint update"
    return "docs(cartographer): apply approved blueprint update"


def _commit_proposal_id(proposal: ProposalRecord, files: list[str]) -> str:
    key = "|".join([proposal.project_id, proposal.proposal_id, ",".join(files)])
    return f"commit-prop-{sha256(key.encode('utf-8')).hexdigest()[:12]}"


def _dirty_commit_proposal_id(
    project_id: str,
    component: str,
    risk: str,
    purpose: str,
    files: list[str],
) -> str:
    key = "|".join([project_id, component, risk, purpose, ",".join(files)])
    return f"commit-prop-{sha256(key.encode('utf-8')).hexdigest()[:12]}"


def _component_and_risk(files: list[str]) -> tuple[str, str]:
    components, unmapped = map_paths(files)
    if components:
        component = components[0].component_id
        risks = [component.risk for component in components]
        for item in components:
            risks.extend(item.matched_path_risks.values())
    else:
        component = "unknown"
        risks = [item.risk for item in unmapped] or ["unknown"]
    return component, _max_risk(risks)


def _status_buckets(
    files: list[str],
    git_status: GitStatus,
) -> tuple[list[str], list[str], list[str]]:
    staged = {_normalize_repo_path(item) for item in git_status.staged_files}
    unstaged = {_normalize_repo_path(item) for item in git_status.unstaged_files}
    untracked = {_normalize_repo_path(item) for item in git_status.untracked_files}
    return (
        [path for path in files if path in staged],
        [path for path in files if path in unstaged],
        [path for path in files if path in untracked],
    )


def _purpose_for_path(path: str) -> str:
    lowered = path.lower()
    if "soak-log" in lowered or "/soak-logs/" in lowered:
        return "soak"
    if lowered.startswith("docs/") or lowered.startswith("_blueprints/") or lowered.endswith(".md"):
        return "docs"
    if "/tests/" in lowered or "/__tests__/" in lowered or lowered.endswith(".test.ts") or lowered.endswith("_test.py"):
        return "test"
    return "code"


def _dirty_tree_message(component: str, risk: str, purpose: str) -> str:
    scope = _commit_scope(component)
    prefix = "docs" if purpose in {"docs", "soak"} else "test" if purpose == "test" else "feat"
    if purpose == "soak":
        return f"chore({scope}): record soak snapshot"
    if risk in {"high", "blocked"}:
        return f"chore({scope}): isolate {risk}-risk changes"
    return f"{prefix}({scope}): update {component.replace('-', ' ')}"


def _commit_scope(component: str) -> str:
    if component in {"blueprint-system", "cartographer-api-bridge"}:
        return "cartographer"
    return component.replace("_", "-") or "work"


def _max_risk(risks: list[str]) -> str:
    return max(risks, key=lambda risk: RISK_ORDER.get(risk, RISK_ORDER["unknown"]))


def _normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if normalized.startswith("a/") or normalized.startswith("b/"):
        normalized = normalized[2:]
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized
