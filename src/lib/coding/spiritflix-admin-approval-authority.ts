import "server-only";

import { randomUUID } from "node:crypto";
import { join } from "node:path";
import { spawn } from "node:child_process";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { hashApprovalContent } from "@/lib/coding/design-approval-authority";

const execFileAsync = promisify(execFile);
const ROOT = "/home/source/SpiritOS-campaign-1-20260712";
const SCRIPT = join(process.cwd(), "scripts", "approval-authority.py");
const CONSUMER = "spiritflix-admin-executor";
const OPERATION = "spiritflix_admin_mutation";
const PLUGIN = "spiritflix-admin";

async function head() { return (await execFileAsync("git", ["rev-parse", "HEAD"], { cwd: ROOT })).stdout.trim(); }
async function invoke(command: string, input: Record<string, unknown>) {
  const result = await new Promise<{ code: number; text: string }>((resolve) => { const child = spawn("python3", [SCRIPT, command], { stdio: ["pipe", "pipe", "ignore"] }); let text = ""; child.stdout.on("data", (chunk) => text += chunk); child.on("close", (code) => resolve({ code: code ?? 1, text })); child.stdin.end(JSON.stringify(input)); });
  try { const value = JSON.parse(result.text); return result.code === 0 ? { ok: true as const, value } : { ok: false as const, reason: String(value.reason ?? "approval_issuer_unavailable") }; } catch { return { ok: false as const, reason: "approval_issuer_unavailable" }; }
}
function content(action: string, target: string, plan: Record<string, unknown>) { return hashApprovalContent({ action, configured_root: "spiritflix-configured-admin-root", plan, target }); }
function binding(input: { action: string; target: string; plan: Record<string, unknown>; source_head: string }) { return { repository: "SpiritOS", worktree: ROOT, root: ROOT, target: input.target, plugin: PLUGIN, content_hash: content(input.action, input.target, input.plan), context: "spiritflix-configured-admin-root", source_head: input.source_head }; }

export async function persistSpiritFlixAdminPreview(action: string, target: string, plan: Record<string, unknown>) { const source_head = await head(); const saved = await invoke("persist-preview", binding({ action, target, plan, source_head })); return saved.ok ? { ok: true as const, value: { preview_id: String(saved.value.preview_id), generation: Number(saved.value.generation), action, target, plan } } : saved; }
export async function issueSpiritFlixAdminApproval(preview_id: string, generation: number) { return invoke("issue", { preview_id, expected_generation: String(generation), consumer: CONSUMER, operation: OPERATION, expires_at: new Date(Date.now() + 300000).toISOString() }); }
export async function consumeSpiritFlixAdminApproval(approval_id: string, action: string, target: string, plan: Record<string, unknown>) { const loaded = await invoke("lookup", { approval_id }); if (!loaded.ok) return loaded; if (loaded.value.consumer !== CONSUMER || loaded.value.operation !== OPERATION) return { ok: false as const, reason: "spiritflix_admin_consumer_mismatch" }; const source_head = await head(); return invoke("consume", { ...binding({ action, target, plan, source_head }), approval_id, generation: String(loaded.value.generation), consumer: CONSUMER, operation: OPERATION, preview: loaded.value.preview }); }
export async function finalizeSpiritFlixAdminApproval(approval_id: string, action: string, target: string, plan: Record<string, unknown>, generation: number, status: "succeeded" | "failed") { const source_head = await head(); const loaded = await invoke("lookup", { approval_id }); if (!loaded.ok) return loaded; return invoke("finalize", { ...binding({ action, target, plan, source_head }), approval_id, generation: String(generation), consumer: CONSUMER, operation: OPERATION, preview: loaded.value.preview, result_id: `spiritflix-admin-${randomUUID()}`, evidence: JSON.stringify({ redacted: true }), status }); }
