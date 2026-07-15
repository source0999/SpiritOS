/// <reference types="vitest/globals" />

import {
  collectPathsFromUnifiedDiff,
  diffTouchesExplicitTarget,
} from "@/lib/coding/unified-diff-paths";

const DOCS_APPEND_STANDARD_UNIFIED_DIFF = [
  "--- a/docs/phase-8-manual-check.md",
  "+++ b/docs/phase-8-manual-check.md",
  "@@ -1,3 +1,4 @@",
  " # Phase 8 Manual Check",
  " ",
  " Approved diffs should require post-apply verification before completion.",
  "+Frontend coding proxy smoke test.",
  "",
].join("\n");

const DOCS_APPEND_GIT_STYLE_DIFF = [
  "diff --git a/docs/phase-8-manual-check.md b/docs/phase-8-manual-check.md",
  "--- a/docs/phase-8-manual-check.md",
  "+++ b/docs/phase-8-manual-check.md",
  "@@ -1,3 +1,4 @@",
  " # Phase 8 Manual Check",
  " ",
  " Approved diffs should require post-apply verification before completion.",
  "+Frontend coding proxy smoke test.",
  "",
].join("\n");

const DOCS_APPEND_UNIFIED_DIFF_WITH_SPACES = [
  "--- a/docs/file with spaces.md",
  "+++ b/docs/file with spaces.md",
  "@@ -1,3 +1,4 @@",
  " # Phase 8 Manual Check",
  " ",
  " Approved diffs should require post-apply verification before completion.",
  "+Frontend coding proxy smoke test.",
  "",
].join("\n");

describe("unified diff path extraction", () => {
  it("keeps git-style diff path extraction", () => {
    expect(collectPathsFromUnifiedDiff(DOCS_APPEND_GIT_STYLE_DIFF)).toEqual([
      "docs/phase-8-manual-check.md",
    ]);
    expect(diffTouchesExplicitTarget(DOCS_APPEND_GIT_STYLE_DIFF, "docs/phase-8-manual-check.md")).toBe(true);
  });

  it("extracts paths from standard unified diff headers without diff --git", () => {
    expect(collectPathsFromUnifiedDiff(DOCS_APPEND_STANDARD_UNIFIED_DIFF)).toEqual([
      "docs/phase-8-manual-check.md",
    ]);
    expect(
      diffTouchesExplicitTarget(
        DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        "docs/phase-8-manual-check.md",
      ),
    ).toBe(true);
  });

  it("rejects standard unified diffs that do not touch the explicit target", () => {
    expect(
      diffTouchesExplicitTarget(
        DOCS_APPEND_STANDARD_UNIFIED_DIFF,
        "labs/coding/CodingAgentInterface.tsx",
      ),
    ).toBe(false);
  });

  it("ignores /dev/null and strips timestamps from unified diff headers", () => {
    const diff = [
      "--- /dev/null\t2026-05-14 12:00:00.000000000 -0400",
      "+++ b/docs/new-note.md\t2026-05-14 12:00:01.000000000 -0400",
      "@@ -0,0 +1 @@",
      "+new",
      "",
    ].join("\n");

    expect(collectPathsFromUnifiedDiff(diff)).toEqual(["docs/new-note.md"]);
    expect(diffTouchesExplicitTarget(diff, "docs/new-note.md")).toBe(true);
  });

  it("normalizes quoted header paths", () => {
    const diff = [
      '--- "a/docs/phase-8-manual-check.md"',
      '+++ "b/docs/phase-8-manual-check.md"',
      "@@ -1 +1 @@",
      "-old",
      "+new",
      "",
    ].join("\n");

    expect(collectPathsFromUnifiedDiff(diff)).toEqual([
      "docs/phase-8-manual-check.md",
    ]);
  });

  it("handles standard unified diff header paths containing spaces", () => {
    expect(collectPathsFromUnifiedDiff(DOCS_APPEND_UNIFIED_DIFF_WITH_SPACES)).toEqual([
      "docs/file with spaces.md",
    ]);
    expect(
      diffTouchesExplicitTarget(
        DOCS_APPEND_UNIFIED_DIFF_WITH_SPACES,
        "docs/file with spaces.md",
      ),
    ).toBe(true);
  });
});
