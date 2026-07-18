import { beforeEach, describe, expect, it, vi } from "vitest";

const authority = vi.hoisted(() => ({
  compensate: vi.fn(),
  consume: vi.fn(),
  finalize: vi.fn(),
}));

vi.mock("@/lib/coding/spiritflix-admin-approval-authority", () => ({
  compensateSpiritFlixAdminApproval: authority.compensate,
  consumeSpiritFlixAdminApproval: authority.consume,
  finalizeSpiritFlixAdminApproval: authority.finalize,
}));

import { runApprovedSpiritFlixAdminMutation } from "../spiritflix-admin-transaction";

const binding = {
  action: "metadata.mutation",
  target: "spiritflix:videos:video-1:tags",
  plan: {
    schema: "spiritflix-admin-mutation-plan/v2" as const,
    writer: "manual-tags" as const,
    mutation: { itemId: "video-1", manualTags: ["solo"] },
    expected_current_state_hash: "a".repeat(64),
    expected_result_contract_hash: "b".repeat(64),
  },
};

describe("SpiritFlix approved mutation transaction", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    authority.consume.mockResolvedValue({ ok: true, value: { generation: 4 } });
    authority.finalize.mockResolvedValue({ ok: true, value: { state: "consumed" } });
    authority.compensate.mockResolvedValue({ ok: true, value: { state: "invalidated" } });
  });

  it("creates independent reviewer, verifier, and evidence invocations before success finalization", async () => {
    const events: string[] = [];
    const completed = await runApprovedSpiritFlixAdminMutation({
      approvalId: "approval-4",
      binding,
      capture: async () => ({ before: [] }),
      mutate: async () => ({ manualTags: ["solo"] }),
      rollback: async () => { events.push("rollback"); },
      verify: async (result) => {
        events.push("verify");
        return { schema: "tag-result/v1", state: result };
      },
    });

    expect(events).toEqual(["verify"]);
    expect(completed.evidence.participant_invocations.map((item) => item.consumer)).toEqual([
      "spiritflix-admin-reviewer",
      "spiritflix-admin-verifier",
      "evidence-recorder",
    ]);
    expect(new Set(completed.evidence.participant_invocations.map((item) => item.invocation_id)).size).toBe(3);
    expect(completed.evidence.participant_invocations.every((item) => (
      item.acknowledgement.approval_id === "approval-4" &&
      item.acknowledgement.generation === 4 &&
      item.acknowledgement.result_hash === completed.evidence.result_hash
    ))).toBe(true);
    expect(authority.finalize).toHaveBeenCalledWith(
      "approval-4",
      binding.action,
      binding.target,
      binding.plan,
      4,
      "succeeded",
      completed.evidence,
    );
  });

  it("rolls back and invalidates the approval when success finalization fails", async () => {
    authority.finalize.mockResolvedValueOnce({ ok: false, reason: "approval_store_unavailable" });
    const rollback = vi.fn().mockResolvedValue(undefined);

    await expect(runApprovedSpiritFlixAdminMutation({
      approvalId: "approval-4",
      binding,
      capture: async () => ({ previous: true }),
      mutate: async () => ({ manualTags: ["solo"] }),
      rollback,
      verify: async (result) => ({ schema: "tag-result/v1", state: result }),
    })).rejects.toThrow("spiritflix_admin_finalization_failed:approval_store_unavailable");

    expect(rollback).toHaveBeenCalledTimes(1);
    expect(authority.compensate).toHaveBeenCalledTimes(1);
  });

  it("cannot finalize success when result verification fails", async () => {
    const rollback = vi.fn().mockResolvedValue(undefined);
    await expect(runApprovedSpiritFlixAdminMutation({
      approvalId: "approval-4",
      binding,
      capture: async () => ({ previous: true }),
      mutate: async () => ({ manualTags: ["solo"] }),
      rollback,
      verify: async () => { throw new Error("stored_state_mismatch"); },
    })).rejects.toThrow("stored_state_mismatch");

    expect(rollback).toHaveBeenCalledTimes(1);
    expect(authority.finalize).toHaveBeenCalledWith(
      "approval-4",
      binding.action,
      binding.target,
      binding.plan,
      4,
      "failed",
      expect.objectContaining({ result_schema: "spiritflix-admin-failure/v1" }),
    );
    expect(authority.finalize).not.toHaveBeenCalledWith(
      expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), "succeeded", expect.anything(),
    );
  });
});
