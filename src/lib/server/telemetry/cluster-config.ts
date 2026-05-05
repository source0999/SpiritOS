export type ClusterNodeConfig = {
  id: string;
  label: string;
  source: "local" | "remote";
  telemetryUrl?: string;
};

/** Strips accidental `< >` from copy-pasted placeholders — `http://<10.0.0.1>:3000` breaks DNS otherwise. */
export function normalizeTelemetryEnvUrl(raw: string | undefined): string | undefined {
  if (!raw) return undefined;
  const t = raw.trim().replaceAll(/[<>]/g, "");
  return t || undefined;
}

export function getClusterConfig(): ClusterNodeConfig[] {
  const localId = process.env.SPIRIT_CLUSTER_LOCAL_ID?.trim() || "spirit-dell";
  const localLabel = process.env.SPIRIT_CLUSTER_LOCAL_LABEL?.trim() || localId;

  const spiritdesktopUrl = normalizeTelemetryEnvUrl(process.env.SPIRITDESKTOP_TELEMETRY_URL);
  const spiritDellUrl = normalizeTelemetryEnvUrl(process.env.SPIRIT_DELL_TELEMETRY_URL);

  const nodes: ClusterNodeConfig[] = [];

  if (localId === "spiritdesktop") {
    nodes.push({ id: "spiritdesktop", label: localLabel, source: "local" });
  } else {
    nodes.push({
      id: "spiritdesktop",
      label: "spiritdesktop",
      source: "remote",
      telemetryUrl: spiritdesktopUrl,
    });
  }

  if (localId === "spirit-dell") {
    nodes.push({ id: "spirit-dell", label: localLabel, source: "local" });
  } else {
    nodes.push({
      id: "spirit-dell",
      label: "Spirit Dell",
      source: "remote",
      telemetryUrl: spiritDellUrl,
    });
  }

  return nodes;
}
