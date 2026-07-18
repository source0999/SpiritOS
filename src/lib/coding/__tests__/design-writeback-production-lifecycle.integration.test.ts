/// <reference types="vitest/globals" />

import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const previewContent = {
  accepted_run: {
    acceptance_id: "acceptance-production-lifecycle",
    approved_by: "human",
    run_status: "accepted",
    trace_id: "trace-production-lifecycle",
  },
  gate: {
    anti_template_originality_status: "pass",
    critic_status: "pass",
    desktop_proof: "pass",
    failed_verifier_probes: [],
    fake_go_flags: [],
    mobile_proof: "pass",
    run_status: "verified",
    trace_id: "trace-production-lifecycle",
    unconsumed_packets: [],
  },
  payload: {
    approval_id: "",
    created_at: "2026-07-17T20:00:00.000Z",
    critic_verdict: "pass",
    design_run_id: "design_production_lifecycle",
    files_changed: ["src/app/coding/design-demo/page.tsx"],
    obsidian_context_refs: ["design-brain/production-lifecycle"],
    project_specific_motif: "SpiritOS approval lifecycle",
    prompt_summary: "Prove the real Design approval issuer and consumer path.",
    reference_dna_refs: ["reference-production-lifecycle"],
    repair_count: 0,
    reusable_pattern_notes: ["Bind one immutable artifact through every participant."],
    screenshot_hashes: ["desktop-production-hash", "mobile-production-hash"],
    screenshot_proofs: [
      {
        captured_at: "2026-07-17T19:58:00.000Z",
        capture_source: "playwright_desktop",
        content_hash: "desktop-production-hash",
        viewport: { height: 900, width: 1440 },
      },
      {
        captured_at: "2026-07-17T19:59:00.000Z",
        capture_source: "playwright_mobile",
        content_hash: "mobile-production-hash",
        viewport: { height: 844, width: 390 },
      },
    ],
    style_family_blend: ["SpiritOS glass console"],
    target_surface: "/coding/design-demo",
    trace_id: "trace-production-lifecycle",
  },
};

describe("Design writeback production authority lifecycle", () => {
  it("persists, issues, consumes, verifies, writes, and finalizes through the production modules", async () => {
    const stateRoot = mkdtempSync(join(tmpdir(), "design-approval-state-"));
    const vaultRoot = mkdtempSync(join(tmpdir(), "design-vault-state-"));
    const priorApprovalRoot = process.env.SPIRITOS_APPROVAL_ROOT;
    const priorApprovalState = process.env.SPIRITOS_APPROVAL_STATE_DIR;
    const priorVaultRoot = process.env.SPIRITOS_DESIGN_VAULT_ROOT;
    process.env.SPIRITOS_APPROVAL_ROOT = process.cwd();
    process.env.SPIRITOS_APPROVAL_STATE_DIR = stateRoot;
    process.env.SPIRITOS_DESIGN_VAULT_ROOT = vaultRoot;
    vi.resetModules();

    try {
      const authority = await import("../design-approval-authority");
      const runtime = await import("../design-studio-approved-writeback-runtime");
      const persisted = await authority.persistDesignPreview({ content: previewContent });
      expect(persisted.ok).toBe(true);
      if (!persisted.ok) throw new Error(persisted.reason);
      const resolved = await authority.resolveDesignWritebackPreview(
        persisted.value.preview_id,
        persisted.value.generation,
      );
      expect(resolved.ok).toBe(true);
      if (!resolved.ok) throw new Error(resolved.reason);
      const issued = await authority.issueDesignWritebackApproval(resolved.value);
      expect(issued.ok).toBe(true);
      if (!issued.ok) throw new Error(issued.reason);

      const result = await runtime.runDesignStudioApprovedWriteback({
        accepted_run: previewContent.accepted_run,
        approval_id: issued.value.approval_id,
        gate: previewContent.gate,
        payload: { ...previewContent.payload, approval_id: issued.value.approval_id },
      } as never);
      expect(result.status).toBe("written");
      if (result.status !== "written") throw new Error(result.reasons.join(", "));
      expect(result.approval_receipt).toMatchObject({ redacted: true, state: "consumed" });
      expect(result.participant_records.map((record) => record.status)).toEqual([
        "accepted",
        "verified",
        "recorded",
      ]);
      expect(existsSync(result.path)).toBe(true);
      expect(JSON.stringify(result)).not.toContain(issued.value.approval_id);
    } finally {
      if (priorApprovalRoot === undefined) delete process.env.SPIRITOS_APPROVAL_ROOT;
      else process.env.SPIRITOS_APPROVAL_ROOT = priorApprovalRoot;
      if (priorApprovalState === undefined) delete process.env.SPIRITOS_APPROVAL_STATE_DIR;
      else process.env.SPIRITOS_APPROVAL_STATE_DIR = priorApprovalState;
      if (priorVaultRoot === undefined) delete process.env.SPIRITOS_DESIGN_VAULT_ROOT;
      else process.env.SPIRITOS_DESIGN_VAULT_ROOT = priorVaultRoot;
      rmSync(stateRoot, { force: true, recursive: true });
      rmSync(vaultRoot, { force: true, recursive: true });
      vi.resetModules();
    }
  }, 30_000);
});
