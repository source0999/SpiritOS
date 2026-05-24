import { sourceProxyFetch } from "@/lib/source-proxy-origin";

const APPROVAL_TOKEN_VALIDATE_PATH = "/v1/cartographer/approval-token/validate";

export async function GET() {
  return proxyApprovalTokenValidation();
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  return proxyApprovalTokenValidation({
    method: "POST",
    body: JSON.stringify(body),
    headers: {
      "content-type": "application/json",
    },
  });
}

async function proxyApprovalTokenValidation(init?: Parameters<typeof sourceProxyFetch>[1]) {
  let response;
  try {
    response = await sourceProxyFetch(APPROVAL_TOKEN_VALIDATE_PATH, {
      method: "GET",
      ...init,
    });
  } catch (error) {
    return Response.json(
      {
        runtime: {
          status: "unavailable",
          validation_only: true,
          authority_granted: false,
          write_authority_granted: false,
          command_authority_granted: false,
          workflow_authority_granted: false,
          queue_authority_granted: false,
          git_authority_granted: false,
          self_approval_allowed: false,
        },
        validation: {
          status: "rejected",
          accepted: false,
          rejected: true,
          reasons: ["source_proxy_unavailable"],
          authority_granted: false,
          write_authority_granted: false,
          command_authority_granted: false,
          workflow_authority_granted: false,
          queue_authority_granted: false,
          git_authority_granted: false,
          validation_only: true,
          safe_next_action:
            "Stop and inspect Source Proxy before relying on approval-token validation.",
        },
        detail:
          error instanceof Error
            ? error.message
            : "The approval-token validation route could not reach Source Proxy.",
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
