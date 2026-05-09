import { collectLocalNodeTelemetry } from "./collect-local-node";
import { fetchRemoteNodeTelemetry } from "./fetch-remote-node";
import type { ClusterNodeConfig } from "./cluster-config";
import type { ClusterNodeTelemetry } from "./types";

/** Same merge semantics as GET /api/telemetry/cluster - single source of truth for node lists. */
export async function collectClusterNodes(configs: ClusterNodeConfig[]): Promise<ClusterNodeTelemetry[]> {
  const results = await Promise.allSettled(
    configs.map((cfg) => {
      if (cfg.source === "local") {
        return collectLocalNodeTelemetry({ id: cfg.id, label: cfg.label });
      }
      return fetchRemoteNodeTelemetry(cfg.id, cfg.label, cfg.telemetryUrl);
    }),
  );

  return results.map((result, i) => {
    if (result.status === "fulfilled") return result.value;
    const cfg = configs[i]!;
    return {
      id: cfg.id,
      label: cfg.label,
      hostname: null,
      status: "offline" as const,
      source: cfg.source,
      telemetryUrl: cfg.telemetryUrl,
      platform: null,
      arch: null,
      cpu: { model: null, cores: null, usagePct: null, loadAvg: null },
      memory: { totalBytes: null, freeBytes: null, usedBytes: null, usedPct: null },
      uptimeSec: null,
      collectedAt: new Date().toISOString(),
      error: result.reason instanceof Error ? result.reason.message : "collection failed",
    };
  });
}
