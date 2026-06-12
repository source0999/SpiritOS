from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from source_proxy.decision.tool_actions import TOOL_CAPABILITIES
from source_proxy.safety.paths import normalize_repo_path_candidate, unsafe_target_finding


AdvisoryPacketSource = Literal["mac_worker", "subagent"]
AdvisoryPacketStatus = Literal["accepted", "blocked"]

MAC_ALLOWED_PACKET_TYPES = {
    "system_status",
    "safe_check",
    "repo_context",
    "search_packet",
    "browser_inspection",
    "design_inspection",
}

SUBAGENT_ROLES = {
    "component_mapper",
    "safety_reviewer",
    "test_scribe",
    "design_reviewer",
    "scout_research_helper",
    "tool_steward",
}

SUBAGENT_ALLOWED_PACKET_TYPES = {
    "component_map",
    "safety_review",
    "test_notes",
    "design_review",
    "scout_research",
    "tool_audit",
}

FORBIDDEN_ADVISORY_ACTIONS = {
    "write",
    "edit",
    "apply",
    "commit",
    "push",
    "start_worker",
    "start_hidden_worker",
    "cartographer_run",
    "provider_route_change",
    "secret_read",
}


@dataclass(frozen=True)
class AdvisoryCapability:
    capability_id: str
    source: str
    label: str
    packet_types: tuple[str, ...]
    advisory_only: bool = True
    write_authority: bool = False
    apply_authority: bool = False
    can_start_workers: bool = False
    can_read_secrets: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdvisoryPacket:
    packet_id: str
    source: AdvisoryPacketSource
    packet_type: str
    role: str
    summary: str
    refs: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()
    blocks: tuple[str, ...] = ()
    requested_actions: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["refs"] = list(self.refs)
        payload["findings"] = list(self.findings)
        payload["blocks"] = list(self.blocks)
        payload["requested_actions"] = list(self.requested_actions)
        return payload


@dataclass(frozen=True)
class AdvisoryPacketValidation:
    status: AdvisoryPacketStatus
    packet: AdvisoryPacket | None
    reason_codes: tuple[str, ...] = ()
    advisory_only: bool = True
    can_execute: bool = False
    can_write: bool = False
    can_apply: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "packet": self.packet.to_dict() if self.packet is not None else None,
            "reason_codes": list(self.reason_codes),
            "advisory_only": self.advisory_only,
            "can_execute": self.can_execute,
            "can_write": self.can_write,
            "can_apply": self.can_apply,
        }


@dataclass(frozen=True)
class AdvisoryConflict:
    conflict_id: str
    packet_ids: tuple[str, ...]
    summary: str
    safety_blocks: tuple[str, ...] = ()
    source_proxy_final_gate: bool = True
    hidden_mutation_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "packet_ids": list(self.packet_ids),
            "summary": self.summary,
            "safety_blocks": list(self.safety_blocks),
            "source_proxy_final_gate": self.source_proxy_final_gate,
            "hidden_mutation_allowed": self.hidden_mutation_allowed,
        }


def advisory_capability_manifest() -> dict[str, Any]:
    source_proxy_tools = [
        {
            "action_type": action_type,
            "capability": capability,
            "authority_lane": "source_proxy_disposable_workspace_executor",
        }
        for action_type, capability in TOOL_CAPABILITIES.items()
    ]
    mac = AdvisoryCapability(
        capability_id="mac_worker_advisory",
        source="mac_worker",
        label="Mac Worker Advisory Context",
        packet_types=tuple(sorted(MAC_ALLOWED_PACKET_TYPES)),
    )
    subagents = [
        AdvisoryCapability(
            capability_id=f"subagent_{role}",
            source="subagent",
            label=role.replace("_", " ").title(),
            packet_types=tuple(sorted(SUBAGENT_ALLOWED_PACKET_TYPES)),
        )
        for role in sorted(SUBAGENT_ROLES)
    ]
    return {
        "source_proxy_tools": source_proxy_tools,
        "mac_worker": mac.to_dict(),
        "subagents": [capability.to_dict() for capability in subagents],
        "truth": advisory_truth_snapshot(),
    }


def advisory_truth_snapshot() -> dict[str, Any]:
    return {
        "mac_worker": {
            "advisory_only": True,
            "presented_as_executor": False,
            "write_authority": False,
            "apply_authority": False,
            "hidden_workers_allowed": False,
            "provider_routing_authority": False,
            "secret_read_authority": False,
        },
        "subagents": {
            "advisory_only": True,
            "presented_as_executor": False,
            "write_authority": False,
            "apply_authority": False,
            "hidden_workers_allowed": False,
            "cartographer_mutation_authority": False,
            "source_proxy_final_gate": True,
        },
    }


