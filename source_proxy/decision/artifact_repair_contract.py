from __future__ import annotations

from typing import Any


FAILURE_PACKET_VERSION = "source-proxy-artifact-failure-packet-v0.2.phase-4"
REPAIR_PROMPT_VERSION = "source-proxy-artifact-repair-prompt-v0.2.phase-4"
DEFAULT_FORBIDDEN_PATHS = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "certificates/*",
    "source_proxy/**",
    "src/**",
    "app/**",
    "pages/**",
    "scripts/**",
]


def build_artifact_failure_packet(
    *,
    prompt: str,
    behavior_contract: dict[str, Any],
    verifier_result: dict[str, Any],
    evidence_packet: dict[str, Any] | None,
    allowed_workspace: str,
    attempt_count: int = 0,
    screenshot_refs: list[str] | None = None,
    log_refs: list[str] | None = None,
) -> dict[str, Any]:
    artifact_path = str(verifier_result.get("path") or "")
    observed = verifier_result.get("observed") if isinstance(verifier_result.get("observed"), dict) else {}
    reason = str(verifier_result.get("reason") or "")
    verdict = str(verifier_result.get("verdict") or "").upper()
    reason_codes = _dedupe(
        [
            *_reason_codes_from_contract(behavior_contract),
            *_reason_codes_from_evidence(evidence_packet or {}),
            _reason_code_from_reason(reason),
        ]
    )
    handoff_reasons: list[str] = []

    if verdict not in {"FAIL", "UNVERIFIED", "NEEDS_FIX", "BLOCKED"}:
        handoff_reasons.append("verifier_result_not_failed")
    if not artifact_path:
        handoff_reasons.append("artifact_path_missing")
    if artifact_path and not _path_within_workspace(artifact_path, allowed_workspace):
        handoff_reasons.append("artifact_path_outside_allowed_workspace")
    if not evidence_packet:
        handoff_reasons.append("evidence_packet_missing")
    if not behavior_contract.get("probe_targets"):
        handoff_reasons.append("behavior_contract_probe_missing")

    status = "HANDOFF" if handoff_reasons else "READY_FOR_LOCAL_REPAIR"
    expected_behavior = _expected_behavior(behavior_contract)

    return {
        "packet_version": FAILURE_PACKET_VERSION,
        "status": status,
        "handoff_required": status == "HANDOFF",
        "handoff_reasons": sorted(set(handoff_reasons)),
        "prompt": prompt,
        "artifact_paths": [artifact_path] if artifact_path else [],
        "allowed_workspace": allowed_workspace,
        "forbidden_paths": list(DEFAULT_FORBIDDEN_PATHS),
        "attempt_count": attempt_count,
        "max_attempts_hint": 1,
        "behavior_contract": behavior_contract,
        "expected_behavior": expected_behavior,
        "observed_behavior": {
            "test": str(verifier_result.get("test") or ""),
            "verdict": verdict or "UNVERIFIED",
            "observed": observed,
            "reason": reason,
        },
        "reason_codes": sorted(set(reason_codes + handoff_reasons)),
        "evidence_refs": {
            "evidence_packet_path": str((evidence_packet or {}).get("evidence_packet_path") or ""),
            "receipt_path": str((evidence_packet or {}).get("receipt_path") or ""),
            "score_path": str((evidence_packet or {}).get("score_path") or ""),
            "transcript_path": str((evidence_packet or {}).get("transcript_path") or ""),
            "diff_path": str((evidence_packet or {}).get("diff_path") or ""),
            "screenshots": list(screenshot_refs or []),
            "logs": list(log_refs or []),
        },
        "repair_scope": {
            "local_only": True,
            "disposable_workspace_only": True,
            "provider_api_allowed": False,
            "production_paths_allowed": False,
            "full_solution_in_prompt_allowed": False,
        },
    }


