import { afterEach, describe, expect, it, vi } from "vitest";
import { getClusterConfig, normalizeTelemetryEnvUrl } from "../cluster-config";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("normalizeTelemetryEnvUrl", () => {
  it("strips angle bracket placeholders from copy-paste", () => {
    expect(normalizeTelemetryEnvUrl("http://<10.0.0.126>:3000/api/telemetry/self")).toBe(
      "http://10.0.0.126:3000/api/telemetry/self",
    );
  });

  it("returns undefined for blank input", () => {
    expect(normalizeTelemetryEnvUrl(undefined)).toBeUndefined();
    expect(normalizeTelemetryEnvUrl("   ")).toBeUndefined();
  });
});

describe("getClusterConfig", () => {
  it("uses normalized spiritdesktop URL", () => {
    vi.stubEnv("SPIRIT_CLUSTER_LOCAL_ID", "spirit-dell");
    vi.stubEnv("SPIRIT_CLUSTER_LOCAL_LABEL", "Spirit Dell");
    vi.stubEnv("SPIRITDESKTOP_TELEMETRY_URL", "http://<192.168.1.5>:3000/api/telemetry/self");
    const nodes = getClusterConfig();
    const remote = nodes.find((n) => n.id === "spiritdesktop" && n.source === "remote");
    expect(remote?.telemetryUrl).toBe("http://192.168.1.5:3000/api/telemetry/self");
  });
});
