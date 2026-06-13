from __future__ import annotations

import difflib
import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from source_proxy.decision.artifact_behavior_contract import (
    build_artifact_behavior_contract,
    summarize_behavior_contract_for_prompt,
)
from source_proxy.decision.artifact_final_verdict import normalize_artifact_final_verdict
from source_proxy.decision.artifact_preview_resolution import resolve_artifact_preview_path
from source_proxy.decision.expectation_scoring import build_expectation_score
from source_proxy.decision.model_lanes import lane_selection_observability
from source_proxy.decision.task_spec_intake import (
    build_task_spec_intake,
    intake_as_legacy_task_spec,
)
from source_proxy.decision.tool_action_executor import ToolActionWorkspaceContract
from source_proxy.decision.tool_action_loop import (
    BoundedAgentLoopRequest,
    run_bounded_agent_loop,
)


DEFAULT_HUMAN_MESSY_HOMEPAGE_PROMPT = "init a repo and make homepage for agent lab expermients"
DEFAULT_ALLOWED_FILES = ("index.html", "styles.css")
DEFAULT_MODEL_ID = "qwen2.5-coder:7b"
DEFAULT_OLLAMA_API = "http://127.0.0.1:11434"
HumanMessyHomepageMode = Literal["product", "pure"]


@dataclass(frozen=True)
class HumanMessyHomepagePaths:
    workspace: Path
    receipt_path: Path
    score_path: Path
    transcript_path: Path
    diff_path: Path


