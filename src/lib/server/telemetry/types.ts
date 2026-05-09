export type ClusterNodeStatus = "online" | "offline" | "degraded" | "unknown";

export type DriveType = "SSD" | "HDD" | "NVME" | "UNKNOWN";
export type SmartStatus = "Healthy" | "Warning" | "Critical" | "Unknown";

export type NodeDrive = {
  id: string;
  name: string;
  mount: string | null;
  fsType: string | null;
  type: DriveType;
  totalBytes: number | null;
  usedBytes: number | null;
  freeBytes: number | null;
  usedPct: number | null;
  tempC: number | null;
  smart: SmartStatus;
};

export type NodeStorage = {
  drives: NodeDrive[];
  collectedAt: string;
  error?: string;
};

export type ClusterNodeTelemetry = {
  id: string;
  label: string;
  hostname: string | null;
  status: ClusterNodeStatus;
  source: "local" | "remote";
  telemetryUrl?: string;
  platform: string | null;
  arch: string | null;
  cpu: {
    model: string | null;
    cores: number | null;
    usagePct: number | null;
    loadAvg: number[] | null;
  };
  memory: {
    totalBytes: number | null;
    freeBytes: number | null;
    usedBytes: number | null;
    usedPct: number | null;
  };
  storage?: NodeStorage;
  uptimeSec: number | null;
  collectedAt: string;
  error?: string;
};

export type ClusterTelemetryResponse = {
  ok: boolean;
  collectedAt: string;
  nodes: ClusterNodeTelemetry[];
  summary: {
    total: number;
    online: number;
    offline: number;
    degraded: number;
    unknown: number;
  };
};