def build_behavior_failure_packet(
    *,
    prompt: str,
    artifact_class: str,
    behavior_contract: dict[str, Any],
    behavior_probe: dict[str, Any],
    selected_preview_path: str,
    generated_files: list[str],
    model_authored_targets: list[str],
    final_reason_codes: list[str],
    allowed_workspace: str,
    attempt_count: int = 0,
    console_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a bounded repair packet from an executed browser behavior failure."""

    observed = behavior_probe.get("actual") or behavior_probe.get("observed") or {}
    expected = _expected_behavior_from_contract_or_probe(behavior_contract, behavior_probe)
    probe_id = str(behavior_probe.get("probe_id") or behavior_probe.get("test") or expected.get("probe_id") or "")
    if probe_id and not expected.get("probe_id"):
        expected["probe_id"] = probe_id
    handoff_reasons: list[str] = []
    if str(behavior_probe.get("verdict") or "").upper() != "FAIL":
        handoff_reasons.append("behavior_probe_not_failed")
    if not selected_preview_path:
        handoff_reasons.append("selected_preview_path_missing")
    if selected_preview_path and not _path_within_workspace(selected_preview_path, allowed_workspace):
        handoff_reasons.append("selected_preview_path_outside_allowed_workspace")
    if not expected.get("acceptance_criterion") and not expected.get("expected_observation"):
        handoff_reasons.append("missing_probe_metadata")
    status = "HANDOFF" if handoff_reasons else "READY_FOR_LOCAL_REPAIR"
    actual = observed if isinstance(observed, dict) else {}
    probe_summary = _probe_evidence_summary(behavior_probe, actual)
    primary_bucket = str(
        behavior_probe.get("primary_behavior_failure_bucket")
        or behavior_probe.get("failureBucket")
        or ""
    )
    artifact_family = _artifact_family_for_probe(expected.get("probe_id") or probe_id, prompt)
    observed_before = _first_present(actual, behavior_probe, "before")
    observed_after = _first_present(actual, behavior_probe, "after")

    return {
        "packet_version": FAILURE_PACKET_VERSION,
        "status": status,
        "handoff_required": status == "HANDOFF",
        "handoff_reasons": sorted(set(handoff_reasons)),
        "failure_kind": "post_behavior_probe_failure",
        "prompt": prompt,
        "original_prompt": prompt,
        "artifact_family": artifact_family,
        "artifact_class": artifact_class,
        "artifact_paths": [selected_preview_path] if selected_preview_path else [],
        "selected_preview_path": selected_preview_path,
        "allowed_workspace": allowed_workspace,
        "forbidden_paths": list(DEFAULT_FORBIDDEN_PATHS),
        "attempt_count": attempt_count,
        "repair_attempt_count": attempt_count,
        "max_attempts_hint": 1,
        "behavior_contract": behavior_contract,
        "behavior_contract_id": str(behavior_contract.get("contract_version") or ""),
        "probe_id": probe_id,
        "expected_behavior": expected,
        "expected_observable_behavior": expected.get("expected_observation") or expected.get("acceptance_criterion") or "",
        "observed_behavior": {
            "test": probe_id,
            "verdict": str(behavior_probe.get("verdict") or "FAIL").upper(),
            "observed": actual,
            "actual": actual,
            "expected": behavior_probe.get("expected") if isinstance(behavior_probe.get("expected"), dict) else str(behavior_probe.get("expected") or ""),
            "before": observed_before,
            "after": observed_after,
            "reason": str(behavior_probe.get("reason") or ""),
        },
        "primary_behavior_failure_bucket": primary_bucket,
        "secondary_behavior_failure_bucket": str(behavior_probe.get("secondary_behavior_failure_bucket") or ""),
        "behavior_probe_evidence": probe_summary,
        "observed_before": observed_before,
        "observed_after": observed_after,
        "observed_interaction": _observed_interaction_summary(probe_summary),
        "why_this_failed": _why_this_failed(primary_bucket, actual, str(behavior_probe.get("reason") or "")),
        "current_files_summary": {
            "selected_preview_path": selected_preview_path,
            "generated_files": list(generated_files),
            "model_authored_targets": list(model_authored_targets),
            "loaded_preview_must_remain_browser_openable": True,
        },
        "required_repair": _required_repair_for_bucket(primary_bucket, artifact_family),
        "required_output_format": "Source Proxy WriteFile JSON action or <file path=\"RELATIVE_ALLOWED_FILE\"> block only",
        "console_details": console_details or {},
        "console_open_summary": {
            "console": console_details or {},
            "open_status": str(behavior_probe.get("open_status") or behavior_probe.get("preview_open_status") or ""),
        },
        "generated_files": list(generated_files),
        "file_list": list(generated_files),
        "model_authored_targets": list(model_authored_targets),
        "current_final_reason_codes": list(final_reason_codes),
        "reason_codes": sorted(
            set(
                code
                for code in [
                    f"behavior_probe_failed:{probe_id}" if probe_id else "behavior_probe_failed",
                    "behavior_failed_verified",
                    *[str(code) for code in behavior_probe.get("reason_codes") or []],
                    *[str(code) for code in final_reason_codes if str(code) != "behavior_required_but_unverified"],
                    *handoff_reasons,
                    "repair_metadata_incomplete" if handoff_reasons else "",
                ]
                if code
            )
        ),
        "repair_scope": {
            "local_only": True,
            "disposable_workspace_only": True,
            "provider_api_allowed": False,
            "production_paths_allowed": False,
            "full_solution_in_prompt_allowed": False,
            "allowed_extensions": [".html", ".css", ".js"],
            "max_attempts": 1,
        },
    }


def build_repair_prompt_from_failure_packet(packet: dict[str, Any]) -> str:
    if packet.get("handoff_required"):
        reasons = ", ".join(packet.get("handoff_reasons") or ["handoff_required"])
        return (
            f"{REPAIR_PROMPT_VERSION}\n"
            "Do not attempt local repair.\n"
            f"Reason: {reasons}.\n"
            "Produce HANDOFF with the packet evidence and approval needed."
        )

    observed = packet.get("observed_behavior") or {}
    expected = packet.get("expected_behavior") or {}
    current_files_summary = packet.get("current_files_summary") if isinstance(packet.get("current_files_summary"), dict) else {}
    artifact_paths = ", ".join(packet.get("artifact_paths") or [])
    forbidden_paths = ", ".join(packet.get("forbidden_paths") or [])
    actions = "; ".join(expected.get("observable_actions") or [])
    allowed_files = ", ".join(_allowed_relative_files(packet))
    primary_bucket = str(packet.get("primary_behavior_failure_bucket") or "")
    artifact_family = str(packet.get("artifact_family") or _artifact_family_for_probe(expected.get("probe_id"), packet.get("prompt")))
    observed_before = packet.get("observed_before", observed.get("before"))
    observed_after = packet.get("observed_after", observed.get("after"))
    observed_interaction = str(packet.get("observed_interaction") or "")
    why_this_failed = str(packet.get("why_this_failed") or "")
    required_repair = str(packet.get("required_repair") or _required_repair_for_bucket(primary_bucket, artifact_family))

    return (
        f"{REPAIR_PROMPT_VERSION}\n"
        "You are repairing a disposable generated artifact only.\n"
        f"artifact_family: {artifact_family}\n"
        f"original_prompt: {packet.get('original_prompt') or packet.get('prompt') or ''}\n"
        f"selected_preview_path: {packet.get('selected_preview_path') or artifact_paths}\n"
        f"allowed_workspace: {packet.get('allowed_workspace') or ''}\n"
        f"allowed_files: {allowed_files}\n"
        f"forbidden_paths: {forbidden_paths}\n"
        f"failed_probe_id: {packet.get('probe_id') or expected.get('probe_id') or observed.get('test') or ''}\n"
        f"expected_behavior: {expected.get('acceptance_criterion') or ''}\n"
        f"expected_observation: {expected.get('expected_observation') or ''}\n"
        f"observable_actions: {actions}\n"
        f"primary_failure_bucket: {primary_bucket}\n"
        f"Primary failure bucket: {primary_bucket}\n"
        f"observed_before: {observed_before}\n"
        f"observed_after: {observed_after}\n"
        f"observed_interaction: {observed_interaction}\n"
        f"why_this_failed: {why_this_failed}\n"
        f"current_files_summary: {current_files_summary}\n"
        f"required_repair: {required_repair}\n"
        "required_output_format: Source Proxy WriteFile JSON action or <file path=\"RELATIVE_ALLOWED_FILE\"> block only\n"
        "Do not edit production source, do not use network, do not call providers, and do not create files outside the allowed workspace.\n"
        "Use only relative .html, .css, and .js paths already in the disposable artifact, and keep at least one browser-openable .html file.\n"
        "If you change an element id, class, script selector, linked script, or linked stylesheet, update every loaded file that depends on it.\n"
        "Repair the existing artifact so the visible state changes for the behavior contract. "
        "Return only one of these accepted path-bound formats for allowed artifact files:\n"
        "1. Source Proxy JSON: {\"action_type\":\"WriteFile\",\"target\":\"RELATIVE_ALLOWED_FILE\",\"arguments\":{\"content\":\"FULL FILE BYTES\"},\"reason\":\"repair behavior\"}\n"
        "2. File block: <file path=\"RELATIVE_ALLOWED_FILE\">FULL FILE BYTES</file>\n"
        "Do not return markdown-only code fences unless the line immediately before the fence names the allowed file path. "
        "Do not include free-floating code, prose-only advice, benchmark answer keys, shell commands, package files, external CDNs, background workers, backend-authored rescue content, scorer changes, fallback scaffolds, or full solution code outside model-authored file content."
    )


def _expected_behavior(contract: dict[str, Any]) -> dict[str, Any]:
    targets = contract.get("probe_targets") if isinstance(contract.get("probe_targets"), list) else []
    first = targets[0] if targets and isinstance(targets[0], dict) else {}
    return {
        "probe_id": str(first.get("probe_id") or ""),
        "acceptance_criterion": str(first.get("acceptance_criterion") or ""),
        "observable_actions": list(first.get("observable_actions") or []),
        "expected_observation": str(first.get("expected_observation") or ""),
        "minimum_proof_tier": first.get("minimum_proof_tier", 2),
    }


def _expected_behavior_from_contract_or_probe(
    contract: dict[str, Any],
    behavior_probe: dict[str, Any],
) -> dict[str, Any]:
    expected = _expected_behavior(contract)
    probe_expected = behavior_probe.get("expected") if isinstance(behavior_probe.get("expected"), dict) else {}
    probe_expected_text = behavior_probe.get("expected") if isinstance(behavior_probe.get("expected"), str) else ""
    probe_id = str(
        expected.get("probe_id")
        or behavior_probe.get("probe_id")
        or behavior_probe.get("test")
        or probe_expected.get("probe_id")
        or ""
    )
    acceptance = str(
        expected.get("acceptance_criterion")
        or behavior_probe.get("acceptance_criterion")
        or probe_expected.get("acceptance_criterion")
        or probe_expected_text
        or ""
    )
    expected_observation = str(
        expected.get("expected_observation")
        or behavior_probe.get("expected_observation")
        or probe_expected.get("expected_observation")
        or probe_expected.get("observable")
        or probe_expected_text
        or ""
    )
    actions = expected.get("observable_actions") or behavior_probe.get("observable_actions") or probe_expected.get("observable_actions") or []
    return {
        "probe_id": probe_id,
        "acceptance_criterion": acceptance,
        "observable_actions": list(actions) if isinstance(actions, list) else [str(actions)],
        "expected_observation": expected_observation,
        "minimum_proof_tier": expected.get("minimum_proof_tier", probe_expected.get("minimum_proof_tier", 2)),
    }


def _probe_evidence_summary(behavior_probe: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe_id": str(behavior_probe.get("probe_id") or behavior_probe.get("test") or ""),
        "clicked": behavior_probe.get("clicked", actual.get("clicked")),
        "filled": behavior_probe.get("filled", actual.get("filled")),
        "canvas": behavior_probe.get("canvas", actual.get("canvas")),
        "before": _first_present(actual, behavior_probe, "before"),
        "after": _first_present(actual, behavior_probe, "after"),
        "actual_values": actual,
        "expected_values": behavior_probe.get("expected") if isinstance(behavior_probe.get("expected"), dict) else str(behavior_probe.get("expected") or ""),
        "reason_codes": list(behavior_probe.get("reason_codes") or []),
    }


def _artifact_family_for_probe(probe_id: Any, prompt: Any = "") -> str:
    text = f"{probe_id or ''} {prompt or ''}".lower()
    if "weather" in text or "forecast" in text:
        return "weather/forecast/tile"
    if "drawing" in text or "canvas" in text or "doodle" in text or "paint" in text or "sketch" in text:
        return "drawing/canvas/sketch"
    if "password" in text or "passphrase" in text or "phrase" in text or "strength" in text:
        return "password/passphrase strength"
    if "theme" in text or "palette" in text or "color" in text or "dusk" in text or "dawn" in text:
        return "theme/mode toggle"
    if "calculator" in text or "split" in text or "share" in text or "cost" in text or "bill" in text:
        return "calculator/splitter"
    return "static_ui_artifact"


def _observed_interaction_summary(probe_summary: dict[str, Any]) -> str:
    parts: list[str] = []
    if probe_summary.get("clicked") is not None:
        parts.append(f"clicked={probe_summary.get('clicked')}")
    if probe_summary.get("filled") is not None:
        parts.append(f"filled={probe_summary.get('filled')}")
    if probe_summary.get("canvas") is not None:
        parts.append(f"canvas={probe_summary.get('canvas')}")
    actual = probe_summary.get("actual_values") if isinstance(probe_summary.get("actual_values"), dict) else {}
    if "changed" in actual:
        parts.append(f"changed={actual.get('changed')}")
    return ", ".join(parts) if parts else "browser probe interaction recorded in observed values"


def _why_this_failed(primary_bucket: str, actual: dict[str, Any], reason: str) -> str:
    if primary_bucket == "weather_static_when_update_expected":
        return "The browser probe clicked the weather control, but visible city/temp/condition/forecast text did not change."
    if primary_bucket == "drawing_canvas_no_pixel_change":
        return "The browser probe performed pointer/mouse drawing, but canvas pixels did not change."
    if primary_bucket == "password_no_visible_strength_text_change":
        return "The browser probe entered weak and stronger values, but visible strength feedback did not change."
    if primary_bucket == "theme_no_computed_state_change":
        return "The browser probe activated the theme control, but computed color or class state did not change."
    if primary_bucket == "calculator_no_visible_result_update":
        return "The browser probe entered values, but no visible numeric result update was observed."
    if reason:
        return reason
    return f"Browser behavior probe failed with bucket {primary_bucket or 'unknown'} and observed values {actual}."


def _required_repair_for_bucket(primary_bucket: str, artifact_family: str) -> str:
    if primary_bucket == "weather_static_when_update_expected" or artifact_family == "weather/forecast/tile":
        return "Fix the selected preview file so the next click visibly changes forecast state by mutating city, temperature, condition, forecast, or status text."
    if primary_bucket == "drawing_canvas_no_pixel_change" or artifact_family == "drawing/canvas/sketch":
        return "Fix the selected preview file so pointer/mouse interaction visibly marks the canvas; keep canvas ids and script selectors consistent."
    if primary_bucket == "password_no_visible_strength_text_change" or artifact_family == "password/passphrase strength":
        return "Fix local input handling so weak and stronger phrase/password inputs visibly produce different strength feedback."
    if primary_bucket == "theme_no_computed_state_change" or artifact_family == "theme/mode toggle":
        return "Fix the local control so theme, palette, class, or computed color state visibly changes after interaction."
    if primary_bucket == "calculator_no_visible_result_update" or artifact_family == "calculator/splitter":
        return "Fix local input/calculation handling so entered numeric values visibly update a total, share, or result."
    return "Fix the selected preview file so the failed browser behavior probe observes visible state mutation."


def _allowed_relative_files(packet: dict[str, Any]) -> list[str]:
    workspace = str(packet.get("allowed_workspace") or "").replace("\\", "/").rstrip("/")
    allowed: list[str] = []
    for raw in [
        *list(packet.get("artifact_paths") or []),
        *list(packet.get("generated_files") or []),
        *list(packet.get("model_authored_targets") or []),
    ]:
        value = str(raw or "").replace("\\", "/")
        if workspace and (value == workspace or value.startswith(workspace + "/")):
            value = value[len(workspace) :].lstrip("/")
        if value and value not in allowed:
            allowed.append(value)
    return allowed


def _first_present(primary: dict[str, Any], secondary: dict[str, Any], key: str) -> Any:
    if key in primary:
        return primary[key]
    return secondary.get(key)


def _path_within_workspace(path: str, allowed_workspace: str) -> bool:
    normalized_path = path.replace("\\", "/").rstrip("/")
    normalized_workspace = allowed_workspace.replace("\\", "/").rstrip("/")
    if not normalized_path or not normalized_workspace:
        return False
    return normalized_path == normalized_workspace or normalized_path.startswith(normalized_workspace + "/")


def _reason_codes_from_contract(contract: dict[str, Any]) -> list[str]:
    expected = _expected_behavior(contract)
    probe_id = expected.get("probe_id")
    return [f"behavior_probe_failed:{probe_id}"] if probe_id else []


def _reason_codes_from_evidence(evidence: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    probe = evidence.get("behavior_probe") if isinstance(evidence.get("behavior_probe"), dict) else {}
    codes.extend(str(code) for code in probe.get("reason_codes") or [])
    codes.extend(str(code) for code in evidence.get("usability_reason_codes") or [])
    if evidence.get("source_proxy_score_status") == "GO":
        codes.append("route_go_not_behavior_pass")
    return codes


def _reason_code_from_reason(reason: str) -> str:
    lowered = reason.lower()
    if "computed colors" in lowered or "colors did not change" in lowered:
        return "computed_visual_state_unchanged"
    if "static" in lowered and "no controls" in lowered:
        return "static_content_no_controls"
    if "no artifact" in lowered or "no preview" in lowered:
        return "artifact_or_preview_missing"
    if "did not equal" in lowered or "instead" in lowered:
        return "observed_value_mismatch"
    if not lowered:
        return "verifier_failure"
    return "behavior_verifier_failed"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
