import "server-only";

import { getClusterConfig } from "@/lib/server/telemetry/cluster-config";
import { collectClusterNodes } from "@/lib/server/telemetry/collect-cluster-nodes";
import type { ClusterNodeTelemetry } from "@/lib/server/telemetry/types";
import type {
  CapabilityNodeBundle,
  CapabilityRegistryHost,
  CapabilityRegistryNode,
  CapabilityRegistryResponse,
  CapabilityToolEntry,
} from "./types";

// ── Capability registry - thin layer on cluster telemetry; no parallel universe ─

/** Registry metadata for Phase 1 read-only tools; native AI SDK wiring is Phase 1.5 (see model runtime hint). */
const PHASE1_TOOLS: CapabilityToolEntry[] = [
  { name: "get_capabilities", enabled: true, readOnly: true, requiresApproval: false },
  { name: "list_nodes", enabled: true, readOnly: true, requiresApproval: false },
  { name: "get_node_status", enabled: true, readOnly: true, requiresApproval: false },
];

/** SPIRIT_PROJECT_PATH: comma-separated abs paths - configured iff any segment non-empty after trim. No fs access. */
export function isSpiritProjectPathConfigured(raw: string | undefined): boolean {
  if (raw === undefined) return false;
  const parts = raw.split(",").map((s) => s.trim()).filter(Boolean);
  return parts.length > 0;
}

function liveTelemetryAllowed(status: ClusterNodeTelemetry["status"]): boolean {
  return status === "online" || status === "degraded";
}

function buildNodeCapabilities(node: ClusterNodeTelemetry): CapabilityNodeBundle {
  const live = liveTelemetryAllowed(node.status);
  const hasStorage =
    Array.isArray(node.storage?.drives) && node.storage.drives.length > 0;
  const projectsConfigured = isSpiritProjectPathConfigured(process.env.SPIRIT_PROJECT_PATH);

  return {
    telemetry: { enabled: live, readOnly: true },
    storageTelemetry: { enabled: live && hasStorage, readOnly: true },
    projects: { enabled: false, configured: projectsConfigured, readOnly: true },
    ssh: { enabled: false, status: "unverified", requiresApproval: true },
    remoteControl: { live, requiresApproval: true },
  };
}

function resolveHost(configs: ReturnType<typeof getClusterConfig>): CapabilityRegistryHost {
  const local = configs.find((c) => c.source === "local");
  if (local) {
    return { id: local.id, label: local.label, source: "local" };
  }
  // Should not happen with current getClusterConfig - fall back without inventing hardware names
  return { id: "unknown", label: "unknown", source: "local" };
}

function toCapabilityNode(node: ClusterNodeTelemetry): CapabilityRegistryNode {
  return {
    id: node.id,
    label: node.label,
    status: node.status,
    source: node.source,
    platform: node.platform,
    capabilities: buildNodeCapabilities(node),
    telemetrySnapshot: {
      cpu: node.cpu,
      memory: node.memory,
      storage: node.storage,
      uptimeSec: node.uptimeSec,
      error: node.error,
    },
  };
}

export async function getCapabilityRegistry(): Promise<CapabilityRegistryResponse> {
  const configs = getClusterConfig();
  const nodes = await collectClusterNodes(configs);
  const collectedAt = new Date().toISOString();

  return {
    ok: true,
    collectedAt,
    host: resolveHost(configs),
    nodes: nodes.map(toCapabilityNode),
    tools: PHASE1_TOOLS,
  };
}
