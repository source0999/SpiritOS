import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import type { OracleBrowserCapabilityReport } from "@/lib/oracle/oracle-browser-capabilities";
import {
  getOracleVisualStateForHomelab,
  getOracleVisualStateFromSessionStatus,
} from "@/lib/oracle/oracle-visual-state";

const healthyHomelabCap = (): OracleBrowserCapabilityReport => ({
  mounted: true,
  isSecureContext: true,
  hasNavigator: true,
  hasMediaDevices: true,
  hasGetUserMedia: true,
  hasMediaRecorder: true,
  hasAudioContext: true,
  canUseMic: true,
  blockedReason: null,
  userMessage: "Mic ready.",
});

describe("oracle-visual-state", () => {
  it("maps session statuses into six visual buckets", () => {
    expect(getOracleVisualStateFromSessionStatus("speaking")).toBe("speaking");
    expect(getOracleVisualStateFromSessionStatus("thinking")).toBe("processing");
    expect(getOracleVisualStateFromSessionStatus("permission-needed")).toBe("permission");
    expect(getOracleVisualStateFromSessionStatus("error")).toBe("error");
  });

  it("homelab uses idle when capability report says mic-ready + secure", () => {
    expect(
      getOracleVisualStateForHomelab({
        mounted: true,
        capability: healthyHomelabCap(),
        badgeVariant: "live",
      }),
    ).toBe("idle");
  });
});

describe("oracle-visuals.css", () => {
  it("defines prefers-reduced-motion handling for orb + visualizer", () => {
    const css = readFileSync(join(process.cwd(), "src/components/oracle/oracle-visuals.css"), "utf8");
    expect(css).toMatch(/prefers-reduced-motion:\s*reduce/);
    expect(css).toMatch(/oracle-orb-orbit-a/);
    expect(css).toMatch(/oracle-viz__bar/);
  });
});
