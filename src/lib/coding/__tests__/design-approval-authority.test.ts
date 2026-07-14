/// <reference types="vitest/globals" />
import {
  DESIGN_ACKNOWLEDGEMENT_CONSUMERS,
  designWritebackAcknowledgements,
  redactedDesignWritebackEvidence,
  type DesignApprovalBinding,
} from "../design-approval-authority";

const approval: DesignApprovalBinding = {
  approval_id: "apr_design_authority_test",
  consumer: "design-writeback",
  content_hash: "content-hash",
  context: "context-hash",
  generation: 7,
  operation: "design_writeback",
  preview_id: "prv_design_authority_test",
  source_head: "a".repeat(40),
  target: "/coding/design-demo",
};

describe("Design writeback acknowledgement envelope", () => {
  it("assigns every canonical acknowledgement the same server approval ID and generation", () => {
    const acknowledgements = designWritebackAcknowledgements(approval);
    expect(Object.keys(acknowledgements)).toEqual([...DESIGN_ACKNOWLEDGEMENT_CONSUMERS]);
    expect(Object.values(acknowledgements)).toEqual(
      DESIGN_ACKNOWLEDGEMENT_CONSUMERS.map(() => ({ approval_id: approval.approval_id, generation: approval.generation })),
    );
  });

  it("creates a durable evidence body without approval IDs, targets, traces, or acceptance values", () => {
    const evidence = JSON.stringify(redactedDesignWritebackEvidence(approval, {
      acceptance_id: "acceptance-private",
      result_status: "written",
      target: approval.target,
      trace_id: "trace-private",
    }));
    expect(evidence).toContain('"redacted":true');
    expect(evidence).toContain('"generation":7');
    expect(evidence).not.toContain(approval.approval_id);
    expect(evidence).not.toContain(approval.target);
    expect(evidence).not.toContain("trace-private");
    expect(evidence).not.toContain("acceptance-private");
  });
});
