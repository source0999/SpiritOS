from __future__ import annotations

from typing import Iterable


AUTONOMY_LEVEL = 1
AUTONOMY_MODE = "auto_rank_only"


def apply_candidate_auto_rank(candidates: list[dict]) -> list[dict]:
    ranks = _rank_items(candidates, _candidate_rank_key)
    for candidate in candidates:
        rank = ranks[id(candidate)]
        auto_rank = {
            "level": AUTONOMY_LEVEL,
            "mode": AUTONOMY_MODE,
            "read_only": True,
            "mutation_allowed": False,
            "recommended_review_order": rank,
            "why_this_first": _candidate_why(candidate),
            "risk_reason": _candidate_risk(candidate),
        }
        candidate["auto_rank"] = auto_rank
        candidate["recommended_review_order"] = rank
        candidate["why_this_first"] = auto_rank["why_this_first"]
        candidate["risk_reason"] = auto_rank["risk_reason"]
    return candidates


def apply_packet_auto_rank(packets: list[dict]) -> list[dict]:
    ranks = _rank_items(packets, _packet_rank_key)
    for packet in packets:
        rank = ranks[id(packet)]
        auto_rank = {
            "level": AUTONOMY_LEVEL,
            "mode": AUTONOMY_MODE,
            "read_only": True,
            "mutation_allowed": False,
            "recommended_review_order": rank,
            "why_this_first": _packet_why(packet),
            "risk_reason": _packet_risk(packet),
        }
        packet["auto_rank"] = auto_rank
        packet["recommended_review_order"] = rank
        packet["why_this_first"] = auto_rank["why_this_first"]
        packet["risk_reason"] = auto_rank["risk_reason"]
    return packets


def _rank_items(items: list[dict], key_fn) -> dict[int, int]:
    ordered = sorted(items, key=key_fn)
    return {id(item): index for index, item in enumerate(ordered, start=1)}


def _candidate_rank_key(candidate: dict) -> tuple:
    score = _candidate_review_score(candidate)
    return (-score, _stable_text(candidate, ("canonical_uri", "candidate_id")))


def _candidate_review_score(candidate: dict) -> float:
    status = str(candidate.get("status") or "")
    status_weight = {
        "recommended": 70,
        "needs_review": 55,
        "stored": 25,
        "approved": 5,
        "rejected": 0,
        "blocked": -20,
    }.get(status, 10)
    confidence = _float(candidate.get("confidence_score")) * 100
    reasons = set(_strings(candidate.get("reason_codes")))
    score = status_weight + confidence
    if candidate.get("trust_tier") == "official":
        score += 12
    if reasons & {
        "official_repo_pattern",
        "official_docs_pattern",
        "official_domain_match",
        "known_ecosystem_match",
    }:
        score += 8
    if "metadata_sufficient" in reasons:
        score += 4
    if "release_notes_pattern" in reasons:
        score += 3
    if status in {"approved", "rejected"}:
        score -= 80
    if status == "blocked" or "blocked_source" in reasons:
        score -= 120
    if "spam_pattern_detected" in reasons:
        score -= 140
    return score


def _candidate_why(candidate: dict) -> str:
    status = str(candidate.get("status") or "")
    reasons = set(_strings(candidate.get("reason_codes")))
    if status in {"approved", "rejected", "blocked"}:
        return "Manual state already set; review only if the operator wants to revisit it."
    if candidate.get("trust_tier") == "official" and status == "recommended":
        return "Recommended source with official trust signals should be reviewed first."
    if reasons & {"official_repo_pattern", "official_docs_pattern", "official_domain_match"}:
        return "Official source signals make this a high-value manual review candidate."
    if status == "needs_review":
        return "Useful source evidence exists, but it still needs human inspection."
    if status == "stored":
        return "Lower-priority stored evidence can wait behind recommended candidates."
    return "Ranked from existing Source Gate evidence only."


def _candidate_risk(candidate: dict) -> str:
    status = str(candidate.get("status") or "")
    reasons = set(_strings(candidate.get("reason_codes")))
    source_kind = str(candidate.get("source_kind") or "")
    if status == "blocked" or "blocked_source" in reasons:
        return "Blocked source; do not activate automatically."
    if status == "rejected":
        return "Rejected source; do not re-open without operator intent."
    if "spam_pattern_detected" in reasons:
        return "Noisy or spam-like signal requires rejection or block review."
    if source_kind == "web_page":
        return "Stored-only source kind may not have poller support."
    if candidate.get("auto_approval_dry_run") is True:
        return "Eligible for dry-run label only; auto-approval remains forbidden."
    return "No automatic source status change is allowed."


def _packet_rank_key(packet: dict) -> tuple:
    score = _packet_review_score(packet)
    return (-score, _stable_text(packet, ("packet_id", "source_uri")))


def _packet_review_score(packet: dict) -> float:
    status = str(packet.get("effective_status") or packet.get("status") or "")
    verdict = str(packet.get("verdict_decision") or "")
    score = {
        "surfaced": 70,
        "stored": 45,
        "promoted": 35,
        "debugger_pending": 25,
        "ignored": 0,
    }.get(status, 15)
    if verdict == "surface":
        score += 15
    elif verdict == "promote":
        score += 12
    elif verdict == "store":
        score += 4
    elif verdict == "ignore":
        score -= 25
    score += _float(packet.get("confidence_score")) * 25
    score += _float(packet.get("source_quality_score")) * 20
    if packet.get("source_trust_label") == "Official GitHub repo":
        score += 5
    if packet.get("promotion_status") in {"queued", "approved"}:
        score -= 20
    return score


def _packet_why(packet: dict) -> str:
    status = str(packet.get("effective_status") or packet.get("status") or "")
    verdict = str(packet.get("verdict_decision") or "")
    if packet.get("promotion_status") in {"queued", "approved"}:
        return "Packet already has promotion state, so review lower unless revisiting."
    if status == "surfaced" or verdict == "surface":
        return "Surfaced packet is likely useful for manual packet review."
    if verdict == "promote":
        return "Promotion verdict suggests this packet deserves manual review."
    if status == "stored":
        return "Stored packet may be useful later, behind surfaced packets."
    return "Ranked from existing packet, verdict, and source-quality evidence only."


def _packet_risk(packet: dict) -> str:
    status = str(packet.get("effective_status") or packet.get("status") or "")
    if packet.get("promotion_status") in {"queued", "approved"}:
        return "Promotion state already exists; do not promote automatically."
    if status == "ignored":
        return "Ignored packet should not be promoted without operator review."
    if not packet.get("source_quality_score"):
        return "Missing source quality score limits confidence."
    return "No automatic packet promotion is allowed."


def _float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _strings(value) -> Iterable[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _stable_text(item: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if value:
            return str(value)
    return ""
