import "server-only";

import {
  type ApprovedDesignMemoryGate,
  type ApprovedDesignMemoryWritebackPayload,
  writeApprovedDesignMemoryNote,
} from "./design-studio-obsidian-writeback";
import {
  consumeDesignWritebackApproval,
  finalizeDesignWritebackApproval,
  loadDesignWritebackApproval,
} from "./design-approval-authority";

export type DesignStudioAcceptedRunGate = {
  acceptance_id?: string;
  approved_by?: "human" | "model";
  run_status: "accepted" | "preview_only" | "rejected";
  trace_id: string;
};

export type DesignStudioApprovedWritebackRequest = {
  approval_id: string;
  accepted_run: DesignStudioAcceptedRunGate;
  gate: ApprovedDesignMemoryGate;
  payload: ApprovedDesignMemoryWritebackPayload;
};

const SAFE_APPROVAL_ID = /^[A-Za-z0-9_-]{6,128}$/;

const SERVER_OWNED_VAULT_ROOT = process.env.SPIRITOS_DESIGN_VAULT_ROOT || "/home/source/.local/state/spiritos/design-vault";

export async function runDesignStudioApprovedWriteback(request: DesignStudioApprovedWritebackRequest) {
  if (request.accepted_run.run_status !== "accepted") {
    return {
      reasons: ["accepted_run_required"],
      status: "rejected" as const,
      write_invoked: false,
    };
  }

  if (!request.approval_id?.trim() || request.payload.approval_id !== request.approval_id) {
    return {
      reasons: ["missing_approval_id"],
      status: "rejected" as const,
      write_invoked: false,
    };
  }

  if (!SAFE_APPROVAL_ID.test(request.payload.approval_id)) {
    return {
      reasons: ["invalid_approval_id"],
      status: "rejected" as const,
      write_invoked: false,
    };
  }

  if (!request.accepted_run.acceptance_id?.trim()) {
    return {
      reasons: ["acceptance_id_required"],
      status: "rejected" as const,
      write_invoked: false,
    };
  }

  if (request.accepted_run.approved_by === "model") {
    return {
      reasons: ["model_cannot_self_promote_approval"],
      status: "rejected" as const,
      write_invoked: false,
    };
  }

  if (request.accepted_run.trace_id !== request.payload.trace_id || request.accepted_run.trace_id !== request.gate.trace_id) {
    return {
      reasons: ["accepted_run_trace_mismatch"],
      status: "rejected" as const,
      write_invoked: false,
    };
  }

  const approval = await loadDesignWritebackApproval(request.approval_id);
  if (!approval.ok) {
    return { reasons: [approval.reason], status: "rejected" as const, write_invoked: false };
  }

  const consumption = await consumeDesignWritebackApproval(approval.value, request.payload);
  if (!consumption.ok) {
    return { reasons: [consumption.reason], status: "rejected" as const, write_invoked: false };
  }

  const result = writeApprovedDesignMemoryNote(request.payload, request.gate, {
    vaultRoot: SERVER_OWNED_VAULT_ROOT,
  });
  const finalized = await finalizeDesignWritebackApproval(approval.value, {
    receipt: {
      acceptance_id: request.accepted_run.acceptance_id,
      result_status: result.status,
      target: request.payload.target_surface,
      trace_id: request.payload.trace_id,
    },
    result_id: result.status === "written" ? result.path : undefined,
    status: result.status === "written" ? "succeeded" : "failed",
  });
  if (!finalized.ok) {
    return { reasons: [finalized.reason], status: "rejected" as const, write_invoked: true };
  }

  return {
    ...result,
    acceptance_id: request.accepted_run.acceptance_id,
    acceptance_trace_id: request.accepted_run.trace_id,
    approval_receipt: finalized.value,
    write_invoked: true,
  };
}
