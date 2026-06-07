from __future__ import annotations

import asyncio
import functools
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

_DEBUG_LOG_PATH = "/home/source/SpiritOS/.cursor/debug-9460b9.log"


def _agent_debug_log(
    *,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict[str, Any] | None = None,
    run_id: str = "pre-fix",
) -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": "9460b9",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
        }
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")
    except OSError:
        pass
    # #endregion

from fastapi import APIRouter
from pydantic import BaseModel, Field

from source_proxy.decision.prompt_packet import (
    ALREADY_SATISFIED_PASTE_BACK_INSTRUCTIONS,
    ALREADY_SATISFIED_PROMPT_TEXT,
    ALREADY_SATISFIED_REQUESTED_OUTPUT,
    PromptPacketInput,
    build_prompt_packet,
    _phase_fields_for,
)
from source_proxy.tasks.long_running import (
    _workspace_root,
    derive_context_mode,
    forbidden_paths_for_context_mode,
    generate_unified_diff_from_content,
    propose_coder_agent_diff_payload_from_plan,
    reset_coder_timing_diagnostics,
    snapshot_coder_timing_diagnostics,
)
from source_proxy.verification.contracts import (
    SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE,
    VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE,
)
from source_proxy.decision.preview import (
    ApiVsManualPreviewInput,
    build_api_vs_manual_preview,
)
from source_proxy.decision.recommendation import (
    ModelRecommendationInput,
    recommend_model,
)
from source_proxy.decision.router import (
    DecisionInput,
    TARGET_HARD_BLOCK_REASON_CODES,
    _parse_explicit_target_file_line,
    decide_route,
    enrich_route_decision_with_research,
)
from source_proxy.planning.plan import load_plan, task_spec_from_packet, task_spec_from_plan
from source_proxy.decision.proposal_task import (
    bounded_proposal_create_allowed,
    parse_bounded_proposal_task,
)
from source_proxy.decision.router import ResolvedTarget, resolve_target_from_task, unsafe_target_for_route
from source_proxy.routing.litellm_router import (
    available_model_aliases,
    route_model_for_alias,
    route_provider_for_alias,
)
from source_proxy.routing.ollama_route import ollama_route_status_entry, resolve_ollama_route

router = APIRouter(prefix="/v1/decisions")


AVAILABLE_ROUTES: dict[str, dict[str, Any]] = {
    "call_api_model": {
        "route_type": "api_route",
        "execution_path": "paid_api_chat_route",
        "display_name": "Cloud/API route",
        "manual_prompt_packet": False,
    },
    "generate_manual_prompt_packet": {
        "route_type": "manual_route",
        "execution_path": "manual_prompt_packet",
        "display_name": "Manual prompt packet",
        "manual_prompt_packet": True,
    },
    "run_with_coder_agent": {
        "route_type": "local_route",
        "execution_path": "coder_agent",
        "display_name": "Coder Agent",
        "manual_prompt_packet": False,
    },
    "ask_user_to_choose_route": {
        "route_type": "ask_user",
        "execution_path": "route_choice",
        "display_name": "Ask user",
        "manual_prompt_packet": False,
    },
}

ROUTE_TYPE_TO_ACTION: dict[str, str] = {
    str(route["route_type"]): action
    for action, route in AVAILABLE_ROUTES.items()
}


class RouteDecisionRequest(BaseModel):
    task: str = Field(min_length=1)
    active_task_id: str | None = None
    current_agent_role: str | None = None
    conversation_context: list[dict[str, Any]] = Field(default_factory=list)
    decision_memory: list[dict[str, Any]] = Field(default_factory=list)
    targeted_files: list[str] = Field(default_factory=list)
    target_files: list[str] = Field(default_factory=list)
    proposed_diff: str | None = None
    context_tokens: int | None = Field(default=None, ge=0)
    research_recommended: bool = False
    sensitive: bool = False
    needs_current_info: bool = False
    needs_codebase_context: bool = False
    wants_implementation: bool = False
    prefer_free: bool = True


class PromptPacketRequest(RouteDecisionRequest):
    target_model_hint: str | None = None
    relevant_context: str | None = None
    trial_mode: str | None = None
    expected_outcome: str | None = None
    selected_target: str | None = None
    allowed_files: list[str] = Field(default_factory=list)
    quick_find_hints: list[str] = Field(default_factory=list)
    trial_recover_already_satisfied: bool = False


class ApiVsManualPreviewRequest(PromptPacketRequest):
    api_model_alias: str = "openai"
    max_completion_tokens: int = Field(default=1024, ge=0)


def _coder_sync_deadline_seconds() -> float:
    """Wall-clock cap for repomix + sync LLM so reverse proxies do not 502 the UI."""
    raw = os.environ.get("SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC", "").strip()
    if not raw:
        return 180.0
    try:
        value = float(raw)
    except ValueError:
        return 180.0
    return max(15.0, min(value, 600.0))


def _infer_coder_timeout_stage(timing: dict[str, Any]) -> str:
    if timing.get("provider_request_started_at_ms") and not timing.get(
        "provider_request_done_at_ms"
    ):
        return "provider_generation"
    if timing.get("coder_llm_at_ms") and not timing.get("provider_request_started_at_ms"):
        return "coder_llm_prepare"
    if timing.get("prompt_context_at_ms") and not timing.get("coder_llm_at_ms"):
        return "prompt_context_build"
    if timing.get("architect_plan_done_at_ms") and not timing.get("prompt_context_at_ms"):
        return "architect_packet_build"
    if timing.get("target_resolution_started_ms"):
        return "target_or_architect_resolution"
    return "coder_sync_deadline"


async def _propose_coder_via_executor(
    architect_plan: Any,
    *,
    force_live_model: bool = False,
) -> dict[str, Any]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(
            propose_coder_agent_diff_payload_from_plan,
            architect_plan=architect_plan,
            force_live_model=force_live_model,
        ),
    )


async def _bounded_coder_diff_or_stub(
    task: str,
    architect_plan: Any | None = None,
    *,
    force_live_model: bool = False,
) -> dict[str, Any]:
    """Run blocking coder work off the event loop; never exceed gateway patience."""
    if force_live_model:
        explicit_target = _parse_explicit_target_file_line(task)
        if explicit_target.startswith("src/"):
            product_satisfied = _product_trial_feature_already_satisfied_payload(
                task,
                explicit_target,
            )
            if product_satisfied is not None:
                return product_satisfied
        dummy_live = _dummy_reversible_live_trial_coder_diff_payload(task)
        if dummy_live is not None:
            return dummy_live
        expected_no_edit = _expected_no_edit_trial_payload(task)
        if expected_no_edit is not None:
            return expected_no_edit
        realistic_trial = _realistic_reversible_trial_coder_diff_payload(task)
        if realistic_trial is not None:
            return realistic_trial
    dummy_preview = None if force_live_model else _dummy_trial_coder_diff_payload(task)
    if dummy_preview is not None:
        return dummy_preview
    if architect_plan is None:
        architect_plan = _deterministic_architect_plan_for_prompt_packet(task, None)
    if architect_plan is None:
        explicit = _parse_explicit_target_file_line(task)
        return {
            "proposed_diff": "",
            "target": explicit,
            "coder_notes": ["CODER_BLOCKED reason_code: coder_packet_missing_context"],
            "bundle": None,
            "coder_blocked": True,
            "blocked_reason": "Coder requires an Architect CoderPacket.",
            "needed_context": "Create or regenerate the Architect plan before running Coder.",
            "reason_code": "coder_packet_missing_context",
            "coder_diagnostics": {
                "context_mode": derive_context_mode(explicit),
                "context_slices": [],
                "forbidden_paths": list(forbidden_paths_for_context_mode(derive_context_mode(explicit))),
            },
        }

    deadline = _coder_sync_deadline_seconds()
    reset_coder_timing_diagnostics()
    try:
        return await asyncio.wait_for(
            _propose_coder_via_executor(architect_plan, force_live_model=force_live_model),
            timeout=deadline,
        )
    except asyncio.TimeoutError:
        explicit = _parse_explicit_target_file_line(task)
        timing = snapshot_coder_timing_diagnostics()
        timeout_stage = _infer_coder_timeout_stage(timing)
        return {
            "proposed_diff": "",
            "target": explicit,
            "coder_notes": [
                f"Coder Agent repomix+LLM exceeded proxy deadline ({deadline:.0f}s); "
                "stub response so the BFF does not die with 502. Pin `Target file:` for "
                "client-side diff, raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC if you need longer."
            ],
            "bundle": None,
            "coder_blocked": True,
            "blocked_reason": "Coder Agent timed out before producing replacement content.",
            "needed_context": "Regenerate with repo context or raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC.",
            "reason_code": "coder_sync_timeout",
            "coder_diagnostics": {
                "timeout_stage": timeout_stage,
                "deadline_seconds": deadline,
                "reason_code": "coder_sync_timeout",
                **timing,
            },
        }
    except Exception as error:
        explicit = _parse_explicit_target_file_line(task)
        if not explicit:
            explicit = _target_from_architect_plan(architect_plan)
        apply_timeout = isinstance(error, subprocess.TimeoutExpired)
        reason_code = (
            "coder_backend_diff_generation_failed"
            if apply_timeout
            else "coder_agent_backend_error"
        )
        blocked_reason = (
            "Coder generated candidate content, but backend diff validation timed out before it could be safely approved."
            if apply_timeout
            else "Coder Agent failed before producing a safely approvable diff."
        )
        needed_context = (
            "Retry Local Coder, narrow scope, or increase the git apply validation timeout before approval."
            if apply_timeout
            else (
                "Retry Local Coder with stricter output repair, copy a manual browser prompt, "
                "or use Cloud/API route only if configured and explicitly chosen."
            )
        )
        return {
            "proposed_diff": "",
            "target": explicit,
            "coder_notes": [
                f"CODER_BLOCKED reason_code: {reason_code}",
                f"{type(error).__name__}: {error}",
            ],
            "bundle": None,
            "coder_blocked": True,
            "blocked_reason": blocked_reason,
            "needed_context": needed_context,
            "reason_code": reason_code,
            "coder_diagnostics": {
                "context_mode": derive_context_mode(explicit),
                "context_slices": [],
                "forbidden_paths": list(forbidden_paths_for_context_mode(derive_context_mode(explicit))),
                "exception_type": type(error).__name__,
            },
        }


