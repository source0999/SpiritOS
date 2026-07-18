import { auditOperatorAction, createOperatorApprovalAssertion, requireOperatorSession } from "@/lib/coding/operator-approval-session";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";

const RESET_PREVIEW_ID = "dummy-product-site-reset";
const RESET_PROMPT_ID = "coder-001-init-dummy-product-site";

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      {
        error: "SPIRIT_CODING_USE_PROXY is not true",
        reason_code: "coding_proxy_disabled",
      },
      { status: 409 },
    );
  }

  let assertion: string;
  let body: string;
  try {
    const session = await requireOperatorSession(request);
    if (session.role !== "approval-issuer") throw new Error("operator_role_forbidden");
    assertion = await createOperatorApprovalAssertion(session, {
      action: "approve",
      generation: 1,
      preview_id: RESET_PREVIEW_ID,
      task_id: RESET_PROMPT_ID,
    });
    body = await request.text();
    await auditOperatorAction(session, "approve", RESET_PREVIEW_ID);
  } catch (error) {
    return Response.json(
      {
        error: "Authenticated dummy product site reset is forbidden",
        reason_code: error instanceof Error ? error.message : "operator_reset_forbidden",
      },
      { status: 403 },
    );
  }

  try {
    const response = await sourceProxyFetch("/v1/coding/dummy-product-site/reset", {
      body,
      headers: {
        "content-type": "application/json",
        "x-spiritos-operator-assertion": assertion,
      },
      method: "POST",
    });
    const text = await response.text();
    return new Response(text, {
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
      status: response.status,
      statusText: response.statusText,
    });
  } catch (error) {
    return Response.json(
      {
        error: "Source Proxy dummy product site reset is unavailable",
        reason_code: "source_proxy_unavailable",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
      },
      { status: 502 },
    );
  }
}
