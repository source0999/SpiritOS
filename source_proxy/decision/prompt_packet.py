from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from source_proxy.decision.router import DecisionInput, RouteDecision, decide_route

TargetModelHint = Literal["chatgpt", "claude", "gemini", "google_ai_studio", "grok"]


@dataclass(frozen=True)
class PromptPacketInput:
    task: str
    target_model_hint: TargetModelHint | None = None
    relevant_context: str | None = None
    context_tokens: int | None = None
    sensitive: bool = False
    needs_current_info: bool = False
    needs_codebase_context: bool = False
    wants_implementation: bool = False
    prefer_free: bool = True


@dataclass(frozen=True)
class PromptPacket:
    target_model_hint: str
    task_summary: str
    relevant_context: str
    constraints: list[str]
    requested_output: list[str]
    paste_back_instructions: str
    prompt_text: str
    route_decision: RouteDecision

    def as_payload(self) -> dict[str, object]:
        return {
            "target_model_hint": self.target_model_hint,
            "task_summary": self.task_summary,
            "relevant_context": self.relevant_context,
            "constraints": self.constraints,
            "requested_output": self.requested_output,
            "paste_back_instructions": self.paste_back_instructions,
            "prompt_text": self.prompt_text,
            "route_decision": self.route_decision.as_payload(),
        }


def build_prompt_packet(input_data: PromptPacketInput) -> PromptPacket:
    decision_input = DecisionInput(
        task=input_data.task,
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
    relevant_context = _build_context_section(input_data)
    constraints = _constraints_for(input_data, decision)
    requested_output = _requested_output_for(input_data, decision)
    paste_back_instructions = (
        "Paste the model answer back into Source. Source will summarize, compare, "
        "and convert the useful parts into a Codex-ready follow-up."
    )
    prompt_text = _render_prompt_text(
        target_model_hint=target_model,
        task_summary=task_summary,
        relevant_context=relevant_context,
        constraints=constraints,
        requested_output=requested_output,
        paste_back_instructions=paste_back_instructions,
    )

    return PromptPacket(
        target_model_hint=target_model,
        task_summary=task_summary,
        relevant_context=relevant_context,
        constraints=constraints,
        requested_output=requested_output,
        paste_back_instructions=paste_back_instructions,
        prompt_text=prompt_text,
        route_decision=decision,
    )


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


def _build_context_section(input_data: PromptPacketInput) -> str:
    context = (input_data.relevant_context or "").strip()
    if context:
        return context

    if input_data.needs_codebase_context:
        return (
            "Use the repository context packet from Source if provided separately. "
            "If context is missing, ask for the specific files or compressed XML excerpt needed."
        )

    return "No additional repository context was supplied."


def _constraints_for(
    input_data: PromptPacketInput,
    decision: RouteDecision,
) -> list[str]:
    constraints = [
        "Do not invent file contents, test results, URLs, logs, or tool output.",
        "Separate facts from assumptions.",
        "Keep recommendations actionable and scoped to the task.",
    ]
    if input_data.sensitive or decision.risk_tier == "high":
        constraints.append("Treat secrets and private data as sensitive; do not echo credentials.")
    if input_data.needs_codebase_context:
        constraints.append("When referencing code, cite file paths and ask for missing files instead of guessing.")
    if input_data.wants_implementation:
        constraints.append("Prefer minimal, reviewable implementation steps over broad rewrites.")
    if input_data.needs_current_info:
        constraints.append("Use current browsing/research if available and cite sources.")
    return constraints


def _requested_output_for(
    input_data: PromptPacketInput,
    decision: RouteDecision,
) -> list[str]:
    if input_data.wants_implementation:
        return [
            "A concise implementation plan",
            "Specific files or modules likely involved",
            "Risks, edge cases, and tests to run",
            "A final Codex-ready instruction block",
        ]
    if decision.task_classification == "codebase_analysis":
        return [
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
    task_summary: str,
    relevant_context: str,
    constraints: list[str],
    requested_output: list[str],
    paste_back_instructions: str,
) -> str:
    constraints_text = "\n".join(f"- {item}" for item in constraints)
    output_text = "\n".join(f"- {item}" for item in requested_output)
    return f"""# Source Manual Prompt Packet

Target model hint: {target_model_hint}

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