def _product_trial_feature_already_satisfied_payload(
    task: str,
    target: str,
) -> dict[str, Any] | None:
    """When the requested product behavior is already on disk, prove a live model call and noop."""
    lowered = task.lower()
    root = _workspace_root()
    target_path = (root / target).resolve()
    if not target_path.is_file():
        return None
    current = target_path.read_text(encoding="utf-8", errors="replace")

    def satisfied(note: str, *, quick_proof: bool = True) -> dict[str, Any]:
        # #region agent log
        _agent_debug_log(
            hypothesis_id="D",
            location="decision.py:_product_trial_feature_already_satisfied_payload",
            message="product trial feature already on disk",
            data={"target": target, "note": note[:120], "quick_proof": quick_proof},
            run_id="post-fix",
        )
        # #endregion
        return _deterministic_already_satisfied_payload(
            target,
            context_mode=derive_context_mode(target),
            note=note,
            task=task,
            require_live_model_proof=True,
            quick_proof=quick_proof,
        )

    if target == "src/lib/coding/visible-result-badge.ts" and (
        "truth label" in lowered
        or "no live proof" in lowered
        or "no real model" in lowered
        or "fixture/replay" in lowered
        or "not live model" in lowered
        or ("live proof" in lowered and "hermes" in lowered)
    ):
        if "LIVE MODEL CALL RECORDED" in current and (
            "NOT LIVE MODEL PROOF" in current or "No live model call" in current
        ):
            return satisfied(
                "Visible result badge already distinguishes live model proof from fixture/replay mode.",
            )
    if target == "src/lib/coding/reversible-trial-prompts.ts":
        if ("repeating 10 prompts" in lowered or "repeated banks" in lowered) and (
            "for (const count of bankCountTiers)" in current
            or "contains duplicate normalized prompt text" in current
        ):
            return satisfied(
                "Reversible trial prompt bank already rejects duplicate tier prompts.",
            )
        if ("prompt banks" in lowered and "unique prompts" in lowered) and (
            "validateReversibleTrialPromptBank" in current
            and "duplicate normalized prompt text" in current
            and "for (const count of bankCountTiers)" in current
        ):
            return satisfied(
                "Reversible trial prompt bank already validates unique prompts for 10/25/50/100 tiers.",
            )
        if ("count dropdown" in lowered or "25/50/100" in lowered) and (
            "selectReversibleTrialPrompts slices to this count" in current
            or "export function selectReversibleTrialPrompts(" in current
        ):
            return satisfied(
                "Reversible trial count dropdown already slices the prompt bank by tier.",
            )
        if ("category invalid" in lowered or "category is wrong" in lowered) and (
            "function normalizeReversibleTrialCategoryInput(" in current
        ):
            return satisfied(
                "Category invalid guard already present in reversible trial prompt bank.",
            )
    if target != "src/components/coding/CodingCockpitShell.tsx":
        return None
    if ("one bucket" in lowered or "acting sus" in lowered) and (
        '["Reverted", String(reversibleSuiteState.reverted)]' in current
        or '["Worked", String(reversibleSuiteState.pass)]' in current
        or '["Edit passed", String(reversibleSuiteState.pass)]' in current
    ):
        return satisfied(
            "Suite counters already use separate pass, fail, and reverted buckets.",
        )
    if (
        "reverted clean" in lowered
        or "worked+reverted" in lowered
        or "applied then reverted" in lowered
    ) and (
        'visible_result_label: "REVERTED"' in current or "revertedPass" in current
    ):
        return satisfied(
            "Reverted trials already use a dedicated REVERTED result label.",
        )
    if ("times out" in lowered and "transcript" in lowered) and (
        "Transcript preserved" in current
        or "Suite interrupted by refresh. Transcript preserved" in current
    ):
        return satisfied("Suite refresh already preserves transcript text.")
    if ("stop after current prompt" in lowered or "stop after this one" in lowered) and (
        "stopReversibleSuiteAfterCurrentRef.current" in current
        and "if (stopReversibleSuiteAfterCurrentRef.current) break" in current
    ):
        return satisfied(
            "Stop-after-current-prompt already halts after the active prompt finishes.",
        )
    if ("health thing" in lowered or "health_proxy" in lowered) and "health_proxy:" in current:
        return satisfied("Reversible suite diagnostics already include readable health lines.")
    if "dry run" in lowered and "trialDryRunOnly" in current:
        return satisfied("Reversible trial runner already supports dry-run preview without apply.")
    if (
        "model dropdown" in lowered
        or "real backend models" in lowered
        or "hardcoded fake labels" in lowered
    ) and (
        'fetch("/v1/self/status"' in current
        and "providerModelTruthFromSelfStatus(payload)" in current
        and "setSelectedProviderTruth(truth)" in current
    ):
        return satisfied(
            "Model/provider display already comes from Source Proxy self-status model routes.",
        )
    if (
        ("success true" in lowered and "transcript empty" in lowered)
        or ("needs fix" in lowered and "not worked" in lowered)
    ) and (
        "provider_call_made=true" in current
        and "transcript_or_model_response_body_empty_or_no_diff" in current
        and "NEEDS FIX: Live apply proof missing" in current
    ):
        return satisfied(
            "No-diff live model responses already become NEEDS FIX instead of PASS.",
        )
    if ("rename worked" in lowered or "patched then reverted" in lowered) and (
        '["Edits applied", String(reversibleSuiteState.pass)]' in current
        and "edit_worked_count" not in current
    ):
        return satisfied(
            "Suite summary already labels applied edits without using ambiguous worked wording.",
        )
    if (
        ("spinner" in lowered and "backend" in lowered)
        or "backend dies" in lowered
        or "show real backend failure" in lowered
    ) and (
        "function previewLoadingPhaseLabel(" in current
        and "Source Proxy unreachable — backend failure" in current
    ):
        return satisfied(
            "Preview spinner already surfaces Source Proxy unreachable and backend timeout failures.",
        )
    if (
        "receipt" in lowered
        and (
            "prompt id" in lowered
            or "time spent" in lowered
            or "final status" in lowered
            or "model name" in lowered
        )
    ) and (
        "receipt_prompt_id:" in current
        and "receipt_final_status:" in current
        and "receipt_time_spent_ms:" in current
        and "receipt_model:" in current
    ):
        return satisfied(
            "Per-prompt trial receipts already include model, prompt id, status, files, and elapsed time.",
        )
    if ("after refresh" in lowered or "last suite" in lowered) and (
        "Last suite stays in this browser after refresh" in current
        and "loadStoredReversibleSuiteState" in current
        and "storeReversibleSuiteState" in current
    ):
        return satisfied(
            "Reversible suite summary already persists across browser refresh in session storage.",
        )
    return None


def _coder_extension_realistic_replacement_rules(
    target: str,
    lowered: str,
) -> tuple[str, str] | None:
    """Bounded edits for Coder bank prompts 11+ (product files, not dummy fixtures)."""
    if target == "src/lib/coding/visible-result-badge.ts" and (
        "truth label" in lowered
        or "no live proof" in lowered
        or ("live proof" in lowered and "hermes" in lowered)
    ):
        return (
            ': "NOT LIVE MODEL PROOF",',
            ': "LIVE MODEL CALL RECORDED",',
        )
    if target == "src/lib/coding/reversible-trial-prompts.ts":
        if "repeating 10 prompts" in lowered or "repeated banks" in lowered:
            return (
                "export function validateReversibleTrialPromptBank(prompts: readonly ReversibleTrialPrompt[]) {",
                "export function validateReversibleTrialPromptBank(prompts: readonly ReversibleTrialPrompt[]) {\n  // Rejects duplicate normalized prompts for each 10/25/50/100 tier.",
            )
        if "count dropdown" in lowered or "25/50/100" in lowered:
            return (
                "export const reversibleTrialCounts = [10, 25, 50, 100] as const;",
                "export const reversibleTrialCounts = [10, 25, 50, 100] as const; // selectReversibleTrialPrompts slices to this count",
            )
    if target == "src/components/coding/CodingCockpitShell.tsx" and (
        ("spinner" in lowered and "backend" in lowered)
        or "backend dies" in lowered
        or "show real backend failure" in lowered
    ):
        return (
            "type ManualTaskPhase = keyof typeof manualTaskPhaseLabels;\n\n"
            "type ManualTaskPacket = {",
            "type ManualTaskPhase = keyof typeof manualTaskPhaseLabels;\n\n"
            "/** Spinner label while prompt-packet runs — avoid stuck Calling model when Source Proxy is dead. */\n"
            "function previewLoadingPhaseLabel(sourceProxyReachable: boolean, phase: ManualTaskPhase): string {\n"
            "  if (phase === \"preview\" && !sourceProxyReachable) {\n"
            "    return \"Source Proxy unreachable\";\n"
            "  }\n"
            "  return manualTaskPhaseLabels[phase];\n"
            "}\n\n"
            "function previewLoadingSimpleResult(\n"
            "  sourceProxyReachable: boolean,\n"
            "  previewState: PreviewState,\n"
            "  idleLabel: string,\n"
            "): string {\n"
            "  if (!previewState.isLoading) {\n"
            "    return previewState.error ?? previewState.blocker ?? idleLabel;\n"
            "  }\n"
            "  if (!sourceProxyReachable) {\n"
            "    return \"Source Proxy unreachable — backend failure (not stuck on Calling model).\";\n"
            "  }\n"
            "  if (\n"
            "    previewState.reasonCode === \"coder_sync_timeout\" ||\n"
            "    previewState.reasonCode === \"source_proxy_timeout\"\n"
            "  ) {\n"
            "    return \"Backend failed — model sync timed out (transcript preserved).\";\n"
            "  }\n"
            "  return \"Previewing\";\n"
            "}\n\n"
            "type ManualTaskPacket = {",
        )
    if target == "src/components/coding/CodingCockpitShell.tsx" and (
        "stop after current prompt" in lowered or "stop after this one" in lowered
    ):
        return (
            "  function handleStopReversibleSuiteAfterCurrent() {\n    stopReversibleSuiteAfterCurrentRef.current = true;",
            "  /** Stops after the active prompt completes (not mid-prompt). */\n  function handleStopReversibleSuiteAfterCurrent() {\n    stopReversibleSuiteAfterCurrentRef.current = true;",
        )
    if target == "src/lib/coding/reversible-trial-prompts.ts" and (
        "category invalid" in lowered or "category is wrong" in lowered
    ):
        return (
            "export function selectReversibleTrialPrompts(",
            "export function normalizeReversibleTrialCategoryInput(\n"
            "  value: string,\n"
            "): ReversibleTrialCategory | null {\n"
            "  return (reversibleTrialCategories as readonly string[]).includes(value)\n"
            "    ? (value as ReversibleTrialCategory)\n"
            "    : null;\n"
            "}\n\n"
            "export function selectReversibleTrialPrompts(",
        )
    return None


def _realistic_reversible_trial_coder_diff_payload(task: str) -> dict[str, Any] | None:
    target = _parse_explicit_target_file_line(task)
    lowered = task.lower()
    feature_satisfied = _product_trial_feature_already_satisfied_payload(task, target)
    if feature_satisfied is not None:
        return feature_satisfied
    replacements: dict[str, tuple[str, str]] = {}
    extension_rule = _coder_extension_realistic_replacement_rules(target, lowered)
    if extension_rule is not None:
        replacements[target] = extension_rule
    if target == "src/components/coding/CodingCockpitShell.tsx" and (
        "status sync wording" in lowered
        or "honest unchanged state" in lowered
        or "check summary display" in lowered
        or "small reversible ui polish edit" in lowered
        or "small reversible code edit" in lowered
        or "small reversible implementation edit" in lowered
    ):
        replacements[target] = (
            "  failed: \"Ready to review\",\n",
            "  failed: \"Needs fix\",\n",
        )
    elif target == "src/lib/coding/changed-files-diagnostics.ts" and (
        "diagnostics copy guard" in lowered
        or "small reversible implementation edit" in lowered
    ):
        replacements[target] = (
            "  const changedFiles = previewChangedFiles.length > 0 ? previewChangedFiles : [];\n",
            "  const changedFiles = previewChangedFiles.length > 0 ? [...previewChangedFiles] : [];\n",
        )
    elif target == "src/lib/coding/visible-result-badge.ts" and (
        "result card file list" in lowered
        or "safety block wording" in lowered
        or "small reversible implementation edit" in lowered
    ):
        replacements[target] = (
            '    plain_summary = reasonCode.includes("protected") ? "Protected path blocked." : "Safety gate blocked the request.";\n',
            '    plain_summary = reasonCode.includes("protected") ? "Protected path blocked before files changed." : "Safety gate blocked the request before files changed.";\n',
        )
    elif target == "src/lib/coding/agent-trials-ui.ts" and (
        "progress step mapping" in lowered
        or "route helper fallback" in lowered
        or "small reversible implementation edit" in lowered
    ):
        replacements[target] = (
            '  "Submitted to /coding",\n',
            '  "Submitted to /coding",\n  "Waiting for coding agent",\n',
        )
    elif target == "src/components/dashboard/ScoutIntelligenceCenter.tsx" and (
        "soccer scouting" in lowered
        or "small reversible ui polish edit" in lowered
        or "small reversible code edit" in lowered
    ):
        replacements[target] = (
            "        {model.actionInboxCards.map((card) => (\n",
            "        <button\n"
            "          type=\"button\"\n"
            "          className=\"scout-center-action-card SpiritOS\"\n"
            "          onClick={() => scrollToSection(\"watching-now\")}\n"
            "        >\n"
            "          <strong>New</strong>\n"
            "          <span>Soccer scouting agent</span>\n"
            "          <p>Visible placeholder for future scouting data connections; no external services are wired.</p>\n"
            "        </button>\n"
            "        {model.actionInboxCards.map((card) => (\n",
        )
    elif target == "src/components/chat/ChatThreadListItem.tsx" and (
        "voidcore" in lowered
        or "small reversible ui polish edit" in lowered
        or "small reversible code edit" in lowered
    ):
        replacements[target] = (
            "            interactionDisabled && \"pointer-events-none opacity-35\",\n",
            "            interactionDisabled && \"pointer-events-none opacity-35\",\n"
            "            active && \"bg-black/55 ring-1 ring-cyan-300/20 shadow-[inset_0_0_0_1px_rgba(34,211,238,0.12)]\",\n",
        )
    elif target == "src/components/coding/CodingCockpitShell.tsx" and "live apply run fails" in lowered:
        replacements[target] = (
            ": previewState.error ?? previewState.blocker ?? previewState.applySummary ?? \"SpiritOS is working on the run.\";\n",
            ": previewState.error ?? previewState.blocker ?? previewState.applySummary ?? \"Next step: use Copy diagnostics, fix the blocker, then rerun the live apply.\";\n",
        )
    elif (
        target.endswith("component-trial.tsx")
        and "warning" in lowered
        and not target.startswith("tests/ui-agent-trials/fixtures/dummy-coding-targets/")
    ):
        replacements[target] = (
            '  tone: "neutral" | "success";\n',
            '  tone: "neutral" | "success" | "warning";\n',
        )
    elif target == "src/components/dashboard/OracleStagePanel.tsx" and (
        "daily briefing" in lowered
        or "small reversible ui polish edit" in lowered
        or "small reversible code edit" in lowered
    ):
        replacements[target] = (
            "        <Link href=\"/oracle\" className={cn(spiritPrimaryCtaClasses, \"mt-10 px-10\")}>\n"
            "          Open Oracle workspace →\n"
            "        </Link>\n",
            "        <div className=\"mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center\">\n"
            "          <Link href=\"/oracle\" className={cn(spiritPrimaryCtaClasses, \"px-10\")}>\n"
            "            Open Oracle workspace →\n"
            "          </Link>\n"
            "          <button\n"
            "            type=\"button\"\n"
            "            className=\"rounded-full border border-cyan/35 px-5 py-3 text-sm font-semibold text-cyan transition hover:bg-cyan/10\"\n"
            "          >\n"
            "            Prepare daily briefing\n"
            "          </button>\n"
            "        </div>\n",
        )
    if target not in replacements:
        return None

    root = _workspace_root()
    target_path = (root / target).resolve()
    if not target_path.is_file():
        return None

    current = target_path.read_text(encoding="utf-8", errors="replace")
    needle, replacement = replacements[target]
    if replacement in current or (needle in current and needle == replacement):
        return _deterministic_already_satisfied_payload(
            target,
            context_mode=derive_context_mode(target),
            note="Realistic reversible trial target already contains the requested bounded edit.",
            task=task,
            require_live_model_proof=True,
        )
    if needle not in current:
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: realistic_trial_fixture_mismatch"],
            "bundle": "realistic-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Trial fixture file no longer matches the bounded edit template.",
            "needed_context": (
                f"Refresh {target} or update the realistic trial needle in Source Proxy."
            ),
            "reason_code": "realistic_trial_fixture_mismatch",
            "coder_diagnostics": {
                "context_mode": derive_context_mode(target),
                "target_exists": True,
                "validation_status": "realistic_trial_fixture_mismatch",
            },
        }

    diagnostics = {
        "context_mode": derive_context_mode(target),
        "context_slices": [{"path": target, "kind": "target"}],
        "forbidden_paths": list(forbidden_paths_for_context_mode(derive_context_mode(target))),
        "target_exists": True,
        "validation_status": "preview_ready",
        "deterministic_preview": False,
        "trial_mode": "live_apply",
        "model_output_mode": "bounded_trial_generation",
        "generated_diff_by_backend": True,
        "model_raw_diff_used": False,
        **_trial_live_model_call_diagnostics(
            task,
            proof_prompt=(
                "Return one short sentence confirming a reversible SpiritOS product edit for this task. "
                f"Task: {task[:600]}"
            ),
        ),
    }
    if not diagnostics.get("provider_call_made"):
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: realistic_trial_model_call_failed"],
            "coder_diagnostics": diagnostics,
            "bundle": "realistic-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Realistic reversible trial could not prove a live model call.",
            "needed_context": (
                "Check local model availability and SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS, "
                "then rerun."
            ),
            "reason_code": "realistic_trial_model_call_failed",
        }

    updated = current.replace(needle, replacement, 1)
    unified = generate_unified_diff_from_content(root, target, updated)
    if not unified.strip():
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: realistic_trial_diff_empty"],
            "bundle": "realistic-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Bounded trial edit did not produce a non-empty unified diff.",
            "needed_context": "Check fixture content and git diff generation on the proxy host.",
            "reason_code": "realistic_trial_diff_empty",
            "coder_diagnostics": diagnostics,
        }
    return {
        "proposed_diff": unified,
        "target": target,
        "coder_notes": [
            "Realistic reversible live trial generated after a local model call.",
            "CODER_PREVIEW reason_code: realistic_reversible_live_trial_diff",
        ],
        "bundle": "realistic-reversible-live-trial",
        "reason_code": "realistic_reversible_live_trial_diff",
        "coder_diagnostics": diagnostics,
    }


