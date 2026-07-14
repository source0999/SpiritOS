import { auditOperatorAction, createOperatorApprovalAssertion, requireOperatorSession } from "@/lib/coding/operator-approval-session";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";

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
  const allowed = new Set(["action", "generation", "preview_id", "proposal_id"]);
  if (Object.keys(body).some((key) => !allowed.has(key))) return Response.json({ reason_code: "operator_client_authority_binding_forbidden" }, { status: 400, headers: { "Cache-Control": "no-store" } });
  const { action, generation, preview_id: previewId, proposal_id: proposalId } = body;
  if ((action !== "approve" && action !== "reject") || !Number.isInteger(generation) || (generation as number) < 1 || typeof previewId !== "string" || !previewId || typeof proposalId !== "string" || !proposalId) return Response.json({ reason_code: "operator_request_invalid" }, { status: 400, headers: { "Cache-Control": "no-store" } });
  try {
    const session = await requireOperatorSession(request);
    if (session.role !== "approval-issuer") throw new Error("operator_role_forbidden");
    const assertion = await createOperatorApprovalAssertion(session, { action, generation: generation as number, preview_id: previewId, task_id: proposalId });
    const response = await sourceProxyFetch(`/v1/cartographer/proposals/${encodeURIComponent(proposalId)}/operator-selection`, {
      body: JSON.stringify({ action, generation, preview_id: previewId }),
      headers: { "content-type": "application/json", "x-spiritos-operator-assertion": assertion },
      method: "POST",
    });
    const text = await response.text();
    if (!response.ok) return new Response(text, { status: response.status, headers: { "Cache-Control": "no-store", "content-type": response.headers.get("content-type") ?? "application/json" } });
    await auditOperatorAction(session, action, previewId);
    return new Response(text, { headers: { "Cache-Control": "no-store", "content-type": response.headers.get("content-type") ?? "application/json" } });
  } catch (error) {
    return Response.json({ reason_code: error instanceof Error ? error.message : "operator_approval_failed" }, { status: 403, headers: { "Cache-Control": "no-store" } });
  }
}
