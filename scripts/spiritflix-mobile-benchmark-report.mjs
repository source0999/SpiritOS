export function percentile(values, p) {
  if (!values.length) return null;
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1));
  return sorted[index];
}

export function summarizeRuns(values) {
  const clean = values.filter((value) => Number.isFinite(value));
  return {
    count: clean.length,
    p50: percentile(clean, 50),
    p75: percentile(clean, 75),
    p95: percentile(clean, 95),
    min: clean.length ? Math.min(...clean) : null,
    max: clean.length ? Math.max(...clean) : null,
    samples: clean,
  };
}

function verdictFor(summary, targetMs) {
  if (summary.p50 == null || summary.p95 == null) return "INCONCLUSIVE";
  if (summary.p50 <= targetMs && summary.p95 <= targetMs * 1.3) return "PASS";
  if (summary.p50 <= 65 && summary.p95 <= 80) return "PARTIAL";
  return "FAIL";
}

export function buildMarkdownSummary({ evidenceDir, payload, targets }) {
  const pageVerdict = verdictFor(payload.metrics.pageUsefulContent, targets.pageP50);
  const videoVerdict = verdictFor(payload.metrics.videoPlaying, targets.videoP50);
  const apiVerdict = verdictFor(payload.metrics.apiMobileOptimizedWarm, 50);

  return `# SpiritFlix mobile 50ms loop evidence

Generated: ${payload.generatedAt}
Evidence: \`${evidenceDir}\`
Base URL: ${payload.baseUrl}
Item ID: ${payload.itemId}
Mode: ${payload.mode}

## Commands

${payload.commands.map((command) => `- \`${command}\``).join("\n")}

## Metrics

| Metric | P50 | P75 | P95 | Verdict |
| --- | ---: | ---: | ---: | --- |
| Page useful content (shell) | ${payload.metrics.pageUsefulContent.p50?.toFixed?.(1) ?? "n/a"} ms | ${payload.metrics.pageUsefulContent.p75?.toFixed?.(1) ?? "n/a"} ms | ${payload.metrics.pageUsefulContent.p95?.toFixed?.(1) ?? "n/a"} ms | ${pageVerdict} |
| Video playing (real API player) | ${payload.metrics.videoPlaying.p50?.toFixed?.(1) ?? "n/a"} ms | ${payload.metrics.videoPlaying.p75?.toFixed?.(1) ?? "n/a"} ms | ${payload.metrics.videoPlaying.p95?.toFixed?.(1) ?? "n/a"} ms | ${videoVerdict} |
| Warm video tap → playing | ${payload.metrics.warmVideoTap?.p50?.toFixed?.(1) ?? "n/a"} ms | ${payload.metrics.warmVideoTap?.p75?.toFixed?.(1) ?? "n/a"} ms | ${payload.metrics.warmVideoTap?.p95?.toFixed?.(1) ?? "n/a"} ms | ${verdictFor(payload.metrics.warmVideoTap ?? { p50: null, p95: null }, targets.videoP50)} |
| Mobile optimized API warm | ${payload.metrics.apiMobileOptimizedWarm.p50?.toFixed?.(1) ?? "n/a"} ms | ${payload.metrics.apiMobileOptimizedWarm.p75?.toFixed?.(1) ?? "n/a"} ms | ${payload.metrics.apiMobileOptimizedWarm.p95?.toFixed?.(1) ?? "n/a"} ms | ${apiVerdict} |
| Mobile optimized API cold | ${payload.apiCold.elapsedMs.toFixed(1)} ms | — | — | — |

## Source selection

- API source: ${payload.sourceSelection.api}
- Player playback class: ${payload.sourceSelection.playerPlaybackSource ?? "unknown"}
- Player video src: ${payload.sourceSelection.playerVideoSrc ?? "unknown"}
- Range supported: ${payload.sourceSelection.rangeSupported ? "yes" : "no"}
- Mobile optimized available: ${payload.sourceSelection.mobileOptimized ? "yes" : "no"}

## Notes

${payload.fixtureNote}

## Git status

\`\`\`
${payload.gitStatus || "(clean)"}
\`\`\`
`;
}
