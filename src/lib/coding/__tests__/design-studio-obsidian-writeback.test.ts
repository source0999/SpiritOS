/// <reference types="vitest/globals" />

import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  approvedDesignMemoryDestination,
  approvedDesignMemoryRejectReasons,
  buildApprovedDesignMemoryNote,
  writeApprovedDesignMemoryNote,
  type ApprovedDesignMemoryGate,
  type ApprovedDesignMemoryWritebackPayload,
} from "../design-studio-obsidian-writeback";

const payload: ApprovedDesignMemoryWritebackPayload = {
  approval_id: "approval_001",
  created_at: "2026-07-01T23:15:00.000Z",
  critic_verdict: "pass",
  design_run_id: "design_run_001",
  files_changed: [
    "src/app/coding/design-demo/page.tsx",
    "src/components/coding/DesignStudioShell.tsx",
  ],
  obsidian_context_refs: ["design-brain/homepage-patterns"],
  project_specific_motif: "SpiritOS preview workbench",
  prompt_summary: "Make the Design Studio preview feel premium and not generic.",
  reference_dna_refs: ["reference-upload-preview-local"],
  repair_count: 1,
  reusable_pattern_notes: ["Use a scope fence before apply proof.", "Pair desktop and mobile proof."],
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

const gate: ApprovedDesignMemoryGate = {
  anti_template_originality_status: "pass",
  critic_status: "pass",
  desktop_proof: "pass",
  failed_verifier_probes: [],
  fake_go_flags: [],
  mobile_proof: "pass",
  run_status: "verified",
  trace_id: "trace_001",
  unconsumed_packets: [],
};

describe("Design Studio Obsidian writeback", () => {
  it("creates a valid design memory note payload for an approved verified run", () => {
    const vaultRoot = mkdtempSync(join(tmpdir(), "design-memory-vault-"));
    try {
      const result = writeApprovedDesignMemoryNote(payload, gate, { vaultRoot });

      expect(result.status).toBe("written");
      if (result.status !== "written") {
        throw new Error(result.reasons.join(", "));
      }
      expect(result.path).toBe(
        join(vaultRoot, "design-memory", "2026-07-01", "design_run_001.md"),
      );
      const note = readFileSync(result.path, "utf8");
      expect(note).toContain("type: design-memory");
      expect(note).toContain("design_run_id: \"design_run_001\"");
      expect(note).toContain("# Design Memory: /coding/design-demo");
      expect(note).toContain("## Why this design was approved");
      expect(note).toContain("- Raw CSS copied: no");
      expect(note).toContain("- Mobile proof passed: yes");
    } finally {
      rmSync(vaultRoot, { force: true, recursive: true });
    }
  });

  it("rejects missing approval_id", () => {
    expect(approvedDesignMemoryRejectReasons({ ...payload, approval_id: "" }, gate)).toContain(
      "missing_approval_id",
    );
  });

  it("rejects missing desktop or mobile screenshot proof", () => {
    expect(
      approvedDesignMemoryRejectReasons(
        { ...payload, screenshot_hashes: ["desktop_hash_001"] },
        { ...gate, mobile_proof: "missing" },
      ),
    ).toEqual(
      expect.arrayContaining([
        "mobile_proof_not_passing",
        "missing_desktop_or_mobile_screenshot_hash",
      ]),
    );
  });

  it("rejects bare screenshot hashes without attributed capture proof", () => {
    expect(
      approvedDesignMemoryRejectReasons(
        { ...payload, screenshot_proofs: undefined },
        gate,
      ),
    ).toContain("missing_structured_screenshot_proof");
  });

  it("rejects unknown screenshot capture sources", () => {
    expect(
      approvedDesignMemoryRejectReasons(
        {
          ...payload,
          screenshot_proofs: [
            {
              captured_at: "2026-07-01T23:12:00.000Z",
              capture_source: "playwright_desktop",
              content_hash: "desktop_hash_001",
              viewport: { height: 900, width: 1440 },
            },
            {
              captured_at: "2026-07-01T23:13:00.000Z",
              capture_source: "manual_upload" as "playwright_mobile",
              content_hash: "mobile_hash_001",
              viewport: { height: 844, width: 390 },
            },
          ],
        },
        gate,
      ),
    ).toEqual(
      expect.arrayContaining([
        "unknown_screenshot_capture_source",
        "missing_desktop_or_mobile_screenshot_proof_source",
      ]),
    );
  });

  it("rejects failed critic verdict", () => {
    expect(approvedDesignMemoryRejectReasons(payload, { ...gate, critic_status: "fail" })).toContain(
      "critic_not_passing",
    );
  });

  it("rejects unconsumed design_packet state", () => {
    expect(
      approvedDesignMemoryRejectReasons(payload, {
        ...gate,
        unconsumed_packets: ["design_packet"],
      }),
    ).toContain("unconsumed_packets_present");
  });

  it("rejects preview-only runs", () => {
    expect(approvedDesignMemoryRejectReasons(payload, { ...gate, run_status: "preview_only" })).toContain(
      "run_not_verified",
    );
  });

  it("rejects failed designs", () => {
    expect(
      approvedDesignMemoryRejectReasons(payload, {
        ...gate,
        anti_template_originality_status: "fail",
        failed_verifier_probes: ["mobile_overflow"],
        run_status: "failed",
      }),
    ).toEqual(
      expect.arrayContaining([
        "run_not_verified",
        "anti_template_originality_not_passing",
        "failed_verifier_probes_present",
      ]),
    );
  });

  it("prevents note destination escape from the approved design memory folder", () => {
    expect(
      approvedDesignMemoryDestination("/tmp/design-vault", {
        created_at: payload.created_at,
        design_run_id: "../escape",
      }),
    ).toEqual({ reason: "unsafe_design_run_id", status: "rejected" });
  });

  it("does not overwrite an existing note", () => {
    const vaultRoot = mkdtempSync(join(tmpdir(), "design-memory-vault-"));
    try {
      const first = writeApprovedDesignMemoryNote(payload, gate, { vaultRoot });
      expect(first.status).toBe("written");
      const destination = approvedDesignMemoryDestination(vaultRoot, payload);
      if (destination.status !== "ok") {
        throw new Error(destination.reason);
      }
      writeFileSync(destination.path, "existing note", "utf8");

      expect(writeApprovedDesignMemoryNote(payload, gate, { vaultRoot })).toEqual({
        reasons: ["destination_exists"],
        status: "rejected",
      });
    } finally {
      rmSync(vaultRoot, { force: true, recursive: true });
    }
  });

  it("builds a human-readable note without performing a write", () => {
    const note = buildApprovedDesignMemoryNote(payload);

    expect(note).toContain("## Summary");
    expect(note).toContain("## Reusable pattern");
    expect(note).toContain("## Evidence");
    expect(note).not.toContain("undefined");
  });
});
