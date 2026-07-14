from __future__ import annotations

from typing import Any


PROPOSAL_ONLY_BOUNDARY = {
    "authority": "proposal_only",
    "approval_issuer_authority": False,
    "git_authority": False,
    "queue_authority": False,
    "write_authority": False,
}


class CartographerProposalTransferError(ValueError):
    def __init__(self, message: str, reason_code: str):
        super().__init__(message)
        self.reason_code = reason_code


def transfer_proposal(*, proposal_id: str, consumer: str, target: str) -> dict[str, Any]:
    del proposal_id, consumer, target
    raise CartographerProposalTransferError(
        "Direct Cartographer transfer is forbidden; create a durable selection preview first.",
        "cartographer_direct_transfer_forbidden",
    )
