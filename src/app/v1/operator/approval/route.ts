import { auditOperatorAction, createOperatorApprovalAssertion, requireOperatorSession } from "@/lib/coding/operator-approval-session";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";

type OperatorAction = "approve" | "reject";

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
  const allowed = new Set(["action", "generation", "preview_id", "task_id"]);
  if (Object.keys(body).some((key) => !allowed.has(key))) {
    return Response.json({ reason_code: "operator_client_authority_binding_forbidden" }, { status: 400, headers: { "Cache-Control": "no-store" } });
  }
  const action = body.action;
  const generation = body.generation;
  const previewId = body.preview_id;
  const taskId = body.task_id;
  if ((action !== "approve" && action !== "reject") || !Number.isInteger(generation) || (generation as number) < 1 || typeof previewId !== "string" || !previewId || typeof taskId !== "string" || !taskId) {
    return Response.json({ reason_code: "operator_request_invalid" }, { status: 400, headers: { "Cache-Control": "no-store" } });
  }
  try {
    const session = await requireOperatorSession(request);
    if (session.role !== "approval-issuer") throw new Error("operator_role_forbidden");
    const assertion = await createOperatorApprovalAssertion(session, { action: action as OperatorAction, generation: generation as number, preview_id: previewId, task_id: taskId });
    const response = await sourceProxyFetch(`/v1/tasks/long-running/${encodeURIComponent(taskId)}/operator-approval`, {
      body: JSON.stringify({ action, generation, preview_id: previewId }),
      headers: { "content-type": "application/json", "x-spiritos-operator-assertion": assertion },
      method: "POST",
    });
    const text = await response.text();
    if (!response.ok) return new Response(text, { headers: { "Cache-Control": "no-store", "content-type": response.headers.get("content-type") ?? "application/json" }, status: response.status });
    await auditOperatorAction(session, action as OperatorAction, previewId);
    return new Response(text, { headers: { "Cache-Control": "no-store", "content-type": response.headers.get("content-type") ?? "application/json" }, status: response.status });
  } catch (error) {
    return Response.json({ reason_code: error instanceof Error ? error.message : "operator_approval_failed" }, { status: 403, headers: { "Cache-Control": "no-store" } });
  }
}
