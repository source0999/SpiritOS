import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("Quarantine → Oracle link", () => {
  it("mentions Oracle Voice MVP and /oracle without breaking imports", () => {
    const p = resolve(process.cwd(), "src/components/dashboard/QuarantineStageVisual.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).toContain("/oracle");
    expect(src).toContain("Oracle Voice MVP");
  });
});
