import "server-only";

import { randomUUID } from "node:crypto";

import {
  compensateSpiritFlixAdminApproval,
  consumeSpiritFlixAdminApproval,
  finalizeSpiritFlixAdminApproval,
  type SpiritFlixAdminFinalizationEvidence,
  type SpiritFlixAdminParticipantInvocation,
} from "@/lib/coding/spiritflix-admin-approval-authority";
import {
  hashSpiritFlixAdminState,
  type SpiritFlixAdminApprovalBinding,
} from "@/lib/coding/spiritflix-admin-approval-binding";

export class SpiritFlixAdminTransactionError extends Error {
  readonly reasonCode: string;
  readonly status: number;

  constructor(reasonCode: string, status = 503) {
    super(reasonCode);
    this.name = "SpiritFlixAdminTransactionError";
    this.reasonCode = reasonCode;
    this.status = status;
  }
}

type VerifiedState = {
  schema: string;
  state: unknown;
};

type TransactionInput<TSnapshot, TResult> = {
  approvalId: string;
  binding: SpiritFlixAdminApprovalBinding;
  capture: () => Promise<TSnapshot>;
  mutate: () => Promise<TResult>;
  rollback: (snapshot: TSnapshot, result: TResult | undefined) => Promise<void>;
  verify: (result: TResult) => Promise<VerifiedState>;
};

type SpiritFlixAdminParticipantOutput = Omit<
  SpiritFlixAdminParticipantInvocation,
  "acknowledgement"
>;

function invocation(
  consumer: SpiritFlixAdminParticipantInvocation["consumer"],
  approvalId: string,
  generation: number,
  resultHash: string,
): SpiritFlixAdminParticipantOutput {
  const body = {
    approval_id: approvalId,
    completed_at: new Date().toISOString(),
    consumer,
    generation,
    invocation_id: `spiritflix-${consumer}-${randomUUID()}`,
    outcome: "accepted",
    output_id: `spiritflix-${consumer}-output-${randomUUID()}`,
    result_hash: resultHash,
  } as const;
  return {
    ...body,
    output_hash: hashSpiritFlixAdminState({
      schema: "spiritflix-admin-participant-output/v2",
      state: body,
    }),
  };
}

function acknowledgeInvocation(
  output: SpiritFlixAdminParticipantOutput,
  consumerInvocationId: string,
): SpiritFlixAdminParticipantInvocation {
  if (!consumerInvocationId || !output.output_hash || !output.output_id) {
    throw new SpiritFlixAdminTransactionError("spiritflix_admin_acknowledgement_invalid", 409);
  }
  return {
    ...output,
    acknowledgement: {
      acknowledgement_id: `spiritflix-ack-${randomUUID()}`,
      consumer_invocation_id: consumerInvocationId,
      invocation_id: output.invocation_id,
      output_hash: output.output_hash,
      output_id: output.output_id,
      consumed: true,
    },
  };
}

async function invokeReviewer(
  artifact: { result_hash: string; result_schema: string; state: unknown; target: string; writer: unknown },
  approvalId: string,
  generation: number,
): Promise<SpiritFlixAdminParticipantOutput> {
  const independentlyComputed = hashSpiritFlixAdminState({ schema: artifact.result_schema, state: artifact.state });
  if (!artifact.result_hash.match(/^[a-f0-9]{64}$/) || independentlyComputed !== artifact.result_hash) {
    throw new SpiritFlixAdminTransactionError("spiritflix_admin_review_rejected", 409);
  }
  return invocation("spiritflix-admin-reviewer", approvalId, generation, artifact.result_hash);
}

async function invokeVerifier<TResult>(
  verify: (result: TResult) => Promise<VerifiedState>,
  result: TResult,
  approvalId: string,
  generation: number,
): Promise<{ invocation: SpiritFlixAdminParticipantOutput; resultHash: string; resultSchema: string; state: unknown }> {
  const verified = await verify(result);
  if (!verified || typeof verified.schema !== "string" || !verified.schema || verified.state === undefined) {
    throw new SpiritFlixAdminTransactionError("spiritflix_admin_verification_invalid", 409);
  }
  const resultHash = hashSpiritFlixAdminState({ schema: verified.schema, state: verified.state });
  return {
    invocation: invocation("spiritflix-admin-verifier", approvalId, generation, resultHash),
    resultHash,
    resultSchema: verified.schema,
    state: verified.state,
  };
}

async function invokeEvidenceRecorder(
  resultHash: string,
  resultSchema: string,
  state: unknown,
  approvalId: string,
  generation: number,
  consumedOutputs: SpiritFlixAdminParticipantOutput[],
): Promise<SpiritFlixAdminParticipantOutput> {
  const projection = JSON.stringify({ result_hash: resultHash, result_schema: resultSchema });
  if (/token|password|authorization|cookie/i.test(projection)) {
    throw new SpiritFlixAdminTransactionError("spiritflix_admin_evidence_redaction_failed", 409);
  }
  // The recorder creates its own digest and invocation. It does not copy the
  // verifier object or reuse the reviewer's identity.
  if (hashSpiritFlixAdminState({ schema: resultSchema, state }) !== resultHash) {
    throw new SpiritFlixAdminTransactionError("spiritflix_admin_evidence_hash_mismatch", 409);
  }
  if (
    consumedOutputs.length !== 2 ||
    new Set(consumedOutputs.map((item) => item.invocation_id)).size !== 2 ||
    consumedOutputs.some(
      (item) => item.result_hash !== resultHash || !item.output_id || !item.output_hash,
    )
  ) {
    throw new SpiritFlixAdminTransactionError("spiritflix_admin_evidence_inputs_invalid", 409);
  }
  return invocation("evidence-recorder", approvalId, generation, resultHash);
}

