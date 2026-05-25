"""Read-only Proxy-to-Cartographer consultation adapter for Plan 9."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping, Sequence


PROXY_CONSULTATION_SCHEMA_VERSION = "cartographer.proxy-consultation.v0.1"

FALSE_CONSULTATION_AUTHORITY: dict[str, bool] = {
    "approval": False,
    "apply": False,
    "commit": False,
    "push": False,
    "queue": False,
    "worker": False,
    "provider": False,
    "shell": False,
}

READ_ONLY_PROXY_ACTIONS: tuple[str, ...] = (
    "preview",
    "plan",
    "review",
    "status",
    "verification",
)

APPLY_CAPABLE_PROXY_ACTIONS: tuple[str, ...] = (
    "apply",
    "docs_update",
    "coding_task",
    "test_generation",
    "queue",
    "commit",
    "push",
    "worker_dispatch",
)


def consult_cartographer_for_proxy_action(
    truth_packet: Mapping[str, Any] | None,
    *,
    request_id: str = "proxy-preflight",
    requested_at: str = "",
    requesting_surface: str = "/coding",
    requesting_lane: str = "coding",
    operator_intent: str = "",
    proposed_action: str = "apply",
    target_paths: Sequence[str] = (),
    allowed_paths: Sequence[str] = (),
    forbidden_paths: Sequence[str] = (),
    current_head: str = "",
    dirty_tree_fingerprint: str = "",
    requested_authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Answer Proxy preflight questions from a supplied truth packet only.

    The adapter never reads the repo, calls providers, mutates state, consumes
    approvals, or grants runtime authority. Missing or malformed Cartographer
    facts fail closed.
    """

    proposed_action = _normalize_action(proposed_action)
    request_packet = {
        "request_id": request_id,
        "requested_at": requested_at,
        "requesting_surface": requesting_surface,
        "requesting_lane": requesting_lane,
        "operator_intent": operator_intent,
        "proposed_action": proposed_action,
        "target_paths": _string_tuple(target_paths),
        "allowed_paths": _string_tuple(allowed_paths),
        "forbidden_paths": _string_tuple(forbidden_paths),
        "current_head": current_head,
        "dirty_tree_fingerprint": dirty_tree_fingerprint,
        "truth_packet_required": True,
        "requested_authority": _requested_authority(requested_authority),
    }
    unsafe_authority = _truthy_authority_fields(request_packet["requested_authority"])

    if not isinstance(truth_packet, Mapping):
        return _blocked_response(
            request_packet=request_packet,
            outcome="cartographer_unavailable",
            reason_codes=("cartographer_unavailable",),
            summary="Cartographer unavailable; default NO-GO.",
            cartographer_packet_status=None,
        )

    if truth_packet.get("schema_version") != "cartographer.truth-packet.v0.1":
        return _blocked_response(
            request_packet=request_packet,
            outcome="cartographer_unavailable",
            reason_codes=("truth_packet_malformed",),
            summary="Cartographer unavailable; default NO-GO.",
            cartographer_packet_status=None,
        )

    status = _string_value(truth_packet.get("status")) or "unknown"
    facts = truth_packet.get("facts") if isinstance(truth_packet.get("facts"), Mapping) else {}
    unknown_fields = _string_tuple(truth_packet.get("unknown_fields"))
    stale_fields = _string_tuple(truth_packet.get("stale_fields"))
    protected_matches = _record_tuple(truth_packet.get("protected_lane_matches"))
    protected_paths = tuple(
        _string_value(match.get("path")) or ""
        for match in protected_matches
        if _string_value(match.get("path"))
    )
    protected_count = _int_value(facts.get("protected_lane_count")) if isinstance(facts, Mapping) else 0
    protected_count = max(protected_count, len(protected_paths))
    total_dirty_count = _int_value(facts.get("total_dirty_count")) if isinstance(facts, Mapping) else 0
    tracked_dirty_count = _int_value(facts.get("tracked_dirty_count")) if isinstance(facts, Mapping) else 0
    untracked_dirty_count = _int_value(facts.get("untracked_dirty_count")) if isinstance(facts, Mapping) else 0
    dirty_paths = _string_tuple(truth_packet.get("tracked_dirty_files")) + _string_tuple(
        truth_packet.get("untracked_files")
    )
    target_path_tuple = request_packet["target_paths"]
    target_overlap = tuple(path for path in target_path_tuple if path in dirty_paths or path in protected_paths)

    if status in {"no_go", "unknown", "stale"} or unknown_fields or stale_fields:
        reasons = [f"cartographer_status_{status or 'unknown'}"]
        if unknown_fields:
            reasons.append("cartographer_truth_packet_unknown")
        if stale_fields:
            reasons.append("cartographer_truth_packet_stale")
        return _blocked_response(
            request_packet=request_packet,
            outcome="cartographer_unavailable",
            reason_codes=tuple(reasons),
            summary="Cartographer unavailable; default NO-GO.",
            cartographer_packet_status=status,
            cartographer_packet_id=_string_value(truth_packet.get("packet_id")),
            lane_status=_lane_status(status, tuple(reasons)),
            dirty_tree_risk=_dirty_tree_risk(
                state="dirty_tree_blocked",
                tracked_count=tracked_dirty_count,
                untracked_count=untracked_dirty_count,
                protected_count=protected_count,
                unknown_count=_int_value(facts.get("unknown_unclassified_dirty_count"))
                if isinstance(facts, Mapping)
                else 0,
                target_overlap=target_overlap,
            ),
        )

    if unsafe_authority:
        return _blocked_response(
            request_packet=request_packet,
            outcome="no_go",
            reason_codes=("requested_authority_must_be_false",),
            summary="Proxy consultation cannot request runtime authority.",
            cartographer_packet_status=status,
            cartographer_packet_id=_string_value(truth_packet.get("packet_id")),
        )

    if status == "blocked" or protected_count:
        blocked_paths = protected_paths or ("protected_lane_match_count",)
        return _blocked_response(
            request_packet=request_packet,
            outcome="dirty_tree_blocked",
            reason_codes=("protected_path_conflict",),
            summary="Dirty tree or protected lane blocks this consultation.",
            blocked_paths=blocked_paths,
            cartographer_packet_status=status,
            cartographer_packet_id=_string_value(truth_packet.get("packet_id")),
            lane_status=_lane_status("blocked", ("protected_path_conflict",)),
            dirty_tree_risk=_dirty_tree_risk(
                state="dirty_tree_blocked",
                tracked_count=tracked_dirty_count,
                untracked_count=untracked_dirty_count,
                protected_count=protected_count,
                unknown_count=_int_value(facts.get("unknown_unclassified_dirty_count"))
                if isinstance(facts, Mapping)
                else 0,
                target_overlap=target_overlap or blocked_paths,
            ),
        )

    if proposed_action not in READ_ONLY_PROXY_ACTIONS:
        return _blocked_response(
            request_packet=request_packet,
            outcome="needs_approval",
            reason_codes=("proxy_action_requires_future_approval",),
            summary="Apply-capable Proxy work requires later human approval and verification.",
            missing_proof=("human approval token", "focused verification proof"),
            cartographer_packet_status=status,
            cartographer_packet_id=_string_value(truth_packet.get("packet_id")),
            lane_status=_lane_status(status if status in {"clear", "caution"} else "unknown", ()),
            dirty_tree_risk=_dirty_tree_risk(
                state="dirty_review_required" if total_dirty_count else "clean",
                tracked_count=tracked_dirty_count,
                untracked_count=untracked_dirty_count,
                protected_count=protected_count,
                unknown_count=_int_value(facts.get("unknown_unclassified_dirty_count"))
                if isinstance(facts, Mapping)
                else 0,
                target_overlap=target_overlap,
            ),
        )

    return {
        **_response_base(
            request_packet=request_packet,
            outcome="go",
            reason_codes=("advisory_read_only",),
            summary="Clear for read-only planning only.",
            cartographer_packet_status=status,
            cartographer_packet_id=_string_value(truth_packet.get("packet_id")),
        ),
        "safe_next_action": "Display the advisory answer and wait for a later approved plan.",
        "missing_proof": [],
        "blocked_paths": [],
        "lane_status": _lane_status("clear" if status == "clear" else "caution", ()),
        "dirty_tree_risk": _dirty_tree_risk(
            state="dirty_review_required" if total_dirty_count else "clean",
            tracked_count=tracked_dirty_count,
            untracked_count=untracked_dirty_count,
            protected_count=protected_count,
            unknown_count=_int_value(facts.get("unknown_unclassified_dirty_count"))
            if isinstance(facts, Mapping)
            else 0,
            target_overlap=target_overlap,
        ),
        "approval_requirements": _approval_requirements(proposed_action),
        "verification_requirements": _verification_requirements(
            proposed_action,
            request_packet["target_paths"],
        ),
        "active_lane_ownership": {
            "ownership_state": "unknown",
            "owner_lane": "",
            "reason_codes": ["lane_registry_not_connected"],
        },
    }


