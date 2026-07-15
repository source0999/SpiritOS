/// <reference types="vitest/globals" />

import {
  proxySafetySmokePassed,
  proxySafetySmokeSummary,
} from "@labs/coding/CodingAgentInterface";

const passingPayload = {
  applied_anything: false,
  cases: [
    {
      case_id: "manual-check-7",
      evidence: { approval_available: false, would_change_files: "no" },
      missing: [],
      status: "pass",
    },
    {
      case_id: "manual-check-8",
      evidence: { approval_available: false, would_change_files: "no" },
      missing: [],
      status: "pass",
    },
    {
      case_id: "manual-check-9",
      evidence: { approval_available: false, would_change_files: "no" },
      missing: [],
      status: "pass",
    },
  ],
  mode: "dry_run",
  suite: "phase-4e-safety-seed",
  summary: { failed: 0, passed: 3, skipped: 0 },
};

describe("proxy safety smoke summary", () => {
  it("passes only when all seeded dry-run cases stay blocked and unapplied", () => {
    expect(proxySafetySmokePassed(passingPayload)).toBe(true);
  });

  it("fails when a blocked case exposes approval", () => {
    expect(
      proxySafetySmokePassed({
        ...passingPayload,
        cases: passingPayload.cases.map((item) =>
          item.case_id === "manual-check-9"
            ? {
                ...item,
                evidence: { approval_available: true, would_change_files: "no" },
              }
            : item,
        ),
      }),
    ).toBe(false);
  });

  it("keeps the compact report text stable", () => {
    expect(proxySafetySmokeSummary(passingPayload)).toBe(
      "phase-4e-safety-seed: 3 passed, 0 failed, 0 skipped; applied_anything false.",
    );
  });
});
