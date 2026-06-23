import { describe, expect, it } from "vitest";
import { buildMarkdownSummary, percentile, summarizeRuns } from "../spiritflix-mobile-benchmark-report.mjs";

describe("spiritflix mobile benchmark report", () => {
  it("computes percentiles and markdown summary", () => {
    const summary = summarizeRuns([40, 50, 60, 70, 80]);
    expect(percentile([40, 50, 60, 70, 80], 50)).toBe(60);
    expect(summary.p50).toBe(60);
    expect(summary.p95).toBe(80);

    const markdown = buildMarkdownSummary({
      evidenceDir: "docs/evidence/test",
      payload: {
        generatedAt: "2026-06-22T00:00:00.000Z",
        baseUrl: "https://localhost:3000",
        itemId: "phase7-candidate-02",
        mode: "warm",
        commands: ["node scripts/spiritflix-mobile-benchmark.mjs"],
        gitStatus: "",
        fixtureNote: "fixture note",
        metrics: {
          pageUsefulContent: summary,
          videoPlaying: summary,
          apiMobileOptimizedWarm: summary,
        },
        apiCold: { elapsedMs: 120, source: "mobileOptimized", available: true, rangeSupported: true },
        sourceSelection: {
          api: "mobileOptimized",
          playerPlaybackSource: "mac_optimized_mp4",
          playerVideoSrc: "/api/spiritflix/mobile-optimized?stream=1&key=phase7",
          rangeSupported: true,
          mobileOptimized: true,
        },
      },
      targets: { pageP50: 50, pageP95: 50, videoP50: 50, videoP95: 50 },
    });

    expect(markdown).toContain("SpiritFlix mobile 50ms loop evidence");
    expect(markdown).toContain("mobileOptimized");
  });
});
