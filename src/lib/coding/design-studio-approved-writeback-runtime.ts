import {
  type ApprovedDesignMemoryGate,
  type ApprovedDesignMemoryWritebackPayload,
  writeApprovedDesignMemoryNote,
} from "./design-studio-obsidian-writeback";

export type DesignStudioAcceptedRunGate = {
  acceptance_id?: string;
  approved_by?: "human" | "model";
  run_status: "accepted" | "preview_only" | "rejected";
  trace_id: string;
};

export type DesignStudioApprovedWritebackRequest = {
  accepted_run: DesignStudioAcceptedRunGate;
  gate: ApprovedDesignMemoryGate;
  payload: ApprovedDesignMemoryWritebackPayload;
  vault_root: string;
};

const SAFE_APPROVAL_ID = /^[A-Za-z0-9_-]{6,128}$/;

export function runDesignStudioApprovedWriteback(request: DesignStudioApprovedWritebackRequest) {
  if (request.accepted_run.run_status !== "accepted") {
    return {
      reasons: ["accepted_run_required"],
      status: "rejected" as const,
      write_invoked: false,
    };
  }

  if (!request.payload.approval_id.trim()) {
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

  const result = writeApprovedDesignMemoryNote(request.payload, request.gate, {
    vaultRoot: request.vault_root,
  });

  return {
    ...result,
    acceptance_id: request.accepted_run.acceptance_id,
    acceptance_trace_id: request.accepted_run.trace_id,
    write_invoked: true,
  };
}
