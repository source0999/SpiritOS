import "server-only";

import { spawn } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { join } from "node:path";
import { promisify } from "node:util";
import { execFile } from "node:child_process";

const execFileAsync = promisify(execFile);
const authorityScript = join(process.cwd(), "scripts", "approval-authority.py");
export const CAMPAIGN_REPOSITORY = "SpiritOS";
export const CAMPAIGN_ROOT = "/home/source/SpiritOS-campaign-1-20260712";
const DESIGN_PLUGIN = "design-studio";

export type DesignPreviewBinding = {
  content_hash: string;
  context: string;
  generation: number;
  preview_id: string;
  source_head: string;
  target: string;
};

export type DesignApprovalBinding = DesignPreviewBinding & {
  approval_id: string;
  consumer: "design-writeback";
  operation: "design_writeback";
};

export const DESIGN_ACKNOWLEDGEMENT_CONSUMERS = [
  "design-writeback",
  "design-reviewer",
  "design-verifier",
  "evidence-recorder",
] as const;

export type DesignAcknowledgements = Record<(typeof DESIGN_ACKNOWLEDGEMENT_CONSUMERS)[number], {
  approval_id: string;
  generation: number;
}>;

function stableJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => `${JSON.stringify(key)}:${stableJson(item)}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function withoutApprovalId(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(withoutApprovalId);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([key]) => key !== "approval_id")
        .map(([key, item]) => [key, withoutApprovalId(item)]),
    );
  }
  return value;
}

export function hashApprovalContent(value: unknown) {
  return createHash("sha256").update(stableJson(withoutApprovalId(value)), "utf8").digest("hex");
}

async function campaignHead() {
  const { stdout } = await execFileAsync("git", ["rev-parse", "HEAD"], { cwd: CAMPAIGN_ROOT });
  return stdout.trim();
}

async function invokeAuthority(command: string, input: Record<string, unknown>) {
  const result = await new Promise<{ code: number; text: string }>((resolve) => {
    const child = spawn("python3", [authorityScript, command], {
      stdio: ["pipe", "pipe", "ignore"],
    });
    let text = "";
    child.stdout.on("data", (chunk) => (text += chunk));
    child.on("close", (code) => resolve({ code: code ?? 1, text }));
    child.stdin.end(JSON.stringify(input));
  });
  try {
    const parsed = JSON.parse(result.text);
    return result.code === 0
      ? { ok: true as const, value: parsed }
      : { ok: false as const, reason: String(parsed.reason ?? "approval_issuer_unavailable") };
  } catch {
    return { ok: false as const, reason: "approval_issuer_unavailable" };
  }
}

function commonBinding(binding: Pick<DesignPreviewBinding, "content_hash" | "context" | "source_head" | "target">) {
  return {
    content_hash: binding.content_hash,
    context: binding.context,
    plugin: DESIGN_PLUGIN,
    repository: CAMPAIGN_REPOSITORY,
    root: CAMPAIGN_ROOT,
    source_head: binding.source_head,
    target: binding.target,
    worktree: CAMPAIGN_ROOT,
  };
}

export async function persistDesignPreview(input: { content: unknown; context: string; target: string }) {
  const source_head = await campaignHead();
  const persisted = await invokeAuthority("persist-preview", {
    ...commonBinding({
      content_hash: hashApprovalContent(input.content),
      context: input.context,
      source_head,
      target: input.target,
    }),
  });
  if (!persisted.ok) return persisted;
  return {
    ok: true as const,
    value: {
      content_hash: hashApprovalContent(input.content),
      context: input.context,
      generation: Number(persisted.value.generation),
      preview_id: String(persisted.value.preview_id),
      source_head,
      target: input.target,
    } satisfies DesignPreviewBinding,
  };
}

export async function resolveDesignWritebackPreview(previewId: string, expectedGeneration: number) {
  const loaded = await invokeAuthority("lookup-preview", { preview_id: previewId });
  if (!loaded.ok) return loaded;
  if (Number(loaded.value.generation) !== expectedGeneration) return { ok: false as const, reason: "approval_generation_mismatch" };
  if (loaded.value.state !== "previewed") return { ok: false as const, reason: "approval_not_approved" };
  if (loaded.value.repository !== CAMPAIGN_REPOSITORY || loaded.value.worktree !== CAMPAIGN_ROOT || loaded.value.root !== CAMPAIGN_ROOT || loaded.value.plugin !== DESIGN_PLUGIN) {
    return { ok: false as const, reason: "approval_worktree_mismatch" };
  }
  const source_head = await campaignHead();
  if (loaded.value.source_head !== source_head) return { ok: false as const, reason: "approval_source_mismatch" };
  return {
    ok: true as const,
    value: {
      content_hash: String(loaded.value.content_hash), context: String(loaded.value.context), generation: Number(loaded.value.generation),
      preview_id: String(loaded.value.id), source_head: String(loaded.value.source_head), target: String(loaded.value.target),
    } satisfies DesignPreviewBinding,
  };
}

export async function issueDesignWritebackApproval(preview: DesignPreviewBinding, ttlMinutes = 30) {
  const expires_at = new Date(Date.now() + Math.min(Math.max(ttlMinutes, 1), 60) * 60_000).toISOString();
  const issued = await invokeAuthority("issue", {
    consumer: "design-writeback",
    expires_at,
    operation: "design_writeback",
    expected_generation: String(preview.generation),
    preview_id: preview.preview_id,
  });
  if (!issued.ok) return issued;
  return {
    ok: true as const,
    value: {
      ...preview,
      approval_id: String(issued.value.approval_id),
      consumer: "design-writeback" as const,
      operation: "design_writeback" as const,
    } satisfies DesignApprovalBinding,
  };
}

export async function rejectDesignWritebackPreview(preview: DesignPreviewBinding) {
  return invokeAuthority("transition-preview", { expected_generation: String(preview.generation), preview_id: preview.preview_id, state: "rejected" });
}

export async function loadDesignWritebackApproval(approvalId: string) {
  const loaded = await invokeAuthority("lookup", { approval_id: approvalId });
  if (!loaded.ok) return loaded;
  if (loaded.value.consumer !== "design-writeback" || loaded.value.operation !== "design_writeback") {
    return { ok: false as const, reason: "approval_consumer_mismatch" };
  }
  return {
    ok: true as const,
    value: {
      approval_id: String(loaded.value.id),
      consumer: "design-writeback" as const,
      content_hash: String(loaded.value.content_hash),
      context: String(loaded.value.context),
      generation: Number(loaded.value.generation),
      operation: "design_writeback" as const,
      preview_id: String(loaded.value.preview),
      source_head: String(loaded.value.source_head),
      target: String(loaded.value.target),
    } satisfies DesignApprovalBinding,
  };
}

export async function consumeDesignWritebackApproval(approval: DesignApprovalBinding, content: unknown) {
  if (hashApprovalContent(content) !== approval.content_hash) {
    return { ok: false as const, reason: "approval_content_hash_mismatch" };
  }
  const source_head = await campaignHead();
  return invokeAuthority("consume", {
    ...commonBinding({ ...approval, source_head }),
    approval_id: approval.approval_id,
    consumer: approval.consumer,
    generation: String(approval.generation),
    operation: approval.operation,
    preview: approval.preview_id,
  });
}

export function designWritebackAcknowledgements(approval: DesignApprovalBinding): DesignAcknowledgements {
  return Object.fromEntries(
    DESIGN_ACKNOWLEDGEMENT_CONSUMERS.map((consumer) => [consumer, {
      approval_id: approval.approval_id,
      generation: approval.generation,
    }]),
  ) as DesignAcknowledgements;
}

export function redactedDesignWritebackEvidence(
  approval: DesignApprovalBinding,
  receipt: { acceptance_id: string; result_status: "rejected" | "written"; target: string; trace_id: string },
) {
  const acknowledgements = designWritebackAcknowledgements(approval);
  for (const acknowledgement of Object.values(acknowledgements)) {
    if (acknowledgement.approval_id !== approval.approval_id || acknowledgement.generation !== approval.generation) {
      throw new Error("design_acknowledgement_mismatch");
    }
  }
  return {
    acknowledgement_consumers: DESIGN_ACKNOWLEDGEMENT_CONSUMERS,
    generation: approval.generation,
    receipt: {
      acceptance_hash: hashApprovalContent(receipt.acceptance_id),
      result_status: receipt.result_status,
      target_hash: hashApprovalContent(receipt.target),
      trace_hash: hashApprovalContent(receipt.trace_id),
    },
    redacted: true,
  };
}

export async function finalizeDesignWritebackApproval(
  approval: DesignApprovalBinding,
  result: {
    receipt: { acceptance_id: string; result_status: "rejected" | "written"; target: string; trace_id: string };
    result_id?: string;
    status: "failed" | "succeeded";
  },
) {
  const source_head = await campaignHead();
  const finalized = await invokeAuthority("finalize", {
    ...commonBinding({ ...approval, source_head }),
    approval_id: approval.approval_id,
    consumer: approval.consumer,
    evidence: stableJson(redactedDesignWritebackEvidence(approval, result.receipt)),
    generation: String(approval.generation),
    operation: approval.operation,
    preview: approval.preview_id,
    result_id: result.result_id ?? `design-writeback-${randomUUID()}`,
    status: result.status,
  });
  if (!finalized.ok) return finalized;
  return {
    ok: true as const,
    value: {
      ...finalized.value,
      acknowledgement_consumers: DESIGN_ACKNOWLEDGEMENT_CONSUMERS,
      generation: approval.generation,
      redacted: true,
    },
  };
}
