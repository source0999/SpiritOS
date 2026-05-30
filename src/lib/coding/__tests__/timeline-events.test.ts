import { describe, expect, it } from "vitest";

import { deriveCodingTimelineEvents, type CodingTimelineInput } from "@/lib/coding/timeline-events";

const baseInput: CodingTimelineInput = {
  allowedFiles: [],
  appliedAt: null,
  approvedAt: null,
  changedFiles: [],
  draftText: "",
  previewMessage: "Preview not requested.",
  previewStatus: "idle",
  previewTarget: "",
  receiptCommandsRun: "not run yet",
  taskId: "",
  taskSubmitted: false,
  verificationMessage: "Verification has not started.",
  verificationStatus: "not_started",
  verifiedAt: null,
};

describe("coding timeline events", () => {
  it("emits the full Codex-class workflow timeline with labeled source and authority", () => {
    const events = deriveCodingTimelineEvents(baseInput);

    expect(events.map((event) => event.step)).toEqual([
      "understand",
      "inspect",
      "scope",
      "draft",
      "preview",
      "approval",
      "apply",
      "verify",
    ]);
    expect(events.every((event) => event.source && event.timestamp && event.authority))
      .toBe(true);
    expect(events.find((event) => event.step === "apply")?.authority).toBe("apply");
  });

  it("marks unavailable evidence honestly instead of inventing facts", () => {
    const events = deriveCodingTimelineEvents({
      ...baseInput,
      draftText: "Explain the coding shell.",
    });

    expect(events.find((event) => event.step === "scope")).toEqual(
      expect.objectContaining({
        evidence: "Scope is unavailable until bounded task data exists.",
        source: "unavailable",
        status: "waiting",
      }),
    );
  });

  it("records preview, approval, apply, and verification evidence as separate events", () => {
    const events = deriveCodingTimelineEvents({
      ...baseInput,
      allowedFiles: ["docs/proxy-test-runner-plan.md"],
      appliedAt: "2026-05-22T01:02:00.000Z",
      approvedAt: "2026-05-22T01:01:00.000Z",
      changedFiles: ["docs/proxy-test-runner-plan.md"],
      draftText: "Update Target file: docs/proxy-test-runner-plan.md.",
      previewMessage: "Preview ready. No files changed yet.",
      previewStatus: "ready",
      previewTarget: "docs/proxy-test-runner-plan.md",
      receiptCommandsRun: "git diff --check",
      taskId: "task-123",
      taskSubmitted: true,
      verificationMessage: "Docs-only verification recorded.",
      verificationStatus: "passed",
      verifiedAt: "2026-05-22T01:03:00.000Z",
    });

    expect(events.find((event) => event.step === "preview")).toEqual(
      expect.objectContaining({
        evidence: "Changed files: docs/proxy-test-runner-plan.md.",
        source: "source_proxy",
        status: "complete",
      }),
    );
    expect(events.find((event) => event.step === "approval")?.source).toBe("human");
    expect(events.find((event) => event.step === "apply")?.evidence).toContain("git diff --check");
    expect(events.find((event) => event.step === "verify")?.status).toBe("complete");
  });
});
