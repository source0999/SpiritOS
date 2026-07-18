import { createHash } from "node:crypto";

import {
  approvedDesignMemoryRejectReasons,
  buildApprovedDesignMemoryNote,
  designMemoryNoteContentHash,
  type ApprovedDesignMemoryGate,
  type ApprovedDesignMemoryWritebackPayload,
} from "./design-studio-obsidian-writeback";

export type DesignWritebackArtifact = {
  artifact_hash: string;
  artifact_id: string;
  binding: {
    accepted_run: Record<string, unknown>;
    gate: Record<string, unknown>;
    payload: Record<string, unknown>;
    schema_version: "spiritos-design-writeback-artifact/v1";
    write_contract: {
      context: string;
      expected_state: {
        approval: "approved";
        target: "absent";
      };
      result_state: {
        approval: "consumed";
        content_hash: string;
        target: "written_verified";
      };
      target: string;
    };
  };
  context: string;
  note_content_hash: string;
  target: string;
};

export type DesignWritebackArtifactResult =
  | { ok: true; value: DesignWritebackArtifact }
  | { ok: false; reason: string };

type DesignWritebackArtifactInput = {
  accepted_run: Record<string, unknown>;
  gate: Record<string, unknown>;
  payload: Record<string, unknown>;
};

export function buildDesignWritebackArtifact(input: unknown): DesignWritebackArtifactResult {
  if (!isRecord(input)) return { ok: false, reason: "design_writeback_contract_invalid" };
  const allowedTopLevel = new Set(["accepted_run", "gate", "payload"]);
  if (Object.keys(input).some((key) => !allowedTopLevel.has(key))) {
    return { ok: false, reason: "design_writeback_contract_unknown_field" };
  }
  if (!isRecord(input.accepted_run) || !isRecord(input.gate) || !isRecord(input.payload)) {
    return { ok: false, reason: "design_writeback_contract_invalid" };
  }

  const artifactInput: DesignWritebackArtifactInput = {
    accepted_run: input.accepted_run,
    gate: input.gate,
    payload: input.payload,
  };
  const shapeReason = validateShape(artifactInput);
  if (shapeReason) return { ok: false, reason: shapeReason };

  const acceptedRun = artifactInput.accepted_run;
  const gate = artifactInput.gate as unknown as ApprovedDesignMemoryGate;
  const payload = artifactInput.payload as unknown as ApprovedDesignMemoryWritebackPayload;
  if (acceptedRun.run_status !== "accepted") {
    return { ok: false, reason: "accepted_run_required" };
  }
  if (acceptedRun.approved_by !== "human") {
    return { ok: false, reason: "human_approval_required" };
  }
  if (typeof acceptedRun.acceptance_id !== "string" || !acceptedRun.acceptance_id.trim()) {
    return { ok: false, reason: "acceptance_id_required" };
  }
  if (
    acceptedRun.trace_id !== payload.trace_id ||
    acceptedRun.trace_id !== gate.trace_id
  ) {
    return { ok: false, reason: "accepted_run_trace_mismatch" };
  }
  const gateReasons = approvedDesignMemoryRejectReasons(
    { ...payload, approval_id: "preview-binding" },
    gate,
  ).filter((reason) => reason !== "missing_approval_id");
  if (gateReasons.length > 0) {
    return { ok: false, reason: gateReasons[0] };
  }

  const date = payload.created_at.slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return { ok: false, reason: "invalid_created_at" };
  }
  if (!/^[A-Za-z0-9_-]+$/.test(payload.design_run_id.trim())) {
    return { ok: false, reason: "unsafe_design_run_id" };
  }
  const target = `design-memory/${date}/${payload.design_run_id.trim()}.md`;
  const note = buildApprovedDesignMemoryNote({ ...payload, approval_id: "" });
  const noteContentHash = designMemoryNoteContentHash(note);
  const binding = {
    accepted_run: withoutApprovalIdentity(acceptedRun) as Record<string, unknown>,
    gate: withoutApprovalIdentity(artifactInput.gate) as Record<string, unknown>,
    payload: withoutApprovalIdentity(artifactInput.payload) as Record<string, unknown>,
    schema_version: "spiritos-design-writeback-artifact/v1" as const,
    write_contract: {
      context: payload.trace_id,
      expected_state: {
        approval: "approved" as const,
        target: "absent" as const,
      },
      result_state: {
        approval: "consumed" as const,
        content_hash: noteContentHash,
        target: "written_verified" as const,
      },
      target,
    },
  };
  const artifactHash = sha256(stableJson(binding));
  return {
    ok: true,
    value: {
      artifact_hash: artifactHash,
      artifact_id: `design-writeback-${artifactHash}`,
      binding,
      context: payload.trace_id,
      note_content_hash: noteContentHash,
      target,
    },
  };
}

function validateShape(input: DesignWritebackArtifactInput) {
  const payload = input.payload;
  const gate = input.gate;
  const stringFields = [
    "created_at",
    "critic_verdict",
    "design_run_id",
    "project_specific_motif",
    "prompt_summary",
    "target_surface",
    "trace_id",
  ];
  if (stringFields.some((field) => typeof payload[field] !== "string" || !(payload[field] as string).trim())) {
    return "design_writeback_payload_invalid";
  }
  const stringArrayFields = [
    "files_changed",
    "obsidian_context_refs",
    "reference_dna_refs",
    "reusable_pattern_notes",
    "screenshot_hashes",
    "style_family_blend",
  ];
  if (stringArrayFields.some((field) => !isStringArray(payload[field]))) {
    return "design_writeback_payload_invalid";
  }
  if (!Number.isInteger(payload.repair_count) || (payload.repair_count as number) < 0) {
    return "design_writeback_payload_invalid";
  }
  if (!Array.isArray(payload.screenshot_proofs)) {
    return "missing_structured_screenshot_proof";
  }
  const gateFields = [
    "anti_template_originality_status",
    "critic_status",
    "desktop_proof",
    "mobile_proof",
    "run_status",
    "trace_id",
  ];
  if (gateFields.some((field) => typeof gate[field] !== "string")) {
    return "design_writeback_gate_invalid";
  }
  return null;
}

function withoutApprovalIdentity(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(withoutApprovalIdentity);
  if (isRecord(value)) {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([key]) => key !== "approval_id")
        .map(([key, item]) => [key, withoutApprovalIdentity(item)]),
    );
  }
  return value;
}

function stableJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (isRecord(value)) {
    return `{${Object.entries(value)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => `${JSON.stringify(key)}:${stableJson(item)}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value: string) {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}
