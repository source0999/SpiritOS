"""Compatibility boundary for removed Cartographer mutation authority."""
from __future__ import annotations

from typing import Any


class CartographerApplyError(ValueError):
    def __init__(self, message: str, reason_code: str):
        super().__init__(message)
        self.reason_code = reason_code


def apply_approved_doc_proposal(
    *,
    proposal_id: str,
    approved: bool,
    approved_by: str = "cartographer-ui",
) -> dict[str, Any]:
    """Fail closed; Cartographer can only transfer a persisted proposal."""

    del proposal_id, approved, approved_by
    raise CartographerApplyError(
        "Cartographer is proposal-only; transfer a persisted selection to the CodingOrchestrator.",
        "forbidden_cartographer_mutation",
    )
