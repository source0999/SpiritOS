from __future__ import annotations

from typing import Any


REQUIRED_CONSUMERS = (
    "coding-executor",
    "coding-reviewer",
    "coding-verifier",
    "coding-anti-cheat",
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
    participant_records = value.get("participant_records")
    if not isinstance(approval_id, str) or not approval_id.startswith("apr_"):
        raise CampaignApprovalEvidenceError("approval_evidence_id_missing")
    if not isinstance(generation, int) or generation < 1:
        raise CampaignApprovalEvidenceError("approval_evidence_generation_missing")
    if not isinstance(acknowledgements, dict):
        raise CampaignApprovalEvidenceError("approval_evidence_acknowledgements_missing")
    if not isinstance(participant_records, list):
        raise CampaignApprovalEvidenceError("approval_evidence_participant_records_missing")
    by_role = {
        str(record.get("role") or ""): record
        for record in participant_records
        if isinstance(record, dict)
    }
    if set(by_role) != set(REQUIRED_CONSUMERS) or len(participant_records) != len(
        REQUIRED_CONSUMERS
    ):
        raise CampaignApprovalEvidenceError("approval_evidence_participant_set_invalid")
    target_plugin_identity = value.get("target_plugin_identity")
    if target_plugin_identity is not None and not isinstance(target_plugin_identity, dict):
        raise CampaignApprovalEvidenceError("approval_target_plugin_identity_invalid")
    for consumer in REQUIRED_CONSUMERS:
        acknowledgement = acknowledgements.get(consumer)
        if not isinstance(acknowledgement, dict):
            raise CampaignApprovalEvidenceError(f"approval_acknowledgement_missing:{consumer}")
        if acknowledgement.get("approval_id") != approval_id or acknowledgement.get("generation") != generation:
            raise CampaignApprovalEvidenceError(f"approval_acknowledgement_mismatch:{consumer}")
        record = by_role[consumer]
        if (
            record.get("consumer_acknowledgement") != acknowledgement
            or record.get("consumer_acknowledgement_id")
            != acknowledgement.get("acknowledgement_id")
        ):
            raise CampaignApprovalEvidenceError(
                f"approval_acknowledgement_not_participant_owned:{consumer}"
            )
        for field in (
            "artifact_sha256",
            "invocation_id",
            "output_id",
            "acknowledgement_id",
        ):
            if not isinstance(acknowledgement.get(field), str) or not acknowledgement[field]:
                raise CampaignApprovalEvidenceError(
                    f"approval_acknowledgement_provenance_missing:{consumer}:{field}"
                )
    artifact_hashes = {
        str(acknowledgements[consumer]["artifact_sha256"])
        for consumer in REQUIRED_CONSUMERS
    }
    if len(artifact_hashes) != 1 or artifact_hashes != {str(value.get("artifact_sha256") or "")}:
        raise CampaignApprovalEvidenceError("approval_participant_artifact_mismatch")
    for field in ("invocation_id", "output_id", "acknowledgement_id"):
        identities = [str(acknowledgements[consumer][field]) for consumer in REQUIRED_CONSUMERS]
        if len(set(identities)) != len(identities):
            raise CampaignApprovalEvidenceError(
                f"approval_participant_identity_not_distinct:{field}"
            )
