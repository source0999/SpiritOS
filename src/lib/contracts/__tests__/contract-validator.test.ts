import { describe, expect, it } from "vitest";

import { isSharedAppliedRunReceipt } from "@/lib/contracts/contract-validator";

describe("shared applied-run receipt contract", () => {
  it("accepts a canonical cross-process receipt", () => {
    expect(isSharedAppliedRunReceipt({
      id: "receipt-1", task_id: "task-1", diff: "diff", reverse_diff: "reverse", target: "src/a.ts", applied_at: "2026-07-14T00:00:00Z",
    })).toBe(true);
  });

  it("rejects the deliberate missing-task violation", () => {
    expect(isSharedAppliedRunReceipt({ id: "receipt-1", diff: "diff", reverse_diff: "reverse", target: "src/a.ts", applied_at: "now" })).toBe(false);
  });
});
