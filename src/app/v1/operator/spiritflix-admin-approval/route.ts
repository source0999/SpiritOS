import { auditOperatorAction, requireOperatorSession } from "@/lib/coding/operator-approval-session";
import { issueSpiritFlixAdminApproval, persistSpiritFlixAdminPreview } from "@/lib/coding/spiritflix-admin-approval-authority";

export const runtime = "nodejs";
const ACTION = "index.rebuild";
const TARGET = "spiritflix:library-smart-rescan";
const PLAN = { runner: "face-organizer", version: 1 };

export async function POST(request: Request) {
  let body: { action?: unknown; generation?: unknown; preview_id?: unknown };
  try { body = await request.json(); } catch { return Response.json({ reason_code: "operator_request_invalid" }, { status: 400 }); }
  if (!body || typeof body !== "object" || Object.keys(body).some((key) => !["action", "generation", "preview_id"].includes(key))) return Response.json({ reason_code: "operator_client_authority_binding_forbidden" }, { status: 400 });
  try {
    const session = await requireOperatorSession(request);
    if (session.role !== "approval-issuer") throw new Error("operator_role_forbidden");
    if (body.action === "preview") {
      const preview = await persistSpiritFlixAdminPreview(ACTION, TARGET, PLAN);
      if (!preview.ok) return Response.json({ reason_code: preview.reason }, { status: 422 });
      await auditOperatorAction(session, "approve", preview.value.preview_id);
      return Response.json({ authority: "spiritos-approval-authority", consumer: "spiritflix-admin-executor", preview: preview.value }, { headers: { "Cache-Control": "no-store" } });
    }
    if (body.action !== "approve" || !Number.isInteger(body.generation) || typeof body.preview_id !== "string") return Response.json({ reason_code: "operator_request_invalid" }, { status: 400 });
    const issued = await issueSpiritFlixAdminApproval(body.preview_id, body.generation as number);
    if (!issued.ok) return Response.json({ reason_code: issued.reason }, { status: 422 });
    await auditOperatorAction(session, "approve", body.preview_id);
    return Response.json({ authority: "spiritos-approval-authority", consumer: "spiritflix-admin-executor", approval: issued }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) { return Response.json({ reason_code: error instanceof Error ? error.message : "operator_approval_failed" }, { status: 403 }); }
}
