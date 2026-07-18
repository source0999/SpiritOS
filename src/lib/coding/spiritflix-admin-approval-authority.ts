import "server-only";

import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { realpath } from "node:fs/promises";
import { isAbsolute, join, resolve } from "node:path";

import {
  type AuthorityRuntimeIdentity,
  resolveAuthorityRuntimeIdentity,
} from "@/lib/coding/authority-runtime-identity";
import { hashApprovalContent } from "@/lib/coding/design-approval-authority";

const CONSUMER = "spiritflix-admin-executor";
const OPERATION = "spiritflix_admin_mutation";
const PLUGIN = "spiritflix-admin";

export type SpiritFlixAdminParticipantInvocation = {
  acknowledgement: {
    approval_id: string;
    generation: number;
    result_hash: string;
  };
  completed_at: string;
  consumer: "spiritflix-admin-reviewer" | "spiritflix-admin-verifier" | "evidence-recorder";
  invocation_id: string;
  outcome: "accepted";
};

export type SpiritFlixAdminFinalizationEvidence = {
  participant_invocations: SpiritFlixAdminParticipantInvocation[];
  redaction_verdict: "passed";
  result_hash: string;
  result_schema: string;
};

async function invoke(
  identity: AuthorityRuntimeIdentity,
  command: string,
  input: Record<string, unknown>,
) {
  const script = join(identity.root, "scripts", "approval-authority.py");
  const result = await new Promise<{ code: number; text: string }>((done) => {
    const child = spawn("python3", [script, command], {
      cwd: identity.root,
      env: { ...process.env, SPIRITOS_APPROVAL_ROOT: identity.root },
      stdio: ["pipe", "pipe", "ignore"],
    });
    let text = "";
    child.stdout.on("data", (chunk) => (text += chunk));
    child.on("close", (code) => done({ code: code ?? 1, text }));
    child.stdin.end(JSON.stringify(input));
  });
  try {
    const value = JSON.parse(result.text) as Record<string, unknown>;
    return result.code === 0
      ? { ok: true as const, value }
      : { ok: false as const, reason: String(value.reason ?? "approval_issuer_unavailable") };
  } catch {
    return { ok: false as const, reason: "approval_issuer_unavailable" };
  }
}

async function configuredAdminRoot(identity: AuthorityRuntimeIdentity): Promise<string> {
  const configured =
    process.env.SPIRITFLIX_ADMIN_ROOT?.trim() ||
    process.env.SPIRITFLIX_MANUAL_MODEL_ROOT?.trim() ||
    process.env.SPIRITFLIX_MEDIA_ROOT?.trim() ||
    identity.root;
  if (!isAbsolute(configured)) throw new Error("spiritflix_admin_root_not_absolute");
  const absolute = resolve(configured);
  let canonical: string;
  try {
    canonical = await realpath(absolute);
  } catch {
    throw new Error("spiritflix_admin_root_unavailable");
  }
  if (canonical !== absolute) throw new Error("spiritflix_admin_root_symlink_forbidden");
  return canonical;
}

function content(
  action: string,
  target: string,
  configuredRoot: string,
  plan: Record<string, unknown>,
) {
  return hashApprovalContent({ action, configured_root: configuredRoot, plan, target });
}

function binding(
  identity: AuthorityRuntimeIdentity,
  input: {
    action: string;
    target: string;
    configuredRoot: string;
    plan: Record<string, unknown>;
  },
) {
  return {
    repository: identity.repository,
    worktree: identity.worktree,
    root: identity.root,
    target: input.target,
    plugin: PLUGIN,
    content_hash: content(input.action, input.target, input.configuredRoot, input.plan),
    context: input.configuredRoot,
    source_head: identity.sourceHead,
  };
}

