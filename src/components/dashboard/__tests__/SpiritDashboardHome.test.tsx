import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

import SpiritDashboardHome from "../SpiritDashboardHome";

vi.mock("@/hooks/useClusterTelemetry", () => ({
  useClusterTelemetry: vi.fn(() => ({
    data: null,
    state: "loaded",
    error: null,
    refetch: vi.fn(),
  })),
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

describe("SpiritDashboardHome", () => {
  beforeEach(() => {
    navMock.path = "/";
  });

  it("renders DashboardDemoV4 as the live root", () => {
    const { container } = render(<SpiritDashboardHome />);

    const root = container.querySelector(".dashboard-demo-v4-root");
    expect(root).not.toBeNull();
    expect(root?.tagName).toBe("MAIN");
  });

  it("does not render old v2 dashboard shell classes", () => {
    const { container } = render(<SpiritDashboardHome />);

    expect(container.querySelector(".dashboard-v2-glass-frame")).toBeNull();
    expect(container.querySelector(".spirit-dashboard-v2-atmos")).toBeNull();
    expect(container.querySelector(".spirit-dashboard-v2-glass")).toBeNull();
    expect(container.querySelector(".spirit-dashboard-route")).toBeNull();
  });

  it("nav contains links to /, /chat, and /oracle", () => {
    render(<SpiritDashboardHome />);

    const nav = screen.getByRole("navigation", {
      name: /dashboard navigation/i,
    });
    const hrefs = Array.from(nav.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );

    expect(hrefs).toContain("/");
    expect(hrefs).toContain("/chat");
    expect(hrefs).toContain("/oracle");
  });

  it("renders the Oracle hero placeholder", () => {
    render(<SpiritDashboardHome />);

    expect(
      screen.getByRole("region", { name: /oracle hero placeholder/i }),
    ).toBeInTheDocument();
  });
});
