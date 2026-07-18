/// <reference types="vitest/globals" />

import {
  consumeDesignWritebackApproval,
  finalizeDesignWritebackApproval,
  loadDesignWritebackApproval,
} from "../design-approval-authority";
import {
  rollbackApprovedDesignMemoryNote,
  verifyApprovedDesignMemoryNote,
  writeApprovedDesignMemoryNote,
} from "../design-studio-obsidian-writeback";
import { runDesignStudioApprovedWriteback } from "../design-studio-approved-writeback-runtime";
import { buildDesignWritebackArtifact } from "../design-writeback-contract";

vi.mock("../design-approval-authority", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../design-approval-authority")>()),
  consumeDesignWritebackApproval: vi.fn(),
  finalizeDesignWritebackApproval: vi.fn(),
  loadDesignWritebackApproval: vi.fn(),
}));
vi.mock("../design-studio-obsidian-writeback", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../design-studio-obsidian-writeback")>()),
  rollbackApprovedDesignMemoryNote: vi.fn(),
  verifyApprovedDesignMemoryNote: vi.fn(),
  writeApprovedDesignMemoryNote: vi.fn(),
}));

const request = {
  approval_id: "apr_design_runtime",
  accepted_run: {
    acceptance_id: "acceptance-private",
    approved_by: "human" as const,
    run_status: "accepted" as const,
    trace_id: "trace-private",
  },
  gate: {
    anti_template_originality_status: "pass" as const,
    critic_status: "pass" as const,
    desktop_proof: "pass" as const,
    failed_verifier_probes: [],
    fake_go_flags: [],
    mobile_proof: "pass" as const,
    run_status: "verified" as const,
    trace_id: "trace-private",
    unconsumed_packets: [],
  },
  payload: {
    approval_id: "apr_design_runtime",
    created_at: "2026-07-01T23:15:00.000Z",
    critic_verdict: "pass" as const,
    design_run_id: "design_run_001",
    files_changed: ["src/app/coding/design-demo/page.tsx"],
    obsidian_context_refs: ["design-brain/homepage-patterns"],
    project_specific_motif: "SpiritOS preview workbench",
    prompt_summary: "Persist only the exact approved verified artifact.",
    reference_dna_refs: ["reference-upload-preview-local"],
    repair_count: 1,
    reusable_pattern_notes: ["Pair desktop and mobile proof."],
    screenshot_hashes: ["desktop_hash_001", "mobile_hash_001"],
    screenshot_proofs: [
      {
        captured_at: "2026-07-01T23:12:00.000Z",
        capture_source: "playwright_desktop" as const,
        content_hash: "desktop_hash_001",
        viewport: { height: 900, width: 1440 },
      },
      {
        captured_at: "2026-07-01T23:13:00.000Z",
        capture_source: "playwright_mobile" as const,
        content_hash: "mobile_hash_001",
        viewport: { height: 844, width: 390 },
      },
    ],
    style_family_blend: ["SpiritOS glass console", "dense product workbench"],
    target_surface: "/coding/design-demo",
    trace_id: "trace-private",
  },
};
const artifactResult = buildDesignWritebackArtifact({
  accepted_run: request.accepted_run,
  gate: request.gate,
  payload: request.payload,
});
if (!artifactResult.ok) throw new Error(artifactResult.reason);
const artifact = artifactResult.value;
const approval = {
  approval_id: request.approval_id,
  artifact_id: artifact.artifact_id,
  consumer: "design-writeback" as const,
  content_hash: artifact.artifact_hash,
  context: artifact.context,
  generation: 3,
  operation: "design_writeback" as const,
  preview_id: "prv_design_runtime",
  source_head: "a".repeat(40),
  target: artifact.target,
};
const written = {
  content_hash: artifact.note_content_hash,
  expected_state: "absent" as const,
  note: "ok",
  path: `/home/source/.local/state/spiritos/design-vault/${artifact.target}`,
  result_state: "written_verified" as const,
  status: "written" as const,
  verified: true as const,
};

