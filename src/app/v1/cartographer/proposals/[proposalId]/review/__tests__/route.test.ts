/// <reference types="vitest/globals" />

import {
  auditOperatorAction,
  createOperatorApprovalAssertion,
  requireOperatorSession,
} from "@/lib/coding/operator-approval-session";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { POST } from "../route";

vi.mock("@/lib/coding/operator-approval-session", () => ({
  auditOperatorAction: vi.fn(),
  createOperatorApprovalAssertion: vi.fn(),
  requireOperatorSession: vi.fn(),
}));
vi.mock("@/lib/source-proxy-origin", () => ({ sourceProxyFetch: vi.fn() }));

const mockedAudit = vi.mocked(auditOperatorAction);
const mockedAssertion = vi.mocked(createOperatorApprovalAssertion);
const mockedSession = vi.mocked(requireOperatorSession);
const mockedProxy = vi.mocked(sourceProxyFetch);

function request(body: unknown) {
  return new Request("https://operator.spirit.test/v1/cartographer/proposals/bp-1/review", {
    body: JSON.stringify(body),
    headers: {
      "content-type": "application/json",
      cookie: "spiritos_operator_approval=session-1",
      host: "operator.spirit.test",
      origin: "https://operator.spirit.test",
    },
    method: "POST",
  });
}

const context = { params: Promise.resolve({ proposalId: "bp-1" }) };

describe("Cartographer authenticated proposal review route", () => {
  beforeEach(() => {
    mockedAudit.mockReset();
    mockedAssertion.mockReset();
    mockedSession.mockReset();
    mockedProxy.mockReset();
    mockedSession.mockResolvedValue({
      id: "session-1",
      operator: "spiritos-local-operator",
      origin: "https://operator.spirit.test",
      role: "approval-issuer",
    });
    mockedAssertion.mockResolvedValue("signed-review-assertion");
  });

  it("creates a server preview then forwards only its signed approval binding", async () => {
    mockedProxy
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ preview: { generation: 1, preview_id: "prv_review" } }),
          { headers: { "content-type": "application/json" }, status: 200 },
        ) as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ proposal: { proposal_id: "bp-1", status: "approved" } }), {
          headers: { "content-type": "application/json" },
          status: 200,
        }) as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
      );

    const response = await POST(request({ decision: "approve" }), context);

    expect(response.status).toBe(200);
    expect(mockedSession).toHaveBeenCalledWith(expect.any(Request), false);
    expect(mockedProxy).toHaveBeenNthCalledWith(
      1,
      "/v1/cartographer/proposals/bp-1/review-preview",
      expect.objectContaining({ body: JSON.stringify({ decision: "approve" }), method: "POST" }),
    );
    expect(mockedAssertion).toHaveBeenCalledWith(expect.objectContaining({ id: "session-1" }), {
      action: "approve",
      generation: 1,
      preview_id: "prv_review",
      task_id: "bp-1",
    });
    expect(mockedProxy).toHaveBeenNthCalledWith(
      2,
      "/v1/cartographer/proposals/bp-1/review",
      expect.objectContaining({
        body: JSON.stringify({ decision: "approve", generation: 1, preview_id: "prv_review" }),
        headers: expect.objectContaining({ "x-spiritos-operator-assertion": "signed-review-assertion" }),
        method: "POST",
      }),
    );
    expect(mockedAudit).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({ id: "session-1" }),
      "preview",
      "prv_review",
    );
    expect(mockedAudit).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({ id: "session-1" }),
      "approve",
      "prv_review",
    );
  });

  it("maps non-approval review decisions to a reject assertion", async () => {
    mockedProxy
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ preview: { generation: 1, preview_id: "prv_edit" } }),
          { headers: { "content-type": "application/json" }, status: 200 },
        ) as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ proposal: { status: "drafted" } }), {
          headers: { "content-type": "application/json" },
          status: 200,
        }) as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
      );

    const response = await POST(
      request({ decision: "request_edit", reason: "Narrow the evidence." }),
      context,
    );

    expect(response.status).toBe(200);
    expect(mockedAssertion).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ action: "reject" }));
  });

  it("rejects browser-authored actor, snapshot, target, or write authority", async () => {
    const response = await POST(
      request({
        actor: "caller",
        decision: "approve",
        proposal: { status: "approved" },
        target: "/tmp/override",
        write_authority: true,
      }),
      context,
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toMatchObject({
      reason_code: "operator_client_authority_binding_forbidden",
    });
    expect(mockedSession).not.toHaveBeenCalled();
    expect(mockedProxy).not.toHaveBeenCalled();
  });
});
