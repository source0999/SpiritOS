"""Canonical Campaign 3 registry for non-core coding participants.

This registry is intentionally a selection boundary, not a dispatcher.  The
R1 orchestrator remains the only task/run/attempt owner and the only component
that may use a selected lane result in a coding lifecycle.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from source_proxy.contracts.coding_lane_contracts import (
    canonical_extended_coding_lane_contracts,
)


EXTENDED_LANE_REGISTRY_VERSION = "coding.extended-lane-registry/v1"
EXTENDED_LANE_IDS = (
    "extended.scout-research",
    "extended.obsidian-knowledge",
    "extended.mac-worker",
    "extended.context-model",
    "extended.retained-sub-agent",
    "extended.platform-verifier",
    "extended.conflict-resolver",
    "extended.diagnosis-envelope",
)
_CONTRACT_IDS = tuple(lane_id.replace(".", "-") for lane_id in EXTENDED_LANE_IDS)
_SELECTABLE_CLASSIFICATIONS = {"mandatory", "conditional", "optional"}
_VALID_CLASSIFICATIONS = _SELECTABLE_CLASSIFICATIONS | {
    "compatibility-only", "test-only", "labs-only", "duplicate", "obsolete", "deferred",
}
_VALID_DISPOSITIONS = {"retained", "provider-only", "decommissioned", "deferred"}


class ExtendedLaneRegistryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExtendedLaneDefinition:
    lane_id: str
    contract_lane_id: str
    classification: str
    disposition: str
    owner: str
    authority_class: str
    contract_version: str
    production_caller: str
    production_consumer: str
    timeout_ms: int
    retry_limit: int
    fallback: str
    applicability: str
    observability: str
    evidence: str
    migration_requirement: str

    @property
    def selectable(self) -> bool:
        return self.disposition == "retained" and self.classification in _SELECTABLE_CLASSIFICATIONS

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": EXTENDED_LANE_REGISTRY_VERSION,
            "lane_id": self.lane_id,
            "contract_lane_id": self.contract_lane_id,
            "classification": self.classification,
            "disposition": self.disposition,
            "owner": self.owner,
            "authority_class": self.authority_class,
            "contract_version": self.contract_version,
            "production_caller": self.production_caller,
            "production_consumer": self.production_consumer,
            "timeout_ms": self.timeout_ms,
            "retry_limit": self.retry_limit,
            "fallback": self.fallback,
            "applicability": self.applicability,
            "observability": self.observability,
            "evidence": self.evidence,
            "migration_requirement": self.migration_requirement,
            "selectable": self.selectable,
        }


def canonical_extended_lane_registry() -> tuple[ExtendedLaneDefinition, ...]:
    contracts = canonical_extended_coding_lane_contracts()
    definitions = (
        _lane("extended.scout-research", "conditional", "retained", "source-proxy-scout", "source_proxy.coding.extended_lanes:invoke_scout", "canonical-context-broker/planner/coder/reviewer/verifier", 10_000, 1, "degrade_claim_ceiling_or_block", "task_requires_current_external_research", "diagnosis-envelope", "immutable research receipt", "replace preview-only Scout use"),
        _lane("extended.obsidian-knowledge", "conditional", "retained", "source-proxy-context", "source_proxy.coding.extended_lanes:invoke_obsidian", "canonical-context-broker/conflict-resolver", 5_000, 0, "exclude_stale_or_unavailable_context", "task_has_registered_project_knowledge", "diagnosis-envelope", "immutable context receipt", "register vault and bounded reads"),
        _lane("extended.mac-worker", "conditional", "retained", "source-proxy-mac-worker", "source_proxy.coding.extended_lanes:invoke_mac", "platform-verifier/verifier/final-verdict", 120_000, 1, "block_when_platform_required", "task_requires_macos_or_webkit_validation", "diagnosis-envelope", "immutable Mac job receipt", "replace advisory-only lane"),
        _lane("extended.context-model", "conditional", "retained", "source-proxy-model-router", "source_proxy.coding.extended_lanes:invoke_context_model", "canonical-context-broker/planner/conflict-resolver", 30_000, 1, "degrade_to_declared_model_fallback", "planner_selects_second_context_opinion", "diagnosis-envelope", "immutable model invocation receipt", "bind model identity and consumption"),
        _lane("extended.retained-sub-agent", "conditional", "retained", "source-proxy-agent-registry", "source_proxy.coding.extended_lanes:invoke_subagent", "planner/reviewer/verifier", 45_000, 1, "block_or_degrade_by_task_policy", "task_selects_registered_nonduplicate_agent", "diagnosis-envelope", "immutable agent invocation receipt", "remove preview-only helpers"),
        _lane("extended.platform-verifier", "conditional", "retained", "source-proxy-verification", "source_proxy.coding.extended_lanes:invoke_platform_verifier", "verifier/final-verdict", 15_000, 0, "block_on_unresolved_platform_conflict", "Mac or local platform evidence is present", "diagnosis-envelope", "immutable platform verification receipt", "reconcile Mac and local evidence"),
        _lane("extended.conflict-resolver", "mandatory", "retained", "source-proxy-orchestrator", "source_proxy.coding.extended_lanes:resolve_conflict", "planner/verifier/diagnosis-envelope", 1_000, 0, "block_on_unresolved_conflict", "two applicable lanes make incompatible claims", "diagnosis-envelope", "immutable conflict receipt", "make precedence explicit"),
        _lane("extended.diagnosis-envelope", "mandatory", "retained", "source-proxy-observability", "source_proxy.coding.extended_lanes:build_diagnosis", "read-only Campaign 4 projection", 1_000, 0, "retain_failed_run_diagnosis", "every coding run", "read-only API", "immutable envelope receipt", "extend backend-only observability"),
    )
    if tuple(item.lane_id for item in definitions) != EXTENDED_LANE_IDS:
        raise ExtendedLaneRegistryError("extended_lane_registry_order_invalid")
    if set(contracts) != set(_CONTRACT_IDS):
        raise ExtendedLaneRegistryError("extended_lane_contract_registry_mismatch")
    for definition in definitions:
        _validate_definition(definition, contracts)
    return definitions


def selectable_extended_lanes(*, applicable_lane_ids: list[str]) -> tuple[ExtendedLaneDefinition, ...]:
    requested = tuple(dict.fromkeys(str(item).strip() for item in applicable_lane_ids if str(item).strip()))
    registry = {item.lane_id: item for item in canonical_extended_lane_registry()}
    unknown = [lane_id for lane_id in requested if lane_id not in registry]
    if unknown:
        raise ExtendedLaneRegistryError(f"unknown_extended_lane:{unknown[0]}")
    selected = tuple(registry[lane_id] for lane_id in requested)
    rejected = [item.lane_id for item in selected if not item.selectable]
    if rejected:
        raise ExtendedLaneRegistryError(f"nonselectable_extended_lane:{rejected[0]}")
    return selected


def _lane(lane_id: str, classification: str, disposition: str, owner: str, production_caller: str, production_consumer: str, timeout_ms: int, retry_limit: int, fallback: str, applicability: str, observability: str, evidence: str, migration_requirement: str) -> ExtendedLaneDefinition:
    return ExtendedLaneDefinition(
        lane_id=lane_id,
        contract_lane_id=lane_id.replace(".", "-"),
        classification=classification,
        disposition=disposition,
        owner=owner,
        authority_class=str(canonical_extended_coding_lane_contracts()[lane_id.replace(".", "-")]["authority_class"]),
        contract_version=str(canonical_extended_coding_lane_contracts()[lane_id.replace(".", "-")]["contract_version"]),
        production_caller=production_caller,
        production_consumer=production_consumer,
        timeout_ms=timeout_ms,
        retry_limit=retry_limit,
        fallback=fallback,
        applicability=applicability,
        observability=observability,
        evidence=evidence,
        migration_requirement=migration_requirement,
    )


def _validate_definition(definition: ExtendedLaneDefinition, contracts: Mapping[str, Mapping[str, Any]]) -> None:
    if definition.lane_id not in EXTENDED_LANE_IDS or definition.contract_lane_id not in contracts:
        raise ExtendedLaneRegistryError("extended_lane_definition_identity_invalid")
    if definition.classification not in _VALID_CLASSIFICATIONS or definition.disposition not in _VALID_DISPOSITIONS:
        raise ExtendedLaneRegistryError(f"extended_lane_definition_disposition_invalid:{definition.lane_id}")
    if not definition.selectable and definition.disposition == "retained":
        raise ExtendedLaneRegistryError(f"retained_extended_lane_not_selectable:{definition.lane_id}")
    if not definition.owner or not definition.production_caller or not definition.production_consumer:
        raise ExtendedLaneRegistryError(f"extended_lane_caller_consumer_missing:{definition.lane_id}")
    if definition.timeout_ms <= 0 or definition.retry_limit < 0 or not definition.fallback:
        raise ExtendedLaneRegistryError(f"extended_lane_execution_policy_invalid:{definition.lane_id}")
    contract = contracts[definition.contract_lane_id]
    if contract.get("contract_version") != definition.contract_version or contract.get("authority_class") != definition.authority_class:
        raise ExtendedLaneRegistryError(f"extended_lane_contract_binding_invalid:{definition.lane_id}")
