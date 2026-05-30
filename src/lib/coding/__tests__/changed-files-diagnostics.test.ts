import { describe, expect, it } from "vitest";

import { buildChangedFilesDiagnostics } from "@/lib/coding/changed-files-diagnostics";

describe("changed files diagnostics", () => {
  it("separates preview-only changes from disk-applied changes", () => {
    const diagnostics = buildChangedFilesDiagnostics({
      diff: [
        "diff --git a/tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx b/tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx",
        "+++ b/tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx",
        "+export const previewOnly = true;",
      ].join("\n"),
      status: "ready",
    });

    expect(diagnostics.previewChangedFiles).toEqual([
      "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx",
    ]);
    expect(diagnostics.diskChangedFiles).toEqual([]);
    expect(diagnostics.appliedChangedFiles).toEqual([]);
  });

  it("reports applied disk changes after apply", () => {
    const diagnostics = buildChangedFilesDiagnostics({
      appliedAt: "2026-05-29T00:00:00.000Z",
      diff: [
        "diff --git a/docs/phase-8-manual-check.md b/docs/phase-8-manual-check.md",
        "+++ b/docs/phase-8-manual-check.md",
        "+applied smoke",
      ].join("\n"),
      status: "applied",
    });

    expect(diagnostics.appliedChangedFiles).toEqual(["docs/phase-8-manual-check.md"]);
    expect(diagnostics.diskChangedFiles).toEqual(["docs/phase-8-manual-check.md"]);
  });
});
