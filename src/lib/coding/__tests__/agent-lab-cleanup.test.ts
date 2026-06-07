import { describe, expect, it } from "vitest";

import {
  buildDeleteFileReverseDiff,
  isAgentLabTrialPath,
  pathIsAllowedForTrialReverse,
} from "@/lib/coding/agent-lab-cleanup";

describe("agent-lab cleanup helpers", () => {
  it("detects agent-lab trial paths", () => {
    expect(isAgentLabTrialPath("src/app/agent-lab/calculator/page.tsx")).toBe(true);
    expect(isAgentLabTrialPath("src/components/coding/CodingCockpitShell.tsx")).toBe(false);
  });

  it("matches glob allowed_files for agent-lab reverses", () => {
    expect(
      pathIsAllowedForTrialReverse("src/app/agent-lab/todo/page.tsx", ["src/app/agent-lab/**"]),
    ).toBe(true);
    expect(pathIsAllowedForTrialReverse("src/app/page.tsx", ["src/app/agent-lab/**"])).toBe(false);
  });

  it("builds delete-file reverse diffs from current content", () => {
    const diff = buildDeleteFileReverseDiff(
      "src/app/agent-lab/revert-smoke/page.tsx",
      'export default function RevertSmoke() { return null; }\n',
    );
    expect(diff).toContain("deleted file mode 100644");
    expect(diff).toContain("+++ /dev/null");
    expect(diff).toContain("-export default function RevertSmoke() { return null; }");
  });
});
