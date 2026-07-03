import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve } from "node:path";

export type ApprovedDesignMemoryWritebackPayload = {
  approval_id: string;
  created_at: string;
  critic_verdict: "bounded_repair_pass" | "pass";
  design_run_id: string;
  files_changed: string[];
  obsidian_context_refs: string[];
  project_specific_motif: string;
  prompt_summary: string;
  reference_dna_refs: string[];
  repair_count: number;
  reusable_pattern_notes: string[];
  screenshot_hashes: string[];
  screenshot_proofs?: ApprovedDesignScreenshotProof[];
  style_family_blend: string[];
  target_surface: string;
  trace_id: string;
};

export type ApprovedDesignScreenshotProof = {
  captured_at: string;
  capture_source: "playwright_desktop" | "playwright_mobile";
  content_hash: string;
  viewport: {
    height: number;
    width: number;
  };
};

export type ApprovedDesignMemoryGate = {
  anti_template_originality_status: "fail" | "pass";
  critic_status: "bounded_repair_pass" | "fail" | "pass";
  desktop_proof: "fail" | "missing" | "pass";
  failed_verifier_probes?: string[];
  fake_go_flags?: string[];
  mobile_proof: "fail" | "missing" | "pass";
  run_status: "failed" | "preview_only" | "verified";
  trace_id: string;
  unconsumed_packets?: string[];
};

export type ApprovedDesignMemoryWriteResult =
  | {
      note: string;
      path: string;
      status: "written";
    }
  | {
      reasons: string[];
      status: "rejected";
    };

const SAFE_ID = /^[A-Za-z0-9_-]+$/;

export function approvedDesignMemoryRejectReasons(
  payload: ApprovedDesignMemoryWritebackPayload,
  gate: ApprovedDesignMemoryGate,
) {
  const reasons: string[] = [];

  if (!payload.approval_id.trim()) {
    reasons.push("missing_approval_id");
  }
  if (gate.run_status !== "verified") {
    reasons.push("run_not_verified");
  }
  if (gate.desktop_proof !== "pass") {
    reasons.push("desktop_proof_not_passing");
  }
  if (gate.mobile_proof !== "pass") {
    reasons.push("mobile_proof_not_passing");
  }
  if (gate.anti_template_originality_status !== "pass") {
    reasons.push("anti_template_originality_not_passing");
  }
  if (gate.critic_status !== "pass" && gate.critic_status !== "bounded_repair_pass") {
    reasons.push("critic_not_passing");
  }
  if (payload.trace_id !== gate.trace_id) {
    reasons.push("trace_id_mismatch");
  }
  if ((gate.failed_verifier_probes ?? []).length > 0) {
    reasons.push("failed_verifier_probes_present");
  }
  if ((gate.fake_go_flags ?? []).length > 0) {
    reasons.push("fake_go_flags_present");
  }
  if ((gate.unconsumed_packets ?? []).length > 0) {
    reasons.push("unconsumed_packets_present");
  }
  if (payload.screenshot_hashes.length < 2) {
    reasons.push("missing_desktop_or_mobile_screenshot_hash");
  }
  const screenshotProofReasons = screenshotProofRejectReasons(payload.screenshot_proofs);
  reasons.push(...screenshotProofReasons);

  return reasons;
}

function screenshotProofRejectReasons(proofs: ApprovedDesignScreenshotProof[] | undefined) {
  if (!Array.isArray(proofs) || proofs.length < 2) {
    return ["missing_structured_screenshot_proof"];
  }
  const reasons: string[] = [];
  const seenSources = new Set<string>();
  for (const proof of proofs) {
    if (!proof || typeof proof !== "object") {
      reasons.push("invalid_screenshot_proof_object");
      continue;
    }
    if (proof.capture_source !== "playwright_desktop" && proof.capture_source !== "playwright_mobile") {
      reasons.push("unknown_screenshot_capture_source");
    } else {
      seenSources.add(proof.capture_source);
    }
    if (!proof.content_hash?.trim()) {
      reasons.push("missing_screenshot_content_hash");
    }
    if (!proof.captured_at?.trim()) {
      reasons.push("missing_screenshot_captured_at");
    }
    if (!proof.viewport || proof.viewport.width <= 0 || proof.viewport.height <= 0) {
      reasons.push("invalid_screenshot_viewport");
    }
  }
  if (!seenSources.has("playwright_desktop") || !seenSources.has("playwright_mobile")) {
    reasons.push("missing_desktop_or_mobile_screenshot_proof_source");
  }
  return Array.from(new Set(reasons));
}