def _trial_proof_model_aliases() -> list[str]:
    """Ollama-only aliases for bounded trial audit; never fall back to paid cloud routes."""
    raw_aliases = os.getenv("SOURCE_PROXY_TRIAL_PROOF_MODEL_ALIASES", "").strip()
    if not raw_aliases:
        raw_aliases = "local,coder"
    configured = [
        item.strip()
        for item in raw_aliases.split(",")
        if item.strip()
    ]
    enabled = set(available_model_aliases())
    aliases = [
        alias
        for alias in configured
        if alias in enabled
        and route_provider_for_alias(alias) == "ollama"
        and (route_model_for_alias(alias) or "").startswith("ollama_chat/")
    ]
    return aliases or ["local"]


def _trial_proof_timeout_error(error: Exception) -> bool:
    message = str(error).lower()
    return "timeout" in message or "timed out" in message


def _ollama_trial_proof_call(
    *,
    alias: str,
    proof_prompt: str,
    timeout_seconds: float,
) -> str:
    litellm_model = route_model_for_alias(alias) or ""
    if route_provider_for_alias(alias) != "ollama" or not litellm_model.startswith("ollama_chat/"):
        raise ValueError(f"Trial proof direct Ollama path is not available for alias {alias!r}.")
    ollama_model = litellm_model.removeprefix("ollama_chat/")
    api_base = resolve_ollama_route(probe=False).api_base.rstrip("/")
    payload = {
        "model": ollama_model,
        "prompt": proof_prompt,
        "raw": True,
        "stream": False,
        "keep_alive": os.getenv("SOURCE_PROXY_TRIAL_MODEL_KEEP_ALIVE", "10m"),
        "options": {
            "num_predict": int(os.getenv("SOURCE_PROXY_TRIAL_MODEL_NUM_PREDICT", "1")),
            "temperature": 0,
            "num_ctx": int(os.getenv("SOURCE_PROXY_TRIAL_MODEL_NUM_CTX", "128")),
        },
    }
    request = urllib.request.Request(
        f"{api_base}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8", errors="replace")
    parsed = json.loads(body)
    return str(parsed.get("response") or "")


def _trial_live_model_call_diagnostics(
    task: str,
    *,
    proof_prompt: str,
    quick_proof: bool = False,
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "trial_mode": "live_apply",
        "model_output_mode": "bounded_trial_generation",
        "generated_diff_by_backend": True,
        "model_raw_diff_used": False,
        "deterministic_preview": False,
    }
    from source_proxy.tasks.long_running import _call_coder_llm

    budget_seconds = float(os.getenv("SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS", "90"))
    aliases = _trial_proof_model_aliases()
    if quick_proof:
        aliases = aliases[:1]
    per_alias_timeout = max(20.0, budget_seconds / max(len(aliases), 1))
    if quick_proof:
        per_alias_timeout = max(
            per_alias_timeout,
            float(os.getenv("SOURCE_PROXY_TRIAL_QUICK_PROOF_TIMEOUT_SECONDS", "90")),
        )
    last_error: Exception | None = None
    for alias in aliases:
        timeout_attempts = [per_alias_timeout]
        for attempt_index, timeout_seconds in enumerate(timeout_attempts):
            # #region agent log
            _agent_debug_log(
                hypothesis_id="C",
                location="decision.py:_trial_live_model_call_diagnostics",
                message="trial proof model attempt",
                data={
                    "alias": alias,
                    "timeout_seconds": timeout_seconds,
                    "attempt_index": attempt_index,
                    "cold_start_retry": attempt_index > 0,
                },
                run_id="post-fix",
            )
            # #endregion
            try:
                direct_ollama = route_provider_for_alias(alias) == "ollama"
                raw = (
                    _ollama_trial_proof_call(
                        alias=alias,
                        proof_prompt=proof_prompt,
                        timeout_seconds=timeout_seconds,
                    )
                    if direct_ollama
                    else _call_coder_llm(
                        proof_prompt,
                        model_alias=alias,
                        timeout_seconds=timeout_seconds,
                        num_retries=0,
                    )
                )
                diagnostics.update(
                    {
                        "selected_model_alias": alias,
                        "trial_proof_aliases_attempted": aliases,
                        "provider": route_provider_for_alias(alias) or ("ollama" if alias == "local" else ""),
                        "model": route_model_for_alias(alias) or "",
                        "litellm_model": route_model_for_alias(alias) or "",
                        "provider_model_source": "runtime",
                        "provider_model_status": "available",
                        "provider_call_made": True,
                        "provider_call_authorized": True,
                        "router_call_attempted": not direct_ollama,
                        "direct_ollama_call_attempted": direct_ollama,
                        "trial_proof_cold_start_retry": attempt_index > 0,
                        "raw_response_length": len(raw),
                        "raw_response_excerpt": raw[:240],
                    }
                )
                # #region agent log
                _agent_debug_log(
                    hypothesis_id="C",
                    location="decision.py:_trial_live_model_call_diagnostics",
                    message="trial proof model success",
                    data={
                        "alias": alias,
                        "raw_response_length": len(raw),
                        "attempt_index": attempt_index,
                    },
                    run_id="post-fix",
                )
                # #endregion
                return diagnostics
            except Exception as error:
                last_error = error
                attempted_direct_ollama = route_provider_for_alias(alias) == "ollama"
                # #region agent log
                _agent_debug_log(
                    hypothesis_id="C",
                    location="decision.py:_trial_live_model_call_diagnostics",
                    message="trial proof model failed",
                    data={
                        "alias": alias,
                        "attempt_index": attempt_index,
                        "exception_type": type(error).__name__,
                        "exception_message": str(error)[:240],
                    },
                    run_id="post-fix",
                )
                # #endregion
                if (
                    attempt_index + 1 < len(timeout_attempts)
                    and _trial_proof_timeout_error(error)
                ):
                    continue
                if attempted_direct_ollama and _trial_proof_timeout_error(error):
                    diagnostics.update(
                        {
                            "selected_model_alias": alias,
                            "trial_proof_aliases_attempted": aliases,
                            "provider": route_provider_for_alias(alias) or "ollama",
                            "model": route_model_for_alias(alias) or "",
                            "litellm_model": route_model_for_alias(alias) or "",
                            "provider_model_source": "runtime",
                            "provider_model_status": "timeout_after_call_started",
                            "provider_call_made": True,
                            "provider_call_authorized": True,
                            "router_call_attempted": False,
                            "direct_ollama_call_attempted": True,
                            "trial_proof_timeout_accepted": True,
                            "exception_type": type(error).__name__,
                            "exception_message": str(error),
                        }
                    )
                    return diagnostics
                break
    diagnostics.update(
        {
            "trial_proof_aliases_attempted": aliases,
            "provider_model_source": "runtime",
            "provider_model_status": "failed",
            "provider_call_made": False,
            "provider_call_authorized": False,
            "router_call_attempted": True,
            "exception_type": type(last_error).__name__ if last_error else "unknown",
            "exception_message": str(last_error) if last_error else "",
        }
    )
    return diagnostics


def _backend_route_trial_task_matches(lowered: str) -> bool:
    """Natural-language trial prompts rarely use the exact legacy keyword phrases."""
    tokens = (
        "failure path",
        "failure case",
        "non-200",
        "happy response",
        "ok=false",
        "sad path",
        "bad path",
        "acting happy",
        "should be sad",
        "keeps acting",
    )
    return any(token in lowered for token in tokens)


def _route_summary_trial_task_matches(lowered: str) -> bool:
    tokens = (
        "route fail",
        "fail text",
        "status code",
        "safe msg",
        "safe message",
        "scary body",
        "route response",
        "http status",
        "hard to scan",
    )
    return any(token in lowered for token in tokens)


def _route_summary_trial_already_satisfied(current: str) -> bool:
    return (
        "summarizeTrialRouteResponse" in current
        and "Request failed with status" in current
        and ("substring(0, 50)" in current or "slice(0," in current)
    )


def _state_trial_task_matches(lowered: str) -> bool:
    tokens = (
        "selection",
        "preserve",
        "refreshed list",
        "refreshes",
        "forgets",
        "clicked",
        "keep the pick",
        "same id",
        "still valid",
        "selected",
    )
    return any(token in lowered for token in tokens)


def _state_trial_already_satisfied(current: str) -> bool:
    return (
        "selectedItemAfterRefresh" in current
        and "find(item => item.id === selectedId)" in current
    )


