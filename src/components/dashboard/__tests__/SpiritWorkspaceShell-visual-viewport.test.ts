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
    expect(src).toContain("keyboardInsetPx");
    expect(src).toContain("SpiritWorkspaceMobileChromeProvider");
    expect(src).toContain("max-lg:fixed");
    expect(src).toContain("--spirit-visual-offset-top");
    expect(src).not.toContain('html.style.overflow = "hidden"');
    expect(src).toContain("usePathname");
    expect(src).toContain("isChatRoute");
    expect(
      readFileSync(
        resolve(process.cwd(), "src/lib/hooks/useSpiritVisualViewportVars.ts"),
        "utf8",
      ),
    ).toMatch(/keyboardInset < 1\d/);
    expect(
      readFileSync(
        resolve(process.cwd(), "src/lib/hooks/useSpiritVisualViewportVars.ts"),
        "utf8",
      ),
    ).toContain("paintVh");
    expect(
      readFileSync(
        resolve(process.cwd(), "src/lib/hooks/useSpiritVisualViewportVars.ts"),
        "utf8",
      ),
    ).toContain("vvListenersAttached");
  });
});
