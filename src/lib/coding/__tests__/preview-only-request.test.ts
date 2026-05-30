import { describe, expect, it } from "vitest";

import { taskRequestsPreviewOnly } from "@/lib/coding/preview-only-request";

describe("taskRequestsPreviewOnly", () => {
  it("matches explicit preview-only phrasing", () => {
    expect(
      taskRequestsPreviewOnly(
        "preview only, no apply no commit no push.",
      ),
    ).toBe(true);
  });

  it("matches preview diff only phrasing used in trial prompts", () => {
    expect(
      taskRequestsPreviewOnly(
        "that fake route response helper should let me pass ok=false for sad paths. preview diff only pls.",
      ),
    ).toBe(true);
  });

  it("does not treat normal implementation asks as preview-only", () => {
    expect(taskRequestsPreviewOnly("add a warning tone to the badge helper and apply when ready")).toBe(false);
  });
});