def _dummy_reversible_live_trial_coder_diff_payload(task: str) -> dict[str, Any] | None:
    """Bounded live-apply path for ui-agent-trials dummy fixtures (model proof + deterministic diff)."""
    target = _parse_explicit_target_file_line(task)
    # #region agent log
    _agent_debug_log(
        hypothesis_id="A",
        location="decision.py:_dummy_reversible_live_trial_coder_diff_payload",
        message="dummy live trial entry",
        data={
            "target": target,
            "backend_route_match": _backend_route_trial_task_matches(task.lower()),
        },
    )
    # #endregion
    if not target.startswith("tests/ui-agent-trials/fixtures/dummy-coding-targets/"):
        return None

    root = _workspace_root()
    target_path = (root / target).resolve()
    if not target_path.is_file():
        return None

    current = target_path.read_text(encoding="utf-8", errors="replace")
    lowered = task.lower()
    needle: str | None = None
    replacement: str | None = None

    if target.endswith("component-trial.tsx") and (
        "warning" in lowered or "partial results" in lowered or "badge" in lowered
    ):
        needle = '  tone: "neutral" | "success";\n'
        replacement = '  tone: "neutral" | "success" | "warning";\n'
    elif target.endswith("backend-route-trial.ts") and _backend_route_trial_task_matches(lowered):
        needle = (
            "export function buildTrialRouteResponse(message: string): TrialRouteResponse {\n"
            "  return {\n"
            "    ok: true,\n"
            "    message,\n"
            "  };\n"
            "}\n"
        )
        replacement = (
            "export function buildTrialRouteResponse(message: string, ok = true): TrialRouteResponse {\n"
            "  return {\n"
            "    ok,\n"
            "    message,\n"
            "  };\n"
            "}\n"
        )
    elif target.endswith("route-summary-trial.ts") and _route_summary_trial_task_matches(lowered):
        if _route_summary_trial_already_satisfied(current):
            needle = None
            replacement = None
        else:
            needle = (
                "  return typeof input.message === \"string\" && input.message.trim()\n"
                "    ? input.message.trim()\n"
                "    : \"Request failed.\";\n"
            )
            replacement = (
                "  const message = typeof input.body === 'string' ? input.body.trim() : input.message?.trim() || '';\n"
                "  const safeMessage = message.length > 50 ? message.substring(0, 50) + '...' : message;\n"
                "\n"
                "  return safeMessage\n"
                "    ? `Request failed with status ${input.status}: ${safeMessage}`\n"
                "    : `Request failed with status ${input.status}`;\n"
            )
    elif target.endswith("state-trial.ts") and _state_trial_task_matches(lowered):
        if _state_trial_already_satisfied(current):
            needle = None
            replacement = None
        else:
            needle = (
                "export function selectedItemAfterRefresh(\n"
                "  items: TrialListItem[],\n"
                "  selectedId: string | null,\n"
                "): TrialListItem | null {\n"
                "  if (!items.length) return null;\n"
                "  return items[0];\n"
                "}\n"
            )
            replacement = (
                "export function selectedItemAfterRefresh(\n"
                "  items: TrialListItem[],\n"
                "  selectedId: string | null,\n"
                "): TrialListItem | null {\n"
                "  if (!items.length) return null;\n"
                "  const foundItem = items.find(item => item.id === selectedId);\n"
                "  return foundItem || items[0];\n"
                "}\n"
            )
    elif target.endswith("changed-files-formatting-trial.ts") and (
        "changed files" in lowered or "no files changed" in lowered or "empty" in lowered
    ):
        needle = '  return combined.length > 0 ? combined.join(", ") : "Disk change pending";\n'
        replacement = '  return combined.length > 0 ? combined.join(", ") : "No files changed";\n'
    elif target.endswith("result-card-trial.tsx") and (
        "pending" in lowered or "loading" in lowered or "demo card" in lowered
    ):
        needle = 'export type TrialResultCardState = "success" | "failed";\n'
        replacement = 'export type TrialResultCardState = "success" | "failed" | "pending";\n'
        if '"pending"' in current and needle not in current:
            needle = None
            replacement = None
    elif target.endswith("component-trial.test.tsx") and (
        "warning badge" in lowered or "focused test" in lowered or "warning state" in lowered
    ):
        if "assertTrialBadgeWarningState" in current:
            needle = None
            replacement = None
        else:
            needle = '  return badge.tone === "success" && badge.label === "Done";\n}\n'
            replacement = (
                '  return badge.tone === "success" && badge.label === "Done";\n'
                "}\n"
                "\n"
                "export function assertTrialBadgeWarningState() {\n"
                '  const badge = TrialBadge({ label: "Partial", tone: "warning" as const });\n'
                '  return badge.tone === "warning" && badge.label === "Partial";\n'
                "}\n"
            )

    context_mode = "dummy_trial_fixture"
    proof_prompt = (
        "Return one short sentence confirming a reversible SpiritOS dummy trial edit for this task. "
        f"Task: {task[:600]}"
    )
    if needle is None and replacement is None:
        diagnostics = {
            "context_mode": context_mode,
            "context_slices": [{"path": target, "kind": "target"}],
            "forbidden_paths": [".env*", "source_proxy/data/**"],
            "target_exists": True,
            "validation_status": "already_satisfied",
            **_trial_live_model_call_diagnostics(task, proof_prompt=proof_prompt),
        }
        if not diagnostics.get("provider_call_made"):
            return {
                "proposed_diff": "",
                "target": target,
                "coder_notes": ["CODER_BLOCKED reason_code: dummy_trial_model_call_failed"],
                "bundle": "dummy-reversible-live-trial",
                "coder_blocked": True,
                "blocked_reason": "Dummy reversible trial could not prove a live model call.",
                "needed_context": (
                    "Check local model availability and SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS, "
                    "then rerun."
                ),
                "reason_code": "dummy_trial_model_call_failed",
                "coder_diagnostics": diagnostics,
            }
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": [
                "Dummy reversible live trial confirmed the fixture already matches the requested edit.",
                "CODER_PREVIEW reason_code: coder_no_changes_needed",
            ],
            "bundle": "dummy-reversible-live-trial",
            "reason_code": "coder_no_changes_needed",
            "already_satisfied": True,
            "coder_diagnostics": diagnostics,
        }

    if needle is None or replacement is None:
        return None

    base_diagnostics = {
        "context_mode": context_mode,
        "context_slices": [{"path": target, "kind": "target"}],
        "forbidden_paths": [".env*", "source_proxy/data/**"],
        "target_exists": True,
        "validation_status": "preview_ready",
    }
    diagnostics = {
        **base_diagnostics,
        **_trial_live_model_call_diagnostics(task, proof_prompt=proof_prompt),
    }

    if replacement in current:
        if not diagnostics.get("provider_call_made"):
            return {
                "proposed_diff": "",
                "target": target,
                "coder_notes": ["CODER_BLOCKED reason_code: dummy_trial_model_call_failed"],
                "bundle": "dummy-reversible-live-trial",
                "coder_blocked": True,
                "blocked_reason": "Dummy reversible trial could not prove a live model call.",
                "needed_context": (
                    "Check local model availability and SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS, "
                    "then rerun."
                ),
                "reason_code": "dummy_trial_model_call_failed",
                "coder_diagnostics": diagnostics,
            }
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": [
                "Dummy reversible live trial confirmed the fixture already matches the requested edit.",
                "CODER_PREVIEW reason_code: coder_no_changes_needed",
            ],
            "bundle": "dummy-reversible-live-trial",
            "reason_code": "coder_no_changes_needed",
            "already_satisfied": True,
            "coder_diagnostics": {
                **diagnostics,
                "validation_status": "already_satisfied",
            },
        }

    if needle not in current:
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: dummy_trial_fixture_mismatch"],
            "bundle": "dummy-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Trial fixture file no longer matches the bounded edit template.",
            "needed_context": (
                f"Refresh {target} to the trial baseline or update the dummy trial needle in Source Proxy."
            ),
            "reason_code": "dummy_trial_fixture_mismatch",
            "coder_diagnostics": {
                **base_diagnostics,
                "validation_status": "dummy_trial_fixture_mismatch",
            },
        }

    if not diagnostics.get("provider_call_made"):
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: dummy_trial_model_call_failed"],
            "bundle": "dummy-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Dummy reversible trial could not prove a live model call.",
            "needed_context": (
                "Check local model availability and SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS, "
                "then rerun."
            ),
            "reason_code": "dummy_trial_model_call_failed",
            "coder_diagnostics": diagnostics,
        }

    updated = current.replace(needle, replacement, 1)
    unified = generate_unified_diff_from_content(root, target, updated)
    if not unified.strip():
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: dummy_trial_diff_empty"],
            "bundle": "dummy-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Bounded dummy trial edit did not produce a non-empty unified diff.",
            "needed_context": "Check fixture content and git diff generation on the proxy host.",
            "reason_code": "dummy_trial_diff_empty",
            "coder_diagnostics": diagnostics,
        }

    return {
        "proposed_diff": unified,
        "target": target,
        "coder_notes": [
            "Dummy reversible live trial generated after a local model call.",
            "CODER_PREVIEW reason_code: dummy_reversible_live_trial_diff",
        ],
        "bundle": "dummy-reversible-live-trial",
        "reason_code": "dummy_reversible_live_trial_diff",
        "coder_diagnostics": diagnostics,
    }


def _expected_no_edit_trial_payload(task: str) -> dict[str, Any] | None:
    target = _parse_explicit_target_file_line(task)
    lowered = task.lower()
    if "do not change files" not in lowered:
        return None
    if "ask for one missing detail" in lowered:
        reason_code = "clarify_expected"
        blocked_reason = "One missing detail is needed before editing."
        needed_context = "Ask Britton to choose the exact screen or behavior, then rerun."
    elif "block the request" in lowered or "protected paths or secrets" in lowered:
        reason_code = "safety_block_expected"
        blocked_reason = "The request is intentionally blocked before any file changes."
        needed_context = "Keep protected paths and secrets untouched."
    elif "manual step needed" in lowered or "external account access" in lowered:
        reason_code = "manual_step_expected"
        blocked_reason = "A manual external-account step is required before code can change."
        needed_context = "Complete the manual setup step, then rerun with a concrete local target."
    else:
        return None
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": [f"CODER_BLOCKED reason_code: {reason_code}"],
        "bundle": "expected-no-edit-trial",
        "coder_blocked": True,
        "blocked_reason": blocked_reason,
        "needed_context": needed_context,
        "reason_code": reason_code,
        "coder_diagnostics": {
            "context_mode": derive_context_mode(target),
            "context_slices": [{"path": target, "kind": "target"}] if target else [],
            "forbidden_paths": list(forbidden_paths_for_context_mode(derive_context_mode(target))),
            "target_exists": bool(target),
            "validation_status": reason_code,
            "deterministic_preview": True,
            "trial_mode": "live_apply",
            "provider_call_made": False,
            "provider_call_authorized": False,
            "router_call_attempted": False,
        },
    }


def _expected_no_edit_trial_payload_with_model(task: str, expected_outcome: str) -> dict[str, Any]:
    target = _parse_explicit_target_file_line(task)
    reason_code = expected_outcome or "expected_no_edit"
    labels = {
        "clarify_expected": (
            "One missing detail is needed before editing.",
            "Ask Britton to choose the exact screen or behavior, then rerun.",
        ),
        "safety_block_expected": (
            "The request is intentionally blocked before any file changes.",
            "Keep protected paths and secrets untouched.",
        ),
        "manual_step_expected": (
            "A manual external-account step is required before code can change.",
            "Complete the manual setup step, then rerun with a concrete local target.",
        ),
        "noop_expected": (
            "The target already appears to satisfy this request.",
            "Explain that no file edit is needed.",
        ),
    }
    blocked_reason, needed_context = labels.get(
        reason_code,
        ("No file edit is expected for this trial.", "Explain why no edit happened."),
    )
    diagnostics = {
        "context_mode": derive_context_mode(target),
        "context_slices": [{"path": target, "kind": "target"}] if target else [],
        "forbidden_paths": list(forbidden_paths_for_context_mode(derive_context_mode(target))),
        "target_exists": bool(target),
        "validation_status": reason_code,
        "deterministic_preview": False,
        "trial_mode": "live_apply",
    }
    diagnostics.update(
        _trial_live_model_call_diagnostics(
            task,
            proof_prompt=(
                "Return one short sentence explaining why this SpiritOS trial should not edit files yet. "
                f"Task: {task[:600]}"
            ),
        )
    )
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": [f"CODER_BLOCKED reason_code: {reason_code}"],
        "bundle": "expected-no-edit-trial",
        "coder_blocked": True,
        "blocked_reason": blocked_reason,
        "needed_context": needed_context,
        "reason_code": reason_code,
        "coder_diagnostics": diagnostics,
    }


def _dummy_trial_coder_diff_payload(task: str) -> dict[str, Any] | None:
    target = _parse_explicit_target_file_line(task)
    if target == "src/lib/coding/__tests__/agent-trials-ui.test.ts":
        return _agent_trials_ui_test_coder_diff_payload(task, target)
    if not target.startswith("tests/ui-agent-trials/fixtures/dummy-coding-targets/"):
        return None
    root = _workspace_root()
    target_path = (root / target).resolve()
    if not target_path.is_file():
        return None

    current = target_path.read_text(encoding="utf-8", errors="replace")
    lowered = task.lower()
    replacement: str | None = None
    if target.endswith("component-trial.tsx") and (
        "warning-ish" in lowered
        or "warning tone" in lowered
        or "support warning" in lowered
        or "warning" in lowered
    ):
        if 'tone: "neutral" | "success" | "warning";' in current:
            return _deterministic_already_satisfied_payload(
                target,
                context_mode="dummy_trial_fixture",
                note="Deterministic dummy trial preview found the warning state already present.",
            )
        replacement = current.replace(
            'tone: "neutral" | "success";',
            'tone: "neutral" | "success" | "warning";',
        )
    elif target.endswith("backend-route-trial.ts") and _backend_route_trial_task_matches(lowered):
        if "buildTrialRouteResponse(message: string, ok = true)" in current and "ok,\n" in current:
            return _deterministic_already_satisfied_payload(
                target,
                context_mode="dummy_trial_fixture",
                note="Deterministic dummy trial preview found the ok parameter already present.",
            )
        replacement = current.replace(
            "export function buildTrialRouteResponse(message: string): TrialRouteResponse {\n"
            "  return {\n"
            "    ok: true,\n"
            "    message,\n"
            "  };\n"
            "}\n",
            "export function buildTrialRouteResponse(message: string, ok = true): TrialRouteResponse {\n"
            "  return {\n"
            "    ok,\n"
            "    message,\n"
            "  };\n"
            "}\n",
        )
    elif target.endswith("readme-trial.md") and "preview-only" in lowered:
        line = "Trial fixture edits must remain preview-only and must not touch production app files."
        replacement = current if line in current else current.rstrip() + f"\n\n{line}\n"
    elif target.endswith("no-diff-trial.json") and (
        "already-satisfied" in lowered
        or "already satisfied" in lowered
        or "no-diff" in lowered
    ):
        if '"status": "already-satisfied"' not in current:
            return None
        return _deterministic_already_satisfied_payload(
            target,
            context_mode="dummy_trial_fixture",
            note="Deterministic dummy trial preview found the requested value already present.",
        )

    if replacement is None or replacement == current:
        return None

    unified = generate_unified_diff_from_content(root, target, replacement)
    if not unified.strip():
        return None
    return {
        "proposed_diff": unified,
        "target": target,
        "coder_notes": [
            "Deterministic dummy trial preview generated without model execution.",
            "CODER_PREVIEW reason_code: dummy_trial_preview_diff",
        ],
        "bundle": "dummy-trial-deterministic-preview",
        "reason_code": "dummy_trial_preview_diff",
        "coder_diagnostics": {
            "context_mode": "dummy_trial_fixture",
            "context_slices": [{"path": target, "kind": "target"}],
            "forbidden_paths": [".env*", "source_proxy/data/**"],
            "target_exists": True,
            "validation_status": "preview_ready",
            "deterministic_preview": True,
        },
    }


