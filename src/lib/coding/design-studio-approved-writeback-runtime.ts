import "server-only";

import { createHash, randomUUID } from "node:crypto";
import { isAbsolute, relative, resolve } from "node:path";

import {
  consumeDesignWritebackApproval,
  finalizeDesignWritebackApproval,
  hashDesignParticipantOutput,
  loadDesignWritebackApproval,
  type DesignParticipantRecord,
} from "./design-approval-authority";
import {
  rollbackApprovedDesignMemoryNote,
  verifyApprovedDesignMemoryNote,
  writeApprovedDesignMemoryNote,
  type ApprovedDesignMemoryGate,
  type ApprovedDesignMemoryWriteResult,
  type ApprovedDesignMemoryWritebackPayload,
} from "./design-studio-obsidian-writeback";
import {
  buildDesignWritebackArtifact,
  type DesignWritebackArtifact,
} from "./design-writeback-contract";

export type DesignStudioAcceptedRunGate = {
  acceptance_id?: string;
  approved_by?: "human" | "model";
  run_status: "accepted" | "preview_only" | "rejected";
  trace_id: string;
};

export type DesignStudioApprovedWritebackRequest = {
  approval_id: string;
  accepted_run: DesignStudioAcceptedRunGate;
  gate: ApprovedDesignMemoryGate;
  payload: ApprovedDesignMemoryWritebackPayload;
};

const SAFE_APPROVAL_ID = /^[A-Za-z0-9_-]{6,128}$/;
const SERVER_OWNED_VAULT_ROOT =
  process.env.SPIRITOS_DESIGN_VAULT_ROOT || "/home/source/.local/state/spiritos/design-vault";

export async function runDesignStudioApprovedWriteback(
  request: DesignStudioApprovedWritebackRequest,
) {
  if (!request || typeof request !== "object") {
    return rejection(["design_writeback_request_invalid"], false);
  }
  if (!request.approval_id?.trim() || request.payload?.approval_id !== request.approval_id) {
    return rejection(["missing_approval_id"], false);
  }
  if (!SAFE_APPROVAL_ID.test(request.approval_id)) {
    return rejection(["invalid_approval_id"], false);
  }

  const artifactResult = buildDesignWritebackArtifact({
    accepted_run: request.accepted_run,
    gate: request.gate,
    payload: request.payload,
  });
  if (!artifactResult.ok) {
    return rejection([artifactResult.reason], false);
  }
  const artifact = artifactResult.value;

  const approval = await loadDesignWritebackApproval(request.approval_id);
  if (!approval.ok) {
    return rejection([approval.reason], false, artifact);
  }
  if (
    approval.value.content_hash !== artifact.artifact_hash ||
    approval.value.artifact_id !== artifact.artifact_id ||
    approval.value.context !== artifact.context ||
    approval.value.target !== artifact.target
  ) {
    return rejection(["approval_artifact_binding_mismatch"], false, artifact);
  }

  const reviewer = invokeDesignReviewer(artifact);
  if (reviewer.status !== "accepted") {
    return rejection(["design_reviewer_rejected"], false, artifact, [reviewer]);
  }

  const consumption = await consumeDesignWritebackApproval(approval.value, artifact);
  if (!consumption.ok) {
    return rejection([consumption.reason], false, artifact, [reviewer]);
  }

  const writeResult = writeApprovedDesignMemoryNote(request.payload, request.gate, {
    vaultRoot: SERVER_OWNED_VAULT_ROOT,
  });
  const verifier = invokeDesignVerifier(artifact, writeResult);
  const evidenceRecorder = invokeDesignEvidenceRecorder(artifact, reviewer, verifier);
  const participantRecords = [reviewer, verifier, evidenceRecorder];

  if (writeResult.status !== "written" || verifier.status !== "verified") {
    const reasons =
      writeResult.status === "rejected"
        ? writeResult.reasons
        : ["post_write_verification_failed"];
    const rollback =
      writeResult.status === "written"
        ? rollbackApprovedDesignMemoryNote(writeResult)
        : undefined;
    const finalized = await finalizeDesignWritebackApproval(approval.value, {
      artifact,
      participant_records: participantRecords,
      receipt: failureReceipt(request, artifact),
      status: "failed",
    });
    return rejection(
      [
        ...reasons,
        ...(rollback?.status === "rollback_failed" ? [rollback.reason] : []),
        ...(!finalized.ok ? [finalized.reason] : []),
      ],
      true,
      artifact,
      participantRecords,
      rollback?.status,
    );
  }

  if (evidenceRecorder.status !== "recorded") {
    const rollback = rollbackApprovedDesignMemoryNote(writeResult);
    const finalized = await finalizeDesignWritebackApproval(approval.value, {
      artifact,
      participant_records: participantRecords,
      receipt: failureReceipt(request, artifact),
      status: "failed",
    });
    return rejection(
      [
        "design_evidence_recorder_rejected",
        ...(rollback.status === "rollback_failed" ? [rollback.reason] : []),
        ...(!finalized.ok ? [finalized.reason] : []),
      ],
      true,
      artifact,
      participantRecords,
      rollback.status,
    );
  }

  const finalized = await finalizeDesignWritebackApproval(approval.value, {
    artifact,
    participant_records: participantRecords,
    receipt: {
      acceptance_id: request.accepted_run.acceptance_id as string,
      content_hash: writeResult.content_hash,
      expected_state: writeResult.expected_state,
      result_state: writeResult.result_state,
      target: artifact.target,
      trace_id: artifact.context,
    },
    result_id: writeResult.path,
    status: "succeeded",
  });
  if (!finalized.ok) {
    const rollback = rollbackApprovedDesignMemoryNote(writeResult);
    return rejection(
      [finalized.reason, ...(rollback.status === "rollback_failed" ? [rollback.reason] : [])],
      true,
      artifact,
      participantRecords,
      rollback.status,
    );
  }

  return {
    ...writeResult,
    acceptance_id_hash: sha256(request.accepted_run.acceptance_id as string),
    approval_receipt: finalized.value,
    artifact_hash: artifact.artifact_hash,
    participant_records: participantRecords,
    write_invoked: true,
  };
}

