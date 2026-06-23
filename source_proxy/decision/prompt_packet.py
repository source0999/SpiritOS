from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from source_proxy.context.obsidian import obsidian_context_diagnostics
from source_proxy.decision.packet_decomposition import build_decomposition_from_brain_switch
from source_proxy.decision.router import DecisionInput, RouteDecision, decide_route

TargetModelHint = Literal["chatgpt", "claude", "gemini", "google_ai_studio", "grok"]

CURRENT_PHASE_LABEL = "Phase 7C"
CURRENT_INCREMENT_LABEL = "Increment 7C.4"
CURRENT_INCREMENT_GOAL = (
    "Add stronger self-correction: check if the agent is being passive, "
    "confirm repo-first research ran, and confirm the active phase."
)
UNSCOPED_PHASE_LABEL = "Current task"
UNSCOPED_INCREMENT_LABEL = "No inherited increment"
UNSCOPED_INCREMENT_GOAL = "Use only the current user request; do not inherit phase state from prior runs."

PROXY_AGENT_CONTEXT = (
    "Coder Agent route selected. Read the repomix repository context and produce strict JSON replacement content only. "
    "The backend generates the unified diff after validation; do not ask the model to write patch hunks."
)

ALREADY_SATISFIED_PROMPT_TEXT = (
    "The target file already satisfies the requested task. No diff is needed."
)
ALREADY_SATISFIED_REQUESTED_OUTPUT = [
    "No approval needed. Target file already matches requested content."
]
ALREADY_SATISFIED_PASTE_BACK_INSTRUCTIONS = (
    "No code change was produced because the target is already up to date."
)


@dataclass(frozen=True)
class PromptPacketInput:
    task: str
    target_model_hint: TargetModelHint | None = None
    relevant_context: str | None = None
    active_task_id: str | None = None
    current_agent_role: str | None = None
    context_tokens: int | None = None
    sensitive: bool = False
    needs_current_info: bool = False
    needs_codebase_context: bool = False
    wants_implementation: bool = False
    prefer_free: bool = True
    brain_switch_recommendation: str | None = None
    task_shape: str | None = None
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromptPacket:
    target_model_hint: str
    phase_label: str
    increment_label: str
    increment_goal: str
    task_summary: str
    relevant_context: str
    context_metadata: dict[str, object]
    constraints: list[str]
    requested_output: list[str]
    paste_back_instructions: str
    prompt_text: str
    route_decision: RouteDecision
    research_sources: list[dict[str, str]] = field(default_factory=list)
    local_decomposition: dict[str, object] | None = None

    def as_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "target_model_hint": self.target_model_hint,
            "phase_label": self.phase_label,
            "increment_label": self.increment_label,
            "increment_goal": self.increment_goal,
            "task_summary": self.task_summary,
            "relevant_context": self.relevant_context,
            "context_metadata": self.context_metadata,
            "constraints": self.constraints,
            "requested_output": self.requested_output,
            "paste_back_instructions": self.paste_back_instructions,
            "prompt_text": self.prompt_text,
            "route_decision": self.route_decision.as_payload(),
            "research_sources": self.research_sources,
        }
        if self.local_decomposition is not None:
            payload["local_decomposition"] = self.local_decomposition
        return payload