export async function persistSpiritFlixAdminPreview(
  action: string,
  target: string,
  plan: Record<string, unknown>,
) {
  const identity = await resolveAuthorityRuntimeIdentity();
  const configuredRoot = await configuredAdminRoot(identity);
  const saved = await invoke(
    identity,
    "persist-preview",
    binding(identity, { action, target, configuredRoot, plan }),
  );
  return saved.ok
    ? {
        ok: true as const,
        value: {
          preview_id: String(saved.value.preview_id),
          generation: Number(saved.value.generation),
          action,
          target,
          plan,
          configured_root: configuredRoot,
        },
      }
    : saved;
}

export async function issueSpiritFlixAdminApproval(preview_id: string, generation: number) {
  const identity = await resolveAuthorityRuntimeIdentity();
  return invoke(identity, "issue", {
    preview_id,
    expected_generation: String(generation),
    consumer: CONSUMER,
    operation: OPERATION,
    expires_at: new Date(Date.now() + 300_000).toISOString(),
  });
}

export async function consumeSpiritFlixAdminApproval(
  approval_id: string,
  action: string,
  target: string,
  plan: Record<string, unknown>,
) {
  const identity = await resolveAuthorityRuntimeIdentity();
  const configuredRoot = await configuredAdminRoot(identity);
  const loaded = await invoke(identity, "lookup", { approval_id });
  if (!loaded.ok) return loaded;
  if (loaded.value.consumer !== CONSUMER || loaded.value.operation !== OPERATION) {
    return { ok: false as const, reason: "spiritflix_admin_consumer_mismatch" };
  }
  return invoke(identity, "consume", {
    ...binding(identity, { action, target, configuredRoot, plan }),
    approval_id,
    generation: String(loaded.value.generation),
    consumer: CONSUMER,
    operation: OPERATION,
    preview: loaded.value.preview,
  });
}

export async function finalizeSpiritFlixAdminApproval(
  approval_id: string,
  action: string,
  target: string,
  plan: Record<string, unknown>,
  generation: number,
  status: "succeeded" | "failed",
  finalization?: SpiritFlixAdminFinalizationEvidence,
) {
  const identity = await resolveAuthorityRuntimeIdentity();
  const configuredRoot = await configuredAdminRoot(identity);
  const loaded = await invoke(identity, "lookup", { approval_id });
  if (!loaded.ok) return loaded;
  return invoke(identity, "finalize", {
    ...binding(identity, { action, target, configuredRoot, plan }),
    approval_id,
    generation: String(generation),
    consumer: CONSUMER,
    operation: OPERATION,
    preview: loaded.value.preview,
    result_id: `spiritflix-admin-${randomUUID()}`,
    evidence: JSON.stringify({
      operation: OPERATION,
      redacted: true,
      ...(finalization ?? {
        participant_invocations: [],
        redaction_verdict: "passed",
        result_hash: "unavailable",
        result_schema: "spiritflix-admin-result/unavailable",
      }),
    }),
    status,
  });
}

export async function compensateSpiritFlixAdminApproval(
  approval_id: string,
  action: string,
  target: string,
  plan: Record<string, unknown>,
  generation: number,
  finalization: SpiritFlixAdminFinalizationEvidence,
) {
  const identity = await resolveAuthorityRuntimeIdentity();
  const configuredRoot = await configuredAdminRoot(identity);
  const loaded = await invoke(identity, "lookup", { approval_id });
  if (!loaded.ok) return loaded;
  if (loaded.value.consumer !== CONSUMER || loaded.value.operation !== OPERATION) {
    return { ok: false as const, reason: "spiritflix_admin_consumer_mismatch" };
  }
  return invoke(identity, "compensate", {
    ...binding(identity, { action, target, configuredRoot, plan }),
    approval_id,
    generation: String(generation),
    consumer: CONSUMER,
    operation: OPERATION,
    preview: loaded.value.preview,
    result_hash: finalization.result_hash,
    evidence: JSON.stringify({
      operation: OPERATION,
      redacted: true,
      compensation: true,
      ...finalization,
    }),
  });
}
