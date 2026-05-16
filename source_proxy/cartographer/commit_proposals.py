from __future__ import annotations

from hashlib import sha256

from source_proxy.cartographer.git_status import read_git_statuses
from source_proxy.cartographer.models import CommitProposal, GitStatus, ProposalRecord
from source_proxy.cartographer.proposals import list_proposals


COMMIT_READY_STATES = {"applied", "commit_pending"}


def build_commit_proposals() -> list[CommitProposal]:
    git_by_project = {
        status.project_id: status
        for status in read_git_statuses()
        if status.project_id and status.available
    }
    proposals: list[CommitProposal] = []
    for proposal in list_proposals():
        if proposal.status not in COMMIT_READY_STATES:
            continue
        git_status = git_by_project.get(proposal.project_id)
        if not git_status:
            continue
        files = _commit_files(proposal, git_status)
        if not files:
            continue
        proposals.append(_commit_proposal(proposal, files))
    return proposals


def _commit_files(proposal: ProposalRecord, git_status: GitStatus) -> list[str]:
    changed = {_normalize_repo_path(path) for path in git_status.changed_files}
    proposed = [_normalize_repo_path(path) for path in proposal.proposed_files]
    if proposed:
        return [path for path in proposed if path in changed]
    return sorted(changed)


def _commit_proposal(proposal: ProposalRecord, files: list[str]) -> CommitProposal:
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
        editable=True,
        requires_approval=True,
        commit_enabled=False,
        action_taken=False,
    )


def _suggested_message(proposal: ProposalRecord) -> str:
    if proposal.type == "starter_blueprint_pack":
        return "docs(cartographer): add starter blueprint pack"
    if proposal.component and proposal.component != "unknown":
        return f"docs({proposal.component}): apply cartographer blueprint update"
    return "docs(cartographer): apply approved blueprint update"


def _commit_proposal_id(proposal: ProposalRecord, files: list[str]) -> str:
    key = "|".join([proposal.project_id, proposal.proposal_id, ",".join(files)])
    return f"commit-prop-{sha256(key.encode('utf-8')).hexdigest()[:12]}"


def _normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if normalized.startswith("a/") or normalized.startswith("b/"):
        normalized = normalized[2:]
    return normalized.lstrip("./")