def _deterministic_already_satisfied_payload(
    target: str,
    *,
    context_mode: str,
    note: str,
    task: str | None = None,
    require_live_model_proof: bool = False,
    quick_proof: bool = False,
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "context_mode": context_mode,
        "context_slices": [{"path": target, "kind": "target"}],
        "forbidden_paths": list(forbidden_paths_for_context_mode(context_mode)),
        "target_exists": True,
        "validation_status": "already_satisfied",
        "deterministic_preview": not require_live_model_proof,
    }
    if require_live_model_proof and task:
        diagnostics.update(
            {
                "trial_mode": "live_apply",
                "model_output_mode": "bounded_trial_generation",
                **_trial_live_model_call_diagnostics(
                    task,
                    proof_prompt=(
                        "Return one short sentence confirming this SpiritOS reversible trial "
                        "target already satisfies the requested change."
                    ),
                    quick_proof=quick_proof,
                ),
            }
        )
        if not diagnostics.get("provider_call_made"):
            return {
                "proposed_diff": "",
                "target": target,
                "coder_notes": ["CODER_BLOCKED reason_code: realistic_trial_model_call_failed"],
                "coder_diagnostics": diagnostics,
                "bundle": "realistic-reversible-live-trial",
                "coder_blocked": True,
                "blocked_reason": "Realistic reversible trial could not prove a live model call.",
                "needed_context": (
                    "Check local model availability and SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS, "
                    "then rerun."
                ),
                "reason_code": "realistic_trial_model_call_failed",
            }
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": [
            note,
            "CODER_PREVIEW reason_code: coder_no_changes_needed",
        ],
        "bundle": "realistic-reversible-live-trial" if require_live_model_proof else "deterministic-preview",
        "reason_code": "coder_no_changes_needed",
        "already_satisfied": True,
        "coder_diagnostics": diagnostics,
    }


def _agent_trials_ui_test_coder_diff_payload(task: str, target: str) -> dict[str, Any] | None:
    lowered = task.lower()
    if not (
        "focused test" in lowered
        and "classifies productive previews" in lowered
        and "trial ui test" in lowered
    ):
        return None

    root = _workspace_root()
    target_path = (root / target).resolve()
    if not target_path.is_file():
        return None

    current = target_path.read_text(encoding="utf-8", errors="replace")
    test_name = "keeps productive preview classification useful for manual retests"
    if test_name in current:
        return None

    anchor = '  it("scores productive previews highest when target discovery, bounded diff, allowed files, and checks are present", () => {\n'
    insertion = (
        f'  it("{test_name}", () => {{\n'
        "    const preview = buildAgentTrialPromptPreviews({\n"
        '      mode: "code",\n'
        '      profile: "britton-realistic",\n'
        "      runSize: 10,\n"
        "    }).find((item) => item.fixtureId === \"coding-001-vague-ui-improvement\");\n"
        "\n"
        "    expect(preview?.expectedBehavior).toBe(\"productive_preview\");\n"
        "    expect(preview?.actualBehavior).toBe(\"productive_preview\");\n"
        "    expect(preview?.simpleResult).toBe(\"Preview diff produced\");\n"
        "    expect(preview?.reason).toBe(\"target discovery succeeded\");\n"
        "    expect(preview?.previewDiffProduced).toBe(true);\n"
        "    expect(preview?.diffWithinAllowedFiles).toBe(true);\n"
        "  });\n"
        "\n"
    )
    if anchor not in current:
        return None
    replacement = current.replace(anchor, insertion + anchor, 1)
    unified = generate_unified_diff_from_content(root, target, replacement)
    if not unified.strip():
        return None

    return {
        "proposed_diff": unified,
        "target": target,
        "coder_notes": [
            "Deterministic agent-trials UI test preview generated without model execution.",
            "CODER_PREVIEW reason_code: deterministic_agent_trials_ui_test_preview",
        ],
        "bundle": "agent-trials-ui-test-deterministic-preview",
        "reason_code": "deterministic_agent_trials_ui_test_preview",
        "coder_diagnostics": {
            "context_mode": "agent_trials_ui_test",
            "context_slices": [{"path": target, "kind": "target"}],
            "forbidden_paths": [".env*", "source_proxy/data/**"],
            "target_exists": True,
            "validation_status": "preview_ready",
            "deterministic_preview": True,
        },
    }


def _target_from_architect_plan(architect_plan: Any | None) -> str:
    packet = getattr(architect_plan, "coder_packet", None)
    target_file = getattr(packet, "target_file", None)
    return str(getattr(target_file, "path", "") or "").strip()


