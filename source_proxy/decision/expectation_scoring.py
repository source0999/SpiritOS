from __future__ import annotations

import re
from typing import Any


EXPECTATION_SCORE_VERSION = "source-proxy-expectation-score-v0.1"

EXPECTED_INTERACTION_BY_PROBE = {
    "timer-start-stop-freeze": "stateful_controls",
    "calculator-basic-arithmetic": "numeric_result",
    "theme-computed-color-change": "visual_state_toggle",
    "todo-add-and-change-item": "list_mutation",
    "weather-card-fields": "demo_data_display",
    "music-player-control-state": "control_state_change",
    "habit-state-change": "tracker_mutation",
    "notes-create-edit-visible-note": "text_create_or_update",
    "password-strength-feedback-change": "input_feedback",
    "drawing-surface-changes": "canvas_mutation",
}


def build_expectation_score(
    *,
    score: dict[str, Any],
    receipt: dict[str, Any] | None = None,
    browser_open_result: dict[str, Any] | None = None,
    behavior_probe_result: dict[str, Any] | None = None,
    diagnostic_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    receipt = receipt or {}
    browser = browser_open_result or {}
    behavior = behavior_probe_result or {}
    diagnostic = diagnostic_row or {}
    contract = score.get("behavior_contract") if isinstance(score.get("behavior_contract"), dict) else {}
    probes = contract.get("probe_targets") if isinstance(contract.get("probe_targets"), list) else []
    probe_ids = [str(probe.get("probe_id") or "") for probe in probes if isinstance(probe, dict)]
    original_prompt = str(score.get("prompt") or diagnostic.get("prompt") or "")
    route_status = str(score.get("route_status") or score.get("status") or "").upper()
    behavior_verdict = str(behavior.get("verdict") or diagnostic.get("behavior_probe_verdict") or "").upper()
    browser_opened = _bool_from_evidence(browser.get("opened"), diagnostic.get("artifact_opens"), score.get("openable_homepage"))
    console_errors = _count_console_errors(browser, diagnostic)
    page_errors = len(browser.get("pageErrors") or diagnostic.get("runtime_errors") or [])
    external_resources = _list(score.get("external_resources") or diagnostic.get("external_urls_or_remote_resources"))
    missing_refs = _list(diagnostic.get("missing_local_references") or score.get("missing_local_references"))
    backend_authored = bool(score.get("backend_created_content") or diagnostic.get("backend_created_content"))
    real_app_touched = bool(score.get("real_app_touched") or diagnostic.get("real_app_files_touched"))
    file_integrity_ok = bool(score.get("file_equals_model_action_content") or diagnostic.get("file_bytes_match_model_authored_content"))
    model_authored_paths = _list(score.get("model_authored_targets") or diagnostic.get("model_authored_targets"))
    proxy_paths = _proxy_suggested_paths(score)
    sidecar_live = bool((score.get("model_lane_observability") or {}).get("sidecar_lanes_live") or diagnostic.get("sidecar_lanes_used"))
    web_search_used = bool(diagnostic.get("web_search_used") or score.get("web_search_used"))
    context_sources = _context_sources(score, diagnostic)
    local_intel = _list(diagnostic.get("local_intelligence_gathered") or diagnostic.get("local_intelligence_used"))

    route_safety = _score_route(route_status)
    artifact_creation = _score_artifact_creation(score)
    model_authorship = _score_model_authorship(file_integrity_ok, backend_authored, model_authored_paths)
    browser_open = 100 if browser_opened and page_errors == 0 else 0 if not browser_opened else 75
    behavior_score = _score_behavior(behavior_verdict, behavior)
    intent_fit = _score_intent_fit(score, diagnostic, behavior_score)
    usability = _score_usability(behavior_score, console_errors, page_errors, missing_refs)
    context_score = _score_context(web_search_used, original_prompt)
    lane_score = _score_lane(score, sidecar_live)
    safety_score = _score_safety(real_app_touched, backend_authored, score)

    reason_codes = []
    reason_codes.extend(_dimension_reasons("route", route_safety))
    reason_codes.extend(_dimension_reasons("artifact", artifact_creation))
    reason_codes.extend(_dimension_reasons("model_authorship", model_authorship))
    reason_codes.extend(_dimension_reasons("browser_open", browser_open))
    reason_codes.extend(_dimension_reasons("behavior", behavior_score))
    reason_codes.extend(_dimension_reasons("usability", usability))
    reason_codes.extend(_dimension_reasons("context", context_score))
    reason_codes.extend(_dimension_reasons("lane", lane_score))
    reason_codes.extend(_dimension_reasons("safety", safety_score))
    if web_search_used and not _prompt_needs_current_info(original_prompt):
        reason_codes.append("web_search_unnecessary_for_local_artifact_prompt")
    if not web_search_used and not _prompt_needs_current_info(original_prompt):
        reason_codes.append("web_search_correctly_not_used")
    if external_resources:
        reason_codes.append("external_resources_present_review_reasonability")
    else:
        reason_codes.append("no_external_resources_detected")
    if missing_refs:
        reason_codes.append("missing_linked_local_files")
    if console_errors:
        reason_codes.append("browser_console_errors_present")
    if page_errors:
        reason_codes.append("browser_page_errors_present")
    if behavior_verdict in {"", "UNVERIFIED", "NOT_RUN", "SKIPPED", "UNKNOWN"}:
        reason_codes.append("behavior_evidence_missing")
    if behavior_verdict == "FAIL" and _looks_like_no_state_change(behavior):
        reason_codes.append("controls_present_but_no_state_change")
    if backend_authored:
        reason_codes.append("backend_authored_content_detected")
    if real_app_touched:
        reason_codes.append("real_app_files_touched")
    if sidecar_live:
        reason_codes.append("sidecar_lane_live_requires_approval")
    else:
        reason_codes.append("sidecar_lanes_preview_only")

    product_verdict = _product_verdict(
        route_safety=route_safety,
        artifact_creation=artifact_creation,
        model_authorship=model_authorship,
        browser_open=browser_open,
        behavior_score=behavior_score,
        intent_fit=intent_fit,
        usability=usability,
        lane_score=lane_score,
        safety_score=safety_score,
        behavior_verdict=behavior_verdict,
    )
    if product_verdict == "PASS" and behavior_verdict != "PASS":
        reason_codes.append("final_pass_without_browser_evidence")
        product_verdict = "WEAK_PASS"

    return {
        "expectation_score_version": EXPECTATION_SCORE_VERSION,
        "original_prompt": original_prompt,
        "inferred_intent": _inferred_intent(score, diagnostic),
        "intent_confidence": _intent_confidence(score, diagnostic),
        "intent_reason_codes": _intent_reason_codes(score, diagnostic),
        "task_shape": str(score.get("task_shape") or diagnostic.get("task_shape") or ""),
        "artifact_class": str(score.get("artifact_class") or diagnostic.get("artifact_class") or ""),
        "expected_artifact_kind": _expected_artifact_kind(score, diagnostic),
        "expected_interaction_level": _expected_interaction_level(probe_ids),
        "expected_primary_behaviors": _expected_primary_behaviors(probes),
        "expected_non_goals": _expected_non_goals(original_prompt),
        "selected_entrypoint": str(score.get("selected_preview_path") or diagnostic.get("selected_preview_path") or ""),
        "entrypoint_reason": str(score.get("preview_selection_reason") or diagnostic.get("preview_selection_reason") or ""),
        "model_authored_paths": model_authored_paths,
        "proxy_suggested_paths": proxy_paths,
        "backend_authored_content_detected": backend_authored,
        "file_integrity_verdict": "PASS" if file_integrity_ok and not backend_authored else "FAIL",
        "missing_local_references": missing_refs,
        "external_resources": external_resources,
        "external_resource_reasonability": _external_resource_reasonability(original_prompt, external_resources),
        "browser_open_verdict": "PASS" if browser_opened else "FAIL",
        "console_error_count": console_errors,
        "page_error_count": page_errors,
        "behavior_probe_results": behavior or diagnostic.get("behavior_probe_actual") or {},
        "behavior_score": behavior_score,
        "usability_score": usability,
        "intent_fit_score": intent_fit,
        "route_safety_score": route_safety,
        "artifact_creation_score": artifact_creation,
        "model_authorship_score": model_authorship,
        "browser_open_score": browser_open,
        "context_discipline_score": context_score,
        "model_lane_discipline_score": lane_score,
        "safety_boundary_score": safety_score,
        "context_decision": _context_decision(original_prompt, web_search_used, context_sources),
        "context_sources_used": context_sources,
        "web_search_decision": "not_needed" if not _prompt_needs_current_info(original_prompt) else "needed_if_current_facts_required",
        "web_search_used": web_search_used,
        "local_intelligence_used": local_intel,
        "model_lane_selected": str(score.get("selected_coder_lane") or diagnostic.get("selected_primary_model_lane") or score.get("model_id") or ""),
        "sidecar_lanes_live": sidecar_live,
        "lane_policy_verdict": "PASS" if lane_score >= 90 else "FAIL",
        "safety_boundary_verdict": "PASS" if safety_score >= 90 else "FAIL",
        "product_verdict": product_verdict,
        "score_reason_codes": sorted(set(reason_codes)),
        "human_review_notes": _human_review_notes(product_verdict, behavior_score, usability, external_resources),
    }


def expectation_score_reason_vocabulary() -> dict[str, str]:
    return {
        "route_pass": "route and safety gates completed",
        "route_weak": "route completed but not strongly",
        "route_fail": "route did not complete safely",
        "artifact_pass": "artifact files were created",
        "artifact_fail": "artifact files were missing",
        "model_authorship_pass": "files and bytes match model-authored actions",
        "model_authorship_fail": "model authorship or byte integrity is missing",
        "browser_open_pass": "selected entrypoint opened in a browser",
        "browser_open_fail": "selected entrypoint did not open",
        "behavior_pass": "browser behavior probe passed",
        "behavior_unverified": "behavior evidence is missing or not authoritative yet",
        "behavior_fail": "browser behavior probe failed",
        "usability_pass": "visible interaction and runtime quality are acceptable for this probe",
        "usability_weak": "basic behavior may work but usability evidence is shallow",
        "context_pass": "context/search choices match the prompt",
        "lane_pass": "Qwen primary lane and preview-only sidecar policy were preserved",
        "safety_pass": "no real app mutation, backend content, or hidden escalation detected",
        "missing_linked_local_files": "generated HTML references local scripts, styles, images, or media that were not created",
        "external_resources_present_review_reasonability": "external resources are present and should be reviewed against inferred intent",
        "browser_console_errors_present": "browser console produced error or warning messages",
        "browser_page_errors_present": "browser reported page runtime errors",
        "behavior_evidence_missing": "browser behavior evidence is not attached yet",
        "controls_present_but_no_state_change": "controls existed but the browser probe did not observe visible state change",
        "final_pass_without_browser_evidence": "final PASS was blocked because browser behavior evidence was missing",
        "web_search_unnecessary_for_local_artifact_prompt": "web search was used even though the prompt looked local/artifact-only",
        "web_search_correctly_not_used": "web search was not used for a local/artifact prompt",
        "sidecar_lane_live_requires_approval": "a sidecar lane was live despite preview-only policy",
        "backend_authored_content_detected": "artifact content appears to have been backend-authored rather than model-authored",
    }


def _score_route(route_status: str) -> int:
    return 100 if route_status == "GO" else 50 if route_status == "EXPECTED-BLOCKED" else 0


def _score_artifact_creation(score: dict[str, Any]) -> int:
    return 100 if score.get("files_changed") or score.get("workspace_files") else 0


def _score_model_authorship(file_integrity_ok: bool, backend_authored: bool, model_authored_paths: list[str]) -> int:
    if file_integrity_ok and model_authored_paths and not backend_authored:
        return 100
    if model_authored_paths and not backend_authored:
        return 70
    return 0


def _score_behavior(behavior_verdict: str, behavior: dict[str, Any]) -> int:
    if behavior_verdict == "PASS" and bool(behavior.get("passed", True)):
        return 100
    if behavior_verdict == "FAIL":
        return 0
    if behavior_verdict in {"NEEDS_FIX", "ERROR"}:
        return 25
    return 50


def _score_intent_fit(score: dict[str, Any], diagnostic: dict[str, Any], behavior_score: int) -> int:
    if diagnostic.get("artifact_matches_plain_user_intent") is True:
        return 100
    if score.get("route_type") == "product" and score.get("artifact_class") in {"static_ui_artifact", "html_static_page"}:
        return 85 if behavior_score >= 50 else 70
    return 50


def _score_usability(behavior_score: int, console_errors: int, page_errors: int, missing_refs: list[str]) -> int:
    score = behavior_score
    score -= min(console_errors * 10, 30)
    score -= min(page_errors * 20, 50)
    score -= min(len(missing_refs) * 15, 45)
    return max(0, min(100, score))


def _score_context(web_search_used: bool, prompt: str) -> int:
    if web_search_used and not _prompt_needs_current_info(prompt):
        return 60
    if not web_search_used and _prompt_needs_current_info(prompt):
        return 70
    return 100


def _score_lane(score: dict[str, Any], sidecar_live: bool) -> int:
    selected = str(score.get("selected_coder_lane") or score.get("model_id") or "")
    if sidecar_live:
        return 0
    if selected in {"qwen_local_coder", "qwen2.5-coder:7b"}:
        return 100
    return 70 if selected else 50


def _score_safety(real_app_touched: bool, backend_authored: bool, score: dict[str, Any]) -> int:
    if real_app_touched or backend_authored:
        return 0
    if score.get("fallback_used") or score.get("deterministic_scaffold_used") or score.get("dummy_fixture_used"):
        return 40
    return 100


def _product_verdict(
    *,
    route_safety: int,
    artifact_creation: int,
    model_authorship: int,
    browser_open: int,
    behavior_score: int,
    intent_fit: int,
    usability: int,
    lane_score: int,
    safety_score: int,
    behavior_verdict: str,
) -> str:
    if min(route_safety, artifact_creation, model_authorship, browser_open, lane_score, safety_score) <= 0:
        return "FAIL"
    if behavior_verdict in {"NEEDS_FIX", "ERROR"}:
        return "NEEDS_FIX"
    if behavior_verdict in {"", "UNVERIFIED", "NOT_RUN", "SKIPPED", "UNKNOWN"}:
        return "WEAK_PASS" if min(route_safety, artifact_creation, model_authorship, browser_open, lane_score, safety_score) >= 90 else "NEEDS_FIX"
    if behavior_score < 50:
        return "FAIL"
    if min(intent_fit, usability) < 80:
        return "WEAK_PASS"
    return "PASS"


def _dimension_reasons(prefix: str, score: int) -> list[str]:
    if score >= 90:
        return [f"{prefix}_pass"]
    if score >= 50:
        return [f"{prefix}_weak"]
    return [f"{prefix}_fail"]


def _inferred_intent(score: dict[str, Any], diagnostic: dict[str, Any]) -> str:
    return str(
        diagnostic.get("inferred_user_intent")
        or score.get("task_shape")
        or score.get("artifact_score_kind")
        or ""
    )


def _intent_confidence(score: dict[str, Any], diagnostic: dict[str, Any]) -> str:
    if diagnostic.get("proxy_confidence"):
        return str(diagnostic["proxy_confidence"])
    if score.get("task_shape_source") == "generic_artifact_resolver":
        return "medium_high"
    if score.get("task_shape"):
        return "medium"
    return "unknown"


def _intent_reason_codes(score: dict[str, Any], diagnostic: dict[str, Any]) -> list[str]:
    codes = []
    if score.get("route_type") == "product":
        codes.append("product_route_selected")
    if score.get("task_shape"):
        codes.append("task_shape_inferred")
    if score.get("artifact_class"):
        codes.append("artifact_class_inferred")
    if diagnostic.get("artifact_matches_plain_user_intent") is True:
        codes.append("plain_intent_behavior_probe_matched")
    return codes


def _expected_artifact_kind(score: dict[str, Any], diagnostic: dict[str, Any]) -> str:
    artifact = str(score.get("artifact_class") or diagnostic.get("artifact_class") or "")
    if artifact == "static_ui_artifact":
        return "browser_viewable_static_ui"
    if artifact == "html_static_page":
        return "browser_viewable_html_page"
    return artifact or "unknown"


def _expected_interaction_level(probe_ids: list[str]) -> str:
    if not probe_ids:
        return "unverified"
    levels = {EXPECTED_INTERACTION_BY_PROBE.get(probe, "interactive") for probe in probe_ids}
    return ",".join(sorted(levels))


def _expected_primary_behaviors(probes: list[Any]) -> list[dict[str, str]]:
    out = []
    for probe in probes:
        if not isinstance(probe, dict):
            continue
        out.append(
            {
                "probe_id": str(probe.get("probe_id") or ""),
                "acceptance_criterion": str(probe.get("acceptance_criterion") or ""),
                "expected_observation": str(probe.get("expected_observation") or ""),
            }
        )
    return out


def _expected_non_goals(prompt: str) -> list[str]:
    non_goals = ["provider_or_cloud_call", "real_app_mutation", "secret_or_env_mutation", "model_self_report_as_pass"]
    if not _prompt_needs_current_info(prompt):
        non_goals.append("web_search_or_current_fact_lookup")
    return non_goals


def _external_resource_reasonability(prompt: str, resources: list[str]) -> str:
    if not resources:
        return "none_detected"
    if re.search(r"\b(embed|youtube|url|remote|live|current)\b", prompt.lower()):
        return "potentially_reasonable_for_prompt_review_required"
    return "unexpected_for_local_artifact_prompt_review_required"


def _context_decision(prompt: str, web_search_used: bool, context_sources: list[str]) -> dict[str, Any]:
    return {
        "web_search_needed": _prompt_needs_current_info(prompt),
        "web_search_used": web_search_used,
        "local_context_needed": False,
        "context_sources_used": context_sources,
        "reason_codes": ["blunt_local_artifact_prompt", "repo_context_not_required"],
    }


def _context_sources(score: dict[str, Any], diagnostic: dict[str, Any]) -> list[str]:
    sources = []
    if score.get("behavior_contract") or (diagnostic.get("context_packet_summary") or {}).get("behavior_probe_ids"):
        sources.append("behavior_contract")
    if score.get("task_shape") or diagnostic.get("task_shape"):
        sources.append("task_spec_intake")
    if score.get("model_lane_observability") or diagnostic.get("model_lane_observability"):
        sources.append("model_lane_observability")
    return sorted(set(sources))


def _human_review_notes(product_verdict: str, behavior_score: int, usability: int, external_resources: list[str]) -> str:
    if product_verdict == "PASS":
        return "Evidence supports PASS for the obvious behavior probe; review polish separately."
    if product_verdict == "WEAK_PASS":
        return "Core artifact signals are healthy but behavior/usability evidence is incomplete or shallow."
    if external_resources:
        return "Review external resource reasonability before final acceptance."
    if behavior_score < 50:
        return "Behavior evidence failed; inspect model output and verifier probe before patching."
    if usability < 80:
        return "Behavior exists but usability depth is weak."
    return "Review missing evidence and reason codes."


def _prompt_needs_current_info(prompt: str) -> bool:
    return bool(re.search(r"\b(current|latest|today|live|real[- ]?time|news|weather now)\b", prompt.lower()))


def _looks_like_no_state_change(behavior: dict[str, Any]) -> bool:
    text = str(behavior.get("reason") or "").lower()
    codes = " ".join(str(code).lower() for code in behavior.get("reason_codes") or [])
    return "state" in text and "change" in text or "state_change" in codes


def _bool_from_evidence(*values: Any) -> bool:
    return any(value is True for value in values)


def _count_console_errors(browser: dict[str, Any], diagnostic: dict[str, Any]) -> int:
    messages = browser.get("consoleMessages") or diagnostic.get("browser_console_errors") or []
    return sum(1 for item in messages if isinstance(item, dict) and item.get("type") in {"error", "warning"})


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def _proxy_suggested_paths(score: dict[str, Any]) -> list[str]:
    target = str(score.get("proxy_exact_target_suggested") or "")
    if target:
        return [target]
    if score.get("system_preselected_target"):
        return _list(score.get("openable_homepage_paths"))
    return []
