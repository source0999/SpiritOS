/// <reference types="vitest/globals" />
import { auditOperatorAction, createOperatorApprovalAssertion, requireOperatorSession } from "@/lib/coding/operator-approval-session";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";
import { POST } from "../route";

vi.mock("@/lib/coding/operator-approval-session", () => ({
  auditOperatorAction: vi.fn(), createOperatorApprovalAssertion: vi.fn(), requireOperatorSession: vi.fn(),
}));
vi.mock("@/lib/source-proxy-origin", () => ({ sourceProxyFetch: vi.fn() }));

const mockedAudit = vi.mocked(auditOperatorAction);
const mockedAssertion = vi.mocked(createOperatorApprovalAssertion);
const mockedSession = vi.mocked(requireOperatorSession);
const mockedProxy = vi.mocked(sourceProxyFetch);
const request = (body: unknown) => new Request("https://operator.spirit.test/v1/operator/cartographer-selection", { body: JSON.stringify(body), headers: { "content-type": "application/json", cookie: "spiritos_operator_approval=session-1", host: "operator.spirit.test", origin: "https://operator.spirit.test", "x-spiritos-csrf": "csrf" }, method: "POST" });

describe("Cartographer durable selection operator route", () => {
  beforeEach(() => {
    mockedAudit.mockReset(); mockedAssertion.mockReset(); mockedSession.mockReset(); mockedProxy.mockReset();
    mockedSession.mockResolvedValue({ id: "session-1", operator: "spiritos-local-operator", origin: "https://operator.spirit.test", role: "approval-issuer" });
    mockedAssertion.mockResolvedValue("signed-server-assertion");
  });

  it("forwards only a persisted selection reference under the server session", async () => {
    mockedProxy.mockResolvedValue(new Response(JSON.stringify({ approval: { approval_id: "apr_selection" } }), { headers: { "content-type": "application/json" }, status: 200 }) as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>);
    const response = await POST(request({ action: "approve", generation: 1, preview_id: "prv_selection", proposal_id: "bp-1" }));
    expect(response.status).toBe(200);
    expect(mockedProxy).toHaveBeenCalledWith("/v1/cartographer/proposals/bp-1/operator-selection", expect.objectContaining({ headers: expect.objectContaining({ "x-spiritos-operator-assertion": "signed-server-assertion" }), method: "POST" }));
    expect(mockedAudit).toHaveBeenCalledWith(expect.objectContaining({ id: "session-1" }), "approve", "prv_selection");
  });

  it("rejects browser authority binding overrides before reading a session", async () => {
    const response = await POST(request({ action: "approve", generation: 1, preview_id: "prv_selection", proposal_id: "bp-1", target: "override" }));
    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toMatchObject({ reason_code: "operator_client_authority_binding_forbidden" });
    expect(mockedSession).not.toHaveBeenCalled();
  });
});