def build_prompt_packet(input_data: PromptPacketInput) -> PromptPacket:
    decision_input = DecisionInput(
        task=input_data.task,
        active_task_id=input_data.active_task_id,
        current_agent_role=input_data.current_agent_role,
        context_tokens=input_data.context_tokens,
        sensitive=input_data.sensitive,
        needs_current_info=input_data.needs_current_info,
        needs_codebase_context=input_data.needs_codebase_context,
        wants_implementation=input_data.wants_implementation,
        prefer_free=input_data.prefer_free,
    )
    decision = decide_route(decision_input)
    target_model = input_data.target_model_hint or _default_model_for_decision(decision)
    task_summary = _summarize_task(input_data.task)
    phase_label, increment_label, increment_goal = _phase_fields_for(input_data)
    relevant_context = _build_context_section(input_data)
    context_metadata = _context_metadata_for(input_data, relevant_context)
    local_decomposition = _local_decomposition_for(input_data)
    if local_decomposition is not None:
        context_metadata["local_decomposition_status"] = local_decomposition["validation_status"]
        context_metadata["local_decomposition_family"] = local_decomposition["decomposition_family"]
    constraints = _constraints_for(input_data, decision)
    requested_output = _requested_output_for(input_data, decision)
    paste_back_instructions = (
        "Paste the model answer back into Source. Source will summarize, compare, "
        "and convert the useful parts into a Codex-ready follow-up."
    )
    prompt_text = _render_prompt_text(
        target_model_hint=target_model,
        phase_label=phase_label,
        increment_label=increment_label,
        increment_goal=increment_goal,
        task_summary=task_summary,
        relevant_context=relevant_context,
        constraints=constraints,
        requested_output=requested_output,
        paste_back_instructions=paste_back_instructions,
    )

    return PromptPacket(
        target_model_hint=target_model,
        phase_label=phase_label,
        increment_label=increment_label,
        increment_goal=increment_goal,
        task_summary=task_summary,
        relevant_context=relevant_context,
        context_metadata=context_metadata,
        constraints=constraints,
        requested_output=requested_output,
        paste_back_instructions=paste_back_instructions,
        prompt_text=prompt_text,
        route_decision=decision,
        local_decomposition=local_decomposition,
    )


def _local_decomposition_for(input_data: PromptPacketInput) -> dict[str, object] | None:
    if input_data.brain_switch_recommendation != "LOCAL_DECOMPOSITION_RECOMMENDED":
        return None
    decomposition = build_decomposition_from_brain_switch(
        input_data.brain_switch_recommendation,
        input_data.task,
        task_shape=input_data.task_shape,
        evidence_ids=input_data.evidence_ids,
    )
    return decomposition.to_dict() if decomposition else None


def _default_model_for_decision(decision: RouteDecision) -> str:
    if decision.task_classification == "codebase_analysis":
        return "claude"
    if decision.task_classification == "current_research":
        return "gemini"
    if decision.task_classification == "implementation":
        return "chatgpt"
    return "chatgpt"


def _summarize_task(task: str) -> str:
    normalized = " ".join(task.strip().split())
    if len(normalized) <= 240:
        return normalized
    return f"{normalized[:237].rstrip()}..."


def _task_mentions_current_phase(input_data: PromptPacketInput) -> bool:
    combined = f"{input_data.task}\n{input_data.relevant_context or ''}".lower()
    return "phase 7c" in combined or "increment 7c" in combined or "7c.4" in combined


def _phase_fields_for(input_data: PromptPacketInput) -> tuple[str, str, str]:
    if _task_mentions_current_phase(input_data):
        return CURRENT_PHASE_LABEL, CURRENT_INCREMENT_LABEL, CURRENT_INCREMENT_GOAL
    return UNSCOPED_PHASE_LABEL, UNSCOPED_INCREMENT_LABEL, UNSCOPED_INCREMENT_GOAL


def _active_phase_context(input_data: PromptPacketInput) -> str:
    if not _task_mentions_current_phase(input_data):
        return ""
    return (
        f"Active work: {CURRENT_PHASE_LABEL} / {CURRENT_INCREMENT_LABEL}. "
        f"Goal: {CURRENT_INCREMENT_GOAL}"
    )