describe("Design Studio approved writeback runtime", () => {
  beforeEach(() => {
    vi.mocked(loadDesignWritebackApproval).mockReset();
    vi.mocked(consumeDesignWritebackApproval).mockReset();
    vi.mocked(finalizeDesignWritebackApproval).mockReset();
    vi.mocked(writeApprovedDesignMemoryNote).mockReset();
    vi.mocked(rollbackApprovedDesignMemoryNote).mockReset();
    vi.mocked(verifyApprovedDesignMemoryNote).mockReset();
    vi.mocked(loadDesignWritebackApproval).mockResolvedValue({ ok: true, value: approval });
    vi.mocked(consumeDesignWritebackApproval).mockResolvedValue({ ok: true, value: { state: "consuming" } });
    vi.mocked(writeApprovedDesignMemoryNote).mockReturnValue(written);
    vi.mocked(rollbackApprovedDesignMemoryNote).mockReturnValue({ status: "rolled_back" });
    vi.mocked(verifyApprovedDesignMemoryNote).mockReturnValue({
      content_hash: artifact.note_content_hash,
      status: "verified",
    });
    vi.mocked(finalizeDesignWritebackApproval).mockResolvedValue({
      ok: true,
      value: {
        artifact_hash: artifact.artifact_hash,
        generation: 3,
        participant_records: [],
        redacted: true,
        result_id_hash: "d".repeat(64),
        state: "consumed",
      },
    });
  });

  it("consumes before writing and finalizes only after independent review, verification, and evidence", async () => {
    const result = await runDesignStudioApprovedWriteback(request);
    expect(consumeDesignWritebackApproval).toHaveBeenCalledWith(approval, artifact);
    expect(vi.mocked(consumeDesignWritebackApproval).mock.invocationCallOrder[0]).toBeLessThan(
      vi.mocked(writeApprovedDesignMemoryNote).mock.invocationCallOrder[0],
    );
    expect(vi.mocked(writeApprovedDesignMemoryNote).mock.invocationCallOrder[0]).toBeLessThan(
      vi.mocked(verifyApprovedDesignMemoryNote).mock.invocationCallOrder[0],
    );
    expect(verifyApprovedDesignMemoryNote).toHaveBeenCalledWith(written);
    expect(finalizeDesignWritebackApproval).toHaveBeenCalledWith(
      approval,
      expect.objectContaining({
        artifact,
        receipt: expect.objectContaining({
          content_hash: artifact.note_content_hash,
          expected_state: "absent",
          result_state: "written_verified",
          target: artifact.target,
        }),
        status: "succeeded",
      }),
    );
    expect(result.status).toBe("written");
    if (result.status !== "written") throw new Error(result.reasons.join(", "));
    expect(result.participant_records.map((record) => [record.participant, record.status])).toEqual([
      ["design-reviewer", "accepted"],
      ["design-verifier", "verified"],
      ["evidence-recorder", "recorded"],
    ]);
    expect(new Set(result.participant_records.map((record) => record.invocation_id)).size).toBe(3);
    expect(new Set(result.participant_records.map((record) => record.output_id)).size).toBe(3);
    expect(JSON.stringify(result.participant_records)).not.toContain(request.approval_id);
    expect(rollbackApprovedDesignMemoryNote).not.toHaveBeenCalled();
  });

  it("rolls the exact write back when approval finalization fails", async () => {
    vi.mocked(finalizeDesignWritebackApproval).mockResolvedValue({
      ok: false,
      reason: "approval_source_mismatch",
    });
    const result = await runDesignStudioApprovedWriteback(request);
    expect(result).toMatchObject({
      reasons: ["approval_source_mismatch"],
      rollback_status: "rolled_back",
      status: "rejected",
      write_invoked: true,
    });
    expect(rollbackApprovedDesignMemoryNote).toHaveBeenCalledWith(written);
  });

  it("cannot finalize success when the post-write content hash does not match the artifact", async () => {
    vi.mocked(writeApprovedDesignMemoryNote).mockReturnValue({
      ...written,
      content_hash: "e".repeat(64),
    });
    const result = await runDesignStudioApprovedWriteback(request);
    expect(result.status).toBe("rejected");
    expect(finalizeDesignWritebackApproval).toHaveBeenCalledWith(
      approval,
      expect.objectContaining({ status: "failed" }),
    );
    expect(finalizeDesignWritebackApproval).not.toHaveBeenCalledWith(
      approval,
      expect.objectContaining({ status: "succeeded" }),
    );
    expect(rollbackApprovedDesignMemoryNote).toHaveBeenCalled();
  });

  it("does not invoke a write unless the consuming transition succeeds", async () => {
    vi.mocked(consumeDesignWritebackApproval).mockResolvedValue({
      ok: false,
      reason: "approval_concurrent_consumption",
    });
    const result = await runDesignStudioApprovedWriteback(request);
    expect(result).toMatchObject({ status: "rejected", write_invoked: false });
    expect(writeApprovedDesignMemoryNote).not.toHaveBeenCalled();
    expect(finalizeDesignWritebackApproval).not.toHaveBeenCalled();
  });

  it("rejects a target or content mismatch before consuming", async () => {
    vi.mocked(loadDesignWritebackApproval).mockResolvedValue({
      ok: true,
      value: { ...approval, target: "design-memory/2026-07-01/other.md" },
    });
    const result = await runDesignStudioApprovedWriteback(request);
    expect(result).toMatchObject({
      reasons: ["approval_artifact_binding_mismatch"],
      status: "rejected",
      write_invoked: false,
    });
    expect(consumeDesignWritebackApproval).not.toHaveBeenCalled();
    expect(writeApprovedDesignMemoryNote).not.toHaveBeenCalled();
  });
});
