// @vitest-environment jsdom
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SpiritDiagnosticsLive } from "@/components/dashboard/SpiritDiagnosticsLive";

describe("SpiritDiagnosticsLive", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ok: true,
          diagnostics: { engine: "vitest" },
        }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("hydration contract: dev host uses useState + useEffect, not useSyncExternalStore", () => {
    const p = resolve(
      process.cwd(),
      "src/components/dashboard/SpiritDiagnosticsLive.tsx",
    );
    const src = readFileSync(p, "utf8");
    expect(src).toContain("setDevOriginHost");
    expect(src).toContain('useState("")');
    expect(src).not.toContain("useSyncExternalStore");
    expect(src).toContain("window.location.host");
  });

  it("in development, renders Origin value from location.host after effects run", async () => {
    vi.stubEnv("NODE_ENV", "development");
    render(<SpiritDiagnosticsLive />);

    await waitFor(() => {
      expect(screen.getByText(window.location.host)).toBeInTheDocument();
    });
    expect(screen.getByText("Origin", { selector: "dt" })).toBeInTheDocument();
  });

  it("does not render Origin row in non-development", async () => {
    vi.stubEnv("NODE_ENV", "production");
    render(<SpiritDiagnosticsLive />);

    await waitFor(() => {
      expect(screen.getByText(/online|offline|checking/i)).toBeInTheDocument();
    });

    expect(
      screen.queryByText(
        "Local settings, Dexie threads, and voice prefs are per-origin (LAN vs Tailscale differ).",
      ),
    ).not.toBeInTheDocument();
  });
});
