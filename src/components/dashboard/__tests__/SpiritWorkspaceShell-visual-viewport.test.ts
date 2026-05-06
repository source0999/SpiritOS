import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("SpiritWorkspaceShell visual viewport (mobile /chat)", () => {
  it("wires useSpiritVisualViewportVars and shell height CSS var on small screens", () => {
    const p = resolve(
      process.cwd(),
      "src/components/dashboard/SpiritWorkspaceShell.tsx",
    );
    const src = readFileSync(p, "utf8");
    expect(src).toContain("useSpiritVisualViewportVars");
    expect(src).toContain("--spirit-visual-viewport-height");
    expect(src).toContain("workspaceRootRef");
  });
});
