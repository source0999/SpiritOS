import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("SpiritFlix load performance harness", () => {
  it("is wired to the npm script with visible-page budgets", () => {
    const packageJson = JSON.parse(readFileSync("package.json", "utf8")) as { scripts?: Record<string, string> };
    const harness = readFileSync("scripts/spiritflix-load-perf.mjs", "utf8");

    expect(packageJson.scripts?.["spiritflix:perf:synthetic"]).toBe("node ./scripts/spiritflix-load-perf.mjs");
    expect(harness).toContain("faceMetadataItems: 20");
    expect(harness).toContain("libraryRequestsBeforeGrid: 1");
    expect(harness).toContain("docs/evidence/spiritflix-load-perf-");
  });
});
