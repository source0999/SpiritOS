import { render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import type { ReactNode } from "react";
import SpiritDashboardHome from "../SpiritDashboardHome";
import type { ClusterTelemetryResponse } from "@/lib/server/telemetry/types";
import { SPIRIT_PALETTES } from "@/theme/spiritPalettes";

const origFetch = globalThis.fetch;

const dashboardTelemetryFixture: ClusterTelemetryResponse = {
  ok: true,
  collectedAt: new Date().toISOString(),
  nodes: [
    {
      id: "spirit-dell",
      label: "Spirit Dell",
      hostname: "srv",
      status: "online",
      source: "local",
      platform: "linux",
      arch: "x64",
      cpu: { model: "x", cores: 4, usagePct: 10, loadAvg: null },
      memory: { totalBytes: 8e9, freeBytes: 4e9, usedBytes: 4e9, usedPct: 50 },
      storage: { drives: [], collectedAt: new Date().toISOString() },
      uptimeSec: 100,
      collectedAt: new Date().toISOString(),
    },
  ],
  summary: { total: 1, online: 1, offline: 0, degraded: 0, unknown: 0 },
};

vi.mock("@/theme/useSpiritTheme", () => ({
  useSpiritTheme: vi.fn(() => ({
    theme: "alice-seagrass",
    setTheme: vi.fn(),
  })),
}));

vi.mock("dexie-react-hooks", () => ({
  useLiveQuery: vi.fn(() => []),
}));

const navMock = vi.hoisted(() => ({ path: "/" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navMock.path,
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

describe("SpiritDashboardHome", () => {
  beforeEach(() => {
    navMock.path = "/";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(dashboardTelemetryFixture), { status: 200 }),
    );
  });

  afterEach(() => {
    globalThis.fetch = origFetch;
  });

  // ── Layout order ──────────────────────────────────────────────────────────

  it("Oracle Voice appears before Daily Briefing in DOM order", () => {
    render(<SpiritDashboardHome />);
    const oracle = screen.getByRole("region", { name: /oracle voice/i });
    const briefing = screen.getByRole("region", { name: /daily briefing/i });
    expect(
      oracle.compareDocumentPosition(briefing) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("Backend Health is not a separate large card region", () => {
    render(<SpiritDashboardHome />);
    expect(screen.queryByRole("region", { name: /^backend health$/i })).toBeNull();
  });

  // ── Oracle Voice ──────────────────────────────────────────────────────────

  it("renders Oracle Voice card", () => {
    render(<SpiritDashboardHome />);
    expect(screen.getByRole("region", { name: /oracle voice/i })).toBeInTheDocument();
  });

  it("renders oracle orb and voice visualizer on the homelab card", () => {
    render(<SpiritDashboardHome />);
    expect(document.querySelector('[data-testid="oracle-orb-sprite"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="oracle-voice-visualizer"]')).not.toBeNull();
  });

  it("oracle orb sprite has inline svg, no raster assets", () => {
    render(<SpiritDashboardHome />);
    const orb = document.querySelector('[data-testid="oracle-orb-sprite"]');
    expect(orb).not.toBeNull();
    expect(orb?.querySelector("svg")).not.toBeNull();
    expect(orb?.querySelector("img")).toBeNull();
  });

  it("Oracle widget shows STT Whisper backend", () => {
    render(<SpiritDashboardHome />);
    const oracleWidget = screen.getByRole("region", { name: /oracle voice/i });
    expect(oracleWidget.textContent).toMatch(/whisper backend/i);
  });

  it("Oracle widget shows secure context and mic capability rows", () => {
    render(<SpiritDashboardHome />);
    const oracleWidget = screen.getByRole("region", { name: /oracle voice/i });
    expect(oracleWidget.textContent).toMatch(/secure context/i);
    expect(oracleWidget.textContent).toMatch(/mic capability/i);
  });

  it("Oracle widget links to /oracle", () => {
    render(<SpiritDashboardHome />);
    const oracleLinks = screen.getAllByRole("link", { name: /open oracle/i });
    expect(oracleLinks.length).toBeGreaterThan(0);
    expect(oracleLinks[0]).toHaveAttribute("href", "/oracle");
  });

  // ── Daily Briefing ────────────────────────────────────────────────────────

  it("renders Daily Briefing widget", () => {
    render(<SpiritDashboardHome />);
    expect(screen.getByRole("region", { name: /daily briefing/i })).toBeInTheDocument();
  });

  it("renders static workspace shortcuts panel with real /chat and /oracle links", () => {
    render(<SpiritDashboardHome />);
    const shortcuts = screen.getByRole("complementary", { name: /workspace shortcuts/i });
    expect(within(shortcuts).getByRole("link", { name: /^open chat$/i })).toHaveAttribute("href", "/chat");
    expect(within(shortcuts).getByRole("link", { name: /^open oracle$/i })).toHaveAttribute(
      "href",
      "/oracle",
    );
  });

  it("Daily Briefing contains at least one briefing item", () => {
    render(<SpiritDashboardHome />);
    const briefing = screen.getByRole("region", { name: /daily briefing/i });
    expect(briefing.textContent).toMatch(/demo/i);
  });

  // ── System Stats & Storage ────────────────────────────────────────────────

  it("renders System Stats card", () => {
    render(<SpiritDashboardHome />);
    expect(screen.getByRole("region", { name: /system stats/i })).toBeInTheDocument();
  });

  it("renders Storage card", () => {
    render(<SpiritDashboardHome />);
    expect(screen.getByRole("region", { name: /storage/i })).toBeInTheDocument();
  });

  it("does not label System Stats or Storage with a standalone Mock badge", async () => {
    render(<SpiritDashboardHome />);
    const stats = screen.getByRole("region", { name: /system stats/i });
    const storage = screen.getByRole("region", { name: /^storage$/i });
    await waitFor(() => expect(stats.textContent).toMatch(/Spirit Dell|Node Vitals/i));
    expect(stats.textContent).not.toMatch(/\bMock\b/);
    expect(storage.textContent).not.toMatch(/\bMock\b/);
  });

  // ── Absent elements ───────────────────────────────────────────────────────

  it("does not render a Chat Core card on home", () => {
    render(<SpiritDashboardHome />);
    expect(screen.queryByRole("region", { name: /chat core/i })).toBeNull();
    expect(screen.queryByRole("link", { name: /open chat workspace/i })).toBeNull();
  });

  it("does not show thread/folder state on home dashboard", () => {
    render(<SpiritDashboardHome />);
    expect(screen.queryByText(/no saved threads/i)).toBeNull();
  });

  it("does not link to /quarantine", () => {
    render(<SpiritDashboardHome />);
    const links = screen.queryAllByRole("link", { name: /quarantine/i });
    expect(links.length).toBe(0);
  });

  // ── Sidebar / nav access ──────────────────────────────────────────────────

  it("Chat is accessible via sidebar /chat link", () => {
    render(<SpiritDashboardHome />);
    const chatLinks = screen.getAllByRole("link", { name: /chat/i });
    const chatHrefs = chatLinks.map((l) => l.getAttribute("href"));
    expect(chatHrefs).toContain("/chat");
  });

  // ── Theme strip ───────────────────────────────────────────────────────────

  it("exposes ThemeStrip palette controls from the registry in the header", () => {
    render(<SpiritDashboardHome />);
    for (const p of SPIRIT_PALETTES) {
      expect(
        screen.getByRole("button", { name: new RegExp(`${p.label} palette`, "i") }),
      ).toBeInTheDocument();
    }
  });
});
