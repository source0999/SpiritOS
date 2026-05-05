import { collectClusterNodes } from "@/lib/server/telemetry/collect-cluster-nodes";
import { getClusterConfig } from "@/lib/server/telemetry/cluster-config";
import type { ClusterTelemetryResponse } from "@/lib/server/telemetry/types";

export const dynamic = "force-dynamic";

export async function GET() {
  const configs = getClusterConfig();
  const nodes = await collectClusterNodes(configs);

  const summary = {
    total: nodes.length,
    online: nodes.filter((n) => n.status === "online").length,
    offline: nodes.filter((n) => n.status === "offline").length,
    degraded: nodes.filter((n) => n.status === "degraded").length,
    unknown: nodes.filter((n) => n.status === "unknown").length,
  };

  const body: ClusterTelemetryResponse = {
    ok: summary.offline < summary.total,
    collectedAt: new Date().toISOString(),
    nodes,
    summary,
  };

  return Response.json(body, { headers: { "Cache-Control": "no-store" } });
}