def validate_mac_advisory_packet(payload: dict[str, Any]) -> AdvisoryPacketValidation:
    packet = _packet_from_payload(payload, source="mac_worker")
    reasons = _base_packet_reasons(packet)
    if packet.packet_type not in MAC_ALLOWED_PACKET_TYPES:
        reasons.append("unsupported_mac_packet_type")
    if packet.role and packet.role != "mac_worker":
        reasons.append("mac_role_must_be_mac_worker")
    reasons.extend(_protected_ref_reasons(packet.refs))
    return _validation(packet, reasons)


def validate_subagent_advisory_packet(payload: dict[str, Any]) -> AdvisoryPacketValidation:
    packet = _packet_from_payload(payload, source="subagent")
    reasons = _base_packet_reasons(packet)
    if packet.role not in SUBAGENT_ROLES:
        reasons.append("unsupported_subagent_role")
    if packet.packet_type not in SUBAGENT_ALLOWED_PACKET_TYPES:
        reasons.append("unsupported_subagent_packet_type")
    reasons.extend(_protected_ref_reasons(packet.refs))
    return _validation(packet, reasons)


def build_advisory_context_packet(validations: list[AdvisoryPacketValidation]) -> dict[str, Any]:
    accepted = [validation.packet for validation in validations if validation.status == "accepted" and validation.packet is not None]
    blocked = [validation for validation in validations if validation.status == "blocked"]
    conflicts = detect_advisory_conflicts([packet for packet in accepted if packet is not None])
    return {
        "advisory_only": True,
        "source_proxy_final_gate": True,
        "accepted_packets": [packet.to_dict() for packet in accepted if packet is not None],
        "blocked_packets": [validation.to_dict() for validation in blocked],
        "conflicts": [conflict.to_dict() for conflict in conflicts],
        "truth": advisory_truth_snapshot(),
    }


def detect_advisory_conflicts(packets: list[AdvisoryPacket]) -> list[AdvisoryConflict]:
    safety_blocks = tuple(
        block
        for packet in packets
        if packet.role == "safety_reviewer"
        for block in packet.blocks
    )
    if not safety_blocks:
        return []
    packet_ids = tuple(packet.packet_id for packet in packets if packet.blocks or packet.findings)
    return [
        AdvisoryConflict(
            conflict_id="safety_reviewer_blocks_present",
            packet_ids=packet_ids,
            summary="Safety Reviewer reported advisory blocks. Source Proxy remains the final gate.",
            safety_blocks=safety_blocks,
        )
    ]


def _packet_from_payload(payload: dict[str, Any], *, source: AdvisoryPacketSource) -> AdvisoryPacket:
    return AdvisoryPacket(
        packet_id=str(payload.get("packet_id") or ""),
        source=source,
        packet_type=str(payload.get("packet_type") or ""),
        role=str(payload.get("role") or ("mac_worker" if source == "mac_worker" else "")),
        summary=str(payload.get("summary") or ""),
        refs=tuple(str(ref) for ref in payload.get("refs", ()) if str(ref)),
        findings=tuple(str(finding) for finding in payload.get("findings", ()) if str(finding)),
        blocks=tuple(str(block) for block in payload.get("blocks", ()) if str(block)),
        requested_actions=tuple(str(action) for action in payload.get("requested_actions", ()) if str(action)),
        metadata=dict(payload.get("metadata") or {}),
    )


def _base_packet_reasons(packet: AdvisoryPacket) -> list[str]:
    reasons: list[str] = []
    if not packet.packet_id:
        reasons.append("packet_id_required")
    if not packet.packet_type:
        reasons.append("packet_type_required")
    if not packet.summary:
        reasons.append("summary_required")
    forbidden = sorted({action for action in packet.requested_actions if action in FORBIDDEN_ADVISORY_ACTIONS})
    if forbidden:
        reasons.append("forbidden_advisory_action_requested:" + ",".join(forbidden))
    return reasons


def _protected_ref_reasons(refs: tuple[str, ...]) -> list[str]:
    reasons: list[str] = []
    for ref in refs:
        normalized = normalize_repo_path_candidate(ref)
        if unsafe_target_finding(normalized) is not None:
            reasons.append(f"protected_or_unsafe_ref:{normalized}")
    return reasons


def _validation(packet: AdvisoryPacket, reasons: list[str]) -> AdvisoryPacketValidation:
    return AdvisoryPacketValidation(
        status="blocked" if reasons else "accepted",
        packet=packet,
        reason_codes=tuple(reasons),
    )

