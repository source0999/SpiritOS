import { auditOperatorAction, createOperatorApprovalAssertion, requireOperatorSession } from "@/lib/coding/operator-approval-session";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export const runtime = "nodejs";

const taskId = "campaign-3.5:model-call-authority";

async function forward(request: Request, action: "approve" | "reject") {
  try {
    const session = await requireOperatorSession(request);
    if (session.role !== "approval-issuer") throw new Error("operator_role_forbidden");
    const previewId = `campaign-3.5:model-call-authority:${action === "approve" ? "issue" : "revoke"}`;
    const assertion = await createOperatorApprovalAssertion(session, { action, generation: 1, preview_id: previewId, task_id: taskId });
    const response = await sourceProxyFetch("/v1/campaigns/campaign-3.5/model-call-authority", {
      headers: { "x-spiritos-operator-assertion": assertion },
      method: action === "approve" ? "POST" : "DELETE",
    });
    const text = await response.text();
    if (!response.ok) return new Response(text, { headers: { "Cache-Control": "no-store", "content-type": response.headers.get("content-type") ?? "application/json" }, status: response.status });
    await auditOperatorAction(session, action, previewId);
    return new Response(text, { headers: { "Cache-Control": "no-store", "content-type": response.headers.get("content-type") ?? "application/json" }, status: response.status });
  } catch (error) {
    return Response.json({ reason_code: error instanceof Error ? error.message : "campaign_3_5_model_call_authority_failed" }, { status: 403, headers: { "Cache-Control": "no-store" } });
  }
}

export async function POST(request: Request) { return forward(request, "approve"); }
export async function DELETE(request: Request) { return forward(request, "reject"); }
