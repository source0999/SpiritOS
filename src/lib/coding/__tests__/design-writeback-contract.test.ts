/// <reference types="vitest/globals" />

import { buildDesignWritebackArtifact } from "../design-writeback-contract";

const payload = {
  approval_id: "apr_execution_only",
  created_at: "2026-07-01T23:15:00.000Z",
  critic_verdict: "pass",
  design_run_id: "design_run_001",
  files_changed: ["src/app/coding/design-demo/page.tsx"],
  obsidian_context_refs: ["design-brain/homepage-patterns"],
  project_specific_motif: "SpiritOS preview workbench",
  prompt_summary: "Use exact immutable Design writeback binding.",
  reference_dna_refs: ["reference-upload-preview-local"],
  repair_count: 1,
  reusable_pattern_notes: ["Pair desktop and mobile proof."],
  screenshot_hashes: ["desktop_hash_001", "mobile_hash_001"],
  screenshot_proofs: [
    {
      captured_at: "2026-07-01T23:12:00.000Z",
      capture_source: "playwright_desktop",
      content_hash: "desktop_hash_001",
      viewport: { height: 900, width: 1440 },
    },
    {
      captured_at: "2026-07-01T23:13:00.000Z",
      capture_source: "playwright_mobile",
      content_hash: "mobile_hash_001",
      viewport: { height: 844, width: 390 },
    },
  ],
  style_family_blend: ["SpiritOS glass console", "dense product workbench"],
  target_surface: "/coding/design-demo",
  trace_id: "trace_001",
};
const input = {
  accepted_run: {
    acceptance_id: "acceptance_001",
    approved_by: "human",
    run_status: "accepted",
    trace_id: "trace_001",
  },
  gate: {
    anti_template_originality_status: "pass",
    critic_status: "pass",
    desktop_proof: "pass",
    failed_verifier_probes: [],
    fake_go_flags: [],
    mobile_proof: "pass",
    run_status: "verified",
    trace_id: "trace_001",
    unconsumed_packets: [],
  },
  payload,
};

describe("Design writeback immutable contract", () => {
  it("binds accepted run, gate, payload, exact target, expected state, and result state", () => {
    const result = buildDesignWritebackArtifact(input);
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error(result.reason);
    expect(result.value.target).toBe("design-memory/2026-07-01/design_run_001.md");
    expect(result.value.binding.write_contract).toMatchObject({
      context: "trace_001",
      expected_state: { approval: "approved", target: "absent" },
      result_state: {
        approval: "consumed",
        content_hash: expect.stringMatching(/^[0-9a-f]{64}$/),
        target: "written_verified",
      },
      target: "design-memory/2026-07-01/design_run_001.md",
    });
    expect(result.value.artifact_hash).toMatch(/^[0-9a-f]{64}$/);
    expect(JSON.stringify(result.value)).not.toContain("apr_execution_only");
  });

  it("allows the server-issued approval ID to be inserted without changing the artifact", () => {
    const preview = buildDesignWritebackArtifact({
      ...input,
      payload: { ...payload, approval_id: "" },
    });
    const execution = buildDesignWritebackArtifact(input);
    expect(preview.ok && execution.ok && preview.value.artifact_hash).toBe(
      execution.ok ? execution.value.artifact_hash : "execution-failed",
    );
  });

  it("changes the artifact for accepted-run, gate, payload, or target changes", () => {
    const baseline = buildDesignWritebackArtifact(input);
    expect(baseline.ok).toBe(true);
    if (!baseline.ok) throw new Error(baseline.reason);
    const variants = [
      { ...input, accepted_run: { ...input.accepted_run, acceptance_id: "acceptance_002" } },
      { ...input, gate: { ...input.gate, critic_status: "bounded_repair_pass" } },
      { ...input, payload: { ...payload, prompt_summary: "changed" } },
      { ...input, payload: { ...payload, design_run_id: "design_run_002" } },
    ];
    for (const variant of variants) {
      const result = buildDesignWritebackArtifact(variant);
      expect(result.ok).toBe(true);
      if (!result.ok) throw new Error(result.reason);
      expect(result.value.artifact_hash).not.toBe(baseline.value.artifact_hash);
    }
  });

  it("fails closed for model approval, failed verification, and unknown envelope fields", () => {
    expect(
      buildDesignWritebackArtifact({
        ...input,
        accepted_run: { ...input.accepted_run, approved_by: "model" },
      }),
    ).toMatchObject({ ok: false, reason: "human_approval_required" });
    expect(
      buildDesignWritebackArtifact({
        ...input,
        gate: { ...input.gate, run_status: "failed" },
      }),
    ).toMatchObject({ ok: false, reason: "run_not_verified" });
    expect(buildDesignWritebackArtifact({ ...input, target: "override" })).toMatchObject({
      ok: false,
      reason: "design_writeback_contract_unknown_field",
    });
  });
});
