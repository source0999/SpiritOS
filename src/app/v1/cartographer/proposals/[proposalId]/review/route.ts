import {
  auditOperatorAction,
  createOperatorApprovalAssertion,
  requireOperatorSession,
} from "@/lib/coding/operator-approval-session";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{
    proposalId: string;
  }>;
};

const reviewDecisions = new Set(["approve", "reject", "request_edit", "defer", "mark_stale"]);

type ProxyResponseMetadata = {
  headers: { get(name: string): string | null };
  status: number;
  statusText: string;
};

function responseFromProxy(response: ProxyResponseMetadata, text: string) {
  return new Response(text, {
    headers: {
      "Cache-Control": "no-store",
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
    status: response.status,
    statusText: response.statusText,
  });
}

export async function POST(request: Request, context: RouteContext) {
  const { proposalId } = await context.params;
  let body: Record<string, unknown>;
  try {
    const value = await request.json();
    if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("invalid");
    body = value as Record<string, unknown>;
  } catch {
    return Response.json(
      { reason_code: "operator_request_invalid" },
      { status: 400, headers: { "Cache-Control": "no-store" } },
    );
  }

  if (Object.keys(body).some((key) => key !== "decision" && key !== "reason")) {
    return Response.json(
      { reason_code: "operator_client_authority_binding_forbidden" },
      { status: 400, headers: { "Cache-Control": "no-store" } },
    );
  }
  const decision = body.decision;
  const reason = body.reason;
  if (
    typeof decision !== "string" ||
    !reviewDecisions.has(decision) ||
    (reason !== undefined && typeof reason !== "string")
  ) {
    return Response.json(
      { reason_code: "operator_request_invalid" },
      { status: 400, headers: { "Cache-Control": "no-store" } },
    );
  }

  try {
    // Same-origin and the short-lived operator session remain mandatory. The
    // Source Proxy mutation receives a separately signed assertion below.
    const session = await requireOperatorSession(request, false);
    if (session.role !== "approval-issuer") throw new Error("operator_role_forbidden");
    const reviewRequest = { decision, ...(reason === undefined ? {} : { reason }) };
    const previewResponse = await sourceProxyFetch(
      `/v1/cartographer/proposals/${encodeURIComponent(proposalId)}/review-preview`,
      {
        body: JSON.stringify(reviewRequest),
        headers: { "content-type": "application/json" },
        method: "POST",
      },
    );
    const previewText = await previewResponse.text();
    if (!previewResponse.ok) return responseFromProxy(previewResponse, previewText);
    let previewPayload: { preview?: { generation?: unknown; preview_id?: unknown } };
    try {
      previewPayload = JSON.parse(previewText) as typeof previewPayload;
    } catch {
      return Response.json(
        { reason_code: "proposal_review_preview_invalid" },
        { status: 502, headers: { "Cache-Control": "no-store" } },
      );
    }
    const previewId = previewPayload.preview?.preview_id;
    const generation = previewPayload.preview?.generation;
    if (typeof previewId !== "string" || !previewId || !Number.isInteger(generation)) {
      return Response.json(
        { reason_code: "proposal_review_preview_invalid" },
        { status: 502, headers: { "Cache-Control": "no-store" } },
      );
    }
    await auditOperatorAction(session, "preview", previewId);
    const action = decision === "approve" ? "approve" : "reject";
    const assertion = await createOperatorApprovalAssertion(session, {
      action,
      generation: generation as number,
      preview_id: previewId,
      task_id: proposalId,
    });
    const response = await sourceProxyFetch(
      `/v1/cartographer/proposals/${encodeURIComponent(proposalId)}/review`,
      {
        body: JSON.stringify({ ...reviewRequest, generation, preview_id: previewId }),
        headers: {
          "content-type": "application/json",
          "x-spiritos-operator-assertion": assertion,
        },
        method: "POST",
      },
    );
    const text = await response.text();
    if (response.ok) await auditOperatorAction(session, action, previewId);
    return responseFromProxy(response, text);
  } catch (error) {
    return Response.json(
      { reason_code: error instanceof Error ? error.message : "operator_approval_failed" },
      { status: 403, headers: { "Cache-Control": "no-store" } },
    );
  }
}
