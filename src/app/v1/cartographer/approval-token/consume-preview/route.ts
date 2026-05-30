import { sourceProxyFetch } from "@/lib/source-proxy-origin";

const APPROVAL_TOKEN_CONSUME_PREVIEW_PATH =
  "/v1/cartographer/approval-token/consume-preview";

export async function GET() {
  return proxyApprovalTokenConsumptionPreview();
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  return proxyApprovalTokenConsumptionPreview({
    method: "POST",
    body: JSON.stringify(body),
    headers: {
      "content-type": "application/json",
    },
  });
}

async function proxyApprovalTokenConsumptionPreview(
  init?: Parameters<typeof sourceProxyFetch>[1],
) {
  let response;
  try {
    response = await sourceProxyFetch(APPROVAL_TOKEN_CONSUME_PREVIEW_PATH, {
      method: "GET",
      ...init,
    });
  } catch (error) {
    return Response.json(
      {
        runtime: {
          status: "unavailable",
          preview_only: true,
          authority_granted: false,
          write_authority_granted: false,
          command_authority_granted: false,
          workflow_authority_granted: false,
          queue_authority_granted: false,
          git_authority_granted: false,
        },
        preview: {
          status: "blocked",
          eligible: false,
          blocked: true,
          reasons: ["source_proxy_unavailable"],
          preview_only: true,
          authority_granted: false,
          write_authority_granted: false,
          command_authority_granted: false,
          workflow_authority_granted: false,
          queue_authority_granted: false,
          git_authority_granted: false,
          safe_next_action:
            "Stop and inspect Source Proxy before relying on approval-token consumption preview.",
        },
        detail:
          error instanceof Error
            ? error.message
            : "The approval-token consumption preview route could not reach Source Proxy.",
      },
      { status: 200 },
    );
  }

  return new Response(await response.text(), {
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
    status: response.status,
    statusText: response.statusText,
  });
}