function evidence(
  resultHash: string,
  resultSchema: string,
  participantInvocations: SpiritFlixAdminParticipantInvocation[],
): SpiritFlixAdminFinalizationEvidence {
  return {
    participant_invocations: participantInvocations,
    redaction_verdict: "passed",
    result_hash: resultHash,
    result_schema: resultSchema,
  };
}

async function compensateAfterRollback(
  input: TransactionInput<unknown, unknown>,
  generation: number,
  finalization: SpiritFlixAdminFinalizationEvidence,
): Promise<void> {
  const compensation = await compensateSpiritFlixAdminApproval(
    input.approvalId,
    input.binding.action,
    input.binding.target,
    input.binding.plan,
    generation,
    finalization,
  );
  if (!compensation.ok) {
    throw new SpiritFlixAdminTransactionError(`spiritflix_admin_compensation_failed:${compensation.reason}`);
  }
}

export async function runApprovedSpiritFlixAdminMutation<TSnapshot, TResult>(
  input: TransactionInput<TSnapshot, TResult>,
): Promise<{ evidence: SpiritFlixAdminFinalizationEvidence; result: TResult }> {
  // Capture must complete before approval consumption. A writer that cannot
  // establish a compensating checkpoint never enters the consuming state.
  const snapshot = await input.capture();
  const consumed = await consumeSpiritFlixAdminApproval(
    input.approvalId,
    input.binding.action,
    input.binding.target,
    input.binding.plan,
  );
  if (!consumed.ok) throw new SpiritFlixAdminTransactionError(consumed.reason, 422);
  const generation = Number(consumed.value.generation);

  let result: TResult | undefined;
  try {
    result = await input.mutate();
    const verified = await invokeVerifier(input.verify, result, input.approvalId, generation);
    const reviewer = await invokeReviewer({
      result_hash: verified.resultHash,
      result_schema: verified.resultSchema,
      state: verified.state,
      target: input.binding.target,
      writer: input.binding.plan.writer,
    }, input.approvalId, generation);
    const recorder = await invokeEvidenceRecorder(
      verified.resultHash,
      verified.resultSchema,
      verified.state,
      input.approvalId,
      generation,
      [reviewer, verified.invocation],
    );
    const recorderInvocationId = recorder.invocation_id;
    const finalizerInvocationId = `spiritflix-authority-finalizer-${randomUUID()}`;
    const finalization = evidence(
      verified.resultHash,
      verified.resultSchema,
      [
        acknowledgeInvocation(reviewer, recorderInvocationId),
        acknowledgeInvocation(verified.invocation, recorderInvocationId),
        acknowledgeInvocation(recorder, finalizerInvocationId),
      ],
    );
    const finalized = await finalizeSpiritFlixAdminApproval(
      input.approvalId,
      input.binding.action,
      input.binding.target,
      input.binding.plan,
      generation,
      "succeeded",
      finalization,
    );
    if (!finalized.ok) {
      await input.rollback(snapshot, result);
      await compensateAfterRollback(input as TransactionInput<unknown, unknown>, generation, finalization);
      throw new SpiritFlixAdminTransactionError(`spiritflix_admin_finalization_failed:${finalized.reason}`);
    }
    return { evidence: finalization, result };
  } catch (error) {
    if (error instanceof SpiritFlixAdminTransactionError && error.reasonCode.startsWith("spiritflix_admin_finalization_failed:")) {
      throw error;
    }

    const failureHash = hashSpiritFlixAdminState({
      error: error instanceof Error ? error.message : "spiritflix_admin_mutation_failed",
      target: input.binding.target,
      writer: input.binding.plan.writer,
    });
    const failureEvidence = evidence(failureHash, "spiritflix-admin-failure/v1", []);
    let rollbackFailed = false;
    try {
      await input.rollback(snapshot, result);
    } catch {
      rollbackFailed = true;
    }
    const finalized = await finalizeSpiritFlixAdminApproval(
      input.approvalId,
      input.binding.action,
      input.binding.target,
      input.binding.plan,
      generation,
      "failed",
      failureEvidence,
    );
    if (!finalized.ok) {
      await compensateAfterRollback(input as TransactionInput<unknown, unknown>, generation, failureEvidence);
    }
    const reason = error instanceof Error ? error.message : "spiritflix_admin_mutation_failed";
    throw new SpiritFlixAdminTransactionError(
      rollbackFailed ? `spiritflix_admin_rollback_failed:${reason}` : reason,
      error instanceof SpiritFlixAdminTransactionError ? error.status : 409,
    );
  }
}
