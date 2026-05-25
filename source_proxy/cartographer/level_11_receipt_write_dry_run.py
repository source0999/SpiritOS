from __future__ import annotations

import dataclasses

from source_proxy.cartographer.level_11_approval_token import (
    CartographerLevel11ApprovalTokenValidation,
)
from source_proxy.cartographer.level_11_event_ledger import (
    CartographerLevel11LedgerValidation,
)


@dataclasses.dataclass(frozen=True)
class CartographerLevel11ReceiptWriteDryRunPacket:
    level: str
    title: str
    status: str
    action_type: str
    mode: str
    target_receipt_file: str
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


def build_level_11_receipt_write_dry_run_packet(
    *,
    target_receipt_file: str,
    allowed_files: tuple[str, ...],
    forbidden_files: tuple[str, ...],
    approval_validation: CartographerLevel11ApprovalTokenValidation,
    ledger_validation: CartographerLevel11LedgerValidation,
) -> CartographerLevel11ReceiptWriteDryRunPacket:
    reasons: list[str] = []

    if not target_receipt_file:
        reasons += ["missing_target_receipt_file"]
    if not target_receipt_file.startswith("docs/"):
        reasons += ["target_receipt_file_outside_docs"]
    if target_receipt_file not in allowed_files:
        reasons += ["target_receipt_file_outside_allowed_files"]
    if target_receipt_file in forbidden_files:
        reasons += ["target_receipt_file_intersects_forbidden_files"]
    if not approval_validation.valid_for_dry_run:
        reasons += [f"approval:{reason}" for reason in approval_validation.blocked_reasons]
    if not ledger_validation.valid_for_dry_run:
        reasons += [f"ledger:{reason}" for reason in ledger_validation.blocked_reasons]

    return CartographerLevel11ReceiptWriteDryRunPacket(
        level="11.4",
        title="Approved Receipt Write Dry Run Runtime",
        status="receipt-write-dry-run-only",
        action_type="approved_receipt_write",
        mode="dry_run",
        target_receipt_file=target_receipt_file,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        approval_token_valid_for_dry_run=approval_validation.valid_for_dry_run,
        ledger_valid_for_dry_run=ledger_validation.valid_for_dry_run,
        would_write_file=False,
        write_authority_granted=False,
        local_execution_authority_granted=False,
        blocked=bool(reasons),
        blocked_reasons=tuple(dict.fromkeys(reasons)),
        next_increment="Cartographer Level 11.5: Approved Evidence Write Dry Run Runtime",
    )
