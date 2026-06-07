import { describe, expect, it } from "vitest";

import { POST } from "@/app/v1/coding/trial-receipt-reconcile/route";

describe("trial receipt reconcile route", () => {
  it("treats an empty body as an empty receipt list", async () => {
    process.env.SPIRIT_CODING_USE_PROXY = "true";

    const response = await POST(
      new Request("http://localhost/v1/coding/trial-receipt-reconcile", {
        method: "POST",
      }),
    );
    const payload = await response.json();

    expect(response.status).toBe(200);
    expect(payload).toMatchObject({
      active_unreverted_trial_receipts: 0,
      receipts: [],
      stale_resolved_count: 0,
      trial_fixtures_clean: "yes",
    });
  });
});
