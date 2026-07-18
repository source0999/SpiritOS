/// <reference types="vitest/globals" />

import {
  DESIGN_PARTICIPANTS,
  hashDesignParticipantOutput,
  redactedDesignWritebackEvidence,
  type DesignApprovalBinding,
  type DesignParticipantRecord,
} from "../design-approval-authority";

const artifactHash = "a".repeat(64);
const approval: DesignApprovalBinding = {
  approval_id: "apr_design_authority_test",
  artifact_id: `design-writeback-${artifactHash}`,
  consumer: "design-writeback",
  content_hash: artifactHash,
  context: "trace-private",
  generation: 7,
  operation: "design_writeback",
  preview_id: "prv_design_authority_test",
  source_head: "b".repeat(40),
  target: "design-memory/2026-07-01/design_run_001.md",
};

const participantRecords = DESIGN_PARTICIPANTS.map((participant, index) => {
  const output = {
    artifact_hash: artifactHash,
    checks: [`${participant}_check`],
    invocation_id: `invocation-${index}`,
    invoked_at: "2026-07-17T20:00:00.000Z",
    output_id: `output-${index}`,
    participant,
    status:
      participant === "design-reviewer"
        ? "accepted" as const
        : participant === "design-verifier"
          ? "verified" as const
          : "recorded" as const,
  };
  return { ...output, output_hash: hashDesignParticipantOutput(output) };
}) satisfies DesignParticipantRecord[];

function evidence(records = participantRecords) {
  return redactedDesignWritebackEvidence(approval, {
    artifact_hash: artifactHash,
    participant_records: records,
    receipt: {
      acceptance_id: "acceptance-private",
      content_hash: "c".repeat(64),
      expected_state: "absent",
      result_state: "written_verified",
      target: approval.target,
      trace_id: approval.context,
    },
  });
}

describe("Design writeback participant evidence", () => {
  it("records three distinct invocations and outputs over one immutable artifact", () => {
    const result = evidence();
    expect(result.participant_records.map((record) => record.participant)).toEqual([
      ...DESIGN_PARTICIPANTS,
    ]);
    expect(new Set(result.participant_records.map((record) => record.invocation_id)).size).toBe(3);
    expect(new Set(result.participant_records.map((record) => record.output_id)).size).toBe(3);
    expect(new Set(result.participant_records.map((record) => record.artifact_hash))).toEqual(
      new Set([artifactHash]),
    );
  });

  it("rejects copied participant identities", () => {
    const copied = participantRecords.map((record) => ({ ...record }));
    copied[1].invocation_id = copied[0].invocation_id;
    copied[1].output_hash = hashDesignParticipantOutput({
      artifact_hash: copied[1].artifact_hash,
      checks: copied[1].checks,
      invocation_id: copied[1].invocation_id,
      invoked_at: copied[1].invoked_at,
      output_id: copied[1].output_id,
      participant: copied[1].participant,
      status: copied[1].status,
    });
    expect(() => evidence(copied)).toThrow("design_participant_evidence_mismatch");
  });

  it("creates durable evidence without approval IDs, targets, traces, or acceptance values", () => {
    const serialized = JSON.stringify(evidence());
    expect(serialized).toContain('"redacted":true');
    expect(serialized).toContain('"generation":7');
    expect(serialized).toContain(artifactHash);
    expect(serialized).not.toContain(approval.approval_id);
    expect(serialized).not.toContain(approval.target);
    expect(serialized).not.toContain("trace-private");
    expect(serialized).not.toContain("acceptance-private");
  });
});