def _build_context_section(input_data: PromptPacketInput) -> str:
    phase_context = _active_phase_context(input_data)
    context = (input_data.relevant_context or "").strip()
    if context:
        if input_data.wants_implementation or input_data.needs_codebase_context:
            return (
                f"{phase_context}\n\n{PROXY_AGENT_CONTEXT}\n\n{context}"
                if phase_context
                else f"{PROXY_AGENT_CONTEXT}\n\n{context}"
            )
        return f"{phase_context}\n\n{context}" if phase_context else context

    if input_data.wants_implementation:
        return f"{phase_context}\n\n{PROXY_AGENT_CONTEXT}" if phase_context else PROXY_AGENT_CONTEXT

    if input_data.needs_codebase_context:
        ask_for_context = (
            f"{PROXY_AGENT_CONTEXT} If context is missing, ask for the specific files or compressed XML excerpt needed."
        )
        return f"{phase_context}\n\n{ask_for_context}" if phase_context else ask_for_context

    return (
        f"{phase_context}\n\nNo additional repository context was supplied."
        if phase_context
        else "No additional repository context was supplied."
    )


def _context_metadata_for(
    input_data: PromptPacketInput,
    relevant_context: str,
) -> dict[str, object]:
    context = (input_data.relevant_context or "").strip()
    if not context:
        mode = "none"
        included_paths: list[str] = []
        redaction_notes = ["No supplied context; prompt asks external model to request missing files."]
    elif _looks_like_path_listing(context):
        mode = "path_listing_only"
        included_paths = _extract_candidate_paths(context)
        redaction_notes = [
            "Only path/listing context was supplied; no file contents are implied.",
            *_secret_shape_notes(context),
        ]
    elif _looks_like_generated_bundle_reference(context):
        mode = "generated_bundle_reference"
        included_paths = _extract_candidate_paths(context)
        redaction_notes = [
            "Generated bundle reference supplied; metadata does not prove contents were read.",
            *_secret_shape_notes(context),
        ]
    else:
        mode = "supplied_excerpt"
        included_paths = _extract_candidate_paths(context)
        redaction_notes = [
            "User-supplied excerpt included as context.",
            *_secret_shape_notes(context),
        ]

    omitted_paths = _omitted_secret_shaped_paths(context)
    return {
        "context_inclusion_mode": mode,
        "included_paths": included_paths,
        "omitted_paths": omitted_paths,
        "redaction_notes": redaction_notes,
        "estimated_context_tokens": _estimate_tokens(relevant_context),
        "file_contents_claimed": mode == "supplied_excerpt",
        "memory_context_diagnostics": obsidian_context_diagnostics(),
    }


def _constraints_for(
    input_data: PromptPacketInput,
    decision: RouteDecision,
) -> list[str]:
    constraints = [
        "Do not invent file contents, test results, URLs, logs, or tool output.",
        "Separate facts from assumptions.",
        "Do not inherit target files, diffs, routes, phase labels, or approval state from previous runs.",
        "Before acting, answer: Am I being passive? Did I scan the repo first? Am I on the correct phase?",
        "Use simple, direct language.",
        "Keep recommendations actionable and scoped to the task.",
    ]
    if _task_mentions_current_phase(input_data):
        constraints.insert(2, f"Name {CURRENT_PHASE_LABEL} / {CURRENT_INCREMENT_LABEL} in the answer.")
    if input_data.sensitive or decision.risk_tier == "high":
        constraints.append("Treat secrets and private data as sensitive; do not echo credentials.")
    if input_data.needs_codebase_context:
        constraints.append("When referencing code, cite file paths and ask for missing files instead of guessing.")
    if input_data.wants_implementation:
        constraints.append("Prefer running the local Coder Agent implementation path before generating a manual browser prompt.")
        constraints.append("Coder Agent output must be strict JSON replacement content only; backend generates the unified diff.")
        constraints.append("Prefer minimal, reviewable code changes over broad rewrites.")
        constraints.append("When possible, show concrete file paths and the exact code changes to make.")
    if input_data.needs_current_info:
        constraints.append("Use current browsing/research if available and cite sources.")
    return constraints


