/// <reference types="vitest/globals" />
import { auditOperatorAction, requireOperatorSession } from "@/lib/coding/operator-approval-session";
import { issueDesignWritebackApproval, resolveDesignWritebackPreview } from "@/lib/coding/design-approval-authority";
import { POST } from "../route";

vi.mock("@/lib/coding/operator-approval-session", () => ({ auditOperatorAction: vi.fn(), requireOperatorSession: vi.fn() }));
vi.mock("@/lib/coding/design-approval-authority", () => ({ issueDesignWritebackApproval: vi.fn(), rejectDesignWritebackPreview: vi.fn(), resolveDesignWritebackPreview: vi.fn() }));

const mockedAudit = vi.mocked(auditOperatorAction);
const mockedSession = vi.mocked(requireOperatorSession);
const mockedIssue = vi.mocked(issueDesignWritebackApproval);
const mockedPreview = vi.mocked(resolveDesignWritebackPreview);
const request = (body: unknown) => new Request("https://operator.spirit.test/v1/operator/design-approval", { body: JSON.stringify(body), headers: { "content-type": "application/json", cookie: "spiritos_operator_approval=session-1", host: "operator.spirit.test", origin: "https://operator.spirit.test", "x-spiritos-csrf": "csrf" }, method: "POST" });
const preview = { artifact_id: "design-writeback-content", content_hash: "content", context: "context", generation: 1, preview_id: "prv_design", source_head: "source", target: "design-memory/2026-07-01/design_run.md" };

describe("operator Design approval route", () => {
  beforeEach(() => {
    mockedAudit.mockReset(); mockedSession.mockReset(); mockedIssue.mockReset(); mockedPreview.mockReset();
    mockedSession.mockResolvedValue({ id: "session-1", operator: "spiritos-local-operator", origin: "https://operator.spirit.test", role: "approval-issuer" });
    mockedPreview.mockResolvedValue({ ok: true, value: preview });
  });
  it("rejects caller-provided Design bindings", async () => {
    const response = await POST(request({ action: "approve", generation: 1, preview_id: "prv_design", target: "override" }));
    expect(response.status).toBe(400); await expect(response.json()).resolves.toMatchObject({ reason_code: "operator_client_authority_binding_forbidden" });
    expect(mockedIssue).not.toHaveBeenCalled();
  });
  it("issues only a server-resolved persisted Design preview", async () => {
    mockedIssue.mockResolvedValue({ ok: true, value: { ...preview, approval_id: "apr_design", consumer: "design-writeback", operation: "design_writeback" } });
    const response = await POST(request({ action: "approve", generation: 1, preview_id: "prv_design" }));
    expect(response.status).toBe(200); expect(mockedPreview).toHaveBeenCalledWith("prv_design", 1); expect(mockedIssue).toHaveBeenCalledWith(preview); expect(mockedAudit).toHaveBeenCalledWith(expect.objectContaining({ id: "session-1" }), "approve", "prv_design");
  });
  it("rejects missing sessions", async () => {
    mockedSession.mockRejectedValue(new Error("operator_session_missing"));
    const response = await POST(request({ action: "approve", generation: 1, preview_id: "prv_design" }));
    expect(response.status).toBe(403); await expect(response.json()).resolves.toMatchObject({ reason_code: "operator_session_missing" });
  });
});