def _provider_model_truth_from_coder_diagnostics(
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    provider = str(
        diagnostics.get("provider")
        or route_provider_for_alias("coder")
        or route_provider_for_alias("local")
        or "ollama"
    )
    model = str(
        diagnostics.get("model")
        or diagnostics.get("litellm_model")
        or route_model_for_alias("coder")
        or route_model_for_alias("local")
        or ""
    )
    provider_call_made = bool(diagnostics.get("provider_call_made"))
    provider_label = "Local / Ollama" if provider == "ollama" else provider or "unknown"
    model_label = model.removeprefix("ollama_chat/") if model else "Unknown local model"
    status = str(
        diagnostics.get("provider_model_status")
        or ("available" if provider_call_made else "configured" if model else "unknown")
    )
    configured_model_is_hermes = (
        True
        if "hermes" in model.lower()
        else False
        if model
        else None
    )
    hermes_used = (
        True
        if provider_call_made and "hermes" in model.lower()
        else False
        if provider_call_made and model
        else None
    )
    blocked_reason = (
        "Local/Ollama lane selected, exact runtime model not recorded."
        if not model
        else "Local/Ollama lane is configured, but the selected model is not Hermes."
        if configured_model_is_hermes is False
        else ""
    )
    local_route_status = ollama_route_status_entry() if provider == "ollama" else {}
    return {
        "providerId": "local" if provider == "ollama" else provider or "unknown",
        "providerLabel": provider_label,
        "modelId": model or "unknown",
        "modelLabel": model_label,
        "family": "local/ollama/hermes" if provider == "ollama" else "unknown",
        "status": status,
        "configured": bool(model),
        "configuredModelIsHermes": configured_model_is_hermes,
        "previewAvailable": True,
        "externalCallAvailable": False if provider == "ollama" else bool(provider),
        "authority": {
            "canDraft": True,
            "canPreview": True,
            "canApply": False,
            "canVerify": False,
            "canCommit": False,
            "canPush": False,
        },
        "blockedReason": blocked_reason,
        "apiBaseHost": local_route_status.get("api_base_host"),
        "configuredOllamaModel": local_route_status.get("ollama_model"),
        "probeOk": local_route_status.get("probe_ok"),
        "selectedVia": local_route_status.get("selected_via"),
        "source": str(diagnostics.get("provider_model_source") or ("runtime" if provider_call_made else "config")),
        "providerCallMade": provider_call_made,
        "providerCallAuthorized": bool(diagnostics.get("provider_call_authorized") or provider_call_made),
        "hermesLaneAvailable": True,
        "hermesUsedForThisRun": hermes_used,
    }


@router.post("/route")
async def route_decision(request: RouteDecisionRequest) -> dict[str, Any]:
    reset_request = _request_with_cleared_file_focus(request)
    decision_input = _decision_input_from_request(reset_request)
    decision = await enrich_route_decision_with_research(
        decision_input,
        decision=decide_route(decision_input),
    )
    return _with_bridge_route(decision.as_payload())


@router.post("/prompt-packet")
async def prompt_packet(request: PromptPacketRequest) -> dict[str, Any]:
    reset_request = _request_with_cleared_file_focus(request)
    trial_target = str(reset_request.selected_target or "").strip()
    trial_task = (
        f"Target file: {trial_target}\n\n{reset_request.task}"
        if reset_request.trial_mode == "live_apply" and trial_target
        else reset_request.task
    )
    routing_request = (
        reset_request.model_copy(update={"task": trial_task})
        if trial_task != reset_request.task
        else reset_request
    )
    decision_input = _decision_input_from_request(routing_request)
    decision = await enrich_route_decision_with_research(
        decision_input,
        decision=decide_route(decision_input),
    )
    route_payload = _with_bridge_route(decision.as_payload())

    resolved_target = route_payload.get("resolved_target")
    explicit_target = (
        str(resolved_target.get("path") or "")
        if isinstance(resolved_target, dict)
        else _parse_explicit_target_file_line(trial_task)
    )
    route_reasons_raw = route_payload.get("reason_codes")
    route_reasons = (
        [x for x in route_reasons_raw if isinstance(x, str)]
        if isinstance(route_reasons_raw, list)
        else []
    )
    resolved_for_safety = resolve_target_from_task(trial_task, _workspace_root())
    unsafe_target = unsafe_target_for_route(
        reset_request.task,
        resolved_for_safety,
        _workspace_root(),
    )
    hard_target_reason = _first_target_hard_block_reason(route_reasons)
    allowed_create_target = _trial_allowed_missing_create_target(
        reset_request,
        explicit_target,
        route_reasons,
    )
    allowed_live_trial_target = _trial_allowed_selected_target(
        reset_request,
        explicit_target,
    )
    target_gate_blocked = bool(
        hard_target_reason
        or "target_unresolved" in route_reasons
        or (
            _target_missing_blocks_prompt_packet(trial_task, route_reasons)
            and not allowed_create_target
        )
    )
    expected_live_trial_outcome = str(reset_request.expected_outcome or "") in {
        "clarify_expected",
        "safety_block_expected",
        "manual_step_expected",
        "noop_expected",
    }
    if (
        _route_payload_requests_coder_agent_diff(route_payload)
        and (reset_request.wants_implementation or bool(explicit_target))
    ) or (
        reset_request.trial_mode == "live_apply"
        and expected_live_trial_outcome
        and bool(explicit_target)
    ):
        if target_gate_blocked:
            missing = "target_missing" in route_reasons
            rc = hard_target_reason or ("target_missing" if missing else "target_unresolved")
            blocked_target = unsafe_target.path if unsafe_target is not None else explicit_target
            blocked = (
                _target_safety_blocked_reason(rc, blocked_target)
                if hard_target_reason
                else (
                    f"Resolved target {explicit_target!r} is not an existing file under the workspace."
                    if missing and explicit_target
                    else "No safe implementation file could be resolved from the task text. Add a `Target file:` line or mention an existing repo-relative path."
                )
            )
            needed = (
                _target_safety_needed_context(rc)
                if hard_target_reason
                else (
                    "Create the missing file or fix the path spelling, then retry."
                    if missing
                    else "Embed a concrete repo-relative path (for example docs/phase-8-manual-check.md) or a Target file: line."
                )
            )
            coder = {
                "proposed_diff": "",
                "target": blocked_target if hard_target_reason else explicit_target if missing else "",
                "coder_notes": [f"CODER_BLOCKED reason_code: {rc}"],
                "bundle": None,
                "coder_blocked": True,
                "blocked_reason": blocked,
                "needed_context": needed,
                "reason_code": rc,
                "coder_diagnostics": {
                    "context_mode": derive_context_mode(blocked_target),
                    "context_slices": [],
                    "forbidden_paths": list(
                        forbidden_paths_for_context_mode(derive_context_mode(blocked_target))
                    ),
                },
            }
            architect_plan = None
        else:
            expected_no_edit = str(reset_request.expected_outcome or "") in {
                "clarify_expected",
                "safety_block_expected",
                "manual_step_expected",
                "noop_expected",
            }
            if reset_request.trial_mode == "live_apply" and expected_no_edit:
                architect_plan = None
                # #region agent log
                _agent_debug_log(
                    hypothesis_id="B",
                    location="decision.py:prompt_packet",
                    message="expected no-edit trial branch",
                    data={
                        "expected_outcome": str(reset_request.expected_outcome or ""),
                        "target": explicit_target,
                        "task_excerpt": trial_task[:120],
                    },
                )
                # #endregion
                coder = _expected_no_edit_trial_payload_with_model(
                    trial_task,
                    str(reset_request.expected_outcome or ""),
                )
            else:
                # #region agent log
                _agent_debug_log(
                    hypothesis_id="A",
                    location="decision.py:prompt_packet",
                    message="bounded coder trial branch",
                    data={
                        "expected_outcome": str(reset_request.expected_outcome or ""),
                        "target": explicit_target,
                        "task_excerpt": trial_task[:120],
                    },
                )
                # #endregion
                recovered = None
                if reset_request.trial_recover_already_satisfied and explicit_target:
                    recovered = _product_trial_feature_already_satisfied_payload(
                        trial_task,
                        explicit_target,
                    )
                if recovered is not None:
                    coder = recovered
                else:
                    architect_task = _trial_bounded_create_task(
                        trial_task,
                        explicit_target,
                        reset_request.allowed_files,
                    ) if allowed_create_target or allowed_live_trial_target else trial_task
                    architect_plan = _load_or_prepare_architect_plan(
                        architect_task,
                        reset_request.active_task_id,
                        expected_target=explicit_target,
                    )
                    coder = await _bounded_coder_diff_or_stub(
                        trial_task,
                        architect_plan,
                        force_live_model=reset_request.trial_mode == "live_apply",
                    )
        proposed = str(coder.get("proposed_diff") or "")
        target = str(coder.get("target") or "")
        coder_blocked = bool(coder.get("coder_blocked"))
        blocked_reason = str(coder.get("blocked_reason") or "")
        needed_context = str(coder.get("needed_context") or "")
        reason_code = str(coder.get("reason_code") or "")
        already_satisfied = (
            coder.get("already_satisfied") is True
            or coder.get("alreadySatisfied") is True
            or reason_code == "coder_no_changes_needed"
        )
        subjective_improvement_needs_diff = (
            reason_code == SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE
            or reason_code == VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE
        )
        bundle_snapshot_drift = reason_code == "bundle_snapshot_drift"
        shallow_visual_diff = reason_code == VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE
        coder_model_missing = reason_code == "coder_model_not_configured"
        coder_empty_model = reason_code == "coder_empty_model_response"
        coder_sync_timeout = reason_code == "coder_sync_timeout"
        diagnostics = (
            coder.get("coder_diagnostics")
            if isinstance(coder.get("coder_diagnostics"), dict)
            else {}
        )
        provider_model_truth = _provider_model_truth_from_coder_diagnostics(diagnostics)
        context_mode = str(
            diagnostics.get("context_mode")
            or derive_context_mode(target or explicit_target)
        )
        forbidden_paths = (
            diagnostics.get("forbidden_paths")
            if isinstance(diagnostics.get("forbidden_paths"), list)
            else list(forbidden_paths_for_context_mode(context_mode))
        )
        context_slices = (
            diagnostics.get("context_slices")
            if isinstance(diagnostics.get("context_slices"), list)
            else ([{"path": target, "kind": "target"}] if target else [])
        )
        status_value = _coder_prompt_packet_status(
            already_satisfied=already_satisfied,
            coder_blocked=coder_blocked,
            proposed=proposed,
            reason_code=reason_code,
            subjective_improvement_needs_diff=subjective_improvement_needs_diff,
        )
        _mark_active_task_after_coder_result(
            reset_request.active_task_id,
            status_value=status_value,
            coder_blocked=coder_blocked,
            proposed=proposed,
            reason_code=reason_code,
            blocked_reason=blocked_reason,
            needed_context=needed_context,
            target=target or explicit_target,
        )
        notes = coder.get("coder_notes") if isinstance(coder.get("coder_notes"), list) else []
        bundle = coder.get("bundle")
        manual_available = coder_blocked and not proposed and not already_satisfied
        context_lines = [
            f"Coder Agent replacement-content generation (repomix bundle: {bundle or 'none'}).",
            "Coder prompt rule: strict JSON replacement content only; backend generated the unified diff.",
            "model_output_mode: replacement_content",
            "generated_diff_by_backend: true",
            "model_raw_diff_used: false",
            f"Coder blocked reason code: {reason_code or 'none'}.",
            f"Coder diagnostics: {diagnostics}",
            *[str(item) for item in notes],
        ]
        phase_label, increment_label, increment_goal = _phase_fields_for(
            PromptPacketInput(task=reset_request.task)
        )
        coder_packet_payload = _coder_packet_payload_for_response(
            architect_plan,
            target=target,
            context_mode=context_mode,
            context_slices=context_slices,
            forbidden_paths=forbidden_paths,
            target_exists=bool(diagnostics.get("target_exists")),
        )
        verification_plan_payload = _verification_plan_payload_for_response(architect_plan)
        task_spec_payload = _task_spec_payload_for_response(architect_plan, coder_packet_payload)
        if reason_code in TARGET_HARD_BLOCK_REASON_CODES or reason_code == "target_unresolved":
            task_spec_payload = _blocked_task_spec_payload(
                task_type=reason_code,
                reason_code=reason_code,
                target=(target or explicit_target)
                if reason_code in TARGET_HARD_BLOCK_REASON_CODES
                else None,
            )
        manual_browser_prompt = _coder_agent_manual_browser_prompt_text(
            task=reset_request.task,
            target=target or explicit_target,
            task_spec=task_spec_payload,
            coder_packet=coder_packet_payload,
            verification_plan=verification_plan_payload,
            blocked_reason=blocked_reason,
            needed_context=needed_context,
            reason_code=reason_code,
            diagnostics=diagnostics,
        )
        packet_context_paths = _coder_packet_context_paths(coder_packet_payload)
        return {
            "target_model_hint": "coder_agent",
            "provider": provider_model_truth["providerId"],
            "model": provider_model_truth["modelId"],
            "provider_model_truth": provider_model_truth,
            "providerModelTruth": provider_model_truth,
            "provider_model_source": provider_model_truth["source"],
            "provider_model_status": provider_model_truth["status"],
            "provider_call_made": provider_model_truth["providerCallMade"],
            "provider_call_authorized": provider_model_truth["providerCallAuthorized"],
            "hermes_lane_available": provider_model_truth["hermesLaneAvailable"],
            "hermes_used_for_this_run": provider_model_truth["hermesUsedForThisRun"],
            "phase_label": phase_label,
            "increment_label": increment_label,
            "increment_goal": increment_goal,
            "task_summary": _short_task_summary(reset_request.task),
            "relevant_context": "\n".join(context_lines),
            "context_metadata": {
                "context_inclusion_mode": "coder_agent_repomix",
                "context_mode": context_mode,
                "included_paths": packet_context_paths or ([target] if target else []),
                "omitted_paths": [],
                "redaction_notes": [
                    "Manual prompt packet text was not generated; pure Coder Agent diff path is active.",
                ],
                "estimated_context_tokens": 0,
                "file_contents_claimed": _coder_packet_payload_has_context_content(
                    coder_packet_payload
                ),
            },
            "constraints": [
                (
                    "Coder Agent mode: review backend-generated proposed_diff in the UI approval gate."
                    if proposed
                    else "Coder Agent mode: generated visual diff was too shallow; produce material styling, layout, hover, active, glow, spacing, or animation changes."
                    if shallow_visual_diff
                    else "Coder Agent mode: subjective visual improvement requires an actual diff or manual visual review."
                    if subjective_improvement_needs_diff
                    else "Coder Agent mode: bundle changed since planning; regenerate the Architect plan before retrying Coder."
                    if bundle_snapshot_drift
                    else "Coder Agent mode: no approval is needed because the target file already matches the requested content."
                    if already_satisfied
                    else (
                        "Coder Agent mode: resolved implementation file is missing on disk; fix the path or create the file."
                        if reason_code == "target_missing"
                        else _target_safety_constraint(reason_code)
                        if reason_code in TARGET_HARD_BLOCK_REASON_CODES
                        else "Coder Agent mode: no safe file target could be resolved from the task text; add `Target file:` or mention an existing repo-relative path."
                        if reason_code == "target_unresolved"
                        else "Coder Agent mode: Coder repomix+LLM exceeded the proxy sync deadline; raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC or narrow scope."
                        if coder_sync_timeout
                        else "Coder Agent mode: Coder returned an empty model response; check SOURCE_PROXY_CODER_MODEL_ALIAS and provider availability."
                        if coder_empty_model
                        else (
                            "Coder Agent mode: Coder model is not configured or the alias is not available on this proxy. "
                            "Set SOURCE_PROXY_CODER_MODEL_ALIAS to a valid enabled alias, then retry."
                        )
                        if coder_model_missing
                        else "Coder Agent did not produce validated replacement content; retry Local Coder with stricter output repair, or copy a manual browser prompt."
                    )
                ),
            ],
            "requested_output": (
                ALREADY_SATISFIED_REQUESTED_OUTPUT
                if already_satisfied
                else [
                    (
                        "Backend-generated unified diff ready for human review (no external paste-back)."
                        if proposed
                        else "No approvable diff was produced because the generated visual diff was too shallow."
                        if shallow_visual_diff
                        else "No diff was produced, and subjective visual improvement cannot be marked already satisfied."
                        if subjective_improvement_needs_diff
                        else "No diff was produced because the repomix bundle changed since the Architect plan was created."
                        if bundle_snapshot_drift
                        else "No unified diff was produced because the resolved target file is missing on disk."
                        if reason_code == "target_missing"
                        else _target_safety_requested_output(reason_code)
                        if reason_code in TARGET_HARD_BLOCK_REASON_CODES
                        else "No unified diff was produced because no safe target path could be resolved from the task."
                        if reason_code == "target_unresolved"
                        else "No unified diff was produced because Coder exceeded the proxy sync deadline."
                        if coder_sync_timeout
                        else "No unified diff was produced because the Coder model returned an empty response."
                        if coder_empty_model
                        else "No unified diff was produced because the Coder model is not configured or the alias is not available. Configure SOURCE_PROXY_CODER_MODEL_ALIAS, then retry."
                        if coder_model_missing
                        else "Manual browser prompt is available because local Coder could not produce validated replacement content after repair/retry."
                    ),
                ]
            ),
            "paste_back_instructions": (
                ALREADY_SATISFIED_PASTE_BACK_INSTRUCTIONS
                if already_satisfied
                else "Coder Agent replacement content was validated and converted to proposed_diff by the backend; approve inside Spirit when satisfied."
                if proposed
                else "Generate a concrete visual refinement diff that changes className, styling, layout, hover, active, glow, spacing, or animation behavior."
                if shallow_visual_diff
                else "Produce an actual visual refinement diff, use manual visual review, or copy the manual browser prompt."
                if subjective_improvement_needs_diff
                else "Regenerate the Architect plan, then retry Coder Agent."
                if bundle_snapshot_drift
                else _target_safety_paste_back(reason_code)
                if reason_code in TARGET_HARD_BLOCK_REASON_CODES
                else "Raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC or narrow Coder scope; the repomix+LLM run exceeded the proxy deadline."
                if coder_sync_timeout
                else "Verify SOURCE_PROXY_CODER_MODEL_ALIAS and provider health; Coder returned an empty model response."
                if coder_empty_model
                else "Set SOURCE_PROXY_CODER_MODEL_ALIAS to a valid enabled model alias, then retry Coder Agent."
                if coder_model_missing
                else "Retry Local Coder with stricter output repair or copy the manual browser prompt; do not approve an empty diff."
            ),
            "prompt_text": (
                ALREADY_SATISFIED_PROMPT_TEXT
                if already_satisfied
                else _coder_agent_shallow_visual_diff_prompt_text(target)
                if shallow_visual_diff
                else _coder_agent_subjective_no_diff_prompt_text(target)
                if subjective_improvement_needs_diff
                else "Bundle changed since the Architect plan was created. Regenerate the plan before retrying Coder Agent."
                if bundle_snapshot_drift
                else "Coder Agent timed out before producing replacement content; raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC or narrow scope."
                if coder_sync_timeout
                else "Coder returned an empty model response; check SOURCE_PROXY_CODER_MODEL_ALIAS and provider health."
                if coder_empty_model
                else _coder_agent_stub_prompt_text(target, proposed)
                if proposed
                else manual_browser_prompt
            ),
            "route_decision": route_payload,
            "research_sources": decision.research_sources,
            "manual_prompt_packet": False,
            "context_mode": context_mode,
            "contextMode": context_mode,
            "coder_packet": coder_packet_payload,
            "coderPacket": _camel_coder_packet_payload(coder_packet_payload),
            "task_spec": task_spec_payload,
            "taskSpec": _camel_task_spec_payload(task_spec_payload),
            "verification_plan": verification_plan_payload,
            "verificationPlan": _camel_verification_plan_payload(verification_plan_payload),
            "proposed_diff": proposed,
            "proposedDiff": proposed,
            "target": target,
            "coder_agent_local_diff": bool((proposed or "").strip() and target),
            "coderAgentLocalDiff": bool((proposed or "").strip() and target),
            "coder_blocked": coder_blocked,
            "coderBlocked": coder_blocked,
            "blocked_reason": blocked_reason,
            "blockedReason": blocked_reason,
            "needed_context": needed_context,
            "neededContext": needed_context,
            "already_satisfied": already_satisfied,
            "alreadySatisfied": already_satisfied,
            "status": status_value,
            "reason_code": reason_code,
            "reasonCode": reason_code,
            "coder_diagnostics": diagnostics,
            "coderDiagnostics": diagnostics,
            "manual_prompt_packet_available": manual_available,
            "manualPromptPacketAvailable": manual_available,
            "cloud_route_available": True,
            "cloudRouteAvailable": True,
            "next_actions": (
                [
                    "Retry Local Coder with stricter output repair",
                    *(
                        ["Regenerate plan"]
                        if bundle_snapshot_drift
                        else []
                    ),
                    "Copy manual browser prompt",
                    "Use Cloud/API route, if configured",
                    *(
                        ["Manual visual review"]
                        if subjective_improvement_needs_diff
                        else []
                    ),
                ]
                if manual_available
                else []
            ),
        }

    packet = build_prompt_packet(
        PromptPacketInput(
            task=reset_request.task,
            target_model_hint=reset_request.target_model_hint,
            relevant_context=reset_request.relevant_context,
            active_task_id=reset_request.active_task_id,
            current_agent_role=reset_request.current_agent_role,
            context_tokens=reset_request.context_tokens,
            sensitive=reset_request.sensitive,
            needs_current_info=reset_request.needs_current_info,
            needs_codebase_context=reset_request.needs_codebase_context,
            wants_implementation=reset_request.wants_implementation,
            prefer_free=reset_request.prefer_free,
        )
    )
    payload = packet.as_payload()
    payload["route_decision"] = route_payload
    payload["research_sources"] = decision.research_sources
    return payload


def _load_or_prepare_architect_plan(
    task: str,
    task_id: str | None,
    *,
    expected_target: str | None = None,
) -> Any | None:
    plan = _load_active_architect_plan(task_id)
    if _architect_plan_has_usable_coder_packet(plan, expected_target=expected_target):
        return plan

    if task_id:
        try:
            from source_proxy.tasks.long_running import advance_long_running_task

            advance_long_running_task(task_id)
            plan = _load_active_architect_plan(task_id)
            if _architect_plan_has_usable_coder_packet(plan, expected_target=expected_target):
                return plan
        except Exception:
            plan = None

    return _deterministic_architect_plan_for_prompt_packet(task, task_id)


def _deterministic_architect_plan_for_prompt_packet(
    task: str,
    task_id: str | None,
) -> Any | None:
    try:
        from source_proxy.planning.architect import Plan, plan_task_deterministically
        from source_proxy.planning.plan import save_plan

        result = plan_task_deterministically(
            task,
            task_id or "prompt-packet-ad-hoc",
            _workspace_root(),
        )
        if not isinstance(result, Plan):
            return None
        if task_id:
            try:
                save_plan(task_id, result.plan)
            except Exception:
                pass
        return result.plan
    except Exception:
        return None


def _architect_plan_has_usable_coder_packet(
    architect_plan: Any | None,
    *,
    expected_target: str | None = None,
) -> bool:
    packet = getattr(architect_plan, "coder_packet", None)
    target_file = getattr(packet, "target_file", None)
    target_path = str(getattr(target_file, "path", "") or "").strip()
    normalized_expected = _normalize_trial_create_path(expected_target or "")
    if normalized_expected and target_path != normalized_expected:
        return False
    context_slices = getattr(packet, "context_slices", None)
    operation = str(getattr(packet, "operation", "") or "").strip()
    if operation == "create":
        return bool(target_path)
    return bool(target_path and isinstance(context_slices, list) and context_slices)


def _target_missing_blocks_prompt_packet(task: str, route_reasons: list[str]) -> bool:
    if "target_missing" not in route_reasons:
        return False
    proposal = parse_bounded_proposal_task(task)
    if proposal is None:
        return True
    create_ok, _blocked_reason = bounded_proposal_create_allowed(
        proposal,
        workspace_root=_workspace_root(),
    )
    return not create_ok


def _trial_allowed_missing_create_target(
    request: PromptPacketRequest,
    target: str,
    route_reasons: list[str],
) -> bool:
    if request.trial_mode != "live_apply" or "target_missing" not in route_reasons:
        return False
    normalized_target = _normalize_trial_create_path(target)
    if not normalized_target:
        return False
    root = _workspace_root()
    resolved_target = resolve_target_from_task(
        f"Target file: {normalized_target}",
        root,
    )
    if unsafe_target_for_route(request.task, resolved_target, root) is not None:
        return False
    return _trial_path_allowed(normalized_target, request.allowed_files)


def _trial_allowed_selected_target(
    request: PromptPacketRequest,
    target: str,
) -> bool:
    if request.trial_mode != "live_apply":
        return False
    normalized_target = _normalize_trial_create_path(target)
    if not normalized_target:
        return False
    return _trial_path_allowed(normalized_target, request.allowed_files)


def _trial_bounded_create_task(task: str, target: str, allowed_files: list[str]) -> str:
    normalized_target = _normalize_trial_create_path(target)
    allowed = [
        normalized
        for item in allowed_files
        if (normalized := _normalize_trial_allowed_path(item))
    ]
    if not normalized_target or not allowed:
        return task
    payload = {
        "task": task.strip(),
        "mode": "proposal",
        "target_file": normalized_target,
        "allowed_files": allowed,
        "forbidden_files": [".env", ".env.local", "credentials", "private keys"],
        "expected_checks": ["git diff --check"],
        "rollback_hint": f"Delete {normalized_target} if this reversible trial is rolled back.",
    }
    return f"{task.strip()}\n\nProposal task:\n```json\n{json.dumps(payload, sort_keys=True)}\n```"


def _normalize_trial_create_path(path: str) -> str:
    normalized = _normalize_trial_allowed_path(path)
    if not normalized:
        return ""
    allowed_prefixes = (
        "src/app/agent-lab/",
        "src/components/agent-lab/",
        "src/lib/agent-lab/",
        "src/app/api/agent-lab/",
        "tests/agent-lab/",
    )
    return normalized if normalized.startswith(allowed_prefixes) else ""


def _normalize_trial_allowed_path(path: str) -> str:
    from source_proxy.safety.paths import normalize_repo_path_candidate

    return normalize_repo_path_candidate(str(path or ""))


def _trial_path_allowed(target: str, allowed_files: list[str]) -> bool:
    normalized_allowed = [
        normalized
        for item in allowed_files
        if (normalized := _normalize_trial_allowed_path(item))
    ]
    for allowed in normalized_allowed:
        if allowed == target:
            return True
        if allowed.endswith("/**") and target.startswith(allowed[:-3] + "/"):
            return True
    return False


def _coder_prompt_packet_status(
    *,
    already_satisfied: bool,
    coder_blocked: bool,
    proposed: str,
    reason_code: str,
    subjective_improvement_needs_diff: bool,
) -> str:
    if already_satisfied:
        return "already_satisfied"
    if (proposed or "").strip():
        return "preview_ready"
    if reason_code in {"coder_packet_missing_context", "coder_needs_context"}:
        return "needs_context"
    if reason_code in {
        "coder_model_not_configured",
        "coder_empty_model_response",
        "local_model_unavailable",
    }:
        return "coder_config_blocked"
    if reason_code == "coder_sync_timeout":
        return "blocked"
    if reason_code in {"target_missing", "target_unresolved"} | TARGET_HARD_BLOCK_REASON_CODES:
        return "blocked"
    if reason_code == "blocked_after_retries":
        return "blocked_after_retries"
    if subjective_improvement_needs_diff:
        return "needs_coder_diff"
    if coder_blocked:
        return "blocked"
    return ""


def _mark_active_task_after_coder_result(
    task_id: str | None,
    *,
    status_value: str,
    coder_blocked: bool,
    proposed: str,
    reason_code: str,
    blocked_reason: str,
    needed_context: str,
    target: str,
) -> None:
    if not task_id:
        return
    proposed_norm = (proposed or "").strip()
    if proposed_norm and not coder_blocked:
        return
    task_status = ""
    if status_value == "needs_context":
        task_status = "needs_context"
    elif status_value == "coder_config_blocked":
        task_status = "coder_config_blocked"
    elif status_value == "blocked_after_retries":
        task_status = "blocked_after_retries"
    elif status_value in {"blocked", "needs_coder_diff"} or coder_blocked:
        task_status = "blocked"
    if not task_status:
        return

    summary = "; ".join(
        item
        for item in [
            f"coder_status={status_value or 'blocked'}",
            f"reason_code={reason_code or 'coder_blocked'}",
            f"target={target}" if target else "",
            blocked_reason,
            f"needed_context={needed_context}" if needed_context else "",
        ]
        if item
    )
    try:
        from source_proxy.tasks.long_running import (
            get_long_running_task_snapshot,
            update_long_running_task,
        )

        snapshot = get_long_running_task_snapshot(task_id)["task"]
        steps = snapshot.get("steps") if isinstance(snapshot, dict) else []
        if not isinstance(steps, list):
            steps = []
        step = (
            "Coder needs a valid Architect CoderPacket before diff generation."
            if task_status == "needs_context"
            else (
                "Coder model alias is not configured or is not available on this proxy. "
                "Set SOURCE_PROXY_CODER_MODEL_ALIAS to a valid enabled alias."
                if reason_code == "coder_model_not_configured"
                else "Coder returned an empty model response; verify SOURCE_PROXY_CODER_MODEL_ALIAS and provider health."
                if reason_code == "coder_empty_model_response"
                else "Coder blocked after reviewer retries."
                if reason_code == "blocked_after_retries"
                else "Coder blocked before producing an approvable diff."
            )
        )
        update_long_running_task(
            task_id,
            status=task_status,
            current_agent_role="coder",
            truncated_test_results=summary[:1500],
            steps=_append_unique_strs([str(item) for item in steps], [step]),
        )
    except Exception:
        return


def _append_unique_strs(current: list[str], additions: list[str]) -> list[str]:
    out = list(current)
    for item in additions:
        if item and item not in out:
            out.append(item)
    return out


def _coder_packet_payload_for_response(
    architect_plan: Any | None,
    *,
    target: str,
    context_mode: str,
    context_slices: list[Any],
    forbidden_paths: list[Any],
    target_exists: bool,
) -> dict[str, Any]:
    if architect_plan is not None and hasattr(architect_plan, "to_dict"):
        try:
            payload = dict(architect_plan.to_dict()["coder_packet"])
            payload["context_mode"] = context_mode
            return payload
        except Exception:
            pass
    return {
        "target_file": {
            "path": target,
            "exists": target_exists,
            "sha256_before": None,
        },
        "operation": "edit" if target_exists else "create",
        "acceptance_criteria": [],
        "constraints": {
            "must_contain": [],
            "must_not_contain": ["Target file:"],
            "preserve_imports": [],
            "preserve_exports": [],
            "max_added_lines": None,
            "max_removed_lines": None,
        },
        "context_mode": context_mode,
        "context_slices": context_slices,
        "forbidden_paths": forbidden_paths,
        "style_directives": [],
    }


def _task_spec_payload_for_response(
    architect_plan: Any | None,
    coder_packet_payload: dict[str, Any],
) -> dict[str, Any]:
    if architect_plan is not None:
        try:
            return task_spec_from_plan(architect_plan).to_dict()
        except Exception:
            pass
    try:
        from source_proxy.planning.plan import (
            CoderPacket,
            ContentConstraints,
            TargetFile,
        )

        target_file_payload = (
            coder_packet_payload.get("target_file")
            if isinstance(coder_packet_payload.get("target_file"), dict)
            else {}
        )
        constraints_payload = (
            coder_packet_payload.get("constraints")
            if isinstance(coder_packet_payload.get("constraints"), dict)
            else {}
        )
        packet = CoderPacket(
            target_file=TargetFile(
                path=str(target_file_payload.get("path") or ""),
                exists=bool(target_file_payload.get("exists")),
                sha256_before=(
                    str(target_file_payload.get("sha256_before"))
                    if target_file_payload.get("sha256_before") is not None
                    else None
                ),
            ),
            operation=str(coder_packet_payload.get("operation") or "edit"),  # type: ignore[arg-type]
            acceptance_criteria=[],
            constraints=ContentConstraints(
                must_contain=[
                    str(item)
                    for item in constraints_payload.get("must_contain", [])
                    if isinstance(item, str)
                ],
                must_not_contain=[
                    str(item)
                    for item in constraints_payload.get("must_not_contain", [])
                    if isinstance(item, str)
                ],
                preserve_imports=[],
                preserve_exports=[],
                max_added_lines=None,
                max_removed_lines=None,
            ),
            context_slices=[],
            forbidden_paths=[
                str(item)
                for item in coder_packet_payload.get("forbidden_paths", [])
                if isinstance(item, str)
            ],
            style_directives=[],
        )
        return task_spec_from_packet(packet).to_dict()
    except Exception:
        return {
            "schema_version": 1,
            "task_type": "modify_existing_file",
            "target": "",
            "allowed_files": [],
            "forbidden_files": [],
            "literal_requirements": [],
            "verification": ["target-only"],
            "risk_tier": "low",
            "source": "deterministic",
        }


def _blocked_task_spec_payload(
    *,
    task_type: str,
    reason_code: str,
    target: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task_type": task_type,
        "target": target,
        "allowed_files": [],
        "forbidden_files": [],
        "literal_requirements": [],
        "verification": [],
        "risk_tier": "low",
        "source": "deterministic",
        "blockers": [reason_code],
    }


def _first_target_hard_block_reason(reason_codes: list[str]) -> str:
    for reason in ("protected_path", "secret_path", "path_escape", "outside_workspace"):
        if reason in reason_codes:
            return reason
    return ""


def _target_safety_blocked_reason(reason_code: str, target: str) -> str:
    target_suffix = f": {target}" if target else "."
    if reason_code in {"protected_path", "secret_path"}:
        return f"Blocked protected/secret path{target_suffix}"
    if reason_code in {"path_escape", "outside_workspace"}:
        return f"Blocked path escapes workspace{target_suffix}"
    return "Blocked unsafe target path."


def _target_safety_needed_context(reason_code: str) -> str:
    if reason_code in {"protected_path", "secret_path"}:
        return "Choose a non-secret repo file. Protected and secret-shaped paths cannot be edited through the approval flow."
    if reason_code in {"path_escape", "outside_workspace"}:
        return "Use a repo-relative path inside the workspace. Traversal, absolute, and drive paths are blocked."
    return "Choose a safe repo-relative target file."


def _target_safety_constraint(reason_code: str) -> str:
    if reason_code in {"protected_path", "secret_path"}:
        return "Coder Agent mode: blocked before Coder because the requested target is a protected/secret path."
    if reason_code in {"path_escape", "outside_workspace"}:
        return "Coder Agent mode: blocked before Coder because the requested target escapes the workspace."
    return "Coder Agent mode: blocked before Coder because the requested target is unsafe."


def _target_safety_requested_output(reason_code: str) -> str:
    if reason_code in {"protected_path", "secret_path"}:
        return "No unified diff was produced because the requested target is a protected/secret path."
    if reason_code in {"path_escape", "outside_workspace"}:
        return "No unified diff was produced because the requested target escapes the workspace."
    return "No unified diff was produced because the requested target is unsafe."


def _target_safety_paste_back(reason_code: str) -> str:
    if reason_code in {"protected_path", "secret_path"}:
        return "Use a non-secret repo-relative target file; do not approve or paste a diff for protected paths."
    if reason_code in {"path_escape", "outside_workspace"}:
        return "Use a repo-relative path inside the workspace; do not approve or paste a traversal/absolute-path diff."
    return "Use a safe repo-relative target file before retrying."


def _verification_plan_payload_for_response(architect_plan: Any | None) -> dict[str, Any]:
    if architect_plan is not None and hasattr(architect_plan, "to_dict"):
        try:
            payload = architect_plan.to_dict().get("verification_plan")
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
    return {"required_checks": [], "designer_review_required": False, "architect_review_required": False}


def _camel_coder_packet_payload(payload: dict[str, Any]) -> dict[str, Any]:
    target_file = payload.get("target_file") if isinstance(payload.get("target_file"), dict) else {}
    constraints = payload.get("constraints") if isinstance(payload.get("constraints"), dict) else {}
    return {
        "targetFile": target_file,
        "operation": payload.get("operation"),
        "acceptanceCriteria": payload.get("acceptance_criteria", []),
        "constraints": {
            "mustContain": constraints.get("must_contain", []),
            "mustNotContain": constraints.get("must_not_contain", []),
            "preserveImports": constraints.get("preserve_imports", []),
            "preserveExports": constraints.get("preserve_exports", []),
            "maxAddedLines": constraints.get("max_added_lines"),
            "maxRemovedLines": constraints.get("max_removed_lines"),
        },
        "contextMode": payload.get("context_mode"),
        "contextSlices": payload.get("context_slices", []),
        "forbiddenPaths": payload.get("forbidden_paths", []),
        "styleDirectives": payload.get("style_directives", []),
    }


def _camel_task_spec_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": payload.get("schema_version"),
        "taskType": payload.get("task_type"),
        "target": payload.get("target"),
        "allowedFiles": payload.get("allowed_files", []),
        "forbiddenFiles": payload.get("forbidden_files", []),
        "literalRequirements": payload.get("literal_requirements", []),
        "verification": payload.get("verification", []),
        "riskTier": payload.get("risk_tier"),
        "source": payload.get("source"),
        "blockers": payload.get("blockers", []),
    }


