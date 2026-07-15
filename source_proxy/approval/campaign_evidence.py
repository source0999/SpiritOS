from __future__ import annotations

from typing import Any


REQUIRED_CONSUMERS = (
    "coding-executor",
    "coding-reviewer",
    "coding-verifier",
    "evidence-recorder",
)


class CampaignApprovalEvidenceError(ValueError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


def validate_coding_approval_evidence(value: dict[str, Any]) -> None:
    approval_id = value.get("approval_id")
    generation = value.get("generation")
    acknowledgements = value.get("acknowledgements")
    if not isinstance(approval_id, str) or not approval_id.startswith("apr_"):
        raise CampaignApprovalEvidenceError("approval_evidence_id_missing")
    if not isinstance(generation, int) or generation < 1:
        raise CampaignApprovalEvidenceError("approval_evidence_generation_missing")
    if not isinstance(acknowledgements, dict):
        raise CampaignApprovalEvidenceError("approval_evidence_acknowledgements_missing")
    target_plugin_identity = value.get("target_plugin_identity")
    if target_plugin_identity is not None and not isinstance(target_plugin_identity, dict):
        raise CampaignApprovalEvidenceError("approval_target_plugin_identity_invalid")
    for consumer in REQUIRED_CONSUMERS:
        acknowledgement = acknowledgements.get(consumer)
        if not isinstance(acknowledgement, dict):
            raise CampaignApprovalEvidenceError(f"approval_acknowledgement_missing:{consumer}")
        if acknowledgement.get("approval_id") != approval_id or acknowledgement.get("generation") != generation:
            raise CampaignApprovalEvidenceError(f"approval_acknowledgement_mismatch:{consumer}")
        if isinstance(target_plugin_identity, dict) and acknowledgement.get("target_plugin_identity") != target_plugin_identity:
            raise CampaignApprovalEvidenceError(f"approval_target_plugin_acknowledgement_mismatch:{consumer}")
