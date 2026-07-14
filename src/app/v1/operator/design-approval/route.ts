import { auditOperatorAction, requireOperatorSession } from "@/lib/coding/operator-approval-session";
import { issueDesignWritebackApproval, rejectDesignWritebackPreview, resolveDesignWritebackPreview } from "@/lib/coding/design-approval-authority";

export const runtime = "nodejs";

export async function POST(request: Request) {
  let body: Record<string, unknown>;
  try {
    const value = await request.json();
    if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("invalid");
    body = value as Record<string, unknown>;
  } catch {
    return Response.json({ reason_code: "operator_request_invalid" }, { status: 400, headers: { "Cache-Control": "no-store" } });
  }
  const allowed = new Set(["action", "generation", "preview_id"]);
  if (Object.keys(body).some((key) => !allowed.has(key))) return Response.json({ reason_code: "operator_client_authority_binding_forbidden" }, { status: 400, headers: { "Cache-Control": "no-store" } });
  const action = body.action;
  const generation = body.generation;
  const previewId = body.preview_id;
  if ((action !== "approve" && action !== "reject") || !Number.isInteger(generation) || (generation as number) < 1 || typeof previewId !== "string" || !previewId) return Response.json({ reason_code: "operator_request_invalid" }, { status: 400, headers: { "Cache-Control": "no-store" } });
  try {
    const session = await requireOperatorSession(request);
    if (session.role !== "approval-issuer") throw new Error("operator_role_forbidden");
    const preview = await resolveDesignWritebackPreview(previewId, generation as number);
    if (!preview.ok) return Response.json({ reason_code: preview.reason }, { status: 422, headers: { "Cache-Control": "no-store" } });
    const outcome = action === "approve" ? await issueDesignWritebackApproval(preview.value) : await rejectDesignWritebackPreview(preview.value);
    if (!outcome.ok) return Response.json({ reason_code: outcome.reason }, { status: 422, headers: { "Cache-Control": "no-store" } });
    await auditOperatorAction(session, action, previewId);
    return Response.json({ authority: "spiritos-approval-authority", consumer: "design-writeback", action, preview: preview.value, ...(action === "approve" ? { approval: outcome.value } : { rejected: outcome.value }) }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return Response.json({ reason_code: error instanceof Error ? error.message : "operator_approval_failed" }, { status: 403, headers: { "Cache-Control": "no-store" } });
  }
}
