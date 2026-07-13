from __future__ import annotations

from hashlib import sha256
from typing import Any

from source_proxy.cartographer.proposals import list_proposals


class CartographerProposalTransferError(ValueError):
    def __init__(self, message: str, reason_code: str):
        super().__init__(message)
        self.reason_code = reason_code


def transfer_proposal(*, proposal_id: str, consumer: str, target: str) -> dict[str, Any]:
    if consumer not in {"design-writeback", "coding-executor"}:
        raise CartographerProposalTransferError(
            "Cartographer transfers proposals only to registered mutation consumers.",
            "approval_consumer_mismatch",
        )
    proposal = next((item for item in list_proposals() if item.proposal_id == proposal_id), None)
    if proposal is None:
        raise CartographerProposalTransferError("Proposal was not found.", "proposal_not_found")
    content = {
        "approved_diff": proposal.approved_diff or proposal.diff_preview or "",
        "proposal_id": proposal.proposal_id,
        "proposed_files": list(proposal.proposed_files),
        "target": target,
    }
    content_hash = sha256(repr(sorted(content.items())).encode("utf-8")).hexdigest()
    return {
        "authority": "proposal_only",
        "cartographer_identity": "cartographer-proposal-transfer",
        "consumer": consumer,
        "content": content,
        "content_hash": content_hash,
        "proposal_id": proposal.proposal_id,
        "transfer_id": f"cartographer-transfer-{content_hash[:16]}",
        "write_authority": False,
        "approval_issuer_authority": False,
        "git_authority": False,
        "queue_authority": False,
    }