export function invokeDesignReviewer(artifact: DesignWritebackArtifact): DesignParticipantRecord {
  const checks = [
    "immutable_artifact_hash_valid",
    "human_acceptance_bound",
    "verified_gate_bound",
    "expected_target_absent_bound",
  ];
  const binding = artifact.binding;
  const accepted =
    /^[0-9a-f]{64}$/.test(artifact.artifact_hash) &&
    binding.accepted_run.approved_by === "human" &&
    binding.accepted_run.run_status === "accepted" &&
    binding.gate.run_status === "verified" &&
    binding.write_contract.expected_state.target === "absent";
  return participantRecord("design-reviewer", artifact, accepted ? "accepted" : "rejected", checks);
}

export function invokeDesignVerifier(
  artifact: DesignWritebackArtifact,
  result: ApprovedDesignMemoryWriteResult,
): DesignParticipantRecord {
  const checks = [
    "write_receipt_verified",
    "result_content_hash_matches_bound_artifact",
    "result_target_matches_bound_artifact",
    "result_state_written_verified",
  ];
  let targetMatches = false;
  let independentVerification = false;
  if (result.status === "written") {
    const relativeTarget = relative(resolve(SERVER_OWNED_VAULT_ROOT), resolve(result.path)).replaceAll("\\", "/");
    targetMatches =
      !isAbsolute(relativeTarget) &&
      relativeTarget !== ".." &&
      !relativeTarget.startsWith("../") &&
      relativeTarget === artifact.target;
    const observed = verifyApprovedDesignMemoryNote(result);
    independentVerification =
      observed.status === "verified" && observed.content_hash === artifact.note_content_hash;
  }
  const verified =
    result.status === "written" &&
    result.verified === true &&
    result.expected_state === artifact.binding.write_contract.expected_state.target &&
    result.result_state === artifact.binding.write_contract.result_state.target &&
    result.content_hash === artifact.note_content_hash &&
    independentVerification &&
    targetMatches;
  return participantRecord("design-verifier", artifact, verified ? "verified" : "rejected", checks);
}

export function invokeDesignEvidenceRecorder(
  artifact: DesignWritebackArtifact,
  reviewer: DesignParticipantRecord,
  verifier: DesignParticipantRecord,
): DesignParticipantRecord {
  const checks = [
    "reviewer_output_distinct",
    "verifier_output_distinct",
    "participant_artifact_hashes_match",
    "review_and_verification_passed",
  ];
  const recorded =
    reviewer.participant === "design-reviewer" &&
    verifier.participant === "design-verifier" &&
    reviewer.invocation_id !== verifier.invocation_id &&
    reviewer.output_id !== verifier.output_id &&
    reviewer.artifact_hash === artifact.artifact_hash &&
    verifier.artifact_hash === artifact.artifact_hash &&
    reviewer.status === "accepted" &&
    verifier.status === "verified";
  return participantRecord("evidence-recorder", artifact, recorded ? "recorded" : "rejected", checks);
}

function participantRecord(
  participant: DesignParticipantRecord["participant"],
  artifact: DesignWritebackArtifact,
  status: DesignParticipantRecord["status"],
  checks: string[],
): DesignParticipantRecord {
  const invocationId = `design-invocation-${randomUUID()}`;
  const outputId = `design-output-${randomUUID()}`;
  const invokedAt = new Date().toISOString();
  const output = {
    artifact_hash: artifact.artifact_hash,
    checks,
    invocation_id: invocationId,
    invoked_at: invokedAt,
    output_id: outputId,
    participant,
    status,
  };
  return {
    ...output,
    output_hash: hashDesignParticipantOutput(output),
  };
}

function failureReceipt(
  request: DesignStudioApprovedWritebackRequest,
  artifact: DesignWritebackArtifact,
) {
  return {
    acceptance_id: request.accepted_run.acceptance_id as string,
    content_hash: artifact.note_content_hash,
    expected_state: "absent" as const,
    result_state: "rejected" as const,
    target: artifact.target,
    trace_id: artifact.context,
  };
}

function rejection(
  reasons: string[],
  writeInvoked: boolean,
  artifact?: DesignWritebackArtifact,
  participantRecords: DesignParticipantRecord[] = [],
  rollbackStatus?: string,
) {
  return {
    ...(artifact ? { artifact_hash: artifact.artifact_hash } : {}),
    participant_records: participantRecords,
    reasons: Array.from(new Set(reasons)),
    ...(rollbackStatus ? { rollback_status: rollbackStatus } : {}),
    status: "rejected" as const,
    write_invoked: writeInvoked,
  };
}

function sha256(value: string) {
  return createHash("sha256").update(value, "utf8").digest("hex");
}
