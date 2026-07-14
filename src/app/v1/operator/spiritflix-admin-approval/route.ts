import { auditOperatorAction, requireOperatorSession } from "@/lib/coding/operator-approval-session";
import { issueSpiritFlixAdminApproval, persistSpiritFlixAdminPreview } from "@/lib/coding/spiritflix-admin-approval-authority";

export const runtime = "nodejs";

type PreviewBinding = { action: string; target: string; plan: Record<string, unknown> };
type PreviewRequest = {
  action?: unknown;
  writer?: unknown;
  item_id?: unknown;
  model_name?: unknown;
  manual_tags?: unknown;
  admin_action?: unknown;
  mode?: unknown;
  path?: unknown;
  paths?: unknown;
  batch_action?: unknown;
  generation?: unknown;
  preview_id?: unknown;
};

function string(value: unknown, field: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`operator_preview_${field}_invalid`);
  return value.trim();
}

function optionalPaths(value: unknown): string[] {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || !item.trim())) {
    throw new Error("operator_preview_paths_invalid");
  }
  return value.map((item) => item.trim());
}

function assertOnlyKeys(body: PreviewRequest, allowed: string[]): void {
  if (Object.keys(body).some((key) => !allowed.includes(key))) throw new Error("operator_client_authority_binding_forbidden");
}

/**
 * A browser can select a bounded writer/input, but only this server map derives
 * the approval action, target, and plan.  The subsequent approve request carries
 * only a persisted preview ID and generation, never caller authority bindings.
 */
function resolvePreviewBinding(body: PreviewRequest): PreviewBinding {
  const writer = string(body.writer, "writer");
  switch (writer) {
    case "library-smart-rescan":
      assertOnlyKeys(body, ["action", "writer"]);
      return { action: "index.rebuild", target: "spiritflix:library-smart-rescan", plan: { runner: "face-organizer", version: 1 } };
    case "admin-action": {
      assertOnlyKeys(body, ["action", "writer", "admin_action", "mode"]);
      const adminAction = string(body.admin_action, "admin_action");
      return { action: "admin.action", target: `spiritflix:admin-actions:${adminAction}`, plan: { mode: string(body.mode, "mode") } };
    }
    case "smart-analysis": {
      assertOnlyKeys(body, ["action", "writer", "path", "batch_action"]);
      const path = string(body.path, "path");
      return { action: "smart.analysis", target: `spiritflix:smart-analysis:${path}`, plan: { action: string(body.batch_action, "batch_action") } };
    }
    case "smart-batch": {
      assertOnlyKeys(body, ["action", "writer", "path", "paths", "batch_action"]);
      const path = typeof body.path === "string" && body.path.trim() ? body.path.trim() : "";
      const paths = optionalPaths(body.paths);
      if (!path && paths.length === 0) throw new Error("operator_preview_batch_target_invalid");
      return { action: "smart.batch", target: `spiritflix:smart-batch:${path || paths.join(",")}`, plan: { action: string(body.batch_action, "batch_action") } };
    }
    case "manual-model": {
      assertOnlyKeys(body, ["action", "writer", "item_id", "model_name"]);
      const itemId = string(body.item_id, "item_id");
      return { action: "metadata.mutation", target: `spiritflix:videos:${itemId}:model`, plan: { field: "modelName", value: string(body.model_name, "model_name") } };
    }
    case "manual-tags": {
      assertOnlyKeys(body, ["action", "writer", "item_id", "manual_tags"]);
      const itemId = string(body.item_id, "item_id");
      if (!Array.isArray(body.manual_tags) || body.manual_tags.some((tag) => typeof tag !== "string")) throw new Error("operator_preview_manual_tags_invalid");
      return { action: "metadata.mutation", target: `spiritflix:videos:${itemId}:tags`, plan: { field: "manualTags", count: body.manual_tags.length } };
    }
    case "face-learning": {
      assertOnlyKeys(body, ["action", "writer", "item_id", "model_name"]);
      const itemId = string(body.item_id, "item_id");
      return { action: "face.learning", target: `spiritflix:videos:${itemId}:face-learning`, plan: { modelName: string(body.model_name, "model_name") } };
    }
    default:
      throw new Error("operator_preview_writer_forbidden");
  }
}

function isPreviewRequest(body: PreviewRequest): boolean {
  return body.action === "preview";
}

function isApproveRequest(body: PreviewRequest): body is PreviewRequest & { preview_id: string; generation: number } {
  return body.action === "approve" && typeof body.preview_id === "string" && Number.isInteger(body.generation);
}

export async function POST(request: Request) {
  let body: PreviewRequest;
  try { body = await request.json(); } catch { return Response.json({ reason_code: "operator_request_invalid" }, { status: 400 }); }
  if (!body || typeof body !== "object") return Response.json({ reason_code: "operator_request_invalid" }, { status: 400 });
  try {
    const session = await requireOperatorSession(request);
    if (session.role !== "approval-issuer") throw new Error("operator_role_forbidden");
    if (isPreviewRequest(body)) {
      const binding = resolvePreviewBinding(body);
      const preview = await persistSpiritFlixAdminPreview(binding.action, binding.target, binding.plan);
      if (!preview.ok) return Response.json({ reason_code: preview.reason }, { status: 422 });
      await auditOperatorAction(session, "preview", preview.value.preview_id);
      return Response.json({ authority: "spiritos-approval-authority", consumer: "spiritflix-admin-executor", preview: preview.value }, { headers: { "Cache-Control": "no-store" } });
    }
    if (!isApproveRequest(body) || Object.keys(body).some((key) => !["action", "preview_id", "generation"].includes(key))) return Response.json({ reason_code: "operator_client_authority_binding_forbidden" }, { status: 400 });
    const issued = await issueSpiritFlixAdminApproval(body.preview_id, body.generation as number);
    if (!issued.ok) return Response.json({ reason_code: issued.reason }, { status: 422 });
    await auditOperatorAction(session, "approve", body.preview_id);
    return Response.json({ authority: "spiritos-approval-authority", consumer: "spiritflix-admin-executor", approval: issued }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) { return Response.json({ reason_code: error instanceof Error ? error.message : "operator_approval_failed" }, { status: 403 }); }
}
