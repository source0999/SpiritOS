/// <reference types="vitest/globals" />

import { runDesignStudioApprovedWriteback } from "@/lib/coding/design-studio-approved-writeback-runtime";
import { POST } from "../route";

vi.mock("@/lib/coding/design-studio-approved-writeback-runtime", () => ({
  runDesignStudioApprovedWriteback: vi.fn(),
}));

describe("Design approved writeback route", () => {
  beforeEach(() => vi.mocked(runDesignStudioApprovedWriteback).mockReset());

  it("fails closed for malformed JSON", async () => {
    const response = await POST(
      new Request("https://spirit.test/v1/coding/design-studio/approved-writeback", {
        body: "{",
        method: "POST",
      }),
    );
    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toMatchObject({
      result: { status: "rejected", write_invoked: false },
      write_authority: false,
    });
    expect(runDesignStudioApprovedWriteback).not.toHaveBeenCalled();
  });

  it("never returns authoritative success for a rejected runtime result", async () => {
    vi.mocked(runDesignStudioApprovedWriteback).mockResolvedValue({
      participant_records: [],
      reasons: ["post_write_verification_failed"],
      status: "rejected",
      write_invoked: true,
    });
    const response = await POST(
      new Request("https://spirit.test/v1/coding/design-studio/approved-writeback", {
        body: JSON.stringify({ approval_id: "apr_test" }),
        method: "POST",
      }),
    );
    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toMatchObject({
      result: { status: "rejected" },
      write_authority: false,
    });
  });
});