def _requested_output_for(
    input_data: PromptPacketInput,
    decision: RouteDecision,
) -> list[str]:
    if input_data.wants_implementation:
        return [
            "A short summary scoped only to the current task",
            "Specific files or modules likely involved",
            "Concrete code changes or diff-style bullets when possible",
            "Risks, edge cases, and tests to run",
            "A final Coder-Agent-ready instruction block",
        ]
    if decision.task_classification == "codebase_analysis":
        return [
            "A short summary scoped only to the current task",
            "Top findings ordered by importance",
            "Evidence or file-path references for each finding",
            "Open questions or missing context",
            "Recommended next action",
        ]
    return [
        "Direct answer",
        "Reasoning summary",
        "Caveats or assumptions",
        "Recommended next action",
    ]


def _render_prompt_text(
    *,
    target_model_hint: str,
    phase_label: str,
    increment_label: str,
    increment_goal: str,
    task_summary: str,
    relevant_context: str,
    constraints: list[str],
    requested_output: list[str],
    paste_back_instructions: str,
) -> str:
    constraints_text = "\n".join(f"- {item}" for item in constraints)
    output_text = "\n".join(f"- {item}" for item in requested_output)
    return f"""# Source Prompt Packet - {phase_label} / {increment_label}

Target model hint: {target_model_hint}

## Active Increment
{phase_label} / {increment_label}

Goal: {increment_goal}

## Task
{task_summary}

## Relevant Context
{relevant_context}

## Constraints
{constraints_text}

## Requested Output
{output_text}

## Paste Back
{paste_back_instructions}
"""


def _looks_like_path_listing(context: str) -> bool:
    lowered = context.lower()
    return any(
        marker in lowered
        for marker in [
            "path listing",
            "directory listing",
            "folder listing",
            "verified_context_roots",
            "available_read_only_sources",
        ]
    )


def _looks_like_generated_bundle_reference(context: str) -> bool:
    lowered = context.lower()
    return any(
        marker in lowered
        for marker in [
            "repomix-output.xml",
            "repomix-output.ast.xml",
            "generated_context_bundle",
            "<repository_context",
            "<source_context_bundle",
        ]
    )


def _extract_candidate_paths(context: str) -> list[str]:
    candidates: list[str] = []
    for raw_token in context.replace(",", "\n").splitlines():
        token = raw_token.strip().strip("-*`'\"")
        if ":" in token and not _looks_like_windows_path(token):
            token = token.rsplit(":", 1)[1].strip()
        if not token or _is_secret_shaped_path(token):
            continue
        if _looks_like_path_token(token):
            candidates.append(token)
    return list(dict.fromkeys(candidates))[:50]


def _omitted_secret_shaped_paths(context: str) -> list[str]:
    omitted: list[str] = []
    for raw_token in context.replace(",", "\n").splitlines():
        token = raw_token.strip().strip("-*`'\"")
        if ":" in token and not _looks_like_windows_path(token):
            token = token.rsplit(":", 1)[1].strip()
        if token and _is_secret_shaped_path(token) and _looks_like_path_token(token):
            omitted.append(token)
    return list(dict.fromkeys(omitted))[:50]


def _secret_shape_notes(context: str) -> list[str]:
    if _omitted_secret_shaped_paths(context):
        return ["Secret-shaped paths were omitted from included_paths metadata."]
    return ["No secret-shaped path names detected in supplied context metadata."]


def _looks_like_path_token(value: str) -> bool:
    return (
        "/" in value
        or "\\" in value
        or value.endswith((".ts", ".tsx", ".py", ".js", ".jsx", ".json", ".md", ".xml"))
    )


def _looks_like_windows_path(value: str) -> bool:
    return len(value) >= 3 and value[1:3] == ":\\"


def _is_secret_shaped_path(value: str) -> bool:
    lowered = value.lower()
    return any(
        marker in lowered
        for marker in [
            ".env",
            ".pem",
            ".key",
            "secret",
            "token",
            "credential",
            "id_rsa",
            "id_ed25519",
        ]
    )


def _estimate_tokens(value: str) -> int:
    return max(1, round(len(value) / 4)) if value else 0
