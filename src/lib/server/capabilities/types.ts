import type { ClusterNodeStatus, ClusterNodeTelemetry } from "@/lib/server/telemetry/types";

/** Hardware snapshot for formatting - same fields as cluster telemetry */
export type CapabilityTelemetrySnapshot = Pick<
  ClusterNodeTelemetry,
  "cpu" | "memory" | "uptimeSec"
> & {
  storage?: ClusterNodeTelemetry["storage"];
  error?: string;
};

/** Phase 1 - execution wiring for SSH / WinRM / remote shell not verified in-app */
export type RemoteCapabilityVerificationStatus = "unverified" | "disabled";

export type CapabilityToolEntry = {
  name: "get_capabilities" | "list_nodes" | "get_node_status";
  enabled: boolean;
  readOnly: boolean;
  requiresApproval: boolean;
};

export type CapabilityNodeBundle = {
  telemetry: { enabled: boolean; readOnly: true };
  storageTelemetry: { enabled: boolean; readOnly: true };
  projects: { enabled: false; configured: boolean; readOnly: true };
  ssh: {
    enabled: false;
    status: RemoteCapabilityVerificationStatus;
    requiresApproval: true;
  };
  remoteControl: {
    /** Live node telemetry path vs offline / unreachable */
    live: boolean;
    requiresApproval: true;
  };
};

export type CapabilityRegistryNode = {
  id: string;
  label: string;
  status: ClusterNodeStatus;
  source: "local" | "remote";
  platform: string | null;
  capabilities: CapabilityNodeBundle;
  telemetrySnapshot: CapabilityTelemetrySnapshot;
};

export type CapabilityRegistryHost = {
  id: string;
  label: string;
  source: "local";
};

export type CapabilityRegistryResponse = {
  ok: true;
  collectedAt: string;
  host: CapabilityRegistryHost;
  nodes: CapabilityRegistryNode[];
  tools: CapabilityToolEntry[];
};