def _blocked_response(
    *,
    request_packet: dict[str, Any],
    outcome: str,
    reason_codes: Sequence[str],
    summary: str,
    safe_next_action: str = "Stop and inspect Cartographer status manually.",
    missing_proof: Sequence[str] = (),
    blocked_paths: Sequence[str] = (),
    cartographer_packet_status: str | None,
    cartographer_packet_id: str | None = None,
    lane_status: dict[str, Any] | None = None,
    dirty_tree_risk: dict[str, Any] | None = None,
) -> dict[str, Any]:
    proposed_action = _normalize_action(str(request_packet.get("proposed_action") or "apply"))
    return {
        **_response_base(
            request_packet=request_packet,
            outcome=outcome,
            reason_codes=reason_codes,
            summary=summary,
            cartographer_packet_status=cartographer_packet_status,
            cartographer_packet_id=cartographer_packet_id,
        ),
        "safe_next_action": safe_next_action,
        "missing_proof": list(missing_proof),
        "blocked_paths": list(blocked_paths),
        "lane_status": lane_status or _lane_status("blocked", reason_codes),
        "dirty_tree_risk": dirty_tree_risk
        or _dirty_tree_risk(
            state="dirty_tree_blocked",
            tracked_count=0,
            untracked_count=0,
            protected_count=0,
            unknown_count=0,
            target_overlap=blocked_paths,
        ),
        "approval_requirements": _approval_requirements(proposed_action),
        "verification_requirements": _verification_requirements(
            proposed_action,
            request_packet["target_paths"],
        ),
        "active_lane_ownership": {
            "ownership_state": "unknown",
            "owner_lane": "",
            "reason_codes": ["lane_registry_not_connected"],
        },
    }


