from __future__ import annotations

import re
from typing import Any, Literal


CanonicalFinalVerdict = Literal[
    "PASS",
    "FAIL",
    "UNVERIFIED",
    "BLOCKED",
    "PARTIAL",
    "NEEDS_FIX",
    "HANDOFF",
]

PASS_ELIGIBLE_BEHAVIOR_VERDICTS = {"PASS"}
FAIL_BEHAVIOR_VERDICTS = {"FAIL"}
UNVERIFIED_BEHAVIOR_VERDICTS = {"", "UNVERIFIED", "NOT_RUN", "SKIPPED", "UNKNOWN"}
BLOCKED_BEHAVIOR_VERDICTS = {"BLOCKED"}
NEEDS_FIX_BEHAVIOR_VERDICTS = {"NEEDS_FIX", "ERROR"}
HANDOFF_BEHAVIOR_VERDICTS = {"HANDOFF"}


def normalize_artifact_final_verdict(
    *,
    route_status: str,
    artifact_ready: bool,
    behavior_required: bool,
    behavior_verdict: str | None = None,
    repair_verdict: str | None = None,
    handoff_required: bool = False,
    reason_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Normalize weak route/artifact signals into an auditable final verdict."""

    reasons = sorted(set(reason_codes or []))
    route = route_status.upper()
    behavior = (behavior_verdict or "").upper()
    repair = (repair_verdict or "").upper()
    if behavior in PASS_ELIGIBLE_BEHAVIOR_VERDICTS:
        reasons = [
            reason
            for reason in reasons
            if reason not in {"behavior_required_but_unverified", "behavior_unverified_without_ready_artifact"}
        ]
    if behavior in FAIL_BEHAVIOR_VERDICTS:
        reasons = [
            reason
            for reason in reasons
            if reason not in {"behavior_required_but_unverified", "behavior_unverified_without_ready_artifact"}
        ]

    if handoff_required or behavior in HANDOFF_BEHAVIOR_VERDICTS or repair in HANDOFF_BEHAVIOR_VERDICTS:
        reasons.append("handoff_required")
        return _verdict("HANDOFF", reasons, behavior)

    if route == "EXPECTED-BLOCKED" or behavior in BLOCKED_BEHAVIOR_VERDICTS:
        reasons.append("blocked_by_scope_or_permission")
        return _verdict("BLOCKED", reasons, behavior)

    if route in {"NO-GO", "NO_GO", "ERROR"} or behavior in NEEDS_FIX_BEHAVIOR_VERDICTS:
        reasons.append("route_or_proof_pipeline_needs_fix")
        return _verdict("NEEDS_FIX", reasons, behavior)

    if not artifact_ready:
        reasons.append("artifact_readiness_failed")
        if behavior_required:
            reasons.append("behavior_unverified_without_ready_artifact")
        return _verdict("FAIL", reasons, behavior)

    if behavior_required:
        if behavior in PASS_ELIGIBLE_BEHAVIOR_VERDICTS:
            reasons.append("behavior_pass_verified")
            return _verdict("PASS", reasons, behavior)
        if behavior in FAIL_BEHAVIOR_VERDICTS:
            reasons.append("behavior_failed")
            return _verdict("FAIL", reasons, behavior)
        if behavior in UNVERIFIED_BEHAVIOR_VERDICTS:
            reasons.append("behavior_required_but_unverified")
            return _verdict("UNVERIFIED", reasons, behavior)
        reasons.append("behavior_verdict_unknown")
        return _verdict("UNVERIFIED", reasons, behavior)

    if route == "GO" and artifact_ready:
        reasons.append("artifact_ready_no_behavior_required")
        return _verdict("PASS", reasons, behavior)

    reasons.append("final_verdict_unverified")
    return _verdict("UNVERIFIED", reasons, behavior)


def build_artifact_final_verdict_row(
    *,
    original_prompt: str,
    normalized_intent: str,
    planner_criterion_id: str,
    behavior_contract: dict[str, Any],
    probe_result: dict[str, Any] | None,
    selected_preview_path: str,
    route_status: str,
    open_status: str,
    artifact_ready: bool,
    repair_result: dict[str, Any] | None = None,
    evidence_refs: dict[str, str] | None = None,
    anti_cheat_flags: dict[str, Any] | None = None,
    reason_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Build an auditable final verdict row for a disposable static UI artifact."""

    probe = probe_result or {}
    repair = repair_result or {}
    behavior_required = bool(behavior_contract.get("behavior_required"))
    behavior_verdict = str(probe.get("verdict") or "").upper()
    repair_status = str(repair.get("status") or "").upper()
    repair_attempt_count = int(repair.get("attempts_used") or repair.get("repair_attempts") or 0)
    probe_id = str(
        probe.get("probe_id")
        or probe.get("test")
        or _first_probe(behavior_contract).get("probe_id")
        or ""
    )
    all_reasons = [
        *(reason_codes or []),
        *[str(code) for code in probe.get("reason_codes") or []],
        *[str(code) for code in repair.get("reason_codes") or []],
    ]
    if behavior_verdict == "FAIL":
        all_reasons.extend(["behavior_failed_verified", "behavior_probe_failed"])
    if repair_attempt_count:
        all_reasons.append(f"repair_attempts_{repair_attempt_count}")
    if repair_attempt_count == 1 and behavior_verdict == "PASS":
        all_reasons.append("post_behavior_repair_pass")
    if repair_attempt_count == 1 and behavior_verdict == "FAIL":
        all_reasons.append("post_behavior_repair_failed")
    if route_status.upper() == "GO" and behavior_required and behavior_verdict != "PASS":
        all_reasons.append("route_go_not_behavior_pass")
    if str(open_status).upper() in {"PASS", "OPEN", "OK"} and behavior_required and behavior_verdict != "PASS":
        all_reasons.append("preview_open_not_behavior_pass")

    final = normalize_artifact_final_verdict(
        route_status=route_status,
        artifact_ready=artifact_ready,
        behavior_required=behavior_required,
        behavior_verdict=behavior_verdict,
        repair_verdict=repair_status,
        handoff_required=bool(repair.get("handoff_required")) or repair_status == "HANDOFF",
        reason_codes=all_reasons,
    )

    return {
        "original_prompt": original_prompt,
        "normalized_intent": normalized_intent,
        "planner_criterion_id": planner_criterion_id,
        "behavior_criterion_id": planner_criterion_id,
        "behavior_contract_id": str(behavior_contract.get("contract_version") or ""),
        "probe_id": probe_id,
        "selected_preview_path": selected_preview_path,
        "route_status": route_status,
        "open_status": open_status,
        "observed_before": _observed_value(probe, "before"),
        "observed_after": _observed_value(probe, "after"),
        "observed_values": _observed_dict(probe),
        "repair_attempt_count": repair_attempt_count,
        "repair_status": repair_status or "NOT_RUN",
        "evidence_refs": evidence_refs or {},
        "anti_cheat_flags": anti_cheat_flags or {},
        "canonical_final_verdict": final["label"],
        "product_pass": final["product_pass"],
        "final_reason_codes": final["reason_codes"],
        "passed_stage": _passed_stage(final["label"], repair_attempt_count),
    }


def classify_artifact_score_integrity(
    *,
    prompt: str,
    category: str = "",
    route_status: str = "",
    open_status: str = "",
    behavior_probe: dict[str, Any] | None = None,
    raw_final_verdict: str | None = None,
) -> dict[str, Any]:
    """Apply product-specific behavior pass rules over raw browser probe output."""

    probe = behavior_probe or {}
    actual = _observed_dict(probe)
    text = f"{prompt} {category} {probe.get('test') or ''}".lower()
    raw_probe_pass = bool(probe.get("passed")) and str(probe.get("verdict") or "").upper() == "PASS"
    raw_label = (raw_final_verdict or ("PASS" if raw_probe_pass else "FAIL")).upper()
    bucket = str(probe.get("primary_behavior_failure_bucket") or probe.get("failureBucket") or "")
    secondary_bucket = str(probe.get("secondary_behavior_failure_bucket") or "")

    strict_pass = raw_probe_pass
    strict_reason = "raw browser behavior probe passed"

    if str(open_status or "").upper() == "FAIL":
        strict_pass = False
        bucket = bucket or _preview_bucket(route_status, text)
        strict_reason = "preview did not open for behavior verification"
    elif _is_notes(text):
        strict_pass = bool(actual.get("appears"))
        bucket = "" if strict_pass else "notes_saved_status_without_note_text"
        strict_reason = "entered note text must remain visible after save"
    elif _is_list(text):
        strict_pass = bool(actual.get("appears"))
        bucket = "" if strict_pass else "checklist_status_without_item_text"
        strict_reason = "entered checklist/list text must appear visibly"
    elif _is_calculator(text):
        after = str(actual.get("after") or "")
        strict_pass = _text_changed(actual) and _has_digit(after)
        bucket = "" if strict_pass else "calculator_no_visible_result_update"
        strict_reason = "numeric inputs must produce a visible numeric result update"
    elif _is_timer(text):
        before = str(actual.get("before") or "")
        after_start = str(actual.get("afterStart") or "")
        after_stop = str(actual.get("afterStop") or "")
        strict_pass = bool(after_start) and after_start != before
        bucket = "" if strict_pass else "timer_no_visible_change_after_start"
        if not strict_pass and after_stop and after_stop != before:
            secondary_bucket = secondary_bucket or "timer_state_changed_after_wrong_action"
        strict_reason = "timer must visibly change after the start action"
    elif _is_theme(text):
        before = actual.get("before")
        after = actual.get("after")
        strict_pass = bool(before is not None and after is not None and before != after)
        bucket = "" if strict_pass else "theme_no_computed_state_change"
        strict_reason = "theme toggle must change computed color or class state"
    elif _is_weather(text):
        strict_pass = bool(actual.get("hasWeatherTerms")) and (not actual.get("clicked") or _text_changed(actual))
        bucket = "" if strict_pass else "weather_static_when_update_expected"
        strict_reason = "weather artifact must show weather fields and update when a control is present"
    elif _is_player(text):
        strict_pass = bool(actual.get("clicked")) and _text_changed(actual)
        bucket = "" if strict_pass else "player_control_no_visible_state_change"
        strict_reason = "player control must visibly change state"
    elif _is_tracker(text):
        strict_pass = bool(actual.get("clicked")) and _text_changed(actual)
        bucket = "" if strict_pass else "tracker_control_no_visible_progress_change"
        strict_reason = "tracker/counter control must visibly change progress or count"
    elif _is_password(text):
        combined = f"{actual.get('weak') or ''} {actual.get('strong') or ''}"
        strict_pass = bool(actual.get("changed")) and _contains_any(combined.lower(), "weak", "medium", "strong", "safe", "strength", "good", "poor")
        bucket = "" if strict_pass else "password_no_visible_strength_text_change"
        strict_reason = "weak and stronger password inputs must change visible strength feedback"
    elif _is_drawing(text):
        strict_pass = bool(actual.get("changed"))
        bucket = "" if strict_pass else "drawing_canvas_no_pixel_change"
        strict_reason = "drawing interaction must change canvas pixels"
    elif not probe:
        strict_pass = False
        bucket = "probe_inconclusive"
        strict_reason = "missing behavior probe evidence"

    strict_label = "PASS" if strict_pass else "FAIL"
    false_positive = raw_label == "PASS" and strict_label != "PASS"
    false_negative = raw_label != "PASS" and strict_label == "PASS"
    return {
        "strict_final_verdict": strict_label,
        "product_pass": strict_pass,
        "primary_behavior_failure_bucket": "" if strict_pass else bucket or "behavior_failed_unbucketed",
        "secondary_behavior_failure_bucket": "" if strict_pass else secondary_bucket,
        "score_integrity_failure": false_positive,
        "report_verdict_mismatch": raw_label != strict_label,
        "false_positive_correction": false_positive,
        "false_negative_correction": false_negative,
        "classification": (
            "false_positive_pass"
            if false_positive
            else "false_negative_fail"
            if false_negative
            else "verified_pass"
            if strict_pass
            else "verified_fail"
        ),
        "strict_reason": strict_reason,
        "raw_behavior_pass": raw_probe_pass,
        "raw_final_verdict": raw_label,
    }


def classify_repair_failure_bucket(repair_result: dict[str, Any] | None) -> str:
    repair = repair_result or {}
    reason_codes = [str(code) for code in repair.get("reason_codes") or []]
    if "free_floating_code_no_path_action" in reason_codes:
        return "repair_free_floating_code_no_path_action"
    if "missing_probe_metadata" in reason_codes or "repair_metadata_incomplete" in reason_codes:
        return "repair_handoff_missing_probe_metadata"
    if str(repair.get("status") or repair.get("repair_status") or "").upper() == "HANDOFF":
        return str(reason_codes[0] if reason_codes else "repair_handoff")
    if int(repair.get("attempts_used") or repair.get("repair_attempts") or 0) > 0 and reason_codes:
        return str(reason_codes[0])
    return ""


def _verdict(label: CanonicalFinalVerdict, reason_codes: list[str], behavior_verdict: str) -> dict[str, Any]:
    return {
        "label": label,
        "product_pass": label == "PASS",
        "behavior_verdict": behavior_verdict or "UNVERIFIED",
        "reason_codes": sorted(set(reason_codes)),
    }


def _first_probe(contract: dict[str, Any]) -> dict[str, Any]:
    targets = contract.get("probe_targets") if isinstance(contract.get("probe_targets"), list) else []
    return targets[0] if targets and isinstance(targets[0], dict) else {}


def _observed_dict(probe: dict[str, Any]) -> dict[str, Any]:
    observed = probe.get("actual") or probe.get("observed") or {}
    return observed if isinstance(observed, dict) else {}


def _observed_value(probe: dict[str, Any], key: str) -> Any:
    observed = _observed_dict(probe)
    if key in observed:
        return observed[key]
    return probe.get(key)


def _passed_stage(label: str, repair_attempt_count: int) -> str:
    if label == "PASS" and repair_attempt_count > 0:
        return "passed_after_repair"
    if label == "PASS":
        return "passed_initially"
    if label == "HANDOFF":
        return "handoff_before_or_after_repair"
    if repair_attempt_count > 0:
        return "failed_after_repair"
    return "failed_or_unverified_before_repair"


def _preview_bucket(route_status: str, text: str) -> str:
    if str(route_status or "").upper() == "EXPECTED-BLOCKED":
        return "route_blocked_no_preview"
    if _is_theme(text):
        return "theme_preview_resolution_failed"
    return "preview_resolution_failed"


def _text_changed(actual: dict[str, Any]) -> bool:
    return str(actual.get("after") or "") != str(actual.get("before") or "")


def _has_digit(value: str) -> bool:
    return any(ch.isdigit() for ch in value)


def _contains_any(text: str, *terms: str) -> bool:
    return any(term in text for term in terms)


def _is_notes(text: str) -> bool:
    return re.search(r"\b(notes?|scratch|jot|memo)\b", text) is not None


def _is_list(text: str) -> bool:
    return _contains_any(text, "checklist", "grocery", "pantry", "packing list", "farmers market")


def _is_calculator(text: str) -> bool:
    return _contains_any(text, "tip", "split", "bill", "share", "splitter", "money", "pizza", "gas", "cost", "calculator")


def _is_timer(text: str) -> bool:
    return _contains_any(text, "timer", "countdown", "steep")


def _is_theme(text: str) -> bool:
    return _contains_any(text, "theme", "light", "dark", "night", "day", "midnight", "sunrise", "mode toggle", "color flipper")


def _is_weather(text: str) -> bool:
    return _contains_any(text, "weather", "forecast")


def _is_player(text: str) -> bool:
    return _contains_any(text, "podcast", "player", "mixtape", "music", "audio", "radio")


def _is_tracker(text: str) -> bool:
    return _contains_any(text, "tracker", "counter", "coffee", "cup", "water", "glass", "pushup", "rep")


def _is_password(text: str) -> bool:
    return _contains_any(text, "password", "passphrase", "safety", "strength", "gauge")


def _is_drawing(text: str) -> bool:
    return _contains_any(text, "doodle", "drawing", "draw", "sketch", "canvas")
