/// <reference types="vitest/globals" />

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const shellSource = readFileSync(
  resolve(process.cwd(), "src/components/coding/DesignStudioShell.tsx"),
  "utf8",
);

describe("DesignStudioShell source contract", () => {
  it("keeps the preview workbench write paths visibly locked", () => {
    expect(shellSource).toContain("Preview Workbench");
    expect(shellSource).toContain("No model call");
    expect(shellSource).toContain("No apply authority");
    expect(shellSource).toContain("No memory write");
    expect(shellSource).toContain("No raw CSS ingest");
    expect(shellSource).toContain("Apply locked");
  });

  it("keeps packet state blocked from downstream GO", () => {
    expect(shellSource).toContain("preview-shell-local");
    expect(shellSource).toContain("blocked_until_packet_acceptance");
    expect(shellSource).toContain("Preview opening is not GO. Downstream consumption is required.");
    expect(shellSource).toContain("Design Packet");
    expect(shellSource).toContain("Coder Packet");
    expect(shellSource).toContain("Bounded coder_packet waits for sandbox apply approval.");
  });
});
