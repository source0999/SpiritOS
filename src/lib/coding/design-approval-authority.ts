import "server-only";

import { spawn } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { join } from "node:path";
import {
  type AuthorityRuntimeIdentity,
  resolveAuthorityRuntimeIdentity,
} from "@/lib/coding/authority-runtime-identity";
import {
  buildDesignWritebackArtifact,
  type DesignWritebackArtifact,
} from "@/lib/coding/design-writeback-contract";

const DESIGN_PLUGIN = "design-studio";

export type DesignPreviewBinding = {
  artifact_id: string;
  content_hash: string;
  context: string;
  generation: number;
  preview_id: string;
  source_head: string;
  target: string;
};

export type DesignApprovalBinding = DesignPreviewBinding & {
  approval_id: string;
  consumer: "design-writeback";
  operation: "design_writeback";
};

export const DESIGN_PARTICIPANTS = [
  "design-reviewer",
  "design-verifier",
  "evidence-recorder",
] as const;

export type DesignParticipantRecord = {
  acknowledgement: {
    acknowledgement_id: string;
    artifact_hash: string;
    consumed: true;
    consumer_invocation_id: string;
    output_hash: string;
    output_id: string;
    producer_invocation_id: string;
    recorded_at: string;
  };
  artifact_hash: string;
  checks: string[];
  invocation_id: string;
  invoked_at: string;
  output_hash: string;
  output_id: string;
  participant: (typeof DESIGN_PARTICIPANTS)[number];
  status: "accepted" | "recorded" | "rejected" | "verified";
};

export type DesignParticipantOutput = Omit<
  DesignParticipantRecord,
  "acknowledgement" | "output_hash"
>;

export type DesignParticipantProducerOutput = DesignParticipantOutput & {
  output_hash: string;
};

export function acknowledgeDesignParticipantOutput(
  output: DesignParticipantProducerOutput,
  consumerInvocationId: string,
): DesignParticipantRecord {
  const { output_hash, ...body } = output;
  if (!consumerInvocationId.trim() || output_hash !== hashDesignParticipantOutput(body)) {
    throw new Error("design_participant_acknowledgement_invalid");
  }
  return {
    ...output,
    acknowledgement: {
      acknowledgement_id: `design-ack-${randomUUID()}`,
      artifact_hash: output.artifact_hash,
      consumed: true,
      consumer_invocation_id: consumerInvocationId,
      output_hash: output.output_hash,
      output_id: output.output_id,
      producer_invocation_id: output.invocation_id,
      recorded_at: new Date().toISOString(),
    },
  };
}

function stableJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => `${JSON.stringify(key)}:${stableJson(item)}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function withoutApprovalId(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(withoutApprovalId);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([key]) => key !== "approval_id")
        .map(([key, item]) => [key, withoutApprovalId(item)]),
    );
  }
  return value;
}

export function hashApprovalContent(value: unknown) {
  return createHash("sha256").update(stableJson(withoutApprovalId(value)), "utf8").digest("hex");
}

export function hashDesignParticipantOutput(output: DesignParticipantOutput) {
  return hashApprovalContent(output);
}

async function invokeAuthority(
  identity: AuthorityRuntimeIdentity,
  command: string,
  input: Record<string, unknown>,
) {
  const authorityScript = join(identity.root, "scripts", "approval-authority.py");
  const result = await new Promise<{ code: number; text: string }>((resolve) => {
    const child = spawn("python3", [authorityScript, command], {
      cwd: identity.root,
      env: { ...process.env, SPIRITOS_APPROVAL_ROOT: identity.root },
      stdio: ["pipe", "pipe", "ignore"],
    });
    let text = "";
    child.stdout.on("data", (chunk) => (text += chunk));
    let settled = false;
    child.on("error", () => {
      if (!settled) {
        settled = true;
        resolve({ code: 1, text: "" });
      }
    });
    child.on("close", (code) => {
      if (!settled) {
        settled = true;
        resolve({ code: code ?? 1, text });
      }
    });
    child.stdin.end(JSON.stringify(input));
  });
  try {
    const parsed = JSON.parse(result.text);
    return result.code === 0
      ? { ok: true as const, value: parsed }
      : { ok: false as const, reason: String(parsed.reason ?? "approval_issuer_unavailable") };
  } catch {
    return { ok: false as const, reason: "approval_issuer_unavailable" };
  }
}

function commonBinding(
  identity: AuthorityRuntimeIdentity,
  binding: Pick<DesignPreviewBinding, "content_hash" | "context" | "source_head" | "target">,
) {
  return {
    content_hash: binding.content_hash,
    context: binding.context,
    plugin: DESIGN_PLUGIN,
    repository: identity.repository,
    root: identity.root,
    source_head: binding.source_head,
    target: binding.target,
    worktree: identity.worktree,
  };
}

export async function persistDesignPreview(input: { content: unknown }) {
  const artifact = buildDesignWritebackArtifact(input.content);
  if (!artifact.ok) return artifact;
  const identity = await resolveAuthorityRuntimeIdentity();
  const source_head = identity.sourceHead;
  const persisted = await invokeAuthority(identity, "persist-preview", {
    ...commonBinding(identity, {
      content_hash: artifact.value.artifact_hash,
      context: artifact.value.context,
      source_head,
      target: artifact.value.target,
    }),
  });
  if (!persisted.ok) return persisted;
  return {
    ok: true as const,
    value: {
      artifact_id: artifact.value.artifact_id,
      content_hash: artifact.value.artifact_hash,
      context: artifact.value.context,
      generation: Number(persisted.value.generation),
      preview_id: String(persisted.value.preview_id),
      source_head,
      target: artifact.value.target,
    } satisfies DesignPreviewBinding,
  };
}

export async function resolveDesignWritebackPreview(previewId: string, expectedGeneration: number) {
  const identity = await resolveAuthorityRuntimeIdentity();
  const loaded = await invokeAuthority(identity, "lookup-preview", { preview_id: previewId });
  if (!loaded.ok) return loaded;
  if (Number(loaded.value.generation) !== expectedGeneration) return { ok: false as const, reason: "approval_generation_mismatch" };
  if (loaded.value.state !== "previewed") return { ok: false as const, reason: "approval_not_approved" };
  if (loaded.value.repository !== identity.repository || loaded.value.worktree !== identity.worktree || loaded.value.root !== identity.root || loaded.value.plugin !== DESIGN_PLUGIN) {
    return { ok: false as const, reason: "approval_worktree_mismatch" };
  }
  const source_head = identity.sourceHead;
  if (loaded.value.source_head !== source_head) return { ok: false as const, reason: "approval_source_mismatch" };
  return {
    ok: true as const,
    value: {
      artifact_id: `design-writeback-${String(loaded.value.content_hash)}`,
      content_hash: String(loaded.value.content_hash), context: String(loaded.value.context), generation: Number(loaded.value.generation),
      preview_id: String(loaded.value.id), source_head: String(loaded.value.source_head), target: String(loaded.value.target),
    } satisfies DesignPreviewBinding,
  };
}

export async function issueDesignWritebackApproval(preview: DesignPreviewBinding, ttlMinutes = 30) {
  const identity = await resolveAuthorityRuntimeIdentity();
  if (
    preview.artifact_id !== `design-writeback-${preview.content_hash}` ||
    preview.source_head !== identity.sourceHead
  ) {
    return { ok: false as const, reason: "approval_artifact_binding_mismatch" };
  }
  const expires_at = new Date(Date.now() + Math.min(Math.max(ttlMinutes, 1), 60) * 60_000).toISOString();
  const issued = await invokeAuthority(identity, "issue", {
    consumer: "design-writeback",
    expires_at,
    operation: "design_writeback",
    expected_generation: String(preview.generation),
    preview_id: preview.preview_id,
  });
  if (!issued.ok) return issued;
  return {
    ok: true as const,
    value: {
      ...preview,
      approval_id: String(issued.value.approval_id),
      consumer: "design-writeback" as const,
      operation: "design_writeback" as const,
    } satisfies DesignApprovalBinding,
  };
}

export async function rejectDesignWritebackPreview(preview: DesignPreviewBinding) {
  const identity = await resolveAuthorityRuntimeIdentity();
  return invokeAuthority(identity, "transition-preview", { expected_generation: String(preview.generation), preview_id: preview.preview_id, state: "rejected" });
}

export async function loadDesignWritebackApproval(approvalId: string) {
  const identity = await resolveAuthorityRuntimeIdentity();
  const loaded = await invokeAuthority(identity, "lookup", { approval_id: approvalId });
  if (!loaded.ok) return loaded;
  if (loaded.value.consumer !== "design-writeback" || loaded.value.operation !== "design_writeback") {
    return { ok: false as const, reason: "approval_consumer_mismatch" };
  }
  if (
    loaded.value.repository !== identity.repository ||
    loaded.value.worktree !== identity.worktree ||
    loaded.value.root !== identity.root ||
    loaded.value.plugin !== DESIGN_PLUGIN
  ) {
    return { ok: false as const, reason: "approval_worktree_mismatch" };
  }
  if (loaded.value.source_head !== identity.sourceHead) {
    return { ok: false as const, reason: "approval_source_mismatch" };
  }
  if (loaded.value.state !== "approved") {
    return { ok: false as const, reason: "approval_not_approved" };
  }
  return {
    ok: true as const,
    value: {
      approval_id: String(loaded.value.id),
      artifact_id: `design-writeback-${String(loaded.value.content_hash)}`,
      consumer: "design-writeback" as const,
      content_hash: String(loaded.value.content_hash),
      context: String(loaded.value.context),
      generation: Number(loaded.value.generation),
      operation: "design_writeback" as const,
      preview_id: String(loaded.value.preview),
      source_head: String(loaded.value.source_head),
      target: String(loaded.value.target),
    } satisfies DesignApprovalBinding,
  };
}

export async function consumeDesignWritebackApproval(
  approval: DesignApprovalBinding,
  artifact: DesignWritebackArtifact,
) {
  if (
    artifact.artifact_hash !== approval.content_hash ||
    artifact.artifact_id !== approval.artifact_id
  ) {
    return { ok: false as const, reason: "approval_content_hash_mismatch" };
  }
  if (artifact.context !== approval.context) {
    return { ok: false as const, reason: "approval_context_mismatch" };
  }
  if (artifact.target !== approval.target) {
    return { ok: false as const, reason: "approval_target_mismatch" };
  }
  const identity = await resolveAuthorityRuntimeIdentity();
  const source_head = identity.sourceHead;
  return invokeAuthority(identity, "consume", {
    ...commonBinding(identity, { ...approval, source_head }),
    approval_id: approval.approval_id,
    consumer: approval.consumer,
    generation: String(approval.generation),
    operation: approval.operation,
    preview: approval.preview_id,
  });
}

export function redactedDesignWritebackEvidence(
  approval: DesignApprovalBinding,
  input: {
    artifact_hash: string;
    participant_records: DesignParticipantRecord[];
    receipt: {
      acceptance_id: string;
      content_hash: string;
      expected_state: "absent";
      result_state: "rejected" | "written_verified";
      target: string;
      trace_id: string;
    };
  },
) {
  const participants = input.participant_records.map((record) => record.participant);
  const invocationIds = new Set(input.participant_records.map((record) => record.invocation_id));
  const outputIds = new Set(input.participant_records.map((record) => record.output_id));
  const acknowledgementIds = new Set(
    input.participant_records.map((record) => record.acknowledgement.acknowledgement_id),
  );
  if (
    input.artifact_hash !== approval.content_hash ||
    input.receipt.target !== approval.target ||
    input.receipt.trace_id !== approval.context ||
    participants.length !== DESIGN_PARTICIPANTS.length ||
    !DESIGN_PARTICIPANTS.every((participant) => participants.includes(participant)) ||
    invocationIds.size !== DESIGN_PARTICIPANTS.length ||
    outputIds.size !== DESIGN_PARTICIPANTS.length ||
    acknowledgementIds.size !== DESIGN_PARTICIPANTS.length ||
    input.participant_records.some(
      (record) =>
        record.artifact_hash !== input.artifact_hash ||
        !/^[0-9a-f]{64}$/.test(record.output_hash) ||
        record.output_hash !== hashDesignParticipantOutput({
          artifact_hash: record.artifact_hash,
          checks: record.checks,
          invocation_id: record.invocation_id,
          invoked_at: record.invoked_at,
          output_id: record.output_id,
          participant: record.participant,
          status: record.status,
        }) ||
        record.acknowledgement.consumed !== true ||
        record.acknowledgement.artifact_hash !== record.artifact_hash ||
        record.acknowledgement.producer_invocation_id !== record.invocation_id ||
        record.acknowledgement.output_id !== record.output_id ||
        record.acknowledgement.output_hash !== record.output_hash ||
        !record.acknowledgement.consumer_invocation_id ||
        record.checks.length === 0,
    )
  ) {
    throw new Error("design_participant_evidence_mismatch");
  }
  return {
    artifact_hash: input.artifact_hash,
    generation: approval.generation,
    participant_records: input.participant_records,
    receipt: {
      acceptance_hash: hashApprovalContent(input.receipt.acceptance_id),
      content_hash: input.receipt.content_hash,
      expected_state: input.receipt.expected_state,
      result_state: input.receipt.result_state,
      target_hash: hashApprovalContent(input.receipt.target),
      trace_hash: hashApprovalContent(input.receipt.trace_id),
    },
    redacted: true,
  };
}

export async function finalizeDesignWritebackApproval(
  approval: DesignApprovalBinding,
  result: {
    artifact: DesignWritebackArtifact;
    participant_records: DesignParticipantRecord[];
    receipt: {
      acceptance_id: string;
      content_hash: string;
      expected_state: "absent";
      result_state: "rejected" | "written_verified";
      target: string;
      trace_id: string;
    };
    result_id?: string;
    status: "failed" | "succeeded";
  },
) {
  if (
    result.artifact.artifact_hash !== approval.content_hash ||
    result.artifact.artifact_hash !== hashApprovalContent(result.artifact.binding) ||
    result.artifact.artifact_id !== approval.artifact_id ||
    result.artifact.context !== approval.context ||
    result.artifact.target !== approval.target ||
    result.artifact.note_content_hash !==
      result.artifact.binding.write_contract.result_state.content_hash ||
    result.receipt.content_hash !== result.artifact.note_content_hash ||
    result.receipt.expected_state !==
      result.artifact.binding.write_contract.expected_state.target ||
    JSON.stringify(result.artifact.binding).includes('"approval_id"')
  ) {
    return { ok: false as const, reason: "approval_artifact_binding_mismatch" };
  }
  let evidence: ReturnType<typeof redactedDesignWritebackEvidence>;
  try {
    evidence = redactedDesignWritebackEvidence(approval, {
      artifact_hash: result.artifact.artifact_hash,
      participant_records: result.participant_records,
      receipt: result.receipt,
    });
  } catch (error) {
    return {
      ok: false as const,
      reason: error instanceof Error ? error.message : "design_participant_evidence_mismatch",
    };
  }
  const successfulStatuses = new Map(
    result.participant_records.map((record) => [record.participant, record.status]),
  );
  if (
    result.status === "succeeded" &&
    (result.receipt.result_state !== "written_verified" ||
      !/^[0-9a-f]{64}$/.test(result.receipt.content_hash) ||
      successfulStatuses.get("design-reviewer") !== "accepted" ||
      successfulStatuses.get("design-verifier") !== "verified" ||
      successfulStatuses.get("evidence-recorder") !== "recorded")
  ) {
    return { ok: false as const, reason: "design_success_evidence_incomplete" };
  }
  if (result.status === "failed" && result.receipt.result_state !== "rejected") {
    return { ok: false as const, reason: "design_failure_evidence_inconsistent" };
  }
  const identity = await resolveAuthorityRuntimeIdentity();
  const source_head = identity.sourceHead;
  const finalized = await invokeAuthority(identity, "finalize", {
    ...commonBinding(identity, { ...approval, source_head }),
    approval_id: approval.approval_id,
    consumer: approval.consumer,
    evidence: stableJson(evidence),
    generation: String(approval.generation),
    operation: approval.operation,
    preview: approval.preview_id,
    result_id: result.result_id ?? `design-writeback-${randomUUID()}`,
    status: result.status,
  });
  if (!finalized.ok) return finalized;
  return {
    ok: true as const,
    value: {
      artifact_hash: result.artifact.artifact_hash,
      generation: approval.generation,
      participant_records: result.participant_records,
      redacted: true,
      result_id_hash: hashApprovalContent(String(finalized.value.result_id)),
      state: String(finalized.value.state),
    },
  };
}