def _response_base(
    *,
    request_packet: dict[str, Any],
    outcome: str,
    reason_codes: Sequence[str],
    summary: str,
    cartographer_packet_status: str | None,
    cartographer_packet_id: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": PROXY_CONSULTATION_SCHEMA_VERSION,
        "response_id": f"{request_packet['request_id']}:cartographer-preflight",
        "request_id": request_packet["request_id"],
        "answered_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "request_packet": request_packet,
        "cartographer_packet_id": cartographer_packet_id or "",
        "cartographer_packet_status": cartographer_packet_status or "unavailable",
        "outcome": outcome,
        "go": False,
        "action_allowed": False,
        "manual_only": True,
        "runtime_action_available": False,
        "operator_review_required": True,
        "reason_codes": list(_dedupe(reason_codes)),
        "summary": summary,
        "authority": FALSE_CONSULTATION_AUTHORITY.copy(),
    }


def _lane_status(state: str, reason_codes: Sequence[str]) -> dict[str, Any]:
    if state not in {"clear", "caution", "blocked", "unknown", "stale"}:
        state = "unknown"
    return {
        "state": state,
        "reason_codes": list(_dedupe(reason_codes)),
        "advisory_only": True,
    }


def _dirty_tree_risk(
    *,
    state: str,
    tracked_count: int,
    untracked_count: int,
    protected_count: int,
    unknown_count: int,
    target_overlap: Sequence[str],
) -> dict[str, Any]:
    return {
        "state": state,
        "tracked_count": tracked_count,
        "untracked_count": untracked_count,
        "protected_lane_count": protected_count,
        "unknown_file_count": unknown_count,
        "target_paths_overlap_dirty_files": bool(target_overlap),
        "target_path_overlaps": list(_dedupe(target_overlap)),
    }


def _approval_requirements(proposed_action: str) -> dict[str, Any]:
    if proposed_action in READ_ONLY_PROXY_ACTIONS:
        return {
            "approval_state": "not_required_for_read_only",
            "required_fields": [],
            "approval_token_consumption_available": False,
            "consumed_during_consultation": False,
        }
    return {
        "approval_state": "required_for_future_action",
        "required_fields": [
            "operator_id",
            "approver_id",
            "token_id",
            "run_id",
            "action_type",
            "exact_allowed_files",
            "expiry",
            "expected_head",
            "expected_dirty_tree",
            "human_approval_timestamp",
        ],
        "approval_token_consumption_available": False,
        "consumed_during_consultation": False,
    }


def _verification_requirements(
    proposed_action: str,
    target_paths: Sequence[str],
) -> dict[str, Any]:
    if proposed_action in READ_ONLY_PROXY_ACTIONS:
        return {
            "verification_state": "not_required_for_read_only",
            "required_checks": [],
            "manual_checks": [],
            "missing_proof": [],
            "closeout_blocked_without_proof": False,
            "commands_run_during_consultation": False,
        }
    path_label = ", ".join(target_paths) if target_paths else "declared target paths"
    required_checks = (
        "git diff --check",
        f"focused tests covering: {path_label}",
    )
    manual_checks = (
        "confirm Cartographer preflight outcome was reviewed",
        "confirm changed files match allowed_paths exactly",
    )
    return {
        "verification_state": "needs_focused_tests",
        "required_checks": list(required_checks),
        "manual_checks": list(manual_checks),
        "missing_proof": [*required_checks, *manual_checks],
        "closeout_blocked_without_proof": True,
        "commands_run_during_consultation": False,
    }


def _requested_authority(value: Mapping[str, Any] | None) -> dict[str, bool]:
    requested = FALSE_CONSULTATION_AUTHORITY.copy()
    if not isinstance(value, Mapping):
        return requested
    for key in requested:
        requested[key] = value.get(key) is True
    return requested


def _truthy_authority_fields(value: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(key for key, granted in value.items() if granted is True)


def _normalize_action(value: str) -> str:
    action = value.strip().lower() if isinstance(value, str) else ""
    return action or "apply"


def _string_value(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


def _record_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _int_value(value: Any) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item or item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return tuple(deduped)