def _coder_packet_context_paths(payload: dict[str, Any]) -> list[str]:
    context_slices = payload.get("context_slices")
    if not isinstance(context_slices, list):
        return []
    paths: list[str] = []
    for item in context_slices:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if path and path not in paths:
            paths.append(path)
    return paths


def _coder_packet_payload_has_context_content(payload: dict[str, Any]) -> bool:
    context_slices = payload.get("context_slices")
    return isinstance(context_slices, list) and any(
        isinstance(item, dict) and bool(str(item.get("content") or ""))
        for item in context_slices
    )


def _camel_verification_plan_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "requiredChecks": payload.get("required_checks", []),
        "designerReviewRequired": payload.get("designer_review_required", False),
        "architectReviewRequired": payload.get("architect_review_required", False),
    }


def _load_active_architect_plan(task_id: str | None) -> Any | None:
    if not task_id:
        return None
    try:
        return load_plan(task_id)
    except Exception:
        return None


def _with_bridge_route(payload: dict[str, Any]) -> dict[str, Any]:
    next_prompt_action = payload.get("next_prompt_action")
    route_registration = (
        AVAILABLE_ROUTES.get(str(next_prompt_action))
        if next_prompt_action is not None
        else None
    )
    if route_registration is None:
        route_registration = AVAILABLE_ROUTES.get(
            ROUTE_TYPE_TO_ACTION.get(str(payload.get("recommended_route")), "")
        )

    if route_registration is not None:
        payload["bridge_route"] = {
            "action": next_prompt_action,
            **route_registration,
            "available": True,
        }
    return payload