export function approvedDesignMemoryDestination(
  vaultRoot: string,
  payload: Pick<ApprovedDesignMemoryWritebackPayload, "created_at" | "design_run_id">,
) {
  const designRunId = payload.design_run_id.trim();
  if (!SAFE_ID.test(designRunId)) {
    return { reason: "unsafe_design_run_id", status: "rejected" as const };
  }

  const date = payload.created_at.slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return { reason: "invalid_created_at", status: "rejected" as const };
  }

  const root = resolve(vaultRoot);
  const path = resolve(root, "design-memory", date, `${designRunId}.md`);
  const allowedRoot = resolve(root, "design-memory");
  const relativeDestination = relative(allowedRoot, path);
  if (
    path !== resolve(path) ||
    relativeDestination === "" ||
    relativeDestination === ".." ||
    relativeDestination.startsWith(`..\\`) ||
    relativeDestination.startsWith("../") ||
    isAbsolute(relativeDestination)
  ) {
    return { reason: "destination_escape", status: "rejected" as const };
  }

  return { path, status: "ok" as const };
}

export function buildApprovedDesignMemoryNote(payload: ApprovedDesignMemoryWritebackPayload) {
  const styleList = payload.style_family_blend.map((item) => `  - ${yamlScalar(item)}`).join("\n");
  const screenshotList = payload.screenshot_hashes.map((item) => `- ${item}`).join("\n");
  const fileList = payload.files_changed.map((item) => `- ${item}`).join("\n");
  const patternNotes = payload.reusable_pattern_notes.map((item) => `- ${item}`).join("\n");
  const contextRefs = payload.obsidian_context_refs.map((item) => `- ${item}`).join("\n") || "- none";
  const referenceRefs = payload.reference_dna_refs.map((item) => `- ${item}`).join("\n") || "- none";

  return `---\ntype: design-memory\ndesign_run_id: ${yamlScalar(payload.design_run_id)}\ntrace_id: ${yamlScalar(payload.trace_id)}\napproval_id: ${yamlScalar(payload.approval_id)}\ntarget_surface: ${yamlScalar(payload.target_surface)}\nstyle_family_blend:\n${styleList}\ncritic_verdict: ${yamlScalar(payload.critic_verdict)}\nrepair_count: ${payload.repair_count}\ncreated_at: ${yamlScalar(payload.created_at)}\n---\n\n# Design Memory: ${payload.target_surface}\n\n## Summary\n${payload.prompt_summary}\n\n## Why this design was approved\nThe run was verified, explicitly approved, checked on desktop and mobile, passed anti-template/originality review, and ended with critic verdict ${payload.critic_verdict}.\n\n## Reusable pattern\n${patternNotes}\n\n## Style DNA\n- Style family blend: ${payload.style_family_blend.join(", ")}\n- Project motif: ${payload.project_specific_motif}\n- Obsidian context refs:\n${contextRefs}\n- Reference DNA refs:\n${referenceRefs}\n\n## Evidence\n- Design run: ${payload.design_run_id}\n- Trace: ${payload.trace_id}\n- Approval: ${payload.approval_id}\n- Screenshots:\n${screenshotList}\n- Files changed:\n${fileList}\n\n## Guardrails\n- Raw CSS copied: no\n- Website cloned: no\n- Generic template accepted: no\n- Mobile proof passed: yes\n`;
}

export function writeApprovedDesignMemoryNote(
  payload: ApprovedDesignMemoryWritebackPayload,
  gate: ApprovedDesignMemoryGate,
  options: { vaultRoot: string },
): ApprovedDesignMemoryWriteResult {
  const reasons = approvedDesignMemoryRejectReasons(payload, gate);
  const destination = approvedDesignMemoryDestination(options.vaultRoot, payload);
  if (destination.status === "rejected") {
    reasons.push(destination.reason);
  }
  if (reasons.length > 0) {
    return { reasons, status: "rejected" };
  }
  if (destination.status !== "ok") {
    return { reasons: ["destination_escape"], status: "rejected" };
  }

  if (existsSync(destination.path)) {
    return { reasons: ["destination_exists"], status: "rejected" };
  }

  const note = buildApprovedDesignMemoryNote(payload);
  mkdirSync(dirname(destination.path), { recursive: true });
  writeFileSync(destination.path, note, { encoding: "utf8", flag: "wx" });
  return { note, path: destination.path, status: "written" };
}

function yamlScalar(value: string) {
  return JSON.stringify(value);
}
