import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("SpiritChat workflow DOM order", () => {
  it("renders SpiritWorkflowVisualizer before sticky composer form", () => {
    const p = resolve(process.cwd(), "src/components/chat/SpiritChat.tsx");
    const src = readFileSync(p, "utf8");
    const iViz = src.indexOf("<SpiritWorkflowVisualizer");
    const iForm = src.indexOf("<form");
    expect(iViz).toBeGreaterThan(-1);
    expect(iForm).toBeGreaterThan(-1);
    expect(iViz).toBeLessThan(iForm);
  });
});