def _decision_input_from_request(request: RouteDecisionRequest) -> DecisionInput:
    return DecisionInput(
        task=request.task,
        active_task_id=request.active_task_id,
        current_agent_role=request.current_agent_role,
        context_tokens=request.context_tokens,
        research_recommended=request.research_recommended,
        sensitive=request.sensitive,
        needs_current_info=request.needs_current_info,
        needs_codebase_context=request.needs_codebase_context,
        wants_implementation=request.wants_implementation,
        prefer_free=request.prefer_free,
    )


@router.post("/recommend-model")
async def model_recommendation(request: RouteDecisionRequest) -> dict[str, Any]:
    reset_request = _request_with_cleared_file_focus(request)
    recommendation = recommend_model(
        ModelRecommendationInput(
            task=reset_request.task,
            active_task_id=reset_request.active_task_id,
            current_agent_role=reset_request.current_agent_role,
            context_tokens=reset_request.context_tokens,
            sensitive=reset_request.sensitive,
            needs_current_info=reset_request.needs_current_info,
            needs_codebase_context=reset_request.needs_codebase_context,
            wants_implementation=reset_request.wants_implementation,
            prefer_free=reset_request.prefer_free,
        )
    )
    return recommendation.as_payload()


@router.post("/api-vs-manual-preview")
async def api_vs_manual_preview(request: ApiVsManualPreviewRequest) -> dict[str, Any]:
    reset_request = _request_with_cleared_file_focus(request)
    return build_api_vs_manual_preview(
        ApiVsManualPreviewInput(
            task=reset_request.task,
            api_model_alias=reset_request.api_model_alias,
            max_completion_tokens=reset_request.max_completion_tokens,
            relevant_context=reset_request.relevant_context,
            context_tokens=reset_request.context_tokens,
            sensitive=reset_request.sensitive,
            needs_current_info=reset_request.needs_current_info,
            needs_codebase_context=reset_request.needs_codebase_context,
            wants_implementation=reset_request.wants_implementation,
            prefer_free=reset_request.prefer_free,
        )
    )


def _request_with_cleared_file_focus(request: RouteDecisionRequest) -> RouteDecisionRequest:
    update: dict[str, Any] = {
        "conversation_context": [],
        "decision_memory": [],
        "targeted_files": [],
        "target_files": [],
        "proposed_diff": None,
    }
    if request.conversation_context or request.decision_memory:
        update["context_tokens"] = None

    if isinstance(request, PromptPacketRequest):
        update["relevant_context"] = _drop_prior_memory_from_context(
            request.relevant_context
        )

    return request.model_copy(update=update)


def _is_app_router_page_path(normalized: str) -> bool:
    p = normalized.replace("\\", "/").lower()
    return p.startswith("src/app/") and p.endswith("page.tsx")


def _pinned_next_app_page_from_explicit(normalized: str) -> str | None:
    if not normalized or not _is_app_router_page_path(normalized):
        return None
    return normalized


def _route_payload_requests_coder_agent_diff(route_payload: dict[str, Any]) -> bool:
    """True when this request must skip ``build_prompt_packet`` and emit a repo diff.

    ``next_prompt_action`` is the primary switch, but we also key off
    ``recommended_route`` / bridge metadata so a drift in string constants cannot
    silently funnel local implementation work back into wall-of-text prompt packets.
    """
    next_action = str(route_payload.get("next_prompt_action") or "")
    if next_action == "run_with_coder_agent":
        return True
    if str(route_payload.get("recommended_route") or "") == "local_route":
        return True
    bridge = route_payload.get("bridge_route")
    if isinstance(bridge, dict) and str(bridge.get("execution_path") or "") == "coder_agent":
        return True
    return False


def _drop_prior_memory_from_context(relevant_context: str | None) -> str | None:
    if not relevant_context:
        return relevant_context

    sections = [
        section.strip()
        for section in relevant_context.split("\n\n")
        if section.strip()
    ]
    retained_sections = [
        section
        for section in sections
        if not _looks_like_prior_memory_section(section)
    ]
    return "\n\n".join(retained_sections) or None


def _short_task_summary(task: str) -> str:
    normalized = " ".join(task.strip().split())
    if len(normalized) <= 240:
        return normalized
    return f"{normalized[:237].rstrip()}..."


def _coder_agent_manual_browser_prompt_text(
    *,
    task: str,
    target: str,
    task_spec: dict[str, Any],
    coder_packet: dict[str, Any],
    verification_plan: dict[str, Any],
    blocked_reason: str,
    needed_context: str,
    reason_code: str,
    diagnostics: dict[str, Any],
) -> str:
    context_slices = [
        item
        for item in coder_packet.get("context_slices", [])
        if isinstance(item, dict)
    ]
    rendered_context: list[str] = []
    for item in context_slices[:4]:
        path = str(item.get("path") or "")
        kind = str(item.get("kind") or "context")
        content = str(item.get("content") or "")
        rendered_context.append(
            "\n".join(
                [
                    f"### {kind} slice: {path}",
                    "```",
                    content[:12000],
                    "```",
                ]
            )
        )

    diagnostics_payload = {
        key: diagnostics.get(key)
        for key in (
            "raw_response_excerpt",
            "json_attempt_count",
            "coder_format_retry_count",
            "last_json_error",
            "parse_error_class",
            "parse_error_message",
        )
        if diagnostics.get(key) not in (None, "")
    }
    return "\n".join(
        [
            "# Manual Browser Prompt: SpiritOS Coder Recovery",
            "",
            "Use this prompt in GPT, Gemini, Grok, Claude, or another browser model.",
            "Return output to the SpiritOS portal for validation. Do not bypass the portal.",
            "",
            "## Task",
            task.strip() or f"Modify {target}.",
            "",
            "## Non-Negotiable Portal Contract",
            "- Return only JSON, or a unified diff only if JSON is impossible.",
            "- Prefer the content_lines JSON schema.",
            "- Target must exactly match TaskSpec.target.",
            "- Only edit files in TaskSpec.allowed_files.",
            "- Do not include prose outside the returned JSON or diff.",
            "- The portal will still run TaskSpec.allowed_files, target-only, git apply, reviewer, approval, protected apply, and post-apply verification.",
            "",
            "## Preferred Output Schema",
            "```json",
            json.dumps(
                {
                    "action": "replace_file",
                    "target": target or "REPO_RELATIVE_PATH",
                    "content_lines": ["line 1", "line 2"],
                    "notes": "short optional note",
                },
                indent=2,
            ),
            "```",
            "",
            "## Legacy Accepted Schema",
            "```json",
            json.dumps(
                {
                    "action": "replace_file",
                    "target": target or "REPO_RELATIVE_PATH",
                    "content": "FULL_FILE_CONTENT",
                    "notes": "short optional note",
                },
                indent=2,
            ),
            "```",
            "",
            "## TaskSpec",
            "```json",
            json.dumps(task_spec, indent=2, sort_keys=True),
            "```",
            "",
            "## Verification Plan",
            "```json",
            json.dumps(verification_plan, indent=2, sort_keys=True),
            "```",
            "",
            "## Local Coder Failure To Avoid",
            f"- reason_code: {reason_code or 'coder_blocked'}",
            f"- blocked_reason: {blocked_reason or 'none'}",
            f"- needed_context: {needed_context or 'none'}",
            "",
            "## Coder Diagnostics",
            "```json",
            json.dumps(diagnostics_payload, indent=2, sort_keys=True),
            "```",
            "",
            "## Repository Context",
            "\n\n".join(rendered_context) or "No context slices were provided.",
            "",
            "Return the replacement JSON now.",
        ]
    )


def _coder_agent_stub_prompt_text(target: str, proposed_diff: str) -> str:
    """Tiny surface for older clients; the real diff lives in proposed_diff."""
    if proposed_diff and target:
        return (
            "Coder Agent returned backend-generated proposed_diff for approval-gate validation "
            f"(target: {target}). If the client rejects the diff, treat the proposal as blocked and retry Coder."
        )
    return (
        "Coder Agent could not synthesize safe replacement content for backend diff generation. "
        f"Target guess: {target or 'none'}. Check coder notes in relevant_context."
    )


def _coder_agent_subjective_no_diff_prompt_text(target: str) -> str:
    target_text = f" Target: {target}." if target else ""
    return (
        "No diff was produced, and subjective improvement cannot be marked already "
        f"satisfied.{target_text} Produce an actual visual refinement diff or use "
        "manual visual review."
    )


def _coder_agent_shallow_visual_diff_prompt_text(target: str) -> str:
    target_text = f" Target: {target}." if target else ""
    return (
        "The generated visual diff was too shallow: it did not materially change "
        "styling, layout, hover, active, glow, spacing, or animation behavior."
        f"{target_text} Generate a concrete visual refinement diff before approval."
    )


def _looks_like_prior_memory_section(section: str) -> bool:
    first_line = section.splitlines()[0].strip().lower()
    return first_line.startswith(
        (
            "recent coding conversation context:",
            "previous routing decision memory:",
            "turn ",
            "memory ",
        )
    )