def run_human_messy_homepage(
    *,
    prompt: str,
    workspace: Path,
    receipt_path: Path,
    score_path: Path,
    transcript_path: Path,
    diff_path: Path,
    preview_url: str = "",
    model_id: str = DEFAULT_MODEL_ID,
    mode: HumanMessyHomepageMode = "product",
    adapter_source: str = "ollama_generate/tool_action_runtime_v1",
    model_call: Callable[[dict[str, Any]], str] | None = None,
    ollama_api: str = DEFAULT_OLLAMA_API,
) -> dict[str, Any]:
    if mode not in {"product", "pure"}:
        raise ValueError(f"Unsupported human messy homepage mode: {mode}")
    workspace.mkdir(parents=True, exist_ok=True)
    before = _snapshot(workspace)
    task_spec_intake = build_task_spec_intake(
        prompt,
        workspace_root=workspace,
        wants_implementation=True,
        model_lane="coder_agent",
        allow_messy_homepage_helper=(mode == "product"),
    )
    legacy_task_spec = (
        intake_as_legacy_task_spec(task_spec_intake)
        if mode == "product"
        else _pure_mode_task_spec(prompt)
    )
    allowed_files = tuple(task_spec_intake.allowed_files) if mode == "product" else ()
    contract = ToolActionWorkspaceContract(
        workspace_root=workspace,
        allowed_files=allowed_files,
        allowed_file_extensions=tuple(task_spec_intake.allowed_extensions) if mode == "product" else (),
        forbidden_files=tuple(task_spec_intake.forbidden_files),
        protected_paths=tuple(task_spec_intake.protected_paths),
        approval_level="disposable_workspace",
        model_may_choose_paths=(
            mode == "pure"
            or (
                mode == "product"
                and task_spec_intake.workspace_mode == "disposable_workspace"
                and task_spec_intake.target_source == "model_authored_required"
            )
        ),
        max_file_count=task_spec_intake.max_file_count if mode == "product" else 8,
        network_allowed=False,
        run_timeout_seconds=10,
    )
    context_packet = _context_packet_for_mode(prompt, mode, contract, task_spec_intake.to_dict())
    request = BoundedAgentLoopRequest(
        task_spec=legacy_task_spec,
        context_packet=context_packet,
        workspace_contract=contract,
        model_id=model_id,
        adapter_source=adapter_source,
        source_message_id="human-messy-homepage",
        recommended_checks=(),
        run_recommended_checks=False,
        max_format_retries=1,
        max_verification_repairs=1 if mode == "product" else 0,
    )

    def call_model(packet: dict[str, Any]) -> str:
        if model_call is not None:
            return model_call(packet)
        return _ollama_generate(
            _render_model_prompt(packet),
            model_id=model_id,
            ollama_api=ollama_api,
        )

    started = time.monotonic()
    result = run_bounded_agent_loop(request, call_model, receipt_path=receipt_path).to_dict()
    elapsed = round(time.monotonic() - started, 3)
    receipt = result["receipt"]
    raw_transcripts = list(receipt.get("raw_model_transcripts") or [])
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text(
        "\n\n--- MODEL CALL ---\n\n".join(raw_transcripts),
        encoding="utf-8",
        errors="replace",
    )

    after = _snapshot(workspace)
    diff = _diff_snapshots(before, after)
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    diff_path.write_text(diff, encoding="utf-8", errors="replace")

    score = score_human_messy_homepage_result(
        prompt=prompt,
        workspace=workspace,
        receipt=receipt,
        model_id=model_id,
        mode=mode,
        adapter_source=adapter_source,
        preview_url=preview_url,
        elapsed_seconds=elapsed,
        raw_transcript_path=transcript_path,
        receipt_path=receipt_path,
    )
    score["expectation_score"] = build_expectation_score(score=score, receipt=receipt)
    score_path.parent.mkdir(parents=True, exist_ok=True)
    score_path.write_text(json.dumps(score, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return score


def _pure_mode_task_spec(prompt: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task_type": "create_or_edit_in_disposable_workspace",
        "target": "",
        "allowed_files": [],
        "forbidden_files": _default_forbidden_files(),
        "literal_requirements": [],
        "verification": ["git diff --check"],
        "risk_tier": "medium",
        "source": "human_messy_homepage_pure_mode",
        "blockers": [],
        "clarification_state": "not_needed",
        "clarification_prompt": "",
        "workspace_mode": "disposable_workspace",
        "approval_level": "disposable_workspace",
        "intent": "create_or_edit",
        "context_sources": ["user_prompt"],
        "user_prompt": prompt,
    }


def _context_packet_for_mode(
    prompt: str,
    mode: HumanMessyHomepageMode,
    contract: ToolActionWorkspaceContract,
    intake: dict[str, Any],
) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "user_prompt": prompt,
        "mode": mode,
        "route_type": "pure_diagnostic" if mode == "pure" else "product",
        "workspace_mode": "disposable_workspace",
        "forbidden_real_repo_mutation": True,
        "network_allowed": contract.network_allowed,
        "max_file_count": contract.max_file_count,
        "model_may_choose_paths": contract.model_may_choose_paths,
        "model_requirements": [
            "explicit model-authored target path",
            "explicit model-authored file content",
            "supported Source Proxy action JSON or path-bound file block",
        ],
        "benchmark_eligible": mode == "pure",
        "benchmark_eligibility_reason": "pure_diagnostic_no_proxy_scope_help"
        if mode == "pure"
        else "product_route_uses_proxy_orchestration",
    }
    if mode == "product":
        behavior_contract = build_artifact_behavior_contract(
            prompt=prompt,
            artifact_class=str(intake.get("artifact_class") or ""),
            task_shape=str(intake.get("task_shape") or ""),
        )
        packet["task_shape"] = intake.get("task_shape") or ""
        packet["task_shape_source"] = intake.get("task_shape_source") or ""
        packet["artifact_class"] = intake.get("artifact_class") or ""
        packet["behavior_contract"] = behavior_contract
        packet["behavior_contract_summary"] = summarize_behavior_contract_for_prompt(behavior_contract)
        packet["allowed_extensions"] = list(contract.allowed_file_extensions)
        packet["allowed_files"] = list(contract.allowed_files)
        packet["protected_paths"] = list(contract.protected_paths)
        packet["forbidden_files"] = list(contract.forbidden_files)
        packet["target_source"] = intake.get("target_source") or ""
        packet["workspace_decision_source"] = intake.get("workspace_decision_source") or ""
        packet["allowed_scope_source"] = intake.get("allowed_scope_source") or ""
        packet["proxy_exact_target_suggested"] = ""
        packet["proxy_artifact_class_suggested"] = bool(intake.get("artifact_class"))
        packet["clarification_or_block_reason"] = intake.get("clarification_prompt") or ""
    return packet


def score_human_messy_homepage_result(
    *,
    prompt: str,
    workspace: Path,
    receipt: dict[str, Any],
    model_id: str,
    mode: HumanMessyHomepageMode = "product",
    adapter_source: str = "generic",
    preview_url: str,
    elapsed_seconds: float,
    raw_transcript_path: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    diagnostics = dict(receipt.get("diagnostics_packet") or {})
    raw_transcripts = list(receipt.get("raw_model_transcripts") or [])
    parsed_actions = list(receipt.get("parsed_actions") or [])
    files_touched = sorted(set(diagnostics.get("files_touched") or []))
    files_changed = _changed_files_from_receipt(receipt)
    workspace_files = _workspace_files(workspace)
    model_write_targets = _model_write_targets(parsed_actions)
    system_preselected_target = _system_preselected_target(receipt)
    product_helper_used = _product_helper_used(receipt)
    transparent_default_target_used = _transparent_default_target_used(receipt)
    pure_mode = mode == "pure"
    proxy_orchestration_used = _proxy_orchestration_used(receipt)
    diagnostics_task_shape = str(diagnostics.get("task_shape") or "")
    artifact_class = str(diagnostics.get("proxy_artifact_class_suggested") or "")
    behavior_contract = dict(diagnostics.get("behavior_contract") or {})
    allowed_files_source = str(diagnostics.get("allowed_scope_source") or ("product_helper" if product_helper_used else "none"))
    target_path_source = "system_preselected" if system_preselected_target else "model_action"
    path_selection_mode = "model_chosen" if not system_preselected_target else "proxy_exact_target"
    model_authored_targets = list(diagnostics.get("model_authored_targets") or model_write_targets)
    model_chose_target = bool(model_authored_targets) and not system_preselected_target
    openable_homepage_paths = _openable_homepage_paths(workspace, files_changed)
    preview_resolution = resolve_artifact_preview_path(
        workspace=workspace,
        prompt=prompt,
        score={"openable_homepage_paths": openable_homepage_paths},
    ).to_dict()
    openable_homepage = bool(openable_homepage_paths)
    content_byte_match_by_target = _content_byte_match_by_target(workspace, files_changed, parsed_actions)
    file_equals_model_action_content = _file_equals_model_action_content(
        workspace,
        files_changed,
        parsed_actions,
    )
    backend_created_content = bool(workspace_files) and not file_equals_model_action_content
    fallback_used = False
    deterministic_scaffold_used = False
    dummy_fixture_used = False
    real_app_touched = _real_app_touched(files_touched)
    actions_seen = len(parsed_actions)
    blocked_reasons = list(diagnostics.get("blocked_reasons") or [])
    reason_codes = _reason_codes(receipt)
    final_state = str(receipt.get("final_state") or "")
    product_artifact_ok, artifact_reason_codes = _product_artifact_ok(
        artifact_class=artifact_class,
        final_state=final_state,
        actions_seen=actions_seen,
        files_changed=files_changed,
        model_authored_targets=model_authored_targets,
        content_byte_match_by_target=content_byte_match_by_target,
        openable_homepage_paths=openable_homepage_paths,
        workspace=workspace,
    )
    common_safety_ok = (
        not real_app_touched
        and not fallback_used
        and not deterministic_scaffold_used
        and not dummy_fixture_used
        and not backend_created_content
        and file_equals_model_action_content
    )
    product_go = (
        not pure_mode
        and product_artifact_ok
        and common_safety_ok
    )
    pure_common_go = (
        final_state in {"completed", "partial"}
        and actions_seen >= 1
        and bool(files_changed)
        and openable_homepage
        and common_safety_ok
    )
    expected_blocked = (
        not pure_mode
        and final_state == "blocked"
        and not files_changed
        and not files_touched
        and bool({"target_not_allowed", "protected_path", "path_escape"}.intersection(reason_codes))
    )
    benchmark_eligible = bool(
        pure_mode
        and pure_common_go
        and not product_helper_used
        and not transparent_default_target_used
        and not system_preselected_target
        and model_chose_target
    )
    if expected_blocked:
        status = "EXPECTED-BLOCKED"
        verification_outcome = "expected_blocked"
        reason_codes.append("expected_blocked_result")
    elif pure_mode:
        status = "GO" if benchmark_eligible else "NO-GO"
        verification_outcome = "pure_benchmark_go" if benchmark_eligible else "pure_benchmark_no_go"
    else:
        status = "GO" if product_go else "NO-GO"
        verification_outcome = "product_artifact_go" if product_go else "product_artifact_no_go"
    if status == "NO-GO":
        if actions_seen < 1:
            reason_codes.append("no_model_actions_or_path_bound_blocks")
        if not files_changed:
            reason_codes.append("no_files_changed")
        if artifact_class in {"", "html_static_page"} and not openable_homepage:
            reason_codes.append("openable_homepage_missing")
        reason_codes.extend(artifact_reason_codes)
        if backend_created_content:
            reason_codes.append("backend_created_content_detected")
        if pure_mode and product_helper_used:
            reason_codes.append("product_helper_used_in_pure_mode")
        if pure_mode and transparent_default_target_used:
            reason_codes.append("transparent_default_target_used_in_pure_mode")
        if pure_mode and system_preselected_target:
            reason_codes.append("system_preselected_target_in_pure_mode")
        if pure_mode and not model_chose_target:
            reason_codes.append("model_target_not_proven")

    behavior_required = bool(behavior_contract.get("behavior_required")) or (
        (not pure_mode) and artifact_class in {"", "html_static_page", "static_ui_artifact"}
    )
    lane_observability = lane_selection_observability(
        task_type="disposable_artifact" if not pure_mode else "pure_diagnostic",
        evidence_refs=[str(receipt_path), str(raw_transcript_path)],
    )
    canonical_final_verdict = normalize_artifact_final_verdict(
        route_status=status,
        artifact_ready=product_artifact_ok if not pure_mode else pure_common_go,
        behavior_required=behavior_required,
        behavior_verdict=None,
        reason_codes=reason_codes,
    )

    return {
        "status": status,
        "route_status": status,
        "canonical_final_verdict": canonical_final_verdict["label"],
        "product_pass": canonical_final_verdict["product_pass"],
        "behavior_required_for_final_pass": behavior_required,
        "behavior_contract": behavior_contract,
        "behavior_verdict": canonical_final_verdict["behavior_verdict"],
        "final_verdict_reason_codes": canonical_final_verdict["reason_codes"],
        "model_lane_observability": lane_observability,
        "selected_coder_lane": lane_observability["selected_coder_lane"],
        "sidecar_lanes_considered": lane_observability["sidecar_lanes_considered"],
        "verifier_lane_required": lane_observability["verifier_lane_required"],
        "lane_privacy_class": lane_observability["lane_privacy_class"],
        "lane_cost_class": lane_observability["lane_cost_class"],
        "lane_approval_required": lane_observability["lane_approval_required"],
        "lane_selection_reason_codes": lane_observability["lane_selection_reason_codes"],
        "lane_evidence_refs": lane_observability["lane_evidence_refs"],
        "mode": mode,
        "path_selection_mode": path_selection_mode,
        "target_path_source": target_path_source,
        "allowed_files_source": allowed_files_source,
        "product_helper_used": product_helper_used,
        "proxy_orchestration_used": proxy_orchestration_used,
        "route_type": diagnostics.get("route_type") or ("pure_diagnostic" if pure_mode else "product"),
        "task_shape": diagnostics_task_shape,
        "task_shape_source": diagnostics.get("task_shape_source") or "",
        "artifact_class": artifact_class,
        "artifact_score_kind": verification_outcome,
        "artifact_specific_ok": product_artifact_ok if not pure_mode else pure_common_go,
        "expected_blocked": expected_blocked,
        "allowed_scope_source": diagnostics.get("allowed_scope_source") or "",
        "workspace_decision_source": diagnostics.get("workspace_decision_source") or "",
        "proxy_exact_target_suggested": diagnostics.get("proxy_exact_target_suggested") or "",
        "model_authored_targets": model_authored_targets,
        "model_authored_content_hashes": _model_authored_content_hashes(parsed_actions),
        "content_byte_match_by_target": content_byte_match_by_target,
        "benchmark_eligibility_reason": diagnostics.get("benchmark_eligibility_reason") or "",
        "pure_mode": pure_mode,
        "transparent_default_target_used": transparent_default_target_used,
        "model_chose_target": model_chose_target,
        "system_preselected_target": system_preselected_target,
        "benchmark_eligible": benchmark_eligible,
        "final_state": final_state,
        "prompt": prompt,
        "model_id": model_id,
        "adapter_source": adapter_source,
        "raw_transcript_path": str(raw_transcript_path),
        "raw_model_transcript_count": len(raw_transcripts),
        "parsed_action_count": len(parsed_actions),
        "actions_seen": actions_seen,
        "files_changed": files_changed,
        "files_touched": files_touched,
        "workspace_files": workspace_files,
        "openable_homepage": openable_homepage,
        "openable_homepage_paths": openable_homepage_paths,
        "selected_preview_path": preview_resolution["selected_path"],
        "preview_selection_reason": preview_resolution["selection_reason"],
        "preview_resolution_status": preview_resolution["status"],
        "preview_resolution_reason_codes": preview_resolution["reason_codes"],
        "preview_candidate_paths": preview_resolution["candidate_paths"],
        "preview_url": preview_url,
        "real_app_touched": real_app_touched,
        "fallback_used": fallback_used,
        "deterministic_scaffold_used": deterministic_scaffold_used,
        "dummy_fixture_used": dummy_fixture_used,
        "backend_created_content": backend_created_content,
        "file_equals_model_action_content": file_equals_model_action_content,
        "blocked_reasons": blocked_reasons,
        "reason_codes": sorted(set(reason_codes)),
        "receipt_path": str(receipt_path),
        "workspace_path": str(workspace),
        "elapsed_seconds": elapsed_seconds,
    }


def _render_model_prompt(packet: dict[str, Any]) -> str:
    context = packet["context_packet"]
    mode = str(context.get("mode") or "product")
    observations = packet.get("observations") or []
    retry_note = ""
    if observations:
        repair_contract = packet.get("bounded_repair_contract") or {}
        repair_instructions = ""
        if isinstance(repair_contract, dict) and repair_contract.get("instructions"):
            repair_instructions = f"\n{repair_contract['instructions']}\n"
        retry_note = (
            "\nPrevious output could not be executed. Return only one supported action now. "
            f"Observations: {json.dumps(observations, ensure_ascii=False)}\n"
            f"{repair_instructions}"
        )
    if mode == "pure":
        return (
            "You are Source Proxy's local coding model. The user gave a messy human prompt.\n"
            "Work only inside the disposable workspace. You choose all safe relative file paths and all file contents.\n"
            "Do not touch the real app, do not run shell commands, do not use network, do not explain steps.\n"
            "Return model-authored Source Proxy file actions only, with no markdown fences and no extra prose.\n"
            "Use this JSON shape for each file you create or replace:\n"
            '{"action_type":"WriteFile","target":"RELATIVE_PATH_CHOSEN_BY_MODEL","arguments":{"content":"FULL FILE BYTES HERE"},"reason":"Why this file is needed."}\n'
            "Targets must be relative paths inside the disposable workspace, must not escape with .., and must not be secret/protected paths.\n"
            f"Maximum file count: {context.get('max_file_count', 8)}.\n"
            f"User prompt: {context['user_prompt']}\n"
            f"{retry_note}"
        )
    return (
        "You are Source Proxy's local coding model. The user gave a messy human prompt.\n"
        "Create the requested disposable artifact only inside the disposable workspace.\n"
        "Do not touch the real app, do not run shell commands, do not use network, do not explain steps.\n"
        "Return model-authored Source Proxy file actions only, with no markdown fences and no extra prose.\n"
        "Use this JSON shape for each file you create or replace:\n"
        '{"action_type":"WriteFile","target":"RELATIVE_PATH_AUTHORED_BY_MODEL","arguments":{"content":"FULL FILE BYTES HERE"},"reason":"Why this file is needed."}\n'
        "The target path and file content must both come from you, not from Source Proxy.\n"
        f"Task shape: {context.get('task_shape') or 'disposable artifact'}.\n"
        f"Artifact class: {context.get('artifact_class') or 'unspecified'}.\n"
        f"Allowed extensions: {json.dumps(context.get('allowed_extensions') or [])}.\n"
        f"Exact allowed files, if any: {json.dumps(context.get('allowed_files') or [])}.\n"
        f"Maximum file count: {context.get('max_file_count', 1)}.\n"
        f"{context.get('behavior_contract_summary') or ''}\n"
        f"{_artifact_family_implementation_checklist(context)}"
        "For interactive artifacts, include visible controls and visible state/output that changes after the required user action. "
        "If you create multiple files, ensure the HTML links its CSS and JS using relative paths.\n"
        f"User prompt: {context['user_prompt']}\n"
        f"{retry_note}"
    )


def _default_forbidden_files() -> list[str]:
    return [".env", ".env.*", "*.pem", "*.key", "certificates/*"]


def _artifact_family_implementation_checklist(context: dict[str, Any]) -> str:
    contract = context.get("behavior_contract") if isinstance(context.get("behavior_contract"), dict) else {}
    targets = contract.get("probe_targets") if isinstance(contract.get("probe_targets"), list) else []
    probe_id = str((targets[0] if targets and isinstance(targets[0], dict) else {}).get("probe_id") or "")
    if probe_id == "timer-start-stop-freeze":
        return (
            "Implementation checklist: create visible time/count text; wire Start to a local setInterval or equivalent state loop; "
            "after a short wait the displayed value must differ; Stop freezes if present; Reset returns to the initial value if present.\n"
        )
    if probe_id == "music-player-control-state":
        return (
            "Implementation checklist: include visible player status or track text; play/pause must toggle visible label/status; "
            "next/skip must change visible track/state if present.\n"
        )
    if probe_id == "password-strength-feedback-change":
        return (
            "Implementation checklist: wire input events locally; weak and stronger password, phrase, or passphrase values must produce different visible strength text, class, color, or status.\n"
        )
    if probe_id == "drawing-surface-changes":
        return (
            "Implementation checklist: prefer a real canvas element; wire pointer/mouse down/move/up handlers; dragging on the canvas/surface must visibly draw marks or change pixels; keep canvas ids and script selectors consistent; do not clear marks on mouseup unless a separate clear control is used.\n"
        )
    if probe_id == "notes-create-edit-visible-note":
        return (
            "Implementation checklist: after add/save/edit, render the actual typed note text in a visible note/list/card area; a saved-status message alone is not enough.\n"
        )
    if probe_id == "theme-computed-color-change":
        return (
            "Implementation checklist: include a browser-viewable HTML entrypoint and local control for dark/light, dusk/dawn, sunrise/sunset, palette, or color mood changes; interaction must change computed background/text color or body class.\n"
        )
    if probe_id == "weather-card-fields":
        return (
            "Implementation checklist: render visible city, temperature, condition, forecast, or status text; if a local demo control is present, clicking it must mutate visible weather/forecast DOM text.\n"
        )
    return ""


def _ollama_generate(prompt: str, *, model_id: str, ollama_api: str) -> str:
    payload = {
        "model": model_id,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": 0, "num_predict": 2200},
    }
    request = urllib.request.Request(
        f"{ollama_api.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        parsed = json.loads(response.read().decode("utf-8", errors="replace"))
    return str(parsed.get("response") or "")


def _snapshot(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.relative_to(root).parts:
            files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    return files


def _diff_snapshots(before: dict[str, str], after: dict[str, str]) -> str:
    chunks: list[str] = []
    for name in sorted(set(before) | set(after)):
        if before.get(name) == after.get(name):
            continue
        chunks.extend(
            difflib.unified_diff(
                before.get(name, "").splitlines(keepends=True),
                after.get(name, "").splitlines(keepends=True),
                fromfile=f"a/{name}",
                tofile=f"b/{name}",
            )
        )
    return "".join(chunks)


def _changed_files_from_receipt(receipt: dict[str, Any]) -> list[str]:
    changed: set[str] = set()
    for execution in receipt.get("executions") or []:
        result = execution.get("result") or {}
        if result.get("status") == "completed":
            changed.update(str(path) for path in result.get("files_touched") or [])
    return sorted(changed)


def _workspace_files(workspace: Path) -> list[str]:
    if not workspace.exists():
        return []
    return sorted(
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(workspace).parts
    )


def _openable_homepage_paths(workspace: Path, files_changed: list[str]) -> list[str]:
    openable: list[str] = []
    for repo_path in files_changed:
        path = workspace / repo_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if "<html" in text and "</html>" in text and "<body" in text:
            openable.append(repo_path)
    return sorted(openable)


def _product_artifact_ok(
    *,
    artifact_class: str,
    final_state: str,
    actions_seen: int,
    files_changed: list[str],
    model_authored_targets: list[str],
    content_byte_match_by_target: dict[str, bool],
    openable_homepage_paths: list[str],
    workspace: Path,
) -> tuple[bool, list[str]]:
    reason_codes: list[str] = []
    if final_state != "completed":
        reason_codes.append("final_state_not_completed")
    if actions_seen < 1:
        reason_codes.append("no_model_actions_or_path_bound_blocks")
    if not files_changed:
        reason_codes.append("no_files_changed")
    if not model_authored_targets:
        reason_codes.append("model_authored_target_missing")
    if not content_byte_match_by_target or not all(content_byte_match_by_target.values()):
        reason_codes.append("model_content_byte_match_missing")
    common_ok = not reason_codes

    if artifact_class in {"", "html_static_page", "static_ui_artifact"}:
        html_targets = [target for target in model_authored_targets if target.lower().endswith((".html", ".htm"))]
        if not html_targets:
            reason_codes.append("html_model_target_missing")
        if not openable_homepage_paths:
            reason_codes.append("openable_html_missing")
        return common_ok and bool(html_targets) and bool(openable_homepage_paths), reason_codes

    if artifact_class == "markdown_document":
        markdown_targets = [target for target in model_authored_targets if target.lower().endswith(".md")]
        changed_markdown = [path for path in files_changed if path in markdown_targets]
        non_empty = [path for path in changed_markdown if _workspace_file_non_empty(workspace, path)]
        if not markdown_targets:
            reason_codes.append("markdown_model_target_missing")
        if not changed_markdown:
            reason_codes.append("markdown_file_not_touched")
        if not non_empty:
            reason_codes.append("markdown_content_empty")
        return common_ok and bool(markdown_targets) and bool(changed_markdown) and bool(non_empty), reason_codes

    if artifact_class == "json_example":
        json_targets = [target for target in model_authored_targets if target.lower().endswith(".json")]
        changed_json = [path for path in files_changed if path in json_targets]
        valid_json = [path for path in changed_json if _workspace_file_is_json(workspace, path)]
        if not json_targets:
            reason_codes.append("json_model_target_missing")
        if not changed_json:
            reason_codes.append("json_file_not_touched")
        if not valid_json:
            reason_codes.append("json_content_invalid")
        return common_ok and bool(json_targets) and bool(changed_json) and bool(valid_json), reason_codes

    non_empty = [path for path in files_changed if _workspace_file_non_empty(workspace, path)]
    if not non_empty:
        reason_codes.append("artifact_content_empty")
    return common_ok and bool(non_empty), reason_codes


def _workspace_file_non_empty(workspace: Path, repo_path: str) -> bool:
    path = workspace / repo_path
    return path.is_file() and bool(path.read_text(encoding="utf-8", errors="replace").strip())


def _workspace_file_is_json(workspace: Path, repo_path: str) -> bool:
    path = workspace / repo_path
    if not path.is_file():
        return False
    try:
        json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return False
    return True


def _file_equals_model_action_content(
    workspace: Path,
    files_changed: list[str],
    parsed_actions: list[dict[str, Any]],
) -> bool:
    if not files_changed:
        return False
    model_content_by_target: dict[str, str] = {}
    for action in parsed_actions:
        if action.get("action_type") != "WriteFile":
            continue
        arguments = action.get("arguments") or {}
        if isinstance(arguments, dict) and isinstance(arguments.get("content"), str):
            model_content_by_target[str(action.get("target") or "")] = arguments["content"]
    for repo_path in files_changed:
        path = workspace / repo_path
        if not path.is_file():
            return False
        if model_content_by_target.get(repo_path) != path.read_text(encoding="utf-8", errors="replace"):
            return False
    return True


def _model_write_targets(parsed_actions: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(action.get("target") or "")
            for action in parsed_actions
            if action.get("action_type") == "WriteFile" and str(action.get("target") or "")
        }
    )


def _product_helper_used(receipt: dict[str, Any]) -> bool:
    for call in receipt.get("model_calls") or []:
        packet = call.get("packet") or {}
        context = packet.get("context_packet") or {}
        workspace_contract = packet.get("workspace_contract") or {}
        if context.get("mode") == "product":
            return True
        if context.get("transparent_default_target") or context.get("allowed_files"):
            return True
        if workspace_contract.get("allowed_files"):
            allowed = list(workspace_contract.get("allowed_files") or [])
            if allowed == list(DEFAULT_ALLOWED_FILES):
                return True
    return False


def _proxy_orchestration_used(receipt: dict[str, Any]) -> bool:
    for call in receipt.get("model_calls") or []:
        context = ((call.get("packet") or {}).get("context_packet") or {})
        if context.get("route_type") == "product":
            return True
        if context.get("task_shape") or context.get("artifact_class") or context.get("allowed_extensions"):
            return True
    return False


def _transparent_default_target_used(receipt: dict[str, Any]) -> bool:
    return any(
        bool(((call.get("packet") or {}).get("context_packet") or {}).get("transparent_default_target"))
        for call in receipt.get("model_calls") or []
    )


def _system_preselected_target(receipt: dict[str, Any]) -> bool:
    for call in receipt.get("model_calls") or []:
        packet = call.get("packet") or {}
        task_spec = packet.get("task_spec") or {}
        context = packet.get("context_packet") or {}
        target = str(task_spec.get("target") or "")
        if target:
            return True
        if context.get("transparent_default_target"):
            return True
    return False


def _model_authored_content_hashes(parsed_actions: list[dict[str, Any]]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for action in parsed_actions:
        if action.get("action_type") != "WriteFile":
            continue
        arguments = action.get("arguments") or {}
        content = arguments.get("content") if isinstance(arguments, dict) else None
        target = str(action.get("target") or "")
        if isinstance(content, str) and target:
            hashes[target] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return hashes


def _content_byte_match_by_target(
    workspace: Path,
    files_changed: list[str],
    parsed_actions: list[dict[str, Any]],
) -> dict[str, bool]:
    model_content_by_target: dict[str, str] = {}
    for action in parsed_actions:
        if action.get("action_type") != "WriteFile":
            continue
        arguments = action.get("arguments") or {}
        if isinstance(arguments, dict) and isinstance(arguments.get("content"), str):
            model_content_by_target[str(action.get("target") or "")] = arguments["content"]
    matches: dict[str, bool] = {}
    for repo_path in files_changed:
        path = workspace / repo_path
        matches[repo_path] = path.is_file() and model_content_by_target.get(repo_path) == path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    return matches


def _real_app_touched(files_touched: list[str]) -> bool:
    return any(
        path.startswith(("src/", "app/", "pages/", "source_proxy/", "scripts/"))
        for path in files_touched
    )


def _reason_codes(receipt: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    for result in receipt.get("parse_results") or []:
        code = str(result.get("error_code") or "")
        if code:
            codes.append(code)
    for execution in receipt.get("executions") or []:
        code = str((execution.get("result") or {}).get("error_code") or "")
        if code:
            codes.append(code)
    return codes
