from __future__ import annotations

import dataclasses

from source_proxy.cartographer.level_11_approval_token import (
    CartographerLevel11ApprovalTokenValidation,
)
from source_proxy.cartographer.level_11_event_ledger import (
    CartographerLevel11LedgerValidation,
)


@dataclasses.dataclass(frozen=True)
class CartographerLevel11EvidenceWriteDryRunPacket:
    level: str
    title: str
    status: str
    action_type: str
    mode: str
    target_evidence_file: str
    evidence_purpose: str
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    approval_token_valid_for_dry_run: bool
    ledger_valid_for_dry_run: bool
    would_write_file: bool
    write_authority_granted: bool
    local_execution_authority_granted: bool
    blocked: bool
    blocked_reasons: tuple[str, ...]
    next_increment: str


def build_level_11_evidence_write_dry_run_packet(
    *,
    target_evidence_file: str,
    evidence_purpose: str,
    allowed_files: tuple[str, ...],
    forbidden_files: tuple[str, ...],
    approval_validation: CartographerLevel11ApprovalTokenValidation,
    ledger_validation: CartographerLevel11LedgerValidation,
) -> CartographerLevel11EvidenceWriteDryRunPacket:
    reasons: list[str] = []

    if not target_evidence_file:
        reasons += ["missing_target_evidence_file"]
    if not evidence_purpose:
        reasons += ["missing_evidence_purpose"]
    if not target_evidence_file.startswith("docs/"):
        reasons += ["target_evidence_file_outside_docs"]
    if target_evidence_file not in allowed_files:
        reasons += ["target_evidence_file_outside_allowed_files"]
    if target_evidence_file in forbidden_files:
        reasons += ["target_evidence_file_intersects_forbidden_files"]
    if not approval_validation.valid_for_dry_run:
        reasons += [f"approval:{reason}" for reason in approval_validation.blocked_reasons]
    if not ledger_validation.valid_for_dry_run:
        reasons += [f"ledger:{reason}" for reason in ledger_validation.blocked_reasons]

    return CartographerLevel11EvidenceWriteDryRunPacket(
        level="11.5",
        title="Approved Evidence Write Dry Run Runtime",
        status="evidence-write-dry-run-only",
        action_type="approved_evidence_write",
        mode="dry_run",
        target_evidence_file=target_evidence_file,
        evidence_purpose=evidence_purpose,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        approval_token_valid_for_dry_run=approval_validation.valid_for_dry_run,
        ledger_valid_for_dry_run=ledger_validation.valid_for_dry_run,
        would_write_file=False,
        write_authority_granted=False,
        local_execution_authority_granted=False,
        blocked=bool(reasons),
        blocked_reasons=tuple(dict.fromkeys(reasons)),
        next_increment="Cartographer Level 11.6: Approved Docs-Only Apply Runtime Dry Run",
    )
