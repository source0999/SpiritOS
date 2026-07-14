/// <reference types="vitest/globals" />
import { consumeDesignWritebackApproval, finalizeDesignWritebackApproval, loadDesignWritebackApproval } from "../design-approval-authority";
import { writeApprovedDesignMemoryNote } from "../design-studio-obsidian-writeback";
import { runDesignStudioApprovedWriteback } from "../design-studio-approved-writeback-runtime";

vi.mock("../design-approval-authority", () => ({
  consumeDesignWritebackApproval: vi.fn(), finalizeDesignWritebackApproval: vi.fn(), loadDesignWritebackApproval: vi.fn(),
}));
vi.mock("../design-studio-obsidian-writeback", () => ({ writeApprovedDesignMemoryNote: vi.fn() }));

const approval = {
  approval_id: "apr_design_runtime",
  consumer: "design-writeback" as const,
  content_hash: "content", context: "context", generation: 3,
  operation: "design_writeback" as const, preview_id: "prv_design_runtime",
  source_head: "a".repeat(40), target: "/coding/design-demo",
};
const request = {
  acceptance_id: "acceptance-private",
  approval_id: approval.approval_id,
  accepted_run: { acceptance_id: "acceptance-private", approved_by: "human" as const, run_status: "accepted" as const, trace_id: "trace-private" },
  gate: { anti_template_originality_status: "pass" as const, critic_status: "pass" as const, desktop_proof: "pass" as const, mobile_proof: "pass" as const, run_status: "verified" as const, trace_id: "trace-private" },
  payload: { approval_id: approval.approval_id, target_surface: "/coding/design-demo", trace_id: "trace-private" },
} as never;

describe("Design Studio approved writeback runtime", () => {
  beforeEach(() => {
    vi.mocked(loadDesignWritebackApproval).mockReset(); vi.mocked(consumeDesignWritebackApproval).mockReset(); vi.mocked(finalizeDesignWritebackApproval).mockReset(); vi.mocked(writeApprovedDesignMemoryNote).mockReset();
    vi.mocked(loadDesignWritebackApproval).mockResolvedValue({ ok: true, value: approval });
    vi.mocked(consumeDesignWritebackApproval).mockResolvedValue({ ok: true, value: {} });
    vi.mocked(writeApprovedDesignMemoryNote).mockReturnValue({ note: "ok", path: "/state/design-memory.md", status: "written" });
    vi.mocked(finalizeDesignWritebackApproval).mockResolvedValue({ ok: true, value: { acknowledgement_consumers: ["design-writeback", "design-reviewer", "design-verifier", "evidence-recorder"], generation: 3, redacted: true } });
  });

  it("finalizes the consumed approval with server-built redacted receipt data", async () => {
    const result = await runDesignStudioApprovedWriteback(request);
    expect(finalizeDesignWritebackApproval).toHaveBeenCalledWith(approval, expect.objectContaining({
      receipt: { acceptance_id: "acceptance-private", result_status: "written", target: "/coding/design-demo", trace_id: "trace-private" },
      status: "succeeded",
    }));
    expect(result).toMatchObject({
      approval_receipt: { acknowledgement_consumers: ["design-writeback", "design-reviewer", "design-verifier", "evidence-recorder"], generation: 3, redacted: true },
      status: "written", write_invoked: true,
    });
    expect(JSON.stringify(result)).not.toContain(approval.approval_id);
  });
});
