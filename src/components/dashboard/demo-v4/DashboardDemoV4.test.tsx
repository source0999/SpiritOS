import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import type { ReactNode } from "react";

import { DashboardDemoV4 } from "./DashboardDemoV4";

const telemetryMock = vi.hoisted(() => ({
  useClusterTelemetry: vi.fn(() => ({
    data: null,
    state: "loaded",
    error: null,
    refetch: vi.fn(),
  })),
}));

vi.mock("@/hooks/useClusterTelemetry", () => ({
  useClusterTelemetry: telemetryMock.useClusterTelemetry,
}));

vi.mock("@/theme/useSpiritTheme", () => ({
  useSpiritTheme: vi.fn(() => ({
    theme: "frozen-water",
    setTheme: vi.fn(),
  })),
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

vi.mock("@/components/oracle/OracleOrbSprite", () => ({
  OracleOrbSprite: () => <div data-testid="oracle-orb-sprite" />,
}));

vi.mock("@/components/oracle/OracleVoiceVisualizer", () => ({
  OracleVoiceVisualizer: () => <div data-testid="oracle-voice-visualizer" />,
}));

describe("DashboardDemoV4", () => {
  beforeEach(() => {
    navMock.path = "/";
    telemetryMock.useClusterTelemetry.mockClear();
  });

  it("renders a <main> with class dashboard-demo-v4-root", () => {
    const { container } = render(<DashboardDemoV4 />);
    const main = container.querySelector("main.dashboard-demo-v4-root");
    expect(main).not.toBeNull();
    expect(main?.tagName).toBe("MAIN");
  });

  it("does not render any old v2 wrapper classes", () => {
    const { container } = render(<DashboardDemoV4 />);
    expect(container.querySelector(".dashboard-v2-glass-frame")).toBeNull();
    expect(container.querySelector(".spirit-dashboard-v2-atmos")).toBeNull();
    expect(container.querySelector(".spirit-dashboard-v2-glass")).toBeNull();
    expect(container.querySelector(".spirit-dashboard-route")).toBeNull();
  });

  it("nav contains links to /, /chat, and /oracle", () => {
    render(<DashboardDemoV4 />);
    const desktopNav = screen.getByRole("navigation", {
      name: /spirit app desktop navigation/i,
    });
    const mobileNav = screen.getByRole("navigation", {
      name: /dashboard mobile navigation/i,
    });

    for (const nav of [desktopNav, mobileNav]) {
      const hrefs = Array.from(nav.querySelectorAll("a")).map((a) =>
        a.getAttribute("href"),
      );
      expect(hrefs).toContain("/");
      expect(hrefs).toContain("/chat");
      expect(hrefs).toContain("/oracle");
    }
  });

  it("nav marks the current path as active when on /", () => {
    navMock.path = "/";
    render(<DashboardDemoV4 />);
    const desktopNav = screen.getByRole("navigation", {
      name: /spirit app desktop navigation/i,
    });
    const mobileNav = screen.getByRole("navigation", {
      name: /dashboard mobile navigation/i,
    });

    expect(
      within(desktopNav).getByRole("link", { name: /^dashboard$/i }),
    ).toBeInTheDocument();
    expect(
      within(mobileNav).getByRole("link", { name: /^dashboard$/i }),
    ).toBeInTheDocument();
    const desktopHome = desktopNav.querySelector('a[href="/"]');
    const mobileHome = mobileNav.querySelector('a[href="/"]');
    expect(desktopHome?.className).toMatch(
      /dashboard-demo-v4-desktop-nav-item-active/,
    );
    expect(mobileHome?.className).toMatch(/dashboard-demo-v4-nav-item-active/);
  });

  it("renders the demo-v4 dashboard content sections", () => {
    render(<DashboardDemoV4 />);
    expect(screen.getByRole("region", { name: /oracle hero/i })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /project tracker/i })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /system stats/i })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /storage pool/i })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /manual checks/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/daily briefing/i)).toBeInTheDocument();
    expect(screen.getAllByText(/demo/i).length).toBeGreaterThan(0);
  });

  it("renders the minimal Oracle hero with visuals and one /oracle action", () => {
    const { container } = render(<DashboardDemoV4 />);
    const oracleHero = screen.getByRole("region", { name: /oracle hero/i });
    const openOracle = within(oracleHero).getByRole("link", { name: /open oracle/i });

    expect(oracleHero).toBeInTheDocument();
    expect(screen.getByTestId("oracle-orb-sprite")).toBeInTheDocument();
    expect(screen.getByTestId("oracle-voice-visualizer")).toBeInTheDocument();
    expect(openOracle).toHaveAttribute("href", "/oracle");
    expect(screen.getByRole("link", { name: /open oracle/i })).toHaveAttribute(
      "href",
      "/oracle",
    );
    expect(container.querySelector(".dashboard-demo-v4-oracle-status-grid")).toBeNull();
    expect(screen.queryByText(/^model$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^mic$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/voice setup/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/local voice status/i)).not.toBeInTheDocument();
  });

  it("does not render old placeholder labels", () => {
    render(<DashboardDemoV4 />);
    expect(screen.queryByText(/oracle hero placeholder/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/system stats placeholder/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^storage placeholder$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/briefing placeholder/i)).not.toBeInTheDocument();
  });

  it("calls useClusterTelemetry exactly once", () => {
    render(<DashboardDemoV4 />);
    expect(telemetryMock.useClusterTelemetry).toHaveBeenCalledTimes(1);
  });

  it("renders the live status pill with the loaded label", () => {
    render(<DashboardDemoV4 />);
    const pill = screen.getByRole("status");
    expect(pill).toHaveAttribute("data-state", "live");
    expect(pill.textContent).toMatch(/trinity mesh live/i);
  });
});
