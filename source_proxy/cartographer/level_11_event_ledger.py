from __future__ import annotations

import dataclasses


LEVEL_11_LEDGER_EVENT_TYPES: tuple[str, ...] = (
    "action_packet_created",
    "approval_requested",
    "approval_granted",
    "approval_rejected",
    "approval_token_created",
    "approval_token_revoked",
    "file_write_requested",
    "file_write_blocked",
    "file_write_completed",
    "command_requested",
    "command_blocked",
    "command_completed",
    "verification_started",
    "verification_passed",
    "verification_failed",
    "rollback_available",
    "rollback_requested",
    "rollback_completed",
    "action_closed_out",
)

LEVEL_11_COMPLETED_ACTION_REQUIRED_EVENTS: tuple[str, ...] = (
    "action_packet_created",
    "approval_requested",
    "approval_granted",
    "approval_token_created",
    "verification_started",
    "verification_passed",
    "action_closed_out",
)


@dataclasses.dataclass(frozen=True)
class CartographerLevel11LedgerEvent:
    event_id: str
    event_type: str
    run_id: str
    action_id: str | None
    token_id: str | None
    sequence: int
    actor: str
    target_files: tuple[str, ...]
    head_before: str | None
    git_status_before: str | None
    rollback_reference: str | None
    verification_reference: str | None
    reason: str | None


@dataclasses.dataclass(frozen=True)
class CartographerLevel11LedgerValidation:
    valid_for_dry_run: bool
    append_only_runtime_enabled: bool
    action_authority_granted: bool
    blocked_reasons: tuple[str, ...]
    event_count: int


def build_level_11_event_ledger_schema_preview() -> dict[str, object]:
    return {
        "level": "11.3",
        "title": "Event Ledger Runtime Model Dry Run",
        "status": "ledger-model-dry-run-only",
        "append_only_runtime_enabled": False,
        "action_authority_granted": False,
        "write_authority_granted": False,
        "local_execution_authority_granted": False,
        "supported_event_types": LEVEL_11_LEDGER_EVENT_TYPES,
        "required_completed_action_events": LEVEL_11_COMPLETED_ACTION_REQUIRED_EVENTS,
        "next_increment": "Cartographer Level 11.4: Approved Receipt Write Dry Run Runtime",
    }


def validate_level_11_event_ledger_dry_run(
    events: tuple[CartographerLevel11LedgerEvent, ...],
) -> CartographerLevel11LedgerValidation:
    reasons: list[str] = []

    if not events:
        reasons += ["missing_events"]
    if len({event.event_id for event in events}) != len(events):
        reasons += ["duplicate_event_id"]

    expected_sequence = 1
    for event in events:
        if event.sequence != expected_sequence:
            reasons += ["sequence_gap_or_reorder"]
            break
        expected_sequence += 1

    for event in events:
        if event.event_type not in LEVEL_11_LEDGER_EVENT_TYPES:
            reasons += ["unsupported_event_type"]
        if not event.event_id:
            reasons += ["missing_event_id"]
        if not event.run_id:
            reasons += ["missing_run_id"]
        if not event.actor:
            reasons += ["missing_actor"]
        if event.event_type.endswith("_blocked") and not event.reason:
            reasons += ["blocked_event_missing_reason"]
        if event.event_type.endswith("_failed") and not event.reason:
            reasons += ["failed_event_missing_reason"]

    event_types = tuple(event.event_type for event in events)
    if "file_write_completed" in event_types or "command_completed" in event_types:
        for required in LEVEL_11_COMPLETED_ACTION_REQUIRED_EVENTS:
            if required not in event_types:
                reasons += [f"missing_required_completed_action_event:{required}"]

    return CartographerLevel11LedgerValidation(
        valid_for_dry_run=not reasons,
        append_only_runtime_enabled=False,
        action_authority_granted=False,
        blocked_reasons=tuple(dict.fromkeys(reasons)),
        event_count=len(events),
    )
