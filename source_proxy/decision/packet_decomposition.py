"""Local packet decomposition for tasks too broad or brittle as one prompt.

Benchmark labels are stripped before shape selection so known eval names cannot
become runtime branches or tailored success paths.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from source_proxy.diagnostics.status_codes import FailureClass




class TaskShape(str, Enum):
    MULTI_NODE_RESOURCE_PLANNING = "multi_node_resource_planning"
    CURRENT_TOOL_COMPARISON = "current_tool_comparison"
    ARCHITECTURE_PLANNING = "architecture_planning"
    IMPLEMENTATION_HANDOFF = "implementation_handoff"
    RESEARCH_BACKED_RECOMMENDATION = "research_backed_recommendation"


BENCHMARK_LABEL_RE = re.compile(r"\b(?:A\d+|\d+R\d*|Set\s+[A-Z])\b", re.IGNORECASE)


@dataclass(frozen=True)
class SubPacket:
    packet_id: str
    task_shape: str
    title: str
    instruction: str
    evidence_requirements: tuple[str, ...]
    validation_focus: tuple[str, ...]
    failure_classifications: tuple[FailureClass, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_requirements"] = list(self.evidence_requirements)
        payload["validation_focus"] = list(self.validation_focus)
        payload["failure_classifications"] = [item.value for item in self.failure_classifications]
        return payload


@dataclass(frozen=True)
class PacketDecomposition:
    task_shape: str
    decomposition_family: str
    source: str
    local_only: bool
    provider_call_performed: bool
    sub_packets: tuple[SubPacket, ...]
    validation_status: str
    validation_findings: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_shape": self.task_shape,
            "decomposition_family": self.decomposition_family,
            "source": self.source,
            "local_only": self.local_only,
            "provider_call_performed": self.provider_call_performed,
            "sub_packets": [packet.to_dict() for packet in self.sub_packets],
            "validation_status": self.validation_status,
            "validation_findings": list(self.validation_findings),
        }


_SHAPE_KEYWORDS: dict[TaskShape, tuple[str, ...]] = {
    TaskShape.MULTI_NODE_RESOURCE_PLANNING: (
        "multi node", "multi-node", "nodes", "cluster", "resource planning", "capacity", "allocation"
    ),
    TaskShape.CURRENT_TOOL_COMPARISON: (
        "compare", "comparison", "versus", " vs ", "tool", "current tool", "which tool"
    ),
    TaskShape.ARCHITECTURE_PLANNING: (
        "architecture", "system design", "design plan", "service boundary", "component", "integration plan"
    ),
    TaskShape.IMPLEMENTATION_HANDOFF: (
        "handoff", "implementation", "patch plan", "coder", "developer", "build this"
    ),
    TaskShape.RESEARCH_BACKED_RECOMMENDATION: (
        "research", "recommendation", "evidence backed", "source backed", "current info", "cite"
    ),
}

_SUBPACKET_TEMPLATES: dict[TaskShape, tuple[tuple[str, str], ...]] = {
    TaskShape.MULTI_NODE_RESOURCE_PLANNING: (
        ("inventory", "Inventory each node, capacity limit, dependency, and unknown before assigning resources."),
        ("allocation", "Draft a per-node allocation plan with explicit assumptions and conflict points."),
        ("validation", "Validate pressure points, missing evidence, and rollback triggers per node."),
    ),
    TaskShape.CURRENT_TOOL_COMPARISON: (
        ("tool-a", "Evaluate the first candidate tool against the same criteria and cite evidence IDs only."),
        ("tool-b", "Evaluate the second candidate tool against the same criteria and cite evidence IDs only."),
        ("decision-matrix", "Compare candidates with neutral criteria and mark missing evidence without inventing conclusions."),
    ),
    TaskShape.ARCHITECTURE_PLANNING: (
        ("constraints", "Extract architectural constraints, ownership boundaries, and non-goals."),
        ("interfaces", "Map interfaces, data flow, and compatibility risks without changing public behavior."),
        ("verification", "Define validation checks, rollback path, and failure classes for the proposed architecture."),
    ),
    TaskShape.IMPLEMENTATION_HANDOFF: (
        ("scope", "Summarize exact implementation scope, files likely involved, and hard stop lines."),
        ("steps", "Break work into small local implementation steps with focused checks."),
        ("readback", "Prepare handoff readback, acceptance proof, and unresolved risks."),
    ),
    TaskShape.RESEARCH_BACKED_RECOMMENDATION: (
        ("question", "Normalize the research question and separate facts needed from recommendation criteria."),
        ("evidence", "Collect evidence references and label unavailable or stale evidence explicitly."),
        ("recommendation", "Produce the recommendation only from cited evidence and state caveats."),
    ),
}

_VALIDATION_FOCUS: dict[TaskShape, tuple[str, ...]] = {
    TaskShape.MULTI_NODE_RESOURCE_PLANNING: ("per-node evidence present", "resource pressure surfaced", "allocation conflicts labeled"),
    TaskShape.CURRENT_TOOL_COMPARISON: ("same criteria for each tool", "no unsupported winner", "fresh evidence IDs required"),
    TaskShape.ARCHITECTURE_PLANNING: ("public contract preserved", "interfaces explicit", "rollback path present"),
    TaskShape.IMPLEMENTATION_HANDOFF: ("scope bounded", "checks executable", "handoff preserves unknowns"),
    TaskShape.RESEARCH_BACKED_RECOMMENDATION: ("evidence IDs present", "no scripted conclusion", "staleness caveats explicit"),
}

_FAILURE_CLASSES: dict[TaskShape, tuple[FailureClass, ...]] = {
    TaskShape.MULTI_NODE_RESOURCE_PLANNING: (FailureClass.RESOURCE_PRESSURE, FailureClass.EVIDENCE_MISSING, FailureClass.VALIDATOR_FAILURE),
    TaskShape.CURRENT_TOOL_COMPARISON: (FailureClass.EVIDENCE_MISSING, FailureClass.VALIDATOR_FAILURE, FailureClass.PROMPT_AMBIGUITY),
    TaskShape.ARCHITECTURE_PLANNING: (FailureClass.ROUTING_FAILURE, FailureClass.BRIDGE_INTEGRATION_FAILURE, FailureClass.VALIDATOR_FAILURE),
    TaskShape.IMPLEMENTATION_HANDOFF: (FailureClass.TOOL_FAILURE, FailureClass.EVIDENCE_MISSING, FailureClass.HUMAN_APPROVAL_REQUIRED),
    TaskShape.RESEARCH_BACKED_RECOMMENDATION: (FailureClass.SEARCH_PROVIDER_EMPTY, FailureClass.SEARCH_PROVIDER_FAILURE, FailureClass.EVIDENCE_MISSING),
}


def supported_task_shapes() -> tuple[str, ...]:
    return tuple(shape.value for shape in TaskShape)


def normalize_task_shape(task_shape: str | None = None, *, task: str = "") -> str:
    candidate = _clean_shape_text(task_shape or "")
    for shape in TaskShape:
        if candidate in {shape.value, shape.value.replace("_", " "), shape.name.lower()}:
            return shape.value
    text = _clean_shape_text(f"{task_shape or ''} {task}")
    scores = {
        shape: sum(1 for keyword in keywords if keyword in text)
        for shape, keywords in _SHAPE_KEYWORDS.items()
    }
    best_shape, best_score = max(scores.items(), key=lambda item: item[1])
    return best_shape.value if best_score > 0 else TaskShape.IMPLEMENTATION_HANDOFF.value


def decompose_task(
    task: str,
    *,
    task_shape: str | None = None,
    evidence_ids: tuple[str, ...] | list[str] | None = None,
    source: str = "local_packet_decomposition",
) -> PacketDecomposition:
    shape = TaskShape(normalize_task_shape(task_shape, task=task))
    evidence = tuple(evidence_ids or ())
    sub_packets = tuple(
        _build_sub_packet(shape, idx, key, instruction, evidence)
        for idx, (key, instruction) in enumerate(_SUBPACKET_TEMPLATES[shape], start=1)
    )
    findings = validate_sub_packets(sub_packets)
    return PacketDecomposition(
        task_shape=shape.value,
        decomposition_family=f"{shape.value}:v1",
        source=source,
        local_only=True,
        provider_call_performed=False,
        sub_packets=sub_packets,
        validation_status="pass" if not findings else "fail",
        validation_findings=tuple(findings),
    )


def build_decomposition_from_brain_switch(
    verdict: Any,
    task: str,
    *,
    task_shape: str | None = None,
    evidence_ids: tuple[str, ...] | list[str] | None = None,
) -> PacketDecomposition | None:
    recommendation = getattr(verdict, "recommendation", verdict)
    recommendation_value = getattr(recommendation, "value", recommendation)
    if recommendation_value != "LOCAL_DECOMPOSITION_RECOMMENDED":
        return None
    return decompose_task(
        task,
        task_shape=task_shape or getattr(verdict, "task_shape", None),
        evidence_ids=evidence_ids or getattr(verdict, "evidence_ids", ()),
        source="brain_switch_dry_run_recommendation",
    )


def validate_sub_packets(sub_packets: tuple[SubPacket, ...] | list[SubPacket]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for packet in sub_packets:
        missing: list[str] = []
        if not packet.evidence_requirements:
            missing.append("evidence_requirements")
        if not packet.validation_focus:
            missing.append("validation_focus")
        if not packet.failure_classifications:
            missing.append("failure_classifications")
        if missing:
            findings.append({
                "packet_id": packet.packet_id,
                "failure_class": FailureClass.EVIDENCE_MISSING.value,
                "missing": missing,
            })
    return findings


def monolithic_packet_quality(task: str) -> dict[str, Any]:
    return {
        "task_shape": normalize_task_shape(task=task),
        "sub_packet_count": 1,
        "has_independent_validation": False,
        "evidence_requirement_count": 0,
    }


def _build_sub_packet(
    shape: TaskShape,
    index: int,
    key: str,
    instruction: str,
    evidence_ids: tuple[str, ...],
) -> SubPacket:
    evidence_requirement = f"evidence_ref:{key}"
    if evidence_ids:
        evidence_requirement = f"evidence_ref:{key}; allowed_ids={','.join(evidence_ids)}"
    return SubPacket(
        packet_id=f"{shape.value}:{index}:{key}",
        task_shape=shape.value,
        title=key.replace("-", " ").title(),
        instruction=instruction,
        evidence_requirements=(evidence_requirement, "mark_missing_evidence_without_filling_substance"),
        validation_focus=_VALIDATION_FOCUS[shape],
        failure_classifications=_FAILURE_CLASSES[shape],
    )


def _clean_shape_text(value: str) -> str:
    without_labels = BENCHMARK_LABEL_RE.sub(" ", value or "")
    return " ".join(without_labels.replace("_", " ").lower().split())
