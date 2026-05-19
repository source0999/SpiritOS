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
const originalFetch = globalThis.fetch;

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
    globalThis.fetch = originalFetch;
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

  it("surfaces the Cartographer v1 closeout rollup without write controls", async () => {
    globalThis.fetch = vi.fn((input) => {
      const url = String(input);
      if (url === "/v1/cartographer/v1-closeout-dashboard") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              status: "observing",
              write_actions_enabled: false,
              authority_granted: false,
              actions_taken: false,
              dashboard_mode: "read_only_v1_closeout_surface",
              docs_path: "docs/cartographer-v1-evidence-artifacts.md",
              docs_label: "Cartographer v1 evidence artifact contract",
              primary_status: "blocked_missing_evidence",
              primary_label: "Blocked by missing evidence",
              next_action: "Record three clean diagnostic or closeout proof artifacts with passing results.",
              dashboard_cards: [
                {
                  card_id: "v1-readiness",
                  label: "V1 readiness",
                  status: "not_ready",
                  value: "blocked",
                  detail: "8 blockers",
                  endpoint: "/v1/cartographer/v1-readiness",
                },
                {
                  card_id: "v1-evidence",
                  label: "Evidence",
                  status: "blocked",
                  value: 8,
                  detail: "missing real proof artifacts",
                  endpoint: "/v1/cartographer/v1-evidence",
                },
                {
                  card_id: "v1-freeze-marker",
                  label: "Freeze marker",
                  status: "missing",
                  value: "data/cartographer-v1-freeze/freeze-marker.json",
                  detail: "external marker validation",
                  endpoint: "/v1/cartographer/v1-freeze-marker-validation",
                },
                {
                  card_id: "v1-authority",
                  label: "Authority",
                  status: "locked",
                  value: "locked",
                  detail: "passing checks do not grant authority",
                  endpoint: "/v1/cartographer/v1-closeout-status",
                },
                {
                  card_id: "v1-docs",
                  label: "Evidence contract",
                  status: "read_only",
                  value: "docs/cartographer-v1-evidence-artifacts.md",
                  detail: "human-recorded artifact shapes",
                  endpoint: "/v1/cartographer/v1-closeout-dashboard",
                },
              ],
            }),
            { status: 200 },
          ),
        );
      }

      return Promise.resolve(
        new Response(JSON.stringify({ status: "unavailable" }), { status: 200 }),
      );
    }) as typeof fetch;

    render(<DashboardDemoV4 />);

    const cartographer = screen.getByRole("region", { name: /spirit cartographer/i });
    expect(await within(cartographer).findByText("Blocked by missing evidence")).toBeInTheDocument();
    expect(within(cartographer).getByText("V1 readiness")).toBeInTheDocument();
    expect(within(cartographer).getByText("Freeze marker")).toBeInTheDocument();
    expect(within(cartographer).getByText("Evidence contract")).toBeInTheDocument();
    expect(within(cartographer).getByText("data/cartographer-v1-freeze/freeze-marker.json")).toBeInTheDocument();
    expect(within(cartographer).getByText("docs/cartographer-v1-evidence-artifacts.md")).toBeInTheDocument();
    expect(within(cartographer).queryByRole("button", { name: /approve|apply|commit|push/i })).toBeNull();
    expect(globalThis.fetch).toHaveBeenCalledWith("/v1/cartographer/v1-closeout-dashboard", {
      cache: "no-store",
    });
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
