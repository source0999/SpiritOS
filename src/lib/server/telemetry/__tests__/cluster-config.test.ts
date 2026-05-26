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
  it("keeps existing Dell local and spiritdesktop remote behavior while adding Mac mini", () => {
    vi.stubEnv("SPIRIT_CLUSTER_LOCAL_ID", "spirit-dell");
    vi.stubEnv("SPIRIT_CLUSTER_LOCAL_LABEL", "Spirit Dell");
    vi.stubEnv("SPIRITDESKTOP_TELEMETRY_URL", "http://10.0.0.126:3000/api/telemetry/self");
    vi.stubEnv("SPIRIT_MACMINI_TELEMETRY_URL", "");

    expect(getClusterConfig()).toEqual([
      {
        id: "spiritdesktop",
        label: "spiritdesktop",
        source: "remote",
        telemetryUrl: "http://10.0.0.126:3000/api/telemetry/self",
      },
      { id: "spirit-dell", label: "Spirit Dell", source: "local" },
      {
        id: "spirit-mac-mini",
        label: "Spirit Mac Mini",
        source: "remote",
        telemetryUrl: "http://10.0.0.147:3187/api/telemetry/self",
      },
    ]);
  });

  it("keeps spiritdesktop local and Spirit Dell remote behavior unchanged", () => {
    vi.stubEnv("SPIRIT_CLUSTER_LOCAL_ID", "spiritdesktop");
    vi.stubEnv("SPIRIT_CLUSTER_LOCAL_LABEL", "spiritdesktop");
    vi.stubEnv("SPIRIT_DELL_TELEMETRY_URL", "http://10.0.0.148:3000/api/telemetry/self");
    vi.stubEnv("SPIRIT_MACMINI_TELEMETRY_URL", "");

    const nodes = getClusterConfig();

    expect(nodes.find((n) => n.id === "spiritdesktop")).toEqual({
      id: "spiritdesktop",
      label: "spiritdesktop",
      source: "local",
    });
    expect(nodes.find((n) => n.id === "spirit-dell")).toEqual({
      id: "spirit-dell",
      label: "Spirit Dell",
      source: "remote",
      telemetryUrl: "http://10.0.0.148:3000/api/telemetry/self",
    });
  });

  it("uses default Mac mini URL", () => {
    vi.stubEnv("SPIRIT_MACMINI_TELEMETRY_URL", "");

    const macMini = getClusterConfig().find((n) => n.id === "spirit-mac-mini");

    expect(macMini).toEqual({
      id: "spirit-mac-mini",
      label: "Spirit Mac Mini",
      source: "remote",
      telemetryUrl: "http://10.0.0.147:3187/api/telemetry/self",
    });
  });

  it("uses normalized Mac mini URL override", () => {
    vi.stubEnv("SPIRIT_MACMINI_TELEMETRY_URL", " http://<10.0.0.149>:3187/api/telemetry/self ");

    const macMini = getClusterConfig().find((n) => n.id === "spirit-mac-mini");

    expect(macMini?.telemetryUrl).toBe("http://10.0.0.149:3187/api/telemetry/self");
  });

  it("uses normalized spiritdesktop URL", () => {
    vi.stubEnv("SPIRIT_CLUSTER_LOCAL_ID", "spirit-dell");
    vi.stubEnv("SPIRIT_CLUSTER_LOCAL_LABEL", "Spirit Dell");
    vi.stubEnv("SPIRITDESKTOP_TELEMETRY_URL", "http://<192.168.1.5>:3000/api/telemetry/self");
    const nodes = getClusterConfig();
    const remote = nodes.find((n) => n.id === "spiritdesktop" && n.source === "remote");
    expect(remote?.telemetryUrl).toBe("http://192.168.1.5:3000/api/telemetry/self");
  });
});
