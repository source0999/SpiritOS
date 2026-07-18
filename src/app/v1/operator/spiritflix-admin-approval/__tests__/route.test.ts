import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  audit: vi.fn(),
  issue: vi.fn(),
  persist: vi.fn(),
  requireSession: vi.fn(),
  resolveBinding: vi.fn(),
}));

vi.mock("@/lib/coding/operator-approval-session", () => ({
  auditOperatorAction: mocks.audit,
  requireOperatorSession: mocks.requireSession,
}));

vi.mock("@/lib/coding/spiritflix-admin-approval-authority", () => ({
  issueSpiritFlixAdminApproval: mocks.issue,
  persistSpiritFlixAdminPreview: mocks.persist,
}));

vi.mock("@/lib/coding/spiritflix-admin-approval-binding", () => ({
  resolveSpiritFlixAdminApprovalBinding: mocks.resolveBinding,
}));

import { POST } from "../route";

describe("SpiritFlix admin operator issuance", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mocks.requireSession.mockResolvedValue({ operator: "fixture-operator", origin: "https://localhost", role: "approval-issuer" });
    mocks.persist.mockResolvedValue({ ok: true, value: { preview_id: "preview-server-owned", generation: 2 } });
    mocks.issue.mockResolvedValue({ ok: true, value: { approval_id: "approval-server-owned", generation: 2 } });
    mocks.resolveBinding.mockResolvedValue({
      action: "metadata.mutation",
      target: "spiritflix:videos:video-1:model",
      plan: {
        schema: "spiritflix-admin-mutation-plan/v2",
        writer: "manual-model",
        mutation: { itemId: "video-1", modelName: "Sava Schultz", knownModelNames: ["Sava Schultz"] },
        expected_current_state_hash: "a".repeat(64),
        expected_result_contract_hash: "b".repeat(64),
      },
    });
  });

  it("derives the manual-model binding on the server before authenticated issuance", async () => {
    const response = await POST(new Request("https://localhost/v1/operator/spiritflix-admin-approval", {
      body: JSON.stringify({
        action: "preview",
        writer: "manual-model",
        mutation: { itemId: "video-1", modelName: "Sava Schultz", knownModelNames: ["Sava Schultz"] },
      }),
      method: "POST",
    }));

    expect(response.status).toBe(200);
    expect(mocks.resolveBinding).toHaveBeenCalledWith("manual-model", {
      itemId: "video-1", modelName: "Sava Schultz", knownModelNames: ["Sava Schultz"],
    });
    expect(mocks.persist).toHaveBeenCalledWith("metadata.mutation", "spiritflix:videos:video-1:model", expect.objectContaining({
      expected_current_state_hash: "a".repeat(64),
      mutation: expect.objectContaining({ knownModelNames: ["Sava Schultz"] }),
    }));
    expect(mocks.audit).toHaveBeenCalledWith(expect.anything(), "preview", "preview-server-owned");
  });

  it("issues only a persisted preview and rejects client binding overrides", async () => {
    const approved = await POST(new Request("https://localhost/v1/operator/spiritflix-admin-approval", {
      body: JSON.stringify({ action: "approve", preview_id: "preview-server-owned", generation: 2 }),
      method: "POST",
    }));
    expect(approved.status).toBe(200);
    expect(mocks.issue).toHaveBeenCalledWith("preview-server-owned", 2);

    const overridden = await POST(new Request("https://localhost/v1/operator/spiritflix-admin-approval", {
      body: JSON.stringify({ action: "approve", preview_id: "preview-server-owned", generation: 2, writer: "manual-tags" }),
      method: "POST",
    }));
    expect(overridden.status).toBe(400);
    await expect(overridden.json()).resolves.toEqual({ reason_code: "operator_client_authority_binding_forbidden" });
  });

  it("maps every bounded writer and rejects an unregistered writer", async () => {
    const requests = [
      { writer: "library-smart-rescan", mutation: {} },
      { writer: "admin-action", mutation: { action: "softDelete", mode: "execute", confirmToken: "preview-1" } },
      { writer: "smart-analysis", mutation: { path: "/media/one.mkv", action: "analyze" } },
      { writer: "smart-batch", mutation: { path: "/media", action: "run" } },
      { writer: "manual-tags", mutation: { itemId: "video-1", manualTags: ["solo"] } },
      { writer: "face-learning", mutation: { itemId: "video-1", modelName: "Sava Schultz" } },
    ];
    for (const request of requests) {
      const response = await POST(new Request("https://localhost/v1/operator/spiritflix-admin-approval", {
        body: JSON.stringify({ action: "preview", ...request }), method: "POST",
      }));
      expect(response.status).toBe(200);
    }
    const rejected = await POST(new Request("https://localhost/v1/operator/spiritflix-admin-approval", {
      body: JSON.stringify({ action: "preview", writer: "unregistered-writer", mutation: {} }), method: "POST",
    }));
    expect(rejected.status).toBe(400);
    await expect(rejected.json()).resolves.toEqual({ reason_code: "operator_client_authority_binding_forbidden" });
  });
});
