import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("SpiritWorkspaceShell scroll policy (/chat pull-to-refresh)", () => {
  it("does not permanently assign html/body overflow:hidden on mount (iOS PTR needs document overscroll)", () => {
    const p = resolve(
      process.cwd(),
      "src/components/dashboard/SpiritWorkspaceShell.tsx",
    );
    const src = readFileSync(p, "utf8");
    expect(src).not.toContain('html.style.overflow = "hidden"');
    expect(src).not.toContain('body.style.overflow = "hidden"');
  });

  it("delegates overlay scroll lock to MobileSheet (portal drawers)", () => {
    const sheet = resolve(
      process.cwd(),
      "src/components/chat/MobileSheet.tsx",
    );
    const src = readFileSync(sheet, "utf8");
    expect(src).toContain('html.style.overflow = "hidden"');
    expect(src).toContain("overscroll-y-contain");
  });
});
