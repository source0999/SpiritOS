import { auditOperatorAction, requireOperatorSession } from "@/lib/coding/operator-approval-session";
import {
  type SpiritFlixAdminApprovalWriter,
  resolveSpiritFlixAdminApprovalBinding,
} from "@/lib/coding/spiritflix-admin-approval-binding";
import {
  issueSpiritFlixAdminApproval,
  persistSpiritFlixAdminPreview,
} from "@/lib/coding/spiritflix-admin-approval-authority";

export const runtime = "nodejs";

type PreviewRequest = {
  action?: unknown;
  generation?: unknown;
  mutation?: unknown;
  preview_id?: unknown;
  writer?: unknown;
};

const WRITERS = new Set<SpiritFlixAdminApprovalWriter>([
  "admin-action",
  "face-learning",
  "library-smart-rescan",
  "manual-model",
  "manual-tags",
  "smart-analysis",
  "smart-batch",
]);

function isWriter(value: unknown): value is SpiritFlixAdminApprovalWriter {
  return typeof value === "string" && WRITERS.has(value as SpiritFlixAdminApprovalWriter);
}

function isPreviewRequest(body: PreviewRequest): body is PreviewRequest & {
  action: "preview";
  mutation: Record<string, unknown>;
  writer: SpiritFlixAdminApprovalWriter;
} {
  return body.action === "preview" && isWriter(body.writer) && Boolean(body.mutation && typeof body.mutation === "object" && !Array.isArray(body.mutation));
}

function isApproveRequest(body: PreviewRequest): body is PreviewRequest & {
  action: "approve";
  generation: number;
  preview_id: string;
} {
  return body.action === "approve" && typeof body.preview_id === "string" && Number.isInteger(body.generation);
}

export async function POST(request: Request) {
  let body: PreviewRequest;
  try {
    body = await request.json() as PreviewRequest;
  } catch {
    return Response.json({ reason_code: "operator_request_invalid" }, { status: 400 });
  }
  if (!body || typeof body !== "object") {
    return Response.json({ reason_code: "operator_request_invalid" }, { status: 400 });
  }

  try {
    // The HttpOnly cookie is SameSite=Strict and this check still enforces an
    // exact configured Origin/Host pair. SpiritFlix callers therefore reuse an
    // authenticated operator session without exposing its CSRF secret to a
    // second application surface.
    const session = await requireOperatorSession(request, false);
    if (session.role !== "approval-issuer") throw new Error("operator_role_forbidden");

    if (isPreviewRequest(body)) {
      if (Object.keys(body).some((key) => !["action", "writer", "mutation"].includes(key))) {
        return Response.json({ reason_code: "operator_client_authority_binding_forbidden" }, { status: 400 });
      }
      const binding = await resolveSpiritFlixAdminApprovalBinding(body.writer, body.mutation);
      const preview = await persistSpiritFlixAdminPreview(binding.action, binding.target, binding.plan);
      if (!preview.ok) return Response.json({ reason_code: preview.reason }, { status: 422 });
      await auditOperatorAction(session, "preview", preview.value.preview_id);
      return Response.json({
        authority: "spiritos-approval-authority",
        consumer: "spiritflix-admin-executor",
        preview: preview.value,
      }, { headers: { "Cache-Control": "no-store" } });
    }

    if (!isApproveRequest(body) || Object.keys(body).some((key) => !["action", "preview_id", "generation"].includes(key))) {
      return Response.json({ reason_code: "operator_client_authority_binding_forbidden" }, { status: 400 });
    }
    const issued = await issueSpiritFlixAdminApproval(body.preview_id, body.generation);
    if (!issued.ok) return Response.json({ reason_code: issued.reason }, { status: 422 });
    await auditOperatorAction(session, "approve", body.preview_id);
    return Response.json({
      authority: "spiritos-approval-authority",
      consumer: "spiritflix-admin-executor",
      approval: issued,
    }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return Response.json({
      reason_code: error instanceof Error ? error.message : "operator_approval_failed",
    }, { status: 403 });
  }
}
