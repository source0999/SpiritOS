"""Non-writing compatibility types for Cartographer proposal reviews.

The canonical mutation lifecycle lives in ``proposal_review_authority``.
Keeping this module free of filesystem mutation prevents a proposal-only
Cartographer helper from becoming an accidental writer again.
"""

from source_proxy.cartographer.proposal_review_authority import (
    CartographerProposalReviewError,
    ReviewDecision,
)

__all__ = ["CartographerProposalReviewError", "ReviewDecision"]
