from __future__ import annotations

from typing import Any

_DECISION_LABELS = {
    "surface": "Useful now",
    "store": "Saved for later",
    "ignore": "Ignored",
    "promote": "Approved for memory",
}

_STATUS_LABELS = {
    "surfaced": "Useful now",
    "stored": "Saved for later",
    "ignored": "Ignored",
    "promoted": "Approved for memory",
    "debugger_pending": "Waiting for Scout debugger",
}

_STATUS_HELP = {
    "surfaced": "Scout thinks this packet is useful to inspect now.",
    "stored": "Scout kept this packet, but it is not important enough to surface.",
    "ignored": "Scout reviewed this packet and does not recommend using it.",
    "promoted": "Scout marked this packet as eligible for human-approved memory promotion.",
    "debugger_pending": "Scout has created the packet, but the debugger has not reviewed it yet.",
}

_RECOMMENDED_ACTIONS = {
    "surfaced": "inspect_now",
    "stored": "save_for_later",
    "ignored": "no_action",
    "promoted": "review_memory_promotion",
    "debugger_pending": "wait_for_debugger",
}

_CONFIDENCE_LABELS = {
    "surfaced": "high",
    "promoted": "high",
    "stored": "medium",
    "ignored": "low",
    "debugger_pending": "pending",
}


def verdict_decision(verdict: dict[str, Any] | None) -> str | None:
    if not verdict:
        return None
    decision = verdict.get("decision")
    return str(decision) if decision else None


def finding_summaries(verdict: dict[str, Any] | None) -> list[dict[str, str | int]]:
    if not verdict:
        return []
    findings = verdict.get("findings") or []
    summaries: list[dict[str, str | int]] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        summaries.append(
            {
                "check_id": str(finding.get("check_id") or ""),
                "tier": int(finding.get("tier") or 0),
                "status": str(finding.get("status") or ""),
                "detail": str(finding.get("detail") or ""),
            }
        )
    return summaries


def embedding_was_skipped(verdict: dict[str, Any] | None) -> bool:
    return any(
        finding.get("check_id") == "embedding_storage"
        and finding.get("status") == "skipped"
        for finding in (verdict or {}).get("findings", [])
        if isinstance(finding, dict)
    )


def status_explanation(
    *,
    raw_status: str | None,
    verdict: dict[str, Any] | None,
    effective_status: str,
) -> dict[str, str | None]:
    decision = verdict_decision(verdict)
    if decision:
        label = _DECISION_LABELS.get(decision, _STATUS_LABELS.get(effective_status, effective_status))
        help_text = _STATUS_HELP.get(effective_status, "Scout debugger reviewed this packet.")
        if decision == "promote" and embedding_was_skipped(verdict):
            label = "Semantic memory skipped"
            help_text = (
                "Scout approved the packet for memory review, but semantic embedding "
                "storage is inactive."
            )
    else:
        label = _STATUS_LABELS.get(effective_status, effective_status)
        help_text = _STATUS_HELP.get(effective_status, "Scout has not explained this status yet.")

    return {
        "raw_status": raw_status or "debugger_pending",
        "verdict_decision": decision,
        "effective_status": effective_status,
        "label": label,
        "help": help_text,
    }


def human_status_label(
    *,
    raw_status: str | None,
    verdict: dict[str, Any] | None,
    effective_status: str,
) -> str:
    return str(
        status_explanation(
            raw_status=raw_status,
            verdict=verdict,
            effective_status=effective_status,
        )["label"]
    )


def usefulness_explanation(
    *,
    raw_status: str | None,
    verdict: dict[str, Any] | None,
    effective_status: str,
) -> dict[str, str | None]:
    status = status_explanation(
        raw_status=raw_status,
        verdict=verdict,
        effective_status=effective_status,
    )
    reason = str(status["help"] or "")
    findings = finding_summaries(verdict)
    reason_codes = (verdict or {}).get("reason_codes") or []
    if findings:
        reason = findings[0]["detail"] or reason
    elif reason_codes:
        reason = f"Scout reason codes: {', '.join(str(code) for code in reason_codes[:3])}."

    return {
        "usefulness_label": status["label"],
        "usefulness_reason": reason,
        "recommended_action": _RECOMMENDED_ACTIONS.get(effective_status, "review_packet"),
        "confidence_label": _CONFIDENCE_LABELS.get(effective_status, "unknown"),
    }
