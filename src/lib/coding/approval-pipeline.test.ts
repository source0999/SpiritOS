/// <reference types="vitest/globals" />

import { parseExplicitTargetFileLine } from "@/lib/coding/explicit-task-target";
import { collectPathsFromUnifiedDiff, diffTouchesExplicitTarget } from "@/lib/coding/unified-diff-paths";

describe("approval pipeline helpers", () => {
  it("parses the last Target file line when multiple appear", () => {
    const text = [
      "Target file: labs/coding/CodingAgentInterface.tsx",
      "",
      "Target file: src/app/coding/design-demo/page.tsx",
    ].join("\n");
    expect(parseExplicitTargetFileLine(text)).toBe("src/app/coding/design-demo/page.tsx");
  });

  it("collects b-side paths from a unified diff", () => {
    const diff = [
      "diff --git a/src/a.ts b/src/a.ts",
      "--- a/src/a.ts",
      "+++ b/src/a.ts",
      "@@ -1 +1 @@",
      "-x",
      "+y",
    ].join("\n");
    expect(collectPathsFromUnifiedDiff(diff)).toEqual(["src/a.ts"]);
  });

  it("detects when a diff does not touch the explicit target", () => {
    const diff = [
      "diff --git a/labs/coding/CodingAgentInterface.tsx b/labs/coding/CodingAgentInterface.tsx",
      "--- a/labs/coding/CodingAgentInterface.tsx",
      "+++ b/labs/coding/CodingAgentInterface.tsx",
      "@@ -1 +1 @@",
      "-a",
      "+b",
    ].join("\n");
    expect(
      diffTouchesExplicitTarget(diff, "src/app/coding/design-demo/page.tsx"),
    ).toBe(false);
  });
});
